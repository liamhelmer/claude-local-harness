"""Integration tests — run the full pipeline against the real 24+ local repos."""

import pytest
from pathlib import Path

# Scanning 26 real repos with git-log-per-file is slow; allow 10 minutes.
pytestmark = pytest.mark.timeout(600)

from catalog.src.db import init_db, get_tombstoned
from catalog.src.ingest import IngestConfig, run_ingestion
from catalog.src.mcp_tools import catalog_search, catalog_recommend, catalog_stats
from catalog.src.sets_generator import generate_all_sets

REPOS_DIR = Path("/Users/liam.helmer/repos/claude-local-harness/repositories")


@pytest.fixture(scope="module")
def integrated_db(tmp_path_factory):
    """Run full ingestion against real repos once, share across all tests."""
    if not REPOS_DIR.exists():
        pytest.skip("Local repos directory not available")

    db_path = tmp_path_factory.mktemp("integration") / "integration.db"
    conn = init_db(str(db_path))

    config = IngestConfig(
        repos_dir=REPOS_DIR,
        db_conn=conn,
        pull_repos=False,
        enrich_github=False,
        run_classifier=True,
    )
    result = run_ingestion(config)
    yield conn, result
    conn.close()


# ---------------------------------------------------------------------------
# TestIntegrationIngestion
# ---------------------------------------------------------------------------


class TestIntegrationIngestion:
    def test_found_repos(self, integrated_db):
        """Should discover at least 20 repos."""
        _conn, result = integrated_db
        assert result.repos_scanned >= 20, f"Only found {result.repos_scanned} repos"

    def test_found_components(self, integrated_db):
        """Should find at least 50 components with skill and agent types."""
        conn, _result = integrated_db
        stats = catalog_stats(conn)
        assert (
            stats["total_components"] >= 50
        ), f"Only {stats['total_components']} components"
        assert (
            "skill" in stats["by_type"]
        ), f"No skills found. Types: {stats['by_type']}"
        assert (
            "agent" in stats["by_type"]
        ), f"No agents found. Types: {stats['by_type']}"

    def test_classified_some_devops(self, integrated_db):
        """Classifier should tag at least 1 component as devops."""
        conn, _result = integrated_db
        stats = catalog_stats(conn)
        devops_count = stats["by_project_type"].get("devops", 0)
        assert (
            devops_count >= 1
        ), f"No devops components. project_types: {stats['by_project_type']}"

    def test_tombstoned_suspicious(self, integrated_db):
        """Every tombstoned entry must have a reason."""
        conn, _result = integrated_db
        tombstoned = get_tombstoned(conn)
        for row in tombstoned:
            assert row[
                "tombstone_reason"
            ], f"Tombstoned component id={row['id']} name={row['name']} has no reason"


# ---------------------------------------------------------------------------
# TestIntegrationSearch
# ---------------------------------------------------------------------------


class TestIntegrationSearch:
    def test_search_terraform(self, integrated_db):
        """Searching 'terraform' should return at least 1 result."""
        conn, _result = integrated_db
        results = catalog_search(conn, query="terraform")
        assert len(results) >= 1, "No results for 'terraform' search"

    def test_search_by_type(self, integrated_db):
        """Filtering by type='skill' should return at least 10 results."""
        conn, _result = integrated_db
        results = catalog_search(conn, type="skill", limit=100)
        assert len(results) >= 10, f"Only {len(results)} skills found"

    def test_recommend_devops(self, integrated_db):
        """Recommending for project_type='devops' should return at least 1."""
        conn, _result = integrated_db
        results = catalog_recommend(conn, project_type="devops")
        assert len(results) >= 1, "No devops recommendations"


# ---------------------------------------------------------------------------
# TestIntegrationSetsGeneration
# ---------------------------------------------------------------------------


class TestIntegrationSetsGeneration:
    def test_generates_all_files(self, integrated_db, tmp_path):
        """Generate sets should write devops-toolkit.md and platform-engineer.md."""
        conn, _result = integrated_db
        generate_all_sets(conn, tmp_path)

        devops_path = tmp_path / "devops-toolkit.md"
        platform_path = tmp_path / "platform-engineer.md"

        assert devops_path.exists(), "devops-toolkit.md not generated"
        assert platform_path.exists(), "platform-engineer.md not generated"

        devops_content = devops_path.read_text()
        platform_content = platform_path.read_text()

        assert (
            len(devops_content) > 100
        ), f"devops-toolkit.md too short ({len(devops_content)} chars)"
        assert (
            len(platform_content) > 100
        ), f"platform-engineer.md too short ({len(platform_content)} chars)"


# ---------------------------------------------------------------------------
# TestReingestionIdempotency
# ---------------------------------------------------------------------------


class TestReingestionIdempotency:
    def test_second_run_skips(self, integrated_db):
        """Second ingestion run should add 0 and skip >= 80% of first run's added."""
        conn, first_result = integrated_db

        config = IngestConfig(
            repos_dir=REPOS_DIR,
            db_conn=conn,
            pull_repos=False,
            enrich_github=False,
            run_classifier=True,
        )
        second_result = run_ingestion(config)

        assert (
            second_result.components_added == 0
        ), f"Second run added {second_result.components_added} components"
        threshold = int(first_result.components_added * 0.8)
        assert second_result.components_skipped >= threshold, (
            f"Second run skipped {second_result.components_skipped}, "
            f"expected >= {threshold} (80% of {first_result.components_added})"
        )
