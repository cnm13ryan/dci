"""Word segmentation shared by every v3 verifier (§5, §9).

A *word* is a maximal run of Unicode-alphabetic characters (``str.isalpha``).
Non-alphabetic characters — digits, punctuation, whitespace, hyphens,
apostrophes, markdown — act as run boundaries. Suffix and letter tests use
the lower-cased word; comma and upper-case counts read raw characters.

``alpha_runs`` is byte-identical (function source) to the v2 instrument that
produced the E2B Gate 1 packet; the carry-over rule of §10 requires the
normalisation to be unchanged, and stages/gate1.py verifies that identity.
"""
from __future__ import annotations


def alpha_runs(text: str) -> list[str]:
    """Maximal runs of alphabetic characters, in order of appearance."""
    runs: list[str] = []
    current: list[str] = []
    for ch in text:
        if ch.isalpha():
            current.append(ch)
        elif current:
            runs.append("".join(current))
            current = []
    if current:
        runs.append("".join(current))
    return runs


def words_lower(text: str) -> list[str]:
    """The lower-cased word list the family verifiers read."""
    return alpha_runs(text.lower())
