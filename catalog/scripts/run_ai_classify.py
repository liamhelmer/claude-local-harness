"""AI classification pass for components with empty project_types/personas.

Two passes:
1. Enhanced keyword pass — searches full body content stored in metadata, not just name/description/tags
2. Repo-context pass — infers classification from the parent repo's other classified components
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from catalog.src.db import init_db, update_component
from catalog.src.classifier import keyword_classify, merge_classifications

DB_PATH = Path(__file__).parent.parent / "data" / "catalog.db"


def enhanced_keyword_classify(row):
    """Keyword classify using all available text, not just name/description/tags."""
    name = row["name"] or ""
    description = row["description"] or ""

    # Extract tags from JSON
    try:
        tags = json.loads(row["tags"]) if row["tags"] else []
    except (json.JSONDecodeError, TypeError):
        tags = []

    # Also search the metadata blob for additional keywords
    try:
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
    except (json.JSONDecodeError, TypeError):
        metadata = {}

    # Build extended text from metadata values
    extra_text_parts = []
    for key, val in metadata.items():
        if isinstance(val, str):
            extra_text_parts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    extra_text_parts.append(item)

    extended_description = f"{description} {' '.join(extra_text_parts)}"

    return keyword_classify(name=name, description=extended_description, tags=tags)


def repo_context_classify(conn, repo_id, existing_classification):
    """Infer classification from sibling components in the same repo."""
    siblings = conn.execute(
        """
        SELECT project_types, personas FROM components
        WHERE repo_id = ? AND tombstoned = 0
        AND (project_types != '[]' OR personas != '[]')
        LIMIT 50
    """,
        (repo_id,),
    ).fetchall()

    if not siblings:
        return existing_classification

    # Collect all project types and personas from siblings
    repo_project_types = set()
    repo_personas = set()
    for sib in siblings:
        try:
            pts = json.loads(sib["project_types"]) if sib["project_types"] else []
            repo_project_types.update(pts)
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            ps = json.loads(sib["personas"]) if sib["personas"] else []
            repo_personas.update(ps)
        except (json.JSONDecodeError, TypeError):
            pass

    # Only apply repo context if the component is truly unclassified
    if (
        not existing_classification["project_types"]
        and not existing_classification["personas"]
    ):
        return {
            "project_types": sorted(repo_project_types),
            "personas": sorted(repo_personas),
        }

    # If partially classified, merge
    return merge_classifications(
        existing_classification,
        {
            "project_types": sorted(repo_project_types),
            "personas": sorted(repo_personas),
        },
    )


def main():
    conn = init_db(str(DB_PATH))

    # Find unclassified components
    unclassified = conn.execute(
        """
        SELECT id, repo_id, name, description, tags, metadata, project_types, personas
        FROM components
        WHERE tombstoned = 0
        AND (project_types = '[]' OR project_types IS NULL)
        AND (personas = '[]' OR personas IS NULL)
    """
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM components WHERE tombstoned = 0"
    ).fetchone()[0]

    print(
        f"Unclassified: {len(unclassified)} / {total} components ({len(unclassified)*100//total}%)"
    )

    # Pass 1: Enhanced keyword classification
    pass1_classified = 0
    still_unclassified = []

    for row in unclassified:
        result = enhanced_keyword_classify(row)
        if result["project_types"] or result["personas"]:
            update_component(
                conn,
                row["id"],
                project_types=result["project_types"],
                personas=result["personas"],
            )
            pass1_classified += 1
        else:
            still_unclassified.append(row)

    print(f"Pass 1 (enhanced keywords): classified {pass1_classified}")

    # Pass 2: Repo-context classification
    pass2_classified = 0
    final_unclassified = 0

    for row in still_unclassified:
        current = {"project_types": [], "personas": []}
        result = repo_context_classify(conn, row["repo_id"], current)
        if result["project_types"] or result["personas"]:
            update_component(
                conn,
                row["id"],
                project_types=result["project_types"],
                personas=result["personas"],
            )
            pass2_classified += 1
        else:
            final_unclassified += 1

    print(f"Pass 2 (repo context): classified {pass2_classified}")
    print(f"Still unclassified: {final_unclassified}")

    # Print updated stats
    stats_by_pt = conn.execute(
        """
        SELECT json_each.value as pt, COUNT(DISTINCT c.id) as cnt
        FROM components c, json_each(c.project_types)
        WHERE c.tombstoned = 0
        GROUP BY json_each.value
        ORDER BY cnt DESC
    """
    ).fetchall()

    print("\n--- Classification coverage ---")
    for row in stats_by_pt:
        print(f"  {row['pt']:20s}  {row['cnt']:5d}")

    stats_by_persona = conn.execute(
        """
        SELECT json_each.value as p, COUNT(DISTINCT c.id) as cnt
        FROM components c, json_each(c.personas)
        WHERE c.tombstoned = 0
        GROUP BY json_each.value
        ORDER BY cnt DESC
    """
    ).fetchall()

    print("\n--- Persona coverage ---")
    for row in stats_by_persona:
        print(f"  {row['p']:20s}  {row['cnt']:5d}")

    conn.close()


if __name__ == "__main__":
    main()
