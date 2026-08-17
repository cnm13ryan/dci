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
from dci1v3.errors import ProtocolError, TerminalStatus
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
