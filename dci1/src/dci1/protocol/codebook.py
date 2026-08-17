"""The codebook (prereg §28): one row per recorded variable, six fields,
four executable checks.

Causal roles: identity, treatment, design, outcome, post_treatment,
provenance. The §21/§28 assertions live here: primary formulas may consume
only declared non-post-treatment fields, and every execution-constraining
field must be consumed by a named §27 check in `evidence.integrity`.
"""
from __future__ import annotations

from typing import Any

from dci1.protocol.constants import ARMS, GENERATION_POOL_SIZE, ProtocolError

ROLES = ("identity", "treatment", "design", "outcome", "post_treatment",
         "provenance")


def _col(name, type_, domain, units, role, definition):
    if role not in ROLES:
        raise ProtocolError(f"bad causal role {role}")
    return {"name": name, "type": type_, "domain": domain, "units": units,
            "causal_role": role, "definition": definition}


_ARM = f"one of {list(ARMS)}"
_BIN = "0 or 1"
_HASH = "64 lower-case hex digits"

CODEBOOKS: dict[str, list[dict[str, Any]]] = {
    "pool": [
        _col("row_id", "str", "model:stream:block:arm:index", "", "identity",
             "The unique identity of one cached pool member."),
        _col("model_key", "str", "registered model slug", "", "identity",
             "Study-internal model identifier."),
        _col("model_id", "str", "HF repository", "", "provenance",
             "Exact model repository."),
        _col("model_revision", "str", "commit hash", "", "provenance",
             "Exact pinned model revision."),
        _col("stream", "str", "generation stream", "", "provenance",
             "Which apparatus stage generated this member."),
        _col("block_id", "str", "block identifier", "", "identity",
             "The block this member's prompt belongs to."),
        _col("arm", "str", _ARM + " or solo:<id>", "", "treatment",
             "The arm this member's prompt belongs to."),
        _col("prompt_hash", "str", _HASH, "", "provenance",
             "SHA-256 of the exact prompt text."),
        _col("pool_index", "int", f"0..{GENERATION_POOL_SIZE - 1}", "",
             "provenance", "This member's index within its cell's pool."),
        _col("generation_seed", "int", "0..2^63-1", "", "provenance",
             "The deterministic level-1 seed of this draw."),
        _col("raw_response", "str", "any text", "", "post_treatment",
             "The complete generated text, immutable raw evidence."),
        _col("final_answer", "str", "any text", "", "post_treatment",
             "The backend's extracted answer (whole generation, stripped)."),
        _col("response_content_hash", "str", _HASH, "", "provenance",
             "SHA-256 of raw_response, computed at write time."),
        _col("token_count", "int", ">=0", "tokens", "post_treatment",
             "Generated token count."),
        _col("finish_reason", "str", "backend finish reason", "",
             "post_treatment", "Why generation stopped."),
        _col("backend_config_hash", "str", _HASH, "", "provenance",
             "Hash of the backend configuration that produced this member."),
        _col("row_sha256", "str", _HASH, "", "provenance",
             "Hash of this stored row's own bytes."),
    ],
    "accepted": [
        _col("row_id", "str", "model:block:arm", "", "identity",
             "One accepted observation per (model, block, arm)."),
        _col("model_key", "str", "registered model slug", "", "identity",
             "Study-internal model identifier."),
        _col("model_id", "str", "HF repository", "", "provenance",
             "Exact model repository."),
        _col("model_revision", "str", "commit hash", "", "provenance",
             "Exact pinned model revision."),
        _col("block_id", "str", "block identifier", "", "identity",
             "The experimental block."),
        _col("arm", "str", _ARM, "", "treatment",
             "The assigned condition of this cell."),
        _col("prompt_hash", "str", _HASH, "", "provenance",
             "SHA-256 of the exact prompt text."),
        _col("pool_index", "int", f"0..{GENERATION_POOL_SIZE - 1}", "",
             "provenance", "Which cached member realised this observation."),
        _col("generation_seed", "int", "0..2^63-1", "", "provenance",
             "The deterministic seed of the realised draw."),
        _col("response", "str", "any text", "", "post_treatment",
             "The accepted response text scored by the verifiers."),
        _col("response_content_hash", "str", _HASH, "", "provenance",
             "SHA-256 of the accepted response."),
        _col("token_count", "int", ">=0", "tokens", "post_treatment",
             "Generated token count."),
        _col("finish_reason", "str", "backend finish reason", "",
             "post_treatment", "Why generation stopped."),
        _col("backend_config_hash", "str", _HASH, "", "provenance",
             "Hash of the producing backend configuration."),
    ],
    "scored": [
        _col("block_id", "str", "block identifier", "", "identity",
             "The experimental block."),
        _col("arm", "str", _ARM, "", "treatment", "The assigned condition."),
        _col("order", "str", "target_first|added_first", "", "design",
             "Block presentation order."),
        _col("wording_target", "int", "0..3", "", "design",
             "Frozen wording index of the target constraint."),
        _col("wording_added", "int", "0..3", "", "design",
             "Frozen wording index of the added constraint."),
        _col("topic_id", "str", "topic identifier", "", "identity",
             "The topic behind this block."),
        _col("s0_count", "int", ">=0", "occurrences", "outcome",
             "S0 target-word count."),
        _col("s1_count", "int", ">=0", "occurrences", "outcome",
             "S1 count (case-sensitive)."),
        _col("s2_count", "int", ">=0", "occurrences", "outcome",
             "S2 substring count."),
        _col("s3_count", "int", ">=0", "occurrences", "outcome",
             "S3 count after preamble/restatement removal."),
        _col("f_s0", "int", _BIN, "", "outcome",
             "Primary target failure under S0."),
        _col("f_s1", "int", _BIN, "", "outcome", "Failure under S1."),
        _col("f_s2", "int", _BIN, "", "outcome", "Failure under S2."),
        _col("f_s3", "int", _BIN, "", "outcome", "Failure under S3."),
        _col("graded", "int", ">=0", "occurrences", "outcome",
             "The graded quantity |count - n| under S0."),
        _col("response_words", "int", ">=0", "words", "post_treatment",
             "Word count of the response."),
        _col("short_flag", "bool", "true/false", "", "post_treatment",
             "Response of three words or fewer."),
        _col("truncated", "bool", "true/false", "", "post_treatment",
             "Generation stopped at the token limit."),
        _col("empty", "bool", "true/false", "", "post_treatment",
             "Response has no non-whitespace character."),
        _col("finish_reason", "str", "backend finish reason", "",
             "post_treatment", "Why generation stopped."),
        _col("token_count", "int", ">=0", "tokens", "post_treatment",
             "Generated token count."),
        _col("non_behavioural", "bool", "true/false", "", "post_treatment",
             "Empty, truncated, or unprocessable (§16 apparatus category)."),
        _col("response_content_hash", "str", _HASH, "", "provenance",
             "Hash linking this row to its raw response."),
        _col("pool_index", "int", f"0..{GENERATION_POOL_SIZE - 1}", "",
             "provenance", "Which cached member realised this observation."),
        _col("uptake", "int|null", "0, 1, or null", "", "post_treatment",
             "Compliance with the added constraint (primary arms only)."),
        _col("joint_compliance", "int|null", "0, 1, or null", "",
             "post_treatment", "Both active constraints pass."),
        _col("failure_category", "str|null", "nine §23 categories or null",
             "", "post_treatment", "Failure taxonomy assignment."),
    ],
}

