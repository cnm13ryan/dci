"""Candidate reference constraints for the FORM factor.

Six candidate families. Every numerator is a REGISTERED statistic, imported
unchanged from ``dci1v4.verifiers.statistics`` — the candidates change the
*predicate*, not the counting. One exception is stated explicitly below.

Naming: ``CR*`` = candidate rate form, ``CL*`` = candidate lower-bound form.
The registered ``RF*`` names are never reused, so no artifact of this screen can
be mistaken for a registered family.
"""
from __future__ import annotations

from dataclasses import dataclass

from dci1v4.verifiers.statistics import FAMILY_STATISTICS
from dci1v4.verifiers.words import alpha_runs


def _words_with_capital(text: str) -> int:
    """CR6's numerator: WORDS containing an upper-case letter.

    Registered RF6 counts upper-case *characters*. A rate form is denominated in
    words ("at most q% of words ..."), so a character numerator over a word
    denominator would not be a proportion of anything. CR6 therefore counts
    words, and is a genuinely new statistic rather than a re-predicated RF6.
    This is the one candidate numerator that is not byte-identical to a
    registered one, and it is recorded as such in the frozen screen protocol.
    """
    return sum(1 for run in alpha_runs(text)
               if any(ch.isupper() for ch in run))


#: kind -> (numerator, form, ladder, registered statistic reused?)
@dataclass(frozen=True)
class CandidateFamily:
    kind: str
    form: str                      # "rate" | "lower_bound"
    numerator: str                 # human-readable description
    ladder: tuple[int, ...]
    statistic_source: str          # registered family reused, or "new"
    rule_statement: str


#: Rate ladders are integer percentage points spanning the range observed on
#: A-solo text across all four models in the 2026-08-20 diagnostic, with
#: headroom at both ends. Lower-bound ladders are absolute counts and are
#: roughly geometric, because the counts differ ~4x between the Gemmas and the
#: Qwens while the RATES do not -- itself a finding, recorded in the report.
CANDIDATES: dict[str, CandidateFamily] = {
    "CR7": CandidateFamily(
        "CR7", "rate", "words containing the letter a",
        (24, 28, 32, 36, 40, 44, 48, 52), "RF7",
        "At most q percent of words may contain the letter a."),
    "CR4": CandidateFamily(
        "CR4", "rate", "words containing two identical adjacent letters",
        (3, 5, 7, 9, 11, 13, 15, 18), "RF4",
        "At most q percent of words may contain doubled letters."),
    "CR6": CandidateFamily(
        "CR6", "rate", "words containing an upper-case letter",
        (3, 4, 5, 6, 7, 8, 10, 12), "new",
        "At most q percent of words may use capitals."),
    "CL1": CandidateFamily(
        "CL1", "lower_bound", "words beginning with the letter b",
        (1, 2, 3, 4, 6, 8, 11, 15), "RF1",
        "At least q words in the answer must begin with the letter b."),
    "CL7": CandidateFamily(
        "CL7", "lower_bound", "words containing the letter a",
        (10, 20, 30, 45, 60, 80, 100, 130), "RF7",
        "At least q words in the answer must contain the letter a."),
    "CL8": CandidateFamily(
        "CL8", "lower_bound", "words ending with the letter y",
        (2, 3, 5, 7, 10, 14, 19, 25), "RF8",
        "At least q words in the answer must end with the letter y."),
}

CANDIDATE_IDS = tuple(CANDIDATES)

#: RF2 is deliberately absent. Words ending in *ing* are frequently seven
#: letters or more, so a lower-bound RF2 fights B at m = 7: the two constraints
#: would be jointly unsatisfiable at the restrictive end of the focal grid.
#: ``witnesses.assert_rf2_conflict`` proves it rather than asserting it.
EXCLUDED_FROM_CANDIDATES = {"RF2": "lower-bound RF2 conflicts with B at m=7"}

_NUMERATORS = {
    "CR7": FAMILY_STATISTICS["RF7"], "CL7": FAMILY_STATISTICS["RF7"],
    "CR4": FAMILY_STATISTICS["RF4"], "CL1": FAMILY_STATISTICS["RF1"],
    "CL8": FAMILY_STATISTICS["RF8"], "CR6": _words_with_capital,
}


def statistic(kind: str, text: str) -> int:
    """The raw numerator count, before any predicate."""
    return _NUMERATORS[kind](text)


def word_count(text: str) -> int:
    return len(alpha_runs(text))


def passes(kind: str, severity: int, text: str) -> bool:
    """The candidate predicate.

    rate:        100 * S / words <= q     (a wordless answer has no rate; it
                                           fails, which is the whole point)
    lower_bound: S >= q
    """
    family = CANDIDATES[kind]
    count = statistic(kind, text)
    if family.form == "lower_bound":
        return count >= severity
    words = word_count(text)
    if words == 0:
        return False
    return 100.0 * count / words <= severity


def graded(kind: str, severity: int, text: str) -> float:
    """A graded score in [0, 1], same spirit as the registered §7.4 forms."""
    family = CANDIDATES[kind]
    count = statistic(kind, text)
    if family.form == "lower_bound":
        return min(1.0, count / severity) if severity else 1.0
    words = word_count(text)
    if words == 0:
        return 0.0
    rate = 100.0 * count / words
    return min(1.0, severity / max(severity, rate)) if rate else 1.0


def ladder(kind: str) -> tuple[int, ...]:
    return CANDIDATES[kind].ladder


def all_severities() -> list[tuple[str, int]]:
    return [(k, q) for k in CANDIDATE_IDS for q in CANDIDATES[k].ladder]
