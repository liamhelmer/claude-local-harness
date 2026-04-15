"""Tests for catalog.src.similarity — pure-Python similarity detection."""

import pytest

from catalog.src.similarity import (
    classify_similarity,
    find_similarities,
    jaccard_similarity,
    tokenize,
)


# ---------------------------------------------------------------------------
# TestTokenize
# ---------------------------------------------------------------------------
class TestTokenize:
    def test_basic_words(self):
        """Lowercases and extracts alphanumeric tokens, removing stopwords."""
        result = tokenize("Deploy Terraform modules to the Cloud")
        assert "deploy" in result
        assert "terraform" in result
        assert "modules" in result
        assert "cloud" in result
        # stopword removed
        assert "the" not in result
        assert "to" not in result

    def test_strips_punctuation(self):
        """Punctuation is removed; only alphanumeric words survive."""
        result = tokenize("hello-world! foo_bar... baz123")
        assert "hello" in result
        assert "world" in result
        assert "foo" in result
        assert "bar" in result
        assert "baz123" in result
        # punctuation chars should not appear
        assert "!" not in result
        assert "..." not in result

    def test_filters_short_words(self):
        """Single-character tokens are dropped."""
        result = tokenize("I a x do big")
        # "i", "a", "x" are length 1 — filtered out
        # "a" is also a stopword
        assert "i" not in result
        assert "a" not in result
        assert "x" not in result
        # "do" length 2, not a stopword
        assert "do" in result
        assert "big" in result

    def test_empty_string(self):
        """Empty input returns empty set."""
        assert tokenize("") == set()

    def test_all_stopwords(self):
        """Input consisting entirely of stopwords returns empty set."""
        assert tokenize("the a an is are") == set()


# ---------------------------------------------------------------------------
# TestJaccardSimilarity
# ---------------------------------------------------------------------------
class TestJaccardSimilarity:
    def test_identical_sets(self):
        """Identical sets have similarity 1.0."""
        s = {"deploy", "terraform", "modules"}
        assert jaccard_similarity(s, s) == pytest.approx(1.0)

    def test_disjoint_sets(self):
        """Completely disjoint sets have similarity 0.0."""
        a = {"deploy", "terraform"}
        b = {"kubernetes", "helm"}
        assert jaccard_similarity(a, b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        """Partial overlap yields a value between 0 and 1."""
        a = {"deploy", "terraform", "modules"}
        b = {"deploy", "terraform", "cloud"}
        # intersection=2, union=4 -> 0.5
        assert jaccard_similarity(a, b) == pytest.approx(0.5)

    def test_empty_sets(self):
        """Two empty sets return 0.0 (not division-by-zero)."""
        assert jaccard_similarity(set(), set()) == pytest.approx(0.0)

    def test_one_empty_set(self):
        """One empty set returns 0.0."""
        assert jaccard_similarity({"a", "b"}, set()) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestClassifySimilarity
# ---------------------------------------------------------------------------
class TestClassifySimilarity:
    def test_same_name_returns_same_purpose(self):
        """Matching names (case-insensitive) yields 'same-purpose'."""
        assert classify_similarity("My-Skill", "my-skill", 0.5, False) == "same-purpose"

    def test_fork_repos(self):
        """repos_are_forks=True yields 'fork'."""
        assert classify_similarity("skill-a", "skill-b", 0.8, True) == "fork"

    def test_high_score_derivative(self):
        """Score > 0.9 yields 'derivative'."""
        assert classify_similarity("skill-a", "skill-b", 0.95, False) == "derivative"

    def test_default_near_duplicate(self):
        """Default classification is 'near-duplicate'."""
        assert classify_similarity("skill-a", "skill-b", 0.7, False) == "near-duplicate"

    def test_same_name_takes_priority_over_fork(self):
        """same-purpose wins even when repos_are_forks is True."""
        assert classify_similarity("Deploy", "deploy", 0.99, True) == "same-purpose"


# ---------------------------------------------------------------------------
# TestFindSimilarities
# ---------------------------------------------------------------------------
class TestFindSimilarities:
    def test_finds_similar_pair_same_type(self):
        """Two similar terraform skills are detected; unrelated k8s skill is not."""
        components = [
            {
                "id": 1,
                "name": "terraform-deploy",
                "type": "skill",
                "content": "Deploy terraform modules to provision cloud infrastructure resources",
            },
            {
                "id": 2,
                "name": "terraform-provision",
                "type": "skill",
                "content": "Provision cloud infrastructure resources using terraform modules",
            },
            {
                "id": 3,
                "name": "k8s-debug",
                "type": "skill",
                "content": "Debug kubernetes pods containers logs network services",
            },
        ]
        results = find_similarities(components, threshold=0.4)
        # Should find the terraform pair
        pairs = {(r["a"], r["b"]) for r in results}
        assert (1, 2) in pairs or (2, 1) in pairs
        # k8s should NOT be paired with either terraform component
        k8s_pairs = [r for r in results if r["a"] == 3 or r["b"] == 3]
        assert len(k8s_pairs) == 0

    def test_different_types_not_compared(self):
        """Components of different types are never compared."""
        components = [
            {
                "id": 1,
                "name": "terraform-deploy",
                "type": "skill",
                "content": "Deploy terraform modules to provision cloud infrastructure resources",
            },
            {
                "id": 2,
                "name": "terraform-deploy-agent",
                "type": "agent",
                "content": "Deploy terraform modules to provision cloud infrastructure resources",
            },
        ]
        results = find_similarities(components, threshold=0.1)
        assert len(results) == 0

    def test_empty_input(self):
        """No components yields no similarities."""
        assert find_similarities([], threshold=0.5) == []

    def test_result_structure(self):
        """Each result dict has the expected keys."""
        components = [
            {
                "id": 1,
                "name": "a",
                "type": "skill",
                "content": "deploy terraform modules cloud",
            },
            {
                "id": 2,
                "name": "b",
                "type": "skill",
                "content": "deploy terraform modules cloud",
            },
        ]
        results = find_similarities(components, threshold=0.1)
        assert len(results) >= 1
        r = results[0]
        assert "a" in r
        assert "b" in r
        assert "score" in r
        assert "type" in r
        assert "notes" in r
