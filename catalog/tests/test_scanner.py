"""Tests for catalog.src.scanner — local repo scanner."""

import json
import os

import pytest

from catalog.src.scanner import (
    compute_content_hash,
    discover_components,
    discover_repos,
    extract_github_urls,
    parse_agent_md,
    parse_command_md,
    parse_hook_json,
    parse_plugin_json,
    parse_skill_md,
)


# ---------------------------------------------------------------------------
# TestDiscoverRepos
# ---------------------------------------------------------------------------
class TestDiscoverRepos:
    def test_finds_git_repos(self, tmp_path):
        """discover_repos returns dirs that contain .git subdirectory."""
        (tmp_path / "repo-a" / ".git").mkdir(parents=True)
        (tmp_path / "repo-b" / ".git").mkdir(parents=True)
        (tmp_path / "not-a-repo").mkdir()

        repos = discover_repos(tmp_path)
        names = [r.name for r in repos]
        assert "repo-a" in names
        assert "repo-b" in names
        assert "not-a-repo" not in names

    def test_skips_hidden_dirs(self, tmp_path):
        """Hidden directories (starting with .) are not returned."""
        (tmp_path / ".hidden-repo" / ".git").mkdir(parents=True)
        (tmp_path / "visible-repo" / ".git").mkdir(parents=True)

        repos = discover_repos(tmp_path)
        names = [r.name for r in repos]
        assert ".hidden-repo" not in names
        assert "visible-repo" in names

    def test_sorted_output(self, tmp_path):
        """Results are sorted alphabetically."""
        for name in ["zebra", "alpha", "middle"]:
            (tmp_path / name / ".git").mkdir(parents=True)

        repos = discover_repos(tmp_path)
        names = [r.name for r in repos]
        assert names == sorted(names)

    def test_skips_non_repos(self, tmp_path):
        """Directories without .git are not returned."""
        (tmp_path / "just-a-dir").mkdir()
        (tmp_path / "another-dir" / "subdir").mkdir(parents=True)

        repos = discover_repos(tmp_path)
        assert repos == []


# ---------------------------------------------------------------------------
# TestParsePluginJson
# ---------------------------------------------------------------------------
class TestParsePluginJson:
    def test_parses_valid(self, tmp_path):
        """Parses a complete plugin.json correctly."""
        p = tmp_path / "plugin.json"
        p.write_text(
            json.dumps(
                {
                    "name": "my-plugin",
                    "description": "Does things",
                    "version": "2.0.0",
                    "keywords": ["terraform", "gcp"],
                }
            )
        )
        result = parse_plugin_json(p)
        assert result["name"] == "my-plugin"
        assert result["description"] == "Does things"
        assert result["version"] == "2.0.0"
        assert result["keywords"] == ["terraform", "gcp"]

    def test_handles_missing_fields(self, tmp_path):
        """Missing optional fields default gracefully."""
        p = tmp_path / "plugin.json"
        p.write_text(json.dumps({"name": "minimal"}))

        result = parse_plugin_json(p)
        assert result["name"] == "minimal"
        assert result["description"] == ""
        assert result["version"] == ""
        assert result["keywords"] == []
        assert "metadata" in result


# ---------------------------------------------------------------------------
# TestParseSkillMd
# ---------------------------------------------------------------------------
class TestParseSkillMd:
    def test_parses_frontmatter(self, tmp_path):
        """Parses YAML frontmatter and body from SKILL.md."""
        p = tmp_path / "SKILL.md"
        p.write_text(
            "---\nname: terraform-skill\ndescription: Manages TF\ntags: [terraform]\ntools: [Bash]\nversion: 1.0.0\n---\n\n# Body\n\nContent here.\n"
        )
        result = parse_skill_md(p)
        assert result["name"] == "terraform-skill"
        assert result["description"] == "Manages TF"
        assert result["tags"] == ["terraform"]
        assert result["tools"] == ["Bash"]
        assert result["version"] == "1.0.0"
        assert "Body" in result["body"]

    def test_handles_no_frontmatter(self, tmp_path):
        """File without frontmatter delimiters still parses gracefully."""
        p = tmp_path / "SKILL.md"
        p.write_text("# Just a heading\n\nSome content.\n")

        result = parse_skill_md(p)
        assert result["name"] == ""
        assert result["description"] == ""
        assert result["tags"] == []
        assert "Just a heading" in result["body"]


