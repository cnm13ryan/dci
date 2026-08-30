"""How much difficulty spread the §11.8 fit needs, computed rather than asserted.

§11.8 fits ``Y_fs = alpha_f + beta d_fs`` by OLS with one intercept per
family. The slope is identified from **within-family** spread only:

    beta_hat = sum_fs (d_fs - dbar_f)(Y_fs - Ybar_f) / sum_fs (d_fs - dbar_f)^2

so a family with one point contributes nothing, and a family with two
points contributes ``(d_1 - d_2)^2 / 2``.

The points share blocks. On the completed development rehearsal
``dci1v7-development`` (qwen3-4b, 384 blocks x 8 draws, 2026-08-29) the
per-companion ``D(B <- R_j)`` has a block-bootstrap SE of 0.012-0.014 per
configuration and the per-block values of different companions correlate at
0.45-0.74 (median about 0.6), so a contrast of two companions in the same
configuration has SE about 0.010-0.013, not the 0.019 independence would
give. ``MEASURED`` records those numbers with their provenance; the tool
``tools/v8_spectrum_precision.py`` recomputes them read-only from any
completed root.

With errors equicorrelated at ``rho`` across points, the slope's variance is
``sigma^2 (1 - rho) sum_fs w_fs^2`` where ``w_fs = (d_fs - dbar_f) /
leverage`` (the weights sum to zero within every family, so the common
component cancels exactly), i.e.

    SE(beta) = sigma sqrt(1 - rho) / sqrt(leverage).

``delta_diff = D(B <- A) - Yhat_A`` with ``Yhat_A = sum w^A_fs Y_fs`` and
``sum w^A = 1``, so its error vector sums to zero as well and
``Var = sigma^2 (1 - rho)(1 + sum (w^A)^2)``.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from dci1v7.analysis.spectrum import SpectrumPoint, fit_difficulty_relation
from dci1v7.protocol import constants as C

__all__ = [
    "MEASURED",
    "design_table",
    "leverage_for_se",
    "projected_se_beta",
    "projected_se_delta_diff",
    "se_point_at",
    "simulate_design",
]

#: Measured on the completed development rehearsal (see module docstring).
#: ``se_point`` is the block-bootstrap SE of one companion's D per
#: configuration at 384 blocks x 8 draws; ``block_corr`` the median
#: between-companion correlation of per-block D.
MEASURED = {"se_point": 0.013, "block_corr": 0.60,
            "se_point_range": [0.009, 0.016],
            "block_corr_range": [0.45, 0.74],
            "source": "dci1v7-development/qwen3-4b CONFIRMATORY_GENERATION "
                      "(384 blocks x 8 draws), read-only, 2026-08-29; SE "
                      "range across the four completed rehearsals"}

#: Šidák planning constant §16.2 quotes for F1 (used conservatively here).
PLANNING_CONSTANT = 2.6310


def _leverage(points: Sequence[tuple[str, float]]) -> tuple[float, dict[str, float]]:
    by: dict[str, list[float]] = {}
    for fam, d in points:
        by.setdefault(fam, []).append(float(d))
    per_family = {f: float(sum((d - sum(ds) / len(ds)) ** 2 for d in ds))
                  for f, ds in by.items()}
    return float(sum(per_family.values())), per_family


def se_point_at(n_blocks: int, *, se_point: float = MEASURED["se_point"],
                measured_blocks: int = C.N_BLOCKS) -> float:
    """The per-point SE at ``n_blocks`` blocks: ``MEASURED["se_point"]`` was
    read at the registered 384 blocks and a block-bootstrap SE scales as
    1/sqrt(blocks). A frame-specific estimate (Approach A,
    docs/V8_FRAME_CONDITIONING.md) rests on the frame's share of the blocks
    and is projected at that share."""
    if n_blocks <= 0:
        raise ValueError("n_blocks must be positive")
    return se_point * math.sqrt(measured_blocks / n_blocks)


def projected_se_beta(points: Sequence[tuple[str, float]], *,
                      se_point: float = MEASURED["se_point"],
                      block_corr: float = MEASURED["block_corr"],
                      n_blocks: int = C.N_BLOCKS) -> dict[str, Any]:
    """Analytic SE of §11.8's slope for a design of (family, d) points,
    at ``n_blocks`` confirmatory blocks (``se_point`` is the value measured
    at the registered ``C.N_BLOCKS`` and is rescaled by ``se_point_at``)."""
    leverage, per_family = _leverage(points)
    se_at = se_point_at(n_blocks, se_point=se_point)
    if leverage <= 0:
        return {"se_beta": None, "leverage": 0.0, "per_family": per_family,
                "half_width_95": None, "n_points": len(points),
                "n_families": len(per_family), "n_blocks": n_blocks,
                "se_point_at_n_blocks": se_at}
    se = se_at * math.sqrt(1.0 - block_corr) / math.sqrt(leverage)
    return {"se_beta": se, "leverage": leverage, "per_family": per_family,
            "half_width_95": 1.96 * se,
            "half_width_planning": PLANNING_CONSTANT * se,
            "n_points": len(points), "n_families": len(per_family),
            "se_point": se_point, "block_corr": block_corr,
            "n_blocks": n_blocks, "se_point_at_n_blocks": se_at}


def projected_se_delta_diff(points: Sequence[tuple[str, str, float]], *,
                            d_a: float, se_point: float = MEASURED["se_point"],
                            block_corr: float = MEASURED["block_corr"]
                            ) -> dict[str, Any]:
    """``points``: (slot, family, d). Uses the registered fit's own
    prediction weights at ``d_a``."""
    fit = fit_difficulty_relation(
        [SpectrumPoint(slot=s, family=f, difficulty=d, loss=0.0)
         for s, f, d in points], predict_at=d_a)
    w = np.array(list(fit.weights_at.values()))
    var = se_point ** 2 * (1.0 - block_corr) * (1.0 + float(np.sum(w ** 2)))
    se = math.sqrt(var)
    return {"se_delta_diff": se, "half_width_planning": PLANNING_CONSTANT * se,
            "meets_precondition":
                PLANNING_CONSTANT * se <= C.PRECISION_PRECONDITIONS["D"],
            "precondition": C.PRECISION_PRECONDITIONS["D"],
            "sum_weights_squared": float(np.sum(w ** 2)),
            "slope_term_at_a": float(abs(d_a - np.mean([d for _, _, d
                                                         in points])))}


def leverage_for_se(target_se_beta: float, *,
                    se_point: float = MEASURED["se_point"],
                    block_corr: float = MEASURED["block_corr"]) -> float:
    """The within-family leverage a target SE(beta) requires."""
    return (se_point * math.sqrt(1.0 - block_corr) / target_se_beta) ** 2


def design_table(*, se_point: float = MEASURED["se_point"],
                 block_corr: float = MEASURED["block_corr"],
                 families: Sequence[int] = (2, 3, 4),
                 points_per_family: Sequence[int] = (2, 3),
                 half_spreads: Sequence[float] = (0.05, 0.075, 0.10, 0.125,
                                                 0.15, 0.20, 0.25),
                 iota_a: float = 0.68) -> list[dict[str, Any]]:
    """SE(beta) and SE(delta_diff) over symmetric designs: each family has
    ``m`` points spread ±w about A (m=3 adds the centre point)."""
    rows = []
    for nf in families:
        for m in points_per_family:
            for w in half_spreads:
                pts = []
                for f in range(nf):
                    fam = f"F{f + 1}"
                    offsets = [-w, w] if m == 2 else [-w, 0.0, w]
                    for j, o in enumerate(offsets):
                        pts.append((f"{fam}:{j}", fam, iota_a + o))
                beta = projected_se_beta([(f, d) for _, f, d in pts],
                                         se_point=se_point,
                                         block_corr=block_corr)
                dd = projected_se_delta_diff(pts, d_a=iota_a,
                                             se_point=se_point,
                                             block_corr=block_corr)
                rows.append({"families": nf, "points_per_family": m,
                             "half_spread": w, "n_points": len(pts),
                             "leverage": beta["leverage"],
                             "se_beta": beta["se_beta"],
                             "half_width_beta_95": beta["half_width_95"],
                             "se_delta_diff": dd["se_delta_diff"],
                             "delta_diff_half_width_planning":
                                 dd["half_width_planning"],
                             "delta_diff_meets_precondition":
                                 dd["meets_precondition"]})
    return rows


def simulate_design(points: Sequence[tuple[str, str, float]], *, d_a: float,
                    beta_true: float, n_sims: int = 2000, seed: int = 7,
                    se_point: float = MEASURED["se_point"],
                    block_corr: float = MEASURED["block_corr"],
                    se_d: float = 0.025, curvature: float = 0.0
                    ) -> dict[str, Any]:
    """Monte Carlo check of the analytic projection, with errors in the
    difficulty coordinate (each d measured at 384 blocks, SE about 0.025)
    and an optional quadratic departure from linearity within family
    (``curvature`` x (d - d_a)^2), which the linear fit absorbs as bias."""
    rng = np.random.default_rng(seed)
    n = len(points)
    fams = sorted({f for _, f, _ in points})
    alpha = {f: 0.05 * i for i, f in enumerate(fams)}
    cov = se_point ** 2 * ((1 - block_corr) * np.eye(n) + block_corr)
    d_true = np.array([d for _, _, d in points])
    slopes, preds = [], []
    for _ in range(n_sims):
        y = np.array([alpha[f] + beta_true * d + curvature * (d - d_a) ** 2
                      for _, f, d in points])
        y = y + rng.multivariate_normal(np.zeros(n), cov)
        d_obs = d_true + rng.normal(0.0, se_d, size=n)
        fit = fit_difficulty_relation(
            [SpectrumPoint(slot=s, family=f, difficulty=float(dd), loss=float(yy))
             for (s, f, _), dd, yy in zip(points, d_obs, y)], predict_at=d_a)
        slopes.append(fit.slope)
        preds.append(fit.predicted_at)
    slopes = np.array(slopes)
    y_a_true = float(np.mean(list(alpha.values()))) + beta_true * d_a
    preds = np.array(preds)
    return {"beta_true": beta_true, "beta_mean": float(slopes.mean()),
            "beta_sd": float(slopes.std(ddof=1)),
            "beta_bias": float(slopes.mean() - beta_true),
            "pred_bias_at_a": float(preds.mean() - y_a_true),
            "pred_sd_at_a": float(preds.std(ddof=1)),
            "analytic_se_beta": projected_se_beta(
                [(f, d) for _, f, d in points], se_point=se_point,
                block_corr=block_corr)["se_beta"],
            "n_sims": n_sims, "se_d": se_d, "curvature": curvature}
