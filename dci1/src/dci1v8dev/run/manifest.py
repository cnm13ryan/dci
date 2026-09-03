"""The pilot manifest: every study-wide binding, as one signed payload.

What v7's registration manifest is to the registered study, this is to the
pilot: the documents by hash, the producing code by hash, every constant of
the rule layer by value, the two instrument hashes, the pinned models, the
topic split, the seed domains, the stage sequence, and the four criteria the
report will evaluate --- signed once per root, before any row exists, so
that nothing the pilot measures can move what it is measured against.

It is **not a registration** of the v8 protocol. The manifest says so in
its own ``status`` field; the study id is ``dci1v8`` under a pilot root and
the classification on every row names a development candidate.
"""
from __future__ import annotations

import types
from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, store
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODELS
from dci1v4.protocol.hashing import sha_file, sha_obj
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import TopicBank, load_bank

import dci1v8dev
from dci1v8dev import rules as R
from dci1v8dev.run import (BASE_PREREGISTRATION, CLASSIFICATION,
                           DESIGN_DOCUMENT, FRAME_DOCUMENT, PILOT_DOCUMENT,
                           PRESCREEN_DOCUMENT, SUPERSEDES)
from dci1v8dev.run import seeds
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import EVIDENCE_DIRNAME, StudyContext
from dci1v8dev.run.lifecycle import instrument_hashes
from dci1v8dev.verifiers import source_hashes as verifier_source_hashes
from dci1v8dev.wordings import V8_FRAMES, assert_v8_instrument

__all__ = ["PROTOCOL_VERSION", "DOCUMENTS", "Blocker", "document_hashes",
           "package_hashes", "rule_table",
           "decoding_policy_form", "build_manifest", "signing_blockers",
           "assert_signable", "sign_registration", "ensure_registration",
           "load_manifest", "manifest_hash"]

PROTOCOL_VERSION = "8.1-pilot"
DOCUMENTS = (DESIGN_DOCUMENT, PILOT_DOCUMENT, FRAME_DOCUMENT,
             PRESCREEN_DOCUMENT, BASE_PREREGISTRATION)


class Blocker(ProtocolError):
    """A named reason the pilot manifest may not be signed."""


def document_hashes(repo_root: Path | str) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in DOCUMENTS:
        path = Path(repo_root) / rel
        if not path.exists():
            raise Blocker(f"the pilot binds the hash of {rel} and the file "
                          f"is not at {path}")
        out[rel] = sha_obj({"path": rel, "bytes": path.read_bytes().hex()})
    return out


def package_hashes() -> dict[str, str]:
    """Every source file of ``dci1v8dev`` (the rule layer, the instrument and
    this execution layer), by content."""
    root = Path(dci1v8dev.__file__).resolve().parent
    return {str(p.relative_to(root.parent)): sha_file(p)
            for p in sorted(root.rglob("*.py")) if "__pycache__" not in p.parts}


def rule_table() -> dict[str, Any]:
    """Every constant of ``dci1v8dev.rules`` and the execution layer's own."""
    def _plain(value: Any) -> Any:
        if isinstance(value, (bool, int, float, str)) or value is None:
            return value
        if isinstance(value, (tuple, list)):
            return [_plain(v) for v in value]
        if isinstance(value, Mapping):
            # A per-model rule table (rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL)
            # is a constant like any other and the most consequential kind to
            # leave unbound: it decides what a named replication measures.
            return {str(k): _plain(v) for k, v in sorted(value.items())}
        raise ProtocolError(f"a rule constant of type {type(value).__name__} "
                            "cannot be bound")
    # Every uppercase name, and `_plain` refuses what it cannot bind. The
    # filter used to be an isinstance allow-list, which silently *dropped* a
    # constant of an unlisted type instead of raising --- so a dict-valued
    # rule was absent from the signed table with nothing to say so.
    table = {name: _plain(getattr(R, name)) for name in dir(R)
             if name.isupper() and not name.startswith("_")
             and not isinstance(getattr(R, name), types.ModuleType)}
    for name in ("WORDING_REFERENCE_BOUND", "WORDING_POLICY_OPTIONS",
                 "WORDING_POLICY_STATUS", "WORDING_POLICY",
                 "FRAME_CONDITIONING", "FRAMES", "FRAME_STATES",
                 "FRAME_FAILURE_STATUSES", "CONFIRMATORY_BLOCKS_PER_FRAME",
                 "CONFIRMATORY_FRAME_OFFSETS", "CONFIRMATORY_FRAME_PASSES",
                 "CONFIRMATORY_BLOCKS_TOTAL",
                 "REPORT_AGGREGATION", "DECIDED_CRITERIA",
                 "RESCREEN_TOPIC_SOURCE", "RESCREEN_TOPICS_PER_AREA",
                 "GATE0_TOPICS", "GATE0_DRAWS", "MIN_LOCAL_FAMILIES",
                 "MIN_CORE_REFERENCES", "MIN_BACKUPS", "NO_COMPOSED_CELLS",
                 "PILOT_CRITERIA"):
        table[f"pilot.{name}"] = _plain(getattr(S, name))
    return table


