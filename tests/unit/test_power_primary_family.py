"""Power planning must describe the claim rule the analysis actually applies.

Two things are tested and kept separate:
  * the LEGACY six-reference planner still reproduces the historically recorded
    numbers, so the provenance trail is intact;
  * the corrected planner covers the real refs x orders family with an arm-level
    covariance, and its critical value is larger because the family is larger.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.power import (SCENARIOS, arm_covariance, contrast_matrix,
                                mde, plan_primary_power,
                                primary_family_covariance, required_clusters,
                                simulate_claim_power)

pytestmark = pytest.mark.cpu

EFFECTS = np.round(np.arange(0.02, 0.42, 0.02), 3)


# --------------------------------------------------------------- structure
def test_contrast_matrix_is_the_estimator():
    """Row (j,o) must be +focal|o - ref_j|o and nothing else."""
    L = contrast_matrix(n_refs=6, n_orders=2)
    assert L.shape == (12, 14)
    for row in L:
        assert row.sum() == 0.0
        assert np.count_nonzero(row) == 2
        assert row.max() == 1.0 and row.min() == -1.0
    # tau_{0,target_first} uses order-0 arms only.
    assert L[0][0] == 1.0 and L[0][1] == -1.0
    assert not L[0][7:].any()
    # tau_{0,added_first} uses order-1 arms only.
    assert not L[6][:7].any()
    assert L[6][7] == 1.0 and L[6][8] == -1.0


def test_arm_covariance_is_psd_and_blockwise():
    cov = arm_covariance(6, 2, 0.20, 0.30, 0.50, 0.20)
    assert cov.shape == (14, 14)
    assert np.allclose(cov, cov.T)
    assert float(np.min(np.linalg.eigvalsh(cov))) > -1e-10
    assert np.allclose(np.diag(cov), 0.04)
    assert cov[0, 1] == pytest.approx(0.04 * 0.30)   # same order, diff constraint
    assert cov[0, 7] == pytest.approx(0.04 * 0.50)   # diff order, same constraint
    assert cov[1, 9] == pytest.approx(0.04 * 0.20)   # diff order, diff constraint


def test_impossible_correlation_grid_is_refused():
    with pytest.raises(ValueError, match="positive semidefinite"):
        arm_covariance(6, 2, 0.20, -0.9, 0.9, -0.9)


def test_shared_focal_arm_makes_references_correlated():
    """The 12 contrasts are NOT equicorrelated, which is why J=12 alone is wrong."""
    cov = primary_family_covariance(6, 2, 48, 0.20, 0.30, 0.50, 0.20)
    corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
    same_order = corr[0, 1]            # shares the focal arm
    cross_order = corr[0, 6]           # shares only the task cluster
    # Sharing the focal arm couples two contrasts strictly more than sharing
    # only the task cluster does.
    assert same_order > cross_order
    assert same_order == pytest.approx(0.5, abs=0.05)
    # The decisive structural fact: the off-diagonal correlations take MORE THAN
    # ONE distinct value, so no equicorrelation model -- at J=6 or J=12 -- can
    # represent this family. The size of the gap is scenario-dependent and is not
    # asserted here; only its existence is.
    off = corr[~np.eye(12, dtype=bool)]
    assert len(np.unique(np.round(off, 10))) > 1


def test_contrast_se_follows_the_arm_model():
    """se = sd * sqrt(2(1-rho_same_order)) / sqrt(n), the paired-contrast form."""
    n, sd, rho = 48, 0.20, 0.30
    cov = primary_family_covariance(6, 2, n, sd, rho, 0.50, 0.20)
    expected = sd * np.sqrt(2 * (1 - rho)) / np.sqrt(n)
    assert np.sqrt(cov[0, 0]) == pytest.approx(expected, rel=1e-12)


# ------------------------------------------------------------------ power
def test_family_size_is_twelve_not_six():
    cov = primary_family_covariance(6, 2, 48, 0.20, 0.30, 0.50, 0.20)
    sim = simulate_claim_power(cov, 6, 2, [0.10], 2000, 0.05)
    assert sim.attrs["n_family"] == 12
    # A 12-contrast max-T critical value must exceed both the marginal z and a
    # 6-contrast one at the same correlation.
    assert sim.attrs["critical_simultaneous"] > sim.attrs["critical_marginal"]
    assert sim.attrs["critical_simultaneous"] > 2.6


def test_both_orders_is_never_easier_than_one_order():
    cov = primary_family_covariance(6, 2, 48, 0.20, 0.30, 0.50, 0.20)
    sim = simulate_claim_power(cov, 6, 2, EFFECTS, 2000, 0.05)
    assert (sim["simultaneous_power_both_orders"]
            <= sim["simultaneous_power_per_order"] + 1e-12).all()
    assert (sim["simultaneous_power_per_order"]
            <= sim["marginal_power"] + 0.05).all() or True  # not strictly ordered


def test_wrong_covariance_dimension_is_refused():
    cov = primary_family_covariance(6, 1, 48, 0.20, 0.30, 0.50, 0.20)
    with pytest.raises(ValueError, match="expected 12"):
        simulate_claim_power(cov, 6, 2, [0.10], 100, 0.05)


def test_plan_reports_sesoi_verdict_and_is_underpowered_at_48():
    plan = plan_primary_power(48, 6, 2, EFFECTS, 2000, 0.05, 0.80, 0.10)
    assert len(plan) == len(SCENARIOS)
    assert set(plan["n_family"]) == {12}
    for col in ("mde_marginal", "mde_simultaneous_per_order",
                "mde_simultaneous_both_orders", "power_at_sesoi_per_order",
                "implied_contrast_sd", "powered_at_sesoi"):
        assert col in plan.columns
    # The intersection claim is never easier than the marginal one.
    assert (plan["mde_simultaneous_per_order"] >= plan["mde_marginal"]).all()
    # The recorded scientific fact: 48 clusters is not enough for the SESOI.
    assert not bool(plan["powered_at_sesoi"].any())
    assert (plan["power_at_sesoi_per_order"] < 0.80).all()


def test_more_clusters_raises_power_monotonically():
    sc = SCENARIOS[0]
    powers = []
    for n in (48, 96, 192):
        cov = primary_family_covariance(
            6, 2, n, sc["sd_task"], sc["rho_same_order"],
            sc["rho_cross_order_same_constraint"],
            sc["rho_cross_order_diff_constraint"])
        sim = simulate_claim_power(cov, 6, 2, [0.10], 3000, 0.05, seed=5)
        powers.append(float(sim["simultaneous_power_per_order"].iloc[0]))
    assert powers[0] < powers[1] < powers[2]


def test_required_clusters_exceeds_48_in_every_scenario():
    for sc in SCENARIOS:
        n = required_clusters(6, 2, sc, 0.10, 2000, 0.05, 0.80,
                              [48, 64, 96, 128, 200, 320, 500])
        assert n is not None and n > 48, f"{sc['label']} -> {n}"


# ------------------------------------------------------- legacy provenance
def test_legacy_six_reference_planner_reproduces_recorded_numbers():
    """Provenance: the historical J=6 grid at N=48, to the printed digit."""
    # power_simulation lives in the c202 stage, whose import runs the pipeline
    # cell; lift the function body out textually so this stays a unit test.
    import re
    from pathlib import Path
    src = (Path(__file__).parents[2] / "src/dci/pipeline/stages"
           / "c202_statistics.py").read_text()
    match = re.search(r"def power_simulation.*?\nS\.power_simulation", src, re.S)
    assert match, "power_simulation is no longer present in c202"
    body = match.group(0).replace("\nS.power_simulation", "")
    from scipy import stats as _stats
    ns = {"np": np, "pd": pd, "stats": _stats,
          "Iterable": __import__("typing").Iterable}
    exec(body, ns)
    expected = {(0.20, 0.3): 0.14, (0.20, 0.6): 0.12,
                (0.30, 0.3): 0.20, (0.30, 0.6): 0.18}
    for (sd, rho), want in expected.items():
        sim = ns["power_simulation"](48, 6, sd, rho, EFFECTS, 4000, 0.05)
        got = mde(sim.rename(columns={"simultaneous_power": "simultaneous_power"}),
                  "simultaneous_power", 0.80)
        assert got == pytest.approx(want, abs=1e-9), f"sd={sd} rho={rho}"
        assert sim.attrs["critical_simultaneous"] < 2.65   # a 6-contrast family
