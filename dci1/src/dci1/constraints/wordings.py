"""Four frozen wordings per constraint (prereg §5).

Wording index 0 is always the preregistration's canonical text. The four
wordings of a constraint state the same rule; the same verifier decides all
four, and `tests/test_wordings.py` executes all four against the fixed
twenty-response check set (D21) asserting identical verdicts. Meaning-identity
was additionally checked by the researcher before calibration (§5).

Written before calibration; frozen thereafter. Parameters n and m are rendered
as numerals; C1/C2 keep the prereg's spelled-out "two"/"three".
"""
from __future__ import annotations

from dci1.constraints.definitions import CANDIDATE_BY_ID
from dci1.protocol.constants import N_WORDINGS, ProtocolError


def target_wordings(n: int) -> tuple[str, str, str, str]:
    t = "time" if n == 1 else "times"
    return (
        f"Use the word however exactly {n} {t}.",
        f"Your answer must contain the word however exactly {n} {t}.",
        f"Include the word however exactly {n} {t} in your answer.",
        f"The word however must appear exactly {n} {t} in your answer.",
    )


def focal_wordings(m: int) -> tuple[str, str, str, str]:
    return (
        f"Every word in the answer must have at most {m} letters.",
        f"Use only words of {m} letters or fewer in your answer.",
        f"Do not use any word longer than {m} letters.",
        f"Your answer must not contain any word with more than {m} letters.",
    )


_NUMBER_WORD = {2: "two", 3: "three"}

_CANDIDATE_WORDINGS: dict[str, tuple[str, str, str, str]] = {}
for _c in CANDIDATE_BY_ID.values():
    if _c.kind == "min_letters":
        k = _NUMBER_WORD[int(_c.param)]
        _CANDIDATE_WORDINGS[_c.constraint_id] = (
            f"Every word in the answer must have at least {k} letters.",
            f"Use only words of at least {k} letters in your answer.",
            f"Do not use any word shorter than {k} letters.",
            f"Your answer must not contain any word with fewer than {k} letters.",
        )
    elif _c.kind == "no_initial":
        letter = str(_c.param)
        _CANDIDATE_WORDINGS[_c.constraint_id] = (
            f"No word in the answer may begin with the letter {letter}.",
            f"Do not use any word that starts with the letter {letter}.",
            f"Avoid using any word beginning with the letter {letter} in your answer.",
            f"Your answer must not contain any word starting with the letter {letter}.",
        )
    elif _c.kind == "no_suffix":
        suffix = str(_c.param)
        _CANDIDATE_WORDINGS[_c.constraint_id] = (
            f"No word in the answer may end with the letters {suffix}.",
            f"Do not use any word that ends with the letters {suffix}.",
            f"Avoid using any word ending in {suffix} in your answer.",
            f"Your answer must not contain any word ending with the letters {suffix}.",
        )
    elif _c.kind == "no_doubled":
        _CANDIDATE_WORDINGS[_c.constraint_id] = (
            "No word in the answer may contain the same letter twice in a row.",
            "Do not use any word in which a letter appears twice in a row.",
            "Avoid using any word that has two identical letters next to each other.",
            "Your answer must not contain any word with a doubled letter.",
        )


def wording(constraint_id: str, index: int, *, n: int | None = None,
            m: int | None = None) -> str:
    """The frozen wording text for a constraint at a wording index."""
    if not 0 <= index < N_WORDINGS:
        raise ProtocolError(f"wording index {index} outside 0..{N_WORDINGS - 1}")
    if constraint_id == "A":
        if n is None:
            raise ProtocolError("target wording requires n")
        return target_wordings(n)[index]
    if constraint_id == "B":
        if m is None:
            raise ProtocolError("focal wording requires m")
        return focal_wordings(m)[index]
    if constraint_id in _CANDIDATE_WORDINGS:
        return _CANDIDATE_WORDINGS[constraint_id][index]
    raise ProtocolError(f"unknown constraint {constraint_id!r}")


def all_wordings(constraint_id: str, *, n: int | None = None,
                 m: int | None = None) -> tuple[str, ...]:
    return tuple(wording(constraint_id, i, n=n, m=m)
                 for i in range(N_WORDINGS))
