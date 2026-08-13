"""Reasoning-mode and chat-template behaviour.

The failure this guards against is the quietest one in the study. Jinja
**silently ignores unknown kwargs**, so a chat-template switch that is renamed,
absent, or misspelled produces no error — the run simply executes whatever the
template defaults to, and records it under the condition you asked for. Gemma 4
defaults thinking OFF and Qwen 3.5 defaults it ON, so the same silent bug
corrupts two families in opposite directions.

Runs on CPU with no GPU stack: `render_prompt` and `verify_template_switch`
touch only the tokenizer interface, which is faked here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import engine                               # noqa: E402
from vllm_backend.contract import GenerationRequest           # noqa: E402
from vllm_backend.reasoning import DelimiterParser, split     # noqa: E402
from vllm_backend.registry import (REGISTRY, ModelCard,       # noqa: E402
                                   ReasoningMode, get)


class LiveSwitchTokenizer:
    """A template whose `enable_thinking` kwarg actually does something."""

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=True, **kwargs):
        body = "".join(f"<{m['role']}>{m['content']}" for m in messages)
        if kwargs.get("enable_thinking"):
            return body + "<assistant><think>"
        return body + "<assistant>"

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))


class DeadSwitchTokenizer:
    """A template that ignores every kwarg — the silent-failure case."""

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=True, **kwargs):
        return "".join(f"<{m['role']}>{m['content']}" for m in messages)

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))


@pytest.fixture
def request_() -> GenerationRequest:
    return GenerationRequest(row_id="r1", user_prompt="why is the sky blue?",
                             system_message="Answer only.")


class TestTemplateSwitchLiveness:
    def test_a_live_switch_passes_and_records_evidence(self, request_) -> None:
        evidence = engine.verify_template_switch(
            LiveSwitchTokenizer(), request_, {"enable_thinking": True})
        checked = evidence["checked"]
        assert len(checked) == 1
        assert checked[0]["kwarg"] == "enable_thinking"
        assert checked[0]["template_differs"] is True

    def test_an_inert_switch_is_refused_loudly(self, request_) -> None:
        """This is the whole point: a template that ignores the kwarg must stop
        the run, not silently record the wrong reasoning condition."""
        with pytest.raises(engine.TemplateSwitchError, match="does not change"):
            engine.verify_template_switch(
                DeadSwitchTokenizer(), request_, {"enable_thinking": True})

    def test_non_boolean_kwargs_are_not_switch_checked(self, request_) -> None:
        """Only booleans have a meaningful negation to compare against."""
        evidence = engine.verify_template_switch(
            DeadSwitchTokenizer(), request_, {"chat_format": "harmony"})
        assert evidence["checked"] == []

    def test_switch_is_checked_in_both_directions(self, request_) -> None:
        for declared in (True, False):
            evidence = engine.verify_template_switch(
                LiveSwitchTokenizer(), request_, {"enable_thinking": declared})
            assert evidence["checked"][0]["declared"] is declared


class TestPromptRendering:
    def test_system_turn_included_only_when_present(self) -> None:
        tokenizer = LiveSwitchTokenizer()
        with_system = engine.render_prompt(
            tokenizer, GenerationRequest(row_id="a", user_prompt="u",
                                         system_message="s"), {})
        without = engine.render_prompt(
            tokenizer, GenerationRequest(row_id="a", user_prompt="u"), {})
        assert "<system>s" in with_system
        assert "<system>" not in without

    def test_template_kwargs_reach_the_tokenizer(self, request_) -> None:
        rendered = engine.render_prompt(LiveSwitchTokenizer(), request_,
                                        {"enable_thinking": True})
        assert rendered.endswith("<think>")


class TestModeDeclarations:
    """Model-specific reasoning facts are declarative and internally consistent."""

    def test_mirrored_reasoning_mode_values_match_the_scientific_contract(self) -> None:
        """`vllm_backend` deliberately does not import `crossmodel` (different
        interpreter), so the mirrored labels are asserted equal instead."""
        from crossmodel.contract import ReasoningMode as Scientific

        for name in ("NO_THINKING", "LIMITED_REASONING", "NATURAL_REASONING",
                     "THINKING_ENABLED_BOUNDED"):
            assert getattr(ReasoningMode, name) == getattr(Scientific, name), (
                f"{name} drifted between the backend and the scientific contract")

    @pytest.mark.parametrize("model_id", sorted(REGISTRY))
    def test_every_supported_mode_has_template_kwargs_or_none_at_all(
            self, model_id: str) -> None:
        card = get(model_id)
        if not card.template_kwargs_by_mode:
            # Kimi-VL: the template takes no reasoning argument at all. Passing
            # one would be silently ignored, which is worse than passing none.
            return
        for mode in card.supported_modes:
            assert mode in card.template_kwargs_by_mode, (
                f"{model_id} supports {mode} but declares no template kwargs "
                f"for it, so the mode would fall back to the template default")

    def test_kimi_vl_has_no_non_thinking_mode(self) -> None:
        card = get("moonshotai/Kimi-VL-A3B-Thinking-2506")
        assert not card.supports(ReasoningMode.NO_THINKING)
        assert card.template_kwargs_by_mode == {}

    def test_gemma_and_qwen_declare_different_delimiters(self) -> None:
        """Assuming Qwen's delimiters for Gemma would have scored scratchpads."""
        qwen = get("Qwen/Qwen3.5-4B")
        gemma = get("google/gemma-4-E4B-it")
        assert (qwen.think_open, qwen.think_close) == ("<think>", "</think>")
        assert (gemma.think_open, gemma.think_close) == ("<|channel>thought",
                                                         "<channel|>")

    def test_kimi_vl_has_no_registered_parser_and_uses_its_own_delimiters(self) -> None:
        card = get("moonshotai/Kimi-VL-A3B-Thinking-2506")
        assert card.reasoning_parser is None
        assert (card.think_open, card.think_close) == ("◁think▷", "◁/think▷")


