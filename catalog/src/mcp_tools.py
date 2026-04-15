"""MCP query logic for the catalog — separated from transport."""

from __future__ import annotations

import json
import sqlite3
from typing import Optional


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, decoding JSON fields."""
    d = dict(row)
    for key in (
        "tags",
        "project_types",
        "personas",
        "tools_used",
        "metadata",
        "topics",
    ):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ---------------------------------------------------------------------------
# catalog_search
# ---------------------------------------------------------------------------


def catalog_search(
    conn: sqlite3.Connection,
    *,
    query: str = "",
    type: str = "",
    project_type: str = "",
    persona: str = "",
    min_stars: int = 0,
    sort_by: str = "relevance",
    limit: int = 20,
) -> list[dict]:
    """Search the catalog with filters. Returns list of dicts."""
    conditions = ["c.tombstoned = 0"]
    params: list = []

    if query:
        conditions.append("(c.name LIKE ? OR c.description LIKE ? OR c.tags LIKE ?)")
        pattern = f"%{query}%"
        params.extend([pattern, pattern, pattern])

    if type:
        conditions.append("c.type = ?")
        params.append(type)

    if project_type:
        conditions.append(
            "EXISTS (SELECT 1 FROM json_each(c.project_types) WHERE json_each.value = ?)"
        )
        params.append(project_type)

    if persona:
        conditions.append(
            "EXISTS (SELECT 1 FROM json_each(c.personas) WHERE json_each.value = ?)"
        )
        params.append(persona)

    if min_stars:
        conditions.append("r.stars >= ?")
        params.append(min_stars)

    where = " AND ".join(conditions)

    sort_map = {
        "stars": "r.stars DESC",
        "recent": "c.file_last_commit DESC",
        "relevance": "r.stars DESC, c.file_last_commit DESC",
    }
    order = sort_map.get(sort_by, sort_map["relevance"])

    sql = f"""
        SELECT c.*, r.name AS repo_name, r.url AS repo_url, r.stars,
               (SELECT COUNT(*) FROM similarities s
                WHERE s.component_a = c.id OR s.component_b = c.id) AS similarity_count
        FROM components c
        JOIN repos r ON r.id = c.repo_id
        WHERE {where}
        ORDER BY {order}
        LIMIT ?
    """
    params.append(limit)

    cur = conn.execute(sql, params)
    return [_row_to_dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# catalog_recommend
# ---------------------------------------------------------------------------


def catalog_recommend(
    conn: sqlite3.Connection,
    *,
    project_type: str = "",
    persona: str = "",
) -> list[dict]:
    """Recommend components, collapsing similar ones into primary + alternatives."""
    results = catalog_search(
        conn,
        project_type=project_type,
        persona=persona,
        sort_by="stars",
        limit=100,
    )

    seen_ids: set[int] = set()
    collapsed: list[dict] = []

    for item in results:
        comp_id = item["id"]
        if comp_id in seen_ids:
            continue

        seen_ids.add(comp_id)

        # Find similar components for this item
        similar = catalog_similar(conn, comp_id)
        alternatives = []
        for sim in similar:
            other_id = sim["id"]
            if other_id not in seen_ids:
                seen_ids.add(other_id)
                alternatives.append(
                    {
                        "id": other_id,
                        "name": sim["name"],
                        "file_path": sim["file_path"],
                        "similarity_score": sim["similarity_score"],
                        "similarity_type": sim["similarity_type"],
                    }
                )

        item["alternatives"] = alternatives if alternatives else []
        collapsed.append(item)

    return collapsed


# ---------------------------------------------------------------------------
# catalog_similar
# ---------------------------------------------------------------------------


def catalog_similar(
    conn: sqlite3.Connection,
    component_id: int,
) -> list[dict]:
    """Return components similar to the given component_id."""
    sql = """
        SELECT
            c.id, c.name, c.file_path, c.file_last_commit,
            s.similarity_score, s.similarity_type, s.notes
        FROM similarities s
        JOIN components c ON c.id = CASE
            WHEN s.component_a = ? THEN s.component_b
            ELSE s.component_a
        END
        WHERE (s.component_a = ? OR s.component_b = ?)
          AND c.tombstoned = 0
    """
    cur = conn.execute(sql, (component_id, component_id, component_id))
    return [_row_to_dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# catalog_stats
# ---------------------------------------------------------------------------


def catalog_stats(conn: sqlite3.Connection) -> dict:
    """Return aggregate statistics about the catalog."""
    total = conn.execute(
        "SELECT COUNT(*) FROM components WHERE tombstoned = 0"
    ).fetchone()[0]

    total_repos = conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0]

    tombstoned_count = conn.execute(
        "SELECT COUNT(*) FROM components WHERE tombstoned = 1"
    ).fetchone()[0]

    # Counts by type
    by_type: dict[str, int] = {}
    cur = conn.execute(
        "SELECT type, COUNT(*) AS cnt FROM components WHERE tombstoned = 0 GROUP BY type"
    )
    for row in cur.fetchall():
        by_type[row[0]] = row[1]

    # Counts by project_type (using json_each)
    by_project_type: dict[str, int] = {}
    cur = conn.execute(
        """SELECT jt.value, COUNT(*) AS cnt
           FROM components c, json_each(c.project_types) jt
           WHERE c.tombstoned = 0
           GROUP BY jt.value"""
    )
    for row in cur.fetchall():
        by_project_type[row[0]] = row[1]

    # Counts by persona (using json_each)
    by_persona: dict[str, int] = {}
    cur = conn.execute(
        """SELECT jt.value, COUNT(*) AS cnt
           FROM components c, json_each(c.personas) jt
           WHERE c.tombstoned = 0
           GROUP BY jt.value"""
    )
    for row in cur.fetchall():
        by_persona[row[0]] = row[1]

    return {
        "total_components": total,
        "total_repos": total_repos,
        "tombstoned_count": tombstoned_count,
        "by_type": by_type,
        "by_project_type": by_project_type,
        "by_persona": by_persona,
    }
