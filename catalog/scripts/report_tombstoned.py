"""Generate a human-readable report of all tombstoned (suspicious) components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from catalog.src.db import init_db

DB_PATH = Path(__file__).parent.parent / "data" / "catalog.db"
REPORT_PATH = (
    Path(__file__).parent.parent.parent / "docs" / "plans" / "tombstoned-report.md"
)


def main():
    conn = init_db(str(DB_PATH))

    tombstoned = conn.execute(
        """
        SELECT c.name, c.type, c.file_path, c.tombstone_reason,
               c.file_last_commit, c.file_last_author,
               r.name as repo_name, r.url as repo_url
        FROM components c
        JOIN repos r ON r.id = c.repo_id
        WHERE c.tombstoned = 1
        ORDER BY r.name, c.file_path
    """
    ).fetchall()

    lines = [
        "# Tombstoned Components Report",
        "",
        f"**Total flagged:** {len(tombstoned)} components",
        "",
        "These components were automatically flagged during ingestion because they contain",
        "suspicious patterns (arbitrary code execution, secret exfiltration, permission bypass,",
        "etc.). They are excluded from search results and recommendations.",
        "",
        "To un-tombstone a component, manually update the database:",
        "```sql",
        "UPDATE components SET tombstoned = 0, tombstone_reason = NULL WHERE id = <id>;",
        "```",
        "",
        "---",
        "",
    ]

    # Group by repo
    by_repo = {}
    for row in tombstoned:
        repo = row["repo_name"]
        by_repo.setdefault(repo, []).append(row)

    for repo_name in sorted(by_repo.keys()):
        components = by_repo[repo_name]
        lines.append(f"## {repo_name} ({len(components)} flagged)")
        lines.append("")

        for comp in components:
            lines.append(f"### {comp['name']} ({comp['type']})")
            lines.append(f"- **File:** `{comp['file_path']}`")
            if comp["file_last_author"]:
                lines.append(f"- **Last author:** {comp['file_last_author']}")
            if comp["file_last_commit"]:
                lines.append(f"- **Last commit:** {comp['file_last_commit'][:10]}")
            lines.append(f"- **Findings:**")
            for finding in comp["tombstone_reason"].split("; "):
                lines.append(f"  - {finding}")
            lines.append("")

    report = "\n".join(lines)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
    print(f"Total tombstoned: {len(tombstoned)} across {len(by_repo)} repos")

    # Print summary to stdout
    print("\n--- Top reasons ---")
    reason_counts = {}
    for row in tombstoned:
        for finding in row["tombstone_reason"].split("; "):
            finding = finding.strip()
            if finding:
                reason_counts[finding] = reason_counts.get(finding, 0) + 1
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {count:4d}x  {reason}")

    conn.close()


if __name__ == "__main__":
    main()
