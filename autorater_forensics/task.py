"""Inspect AI task: one fixed (constraint, frozen response) judged by
openai/gpt-oss-20b through the local vLLM OpenAI endpoint, with
reasoning effort as the ONLY manipulated variable.

Run (from autorater_forensics/, venv activated, server up):

    inspect eval task.py@forensics -T effort=low \
        --model openai/gpt-oss-20b \
        --model-base-url http://127.0.0.1:8555/v1 \
        --log-dir logs/low --max-connections 4

Everything else is pinned in-task: greedy decoding (temperature 0,
top_p 1), max_tokens 2048, fixed dataset order, the registered judge
prompt, and the registered parsing vocabulary. ``reasoning_effort`` is
sent as a top-level chat-completions parameter via extra_body; the
pinned vLLM maps it into the harmony chat template
(chat_completion/serving.py:299) and returns the analysis channel
separately in ``reasoning_content``.
"""
from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset, FieldSpec
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    Target,
    metric,
    scorer,
)
from inspect_ai.solver import TaskState, generate

from src.forensics.parser import parse_final

EFFORTS = ("low", "medium", "high")


@metric
def valid_agreement() -> Metric:
    """Agreement with the deterministic verifier among VALID judgments.
    A proxy diagnostic only — never human validation or ground truth."""
    def compute(scores: list[SampleScore]) -> float:
        valid = [s for s in scores
                 if s.score.metadata.get("status") == "valid"]
        if not valid:
            return 0.0
        return sum(1 for s in valid
                   if s.score.metadata.get("agrees_verifier")) \
            / len(valid)
    return compute


@metric
def coverage() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        if not scores:
            return 0.0
        return sum(1 for s in scores
                   if s.score.metadata.get("status") == "valid") \
            / len(scores)
    return compute


@scorer(metrics=[valid_agreement(), coverage()])
def judge_parse():
    async def score(state: TaskState, target: Target) -> Score:
        message = state.output.message
        reasoning_parts, text_parts = [], []
        content = message.content
        if isinstance(content, str):
            text_parts.append(content)
        else:
            for part in content:
                kind = getattr(part, "type", None)
                if kind == "reasoning":
                    reasoning_parts.append(part.reasoning)
                elif kind == "text":
                    text_parts.append(part.text)
        final_text = "\n".join(t for t in text_parts if t)
        reasoning_text = "\n".join(r for r in reasoning_parts if r)
        status, label, justification = parse_final(final_text)
        stop = state.output.stop_reason
        truncated = stop == "max_tokens"
        verifier = state.metadata["deterministic_verifier_label"]
        usage = state.output.usage
        return Score(
            value=(status if status != "valid" else
                   ("agree" if label == verifier else "disagree")),
            answer=label or "",
            explanation=justification,
            metadata={
                "status": status,
                "parsed_label": label,
                "agrees_verifier": (status == "valid"
                                    and label == verifier),
                "deterministic_verifier_label": verifier,
                "stop_reason": stop,
                "truncated": truncated,
                "reasoning_chars": len(reasoning_text),
                "final_chars": len(final_text),
                "reasoning_text": reasoning_text,
                "final_text": final_text,
                "completion_tokens": (usage.output_tokens
                                      if usage else None),
                "prompt_tokens": (usage.input_tokens
                                  if usage else None),
            })
    return score


@task
def forensics(effort: str = "low",
              dataset_path: str = "dataset/diagnostic.jsonl") -> Task:
    if effort not in EFFORTS:
        raise ValueError(f"effort must be one of {EFFORTS}")
    dataset = json_dataset(
        dataset_path,
        FieldSpec(input="input", target="target", id="id",
                  metadata=["item_id", "source_model", "source_pool",
                            "constraint_text", "response_text",
                            "target_n", "s0_count",
                            "deterministic_verifier_label",
                            "split_class", "response_chars",
                            "response_words",
                            "prior_low_label", "prior_low_status",
                            "prior_medium_label", "prior_medium_status",
                            "prior_high_label", "prior_high_status",
                            "contested", "contested_reasons"]),
        shuffle=False)
    return Task(
        dataset=dataset,
        solver=generate(),
        scorer=judge_parse(),
        config=GenerateConfig(
            temperature=0.0,
            top_p=1.0,
            max_tokens=2048,
            seed=20260817,
            # verbatim top-level chat-completions parameter; the pinned
            # vLLM maps it into the harmony chat template
            extra_body={"reasoning_effort": effort},
        ),
        metadata={"reasoning_effort": effort,
                  "judge": "openai/gpt-oss-20b",
                  "judge_revision":
                      "6cee5e81ee83917806bbde320786a8fb61efebee",
                  "prompt_version": "gate1-judge/2.0.0",
                  "parser": "forensics parse_final (mirrors "
                            "gate1-parse/2.0.0 vocabulary)"},
    )