# ---------------------------------------------------------------------------
# TestParseAgentMd
# ---------------------------------------------------------------------------
class TestParseAgentMd:
    def test_parses_agent_with_model_and_tools(self, tmp_path):
        """Agent .md with model, tools, and color parses correctly."""
        p = tmp_path / "deploy-agent.md"
        p.write_text(
            "---\nname: deploy-agent\ndescription: Deploys to k8s\nmodel: sonnet\ntools: [Bash, Read, Write]\ncolor: blue\n---\n\n# Deploy Agent\n\nDeploys stuff.\n"
        )
        result = parse_agent_md(p)
        assert result["name"] == "deploy-agent"
        assert result["description"] == "Deploys to k8s"
        assert result["model"] == "sonnet"
        assert result["tools"] == ["Bash", "Read", "Write"]
        assert result["color"] == "blue"
        assert "Deploy Agent" in result["body"]

    def test_handles_minimal_agent(self, tmp_path):
        """Agent with minimal frontmatter defaults gracefully."""
        p = tmp_path / "simple.md"
        p.write_text("---\nname: simple\n---\n\nJust an agent.\n")

        result = parse_agent_md(p)
        assert result["name"] == "simple"
        assert result["model"] == ""
        assert result["tools"] == []
        assert result["color"] == ""


# ---------------------------------------------------------------------------
# TestParseCommandMd
# ---------------------------------------------------------------------------
class TestParseCommandMd:
    def test_parses_command(self, tmp_path):
        """Command .md derives name from stem and extracts argument_hint."""
        p = tmp_path / "deploy.md"
        p.write_text(
            "---\ndescription: Deploy the app\nargument_hint: <environment>\n---\n\nRun deployment steps.\n"
        )
        result = parse_command_md(p)
        assert result["name"] == "deploy"
        assert result["description"] == "Deploy the app"
        assert result["argument_hint"] == "<environment>"
        assert "deployment steps" in result["body"]

    def test_command_no_frontmatter(self, tmp_path):
        """Command without frontmatter still has name from stem."""
        p = tmp_path / "hello.md"
        p.write_text("Just say hello.\n")

        result = parse_command_md(p)
        assert result["name"] == "hello"
        assert result["description"] == ""


# ---------------------------------------------------------------------------
# TestParseHookJson
# ---------------------------------------------------------------------------
class TestParseHookJson:
    def test_parses_hooks(self, tmp_path):
        """hooks.json parses event names."""
        p = tmp_path / "hooks.json"
        hooks_data = {
            "hooks": [
                {"event": "PreToolUse", "command": "echo pre"},
                {"event": "PostToolUse", "command": "echo post"},
                {"event": "Stop", "command": "echo stop"},
            ]
        }
        p.write_text(json.dumps(hooks_data))

        result = parse_hook_json(p)
        assert result["name"] == "hooks"
        assert sorted(result["events"]) == ["PostToolUse", "PreToolUse", "Stop"]

    def test_handles_empty_hooks(self, tmp_path):
        """Empty hooks.json returns empty events list."""
        p = tmp_path / "hooks.json"
        p.write_text(json.dumps({}))

        result = parse_hook_json(p)
        assert result["events"] == []


# ---------------------------------------------------------------------------
# TestExtractGithubUrls
# ---------------------------------------------------------------------------
class TestExtractGithubUrls:
    def test_extracts_urls(self, tmp_path):
        """Extracts GitHub owner/repo URLs from file content."""
        p = tmp_path / "README.md"
        p.write_text(
            "Check out https://github.com/obra/superpowers and "
            "also https://github.com/anthropics/claude-code for more.\n"
            "And this too: https://github.com/obra/superpowers (duplicate).\n"
        )
        urls = extract_github_urls(p)
        assert len(urls) == 2
        assert "https://github.com/anthropics/claude-code" in urls
        assert "https://github.com/obra/superpowers" in urls

    def test_deduplicates(self, tmp_path):
        """Duplicate URLs are removed."""
        p = tmp_path / "doc.md"
        p.write_text(
            "https://github.com/foo/bar\nhttps://github.com/foo/bar\nhttps://github.com/foo/bar\n"
        )
        urls = extract_github_urls(p)
        assert len(urls) == 1
        assert urls[0] == "https://github.com/foo/bar"

    def test_sorted(self, tmp_path):
        """URLs are returned sorted."""
        p = tmp_path / "doc.md"
        p.write_text("https://github.com/zzz/repo\nhttps://github.com/aaa/repo\n")
        urls = extract_github_urls(p)
        assert urls == sorted(urls)

    def test_no_urls(self, tmp_path):
        """File with no GitHub URLs returns empty list."""
        p = tmp_path / "empty.md"
        p.write_text("No links here.\n")
        urls = extract_github_urls(p)
        assert urls == []


