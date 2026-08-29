#!/usr/bin/env python3
"""The reference-support landscape, on the corrected chance basis. DIAGNOSTIC.

    python3 tools/v7_reference_support_landscape.py \\
        --tree v7=/path/dci1/evidence/dci1v7 \\
        --tree dev=/path/dci1/evidence/dci1v7-development/evidence/dci1v7 \\
        --out reports/dci1v7/reference_support_landscape --workers 4

Read-only over every tree it is given. Everything here is *exploratory /
diagnostic*: it reconstructs, from stored Gate-2 calibration rows and the
grid runs' unconstrained cells, the landscape §12.6 and §13 decide on, with
`chance_compliance` measured as §13.2 registers it (the 2026-08-29
correction) --- never the recorded 0.0 column --- and asks why the core
matched-reference contrast Delta_R is supported while the difficulty-response
analysis (delta_diff, beta) is not.

Per replication it produces:

* the per-rung table (family, tier, group, severity, solo, kappa, iota, lift,
  vacuity, kappa(R|B), §12.6 eligibility, every V(R) component incl. §13.7
  stability on the corrected split tables, the §13.12 spectrum verdict);
* §12.6's C1--C8 on the calibrated basis (production kernel), per-family C4
  state on several bases (calibrated-corrected, calibrated-recorded (kappa=0),
  pre-screen certificate, raw pool ignoring eligibility, spectrum-qualified
  pool), and descriptive relaxations of C4's span / rung floors;
* Gate 3B's selection on the corrected table (R1--R3, spectrum attempt per
  qualified family, backups), the nearby-support counts around iota_A, and
  per-family monotonicity of severity -> iota;
* the composed B+R outcomes that genuinely exist (Gate 4's 24 topics; the
  confirmatory blocks where generated), D(B <- R) per configuration, and the
  realised iota of every composed companion on those blocks.

Nothing under any tree is written. Plots are written with matplotlib.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import time
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))


import v7_chance_basis_impact as impact

from dci1v7.analysis.intervals import interval_inside
from dci1v7.protocol import constants as C
from dci1v7.protocol.taxonomy import (
    SLOT_BROAD_CLASS,
    SLOT_CORE,
    SLOT_SPECTRUM,
)
from dci1v7.run import gates_run
from dci1v7.stages import feasibility, regime, selection
from dci1v7.stages.calibration_table import (
    instructed_compliance,
    load_calibration_table,
    tie_key,
)
from dci1v7.stages.validity import VALIDITY_COMPONENTS, evaluate_validity
from dci1v7.verifiers.constraints import FAMILIES, FEATURE_GROUP_IDS

STAGE_FILES = dict(impact.STAGE_FILES)
STAGE_FILES["gate4"] = ("GATE_4_COMPOSED_CONTRAST", "gate4_composed.json")
STAGE_FILES["probe"] = ("GATE_2_75_COMPOSED_PROBE",
                        "gate2_75_composed_probe.json")
CALIPERS = (0.05, 0.10, 0.15)
SPAN_RELAXATIONS = (0.40, 0.30, 0.20, 0.10)
RUNG_RELAXATIONS = (3, 2)


def _record(model_dir: pathlib.Path, key: str) -> dict[str, Any] | None:
    stage, name = STAGE_FILES[key]
    path = model_dir / stage / name
    return json.load(open(path)) if path.exists() else None


def _family_order(kind: str) -> tuple:
    f = FAMILIES[kind]
    return (f.structural_tier, FEATURE_GROUP_IDS.index(f.feature_group), kind)


def _natural_slot(kind: str) -> str:
    f = FAMILIES[kind]
    if f.structural_tier in (1, 2):
        return SLOT_CORE
    return SLOT_BROAD_CLASS


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / math.sqrt(
        sxx * syy)


# ----------------------------------------------------------- C4 by family

def _c4_family_table(entries: list[dict[str, Any]], *, iota_a: float,
                     ignore_eligibility: bool = False
                     ) -> dict[str, dict[str, Any]]:
    """Per family: the registered C4 state (`regime.family_c4_state`) and its
    first deficiency, plus the counts the report asks for."""
    by_family: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        by_family.setdefault(e["family"], []).append(e)
    out: dict[str, dict[str, Any]] = {}
    for family, rows in sorted(by_family.items(), key=lambda kv:
                               _family_order(kv[0])):
        if ignore_eligibility:
            rows = [{**r, "eligible": r.get("iota") is not None} for r in rows]
        state = regime.family_c4_state(rows, iota_a=iota_a)
        deficiency = regime.family_deficiency(state)
        elig = [r for r in rows if r.get("eligible") and r.get("iota")
                is not None]
        iotas = [r["iota"] for r in elig]
        meta = FAMILIES[family]
        out[family] = {
            "family": family, "structural_tier": meta.structural_tier,
            "feature_group": meta.feature_group,
            "constraint_class": meta.constraint_class,
            "n_measured": len(rows), "n_eligible": len(elig),
            "ineligible": {r["candidate"]: (r.get("eligibility") or {})
                           .get("reason") for r in rows
                           if not r.get("eligible") or r.get("iota") is None},
            "min_iota": min(iotas) if iotas else None,
            "max_iota": max(iotas) if iotas else None,
            "span": state["span"],
            "n_below": sum(1 for v in iotas if tie_key(v) < tie_key(iota_a)),
            "n_above": sum(1 for v in iotas if tie_key(v) > tie_key(iota_a)),
            "straddles": bool(state["has_below"] and state["has_above"]),
            "meets_rung_floor": state["n_rungs"]
            >= C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY,
            "meets_span": state["span"] >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN,
            "c4_met": deficiency is None,
            "first_deficiency": deficiency,
            "severities_eligible": state["severities"],
            "nearest_below": (max((r["iota"] for r in elig
                                   if tie_key(r["iota"]) < tie_key(iota_a)),
                                  default=None)),
            "nearest_above": (min((r["iota"] for r in elig
                                   if tie_key(r["iota"]) > tie_key(iota_a)),
                                  default=None)),
        }
    return out


def _c4_summary(table: dict[str, dict[str, Any]]) -> dict[str, Any]:
    groups_met = {v["feature_group"] for v in table.values() if v["c4_met"]}
    deficiencies: dict[str, list[str]] = {}
    for v in table.values():
        if not v["c4_met"]:
            deficiencies.setdefault(v["first_deficiency"], []).append(
                v["family"])
    # Closest to passing: straddling families ranked by span shortfall.
    closest = sorted(
        (v for v in table.values() if not v["c4_met"] and v["straddles"]
         and v["meets_rung_floor"]),
        key=lambda v: C.COVERAGE_MIN_WITHIN_FAMILY_SPAN - v["span"])
    return {
        "straddling_groups": sorted(groups_met),
        "n_straddling_groups": len(groups_met),
        "required": C.COVERAGE_MIN_STRADDLING_FAMILIES,
        "c4_met": len(groups_met) >= C.COVERAGE_MIN_STRADDLING_FAMILIES,
        "families_met": sorted(v["family"] for v in table.values()
                               if v["c4_met"]),
        "first_deficiency_by_family": deficiencies,
        "closest_to_passing": [
            {"family": v["family"], "span": v["span"],
             "shortfall": C.COVERAGE_MIN_WITHIN_FAMILY_SPAN - v["span"],
             "n_eligible": v["n_eligible"]} for v in closest[:6]],
        "relaxations_descriptive": {
            f"span>={s:.2f},rungs>={r}": len({
                v["feature_group"] for v in table.values()
                if v["straddles"] and v["n_eligible"] >= r
                and v["span"] >= s})
            for s in SPAN_RELAXATIONS for r in RUNG_RELAXATIONS},
    }


# ------------------------------------------------------- composed outcomes

def _read_rows(path: pathlib.Path):
    with open(path) as f:
        for line in f:
            yield json.loads(line)


def _verdict(row: dict[str, Any], kind: str, severity: int | None,
             present: bool) -> bool | None:
    for s in row["scores"]:
        if s["kind"] == kind and s["present"] == present and (
                severity is None or int(s["severity"]) == int(severity)):
            return bool(s["passed"])
    return None


def _composed_from_runs(runs: list[pathlib.Path], slot_map: dict[str, Any],
                        *, basis: str,
                        external_b_solo: dict[str, list[float]] | None = None
                        ) -> dict[str, Any] | None:
    """D(B <- X) for every composed companion X that has B+X / X+B rows,
    per configuration, paired by block; plus realised solo/chance/iota of
    every slot on the same rows.

    ``external_b_solo`` (topic -> B verdicts) supplies the B-solo cell when
    the runs themselves carry none (Gate 2.75's probe run pairs with Gate
    2's `solo:B:m*` cell on the same 192 topics, as the probe stage itself
    does for A); pairing is then by topic rather than block."""
    if not runs:
        return None
    slot_kind = {slot: (str(v[0]), int(v[1])) for slot, v in slot_map.items()}
    b_kind, b_sev = slot_kind["B"]
    per_block: dict[str, dict[str, list[float]]] = {}
    # per_block[block][cell] -> list of B verdicts
    solo_by_slot: dict[str, dict[str, list[float]]] = {}
    chance_by_slot: dict[str, dict[str, list[float]]] = {}
    n_rows = 0
    key = "topic_id" if external_b_solo else "block_id"
    if external_b_solo:
        for topic, verdicts in external_b_solo.items():
            per_block.setdefault(topic, {})["solo:B"] = list(verdicts)
    for run in runs:
        for r in _read_rows(run / "scored.jsonl"):
            n_rows += 1
            block = str(r.get(key, r["topic_id"]))
            cell = r["cell_id"]
            if cell.startswith("pair:") or cell == "solo:B":
                v = _verdict(r, b_kind, b_sev, present=(
                    "B" in cell.split(":", 1)[1].split("+")))
                if v is not None and (cell == "solo:B" or "B" in
                                      cell.split(":", 1)[1].split("+")):
                    per_block.setdefault(block, {}).setdefault(
                        cell, []).append(float(v))
            if cell.startswith("solo:"):
                slot = cell.split(":", 1)[1]
                if slot in slot_kind:
                    k, s = slot_kind[slot]
                    v = _verdict(r, k, s, present=True)
                    if v is not None:
                        solo_by_slot.setdefault(slot, {}).setdefault(
                            block, []).append(float(v))
            if cell == "unconstrained":
                for slot, (k, s) in slot_kind.items():
                    v = _verdict(r, k, s, present=False)
                    if v is not None:
                        chance_by_slot.setdefault(slot, {}).setdefault(
                            block, []).append(float(v))
    blocks = sorted(b for b, cells in per_block.items() if "solo:B" in cells)

    def block_mean(values):
        return sum(values) / len(values)

    companions = sorted({
        c.split(":", 1)[1].replace("B+", "").replace("+B", "")
        for cells in per_block.values() for c in cells
        if c.startswith("pair:") and ("B+" in c or "+B" in c)})
    out_d: dict[str, Any] = {}
    for x in companions:
        for configuration, cell in ((C.OUTCOME_FIRST, f"pair:B+{x}"),
                                    (C.OUTCOME_SECOND, f"pair:{x}+B")):
            diffs = []
            for b in blocks:
                cells = per_block[b]
                if cell in cells:
                    diffs.append(block_mean(cells["solo:B"])
                                 - block_mean(cells[cell]))
            if not diffs:
                continue
            n = len(diffs)
            mean = sum(diffs) / n
            sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (n - 1)) \
                if n > 1 else float("nan")
            out_d[f"D(B<-{x})|{configuration}"] = {
                "companion": x, "configuration": configuration,
                "estimate": mean, "se_blocks": sd / math.sqrt(n),
                "n_blocks": n, "cell": cell,
                "p_b_solo": sum(block_mean(per_block[b]["solo:B"])
                                for b in blocks) / len(blocks),
                "p_b_composed": sum(block_mean(per_block[b][cell])
                                    for b in blocks if cell in per_block[b])
                / n}
    realised: dict[str, Any] = {}
    for slot in slot_kind:
        solo = solo_by_slot.get(slot)
        chance = chance_by_slot.get(slot)
        if not solo:
            continue
        p = sum(block_mean(v) for v in solo.values()) / len(solo)
        k = (sum(block_mean(v) for v in chance.values()) / len(chance)
             if chance else None)
        realised[slot] = {
            "kind": slot_kind[slot][0], "severity": slot_kind[slot][1],
            "solo": p, "chance": k, "n_blocks": len(solo),
            "iota": (None if k is None or k >= C.CHANCE_DEGENERACY_MAX
                     else instructed_compliance(p, k))}
    return {"basis": basis, "n_runs": len(runs), "n_rows": n_rows,
            "n_blocks": len(blocks), "companions": companions,
            "delivery_loss": out_d, "realised": realised}


def _b_solo_by_topic(gate2_dir: pathlib.Path, m_star: int
                     ) -> dict[str, list[float]]:
    """Gate 2's `solo:B:m*` cell on the 192 pooled calibration topics."""
    out: dict[str, list[float]] = {}
    wanted = f"solo:B:{m_star}"
    for run in sorted(p for p in (gate2_dir / "backend_runs").iterdir()
                      if p.name.startswith("grid")):
        for r in _read_rows(run / "scored.jsonl"):
            if r["cell_id"] != wanted:
                continue
            v = _verdict(r, "B", m_star, present=True)
            if v is not None:
                out.setdefault(r["topic_id"], []).append(float(v))
    return out


