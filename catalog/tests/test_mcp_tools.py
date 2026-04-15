"""Tests for catalog.src.mcp_tools — MCP query logic."""

import json
import sqlite3

import pytest

from catalog.src.db import (
    init_db,
    insert_component,
    insert_repo,
    insert_similarity,
    tombstone_component,
)
from catalog.src.mcp_tools import (
    catalog_recommend,
    catalog_search,
    catalog_similar,
    catalog_stats,
)


@pytest.fixture
def populated_db(tmp_path):
    """Create a DB with 2 repos, 3 live components, 1 tombstoned, and 1 similarity."""
    db_path = tmp_path / "test_catalog.db"
    conn = init_db(str(db_path))

    # Repo 1: local, 500 stars
    repo1 = insert_repo(
        conn,
        url="https://github.com/acme/infra-tools",
        name="infra-tools",
        description="Infrastructure automation tools",
        stars=500,
        forks=50,
        is_local=True,
    )

    # Repo 2: external, 100 stars
    repo2 = insert_repo(
        conn,
        url="https://github.com/external/k8s-ops",
        name="k8s-ops",
        description="Kubernetes operations toolkit",
        stars=100,
        forks=10,
        is_local=False,
    )

    # Component 1: terraform-skill (skill, devops, platform-engineer)
    c1 = insert_component(
        conn,
        repo_id=repo1,
        name="terraform-skill",
        type="skill",
        file_path="skills/terraform/SKILL.md",
        description="Terraform infrastructure provisioning skill",
        file_last_commit="2026-03-01T00:00:00Z",
        tags=["terraform", "iac", "devops"],
        project_types=["devops"],
        personas=["platform-engineer"],
        content_hash="hash_tf",
    )

    # Component 2: k8s-deploy (agent, app-deploy+devops, platform-engineer+cloud-sre)
    c2 = insert_component(
        conn,
        repo_id=repo2,
        name="k8s-deploy",
        type="agent",
        file_path="agents/k8s-deploy.md",
        description="Kubernetes deployment agent for managing clusters",
        file_last_commit="2026-04-01T00:00:00Z",
        tags=["kubernetes", "deployment"],
        project_types=["app-deploy", "devops"],
        personas=["platform-engineer", "cloud-sre"],
        content_hash="hash_k8s",
    )

    # Component 3: tf-reviewer (skill, devops, platform-engineer)
    c3 = insert_component(
        conn,
        repo_id=repo1,
        name="tf-reviewer",
        type="skill",
        file_path="skills/tf-reviewer/SKILL.md",
        description="Reviews terraform plans for best practices",
        file_last_commit="2026-02-01T00:00:00Z",
        tags=["terraform", "review", "devops"],
        project_types=["devops"],
        personas=["platform-engineer"],
        content_hash="hash_tfr",
    )

    # Component 4: evil-skill (tombstoned)
    c4 = insert_component(
        conn,
        repo_id=repo1,
        name="evil-skill",
        type="skill",
        file_path="skills/evil/SKILL.md",
        description="A malicious skill that should be hidden",
        tags=["evil"],
        project_types=["devops"],
        personas=["platform-engineer"],
        content_hash="hash_evil",
    )
    tombstone_component(conn, c4, reason="Security violation")

    # Similarity: terraform-skill <-> tf-reviewer (score 0.82, same-purpose)
    insert_similarity(conn, comp_a=c1, comp_b=c3, score=0.82, sim_type="same-purpose")

    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# TestCatalogSearch
