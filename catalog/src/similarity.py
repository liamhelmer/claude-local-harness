"""Pure-Python similarity detection for catalog components."""

from __future__ import annotations

import re
from collections import defaultdict

STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "and",
    "or",
    "not",
    "this",
    "that",
    "it",
    "as",
}

_WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    """Lowercase, extract alphanumeric words, remove stopwords, filter len <= 1."""
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if len(w) > 1 and w not in STOPWORDS}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Return |intersection| / |union|, or 0.0 for two empty sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def classify_similarity(
    name_a: str,
    name_b: str,
    score: float,
    repos_are_forks: bool,
) -> str:
    """Classify the relationship between two similar components.

    Returns one of: "same-purpose", "fork", "derivative", "near-duplicate".
    """
    if name_a.lower() == name_b.lower():
        return "same-purpose"
    if repos_are_forks:
        return "fork"
    if score > 0.9:
        return "derivative"
    return "near-duplicate"


def find_similarities(
    components: list[dict],
    threshold: float = 0.7,
    max_results: int = 5000,
) -> list[dict]:
    """Compare components within each type group using Jaccard similarity.

    Each component dict must have keys: id, name, type, content.
    Returns list of {a, b, score, type, notes} for pairs above *threshold*.
    Caps output at *max_results* to avoid O(n^2) blowup on large catalogs.
    """
    # Group by type
    by_type: dict[str, list[dict]] = defaultdict(list)
    for comp in components:
        by_type[comp["type"]].append(comp)

    results: list[dict] = []

    for comp_type, group in by_type.items():
        # Pre-tokenize all content in this group
        tokens = {comp["id"]: tokenize(comp["content"]) for comp in group}

        # Compare all pairs
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i]
                b = group[j]
                score = jaccard_similarity(tokens[a["id"]], tokens[b["id"]])
                if score >= threshold:
                    classification = classify_similarity(
                        a["name"], b["name"], score, repos_are_forks=False
                    )
                    results.append(
                        {
                            "a": a["id"],
                            "b": b["id"],
                            "score": score,
                            "type": comp_type,
                            "notes": classification,
                        }
                    )
                    if len(results) >= max_results:
                        return results

    return results
