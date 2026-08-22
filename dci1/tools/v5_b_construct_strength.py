#!/usr/bin/env python3
"""§34 D17: B's chance-compliance curve over the whole v5 focal grid.

**What this measures and why it did not exist.** §12.3 selects the focal
severity whose *solo* compliance is nearest 0.80. B's **chance** compliance
--- the share of answers written with no instruction at all that already
satisfy `every word at most m letters` --- is what says whether B at that
severity is still a construct rather than a formality, and v4r4 recorded it
as a single number at the selected m* alone. That number is 0.000 on all four
models, because v4r4's grid stopped at 10 and no 60-to-120-word answer avoids
an eleven-letter word by accident.

v5 extends the grid to 16, which is the whole of R14's objection: band
membership bought in a region nobody had measured. This recomputes the curve
over 7..16 from v4r4's **load-zero calibration rows** --- answers to the same
stem with no constraint stated --- using v5's own segmenter, so the quantity
means what v5's B means.

**Classification: DEVELOPMENT_EVIDENCE (§30).** It is a v4r4 measurement used
to choose a v5 rule. It is design fitting and it is not evidence that the
rule generalises; §30's declaration applies and the D17 packet says so.

    python3 tools/v5_b_construct_strength.py [--check]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v5.protocol import constants as C          # noqa: E402
from dci1v5.verifiers.statistics import alpha_runs  # noqa: E402

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v5" / "development" / "d7_b_construct_strength.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
#: v4r4's calibration run: one load-zero cell per topic, four draws each.
SOURCE = "{model}/GATE_2_REGIME/backend_runs/calibration"


def unconstrained_texts(model_key: str) -> list[str]:
    base = DCI1 / "evidence" / "dci1v4r4" / SOURCE.format(model=model_key)
    design = {}
    for line in (base / "design.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            design[row["row_id"]] = row["cell_id"]
    texts = []
    for line in (base / "rows.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        # `load0` is v4r4's name for the unconstrained cell. Nothing else in
        # this run is pre-treatment for B.
        if design.get(row.get("row_id"), "").endswith("load0"):
            texts.append(row.get("final_answer") or "")
    return texts


def curve(texts: list[str], grid: list[int]) -> dict[str, object]:
    lengths = [[len(w) for w in alpha_runs(t)] for t in texts]
    lengths = [L for L in lengths if L]
    if not lengths:
        raise SystemExit("no non-empty unconstrained answers")
    per_m = {}
    for m in grid:
        per_m[str(m)] = {
            # kappa_B(m) = P(B passes | unconstrained) = P(longest word <= m)
            "chance_compliance": round(
                sum(1 for L in lengths if max(L) <= m) / len(lengths), 4),
            # the registered `long_word_share` quantity
            "long_word_share": round(statistics.mean(
                sum(1 for x in L if x > m) / len(L) for L in lengths), 4),
            "median_words_over_m": statistics.median(
                sum(1 for x in L if x > m) for L in lengths),
        }
    ordered = sorted(max(L) for L in lengths)
    return {
        "n_answers": len(lengths),
        "median_words_per_answer": statistics.median(len(L) for L in lengths),
        "longest_word": {
            "median": statistics.median(max(L) for L in lengths),
            "q90": ordered[int(0.9 * len(ordered)) - 1],
            "max": ordered[-1]},
        "per_m": per_m,
    }


def build() -> dict[str, object]:
    grid = sorted(set(tuple(C.FOCAL_GRID) + tuple(C.FOCAL_EXTENSION)))
    models = {m: curve(unconstrained_texts(m), grid) for m in MODELS}
    per_m = {}
    for m in grid:
        values = [models[k]["per_m"][str(m)]["chance_compliance"]
                  for k in MODELS]
        per_m[str(m)] = {"min": min(values), "max": max(values),
                         "spread": round(max(values) - min(values), 4)}
    gaps = []
    for lo, hi in zip(grid, grid[1:]):
        gap = per_m[str(hi)]["min"] - per_m[str(lo)]["max"]
        gaps.append({"below": lo, "above": hi, "separation": round(gap, 4)})
    return {
        "_what": "B's chance compliance, word-level bite and per-answer edit "
                 "burden over the whole v5 focal grid, from v4r4's load-zero "
                 "calibration answers",
        "_classification": "DEVELOPMENT_EVIDENCE (§30): a v4r4 measurement "
                           "used to choose a v5 rule. Design fitting, not "
                           "evidence that the rule generalises",
        "_decision": "§34 D17",
        "_source": SOURCE,
        "_segmenter": "dci1v5.verifiers.statistics.alpha_runs, carried "
                      "byte-identically from v3",
        "grid": grid,
        "focal_band": list(C.FOCAL_BAND),
        "models": models,
        "chance_compliance_across_models": per_m,
        "separations": gaps,
        "widest_separation": max(gaps, key=lambda g: g["separation"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed artifact is stale")
    args = parser.parse_args()
    built = build()
    text = json.dumps(built, indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; rerun without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    widest = built["widest_separation"]
    print(f"wrote {OUT}")
    print(f"widest separation in kappa_B: m={widest['below']} -> "
          f"m={widest['above']}, {widest['separation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
