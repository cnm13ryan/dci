#!/usr/bin/env python3
"""Simulate the selected-coverage gate's operating characteristics and the
prospective threshold choice (synthetic; no evidence read).

    python3 tools/v8_coverage_simulation.py [--n-sims 400]

Writes reports/dci1v8dev/coverage_simulation.{json,md}.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev.spectrum.coverage import CoverageRule                     # noqa: E402
from dci1v8dev.spectrum.coverage_simulation import (                     # noqa: E402
    SimulationGrid, attenuation_table, simulate_gate, threshold_choice)

OUT = Path(__file__).resolve().parents[1] / "reports" / "dci1v8dev"


def _f(x, nd=2):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sims", type=int, default=400)
    args = ap.parse_args()
    t0 = time.time()
    grid = SimulationGrid(n_sims=args.n_sims)
    rule = CoverageRule()
    sim = simulate_gate(rule, grid=grid)
    choice = threshold_choice(rule, grid=grid)
    atten = attenuation_table()
    report = {"generated_by": "tools/v8_coverage_simulation.py", "synthetic": True,
              "simulation": sim, "threshold_choice": choice,
              "attenuation": atten, "seconds": round(time.time() - t0, 1)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "coverage_simulation.json").write_text(json.dumps(report, indent=1))
    L = ["# The selected-coverage gate: simulated operating characteristics (synthetic)", "",
         f"Grid: {grid.families} families × 2 points, true offsets below "
         f"{list(grid.offsets_below)} / above {list(grid.offsets_above)} (the farthest family "
         "reaches the nominal offset; the others 60–100 % of it), calibration SE(ι) "
         f"{list(grid.se_calibration)}, confirmatory SE(d) {grid.se_confirmatory}, "
         f"{grid.n_sims} designs per cell, seed {grid.seed}. Truth = realised SE(β̂) ≤ "
         f"{rule.max_se_beta} at the measured per-point precision ({rule.se_point}, block "
         f"correlation {rule.block_corr}), A bracketed by ≥ {grid.d_min} on both sides after "
         "re-measurement, attenuation ≤ 10 %.", "",
         "## Current rule", "",
         f"d_below {rule.d_below}, d_above {rule.d_above}, min span {rule.min_total_span}, "
         f"SE(ι) ≤ {rule.max_se_iota}, SE(β̂) ≤ {rule.max_se_beta}, ≥ {rule.min_points_below}/"
         f"{rule.min_points_above} points and ≥ {rule.min_families_per_side} families per side.", "",
         "| offset below | offset above | SE(ι) cal | P(gate) | P(truth) | FP | FN | "
         "median realised SE(β̂) | median attenuation |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in sim["cells"]:
        L.append(f"| {c['offset_below']} | {c['offset_above']} | {c['se_calibration']} | "
                 f"{_f(c['p_gate_identified'])} | {_f(c['p_truly_identifiable'])} | "
                 f"{_f(c['false_positive'])} | {_f(c['false_negative'])} | "
                 f"{_f(c['se_beta_realised_median'], 3)} | {_f(c['attenuation_median'], 3)} |")
    ch = choice["chosen"]
    cur = choice["current_rule"]
    L += ["", "## Threshold choice (prospective)", "",
          f"Criterion: PPV ≥ {choice['criterion']['min_ppv']} pooled over the grid the SE(ι) "
          "ceiling admits; among acceptable rules the highest recall, then the looser SE(ι) "
          "ceiling, then the smaller span.", "",
          "| d_below | d_above | min span | SE(ι) ≤ | PPV | recall | gate + | truth + | acceptable |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in choice["candidates"]:
        mark = " **chosen**" if r is ch else (" (current)" if r is cur else "")
        L.append(f"| {r['d_below']} | {r['d_above']} | {r['min_total_span']} | {r['max_se_iota']} | "
                 f"{_f(r['ppv'])} | {_f(r['recall'])} | {r['n_gate_identified']} | "
                 f"{r['n_truly_identifiable']} | {r['acceptable']}{mark} |")
    L += ["", f"Chosen: {ch}", "", f"Current rule: {cur}", "",
          "## Errors-in-variables attenuation at confirmatory precision", "",
          "| half-spread within family | reliability | attenuation of β̂ |", "|---|---|---|"]
    for a in atten:
        L.append(f"| ±{a['half_spread']} | {_f(a['reliability'], 3)} | {_f(a['attenuation'], 3)} |")
    (OUT / "coverage_simulation.md").write_text("\n".join(L) + "\n")
    print("written", OUT / "coverage_simulation.md", f"[{time.time() - t0:.0f}s]")
    print("chosen:", ch); print("current:", cur)
    return 0


if __name__ == "__main__":
    sys.exit(main())
