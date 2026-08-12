"""Score and report the ACTUAL cross-model DCI dataset, mixed backends and all.

This is the reporting pass for a run that was allowed to differ in execution
where it had to. It replaces nothing in `xm_analysis.py`; that script guards a
single-backend, never-binding-ceiling condition and refuses a dataset that
violates it, which is right for what it was written for and wrong here. This one
is built for the dataset that actually exists:

* **Backends differ per checkpoint and the difference is carried on every row.**
  Model, revision, backend, version, dtype, device layout, TP size, thinking
  mechanism, reasoning parser and generation ceiling all travel with the row and
  are reprinted in the manifest, so no cross-model comparison can be made
  without the reader seeing what else changed.

* **A row that produced no final answer is its own state.** It is counted, it is
  reported, and it never enters a pass/fail rate. Folding NO_FINAL_WITHIN_BUDGET
  into "A failed" would convert an execution limit into a behavioural result —
  the single most likely way this dataset could be made to lie.

* **Degeneracy is labelled, not suppressed.** Where the target never fails in
  either arm, tau is 0 by construction. That is printed as 0 with the label
  TARGET_CEILING beside it, both raw components shown, and the result is not
  withheld.

    uv run python xm_actual_results.py runs/DIR [runs/DIR ...]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, schema, seeds
from dci_exploratory import extensions, harvest, plotstyle

extensions.register()
STATE = harvest.load()

SEMICOLON = contract.SEMICOLON_BACKGROUND
CONTROL = contract.CONTROL_BACKGROUND
FOCAL, REFERENCE = contract.FOCAL, contract.REFERENCE
LABEL = {CONTROL: "control (+1 bracket pair)", SEMICOLON: "+1 semicolon"}
CEILING, FLOOR = 0.02, 0.98


# ------------------------------------------------------------------- loading
def load(dirs: list[Path]) -> pd.DataFrame:
    rows = []
    for directory in dirs:
        path = (directory if directory.is_file()
                else directory / "generations.jsonl")
        if not path.exists():
            print(f"  !! {path} missing — skipped")
            continue
        found = [json.loads(line) for line in path.open()]
        for record in found:
            record.setdefault("source_dir", str(directory))
            # Rows written before the bounded condition existed carry neither
            # field. Deriving them here keeps one status vocabulary across every
            # backend instead of two shapes the report has to special-case.
            record.setdefault("not_generated", False)
            record.setdefault("generation_ceiling",
                              record.get("engineering_ceiling"))
            record.setdefault("final_answer_status",
                              schema.final_answer_status(record))
        print(f"  {len(found):4d} rows  {path}")
        rows.extend(found)
    if not rows:
        raise SystemExit("no rows loaded")
    return pd.DataFrame(rows)


def score(frame: pd.DataFrame) -> pd.DataFrame:
    """Verify the FINAL ANSWER only, and only where there is one.

    A row without a final answer scores NaN on every constraint rather than 0.
    NaN propagates out of every mean below, so such a row cannot silently become
    a failure; it is counted in its own column instead.
    """
    frame = frame.copy()
    scoreable = frame["final_answer_status"] == schema.FINAL_ANSWER

    def passes(text, constraint, ok):
        if not ok or not isinstance(text, str) or not text.strip():
            return float("nan")
        return float(STATE.verify(text, constraint).binary_pass)

    target = contract.TARGET
    frame["a_pass"] = [passes(t, target, ok) for t, ok
                       in zip(frame["final_answer"], scoreable)]
    frame["arm_pass"] = [passes(t, a, ok) for t, a, ok
                         in zip(frame["final_answer"], frame["arm"], scoreable)]
    frame["c_pass"] = [passes(t, v, ok) for t, v, ok in
                       zip(frame["final_answer"], frame["background"],
                           scoreable)]
    frame["a_failure"] = 1.0 - frame["a_pass"]
    frame["outcome"] = np.select(
        [~scoreable,
         (frame["a_pass"] == 1) & (frame["arm_pass"] == 1),
         (frame["a_pass"] == 1) & (frame["arm_pass"] == 0),
         (frame["a_pass"] == 0) & (frame["arm_pass"] == 1)],
        ["no final answer", "both satisfied", "target only", "focal only"],
        default="neither")
    frame["scoreable"] = scoreable
    return frame


# ---------------------------------------------------------------- estimation
def tau_per_task(cell: pd.DataFrame) -> pd.Series:
    """Paired over tasks — the task is the resampling cluster, as before."""
    rates = cell.groupby(["arm", "task_id"])["a_failure"].mean()
    levels = rates.index.get_level_values(0)
    if FOCAL not in levels or REFERENCE not in levels:
        return pd.Series(dtype=float)
    return (rates.loc[FOCAL] - rates.loc[REFERENCE]).dropna()


def degeneracy(focal_failure: float, reference_failure: float) -> str:
    if np.isnan(focal_failure) or np.isnan(reference_failure):
        return "not estimated — no scoreable rows"
    if focal_failure <= CEILING and reference_failure <= CEILING:
        return "TARGET_CEILING"
    if focal_failure >= FLOOR and reference_failure >= FLOOR:
        return "TARGET_FLOOR"
    return "estimable"


def per_cell(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per model x load x background: counts first, then the estimate."""
    out = []
    for (model, load, background), cell in frame.groupby(
            ["model_id", "load", "background"], sort=True):
        focal = cell[cell["arm"] == FOCAL]
        reference = cell[cell["arm"] == REFERENCE]
        per_task = tau_per_task(cell)
        stats = (plotstyle.summarise(per_task, f"{model}|{load}|{background}")
                 if len(per_task) else
                 {"estimate": float("nan"), "lo": float("nan"),
                  "hi": float("nan"), "n_tasks": 0})
        focal_rate = focal["a_failure"].mean()
        reference_rate = reference["a_failure"].mean()
        out.append({
            "model": model.split("/")[-1], "model_id": model,
            "backend": cell["backend"].iloc[0], "load": load,
            "background": LABEL[background], "variant": background,
            "requested": len(cell),
            "final_answers": int(cell["scoreable"].sum()),
            "no_final": int((cell["final_answer_status"]
                             == schema.NO_FINAL_WITHIN_BUDGET).sum()),
            "technical_failures": int((cell["final_answer_status"]
                                       == schema.TECHNICAL_FAILURE).sum()),
            "not_generated": int((cell["final_answer_status"]
                                  == schema.NOT_GENERATED).sum()),
            "A_fail_focal": focal_rate, "A_fail_reference": reference_rate,
            "tau": stats["estimate"], "lo": stats["lo"], "hi": stats["hi"],
            "n_tasks": stats["n_tasks"],
            "joint_focal": (focal["outcome"] == "both satisfied").sum()
            / max(int(focal["scoreable"].sum()), 1),
            "degeneracy": degeneracy(focal_rate, reference_rate)})
    return pd.DataFrame(out)


