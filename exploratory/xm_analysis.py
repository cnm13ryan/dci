"""Cross-model DCI analysis, with hard guards.

Every number the cross-model documents publish is produced here, from the raw
generation rows, scored through the same registry every earlier round used, from
the FINAL ANSWER field only. The guards fail loudly: an analysis that quietly
proceeds on a defective dataset is worse than one that stops.

The estimand, per model m, background c and reasoning condition r:

    tau[m,c,r] = P(F_A = 1 | B, m, c, r) - P(F_A = 1 | R, m, c, r)

and the background contrast

    Delta_semicolon[m,r] = tau[m, semicolon, r] - tau[m, control, r]

Both components of every difference are reported beside it. A reader who is
shown only a difference-of-differences cannot tell a real amplification from two
floors, and the floor case is live on at least one checkpoint here.

    uv run python xm_analysis.py runs/XM_DIR/generations.jsonl [...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crossmodel import contract, seeds
from dci_exploratory import extensions, harvest, plotstyle

extensions.register()
STATE = harvest.load()
pd.set_option("display.width", 250)

SEMICOLON = contract.SEMICOLON_BACKGROUND
CONTROL = contract.CONTROL_BACKGROUND
FOCAL, REFERENCE = contract.FOCAL, contract.REFERENCE
LABEL = {CONTROL: "+ one bracket pair (control)", SEMICOLON: "+ one semicolon"}

_FAILURES: list[str] = []


def guard(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'ok  ' if ok else 'FAIL'}] {label} {detail}")
    if not ok:
        _FAILURES.append(label)


# ------------------------------------------------------------------- loading
def load(paths: list[Path]) -> pd.DataFrame:
    rows = []
    for path in paths:
        rows.extend(json.loads(line) for line in Path(path).open())
    frame = pd.DataFrame(rows)
    print(f"\nloaded {len(frame)} rows from {len(paths)} file(s)")
    return frame


def score(frame: pd.DataFrame) -> pd.DataFrame:
    """Verify the FINAL ANSWER, and nothing else, against the registry.

    The reasoning channel never reaches a verifier. That is not a convention
    here, it is the validity condition of the whole study: a scored scratchpad
    would count planning prose as the answer's sentences.
    """
    frame = frame.copy()

    def passes(text, constraint):
        if not isinstance(text, str) or not text.strip():
            return float("nan")
        return float(STATE.verify(text, constraint).binary_pass)

    target = frame["measured"].iloc[0]
    frame["a_pass"] = [passes(t, target) for t in frame["final_answer"]]
    frame["arm_pass"] = [passes(t, a) for t, a in
                         zip(frame["final_answer"], frame["arm"])]
    frame["c_pass"] = [passes(t, v) for t, v in
                       zip(frame["final_answer"], frame["background"])]
    frame["a_failure"] = 1.0 - frame["a_pass"]
    frame["outcome"] = np.select(
        [(frame["a_pass"] == 1) & (frame["arm_pass"] == 1),
         (frame["a_pass"] == 1) & (frame["arm_pass"] == 0),
         (frame["a_pass"] == 0) & (frame["arm_pass"] == 1)],
        ["both satisfied", "target only", "focal only"], default="neither")
    return frame


# -------------------------------------------------------------------- guards
def check(frame: pd.DataFrame) -> None:
    print("\nguards — design integrity")
    guard("unique row ids per model and mode",
          not frame.duplicated(["model_id", "reasoning_mode",
                                "row_id"]).any())
    guard("instruction order is QAC", set(frame["order"]) == {contract.ORDER})
    guard("load is 3", set(frame["load"]) == {contract.LOAD})
    guard("arms are focal and matched reference",
          set(frame["arm"]) == {FOCAL, REFERENCE})
    guard("backgrounds are the two intended ones",
          set(frame["background"]) == {SEMICOLON, CONTROL})
    guard("target measured everywhere",
          set(frame["measured"]) == {contract.TARGET})

    print("\nguards — provenance")
    guard("every row carries a model id", frame["model_id"].notna().all())
    guard("every row carries a 40-char revision",
          frame["model_revision"].fillna("").str.len().eq(40).all())
    guard("one revision per model",
          (frame.groupby("model_id")["model_revision"].nunique() == 1).all())
    guard("decoding identical across models",
          frame[["temperature", "top_p", "top_k",
                 "max_final_answer_tokens"]].drop_duplicates().shape[0] == 1,
          f"({frame[['temperature','top_p','top_k']].drop_duplicates().to_dict('records')})")

    for (model, mode), cell in frame.groupby(["model_id", "reasoning_mode"]):
        name = f"{model.split('/')[-1]}/{mode}"
        print(f"\nguards — {name}")
        guard(f"{name}: {contract.EXPECTED_ROWS} rows",
              len(cell) == contract.EXPECTED_ROWS, f"({len(cell)})")
        guard(f"{name}: {contract.N_TASKS} tasks",
              cell["task_id"].nunique() == contract.N_TASKS)
        sizes = cell.groupby(["task_id", "arm", "background"]).size()
        guard(f"{name}: every cell has exactly {contract.REPLICATES} replicates",
              bool((sizes == contract.REPLICATES).all()),
              f"({sizes.min()}–{sizes.max()})")
        audit = seeds.replicate_duplication(cell.to_dict("records"))
        guard(f"{name}: replicates are independent draws",
              not audit["implausible"],
              f"({audit['identical_pairs']}/{audit['replicate_pairs']} "
              f"identical = {audit['identical_rate']:.1%})")
        guard(f"{name}: no technical failures",
              int(cell["technical_failure"].sum()) == 0,
              f"({int(cell['technical_failure'].sum())})")
        guard(f"{name}: no empty answers",
              int(cell["answer_empty"].sum()) == 0,
              f"({int(cell['answer_empty'].sum())})")
        guard(f"{name}: no truncated answers",
              int(cell["answer_truncated"].sum()) == 0,
              f"({int(cell['answer_truncated'].sum())})")
        if mode == "NATURAL_REASONING":
            caps = int(cell["reasoning_cap_hit"].sum())
            guard(f"{name}: 0 engineering-ceiling hits", caps == 0, f"({caps})")
            ceiling = cell["engineering_ceiling"].iloc[0]
            guard(f"{name}: realised reasoning far below the ceiling",
                  cell["reasoning_tokens"].max() < ceiling * 0.5,
                  f"(max {int(cell['reasoning_tokens'].max())} of {ceiling})")
            guard(f"{name}: no assigned budget under natural reasoning",
                  cell["assigned_reasoning_budget"].isna().all())
        if mode == "NO_THINKING":
            guard(f"{name}: no reasoning trace was produced",
                  int((cell["reasoning_tokens"] > 0).sum()) == 0)


# ---------------------------------------------------------------- estimation
def tau_per_task(cell: pd.DataFrame) -> pd.Series:
    """Paired over tasks: the task is the resampling cluster."""
    rates = cell.groupby(["arm", "task_id"])["a_failure"].mean()
    if FOCAL not in rates.index.get_level_values(0):
        return pd.Series(dtype=float)
    return (rates.loc[FOCAL] - rates.loc[REFERENCE]).dropna()


def main_result(frame: pd.DataFrame) -> pd.DataFrame:
    """tau and its two raw components, per model, background and mode."""
    rows = []
    for (model, mode, background), cell in frame.groupby(
            ["model_id", "reasoning_mode", "background"]):
        per_task = tau_per_task(cell)
        stats = plotstyle.summarise(
            per_task, f"{model}|{mode}|tau|{background}")
        focal = cell[cell["arm"] == FOCAL]
        reference = cell[cell["arm"] == REFERENCE]
        rows.append({
            "model": model.split("/")[-1], "model_id": model,
            "reasoning": mode, "background": LABEL[background],
            "variant": background,
            "focal_A_failure": focal["a_failure"].mean(),
            "reference_A_failure": reference["a_failure"].mean(),
            "tau": stats["estimate"], "lo": stats["lo"], "hi": stats["hi"],
            "n_tasks": stats["n_tasks"], "n_rows": len(cell),
            "tasks_positive": int((per_task > 0).sum()),
            "tasks_zero": int((per_task == 0).sum()),
            "tasks_negative": int((per_task < 0).sum()),
            "degeneracy": degeneracy(focal["a_failure"].mean(),
                                     reference["a_failure"].mean())})
    return pd.DataFrame(rows)


#: Rates at or beyond these are treated as saturated for interpretation.
CEILING, FLOOR = 0.02, 0.98


def degeneracy(focal_failure: float, reference_failure: float) -> str:
    """Is tau estimable here, or is the target saturated?

    The brief warns about the FLOOR case — a focal instruction the model can
    barely satisfy, where the four-state table reports "neither" versus "target
    only" rather than arbitration. The mirror case is just as important and is
    easier to misread: if the target never fails in EITHER arm, tau is zero by
    construction, not by absence of interference. "No extra failures" and "no
    failures to add to" are different findings and must not share a row.
    """
    if focal_failure <= CEILING and reference_failure <= CEILING:
        return ("TARGET_CEILING — the target never fails in either arm, so tau "
                "is 0 by construction and cannot detect interference")
    if focal_failure >= FLOOR and reference_failure >= FLOOR:
        return ("TARGET_FLOOR — the target always fails in either arm, so tau "
                "is 0 by construction")
    return "estimable"


def background_contrast(frame: pd.DataFrame) -> pd.DataFrame:
    """Delta = tau(semicolon) - tau(control), paired within task."""
    rows = []
    for (model, mode), cell in frame.groupby(["model_id", "reasoning_mode"]):
        taus = {v: tau_per_task(sub)
                for v, sub in cell.groupby("background")}
        if SEMICOLON not in taus or CONTROL not in taus:
            continue
        delta = (taus[SEMICOLON] - taus[CONTROL]).dropna()
        stats = plotstyle.summarise(delta, f"{model}|{mode}|delta")
        rows.append({
            "model": model.split("/")[-1], "reasoning": mode,
            "tau_control": taus[CONTROL].mean(),
            "tau_semicolon": taus[SEMICOLON].mean(),
            "delta_semicolon": stats["estimate"],
            "lo": stats["lo"], "hi": stats["hi"],
            "n_tasks": stats["n_tasks"]})
    return pd.DataFrame(rows)


def joint_contrast(frame: pd.DataFrame) -> pd.DataFrame:
    """SECONDARY, and only because the primary estimand is degenerate here.

    Every checkpoint in this study protects the target instruction almost
    perfectly, so `tau` — a contrast between two target-failure rates — is zero
    by construction and can carry no signal. That is a real finding, not a
    measurement failure, but it leaves the question "does the semicolon context
    cost anything at all?" unanswered by the pre-registered quantity.

    This asks it of the outcome that still moves: joint satisfaction in the
    focal arm, where the two instructions actually compete.

        J(m,c,r) = P(A and B both satisfied | focal arm, m, c, r)
        Delta_J  = J(semicolon) - J(control)

    Paired over tasks and bootstrapped the same way. It is NOT the study's
    estimand, it was not pre-registered, and it is reported as exploratory.
    """
    rows = []
    focal_only = frame[frame["arm"] == FOCAL]
    for (model, mode), cell in focal_only.groupby(["model_id",
                                                   "reasoning_mode"]):
        cell = cell.copy()
        cell["both"] = (cell["outcome"] == "both satisfied").astype(float)
        rates = cell.groupby(["background", "task_id"])["both"].mean()
        if (SEMICOLON not in rates.index.get_level_values(0)
                or CONTROL not in rates.index.get_level_values(0)):
            continue
        delta = (rates.loc[SEMICOLON] - rates.loc[CONTROL]).dropna()
        stats = plotstyle.summarise(delta, f"{model}|{mode}|joint")
        rows.append({
            "model": model.split("/")[-1], "reasoning": mode,
            "joint_control": rates.loc[CONTROL].mean(),
            "joint_semicolon": rates.loc[SEMICOLON].mean(),
            "delta_joint": stats["estimate"], "lo": stats["lo"],
            "hi": stats["hi"], "n_tasks": stats["n_tasks"]})
    return pd.DataFrame(rows)


def four_state(frame: pd.DataFrame) -> pd.DataFrame:
    """What the model did in the FOCAL arm, where the two instructions compete."""
    focal = frame[frame["arm"] == FOCAL]
    table = (pd.crosstab(
        [focal["model_id"].str.split("/").str[-1], focal["reasoning_mode"],
         focal["background"].map(LABEL)], focal["outcome"], normalize="index")
        .reindex(columns=["both satisfied", "target only", "focal only",
                          "neither"], fill_value=0.0))
    table.index.names = ["model", "reasoning", "background"]
    return table


def primitive_compliance(frame: pd.DataFrame) -> pd.DataFrame:
    """In-context compliance with each instruction, by model and mode.

    Not a substitute for the Stage D isolated gate, but the same question asked
    of the scientific rows: can this checkpoint satisfy the pieces at all? A
    focal instruction near floor makes the four-state table mostly a report on
    'neither' versus 'target only', not on arbitration.
    """
    rows = []
    for (model, mode), cell in frame.groupby(["model_id", "reasoning_mode"]):
        focal = cell[cell["arm"] == FOCAL]
        reference = cell[cell["arm"] == REFERENCE]
        rows.append({
            "model": model.split("/")[-1], "reasoning": mode,
            "A_in_focal_arm": focal["a_pass"].mean(),
            "A_in_reference_arm": reference["a_pass"].mean(),
            "B_compliance": focal["arm_pass"].mean(),
            "R_compliance": reference["arm_pass"].mean(),
            "background_compliance": cell["c_pass"].mean()})
    return pd.DataFrame(rows)


def reasoning_use(frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive, model-specific, and never pooled across families.

    Reasoning tokens are not a universal unit of compute: a Qwen token, a Gemma
    token and a Kimi token index different tokenizers and different training. The
    table is reported per model and is not summed, averaged or ranked across them.
    """
    rows = []
    natural = frame[frame["reasoning_mode"] == "NATURAL_REASONING"]
    for (model, background, arm), cell in natural.groupby(
            ["model_id", "background", "arm"]):
        tokens = cell["reasoning_tokens"]
        rows.append({
            "model": model.split("/")[-1],
            "background": LABEL[background],
            "arm": "focal B" if arm == FOCAL else "reference R",
            "n": len(cell), "median": tokens.median(),
            "p25": tokens.quantile(.25), "p75": tokens.quantile(.75),
            "p90": tokens.quantile(.90), "p95": tokens.quantile(.95),
            "max": tokens.max(),
            "closure_rate": cell["natural_reasoning_closed"].mean(),
            "ceiling_hits": int(cell["reasoning_cap_hit"].sum()),
            "answer_tokens": cell["final_answer_tokens"].mean(),
            "latency_s": cell["latency_seconds"].mean()})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ leakage