class TestDelimiterFallback:
    """`build_parser` with no registered name must use the card's delimiters."""

    def test_unregistered_checkpoint_gets_a_delimiter_parser(self) -> None:
        from vllm_backend.reasoning import build_parser

        card = ModelCard(model_id="x/y", family="f", reasoning_parser=None,
                         think_open="◁think▷", think_close="◁/think▷")
        parser, label = build_parser(None, None, card.think_open,
                                     card.think_close)
        assert isinstance(parser, DelimiterParser)
        assert "delimiters" in label
        assert split(parser, "◁think▷musing◁/think▷Tokyo") == ("musing", "Tokyo")


class TestPreOpenedTemplateRepair:
    """A template that pre-opens `<think>` must not leak reasoning into the answer.

    Regression, found by running the consolidated backend against
    Qwen3-4B-Thinking-2507 on vLLM 0.15.1. Its chat template renders
    `...<|im_start|>assistant\\n<think>\\n`, so the OPENING marker lives in the
    prompt and never appears in the generation. vLLM's `qwen3` parser searches
    the output for that marker, fails, and returns the entire reasoning trace as
    content — with `outcome == OK`, so nothing looks wrong. All four probe rows
    contained `</think>` and no `<think>`, and 100% of the trace was scored as
    the answer.

    This bug predates the consolidation (`crossmodel/vllm_tp2.py` used the same
    parser-then-split path); having one splitter is what makes fixing it a
    one-line change instead of an eight-file sweep.
    """

    class LeakyParser:
        """Stands in for vLLM's qwen3 parser on a pre-opened template."""

        def extract_reasoning(self, text, request=None):
            return "", text

    #: A real generation shape: trace, close marker, then the answer.
    RAW = ("Hmm, the user asks for the capital of France.\n"
           "Just \"Paris\" will do.\n</think>\n\nParis")

    def test_leak_is_repaired_when_delimiters_are_known(self) -> None:
        reasoning, answer = split(self.LeakyParser(), self.RAW,
                                  "<think>", "</think>")
        assert answer == "Paris"
        assert "Hmm, the user asks" in reasoning
        assert "</think>" not in answer

    def test_without_delimiters_the_leak_is_reproduced(self) -> None:
        """Proves the repair is what fixes it, not something else."""
        reasoning, answer = split(self.LeakyParser(), self.RAW)
        assert reasoning == ""
        assert "Hmm, the user asks" in answer

    def test_repair_does_not_fire_when_the_parser_succeeded(self) -> None:
        class GoodParser:
            def extract_reasoning(self, text, request=None):
                return "trace", "ANSWER"

        assert split(GoodParser(), self.RAW, "<think>", "</think>") == (
            "trace", "ANSWER")

    def test_repair_does_not_fire_without_a_close_delimiter(self) -> None:
        """No close marker means the split did not provably fail; leave it."""
        reasoning, answer = split(self.LeakyParser(), "plain answer text",
                                  "<think>", "</think>")
        assert reasoning == ""
        assert answer == "plain answer text"

    def test_delimiter_parser_already_handled_this_case(self) -> None:
        """The repair reuses DelimiterParser precisely because it was correct."""
        parser = DelimiterParser("<think>", "</think>")
        reasoning, answer = parser.extract_reasoning(self.RAW)
        assert answer == "Paris"
        assert "Hmm" in reasoning
