"""Verifiers for the focal constraint B and the twelve reference candidates.

Each verifier is a deterministic pure function ``(response_text, param) -> bool``
(True = pass) reading only the response text and its own fixed parameter —
never an arm label, another verifier's verdict, or any prompt metadata
(prereg §10). Word segmentation is the shared D16 rule (`words.words_lower`).

A response containing no words passes every universally quantified rule
vacuously (D16); such degenerate responses are surfaced by the §16 compliance
flag, never hidden here.
"""
from __future__ import annotations

from dci1.verifiers.words import words_lower


def focal_max_letters(text: str, m: int) -> bool:
    """B: every word in the answer must have at most m letters."""
    return all(len(w) <= m for w in words_lower(text))


def min_letters(text: str, k: int) -> bool:
    """C1 (k=2) / C2 (k=3): every word must have at least k letters."""
    return all(len(w) >= k for w in words_lower(text))


def no_initial(text: str, letter: str) -> bool:
    """C3–C9: no word may begin with the given letter."""
    return all(not w.startswith(letter) for w in words_lower(text))


def no_suffix(text: str, suffix: str) -> bool:
    """C10 (ly) / C11 (ing): no word may end with the given letters."""
    return all(not w.endswith(suffix) for w in words_lower(text))


def no_doubled_letter(text: str, _param: None = None) -> bool:
    """C12: no word may contain the same letter twice in a row."""
    return all(all(a != b for a, b in zip(w, w[1:])) for w in words_lower(text))
