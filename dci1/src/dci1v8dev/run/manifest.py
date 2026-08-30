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

import hashlib
import json
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
                           DESIGN_DOCUMENT, PILOT_DOCUMENT, SUPERSEDES)
from dci1v8dev.run import seeds
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import EVIDENCE_DIRNAME, StudyContext
from dci1v8dev.run.lifecycle import instrument_hashes
from dci1v8dev.verifiers import source_hashes as verifier_source_hashes
from dci1v8dev.wordings import V8_FRAMES, assert_v8_instrument

__all__ = ["PROTOCOL_VERSION", "DOCUMENTS", "Blocker", "document_hashes",
           "package_hashes", "rule_table", "frame_reference",
           "decoding_policy_form", "build_manifest", "signing_blockers",
           "assert_signable", "sign_registration", "ensure_registration",
           "load_manifest", "manifest_hash"]

PROTOCOL_VERSION = "8.0-pilot"
DOCUMENTS = (DESIGN_DOCUMENT, PILOT_DOCUMENT, BASE_PREREGISTRATION)


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
        raise ProtocolError(f"a rule constant of type {type(value).__name__} "
                            "cannot be bound")
    table = {name: _plain(getattr(R, name)) for name in dir(R)
             if name.isupper() and not name.startswith("_")
             and isinstance(getattr(R, name), (bool, int, float, str, tuple, list))}
    for name in ("FRAME_RELIABILITY_MARGIN", "FRAME_REFERENCE_SOURCE",
                 "RESCREEN_TOPIC_SOURCE", "RESCREEN_TOPICS_PER_AREA",
                 "GATE0_TOPICS", "GATE0_DRAWS", "MIN_LOCAL_FAMILIES",
                 "MIN_CORE_REFERENCES", "MIN_BACKUPS", "NO_COMPOSED_CELLS",
                 "PILOT_CRITERIA"):
        table[f"pilot.{name}"] = _plain(getattr(S, name))
    return table


def frame_reference(repo_root: Path | str) -> dict[str, Any]:
    """The v7 frames' marker-absent shares per model, bound by content."""
    path = Path(repo_root) / S.FRAME_REFERENCE_SOURCE
    if not path.exists():
        raise Blocker(f"the FRAME_RELIABILITY criterion is stated against "
                      f"{S.FRAME_REFERENCE_SOURCE}, which is not at {path}; "
                      "run tools/v8_frame_reference.py")
    data = json.loads(path.read_text())
    return {"path": S.FRAME_REFERENCE_SOURCE,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "statistic": data.get("statistic"),
            "v7_frames": data.get("v7_frames"),
            "models": {m: {"reference_tree": v.get("reference_tree"),
                           "best_v7_frame_share": v.get("best_v7_frame_share"),
                           "best_v7_frames": v.get("best_v7_frames"),
                           "shares": (v.get("by_tree") or {}).get(
                               v.get("reference_tree") or "", {}).get(
                               "marker_absent_share")}
                       for m, v in (data.get("models") or {}).items()}}


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
        "frame_reference": frame_reference(repo_root),
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
                                    "second_pass_batch_topics":
                                        R.RESCREEN_BATCH_TOPICS,
                                    "second_pass_max_batches":
                                        R.RESCREEN_MAX_BATCHES,
                                    "calibration_topics": C.N_CALIBRATION,
                                    "calibration_draws": C.M_CAL},
                   "completion_caps": list(C.COMPLETION_CAPS),
                   "target_grid": list(C.TARGET_GRID),
                   "focal_grid": list(C.FOCAL_GRID),
                   "no_composed_cells": S.NO_COMPOSED_CELLS},
        "lifecycle": {"stages": list(S.STAGE_SEQUENCE),
                      "generation_stages": list(S.GENERATION_STAGES),
                      "terminal_statuses": list(S.TERMINAL_STATUSES),
                      "record_files": dict(S.STAGE_RECORD_FILES)},
        "criteria": {"names": list(S.PILOT_CRITERIA),
                     "evaluated_by": f"{S.STAGE_REPORT} on signed records only",
                     "frame_reliability_margin": S.FRAME_RELIABILITY_MARGIN,
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
                     (lambda: frame_reference(repo_root), "frame reference"),
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
