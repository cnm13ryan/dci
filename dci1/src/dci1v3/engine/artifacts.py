"""Artifact lifecycle (item 54/55, §27): generated → committed → accepted,
with superseded as the only exit from accepted. Monotonic, append-only.

The ledger is an append-only JSONL per model tree. State legality is
enforced at append time and re-checked by evidence verification; a
superseded artifact can never return to accepted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v3.engine import fs
from dci1v3.engine.paths import ModelTree
from dci1v3.errors import IntegrityError
from dci1v3.protocol.constants import ARTIFACT_STATES, ARTIFACT_TYPES
from dci1v3.protocol.hashing import sha_file

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
            f"artifact {artifact_id!r} cannot move {previous!r} -> "
            f"{state!r}; artifact states are monotonic")
    if state in ("committed", "accepted"):
        if not Path(path).exists():
            raise IntegrityError(f"{artifact_id!r}: no durable bytes at "
                                 f"{path}")
        actual = sha_file(path)
        if content_hash is not None and actual != content_hash:
            raise IntegrityError(f"{artifact_id!r}: content hash mismatch "
                                 f"at {state}")
        content_hash = actual
    entry = {
        "artifact_id": artifact_id,
        "path": str(Path(path).relative_to(tree.root))
                if Path(path).is_relative_to(tree.root) else str(path),
        "artifact_type": artifact_type, "state": state, "stage": stage,
        "namespace": tree.context.namespace,
        "producing_commit": producing_commit,
        "content_hash": content_hash,
    }
    fs.append_jsonl(tree.artifact_ledger, fs.row_with_hash(entry))
    return entry
