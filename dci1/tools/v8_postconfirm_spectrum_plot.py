#!/usr/bin/env python3
"""Three publication figures for the registered SPECTRUM arm.

Reads ONLY the committed post-confirmatory tables (``spectrum_points.csv``
and ``spectrum_results.csv`` under ``reports/dci1v8dev/postconfirm/data``),
themselves copies of the signed ``CONFIRMATORY_ANALYSIS`` records. Nothing
scientific is recomputed: the line is drawn from the recorded slope and
family intercepts, and the script asserts per panel --- failing closed ---
that the line it draws passes through the record's own
``predicted_loss_at_A_pp`` at the record's own ``difficulty_a``.

**On the x axis.** iota is ``(solo - chance) / (1 - chance)``
(``calibration_table.instructed_compliance``): a chance-corrected stand-alone
**compliance**. Higher iota is an EASIER companion. The protocol names it
"the difficulty coordinate" because it indexes difficulty, but it runs the
other way, and its own spectrum slots agree --- ``SPECTRUM_LOW``/``below``
sits at low iota. The axis is therefore labelled as compliance and carries an
explicit harder/easier direction cue. iota is NOT transformed: the registered
beta is defined on this scale, and flipping the axis would put a sign on the
plotted line that the record does not contain.

    tools/v8_postconfirm_spectrum_plot.py --data <dir> --out <dir>
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

MODELS = ("qwen3-4b", "qwen3-4b-instruct-2507",
          "gemma-3n-e2b-it", "gemma-3n-e4b-it")
NAME = {"qwen3-4b": "Qwen3-4B",
        "qwen3-4b-instruct-2507": "Qwen3-4B-Instruct-2507",
        "gemma-3n-e2b-it": "Gemma-3n-E2B-it",
        "gemma-3n-e4b-it": "Gemma-3n-E4B-it"}
SHORT = {"qwen3-4b": "Qwen3-4B",
         "qwen3-4b-instruct-2507": "Qwen3-4B-Instr-2507",
         "gemma-3n-e2b-it": "Gemma-3n-E2B-it",
         "gemma-3n-e4b-it": "Gemma-3n-E4B-it"}
ORDERS = ("B first", "B second")
FRAMES = ("0", "1", "2", "3")
EQUIV_PP = 10.0
XLABEL = "companion stand-alone compliance ι  (chance-corrected)"
XCUE = "← harder companion            easier companion →"

MUTED = "#9AA5AD"          # ordinary cases
INK = "#1F2933"            # fit line, text
A_COLOUR = "#C2185B"       # A, one consistent highlight everywhere
POS = "#1565C0"            # beta > 0, interval excludes zero
NEG = "#C62828"            # beta < 0, interval excludes zero
NULL = "#B0BEC5"           # interval spans zero
L3E = "#2E7D32"
L3D = "#EF6C00"
NOLEVEL = "#37474F"


def _f(row, key, default=None):
    v = row.get(key, "")
    return default if v in ("", "None", None) else float(v)


def load(data: Path):
    points, fits = {}, {}
    for r in csv.DictReader((data / "spectrum_points.csv").open()):
        key = (r["model"], r["frame"], r["order"])
        points.setdefault(key, {"companions": [], "focal": None})
        if r["is_focal"] == "True":
            points[key]["focal"] = r
        else:
            points[key]["companions"].append(r)
    for r in csv.DictReader((data / "spectrum_results.csv").open()):
        fits[(r["model"], r["frame"], r["order"])] = r
    return points, fits


def fit_line(fit):
    """``mean(family intercepts) + beta * iota``, in pp, asserted against the
    record's own prediction at iota_A."""
    beta = _f(fit, "slope")
    alpha_bar = statistics.fmean(json.loads(fit["intercepts"]).values())
    drawn = (alpha_bar + beta * _f(fit, "difficulty_a")) * 100.0
    recorded = _f(fit, "predicted_loss_at_A_pp")
    if abs(drawn - recorded) > 1e-3:
        raise SystemExit(
            f"{fit['model']} f{fit['frame']} {fit['order']}: drawn line "
            f"predicts {drawn:.4f} pp at iota_A, record says {recorded:.4f}")
    return alpha_bar * 100.0, beta * 100.0


