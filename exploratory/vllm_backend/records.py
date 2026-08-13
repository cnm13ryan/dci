"""Every stored row is built here, by one function per outcome.

Stdlib only. The old code had three record constructors in `vllm_tp2.py` alone
that disagreed on their key sets, plus four more schemas across the other
scripts. `contract.ROW_KEYS` plus these constructors make the schema a single
testable fact.
"""
from __future__ import annotations

from typing import Any

from vllm_backend.contract import GenerationRequest, GenerationResult, Outcome


def _token_count(tokenizer, text: str) -> int:
    if not text or tokenizer is None:
        return 0
    try:
        return len(tokenizer.encode(text, add_special_tokens=False))
    except Exception:
        return 0


def generated(request: GenerationRequest, rendered_prompt: str, completion,
              reasoning: str, answer: str, think_close: str,
              tokenizer=None) -> GenerationResult:
    """A row that was actually generated."""
    text = completion.text
    emitted = bool(reasoning.strip())
    # Text carrying no reasoning delimiter at all could not be segmented into
    # the two channels the contract requires. Recorded as CHANNEL_INVALID so
    # the cell is not read as a model that simply answered badly.
    channel_valid = bool(emitted or answer.strip())
    closed = emitted and bool(answer.strip() or (think_close and think_close in text))
    finish_reason = completion.finish_reason or ""
    return GenerationResult(
        row_id=request.row_id,
        outcome=(Outcome.OK.value if channel_valid
                 else Outcome.CHANNEL_INVALID.value),
        outcome_detail=("" if channel_valid else
                        "generation carried no reasoning delimiter and no "
                        "answer; not promotable to a final answer"),
        rendered_prompt=rendered_prompt,
        raw_generation=text,
        reasoning_text=reasoning,
        final_answer=answer,
        reasoning_tokens=_token_count(tokenizer, reasoning),
        final_answer_tokens=_token_count(tokenizer, answer),
        total_generated_tokens=len(completion.token_ids),
        finish_reason=finish_reason,
        stop_reason=str(getattr(completion, "stop_reason", "")),
        reasoning_emitted=emitted,
        channel_valid=channel_valid,
        reasoning_closed=closed,
        # The ceiling binds only when the whole budget was consumed WITHOUT the
        # model ever closing its reasoning.
        reasoning_cap_hit=(finish_reason == "length" and not closed),
        answer_truncated=finish_reason == "length",
        seed_reasoning=request.scientific_seed,
        seed_answer=request.answer_seed,
        identity=dict(request.identity),
    )


def spliced(request: GenerationRequest, rendered_prompt: str,
            reasoning_text: str, reasoning_tokens: int, reasoning_closed: bool,
            answer_completion, tokenizer=None) -> GenerationResult:
    """A row from the two-phase splice strategy.

    Phase 1 thinks under the assigned budget; phase 2 answers under a budget
    identical in every treatment. The two channels are never concatenated: the
    reasoning channel is NEVER part of the response.
    """
    finish_reason = answer_completion.finish_reason or ""
    answer = answer_completion.text.strip()
    channel_valid = bool(reasoning_text.strip() or answer)
    return GenerationResult(
        row_id=request.row_id,
        outcome=(Outcome.OK.value if channel_valid
                 else Outcome.CHANNEL_INVALID.value),
        rendered_prompt=rendered_prompt,
        raw_generation=reasoning_text,
        reasoning_text=reasoning_text,
        final_answer=answer,
        reasoning_tokens=reasoning_tokens,
        final_answer_tokens=len(answer_completion.token_ids),
        total_generated_tokens=reasoning_tokens + len(answer_completion.token_ids),
        finish_reason=finish_reason,
        stop_reason=str(getattr(answer_completion, "stop_reason", "")),
        reasoning_emitted=bool(reasoning_text.strip()),
        channel_valid=channel_valid,
        reasoning_closed=reasoning_closed,
        reasoning_cap_hit=not reasoning_closed,
        answer_truncated=finish_reason == "length",
        seed_reasoning=request.scientific_seed,
        seed_answer=request.answer_seed,
        identity=dict(request.identity),
    )


def not_generated(request: GenerationRequest, rendered_prompt: str,
                  why: str) -> GenerationResult:
    """A row the run never asked for. Missing, not failed, not zero."""
    return GenerationResult(
        row_id=request.row_id,
        outcome=Outcome.NOT_GENERATED.value,
        outcome_detail=why,
        rendered_prompt=rendered_prompt,
        seed_reasoning=request.scientific_seed,
        seed_answer=request.answer_seed,
        identity=dict(request.identity),
    )


def failed(request: GenerationRequest, rendered_prompt: str,
           error: BaseException,
           outcome: str = Outcome.TECHNICAL_FAILURE.value) -> GenerationResult:
    """A row whose generation raised."""
    return GenerationResult(
        row_id=request.row_id,
        outcome=outcome,
        outcome_detail=f"{type(error).__name__}: {error}"[:500],
        rendered_prompt=rendered_prompt,
        seed_reasoning=request.scientific_seed,
        seed_answer=request.answer_seed,
        identity=dict(request.identity),
    )


def blocked(requests: list[GenerationRequest], outcome: str,
            detail: str) -> list[GenerationResult]:
    """Every row of a run the backend could not execute at all.

    A whole-run block (BACKEND_UNSUPPORTED / CAPACITY_EXCEEDED) still produces
    one row per design row, so the cell is explicitly missing rather than absent
    from the file.
    """
    return [GenerationResult(
        row_id=r.row_id, outcome=outcome, outcome_detail=detail,
        seed_reasoning=r.scientific_seed, seed_answer=r.answer_seed,
        identity=dict(r.identity)) for r in requests]


def summarise(results: list[GenerationResult]) -> dict[str, Any]:
    """Run-level counts, computed one way."""
    by_outcome: dict[str, int] = {}
    for result in results:
        by_outcome[result.outcome] = by_outcome.get(result.outcome, 0) + 1
    behavioural = [r for r in results if r.is_behavioural]
    return {
        "rows": len(results),
        "by_outcome": by_outcome,
        "behavioural_rows": len(behavioural),
        "reasoning_emitted": sum(1 for r in behavioural if r.reasoning_emitted),
        "reasoning_cap_hits": sum(1 for r in behavioural if r.reasoning_cap_hit),
        "empty_answers": sum(1 for r in behavioural if not r.final_answer.strip()),
        "answers_truncated": sum(1 for r in behavioural if r.answer_truncated),
    }
