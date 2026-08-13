"""The output-cap safeguard must actually stop a run, and must never filter rows.

Pre-repair, `output_cap_report` had zero call sites, both declared thresholds had
zero consumers, and OUTPUT_CAP_DOMINATES was unreachable. These tests pin the
three triggers and the two prohibitions.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.output_budget import (TERMINATION_FIELDS, arm_gap, cap_verdict,
                                        termination_coverage, termination_report)

pytestmark = pytest.mark.cpu

FOCAL = "B"
REFS = ["S_SEMICOLON", "C_W3", "S_COMMA", "S_MINWORDS15", "C_L3", "S_MINWORDS12"]
ORDERS = ["target_first", "added_first"]
THRESHOLDS = dict(warn_share=0.05, stop_share=0.20, max_arm_gap=0.05)


def _scored(truncation: dict[str, float], n_per_cell: int = 24,
            tokens: dict[str, int] | None = None,
            missing_metadata: float = 0.0) -> pd.DataFrame:
    """Synthetic confirmatory scores with a controlled truncation share per arm."""
    rng = np.random.default_rng(11)
    rows = []
    for arm in [FOCAL, *REFS]:
        for order in ORDERS:
            share = truncation.get(arm, 0.0)
            n_trunc = int(round(share * n_per_cell))
            flags = [True] * n_trunc + [False] * (n_per_cell - n_trunc)
            for i, truncated in enumerate(flags):
                drop = rng.random() < missing_metadata
                rows.append({
                    "row_id": f"{arm}|{order}|{i}", "added_constraint": arm,
                    "order": order, "paraphrase_id": i % 2, "is_measured": True,
                    "fail": int(truncated),
                    "generated_token_count": None if drop else
                        (tokens or {}).get(arm, 60) + (120 if truncated else 0),
                    "ended_with_eos": None if drop else (not truncated),
                    "hit_max_new_tokens": None if drop else truncated,
                    "output_truncated": None if drop else truncated,
                    "stop_reason": None if drop else
                        ("max_new_tokens" if truncated else "eos"),
                })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- reporting
def test_report_covers_every_arm_and_order():
    scored = _scored({})
    report = termination_report(scored, ["added_constraint", "order"])
    assert len(report) == (1 + len(REFS)) * len(ORDERS)
    assert set(report["added_constraint"]) == {FOCAL, *REFS}
    assert (report["truncated_share"] == 0.0).all()
    assert (report["eos_share"] == 1.0).all()
    for col in ("mean_generated_tokens", "p90_generated_tokens",
                "max_generated_tokens", "n_with_metadata"):
        assert col in report.columns


def test_coverage_detects_absent_metadata():
    assert termination_coverage(_scored({}))["coverage"] == 1.0
    partial = termination_coverage(_scored({}, missing_metadata=0.5))["coverage"]
    assert 0.3 < partial < 0.7
    bare = pd.DataFrame([{"row_id": "x"}])
    assert termination_coverage(bare)["coverage"] == 0.0
    assert np.isnan(termination_coverage(pd.DataFrame())["coverage"])


# -------------------------------------------------------------------- verdicts
def test_balanced_low_truncation_fixture_passes():
    scored = _scored({arm: 0.02 for arm in [FOCAL, *REFS]})
    report = termination_report(scored, ["added_constraint", "order", "paraphrase_id"])
    gaps = arm_gap(termination_report(scored, ["added_constraint", "order"]),
                   "added_constraint", FOCAL, REFS)
    verdict = cap_verdict(report, gaps, coverage=termination_coverage(scored),
                          **THRESHOLDS)
    assert verdict["ok"], verdict["reasons"]
    assert verdict["coverage_ok"]
    assert verdict["worst_abs_arm_gap"] == pytest.approx(0.0, abs=1e-12)


def test_absolute_truncation_triggers_the_stop():
    """The declared rule: any reported cell above stop_share stops the run."""
    scored = _scored({arm: 0.30 for arm in [FOCAL, *REFS]})
    report = termination_report(scored, ["added_constraint", "order", "paraphrase_id"])
    gaps = arm_gap(termination_report(scored, ["added_constraint", "order"]),
                   "added_constraint", FOCAL, REFS)
    verdict = cap_verdict(report, gaps, coverage=termination_coverage(scored),
                          **THRESHOLDS)
    assert not verdict["ok"]
    assert any("stop share" in r for r in verdict["reasons"])
    assert len(verdict["cells_over_stop_share"]) > 0


def test_differential_truncation_triggers_the_stop_even_when_absolute_passes():
    """The case that biases tau: both arms under 0.20, but far apart.

    This is the scenario the review identified as able to reverse a result -- the
    long word-floor references censored more often than B -- and the absolute
    per-cell rule alone does not catch it.
    """
    scored = _scored({FOCAL: 0.02, "S_MINWORDS15": 0.18, "S_MINWORDS12": 0.15,
                      "S_SEMICOLON": 0.02, "C_W3": 0.02, "S_COMMA": 0.02,
                      "C_L3": 0.02})
    report = termination_report(scored, ["added_constraint", "order", "paraphrase_id"])
    assert (pd.to_numeric(report["truncated_share"]) <= 0.20).all()
    gaps = arm_gap(termination_report(scored, ["added_constraint", "order"]),
                   "added_constraint", FOCAL, REFS)
    verdict = cap_verdict(report, gaps, coverage=termination_coverage(scored),
                          **THRESHOLDS)
    assert not verdict["ok"]
    assert any("truncation gap" in r for r in verdict["reasons"])
    worst = verdict["gaps_over_tolerance"]
    assert set(worst["reference"]) == {"S_MINWORDS15", "S_MINWORDS12"}
    # The focal arm is the LESS truncated one, so measured reference failure is
    # inflated and tau is biased downward -- the masking direction.
    assert (worst["gap"] < 0).all()


def test_missing_metadata_cannot_be_reported_as_satisfied():
    """A cap gate on absent metadata reports 0.00 truncation. That must not pass."""
    scored = _scored({}, missing_metadata=1.0)
    report = termination_report(scored, ["added_constraint", "order"])
    gaps = arm_gap(report, "added_constraint", FOCAL, REFS)
    verdict = cap_verdict(report, gaps, coverage=termination_coverage(scored),
                          **THRESHOLDS)
    assert not verdict["ok"]
    assert not verdict["coverage_ok"]
    assert any("cannot be evaluated" in r for r in verdict["reasons"])


def test_warn_band_warns_without_stopping():
    scored = _scored({arm: 0.10 for arm in [FOCAL, *REFS]})
    report = termination_report(scored, ["added_constraint", "order"])
    gaps = arm_gap(report, "added_constraint", FOCAL, REFS)
    verdict = cap_verdict(report, gaps, coverage=termination_coverage(scored),
                          **THRESHOLDS)
    assert verdict["ok"]
    assert verdict["warnings"]


# ---------------------------------------------------------------- prohibitions
def test_reporting_never_drops_or_reweights_rows():
    """Post-treatment quantities may be described, never used to select."""
    scored = _scored({FOCAL: 0.25, "S_MINWORDS15": 0.02})
    report = termination_report(scored, ["added_constraint", "order"])
    assert int(report["n"].sum()) == len(scored)
    # every arm still present, including the heavily truncated one
    assert set(report["added_constraint"]) == {FOCAL, *REFS}
    counts = report.groupby("added_constraint")["n"].sum()
    assert counts.nunique() == 1


def test_termination_fields_are_the_declared_five():
    assert TERMINATION_FIELDS == ("generated_token_count", "ended_with_eos",
                                  "hit_max_new_tokens", "output_truncated",
                                  "stop_reason")
