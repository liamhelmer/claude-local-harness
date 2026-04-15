"""Tests for catalog.src.enricher — GitHub API enricher module."""

import json
from unittest.mock import patch

import pytest

from catalog.src.enricher import (
    batch_enrich_repos,
    fetch_repo_metadata,
    parse_gh_api_response,
)

# Sample full API response matching GitHub's repos endpoint format
FULL_API_RESPONSE = json.dumps(
    {
        "full_name": "anthropics/claude-code",
        "description": "CLI for Claude",
        "stargazers_count": 5200,
        "forks_count": 310,
        "pushed_at": "2025-05-01T12:00:00Z",
        "license": {"spdx_id": "MIT"},
        "topics": ["ai", "cli", "claude"],
    }
)

MISSING_LICENSE_RESPONSE = json.dumps(
    {
        "full_name": "owner/repo",
        "description": "A repo",
        "stargazers_count": 10,
        "forks_count": 2,
        "pushed_at": "2025-01-01T00:00:00Z",
        "license": None,
        "topics": [],
    }
)


# ---------------------------------------------------------------------------
# TestParseGhApiResponse
# ---------------------------------------------------------------------------
class TestParseGhApiResponse:
    def test_parses_full_response(self):
        """Full JSON with all fields yields correct stars, license, topics."""
        result = parse_gh_api_response(FULL_API_RESPONSE)
        assert result is not None
        assert result["name"] == "anthropics/claude-code"
        assert result["description"] == "CLI for Claude"
        assert result["stars"] == 5200
        assert result["forks"] == 310
        assert result["last_repo_commit"] == "2025-05-01T12:00:00Z"
        assert result["license"] == "MIT"
        assert result["topics"] == ["ai", "cli", "claude"]

    def test_handles_missing_license(self):
        """license: null in response maps to empty string."""
        result = parse_gh_api_response(MISSING_LICENSE_RESPONSE)
        assert result is not None
        assert result["license"] == ""

    def test_handles_invalid_json(self):
        """Non-JSON input returns None."""
        result = parse_gh_api_response("not json")
        assert result is None


# ---------------------------------------------------------------------------
# TestFetchRepoMetadata
# ---------------------------------------------------------------------------
class TestFetchRepoMetadata:
    @patch("catalog.src.enricher._run_gh_api")
    def test_calls_gh_api(self, mock_gh_api):
        """Extracts owner/repo from URL and calls _run_gh_api correctly."""
        mock_gh_api.return_value = FULL_API_RESPONSE
        result = fetch_repo_metadata("https://github.com/anthropics/claude-code")
        mock_gh_api.assert_called_once_with("repos/anthropics/claude-code")
        assert result is not None
        assert result["name"] == "anthropics/claude-code"

    @patch("catalog.src.enricher._run_gh_api")
    def test_handles_api_failure(self, mock_gh_api):
        """When _run_gh_api returns None, fetch_repo_metadata returns None."""
        mock_gh_api.return_value = None
        result = fetch_repo_metadata("https://github.com/owner/repo")
        assert result is None


# ---------------------------------------------------------------------------
# TestBatchEnrich
# ---------------------------------------------------------------------------
class TestBatchEnrich:
    @patch("catalog.src.enricher.fetch_repo_metadata")
    def test_processes_batch(self, mock_fetch):
        """Valid data for 2 URLs produces 2 results with url key added."""
        mock_fetch.side_effect = [
            {"name": "owner/repo1", "stars": 10},
            {"name": "owner/repo2", "stars": 20},
        ]
        urls = [
            "https://github.com/owner/repo1",
            "https://github.com/owner/repo2",
        ]
        results = batch_enrich_repos(urls, batch_size=50, delay=0)
        assert len(results) == 2
        assert results[0]["url"] == "https://github.com/owner/repo1"
        assert results[1]["url"] == "https://github.com/owner/repo2"

    @patch("catalog.src.enricher.fetch_repo_metadata")
    def test_skips_failures(self, mock_fetch):
        """When first URL fails (None), only the second valid result appears."""
        mock_fetch.side_effect = [
            None,
            {"name": "owner/repo2", "stars": 20},
        ]
        urls = [
            "https://github.com/owner/repo1",
            "https://github.com/owner/repo2",
        ]
        results = batch_enrich_repos(urls, batch_size=50, delay=0)
        assert len(results) == 1
        assert results[0]["name"] == "owner/repo2"
