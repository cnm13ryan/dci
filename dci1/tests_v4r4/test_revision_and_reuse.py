"""The revision boundary: what v4r4 changed, and what it may not touch.

v4r4 exists because v4r3's Gate 1 refused. That makes two classes of mistake
available which no amount of care in the new rule would catch, and this file
exists to make both mechanically impossible:

* **rewriting the older study.** v4r3's records, its failed Gate-1 decision and
  its reviewer evidence must stay exactly as they are, stay readable, and stay
  labelled as v4r3's. A closure record is a statement *about* a study; it is
  never an edit *to* one.
* **letting the older study satisfy the newer one.** v4r3's signed QUALIFIED,
  GATE_0_APPARATUS and REGIME_SCREEN records sit on disk beside v4r4's. None
  may serve as a v4r4 predecessor, and the guard has to be at the point of
  reading rather than in the shape of a path.

The third theme is reuse. Generations *are* carried, which is right --- the
model, its revision, the decoding and every prompt are unchanged --- and the
tests below check that the conditions permitting that are verified rather than
assumed, and that changing any one of them stops the carry.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODEL_KEYS

from dci1v4r4 import (
    FOREIGN_STUDY_PREFIXES, STUDY_ID, SUPERSEDES, SUPERSEDES_TERMINAL_STATUS,
)
from dci1v4r4.engine.context import foreign_roots, synthetic_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import (
    assert_own_study, assert_predecessor_passed, assert_transition_legal,
    read_stage_record, write_stage_record,
)
from dci1v4r4.protocol import constants as C
from dci1v4r4.protocol.revision import (
    DIFFERENCES, INHERITED_UNCHANGED, PROTOCOL_DOCUMENTS, document_hashes,
    protocol_hash, revision_record,
)
from dci1v4r4.stages.gate1 import gate1_payload
from dci1v4r4.stages.reuse import (
    CARRYING_CLASSES, REUSE_CLASSES, REUSE_INVARIANTS, LedgerEntry,
    assert_reusable, build_ledger, verifier_semantics_agree,
)
from dci1v4r4.stages.specification import (
    DIRECTION_LEXICON, DOCUMENTED_CONSTRUCTIONS, classify_wording,
    unmatched_wordings,
)
from dci1v4r4.verifiers import verifier_source_hash
from dci1v4r4.verifiers.boundary import instrument_population
from dci1v4r4.verifiers.constraints import FAMILIES, REMOVED_IN_V4R4

DCI1 = Path(__file__).resolve().parents[1]
SUPERSEDED_EVIDENCE = DCI1 / "evidence" / "dci1v4r3"
SUPERSEDED_REPORTS = DCI1 / "reports" / "dci1v4r3"
MODEL = "gemma-3n-e2b-it"


@pytest.fixture()
def tree(tmp_path):
    from dci1v4.engine.signing import create_signing_key

    context = synthetic_context(tmp_path)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    return model_tree(context, MODEL)


def _payload(stage: str, outcome: str = "PASS") -> dict:
    return {"stage": stage, "outcome": outcome,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[stage],
            "model_key": MODEL}


# --------------------------------------------------- 1: v4r3 stays as it is
def test_the_superseded_gate_1_failure_is_preserved_and_says_it_failed():
    """Required failure: v4r3's Gate-1 record must never read as a pass."""
    path = SUPERSEDED_REPORTS / "gate1_decision.json"
    if not path.exists():                                # pragma: no cover
        pytest.skip("the superseded study's reports are not in this tree")
    decision = json.loads(path.read_text())
    assert decision["status_written_by_the_gate"] == \
        "MEASUREMENT_EVIDENCE_INSUFFICIENT"
    assert decision["decision"] == "GATE_1_BLOCKED_MEASUREMENT"
    assert decision["measurement_basis"] == "human_validation_unavailable"
    # The rule it was decided under, verbatim, so that a reader of the v4r4
    # record can see it was a different rule and not a different reading.
    assert "§10.3 or §10.4" in decision["registered_rule"]
    assert SUPERSEDES_TERMINAL_STATUS == \
        decision["status_written_by_the_gate"]


def test_the_closure_record_states_the_terminal_stage_and_edits_nothing():
    path = SUPERSEDED_REPORTS / "closure.json"
    if not path.exists():                                # pragma: no cover
        pytest.skip("the closure record has not been written in this tree")
    closure = json.loads(path.read_text())
    assert closure["status"] == "CLOSED"
    assert closure["closed_at_stage"] == "GATE_1_MEASUREMENT"
    assert closure["terminal_status"] == "MEASUREMENT_EVIDENCE_INSUFFICIENT"
    assert closure["every_downstream_artifact_absent"] is True
    # It says what it does not say. That sentence is load-bearing.
    assert any("did not" in line
               for line in closure["what_this_record_does_not_say"])


