"""Local repo scanner — discovers repos and parses Claude Code components."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Split a file on ``---`` delimiters and parse YAML frontmatter.

    Returns (frontmatter_dict, body_string).  If the file has no frontmatter
    the dict is empty and body is the full text.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    # parts[0] is '' (before first ---), parts[1] is frontmatter, parts[2] is body
    if len(parts) < 3:
        return {}, text

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}

    body = parts[2].strip()
    return fm, body


# ---------------------------------------------------------------------------
# Repo discovery & git helpers
# ---------------------------------------------------------------------------


def discover_repos(base_dir: Path) -> list[Path]:
    """Find all non-hidden directories with a ``.git`` subdirectory, sorted."""
    repos: list[Path] = []
    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if (entry / ".git").is_dir():
            repos.append(entry)
    return repos


def pull_repos(repos: list[Path]) -> dict[Path, str]:
    """Run ``git pull --ff-only`` in each repo, return a results dict.

    Each value is either ``"ok"`` or the error message.  Timeout is 30 s.
    """
    results: dict[Path, str] = {}
    for repo in repos:
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=30,
            )
            results[repo] = "ok"
        except subprocess.TimeoutExpired:
            results[repo] = "timeout"
        except Exception as exc:  # noqa: BLE001
            results[repo] = str(exc)
    return results


def get_file_git_info(repo_path: Path, file_path: str) -> dict:
    """Return ``{"date": ..., "author": ...}`` from the last commit touching *file_path*."""
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%aI|%an", "--", file_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = proc.stdout.strip()
        if "|" in output:
            date, author = output.split("|", 1)
            return {"date": date, "author": author}
    except Exception:  # noqa: BLE001
        pass
    return {"date": "", "author": ""}


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------


def compute_content_hash(content: str) -> str:
    """Normalize whitespace, SHA-256 hash, return first 16 hex chars."""
    normalized = re.sub(r"\s+", " ", content).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:16]


# ---------------------------------------------------------------------------
# Component parsers
# ---------------------------------------------------------------------------


def parse_plugin_json(path: Path) -> dict:
    """Parse ``plugin.json``, return structured dict."""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        data = {}

    return {
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "version": data.get("version", ""),
        "keywords": data.get("keywords", []),
        "metadata": data,
    }


def parse_skill_md(path: Path) -> dict:
    """Parse ``SKILL.md`` with YAML frontmatter."""
    fm, body = _parse_frontmatter(path)
    return {
        "name": fm.get("name", ""),
        "description": fm.get("description", ""),
        "tags": fm.get("tags", []),
        "tools": fm.get("tools", []),
        "version": fm.get("version", ""),
        "body": body,
        "metadata": fm,
    }


def parse_agent_md(path: Path) -> dict:
    """Parse an agent ``.md`` with YAML frontmatter."""
    fm, body = _parse_frontmatter(path)
    return {
        "name": fm.get("name", ""),
        "description": fm.get("description", ""),
        "model": fm.get("model", ""),
        "tools": fm.get("tools", []),
        "color": fm.get("color", ""),
        "body": body,
        "metadata": fm,
    }


def parse_command_md(path: Path) -> dict:
    """Parse a command ``.md``.  Name comes from the file stem."""
    fm, body = _parse_frontmatter(path)
    return {
        "name": path.stem,
        "description": fm.get("description", ""),
        "argument_hint": fm.get("argument_hint", ""),
        "body": body,
        "metadata": fm,
    }


def parse_hook_json(path: Path) -> dict:
    """Parse ``hooks.json``, return list of hook event names."""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        data = {}

    hooks_list = data.get("hooks", [])
    events = sorted({h.get("event", "") for h in hooks_list if h.get("event")})

    return {
        "name": path.stem,
        "events": events,
        "metadata": data,
    }


# ---------------------------------------------------------------------------
# URL extraction
# ---------------------------------------------------------------------------


def extract_github_urls(path: Path) -> list[str]:
    """Regex-extract ``https://github.com/owner/repo`` URLs, deduplicate, return sorted."""
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
    matches = re.findall(pattern, text)
    # Strip trailing punctuation that might have been captured
    cleaned: set[str] = set()
    for m in matches:
        url = m.rstrip(".")
        cleaned.add(url)
    return sorted(cleaned)


