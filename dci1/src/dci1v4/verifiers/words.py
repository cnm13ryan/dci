"""Word segmentation shared by every v4 verifier (v4r2 §7.2, §9.2).

A *word* is a maximal run of Unicode-alphabetic characters (``str.isalpha``).
Non-alphabetic characters — digits, punctuation, whitespace, hyphens,
apostrophes, markdown — act as run boundaries. Suffix and letter tests use
the lower-cased word; comma and upper-case counts read raw characters.

Both function sources are carried byte-identically from the closed v3
instrument (dci1v3/verifiers/words.py) under the §10.2 carry-over rule;
``dci1v4.carryover`` verifies the identity and refuses on drift.
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
