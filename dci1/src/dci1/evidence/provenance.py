"""Analysis provenance and registered-artifact refusal rules (Addendum A §5).

A registered analysis artifact is refused when: the git tree is dirty; the
freeze-record hash differs from the record on disk; a parent manifest hash
differs; the requested stage is inconsistent with unmasking status; or a
full-design estimand violates ``n_observations = n_blocks × 6`` (enforced in
the table builder).
"""
from __future__ import annotations

import json
from typing import Any

from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import MANIFEST_NAME, writer_identity
from dci1.protocol.constants import (
    AMENDMENT_ID,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    ProtocolError,
)
from dci1.protocol.hashing import sha, sha_text


def protocol_identity() -> str:
    return f"{PROTOCOL_ID}-{PROTOCOL_VERSION}+{AMENDMENT_ID}"


def input_manifest_hashes(tree: StudyTree) -> dict[str, str]:
    hashes = {}
    for stage in ("prompts", "cache", "selection"):
        manifest = tree.stage_dir(stage) / MANIFEST_NAME
        if manifest.exists():
            hashes[stage] = sha_text(manifest.read_text())
    return hashes


def require_registered_writer(*, allow_dirty: bool = False,
                              writer: dict[str, Any] | None = None
                              ) -> dict[str, Any]:
    """Registered artifacts require ``writer_dirty = false`` (R20)."""
    writer = writer if writer is not None else writer_identity()
    if writer["writer_dirty"] and not allow_dirty:
        raise ProtocolError(
            "the git tree is dirty; registered analysis artifacts are "
            "refused (Addendum A §5). Commit the tree and rerun.")
    return writer


def require_freeze_consistency(tree: StudyTree,
                               freeze_record_hash: str) -> None:
    if not tree.freeze_record.exists():
        raise ProtocolError(f"no freeze record at {tree.freeze_record}")
    on_disk = json.loads(tree.freeze_record.read_text())
    body = {k: v for k, v in on_disk.items() if k != "freeze_hash"}
    actual = sha(body)
    if actual != freeze_record_hash:
        raise ProtocolError(
            f"freeze_record_hash {freeze_record_hash[:12]} differs from the "
            f"record on disk ({actual[:12]}); registered output refused")


def require_stage_consistent_with_unmasking(tree: StudyTree,
                                            analysis_stage: str) -> None:
    unmasked = tree.unmasking_record.exists()
    if analysis_stage == "final" and not unmasked:
        raise ProtocolError(
            'analysis_stage="final" without an unmasking record is refused')
    if analysis_stage == "masked" and unmasked:
        raise ProtocolError(
            'analysis_stage="masked" after unmasking is refused — the '
            "registered masked analysis may not be re-run")


def require_parent_manifests(tree: StudyTree,
                             recorded: dict[str, str]) -> None:
    current = input_manifest_hashes(tree)
    for stage, digest in recorded.items():
        if current.get(stage) != digest:
            raise ProtocolError(
                f"parent manifest for stage {stage!r} differs from the "
                f"recorded hash; registered output refused")


def analysis_provenance(tree: StudyTree, *, analysis_command: str,
                        masking_state: str,
                        environment_record: dict[str, Any],
                        resampling_root_seed: int) -> dict[str, Any]:
    if masking_state not in ("masked", "final", "sensitivity"):
        raise ProtocolError(f"bad masking_state {masking_state!r}")
    return {
        "protocol_identity": protocol_identity(),
        "input_manifest_hashes": input_manifest_hashes(tree),
        "resampling_root_seed": resampling_root_seed,
        "masking_state": masking_state,
        "environment_record_hash": sha(environment_record),
        "analysis_command": analysis_command,
    }
