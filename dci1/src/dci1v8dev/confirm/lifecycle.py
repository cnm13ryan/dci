"""The confirmatory stage machine: seven stages, in order, once, signed.

The pilot's rules (``dci1v8dev.run.lifecycle`` / ``transitions``), carried
verbatim onto this layer's own stage table: every attempted transition is
logged, refusals included; a record is write-once; a terminal status is
written before the traceback leaves; the two instrument hashes are
re-read at entry and exit. What is new is the **freeze protection**: once
``FROZEN`` exists, ``assert_no_post_freeze_mutation`` refuses any write at
or before it, and every later stage asserts its inputs against the freeze
hash it was signed under.

A confirm root is a ``StudyContext`` in the ``confirm`` (pinned backend) or
``confirm-synthetic`` (stand-in generator) namespace. It carries the same
study id as a pilot root, lives under its own ``dci1v8-confirm-*`` tree,
and holds records under stage names no pilot reader looks for.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from dci1v4.engine import fs, store
from dci1v4.engine.signing import sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import canonical_json

from dci1v8dev.run import stages as PS
from dci1v8dev.run.context import (REPO_ROOT, STUDY_ID, SYNTHETIC_STUDY_ID,
                                   StudyContext, EVIDENCE_DIRNAME)
from dci1v8dev.run.lifecycle import (environment_record, instrument_hashes,
                                     now, stage_provenance)
from dci1v8dev.confirm import CLASSIFICATION

__all__ = [
    "STAGE_REGISTERED", "STAGE_TOPUP", "STAGE_MEMBERSHIP", "STAGE_FROZEN",
    "STAGE_GENERATION", "STAGE_ANALYSIS", "STAGE_REPORT", "STAGE_SEQUENCE",
    "STAGE_RECORD_FILES", "STAGE_ARTIFACT_TYPE", "GENERATION_STAGES",
    "PROTECTED_STAGES", "TERMINAL_STATUSES", "PREDECESSOR", "NAMESPACES",
    "ConfirmTree", "confirm_context", "confirm_tree", "TerminalStatus",
    "StageOutcome", "run_stage", "read_stage_record", "stage_reached",
    "terminal_status", "assert_transition_legal", "write_stage_record",
    "assert_no_post_freeze_mutation", "log_transition", "transition_rows",
    "MANIFEST_FILENAME", "CLASSIFICATION",
]

STAGE_REGISTERED = "CONFIRM_REGISTERED"
STAGE_TOPUP = "LOCAL_TOPUP"
STAGE_MEMBERSHIP = "MEMBERSHIP"
STAGE_FROZEN = "FROZEN"
STAGE_GENERATION = "CONFIRMATORY_GENERATION"
STAGE_ANALYSIS = "CONFIRMATORY_ANALYSIS"
STAGE_REPORT = "FINAL_REPORT"
STAGE_SEQUENCE = (STAGE_REGISTERED, STAGE_TOPUP, STAGE_MEMBERSHIP,
                  STAGE_FROZEN, STAGE_GENERATION, STAGE_ANALYSIS,
                  STAGE_REPORT)
assert len(STAGE_SEQUENCE) == 7
STAGE_RECORD_FILES = {
    STAGE_REGISTERED: "confirm_registration.json",
    STAGE_TOPUP: "local_topup.json",
    STAGE_MEMBERSHIP: "membership.json",
    STAGE_FROZEN: "freeze.json",
    STAGE_GENERATION: "confirmatory_generation.json",
    STAGE_ANALYSIS: "confirmatory_analysis.json",
    STAGE_REPORT: "final_report.json",
}
STAGE_ARTIFACT_TYPE = {
    STAGE_REGISTERED: "registration_record",
    STAGE_TOPUP: "calibration_record",
    STAGE_MEMBERSHIP: "membership_record",
    STAGE_FROZEN: "freeze_record",
    STAGE_GENERATION: "confirmatory_record",
    STAGE_ANALYSIS: "analysis_record",
    STAGE_REPORT: "final_report",
}
#: The stages that generate. ``LOCAL_TOPUP`` generates load-0/1 cells only;
#: ``CONFIRMATORY_GENERATION`` is the one stage in v8 that renders a
#: composed cell, and it does so under a verified freeze.
GENERATION_STAGES = (STAGE_TOPUP, STAGE_GENERATION)
#: Stages whose records carry, or are computed from, a protected outcome.
PROTECTED_STAGES = (STAGE_GENERATION, STAGE_ANALYSIS, STAGE_REPORT)
TERMINAL_STATUSES = ("APPARATUS_FAILURE", "NOT_ELIGIBLE",
                     "FREEZE_REFUSED", "GENERATION_INCOMPLETE")
TERMINAL_SENTENCE = ("a terminal confirmatory status is a statement about "
                     "the apparatus or the design's admissibility for this "
                     "replication and carries no evidence about the effect")
PREDECESSOR: dict[str, str | None] = {
    stage: STAGE_SEQUENCE[i - 1] if i else None
    for i, stage in enumerate(STAGE_SEQUENCE)}
NAMESPACES = PS.CONFIRM_NAMESPACES
MANIFEST_FILENAME = "confirm_manifest.json"


def confirm_context(root: Path, *, synthetic: bool = False,
                    repo_root: Path | str | None = None) -> StudyContext:
    root = Path(root)
    return StudyContext(
        namespace="confirm-synthetic" if synthetic else "confirm",
        study_id=SYNTHETIC_STUDY_ID if synthetic else STUDY_ID,
        repo_root=Path(repo_root) if repo_root is not None else REPO_ROOT,
        evidence_root=root / "evidence", durable_root=root / "durable")


@dataclass(frozen=True)
class ConfirmTree:
    """One replication's confirmatory evidence tree, in both roots."""

    context: StudyContext
    model_key: str

    def __post_init__(self):
        if self.context.namespace not in NAMESPACES:
            raise ProtocolError(
                f"a confirm tree needs a confirm namespace, not "
                f"{self.context.namespace!r}")

    @property
    def synthetic(self) -> bool:
        return self.context.namespace == "confirm-synthetic"

    @property
    def root(self) -> Path:
        return self.context.model_root(self.model_key)

    @property
    def durable(self) -> Path:
        return (Path(self.context.durable_root) / EVIDENCE_DIRNAME
                / self.model_key)

    @property
    def registration_manifest(self) -> Path:
        return self.context.registration_root / MANIFEST_FILENAME

    def stage_dir(self, stage: str) -> Path:
        if stage not in STAGE_RECORD_FILES:
            raise ProtocolError(f"{stage!r} is not a v8 confirmatory stage")
        return self.root / stage

    def stage_record(self, stage: str) -> Path:
        return self.stage_dir(stage) / "records" / STAGE_RECORD_FILES[stage]

    def stage_record_reader_copy(self, stage: str) -> Path:
        return self.stage_dir(stage) / STAGE_RECORD_FILES[stage]

    def backend_runs(self, stage: str) -> Path:
        return self.stage_dir(stage) / "backend_runs"

    @property
    def transition_log(self) -> Path:
        return self.root / "transition_log.jsonl"

    @property
    def terminal_report(self) -> Path:
        return self.root / "terminal_report.json"


