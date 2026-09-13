"""Gates 2, 3 and 4: the deterministic selection and viability rules.

**Gate 2, the operating regime (§12.3, §12.4).** n* and m* are chosen from the
solo-compliance curves by a rule with no free parameter. The diagnoses are
distinguished exactly as §12.3 requires: ``GRID_RESOLUTION_INSUFFICIENT`` when
two adjacent registered severities lie on opposite sides of a whole band, and
``TARGET_RANGE_EXHAUSTED`` / ``FOCAL_RANGE_EXHAUSTED`` when the curve reaches a
grid boundary while staying on one side of it. Every diagnosis records the
complete curve and makes a claim only about the registered grid.

**Gate 3, references (§13.2, T-8, T-9).** The reference is matched to **A** on
solo **compliance**, which inverts v3 in both respects, and composed uptake is
not a criterion at any point: selecting a control on the outcome it is meant to
counterfactual is circular. Fewer than three admitted families is **not
terminal** — it sets ``EXCESS_NOT_IDENTIFIED`` and routes the model to the
reduced design of §8.6 (T-11).

**Gate 4, composed headroom (§13.6, T-9).** Each registered cell type is
evaluated independently against [0.05, 0.95] for each of its two constraints.
The gate ranks nothing, selects nothing, and computes no contrast between
cells; there is deliberately no comparison of one cell against another here.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.analysis.intervals import (
    clustered_paired_se,
    intersects,
    newcombe_paired,
    paired_table,
)
from dci1v4.errors import ProtocolError, TerminalStatus
from dci1v4.protocol import constants as C
from dci1v4.protocol.wordings import length_caliper_ok
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    Constraint,
    TARGET_GRID,
)
from dci1v4.verifiers.witnesses import verify_pair

#: Registered tie-breaks fire on an *exact* tie (§12.3, §13.2). Binary
#: floating point does not represent 0.70 or 0.05 exactly, so two
#: mathematically equal distances can compare unequal in the twelfth decimal
#: and silently decide a selection the protocol says a tie-break decides.
#: Every selection key is rounded here before comparison, at a precision far
#: below any rate the design can measure.
TIE_PRECISION = 12


def tie_key(value: float) -> float:
    return round(value, TIE_PRECISION)


# ------------------------------------------------------------------- Gate 2
def _diagnose_band(curve: Mapping[int, float], grid: Sequence[int],
                   band: tuple[float, float], *, exhausted_status: str,
                   quantity: str) -> None:
    """Raise the registered terminal status when no severity is eligible."""
    low, high = band
    ordered = [(s, curve[s]) for s in grid if s in curve]
    if not ordered:
        raise ProtocolError(f"no {quantity} curve was measured")
    for (s1, v1), (s2, v2) in zip(ordered, ordered[1:]):
        if (v1 > high and v2 < low) or (v1 < low and v2 > high):
            raise TerminalStatus("GRID_RESOLUTION_INSUFFICIENT", {
                "status": "GRID_RESOLUTION_INSUFFICIENT",
                "gate": C.STAGE_GATE2, "criterion": f"{quantity} band",
                "threshold": list(band),
                "observed": {"adjacent": [s1, s2], "values": [v1, v2]},
                "curves": {quantity: dict(curve)}, "artifact_hashes": {},
                "strongest_permissible_statement":
                    f"adjacent registered {quantity} severities {s1} and {s2} "
                    f"lie on opposite sides of the whole band {band}; the "
                    f"statement is about the registered grid and about "
                    f"nothing else",
                "estimands_unanswerable": "all"})
    side = ("above" if all(v > high for _, v in ordered)
            else "below" if all(v < low for _, v in ordered) else "mixed")
    raise TerminalStatus(exhausted_status, {
        "status": exhausted_status, "gate": C.STAGE_GATE2,
        "criterion": f"{quantity} solo compliance inside {band}",
        "threshold": list(band),
        "observed": {"side": side, "curve": dict(curve)},
        "curves": {quantity: dict(curve)}, "artifact_hashes": {},
        "strongest_permissible_statement":
            f"the {quantity} curve reaches a registered grid boundary while "
            f"staying {side} the band; the statement is about the registered "
            f"grid and never about the model or the hypothesis",
        "estimands_unanswerable": "all"})


def select_severity(curve: Mapping[int, float], grid: Sequence[int],
                    band: tuple[float, float], aim: float, *,
                    exhausted_status: str, quantity: str) -> dict[str, Any]:
    """§12.3: minimise the distance from ``aim`` among eligible severities;
    the smaller severity breaks an exact tie."""
    low, high = band
    eligible = [(s, curve[s]) for s in grid
                if s in curve and low <= curve[s] <= high]
    if not eligible:
        _diagnose_band(curve, grid, band, exhausted_status=exhausted_status,
                       quantity=quantity)
    best = min(eligible,
               key=lambda item: (tie_key(abs(item[1] - aim)), item[0]))
    return {"selected": best[0], "solo_compliance": best[1],
            "band": list(band), "aim": aim,
            "eligible": [{"severity": s, "solo_compliance": v}
                         for s, v in eligible],
            "curve": {int(k): v for k, v in sorted(curve.items())},
            "tie_break": "the smaller severity breaks an exact tie"}


def gate2_payload(*, a_curve: Mapping[int, float],
                  b_curve: Mapping[int, float],
                  b_solo_vacuity: float,
                  graded_distribution: Mapping[str, float],
                  truncation_by_cell: Mapping[str, float] | None = None
                  ) -> dict[str, Any]:
    """Gate 2: n*, m* and the §12.4 adequacy check."""
    n_star = select_severity(a_curve, TARGET_GRID, C.TARGET_BAND, C.TARGET_AIM,
                             exhausted_status="TARGET_RANGE_EXHAUSTED",
                             quantity="A")
    m_star = select_severity(b_curve, FOCAL_GRID, C.FOCAL_BAND, C.FOCAL_AIM,
                             exhausted_status="FOCAL_RANGE_EXHAUSTED",
                             quantity="B")

    failures: list[str] = []
    if b_solo_vacuity > C.REGIME_VACUITY_MAX:
        failures.append(f"B solo vacuity {b_solo_vacuity:.3f} exceeds "
                        f"{C.REGIME_VACUITY_MAX}")
    for name, value in sorted(graded_distribution.items()):
        if value > C.GRADED_DEGENERACY_HIGH or value < C.GRADED_DEGENERACY_LOW:
            failures.append(f"the graded distribution of {name} is degenerate "
                            f"at {value:.4f}")
    if failures:
        raise TerminalStatus("REGIME_NOT_FOUND", {
            "status": "REGIME_NOT_FOUND", "gate": C.STAGE_GATE2,
            "criterion": "§12.4 regime adequacy",
            "threshold": {"b_solo_vacuity_max": C.REGIME_VACUITY_MAX,
                          "graded_bounds": [C.GRADED_DEGENERACY_LOW,
                                            C.GRADED_DEGENERACY_HIGH]},
            "observed": {"b_solo_vacuity": b_solo_vacuity,
                         "graded": dict(graded_distribution),
                         "failures": failures},
            "curves": {"A": dict(a_curve), "B": dict(b_curve)},
            "artifact_hashes": {},
            "strongest_permissible_statement":
                "the registered grid does not place both outcome constraints "
                "in an adequate regime; this is a statement about the "
                "registered grid and never about the model or the hypothesis",
            "estimands_unanswerable": "all"})

    return {"outcome": "PASS", "n_star": n_star, "m_star": m_star,
            "regime_adequacy": {"b_solo_vacuity": b_solo_vacuity,
                                "graded_distribution":
                                    dict(graded_distribution),
                                "passed": True},
            "truncation_by_cell": dict(truncation_by_cell or {}),
            "identification_statuses": []}


# ------------------------------------------------------------------- Gate 3
def admit_family(family: str, *, n_star: int,
                 calibration: Mapping[int, Sequence[float]],
                 a_calibration: Sequence[float],
                 prescreen: Mapping[int, float], a_prescreen: float,
                 vacuity: Mapping[int, float],
                 draw_level: Mapping[int, tuple[Sequence[int], Sequence[int]]]
                 ) -> dict[str, Any]:
    """§13.2 within one family: the admissible severity, or None with reasons.

    ``calibration`` maps a severity to its per-topic solo-compliance cell means
    on the 96 calibration topics; ``draw_level`` maps a severity to the paired
    draw-level 0/1 sequences (reference, A) the Newcombe interval reads.
    """
    a_mean = sum(a_calibration) / len(a_calibration)
    candidates: list[dict[str, Any]] = []
    for q in REFERENCE_LADDERS[family]:
        if q not in calibration:
            continue
        values = calibration[q]
        mean = sum(values) / len(values)
        difference = mean - a_mean
        reasons: list[str] = []

        if abs(difference) > C.REFERENCE_CALIPER:
            reasons.append(f"solo distance {abs(difference):.4f} exceeds the "
                           f"caliper {C.REFERENCE_CALIPER}")
        ref_draws, a_draws = draw_level.get(q, ((), ()))
        interval = None
        if ref_draws and a_draws:
            interval = newcombe_paired(*paired_table(ref_draws, a_draws))
            if not intersects(interval, C.REFERENCE_NEWCOMBE_REGION):
                reasons.append(
                    f"the 95% Newcombe interval "
                    f"[{interval['lower']:.4f}, {interval['upper']:.4f}] does "
                    f"not intersect ±{C.REFERENCE_NEWCOMBE_REGION}")
        else:
            reasons.append("no paired draw-level data for the Newcombe "
                           "condition")

        pre = prescreen.get(q)
        if pre is None:
            reasons.append("no pre-screen measurement")
        elif abs(pre - a_prescreen) > C.REFERENCE_PRESCREEN_CALIPER:
            reasons.append(
                f"pre-screen distance {abs(pre - a_prescreen):.4f} exceeds "
                f"{C.REFERENCE_PRESCREEN_CALIPER}")

        if not length_caliper_ok(family, q, n_star):
            reasons.append("a frozen wording is outside 20% of the "
                           "corresponding A wording")

        vac = vacuity.get(q)
        if vac is None:
            reasons.append("no vacuity measurement")
        elif vac > C.REFERENCE_VACUITY_MAX:
            reasons.append(f"solo vacuity {vac:.3f} exceeds "
                           f"{C.REFERENCE_VACUITY_MAX}")

        try:
            verify_pair(Constraint(family, q), Constraint("A", n_star))
            for m in FOCAL_GRID:
                verify_pair(Constraint(family, q), Constraint("B", m))
        except ProtocolError as error:
            reasons.append(f"witness failure: {error}")

        candidates.append({
            "severity": q, "solo_compliance": mean,
            "difference_from_A": difference,
            "abs_difference": tie_key(abs(difference)),
            "newcombe": interval,
            "paired_se": clustered_paired_se(
                [r - a for r, a in zip(values, a_calibration)]),
            "prescreen_compliance": pre,
            "vacuity": vac, "admissible": not reasons, "reasons": reasons})

    admissible = [c for c in candidates if c["admissible"]]
    if not admissible:
        return {"family": family, "selected": None, "candidates": candidates}
    # Minimise the solo distance; the LESS restrictive severity breaks an
    # exact within-family tie (§13.2). Less restrictive means the larger q.
    best = min(admissible,
               key=lambda c: (tie_key(c["abs_difference"]), -c["severity"]))
    return {"family": family, "selected": best, "candidates": candidates}


def gate3_payload(family_results: Sequence[Mapping[str, Any]], *,
                  n_star: int) -> dict[str, Any]:
    """§13.2: the final three, or EXCESS_NOT_IDENTIFIED and the reduced design.

    **This gate is not terminal (§13.5, T-11).** v3 returned
    REFERENCE_POOL_MISMATCH and stopped, and two of four v3 replications
    produced no evidence at all as a result. v4 records an identification
    status and continues.
    """
    admitted = [r for r in family_results if r.get("selected")]
    admitted.sort(key=lambda r: (tie_key(r["selected"]["abs_difference"]),
                                 r["family"]))
    chosen = admitted[:C.N_FINAL_REFERENCES]

    if len(chosen) < C.N_FINAL_REFERENCES:
        return {
            "outcome": "PASS",
            "admitted": [{"family": r["family"], **r["selected"]}
                         for r in chosen],
            "admission_table": list(family_results),
            "design": "reduced",
            "slots": list(C.REDUCED_SLOTS),
            "cells_per_block": C.N_CELLS_REDUCED,
            "identification_statuses": ["EXCESS_NOT_IDENTIFIED"],
            "note": ("fewer than three families were admitted, so L3 is "
                     "withheld and the replication runs the reduced design of "
                     "§8.6. L1 and L2 remain available; this is a registered "
                     "outcome and not a failure of the study (§13.5)"),
        }

    slot_map = {"A": ("A", n_star)}
    for index, entry in enumerate(chosen, start=1):
        slot_map[f"R{index}"] = (entry["family"], entry["selected"]["severity"])
    return {
        "outcome": "PASS",
        "admitted": [{"family": r["family"], **r["selected"]} for r in chosen],
        "admission_table": list(family_results),
        "design": "full",
        "slots": list(C.REGISTERED_SLOTS),
        "cells_per_block": C.N_CELLS_FULL,
        "reference_slots": {f"R{i}": [r["family"], r["selected"]["severity"]]
                            for i, r in enumerate(chosen, start=1)},
        "identification_statuses": [],
        "tie_break": ("the less restrictive severity breaks an exact "
                      "within-family tie; the family identifier breaks an "
                      "exact tie between families"),
        "not_a_criterion": ("composed uptake is never a matching criterion: "
                            "composed compliance is the outcome and selecting "
                            "a control on it would be circular (§13.3)"),
    }


# ------------------------------------------------------------------- Gate 4
def gate4_payload(cell_rates: Mapping[str, Mapping[str, float]]
                  ) -> dict[str, Any]:
    """§13.6: each cell type evaluated independently against [0.05, 0.95].

    ``cell_rates`` maps a cell type to {slot: compliance rate}. The gate is a
    viability predicate applied cell by cell. It does not rank, select, or
    reorder anything, and it computes no contrast between cells.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    table: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for cell_type, rates in sorted(cell_rates.items()):
        for slot, rate in sorted(rates.items()):
            row = {"cell_type": cell_type, "slot": slot, "compliance": rate,
                   "inside_band": low <= rate <= high}
            table.append(row)
            if not row["inside_band"]:
                failures.append(row)
    if failures:
        raise TerminalStatus("COMPOSED_HEADROOM_FAILURE", {
            "status": "COMPOSED_HEADROOM_FAILURE", "gate": C.STAGE_GATE4,
            "criterion": "every registered cell type inside the band on both "
                         "constraints",
            "threshold": list(C.COMPOSED_HEADROOM_BAND),
            "observed": failures, "composed_table": table,
            "artifact_hashes": {},
            "strongest_permissible_statement":
                "at least one registered cell type falls outside the "
                "composed-headroom band on one of its constraints",
            "estimands_unanswerable": "all"})
    return {"outcome": "PASS", "composed_table": table,
            "band": list(C.COMPOSED_HEADROOM_BAND),
            "computes_no_contrast": True, "identification_statuses": []}