def headline(cells: pd.DataFrame) -> pd.DataFrame:
    """The table the results document opens with: one line per model and load."""
    out = []
    for (model, backend, load), part in cells.groupby(
            ["model", "backend", "load"], sort=True):
        weight = part["final_answers"]
        out.append({
            "Model": model, "Backend": backend, "k": load,
            "Requested": int(part["requested"].sum()),
            "Final answers": int(part["final_answers"].sum()),
            "No-final": int(part["no_final"].sum()),
            # Pooled over backgrounds and weighted by the rows that actually
            # produced an answer, so a background with few answers cannot
            # dominate the headline number.
            "A-fail focal": float(np.average(
                part["A_fail_focal"].fillna(0), weights=weight)
                if weight.sum() else float("nan")),
            "A-fail ref": float(np.average(
                part["A_fail_reference"].fillna(0), weights=weight)
                if weight.sum() else float("nan")),
            "tau": float(np.average(part["tau"].fillna(0), weights=weight)
                         if weight.sum() else float("nan"))})
    return pd.DataFrame(out)


def missingness(frame: pd.DataFrame) -> pd.DataFrame:
    """Who is missing from the scored subsample, per arm and background.

    Every rate in this report is conditional on the row having produced a final
    answer. That is unavoidable — there is nothing to score otherwise — but it
    is only harmless if the missing rows are missing at the same rate on both
    sides of a contrast. When they are not, the contrast is partly a comparison
    between two differently-selected subsamples, and no bootstrap interval
    accounts for that. So the rates are tabulated and the worst gap is stated.
    """
    out = []
    for (model, load, background, arm), cell in frame.groupby(
            ["model_id", "load", "background", "arm"]):
        out.append({
            "model": model.split("/")[-1], "load": load,
            "background": LABEL[background],
            "arm": "focal B" if arm == FOCAL else "reference C_L3",
            "requested": len(cell),
            "answered": int(cell["scoreable"].sum()),
            "answer_rate": float(cell["scoreable"].mean())})
    return pd.DataFrame(out)