def beta_class(fit):
    lo, hi = _f(fit, "slope_lower"), _f(fit, "slope_upper")
    if lo is not None and lo > 0:
        return "pos"
    if hi is not None and hi < 0:
        return "neg"
    return "null"


def dd_class(fit):
    return fit["delta_difficulty_reading"] or "NO_LEVEL"


# ============================================================ FIGURE 1
def figure_forest(fits, out: Path):
    """Two panels, rows grouped by model then prompt order, read top to
    bottom, shape by order, colour only on the exceptional cases."""
    display, seps, group_at, order_at = [], [], [], []
    for m in MODELS:
        block_start = len(display)
        for o in ORDERS:
            sub = [(m, f, o) for f in FRAMES if (m, f, o) in fits]
            if not sub:
                continue
            order_at.append((len(display) + (len(sub) - 1) / 2.0, o))
            display.extend(sub)
        group_at.append((block_start + (len(display) - block_start - 1) / 2.0, m))
        seps.append(len(display) - 0.5)
    seps = seps[:-1]
    n = len(display)
    rows = [(n - 1 - i, key) for i, key in enumerate(display)]   # top-down
    group_at = [(n - 1 - c, m) for c, m in group_at]
    order_at = [(n - 1 - c, o) for c, o in order_at]
    seps = [n - 1 - c for c in seps]

    fig, (axl, axr) = plt.subplots(
        1, 2, figsize=(13.0, 0.40 * n + 3.0),
        gridspec_kw={"width_ratios": [1.0, 1.35], "wspace": 0.05})

    n_pos = sum(1 for k in fits if beta_class(fits[k]) == "pos")
    n_neg = sum(1 for k in fits if beta_class(fits[k]) == "neg")
    n_null = len(fits) - n_pos - n_neg
    dd = [dd_class(fits[k]) for k in fits]

    for ax in (axl, axr):
        for sy in seps:
            ax.axhline(sy, color="#DCE1E4", lw=1.0, zorder=0)

    for ypos, key in rows:
        fit = fits[key]
        marker = "o" if key[2] == "B first" else "s"
        cls = beta_class(fit)
        exceptional = cls == "neg"
        colour = NEG if exceptional else (MUTED if cls == "pos" else NULL)
        lw = 3.0 if exceptional else 1.9
        axl.plot([_f(fit, "slope_lower"), _f(fit, "slope_upper")],
                 [ypos, ypos], color=colour, lw=lw, solid_capstyle="round",
                 zorder=3 if exceptional else 2)
        axl.scatter([_f(fit, "slope")], [ypos], s=52 if exceptional else 32,
                    color=colour, marker=marker, zorder=4,
                    edgecolor="white", linewidth=0.7)
        r = dd_class(fit)
        exc_r = r in ("L3d", "NO_LEVEL")
        colour_r = {"L3d": L3D, "NO_LEVEL": NOLEVEL}.get(r, MUTED)
        axr.plot([_f(fit, "delta_difficulty_joint_lower_pp"),
                  _f(fit, "delta_difficulty_joint_upper_pp")],
                 [ypos, ypos], color=colour_r, lw=3.0 if exc_r else 1.9,
                 solid_capstyle="round", zorder=3 if exc_r else 2)
        axr.scatter([_f(fit, "delta_difficulty_pp")], [ypos],
                    s=52 if exc_r else 32, color=colour_r, marker=marker,
                    zorder=4, edgecolor="white", linewidth=0.7)

    for ax in (axl, axr):
        ax.set_yticks([yp for yp, _ in rows])
        ax.set_ylim(-0.7, n - 0.3)
        ax.tick_params(axis="y", length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#B0BEC5")
    axl.set_yticklabels([f"f{k[1]}" for _, k in rows], fontsize=9.5)
    axr.set_yticklabels([])
    for ax in (axl, axr):
        ax.axvline(0, color=INK, lw=1.5, zorder=1)
    axr.axvspan(-EQUIV_PP, EQUIV_PP, color="#000000", alpha=0.055, lw=0,
                zorder=0)

    for ypos, o in order_at:
        axl.annotate(o, xy=(-0.105, ypos),
                     xycoords=("axes fraction", "data"), ha="right",
                     va="center", fontsize=8.5, color="#62727B",
                     annotation_clip=False)
    for ypos, m in group_at:
        axl.annotate(NAME[m], xy=(-0.185, ypos),
                     xycoords=("axes fraction", "data"), ha="right",
                     va="center", fontsize=11, color=INK, weight="bold",
                     annotation_clip=False)

    axl.set_title("A   Does the companion's compliance predict B's loss?\n"
                  "fitted slope β, simultaneous 95% interval",
                  fontsize=11, pad=26, loc="left")
    axr.set_title("B   Does A sit above, below or on that relation?\n"
                  "δ_difficulty, joint 95% decision interval",
                  fontsize=11, pad=26, loc="left")
    axl.set_xlabel("β  (pp of B-loss per unit of companion compliance ι)\n"
                   "β > 0 means B fares WORSE beside an EASIER companion",
                   fontsize=9)
    axr.set_xlabel("δ_difficulty = observed D(B←A) − loss predicted at ι_A, pp\n"
                   "negative: A costs B LESS than its compliance predicts",
                   fontsize=9)
    axl.annotate(f"{n_pos} of {len(fits)} positive   ·   {n_neg} negative   "
                 f"·   {n_null} span zero",
                 xy=(0.0, 1.012), xycoords="axes fraction", fontsize=9.5,
                 color="#4A5560", ha="left", va="bottom")
    axr.annotate(f"{dd.count('L3e')} within ±10 pp (L3e)   ·   "
                 f"{dd.count('L3d')} above prediction (L3d)   ·   "
                 f"{dd.count('NO_LEVEL')} large and negative, no level",
                 xy=(0.0, 1.012), xycoords="axes fraction", fontsize=9.5,
                 color="#4A5560", ha="left", va="bottom")

    hl = [Line2D([], [], marker="o", ls="", color=INK, markersize=6,
                 markeredgecolor="white", label="B stated first"),
          Line2D([], [], marker="s", ls="", color=INK, markersize=6,
                 markeredgecolor="white", label="B stated second"),
          Line2D([], [], color=MUTED, lw=1.9,
                 label="β > 0: B worse beside an easier companion (the majority)"),
          Line2D([], [], color=NEG, lw=3.0,
                 label="β < 0: the intuitive direction — harder companions cost more"),
          Line2D([], [], color=NULL, lw=1.9, label="interval spans zero")]
    hr = [Line2D([], [], color=MUTED, lw=1.9,
                 label="L3e: A within ±10 pp of the prediction"),
          Line2D([], [], color=L3D, lw=3.0,
                 label="L3d: A above the prediction, interval excludes zero"),
          Line2D([], [], color=NOLEVEL, lw=3.0,
                 label="no registered level: residual large and negative"),
          Patch(facecolor="#000000", alpha=0.055,
                label="±10 pp registered equivalence region")]
    axl.legend(handles=hl, fontsize=8.5, frameon=False, loc="upper left",
               bbox_to_anchor=(-0.26, -0.055))
    axr.legend(handles=hr, fontsize=8.5, frameon=False, loc="upper left",
               bbox_to_anchor=(0.0, -0.055))
    fig.suptitle("The registered SPECTRUM arm: all 28 entering "
                 "model × wording-frame × prompt-order conditions",
                 fontsize=13.5, y=0.988)
    fig.tight_layout(rect=(0.115, 0.075, 1, 0.955))
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig1_spectrum_forest.{ext}", dpi=300,
                    bbox_inches="tight")
    plt.close(fig)


