"""MP-EB two-sided tail allocation and exact-support enforcement.

Both defects reproduced here were found in review of the first v19 inference
increment, and both let a finite, plausible-looking claim-bearing number out of a
procedure whose stated guarantee did not hold.

  * A "two-sided interval" assembled from `lower_bound` and `upper_bound` mixed
    lambda = log(2M/alpha) with lambda_2 = log(4M/alpha), so the pair controlled
    neither the one-sided nor the two-sided level (section 12.12).
  * MP-EB computed the mean and pairwise variance without first proving that
    every contribution obeyed the declared support. Forty copies of 5.0 under
    support [-1, 1] returned a "lower bound" of 4.095 - the empirical-Bernstein
    theorem simply does not apply to unbounded input (section 12.3).

The assertions are written against the *allocation* and the *support*, not against
golden numbers, so they keep holding if a later change alters interval widths for
a legitimate reason.
"""
import math

import pytest

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT, SECONDARY_SUPPORT
from dci.v19 import mpeb
from dci.v19.supports import Interval

pytestmark = pytest.mark.cpu

FAMILIES = (1, 3, 48, 144, 480)


def _mixed(n):
    """Heterogeneous interior values, so the variance term is genuinely active."""
    return [(-1.0 + 2.0 * (i % 7) / 6.0) * 0.5 for i in range(n)]


# ---------------------------------------------------------------- MP-EB tails
@pytest.mark.parametrize("family", FAMILIES)
def test_mpeb_two_sided_lambda_is_log_four_m_over_alpha(family):
    assert mpeb.two_sided_lambda(family) == pytest.approx(
        math.log(4.0 * family / ALPHA))
    assert mpeb.one_sided_lambda(family) == pytest.approx(
        math.log(2.0 * family / ALPHA))
    # The two-sided allocation is strictly the more expensive one.
    assert mpeb.two_sided_lambda(family) > mpeb.one_sided_lambda(family)


@pytest.mark.parametrize("family", FAMILIES)
def test_mpeb_two_sided_interval_uses_one_allocation_for_both_tails(family):
    """The defect: lower used log(2M/a) while upper used log(4M/a)."""
    values = _mixed(20)
    interval = mpeb.two_sided_interval(values, family)
    expected = mpeb.two_sided_lambda(family)
    assert interval.lower_bound.lambda_ == pytest.approx(expected)
    assert interval.upper_bound.lambda_ == pytest.approx(expected)
    assert interval.lambda_ == pytest.approx(expected)
    assert interval.lower <= interval.upper


@pytest.mark.parametrize("family", FAMILIES)
def test_mpeb_two_sided_lower_is_below_the_one_sided_lower(family):
    """Paying for both tails must cost precision, never gain it."""
    values = _mixed(20)
    one_sided = mpeb.lower_bound(values, family)
    two_sided = mpeb.two_sided_interval(values, family)
    assert two_sided.lower <= one_sided.lower


def test_mpeb_refuses_to_label_a_mixed_allocation_two_sided():
    values = _mixed(12)
    one_sided = mpeb.lower_bound(values, 48)
    proper = mpeb.two_sided_interval(values, 48)
    assert one_sided.allocation == "one_sided"
    assert proper.lower_bound.allocation == "two_sided"
    with pytest.raises(ValueError, match="two_sided"):
        mpeb.TwoSidedInterval(lower_bound=one_sided,
                              upper_bound=proper.upper_bound,
                              family_size=48, alpha=ALPHA)


@pytest.mark.parametrize("support", [PRIMITIVE_SUPPORT, SECONDARY_SUPPORT])
def test_mpeb_two_sided_interval_on_both_declared_supports(support):
    scale = (support[1] - support[0]) / 2.0
    values = [v * scale for v in _mixed(15)]
    got = mpeb.two_sided_interval(values, 48, support=support)
    assert got.lower_bound.width == pytest.approx(support[1] - support[0])
    assert support[0] <= got.lower <= got.upper <= support[1]