def confirm_tree(context: StudyContext, model_key: str) -> ConfirmTree:
    from dci1v4.models.registry import get_model
    get_model(model_key)
    return ConfirmTree(context=context, model_key=model_key)


class TerminalStatus(Exception):
    def __init__(self, status: str, *, gate: str, criterion: str,
                 observed: Any, strongest_permissible_statement: str):
        if status not in TERMINAL_STATUSES:
            raise ProtocolError(f"{status!r} is not a confirmatory terminal "
                                f"status; registered: {TERMINAL_STATUSES}")
        super().__init__(f"{gate}: {status}")
        self.status, self.gate = status, gate
        self.criterion, self.observed = criterion, observed
        self.strongest_permissible_statement = strongest_permissible_statement

    def payload(self, model_key: str, producing_commit: str) -> dict[str, Any]:
        return {"status": self.status, "model_key": model_key,
                "gate": self.gate, "criterion": self.criterion,
                "observed": self.observed,
                "producing_commit": producing_commit,
                "strongest_permissible_statement":
                    self.strongest_permissible_statement}


@dataclass(frozen=True)
class StageOutcome:
    stage: str
    outcome: str
    payload: dict[str, Any]
    record_path: Path | None
    terminal: str | None = None


# ------------------------------------------------------------ transitions
def log_transition(tree: ConfirmTree, *, stage: str, outcome: str,
                   producing_commit: str, environment_digest: str,
                   detail: dict[str, Any] | None = None) -> dict[str, Any]:
    row = fs.row_with_hash({
        "timestamp": now(), "stage": stage, "outcome": outcome,
        "study_id": tree.context.study_id, "model_key": tree.model_key,
        "namespace": tree.context.namespace, "layer": "confirm",
        "producing_commit": producing_commit,
        "environment_digest": environment_digest, "detail": detail or {}})
    fs.append_jsonl(tree.transition_log, row)
    return row


