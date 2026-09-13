"""Stage 4, ``FROZEN``: the signed design, and the last pre-freeze write.

Binds, for this model: the manifest hash; the pilot record hashes; the
top-up and membership record hashes; the study-level membership document
(``confirm.MEMBERSHIP_DOCUMENT``) by hash, and the assertion that its
entry for this model equals this model's own membership; the allocation in
force (blocks per frame, draws, cap); per entering frame the arms, the
slot map, the spectrum slots and aliases, the operating points and their
stability; the estimands; the family declarations, the multiplicity rule,
the bootstrap algorithm and resamples, the precision preconditions and the
claim thresholds; the analysis code by hash; the deviations from v7's
registered post-freeze sequence, each with its reason. After this record
exists no earlier stage may write (``lifecycle.assert_no_post_freeze_
mutation``), and every later stage asserts its inputs against this
record's hash.

A model with no entering frame is terminal ``NOT_ELIGIBLE`` here: nothing
is generated for it and the verdict is on its record.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import (CONFIRM_DOCUMENT, MEMBERSHIP_DOCUMENT,
                               PROTOCOL_VERSION)
from dci1v8dev import rules as R
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.pilot_import import open_pilot
from dci1v8dev.confirm.readiness import assert_freeze_ready, freeze_readiness
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.manifest import analysis_code_hashes

__all__ = ["DEVIATIONS", "freeze_payload", "run_freeze", "load_freeze",
           "assert_matches_freeze", "frozen_frames"]

#: What this layer does differently from v7's registered stages 15-19,
#: stated on the freeze rather than discovered later.
DEVIATIONS = [
    {"what": "no MASKED_ANALYSIS / UNMASKING stages",
     "why": "v7 §20 masks companion labels to protect analyst decisions "
            "taken between generation and the final report; this layer has "
            "no such decision point --- CONFIRMATORY_ANALYSIS is frozen code "
            "that runs once, unattended, on the complete row set and emits "
            "every registered quantity, so there is nothing a mask would "
            "protect. Recorded as a deviation, not an equivalence."},
    {"what": "the near-form and class arms are not run",
     "why": "v8's pilot selected no near-form controls and no class "
            "companion; Delta_near, Delta_broad and their statuses "
            "(NEAR_FORM_ARM_NOT_AVAILABLE, CLASS_ARM_NOT_AVAILABLE) are "
            "recorded as unavailable and L3c's near-form requirement is "
            "therefore not satisfiable: L3c is reported as "
            "NEAR_FORM_UNAVAILABLE rather than emitted."},
    {"what": "the backup arm (R4, R5 beside B) is generated",
     "why": "the pre-registered reference-sensitivity contrast; R4/R5 never "
            "enter Delta_R, Rbar, Xi or the fit."},
    {"what": "spectrum points are the v8 selection, not six core-family "
             "companions",
     "why": "V8_CANDIDATE.md §5: the v8 selection is decoupled from the core "
            "families; the §11.8 fit, support verdict and delta_difficulty "
            "are v7's code on these points."},
]


def frozen_frames(membership: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for w, e in membership["by_frame"].items():
        if not e.get("enters"):
            continue
        out[w] = {k: e[k] for k in (
            "frame", "state", "enters_local", "enters_spectrum", "arms",
            "cells_per_block", "slot_map", "spectrum_points",
            "spectrum_aliases", "n_spectrum_slots", "n_star", "m_star",
            "iota_a", "solo_compliance_b", "core", "backups",
            "local_valid_families", "identification_statuses", "stability",
            "reference_sensitivity")}
        out[w]["runner_up_slots"] = list(e.get("runner_up_slots") or [])
        out[w]["runner_up"] = e.get("runner_up")
    return out


def freeze_payload(tree: L.ConfirmTree, membership: Mapping[str, Any], *,
                   producing_commit: str, repo_root: Path | str,
                   blocks_per_frame: int | None = None) -> dict[str, Any]:
    registration = L.read_stage_record(tree, L.STAGE_REGISTERED)
    topup_path = tree.stage_record(L.STAGE_TOPUP)
    membership_path = tree.stage_record(L.STAGE_MEMBERSHIP)
    doc_path = Path(repo_root) / MEMBERSHIP_DOCUMENT
    if not doc_path.exists():
        raise ProtocolError(
            f"the study-level membership lock {MEMBERSHIP_DOCUMENT} does not "
            "exist; tools/v8_membership_lock.py writes it from every model's "
            "MEMBERSHIP record before any freeze")
    lock = fs.read_json(doc_path)
    mine = lock.get("models", {}).get(tree.model_key)
    if mine is None:
        raise ProtocolError(f"{tree.model_key} is not in the membership lock")
    expected = {"frames_entering_local": membership["frames_entering_local"],
                "frames_entering_spectrum": membership["frames_entering_spectrum"],
                "membership_record_hash": fs.read_json(membership_path)["record_hash"]}
    got = {k: mine.get(k) for k in expected}
    if got != expected:
        raise ProtocolError(
            f"the membership lock's entry for {tree.model_key} {got} differs "
            f"from this model's MEMBERSHIP record {expected}; re-run the "
            "lock tool before freezing")
    pilot = open_pilot(Path(registration["pilot_source"]["root"]),
                       tree.model_key, synthetic=tree.synthetic)
    readiness = freeze_readiness(tree, membership, repo_root=repo_root,
                                 lock=lock, registration=registration,
                                 pilot_gate2=pilot.gate2,
                                 pilot_regime=pilot.regime)
    if not membership["enters_study"]:
        raise L.TerminalStatus(
            "NOT_ELIGIBLE", gate=L.STAGE_FROZEN,
            criterion="a model enters confirmatory generation only with at "
                      "least one frame in the LOCAL or SPECTRUM arm",
            observed={"frames_entering": membership["frames_entering"]},
            strongest_permissible_statement=(
                "no frame of this model is LOCAL-supported on an eligible "
                "model or SPECTRUM-identified; nothing is generated"))
    assert_freeze_ready(readiness, tree=tree)
    blocks = int(lock["allocation"]["chosen_blocks_per_frame"]
                 if blocks_per_frame is None else blocks_per_frame)
    if blocks_per_frame is not None and not tree.synthetic:
        raise ProtocolError("blocks_per_frame is a synthetic-namespace knob")
    if blocks_per_frame is None and blocks != R.CONFIRMATORY_BLOCKS_PER_FRAME:
        raise ProtocolError(
            f"the membership lock says {blocks} blocks per frame and "
            f"rules.CONFIRMATORY_BLOCKS_PER_FRAME says "
            f"{R.CONFIRMATORY_BLOCKS_PER_FRAME}; one allocation exists and "
            "the lock must be regenerated")
    return {
        "stage": L.STAGE_FROZEN,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_FROZEN],
        "outcome": "PASS", "producing_commit": producing_commit,
        "protocol_version": PROTOCOL_VERSION,
        "inputs": {
            "manifest_hash": registration["manifest_hash"],
            "pilot_record_hashes": registration["pilot_source"]["record_hashes"],
            "topup_record_hash": fs.read_json(topup_path)["record_hash"],
            "membership_record_hash": expected["membership_record_hash"],
            "membership_lock_hash": sha_obj(lock),
            "membership_lock_path": MEMBERSHIP_DOCUMENT},
        "design": {
            "blocks_per_frame": blocks,
            "draws": C.M_DRAWS,
            "completion_cap": registration["selected_cap"],
            "frames": frozen_frames(membership),
            "frames_entering_local": membership["frames_entering_local"],
            "frames_entering_spectrum": membership["frames_entering_spectrum"],
            "frame_of_block": "block_index % N_WORDINGS; every stated line "
                              "of a block under the block's frame",
            "allocation": lock["allocation"],
            "generations_planned": sum(
                blocks * C.M_DRAWS * e["cells_per_block"]
                for e in frozen_frames(membership).values())},
        "estimands": membership["estimands"],
        "families": {k: list(v) for k, v in C.FAMILY_MEMBERS.items()},
        "primary_family": C.PRIMARY_FAMILY,
        "multiplicity_rule": P.MULTIPLICITY_RULE,
        "precision_rule": P.PRECISION_RULE,
        "bootstrap": {"resamples": C.BOOTSTRAP_RESAMPLES,
                      "unit": "block (one topic under one frame) per frame; "
                              "topic across frames for the joint family",
                      "refit_every_replicate": True,
                      "seed_rule": "seeds.bootstrap_seed(estimand, model_id)"},
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "thresholds": {
            "smallest_effect_of_interest": C.SMALLEST_EFFECT_OF_INTEREST,
            "equivalence_region": C.EQUIVALENCE_REGION,
            "delta_r_generic": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_r_pair_specific": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD},
        "claim_ladder": list(C.CLAIM_LEVELS),
        "analysis_code": analysis_code_hashes(),
        "package": registration.get("instrument"),
        "deviations": DEVIATIONS,
        "documents": {**registration["documents"],
                      "confirm_document": CONFIRM_DOCUMENT},
        "backups_never_substituted": True,
        "readiness": readiness,
        "preregistration": registration.get("preregistration"),
        "rules_hash": registration.get("rules_hash"),
        "operating_point_rule": {
            "min_recovery": R.OPERATING_POINT_MIN_RECOVERY,
            "resamples": R.OPERATING_POINT_BOOTSTRAP_RESAMPLES,
            "statuses_by_frame": {w: ((e.get("stability") or {}).get("status"))
                                  for w, e in frozen_frames(membership).items()},
            "frozen_point_authoritative": True,
            "runner_up_arm": "sensitivity only; licenses no claim"},
        "calibration_policy": {"rule": R.CALIBRATION_POLICY,
                               "frame_offsets": list(R.CALIBRATION_FRAME_OFFSETS),
                               "topics_per_frame": R.CALIBRATION_TOPICS_PER_FRAME},
        "no_composed_cells_before_this_record": True,
        "immutable_after": "this record; lifecycle.assert_no_post_freeze_"
                           "mutation refuses any earlier stage",
    }


def run_freeze(tree: L.ConfirmTree, *, producing_commit: str | None = None,
               environment_digest: str = "",
               repo_root: Path | str | None = None,
               blocks_per_frame: int | None = None) -> L.StageOutcome:
    repo = Path(repo_root) if repo_root is not None else Path(tree.context.repo_root)
    commit = producing_commit or gitinfo.head_commit(repo)
    return L.run_stage(
        tree, L.STAGE_FROZEN,
        compute=lambda prev: freeze_payload(
            tree, prev, producing_commit=commit, repo_root=repo,
            blocks_per_frame=blocks_per_frame),
        producing_commit=commit, environment_digest=environment_digest)


def load_freeze(tree: L.ConfirmTree) -> tuple[dict[str, Any], str]:
    payload = L.read_stage_record(tree, L.STAGE_FROZEN)
    record_hash = fs.read_json(tree.stage_record(L.STAGE_FROZEN))["record_hash"]
    return payload, record_hash


def assert_matches_freeze(freeze: Mapping[str, Any], *, claimed: Mapping[str, Any],
                          where: str) -> None:
    moved = {k: (freeze["design"].get(k), v) for k, v in claimed.items()
             if freeze["design"].get(k) != v}
    if moved:
        raise ProtocolError(f"{where}: the design in use differs from the "
                            f"freeze on {moved}")
