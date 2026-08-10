"""v19 claim-bearing inference: the fixtures Appendix D.15 makes mandatory.

Both candidate procedures must produce a finite, support-valid bound with no
standard-error failure branch for: all-zero observations, all-one observations,
constant interior observations, mixed point/interval contributions, and
permanent-missingness intervals. The discarded max-T bootstrap needed a
zero-variance workaround; neither of these does, and these tests exist to hold
that line - a "drop the degenerate member" branch reintroduced here would change
the family cardinality and therefore the guarantee.
"""
import math

import pytest

from dci.v19 import ALPHA, PRIMITIVE_SUPPORT, SECONDARY_SUPPORT, SESOI_FLOOR
from dci.v19 import families, mpeb, wsr
from dci.v19.supports import (Interval, linear_contrast, missing, observed,
                              primitive_contribution, replicate_mean,
                              secondary_contribution)

pytestmark = pytest.mark.cpu

FAMILY = families.primary_family_size(3)          # 48 * 3 = 144


# ------------------------------------------------------------ exact supports
def test_the_primary_family_is_48_times_the_retained_budget_count():
    assert families.primary_family_size(3) == 144
    assert families.primary_family_size(5) == 240
    assert families.compute_family_size() == 48
    assert families.load_family_size(3) == families.order_family_size(3) == 72


def test_fewer_than_three_retained_budgets_is_refused():
    with pytest.raises(ValueError, match="compute-treatment gate"):
        families.primary_family_size(2)


def test_a_family_that_lost_a_member_fails_closed():
    families.assert_family_cardinality("primary_primitive_one_sided", 144, 3)
    with pytest.raises(ValueError, match="not protected at the level"):
        families.assert_family_cardinality("primary_primitive_one_sided", 143, 3)


def test_no_joint_guarantee_is_claimable():
    described = families.describe_guarantees(3)
    assert described["joint_alpha_across_families"] is None
    assert "separately" in described["permitted_statement"]


# ------------------------------------------------- interval completion algebra
def test_a_missing_generation_widens_the_replicate_mean():
    assert replicate_mean([1.0, 0.0]) == Interval(0.5, 0.5)
    assert replicate_mean([1.0, None]) == Interval(0.5, 1.0)
    assert replicate_mean([None, None]) == Interval(0.0, 1.0)


def test_a_delivered_malformed_answer_is_observed_not_missing():
    """Refused, empty and truncated answers keep their verdict."""
    assert observed(1.0).observed is True
    assert missing().span == 1.0


def test_the_primitive_contribution_is_the_exact_envelope():
    focal, reference = Interval(0.5, 1.0), Interval(0.0, 0.25)
    got = primitive_contribution(focal, reference)
    assert got == Interval(0.25, 1.0)
    assert PRIMITIVE_SUPPORT[0] <= got.lower <= got.upper <= PRIMITIVE_SUPPORT[1]


def test_the_secondary_contribution_uses_the_declared_endpoints():
    """Section 12.13: [l(5) - u(2), u(5) - l(2)]."""
    high, low = Interval(0.2, 0.6), Interval(-0.1, 0.3)
    got = secondary_contribution(high, low)
    assert got.lower == pytest.approx(-0.1)
    assert got.upper == pytest.approx(0.7)


def test_a_linear_contrast_selects_endpoints_by_sign():
    a, b = Interval(0.0, 1.0), Interval(0.0, 1.0)
    assert linear_contrast([(1.0, a), (-1.0, b)]) == Interval(-1.0, 1.0)
    assert linear_contrast([(1.0, a), (1.0, b)]) == Interval(0.0, 2.0)


def test_intervals_are_clipped_to_the_exact_support():
    wide = linear_contrast([(1.0, Interval(0.0, 1.0))] * 4)
    assert wide.upper == SECONDARY_SUPPORT[1]


def test_brute_force_agreement_on_all_binary_completions():
    """The envelope must equal the true min and max over every completion."""
    import itertools
    focal = [1.0, None, 0.0]
    reference = [0.0, 1.0, None]
    envelope = primitive_contribution(replicate_mean(focal),
                                      replicate_mean(reference))
    seen = []
    for fills in itertools.product([0.0, 1.0], repeat=2):
        f = [fills[0] if v is None else v for v in focal]
        r = [fills[1] if v is None else v for v in reference]
        seen.append(sum(f) / 3 - sum(r) / 3)
    assert envelope.lower == pytest.approx(min(seen))
    assert envelope.upper == pytest.approx(max(seen))