def decoding_policy_form() -> dict[str, Any]:
    """The decoding policy every generating stage uses, minus the fields that
    are per model or per stage (the cap)."""
    from dci1v4.generation.backend import build_plan

    plan = build_plan(MODELS[0], stage="manifest", max_new_tokens=1)
    keep = ("temperature", "top_p", "top_k", "engine_seed", "strategy",
            "reasoning_mode", "decoding_policy", "skip_special_tokens",
            "quantization")
    return {k: plan[k] for k in keep}


def build_manifest(context: StudyContext, *, producing_commit: str,
                   bank: TopicBank | None = None,
                   repo_root: Path | str = ".") -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    hashes = instrument_hashes()
    from dci1v7.verifiers import verifier_source_hash as v7_verifier_hash
    from dci1v7.protocol.wordings import wording_source_hash as v7_wording_hash

    return {
        "study_id": context.study_id,
        "namespace": context.namespace,
        "protocol": "DCI-1",
        "protocol_version": PROTOCOL_VERSION,
        "classification": CLASSIFICATION,
        "status": ("pilot manifest of a development candidate; the v8 "
                   "protocol is NOT registered, NOT frozen, and no "
                   "confirmatory or composed row exists or can be produced "
                   "by this layer"),
        "supersedes": SUPERSEDES,
        "producing_commit": producing_commit,
        "documents": document_hashes(repo_root),
        "package": package_hashes(),
        "rules": rule_table(),
        "instrument": {
            **hashes,
            "verifier_sources": verifier_source_hashes(),
            "v7_verifier_hash": v7_verifier_hash(),
            "v7_wording_hash": v7_wording_hash(),
            "frames": list(V8_FRAMES),
            "instrument_assertions": assert_v8_instrument(),
        },
        "wording_diagnostic": {
            "primary": "per (frame, family, q): sample, exact compliance, "
                       "chance on the unconstrained cell, iota, SE, and the "
                       "comparison with the other frames (run/wording.py)",
            "reference_bound": S.WORDING_REFERENCE_BOUND,
            "reference_bound_source": "§13.7 STABILITY_EQUIVALENCE_BOUND, "
                                      "descriptive only",
            "classes": ["CONSISTENT", "UNRESOLVED", "WORDING_SENSITIVE"],
            "selection_rule": None,
            "v7_frame_statistics_affect_verdicts": False,
            "wording_policy": {"status": S.WORDING_POLICY_STATUS,
                               "policy": S.WORDING_POLICY,
                               "decided": "2026-08-30 (researcher): the frame "
                                          "is part of the experimental "
                                          "condition; no frame retained or "
                                          "discarded on the diagnostic",
                               "options": list(S.WORDING_POLICY_OPTIONS),
                               "evidence_admissible": "solo, pre-screen and "
                                                      "calibration only"},
        },
        "frame_conditioning": {
            "policy": S.FRAME_CONDITIONING,
            "document": FRAME_DOCUMENT,
            "frames": list(S.FRAMES),
            "frame_of_block": "block_index % N_WORDINGS",
            "difficulty": "iota(X, f) per frame; n*(f), m*(f), LOCAL(R, f), "
                          "SPECTRUM(R, f), core, spectrum points, coverage "
                          "and backups per frame",
            "pooled_over_frames": "descriptive only; decides nothing",
            "screen_and_second_pass": "per frame (2026-09-03): the screen "
                                      "and every batch are laid out one pass "
                                      "per frame offset, each frame is "
                                      "screened on its own blocks, and Gate 2 "
                                      "forwards each frame's set against the "
                                      "frame's own iota_A(f); a rung is "
                                      "calibrated on the blocks of the frames "
                                      "whose evidence selected it "
                                      "(rules.RETENTION_POLICY)",
            "unsupported_frame": "recorded with its §12.3/§12.4 status; the "
                                 "other frames continue; terminal only when "
                                 "no frame is supported",
            "frame_states": list(S.FRAME_STATES),
            "confirmatory_blocks_per_frame": S.CONFIRMATORY_BLOCKS_PER_FRAME,
            "confirmatory_passes": S.CONFIRMATORY_FRAME_PASSES,
            "frame_of_confirmatory_block": "(position + frame_offsets[pass]) "
                                           "% N_WORDINGS; the offsets are "
                                           "distinct modulo N_WORDINGS, so a "
                                           "frame's blocks are distinct "
                                           "topics",
            "estimands": "Delta_R(f) and the difficulty-response slope per "
                         "frame; cross-frame comparison afterwards; never a "
                         "silent average",
            "report_aggregation": S.REPORT_AGGREGATION,
        },
        "models": [{"model_key": m.model_key, "model_id": m.model_id,
                    "revision": m.revision, "family": m.family,
                    "thinking_policy": m.thinking_policy}
                   for m in MODELS],
        "backend": {"seam": "dci1v4.generation.backend (pinned; TP=1 lanes)",
                    "decoding_policy_form": decoding_policy_form()},
        "topics": bank.split_identity,
        "seeds": {"generation_root_seed": seeds.GENERATION_ROOT_SEED,
                  "bootstrap_root_seed": seeds.BOOTSTRAP_ROOT_SEED,
                  "domains": list(seeds.V8_DOMAINS),
                  "screen_base_seed_rule": "seeds.screen_seed(model_id, stage)"},
        "design": {"sample_sizes": {"prescreen_topics": C.N_PRESCREEN,
                                    "screen_draws": C.LADDER_SCREEN_DRAWS,
                                    "screen_frame_passes": R.SCREEN_FRAME_PASSES,
                                    "screen_topics_per_frame":
                                        R.SCREEN_TOPICS_PER_FRAME,
                                    "second_pass_batch_topics":
                                        R.RESCREEN_BATCH_TOPICS,
                                    "second_pass_max_batches":
                                        R.RESCREEN_MAX_BATCHES,
                                    "calibration_topics": C.N_CALIBRATION,
                                    "calibration_draws": C.M_CAL,
                                    # The allocation is per model since
                                    # 2026-08-31; these two are the *default*
                                    # and `calibration_allocation.by_model`
                                    # below says what each model runs. Named
                                    # for what they are, so a reader cannot
                                    # take them for the study's one value.
                                    "calibration_frame_passes_default":
                                        R.CALIBRATION_FRAME_PASSES,
                                    "calibration_topics_per_frame_default":
                                        R.CALIBRATION_TOPICS_PER_FRAME},
                   "calibration_allocation": {
                       "default_frame_offsets":
                           list(R.CALIBRATION_FRAME_OFFSETS),
                       "default_topics_per_frame":
                           R.CALIBRATION_TOPICS_PER_FRAME,
                       "default_topics_per_frame_per_split":
                           R.CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT,
                       "default_generations_per_rung":
                           R.CALIBRATION_GENERATIONS_PER_RUNG,
                       # The allocation is per model: the default above, and
                       # the overrides the researcher has raised. Bound here
                       # so the signed manifest states what each model in
                       # this study will actually be measured at.
                       "by_model": {
                           m.model_key: {
                               "frame_offsets":
                                   list(R.calibration_frame_offsets(m.model_key)),
                               "passes": R.calibration_passes(m.model_key),
                               "topics_per_frame":
                                   R.calibration_topics_per_frame(m.model_key),
                               "topics_per_frame_per_split":
                                   R.calibration_topics_per_frame_per_split(
                                       m.model_key),
                               "generations_per_rung":
                                   R.calibration_generations_per_rung(m.model_key),
                               "is_default": R.calibration_frame_offsets(
                                   m.model_key) == R.CALIBRATION_FRAME_OFFSETS,
                           } for m in MODELS},
                       "max_passes": R.CALIBRATION_MAX_PASSES,
                       "max_topics_per_frame": R.CALIBRATION_MAX_TOPICS_PER_FRAME,
                       "rule": "Approach A measures every difficulty inside "
                               "a frame; a calibration pass renders every "
                               "calibration topic under one frame and the "
                               "passes' offsets are distinct modulo the "
                               "wordings, so each frame is measured on "
                               "passes/N_WORDINGS of the topics and no topic "
                               "recurs within a frame. Four passes is the "
                               "ceiling: every frame then holds every "
                               "calibration topic"},
                   # The confirmatory allocation is a property of the design,
                   # not of a model: no override, no run-time input. Bound
                   # here so the signed manifest states the block count every
                   # frame-specific estimate will eventually be formed at,
                   # before any confirmatory row exists.
                   "confirmatory_allocation": R.confirmatory_allocation(),
                   "screen_allocation": {
                       "frame_offsets": list(R.SCREEN_FRAME_OFFSETS),
                       "passes": R.SCREEN_FRAME_PASSES,
                       "topics_per_frame": R.SCREEN_TOPICS_PER_FRAME,
                       "batch_layout": R.RESCREEN_BATCH_LAYOUT},
                   "retention": {"policy": R.RETENTION_POLICY,
                                 "target_basis": R.RETENTION_TARGET_BASIS,
                                 "comparator": R.RETENTION_COMPARATOR,
                                 "decided_at": S.STAGE_GATE2},
                   "completion_caps": list(C.COMPLETION_CAPS),
                   "target_grid": list(C.TARGET_GRID),
                   "focal_grid": list(C.FOCAL_GRID),
                   "no_composed_cells": S.NO_COMPOSED_CELLS},
        "lifecycle": {"stages": list(S.STAGE_SEQUENCE),
                      "generation_stages": list(S.GENERATION_STAGES),
                      "terminal_statuses": list(S.TERMINAL_STATUSES),
                      "record_files": dict(S.STAGE_RECORD_FILES)},
        "criteria": {"names": list(S.PILOT_CRITERIA),
                     "decided": list(S.DECIDED_CRITERIA),
                     "evaluated_by": f"{S.STAGE_REPORT} on signed records only",
                     "min_local_families": S.MIN_LOCAL_FAMILIES,
                     "min_core_references": S.MIN_CORE_REFERENCES,
                     "min_backups": S.MIN_BACKUPS,
                     "coverage_rule": {k: v for k, v in rule_table().items()
                                       if k.startswith("SPECTRUM_")}},
    }