#: The repository's own detector. It over-flags ordinary prose — the canonical
#: run's 2 hits were both benign — so its output is a QUEUE for inspection, never
#: a count of confirmed leakage.
LEAK_PATTERN = (r"\b(wait|let me (check|count|think|see)|i need to|hmm|"
                r"actually,? (no|wait)|let'?s count|recount|that'?s wrong)\b")


def leakage_queue(frame: pd.DataFrame) -> pd.DataFrame:
    hits = frame[frame["final_answer"].str.contains(
        LEAK_PATTERN, case=False, na=False, regex=True)]
    return hits[["model_id", "reasoning_mode", "task_id", "arm", "background",
                 "row_id", "final_answer"]]


# --------------------------------------------------------------------- main
def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print(__doc__)
        return 2

    frame = score(load(paths))
    check(frame)

    print("\n\n### 1. tau(B->A) by model, background and reasoning condition")
    print("### Both raw components are shown beside every difference.\n")
    result = main_result(frame)
    print(result.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    degenerate = result[result["degeneracy"] != "estimable"]
    if len(degenerate):
        print("\n  !! tau is NOT estimable in some cells:")
        for row in degenerate.itertuples():
            print(f"     {row.model} / {row.reasoning} / {row.background}: "
                  f"{row.degeneracy}")

    print("\n\n### 2. Semicolon-minus-control contrast\n")
    delta = background_contrast(frame)
    print(delta.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    print("\n\n### 2b. SECONDARY, exploratory: joint satisfaction in the focal arm")
    print("### Reported because the primary estimand is degenerate here.\n")
    joint = joint_contrast(frame)
    print(joint.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))

    print("\n\n### 3. Four-state outcomes in the focal arm\n")
    print(four_state(frame).to_string(float_format=lambda v: f"{v:.3f}"))

    print("\n\n### 4. In-context compliance with each instruction\n")
    print(primitive_compliance(frame).to_string(
        index=False, float_format=lambda v: f"{v:.3f}"))

    print("\n\n### 5. Natural-reasoning use (descriptive, per model only)\n")
    use = reasoning_use(frame)
    if len(use):
        print(use.to_string(index=False, float_format=lambda v: f"{v:.1f}"))

    print("\n\n### 6. Leakage detector queue (hits, NOT confirmed leakage)\n")
    queue = leakage_queue(frame)
    print(f"  {len(queue)} detector hit(s) of {len(frame)} rows — "
          "each requires manual classification before it counts as leakage")

    out = paths[0].parent / "analysis"
    out.mkdir(exist_ok=True)
    result.to_csv(out / "tau_by_model.csv", index=False)
    delta.to_csv(out / "delta_semicolon.csv", index=False)
    four_state(frame).to_csv(out / "four_state.csv")
    primitive_compliance(frame).to_csv(out / "compliance.csv", index=False)
    use.to_csv(out / "reasoning_use.csv", index=False)
    joint.to_csv(out / "joint_contrast.csv", index=False)
    queue.to_csv(out / "leakage_queue.csv", index=False)
    frame.drop(columns=["raw_generation", "reasoning_text", "rendered_prompt"],
               errors="ignore").to_json(
        out / "scored.jsonl", orient="records", lines=True)
    print(f"\nwrote {out}/")

    print(f"\n{'ALL GUARDS PASSED' if not _FAILURES else f'{len(_FAILURES)} GUARD(S) FAILED: {_FAILURES}'}")
    return 1 if _FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
