"""The codebook and its four executable checks (§27, §22).

One row per released variable: name, type, permitted values, units, causal role
and a one-sentence definition. Causal role takes one of identity, treatment,
design, outcome, post-treatment, provenance.

The four checks §27 requires are executable here:

1. every released column appears in the codebook and every codebook row
   appears as a column;
2. every value is in domain and of the declared type;
3. **no post-treatment field appears in a primary formula** — this is the
   §22 prohibition, and it is checked against the declared causal role rather
   than against a hand-maintained list;
4. every field declared to constrain execution is consumed by a named check.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C


def _row(name: str, type_: str, permitted: Any, units: str, role: str,
         definition: str, consumed_by: str | None = None) -> dict[str, Any]:
    if role not in C.CAUSAL_ROLES:
        raise ProtocolError(f"{name}: causal role {role!r} is not registered")
    return {"name": name, "type": type_, "permitted_values": permitted,
            "units": units, "causal_role": role, "definition": definition,
            "consumed_by": consumed_by}


CODEBOOK: tuple[dict[str, Any], ...] = (
    _row("row_id", "string", "cell_id:draw_index", "none", "identity",
         "The unique identity of one cached draw.", "generation.cache"),
    _row("study_id", "string", ["dci1-v4", "dci1-v4-synthetic"], "none",
         "provenance", "The study whose namespace owns this row.",
         "engine.guards"),
    _row("stage", "string", list(C.STAGE_SEQUENCE) + ["greedy"], "none",
         "provenance", "The registered stage that produced the row.",
         "engine.dispatch"),
    _row("artifact_state", "string", list(C.ARTIFACT_STATES), "none",
         "provenance", "The row's position in the artifact lifecycle.",
         "engine.artifacts"),
    _row("model_key", "string", "registered replication key", "none",
         "identity", "Which registered replication produced the row.",
         "generation.cache"),
    _row("model_revision", "string", "40-character commit", "none",
         "provenance", "The exact pinned model revision.",
         "generation.cache"),
    _row("cell_id", "string", "stage:block:cell_type", "none", "identity",
         "The logical prompt cell.", "generation.cache"),
    _row("cell_type", "string", "solo:<slot> or pair:<s1>+<s2>:<order>",
         "none", "treatment",
         "Which registered cell of the design this row belongs to.",
         "design.cells"),
    _row("block_id", "string", "b###-topic", "none", "identity",
         "The experimental unit: one topic with its wording indices.",
         "analysis.observations"),
    _row("order", "string", list(C.ORDERS) + [None], "none", "treatment",
         "Which constituent of the registered slot order is stated first.",
         "design.cells"),
    _row("load", "integer", [1, 2], "constraints", "treatment",
         "The number of constraints in the prompt.", "design.cells"),
    _row("constituents", "array", "slot, kind, severity, position, wording",
         "none", "treatment",
         "Every constraint present in the prompt, with its position.",
         "generation.cache"),
    _row("draw_index", "integer", f"0..{C.M_DRAWS - 1}", "none", "design",
         "Which cached draw of the cell this row is.", "generation.cache"),
    _row("prompt_hash", "string", "sha256", "none", "identity",
         "The content hash of the exact prompt sent.", "generation.cache"),
    _row("seed", "integer", "non-negative", "none", "design",
         "The generation seed derived from experimental identity.",
         "generation.cache"),
    _row("raw_response", "string", "any", "none", "outcome",
         "The complete text the model produced.", "generation.cache"),
    _row("response_content_hash", "string", "sha256", "none", "provenance",
         "The content hash of the raw response.", "generation.cache"),
    _row("scores", "array", "one entry per constraint present", "none",
         "outcome",
         "The compliance vector: verdict, graded score and non-vacuity per "
         "constraint present.", "analysis.observations"),
    _row("accidental", "array", "one entry per constraint absent", "none",
         "post-treatment",
         "Every registered constraint absent from the prompt, still scored, "
         "as an accidental-compliance diagnostic.", "analysis.diagnostics"),
    _row("accidental_s0", "integer", ">= 0 or null", "occurrences",
         "post-treatment",
         "The accidental occurrence count of the exact-count target word "
         "where A is absent.", "analysis.diagnostics"),
    _row("exact_count_alternatives", "object", "s0, s1, s2, s3",
         "occurrences", "post-treatment",
         "The registered alternative exact-count rules, for the robustness "
         "family only.", "analysis.diagnostics"),
    _row("empty", "boolean", [True, False], "none", "post-treatment",
         "Whether the response contains no word.", "analysis.observations"),
    _row("word_count", "integer", ">= 0", "words", "post-treatment",
         "The realised response length; a registered mediator.",
         "analysis.diagnostics"),
    _row("token_count", "integer", ">= 0", "tokens", "post-treatment",
         "Generated token count.", "analysis.diagnostics"),
    _row("truncated", "boolean", [True, False], "none", "post-treatment",
         "Whether the completion cap stopped the response.",
         "analysis.diagnostics"),
    _row("finish_reason", "string", "backend vocabulary", "none",
         "post-treatment", "Why generation stopped.",
         "analysis.diagnostics"),
    _row("verifier_processing_failure", "boolean", [True, False], "none",
         "post-treatment", "Whether any verifier raised on this response.",
         "analysis.observations"),
    _row("verifier_source_hash", "string", "sha256", "none", "provenance",
         "The canonical verifier hash the verdicts were produced under.",
         "engine.binding"),
    _row("backend_version", "string", "any", "none", "provenance",
         "The inference backend version.", "engine.environment"),
    _row("interpreter", "string", "path", "none", "provenance",
         "The interpreter that produced the row.", "engine.environment"),
    _row("dependency_digest", "string", "sha256", "none", "provenance",
         "The lockfile-plus-export dependency digest.",
         "engine.environment"),
    _row("hardware_class", "string", "GPU name", "none", "provenance",
         "The accelerator the row was generated on.", "engine.environment"),
)

CODEBOOK_BY_NAME = {row["name"]: row for row in CODEBOOK}

#: §22: fields that may never enter a primary formula.
POST_TREATMENT = tuple(row["name"] for row in CODEBOOK
                       if row["causal_role"] == "post-treatment")

_TYPE_CHECKS = {
    "string": str, "integer": int, "boolean": bool, "array": list,
    "object": dict, "number": (int, float),
}


def check_columns(columns: Iterable[str]) -> None:
    """Check one: released columns and codebook rows are the same set."""
    columns = set(columns)
    known = set(CODEBOOK_BY_NAME)
    undocumented = sorted(columns - known)
    unreleased = sorted(known - columns)
    if undocumented:
        raise ProtocolError(f"released columns absent from the codebook: "
                            f"{undocumented}")
    if unreleased:
        raise ProtocolError(f"codebook rows absent from the released table: "
                            f"{unreleased}")


def check_values(rows: Sequence[Mapping[str, Any]]) -> int:
    """Check two: every value is in domain and of the declared type."""
    checked = 0
    for row in rows:
        for name, value in row.items():
            spec = CODEBOOK_BY_NAME.get(name)
            if spec is None:
                raise ProtocolError(f"undocumented column {name!r}")
            if value is None:
                continue
            expected = _TYPE_CHECKS.get(spec["type"])
            if expected and not isinstance(value, expected):
                raise ProtocolError(
                    f"{name}: value {value!r} is not {spec['type']}")
            permitted = spec["permitted_values"]
            if isinstance(permitted, list) and value not in permitted:
                raise ProtocolError(
                    f"{name}: value {value!r} outside {permitted}")
            checked += 1
    return checked


def check_no_post_treatment_in_primary(formula_fields: Iterable[str]) -> None:
    """Check three, the §22 prohibition, read from the declared causal role."""
    offending = [f for f in formula_fields
                 if CODEBOOK_BY_NAME.get(f, {}).get("causal_role")
                 == "post-treatment"]
    if offending:
        raise ProtocolError(
            f"post-treatment field(s) {offending} appear in a primary "
            f"formula; §22 forbids them as covariate, filter, stratifier or "
            f"weight")


def check_execution_fields_consumed(known_checks: Iterable[str]) -> None:
    """Check four: every field declared to constrain execution is consumed by
    a named check."""
    known = set(known_checks)
    dangling = sorted({row["name"] for row in CODEBOOK
                       if row["consumed_by"] and row["consumed_by"] not in known})
    if dangling:
        raise ProtocolError(f"codebook fields name a consumer that does not "
                            f"exist: {dangling}")


#: The named checks §27 item four resolves against.
REGISTERED_CONSUMERS = (
    "generation.cache", "engine.guards", "engine.dispatch",
    "engine.artifacts", "engine.binding", "engine.environment",
    "design.cells", "analysis.observations", "analysis.diagnostics",
)


def run_all_checks(columns: Iterable[str], rows: Sequence[Mapping[str, Any]],
                   primary_formula_fields: Iterable[str]) -> dict[str, Any]:
    check_columns(columns)
    values = check_values(rows)
    check_no_post_treatment_in_primary(primary_formula_fields)
    check_execution_fields_consumed(REGISTERED_CONSUMERS)
    return {"codebook_rows": len(CODEBOOK), "values_checked": values,
            "post_treatment_fields": list(POST_TREATMENT)}