# ----------------------------------------------------------------- MP-EB
def test_pairwise_variance_equals_the_unbiased_sample_variance():
    values = [0.1, -0.4, 0.25, 0.0, 0.9]
    mean = sum(values) / len(values)
    unbiased = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    assert mpeb.pairwise_variance(values) == pytest.approx(unbiased)


@pytest.mark.parametrize("constant", [0.0, 1.0, -1.0, 0.25, -0.6])
def test_zero_variance_is_an_ordinary_case_for_mpeb(constant):
    """All-zero, all-one and constant-interior fixtures (Appendix D.15)."""
    bound = mpeb.lower_bound([constant] * 40, FAMILY)
    assert bound.variance == 0.0
    assert bound.variance_term == 0.0
    assert bound.range_term > 0.0            # the finite-sample term survives
    assert math.isfinite(bound.lower)
    assert PRIMITIVE_SUPPORT[0] <= bound.lower <= constant


def test_mpeb_never_exceeds_the_sample_mean():
    values = [0.3, 0.1, 0.5, 0.2, 0.4] * 8
    bound = mpeb.lower_bound(values, FAMILY)
    assert bound.lower <= bound.mean


def test_mpeb_respects_the_declared_support_floor():
    bound = mpeb.lower_bound([-0.9] * 3, FAMILY)
    assert bound.lower == PRIMITIVE_SUPPORT[0]
    assert bound.clipped_at_support is True


def test_mpeb_needs_two_superblocks():
    with pytest.raises(ValueError, match="H >= 2"):
        mpeb.lower_bound([0.4], FAMILY)


def test_the_range_term_does_not_move_with_replicates():
    """Only H enters it, which is why the simulator must report it separately."""
    few = mpeb.lower_bound([0.3] * 10, FAMILY)
    many = mpeb.lower_bound([0.3] * 40, FAMILY)
    assert many.range_term < few.range_term
    assert mpeb.decompose(few)["range_term_dominates"] is True


def test_a_larger_family_gives_a_smaller_bound():
    values = [0.4, 0.2, 0.5, 0.3] * 10
    assert (mpeb.lower_bound(values, 144).lower
            > mpeb.lower_bound(values, 240).lower)


def test_interval_completion_is_never_more_optimistic_than_complete_data():
    values = [0.4, 0.2, 0.6, 0.3] * 10
    complete = mpeb.lower_bound(values, FAMILY)
    widened = mpeb.lower_bound_with_missingness(
        [observed(v) for v in values[:-1]] + [Interval(-0.2, 0.8)], FAMILY)
    assert widened.lower <= complete.lower


def test_the_variance_envelope_dominates_the_realised_variance():
    intervals = [Interval(0.1, 0.3), Interval(0.4, 0.4), Interval(-0.2, 0.5)]
    envelope = mpeb.pairwise_variance_envelope(intervals)
    for pick in ([0.1, 0.4, -0.2], [0.3, 0.4, 0.5], [0.2, 0.4, 0.1]):
        assert mpeb.pairwise_variance(pick) <= envelope + 1e-12


def test_the_two_sided_allocation_is_wider_than_the_one_sided_one():
    assert mpeb.two_sided_lambda(144) > mpeb.one_sided_lambda(144)


def test_upper_and_lower_bounds_bracket_the_mean():
    values = [0.35, 0.4, 0.3, 0.45] * 12
    low = mpeb.lower_bound(values, FAMILY)
    high = mpeb.upper_bound(values, FAMILY)
    assert low.lower <= low.mean <= high.lower


# ----------------------------------------------------------------- WSR-PP
def test_the_memberwise_delta_matches_the_frozen_primary_rule():
    """delta_prim = 0.05 / (48 |B_ret|) (section 12.6)."""
    assert wsr.memberwise_delta(families.primary_family_size(3)) == 0.05 / 144
    assert wsr.two_sided_delta(144) == 0.05 / 288


def test_the_stake_is_predictable():
    """lam~_t must read the variance available BEFORE observation t."""
    values = [0.2, 0.9, 0.5, 0.1]
    _, sigma2 = wsr.predictable_summaries(values)
    assert sigma2[0] == wsr.INITIAL_VARIANCE
    got = wsr.stakes(values, 0.4, horizon=len(values), delta=0.05 / 144)
    for stake in got:
        expected = math.sqrt(2 * math.log(2 / (0.05 / 144))
                             / (len(values) * sigma2[stake.index - 1]))
        assert stake.base == pytest.approx(expected)


def test_the_first_stake_uses_the_smoothing_prior_only():
    got = wsr.stakes([0.5], 0.3, horizon=1, delta=0.01)
    assert got[0].base == pytest.approx(
        math.sqrt(2 * math.log(2 / 0.01) / (1 * 0.25)))