# ---------------------------------------------------------------------------
# TestContentHash
# ---------------------------------------------------------------------------
class TestContentHash:
    def test_consistent(self):
        """Same input produces same hash."""
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2
        assert len(h1) == 16

    def test_ignores_whitespace(self):
        """Different whitespace produces same hash."""
        h1 = compute_content_hash("hello   world")
        h2 = compute_content_hash("hello\n\tworld")
        h3 = compute_content_hash("  hello world  ")
        assert h1 == h2 == h3

    def test_different_content(self):
        """Different content produces different hash."""
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("goodbye world")
        assert h1 != h2


# ---------------------------------------------------------------------------
# TestDiscoverComponents
# ---------------------------------------------------------------------------
class TestDiscoverComponents:
    def test_finds_all_types(self, sample_repo):
        """discover_components finds plugin, skill, and agent from fixture."""
        components = discover_components(sample_repo)
        types = {c["type"] for c in components}
        assert "plugin" in types
        assert "skill" in types
        assert "agent" in types

    def test_includes_correct_file_path(self, sample_repo):
        """file_path is relative to the repo root."""
        components = discover_components(sample_repo)
        paths = {c["file_path"] for c in components}
        assert ".claude-plugin/plugin.json" in paths
        assert "skills/test-skill/SKILL.md" in paths
        assert "agents/test-agent.md" in paths

    def test_component_fields(self, sample_repo):
        """Each component has all required fields."""
        required_keys = {
            "type",
            "name",
            "description",
            "version",
            "file_path",
            "file_last_commit",
            "file_last_author",
            "tags",
            "tools_used",
            "triggers",
            "metadata",
            "content_hash",
        }
        components = discover_components(sample_repo)
        for comp in components:
            missing = required_keys - set(comp.keys())
            assert (
                not missing
            ), f"Component {comp.get('name', '?')} missing keys: {missing}"

    def test_skips_git_directory(self, tmp_path):
        """Files inside .git/ are not discovered."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Put a SKILL.md inside .git — should be skipped
        (repo / ".git" / "SKILL.md").write_text("---\nname: bad\n---\n")
        # Put a real one outside
        skill_dir = repo / "skills" / "good"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: good\n---\n")

        components = discover_components(repo)
        names = [c["name"] for c in components]
        assert "good" in names
        assert "bad" not in names

    def test_discovers_commands(self, tmp_path):
        """Command .md files under commands/ are discovered."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        cmd_dir = repo / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "deploy.md").write_text(
            "---\ndescription: Deploy it\n---\n\nDeploy.\n"
        )
        components = discover_components(repo)
        assert any(c["type"] == "command" and c["name"] == "deploy" for c in components)

    def test_discovers_hooks(self, tmp_path):
        """hooks.json files are discovered."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "hooks.json").write_text(
            json.dumps({"hooks": [{"event": "PreToolUse", "command": "echo"}]})
        )
        components = discover_components(repo)
        assert any(c["type"] == "hook" for c in components)


# ---------------------------------------------------------------------------
# TestIntegrationLocalRepos
# ---------------------------------------------------------------------------
class TestIntegrationLocalRepos:
    def test_discover_real_repos(self, local_repos_dir):
        """Integration: discovers >= 20 repos from the local harness directory."""
        repos = discover_repos(local_repos_dir)
        assert len(repos) >= 20, f"Expected >= 20 repos, found {len(repos)}"

    def test_scan_awesome_claude_code(self, local_repos_dir):
        """Integration: awesome-claude-code README contains >= 50 GitHub URLs."""
        awesome = local_repos_dir / "awesome-claude-code"
        if not awesome.exists():
            pytest.skip("awesome-claude-code repo not found")
        readme = awesome / "README.md"
        if not readme.exists():
            pytest.skip("awesome-claude-code/README.md not found")
        urls = extract_github_urls(readme)
        assert len(urls) >= 50, f"Expected >= 50 URLs, found {len(urls)}"
