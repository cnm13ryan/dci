#!/usr/bin/env python3
"""Wording sensitivity and wording-robust ladders. DEVELOPMENT / DIAGNOSTIC.

    python tools/v7_spectrum_dev_wording_summary.py reports/dci1v7/difficulty_spectrum_dev

Pure function of ``counts/wordings_<model>.json`` (tools/v7_spectrum_dev_wordings.py)
and ``spectrum_dev.json`` (for iota_A). Writes ``wording_sensitivity.json`` —
per (model, family) the mean over the family's calibrated severities of
P(S = q) and P(S = 0) for each of the four frozen wording indices — and
``robust_wording_ladders.json`` — per family the ladder iota(q) over the
*robust* wordings only (mean P(S = 0) <= 0.15 over the ladder), Spearman(q,
iota), and a C4-like state (straddles iota_A with >= 3 rungs inside
[0.10, 0.90] spanning >= 0.40). Markers are chance-free (kappa_c <= 0.007),
so iota is P(S = q). Nothing outside ``--out`` is written or read.
"""
from __future__ import annotations

import json
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v7.protocol import constants as C  # noqa: E402

MODELS = ["gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507"]
KINDS = ["A", "MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "MK7", "MK8"]
ROBUST_P_ZERO_MAX = 0.15


def spearman(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    rx = sorted(range(n), key=lambda i: xs[i])
    ry = sorted(range(n), key=lambda i: ys[i])
    px = [0] * n
    py = [0] * n
    for r, i in enumerate(rx):
        px[i] = r
    for r, i in enumerate(ry):
        py[i] = r
    d2 = sum((px[i] - py[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


def main() -> int:
    out = pathlib.Path(sys.argv[1])
    spec = json.load(open(out / "spectrum_dev.json"))
    iota_a = {r["model"]: r["iota_a"] for r in spec["results"]}
    sensitivity: dict = {}
    ladders: dict = {}
    for m in MODELS:
        d = json.load(open(out / "counts" / f"wordings_{m}.json"))
        sensitivity[m] = {}
        ladders[m] = {}
        for kind in KINDS:
            cells = {int(k.split(":")[1]): v for k, v in d["cells"].items()
                     if k.split(":")[0] == kind}
            if not cells:
                continue
            per = {i: [] for i in range(4)}
            zero = {i: [] for i in range(4)}
            allw = []
            by_w = {i: {} for i in range(4)}
            for q, v in sorted(cells.items()):
                tot = n = 0
                for i in range(4):
                    if str(i) in v:
                        per[i].append(v[str(i)]["p_exact"])
                        zero[i].append(v[str(i)]["p_zero"])
                        by_w[i][q] = v[str(i)]["p_exact"]
                        tot += v[str(i)]["p_exact"] * v[str(i)]["n"]
                        n += v[str(i)]["n"]
                allw.append(tot / n)
            means = {i: st.mean(per[i]) for i in range(4) if per[i]}
            zeros = {i: st.mean(zero[i]) for i in range(4) if zero[i]}
            best = max(means, key=means.get)
            sensitivity[m][kind] = {
                "mean_p_exact_by_wording": means,
                "mean_p_zero_by_wording": zeros,
                "best_wording": best,
                "ladder_by_wording": by_w,
                "mean_p_exact_all": st.mean(allw),
            }
            robust = [i for i, z in zeros.items() if z <= ROBUST_P_ZERO_MAX]
            ladder = {}
            for q, v in sorted(cells.items()):
                tot = n = 0
                for i in robust:
                    if str(i) in v:
                        tot += v[str(i)]["p_exact"] * v[str(i)]["n"]
                        n += v[str(i)]["n"]
                if n:
                    ladder[q] = (tot / n, n)
            qs = sorted(ladder)
            ys = [ladder[q][0] for q in qs]
            lo, hi = C.HEADROOM_BAND
            elig = [q for q in qs if lo <= ladder[q][0] <= hi]
            state = None
            if kind != "A" and elig:
                ey = [ladder[q][0] for q in elig]
                below = [q for q in elig if ladder[q][0] < iota_a[m]]
                above = [q for q in elig if ladder[q][0] > iota_a[m]]
                span = max(ey) - min(ey)
                state = {"n_elig": len(elig), "below": len(below),
                         "above": len(above), "span": span,
                         "straddle": bool(below and above),
                         "c4_like": bool(below and above)
                         and len(elig) >= C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY
                         and span >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN}
            ladders[m][kind] = {
                "robust_wordings": [str(i) for i in robust],
                "ladder": {q: {"iota": ladder[q][0], "n": ladder[q][1]}
                           for q in qs},
                "spearman_q_iota": spearman(qs, ys),
                "state": state,
            }
        ladders[m]["_n_tier1_c4_like"] = sum(
            1 for k, v in ladders[m].items()
            if not k.startswith("_") and v["state"] and v["state"]["c4_like"])
    json.dump(sensitivity, open(out / "wording_sensitivity.json", "w"), indent=1)
    json.dump(ladders, open(out / "robust_wording_ladders.json", "w"), indent=1)
    for m in MODELS:
        print(m, "Tier-1 families C4-like under robust wordings:",
              ladders[m]["_n_tier1_c4_like"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
