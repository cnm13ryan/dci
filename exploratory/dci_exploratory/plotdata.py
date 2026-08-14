"""Rebuild every plotted quantity from the preserved run artifacts.

Nothing here reads a summary table or a matrix document. Each estimate is
recomputed from the stored generations, scored against the same registry the
runs used, so a figure and a matrix disagreeing is a detectable event rather
than a silent one.

Two channels are kept apart throughout: the reasoning trace is never scored and
never reaches a verifier. Only `answer` (vLLM path) or `response` (Transformers
path) is verified.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dci_exploratory import extensions, harvest, mechanism, plotstyle
from vllm_backend.contract import canonicalise_row

#: Language that would mean the answer channel is continued scratch work rather
#: than an answer. This is the Round 8 failure mode, checked rather than assumed.
SCRATCH = re.compile(
    r"\b(wait|let me (check|count|think|see)|i need to|hmm|actually,? (no|wait)|"
    r"let'?s count|recount|that'?s wrong)\b", re.IGNORECASE)

_STATE: Any = None


def state():
    global _STATE
    if _STATE is None:
        extensions.register()
        _STATE = harvest.load()
    return _STATE


def _pass(text: Any, constraint: str) -> float:
    if not isinstance(text, str) or not text.strip():
        return float("nan")
    return float(state().verify(text, constraint).binary_pass)


def latest(pattern: str) -> Path:
    import glob
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return Path(matches[-1])


# ------------------------------------------------------- the reasoning run
#: Generation files that exist on disk and must never reach a figure or a table,
#: with the reason, mirroring the status column in `REASONING_DATA_PROVENANCE.md`.
#: Keyed by basename because that is what survives a run directory being copied.
#:
#: This check lives in `load_reasoning`, not only in `load_all_reasoning`, because
#: `load_all_reasoning` was the guarded wrapper and `make_figures.py` reached past
#: it to the raw loader — so the tested invariant and the production figure path
#: disagreed, and the committed row-level export came from the unguarded one. A
#: guard beside the path is not a guard.
NON_ADMISSIBLE: dict[str, str] = {
    "s18_reasoning.jsonl": (
        "DEPRECATED: one shared seed for all 160 requests, so nominal replicate "
        "pairs are byte-identical (390/400). Superseded by s18_reseeded.jsonl"),
    "s18_transition.jsonl": (
        "FOREIGN: Round 10 transition budgets from another branch, 98.4% "
        "duplicate replicate pairs; deprecated as curve-shape evidence"),
    "s18_reasoning.scored.jsonl": (
        "DERIVED from the deprecated shared-seed grid, not a generation artifact"),
}


class NonAdmissibleEvidence(ValueError):
    """A generation file whose recorded status forbids it as analysis input."""


def check_admissible(path: Path, *, allow_non_admissible: bool = False) -> None:
    """Refuse a known-deprecated generation file as an analysis input."""
    reason = NON_ADMISSIBLE.get(Path(path).name)
    if reason and not allow_non_admissible:
        raise NonAdmissibleEvidence(
            f"{path} is not admissible evidence — {reason}. Pass "
            "allow_non_admissible=True only to demonstrate the defect itself.")


def load_reasoning(path: Path, *,
                   allow_non_admissible: bool = False) -> pd.DataFrame:
    """Score the vLLM reasoning-budget generations from the ANSWER field only."""
    check_admissible(path, allow_non_admissible=allow_non_admissible)
    # ONE migration boundary: archived generations, read as canonical.
    frame = pd.DataFrame([canonicalise_row(json.loads(line))
                          for line in Path(path).open()])
    target = frame["measured"].iloc[0]

    frame["a_pass"] = [_pass(t, target) for t in frame["final_answer"]]
    frame["arm_pass"] = [_pass(t, a) for t, a in zip(frame["final_answer"], frame["arm"])]
    frame["c_pass"] = [_pass(t, v) for t, v in zip(frame["final_answer"], frame["variant"])]
    frame["a_failure"] = 1.0 - frame["a_pass"]
    frame["joint"] = frame["a_pass"] * frame["arm_pass"] * frame["c_pass"]

    frame["answer_empty"] = frame["final_answer"].str.strip().str.len().eq(0)
    frame["scratch_marker"] = frame["final_answer"].str.contains(SCRATCH, na=False)
    features = pd.DataFrame([mechanism.row_features(t) for t in frame["final_answer"]],
                            index=frame.index)
    frame = pd.concat([frame, features], axis=1)

    frame["arbitration"] = np.select(
        [(frame["a_pass"] == 1) & (frame["arm_pass"] == 1),
         (frame["a_pass"] == 1) & (frame["arm_pass"] == 0),
         (frame["a_pass"] == 0) & (frame["arm_pass"] == 1)],
        ["both", "target only", "focal only"], default="neither")
    return frame.drop(columns=["reasoning_text"])


def load_all_reasoning(run_dir: Path) -> pd.DataFrame:
    """Every reasoning condition in one frame, with the three kinds kept apart.

    `condition` distinguishes what was actually done to the model, which the bare
    budget number cannot:

      NO_THINKING        the model's own non-thinking mode; there is no reasoning
                         phase to cap, so "0 tokens" is a native setting rather
                         than a truncation.
      LIMITED_REASONING  the thinking phase was deliberately stopped at b tokens.
      NATURAL_REASONING  the thinking phase was not stopped; the only limit is an
                         engineering ceiling derived from the context window, and
                         the condition is valid only if that ceiling never binds.

    `setting` is the ordered label the figures use: the budget for the capped
    conditions, the string "natural" for the uncapped one.
    """
    run_dir = Path(run_dir)
    # The re-seeded capped grid is the ONLY admissible capped input. The original
    # S18 file was generated with ONE seed for all 160 requests, which made
    # replicate pairs byte-identical — two draws counted once. Putting it on the
    # same figure as the natural condition, which is seeded per row, would show
    # two different sampling regimes as one curve.
    #
    # There is deliberately no fallback. `runs/` is gitignored, so a regenerated
    # or partially transferred run directory can easily be missing the re-seeded
    # file while still holding the deprecated one; silently substituting it would
    # publish the defect this file exists to avoid. A missing canonical input is
    # a stop condition, not a degraded mode. The original file is kept, not
    # deleted, so the deprecation remains auditable.
    capped = run_dir / "s18_reseeded.jsonl"
    if not capped.exists():
        raise FileNotFoundError(
            f"canonical capped grid {capped} is absent. The shared-seed grid "
            f"{run_dir / 's18_reasoning.jsonl'} is deprecated (byte-identical "
            "replicate pairs) and is never substituted for it. Regenerate the "
            "re-seeded grid before building any canonical output.")
    frame = load_reasoning(capped)
    frame["capped_source"] = capped.name
    frame["condition"] = np.where(frame["reasoning_budget"] == 0,
                                  "NO_THINKING", "LIMITED_REASONING")
    frame["setting"] = frame["reasoning_budget"]
    frame["engineering_ceiling"] = np.nan

    natural_path = run_dir / "natural_reasoning.jsonl"
    if natural_path.exists():
        natural = load_reasoning(natural_path)
        natural["condition"] = "NATURAL_REASONING"
        natural["setting"] = "natural"
        frame = pd.concat([frame, natural], ignore_index=True)
    frame["setting"] = frame["setting"].astype(object)
    return frame


def reasoning_timing(log_path: Path, rows_per_budget: int) -> pd.DataFrame:
    """Per-budget wall clock, parsed from the preserved generation log.

    This is BATCH wall clock under vLLM continuous batching for all rows at that
    budget, covering both generation phases. Dividing by the row count gives a
    throughput figure, NOT the latency of an isolated request, and every axis
    built from it says so.
    """
    pattern = re.compile(r"^b=\s*(\d+)\s+(\d+) rows\s+([\d.]+)s")
    records = []
    for line in Path(log_path).read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            budget, rows, seconds = int(match[1]), int(match[2]), float(match[3])
            records.append({"reasoning_budget": budget, "rows_cumulative": rows,
                            "batch_wall_seconds": seconds,
                            "seconds_per_row_batched": seconds / rows_per_budget})
    return pd.DataFrame(records).sort_values("reasoning_budget")


def reasoning_cells(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per (budget, background, arm): compliance, τ inputs, diagnostics."""
    records = []
    for (budget, variant, arm), cell in frame.groupby(
            ["reasoning_budget", "variant", "arm"]):
        record = {"reasoning_budget": budget, "variant": variant, "arm": arm,
                  "n_rows": len(cell), "n_tasks": cell["task_id"].nunique(),
                  "cap_hit": cell["reasoning_cap_hit"].mean(),
                  "reasoning_closed": cell["reasoning_closed"].mean(),
                  "realised_reasoning_mean": cell["reasoning_tokens"].mean(),
                  "realised_reasoning_median": cell["reasoning_tokens"].median(),
                  "realised_reasoning_p25": cell["reasoning_tokens"].quantile(.25),
                  "realised_reasoning_p75": cell["reasoning_tokens"].quantile(.75),
                  "answer_tokens_mean": cell["final_answer_tokens"].mean(),
                  "answer_truncated": cell["answer_truncated"].mean(),
                  "answer_empty": cell["answer_empty"].mean(),
                  "scratch_in_answer": cell["scratch_marker"].mean(),
                  "n_sentences": cell["n_sentences"].mean(),
                  "chain_share": cell["chain_share"].mean(),
                  "native_nonthinking": bool(cell["native_nonthinking"].iloc[0])}
        for label, column in (("A", "a_pass"), ("QC", "arm_pass"),
                              ("C", "c_pass"), ("joint", "joint"),
                              ("A_failure", "a_failure")):
            stats = plotstyle.cluster_rate(
                cell, column, f"cells|{budget}|{variant}|{arm}|{label}")
            record[f"{label}"] = stats["estimate"]
            record[f"{label}_lo"], record[f"{label}_hi"] = stats["lo"], stats["hi"]
        for state_name in plotstyle.ARBITRATION_ORDER:
            record[f"arb_{state_name.replace(' ', '_')}"] = (
                cell["arbitration"] == state_name).mean()
        records.append(record)
    return pd.DataFrame(records).sort_values(["reasoning_budget", "variant", "arm"])


