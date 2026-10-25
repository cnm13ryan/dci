"""Which backend rows are behavioural evidence (decision D04).

Every row the backend returns is put in exactly one class:

* ``VALID``     --- the model generated an answer with visible text. Scored.
  A truncated answer (the completion cap bound) is VALID and keeps its
  truncation flag; D04 then makes it never compliant.
* ``EMPTY``     --- the model completed a generation and the answer is empty
  or whitespace. Behavioural: it enters every denominator and never
  complies. It is not regenerated: an empty answer is an observation.
* ``TECHNICAL`` --- no completed generation stands behind the row. Never
  evidence, never scored, kept out of ``rows.jsonl``; the request stays
  open and ``resume`` asks for it again.

**The seam's ``CHANNEL_INVALID``** (``exploratory/vllm_backend/records.py``
``generated``) means "no reasoning and no answer text". Batch 1 runs
``NO_THINKING``, whose ``NullParser`` returns the stripped generation as the
answer, so there it means the model produced only whitespace. It is read as
EMPTY only when the row itself shows that: no reasoning emitted, a raw
generation and an answer that are both blank, and a completed decode
(``finish_reason`` ``stop`` or ``length``). Any other ``CHANNEL_INVALID`` is
TECHNICAL, because the contract was not met in a way this rule can explain.

The other non-OK outcomes (``BACKEND_UNSUPPORTED``, ``CAPACITY_EXCEEDED``,
``NOT_GENERATED``, ``TECHNICAL_FAILURE``) and any outcome this module does
not know are TECHNICAL. So is an ``OK`` row without a completed decode or a
string answer.

``refusal_like`` is a diagnostic: a fixed phrase list on the opening of the
answer. It never changes a verdict or a denominator.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

__all__ = ["VALID", "EMPTY", "TECHNICAL", "BEHAVIOURAL", "Classification",
           "classify", "refusal_like", "COMPLETED_FINISH_REASONS",
           "TECHNICAL_OUTCOMES", "SEAM_ROW_KEYS"]

VALID, EMPTY, TECHNICAL = "VALID", "EMPTY", "TECHNICAL"
BEHAVIOURAL = frozenset({VALID, EMPTY})

#: Every key the seam writes on a row (``vllm_backend.contract.ROW_KEYS``,
#: checked equal by a test; copied because that package runs in the backend
#: interpreter). A real run root holds no row without all of them.
SEAM_ROW_KEYS = frozenset({
    "answer_truncated", "channel_valid", "final_answer", "final_answer_tokens",
    "finish_reason", "outcome", "outcome_detail", "raw_generation",
    "reasoning_cap_hit", "reasoning_closed", "reasoning_emitted",
    "reasoning_text", "reasoning_tokens", "rendered_prompt", "row_id",
    "seed_answer", "seed_reasoning", "stop_reason", "total_generated_tokens"})

COMPLETED_FINISH_REASONS = frozenset({"stop", "length"})
TECHNICAL_OUTCOMES = frozenset({"BACKEND_UNSUPPORTED", "CAPACITY_EXCEEDED",
                                "NOT_GENERATED", "TECHNICAL_FAILURE"})
#: The only reasoning mode Batch 1 runs (``config.DECODING``).
REASONING_MODE = "NO_THINKING"


@dataclass(frozen=True)
class Classification:
    kind: str
    reason: str

    @property
    def behavioural(self) -> bool:
        return self.kind in BEHAVIOURAL


def _blank(value: Any) -> bool:
    return isinstance(value, str) and not value.strip()


def classify(raw: Mapping[str, Any]) -> Classification:
    outcome = raw.get("outcome")
    answer = raw.get("final_answer")
    finish = raw.get("finish_reason")
    completed = finish in COMPLETED_FINISH_REASONS
    if outcome == "OK":
        if not isinstance(answer, str):
            return Classification(TECHNICAL, "OK row without a final answer")
        if not completed:
            return Classification(TECHNICAL, f"OK row without a completed "
                                             f"decode (finish_reason {finish!r})")
        if answer.strip():
            return Classification(VALID, "generated")
        return Classification(EMPTY, "generated; the answer is blank")
    if outcome == "CHANNEL_INVALID":
        evidence = (not raw.get("reasoning_emitted")
                    and _blank(raw.get("raw_generation", None))
                    and (answer is None or _blank(answer)) and completed)
        if evidence:
            return Classification(EMPTY, "completed NO_THINKING generation "
                                         "whose text is blank (seam "
                                         "CHANNEL_INVALID)")
        return Classification(TECHNICAL, "CHANNEL_INVALID without the marks "
                                         "of a completed blank generation")
    if outcome in TECHNICAL_OUTCOMES:
        return Classification(TECHNICAL, str(outcome))
    return Classification(TECHNICAL, f"unknown outcome {outcome!r}")


_REFUSAL = re.compile(
    r"^\W*(i'?m sorry|i am sorry|sorry,|i can(?:no|')t|i cannot|i won'?t|"
    r"i am unable|i'?m unable|as an ai)", re.IGNORECASE)


def refusal_like(text: Any) -> bool:
    return isinstance(text, str) and bool(_REFUSAL.match(text[:200]))
