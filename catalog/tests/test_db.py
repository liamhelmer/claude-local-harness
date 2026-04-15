"""Tests for catalog.src.db — SQLite database module."""

import json
import sqlite3

import pytest

from catalog.src.db import (
    get_component_by_path,
    get_repo_by_url,
    get_similarities_for,
    get_tombstoned,
    init_db,
    insert_component,
    insert_repo,
    insert_similarity,
    should_update_component,
    tombstone_component,
    update_component,
    upsert_repo,
)


# ---------------------------------------------------------------------------
# TestInitDb
# ---------------------------------------------------------------------------
class TestInitDb:
    def test_creates_tables(self, tmp_db):
        """init_db creates repos, components, and similarities tables."""
        cursor = tmp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = sorted(row["name"] for row in cursor.fetchall())
        assert "components" in tables
        assert "repos" in tables
        assert "similarities" in tables

    def test_idempotent(self, tmp_path):
        """Calling init_db twice on the same path doesn't raise."""
        db_path = str(tmp_path / "idem.db")
        conn1 = init_db(db_path)
        conn2 = init_db(db_path)
        # Both connections should work
        assert conn1.execute("SELECT count(*) FROM repos").fetchone()[0] == 0
        assert conn2.execute("SELECT count(*) FROM repos").fetchone()[0] == 0
        conn1.close()
        conn2.close()


# ---------------------------------------------------------------------------
# TestRepos
# ---------------------------------------------------------------------------
class TestRepos:
    def test_insert_and_get(self, tmp_db):
        """insert_repo returns an ID, get_repo_by_url retrieves the row."""
        repo_id = insert_repo(
            tmp_db,
            url="https://github.com/example/repo",
            name="repo",
            description="A test repo",
            stars=42,
            forks=5,
            last_repo_commit="abc123",
            license="MIT",
            topics=["python", "testing"],
            is_local=False,
            fetched_at="2026-01-01T00:00:00Z",
        )
        assert isinstance(repo_id, int)

        row = get_repo_by_url(tmp_db, "https://github.com/example/repo")
        assert row is not None
        assert row["name"] == "repo"
        assert row["stars"] == 42
        assert row["license"] == "MIT"
        assert json.loads(row["topics"]) == ["python", "testing"]

    def test_upsert_updates_existing(self, tmp_db):
        """upsert_repo updates an existing repo on URL conflict."""
        insert_repo(
            tmp_db,
            url="https://github.com/example/repo",
            name="repo",
            stars=10,
        )
        new_id = upsert_repo(
            tmp_db,
            url="https://github.com/example/repo",
            name="repo-updated",
            stars=100,
        )
        row = get_repo_by_url(tmp_db, "https://github.com/example/repo")
        assert row["name"] == "repo-updated"
        assert row["stars"] == 100
        assert row["id"] == new_id


# ---------------------------------------------------------------------------
# TestComponents
# ---------------------------------------------------------------------------
class TestComponents:
    def _make_repo(self, conn):
        return insert_repo(conn, url="https://github.com/test/repo", name="repo")

    def test_insert_and_get_with_content_hash(self, tmp_db):
        """insert_component stores content_hash; retrievable by path."""
        repo_id = self._make_repo(tmp_db)
        comp_id = insert_component(
            tmp_db,
            repo_id=repo_id,
            name="my-skill",
            type="skill",
            file_path="skills/my-skill/SKILL.md",
            description="A skill",
            content_hash="sha256:abc123",
        )
        assert isinstance(comp_id, int)

        row = get_component_by_path(tmp_db, repo_id, "skills/my-skill/SKILL.md")
        assert row is not None
        assert row["content_hash"] == "sha256:abc123"
        assert row["name"] == "my-skill"
        assert row["last_ingested_at"] is not None  # auto-set

    def test_should_update_detects_change(self, tmp_db):
        """should_update_component returns True when hash differs, False when same."""
        repo_id = self._make_repo(tmp_db)
        insert_component(
            tmp_db,
            repo_id=repo_id,
            name="comp",
            type="skill",
            file_path="skills/comp/SKILL.md",
            content_hash="hash_v1",
            file_last_commit="commit_a",
        )
        existing = get_component_by_path(tmp_db, repo_id, "skills/comp/SKILL.md")

        # Same hash and commit -> no update needed
        assert (
            should_update_component(existing, new_commit="commit_a", new_hash="hash_v1")
            is False
        )

        # Different hash -> update needed
        assert (
            should_update_component(existing, new_commit="commit_a", new_hash="hash_v2")
            is True
        )

        # Different commit -> update needed
        assert (
            should_update_component(existing, new_commit="commit_b", new_hash="hash_v1")
            is True
        )


# ---------------------------------------------------------------------------
# TestTombstoning
# ---------------------------------------------------------------------------
class TestTombstoning:
    def _setup(self, conn):
        repo_id = insert_repo(conn, url="https://github.com/test/tomb", name="tomb")
        comp_id = insert_component(
            conn,
            repo_id=repo_id,
            name="dead-skill",
            type="skill",
            file_path="skills/dead/SKILL.md",
            content_hash="hash1",
        )
        return repo_id, comp_id

    def test_tombstone_and_list(self, tmp_db):
        """tombstone_component marks it; get_tombstoned returns name and reason."""
        repo_id, comp_id = self._setup(tmp_db)
        tombstone_component(tmp_db, comp_id, reason="File deleted")

        tombstoned = get_tombstoned(tmp_db)
        assert len(tombstoned) == 1
        assert tombstoned[0]["name"] == "dead-skill"
        assert tombstoned[0]["tombstone_reason"] == "File deleted"

    def test_tombstoned_excluded_from_normal_queries(self, tmp_db):
        """get_component_by_path returns None for tombstoned components."""
        repo_id, comp_id = self._setup(tmp_db)
        tombstone_component(tmp_db, comp_id, reason="Removed")

        row = get_component_by_path(tmp_db, repo_id, "skills/dead/SKILL.md")
        assert row is None


# ---------------------------------------------------------------------------
# TestSimilarities
# ---------------------------------------------------------------------------
class TestSimilarities:
    def _setup(self, conn):
        repo_id = insert_repo(conn, url="https://github.com/test/sim", name="sim")
        a = insert_component(
            conn,
            repo_id=repo_id,
            name="comp-a",
            type="skill",
            file_path="skills/a/SKILL.md",
            content_hash="ha",
        )
        b = insert_component(
            conn,
            repo_id=repo_id,
            name="comp-b",
            type="skill",
            file_path="skills/b/SKILL.md",
            content_hash="hb",
        )
        return a, b

    def test_insert_and_get(self, tmp_db):
        """insert_similarity stores a score; get_similarities_for retrieves it."""
        a, b = self._setup(tmp_db)
        insert_similarity(tmp_db, comp_a=a, comp_b=b, score=0.87, sim_type="cosine")

        sims = get_similarities_for(tmp_db, a)
        assert len(sims) >= 1
        match = [s for s in sims if s["similarity_score"] == pytest.approx(0.87)]
        assert len(match) == 1
