"""Counted statistics for every v4r3 family (v4r3 §7.0, §7.3, §7.4).

Every statistic is a deterministic pure function of the response text alone:
it receives no companion identity, cell label, order, severity, or other
verifier's output (§7.5 parse independence).

**Fifteen numerators over one corrected word list.** §7.0's grammar is
(numerator x predicate form), so a family in a new form changes the
*predicate*, not the counting: CR4 counts what RF4 counts, CR7 and CL7 and
CP7 count what RF7 counts, CL8 counts what RF8 counts.

The counting predicates are v4r2's, one line each and unchanged in substance.
What changed is the word list they read: ``dci1v4r3.verifiers.words`` composes
segmentation and lower-casing in §7.3's registered order rather than v4r2's,
after §10.2's independent reimplementation disagreed with the carried helper.
That module carries the finding, its one-character scope and its zero realised
frequency. ``assert_agrees_with_v4r2`` re-derives the equivalence here rather
than asserting it in prose: on any response free of U+0130 every one of these
carried functions returns exactly what ``dci1v4.verifiers.statistics``
returns; the six numerators §7.0-R3 adds have no v4r2 counterpart and are
excluded from the equivalence by construction.

**Two statistics are measured on the word as written, not as folded**, because
they count *letters* rather than testing them: ``one_letter`` -- "words that
have exactly one letter" -- and ``focal_statistic``, B's longest word. Folding
``Istanbul`` with a dotted capital adds a combining mark that is not a letter,
so a folded length would count something the construct does not.

**``capital_word`` is the one new numerator and is flagged as such.**
Registered RF6 counts upper-case *characters*. A rate form is denominated in
words -- "at most q percent of words ..." -- so a character numerator over a
word denominator would not be a proportion of anything. CR6 counts *words
containing an upper-case letter*, has no v3 ancestor, and carries no
carry-over evidence; §10.2 requires it to earn its own.

The one rate family whose numerator is not word-shaped is CR5, whose statistic
is comma *characters*. Its wording says so: "at most q comma characters per
hundred words" is a ratio of commas to words, which is a rate people quote,
not a proportion of words. §7.3 records the distinction.
"""
from __future__ import annotations

from typing import Callable

from dci1v4.verifiers.statistics import FAMILY_STATISTICS as _V4_STATISTICS

from dci1v4r3.verifiers.constraints import (
    FAMILIES, FAMILY_IDS, MARKER_WORDS, R3_STATISTIC_IDS, STATISTIC_IDS,
)
from dci1v4r3.verifiers.words import alpha_runs, sentence_units, words_lower

__all__ = ["focal_statistic", "word_count", "STATISTICS", "FAMILY_STATISTICS",
           "family_statistic", "statistic_of", "words_with_capital",
           "CARRIED_STATISTICS", "NEW_STATISTICS", "assert_agrees_with_v4r2",
           "alpha_runs", "words_lower", "sentence_units", "VOWELS"]


def word_count(text: str) -> int:
    """The rate denominator: alphabetic runs, §7.3's *word*."""
    return len(alpha_runs(text))


def focal_statistic(text: str) -> int:
    """B: the longest word's letter count (0 for a wordless answer)."""
    return max((len(run) for run in alpha_runs(text)), default=0)


def _b_initial(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.startswith("b"))


def _ing_final(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("ing"))


def _one_letter(text: str) -> int:
    return sum(1 for run in alpha_runs(text) if len(run) == 1)


def _doubled_letter(text: str) -> int:
    return sum(1 for w in words_lower(text)
               if any(a == b for a, b in zip(w, w[1:])))


def _comma(text: str) -> int:
    return text.count(",")


def _capital_char(text: str) -> int:
    return sum(1 for ch in text if "A" <= ch <= "Z")


def words_with_capital(text: str) -> int:
    """``capital_word``: words containing an upper-case character.

    New in v4r3. See the module docstring for why it is not RF6's statistic.
    """
    return sum(1 for run in alpha_runs(text)
               if any(ch.isupper() for ch in run))


def _letter_a(text: str) -> int:
    return sum(1 for w in words_lower(text) if "a" in w)


def _y_final(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("y"))


# --------------------------------------------------- §7.0-R3's six numerators
#
# Four are word-shaped and read the §7.3 word list, exactly as the nine do.
# `sentence` is the first registered statistic that is not a property of the
# word list at all; `semicolon` reads raw characters, as `comma` does.