# ---------------------------------------------------------------------------
class TestCatalogSearch:
    def test_text_search(self, populated_db):
        """Search by query text matches name/description/tags."""
        results = catalog_search(populated_db, query="terraform")
        assert len(results) >= 2
        names = {r["name"] for r in results}
        assert "terraform-skill" in names
        assert "tf-reviewer" in names

    def test_filter_by_type(self, populated_db):
        """Filter by component type returns only that type."""
        results = catalog_search(populated_db, type="agent")
        assert len(results) == 1
        assert results[0]["name"] == "k8s-deploy"

    def test_filter_by_project_type(self, populated_db):
        """Filter by project_type uses json_each to match."""
        results = catalog_search(populated_db, project_type="app-deploy")
        assert len(results) == 1
        assert results[0]["name"] == "k8s-deploy"

    def test_filter_by_persona(self, populated_db):
        """Filter by persona uses json_each to match."""
        results = catalog_search(populated_db, persona="cloud-sre")
        assert len(results) == 1
        assert results[0]["name"] == "k8s-deploy"

    def test_excludes_tombstoned(self, populated_db):
        """Search never returns tombstoned components."""
        results = catalog_search(populated_db, query="evil")
        assert len(results) == 0

    def test_sort_by_stars(self, populated_db):
        """Sort by stars puts higher-star repo components first."""
        results = catalog_search(populated_db, sort_by="stars")
        assert len(results) >= 2
        # First result should be from repo with 500 stars
        assert results[0]["name"] in ("terraform-skill", "tf-reviewer")

    def test_min_stars(self, populated_db):
        """min_stars filters out repos below the threshold."""
        results = catalog_search(populated_db, min_stars=200)
        names = {r["name"] for r in results}
        assert "k8s-deploy" not in names
        assert "terraform-skill" in names


# ---------------------------------------------------------------------------
# TestCatalogRecommend
# ---------------------------------------------------------------------------
class TestCatalogRecommend:
    def test_recommend_devops(self, populated_db):
        """Recommend for devops project_type returns results."""
        results = catalog_recommend(populated_db, project_type="devops")
        assert len(results) >= 1

    def test_recommend_persona(self, populated_db):
        """Recommend for platform-engineer persona returns results."""
        results = catalog_recommend(populated_db, persona="platform-engineer")
        assert len(results) >= 1

    def test_collapses_duplicates(self, populated_db):
        """Similar terraform skills should be collapsed with alternatives."""
        results = catalog_recommend(populated_db, project_type="devops")
        # Find the primary terraform-related entry
        tf_entries = [
            r
            for r in results
            if "terraform" in r["name"].lower() or "tf" in r["name"].lower()
        ]
        # At least one should have alternatives
        has_alternatives = any(r.get("alternatives") for r in tf_entries)
        assert (
            has_alternatives
        ), f"Expected alternatives in terraform entries: {tf_entries}"


# ---------------------------------------------------------------------------
# TestCatalogSimilar
# ---------------------------------------------------------------------------
class TestCatalogSimilar:
    def test_finds_similar(self, populated_db):
        """catalog_similar returns the similar component with correct score."""
        # Get terraform-skill's ID
        cur = populated_db.execute(
            "SELECT id FROM components WHERE name = 'terraform-skill'"
        )
        comp_id = cur.fetchone()["id"]

        results = catalog_similar(populated_db, comp_id)
        assert len(results) >= 1
        match = [r for r in results if r["name"] == "tf-reviewer"]
        assert len(match) == 1
        assert match[0]["similarity_score"] == pytest.approx(0.82)
        assert match[0]["similarity_type"] == "same-purpose"


# ---------------------------------------------------------------------------
# TestCatalogStats
# ---------------------------------------------------------------------------
class TestCatalogStats:
    def test_returns_totals(self, populated_db):
        """catalog_stats returns correct totals."""
        stats = catalog_stats(populated_db)
        assert stats["total_components"] == 3  # excludes tombstoned
        assert stats["total_repos"] == 2
        assert stats["tombstoned_count"] == 1

    def test_by_type(self, populated_db):
        """catalog_stats has by_type with 'skill' count."""
        stats = catalog_stats(populated_db)
        assert "skill" in stats["by_type"]
        assert stats["by_type"]["skill"] == 2

    def test_by_project_type(self, populated_db):
        """catalog_stats has by_project_type counts."""
        stats = catalog_stats(populated_db)
        assert "devops" in stats["by_project_type"]

    def test_by_persona(self, populated_db):
        """catalog_stats has by_persona counts."""
        stats = catalog_stats(populated_db)
        assert "platform-engineer" in stats["by_persona"]