# -------------------------------- 2: there is no v4r3 Gate-1 PASS to inherit
def test_no_gate_1_pass_exists_anywhere_in_the_superseded_study():
    if not SUPERSEDED_EVIDENCE.exists():                 # pragma: no cover
        pytest.skip("the superseded study's evidence is not in this tree")
    assert not list(SUPERSEDED_EVIDENCE.rglob("gate1_measurement.json"))
    for name in ("gate2_regime.json", "gate3_references.json",
                 "gate4_composed.json", "gate5_freeze.json",
                 "confirmatory_manifest.json", "masked_result.json",
                 "unmask_record.json", "unmasked_result.json"):
        assert not list(SUPERSEDED_EVIDENCE.rglob(name)), name


# ------------------------------------------ 12: v4r3 cannot satisfy v4r4
def test_a_record_from_the_superseded_study_is_refused_where_it_is_read(tree):
    foreign = {**_payload(C.STAGE_QUALIFIED), "study_id": "dci1v4r3"}
    with pytest.raises(IntegrityError) as refusal:
        assert_own_study(tree, C.STAGE_QUALIFIED, foreign)
    assert "dci1v4r3" in str(refusal.value)
    assert tree.context.study_id in str(refusal.value)


def test_a_record_with_no_study_id_is_refused(tree):
    with pytest.raises(IntegrityError):
        assert_own_study(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))


def test_writing_a_record_stamped_with_another_study_is_refused(tree):
    with pytest.raises(IntegrityError):
        write_stage_record(tree, C.STAGE_QUALIFIED,
                           {**_payload(C.STAGE_QUALIFIED),
                            "study_id": "dci1v4r3"})


def test_the_superseded_trees_are_foreign_roots():
    assert "dci1v4r3" in FOREIGN_STUDY_PREFIXES
    names = {p.name for p in foreign_roots()}
    assert "dci1v4r3" in names
    assert STUDY_ID not in names


# ---------------------------------------- 11: round-trip and signature
def test_a_stage_record_survives_serialisation_and_signature_round_trip(tree):
    written = write_stage_record(
        tree, C.STAGE_QUALIFIED,
        {**_payload(C.STAGE_QUALIFIED),
         "table": {512: [0.1, None], 1024: {"nested": True}}})
    payload = read_stage_record(tree, C.STAGE_QUALIFIED)
    on_disk = json.loads(written.read_text())
    assert payload == on_disk["payload"]
    assert payload["study_id"] == tree.context.study_id
    # Integer keys are the defect that made a v4r3 record unverifiable: JSON
    # has no integer keys, so what is signed has to be the wire form.
    assert set(payload["table"]) == {"512", "1024"}


def test_a_tampered_record_fails_verification(tree):
    written = write_stage_record(tree, C.STAGE_QUALIFIED,
                                 _payload(C.STAGE_QUALIFIED))
    record = json.loads(written.read_text())
    record["payload"]["outcome"] = "PASS "
    written.write_text(json.dumps(record))
    with pytest.raises(Exception):
        read_stage_record(tree, C.STAGE_QUALIFIED)


# ------------------------------- 13: Gate 2 needs a v4r4 Gate-1 PASS
def test_gate_2_cannot_run_without_a_v4r4_gate_1_pass(tree):
    for stage in (C.STAGE_QUALIFIED, C.STAGE_GATE0, C.STAGE_REGIME):
        write_stage_record(tree, stage, _payload(stage))
    with pytest.raises(IntegrityError) as refusal:
        assert_transition_legal(tree, C.STAGE_GATE2)
    assert C.STAGE_GATE1 in str(refusal.value)

    # A Gate 1 that recorded anything but PASS still refuses.
    write_stage_record(tree, C.STAGE_GATE1,
                       _payload(C.STAGE_GATE1, outcome="REFUSED"))
    with pytest.raises(IntegrityError):
        assert_predecessor_passed(tree, C.STAGE_GATE2)


# ----------------------- 6: directional wordings must expose their operator
def test_a_wording_that_states_only_a_target_quantity_is_a_blocker():
    """The v4r3 blocker, by name, against a family that survives."""
    for text in ("Give 20 percent of words letter a.",
                 "Make 20 percent of words carry doubled letters.",
                 "Your answer: 20 words with letter a."):
        verdict = classify_wording("CL7", 20, 3, text)
        assert verdict["classification"] == "genuinely_ambiguous"
        assert verdict["finding"] == "direction_not_named"


