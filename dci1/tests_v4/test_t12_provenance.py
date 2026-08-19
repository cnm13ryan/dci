"""T12. Provenance and reporting.

Clean-tree enforcement; producing-commit membership; non-empty dependency
manifests; environment digests; stage records; transition logs; content hashes;
durable restoration; the four codebook checks; the append-only amendment
register; the freeze-record completeness check refusing an unresolved field;
the result-table column set; programmatic result generation with no manually
transcribed number.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.analysis.bootstrap import FamilyResult, MemberResult
from dci1v4.analysis.results import (
    RESULT_COLUMNS,
    assert_no_manual_numbers,
    assert_table_complete,
    result_rows,
)
from dci1v4.engine import artifacts, environment, fs, gitinfo, store
from dci1v4.engine.context import DCI1_ROOT, registered_context, synthetic_context
from dci1v4.engine.paths import (
    AUX_RECORD_FILES,
    STAGE_RECORD_FILES,
    model_tree,
    required_records,
    unexpected_root_files,
)
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import codebook
from dci1v4.protocol import constants as C
from dci1v4.stages import amendments, freeze as freeze_stage


@pytest.fixture()
def tree(tmp_path):
    context = synthetic_context(tmp_path)
    create_signing_key(context.signing_key_path)
    t = model_tree(context, "gemma-3n-e2b-it")
    t.root.mkdir(parents=True, exist_ok=True)
    return t


def test_the_clean_tree_check_has_no_bypass():
    """No parameter, name or environment read can switch the check off.

    Checked on the parsed module rather than on its prose, which states that
    no allow_dirty flag exists.
    """
    import ast

    path = DCI1_ROOT / "src" / "dci1v4" / "engine" / "gitinfo.py"
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = [a.arg for a in node.args.args + node.args.kwonlyargs]
            for bypass in ("allow_dirty", "force", "skip", "override"):
                assert bypass not in names, (node.name, bypass)
        if isinstance(node, ast.Attribute) and node.attr == "environ":
            pytest.fail("the clean-tree check reads the environment")
    assert ast.get_docstring(tree).count("no allow_dirty flag") == 1


def test_producing_commit_membership_refuses_an_untracked_source(tmp_path):
    context = registered_context()
    commit = gitinfo.head_commit(context.repo_root)
    stray = gitinfo.PACKAGE_DIR / "_untracked_probe.py"
    stray.write_text("# not in any commit\n")
    try:
        with pytest.raises(IntegrityError, match="absent from commit"):
            gitinfo.assert_sources_in_commit(context.repo_root, commit)
    finally:
        stray.unlink()


def test_a_non_empty_dependency_manifest_is_required(tmp_path):
    context = synthetic_context(tmp_path)
    report = environment.dependency_digest(context)
    assert report["lockfile_hash"] and report["export_hash"]
    empty = tmp_path / "empty.lock"
    empty.write_text("")
    broken = type(context)(
        namespace=context.namespace, study_id=context.study_id,
        repo_root=context.repo_root, evidence_root=context.evidence_root,
        durable_root=context.durable_root, deps_lock_path=empty,
        deps_export_path=context.deps_export_path)
    with pytest.raises(IntegrityError, match="empty"):
        environment.dependency_digest(broken)


def test_a_dependency_change_moves_the_environment_digest(tmp_path):
    context = synthetic_context(tmp_path)
    record = environment.environment_record(context, command=["x"])
    digest = environment.environment_digest(record)
    other = environment.environment_digest({**record, "lockfile_hash": "z"})
    assert digest != other
    assert "container" not in record or Path("/.dockerenv").exists()


def test_stage_records_are_signed_and_verified(tree):
    payload = {"stage": C.STAGE_QUALIFIED, "outcome": "PASS",
               "artifact_type": "qualification_record"}
    signed = sign_payload(payload, tree.context.signing_key_path)
    assert verify_signed(signed, tree.context.signing_key_path) == payload
    tampered = {**signed, "payload": {**payload, "outcome": "FAIL"}}
    with pytest.raises(IntegrityError, match="record hash mismatch"):
        verify_signed(tampered, tree.context.signing_key_path)
    forged = {**signed, "signature": "0" * 64}
    with pytest.raises(IntegrityError, match="signature mismatch"):
        verify_signed(forged, tree.context.signing_key_path)


def test_one_frozen_path_function_and_a_closed_root_vocabulary(tree):
    assert set(STAGE_RECORD_FILES) == set(C.STAGE_SEQUENCE)
    names = required_records(C.STAGE_GATE2)
    assert names[0] == "qualification.json"
    assert names[-1] == "gate2_regime.json"
    (tree.root / "stray_record.json").write_text("{}")
    assert unexpected_root_files(tree) == ["stray_record.json"]
    (tree.root / "stray_record.json").unlink()
    (tree.root / AUX_RECORD_FILES[0]).write_text("")
    assert unexpected_root_files(tree) == []


def test_the_artifact_ledger_is_monotonic_and_append_only(tree):
    path = tree.root / "artifacts" / "thing.json"
    fs.write_json(path, {"x": 1})
    for state in ("generated", "committed", "accepted"):
        artifacts.record_state(tree, artifact_id="thing", path=path,
                               artifact_type="gate_record", state=state,
                               stage=C.STAGE_GATE1, producing_commit="c")
    with pytest.raises(IntegrityError, match="monotonic"):
        artifacts.record_state(tree, artifact_id="thing", path=path,
                               artifact_type="gate_record", state="committed",
                               stage=C.STAGE_GATE1, producing_commit="c")
    artifacts.record_state(tree, artifact_id="thing", path=path,
                           artifact_type="gate_record", state="superseded",
                           stage=C.STAGE_GATE1, producing_commit="c")
    with pytest.raises(IntegrityError):
        artifacts.record_state(tree, artifact_id="thing", path=path,
                               artifact_type="gate_record", state="accepted",
                               stage=C.STAGE_GATE1, producing_commit="c")
    counts = artifacts.state_counts(tree)
    assert counts["generated"] == counts["committed"] == 1
    assert counts["accepted"] == 1 and counts["superseded"] == 1


def test_the_one_shot_ledger_precedes_the_mutation(tree):
    artifacts.claim_one_shot(tree, operation="calibration", detail={},
                             producing_commit="c")
    assert artifacts.one_shot_claimed(tree, "calibration")
    with pytest.raises(IntegrityError, match="already claimed"):
        artifacts.claim_one_shot(tree, operation="calibration", detail={},
                                 producing_commit="c")


def test_a_committed_artifact_needs_durable_bytes_and_a_matching_hash(tree):
    # `generated` precedes the durable write; `committed` requires the bytes.
    missing = tree.root / "artifacts" / "absent.json"
    artifacts.record_state(tree, artifact_id="a", path=missing,
                           artifact_type="gate_record", state="generated",
                           stage=C.STAGE_GATE1, producing_commit="c")
    with pytest.raises(IntegrityError, match="no durable bytes"):
        artifacts.record_state(tree, artifact_id="a", path=missing,
                               artifact_type="gate_record", state="committed",
                               stage=C.STAGE_GATE1, producing_commit="c")
    path = tree.root / "artifacts" / "present.json"
    fs.write_json(path, {"x": 1})
    artifacts.record_state(tree, artifact_id="b", path=path,
                           artifact_type="gate_record", state="generated",
                           stage=C.STAGE_GATE1, producing_commit="c")
    with pytest.raises(IntegrityError, match="content hash mismatch"):
        artifacts.record_state(tree, artifact_id="b", path=path,
                               artifact_type="gate_record", state="committed",
                               stage=C.STAGE_GATE1, producing_commit="c",
                               content_hash="0" * 64)


def test_durable_replication_and_restoration(tree, tmp_path):
    fs.write_json(tree.root / "confirmatory" / "cache.jsonl", {"x": 1})
    store.replicate(tree.root, tree.durable)
    store.assert_replicated(tree.root, tree.durable)
    (tree.root / "confirmatory" / "cache.jsonl").unlink()
    with pytest.raises(IntegrityError, match="out of date"):
        store.assert_replicated(tree.durable, tree.root)
    store.restore(tree.durable, tree.root)
    store.assert_replicated(tree.root, tree.durable)


def test_the_four_codebook_checks():
    columns = [row["name"] for row in codebook.CODEBOOK]
    report = codebook.run_all_checks(columns, [], ["scores", "cell_type"])
    assert report["codebook_rows"] == len(codebook.CODEBOOK)
    with pytest.raises(ProtocolError, match="absent from the codebook"):
        codebook.check_columns(columns + ["invented"])
    with pytest.raises(ProtocolError, match="absent from the released table"):
        codebook.check_columns(columns[:-1])
    with pytest.raises(ProtocolError, match="not integer"):
        codebook.check_values([{"draw_index": "three"}])
    with pytest.raises(ProtocolError, match="outside"):
        codebook.check_values([{"load": 3}])
    with pytest.raises(ProtocolError, match="post-treatment"):
        codebook.check_no_post_treatment_in_primary(["word_count"])
    with pytest.raises(ProtocolError, match="consumer"):
        codebook.check_execution_fields_consumed(["nothing"])


def test_every_codebook_row_declares_a_registered_causal_role():
    for row in codebook.CODEBOOK:
        assert row["causal_role"] in C.CAUSAL_ROLES
    assert set(codebook.POST_TREATMENT) <= set(C.POST_TREATMENT_FIELDS) | \
        {"accidental", "exact_count_alternatives", "empty",
         "verifier_processing_failure"}


def test_the_amendment_register_is_append_only_and_refuses_weakening(tmp_path):
    path = tmp_path / "amendments.jsonl"
    amendments.record_amendment(
        path, text="clarified the wording of RF3", kind="revision",
        supersedes=[], leaves_untouched=["every gate"],
        affected_artifacts=[], before_study_freeze=True)
    with pytest.raises(ProtocolError, match="weaken a criterion"):
        amendments.record_amendment(
            path, text="widen the caliper so that the gate passes",
            kind="revision", supersedes=[], leaves_untouched=[],
            affected_artifacts=[], before_study_freeze=True)
    with pytest.raises(ProtocolError, match="creates v5"):
        amendments.record_amendment(
            path, text="change an estimand", kind="revision", supersedes=[],
            leaves_untouched=[], affected_artifacts=[],
            before_study_freeze=False)
    with pytest.raises(ProtocolError, match="environment note"):
        amendments.record_amendment(
            path, text="move to another card", kind="operational",
            supersedes=[], leaves_untouched=[], affected_artifacts=[],
            before_study_freeze=False)
    rows = amendments.read_register(path)
    assert len(rows) == 1


def test_the_freeze_refuses_while_anything_is_unresolved():
    record = freeze_stage.build_freeze_record()
    checks = {c: "COMPLETE" for c in freeze_stage.BLOCKING_CHECKS}
    decisions = {d: {"closed": True} for d in freeze_stage.OPEN_DECISIONS}
    report = freeze_stage.check_completeness(record, decisions=decisions,
                                             checks=checks)
    assert report["can_freeze"] is False
    assert report["unresolved_fields"]        # every field is UNKNOWN
    with pytest.raises(ProtocolError, match="freeze is refused"):
        freeze_stage.freeze(record, decisions=decisions, checks=checks)

    complete = {name: "value" for name in freeze_stage.FREEZE_FIELDS}
    open_report = freeze_stage.check_completeness(
        complete, decisions={d: {"closed": False}
                             for d in freeze_stage.OPEN_DECISIONS},
        checks=checks)
    assert open_report["can_freeze"] is False
    assert open_report["open_decisions"] == list(freeze_stage.OPEN_DECISIONS)

    incomplete = freeze_stage.check_completeness(
        complete, decisions=decisions, checks={"C1": "BLOCKED"})
    assert incomplete["can_freeze"] is False
    assert "C1" in incomplete["incomplete_blocking_checks"]

    passing = freeze_stage.freeze(complete, decisions=decisions, checks=checks)
    assert passing["outcome"] == "PASS"


def test_group_d_checks_block_nothing():
    assert set(freeze_stage.REPORT_ONLY_CHECKS) == {"C18", "C19", "C20"}
    assert not set(freeze_stage.REPORT_ONLY_CHECKS) & \
        set(freeze_stage.BLOCKING_CHECKS)


def test_the_result_table_column_set_and_completeness():
    member = MemberResult("D(B<-A)", 0.2, 0.01, 0.18, 0.22, 0.17, 0.23, 0.03)
    family = FamilyResult(family="F1", configuration="outcome_first",
                          resamples=10, critical_value=2.5,
                          members={"D(B<-A)": member})
    rows = result_rows("m", {"F1": family}, claim_levels={"D(B<-A)": "L1"},
                       identification_status=[], measurement_basis="human_validated",
                       precision_preconditions={"D(B<-A)": 0.05},
                       variance={"sigma2_topic": 0.05, "sigma2_draw": 0.15,
                                 "phi": 0.25},
                       detectable={"D(B<-A)": 0.06}, cells_per_block=25,
                       blocks=384, draws_per_cell=4, scope_sentence=None)
    assert assert_table_complete(rows) == 1
    assert set(rows[0]) == set(RESULT_COLUMNS)
    with pytest.raises(ProtocolError, match="without its configuration"):
        assert_table_complete([{**rows[0], "configuration": None}])
    with pytest.raises(ProtocolError, match="missing"):
        assert_table_complete([{k: v for k, v in rows[0].items()
                                if k != "standard_error"}])


def test_no_number_in_a_report_is_transcribed_by_hand():
    rows = [{"estimate": 0.4213, "simultaneous_lower": 0.3800}]
    assert_no_manual_numbers("the estimate was 0.4213 with a lower bound of "
                             "0.3800, against the registered 0.10 threshold",
                             rows)
    with pytest.raises(ProtocolError, match="transcribed by hand"):
        assert_no_manual_numbers("the estimate was 0.9999", rows)
