"""The one way a v5 stage runs: guard, compute, sign, mirror, log.

Every runner in this package is the same five steps in the same order, and
they are here rather than in each runner so that a stage cannot be written
that skips one:

1. ``assert_transition_legal`` --- §18's four rules and §34's decisions. A
   stage may run once, in order, with its predecessor's record verified, and
   only while no decision it depends on is open.
2. ``verifier_source_hash`` --- §10.6's binding, re-read at entry and again
   after the payload is built. A hash that moved mid-stage fails the stage
   closed.
3. the stage's own computation, which is the only part a runner writes.
4. ``write_stage_record`` --- sign, write once, write the reader copy.
5. ``store.replicate`` --- §26's durable mirror, and the transition log.

**The refusal is logged too.** ``log_transition`` runs on the way out
whichever way the stage went, so an illegal attempt leaves a row saying which
decisions were open when it was made. A log that recorded only successes
would make the interesting event invisible.

**A terminal status is a return value, not an exception that escapes.**
``TerminalStatus`` is raised by a stage's computation, caught here, written to
the terminal report and re-raised, so that the record exists before the
traceback reaches a caller who might not write one.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import store
from dci1v4.errors import ProtocolError

from dci1v6.engine import transitions
from dci1v6.engine.paths import ModelTree
from dci1v6.protocol import constants as C
from dci1v6.run import field_access
from dci1v6.verifiers import verifier_source_hash

__all__ = ["TerminalStatus", "StageOutcome", "run_stage", "mirror_records",
           "protocol_identity",
           "mirror_terminal_report", "now", "stage_input",
           "terminal_statuses_in_force", "confirmatory_licensed",
           "frozen_identified_replications"]


def terminal_statuses_in_force() -> tuple[str, ...]:
    """§28's registered terminal statuses, plus the one §34 D6 can add.

    §28's list is written for D6's standing proposal, under which
    ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` is an identification status and
    therefore not terminal. Closing D6 at ``terminal`` **is** the act that
    makes it terminal, so the vocabulary is derived from the closure rather
    than hard-coded to one reading --- and while D6 is open the extra status
    is absent, so a runner cannot raise it by accident.
    """
    from dci1v6.protocol import decisions

    if decisions.value_of("D6") == "terminal":
        return C.TERMINAL_STATUSES + ("REFERENCE_SUPPORT_NOT_IDENTIFIED",)
    return C.TERMINAL_STATUSES


def frozen_identified_replications(context, model_keys) -> list[str]:
    """Replications with a passing ``GATE_5_FREEZE`` record and D6 identified.

    Reads signed records only, and reads them per replication --- §6.1's
    firewall means this counts survivors, it never pools anything and it
    never lets one replication's scientific outcome change another's rules.
    A replication with a terminal report is not a survivor whatever stage it
    reached.
    """
    from dci1v6.engine.paths import model_tree

    survivors: list[str] = []
    for model_key in model_keys:
        tree = model_tree(context, model_key)
        if tree.terminal_report.exists():
            continue
        if not tree.stage_record(C.STAGE_GATE5).exists():
            continue
        try:
            record = transitions.read_stage_record(tree, C.STAGE_GATE5)
        except Exception:                                     # noqa: BLE001
            continue
        if record.get("outcome") == "PASS":
            survivors.append(model_key)
    return survivors


def confirmatory_licensed(*, this_replication_frozen: bool,
                          survivors: Sequence[str]) -> dict[str, Any]:
    """§34 D22 (READINESS R4): what licenses confirmatory generation.

    Both branches exist in the source and neither is reachable while the
    decision is open.

    * ``two_survivors_before_any`` --- no replication may generate until at
      least two have reached ``GATE_5_FREEZE`` identified. The cost is stated
      plainly because it is the reason the decision is open: it withholds
      **every** registered claim from a legitimately identified, frozen
      replication because a *different* replication failed, and §6.1
      registers four replications each analysed separately with no cross-model
      scalar carrying a claim, while L5 --- generalisation --- is never
      licensed by this design. There is no registered study-level claim that
      a two-survivor rule protects.
    * ``per_replication`` --- each independently identified and frozen
      replication may generate its own confirmatory data; two or more
      survivors are required only for replicated or generalised study-level
      statements, and D25 registers before data what v6 says when exactly one
      survives.

    Returns the verdict rather than raising, so the reason is a value the
    caller can put on a record.
    """
    from dci1v6.protocol import decisions

    rule = decisions.choice(
        "D22",
        {"two_survivors_before_any": "two_survivors_before_any",
         "per_replication": "per_replication"},
        where="run.lifecycle.confirmatory_licensed")
    n = len(survivors)
    if rule == "per_replication":
        licensed = bool(this_replication_frozen)
        reason = ("this replication is frozen and identified, so its own "
                  "L1-L4 ladder is licensed; a replicated or generalised "
                  "study-level statement still needs two survivors and L5 "
                  "is never licensed"
                  if licensed else
                  "this replication has no passing GATE_5_FREEZE record")
    else:
        licensed = bool(this_replication_frozen) and n >= 2
        reason = ("two or more replications are frozen and identified"
                  if licensed else
                  f"§34 D22 closed at two_survivors_before_any and {n} "
                  "replication(s) are frozen and identified")
    return {"licensed": licensed, "rule": rule, "survivors": list(survivors),
            "n_survivors": n,
            "this_replication_frozen": bool(this_replication_frozen),
            "reason": reason,
            "l5_withheld": "generalisation is never licensed by this design"}


class TerminalStatus(Exception):
    """A registered §28 terminal status, raised by a stage's computation."""

    def __init__(self, status: str, *, gate: str, criterion: str,
                 observed: Any, strongest_permissible_statement: str):
        in_force = terminal_statuses_in_force()
        if status not in in_force:
            raise ProtocolError(
                f"{status!r} is not a registered v6 terminal status; "
                f"in force: {in_force}")
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
    outcome: str                     # PASS | FAIL
    payload: dict[str, Any]
    record_path: Path | None
    terminal: str | None = None


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def mirror_records(tree: ModelTree, stage: str) -> dict[str, str]:
    """§26: a stage's signed records get a durable copy as soon as they
    exist, not at the end of the study."""
    source = tree.stage_dir(stage)
    durable = tree.durable / stage
    if not source.exists():
        return {}
    fingerprint = store.replicate(source, durable)
    store.assert_replicated(source, durable)
    return fingerprint


def mirror_terminal_report(tree: ModelTree) -> None:
    """A terminal report is a result, and it needs a second copy too."""
    if not tree.terminal_report.exists():
        return
    durable = tree.durable
    durable.mkdir(parents=True, exist_ok=True)
    durable.joinpath(tree.terminal_report.name).write_bytes(
        tree.terminal_report.read_bytes())


def protocol_identity(tree: ModelTree, stage: str) -> dict[str, Any]:
    """What "the same protocol" means for a row generated at ``stage``.

    Part of a row's reuse key (``run/execute.py``): a stored generation may
    satisfy a planned row only when the protocol that planned it is the same
    protocol. Before the freeze that is the signed registration manifest; at
    and after the freeze it is the freeze hash as well, because the freeze is
    what binds the scientific state the confirmatory rows belong to.

    A stage record that does not exist contributes ``None`` rather than being
    skipped, so "no freeze yet" and "a different freeze" are different keys.
    """
    out: dict[str, Any] = {"study_id": tree.context.study_id, "stage": stage}
    for name, source, field in (
            ("registration", C.STAGE_REGISTERED, "manifest_hash"),
            ("freeze", C.STAGE_GATE5, "freeze_hash")):
        if source == C.STAGE_GATE5 and \
                C.STAGE_SEQUENCE.index(stage) < \
                C.STAGE_SEQUENCE.index(C.STAGE_GATE5):
            out[name] = None
            continue
        if tree.stage_record(source).exists():
            out[name] = transitions.read_stage_record(tree, source).get(field)
        else:
            out[name] = None
    return out


def stage_input(tree: ModelTree, stage: str) -> dict[str, Any]:
    """The predecessor's verified payload, which is a runner's only input.

    A runner reads its input **from the record**, never from a value another
    runner happened to still be holding. That is what makes a resumed or
    separately invoked stage identical to one run in sequence, and it is why
    every field a stage needs has to have been written by the stage before it
    --- the property ``run/contracts.py`` audits.
    """
    predecessor = transitions.PREDECESSOR[stage]
    if predecessor is None:
        return {}
    return transitions.read_stage_record(tree, predecessor)


def run_stage(tree: ModelTree, stage: str, *,
              compute: Callable[[dict[str, Any]], dict[str, Any]],
              producing_commit: str, environment_digest: str,
              model_revision: str | None = None) -> StageOutcome:
    """The five steps. ``compute`` receives the predecessor payload."""
    if stage not in C.STAGE_SEQUENCE:
        raise ProtocolError(f"{stage!r} is not a registered v5 stage")
    entry_hash = verifier_source_hash()
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
        with field_access.reading_for(stage):
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
    if verifier_source_hash() != entry_hash:
        raise ProtocolError(
            f"§10.6: the canonical verifier hash moved while {stage} was "
            "running; its record cannot be placed and the stage fails closed")
    payload.setdefault("stage", stage)
    payload.setdefault("artifact_type", C.STAGE_ARTIFACT_TYPE[stage])
    payload.setdefault("study_id", tree.context.study_id)
    payload.setdefault("model_key", tree.model_key)
    payload.setdefault("producing_commit", producing_commit)
    payload.setdefault("environment_digest", environment_digest)
    payload.setdefault("verifier_hash", entry_hash)
    payload.setdefault("recorded_at", now())
    outcome = str(payload.setdefault("outcome", "PASS"))
    path = transitions.write_stage_record(tree, stage, payload)
    mirror_records(tree, stage)
    transitions.log_transition(
        tree, stage=stage, outcome=outcome,
        producing_commit=producing_commit,
        environment_digest=environment_digest,
        model_revision=model_revision,
        output_hash=payload.get("content_hash"),
        detail={"record": str(path.name)})
    return StageOutcome(stage=stage, outcome=outcome, payload=payload,
                        record_path=path)


def assert_reads_only_records(payload: Mapping[str, Any], *,
                              where: str) -> None:
    """A stage record names the records it read, and they are v5's.

    §18's rule is that every command verifies its predecessor's record. This
    is the readable half of it: a record that does not say what it consumed
    cannot be audited for having consumed the right thing, and a record that
    names a foreign study's artifact is refused where it is read.
    """
    sources = payload.get("inputs")
    if not isinstance(sources, Mapping):
        raise ProtocolError(
            f"{where}: the record carries no `inputs` block; every v5 stage "
            "record names the records it read (§18)")
    for name, entry in sources.items():
        study = (entry or {}).get("study_id") if isinstance(entry, Mapping) \
            else None
        if study is not None and study != payload.get("study_id"):
            raise ProtocolError(
                f"{where}: input {name!r} declares study_id {study!r}; a "
                "record from another revision is never a predecessor here")
