"""K + L. The eighteen-stage lifecycle, and §34's execution block."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError
from dci1v6.engine import transitions
from dci1v6.engine.paths import STAGE_RECORD_FILES
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.stages.audit_prefreeze import (
    CHECKLIST, run_prefreeze_audit,
)


#: All nineteen, from the committed record. It was four.
CLOSED = set(decisions.DECISION_IDS)
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_the_stage_sequence_is_the_registered_nineteen():
    assert len(C.STAGE_SEQUENCE) == 19
    assert C.STAGE_SEQUENCE[0] == C.STAGE_REGISTERED
    assert C.STAGE_SEQUENCE[-1] == C.STAGE_FINAL_REPORT
    for inserted in (C.STAGE_GATE2_5, C.STAGE_GATE2_75, C.STAGE_GATE3A,
                     C.STAGE_GATE3B, C.STAGE_GATE3C,
                     C.STAGE_PREFREEZE_AUDIT):
        assert inserted in C.STAGE_SEQUENCE


def test_the_probe_sits_between_gate_2_5_and_gate_3a():
    """Its placement is the whole point of it.

    At this position no reference exists --- Gate 3B has not run and the slot
    map is empty --- so composed headroom is measured *before* selection
    rather than after it, and reference selection stays interaction-blind
    because there is nothing yet to be blind to.
    """
    order = list(C.STAGE_SEQUENCE)
    assert order.index(C.STAGE_GATE2_75) == order.index(C.STAGE_GATE2_5) + 1
    assert order.index(C.STAGE_GATE3A) == order.index(C.STAGE_GATE2_75) + 1
    assert C.STAGE_GATE2_75 in C.GENERATION_STAGES


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


def test_protocol_registered_depends_on_every_decision_and_all_are_closed():
    """Stage 1 needs all nineteen, and all nineteen are taken."""
    assert set(decisions.closed_decisions()) == set(decisions.DECISION_IDS)
    assert decisions.decisions_blocking_stage(C.STAGE_REGISTERED) == ()
    transitions.assert_decisions_permit(C.STAGE_REGISTERED)


def test_every_stage_is_permitted_now_and_refuses_again_if_one_reopens():
    """The guard is still a guard.

    Every stage passes because every decision it depends on is closed --- and
    reopening one puts its own stages back behind the refusal, with stage 1
    behind it too, because stage 1 depends on all nineteen.
    """
    for stage in (C.STAGE_REGISTERED, C.STAGE_REGIME, C.STAGE_GATE2,
                  C.STAGE_QUALIFIED, C.STAGE_GATE3A, C.STAGE_GATE3C,
                  C.STAGE_UNMASKED_ANALYSIS):
        transitions.assert_decisions_permit(stage)

    held = decisions.DECISIONS["D17"]
    try:
        decisions.DECISIONS["D17"] = dataclasses.replace(
            held, value=decisions.UNRESOLVED)
        # D17 blocks stage 1 and Gate 2, and nothing else.
        for stage in (C.STAGE_REGISTERED, C.STAGE_GATE2):
            with pytest.raises(decisions.DecisionOpenError):
                transitions.assert_decisions_permit(stage)
        for stage in (C.STAGE_QUALIFIED, C.STAGE_GATE3A, C.STAGE_GATE3C):
            transitions.assert_decisions_permit(stage)
    finally:
        decisions.DECISIONS["D17"] = held


def test_a_stage_with_no_blocking_decision_is_permitted():
    transitions.assert_decisions_permit(C.STAGE_GATE2_5)
    transitions.assert_decisions_permit(C.STAGE_GATE3B)


def test_closing_a_decision_unblocks_only_its_own_stages(restore_decisions):
    """Reopened, then re-closed at the branch nobody took.

    D17's stages come back the moment it has any value, and the value it has
    here is the standing proposal the researcher declined --- so the branch
    stays executed rather than merely present.
    """
    restore_decisions.override_for_testing("D17", "no_floor")
    assert "D17" not in decisions.decisions_blocking_stage(C.STAGE_GATE2)
    assert decisions.value_of("D17") == "no_floor"


def test_the_decision_registry_is_v5s_nineteen_plus_v6s_eight():
    assert len(decisions.DECISIONS) == 27
    assert decisions.DECISION_IDS == tuple(f"D{i}" for i in range(27))
    assert decisions.V5_DECISION_IDS == tuple(f"D{i}" for i in range(19))
    assert decisions.V6_DECISION_IDS == (
        "D19", "D20", "D21", "D22", "D23", "D24", "D25", "D26")
    # D19-D24 are the six open researcher decisions of
    # `dci1/reports/dci1v6/READINESS.md` §5, and each names the memo's own
    # identifier so the two documents cannot drift apart.
    assert decisions.READINESS_MEMO_IDS == {
        "D19": "R1", "D20": "R2", "D21": "R3", "D22": "R4", "D23": "R5",
        "D24": "R6"}


def test_the_committed_record_closes_every_decision_with_its_evidence():
    """The committed state, read from the real path the fixture cannot reach.

    ``tests_v6/conftest.py`` monkeypatches ``RECORD_PATH`` to a fixture so the
    suite can exercise the open branches at all. This reads the path the
    module is actually born with. What is asserted is the **shape §34
    requires** --- one entry per decision, each with a value the register
    admits, evidence, an author and a date --- and not any particular value:
    a test that pinned the values would make the researcher's decisions an
    expectation of the code.
    """
    real = REPO_ROOT / decisions.RECORD_RELPATH
    assert real.exists(), (
        f"{decisions.RECORD_RELPATH} is missing. v6 is adopted and its "
        "closures live there; without it every dependent path refuses")
    recorded = {e["id"]: e for e in decisions.recorded_closures(real)}
    assert set(recorded) == set(decisions.DECISION_IDS)
    for entry in recorded.values():
        assert entry["evidence"].strip()
        assert entry["decided_by"].strip()
        assert entry["decided_on"].strip()
    # v5's nineteen are carried, and a carried closure names where it came
    # from --- carrying is a researcher act, not a transcription.
    for did in decisions.V5_DECISION_IDS:
        origin = recorded[did].get("carried_from") or {}
        assert origin.get("study") == "dci1v5"
        assert origin.get("record", "").endswith("researcher_decisions.json")
    for did in decisions.V6_DECISION_IDS:
        assert "carried_from" not in recorded[did]
    assert decisions.record_hash(real)


def test_the_adoption_guard_reads_what_each_document_says_about_itself(
        tmp_path):
    """Blocker 3 of READINESS.md, as an executable refusal --- **restated**.

    A missing document already refuses. A complete DRAFT is the thing that
    could be mistaken for a registration by being present, so each governed
    document declares its own status and ``assert_documents_adopted`` reads
    it. Both are now `ADOPTED`, so what this pins is the guard's mechanism on
    a root where they are not: a missing document and a document declaring
    itself a draft must refuse on the same terms, and ``document_hashes`` must
    refuse the same two files for the same reason --- before that was true,
    `plan_registration` could report `can_register` while neither document was
    written.
    """
    import json as _json
    import shutil

    from dci1v6 import PREREGISTRATION, REFERENCE_DESIGN_SPEC
    from dci1v6.protocol.manifest import (Blocker, assert_documents_adopted,
                                          document_hashes)

    bound = document_hashes(REPO_ROOT)
    assert set(bound) == {"protocol_hash", "reference_design_spec_hash"}
    assert assert_documents_adopted(REPO_ROOT)["adopted"] is True

    # A root with no documents at all.
    assert assert_documents_adopted(tmp_path)["adopted"] is False
    with pytest.raises(Blocker) as excinfo:
        document_hashes(tmp_path)
    assert "DCI1_preregistration_v6.md" in str(excinfo.value)

    # A root whose documents are present, complete, and declare themselves
    # drafts. Hashable, and still refused.
    draft = tmp_path / "draft"
    for relpath in (PREREGISTRATION, REFERENCE_DESIGN_SPEC):
        target = draft / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / relpath, target)
    prereg = draft / PREREGISTRATION
    prereg.write_text(prereg.read_text().replace(
        "    status: ADOPTED", "    status: DRAFT_NOT_ADOPTED", 1))
    spec_path = draft / REFERENCE_DESIGN_SPEC
    spec = _json.loads(spec_path.read_text())
    spec["_status"] = "DRAFT_NOT_ADOPTED"
    spec_path.write_text(_json.dumps(spec))
    assert set(document_hashes(draft)) == {"protocol_hash",
                                           "reference_design_spec_hash"}
    verdict = assert_documents_adopted(draft)
    assert verdict["adopted"] is False
    assert {f["declared"] for f in verdict["findings"]} == {
        "DRAFT_NOT_ADOPTED"}


def test_the_synthetic_walk_runs_the_values_the_study_registered():
    """The harness supplies D19-D26 because the fixture record is v5's and
    carries none of them --- and **which** values it supplies matters.

    Before adoption they were arbitrary: ``D26 = 0.05`` was a number the code
    path needed. After adoption a harness keeping its own literals would make
    the 19-stage walk and the execution-path audit exercise a study nobody
    registered. So the recorded value wins wherever there is one, and the
    fallback survives only where there is not.
    """
    from tests_v6 import synthetic_lifecycle as SL

    recorded = {e["id"]: e["value"] for e in decisions.recorded_closures(
        REPO_ROOT / decisions.RECORD_RELPATH)}
    harness = SL._harness_values()
    assert set(harness) == set(decisions.V6_DECISION_IDS)
    for key, value in harness.items():
        assert value == recorded.get(key, SL._HARNESS_FALLBACK[key])
    # And the fixture the suite runs against still leaves them open, or the
    # refusal branches would not be reachable in any test.
    fixture = {e["id"] for e in decisions.recorded_closures(SL.FIXTURE_RECORD)}
    assert not (fixture & set(decisions.V6_DECISION_IDS))


def test_a_recorded_closure_carries_its_evidence_and_survives_a_reopen():
    """§34 binds the decision AND its evidence, durably.

    The record under test is the fixture --- v5's own, carried into
    ``tests_v6`` --- because the suite runs against it rather than against the
    researcher's own record, so that the open branches stay reachable. What it
    covers is the mechanism: a closure read from a file carries its evidence,
    its author and its date, and a reopen restores that state rather than a
    blank registry. v6's own D19-D26 are deliberately absent from the fixture.
    """
    recorded = {e["id"]: e for e in decisions.recorded_closures()}
    assert set(recorded) == set(decisions.V5_DECISION_IDS)
    assert not set(recorded) & set(decisions.V6_DECISION_IDS)
    for entry in recorded.values():
        assert entry["evidence"] and entry["decided_by"] and \
            entry["decided_on"]
    assert decisions.record_hash()
    payload = decisions.registration_payload()
    assert payload["record"]["hash"] == decisions.record_hash()
    assert payload["record"]["path"] == decisions.RECORD_RELPATH
    # Every decision that offers a choice records the branch nobody took, so
    # a reader can see what was declined as well as what was taken. The
    # decisions absent here are the ones that offer no coded branch at all:
    # D26 is a number, and the 2026-08-26 red team converted twelve v5-era
    # entries plus D21 into acceptances because their alternatives had no
    # implementation, so a closure there would have registered a study the
    # code cannot run. What each of them declined is not lost --- it moves to
    # `unimplemented_alternatives`, which `as_dict` carries.
    acceptances = {d for d in decisions.DECISION_IDS
                   if not decisions.DECISIONS[d].admissible_values}
    assert "D26" in acceptances and "D21" in acceptances
    assert set(payload["non_adopted_alternatives"]) == set(
        decisions.DECISION_IDS) - acceptances
    for did in acceptances - {"D26"}:
        assert decisions.DECISIONS[did].unimplemented_alternatives, did
    # The record hash covers the open-item resolutions too: U2 blocks the
    # manifest outright, and a hash that covered only half the file would let
    # its resolution change under a signature that did not move.
    assert payload["record"]["resolved_here"] == ["U2", "P1", "U4"]


def test_the_record_hash_moves_when_a_resolution_moves(tmp_path):
    import json

    base = json.loads(decisions.RECORD_PATH.read_text())
    one = tmp_path / "a.json"
    two = tmp_path / "b.json"
    one.write_text(json.dumps(base))
    two.write_text(json.dumps({**base, "open_items": []}))
    assert decisions.record_hash(one) != decisions.record_hash(two)


def test_a_decision_whose_value_needs_parameters_carries_them(
        restore_decisions):
    """§34 D17 is the case: `floor` alone is a rule with no rule in it."""
    spec = decisions.recorded_spec("D17")
    assert spec["quantity"] == "chance_compliance"
    assert spec["value"] == 0.50
    assert spec["semantics"] == "point_estimate_refuses_wilson_reported"
    assert spec["derivation"] and spec["decided_by"] and spec["decided_on"]
    # Most decisions need none, and that is not an error.
    assert decisions.recorded_spec("D5") is None


def test_the_record_and_a_closure_in_force_may_not_disagree(restore_decisions):
    """A change to a closed decision is a §32 amendment, not a file edit."""
    restore_decisions.override_for_testing("D18", "not_a_precondition")
    with pytest.raises(ProtocolError, match="amendment"):
        decisions.apply_recorded_closures()


def test_a_decision_cannot_be_closed_without_its_evidence(restore_decisions):
    """Every closure needs the value, the evidence, the author and the date.

    Run against a reopened D0, because D0 is closed now and ``close`` is
    write-once --- which is itself the last assertion here.
    """
    restore_decisions.DECISIONS["D0"] = dataclasses.replace(
        restore_decisions.DECISIONS["D0"], value=decisions.UNRESOLVED,
        evidence=None, decided_by=None, decided_on=None)
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
    """The guard that found the dead branches: `choice` refuses a table that
    omits an admissible value, so a decision offering a value the code has no
    behaviour for is a defect here and not a researcher error.

    D7 used to be the example. It is an **acceptance** since 2026-08-26 --- its
    0.85 and 0.95 had no implementation anywhere --- so the example is now a
    decision that really does select between coded branches.
    """
    assert decisions.DECISIONS["D20"].admissible_values
    with pytest.raises(ProtocolError) as excinfo:
        decisions.choice("D20", {"reserved_composed": "composed"},
                         where="test")
    assert "both branches" in str(excinfo.value)


def test_an_acceptance_still_refuses_its_dependent_call_while_open(
        restore_decisions):
    """An acceptance offers no branch, so `choice`'s completeness guard cannot
    protect it. What must still hold is that its dependent call refuses while
    it is open --- otherwise converting a decision to an acceptance would have
    quietly given its callers a default."""
    restore_decisions.reopen_all_for_testing()
    acceptances = [d for d in decisions.DECISION_IDS
                   if not decisions.DECISIONS[d].admissible_values
                   and decisions.DECISIONS[d].blocks_calls]
    assert "D21" in acceptances and "D26" in acceptances
    for did in acceptances:
        for call in decisions.DECISIONS[did].blocks_calls:
            assert did in decisions.decisions_blocking_call(call), (did, call)
            with pytest.raises(decisions.DecisionOpenError):
                decisions.assert_decisions_closed_for(call)


def test_the_prefreeze_audit_runs_fifteen_checks_and_no_decision_is_open():
    """The audit no longer fails for §34's reason.

    It can still fail for its own --- checks 1 to 15 read a replication's
    records, and this call has none --- and that is a different fact from
    "a decision nobody took". Only the decision half is asserted here.
    """
    audit = run_prefreeze_audit(repo_root=REPO_ROOT)
    assert len(CHECKLIST) == 15
    assert audit["n_checks"] == 15
    assert audit["n_open_decisions"] == 0
    assert audit["open_decisions"] == []


def test_the_audit_surfaces_every_unresolved_redteam_finding():
    """All five are surfaced; four block, and R5 is a permanent limitation.

    A finding blocks while **its registered mitigation is still open**, and
    the mitigation is a §34 decision. R5 has none --- §13.8 closes its second
    half and its first half is not closeable by a rule --- so treating its
    presence as a blocker would make ``can_freeze`` unsatisfiable however the
    study went, which is a gate that cannot pass rather than a hard one.
    """
    from dci1v6.stages.audit_prefreeze import UNRESOLVED_REDTEAM_FINDINGS

    audit = run_prefreeze_audit(repo_root=REPO_ROOT)
    assert set(UNRESOLVED_REDTEAM_FINDINGS) == {"R1", "R5", "R11", "R14",
                                                "R16"}
    # R1, R11, R14 and R16 were carried by D18, D16, D17 and D6, and the
    # researcher has taken all four: they stop blocking the freeze the moment
    # the decision they name is closed, which is what "the mitigation IS the
    # decision" means executably.
    assert set(audit["unresolved_redteam_findings"]) == set()
    # R5 is not resolved and never will be by a rule. It is an ACCEPTED
    # PERMANENT LIMITATION and it stays reported --- calling it resolved
    # because nothing blocks any more is the one move this distinction exists
    # to prevent.
    assert set(audit["permanent_limitations"]) == {"R5"}
    assert audit["permanent_limitations"]["R5"]["closeable_by_rule"] is False
    assert audit["permanent_limitations"]["R5"]["decision"] is None
    for finding in ("R1", "R11", "R14", "R16"):
        entry = UNRESOLVED_REDTEAM_FINDINGS[finding]
        assert entry["closeable_by_rule"] is True
        assert decisions.is_closed(entry["decision"])


def test_only_the_final_report_check_is_deferred():
    """§33 check 14 reads a table that does not exist at stage 12.

    Check 15 is **not** deferred. It scans the v5 artifact texts, which exist
    from stage 1; an earlier revision passed none and got UNRESOLVED forever,
    which is a check that never ran.
    """
    from dci1v6.stages.audit_prefreeze import DEFERRED_CHECKS

    audit = run_prefreeze_audit(repo_root=REPO_ROOT)
    assert DEFERRED_CHECKS == (14,)
    deferred = {c["n"] for c in audit["deferred_to_final_report"]}
    assert deferred == {14}
    assert all(c["verdict"] == "UNRESOLVED"
               for c in audit["deferred_to_final_report"])
    # And an unestablished check that is NOT deferred still blocks.
    assert any(c["n"] == 8 for c in audit["checklist"])


def test_check_15_has_a_producer_and_refuses_a_missing_v6_artifact():
    """§33 check 15 scans v6's artifact texts, and one of them is not written.

    v5's version of this test asserted the check passes over the real
    artifacts. **For v6 the correct behaviour is a refusal**: the check names
    `user-notes/DCI1_preregistration_v6.md`, it does not exist, and a text
    check that silently scans nothing is not a check. The refusal is blocker 3
    reaching one more place.

    What the test still covers is that check 15 has a *producer* --- the
    declaration in `reuse_ledger.ARTIFACT_TEXT_GLOBS`, not a caller's
    argument, which is how an earlier revision came to report UNRESOLVED at
    every stage that ran it.
    """
    from dci1v6.protocol import reuse_ledger

    assert reuse_ledger.ARTIFACT_TEXT_GLOBS
    # The preregistration now exists as a draft, so the collector finds it
    # and the refusal has to be provoked on a tree that does not.
    assert "DCI1_preregistration_v6.md" in "".join(
        reuse_ledger.collect_artifact_texts(REPO_ROOT))
    import tempfile

    with pytest.raises(ProtocolError) as excinfo:
        reuse_ledger.collect_artifact_texts(Path(tempfile.mkdtemp()))
    assert "DCI1_preregistration_v6.md" in str(excinfo.value)

    # And over the texts that DO exist, the phrase scan runs and is clean.
    existing = {}
    for pattern in reuse_ledger.ARTIFACT_TEXT_GLOBS:
        if "*" not in pattern:
            continue
        for path in sorted(REPO_ROOT.glob(pattern)):
            existing[str(path.relative_to(REPO_ROOT))] = path.read_text()
    assert existing, "no v6 report text to scan"
    result = reuse_ledger.assert_no_validation_language(existing)
    assert result["offences"] == 0


def test_a_named_artifact_that_is_absent_is_a_refusal_not_an_empty_scan():
    from dci1v4.errors import ProtocolError
    from dci1v6.protocol.reuse_ledger import collect_artifact_texts

    with pytest.raises(ProtocolError, match="scans nothing is not a check"):
        collect_artifact_texts("/nonexistent-repo-root")


def test_one_failing_check_is_enough_to_block_the_freeze():
    audit = run_prefreeze_audit(
        repo_root=REPO_ROOT,
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
    audit = run_prefreeze_audit(repo_root=REPO_ROOT)
    unresolved = [c for c in audit["checklist"] if c["verdict"] == "UNRESOLVED"]
    assert unresolved
    assert all(c["n"] in (8, 14, 15) for c in unresolved)
    assert audit["can_freeze"] is False
    assert {c["n"] for c in audit["failures"]} >= {8, 15}


def test_the_two_status_vocabularies_are_disjoint():
    """A15: a readiness verdict and a §28 terminal outcome are not the same
    kind of statement, and the separation is structural.

    ``REGISTRATION_INCOMPLETE`` was in ``TERMINAL_STATUSES`` until 2026-08-26,
    which made every entry ``signing_blockers`` can report --- all of them
    outstanding *researcher* work --- irreversible for whichever replication
    discovered it. What §28 says about a gate's verdict is untouched:
    ``PREFREEZE_AUDIT_FAILURE`` is where it was and is as terminal as it was.
    """
    assert "REGISTRATION_INCOMPLETE" in C.READINESS_REFUSAL_STATUSES
    assert "REGISTRATION_INCOMPLETE" not in C.TERMINAL_STATUSES
    assert "PREFREEZE_AUDIT_FAILURE" in C.TERMINAL_STATUSES
    assert not set(C.READINESS_REFUSAL_STATUSES) & set(C.TERMINAL_STATUSES)


def test_the_new_identification_statuses_are_registered():
    for status in ("REFERENCE_SUPPORT_NOT_IDENTIFIED", "LOCAL_TIER_DISAGREE",
                   "INTERACTION_ESTIMATE_DRIFTED",
                   "REFERENCE_ROLE_NOT_MATCHED", "REFERENCE_POOL_SAME_FORM",
                   "NEAR_FORM_ARM_NOT_AVAILABLE",
                   "OPERATING_POINT_AT_GRID_BOUNDARY"):
        assert status in C.IDENTIFICATION_STATUSES
        assert status in C.NEW_IDENTIFICATION_STATUSES


def test_the_freeze_record_refuses_an_unexplained_empty_field():
    from dci1v6.stages import freeze

    record = {f: "x" for f in freeze.REQUIRED_FIELDS}
    record.update(build := freeze.build_freeze_record())
    record.update(admitted_arms=["base"], derived_cell_count=5,
                  open_decisions=[], core_references=[])
    with pytest.raises(ProtocolError):
        freeze.assert_freeze_complete(record, identification_statuses=[])
    freeze.assert_freeze_complete(
        record, identification_statuses=["REFERENCE_SUPPORT_NOT_IDENTIFIED"])
    assert build["backups_never_substituted"] is True


def test_the_freeze_refuses_if_a_decision_reopens():
    """§34's guard on the freeze, exercised by reopening one decision.

    Every decision is closed, so the guard cannot be shown by the repository's
    own state any more --- and a guard nothing exercises is a guard that
    quietly stops working.
    """
    from dci1v6.stages import freeze

    held = decisions.DECISIONS["D12"]
    decisions.DECISIONS["D12"] = dataclasses.replace(
        held, value=decisions.UNRESOLVED)
    try:
        _assert_freeze_refuses_for_section_34(freeze)
    finally:
        decisions.DECISIONS["D12"] = held


def _assert_freeze_refuses_for_section_34(freeze):
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
