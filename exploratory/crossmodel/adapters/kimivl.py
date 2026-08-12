"""Kimi-VL-A3B-Thinking-2506 execution adapter.

Read off the official model card and the checkpoint's own chat template, not
inferred from the other families:

* **The reasoning delimiters are `◁think▷` and `◁/think▷`.** The card ships the
  reference parser verbatim — `extract_thinking_and_summary(text, bot="◁think▷",
  eot="◁/think▷")` — which splits the trace from the summary at exactly those
  markers. `parse_output` below is that function's semantics, with one
  difference: where the card returns the whole text as the summary when no
  marker is present, this adapter returns an EMPTY answer in a thinking mode,
  because a scored scratchpad is worse than a missing datum.

* **There is no reasoning toggle.** The chat template has no `enable_thinking`
  branch; `add_generation_prompt` emits `<|im_assistant|>assistant<|im_middle|>`
  and nothing else. This checkpoint always thinks. The card names a separate
  non-thinking checkpoint (`Kimi-VL-A3B-Instruct`) — a DIFFERENT checkpoint, and
  therefore a different execution condition, never a mode of this one. So
  `SUPPORTED_MODES` holds NATURAL_REASONING alone and the NO_THINKING cell is
  left missing rather than fabricated.

* **The architecture is not in Transformers.** `kimi_vl` is absent from
  transformers 5.15.0's config mapping, so the checkpoint carries its own
  modeling code (`modeling_kimi_vl.py`, `tokenization_moonshot.py`) and requires
  `trust_remote_code=True`. That code was published against transformers 4.48.2;
  whether it still imports under 5.x is an empirical question the Stage B gate
  answers, and a failure there is a BACKEND_BLOCKED result, not a behavioural one.

* **`A3B` is the ACTIVE parameter count, not the total.** The checkpoint is a
  mixture of experts and 30.6 GiB of bf16 weights on disk — more than one 24 GiB
  card holds. Memory is planned from that measurement, and dual-GPU capacity mode
  is expected. Nothing here treats it as a 3B dense model.

* **No CUDA-only dependencies.** The card's vLLM recipe suggests flash-attn;
  that is a CUDA package and installing it on this ROCm host is explicitly not
  done. The adapter asks for the eager attention implementation instead.
"""
from __future__ import annotations

from typing import Any

from crossmodel.adapters.transformers_base import TransformersAdapter
from crossmodel.contract import ReasoningMode


