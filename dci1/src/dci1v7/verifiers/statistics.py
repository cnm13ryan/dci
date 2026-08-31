"""Counted statistics for every v7 family (§7.6, §9.2).

The library is v5's, carried through v6 into this namespace; "new in v5" and
"carried from v4r4" below are provenance, not descriptions of this revision.

Every statistic is a deterministic pure function of the response text alone:
it receives no companion identity, cell label, order, severity, or other
verifier's output (§7.7 parse independence).

**Twenty-two numerators.** Eight marker occurrences and fourteen carried from
v4r4. §7.3's grammar is (numerator x predicate form), so a family in a new
form changes the *predicate*, not the counting: `XC2` counts what `RF5`
counts and `XC3` counts what `RF12` counts, which is why §10.2's carry-over
evidence covers their numerators and only their form is new.

**A's counter and the eight marker counters are one function with nine
target strings**, ``marker_count``, and that is what makes the same-form claim
an identity of implementation rather than a resemblance of prose. All nine use
§9.2's convention --- segment the answer, then fold each word.
`marker_thus` is carried from v4r4's `CX1`, which made the same choice for the
same reason.

*History of A's counter.* Until 2026-08-29 A was scored by
``dci1v4.verifiers.target.s0_count``, carried byte-identically from the closed
v3 instrument, which lower-cases the whole response **before** segmenting;
the markers segmented first. The two orders differ on exactly one character
of Unicode, U+0130 (``verifiers/words.py``), which occurs in no response any
DCI-1 revision has scored, so no stored A or marker verdict moves under the
shared implementation --- measured over every stored row by
``tools/v7_marker_counter_rescore_audit.py`` rather than asserted. The change
is prospective and is entered in ``CHANGES_SCIENTIFIC.md``; ``dci1v4``'s
``s0_count`` is untouched and still scores every earlier revision's evidence.

**Two statistics read the word as written, not as folded**, because they count
*letters* rather than testing them: ``one_letter`` and ``focal_statistic``,
B's longest word. Folding ``İstanbul`` adds a combining mark that is not a
letter, so a folded length would count something the construct does not.
"""
from __future__ import annotations

from typing import Callable

from dci1v7.verifiers.constraints import (
    FAMILIES, FAMILY_IDS, MARKER_WORDS, STATISTIC_IDS, TARGET_WORD,
)
from dci1v7.verifiers.words import alpha_runs, sentence_units, words_lower

__all__ = ["focal_statistic", "word_count", "STATISTICS", "FAMILY_STATISTICS",
           "family_statistic", "statistic_of", "words_with_capital",
           "marker_count", "MARKER_STATISTICS", "CARRIED_STATISTICS",
           "NEW_STATISTICS", "alpha_runs", "words_lower", "sentence_units",
           "VOWELS", "s0_count"]

def word_count(text: str) -> int:
    """The rate denominator: alphabetic runs, §9.2's *word*."""
    return len(alpha_runs(text))


def focal_statistic(text: str) -> int:
    """B: the longest word's letter count (0 for a wordless answer)."""
    return max((len(run) for run in alpha_runs(text)), default=0)


def marker_count(text: str, marker: str) -> int:
    """§9.2's convention: segment the answer, then fold each word.

    One function, nine target strings: A's own word and the eight registered
    markers. A Tier-1 family is A's *predicate form* over a different marker
    word, and this is where that is an identity of implementation rather than
    a claim about prose --- ``s0_count`` below is this function with
    ``TARGET_WORD`` and nothing else.
    """
    return sum(1 for w in words_lower(text) if w == marker)


def s0_count(text: str) -> int:
    """A's counter, S0: the marker counter with A's own word.

    Not a separate implementation. ``s0_count(text) == marker_count(text,
    TARGET_WORD)`` by definition, which is the literal form of §9.2's claim
    that every Tier-1 family uses the same function with a different target
    string. A's declared alternatives S1 and S2 (§9.2, robustness readings
    that never redefine X_A) stay in ``dci1v4.verifiers.target``.
    """
    return marker_count(text, TARGET_WORD)


def _marker(marker: str) -> Callable[[str], int]:
    def counter(text: str) -> int:
        return marker_count(text, marker)
    counter.__name__ = f"count_{marker}"
    counter.__doc__ = f"Occurrences of the whole word {marker!r} (§7.6, §9.2)."
    return counter


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

    Not RF6's statistic. RF6 counts upper-case *characters*; a rate form is
    denominated in words, so a character numerator over a word denominator
    would not be a proportion of anything.
    """
    return sum(1 for run in alpha_runs(text)
               if any(ch.isupper() for ch in run))


def _letter_a(text: str) -> int:
    return sum(1 for w in words_lower(text) if "a" in w)


def _y_final(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("y"))


def _t_initial(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.startswith("t"))


def _s_final(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("s"))


#: §9.2. The five vowels of the English alphabet; `y` is not one of them here,
#: and the rule statement says so, because `y` already carries a family of its
#: own and a reader asked whether `yellow` begins with a vowel would not agree
#: with themselves.
VOWELS = "aeiou"


def _vowel_initial(text: str) -> int:
    return sum(1 for w in words_lower(text) if w[:1] in VOWELS)


def _sentence(text: str) -> int:
    return sentence_units(text)


def _semicolon(text: str) -> int:
    return text.count(";")


MARKER_STATISTICS: dict[str, Callable[[str], int]] = {
    statistic_id: _marker(word) for statistic_id, word in MARKER_WORDS.items()
}

STATISTICS: dict[str, Callable[[str], int]] = {
    **MARKER_STATISTICS,
    "b_initial": _b_initial, "ing_final": _ing_final,
    "one_letter": _one_letter, "doubled_letter": _doubled_letter,
    "comma": _comma, "capital_char": _capital_char,
    "capital_word": words_with_capital, "letter_a": _letter_a,
    "y_final": _y_final, "t_initial": _t_initial, "s_final": _s_final,
    "vowel_initial": _vowel_initial, "sentence": _sentence,
    "semicolon": _semicolon,
}
assert set(STATISTICS) == set(STATISTIC_IDS), (
    "§7.6 names the registered numerators and this module must supply "
    "exactly those")
assert len(STATISTICS) == 22, "§7.6: twenty-two statistics in all"

#: Which numerators carry v4r4 evidence and which must earn their own
#: (§10.2, §30). Seven of the eight markers are new; `marker_thus` is v4r4's
#: `CX1` numerator carried.
NEW_STATISTICS = tuple(s for s in MARKER_WORDS if s != "marker_thus")
CARRIED_STATISTICS = tuple(k for k in STATISTIC_IDS
                           if k not in NEW_STATISTICS)

FAMILY_STATISTICS: dict[str, Callable[[str], int]] = {
    kind: STATISTICS[family.statistic_id] for kind, family in FAMILIES.items()
}
assert set(FAMILY_STATISTICS) == set(FAMILY_IDS)


def family_statistic(kind: str, text: str) -> int:
    """The numerator of ``kind``'s family, evaluated on ``text``."""
    return FAMILY_STATISTICS[kind](text)


def statistic_of(statistic_id: str, text: str) -> int:
    return STATISTICS[statistic_id](text)
