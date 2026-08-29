#!/usr/bin/env python3
"""Difficulty-spectrum / C4 investigation on the stored v7 evidence. DEVELOPMENT.

    python tools/v7_spectrum_dev_analysis.py \
        --tree /path/dci1/evidence/dci1v7 \
        --landscape reports/dci1v7/reference_support_landscape/landscape.json \
        --out reports/dci1v7/difficulty_spectrum_dev

Read-only over the tree. For each registered v7 replication it rebuilds, with
the production kernels and §13.2's corrected chance basis (the 2026-08-29
correction, `tools/v7_chance_basis_impact.py`):

* the per-rung reference table (Phase 2): family, tier, feature group,
  severity, solo, κ_c, ι, eligibility and its reason, side of ι_A and
  distance, Gate-2.5 qualification, §13.7 stability, full V(R), the signed
  slot (R1–R3, R±, CL, frozen backup);
* §12.6's C1–C8 on the calibrated basis and the exact per-family C4 state on
  four bases — calibrated eligible (the gating one), calibrated all-measured
  (eligibility ignored), pre-screen same rungs, pre-screen certificate — and
  the first deficiency, then a classification of every non-straddling family
  into the buckets flat / missing side / eligibility cutoff / pre-screen
  noise / other (Phase 3);
* local support (rungs within ±0.05/0.10/0.15 of ι_A) against spectrum
  support (usable range, straddling families, span, coverage by ι bin)
  (Phase 4);
* two plots per model: the reference landscape and the family ladders.

Stability, full-V(R) and registered-spectrum verdicts per rung are joined
from the prior session's `landscape.json` (same kernels, same corrected
basis) and every joined row is checked for ι and eligibility agreement with
this reconstruction; a disagreement is recorded, never silently resolved.
Nothing under the tree is written.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

import v7_chance_basis_impact as impact  # noqa: E402

from dci1v7.analysis.intervals import wilson  # noqa: E402
from dci1v7.protocol import constants as C  # noqa: E402
from dci1v7.run import gates_run  # noqa: E402
from dci1v7.stages import regime  # noqa: E402
from dci1v7.stages.calibration_table import tie_key  # noqa: E402
from dci1v7.verifiers.constraints import FAMILIES  # noqa: E402

MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
BINS = [-0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5]


def _load(path: pathlib.Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _iota(solo: float | None, chance: float | None) -> float | None:
    if solo is None or chance is None or chance >= C.CHANCE_DEGENERACY_MAX:
        return None
    return (solo - chance) / (1.0 - chance)


def _side(iota: float | None, iota_a: float) -> str | None:
    if iota is None:
        return None
    if tie_key(iota) < tie_key(iota_a):
        return "below"
    if tie_key(iota) > tie_key(iota_a):
        return "above"
    return "at"


def _family_state(entries: list[dict[str, Any]], iota_a: float,
                  *, eligible_only: bool) -> dict[str, Any]:
    rows = [e for e in entries if e.get("iota") is not None
            and (e.get("eligible") or not eligible_only)]
    if eligible_only:
        state = regime.family_c4_state(entries, iota_a=iota_a)
    else:
        below = [e for e in rows if tie_key(e["iota"]) < tie_key(iota_a)]
        above = [e for e in rows if tie_key(e["iota"]) > tie_key(iota_a)]
        span = (max(e["iota"] for e in rows) - min(e["iota"] for e in rows)
                if rows else 0.0)
        state = {"n_rungs": len(rows), "has_below": bool(below),
                 "has_above": bool(above), "span": span,
                 "severities": sorted(e["severity"] for e in rows)}
    state["n_below"] = sum(1 for e in rows
                           if tie_key(e["iota"]) < tie_key(iota_a))
    state["n_above"] = sum(1 for e in rows
                           if tie_key(e["iota"]) > tie_key(iota_a))
    state["min_iota"] = min((e["iota"] for e in rows), default=None)
    state["max_iota"] = max((e["iota"] for e in rows), default=None)
    state["deficiency"] = regime.family_deficiency(state)
    state["met"] = state["deficiency"] is None
    return state


def _bucket(cal_elig: dict, cal_all: dict, pre_same: dict | None,
            n_measured: int, tier: int) -> tuple[str, str]:
    """Classify why a family does not contribute a C4 group (Phase 3)."""
    if cal_elig["met"]:
        return "MET", "contributes a straddling group on the calibrated basis"
    pre_wide = bool(pre_same and pre_same["n_rungs"] >= 3
                    and pre_same["has_below"] and pre_same["has_above"]
                    and pre_same["span"] >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN)
    if tier == 3 and n_measured < 3:
        return ("E", "Tier-3 family: §12.7's 24-rung cap carried "
                     f"{n_measured} rung(s) into calibration, too few for C4")
    if not (cal_all["has_below"] and cal_all["has_above"]):
        side = "above" if cal_all["has_below"] else "below"
        if cal_all["n_rungs"] == 0:
            return "E", "no measured rung has a defined coordinate"
        return ("B", f"every measured rung lies {'below' if side == 'above' else 'above'} "
                     f"iota_A; nothing measured on the {side} side"
                + (" (pre-screen showed a wide straddle: D)" if pre_wide else ""))
    if not (cal_elig["has_below"] and cal_elig["has_above"]):
        side = "above" if cal_elig["has_below"] else "below"
        return ("C", f"measured rungs straddle iota_A but every rung {side} "
                     "iota_A is ineligible (solo outside [0.10, 0.90] or "
                     "vacuity > 0.10)")
    if cal_elig["n_rungs"] < C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY:
        return ("C", f"straddles with only {cal_elig['n_rungs']} eligible "
                     "rung(s); the rest are ineligible")
    if cal_all["span"] >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN:
        return ("C", f"all-measured span {cal_all['span']:.3f} >= 0.40 but the "
                     f"eligible span is {cal_elig['span']:.3f}: the extreme "
                     "rungs are trimmed by the eligibility band")
    if pre_wide:
        return ("D", f"pre-screen span on the same rungs {pre_same['span']:.3f} "
                     f">= 0.40, calibrated span {cal_all['span']:.3f}: the "
                     "24x1 pre-screen inflated the span")
    return ("A", f"flat ladder: straddles but the whole measured ladder spans "
                 f"only {cal_all['span']:.3f} (< 0.40)")


def analyse(model: str, tree: pathlib.Path, landscape: dict[str, Any]
            ) -> dict[str, Any]:
    mdir = tree / model
    reg = _load(mdir / "REGIME_SCREEN" / "regime_record.json")
    g2 = _load(mdir / "GATE_2_FOCAL_CALIBRATION" / "gate2_focal_calibration.json")
    g25 = _load(mdir / "GATE_2_5_CANDIDATE_QUALIFICATION"
                / "gate2_5_candidate_qualification.json")
    g3a = _load(mdir / "GATE_3A_REFERENCE_CALIBRATION"
                / "gate3a_reference_calibration.json")
    g3b = _load(mdir / "GATE_3B_REFERENCE_SELECTION"
                / "gate3b_reference_selection.json")
    g3c = _load(mdir / "GATE_3C_IDENTIFICATION" / "gate3c_identification.json")
    iota_a = float(g2["iota_a"])
    iota_a_pre = float(reg["iota_a_prescreen"])
    m_star = int(g2["m_star"])
    formulation = reg["coverage_eligibility_formulation"]

    # ---- corrected chance basis (production `cell_rates` on the grid runs)
    unconstrained = impact._unconstrained_rows(mdir / "GATE_2_FOCAL_CALIBRATION")
    corrected = impact._corrected_tables(g2, unconstrained)
    pooled = corrected["pooled"]
    shaped = regime.calibration_coverage_rows(pooled, formulation=formulation)
    shaped_recorded = regime.calibration_coverage_rows(
        g2["calibration_rows"]["pooled"], formulation=formulation)
    cov = regime.coverage_criterion(shaped, iota_a=iota_a)
    cov_recorded = regime.coverage_criterion(shaped_recorded, iota_a=iota_a)
    signed_cov = g3a["coverage_at_calibrated_iota_a"]
    assert cov_recorded["conditions"] == signed_cov["conditions"], (
        model, cov_recorded["conditions"], signed_cov["conditions"])

    # ---- Gate-2.5 qualification on the corrected pooled table
    kept, withheld = gates_run._withhold_degenerate(corrected)
    qual = impact._qualify(kept["pooled"], model_key=model, m_star=m_star)
    qual_by = {v["candidate"]: v for v in qual["verdicts"]}
    for w in withheld["pooled"]:
        qual_by[f"{w['kind']}:{w['severity']}"] = {
            "passed": False, "first_failing_component": "WITHHELD_DEGENERATE"}
    qual_signed = {v["candidate"]: v for v in
                   g25["qualification_by_severity"][str(m_star)]
                   ["qualification"]["verdicts"]} \
        if "verdicts" in g25["qualification_by_severity"][str(m_star)].get(
            "qualification", {}) else {}

    # ---- prior-session landscape rows (stability, full V(R), spectrum)
    land = next((r for r in landscape["results"]
                 if r["tree"] == "v7" and r["model_key"] == model), None)
    land_by = {r["candidate"]: r for r in (land or {}).get("rungs", [])}
    land_slots = (land or {}).get("selection_corrected", {}).get("slot_map", {})
    join_mismatch: list[dict[str, Any]] = []

    # ---- signed slots
    slot_map = g3b["slot_map"]
    slot_of: dict[str, str] = {}
    for slot, (fam, sev) in slot_map.items():
        slot_of[f"{fam}:{sev}"] = slot
    backups = list(g3c["support"]["realised"].get("frozen_backups") or [])
    corrected_slot_of = {f"{v[0]}:{v[1]}": k for k, v in land_slots.items()}

    # ---- pre-screen table (24 topics x 1 draw)
    pre_by = {r["candidate"]: r for r in reg["difficulty_table"]}
    certified_groups = set(reg["expansion"]["coverage"]["realised"]
                           ["straddling_groups"])
    expansion_rounds = reg["expansion"]["rounds"]
    expanded = {}
    for rnd in expansion_rounds:
        for fam, picks in rnd["admitted"].items():
            expanded.setdefault(fam, []).extend(picks)

    # ---- per-rung table
    rungs: list[dict[str, Any]] = []
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row, sh in zip(pooled, shaped):
        label = sh["candidate"]
        fam = sh["family"]
        pre = pre_by.get(label)
        q = qual_by.get(label, {})
        lr = land_by.get(label, {})
        entry = {
            "model": model, "candidate": label, "family": fam,
            "severity": sh["severity"], "tier": sh["structural_tier"],
            "feature_group": sh["feature_group"],
            "constraint_class": sh["constraint_class"],
            "form": FAMILIES[fam].form,
            "discourse_role": FAMILIES[fam].metadata.get("discourse_role"),
            "solo": sh["solo"], "chance_corrected": row["chance_compliance"],
            "chance_recorded": g2["calibration_rows"]["pooled"][
                pooled.index(row)]["chance_compliance"],
            "iota": sh["iota"], "iota_recorded_basis": sh["solo"],
            "lift": (sh["solo"] - row["chance_compliance"]),
            "vacuity": sh["vacuity"], "kappa_under_b": row.get("kappa_under_b"),
            "median_words": row.get("median_words"),
            "solo_wilson": list(wilson(sh["solo"], row["n_topics"])),
            "eligible": sh["eligible"],
            "ineligibility_reason": sh["eligibility"]["reason"],
            "side": _side(sh["iota"], iota_a),
            "distance": (None if sh["iota"] is None else sh["iota"] - iota_a),
            "abs_distance": (None if sh["iota"] is None
                             else abs(sh["iota"] - iota_a)),
            "qualified_gate2_5": q.get("passed"),
            "first_failing_component": q.get("first_failing_component"),
            "stability_passed": lr.get("stability_passed"),
            "v_r_passed": lr.get("v_r_passed"),
            "first_failing_full_v_r": lr.get("first_failing"),
            "spectrum_eligible_registered": lr.get(
                "spectrum_eligible_registered"),
            "spectrum_eligible_unfolded": lr.get(
                "spectrum_eligible_unfolded_diagnostic"),
            "signed_slot": slot_of.get(label),
            "corrected_slot": corrected_slot_of.get(label),
            "frozen_backup_family": fam in backups,
            "admitted_by_expansion": sh["severity"] in expanded.get(fam, []),
            "prescreen_solo": (None if pre is None else pre["solo"]),
            "prescreen_chance": (None if pre is None else pre["chance"]),
            "prescreen_iota": (None if pre is None else pre.get("iota")),
            "prescreen_vacuity": (None if pre is None else pre.get("vacuity")),
        }
        if lr:
            d_iota = (None if lr.get("iota") is None or sh["iota"] is None
                      else abs(lr["iota"] - sh["iota"]))
            if (d_iota is None and (lr.get("iota") is None) != (sh["iota"] is None)) \
                    or (d_iota is not None and d_iota > 1e-9) \
                    or bool(lr.get("eligible_12_6")) != bool(sh["eligible"]):
                join_mismatch.append({"candidate": label, "ours": sh["iota"],
                                      "landscape": lr.get("iota"),
                                      "elig_ours": sh["eligible"],
                                      "elig_land": lr.get("eligible_12_6")})
        rungs.append(entry)
        by_family.setdefault(fam, []).append(sh)

    # ---- per-family C4 states on four bases
    families: dict[str, dict[str, Any]] = {}
    for fam, entries in by_family.items():
        tier = FAMILIES[fam].structural_tier
        cal_elig = _family_state(entries, iota_a, eligible_only=True)
        cal_all = _family_state(entries, iota_a, eligible_only=False)
        # pre-screen on the same rungs, pre-screen eligibility, pre-screen iota_A
        pre_rows = []
        for e in entries:
            pre = pre_by.get(e["candidate"])
            if pre is None:
                continue
            shaped_pre = {"candidate": e["candidate"], "severity": e["severity"],
                          "iota": pre.get("iota"), "solo": pre["solo"],
                          "vacuity": pre.get("vacuity")}
            v = regime.coverage_eligibility(shaped_pre, formulation=formulation)
            shaped_pre["eligible"] = v["eligible"]
            pre_rows.append(shaped_pre)
        pre_same = (_family_state(pre_rows, iota_a_pre, eligible_only=True)
                    if pre_rows else None)
        # pre-screen certificate: every pre-screen rung of the family
        cert_rows = []
        for cand, pre in pre_by.items():
            if pre["family"] != fam:
                continue
            shaped_pre = {"candidate": cand, "severity": pre["severity"],
                          "iota": pre.get("iota"), "solo": pre["solo"],
                          "vacuity": pre.get("vacuity")}
            v = regime.coverage_eligibility(shaped_pre, formulation=formulation)
            shaped_pre["eligible"] = v["eligible"]
            cert_rows.append(shaped_pre)
        cert = (_family_state(cert_rows, iota_a_pre, eligible_only=True)
                if cert_rows else None)
        bucket, why = _bucket(cal_elig, cal_all, pre_same, len(entries), tier)
        inel = [(e["candidate"], e["eligibility"]["reason"]) for e in entries
                if not e["eligible"]]
        families[fam] = {
            "family": fam, "tier": tier,
            "feature_group": FAMILIES[fam].feature_group,
            "form": FAMILIES[fam].form,
            "n_measured": len(entries),
            "n_eligible": cal_elig["n_rungs"],
            "eligible_severities": cal_elig["severities"],
            "min_iota": cal_elig["min_iota"], "max_iota": cal_elig["max_iota"],
            "span": cal_elig["span"],
            "n_below": cal_elig["n_below"], "n_above": cal_elig["n_above"],
            "straddles": cal_elig["has_below"] and cal_elig["has_above"],
            "meets_rungs": cal_elig["n_rungs"]
            >= C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY,
            "meets_span": cal_elig["span"] >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN,
            "first_deficiency": cal_elig["deficiency"],
            "c4_group": cal_elig["met"],
            "all_measured": {k: cal_all[k] for k in
                             ("n_rungs", "has_below", "has_above", "span",
                              "min_iota", "max_iota", "deficiency", "met")},
            "prescreen_same_rungs": (None if pre_same is None else {
                k: pre_same[k] for k in ("n_rungs", "has_below", "has_above",
                                         "span", "min_iota", "max_iota",
                                         "deficiency", "met")}),
            "prescreen_certificate": (None if cert is None else {
                k: cert[k] for k in ("n_rungs", "has_below", "has_above",
                                     "span", "min_iota", "max_iota",
                                     "deficiency", "met", "severities")}),
            "certified_straddling_group": FAMILIES[fam].feature_group
            in certified_groups,
            "ineligible": inel,
            "bucket": bucket, "bucket_reason": why,
            "expansion_picks": expanded.get(fam, []),
        }

    # ---- local support vs spectrum support (Phase 4)
    elig = [r for r in rungs if r["eligible"] and r["iota"] is not None]
    elig12 = [r for r in elig if r["tier"] in (1, 2)]

    def _near(cal: float, rows: list[dict[str, Any]]) -> dict[str, Any]:
        sel = [r for r in rows if r["abs_distance"] <= cal + 1e-12]
        return {"rungs": len(sel),
                "families": len({r["family"] for r in sel}),
                "feature_groups": len({r["feature_group"] for r in sel}),
                "tier12_rungs": sum(1 for r in sel if r["tier"] in (1, 2)),
                "tier12_families": len({r["family"] for r in sel
                                        if r["tier"] in (1, 2)}),
                "full_v_r_rungs": sum(1 for r in sel if r["v_r_passed"]),
                "full_v_r_families": len({r["family"] for r in sel
                                          if r["v_r_passed"]}),
                "candidates": sorted(r["candidate"] for r in sel)}

    local = {f"{c:.2f}": _near(c, elig) for c in (0.05, 0.10, 0.15)}
    refs = {slot: {"candidate": f"{fam}:{sev}",
                   "iota": next((r["iota"] for r in rungs
                                 if r["candidate"] == f"{fam}:{sev}"), None)}
            for slot, (fam, sev) in slot_map.items()}
    for v in refs.values():
        v["distance"] = (None if v["iota"] is None else v["iota"] - iota_a)
    # spectrum support
    hist: dict[str, int] = {}
    hist12: dict[str, int] = {}
    hist_full: dict[str, int] = {}
    for lo, hi in zip(BINS, BINS[1:]):
        key = f"[{lo:+.1f},{hi:+.1f})"
        hist[key] = sum(1 for r in elig if lo <= r["distance"] < hi)
        hist12[key] = sum(1 for r in elig12 if lo <= r["distance"] < hi)
        hist_full[key] = sum(1 for r in elig12 if lo <= r["distance"] < hi
                             and r["v_r_passed"])
    n_cal = int(C.N_CALIBRATION)
    # the largest p_solo whose Wilson upper bound stays <= 0.90 at n = 192
    p_ceiling = max(p / 10000 for p in range(0, 10001)
                    if wilson(p / 10000, n_cal)[1] <= C.HEADROOM_BAND[1])
    spectrum = {
        "eligible_range_all": [min(r["iota"] for r in elig),
                               max(r["iota"] for r in elig)],
        "eligible_range_tier12": [min(r["iota"] for r in elig12),
                                  max(r["iota"] for r in elig12)],
        "eligible_range_tier12_full_v_r": (
            [min(r["iota"] for r in elig12 if r["v_r_passed"]),
             max(r["iota"] for r in elig12 if r["v_r_passed"])]
            if any(r["v_r_passed"] for r in elig12) else None),
        "n_eligible": len(elig), "n_eligible_tier12": len(elig12),
        "n_below": sum(1 for r in elig if r["side"] == "below"),
        "n_above": sum(1 for r in elig if r["side"] == "above"),
        "straddling_families": sorted(f for f, s in families.items()
                                      if s["straddles"]),
        "straddling_tier12_families": sorted(
            f for f, s in families.items() if s["straddles"]
            and s["tier"] in (1, 2)),
        "c4_groups": sorted(s["feature_group"] for s in families.values()
                            if s["c4_group"]),
        "n_c4_groups": sum(1 for s in families.values() if s["c4_group"]),
        "c4_required": C.COVERAGE_MIN_STRADDLING_FAMILIES,
        "coverage_by_bin_all": hist,
        "coverage_by_bin_tier12": hist12,
        "coverage_by_bin_tier12_full_v_r": hist_full,
        "v_head_p_solo_ceiling_at_192": p_ceiling,
        "iota_a_plus_0_20_reachable_under_v_head": (iota_a + C.SPECTRUM_OFFSET)
        <= p_ceiling,
        "iota_a_minus_0_20": iota_a - C.SPECTRUM_OFFSET,
        "iota_a_plus_0_20": iota_a + C.SPECTRUM_OFFSET,
        "registered_spectrum_pool": sorted(
            r["candidate"] for r in rungs if r["spectrum_eligible_registered"]),
        "registered_spectrum_pool_range": (
            [min(r["iota"] for r in rungs if r["spectrum_eligible_registered"]),
             max(r["iota"] for r in rungs if r["spectrum_eligible_registered"])]
            if any(r["spectrum_eligible_registered"] for r in rungs) else None),
        "unfolded_spectrum_pool_range": (
            [min(r["iota"] for r in rungs if r["spectrum_eligible_unfolded"]),
             max(r["iota"] for r in rungs if r["spectrum_eligible_unfolded"])]
            if any(r["spectrum_eligible_unfolded"] for r in rungs) else None),
    }
    return {
        "model": model, "iota_a": iota_a, "iota_a_prescreen": iota_a_pre,
        "iota_a_unconstrained_basis": (land or {}).get(
            "iota_a_unconstrained_basis"),
        "solo_a": g2["solo_compliance_a"], "n_star": g2["n_star"],
        "m_star": m_star, "formulation": formulation,
        "n_candidates": len(pooled),
        "n_unconstrained_rows": len(unconstrained),
        "coverage_conditions_corrected": cov["conditions"],
        "coverage_conditions_signed": signed_cov["conditions"],
        "coverage_conditions_certified": signed_cov["certified_conditions"],
        "coverage_realised_corrected": cov["realised"],
        "certified_straddling_groups": sorted(certified_groups),
        "expansion_rounds": len(expansion_rounds),
        "expansion_admitted": expanded,
        "signed_slot_map": slot_map, "frozen_backups": backups,
        "corrected_slot_map": land_slots,
        "join_mismatches": join_mismatch,
        "rungs": rungs, "families": families,
        "local_support": local, "selected_references": refs,
        "spectrum_support": spectrum,
    }


# ------------------------------------------------------------------ plots

def _plots(res: dict[str, Any], out: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    written = []
    model, iota_a = res["model"], res["iota_a"]
    rungs = res["rungs"]
    fam_order = sorted({r["family"] for r in rungs},
                       key=lambda f: (FAMILIES[f].structural_tier,
                                      list(FAMILIES).index(f)))
    tier_colour = {1: "#1f77b4", 2: "#2ca02c", 3: "#7f7f7f"}

    # ---- Plot A: landscape
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(fam_order) + 2.2))
    ypos = {f: i for i, f in enumerate(fam_order)}
    for r in rungs:
        if r["iota"] is None:
            continue
        y = ypos[r["family"]]
        col = tier_colour[r["tier"]]
        if r["eligible"] and r["v_r_passed"]:
            ax.plot(r["iota"], y, "o", color=col, ms=6, zorder=3)
        elif r["eligible"]:
            ax.plot(r["iota"], y, "o", color=col, ms=6, alpha=0.35, zorder=3)
        else:
            ax.plot(r["iota"], y, "o", mfc="none", mec=col, ms=5, alpha=0.6,
                    zorder=2)
        ax.annotate(str(r["severity"]), (r["iota"], y), fontsize=5.5,
                    xytext=(0, 4), textcoords="offset points", ha="center",
                    color=col)
        if r["signed_slot"]:
            ax.plot(r["iota"], y, "*", color="crimson", ms=13, zorder=4,
                    mec="black", mew=0.4)
            ax.annotate(r["signed_slot"], (r["iota"], y), fontsize=7,
                        xytext=(0, -10), textcoords="offset points",
                        ha="center", color="crimson")
    for f in res["frozen_backups"]:
        if f in ypos:
            ax.annotate("frozen backup", (-0.12, ypos[f]), fontsize=6.5,
                        color="darkorange", va="center")
    ax.axvline(iota_a, color="black", lw=1.2)
    ax.axvspan(iota_a - 0.10, iota_a + 0.10, color="gold", alpha=0.12,
               label="§13.8 caliper ±0.10")
    ax.axvspan(iota_a - 0.15, iota_a + 0.15, color="gold", alpha=0.07)
    ax.axvline(iota_a - 0.20, color="purple", ls=":", lw=0.8)
    ax.axvline(iota_a + 0.20, color="purple", ls=":", lw=0.8,
               label="§13.12 targets ι_A ± 0.20")
    ceil = res["spectrum_support"]["v_head_p_solo_ceiling_at_192"]
    ax.axvline(ceil, color="red", ls="--", lw=0.8,
               label=f"V_head ceiling (Wilson upper ≤ 0.90): p ≤ {ceil:.3f}")
    ax.axvline(0.10, color="red", ls="--", lw=0.8)
    ax.set_yticks(range(len(fam_order)))
    ax.set_yticklabels([f"{f} (T{FAMILIES[f].structural_tier}, "
                        f"{FAMILIES[f].feature_group})" for f in fam_order],
                       fontsize=7)
    ax.set_xlim(-0.15, 1.05)
    ax.set_xlabel("ι(R) on the corrected chance basis (192 calibration topics × 4 draws)")
    ax.set_title(f"Plot A — reference landscape, v7 {model}: ι_A = {iota_a:.3f} "
                 f"(n* = {res['n_star']}, m* = {res['m_star']}); filled = eligible & full V(R), "
                 "faded = eligible only, hollow = ineligible, ★ = signed slot",
                 fontsize=8.5)
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, -0.06), ncol=3, frameon=False)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    p = out / f"plotA_landscape_{model}.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    written.append(str(p))

    # ---- Plot B: ladders (Tier 1 + Tier 2 + the Tier-3 families with >= 3 rungs)
    fams = [f for f in fam_order if FAMILIES[f].structural_tier in (1, 2)
            or len(res["families"][f]["eligible_severities"]) + len(
                res["families"][f]["ineligible"]) >= 3]
    ncol = 4
    nrow = math.ceil(len(fams) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 2.6 * nrow),
                             sharey=True)
    axes = axes.flatten()
    for ax, f in zip(axes, fams):
        rows = sorted((r for r in rungs if r["family"] == f),
                      key=lambda r: r["severity"])
        xs = [r["severity"] for r in rows]
        ys = [r["iota"] if r["iota"] is not None else float("nan") for r in rows]
        ax.plot(xs, ys, "-", color="lightgray", zorder=1)
        for r in rows:
            if r["iota"] is None:
                continue
            col = tier_colour[r["tier"]]
            if r["eligible"]:
                ax.plot(r["severity"], r["iota"], "o", color=col, ms=5,
                        zorder=3)
            else:
                ax.plot(r["severity"], r["iota"], "o", mfc="none", mec=col,
                        ms=5, zorder=3)
            if r["signed_slot"]:
                ax.plot(r["severity"], r["iota"], "*", color="crimson",
                        ms=11, zorder=4)
            if r["admitted_by_expansion"]:
                ax.plot(r["severity"], r["iota"], "s", mfc="none",
                        mec="darkorange", ms=9, zorder=2)
        ax.axhline(iota_a, color="black", lw=1)
        ax.axhspan(iota_a - 0.10, iota_a + 0.10, color="gold", alpha=0.12)
        ax.axhline(0.90, color="red", ls="--", lw=0.6)
        ax.axhline(0.10, color="red", ls="--", lw=0.6)
        st = res["families"][f]
        ax.set_title(f"{f} {FAMILIES[f].feature_group} T{st['tier']}: "
                     f"elig span {st['span']:.2f} "
                     f"({st['n_below']}↓/{st['n_above']}↑) "
                     f"{st['first_deficiency'] or 'C4 met'} [{st['bucket']}]",
                     fontsize=7)
        ax.set_xlabel("severity q", fontsize=7)
        ax.tick_params(labelsize=7)
        ax.set_ylim(-0.1, 1.05)
    for ax in axes[len(fams):]:
        ax.axis("off")
    fig.suptitle(f"Plot B — family difficulty ladders, v7 {model}: corrected ι "
                 f"vs severity; ι_A = {iota_a:.3f}; filled = §12.6-eligible, "
                 "hollow = ineligible, ★ = signed slot, □ = expansion rung",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    p = out / f"plotB_ladders_{model}.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(str(p))
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--landscape", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "plots").mkdir(exist_ok=True)
    landscape = _load(pathlib.Path(a.landscape))
    results = []
    for m in a.models:
        res = analyse(m, pathlib.Path(a.tree), landscape)
        res["plots"] = _plots(res, out / "plots")
        results.append(res)
        print(f"{m}: iota_A={res['iota_a']:.4f} C4 groups="
              f"{res['spectrum_support']['n_c4_groups']}/6 "
              f"conditions={res['coverage_conditions_corrected']} "
              f"join_mismatches={len(res['join_mismatches'])}")
    with open(out / "spectrum_dev.json", "w") as f:
        json.dump({"read_only": True, "development": True,
                   "chance_basis": "§13.2 kappa_c on the grid runs' unconstrained "
                                   "cells (2026-08-29 correction)",
                   "results": results}, f, indent=1, sort_keys=True)
    cols = ["model", "family", "tier", "feature_group", "form", "severity",
            "solo", "chance_corrected", "iota", "lift", "vacuity",
            "kappa_under_b", "median_words", "eligible",
            "ineligibility_reason", "side", "distance",
            "qualified_gate2_5", "first_failing_component",
            "stability_passed", "v_r_passed", "first_failing_full_v_r",
            "spectrum_eligible_registered", "spectrum_eligible_unfolded",
            "signed_slot", "corrected_slot", "frozen_backup_family",
            "admitted_by_expansion", "prescreen_solo", "prescreen_chance",
            "prescreen_iota", "prescreen_vacuity"]
    with open(out / "rung_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for res in results:
            for r in res["rungs"]:
                w.writerow(r)
    fcols = ["model", "family", "tier", "feature_group", "form", "n_measured",
             "n_eligible", "min_iota", "max_iota", "span", "n_below",
             "n_above", "straddles", "meets_rungs", "meets_span",
             "first_deficiency", "c4_group", "all_measured_span",
             "all_measured_straddles", "prescreen_same_span",
             "prescreen_certificate_span", "certified_straddling_group",
             "bucket", "bucket_reason", "expansion_picks"]
    with open(out / "family_c4_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fcols)
        w.writeheader()
        for res in results:
            for fam, s in res["families"].items():
                w.writerow({
                    "model": res["model"], **{k: s[k] for k in fcols
                                              if k in s},
                    "all_measured_span": s["all_measured"]["span"],
                    "all_measured_straddles": s["all_measured"]["has_below"]
                    and s["all_measured"]["has_above"],
                    "prescreen_same_span": (None if s["prescreen_same_rungs"]
                                            is None else
                                            s["prescreen_same_rungs"]["span"]),
                    "prescreen_certificate_span": (
                        None if s["prescreen_certificate"] is None
                        else s["prescreen_certificate"]["span"]),
                })
    print("written:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
