"""Every stored row carries the same keys, whatever happened to it.

The pre-consolidation code had three record constructors in `vllm_tp2.py` alone
and they disagreed: `unattempted()` emitted `not_generated_reason` and omitted
`channel_valid`, so a deadline-stopped run produced rows the ingest could not
distinguish from generated ones. Four more schemas existed across the other
scripts. This test makes the schema one fact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import records                              # noqa: E402
from vllm_backend.contract import (NON_BEHAVIOURAL, ROW_KEYS,  # noqa: E402
                                   GenerationRequest, GenerationResult,
                                   Outcome)
from vllm_backend.registry import get                          # noqa: E402


class FakeCompletion:
    """The only shape the record builders touch on a vLLM completion."""

    def __init__(self, text: str, token_ids=(1, 2, 3), finish_reason="stop",
                 stop_reason=None):
        self.text = text
        self.token_ids = list(token_ids)
        self.finish_reason = finish_reason
        self.stop_reason = stop_reason


@pytest.fixture
def request_() -> GenerationRequest:
    return GenerationRequest(
        row_id="r1", user_prompt="p", system_message="s",
        scientific_seed=11, answer_seed=22,
        identity={"task_id": "t1", "arm": "focal", "replicate": 0})


@pytest.fixture
def card():
    return get("Qwen/Qwen3.5-4B")


def _all_constructors(request_, card) -> dict[str, GenerationResult]:
    completion = FakeCompletion("<think>because</think>Paris")
    return {
        "generated": records.generated(
            request_, "PROMPT", completion, "because", "Paris",
            card.think_close),
        "spliced": records.spliced(
            request_, "PROMPT", "because", 3, True,
            FakeCompletion("Paris")),
        "not_generated": records.not_generated(request_, "PROMPT", "deadline"),
        "failed": records.failed(request_, "PROMPT", RuntimeError("boom")),
        "blocked": records.blocked(
            [request_], Outcome.BACKEND_UNSUPPORTED.value, "no arch")[0],
    }


def test_every_constructor_emits_the_same_key_set(request_, card) -> None:
    for name, result in _all_constructors(request_, card).items():
        keys = set(result.as_row()) - set(request_.identity)
        assert keys == set(ROW_KEYS), (
            f"{name}() emitted a different schema; missing "
            f"{sorted(set(ROW_KEYS) - keys)}, extra {sorted(keys - set(ROW_KEYS))}")


def test_identity_is_merged_and_never_nested(request_, card) -> None:
    row = _all_constructors(request_, card)["generated"]
    assert row.as_row()["task_id"] == "t1"
    assert "identity" not in row.as_row()


def test_schema_fields_win_over_identity_collisions(request_) -> None:
    """A stray identity key must never silently redefine an outcome field."""
    colliding = GenerationRequest(row_id="r1", user_prompt="p",
                                  identity={"outcome": "SNEAKY"})
    row = records.not_generated(colliding, "P", "why").as_row()
    assert row["outcome"] == Outcome.NOT_GENERATED.value


def test_every_row_is_json_serialisable(request_, card) -> None:
    for name, result in _all_constructors(request_, card).items():
        json.dumps(result.as_row())          # must not raise


class TestOutcomes:
    def test_generated_row_is_behavioural(self, request_, card) -> None:
        result = records.generated(
            request_, "P", FakeCompletion("<think>x</think>Paris"),
            "x", "Paris", card.think_close)
        assert result.outcome == Outcome.OK.value
        assert result.is_behavioural

    def test_unsegmentable_output_is_channel_invalid(self, request_, card) -> None:
        """Text with no delimiter and no answer must not be promoted to a final
        answer — that would manufacture a datum out of a parser failure."""
        result = records.generated(
            request_, "P", FakeCompletion("rambling scratchpad"),
            "", "", card.think_close)
        assert result.outcome == Outcome.CHANNEL_INVALID.value
        assert not result.is_behavioural
        assert not result.channel_valid

    def test_not_generated_is_missing_not_zero(self, request_) -> None:
        result = records.not_generated(request_, "P", "deadline exceeded")
        assert result.outcome == Outcome.NOT_GENERATED.value
        assert not result.is_behavioural
        assert "deadline" in result.outcome_detail

    def test_blocked_run_yields_one_row_per_design_row(self, request_) -> None:
        rows = records.blocked([request_, request_],
                               Outcome.CAPACITY_EXCEEDED.value, "OOM at load")
        assert len(rows) == 2
        assert all(r.outcome == Outcome.CAPACITY_EXCEEDED.value for r in rows)
        assert all(not r.is_behavioural for r in rows)

    def test_technical_failure_carries_the_exception(self, request_) -> None:
        result = records.failed(request_, "P", ValueError("bad shape"))
        assert result.outcome == Outcome.TECHNICAL_FAILURE.value
        assert "ValueError" in result.outcome_detail

    def test_all_named_failure_outcomes_are_non_behavioural(self) -> None:
        for outcome in (Outcome.BACKEND_UNSUPPORTED, Outcome.CAPACITY_EXCEEDED,
                        Outcome.TECHNICAL_FAILURE, Outcome.NOT_GENERATED,
                        Outcome.CHANNEL_INVALID):
            assert outcome in NON_BEHAVIOURAL


class TestCapAndTruncationSemantics:
    """The ceiling binds only when the budget was consumed WITHOUT closing."""

    def test_length_stop_without_closing_is_a_cap_hit(self, request_, card) -> None:
        result = records.generated(
            request_, "P", FakeCompletion("<think>on and on",
                                          finish_reason="length"),
            "on and on", "", card.think_close)
        assert result.reasoning_cap_hit
        assert result.answer_truncated

    def test_length_stop_after_closing_is_truncation_not_a_cap_hit(
            self, request_, card) -> None:
        result = records.generated(
            request_, "P",
            FakeCompletion("<think>x</think>a long answer",
                           finish_reason="length"),
            "x", "a long answer", card.think_close)
        assert not result.reasoning_cap_hit
        assert result.answer_truncated

    def test_spliced_cap_hit_follows_the_close(self, request_) -> None:
        closed = records.spliced(request_, "P", "x", 3, True,
                                 FakeCompletion("Paris"))
        open_ = records.spliced(request_, "P", "x", 3, False,
                                FakeCompletion("Paris"))
        assert not closed.reasoning_cap_hit
        assert open_.reasoning_cap_hit


def test_summarise_counts_only_behavioural_rows(request_, card) -> None:
    rows = [
        records.generated(request_, "P", FakeCompletion("<think>x</think>A"),
                          "x", "A", card.think_close),
        records.not_generated(request_, "P", "deadline"),
        records.blocked([request_], Outcome.CAPACITY_EXCEEDED.value, "OOM")[0],
    ]
    summary = records.summarise(rows)
    assert summary["rows"] == 3
    assert summary["behavioural_rows"] == 1
    assert summary["by_outcome"][Outcome.NOT_GENERATED.value] == 1
    assert summary["by_outcome"][Outcome.CAPACITY_EXCEEDED.value] == 1
