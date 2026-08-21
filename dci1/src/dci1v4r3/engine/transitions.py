"""The v4r3 stage machine (§18): legal transitions and the transition log.

**Why this module exists.** v4r3 was implemented without one. `dci1v4` has
`engine/transitions.py` and every v4r2 command verifies its predecessor's
signed PASS record before it mutates anything; v4r3 had only
`STAGE_SEQUENCE` as a list of strings in `constants.py` and nothing that read
it. That is how the §12.2 regime screen came to run before `QUALIFIED` and
before `GATE_0_APPARATUS` --- not by a decision, but because no guard existed
to refuse it. The out-of-order run is recorded as such rather than
reinterpreted; see `adopt_out_of_order` below and §4i of `RESEARCH_STATE.md`.

The rules, all three enforced here and none of them documentation:

* **In order.** A stage may run only when its `STAGE_SEQUENCE` predecessor
  has a record whose `outcome` is `PASS`, whose content hash recomputes, and
  whose signature verifies under the study signing key.
* **Once.** Stage records are write-once. Re-running a stage that already has
  a record is an `IntegrityError`, not an overwrite. Repair means a new
  producing commit and a fresh model tree, exactly as §19 says for
  `APPARATUS_FAILURE`.
* **Terminal is terminal.** Once a replication has written a terminal report,
  every later stage is mechanically disabled. `TERMINAL_SENTENCE` travels with
  the refusal so that a reader who meets only the refusal still learns that a
  terminal pre-confirmatory status carries no evidence about the effect.

Post-freeze mutation is a fourth rule and it lives here too: once
`GATE_5_FREEZE` has passed, `assert_no_post_freeze_mutation` refuses any
attempt to write a record for a stage at or before the freeze.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

from dci1v4.engine import fs
from dci1v4.engine.signing import sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r3.engine.paths import ModelTree
from dci1v4r3.protocol import constants as C

__all__ = ["PREDECESSOR", "log_transition", "transition_rows",
           "terminal_status", "read_stage_record", "stage_reached",
           "assert_predecessor_passed", "assert_transition_legal",
           "assert_no_post_freeze_mutation", "write_stage_record",
           "write_terminal_report", "adopt_out_of_order"]

#: stage -> the stage that must have PASSED before it may run.
PREDECESSOR: dict[str, str | None] = {
    stage: C.STAGE_SEQUENCE[index - 1] if index else None
    for index, stage in enumerate(C.STAGE_SEQUENCE)}


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def log_transition(tree: ModelTree, *, stage: str, outcome: str,
                   producing_commit: str, environment_digest: str,
                   input_hash: str | None = None,
                   output_hash: str | None = None,
                   model_revision: str | None = None,
                   detail: dict[str, Any] | None = None) -> dict[str, Any]:
    """§18: every *attempted* transition is logged, refusals included.

    A log that recorded only successes would make an illegal attempt
    invisible, and the reason to have a stage machine at all is that the
    attempt is the thing worth seeing.
    """
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
    """The recorded terminal status of this replication, if any."""
    if not tree.terminal_report.exists():
        return None
    record = fs.read_json(tree.terminal_report)
    payload = record.get("payload", record)
    return payload.get("status")


def read_stage_record(tree: ModelTree, stage: str) -> dict[str, Any]:
    """The signed record's payload, hash and signature both verified."""
    path = tree.stage_record(stage)
    if not path.exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} record missing at {path}")
    record = fs.read_json(path)
    return verify_signed(record, tree.context.signing_key_path,
                         where=f"{tree.model_key}:{stage}")


def stage_reached(tree: ModelTree) -> str | None:
    """The furthest stage with a record, in registered order."""
    reached = None
    for stage in C.STAGE_SEQUENCE:
        if tree.stage_record(stage).exists():
            reached = stage
    return reached


def assert_predecessor_passed(tree: ModelTree, stage: str) -> dict[str, Any]:
    """Verify the predecessor's PASS record: hash, signature and outcome."""
    if stage not in PREDECESSOR:
        raise ProtocolError(f"{stage!r} is not a registered v4r3 stage")
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