def missingness_warnings(gaps: pd.DataFrame) -> list[str]:
    """One line per model x load whose answer rate moves across the contrast."""
    lines = []
    for (model, load), part in gaps.groupby(["model", "load"]):
        spread = part["answer_rate"].max() - part["answer_rate"].min()
        if part["answer_rate"].min() >= 0.999:
            continue
        worst = part.loc[part["answer_rate"].idxmin()]
        best = part.loc[part["answer_rate"].idxmax()]
        severity = ("**differential**" if spread >= 0.10
                    else "roughly balanced")
        lines.append(
            f"* **{model}** (k={load}) — answer rate ranges "
            f"{worst['answer_rate']:.0%} ({worst['background']}, "
            f"{worst['arm']}) to {best['answer_rate']:.0%} "
            f"({best['background']}, {best['arm']}); spread "
            f"{spread:.0%}, {severity}.")
    return lines


def background_contrast(frame: pd.DataFrame) -> pd.DataFrame:
    """Delta = tau(semicolon) - tau(control), paired within task."""
    out = []
    for (model, load), cell in frame.groupby(["model_id", "load"]):
        taus = {v: tau_per_task(sub) for v, sub in cell.groupby("background")}
        if (SEMICOLON not in taus or CONTROL not in taus
                or not len(taus[SEMICOLON]) or not len(taus[CONTROL])):
            continue
        delta = (taus[SEMICOLON] - taus[CONTROL]).dropna()
        if not len(delta):
            continue
        stats = plotstyle.summarise(delta, f"{model}|{load}|delta")
        out.append({
            "model": model.split("/")[-1], "load": load,
            "tau_control": taus[CONTROL].mean(),
            "tau_semicolon": taus[SEMICOLON].mean(),
            "delta_semicolon": stats["estimate"],
            "lo": stats["lo"], "hi": stats["hi"], "n_tasks": stats["n_tasks"]})
    return pd.DataFrame(out)


def joint_contrast(frame: pd.DataFrame) -> pd.DataFrame:
    """Secondary: joint satisfaction in the focal arm, where A and B compete."""
    out = []
    focal_only = frame[(frame["arm"] == FOCAL) & frame["scoreable"]]
    for (model, load), cell in focal_only.groupby(["model_id", "load"]):
        cell = cell.copy()
        cell["both"] = (cell["outcome"] == "both satisfied").astype(float)
        rates = cell.groupby(["background", "task_id"])["both"].mean()
        levels = rates.index.get_level_values(0)
        if SEMICOLON not in levels or CONTROL not in levels:
            continue
        delta = (rates.loc[SEMICOLON] - rates.loc[CONTROL]).dropna()
        if not len(delta):
            continue
        stats = plotstyle.summarise(delta, f"{model}|{load}|joint")
        out.append({
            "model": model.split("/")[-1], "load": load,
            "joint_control": rates.loc[CONTROL].mean(),
            "joint_semicolon": rates.loc[SEMICOLON].mean(),
            "delta_joint": stats["estimate"], "lo": stats["lo"],
            "hi": stats["hi"], "n_tasks": stats["n_tasks"]})
    return pd.DataFrame(out)


def four_state(frame: pd.DataFrame) -> pd.DataFrame:
    """Focal-arm outcomes. `no final answer` is a COLUMN, not a silent drop."""
    focal = frame[frame["arm"] == FOCAL]
    table = (pd.crosstab(
        [focal["model_id"].str.split("/").str[-1], focal["load"],
         focal["background"].map(LABEL)],
        focal["outcome"], normalize="index")
        .reindex(columns=["both satisfied", "target only", "focal only",
                          "neither", "no final answer"], fill_value=0.0))
    table.index.names = ["model", "k", "background"]
    return table


