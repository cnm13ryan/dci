"""Registered twenty-response wording-equivalence suites (§5).

Each target, focal, and reference-family template has four frozen wordings.
This module (1) binds every wording text back to its (constraint, severity)
through exact rendered-text matching, and (2) executes the constraint's
verifier on a fixed twenty-response suite whose statistics straddle every
registered severity, asserting that all four wordings return identical
verdicts at every severity. Failure is a qualification failure.
"""
from __future__ import annotations

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import (
    FOCAL_GRID,
    REFERENCE_FAMILIES,
    TARGET_GRID,
)
from dci1v3.protocol.wordings import (
    N_WORDINGS,
    family_wordings,
    focal_wordings,
    target_wordings,
)
from dci1v3.verifiers.families import family_statistic, focal_statistic
from dci1v3.verifiers.target import s0_count

#: Fixed statistic values covering every grid threshold and both neighbours.
SUITE_LEVELS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17,
                23, 24, 25)
assert len(SUITE_LEVELS) == 20

_FILLER = "the wind moves north."
_STAT_TOKENS = {
    "RF1": "bold", "RF2": "going", "RF3": "o", "RF4": "coffee",
    "RF5": ",", "RF6": "Q", "RF7": "cat", "RF8": "grey",
}


def suite_response(constraint_id: str, level: int) -> str:
    """A response whose relevant statistic equals ``level`` exactly."""
    if constraint_id == "A":
        return " ".join(["however"] * level) if level else _FILLER
    if constraint_id == "B":
        word = ("ab" * 20)[:max(level, 4)]
        return f"{word} {_FILLER}"
    token = _STAT_TOKENS[constraint_id]
    if constraint_id == "RF5":
        return _FILLER + "," * level
    if constraint_id == "RF6":
        return _FILLER + " " + "Q" * level if level else _FILLER
    return " ".join([token] * level + [_FILLER]) if level else _FILLER


def suite(constraint_id: str) -> list[str]:
    return [suite_response(constraint_id, level) for level in SUITE_LEVELS]


import functools


@functools.lru_cache(maxsize=4096)
def parse_wording(text: str) -> tuple[str, int]:
    """Bind a rendered wording back to (constraint_id, severity) by exact
    match against every registered rendering; fail closed on ambiguity."""
    matches: list[tuple[str, int]] = []
    for n in TARGET_GRID:
        if text in target_wordings(n):
            matches.append(("A", n))
    for m in FOCAL_GRID:
        if text in focal_wordings(m):
            matches.append(("B", m))
    for family, grid in REFERENCE_FAMILIES.items():
        for q in grid:
            if text in family_wordings(family, q):
                matches.append((family, q))
    if len(matches) != 1:
        raise ProtocolError(f"wording binds to {len(matches)} constraints: "
                            f"{text!r}")
    return matches[0]


def _verdict(constraint_id: str, severity: int, response: str) -> bool:
    if constraint_id == "A":
        return s0_count(response) == severity
    if constraint_id == "B":
        return focal_statistic(response) <= severity
    return family_statistic(constraint_id, response) <= severity


def check_equivalence() -> dict:
    """Every wording of every constraint at every severity binds uniquely
    and yields identical verifier behaviour on the registered suite."""
    checked = 0
    combos: list[tuple[str, int]] = []
    combos += [("A", n) for n in TARGET_GRID]
    combos += [("B", m) for m in FOCAL_GRID]
    for family, grid in REFERENCE_FAMILIES.items():
        combos += [(family, q) for q in grid]
    for constraint_id, severity in combos:
        responses = suite(constraint_id)
        if constraint_id == "A":
            wordings = target_wordings(severity)
        elif constraint_id == "B":
            wordings = focal_wordings(severity)
        else:
            wordings = family_wordings(constraint_id, severity)
        if len(wordings) != N_WORDINGS:
            raise ProtocolError(f"{constraint_id}@{severity}: "
                                f"{len(wordings)} wordings")
        vectors = []
        for text in wordings:
            bound = parse_wording(text)
            if bound != (constraint_id, severity):
                raise ProtocolError(
                    f"wording {text!r} binds to {bound}, not "
                    f"({constraint_id}, {severity})")
            vectors.append([_verdict(*bound, r) for r in responses])
        if any(v != vectors[0] for v in vectors[1:]):
            raise ProtocolError(
                f"{constraint_id}@{severity}: wordings disagree on the "
                f"registered suite")
        checked += 1
    return {"combinations": checked, "suite_size": len(SUITE_LEVELS),
            "equivalent": True}
