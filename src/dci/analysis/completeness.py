"""Task-level completeness of the primary estimator's input table.

WHAT THIS STRENGTHENS
---------------------
The pre-repair confirmatory stage already checked that every required CONDITION
existed as a column of the task table, and it already refused rows generated
outside the frozen batch plan. Both checks are real and are kept.

Neither of them constrains the CELLS. `bootstrap_functional` averages the task
table with `np.nanmean(..., axis=0)`, so a hole in one column is silently
averaged over a different subset of tasks than its neighbours. The focal and
reference arms of a contrast would then be means over different task
populations, which is precisely the confound the complete crossing exists to
remove -- and it would be invisible, because a mean of the surviving cells is
always a number.

This module makes such a hole loud, and does it BEFORE the bootstrap, where the
remedy is still "find the missing generations" rather than "reinterpret tau".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Iterable


def missing_cells(table: pd.DataFrame) -> pd.DataFrame:
    """Every (task, column) hole in a task-level cell table."""
    holes = table.isna()
    if not bool(holes.to_numpy().any()):
        return pd.DataFrame(columns=["task_id", "column"])
    stacked = holes.stack(list(range(holes.columns.nlevels)), future_stack=True)
    idx = stacked[stacked].index
    return pd.DataFrame(
        [{"task_id": str(row[0]), "column": "|".join(str(p) for p in row[1:])}
         for row in idx],
        columns=["task_id", "column"])


def column_support(table: pd.DataFrame) -> pd.Series:
    """Number of tasks actually contributing to each column's mean."""
    return table.notna().sum(axis=0)


def assert_primary_table_complete(table: pd.DataFrame,
                                  required_columns: Iterable = (),
                                  label: str = "primary") -> pd.DataFrame:
    """Refuse to bootstrap an incomplete task x condition table.

    Three distinct failures, each with its own message because each has its own
    remedy:
      * a required column is absent            -> the design never generated it;
      * a cell is NaN                          -> that generation is missing;
      * columns have unequal support           -> arms would be averaged over
                                                  different task populations.
    Returns a per-column support report for the artifact trail.
    """
    required = list(required_columns)
    absent = [c for c in required if c not in table.columns]
    if absent:
        raise ValueError(
            f"{label} task table is missing required columns: {absent}")

    holes = missing_cells(table)
    if len(holes):
        shown = holes.head(12).to_string(index=False)
        raise ValueError(
            f"{label} task table has {len(holes)} empty task x condition cells, "
            f"so its columns would be averaged over different task subsets. "
            f"np.nanmean would hide this. First rows:\n{shown}")

    support = column_support(table)
    distinct = sorted(set(int(v) for v in support.to_numpy()))
    if len(distinct) != 1:
        raise ValueError(
            f"{label} task table columns have unequal task support {distinct}; "
            "a contrast between two such columns is not a within-task contrast")
    if distinct[0] != len(table):
        raise ValueError(
            f"{label} task table has {len(table)} rows but every column is "
            f"supported by {distinct[0]} tasks")

    report = pd.DataFrame({"support": support.astype(int)})
    report["n_tasks"] = len(table)
    report["complete"] = report["support"] == len(table)
    return report


def assert_finite_point_estimates(point: pd.Series, keys: Iterable[str],
                                  label: str = "primary") -> None:
    """Every named estimand must be a finite number before inference."""
    bad = [str(k) for k in keys
           if k not in point.index
           or not np.isfinite(pd.to_numeric(point.get(k), errors="coerce"))]
    if bad:
        raise ValueError(
            f"{label} point estimates are missing or non-finite for: {bad}")
