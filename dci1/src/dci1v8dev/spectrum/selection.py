"""A deterministic spectrum-selection rule (v8 candidate).

Inputs are **pre-composition only**: the pooled calibration rows that
passed ``validity.spectrum_validity`` (solo, chance, kappa(R|B), vacuity,
structure, the unfolded two-split stability, and the position rule),
iota_A on the same table, the core references (whose rungs may serve as
centre points when their family is selected), and the rule's constants.
No composed quantity exists in the input schema (§13.11's loader refuses
it before this function is reached).

The rule, in order, every step deterministic with registered tie-breaks
(structural tier, then registered feature-group order, then the less
restrictive severity, then family id):

1. Per family, the candidate **low** point is the spectrum-valid rung at
   or below ``iota_A - d_min`` nearest ``iota_A - target_below``; the
   candidate **high** point is the rung at or above ``iota_A + d_min``
   nearest ``iota_A + target_above``. A family with both is *straddling*;
   its points are the two, plus its core rung when it is a core family
   (§11.8's family intercept makes the centre point pure leverage).
2. Straddling families are ranked by within-family leverage
   ``sum (d - dbar_f)^2`` (what the slope is identified from), taken in
   that order **preferring a feature group not yet represented**, up to
   ``max_families``.
3. If the selected set does not meet ``coverage.CoverageRule`` on a side
   (points, families, offset), one-sided families are added for that
   side: the two spectrum-valid rungs on that side farthest apart (a pair
   carries leverage; a single point carries none), again by leverage and
   diversity, until the side is covered or the pool is exhausted.
4. ``selected_coverage`` is evaluated on the final set and its verdict is
   the identification status of the spectrum arm at design time.

Targets are asymmetric because the admissible band is: with A aimed at
0.70 solo and V_head capping a chance-free reference near 0.855, the easy
side has at most ~0.15 of room; the hard side has ~0.55. The defaults are
the values the precision analysis supports (``tools/v8_spectrum_precision``).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from dci1v7.stages.calibration_table import CalibrationRow, tie_key
from dci1v7.stages.selection import _group_order, restrictiveness_key
from dci1v8dev import rules as R
from dci1v8dev.spectrum.coverage import CoverageRule, selected_coverage
from dci1v8dev.spectrum.validity import _se_iota

__all__ = ["DEFAULT_SELECTION_RULE", "SelectionRule", "select_spectrum"]


@dataclass(frozen=True)
class SelectionRule:
    d_min: float = R.SPECTRUM_D_MIN
    target_below: float = R.SELECTION_TARGET_BELOW
    target_above: float = R.SELECTION_TARGET_ABOVE
    max_families: int = R.SELECTION_MAX_FAMILIES
    include_core_rungs: bool = True
    #: Two points of one family must differ in iota by at least this, so a
    #: pair of nearly identical rungs is never taken as two design points.
    min_separation: float = R.SELECTION_MIN_SEPARATION
    coverage: CoverageRule = field(default_factory=CoverageRule)


DEFAULT_SELECTION_RULE = SelectionRule()


def _tiebreak(row: CalibrationRow) -> tuple:
    return (row.structural_tier, _group_order(row.kind),
            restrictiveness_key(row.kind, row.severity), row.kind)


def _leverage(ds: Sequence[float]) -> float:
    if len(ds) < 2:
        return 0.0
    m = sum(ds) / len(ds)
    return float(sum((d - m) ** 2 for d in ds))


def select_spectrum(valid_rows: Sequence[CalibrationRow], *, iota_a: float,
                    core_references: Mapping[str, int] = (),
                    rule: SelectionRule = DEFAULT_SELECTION_RULE) -> dict[str, Any]:
    core_references = dict(core_references)
    by_family: dict[str, list[CalibrationRow]] = {}
    for r in valid_rows:
        by_family.setdefault(r.kind, []).append(r)
    trace: list[str] = []
    candidates: dict[str, dict[str, Any]] = {}
    for fam, rows in sorted(by_family.items()):
        below = [r for r in rows if tie_key(r.iota) <= tie_key(iota_a - rule.d_min)]
        above = [r for r in rows if tie_key(r.iota) >= tie_key(iota_a + rule.d_min)]
        low = min(below, key=lambda r: (tie_key(abs(r.iota - (iota_a - rule.target_below))),
                                        _tiebreak(r))) if below else None
        high = min(above, key=lambda r: (tie_key(abs(r.iota - (iota_a + rule.target_above))),
                                         _tiebreak(r))) if above else None
        core_row = None
        if rule.include_core_rungs and fam in core_references:
            core_row = next((r for r in rows
                             if r.severity == core_references[fam]), None)
        # the core rung on the pooled table is not in `valid_rows` when V_pos
        # excludes it (it is by construction near A); look it up separately
        candidates[fam] = {"low": low, "high": high, "core": core_row,
                           "below_pool": sorted(below, key=lambda r: r.iota),
                           "above_pool": sorted(above, key=lambda r: r.iota)}

    def family_points(fam: str, entries: dict[str, Any], *, sides=("low", "high")
                      ) -> list[dict[str, Any]]:
        pts = []
        for side in sides:
            r = entries.get(side)
            if r is not None:
                pts.append({"candidate": r.label, "family": fam,
                            "severity": r.severity, "iota": r.iota,
                            "se_iota": _se_iota(r),
                            "side": "below" if side == "low" else "above",
                            "role": "SPECTRUM_LOW" if side == "low"
                            else "SPECTRUM_HIGH",
                            "structural_tier": r.structural_tier,
                            "feature_group": r.feature_group})
        return pts

    straddling = []
    for fam, e in candidates.items():
        if e["low"] is not None and e["high"] is not None:
            pts = family_points(fam, e)
            ds = [p["iota"] for p in pts]
            if e["core"] is not None:
                ds.append(e["core"].iota)
            straddling.append((fam, _leverage(ds), pts))
    ranked = sorted(straddling, key=lambda t: (
        -t[1], t[2][0]["structural_tier"], _group_order(t[0]), t[0]))
    selected: list[dict[str, Any]] = []
    families: list[str] = []
    groups: set[str] = set()
    for fam, lev, pts in ranked:               # diversity pass
        if len(families) >= rule.max_families:
            break
        g = pts[0]["feature_group"]
        if g in groups:
            continue
        families.append(fam)
        groups.add(g)
        selected.extend(pts)
        trace.append(f"{fam}: straddling, leverage {lev:.4f}, new group {g}")
    for fam, lev, pts in ranked:               # fill pass
        if len(families) >= rule.max_families:
            break
        if fam in families:
            continue
        families.append(fam)
        selected.extend(pts)
        trace.append(f"{fam}: straddling, leverage {lev:.4f}, repeated group")

    def with_core(points):
        out = list(points)
        for fam in families:
            e = candidates[fam]
            if e["core"] is not None and rule.include_core_rungs:
                out.append({"candidate": e["core"].label, "family": fam,
                            "severity": e["core"].severity,
                            "iota": e["core"].iota, "side": "core",
                            "se_iota": _se_iota(e["core"]),
                            "role": "CORE_CENTRE",
                            "structural_tier": e["core"].structural_tier,
                            "feature_group": e["core"].feature_group})
        return out

    coverage = selected_coverage(with_core(selected), iota_a=iota_a,
                                 rule=rule.coverage)
    # one-sided fill, per deficient side
    for side_key, pool_key in (("below", "below_pool"), ("above", "above_pool")):
        deficient = any(side_key in r for r in coverage["reasons"])
        if not deficient:
            continue
        options = []
        for fam, e in candidates.items():
            if fam in families:
                continue
            pool = e[pool_key]
            if len(pool) >= 2 and abs(pool[-1].iota - pool[0].iota) >= rule.min_separation:
                pair = [pool[0], pool[-1]]
                options.append((fam, _leverage([r.iota for r in pair]), pair))
        for fam, lev, pair in sorted(options, key=lambda t: (
                -t[1], t[2][0].structural_tier, _group_order(t[0]), t[0])):
            if len(families) >= rule.max_families + 2:
                break
            families.append(fam)
            for r in pair:
                selected.append({"candidate": r.label, "family": fam,
                                 "severity": r.severity, "iota": r.iota,
                                 "se_iota": _se_iota(r), "side": side_key,
                                 "role": f"SPECTRUM_{side_key.upper()}_PAIR",
                                 "structural_tier": r.structural_tier,
                                 "feature_group": r.feature_group})
            trace.append(f"{fam}: one-sided {side_key} pair, leverage "
                         f"{lev:.4f}")
            coverage = selected_coverage(with_core(selected), iota_a=iota_a,
                                         rule=rule.coverage)
            if not any(side_key in r for r in coverage["reasons"]):
                break
    points = with_core(selected)
    slots = {}
    for i, p in enumerate(sorted(points, key=lambda p: (families.index(p["family"]),
                                                        p["iota"]))):
        slots[f"X{i + 1}"] = p["candidate"]
    per_family = {}
    for fam in families:
        ds = [p["iota"] for p in points if p["family"] == fam]
        per_family[fam] = {"n_points": len(ds), "leverage": _leverage(ds),
                           "min_iota": min(ds), "max_iota": max(ds)}
    return {"iota_a": iota_a, "families": families,
            "points": sorted(points, key=lambda p: (p["family"], p["iota"])),
            "slots": slots,
            "n_spectrum_references": sum(1 for p in points
                                         if p["role"] != "CORE_CENTRE"),
            "per_family": per_family,
            "coverage": coverage,
            "identified": coverage["identified"],
            "status": coverage["status"],
            "trace": trace,
            "rule": {"d_min": rule.d_min, "target_below": rule.target_below,
                     "target_above": rule.target_above,
                     "max_families": rule.max_families,
                     "include_core_rungs": rule.include_core_rungs,
                     "min_separation": rule.min_separation}}