def compliance(frame: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (model, load), cell in frame.groupby(["model_id", "load"]):
        focal = cell[cell["arm"] == FOCAL]
        reference = cell[cell["arm"] == REFERENCE]
        out.append({
            "model": model.split("/")[-1], "load": load,
            "A_in_focal_arm": focal["a_pass"].mean(),
            "A_in_reference_arm": reference["a_pass"].mean(),
            "B_compliance": focal["arm_pass"].mean(),
            "R_compliance": reference["arm_pass"].mean(),
            "background_compliance": cell["c_pass"].mean()})
    return pd.DataFrame(out)


def termination(frame: pd.DataFrame) -> pd.DataFrame:
    """Reasoning length and termination — per model, never pooled or ranked.

    Reasoning tokens are not a common unit: a Qwen token, a Gemma token and a
    Kimi token index different tokenizers. These rows sit side by side for
    reading, and are never summed or compared numerically across families.
    """
    out = []
    for (model, load), cell in frame.groupby(["model_id", "load"]):
        tokens = cell["reasoning_tokens"]
        out.append({
            "model": model.split("/")[-1], "load": load,
            "backend": cell["backend"].iloc[0],
            "ceiling": int(cell["generation_ceiling"].iloc[0] or 0),
            "n": len(cell),
            "median": tokens.median(), "p90": tokens.quantile(.90),
            "max": int(tokens.max()),
            "closed": float(cell["natural_reasoning_closed"].mean()),
            "hit_ceiling": int(cell["reasoning_cap_hit"].sum()),
            "answered": float(cell["scoreable"].mean()),
            "answer_tokens": cell["final_answer_tokens"].mean()})
    return pd.DataFrame(out)


def termination_by_cell(frame: pd.DataFrame) -> pd.DataFrame:
    """Reasoning length and ceiling contact per arm and background.

    The companion to the missingness table: where answer rates differ across a
    contrast, this is where to look for why. Still per model — token counts are
    not comparable across families.
    """
    out = []
    for (model, load, background, arm), cell in frame.groupby(
            ["model_id", "load", "background", "arm"]):
        tokens = cell["reasoning_tokens"]
        out.append({
            "model": model.split("/")[-1], "load": load,
            "background": LABEL[background],
            "arm": "focal B" if arm == FOCAL else "reference C_L3",
            "median_reasoning": tokens.median(),
            "p90": tokens.quantile(.90), "max": int(tokens.max()),
            "hit_ceiling": int(cell["reasoning_cap_hit"].sum()),
            "of": len(cell)})
    return pd.DataFrame(out)


def manifest(frame: pd.DataFrame) -> list[dict]:
    """Everything §8 requires, one entry per checkpoint and load."""
    out = []
    for (model, load), cell in frame.groupby(["model_id", "load"]):
        first = cell.iloc[0]
        out.append({
            "model_id": model,
            "model_revision": first["model_revision"],
            "model_family": first["model_family"],
            "backend": first["backend"],
            "backend_version": first["backend_version"],
            "dtype": first["dtype"],
            "quantization": first["quantization"],
            "gpu_layout": first["device_configuration"],
            "tensor_parallel_size":
                2 if "tensor_parallel_size=2" in str(
                    first["device_configuration"]) else None,
            "thinking_implementation": first["reasoning_control"],
            "reasoning_mode": first["reasoning_mode"],
            "reasoning_parser": (
                str(first["reasoning_control"]).split("parser=")[-1]
                if "parser=" in str(first["reasoning_control"])
                else "adapter delimiters"),
            "generation_ceiling": int(first["generation_ceiling"] or 0),
            "engineering_ceiling": int(first["engineering_ceiling"] or 0),
            "max_final_answer_tokens": int(first["max_final_answer_tokens"]),
            "temperature": float(first["temperature"]),
            "top_p": float(first["top_p"]), "top_k": int(first["top_k"]),
            "load": int(load), "rows": len(cell),
            "source_dirs": sorted(set(cell["source_dir"])),
            "final_answers": int(cell["scoreable"].sum()),
            "no_final_within_budget": int((cell["final_answer_status"]
                                           == schema.NO_FINAL_WITHIN_BUDGET
                                           ).sum()),
            "technical_failures": int((cell["final_answer_status"]
                                       == schema.TECHNICAL_FAILURE).sum()),
            "not_generated": int((cell["final_answer_status"]
                                  == schema.NOT_GENERATED).sum()),
            "replicate_duplication": seeds.replicate_duplication(
                cell.to_dict("records")),
        })
    return out


# ------------------------------------------------------------------ document
def table(frame: pd.DataFrame, floats: str = "{:.3f}") -> str:
    if not len(frame):
        return "_(no rows)_\n"
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    lines = [header, rule]
    for row in frame.itertuples(index=False):
        cells = []
        for value in row:
            if isinstance(value, float):
                cells.append("—" if np.isnan(value) else floats.format(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def indexed_table(frame: pd.DataFrame) -> str:
    return table(frame.reset_index())


def document(frame: pd.DataFrame, cells: pd.DataFrame, missing: list[dict],
             stamp: str) -> str:
    head = headline(cells)
    parts = [
        "# Cross-model DCI — the actual dataset",
        "",
        f"Recorded {stamp}. Machine-readable twins: "
        "`ACTUAL_CROSS_MODEL_DCI_ROWS.jsonl`, "
        "`ACTUAL_CROSS_MODEL_DCI_RUN_MANIFEST.json`.",
        "",
        "`EXPLORATORY_NO_EVIDENCE`. One frozen design — target A, focal B, "
        "reference C_L3, order QAC, 20 pilot tasks, 2 replicates, two "
        "backgrounds — run against every checkpoint that could be made to "
        "execute it. **Backends differ per checkpoint** and that difference is "
        "recorded on every row; see §6 before comparing any two models.",
        "",
        "Condition: `THINKING_ENABLED_BOUNDED`. Thinking is on, no budget is "
        "assigned, and a fixed ceiling bounds total generation. A request that "
        "reaches the ceiling is recorded `NO_FINAL_WITHIN_BUDGET` and kept — "
        "never force-closed, never given an invented answer, never counted as "
        "an A-failure.",
        "",
        table(head),
        "",
        "τ = P(A fails | focal B) − P(A fails | reference C_L3), over rows that "
        "produced a final answer, pooled across backgrounds and weighted by "
        "those rows. Per-background detail and the degeneracy label are in §1.",
        "",
        "## 1. k=3 results",
        "",
        table(cells[["model", "backend", "load", "background", "requested",
                     "final_answers", "no_final", "technical_failures",
                     "A_fail_focal", "A_fail_reference", "tau", "lo", "hi",
                     "n_tasks", "joint_focal", "degeneracy"]]
              [cells["load"] == contract.LOAD]),
        "",
        "A `TARGET_CEILING` label means the target instruction essentially "
        "never fails in either arm, so τ is 0 **by construction** rather than "
        "by absence of interference. The number is reported, not withheld; it "
        "simply cannot carry the signal the design was built to detect.",
        "",
        "### Who is missing from the scored subsample",
        "",
        "Every rate above is conditional on the row having produced a final "
        "answer. That is only harmless if rows go missing at the same rate on "
        "both sides of a contrast.",
        "",
        table(missingness(frame), floats="{:.3f}"),
        "",
        *(missingness_warnings(missingness(frame)) or
          ["* No checkpoint lost a row; every contrast is between complete "
           "cells."]),
        "",
        "Where the spread is marked **differential**, the τ and Δ below compare "
        "two differently-selected subsamples and the bootstrap intervals do "
        "not account for it. Treat those estimates as descriptive of the rows "
        "that finished, not of the design as specified.",
        "",
        "### Semicolon-minus-control contrast",
        "",
        table(background_contrast(frame[frame["load"] == contract.LOAD])),
        "",
        "### Secondary, exploratory: joint satisfaction in the focal arm",
        "",
        "Not pre-registered, and reported because the primary estimand is "
        "degenerate wherever the target is at ceiling. J = P(A and B both "
        "satisfied | focal arm).",
        "",
        table(joint_contrast(frame[frame["load"] == contract.LOAD])),
        "",
        "## 2. Four-state outcomes in the focal arm",
        "",
        indexed_table(four_state(frame)),
        "",
        "### In-context compliance with each instruction",
        "",
        table(compliance(frame)),
        "",
        "## 3. Reasoning length and termination",
        "",
        "Per model only. Token counts index different tokenizers and are never "
        "summed, averaged or ranked across families.",
        "",
        table(termination(frame), floats="{:.1f}"),
        "",
        "By arm and background — where an answer-rate gap comes from:",
        "",
        table(termination_by_cell(frame), floats="{:.1f}"),
        "",
    ]

    k5 = cells[cells["load"] != contract.LOAD]
    parts += ["## 4. k=5 results", ""]
    if len(k5):
        parts += [
            "Run for checkpoints whose target instruction is saturated at k=3, "
            "using the repository's existing k=5 construction — the same QAC "
            "contrast with `U_LEX_FORBID3` and `U_NUM_MAXINT` pinned in a fixed "
            "tail. No new difficulty was invented.",
            "",
            table(k5[["model", "backend", "load", "background", "requested",
                      "final_answers", "no_final", "A_fail_focal",
                      "A_fail_reference", "tau", "lo", "hi", "n_tasks",
                      "degeneracy"]]),
            "",
            "### Semicolon-minus-control contrast at k=5",
            "",
            table(background_contrast(frame[frame["load"] != contract.LOAD])),
            "",
        ]
    else:
        parts += ["Not run. See §6.", ""]

    failures = frame[frame["final_answer_status"].isin(
        [schema.TECHNICAL_FAILURE, schema.NOT_GENERATED])]
    parts += ["## 5. Technical failures", ""]
    if len(failures):
        summary = (failures.groupby(
            ["model_id", "final_answer_status"]).size()
            .rename("rows").reset_index())
        parts += [table(summary), ""]
        reasons = sorted({str(r)[:200] for r
                          in failures["technical_failure_reason"] if str(r).strip()}
                         | {str(r)[:200] for r
                            in failures.get("not_generated_reason", pd.Series(dtype=str))
                            if str(r).strip()})
        for reason in reasons[:10]:
            parts.append(f"* `{reason}`")
        parts.append("")
    else:
        parts += ["None. Every requested row was attempted and returned a "
                  "generation.", ""]

    parts += ["## 6. Backend and execution limitations", ""]
    for entry in manifest(frame):
        parts.append(
            f"* **{entry['model_id'].split('/')[-1]}** (k={entry['load']}) — "
            f"`{entry['backend']} {entry['backend_version']}`, "
            f"{entry['dtype']}, {entry['quantization']}, "
            f"{entry['gpu_layout']}; thinking via "
            f"`{entry['thinking_implementation']}`; ceiling "
            f"{entry['generation_ceiling']} tokens/request; revision "
            f"`{entry['model_revision'][:12]}`")
    parts.append("")
    if missing:
        parts += ["### Checkpoints with no rows", ""]
        for entry in missing:
            parts.append(f"* **{entry['model_id']}** — {entry['reason']}")
        parts.append("")
    parts += [
        "Cross-model differences must be read against this table. Two "
        "checkpoints executed on different backends differ in more than their "
        "weights: attention kernel, batching, KV layout and sampler "
        "implementation all move together with the backend. Nothing here "
        "licenses attributing a between-model difference to the models.",
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dirs", nargs="+")
    parser.add_argument("--missing", default=None,
                        help="JSON list of {model_id, reason} for checkpoints "
                             "that produced no rows")
    parser.add_argument("--out", default="ACTUAL_CROSS_MODEL_DCI_RESULTS.md")
    args = parser.parse_args()

    frame = score(load([Path(d) for d in args.dirs]))
    cells = per_cell(frame)
    missing = json.loads(Path(args.missing).read_text()) if args.missing else []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    out = Path(args.out)
    out.write_text(document(frame, cells, missing, stamp))

    rows_path = out.with_name("ACTUAL_CROSS_MODEL_DCI_ROWS.jsonl")
    keep = [c for c in frame.columns if c not in ("rendered_prompt",)]
    with rows_path.open("w") as handle:
        for record in frame[keep].to_dict("records"):
            handle.write(json.dumps(record, default=str) + "\n")

    manifest_path = out.with_name("ACTUAL_CROSS_MODEL_DCI_RUN_MANIFEST.json")
    manifest_path.write_text(json.dumps({
        "stamp": "EXPLORATORY_NO_EVIDENCE",
        "experiment": "ACTUAL_CROSS_MODEL_DCI",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "contract": contract.as_dict(STATE),
        "bootstrap_draws": plotstyle.BOOTSTRAP_DRAWS,
        "bootstrap_cluster": "task_id (paired within task)",
        "executions": manifest(frame),
        "checkpoints_without_rows": missing,
        "headline": headline(cells).to_dict("records"),
        "cells": cells.to_dict("records"),
    }, indent=1, default=str))

    print(document(frame, cells, missing, stamp))
    print(f"wrote {out}\n      {rows_path}\n      {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
