"""Counted statistics for the word-length and reference constraints (v4r2 §7).

Every statistic is a deterministic pure function of the response text alone:
it receives no companion identity, cell label, order, severity, or other
verifier's output (§7.3 parse independence). Pass and graded-score mappings
against a severity live in ``dci1v4.compliance``.

The function sources are byte-identical to the closed v3 instruments
(dci1v3/verifiers/families.py); the identity is recorded as compatibility
evidence by ``dci1v4.carryover``. Unlike v3, no grid check lives here —
severity validation belongs to ``dci1v4.constraints`` and covers the dense
v4 ladders rather than the four-point v3 grids.
"""
from __future__ import annotations

from typing import Callable

from dci1v4.verifiers.constraints import REFERENCE_LADDERS
from dci1v4.verifiers.words import words_lower


def focal_statistic(text: str) -> int:
    """The longest word's letter count (0 for a wordless answer)."""
    return max((len(w) for w in words_lower(text)), default=0)


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
assert set(FAMILY_STATISTICS) == set(REFERENCE_LADDERS)