# ---------------------------------------------------------------------------
# Component discovery
# ---------------------------------------------------------------------------


def _is_under_git_dir(path: Path, repo_root: Path) -> bool:
    """Return True if *path* is inside a ``.git`` directory."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False
    return ".git" in rel.parts


def _make_component(
    *,
    comp_type: str,
    parsed: dict,
    file_path: str,
    repo_path: Path,
    content: str,
) -> dict:
    """Build a unified component dict from parsed data."""
    git_info = get_file_git_info(repo_path, file_path)

    return {
        "type": comp_type,
        "name": parsed.get("name", ""),
        "description": parsed.get("description", ""),
        "version": parsed.get("version", ""),
        "file_path": file_path,
        "file_last_commit": git_info["date"],
        "file_last_author": git_info["author"],
        "tags": parsed.get("tags", parsed.get("keywords", [])),
        "tools_used": parsed.get("tools", []),
        "triggers": parsed.get("events", []),
        "metadata": parsed.get("metadata", {}),
        "content_hash": compute_content_hash(content),
    }


def discover_components(repo_path: Path) -> list[dict]:
    """Recursively find and parse all component types in a repo.

    Component types:
    - ``**/plugin.json``  -> ``"plugin"``
    - ``**/SKILL.md``     -> ``"skill"``
    - ``**/agents/*.md``  -> ``"agent"``
    - ``**/commands/*.md`` -> ``"command"``
    - ``**/hooks.json``   -> ``"hook"``

    Skips anything under ``.git/`` directories.
    """
    components: list[dict] = []

    # plugin.json
    for p in repo_path.rglob("plugin.json"):
        if _is_under_git_dir(p, repo_path):
            continue
        parsed = parse_plugin_json(p)
        rel = str(p.relative_to(repo_path))
        content = p.read_text(encoding="utf-8", errors="replace")
        components.append(
            _make_component(
                comp_type="plugin",
                parsed=parsed,
                file_path=rel,
                repo_path=repo_path,
                content=content,
            )
        )

    # SKILL.md
    for p in repo_path.rglob("SKILL.md"):
        if _is_under_git_dir(p, repo_path):
            continue
        parsed = parse_skill_md(p)
        rel = str(p.relative_to(repo_path))
        content = p.read_text(encoding="utf-8", errors="replace")
        components.append(
            _make_component(
                comp_type="skill",
                parsed=parsed,
                file_path=rel,
                repo_path=repo_path,
                content=content,
            )
        )

    # agents/*.md
    for p in repo_path.rglob("agents/*.md"):
        if _is_under_git_dir(p, repo_path):
            continue
        parsed = parse_agent_md(p)
        rel = str(p.relative_to(repo_path))
        content = p.read_text(encoding="utf-8", errors="replace")
        components.append(
            _make_component(
                comp_type="agent",
                parsed=parsed,
                file_path=rel,
                repo_path=repo_path,
                content=content,
            )
        )

    # commands/*.md
    for p in repo_path.rglob("commands/*.md"):
        if _is_under_git_dir(p, repo_path):
            continue
        parsed = parse_command_md(p)
        rel = str(p.relative_to(repo_path))
        content = p.read_text(encoding="utf-8", errors="replace")
        components.append(
            _make_component(
                comp_type="command",
                parsed=parsed,
                file_path=rel,
                repo_path=repo_path,
                content=content,
            )
        )

    # hooks.json
    for p in repo_path.rglob("hooks.json"):
        if _is_under_git_dir(p, repo_path):
            continue
        parsed = parse_hook_json(p)
        rel = str(p.relative_to(repo_path))
        content = p.read_text(encoding="utf-8", errors="replace")
        components.append(
            _make_component(
                comp_type="hook",
                parsed=parsed,
                file_path=rel,
                repo_path=repo_path,
                content=content,
            )
        )

    return components
