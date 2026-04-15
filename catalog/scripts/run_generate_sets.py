import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from catalog.src.db import init_db
from catalog.src.mcp_tools import catalog_stats
from catalog.src.sets_generator import generate_all_sets

DB_PATH = Path(__file__).parent.parent / "data" / "catalog.db"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "plans" / "catalog-sets"


def main():
    conn = init_db(str(DB_PATH))
    stats = catalog_stats(conn)
    print(
        f"Catalog: {stats['total_components']} components, {stats['total_repos']} repos"
    )
    print(f"By type: {stats['by_type']}")
    print(f"By project type: {stats['by_project_type']}")
    print(f"Tombstoned: {stats['tombstoned_count']}")
    print(f"\nGenerating sets to {OUTPUT_DIR}...")
    generate_all_sets(conn, OUTPUT_DIR)
    print("Done! Files written:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size} bytes)")
    conn.close()


if __name__ == "__main__":
    main()
