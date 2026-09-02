"""Stage 1, ``CONFIRM_REGISTERED``: bind the confirmatory manifest."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import gitinfo

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import manifest as M
from dci1v8dev.confirm.pilot_import import open_pilot

__all__ = ["registration_payload", "run_registration"]


def registration_payload(tree: L.ConfirmTree, *, producing_commit: str,
                         repo_root: Path | str,
                         pilot_roots: Mapping[str, str]) -> dict[str, Any]:
    manifest, created = M.ensure_registration(
        tree.context, producing_commit=producing_commit,
        pilot_roots=pilot_roots, repo_root=repo_root)
    if tree.model_key not in manifest["pilot_sources"]:
        raise L.TerminalStatus(
            "NOT_ELIGIBLE", gate=L.STAGE_REGISTERED,
            criterion="a model enters the confirmatory study only with a "
                      "pilot root bound in the manifest",
            observed={"model_key": tree.model_key,
                      "bound": sorted(manifest["pilot_sources"])},
            strongest_permissible_statement="no pilot evidence was bound "
                                            "for this model")
    source = open_pilot(Path(manifest["pilot_sources"][tree.model_key]["root"]),
                        tree.model_key, synthetic=tree.synthetic)
    bound = manifest["pilot_sources"][tree.model_key]
    if source.as_record()["record_hashes"] != bound["record_hashes"]:
        raise L.TerminalStatus(
            "APPARATUS_FAILURE", gate=L.STAGE_REGISTERED,
            criterion="the pilot records this model is read from are the "
                      "ones the manifest bound",
            observed={"bound": bound["record_hashes"],
                      "read": source.as_record()["record_hashes"]},
            strongest_permissible_statement="the pilot evidence moved after "
                                            "the manifest was signed")
    return {
        "stage": L.STAGE_REGISTERED,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_REGISTERED],
        "outcome": "PASS", "producing_commit": producing_commit,
        "manifest_hash": M.manifest_hash(manifest),
        "manifest_signed_by_this_replication": created,
        "protocol_version": manifest["protocol_version"],
        "pilot_source": source.as_record(),
        "selected_cap": source.selected_cap,
        "allocation": manifest["allocation"],
        "analysis_code": manifest["analysis_code"],
        "documents": manifest["documents"],
        "instrument": manifest["instrument"],
        "lifecycle": manifest["lifecycle"],
    }


def run_registration(tree: L.ConfirmTree, *, pilot_roots: Mapping[str, str],
                     producing_commit: str | None = None,
                     environment_digest: str = "",
                     repo_root: Path | str | None = None) -> L.StageOutcome:
    repo = Path(repo_root) if repo_root is not None else Path(tree.context.repo_root)
    commit = producing_commit or gitinfo.head_commit(repo)
    return L.run_stage(
        tree, L.STAGE_REGISTERED,
        compute=lambda _prev: registration_payload(
            tree, producing_commit=commit, repo_root=repo,
            pilot_roots=pilot_roots),
        producing_commit=commit, environment_digest=environment_digest)
