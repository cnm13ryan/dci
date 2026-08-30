"""Who writes each field a later pilot stage reads, and the audit that they
match --- statically, and against the payloads a walk produced.

The defect this exists for is the reader with no producer: a stage that
reads ``record["x"]`` where nothing upstream writes ``x``, invisible until
the path first executes. Every field one stage reads from another is listed
with its producer; ``audit_contracts`` checks that every reader follows its
producer, that every declared field has exactly one producer, and --- given
payloads --- that every required field is actually present.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v8dev.run import stages as S

__all__ = ["Field", "CONTRACT", "audit_contracts", "assert_contracts_clean",
           "matrix_rows", "matrix_markdown"]

R, Q, G0 = S.STAGE_REGISTERED, S.STAGE_QUALIFIED, S.STAGE_GATE0
RG, SP, G1 = S.STAGE_REGIME, S.STAGE_SECOND_PASS, S.STAGE_GATE1
G2, G3, RP = S.STAGE_GATE2, S.STAGE_GATE3, S.STAGE_REPORT


@dataclass(frozen=True)
class Field:
    artifact: str
    field: str
    producer: str
    readers: tuple[str, ...]
    required: bool

    def as_dict(self) -> dict[str, Any]:
        return {"artifact": self.artifact, "field": self.field,
                "producer": self.producer, "readers": list(self.readers),
                "required": self.required}


def _f(stage: str, field: str, readers: Sequence[str], *,
       required: bool = True) -> Field:
    return Field(artifact=stage, field=field, producer=stage,
                 readers=tuple(readers), required=required)


CONTRACT: tuple[Field, ...] = (
    _f(R, "manifest_hash", (RP,)),
    _f(R, "instrument", (G1,)),
    _f(R, "wording_policy", (G1, RP)),
    _f(R, "frame_conditioning", (), required=True),
    _f(R, "criteria", (RP,)),
    _f(Q, "checks", (), required=True),
    _f(Q, "topic_split_identity", (), required=True),
    _f(G0, "acceptance", (), required=True),
    _f(G0, "rows", (RP,)),
    _f(RG, "selected_cap", (SP, G2)),
    _f(RG, "prescreen_table", (SP,)),
    _f(RG, "difficulty_table", (G2,)),
    _f(RG, "frame_reliability", (G1,)),
    _f(RG, "frame_conditioning", (), required=True),
    _f(RG, "row_accounting", (RP,)),
    _f(RG, "chance_basis", (RP,)),
    _f(RG, "n_rungs_measured", (RP,)),
    _f(RG, "cap_selection", (RP,)),
    _f(RG, "screen", (), required=True),
    _f(SP, "forwarded_set", (G2,)),
    _f(SP, "retention", (G2, RP)),
    _f(SP, "frame_reliability", (G1,)),
    _f(SP, "frame_conditioning", (), required=True),
    _f(SP, "topic_isolation", (RP,)),
    _f(SP, "row_accounting", (RP,)),
    _f(SP, "n_batches", (RP,)),
    _f(SP, "resolved_at_max", (RP,)),
    _f(SP, "cost_generations", (RP,)),
    _f(G1, "frame_reliability", (RP,)),
    _f(G1, "ladders_by_frame_screen", (RP,)),
    _f(G1, "wording_dependence_screen", (RP,)),
    _f(G1, "frame_comparison_screen", (), required=True),
    _f(G1, "stability_screen_vs_second_pass", (RP,), required=False),
    _f(G1, "verifier_hash", (), required=True),
    _f(G1, "wording_hash", (), required=True),
    # Gate 2 is per frame (Approach A): every operating point, iota_A,
    # §13.11 table and extension reach lives under by_frame[f]; the only
    # frame-pooled block is descriptive and has no reader.
    _f(G2, "frame_conditioning", (G3, RP)),
    _f(G2, "frames", (G3, RP)),
    _f(G2, "supported_frames", (G3, RP)),
    _f(G2, "unsupported_frames", (G3, RP)),
    _f(G2, "by_frame", (G3, RP)),
    _f(G2, "descriptive_pooled", (), required=True),
    _f(G2, "reserve_instances_declared_on_the_grids", (), required=True),
    _f(G2, "grids", (RP,)),
    _f(G2, "calibration_topic_ids", (RP,)),
    _f(G2, "calibration_population", (RP,)),
    _f(G2, "chance_basis", (), required=True),
    _f(G2, "extension", (RP,)),
    _f(G2, "frame_comparison_pooled", (G3,)),
    _f(G2, "wording_by_frame", (), required=True),
    _f(G2, "ladders_by_frame_pooled", (RP,)),
    _f(G2, "wording_dependence_pooled", (RP,)),
    _f(G2, "split_stability_by_frame", (RP,)),
    _f(G2, "row_accounting", (RP,)),
    _f(G3, "frames", (), required=True),
    _f(G3, "supported_frames", (), required=True),
    _f(G3, "by_frame", (RP,)),
    _f(G3, "frame_states", (RP,)),
    _f(G3, "cross_frame", (), required=True),
    _f(G3, "estimands", (RP,)),
    _f(RP, "criteria", (), required=True),
    _f(RP, "pilot_status", (), required=True),
    _f(RP, "frames_meeting_all_decided_criteria", (), required=True),
)


def audit_contracts(payloads: Mapping[str, Mapping[str, Any]] | None = None
                    ) -> dict[str, Any]:
    order = {s: i for i, s in enumerate(S.STAGE_SEQUENCE)}
    defects: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for f in CONTRACT:
        if f.producer not in order:
            defects.append({"kind": "UNKNOWN_PRODUCER", "field": f.field,
                            "producer": f.producer})
            continue
        key = (f.artifact, f.field)
        if key in seen:
            defects.append({"kind": "DUPLICATE_PRODUCER", "field": f.field,
                            "artifact": f.artifact})
        seen.add(key)
        for reader in f.readers:
            if reader not in order:
                defects.append({"kind": "UNKNOWN_READER", "field": f.field,
                                "reader": reader})
            elif order[reader] <= order[f.producer]:
                defects.append({"kind": "READER_BEFORE_PRODUCER",
                                "field": f.field, "producer": f.producer,
                                "reader": reader})
    checked = 0
    if payloads is not None:
        for f in CONTRACT:
            payload = payloads.get(f.artifact)
            if payload is None:
                continue
            checked += 1
            if f.required and f.field not in payload:
                defects.append({"kind": "REQUIRED_FIELD_MISSING",
                                "artifact": f.artifact, "field": f.field})
    return {"n_fields": len(CONTRACT), "defects": defects,
            "clean": not defects,
            "n_checked_against_payloads": checked}


def assert_contracts_clean(payloads: Mapping[str, Mapping[str, Any]] | None
                           = None) -> None:
    result = audit_contracts(payloads)
    if not result["clean"]:
        raise AssertionError(f"contract defects: {result['defects']}")


def matrix_rows(payloads: Mapping[str, Mapping[str, Any]] | None = None
                ) -> list[dict[str, Any]]:
    rows = []
    for f in CONTRACT:
        row = f.as_dict()
        if payloads is not None and f.artifact in payloads:
            row["exercised"] = ("PRESENT" if f.field in payloads[f.artifact]
                                else "MISSING")
        rows.append(row)
    return rows


def matrix_markdown(payloads: Mapping[str, Mapping[str, Any]] | None = None
                    ) -> str:
    lines = ["| artifact | field | readers | required | exercised |",
             "|---|---|---|---|---|"]
    for row in matrix_rows(payloads):
        lines.append(f"| {row['artifact']} | `{row['field']}` | "
                     f"{', '.join(row['readers']) or '—'} | "
                     f"{'yes' if row['required'] else 'no'} | "
                     f"{row.get('exercised', '—')} |")
    return "\n".join(lines) + "\n"
