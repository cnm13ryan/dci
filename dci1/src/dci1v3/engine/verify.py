"""Canonical evidence verification (item 7): one routine, the complete
execution-integrity contract, used by the public command and by every
irreversible registered transition.

Each element of the contract is a named check consumed here, so a declared
execution-constraining field cannot be inert (§28 check 4). Verification
always runs against current durable state; a previous success authorises
nothing.
"""
from __future__ import annotations

from typing import Any, Callable

from dci1v3.engine import fs, gitinfo, store, transitions
from dci1v3.engine.environment import dependency_digest, interpreter_identity
from dci1v3.engine.paths import (
    STAGE_RECORD_FILES,
    ModelTree,
    unexpected_root_files,
)
from dci1v3.engine.signing import verify_signed
from dci1v3.engine.artifacts import artifact_states
from dci1v3.errors import IntegrityError
from dci1v3.models.registry import get_model, registration_models
from dci1v3.protocol import constants as C

CheckFn = Callable[[ModelTree], dict[str, Any]]
NAMED_CHECKS: dict[str, CheckFn] = {}


def _check(name: str):
    def register(fn: CheckFn) -> CheckFn:
        NAMED_CHECKS[name] = fn
        return fn
    return register


def _registration(tree: ModelTree) -> dict[str, Any]:
    path = tree.context.registration_manifest
    if not path.exists():
        raise IntegrityError("registration manifest missing; the study is "
                             "not registered")
    return verify_signed(fs.read_json(path),
                         tree.context.signing_key_path,
                         where="registration manifest")


@_check("protocol_identity")
def _protocol_identity(tree: ModelTree) -> dict[str, Any]:
    manifest = _registration(tree)
    if (manifest.get("protocol"), manifest.get("protocol_version")) != \
            (C.PROTOCOL, C.PROTOCOL_VERSION):
        raise IntegrityError("registration manifest protocol identity "
                             "mismatch")
    if manifest.get("study_id") != tree.context.study_id:
        raise IntegrityError("registration manifest study_id mismatch")
    return {"protocol": C.PROTOCOL, "version": C.PROTOCOL_VERSION}


@_check("model_replication_identity")
def _model_identity(tree: ModelTree) -> dict[str, Any]:
    manifest = _registration(tree)
    spec = get_model(tree.model_key)
    entry = next((m for m in manifest.get("models", [])
                  if m["model_key"] == tree.model_key), None)
    if entry is None:
        raise IntegrityError(f"{tree.model_key} absent from the signed "
                             f"registration manifest")
    if entry["model_id"] != spec.model_id or \
            entry["revision"] != spec.revision:
        raise IntegrityError(f"{tree.model_key}: registry and manifest "
                             f"disagree on model identity or revision")
    if manifest.get("models") != registration_models():
        raise IntegrityError("registration manifest model block differs "
                             "from the registered replications")
    return {"model_id": spec.model_id, "revision": spec.revision}


@_check("stage_chain")
def _stage_chain(tree: ModelTree) -> dict[str, Any]:
    """Predecessor PASS identity, hash, and signature for every present
    stage record, in sequence, with no gaps."""
    state = None
    gap = False
    for stage in C.STAGE_SEQUENCE:
        present = transitions.load_stage_record(tree, stage) is not None
        if present and gap:
            raise IntegrityError(
                f"{tree.model_key}: stage record {stage} exists but an "
                f"earlier stage record is missing")
        if not present:
            gap = True
            continue
        transitions.verify_stage_record(tree, stage)
        state = stage
    return {"state": state}


@_check("git_provenance")
def _git_provenance(tree: ModelTree) -> dict[str, Any]:
    gitinfo.assert_clean_worktree(tree.context.repo_root)
    commit = gitinfo.head_commit(tree.context.repo_root)
    return gitinfo.assert_sources_in_commit(tree.context.repo_root, commit)


@_check("dependency_and_interpreter")
def _deps(tree: ModelTree) -> dict[str, Any]:
    return {**dependency_digest(tree.context), **interpreter_identity()}


@_check("hardware_class")
def _hardware(tree: ModelTree) -> dict[str, Any]:
    qual = transitions.load_stage_record(tree, C.STAGE_QUALIFIED)
    if qual is None:
        return {"hardware": None}
    payload = verify_signed(qual, tree.context.signing_key_path,
                            where="qualification")
    hardware = payload["body"].get("hardware_class")
    for stage in C.STAGE_SEQUENCE[1:]:
        record = transitions.load_stage_record(tree, stage)
        if record is None:
            continue
        body = verify_signed(record, tree.context.signing_key_path,
                             where=stage)["body"]
        if body.get("hardware_class") not in (None, hardware):
            raise IntegrityError(f"{stage}: hardware class differs from "
                                 f"the qualification value")
    return {"hardware": hardware}