#: Fields a primary formula may consume (§21): asserted non-post-treatment.
PRIMARY_FORMULA_FIELDS = ("block_id", "arm", "order", "f_s0")

#: Execution-constraining provenance fields → the named §27 check consuming
#: them (codebook executable check 4: a declared field cannot be inert).
CONSTRAINING_CHECKS = {
    "prompt_hash": "check_prompt_hash_in_plan",
    "model_revision": "check_model_revision",
    "backend_config_hash": "check_backend_config",
    "response_content_hash": "check_response_hash",
    "row_sha256": "check_row_bytes",
    "generation_seed": "check_seed_derivation",
}


def assert_primary_fields() -> None:
    roles = {c["name"]: c["causal_role"] for c in CODEBOOKS["scored"]}
    for field in PRIMARY_FORMULA_FIELDS:
        if roles.get(field) == "post_treatment":
            raise ProtocolError(
                f"primary formula field {field!r} is post-treatment (§21)")
        if field not in roles:
            raise ProtocolError(f"primary formula field {field!r} not in "
                                f"codebook")


def assert_constraining_checks_exist() -> None:
    from dci1.evidence import integrity

    for field, check in CONSTRAINING_CHECKS.items():
        if not hasattr(integrity, check):
            raise ProtocolError(
                f"execution-constraining field {field!r} has no named "
                f"consuming check {check!r} (§28 check 4)")


def validate_rows(table: str, rows: list[dict[str, Any]]) -> None:
    """Checks 1–2: column ↔ codebook bijection; types and domains."""
    spec = CODEBOOKS.get(table)
    if spec is None:
        raise ProtocolError(f"no codebook for table {table!r}")
    declared = {c["name"]: c for c in spec}
    for i, row in enumerate(rows):
        extra = set(row) - set(declared)
        missing = set(declared) - set(row)
        if extra or missing:
            raise ProtocolError(
                f"{table} row {i}: columns diverge from codebook "
                f"(extra={sorted(extra)}, missing={sorted(missing)})")
        for name, column in declared.items():
            value = row[name]
            t = column["type"]
            ok = (
                (t == "str" and isinstance(value, str)) or
                (t == "int" and isinstance(value, int)
                 and not isinstance(value, bool)) or
                (t == "bool" and isinstance(value, bool)) or
                (t == "int|null" and (value is None or
                 (isinstance(value, int) and not isinstance(value, bool)))) or
                (t == "str|null" and (value is None or isinstance(value, str)))
            )
            if not ok:
                raise ProtocolError(
                    f"{table} row {i}: {name}={value!r} violates declared "
                    f"type {t}")
        if "arm" in row and table in ("accepted", "scored") and \
                row["arm"] not in ARMS:
            raise ProtocolError(f"{table} row {i}: arm {row['arm']!r} "
                                f"outside domain")
        for f in ("f_s0", "f_s1", "f_s2", "f_s3"):
            if f in row and row[f] not in (0, 1):
                raise ProtocolError(f"{table} row {i}: {f} outside {{0,1}}")
