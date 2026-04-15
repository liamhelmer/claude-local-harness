"""GitHub API enricher — fetches repo metadata via the gh CLI."""

from __future__ import annotations

import json
import re
import subprocess
import time
from typing import Optional


def _run_gh_api(endpoint: str) -> Optional[str]:
    """Run ``gh api <endpoint> --cache 1h`` and return stdout on success, None on failure."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint, "--cache", "1h"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def parse_gh_api_response(raw: str) -> Optional[dict]:
    """Parse a JSON response from the GitHub repos API into a normalised dict.

    Returns ``None`` on invalid JSON.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    license_obj = data.get("license")
    license_id = ""
    if license_obj and isinstance(license_obj, dict):
        license_id = license_obj.get("spdx_id") or ""

    return {
        "name": data.get("full_name", ""),
        "description": data.get("description", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "last_repo_commit": data.get("pushed_at", ""),
        "license": license_id,
        "topics": data.get("topics", []),
    }


def fetch_repo_metadata(url: str) -> Optional[dict]:
    """Extract owner/repo from a GitHub URL and fetch metadata via ``gh api``.

    Returns ``None`` when the URL cannot be parsed or the API call fails.
    """
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        return None

    owner, repo = match.group(1), match.group(2)
    raw = _run_gh_api(f"repos/{owner}/{repo}")
    if raw is None:
        return None

    return parse_gh_api_response(raw)


def batch_enrich_repos(
    urls: list[str],
    batch_size: int = 50,
    delay: float = 1.0,
) -> list[dict]:
    """Enrich a list of GitHub URLs, skipping failures.

    Sleeps *delay* seconds every *batch_size* items to stay within rate limits.
    """
    results: list[dict] = []
    for idx, url in enumerate(urls):
        if idx > 0 and idx % batch_size == 0 and delay > 0:
            time.sleep(delay)

        meta = fetch_repo_metadata(url)
        if meta is None:
            continue

        meta["url"] = url
        results.append(meta)

    return results
