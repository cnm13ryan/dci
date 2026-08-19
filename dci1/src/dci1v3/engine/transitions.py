"""The canonical state machine (item 6): signed stage records, authenticated
predecessor verification, append-only transition log, terminal handling.

Every stage record is signed and write-once at its §27 filename. Every
transition — attempted or completed — is appended to the transition log with
timestamp, model revision, producing commit, environment digest, and input
and output hashes. A terminal report mechanically disables every later
generation command.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from dci1v3.engine import artifacts, fs
from dci1v3.engine.paths import ModelTree
from dci1v3.engine.signing import sign_payload, verify_signed
from dci1v3.errors import IntegrityError, StateError
from dci1v3.models.registry import get_model
from dci1v3.protocol import constants as C


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def append_transition(tree: ModelTree, entry: dict[str, Any]) -> None:
    fs.append_jsonl(tree.transition_log, {"timestamp": utc_now(), **entry})


def terminal_status(tree: ModelTree) -> str | None:
    if not tree.terminal_report.exists():
        return None
    record = fs.read_json(tree.terminal_report)
    payload = verify_signed(record, tree.context.signing_key_path,
                            where="terminal_report")
    return payload["status"]


def assert_generation_allowed(tree: ModelTree) -> None:
    status = terminal_status(tree)
    if status is not None:
        raise StateError(
            f"{tree.model_key} reached terminal status {status}; every "
            f"later generation command is disabled")


def load_stage_record(tree: ModelTree, stage: str) -> dict[str, Any] | None:
    path = tree.stage_record(stage)
    if not path.exists():
        return None
    return fs.read_json(path)


def verify_stage_record(tree: ModelTree, stage: str) -> dict[str, Any]:
    """Authenticate one stage record: content hash AND signature, stage
    identity, PASS status, model identity and revision, producing commit,
    environment digest, input hashes, and namespace."""
    record = load_stage_record(tree, stage)
    if record is None:
        raise StateError(f"required predecessor record for {stage} is "
                         f"missing from {tree.model_key}")
    payload = verify_signed(record, tree.context.signing_key_path,
                            where=f"{tree.model_key}:{stage}")
    spec = get_model(tree.model_key)
    checks = {
        "stage identity": payload.get("stage") == stage,
        "PASS status": payload.get("status") == "PASSED",
        "model replication": payload.get("model_key") == tree.model_key,
        "model identity": payload.get("model_id") == spec.model_id,
        "model revision": payload.get("model_revision") == spec.revision,
        "producing commit": bool(payload.get("producing_commit")),
        "environment digest": bool(payload.get("environment_digest")),
        "input hashes": isinstance(payload.get("input_hashes"), dict),
        "namespace": payload.get("namespace") == tree.context.namespace,
        "study": payload.get("study_id") == tree.context.study_id,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise IntegrityError(
            f"{tree.model_key}:{stage} predecessor verification failed: "
            f"{failed}")
    index = C.STAGE_SEQUENCE.index(stage)
    if index > C.STAGE_SEQUENCE.index(C.STAGE_FREEZE):
        freeze = load_stage_record(tree, C.STAGE_FREEZE)
        if freeze is None or payload.get("freeze_record_hash") != \
                freeze["record_hash"]:
            raise IntegrityError(
                f"{tree.model_key}:{stage} is not bound to the frozen "
                f"provenance (freeze_record_hash mismatch)")
    return {"payload": payload, "record_hash": record["record_hash"],
            "signature": record["signature"]}


def predecessor_stage(stage: str) -> str | None:
    index = C.STAGE_SEQUENCE.index(stage)
    return C.STAGE_SEQUENCE[index - 1] if index else None


def verify_chain(tree: ModelTree, through: str) -> list[dict[str, Any]]:
    """Verify every stage record from QUALIFIED through ``through``."""
    verified = []
    for stage in C.STAGE_SEQUENCE:
        verified.append(verify_stage_record(tree, stage))
        if stage == through:
            break
    return verified


def current_state(tree: ModelTree) -> str | None:
    """The furthest stage whose signed PASS record verifies, chain-checked."""
    state = None
    for stage in C.STAGE_SEQUENCE:
        if load_stage_record(tree, stage) is None:
            break
        verify_stage_record(tree, stage)
        state = stage
    return state


def assert_transition_allowed(tree: ModelTree, stage: str) -> None:
    if stage in C.GENERATION_STAGES:
        assert_generation_allowed(tree)
    elif terminal_status(tree) is not None:
        raise StateError(f"{tree.model_key} is terminal; {stage} refused")
    if tree.stage_record(stage).exists():
        raise StateError(f"{tree.model_key}:{stage} record already exists; "
                         f"stage transitions are single-shot")
    previous = predecessor_stage(stage)
    if previous is not None:
        verify_stage_record(tree, previous)


def write_stage_record(tree: ModelTree, stage: str, *, status: str,
                       body: dict[str, Any], producing_commit: str,
                       environment_digest: str,
                       input_hashes: dict[str, str],
                       output_hashes: dict[str, str] | None = None
                       ) -> dict[str, Any]:
    """Sign and write one stage record; ledger and transition log entries."""
    spec = get_model(tree.model_key)
    payload: dict[str, Any] = {
        "protocol": C.PROTOCOL, "protocol_version": C.PROTOCOL_VERSION,
        "study_id": tree.context.study_id,
        "namespace": tree.context.namespace,
        "stage": stage, "status": status,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[stage],
        "model_key": tree.model_key, "model_id": spec.model_id,
        "model_revision": spec.revision,
        "producing_commit": producing_commit,
        "environment_digest": environment_digest,
        "input_hashes": input_hashes,
        "output_hashes": output_hashes or {},
        "timestamp": utc_now(),
        "body": body,
    }
    previous = predecessor_stage(stage)
    if previous is not None:
        pred = verify_stage_record(tree, previous)
        payload["predecessor"] = {
            "stage": previous, "record_hash": pred["record_hash"],
            "signature": pred["signature"]}
    if C.STAGE_SEQUENCE.index(stage) > \
            C.STAGE_SEQUENCE.index(C.STAGE_FREEZE):
        freeze = load_stage_record(tree, C.STAGE_FREEZE)
        if freeze is None:
            raise StateError(f"{stage} requires the freeze record")
        payload["freeze_record_hash"] = freeze["record_hash"]
    record = sign_payload(payload, tree.context.signing_key_path)
    fs.write_json_once(tree.stage_record(stage), record)
    artifacts.record_state(
        tree, artifact_id=f"stage:{stage}", path=tree.stage_record(stage),
        artifact_type=C.STAGE_ARTIFACT_TYPE[stage], state="generated",
        stage=stage, producing_commit=producing_commit)
    artifacts.record_state(
        tree, artifact_id=f"stage:{stage}", path=tree.stage_record(stage),
        artifact_type=C.STAGE_ARTIFACT_TYPE[stage], state="committed",
        stage=stage, producing_commit=producing_commit)
    if status == "PASSED":
        artifacts.record_state(
            tree, artifact_id=f"stage:{stage}", path=tree.stage_record(stage),
            artifact_type=C.STAGE_ARTIFACT_TYPE[stage], state="accepted",
            stage=stage, producing_commit=producing_commit)
    append_transition(tree, {
        "operation": stage, "outcome": status,
        "model_revision": spec.revision,
        "producing_commit": producing_commit,
        "environment_digest": environment_digest,
        "input_hashes": input_hashes, "output_hashes": output_hashes or {},
        "record_hash": record["record_hash"]})
    return record


def write_terminal_report(tree: ModelTree, *, status: str,
                          body: dict[str, Any], producing_commit: str,
                          environment_digest: str) -> dict[str, Any]:
    """Emit the mandatory terminal report (§26) and disable generation."""
    if status not in C.TERMINAL_STATUSES:
        raise IntegrityError(f"{status!r} is not a registered terminal "
                             f"status")
    spec = get_model(tree.model_key)
    payload = {
        "protocol": C.PROTOCOL, "protocol_version": C.PROTOCOL_VERSION,
        "study_id": tree.context.study_id,
        "namespace": tree.context.namespace,
        "status": status, "model_key": tree.model_key,
        "model_id": spec.model_id, "model_revision": spec.revision,
        "producing_commit": producing_commit,
        "environment_digest": environment_digest,
        "timestamp": utc_now(), "body": body,
    }
    record = sign_payload(payload, tree.context.signing_key_path)
    fs.write_json_once(tree.terminal_report, record)
    append_transition(tree, {
        "operation": "terminal_report", "outcome": status,
        "model_revision": spec.revision,
        "producing_commit": producing_commit,
        "environment_digest": environment_digest,
        "record_hash": record["record_hash"]})
    return record