def _probe_composed(model_dir: pathlib.Path, gate2_dir: pathlib.Path,
                    n_star: int) -> dict[str, Any] | None:
    """Gate 2.75's stand-in composed cells (B+P2, P2+B, ...), if generated.
    The stand-ins are probe-only instruments (v6 A10): non-selectable, and
    not scored on the unconstrained cell, so they carry raw solo compliance
    and NO registered iota. B's solo cell is Gate 2's, on the same topics."""
    probe = _record(model_dir, "probe")
    if probe is None:
        return None
    m_star = int(probe["m_star"])
    run = model_dir / STAGE_FILES["probe"][0] / "backend_runs" / f"m{m_star}"
    if not (run / "scored.jsonl").exists():
        return None
    standins = {s.split(":")[0]: s for s in probe.get("standins") or []}
    placement = probe.get("standin_placement") or {}
    slot_map = {"B": ("B", m_star), "A": ("A", int(n_star))}
    for slot in ("P1", "P2", "P3"):
        kind = "PS" + slot[1]
        p = placement.get(kind) or {}
        if p.get("placed") and p.get("severity") is not None:
            slot_map[slot] = (kind, int(p["severity"]))
    composed = _composed_from_runs(
        [run], slot_map, basis="gate2_75_probe",
        external_b_solo=_b_solo_by_topic(gate2_dir, m_star))
    if composed is None:
        return None
    composed["note"] = ("Gate 2.75 stand-ins are probe-only instruments; "
                        "they are never selectable as references and were "
                        "not scored on the unconstrained cell, so they have "
                        "raw solo compliance and no registered iota. "
                        "P(B | solo) is Gate 2's solo:B:m* cell on the same "
                        "192 topics (a different generation identity), "
                        "paired by topic")
    composed["standins"] = standins
    return composed


# ------------------------------------------------------------- analysis

