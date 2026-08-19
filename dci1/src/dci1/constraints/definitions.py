"""Constraint identities of DCI-1 v2 (prereg §5), transcribed literally.

Target A, focal B, and the twelve-candidate reference pool. Rule parameters
are declared here as data so that the parse-independence property (§5) is an
executable check over declared parameters rather than prose.
"""
from __future__ import annotations

from dataclasses import dataclass

from dci1.protocol.constants import ProtocolError
from dci1.verifiers import pool as pool_verifiers
from dci1.verifiers.words import alpha_runs

#: Letters whose mention by any pool constraint would break parse independence:
#: the letters of the target word (prereg §5).
TARGET_LETTERS = frozenset("however")          # {h, o, w, e, v, r}
TARGET_WORD = "however"


@dataclass(frozen=True)
class Candidate:
    """One reference-pool candidate: identity, rule kind, rule parameter."""

    constraint_id: str
    canonical_text: str
    kind: str            # "min_letters" | "no_initial" | "no_suffix" | "no_doubled"
    param: object        # int for min_letters, str for no_initial/no_suffix, None


CANDIDATES: tuple[Candidate, ...] = (
    Candidate("C1", "Every word in the answer must have at least two letters.",
              "min_letters", 2),
    Candidate("C2", "Every word in the answer must have at least three letters.",
              "min_letters", 3),
    Candidate("C3", "No word in the answer may begin with the letter b.",
              "no_initial", "b"),
    Candidate("C4", "No word in the answer may begin with the letter c.",
              "no_initial", "c"),
    Candidate("C5", "No word in the answer may begin with the letter f.",
              "no_initial", "f"),
    Candidate("C6", "No word in the answer may begin with the letter m.",
              "no_initial", "m"),
    Candidate("C7", "No word in the answer may begin with the letter p.",
              "no_initial", "p"),
    Candidate("C8", "No word in the answer may begin with the letter s.",
              "no_initial", "s"),
    Candidate("C9", "No word in the answer may begin with the letter t.",
              "no_initial", "t"),
    Candidate("C10", "No word in the answer may end with the letters ly.",
              "no_suffix", "ly"),
    Candidate("C11", "No word in the answer may end with the letters ing.",
              "no_suffix", "ing"),
    Candidate("C12",
              "No word in the answer may contain the same letter twice in a row.",
              "no_doubled", None),
)

CANDIDATE_IDS = tuple(c.constraint_id for c in CANDIDATES)
CANDIDATE_BY_ID = {c.constraint_id: c for c in CANDIDATES}


def target_canonical_text(n: int) -> str:
    plural = "time" if n == 1 else "times"
    return f"Use the word however exactly {n} {plural}."


def focal_canonical_text(m: int) -> str:
    return f"Every word in the answer must have at most {m} letters."


def added_verifier(constraint_id: str, param: int | None = None):
    """The verifier for the constraint occupying the added slot.

    Returns a closure ``(response_text) -> bool``. For "B" the focal parameter
    m must be supplied; candidates carry their own declared parameters.
    """
    if constraint_id == "B":
        if param is None:
            raise ProtocolError("focal verifier requires the calibrated m")
        m = int(param)
        return lambda text: pool_verifiers.focal_max_letters(text, m)
    candidate = CANDIDATE_BY_ID.get(constraint_id)
    if candidate is None:
        raise ProtocolError(f"unknown added constraint {constraint_id!r}")
    if candidate.kind == "min_letters":
        k = int(candidate.param)
        return lambda text: pool_verifiers.min_letters(text, k)
    if candidate.kind == "no_initial":
        letter = str(candidate.param)
        return lambda text: pool_verifiers.no_initial(text, letter)
    if candidate.kind == "no_suffix":
        suffix = str(candidate.param)
        return lambda text: pool_verifiers.no_suffix(text, suffix)
    if candidate.kind == "no_doubled":
        return lambda text: pool_verifiers.no_doubled_letter(text)
    raise ProtocolError(f"unknown rule kind {candidate.kind!r}")


def assert_parse_independence() -> dict:
    """Prereg §5: executable form of the parse-independence property.

    No candidate rule parameter names the sequence 'however' or any of the
    letters h, o, w, e, v, r, and the word 'however' itself satisfies every
    candidate rule and every admissible focal value, so no treatment can alter
    the target verifier's decision procedure.
    """
    for candidate in CANDIDATES:
        if candidate.kind in ("no_initial", "no_suffix"):
            mentioned = set(str(candidate.param))
            clash = mentioned & TARGET_LETTERS
            if clash:
                raise ProtocolError(
                    f"{candidate.constraint_id} mentions target letters "
                    f"{sorted(clash)}; parse independence violated")
        if TARGET_WORD in str(candidate.param).lower():
            raise ProtocolError(
                f"{candidate.constraint_id} mentions the target word")
    # 'however': seven letters, no doubled letter, begins with h, ends 'er'.
    for candidate in CANDIDATES:
        if not added_verifier(candidate.constraint_id)(TARGET_WORD):
            raise ProtocolError(
                f"'however' fails {candidate.constraint_id}; the §5 pool "
                f"property does not hold")
    for m in (7, 8, 9, 10):
        if not added_verifier("B", m)(TARGET_WORD):
            raise ProtocolError(f"'however' fails B at m={m}")
    if len(TARGET_WORD) != 7 or alpha_runs(TARGET_WORD) != [TARGET_WORD]:
        raise ProtocolError("target word integrity check failed")
    return {"parse_independent": True,
            "candidates_checked": list(CANDIDATE_IDS),
            "focal_grid_checked": [7, 8, 9, 10]}
