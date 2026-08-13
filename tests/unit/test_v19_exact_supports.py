"""Exact-support enforcement, independent of either inference candidate.

Section 12.3 declares the supports as scientific inputs: a primitive contribution
lives in [-1, 1] and a secondary difference in [-2, 2], "even when all realised
observations occupy a narrower range". Both claim-bearing procedures depend on
that: MP-EB's range term is 7 w lambda / (3(H-1)) and its theorem holds only for
variables genuinely confined to [a, b]; WSR-PP normalises onto [0, 1] and needs
every capital factor nonnegative.

So a contribution outside the declared support does not make an answer slightly
wrong - it makes the stated theorem inapplicable. These validators are the single
place that decides what counts as inside, and they are exercised here directly so
the rule is pinned independently of how the candidates call it.
"""
import math

import pytest

from dci.v19 import PRIMITIVE_SUPPORT, SECONDARY_SUPPORT
from dci.v19.supports import (SUPPORT_TOLERANCE, Interval,
                              assert_interval_in_support,
                              assert_intervals_in_support, assert_support,
                              assert_value_in_support, assert_values_in_support,
                              missing, observed, replicate_mean)

pytestmark = pytest.mark.cpu


# ------------------------------------------------------------- the support itself
@pytest.mark.parametrize("support", [PRIMITIVE_SUPPORT, SECONDARY_SUPPORT,
                                     (0.0, 1.0), (-3.5, 2.25)])
def test_a_well_formed_support_is_accepted(support):
    assert assert_support(support) == (float(support[0]), float(support[1]))


@pytest.mark.parametrize("support", [(1.0, -1.0), (0.0, 0.0),
                                     (float("nan"), 1.0), (0.0, float("inf")),
                                     (float("-inf"), 0.0)])
def test_a_malformed_support_is_refused(support):
    with pytest.raises(ValueError, match="support"):
        assert_support(support)


# ------------------------------------------------------------------ point values
@pytest.mark.parametrize("value", [-1.0, 1.0, 0.0, -0.999999, 0.5,
                                   -1.0 + 1e-15, 1.0 - 1e-15])
def test_values_inside_the_primitive_support_pass_through(value):
    assert assert_value_in_support(value, PRIMITIVE_SUPPORT) == pytest.approx(value)


@pytest.mark.parametrize("value", [1.0 + 1e-6, -1.0 - 1e-6, 2.0, 5.0, -5.0,
                                   1e300])
def test_values_outside_the_primitive_support_are_refused(value):
    with pytest.raises(ValueError, match="escapes the declared support"):
        assert_value_in_support(value, PRIMITIVE_SUPPORT)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_unrepresentable_values_are_refused_under_every_support(value):
    for support in (PRIMITIVE_SUPPORT, SECONDARY_SUPPORT, (0.0, 1.0)):
        with pytest.raises(ValueError, match="support"):
            assert_value_in_support(value, support)


def test_representation_slack_is_snapped_not_rejected():
    """A 1e-13 overshoot is float arithmetic; a 1e-6 overshoot is data."""
    inside = 1.0 + SUPPORT_TOLERANCE / 2.0
    assert assert_value_in_support(inside, PRIMITIVE_SUPPORT) == 1.0
    with pytest.raises(ValueError):
        assert_value_in_support(1.0 + SUPPORT_TOLERANCE * 1000, PRIMITIVE_SUPPORT)


def test_the_error_names_the_offending_position():
    with pytest.raises(ValueError, match="position 3"):
        assert_values_in_support([0.0, 0.1, 0.2, 9.0], PRIMITIVE_SUPPORT)


@pytest.mark.parametrize("value", [None, "0.5", object()])
def test_a_non_numeric_contribution_is_refused(value):
    with pytest.raises((ValueError, TypeError)):
        assert_value_in_support(value, PRIMITIVE_SUPPORT)


def test_the_secondary_support_is_four_wide_and_enforced_as_such():
    assert SECONDARY_SUPPORT == (-2.0, 2.0)
    for edge in (-2.0, 2.0, 1.75):
        assert assert_value_in_support(edge, SECONDARY_SUPPORT) == edge
    for outside in (-2.5, 2.5):
        with pytest.raises(ValueError, match="support"):
            assert_value_in_support(outside, SECONDARY_SUPPORT)
    # A value legal for a secondary contrast is illegal for a primitive.
    assert assert_value_in_support(1.5, SECONDARY_SUPPORT) == 1.5
    with pytest.raises(ValueError, match="support"):
        assert_value_in_support(1.5, PRIMITIVE_SUPPORT)


