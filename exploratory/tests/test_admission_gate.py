"""Only a positively valid mode may enter the scientific matrix.

Defect: `admission()` rejected `MODE_FAILED` and let everything else through.
`MODE_SUSPECT` is not a soft warning — Stage B/C raises it for, among others:

    * an empty final answer;
    * a reasoning trace appearing in the native non-thinking mode;
    * a trace opened but never closed;
    * the thinking mode never opening a reasoning block;
    * WEIGHTS SUSPECT: not one trivial weight-integrity question answered
      correctly, which is what a partially initialised load looks like.

Marker leak and control-token residue were separately rejected, so those two
problems were caught. Every other problem above was admitted.

The NO_THINKING branch is where this bites hardest: it returns `admitted: True`
immediately after the MODE_FAILED check, with no later gate that could catch a
suspect verdict. The NATURAL_REASONING branch still has to pass Stage E, which
is why the one suspect cell in the committed matrix (Qwen3.5-4B natural) happened
not to be admitted — luck, not design.

Classification: validity-gate failure and execution-condition (E) violation. A
cell built on a partially initialised load is not a measurement of the model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xm_matrix  # noqa: E402
from crossmodel.adapters import REGISTRY  # noqa: E402
from crossmodel.contract import ReasoningMode  # noqa: E402

QWEN = REGISTRY["Qwen/Qwen3.5-4B"]
NO_THINKING = ReasoningMode.NO_THINKING
NATURAL = ReasoningMode.NATURAL_REASONING


def validate_record(mode: str, status: str, **verdict) -> dict:
    return {"load_status": "LOAD_VALID",
            "modes": {mode: {"status": status, **verdict}}}


def stage_e(validated: bool = True) -> dict:
    return {"stage_e": {"validated": validated, "reasoning_cap_hits": 0,
                        "empty_answers": 0}}


class TestSuspectIsNeverAdmitted:
    def test_suspect_non_thinking_is_refused(self) -> None:
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_SUSPECT",
                            problems=["WEIGHTS SUSPECT — not one trivial "
                                      "question was answered correctly"]),
            stage_e())
        assert result["admitted"] is False
        assert "MODE_SUSPECT" in result["reason"] or "suspect" in result["reason"]

    def test_suspect_natural_reasoning_is_refused(self) -> None:
        result = xm_matrix.admission(
            QWEN, NATURAL,
            validate_record(NATURAL, "MODE_SUSPECT",
                            problems=["2 trace(s) opened but never closed"]),
            stage_e())
        assert result["admitted"] is False

    def test_the_reason_names_the_problems(self) -> None:
        """A refusal has to be diagnosable without opening the artefact."""
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_SUSPECT",
                            problems=["empty final answer"]),
            stage_e())
        assert "empty final answer" in result["reason"]

    @pytest.mark.parametrize("problem", [
        "empty final answer",
        "a reasoning trace appeared in the non-thinking mode",
        "3 trace(s) opened but never closed",
        "the thinking mode never opened a reasoning block",
        "WEIGHTS SUSPECT — not one trivial question was answered correctly",
    ])
    def test_every_stage_bc_problem_blocks_admission(self, problem: str) -> None:
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_SUSPECT", problems=[problem]),
            stage_e())
        assert result["admitted"] is False, f"{problem!r} was admitted"


class TestValidStillAdmitted:
    def test_valid_non_thinking_is_admitted(self) -> None:
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_VALID"), stage_e())
        assert result["admitted"] is True

    def test_valid_natural_with_stage_e_is_admitted(self) -> None:
        result = xm_matrix.admission(
            QWEN, NATURAL, validate_record(NATURAL, "MODE_VALID"), stage_e())
        assert result["admitted"] is True

    def test_valid_natural_without_stage_e_is_refused(self) -> None:
        result = xm_matrix.admission(
            QWEN, NATURAL, validate_record(NATURAL, "MODE_VALID"),
            stage_e(validated=False))
        assert result["admitted"] is False


class TestExistingRefusalsSurvive:
    def test_failed_is_still_refused(self) -> None:
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_FAILED", error="boom"), stage_e())
        assert result["admitted"] is False

    def test_marker_leak_is_still_refused(self) -> None:
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_VALID",
                            marker_leak_into_answer=True), stage_e())
        assert result["admitted"] is False

    def test_unknown_status_is_refused(self) -> None:
        """Fail closed on a verdict this code has never seen."""
        result = xm_matrix.admission(
            QWEN, NO_THINKING,
            validate_record(NO_THINKING, "MODE_SOMETHING_NEW"), stage_e())
        assert result["admitted"] is False

    def test_missing_validation_is_refused(self) -> None:
        result = xm_matrix.admission(QWEN, NO_THINKING, None, stage_e())
        assert result["admitted"] is False
