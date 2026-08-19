"""Mask-key custody, pre-unmasking commitment, and the unmasking record
(Addendum A §4 — custody controls retained around the v2 §19 masking
procedure; reconciliation R41–R45).

The permutation itself is v2's: per-block random permutation of the four
primary arms, system random source, constructed after generation (R36/R40
resolved to v2). This module only guards the key's custody:

* the key is written exactly once per (model, freeze_id) — a second key
  fails closed;
* a sealed hash sidecar binds the key's bytes;
* unmasking is single-shot and irreversible — a second attempt fails closed;
* nothing under ``dci1.analysis`` may import this module (tested).
"""
from __future__ import annotations

import json
from typing import Any

from dci1.evidence.layout import StudyTree
from dci1.evidence.sealing import utc_now, writer_identity
from dci1.evidence.store import atomic_write, write_json
from dci1.protocol.constants import ProtocolError
from dci1.protocol.hashing import sha_text

MASKING_SCHEME_ID = "v2-s19-block-primary-permutation"


def write_mask_key_sealed(tree: StudyTree,
                          permutations: dict[str, dict[str, str]]) -> str:
    """Write the key exactly once; seal it; return its hash (R41)."""
    if tree.unmasking_record.exists():
        raise ProtocolError(
            "re-masking after unmasking is refused — unmasking is "
            "irreversible (Addendum A §4)")
    if tree.mask_key.exists():
        raise ProtocolError(
            f"a mask key already exists for ({tree.model_slug}, "
            f"{tree.freeze_id}); a second key fails closed")
    payload = json.dumps(
        {"masking_scheme_id": MASKING_SCHEME_ID,
         "permutations": permutations, "created_at_utc": utc_now()},
        indent=2, sort_keys=True)
    atomic_write(tree.mask_key, payload)
    key_hash = sha_text(payload)
    atomic_write(tree.mask_key.with_suffix(".json.sha256"), key_hash)
    return key_hash


def mask_key_hash(tree: StudyTree) -> str:
    sidecar = tree.mask_key.with_suffix(".json.sha256")
    if not (tree.mask_key.exists() and sidecar.exists()):
        raise ProtocolError("no sealed mask key")
    recorded = sidecar.read_text().strip()
    actual = sha_text(tree.mask_key.read_text())
    if actual != recorded:
        raise ProtocolError("mask key fails its sealed hash")
    return recorded


def write_commitment(tree: StudyTree, *, analysis_plan_hash: str,
                     exclusion_decisions_hash: str, verifier_versions: str,
                     failure_taxonomy_assignments_hash: str,
                     masked_analysis_result_hash: str, diagnostics_hash: str,
                     actor: str, model_id: str,
                     allow_dirty: bool = False) -> str:
    """The sealed pre-unmasking commitment (R43)."""
    if tree.commitment.exists():
        raise ProtocolError("a commitment already exists; refusing to "
                            "overwrite")
    writer = writer_identity()
    if writer["writer_dirty"] and not allow_dirty:
        raise ProtocolError(
            "commitment requires a clean git tree (Addendum A §4)")
    if not masked_analysis_result_hash:
        raise ProtocolError(
            "commitment requires a completed masked analysis")
    mask_key_hash(tree)                      # referenced artifact is sealed
    payload = {
        "freeze_id": tree.freeze_id,
        "model_id": model_id,
        "analysis_code_commit": writer["writer_commit"],
        "analysis_plan_hash": analysis_plan_hash,
        "exclusion_decisions_hash": exclusion_decisions_hash,
        "verifier_versions": verifier_versions,
        "failure_taxonomy_assignments_hash":
            failure_taxonomy_assignments_hash,
        "masked_analysis_result_hash": masked_analysis_result_hash,
        "diagnostics_hash": diagnostics_hash,
        "committed_at_utc": utc_now(),
        "actor": actor,
    }
    write_json(tree.commitment, payload)
    return sha_text(tree.commitment.read_text())


def verify_commitment(tree: StudyTree,
                      masked_analysis_result_hash: str) -> dict[str, Any]:
    if not tree.commitment.exists():
        raise ProtocolError("unmasking without a valid commitment is refused")
    commitment = json.loads(tree.commitment.read_text())
    if commitment["masked_analysis_result_hash"] != \
            masked_analysis_result_hash:
        raise ProtocolError(
            "the committed masked-analysis hash does not match the masked "
            "result on disk; unmasking refused")
    return commitment


def write_unmasking_record(tree: StudyTree, *, actor: str, model_id: str,
                           reason: str) -> str:
    """Create and seal the single unmasking record (R44/R45)."""
    if tree.unmasking_record.exists():
        raise ProtocolError(
            "an unmasking record already exists — unmasking is single-shot "
            "and irreversible")
    commitment_hash = sha_text(tree.commitment.read_text())
    payload = {
        "unmasked_at_utc": utc_now(),
        "actor": actor,
        "freeze_id": tree.freeze_id,
        "model_id": model_id,
        "commitment_hash": commitment_hash,
        "mask_key_hash": mask_key_hash(tree),
        "analysis_code_commit": writer_identity()["writer_commit"],
        "reason": reason,
    }
    write_json(tree.unmasking_record, payload)
    return sha_text(tree.unmasking_record.read_text())
