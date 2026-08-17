"""Word segmentation shared by every verifier (prereg §9; decision D16).

A *word* is a maximal run of Unicode-alphabetic characters (``str.isalpha``).
Non-alphabetic characters — digits, punctuation, whitespace, hyphens,
apostrophes, markdown — act as run boundaries, so punctuation adjacent to a
word leaves the run unchanged and hyphenated forms split into separate runs.

The target verifier counts runs of the *lower-cased* text (S0) or the original
text (S1); the pool verifiers operate on lower-cased runs (D16).
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
    """The lower-cased word list every pool verifier reads."""
    return alpha_runs(text.lower())
