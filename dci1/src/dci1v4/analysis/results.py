"""The machine-readable result table (§30).

Every reported figure must be reproducible from this table without
regenerating a response, and every number in it from accepted raw responses in
the recorded environment. **No number is transcribed by hand**: the table is
the only source a report reads, and ``assert_table_complete`` refuses a row
missing any registered column.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.analysis.bootstrap import FamilyResult, MemberResult
from dci1v4.errors import ProtocolError

#: §30, the registered column set. A row missing any of these is refused.
RESULT_COLUMNS = (
    "model_key", "configuration", "member", "family", "claim_level",
    "identification_status", "measurement_basis", "estimate",
    "standard_error", "marginal_lower", "marginal_upper",
    "simultaneous_lower", "simultaneous_upper", "realised_half_width",
    "precision_precondition", "precision_met", "realised_variance_topic",
    "realised_variance_draw", "realised_phi", "achieved_detectable_effect",
    "cells_per_block", "blocks", "draws_per_cell", "markers", "scope_sentence",
)


def result_rows(model_key: str, families: Mapping[str, FamilyResult], *,
                claim_levels: Mapping[str, str],
                identification_status: Sequence[str],
                measurement_basis: str,
                precision_preconditions: Mapping[str, float],
                variance: Mapping[str, float],
                detectable: Mapping[str, float],
                cells_per_block: int, blocks: int, draws_per_cell: int,
                scope_sentence: str | None,
                markers: Mapping[str, Sequence[str]] | None = None
                ) -> list[dict[str, Any]]:
    """One row per (configuration, family member)."""
    markers = markers or {}
    rows: list[dict[str, Any]] = []
    for family_name, family in sorted(families.items()):
        for name, member in sorted(family.members.items()):
            precondition = precision_preconditions.get(name)
            rows.append({
                "model_key": model_key,
                "configuration": family.configuration,
                "member": name,
                "family": family_name,
                "claim_level": claim_levels.get(name, "none"),
                "identification_status": list(identification_status),
                "measurement_basis": measurement_basis,
                "estimate": member.estimate,
                "standard_error": member.standard_error,
                "marginal_lower": member.marginal_lower,
                "marginal_upper": member.marginal_upper,
                "simultaneous_lower": member.simultaneous_lower,
                "simultaneous_upper": member.simultaneous_upper,
                "realised_half_width": member.half_width,
                "precision_precondition": precondition,
                "precision_met": (None if precondition is None
                                  else member.half_width <= precondition),
                "realised_variance_topic": variance.get("sigma2_topic"),
                "realised_variance_draw": variance.get("sigma2_draw"),
                "realised_phi": variance.get("phi"),
                "achieved_detectable_effect": detectable.get(name),
                "cells_per_block": cells_per_block,
                "blocks": blocks,
                "draws_per_cell": draws_per_cell,
                "markers": list(markers.get(name, ())),
                "scope_sentence": scope_sentence,
            })
    return rows


def assert_table_complete(rows: Iterable[Mapping[str, Any]]) -> int:
    """§30: every row carries every registered column."""
    count = 0
    for row in rows:
        missing = [c for c in RESULT_COLUMNS if c not in row]
        if missing:
            raise ProtocolError(
                f"result row {row.get('member')!r} is missing {missing}")
        if row.get("configuration") in (None, ""):
            raise ProtocolError(
                f"result row {row.get('member')!r} quotes a scalar without "
                f"its configuration")
        count += 1
    return count


def assert_no_manual_numbers(report_text: str,
                             rows: Sequence[Mapping[str, Any]]) -> None:
    """§30: every number in a report must come from the table.

    The check is deliberately crude and deliberately strict: any decimal
    literal in the narrative must appear, rounded to its own precision, among
    the table's numeric values or among the registered constants a report may
    quote. A number that appears nowhere in the table was transcribed by hand.
    """
    import re

    from dci1v4.protocol import constants as C

    allowed: set[str] = set()
    for row in rows:
        for value in row.values():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                for places in range(0, 7):
                    allowed.add(f"{float(value):.{places}f}")
    for value in (C.DELTA_R_GENERIC_THRESHOLD,
                  C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
                  C.SMALLEST_EFFECT_OF_INTEREST, C.EQUIVALENCE_REGION,
                  C.REFERENCE_CALIPER, C.REALISED_GAP_QUALIFIER,
                  C.TRUNCATION_BOUND_THRESHOLD, C.F6_VACUITY_GATE,
                  *C.PRECISION_PRECONDITIONS.values()):
        for places in range(0, 7):
            allowed.add(f"{float(value):.{places}f}")
    for literal in re.findall(r"(?<![\w.])-?\d+\.\d+", report_text):
        places = len(literal.split(".")[1])
        if f"{float(literal):.{places}f}" not in allowed:
            raise ProtocolError(
                f"the report quotes {literal}, which is not reproducible from "
                f"the result table; no number is transcribed by hand (§30)")
