"""Artifact lifecycle (§26): generated → committed → accepted, with superseded
as the only exit. Monotonic, append-only, and checked before any mutation.

Two ledgers live here and they do different jobs:

* the **artifact ledger** records every state transition of every registered
  artifact, and re-verifies legality on every read, so a superseded artifact
  can never return to accepted;
* the **one-shot ledger** records that a single-use operation has been
  entered — §10.4's calibration on the untouched half, and the §10.4 sealed
  final-check set. The entry is written *before* the operation mutates
  anything, so deleting the resulting record file cannot re-open the
  operation. That ordering is the whole point and is what v3's artifacts.py
  established.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v4.engine import fs
from dci1v4.engine.paths import ModelTree
from dci1v4.errors import IntegrityError
from dci1v4.protocol.constants import ARTIFACT_STATES, ARTIFACT_TYPES
from dci1v4.protocol.hashing import sha_file

_ALLOWED_NEXT = {
    None: {"generated"},
    "generated": {"committed"},
    "committed": {"accepted", "superseded"},
    "accepted": {"superseded"},
    "superseded": set(),
}


def _entries(tree: ModelTree) -> list[dict[str, Any]]:
    if not tree.artifact_ledger.exists():
        return []
    rows = fs.read_jsonl(tree.artifact_ledger)
    for row in rows:
        fs.verify_row_hash(row, where=f"ledger:{row.get('artifact_id')}")
    return rows


def artifact_states(tree: ModelTree) -> dict[str, dict[str, Any]]:
    """artifact_id -> latest ledger entry, with legality re-verified."""
    latest: dict[str, dict[str, Any]] = {}
    for row in _entries(tree):
        previous = latest.get(row["artifact_id"], {}).get("state")
        if row["state"] not in _ALLOWED_NEXT[previous]:
            raise IntegrityError(
                f"artifact {row['artifact_id']!r} moved {previous!r} -> "
                f"{row['state']!r}; artifact states are monotonic")
        latest[row["artifact_id"]] = row
    return latest


def state_counts(tree: ModelTree) -> dict[str, int]:
    """§26: generated, committed and accepted counts reported separately."""
    counts = {state: 0 for state in ARTIFACT_STATES}
    for row in _entries(tree):
        counts[row["state"]] += 1
    return counts


def record_state(tree: ModelTree, *, artifact_id: str, path: Path,
                 artifact_type: str, state: str, stage: str,
                 producing_commit: str, content_hash: str | None = None
                 ) -> dict[str, Any]:
    if artifact_type not in ARTIFACT_TYPES:
        raise IntegrityError(f"unknown artifact type {artifact_type!r}")
    if state not in ARTIFACT_STATES:
        raise IntegrityError(f"unknown artifact state {state!r}")
    previous = artifact_states(tree).get(artifact_id, {}).get("state")
    if state not in _ALLOWED_NEXT[previous]:
        raise IntegrityError(
            f"artifact {artifact_id!r} cannot move {previous!r} -> {state!r}; "
            f"artifact states are monotonic")
    if state in ("committed", "accepted"):
        if not Path(path).exists():
            raise IntegrityError(f"{artifact_id!r}: no durable bytes at {path}")
        actual = sha_file(path)
        if content_hash is not None and actual != content_hash:
            raise IntegrityError(f"{artifact_id!r}: content hash mismatch at "
                                 f"{state}")
        content_hash = actual
    entry = {
        "artifact_id": artifact_id,
        "path": (str(Path(path).relative_to(tree.root))
                 if Path(path).is_relative_to(tree.root) else str(path)),
        "artifact_type": artifact_type, "state": state, "stage": stage,
        "namespace": tree.context.namespace,
        "producing_commit": producing_commit,
        "content_hash": content_hash,
    }
    fs.append_jsonl(tree.artifact_ledger, fs.row_with_hash(entry))
    return entry


def claim_one_shot(tree: ModelTree, *, operation: str, detail: dict[str, Any],
                   producing_commit: str) -> dict[str, Any]:
    """Claim a single-use operation BEFORE it mutates anything (§10.4).

    A second claim of the same operation is refused whether or not the record
    the first claim produced still exists, so deleting an output cannot
    re-open a one-shot stage.
    """
    if tree.calibration_ledger.exists():
        for row in fs.read_jsonl(tree.calibration_ledger):
            fs.verify_row_hash(row, where=f"one_shot:{row.get('operation')}")
            if row["operation"] == operation:
                raise IntegrityError(
                    f"one-shot operation {operation!r} was already claimed at "
                    f"commit {row['producing_commit'][:12]}; it cannot run "
                    f"again, and deleting its output does not re-open it")
    entry = {"operation": operation, "detail": detail,
             "namespace": tree.context.namespace,
             "producing_commit": producing_commit}
    fs.append_jsonl(tree.calibration_ledger, fs.row_with_hash(entry))
    return entry


def one_shot_claimed(tree: ModelTree, operation: str) -> bool:
    if not tree.calibration_ledger.exists():
        return False
    return any(row["operation"] == operation
               for row in fs.read_jsonl(tree.calibration_ledger))