def transition_rows(tree: ConfirmTree) -> list[dict[str, Any]]:
    if not tree.transition_log.exists():
        return []
    rows = fs.read_jsonl(tree.transition_log)
    for row in rows:
        fs.verify_row_hash(row, where=f"transition:{row.get('stage')}")
    return rows


def terminal_status(tree: ConfirmTree) -> str | None:
    if not tree.terminal_report.exists():
        return None
    record = fs.read_json(tree.terminal_report)
    return record.get("payload", record).get("status")


def read_stage_record(tree: ConfirmTree, stage: str) -> dict[str, Any]:
    path = tree.stage_record(stage)
    if not path.exists():
        raise IntegrityError(f"{tree.model_key}: {stage} record missing at "
                             f"{path}")
    payload = verify_signed(fs.read_json(path), tree.context.signing_key_path,
                            where=f"{tree.model_key}:{stage}")
    if payload.get("study_id") != tree.context.study_id:
        raise IntegrityError(
            f"{tree.model_key}: the {stage} record declares study_id "
            f"{payload.get('study_id')!r}; this study is "
            f"{tree.context.study_id!r}")
    if payload.get("layer") != "confirm":
        raise IntegrityError(f"{tree.model_key}: the {stage} record is not a "
                             "confirmatory-layer record")
    return payload


def stage_reached(tree: ConfirmTree) -> str | None:
    reached = None
    for stage in STAGE_SEQUENCE:
        if tree.stage_record(stage).exists():
            reached = stage
    return reached


def assert_no_post_freeze_mutation(tree: ConfirmTree, stage: str) -> None:
    """Once ``FROZEN`` exists, no stage at or before it may write."""
    if not tree.stage_record(STAGE_FROZEN).exists():
        return
    if STAGE_SEQUENCE.index(stage) <= STAGE_SEQUENCE.index(STAGE_FROZEN):
        raise IntegrityError(
            f"{tree.model_key}: {stage} may not write after the freeze; the "
            "frozen design is immutable and a repair takes a fresh root")


def assert_transition_legal(tree: ConfirmTree, stage: str) -> None:
    if stage not in STAGE_SEQUENCE:
        raise ProtocolError(f"{stage!r} is not a v8 confirmatory stage")
    if tree.stage_record(stage).exists():
        raise IntegrityError(
            f"{tree.model_key}: {stage} already has a record; confirmatory "
            "records are write-once. Repair runs in a fresh root")
    assert_no_post_freeze_mutation(tree, stage)
    status = terminal_status(tree)
    if status is not None:
        raise IntegrityError(
            f"{tree.model_key} is terminal at {status}; every later stage is "
            f"mechanically disabled ({TERMINAL_SENTENCE})")
    predecessor = PREDECESSOR[stage]
    if predecessor is None:
        return
    payload = read_stage_record(tree, predecessor)
    if payload.get("outcome") != "PASS":
        raise IntegrityError(
            f"{tree.model_key}: {predecessor} recorded "
            f"{payload.get('outcome')!r}, not PASS; {stage} may not run")


def write_stage_record(tree: ConfirmTree, stage: str,
                       payload: dict[str, Any]) -> Path:
    if payload.get("stage") != stage:
        raise ProtocolError(f"record payload declares stage "
                            f"{payload.get('stage')!r}, not {stage!r}")
    if payload.get("artifact_type") != STAGE_ARTIFACT_TYPE[stage]:
        raise IntegrityError(
            f"artifact type {payload.get('artifact_type')!r} disagrees with "
            f"stage {stage!r}")
    payload = json.loads(canonical_json({**payload,
                                         "study_id": tree.context.study_id,
                                         "layer": "confirm"}))
    signed = sign_payload(payload, tree.context.signing_key_path)
    verify_signed(signed, tree.context.signing_key_path,
                  f"{tree.model_key}:{stage}:at-write")
    path = tree.stage_record(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, signed)
    reader = tree.stage_record_reader_copy(stage)
    fs.write_json(reader, payload)
    return path


