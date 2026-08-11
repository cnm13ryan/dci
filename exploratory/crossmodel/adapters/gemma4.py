"""Gemma 4 execution adapter.

Nothing here is transferred from the Qwen adapter. Gemma 4's reasoning interface
is structurally different, and assuming Qwen's delimiters would have produced a
run whose "final answers" were scratchpads. Read off the checkpoint's own
canonical chat template:

* Thinking is **off by default** — `{%- set enable_thinking =
  enable_thinking | default(false) -%}`. The backend default is therefore the
  NO_THINKING condition, which is why the mode is passed explicitly for every
  generation rather than relied upon.
* Enabling it injects a `<|think|>` directive at the top of the **first system
  turn**, not at the assistant turn. Reasoning is a system-level channel switch,
  not an assistant-side prefix.
* The trace itself is emitted as a named channel:
  `<|channel>thought\\n ... \\n<channel|>`. The template's own `strip_thinking`
  macro splits on exactly these markers, which is the model card's statement of
  where the boundary is.

The consequence that matters most: `<|channel>` and `<channel|>` are **special
tokens** (ids 100 and 101). Decoded with `skip_special_tokens=True` they
disappear, the boundary disappears with them, and the reasoning trace flows
silently into the scored answer. `TransformersAdapter` therefore decodes with
`skip_special_tokens=False` and strips only the control tokens listed below —
never the channel markers.

Both checkpoints are multimodal conditional-generation architectures and the DCI
prompts are text-only, so the adapter asks for the causal-LM class first and
records whether that succeeded.
"""
from __future__ import annotations

from typing import Any

from crossmodel.adapters.transformers_base import TransformersAdapter
from crossmodel.contract import ReasoningMode


class Gemma4Adapter(TransformersAdapter):
    FAMILY = "gemma4"
    #: The channel opener. The template writes `<|channel>thought\n`; matching
    #: on the channel name as well as the token avoids treating some future
    #: non-thought channel as reasoning.
    THINK_OPEN = "<|channel>thought"
    THINK_CLOSE = "<channel|>"
    SUPPORTED_MODES = (ReasoningMode.NO_THINKING,
                       ReasoningMode.NATURAL_REASONING)
    #: The delimiter is a composite — the special token `<|channel>` followed by
    #: the channel name `thought` — so the tokens to preserve are named
    #: explicitly rather than derived from THINK_OPEN.
    PRESERVE_TOKENS = ("<|channel>", "<channel|>")
    #: Turn and sequence control, beyond whatever the tokenizer declares.
    CONTROL_TOKENS = ("<|turn>", "<turn|>", "<|think|>")

    #: PRACTICAL context envelope, not the architectural maximum (131k for E4B,
    #: 262k for 12B). See the note in the Qwen adapter: a ceiling derived from
    #: the advertised maximum would be a number the hardware cannot serve and no
    #: trace approaches. Held equal to the other families so the engineering
    #: ceiling is not itself a cross-model confound.
    CONTEXT_LIMIT = 40960

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        return {"enable_thinking":
                reasoning_mode == ReasoningMode.NATURAL_REASONING}

    def normalise_reasoning(self, trace: str) -> str:
        """Drop the channel opener and its channel name from the stored trace."""
        text = trace.lstrip()
        if text.startswith(self.THINK_OPEN):
            text = text[len(self.THINK_OPEN):]
        elif text.startswith("<|channel>"):
            text = text[len("<|channel>"):]
            text = text.split("\n", 1)[1] if "\n" in text else ""
        return text.strip("\n")

    def clean_answer(self, text: str) -> str:
        """The answer channel, with any residual channel scaffolding removed.

        Gemma closes the model turn with `<turn|>`, already stripped as a control
        token. What can still appear is a leading channel header if the model
        opens a second channel for its answer; that header is scaffolding, not
        content, and is removed so the verifier sees prose.
        """
        cleaned = text.strip()
        if cleaned.startswith("<|channel>"):
            cleaned = cleaned[len("<|channel>"):]
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        return cleaned.strip()


class Gemma4_E4B(Gemma4Adapter):
    MODEL_ID = "google/gemma-4-E4B-it"
    #: `Gemma4ForConditionalGeneration` in the checkpoint; the text tower is
    #: `Gemma4ForCausalLM`. E4B does NOT mean 4B stored parameters — the
    #: checkpoint is 14.9 GiB of bf16 weights — so memory is planned from the
    #: measured file size, never from the name.
    TEXT_ONLY_CLASS = "Gemma4ForCausalLM"
    FULL_CLASS = "Gemma4ForConditionalGeneration"


class Gemma4_12B(Gemma4Adapter):
    MODEL_ID = "google/gemma-4-12B-it"
    #: A different architecture from E4B, not merely a larger one:
    #: `gemma4_unified` / `Gemma4UnifiedForConditionalGeneration`. 22.3 GiB of
    #: bf16 weights against a 24 GiB card, so this checkpoint is expected to need
    #: dual-GPU capacity mode; the runner decides that from measurement.
    TEXT_ONLY_CLASS = "Gemma4UnifiedForCausalLM"
    FULL_CLASS = "Gemma4UnifiedForConditionalGeneration"
