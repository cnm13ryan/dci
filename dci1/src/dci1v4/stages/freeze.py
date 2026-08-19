"""Gate 5, GATE_5_FREEZE (§18.1). Implemented and deliberately not executed.

The freeze record carries every field §18.1 names, and ``check_completeness``
refuses to freeze while **any** required field is unknown, **any** registered
open decision (V1 to V9) is unresolved, or **any** blocking pre-freeze check
(Groups A, B and C of ``DCI1_v4r2_prefreeze_checks.md``) is incomplete. An
unknown or unresolved required field fails the freeze; nothing here can be
waived, and no default silently fills a gap.

After the study-wide freeze no scientific rule changes. Any change creates v5;
a model-specific frozen-field change after that model's confirmatory generation
begins creates a new protocol version and leaves the original result unchanged
(§31). An amendment is never used to weaken a criterion so a gate passes.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C

#: §18.1, verbatim. Every one of these must be present and resolved.
FREEZE_FIELDS = (
    "model_revision", "completion_cap", "n_star", "m_star",
    "admitted_references_or_excess_not_identified", "wordings",
    "topic_splits", "prompt_template", "chat_template_hash",
    "verifier_sources", "canonical_verifier_hash", "graded_score_definitions",
    "non_vacuity_predicates", "decoding_settings", "M", "block_count",
    "variance_reestimate", "seed_rules", "cell_plan", "family_declarations",
    "thresholds_and_regions", "precision_preconditions", "claim_ladder",
    "codebook", "producing_commit", "clean_tree_assertion",
    "dependency_digest", "environment_digest", "hardware_record",
    "gate_record_hashes", "gate1_measurement_basis", "analysis_plan",
)

#: §33 / the unresolved-decisions register. All nine must be closed in the
#: signed manifest before the study-wide freeze.
OPEN_DECISIONS = ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9")

#: The pre-freeze checks that block. Group D is report-only and blocks nothing.
BLOCKING_CHECKS = (
    "C1", "C2", "C3", "C4", "C5",                       # blocks Gate 1
    "C6", "C7", "C7b", "C8", "C9", "C10", "C11",        # blocks Gates 2 and 3
    "C12", "C13", "C14", "C15", "C16", "C17",           # blocks the freeze
)
REPORT_ONLY_CHECKS = ("C18", "C19", "C20")

#: §16 of the brief: the four distinct provenances every registered threshold,
#: region, precondition and caliper must carry.
THRESHOLD_PROVENANCE = {
    "delta_r_generic_threshold": {
        "value": C.DELTA_R_GENERIC_THRESHOLD,
        "provenance": "dci-construct-pass2.md §G row 1, 14 August 2026, "
                      "verbatim"},
    "delta_r_pair_specific_threshold": {
        "value": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
        "provenance": "dci-construct-pass2.md §G row 1, 14 August 2026, "
                      "verbatim"},
    "smallest_effect_of_interest": {
        "value": C.SMALLEST_EFFECT_OF_INTEREST,
        "provenance": "carried from DCI-1 v3 §11"},
    "equivalence_region": {
        "value": C.EQUIVALENCE_REGION,
        "provenance": "carried from DCI-1 v3 §11"},
    "precision_preconditions": {
        "value": dict(C.PRECISION_PRECONDITIONS),
        "provenance": "DCI1_preregistration_v4r2.md §16.2"},
    "reference_caliper": {
        "value": C.REFERENCE_CALIPER,
        "provenance": "DCI1_preregistration_v4r2.md §13.2"},
    "reference_newcombe_region": {
        "value": C.REFERENCE_NEWCOMBE_REGION,
        "provenance": "DCI1_preregistration_v4r2.md §13.2"},
    "realised_gap_qualifier": {
        "value": C.REALISED_GAP_QUALIFIER,
        "provenance": "DCI1_preregistration_v4r2.md §13.2"},
}


def assert_threshold_provenance() -> dict[str, Any]:
    """Every registered threshold, region, precondition and caliper carries
    its provenance in the manifest (brief §16, check T13)."""
    missing = [name for name, entry in THRESHOLD_PROVENANCE.items()
               if not entry.get("provenance")]
    if missing:
        raise ProtocolError(f"thresholds without recorded provenance: "
                            f"{missing}")
    return dict(THRESHOLD_PROVENANCE)


def check_completeness(record: Mapping[str, Any], *,
                       decisions: Mapping[str, Any],
                       checks: Mapping[str, str]) -> dict[str, Any]:
    """Refuse to freeze while anything required is unresolved (§18.1)."""
    unresolved_fields = [f for f in FREEZE_FIELDS
                         if record.get(f) in (None, "", [], {})
                         or record.get(f) == "UNKNOWN"]
    open_decisions = [d for d in OPEN_DECISIONS
                      if not decisions.get(d, {}).get("closed")]
    incomplete_checks = [c for c in BLOCKING_CHECKS
                         if checks.get(c) != "COMPLETE"]
    blocked = bool(unresolved_fields or open_decisions or incomplete_checks)
    return {
        "can_freeze": not blocked,
        "unresolved_fields": unresolved_fields,
        "open_decisions": open_decisions,
        "incomplete_blocking_checks": incomplete_checks,
        "report_only_checks": {c: checks.get(c, "NOT_RUN")
                               for c in REPORT_ONLY_CHECKS},
        "rule": ("an unknown or unresolved required field fails the freeze; "
                 "every registered open decision is closed in the signed "
                 "manifest before the study-wide freeze; every blocking "
                 "pre-freeze check is complete"),
    }


def build_freeze_record(**fields: Any) -> dict[str, Any]:
    """Assemble a §18.1 freeze record, filling nothing in silently."""
    record = {name: fields.get(name, "UNKNOWN") for name in FREEZE_FIELDS}
    record["threshold_provenance"] = assert_threshold_provenance()
    record["amendment_note"] = (
        "no scientific rule changes after the study-wide freeze; any change "
        "creates v5, and an amendment is never used to weaken a criterion in "
        "order to make a gate pass (§31)")
    return record


def freeze(record: Mapping[str, Any], *, decisions: Mapping[str, Any],
           checks: Mapping[str, str]) -> dict[str, Any]:
    """Gate 5. Raises unless everything is resolved. **Not executed in this
    implementation task**: the task ends before the freeze."""
    completeness = check_completeness(record, decisions=decisions,
                                      checks=checks)
    if not completeness["can_freeze"]:
        raise ProtocolError(
            f"the freeze is refused: {completeness['unresolved_fields'][:3]} "
            f"unresolved field(s), {completeness['open_decisions']} open "
            f"decision(s), {completeness['incomplete_blocking_checks'][:3]} "
            f"incomplete blocking check(s)")
    return {"outcome": "PASS", "freeze_record": dict(record),
            "completeness": completeness, "identification_statuses": []}
