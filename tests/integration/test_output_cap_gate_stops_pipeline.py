"""The output-cap gate must stop a real pipeline run, not just a unit fixture.

The shipped oracle never truncates, so the gate can only be exercised end to end
by injecting truncation deliberately (`oracle_truncation_by_constraint`). Two runs
are compared: the default, which must reach export, and a differentially
truncated one, which must stop with OUTPUT_CAP_DOMINATES at exit 10.

The injected shares are chosen to sit UNDER the absolute per-cell stop share, so
what fires is the differential rule -- the condition that actually biases tau.
"""
from pathlib import Path

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]


def _run(tmp_path: Path, overrides: dict):
    """dev_fast, which is the only shipped dry-run profile that REACHES c362.

    `integration_pass` runs with no bypass but stops at Gate 2, so it never gets
    to the confirmatory analysis; dev_fast reaches it but bypasses gates. The
    bypass is therefore left ON here and the assertion is on the RECORDED gate
    outcome, which `S.stop()` writes before deciding whether to raise. The
    no-bypass end-to-end traversal is a separate fixture (see
    tests/integration/test_full_traversal.py) and needs an admissible panel.
    """
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = str(tmp_path / "artifacts")
    cfg.protocol_overrides = {**getattr(cfg, "protocol_overrides", {}), **overrides}
    loader.activate(cfg)
    code = run_pipeline()
    return code, S


def test_default_oracle_records_no_truncation(tmp_path):
    """The shipped dry run must be unchanged: no truncation, full coverage."""
    code, S = _run(tmp_path, {})
    assert code == 0
    assert S.OUTPUT_CAP_VERDICT["ok"], S.OUTPUT_CAP_VERDICT["reasons"]
    assert S.OUTPUT_CAP_COVERAGE["coverage"] == 1.0
    assert float(S.OUTPUT_CAP_VERDICT["worst_truncated_share"]) == 0.0
    assert "5_output_budget" not in S.GATE_STATE, (
        "a clean run must not record an output-budget failure")


def test_differential_truncation_trips_the_gate(tmp_path):
    """Shares UNDER the absolute stop share: what fires is the differential rule."""
    from dci.statuses import GateStatus
    code, S = _run(tmp_path, {
        "oracle_truncation_by_constraint": (("S_MINWORDS15", 0.18),
                                            ("S_MINWORDS12", 0.16)),
    })
    outcome = S.GATE_STATE.get("5_output_budget")
    assert outcome is not None, f"gate did not run; gates={list(S.GATE_STATE)}"
    assert outcome.status == GateStatus.OUTPUT_CAP_DOMINATES
    assert outcome.new_protocol_version_required
    # The differential rule is named explicitly in the recorded reasons. (At
    # smoke cell sizes an 18% target share can also breach the absolute rule,
    # because a cell holds only a handful of rows; the isolated
    # differential-only case is pinned in tests/unit/test_output_budget.py.)
    assert any("truncation gap" in r for r in outcome.quantities["reasons"])
    assert float(outcome.quantities["worst_abs_arm_gap"]) > 0.05
    # dev_fast bypasses, so the process still completes; the record stands.
    assert code == 0 and outcome.dry_run_bypassed


def test_truncated_rows_are_retained_not_filtered(tmp_path):
    """The gate blocks interpretation; it never removes a row from the estimator."""
    code, S = _run(tmp_path, {
        "oracle_truncation_by_constraint": (("S_MINWORDS15", 0.18),),
    })
    assert code == 0
    scored = S.confirmatory_scores.query("is_measured")
    # A_ONLY carries no order dimension, so it legitimately has half the rows of
    # a tau-bearing arm; compare only the arms that enter a contrast.
    tau_arms = [S.CFG.focal_id, *S.SELECTED_REFERENCES]
    per_arm = (scored[scored["added_constraint"].isin(tau_arms)]
               .groupby("added_constraint")["row_id"].nunique())
    assert len(per_arm) == len(tau_arms)
    assert per_arm.nunique() == 1, (
        f"arms have unequal row counts after truncation: {per_arm.to_dict()}")
    truncated = scored[scored["output_truncated"].astype("boolean").fillna(False)]
    assert len(truncated) > 0, "the fixture injected no truncation"
    # Truncated rows still carry a scored outcome and still enter the table.
    assert truncated["fail"].notna().all()
    # And the primary table is still complete, which is the real guarantee.
    assert bool(S.CONF_SUPPORT["complete"].all())
