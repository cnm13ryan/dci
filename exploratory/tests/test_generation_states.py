"""An apparatus failure must never become a behavioural outcome.

Defect: `score()` began with `frame["raw_final_answer"].fillna("")`. A row the
harness had already marked `technical_failure=True` — an empty generation, a
decoding failure, a backend exception — therefore reached the verifiers as the
empty string. Every verifier returns `binary_pass=0` on it, so the row was
scored `A_pass=0`, `A_failure=1.0`, classified into the "neither" arbitration
state, and included in tau, delta, gamma and the arbitration summaries. The
validity table reported the row as technical while the estimates counted it as
target failure.

The three states the framework requires are kept distinct here:

  A. VALID_ANSWER      a final answer exists; the verifiers decide the outcome.
  B. NO_FINAL_ANSWER   the run was valid but the model produced no acceptable
                       final answer. This is model behaviour, so it is SCORED
                       (an empty answer does not satisfy "exactly four
                       sentences") rather than dropped — excluding it would
                       condition on a treatment-affected outcome — but it is
                       labelled so the sensitivity is computable.
  C. TECHNICAL_FAILURE verified apparatus failure. Never a behavioural outcome:
                       the pass columns are NaN and the row leaves every
                       behavioural estimand.

Classification: technical-failure classification error, causing a denominator
error in every downstream estimand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dci_exploratory import arbprogram as A  # noqa: E402

FOUR = "Alpha beta. Gamma delta epsilon. Zeta eta theta iota. Kappa lambda mu nu xi."
ONE = "Alpha beta gamma delta epsilon zeta eta theta."


def row(task: str, arm: str, answer, *, technical: bool = False,
        background: str = A.AMPLIFIER, replicate: int = 0) -> dict:
    return {
        "row_id": f"{task}-{arm}-{background}-{replicate}-{int(technical)}",
        "task_id": task,
        "arm": arm,
        "background": background,
        "measured": "A",
        "order": "QAC",
        "reasoning_budget": 0,
        "raw_final_answer": answer,
        "technical_failure": technical,
        "replicate": replicate,
    }


def scored(rows):
    return A.score(rows)


class TestTechnicalFailuresLeaveTheEstimands:
    def test_technical_failure_is_not_scored_as_target_failure(self) -> None:
        frame = scored([row("PLT01", "B", None, technical=True)])
        assert np.isnan(frame["A_pass"].iloc[0]), "a backend failure was scored"
        assert np.isnan(frame["A_failure"].iloc[0])

    def test_technical_failure_is_not_an_arbitration_state(self) -> None:
        frame = scored([row("PLT01", "B", "", technical=True)])
        assert frame["arbitration_state"].iloc[0] not in A.STATES, (
            "an apparatus failure was classified into a behavioural state")

    def test_technical_failure_is_labelled(self) -> None:
        frame = scored([row("PLT01", "B", None, technical=True)])
        assert frame["generation_state"].iloc[0] == A.TECHNICAL_FAILURE

    def test_technical_rows_do_not_move_tau(self) -> None:
        """The estimand computed with and without an added apparatus failure
        must be identical."""
        clean = [row("PLT01", "B", ONE), row("PLT01", "C_L3", FOUR),
                 row("PLT02", "B", FOUR), row("PLT02", "C_L3", FOUR)]
        polluted = clean + [row("PLT01", "B", None, technical=True, replicate=1),
                            row("PLT02", "C_L3", "", technical=True, replicate=1)]
        common = dict(background=A.AMPLIFIER, order="QAC", reasoning_budget=0)
        before = A.tau(scored(clean), **common)
        after = A.tau(scored(polluted), **common)
        pd.testing.assert_series_equal(before, after)

    def test_technical_rows_do_not_move_the_arbitration_summaries(self) -> None:
        """The four state probabilities partition the behavioural rows. A
        technical row in the denominator counted as a miss for every state, so
        one valid 'both' answer beside one apparatus failure read P(both)=0.5."""
        clean = [row("PLT01", "B", FOUR), row("PLT01", "C_L3", FOUR),
                 row("PLT02", "B", ONE), row("PLT02", "C_L3", FOUR)]
        polluted = clean + [row("PLT01", "B", None, technical=True, replicate=1),
                            row("PLT02", "B", "", technical=True, replicate=1)]
        common = dict(background=A.AMPLIFIER, order="QAC", reasoning_budget=0)
        before = A.arbitration(scored(clean), **common)
        after = A.arbitration(scored(polluted), **common)
        for state in A.STATES:
            pd.testing.assert_series_equal(before[state], after[state])
        assert sum(after[state]["PLT01"] for state in A.STATES) == 1.0
        pd.testing.assert_series_equal(A.survival(scored(clean), **common),
                                       A.survival(scored(polluted), **common))


    def test_every_printed_arbitration_view_reads_behavioural_rows(self) -> None:
        """The crosstabs printed beside the bootstrap table must share its
        denominator, or one report shows two sets of probabilities for one run
        (Codex on PR #37)."""
        for script in ("arb_exp1.py", "arb_exp2.py", "arb_exp3.py",
                       "mfr_focal_calibration.py", "mfr_figures.py"):
            text = (ROOT / script).read_text()
            reads_states = text.count('["arbitration_state"]')
            assert reads_states, script
            assert text.count("A.behavioural(") >= reads_states, (
                f"{script} reads arbitration_state without A.behavioural()")

    def test_a_task_lost_to_technical_failures_keeps_the_interval_finite(self) -> None:
        """A task whose focal rows are all technical leaves the per-task series.
        A bootstrap draw of only such tasks has no mean, and one such draw used
        to make both bounds NaN (Codex on PR #37)."""
        rows = [row("PLT01", "B", FOUR), row("PLT01", "C_L3", FOUR)]
        for task in ("PLT02", "PLT03", "PLT04", "PLT05"):
            rows += [row(task, "B", None, technical=True),
                     row(task, "C_L3", FOUR)]
        frame = scored(rows)
        both = A.arbitration(frame, background=A.AMPLIFIER, order="QAC",
                             reasoning_budget=0)["both"]
        assert list(both.index) == ["PLT01"]
        clusters = A.Clusters(sorted(frame["task_id"].unique()), "finite", draws=500)
        estimate, lo, hi = clusters.interval(both)
        assert (estimate, lo, hi) == (1.0, 1.0, 1.0)

    def test_a_complete_series_keeps_its_interval_exactly(self) -> None:
        tasks = [f"PLT{i:02d}" for i in range(1, 21)]
        series = pd.Series(np.linspace(0.0, 1.0, 20), index=tasks)
        clusters = A.Clusters(tasks, "unchanged", draws=2000)
        means = np.nanmean(series.to_numpy()[clusters.index], axis=1)
        assert clusters.interval(series) == (
            float(series.mean()), float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)))


