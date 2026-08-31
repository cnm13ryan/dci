#!/usr/bin/env python3
"""Build the DCI-1 v7 main-paper figures and Table 1.

Reads the verified dossier (`dci1/reports/dci1v7/dossier/`), cross-checks every
plotted number a second time against the **signed `FINAL_REPORT` records** in the
development-lane evidence trees, and writes PDF/SVG/PNG plus the exact CSV each
figure consumes.

Only the four **canonical** lanes are plotted: one lane per model. The two
`repeat` lanes are the same model re-run on a later commit with re-selected
reference severities; they are reproducibility evidence, never extra
observations, and appear in no main-paper figure.

All results are development-rehearsal evidence. The registered v7 study produced
zero confirmatory rows.

Shared visual grammar, identical across Figures 2-4:
  colour  = the companion instruction present in the composed cell
            (blue = A, rust = B, teal = the matched reference pool);
            neutral ink where the mark is a contrast between two arms.
  shape   = what the mark is: circle a loss measured on B, square a loss
            measured on A, hexagon the mean loss over the three matched
            references, diamond a contrast between two composed arms.
  fill    = the measured instruction's position (filled first, open second).
Colour is always redundant with shape and fill, so every figure survives
grayscale printing.

Usage:  python dci1/tools/v7_paper_figures.py [--out DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

REPO = Path(__file__).resolve().parents[2]
DOSSIER = REPO / "dci1" / "reports" / "dci1v7" / "dossier"
EVIDENCE = REPO / "dci1" / "evidence"
DEFAULT_OUT = REPO / "dci1" / "reports" / "dci1v7" / "paper_figures"

# Colourblind-safe, validated with the dataviz skill's own checker:
#   node scripts/validate_palette.js "#0173B2,#B4590A,#029E73" \
#        --mode light --pairs all      ->  ALL CHECKS PASS
C_A = "#0173B2"      # companion is A  ("use the word however exactly n times")
C_B = "#B4590A"      # companion is B  ("every word at most m letters")
C_R = "#029E73"      # companion is the matched reference pool R1..R3
INK = "#1A1A1A"
INK_2 = "#555555"
GRID = "#D8D8D8"
RULE = "#9A9A9A"
BAND = "#EEEEEE"

M_B = "o"            # B measured
M_A = "s"            # A measured
M_CONTRAST = "D"     # a contrast between two composed arms
M_RBAR = "h"         # the mean loss over the three matched references

MODEL_ORDER = ["gemma-3n-e2b-it", "gemma-3n-e4b-it",
               "qwen3-4b", "qwen3-4b-instruct-2507"]
MODEL_LABEL = {
    "gemma-3n-e2b-it": "Gemma 3n E2B",
    "gemma-3n-e4b-it": "Gemma 3n E4B",
    "qwen3-4b": "Qwen3 4B",
    "qwen3-4b-instruct-2507": "Qwen3 4B Instruct",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.2,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.0,
    "xtick.major.size": 3,
    "ytick.major.size": 0,
    "axes.edgecolor": "#4A4A4A",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

PP = 100.0  # compliance -> percentage points
LEFT_ARROW = "⟵"
RIGHT_ARROW = "⟶"
EMDASH = "—"


# ---------------------------------------------------------------- data layer
def read(name):
    with (DOSSIER / name).open() as fh:
        return list(csv.DictReader(fh))


def num(x):
    if x is None or x == "":
        return None
    return float(x)


def canonical_lanes():
    lanes = {l["model"]: l for l in read("lanes.csv") if l["lane_role"] == "canonical"}
    missing = [m for m in MODEL_ORDER if m not in lanes]
    if missing:
        raise SystemExit(f"no canonical lane for {missing}")
    return lanes


def master_index(rows):
    return {(r["lane_id"], r["member"], r["configuration"] or "cross"): r for r in rows}


def build_rows():
    """One record per (model, B position). Eight canonical configurations."""
    lanes = canonical_lanes()
    master = master_index(read("estimands_master.csv"))
    cells = read("cell_compliance.csv")
    forest = {(r["lane_id"], r["outcome_position"]): r
              for r in read("fig1_delta_r_forest.csv")}

    def cell_level(lane, member, cfg, role):
        for c in cells:
            if (c["lane_id"] == lane and c["member"] == member
                    and c["configuration"] == cfg and c["role"] == role):
                return num(c["compliance_rate"]), c["cell"]
        return None, None

    out = []
    for model in MODEL_ORDER:
        lane = lanes[model]["lane_id"]
        for cfg, bpos in (("outcome_first", "first"), ("outcome_second", "second")):
            # B first  <=> the prompt lists B then A;  B second <=> A then B.
            # A is measured in that SAME prompt at the complementary position,
            # so its configuration is the complement of B's (v5 s11.1: the two
            # losses of one prompt are read from one cell, not two).
            dab_cfg = "outcome_second" if cfg == "outcome_first" else "outcome_first"
            dr = master[(lane, "Delta_R", cfg)]
            dba = master[(lane, "D(B<-A)", cfg)]
            dab = master[(lane, "D(A<-B)", dab_cfg)]
            solo_b, _ = cell_level(lane, "D(B<-A)", cfg, "solo")
            comp_b, comp_b_cell = cell_level(lane, "D(B<-A)", cfg, "composed")
            solo_a, _ = cell_level(lane, "D(A<-B)", dab_cfg, "solo")
            comp_a, comp_a_cell = cell_level(lane, "D(A<-B)", dab_cfg, "composed")
            f = forest[(lane, bpos)]
            d_ba, d_r = num(dba["point_estimate"]), num(dr["point_estimate"])
            out.append({
                "model": model, "model_label": MODEL_LABEL[model], "lane_id": lane,
                "b_position": bpos,
                "prompt_order": "B+A" if bpos == "first" else "A+B",
                "n_star": int(lanes[model]["n_star"]),
                "m_star": int(lanes[model]["m_star"]),
                "n_blocks": int(dr["n_blocks"]),
                "D_B_from_A": d_ba,
                "D_B_from_A_sim_lower": num(dba["simultaneous_lower"]),
                "D_B_from_A_sim_upper": num(dba["simultaneous_upper"]),
                "D_B_from_A_position_confounded": bpos == "second",
                "solo_B": solo_b, "B_given_A": comp_b, "B_given_A_cell": comp_b_cell,
                "D_B_from_Rbar_DERIVED": d_ba - d_r,
                "Delta_R": d_r,
                "Delta_R_sim_lower": num(dr["simultaneous_lower"]),
                "Delta_R_sim_upper": num(dr["simultaneous_upper"]),
                "Delta_R_marg_lower": num(dr["marginal_lower"]),
                "Delta_R_marg_upper": num(dr["marginal_upper"]),
                "Delta_R_half_width": num(dr["realised_half_width"]),
                "Delta_R_precision_met": dr["precision_met"],
                "Delta_R_direction": f["direction"],
                "attainable_min": num(f["attainable_min"]),
                "attainable_max": num(f["attainable_max"]),
                "positive_direction_compressed":
                    f["positive_direction_compressed"] == "True",
                "negative_direction_compressed":
                    f["negative_direction_compressed"] == "True",
                "compressed_by": f["compressed_by"],
                "A_measured_position": "second" if bpos == "first" else "first",
                "D_A_from_B": num(dab["point_estimate"]),
                "D_A_from_B_sim_lower": num(dab["simultaneous_lower"]),
                "D_A_from_B_sim_upper": num(dab["simultaneous_upper"]),
                "D_A_from_B_position_confounded": dab_cfg == "outcome_second",
                "solo_A": solo_a, "A_given_B": comp_a, "A_given_B_cell": comp_a_cell,
                "evidence_status": dr["evidence_status"],
                "source_artifact": dr["source_artifact"],
            })
    return out


def build_order_rows():
    """F11 order contrasts: one per (model, measured instruction)."""
    lanes = canonical_lanes()
    master = master_index(read("estimands_master.csv"))
    out = []
    for model in MODEL_ORDER:
        lane = lanes[model]["lane_id"]
        for member, measured, companion in (("Ord_B", "B", "A"), ("Ord_A", "A", "B")):
            r = master[(lane, member, "cross")]
            if r["status"] != "IDENTIFIED":
                continue
            out.append({
                "model": model, "model_label": MODEL_LABEL[model], "lane_id": lane,
                "member": member, "measured_instruction": measured,
                "companion": companion,
                "definition": (f"D({measured}<-{companion}) | {measured} stated first "
                               f"- D({measured}<-{companion}) | {measured} stated second"),
                "estimate": num(r["point_estimate"]),
                "sim_lower": num(r["simultaneous_lower"]),
                "sim_upper": num(r["simultaneous_upper"]),
                "marg_lower": num(r["marginal_lower"]),
                "marg_upper": num(r["marginal_upper"]),
                "half_width": num(r["realised_half_width"]),
                "precision_precondition": num(r["precision_precondition"]),
                "precision_met": r["precision_met"],
                "n_blocks": int(r["n_blocks"]), "family": r["family"],
                "evidence_status": r["evidence_status"],
                "source_artifact": r["source_artifact"],
            })
    return out


# ------------------------------------------------------------- verification
def verify(rows, order_rows):
    """Re-check every plotted number against the signed FINAL_REPORT records."""
    problems, checked = [], 0
    signed = {}
    for lane in canonical_lanes().values():
        root, model = lane["lane_id"].split("/", 1)
        p = (EVIDENCE / root / "evidence" / "dci1v7" / model
             / "FINAL_REPORT" / "final_report.json")
        with p.open() as fh:
            fr = json.load(fh)
        for res in fr["results"]:
            signed[(lane["lane_id"], res["member"],
                    res["configuration"] or "cross")] = res

    def same(a, b, what):
        nonlocal checked
        checked += 1
        if a is None or b is None or not math.isclose(a, b, rel_tol=0, abs_tol=1e-12):
            problems.append(f"{what}: figure {a!r} vs signed record {b!r}")

    for r in rows:
        cfg = "outcome_first" if r["b_position"] == "first" else "outcome_second"
        dab_cfg = "outcome_second" if cfg == "outcome_first" else "outcome_first"
        for member, mcfg, keys in (
                ("Delta_R", cfg, ("Delta_R", "Delta_R_sim_lower", "Delta_R_sim_upper")),
                ("D(B<-A)", cfg, ("D_B_from_A", "D_B_from_A_sim_lower",
                                  "D_B_from_A_sim_upper")),
                ("D(A<-B)", dab_cfg, ("D_A_from_B", "D_A_from_B_sim_lower",
                                      "D_A_from_B_sim_upper"))):
            s = signed[(r["lane_id"], member, mcfg)]
            same(r[keys[0]], s["point"], f"{r['lane_id']} {member} {mcfg} point")
            same(r[keys[1]], s["simultaneous_lower"],
                 f"{r['lane_id']} {member} {mcfg} lower")
            same(r[keys[2]], s["simultaneous_upper"],
                 f"{r['lane_id']} {member} {mcfg} upper")
        s_dr = signed[(r["lane_id"], "Delta_R", cfg)]
        s_ba = signed[(r["lane_id"], "D(B<-A)", cfg)]
        s_ab = signed[(r["lane_id"], "D(A<-B)", dab_cfg)]
        same(r["D_B_from_Rbar_DERIVED"], s_ba["point"] - s_dr["point"],
             f"{r['lane_id']} {cfg} D(B<-Rbar) identity")
        same(r["solo_B"] - r["B_given_A"], s_ba["point"],
             f"{r['lane_id']} {cfg} solo_B - B|A == D(B<-A)")
        same(r["solo_A"] - r["A_given_B"], s_ab["point"],
             f"{r['lane_id']} {dab_cfg} solo_A - A|B == D(A<-B)")

    for r in order_rows:
        s = signed[(r["lane_id"], r["member"], "cross")]
        same(r["estimate"], s["point"], f"{r['lane_id']} {r['member']} point")
        same(r["sim_lower"], s["simultaneous_lower"],
             f"{r['lane_id']} {r['member']} lower")
        same(r["sim_upper"], s["simultaneous_upper"],
             f"{r['lane_id']} {r['member']} upper")

    lanes_used = {r["lane_id"] for r in rows} | {r["lane_id"] for r in order_rows}
    canon = {l["lane_id"] for l in canonical_lanes().values()}
    if lanes_used - canon:
        problems.append(f"non-canonical lane reached a figure: {lanes_used - canon}")
    if len(rows) != 8:
        problems.append(f"expected 8 canonical model x position rows, got {len(rows)}")
    return checked, problems


# ------------------------------------------------------------------ helpers
def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)


def save(fig, out, stem):
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{stem}.{ext}")
    plt.close(fig)


def stacked_ys(n, gap=0.72):
    ys, y = [], 0.0
    for i in range(n):
        ys.append(y)
        y += 1.0
        if i % 2 == 1:
            y += gap
    top = max(ys)
    return [top - v for v in ys]


def model_bands(ax, n, ys):
    for i in range(0, n, 2):
        if i % 4 == 0:
            pair = ys[i:i + 2]
            ax.axhspan(min(pair) - 0.5, max(pair) + 0.5, color=BAND, zorder=0, lw=0)


def model_names(ax, rows, ys, size=8.2):
    seen = set()
    for r, y in zip(rows, ys):
        if r["model"] in seen:
            continue
        seen.add(r["model"])
        ax.text(-0.008, y + 0.5, MODEL_LABEL[r["model"]],
                transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=size, fontweight="bold", color=INK, clip_on=False)


# ------------------------------------------------------------------ figure 2
def figure2(rows, out):
    ys = stacked_ys(len(rows))
    XLO, XHI, XDATA = -17.0, 25.0, 15.5
    fig, ax = plt.subplots(figsize=(6.9, 3.45))
    model_bands(ax, len(rows), ys)

    # Arithmetic bounds: a short hatched apron just past the limit, with a solid
    # stop bar at the limit itself. Nothing beyond it was reachable whatever the
    # model did (v7 s13.14 reading 3).
    APRON = 3.2
    for r, y in zip(rows, ys):
        for compressed, limit, sign in (
                (r["positive_direction_compressed"], r["attainable_max"], +1),
                (r["negative_direction_compressed"], r["attainable_min"], -1)):
            if not compressed or limit is None:
                continue
            x0 = limit * PP
            lo_edge = x0 if sign > 0 else x0 - APRON
            ax.add_patch(Rectangle((lo_edge, y - 0.32), APRON, 0.64,
                                   facecolor="none", edgecolor=INK_2, hatch="///",
                                   lw=0.0, alpha=0.5, zorder=2))
            ax.plot([x0, x0], [y - 0.32, y + 0.32], color=INK_2, lw=1.2, zorder=3)

    ax.axvline(0, color=RULE, lw=0.9, zorder=1)
    ax.axvline(10, color=INK, lw=1.2, ls=(0, (4.5, 2.2)), zorder=3)

    for r, y in zip(rows, ys):
        lo, hi = r["Delta_R_sim_lower"] * PP, r["Delta_R_sim_upper"] * PP
        est = r["Delta_R"] * PP
        filled = r["b_position"] == "first"
        ax.plot([lo, hi], [y, y], color=INK, lw=1.7, solid_capstyle="butt", zorder=4)
        for x in (lo, hi):
            ax.plot([x, x], [y - 0.15, y + 0.15], color=INK, lw=1.7, zorder=4)
        ax.plot([est], [y], marker=M_CONTRAST, ms=6.6, zorder=5, ls="none",
                mfc=INK if filled else "white", mec=INK, mew=1.4)
        ax.text(XDATA + 1.2, y, f"{est:+.1f}", va="center", ha="left",
                fontsize=7.3, color=INK)
        ax.text(XDATA + 4.6, y, f"[{lo:+.1f}, {hi:+.1f}]", va="center", ha="left",
                fontsize=7.0, color=INK_2)

    ax.plot([XDATA + 0.6, XDATA + 0.6], [min(ys) - 0.5, max(ys) + 0.5],
            color=GRID, lw=0.7, zorder=1)
    ax.text(XDATA + 1.2, max(ys) + 0.82, "$\\Delta_R$", fontsize=7.2, color=INK_2,
            ha="left", va="center")
    ax.text(XDATA + 4.6, max(ys) + 0.82, "simultaneous 95% CI", fontsize=7.0,
            color=INK_2, ha="left", va="center")
    ax.text(10, max(ys) + 0.82, "+10 pp", fontsize=7.2, color=INK, ha="center",
            va="center", bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none"))

    ax.set_xlim(XLO, XHI)
    ax.set_ylim(min(ys) - 0.7, max(ys) + 1.2)
    ax.set_xlabel(f"{LEFT_ARROW} A less harmful     $\\Delta_R$  "
                  f"(percentage points of B-compliance)     "
                  f"A more harmful {RIGHT_ARROW}")
    ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_bounds(XLO, XDATA)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"B {r['b_position']}   ({r['prompt_order']})" for r in rows])
    model_names(ax, rows, ys)

    handles = [
        Line2D([], [], marker=M_CONTRAST, ls="none", ms=6.6, mfc=INK, mec=INK,
               label="B stated first (prompt B+A)"),
        Line2D([], [], marker=M_CONTRAST, ls="none", ms=6.6, mfc="white", mec=INK,
               mew=1.4, label="B stated second (prompt A+B)"),
        Line2D([], [], color=INK, lw=1.7, label="simultaneous 95% CI (family F1)"),
        Patch(facecolor="white", edgecolor=INK_2, hatch="///", lw=0.0,
              label="limit of what $\\Delta_R$ could reach"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.40, -0.43),
              ncol=2, frameon=False, handlelength=1.9, columnspacing=1.6)
    fig.subplots_adjust(left=0.275, right=0.995, top=0.94, bottom=0.30)
    save(fig, out, "figure2_delta_r_forest")


# ------------------------------------------------------------------ figure 3
def figure3(rows, out):
    ys = stacked_ys(len(rows))
    XLO, XHI, XDATA = -21.0, 68.0, 50.0
    fig, ax = plt.subplots(figsize=(6.9, 3.5))
    model_bands(ax, len(rows), ys)
    ax.axvline(0, color=RULE, lw=0.9, zorder=1)

    for r, y in zip(rows, ys):
        a, rbar = r["D_B_from_A"] * PP, r["D_B_from_Rbar_DERIVED"] * PP
        filled = r["b_position"] == "first"
        ax.plot([rbar, a], [y, y], color="#B9B9B9", lw=3.4,
                solid_capstyle="butt", zorder=3)
        ax.plot([rbar], [y], marker=M_RBAR, ms=7.6, ls="none", zorder=5,
                mfc=C_R if filled else "white", mec=C_R, mew=1.5)
        ax.plot([a], [y], marker=M_B, ms=7.0, ls="none", zorder=6,
                mfc=C_A if filled else "white", mec=C_A, mew=1.5)
        lo = r["D_B_from_A_sim_lower"] * PP
        hi = r["D_B_from_A_sim_upper"] * PP
        ax.plot([lo, hi], [y - 0.32, y - 0.32], color=C_A, lw=1.1, zorder=4,
                solid_capstyle="butt")
        for x in (lo, hi):
            ax.plot([x, x], [y - 0.41, y - 0.23], color=C_A, lw=1.1, zorder=4)
        ax.text(XDATA + 2.4, y, f"{r['Delta_R'] * PP:+.1f}", va="center", ha="left",
                fontsize=7.3, color=INK)

    ax.plot([XDATA + 1.2, XDATA + 1.2], [min(ys) - 0.5, max(ys) + 0.5],
            color=GRID, lw=0.7, zorder=1)
    ax.text(XDATA + 2.4, max(ys) + 0.82, "$\\Delta_R$ (pp)", fontsize=7.2,
            color=INK_2, ha="left", va="center")

    ax.set_xlim(XLO, XHI)
    ax.set_ylim(min(ys) - 0.7, max(ys) + 1.2)
    ax.set_xlabel(f"{LEFT_ARROW} composition improved B     "
                  f"delivery loss for B, solo $-$ composed  (pp)     "
                  f"composition reduced B {RIGHT_ARROW}")
    ax.set_xticks([-20, -10, 0, 10, 20, 30, 40, 50])
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_bounds(XLO, XDATA)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"B {r['b_position']}   ({r['prompt_order']})" for r in rows])
    model_names(ax, rows, ys)

    handles = [
        Line2D([], [], marker=M_B, ls="none", ms=7.0, mfc=C_A, mec=C_A,
               label=f"$D(B\\leftarrow A)$ {EMDASH} companion is A"),
        Line2D([], [], marker=M_RBAR, ls="none", ms=7.6, mfc=C_R, mec=C_R,
               label=f"mean$_j D(B\\leftarrow R_j)$ {EMDASH} matched references"),
        Line2D([], [], color="#B9B9B9", lw=3.4, label="separation $=\\Delta_R$"),
        Line2D([], [], color=C_A, lw=1.1,
               label="simultaneous 95% CI on $D(B\\leftarrow A)$"),
        Line2D([], [], marker=M_B, ls="none", ms=7.0, mfc="white", mec=INK_2,
               mew=1.5, label="open markers: B stated second"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.40, -0.45),
              ncol=2, frameon=False, handlelength=1.9, columnspacing=1.6)
    fig.subplots_adjust(left=0.275, right=0.995, top=0.94, bottom=0.32)
    save(fig, out, "figure3_loss_decomposition")


# ------------------------------------------------------------------ figure 4
def figure4(rows, order_rows, out):
    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(7.1, 3.6),
        gridspec_kw={"width_ratios": [1.30, 1.0], "wspace": 0.22})

    ys = stacked_ys(len(rows))

    # ---- Panel A: both instructions measured inside the SAME prompt
    model_bands(axA, len(rows), ys)
    axA.axvline(0, color=RULE, lw=0.9, zorder=1)
    for r, y in zip(rows, ys):
        for which, colour, marker, off in (("B", C_A, M_B, +0.21),
                                           ("A", C_B, M_A, -0.21)):
            if which == "B":
                est = r["D_B_from_A"] * PP
                lo = r["D_B_from_A_sim_lower"] * PP
                hi = r["D_B_from_A_sim_upper"] * PP
                first = r["b_position"] == "first"
            else:
                est = r["D_A_from_B"] * PP
                lo = r["D_A_from_B_sim_lower"] * PP
                hi = r["D_A_from_B_sim_upper"] * PP
                first = r["A_measured_position"] == "first"
            axA.plot([lo, hi], [y + off, y + off], color=colour, lw=1.4, zorder=4,
                     solid_capstyle="butt")
            for x in (lo, hi):
                axA.plot([x, x], [y + off - 0.10, y + off + 0.10], color=colour,
                         lw=1.4, zorder=4)
            axA.plot([est], [y + off], marker=marker, ms=5.8, ls="none", zorder=5,
                     mfc=colour if first else "white", mec=colour, mew=1.4)

    axA.set_xlim(-22, 52)
    axA.set_ylim(min(ys) - 0.7, max(ys) + 0.95)
    axA.set_xlabel("Delivery loss, solo $-$ composed  (pp)")
    axA.set_xticks([-20, 0, 20, 40])
    axA.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    axA.set_axisbelow(True)
    for s in ("top", "right", "left"):
        axA.spines[s].set_visible(False)
    axA.set_yticks(ys)
    axA.set_yticklabels([f"prompt {r['prompt_order']}" for r in rows])
    model_names(axA, rows, ys)
    axA.set_title("A   Which instruction is measured", loc="left", fontweight="bold",
                  color=INK, pad=5)

    handlesA = [
        Line2D([], [], marker=M_B, ls="none", ms=5.8, mfc=C_A, mec=C_A,
               label="B measured, A the companion"),
        Line2D([], [], marker=M_A, ls="none", ms=5.8, mfc=C_B, mec=C_B,
               label="A measured, B the companion"),
        Line2D([], [], marker=M_B, ls="none", ms=5.8, mfc="white", mec=INK_2,
               mew=1.4, label="open: measured instruction stated second\n"
                              "(composition and position change together)"),
    ]
    axA.legend(handles=handlesA, loc="upper left", bbox_to_anchor=(-0.36, -0.20),
               ncol=1, frameon=False, handlelength=1.5, labelspacing=0.38,
               handletextpad=0.6)

    # ---- Panel B: F11 order contrasts, same row geometry so the panels align
    by_model = {}
    for r in order_rows:
        by_model.setdefault(r["model"], {})[r["member"]] = r
    model_bands(axB, len(rows), ys)
    for x in (-10, 10):
        axB.axvline(x, color=INK_2, lw=0.8, ls=(0, (1.2, 1.8)), zorder=1)
    axB.axvline(0, color=RULE, lw=0.9, zorder=1)

    k = 0
    tick_labels = []
    for model in MODEL_ORDER:
        for member, colour, marker in (("Ord_B", C_A, M_B), ("Ord_A", C_B, M_A)):
            y = ys[k]
            k += 1
            tick_labels.append("$\\mathrm{Ord}_B$" if member == "Ord_B"
                               else "$\\mathrm{Ord}_A$")
            r = by_model.get(model, {}).get(member)
            if r is None:
                axB.text(0, y, "not identified", ha="center", va="center",
                         fontsize=6.6, color=INK_2, style="italic", zorder=5)
                continue
            lo, hi = r["sim_lower"] * PP, r["sim_upper"] * PP
            axB.plot([lo, hi], [y, y], color=colour, lw=1.4, zorder=4,
                     solid_capstyle="butt")
            for x in (lo, hi):
                axB.plot([x, x], [y - 0.13, y + 0.13], color=colour, lw=1.4, zorder=4)
            axB.plot([r["estimate"] * PP], [y], marker=marker, ms=5.8, ls="none",
                     zorder=5, mfc=colour, mec=colour)
            if r["precision_met"] == "False":
                axB.text(hi + 1.6, y, "*", fontsize=9.5, va="center", color=INK_2)

    axB.set_xlim(-47, 20)
    axB.set_ylim(min(ys) - 0.7, max(ys) + 0.95)
    axB.set_xlabel("Stated first $-$ stated second  (pp)")
    axB.set_xticks([-40, -20, 0, 20])
    axB.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    axB.set_axisbelow(True)
    for s in ("top", "right", "left"):
        axB.spines[s].set_visible(False)
    axB.set_yticks(ys)
    axB.set_yticklabels(tick_labels)
    axB.set_title("B   Where the measured instruction appears", loc="left",
                  fontweight="bold", color=INK, pad=5)

    handlesB = [
        Line2D([], [], marker=M_B, ls="none", ms=5.8, mfc=C_A, mec=C_A,
               label="$\\mathrm{Ord}_B$: B measured, companion A"),
        Line2D([], [], marker=M_A, ls="none", ms=5.8, mfc=C_B, mec=C_B,
               label="$\\mathrm{Ord}_A$: A measured, companion B"),
        Line2D([], [], color=INK_2, lw=0.8, ls=(0, (1.2, 1.8)),
               label="$\\pm$10 pp, the smallest effect of interest"),
        Line2D([], [], color="none", label="*  realised precision below precondition"),
    ]
    axB.legend(handles=handlesB, loc="upper left", bbox_to_anchor=(-0.19, -0.20),
               ncol=1, frameon=False, handlelength=1.5, labelspacing=0.38,
               handletextpad=0.6)

    fig.subplots_adjust(left=0.175, right=0.995, top=0.90, bottom=0.34)
    save(fig, out, "figure4_direction_position")


# ------------------------------------------------------------------- table 1
def table1(rows, out):
    def pp(x):
        return f"${x * PP:+.1f}$"

    lines = [
        r"% Generated by dci1/tools/v7_paper_figures.py -- do not edit by hand.",
        r"% Requires \usepackage{booktabs}.",
        r"\begin{table}[t]",
        r"  \centering",
        r"  \small",
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{llrrrc}",
        r"    \toprule",
        r"    & B stated & $D(B\!\leftarrow\!A)$ & $\overline{D(B\!\leftarrow\!R)}$"
        r" & $\Delta_R$ & Simultaneous 95\% CI \\",
        r"    Model & (prompt) & (pp) & (pp) & (pp) & for $\Delta_R$ (pp) \\",
        r"    \midrule",
    ]
    for i, r in enumerate(rows):
        model = MODEL_LABEL[r["model"]] if i % 2 == 0 else ""
        pos = f"{r['b_position']} ({r['prompt_order']})"
        ci = (f"$[{r['Delta_R_sim_lower'] * PP:+.1f},\\;"
              f"{r['Delta_R_sim_upper'] * PP:+.1f}]$")
        dag = r"\,$^{\dagger}$" if (r["positive_direction_compressed"]
                                  or r["negative_direction_compressed"]) else ""
        lines.append(
            f"    {model} & {pos} & {pp(r['D_B_from_A'])} & "
            f"{pp(r['D_B_from_Rbar_DERIVED'])} & {pp(r['Delta_R'])}{dag} & {ci} \\\\")
        if i % 2 == 1 and i != len(rows) - 1:
            lines.append(r"    \addlinespace[2pt]")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \caption{Matched-reference results for the four models in both prompt "
        r"orders, in percentage points of B-compliance over 384 topic blocks. "
        r"$D(B\!\leftarrow\!A)$ is B's solo compliance minus its compliance beside "
        r"A, and $\overline{D(B\!\leftarrow\!R)}$ the unweighted mean of the same "
        r"loss beside the three matched same-form references, so "
        r"$\Delta_R=D(B\!\leftarrow\!A)-\overline{D(B\!\leftarrow\!R)}$ and a "
        r"positive value means A is associated with lower B-compliance than its "
        r"matched references. Intervals are simultaneous 95\% block-bootstrap "
        r"intervals for multiplicity family F1; $\overline{D(B\!\leftarrow\!R)}$ is "
        r"a derived mean and carries no registered interval. $^{\dagger}$~marks "
        r"configurations where an arm's compliance level arithmetically restricts "
        r"the range $\Delta_R$ can take. Development-rehearsal evidence, not "
        r"confirmatory results.}",
        r"  \label{tab:primary-results}",
        r"\end{table}",
        "",
    ]
    (out / "table1_primary_results.tex").write_text("\n".join(lines))


def accessibility_renders(out, paper_width_in=7.0, dpi=150):
    """Grayscale and final-paper-width renders, for the accessibility pass.

    Colour is redundant with shape and fill everywhere, so the grayscale render
    must stay readable; the paper-width render is the one to eyeball for label
    collisions at the size the figure is actually printed.
    """
    try:
        from PIL import Image
    except ImportError:                                    # pragma: no cover
        print("  (Pillow absent: skipped the grayscale/paper-size renders)")
        return
    for stem in ("figure2_delta_r_forest", "figure3_loss_decomposition",
                 "figure4_direction_position"):
        src = out / f"{stem}.png"
        im = Image.open(src)
        im.convert("L").save(out / f"_check_gray_{stem}.png")
        w = int(paper_width_in * dpi)
        im.resize((w, int(im.height * w / im.width)),
                  Image.LANCZOS).save(out / f"_check_papersize_{stem}.png")


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    rows = build_rows()
    order_rows = build_order_rows()

    checked, problems = verify(rows, order_rows)
    if problems:
        for p in problems:
            print("VERIFY FAIL:", p)
        raise SystemExit(f"{len(problems)} verification failure(s)")
    print(f"verified {checked} values against the signed FINAL_REPORT records: "
          f"all agree")

    write_csv(out / "figure2_delta_r_forest_data.csv", rows, [
        "model", "model_label", "lane_id", "b_position", "prompt_order",
        "n_star", "m_star", "n_blocks", "Delta_R", "Delta_R_sim_lower",
        "Delta_R_sim_upper", "Delta_R_marg_lower", "Delta_R_marg_upper",
        "Delta_R_half_width", "Delta_R_precision_met", "Delta_R_direction",
        "attainable_min", "attainable_max", "positive_direction_compressed",
        "negative_direction_compressed", "compressed_by", "evidence_status",
        "source_artifact"])
    write_csv(out / "figure3_loss_decomposition_data.csv", rows, [
        "model", "model_label", "lane_id", "b_position", "prompt_order", "n_blocks",
        "solo_B", "B_given_A", "B_given_A_cell", "D_B_from_A",
        "D_B_from_A_sim_lower", "D_B_from_A_sim_upper", "D_B_from_Rbar_DERIVED",
        "Delta_R", "Delta_R_sim_lower", "Delta_R_sim_upper", "evidence_status",
        "source_artifact"])
    write_csv(out / "figure4_direction_position_data.csv", rows, [
        "model", "model_label", "lane_id", "prompt_order", "b_position",
        "A_measured_position", "n_blocks",
        "solo_B", "B_given_A", "D_B_from_A", "D_B_from_A_sim_lower",
        "D_B_from_A_sim_upper", "D_B_from_A_position_confounded",
        "solo_A", "A_given_B", "D_A_from_B", "D_A_from_B_sim_lower",
        "D_A_from_B_sim_upper", "D_A_from_B_position_confounded",
        "evidence_status", "source_artifact"])
    write_csv(out / "figure4_order_contrasts_data.csv", order_rows)
    write_csv(out / "table1_primary_results_data.csv", rows, [
        "model", "model_label", "b_position", "prompt_order", "D_B_from_A",
        "D_B_from_Rbar_DERIVED", "Delta_R", "Delta_R_sim_lower",
        "Delta_R_sim_upper", "positive_direction_compressed",
        "negative_direction_compressed", "n_blocks", "lane_id", "evidence_status"])

    figure2(rows, out)
    figure3(rows, out)
    figure4(rows, order_rows, out)
    table1(rows, out)
    accessibility_renders(out)
    print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
