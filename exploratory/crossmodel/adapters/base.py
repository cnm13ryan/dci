"""The common execution contract every checkpoint is driven through.

The operating principle of the cross-model study is that the SCIENCE is fixed
and the EXECUTION may differ. This module is the seam between the two. Above it,
the runner and the scoring code know about tasks, arms, backgrounds and final
answers; below it, a subclass knows about `<think>` versus `◁think▷`, about
whether a chat template pre-opens the reasoning block, and about which
`device_map` a 22 GiB checkpoint needs on two 24 GiB cards.

Two rules keep that seam honest:

1. **Nothing family-specific may leak upward.** The scoring path receives
   `Generation.final_answer` and never learns which family produced it. If a
   verifier ever needed to know, the separation would have failed.

2. **Nothing scientific may leak downward.** An adapter chooses HOW to render a
   prompt and HOW to split a response; it never chooses the decoding parameters,
   the answer allowance, the seeds, or which rows to run. Those come from
   `crossmodel.contract` for every checkpoint alike.

The reasoning/answer separation is a **two-phase splice**, inherited from the
canonical vLLM run (`vllm_backend/natural_reasoning.py`) so the cross-model runs
keep the study's existing semantics:

    phase 1  generate with a stop at the family's think-close marker
    phase 2  re-prompt with prompt + reasoning + think-close, generate the answer

This is deliberately not "generate one long string and split it". The splice
guarantees the answer allowance is exactly `ANSWER_TOKENS` in every condition and
every model, and it makes natural closure directly observable: the reasoning
phase either stopped on the marker (closed) or ran into the ceiling (cap hit).
"""
from __future__ import annotations

import abc
import gc
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from crossmodel.contract import ReasoningMode


# ------------------------------------------------------------------- results
@dataclass(frozen=True)
class GenerationConfig:
    """Decoding, identical across checkpoints; only the ceiling is per-model."""

    reasoning_mode: str
    max_answer_tokens: int
    temperature: float
    top_p: float
    top_k: int
    #: The ENGINEERING CEILING for NATURAL_REASONING, or the assigned budget for
    #: LIMITED_REASONING. For NO_THINKING there is no reasoning phase at all.
    #: A ceiling is a safety bound, never a dose — see `assigned_reasoning_budget`.
    max_reasoning_tokens: int = 0

    @property
    def assigned_reasoning_budget(self) -> Optional[int]:
        """`b`, the treatment. `None` under natural reasoning, and that is the point.

        Encoding natural reasoning as "b = 39550" would turn a safety ceiling
        into a dose and invite a reader to place it on a budget axis. Natural
        reasoning has no assigned budget; it has a ceiling it must not reach.
        """
        if self.reasoning_mode == ReasoningMode.NO_THINKING:
            return 0
        if self.reasoning_mode == ReasoningMode.LIMITED_REASONING:
            return self.max_reasoning_tokens
        return None

    @property
    def engineering_ceiling(self) -> Optional[int]:
        if self.reasoning_mode in ReasoningMode.THINKING:
            return self.max_reasoning_tokens
        return None


@dataclass
class Generation:
    """One completed generation, family-agnostic from here upward."""

    prompt: str
    raw_generation: str
    reasoning_text: str
    final_answer: str
    reasoning_tokens: int
    final_answer_tokens: int
    finish_reason: str
    natural_reasoning_closed: bool
    reasoning_cap_hit: bool
    answer_truncated: bool
    #: Did the model open a reasoning block at all? Distinct from "closed it".
    #: A checkpoint whose template leaves thinking optional may simply decline to
    #: think on an easy prompt, and that is a property of the checkpoint, not a
    #: parser failure — but it is also not a closure, so the two are kept apart.
    reasoning_emitted: bool = True
    #: The splice force-closed a trace that had not finished, and the model then
    #: continued thinking, closed AGAIN, and re-answered. The answer channel is
    #: repaired by taking the text after the final close, but the row is marked:
    #: this is the "forced-close artefact" that makes a reasoning condition
    #: invalid, and it must never be read as a behavioural failure.
    forced_close_artefact: bool = False
    seed_reasoning: Optional[int] = None
    seed_answer: Optional[int] = None
    batch_seed: Optional[int] = None
    latency_seconds: float = 0.0
    technical_failure: bool = False
    technical_failure_reason: str = ""

    @property
    def total_generated_tokens(self) -> int:
        return self.reasoning_tokens + self.final_answer_tokens

    @property
    def answer_empty(self) -> bool:
        return not self.final_answer.strip()

    @property
    def generation_ok(self) -> bool:
        return not self.technical_failure and not self.answer_empty