def test_a_wording_that_names_the_wrong_direction_is_a_blocker():
    verdict = classify_wording("CL7", 20, 0, "At most 20 words may have a.")
    assert verdict["classification"] == "requires_correction"
    assert verdict["finding"] == "names_the_wrong_direction"


def test_a_documented_construction_is_admissible_only_for_its_operator():
    lower = classify_wording("CL7", 20, 3,
                             "Your answer needs 20 words with letter a.")
    assert lower["classification"] == "unambiguous_documented"
    assert lower["construction"] == "requirement_verb"
    exact = classify_wording("CX1", 4, 0,
                             "Your answer must contain thus 4 times.")
    assert exact["classification"] == "requires_correction"
    assert exact["finding"] == "construction_not_admissible_for_this_operator"


def test_every_documented_construction_records_its_derivation():
    for name, entry in DOCUMENTED_CONSTRUCTIONS.items():
        assert entry["derivation"], name
        assert entry["entails"] in DIRECTION_LEXICON, name
        assert set(entry["admissible_for"]) <= set(DIRECTION_LEXICON), name
        # A construction admissible for an operator it does not entail would
        # be a wording licensed to mean something else.
        assert set(entry["admissible_for"]) == {entry["entails"]}, name


def test_the_invariant_resolves_every_wording_in_the_final_population():
    assert unmatched_wordings() == []


# --------------------------- 10: reuse requires the invariants to be checked
def test_a_carried_entry_without_a_finding_for_every_invariant_is_refused():
    for classification in CARRYING_CLASSES:
        entry = LedgerEntry(
            artifact="x", classification=classification,
            source_path="p", source_hash="h", reason="r",
            satisfies="a v4r4 criterion",
            invariants={name: True for name in REUSE_INVARIANTS[:-1]})
        with pytest.raises(ProtocolError) as refusal:
            assert_reusable(entry)
        assert REUSE_INVARIANTS[-1] in str(refusal.value)


def test_a_carried_entry_whose_invariant_fails_is_refused():
    entry = LedgerEntry(
        artifact="x", classification="RECOMPUTED_FROM_EXISTING_RAW_DATA",
        source_path="p", source_hash="h", reason="r",
        satisfies="a v4r4 criterion",
        invariants={**{name: True for name in REUSE_INVARIANTS},
                    "model_facing_prompt": {"holds": False}})
    with pytest.raises(ProtocolError) as refusal:
        assert_reusable(entry)
    assert "model_facing_prompt" in str(refusal.value)


def test_a_carried_entry_must_name_the_criterion_it_satisfies():
    with pytest.raises(ProtocolError):
        LedgerEntry(artifact="x",
                    classification="RECOMPUTED_FROM_EXISTING_RAW_DATA",
                    source_path="p", source_hash="h", reason="r")


def test_a_historical_entry_may_not_claim_to_satisfy_anything():
    with pytest.raises(ProtocolError):
        LedgerEntry(artifact="x", classification="HISTORICAL_ONLY",
                    source_path="p", source_hash="h", reason="r",
                    satisfies="§18 stage 3")


def test_an_unregistered_classification_is_refused():
    with pytest.raises(ProtocolError):
        LedgerEntry(artifact="x", classification="PROBABLY_FINE",
                    source_path="p", source_hash="h", reason="r")
    assert set(CARRYING_CLASSES) <= set(REUSE_CLASSES)


def test_the_two_revisions_verifiers_agree_on_every_carried_instrument():
    """The check the ledger rests on, run for itself.

    §10.6 forbids carrying a stale hash forward because behaviour *looks*
    unchanged. This measures the behaviour: 524 instruments x 164 frozen
    cases, both packages' compliance predicates, verdict against verdict.
    """
    finding = verifier_semantics_agree()
    assert finding["holds"] is True
    assert finding["disagreements"] == []
    assert finding["instruments_not_declared_in_v4r3"] == []
    assert finding["verdicts_compared"] == 164 * len(instrument_population())


def test_a_ledger_of_only_historical_entries_says_nothing_was_regenerated():
    ledger = build_ledger([
        LedgerEntry(artifact="x", classification="HISTORICAL_ONLY",
                    source_path="p", source_hash="h", reason="r")])
    assert ledger["counts"]["INVALIDATED_AND_REGENERATED"] == 0
    assert ledger["nothing_is_regenerated_because"]


