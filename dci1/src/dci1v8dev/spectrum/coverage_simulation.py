"""Why the coverage gate's thresholds are what they are: simulated, not asserted.

The gate (``coverage.CoverageRule``) is evaluated at **design time** on
calibration-stage coordinates (192 topics × 4 draws; SE(ι) ≈ 0.03–0.05) and
must predict whether the **confirmatory** fit (§11.8, one intercept per
family, d measured on the 384 confirmatory blocks × 8 draws, SE(d) ≈ 0.015)
will identify the common slope with SE(β̂) ≤ ``max_se_beta``. Two things can
go wrong between the two stages: a coordinate believed to sit beyond an
offset may sit inside it (calibration noise), and the fit's slope is
attenuated by measurement error in d (errors-in-variables:
``E[β̂] ≈ β · V(d)/(V(d) + SE(d)²)`` within family). The simulation here
measures both across a grid of true geometries and calibration precisions,
and reports the gate's false-positive / false-negative rates against the
**realised** identifiability, which is the quantity the gate is for.

Truth, per simulated design: identifiable iff (a) the realised SE(β̂) from
the confirmatory coordinates is at most ``max_se_beta``, (b) the realised
coordinates still bracket A by at least ``d_min`` on each side, and (c) the
attenuation of β̂ is within 10 %.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from dci1v8dev.spectrum import precision
from dci1v8dev.spectrum.coverage import CoverageRule, selected_coverage

__all__ = ["SimulationGrid", "attenuation_table", "simulate_gate",
           "threshold_choice"]


@dataclass(frozen=True)
class SimulationGrid:
    offsets_below: Sequence[float] = (0.05, 0.10, 0.15, 0.20, 0.30)
    offsets_above: Sequence[float] = (0.05, 0.10, 0.15, 0.20)
    se_calibration: Sequence[float] = (0.02, 0.035, 0.05, 0.08)
    families: int = 3
    n_sims: int = 400
    se_confirmatory: float = 0.015
    iota_a: float = 0.68
    d_min: float = 0.05
    beta_true: float = 0.40
    seed: int = 2026


def _true_points(rng: np.random.Generator, *, families: int, off_b: float,
                 off_a: float, iota_a: float) -> list[tuple[str, float]]:
    """Each family: one point below A at U(0.6, 1.0)·off_b and one above at
    U(0.6, 1.0)·off_a (so the nominal offset is reached by the farthest
    family, not by every one)."""
    pts = []
    for f in range(families):
        lo = iota_a - off_b * rng.uniform(0.6, 1.0)
        hi = iota_a + off_a * rng.uniform(0.6, 1.0)
        pts.append((f"F{f + 1}", float(lo)))
        pts.append((f"F{f + 1}", float(hi)))
    return pts


def _realised(points_true: Sequence[tuple[str, float]], rng: np.random.Generator,
              *, se_conf: float, beta_true: float, rule: CoverageRule,
              iota_a: float, d_min: float) -> dict[str, Any]:
    d_obs = np.array([d for _, d in points_true]) + rng.normal(0.0, se_conf, len(points_true))
    fams = [f for f, _ in points_true]
    proj = precision.projected_se_beta(list(zip(fams, d_obs.tolist())),
                                       se_point=rule.se_point, block_corr=rule.block_corr)
    # attenuation of the within-family slope by measurement error in d
    by: dict[str, list[float]] = {}
    for f, d in points_true:
        by.setdefault(f, []).append(d)
    var_within = float(np.mean([np.var(v) for v in by.values() if len(v) > 1]))
    reliability = var_within / (var_within + se_conf ** 2) if var_within > 0 else 0.0
    below = [d for d in d_obs if d <= iota_a - d_min]
    above = [d for d in d_obs if d >= iota_a + d_min]
    return {"se_beta_realised": proj["se_beta"],
            "reliability": reliability,
            "attenuation": 1.0 - reliability,
            "bracketed": bool(below and above),
            "identifiable": bool(proj["se_beta"] is not None
                                 and proj["se_beta"] <= rule.max_se_beta
                                 and below and above
                                 and (1.0 - reliability) <= 0.10)}


def simulate_gate(rule: CoverageRule = CoverageRule(), *,
                  grid: SimulationGrid = SimulationGrid()) -> dict[str, Any]:
    rng = np.random.default_rng(grid.seed)
    cells = []
    for off_b in grid.offsets_below:
        for off_a in grid.offsets_above:
            for se_cal in grid.se_calibration:
                fp = fn = tp = tn = 0
                se_real, atten = [], []
                for _ in range(grid.n_sims):
                    pts = _true_points(rng, families=grid.families, off_b=off_b,
                                       off_a=off_a, iota_a=grid.iota_a)
                    hat = [{"candidate": f"{f}:{i}", "family": f,
                            "iota": float(d + rng.normal(0.0, se_cal)),
                            "se_iota": se_cal}
                           for i, (f, d) in enumerate(pts)]
                    gate = selected_coverage(hat, iota_a=grid.iota_a, rule=rule)["identified"]
                    real = _realised(pts, rng, se_conf=grid.se_confirmatory,
                                     beta_true=grid.beta_true, rule=rule,
                                     iota_a=grid.iota_a, d_min=grid.d_min)
                    if real["se_beta_realised"] is not None:
                        se_real.append(real["se_beta_realised"])
                    atten.append(real["attenuation"])
                    if gate and real["identifiable"]:
                        tp += 1
                    elif gate and not real["identifiable"]:
                        fp += 1
                    elif not gate and real["identifiable"]:
                        fn += 1
                    else:
                        tn += 1
                n = grid.n_sims
                cells.append({
                    "offset_below": off_b, "offset_above": off_a,
                    "se_calibration": se_cal,
                    "p_gate_identified": (tp + fp) / n,
                    "p_truly_identifiable": (tp + fn) / n,
                    "false_positive": fp / n, "false_negative": fn / n,
                    "fp_given_gate": fp / (tp + fp) if tp + fp else None,
                    "fn_given_truth": fn / (tp + fn) if tp + fn else None,
                    "se_beta_realised_median": float(np.median(se_real)) if se_real else None,
                    "attenuation_median": float(np.median(atten)),
                })
    return {"rule": {"d_below": rule.d_below, "d_above": rule.d_above,
                     "min_total_span": rule.min_total_span,
                     "max_se_iota": rule.max_se_iota,
                     "max_se_beta": rule.max_se_beta,
                     "min_points_below": rule.min_points_below,
                     "min_points_above": rule.min_points_above,
                     "min_families_per_side": rule.min_families_per_side,
                     "se_point": rule.se_point, "block_corr": rule.block_corr},
            "grid": {"offsets_below": list(grid.offsets_below),
                     "offsets_above": list(grid.offsets_above),
                     "se_calibration": list(grid.se_calibration),
                     "families": grid.families, "n_sims": grid.n_sims,
                     "se_confirmatory": grid.se_confirmatory,
                     "iota_a": grid.iota_a, "beta_true": grid.beta_true,
                     "seed": grid.seed},
            "cells": cells}


def attenuation_table(*, se_confirmatory: float = 0.015,
                      half_spreads: Sequence[float] = (0.03, 0.05, 0.075, 0.10,
                                                       0.125, 0.15, 0.20)) -> list[dict[str, Any]]:
    """Errors-in-variables attenuation of the within-family slope, analytic:
    two points at ±w about the family mean have within-family variance w²."""
    return [{"half_spread": w, "within_family_variance": w * w,
             "reliability": w * w / (w * w + se_confirmatory ** 2),
             "attenuation": 1.0 - w * w / (w * w + se_confirmatory ** 2)}
            for w in half_spreads]


def threshold_choice(base: CoverageRule = CoverageRule(), *,
                     grid: SimulationGrid = SimulationGrid(),
                     min_ppv: float = 0.95,
                     candidate_offsets: Sequence[tuple[float, float]] = (
                         (0.10, 0.10), (0.15, 0.10), (0.15, 0.15), (0.20, 0.15)),
                     candidate_spans: Sequence[float] = (0.15, 0.20, 0.25, 0.30),
                     candidate_se_iota: Sequence[float] = (0.035, 0.05, 0.08)
                     ) -> dict[str, Any]:
    """Prospective choice of the gate's geometry thresholds.

    For every candidate rule (offset pair, minimum span, SE(ι) ceiling) the
    gate is replayed on the same simulated designs (paired by seed) across
    the whole grid of true geometries and calibration precisions the ceiling
    admits, and two operating characteristics are pooled over that grid:
    **PPV** = P(realised identifiable | gate says identified) and **recall**
    = P(gate says identified | realised identifiable). The chosen rule is the
    one with the highest recall among those with PPV ≥ ``min_ppv``; ties go
    to the looser SE(ι) ceiling (more calibrated coordinates count) and then
    the smaller span. The current rule's characteristics are reported beside
    the choice so a reader can see what stricter offsets buy.
    """
    rows = []
    for (d_b, d_a) in candidate_offsets:
        for span in candidate_spans:
            if span < d_b + d_a - 1e-9:
                continue                       # a span below the offsets' sum is never binding
            for se_iota in candidate_se_iota:
                rule = replace(base, d_below=d_b, d_above=d_a,
                               min_total_span=span, max_se_iota=se_iota)
                sim = simulate_gate(rule, grid=replace(grid, se_calibration=tuple(
                    v for v in grid.se_calibration if v <= se_iota + 1e-9)))
                n = grid.n_sims
                tp = sum((c["p_gate_identified"] - c["false_positive"]) * n for c in sim["cells"])
                fp = sum(c["false_positive"] * n for c in sim["cells"])
                fn = sum(c["false_negative"] * n for c in sim["cells"])
                ppv = tp / (tp + fp) if tp + fp else None
                recall = tp / (tp + fn) if tp + fn else None
                rows.append({"d_below": d_b, "d_above": d_a, "min_total_span": span,
                             "max_se_iota": se_iota, "ppv": ppv, "recall": recall,
                             "n_gate_identified": int(tp + fp),
                             "n_truly_identifiable": int(tp + fn),
                             "acceptable": ppv is not None and ppv >= min_ppv})
    ok = [r for r in rows if r["acceptable"]]
    chosen = (max(ok, key=lambda r: (r["recall"], r["max_se_iota"], -r["min_total_span"]))
              if ok else None)
    current = next((r for r in rows if r["d_below"] == base.d_below
                    and r["d_above"] == base.d_above
                    and r["min_total_span"] == base.min_total_span
                    and r["max_se_iota"] == base.max_se_iota), None)
    return {"criterion": {"min_ppv": min_ppv,
                          "truth": "realised SE(beta) <= max_se_beta and A bracketed by "
                                   ">= d_min on both sides after confirmatory "
                                   "re-measurement and attenuation <= 10%"},
            "candidates": rows, "chosen": chosen, "current_rule": current}
