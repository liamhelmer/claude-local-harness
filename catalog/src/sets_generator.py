"""Generate curated markdown sets for project types and personas."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

PROJECT_TYPE_LABELS = {
    "devops": "DevOps",
    "app-deploy": "Application Deployment",
    "policy-as-code": "Policy as Code",
    "docs": "Documentation",
    "sales-marketing": "Sales & Marketing",
    "big-data": "Big Data",
    "finops": "FinOps",
}

PERSONA_LABELS = {
    "platform-engineer": "Platform Engineer",
    "cloud-sre": "Cloud Engineer / SRE",
    "data-engineer": "Data Engineer",
    "ml-engineer": "ML Engineer",
    "sales": "Sales",
    "marketing": "Marketing",
    "accounting": "Accounting",
    "director-vp": "Director / VP",
}

# Section ordering for project sets
_PROJECT_SECTIONS = [
    "plugin",
    "skill",
    "agent",
    "hook",
    "mcp-server",
]

# Section ordering for persona sets
_PERSONA_SECTIONS = [
    "plugin",
    "skill",
    "agent",
    "hook",
    "mcp-server",
]

_SECTION_HEADINGS = {
    "plugin": "Recommended Plugins",
    "skill": "Recommended Skills",
    "agent": "Recommended Agents",
    "hook": "Recommended Hooks",
    "mcp-server": "Recommended MCP Servers",
}

_PERSONA_SECTION_HEADINGS = {
    "plugin": "Always-On Plugins",
    "skill": "Recommended Skills",
    "agent": "Recommended Agents",
    "hook": "Recommended Hooks",
    "mcp-server": "Recommended MCP Servers",
}


def _truncate(text: str, length: int = 200) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def _parse_json_field(value) -> list:
    """Safely parse a JSON field that may be a string, list, or None."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ---------------------------------------------------------------------------
# DB query (minimal catalog_recommend replacement)
# ---------------------------------------------------------------------------


def catalog_recommend(
    conn: sqlite3.Connection,
    *,
    project_type: Optional[str] = None,
    persona: Optional[str] = None,
) -> list[dict]:
    """Query components matching a project_type or persona.

    Returns a list of dicts with component + repo info.
    This is a local implementation; if catalog.src.mcp_tools exists
    with a catalog_recommend function, prefer that instead.
    """
    rows = conn.execute(
        """
        SELECT c.*, r.url AS repo_url, r.name AS repo_name,
               r.stars AS repo_stars, r.is_local AS repo_is_local
        FROM components c
        JOIN repos r ON r.id = c.repo_id
        WHERE c.tombstoned = 0
        ORDER BY r.stars DESC, c.name ASC
        """,
    ).fetchall()

    results = []
    for row in rows:
        row_dict = dict(row)
        project_types = _parse_json_field(row_dict.get("project_types"))
        personas = _parse_json_field(row_dict.get("personas"))

        if project_type and project_type not in project_types:
            continue
        if persona and persona not in personas:
            continue

        results.append(row_dict)

    return results


# ---------------------------------------------------------------------------
# Similarity / alternatives lookup
# ---------------------------------------------------------------------------