# --------------------------------------------------------------------- intervals
def test_an_interval_inside_the_support_passes_through():
    got = assert_interval_in_support(Interval(-0.5, 0.5), PRIMITIVE_SUPPORT)
    assert (got.lower, got.upper) == (-0.5, 0.5)


@pytest.mark.parametrize("interval", [Interval(-1.5, 0.0), Interval(0.0, 1.5),
                                      Interval(-2.0, 2.0)])
def test_an_interval_leaving_the_support_is_refused(interval):
    """A wider-than-support interval claims a possibility the design excludes."""
    with pytest.raises(ValueError, match="support"):
        assert_interval_in_support(interval, PRIMITIVE_SUPPORT)


def test_the_full_missing_primitive_interval_is_exactly_the_support():
    """A missing binary generation contributes [0, 1]; a fully missing contrast
    contributes the whole primitive support and must remain admissible."""
    whole = Interval(-1.0, 1.0)
    assert assert_interval_in_support(whole, PRIMITIVE_SUPPORT) == whole


def test_a_sequence_of_intervals_is_validated_positionally():
    good = [Interval(0.0, 0.0), Interval(-1.0, 1.0)]
    assert assert_intervals_in_support(good, PRIMITIVE_SUPPORT) == good
    with pytest.raises(ValueError, match="position 1"):
        assert_intervals_in_support([Interval(0.0, 0.0), Interval(0.0, 3.0)],
                                    PRIMITIVE_SUPPORT)


@pytest.mark.parametrize("value", [0.5, (0.0, 1.0), [0.0, 1.0], None])
def test_a_non_interval_is_refused_where_an_interval_is_required(value):
    with pytest.raises(ValueError, match="Interval"):
        assert_interval_in_support(value, PRIMITIVE_SUPPORT)


# ---------------------------------------------------- Interval well-formedness
def test_an_inverted_interval_cannot_be_constructed():
    with pytest.raises(ValueError, match="0.5 > 0.4"):
        Interval(0.5, 0.4)


@pytest.mark.parametrize("pair", [(float("nan"), 1.0), (0.0, float("nan")),
                                  (float("nan"), float("nan")),
                                  (0.0, float("inf")), (float("-inf"), 0.0)])
def test_a_non_finite_interval_cannot_be_constructed(pair):
    """NaN and infinity are malformed measurements, not unusually wide ones."""
    with pytest.raises(ValueError, match="finite|>"):
        Interval(*pair)


def test_a_degenerate_interval_is_an_observed_point():
    assert observed(1.0) == Interval(1.0, 1.0)
    assert observed(1.0).observed and observed(1.0).span == 0.0
    assert missing() == Interval(0.0, 1.0)
    assert not missing().observed


# --------------------------------- propagation stays inside the declared support
@pytest.mark.parametrize("n_missing", range(0, 5))
def test_replicate_means_stay_within_the_binary_support(n_missing):
    generations = [1.0, 0.0, 1.0, 0.0][:4 - n_missing] + [None] * n_missing
    got = replicate_mean(generations)
    assert 0.0 <= got.lower <= got.upper <= 1.0
    assert assert_interval_in_support(got, (0.0, 1.0)) == got
    assert got.span == pytest.approx(n_missing / 4.0)


def test_a_fully_missing_cell_spans_the_whole_binary_support():
    got = replicate_mean([None] * 6)
    assert (got.lower, got.upper) == (0.0, 1.0)


def test_every_primitive_contribution_from_binary_arms_is_in_support():
    """Brute force over all binary replicate patterns for G = 3."""
    from itertools import product
    for focal in product([0.0, 1.0, None], repeat=3):
        for reference in product([0.0, 1.0, None], repeat=3):
            got = replicate_mean(list(focal)) - replicate_mean(list(reference))
            assert PRIMITIVE_SUPPORT[0] - 1e-12 <= got.lower
            assert got.upper <= PRIMITIVE_SUPPORT[1] + 1e-12
            assert math.isfinite(got.lower) and math.isfinite(got.upper)
