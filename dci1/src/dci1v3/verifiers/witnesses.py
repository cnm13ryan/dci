"""Machine-verified witnesses (§5): joint satisfiability and non-entailment.

For every n, m, family, and severity the protocol contains an answer
satisfying both A and the added constraint, one satisfying A and failing the
added constraint, and one satisfying the added constraint and failing A.
``verify_all_witnesses`` executes every witness against the real verifiers
and is an executable precondition of calibration and confirmation.

The universal joint witness sentence satisfies every registered added
constraint at every severity simultaneously: all lower-case, no commas, no
letter a, no word starting with b, none ending ``ing`` or ``y``, no
one-letter word, no doubled letters, every word at most seven letters, and
exactly one ``however`` per repetition.
"""
from __future__ import annotations

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import (
    FOCAL_GRID,
    REFERENCE_FAMILIES,
    TARGET_GRID,
)
from dci1v3.verifiers.families import family_passes, focal_passes
from dci1v3.verifiers.target import passes, s0_count

_JOINT_SENTENCE = ("however the wind moves north then it turns south "
                   "over time.")
_NO_TARGET_SENTENCE = "the wind moves north then it turns south over time."

#: One token whose repetition k times raises the family statistic by exactly
#: k while leaving every other statistic and the target count unchanged.
_VIOLATION_TOKENS = {
    "B": "extraordinarily",     # 15 letters > every registered m
    "RF1": "bold", "RF2": "going", "RF3": "o", "RF4": "coffee",
    "RF5": ",", "RF6": "Q", "RF7": "cat", "RF8": "grey",
}


def joint_witness(n: int) -> str:
    """Satisfies A at n and every registered added constraint jointly."""
    if n not in TARGET_GRID:
        raise ProtocolError(f"n={n} outside the registered target grid")
    return " ".join([_JOINT_SENTENCE] * n)


def a_only_witness(n: int, constraint_id: str, severity: int) -> str:
    """Satisfies A at n and fails the added constraint at this severity."""
    token = _VIOLATION_TOKENS[constraint_id]
    if constraint_id == "B":
        tail = token
    elif constraint_id == "RF5":
        tail = "," * (severity + 1)
    elif constraint_id == "RF6":
        tail = "Q" * (severity + 1)
    else:
        tail = " ".join([token] * (severity + 1))
    return joint_witness(n) + " " + tail


def added_only_witness() -> str:
    """Satisfies every registered added constraint and fails A (count 0)."""
    return _NO_TARGET_SENTENCE


def _added_passes(constraint_id: str, text: str, severity: int) -> bool:
    if constraint_id == "B":
        return focal_passes(text, severity)
    return family_passes(constraint_id, text, severity)


def verify_composition(n: int, constraint_id: str, severity: int) -> None:
    """Assert all three witnesses for one composition; raise on any failure."""
    joint = joint_witness(n)
    if not passes(s0_count(joint), n):
        raise ProtocolError(f"joint witness fails A at n={n}")
    if not _added_passes(constraint_id, joint, severity):
        raise ProtocolError(f"joint witness fails {constraint_id}@{severity}")
    a_only = a_only_witness(n, constraint_id, severity)
    if not passes(s0_count(a_only), n):
        raise ProtocolError(f"a-only witness fails A at n={n}")
    if _added_passes(constraint_id, a_only, severity):
        raise ProtocolError(
            f"a-only witness passes {constraint_id}@{severity}; "
            f"non-entailment not demonstrated")
    b_only = added_only_witness()
    if not _added_passes(constraint_id, b_only, severity):
        raise ProtocolError(f"added-only witness fails "
                            f"{constraint_id}@{severity}")
    if passes(s0_count(b_only), n):
        raise ProtocolError(f"added-only witness passes A at n={n}; "
                            f"non-entailment not demonstrated")


def all_compositions() -> list[tuple[int, str, int]]:
    out: list[tuple[int, str, int]] = []
    for n in TARGET_GRID:
        for m in FOCAL_GRID:
            out.append((n, "B", m))
        for family, grid in REFERENCE_FAMILIES.items():
            for q in grid:
                out.append((n, family, q))
    return out


def verify_all_witnesses() -> dict:
    """Execute every registered composition's witnesses; fail closed."""
    compositions = all_compositions()
    for n, constraint_id, severity in compositions:
        verify_composition(n, constraint_id, severity)
    return {"compositions": len(compositions), "witnesses_verified": True}
