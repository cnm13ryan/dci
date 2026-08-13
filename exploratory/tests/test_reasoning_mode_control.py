"""Reasoning-mode control must be declared per checkpoint, or refused.

The regression this file exists for: `Qwen/Qwen3-4B` and
`Qwen/Qwen3-4B-Instruct-2507` produced every reasoning result in this study and
neither had a `ModelCard`. They therefore fell back to a card whose
`template_kwargs_by_mode` was empty, so `enable_thinking` was never passed —
NO_THINKING and natural reasoning would have rendered IDENTICALLY on Qwen3-4B,
and `verify_template_switch`, guarded on `if template_kwargs:`, disappeared in
exactly that case. That produces scientifically invalid data with no error.

Three properties are pinned here:

1. the two checkpoints are registered, with the modes and kwargs their templates
   actually implement;
2. an unregistered checkpoint raises rather than defaulting to "no kwargs";
3. the switch check cannot be skipped by supplying an empty mapping.

The template facts asserted below were read off the cached tokenizers by
rendering, not inferred from the checkpoint names. `TestAgainstRealTemplates`
re-derives them and is skipped where transformers or the weights are absent, so
the suite still runs on a machine with neither.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import engine, registry  # noqa: E402
from vllm_backend.contract import GenerationRequest  # noqa: E402
from vllm_backend.registry import (  # noqa: E402
    ReasoningMode, UnregisteredReasoningControl, get, get_or_default)

CANONICAL = "Qwen/Qwen3-4B"
LADDER = "Qwen/Qwen3-4B-Instruct-2507"


class TestTheTwoCheckpointsAreRegistered:
    """Both carry published results; neither may rely on a default."""

    @pytest.mark.parametrize("model_id", [CANONICAL, LADDER])
    def test_registered(self, model_id: str) -> None:
        assert model_id in registry.REGISTRY
        assert get(model_id).reasoning_control_declared is True

    def test_the_hybrid_supports_every_reasoning_mode(self) -> None:
        card = get(CANONICAL)
        for mode in (ReasoningMode.NO_THINKING, ReasoningMode.LIMITED_REASONING,
                     ReasoningMode.NATURAL_REASONING,
                     ReasoningMode.THINKING_ENABLED_BOUNDED):
            assert card.supports(mode), f"{mode} missing from {CANONICAL}"

    def test_no_thinking_disables_thinking(self) -> None:
        assert get(CANONICAL).template_kwargs(
            ReasoningMode.NO_THINKING) == {"enable_thinking": False}

    def test_natural_reasoning_enables_thinking(self) -> None:
        assert get(CANONICAL).template_kwargs(
            ReasoningMode.NATURAL_REASONING) == {"enable_thinking": True}

    def test_limited_reasoning_is_supported_and_enables_thinking(self) -> None:
        """The capped ladder is the mode the fallback card silently removed."""
        card = get(CANONICAL)
        assert card.supports(ReasoningMode.LIMITED_REASONING)
        assert card.template_kwargs(
            ReasoningMode.LIMITED_REASONING) == {"enable_thinking": True}

    def test_the_conditions_are_declared_differently(self) -> None:
        """The bug in one assertion: thinking and non-thinking must not agree."""
        card = get(CANONICAL)
        assert (card.template_kwargs(ReasoningMode.NO_THINKING)
                != card.template_kwargs(ReasoningMode.NATURAL_REASONING))

    def test_the_instruct_checkpoint_is_non_thinking_only(self) -> None:
        """Its template has no reasoning variable, so it has one mode."""
        card = get(LADDER)
        assert card.supported_modes == (ReasoningMode.NO_THINKING,)
        assert card.supports(ReasoningMode.NATURAL_REASONING) is False
        assert card.template_kwargs(ReasoningMode.NO_THINKING) == {}
        assert card.reasoning_parser is None


class TestUnregisteredCheckpointsFailClosed:
    def test_the_fallback_declares_no_reasoning_control(self) -> None:
        assert get_or_default("some/unknown-model").reasoning_control_declared is False

    def test_asking_for_template_kwargs_raises(self) -> None:
        card = get_or_default("some/unknown-model")
        with pytest.raises(UnregisteredReasoningControl):
            card.template_kwargs(ReasoningMode.NO_THINKING)

    def test_it_does_not_quietly_return_an_empty_mapping(self) -> None:
        """`{}` would mean "this template takes no reasoning argument" — a claim
        about the checkpoint that a fallback cannot make."""
        card = get_or_default("some/unknown-model")
        try:
            result = card.template_kwargs(ReasoningMode.NATURAL_REASONING)
        except UnregisteredReasoningControl:
            return
        pytest.fail(f"returned {result!r} instead of refusing")

    def test_the_fallback_supports_no_mode(self) -> None:
        card = get_or_default("some/unknown-model")
        for mode in (ReasoningMode.NO_THINKING, ReasoningMode.LIMITED_REASONING,
                     ReasoningMode.NATURAL_REASONING):
            assert card.supports(mode) is False

    def test_the_error_names_the_checkpoint_and_the_remedy(self) -> None:
        with pytest.raises(UnregisteredReasoningControl) as caught:
            get_or_default("some/unknown-model").template_kwargs("NO_THINKING")
        message = str(caught.value)
        assert "some/unknown-model" in message
        assert "ModelCard" in message

    def test_strict_lookup_still_raises_for_unknown(self) -> None:
        with pytest.raises(KeyError):
            get("some/unknown-model")


class _Tokenizer:
    """Minimal chat template with a live `enable_thinking` switch."""

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=True, **kwargs) -> str:
        body = "".join(f"<{m['role']}>{m['content']}" for m in messages)
        if kwargs.get("enable_thinking") is False:
            return body + "<assistant><think>\n\n</think>\n\n"
        return body + "<assistant>"

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))


class _InertTokenizer(_Tokenizer):
    """A template that ignores the switch — the silent-wrong-condition case."""

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=True, **kwargs) -> str:
        return "".join(f"<{m['role']}>{m['content']}" for m in messages) + "<assistant>"


def _request() -> GenerationRequest:
    return GenerationRequest(row_id="r1", user_prompt="explain a corkscrew",
                             system_message="", scientific_seed=1,
                             answer_seed=2, identity={})


class TestTheSwitchCheckCannotBeSkipped:
    def test_a_live_switch_passes_and_records_evidence(self) -> None:
        evidence = engine.verify_template_switch(
            _Tokenizer(), _request(), {"enable_thinking": False},
            get(CANONICAL), ReasoningMode.NO_THINKING)
        assert evidence["checked"][0]["template_differs"] is True

    def test_an_inert_switch_is_refused(self) -> None:
        with pytest.raises(engine.TemplateSwitchError):
            engine.verify_template_switch(
                _InertTokenizer(), _request(), {"enable_thinking": False},
                get(CANONICAL), ReasoningMode.NO_THINKING)

    def test_empty_kwargs_are_accepted_only_when_no_switch_is_declared(self) -> None:
        """Qwen3-4B-Instruct-2507 and Kimi-VL: genuinely no reasoning argument."""
        evidence = engine.verify_template_switch(
            _InertTokenizer(), _request(), {}, get(LADDER),
            ReasoningMode.NO_THINKING)
        assert evidence["no_reasoning_argument"] is True

    def test_empty_kwargs_are_refused_when_the_card_declares_switches(self) -> None:
        """The regression shape: a mode that would inherit the template default."""
        with pytest.raises(engine.TemplateSwitchError) as caught:
            engine.verify_template_switch(
                _Tokenizer(), _request(), {}, get(CANONICAL),
                ReasoningMode.NO_THINKING)
        assert "NO_THINKING" in str(caught.value)


class TestRenderedPromptsDifferWhereTheConditionDoes:
    def test_no_thinking_and_natural_render_differently(self) -> None:
        card, tokenizer = get(CANONICAL), _Tokenizer()
        rendered = {
            mode: engine.render_prompt(tokenizer, _request(),
                                       card.template_kwargs(mode))
            for mode in (ReasoningMode.NO_THINKING,
                         ReasoningMode.NATURAL_REASONING)}
        assert (rendered[ReasoningMode.NO_THINKING]
                != rendered[ReasoningMode.NATURAL_REASONING])


try:                                            # optional: the study venv has no
    import transformers                         # transformers, the vLLM one does
except ImportError:                             # noqa: BLE001
    transformers = None


@pytest.mark.skipif(transformers is None,
                    reason="transformers is not installed in this interpreter")
class TestAgainstRealTemplates:
    """Re-derive the registry's claims from the actual cached tokenizers.

    A card is only as good as the template it describes, and these are the facts
    that cannot be guessed from a checkpoint name.
    """

    @staticmethod
    def _tokenizer(model_id: str):
        try:
            return transformers.AutoTokenizer.from_pretrained(model_id)
        except Exception as error:                       # not cached on this host
            pytest.skip(f"{model_id} unavailable: {type(error).__name__}")

    @staticmethod
    def _render(tokenizer, **kwargs) -> str:
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": "explain a corkscrew"}],
            tokenize=False, add_generation_prompt=True, **kwargs)

    def test_the_hybrid_switch_is_live(self) -> None:
        tokenizer = self._tokenizer(CANONICAL)
        card = get(CANONICAL)
        thinking = self._render(
            tokenizer, **card.template_kwargs(ReasoningMode.NATURAL_REASONING))
        not_thinking = self._render(
            tokenizer, **card.template_kwargs(ReasoningMode.NO_THINKING))
        assert thinking != not_thinking, (
            "enable_thinking is inert on the checkpoint the reasoning line runs "
            "on; the registry entry is wrong")

    def test_no_thinking_pre_closes_the_channel(self) -> None:
        """How this template implements it: a closed empty block, not omission."""
        tokenizer = self._tokenizer(CANONICAL)
        rendered = self._render(tokenizer, **get(CANONICAL).template_kwargs(
            ReasoningMode.NO_THINKING))
        assert get(CANONICAL).think_close in rendered

    def test_the_instruct_template_really_has_no_switch(self) -> None:
        """Justifies declaring empty kwargs rather than passing an inert one."""
        tokenizer = self._tokenizer(LADDER)
        assert (self._render(tokenizer, enable_thinking=True)
                == self._render(tokenizer, enable_thinking=False))

    def test_the_switch_check_agrees_with_the_real_template(self) -> None:
        tokenizer = self._tokenizer(CANONICAL)
        card = get(CANONICAL)
        for mode in (ReasoningMode.NO_THINKING, ReasoningMode.NATURAL_REASONING,
                     ReasoningMode.LIMITED_REASONING):
            engine.verify_template_switch(tokenizer, _request(),
                                          card.template_kwargs(mode), card, mode)