@_check("cache_integrity")
def _cache(tree: ModelTree) -> dict[str, Any]:
    """Prompt-plan membership, cached-draw identities and counts, response
    content hashes, accepted-row uniqueness — for every stage cache."""
    report: dict[str, Any] = {}
    for stage_dir in ("pilot", "prescreen", "gate1", "gate2a", "gate2b",
                      "confirmatory"):
        cache = tree.data_dir(stage_dir) / "cache.jsonl"
        plan = tree.data_dir(stage_dir) / "prompt_plan.json"
        if not cache.exists():
            continue
        rows = store.CacheWriter(cache).rows()   # row + content hashes
        spec = get_model(tree.model_key)
        seen: set[str] = set()
        planned: dict[str, int] | None = None
        if plan.exists():
            plan_payload = fs.read_json(plan)
            planned = {cell["prompt_hash"]: int(cell["draws"])
                       for cell in plan_payload["cells"]}
        counts: dict[str, int] = {}
        for row in rows:
            if row["row_id"] in seen:
                raise IntegrityError(f"duplicate accepted draw "
                                     f"{row['row_id']}")
            seen.add(row["row_id"])
            if row["model_id"] != spec.model_id or \
                    row["model_revision"] != spec.revision:
                raise IntegrityError(f"{row['row_id']}: model identity "
                                     f"mismatch")
            from dci1v3.protocol.hashing import sha_text
            if sha_text(row["raw_response"]) != row["response_content_hash"]:
                raise IntegrityError(f"{row['row_id']}: stored response "
                                     f"bytes fail their content hash")
            if planned is not None:
                if row["prompt_hash"] not in planned:
                    raise IntegrityError(
                        f"{row['row_id']}: prompt hash outside the frozen "
                        f"prompt plan")
                counts[row["prompt_hash"]] = \
                    counts.get(row["prompt_hash"], 0) + 1
        if planned is not None:
            complete = all(counts.get(h, 0) == d for h, d in planned.items())
            report[stage_dir] = {"rows": len(rows), "complete": complete}
        else:
            report[stage_dir] = {"rows": len(rows), "complete": None}
    return report


@_check("artifact_states")
def _artifact_states(tree: ModelTree) -> dict[str, Any]:
    states = artifact_states(tree)     # raises on illegal transitions
    for artifact_id, entry in states.items():
        if entry["artifact_type"] not in C.ARTIFACT_TYPES:
            raise IntegrityError(f"{artifact_id}: illegal artifact type")
        if entry["namespace"] != tree.context.namespace:
            raise IntegrityError(f"{artifact_id}: namespace mismatch — "
                                 f"synthetic evidence can never be "
                                 f"registered")
        stage = entry.get("stage")
        if stage in C.STAGE_ARTIFACT_TYPE and \
                entry["artifact_type"] != C.STAGE_ARTIFACT_TYPE[stage]:
            raise IntegrityError(f"{artifact_id}: artifact type disagrees "
                                 f"with its stage")
    return {"artifacts": len(states)}


@_check("required_and_stale_paths")
def _paths(tree: ModelTree) -> dict[str, Any]:
    unexpected = unexpected_root_files(tree)
    if unexpected:
        raise IntegrityError(f"unexpected registered paths in "
                             f"{tree.model_key}: {unexpected}")
    state = None
    for stage in C.STAGE_SEQUENCE:
        if transitions.load_stage_record(tree, stage) is not None:
            state = stage
    missing = []
    if state is not None:
        for stage in C.STAGE_SEQUENCE:
            if not tree.stage_record(stage).exists():
                missing.append(STAGE_RECORD_FILES[stage])
            if stage == state:
                break
        if not tree.transition_log.exists():
            missing.append("transition_log.jsonl")
    if missing:
        raise IntegrityError(f"required records missing from "
                             f"{tree.model_key}: {missing}")
    return {"state": state, "unexpected": []}


@_check("durable_storage")
def _durable(tree: ModelTree) -> dict[str, Any]:
    if not tree.root.exists():
        return {"files": 0}
    store.assert_replicated(tree.root, tree.durable)
    return {"files": len(store.fingerprint_tree(tree.root))}


@_check("namespace")
def _namespace(tree: ModelTree) -> dict[str, Any]:
    expected = (C.STUDY_ID if tree.context.namespace == "registered"
                else C.SYNTHETIC_STUDY_ID)
    if tree.context.study_id != expected:
        raise IntegrityError("namespace and study_id disagree")
    return {"namespace": tree.context.namespace}


def verify_evidence(tree: ModelTree, *, expected_stage: str | None = None
                    ) -> dict[str, Any]:
    """Run the complete contract; raise IntegrityError on the first
    violation; return the per-check report on success."""
    report: dict[str, Any] = {}
    for name, fn in NAMED_CHECKS.items():
        report[name] = fn(tree)
    if expected_stage is not None:
        state = report["stage_chain"]["state"]
        if state != expected_stage:
            raise IntegrityError(
                f"{tree.model_key}: expected stage {expected_stage}, "
                f"durable state is {state}")
    return report
