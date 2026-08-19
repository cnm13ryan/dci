"""Evidence verification (§26, §27): the whole tree, checked from the outside.

Verification is deliberately independent of the code that wrote the tree. It
re-derives every required path through the one frozen path function, re-checks
every signature and content hash, replays the artifact ledger for legality,
replays the transition log, and refuses any unexpected, stale or missing path.

It also enforces the isolation invariants that no single stage can check for
itself: that no v4 artifact sits inside a historical tree, and that every
committed row is reproducible from the durable mirror without regenerating a
draw.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v4.engine import artifacts, fs, store, transitions
from dci1v4.engine.guards import classify
from dci1v4.engine.paths import (
    STAGE_RECORD_FILES,
    ModelTree,
    required_records,
    unexpected_root_files,
)
from dci1v4.engine.signing import verify_signed
from dci1v4.errors import IntegrityError
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import sha_file


def reached_stage(tree: ModelTree) -> str | None:
    """The last stage with a record on disk, in registered order."""
    reached = None
    for stage in C.STAGE_SEQUENCE:
        if tree.stage_record(stage).exists():
            reached = stage
        else:
            break
    return reached


def verify_model_tree(tree: ModelTree) -> dict[str, Any]:
    """Full evidence verification for one replication. Fails closed."""
    root = tree.root
    if not root.exists():
        raise IntegrityError(f"{tree.model_key}: no evidence tree at {root}")
    if classify(root) is not None:
        raise IntegrityError(
            f"{tree.model_key}: the v4 tree resolves inside a historical "
            f"tree ({classify(root)}); v4 writes nothing there (§26)")

    reached = reached_stage(tree)
    if reached is None:
        raise IntegrityError(f"{tree.model_key}: no stage record present")

    missing = [name for name in required_records(reached)
               if not (root / name).exists()]
    if missing:
        raise IntegrityError(f"{tree.model_key}: required records missing "
                             f"{missing}")
    unexpected = unexpected_root_files(tree)
    if unexpected:
        raise IntegrityError(f"{tree.model_key}: unexpected registered-looking "
                             f"files in the tree root: {unexpected}")

    verified: dict[str, str] = {}
    for stage in C.STAGE_SEQUENCE:
        path = tree.stage_record(stage)
        if not path.exists():
            continue
        record = fs.read_json(path)
        payload = verify_signed(record, tree.context.signing_key_path,
                                where=f"{tree.model_key}:{stage}")
        if payload.get("stage") != stage:
            raise IntegrityError(
                f"{path.name} declares stage {payload.get('stage')!r}")
        declared = payload.get("artifact_type")
        if declared != C.STAGE_ARTIFACT_TYPE[stage]:
            raise IntegrityError(
                f"{path.name}: artifact type {declared!r} disagrees with its "
                f"stage")
        if payload.get("namespace") != tree.context.namespace:
            raise IntegrityError(f"{path.name}: namespace mismatch")
        verified[STAGE_RECORD_FILES[stage]] = sha_file(path)

    ledger = artifacts.artifact_states(tree)      # replays legality
    counts = artifacts.state_counts(tree)
    log = transitions.transition_rows(tree)

    return {
        "model_key": tree.model_key,
        "namespace": tree.context.namespace,
        "reached_stage": reached,
        "terminal_status": transitions.terminal_status(tree),
        "identification_statuses": transitions.identification_statuses(tree),
        "records_verified": verified,
        "artifacts": {"tracked": len(ledger), "state_counts": counts},
        "transitions_logged": len(log),
    }


def verify_durable_mirror(tree: ModelTree) -> dict[str, Any]:
    """§27: the durable mirror reproduces every committed byte."""
    store.assert_replicated(tree.root, tree.durable)
    return {"files": len(store.fingerprint_tree(tree.durable))}


def restore_and_compare(tree: ModelTree, target: Path) -> dict[str, Any]:
    """§27: cache deletion and durable restore reproduce every committed row
    with matching hashes, regenerating no draw."""
    restored = store.restore(tree.durable, Path(target))
    original = store.fingerprint_tree(tree.root)
    differing = [rel for rel, digest in original.items()
                 if restored.get(rel) != digest]
    if differing:
        raise IntegrityError(f"restoration differs for {len(differing)} "
                             f"file(s), first: {differing[0]}")
    return {"restored_files": len(restored)}