def reasoning_tau(frame: pd.DataFrame) -> pd.DataFrame:
    """τ per (budget, background) and the paired amplification Δ per budget."""
    taus: dict[tuple[int, str], pd.Series] = {}
    records = []
    for (budget, variant), cell in frame.groupby(["reasoning_budget", "variant"]):
        series = plotstyle.per_task_tau(cell)
        taus[(budget, variant)] = series
        records.append({"reasoning_budget": budget, "variant": variant,
                        "quantity": "tau",
                        **plotstyle.summarise(series, f"tau|{budget}|{variant}")})
    for budget in sorted(frame["reasoning_budget"].unique()):
        amplifier = taus.get((budget, plotstyle.AMP))
        control = taus.get((budget, plotstyle.CTRL))
        if amplifier is None or control is None:
            continue
        delta = (amplifier - control).dropna()
        records.append({"reasoning_budget": budget, "variant": "DELTA_amp",
                        "quantity": "delta_amplification",
                        **plotstyle.summarise(delta, f"delta|{budget}")})
    return pd.DataFrame(records).sort_values(["reasoning_budget", "variant"])


# ------------------------------------------------------ the amplifier runs
#: Structural class of each background, declared here rather than inferred from
#: its result, so the grouping in the figures cannot be circular.
STRUCTURAL_CLASS = {
    "X_SEMI_EXACT1": "unattached mark", "X_SEMICOLON_FREE": "unattached mark",
    "U_FMT_COLON1": "unattached mark", "X_COLON_FREE": "unattached mark",
    "X_ELLIPSIS_FREE": "unattached mark", "X_DASHDASH_FREE": "unattached mark",
    "U_FMT_PAREN1": "enclosing pair", "X_PAREN_FREE": "enclosing pair",
    "U_FMT_QUOTE1": "enclosing pair",
}
#: How many characters the demanded mark spans, and whether its position is left
#: to the model. Both are declared properties of the INSTRUCTION.
MARK_CHARS = {"X_SEMI_EXACT1": 1, "X_SEMICOLON_FREE": 1, "U_FMT_COLON1": 1,
              "X_COLON_FREE": 1, "X_ELLIPSIS_FREE": 3, "X_DASHDASH_FREE": 2,
              "U_FMT_PAREN1": 2, "X_PAREN_FREE": 2, "U_FMT_QUOTE1": 2}

