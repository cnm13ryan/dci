"""Regression tests for the Kimi-VL generation backend's parsing and trimming.

Both cases here are defects the 24-row pilot caught on real output, which is
what the pilot was run for.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel.kimi_hf_backend import (THINK_CLOSE, THINK_OPEN,
                                        split_reasoning, strip_control,
                                        trim_generated)


class FakeTensor:
    """Stands in for the 1-D torch tensor `generate` returns."""

    def __init__(self, values):
        self._values = list(values)

    def tolist(self):
        return list(self._values)


class FakeTokenizer:
    def __init__(self, eos_token_id=2, pad_token_id=0):
        self.eos_token_id = eos_token_id
        self.pad_token_id = pad_token_id


# ------------------------------------------------------- padding, the bug
def test_trailing_padding_is_removed():
    """A batch pads the shorter sequence out to the longer one's length.

    Left unfixed this put [PAD] runs into three scored answers in the pilot.
    """
    tail = FakeTensor([10, 11, 12, 2, 0, 0, 0, 0])
    assert trim_generated(tail, FakeTokenizer()) == [10, 11, 12]


def test_generated_length_no_longer_counts_padding():
    """The symptom that made answer_truncated true for a row that never ran on."""
    padded = FakeTensor([10, 11, 2] + [0] * 8000)
    assert len(trim_generated(padded, FakeTokenizer())) == 2


def test_sequence_without_eos_is_kept_whole():
    """A row that really did run to the ceiling must not be trimmed."""
    tail = FakeTensor([10, 11, 12, 13])
    assert trim_generated(tail, FakeTokenizer()) == [10, 11, 12, 13]


def test_trailing_pads_are_dropped_when_pad_differs_from_eos():
    tail = FakeTensor([10, 11, 99, 99])
    assert trim_generated(tail, FakeTokenizer(eos_token_id=2,
                                              pad_token_id=99)) == [10, 11]


def test_padding_inside_content_is_not_touched():
    """Only TRAILING padding is scaffolding; nothing rewrites the middle."""
    tail = FakeTensor([10, 0, 11, 2, 0])
    assert trim_generated(tail, FakeTokenizer()) == [10, 0, 11]


def test_missing_pad_token_id_does_not_crash():
    tail = FakeTensor([10, 11, 2])
    assert trim_generated(tail, FakeTokenizer(pad_token_id=None)) == [10, 11]


# --------------------------------------------- markerless output, the guard
def test_markerless_output_yields_no_answer():
    """An always-thinking checkpoint emitting no markers is a parser failure.

    Returning the raw text as the answer would hand an unsegmented scratchpad to
    the behavioural verifiers.
    """
    reasoning, answer = split_reasoning("plain prose with no markers at all")
    assert (reasoning, answer) == ("", "")


def test_closed_trace_splits_into_reasoning_and_answer():
    text = f"{THINK_OPEN}counting sentences{THINK_CLOSE}Sun rises. Sky glows."
    reasoning, answer = split_reasoning(text)
    assert reasoning == "counting sentences"
    assert answer == "Sun rises. Sky glows."


def test_unclosed_trace_yields_no_answer():
    reasoning, answer = split_reasoning(f"{THINK_OPEN}still thinking")
    assert reasoning == "still thinking"
    assert answer == ""


def test_content_before_the_marker_is_answer_not_reasoning():
    """The template does not enforce an ordering, so the split must not assume one."""
    text = f"Sun rises.{THINK_OPEN}second thoughts{THINK_CLOSE}Sky glows."
    reasoning, answer = split_reasoning(text)
    assert reasoning == "second thoughts"
    assert "Sun rises." in answer and "Sky glows." in answer


def test_control_tokens_are_stripped_but_think_markers_survive():
    text = f"<|im_start|>{THINK_OPEN}plan{THINK_CLOSE}answer<|im_end|>"
    cleaned = strip_control(text)
    assert "<|im_start|>" not in cleaned and "<|im_end|>" not in cleaned
    assert THINK_OPEN in cleaned and THINK_CLOSE in cleaned