class KimiVLThinkingAdapter(TransformersAdapter):
    MODEL_ID = "moonshotai/Kimi-VL-A3B-Thinking-2506"
    FAMILY = "kimi-vl"
    THINK_OPEN = "◁think▷"
    THINK_CLOSE = "◁/think▷"
    #: Thinking only. See the module docstring: the non-thinking sibling is a
    #: separate checkpoint, not a mode.
    SUPPORTED_MODES = (ReasoningMode.NATURAL_REASONING,)
    #: `◁think▷` is ordinary vocabulary rather than a declared special token, so
    #: naming it here keeps it safe even if the tokenizer registers it later.
    PRESERVE_TOKENS = ("◁think▷", "◁/think▷")
    CONTROL_TOKENS = ("<|im_end|>", "<|im_start|>", "<|im_assistant|>",
                      "<|im_user|>", "<|im_system|>", "<|im_middle|>")
    #: The custom modeling code is the documented path for this architecture.
    LOAD_KWARGS = {"trust_remote_code": True}
    #: No text-only tower is exposed by the remote code; the full multimodal
    #: class is the only entry point, so the vision weights are allocated and
    #: that fact is recorded rather than hidden.
    TEXT_ONLY_CLASS = None
    FULL_CLASS = "AutoModelForCausalLM"

    #: PRACTICAL envelope; the architecture advertises 131,072.
    CONTEXT_LIMIT = 40960

    #: The model card's reference parser reads ONE unbroken generation and
    #: splits it. The template does not pre-open the reasoning block, so nothing
    #: guarantees the trace comes first, and the documented path is the one this
    #: adapter follows rather than a splice borrowed from another family.
    GENERATION_STRATEGY = "single_phase"

    def template_kwargs(self, reasoning_mode: str) -> dict[str, Any]:
        # The template takes no reasoning argument. Passing one would be
        # silently ignored, which is worse than passing none.
        return {}

    @staticmethod
    def _shim_removed_import() -> str:
        """Restore the ONE symbol transformers 5.x removed that this code needs.

        `modeling_kimi_vl.py` was published against transformers 4.48.2 and does:

            from transformers.utils.import_utils import is_torch_fx_available
            if is_torch_fx_available():
                _prepare_4d_causal_attention_mask = torch.fx.wrap(...)

        Transformers 5.15.0 dropped `is_torch_fx_available` along with symbolic
        tracing, so the import raises and the checkpoint cannot load at all. Every
        other name the remote code imports — fourteen of them, checked
        individually — still exists in 5.15.0, so this is the whole gap.

        The shim returns False, which is the truthful answer under 5.x: fx
        tracing is gone. The guarded block then does not run, and all it would
        have done is mark a function as a leaf **for tracing**. Nothing in eager
        generation reads it. So this restores loadability without altering a
        weight, a shape, an attention path or a forward pass — and it is applied
        to the interpreter's view of `transformers`, never to the checkpoint's
        files, which stay byte-identical to the pinned revision.
        """
        from transformers.utils import import_utils

        if hasattr(import_utils, "is_torch_fx_available"):
            return "not needed"
        import_utils.is_torch_fx_available = lambda: False
        return ("transformers.utils.import_utils.is_torch_fx_available = "
                "lambda: False (removed in transformers 5.x; the block it "
                "guards only marks an fx tracing leaf)")

    @staticmethod
    def _restore_declared_rope(config) -> str:
        """Undo transformers 5.x's rope normalisation, which this code misreads.

        The checkpoint declares, verbatim in its own `config.json`:

            "rope_scaling": null,
            "rope_theta": 800000.0

        i.e. **no rope scaling**. Transformers 5.15.0 no longer leaves that as
        `None`; it synthesises `{"rope_theta": 800000.0, "rope_type":
        "default"}`, where `"default"` is its way of spelling the same absence.

        `DeepseekV3Attention._init_rope` was written against the old shape:

            if self.config.rope_scaling is None:   -> plain rotary, base=rope_theta
            else:                                  -> self.config.rope_scaling["type"]

        A synthesised dict is not `None`, so the code takes the scaled branch
        and dies on `KeyError: 'type'`. Restoring `None` puts it back on the
        branch the checkpoint's own config selects.

        This does not choose an architecture — it preserves the declared one.
        `rope_theta` and `max_position_embeddings` are separate attributes and
        are asserted intact afterwards, so the plain-rotary embedding is built
        with exactly the base and window the checkpoint specifies. Contrast the
        Gemma 4 override refused in V12: there the per-layer attributes genuinely
        DIFFERED and collapsing them would have built a different model. Here
        the two spellings denote the same thing and only one is readable by the
        checkpoint's own code.
        """
        text = getattr(config, "text_config", None)
        if text is None:
            return "not needed: no text_config"
        scaling = getattr(text, "rope_scaling", None)
        if scaling is None:
            return "not needed: rope_scaling already None"
        rope_type = str(scaling.get("rope_type", "")).lower()
        if rope_type not in ("default", ""):
            # A checkpoint that really does scale rope must not be silently
            # unscaled. Nothing is touched and the caller sees the real error.
            raise ValueError(
                f"{scaling!r} declares rope_type={rope_type!r}, which is real "
                "scaling — refusing to null it; that would change the model")
        theta, window = text.rope_theta, text.max_position_embeddings
        text.rope_scaling = None
        assert text.rope_theta == theta and \
            text.max_position_embeddings == window, \
            "nulling rope_scaling disturbed rope_theta or the context window"
        return (f"text_config.rope_scaling {scaling} -> None (checkpoint "
                f"declares null; transformers 5.x synthesises rope_type="
                f"'default', which the checkpoint's own _init_rope cannot "
                f"read); rope_theta={theta} and max_position_embeddings="
                f"{window} preserved")

    def _load_weights(self, revision: str, dtype):
        """Load through the checkpoint's own remote code, eager attention.

        `attn_implementation="eager"` is set explicitly: the default resolution
        can select a fused kernel that is CUDA-only or unsupported on gfx1100,
        and a backend that silently picks a different attention path is a
        changed execution condition.
        """
        import transformers

        shims = [self._shim_removed_import()]

        # The config is loaded, repaired and passed in explicitly, rather than
        # letting `from_pretrained` fetch it internally, so the rope repair is
        # provably applied to the object the model is actually built from.
        config = transformers.AutoConfig.from_pretrained(
            self.MODEL_ID, revision=revision, **self.LOAD_KWARGS)
        shims.append(self._restore_declared_rope(config))
        self.compatibility_shim = "; ".join(
            s for s in shims if not s.startswith("not needed"))

        kwargs = dict(config=config, revision=revision, dtype=dtype,
                      device_map=self._device_map,
                      attn_implementation="eager", **self.LOAD_KWARGS)
        model = transformers.AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID, **kwargs)
        return model, "AutoModelForCausalLM(trust_remote_code)", True
