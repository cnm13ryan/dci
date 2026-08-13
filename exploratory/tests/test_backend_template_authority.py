"""The backend is the one authority on chat-template behaviour.

Model loading, template interpretation, reasoning-mode validation and inference
must be the same code path. If validation renders templates its own way, it can
resolve a different revision, a different `trust_remote_code` decision or a
different chat template from the one inference will use — and then it certifies
a template no run ever renders, which is worse than not checking.

So these tests go through `engine.load_tokenizer` and
`engine.validate_reasoning_control`, the same functions `engine.run` calls
before it generates. They need the real weights' tokenizer files and an
interpreter with vLLM or transformers, so they skip where those are absent; the
schema and registry logic they sit on top of is unit-tested separately and runs
everywhere.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend import engine                                   # noqa: E402
from vllm_backend.contract import GenerationRequest               # noqa: E402
from vllm_backend.registry import ReasoningMode, get              # noqa: E402

CANONICAL = "Qwen/Qwen3-4B"          # hybrid: the switch is live
LADDER = "Qwen/Qwen3-4B-Instruct-2507"   # no reasoning channel at all
PRE_OPENING = "Qwen/Qwen3-4B-Thinking-2507"   # renders `<think>` into the prompt


def _tokenizer(model_id: str):
    """Through the backend, never `transformers.AutoTokenizer` directly."""
    from vllm_backend.registry import get_or_default
    try:
        return engine.load_tokenizer(get_or_default(model_id))
    except Exception as error:                          # noqa: BLE001
        pytest.skip(f"{model_id} unavailable here: {type(error).__name__}")


def _request() -> GenerationRequest:
    return GenerationRequest(row_id="r1", scientific_seed=1, answer_seed=2,
                             user_prompt="Explain how a corkscrew removes a cork.",
                             system_message="", identity={})


class TestTokenizerAcquisitionIsTheBackends:
    def test_it_records_how_the_tokenizer_was_obtained(self) -> None:
        """Provenance, so a fallback acquisition is never silently trusted."""
        tokenizer = _tokenizer(CANONICAL)
        assert getattr(tokenizer, "_dci_acquisition", None)

    def test_it_prefers_vllms_own_utility_and_admits_when_it_cannot(self) -> None:
        """Both branches asserted, against the constants rather than substrings.

        The earlier form skipped unless "vllm" appeared in the acquisition
        string -- which it does in the FALLBACK string "(vllm util absent)", so
        the skip never fired and the assertion failed under vLLM 0.27, where the
        utility has moved. Whichever branch this interpreter takes, the record
        must name it exactly: a template certified through the fallback must
        never be mistaken for one certified through the engine's own path.
        """
        acquisition = _tokenizer(CANONICAL)._dci_acquisition
        if engine.vllm_tokenizer_utility_available():
            assert acquisition == engine.ACQUIRED_BY_VLLM
        else:
            assert acquisition == engine.ACQUIRED_BY_FALLBACK

    def test_the_two_acquisitions_are_not_confusable_by_substring(self) -> None:
        """The regression: neither constant may contain the other."""
        vllm_path, fallback = engine.ACQUIRED_BY_VLLM, engine.ACQUIRED_BY_FALLBACK
        assert vllm_path != fallback
        assert vllm_path not in fallback and fallback not in vllm_path
        # And the discriminator a reader would reach for first must actually
        # discriminate, which "vllm" does not.
        assert ("vllm" in vllm_path) and ("vllm" in fallback)


class TestTheCardIsValidatedAgainstTheRealTemplate:
    def test_the_hybrid_card_validates_every_mode_it_declares(self) -> None:
        card = get(CANONICAL)
        evidence = engine.validate_reasoning_control(
            card, _tokenizer(CANONICAL), _request())
        assert set(evidence["modes"]) == set(card.supported_modes)
        assert evidence["modes_render_distinctly"] is True

    def test_no_thinking_and_natural_render_differently_on_the_real_template(self) -> None:
        """The regression, asserted against the actual checkpoint."""
        card, tokenizer = get(CANONICAL), _tokenizer(CANONICAL)
        thinking = engine.render_prompt(
            tokenizer, _request(),
            card.template_kwargs(ReasoningMode.NATURAL_REASONING))
        not_thinking = engine.render_prompt(
            tokenizer, _request(),
            card.template_kwargs(ReasoningMode.NO_THINKING))
        assert thinking != not_thinking

    def test_no_thinking_pre_closes_the_channel(self) -> None:
        """How this template implements it: a closed empty block, not omission."""
        card = get(CANONICAL)
        rendered = engine.render_prompt(
            _tokenizer(CANONICAL), _request(),
            card.template_kwargs(ReasoningMode.NO_THINKING))
        assert card.think_close in rendered

    def test_the_instruct_card_validates_as_having_no_switch(self) -> None:
        evidence = engine.validate_reasoning_control(
            get(LADDER), _tokenizer(LADDER), _request())
        mode = evidence["modes"][ReasoningMode.NO_THINKING]
        assert mode["no_reasoning_argument"] is True

    def test_declaring_a_switch_the_instruct_template_lacks_is_refused(self) -> None:
        """Proves the check would catch a wrong card, not just pass a right one."""
        from dataclasses import replace
        wrong = replace(get(LADDER), template_kwargs_by_mode={
            ReasoningMode.NO_THINKING: {"enable_thinking": False}})
        with pytest.raises(engine.TemplateSwitchError):
            engine.validate_reasoning_control(wrong, _tokenizer(LADDER), _request())


class TestThePreOpenedThinkCase:
    """Validated on the exact checkpoint that exhibits it, not a stand-in."""

    def test_the_thinking_checkpoint_pre_opens_its_reasoning_block(self) -> None:
        from vllm_backend.registry import get_or_default
        tokenizer = _tokenizer(PRE_OPENING)
        rendered = engine.render_prompt(
            tokenizer, _request(), {})
        assert rendered.rstrip().endswith("<think>"), (
            "this is the checkpoint the split repair exists for; if it stops "
            "pre-opening, the repair's justification has changed")

    def test_the_canonical_checkpoint_does_not_pre_open(self) -> None:
        """The distinction the repair depends on."""
        card = get(CANONICAL)
        rendered = engine.render_prompt(
            _tokenizer(CANONICAL), _request(),
            card.template_kwargs(ReasoningMode.NATURAL_REASONING))
        assert not rendered.rstrip().endswith("<think>")

    def test_the_split_repairs_a_pre_opened_trace(self) -> None:
        """A generation with a close marker and no open marker: the leak shape."""
        from vllm_backend.reasoning import DelimiterParser, split

        class _ParserThatMissesIt:
            """What vLLM's qwen3 parser does when the open marker is in the prompt."""

            def extract_reasoning(self, text, request=None):
                return None, text

        text = "counting the sentences</think>Alpha. Beta. Gamma. Delta."
        reasoning, answer = split(_ParserThatMissesIt(), text,
                                  "<think>", "</think>")
        assert answer == "Alpha. Beta. Gamma. Delta."
        assert "counting the sentences" in reasoning
        assert "</think>" not in answer


@pytest.mark.skipif(os.environ.get("DCI_BACKEND_SMOKE") != "1",
                    reason="set DCI_BACKEND_SMOKE=1 to load weights and generate")
class TestEndToEndThroughTheRealPath:
    """Resolve, render, validate and GENERATE, via the experiment code path.

    Opt-in because it reads weights and occupies both cards. It is the only test
    that proves the four stages compose; everything above proves them singly.
    """

    def test_a_reasoning_run_reaches_generation(self) -> None:
        from vllm_backend.hardware import probe as probe_host
        from vllm_backend.resolve import resolve_engine, resolve_run, resolve_sampling

        card, host = get(CANONICAL), probe_host()
        engine_plan = resolve_engine(card, host, {})
        run_plan = resolve_run(card, ReasoningMode.NO_THINKING,
                               {"max_tokens": 64})
        outcome = engine.run(engine_plan, resolve_sampling(run_plan, {}),
                             run_plan, card, [_request()], host)
        results = outcome["results"]
        assert len(results) == 1
        assert results[0].outcome == "OK", results[0].outcome_detail
        assert results[0].final_answer.strip()
        # The evidence the run recorded about its own template.
        assert outcome["provenance"]["switch_evidence"]["card"][
            "modes_render_distinctly"] is True
