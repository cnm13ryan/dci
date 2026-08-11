"""Canonical analysis of the natural-reasoning endpoint, with hard guards.

Every number this branch publishes is produced here, from the frozen raw
generations, scored through the same registry, with the same paired
task-cluster bootstrap. Markdown matrices are QA targets, never inputs.

The guards fail loudly rather than warn: an analysis that quietly proceeds on a
defective dataset is worse than one that stops.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dci_exploratory import extensions, harvest, mechanism, plotstyle

extensions.register()
STATE = harvest.load()
pd.set_option("display.width", 250)

OUT = Path("figures/reasoning_compute/data")
BRACKET, SEMICOLON = "X_PAREN_FREE", "X_SEMICOLON_FREE"
LABEL = {BRACKET: "+ one bracket pair", SEMICOLON: "+ one semicolon"}
FOCAL, REFERENCE = "B", "C_L3"
EXPECTED = {"tasks": 20, "replicates": 2, "arms": {FOCAL, REFERENCE},
            "variants": {BRACKET, SEMICOLON},
            "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
            "capped_budgets": [0, 256, 512, 1024, 4096]}
#: Anything above this in a nominal-replicate set means a shared seed.
DUPLICATE_ALARM = 0.25

_FAILURES: list[str] = []


def guard(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'ok  ' if ok else 'FAIL'}] {label} {detail}")
    if not ok:
        _FAILURES.append(label)


def _score(frame: pd.DataFrame) -> pd.DataFrame:
    target = frame["measured"].iloc[0]

    def passes(text, constraint):
        if not isinstance(text, str) or not text.strip():
            return float("nan")
        return float(STATE.verify(text, constraint).binary_pass)

    frame = frame.copy()
    frame["a_pass"] = [passes(t, target) for t in frame["answer"]]
    frame["arm_pass"] = [passes(t, a) for t, a in zip(frame["answer"], frame["arm"])]
    frame["c_pass"] = [passes(t, v) for t, v in zip(frame["answer"], frame["variant"])]
    frame["a_failure"] = 1.0 - frame["a_pass"]
    frame["outcome"] = np.select(
        [(frame["a_pass"] == 1) & (frame["arm_pass"] == 1),
         (frame["a_pass"] == 1) & (frame["arm_pass"] == 0),
         (frame["a_pass"] == 0) & (frame["arm_pass"] == 1)],
        ["both satisfied", "main instruction only", "competing instruction only"],
        default="neither")
    features = pd.DataFrame([mechanism.row_features(t) for t in frame["answer"]],
                            index=frame.index)
    return pd.concat([frame, features], axis=1)


def load_canonical(run: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Natural and capped canonical files, scored, after passing every guard."""
    natural_path, capped_path = (run / "natural_reasoning.jsonl",
                                 run / "s18_reseeded.jsonl")
    deprecated = run / "s18_reasoning.jsonl"
    print("canonical inputs:")
    print(f"  natural  {natural_path.name}")
    print(f"  capped   {capped_path.name}")
    if deprecated.exists():
        print(f"  (refusing {deprecated.name}: shared-seed grid, deprecated)")

    natural = _score(pd.DataFrame([json.loads(l) for l in natural_path.open()]))
    capped = _score(pd.DataFrame([json.loads(l) for l in capped_path.open()]))
    config = json.loads((run / "config.json").read_text())

    print("\nguards — natural reasoning:")
    guard("160 rows", len(natural) == 160, f"({len(natural)})")
    guard("20 tasks", natural["task_id"].nunique() == EXPECTED["tasks"])
    guard("2 arms × 2 backgrounds, all cells present",
          set(natural.groupby(["arm", "variant"]).size()) == {40})
    guard("unique row ids", natural["row_id"].is_unique)
    guard("all reasoning closed naturally",
          bool(natural["closed_naturally"].all()),
          f"({int(natural['closed_naturally'].sum())}/{len(natural)})")
    guard("0 engineering-ceiling hits", natural["reasoning_cap_hit"].sum() == 0,
          f"({int(natural['reasoning_cap_hit'].sum())})")
    guard("0 empty answers",
          natural["answer"].str.strip().str.len().gt(0).all())
    guard("0 truncated answers", natural["answer_truncated"].sum() == 0)
    guard("condition label is NATURAL_REASONING",
          set(natural["condition"]) == {"NATURAL_REASONING"})
    guard("ceiling is the derived 39,550, not a round budget",
          set(natural["engineering_ceiling"]) == {39550})
    guard("realised reasoning is far below the ceiling",
          natural["reasoning_tokens"].max() < 39550 * 0.5,
          f"(max {int(natural['reasoning_tokens'].max())})")

    for name, frame, budgets in (("natural", natural, None),
                                 ("capped", capped, EXPECTED["capped_budgets"])):
        pairs = frame.groupby(["reasoning_budget", "task_id", "arm", "variant"])
        sizes = pairs.size()
        complete = sizes[sizes == 2]
        identical = sum(
            1 for _, group in frame.groupby(
                ["reasoning_budget", "task_id", "arm", "variant"])
            if len(group) == 2 and group["answer"].nunique() == 1)
        rate = identical / len(complete) if len(complete) else float("nan")
        print(f"\nguards — {name} sampling:")
        guard(f"{name}: every cell has exactly 2 replicates",
              bool((sizes == 2).all()), f"({sizes.min()}–{sizes.max()})")
        guard(f"{name}: replicates are independent draws",
              rate < DUPLICATE_ALARM,
              f"({identical}/{len(complete)} identical = {rate:.1%})")
        if budgets is not None:
            guard("capped: exactly the expected budgets",
                  sorted(frame["reasoning_budget"].unique()) == budgets,
                  f"({sorted(frame['reasoning_budget'].unique())})")

    print("\nguards — execution condition:")
    # The natural and re-seeded runs were generated by the vLLM backend, whose
    # model identity is NOT in the design config (that records the Transformers
    # model the design was built for) and was never written into the rows — a
    # provenance gap in the runner, since fixed. It IS in the vLLM engine banner
    # of the preserved generation log, which is what this reads.
    banner = re.compile(r"revision=([0-9a-f]{40})")
    logs = {"natural": run / "natural_reasoning_generation.log",
            "capped": run / "s18_reseeded_generation.log"}
    for name, log in logs.items():
        found = set(banner.findall(log.read_text(errors="ignore"))) if log.exists() else set()
        guard(f"{name}: model revision recorded and matches",
              found == {EXPECTED["revision"]},
              f"({sorted(x[:8] for x in found) or 'no log preserved'})")
    guard("instruction order is QAC", set(natural["order"]) == {"QAC"})
    guard("load is 3", set(natural["load"]) == {3})
    guard("variants are the two intended backgrounds",
          set(natural["variant"]) == EXPECTED["variants"])
    guard("arms are focal and matched reference",
          set(natural["arm"]) == EXPECTED["arms"])
    return natural, capped