def _get_alternatives(conn: sqlite3.Connection, comp_id: int) -> list[str]:
    """Return names of similar components."""
    cur = conn.execute(
        """
        SELECT c.name
        FROM similarities s
        JOIN components c
          ON c.id = CASE
               WHEN s.component_a = ? THEN s.component_b
               ELSE s.component_a
             END
        WHERE (s.component_a = ? OR s.component_b = ?)
          AND c.tombstoned = 0
        """,
        (comp_id, comp_id, comp_id),
    )
    return [r["name"] for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Markdown rendering helpers
# ---------------------------------------------------------------------------


def _render_component(comp: dict, alternatives: list[str]) -> str:
    """Render a single component as a markdown list item."""
    name = comp.get("name", "unknown")
    ctype = comp.get("type", "unknown")
    stars = comp.get("repo_stars", 0) or 0
    repo_url = comp.get("repo_url", "")
    last_update = comp.get("file_last_commit", "")
    desc = _truncate(comp.get("description", "") or "")

    parts = [f"- **{name}** ({ctype})"]
    meta_parts = []
    if stars:
        meta_parts.append(f"{stars} stars")
    if repo_url:
        meta_parts.append(f"[source]({repo_url})")
    if last_update:
        meta_parts.append(f"updated {last_update}")
    if meta_parts:
        parts.append(f"  {' | '.join(meta_parts)}")
    if desc:
        parts.append(f"  {desc}")
    if alternatives:
        parts.append(f"  Alternatives: {', '.join(alternatives)}")

    return "\n".join(parts)


def _group_by_type(components: list[dict]) -> dict[str, list[dict]]:
    """Group component dicts by their type field."""
    groups: dict[str, list[dict]] = {}
    for comp in components:
        ctype = comp.get("type", "other")
        groups.setdefault(ctype, []).append(comp)
    return groups


# ---------------------------------------------------------------------------
# Public generators
# ---------------------------------------------------------------------------


def generate_project_set(conn: sqlite3.Connection, project_type: str) -> str:
    """Generate a markdown toolkit document for a project type."""
    label = PROJECT_TYPE_LABELS.get(project_type, project_type.title())
    components = catalog_recommend(conn, project_type=project_type)
    groups = _group_by_type(components)

    lines = [f"# {label} Toolkit", ""]

    has_content = False
    # Render known sections in order
    for section_key in _PROJECT_SECTIONS:
        heading = _SECTION_HEADINGS.get(section_key, section_key.title())
        if section_key in groups:
            has_content = True
            lines.append(f"## {heading}")
            lines.append("")
            for comp in groups[section_key]:
                alts = _get_alternatives(conn, comp["id"])
                lines.append(_render_component(comp, alts))
                lines.append("")

    # Render any remaining types not in the predefined list
    for ctype, comps in groups.items():
        if ctype not in _PROJECT_SECTIONS:
            has_content = True
            lines.append(f"## Recommended {ctype.title()}s")
            lines.append("")
            for comp in comps:
                alts = _get_alternatives(conn, comp["id"])
                lines.append(_render_component(comp, alts))
                lines.append("")

    if not has_content:
        lines.append("## Gaps")
        lines.append("")
        lines.append("No components found for this project type yet.")
        lines.append("")

    return "\n".join(lines)


def generate_persona_set(conn: sqlite3.Connection, persona: str) -> str:
    """Generate a markdown setup document for a persona."""
    label = PERSONA_LABELS.get(persona, persona.title())
    components = catalog_recommend(conn, persona=persona)
    groups = _group_by_type(components)

    lines = [f"# {label} Setup", ""]

    has_content = False
    for section_key in _PERSONA_SECTIONS:
        heading = _PERSONA_SECTION_HEADINGS.get(section_key, section_key.title())
        if section_key in groups:
            has_content = True
            lines.append(f"## {heading}")
            lines.append("")
            for comp in groups[section_key]:
                alts = _get_alternatives(conn, comp["id"])
                lines.append(_render_component(comp, alts))
                lines.append("")

    # Render any remaining types
    for ctype, comps in groups.items():
        if ctype not in _PERSONA_SECTIONS:
            has_content = True
            lines.append(f"## {ctype.title()}")
            lines.append("")
            for comp in comps:
                alts = _get_alternatives(conn, comp["id"])
                lines.append(_render_component(comp, alts))
                lines.append("")

    if not has_content:
        lines.append("## Gaps")
        lines.append("")
        lines.append("No components found for this persona yet.")
        lines.append("")

    return "\n".join(lines)


def generate_all_sets(conn: sqlite3.Connection, output_dir: Path) -> None:
    """Generate all project-type and persona markdown files into output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 7 project type files
    for slug in PROJECT_TYPE_LABELS:
        md = generate_project_set(conn, slug)
        (output_dir / f"{slug}-toolkit.md").write_text(md)

    # 8 persona files
    for slug in PERSONA_LABELS:
        md = generate_persona_set(conn, slug)
        (output_dir / f"{slug}.md").write_text(md)
