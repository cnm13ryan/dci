"""The advertised tail share must be the share actually removed, per arm.

Two defects in `long_trace_sensitivity`:

  * the removal count was `int(share * len(natural) / 4)` — a denominator of 40
    unrelated to the 80-row cell being trimmed — so "5%" removed 2.5% and "10%"
    removed 5%;
  * the drop was applied to the pooled background cell. The estimator is a
    paired focal-minus-reference contrast and focal traces run systematically
    longer, so the pooled drop removed focal rows almost exclusively, leaving
    the two arms describing different task sets.

Classification: denominator/aggregation error compounded by a pairing error.
Descriptive sensitivity output only — no headline estimate depends on it — but
it was published as a robustness claim.
"""
from __future__ import annotations

import sys
from pathlib import Path

EXPLORATORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPLORATORY))

import natural_analysis  # noqa: E402
from tests import gridfixtures  # noqa: E402

FOCAL, REFERENCE = gridfixtures.FOCAL, gridfixtures.REFERENCE


def test_labelled_share_is_the_share_removed() -> None:
    """Each background cell holds 80 rows: 5% is 4 rows, 10% is 8."""
    table = natural_analysis.long_trace_sensitivity(gridfixtures.natural_frame())
    for label, removed in (("drop longest 5%", 4), ("drop longest 10%", 8)):
        kept = set(table[table["exclusion"] == label]["rows_kept"])
        assert kept == {80 - removed}, (
            f"{label!r} kept {sorted(kept)}, expected {80 - removed}")


def test_each_arm_loses_the_same_rows() -> None:
    """The pooled-drop defect: with focal traces uniformly longer, the old code
    removed focal rows only. Both arms must be trimmed equally."""
    table = natural_analysis.long_trace_sensitivity(gridfixtures.natural_frame())
    for _, row in table.iterrows():
        assert row["rows_kept_focal"] == row["rows_kept_reference"], (
            f"{row['exclusion']!r} left {row['rows_kept_focal']} focal vs "
            f"{row['rows_kept_reference']} reference rows")


def test_pooled_drop_would_have_been_arm_correlated() -> None:
    """Pins the defect itself, so a regression is detectable rather than
    merely absent: on this frame the longest 4 rows are all focal."""
    frame = gridfixtures.natural_frame()
    cell = frame[frame["variant"] == gridfixtures.SEMICOLON]
    longest_four = cell.sort_values("reasoning_tokens").iloc[-4:]
    assert set(longest_four["arm"]) == {FOCAL}


def test_per_arm_drop_removes_the_requested_count() -> None:
    frame = gridfixtures.natural_frame()
    cell = frame[frame["variant"] == gridfixtures.SEMICOLON]
    kept = natural_analysis.drop_longest_per_arm(cell, share=0.05)
    assert (kept["arm"] == FOCAL).sum() == 38
    assert (kept["arm"] == REFERENCE).sum() == 38


def test_task_loss_is_reported_not_hidden() -> None:
    """A length-based exclusion can drop a whole task when both replicates sit
    in the tail. That is a real property of the analysis; it must be visible."""
    table = natural_analysis.long_trace_sensitivity(gridfixtures.natural_frame())
    assert "n_tasks" in table.columns
    assert set(table[table["exclusion"] == "all rows"]["n_tasks"]) == {20}


def test_all_rows_row_keeps_everything() -> None:
    table = natural_analysis.long_trace_sensitivity(gridfixtures.natural_frame())
    assert set(table[table["exclusion"] == "all rows"]["rows_kept"]) == {80}
