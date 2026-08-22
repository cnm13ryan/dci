"""K + L. The eighteen-stage lifecycle, and §34's execution block."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v5.engine import transitions
from dci1v5.engine.paths import STAGE_RECORD_FILES
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages.audit_prefreeze import (
    CHECKLIST, run_prefreeze_audit,
)


def test_the_stage_sequence_is_the_registered_eighteen():
    assert len(C.STAGE_SEQUENCE) == 18
    assert C.STAGE_SEQUENCE[0] == C.STAGE_REGISTERED
    assert C.STAGE_SEQUENCE[-1] == C.STAGE_FINAL_REPORT
    for inserted in (C.STAGE_GATE2_5, C.STAGE_GATE3A, C.STAGE_GATE3B,
                     C.STAGE_GATE3C, C.STAGE_PREFREEZE_AUDIT):
        assert inserted in C.STAGE_SEQUENCE


def test_every_stage_owns_exactly_one_record_and_one_artifact_type():
    assert set(STAGE_RECORD_FILES) == set(C.STAGE_SEQUENCE)
    assert len(set(STAGE_RECORD_FILES.values())) == len(C.STAGE_SEQUENCE)
    assert set(C.STAGE_ARTIFACT_TYPE) == set(C.STAGE_SEQUENCE)


def test_each_stage_has_exactly_one_predecessor_in_order():
    for index, stage in enumerate(C.STAGE_SEQUENCE):
        expected = None if index == 0 else C.STAGE_SEQUENCE[index - 1]
        assert transitions.PREDECESSOR[stage] == expected


def test_gate_5_is_unreachable_while_the_prefreeze_audit_has_not_passed():
    """§18 makes the audit Gate 5's predecessor; no special case is needed."""
    assert transitions.PREDECESSOR[C.STAGE_GATE5] == C.STAGE_PREFREEZE_AUDIT


def test_gate_2_5_needs_no_generation():
    """The point of §9.1's presence rule: kappa(R|B) is free."""
    assert C.STAGE_GATE2_5 not in C.GENERATION_STAGES
    assert C.STAGE_GATE2 in C.GENERATION_STAGES


def test_protocol_registered_depends_on_every_open_decision():
    blocking = decisions.decisions_blocking_stage(C.STAGE_REGISTERED)
    assert set(blocking) == set(decisions.DECISION_IDS)
    with pytest.raises(decisions.DecisionOpenError):
        transitions.assert_decisions_permit(C.STAGE_REGISTERED)


def test_no_v5_stage_can_run_today():
    """The whole lifecycle is closed at stage 1 while §34 is open."""
    with pytest.raises(decisions.DecisionOpenError):
        transitions.assert_decisions_permit(C.STAGE_REGISTERED)
    for stage in (C.STAGE_QUALIFIED, C.STAGE_REGIME, C.STAGE_GATE2,
                  C.STAGE_GATE3A, C.STAGE_GATE3C, C.STAGE_UNMASKED_ANALYSIS):
        with pytest.raises(decisions.DecisionOpenError):
            transitions.assert_decisions_permit(stage)


def test_a_stage_with_no_blocking_decision_is_permitted():
    transitions.assert_decisions_permit(C.STAGE_GATE2_5)
    transitions.assert_decisions_permit(C.STAGE_GATE3B)


