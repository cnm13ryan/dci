"""A pooled rate must equal the rate over the rows it claims to describe.

Defect: `headline()` weighted BOTH arm rates by `part["final_answers"]`, the
background's combined answered-row count. That silently assumes the two arms
answered at the same rate. A background with 40 focal answers and 1 reference
answer therefore received the same focal weight as one with the reverse pattern
whenever their totals matched, so the published "A-fail focal" and "A-fail ref"
stopped being the pooled answered-row rates the report describes.

Final-answer missingness differing by arm is not hypothetical: it is exactly
what happens when a checkpoint struggles in one arm, and the report has a whole
`missingness()` section devoted to it.

The invariant asserted here is the one the review asked for: each published
pooled rate equals the rate computed directly from the corresponding rows.

Classification: denominator/aggregation error.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_actual_results as R  # noqa: E402


def cell(model: str, background: str, *, focal_n: int, focal_fail: int,
         ref_n: int, ref_fail: int, load: int = 3,
         backend: str = "transformers", identification: str = "IDENTIFIED",
         estimable: bool = True) -> dict:
    """One per-cell row with independently controllable arm denominators.

    `identification`/`estimable` default to an identified cell so the
    denominator assertions below isolate the weighting, not the pooling gate.
    """
    return {
        "identification": identification,
        "identification_reason": "",
        "estimable": estimable,
        "focal_uptake": 1.0, "reference_uptake": 1.0, "cap_hit_rate": 0.0,
        "model": model, "model_id": f"org/{model}", "backend": backend,
        "load": load, "background": background, "variant": background,
        "requested": (focal_n + ref_n) * 2,
        "final_answers": focal_n + ref_n,
        "final_answers_focal": focal_n,
        "final_answers_reference": ref_n,
        "no_final": 0, "technical_failures": 0, "not_generated": 0,
        "A_fail_focal": focal_fail / focal_n if focal_n else float("nan"),
        "A_fail_reference": ref_fail / ref_n if ref_n else float("nan"),
        "tau": 0.0, "lo": 0.0, "hi": 0.0, "n_tasks": 20,
        "joint_focal": 0.0,
    }


class TestPooledRateEqualsRowLevelRate:
    def test_asymmetric_missingness_pools_correctly(self) -> None:
        """The reviewed case: arms with very different answered counts."""
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=40, focal_fail=20,
                 ref_n=1, ref_fail=1),
            cell("M", "+ one bracket pair", focal_n=1, focal_fail=0,
                 ref_n=40, ref_fail=4),
        ])
        table = R.headline(cells)
        row = table.iloc[0]
        # Direct row-level rates: focal 20+0 failures over 40+1 answers.
        assert row["A-fail focal"] == pytest.approx(20 / 41)
        assert row["A-fail ref"] == pytest.approx(5 / 41)

    def test_equal_denominators_are_unchanged(self) -> None:
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=40, focal_fail=10,
                 ref_n=40, ref_fail=20),
            cell("M", "+ one bracket pair", focal_n=40, focal_fail=30,
                 ref_n=40, ref_fail=0),
        ])
        table = R.headline(cells)
        row = table.iloc[0]
        assert row["A-fail focal"] == pytest.approx(40 / 80)
        assert row["A-fail ref"] == pytest.approx(20 / 80)

    def test_the_combined_weight_would_have_been_wrong(self) -> None:
        """Pins the defect: the old weighting gives a different number."""
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=40, focal_fail=40,
                 ref_n=1, ref_fail=0),
            cell("M", "+ one bracket pair", focal_n=1, focal_fail=0,
                 ref_n=40, ref_fail=0),
        ])
        combined = cells["final_answers"]
        old = float(np.average(cells["A_fail_focal"], weights=combined))
        new = R.headline(cells).iloc[0]["A-fail focal"]
        assert new == pytest.approx(40 / 41)
        assert old != pytest.approx(new), "fixture no longer separates the two"


class TestDegenerateDenominators:
    def test_arm_with_no_answers_is_dropped_not_counted_as_zero(self) -> None:
        """A cell that produced no answers in an arm carries no information
        about that arm; `fillna(0)` used to enter it as a zero failure rate."""
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=10, focal_fail=10,
                 ref_n=10, ref_fail=10),
            cell("M", "+ one bracket pair", focal_n=0, focal_fail=0,
                 ref_n=10, ref_fail=0),
        ])
        table = R.headline(cells)
        # Focal saw only the first cell: 10/10.
        assert table.iloc[0]["A-fail focal"] == pytest.approx(1.0)

    def test_no_answers_at_all_is_nan_not_zero(self) -> None:
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=0, focal_fail=0,
                 ref_n=0, ref_fail=0)])
        table = R.headline(cells)
        assert np.isnan(table.iloc[0]["A-fail focal"])
        assert np.isnan(table.iloc[0]["A-fail ref"])


class TestPerArmCountsArePublished:
    def test_headline_reports_each_arm_denominator(self) -> None:
        cells = pd.DataFrame([
            cell("M", "+ one semicolon", focal_n=30, focal_fail=3,
                 ref_n=7, ref_fail=1)])
        row = R.headline(cells).iloc[0]
        assert row["Final answers focal"] == 30
        assert row["Final answers ref"] == 7