# ------------------------------------ 14: the historical artifacts are placed
def test_the_reviewer_artifacts_remain_readable_and_are_labelled_diagnostic():
    wanted = {
        "section_10_4R2_outcome.json": "FAIL",
        "section_10_4R_outcome.json": None,
        "validator_diagnosis.json": None,
        "defect_sensitivity.json": None,
    }
    for name, outcome in wanted.items():
        path = SUPERSEDED_REPORTS / name
        if not path.exists():                            # pragma: no cover
            pytest.skip(f"{name} is not in this tree")
        payload = json.loads(path.read_text())
        assert payload
        if outcome is not None:
            assert payload["outcome"] == outcome


def test_no_v4r4_gate_reads_a_reviewer_quantity():
    """The whole point, asserted at the rule rather than at a call site."""
    import inspect

    from dci1v4r4.stages import gate1

    source = inspect.getsource(gate1.gate1_payload)
    for forbidden in ("human_agreement", "autorater", "wilson",
                      "agreement_rate", "judge"):
        assert forbidden not in source.lower(), forbidden
    # It is carried, and it is carried opaquely.
    assert "supplementary_diagnostics" in source


# ------------------------------------------------- the revision boundary
def test_every_difference_from_the_superseded_revision_is_enumerated():
    ids = [entry["id"] for entry in DIFFERENCES]
    assert ids == sorted(set(ids))
    for entry in DIFFERENCES:
        for field in ("area", "v4r3", "v4r4", "why", "consequence"):
            assert entry[field], (entry["id"], field)
    assert INHERITED_UNCHANGED
    assert SUPERSEDES == "dci1v4r3"


def test_the_protocol_hash_moves_when_a_protocol_document_moves(tmp_path,
                                                                monkeypatch):
    first = protocol_hash()
    record = revision_record()
    assert first == protocol_hash(record)
    moved = {**record, "documents": {**record["documents"],
                                     PROTOCOL_DOCUMENTS[0]: "0" * 64}}
    assert protocol_hash(moved) != first


def test_the_removed_families_are_recorded_with_their_finding():
    assert set(REMOVED_IN_V4R4) == {"CP4", "CP7"}
    assert not set(REMOVED_IN_V4R4) & set(FAMILIES)
    for kind, entry in REMOVED_IN_V4R4.items():
        assert entry["finding"] == "specification_ambiguity"
        assert "target" in entry["why"]
        assert "§10.2" in entry["rule"]


def test_the_population_and_the_verifier_hash_both_moved():
    from dci1v4r3.verifiers import verifier_source_hash as superseded_hash
    from dci1v4r3.verifiers.boundary import (
        instrument_population as superseded_population,
    )
    assert len(instrument_population()) == 524
    assert len(superseded_population()) == 584
    assert verifier_source_hash() != superseded_hash()


def test_gate_1_refuses_to_write_a_reviewer_basis_before_reading_evidence():
    """No evidence is supplied at all: the refusal must precede it."""
    for basis in C.MEASUREMENT_BASES_REFUSED:
        with pytest.raises(ProtocolError):
            gate1_payload(evidence={}, specification_evidence={},
                          provenance={}, measurement_basis=basis)


# ----------------------------------- the lifecycle machinery, as it stands
def _artifact(name: str):
    path = DCI1 / "reports" / "dci1v4r4" / name
    if not path.exists():                                # pragma: no cover
        pytest.skip(f"{name} has not been produced in this tree")
    return json.loads(path.read_text())


def test_the_lifecycle_integrity_report_passes_and_licenses_gate_2():
    report = _artifact("lifecycle_integrity.json")
    assert report["problems"] == []
    assert report["passed"] is True
    assert report["integer_key_canonicalisation"]["holds"] is True
    assert report["historical_evidence_untouched"]["holds"] is True
    assert report["foreign_record_refused"]["holds"] is True
    assert report["gate_2_may_run"] is True
    for model_key, entry in report["models"].items():
        assert entry["furthest_stage"] == C.STAGE_GATE1, model_key
        for stage, record in entry["records"].items():
            assert record["study_id"] == "dci1v4r4", (model_key, stage)
            assert record["round_trips"], (model_key, stage)
            assert record["reader_copy_matches"], (model_key, stage)
            assert record["write_once_enforced"], (model_key, stage)
            assert record["producing_commit"] or stage != C.STAGE_QUALIFIED