def test_closing_a_decision_unblocks_only_its_own_stages(restore_decisions):
    restore_decisions.close("D17", "no_floor", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    assert "D17" not in decisions.decisions_blocking_stage(C.STAGE_GATE2)
    with pytest.raises(decisions.DecisionOpenError):
        transitions.assert_decisions_permit(C.STAGE_REGISTERED)


def test_the_decision_registry_is_the_registered_nineteen():
    assert len(decisions.DECISIONS) == 19
    assert decisions.DECISION_IDS == tuple(f"D{i}" for i in range(19))
    assert len(decisions.open_decisions()) == 19


def test_a_decision_cannot_be_closed_without_its_evidence(restore_decisions):
    with pytest.raises(ProtocolError):
        restore_decisions.close("D0", "adopt", evidence="", decided_by="x",
                                decided_on="2026-08-22")
    with pytest.raises(ProtocolError):
        restore_decisions.close("D0", "not_an_option", evidence="e",
                                decided_by="x", decided_on="2026-08-22")
    restore_decisions.close("D0", "adopt", evidence="e", decided_by="x",
                            decided_on="2026-08-22")
    with pytest.raises(ProtocolError):
        restore_decisions.close("D0", "adopt", evidence="e", decided_by="x",
                                decided_on="2026-08-22")


def test_a_choice_must_supply_a_branch_for_every_admissible_value():
    with pytest.raises(ProtocolError):
        decisions.choice("D6", {"identification_status": 1}, where="test")


def test_the_prefreeze_audit_runs_fifteen_checks_and_blocks_the_freeze():
    audit = run_prefreeze_audit(repo_root="..")
    assert len(CHECKLIST) == 15
    assert audit["n_checks"] == 15
    assert audit["can_freeze"] is False
    assert audit["outcome"] == "PREFREEZE_AUDIT_FAILURE"
    assert audit["n_open_decisions"] == 19


def test_the_audit_surfaces_every_unresolved_redteam_finding():
    """All five are surfaced; four block, and R5 is a permanent limitation.

    A finding blocks while **its registered mitigation is still open**, and
    the mitigation is a §34 decision. R5 has none --- §13.8 closes its second
    half and its first half is not closeable by a rule --- so treating its
    presence as a blocker would make ``can_freeze`` unsatisfiable however the
    study went, which is a gate that cannot pass rather than a hard one.
    """
    from dci1v5.stages.audit_prefreeze import UNRESOLVED_REDTEAM_FINDINGS

    audit = run_prefreeze_audit(repo_root="..")
    assert set(UNRESOLVED_REDTEAM_FINDINGS) == {"R1", "R5", "R11", "R14",
                                                "R16"}
    assert set(audit["unresolved_redteam_findings"]) == {"R1", "R11", "R14",
                                                         "R16"}
    assert set(audit["permanent_limitations"]) == {"R5"}
    assert audit["permanent_limitations"]["R5"]["closeable_by_rule"] is False
    assert audit["unresolved_redteam_findings"]["R1"]["decision"] == "D18"


def test_only_the_final_report_check_is_deferred():
    """§33 check 14 reads a table that does not exist at stage 12.

    Check 15 is **not** deferred. It scans the v5 artifact texts, which exist
    from stage 1; an earlier revision passed none and got UNRESOLVED forever,
    which is a check that never ran.
    """
    from dci1v5.stages.audit_prefreeze import DEFERRED_CHECKS

    audit = run_prefreeze_audit(repo_root="..")
    assert DEFERRED_CHECKS == (14,)
    deferred = {c["n"] for c in audit["deferred_to_final_report"]}
    assert deferred == {14}
    assert all(c["verdict"] == "UNRESOLVED"
               for c in audit["deferred_to_final_report"])
    # And an unestablished check that is NOT deferred still blocks.
    assert any(c["n"] == 8 for c in audit["checklist"])


def test_check_15_has_a_producer_and_passes_over_the_real_artifacts():
    """The v5 artifact texts, from the declaration the check itself owns."""
    from dci1v5.protocol.reuse_ledger import collect_artifact_texts

    texts = collect_artifact_texts("..")
    assert len(texts) >= 3
    audit = run_prefreeze_audit(repo_root="..", artifact_texts=texts)
    check15 = next(c for c in audit["checklist"] if c["n"] == 15)
    assert check15["verdict"] == "PASS"
    assert check15["detail"]["scanned"] == len(texts)


def test_a_named_artifact_that_is_absent_is_a_refusal_not_an_empty_scan():
    from dci1v4.errors import ProtocolError
    from dci1v5.protocol.reuse_ledger import collect_artifact_texts

    with pytest.raises(ProtocolError, match="scans nothing is not a check"):
        collect_artifact_texts("/nonexistent-repo-root")


def test_one_failing_check_is_enough_to_block_the_freeze():
    audit = run_prefreeze_audit(
        repo_root="..",
        gate4_record={"outcome": "PASS", "replace_reference": "R1"})
    check8 = next(c for c in audit["checklist"] if c["n"] == 8)
    assert check8["verdict"] == "FAIL"
    assert audit["can_freeze"] is False


def test_an_unresolved_check_is_not_a_pass():
    """Called with nothing supplied, three checks cannot be established.

    8 has no Gate-4 record, 14 has no final-report table and 15 has no texts.
    Only 14 is *deferred*; the other two block, which is the point. The stage
    runner supplies a Gate-4 record and the artifact texts, so on the real
    path only 14 is left unestablished.
    """
    audit = run_prefreeze_audit(repo_root="..")
    unresolved = [c for c in audit["checklist"] if c["verdict"] == "UNRESOLVED"]
    assert unresolved
    assert all(c["n"] in (8, 14, 15) for c in unresolved)
    assert audit["can_freeze"] is False
    assert {c["n"] for c in audit["failures"]} >= {8, 15}


def test_terminal_statuses_include_the_two_new_ones():
    assert "REGISTRATION_INCOMPLETE" in C.TERMINAL_STATUSES
    assert "PREFREEZE_AUDIT_FAILURE" in C.TERMINAL_STATUSES


def test_the_new_identification_statuses_are_registered():
    for status in ("REFERENCE_SUPPORT_NOT_IDENTIFIED", "LOCAL_TIER_DISAGREE",
                   "INTERACTION_ESTIMATE_DRIFTED",
                   "REFERENCE_ROLE_NOT_MATCHED", "REFERENCE_POOL_SAME_FORM",
                   "NEAR_FORM_ARM_NOT_AVAILABLE",
                   "OPERATING_POINT_AT_GRID_BOUNDARY"):
        assert status in C.IDENTIFICATION_STATUSES
        assert status in C.NEW_IDENTIFICATION_STATUSES


def test_the_freeze_record_refuses_an_unexplained_empty_field():
    from dci1v5.stages import freeze

    record = {f: "x" for f in freeze.REQUIRED_FIELDS}
    record.update(build := freeze.build_freeze_record())
    record.update(admitted_arms=["base"], derived_cell_count=5,
                  open_decisions=[], core_references=[])
    with pytest.raises(ProtocolError):
        freeze.assert_freeze_complete(record, identification_statuses=[])
    freeze.assert_freeze_complete(
        record, identification_statuses=["REFERENCE_SUPPORT_NOT_IDENTIFIED"])
    assert build["backups_never_substituted"] is True


def test_the_freeze_refuses_while_a_decision_is_open():
    from dci1v5.stages import freeze

    record = {f: "x" for f in freeze.REQUIRED_FIELDS}
    record.update(freeze.build_freeze_record())
    record.update(admitted_arms=["base", "class"], derived_cell_count=8,
                  open_decisions=list(decisions.open_decisions()),
                  core_references=[], spectrum_severities=[],
                  near_form_controls=[], frozen_backup_families=[],
                  qualified_pool=[])
    with pytest.raises(ProtocolError) as excinfo:
        freeze.assert_freeze_complete(
            record,
            identification_statuses=["REFERENCE_SUPPORT_NOT_IDENTIFIED",
                                     "DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
                                     "NEAR_FORM_ARM_NOT_AVAILABLE"])
    assert "§34" in str(excinfo.value)
