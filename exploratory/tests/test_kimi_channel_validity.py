"""Markerless output in a thinking condition is not a final answer.

Defect: `DelimiterParser.extract_reasoning` ended with `return None,
text.strip()`. When Kimi emitted neither `◁think▷` nor `◁/think▷` — which is what
a failed reasoning interface or an incompatible parser looks like — the whole
raw generation was returned as answer content. The row was then marked as
having a final answer and sent to the behavioural verifiers.

The class docstring already promised the opposite: "Where the card returns the
whole text as the summary when no marker is present, this returns an EMPTY
answer in a thinking condition, because a scored scratchpad is worse than a
missing datum." The code contradicted its own contract.

Scoring a scratchpad manufactures a behavioural datum out of a parser failure,
which is the CHANNEL_INVALID case: the two channels the contract requires could
not be separated at all.

Classification: reasoning/final-answer channel error, with a construct-validity
consequence — an unsegmented trace scored as an answer is not a measurement of
the target instruction.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel.vllm_tp2 import DelimiterParser, split  # noqa: E402

START, END = "◁think▷", "◁/think▷"


@pytest.fixture()
def parser() -> DelimiterParser:
    return DelimiterParser(START, END)


class TestMarkerlessOutput:
    def test_markerless_text_yields_no_answer(self, parser) -> None:
        raw = "Let me count the sentences. One, two, three. Hmm, that is wrong."
        reasoning, answer = parser.extract_reasoning(raw)
        assert answer == "", "a markerless scratchpad was promoted to an answer"

    def test_markerless_text_through_split_yields_no_answer(self, parser) -> None:
        raw = "I need to check whether this has four sentences."
        reasoning, answer = split(parser, raw)
        assert answer == ""

    def test_markerless_text_is_not_reported_as_reasoning_either(self, parser) -> None:
        """It is unsegmented, so it is neither channel — not silently one."""
        reasoning, answer = split(parser, "unsegmented text")
        assert answer == ""
        assert reasoning == ""

    def test_empty_generation_yields_no_answer(self, parser) -> None:
        assert split(parser, "")[1] == ""


class TestWellFormedOutputStillParses:
    def test_closed_block_splits_into_two_channels(self, parser) -> None:
        raw = f"{START}counting sentences{END}Alpha. Beta. Gamma. Delta."
        reasoning, answer = split(parser, raw)
        assert reasoning == "counting sentences"
        assert answer == "Alpha. Beta. Gamma. Delta."

    def test_content_before_the_opening_marker_is_answer(self, parser) -> None:
        raw = f"Preamble. {START}thinking{END} Alpha. Beta."
        reasoning, answer = split(parser, raw)
        assert reasoning == "thinking"
        assert "Preamble." in answer and "Alpha. Beta." in answer

    def test_opened_but_never_closed_yields_no_answer(self, parser) -> None:
        """Already correct before the repair; pinned so it stays that way."""
        reasoning, answer = split(parser, f"{START}thinking forever and ever")
        assert answer == ""
        assert "thinking forever" in reasoning


class TestNoRawTextEverBecomesBothChannels:
    @pytest.mark.parametrize("raw", [
        "plain text",
        f"{START}only an opening marker",
        f"trailing {END} only a closing marker",
        "",
    ])
    def test_reasoning_and_answer_are_never_the_same_raw_text(self, parser, raw) -> None:
        reasoning, answer = split(parser, raw)
        assert not (reasoning and answer and reasoning == answer)
