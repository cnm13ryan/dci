"""The confirmatory manifest: every study-wide binding, signed once per root.

What the pilot manifest is to the pilot, this is to the confirmatory
study: the documents by hash, the producing package by hash (the v8
package including this layer and the v7 analysis modules it calls), the
rule layer by value, the allocation and multiplicity rule, the pilot roots
each model's design is read from (by manifest hash), the instrument
hashes, the models, the topic split and the seed domains --- before any
composed row exists.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, store
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODELS
from dci1v4.protocol.hashing import sha_file, sha_obj
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import TopicBank, load_bank

from dci1v8dev.confirm import (CLASSIFICATION, CONFIRM_DOCUMENT,
                               MEMBERSHIP_DOCUMENT, PREREGISTRATION_DOCUMENT,
                               PROTOCOL_VERSION)
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import precision as P
from dci1v8dev.run import (BASE_PREREGISTRATION, DESIGN_DOCUMENT,
                           FRAME_DOCUMENT, PILOT_DOCUMENT, PRESCREEN_DOCUMENT)
from dci1v8dev.run import seeds
from dci1v8dev.run.context import StudyContext, EVIDENCE_DIRNAME
from dci1v8dev.run.lifecycle import instrument_hashes
from dci1v8dev.run.manifest import (decoding_policy_form, package_hashes,
                                    rule_table)

__all__ = ["DOCUMENTS", "analysis_code_hashes", "document_hashes",
           "build_manifest", "sign_registration", "ensure_registration",
           "load_manifest", "manifest_hash", "Blocker"]

DOCUMENTS = (PREREGISTRATION_DOCUMENT, CONFIRM_DOCUMENT, FRAME_DOCUMENT,
             PRESCREEN_DOCUMENT, DESIGN_DOCUMENT, PILOT_DOCUMENT,
             BASE_PREREGISTRATION)
#: The registered analysis code the confirmatory analysis calls, hashed.
V7_ANALYSIS_MODULES = ("analysis/observations.py", "analysis/estimators.py",
                       "analysis/bootstrap.py", "analysis/intervals.py",
                       "analysis/spectrum.py", "analysis/boundary.py",
                       "analysis/claims.py")


class Blocker(ProtocolError):
    pass


def document_hashes(repo_root: Path | str) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in DOCUMENTS:
        path = Path(repo_root) / rel
        if not path.exists():
            raise Blocker(f"the manifest binds {rel} and it is not at {path}")
        out[rel] = sha_obj({"path": rel, "bytes": path.read_bytes().hex()})
    return out


def analysis_code_hashes() -> dict[str, str]:
    import dci1v7
    root = Path(dci1v7.__file__).resolve().parent
    return {f"dci1v7/{rel}": sha_file(root / rel) for rel in V7_ANALYSIS_MODULES}


def build_manifest(context: StudyContext, *, producing_commit: str,
                   pilot_roots: Mapping[str, str],
                   bank: TopicBank | None = None,
                   repo_root: Path | str = ".") -> dict[str, Any]:
    from dci1v8dev.confirm.pilot_import import open_pilot
    bank = bank if bank is not None else load_bank()
    sources = {}
    for model_key, root in sorted(pilot_roots.items()):
        src = open_pilot(Path(root), model_key,
                         synthetic=context.namespace == "confirm-synthetic")
        sources[model_key] = src.as_record()
    return {
        "study_id": context.study_id, "namespace": context.namespace,
        "layer": "confirm", "protocol": "DCI-1",
        "protocol_version": PROTOCOL_VERSION,
        "classification": CLASSIFICATION,
        "status": ("confirmatory manifest of the v8 design; the design is "
                   "frozen per model at FROZEN and no composed row exists "
                   "before CONFIRMATORY_GENERATION"),
        "producing_commit": producing_commit,
        "documents": document_hashes(repo_root),
        "preregistration": {"path": PREREGISTRATION_DOCUMENT,
                            "hash": document_hashes(repo_root)[PREREGISTRATION_DOCUMENT]},
        "rules_hash": sha_obj(rule_table()),
        "package": package_hashes(),
        "analysis_code": analysis_code_hashes(),
        "rules": rule_table(),
        "instrument": instrument_hashes(),
        "pilot_sources": sources,
        "allocation": {"blocks_per_frame": P.ALLOCATION,
                       "source": "rules.CONFIRMATORY_BLOCKS_PER_FRAME",
                       "precision_rule": P.PRECISION_RULE,
                       "multiplicity_rule": P.MULTIPLICITY_RULE,
                       "rule_scenarios": list(P.RULE_SCENARIOS),
                       "scenarios": P.SCENARIOS,
                       "precondition": P.PRECONDITION,
                       "family_size_per_frame": P.FAMILY_SIZE_PER_FRAME,
                       "draws": C.M_DRAWS,
                       "completion_caps": list(C.COMPLETION_CAPS)},
        "models": [{"model_key": m.model_key, "model_id": m.model_id,
                    "revision": m.revision} for m in MODELS],
        "backend": {"seam": "dci1v4.generation.backend (pinned; TP=1 lanes)",
                    "decoding_policy_form": decoding_policy_form()},
        "topics": bank.split_identity,
        "seeds": {"generation_root_seed": seeds.GENERATION_ROOT_SEED,
                  "bootstrap_root_seed": seeds.BOOTSTRAP_ROOT_SEED,
                  "domains": list(seeds.V8_DOMAINS)},
        "lifecycle": {"stages": list(L.STAGE_SEQUENCE),
                      "generation_stages": list(L.GENERATION_STAGES),
                      "protected_stages": list(L.PROTECTED_STAGES),
                      "terminal_statuses": list(L.TERMINAL_STATUSES),
                      "record_files": dict(L.STAGE_RECORD_FILES)},
        "membership_document": MEMBERSHIP_DOCUMENT,
    }


def manifest_hash(manifest: Mapping[str, Any]) -> str:
    return sha_obj(dict(manifest))


def sign_registration(context: StudyContext, *, producing_commit: str,
                      pilot_roots: Mapping[str, str],
                      bank: TopicBank | None = None,
                      repo_root: Path | str = ".") -> dict[str, Any]:
    manifest = build_manifest(context, producing_commit=producing_commit,
                              pilot_roots=pilot_roots, bank=bank,
                              repo_root=repo_root)
    key = context.signing_key_path
    key.parent.mkdir(parents=True, exist_ok=True)
    if not key.exists():
        create_signing_key(key)
    context.registration_root.mkdir(parents=True, exist_ok=True)
    path = context.registration_root / L.MANIFEST_FILENAME
    fs.write_json_once(path, sign_payload(manifest, key))
    durable = Path(context.durable_root) / EVIDENCE_DIRNAME / "registration"
    store.replicate(context.registration_root, durable)
    store.assert_replicated(context.registration_root, durable)
    return manifest


def load_manifest(context: StudyContext) -> dict[str, Any]:
    path = context.registration_root / L.MANIFEST_FILENAME
    if not path.exists():
        raise IntegrityError(f"no confirmatory manifest at {path}")
    return verify_signed(fs.read_json(path), context.signing_key_path,
                         where="confirm manifest")


def ensure_registration(context: StudyContext, *, producing_commit: str,
                        pilot_roots: Mapping[str, str],
                        bank: TopicBank | None = None,
                        repo_root: Path | str = ".") -> tuple[dict[str, Any], bool]:
    path = context.registration_root / L.MANIFEST_FILENAME
    if not path.exists():
        return sign_registration(context, producing_commit=producing_commit,
                                 pilot_roots=pilot_roots, bank=bank,
                                 repo_root=repo_root), True
    signed = load_manifest(context)
    rebuilt = build_manifest(context, producing_commit=producing_commit,
                             pilot_roots=pilot_roots, bank=bank,
                             repo_root=repo_root)
    if rebuilt != signed:
        moved = sorted(k for k in set(signed) | set(rebuilt)
                       if signed.get(k) != rebuilt.get(k))
        raise IntegrityError(
            f"the signed confirmatory manifest disagrees with a rebuild on "
            f"{moved}; a binding that moved after signing is a different "
            "study and takes a fresh root")
    return signed, False
