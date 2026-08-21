"""Independent reimplementation of the registered DCI-1 text-scoring rules.

Instrument validation, not production scoring. This file is written from the
registered prose alone, by an author who did not read the primary verifiers, so
that agreement between the two is evidence about the specification rather than
evidence that one file was copied from the other. For the same reason it takes a
different route wherever a route exists: segmentation is `unicodedata.category`
plus `itertools.groupby` run-length grouping rather than an `str.isalpha`
accumulator loop, adjacent duplicates fall out of that same grouping rather than
a pairwise `zip`, and raw-character tallies come from a `Counter` histogram
rather than `str.count`. Standard library only; nothing imports from dci1.

The specification, transcribed:

  Lexical rule. A word is a maximal run of alphabetic characters, alphabetic
  meaning Unicode general category L (Lu, Ll, Lt, Lm, Lo). Digits, punctuation,
  symbols, marks and non-decimal numerics all terminate a word. Suffix and letter
  tests use the lower-cased word; comma counts and upper-case-letter counts read
  raw characters of the response, not words. W is the number of words.

  A ("use the word *however* exactly n times"): lower-case the whole response,
  take maximal alphabetic runs, count the runs equal to "however"; pass iff that
  count is exactly n. B ("every word must have at most m letters"): the statistic
  is the letter count of the longest word, 0 for a response with no words; pass
  iff it is at most m.

  The nine numerators, the four predicate forms, the twenty families, the graded
  shapes and the non-vacuity floor are transcribed at their definitions below.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Callable, Sequence
from itertools import groupby

TARGET = "however"
MIN_WORDS_NON_VACUOUS = 20

# Family identifier -> (statistic id, predicate form). Spelled out per form so a
# transcription error stays visible on the line where it was made.
FAMILY_SPEC: dict[str, tuple[str, str]] = {
    **{
        f"RF{i}": (stat, "count_budget")
        for i, stat in enumerate(
            ["b_initial", "ing_final", "one_letter", "doubled_letter",
             "comma", "capital_char", "letter_a", "y_final"], start=1)
    },
    **{
        f"CR{i}": (stat, "rate_budget")
        for i, stat in enumerate(
            ["b_initial", "ing_final", "one_letter", "doubled_letter",
             "comma", "capital_word", "letter_a", "y_final"], start=1)
    },
    "CL7": ("letter_a", "count_lower_bound"),
    "CL8": ("y_final", "count_lower_bound"),
    "CP4": ("doubled_letter", "rate_lower_bound"),
    "CP7": ("letter_a", "rate_lower_bound"),
}

_ASCII_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _is_letter(ch: str) -> bool:
    """Category-L membership: the general category begins with 'L' for exactly
    Lu/Ll/Lt/Lm/Lo, which is the registered definition verbatim."""
    return unicodedata.category(ch)[0] == "L"


def _runs(text: str) -> list[str]:
    """Maximal alphabetic runs, via run-length grouping on the letter flag.

    `groupby` collapses the text into alternating letter / non-letter blocks, so
    maximality is structural rather than something a loop has to maintain; the
    non-letter blocks are simply dropped."""
    return ["".join(chars) for is_word, chars in groupby(text, _is_letter) if is_word]


def words(text: str) -> list[str]:
    return _runs(text)


def lower_words(text: str) -> list[str]:
    """Words folded for the suffix and letter tests. The fold happens *after*
    segmentation here, because the prose folds "the word"; s0 folds first."""
    return [word.lower() for word in _runs(text)]


def word_count(text: str) -> int:
    return len(_runs(text))


# --- exact-count rule variants for A ------------------------------------------------


def s0(text: str) -> int:
    """Primary rule: fold the whole response, then segment and match.

    Folding before segmenting is what the prose says and is not quite the same as
    folding each word -- 'İ'.lower() introduces a combining mark (category Mn)
    that splits a run -- so the prose is followed literally."""
    return _runs(text.lower()).count(TARGET)


def s1(text: str) -> int:
    """Case-sensitive variant: only a run spelled exactly 'however' counts."""
    return _runs(text).count(TARGET)


def s2(text: str) -> int:
    """Substring variant: non-overlapping occurrences in the folded raw text.
    Unlike s0 it counts targets embedded in longer words, which is the contrast."""
    return text.lower().count(TARGET)


def s3(text: str, wordings: Sequence[str] = ()) -> int:
    """s0 after removing prompt echo: a leading colon-terminated line, and any
    line whose stripped text repeats an active constraint wording."""
    banned = {w.strip() for w in wordings if w.strip()}  # empty wordings would eat blanks
    kept = [
        line
        for index, line in enumerate(text.splitlines())
        if not (index == 0 and line.strip().endswith(":")) and line.strip() not in banned
    ]
    return s0("\n".join(kept))


def focal_statistic(text: str) -> int:
    """B's statistic: letters in the longest word, 0 when there are no words.
    Measured on the word as it appears, since folding can change length."""
    return max((len(word) for word in _runs(text)), default=0)


# --- the nine counted statistics ----------------------------------------------------


def _has_doubled_letter(word: str) -> bool:
    """Two identical adjacent letters == a grouping run of length >= 2."""
    return any(sum(1 for _ in chars) > 1 for _, chars in groupby(word))


def _is_upper(ch: str) -> bool:
    # capital_word is stated without an ASCII restriction, so category Lu is the
    # reading; inside a word (all category L) that coincides with str.isupper().
    return unicodedata.category(ch) == "Lu"


# One entry per registered numerator, each a direct transcription of its sentence.
# comma and capital_char read RAW response characters; the other seven read words.
# capital_char is registered as A-Z, so it stays ASCII and must not widen to Lu.
_STATISTICS: dict[str, Callable[[str], int]] = {
    "b_initial": lambda t: sum(w.startswith("b") for w in lower_words(t)),
    "ing_final": lambda t: sum(w.endswith("ing") for w in lower_words(t)),
    "one_letter": lambda t: sum(len(w) == 1 for w in _runs(t)),
    "doubled_letter": lambda t: sum(_has_doubled_letter(w) for w in lower_words(t)),
    "comma": lambda t: Counter(t)[","],
    "capital_char": lambda t: sum(n for c, n in Counter(t).items() if c in _ASCII_UPPER),
    "capital_word": lambda t: sum(any(map(_is_upper, w)) for w in _runs(t)),
    "letter_a": lambda t: sum("a" in w for w in lower_words(t)),
    "y_final": lambda t: sum(w.endswith("y") for w in lower_words(t)),
}


def statistic(statistic_id: str, text: str) -> int:
    return _STATISTICS[statistic_id](text)


def family_statistic(family: str, text: str) -> int:
    return statistic(FAMILY_SPEC[family][0], text)


# --- predicates and graded scores ---------------------------------------------------


def passes(kind: str, severity: int, text: str) -> bool:
    """Binary satisfaction; `kind` is "A", "B", or a family identifier.

    A rate over zero words is undefined, and an undefined rate fails in *both*
    directions: a wordless response is neither credited with a lower bound it
    never demonstrated nor excused a budget it never respected."""
    if kind == "A":
        return s0(text) == severity
    if kind == "B":
        return focal_statistic(text) <= severity
    stat_id, form = FAMILY_SPEC[kind]
    value = statistic(stat_id, text)
    if form == "count_budget":
        return value <= severity
    if form == "count_lower_bound":
        return value >= severity
    total = word_count(text)
    if total == 0:
        return False
    rate = 100.0 * value / total
    return rate <= severity if form == "rate_budget" else rate >= severity


def graded(kind: str, severity: int, text: str) -> float:
    """Partial credit in [0, 1]; each form has its own registered shape."""
    if kind == "A":
        if severity == 0:
            # n >= 1 for every registered A; the ratio would be 0/0, so fall back
            # to the degenerate all-or-nothing reading rather than raising.
            return 1.0 if s0(text) == 0 else 0.0
        return max(0.0, 1.0 - abs(s0(text) - severity) / severity)
    if kind == "B":
        lengths = [len(word) for word in _runs(text)]
        if not lengths:
            return 0.0
        return 1.0 - sum(length > severity for length in lengths) / len(lengths)
    stat_id, form = FAMILY_SPEC[kind]
    value = statistic(stat_id, text)
    if form == "count_budget":
        if severity == 0:
            return 1.0 if value == 0 else 0.0
        return min(1.0, severity / max(severity, value))
    if form == "count_lower_bound":
        return min(1.0, value / severity) if severity > 0 else 1.0
    total = word_count(text)
    if total == 0:
        return 0.0
    rate = 100.0 * value / total
    if form == "rate_budget":
        # A zero rate is perfect even at q = 0, where the ratio would be 0/0.
        return 1.0 if rate == 0 else min(1.0, severity / max(severity, rate))
    return min(1.0, rate / severity) if severity > 0 else 1.0


def non_vacuous(kind: str, text: str, truncated: bool) -> bool:
    """Whether the response is a real enough attempt for the score to mean anything.

    Budget forms and B are trivially satisfied by saying almost nothing, so they
    carry a 20-word floor; lower-bound forms and A cannot be gamed that way and
    carry no floor beyond being non-empty and untruncated."""
    if truncated or not text.strip():
        return False
    if kind == "A":
        return True
    if kind == "B":
        return word_count(text) >= MIN_WORDS_NON_VACUOUS
    if FAMILY_SPEC[kind][1].endswith("lower_bound"):
        return True
    return word_count(text) >= MIN_WORDS_NON_VACUOUS
