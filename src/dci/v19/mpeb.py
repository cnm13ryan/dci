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

Two allocations exist and must not be mixed. The primary one-sided primitive
family uses lam = log(2m/alpha). A declared two-sided family of size M uses
lam_2 = log(4M/alpha) on BOTH tails (section 12.12), which is why every Bound
records which allocation produced it and why TwoSidedInterval refuses a pair that
does not agree: assembling a log(2M/alpha) lower endpoint with a log(4M/alpha)
upper endpoint advertises alpha while spending closer to 1.5 alpha.

Every entry point validates its inputs against the declared support first. The
empirical-Bernstein theorem is a statement about variables confined to [a, b]; a
scorer contribution of 5.0 under support [-1, 1] does not make the bound slightly
optimistic, it makes the theorem inapplicable, and unvalidated input of that kind
produced a "lower bound" above 4 in review.

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
from dci.v19.supports import (Interval, assert_intervals_in_support,
                              assert_support, assert_values_in_support,
                              support_width)

METHOD_ID = "MP-EB"

# Which familywise allocation a bound was built with. Recorded on the bound
# itself so a one-sided endpoint cannot be silently composed into something
# labelled a two-sided interval: section 12.12 gives each two-sided family the
# lambda_2 = log(4M/alpha) allocation for BOTH tails, and pairing a log(2M/alpha)
# lower endpoint with a log(4M/alpha) upper one controls neither level.
ONE_SIDED = "one_sided"
TWO_SIDED = "two_sided"


@dataclass(frozen=True)
class Bound:
    """One endpoint and the terms it was built from."""
    lower: float
    mean: float
    variance: float
    variance_term: float
    range_term: float
    n: int
    width: float
    lambda_: float
    clipped_at_support: bool
    allocation: str = ONE_SIDED
    side: str = "lower"

    @property
    def value(self) -> float:
        """The bound itself, whichever side it is. `lower` is the legacy name."""
        return self.lower


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


def _bound(mean: float, variance: float, n: int, width: float, lam: float,
           low: float, allocation: str, side: str) -> Bound:
    variance_term = math.sqrt(2.0 * variance * lam / n)
    range_term = 7.0 * width * lam / (3.0 * (n - 1))
    raw = mean - variance_term - range_term
    return Bound(lower=max(low, raw), mean=mean, variance=variance,
                 variance_term=variance_term, range_term=range_term, n=n,
                 width=width, lambda_=lam, clipped_at_support=raw < low,
                 allocation=allocation, side=side)


def _checked_values(values: Sequence[float],
                    support: tuple[float, float]) -> list[float]:
    if len(values) < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    return assert_values_in_support(values, support)


def _checked_intervals(intervals: Sequence[Interval],
                       support: tuple[float, float]) -> list[Interval]:
    if len(intervals) < 2:
        raise ValueError("the empirical-Bernstein bound needs H >= 2")
    return assert_intervals_in_support(intervals, support)


def _lower_at(values: Sequence[float], lam: float,
              support: tuple[float, float], allocation: str) -> Bound:
    low, _ = assert_support(support)
    mean = sum(values) / len(values)
    return _bound(mean, pairwise_variance(values), len(values),
                  support_width(support), lam, low, allocation, "lower")


def _lower_at_intervals(intervals: Sequence[Interval], lam: float,
                        support: tuple[float, float], allocation: str) -> Bound:
    low, _ = assert_support(support)
    mean = sum(i.lower for i in intervals) / len(intervals)
    return _bound(mean, pairwise_variance_envelope(intervals), len(intervals),
                  support_width(support), lam, low, allocation, "lower")


def _upper_from(reflected: Bound, lam: float, allocation: str) -> Bound:
    """Negate a lower bound computed on the sign-reflected contributions."""
    return Bound(lower=-reflected.lower, mean=-reflected.mean,
                 variance=reflected.variance,
                 variance_term=reflected.variance_term,
                 range_term=reflected.range_term, n=reflected.n,
                 width=reflected.width, lambda_=lam,
                 clipped_at_support=reflected.clipped_at_support,
                 allocation=allocation, side="upper")


def lower_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA) -> Bound:
    """Complete-data one-sided lower bound, log(2m/alpha) allocation.

    This is the primary primitive family's endpoint (section 12.5). It is NOT an
    endpoint of the declared two-sided interval - use two_sided_interval() for
    that, which spends log(4M/alpha) on each tail.
    """
    checked = _checked_values(values, support)
    return _lower_at(checked, one_sided_lambda(family_size, alpha), support,
                     ONE_SIDED)


def lower_bound_with_missingness(intervals: Sequence[Interval],
                                 family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA) -> Bound:
    """Interval-completed one-sided lower bound: lower-endpoint mean and V+."""
    checked = _checked_intervals(intervals, support)
    return _lower_at_intervals(checked, one_sided_lambda(family_size, alpha),
                               support, ONE_SIDED)


