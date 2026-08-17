"""Study-wide registration (§4, item 13): the signed manifest and signing
key, created before any qualification. Study-wide rules freeze here; E2B
outcomes cannot change them for later replications.
"""
from __future__ import annotations

from typing import Any

from dci1v3.engine import fs, gitinfo, store
from dci1v3.engine.context import StudyContext
from dci1v3.engine.environment import (
    dependency_digest,
    environment_digest,
    environment_record,
)
from dci1v3.engine.signing import create_signing_key, sign_payload
from dci1v3.errors import StateError
from dci1v3.models.registry import registration_models
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_file
from dci1v3.verifiers import source_hashes


def register_study(context: StudyContext) -> dict[str, Any]:
    """Create the signing key and the signed study-wide manifest."""
    if context.registration_manifest.exists():
        raise StateError("the study is already registered; registration is "
                         "single-shot")
    gitinfo.assert_clean_worktree(context.repo_root)
    commit = gitinfo.head_commit(context.repo_root)
    gitinfo.assert_sources_in_commit(context.repo_root, commit)
    key_hash = create_signing_key(context.signing_key_path)
    env = environment_record(context)
    payload: dict[str, Any] = {
        "protocol": C.PROTOCOL, "protocol_version": C.PROTOCOL_VERSION,
        "study_id": context.study_id, "namespace": context.namespace,
        "hash_function": C.HASH_FUNCTION,
        "models": registration_models(),
        "execution_order": [m["model_key"]
                            for m in sorted(registration_models(),
                                            key=lambda m:
                                            m["execution_order"])],
        "root_seeds": {
            "generation": C.GENERATION_ROOT_SEED,
            "pseudo_run": C.PSEUDO_RUN_ROOT_SEED,
            "bootstrap": C.BOOTSTRAP_ROOT_SEED,
            "topic_split": C.TOPIC_SPLIT_SEED,
            "gate1_sample": C.GATE1_SAMPLE_SEED,
            "engine": C.ENGINE_SEED,
        },
        "decoding": C.DECODING, "cap_grid": list(C.CAP_GRID),
        "sesoi": C.SESOI,
        "exchangeability_margin": C.EXCHANGEABILITY_MARGIN,
        "verifier_source_hashes": source_hashes(),
        "constants_source_hash": sha_file(
            __import__("dci1v3.protocol.constants",
                       fromlist=["__file__"]).__file__),
        "signing_key_hash": key_hash,
        "producing_commit": commit,
        "environment_digest": environment_digest(env),
        **dependency_digest(context),
    }
    record = sign_payload(payload, context.signing_key_path)
    fs.write_json_once(context.registration_manifest, record)
    store.replicate(context.registration_dir,
                    context.durable_study_root / "registration")
    return {"registered": True, "record_hash": record["record_hash"],
            "producing_commit": commit}
