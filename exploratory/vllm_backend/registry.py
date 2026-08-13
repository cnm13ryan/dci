"""Declarative per-checkpoint facts — the ONLY place model-specific behaviour lives.

Stdlib only, and deliberately free of any vLLM import: the plan builders that
consume this run in the SCIENTIFIC environment (torch 2.9.1, no vLLM).

Everything here is a fact about a *checkpoint* that no upstream API can report.
Anything vLLM can answer for itself (is the architecture registered? is it
multimodal? which reasoning parsers exist?) belongs in `capabilities.py`, not
here, and anything about the host (VRAM, arch, TP size) belongs in `resolve.py`.

The bar for adding a field to `ModelCard` is: *a probe cannot discover it, and
guessing it wrong corrupts the science silently.* Four things clear that bar —
the reasoning switch, the delimiters, the supported modes, and remote code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ReasoningMode:
    """Mirrors `crossmodel.contract.ReasoningMode`.

    Duplicated rather than imported on purpose: this package is executed by a
    different interpreter from `crossmodel` and must not import it. The values
    are asserted equal by `test_model_registry.py` so the two cannot drift.
    """

    NO_THINKING = "NO_THINKING"
    LIMITED_REASONING = "LIMITED_REASONING"
    NATURAL_REASONING = "NATURAL_REASONING"
    THINKING_ENABLED_BOUNDED = "THINKING_ENABLED_BOUNDED"


@dataclass(frozen=True)
class ModelCard:
    """How one checkpoint is driven, and nothing else."""

    model_id: str
    family: str

    #: vLLM's registered reasoning parser name, or None to fall back to the
    #: delimiters below. NOT discoverable in advance: which parsers a given
    #: wheel registers is a property of the build, so `capabilities.probe()`
    #: verifies this name really is registered before the run trusts it.
    reasoning_parser: str | None = None

    #: Kwargs forwarded to `apply_chat_template`, per reasoning mode.
    #:
    #: IRREDUCIBLE. A chat template is a Jinja program; there is no upstream API
    #: that answers "does this template have a thinking switch and what is the
    #: kwarg called". Worse, Jinja *silently ignores* unknown kwargs, so a wrong
    #: name yields no error and the wrong experimental condition. The defaults
    #: genuinely differ by family — Qwen 3.5 defaults thinking ON, Gemma 4's
    #: template sets `enable_thinking | default(false)` — so the mode is always
    #: passed explicitly and never inherited from a backend default.
    #:
    #: `engine.render_prompts` verifies the switch is live by rendering both
    #: ways and asserting the strings differ, which converts a silently-ignored
    #: kwarg into a loud failure.
    template_kwargs_by_mode: dict[str, dict[str, Any]] = field(
        default_factory=dict)

    #: Reasoning delimiters.
    #:
    #: IRREDUCIBLE for any checkpoint vLLM registers no parser for. These come
    #: off the model card and cannot be derived from the tokenizer: Kimi-VL's
    #: `◁think▷` is ordinary vocabulary, not a declared special token.
    think_open: str = "<think>"
    think_close: str = "</think>"

    #: Modes this checkpoint natively supports.
    #:
    #: IRREDUCIBLE. No probe can tell that a mode's absence is intentional
    #: rather than a bug. Kimi-VL-A3B-Thinking-2506 always thinks; its
    #: non-thinking sibling is a DIFFERENT checkpoint, i.e. a different
    #: execution condition. An unsupported mode is a missing cell, never
    #: something to emulate.
    supported_modes: tuple[str, ...] = (
        ReasoningMode.NO_THINKING, ReasoningMode.NATURAL_REASONING)

    #: The checkpoint carries its own modeling code.
    #:
    #: Semi-derivable (`config.json` declares `auto_map`), so `capabilities.probe()`
    #: derives it and asserts the declared value matches rather than trusting
    #: this field blindly.
    trust_remote_code: bool = False

    #: Text-only knob for a multimodal checkpoint. Generic in principle — vLLM
    #: knows which architectures are multimodal — so `resolve.py` only applies
    #: it when the probe confirms multimodality.
    limit_mm_per_prompt: dict[str, int] | None = None

    #: PRACTICAL context envelope, NOT the advertised maximum. Qwen3.5 and
    #: gemma-4-12B advertise 262,144; allocating that as KV on two 24 GiB cards
    #: would be a guess dressed as a limit. Held equal across families so the
    #: engineering ceiling is not itself a cross-model confound.
    max_model_len: int = 40960

    notes: str = ""

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        """Template kwargs for a mode. Unknown mode -> empty, never a guess."""
        return dict(self.template_kwargs_by_mode.get(reasoning_mode, {}))

    def supports(self, reasoning_mode: str) -> bool:
        return reasoning_mode in self.supported_modes


#: Verified against the installed wheels, not inferred from names. vLLM 0.15.1
#: registers `qwen3` and `kimi_k2` but NOT `gemma4`; vLLM 0.27.1 registers
#: `qwen3` and `gemma4`. Neither registers anything for Kimi-VL — the `kimi_k2`
#: / `kimi_k3` entries are the K-series TEXT models, not this vision-language
#: checkpoint — so Kimi falls back to its documented delimiters.
#: `capabilities.probe()` re-checks this at run time against the live wheel.
REGISTRY: dict[str, ModelCard] = {
    "Qwen/Qwen3.5-4B": ModelCard(
        model_id="Qwen/Qwen3.5-4B", family="qwen3.5",
        reasoning_parser="qwen3",
        template_kwargs_by_mode={
            ReasoningMode.NATURAL_REASONING: {"enable_thinking": True},
            ReasoningMode.THINKING_ENABLED_BOUNDED: {"enable_thinking": True},
            ReasoningMode.LIMITED_REASONING: {"enable_thinking": True},
            ReasoningMode.NO_THINKING: {"enable_thinking": False},
        },
        think_open="<think>", think_close="</think>",
        notes="template pre-opens <think>; enable_thinking is the documented "
              "native switch"),
    "Qwen/Qwen3.5-9B": ModelCard(
        model_id="Qwen/Qwen3.5-9B", family="qwen3.5",
        reasoning_parser="qwen3",
        template_kwargs_by_mode={
            ReasoningMode.NATURAL_REASONING: {"enable_thinking": True},
            ReasoningMode.THINKING_ENABLED_BOUNDED: {"enable_thinking": True},
            ReasoningMode.LIMITED_REASONING: {"enable_thinking": True},
            ReasoningMode.NO_THINKING: {"enable_thinking": False},
        },
        think_open="<think>", think_close="</think>"),
    "google/gemma-4-E4B-it": ModelCard(
        model_id="google/gemma-4-E4B-it", family="gemma4",
        reasoning_parser="gemma4",
        template_kwargs_by_mode={
            ReasoningMode.NATURAL_REASONING: {"enable_thinking": True},
            ReasoningMode.THINKING_ENABLED_BOUNDED: {"enable_thinking": True},
            ReasoningMode.LIMITED_REASONING: {"enable_thinking": True},
            ReasoningMode.NO_THINKING: {"enable_thinking": False},
        },
        # Special tokens (ids 100/101). Decoded with skip_special_tokens=True
        # they vanish and the reasoning trace flows silently into the scored
        # answer, which is why the boundary is named explicitly here.
        think_open="<|channel>thought", think_close="<channel|>",
        notes="thinking defaults to FALSE in this template; the <|think|> "
              "directive is injected into the system turn when enabled"),
    "google/gemma-4-12B-it": ModelCard(
        model_id="google/gemma-4-12B-it", family="gemma4",
        reasoning_parser="gemma4",
        template_kwargs_by_mode={
            ReasoningMode.NATURAL_REASONING: {"enable_thinking": True},
            ReasoningMode.THINKING_ENABLED_BOUNDED: {"enable_thinking": True},
            ReasoningMode.LIMITED_REASONING: {"enable_thinking": True},
            ReasoningMode.NO_THINKING: {"enable_thinking": False},
        },
        think_open="<|channel>thought", think_close="<channel|>",
        notes="gemma4_unified architecture; 22.3 GiB of weights — the "
              "checkpoint TP=2 exists to rescue"),
    "moonshotai/Kimi-VL-A3B-Thinking-2506": ModelCard(
        model_id="moonshotai/Kimi-VL-A3B-Thinking-2506", family="kimi-vl",
        # No registered parser in any wheel on this host.
        reasoning_parser=None,
        # The template takes no reasoning argument. Passing one would be
        # silently ignored, which is worse than passing none.
        template_kwargs_by_mode={},
        think_open="◁think▷", think_close="◁/think▷",
        # Thinking only: the non-thinking sibling is a separate checkpoint.
        supported_modes=(ReasoningMode.NATURAL_REASONING,
                         ReasoningMode.THINKING_ENABLED_BOUNDED),
        trust_remote_code=True,
        limit_mm_per_prompt={"image": 0},
        notes="always-thinking checkpoint; no no-thinking toggle exists and "
              "its non-thinking sibling is a different checkpoint"),
}

CHECKPOINTS = tuple(REGISTRY)


def get(model_id: str) -> ModelCard:
    if model_id not in REGISTRY:
        raise KeyError(f"{model_id!r} is not a registered checkpoint. "
                       f"Known: {', '.join(CHECKPOINTS)}")
    return REGISTRY[model_id]


def get_or_default(model_id: str) -> ModelCard:
    """A card for an unregistered checkpoint, with conservative defaults.

    Used by the probes and smoke tests, which legitimately point at arbitrary
    checkpoints. Experiment runners call `get()` so an unregistered model is a
    loud error rather than a silent set of assumptions.
    """
    if model_id in REGISTRY:
        return REGISTRY[model_id]
    return ModelCard(model_id=model_id, family="unregistered",
                     reasoning_parser=None,
                     notes="not in REGISTRY; defaults assumed")