class TestModelCausedNonAnswers:
    def test_empty_answer_without_technical_flag_is_still_scored(self) -> None:
        """Category B is model behaviour. Dropping it would condition on a
        treatment-affected outcome, so it stays in the estimand."""
        frame = scored([row("PLT01", "B", "")])
        assert frame["generation_state"].iloc[0] == A.NO_FINAL_ANSWER
        assert frame["A_pass"].iloc[0] == 0
        assert frame["A_failure"].iloc[0] == 1.0

    def test_whitespace_only_answer_is_a_non_answer(self) -> None:
        frame = scored([row("PLT01", "B", "   \n\t ")])
        assert frame["generation_state"].iloc[0] == A.NO_FINAL_ANSWER

    def test_missing_answer_without_technical_flag_is_a_non_answer(self) -> None:
        frame = scored([row("PLT01", "B", None)])
        assert frame["generation_state"].iloc[0] == A.NO_FINAL_ANSWER
        assert frame["A_failure"].iloc[0] == 1.0


class TestValidAnswers:
    def test_valid_answer_is_labelled_and_scored(self) -> None:
        frame = scored([row("PLT01", "B", FOUR)])
        assert frame["generation_state"].iloc[0] == A.VALID_ANSWER
        assert frame["A_pass"].iloc[0] == 1

    def test_valid_answer_failing_the_target_is_ordinary_failure(self) -> None:
        frame = scored([row("PLT01", "B", ONE)])
        assert frame["generation_state"].iloc[0] == A.VALID_ANSWER
        assert frame["A_failure"].iloc[0] == 1.0

    def test_states_partition_every_row(self) -> None:
        frame = scored([row("PLT01", "B", FOUR),
                        row("PLT02", "B", ""),
                        row("PLT03", "B", None, technical=True)])
        assert set(frame["generation_state"]) == {
            A.VALID_ANSWER, A.NO_FINAL_ANSWER, A.TECHNICAL_FAILURE}
        assert frame["generation_state"].notna().all()
