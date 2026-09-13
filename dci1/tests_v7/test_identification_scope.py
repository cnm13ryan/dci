"""v7 A6/A7/A8: the two non-identification blocks, the per-arm coverage
verdict, and the pre-freeze audit that reads the record rather than the
verdict.

Seven replications of v5, v6 and v7 passed every scientific gate and ended
on a pre-freeze check that required §13.15 to have been *met*, against a
closed §34 D6 that says the replication continues. These tests pin the
corrected shape: which members each design-time status makes
``NOT_IDENTIFIED``, which arm a lost coverage condition costs, and what the
audit establishes instead of ``support_met``.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.design.cells import arms_from_identification
from dci1v7.protocol import constants as C
from dci1v7.protocol import identification
from dci1v7.run import analysis_run, prefreeze_run
from dci1v7.stages import support


# ----------------------------------------------------------- the two sets

def test_the_spectrum_set_is_a_strict_subset_of_the_reference_set():
    spectrum = set(identification.SPECTRUM_ESTIMANDS)
    affected = set(identification.AFFECTED_ESTIMANDS)
    assert spectrum < affected
    # §8.1: a replication that cannot identify the spectrum still estimates
    # Delta_R, Delta_j, Xi and the reciprocal matrix.
    for kept in ("Delta_R", "Delta_1", "Delta_2", "Delta_3", "Xi",
                 "D(B<-R1)", "D(A<-R1)", "D(R1<-B)", "D(Rbar<-A)",
                 "D(Rbar<-Rbar')", "Ord_Rbar", "Delta^A",
                 "Delta_R|vacuity_forced", "vac(B|B+R1)-vac(B solo)"):
        assert kept in affected and kept not in spectrum, kept
    # And what the spectrum set does hold: the six rungs' losses and vacuity
    # rows, the residual and its recodings, the fit's own parameters.
    for lost in ("D(B<-R1-)", "D(B<-R3+)", "vac(B|B+R2+)-vac(B solo)",
                 "delta_difficulty", "delta_difficulty|graded_0.99", "beta",
                 "alpha_2", "gamma_tier"):
        assert lost in spectrum, lost
    assert len(spectrum) == 20 and len(affected) == 48


def test_affected_members_follows_the_statuses():
    assert identification.affected_members(
        ["REFERENCE_SUPPORT_NOT_IDENTIFIED"]) == \
        identification.AFFECTED_ESTIMANDS
    assert identification.affected_members(
        ["EXCESS_NOT_IDENTIFIED", "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]) == \
        identification.AFFECTED_ESTIMANDS
    assert identification.affected_members(
        ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]) == \
        identification.SPECTRUM_ESTIMANDS
    assert identification.affected_members(
        ["NEAR_FORM_ARM_NOT_AVAILABLE", "CLASS_ARM_NOT_AVAILABLE"]) == ()
    assert identification.status_of_members(
        ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]) == \
        "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    assert identification.status_of_members([]) is None


def test_the_base_arm_is_unconditional():
    """A8: nothing a Gate-3 verdict can do removes the base arm."""
    assert arms_from_identification(
        core_identified=False, spectrum_identified=False,
        near_form_identified=False, class_identified=False) == ("base",)
    assert set(identification.BASE_ARM_ESTIMANDS) <= set(
        identification.UNAFFECTED_ESTIMANDS)
    assert not any("SUPPORT" in s for s in C.TERMINAL_STATUSES)


# -------------------------------------------------------- the two blocks

def test_a_spectrum_only_loss_writes_its_own_irreversible_block():
    block = identification.non_identification(
        model_key="m", support_met=True, spectrum_identified=False,
        spectrum_failures=["C4 on the calibrated basis"])
    assert block["status"] == "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    assert block["terminal"] is False and block["irreversible"] is True
    assert block["replication_continues"] is True
    assert set(block["not_identified_members"]) == set(
        identification.SPECTRUM_ESTIMANDS)
    assert "Delta_R" in block["still_identified_members"]
    assert "D(B<-A)" in block["still_identified_members"]
    assert identification.non_identification(
        model_key="m", support_met=True, spectrum_identified=True) is None


def test_a_block_refuses_an_unregistered_status():
    with pytest.raises(ProtocolError):
        identification.NonIdentification(
            model_key="m", failures=(), members=(),
            status="NEAR_FORM_ARM_NOT_AVAILABLE").as_dict()


def test_the_spectrum_block_cannot_be_lifted_either():
    block = identification.non_identification(
        model_key="m", support_met=True, spectrum_identified=False)
    with pytest.raises(ProtocolError, match="DIFFICULTY_SUPPORT"):
        identification.assert_not_rehabilitated(
            {"estimands": {"delta_difficulty": {"estimate": 0.1}}},
            gate3c=block, where="test")
    # Delta_R is not in the spectrum block, so an estimate for it is legal.
    identification.assert_not_rehabilitated(
        {"estimands": {"Delta_R": {"estimate": 0.1}}}, gate3c=block,
        where="test")


# ---------------------------------------------------- the support kernel

def _core():
    return [{"family": f, "severity": 4, "structural_tier": 1,
             "feature_group": g, "discourse_role": r}
            for f, g, r in (("MK1", "marker_thus", "consecutive"),
                            ("MK3", "marker_though", "contrastive"),
                            ("MK6", "marker_namely", "exemplifying"))]


def _support(**kwargs):
    defaults = dict(
        model_key="fixture-model",
        structurally_eligible_tier12_families=list(C.TIER1_FAMILY_IDS)
        + list(C.TIER2_FAMILY_IDS),
        qualified_families=["MK1", "MK3", "MK6", "MK2", "XC1"],
        selection={"core_references": _core(),
                   "identification_statuses": []},
        near_form_available=True, class_available=True,
        spectrum_identified=True)
    defaults.update(kwargs)
    return support.evaluate_support(**defaults)


def test_a7_a_calibrated_c4_failure_drops_the_spectrum_and_keeps_the_core():
    out = _support(spectrum_design_time_failures=["C4 on the calibrated basis"])
    assert out["support_met"] and not out["spectrum_met"]
    assert out["failures"] == []
    assert out["spectrum_failures"] == ["C4 on the calibrated basis"]
    assert "core" in out["admitted_arms"]
    assert "spectrum" not in out["admitted_arms"]
    assert out["derived_cell_count"] == 56 - 18
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in out["identification_statuses"]
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in \
        out["identification_statuses"]
    assert out["disposition"] == "SUPPORTED"
    assert out["non_identification"]["status"] == \
        "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    assert set(out["not_identified_members"]) == set(
        identification.SPECTRUM_ESTIMANDS)
    assert out["replication_continues"] is True


def test_a7_a_calibrated_core_failure_still_drops_both_arms():
    out = _support(design_time_failures=["C1 on the calibrated basis"])
    assert not out["support_met"]
    assert "core" not in out["admitted_arms"]
    assert "spectrum" not in out["admitted_arms"]
    assert out["non_identification"]["status"] == \
        "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    assert set(out["not_identified_members"]) == set(
        identification.AFFECTED_ESTIMANDS)
    assert out["terminal"] is False


def test_a_full_design_carries_no_block():
    out = _support()
    assert out["support_met"] and out["spectrum_met"]
    assert out["non_identification"] is None
    assert set(out["admitted_arms"]) == set(C.ARMS)


# ------------------------------------------------------- the audit's read

def _gate3c(report, **extra):
    return {"support": report,
            "identification_statuses": report["identification_statuses"],
            "non_identification": report["non_identification"],
            "not_identified_members": report["not_identified_members"],
            "admitted_arms": report["admitted_arms"], **extra}


def _verdicts(gate3c, gate4=None):
    if gate4 is None:
        gate4 = {"composed_contrast": {"families": {}}}
    return {c: ok for c, ok, _d in prefreeze_run.support_checks(
        gate3c, gate4=gate4)}


def test_a6_no_artifact_check_requires_support_met():
    ids = [cid for cid, _w, _b in prefreeze_run.ARTIFACT_CHECKS]
    assert "support_satisfied" not in ids
    for required in ("support_recorded", "d6_disposition_registered",
                     "arms_match_identification", "no_rehabilitation_path",
                     "freeze_fields_explained"):
        assert required in ids
    import inspect
    assert 'bool(report.get("support_met"))' not in inspect.getsource(
        prefreeze_run.artifact_checks)


@pytest.mark.parametrize("case", ["core_lost", "spectrum_lost", "full"])
def test_a6_a_consistent_record_passes_whatever_it_lost(case):
    if case == "core_lost":
        report = _support(qualified_families=["MK1", "MK3"],
                          selection={"core_references": [],
                                     "identification_statuses": []},
                          spectrum_identified=False)
    elif case == "spectrum_lost":
        report = _support(spectrum_design_time_failures=["C4"])
    else:
        report = _support()
    verdicts = _verdicts(_gate3c(report))
    assert all(verdicts.values()), verdicts


def test_a6_an_inconsistent_record_fails_the_audit():
    report = _support(qualified_families=["MK1", "MK3"],
                      selection={"core_references": [],
                                 "identification_statuses": []},
                      spectrum_identified=False)
    # 1. a member missing from the block: the rule derives 48, the record 47
    tampered = dict(report)
    block = dict(report["non_identification"])
    block["not_identified_members"] = block["not_identified_members"][:-1]
    tampered["non_identification"] = block
    gate3c = _gate3c(report)
    gate3c["non_identification"] = block
    gate3c["not_identified_members"] = block["not_identified_members"]
    assert _verdicts(gate3c)["d6_disposition_registered"] is False
    # 2. the core arm present while REFERENCE_SUPPORT_NOT_IDENTIFIED stands
    gate3c = _gate3c(report)
    gate3c["admitted_arms"] = ["base", "core"]
    assert _verdicts(gate3c)["arms_match_identification"] is False
    # 3. the base arm missing
    gate3c = _gate3c(report)
    gate3c["admitted_arms"] = []
    assert _verdicts(gate3c)["arms_match_identification"] is False
    # 4. a later record offering Delta_R
    gate3c = _gate3c(report)
    assert _verdicts(gate3c, gate4={"composed_contrast": {"families": {
        "F1:outcome_first": {"members": {"Delta_R": {"estimate": 0.2}}}}}})[
        "no_rehabilitation_path"] is False
    # 5. a block declared reversible
    gate3c = _gate3c(report)
    block = dict(report["non_identification"]); block["irreversible"] = False
    gate3c["non_identification"] = block
    assert _verdicts(gate3c)["d6_disposition_registered"] is False
    # 6. a met support that still carries a block
    met = _support()
    gate3c = _gate3c(met)
    gate3c["non_identification"] = report["non_identification"]
    assert _verdicts(gate3c)["d6_disposition_registered"] is False


def test_not_applicable_does_not_block_and_names_its_status():
    assert prefreeze_run.NOT_APPLICABLE in prefreeze_run.NON_BLOCKING_VERDICTS
    assert "FAIL" not in prefreeze_run.NON_BLOCKING_VERDICTS
    assert "UNRESOLVED" not in prefreeze_run.NON_BLOCKING_VERDICTS


# ------------------------------------------------------ the analysis read

def test_the_analysis_blocks_exactly_the_frozen_members():
    block = identification.non_identification(
        model_key="m", support_met=True, spectrum_identified=False)
    licensed = analysis_run._licensed(["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"],
                                      block)
    assert set(licensed) == set(identification.SPECTRUM_ESTIMANDS)
    assert all(v == "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
               for v in licensed.values())
    assert "Delta_R" not in licensed
    # Without a frozen block --- §13.13 failing on the confirmatory data ---
    # only the fit's members are blocked and the spectrum losses stay
    # estimable.
    analysis_time = analysis_run._licensed(
        ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"], None)
    assert "delta_difficulty" in analysis_time
    assert "D(B<-R1-)" not in analysis_time


# ------------------------------------------------- the §11.8 ladder guard

@pytest.mark.parametrize("arms", [("base",), ("base", "core"),
                                  ("base", "core", "nearform", "class")])
def test_no_spectrum_ladder_without_the_nine_slots(arms):
    """Found by the first end-to-end walk of a non-identified replication:
    a freeze whose slot map lacks the spectrum slots supplies no §11.8
    ladder, rather than an empty or three-point one that crashes the
    identity check."""
    from tests_v7.conftest import observation_table
    table = observation_table(arms, blocks=4)
    slot_families = {slot: f"MK{i + 1}"
                     for i, slot in enumerate(C.CORE_SLOTS)}
    assert analysis_run.spectrum_inputs(table, slot_families) == {}
    assert analysis_run.spectrum_inputs(table, {}) == {}


def test_the_full_ladder_still_builds():
    from tests_v7.conftest import observation_table
    table = observation_table(("base", "core", "spectrum"), blocks=4)
    slot_families = {slot: f"MK{i + 1}"
                     for i, slot in enumerate(C.CORE_SLOTS)}
    for i, slot in enumerate(C.SPECTRUM_SLOTS):
        slot_families[slot] = f"MK{i // 2 + 1}"
    inputs = analysis_run.spectrum_inputs(table, slot_families)
    assert set(inputs) == set(C.CONFIGURATIONS)
    assert len(inputs[C.OUTCOME_FIRST].family_of) == 9