def signing_blockers(context: StudyContext, *, repo_root: Path | str,
                     bank: TopicBank | None = None) -> list[str]:
    blockers: list[str] = []
    for fn, what in ((lambda: document_hashes(repo_root), "documents"),
                     (assert_v8_instrument, "instrument assertions")):
        try:
            fn()
        except Exception as error:                           # noqa: BLE001
            blockers.append(f"{what}: {error}")
    try:
        bank = bank if bank is not None else load_bank()
        if not bank.complete:
            blockers.append("topics: Calibration-B is not authored; the "
                            "pilot's calibration needs both splits")
    except Exception as error:                               # noqa: BLE001
        blockers.append(f"topics: {error}")
    return blockers


def assert_signable(context: StudyContext, *, repo_root: Path | str,
                    bank: TopicBank | None = None) -> None:
    blockers = signing_blockers(context, repo_root=repo_root, bank=bank)
    if blockers:
        raise Blocker("the pilot manifest cannot be signed: "
                      + "; ".join(blockers))


def manifest_hash(manifest: Mapping[str, Any]) -> str:
    return sha_obj(dict(manifest))


def sign_registration(context: StudyContext, *, producing_commit: str,
                      bank: TopicBank | None = None,
                      repo_root: Path | str = ".") -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    assert_signable(context, repo_root=repo_root, bank=bank)
    manifest = build_manifest(context, producing_commit=producing_commit,
                              bank=bank, repo_root=repo_root)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    context.registration_root.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(context.registration_manifest,
                       sign_payload(manifest, context.signing_key_path))
    durable = (Path(context.durable_root) / EVIDENCE_DIRNAME
               / context.registration_root.name)
    store.replicate(context.registration_root, durable)
    store.assert_replicated(context.registration_root, durable)
    return manifest


