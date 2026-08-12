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
