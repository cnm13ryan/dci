"""Tests for the arbitration programme's seeding and estimators.

The seeding rule and the estimand definitions are the two places where a silent
error would corrupt every number in the programme without failing loudly, so
both are pinned here against hand-computed cases.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dci_exploratory import arbprogram as A


def load_harness():
    """Import the vLLM harness for its seed rule without importing vLLM."""
    path = ROOT / "vllm_backend" / "arbitration_vllm.py"
    spec = importlib.util.spec_from_file_location("arbitration_vllm", path)
    module = importlib.util.module_from_spec(spec)
    module.__dict__["MASTER_SEED"] = 20260812
    source = path.read_text()
    # The module reads sys.argv at import time; execute only the pieces that do
    # not, which is exactly the seed function and its constants.
    body = source.split("def scientific_seed", 1)[1]
    namespace = {"hashlib": __import__("hashlib"), "MASTER_SEED": 20260812,
                 "SEED_MODULUS": 2 ** 31 - 1}
    exec("def scientific_seed" + body.split("\n\n\ndef main", 1)[0], namespace)
    return namespace["scientific_seed"]


scientific_seed = load_harness()


# ------------------------------------------------------------------ seeding
def test_replicates_of_one_task_get_different_seeds():
    seeds = {scientific_seed("PLT01", r, "answer") for r in range(4)}
    assert len(seeds) == 4


def test_matched_conditions_share_a_seed():
    """Arm, background, order and budget are not inputs, so they cannot split it."""
    assert scientific_seed("PLT01", 0, "answer") == scientific_seed("PLT01", 0, "answer")


def test_phases_are_seeded_apart():
    assert scientific_seed("PLT01", 0, "think") != scientific_seed("PLT01", 0, "answer")


def test_seeds_are_in_range_and_stable():
    seed = scientific_seed("PLT07", 2, "think")
    assert 0 <= seed < 2 ** 31 - 1
    assert seed == scientific_seed("PLT07", 2, "think")


def test_different_tasks_get_different_seeds():
    seeds = {scientific_seed(f"PLT{i:02d}", 0, "answer") for i in range(1, 21)}
    assert len(seeds) == 20


# ---------------------------------------------------------------- estimators
def make_frame() -> pd.DataFrame:
    """Two tasks with hand-chosen A-failures, one replicate, one order."""
    rows = []
    plan = {
        # (task, background, arm): A_failure
        ("T1", A.AMPLIFIER, "B"): 1.0, ("T1", A.AMPLIFIER, "C_L3"): 0.0,
        ("T1", A.CONTROL, "B"): 0.0, ("T1", A.CONTROL, "C_L3"): 0.0,
        ("T2", A.AMPLIFIER, "B"): 0.0, ("T2", A.AMPLIFIER, "C_L3"): 0.0,
        ("T2", A.CONTROL, "B"): 1.0, ("T2", A.CONTROL, "C_L3"): 0.0,
    }
    for (task, background, arm), failure in plan.items():
        rows.append({"task_id": task, "background": background, "arm": arm,
                     "order": "QAC", "reasoning_budget": 0, "A_failure": failure,
                     "A_pass": 1 - failure, "Q_pass": 0,
                     "background_name": A.BACKGROUND_LABEL[background],
                     "arbitration_state": "target only" if failure == 0 else "neither"})
    return pd.DataFrame(rows)


def test_tau_is_the_paired_focal_minus_reference_difference():
    frame = make_frame()
    tau = A.tau(frame, background=A.AMPLIFIER, order="QAC", reasoning_budget=0)
    assert tau["T1"] == pytest.approx(1.0)
    assert tau["T2"] == pytest.approx(0.0)


def test_delta_is_amplifier_minus_control_within_task():
    frame = make_frame()
    delta = A.delta(frame, order="QAC", reasoning_budget=0)
    assert delta["T1"] == pytest.approx(1.0)   # 1.0 - 0.0
    assert delta["T2"] == pytest.approx(-1.0)  # 0.0 - 1.0
    assert delta.mean() == pytest.approx(0.0)


def test_gamma_is_the_change_in_delta_across_budgets():
    frame = make_frame()
    high = frame.copy()
    high["reasoning_budget"] = 4096
    high.loc[high["background"] == A.AMPLIFIER, "A_failure"] = 0.0
    both = pd.concat([frame, high], ignore_index=True)
    gamma = A.gamma(both, order="QAC", low=0, high=4096)
    # at b=4096 the amplifier arm no longer fails, so Delta becomes 0 - control
    assert gamma["T1"] == pytest.approx(-1.0)


def test_arbitration_states_are_a_partition():
    frame = make_frame()
    states = A.arbitration(frame, order="QAC", reasoning_budget=0)
    total = sum(series.reindex(["T1", "T2"]).fillna(0) for series in states.values())
    assert np.allclose(total.to_numpy(), 1.0)


def test_survival_is_target_only_minus_focal_only():
    frame = make_frame()
    survival = A.survival(frame, order="QAC", reasoning_budget=0)
    states = A.arbitration(frame, order="QAC", reasoning_budget=0)
    expected = states["target only"] - states["focal only"]
    assert survival.round(9).equals(expected.dropna().round(9))


# ---------------------------------------------------------------- bootstrap
def test_bootstrap_is_deterministic_in_its_key_and_not_in_call_order():
    tasks = [f"T{i}" for i in range(20)]
    series = pd.Series(np.linspace(0, 1, 20), index=tasks)
    first = A.Clusters(tasks, key="alpha", draws=500).interval(series)
    A.Clusters(tasks, key="beta", draws=500).interval(series)
    again = A.Clusters(tasks, key="alpha", draws=500).interval(series)
    assert first == again


def test_bootstrap_resamples_tasks_not_generations():
    tasks = [f"T{i}" for i in range(20)]
    clusters = A.Clusters(tasks, key="shape", draws=64)
    assert clusters.index.shape == (64, 20)
    assert clusters.index.max() < 20


def test_interval_brackets_the_point_estimate():
    tasks = [f"T{i}" for i in range(20)]
    series = pd.Series(np.linspace(-1, 1, 20), index=tasks)
    estimate, lo, hi = A.Clusters(tasks, key="bracket", draws=2000).interval(series)
    assert lo <= estimate <= hi


def test_scratch_regex_matches_continued_scratch_work_only():
    assert A.SCRATCH.search("Wait, that is five sentences.")
    assert A.SCRATCH.search("Let me count the words again.")
    assert not A.SCRATCH.search("A corkscrew removes a cork by twisting.")
