"""Tests for catalog.src.classifier — Hybrid keyword classifier."""

import pytest

from catalog.src.classifier import (
    PROJECT_TYPE_KEYWORDS,
    PERSONA_KEYWORDS,
    keyword_classify,
    merge_classifications,
)


# ---------------------------------------------------------------------------
# TestKeywordDictionaries
# ---------------------------------------------------------------------------
class TestKeywordDictionaries:
    def test_all_project_types_defined(self):
        """All 7 project-type slugs exist as keys."""
        expected = {
            "devops",
            "app-deploy",
            "policy-as-code",
            "docs",
            "sales-marketing",
            "big-data",
            "finops",
        }
        assert set(PROJECT_TYPE_KEYWORDS.keys()) == expected

    def test_all_personas_defined(self):
        """All 8 persona slugs exist as keys."""
        expected = {
            "platform-engineer",
            "cloud-sre",
            "data-engineer",
            "ml-engineer",
            "sales",
            "marketing",
            "accounting",
            "director-vp",
        }
        assert set(PERSONA_KEYWORDS.keys()) == expected


# ---------------------------------------------------------------------------
# TestKeywordClassify
# ---------------------------------------------------------------------------
class TestKeywordClassify:
    def test_devops_by_keyword(self):
        """Name 'tf-plan-reviewer' with 'terraform' in description -> devops."""
        result = keyword_classify(
            name="tf-plan-reviewer",
            description="Reviews terraform plan output for compliance",
            tags=[],
        )
        assert "devops" in result["project_types"]

    def test_multiple_matches(self):
        """Description with kubernetes AND terraform -> both devops and app-deploy."""
        result = keyword_classify(
            name="infra-deployer",
            description="Uses terraform to provision kubernetes clusters",
            tags=[],
        )
        assert "devops" in result["project_types"]
        assert "app-deploy" in result["project_types"]

    def test_persona_mapping(self):
        """Description with 'billing' and 'budget' -> finops project type, accounting or director-vp persona."""
        result = keyword_classify(
            name="cost-tracker",
            description="Tracks billing and budget across cloud accounts",
            tags=[],
        )
        assert "finops" in result["project_types"]
        assert "accounting" in result["personas"] or "director-vp" in result["personas"]

    def test_no_match(self):
        """Generic name/description -> empty lists."""
        result = keyword_classify(
            name="my-tool",
            description="A simple utility",
            tags=[],
        )
        assert result["project_types"] == []
        assert result["personas"] == []

    def test_case_insensitive(self):
        """'KUBERNETES' still matches app-deploy."""
        result = keyword_classify(
            name="deployer",
            description="Deploys to KUBERNETES",
            tags=[],
        )
        assert "app-deploy" in result["project_types"]


# ---------------------------------------------------------------------------
# TestMergeClassifications
# ---------------------------------------------------------------------------
class TestMergeClassifications:
    def test_union(self):
        """Keyword says devops, AI says devops+app-deploy -> both present."""
        keyword_result = {"project_types": ["devops"], "personas": []}
        ai_result = {"project_types": ["devops", "app-deploy"], "personas": []}
        merged = merge_classifications(keyword_result, ai_result)
        assert "devops" in merged["project_types"]
        assert "app-deploy" in merged["project_types"]

    def test_ai_never_removes(self):
        """Keyword says devops+big-data, AI says only devops -> big-data still present."""
        keyword_result = {
            "project_types": ["devops", "big-data"],
            "personas": ["data-engineer"],
        }
        ai_result = {"project_types": ["devops"], "personas": []}
        merged = merge_classifications(keyword_result, ai_result)
        assert "big-data" in merged["project_types"]
        assert "devops" in merged["project_types"]
        assert "data-engineer" in merged["personas"]
