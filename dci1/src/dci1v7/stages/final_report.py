"""§18 stage 18 and §31: the machine-readable result table.

**A stage in v5 where v4r4 had a tool.** Every number in the released table is
traceable to a signed stage record and a hash, and this module refuses a table
where one is not: §33 check 14 asks that no v4r4 outcome is presented as a v5
observation, and the executable form of that is that every v5 number names the
v5 record it came from.

The table carries, per estimate: the configuration, the **cell**, the claim
level, the family, the identification status, the measurement basis, the
difficulty coordinate, the reference-pool tier, the standard error, the
marginal and simultaneous bounds, the realised half-width, the realised
variance decomposition, the achieved detectable effect and the cell counts.
§26's methodological success criterion is reported **whether or not any L3
statement is emitted**, because it is a different question from the effect
claim and answering only one of them is how v4r4's reports read.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C

__all__ = ["ROW_FIELDS", "assert_row_traceable", "assert_table_traceable",
           "build_final_report"]

#: §31's per-estimate fields.
ROW_FIELDS: tuple[str, ...] = (
    "member", "configuration", "cell", "claim_level", "family",
    "identification_status", "measurement_basis", "difficulty_coordinate",
    "structural_tier_of_reference_pool", "estimate", "standard_error",
    "marginal_lower", "marginal_upper", "simultaneous_lower",
    "simultaneous_upper", "realised_half_width", "variance_decomposition",
    "achieved_detectable_effect", "cell_counts", "stage_record",
    "stage_record_hash",
)


def assert_row_traceable(row: Mapping[str, Any], *, where: str) -> None:
    """Every field present, and the number traced to a v5 stage record."""
    missing = [f for f in ROW_FIELDS if f not in row]
    if missing:
        raise ProtocolError(f"{where}: the result row is missing {missing}")
    if not row.get("stage_record") or not row.get("stage_record_hash"):
        raise ProtocolError(
            f"{where}: §31 requires every number to be traceable to a v5 "
            "stage record and a hash. §33 check 14's executable form is that "
            "a number with no v5 record behind it cannot be released")
    if row.get("measurement_basis") != C.MEASUREMENT_BASIS:
        raise ProtocolError(
            f"{where}: every analysis record carries "
            f"{C.MEASUREMENT_BASIS!r} and its scope sentence")
    if row.get("claim_level") in C.WITHHELD_CLAIM_LEVELS:
        raise ProtocolError(f"{where}: {row['claim_level']} is permanently "
                            "withheld")


def assert_table_traceable(rows: Iterable[Mapping[str, Any]]) -> int:
    rows = list(rows)
    for index, row in enumerate(rows):
        assert_row_traceable(row, where=f"result row {index}")
    return len(rows)


def build_final_report(*, model_key: str, rows: Sequence[Mapping[str, Any]],
                       statements: Sequence[Mapping[str, Any]],
                       success_criterion: Mapping[str, Any],
                       identification_statuses: Sequence[str],
                       admitted_arms: Sequence[str],
                       projection_audit: Sequence[Mapping[str, Any]] = (),
                       raw_coordinate_secondary: Mapping[str, Any] | None
                       = None,
                       stage_record_hashes: Mapping[str, str] | None = None,
                       composed_boundary: Mapping[str, Any] | None = None,
                       ) -> dict[str, Any]:
    """§31's payload, with every invariant this stage can check, checked."""
    n = assert_table_traceable(rows)
    unknown = sorted(set(identification_statuses)
                     - set(C.IDENTIFICATION_STATUSES))
    if unknown:
        raise ProtocolError(
            f"§28.2: unregistered identification status {unknown}")
    l3 = [s for s in statements
          if str(s.get("claim_level", "")).startswith("L3")
          and s.get("emitted")]
    for statement in l3:
        if "REFERENCE_POOL_SAME_FORM" not in \
                statement.get("identification_status", []):
            raise ProtocolError(
                "§28.2: every emitted L3 statement carries "
                "REFERENCE_POOL_SAME_FORM and its fixed sentence")
    return {
        "stage": C.STAGE_FINAL_REPORT,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_FINAL_REPORT],
        "model_key": model_key,
        "measurement_basis": C.MEASUREMENT_BASIS,
        "scope_sentence": C.SCOPE_SENTENCE,
        "admitted_arms": list(admitted_arms),
        "identification_statuses": sorted(set(identification_statuses)),
        "n_result_rows": n,
        "results": [dict(r) for r in rows],
        "statements": [dict(s) for s in statements],
        # §26 is reported whether or not any L3 statement is emitted: it is a
        # different question from the effect claim.
        "methodological_success_criterion": dict(success_criterion),
        # §23: the prospective record of §13.6's projection, reported for
        # every companion and licensing no claim.
        "projection_audit": [dict(p) for p in projection_audit],
        # §23: "the fitted difficulty relation ... the tier-indicator
        # secondary, and the same on the raw coordinate". §15 gives the
        # raw-coordinate replication marginal intervals only and no claim,
        # and the payload says so in `step_12` rather than leaving a reader
        # to assume a simultaneous interval was computed and omitted.
        "raw_coordinate_secondary": dict(raw_coordinate_secondary or {}),
        # v7 §13.14: every member's boundary reading, realised on the
        # confirmatory blocks, beside the Gate-4 projection the freeze bound.
        # A statement's qualification is checkable here against a reading
        # that was on a signed record before the freeze.
        "composed_boundary": dict(composed_boundary or {}),
        "stage_record_hashes": dict(stage_record_hashes or {}),
        "every_number_traces_to_a_v5_stage_record": True,
    }
