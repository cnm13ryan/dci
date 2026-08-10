"""Candidate 2: the WSR predictable-plug-in betting lower bound.

Preregistration section 12.6. For contributions normalised onto [0, 1],

    mu_t     = (1/2 + sum_{i<=t} x_i) / (t + 1)
    sigma2_t = (1/4 + sum_{i<=t} (x_i - mu_i)^2) / (t + 1),   sigma2_0 = 1/4
    lam~_t   = sqrt(2 log(2/delta) / (H sigma2_{t-1}))
    lam+_t(m)= min{lam~_t, c/m},                              c = 1/2
    K_H(m)   = prod_t [1 + lam+_t(m) (x_t - m)]
    L_X      = sup({m in [0,1] : K_H(m) >= 1/delta} u {0})

Why this is a candidate at all: validity needs only E[X_t | F_{t-1}] = mu, which
section 8.3's independent with-replacement superblock law supplies by
construction. There is no studentisation, so - like MP-EB and unlike the
discarded max-T bootstrap - zero empirical variance is an ordinary case rather
than a failure branch.

Three implementation details are part of the frozen method specification, not
free choices, and each is load-bearing:

  * the stake is PREDICTABLE. lam~_t reads sigma2_{t-1}, computed from strictly
    earlier observations. Using sigma2_t would make the stake depend on the
    observation it is about to bet on and destroy the martingale property.
  * the truncation c/m is operationally material, not an edge case. The tex
    works an example at H=200, sigma2=0.0225 and delta=0.05/144 where lam~ is
    about 1.962 while c/m at m=0.55 is about 0.909, so truncation binds. This is
    why every factor stays nonnegative: lam+_t(m) <= c/m < 1/m.
  * the root is found by conservative bisection to a width of 2^-40, returning
    the LOWER endpoint so floating-point error can never inflate the reported
    bound. K is nonincreasing in m (both branches decrease), so the rejected set
    is a lower interval and bisection is exact up to that width.

Under permanent technical missingness the capital is built from the normalised
LOWER endpoints x_t^-. Pathwise 1 + lam(x^- - m) <= 1 + lam(X - m), and the
stakes computed from earlier lower endpoints are measurable with respect to the
latent past, so the latent process with those same stakes remains a valid test
martingale while the interval-completed capital is no larger.

Two further properties are enforced mechanically because review found both
violated:

  * the horizon H in lam~_t is the FROZEN PLANNED number of superblocks, not the
    length of whatever sequence is in hand. The two coincide for a complete
    design and diverge for a prefix, and betting at H = len(values) when the plan
    said H = 200 is a materially more aggressive process than the one reported.
    `horizon` is therefore threaded through stakes, log-capital, root finding,
    diagnostics, the reflected upper tail and the missingness variants.
  * a two-sided family allocates alpha/(2M) to EACH tail (section 12.12). Pairing
    two alpha/M one-sided endpoints spends 2 alpha. `two_sided_interval` is the
    only sanctioned composition and every Bound records its allocation so the
    incoherent pairing is refused rather than merely discouraged.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Union

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT
from dci.v19.supports import (Interval, assert_intervals_in_support,
                              assert_values_in_support, denormalise, normalise)

METHOD_ID = "WSR-PP"

# Frozen method constants (section 12.6). Changing either is a new method.
TRUNCATION_C = 0.5
BISECTION_WIDTH = 2.0 ** -40
INITIAL_VARIANCE = 0.25

ONE_SIDED = "one_sided"
TWO_SIDED = "two_sided"


class _Unset:
    """Sentinel: no horizon supplied, so the observed length is the plan."""

    def __repr__(self) -> str:                       # pragma: no cover - debug
        return "<horizon unset>"


UNSET = _Unset()


def validate_horizon(horizon: Union[int, _Unset, None], n_observed: int) -> int:
    """The planned horizon H: a positive integer at least as large as the data.

    `None` is deliberately not accepted. An unset horizon is expressed by
    omitting the argument, so a None arriving here is an unthreaded variable
    rather than a decision, and silently substituting len(values) is exactly the
    substitution that produced the reviewed defect.
    """
    if isinstance(horizon, _Unset):
        return n_observed
    if isinstance(horizon, bool) or not isinstance(horizon, int):
        raise TypeError(
            f"horizon must be a positive integer number of planned superblocks, "
            f"got {horizon!r}; pass no horizon to plan at the observed length")
    if horizon < 1:
        raise ValueError(f"horizon {horizon} is not a positive integer")
    if horizon < n_observed:
        raise ValueError(
            f"horizon {horizon} is smaller than the {n_observed} contributions "
            "supplied; more observations than the planned horizon means the "
            "generation manifest and the analysis disagree")
    return horizon


@dataclass(frozen=True)
class Stake:
    """One predictable stake and which branch produced it."""
    index: int
    base: float                 # lam~_t
    truncation: float           # c/m, or inf at m = 0
    value: float                # lam+_t(m)
    truncation_bound: bool      # section 13.4 diagnostic


def memberwise_delta(family_size: int, alpha: float = ALPHA) -> float:
    """delta = alpha_F / M: the generic WSR-PP family rule (section 12.6)."""
    if family_size < 1:
        raise ValueError("a family has at least one member")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha={alpha} is not a probability")
    return alpha / family_size


def predictable_summaries(values: Sequence[float]) -> tuple[list[float], list[float]]:
    """The smoothed running mean and variance, indexed so lam~_t reads t-1.

    Returns (mu, sigma2) with sigma2[0] = 1/4 and sigma2[t] the value available
    AFTER observing x_1..x_t. lam~_t therefore uses sigma2[t-1].
    """
    mu: list[float] = []
    sigma2: list[float] = [INITIAL_VARIANCE]
    running_sum = 0.0
    running_sq = 0.0
    for t, x in enumerate(values, start=1):
        running_sum += x
        mu_t = (0.5 + running_sum) / (t + 1)
        mu.append(mu_t)
        running_sq += (x - mu_t) ** 2
        sigma2.append((0.25 + running_sq) / (t + 1))
    return mu, sigma2


def stakes(values: Sequence[float], candidate_mean: float, horizon: int,
           delta: float) -> list[Stake]:
    """The stake sequence at candidate mean m, with the truncation branch marked.

    `horizon` is the frozen planned H and is required: lam~_t scales as
    1/sqrt(H), so it is the single most consequential input after the data.
    """
    horizon = validate_horizon(horizon, len(values))
    if not 0.0 < delta < 1.0:
        raise ValueError(f"delta={delta} is not a memberwise error allocation")
    _, sigma2 = predictable_summaries(values)
    log_term = 2.0 * math.log(2.0 / delta)
    truncation = math.inf if candidate_mean == 0 else TRUNCATION_C / candidate_mean
    out = []
    for t in range(1, len(values) + 1):
        prior_variance = sigma2[t - 1]
        base = math.sqrt(log_term / (horizon * prior_variance))
        value = min(base, truncation)
        out.append(Stake(index=t, base=base, truncation=truncation, value=value,
                         truncation_bound=truncation <= base))
    return out


def log_capital(values: Sequence[float], candidate_mean: float, delta: float,
                horizon: Union[int, _Unset, None] = UNSET) -> float:
    """log K_H(m), accumulated in the log domain as the method specifies.

    Every factor is at least 1 - c = 1/2 for m > 0 and at least 1 at m = 0, so
    the logarithm is always defined; accumulating in the log domain keeps a long
    horizon from overflowing the product.
    """
    planned = validate_horizon(horizon, len(values))
    total = 0.0
    for stake, x in zip(stakes(values, candidate_mean, planned, delta), values):
        factor = 1.0 + stake.value * (x - candidate_mean)
        if factor <= 0.0:
            # Unreachable under the specified truncation; refuse rather than
            # silently return -inf and report a bound of zero.
            raise AssertionError(
                f"nonpositive capital factor {factor} at m={candidate_mean}; the "
                "truncation constant no longer guarantees nonnegativity")
        total += math.log(factor)
    return total


@dataclass(frozen=True)
class Bound:
    lower: float
    normalised_lower: float
    delta: float
    n: int
    horizon: int
    truncation_bound_fraction: float
    truncation_transitions: int
    allocation: str = ONE_SIDED
    side: str = "lower"

    @property
    def value(self) -> float:
        """The bound itself, whichever side it is. `lower` is the legacy name."""
        return self.lower


def _truncation_diagnostics(values: Sequence[float], m: float, delta: float,
                            horizon: int) -> tuple[float, int]:
    """Section 13.4: how often the truncation branch bound, and transitions.

    Computed at the same horizon that produced the bound, so the diagnostic
    describes the betting process that was actually run.
    """
    if not values:
        return 0.0, 0
    marks = [s.truncation_bound for s in stakes(values, m, horizon, delta)]
    transitions = sum(1 for a, b in zip(marks, marks[1:]) if a != b)
    return sum(marks) / len(marks), transitions


def _normalised_lower_bound(lower_endpoints: Sequence[float], delta: float,
                            horizon: int) -> float:
    """Conservative bisection for sup{m : K_H(m) >= 1/delta}."""
    threshold = math.log(1.0 / delta)
    if log_capital(lower_endpoints, 0.0, delta, horizon) < threshold:
        return 0.0                      # nothing is rejected; the bound is 0
    lo, hi = 0.0, 1.0
    if log_capital(lower_endpoints, 1.0, delta, horizon) >= threshold:
        return 1.0
    while hi - lo > BISECTION_WIDTH:
        mid = 0.5 * (lo + hi)
        if log_capital(lower_endpoints, mid, delta, horizon) >= threshold:
            lo = mid
        else:
            hi = mid
    return lo                            # the LOWER endpoint, deliberately


def _normalised_points(values: Sequence[float],
                       support: tuple[float, float]) -> list[float]:
    if not values:
        raise ValueError("no superblock contributions")
    return [normalise(v, support) for v in assert_values_in_support(values, support)]


def _normalised_endpoints(intervals: Sequence[Interval],
                          support: tuple[float, float]
                          ) -> tuple[list[float], list[float]]:
    if not intervals:
        raise ValueError("no superblock contributions")
    checked = assert_intervals_in_support(intervals, support)
    return ([normalise(iv.lower, support) for iv in checked],
            [normalise(iv.upper, support) for iv in checked])


def _bound_from(root: float, normalised: Sequence[float], delta: float,
                horizon: int, support: tuple[float, float], allocation: str,
                side: str, reflected: bool = False) -> Bound:
    share, transitions = _truncation_diagnostics(normalised, root, delta, horizon)
    normalised_value = (1.0 - root) if reflected else root
    return Bound(lower=denormalise(normalised_value, support),
                 normalised_lower=normalised_value, delta=delta,
                 n=len(normalised), horizon=horizon,
                 truncation_bound_fraction=share,
                 truncation_transitions=transitions,
                 allocation=allocation, side=side)


def _lower(values: Sequence[float], delta: float,
           support: tuple[float, float], horizon: Union[int, _Unset, None],
           allocation: str) -> Bound:
    normalised = _normalised_points(values, support)
    planned = validate_horizon(horizon, len(normalised))
    root = _normalised_lower_bound(normalised, delta, planned)
    return _bound_from(root, normalised, delta, planned, support, allocation,
                       "lower")


def _lower_intervals(intervals: Sequence[Interval], delta: float,
                     support: tuple[float, float],
                     horizon: Union[int, _Unset, None],
                     allocation: str) -> Bound:
    lowers, _ = _normalised_endpoints(intervals, support)
    planned = validate_horizon(horizon, len(lowers))
    root = _normalised_lower_bound(lowers, delta, planned)
    return _bound_from(root, lowers, delta, planned, support, allocation, "lower")


def _upper_intervals(intervals: Sequence[Interval], delta: float,
                     support: tuple[float, float],
                     horizon: Union[int, _Unset, None],
                     allocation: str) -> Bound:
    """U_X = 1 - L_Z on the reflected variables Z = 1 - X (section 12.10).

    The reflected support interval for Z is [1 - x^+, 1 - x^-], so its
    conservative lower endpoint is 1 - x^+: the upper endpoint of the original.
    """
    _, uppers = _normalised_endpoints(intervals, support)
    planned = validate_horizon(horizon, len(uppers))
    reflected = [1.0 - u for u in uppers]
    root = _normalised_lower_bound(reflected, delta, planned)
    return _bound_from(root, reflected, delta, planned, support, allocation,
                       "upper", reflected=True)


def lower_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA,
                horizon: Union[int, _Unset, None] = UNSET) -> Bound:
    """Complete-data ONE-SIDED lower bound at delta = alpha/M.

    This is the primary primitive family's endpoint. It is not an endpoint of the
    declared two-sided interval - see two_sided_interval().
    """
    return _lower(values, memberwise_delta(family_size, alpha), support, horizon,
                  ONE_SIDED)


def lower_bound_with_missingness(intervals: Sequence[Interval], family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA,
                                 horizon: Union[int, _Unset, None] = UNSET
                                 ) -> Bound:
    """Interval-completed one-sided lower bound, from normalised lower endpoints."""
    return _lower_intervals(intervals, memberwise_delta(family_size, alpha),
                            support, horizon, ONE_SIDED)


def upper_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA,
                horizon: Union[int, _Unset, None] = UNSET) -> Bound:
    """The reflected TWO-SIDED upper endpoint for point-valued contributions."""
    return _upper_intervals([Interval(v, v) for v in
                             assert_values_in_support(values, support)],
                            two_sided_delta(family_size, alpha), support,
                            horizon, TWO_SIDED)


def upper_bound_with_missingness(intervals: Sequence[Interval],
                                 family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA,
                                 horizon: Union[int, _Unset, None] = UNSET
                                 ) -> Bound:
    """The reflected TWO-SIDED upper endpoint at delta_tail = alpha/(2M).

    Before repair this used the one-sided alpha/M allocation, so pairing it with
    the ordinary lower bound spent 2 alpha on a family advertised at alpha.
    """
    return _upper_intervals(intervals, two_sided_delta(family_size, alpha),
                            support, horizon, TWO_SIDED)


def two_sided_lower_bound(values: Sequence[float], family_size: int,
                          support: tuple[float, float] = PRIMITIVE_SUPPORT,
                          alpha: float = ALPHA,
                          horizon: Union[int, _Unset, None] = UNSET) -> Bound:
    """The lower endpoint of a two-sided family, at delta_tail = alpha/(2M)."""
    return _lower(values, two_sided_delta(family_size, alpha), support, horizon,
                  TWO_SIDED)


def two_sided_lower_bound_with_missingness(
        intervals: Sequence[Interval], family_size: int,
        support: tuple[float, float] = PRIMITIVE_SUPPORT, alpha: float = ALPHA,
        horizon: Union[int, _Unset, None] = UNSET) -> Bound:
    return _lower_intervals(intervals, two_sided_delta(family_size, alpha),
                            support, horizon, TWO_SIDED)


def two_sided_delta(family_size: int, alpha: float = ALPHA) -> float:
    """delta_tail = alpha / (2M) for a two-sided family (section 12.12)."""
    return memberwise_delta(family_size, alpha) / 2.0


@dataclass(frozen=True)
class TwoSidedInterval:
    """A coherent two-sided WSR-PP interval for one family member.

    Both tails must carry the alpha/(2M) allocation. The class exists so the
    reviewed defect - two alpha/M endpoints presented as one alpha-level interval
    - cannot be assembled by accident.
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
                    f"the {name} tail carries the {bound.allocation!r} "
                    f"allocation; a two-sided interval requires both tails at "
                    f"the {TWO_SIDED!r} allocation alpha/(2M) (section 12.12)")
        expected = two_sided_delta(self.family_size, self.alpha)
        for name, bound in (("lower", self.lower_bound),
                            ("upper", self.upper_bound)):
            if abs(bound.delta - expected) > 1e-18:
                raise ValueError(
                    f"the {name} tail spends delta={bound.delta} but a two-sided "
                    f"family of size {self.family_size} at alpha={self.alpha} "
                    f"allocates {expected} per tail")
        if self.lower_bound.horizon != self.upper_bound.horizon:
            raise ValueError(
                f"the two tails bet at different horizons "
                f"({self.lower_bound.horizon} and {self.upper_bound.horizon}); "
                "one interval describes one betting process")
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
    def total_allocation(self) -> float:
        """What this member spends across both tails: alpha/M, as declared."""
        return self.lower_bound.delta + self.upper_bound.delta

    @property
    def width(self) -> float:
        return self.upper - self.lower


def two_sided_interval(values: Sequence[float], family_size: int,
                       support: tuple[float, float] = PRIMITIVE_SUPPORT,
                       alpha: float = ALPHA,
                       horizon: Union[int, _Unset, None] = UNSET
                       ) -> TwoSidedInterval:
    """The declared two-sided interval: alpha/(2M) on each tail."""
    return TwoSidedInterval(
        lower_bound=two_sided_lower_bound(values, family_size, support, alpha,
                                          horizon),
        upper_bound=upper_bound(values, family_size, support, alpha, horizon),
        family_size=family_size, alpha=alpha)


def two_sided_interval_with_missingness(
        intervals: Sequence[Interval], family_size: int,
        support: tuple[float, float] = PRIMITIVE_SUPPORT, alpha: float = ALPHA,
        horizon: Union[int, _Unset, None] = UNSET) -> TwoSidedInterval:
    """The interval-completed two-sided interval."""
    return TwoSidedInterval(
        lower_bound=two_sided_lower_bound_with_missingness(
            intervals, family_size, support, alpha, horizon),
        upper_bound=upper_bound_with_missingness(
            intervals, family_size, support, alpha, horizon),
        family_size=family_size, alpha=alpha)
