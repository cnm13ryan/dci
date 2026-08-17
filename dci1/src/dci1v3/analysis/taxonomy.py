"""The nine-category failure taxonomy (§23), deterministic and frozen.

Categories are assigned to every target failure in the four primary arms in
the fixed priority order; the first matching rule wins. The twenty refusal
patterns and the restatement similarity function are frozen here and hashed
into the freeze record with this module's source.
"""
from __future__ import annotations

import difflib
import re

from dci1v3.protocol.constants import (
    FAILURE_CATEGORIES,
    RESTATEMENT_SIMILARITY,
)

#: The twenty frozen refusal patterns. Lower-case substring match.
REFUSAL_PATTERNS: tuple[str, ...] = (
    "i cannot", "i can't", "i can not", "i am unable", "i'm unable",
    "i am sorry", "i'm sorry", "i apologize", "i apologise",
    "as an ai", "as a language model", "i am not able", "i'm not able",
    "i won't", "i will not", "cannot assist", "can't assist",
    "cannot help with", "can't help with", "unable to comply",
)
assert len(REFUSAL_PATTERNS) == 20

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def is_refusal(text: str) -> bool:
    """At least one frozen pattern occurs, and removing every sentence that
    contains a pattern leaves no alphabetic character."""
    lowered = text.lower()
    if not any(p in lowered for p in REFUSAL_PATTERNS):
        return False
    remainder = [s for s in _SENTENCE_SPLIT.split(text)
                 if not any(p in s.lower() for p in REFUSAL_PATTERNS)]
    return not any(ch.isalpha() for chunk in remainder for ch in chunk)


def similarity(a: str, b: str) -> float:
    """Frozen restatement similarity: SequenceMatcher ratio over
    lower-cased, whitespace-collapsed text."""
    normalize = lambda s: " ".join(s.lower().split())  # noqa: E731
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def is_restatement(response: str, instruction_text: str) -> bool:
    return similarity(response, instruction_text) > RESTATEMENT_SIMILARITY


def classify_failure(*, response: str, finish_reason: str, s0: int, s2: int,
                     n: int, instruction_text: str) -> str:
    """Assign exactly one category, first matching rule wins (§23)."""
    if not response.strip():
        return "empty"
    if finish_reason == "length":
        return "cut_off"
    if is_refusal(response):
        return "refusal"
    if is_restatement(response, instruction_text):
        return "restatement"
    if s0 == 0 and s2 > 0:
        return "target_inside_longer_word"
    if s0 == 0:
        return "zero_occurrences"
    if 0 < s0 < n:
        return "too_few"
    if s0 > n:
        return "too_many"
    return "other"


assert set(FAILURE_CATEGORIES) == {
    "empty", "cut_off", "refusal", "restatement",
    "target_inside_longer_word", "zero_occurrences", "too_few", "too_many",
    "other"}
