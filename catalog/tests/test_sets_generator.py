"""Tests for catalog.src.sets_generator — toolkit and persona set generation."""

import json
import pytest

from catalog.src.db import init_db, insert_repo, insert_component
from catalog.src.sets_generator import (
    generate_all_sets,
    generate_persona_set,
    generate_project_set,
)


@pytest.fixture
def catalog_db(tmp_path):
    """Seed a DB with 2 repos and 3 components spanning different project types/personas."""
    db_path = tmp_path / "catalog.db"
    conn = init_db(str(db_path))

    # r1: local repo with 500 stars
    r1 = insert_repo(
        conn,
        url="https://github.com/acme/local-tools",
        name="local-tools",
        description="Local tooling repo",
        stars=500,
        is_local=True,
    )

    # r2: external repo with 100 stars
    r2 = insert_repo(
        conn,
        url="https://github.com/community/ext-tools",
        name="ext-tools",
        description="External tooling repo",
        stars=100,
        is_local=False,
    )

    # tf-skill: devops, platform-engineer
    insert_component(
        conn,
        repo_id=r1,
        name="tf-skill",
        type="skill",
        file_path="skills/tf-skill/SKILL.md",
        description="Terraform deployment skill for provisioning cloud infrastructure resources",
        project_types=["devops"],
        personas=["platform-engineer"],
        file_last_commit="2025-01-15",
    )

    # k8s-agent: devops+app-deploy, platform-engineer+cloud-sre
    insert_component(
        conn,
        repo_id=r1,
        name="k8s-agent",
        type="agent",
        file_path="agents/k8s-agent.md",
        description="Kubernetes deployment agent for managing containerized applications",
        project_types=["devops", "app-deploy"],
        personas=["platform-engineer", "cloud-sre"],
        file_last_commit="2025-02-20",
    )

    # dbt-runner: big-data, data-engineer
    insert_component(
        conn,
        repo_id=r2,
        name="dbt-runner",
        type="skill",
        file_path="skills/dbt-runner/SKILL.md",
        description="dbt runner skill for executing data transformations in a warehouse",
        project_types=["big-data"],
        personas=["data-engineer"],
        file_last_commit="2025-03-10",
    )

    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# TestGenerateProjectSet
# ---------------------------------------------------------------------------
class TestGenerateProjectSet:
    def test_produces_markdown(self, catalog_db):
        """devops set contains heading and both tf-skill and k8s-agent names."""
        md = generate_project_set(catalog_db, "devops")
        assert "# DevOps Toolkit" in md
        assert "tf-skill" in md
        assert "k8s-agent" in md

    def test_excludes_unrelated(self, catalog_db):
        """big-data set contains dbt-runner but not tf-skill."""
        md = generate_project_set(catalog_db, "big-data")
        assert "dbt-runner" in md
        assert "tf-skill" not in md


# ---------------------------------------------------------------------------
# TestGeneratePersonaSet
# ---------------------------------------------------------------------------
class TestGeneratePersonaSet:
    def test_produces_markdown(self, catalog_db):
        """platform-engineer set contains heading and tf-skill."""
        md = generate_persona_set(catalog_db, "platform-engineer")
        assert "# Platform Engineer Setup" in md
        assert "tf-skill" in md


# ---------------------------------------------------------------------------
# TestGenerateAllSets
# ---------------------------------------------------------------------------
class TestGenerateAllSets:
    def test_writes_files(self, catalog_db, tmp_path):
        """Generates files; devops-toolkit.md and platform-engineer.md exist with content."""
        out = tmp_path / "sets"
        generate_all_sets(catalog_db, out)

        devops_file = out / "devops-toolkit.md"
        persona_file = out / "platform-engineer.md"

        assert devops_file.exists()
        assert persona_file.exists()
        assert len(devops_file.read_text()) > 100
