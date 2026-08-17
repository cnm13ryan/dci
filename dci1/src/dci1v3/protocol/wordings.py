"""Four frozen wordings per constraint template (§5, §18.4).

Wording index 0 is the preregistration's canonical text. All four wordings of
a template state the same rule; one verifier decides all four, and the
registered twenty-response suites assert identical verdicts at every severity
(verifiers/wording_suite.py). Written before qualification; frozen.

Severity parameters render as numerals. A *word* for the length caliper is a
maximal alphabetic run (the study's word rule), so numerals contribute no
words and the caliper is severity-invariant. Gate 2A requires every reference
wording within 20% of the corresponding focal wording's word count.
"""
from __future__ import annotations

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import (
    FAMILY_IDS,
    FOCAL_GRID,
    REFERENCE_FAMILIES,
    TARGET_GRID,
    WORDING_LENGTH_TOLERANCE,
)

N_WORDINGS = 4


def target_wordings(n: int) -> tuple[str, str, str, str]:
    if n not in TARGET_GRID:
        raise ProtocolError(f"n={n} outside the registered target grid")
    t = "time" if n == 1 else "times"
    return (
        f"Use the word however exactly {n} {t}.",
        f"Your answer must contain the word however exactly {n} {t}.",
        f"Include the word however exactly {n} {t} in your answer.",
        f"The word however must appear exactly {n} {t} in your answer.",
    )


def focal_wordings(m: int) -> tuple[str, str, str, str]:
    if m not in FOCAL_GRID:
        raise ProtocolError(f"m={m} outside the registered focal grid")
    return (
        f"Every word in the answer must have at most {m} letters.",
        f"Use only words of {m} letters or fewer in your answer.",
        f"Do not use any word longer than {m} letters.",
        f"Your answer must not contain any word with more than {m} letters.",
    )


_FAMILY_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "RF1": (
        "At most {q} words in the answer may begin with the letter b.",
        "Use at most {q} words that start with the letter b.",
        "No more than {q} words may start with b.",
        "Your answer may contain at most {q} words beginning with the letter b.",
    ),
    "RF2": (
        "At most {q} words in the answer may end with the letters ing.",
        "Use at most {q} words that end with the letters ing.",
        "No more than {q} words may end in ing.",
        "Your answer may contain at most {q} words ending with the letters ing.",
    ),
    "RF3": (
        "At most {q} words in the answer may have one letter.",
        "Use at most {q} words consisting of a single letter.",
        "No more than {q} words may have one letter.",
        "Your answer may contain at most {q} words that have one letter.",
    ),
    "RF4": (
        "At most {q} words may contain two identical adjacent letters.",
        "Use at most {q} words containing the same letter twice in a row.",
        "No more than {q} words may contain a doubled letter.",
        "Your answer may contain at most {q} words with a doubled letter.",
    ),
    "RF5": (
        "The answer may contain at most {q} comma characters.",
        "Use at most {q} comma characters in your whole answer.",
        "No more than {q} commas may appear in the answer.",
        "Your answer must not contain more than {q} comma characters.",
    ),
    "RF6": (
        "The answer may contain at most {q} upper-case English letters.",
        "Use at most {q} upper-case English letters in your answer.",
        "No more than {q} upper-case English letters may appear.",
        "Your answer must not contain more than {q} upper-case English letters.",
    ),
    "RF7": (
        "At most {q} words in the answer may contain the letter a.",
        "Use at most {q} words that contain the letter a.",
        "No more than {q} words may contain the letter a.",
        "Your answer may contain at most {q} words with the letter a.",
    ),
    "RF8": (
        "At most {q} words in the answer may end with the letter y.",
        "Use at most {q} words that end with the letter y.",
        "No more than {q} words may end in y.",
        "Your answer may contain at most {q} words ending with the letter y.",
    ),
}
assert set(_FAMILY_TEMPLATES) == set(FAMILY_IDS)


def family_wordings(family: str, q: int) -> tuple[str, str, str, str]:
    if family not in REFERENCE_FAMILIES:
        raise ProtocolError(f"unknown reference family {family!r}")
    if q not in REFERENCE_FAMILIES[family]:
        raise ProtocolError(f"severity q={q} outside the registered "
                            f"{family} grid")
    return tuple(t.format(q=q) for t in _FAMILY_TEMPLATES[family])


def wording(constraint_id: str, index: int, *, n: int | None = None,
            m: int | None = None, q: int | None = None) -> str:
    """The frozen wording text for one constraint at one wording index."""
    if not 0 <= index < N_WORDINGS:
        raise ProtocolError(f"wording index {index} outside 0..3")
    if constraint_id == "A":
        if n is None:
            raise ProtocolError("target wording requires n")
        return target_wordings(n)[index]
    if constraint_id == "B":
        if m is None:
            raise ProtocolError("focal wording requires m")
        return focal_wordings(m)[index]
    if constraint_id in REFERENCE_FAMILIES:
        if q is None:
            raise ProtocolError("reference wording requires a severity q")
        return family_wordings(constraint_id, q)[index]
    raise ProtocolError(f"unknown constraint {constraint_id!r}")


def wording_word_count(text: str) -> int:
    """Word count under the study's word rule (maximal alphabetic runs)."""
    count, in_run = 0, False
    for ch in text:
        if ch.isalpha():
            if not in_run:
                count += 1
                in_run = True
        else:
            in_run = False
    return count


def length_caliper_ok(family: str, q: int, m: int) -> bool:
    """§18.4 condition 2: every frozen wording within 20% of the
    corresponding focal wording's word count."""
    focal = [wording_word_count(w) for w in focal_wordings(m)]
    ref = [wording_word_count(w) for w in family_wordings(family, q)]
    tol = WORDING_LENGTH_TOLERANCE
    return all(abs(r - f) <= tol * f for r, f in zip(ref, focal))
