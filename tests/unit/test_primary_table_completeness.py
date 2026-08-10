"""A hole in the task x condition table must stop the bootstrap, not be averaged.

`bootstrap_functional` uses np.nanmean, so an empty cell silently narrows one
column's task population. The focal and reference arms of a contrast would then
be means over different tasks -- the exact confound the complete crossing exists
to remove, and invisible, because the mean of the surviving cells is a number.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.completeness import (assert_finite_point_estimates,
                                       assert_primary_table_complete,
                                       column_support, missing_cells)

pytestmark = pytest.mark.cpu

CONDITIONS = ["A_ONLY", "B|target_first", "C1|target_first"]
TARGET = "A"


def _table(n_tasks: int = 8) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    cols = pd.MultiIndex.from_tuples([(c, TARGET) for c in CONDITIONS],
                                     names=["condition_id", "constraint_id"])
    return pd.DataFrame(rng.random((n_tasks, len(CONDITIONS))),
                        index=[f"t{i}" for i in range(n_tasks)], columns=cols)


def test_complete_table_passes_and_reports_support():
    table = _table()
    report = assert_primary_table_complete(
        table, [(c, TARGET) for c in CONDITIONS], label="confirmatory")
    assert len(report) == len(CONDITIONS)
    assert bool(report["complete"].all())
    assert set(report["support"]) == {8}
    assert missing_cells(table).empty


def test_single_empty_cell_is_refused():
    table = _table()
    table.iloc[3, 1] = np.nan
    with pytest.raises(ValueError, match="empty task x condition cells"):
        assert_primary_table_complete(table, [(c, TARGET) for c in CONDITIONS])
    holes = missing_cells(table)
    assert len(holes) == 1
    assert holes.iloc[0]["task_id"] == "t3"
    assert "B|target_first" in holes.iloc[0]["column"]


def test_unequal_support_is_named_as_such():
    """A whole-column hole is the dangerous case: every remaining cell is fine."""
    table = _table()
    table.iloc[:2, 2] = np.nan
    with pytest.raises(ValueError, match="empty task x condition cells"):
        assert_primary_table_complete(table, [(c, TARGET) for c in CONDITIONS])
    support = column_support(table)
    assert sorted(set(int(v) for v in support)) == [6, 8]


def test_missing_required_column_is_distinguished_from_a_hole():
    table = _table().drop(columns=[("C1|target_first", TARGET)])
    with pytest.raises(ValueError, match="missing required columns"):
        assert_primary_table_complete(table, [(c, TARGET) for c in CONDITIONS])


def test_nanmean_would_have_hidden_the_hole():
    """Demonstrates the failure mode the invariant prevents."""
    table = _table()
    table.iloc[:4, 2] = np.nan          # C1 measured on half the tasks only
    means = np.nanmean(table.to_numpy(dtype=float), axis=0)
    assert np.all(np.isfinite(means))   # nothing looks wrong
    tau = means[1] - means[2]           # B minus C1, over DIFFERENT task sets
    assert np.isfinite(tau)
    with pytest.raises(ValueError):
        assert_primary_table_complete(table, [(c, TARGET) for c in CONDITIONS])


def test_finite_point_estimates():
    point = pd.Series({"tau|C1|target_first": 0.1, "tau|C2|target_first": np.nan})
    assert_finite_point_estimates(point, ["tau|C1|target_first"])
    with pytest.raises(ValueError, match="non-finite"):
        assert_finite_point_estimates(
            point, ["tau|C1|target_first", "tau|C2|target_first"])
    with pytest.raises(ValueError, match="non-finite"):
        assert_finite_point_estimates(point, ["tau|absent|target_first"])
