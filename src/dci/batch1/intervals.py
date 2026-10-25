"""Binomial intervals for pilot reporting and boundary decisions.

Wilson score intervals for one proportion and Newcombe's hybrid score
interval (method 10) for a difference of two independent proportions. Both
are closed-form, defined at k = 0 and k = n, and need no simulation. They
report uncertainty and flag boundary cells; no pilot decision is made on an
interval except Stage 2's choice of which cells to refine.
"""
from __future__ import annotations

import math

__all__ = ["wilson", "newcombe", "boundary_distance"]


def wilson(k: int, n: int, z: float) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    if not 0 <= k <= n:
        raise ValueError(f"k={k} outside 0..{n}")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def newcombe(k1: int, n1: int, k2: int, n2: int, z: float
             ) -> tuple[float, float]:
    """Interval for p1 - p2."""
    p1, p2 = (k1 / n1 if n1 else 0.0), (k2 / n2 if n2 else 0.0)
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    # Squares as products, not ``** 2``: a float power goes through the C
    # library's pow, which is not correctly rounded on every platform, so
    # the pilot of 2026-10-25 hashed differently on Linux and macOS in the
    # last digit. Multiplication and sqrt are exactly rounded (IEEE 754);
    # this reproduces every Linux value of that pilot (revision 2026-10).
    a, b = p1 - l1, u2 - p2
    c, e = u1 - p1, p2 - l2
    lower = d - math.sqrt(a * a + b * b)
    upper = d + math.sqrt(c * c + e * e)
    return (max(-1.0, lower), min(1.0, upper))


def boundary_distance(estimate: float, boundary: float, se: float) -> float:
    """Standardised distance to a boundary, for ranking refinement cells."""
    return abs(estimate - boundary) / se if se > 0 else math.inf
