#!/usr/bin/env python3
"""Are the Tier-1 severity grids long enough? (read-only, exploratory)

Reads the wording audit's repaired ladders (robust frames) and, per model
and family, extrapolates the logit-linear ladder to the severity at which it
would reach the spectrum's hard-side region (iota_A - 0.15) and the easy-side
region (iota_A + 0.10); reports whether the registered ladder (1..8), the
frozen reserve (..12) or neither contains it.

    python3 tools/v8_severity_range_audit.py
Writes ``reports/dci1v8dev/prescreen/severity_range_audit.json`` and ``.md``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v8dev.prescreen.extension import expected_severity_to_reach

OUT = Path(__file__).resolve().parents[1] / "reports" / "dci1v8dev" / "prescreen"


def _load(path):
    with open(path) as f:
        return json.load(f)


def main() -> int:
    audit = _load(OUT / "wording_audit.json")
    rows = []
    for r in audit["results"]:
        iota_a = r["iota_a"]
        for kind, lad in sorted(r["ladders_robust"].items()):
            if kind == "A":
                continue
            ladder = {int(q): v["rate"] for q, v in lad["ladder"].items()}
            hard = expected_severity_to_reach(kind, ladder, target=max(0.02, iota_a - 0.15))
            easy = expected_severity_to_reach(kind, ladder, target=min(0.98, iota_a + 0.10))
            rows.append({"tree": r["tree"], "model": r["model"], "family": kind,
                         "iota_a": iota_a, "classification": lad["classification"],
                         "min": lad["min_iota"], "max": lad["max_iota"],
                         "measured_max_q": max(ladder),
                         "reaches_below_measured": lad["reaches_below"],
                         "reaches_above_measured": lad["reaches_above"],
                         "q_to_reach_hard": hard.get("estimate"),
                         "hard_within_reserve": hard.get("within_reserve"),
                         "q_to_reach_easy": easy.get("estimate"),
                         "slope_logit": hard.get("slope_logit_per_severity")})
    summary = {}
    for m in sorted({x["model"] for x in rows}):
        mine = [x for x in rows if x["model"] == m]
        summary[m] = {
            "families_not_reaching_hard_side": sorted({x["family"] for x in mine
                                                       if not x["reaches_below_measured"]}),
            "of_which_reserve_would_reach": sorted({
                x["family"] for x in mine if not x["reaches_below_measured"]
                and x["q_to_reach_hard"] is not None and x["hard_within_reserve"]}),
            "of_which_beyond_reserve": sorted({
                x["family"] for x in mine if not x["reaches_below_measured"]
                and x["q_to_reach_hard"] is not None and not x["hard_within_reserve"]}),
            "max_q_needed": max((x["q_to_reach_hard"] for x in mine
                                 if x["q_to_reach_hard"] is not None), default=None)}
    report = {"rows": rows, "summary": summary,
              "source": "wording_audit.json (robust frames)",
              "targets": "hard: iota_A - 0.15; easy: iota_A + 0.10"}
    (OUT / "severity_range_audit.json").write_text(json.dumps(report, indent=1))
    L = ["# Severity-range audit (read-only, exploratory)", "",
         "Logit-linear extrapolation of each repaired MK ladder to the severity at "
         "which it reaches ι_A − 0.15 (hard side) and ι_A + 0.10 (easy side). "
         "Ladder = 1..8, reserve = ..12.", "", "## Per model", ""]
    for m, s in summary.items():
        L.append(f"- **{m}**: not reaching the hard side within the measured rungs: "
                 f"{s['families_not_reaching_hard_side']}; reserve would reach: "
                 f"{s['of_which_reserve_would_reach']}; beyond the reserve: "
                 f"{s['of_which_beyond_reserve']}; max q needed ≈ "
                 f"{s['max_q_needed'] if s['max_q_needed'] is None else round(s['max_q_needed'], 1)}")
    L += ["", "| tree | model | family | ι_A | class | min ι | max ι | measured to q | "
          "reaches hard | reaches easy | q for hard | in reserve | q for easy |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "—" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))
    for x in rows:
        L.append(f"| {x['tree']} | {x['model']} | {x['family']} | {x['iota_a']:.3f} | "
                 f"{x['classification']} | {f(x['min'])} | {f(x['max'])} | {x['measured_max_q']} | "
                 f"{x['reaches_below_measured']} | {x['reaches_above_measured']} | "
                 f"{f(x['q_to_reach_hard'])} | {x['hard_within_reserve']} | {f(x['q_to_reach_easy'])} |")
    (OUT / "severity_range_audit.md").write_text("\n".join(L) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
