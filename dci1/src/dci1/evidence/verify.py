"""`verify-evidence` and the restore drill (Addendum A R24, R26).

Verification recomputes every hash and record count in every present stage
manifest, checks seals and the study manifest's bindings, and raises (CLI:
exits non-zero) on any mismatch. The restore drill rebuilds all derived
artifacts for one model from the replicated raw layers alone, in a clean
workspace, and verifies byte identity against the originals.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1.evidence.layout import RAW_LAYERS, StudyTree
from dci1.evidence.provenance import require_freeze_consistency
from dci1.evidence.sealing import MANIFEST_NAME, CacheWriter, is_sealed, verify_stage
from dci1.evidence.store import fingerprint_tree, restore_from_durable
from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_text


def verify_evidence(tree: StudyTree) -> dict[str, Any]:
    """Full verification of one (study, model, freeze_id) tree; raises on any
    mismatch."""
    report: dict[str, Any] = {"study_id": tree.study_id,
                              "model_slug": tree.model_slug,
                              "freeze_id": tree.freeze_id, "stages": {}}
    for stage in ("prompts", "cache", "selection", "masking"):
        stage_dir = tree.stage_dir(stage)
        if not stage_dir.exists():
            report["stages"][stage] = "absent"
            continue
        if (stage_dir / MANIFEST_NAME).exists():
            report["stages"][stage] = verify_stage(tree, stage)
        elif is_sealed(stage_dir):
            raise ProtocolError(f"{stage_dir}: sealed without a manifest")
        else:
            report["stages"][stage] = "unsealed (no manifest yet)"
    if tree.cache_file.exists():
        CacheWriter(tree.cache_file).verify_hashes()
        report["cache_records_verified"] = True
    if tree.study_manifest.exists():
        manifest = json.loads(tree.study_manifest.read_text())
        for stage, digest in (manifest.get("stage_manifest_sha256")
                              or {}).items():
            actual = sha_text(
                (tree.stage_dir(stage) / MANIFEST_NAME).read_text())
            if actual != digest:
                raise ProtocolError(
                    f"study manifest binding for stage {stage!r} fails "
                    f"({actual[:10]} != {digest[:10]})")
        # A recorded binding makes the freeze record mandatory: a missing,
        # unreadable or different record fails, by the check analysis uses.
        if manifest.get("freeze_record_hash"):
            require_freeze_consistency(tree, manifest["freeze_record_hash"])
        report["study_manifest_verified"] = True
    report["ok"] = True
    return report


def restore_drill(tree: StudyTree, rebuild, workspace: Path) -> dict[str, Any]:
    """R26: reconstruct every derived artifact from the replicated raw layers
    alone, in a clean workspace, and verify byte identity.

    ``rebuild(restored_tree)`` must regenerate the derived artifacts inside
    the restored tree using only its raw layers.
    """
    workspace = Path(workspace)
    if workspace.exists() and any(workspace.iterdir()):
        raise ProtocolError("restore drill requires a clean workspace")
    restored = StudyTree(model_slug=tree.model_slug, freeze_id=tree.freeze_id,
                         study_id=tree.study_id, base=workspace)
    for layer in RAW_LAYERS:
        src = tree.durable_root / layer
        if src.exists():
            restore_from_durable(src, restored.root / layer)
    if tree.freeze_record.exists():
        (restored.root).mkdir(parents=True, exist_ok=True)
        restored.freeze_record.write_text(tree.freeze_record.read_text())
    rebuild(restored)
    original = fingerprint_tree(tree.root / "derived")
    rebuilt = fingerprint_tree(restored.root / "derived")
    if original != rebuilt:
        differing = sorted(set(original.items()) ^ set(rebuilt.items()))
        raise ProtocolError(
            f"restore drill: derived artifacts are not byte-identical "
            f"({differing[:4]})")
    return {"derived_files": len(original), "byte_identical": True}
