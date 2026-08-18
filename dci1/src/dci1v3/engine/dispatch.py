"""The canonical dispatcher (item 5). Every mutating registered operation
follows exactly one production path:

    public entrypoint -> canonical dispatcher -> exclusive writer lock
    -> clean-worktree check -> canonical evidence verification
    -> state and predecessor validation -> production stage function
    -> canonical evidence writer -> durable write -> content-hash
    verification -> artifact acceptance -> signed stage or operation record
    -> append-only transition log

Registered commands never call generation, storage, selection, masking,
analysis, or reporting implementations directly; they name an operation and
the dispatcher runs this path. A ``TerminalStatus`` raised by a stage
function becomes the mandatory terminal report of §26.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from dci1v3.engine import gitinfo, store, transitions
from dci1v3.engine.context import StudyContext
from dci1v3.engine.environment import environment_digest, environment_record
from dci1v3.engine.locks import WriterLock
from dci1v3.engine.paths import ModelTree, model_tree
from dci1v3.engine.verify import verify_evidence
from dci1v3.errors import IntegrityError, ProtocolError, TerminalStatus
from dci1v3.models.registry import ModelSpec, get_model
from dci1v3.protocol import constants as C


@dataclass
class Job:
    """What a production stage function receives."""

    context: StudyContext
    tree: ModelTree
    spec: ModelSpec
    producing_commit: str
    environment: dict[str, Any]
    environment_digest: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Operation:
    name: str
    stage: str | None                 # stage record produced, if any
    handler: Callable[[Job], dict[str, Any]]
    mutating: bool = True

REGISTRY: dict[str, Operation] = {}


def operation(name: str, *, stage: str | None, mutating: bool = True):
    def register(fn: Callable[[Job], dict[str, Any]]):
        if name in REGISTRY:
            raise ProtocolError(f"operation {name!r} registered twice")
        REGISTRY[name] = Operation(name=name, stage=stage, handler=fn,
                                   mutating=mutating)
        return fn
    return register


def verifier_binding_required(op: Operation) -> bool:
    """Whether an operation's scientific validity depends on the Gate-1
    verifier freeze: every stage from Gate 2A onward, plus the greedy
    replication — the one non-stage command that scores newly generated
    rows. GATE_1 itself is excluded: its approval path performs its own
    drift check with the registered calibration-supersession handling."""
    if op.name == "greedy":
        return True
    return op.stage is not None and \
        C.STAGE_SEQUENCE.index(op.stage) > \
        C.STAGE_SEQUENCE.index(C.STAGE_GATE1)


def assert_verifier_binding(context: StudyContext) -> None:
    """Post-Gate-1 instrument integrity: the current verifier sources
    must be byte-identical to the signed verifier-freeze manifest before
    any downstream mutation. Fails closed when the manifest is missing
    or unverifiable, and never rewrites the manifest — reconciling a
    drift is an audited supersession-and-recalibration decision."""
    from dci1v3.engine import fs
    from dci1v3.engine.signing import verify_signed
    from dci1v3.stages.autorater import assert_verifier_unchanged

    manifest_path = context.study_root / "verifier_freeze.json"
    if not manifest_path.exists():
        raise IntegrityError(
            "post-Gate-1 operations require the signed verifier-freeze "
            f"manifest; missing from {manifest_path}")
    payload = verify_signed(fs.read_json(manifest_path),
                            context.signing_key_path,
                            where="verifier_freeze")
    assert_verifier_unchanged(payload)


def _assert_execution_order(context: StudyContext, model_key: str) -> None:
    """Item 15: E2B runs first; its stop statuses prevent the remaining
    replications from starting."""
    from dci1v3.models.registry import E2B_STOP_STATUSES, FIRST_MODEL_KEY

    if model_key == FIRST_MODEL_KEY:
        return
    first = model_tree(context, FIRST_MODEL_KEY)
    if transitions.load_stage_record(first, C.STAGE_QUALIFIED) is None:
        raise ProtocolError(
            f"{FIRST_MODEL_KEY} runs first (registered execution order); "
            f"{model_key} cannot start before its qualification")
    status = transitions.terminal_status(first)
    if status in E2B_STOP_STATUSES:
        raise ProtocolError(
            f"{FIRST_MODEL_KEY} terminated with {status}; the remaining v3 "
            f"replications do not start (redesign requires v4)")


def dispatch(context: StudyContext, name: str, model_key: str,
             **options: Any) -> dict[str, Any]:
    if name not in REGISTRY:
        raise ProtocolError(f"unknown operation {name!r}; registered: "
                            f"{sorted(REGISTRY)}")
    op = REGISTRY[name]
    tree = model_tree(context, model_key)
    spec = get_model(model_key)

    if not op.mutating:
        job = Job(context=context, tree=tree, spec=spec,
                  producing_commit="", environment={},
                  environment_digest="", options=options)
        return op.handler(job)

    _assert_execution_order(context, model_key)
    with WriterLock(context.lock_dir, context.study_id, model_key, op.name):
        gitinfo.assert_clean_worktree(context.repo_root)
        commit = gitinfo.head_commit(context.repo_root)
        gitinfo.assert_sources_in_commit(context.repo_root, commit)
        verify_evidence(tree)
        if op.stage is not None:
            transitions.assert_transition_allowed(tree, op.stage)
        else:
            transitions.assert_generation_allowed(tree)
        if verifier_binding_required(op):
            assert_verifier_binding(context)
        env = environment_record(context)
        job = Job(context=context, tree=tree, spec=spec,
                  producing_commit=commit, environment=env,
                  environment_digest=environment_digest(env),
                  options=options)
        try:
            result = op.handler(job)
        except TerminalStatus as terminal:
            record = transitions.write_terminal_report(
                tree, status=terminal.status, body=terminal.payload,
                producing_commit=commit,
                environment_digest=job.environment_digest)
            store.replicate(tree.root, tree.durable)
            store.assert_replicated(tree.root, tree.durable)
            return {"outcome": "TERMINAL", "status": terminal.status,
                    "record_hash": record["record_hash"]}
        except BaseException:
            # A failed or pending operation still leaves its committed
            # bytes durable, so verification keeps running against current
            # durable state on the next attempt.
            store.replicate(tree.root, tree.durable)
            raise
        if op.stage is not None:
            record = transitions.write_stage_record(
                tree, op.stage,
                status=result.get("status", "PASSED"),
                body=result.get("body", {}),
                producing_commit=commit,
                environment_digest=job.environment_digest,
                input_hashes=result.get("input_hashes", {}),
                output_hashes=result.get("output_hashes", {}))
            outcome: dict[str, Any] = {
                "outcome": result.get("status", "PASSED"),
                "stage": op.stage, "record_hash": record["record_hash"]}
        else:
            transitions.append_transition(tree, {
                "operation": op.name,
                "outcome": result.get("status", "COMPLETED"),
                "model_revision": spec.revision,
                "producing_commit": commit,
                "environment_digest": job.environment_digest,
                "input_hashes": result.get("input_hashes", {}),
                "output_hashes": result.get("output_hashes", {})})
            outcome = {"outcome": result.get("status", "COMPLETED"),
                       "operation": op.name}
        store.replicate(tree.root, tree.durable)
        store.assert_replicated(tree.root, tree.durable)
        verify_evidence(tree)
        outcome["body"] = result.get("body", {})
        return outcome
