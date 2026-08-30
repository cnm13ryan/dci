"""The one way a pilot stage runs: guard, compute, sign, mirror, log.

v7's five steps (``dci1v7.run.lifecycle.run_stage``), with two hashes
re-read at entry and exit instead of one: the v8 **verifier** hash
(``dci1v8dev.verifiers``) and the v8 **wording** hash
(``dci1v8dev.wordings``). A hash that moved while a stage was running fails
the stage closed: the rows it generated could not be placed under one
instrument.

A terminal status is raised by the computation, caught here, written to the
terminal report and re-raised, so the record exists before the traceback
reaches a caller who might not write one.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from dci1v4.engine import store
from dci1v4.errors import ProtocolError

from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.wordings import v8_wording_source_hash

__all__ = ["TerminalStatus", "StageOutcome", "run_stage", "mirror_records",
           "mirror_terminal_report", "protocol_identity", "stage_input",
           "now", "instrument_hashes"]


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def instrument_hashes() -> dict[str, str]:
    """The two hashes that fix what a model is asked and how it is scored."""
    return {"verifier_hash": verifier_source_hash(),
            "wording_hash": v8_wording_source_hash()}


class TerminalStatus(Exception):
    """A registered pilot terminal status, raised by a stage's computation."""

    def __init__(self, status: str, *, gate: str, criterion: str,
                 observed: Any, strongest_permissible_statement: str):
        if status not in S.TERMINAL_STATUSES:
            raise ProtocolError(
                f"{status!r} is not a v8 pilot terminal status; registered: "
                f"{S.TERMINAL_STATUSES}")
        super().__init__(f"{gate}: {status}")
        self.status = status
        self.gate = gate
        self.criterion = criterion
        self.observed = observed
        self.strongest_permissible_statement = strongest_permissible_statement

    def payload(self, model_key: str, producing_commit: str
                ) -> dict[str, Any]:
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


def mirror_records(tree: ModelTree, stage: str) -> dict[str, str]:
    """§26: a stage's signed records get a durable copy as soon as they exist."""
    source = tree.stage_dir(stage)
    durable = tree.durable / stage
    if not source.exists():
        return {}
    fingerprint = store.replicate(source, durable)
    store.assert_replicated(source, durable)
    return fingerprint


def mirror_terminal_report(tree: ModelTree) -> None:
    if not tree.terminal_report.exists():
        return
    tree.durable.mkdir(parents=True, exist_ok=True)
    tree.durable.joinpath(tree.terminal_report.name).write_bytes(
        tree.terminal_report.read_bytes())


def protocol_identity(tree: ModelTree, stage: str) -> dict[str, Any]:
    """What "the same protocol" means for a row generated at ``stage``: the
    study, the stage and the signed pilot manifest's hash (``None`` before
    registration, so the two are different reuse keys)."""
    out: dict[str, Any] = {"study_id": tree.context.study_id, "stage": stage,
                           "registration": None}
    if tree.stage_record(S.STAGE_REGISTERED).exists():
        out["registration"] = transitions.read_stage_record(
            tree, S.STAGE_REGISTERED).get("manifest_hash")
    return out


def stage_input(tree: ModelTree, stage: str) -> dict[str, Any]:
    """The predecessor's verified payload: a runner's only input."""
    predecessor = transitions.PREDECESSOR[stage]
    if predecessor is None:
        return {}
    return transitions.read_stage_record(tree, predecessor)


def run_stage(tree: ModelTree, stage: str, *,
              compute: Callable[[dict[str, Any]], dict[str, Any]],
              producing_commit: str, environment_digest: str,
              model_revision: str | None = None) -> StageOutcome:
    """The five steps. ``compute`` receives the predecessor payload."""
    if stage not in S.STAGE_SEQUENCE:
        raise ProtocolError(f"{stage!r} is not a v8 pilot stage")
    entry = instrument_hashes()
    try:
        transitions.assert_transition_legal(tree, stage)
    except Exception as exc:
        transitions.log_transition(
            tree, stage=stage, outcome="REFUSED",
            producing_commit=producing_commit,
            environment_digest=environment_digest,
            model_revision=model_revision,
            detail={"error": type(exc).__name__, "message": str(exc)[:2000]})
        raise
    previous = stage_input(tree, stage)
    try:
        payload = compute(previous)
    except TerminalStatus as terminal:
        transitions.write_terminal_report(
            tree, terminal.payload(tree.model_key, producing_commit))
        mirror_terminal_report(tree)
        transitions.log_transition(
            tree, stage=stage, outcome="TERMINAL",
            producing_commit=producing_commit,
            environment_digest=environment_digest,
            model_revision=model_revision,
            detail={"status": terminal.status, "gate": terminal.gate})
        raise
    if instrument_hashes() != entry:
        raise ProtocolError(
            f"the v8 verifier or wording hash moved while {stage} was "
            "running; its record cannot be placed and the stage fails closed")
    payload.setdefault("stage", stage)
    payload.setdefault("artifact_type", S.STAGE_ARTIFACT_TYPE[stage])
    payload.setdefault("study_id", tree.context.study_id)
    payload.setdefault("namespace", tree.context.namespace)
    payload.setdefault("model_key", tree.model_key)
    payload.setdefault("producing_commit", producing_commit)
    payload.setdefault("environment_digest", environment_digest)
    payload.setdefault("verifier_hash", entry["verifier_hash"])
    payload.setdefault("wording_hash", entry["wording_hash"])
    payload.setdefault("recorded_at", now())
    outcome = str(payload.setdefault("outcome", "PASS"))
    path = transitions.write_stage_record(tree, stage, payload)
    mirror_records(tree, stage)
    transitions.log_transition(
        tree, stage=stage, outcome=outcome,
        producing_commit=producing_commit,
        environment_digest=environment_digest,
        model_revision=model_revision,
        detail={"record": str(path.name)})
    return StageOutcome(stage=stage, outcome=outcome, payload=payload,
                        record_path=path)
