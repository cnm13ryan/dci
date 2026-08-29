#!/usr/bin/env python3
"""Operating characteristics of the legacy and the uncertainty-aware screen
on synthetic families (development candidate; nothing here is evidence).

    python3 tools/v8_prescreen_simulation.py [--sims 200] [--quick]

Writes ``reports/dci1v8dev/prescreen/simulation.json`` and
``simulation.md``. Thresholds are chosen **prospectively** here, on the
synthetic archetypes' operating characteristics, and never on stored
calibration outcomes; the backtest tool reads the choice from this file.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev import simulate as S
from dci1v8dev.prescreen.geometry import Geometry
from dci1v8dev.prescreen.rescreen import RescreenConfig
from dci1v8dev.prescreen.screen import ScreenConfig

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / "prescreen"

#: Prospective grid. Offsets are the ones the precision analysis supports
#: (below 0.15 / above 0.10) and their neighbours; the event is the
#: support-both geometry or C4-as-registered.
GRID = [
    {"event": "support_both", "d_below": 0.15, "d_above": 0.10},
    {"event": "support_both", "d_below": 0.20, "d_above": 0.10},
    {"event": "support_both", "d_below": 0.15, "d_above": 0.15},
    {"event": "c4", "d_below": 0.15, "d_above": 0.10},
]
#: (accept, reject, final_accept_at): the third is the posterior majority
#: rule applied to a family still undecided at the maximum batch count.
THRESHOLDS = [(0.70, 0.15, 0.50), (0.80, 0.20, 0.50), (0.75, 0.15, 0.75),
              (0.80, 0.20, 0.80), (0.85, 0.20, 0.70)]


def run(n_sims: int, quick: bool) -> dict:
    curves = {"qwen3-4b-like (iota_A~0.68)": S.A_CURVE_QWEN,
              "qwen-2507-like (iota_A~0.55)": S.A_CURVE_2507}
    if quick:
        curves = {"qwen3-4b-like (iota_A~0.68)": S.A_CURVE_QWEN}
    grid = GRID[:2] if quick else GRID
    thresholds = THRESHOLDS[:2] if quick else THRESHOLDS
    results = []
    t0 = time.time()
    for g in grid:
        for accept, reject, final_at in thresholds:
            cfg = ScreenConfig(
                geometry=Geometry(d_below=g["d_below"], d_above=g["d_above"]),
                draws=2000, accept=accept, reject=reject,
                spectrum_event=g["event"])
            rcfg = RescreenConfig(final_accept_at=final_at)
            for cname, curve in curves.items():
                sim = S.simulate_all(a_curve=curve, n_sims=n_sims,
                                     seed=20260829, screen_config=cfg,
                                     rescreen_config=rcfg)
                summary = _summarise(sim["results"])
                results.append({"grid": g, "accept": accept, "reject": reject,
                                "final_accept_at": final_at,
                                "a_curve": cname, "summary": summary,
                                "per_archetype": {
                                    k: {"true_event": v["true_event"],
                                        "true_c4": v["true_c4"],
                                        "legacy": v["legacy"],
                                        "new": v["new"],
                                        "calibrated": v["calibrated"],
                                        "mean_stage1_p": v["mean_stage1_p"],
                                        "mean_final_p": v["mean_final_p"]}
                                    for k, v in sim["results"].items()}})
                print(f"  {g['event']} d=({g['d_below']},{g['d_above']}) "
                      f"acc={accept} rej={reject} fin={final_at} {cname}: "
                      f"FP legacy={summary['legacy_fp_rate']:.2f} "
                      f"new={summary['new_fp_rate']:.2f} | FN legacy="
                      f"{summary['legacy_fn_rate']:.2f} new="
                      f"{summary['new_fn_rate']:.2f} | resampled="
                      f"{summary['fraction_resampled']:.2f} cost="
                      f"{summary['mean_rescreen_cost']:.0f} "
                      f"[{time.time() - t0:.0f}s]", flush=True)
    chosen = _choose(results)
    return {"n_sims": n_sims, "quick": quick, "grid": grid,
            "thresholds": thresholds, "results": results, "chosen": chosen,
            "archetypes": {k: {"family": a.family, "expectation": a.expectation,
                               "true_p": {str(q): p for q, p in a.true_p.items()}}
                           for k, a in S.ARCHETYPES.items()},
            "seconds": time.time() - t0}


def _summarise(res: dict) -> dict:
    """Pooled operating characteristics over the archetypes, equal weight."""
    names = list(res)
    legacy_fp = [res[k]["legacy"]["false_positive_rate"] for k in names
                 if not res[k]["true_c4"]]
    legacy_fn = [res[k]["legacy"]["false_negative_rate"] for k in names
                 if res[k]["true_c4"]]
    new_fp = [res[k]["new"]["false_positive_rate"] for k in names
              if not res[k]["true_event"]]
    new_fn = [res[k]["new"]["false_negative_rate"] for k in names
              if res[k]["true_event"]]
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0
    surv_leg = [res[k]["legacy"]["calibrated_c4_given_pass"] for k in names
                if res[k]["legacy"]["calibrated_c4_given_pass"] is not None]
    surv_new = [res[k]["new"]["calibrated_event_given_accept"] for k in names
                if res[k]["new"]["calibrated_event_given_accept"] is not None]
    return {"legacy_fp_rate": mean(legacy_fp), "legacy_fn_rate": mean(legacy_fn),
            "new_fp_rate": mean(new_fp), "new_fn_rate": mean(new_fn),
            "fraction_resampled": mean([res[k]["new"]["fraction_resampled"]
                                        for k in names]),
            "mean_rescreen_cost": mean([res[k]["new"]["mean_rescreen_cost"]
                                        for k in names]),
            "legacy_survival_given_pass": mean(surv_leg),
            "new_survival_given_accept": mean(surv_new),
            "n_true_event": sum(1 for k in names if res[k]["true_event"]),
            "n_true_c4": sum(1 for k in names if res[k]["true_c4"])}


def _choose(results: list[dict]) -> dict:
    """Prospective choice: minimise FP + FN (equal weight, averaged over the
    A curves), tie-break on the smaller resample fraction. Recorded with
    every alternative so the choice is auditable."""
    keyed: dict[tuple, list[dict]] = {}
    for r in results:
        key = (r["grid"]["event"], r["grid"]["d_below"], r["grid"]["d_above"],
               r["accept"], r["reject"], r["final_accept_at"])
        keyed.setdefault(key, []).append(r)
    scored = []
    for key, rs in keyed.items():
        fp = sum(r["summary"]["new_fp_rate"] for r in rs) / len(rs)
        fn = sum(r["summary"]["new_fn_rate"] for r in rs) / len(rs)
        res = sum(r["summary"]["fraction_resampled"] for r in rs) / len(rs)
        scored.append({"event": key[0], "d_below": key[1], "d_above": key[2],
                       "accept": key[3], "reject": key[4],
                       "final_accept_at": key[5], "fp": fp, "fn": fn,
                       "objective": fp + fn, "fraction_resampled": res})
    scored.sort(key=lambda s: (round(s["objective"], 4),
                               round(s["fraction_resampled"], 4),
                               -s["d_below"], s["accept"]))
    return {"rule": "minimise FP + FN over archetypes (equal weight, both A "
                    "curves); tie-break: smaller resample fraction, larger "
                    "d_below, lower accept", "ranked": scored,
            "chosen": scored[0] if scored else None}


def _md(report: dict) -> str:
    lines = ["# Pre-screen simulation (development candidate)", "",
             f"n_sims per archetype = {report['n_sims']}; every number is "
             "synthetic. Legacy = the v7 per-family C4 certificate on 24-topic "
             "point estimates; New = the posterior-predictive screen with the "
             "targeted second pass. FP/FN are against the TRUE event on the "
             "true parameters.", "",
             "## Chosen thresholds (prospective)", "",
             f"Rule: {report['chosen']['rule']}", "",
             "| rank | event | d_below | d_above | accept | reject | final at | FP | FN | resampled |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, s in enumerate(report["chosen"]["ranked"][:12]):
        lines.append(f"| {i + 1} | {s['event']} | {s['d_below']} | {s['d_above']} "
                     f"| {s['accept']} | {s['reject']} | {s['final_accept_at']} | "
                     f"{s['fp']:.3f} | {s['fn']:.3f} | {s['fraction_resampled']:.2f} |")
    lines += ["", "## Per archetype, at the chosen configuration", ""]
    ch = report["chosen"]["chosen"]
    for r in report["results"]:
        g = r["grid"]
        if (g["event"], g["d_below"], g["d_above"], r["accept"], r["reject"],
                r["final_accept_at"]) != (
                ch["event"], ch["d_below"], ch["d_above"], ch["accept"],
                ch["reject"], ch["final_accept_at"]):
            continue
        lines += [f"### A curve: {r['a_curve']}", "",
                  "| archetype | true event | true C4 | legacy pass | legacy FP | legacy FN | "
                  "new accept | new FP | new FN | resampled | mean batches | "
                  "P(cal C4 \\| legacy pass) | P(cal event \\| new accept) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, v in r["per_archetype"].items():
            L, N = v["legacy"], v["new"]
            f = lambda x: "—" if x is None else f"{x:.2f}"
            lines.append(f"| {k} | {v['true_event']} | {v['true_c4']} | "
                         f"{f(L['pass_rate'])} | {f(L['false_positive_rate'])} | "
                         f"{f(L['false_negative_rate'])} | {f(N['accept_rate'])} | "
                         f"{f(N['false_positive_rate'])} | {f(N['false_negative_rate'])} | "
                         f"{f(N['fraction_resampled'])} | {f(N['mean_batches'])} | "
                         f"{f(L['calibrated_c4_given_pass'])} | "
                         f"{f(N['calibrated_event_given_accept'])} |")
        lines.append("")
    lines += ["## Whole grid (pooled over archetypes)", "",
              "| event | d_below | d_above | accept | reject | final at | A curve | legacy FP | "
              "legacy FN | new FP | new FN | resampled | mean re-screen gens | "
              "survival legacy | survival new |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        s, g = r["summary"], r["grid"]
        lines.append(f"| {g['event']} | {g['d_below']} | {g['d_above']} | {r['accept']} | "
                     f"{r['reject']} | {r['final_accept_at']} | {r['a_curve']} | "
                     f"{s['legacy_fp_rate']:.2f} | "
                     f"{s['legacy_fn_rate']:.2f} | {s['new_fp_rate']:.2f} | "
                     f"{s['new_fn_rate']:.2f} | {s['fraction_resampled']:.2f} | "
                     f"{s['mean_rescreen_cost']:.0f} | "
                     f"{s['legacy_survival_given_pass']:.2f} | "
                     f"{s['new_survival_given_accept']:.2f} |")
    lines += ["", "## Archetypes", ""]
    for k, a in report["archetypes"].items():
        lines.append(f"- **{k}** ({a['family']}): {a['expectation']}; true p = "
                     f"{a['true_p']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = run(args.sims, args.quick)
    (OUT / "simulation.json").write_text(json.dumps(report, indent=1))
    (OUT / "simulation.md").write_text(_md(report))
    print("chosen:", report["chosen"]["chosen"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
