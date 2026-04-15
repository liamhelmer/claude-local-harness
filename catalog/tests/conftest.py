import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Add parent to path so imports work
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database with schema."""
    db_path = tmp_path / "test_catalog.db"
    from catalog.src.db import init_db

    conn = init_db(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
def sample_repo(tmp_path):
    """Create a minimal fake repo structure for testing."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    # plugin.json
    plugin_dir = repo / ".claude-plugin"
    plugin_dir.mkdir()
    import json

    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {"name": "test-plugin", "description": "A test plugin", "version": "1.0.0"}
        )
    )

    # skill
    skill_dir = repo / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-skill\ndescription: A test skill for terraform\ntags: [terraform, devops]\n---\n\n# Test Skill\n\nDoes terraform things.\n"
    )

    # agent
    agent_dir = repo / "agents"
    agent_dir.mkdir()
    (agent_dir / "test-agent.md").write_text(
        "---\nname: test-agent\ndescription: A test agent for kubernetes deployment\nmodel: sonnet\ntools: [Bash, Read]\n---\n\n# Test Agent\n\nDeploys to k8s.\n"
    )

    # README with GitHub links
    (repo / "README.md").write_text(
        "# Test Repo\n\nSee also:\n- https://github.com/obra/superpowers\n- https://github.com/anthropics/claude-code\n"
    )

    return repo


@pytest.fixture
def local_repos_dir():
    """Point to the actual local repos for integration tests."""
    path = Path("/Users/liam.helmer/repos/claude-local-harness/repositories")
    if path.exists():
        return path
    pytest.skip("Local repos directory not available")
