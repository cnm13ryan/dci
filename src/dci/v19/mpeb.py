"""Candidate 1: the Maurer-Pontil empirical-Bernstein lower bound.

Preregistration section 12.5. For contributions D_1..D_H in [a, b] with width
w = b - a, and a one-sided family of size m protected at alpha:

    Dbar = mean(D_i)
    V    = (1 / (H(H-1))) * sum_{i<j} (D_i - D_j)^2
    lam  = log(2m / alpha)
    L    = max{a, Dbar - sqrt(2 V lam / H) - 7 w lam / (3 (H-1))}

Two properties matter more than the algebra:

  * there is NO standard-error denominator. V = 0 is an ordinary numerical
    value: it removes the variance term and leaves the finite-sample range
    term, so an all-zero or all-one primitive still yields a finite, valid,
    support-respecting bound. v15.1 dropped zero-SE members from a studentised
    family; v19 forbids that (section 12.4, register D30) and it is not needed.
  * the range term depends on H and w but NOT on the replicate count G, so
    additional decoder replicates cannot buy their way out of it. The design
    simulator has to report the two terms separately for exactly this reason
    (section 13.4), which is why decompose() exists.

Under permanent technical missingness (section 12.10) the same formula is
evaluated on the lower-endpoint mean and the conservative pairwise variance
envelope V+ = (1/(H(H-1))) sum_{i<j} max{(l_i-u_j)^2, (u_i-l_j)^2}. Pointwise
l_i <= D_i and V+ upper-bounds the latent pairwise variance, so the result is no
larger than the complete-data bound.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT
from dci.v19.supports import Interval, support_width

METHOD_ID = "MP-EB"


@dataclass(frozen=True)
class Bound:
    """A one-sided lower bound and the terms it was built from."""
    lower: float
    mean: float
    variance: float
    variance_term: float
    range_term: float
    n: int
    width: float
    lambda_: float
    clipped_at_support: bool


def one_sided_lambda(family_size: int, alpha: float = ALPHA) -> float:
    """log(2m/alpha): the finite-class union allocation for a one-sided family."""
    if family_size < 1:
        raise ValueError("a family has at least one member")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha={alpha} is not a probability")
    return math.log(2.0 * family_size / alpha)


def two_sided_lambda(family_size: int, alpha: float = ALPHA) -> float:
    """log(4M/alpha): both tails for every member of a two-sided family."""
    if family_size < 1:
        raise ValueError("a family has at least one member")
    return math.log(4.0 * family_size / alpha)


def pairwise_variance(values: Sequence[float]) -> float:
    """V = (1/(H(H-1))) sum_{i<j} (D_i - D_j)^2.

    Algebraically identical to the unbiased sample variance, and written in the
    pairwise form the theorem states so the interval-completed envelope below is
    visibly the same object with each pair replaced by its worst case.
    """
    n = len(values)
    if n < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    total = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            total += (values[i] - values[j]) ** 2
    return total / (n * (n - 1))


def pairwise_variance_envelope(intervals: Sequence[Interval]) -> float:
    """V+ : each pair contributes the larger of its two extreme differences."""
    n = len(intervals)
    if n < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    total = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = intervals[i], intervals[j]
            total += max((a.lower - b.upper) ** 2, (a.upper - b.lower) ** 2)
    return total / (n * (n - 1))


def _bound(mean: float, variance: float, n: int, width: float,
           lam: float, low: float) -> Bound:
    variance_term = math.sqrt(2.0 * variance * lam / n)
    range_term = 7.0 * width * lam / (3.0 * (n - 1))
    raw = mean - variance_term - range_term
    return Bound(lower=max(low, raw), mean=mean, variance=variance,
                 variance_term=variance_term, range_term=range_term, n=n,
                 width=width, lambda_=lam, clipped_at_support=raw < low)


def lower_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA) -> Bound:
    """Complete-data one-sided lower bound."""
    if len(values) < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    lam = one_sided_lambda(family_size, alpha)
    mean = sum(values) / len(values)
    return _bound(mean, pairwise_variance(values), len(values),
                  support_width(support), lam, support[0])


def lower_bound_with_missingness(intervals: Sequence[Interval],
                                 family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA) -> Bound:
    """Interval-completed lower bound: lower-endpoint mean and V+."""
    if len(intervals) < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    lam = one_sided_lambda(family_size, alpha)
    mean = sum(i.lower for i in intervals) / len(intervals)
    return _bound(mean, pairwise_variance_envelope(intervals), len(intervals),
                  support_width(support), lam, support[0])


def upper_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA) -> Bound:
    """The sign-reflected analogue, for a two-sided family.

    Reflection rather than a separate derivation: bounding -D from below and
    negating is the same theorem applied to the same support.
    """
    low, high = support
    reflected = [(-v) for v in values]
    lam = two_sided_lambda(family_size, alpha)
    mean = sum(reflected) / len(reflected)
    got = _bound(mean, pairwise_variance(reflected), len(reflected),
                 support_width(support), lam, -high)
    return Bound(lower=-got.lower, mean=-got.mean, variance=got.variance,
                 variance_term=got.variance_term, range_term=got.range_term,
                 n=got.n, width=got.width, lambda_=lam,
                 clipped_at_support=got.clipped_at_support)


def decompose(bound: Bound) -> dict[str, float]:
    """Variance versus finite-range contribution, and which one dominates.

    Section 13.4 requires this split because only H reduces the range term:
    reporting a single width lets a design spend compute on replicates when the
    term that binds cannot be moved by replicates at all.
    """
    total = bound.variance_term + bound.range_term
    return {"variance_term": bound.variance_term,
            "range_term": bound.range_term,
            "range_share": (bound.range_term / total) if total else 0.0,
            "range_term_dominates": bound.range_term > bound.variance_term,
            "reducible_by_replicates": bound.variance_term}
