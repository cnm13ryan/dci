"""Exact supports and interval completion for permanent technical missingness.

v19 handles a generation that never produced durable output bytes by widening
its contribution to an interval, never by deleting the superblock, replacing the
scientific seed, or averaging the observed subset (preregistration section 12.10
and Appendix E). Three properties make that sound and all three are enforced
here rather than assumed:

  * the support is EXACT and declared, not the observed range. A primitive
    contribution lives in [-1, 1] and a secondary difference in [-2, 2] even
    when every realised value sits in a narrower band;
  * a missing binary generation contributes [0, 1] and is propagated through
    the replicate average and the contrast algebra, so the interval endpoints
    are computed rather than guessed;
  * for a linear contrast with known signs, the lower endpoint takes the lower
    end of positively signed terms and the upper end of negatively signed ones,
    and the reverse for the upper endpoint. That is the exact envelope, so it is
    conservative by construction and no MCAR/MAR model is needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from dci.v19 import PRIMITIVE_SUPPORT, SECONDARY_SUPPORT

# A permanently missing binary target verdict. Not 0, not 0.5, not dropped.
MISSING_BINARY = (0.0, 1.0)


@dataclass(frozen=True)
class Interval:
    """A closed contribution interval. Degenerate when observed exactly."""
    lower: float
    upper: float

    def __post_init__(self):
        if not self.lower <= self.upper:
            raise ValueError(f"interval {self.lower} > {self.upper}")

    @property
    def observed(self) -> bool:
        return self.lower == self.upper

    @property
    def span(self) -> float:
        return self.upper - self.lower

    @property
    def midpoint(self) -> float:
        return 0.5 * (self.lower + self.upper)

    def __add__(self, other: "Interval") -> "Interval":
        return Interval(self.lower + other.lower, self.upper + other.upper)

    def __sub__(self, other: "Interval") -> "Interval":
        # The envelope of a difference: worst case pairs this lower endpoint
        # with the other's UPPER endpoint.
        return Interval(self.lower - other.upper, self.upper - other.lower)

    def scaled(self, factor: float) -> "Interval":
        lo, hi = self.lower * factor, self.upper * factor
        return Interval(min(lo, hi), max(lo, hi))

    def clipped(self, support: tuple[float, float]) -> "Interval":
        low, high = support
        return Interval(max(self.lower, low), min(self.upper, high))


def observed(value: float) -> Interval:
    """A delivered behavioural outcome: a point, not an interval.

    A refused, malformed, truncated or empty ANSWER is observed behaviour and
    keeps its 0/1 verdict. Only computation that failed before output bytes were
    persisted becomes an interval.
    """
    return Interval(float(value), float(value))


def missing() -> Interval:
    """A permanently technically missing binary generation."""
    return Interval(*MISSING_BINARY)


def replicate_mean(generations: Sequence[Optional[float]]) -> Interval:
    """Mean target failure over G replicates, with missing ones as [0, 1].

    `None` marks a permanently missing generation. The interval is the exact
    envelope over all binary completions of the missing entries, which is why
    the endpoints are simply the average with the missing terms held at 0 and
    at 1 respectively.
    """
    if not generations:
        raise ValueError("a cell must plan at least one replicate")
    total = len(generations)
    low = sum(0.0 if g is None else float(g) for g in generations) / total
    high = sum(1.0 if g is None else float(g) for g in generations) / total
    return Interval(low, high)


def primitive_contribution(focal: Interval, reference: Interval) -> Interval:
    """One superblock's focal-minus-reference contribution, in [-1, 1]."""
    return (focal - reference).clipped(PRIMITIVE_SUPPORT)


def secondary_contribution(high: Interval, low: Interval) -> Interval:
    """A compute, load or order difference of two primitives, in [-2, 2].

    Section 12.13 gives these endpoints explicitly, for example the paired load
    contrast [l(5) - u(2), u(5) - l(2)]. They are executable definitions and are
    never replaced by a narrower observed range.
    """
    return (high - low).clipped(SECONDARY_SUPPORT)


def linear_contrast(terms: Iterable[tuple[float, Interval]],
                    support: tuple[float, float] = SECONDARY_SUPPORT
                    ) -> Interval:
    """Exact envelope of sum_c s_c * Y_c for known signs s_c (Appendix E).

    Positive terms contribute their lower endpoint to the lower bound and their
    upper endpoint to the upper bound; negative terms contribute the reverse.
    """
    low = high = 0.0
    for sign, value in terms:
        if sign >= 0:
            low += sign * value.lower
            high += sign * value.upper
        else:
            low += sign * value.upper
            high += sign * value.lower
    return Interval(low, high).clipped(support)


def support_width(support: tuple[float, float]) -> float:
    return float(support[1] - support[0])


def normalise(value: float, support: tuple[float, float]) -> float:
    """Map a contribution onto [0, 1] for the betting construction."""
    low, high = support
    width = high - low
    if width <= 0:
        raise ValueError(f"degenerate support {support}")
    return (value - low) / width


def denormalise(value: float, support: tuple[float, float]) -> float:
    low, high = support
    return low + (high - low) * value