#: A manipulation this weak cannot support a claim about the property it varies.
COMPLIANCE_GATE = 0.50


def load_amplifier_run(run_dir: Path) -> pd.DataFrame:
    frame, config = mechanism.load(run_dir)
    frame = frame[frame["condition"].isin(["focal", "reference"])].copy()
    frame["variant_pass"] = [_pass(t, v) for t, v
                             in zip(frame["response"], frame["variant"])]
    frame["run"] = run_dir.name
    frame["stage"] = config["stage"]
    return frame


def amplifier_conditions(runs: dict[str, Path]) -> pd.DataFrame:
    """One row per (run, background): τ, Δ vs the run's own enclosing control."""
    records = []
    for label, run_dir in runs.items():
        frame = load_amplifier_run(run_dir)
        taus = {v: plotstyle.per_task_tau(cell)
                for v, cell in frame.groupby("variant")}
        controls = [v for v in taus if STRUCTURAL_CLASS.get(v) == "enclosing pair"]
        baseline = controls[0] if controls else None
        for variant, cell in frame.groupby("variant"):
            compliance = cell["variant_pass"].mean()
            record = {
                "run": run_dir.name, "stage": label, "variant": variant,
                "order": "/".join(sorted(cell["order"].astype(str).unique())),
                "load": int(cell["load"].iloc[0]),
                "structural_class": STRUCTURAL_CLASS.get(variant, "unclassified"),
                "mark_chars": MARK_CHARS.get(variant),
                "own_compliance": compliance,
                "manipulation_ok": bool(compliance >= COMPLIANCE_GATE),
                "n_rows": len(cell), "n_tasks": cell["task_id"].nunique(),
                "focal_A_failure": cell[cell["arm"] == "B"]["a_failure"].mean(),
                "reference_A_failure": cell[cell["arm"] != "B"]["a_failure"].mean(),
                "chain_share_focal": cell[cell["arm"] == "B"]["chain_share"].mean(),
                "n_sentences_focal": cell[cell["arm"] == "B"]["n_sentences"].mean(),
                "baseline_variant": baseline,
            }
            record.update({f"tau_{k}": v for k, v in plotstyle.summarise(
                taus[variant], f"amp_tau|{run_dir.name}|{variant}").items()})
            if baseline is not None and variant != baseline:
                delta = (taus[variant] - taus[baseline]).dropna()
                record.update({f"delta_{k}": v for k, v in plotstyle.summarise(
                    delta, f"amp_delta|{run_dir.name}|{variant}").items()})
            records.append(record)
    return pd.DataFrame(records)
