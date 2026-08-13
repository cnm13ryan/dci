"""Per-family vLLM execution configuration for the TP=2 retry.

Deliberately free of any vLLM import: this runs in the SCIENTIFIC environment,
which has torch 2.9.1 and no vLLM. It only describes how each checkpoint should
be driven; `vllm_backend` consumes the description in the backend
environment.

Everything here was read off the installed vLLM 0.27.1+rocm723 wheel, not
assumed:

* `ModelRegistry` in that build recognises all five architectures —
  `Qwen3_5ForConditionalGeneration`, `Gemma4ForConditionalGeneration`,
  `Gemma4UnifiedForConditionalGeneration`, `KimiVLForConditionalGeneration`.
  vLLM 0.15.1, the version this machine used for the canonical run, recognises
  only Kimi-VL, which is why the canonical build cannot serve as the common
  backend for this study.
* `ReasoningParserManager` registers `qwen3` and `gemma4`. It does NOT register
  anything for Kimi-VL: its `kimi_k2` / `kimi_k3` entries are the K-series text
  models, not this vision-language checkpoint. Kimi therefore falls back to the
  delimiters its own model card documents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class VllmModel:
    """How one checkpoint is driven through vLLM TP=2."""

    model_id: str
    family: str
    #: vLLM's registered reasoning parser, or None to fall back to delimiters.
    reasoning_parser: Optional[str]
    #: Kwargs forwarded to `apply_chat_template`. Native thinking is requested
    #: EXPLICITLY for every checkpoint that has a switch; a backend default is
    #: never a reasoning condition. Gemma 4's template defaults thinking OFF.
    chat_template_kwargs: dict[str, Any]
    think_open: str
    think_close: str
    #: Text-only: stop vLLM reserving multimodal cache the DCI prompts never
    #: use. This is vLLM's own supported knob, not model surgery.
    limit_mm_per_prompt: dict[str, int] = field(
        default_factory=lambda: {"image": 0, "video": 0})
    trust_remote_code: bool = False
    #: Practical context envelope. NOT the advertised maximum: Qwen3.5 and
    #: gemma-4-12B advertise 262,144 and allocating that as KV on two 24 GiB
    #: cards would be a guess dressed as a limit. Measured against the observed
    #: reasoning tail at calibration and raised only on evidence.
    max_model_len: int = 40960
    notes: str = ""


REGISTRY: dict[str, VllmModel] = {
    "Qwen/Qwen3.5-4B": VllmModel(
        model_id="Qwen/Qwen3.5-4B", family="qwen3.5",
        reasoning_parser="qwen3",
        chat_template_kwargs={"enable_thinking": True},
        think_open="<think>", think_close="</think>",
        notes="template pre-opens <think>; enable_thinking=True is the "
              "documented native switch"),
    "Qwen/Qwen3.5-9B": VllmModel(
        model_id="Qwen/Qwen3.5-9B", family="qwen3.5",
        reasoning_parser="qwen3",
        chat_template_kwargs={"enable_thinking": True},
        think_open="<think>", think_close="</think>"),
    "google/gemma-4-E4B-it": VllmModel(
        model_id="google/gemma-4-E4B-it", family="gemma4",
        reasoning_parser="gemma4",
        chat_template_kwargs={"enable_thinking": True},
        think_open="<|channel>thought", think_close="<channel|>",
        notes="thinking defaults to FALSE in this template; the <|think|> "
              "directive is injected into the system turn when enabled"),
    "google/gemma-4-12B-it": VllmModel(
        model_id="google/gemma-4-12B-it", family="gemma4",
        reasoning_parser="gemma4",
        chat_template_kwargs={"enable_thinking": True},
        think_open="<|channel>thought", think_close="<channel|>",
        notes="gemma4_unified architecture; 22.3 GiB of weights — the "
              "checkpoint TP=2 exists to rescue"),
    "moonshotai/Kimi-VL-A3B-Thinking-2506": VllmModel(
        model_id="moonshotai/Kimi-VL-A3B-Thinking-2506", family="kimi-vl",
        # vLLM 0.27.1 registers no parser for this checkpoint.
        reasoning_parser=None,
        # No reasoning switch exists in the template: it always thinks.
        chat_template_kwargs={},
        think_open="◁think▷", think_close="◁/think▷",
        trust_remote_code=True,
        limit_mm_per_prompt={"image": 0},
        notes="always-thinking checkpoint; no no-thinking toggle exists and "
              "its non-thinking sibling is a different checkpoint"),
}

CHECKPOINTS = tuple(REGISTRY)


def get(model_id: str) -> VllmModel:
    if model_id not in REGISTRY:
        raise KeyError(f"{model_id!r} is not a registered cross-model "
                       f"checkpoint. Known: {', '.join(CHECKPOINTS)}")
    return REGISTRY[model_id]
