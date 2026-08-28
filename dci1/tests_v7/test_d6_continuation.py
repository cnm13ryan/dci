"""v7 A6/A7/A8, end to end: a replication that loses its reference set, or
only its spectrum, reaches FINAL_REPORT on its surviving arms.

Marked ``slow``: each scenario drives the production runners from a signed
GATE_1 prefix through the pre-freeze audit, the freeze, confirmatory
generation, both analyses and the final report. The audit tool runs the same
scenarios; these tests pin their outcomes in the suite so that the invariant
"D6 = identification_status reaches the freeze" cannot regress silently ---
which is exactly what it did for two revisions while the only scenario
stopped at Gate 3C.
"""
from __future__ import annotations

import pytest

from dci1v7.protocol import constants as C
from dci1v7.protocol import identification

from tests_v7 import scenarios as SC
from tests_v7 import synthetic_lifecycle as SL


@pytest.fixture(scope="module")
def d6(tmp_path_factory):
    SL.resolved_manifest()
    root = tmp_path_factory.mktemp("d6")
    try:
        yield {name: SC.run_scenario(name, root / name) for name in (
            "reference_support_not_identified", "c4_lost_core_kept",
            "reference_checks_conditional", "full_support_unchanged")}
    finally:
        SL.restore()


@pytest.mark.slow
def test_a_non_identified_replication_reaches_the_final_report(d6):
    out = d6["reference_support_not_identified"]
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" in out["gate3c_statuses"]
    assert out["support_met"] is False
    assert out["disposition"] == "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    assert "core" not in out["admitted_arms"]
    assert "spectrum" not in out["admitted_arms"]
    assert "base" in out["admitted_arms"]
    assert out["n_not_identified"] == len(identification.AFFECTED_ESTIMANDS)
    assert out["delta_r_blocked"] and out["irreversible"]
    assert out["prefreeze_outcome"] == "PASS"
    assert out["prefreeze_support_met_required"] is False
    checks = out["prefreeze_checks"]
    for name in ("support_recorded", "d6_disposition_registered",
                 "arms_match_identification", "no_rehabilitation_path",
                 "freeze_fields_explained"):
        assert checks[name] == "PASS", (name, checks)
    assert checks["selected_references_valid"] == "NOT_APPLICABLE"
    assert checks["calibration_stability_satisfied"] == "NOT_APPLICABLE"
    assert out["freeze_block_status"] == "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    assert out["confirmatory_rows"] > 0
    assert out["d_b_from_a"] == "IDENTIFIED"
    assert out["lambda"] == "IDENTIFIED"
    assert out["delta_r"] == "NOT_IDENTIFIED"
    assert out["delta_r_reason"] == "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    assert out["final_report_outcome"] == "PASS"
    assert out["tamper_delta_r_refused"]
    assert out["still_identified_includes_base_arm"]


@pytest.mark.slow
def test_c4_lost_alone_keeps_delta_r_and_drops_the_spectrum(d6):
    out = d6["c4_lost_core_kept"]
    assert out["calibrated_conditions"]["C4"] is False
    assert out["calibrated_core_met"] is True
    assert out["calibrated_spectrum_met"] is False
    assert out["calibrated_core_failures"] == []
    assert out["calibrated_spectrum_failures"]
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in out["gate3c_statuses"]
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in out["gate3c_statuses"]
    assert out["support_met"] is True and out["spectrum_met"] is False
    assert "core" in out["admitted_arms"]
    assert "spectrum" not in out["admitted_arms"]
    assert out["block_status"] == "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    assert out["blocked_is_the_spectrum_set"]
    assert not out["delta_r_blocked"]
    assert out["prefreeze_outcome"] == "PASS"
    assert out["prefreeze_checks"]["selected_references_valid"] == "PASS"
    assert out["prefreeze_checks"]["calibration_stability_satisfied"] == "PASS"
    assert out["delta_r"] == "IDENTIFIED"
    assert out["delta_difficulty"] == "NOT_IDENTIFIED"
    assert out["delta_difficulty_reason"] == "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    assert out["d_b_from_r1_minus"] == "NOT_IDENTIFIED"
    assert out["final_report_outcome"] == "PASS"
    assert out["tamper_delta_difficulty_refused"]
    assert out["tamper_delta_r_allowed"]


@pytest.mark.slow
def test_reference_checks_follow_the_core_arm(d6):
    out = d6["reference_checks_conditional"]
    for name, (verdict, explained) in out["without_core_arm"].items():
        assert verdict == "NOT_APPLICABLE", name
        assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" in (explained or [])
    for name, (verdict, _explained) in out["with_core_arm"].items():
        assert verdict == "PASS", name
    assert out["without_core_arm_outcome"] == "PASS"
    assert out["with_core_arm_outcome"] == "PASS"
    assert out["without_core_arm_not_applicable"] == 2
    assert out["with_core_arm_not_applicable"] == 0


@pytest.mark.slow
def test_the_full_design_is_unchanged(d6):
    out = d6["full_support_unchanged"]
    assert out["calibrated_core_met"] and out["calibrated_spectrum_met"]
    assert out["support_met"] and out["spectrum_met"]
    assert set(out["admitted_arms"]) == set(C.ARMS)
    assert out["derived_cell_count"] == 56
    assert out["non_identification"] is None
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in out["gate3c_statuses"]
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" not in out["gate3c_statuses"]
    assert out["prefreeze_outcome"] == "PASS"
    assert out["n_not_applicable"] == 0
    assert set(out["freeze_admitted_arms"]) == set(C.ARMS)
    assert out["delta_r"] == "IDENTIFIED"
    assert out["delta_difficulty"] == "IDENTIFIED", out
    assert out["d_b_from_r1_minus"] == "IDENTIFIED"
    assert out["final_report_outcome"] == "PASS"
