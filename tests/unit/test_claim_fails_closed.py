"""The reference-robust claim must never be certified on a reduced family.

The counterexample in `test_zero_se_reference_cannot_be_dropped` is the defect
that motivated dci.analysis.claim: five references with a genuine positive effect
and one degenerate reference at tau=0. Pre-repair, `sim_lower.min()` skipped the
degenerate NaN and reported `robust_positive=True` while naming that same
reference as the least favourable one in the adjacent column.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.claim import (CLAIM_INCONCLUSIVE, CLAIM_PASS, claim_blockers,
                                family_problems, nonfinite_cells,
                                reference_robust_claim)
from dci.analysis.stats import degenerate_components, simultaneous_bounds

pytestmark = pytest.mark.cpu

REFS = [f"R{j}" for j in range(6)]
ORDERS = ["target_first", "added_first"]


def _draws(effects: dict[str, float], degenerate: tuple[str, ...] = (),
           reps: int = 4000, sd: float = 0.05, seed: int = 0):
    """Bootstrap draws for a full 6x2 family, with named degenerate columns."""
    rng = np.random.default_rng(seed)
    cols, point = {}, {}
    for o in ORDERS:
        for j in REFS:
            key = f"tau|{j}|{o}"
            eff = effects.get(j, 0.20)
            if j in degenerate:
                cols[key] = np.zeros(reps)
                point[key] = 0.0
            else:
                cols[key] = rng.normal(eff, sd, reps)
                point[key] = eff
    return pd.Series(point), pd.DataFrame(cols)


def _primary(point, draws, level: float = 0.95):
    sim = simultaneous_bounds(point, draws, level)
    out = sim.copy()
    out["reference"] = [c.split("|")[1] for c in out.index]
    out["order"] = [c.split("|")[2] for c in out.index]
    return out, sim.attrs


def test_healthy_family_supports_the_claim():
    point, draws = _draws({})
    primary, attrs = _primary(point, draws)
    claim = reference_robust_claim(primary, REFS, ORDERS, sim_attrs=attrs)
    assert attrs["n_family_requested"] == 12
    assert attrs["n_family_calibrated"] == 12
    assert list(claim.index) == ORDERS
    for o in ORDERS:
        assert claim.loc[o, "inference_status"] == CLAIM_PASS
        assert bool(claim.loc[o, "robust_positive"]) is True
        assert int(claim.loc[o, "n_references_in_inference"]) == 6
    assert claim_blockers(claim) == []


def test_zero_se_reference_cannot_be_dropped():
    """The exact pre-repair counterexample: 5 positive + 1 zero-variance."""
    point, draws = _draws({}, degenerate=("R5",))
    primary, attrs = _primary(point, draws)

    # The degeneracy is visible at the stats layer rather than silent.
    assert degenerate_components(draws) == [f"tau|R5|{o}" for o in ORDERS]
    assert attrs["n_family_requested"] == 12
    assert attrs["n_family_calibrated"] == 10

    # Pandas' own skipna default is what used to certify the claim.
    for o in ORDERS:
        sub = primary[primary["order"] == o]
        assert sub["sim_lower"].min() > 0            # the defect, still latent
        assert not (sub["sim_lower"].min(skipna=False) > 0)

    claim = reference_robust_claim(primary, REFS, ORDERS, sim_attrs=attrs)
    for o in ORDERS:
        assert bool(claim.loc[o, "robust_positive"]) is False
        assert bool(claim.loc[o, "robust_negative"]) is False
        assert bool(claim.loc[o, "reference_robust_claim_supported"]) is False
        assert claim.loc[o, "inference_status"] == CLAIM_INCONCLUSIVE
        # The offending reference is RECORDED, not merely excluded.
        assert claim.loc[o, "degenerate_references"] == "R5"
        assert int(claim.loc[o, "n_references_in_inference"]) == 5
        assert int(claim.loc[o, "n_references_declared"]) == 6
    blockers = claim_blockers(claim)
    assert len(blockers) == 2 and all("R5" in b for b in blockers)


def test_nonfinite_cells_names_the_quantity():
    point, draws = _draws({}, degenerate=("R2",))
    primary, _ = _primary(point, draws)
    bad = nonfinite_cells(primary)
    assert set(bad["reference"]) == {"R2"}
    assert set(bad["order"]) == set(ORDERS)
    for row in bad.itertuples():
        assert "se" in row.nonfinite and "sim_lower" in row.nonfinite


def test_short_family_is_refused_not_reduced():
    """A missing reference-order cell is a construction error, so it raises."""
    point, draws = _draws({})
    primary, attrs = _primary(point, draws)
    truncated = primary[primary["reference"] != "R3"]
    with pytest.raises(ValueError, match="structurally incomplete"):
        reference_robust_claim(truncated, REFS, ORDERS, sim_attrs=attrs)
    problems = family_problems(truncated, REFS, ORDERS)
    assert any("R3" in p for p in problems)
    assert any("10 rows, expected 12" in p for p in problems)


def test_duplicated_cell_is_refused():
    point, draws = _draws({})
    primary, attrs = _primary(point, draws)
    doubled = pd.concat([primary, primary.iloc[[0]]])
    with pytest.raises(ValueError, match="structurally incomplete"):
        reference_robust_claim(doubled, REFS, ORDERS, sim_attrs=attrs)


def test_family_smaller_than_declared_blocks_the_claim():
    """A critical value calibrated on a 6-column family cannot certify 12."""
    point, draws = _draws({})
    six = [c for c in draws.columns if c.endswith("target_first")]
    sim_six = simultaneous_bounds(point[six], draws[six], 0.95)
    primary, attrs = _primary(point, draws)
    claim = reference_robust_claim(primary, REFS, ORDERS,
                                  sim_attrs=dict(sim_six.attrs))
    for o in ORDERS:
        assert claim.loc[o, "inference_status"] == CLAIM_INCONCLUSIVE
        assert "declared primary family is 12" in claim.loc[o, "family_problems"]
        assert bool(claim.loc[o, "robust_positive"]) is False


def test_robust_negative_also_requires_the_whole_family():
    point, draws = _draws({j: -0.20 for j in REFS})
    primary, attrs = _primary(point, draws)
    claim = reference_robust_claim(primary, REFS, ORDERS, sim_attrs=attrs)
    for o in ORDERS:
        assert bool(claim.loc[o, "robust_negative"]) is True
    point, draws = _draws({j: -0.20 for j in REFS}, degenerate=("R0",))
    primary, attrs = _primary(point, draws)
    claim = reference_robust_claim(primary, REFS, ORDERS, sim_attrs=attrs)
    for o in ORDERS:
        assert bool(claim.loc[o, "robust_negative"]) is False
        assert claim.loc[o, "inference_status"] == CLAIM_INCONCLUSIVE


def test_exact_zero_breaks_unanimity_of_sign():
    """sign(0)==0 is the absence of a direction, not a third direction."""
    point, draws = _draws({"R4": 0.0})
    primary, attrs = _primary(point, draws)
    claim = reference_robust_claim(primary, REFS, ORDERS, sim_attrs=attrs)
    for o in ORDERS:
        assert bool(claim.loc[o, "all_same_sign"]) is False
