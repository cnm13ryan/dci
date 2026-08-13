#!/usr/bin/env python3
"""Reconstruct what has actually been tested, from the run configs themselves.

Written against `runs/*/config.json` rather than against the write-ups, because
the write-ups are what is being audited. Every coordinate below is read out of a
stored config or derived from the registered constraint parameters; nothing is
recalled.

The coordinate that matters most is the pair (q, N):

  q  the number of semicolons the ARM demands.
  N  the number of sentences the TARGET demands.

A per-sentence rule ("a semicolon in every sentence") does not have a free q: it
demands one per sentence, so q is pinned to N by construction. Only a
whole-answer floor ("at least q semicolons in the answer") has q free. That
distinction is the whole reason the q x N crossing has to be checked rather than
assumed, and it is why `q_kind` is reported alongside `q`.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)

# Registry arms whose parameters are not in any run's extensions manifest.
_REGISTRY_ARMS = {
    "S_SEMICOLON":  ("semicolon", "per_sentence", 1),
    "S_TWOCOMMA":   ("comma",     "per_sentence", 2),
    "S_COMMA":      ("comma",     "per_sentence", 1),
    "U_FMT_SEMI2":  ("semicolon", "whole_answer_exact", 2),
    "U_FMT_COLON1": ("colon",     "whole_answer_exact", 1),
    "B":            (None, "cross_sentence", None),
    "B_SOFT":       (None, "cross_sentence", None),
    "C_L3":         (None, "per_sentence_nonmark", None),
    "C_W3":         (None, "per_sentence_nonmark", None),
    "C_O2":         (None, "cross_sentence", None),
    "A":            (None, "target", None),
}

_TARGET_N = {"A": 4, "X_A2": 2, "X_A3": 3, "X_A5": 5, "X_A6": 6}


def arm_coordinates(arm: str, manifest: dict) -> tuple:
    """(mark, scope, per_unit_demand) for one arm id."""
    entry = (manifest or {}).get("constraints", {}).get(arm)
    if entry is not None:
        params = entry.get("params") or {}
        family = entry.get("rule_family", "")
        mark = params.get("mark")
        if "per_sentence" in family:
            return (mark, "per_sentence", 1)
        if "total" in family:
            return (mark, "whole_answer_min", int(params.get("n", 0)))
        if family == "exact_sentence_count":
            return (None, "target", None)
        return (mark, family, None)
    return _REGISTRY_ARMS.get(arm, (None, "unknown", None))


def load_runs() -> pd.DataFrame:
    rows = []
    for d in sorted(glob.glob(str(Path(__file__).resolve().parent / "runs" / "stage*"))):
        run = Path(d)
        if not (run / "generations.jsonl").exists():
            continue
        config = json.loads((run / "config.json").read_text(encoding="utf-8"))
        manifest = config.get("extensions_manifest")
        selection = config["selection"]
        target = selection["target"]
        n_target = _TARGET_N.get(target)
        model = config["model"]
        for arm in [selection["focal"], *selection["references"]]:
            mark, scope, demand = arm_coordinates(arm, manifest)
            if scope == "per_sentence" and mark == "semicolon":
                q, q_kind = n_target, "implied by N (one per sentence)"
            elif scope == "whole_answer_min" and mark == "semicolon":
                q, q_kind = demand, "free (whole-answer floor)"
            elif scope == "whole_answer_exact" and mark == "semicolon":
                q, q_kind = demand, "free (whole-answer exact)"
            else:
                q, q_kind = 0, "no semicolon demanded"
            rows.append({
                "run": config["stage"],
                "model": model["model_id"].split("/")[-1],
                "dtype": model["dtype"], "temp": model["temperature"],
                "top_p": model["top_p"], "max_new": model["max_new_tokens"],
                "target": target, "N": n_target,
                "arm": arm, "mark": mark or "-", "scope": scope,
                "q": q, "q_kind": q_kind,
                "orders": "+".join(config["orders"]),
                "background": " + ".join(selection["background"]) or "(none)",
                "wording": config.get("paraphrase_id", 0),
                "split": config.get("task_split", "pilot"),
                "offset": config.get("task_offset", 0),
                "n_tasks": config["n_tasks"], "reps": config["replicates"],
                "seed": model["base_seed"],
                "scaffolds": "+".join(config.get("scaffolds", [""])) or "(none)",
                "load": config["load"],
            })
    return pd.DataFrame(rows)


def main() -> int:
    frame = load_runs()
    print("### every (run, arm) cell\n")
    print(frame.to_string(index=False))

    print("\n\n### THE CRITICAL QUESTION: are q and N crossed?\n")
    semis = frame[(frame["mark"] == "semicolon") & frame["N"].notna()]
    grid = (semis.groupby(["q_kind", "N", "q"]).size()
            .rename("cells").reset_index())
    print(grid.to_string(index=False))

    print("\n#### q x N grid, semicolon arms only (count of run-cells)\n")
    pivot = semis.pivot_table(index="q", columns="N", values="run",
                              aggfunc="count", fill_value=0)
    print(pivot.to_string())

    print("\n#### and the same grid restricted to a FREE q (whole-answer floor)\n")
    free = semis[semis["q_kind"].str.startswith("free")]
    if len(free):
        print(free.pivot_table(index="q", columns="N", values="run",
                               aggfunc="count", fill_value=0).to_string())
    else:
        print("(none)")

    print("\n\n### models x arms\n")
    print(frame.pivot_table(index="model", columns="scope", values="run",
                            aggfunc="count", fill_value=0).to_string())

    print("\n\n### one-line-per-dimension coverage\n")
    for column in ("model", "target", "N", "mark", "scope", "q", "orders",
                   "wording", "split", "temp", "reps", "scaffolds", "load"):
        values = sorted({str(v) for v in frame[column].dropna()})
        print(f"  {column:12s} {len(values):2d} distinct: {', '.join(values)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
