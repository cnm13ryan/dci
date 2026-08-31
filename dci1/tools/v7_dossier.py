#!/usr/bin/env python3
"""Build the v7 visualisation/results dossier from the signed records.

Reads only signed stage records under ``dci1/evidence/dci1v7*`` and writes
machine-readable tables under ``dci1/reports/dci1v7/dossier/``. It computes no
new estimate: every number is either copied from a record or, for the
block-level tables, reconstructed from the masked rows and the mask key and
**checked against the record it must reproduce** (``--verify`` is on by
default and a mismatch is fatal).

The registered v7 study produced no confirmatory data. Everything here comes
from the six completed development-rehearsal lanes in the structurally
separate ``dci1v7-development`` namespace, which the protocol's own guards
refuse to admit as study evidence (``engine/guards.py``). Every row carries
``evidence_status`` saying so.

Usage:
    python dci1/tools/v7_dossier.py [--out DIR] [--no-blocks]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "dci1" / "evidence"
DEFAULT_OUT = REPO / "dci1" / "reports" / "dci1v7" / "dossier"

#: (root, model, role). ``canonical`` is the lane a per-model number should be
#: quoted from; ``repeat`` lanes are the same model re-run on a later commit
#: and exist as reproducibility evidence, never as a second replication.
LANES: tuple[tuple[str, str, str], ...] = (
    ("dci1v7-development",    "qwen3-4b",               "repeat"),
    ("dci1v7-development-r3", "qwen3-4b",               "canonical"),
    ("dci1v7-development-r3", "gemma-3n-e2b-it",        "repeat"),
    ("dci1v7-development-r4", "qwen3-4b-instruct-2507", "canonical"),
    ("dci1v7-development-r4", "gemma-3n-e4b-it",        "canonical"),
    ("dci1v7-development-r5", "gemma-3n-e2b-it",        "canonical"),
)

#: Registered decision thresholds, by member (constants.py:390-407).
THRESHOLDS: dict[str, str] = {
    "Delta_R": "L3a 0.10 lower; L3b 0.25 lower; L3c 0.10 upper; direction at 0",
    "Delta_near": "direction at 0; generic 0.10",
    "Delta_broad": "direction at 0 only (one companion bounds, never estimates, a class effect)",
    "delta_difficulty": "direction at 0; equivalence +/-0.10",
    "Xi": "direction at 0 only",
    "D(B<-A)": "direction at 0; SESOI 0.10",
    "D(A<-B)": "direction at 0; SESOI 0.10",
    "Lambda": "direction at 0; SESOI 0.10",
    "Ord_A": "direction at 0; equivalence +/-0.10",
    "Ord_B": "direction at 0; equivalence +/-0.10",
    "Ord_Lambda": "direction at 0; equivalence +/-0.10",
    "Ord_Rbar": "direction at 0; equivalence +/-0.10",
    "Ord_CL": "direction at 0; equivalence +/-0.10",
}
PRECISION = {"D": 0.05, "Delta_R": 0.05, "Delta_near": 0.05,
             "delta_difficulty": 0.05, "Lambda": 0.08, "Delta_j": 0.06,
             "Ord_A": 0.05, "Ord_B": 0.05, "Ord_Lambda": 0.08}

PRIMARY_TIER = {"F1", "F11"}


def lane_dir(root: str, model: str) -> Path:
    return EVIDENCE / root / "evidence" / "dci1v7" / model


def load(root: str, model: str, stage: str, name: str):
    p = lane_dir(root, model) / stage / name
    with p.open() as fh:
        return json.load(fh), str(p.relative_to(REPO))


def precision_key(member: str) -> str:
    stem = member.split("|", 1)[0]
    if stem.startswith("Ord_"):
        return stem
    if stem in ("Delta_R", "Delta_near", "delta_difficulty", "Lambda"):
        return stem
    if stem.startswith("Delta_") and stem[6:].isdigit():
        return "Delta_j"
    if stem.startswith("D("):
        return "D"
    return stem


def evidence_status(row: dict) -> str:
    """The ladder the paper must keep separate."""
    if row["status"] != "IDENTIFIED":
        return "NOT_IDENTIFIED_never_a_null"
    fam = row.get("family") or ""
    member = row["member"]
    if "|vacuity_forced" in member or "|graded_0.99" in member:
        return "DEV_REHEARSAL_robustness"
    if fam == "F6":
        return "DEV_REHEARSAL_degeneracy_gate"
    if fam in PRIMARY_TIER:
        return "DEV_REHEARSAL_primary"
    return "DEV_REHEARSAL_secondary"


def w(out: Path, name: str, rows: list[dict], fields: list[str]) -> None:
    if not rows:
        return
    with (out / name).open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    print(f"  {name:38s} {len(rows):6d} rows")


# --------------------------------------------------------------- extraction
def build() -> dict:
    lanes, master, cells, refs, cand, cov = [], [], [], [], [], []
    curves, opp, robust, vac, proj, stmts, stability = [], [], [], [], [], [], []
    compression: dict[tuple, dict] = {}

    for root, model, role in LANES:
        fr, fr_path = load(root, model, "FINAL_REPORT", "final_report.json")
        ua, ua_path = load(root, model, "UNMASKED_ANALYSIS", "unmasked_result.json")
        g2, g2_path = load(root, model, "GATE_2_FOCAL_CALIBRATION",
                           "gate2_focal_calibration.json")
        g3a, g3a_path = load(root, model, "GATE_3A_REFERENCE_CALIBRATION",
                             "gate3a_reference_calibration.json")
        g3b, g3b_path = load(root, model, "GATE_3B_REFERENCE_SELECTION",
                             "gate3b_reference_selection.json")
        g3c, g3c_path = load(root, model, "GATE_3C_IDENTIFICATION",
                             "gate3c_identification.json")
        lane_id = f"{root}/{model}"

        lanes.append({
            "lane_id": lane_id, "root": root, "model": model, "lane_role": role,
            "namespace": "development", "study_id": fr["study_id"],
            "n_star": g2["n_star"], "m_star": g2["m_star"],
            "iota_a_calibration": g3a["iota_a"],
            "solo_compliance_a_calibration": g3a["solo_compliance_a"],
            "solo_compliance_b_calibration": g2["solo_compliance_b"],
            "admitted_arms": ";".join(fr["admitted_arms"]),
            "cells_per_block": fr["results"][0]["cell_counts"]["cells_per_block"],
            "n_blocks": fr["results"][0]["cell_counts"]["blocks"],
            "draws_per_cell": fr["results"][0]["cell_counts"]["draws_per_cell"],
            "confirmatory_rows": fr["results"][0]["cell_counts"]["rows"],
            "identification_statuses": ";".join(fr["identification_statuses"]),
            "support_disposition": g3c["support_disposition"],
            "success_criterion_verdict": fr["methodological_success_criterion"]["verdict"],
            "n_final_report_checks_passed": fr["n_final_report_passed"],
            "n_final_report_checks": fr["n_final_report_checks"],
            "n_statements": len(fr["statements"]),
            "producing_commit": fr["producing_commit"],
            "freeze_hash": fr["results"][0]["freeze_hash"],
            "verifier_hash": fr["verifier_hash"],
            "measurement_basis": fr["measurement_basis"],
            "recorded_at": fr["recorded_at"],
            "source_final_report": fr_path,
            "evidence_status": "DEVELOPMENT_REHEARSAL_not_a_v7_replication",
        })

        # ---- master estimand table, straight from FINAL_REPORT.results
        for r in fr["results"]:
            member = r["member"]
            row = {
                "lane_id": lane_id, "model": model, "lane_role": role,
                "configuration": r["configuration"],
                "outcome_position": ("first" if r["configuration"] == "outcome_first"
                                     else "second" if r["configuration"] == "outcome_second"
                                     else "cross"),
                "member": member, "family": r["family"], "cell": r["cell"],
                "claim_level": r["claim_level"],
                "point_estimate": r["point"],
                "estimate": r["estimate"],
                "simultaneous_lower": r["simultaneous_lower"],
                "simultaneous_upper": r["simultaneous_upper"],
                "marginal_lower": r["marginal_lower"],
                "marginal_upper": r["marginal_upper"],
                "standard_error": r["standard_error"],
                "realised_half_width": r["realised_half_width"],
                "precision_precondition": PRECISION.get(precision_key(member)),
                "precision_met": (r["achieved_detectable_effect"] or {}).get("met"),
                "threshold": THRESHOLDS.get(member.split("|", 1)[0], "no registered magnitude threshold"),
                "n_blocks": r["cell_counts"]["blocks"],
                "status": r["status"],
                "identification_status": r["identification_status"],
                "family_tier": "primary" if r["family"] in PRIMARY_TIER else "secondary",
                "source_artifact": fr_path,
                "source_stage": r["source_stage"],
                "stage_record_hash": r["stage_record_hash"],
            }
            row["evidence_status"] = evidence_status(row)
            master.append(row)
            if "|vacuity_forced" in member or "|graded_0.99" in member:
                robust.append(row)
            if r["family"] == "F6":
                vac.append(row)

        # ---- decision intervals + constituent cell levels from the boundary read
        for key, members in ua["estimands"]["intervals"].items():
            fam, cfg = key.split(":", 1)
            if members.get("status") == "NOT_IDENTIFIED":
                # whole family unavailable: §15's simultaneous interval is not
                # defined for it. Recorded, never rendered as a null.
                continue
            for member, e in members.items():
                if not isinstance(e, dict):
                    continue
                b = e.get("boundary")
                if b:
                    comp = b.get("compression") or {}
                    if comp.get("two_arm"):
                        lo_a, hi_a = comp["attainable_given_negative_arm"]
                        lo_b, hi_b = comp["attainable_given_positive_arm"]
                        compression[(lane_id, member, cfg)] = {
                            "positive_direction_compressed": comp["positive_direction_compressed"],
                            "negative_direction_compressed": comp["negative_direction_compressed"],
                            "compressed_by": ";".join(
                                f"{c['arm']}:{c['direction']}:{c['bound']}"
                                for c in comp.get("compressed_by", [])),
                            "negative_arm": comp["negative_arm"],
                            "positive_arm": comp["positive_arm"],
                            "attainable_min": max(lo_a, lo_b),
                            "attainable_max": min(hi_a, hi_b),
                        }
                    for c in b["constituents"]:
                        cells.append({
                            "lane_id": lane_id, "model": model, "lane_role": role,
                            "family": fam, "configuration": cfg, "member": member,
                            "cell": c["cell"], "outcome_slot": c["outcome"],
                            "companion_slot": c["companion"], "role": c["role"],
                            "weight": c["weight"], "compliance_rate": c["level"],
                            "n_blocks": c["n_blocks"],
                            "exact_boundary": c["exact_boundary"],
                            "near_boundary": c["near_boundary"],
                            "structural_zero": b["structural_zero"],
                            "positive_arm_level": comp.get("positive_arm"),
                            "negative_arm_level": comp.get("negative_arm"),
                            "positive_direction_compressed": comp.get("positive_direction_compressed"),
                            "negative_direction_compressed": comp.get("negative_direction_compressed"),
                            "source_artifact": ua_path,
                            "evidence_status": "DEV_REHEARSAL_cell_level_input",
                        })
                # decision interval onto the master row
                for m2 in master:
                    if (m2["lane_id"] == lane_id and m2["member"] == member
                            and m2["family"] == fam
                            and (m2["configuration"] or "cross") == cfg):
                        m2["decision_lower"] = e.get("decision_lower")
                        m2["decision_upper"] = e.get("decision_upper")
                        m2["boundary_statuses"] = ";".join(e.get("boundary_statuses") or [])
                        m2["degenerate"] = e.get("degenerate")

        # ---- selected references and their matching quantities
        sel = g3b["selection"]
        stab = g3a.get("stability") or {}
        for entry in sel["core"]["core_references"] + (
                [sel["broad_class"]["companion"]] if sel["broad_class"].get("available") else []):
            label = f"{entry['family']}:{entry['severity']}"
            st = stab.get(label) or {}
            row_pool = next((r for r in g3a["pooled_table"]
                             if r["kind"] == entry["family"]
                             and r["severity"] == entry["severity"]), {})
            refs.append({
                "lane_id": lane_id, "model": model, "lane_role": role,
                "slot": entry["slot"], "family": entry["family"],
                "severity": entry["severity"], "instance": label,
                "structural_tier": entry["structural_tier"],
                "feature_group": entry.get("feature_group"),
                "discourse_role": entry.get("discourse_role"),
                "constraint_class": entry.get("constraint_class",
                                              "production" if entry["structural_tier"] < 3 else "budget"),
                "iota_reference": entry["iota"],
                "iota_a": g3b["iota_a"],
                "abs_iota_distance": entry["distance"],
                "caliper": 0.10,
                "solo_compliance": row_pool.get("solo_compliance"),
                "solo_compliance_a": g3b["solo_compliance_a"],
                "chance_compliance_recorded": row_pool.get("chance_compliance"),
                "kappa_under_b": row_pool.get("kappa_under_b"),
                "solo_vacuity": row_pool.get("solo_vacuity"),
                "median_words": row_pool.get("median_words"),
                "stability_passed": st.get("passed"),
                "iota_split_diff_point": (st.get("iota_split_difference") or {}).get("point"),
                "iota_split_diff_lower": (st.get("iota_split_difference") or {}).get("lower"),
                "iota_split_diff_upper": (st.get("iota_split_difference") or {}).get("upper"),
                "stability_equivalence_bound": st.get("equivalence_bound"),
                "prescreen_solo_compliance": row_pool.get("prescreen_solo_compliance"),
                "prescreen_chance_compliance": row_pool.get("prescreen_chance_compliance"),
                "source_artifact": g3b_path,
                "evidence_status": "DEV_REHEARSAL_selection_input_prospective",
            })

        # ---- every candidate's earliest failing validity component
        for arm_name in ("core", "near_form", "broad_class"):
            arm = sel.get(arm_name) or {}
            for fv in arm.get("family_verdicts", []):
                for rung in fv.get("rungs", []):
                    comps = rung.get("components", [])
                    failed = next((c for c in comps if c["evaluated"] and not c["passed"]), None)
                    head = next((c for c in comps if c["component"] == "V_head"), None)
                    chance = next((c for c in comps if c["component"] == "V_chance"), None)
                    inter = next((c for c in comps if c["component"] == "V_inter"), None)
                    cand.append({
                        "lane_id": lane_id, "model": model, "lane_role": role,
                        "arm": arm_name, "family": fv["family"],
                        "feature_group": fv.get("feature_group"),
                        "discourse_role": fv.get("discourse_role"),
                        "candidate": rung["candidate"],
                        "family_admitted": fv.get("admitted"),
                        "iota": fv.get("iota"), "distance": fv.get("distance"),
                        "earliest_failing_component": failed["component"] if failed else None,
                        "failure_reason": failed["reason"] if failed else None,
                        "solo_compliance": (head or {}).get("values", {}).get("solo_compliance"),
                        "solo_wilson_lower": (head or {}).get("values", {}).get("wilson_lower"),
                        "solo_wilson_upper": (head or {}).get("values", {}).get("wilson_upper"),
                        "instruction_lift": (head or {}).get("values", {}).get("instruction_lift"),
                        "solo_vacuity": (head or {}).get("values", {}).get("solo_vacuity"),
                        "chance_compliance": (chance or {}).get("values", {}).get("chance_compliance"),
                        "kappa_under_b": (inter or {}).get("values", {}).get("kappa_under_b"),
                        "projected_compliance": (inter or {}).get("values", {}).get("projected_compliance"),
                        "displacement": (inter or {}).get("values", {}).get("displacement"),
                        "source_artifact": g3b_path,
                        "evidence_status": "DEV_REHEARSAL_selection_diagnostic",
                    })

        # ---- coverage C1-C8 on both bases
        cvg = g3a["coverage_at_calibrated_iota_a"]
        for cond in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
            cov.append({
                "lane_id": lane_id, "model": model, "lane_role": role,
                "condition": cond,
                "gates_arm": ("core" if cond in cvg["core_conditions"]
                              else "spectrum" if cond in ("C2", "C4")
                              else "class" if cond == "C7" else "nearform"),
                "met_on_prescreen_basis": cvg["certified_conditions"][cond],
                "met_on_calibration_basis": cvg["conditions"][cond],
                "moved_by_basis": cond in cvg["conditions_moved_by_the_basis"],
                "iota_a_prescreen": cvg["iota_a_prescreen"],
                "iota_a_calibrated": cvg["iota_a_measured"],
                "iota_a_movement": cvg["iota_a_movement"],
                "n_eligible": cvg["n_eligible"],
                "straddling_groups": ";".join(cvg["realised"].get("straddling_groups") or []),
                "n_straddling_groups": len(cvg["realised"].get("straddling_groups") or []),
                "source_artifact": g3a_path,
                "evidence_status": "DEV_REHEARSAL_design_time_coverage",
            })

        # ---- calibration curves for n* and m*
        for kind, band, aim, sel_key in (("A", (0.50, 0.85), 0.70, "target_selection"),
                                         ("B", (0.60, 0.95), 0.80, "focal_selection")):
            s = g2[sel_key]
            for sev, val in sorted(g2["solo_curves"][kind].items(), key=lambda kv: int(kv[0])):
                q = int(sev)
                curves.append({
                    "lane_id": lane_id, "model": model, "lane_role": role,
                    "constraint": kind, "severity": q,
                    "solo_compliance": val,
                    "chance_compliance": g2["chance_curves"][kind].get(sev),
                    "load_zero_chance_compliance": g2["load_zero_chance_curves"][kind].get(sev),
                    # Availability, not a value, and named for what it is.
                    # kappa(R|B) is per *candidate* --- the record nests it
                    # severity -> split -> candidate --- so this row, which is
                    # one (constraint, severity) of a curve, has no single
                    # kappa to carry. The numbers are in
                    # reference_candidates.csv, one per candidate.
                    "kappa_under_b_measured":
                        (g2["kappa_under_b_by_severity"].get(sev) is not None
                         if kind == "B" else None),
                    "band_lower": band[0], "band_upper": band[1], "aim": aim,
                    "eligible": q in s["eligible"],
                    "selected": q == s["selected"],
                    "n_topics": 192, "draws_per_cell": 4,
                    "at_grid_top": s["at_grid_top"], "bracketed": s["bracketed"],
                    "selection_status": ";".join(s["identification_statuses"]),
                    "source_artifact": g2_path,
                    "evidence_status": "DEV_REHEARSAL_calibration_prospective",
                })
        cs = g2.get("construct_strength") or {}
        opp.append({
            "lane_id": lane_id, "model": model, "lane_role": role,
            "n_star": g2["n_star"], "m_star": g2["m_star"],
            "solo_compliance_a": g2["solo_compliance_a"],
            "solo_compliance_b": g2["solo_compliance_b"],
            "iota_a": g2["iota_a"],
            "n_star_bracketed": g2["target_selection"]["bracketed"],
            "m_star_bracketed": g2["focal_selection"]["bracketed"],
            "focal_extension_measured": g2["focal_extension_measured"],
            "focal_admissible": ";".join(str(x) for x in g2["focal_admissible"]),
            "construct_floor_quantity": cs.get("floor", {}).get("quantity") if isinstance(cs.get("floor"), dict) else None,
            "construct_floor_value": cs.get("floor", {}).get("value") if isinstance(cs.get("floor"), dict) else None,
            "identification_statuses": ";".join(g2["identification_statuses"]),
            "source_artifact": g2_path,
            "evidence_status": "DEV_REHEARSAL_calibration_prospective",
        })

        # ---- iota_A stability across the two calibration splits
        ias = g3a.get("iota_a_stability") or {}
        stability.append({
            "lane_id": lane_id, "model": model, "lane_role": role,
            "quantity": "iota_A", "passed": ias.get("passed"),
            "point": (ias.get("iota_split_difference") or ias.get("difference") or {}).get("point"),
            "lower": (ias.get("iota_split_difference") or ias.get("difference") or {}).get("lower"),
            "upper": (ias.get("iota_split_difference") or ias.get("difference") or {}).get("upper"),
            "equivalence_bound": g3a.get("equivalence_bound"),
            "n_qualified": g3a.get("n_qualified"), "n_stable": g3a.get("n_stable"),
            "source_artifact": g3a_path,
            "evidence_status": "DEV_REHEARSAL_selection_diagnostic",
        })

        # ---- projection audit (post-hoc; licenses nothing)
        for p in ua["projection_audit"]:
            proj.append({
                "lane_id": lane_id, "model": model, "lane_role": role,
                "cell": p["cell"], "companion": p["companion"],
                "configuration": p["configuration"],
                "projected_mean": p["projected_mean"],
                "realised_mean": p["realised_mean"],
                "absolute_error_mean": p["absolute_error_mean"],
                "absolute_error_median": p["absolute_error_median"],
                "absolute_error_max": p["absolute_error_max"],
                "displacement_mean": p["displacement_mean"],
                "allowance": p["allowance"],
                "within_allowance": p["within_allowance"],
                "n_blocks": p["n_blocks"],
                "n_blocks_degenerate": p.get("n_blocks_degenerate"),
                "degenerate_reading": p.get("degenerate_reading"),
                "status": p.get("status"),
                "source_artifact": ua_path,
                "evidence_status": "POST_HOC_diagnostic_licenses_nothing",
            })

        # ---- emitted statements
        for s in ua["statements"]:
            stmts.append({
                "lane_id": lane_id, "model": model, "lane_role": role,
                "claim_level": s["claim_level"],
                "member": s.get("member"),
                "configuration": s.get("configuration"),
                "cell": s.get("cell"),
                "emitted": s.get("emitted"),
                "estimate": s.get("estimate"),
                "interval_lower": (s.get("interval") or [None, None])[0],
                "interval_upper": (s.get("interval") or [None, None])[1],
                "interval_type": s.get("interval_type"),
                "half_width": s.get("half_width"),
                "direction": s.get("direction"),
                "reason": s.get("reason"),
                "identification_status": ";".join(s.get("identification_status") or []),
                "source_artifact": ua_path,
                "evidence_status": "DEV_REHEARSAL_emitted_claim",
            })

    return {"lanes": lanes, "master": master, "cells": cells, "refs": refs,
            "candidates": cand, "coverage": cov, "curves": curves,
            "operating_points": opp, "robustness": robust, "vacuity": vac,
            "projection": proj, "statements": stmts, "stability": stability,
            "compression": compression}


# ------------------------------------------------------------- block level
def block_tables(out: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Per-block cell means and per-block contrast values, unmasked.

    Verified against the signed UNMASKED_ANALYSIS point estimates; a
    disagreement above 1e-12 aborts.
    """
    cell_rows: list[dict] = []
    contrast_rows: list[dict] = []
    difficulty_rows: list[dict] = []
    for root, model, role in LANES:
        d = lane_dir(root, model)
        key = json.loads((d / "masking" / "confirmatory_mask" / "mask_key.json").read_text())
        inv = {}
        for k, masked in key["mapping"].items():
            o, c, blk, true = k.split("|")
            inv[(o, c, blk, masked)] = true
        cells: dict[tuple, dict[str, float]] = defaultdict(dict)
        extra: dict[tuple, dict[str, dict]] = defaultdict(dict)
        with (d / "masking" / "confirmatory_mask" / "masked_rows.jsonl").open() as fh:
            for line in fh:
                r = json.loads(line)
                if not r["present"]:
                    continue
                o, cfg, blk = r["outcome_slot"], r["configuration"], r["block_id"]
                comp = r["companion_label"]
                if comp is not None:
                    comp = inv[(o, cfg, blk, comp)]
                cells[(o, comp, cfg)][blk] = r["compliance"]
                extra[(o, comp, cfg)][blk] = r
        blocks = sorted(cells[("B", None, None)])
        lane_id = f"{root}/{model}"
        for (o, comp, cfg), per_block in sorted(cells.items(), key=lambda kv: str(kv[0])):
            for blk in blocks:
                if blk not in per_block:
                    continue
                r = extra[(o, comp, cfg)][blk]
                cell_rows.append({
                    "lane_id": lane_id, "model": model, "lane_role": role,
                    "block_id": blk, "outcome_slot": o,
                    "companion_slot": comp or "",
                    "configuration": cfg or "",
                    "arm": r["arm"], "position": r["position"],
                    "compliance": per_block[blk], "graded": r["graded"],
                    "graded_threshold": r["graded_threshold"],
                    "non_vacuous_compliance": r["non_vacuous_compliance"],
                    "vacuity": r["vacuity"], "truncation": r["truncation"],
                    "response_words": r["response_words"], "draws": r["draws"],
                })
        # ---- POST-HOC: the difficulty coordinate recomputed on the
        # confirmatory unconstrained cells. §13.2 defines kappa_c there; the
        # §13.11 calibration table recorded 0.0 for every candidate
        # (CHANGES_SCIENTIFIC.md 2026-08-29, finding not in force), so this is
        # the only place the realised coordinate can be read. It licenses
        # nothing and revises no admission (§13.14: Gate 4 and later may not
        # replace a companion).
        unconstrained: dict[str, list[float]] = defaultdict(list)
        solo_only: dict[str, list[float]] = defaultdict(list)
        with (d / "masking" / "confirmatory_mask" / "masked_rows.jsonl").open() as fh:
            for line in fh:
                r = json.loads(line)
                if r["arm"] == "unconstrained":
                    unconstrained[r["outcome_slot"]].append(r["compliance"])
                elif r["arm"] == "solo" and r["present"]:
                    solo_only[r["outcome_slot"]].append(r["compliance"])
        g3b = json.loads((d / "GATE_3B_REFERENCE_SELECTION"
                          / "gate3b_reference_selection.json").read_text())
        g3a = json.loads((d / "GATE_3A_REFERENCE_CALIBRATION"
                          / "gate3a_reference_calibration.json").read_text())
        slot_map = {k: f"{v[0]}:{v[1]}" for k, v in g3b["slot_map"].items()}
        pooled = {f"{r['kind']}:{r['severity']}": r for r in g3a["pooled_table"]}

        def _m(v):
            return sum(v) / len(v)

        k_a, p_a = _m(unconstrained["A"]), _m(solo_only["A"])
        iota_a_conf = (p_a - k_a) / (1 - k_a)
        for slot in ("A", "R1", "R2", "R3", "CL"):
            if slot not in solo_only:
                continue
            k, p = _m(unconstrained[slot]), _m(solo_only[slot])
            iota = (p - k) / (1 - k) if k < 1 else None
            cal = pooled.get(slot_map.get(slot, ""), {})
            difficulty_rows.append({
                "lane_id": lane_id, "model": model, "lane_role": role,
                "slot": slot, "instance": slot_map.get(slot, "A:n*"),
                "kappa_confirmatory_unconstrained": k,
                "solo_confirmatory": p,
                "instruction_lift_confirmatory": p - k,
                "iota_confirmatory": iota,
                "iota_A_confirmatory": iota_a_conf,
                "abs_iota_gap_confirmatory": (None if iota is None
                                              else abs(iota - iota_a_conf)),
                "realised_gap_qualifier": 0.15,
                "exceeds_realised_gap_qualifier": (
                    None if iota is None else abs(iota - iota_a_conf) > 0.15),
                "class_match_caliper": 0.15,
                "kappa_recorded_at_calibration": cal.get("chance_compliance"),
                "solo_recorded_at_calibration": cal.get("solo_compliance"),
                "iota_used_for_admission": cal.get("solo_compliance"),
                "kappa_column_defect": (
                    "the §13.11 calibration table recorded chance_compliance "
                    "= 0.0 for every candidate on every v5/v6/v7 replication "
                    "(CHANGES_SCIENTIFIC.md 2026-08-29); admission therefore "
                    "used raw solo compliance as iota(R)"),
                "source_artifact": str(
                    (d / "masking" / "confirmatory_mask" / "masked_rows.jsonl")
                    .relative_to(REPO)),
                "evidence_status": "POST_HOC_diagnostic_licenses_nothing",
            })

        solo_b, solo_a = cells[("B", None, None)], cells[("A", None, None)]
        has_cl = ("B", "CL", "outcome_first") in cells
        for cfg in ("outcome_first", "outcome_second"):
            ba, ab = cells[("B", "A", cfg)], cells[("A", "B", cfg)]
            rj = [cells[("B", f"R{i}", cfg)] for i in (1, 2, 3)]
            for blk in blocks:
                rbar = sum(x[blk] for x in rj) / 3
                row = {
                    "lane_id": lane_id, "model": model, "lane_role": role,
                    "configuration": cfg, "block_id": blk,
                    "solo_B": solo_b[blk], "solo_A": solo_a[blk],
                    "B_given_A": ba[blk], "A_given_B": ab[blk],
                    "B_given_R1": rj[0][blk], "B_given_R2": rj[1][blk],
                    "B_given_R3": rj[2][blk], "B_given_Rbar": rbar,
                    "D_B_from_A": solo_b[blk] - ba[blk],
                    "D_B_from_Rbar": solo_b[blk] - rbar,
                    "D_A_from_B": solo_a[blk] - ab[blk],
                    "Lambda": (solo_b[blk] - ba[blk]) - (solo_a[blk] - ab[blk]),
                    "Delta_R": rbar - ba[blk],
                    "Delta_1": rj[0][blk] - ba[blk],
                    "Delta_2": rj[1][blk] - ba[blk],
                    "Delta_3": rj[2][blk] - ba[blk],
                }
                if has_cl:
                    cl = cells[("B", "CL", cfg)][blk]
                    row["B_given_CL"] = cl
                    row["Delta_broad"] = cl - ba[blk]
                contrast_rows.append(row)
        # verify against the signed record
        ua = json.loads((d / "UNMASKED_ANALYSIS" / "unmasked_result.json").read_text())
        for cfg in ("outcome_first", "outcome_second"):
            rec = ua["estimands"]["configurations"][cfg]
            mine = {k: sum(r[v] for r in contrast_rows
                           if r["lane_id"] == lane_id and r["configuration"] == cfg) / len(blocks)
                    for k, v in (("D(B<-A)", "D_B_from_A"), ("D(A<-B)", "D_A_from_B"),
                                 ("Lambda", "Lambda"), ("Delta_R", "Delta_R"))}
            for member, got in mine.items():
                want = rec[member]["point"]
                if not math.isclose(got, want, abs_tol=1e-12):
                    raise SystemExit(
                        f"FATAL {lane_id} {cfg} {member}: reconstructed {got!r} "
                        f"!= record {want!r}")
        print(f"  verified block-level reconstruction: {lane_id}")
    return cell_rows, contrast_rows, difficulty_rows