def upper_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA) -> Bound:
    """The sign-reflected upper endpoint of a TWO-SIDED family.

    Reflection rather than a separate derivation: bounding -D from below and
    negating is the same theorem applied to the reflected support. It carries the
    two-sided allocation, so it may only be paired with two_sided_lower_bound().
    """
    checked = _checked_values(values, support)
    low, high = assert_support(support)
    lam = two_sided_lambda(family_size, alpha)
    reflected = _lower_at([-v for v in checked], lam, (-high, -low), TWO_SIDED)
    return _upper_from(reflected, lam, TWO_SIDED)


def upper_bound_with_missingness(intervals: Sequence[Interval],
                                 family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA) -> Bound:
    """Interval-completed two-sided upper endpoint.

    Reflecting an interval swaps and negates its endpoints, so the reflected
    lower endpoint is -u_i: the conservative side for an upper bound. The
    pairwise envelope V+ is invariant under this reflection, which is why the
    same envelope function is reused.
    """
    checked = _checked_intervals(intervals, support)
    low, high = assert_support(support)
    lam = two_sided_lambda(family_size, alpha)
    flipped = [Interval(-iv.upper, -iv.lower) for iv in checked]
    reflected = _lower_at_intervals(flipped, lam, (-high, -low), TWO_SIDED)
    return _upper_from(reflected, lam, TWO_SIDED)


def two_sided_lower_bound(values: Sequence[float], family_size: int,
                          support: tuple[float, float] = PRIMITIVE_SUPPORT,
                          alpha: float = ALPHA) -> Bound:
    """The lower endpoint of a two-sided family, at log(4M/alpha)."""
    checked = _checked_values(values, support)
    return _lower_at(checked, two_sided_lambda(family_size, alpha), support,
                     TWO_SIDED)


def two_sided_lower_bound_with_missingness(
        intervals: Sequence[Interval], family_size: int,
        support: tuple[float, float] = PRIMITIVE_SUPPORT,
        alpha: float = ALPHA) -> Bound:
    checked = _checked_intervals(intervals, support)
    return _lower_at_intervals(checked, two_sided_lambda(family_size, alpha),
                               support, TWO_SIDED)


@dataclass(frozen=True)
class TwoSidedInterval:
    """A coherent two-sided MP-EB interval for one family member.

    Both endpoints must carry the two-sided allocation and the identical lambda.
    Composing a one-sided lower endpoint with a two-sided upper one - the defect
    this class exists to make impossible - would advertise level alpha while
    spending more.
    """
    lower_bound: Bound
    upper_bound: Bound
    family_size: int
    alpha: float

    def __post_init__(self):
        for name, bound in (("lower", self.lower_bound),
                            ("upper", self.upper_bound)):
            if bound.allocation != TWO_SIDED:
                raise ValueError(
                    f"the {name} endpoint carries the {bound.allocation!r} "
                    f"allocation; a two-sided interval requires both endpoints "
                    f"built with the {TWO_SIDED!r} allocation lambda_2 = "
                    "log(4M/alpha) (section 12.12)")
        if self.lower_bound.lambda_ != self.upper_bound.lambda_:
            raise ValueError(
                f"endpoint allocations differ: lambda {self.lower_bound.lambda_}"
                f" versus {self.upper_bound.lambda_}; both tails of one family "
                "member must use the same two-sided allocation")
        if self.lower > self.upper:
            raise ValueError(
                f"two-sided interval [{self.lower}, {self.upper}] is inverted")

    @property
    def lower(self) -> float:
        return self.lower_bound.value

    @property
    def upper(self) -> float:
        return self.upper_bound.value

    @property
    def lambda_(self) -> float:
        return self.lower_bound.lambda_

    @property
    def width(self) -> float:
        return self.upper - self.lower


def two_sided_interval(values: Sequence[float], family_size: int,
                       support: tuple[float, float] = PRIMITIVE_SUPPORT,
                       alpha: float = ALPHA) -> TwoSidedInterval:
    """The declared two-sided interval: log(4M/alpha) on each tail."""
    return TwoSidedInterval(
        lower_bound=two_sided_lower_bound(values, family_size, support, alpha),
        upper_bound=upper_bound(values, family_size, support, alpha),
        family_size=family_size, alpha=alpha)


def two_sided_interval_with_missingness(
        intervals: Sequence[Interval], family_size: int,
        support: tuple[float, float] = PRIMITIVE_SUPPORT,
        alpha: float = ALPHA) -> TwoSidedInterval:
    """The interval-completed two-sided interval."""
    return TwoSidedInterval(
        lower_bound=two_sided_lower_bound_with_missingness(
            intervals, family_size, support, alpha),
        upper_bound=upper_bound_with_missingness(
            intervals, family_size, support, alpha),
        family_size=family_size, alpha=alpha)


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
