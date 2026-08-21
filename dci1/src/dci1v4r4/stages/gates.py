"""Gate 2, Gate 3 and Gate 4 payloads (v4r3 §12.3, §12.4, §13, §13.10).

Gate 2 differs from v4r2's in two registered ways, and both are defect
resolutions rather than preferences:

**§12.4's graded clause is a share.** v4r2 said the graded distribution must
not be *"concentrated above 0.99 or below 0.01"* and its code compared one
float per constraint against 0.99 without saying which. Read as the *mean*
graded score the clause fires on every severity §12.3 declares eligible,
because B's graded score rises with compliance and crosses 0.99 inside the
focal band -- so §12.3 would declare a rung eligible and §12.4 would declare
the same rung degenerate, on every model under every prompt. This module
takes a distribution and reads a share, and refuses a bare float, so the
ambiguity cannot recur silently.

**The focal grid escalates.** ``select_focal_severity`` tries the registered
grid first and reports whether the §7.2 extension is needed. Only when it is
does the caller measure the extension and call again with ``extended=True``.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C
from dci1v4r4.verifiers.constraints import FOCAL_EXTENSION, focal_severities

__all__ = ["TerminalStatus", "tie_key", "select_severity",
           "select_focal_severity", "graded_degeneracy", "gate2_payload",
           "gate3_payload", "gate4_payload"]


class TerminalStatus(Exception):
    """A registered terminal outcome, raised as a value and written once."""

    def __init__(self, status: str, detail: Mapping[str, Any]):
        if status not in C.TERMINAL_STATUSES:
            raise ProtocolError(f"{status!r} is not a registered terminal "
                                "status")
        super().__init__(status)
        self.status = status
        self.detail = dict(detail)
        self.detail["terminal_sentence"] = C.TERMINAL_SENTENCE


def tie_key(value: float) -> float:
    return round(value, 12)


def _diagnose_band(curve: Mapping[int, float], band: tuple[float, float],
                   grid: Sequence[int], *, exhausted: str) -> str:
    """§12.3: distinguish a resolution gap from an exhausted range."""
    lo, hi = band
    ordered = sorted(curve)
    for a, b in zip(ordered, ordered[1:]):
        va, vb = curve[a], curve[b]
        if (va < lo and vb > hi) or (va > hi and vb < lo):
            return "GRID_RESOLUTION_INSUFFICIENT"
    return exhausted


def select_severity(curve: Mapping[int, float], *, band: tuple[float, float],
                    aim: float, prefer: str = "smaller") -> int | None:
    """Minimise |value - aim| among severities inside the band."""
    lo, hi = band
    eligible = [q for q, v in curve.items() if lo <= v <= hi]
    if not eligible:
        return None
    sign = 1 if prefer == "smaller" else -1
    return min(eligible, key=lambda q: (tie_key(abs(curve[q] - aim)), sign * q))


def select_focal_severity(registered_curve: Mapping[int, float],
                          extended_curve: Mapping[int, float] | None = None
                          ) -> dict[str, Any]:
    """§12.3's focal selection with the §7.2 escalation.

    The extension is *measured* in the §12.2 dense screen on every model, but
    it becomes selectable only here and only when the registered grid supplies
    no eligible severity. A flat six-rung grid would move ``m*`` on a model
    whose registered grid already works, because selection takes the rung
    nearest 0.80 and a new rung can be nearer -- which is a change of
    operating point that no evidence asked for.
    """
    for q in registered_curve:
        if q not in C.FOCAL_GRID:
            raise ProtocolError(
                f"m={q} is not in the registered focal grid {C.FOCAL_GRID}; "
                "extension rungs belong in extended_curve")
    m_star = select_severity(registered_curve, band=C.FOCAL_BAND,
                             aim=C.FOCAL_AIM, prefer="smaller")
    if m_star is not None:
        return {"m_star": m_star, "extension_measured": False,
                "grid_used": C.FOCAL_GRID, "curve": dict(registered_curve)}
    if extended_curve is None:
        return {"m_star": None, "extension_required": True,
                "extension_measured": False, "grid_used": C.FOCAL_GRID,
                "curve": dict(registered_curve),
                "reading": ("no severity of the registered grid is eligible; "
                            "§7.2's extension must be measured on the same 96 "
                            "solo-calibration topics before selection can "
                            "run over the union")}
    for q in extended_curve:
        if q not in FOCAL_EXTENSION:
            raise ProtocolError(f"m={q} is not a §7.2 extension rung")
    union = {**registered_curve, **extended_curve}
    m_star = select_severity(union, band=C.FOCAL_BAND, aim=C.FOCAL_AIM,
                             prefer="smaller")
    if m_star is None:
        raise TerminalStatus("FOCAL_RANGE_EXHAUSTED", {
            "curve": union, "band": C.FOCAL_BAND,
            "grid": focal_severities(extended=True),
            "diagnosis": _diagnose_band(union, C.FOCAL_BAND,
                                        focal_severities(extended=True),
                                        exhausted="FOCAL_RANGE_EXHAUSTED")})
    return {"m_star": m_star, "extension_measured": True,
            "grid_used": focal_severities(extended=True), "curve": union}


def graded_degeneracy(distribution: Sequence[float]) -> dict[str, float]:
    """§12.4 condition 3, read as a SHARE of a distribution.

    ``distribution`` is one graded score per scored response, not a summary.
    Passing a single float is refused: that is the shape that let v4r2's code
    leave the reading open.
    """
    if isinstance(distribution, (int, float)):
        raise ProtocolError(
            "§12.4 condition 3 reads a distribution, not a summary. v4r2's "
            "code compared one float per constraint against 0.99 and never "
            "said which float; under the mean reading the clause fires on "
            "every severity §12.3 declares eligible. Pass the graded scores.")
    values = list(distribution)
    if not values:
        raise ProtocolError("an empty graded distribution")
    n = len(values)
    high = sum(1 for g in values if g > C.GRADED_DEGENERACY_HIGH) / n
    low = sum(1 for g in values if g < C.GRADED_DEGENERACY_LOW) / n
    return {"share_above_high": high, "share_below_low": low,
            "n": n, "reading": C.GRADED_CLAUSE_READING}


def gate2_payload(*, a_curve: Mapping[int, float],
                  focal_registered_curve: Mapping[int, float],
                  focal_extended_curve: Mapping[int, float] | None,
                  b_solo_vacuity: float,
                  graded_distributions: Mapping[str, Sequence[float]],
                  a_chance: float, b_chance: float,
                  truncation_by_cell: Mapping[str, float] | None = None
                  ) -> dict[str, Any]:
    """§12.3 selection and §12.4 adequacy, in that order."""
    n_star = select_severity(a_curve, band=C.TARGET_BAND, aim=C.TARGET_AIM,
                             prefer="smaller")
    if n_star is None:
        raise TerminalStatus(
            _diagnose_band(a_curve, C.TARGET_BAND, C.TARGET_GRID,
                           exhausted="TARGET_RANGE_EXHAUSTED"),
            {"curve": dict(a_curve), "band": C.TARGET_BAND,
             "grid": C.TARGET_GRID})

    focal = select_focal_severity(focal_registered_curve, focal_extended_curve)
    if focal["m_star"] is None:
        return {"outcome": "PENDING_FOCAL_EXTENSION", "n_star": n_star,
                "focal": focal}

    adequacy: list[str] = []
    if b_solo_vacuity > C.REGIME_VACUITY_MAX:
        adequacy.append(
            f"B solo vacuity {b_solo_vacuity:.3f} above "
            f"{C.REGIME_VACUITY_MAX}")
    graded = {}
    for kind, dist in graded_distributions.items():
        summary = graded_degeneracy(dist)
        graded[kind] = summary
        if summary["share_above_high"] > C.GRADED_DEGENERACY_SHARE_MAX:
            adequacy.append(
                f"{kind}: {summary['share_above_high']:.3f} of responses have "
                f"a graded score above {C.GRADED_DEGENERACY_HIGH}")
        if summary["share_below_low"] > C.GRADED_DEGENERACY_SHARE_MAX:
            adequacy.append(
                f"{kind}: {summary['share_below_low']:.3f} of responses have "
                f"a graded score below {C.GRADED_DEGENERACY_LOW}")
    if adequacy:
        raise TerminalStatus("REGIME_NOT_FOUND", {
            "n_star": n_star, "m_star": focal["m_star"],
            "a_curve": dict(a_curve), "focal": focal,
            "b_solo_vacuity": b_solo_vacuity, "graded": graded,
            "failures": adequacy,
            "note": ("REGIME_NOT_FOUND is a statement about the registered "
                     "grid. It is never reported as a failure of the model "
                     "or of the hypothesis.")})

    from dci1v4r4.stages.selection import instructed_compliance
    return {
        "outcome": "PASS", "stage": C.STAGE_GATE2,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE2],
        "n_star": n_star, "m_star": focal["m_star"], "focal": focal,
        "a_solo_compliance": a_curve[n_star],
        "b_solo_compliance": focal["curve"][focal["m_star"]],
        "a_chance_compliance": a_chance, "b_chance_compliance": b_chance,
        "iota_a": instructed_compliance(a_curve[n_star], a_chance),
        "iota_b": instructed_compliance(focal["curve"][focal["m_star"]],
                                        b_chance),
        "b_solo_vacuity": b_solo_vacuity, "graded": graded,
        "graded_clause_reading": C.GRADED_CLAUSE_READING,
        "truncation_by_cell": dict(truncation_by_cell or {}),
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
    }


def gate3_payload(selection: Any) -> dict[str, Any]:
    """§13.4, §13.6 and §13.7's outcome, as a signed record.

    Not terminal in any branch: fewer than three straddling families sets
    `EXCESS_NOT_IDENTIFIED` and `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and routes
    the replication to §8.6's reduced design, which still estimates
    D(B<-A), D(A<-B), Lambda and -- when the class arm survives --
    Delta_class.
    """
    slot_map = selection.slot_map()
    full = selection.design == "full"
    class_arm = bool(selection.klass.get("available"))
    if full:
        cells = C.N_CELLS_FULL if class_arm else C.N_CELLS_FULL_NO_CLASS
    else:
        cells = (C.N_CELLS_REDUCED_WITH_CLASS if class_arm
                 else C.N_CELLS_REDUCED)
    return {
        "outcome": "PASS", "stage": C.STAGE_GATE3,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE3],
        "design": selection.design, "cells_per_block": cells,
        "class_arm": class_arm,
        "core_references": selection.core["core_references"],
        "spectrum": selection.spectrum,
        "spectrum_triples": selection.core["spectrum_triples"],
        "dropped_for_no_triple": selection.core["dropped_for_no_triple"],
        "class_companion": selection.klass.get("companion"),
        "slot_map": slot_map,
        "identification_statuses": selection.identification_statuses,
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "selection_read_only_solo_and_chance": True,
    }


def gate4_payload(cell_rates: Mapping[str, Mapping[str, float]]
                  ) -> dict[str, Any]:
    """§13.10: a viability predicate, cell by cell, on every constraint.

    It ranks nothing, selects nothing and computes no contrast between cells.
    A headroom failure is terminal for the replication and is never an
    instruction to choose different rungs: Gate 4 runs *after* the spectrum
    and the class companion are fixed.
    """
    lo, hi = C.COMPOSED_HEADROOM_BAND
    failures = [{"cell": cell, "slot": slot, "rate": rate}
                for cell, by_slot in sorted(cell_rates.items())
                for slot, rate in sorted(by_slot.items())
                if not lo <= rate <= hi]
    if failures:
        raise TerminalStatus("COMPOSED_HEADROOM_FAILURE", {
            "band": list(C.COMPOSED_HEADROOM_BAND), "failures": failures,
            "table": {k: dict(v) for k, v in cell_rates.items()}})
    return {"outcome": "PASS", "stage": C.STAGE_GATE4,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE4],
            "band": list(C.COMPOSED_HEADROOM_BAND),
            "table": {k: dict(v) for k, v in cell_rates.items()},
            "computes_no_contrast": True, "ranks_nothing": True}
