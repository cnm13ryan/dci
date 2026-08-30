"""Stage 1, ``PILOT_REGISTERED``: bind the pilot manifest to this replication.

Signs the manifest once per root (the first replication) and verifies every
later replication against it; the record carries the manifest hash, the
bindings a later reader needs without re-opening the manifest, and this
model's own frame reference.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v7.topics.bank import TopicBank

from dci1v8dev.run import manifest as M
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import ModelTree, StudyContext
from dci1v8dev.run.lifecycle import StageOutcome, run_stage

__all__ = ["plan_registration", "registration_payload", "run_registration"]


def plan_registration(context: StudyContext, *, repo_root: Path | str,
                      producing_commit: str | None = None,
                      bank: TopicBank | None = None) -> dict[str, Any]:
    """What signing would bind, and what blocks it. Writes nothing."""
    commit = producing_commit or gitinfo.head_commit(Path(repo_root))
    blockers = M.signing_blockers(context, repo_root=repo_root, bank=bank)
    out: dict[str, Any] = {"blockers": blockers, "signable": not blockers,
                           "producing_commit": commit}
    if not blockers:
        manifest = M.build_manifest(context, producing_commit=commit,
                                    bank=bank, repo_root=repo_root)
        out["manifest_hash"] = M.manifest_hash(manifest)
        out["manifest"] = manifest
    return out


def registration_payload(tree: ModelTree, *, producing_commit: str,
                         repo_root: Path | str,
                         bank: TopicBank | None = None) -> dict[str, Any]:
    manifest, created = M.ensure_registration(
        tree.context, producing_commit=producing_commit, bank=bank,
        repo_root=repo_root)
    model = next(m for m in manifest["models"]
                 if m["model_key"] == tree.model_key)
    return {
        "stage": S.STAGE_REGISTERED,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_REGISTERED],
        "outcome": "PASS",
        "inputs": {},
        "producing_commit": producing_commit,
        "manifest_hash": M.manifest_hash(manifest),
        "manifest_signed_by_this_replication": created,
        "protocol_version": manifest["protocol_version"],
        "status": manifest["status"],
        "documents": manifest["documents"],
        "instrument": {k: manifest["instrument"][k]
                       for k in ("verifier_hash", "wording_hash",
                                 "v7_verifier_hash", "v7_wording_hash",
                                 "frames")},
        "model": model,
        "wording_diagnostic": manifest["wording_diagnostic"],
        "wording_policy": manifest["wording_diagnostic"]["wording_policy"],
        "topics": manifest["topics"],
        "seeds": manifest["seeds"],
        "criteria": manifest["criteria"],
        "rules": manifest["rules"],
        "lifecycle": manifest["lifecycle"],
        "no_composed_cells": S.NO_COMPOSED_CELLS,
    }


def run_registration(tree: ModelTree, *, producing_commit: str | None = None,
                     environment_digest: str = "",
                     repo_root: Path | str | None = None,
                     bank: TopicBank | None = None) -> StageOutcome:
    repo = Path(repo_root) if repo_root is not None else Path(tree.context.repo_root)
    commit = producing_commit or gitinfo.head_commit(repo)
    return run_stage(
        tree, S.STAGE_REGISTERED,
        compute=lambda _prev: registration_payload(
            tree, producing_commit=commit, repo_root=repo, bank=bank),
        producing_commit=commit, environment_digest=environment_digest)
