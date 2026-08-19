"""State-machine correctness (item 62): legal and illegal transitions,
authenticated predecessor verification, terminal lockout, single-shot stage
records, and stage/artifact-type agreement."""
from __future__ import annotations

import json

import pytest

from dci1v3.engine import fs, transitions
from dci1v3.engine.dispatch import dispatch
from dci1v3.engine.paths import model_tree
from dci1v3.errors import IntegrityError, ProtocolError, StateError
from dci1v3.protocol import constants as C

MODEL = "gemma-3n-e2b-it"


@pytest.fixture()
def qualified(registered_ctx):
    outcome = dispatch(registered_ctx, "qualify", MODEL)
    assert outcome["outcome"] == "PASSED"
    return registered_ctx


def test_stage_skipping_refused(registered_ctx):
    with pytest.raises(StateError, match="missing"):
        dispatch(registered_ctx, "prescreen", MODEL)


def test_execution_order_enforced(registered_ctx):
    with pytest.raises(ProtocolError, match="runs first"):
        dispatch(registered_ctx, "qualify", "qwen3-4b")


def test_qualification_passes_and_verifies(qualified):
    tree = model_tree(qualified, MODEL)
    assert transitions.current_state(tree) == C.STAGE_QUALIFIED
    record = transitions.verify_stage_record(tree, C.STAGE_QUALIFIED)
    assert record["payload"]["artifact_type"] == "qualification_record"
    log = fs.read_jsonl(tree.transition_log)
    assert any(e["operation"] == C.STAGE_QUALIFIED for e in log)


def test_stage_record_single_shot(qualified):
    with pytest.raises(StateError, match="single-shot"):
        dispatch(qualified, "qualify", MODEL)


def test_tampered_predecessor_hash_detected(qualified):
    tree = model_tree(qualified, MODEL)
    record = json.loads(tree.stage_record(C.STAGE_QUALIFIED).read_text())
    record["payload"]["body"]["checks"]["stores_reachable"] = False
    tree.stage_record(C.STAGE_QUALIFIED).write_text(json.dumps(record))
    with pytest.raises(IntegrityError, match="hash"):
        transitions.verify_stage_record(tree, C.STAGE_QUALIFIED)
    with pytest.raises(IntegrityError):
        dispatch(qualified, "pilot", MODEL)


def test_tampered_predecessor_signature_detected(qualified):
    tree = model_tree(qualified, MODEL)
    record = json.loads(tree.stage_record(C.STAGE_QUALIFIED).read_text())
    record["signature"] = "f" * 64
    tree.stage_record(C.STAGE_QUALIFIED).write_text(json.dumps(record))
    with pytest.raises(IntegrityError, match="signature"):
        transitions.verify_stage_record(tree, C.STAGE_QUALIFIED)


def test_terminal_disables_generation(qualified):
    tree = model_tree(qualified, MODEL)
    transitions.write_terminal_report(
        tree, status="RESPONSE_LENGTH_INCOMPATIBLE",
        body={"criterion": "test"}, producing_commit="c" * 40,
        environment_digest="d" * 64)
    from dci1v3.engine import store
    store.replicate(tree.root, tree.durable)
    with pytest.raises(StateError, match="terminal"):
        dispatch(qualified, "pilot", MODEL)
    with pytest.raises(StateError, match="terminal"):
        dispatch(qualified, "generate", MODEL)


def test_terminal_report_requires_registered_status(qualified):
    tree = model_tree(qualified, MODEL)
    with pytest.raises(IntegrityError, match="not a registered terminal"):
        transitions.write_terminal_report(
            tree, status="MADE_UP", body={}, producing_commit="c" * 40,
            environment_digest="d" * 64)


def test_e2b_stop_status_blocks_other_models(qualified):
    tree = model_tree(qualified, MODEL)
    transitions.write_terminal_report(
        tree, status="REFERENCE_POOL_MISMATCH",
        body={"criterion": "test"}, producing_commit="c" * 40,
        environment_digest="d" * 64)
    with pytest.raises(ProtocolError, match="do not start"):
        dispatch(qualified, "qualify", "qwen3-4b")


def test_stage_artifact_types_are_registered():
    for stage, artifact_type in C.STAGE_ARTIFACT_TYPE.items():
        assert stage in C.STAGE_SEQUENCE
        assert artifact_type in C.ARTIFACT_TYPES


def test_unexpected_registered_path_fails_verification(qualified):
    from dci1v3.engine.verify import verify_evidence
    tree = model_tree(qualified, MODEL)
    stray = tree.root / "stray_record.json"
    stray.write_text("{}")
    with pytest.raises(IntegrityError, match="unexpected registered"):
        verify_evidence(tree)
