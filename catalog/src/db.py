"""SQLite database module for the catalog."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    name TEXT,
    description TEXT,
    stars INTEGER,
    forks INTEGER,
    last_repo_commit TEXT,
    license TEXT,
    topics JSON,
    is_local INTEGER DEFAULT 0,
    fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER REFERENCES repos(id),
    name TEXT,
    type TEXT,
    description TEXT,
    file_path TEXT,
    file_last_commit TEXT,
    file_last_author TEXT,
    version TEXT,
    triggers TEXT,
    tools_used JSON,
    metadata JSON,
    tags JSON,
    project_types JSON,
    personas JSON,
    source_url TEXT,
    content_hash TEXT,
    tombstoned INTEGER DEFAULT 0,
    tombstone_reason TEXT,
    last_ingested_at TEXT,
    UNIQUE(repo_id, file_path)
);

CREATE TABLE IF NOT EXISTS similarities (
    id INTEGER PRIMARY KEY,
    component_a INTEGER REFERENCES components(id),
    component_b INTEGER REFERENCES components(id),
    similarity_score REAL,
    similarity_type TEXT,
    notes TEXT,
    UNIQUE(component_a, component_b)
);

CREATE INDEX IF NOT EXISTS idx_components_type ON components(type);
CREATE INDEX IF NOT EXISTS idx_components_repo_id ON components(repo_id);
CREATE INDEX IF NOT EXISTS idx_components_tombstoned ON components(tombstoned);
CREATE INDEX IF NOT EXISTS idx_similarities_component_a ON similarities(component_a);
CREATE INDEX IF NOT EXISTS idx_similarities_component_b ON similarities(component_b);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class _SafeEncoder(json.JSONEncoder):
    """Handle date/datetime objects that YAML frontmatter parsing can produce."""

    def default(self, o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return super().default(o)


def _json_encode(val) -> Optional[str]:
    """Encode a value as JSON string if it is a list or dict, else return None."""
    if val is None:
        return None
    return json.dumps(val, cls=_SafeEncoder)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def init_db(db_path: str) -> sqlite3.Connection:
    """Create tables if not exist, return connection with row_factory=sqlite3.Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


# ---------------------------------------------------------------------------
# Repos
# ---------------------------------------------------------------------------