def analyse(label: str, model_dir: pathlib.Path) -> dict[str, Any] | None:
    gate2 = _record(model_dir, "gate2")
    regime_rec = _record(model_dir, "regime")
    if gate2 is None or regime_rec is None:
        return None
    t0 = time.time()
    model_key = gate2["model_key"]
    m_star = int(gate2["m_star"])
    n_star = str(gate2["n_star"])
    gate2_dir = model_dir / STAGE_FILES["gate2"][0]
    signed = {k: _record(model_dir, k)
              for k in ("gate2_5", "gate3a", "gate3b", "gate3c", "gate4",
                        "final")}
    unconstrained = impact._unconstrained_rows(gate2_dir)
    corrected_all = impact._corrected_tables(gate2, unconstrained)
    corrected, withheld = gates_run._withhold_degenerate(corrected_all)
    recorded = {s: [dict(r) for r in gate2["calibration_rows"][s]]
                for s in impact.SPLITS}
    iota_a = float(gate2["iota_a"])
    solo_a = float(gate2["solo_compliance_a"])
    iota_a_unc = instructed_compliance(
        solo_a, float(gate2["load_zero_chance_curves"]["A"][n_star]))
    formulation = regime_rec.get("coverage_eligibility_formulation")

    # --- the production kernels on the corrected table
    q_new = impact._qualify(corrected["pooled"], model_key=model_key,
                            m_star=m_star)
    gate2_new = dict(gate2)
    gate2_new["calibration_rows"] = corrected
    gate2_new["calibration_rows_withheld"] = withheld
    shaped = {"qualification_by_severity": {str(m_star): {
        "qualified_pool": q_new["qualified_pool"],
        "qualified_families": q_new["qualified_families"],
        "n_qualified": q_new["n_qualified"]}}}
    calibration = feasibility.calibration_at(
        model_key=model_key, gate2_record=gate2_new, gate2_5_record=shaped,
        m_star=m_star, seed=0, resamples=C.STABILITY_BOOTSTRAP_RESAMPLES)
    chosen = feasibility.selection_at(calibration, model_key=model_key)
    coverage = feasibility.coverage_at_calibrated_iota_a(
        gate2_record=gate2_new, regime_record=regime_rec)
    sup = feasibility.support_at(
        chosen, model_key=model_key,
        calibration={"qualified_families": list(q_new["qualified_families"])},
        regime_record=regime_rec,
        extra_design_time_failures=list(coverage["failures"]),
        extra_spectrum_failures=list(coverage["spectrum_failures"]))
    stability_by = dict(calibration["stability"])
    rows = load_calibration_table(corrected["pooled"], model_key=model_key,
                                  m_star=m_star, split="pooled")
    rows_a = load_calibration_table(corrected[C.CALIBRATION_A],
                                    model_key=model_key, m_star=m_star,
                                    split=C.CALIBRATION_A)
    rows_b = load_calibration_table(corrected[C.CALIBRATION_B],
                                    model_key=model_key, m_star=m_star,
                                    split=C.CALIBRATION_B)
    by_split = {C.CALIBRATION_A: {r.label: r for r in rows_a},
                C.CALIBRATION_B: {r.label: r for r in rows_b}}

    # --- §12.6 eligibility rows (E2) on the corrected calibrated basis
    cov_rows = regime.calibration_coverage_rows(
        list(corrected["pooled"]) + list(withheld["pooled"]),
        formulation=formulation)
    cov_rows_recorded = regime.calibration_coverage_rows(
        recorded["pooled"], formulation=formulation)
    prescreen_rows = regime.coverage_rows(
        regime_rec["difficulty_table"], regime_rec["carried_set"],
        formulation=formulation)
    iota_a_prescreen = float(regime_rec["iota_a_prescreen"])
    calibrated_labels = {r["candidate"] for r in cov_rows}

    # --- per-rung landscape
    {e["family"]: e for e in chosen["core"]["core_references"]}
    core_labels = {f"{e['family']}:{e['severity']}"
                   for e in chosen["core"]["core_references"]}
    slot_of = {f"{k}:{s}": slot
               for slot, (k, s) in chosen["slot_map"].items()}
    cov_by = {r["candidate"]: r for r in cov_rows}
    rungs: list[dict[str, Any]] = []
    bound = (-C.STABILITY_EQUIVALENCE_BOUND, C.STABILITY_EQUIVALENCE_BOUND)
    for row in sorted(rows, key=lambda r: (_family_order(r.kind),
                                           r.severity)):
        slot = _natural_slot(row.kind)
        full = evaluate_validity(
            row, slot=slot, iota_a=iota_a, solo_compliance_a=solo_a,
            stability=stability_by.get(row.label),
            components=VALIDITY_COMPONENTS)
        spectrum = evaluate_validity(
            row, slot=SLOT_SPECTRUM, iota_a=iota_a, solo_compliance_a=solo_a,
            stability=stability_by.get(row.label),
            components=selection.SPECTRUM_COMPONENTS,
            core_family_tier=FAMILIES[row.kind].structural_tier)
        spectrum_ok = all(c.passed for c in spectrum.components
                          if c.name in selection.SPECTRUM_COMPONENTS)
        # Diagnostic what-if: §13.7 condition 1 WITHOUT V_diff folded in
        # (the registered tension RESEARCH_STATE §4an records). Same
        # bootstrap intervals, admissibility re-read per split on V_head,
        # V_chance, V_inter alone.
        stab = stability_by.get(row.label) or {}
        unfolded = None
        if stab:
            per_split_ok = True
            for split in (C.CALIBRATION_A, C.CALIBRATION_B):
                srow = by_split[split].get(row.label)
                if srow is None:
                    per_split_ok = False
                    break
                v = evaluate_validity(
                    srow, slot=slot, iota_a=gate2["iota_a_by_split"][split],
                    solo_compliance_a=gate2["solo_a_by_split"][split],
                    components=("V_head", "V_chance", "V_inter"))
                if not all(c.passed for c in v.components
                           if c.name in ("V_head", "V_chance", "V_inter")):
                    per_split_ok = False
            gaps = (stab.get("iota_split_difference"),
                    stab.get("solo_split_difference"))
            equivalent = all(g is not None and interval_inside(
                (g["lower"], g["upper"]), bound) for g in gaps)
            unfolded = bool(per_split_ok and equivalent)
        spectrum_unfolded = None
        if unfolded is not None:
            others = [c.passed for c in spectrum.components
                      if c.name in selection.SPECTRUM_COMPONENTS
                      and c.name != "V_stab"]
            spectrum_unfolded = bool(all(others) and unfolded)
        cov = cov_by.get(row.label) or {}
        rungs.append({
            "candidate": row.label, "family": row.kind,
            "severity": row.severity,
            "structural_tier": row.structural_tier,
            "feature_group": row.feature_group,
            "constraint_class": row.constraint_class,
            "form": FAMILIES[row.kind].form,
            "solo": row.solo_compliance, "chance": row.chance_compliance,
            "iota": row.iota, "lift": row.lift,
            "vacuity": row.solo_vacuity, "kappa_under_b": row.kappa_under_b,
            "distance": abs(row.iota - iota_a),
            "side": ("below" if tie_key(row.iota) < tie_key(iota_a)
                     else "above" if tie_key(row.iota) > tie_key(iota_a)
                     else "at"),
            "prescreen_iota": row.prescreen_iota,
            "eligible_12_6": bool(cov.get("eligible")),
            "ineligibility_reason": (cov.get("eligibility") or {}).get(
                "reason"),
            "qualified_gate2_5": row.label in set(q_new["qualified_pool"]),
            "validity_slot": slot,
            "v_r_passed": full.passed,
            "first_failing": full.first_failing_component,
            "failing_components": list(full.failing_components),
            "stability_passed": bool(stab.get("passed")) if stab else None,
            "stability_reason": stab.get("reason") if stab else None,
            "stability_unfolded_diagnostic": unfolded,
            "spectrum_eligible_registered": spectrum_ok,
            "spectrum_first_failing": next(
                (c.name for c in spectrum.components
                 if c.name in selection.SPECTRUM_COMPONENTS
                 and c.passed is False), None),
            "spectrum_eligible_unfolded_diagnostic": spectrum_unfolded,
            "selected_slot": slot_of.get(row.label),
            "is_core_reference": row.label in core_labels,
        })
    for w in withheld["pooled"]:
        rungs.append({
            "candidate": f"{w['kind']}:{w['severity']}", "family": w["kind"],
            "severity": w["severity"],
            "structural_tier": FAMILIES[w["kind"]].structural_tier,
            "feature_group": FAMILIES[w["kind"]].feature_group,
            "constraint_class": FAMILIES[w["kind"]].constraint_class,
            "form": FAMILIES[w["kind"]].form,
            "solo": w["solo_compliance"], "chance": w["chance_compliance"],
            "iota": None, "lift": w["solo_compliance"]
            - w["chance_compliance"], "vacuity": w["solo_vacuity"],
            "kappa_under_b": w.get("kappa_under_b"), "distance": None,
            "side": "undefined", "prescreen_iota": None,
            "eligible_12_6": bool((cov_by.get(
                f"{w['kind']}:{w['severity']}") or {}).get("eligible")),
            "ineligibility_reason": "DIFFICULTY_COORDINATE_DEGENERATE",
            "qualified_gate2_5": False, "validity_slot": None,
            "v_r_passed": False, "first_failing": "WITHHELD_DEGENERATE",
            "failing_components": ["withheld"], "stability_passed": None,
            "stability_reason": None, "stability_unfolded_diagnostic": None,
            "spectrum_eligible_registered": False,
            "spectrum_first_failing": "WITHHELD_DEGENERATE",
            "spectrum_eligible_unfolded_diagnostic": False,
            "selected_slot": None, "is_core_reference": False,
        })

    # --- C4 on every basis
    c4 = {
        "calibrated_corrected": _c4_family_table(cov_rows, iota_a=iota_a),
        "calibrated_recorded_kappa0": _c4_family_table(cov_rows_recorded,
                                                       iota_a=iota_a),
        "calibrated_corrected_at_unconstrained_iota_a":
            _c4_family_table(cov_rows, iota_a=iota_a_unc),
        "prescreen_certified": _c4_family_table(prescreen_rows,
                                                iota_a=iota_a_prescreen),
        "prescreen_restricted_to_calibrated_rungs": _c4_family_table(
            [r for r in prescreen_rows if r["candidate"] in calibrated_labels],
            iota_a=iota_a_prescreen),
        "calibrated_raw_pool_ignoring_eligibility": _c4_family_table(
            cov_rows, iota_a=iota_a, ignore_eligibility=True),
        "calibrated_spectrum_qualified_registered": _c4_family_table(
            [{**cov_by[r["candidate"]],
              "eligible": r["spectrum_eligible_registered"]}
             for r in rungs if r["candidate"] in cov_by],
            iota_a=iota_a),
        "calibrated_spectrum_qualified_unfolded_diagnostic": _c4_family_table(
            [{**cov_by[r["candidate"]],
              "eligible": bool(r["spectrum_eligible_unfolded_diagnostic"])}
             for r in rungs if r["candidate"] in cov_by],
            iota_a=iota_a),
    }
    c4_summary = {k: _c4_summary(v) for k, v in c4.items()}
    # Attrition per family: pre-screen span on the SAME rungs vs calibrated.
    attrition = {}
    for family, cal in c4["calibrated_corrected"].items():
        pre_same = c4["prescreen_restricted_to_calibrated_rungs"].get(family)
        pre_all = c4["prescreen_certified"].get(family)
        raw = c4["calibrated_raw_pool_ignoring_eligibility"][family]
        attrition[family] = {
            "prescreen_span_all_carried": pre_all["span"] if pre_all else None,
            "prescreen_span_same_rungs": pre_same["span"] if pre_same else None,
            "calibrated_span_eligible": cal["span"],
            "calibrated_span_all_measured": raw["span"],
            "prescreen_c4_met": bool(pre_all and pre_all["c4_met"]),
            "calibrated_c4_met": cal["c4_met"],
            "lost_to_eligibility": raw["c4_met"] and not cal["c4_met"],
            "n_measured": cal["n_measured"], "n_eligible": cal["n_eligible"],
            "ineligible_reasons": cal["ineligible"],
        }

    # --- monotonicity of severity -> iota per family (all measured rungs)
    monotonic = {}
    for family in sorted({r["family"] for r in rungs}, key=_family_order):
        fam = [r for r in rungs if r["family"] == family
               and r["iota"] is not None]
        fam.sort(key=lambda r: selection.restrictiveness_key(family,
                                                             r["severity"]))
        keys = [selection.restrictiveness_key(family, r["severity"])
                for r in fam]
        iotas = [r["iota"] for r in fam]
        inversions = sum(1 for i in range(len(fam) - 1)
                         if iotas[i + 1] > iotas[i] + 1e-12)
        steps = [iotas[i] - iotas[i + 1] for i in range(len(fam) - 1)]
        monotonic[family] = {
            "n": len(fam),
            "spearman_restrictiveness_vs_iota": _spearman(keys, iotas),
            "adjacent_inversions": inversions,
            "median_step": (sorted(steps)[len(steps) // 2] if steps
                            else None),
            "max_step": max(steps) if steps else None,
            "span_all_measured": (max(iotas) - min(iotas)) if iotas else None,
            "ladder": [(r["severity"], round(r["iota"], 4),
                        r["eligible_12_6"]) for r in fam],
        }

    # --- nearby support
    eligible_rows = [r for r in rungs if r["eligible_12_6"]
                     and r["iota"] is not None]
    nearby = {}
    for cal in CALIPERS:
        near = [r for r in eligible_rows if r["distance"] <= cal]
        near_q = [r for r in near if r["v_r_passed"]]
        near_spec = [r for r in near if r["spectrum_eligible_registered"]]
        nearby[f"{cal:.2f}"] = {
            "eligible_rungs": len(near),
            "eligible_families": sorted({r["family"] for r in near}),
            "eligible_tier12_families": sorted({
                r["family"] for r in near if r["structural_tier"] in (1, 2)}),
            "v_r_qualified_rungs": len(near_q),
            "v_r_qualified_families": sorted({r["family"] for r in near_q}),
            "spectrum_eligible_rungs": len(near_spec),
            "below": sum(1 for r in near if r["side"] == "below"),
            "above": sum(1 for r in near if r["side"] == "above"),
        }
    all_iotas = [r["iota"] for r in eligible_rows]
    spread = {
        "n_eligible": len(eligible_rows),
        "min_iota": min(all_iotas) if all_iotas else None,
        "max_iota": max(all_iotas) if all_iotas else None,
        "n_below": sum(1 for r in eligible_rows if r["side"] == "below"),
        "n_above": sum(1 for r in eligible_rows if r["side"] == "above"),
        "n_v_r_qualified": sum(1 for r in eligible_rows if r["v_r_passed"]),
        "n_spectrum_eligible_registered": sum(
            1 for r in eligible_rows if r["spectrum_eligible_registered"]),
        "spectrum_eligible_registered_range": [
            min((r["iota"] for r in eligible_rows
                 if r["spectrum_eligible_registered"]), default=None),
            max((r["iota"] for r in eligible_rows
                 if r["spectrum_eligible_registered"]), default=None)],
        "n_spectrum_eligible_unfolded_diagnostic": sum(
            1 for r in eligible_rows
            if r["spectrum_eligible_unfolded_diagnostic"]),
        "spectrum_eligible_unfolded_range": [
            min((r["iota"] for r in eligible_rows
                 if r["spectrum_eligible_unfolded_diagnostic"]),
                default=None),
            max((r["iota"] for r in eligible_rows
                 if r["spectrum_eligible_unfolded_diagnostic"]),
                default=None)],
    }

    # --- selection detail: R1-R3, spectrum attempts, backups
    by_label = {r["candidate"]: r for r in rungs}
    core_detail = []
    for e in chosen["core"]["core_references"]:
        lab = f"{e['family']}:{e['severity']}"
        r = by_label[lab]
        stab = stability_by.get(lab) or {}
        core_detail.append({
            "slot": e["slot"], "candidate": lab, "family": e["family"],
            "severity": e["severity"], "structural_tier": e["structural_tier"],
            "feature_group": e["feature_group"],
            "discourse_role": e["discourse_role"],
            "iota": r["iota"], "distance": r["distance"], "side": r["side"],
            "chance": r["chance"], "solo": r["solo"], "lift": r["lift"],
            "vacuity": r["vacuity"], "kappa_under_b": r["kappa_under_b"],
            "eligible_12_6": r["eligible_12_6"],
            "v_r_passed": r["v_r_passed"],
            "stability": {
                "passed": stab.get("passed"),
                "iota_split_difference": stab.get("iota_split_difference"),
                "per_split_iota": {s: (stab.get("per_split") or {}).get(
                    s, {}).get("iota") for s in (C.CALIBRATION_A,
                                                 C.CALIBRATION_B)}},
        })
    spectrum_attempts = []
    for fam_v in chosen["core"]["family_verdicts"]:
        if not fam_v["admitted"]:
            continue
        family = fam_v["family"]
        pool = [r for r in rungs if r["family"] == family
                and r["severity"] != fam_v["severity"]
                and r["spectrum_eligible_registered"]]
        pool_unf = [r for r in rungs if r["family"] == family
                    and r["severity"] != fam_v["severity"]
                    and r["spectrum_eligible_unfolded_diagnostic"]]
        triple = selection.select_spectrum_triple(
            family, rows, core_severity=fam_v["severity"], iota_a=iota_a,
            solo_compliance_a=solo_a, stability_by_candidate=stability_by)
        spectrum_attempts.append({
            "family": family, "core_severity": fam_v["severity"],
            "core_iota": fam_v["iota"], "core_distance": fam_v["distance"],
            "registered_pool_below": sorted(
                (r["candidate"], round(r["iota"], 4)) for r in pool
                if r["side"] == "below"),
            "registered_pool_above": sorted(
                (r["candidate"], round(r["iota"], 4)) for r in pool
                if r["side"] == "above"),
            "triple": triple,
            "unfolded_pool_below": sorted(
                (r["candidate"], round(r["iota"], 4)) for r in pool_unf
                if r["side"] == "below"),
            "unfolded_pool_above": sorted(
                (r["candidate"], round(r["iota"], 4)) for r in pool_unf
                if r["side"] == "above"),
            "family_c4": c4["calibrated_corrected"].get(family),
        })
    report = sup["report"]
    backups = list((report.get("realised") or {}).get("frozen_backups") or [])
    backup_detail = []
    for fam in backups:
        v = next((x for x in chosen["core"]["family_verdicts"]
                  if x["family"] == fam), None)
        fam_rungs = [r for r in rungs if r["family"] == fam
                     and r["iota"] is not None]
        q_rungs = [r for r in fam_rungs if r["qualified_gate2_5"]]
        best = min(q_rungs or fam_rungs, key=lambda r: r["distance"],
                   default=None)
        backup_detail.append({
            "family": fam,
            "admitted_full_v_r": bool(v and v["admitted"]),
            "severity": (v["severity"] if v and v["admitted"]
                         else (best or {}).get("severity")),
            "iota": (v["iota"] if v and v["admitted"]
                     else (best or {}).get("iota")),
            "distance": (v["distance"] if v and v["admitted"]
                         else (best or {}).get("distance")),
            "nearest_gate2_5_rung": (best or {}).get("candidate"),
            "nearest_rung_first_failing": (best or {}).get("first_failing"),
            "note": ("§13.15 freezes backups from Gate 2.5's qualified "
                     "families in sorted order; a backup family need not "
                     "pass the full V(R) (V_stab, V_diff) at Gate 3B"),
        })

    # --- composed outcomes that actually exist
    composed: dict[str, Any] = {}
    gate4 = signed["gate4"]
    if gate4 is not None:
        run = model_dir / STAGE_FILES["gate4"][0] / "backend_runs" / "composed"
        if (run / "scored.jsonl").exists():
            composed["gate4_24_topics"] = _composed_from_runs(
                [run], gate4["slot_map"], basis="gate4_24_topics")
        conf = model_dir / "CONFIRMATORY_GENERATION" / "backend_runs"
        if conf.exists():
            runs = sorted(p for p in conf.iterdir()
                          if (p / "scored.jsonl").exists())
            planned = sorted(p for p in conf.iterdir() if p.is_dir())
            got = _composed_from_runs(runs, gate4["slot_map"],
                                      basis="confirmatory_blocks")
            if got is not None:
                got["complete"] = len(runs) == len(planned) == 12
                got["n_planned_runs"] = len(planned)
                composed["confirmatory_blocks"] = got
    probe = _probe_composed(model_dir, gate2_dir, int(gate2["n_star"]))
    if probe is not None:
        composed["gate2_75_probe_standins"] = probe
    # Realised matching on the confirmatory blocks, per core reference.
    realised_gap = {}
    conf = composed.get("confirmatory_blocks")
    if conf:
        ia = (conf["realised"].get("A") or {}).get("iota")
        for slot in ("R1", "R2", "R3"):
            got = conf["realised"].get(slot)
            if got and got.get("iota") is not None and ia is not None:
                realised_gap[slot] = {
                    "candidate": f"{got['kind']}:{got['severity']}",
                    "calibration_iota": (by_label.get(
                        f"{got['kind']}:{got['severity']}") or {}).get("iota"),
                    "realised_iota": got["iota"], "realised_iota_a": ia,
                    "realised_gap": abs(got["iota"] - ia),
                    "exceeds_0_15": abs(got["iota"] - ia) > 0.15}

    final = signed["final"]
    delta_r_rows = ([{k: s.get(k) for k in (
        "member", "configuration", "estimate", "simultaneous_lower",
        "simultaneous_upper", "status", "claim_level")}
        for s in final.get("results", [])
        if isinstance(s, dict) and s.get("member") in (
            "Delta_R", "D(B<-A)", "D(B<-R1)", "D(B<-R2)", "D(B<-R3)")]
        if final else [])

    return {
        "tree": label, "model_key": model_key, "study_id": gate2.get(
            "study_id"), "producing_commit": gate2.get("producing_commit"),
        "gate2_record": str(gate2_dir / STAGE_FILES["gate2"][1]),
        "gate2_record_sha256": impact._sha256(
            gate2_dir / STAGE_FILES["gate2"][1]),
        "m_star": m_star, "n_star": gate2["n_star"],
        "iota_a": iota_a, "solo_a": solo_a,
        "iota_a_unconstrained_basis": iota_a_unc,
        "iota_a_prescreen": iota_a_prescreen,
        "iota_a_by_split": gate2.get("iota_a_by_split"),
        "chance_basis": gates_run._chance_basis(unconstrained),
        "eligibility_formulation": formulation,
        "n_candidates": len(rows), "n_withheld": len(withheld["pooled"]),
        "coverage_calibrated": {k: coverage[k] for k in (
            "conditions", "core_met", "spectrum_met", "core_failed",
            "spectrum_failed", "n_eligible", "n_withheld_degenerate",
            "n_coordinate_undefined", "certified_conditions",
            "conditions_at_prescreen_iota_a",
            "conditions_moved_by_the_reference_point",
            "conditions_moved_by_the_basis", "iota_a_movement")},
        "coverage_realised": coverage["realised"],
        "signed_gate3c": (None if signed["gate3c"] is None else {
            "admitted_arms": signed["gate3c"].get("admitted_arms"),
            "identification_statuses": signed["gate3c"].get(
                "identification_statuses"),
            "spectrum_failures": signed["gate3c"].get("spectrum_failures")}),
        "signed_gate3b_slot_map": (None if signed["gate3b"] is None
                                   else signed["gate3b"]["slot_map"]),
        "selection_corrected": {
            "slot_map": chosen["slot_map"],
            "identification_statuses": chosen["identification_statuses"],
            "core_references": core_detail,
            "qualified_families_ranked": chosen["core"]["qualified_families"],
            "dropped": chosen["core"]["dropped"],
            "spectrum_identified": chosen["core"]["spectrum_identified"],
            "spectrum_exhausted": chosen["core"].get("spectrum_exhausted",
                                                     False),
            "spectrum_attempts": spectrum_attempts,
            "backups": backup_detail,
            "support_met": report["support_met"],
            "support_failures": report["failures"],
            "spectrum_met": report["spectrum_met"],
            "spectrum_failures": report["spectrum_failures"],
            "arms": sup["arms"],
            "realised": report["realised"],
        },
        "c4": c4, "c4_summary": c4_summary, "attrition": attrition,
        "monotonicity": monotonic,
        "nearby": nearby, "spread": spread,
        "rungs": rungs,
        "composed": composed,
        "realised_gap_confirmatory": realised_gap,
        "final_report_rows": delta_r_rows,
        "seconds": round(time.time() - t0, 1),
    }


def _job(job: tuple[str, pathlib.Path]) -> dict[str, Any] | None:
    return analyse(*job)


# ---------------------------------------------------------------- plots

def _plots(results: list[dict[str, Any]], out: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plots = out / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    tier_colour = {1: "#1f77b4", 2: "#2ca02c", 3: "#7f7f7f"}

    for r in results:
        tag = f"{r['tree']}_{r['model_key']}"
        iota_a = r["iota_a"]
        rungs = [x for x in r["rungs"] if x["iota"] is not None]
        families = sorted({x["family"] for x in rungs}, key=_family_order)
        y_of = {f: i for i, f in enumerate(families)}

        # ---- 1. landscape
        fig, ax = plt.subplots(figsize=(13, 0.32 * len(families) + 2.6))
        ax.axvspan(iota_a - 0.10, iota_a + 0.10, color="#ffe9a8", alpha=0.6,
                   lw=0, label="±0.10 (§13.8 caliper)")
        ax.axvspan(iota_a - 0.15, iota_a - 0.10, color="#fff4d6", alpha=0.6,
                   lw=0)
        ax.axvspan(iota_a + 0.10, iota_a + 0.15, color="#fff4d6", alpha=0.6,
                   lw=0, label="±0.15 (§12.6 C3/C7)")
        ax.axvline(iota_a, color="k", lw=1.4, label=f"ι_A = {iota_a:.3f}")
        ax.axvline(r["iota_a_unconstrained_basis"], color="k", lw=0.8,
                   ls=":", label="ι_A on the unconstrained-cell basis")
        x_floor = -0.28
        for x in rungs:
            y = y_of[x["family"]] + (x["severity"] % 5 - 2) * 0.09
            col = tier_colour[x["structural_tier"]]
            xi = max(x["iota"], x_floor)
            off_scale = x["iota"] < x_floor
            if not x["eligible_12_6"]:
                ax.scatter(xi, y, s=22, facecolors="none",
                           edgecolors=col, lw=0.8, alpha=0.7, zorder=2,
                           marker="<" if off_scale else "o")
            elif x["v_r_passed"]:
                ax.scatter(xi, y, s=42, c=col, marker="o", zorder=3)
            elif x["spectrum_eligible_registered"]:
                ax.scatter(xi, y, s=34, c=col, marker="D", zorder=3,
                           alpha=0.9)
            else:
                ax.scatter(xi, y, s=22, c=col, alpha=0.35, zorder=2,
                           marker="<" if off_scale else "o")
            ax.annotate(str(x["severity"]), (xi, y), fontsize=5.5,
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", color=col, alpha=0.9)
        for e in r["selection_corrected"]["core_references"]:
            ax.scatter(e["iota"], y_of[e["family"]], s=260, marker="*",
                       facecolors="none", edgecolors="red", lw=1.6, zorder=5)
            ax.annotate(f"{e['slot']}={e['candidate']}", (e["iota"],
                        y_of[e["family"]]), fontsize=7, color="red",
                        xytext=(6, -9), textcoords="offset points")
        for b in r["selection_corrected"]["backups"]:
            if b.get("iota") is None or b["family"] not in y_of:
                continue
            ax.scatter(b["iota"], y_of[b["family"]], s=200, marker="s",
                       facecolors="none", edgecolors="purple", lw=1.4,
                       zorder=5)
            ax.annotate(f"backup {b['family']}:{b['severity']}"
                        + ("" if b["admitted_full_v_r"] else
                           " (fails full V(R))"),
                        (b["iota"], y_of[b["family"]]), fontsize=7,
                        color="purple", xytext=(6, 5),
                        textcoords="offset points")
        ax.set_yticks(range(len(families)))
        ax.set_yticklabels([f"{f} (T{FAMILIES[f].structural_tier}, "
                            f"{FAMILIES[f].feature_group})"
                            for f in families], fontsize=7)
        ax.set_xlabel("corrected ι(R) = (p_solo − κ)/(1 − κ), κ on the "
                      "unconstrained cell (pooled 192 topics × 4 draws)")
        ax.set_xlim(-0.3, 1.02)
        ax.text(-0.29, -0.6, "◄ ι < −0.28 clipped (Tier-3 rungs with κ "
                "near 1: stating the constraint hurt)", fontsize=6,
                color="#555")
        ax.grid(axis="x", lw=0.3, alpha=0.5)
        ax.invert_yaxis()
        c4s = r["c4_summary"]["calibrated_corrected"]
        ax.set_title(
            f"[{r['tree']}] {r['model_key']}  m*={r['m_star']}  — reference "
            f"difficulty landscape (DIAGNOSTIC, corrected κ basis)\n"
            f"eligible rungs {r['spread']['n_eligible']} "
            f"({r['spread']['n_below']} below / {r['spread']['n_above']} "
            f"above A); C4 straddling groups "
            f"{c4s['n_straddling_groups']}/{c4s['required']} "
            f"{'MET' if c4s['c4_met'] else 'NOT MET'}; "
            f"within ±0.10: {r['nearby']['0.10']['eligible_rungs']} eligible "
            f"rungs, {r['nearby']['0.10']['v_r_qualified_rungs']} pass full "
            f"V(R)", fontsize=9)
        handles = [
            Line2D([], [], marker="o", color="w", markerfacecolor="#1f77b4",
                   markersize=7, label="eligible & passes full V(R) (core)"),
            Line2D([], [], marker="D", color="w", markerfacecolor="#1f77b4",
                   markersize=6, label="eligible & spectrum-eligible "
                                       "(V(R) minus V_diff)"),
            Line2D([], [], marker="o", color="w", markerfacecolor="#1f77b4",
                   alpha=0.35, markersize=6, label="eligible (§12.6) only"),
            Line2D([], [], marker="o", color="#1f77b4", markerfacecolor="none",
                   ls="", markersize=6, label="ineligible (solo ∉ [0.10,"
                                              "0.90] or vacuity)"),
            Line2D([], [], marker="*", color="red", markerfacecolor="none",
                   ls="", markersize=12, label="selected R1/R2/R3"),
            Line2D([], [], marker="s", color="purple", markerfacecolor="none",
                   ls="", markersize=9, label="frozen backup family"),
            Line2D([], [], color="#1f77b4", lw=4, label="Tier 1"),
            Line2D([], [], color="#2ca02c", lw=4, label="Tier 2"),
            Line2D([], [], color="#7f7f7f", lw=4, label="Tier 3"),
        ]
        h2, _l2 = ax.get_legend_handles_labels()
        ax.legend(handles=h2 + handles, fontsize=6.5, loc="lower left",
                  ncol=2, framealpha=0.9)
        fig.tight_layout()
        p = plots / f"landscape_{tag}.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        written.append(str(p.relative_to(out)))

        # ---- 2. per-family ladders
        n = len(families)
        ncol = 6
        nrow = math.ceil(n / ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(2.6 * ncol, 2.3 * nrow),
                                 squeeze=False)
        c4f = r["c4"]["calibrated_corrected"]
        for i, fam in enumerate(families):
            ax = axes[i // ncol][i % ncol]
            fam_rows = sorted((x for x in rungs if x["family"] == fam),
                              key=lambda x: x["severity"])
            xs = [x["severity"] for x in fam_rows]
            ys = [x["iota"] for x in fam_rows]
            col = tier_colour[FAMILIES[fam].structural_tier]
            ax.plot(xs, ys, "-", color=col, lw=0.8, alpha=0.6)
            for x in fam_rows:
                if x["eligible_12_6"]:
                    ax.scatter(x["severity"], x["iota"], s=26, c=col,
                               zorder=3)
                else:
                    ax.scatter(x["severity"], x["iota"], s=26,
                               facecolors="none", edgecolors=col, zorder=3)
                if x["is_core_reference"]:
                    ax.scatter(x["severity"], x["iota"], s=160, marker="*",
                               facecolors="none", edgecolors="red", lw=1.3,
                               zorder=4)
            ax.axhline(iota_a, color="k", lw=1)
            ax.axhspan(iota_a - 0.10, iota_a + 0.10, color="#ffe9a8",
                       alpha=0.5, lw=0)
            st = c4f.get(fam) or {}
            ax.set_title(f"{fam} T{FAMILIES[fam].structural_tier} "
                         f"{FAMILIES[fam].form}\n"
                         f"span {st.get('span', 0):.2f} elig {st.get('n_eligible', 0)}"
                         f"/{st.get('n_measured', 0)} "
                         f"{'C4 ok' if st.get('c4_met') else st.get('first_deficiency')}",
                         fontsize=7)
            ax.set_ylim(-0.05, 1.05)
            ax.tick_params(labelsize=6)
            ax.grid(lw=0.3, alpha=0.5)
        for j in range(n, nrow * ncol):
            axes[j // ncol][j % ncol].axis("off")
        fig.suptitle(f"[{r['tree']}] {r['model_key']} — per-family severity "
                     f"ladders (y = corrected ι; line = ι_A; band = ±0.10; "
                     f"hollow = ineligible; ★ = core reference). DIAGNOSTIC",
                     fontsize=9)
        fig.tight_layout()
        p = plots / f"ladders_{tag}.png"
        fig.savefig(p, dpi=140)
        plt.close(fig)
        written.append(str(p.relative_to(out)))

    # ---- 3. C4 overview across replications
    fig, axes = plt.subplots(len(results), 1,
                             figsize=(13, 2.2 * len(results) + 1),
                             squeeze=False)
    for ax, r in zip(axes[:, 0], results):
        table = r["c4"]["calibrated_corrected"]
        fams = [f for f in table if table[f]["n_eligible"] > 0]
        for i, f in enumerate(fams):
            st = table[f]
            col = ("#2ca02c" if st["c4_met"] else "#d62728"
                   if st["straddles"] else "#7f7f7f")
            ax.plot([i, i], [st["min_iota"], st["max_iota"]], color=col,
                    lw=3, solid_capstyle="butt")
            ax.scatter([i] * st["n_eligible"],
                       [x["iota"] for x in r["rungs"] if x["family"] == f
                        and x["eligible_12_6"] and x["iota"] is not None],
                       s=8, c="k", zorder=3)
        ax.axhline(r["iota_a"], color="k", lw=1)
        ax.set_xticks(range(len(fams)))
        ax.set_xticklabels(fams, fontsize=6.5, rotation=60)
        ax.set_ylim(-0.3, 1)
        s = r["c4_summary"]["calibrated_corrected"]
        ax.set_ylabel("corrected ι", fontsize=7)
        ax.set_title(f"[{r['tree']}] {r['model_key']}: eligible span per "
                     f"family (green = C4 group met; red = straddles but "
                     f"fails; grey = one side only). straddling groups "
                     f"{s['n_straddling_groups']}/{s['required']}", fontsize=8)
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    p = plots / "c4_spans_all_replications.png"
    fig.savefig(p, dpi=140)
    plt.close(fig)
    written.append(str(p.relative_to(out)))

    # ---- 5. composed D(B<-R) vs corrected iota
    with_composed = [r for r in results if r["composed"]]
    if with_composed:
        for basis, title in (("confirmatory_blocks", ("confirmatory blocks "
                              "(384 blocks × 8 draws where complete)")),
                             ("gate4_24_topics", ("Gate 4 composed set "
                              "(24 topics × 4 draws)"))):
            fig, ax = plt.subplots(figsize=(11, 6.5))
            markers = ["o", "s", "^", "D", "v", "P"]
            colours = {C.OUTCOME_FIRST: "#d62728", C.OUTCOME_SECOND: "#1f77b4"}
            any_point = False
            for mi, r in enumerate(with_composed):
                comp = r["composed"].get(basis)
                if not comp:
                    continue
                by_label = {x["candidate"]: x for x in r["rungs"]}
                slot_map = (r["signed_gate3b_slot_map"]
                            or r["selection_corrected"]["slot_map"])
                for d in comp["delivery_loss"].values():
                    x_slot = d["companion"]
                    # calibration iota (corrected) for R slots; A at iota_A
                    if x_slot == "A":
                        iota, lab = r["iota_a"], "A"
                    elif x_slot in slot_map:
                        kind, sev = slot_map[x_slot]
                        lab = f"{kind}:{sev}"
                        iota = (by_label.get(lab) or {}).get("iota")
                    else:
                        continue
                    if iota is None:
                        continue
                    any_point = True
                    col = colours[d["configuration"]]
                    ax.errorbar(iota, d["estimate"], yerr=1.96 * d["se_blocks"],
                                fmt=markers[mi % len(markers)], color=col,
                                mfc=("none" if x_slot == "A" else col),
                                ms=(11 if x_slot == "A" else 8),
                                capsize=2, lw=0.8, alpha=0.9)
                    ax.annotate(f"{x_slot}={lab}" if x_slot != "A"
                                else f"A ({r['model_key']})",
                                (iota, d["estimate"]), fontsize=6,
                                xytext=(5, 3), textcoords="offset points")
            if any_point:
                ax.axhline(0, color="k", lw=0.6)
                ax.set_xlabel("corrected ι of the companion on the "
                              "calibration table (A at ι_A)")
                ax.set_ylabel("D(B ← X) = P(B pass | B solo) − P(B pass | "
                              "B + X)  [±1.96 SE over blocks]")
                handles = [Line2D([], [], color=colours[C.OUTCOME_FIRST],
                                  marker="o", ls="", label="outcome_first "
                                  "(B stated first: B+X)"),
                           Line2D([], [], color=colours[C.OUTCOME_SECOND],
                                  marker="o", ls="", label="outcome_second "
                                  "(B stated second: X+B)"),
                           Line2D([], [], color="k", marker="o",
                                  markerfacecolor="none", ls="", ms=10,
                                  label="X = A (hollow)")]
                for mi, r in enumerate(with_composed):
                    if r["composed"].get(basis):
                        handles.append(Line2D(
                            [], [], color="k", marker=markers[mi % len(
                                markers)], ls="",
                            label=f"[{r['tree']}] {r['model_key']}"))
                ax.legend(handles=handles, fontsize=7, loc="best")
                ax.set_title(f"Existing composed outcomes: D(B←X) against "
                             f"companion difficulty — {title}. DIAGNOSTIC; "
                             "only companions with stored B+X / X+B rows",
                             fontsize=9)
                ax.grid(lw=0.3, alpha=0.5)
                fig.tight_layout()
                p = plots / f"composed_D_vs_iota_{basis}.png"
                fig.savefig(p, dpi=150)
                written.append(str(p.relative_to(out)))
            plt.close(fig)

        # ---- 5b. secondary coordinate: D(B<-X) vs raw solo compliance,
        # where the probe stand-ins (no registered iota) can be shown.
        fig, ax = plt.subplots(figsize=(11, 6.5))
        markers = ["o", "s", "^", "D", "v", "P"]
        colours = {C.OUTCOME_FIRST: "#d62728", C.OUTCOME_SECOND: "#1f77b4"}
        any_point = False
        for mi, r in enumerate(with_composed):
            by_label = {x["candidate"]: x for x in r["rungs"]}
            slot_map = (r["signed_gate3b_slot_map"]
                        or r["selection_corrected"]["slot_map"])
            for basis, style in (("confirmatory_blocks", 1.0),
                                 ("gate2_75_probe_standins", 0.45)):
                comp = r["composed"].get(basis)
                if not comp:
                    continue
                for d in comp["delivery_loss"].values():
                    x_slot = d["companion"]
                    if x_slot == "A":
                        solo = r["solo_a"]
                        lab = "A"
                    elif x_slot in slot_map:
                        k, sv = slot_map[x_slot]
                        lab = f"{k}:{sv}"
                        solo = (by_label.get(lab) or {}).get("solo")
                    else:
                        got = comp["realised"].get(x_slot) or {}
                        solo = got.get("solo")
                        lab = f"{got.get('kind')}:{got.get('severity')} (probe)"
                    if solo is None:
                        continue
                    any_point = True
                    col = colours[d["configuration"]]
                    ax.errorbar(solo, d["estimate"], yerr=1.96 * d["se_blocks"],
                                fmt=markers[mi % len(markers)], color=col,
                                mfc=("none" if x_slot == "A" else col),
                                ms=(11 if x_slot == "A" else 8), capsize=2,
                                lw=0.8, alpha=style)
                    ax.annotate(f"{x_slot}={lab}" if x_slot != "A"
                                else f"A ({r['model_key']})",
                                (solo, d["estimate"]), fontsize=6,
                                xytext=(5, 3), textcoords="offset points",
                                alpha=style)
        if any_point:
            ax.axhline(0, color="k", lw=0.6)
            ax.set_xlabel("raw solo compliance of the companion (§13.2's "
                          "registered SECONDARY coordinate); probe stand-ins "
                          "faded (192 topics × 4 draws, B-solo from Gate 2)")
            ax.set_ylabel("D(B ← X)  [±1.96 SE over blocks]")
            handles = [Line2D([], [], color=colours[C.OUTCOME_FIRST],
                              marker="o", ls="", label="outcome_first (B+X)"),
                       Line2D([], [], color=colours[C.OUTCOME_SECOND],
                              marker="o", ls="", label="outcome_second (X+B)"),
                       Line2D([], [], color="k", marker="o",
                              markerfacecolor="none", ls="", ms=10,
                              label="X = A (hollow)")]
            for mi, r in enumerate(with_composed):
                handles.append(Line2D([], [], color="k", marker=markers[
                    mi % len(markers)], ls="",
                    label=f"[{r['tree']}] {r['model_key']}"))
            ax.legend(handles=handles, fontsize=7, loc="best")
            ax.set_title("Existing composed outcomes on the secondary "
                         "coordinate: confirmatory blocks (solid) and Gate "
                         "2.75 probe stand-ins (faded; NOT references, no "
                         "registered ι). DIAGNOSTIC", fontsize=9)
            ax.grid(lw=0.3, alpha=0.5)
            fig.tight_layout()
            p = plots / "composed_D_vs_raw_solo.png"
            fig.savefig(p, dpi=150)
            written.append(str(p.relative_to(out)))
        plt.close(fig)

    # ---- 4. nearby support summary
    fig, ax = plt.subplots(figsize=(11, 4.5))
    labels = [f"[{r['tree']}]\n{r['model_key']}" for r in results]
    xs = list(range(len(results)))
    for k, (cal, off) in enumerate(zip(("0.05", "0.10", "0.15"),
                                       (-0.25, 0.0, 0.25))):
        ax.bar([x + off for x in xs],
               [r["nearby"][cal]["eligible_rungs"] for r in results],
               width=0.24, alpha=0.35, color=f"C{k}",
               label=f"eligible rungs within ±{cal}")
        ax.bar([x + off for x in xs],
               [r["nearby"][cal]["v_r_qualified_rungs"] for r in results],
               width=0.24, color=f"C{k}",
               label=f"…of which pass full V(R) (±{cal})")
    ax2 = ax.twinx()
    ax2.plot(xs, [r["spread"]["max_iota"] - r["spread"]["min_iota"]
                  for r in results], "k*", ms=10,
             label="total eligible ι spread (right axis)")
    ax2.plot(xs, [(r["spread"]["spectrum_eligible_registered_range"][1] or 0)
                  - (r["spread"]["spectrum_eligible_registered_range"][0]
                     or 0) for r in results], "kx", ms=9,
             label="ι spread of spectrum-eligible rungs (registered V_stab)")
    ax2.set_ylim(0, 1)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("rungs")
    ax.legend(fontsize=6.5, loc="upper left", ncol=2)
    ax2.legend(fontsize=6.5, loc="upper right")
    ax.set_title("Local support near A versus global difficulty spread "
                 "(DIAGNOSTIC, corrected κ basis)", fontsize=9)
    fig.tight_layout()
    p = plots / "nearby_support_vs_spread.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    written.append(str(p.relative_to(out)))
    return written


# --------------------------------------------------------------- report

def _fmt(v, nd=3):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _md(results: list[dict[str, Any]], plots: list[str]) -> str:
    L = [("# Reference-support landscape on the corrected chance basis "
         "(DIAGNOSTIC)"), "",
         ("> Generated by `dci1/tools/v7_reference_support_landscape.py`. "
         "Every number is in `landscape.json`. **Exploratory / diagnostic**: "
         "reconstructed read-only from stored Gate-2 calibration rows and "
         "the grid runs' unconstrained cells, with `chance_compliance` "
         "measured as §13.2 registers it (never the recorded 0.0 column). "
         "Nothing here is a confirmatory claim; development-tree numbers "
         "are development numbers."), ""]
    L += ["## Per replication: ι_A, eligibility, C1–C8, selection", "",
          ("| tree | model | m* | ι_A (rec.) | ι_A (unc.) | ι_A pre-screen | "
          "cand. | eligible (§12.6) | below/above A | pass full V(R) | "
          "spectrum-elig. (reg.) | C1–C8 (calibrated, corrected) | C4 groups | "
          "R1/R2/R3 (corrected) | signed R1/R2/R3 | backups | arms |"),
          "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---|---|---|---|---|"]
    for r in results:
        cc = r["coverage_calibrated"]["conditions"]
        conds = "".join(("✓" if cc[c] else "✗") for c in C.COVERAGE_CONDITIONS)
        s = r["c4_summary"]["calibrated_corrected"]
        core = ", ".join(f"{e['slot']}={e['candidate']}"
                         for e in r["selection_corrected"]["core_references"])
        signed_map = r["signed_gate3b_slot_map"] or {}
        signed_core = ", ".join(f"{k}={v[0]}:{v[1]}" for k, v in sorted(
            signed_map.items()) if k in ("R1", "R2", "R3"))
        L.append(
            f"| {r['tree']} | {r['model_key']} | {r['m_star']} | "
            f"{r['iota_a']:.3f} | {r['iota_a_unconstrained_basis']:.3f} | "
            f"{r['iota_a_prescreen']:.3f} | {r['n_candidates']} | "
            f"{r['spread']['n_eligible']} | {r['spread']['n_below']}/"
            f"{r['spread']['n_above']} | {r['spread']['n_v_r_qualified']} | "
            f"{r['spread']['n_spectrum_eligible_registered']} | {conds} | "
            f"{s['n_straddling_groups']}/{s['required']} | {core} | "
            f"{signed_core or '—'} | "
            f"{', '.join(b['family'] for b in r['selection_corrected']['backups']) or '—'} | "
            f"{r['selection_corrected']['arms']} |")
    L += ["", ("C1–C8 order: C1 straddle, C2 ≥3 T1/2 groups each side, C3 ≥8 "
          "rungs within 0.15 from ≥4 groups, C4 ≥6 straddling groups (≥3 "
          "eligible rungs, span ≥0.40), C5 ≥16 eligible, C6 ≥8 T1/2 families "
          "from ≥6 groups, C7 Tier-3 budget within 0.15, C8 ≥3 Tier-2 rungs "
          "from 3 groups."), ""]

    L += ["## Core references and local support", ""]
    for r in results:
        L += [(f"### [{r['tree']}] {r['model_key']}  (ι_A = {r['iota_a']:.4f}, "
              f"p_solo(A) = {r['solo_a']:.4f})"), "",
              ("| slot | candidate | tier | group | role | ι(R) | |ι−ι_A| | side "
              "| κ | p_solo | lift | vacuity | κ(R|B) | §12.6 eligible | full "
              "V(R) | §13.7 stable | ι on split A / B |"),
              "|---|---|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|---|"]
        for e in r["selection_corrected"]["core_references"]:
            ps = e["stability"]["per_split_iota"]
            L.append(
                f"| {e['slot']} | {e['candidate']} | {e['structural_tier']} | "
                f"{e['feature_group']} | {e['discourse_role']} | "
                f"{e['iota']:.4f} | {e['distance']:.4f} | {e['side']} | "
                f"{e['chance']:.3f} | {e['solo']:.3f} | {e['lift']:.3f} | "
                f"{e['vacuity']:.3f} | {_fmt(e['kappa_under_b'])} | "
                f"{e['eligible_12_6']} | {e['v_r_passed']} | "
                f"{e['stability']['passed']} | "
                f"{_fmt(ps.get(C.CALIBRATION_A))} / "
                f"{_fmt(ps.get(C.CALIBRATION_B))} |")
        nb = r["nearby"]
        if r["selection_corrected"]["backups"]:
            L += ["", ("Frozen backups (§13.15; from Gate 2.5's qualified "
                  "families in sorted order, never substituted):"), ""]
            for b in r["selection_corrected"]["backups"]:
                L.append(f"- {b['family']}: nearest Gate-2.5 rung "
                         f"{b['nearest_gate2_5_rung']} at ι {_fmt(b['iota'], 4)} "
                         f"(|ι−ι_A| {_fmt(b['distance'], 4)}); admitted under "
                         f"the full V(R) at Gate 3B: {b['admitted_full_v_r']}"
                         + ("" if b["admitted_full_v_r"] else
                            f" (first failing: {b['nearest_rung_first_failing']})"))
        L += ["", ("| caliper | eligible rungs | families | Tier-1/2 families "
              "| pass full V(R) | V(R) families | spectrum-eligible (reg.) | "
              "below / above |"), "|---|---:|---:|---:|---:|---:|---:|---|"]
        for cal in ("0.05", "0.10", "0.15"):
            x = nb[cal]
            L.append(f"| ±{cal} | {x['eligible_rungs']} | "
                     f"{len(x['eligible_families'])} | "
                     f"{len(x['eligible_tier12_families'])} | "
                     f"{x['v_r_qualified_rungs']} | "
                     f"{len(x['v_r_qualified_families'])} | "
                     f"{x['spectrum_eligible_rungs']} | {x['below']} / "
                     f"{x['above']} |")
        sp = r["spread"]
        L += ["", (f"Eligible ι range [{_fmt(sp['min_iota'])}, "
              f"{_fmt(sp['max_iota'])}] over {sp['n_eligible']} rungs; "
              f"spectrum-eligible under the registered V_stab (which folds "
              f"V_diff in per split): {sp['n_spectrum_eligible_registered']} "
              f"rungs in [{_fmt(sp['spectrum_eligible_registered_range'][0])}, "
              f"{_fmt(sp['spectrum_eligible_registered_range'][1])}]; with "
              f"V_diff unfolded (diagnostic what-if): "
              f"{sp['n_spectrum_eligible_unfolded_diagnostic']} rungs in "
              f"[{_fmt(sp['spectrum_eligible_unfolded_range'][0])}, "
              f"{_fmt(sp['spectrum_eligible_unfolded_range'][1])}]."), ""]
        if r["selection_corrected"]["spectrum_attempts"]:
            L += [("Spectrum attempt per qualified family (§13.12 needs one "
                  "spectrum-eligible rung strictly below and one strictly "
                  "above ι_A, excluding the core rung):"), "",
                  ("| family | core rung (ι, dist) | registered pool below | "
                  "registered pool above | triple | unfolded pool below | "
                  "unfolded pool above | family C4 |"),
                  "|---|---|---|---|---|---|---|---|"]
            for a in r["selection_corrected"]["spectrum_attempts"]:
                fc = a["family_c4"] or {}
                L.append(
                    f"| {a['family']} | {a['core_severity']} "
                    f"({_fmt(a['core_iota'])}, {_fmt(a['core_distance'])}) | "
                    f"{a['registered_pool_below'] or '—'} | "
                    f"{a['registered_pool_above'] or '—'} | "
                    f"{'yes' if a['triple'] else 'none'} | "
                    f"{a['unfolded_pool_below'] or '—'} | "
                    f"{a['unfolded_pool_above'] or '—'} | "
                    f"{'met' if fc.get('c4_met') else fc.get('first_deficiency')} "
                    f"(span {_fmt(fc.get('span'), 2)}, n={fc.get('n_eligible')}) |")
            L.append("")

    L += [("## C4 diagnostic (registered construction, calibrated basis, "
          "corrected κ)"), ""]
    for r in results:
        table = r["c4"]["calibrated_corrected"]
        s = r["c4_summary"]
        L += [f"### [{r['tree']}] {r['model_key']}", "",
              (f"Straddling groups: **{s['calibrated_corrected']['n_straddling_groups']} "
              f"of {s['calibrated_corrected']['required']} required** "
              f"({s['calibrated_corrected']['straddling_groups']}). "
              f"On the recorded κ=0 table: "
              f"{s['calibrated_recorded_kappa0']['n_straddling_groups']}; "
              f"at the unconstrained-basis ι_A: "
              f"{s['calibrated_corrected_at_unconstrained_iota_a']['n_straddling_groups']}; "
              f"pre-screen certificate (24 topics × 1 draw, all carried rungs): "
              f"{s['prescreen_certified']['n_straddling_groups']}; pre-screen "
              f"restricted to the calibrated rungs: "
              f"{s['prescreen_restricted_to_calibrated_rungs']['n_straddling_groups']}; "
              f"calibrated raw pool ignoring eligibility: "
              f"{s['calibrated_raw_pool_ignoring_eligibility']['n_straddling_groups']}; "
              f"spectrum-qualified rungs only (registered): "
              f"{s['calibrated_spectrum_qualified_registered']['n_straddling_groups']}; "
              f"spectrum-qualified with V_diff unfolded (diagnostic): "
              f"{s['calibrated_spectrum_qualified_unfolded_diagnostic']['n_straddling_groups']}."),
              "",
              (f"First deficiency by family: "
              f"{s['calibrated_corrected']['first_deficiency_by_family']}. "
              f"Closest to passing: {s['calibrated_corrected']['closest_to_passing']}."),
              "",
              (f"Descriptive relaxations (straddling groups if the span floor / "
              f"rung floor were): {s['calibrated_corrected']['relaxations_descriptive']}"),
              "",
              ("| family | tier | group | measured | eligible | min ι | max ι | "
              "span | below | above | straddles | ≥3 rungs | span ≥0.40 | C4 | "
              "first deficiency | ineligible rungs (reason) | pre-screen span "
              "(same rungs) | span all measured | Spearman(restrictiveness, ι) "
              "| inversions |"),
              "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|"]
        for fam, st in table.items():
            at = r["attrition"][fam]
            mo = r["monotonicity"].get(fam, {})
            inel = "; ".join(f"{k}: {v}" for k, v in st["ineligible"].items())
            L.append(
                f"| {fam} | {st['structural_tier']} | {st['feature_group']} | "
                f"{st['n_measured']} | {st['n_eligible']} | "
                f"{_fmt(st['min_iota'])} | {_fmt(st['max_iota'])} | "
                f"{st['span']:.3f} | {st['n_below']} | {st['n_above']} | "
                f"{st['straddles']} | {st['meets_rung_floor']} | "
                f"{st['meets_span']} | {'MET' if st['c4_met'] else 'no'} | "
                f"{st['first_deficiency'] or '—'} | {inel or '—'} | "
                f"{_fmt(at['prescreen_span_same_rungs'])} | "
                f"{_fmt(at['calibrated_span_all_measured'])} | "
                f"{_fmt(mo.get('spearman_restrictiveness_vs_iota'), 2)} | "
                f"{mo.get('adjacent_inversions')} |")
        L.append("")

    L += ["## Composed B+R outcomes that exist", ""]
    for r in results:
        if not r["composed"]:
            L.append(f"- [{r['tree']}] {r['model_key']}: **no composed B+R "
                     f"rows** (arms {(r['signed_gate3c'] or {}).get('admitted_arms')}).")
            continue
        L.append(f"### [{r['tree']}] {r['model_key']}")
        L.append("")
        for basis, comp in r["composed"].items():
            if comp is None:
                continue
            L.append(f"**{basis}** — {comp['n_rows']} rows, "
                     f"{comp['n_blocks']} blocks, companions "
                     f"{comp['companions']}"
                     + (f", complete={comp.get('complete')}"
                        if "complete" in comp else "") + ".")
            L.append("")
            L += [("| contrast | configuration | estimate | ±1.96 SE | "
                  "P(B|solo) | P(B|composed) | companion | calibration ι "
                  "(corrected) | realised ι on these blocks |"),
                  "|---|---|---:|---:|---:|---:|---|---:|---:|"]
            by_label = {x["candidate"]: x for x in r["rungs"]}
            slot_map = (r["signed_gate3b_slot_map"]
                        or r["selection_corrected"]["slot_map"])
            for key, d in sorted(comp["delivery_loss"].items()):
                x = d["companion"]
                if x == "A":
                    lab, iota = "A", r["iota_a"]
                elif x in slot_map:
                    k, sv = slot_map[x]
                    lab = f"{k}:{sv}"
                    iota = (by_label.get(lab) or {}).get("iota")
                else:
                    st = (comp.get("standins") or {})
                    lab = st.get("PS" + x[1], x) if x.startswith("P") else x
                    iota = None
                real = (comp["realised"].get(x) or {}).get("iota")
                L.append(f"| D(B←{x}) | {d['configuration']} | "
                         f"{d['estimate']:+.4f} | {1.96 * d['se_blocks']:.4f} | "
                         f"{d['p_b_solo']:.3f} | {d['p_b_composed']:.3f} | "
                         f"{lab} | {_fmt(iota, 4)} | {_fmt(real, 4)} |")
            L.append("")
        if r.get("realised_gap_confirmatory"):
            L += [("Realised matching on the confirmatory blocks (§13.8's "
                  "realised-gap rule, 0.15):"), "",
                  ("| slot | candidate | calibration ι | realised ι | realised "
                  "ι_A | realised gap | > 0.15 |"),
                  "|---|---|---:|---:|---:|---:|---|"]
            for slot, g in sorted(r["realised_gap_confirmatory"].items()):
                L.append(f"| {slot} | {g['candidate']} | "
                         f"{_fmt(g['calibration_iota'], 4)} | "
                         f"{g['realised_iota']:.4f} | "
                         f"{g['realised_iota_a']:.4f} | "
                         f"{g['realised_gap']:.4f} | {g['exceeds_0_15']} |")
            L.append("")
        if r["final_report_rows"]:
            L.append("Final-report rows (production estimators, for "
                     "cross-check):")
            L.append("")
            L += [("| member | configuration | estimate | simultaneous "
                  "interval | status |"), "|---|---|---:|---|---|"]
            for s in r["final_report_rows"]:
                L.append(f"| {s['member']} | {s['configuration']} | "
                         f"{_fmt(s['estimate'], 4)} | "
                         f"[{_fmt(s['simultaneous_lower'], 4)}, "
                         f"{_fmt(s['simultaneous_upper'], 4)}] | "
                         f"{s['status']} |")
            L.append("")
    L += ["## Plots", ""] + [f"- `{p}`" for p in plots] + [""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--replot", action="store_true",
                    help="re-render plots and REPORT.md from <out>/landscape.json")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    if args.replot:
        with open(out / "landscape.json") as f:
            payload = json.load(f)
        results = payload["results"]
        plots = _plots(results, out)
        (out / "REPORT.md").write_text(_md(results, plots))
        print(f"re-rendered {len(plots)} plots and REPORT.md")
        return 0
    jobs: list[tuple[str, pathlib.Path]] = []
    for spec in args.tree:
        label, _, path = spec.partition("=")
        root = pathlib.Path(path)
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if args.models and model_dir.name not in args.models:
                continue
            if (model_dir / STAGE_FILES["gate2"][0]
                    / STAGE_FILES["gate2"][1]).exists():
                jobs.append((label, model_dir))
    if args.workers <= 1:
        outcomes = [analyse(*job) for job in jobs]
    else:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(args.workers,
                                 mp_context=mp.get_context("spawn")) as pool:
            outcomes = list(pool.map(_job, jobs))
    results = [r for r in outcomes if r is not None]
    for r in results:
        s = r["c4_summary"]["calibrated_corrected"]
        print(f"{r['tree']}/{r['model_key']}: eligible "
              f"{r['spread']['n_eligible']}, C4 {s['n_straddling_groups']}/"
              f"{s['required']}, core "
              f"{[e['candidate'] for e in r['selection_corrected']['core_references']]}, "
              f"composed {list(r['composed'])} ({r['seconds']} s)", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"generated_by": "dci1/tools/v7_reference_support_landscape.py",
               "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime()),
               "read_only": True, "diagnostic": True,
               "chance_basis": "§13.2 unconstrained cell (2026-08-29 "
                               "correction); the recorded 0.0 column is "
                               "used only where labelled kappa0",
               "results": results}
    (out / "landscape.json").write_text(json.dumps(payload, indent=1,
                                                   sort_keys=True))
    plots = _plots(results, out)
    (out / "REPORT.md").write_text(_md(results, plots))
    print(f"wrote {out / 'landscape.json'}, {out / 'REPORT.md'} and "
          f"{len(plots)} plots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
