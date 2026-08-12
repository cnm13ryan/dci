"""Synthetic generation grids for the canonical-pipeline regression tests.

Kept separate from any single test module because three unrelated defects
(canonical-input fallback, guard ordering, tail-sensitivity arithmetic) all need
the same row shape. The fields mirror the real S18 rows exactly; a fixture that
drifted from the real schema would let a repaired guard pass on data the runner
never produces.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

FOCAL, REFERENCE = "B", "C_L3"
BRACKET, SEMICOLON = "X_PAREN_FREE", "X_SEMICOLON_FREE"


def row(task: int, arm: str, variant: str, budget: int, answer: str,
        replicate: int) -> dict:
    """One generation row carrying every field the loaders and guards read."""
    return {
        "row_id": f"PLT{task:02d}-{arm}-{variant}-b{budget}-r{replicate}",
        "task_id": f"PLT{task:02d}",
        "arm": arm,
        "variant": variant,
        "reasoning_budget": budget,
        "reasoning": "some trace",
        "reasoning_tokens": 10 + task,
        "answer": answer,
        "answer_tokens": 20,
        "answer_truncated": False,
        "closed_naturally": True,
        "reasoning_cap_hit": False,
        "measured": "A",
        "order": "QAC",
        "load": 3,
        "condition": "LIMITED_REASONING",
        "native_nonthinking": False,
        "pair_key": f"PLT{task:02d}|QAC|{variant}|r{replicate}",
        "paraphrase_id": 0,
        "ordered_ids": [arm, "A", variant],
        "engineering_ceiling": 39550,
        "replicate": replicate,
        "scaffold": "none",
        "stage": "S18",
        "topic": "t",
        "user_prompt": "p",
    }


def write_grid(path: Path, *, shared_seed: bool, tasks: int = 2) -> None:
    """A small capped grid. Under `shared_seed` both replicates are identical,
    which is the defect that deprecated the original S18 file."""
    rows = []
    for task in range(tasks):
        for arm in (FOCAL, REFERENCE):
            for variant in (BRACKET, SEMICOLON):
                for replicate in range(2):
                    answer = ("One. Two. Three. Four."
                              if shared_seed or replicate == 0
                              else "Alpha. Beta. Gamma. Delta.")
                    rows.append(row(task, arm, variant, 0, answer, replicate))
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def natural_frame(focal_traces_longer: bool = True) -> pd.DataFrame:
    """160 scored rows: 20 tasks x 2 arms x 2 variants x 2 replicates.

    When `focal_traces_longer`, every focal trace is longer than every reference
    trace. That is the adversarial case for a tail-drop applied to the pooled
    cell: it removes focal rows exclusively and unbalances the paired contrast.
    """
    rows = []
    for task in range(20):
        for arm in (FOCAL, REFERENCE):
            for variant in (BRACKET, SEMICOLON):
                for replicate in range(2):
                    record = row(task, arm, variant, 0,
                                 "One. Two. Three. Four.", replicate)
                    if focal_traces_longer:
                        record["reasoning_tokens"] = (
                            1000 + task * 10 + replicate if arm == FOCAL
                            else 10 + task)
                    record["a_failure"] = 0.0
                    record["a_pass"] = 1.0
                    record["arm_pass"] = 1.0
                    record["c_pass"] = 1.0
                    record["outcome"] = "both satisfied"
                    rows.append(record)
    return pd.DataFrame(rows)