def test_every_gate_1_record_carries_the_deterministic_basis_and_its_scope():
    report = _artifact("gate1_decision.json")
    assert report["outcome"] == "PASS"
    assert report["measurement_basis"] == C.MEASUREMENT_BASIS
    assert report["measurement_basis"] != "human_validated"
    assert report["scope_sentence"] == C.SCOPE_SENTENCE
    assert report["instruments"] == 524
    assert report["canonical_verifier_hash"] == verifier_source_hash()
    # The reviewer evidence travels, labelled, and keeps its own outcomes.
    diagnostics = report["supplementary_diagnostics"]
    assert "SUPPLEMENTARY" in diagnostics["role"]
    assert "FAILED" in diagnostics["section_10_4R2"]["what_it_is"]
    assert "not independent validation" in \
        diagnostics["section_10_3"]["what_it_is"]


def test_the_reuse_ledger_carries_only_what_the_invariants_allow():
    ledger = _artifact("evidence_reuse_ledger.json")
    assert ledger["counts"]["INVALIDATED_AND_REGENERATED"] == 0
    assert ledger["invariant_findings"]["verifier_semantics"]["holds"]
    assert ledger["invariant_findings"]["model_facing_prompt"]["holds"]
    for entry in ledger["entries"]:
        assert entry["classification"] in REUSE_CLASSES
        if entry["classification"] in CARRYING_CLASSES:
            assert entry["satisfies"]
            assert set(entry["invariants"]) == set(REUSE_INVARIANTS)


def test_the_coverage_report_holds_on_every_replication():
    coverage = _artifact("coverage.json")
    assert coverage["every_model_passes"] is True
    assert coverage["identification_status"] is None
    for model_key, entry in coverage["models"].items():
        assert entry["study_id"] == "dci1v4r4", model_key
        decisive = {k: v["met"] for k, v in entry["coverage"]["conditions"].items()
                    if k != "C7_class_matched"}
        assert all(decisive.values()), (model_key, decisive)
        # C7 is not terminal, and the report says which it is either way.
        assert "terminal" in entry["coverage"]["conditions"]["C7_class_matched"]


def test_the_cp4_cp7_decision_read_no_composed_outcome():
    decision = _artifact("cp4_cp7_analysis.json")
    assert decision["reads_no_composed_outcome"] is True
    assert decision["decision"] == "REMOVE_CP4_AND_CP7"
    assert decision["every_coverage_condition_holds_without_them"] is True
    assert decision["no_condition_changed_on_any_model"] is True
    # The fragility it found is inherited, not introduced, and it says so.
    assert decision["leave_one_family_out_is_unchanged_by_the_removal"] is True


def test_the_register_amendment_is_confined_to_the_register():
    """B6 and B7 were entered after Gate 1 sealed the protocol hash.

    That is legitimate --- they were taken before Gate 2 and neither changes a
    rule Gate 1 applied --- but it must not be silent. The amendment record
    resolves the delta, and this asserts the two properties that make it an
    amendment rather than a re-seal: only the decisions register moved, and no
    measurement hash moved with it.
    """
    amendment = _artifact("register_amendment.json")
    assert amendment["problems"] == []
    assert amendment["passed"] is True
    assert amendment["protocol_hash"]["moved"] is True
    assert list(amendment["documents"]["moved"]) == ["dci1/DECISIONS_V4R4.md"]
    assert amendment["measurement_hashes"]["moved"] == {}
    assert amendment["measurement_hashes"]["holds"] is True
    # The three documents that carry the science are untouched, and the
    # register's live bytes are what the amendment says they are.
    now = document_hashes()
    for relative in amendment["documents"]["unchanged"]:
        sealed = amendment["sealed_by_gate1"][
            "gemma-3n-e2b-it"]["documents"][relative]
        assert now[relative] == sealed, relative
    assert now["dci1/DECISIONS_V4R4.md"] == \
        amendment["documents"]["moved"]["dci1/DECISIONS_V4R4.md"]["now"]


def test_the_sealed_gate_1_records_were_not_rewritten_by_the_amendment():
    """Whatever the register does, the gate's own record stands as written."""
    amendment = _artifact("register_amendment.json")
    sealed = amendment["sealed_by_gate1"]
    assert set(sealed) == set(MODEL_KEYS)
    one = sealed["gemma-3n-e2b-it"]
    for model_key, entry in sealed.items():
        assert entry["outcome"] == "PASS", model_key
        assert entry["protocol_hash"] == one["protocol_hash"], model_key
        assert entry["documents"] == one["documents"], model_key
    # The sealed protocol hash is the superseded one, not today's.
    assert one["protocol_hash"] != protocol_hash()
    assert one["protocol_hash"] == amendment["protocol_hash"]["sealed_by_gate1"]
    # ... and the instrument the gate certified is still the live one.
    assert one["canonical_verifier_hash"] == verifier_source_hash()
