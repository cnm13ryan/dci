#!/usr/bin/env python3
"""Validate the v8 candidate pipeline end to end and gather every result
into one report (synthetic cases here; the retrospective replays are read
from the JSON the other tools wrote).

    python3 tools/v8_pipeline_validation.py [--resamples 300]

Writes reports/dci1v8dev/pipeline_validation.{json,md}.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v4.errors import ProtocolError                                   # noqa: E402
from dci1v7.protocol import constants as C                                # noqa: E402
from dci1v7.stages.calibration_table import (                             # noqa: E402
    FORBIDDEN_CALIBRATION_FIELDS, load_calibration_table)
from dci1v8dev import rules as R                                          # noqa: E402
from dci1v8dev import wordings as W                                       # noqa: E402
from dci1v8dev.e2e import (                                               # noqa: E402
    FamilyTruth, World, run_candidate, truth_of, world_from_archetypes)
from dci1v8dev.simulate import A_CURVE_2507, A_CURVE_QWEN                 # noqa: E402
from dci1v8dev.simulate_wording import FLAT, STEEP, simulate_wording_case  # noqa: E402
from dci1v8dev.spectrum.design import spectrum_generation_cost            # noqa: E402

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev"
SRC = DCI1 / "src" / "dci1v8dev"


def _ladder(kind, values, reserve=()):
    from dci1v7.verifiers.constraints import LADDERS, RESERVES
    sev = list(LADDERS[kind]) + [q for q in RESERVES[kind] if q not in LADDERS[kind]]
    vals = list(values) + list(reserve)
    if len(vals) < len(sev):
        vals += [vals[-1]] * (len(sev) - len(vals))
    return {q: float(min(0.995, max(0.005, v))) for q, v in zip(sev, vals)}


def worlds() -> dict[str, World]:
    base = {"MK1": "wide", "MK2": "wide", "XC1": "wide", "MK5": "flat"}
    W_ = {}
    W_["wide"] = world_from_archetypes({**base, "MK3": "borderline", "MK6": "outlier"},
                                       a_curve=A_CURVE_QWEN, name="wide")
    W_["narrow"] = world_from_archetypes({"MK1": "narrow_noisy", "MK2": "narrow_noisy",
                                          "MK3": "narrow_noisy", "MK4": "borderline"},
                                         a_curve=A_CURVE_QWEN, name="narrow")
    W_["flat"] = world_from_archetypes({"MK1": "flat", "MK2": "flat", "MK3": "flat",
                                        "XC1": "flat"}, a_curve=A_CURVE_QWEN, name="flat")
    W_["one_sided"] = world_from_archetypes({"MK1": "one_sided", "MK2": "one_sided",
                                             "MK3": "one_sided", "MK4": "one_sided"},
                                            a_curve=A_CURVE_QWEN, name="one_sided")
    W_["outlier"] = world_from_archetypes({"MK1": "outlier", "MK2": "outlier",
                                           "MK3": "wide", "MK5": "flat"},
                                          a_curve=A_CURVE_QWEN, name="outlier")
    # 2507-like: every marker ladder too easy over q<=8, difficulty only in the reserve
    easy = [0.98, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.90]
    W_["too_easy_reserve"] = World(
        families={"MK1": FamilyTruth("MK1", _ladder("MK1", easy, [0.75, 0.55, 0.40, 0.30])),
                  "MK2": FamilyTruth("MK2", _ladder("MK2", easy, [0.72, 0.50, 0.38, 0.28])),
                  "MK3": FamilyTruth("MK3", _ladder("MK3", easy, [0.70, 0.52, 0.36, 0.25])),
                  "MK4": FamilyTruth("MK4", _ladder("MK4", [0.90, 0.85, 0.78, 0.70, 0.62, 0.52,
                                                            0.44, 0.36], [0.30, 0.25, 0.2, 0.15]))},
        a_curve=A_CURVE_2507, name="too_easy_reserve")
    # extremes survive, degenerates fail: a family whose easy end sits beyond
    # V_head's cap (0.93 solo, chance-free) and Tier-3 budget rungs that are
    # chance-dominated (kappa 0.80), vacuous (0.30) or degenerate (0.995)
    W_["extremes"] = World(
        families={"MK1": FamilyTruth("MK1", _ladder("MK1", [0.94, 0.93, 0.86, 0.76, 0.66,
                                                            0.55, 0.45, 0.35])),
                  "MK2": FamilyTruth("MK2", _ladder("MK2", [0.93, 0.90, 0.84, 0.75, 0.66,
                                                            0.56, 0.46, 0.34])),
                  "XC1": FamilyTruth("XC1", _ladder("XC1", [0.92, 0.88, 0.80, 0.70, 0.60,
                                                            0.50, 0.42, 0.34])),
                  "CR5": FamilyTruth("CR5", _ladder("CR5", [0.40, 0.55, 0.70, 0.80, 0.85, 0.90,
                                                            0.93, 0.95]), kappa=0.80),
                  "RF7": FamilyTruth("RF7", _ladder("RF7", [0.30, 0.45, 0.60, 0.70, 0.78, 0.84,
                                                            0.88, 0.90, 0.92, 0.93, 0.94, 0.95,
                                                            0.95]), vacuity=0.30),
                  "RF6": FamilyTruth("RF6", _ladder("RF6", [0.995] * 13), kappa=0.995)},
        a_curve=A_CURVE_QWEN, name="extremes")
    # wording confusion: MK3's ladder is steep, but two of the four v7 frames
    # are read with the marker absent
    conf = {"MK1": FamilyTruth("MK1", _ladder("MK1", [0.95, 0.90, 0.84, 0.76, 0.66, 0.55,
                                                       0.44, 0.34])),
            "MK2": FamilyTruth("MK2", _ladder("MK2", [0.94, 0.89, 0.82, 0.74, 0.65, 0.54,
                                                       0.45, 0.35])),
            "MK3": FamilyTruth("MK3", _ladder("MK3", [0.96, 0.92, 0.86, 0.78, 0.68, 0.56,
                                                       0.46, 0.36]), misread_frames=2),
            "MK6": FamilyTruth("MK6", _ladder("MK6", [0.95, 0.90, 0.83, 0.75, 0.66, 0.55,
                                                       0.45, 0.35]), misread_frames=2)}
    W_["wording_confusion_v7"] = World(families=conf, a_curve=A_CURVE_QWEN,
                                       name="wording_confusion_v7", instrument="v7")
    W_["wording_confusion_v8"] = World(families=conf, a_curve=A_CURVE_QWEN,
                                       name="wording_confusion_v8", instrument="v8")
    return W_


def _case_metrics(rec, truth) -> dict:
    fam_truth = truth["family_support"]
    accepted = set(rec["final_screen"]["statuses"]["SCREEN_ACCEPT"])
    tp = sum(1 for k, t in fam_truth.items() if t and k in accepted)
    fp = sum(1 for k, t in fam_truth.items() if not t and k in accepted)
    fn = sum(1 for k, t in fam_truth.items() if t and k not in accepted)
    local_found = sorted({lab.split(":")[0] for lab in rec["validity"]["local_valid"]})
    cov = rec["selection"]["coverage"]
    return {"identified": rec["identified"], "truly_identifiable": truth["identified"],
            "family_accept_tp": tp, "family_accept_fp": fp, "family_accept_fn": fn,
            "selected_families": rec["selection"]["families"],
            "n_spectrum_references": rec["selection"]["n_spectrum_references"],
            "offset_below": cov["offset_below"], "offset_above": cov["offset_above"],
            "total_span": cov["total_span"],
            "se_beta": cov["projection"]["se_beta"],
            "coverage_reasons": cov["reasons"],
            "local_families_found": local_found,
            "local_families_true": truth["local_families"],
            "local_recall": (len(set(local_found) & set(truth["local_families"]))
                            / len(truth["local_families"]) if truth["local_families"] else None),
            "core_references": rec["core_references"],
            "backups": rec["backups"]["backups"],
            "forwarded_rungs": len(rec["retention"]["forwarded"]),
            "extension_picks": rec["extension"]["picks"],
            "reserve_picks_in_rescreen": rec["final_screen"]["reserve_picks"],
            "costs": rec["costs"]}


def _strip(rec):
    return json.loads(json.dumps(rec, sort_keys=True))


def synthetic(resamples: int) -> dict:
    out = {}
    for name, w in worlds().items():
        t0 = time.time()
        rec = run_candidate(w, stability_resamples=resamples)
        truth = truth_of(w)
        out[name] = {"metrics": _case_metrics(rec, truth), "seconds": round(time.time() - t0, 1),
                     "final_statuses": rec["final_screen"]["statuses"],
                     "truth_family_support": truth["family_support"],
                     "spectrum_valid": rec["validity"]["spectrum_valid"],
                     "first_failing_spectrum": rec["validity"]["first_failing_spectrum"],
                     "selected_points": rec["selection"]["points"]}
        print(f"  {name}: identified={rec['identified']} (truth {truth['identified']}) "
              f"families={rec['selection']['families']} SE={out[name]['metrics']['se_beta']} "
              f"forwarded={len(rec['retention']['forwarded'])} [{time.time() - t0:.1f}s]", flush=True)
    return out


def invariances(resamples: int) -> dict:
    w = worlds()["wide"]
    a = _strip(run_candidate(w, stability_resamples=resamples))
    b = _strip(run_candidate(w, stability_resamples=resamples))
    order = list(reversed(sorted(w.families)))
    c = _strip(run_candidate(w, stability_resamples=resamples, family_order=order))
    # composed-outcome invariance: a world that differs only in interference
    fams = {k: FamilyTruth(**{**f.__dict__, "interference": 0.37}) for k, f in w.families.items()}
    d = _strip(run_candidate(World(families=fams, a_curve=w.a_curve, name=w.name,
                                   seed=w.seed), stability_resamples=resamples))
    # a different seed moves Monte Carlo numbers, never the rule
    e = _strip(run_candidate(World(families=w.families, a_curve=w.a_curve, name=w.name,
                                   seed=w.seed + 1), stability_resamples=resamples))
    # runtime refusal of a composed column
    refused = False
    try:
        load_calibration_table([{"kind": "MK1", "severity": 2, "split": "pooled",
                                 "model_key": "m", "solo_compliance": 0.8,
                                 "chance_compliance": 0.0, "solo_vacuity": 0.0,
                                 "composed_compliance": 0.5}],
                               model_key="m", m_star=9, split="pooled")
    except ProtocolError:
        refused = True
    # static: no rule module READS a composed quantity --- no attribute
    # access `.composed_...` and no subscript `["delta_r"]` on any object
    # names one of §13.11's forbidden fields (a local variable called
    # `pair` is a SplitPair, not a cell, and is not a read of a field)
    banned = set(FORBIDDEN_CALIBRATION_FIELDS)
    hits = []
    for path in sorted(list((SRC / "spectrum").glob("*.py")) + list((SRC / "prescreen").glob("*.py"))
                       + [SRC / "e2e.py"]):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.lower() in banned:
                hits.append(f"{path.name}:{node.lineno}:.{node.attr}")
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                    and isinstance(node.slice.value, str) and node.slice.value.lower() in banned:
                hits.append(f"{path.name}:{node.lineno}:[{node.slice.value!r}]")
    return {"same_seed_identical": a == b,
            "family_order_invariant": a == c,
            "composed_outcome_invariant": a == d,
            "new_seed_same_verdict": a["identified"] == e["identified"],
            "new_seed_selected_families": [a["selection"]["families"], e["selection"]["families"]],
            "new_seed_moves_numbers": a["stage1"]["p_spectrum"] != e["stage1"]["p_spectrum"],
            "composed_column_refused_by_loader": refused,
            "static_composed_identifiers_in_rule_modules": hits}


def retrospective() -> dict:
    """What the replay tools wrote, gathered (read-only)."""
    P = OUT / "prescreen"
    out = {}
    for name, path in (("prescreen_backtest", P / "backtest.json"),
                       ("spectrum_backtest", P / "spectrum_backtest.json"),
                       ("prescreen_simulation", P / "simulation.json"),
                       ("coverage_simulation", OUT / "coverage_simulation.json"),
                       ("wording_audit", P / "wording_audit.json"),
                       ("severity_range_audit", P / "severity_range_audit.json")):
        if path.exists():
            with open(path) as f:
                out[name] = {"path": str(path.relative_to(DCI1)), "data": json.load(f)}
    summary = {}
    b = out.get("prescreen_backtest", {}).get("data")
    if b:
        rl = b["replication_level"]
        summary["prescreen_backtest"] = {
            "chance_basis": b.get("chance_basis"),
            "metrics_support_both_pooled": b["summary"]["calibrated support-both (pooled)"],
            "failure_causes": b["failure_causes"],
            "retention_recovery": {k: v for k, v in b["retention_recovery"].items()
                                   if k != "families"},
            "local_recovery": {k: v for k, v in b["local_recovery_detail"].items()
                               if k != "families"},
            "forwarded_new": [r["forwarded_new"] for r in rl],
            "forwarded_legacy": [r["forwarded_legacy"] for r in rl],
            "calibration_generations_new": [r["calibration_cost_new"] for r in rl],
            "calibration_generations_legacy": [r["calibration_cost_legacy"] for r in rl],
            "rescreen_generations": [r["rescreen_cost"] for r in rl]}
    s = out.get("spectrum_backtest", {}).get("data")
    if s:
        summary["spectrum_backtest"] = {
            "chance_basis": s.get("chance_basis"), "summary": s["summary"],
            "per_replication": [{"tree": r["tree"], "model": r["model"],
                                 "identified": r["selection"]["identified"],
                                 "v7_identified": r["v7_spectrum_identified"],
                                 "families": r["selection"]["families"],
                                 "n_points": r["selection"]["n_spectrum_references"],
                                 "offset_below": r["selection"]["coverage"]["offset_below"],
                                 "offset_above": r["selection"]["coverage"]["offset_above"],
                                 "se_beta": r["selection"]["coverage"]["projection"]["se_beta"],
                                 "n_spectrum_valid": r["n_spectrum_valid"],
                                 "spectrum_valid_range": r["spectrum_valid_range"],
                                 "admissible_families": r["backups"]["n_fully_admissible"],
                                 "recorded_backups_inadmissible":
                                     r["backups"]["recorded_backups_inadmissible"]}
                                for r in s["results"]]}
    sim = out.get("prescreen_simulation", {}).get("data")
    if sim:
        summary["prescreen_simulation_choice"] = sim["chosen"]["chosen"]
    cov = out.get("coverage_simulation", {}).get("data")
    if cov:
        summary["coverage_simulation_choice"] = cov["threshold_choice"]["chosen"]
        summary["coverage_simulation_current"] = cov["threshold_choice"]["current_rule"]
    return {"summary": summary, "sources": {k: v["path"] for k, v in out.items()}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resamples", type=int, default=300)
    args = ap.parse_args()
    t0 = time.time()
    print("synthetic cases:", flush=True)
    syn = synthetic(args.resamples)
    print("invariances:", flush=True)
    inv = invariances(args.resamples)
    print(" ", inv, flush=True)
    wording = {"instrument": W.assert_v8_instrument(),
               "hash": W.v8_wording_source_hash(),
               "detection_steep": simulate_wording_case("steep", STEEP, bad=[1, 2],
                                                        p_confused=0.9, n_sims=40),
               "detection_flat": simulate_wording_case("flat", FLAT, bad=[],
                                                       p_confused=0.0, n_sims=40)}
    retro = retrospective()
    rules = {k: getattr(R, k) for k in R.__all__
             if isinstance(getattr(R, k), (int, float, tuple, str))}
    report = {"generated_by": "tools/v8_pipeline_validation.py",
              "rules": rules, "synthetic": syn, "invariances": inv,
              "wording": {k: (v if k != "detection_steep" and k != "detection_flat"
                              else _compact(v)) for k, v in wording.items()},
              "retrospective": retro,
              "spectrum_generation_cost_6": spectrum_generation_cost(6),
              "spectrum_generation_cost_8": spectrum_generation_cost(8),
              "seconds": round(time.time() - t0, 1)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pipeline_validation.json").write_text(json.dumps(report, indent=1, default=str))
    (OUT / "pipeline_validation.md").write_text(_md(report))
    print("written", OUT / "pipeline_validation.md", f"[{time.time() - t0:.0f}s]")
    return 0


def _compact(v):
    if isinstance(v, dict):
        return {k: x for k, x in v.items() if not isinstance(x, (list, dict)) or k in ("summary",)}
    return v


def _f(x, nd=3):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _md(report: dict) -> str:
    L = ["# v8 candidate pipeline: end-to-end validation (synthetic + retrospective gather)", "",
         "Synthetic worlds run the whole chain with seeded draws at the registered sample "
         "sizes; the truth is the same rule set on the true parameters over each family's "
         "declared range. Retrospective numbers are read from the replay tools' JSON "
         "(development-level; see each file).", "",
         "## Synthetic cases", "",
         "| world | identified | truth | family accept TP/FP/FN | selected families | points | "
         "offset below/above | span | SE(β̂) | local found/true | forwarded rungs | "
         "reserve picks (2nd pass) | extension | gens to freeze |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, c in report["synthetic"].items():
        m = c["metrics"]
        L.append(f"| {name} | {m['identified']} | {m['truly_identifiable']} | "
                 f"{m['family_accept_tp']}/{m['family_accept_fp']}/{m['family_accept_fn']} | "
                 f"{', '.join(m['selected_families'])} | {m['n_spectrum_references']} | "
                 f"{_f(m['offset_below'], 2)}/{_f(m['offset_above'], 2)} | {_f(m['total_span'], 2)} | "
                 f"{_f(m['se_beta'])} | {len(m['local_families_found'])}/{len(m['local_families_true'])} | "
                 f"{m['forwarded_rungs']} | {m['reserve_picks_in_rescreen']} | "
                 f"{m['extension_picks']} | {m['costs']['total_to_freeze']} |")
    for name, c in report["synthetic"].items():
        m = c["metrics"]
        if m["coverage_reasons"]:
            L.append(f"- {name}: coverage reasons — {'; '.join(m['coverage_reasons'])}")
        if c["first_failing_spectrum"]:
            worst = sorted(c["first_failing_spectrum"].items())[:12]
            L.append(f"- {name}: first failing spectrum component — "
                     + ", ".join(f"{k}:{v}" for k, v in worst))
    inv = report["invariances"]
    L += ["", "## Invariances", "",
          f"- same seed → identical record: {inv['same_seed_identical']}",
          f"- family order permuted → identical record: {inv['family_order_invariant']}",
          f"- composed outcome changed in the world → identical record: {inv['composed_outcome_invariant']}",
          f"- new seed → same verdict and selected families: {inv['new_seed_same_verdict']} "
          f"(Monte Carlo numbers move: {inv['new_seed_moves_numbers']})",
          f"- a composed column in a calibration table is refused by the loader: "
          f"{inv['composed_column_refused_by_loader']}",
          f"- composed identifiers named in the rule modules: "
          f"{inv['static_composed_identifiers_in_rule_modules'] or 'none'}", ""]
    w = report["wording"]
    L += ["## Wording instrument", "",
          f"v8 wording hash `{w['hash'][:16]}…`; renderings checked: "
          f"{sum(w['instrument']['renderings_checked'].values())}; differences from v7: "
          f"{w['instrument']['n_differences_from_v7']} ({w['instrument']['differences_by_reason']}).", ""]
    rs = report["retrospective"]["summary"]
    if "prescreen_backtest" in rs:
        b = rs["prescreen_backtest"]
        m = b["metrics_support_both_pooled"]
        L += ["## Retrospective (stored evidence, corrected chance basis)", "",
              f"Chance basis: {b['chance_basis']}", "",
              "| screen | precision | recall | FPR | predicted + | true + |", "|---|---|---|---|---|---|"]
        for k, v in m.items():
            L.append(f"| {k} | {_f(v['precision'], 2)} | {_f(v['recall'], 2)} | "
                     f"{_f(v['false_positive_rate'], 2)} | {v['n_predicted_positive']} | {v['n_true_positive']} |")
        rr = b["retention_recovery"]
        lr = b["local_recovery"]
        L += ["", f"Failure causes of pre-screen passes: {b['failure_causes']}.",
              f"Retention artefacts: {rr['n']}; refuted at the screen {rr['by_class']['REFUTED_AT_SCREEN']}, "
              f"accepted after the emulated second pass {rr['by_class']['SECOND_PASS_ACCEPTED']}, "
              f"undecidable (extremes never calibrated) {rr['by_class']['SECOND_PASS_UNDECIDABLE']}; "
              f"geometry retainable at the screen {rr['n_geometry_retainable']}; chance mirages "
              f"{rr['n_mirage_only']}.",
              f"Local references: {lr['n_kept']}/{lr['n_families']} calibrated-caliper rungs forwarded "
              f"(§12.7: {lr['n_kept_legacy']}); why not: {lr['why']}.",
              f"Rungs forwarded per replication: new {b['forwarded_new']} vs §12.7 {b['forwarded_legacy']}; "
              f"calibration generations new {b['calibration_generations_new']} vs "
              f"{b['calibration_generations_legacy']}; re-screen generations {b['rescreen_generations']}.", ""]
    if "spectrum_backtest" in rs:
        s = rs["spectrum_backtest"]
        L += [f"Spectrum replay ({s['chance_basis']}): {s['summary']}", "",
              "| tree | model | identified | v7 | families | points | offset below/above | SE(β̂) | "
              "spectrum-valid (range) | admissible families | recorded backups inadmissible |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in s["per_replication"]:
            rng = r["spectrum_valid_range"]
            L.append(f"| {r['tree']} | {r['model']} | {r['identified']} | {r['v7_identified']} | "
                     f"{', '.join(r['families'])} | {r['n_points']} | {_f(r['offset_below'], 2)}/"
                     f"{_f(r['offset_above'], 2)} | {_f(r['se_beta'])} | {r['n_spectrum_valid']} "
                     f"({_f(rng[0] if rng else None, 2)}–{_f(rng[1] if rng else None, 2)}) | "
                     f"{r['admissible_families']} | {', '.join(r['recorded_backups_inadmissible'])} |")
    if "prescreen_simulation_choice" in rs:
        L += ["", f"Pre-screen simulation choice: {rs['prescreen_simulation_choice']}"]
    if "coverage_simulation_choice" in rs:
        L += [f"Coverage-gate simulation choice: {rs['coverage_simulation_choice']} "
              f"(current rule: {rs['coverage_simulation_current']})"]
    L += ["", "## Constants in force (dci1v8dev.rules)", "", "```",
          json.dumps(report["rules"], indent=0), "```", "",
          f"Spectrum confirmatory cost: {report['spectrum_generation_cost_6']['generations']} generations for "
          f"6 references, {report['spectrum_generation_cost_8']['generations']} for 8 "
          "(solo:X, B+X, X+B on 384 blocks × 8).", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
