"""The v4 stage machine (§18): legal transitions, terminal states, and the
append-only transition log.

The only valid sequence is ``STAGE_SEQUENCE``. Every command verifies the
content hash **and** signature of its predecessor's PASS record and
re-verifies the frozen verifier hash before any mutation. A terminal state
mechanically disables every later generation command.

Two v4 rules differ from v3 and both are load-bearing:

* **Gate 3 is not terminal (T-11, §13.5).** Fewer than three admitted
  reference families sets the identification status ``EXCESS_NOT_IDENTIFIED``,
  selects the reduced design of §8.6, and the replication continues. v3's
  ``REFERENCE_POOL_MISMATCH`` stop is withdrawn and is not emittable here.
* **No replication is blocked by another (§6.1).** There is no early-stop rule
  and no cross-model gate; ``E2B_STOP_STATUSES`` has no analogue in v4.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

from dci1v4.engine import fs
from dci1v4.engine.paths import ModelTree
from dci1v4.engine.signing import verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C

#: stage -> the stage that must have PASSED before it may run.
PREDECESSOR = {stage: C.STAGE_SEQUENCE[index - 1] if index else None
               for index, stage in enumerate(C.STAGE_SEQUENCE)}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def log_transition(tree: ModelTree, *, stage: str, outcome: str,
                   producing_commit: str, environment_digest: str,
                   input_hash: str | None = None,
                   output_hash: str | None = None,
                   model_revision: str | None = None,
                   detail: dict[str, Any] | None = None) -> dict[str, Any]:
    """§18: every *attempted* transition is logged, including refusals."""
    row = fs.row_with_hash({
        "timestamp": _now(), "stage": stage, "outcome": outcome,
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
    """The recorded terminal status of this replication, if any."""
    if not tree.terminal_report.exists():
        return None
    record = fs.read_json(tree.terminal_report)
    payload = record.get("payload", record)
    return payload.get("status")


def identification_statuses(tree: ModelTree) -> list[str]:
    """Identification statuses recorded on gate records. Not terminal."""
    out: list[str] = []
    for stage in C.STAGE_SEQUENCE:
        path = tree.stage_record(stage)
        if not path.exists():
            continue
        payload = fs.read_json(path)
        payload = payload.get("payload", payload)
        for status in payload.get("identification_statuses", []):
            if status not in out:
                out.append(status)
    return out


def read_stage_record(tree: ModelTree, stage: str) -> dict[str, Any]:
    path = tree.stage_record(stage)
    if not path.exists():
        raise IntegrityError(f"{tree.model_key}: {stage} record missing at "
                             f"{path}")
    record = fs.read_json(path)
    return verify_signed(record, tree.context.signing_key_path,
                         where=f"{tree.model_key}:{stage}")


def assert_predecessor_passed(tree: ModelTree, stage: str) -> dict[str, Any]:
    """Verify the predecessor PASS record's hash and signature (§18)."""
    if stage not in PREDECESSOR:
        raise ProtocolError(f"{stage!r} is not a registered v4 stage")
    status = terminal_status(tree)
    if status is not None:
        raise IntegrityError(
            f"{tree.model_key} is terminal at {status}; every later stage is "
            f"mechanically disabled ({C.TERMINAL_SENTENCE})")
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
    """A stage may run once, in order, with its predecessor passed."""
    if tree.stage_record(stage).exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} already has a record; v4 stage "
            f"records are write-once")
    assert_predecessor_passed(tree, stage)


def write_stage_record(tree: ModelTree, stage: str, payload: dict[str, Any]
                       ) -> Path:
    """Sign and write a stage record write-once."""
    from dci1v4.engine.signing import sign_payload

    if payload.get("stage") != stage:
        raise ProtocolError(f"record payload declares stage "
                            f"{payload.get('stage')!r}, not {stage!r}")
    declared = payload.get("artifact_type")
    if declared != C.STAGE_ARTIFACT_TYPE[stage]:
        raise IntegrityError(
            f"artifact type {declared!r} disagrees with stage {stage!r}, "
            f"which requires {C.STAGE_ARTIFACT_TYPE[stage]!r}")
    path = tree.stage_record(stage)
    fs.write_json_once(path, sign_payload(payload,
                                          tree.context.signing_key_path))
    return path


def write_terminal_report(tree: ModelTree, payload: dict[str, Any]) -> Path:
    """§28.3: the terminal record, carrying the registered sentence verbatim."""
    from dci1v4.engine.signing import sign_payload

    status = payload.get("status")
    if status not in C.TERMINAL_STATUSES:
        note = ""
        if status in C.WITHDRAWN_STATUSES:
            note = (" It stays the correct HISTORICAL label when v4 cites the "
                    "two v3 Qwen terminations or the withdrawn revision 1 "
                    "gate; the ban is on emission, not on the string.")
        raise ProtocolError(
            f"{status!r} is not a registered v4 terminal status.{note} "
            f"Registered: {C.TERMINAL_STATUSES}")
    missing = [field for field in
               ("model_key", "model_revision", "gate", "criterion",
                "threshold", "observed", "artifact_hashes",
                "producing_commit", "environment_digest",
                "strongest_permissible_statement", "estimands_unanswerable")
               if field not in payload]
    if missing:
        raise ProtocolError(f"terminal record is missing {missing}")
    payload = {**payload, "terminal_sentence": C.TERMINAL_SENTENCE}
    path = tree.terminal_report
    fs.write_json_once(path, sign_payload(payload,
                                          tree.context.signing_key_path))
    return path
