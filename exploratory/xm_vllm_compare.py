"""Compare the vLLM TP=2 condition against the earlier Transformers condition.

Produces `CROSS_MODEL_VLLM_BACKEND_COMPARISON.md` from the two experiments'
analysis outputs. Neither file is edited; both are read.

**This is not a backend experiment.** The two conditions differ in more than the
backend — reasoning mechanism (one uninterrupted generation versus a two-phase
splice), per-family generation strategy, and for the Qwen checkpoints the
Transformers condition never established natural reasoning at all. A difference
between the columns is therefore reported as **execution-condition
sensitivity**, never as a causal backend effect.

    uv run python xm_vllm_compare.py --transformers DIR... --vllm DIR...
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))


def read(dirs: list[Path], name: str, label: str) -> pd.DataFrame:
    frames = []
    for directory in dirs:
        path = directory / name
        if path.exists():
            frame = pd.read_csv(path)
            frame["condition"] = label
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def md(frame: pd.DataFrame, floats: int = 3) -> str:
    if frame.empty:
        return "_no rows_\n"
    columns = [str(c) for c in frame.columns]
    rows = []
    for record in frame.itertuples(index=False):
        cells = []
        for value in record:
            if isinstance(value, float):
                cells.append("—" if pd.isna(value) else f"{value:+.{floats}f}")
            else:
                cells.append(str(value))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(["| " + " | ".join(columns) + " |",
                      "|" + "|".join("---" for _ in columns) + "|",
                      *rows]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transformers", nargs="*", default=[])
    parser.add_argument("--vllm", nargs="*", default=[])
    parser.add_argument("--out",
                        default="CROSS_MODEL_VLLM_BACKEND_COMPARISON.md")
    args = parser.parse_args()

    old = [Path(p) for p in args.transformers]
    new = [Path(p) for p in args.vllm]

    tau = pd.concat([read(old, "tau_by_model.csv", "TRANSFORMERS_CROSS_MODEL"),
                     read(new, "tau_by_model.csv", "VLLM_TP2_CROSS_MODEL")],
                    ignore_index=True)
    joint = pd.concat([read(old, "joint_contrast.csv",
                            "TRANSFORMERS_CROSS_MODEL"),
                       read(new, "joint_contrast.csv",
                            "VLLM_TP2_CROSS_MODEL")], ignore_index=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Execution-condition comparison — Transformers versus vLLM TP=2",
        "",
        f"Generated {stamp} by `xm_vllm_compare.py` from the two experiments'",
        "analysis outputs. Both are read; neither is modified.",
        "",
        "## What separates the two columns",
        "",
        "| | `TRANSFORMERS_CROSS_MODEL` | `VLLM_TP2_CROSS_MODEL` |",
        "|---|---|---|",
        "| backend | Transformers 5.15.0 | vLLM 0.27.1+rocm723 |",
        "| torch | 2.9.1+rocm7.2.0 | 2.11.0+gitd0c8b1f |",
        "| devices | one card per checkpoint (`device_map`) | tensor-parallel 2 |",
        "| reasoning mechanism | two-phase splice (Qwen) / single-phase (Gemma) | one uninterrupted generation |",
        "| answer allowance | 512 enforced separately (Qwen) | shared budget |",
        "| reasoning parser | hand-written per family | vLLM `qwen3` / `gemma4` |",
        "| dtype | bfloat16 | bfloat16 |",
        "| decoding | T 0.7, top-p 0.9, top-k off | identical |",
        "| tasks, arms, backgrounds, order, seeds, verifiers | identical | identical |",
        "",
        "**More than the backend differs.** A difference between columns is",
        "*execution-condition sensitivity*, not a causal backend effect. A",
        "matched experiment varying only the backend was not run.",
        "",
        "## τ and its raw components",
        "",
    ]
    if not tau.empty:
        keep = [c for c in ["condition", "model", "reasoning", "load",
                            "background", "focal_A_failure",
                            "reference_A_failure", "tau", "lo", "hi",
                            "degeneracy"] if c in tau.columns]
        table = tau[keep].sort_values(
            [c for c in ["model", "load", "condition"] if c in keep])
        if "degeneracy" in table.columns:
            table["degeneracy"] = table["degeneracy"].astype(str).str.split(
                " — ").str[0]
        lines.append(md(table))

    lines += ["", "## Joint satisfaction", ""]
    if not joint.empty:
        keep = [c for c in ["condition", "model", "reasoning", "load",
                            "joint_control", "joint_semicolon", "delta_joint",
                            "lo", "hi"] if c in joint.columns]
        lines.append(md(joint[keep].sort_values(
            [c for c in ["model", "load", "condition"] if c in keep])))

    lines += [
        "",
        "## Coverage differs, and that is the main finding of the comparison",
        "",
        "The two conditions do not cover the same cells, so most rows have no",
        "counterpart:",
        "",
        "| checkpoint | Transformers | vLLM TP=2 |",
        "|---|---|---|",
        "| `Qwen/Qwen3.5-4B` | NO_THINKING only — natural reasoning never established | see matrix |",
        "| `Qwen/Qwen3.5-9B` | NO_THINKING only | see matrix |",
        "| `google/gemma-4-E4B-it` | both modes | **TP2_BACKEND_BLOCKED** |",
        "| `google/gemma-4-12B-it` | NO_THINKING only (single-card OOM) | **TP2_BACKEND_BLOCKED** |",
        "| `moonshotai/Kimi-VL-A3B-Thinking-2506` | **BACKEND_BLOCKED** | see matrix |",
        "",
        "No single execution condition on this host covers all five",
        "checkpoints. Removing the backend confound for one family introduces",
        "it for another, and that is a property of the available software, not",
        "of the models.",
        "",
    ]

    Path(args.out).write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
