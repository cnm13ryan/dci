"""The process boundary: plan.json / design.jsonl in, rows.jsonl out.

Stdlib only. This preserves the pattern the study already relies on — the
SCIENTIFIC environment (torch 2.9.1, no vLLM) writes a plan and a design, a
DIFFERENT interpreter reads them and generates — because vLLM's ROCm wheels pin
a torch that the scientific environment cannot hold. That boundary is not a
workaround to be refactored away; it is load-bearing.

`load_plan` reads the EXISTING `plan.json` shape emitted by `xm_vllm_plan.py`
unchanged, so archived plans stay executable.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from vllm_backend.contract import GenerationRequest, GenerationResult
from vllm_backend.plan import EnginePlan, RunPlan, SamplingPlan
from vllm_backend.registry import ModelCard, ReasoningMode, get_or_default

#: Design-row keys consumed directly; everything else travels as identity.
_REQUEST_KEYS = {"row_id", "user_prompt", "system_message", "scientific_seed",
                 "answer_seed"}


def load_plan(path: str | Path) -> tuple[EnginePlan, SamplingPlan, RunPlan,
                                         ModelCard, dict[str, Any]]:
    """Read a plan.json into typed objects, tolerating the legacy shape."""
    raw = json.loads(Path(path).read_text())

    engine = EnginePlan(
        model_id=raw["model_id"],
        model_revision=raw.get("model_revision", ""),
        dtype=raw.get("dtype", "bfloat16"),
        quantization=raw.get("quantization", "none"),
        tensor_parallel_size=int(raw.get("tensor_parallel_size", 1)),
        gpu_memory_utilization=float(raw.get("gpu_memory_utilization", 0.85)),
        disable_custom_all_reduce=bool(raw.get("disable_custom_all_reduce", True)),
        enforce_eager=bool(raw.get("enforce_eager", True)),
        cpu_offload_gb=float(raw.get("cpu_offload_gb") or 0.0),
        max_model_len=int(raw.get("max_model_len", 40960)),
        seed=int(raw.get("engine_seed", 20260812)),
        trust_remote_code=bool(raw.get("trust_remote_code", False)),
        limit_mm_per_prompt=raw.get("limit_mm_per_prompt") or None,
    )

    # The bounded condition names ONE number: the total tokens a request may
    # produce, reasoning and answer together. `generation_ceiling` states it
    # directly; older plans state it as reasoning ceiling + answer allowance.
    answer_tokens = int(raw.get("answer_tokens", 512))
    budget = int(raw.get("generation_ceiling")
                 or int(raw.get("engineering_ceiling", 0)) + answer_tokens)
    top_k = raw.get("top_k", 0)
    sampling = SamplingPlan(
        temperature=float(raw.get("temperature", 0.7)),
        top_p=float(raw.get("top_p", 0.9)),
        # Legacy plans write 0 to mean "off"; vLLM spells that -1.
        top_k=int(top_k) if top_k and int(top_k) > 0 else -1,
        max_tokens=budget,
        answer_tokens=answer_tokens,
    )

    card = get_or_default(raw["model_id"])
    # A plan may pin the parser/delimiters explicitly; that pin wins over the
    # registry so an archived plan replays exactly as it ran.
    overrides: dict[str, Any] = {}
    if "reasoning_parser" in raw:
        overrides["reasoning_parser"] = raw["reasoning_parser"]
    if raw.get("think_open"):
        overrides["think_open"] = raw["think_open"]
    if raw.get("think_close"):
        overrides["think_close"] = raw["think_close"]
    if raw.get("model_family"):
        overrides["family"] = raw["model_family"]
    if overrides:
        from dataclasses import replace

        card = replace(card, **overrides)

    mode = raw.get("reasoning_mode", ReasoningMode.NATURAL_REASONING)
    template_kwargs = raw.get("chat_template_kwargs")
    if template_kwargs is None:
        template_kwargs = card.template_kwargs(mode)
    run = RunPlan(
        chunk_size=int(raw.get("chunk_size") or 32),
        deadline_seconds=raw.get("deadline_seconds"),
        chat_template_kwargs=dict(template_kwargs),
        strategy=raw.get("strategy", "single_phase"),
        reasoning_mode=mode,
    )
    return engine, sampling, run, card, raw


def load_design(path: str | Path) -> list[GenerationRequest]:
    """Read design.jsonl into requests, carrying scientific identity through."""
    requests = []
    for line in Path(path).open():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        requests.append(GenerationRequest(
            row_id=str(row["row_id"]),
            user_prompt=row["user_prompt"],
            system_message=row.get("system_message", "") or "",
            scientific_seed=int(row.get("scientific_seed", 0)),
            answer_seed=int(row.get("answer_seed", 0)),
            identity={k: v for k, v in row.items() if k not in _REQUEST_KEYS},
        ))
    return requests


def write_rows(path: str | Path, results: Iterable[GenerationResult],
               append: bool = False) -> None:
    """Append rows as JSONL so a stopped run keeps every completed row."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a" if append else "w") as handle:
        for result in results:
            handle.write(json.dumps(result.as_row()) + "\n")


def write_provenance(path: str | Path, provenance: dict[str, Any]) -> Path:
    """Engine/host/capability record beside the rows."""
    target = Path(path)
    out = target.with_name(target.stem + "_engine.json")
    out.write_text(json.dumps(provenance, indent=1, default=str))
    return out
