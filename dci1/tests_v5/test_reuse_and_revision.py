"""§30's ledger, §31's result table, and the v4r4 -> v5 change map."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v5.protocol import constants as C
from dci1v5.protocol import reuse_ledger, revision
from dci1v5.stages import final_report


def test_every_registered_change_is_present_in_the_code():
    record = revision.revision_record()
    assert record["study_id"] == "dci1v5"
    assert record["supersedes"] == "dci1v4r4"
    assert record["supersedes_terminal_status"] == "COMPLETED"
    assert record["n_checked"] >= 10
    assert all(c["realised"] is not False for c in record["changes"])


def test_what_v5_deliberately_does_not_change_is_named():
    sections = {s for s, _ in revision.UNCHANGED}
    assert {"§10.7", "§10.5", "§11.9", "§16", "§20"} <= sections


def test_the_ledger_carries_all_five_classifications():
    ledger = reuse_ledger.build_ledger("..")
    assert set(ledger["classifications"]) == set(C.REUSE_CLASSIFICATIONS)
    assert ledger["no_v4r4_generation_in_a_v5_estimand"] is True
    assert "design fitting" in ledger["declaration"]


def test_a_reused_implementation_entry_must_measure_two_invariants():
    with pytest.raises(ProtocolError):
        reuse_ledger.LedgerEntry("x", "REUSED_IMPLEMENTATION", "because",
                                 "§10.2")
    reuse_ledger.LedgerEntry("x", "REUSED_IMPLEMENTATION", "because", "§10.2",
                             measured_invariants=("verifier_semantics",))


def test_an_entry_needs_its_reason_and_its_criterion():
    with pytest.raises(ProtocolError):
        reuse_ledger.LedgerEntry("x", "DEVELOPMENT_EVIDENCE", "", "§12.5")
    with pytest.raises(ProtocolError):
        reuse_ledger.LedgerEntry("x", "NOT_A_CLASS", "because", "§12.5")


def test_a_result_row_must_trace_to_a_v5_stage_record():
    row = {f: "x" for f in final_report.ROW_FIELDS}
    row.update(measurement_basis=C.MEASUREMENT_BASIS, claim_level="L1",
               stage_record="", stage_record_hash="")
    with pytest.raises(ProtocolError) as excinfo:
        final_report.assert_row_traceable(row, where="row 0")
    assert "traceable" in str(excinfo.value)


def test_the_final_report_refuses_an_l3_without_reference_pool_same_form():
    row = {f: "x" for f in final_report.ROW_FIELDS}
    row.update(measurement_basis=C.MEASUREMENT_BASIS, claim_level="L1",
               stage_record="GATE_5_FREEZE", stage_record_hash="abc")
    with pytest.raises(ProtocolError):
        final_report.build_final_report(
            model_key="m", rows=[row],
            statements=[{"claim_level": "L3a", "emitted": True,
                         "identification_status": []}],
            success_criterion={"verdict": "MET"},
            identification_statuses=[], admitted_arms=["base"])


def test_the_success_criterion_is_in_the_report_whatever_was_emitted():
    row = {f: "x" for f in final_report.ROW_FIELDS}
    row.update(measurement_basis=C.MEASUREMENT_BASIS, claim_level="L1",
               stage_record="GATE_5_FREEZE", stage_record_hash="abc")
    report = final_report.build_final_report(
        model_key="m", rows=[row], statements=[],
        success_criterion={"verdict": "NOT_MET"},
        identification_statuses=["REFERENCE_SUPPORT_NOT_IDENTIFIED"],
        admitted_arms=["base"])
    assert report["methodological_success_criterion"]["verdict"] == "NOT_MET"
    assert report["scope_sentence"] == C.SCOPE_SENTENCE


def test_the_report_refuses_an_unregistered_identification_status():
    row = {f: "x" for f in final_report.ROW_FIELDS}
    row.update(measurement_basis=C.MEASUREMENT_BASIS, claim_level="L1",
               stage_record="GATE_5_FREEZE", stage_record_hash="abc")
    with pytest.raises(ProtocolError):
        final_report.build_final_report(
            model_key="m", rows=[row], statements=[],
            success_criterion={}, identification_statuses=["INVENTED"],
            admitted_arms=["base"])