# ============================================================ FIGURE 2
def figure_explainer(points, fits, out: Path,
                     key=("gemma-3n-e4b-it", "1", "B second")):
    fit, entry = fits[key], points[key]
    alpha_pp, beta_pp = fit_line(fit)
    comps = entry["companions"]
    xs = [_f(c, "difficulty_iota") for c in comps]
    ys = [_f(c, "B_loss_pp") for c in comps]
    lo, hi = json.loads(fit["fitted_range"])
    ia = _f(fit, "difficulty_a")
    pred = _f(fit, "predicted_loss_at_A_pp")
    obs = _f(fit, "D_B_from_A_pp")
    d = _f(fit, "delta_difficulty_pp")
    dlo = _f(fit, "delta_difficulty_joint_lower_pp")
    dhi = _f(fit, "delta_difficulty_joint_upper_pp")

    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    span = [min(lo, ia) - 0.035, max(hi, ia) + 0.045]
    ax.axhspan(pred - EQUIV_PP, pred + EQUIV_PP, color="#000000", alpha=0.05,
               lw=0, zorder=0)
    b_lo, b_hi = _f(fit, "slope_lower"), _f(fit, "slope_upper")
    cx = statistics.fmean(xs)
    cy = alpha_pp + beta_pp * cx
    ax.fill_between(span,
                    [cy + b_lo * 100 * (x - cx) for x in span],
                    [cy + b_hi * 100 * (x - cx) for x in span],
                    color=INK, alpha=0.10, lw=0, zorder=1)
    ax.plot(span, [alpha_pp + beta_pp * x for x in span], color=INK, lw=2.0,
            zorder=3)
    ax.scatter(xs, ys, s=62, color=MUTED, edgecolor="white", linewidth=0.8,
               zorder=4)
    for c, x, yv in zip(comps, xs, ys):
        ax.annotate(c["slot"], (x, yv), textcoords="offset points",
                    xytext=(0, 9), fontsize=7.5, color="#62727B", ha="center")

    # the residual, as a labelled vertical segment
    ax.plot([ia, ia], [pred, obs], color=A_COLOUR, lw=2.4, zorder=5)
    ax.plot([ia, ia], [pred + dlo, pred + dhi], color=A_COLOUR, lw=6.5,
            alpha=0.28, solid_capstyle="butt", zorder=4)
    ax.scatter([ia], [pred], s=150, facecolor="white", edgecolor=A_COLOUR,
               linewidth=2.0, zorder=6, marker="o")
    ax.scatter([ia], [obs], s=460, color=A_COLOUR, marker="*",
               edgecolor="white", linewidth=1.0, zorder=7)

    dx = (span[1] - span[0])
    ax.annotate(f"A observed: {obs:.1f} pp",
                xy=(ia - 0.012 * dx, obs), xytext=(ia - 0.215 * dx, obs - 1.5),
                fontsize=10.5, color=A_COLOUR, weight="bold",
                ha="right", va="center",
                arrowprops=dict(arrowstyle="-", color=A_COLOUR, lw=1.0))
    ax.annotate(f"predicted for a companion of A's compliance: {pred:.1f} pp",
                xy=(ia - 0.012 * dx, pred), xytext=(ia - 0.055 * dx, pred + 12),
                fontsize=10.5, color=A_COLOUR, ha="right",
                arrowprops=dict(arrowstyle="-", color=A_COLOUR, lw=1.0))
    ax.annotate(f"δ = {d:.1f} pp\n[{dlo:.1f}, {dhi:.1f}]",
                xy=(ia, (pred + obs) / 2),
                xytext=(ia + 0.13 * dx, (pred + obs) / 2),
                fontsize=11, color=A_COLOUR, fontweight="bold",
                va="center", ha="left",
                arrowprops=dict(arrowstyle="-[, widthB=1.1, lengthB=0.35",
                                color=A_COLOUR, lw=1.2))
    ax.annotate(f"fitted relation, β = {beta_pp / 100:+.3f}",
                xy=(span[0] + 0.06 * dx,
                    alpha_pp + beta_pp * (span[0] + 0.06 * dx)),
                xytext=(span[0] + 0.03 * dx,
                        alpha_pp + beta_pp * span[0] - 13),
                fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.0))

    ax.set_xlim(*span)
    ax.set_xlabel(f"{XLABEL}\n{XCUE}", fontsize=10.5, labelpad=10)
    ax.set_ylabel("loss in B-compliance beside the companion, pp\n"
                  "(B solo minus B beside it)", fontsize=10.5)
    ax.set_title("A is not unusually harmful here — it costs B 11.5 points "
                 "LESS\nthan its stand-alone compliance predicts\n",
                 fontsize=13.5, loc="left", color=INK)
    ax.annotate(f"{NAME[key[0]]} · wording frame {key[1]} · {key[2]} — "
                "the one condition whose LOCAL contrast put A above its "
                "three matched references",
                xy=(0.0, 1.005), xycoords="axes fraction", fontsize=9.5,
                color="#62727B", ha="left", va="bottom")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#B0BEC5")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=MUTED, markersize=8,
               markeredgecolor="white", label="spectrum companion"),
        Line2D([], [], marker="*", ls="", color=A_COLOUR, markersize=17,
               markeredgecolor="white", label="A, observed"),
        Line2D([], [], marker="o", ls="", markerfacecolor="white",
               markeredgecolor=A_COLOUR, markersize=10, markeredgewidth=2,
               label="A, predicted by the fit"),
        Line2D([], [], color=A_COLOUR, lw=6.5, alpha=0.28,
               label="joint 95% interval on δ"),
        Line2D([], [], color=INK, lw=2.0, label="registered fit"),
        Patch(facecolor=INK, alpha=0.10, label="simultaneous interval on β"),
        Patch(facecolor="#000000", alpha=0.05, label="±10 pp of the prediction"),
    ], fontsize=9, frameon=False, loc="upper center", ncol=4,
        bbox_to_anchor=(0.5, -0.20))
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 - 0.04 * (y1 - y0), y1 + 0.06 * (y1 - y0))
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig2_spectrum_explainer.{ext}", dpi=300,
                    bbox_inches="tight")
    plt.close(fig)


