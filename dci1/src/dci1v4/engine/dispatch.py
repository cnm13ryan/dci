"""Fail-closed stage dispatch (§18, §10.6).

One entry point for every stage command. Before any mutation it:

1. refuses to run at all if the replication is terminal;
2. verifies the predecessor PASS record's content hash **and** signature;
3. re-verifies the frozen canonical verifier hash for this entry point;
4. asserts a clean worktree and that every invoked source belongs to the
   producing commit;
5. records the attempted transition, whatever its outcome.

Terminal statuses are *values*, not exceptions in flight: a stage body raises
``TerminalStatus`` carrying its record, the dispatcher writes the terminal
report and logs the transition, and every later generation command is
mechanically disabled from then on.
"""
from __future__ import annotations

from typing import Any, Callable

from dci1v4.engine import fs, store, gitinfo, transitions
from dci1v4.engine.binding import require_frozen_verifier
from dci1v4.engine.environment import environment_digest, environment_record
from dci1v4.engine.paths import ModelTree
from dci1v4.protocol.hashing import sha_file
from dci1v4.errors import IntegrityError, TerminalStatus
from dci1v4.protocol import constants as C

#: stage -> the §10.6 entry point whose binding it runs under.
STAGE_ENTRY_POINT = {
    C.STAGE_QUALIFIED: "scoring",
    C.STAGE_GATE0: "confirmatory_generation",
    C.STAGE_REGIME: "ladder_screen",
    C.STAGE_GATE1: "scoring",
    C.STAGE_GATE2: "solo_calibration",
    C.STAGE_GATE3: "reference_admission",
    C.STAGE_GATE4: "composed_headroom",
    C.STAGE_GATE5: "freeze",
    C.STAGE_CONFIRMATORY: "confirmatory_generation",
    C.STAGE_MASKED_ANALYSIS: "analysis",
    C.STAGE_UNMASKING: "unmasking",
    C.STAGE_UNMASKED_ANALYSIS: "report_generation",
}


def frozen_verifier_hash(tree: ModelTree) -> str | None:
    """The hash frozen in this model's Gate 1 record, or None before it."""
    path = tree.stage_record(C.STAGE_GATE1)
    if not path.exists():
        return None
    payload = transitions.read_stage_record(tree, C.STAGE_GATE1)
    return payload.get("verifier_source_hash")



def _mirror(tree: ModelTree) -> None:
    """Replicate to durable storage AFTER the record exists, and verify.

    The stage bodies used to call ``store.replicate`` themselves and then
    return, so the signed stage record and its transition-log entry -- written
    by this function afterwards -- were the two files guaranteed *not* to reach
    the mirror. Four ``regime_screen.json`` records and the registration
    manifest were found with no second copy at all. Replication belongs on the
    way out, not inside the body, and it is verified rather than assumed.
    """
    store.replicate(tree.root, tree.durable)
    store.assert_replicated(tree.root, tree.durable)


def run_stage(tree: ModelTree, stage: str,
              body: Callable[[dict[str, Any]], dict[str, Any]], *,
              entry_point: str | None = None,
              require_clean_tree: bool = True) -> dict[str, Any]:
    """Execute one stage under the full §18 preconditions."""
    if stage not in C.STAGE_SEQUENCE:
        raise IntegrityError(f"{stage!r} is not a registered v4 stage")
    entry_point = entry_point or STAGE_ENTRY_POINT[stage]

    context = tree.context
    environment = environment_record(context)
    digest = environment_digest(environment)
    commit = gitinfo.head_commit(context.repo_root)

    try:
        transitions.assert_transition_legal(tree, stage)
        predecessor = transitions.assert_predecessor_passed(tree, stage)
        verifier_hash = require_frozen_verifier(entry_point,
                                                frozen_verifier_hash(tree))
        if require_clean_tree:
            gitinfo.assert_clean_worktree(context.repo_root)
            gitinfo.assert_sources_in_commit(context.repo_root, commit)
    except Exception as error:
        transitions.log_transition(
            tree, stage=stage, outcome="REFUSED", producing_commit=commit,
            environment_digest=digest, detail={"error": str(error)})
        raise

    ctx = {"tree": tree, "stage": stage, "entry_point": entry_point,
           "predecessor": predecessor, "verifier_source_hash": verifier_hash,
           "producing_commit": commit, "environment": environment,
           "environment_digest": digest}

    try:
        payload = body(ctx)
    except TerminalStatus as terminal:
        record = {**terminal.record, "model_key": tree.model_key,
                  "producing_commit": commit, "environment_digest": digest,
                  "verifier_source_hash": verifier_hash}
        transitions.write_terminal_report(tree, record)
        transitions.log_transition(
            tree, stage=stage, outcome=terminal.status,
            producing_commit=commit, environment_digest=digest,
            detail={"terminal": True})
        _mirror(tree)
        return {"outcome": terminal.status, "terminal": True,
                "record": record}
    except Exception as error:
        transitions.log_transition(
            tree, stage=stage, outcome="FAILED", producing_commit=commit,
            environment_digest=digest, detail={"error": str(error)})
        raise

    payload = {**payload, "stage": stage, "model_key": tree.model_key,
               "outcome": payload.get("outcome", "PASS"),
               "artifact_type": C.STAGE_ARTIFACT_TYPE[stage],
               "verifier_source_hash": verifier_hash,
               "producing_commit": commit, "environment_digest": digest,
               "namespace": context.namespace}
    path = transitions.write_stage_record(tree, stage, payload)
    transitions.log_transition(
        tree, stage=stage, outcome=payload["outcome"],
        producing_commit=commit, environment_digest=digest,
        output_hash=sha_file(path),
        detail={"identification_statuses":
                payload.get("identification_statuses", [])})
    _mirror(tree)
    return {"outcome": payload["outcome"], "terminal": False,
            "record": fs.read_json(path)["payload"], "path": str(path)}