def test_the_truncation_branch_binds_at_the_documented_example():
    """Section 12.6 works H=200, sigma2=0.0225, delta=0.05/144, m=0.55."""
    delta = 0.05 / 144
    base = math.sqrt(2 * math.log(2 / delta) / (200 * 0.0225))
    assert base == pytest.approx(1.962, abs=1e-3)
    assert wsr.TRUNCATION_C / 0.55 == pytest.approx(0.909, abs=1e-3)
    assert wsr.TRUNCATION_C / 0.55 < base            # truncation determines it


def test_every_capital_factor_stays_nonnegative():
    """lam+ <= c/m < 1/m, so no factor can reach zero for m > 0."""
    values = [0.0, 1.0, 0.5, 0.0, 1.0] * 8
    for m in (1e-9, 0.01, 0.3, 0.5, 0.9, 1.0):
        assert math.isfinite(wsr.log_capital(values, m, 0.05 / 144))


def test_the_capital_is_nonincreasing_in_the_candidate_mean():
    """The property that makes conservative bisection exact."""
    values = [0.6, 0.4, 0.8, 0.5] * 10
    grid = [i / 50 for i in range(51)]
    caps = [wsr.log_capital(values, m, 0.05 / 144) for m in grid]
    assert all(b <= a + 1e-9 for a, b in zip(caps, caps[1:]))


@pytest.mark.parametrize("constant", [0.0, 1.0, 0.5])
def test_zero_variance_is_an_ordinary_case_for_wsr(constant):
    bound = wsr.lower_bound([constant * 2 - 1] * 60, FAMILY)
    assert math.isfinite(bound.lower)
    assert PRIMITIVE_SUPPORT[0] <= bound.lower <= constant * 2 - 1 + 1e-9


def test_all_zero_observations_give_the_support_floor():
    """Every contribution at the support minimum: nothing is rejected."""
    bound = wsr.lower_bound([-1.0] * 40, FAMILY)
    assert bound.lower == pytest.approx(PRIMITIVE_SUPPORT[0])


def test_all_one_observations_give_a_high_bound():
    bound = wsr.lower_bound([1.0] * 60, FAMILY)
    assert bound.lower > 0.5
    assert bound.lower <= 1.0


def test_wsr_never_exceeds_the_mean():
    values = [0.4, 0.2, 0.5, 0.3] * 20
    mean = sum(values) / len(values)
    assert wsr.lower_bound(values, FAMILY).lower <= mean + 1e-9


def test_the_bisection_returns_the_lower_endpoint():
    """Floating-point error must not be able to inflate the bound."""
    values = [0.5] * 80
    bound = wsr.lower_bound(values, FAMILY)
    delta = wsr.memberwise_delta(FAMILY)
    normalised = [(v + 1) / 2 for v in values]
    threshold = math.log(1 / delta)
    assert wsr.log_capital(normalised, bound.normalised_lower, delta) >= threshold
    just_above = min(1.0, bound.normalised_lower + 1e-9)
    assert (wsr.log_capital(normalised, just_above, delta) < threshold
            or just_above == 1.0)


def test_wsr_interval_completion_is_never_more_optimistic():
    values = [0.4, 0.3, 0.5, 0.35] * 15
    complete = wsr.lower_bound(values, FAMILY)
    widened = wsr.lower_bound_with_missingness(
        [observed(v) for v in values[:-2]] + [Interval(-1.0, 1.0)] * 2, FAMILY)
    assert widened.lower <= complete.lower


def test_all_interval_observations_still_produce_a_valid_bound():
    bound = wsr.lower_bound_with_missingness([Interval(-1.0, 1.0)] * 30, FAMILY)
    assert bound.lower == pytest.approx(PRIMITIVE_SUPPORT[0])


def test_mixed_point_and_interval_contributions():
    mixed = ([observed(0.6)] * 20 + [Interval(0.2, 0.9)] * 5
             + [observed(0.5)] * 15)
    for method in (mpeb.lower_bound_with_missingness,
                   wsr.lower_bound_with_missingness):
        got = method(mixed, FAMILY)
        low = got.lower if hasattr(got, "lower") else got
        assert math.isfinite(low) and low <= 0.6


def test_the_reflected_upper_bound_brackets_the_lower_one():
    intervals = [observed(0.3)] * 40
    low = wsr.lower_bound_with_missingness(intervals, FAMILY).lower
    high = wsr.upper_bound_with_missingness(intervals, FAMILY)
    assert low <= 0.3 <= high