def _t_initial(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.startswith("t"))


def _s_final(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("s"))


#: §7.3-R3. The five vowels of the English alphabet; `y` is not one of them
#: here, and the rule statement says so, because `y` already carries a family
#: of its own and a reader asked whether `yellow` begins with a vowel would
#: not agree with themselves.
VOWELS = "aeiou"


def _vowel_initial(text: str) -> int:
    return sum(1 for w in words_lower(text) if w[:1] in VOWELS)


def _sentence(text: str) -> int:
    return sentence_units(text)


def _marker_thus(text: str) -> int:
    """CX1's numerator: occurrences of the marker word.

    §7.3's convention, not §9.2's: segment the answer, then fold each word.
    A's own counter folds first and segments after, and the two readings differ
    on exactly one character of Unicode (`words.py`). CX1 is registered as A's
    *predicate form* over a different marker, not as a byte-identical copy of
    A's counter, and this line is where that distinction lives.
    """
    marker = MARKER_WORDS["marker_thus"]
    return sum(1 for w in words_lower(text) if w == marker)


def _semicolon(text: str) -> int:
    return text.count(";")


#: §7.0's registered numerators, keyed by the registered statistic identifier.
STATISTICS: dict[str, Callable[[str], int]] = {
    "b_initial": _b_initial,
    "ing_final": _ing_final,
    "one_letter": _one_letter,
    "doubled_letter": _doubled_letter,
    "comma": _comma,
    "capital_char": _capital_char,
    "capital_word": words_with_capital,
    "letter_a": _letter_a,
    "y_final": _y_final,
    "t_initial": _t_initial,
    "s_final": _s_final,
    "vowel_initial": _vowel_initial,
    "sentence": _sentence,
    "marker_thus": _marker_thus,
    "semicolon": _semicolon,
}
assert set(STATISTICS) == set(STATISTIC_IDS), (
    "§7.0's grammar names the registered numerators and this module must "
    "supply exactly those")

#: Which numerators carry v3/v4r2 evidence and which must earn their own
#: (§10.2). Reported in the Gate 1 record rather than argued in prose.
NEW_STATISTICS = ("capital_word",) + R3_STATISTIC_IDS
CARRIED_STATISTICS = tuple(k for k in STATISTIC_IDS if k not in NEW_STATISTICS)

FAMILY_STATISTICS: dict[str, Callable[[str], int]] = {
    kind: STATISTICS[family.statistic_id] for kind, family in FAMILIES.items()
}
assert set(FAMILY_STATISTICS) == set(FAMILY_IDS), (
    "every registered family needs exactly one statistic")


def family_statistic(kind: str, text: str) -> int:
    return FAMILY_STATISTICS[kind](text)


def statistic_of(statistic_id: str, text: str) -> int:
    return STATISTICS[statistic_id](text)


#: Which v4r2 family verifier each numerator reproduces, for the equivalence
#: check below. ``capital_word`` has no v4r2 counterpart and is excluded.
_V4_EQUIVALENT = {"b_initial": "RF1", "ing_final": "RF2", "one_letter": "RF3",
                  "doubled_letter": "RF4", "comma": "RF5",
                  "capital_char": "RF6", "letter_a": "RF7", "y_final": "RF8"}


def assert_agrees_with_v4r2(texts) -> dict[str, int]:
    """Every carried numerator returns v4r2's value on U+0130-free text.

    This is the executable form of the scope claim in
    ``dci1v4r3.verifiers.words``: the composition correction changes what a
    verifier returns only where the one splitting character appears, and it
    appears in none of the 285,936 rows this programme has generated. Run over
    the real corpus, a clean result means the correction moves no measured
    number; run over text containing U+0130, it is *expected* to differ and
    the caller is told which texts were skipped.
    """
    checked = skipped = 0
    for text in texts:
        if "\u0130" in text:
            skipped += 1
            continue
        for statistic_id, family in _V4_EQUIVALENT.items():
            mine = STATISTICS[statistic_id](text)
            theirs = _V4_STATISTICS[family](text)
            if mine != theirs:
                raise AssertionError(
                    f"{statistic_id} reads {mine} where v4r2 reads {theirs} "
                    f"on a response with no U+0130: {text[:80]!r}. §7.3's "
                    "correction is scoped to that character alone and the "
                    "scope claim has failed")
        checked += 1
    return {"checked": checked, "skipped_containing_u0130": skipped}
