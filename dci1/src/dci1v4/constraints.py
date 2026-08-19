"""Registered constraints and severity grids (v4r2 §7.1–§7.2).

Two outcome constraints — A (use the target word exactly n times) and B
(every word at most m letters) — and eight reference families, each
carrying the complete integer severity ladder from 0 to its registered
maximum: 94 reference severities in total. The family maxima are the v3
grid maxima; v4 fills the interiors.
"""
from __future__ import annotations

from dataclasses import dataclass

from dci1v4.errors import InstrumentError
from dci1v4.target import TARGET_WORD

__all__ = ["TARGET_WORD", "TARGET_GRID", "FOCAL_GRID", "REFERENCE_LADDERS",
           "KINDS", "Constraint", "registered_severities"]

TARGET_GRID = tuple(range(1, 9))                    # A: n
FOCAL_GRID = (7, 8, 9, 10)                          # B: m

#: family -> complete integer ladder, from 0 (the most restrictive budget)
#: to the registered maximum (the v3 grid maximum).
REFERENCE_LADDERS: dict[str, tuple[int, ...]] = {
    "RF1": tuple(range(0, 9)),    # words beginning with b
    "RF2": tuple(range(0, 9)),    # words ending with ing
    "RF3": tuple(range(0, 9)),    # one-letter words
    "RF4": tuple(range(0, 7)),    # words with identical adjacent letters
    "RF5": tuple(range(0, 13)),   # comma characters
    "RF6": tuple(range(0, 13)),   # upper-case English letters
    "RF7": tuple(range(0, 25)),   # words containing a
    "RF8": tuple(range(0, 9)),    # words ending with y
}

KINDS = ("A", "B") + tuple(REFERENCE_LADDERS)


def registered_severities(kind: str) -> tuple[int, ...]:
    if kind == "A":
        return TARGET_GRID
    if kind == "B":
        return FOCAL_GRID
    if kind in REFERENCE_LADDERS:
        return REFERENCE_LADDERS[kind]
    raise InstrumentError(f"unknown constraint kind {kind!r}")


@dataclass(frozen=True)
class Constraint:
    """One registered constraint instance: a kind and a severity."""

    kind: str
    severity: int

    def __post_init__(self):
        if self.severity not in registered_severities(self.kind):
            raise InstrumentError(
                f"severity {self.severity} outside the registered "
                f"{self.kind} grid")
