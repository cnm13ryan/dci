"""The current (v5-v7) pre-screen certificate and retention, for comparison.

Reproduced by calling the registered v7 kernels on the same input, so the
comparison is against what the study actually computes and not against a
paraphrase: ``regime.coverage_rows`` + ``regime.coverage_criterion`` at
§12.6's pre-screen iota_A (A's severity whose solo compliance is nearest
§12.3's aim, no band --- ``run/regime_run.regime_payload``), per-family C4
state via ``regime.family_c4_state``, and §12.7's retention
(``regime.calibration_priority``: every Tier-1/2 rung plus the 24 Tier-3
rungs nearest iota_A on the pre-screen point estimate).
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dci1v7.protocol import constants as C
from dci1v7.stages import regime
from dci1v7.stages.calibration_table import tie_key
from dci1v7.verifiers.constraints import FAMILIES
from dci1v8dev.prescreen.schema import ARung, PrescreenRung

__all__ = [
    "family_c4_states",
    "legacy_certificate",
    "legacy_retention",
    "legacy_rows",
    "prescreen_iota_a",
]

ELIGIBILITY_FORMULATION = "E2"   # §33 U4's resolution, v5 A5


def prescreen_iota_a(a_grid: Sequence[ARung]) -> tuple[float | None, int | None]:
    """§12.6's pre-screen iota_A, exactly as ``regime_payload`` computes it."""
    rows = []
    for a in a_grid:
        if a.chance_rate >= C.CHANCE_DEGENERACY_MAX:
            continue
        iota = (a.solo_rate - a.chance_rate) / (1.0 - a.chance_rate)
        rows.append((tie_key(abs(a.solo_rate - C.TARGET_AIM)), a.severity, iota))
    if not rows:
        return None, None
    _, severity, iota = min(rows)
    return iota, severity


def legacy_rows(table: Sequence[PrescreenRung]) -> list[dict[str, Any]]:
    """§12.2's difficulty-table rows in the shape the v7 kernels read."""
    raw = []
    for r in table:
        kappa = r.chance_rate
        iota = (None if kappa >= C.CHANCE_DEGENERACY_MAX
                else (r.solo_rate - kappa) / (1.0 - kappa))
        raw.append({"candidate": r.label, "kind": r.kind,
                    "severity": r.severity, "solo": r.solo_rate,
                    "chance": kappa, "iota": iota,
                    "vacuity": r.vacuity_rate, "n_topics": r.n_topics,
                    "tier": FAMILIES[r.kind].structural_tier,
                    "family": r.kind, "is_outcome": False})
    carried = [r["candidate"] for r in raw]     # §12.2 carries all of these
    return regime.coverage_rows(raw, carried,
                                formulation=ELIGIBILITY_FORMULATION)


def family_c4_states(rows: Sequence[dict[str, Any]], *, iota_a: float
                     ) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_family.setdefault(r["family"], []).append(r)
    out = {}
    for family, entries in sorted(by_family.items()):
        state = regime.family_c4_state(entries, iota_a=iota_a)
        state["deficiency"] = regime.family_deficiency(state)
        state["c4_met"] = state["deficiency"] is None
        state["feature_group"] = FAMILIES[family].feature_group
        state["structural_tier"] = FAMILIES[family].structural_tier
        out[family] = state
    return out


def legacy_certificate(table: Sequence[PrescreenRung],
                       a_grid: Sequence[ARung]) -> dict[str, Any]:
    """§12.6's C1-C8 on the pre-screen point estimates (the v7 certificate)."""
    iota_a, severity = prescreen_iota_a(a_grid)
    rows = legacy_rows(table)
    if iota_a is None:
        return {"iota_a_prescreen": None, "iota_a_severity": None,
                "coverage": None, "families": {}, "rows": rows}
    coverage = regime.coverage_criterion(rows, iota_a=iota_a)
    return {"iota_a_prescreen": iota_a, "iota_a_severity": severity,
            "coverage": coverage,
            "families": family_c4_states(rows, iota_a=iota_a),
            "rows": rows}


def legacy_retention(table: Sequence[PrescreenRung], *, iota_a: float | None
                     ) -> dict[str, Any]:
    """§12.7: every Tier-1/2 rung plus at most 24 Tier-3 nearest iota_A."""
    carried = []
    for r in table:
        kappa = r.chance_rate
        iota = (None if kappa >= C.CHANCE_DEGENERACY_MAX
                else (r.solo_rate - kappa) / (1.0 - kappa))
        carried.append({"candidate": r.label, "family": r.kind,
                        "structural_tier": FAMILIES[r.kind].structural_tier,
                        "prescreen_iota": iota})
    return regime.calibration_priority(
        carried, iota_a_prescreen=iota_a if iota_a is not None else 0.5)
