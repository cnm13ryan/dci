#!/usr/bin/env python3
"""Backtest of the uncertainty-aware pre-screen on stored evidence (read-only).

    python3 tools/v8_prescreen_backtest.py --evidence /path/to/dci1/evidence \\
        [--config-from reports/dci1v8dev/prescreen/simulation.json]

Writes ``reports/dci1v8dev/prescreen/backtest.json``, ``backtest.md`` and
``failure_table.md``. The screen's thresholds are read from the simulation's
prospective choice when that file exists; the LOMO section is labelled
retrospective development.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev import backtest as B
from dci1v8dev.prescreen.geometry import Geometry
from dci1v8dev.prescreen.rescreen import RescreenConfig
from dci1v8dev.prescreen.retention import RetentionConfig
from dci1v8dev.prescreen.screen import ScreenConfig

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / "prescreen"


def config_from(path: Path | None) -> tuple[ScreenConfig, RescreenConfig, dict]:
    if path is not None and path.exists():
        chosen = _load(path)["chosen"]["chosen"]
        cfg = ScreenConfig(geometry=Geometry(d_below=chosen["d_below"],
                                             d_above=chosen["d_above"]),
                           accept=chosen["accept"], reject=chosen["reject"],
                           spectrum_event=chosen["event"])
        rcfg = RescreenConfig(include_a_grid=False,
                              final_accept_at=chosen.get("final_accept_at", 0.5))
        return cfg, rcfg, {"source": str(path), **chosen}
    return ScreenConfig(), RescreenConfig(include_a_grid=False), {"source": "defaults"}


def _load(path):
    with open(path) as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--config-from", default=str(OUT / "simulation.json"))
    ap.add_argument("--no-rescreen", action="store_true")
    ap.add_argument("--chance-cache", default=str(DCI1 / "reports" / "dci1v8dev" / "chance_basis"),
                    help="the §13.2 chance-basis cache (tools/v8_chance_basis_cache.py)")
    args = ap.parse_args()
    ev = Path(args.evidence)
    cfg, rcfg, provenance = config_from(Path(args.config_from))
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    reps = []
    for tree, model, rel in B.REPLICATIONS:
        rep = B.load_replication(ev, rel, chance_cache_dir=Path(args.chance_cache),
                                 tree=tree, model=model)
        if rep["regime"] is None or rep["gate2"] is None:
            print(f"skip {tree}/{model}: no pre-screen or Gate-2 record")
            continue
        out = B.backtest_replication(
            rep, label=tree, model=model, screen_config=cfg,
            rescreen_config=rcfg,
            retention_config=RetentionConfig(),
            emulate_rescreen=not args.no_rescreen)
        reps.append(out)
        print(f"{tree}/{model}: legacy C4 groups {len(out['legacy_c4_groups_prescreen'])}"
              f" -> {len(out['c4_groups_calibrated'])} calibrated; pass->fail "
              f"{out['n_pass_to_fail']}; stage1 "
              f"{ {k: len(v) for k, v in out['stage1_statuses'].items()} }; "
              f"final { {k: len(v) for k, v in out['final_statuses'].items()} }; "
              f"forwarded {out['retention']['n_forwarded']} vs "
              f"{out['legacy_retention']['n_measured']} [{time.time() - t0:.0f}s]",
              flush=True)
    rows = [r for out in reps for r in out["families"]]
    truths = {"calibrated C4 (production, pooled)": "calibration_c4",
              "calibrated support-both (pooled)": "calibration_support_both",
              "calibrated support-both (Calibration-B only)":
                  "calibration_b_support_both",
              "calibrated C4 (Calibration-B only)": "calibration_b_c4"}
    summary = {}
    for name, key in truths.items():
        summary[name] = {
            "legacy (pre-screen C4 per family)": B.metrics(
                rows, pred=lambda r: r["prescreen_c4"], truth=lambda r, k=key: r[k]),
            "new stage 1 accept": B.metrics(
                rows, pred=lambda r: r["stage1_status"] == "SCREEN_ACCEPT",
                truth=lambda r, k=key: r[k]),
            "new stage 1 accept-or-resample": B.metrics(
                rows, pred=lambda r: r["stage1_status"] in ("SCREEN_ACCEPT",
                                                            "SCREEN_RESAMPLE"),
                truth=lambda r, k=key: r[k]),
            "new final accept (emulated second pass)": B.metrics(
                rows, pred=lambda r: r["final_status"] == "SCREEN_ACCEPT",
                truth=lambda r, k=key: r[k]),
        }
    causes = {c: sum(1 for r in rows if r["failure_cause"] == c)
              for c in B.FAILURE_CAUSES}
    n_pass_fail = sum(1 for r in rows if r["prescreen_c4"] and not r["calibration_c4"])
    n_pass = sum(1 for r in rows if r["prescreen_c4"])
    lomo = B.leave_one_model_out(rows, p_key="stage1_p",
                                 truth_key="calibration_support_both")
    lomo_c4 = B.leave_one_model_out(rows, p_key="stage1_p_c4",
                                    truth_key="calibration_c4")
    # usable local families: does the forwarded set keep the rungs that
    # calibrated inside the caliper?
    local_recovery = []
    for out in reps:
        for r in out["families"]:
            if r["calibration_local"]:
                local_recovery.append({
                    "tree": out["tree"], "model": out["model"],
                    "family": r["family"],
                    "forwarded_new": bool(r["forwarded_new"]),
                    "forwarded_legacy": bool(r["forwarded_legacy"])})
    recovery = B.retention_recovery(rows, d_below=cfg.geometry.d_below,
                                    d_above=cfg.geometry.d_above)
    local_detail = B.local_recovery_detail(rows)
    report = {
        "config": provenance, "screen_config": cfg.__dict__ | {
            "geometry": cfg.geometry.__dict__},
        "chance_basis": reps[0]["chance_basis"] if reps else None,
        "retention_recovery": recovery,
        "local_recovery_detail": local_detail,
        "replications": reps, "summary": summary,
        "failure_causes": causes,
        "n_prescreen_pass_families": n_pass,
        "n_pass_to_fail_families": n_pass_fail,
        "replication_level": [
            {"tree": o["tree"], "model": o["model"],
             "legacy_groups_prescreen": len(o["legacy_c4_groups_prescreen"]),
             "groups_calibrated": len(o["c4_groups_calibrated"]),
             "legacy_c4_prescreen": o["legacy_c4_prescreen"],
             "c4_calibrated": o["c4_calibrated"],
             "n_pass_to_fail": o["n_pass_to_fail"],
             "stage1_accept": len(o["stage1_statuses"]["SCREEN_ACCEPT"]),
             "stage1_resample": len(o["stage1_statuses"]["SCREEN_RESAMPLE"]),
             "final_accept": len(o["final_statuses"]["SCREEN_ACCEPT"]),
             "final_accept_calibrated_true": sum(
                 1 for r in o["families"] if r["final_status"] == "SCREEN_ACCEPT"
                 and r["calibration_support_both"]),
             "forwarded_new": o["retention"]["n_forwarded"],
             "forwarded_legacy": o["legacy_retention"]["n_measured"],
             "rescreen_cost": (o["rescreen"] or {}).get("cost_generations", 0),
             "calibration_cost_new":
                 o["retention"]["calibration_cost_generations"],
             "calibration_cost_legacy":
                 o["legacy_retention"]["n_measured"] * 768}
            for o in reps],
        "local_recovery": local_recovery,
        "lomo_support_both": lomo, "lomo_c4": lomo_c4,
        "seconds": time.time() - t0,
    }
    (OUT / "backtest.json").write_text(json.dumps(report, indent=1))
    (OUT / "backtest.md").write_text(_md(report))
    (OUT / "failure_table.md").write_text(_failure_md(report))
    print("written", OUT)
    return 0


def _f(x, nd=2):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _md(report: dict) -> str:
    L = ["# Pre-screen backtest on stored evidence (development candidate)", "",
         f"Screen configuration: {report['config']}", "",
         f"Chance basis of every calibrated verdict: {report.get('chance_basis')}.", "",
         "Read-only over the registered v7 and v6 trees and the completed "
         "development rehearsals. The second pass is EMULATED by carving 24-topic "
         "batches from Calibration-A's per-topic rows (no reserve rungs, no A-grid "
         "re-measurement); the 'Calibration-B only' truth shares no topic with the "
         "carved batches. Family-level rows: one per (replication, family).", "",
         "## Family-level metrics", ""]
    for truth, block in report["summary"].items():
        L += [f"### Truth: {truth}", "",
              "| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |",
              "|---|---|---|---|---|---|---|---|---|"]
        for name, m in block.items():
            L.append(f"| {name} | {m['n_predicted_positive']} | {m['n_true_positive']} | "
                     f"{m['tp']} | {m['fp']} | {m['fn']} | {_f(m['precision'])} | "
                     f"{_f(m['recall'])} | {_f(m['false_positive_rate'])} |")
        L.append("")
    L += ["## Replication level", "",
          "| tree | model | legacy groups (pre-screen) | groups calibrated | C4 pre | C4 cal | "
          "pass→fail families | stage-1 accept | stage-1 resample | final accept | "
          "final accept & calibrated | forwarded new | forwarded legacy | re-screen gens | "
          "calibration gens new | legacy |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["replication_level"]:
        L.append(f"| {r['tree']} | {r['model']} | {r['legacy_groups_prescreen']} | "
                 f"{r['groups_calibrated']} | {r['legacy_c4_prescreen']} | "
                 f"{r['c4_calibrated']} | {r['n_pass_to_fail']} | {r['stage1_accept']} | "
                 f"{r['stage1_resample']} | {r['final_accept']} | "
                 f"{r['final_accept_calibrated_true']} | {r['forwarded_new']} | "
                 f"{r['forwarded_legacy']} | {r['rescreen_cost']} | "
                 f"{r['calibration_cost_new']} | {r['calibration_cost_legacy']} |")
    rec = report["retention_recovery"]
    L += ["", "## Retention recovery: the historical RETENTION_ARTIFACT families", "",
          f"{rec['n']} pre-screen passes were lost to §12.7's nearest-24 Tier-3 retention. "
          f"Under the new screen: {rec['by_class']['REFUTED_AT_SCREEN']} are refuted at stage 1 "
          "(their spread rests on chance-inflated or lift-less rungs: a mirage, not a loss); "
          f"{rec['by_class']['SECOND_PASS_ACCEPTED']} are accepted after the emulated second pass and "
          f"forwarded with their spaced set ({rec['n_recovered']} with a rung beyond each offset); "
          f"{rec['by_class']['SECOND_PASS_UNDECIDABLE']} are rejected by the emulated pass, which "
          "could not measure their dropped extremes (never calibrated) — of these "
          f"{rec['n_undecidable_but_retainable']} have admissible rungs on both offsets at the screen, "
          "which the spaced retention would carry if the production pass accepted them; "
          f"{rec['by_class']['SECOND_PASS_REJECTED']} are rejected with every rung measurable. "
          f"Geometry retainable at the screen (an admissible rung at or beyond both offsets): "
          f"{rec['n_geometry_retainable']}/{rec['n']}.", "",
          "| tree | model | family | tier | class | stage-1 (P) | final (P) | P(below)/P(above) | "
          "dropped by §12.7 | retainable | mirage rungs | forwarded (new) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rec["families"]:
        L.append(f"| {x['tree']} | {x['model']} | {x['family']} | {x['structural_tier']} | {x['class']} | "
                 f"{x['stage1_status']} ({_f(x['stage1_p'])}) | {x['final_status']} ({_f(x['final_p'])}) | "
                 f"{_f(x['stage1_p_below'])}/{_f(x['stage1_p_above'])} | "
                 f"{', '.join(x['rungs_dropped_by_12_7'][:5])} | {x['geometry_retainable']} | "
                 f"{', '.join(x['chance_mirage_rungs'][:4])} | {', '.join(x['forwarded_new'])} |")
    ld = report["local_recovery_detail"]
    L += ["", "## Local-reference recovery (detail)", "",
          f"{ld['n_families']} family-replications calibrated a chance/lift-admissible rung inside the "
          f"±0.10 caliper. The new retention forwards that very rung for {ld['n_kept']} "
          f"({ld['why']['OTHER_RUNGS_FORWARDED']} forward other rungs of the family, "
          f"{ld['why']['NOT_LABELLED_LOCAL']} are not labelled local at the screen, "
          f"{ld['why']['FAMILY_NOT_FORWARDED']} labelled but not forwarded); §12.7 forwarded it for "
          f"{ld['n_kept_legacy']}.", ""]
    n_loc = len(report["local_recovery"])
    L += ["", "## Local-reference recovery", "",
          f"Families with a rung inside the ±0.10 caliper at calibration: {n_loc}; "
          f"kept by the new retention: "
          f"{sum(1 for x in report['local_recovery'] if x['forwarded_new'])}; "
          f"by §12.7: {sum(1 for x in report['local_recovery'] if x['forwarded_legacy'])}.",
          "", "## Failure causes (pre-screen PASS → calibration FAIL, per family)", "",
          f"{report['n_pass_to_fail_families']} of {report['n_prescreen_pass_families']} "
          "pre-screen passes failed at calibration.", "",
          "| cause | families |", "|---|---|"]
    for c, n in report["failure_causes"].items():
        L.append(f"| {c} | {n} |")
    for key in ("lomo_support_both", "lomo_c4"):
        lo = report[key]
        L += ["", f"## {lo['label']}: {lo['p_key']} vs {lo['truth_key']}", "",
              "| held-out model | chosen accept | train precision | train recall | "
              "test precision | test recall | test FPR | test n+ |",
              "|---|---|---|---|---|---|---|---|"]
        for m, v in lo["per_held_out_model"].items():
            tr, te = v["train"] or {}, v["test"]
            L.append(f"| {m} | {v['chosen_accept']} | {_f(tr.get('precision'))} | "
                     f"{_f(tr.get('recall'))} | {_f(te['precision'])} | "
                     f"{_f(te['recall'])} | {_f(te['false_positive_rate'])} | "
                     f"{te['n_true_positive']} |")
    return "\n".join(L) + "\n"


def _failure_md(report: dict) -> str:
    L = ["# Pre-screen vs calibration, family by family (read-only reconstruction)",
         "", "Spans are §12.6's per-family C4 span over eligible rungs (raw max−min "
         "of ι); 'same rungs' restricts the pre-screen to the rungs calibration "
         "measured. Straddle = an eligible rung on each side of ι_A.", ""]
    for o in report["replications"]:
        L += [f"## {o['tree']} / {o['model']} — ι_A pre-screen {o['iota_a_prescreen']:.3f}, "
              f"calibrated {o['iota_a_calibrated']:.3f}; legacy C4 groups "
              f"{len(o['legacy_c4_groups_prescreen'])} → {len(o['c4_groups_calibrated'])}",
              "",
              "| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | "
              "pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | "
              "stage-1 | final |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(o["families"], key=lambda r: (not r["prescreen_c4"],
                                                      r["family"])):
            if not (r["prescreen_c4"] or r["calibration_c4"]
                    or r["final_status"] == "SCREEN_ACCEPT"):
                continue
            L.append(f"| {r['family']} | {r['structural_tier']} | {_f(r['prescreen_span'])} | "
                     f"{_f(r['prescreen_span_same_rungs'])} | {_f(r['calibration_span'])} | "
                     f"{r['prescreen_straddle']} | {r['calibration_straddle']} | "
                     f"{r['prescreen_c4']} | {r['calibration_c4']} | "
                     f"{r['failure_cause'] or ''} | "
                     f"{', '.join(r['rungs_disappeared'][:5])} | "
                     f"{len(r['rungs_not_calibrated'])} | {r['ladder_class']} | "
                     f"{r['stage1_status']} ({_f(r['stage1_p'])}) | "
                     f"{r['final_status']} ({_f(r['final_p'])}) |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
