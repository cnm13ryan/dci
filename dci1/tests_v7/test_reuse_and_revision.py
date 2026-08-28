"""§30's ledger, §31's result table, and the v4r4 -> v5 change map."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.protocol import reuse_ledger, revision
from dci1v7.stages import final_report


def test_every_registered_change_is_present_in_the_code():
    record = revision.revision_record()
    assert record["study_id"] == "dci1v7"
    assert record["supersedes"] == "dci1v6"
    assert record["supersedes_terminal_status"] == \
        "CLOSED_WITHOUT_CONFIRMATORY_GENERATION"
    assert set(record["superseded_terminal_statuses"]) == {
        "COMPOSED_HEADROOM_UNREACHABLE", "COMPOSED_HEADROOM_FAILURE"}
    # Every v7 change is executable and every one is checked. A listed change
    # the code does not make stops stage 1, because `assert_changes_realised`
    # is on the registration path.
    assert record["n_changes"] == record["n_checked"] == 13
    assert all(c["realised"] is True for c in record["changes"])
    assert [c["id"] for c in record["changes"]] == [
        f"V{i}" for i in range(1, 14)]


def test_the_withdrawal_is_a_registered_change_with_an_executable_check():
    """V1 is the change v7 exists for, and it is checked two ways: the two
    statuses are out of the terminal vocabulary, and no module can raise
    either."""
    by_id = {c.id: c for c in revision.CHANGES}
    assert by_id["V1"].section == "§13.14, §28.3"
    assert "WITHDRAWN" in by_id["V1"].what
    assert by_id["V1"].check()
    assert revision.assert_no_raise_path()["raise_paths"] == []
    # The boundary rule and the two recording stages are registered changes
    # with behavioural checks, not docstrings.
    for cid in ("V2", "V3", "V4", "V5", "V7", "V10", "V11", "V12", "V13"):
        assert by_id[cid].check is not None and by_id[cid].check(), cid


def test_no_threshold_moves_and_the_absence_is_checked():
    """v5 failed on C4 and on §13.14's band; v6 moved neither; v7 withdraws
    a criterion and moves no threshold either.

    A revision after a failed study is exactly where a bar gets lowered, so
    the absence is a registered change with a callable rather than a sentence
    in a document.
    """
    by_id = {c.id: c for c in revision.CHANGES}
    assert by_id["V8"].what == "NO THRESHOLD MOVES"
    assert by_id["V8"].check()
    assert C.SMALLEST_EFFECT_OF_INTEREST == 0.10
    assert C.CONTRAST_COMPRESSION_LEVEL == 1.0 - C.SMALLEST_EFFECT_OF_INTEREST


def test_the_estimand_layer_is_byte_identical_to_v6_except_where_named():
    by_id = {c.id: c for c in revision.CHANGES}
    assert by_id["V9"].check()
    assert "analysis/boundary.py" not in revision.ESTIMAND_LAYER
    assert "stages/support.py" in revision.ESTIMAND_LAYER
    # A6/A7 amend two functions of support.py and add to identification.py;
    # the exceptions are named, and the identification RULE is compared on
    # its derived sets rather than waved through.
    assert set(revision._ESTIMAND_LAYER_EXCLUDED_FUNCTIONS[
        "stages/support.py"]) == {"methodological_success", "evaluate_support"}
    assert "protocol/identification.py" in \
        revision._ESTIMAND_LAYER_OUTPUT_COMPARED
    assert revision._identification_rule_agrees_with_predecessor()


def test_a6_a7_a8_are_registered_changes_with_executable_checks():
    by_id = {c.id: c for c in revision.CHANGES}
    assert "A7" in by_id["V11"].section and by_id["V11"].check()
    assert "A6" in by_id["V12"].section and by_id["V12"].check()
    assert "A8" in by_id["V13"].section and by_id["V13"].check()
    # V8 still holds: the re-scoping moved no number.
    assert by_id["V8"].check()


def test_what_v7_deliberately_does_not_change_is_named():
    sections = {s for s, _ in revision.UNCHANGED}
    assert {"§3.2", "§6.1", "§13.11", "§13.15, §28"} <= sections
    text = " ".join(w for _s, w in revision.UNCHANGED)
    assert "permanently withheld" in text          # L5
    assert "never pooled" in text                  # §6.1's firewall
    assert "m* frozen at Gate 2" in text           # A13 stands


def test_the_ledger_carries_all_five_classifications():
    ledger = reuse_ledger.build_ledger("..")
    assert set(ledger["classifications"]) == set(C.REUSE_CLASSIFICATIONS)
    assert ledger["no_v6_generation_in_a_v7_estimand"] is True
    assert "design fitting" in ledger["declaration"]
    assert "loosening" in ledger["declaration"]
    sources = {e["source"] for e in ledger["entries"]}
    assert "dci1/evidence/dci1v6/*/terminal_report.json" in sources
    assert "dci1/src/dci1v6" in sources


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
