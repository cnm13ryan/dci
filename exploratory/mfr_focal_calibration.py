"""Apply the focal-ladder construction gates and freeze the first passing rung.

The gates are construction criteria, not inferential results: they ask whether a
candidate focal instruction creates a regime in which all four outcome states can
actually occur, so that a priority intervention has something to move. They are
applied to CALIBRATION tasks only, in the fixed order B -> X_B_INC2 -> X_B_INC1,
and the FIRST rung that passes is taken.

Nothing here looks at whether a rung produces an interesting priority pattern.
It cannot: the calibration design contains no priority conditions at all.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from dci_exploratory import arbprogram as A

pd.set_option("display.width", 240)
SCORED = Path(sys.argv[1])
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else None
PRIMARY_BACKGROUND = "X_PAREN_FREE"
LADDER = ("B", "X_B_INC2", "X_B_INC1")

#: The operational calibration target, quoted from the directive and applied as
#: written. Pooled over the reasoning conditions, on calibration tasks.
GATES = {
    "focal pass rate in [0.25, 0.75]": lambda s: 0.25 <= s["focal"] <= 0.75,
    "target pass rate in [0.15, 0.85]": lambda s: 0.15 <= s["target"] <= 0.85,
    "P(both) >= 0.05": lambda s: s["both"] >= 0.05,
    "P(target only) >= 0.05": lambda s: s["target only"] >= 0.05,
    "P(focal only) >= 0.05": lambda s: s["focal only"] >= 0.05,
    "technical invalidity <= 0.02": lambda s: s["invalid"] <= 0.02,
}

frame = pd.read_json(SCORED, lines=True)
frame["rung"] = frame["arm"]

print(f"### {len(frame)} calibration generations on "
      f"{frame['task_id'].nunique()} calibration tasks "
      f"({frame['task_id'].min()}..{frame['task_id'].max()}), "
      f"disjoint from the 20 evaluation tasks\n")

print("### Rates by rung, background and reasoning condition\n")
by_cell = frame.groupby(["rung", "background_name", "reasoning_budget"]).agg(
    n=("A_pass", "size"), target=("A_pass", "mean"), focal=("Q_pass", "mean"),
    background=("background_pass", "mean"),
    sentences=("sentence_count", "mean"), words=("word_count", "mean"),
    truncated=("truncated", "mean"),
    technical_failure=("technical_failure", "mean"),
    leaked=("scratchpad_leakage", "mean"))
print(by_cell.to_string(float_format=lambda v: f"{v:.3f}"))

print("\n\n### Four-state distribution by rung and background\n")
print(pd.crosstab([frame["rung"], frame["background_name"],
                   frame["reasoning_budget"]], frame["arbitration_state"],
                  normalize="index").to_string(float_format=lambda v: f"{v:.3f}"))

print(f"\n\n### Gates, on the primary background ({PRIMARY_BACKGROUND}), "
      f"pooled over reasoning conditions\n")
primary = frame[frame["background"] == PRIMARY_BACKGROUND]
selected, rows = None, []
for rung in LADDER:
    subset = primary[primary["rung"] == rung]
    states = subset["arbitration_state"].value_counts(normalize=True)
    summary = {
        "rung": rung, "n": len(subset),
        "focal": subset["Q_pass"].mean(), "target": subset["A_pass"].mean(),
        "both": float(states.get("both", 0.0)),
        "target only": float(states.get("target only", 0.0)),
        "focal only": float(states.get("focal only", 0.0)),
        "neither": float(states.get("neither", 0.0)),
        "invalid": float((subset["technical_failure"] | subset["truncated"]).mean()),
    }
    failed = [name for name, gate in GATES.items() if not gate(summary)]
    summary["verdict"] = "PASS" if not failed else "fail"
    summary["failed_gates"] = "; ".join(failed)
    rows.append(summary)
    if not failed and selected is None:
        selected = rung

table = pd.DataFrame(rows)
print(table[["rung", "n", "focal", "target", "both", "target only", "focal only",
             "neither", "invalid", "verdict"]].to_string(
    index=False, float_format=lambda v: f"{v:.3f}"))
print()
for row in rows:
    if row["failed_gates"]:
        print(f"  {row['rung']:<10} failed: {row['failed_gates']}")

print()
if selected is None:
    print("NONDEGENERATE_FOCAL_NOT_IDENTIFIED")
    print("  no prespecified rung passed the construction gate; the priority "
          "re-test is stopped rather than weakening B further.")
    raise SystemExit(2)
print(f"SELECTED FOCAL = {selected}  (first rung in the fixed order to pass)")

print(f"\n\n### Secondary check: the same rung under the semicolon background\n")
secondary = frame[(frame["background"] != PRIMARY_BACKGROUND)
                  & (frame["rung"] == selected)]
if len(secondary):
    states = secondary["arbitration_state"].value_counts(normalize=True)
    print(f"  n={len(secondary)}  focal={secondary['Q_pass'].mean():.3f}  "
          f"target={secondary['A_pass'].mean():.3f}")
    print("  " + "  ".join(f"{s}={float(states.get(s, 0.0)):.3f}" for s in A.STATES))
    print("\n  Reported only. The gates were applied to the parenthetical "
          "background, as specified.")

if DEST:
    DEST.write_text(json.dumps({
        "selected_focal": selected,
        "ladder_order": list(LADDER),
        "primary_background": PRIMARY_BACKGROUND,
        "gates": list(GATES),
        "per_rung": rows,
        "calibration_tasks": sorted(frame["task_id"].unique().tolist()),
        "n_generations": len(frame),
    }, indent=1))
    print(f"\nwrote {DEST}")
