import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from catalog.src.db import init_db
from catalog.src.ingest import IngestConfig, run_ingestion

DB_PATH = Path(__file__).parent.parent / "data" / "catalog.db"
REPOS_DIR = Path("/Users/liam.helmer/repos/claude-local-harness/repositories")


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = init_db(str(DB_PATH))
    config = IngestConfig(
        repos_dir=REPOS_DIR,
        db_conn=conn,
        pull_repos=True,
        enrich_github=True,
        run_classifier=True,
    )
    print(f"Scanning repos in {REPOS_DIR}...")
    result = run_ingestion(config)
    print(f"\n--- Ingestion Complete ---")
    print(f"Repos scanned: {result.repos_scanned}")
    print(f"Components added: {result.components_added}")
    print(f"Components updated: {result.components_updated}")
    print(f"Components skipped: {result.components_skipped}")
    print(f"Tombstoned: {result.tombstoned}")
    print(f"URLs extracted: {result.urls_extracted}")
    print(f"Similarities found: {result.similarities_found}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for e in result.errors[:10]:
            print(f"  - {e}")
    conn.close()


if __name__ == "__main__":
    main()