# --------------------------------------------------------------- the contract
class ModelAdapter(abc.ABC):
    """One checkpoint, executed faithfully, behind one interface."""

    #: Hub id. Never a local path: provenance must survive a cache move.
    MODEL_ID: str = ""
    #: Coarse family label, for grouping in the results — never for scoring.
    FAMILY: str = ""
    #: The reasoning modes this checkpoint NATIVELY supports. A mode absent here
    #: is a missing cell in the design, never something to emulate by truncating
    #: a trace or by prompting the model to "not think".
    SUPPORTED_MODES: tuple[str, ...] = ()
    #: The family's reasoning delimiters, as they appear in decoded text.
    THINK_OPEN: str = "<think>"
    THINK_CLOSE: str = "</think>"
    #: Context window used to derive the natural-reasoning engineering ceiling.
    CONTEXT_LIMIT: int = 32768
    #: Fraction of the window held back rather than trusting the edge.
    SAFETY_FRACTION: float = 0.02

    def __init__(self, revision: Optional[str] = None,
                 device_map: Any = None, dtype: str = "bfloat16"):
        self._revision = revision
        self._device_map = device_map
        self._dtype = dtype
        self._model = None
        self._tokenizer = None
        self._load_metadata: dict[str, Any] = {}

    # -- identity ---------------------------------------------------------
    @abc.abstractmethod
    def resolve_revision(self) -> str:
        """The exact commit sha this run will execute. Never an alias.

        Must raise rather than fall back to `main`: a run whose checkpoint
        identity cannot be established is not a scientific run.
        """

    # -- lifecycle --------------------------------------------------------
    @abc.abstractmethod
    def load(self) -> None:
        """Load weights and tokenizer at the resolved revision."""

    def unload(self) -> None:
        """Release the weights and return the VRAM, best effort."""
        import torch

        self._model = None
        self._tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

    # -- rendering --------------------------------------------------------
    @abc.abstractmethod
    def render_prompt(self, messages: Sequence[dict[str, str]],
                      reasoning_mode: str) -> str:
        """Apply the checkpoint's own chat template in the requested mode."""

    # -- generation -------------------------------------------------------
    @abc.abstractmethod
    def generate(self, prompts: Sequence[str], seeds: Sequence[tuple[int, int]],
                 generation_config: GenerationConfig) -> list[Generation]:
        """Run the two-phase splice over a batch of rendered prompts.

        `seeds` carries `(reasoning_seed, answer_seed)` per prompt. Batch
        composition must be a deterministic function of the caller's ordering;
        the caller guarantees that ordering is derived from row identity rather
        than from device or arrival order.
        """

    # -- parsing ----------------------------------------------------------
    @abc.abstractmethod
    def parse_output(self, raw_output: str, reasoning_mode: str
                     ) -> tuple[str, str]:
        """Split a raw generation into `(reasoning_text, final_answer)`.

        Must be total: a response with no reasoning markers still has to yield a
        final answer, and a response that is nothing but reasoning must yield an
        empty answer rather than silently returning the trace as the answer.
        """

    # -- the accessors named by the adapter contract ----------------------
    # They take the Generation rather than reading adapter state: a stateful
    # `get_final_answer()` is a race waiting to happen once anything batches.
    def get_reasoning_text(self, generation: Generation) -> str:
        return generation.reasoning_text

    def get_final_answer(self, generation: Generation) -> str:
        return generation.final_answer

    def get_reasoning_tokens(self, generation: Generation) -> int:
        return generation.reasoning_tokens

    def get_final_answer_tokens(self, generation: Generation) -> int:
        return generation.final_answer_tokens

    def natural_reasoning_closed(self, generation: Generation) -> bool:
        return generation.natural_reasoning_closed

    def reasoning_cap_hit(self, generation: Generation) -> bool:
        return generation.reasoning_cap_hit

    def answer_truncated(self, generation: Generation) -> bool:
        return generation.answer_truncated

    # -- provenance -------------------------------------------------------
    def execution_metadata(self) -> dict[str, Any]:
        """Everything that defines the execution condition E for this adapter."""
        import torch
        import transformers

        meta = {
            "model_id": self.MODEL_ID,
            "model_revision": self._revision,
            "model_family": self.FAMILY,
            "backend": "transformers",
            "backend_version": transformers.__version__,
            "torch_version": torch.__version__,
            "dtype": self._dtype,
            "quantization": "none",
            "device_configuration": self._describe_devices(),
            "think_open": self.THINK_OPEN,
            "think_close": self.THINK_CLOSE,
            "context_limit": self.CONTEXT_LIMIT,
            "supported_reasoning_modes": list(self.SUPPORTED_MODES),
            "adapter_class": type(self).__name__,
        }
        # A shim applied to make a checkpoint load at all is part of the
        # execution condition and is recorded, never left implicit.
        if getattr(self, "compatibility_shim", ""):
            meta["compatibility_shim"] = self.compatibility_shim
        meta.update(self._load_metadata)
        return meta

    def _describe_devices(self) -> str:
        if self._model is None:
            return str(self._device_map)
        try:
            devices = sorted({str(p.device) for p in self._model.parameters()})
        except Exception:
            return str(self._device_map)
        return ",".join(devices)

    # -- the natural-reasoning envelope -----------------------------------
    def natural_reasoning_ceiling(self, prompts: Sequence[str],
                                  answer_tokens: int) -> dict[str, Any]:
        """A ceiling derived from THIS model's context envelope.

        Not transferred from another checkpoint, and not a round number: a round
        number would be a guess about how much room is enough. The requirement is
        a bound the model almost never touches, so the run can say the reasoning
        finished on its own rather than that the experiment stopped it.
        """
        import math

        tokenizer = self._require_tokenizer()
        lengths = [len(tokenizer.encode(p, add_special_tokens=False))
                   for p in prompts]
        longest = max(lengths)
        control = len(tokenizer.encode(f"{self.THINK_CLOSE}\n\n",
                                       add_special_tokens=False))
        safety = math.ceil(self.CONTEXT_LIMIT * self.SAFETY_FRACTION)
        ceiling = self.CONTEXT_LIMIT - longest - answer_tokens - control - safety
        if ceiling <= 0:
            raise ValueError(
                f"{self.MODEL_ID}: the context envelope leaves no room for "
                f"reasoning (limit {self.CONTEXT_LIMIT}, longest prompt "
                f"{longest}, answer {answer_tokens})")
        return {"context_limit": self.CONTEXT_LIMIT,
                "longest_prompt_tokens": longest,
                "median_prompt_tokens": sorted(lengths)[len(lengths) // 2],
                "answer_allowance": answer_tokens,
                "control_tokens": control, "safety_margin": safety,
                "derived_ceiling": ceiling}

    # -- helpers ----------------------------------------------------------
    def _require_tokenizer(self):
        if self._tokenizer is None:
            raise RuntimeError(f"{self.MODEL_ID}: load() has not been called")
        return self._tokenizer

    def _require_model(self):
        if self._model is None:
            raise RuntimeError(f"{self.MODEL_ID}: load() has not been called")
        return self._model

    def supports(self, reasoning_mode: str) -> bool:
        return reasoning_mode in self.SUPPORTED_MODES

    def require_mode(self, reasoning_mode: str) -> None:
        if not self.supports(reasoning_mode):
            raise ValueError(
                f"{self.MODEL_ID} does not natively support {reasoning_mode}. "
                "Emulating it would make the reasoning condition an artefact of "
                "this harness rather than a property of the checkpoint; the cell "
                "is left missing instead.")