def load_manifest(context: StudyContext) -> dict[str, Any]:
    if not context.registration_manifest.exists():
        raise IntegrityError(f"no pilot manifest at "
                             f"{context.registration_manifest}")
    record = fs.read_json(context.registration_manifest)
    return verify_signed(record, context.signing_key_path,
                         where="pilot manifest")


def ensure_registration(context: StudyContext, *, producing_commit: str,
                        bank: TopicBank | None = None,
                        repo_root: Path | str = ".") -> tuple[dict[str, Any], bool]:
    """The manifest for this root: signed now, or the signed one verified
    against a rebuild. Every replication of one root registers under one
    commit and one set of bindings; a difference is refused, not merged."""
    if not context.registration_manifest.exists():
        return sign_registration(context, producing_commit=producing_commit,
                                 bank=bank, repo_root=repo_root), True
    signed = load_manifest(context)
    rebuilt = build_manifest(context, producing_commit=producing_commit,
                             bank=bank, repo_root=repo_root)
    if rebuilt != signed:
        moved = sorted(k for k in set(signed) | set(rebuilt)
                       if signed.get(k) != rebuilt.get(k))
        if moved == ["producing_commit"]:
            raise IntegrityError(
                f"the signed pilot manifest was produced at "
                f"{signed['producing_commit']} and this replication is "
                f"registering at {producing_commit}. Every replication in a "
                "root registers under one commit; a different commit is a "
                "different pilot and takes a fresh root")
        raise IntegrityError(
            f"the signed pilot manifest disagrees with a rebuild on {moved}; "
            "a binding that moved after signing is a different pilot and "
            "takes a fresh root")
    return signed, False
