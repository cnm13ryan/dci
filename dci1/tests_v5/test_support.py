"""G. §13.15's support requirements, backups, and §19 test 4."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages import selection, support


def _core(*families):
    roles = {"MK1": ("consecutive", "marker_thus"),
             "MK3": ("contrastive", "marker_though"),
             "MK6": ("exemplifying", "marker_namely"),
             "XC1": ("none", "semicolon")}
    return [{"family": f, "severity": 4,
             "structural_tier": 1 if f.startswith("MK") else 2,
             "feature_group": roles[f][1], "discourse_role": roles[f][0]}
            for f in families]


def _support(**kwargs):
    defaults = dict(
        model_key="fixture-model",
        structurally_eligible_tier12_families=list(C.TIER1_FAMILY_IDS)
        + list(C.TIER2_FAMILY_IDS),
        qualified_families=["MK1", "MK3", "MK6", "MK2", "XC1"],
        selection={"core_references": _core("MK1", "MK3", "MK6"),
                   "identification_statuses": ["REFERENCE_POOL_SAME_FORM"]},
        near_form_available=True, class_available=True,
        spectrum_identified=True)
    defaults.update(kwargs)
    return support.evaluate_support(**defaults)


def test_the_registered_requirements_are_the_protocol_values():
    assert C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES == 8
    assert C.MIN_QUALIFIED_FAMILIES == 5
    assert C.N_CORE_REFERENCES == 3
    assert C.MIN_TIER1_CORE == 2
    assert C.N_CORE_FEATURE_GROUPS == 3
    assert C.N_BACKUP_FAMILIES == 2
    assert C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 is False


def test_a_supported_replication_admits_every_arm_and_derives_56_cells():
    out = _support()
    assert out["support_met"]
    assert out["derived_cell_count"] == 56
    assert set(out["admitted_arms"]) == set(C.ARMS)
    assert len(out["realised"]["frozen_backups"]) == 2


def test_four_qualifying_families_is_not_enough():
    out = _support(qualified_families=["MK1", "MK3", "MK6", "MK2"])
    assert not out["support_met"]
    assert any("frozen backups" in f for f in out["failures"])
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" in out["identification_statuses"]
    # §8.1: dropping an arm never drops another. The core and spectrum arms
    # go; the near-form and broad-class arms still run, so Delta_near and
    # Delta_broad stay identified.
    assert set(out["admitted_arms"]) == {"base", "nearform", "class"}
    assert out["derived_cell_count"] == 17


def test_one_tier_one_core_reference_is_not_enough():
    out = _support(selection={"core_references":
                              [dict(e, structural_tier=2)
                               for e in _core("MK1", "MK3")]
                              + _core("MK6"),
                              "identification_statuses": []})
    assert not out["support_met"]
    assert any("Tier-1" in f for f in out["failures"])


def test_a_dropped_arm_never_drops_another():
    out = _support(near_form_available=False, class_available=False)
    assert out["support_met"]
    assert set(out["admitted_arms"]) == {"base", "core", "spectrum"}
    assert "NEAR_FORM_ARM_NOT_AVAILABLE" in out["identification_statuses"]
    assert "CLASS_ARM_NOT_AVAILABLE" in out["identification_statuses"]


def test_the_spectrum_can_drop_without_the_core_arm():
    out = _support(spectrum_identified=False)
    assert out["support_met"]
    assert "spectrum" not in out["admitted_arms"]
    assert "core" in out["admitted_arms"]
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in \
        out["identification_statuses"]


def test_the_disposition_is_unresolved_while_d6_is_open(restore_decisions):
    out = _support(qualified_families=["MK1", "MK3", "MK6"])
    assert out["disposition"] == decisions.UNRESOLVED
    with pytest.raises(decisions.DecisionOpenError):
        support.support_disposition(met=False)
    restore_decisions.close("D6", "terminal", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    assert support.support_disposition(met=False) == \
        "REFERENCE_SUPPORT_NOT_IDENTIFIED_TERMINAL"


def test_no_backup_substitution_function_exists():
    """§19 test 4: the path must not exist, not merely be unused."""
    selection.assert_no_backup_substitution(vars(selection))
    selection.assert_no_backup_substitution(vars(support))
    with pytest.raises(ProtocolError):
        selection.assert_no_backup_substitution(
            {"substitute_backup": lambda: None})
    with pytest.raises(ProtocolError):
        selection.assert_no_backup_substitution(
            {"promote_backup_after_gate4": lambda: None})


def test_no_gate4_table_can_reach_a_selection_function():
    """§19 test 4's other half: the loader refuses a Gate-4 column."""
    from dci1v5.stages.calibration_table import load_calibration_table
    row = {"kind": "MK1", "severity": 3, "split": "pooled",
           "model_key": "fixture-model", "solo_compliance": 0.7,
           "chance_compliance": 0.0, "solo_vacuity": 0.0,
           "gate4_composed_rate": 0.5}
    with pytest.raises(ProtocolError):
        load_calibration_table([row], model_key="fixture-model", m_star=9,
                               split="pooled")


def test_the_success_criterion_is_reported_before_gate_4():
    out = _support()
    pre = support.methodological_success(out)
    assert pre["verdict"] == "MET"
    assert pre["stage"] == "pre_gate_4"
    post = support.methodological_success(out, gate4_passed=False)
    assert post["verdict"] == "NOT_MET"
    assert "finding about §13.6's interaction rule" in post["note"]