# ============================================================ FIGURE 3
def figure_grid(points, fits, out: Path):
    rows = [(m, o) for m in MODELS for o in ORDERS]
    fig, axes = plt.subplots(len(rows), len(FRAMES), squeeze=False,
                             figsize=(3.05 * len(FRAMES), 2.55 * len(rows)))
    for ri, (m, o) in enumerate(rows):
        for ci, f in enumerate(FRAMES):
            ax = axes[ri][ci]
            key = (m, f, o)
            fit, entry = fits.get(key), points.get(key)
            if ri == 0:
                ax.annotate(f"wording frame {f}", xy=(0.5, 1.30),
                            xycoords="axes fraction", ha="center",
                            fontsize=12, color=INK, fontweight="semibold",
                            annotation_clip=False)
            if fit is None:
                ax.set_xticks([]); ax.set_yticks([])
                for s_ in ("top", "right", "left", "bottom"):
                    ax.spines[s_].set_visible(False)
                ax.text(0.5, 0.5, "does not enter\nthe SPECTRUM arm",
                        ha="center", va="center", fontsize=8.5,
                        color="#B0BEC5", transform=ax.transAxes)
                continue
            alpha_pp, beta_pp = fit_line(fit)
            comps = entry["companions"]
            xs = [_f(c, "difficulty_iota") for c in comps]
            ys = [_f(c, "B_loss_pp") for c in comps]
            lo, hi = json.loads(fit["fitted_range"])
            ia = _f(fit, "difficulty_a")
            pred = _f(fit, "predicted_loss_at_A_pp")
            obs = _f(fit, "D_B_from_A_pp")
            span = [min(lo, ia) - 0.03, max(hi, ia) + 0.03]
            ax.axhspan(pred - EQUIV_PP, pred + EQUIV_PP, color="#000000",
                       alpha=0.05, lw=0, zorder=0)
            b_lo, b_hi = _f(fit, "slope_lower"), _f(fit, "slope_upper")
            cx = statistics.fmean(xs); cy = alpha_pp + beta_pp * cx
            ax.fill_between(span,
                            [cy + b_lo * 100 * (x - cx) for x in span],
                            [cy + b_hi * 100 * (x - cx) for x in span],
                            color=INK, alpha=0.10, lw=0, zorder=1)
            ax.plot(span, [alpha_pp + beta_pp * x for x in span], color=INK,
                    lw=1.6, zorder=3)
            ax.scatter(xs, ys, s=34, color=MUTED, edgecolor="white",
                       linewidth=0.6, zorder=4)
            ax.plot([ia, ia], [pred, obs], color=A_COLOUR, lw=1.6, zorder=5)
            ax.scatter([ia], [pred], s=52, facecolor="white",
                       edgecolor=A_COLOUR, linewidth=1.5, zorder=6)
            ax.scatter([ia], [obs], s=170, color=A_COLOUR, marker="*",
                       edgecolor="white", linewidth=0.7, zorder=7)
            ax.set_xlim(*span)
            ax.set_title(f"β = {beta_pp / 100:+.3f}    "
                         f"δ = {_f(fit, 'delta_difficulty_pp'):+.1f} pp",
                         fontsize=9, color="#4A5560", pad=4)
            ax.tick_params(labelsize=7.5)
            for s_ in ("top", "right"):
                ax.spines[s_].set_visible(False)
            for s_ in ("left", "bottom"):
                ax.spines[s_].set_color("#B0BEC5")
    fig.tight_layout(rect=(0.075, 0.075, 1, 0.945))
    for ri, (m, o) in enumerate(rows):
        box = axes[ri][0].get_position()
        fig.text(0.026, (box.y0 + box.y1) / 2, f"{SHORT[m]}\n{o}",
                 rotation=90, va="center", ha="center", fontsize=10.5,
                 color=INK, weight="bold")
    bottom = axes[-1][0].get_position()
    fig.text(0.54, bottom.y0 - 0.030, f"{XLABEL}      {XCUE}",
             ha="center", va="top", fontsize=11, color=INK)
    fig.legend(handles=[
        Line2D([], [], marker="o", ls="", color=MUTED, markersize=7,
               markeredgecolor="white", label="spectrum companion"),
        Line2D([], [], marker="*", ls="", color=A_COLOUR, markersize=15,
               markeredgecolor="white", label="A, observed loss"),
        Line2D([], [], marker="o", ls="", markerfacecolor="white",
               markeredgecolor=A_COLOUR, markersize=8, markeredgewidth=1.5,
               label="A, predicted by the fit"),
        Line2D([], [], color=A_COLOUR, lw=1.6, label="δ_difficulty"),
        Line2D([], [], color=INK, lw=1.6, label="registered fit"),
        Patch(facecolor=INK, alpha=0.10, label="simultaneous interval on β"),
        Patch(facecolor="#000000", alpha=0.05,
              label="±10 pp of the prediction"),
    ], loc="lower center", ncol=7, fontsize=9.5, frameon=False,
        bbox_to_anchor=(0.5, 0.008))
    fig.suptitle("All 28 SPECTRUM conditions — companion stand-alone "
                 "compliance against the loss in B-compliance\n"
                 "y axis: loss in B-compliance beside the companion, pp "
                 "(each panel on its own scale)",
                 fontsize=12.5, y=0.982)
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig3_spectrum_grid.{ext}", dpi=220,
                    bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data, out = Path(args.data).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    points, fits = load(data)
    for key in fits:                      # assert every panel's fit up front
        fit_line(fits[key])
    figure_forest(fits, out)
    figure_explainer(points, fits, out)
    figure_grid(points, fits, out)
    print(json.dumps({"cells": len(fits), "figures": sorted(
        p.name for p in out.iterdir() if p.suffix in (".pdf", ".png"))},
        indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