# ------------------------------------------------------------- estimation
def tau_per_task(cell: pd.DataFrame) -> pd.Series:
    rates = cell.groupby(["arm", "task_id"])["a_failure"].mean()
    return (rates.loc[FOCAL] - rates.loc[REFERENCE]).dropna()


def estimate(series: pd.Series, key: str) -> dict:
    return plotstyle.summarise(series, key)


def question_one(natural: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant, cell in natural.groupby("variant"):
        per_task = tau_per_task(cell)
        stats = estimate(per_task, f"natural|tau|{variant}")
        focal = cell[cell["arm"] == FOCAL]
        reference = cell[cell["arm"] == REFERENCE]
        rows.append({
            "background": LABEL[variant], "variant": variant,
            "focal_failure": focal["a_failure"].mean(),
            "reference_failure": reference["a_failure"].mean(),
            "extra_failures": stats["estimate"], "lo": stats["lo"], "hi": stats["hi"],
            "tasks_positive": int((per_task > 0).sum()),
            "tasks_zero": int((per_task == 0).sum()),
            "tasks_negative": int((per_task < 0).sum()),
            "task_min": per_task.min(), "task_max": per_task.max(),
            "n_rows": len(cell)})
    return pd.DataFrame(rows)


def question_two(natural: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (variant, arm), cell in natural.groupby(["variant", "arm"]):
        tokens = cell["reasoning_tokens"]
        rows.append({
            "background": LABEL[variant],
            "arm": "competing instruction" if arm == FOCAL else "matched comparison",
            "n": len(cell), "mean": tokens.mean(), "median": tokens.median(),
            "p25": tokens.quantile(.25), "p75": tokens.quantile(.75),
            "p90": tokens.quantile(.90), "p95": tokens.quantile(.95),
            "max": tokens.max(),
            "natural_closure": cell["closed_naturally"].mean(),
            "ceiling_hits": int(cell["reasoning_cap_hit"].sum()),
            "answer_tokens": cell["answer_tokens"].mean()})
    return pd.DataFrame(rows)


def question_three(natural: pd.DataFrame) -> pd.DataFrame:
    focal = natural[natural["arm"] == FOCAL]
    table = (pd.crosstab(focal["variant"], focal["outcome"], normalize="index")
             .reindex(columns=["both satisfied", "main instruction only",
                               "competing instruction only", "neither"],
                      fill_value=0.0))
    table.index = [LABEL[v] for v in table.index]
    return table


def task_heterogeneity(natural: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for variant, cell in natural.groupby("variant"):
        per_task = tau_per_task(cell).rename(LABEL[variant])
        frames.append(per_task)
    return pd.concat(frames, axis=1).sort_values(LABEL[SEMICOLON], ascending=False)


def leave_one_out(natural: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant, cell in natural.groupby("variant"):
        per_task = tau_per_task(cell)
        for task in per_task.index:
            rows.append({"background": LABEL[variant], "omitted_task": task,
                         "estimate": per_task.drop(task).mean()})
    return pd.DataFrame(rows)


def long_trace_sensitivity(natural: pd.DataFrame) -> pd.DataFrame:
    """Does the headline depend on a handful of very long traces?

    A SENSITIVITY analysis only. Reasoning length is post-treatment, so dropping
    rows by length is not an estimator of anything — it answers one narrow
    question: would the result look different without the tail?
    """
    rows = []
    for label, drop in (("all rows", 0), ("drop longest 1", 1),
                        ("drop longest 5%", int(0.05 * len(natural) / 4)),
                        ("drop longest 10%", int(0.10 * len(natural) / 4))):
        for variant, cell in natural.groupby("variant"):
            kept = (cell.sort_values("reasoning_tokens").iloc[:len(cell) - drop]
                    if drop else cell)
            per_task = tau_per_task(kept)
            rows.append({"exclusion": label, "background": LABEL[variant],
                         "rows_kept": len(kept), "estimate": per_task.mean(),
                         "n_tasks": len(per_task)})
    return pd.DataFrame(rows)


#: Detector, deliberately kept identical to the one used elsewhere so the
#: definition does not change between datasets. A hit is a candidate, not a
#: finding: every hit is written out with its context for classification.
LEAK = re.compile(r"\b(wait|let me (check|count|think|see)|i need to|hmm|"
                  r"actually,? (no|wait)|let'?s count|recount|that'?s wrong|"
                  r"that'?s \d+ words|now the (second|third|fourth) sentence)\b",
                  re.IGNORECASE)
#: Ordinary-English uses that the detector cannot distinguish from scratch work.
BENIGN = re.compile(r"\b(?:have to |having to |cannot |can'?t |could not |couldn'?t |"
                    r"don'?t |does not |doesn'?t |without )wait\b", re.IGNORECASE)


def leakage_audit(natural: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in natural.iterrows():
        match = LEAK.search(row["answer"])
        if not match:
            continue
        start, end = match.span()
        context = row["answer"][max(0, start - 60):end + 60].replace("\n", " ")
        benign = bool(BENIGN.search(row["answer"][max(0, start - 30):end + 5]))
        rows.append({"task_id": row["task_id"], "arm": row["arm"],
                     "background": LABEL[row["variant"]],
                     "trigger": match.group(0), "context": f"…{context}…",
                     "auto_label": "benign prose" if benign else "needs review"})
    return pd.DataFrame(rows)


def capped_curve(capped: pd.DataFrame, natural: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for budget, group in capped.groupby("reasoning_budget"):
        for variant, cell in group.groupby("variant"):
            stats = estimate(tau_per_task(cell), f"capped|{budget}|{variant}")
            rows.append({"setting": str(budget), "order": budget,
                         "background": LABEL[variant], "variant": variant,
                         "cap_hit": cell["reasoning_cap_hit"].mean(),
                         "realised_median": cell["reasoning_tokens"].median(),
                         **stats})
    for variant, cell in natural.groupby("variant"):
        stats = estimate(tau_per_task(cell), f"natural|tau|{variant}")
        rows.append({"setting": "natural", "order": 10 ** 9,
                     "background": LABEL[variant], "variant": variant,
                     "cap_hit": 0.0,
                     "realised_median": cell["reasoning_tokens"].median(), **stats})
    return pd.DataFrame(rows).sort_values(["order", "variant"])


def main() -> int:
    from dci_exploratory import plotdata
    run = plotdata.latest("runs/stageS18_reasoning_design_*/")
    natural, capped = load_canonical(run)
    OUT.mkdir(parents=True, exist_ok=True)

    q1, q2, q3 = question_one(natural), question_two(natural), question_three(natural)
    het = task_heterogeneity(natural)
    loo = leave_one_out(natural)
    tail = long_trace_sensitivity(natural)
    leaks = leakage_audit(natural)
    curve = capped_curve(capped, natural)

    for name, table in (("natural_question1_interference", q1),
                        ("natural_question2_reasoning_use", q2),
                        ("natural_question3_outcomes", q3),
                        ("natural_task_heterogeneity", het),
                        ("natural_leave_one_task_out", loo),
                        ("natural_long_trace_sensitivity", tail),
                        ("natural_leakage_audit", leaks),
                        ("canonical_capped_and_natural_curve", curve)):
        table.to_csv(OUT / f"{name}.csv", index=(name.endswith(("outcomes",
                                                                "heterogeneity"))))

    fmt = lambda v: f"{v:+.3f}"
    print("\n\n### Q1 — extra main-instruction failures under natural reasoning\n")
    print(q1.to_string(index=False, float_format=fmt))
    print("\n\n### Q2 — how much reasoning the model chose to use\n")
    print(q2.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
    print("\n\n### Q3 — what it did when the instructions competed "
          "(competing-instruction arm)\n")
    print(q3.to_string(float_format=lambda v: f"{v:.3f}"))
    print("\n\n### Task heterogeneity (paired effect per task)\n")
    print(het.to_string(float_format=fmt))
    print("\n\n### Leave-one-task-out\n")
    for background, group in loo.groupby("background"):
        values = group["estimate"]
        print(f"  {background:22s} min {values.min():+.3f}  max {values.max():+.3f}  "
              f"sign changes: {'YES' if values.min() * values.max() < 0 else 'no'}")
    print("\n\n### Long-trace sensitivity (descriptive only)\n")
    print(tail.to_string(index=False, float_format=fmt))
    print("\n\n### Leakage audit\n")
    print(f"  detector hits: {len(leaks)}/{len(natural)}")
    if not leaks.empty:
        print(leaks[["task_id", "arm", "trigger", "auto_label"]].to_string(index=False))
        print("\n  contexts:")
        for _, row in leaks.iterrows():
            print(f"    [{row['auto_label']}] {row['context'][:150]}")
    print("\n\n### Canonical curve (corrected seeds only)\n")
    print(curve[["setting", "background", "estimate", "lo", "hi", "cap_hit",
                 "realised_median"]].to_string(index=False, float_format=fmt))

    print(f"\n{'ALL GUARDS PASSED' if not _FAILURES else f'{len(_FAILURES)} GUARD(S) FAILED: {_FAILURES}'}")
    return 1 if _FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
