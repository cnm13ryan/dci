"""Focal and reference-family verifiers (§5).

Every verifier is a deterministic pure function of the response text and its
own severity parameter. Each family exposes a counted *statistic*; the
verdict is ``statistic <= q``. The focal statistic is the maximum word
length; the verdict is ``statistic <= m``. All constraints are single-clause
and apply to the whole answer.

Word tests use the lower-cased word (words.words_lower); the comma and
upper-case budgets read raw response characters (§5).
"""
from __future__ import annotations

from typing import Callable

from dci1v3.errors import ProtocolError
from dci1v3.protocol.constants import FOCAL_GRID, REFERENCE_FAMILIES
from dci1v3.verifiers.words import words_lower


def focal_statistic(text: str) -> int:
    """The longest word's letter count (0 for a wordless answer)."""
    return max((len(w) for w in words_lower(text)), default=0)


def focal_passes(text: str, m: int) -> bool:
    """B: every word in the answer has at most m letters."""
    if m not in FOCAL_GRID:
        raise ProtocolError(f"m={m} outside the registered focal grid")
    return focal_statistic(text) <= m


def _rf1(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.startswith("b"))


def _rf2(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("ing"))


def _rf3(text: str) -> int:
    return sum(1 for w in words_lower(text) if len(w) == 1)


def _rf4(text: str) -> int:
    return sum(1 for w in words_lower(text)
               if any(a == b for a, b in zip(w, w[1:])))


def _rf5(text: str) -> int:
    return text.count(",")


def _rf6(text: str) -> int:
    return sum(1 for ch in text if "A" <= ch <= "Z")


def _rf7(text: str) -> int:
    return sum(1 for w in words_lower(text) if "a" in w)


def _rf8(text: str) -> int:
    return sum(1 for w in words_lower(text) if w.endswith("y"))


FAMILY_STATISTICS: dict[str, Callable[[str], int]] = {
    "RF1": _rf1, "RF2": _rf2, "RF3": _rf3, "RF4": _rf4,
    "RF5": _rf5, "RF6": _rf6, "RF7": _rf7, "RF8": _rf8,
}
assert set(FAMILY_STATISTICS) == set(REFERENCE_FAMILIES)


def family_statistic(family: str, text: str) -> int:
    if family not in FAMILY_STATISTICS:
        raise ProtocolError(f"unknown reference family {family!r}")
    return FAMILY_STATISTICS[family](text)


def family_passes(family: str, text: str, q: int) -> bool:
    """R_f at severity q: the counted statistic is at most q."""
    if q not in REFERENCE_FAMILIES[family]:
        raise ProtocolError(f"severity q={q} outside the registered "
                            f"{family} grid")
    return family_statistic(family, text) <= q


def added_verifier(constraint_id: str, severity: int
                   ) -> Callable[[str], bool]:
    """The uptake verifier for the constraint occupying the added slot.

    Receives only the constraint's own identity and severity; returns a pure
    function of the response text.
    """
    if constraint_id == "B":
        return lambda text: focal_passes(text, severity)
    if constraint_id in REFERENCE_FAMILIES:
        return lambda text: family_passes(constraint_id, text, severity)
    raise ProtocolError(f"unknown added constraint {constraint_id!r}")
