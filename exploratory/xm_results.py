"""Render CROSS_MODEL_DCI_RESULTS.md from the analysis outputs.

The markdown is a VIEW of `analysis/*.csv`, never an input to anything. Every
number here was produced by `xm_analysis.py` from the raw rows and checked by
`xm_verify_independently.py` with separate arithmetic.

    uv run python xm_results.py runs/xm_main_*/analysis --out CROSS_MODEL_DCI_RESULTS.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract


def read_all(dirs: list[Path], name: str) -> pd.DataFrame:
    frames = [pd.read_csv(d / name) for d in dirs if (d / name).exists()]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def md(frame: pd.DataFrame, floats: int = 3, index: bool = False) -> str:
    """Markdown for a frame, without depending on `tabulate`."""
    if frame.empty:
        return "_no rows_\n"
    frame = frame.reset_index() if index else frame
    columns = [str(c) for c in frame.columns]
    rows = []
    for record in frame.itertuples(index=False):
        cells = []
        for value in record:
            if isinstance(value, float):
                cells.append("—" if pd.isna(value) else f"{value:.{floats}f}")
            else:
                cells.append(str(value))
        rows.append("| " + " | ".join(cells) + " |")
    header = "| " + " | ".join(columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    return "\n".join([header, rule, *rows]) + "\n"


def table(frame: pd.DataFrame, columns: list[str], floats: int = 3) -> str:
    if frame.empty:
        return "_no rows_\n"
    frame = frame[[c for c in columns if c in frame.columns]].copy()
    for column in frame.columns:
        if pd.api.types.is_float_dtype(frame[column]):
            frame[column] = frame[column].map(
                lambda v: "—" if pd.isna(v) else f"{v:+.{floats}f}"
                if column not in ("closure_rate",) else f"{v:.{floats}f}")
    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |"
            for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *body]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dirs", nargs="+")
    parser.add_argument("--out", default="CROSS_MODEL_DCI_RESULTS.md")
    args = parser.parse_args()
    dirs = [Path(d) for d in args.dirs]

    tau = read_all(dirs, "tau_by_model.csv")
    delta = read_all(dirs, "delta_semicolon.csv")
    four = read_all(dirs, "four_state.csv")
    compliance = read_all(dirs, "compliance.csv")
    use = read_all(dirs, "reasoning_use.csv")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    models = sorted(tau["model"].unique()) if not tau.empty else []

    lines = [
        "# Cross-model DCI transport — results",
        "",
        f"Generated {stamp} by `xm_results.py` from `analysis/*.csv`, which",
        "`xm_analysis.py` produced from the raw generation rows and",
        "`xm_verify_independently.py` reproduced with separate arithmetic.",
        "This document is a view; it is never an input.",
        "",
        "**Status: exploratory.** No claim here is confirmatory, and the",
        "execution condition differs from the canonical Qwen3-4B result in a way",
        "that matters — see the backend note below.",
        "",
        "## The estimand",
        "",
        "For model *m*, background *c* and reasoning condition *r*:",
        "",
        "> τ(m,c,r) = P(F_A = 1 | B, m, c, r) − P(F_A = 1 | R, m, c, r)",
        "",
        "> Δ_semicolon(m,r) = τ(m, semicolon, r) − τ(m, control, r)",
        "",
        "where A is *\"Write exactly 4 sentences.\"*, B is *\"Make each sentence",
        "strictly longer than the preceding sentence when measured by word",
        "count.\"* and R is the matched reference *\"Begin every sentence with a",
        "word whose first letter is S.\"* F_A = 1 means A failed.",
        "",
        "Both raw components are printed beside every difference. A reader shown",
        "only a difference-of-differences cannot tell amplification from two",
        "floors.",
        "",
        "## Execution condition, and what it is NOT comparable with",
        "",
        "Every checkpoint here ran on **Transformers**, because vLLM is not",
        "installed on this machine and no ROCm build of it is present. The",
        "canonical +0.400 semicolon result was produced by vLLM 0.15.1+rocm720 on",
        f"`{contract.CANONICAL_MODEL}` @ `{contract.CANONICAL_REVISION[:12]}`, a",
        "checkpoint that is not in this study. The five-way comparison below is",
        "internally consistent; a comparison against that number would be",
        "backend-confounded and is not made.",
        "",
        "## 1. τ(B→A) by model, background and reasoning condition",
        "",
    ]
    lines.append(table(tau, ["model", "reasoning", "background",
                             "focal_A_failure", "reference_A_failure",
                             "tau", "lo", "hi", "n_tasks", "n_rows"]))

    degenerate = (tau[tau["degeneracy"] != "estimable"]
                  if "degeneracy" in tau.columns else pd.DataFrame())
    if len(degenerate):
        lines += [
            "",
            "> **τ is not estimable in some cells above.** Where the target",
            "> instruction never fails in EITHER arm, τ is zero by construction",
            "> and cannot detect interference — \"no extra failures\" and \"no",
            "> failures to add to\" are different findings. The affected cells:",
            "",
        ]
        for row in degenerate.itertuples():
            lines.append(f"> * `{row.model}` / {row.reasoning} / "
                         f"{row.background} — {row.degeneracy.split(' — ')[0]}")
        lines.append("")

    lines += ["", "## 2. Semicolon-minus-control contrast", ""]
    lines.append(table(delta, ["model", "reasoning", "tau_control",
                               "tau_semicolon", "delta_semicolon", "lo", "hi",
                               "n_tasks"]))

    lines += [
        "",
        "## 3. Four-state outcomes in the focal arm",
        "",
        "Identical target-failure rates can arise through different behavioural",
        "strategies, so the arbitration states are reported separately. Where the",
        "focal instruction B is near floor for a checkpoint, this table mostly",
        "distinguishes *neither* from *target only* and does **not** identify",
        "arbitration between two live constraints — see the execution matrix's",
        "Stage D column before reading it as arbitration.",
        "",
    ]
    if not four.empty:
        lines.append(md(four, floats=3, index=True))

    lines += [
        "",
        "## 4. In-context compliance with each instruction",
        "",
        "The same question the Stage D gate asks in isolation, asked of the",
        "scientific rows.",
        "",
    ]
    lines.append(table(compliance, ["model", "reasoning", "A_in_focal_arm",
                                    "A_in_reference_arm", "B_compliance",
                                    "R_compliance", "background_compliance"]))

    lines += [
        "",
        "## 5. Natural reasoning — descriptive, per model only",
        "",
        "**Reasoning tokens are not a universal unit of compute.** A Qwen token, a",
        "Gemma token and a Kimi token index different tokenizers, different",
        "training and different reasoning formats. These distributions are",
        "reported per checkpoint and are never summed, averaged or ranked across",
        "families. Realised length is post-treatment and no mediation is claimed.",
        "",
    ]
    if not use.empty:
        lines.append(md(use, floats=1))

    lines += [
        "",
        "## What this does not establish",
        "",
        "* Nothing about model families in general — these are single",
        "  checkpoints, one instruction pair, 20 tasks, 2 replicates.",
        "* No parameter-count claim. Qwen3.5-4B and 9B differ in training and",
        "  post-training as well as scale, and E4B and 12B are different",
        "  architectures, not one architecture at two sizes.",
        "* No claim that longer realised reasoning causes anything. It is chosen",
        "  by the model, not assigned.",
        "* No claim that semicolons universally amplify instruction conflict.",
        "* Where a checkpoint's focal instruction sits near floor, no claim that",
        "  it \"has less DCI\" — the contrast cannot be estimated there.",
        "",
        f"Models covered: {', '.join(models) if models else 'none'}.",
        "",
    ]

    Path(args.out).write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
