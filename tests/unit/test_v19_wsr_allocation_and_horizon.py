"""WSR-PP two-sided tail allocation and planned-horizon fidelity.

Two defects from review of the first v19 inference increment:

  * `upper_bound_with_missingness` used the one-sided delta = alpha/M, so pairing
    it with the ordinary lower bound spent up to 2 alpha on a family advertised at
    alpha. Section 12.12 allocates alpha/(2M) to each tail; the `two_sided_delta`
    helper defined that correctly and was never called.
  * The returned `Bound` recorded a caller-supplied `horizon` while root finding
    and `log_capital` rebuilt every stake at `len(values)`. Since lam~_t scales as
    1/sqrt(H), a prefix evaluated against a frozen planned horizon calculated a
    materially more aggressive betting process than the one it reported.

The assertions target the allocation and the stake sequence rather than golden
bound values, so they survive legitimate changes to interval width.
"""
import math

import pytest

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT, SECONDARY_SUPPORT
from dci.v19 import wsr
from dci.v19.supports import Interval

pytestmark = pytest.mark.cpu

FAMILIES = (1, 3, 48, 144, 480)


def _mixed(n):
    """Heterogeneous interior values, so the variance term is genuinely active."""
    return [(-1.0 + 2.0 * (i % 7) / 6.0) * 0.5 for i in range(n)]


# ------------------------------------------------------------------- WSR tails
@pytest.mark.parametrize("family", FAMILIES)
def test_wsr_two_sided_tail_is_alpha_over_two_m(family):
    assert wsr.two_sided_delta(family) == pytest.approx(ALPHA / (2.0 * family))
    assert wsr.memberwise_delta(family) == pytest.approx(ALPHA / family)


@pytest.mark.parametrize("family", FAMILIES)
def test_wsr_two_sided_interval_spends_alpha_not_two_alpha(family):
    """The defect: both tails used alpha/M, so the interval cost 2 alpha."""
    values = _mixed(24)
    got = wsr.two_sided_interval(values, family)
    tail = ALPHA / (2.0 * family)
    assert got.lower_bound.delta == pytest.approx(tail)
    assert got.upper_bound.delta == pytest.approx(tail)
    assert got.total_allocation == pytest.approx(ALPHA / family)
    # The whole family, both tails, is exactly alpha.
    assert got.total_allocation * family == pytest.approx(ALPHA)


@pytest.mark.parametrize("family", FAMILIES)
def test_wsr_two_sided_lower_is_below_the_one_sided_lower(family):
    values = _mixed(24)
    assert (wsr.two_sided_interval(values, family).lower
            <= wsr.lower_bound(values, family).lower)


def test_wsr_refuses_to_label_a_mixed_allocation_two_sided():
    values = _mixed(12)
    one_sided = wsr.lower_bound(values, 48)
    proper = wsr.two_sided_interval(values, 48)
    assert one_sided.allocation == "one_sided"
    with pytest.raises(ValueError, match="two_sided"):
        wsr.TwoSidedInterval(lower_bound=one_sided,
                             upper_bound=proper.upper_bound,
                             family_size=48, alpha=ALPHA)


def test_wsr_two_sided_interval_on_point_and_interval_inputs():
    values = [0.2, -0.4, 0.6, 0.0, 0.1, -0.1]
    intervals = [Interval(v, v) for v in values]
    a = wsr.two_sided_interval(values, 48)
    b = wsr.two_sided_interval_with_missingness(intervals, 48)
    assert a.lower == pytest.approx(b.lower)
    assert a.upper == pytest.approx(b.upper)


def test_wsr_two_sided_interval_widens_under_missingness():
    values = [0.2, 0.2, 0.2, 0.2, 0.2, 0.2]
    observed = [Interval(v, v) for v in values]
    with_gap = list(observed)
    with_gap[2] = Interval(-1.0, 1.0)
    tight = wsr.two_sided_interval_with_missingness(observed, 48)
    loose = wsr.two_sided_interval_with_missingness(with_gap, 48)
    assert loose.lower <= tight.lower
    assert loose.upper >= tight.upper