def test_the_truncation_diagnostic_is_reported():
    """Section 13.4 requires the truncation-bound frequency and transitions."""
    bound = wsr.lower_bound([0.9] * 50, FAMILY)
    assert 0.0 <= bound.truncation_bound_fraction <= 1.0
    assert bound.truncation_transitions >= 0


def test_a_contribution_outside_the_declared_support_is_refused():
    with pytest.raises(ValueError, match="escapes the declared support"):
        wsr.lower_bound([1.5, 0.2, 0.3], FAMILY)


# --------------------------------------------------------------- the headline
def _cell(pair, budget, load, order):
    return families.Cell(pair=pair, budget=budget, load=load, order=order)


def test_the_least_favourable_reference_decides_the_cell():
    bounds = {"R1": 0.08, "R2": 0.01, "R3": 0.13, "R4": -0.02}
    assert families.cell_lower_bound(bounds) == -0.02


def test_a_cell_missing_a_reference_is_refused():
    with pytest.raises(ValueError, match="exactly 4"):
        families.cell_lower_bound({"R1": 0.1, "R2": 0.2, "R3": 0.3})


def test_the_worked_example_from_the_preregistration():
    """Estimates (0.18,0.12,0.25,0.07), bounds (0.08,0.01,0.13,-0.02).

    Point-estimate robustness is 0.07; the robust lower bound is -0.02, so the
    cell does NOT support reference-robust positive DCI.
    """
    cell = _cell("p1", "b1", 2, "o_A")
    bounds = {"R1": 0.08, "R2": 0.01, "R3": 0.13, "R4": -0.02}
    estimates = {"R1": 0.18, "R2": 0.12, "R3": 0.25, "R4": 0.07}
    head = families.global_headline({cell: bounds}, {cell: estimates})
    assert head.plug_in == pytest.approx(0.07)
    assert head.l_theta == pytest.approx(-0.02)
    assert families.headline_label(head.l_theta, SESOI_FLOOR) == "NOT_ESTABLISHED"


def test_the_outer_maximum_searches_the_frozen_set():
    a, b = _cell("p1", "b1", 2, "o_A"), _cell("p2", "b1", 5, "o_Q")
    cells = {a: {"R1": 0.05, "R2": 0.06, "R3": 0.07, "R4": 0.08},
             b: {"R1": 0.20, "R2": 0.01, "R3": 0.30, "R4": 0.40}}
    head = families.global_headline(cells)
    assert head.l_theta == pytest.approx(0.05)     # a's minimum beats b's 0.01


def test_ties_resolve_by_the_frozen_lexicographic_order():
    a, b = _cell("p2", "b1", 2, "o_A"), _cell("p1", "b1", 2, "o_A")
    same = {"R1": 0.1, "R2": 0.1, "R3": 0.1, "R4": 0.1}
    head = families.global_headline({a: same, b: same}, {a: same, b: same})
    assert head.selected_cell == b.key            # p1 before p2, not insertion order


@pytest.mark.parametrize("l_theta,expected", [
    (0.10, "ROBUST_POSITIVE_SESOI"),
    (0.03, "ROBUST_POSITIVE"),
    (0.0, "NOT_ESTABLISHED"),
    (-0.5, "NOT_ESTABLISHED"),
])
def test_the_headline_labels_are_mutually_exclusive(l_theta, expected):
    assert families.headline_label(l_theta, SESOI_FLOOR) == expected


def test_a_feasibility_pilot_cannot_be_promoted_by_a_large_estimate():
    assert families.headline_label(0.5, SESOI_FLOOR, feasibility_pilot=True) == \
        "FEASIBILITY_MEASUREMENT_PILOT"


def test_the_selection_warning_travels_with_the_plug_in():
    cell = _cell("p1", "b1", 2, "o_A")
    same = {"R1": 0.1, "R2": 0.1, "R3": 0.1, "R4": 0.1}
    head = families.global_headline({cell: same}, {cell: same})
    assert "overstate" in head.warning


def test_the_transformation_preserves_coverage_by_monotonicity():
    """If every L_r <= tau_r then L_Theta <= Theta_crit, mechanically."""
    cells = {}
    truths = {}
    for i, (pair, load) in enumerate([("p1", 2), ("p2", 5), ("p3", 2)]):
        cell = _cell(pair, "b1", load, "o_A")
        tau = {f"R{j}": 0.1 + 0.01 * (i + j) for j in range(1, 5)}
        cells[cell] = {k: v - 0.05 for k, v in tau.items()}     # covering bounds
        truths[cell] = tau
    head = families.global_headline(cells, truths)
    theta_crit = max(min(t.values()) for t in truths.values())
    assert head.l_theta <= theta_crit
