"""The v5 stage machine (§18): legal transitions and the transition log.

Carried from v4r4 in substance --- in order, once, terminal is terminal, one
study, no post-freeze mutation --- with **one addition that is the point of
this revision's implementation**: a stage may not run while a §34 decision it
depends on is open. ``assert_transition_legal`` calls
``decisions.assert_decisions_closed_for_stage``, and ``PROTOCOL_REGISTERED``
depends on all nineteen, so with the draft as it stands **no v5 stage can
run**. That is the intended state and §18 stage 1's failure status
``REGISTRATION_INCOMPLETE`` is its name.

The rules, all six enforced here and none of them documentation:

* **In order.** A stage may run only when its ``STAGE_SEQUENCE`` predecessor
  has a record whose ``outcome`` is ``PASS``, whose content hash recomputes,
  and whose signature verifies under the study signing key.
* **Once.** Stage records are write-once. Re-running a stage that already has
  a record is an ``IntegrityError``, not an overwrite.
* **Terminal is terminal.** Once a replication has written a terminal report,
  every later stage is mechanically disabled, and ``TERMINAL_SENTENCE``
  travels with the refusal.
* **One study.** A record belongs to the study whose id it carries. A record
  from another revision is refused *where it is read*, not merely absent from
  the path it is looked for in.
* **No post-freeze mutation.** Once ``GATE_5_FREEZE`` has passed, nothing at
  or before it may be rewritten.
* **No open decision.** §34.

**Gate 5 is unreachable while the pre-freeze audit fails**, and that needs no
special rule: ``PREFREEZE_AUDIT`` is Gate 5's registered predecessor, and a
predecessor that did not record ``PASS`` stops the successor. That is the
whole reason §18 made the audit a stage rather than a tool.
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

from dci1v6.engine.paths import ModelTree
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions

__all__ = ["PREDECESSOR", "assert_own_study", "log_transition",
           "transition_rows", "terminal_status", "read_stage_record",
           "stage_reached", "assert_predecessor_passed",
           "assert_transition_legal", "assert_no_post_freeze_mutation",
           "on_the_wire", "write_stage_record", "write_terminal_report",
           "assert_decisions_permit"]

#: stage -> the stage that must have PASSED before it may run.
PREDECESSOR: dict[str, str | None] = {
    stage: C.STAGE_SEQUENCE[index - 1] if index else None
    for index, stage in enumerate(C.STAGE_SEQUENCE)}
assert PREDECESSOR[C.STAGE_GATE5] == C.STAGE_PREFREEZE_AUDIT, (
    "§18: Gate 5 is unreachable while the pre-freeze audit has not passed, "
    "and that is enforced by the audit being its predecessor")


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
        "open_decisions": list(decisions.open_decisions()),
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


def assert_own_study(tree: ModelTree, stage: str,
                     payload: Mapping[str, Any]) -> None:
    """A record belongs to the study whose id it carries.

    v5's lifecycle runs beside a **completed** v4r4 whose signed records reach
    ``UNMASKED_ANALYSIS``. The path and the signing key already keep them
    apart; this keeps them apart at the point of reading, which is the check
    that still holds if a record is ever copied. A payload with no
    ``study_id`` is refused for the same reason: every record v5 writes
    carries one.
    """
    declared = payload.get("study_id")
    if declared == tree.context.study_id:
        return
    raise IntegrityError(
        f"{tree.model_key}: the {stage} record declares study_id "
        f"{declared!r} and this study is {tree.context.study_id!r}. A record "
        "from another revision is evidence of that revision and never a "
        "predecessor here; v4r4 evidence enters v5 only through the reuse "
        "ledger of protocol/reuse_ledger.py, as DEVELOPMENT_EVIDENCE")


def read_stage_record(tree: ModelTree, stage: str) -> dict[str, Any]:
    """The signed record's payload, hash and signature both verified."""
    path = tree.stage_record(stage)
    if not path.exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} record missing at {path}")
    record = fs.read_json(path)
    payload = verify_signed(record, tree.context.signing_key_path,
                            where=f"{tree.model_key}:{stage}")
    assert_own_study(tree, stage, payload)
    # Observation only, and only when a harness asked for it: `track` returns
    # the payload unchanged unless `run/field_access` is recording, and the
    # wrapper it returns then is a dict subclass that alters no value. See
    # `run/field_access` for why a declared reader is not a read.
    from dci1v6.run import field_access
    return field_access.track(stage, payload)


def stage_reached(tree: ModelTree) -> str | None:
    """The furthest stage with a record, in registered order."""
    reached = None
    for stage in C.STAGE_SEQUENCE:
        if tree.stage_record(stage).exists():
            reached = stage
    return reached


def assert_decisions_permit(stage: str) -> None:
    """§34: a stage may not run while a decision it depends on is open."""
    decisions.assert_decisions_closed_for_stage(stage)


def assert_predecessor_passed(tree: ModelTree, stage: str) -> dict[str, Any]:
    """Verify the predecessor's PASS record: hash, signature and outcome."""
    if stage not in PREDECESSOR:
        raise ProtocolError(f"{stage!r} is not a registered v5 stage")
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
    """§18.1: after the freeze passes, nothing at or before it is rewritten.

    A later write to a stage the freeze already bound would change what the
    freeze record refers to without changing the freeze record, which is
    precisely the silent post-freeze mutation §18.1 exists to make impossible.
    """
    freeze = tree.stage_record(C.STAGE_GATE5)
    if not freeze.exists():
        return
    order = list(C.STAGE_SEQUENCE)
    if order.index(stage) <= order.index(C.STAGE_GATE5):
        raise IntegrityError(
            f"{tree.model_key}: {C.STAGE_GATE5} has passed, so {stage} is "
            "frozen. A scientific change now requires a new protocol "
            "revision, not a rewritten record")


def assert_transition_legal(tree: ModelTree, stage: str) -> None:
    """A stage may run once, in order, with its predecessor passed --- and
    only when every §34 decision it depends on is closed."""
    assert_decisions_permit(stage)
    if tree.stage_record(stage).exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} already has a record; v5 stage "
            "records are write-once. Repair creates a new producing commit "
            "and runs the stage in a fresh tree")
    assert_no_post_freeze_mutation(tree, stage)
    assert_predecessor_passed(tree, stage)


def on_the_wire(payload: dict[str, Any]) -> dict[str, Any]:
    """The payload as a reader will get it back, and what must be signed.

    ``canonical_json`` sorts keys, and a Python dict keyed by integers sorts
    them numerically --- 512, 768, 1024. JSON has no integer keys, so a reader
    gets "512", "768", "1024" and canonicalises them lexicographically. The
    two orders hash differently, so a record signed over the in-memory object
    and verified over the file it was written to disagrees with no tampering
    anywhere. Signing the wire form removes the class of defect rather than
    the instance.
    """
    return json.loads(canonical_json(payload))


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
    declared_study = payload.get("study_id")
    if declared_study is None:
        payload = {**payload, "study_id": tree.context.study_id}
    elif declared_study != tree.context.study_id:
        raise IntegrityError(
            f"record payload declares study_id {declared_study!r} and this "
            f"context is {tree.context.study_id!r}; a record belongs to the "
            "study that produced it and is never re-stamped")
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
    """§28.3's terminal record, carrying the registered sentence verbatim."""
    status = payload.get("status")
    if status not in C.TERMINAL_STATUSES:
        raise ProtocolError(
            f"{status!r} is not a registered v5 terminal status. "
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
