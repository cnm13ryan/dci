"""Interval machinery: Wilson score intervals (§18.2, §10) and the Newcombe
difference interval (§18.2). Deterministic, dependency-light."""
from __future__ import annotations

import math

Z_TWO_SIDED_95 = 1.959963984540054
Z_ONE_SIDED_95 = 1.6448536269514722


def wilson_interval(successes: int, trials: int,
                    z: float = Z_TWO_SIDED_95) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("Wilson interval needs at least one trial")
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / trials
                                   + z * z / (4 * trials * trials))
    return (max(0.0, centre - half), min(1.0, centre + half))


def wilson_upper_one_sided(disagreements: int, trials: int) -> float:
    """The one-sided 95% Wilson upper bound on a proportion (§10)."""
    return wilson_interval(disagreements, trials, z=Z_ONE_SIDED_95)[1]


def newcombe_interval(k1: int, n1: int, k2: int, n2: int
                      ) -> tuple[float, float]:
    """95% Newcombe (score-based) interval for p1 - p2 (§18.2)."""
    l1, u1 = wilson_interval(k1, n1)
    l2, u2 = wilson_interval(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    diff = p1 - p2
    lower = diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (max(-1.0, lower), min(1.0, upper))


def intersects(interval: tuple[float, float],
               band: tuple[float, float]) -> bool:
    return interval[0] <= band[1] and interval[1] >= band[0]


def inside(interval: tuple[float, float],
           band: tuple[float, float]) -> bool:
    return band[0] <= interval[0] and interval[1] <= band[1]
