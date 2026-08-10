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
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT
from dci.v19.supports import Interval, denormalise, normalise, support_width

METHOD_ID = "WSR-PP"

# Frozen method constants (section 12.6). Changing either is a new method.
TRUNCATION_C = 0.5
BISECTION_WIDTH = 2.0 ** -40
INITIAL_VARIANCE = 0.25


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
    """The stake sequence at candidate mean m, with the truncation branch marked."""
    if horizon < 1:
        raise ValueError("the horizon is the frozen number of superblocks")
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


def log_capital(values: Sequence[float], candidate_mean: float,
                delta: float) -> float:
    """log K_H(m), accumulated in the log domain as the method specifies.

    Every factor is at least 1 - c = 1/2 for m > 0 and at least 1 at m = 0, so
    the logarithm is always defined; accumulating in the log domain keeps a long
    horizon from overflowing the product.
    """
    total = 0.0
    for stake, x in zip(stakes(values, candidate_mean, len(values), delta), values):
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


def _truncation_diagnostics(values: Sequence[float], m: float,
                            delta: float) -> tuple[float, int]:
    """Section 13.4: how often the truncation branch bound, and transitions."""
    if not values:
        return 0.0, 0
    marks = [s.truncation_bound for s in stakes(values, m, len(values), delta)]
    transitions = sum(1 for a, b in zip(marks, marks[1:]) if a != b)
    return sum(marks) / len(marks), transitions


def _normalised_lower_bound(lower_endpoints: Sequence[float],
                            delta: float) -> float:
    """Conservative bisection for sup{m : K(m) >= 1/delta}."""
    threshold = math.log(1.0 / delta)
    if log_capital(lower_endpoints, 0.0, delta) < threshold:
        return 0.0                      # nothing is rejected; the bound is 0
    lo, hi = 0.0, 1.0
    if log_capital(lower_endpoints, 1.0, delta) >= threshold:
        return 1.0
    while hi - lo > BISECTION_WIDTH:
        mid = 0.5 * (lo + hi)
        if log_capital(lower_endpoints, mid, delta) >= threshold:
            lo = mid
        else:
            hi = mid
    return lo                            # the LOWER endpoint, deliberately


def lower_bound(values: Sequence[float], family_size: int,
                support: tuple[float, float] = PRIMITIVE_SUPPORT,
                alpha: float = ALPHA, horizon: int | None = None) -> Bound:
    """Complete-data one-sided lower bound on the mean contribution."""
    if not values:
        raise ValueError("no superblock contributions")
    delta = memberwise_delta(family_size, alpha)
    normalised = [normalise(v, support) for v in values]
    for x in normalised:
        if not 0.0 <= x <= 1.0 + 1e-12:
            raise ValueError(f"contribution {x} escapes the declared support "
                             f"{support}; the support is exact, not observed")
    root = _normalised_lower_bound(normalised, delta)
    share, transitions = _truncation_diagnostics(normalised, root, delta)
    return Bound(lower=denormalise(root, support), normalised_lower=root,
                 delta=delta, n=len(values), horizon=horizon or len(values),
                 truncation_bound_fraction=share,
                 truncation_transitions=transitions)


def lower_bound_with_missingness(intervals: Sequence[Interval], family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA,
                                 horizon: int | None = None) -> Bound:
    """Interval-completed lower bound, built from normalised lower endpoints."""
    if not intervals:
        raise ValueError("no superblock contributions")
    delta = memberwise_delta(family_size, alpha)
    lowers = [normalise(i.lower, support) for i in intervals]
    root = _normalised_lower_bound(lowers, delta)
    share, transitions = _truncation_diagnostics(lowers, root, delta)
    return Bound(lower=denormalise(root, support), normalised_lower=root,
                 delta=delta, n=len(intervals),
                 horizon=horizon or len(intervals),
                 truncation_bound_fraction=share,
                 truncation_transitions=transitions)


def upper_bound_with_missingness(intervals: Sequence[Interval],
                                 family_size: int,
                                 support: tuple[float, float] = PRIMITIVE_SUPPORT,
                                 alpha: float = ALPHA) -> float:
    """U_X = 1 - L_Z on the reflected variables Z = 1 - X (section 12.10).

    The reflected support interval for Z is [1 - x^+, 1 - x^-], so its
    conservative lower endpoint is 1 - x^+: the upper endpoint of the original.
    """
    delta = memberwise_delta(family_size, alpha)
    reflected = [1.0 - normalise(i.upper, support) for i in intervals]
    lower_z = _normalised_lower_bound(reflected, delta)
    return denormalise(1.0 - lower_z, support)


def two_sided_delta(family_size: int, alpha: float = ALPHA) -> float:
    """delta_tail = alpha / (2M) for a two-sided family (section 12.12)."""
    return memberwise_delta(family_size, alpha) / 2.0
