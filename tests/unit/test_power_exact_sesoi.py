"""`power_at_sesoi` must be power at the SESOI, not at whatever the grid holds.

Power rises with the true effect, so reporting the nearest simulated point is
biased in a direction that depends on which side the neighbour falls: a grid of
{0.05, 0.10} with a SESOI of 0.06 reported power at 0.05 and understated it,
while a SESOI of 0.09 would have reported 0.10 and OVERSTATED it - the direction
that lets an underpowered design look acceptable.
"""
import numpy as np
import pytest

from dci.analysis.power import (REQUIRED_SESOI_MULTIPLES, plan_primary_power,
                                power_at_exact_effect, primary_family_covariance,
                                scenario_effects, simulate_claim_power)

pytestmark = pytest.mark.cpu

COARSE = [0.0, 0.05, 0.10, 0.15]
SESOI = 0.06                      # deliberately between two coarse grid points


def test_the_exact_sesoi_is_inserted_into_a_coarse_grid():
    grid = scenario_effects(COARSE, SESOI)
    assert SESOI in grid
    assert grid == sorted(grid)
    assert set(COARSE) <= set(grid)


def test_every_required_multiple_of_the_sesoi_is_present():
    grid = scenario_effects([0.05], SESOI)
    for multiple in REQUIRED_SESOI_MULTIPLES:
        assert multiple * SESOI in grid, multiple


def test_an_already_present_effect_is_not_duplicated():
    grid = scenario_effects([0.0, 0.06, 0.12], 0.06)
    assert grid == [0.0, 0.06, 0.12]


def test_planner_reports_power_at_the_sesoi_itself():
    """The reported number must be the row simulated AT 0.06."""
    plan = plan_primary_power(n_clusters=40, n_refs=6, n_orders=2, effects=COARSE,
                              reps=400, alpha=0.05, power=0.80, sesoi=SESOI,
                              scenarios=({"label": "s", "sd_task": 0.20,
                                          "rho_same_order": 0.30,
                                          "rho_cross_order_same_constraint": 0.50,
                                          "rho_cross_order_diff_constraint": 0.20},))
    row = plan.iloc[0]
    cov = primary_family_covariance(6, 2, 40, 0.20, 0.30, 0.50, 0.20)
    sim = simulate_claim_power(cov, 6, 2, scenario_effects(COARSE, SESOI), 400,
                              0.05, seed=20260809)
    at_sesoi = sim[sim["true_tau"] == SESOI].iloc[0]
    at_neighbour = sim[sim["true_tau"] == 0.05].iloc[0]

    assert row["power_at_sesoi_per_order"] == pytest.approx(
        float(at_sesoi["simultaneous_power_per_order"]))
    # And it is genuinely a different number from the neighbour it used to report.
    assert (float(at_sesoi["simultaneous_power_per_order"])
            != float(at_neighbour["simultaneous_power_per_order"]))


def test_the_null_and_twice_sesoi_points_are_also_exact():
    plan = plan_primary_power(n_clusters=40, n_refs=6, n_orders=2, effects=[0.05],
                              reps=200, alpha=0.05, power=0.80, sesoi=SESOI,
                              scenarios=({"label": "s", "sd_task": 0.20,
                                          "rho_same_order": 0.30,
                                          "rho_cross_order_same_constraint": 0.50,
                                          "rho_cross_order_diff_constraint": 0.20},))
    row = plan.iloc[0]
    assert 0.0 <= row["false_positive_at_zero"] <= 0.10
    assert row["power_at_two_sesoi_per_order"] >= row["power_at_sesoi_per_order"]


def test_a_grid_without_the_effect_refuses_rather_than_approximating():
    cov = primary_family_covariance(6, 2, 40, 0.20, 0.30, 0.50, 0.20)
    sim = simulate_claim_power(cov, 6, 2, [0.0, 0.05, 0.10], 100, 0.05)
    with pytest.raises(ValueError, match="does not contain exactly one row"):
        power_at_exact_effect(sim, 0.06, "marginal_power")


def test_exact_lookup_is_not_a_tolerance_search():
    cov = primary_family_covariance(6, 2, 40, 0.20, 0.30, 0.50, 0.20)
    sim = simulate_claim_power(cov, 6, 2, [0.0, 0.06], 100, 0.05)
    assert power_at_exact_effect(sim, 0.06, "marginal_power") >= 0.0
    with pytest.raises(ValueError):
        power_at_exact_effect(sim, 0.06 + 1e-9, "marginal_power")


def test_nearest_neighbour_would_have_reported_a_different_row():
    """Pins the defect: argmin over |effects - sesoi| lands on 0.05, not 0.06."""
    nearest = int(np.argmin(np.abs(np.array(COARSE) - SESOI)))
    assert COARSE[nearest] == 0.05 != SESOI
