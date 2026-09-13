#!/usr/bin/env python3
"""Plot C: exact-count compliance vs severity, split by frozen wording index.
DEVELOPMENT / DIAGNOSTIC. Reads counts/wordings_<model>.json written by
tools/v7_spectrum_dev_wordings.py; writes plots/plotC_wordings_<model>.png."""
from __future__ import annotations
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = pathlib.Path(sys.argv[1])
S = json.load(open(OUT / "spectrum_dev.json"))
IA = {r["model"]: r["iota_a"] for r in S["results"]}
FRAMES = ["w0 'Use the word X exactly q times.'",
          "w1 'Your answer must contain X exactly q times.'",
          "w2 'Include X exactly q times in your answer.'",
          "w3 'The word X must appear exactly q times.'"]
COL = ["#1f77b4", "#d62728", "#ff7f0e", "#2ca02c"]
KINDS = ["A", "MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "MK7", "MK8"]
for model, iota_a in IA.items():
    d = json.load(open(OUT / "counts" / f"wordings_{model}.json"))
    fig, axes = plt.subplots(3, 3, figsize=(12, 9), sharey=True)
    for ax, kind in zip(axes.flatten(), KINDS):
        cells = {int(k.split(":")[1]): v for k, v in d["cells"].items()
                 if k.split(":")[0] == kind}
        qs = sorted(cells)
        for i in range(4):
            ys = [cells[q][str(i)]["p_exact"] if str(i) in cells[q] else float("nan") for q in qs]
            ax.plot(qs, ys, "-o", ms=3.5, color=COL[i], label=FRAMES[i] if kind == "A" else None)
        ax.axhline(iota_a, color="black", lw=0.8)
        ax.axhline(0.90, color="gray", ls="--", lw=0.6); ax.axhline(0.10, color="gray", ls="--", lw=0.6)
        word = "however" if kind == "A" else {"MK1":"thus","MK2":"hence","MK3":"though","MK4":"whereas","MK5":"indeed","MK6":"namely","MK7":"instead","MK8":"overall"}[kind]
        ax.set_title(f"{kind} ({word})", fontsize=9); ax.set_xlabel("q", fontsize=8); ax.tick_params(labelsize=7)
        ax.set_ylim(-0.02, 1.02)
    fig.legend(loc="lower center", ncol=2, fontsize=8, frameon=False)
    fig.suptitle(f"Plot C — P(S = q) in the solo cell by frozen wording index, v7 {model} "
                 f"(192 topics × 1 draw per wording per rung; ι_A = {iota_a:.3f} line)", fontsize=10)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    p = OUT / "plots" / f"plotC_wordings_{model}.png"; fig.savefig(p, dpi=130); plt.close(fig); print(p)
