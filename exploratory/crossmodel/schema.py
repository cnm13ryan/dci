"""The stored generation row, and what makes one valid.

Two rules this module enforces, both learned from the existing runs:

1. **Provenance travels in the row.** The canonical natural-reasoning file
   carries no `model_id` and no `model_revision`; the analysis recovers the
   checkpoint identity by regex over a preserved vLLM banner in a log file
   (`natural_analysis.py`, "a provenance gap in the runner"). A raw row that
   cannot say what produced it is only as trustworthy as the directory it sits
   in. Here every row carries model id, revision, backend, dtype, device layout,
   chat-template hash, reasoning mode and decoding.

2. **Missing metadata stays missing.** No field is defaulted to a plausible
   value. `build_row` requires what it needs and writes `None` for what genuinely
   was not observed, so a later reader can distinguish "not measured" from
   "measured as zero".
"""
from __future__ import annotations

from typing import Any, Optional

from crossmodel.adapters.base import Generation, GenerationConfig

#: Every field a scientific row must carry. Order is the stored column order.
REQUIRED_FIELDS = (
    "run_id",
    # provenance
    "model_id", "model_revision", "model_family",
    "backend", "backend_version", "dtype", "quantization",
    "device_configuration",
    "chat_template_identifier", "chat_template_sha256",
    # reasoning condition
    "reasoning_mode", "reasoning_control", "assigned_reasoning_budget",
    "engineering_ceiling",
    # decoding
    "temperature", "top_p", "top_k", "max_final_answer_tokens",
    # design identity
    "scientific_seed", "row_id", "task_id", "replicate_id", "arm",
    "background", "order", "measured", "load", "paraphrase_id", "pair_key",
    "condition",
    # payload
    "prompt", "rendered_prompt", "raw_generation", "reasoning_text",
    "final_answer",
    # accounting
    "reasoning_tokens", "final_answer_tokens", "total_generated_tokens",
    "finish_reason", "reasoning_emitted", "natural_reasoning_closed",
    "reasoning_cap_hit", "answer_truncated", "answer_empty",
    "generation_ok", "technical_failure", "technical_failure_reason",
)


def build_row(*, run_id: str, design_row: Any, generation: Generation,
              adapter_metadata: dict[str, Any], config: GenerationConfig,
              reasoning_control: str,
              scientific_seed: int) -> dict[str, Any]:
    """One stored row. Raises rather than inventing absent provenance."""
    for key in ("model_id", "model_revision", "model_family", "backend",
                "backend_version", "dtype", "device_configuration"):
        if not adapter_metadata.get(key):
            raise ValueError(
                f"adapter metadata is missing {key!r}; a row without it cannot "
                "establish what executed it and must not be written")

    def field(name: str) -> Any:
        return (design_row[name] if isinstance(design_row, dict)
                else getattr(design_row, name))

    row = {
        "run_id": run_id,
        "model_id": adapter_metadata["model_id"],
        "model_revision": adapter_metadata["model_revision"],
        "model_family": adapter_metadata["model_family"],
        "backend": adapter_metadata["backend"],
        "backend_version": adapter_metadata["backend_version"],
        "dtype": adapter_metadata["dtype"],
        "quantization": adapter_metadata.get("quantization", "none"),
        "device_configuration": adapter_metadata["device_configuration"],
        "chat_template_identifier":
            adapter_metadata.get("chat_template_identifier"),
        "chat_template_sha256": adapter_metadata.get("chat_template_sha256"),

        "reasoning_mode": config.reasoning_mode,
        "reasoning_control": reasoning_control,
        # `b`, the treatment: None under natural reasoning, deliberately.
        "assigned_reasoning_budget": config.assigned_reasoning_budget,
        # A safety bound, never a dose.
        "engineering_ceiling": config.engineering_ceiling,

        "temperature": config.temperature,
        "top_p": config.top_p,
        "top_k": config.top_k,
        "max_final_answer_tokens": config.max_answer_tokens,

        "scientific_seed": scientific_seed,
        "row_id": field("row_id"),
        "task_id": field("task_id"),
        "replicate_id": int(field("replicate")),
        "arm": field("arm"),
        "background": field("variant"),
        "order": field("order"),
        "measured": field("measured"),
        "load": int(field("load")),
        "paraphrase_id": int(field("paraphrase_id")),
        "pair_key": field("pair_key"),
        "condition": field("condition"),

        "prompt": field("user_prompt"),
        "rendered_prompt": generation.prompt,
        "raw_generation": generation.raw_generation,
        "reasoning_text": generation.reasoning_text,
        "final_answer": generation.final_answer,

        "reasoning_tokens": generation.reasoning_tokens,
        "final_answer_tokens": generation.final_answer_tokens,
        "total_generated_tokens": generation.total_generated_tokens,
        "finish_reason": generation.finish_reason,
        "reasoning_emitted": generation.reasoning_emitted,
        "natural_reasoning_closed": generation.natural_reasoning_closed,
        "reasoning_cap_hit": generation.reasoning_cap_hit,
        "answer_truncated": generation.answer_truncated,
        "answer_empty": generation.answer_empty,
        "generation_ok": generation.generation_ok,
        "technical_failure": generation.technical_failure,
        "technical_failure_reason": generation.technical_failure_reason,
        # execution detail, kept for reproducibility but never scientific
        "seed_reasoning": generation.seed_reasoning,
        "seed_answer": generation.seed_answer,
        "batch_seed": generation.batch_seed,
        "latency_seconds": round(generation.latency_seconds, 3),
    }
    missing = [f for f in REQUIRED_FIELDS if f not in row]
    if missing:
        raise ValueError(f"row is missing required fields: {missing}")
    return row


def assert_provenance(rows: list[dict[str, Any]],
                      expected_model: Optional[str] = None,
                      expected_revision: Optional[str] = None) -> dict[str, Any]:
    """Every row names one checkpoint, and it is the expected one."""
    models = {r.get("model_id") for r in rows}
    revisions = {r.get("model_revision") for r in rows}
    problems = []
    if len(models) != 1:
        problems.append(f"rows span several model ids: {sorted(models)}")
    if len(revisions) != 1:
        problems.append(f"rows span several revisions: {sorted(revisions)}")
    if None in models or "" in models:
        problems.append("some rows carry no model id")
    if any(not r or len(r) != 40 for r in revisions):
        problems.append(f"revision is not a commit sha: {sorted(revisions)}")
    if expected_model and models != {expected_model}:
        problems.append(f"expected model {expected_model}, found {models}")
    if expected_revision and revisions != {expected_revision}:
        problems.append(
            f"expected revision {expected_revision}, found {revisions}")
    if problems:
        raise AssertionError("provenance check failed: " + "; ".join(problems))
    return {"model_id": models.pop(), "model_revision": revisions.pop(),
            "rows": len(rows)}