@pytest.mark.parametrize("support", [PRIMITIVE_SUPPORT, SECONDARY_SUPPORT])
def test_wsr_two_sided_interval_respects_each_declared_support(support):
    scale = (support[1] - support[0]) / 2.0
    values = [v * scale for v in _mixed(18)]
    got = wsr.two_sided_interval(values, 48, support=support)
    assert support[0] <= got.lower <= got.upper <= support[1]


@pytest.mark.parametrize("bad", [5.0, -5.0, float("nan"), float("inf")])
def test_wsr_refuses_values_outside_the_declared_support(bad):
    with pytest.raises(ValueError, match="support"):
        wsr.lower_bound([0.0] * 9 + [bad], 48)
    with pytest.raises(ValueError, match="support"):
        wsr.two_sided_interval([0.0] * 9 + [bad], 48)


def test_wsr_missingness_path_also_validates_the_support():
    with pytest.raises(ValueError, match="support"):
        wsr.lower_bound_with_missingness(
            [Interval(-1.5, 0.0), Interval(0.0, 0.0)], 48)


# ---------------------------------------------------------------- WSR horizon
def test_wsr_stakes_follow_the_supplied_horizon_not_the_sample_length():
    """The defect: log_capital rebuilt stakes at horizon=len(values)."""
    values = [0.3, 0.5, 0.4, 0.6]
    delta = wsr.memberwise_delta(48)
    short = wsr.stakes(values, 0.4, len(values), delta)
    planned = wsr.stakes(values, 0.4, 200, delta)
    assert [s.base for s in short] != [s.base for s in planned]
    # lam~_t scales as 1/sqrt(H): a longer planned horizon bets smaller.
    for a, b in zip(short, planned):
        assert b.base < a.base
        assert b.base == pytest.approx(a.base * math.sqrt(len(values) / 200))


def test_wsr_log_capital_uses_the_supplied_horizon():
    values = [0.3, 0.5, 0.4, 0.6]
    delta = wsr.memberwise_delta(48)
    assert (wsr.log_capital(values, 0.4, delta, horizon=len(values))
            != wsr.log_capital(values, 0.4, delta, horizon=200))


def test_wsr_a_prefix_bound_bets_at_the_planned_horizon():
    """A prefix of a frozen H=60 design must not bet as if H were 6."""
    values = [0.25] * 6
    naive = wsr.lower_bound(values, 48)
    prefix = wsr.lower_bound(values, 48, horizon=60)
    assert prefix.horizon == 60 and naive.horizon == 6
    assert prefix.lower != naive.lower
    # Betting smaller at a longer planned horizon rejects less, so the reported
    # lower bound cannot be the more optimistic of the two by accident.
    assert prefix.lower <= naive.lower


def test_wsr_diagnostics_describe_the_process_that_produced_the_bound():
    values = [0.9] * 30
    got = wsr.lower_bound(values, 48, horizon=400)
    recomputed = wsr.stakes([wsr_normalise(v) for v in values],
                            got.normalised_lower, got.horizon, got.delta)
    share = sum(s.truncation_bound for s in recomputed) / len(recomputed)
    assert got.truncation_bound_fraction == pytest.approx(share)


def wsr_normalise(value):
    from dci.v19.supports import normalise
    return normalise(value, PRIMITIVE_SUPPORT)


@pytest.mark.parametrize("bad", [0, -1, 2.5, None, True, "60"])
def test_wsr_refuses_a_malformed_horizon(bad):
    with pytest.raises((ValueError, TypeError)):
        wsr.lower_bound([0.2, 0.3, 0.4], 48, horizon=bad)


def test_wsr_refuses_a_horizon_shorter_than_the_observed_sequence():
    """More observations than the planned horizon is a manifest defect."""
    with pytest.raises(ValueError, match="horizon"):
        wsr.lower_bound([0.2] * 10, 48, horizon=5)


def test_wsr_reflected_and_missingness_paths_share_the_horizon():
    intervals = [Interval(0.2, 0.2)] * 8
    lower = wsr.lower_bound_with_missingness(intervals, 48, horizon=100)
    upper = wsr.upper_bound_with_missingness(intervals, 48, horizon=100)
    assert lower.horizon == upper.horizon == 100
    both = wsr.two_sided_interval_with_missingness(intervals, 48, horizon=100)
    assert both.lower_bound.horizon == both.upper_bound.horizon == 100
