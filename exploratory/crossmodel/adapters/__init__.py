"""The adapter registry: the only place a checkpoint name meets a class.

The runner, the validators and the analysis all address checkpoints by their hub
id and get an adapter back. Nothing downstream branches on family, and nothing
downstream constructs an adapter class directly — which is what keeps
family-specific execution out of the scientific code.
"""
from __future__ import annotations

from typing import Any, Optional

from crossmodel.adapters.base import (Generation, GenerationConfig,
                                      ModelAdapter)
from crossmodel.adapters.gemma4 import Gemma4_12B, Gemma4_E4B
from crossmodel.adapters.kimivl import KimiVLThinkingAdapter
from crossmodel.adapters.qwen35 import Qwen35_4B, Qwen35_9B
from crossmodel.adapters.transformers_base import TransformersAdapter

#: The five checkpoints of the cross-model replication, in a fixed order.
REGISTRY: dict[str, type[ModelAdapter]] = {
    Qwen35_4B.MODEL_ID: Qwen35_4B,
    Qwen35_9B.MODEL_ID: Qwen35_9B,
    Gemma4_E4B.MODEL_ID: Gemma4_E4B,
    Gemma4_12B.MODEL_ID: Gemma4_12B,
    KimiVLThinkingAdapter.MODEL_ID: KimiVLThinkingAdapter,
}

CHECKPOINTS = tuple(REGISTRY)


def get_adapter(model_id: str, revision: Optional[str] = None,
                device_map: Any = None, dtype: str = "bfloat16"
                ) -> ModelAdapter:
    if model_id not in REGISTRY:
        raise KeyError(
            f"{model_id!r} is not a registered cross-model checkpoint. "
            f"Known: {', '.join(CHECKPOINTS)}")
    return REGISTRY[model_id](revision=revision, device_map=device_map,
                              dtype=dtype)


__all__ = ["REGISTRY", "CHECKPOINTS", "get_adapter", "ModelAdapter",
           "TransformersAdapter", "Generation", "GenerationConfig",
           "Qwen35_4B", "Qwen35_9B", "Gemma4_E4B", "Gemma4_12B",
           "KimiVLThinkingAdapter"]