def figure_views(out: Path, t: dict) -> None:
    """Tidy one-row-per-mark tables, one per proposed figure."""
    master = t["master"]
    comp = t["compression"]

    def get(lane, cfg, member):
        for r in master:
            if (r["lane_id"] == lane and r["member"] == member
                    and (r["configuration"] or "cross") == cfg):
                return r
        return None

    lanes = [(l["lane_id"], l["model"], l["lane_role"]) for l in t["lanes"]]

    # --- F1: forest of Delta_R
    forest = []
    for lane, model, role in lanes:
        for cfg in ("outcome_first", "outcome_second"):
            r = get(lane, cfg, "Delta_R")
            if not r or r["status"] != "IDENTIFIED":
                continue
            lo, hi = float(r["simultaneous_lower"]), float(r["simultaneous_upper"])
            k = comp.get((lane, "Delta_R", cfg), {})
            forest.append({
                "lane_id": lane, "model": model, "lane_role": role,
                "outcome_position": r["outcome_position"],
                "estimate": r["point_estimate"],
                "sim_lower": lo, "sim_upper": hi,
                "marg_lower": r["marginal_lower"], "marg_upper": r["marginal_upper"],
                "half_width": r["realised_half_width"],
                "n_blocks": r["n_blocks"], "family": "F1",
                "threshold_L3a_L3c": 0.10, "threshold_L3b": 0.25, "zero": 0.0,
                "reading": ("L3c_upper_below_0.10" if hi < 0.10 else "spans_0.10"),
                "direction": ("A_COMPARATIVELY_BETTER" if hi < 0 else
                              "A_HARMS_MORE" if lo > 0 else "DIRECTION_UNRESOLVED"),
                "precision_met": r["precision_met"],
                "boundary_statuses": r.get("boundary_statuses") or "",
                "positive_direction_compressed": k.get("positive_direction_compressed"),
                "negative_direction_compressed": k.get("negative_direction_compressed"),
                "compressed_by": k.get("compressed_by"),
                "arm_B_under_A": k.get("negative_arm"),
                "arm_B_under_Rbar": k.get("positive_arm"),
                "attainable_min": k.get("attainable_min"),
                "attainable_max": k.get("attainable_max"),
                "l3c_bounded_by_arm_level": bool(k.get("positive_direction_compressed")),
                "evidence_status": r["evidence_status"],
                "source_artifact": r["source_artifact"],
            })
    w(out, "fig1_delta_r_forest.csv", forest, list(forest[0]))

    # --- F2: raw loss vs matched-reference loss vs Delta_R
    cellmap = {}
    for c in t["cells"]:
        cellmap[(c["lane_id"], c["member"], c["configuration"], c["cell"])] = c
    decomp = []
    for lane, model, role in lanes:
        for cfg in ("outcome_first", "outcome_second"):
            dba, dr = get(lane, cfg, "D(B<-A)"), get(lane, cfg, "Delta_R")
            if not (dba and dr and dr["status"] == "IDENTIFIED"):
                continue
            const = [c for c in t["cells"]
                     if c["lane_id"] == lane and c["member"] == "Delta_R"
                     and c["configuration"] == cfg]
            byslot = {c["companion_slot"]: c["compliance_rate"] for c in const}
            solo_b = next((c["compliance_rate"] for c in t["cells"]
                           if c["lane_id"] == lane and c["member"] == "D(B<-A)"
                           and c["configuration"] == cfg and c["role"] == "solo"), None)
            d_rbar = (None if solo_b is None
                      else float(dba["point_estimate"]) - float(dr["point_estimate"]))
            decomp.append({
                "lane_id": lane, "model": model, "lane_role": role,
                "outcome_position": dba["outcome_position"],
                "solo_B": solo_b,
                "B_given_A": byslot.get("A"),
                "B_given_R1": byslot.get("R1"), "B_given_R2": byslot.get("R2"),
                "B_given_R3": byslot.get("R3"),
                "B_given_Rbar": (None if d_rbar is None or solo_b is None
                                 else solo_b - d_rbar),
                "D_B_from_A": dba["point_estimate"],
                "D_B_from_A_sim_lower": dba["simultaneous_lower"],
                "D_B_from_A_sim_upper": dba["simultaneous_upper"],
                "D_B_from_Rbar_point_DERIVED_no_registered_interval": d_rbar,
                "Delta_R": dr["point_estimate"],
                "Delta_R_sim_lower": dr["simultaneous_lower"],
                "Delta_R_sim_upper": dr["simultaneous_upper"],
                "n_blocks": dr["n_blocks"],
                "evidence_status": dr["evidence_status"],
                "note": ("D(B<-Rbar) is the unweighted mean of the three F2 "
                         "members and is NOT itself a registered estimand: it "
                         "has no simultaneous interval. Delta_R = "
                         "D(B<-A) - D(B<-Rbar) exactly."),
                "source_artifact": dr["source_artifact"],
            })
    w(out, "fig2_loss_decomposition.csv", decomp, list(decomp[0]))

    # --- F3: direction x outcome position
    dirpos = []
    for lane, model, role in lanes:
        for cfg in ("outcome_first", "outcome_second"):
            for member in ("D(B<-A)", "D(A<-B)", "Lambda"):
                r = get(lane, cfg, member)
                if not r or r["status"] != "IDENTIFIED":
                    continue
                dirpos.append({
                    "lane_id": lane, "model": model, "lane_role": role,
                    "outcome_position": r["outcome_position"],
                    "direction_measured": ("B" if member == "D(B<-A)"
                                           else "A" if member == "D(A<-B)"
                                           else "B minus A"),
                    "member": member, "cell": r["cell"],
                    "estimate": r["point_estimate"],
                    "sim_lower": r["simultaneous_lower"],
                    "sim_upper": r["simultaneous_upper"],
                    "half_width": r["realised_half_width"],
                    "precision_met": r["precision_met"],
                    "n_blocks": r["n_blocks"],
                    "position_confounded": r["outcome_position"] == "second",
                    "evidence_status": r["evidence_status"],
                    "source_artifact": r["source_artifact"],
                })
    for lane, model, role in lanes:
        for member in ("Ord_A", "Ord_B", "Ord_Lambda", "Ord_Rbar", "Ord_CL"):
            r = get(lane, "cross", member)
            if not r or r["status"] != "IDENTIFIED":
                continue
            dirpos.append({
                "lane_id": lane, "model": model, "lane_role": role,
                "outcome_position": "cross", "direction_measured": member,
                "member": member, "cell": r["cell"],
                "estimate": r["point_estimate"],
                "sim_lower": r["simultaneous_lower"],
                "sim_upper": r["simultaneous_upper"],
                "half_width": r["realised_half_width"],
                "precision_met": r["precision_met"],
                "n_blocks": r["n_blocks"], "position_confounded": False,
                "evidence_status": r["evidence_status"],
                "source_artifact": r["source_artifact"],
            })
    w(out, "fig3_direction_and_position.csv", dirpos, list(dirpos[0]))

    # --- F4: same-form vs broad-class (class-arm lanes only)
    sfb = []
    for lane, model, role in lanes:
        for cfg in ("outcome_first", "outcome_second"):
            dr, db = get(lane, cfg, "Delta_R"), get(lane, cfg, "Delta_broad")
            if not (dr and db and db["status"] == "IDENTIFIED"):
                continue
            for label, r, comp in (("same-form (mean of 3 Tier-1 markers)", dr, "Rbar"),
                                   ("broad-class (1 Tier-3 budget)", db, "CL")):
                sfb.append({
                    "lane_id": lane, "model": model, "lane_role": role,
                    "outcome_position": r["outcome_position"],
                    "contrast": r["member"], "comparison_pool": label,
                    "companion": comp,
                    "estimate": r["point_estimate"],
                    "sim_lower": r["simultaneous_lower"],
                    "sim_upper": r["simultaneous_upper"],
                    "half_width": r["realised_half_width"],
                    "n_blocks": r["n_blocks"], "family": r["family"],
                    "registered_threshold": r["threshold"],
                    "evidence_status": r["evidence_status"],
                    "caveat": ("" if comp == "Rbar" else
                               "COMPANION_CLASS_NOT_MATCHED is registered; and "
                               "the post-hoc confirmatory coordinate shows CL "
                               "was NOT difficulty-matched (see "
                               "posthoc_confirmatory_difficulty.csv)"),
                    "source_artifact": r["source_artifact"],
                })
    if sfb:
        w(out, "fig4_same_form_vs_broad_class.csv", sfb, list(sfb[0]))

    # --- A1: repeat-lane agreement (same model, two roots)
    rep = []
    dup = {}
    for lane, model, role in lanes:
        dup.setdefault(model, []).append((lane, role))
    for model, entries in dup.items():
        if len(entries) < 2:
            continue
        for cfg in ("outcome_first", "outcome_second"):
            for member in ("Delta_R", "D(B<-A)", "D(A<-B)", "Lambda"):
                vals = {}
                for lane, role in entries:
                    r = get(lane, cfg, member)
                    if r and r["status"] == "IDENTIFIED":
                        vals[role] = (lane, r)
                if len(vals) == 2:
                    (cl, cr), (rl, rr) = vals["canonical"], vals["repeat"]
                    rep.append({
                        "model": model, "member": member,
                        "outcome_position": cr["outcome_position"],
                        "canonical_lane": cl, "repeat_lane": rl,
                        "canonical_estimate": cr["point_estimate"],
                        "repeat_estimate": rr["point_estimate"],
                        "difference": float(cr["point_estimate"]) - float(rr["point_estimate"]),
                        "canonical_half_width": cr["realised_half_width"],
                        "repeat_half_width": rr["realised_half_width"],
                        "evidence_status": "DEV_REHEARSAL_repeat_run_not_a_replication",
                        "note": ("the two roots re-ran §12-§13 from scratch, so "
                                 "the reference severities differ; this is "
                                 "selection-plus-sampling variability, not "
                                 "measurement error"),
                    })
    if rep:
        w(out, "figA1_repeat_lane_agreement.csv", rep, list(rep[0]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--no-blocks", action="store_true")
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    print("extracting from signed records ...")
    t = build()

    w(out, "lanes.csv", t["lanes"], list(t["lanes"][0]))
    master_fields = [
        "lane_id", "model", "lane_role", "configuration", "outcome_position",
        "member", "family", "family_tier", "cell", "claim_level",
        "point_estimate", "estimate", "simultaneous_lower", "simultaneous_upper",
        "decision_lower", "decision_upper", "marginal_lower", "marginal_upper",
        "standard_error", "realised_half_width", "precision_precondition",
        "precision_met", "threshold", "n_blocks", "status", "evidence_status",
        "identification_status", "boundary_statuses", "degenerate",
        "source_artifact", "source_stage", "stage_record_hash"]
    w(out, "estimands_master.csv", t["master"], master_fields)

    core = [r for r in t["master"]
            if r["member"] in ("Delta_R", "D(B<-A)", "D(A<-B)", "Lambda", "Xi",
                               "Delta_broad", "D(B<-CL)")
            and r["status"] == "IDENTIFIED"]
    w(out, "fig_primary_estimands.csv", core, master_fields)

    dj = [r for r in t["master"]
          if r["member"] in ("Delta_1", "Delta_2", "Delta_3", "D(B<-R1)",
                             "D(B<-R2)", "D(B<-R3)") and r["status"] == "IDENTIFIED"]
    w(out, "fig_delta_j.csv", dj, master_fields)

    orders = [r for r in t["master"] if r["family"] == "F11"]
    w(out, "fig_order_contrasts.csv", orders, master_fields)

    w(out, "cell_compliance.csv", t["cells"], list(t["cells"][0]))
    w(out, "references_selected.csv", t["refs"], list(t["refs"][0]))
    w(out, "reference_candidates.csv", t["candidates"], list(t["candidates"][0]))
    w(out, "coverage_c1_c8.csv", t["coverage"], list(t["coverage"][0]))
    w(out, "calibration_curves.csv", t["curves"], list(t["curves"][0]))
    w(out, "operating_points.csv", t["operating_points"], list(t["operating_points"][0]))
    w(out, "robustness_f5.csv", t["robustness"], master_fields)
    w(out, "vacuity_f6.csv", t["vacuity"], master_fields)
    w(out, "projection_audit.csv", t["projection"], list(t["projection"][0]))
    w(out, "statements.csv", t["statements"], list(t["statements"][0]))
    w(out, "iota_a_stability.csv", t["stability"], list(t["stability"][0]))

    not_id = [r for r in t["master"] if r["status"] != "IDENTIFIED"]
    w(out, "not_identified.csv", not_id, master_fields)

    if not args.no_blocks:
        print("reconstructing block-level tables ...")
        cell_rows, contrast_rows, difficulty_rows = block_tables(out)
        w(out, "posthoc_confirmatory_difficulty.csv", difficulty_rows,
          list(difficulty_rows[0]))
        cf = list(cell_rows[0])
        with gzip.open(out / "cell_means_blocklevel.csv.gz", "wt", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=cf, extrasaction="ignore")
            wr.writeheader()
            wr.writerows(cell_rows)
        print(f"  cell_means_blocklevel.csv.gz          {len(cell_rows):6d} rows")
        kf = ["lane_id", "model", "lane_role", "configuration", "block_id",
              "solo_B", "solo_A", "B_given_A", "A_given_B", "B_given_R1",
              "B_given_R2", "B_given_R3", "B_given_Rbar", "B_given_CL",
              "D_B_from_A", "D_B_from_Rbar", "D_A_from_B", "Lambda", "Delta_R", "Delta_1",
              "Delta_2", "Delta_3", "Delta_broad"]
        with gzip.open(out / "block_contrasts.csv.gz", "wt", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=kf, extrasaction="ignore")
            wr.writeheader()
            wr.writerows(contrast_rows)
        print(f"  block_contrasts.csv.gz                {len(contrast_rows):6d} rows")

    figure_views(out, t)
    # `--out` is a user-supplied path and need not sit under the repository
    # (nor be absolute), so report it relatively only when it actually is.
    try:
        shown = out.resolve().relative_to(REPO)
    except ValueError:
        shown = out
    print(f"\nwrote {shown}")


if __name__ == "__main__":
    main()