def test_mpeb_two_sided_interval_reflection_symmetry():
    """Negating every contribution must mirror the interval about zero."""
    values = _mixed(16)
    a = mpeb.two_sided_interval(values, 48)
    b = mpeb.two_sided_interval([-v for v in values], 48)
    assert a.lower == pytest.approx(-b.upper)
    assert a.upper == pytest.approx(-b.lower)


def test_mpeb_two_sided_interval_accepts_interval_completed_input():
    intervals = [Interval(0.1, 0.1), Interval(0.0, 1.0), Interval(-0.2, -0.2),
                 Interval(-1.0, 1.0), Interval(0.3, 0.3)]
    got = mpeb.two_sided_interval_with_missingness(intervals, 48)
    assert got.lambda_ == pytest.approx(mpeb.two_sided_lambda(48))
    assert got.lower_bound.allocation == got.upper_bound.allocation == "two_sided"
    complete = mpeb.two_sided_interval([i.midpoint for i in intervals], 48)
    # Interval completion is conservative on both sides.
    assert got.lower <= complete.lower and got.upper >= complete.upper


# ----------------------------------------------------- MP-EB support validation
@pytest.mark.parametrize("bad", [5.0, -5.0, 1.0 + 1e-6, -1.0 - 1e-6,
                                 float("nan"), float("inf"), float("-inf")])
def test_mpeb_refuses_values_outside_the_primitive_support(bad):
    """The defect: many copies of 5.0 produced a lower bound above 1."""
    values = [0.0] * 9 + [bad]
    with pytest.raises(ValueError, match="support"):
        mpeb.lower_bound(values, 48)
    with pytest.raises(ValueError, match="support"):
        mpeb.two_sided_interval(values, 48)


@pytest.mark.parametrize("edge", [-1.0, 1.0, -1.0 + 1e-15, 1.0 - 1e-15])
def test_mpeb_accepts_the_exact_support_endpoints(edge):
    got = mpeb.lower_bound([edge] * 10, 48)
    assert math.isfinite(got.lower)
    assert PRIMITIVE_SUPPORT[0] <= got.lower <= PRIMITIVE_SUPPORT[1]


@pytest.mark.parametrize("bad", [3.0, -3.0, float("nan")])
def test_mpeb_refuses_values_outside_the_secondary_support(bad):
    with pytest.raises(ValueError, match="support"):
        mpeb.lower_bound([0.0] * 9 + [bad], 48, support=SECONDARY_SUPPORT)


def test_mpeb_accepts_the_secondary_support_endpoints():
    got = mpeb.lower_bound([-2.0, 2.0, 0.0, 1.5], 48, support=SECONDARY_SUPPORT)
    assert SECONDARY_SUPPORT[0] <= got.lower <= SECONDARY_SUPPORT[1]


def test_a_malformed_interval_cannot_be_built_at_all():
    with pytest.raises(ValueError):
        Interval(0.5, 0.4)
    with pytest.raises(ValueError):
        Interval(float("nan"), 1.0)
    with pytest.raises(ValueError):
        Interval(0.0, float("inf"))


@pytest.mark.parametrize("interval", [Interval(-1.5, 0.0), Interval(0.0, 1.5),
                                      Interval(-2.0, 2.0)])
def test_mpeb_refuses_intervals_that_leave_the_declared_support(interval):
    others = [Interval(0.0, 0.0)] * 4
    with pytest.raises(ValueError, match="support"):
        mpeb.lower_bound_with_missingness([interval] + others, 48)


def test_no_out_of_support_input_can_produce_a_finite_claim():
    """The property the review asked for, stated directly."""
    for bad in (5.0, -5.0, 2.0, float("inf")):
        for fn in (mpeb.lower_bound, mpeb.upper_bound):
            with pytest.raises(ValueError):
                fn([bad] * 10, 48)
