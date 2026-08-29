"""Counted statistics for v8: A and the markers through one function.

Twenty-two numerators, as in v7 (§7.6). The fourteen non-marker numerators are
v7's own functions, imported rather than copied, so their bytes are hashed at
their v7 location. The eight marker numerators and **A's numerator** are
``functools.partial(count_marker, marker=word)``: the same function object
bound to nine different words, which is what makes "A's rule with a different
target string" an identity a test can check (``.func is count_marker``) rather
than a sentence in a docstring.
"""
from __future__ import annotations

from functools import partial
from typing import Any, Callable

from dci1v7.verifiers.constraints import (
    FAMILIES, FAMILY_IDS, MARKER_WORDS, STATISTIC_IDS, TARGET_WORD,
)
from dci1v7.verifiers.statistics import STATISTICS as _V7_STATISTICS
from dci1v7.verifiers.statistics import focal_statistic, word_count

from dci1v8dev.verifiers.words import (
    alpha_runs, assert_marker_word, count_marker, sentence_units, words_lower,
)

__all__ = ["count_marker", "marker_counter", "TARGET_STATISTIC",
           "MARKER_STATISTICS", "CARRIED_STATISTICS", "STATISTICS",
           "FAMILY_STATISTICS", "family_statistic", "statistic_of",
           "statistic_for", "target_statistic", "focal_statistic",
           "word_count", "alpha_runs", "words_lower", "sentence_units",
           "TARGET_WORD"]


def marker_counter(marker: str) -> Callable[[str], int]:
    """``count_marker`` bound to one word. ``.func`` is the shared function."""
    counter = partial(count_marker, marker=assert_marker_word(marker))
    counter.__name__ = f"count_{marker}"          # type: ignore[attr-defined]
    counter.__doc__ = f"Occurrences of the whole word {marker!r} (§9.2)."
    return counter


#: A's numerator. v7 used ``dci1v4.verifiers.target.s0_count`` here.
TARGET_STATISTIC: Callable[[str], int] = marker_counter(TARGET_WORD)

MARKER_STATISTICS: dict[str, Callable[[str], int]] = {
    statistic_id: marker_counter(word) for statistic_id, word in MARKER_WORDS.items()
}

#: The fourteen v7 numerators that are not marker occurrences, unchanged.
CARRIED_STATISTICS: dict[str, Callable[[str], int]] = {
    k: v for k, v in _V7_STATISTICS.items() if k not in MARKER_WORDS
}

STATISTICS: dict[str, Callable[[str], int]] = {**MARKER_STATISTICS,
                                                **CARRIED_STATISTICS}
assert set(STATISTICS) == set(STATISTIC_IDS), (
    "§7.6 names the registered numerators and this module must supply "
    "exactly those")
assert len(STATISTICS) == 22 and len(MARKER_STATISTICS) == 8

FAMILY_STATISTICS: dict[str, Callable[[str], int]] = {
    kind: STATISTICS[family.statistic_id] for kind, family in FAMILIES.items()
}
assert set(FAMILY_STATISTICS) == set(FAMILY_IDS)


def target_statistic(text: str) -> int:
    """A's count: ``count_marker(text, "however")``."""
    return TARGET_STATISTIC(text)


def family_statistic(kind: str, text: str) -> int:
    return FAMILY_STATISTICS[kind](text)


def statistic_of(statistic_id: str, text: str) -> int:
    return STATISTICS[statistic_id](text)


def statistic_for(constraint: Any) -> Callable[[str], int]:
    """The numerator of one constraint instance, by kind."""
    if constraint.kind == "A":
        return TARGET_STATISTIC
    if constraint.kind == "B":
        return focal_statistic
    return FAMILY_STATISTICS[constraint.kind]
