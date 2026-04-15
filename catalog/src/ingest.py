"""Ingestion orchestrator — discovers repos, scans components, enriches, finds similarities."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from catalog.src import scanner, db, security, similarity, classifier


@dataclass
class IngestConfig:
    repos_dir: Path
    db_conn: sqlite3.Connection
    pull_repos: bool = True
    enrich_github: bool = True
    run_classifier: bool = True
    force: bool = False
    batch_size: int = 50


@dataclass
class IngestResult:
    repos_scanned: int = 0
    repos_pulled: int = 0
    components_added: int = 0
    components_updated: int = 0
    components_skipped: int = 0
    tombstoned: int = 0
    urls_extracted: int = 0
    urls_enriched: int = 0
    similarities_found: int = 0
    errors: list = field(default_factory=list)


def run_ingestion(config: IngestConfig) -> IngestResult:
    """Run the full ingestion pipeline.

    Phase 0: Discover and optionally pull repos.
    Phase 1: Scan each repo for components, security-check, classify, upsert.
    Phase 2: Enrich GitHub URLs if enabled.
    Phase 3: Find similarities among collected components.
    """
    result = IngestResult()
    conn = config.db_conn
    all_urls: list[str] = []
    similarity_candidates: list[dict] = []

    # ------------------------------------------------------------------
    # Phase 0: Discover repos
    # ------------------------------------------------------------------
    repos = scanner.discover_repos(config.repos_dir)
    result.repos_scanned = len(repos)

    if config.pull_repos:
        pull_results = scanner.pull_repos(repos)
        result.repos_pulled = sum(1 for v in pull_results.values() if v == "ok")

    # ------------------------------------------------------------------
    # Phase 1: Process each repo
    # ------------------------------------------------------------------
    for repo_path in repos:
        # Register/upsert repo in DB (local repo)
        repo_url = str(repo_path)
        repo_row = db.get_repo_by_url(conn, repo_url)
        if repo_row is None:
            repo_id = db.insert_repo(
                conn,
                url=repo_url,
                name=repo_path.name,
                is_local=True,
            )
        else:
            # upsert to refresh fields, but lastrowid is unreliable for
            # ON CONFLICT DO UPDATE — always use the known id from the
            # existing row.
            db.upsert_repo(
                conn,
                url=repo_url,
                name=repo_path.name,
                is_local=True,
            )
            repo_id = repo_row["id"]

        # Discover components
        try:
            components = scanner.discover_components(repo_path)
        except Exception as exc:
            result.errors.append(f"discover_components({repo_path}): {exc}")
            continue

        for comp in components:
            file_path = comp["file_path"]

            # Check tombstoned directly in DB (don't use get_component_by_path
            # which filters out tombstoned rows)
            cur = conn.execute(
                "SELECT id, tombstoned FROM components WHERE repo_id = ? AND file_path = ?",
                (repo_id, file_path),
            )
            existing_raw = cur.fetchone()

            # If tombstoned, skip permanently
            if existing_raw and existing_raw["tombstoned"]:
                result.components_skipped += 1
                continue

            # Check if update needed
            existing = db.get_component_by_path(conn, repo_id, file_path)
            if existing and not config.force:
                needs_update = db.should_update_component(
                    existing,
                    new_commit=comp.get("file_last_commit", ""),
                    new_hash=comp.get("content_hash", ""),
                )
                if not needs_update:
                    result.components_skipped += 1
                    # Still collect for similarity analysis
                    content = (repo_path / file_path).read_text(
                        encoding="utf-8", errors="replace"
                    )
                    similarity_candidates.append(
                        {
                            "id": existing["id"],
                            "name": comp["name"],
                            "type": comp["type"],
                            "content": content,
                        }
                    )
                    continue

            # Read file content for security scan
            content = (repo_path / file_path).read_text(
                encoding="utf-8", errors="replace"
            )

            # Security scan
            verdict = security.scan_component(content, comp["type"], comp["name"])

            # Classify
            classification = {"project_types": [], "personas": []}
            if config.run_classifier:
                classification = classifier.keyword_classify(
                    name=comp.get("name", ""),
                    description=comp.get("description", ""),
                    tags=comp.get("tags", []),
                )

            # Build common fields for insert/update
            comp_fields = dict(
                repo_id=repo_id,
                name=comp.get("name", ""),
                type=comp["type"],
                file_path=file_path,
                description=comp.get("description", ""),
                file_last_commit=comp.get("file_last_commit", ""),
                file_last_author=comp.get("file_last_author", ""),
                version=comp.get("version", ""),
                triggers=",".join(comp.get("triggers", [])),
                tools_used=comp.get("tools_used"),
                metadata=comp.get("metadata"),
                tags=comp.get("tags"),
                project_types=classification.get("project_types"),
                personas=classification.get("personas"),
                content_hash=comp.get("content_hash", ""),
            )

            # Insert or update
            if existing:
                # Update existing component
                comp_id = existing["id"]
                update_fields = {k: v for k, v in comp_fields.items() if k != "repo_id"}
                db.update_component(conn, comp_id, **update_fields)
                result.components_updated += 1
            else:
                # Insert new component
                comp_id = db.insert_component(conn, **comp_fields)
                result.components_added += 1

            # If security verdict is not safe: tombstone
            if not verdict.is_safe:
                reason = "; ".join(verdict.findings)
                db.tombstone_component(conn, comp_id, reason)
                result.tombstoned += 1
            else:
                # Safe — add to similarity candidates
                similarity_candidates.append(
                    {
                        "id": comp_id,
                        "name": comp.get("name", ""),
                        "type": comp["type"],
                        "content": content,
                    }
                )

        # Extract GitHub URLs from .md files
        for md_file in repo_path.rglob("*.md"):
            try:
                urls = scanner.extract_github_urls(md_file)
                all_urls.extend(urls)
                result.urls_extracted += len(urls)
            except Exception:
                pass

    # Deduplicate URLs
    all_urls = sorted(set(all_urls))

    # ------------------------------------------------------------------
    # Phase 2: Enrich GitHub URLs
    # ------------------------------------------------------------------
    if config.enrich_github and all_urls:
        from catalog.src import enricher

        enriched = enricher.batch_enrich_repos(all_urls, batch_size=config.batch_size)
        for meta in enriched:
            db.upsert_repo(
                conn,
                url=meta.get("url", ""),
                name=meta.get("name", ""),
                description=meta.get("description", ""),
                stars=meta.get("stars", 0),
                forks=meta.get("forks", 0),
                last_repo_commit=meta.get("last_repo_commit", ""),
                license=meta.get("license", ""),
                topics=meta.get("topics"),
            )
            result.urls_enriched += 1

    # ------------------------------------------------------------------
    # Phase 3: Find similarities
    # ------------------------------------------------------------------
    if similarity_candidates:
        sim_results = similarity.find_similarities(similarity_candidates)
        for sim in sim_results:
            # Use executemany-style batch insert; commit once at the end
            conn.execute(
                """INSERT OR REPLACE INTO similarities
                   (component_a, component_b, similarity_score, similarity_type, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (sim["a"], sim["b"], sim["score"], sim["type"], sim.get("notes", "")),
            )
            result.similarities_found += 1
        conn.commit()

    return result
