"""Qwen3.5 execution adapter.

The reasoning interface is read off the checkpoint's OWN chat template rather
than assumed from the Qwen3 generation:

    {%- if add_generation_prompt %}
        {{- '<|im_start|>assistant\\n' }}
        {%- if enable_thinking is defined and enable_thinking is false %}
            {{- '<think>\\n\\n</think>\\n\\n' }}
        {%- else %}
            {{- '<think>\\n' }}
        {%- endif %}
    {%- endif %}

Two consequences, both handled here rather than in the runner:

* **Thinking is the template default and it PRE-OPENS the block.** The generation
  prompt already ends with `<think>\\n`, so the completion does not repeat the
  opening delimiter — unlike Qwen3, whose template emitted nothing and left the
  model to open the block itself. The stored trace is normalised either way.

* **Non-thinking is a native, structural mechanism.** `enable_thinking=False`
  splices an already-closed empty reasoning block into the prompt, so the model
  answers directly. This is the documented control, not a soft-prompt trick and
  not a truncated trace: NO_THINKING here runs no reasoning phase at all.

Both checkpoints are `Qwen3_5ForConditionalGeneration` — multimodal — and the DCI
prompts are text-only, so the adapter loads `Qwen3_5ForCausalLM` to avoid
allocating a vision tower that no prompt in this study uses.
"""
from __future__ import annotations

from typing import Any

from crossmodel.adapters.transformers_base import TransformersAdapter
from crossmodel.contract import ReasoningMode


class Qwen35Adapter(TransformersAdapter):
    FAMILY = "qwen3.5"
    THINK_OPEN = "<think>"
    THINK_CLOSE = "</think>"
    SUPPORTED_MODES = (ReasoningMode.NO_THINKING,
                       ReasoningMode.NATURAL_REASONING)
    TEXT_ONLY_CLASS = "Qwen3_5ForCausalLM"
    FULL_CLASS = "Qwen3_5ForConditionalGeneration"

    #: PRACTICAL context envelope, not the architectural maximum.
    #: `text_config.max_position_embeddings` is 262,144 for both checkpoints.
    #: Deriving the engineering ceiling from that would produce a "ceiling" of a
    #: quarter of a million tokens that the hardware cannot serve and that no
    #: observed trace approaches — a number that would look like a treatment and
    #: behave like a fiction. 40,960 is the envelope the canonical Qwen3-4B run
    #: used, it is two orders of magnitude above the observed natural traces, and
    #: it fits the two 24 GiB cards. Recorded as a deliberate choice.
    CONTEXT_LIMIT = 40960

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        if reasoning_mode == ReasoningMode.NO_THINKING:
            return {"enable_thinking": False}
        return {"enable_thinking": True}


class Qwen35_4B(Qwen35Adapter):
    MODEL_ID = "Qwen/Qwen3.5-4B"


class Qwen35_9B(Qwen35Adapter):
    MODEL_ID = "Qwen/Qwen3.5-9B"
