"""§30's ledger, §31's result table, and the v4r4 -> v5 change map."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v6.protocol import constants as C
from dci1v6.protocol import reuse_ledger, revision
from dci1v6.stages import final_report


def test_every_registered_change_is_present_in_the_code():
    record = revision.revision_record()
    assert record["study_id"] == "dci1v6"
    assert record["supersedes"] == "dci1v5"
    assert record["supersedes_terminal_status"] == \
        "CLOSED_WITHOUT_CONFIRMATORY_GENERATION"
    # Every v6 change is executable and every one is checked. A listed change
    # the code does not make stops stage 1, because `assert_changes_realised`
    # is on the registration path.
    assert record["n_changes"] == record["n_checked"] == 8
    assert all(c["realised"] is True for c in record["changes"])
    assert [c["id"] for c in record["changes"]] == [
        f"V{i}" for i in range(1, 9)]


def test_the_two_expansion_repairs_are_registered_changes():
    """V6-E01 and V6-E02 are scientific changes, not bug fixes.

    Both alter which data §12.6's coverage criterion reads, which is the rule
    that decides whether a replication has reference support at all. They are
    listed with an executable check apiece so that neither can be quietly
    reverted.
    """
    by_id = {c.id: c for c in revision.CHANGES}
    assert by_id["V1"].section == "§12.6" and by_id["V1"].check is not None
    assert by_id["V2"].section == "§12.6" and by_id["V2"].check is not None
    assert by_id["V1"].check() and by_id["V2"].check()


def test_no_threshold_moves_and_the_absence_is_checked():
    """v5 failed on C4 and on §13.14's band, and v6 moves neither.

    A revision after a failed study is exactly where a bar gets lowered, so
    the absence is a registered change with a callable rather than a sentence
    in a document.
    """
    by_id = {c.id: c for c in revision.CHANGES}
    assert by_id["V8"].what == "NO THRESHOLD MOVES"
    assert by_id["V8"].check()


def test_what_v6_deliberately_does_not_change_is_named():
    sections = {s for s, _ in revision.UNCHANGED}
    assert {"§3.2", "§6.1", "§12.6", "§13.11", "§15", "§16"} <= sections
    text = " ".join(w for _s, w in revision.UNCHANGED)
    assert "permanently withheld" in text          # L5
    assert "never pooled" in text                  # §6.1's firewall


def test_the_ledger_carries_all_five_classifications():
    ledger = reuse_ledger.build_ledger("..")
    assert set(ledger["classifications"]) == set(C.REUSE_CLASSIFICATIONS)
    assert ledger["no_v5_generation_in_a_v6_estimand"] is True
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
