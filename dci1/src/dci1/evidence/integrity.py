"""Execution-integrity checks (prereg §27), named and fail-closed.

Each named ``check_*`` function consumes one execution-constraining codebook
field (§28 check 4). `validate_accepted` runs the row-level checks over an
accepted table against the frozen plan; any violation aborts. These are the
only permitted stops, and none depends on an observed outcome.
"""
from __future__ import annotations

from typing import Any

from dci1.generation.pools import Cell
from dci1.models.adapters import ModelSpec
from dci1.protocol.constants import ProtocolError, StudyConfig
from dci1.protocol.hashing import sha_text
from dci1.protocol.seeds import generation_seed
from dci1.verifiers.registry import verifier_source_hash


def check_prompt_hash_in_plan(row: dict[str, Any],
                              plan_hashes: dict[tuple[str, str], str]) -> None:
    expected = plan_hashes.get((row["block_id"], row["arm"]))
    if expected is None or row["prompt_hash"] != expected:
        raise ProtocolError(
            f"§27 abort: prompt hash of ({row['block_id']}, {row['arm']}) "
            f"is absent from the frozen plan")


def check_model_revision(row: dict[str, Any], spec: ModelSpec) -> None:
    if row.get("model_revision") != spec.revision or \
            row.get("model_id") != spec.model_id:
        raise ProtocolError(
            f"§27 abort: model identity {row.get('model_id')}@"
            f"{row.get('model_revision')} differs from the frozen "
            f"{spec.model_id}@{spec.revision}")


def check_backend_config(row: dict[str, Any], frozen_hash: str) -> None:
    if row.get("backend_config_hash") != frozen_hash:
        raise ProtocolError(
            f"§27 abort: backend configuration hash differs from the frozen "
            f"value for row {row.get('row_id')}")


def check_response_hash(row: dict[str, Any],
                        response_field: str = "response") -> None:
    if sha_text(row[response_field]) != row["response_content_hash"]:
        raise ProtocolError(
            f"§27 abort: stored response of {row.get('row_id')} fails its "
            f"recorded content hash")


def check_row_bytes(store) -> None:
    store.verify_hashes()


def check_seed_derivation(row: dict[str, Any], spec: ModelSpec,
                          stream: str, config: StudyConfig) -> None:
    expected = generation_seed(config.generation_root_seed, stream,
                               spec.model_id, row["prompt_hash"],
                               int(row["pool_index"]))
    if int(row["generation_seed"]) != expected:
        raise ProtocolError(
            f"§27 abort: generation seed of {row.get('row_id')} differs "
            f"from its deterministic derivation")


def check_verifier_hash(frozen_hash: str) -> None:
    current = verifier_source_hash()
    if current != frozen_hash:
        raise ProtocolError(
            f"§27 abort: verifier source hash {current[:12]} differs from "
            f"the frozen {frozen_hash[:12]}")


def check_hardware_class(provenance: dict[str, Any],
                         frozen_archs: list[str]) -> None:
    archs = list((provenance.get("host") or {}).get("gcn_archs") or [])
    if archs != frozen_archs:
        raise ProtocolError(
            f"§27 abort: hardware class {archs} differs from the frozen "
            f"{frozen_archs}")


def validate_accepted(accepted_rows: list[dict[str, Any]],
                      cells: list[Cell], spec: ModelSpec, *, stream: str,
                      config: StudyConfig,
                      frozen_backend_config_hash: str | None = None,
                      frozen_verifier_hash: str | None = None) -> None:
    """Row-level §27 gate over one accepted table; aborts on any violation."""
    plan_hashes = {(c.block_id, c.arm): c.prompt_sha for c in cells}
    seen: set[tuple[str, str]] = set()
    for row in accepted_rows:
        key = (row["block_id"], row["arm"])
        if key in seen:
            raise ProtocolError(
                f"§27 abort: two accepted responses for cell {key}")
        seen.add(key)
        check_prompt_hash_in_plan(row, plan_hashes)
        check_model_revision(row, spec)
        check_response_hash(row)
        check_seed_derivation(row, spec, stream, config)
        if frozen_backend_config_hash is not None:
            check_backend_config(row, frozen_backend_config_hash)
    missing = set(plan_hashes) - seen
    if missing:
        raise ProtocolError(
            f"§27 abort: {len(missing)} cells missing from the accepted "
            f"table, first: {sorted(missing)[:3]}")
    if frozen_verifier_hash is not None:
        check_verifier_hash(frozen_verifier_hash)