def assert_no_post_freeze_mutation(tree: ModelTree, stage: str) -> None:
    """§18.1: after the freeze passes, nothing at or before it may be rewritten.

    The freeze binds the scientific state. A later write to a stage the freeze
    already bound would change what the freeze record refers to without
    changing the freeze record, which is precisely the silent post-freeze
    mutation §18.1 exists to make impossible.
    """
    freeze = tree.stage_record(C.STAGE_GATE5)
    if not freeze.exists():
        return
    order = list(C.STAGE_SEQUENCE)
    if order.index(stage) <= order.index(C.STAGE_GATE5):
        raise IntegrityError(
            f"{tree.model_key}: {C.STAGE_GATE5} has passed, so {stage} is "
            f"frozen. A scientific change now requires a new protocol "
            f"revision, not a rewritten record")


def assert_transition_legal(tree: ModelTree, stage: str) -> None:
    """A stage may run once, in order, with its predecessor passed."""
    if tree.stage_record(stage).exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} already has a record; v4r3 stage "
            f"records are write-once. Repair creates a new producing commit "
            f"and runs the stage in a fresh tree")
    assert_no_post_freeze_mutation(tree, stage)
    assert_predecessor_passed(tree, stage)


def write_stage_record(tree: ModelTree, stage: str, payload: dict[str, Any]
                       ) -> Path:
    """Sign and write a stage record write-once, with a reader copy."""
    if payload.get("stage") != stage:
        raise ProtocolError(f"record payload declares stage "
                            f"{payload.get('stage')!r}, not {stage!r}")
    declared = payload.get("artifact_type")
    if declared != C.STAGE_ARTIFACT_TYPE[stage]:
        raise IntegrityError(
            f"artifact type {declared!r} disagrees with stage {stage!r}, "
            f"which requires {C.STAGE_ARTIFACT_TYPE[stage]!r}")
    signed = sign_payload(payload, tree.context.signing_key_path)
    path = tree.stage_record(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, signed)
    reader = tree.stage_record_reader_copy(stage)
    reader.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(reader, payload)
    return path


def write_terminal_report(tree: ModelTree, payload: dict[str, Any]) -> Path:
    """§28.3's terminal record, carrying the registered sentence verbatim."""
    status = payload.get("status")
    if status not in C.TERMINAL_STATUSES:
        raise ProtocolError(
            f"{status!r} is not a registered v4r3 terminal status. "
            f"Registered: {C.TERMINAL_STATUSES}")
    missing = [field for field in
               ("model_key", "gate", "criterion", "observed",
                "producing_commit", "strongest_permissible_statement")
               if field not in payload]
    if missing:
        raise ProtocolError(f"terminal record is missing {missing}")
    payload = {**payload, "terminal_sentence": C.TERMINAL_SENTENCE}
    path = tree.terminal_report
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, sign_payload(payload,
                                          tree.context.signing_key_path))
    return path


def adopt_out_of_order(tree: ModelTree, stage: str, payload: dict[str, Any], *,
                       reason: str, produced_before_commit: str) -> Path:
    """Admit evidence that was generated before the stage machine existed.

    This is deliberately **not** a way around `assert_transition_legal`. It
    writes the record with an `out_of_order` block naming the commit the rows
    were produced under and the reason, and it sets `outcome` to
    `ADOPTED_OUT_OF_ORDER` rather than `PASS`, so a later stage's
    `assert_predecessor_passed` still refuses. Its only purpose is to make the
    history legible: the §12.2 rows exist, they were generated before
    `QUALIFIED` and `GATE_0_APPARATUS` passed, and pretending otherwise would
    be worse than recording it.

    A replication that wants a `PASS` at this stage regenerates it under the
    bound commit through the ordinary path.
    """
    if not reason or not produced_before_commit:
        raise ProtocolError(
            "adopting out-of-order evidence requires the reason and the "
            "commit the rows were produced under")
    payload = {**payload, "outcome": "ADOPTED_OUT_OF_ORDER",
               "out_of_order": {
                   "reason": reason,
                   "produced_under_commit": produced_before_commit,
                   "consequence": "this record does not satisfy the "
                                  "predecessor requirement of any later "
                                  "stage; the stage must be re-run in order "
                                  "under the bound producing commit",
                   "tier": "REGISTERED DIAGNOSTIC, not confirmatory"}}
    signed = sign_payload(payload, tree.context.signing_key_path)
    path = tree.stage_record(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, signed)
    return path