def write_terminal_report(tree: ConfirmTree, payload: dict[str, Any]) -> Path:
    payload = {**payload, "terminal_sentence": TERMINAL_SENTENCE,
               "study_id": tree.context.study_id, "layer": "confirm"}
    path = tree.terminal_report
    path.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(path, sign_payload(payload,
                                          tree.context.signing_key_path))
    return path


def mirror(tree: ConfirmTree, stage: str) -> dict[str, str]:
    source = tree.stage_dir(stage)
    if not source.exists():
        return {}
    durable = tree.durable / stage
    fingerprint = store.replicate(source, durable)
    store.assert_replicated(source, durable)
    return fingerprint


def protocol_identity(tree: ConfirmTree, stage: str) -> dict[str, Any]:
    out: dict[str, Any] = {"study_id": tree.context.study_id, "stage": stage,
                           "layer": "confirm", "registration": None,
                           "freeze": None}
    if tree.stage_record(STAGE_REGISTERED).exists():
        out["registration"] = read_stage_record(
            tree, STAGE_REGISTERED).get("manifest_hash")
    if tree.stage_record(STAGE_FROZEN).exists():
        out["freeze"] = fs.read_json(tree.stage_record(STAGE_FROZEN))[
            "record_hash"]
    return out


def run_stage(tree: ConfirmTree, stage: str, *,
              compute: Callable[[dict[str, Any]], dict[str, Any]],
              producing_commit: str, environment_digest: str) -> StageOutcome:
    """Guard, compute, sign, mirror, log --- the one way a stage runs."""
    provenance = stage_provenance(tree.context.repo_root,
                                  namespace=tree.context.namespace,
                                  producing_commit=producing_commit)
    producing_commit = provenance["producing_commit"]
    environment = environment_record(environment_digest)
    entry = instrument_hashes()
    try:
        assert_transition_legal(tree, stage)
    except Exception as exc:
        log_transition(tree, stage=stage, outcome="REFUSED",
                       producing_commit=producing_commit,
                       environment_digest=environment_digest,
                       detail={"error": type(exc).__name__,
                               "message": str(exc)[:2000]})
        raise
    predecessor = PREDECESSOR[stage]
    previous = read_stage_record(tree, predecessor) if predecessor else {}
    try:
        payload = compute(previous)
    except TerminalStatus as terminal:
        write_terminal_report(tree, terminal.payload(tree.model_key,
                                                     producing_commit))
        log_transition(tree, stage=stage, outcome="TERMINAL",
                       producing_commit=producing_commit,
                       environment_digest=environment_digest,
                       detail={"status": terminal.status,
                               "gate": terminal.gate})
        raise
    if instrument_hashes() != entry:
        raise ProtocolError(
            f"the v8 verifier or wording hash moved while {stage} was "
            "running; the stage fails closed")
    payload.setdefault("stage", stage)
    payload.setdefault("artifact_type", STAGE_ARTIFACT_TYPE[stage])
    payload.setdefault("namespace", tree.context.namespace)
    payload.setdefault("model_key", tree.model_key)
    payload.setdefault("classification", CLASSIFICATION)
    payload["producing_commit"] = producing_commit
    payload.setdefault("environment_digest", environment_digest)
    payload["provenance"] = provenance
    payload["environment"] = environment
    payload.setdefault("verifier_hash", entry["verifier_hash"])
    payload.setdefault("wording_hash", entry["wording_hash"])
    payload.setdefault("recorded_at", now())
    outcome = str(payload.setdefault("outcome", "PASS"))
    path = write_stage_record(tree, stage, payload)
    mirror(tree, stage)
    log_transition(tree, stage=stage, outcome=outcome,
                   producing_commit=producing_commit,
                   environment_digest=environment_digest,
                   detail={"record": path.name})
    return StageOutcome(stage=stage, outcome=outcome, payload=payload,
                        record_path=path)
