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

    #: Whether this card's reasoning control was ESTABLISHED for the checkpoint,
    #: as opposed to defaulted for one it has never seen.
    #:
    #: False only on the fallback card from `get_or_default`. It exists because
    #: an empty `template_kwargs_by_mode` is ambiguous on its own: for Kimi-VL it
    #: is a finding (the template takes no reasoning argument, so passing one
    #: would be silently ignored), and for an unregistered checkpoint it is the
    #: absence of a finding. Collapsing the two let `enable_thinking` quietly
    #: stop being passed on `Qwen/Qwen3-4B`, which would have rendered the
    #: NO_THINKING control identically to the thinking condition.
    reasoning_control_declared: bool = True

    notes: str = ""

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        """Template kwargs for a mode. Never a guess, and never silently empty.

        An undeclared card raises rather than returning `{}`: empty kwargs mean
        "this template takes no reasoning argument", which is a claim about the
        checkpoint that a fallback is in no position to make.
        """
        if not self.reasoning_control_declared:
            raise UnregisteredReasoningControl(
                f"{self.model_id!r} is not a registered checkpoint, so how its "
                f"chat template selects reasoning mode {reasoning_mode!r} is "
                f"unknown. Returning no kwargs would render every mode "
                f"identically and record the wrong experimental condition. "
                f"Add a ModelCard for it -- verified by rendering the template "
                f"both ways -- or run a mode-agnostic probe that does not ask "
                f"for template kwargs.")
        return dict(self.template_kwargs_by_mode.get(reasoning_mode, {}))

    def supports(self, reasoning_mode: str) -> bool:
        return reasoning_mode in self.supported_modes


class UnregisteredReasoningControl(RuntimeError):
    """A mode-specific rendering was asked of a checkpoint with no ModelCard."""


#: Verified against the installed wheels, not inferred from names. vLLM 0.15.1
#: registers `qwen3` and `kimi_k2` but NOT `gemma4`; vLLM 0.27.1 registers
#: `qwen3` and `gemma4`. Neither registers anything for Kimi-VL — the `kimi_k2`
#: / `kimi_k3` entries are the K-series TEXT models, not this vision-language
#: checkpoint — so Kimi falls back to its documented delimiters.
#: `capabilities.probe()` re-checks this at run time against the live wheel.
REGISTRY: dict[str, ModelCard] = {
    # The two checkpoints that produced this study's existing results. Both were
    # missing until the consolidation audit, so both fell back to the
    # undeclared card and lost their reasoning switch. Every value below was
    # read off the cached tokenizer by rendering the template, not inferred.
    "Qwen/Qwen3-4B": ModelCard(
        model_id="Qwen/Qwen3-4B", family="qwen3",
        reasoning_parser="qwen3",
        template_kwargs_by_mode={
            ReasoningMode.NATURAL_REASONING: {"enable_thinking": True},
            ReasoningMode.THINKING_ENABLED_BOUNDED: {"enable_thinking": True},
            ReasoningMode.LIMITED_REASONING: {"enable_thinking": True},
            ReasoningMode.NO_THINKING: {"enable_thinking": False},
        },
        think_open="<think>", think_close="</think>",
        supported_modes=(ReasoningMode.NO_THINKING,
                         ReasoningMode.LIMITED_REASONING,
                         ReasoningMode.NATURAL_REASONING,
                         ReasoningMode.THINKING_ENABLED_BOUNDED),
        notes="hybrid checkpoint; the reasoning-compute line of work runs here "
              "because vLLM 0.15.1 registers Qwen3ForCausalLM and not "
              "Qwen3_5ForCausalLM. Verified by rendering: enable_thinking=False "
              "injects a PRE-CLOSED '<think>\\n\\n</think>' block, so "
              "non-thinking is implemented by closing the channel rather than "
              "omitting it, and enable_thinking=True equals the template "
              "default. It does NOT pre-open <think> -- that is "
              "Qwen3-4B-Thinking-2507, which is why the split repair exists."),
    "Qwen/Qwen3-4B-Thinking-2507": ModelCard(
        model_id="Qwen/Qwen3-4B-Thinking-2507", family="qwen3",
        reasoning_parser="qwen3",
        # The template takes no switch: this checkpoint always thinks, so the
        # mode is the checkpoint rather than an argument to it.
        template_kwargs_by_mode={},
        think_open="<think>", think_close="</think>",
        supported_modes=(ReasoningMode.NATURAL_REASONING,
                         ReasoningMode.LIMITED_REASONING,
                         ReasoningMode.THINKING_ENABLED_BOUNDED),
        notes="PRE-OPENS <think> in the prompt, verified by rendering. vLLM's "
              "qwen3 parser looks for that marker in the OUTPUT, does not find "
              "it, and returns the whole trace as content -- the leak the split "
              "repair exists for. This is the checkpoint that exhibits it."),
    "Qwen/Qwen3-4B-Instruct-2507": ModelCard(
        model_id="Qwen/Qwen3-4B-Instruct-2507", family="qwen3",
        # Nothing to parse: this checkpoint has no reasoning channel.
        reasoning_parser=None,
        # DECLARED empty, exactly as for Kimi-VL and for the same reason:
        # rendering with enable_thinking True and False gives byte-identical
        # prompts, so the template has no such variable and passing one would
        # be silently ignored.
        template_kwargs_by_mode={},
        supported_modes=(ReasoningMode.NO_THINKING,),
        notes="the non-thinking half of the Qwen3-4B split; its thinking "
              "sibling is Qwen3-4B-Thinking-2507, i.e. a different execution "
              "condition. Carries the entire exploratory ladder (57 runs). "
              "Verified by rendering: enable_thinking is INERT here."),
    # The dev/validation checkpoint. Small enough to load on one card, which is
    # what makes a TP=1 vs TP=2 comparison cheap. Verified by rendering:
    # enable_thinking is INERT, so it declares no reasoning argument.
    "Qwen/Qwen2.5-0.5B-Instruct": ModelCard(
        model_id="Qwen/Qwen2.5-0.5B-Instruct", family="qwen2.5",
        reasoning_parser=None,
        template_kwargs_by_mode={},
        supported_modes=(ReasoningMode.NO_THINKING,),
        # 32,768, not the 40,960 the other cards use: this checkpoint's
        # max_position_embeddings is 32k, and vLLM refuses an envelope larger
        # than the positions the weights were trained for. Caught by hardware
        # validation, which is the only place a wrong envelope shows up.
        max_model_len=32768,
        notes="no reasoning channel; used for hardware validation and the "
              "dev_fast profile"),
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

    The fallback is deliberately *unusable* for mode-specific work: it declares
    no supported modes and raises from `template_kwargs`. A probe that only
    needs to load a checkpoint and generate is unaffected; anything that asks
    how to select a reasoning condition gets an error instead of a default,
    because the default would be "render every mode identically".
    """
    if model_id in REGISTRY:
        return REGISTRY[model_id]
    return ModelCard(model_id=model_id, family="unregistered",
                     reasoning_parser=None,
                     supported_modes=(),
                     reasoning_control_declared=False,
                     notes="not in REGISTRY; reasoning control unknown")
