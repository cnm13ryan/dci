"""Backend plan payloads (§4). Every backend-consumed field is explicit;
the backend registry supplies nothing. The completion cap is the
model-adaptive value selected by the regime pre-screen (or the registered
stage-specific cap)."""
from __future__ import annotations

from typing import Any

from dci1v3.errors import ProtocolError
from dci1v3.models.registry import ModelSpec
from dci1v3.protocol.constants import (
    CAP_GRID,
    DECODING,
    ENGINE_SEED,
    GREEDY_DECODING,
    PILOT_CAP,
)


def backend_plan(spec: ModelSpec, *, cap: int, decoding: str = "stochastic",
                 chunk_size: int = 32) -> dict[str, Any]:
    if cap not in CAP_GRID and cap != PILOT_CAP:
        raise ProtocolError(f"cap {cap} outside the registered grid")
    if decoding == "stochastic":
        policy, top_k = DECODING, DECODING["top_k"]
    elif decoding == "greedy":
        policy, top_k = GREEDY_DECODING, 0
    else:
        raise ProtocolError(f"unknown decoding policy {decoding!r}")
    return {
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "model_family": spec.family,
        "dtype": spec.dtype,
        "quantization": "none",
        "tensor_parallel_size": spec.tensor_parallel_size,
        "gpu_memory_utilization": spec.gpu_memory_utilization,
        "disable_custom_all_reduce": True,
        "enforce_eager": True,
        "cpu_offload_gb": 0.0,
        "max_model_len": spec.max_model_len,
        "engine_seed": ENGINE_SEED,
        "trust_remote_code": False,
        "limit_mm_per_prompt": None,
        "temperature": policy["temperature"],
        "top_p": policy["top_p"],
        "top_k": top_k,
        "generation_ceiling": cap,
        "answer_tokens": cap,
        "chunk_size": chunk_size,
        "deadline_seconds": None,
        "strategy": "single_phase",
        "reasoning_mode": "NO_THINKING",
        "chat_template_kwargs": dict(spec.chat_template_kwargs),
        "reasoning_parser": None,
        "think_open": "",
        "think_close": "",
        "decoding_policy": decoding,
    }
