"""Who writes each field, who reads it, and the audit that they match.

This repository has been bitten more than once by a **reader with no
producer**: a downstream function that reads ``record["x"]`` where nothing
upstream ever writes ``x``. The defect is invisible until the path first
executes, which for a confirmatory study is after the expensive part. v4r4's
first real execution found several, and its L4 emitter was found after the
mask was sealed --- too late to repair under §20.

So the contract is written down and audited **statically**, before anything
runs, and again **at runtime** against the real payloads the synthetic
lifecycle produces.

Each entry is one field of one artifact: the stage that produces it, the
stages that read it, whether it is required, and the test that covers it.
``audit_contracts`` then establishes four things:

1. every reader names a stage that exists and comes **after** the producer;
2. every declared field has exactly one producer;
3. no required field is read by a stage the producer cannot precede;
4. given real payloads, every required field is actually present.

A required field with no producer is a blocking implementation defect and is
reported as one, not deferred to first execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C

__all__ = ["Field", "CONTRACT", "audit_contracts", "matrix_rows",
           "matrix_markdown"]

_S = C
R, Q = _S.STAGE_REGISTERED, _S.STAGE_QUALIFIED
G0, RG, G1 = _S.STAGE_GATE0, _S.STAGE_REGIME, _S.STAGE_GATE1
G2, G25 = _S.STAGE_GATE2, _S.STAGE_GATE2_5
G3A, G3B, G3C = _S.STAGE_GATE3A, _S.STAGE_GATE3B, _S.STAGE_GATE3C
G4, PF, G5 = _S.STAGE_GATE4, _S.STAGE_PREFREEZE_AUDIT, _S.STAGE_GATE5
CONF = _S.STAGE_CONFIRMATORY
MA, UN, UA = (_S.STAGE_MASKED_ANALYSIS, _S.STAGE_UNMASKING,
              _S.STAGE_UNMASKED_ANALYSIS)
FR = _S.STAGE_FINAL_REPORT


@dataclass(frozen=True)
class Field:
    artifact: str            # the producing stage's record
    field: str
    producer: str
    readers: tuple[str, ...]
    required: bool
    test: str

    def as_dict(self) -> dict[str, Any]:
        return {"artifact": self.artifact, "field": self.field,
                "producer": self.producer, "readers": list(self.readers),
                "stage_introduced": self.producer,
                "required": self.required, "test": self.test}


def _f(stage: str, field: str, readers: Sequence[str], *, required: bool = True,
       test: str = "tests_v5/test_run_contracts.py") -> Field:
    return Field(artifact=stage, field=field, producer=stage,
                 readers=tuple(readers), required=required, test=test)


#: Every field one v5 stage writes that another v5 stage reads. Fields a stage
#: writes purely for the record --- provenance, counts, the statements a
#: reader needs --- are not listed: this registry is about *contracts*, and a
#: field nobody reads cannot have a missing producer.
CONTRACT: tuple[Field, ...] = (
    # -------------------------------------------------- PROTOCOL_REGISTERED
    _f(R, "manifest_hash", (Q, G5, PF)),
    _f(R, "protocol_hash", (G5, PF)),
    _f(R, "reference_design_spec_hash", (G5, PF)),
    _f(R, "protocol_version", (G5,)),
    _f(R, "decisions", (PF,)),
    _f(R, "open_items", (PF,)),
    _f(R, "topic_hashes", (G5, PF)),
    _f(R, "calibration_a_hash", (G3A, G5)),
    _f(R, "calibration_b_hash", (G3A, G5)),
    _f(R, "split_hash", (G5,)),
    _f(R, "models", (G5, PF)),
    _f(R, "measurement_basis", (G1, G5, UA)),

    # ------------------------------------------------------------ QUALIFIED
    _f(Q, "canonical_verifier_hash", (G1,)),
    _f(Q, "instrument_population", (G1,)),
    _f(Q, "checks", (PF,)),
    _f(Q, "topic_split_identity", (G2, G3A)),

    # ------------------------------------------------------ GATE_0_APPARATUS
    _f(G0, "acceptance", (PF,)),
    _f(G0, "admitted_arms_exercised", (), required=False),

    # ---------------------------------------------------------- REGIME_SCREEN
    _f(RG, "selected_cap", (G2, G4, CONF, G5)),
    _f(RG, "carried_set", (G2, G25, G3A, G5)),
    _f(RG, "n_carried", (G1, PF)),
    _f(RG, "difficulty_table", (G25, G3A)),
    _f(RG, "vocabulary_frozen", (PF, G5)),
    _f(RG, "coverage", (G3C, G5)),
    _f(RG, "calibration_priority", (G3A,)),
    _f(RG, "iota_a_prescreen", (), required=False),

    # ----------------------------------------------------- GATE_1_MEASUREMENT
    _f(G1, "canonical_verifier_hash", (CONF, PF, G5)),
    _f(G1, "wording_hash", (PF, G5)),
    _f(G1, "measurement_basis", (UA, FR, G5)),
    _f(G1, "scope_sentence", (UA, FR)),
    _f(G1, "instrument_population", (G5,)),

    # ----------------------------------------------- GATE_2_FOCAL_CALIBRATION
    _f(G2, "n_star", (G25, G3B, G4, G5, CONF)),
    _f(G2, "m_star", (G25, G3A, G3B, G4, G5, CONF)),
    _f(G2, "iota_a", (G3B, G5)),
    _f(G2, "solo_compliance_a", (G3B, G5)),
    _f(G2, "chance_curves", (G5,)),
    _f(G2, "solo_curves", (G5,)),
    _f(G2, "construct_strength", (G5, FR)),
    _f(G2, "identification_statuses", (G3C, G5, UA)),
    _f(G2, "calibration_binding", (G3A, G5)),

    # ------------------------------------- GATE_2_5_CANDIDATE_QUALIFICATION
    _f(G25, "m_star", (G3A,)),
    _f(G25, "qualification", (G5,)),
    _f(G25, "qualified_pool", (G3A, G5)),
    _f(G25, "qualified_families", (G3C, G5)),
    _f(G25, "earliest_failing_components", (G5,)),
    _f(G25, "interaction", (G3B, G5)),

    # ------------------------------------- GATE_3A_REFERENCE_CALIBRATION
    _f(G3A, "m_star", (G3B, G4)),
    _f(G3A, "pooled_table", (G3B,)),
    _f(G3A, "stability", (G3B, G5, PF)),
    _f(G3A, "split_tables", (G5, PF)),
    _f(G3A, "calibration_b_population", (G5,)),

    # ---------------------------------------- GATE_3B_REFERENCE_SELECTION
    _f(G3B, "m_star", (G3C,)),
    _f(G3B, "selection", (G3C, G4, G5, PF, CONF)),
    _f(G3B, "iota_a", (G5,)),

    # ------------------------------------------- GATE_3C_IDENTIFICATION
    _f(G3C, "admitted_arms", (G4, G5, CONF, UA, FR, PF)),
    _f(G3C, "derived_cell_count", (G4, G5, CONF, PF)),
    _f(G3C, "slots", (G4, CONF)),
    _f(G3C, "identification_statuses", (G4, G5, UA, FR, PF)),
    _f(G3C, "support", (G5, FR, PF)),
    _f(G3C, "m_star", (G4, G5)),

    # ------------------------------------------- GATE_4_COMPOSED_HEADROOM
    _f(G4, "headroom_table", (G5, PF)),
    _f(G4, "admitted_arms", (G5, PF)),
    _f(G4, "failures", (G5, PF)),
    _f(G4, "expected_rows", (PF,)),
    _f(G4, "rows", (PF,)),
    _f(G4, "n_cell_types", (PF,)),
    # §33 check 8 requires the record to *declare* §13.14's refusal, not
    # merely to lack a field that names a substitution.
    _f(G4, "declared_refusals", (PF, FR)),

    # -------------------------------------------------------- PREFREEZE_AUDIT
    _f(PF, "can_freeze", (G5,)),
    _f(PF, "artifact_checks", (G5,)),
    _f(PF, "checklist", (G5, FR)),

    # ---------------------------------------------------------- GATE_5_FREEZE
    _f(G5, "freeze", (CONF, MA, UN, UA, FR)),
    _f(G5, "freeze_hash", (CONF, MA, UA, FR)),
    _f(G5, "blocks", (CONF,)),
    _f(G5, "cells_per_block", (CONF,)),
    _f(G5, "M", (CONF, MA, UA)),
    _f(G5, "slot_map", (CONF,)),
    _f(G5, "admitted_arms", (CONF, UA, FR)),
    _f(G5, "identification_statuses", (UA, FR)),
    _f(G5, "selected_cap", (CONF,)),

    # ------------------------------------------------ CONFIRMATORY_GENERATION
    _f(CONF, "rows_path", (MA,)),
    _f(CONF, "n_rows", (MA, UA, FR)),
    _f(CONF, "completeness", (MA, FR), required=True),
    _f(CONF, "freeze_hash", (MA, UA)),

    # ---------------------------------------------------------- MASKED_ANALYSIS
    _f(MA, "mask_namespace", (UN,)),
    _f(MA, "masked_result_hash", (UN, UA)),
    _f(MA, "analysis_code_hash", (UN, UA)),
    _f(MA, "sealed", (UN,)),

    # ------------------------------------------------------------- UNMASKING
    _f(UN, "unmasked", (UA,)),
    _f(UN, "mask_key_hash", (UA,)),
    _f(UN, "unmask_event", (UA, FR)),

    # ------------------------------------------------------ UNMASKED_ANALYSIS
    _f(UA, "statements", (FR,)),
    _f(UA, "identification_statuses", (FR,)),
    _f(UA, "success_criterion", (FR,)),
    _f(UA, "estimands", (FR,)),
    _f(UA, "projection_audit", (FR,), required=False),
)


def audit_contracts(payloads: Mapping[str, Mapping[str, Any]] | None = None
                    ) -> dict[str, Any]:
    """The static audit, plus the runtime one when payloads are supplied."""
    order = {stage: i for i, stage in enumerate(C.STAGE_SEQUENCE)}
    defects: list[dict[str, Any]] = []
    producers: dict[tuple[str, str], str] = {}

    for entry in CONTRACT:
        key = (entry.artifact, entry.field)
        if key in producers:
            defects.append({"kind": "DUPLICATE_PRODUCER",
                            "artifact": entry.artifact, "field": entry.field})
        producers[key] = entry.producer
        if entry.producer not in order:
            defects.append({"kind": "UNKNOWN_PRODUCER",
                            "artifact": entry.artifact, "field": entry.field,
                            "producer": entry.producer})
            continue
        for reader in entry.readers:
            if reader not in order:
                defects.append({"kind": "UNKNOWN_READER",
                                "artifact": entry.artifact,
                                "field": entry.field, "reader": reader})
            elif order[reader] <= order[entry.producer]:
                defects.append({"kind": "READER_PRECEDES_PRODUCER",
                                "artifact": entry.artifact,
                                "field": entry.field, "reader": reader,
                                "producer": entry.producer})

    checked = 0
    if payloads is not None:
        for entry in CONTRACT:
            payload = payloads.get(entry.artifact)
            if payload is None:
                continue
            checked += 1
            if entry.required and entry.field not in payload:
                defects.append({"kind": "REQUIRED_FIELD_NOT_PRODUCED",
                                "artifact": entry.artifact,
                                "field": entry.field,
                                "producer": entry.producer,
                                "readers": list(entry.readers)})
    return {
        "n_fields": len(CONTRACT),
        "n_artifacts": len({e.artifact for e in CONTRACT}),
        "n_checked_against_payloads": checked,
        "defects": defects,
        "n_defects": len(defects),
        "clean": not defects,
    }


def assert_contracts_clean(payloads: Mapping[str, Mapping[str, Any]] | None
                           = None) -> dict[str, Any]:
    result = audit_contracts(payloads)
    if result["defects"]:
        raise ProtocolError(
            f"the producer/consumer contract has {result['n_defects']} "
            f"defect(s): {result['defects'][:5]}. A required field with no "
            "producer is a blocking implementation defect")
    return result


def matrix_rows(payloads: Mapping[str, Mapping[str, Any]] | None = None
                ) -> list[dict[str, Any]]:
    """The audit matrix, one row per (artifact, field)."""
    rows = []
    for entry in CONTRACT:
        row = entry.as_dict()
        if payloads is not None and entry.artifact in payloads:
            present = entry.field in payloads[entry.artifact]
            row["status"] = ("PRODUCED" if present
                             else "MISSING" if entry.required
                             else "ABSENT_OPTIONAL")
            row["exercised"] = present
        else:
            row["status"] = "NOT_EXERCISED"
            row["exercised"] = False
        rows.append(row)
    return rows


def matrix_markdown(payloads: Mapping[str, Mapping[str, Any]] | None = None
                    ) -> str:
    """The same matrix as a Markdown table, for the status report."""
    head = ("| artifact | field | producer | reader(s) | stage introduced | "
            "required | test | exercised | status |\n"
            "|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for row in matrix_rows(payloads):
        lines.append(
            f"| `{row['artifact']}` | `{row['field']}` | "
            f"`{row['producer']}` | "
            f"{', '.join('`' + r + '`' for r in row['readers']) or '—'} | "
            f"`{row['stage_introduced']}` | "
            f"{'yes' if row['required'] else 'no'} | "
            f"`{row['test']}` | "
            f"{'yes' if row.get('exercised') else 'no'} | "
            f"{row['status']} |")
    return "\n".join(lines)
