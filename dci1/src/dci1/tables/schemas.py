"""Typed schemas for the three registered derived tables (Addendum A §3).

Frozen after protocol freeze: added, removed, renamed or retyped columns are
rejected, and unknown columns are rejected rather than ignored. Readers
validate ``schema_name``/``schema_version`` before parsing (R19, R21, R35).

Byte-identity note (R26): every derived artifact's ``created_at_utc`` (and the
analysis rows' ``wall_clock_utc``) is *input-derived* — the cache stage's seal
timestamp — so that regeneration from sealed evidence is byte-identical. The
true wall-clock moments of each build live in the append-only run record.
"""
from __future__ import annotations

import pyarrow as pa

from dci1.protocol.constants import ProtocolError

SCHEMA_VERSIONS = {"accepted": "1.0.0", "scored": "1.0.0",
                   "analysis": "1.0.0"}
ADDENDUM_VERSION = "A-1.0"

_HEADER = [
    ("study_id", pa.string()), ("model_id", pa.string()),
    ("freeze_id", pa.string()), ("freeze_record_hash", pa.string()),
    ("schema_name", pa.string()), ("schema_version", pa.string()),
    ("addendum_version", pa.string()), ("writer_commit", pa.string()),
    ("writer_dirty", pa.bool_()), ("created_at_utc", pa.string()),
]

ACCEPTED_FIELDS = _HEADER + [
    ("model_revision", pa.string()), ("block_id", pa.string()),
    ("topic_id", pa.string()), ("stratum_id", pa.string()),
    ("arm", pa.string()), ("presentation_order", pa.string()),
    ("wording_id", pa.string()), ("prompt_hash", pa.string()),
    ("selection_source", pa.string()), ("pseudo_run_id", pa.string()),
    ("selected_pool_index", pa.int64()),
    ("response_content_hash", pa.string()),
    ("cache_record_id", pa.string()), ("token_count", pa.int64()),
    ("finish_reason", pa.string()), ("generation_seed", pa.int64()),
    ("resampling_seed", pa.int64()),
]

SCORED_FIELDS = _HEADER + [
    ("block_id", pa.string()), ("arm", pa.string()),
    ("response_content_hash", pa.string()), ("verifier_id", pa.string()),
    ("verifier_version", pa.string()),
    ("verifier_source_hash", pa.string()),
    ("constraint_id", pa.string()), ("constraint_role", pa.string()),
    ("wording_id", pa.string()), ("verdict", pa.bool_()),
    ("verdict_reason_code", pa.string()), ("parse_status", pa.string()),
    ("scoring_rule", pa.string()), ("score_value", pa.float64()),
    ("manipulation_check_value", pa.float64()),
    ("compliance_flag", pa.bool_()),
    ("failure_taxonomy_code", pa.string()),
    ("cache_record_id", pa.string()),
]

ANALYSIS_FIELDS = _HEADER + [
    ("model_revision", pa.string()), ("family_id", pa.string()),
    ("estimand_id", pa.string()), ("contrast_id", pa.string()),
    ("estimator_id", pa.string()), ("point_estimate", pa.float64()),
    ("ci_lower", pa.float64()), ("ci_upper", pa.float64()),
    ("ci_method", pa.string()), ("n_bootstrap", pa.int64()),
    ("simultaneous", pa.bool_()),
    ("multiplicity_adjustment", pa.string()),
    ("equivalence_lower", pa.float64()), ("equivalence_upper", pa.float64()),
    ("smallest_effect_of_interest", pa.float64()),
    ("claim_rule_id", pa.string()), ("claim_outcome", pa.string()),
    ("n_blocks", pa.int64()), ("n_observations", pa.int64()),
    ("bootstrap_seed", pa.int64()), ("analysis_stage", pa.string()),
    ("masked", pa.bool_()),
    ("input_accepted_hash", pa.string()),
    ("input_scored_hash", pa.string()),
    ("protocol_identity", pa.string()),
    ("input_manifest_hashes", pa.string()),
    ("resampling_root_seed", pa.int64()),
    ("masking_state", pa.string()),
    ("environment_record_hash", pa.string()),
    ("analysis_command", pa.string()),
    ("wall_clock_utc", pa.string()),
]

_SCHEMAS = {"accepted": ACCEPTED_FIELDS, "scored": SCORED_FIELDS,
            "analysis": ANALYSIS_FIELDS}

PRIMARY_KEYS = {
    "accepted": ("study_id", "model_id", "block_id", "arm"),
    "scored": ("study_id", "model_id", "block_id", "arm", "verifier_id"),
    "analysis": ("study_id", "model_id", "family_id", "estimand_id",
                 "contrast_id"),
}


def arrow_schema(name: str) -> pa.Schema:
    if name not in _SCHEMAS:
        raise ProtocolError(f"unknown schema {name!r}")
    return pa.schema(_SCHEMAS[name])


def validate_columns(name: str, columns: list[str]) -> None:
    declared = [f for f, _t in _SCHEMAS[name]]
    extra = set(columns) - set(declared)
    missing = set(declared) - set(columns)
    if extra:
        raise ProtocolError(
            f"{name}: unknown columns {sorted(extra)} are rejected, never "
            f"ignored (Addendum A R35)")
    if missing:
        raise ProtocolError(f"{name}: missing columns {sorted(missing)}")


def validate_table(name: str, table: pa.Table, *,
                   expect_rows: int | None = None,
                   forbid_nulls: bool = False) -> None:
    validate_columns(name, table.column_names)
    meta = {k.decode(): v.decode()
            for k, v in (table.schema.metadata or {}).items()}
    if meta.get("schema_name") != name or \
            meta.get("schema_version") != SCHEMA_VERSIONS[name]:
        raise ProtocolError(
            f"{name}: schema metadata {meta.get('schema_name')!r}/"
            f"{meta.get('schema_version')!r} does not match the registered "
            f"{name}/{SCHEMA_VERSIONS[name]}; unknown or missing versions "
            f"fail closed (R21)")
    keys = PRIMARY_KEYS[name]
    seen = set()
    key_columns = [table.column(k).to_pylist() for k in keys]
    for row in zip(*key_columns):
        if row in seen:
            raise ProtocolError(f"{name}: duplicate primary key {row}")
        seen.add(row)
    if expect_rows is not None and table.num_rows != expect_rows:
        raise ProtocolError(
            f"{name}: {table.num_rows} rows, expected exactly {expect_rows}")
    if forbid_nulls:
        for column in table.column_names:
            if table.column(column).null_count:
                raise ProtocolError(f"{name}: null values in {column!r}")
