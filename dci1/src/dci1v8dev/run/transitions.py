"""The pilot's stage machine: in order, once, terminal is terminal, one study.

v7's six rules (``dci1v7.engine.transitions``) minus the two that have no
object here: there is no §34 decision registry in the pilot (its rules are
``dci1v8dev.rules`` and are bound by the manifest, not decided per stage),
and there is no freeze to protect. Every *attempted* transition is logged,
refusals included, on the replication's own append-only log.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs
from dci1v4.engine.signing import sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import canonical_json

from dci1v8dev.run import stages as S
from dci1v8dev.run.context import ModelTree

__all__ = ["PREDECESSOR", "log_transition", "transition_rows",
           "terminal_status", "assert_own_study", "read_stage_record",
           "stage_reached", "assert_predecessor_passed",
           "assert_transition_legal", "on_the_wire", "write_stage_record",
           "write_terminal_report"]

PREDECESSOR: dict[str, str | None] = {
    stage: S.STAGE_SEQUENCE[index - 1] if index else None
    for index, stage in enumerate(S.STAGE_SEQUENCE)}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def log_transition(tree: ModelTree, *, stage: str, outcome: str,
                   producing_commit: str, environment_digest: str,
                   input_hash: str | None = None,
                   output_hash: str | None = None,
                   model_revision: str | None = None,
                   detail: dict[str, Any] | None = None) -> dict[str, Any]:
    row = fs.row_with_hash({
        "timestamp": _now(), "stage": stage, "outcome": outcome,
        "study_id": tree.context.study_id,
        "model_key": tree.model_key, "model_revision": model_revision,
        "namespace": tree.context.namespace,
        "producing_commit": producing_commit,
        "environment_digest": environment_digest,
        "input_hash": input_hash, "output_hash": output_hash,
        "detail": detail or {},
    })
    fs.append_jsonl(tree.transition_log, row)
    return row


def transition_rows(tree: ModelTree) -> list[dict[str, Any]]:
    if not tree.transition_log.exists():
        return []
    rows = fs.read_jsonl(tree.transition_log)
    for row in rows:
        fs.verify_row_hash(row, where=f"transition:{row.get('stage')}")
    return rows


def terminal_status(tree: ModelTree) -> str | None:
    if not tree.terminal_report.exists():
        return None
    record = fs.read_json(tree.terminal_report)
    payload = record.get("payload", record)
    return payload.get("status")


def assert_own_study(tree: ModelTree, stage: str,
                     payload: Mapping[str, Any]) -> None:
    declared = payload.get("study_id")
    if declared == tree.context.study_id:
        return
    raise IntegrityError(
        f"{tree.model_key}: the {stage} record declares study_id "
        f"{declared!r} and this study is {tree.context.study_id!r}. A "
        "record from another revision or namespace is never a predecessor "
        "here")


def read_stage_record(tree: ModelTree, stage: str) -> dict[str, Any]:
    """The signed record's payload, hash and signature both verified."""
    path = tree.stage_record(stage)
    if not path.exists():
        raise IntegrityError(f"{tree.model_key}: {stage} record missing at "
                             f"{path}")
    record = fs.read_json(path)
    payload = verify_signed(record, tree.context.signing_key_path,
                            where=f"{tree.model_key}:{stage}")
    assert_own_study(tree, stage, payload)
    return payload


def stage_reached(tree: ModelTree) -> str | None:
    reached = None
    for stage in S.STAGE_SEQUENCE:
        if tree.stage_record(stage).exists():
            reached = stage
    return reached


def assert_predecessor_passed(tree: ModelTree, stage: str) -> dict[str, Any]:
    if stage not in PREDECESSOR:
        raise ProtocolError(f"{stage!r} is not a v8 pilot stage")
    status = terminal_status(tree)
    if status is not None:
        raise IntegrityError(
            f"{tree.model_key} is terminal at {status}; every later stage is "
            f"mechanically disabled ({S.TERMINAL_SENTENCE})")
    predecessor = PREDECESSOR[stage]
    if predecessor is None:
        return {}
    payload = read_stage_record(tree, predecessor)
    if payload.get("outcome") != "PASS":
        raise IntegrityError(
            f"{tree.model_key}: {predecessor} recorded "
            f"{payload.get('outcome')!r}, not PASS; {stage} may not run")
    return payload


def assert_transition_legal(tree: ModelTree, stage: str) -> None:
    """Once, in order, with the predecessor passed and no terminal report."""
    if stage not in S.STAGE_SEQUENCE:
        raise ProtocolError(f"{stage!r} is not a v8 pilot stage")
    if tree.stage_record(stage).exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} already has a record; v8 stage "
            "records are write-once. Repair runs the stage in a fresh root")
    assert_predecessor_passed(tree, stage)


def on_the_wire(payload: dict[str, Any]) -> dict[str, Any]:
    """The payload as a reader gets it back (JSON keys are strings)."""
    return json.loads(canonical_json(payload))


def write_stage_record(tree: ModelTree, stage: str, payload: dict[str, Any]
                       ) -> Path:
    if payload.get("stage") != stage:
        raise ProtocolError(f"record payload declares stage "
                            f"{payload.get('stage')!r}, not {stage!r}")
    declared = payload.get("artifact_type")
    if declared != S.STAGE_ARTIFACT_TYPE[stage]:
        raise IntegrityError(
            f"artifact type {declared!r} disagrees with stage {stage!r}, "
            f"which requires {S.STAGE_ARTIFACT_TYPE[stage]!r}")
    declared_study = payload.get("study_id")
    if declared_study is None:
        payload = {**payload, "study_id": tree.context.study_id}
    elif declared_study != tree.context.study_id:
        raise IntegrityError(
            f"record payload declares study_id {declared_study!r} and this "
            f"context is {tree.context.study_id!r}")
    payload = on_the_wire(payload)
    signed = sign_payload(payload, tree.context.signing_key_path)
    verify_signed(signed, tree.context.signing_key_path,
                  f"{tree.model_key}:{stage}:at-write")
    path = tree.stage_record(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, signed)
    reader = tree.stage_record_reader_copy(stage)
    reader.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(reader, payload)
    return path


def write_terminal_report(tree: ModelTree, payload: dict[str, Any]) -> Path:
    status = payload.get("status")
    if status not in S.TERMINAL_STATUSES:
        raise ProtocolError(
            f"{status!r} is not a v8 pilot terminal status. Registered: "
            f"{S.TERMINAL_STATUSES}")
    missing = [f for f in ("model_key", "gate", "criterion", "observed",
                           "producing_commit",
                           "strongest_permissible_statement")
               if f not in payload]
    if missing:
        raise ProtocolError(f"terminal record is missing {missing}")
    payload = {**payload, "terminal_sentence": S.TERMINAL_SENTENCE,
               "study_id": tree.context.study_id}
    path = tree.terminal_report
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, sign_payload(payload,
                                          tree.context.signing_key_path))
    return path