def insert_repo(
    conn: sqlite3.Connection,
    *,
    url: str,
    name: str,
    description: str = "",
    stars: int = 0,
    forks: int = 0,
    last_repo_commit: str = "",
    license: str = "",
    topics: Optional[list] = None,
    is_local: bool = False,
    fetched_at: str = "",
) -> int:
    """Insert a repo row, return its ID."""
    cur = conn.execute(
        """INSERT INTO repos (url, name, description, stars, forks,
                              last_repo_commit, license, topics, is_local, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            url,
            name,
            description,
            stars,
            forks,
            last_repo_commit,
            license,
            _json_encode(topics),
            int(is_local),
            fetched_at,
        ),
    )
    conn.commit()
    return cur.lastrowid


def upsert_repo(
    conn: sqlite3.Connection,
    *,
    url: str,
    name: str,
    description: str = "",
    stars: int = 0,
    forks: int = 0,
    last_repo_commit: str = "",
    license: str = "",
    topics: Optional[list] = None,
    is_local: bool = False,
    fetched_at: str = "",
) -> int:
    """Insert or update on conflict(url), return ID."""
    cur = conn.execute(
        """INSERT INTO repos (url, name, description, stars, forks,
                              last_repo_commit, license, topics, is_local, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(url) DO UPDATE SET
               name=excluded.name,
               description=excluded.description,
               stars=excluded.stars,
               forks=excluded.forks,
               last_repo_commit=excluded.last_repo_commit,
               license=excluded.license,
               topics=excluded.topics,
               is_local=excluded.is_local,
               fetched_at=excluded.fetched_at""",
        (
            url,
            name,
            description,
            stars,
            forks,
            last_repo_commit,
            license,
            _json_encode(topics),
            int(is_local),
            fetched_at,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_repo_by_url(conn: sqlite3.Connection, url: str) -> Optional[sqlite3.Row]:
    """Return a repo row by URL, or None."""
    cur = conn.execute("SELECT * FROM repos WHERE url = ?", (url,))
    return cur.fetchone()


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def insert_component(
    conn: sqlite3.Connection,
    *,
    repo_id: int,
    name: str,
    type: str,
    file_path: str,
    description: str = "",
    file_last_commit: str = "",
    file_last_author: str = "",
    version: str = "",
    triggers: str = "",
    tools_used: Optional[list] = None,
    metadata: Optional[dict] = None,
    tags: Optional[list] = None,
    project_types: Optional[list] = None,
    personas: Optional[list] = None,
    source_url: str = "",
    content_hash: str = "",
) -> int:
    """Insert a component with last_ingested_at timestamp, return its ID."""
    cur = conn.execute(
        """INSERT INTO components
           (repo_id, name, type, file_path, description,
            file_last_commit, file_last_author, version, triggers,
            tools_used, metadata, tags, project_types, personas,
            source_url, content_hash, last_ingested_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            repo_id,
            name,
            type,
            file_path,
            description,
            file_last_commit,
            file_last_author,
            version,
            triggers,
            _json_encode(tools_used),
            _json_encode(metadata),
            _json_encode(tags),
            _json_encode(project_types),
            _json_encode(personas),
            source_url,
            content_hash,
            _now_iso(),
        ),
    )
    conn.commit()
    return cur.lastrowid


_COMPONENT_UPDATABLE = frozenset(
    {
        "name",
        "type",
        "description",
        "file_path",
        "file_last_commit",
        "file_last_author",
        "version",
        "triggers",
        "tools_used",
        "metadata",
        "tags",
        "project_types",
        "personas",
        "source_url",
        "content_hash",
    }
)

_JSON_FIELDS = frozenset(
    {
        "tools_used",
        "metadata",
        "tags",
        "project_types",
        "personas",
    }
)


def update_component(conn: sqlite3.Connection, comp_id: int, **kwargs) -> None:
    """Update allowed fields on a component, auto-set last_ingested_at."""
    fields = {k: v for k, v in kwargs.items() if k in _COMPONENT_UPDATABLE}
    if not fields:
        return
    # JSON-encode any list/dict fields
    for key in _JSON_FIELDS:
        if key in fields:
            fields[key] = _json_encode(fields[key])
    fields["last_ingested_at"] = _now_iso()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [comp_id]
    conn.execute(
        f"UPDATE components SET {set_clause} WHERE id = ?",
        values,
    )
    conn.commit()


def get_component_by_path(
    conn: sqlite3.Connection, repo_id: int, file_path: str
) -> Optional[sqlite3.Row]:
    """Return a component row by repo_id + file_path. Returns None for tombstoned."""
    cur = conn.execute(
        "SELECT * FROM components WHERE repo_id = ? AND file_path = ? AND tombstoned = 0",
        (repo_id, file_path),
    )
    return cur.fetchone()


def should_update_component(
    existing_row: sqlite3.Row,
    *,
    new_commit: str = "",
    new_hash: str = "",
) -> bool:
    """Return True if content_hash or file_last_commit changed."""
    if new_hash and new_hash != existing_row["content_hash"]:
        return True
    if new_commit and new_commit != existing_row["file_last_commit"]:
        return True
    return False


# ---------------------------------------------------------------------------
# Tombstoning
# ---------------------------------------------------------------------------


def tombstone_component(conn: sqlite3.Connection, comp_id: int, reason: str) -> None:
    """Set tombstoned=1 and tombstone_reason on a component."""
    conn.execute(
        "UPDATE components SET tombstoned = 1, tombstone_reason = ? WHERE id = ?",
        (reason, comp_id),
    )
    conn.commit()


def get_tombstoned(conn: sqlite3.Connection) -> list:
    """Return all tombstoned components."""
    cur = conn.execute("SELECT * FROM components WHERE tombstoned = 1")
    return cur.fetchall()


# ---------------------------------------------------------------------------
# Similarities
# ---------------------------------------------------------------------------


def insert_similarity(
    conn: sqlite3.Connection,
    comp_a: int,
    comp_b: int,
    score: float,
    sim_type: str,
    notes: str = "",
) -> None:
    """INSERT OR REPLACE a similarity record."""
    conn.execute(
        """INSERT OR REPLACE INTO similarities
           (component_a, component_b, similarity_score, similarity_type, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (comp_a, comp_b, score, sim_type, notes),
    )
    conn.commit()


def get_similarities_for(conn: sqlite3.Connection, comp_id: int) -> list:
    """Get all similarities involving comp_id, joining to get the other component's name/path."""
    cur = conn.execute(
        """SELECT s.*,
                  c.name AS other_name,
                  c.file_path AS other_file_path
           FROM similarities s
           JOIN components c
             ON c.id = CASE
                  WHEN s.component_a = ? THEN s.component_b
                  ELSE s.component_a
                END
           WHERE s.component_a = ? OR s.component_b = ?""",
        (comp_id, comp_id, comp_id),
    )
    return cur.fetchall()
