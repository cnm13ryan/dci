#!/usr/bin/env python3
"""How much difficulty spread the §11.8 fit needs: analytic projections, a
Monte Carlo check, and (optionally) the block-level precision inputs
recomputed read-only from a completed confirmatory root.

    python3 tools/v8_spectrum_precision.py [--root <model dir with CONFIRMATORY_GENERATION>]

Writes ``reports/dci1v8dev/prescreen/spectrum_precision.json`` and ``.md``.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v4.errors import ProtocolError
from dci1v8dev.spectrum import precision as P

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v8dev" / "prescreen"


def block_inputs(root: Path) -> dict:
    """Per-block D(B <- X) for every composed companion, read-only."""
    acc: dict = {}
    for path in sorted(glob.glob(str(root / "CONFIRMATORY_GENERATION" /
                                     "backend_runs" / "blocks-*" /
                                     "scored.jsonl"))):
        with open(path) as f:
            for line in f:
                if '"cell_id": "pair:' not in line and \
                        '"cell_id": "solo:B"' not in line:
                    continue
                r = json.loads(line)
                cell = r["cell_id"]
                if cell != "solo:B" and "B" not in cell.split(":")[1].split("+"):
                    continue
                b = next(s for s in r["scores"] if s["kind"] == "B"
                         and s["present"])
                a = acc.setdefault((r["block_id"], cell), [0, 0])
                a[0] += int(b["passed"])
                a[1] += 1
    blocks = sorted({b for b, _ in acc})
    cells = sorted({c for _, c in acc})
    P_ = {c: np.array([acc[(b, c)][0] / acc[(b, c)][1] for b in blocks])
          for c in cells}
    solo = P_["solo:B"]
    D = {}
    for c in cells:
        if c == "solo:B":
            continue
        first, second = c.split(":")[1].split("+")
        comp = second if first == "B" else first
        cfg = "outcome_first" if first == "B" else "outcome_second"
        D[f"{comp}|{cfg}"] = solo - P_[c]
    keys = sorted(D)
    M = np.array([D[k] for k in keys])
    n = len(blocks)
    se = M.std(axis=1, ddof=1) / np.sqrt(n)
    corr = np.corrcoef(M)
    off = corr[~np.eye(len(keys), dtype=bool)]
    return {"root": str(root), "n_blocks": n, "companions": keys,
            "D": M.mean(axis=1).tolist(), "se_blocks": se.tolist(),
            "se_point_median": float(np.median(se)),
            "block_corr_median": float(np.median(off)),
            "block_corr_range": [float(off.min()), float(off.max())],
            "corr": corr.tolist()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    inputs = block_inputs(Path(args.root)) if args.root else None
    se_point = inputs["se_point_median"] if inputs else P.MEASURED["se_point"]
    rho = inputs["block_corr_median"] if inputs else P.MEASURED["block_corr"]
    table = P.design_table(se_point=se_point, block_corr=rho)
    targets = {t: P.leverage_for_se(t, se_point=se_point, block_corr=rho)
               for t in (0.25, 0.125, 0.10, 0.05, 0.025)}
    designs = {
        "v7 registered (3 core + 2 spectrum per family at ±0.20)": [
            (f"{f}:{j}", f, 0.68 + o) for f in ("F1", "F2", "F3")
            for j, o in enumerate((-0.20, 0.0, 0.20))],
        "v7 realised (3 core rungs, one per family)": [
            ("R1", "MK1", 0.697), ("R2", "MK7", 0.666), ("R3", "MK6", 0.630)],
        "v8 candidate: 3 families x (−0.15, centre, +0.10)": [
            (f"{f}:{j}", f, 0.68 + o) for f in ("F1", "F2", "F3")
            for j, o in enumerate((-0.15, 0.0, 0.10))],
        "v8 candidate: 3 families x (−0.15, +0.10) no centre": [
            (f"{f}:{j}", f, 0.68 + o) for f in ("F1", "F2", "F3")
            for j, o in enumerate((-0.15, 0.10))],
        "v8 minimum: 2 families x (−0.10, +0.07)": [
            (f"{f}:{j}", f, 0.68 + o) for f in ("F1", "F2")
            for j, o in enumerate((-0.10, 0.07))],
        "v8 feasible on gemma-e4b-like A (0.73): 3 x (−0.20, +0.08)": [
            (f"{f}:{j}", f, 0.73 + o) for f in ("F1", "F2", "F3")
            for j, o in enumerate((-0.20, 0.08))],
    }
    projections = {}
    for name, pts in designs.items():
        beta = P.projected_se_beta([(f, d) for _, f, d in pts],
                                   se_point=se_point, block_corr=rho)
        d_a = 0.73 if "0.73" in name else 0.68
        try:
            dd = P.projected_se_delta_diff(pts, d_a=d_a, se_point=se_point,
                                           block_corr=rho)
        except ProtocolError as exc:            # zero leverage: fit refuses
            dd = {"error": str(exc)}
        mc = (P.simulate_design(pts, d_a=d_a, beta_true=0.5, n_sims=1000,
                                se_point=se_point, block_corr=rho)
              if beta["se_beta"] is not None else None)
        mc_curv = (P.simulate_design(pts, d_a=d_a, beta_true=0.5, n_sims=1000,
                                     se_point=se_point, block_corr=rho,
                                     curvature=1.0)
                   if beta["se_beta"] is not None else None)
        projections[name] = {"points": pts, "beta": beta, "delta_diff": dd,
                             "monte_carlo": mc,
                             "monte_carlo_curvature_1": mc_curv}
    report = {"inputs": inputs, "se_point": se_point, "block_corr": rho,
              "measured_constants": P.MEASURED, "design_table": table,
              "leverage_for_target_se_beta": targets,
              "projections": projections, "seconds": time.time() - t0}
    (OUT / "spectrum_precision.json").write_text(json.dumps(report, indent=1))
    (OUT / "spectrum_precision.md").write_text(_md(report))
    print("written", OUT, f"se_point={se_point:.4f} rho={rho:.3f}")
    return 0


def _f(x, nd=3):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _md(r: dict) -> str:
    L = ["# Spectrum precision: how much spread the §11.8 fit needs", "",
         f"Per-point SE (D per configuration, 384 blocks × 8 draws): {r['se_point']:.4f}; "
         f"block-level correlation between companions: {r['block_corr']:.3f}"
         + (f" (recomputed read-only from `{r['inputs']['root']}`, "
            f"{r['inputs']['n_blocks']} blocks; range "
            f"{r['inputs']['block_corr_range'][0]:.2f}–{r['inputs']['block_corr_range'][1]:.2f})"
            if r["inputs"] else " (recorded constants)") + ".", "",
         "Under §11.8 (one intercept per family, common slope), "
         "SE(β̂) = σ√(1−ρ)/√leverage with leverage = Σ_f Σ_s (d_fs − d̄_f)²: a family "
         "with one point contributes nothing.", "",
         "## Leverage required", "",
         "| target SE(β̂) | 95% half-width | leverage needed | e.g. 3 families × 2 points at ±w |",
         "|---|---|---|---|"]
    for t, lev in r["leverage_for_target_se_beta"].items():
        w = (lev / 6.0) ** 0.5
        L.append(f"| {t} | {1.96 * float(t):.2f} | {lev:.4f} | w = {w:.3f} |")
    L += ["", "## Designs", "",
          "| design | points | leverage | SE(β̂) | 95% hw | SE(δ_diff) | δ_diff planning hw | "
          "meets 0.05 | MC SD(β̂) | MC bias(β̂) | MC bias with curvature 1.0 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, p in r["projections"].items():
        b, dd, mc, mcc = p["beta"], p["delta_diff"], p["monte_carlo"], p["monte_carlo_curvature_1"]
        L.append(f"| {name} | {b['n_points']} | {b['leverage']:.4f} | {_f(b['se_beta'])} | "
                 f"{_f(b['half_width_95'])} | {_f(dd.get('se_delta_diff'))} | "
                 f"{_f(dd.get('half_width_planning'))} | {dd.get('meets_precondition', '—')} | "
                 f"{_f(mc['beta_sd']) if mc else '—'} | {_f(mc['beta_bias']) if mc else '—'} | "
                 f"{_f(mcc['beta_bias']) if mcc else '—'} |")
    L += ["", "## Symmetric design table", "",
          "| families | points/family | ±w | leverage | SE(β̂) | 95% hw | SE(δ_diff) | δ_diff hw |",
          "|---|---|---|---|---|---|---|---|"]
    for t in r["design_table"]:
        L.append(f"| {t['families']} | {t['points_per_family']} | {t['half_spread']} | "
                 f"{t['leverage']:.4f} | {t['se_beta']:.3f} | {t['half_width_beta_95']:.3f} | "
                 f"{t['se_delta_diff']:.4f} | {t['delta_diff_half_width_planning']:.4f} |")
    if r["inputs"]:
        L += ["", "## Measured per-companion D and SE (read-only)", "",
              "| companion | D | SE |", "|---|---|---|"]
        for k, d, s in zip(r["inputs"]["companions"], r["inputs"]["D"],
                           r["inputs"]["se_blocks"]):
            L.append(f"| {k} | {d:+.4f} | {s:.4f} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
