"""Tests for the non-boundary controls and the focal ladder.

Written and passing before any model data was generated, because both are new
verifiers that every downstream number depends on.

Two things are pinned here that a reading of the code would not settle:

* the two candidate symbols are counted **literally**, and the asterisk's known
  interaction with the list-marker stripper is asserted rather than assumed
  absent — the preflight needs to know the exact shape of the problem;
* the ladder is a genuine prefix of the frozen rule: at k = 4 it agrees with
  `v_increasing_lengths` on every four-sentence text, and no rung reads the
  sentence count.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dci_exploratory import extensions, harvest

extensions.register()
STATE = harvest.load()

from dci.verifiers.rules import (split_sentences, v_exact_char_total,  # noqa: E402
                                 v_increasing_lengths)
from dci_exploratory.extensions import v_increasing_prefix  # noqa: E402

FOUR = "Alpha one. Beta two three. Gamma four five six. Delta seven eight nine ten."


# ------------------------------------------------------- the ladder verifier
def test_prefix_at_k4_agrees_with_the_frozen_rule():
    """The top rung must BE the existing constraint, or it is not a ladder."""
    texts = [
        FOUR,
        "One. Two. Three. Four.",
        "Long one two three four. Short. Mid one two. Tail one two three.",
        "A b c. D e. F g h i. J k l m n.",
    ]
    for text in texts:
        assert v_increasing_prefix(text, 4).binary_pass == \
            v_increasing_lengths(text).binary_pass, text


def test_b_inc2_passes_when_the_first_three_increase():
    assert v_increasing_prefix("One. Two words. Three words here. Tiny.", 3).binary_pass == 1


def test_b_inc2_ignores_the_fourth_sentence_entirely():
    rising = "One. Two words. Three words here. A much longer fourth sentence here."
    falling = "One. Two words. Three words here. Tiny."
    assert v_increasing_prefix(rising, 3).binary_pass == 1
    assert v_increasing_prefix(falling, 3).binary_pass == 1


def test_b_inc2_fails_when_an_early_increase_is_missing():
    assert v_increasing_prefix("One two three. Two. Three words here. Tiny.", 3).binary_pass == 0
    assert v_increasing_prefix("One. Two words three four. Three. Tiny.", 3).binary_pass == 0


def test_b_inc1_passes_on_a_single_increase():
    assert v_increasing_prefix("One. Two words. Tiny. Tiny.", 2).binary_pass == 1


def test_b_inc1_fails_when_the_second_is_not_longer():
    assert v_increasing_prefix("One two three. Two. Long one two three four.", 2).binary_pass == 0
    assert v_increasing_prefix("Two words. Two words. Tiny.", 2).binary_pass == 0


def test_the_ladder_is_monotone_by_construction():
    """Passing a longer prefix implies passing every shorter one."""
    for text in [FOUR, "One. Two words. Three words here. Tiny.",
                 "One. Two words. Tiny. Tiny.", "Big one two three. A. B. C."]:
        for k in (4, 3):
            if v_increasing_prefix(text, k).binary_pass == 1:
                assert v_increasing_prefix(text, k - 1).binary_pass == 1, (text, k)


def test_short_texts_are_unscorable_not_failing():
    result = v_increasing_prefix("One. Two words.", 3)
    assert result.status == "unscorable"
    assert result.binary_pass == 0


def test_the_ladder_never_reads_the_sentence_count():
    """Adding sentences beyond the rung must not change the verdict."""
    for k, base in ((3, "One. Two words. Three words here."),
                    (2, "One. Two words.")):
        verdict = v_increasing_prefix(base + " Tiny.", k).binary_pass
        for extra in (" Tiny.", " Tiny. Tiny.", " Tiny. Tiny. Tiny."):
            assert v_increasing_prefix(base + extra, k).binary_pass == verdict


def test_ladder_registered_and_reachable_through_the_state():
    for cid, text, expected in (("X_B_INC2", "One. Two words. Three words here. X.", 1),
                                ("X_B_INC2", "One two. Two. Three words here. X.", 0),
                                ("X_B_INC1", "One. Two words. X. X.", 1),
                                ("X_B_INC1", "One two. Two. X. X.", 0)):
        assert int(STATE.verify(text, cid).binary_pass) == expected, (cid, text)


# ------------------------------------------------ the non-boundary controls
def test_both_candidate_symbols_are_counted_literally():
    assert v_exact_char_total("Rain falls at 5° today.", "°", 1).binary_pass == 1
    assert v_exact_char_total("Rain falls* today.", "*", 1).binary_pass == 1
    assert v_exact_char_total("Rain falls at 5° and 9° today.", "°", 1).binary_pass == 0


def test_controls_registered_with_the_semicolon_wording_template():
    semicolon = STATE.CONSTRAINTS["X_SEMICOLON_FREE"]
    for cid in ("X_DEGREE_FREE", "X_ASTERISK_FREE"):
        spec = STATE.CONSTRAINTS[cid]
        assert spec.rule_family == semicolon.rule_family
        assert spec.generative_scope == semicolon.generative_scope
        assert spec.verifier_span == semicolon.verifier_span
        assert dict(spec.params)["n"] == 1


def test_control_prompts_differ_from_the_semicolon_only_in_the_mark_name():
    """The whole contrast rests on this; a wording difference would confound it."""
    semicolon = harvest.compose_prompt("T", ["X_SEMICOLON_FREE"], 0)
    for cid, name in (("X_DEGREE_FREE", "degree symbol (°)"),
                      ("X_ASTERISK_FREE", "asterisk (*)")):
        rendered = harvest.compose_prompt("T", [cid], 0)
        assert rendered == semicolon.replace("semicolon", name), rendered


def test_asterisk_markdown_hazard_is_real_and_is_measured_not_assumed():
    """`**emphasis**` and a bullet list both break the asterisk count."""
    assert v_exact_char_total("This is **bold** text.", "*", 1).detail["observed"] == 4
    bullet = "* Rain falls.\n* Rivers rise."
    assert v_exact_char_total(bullet, "*", 1).detail["observed"] == 2
    # The stripper removes the bullet for SEGMENTATION while the counter still
    # sees it, so the two views of the same text disagree. That asymmetry is the
    # hazard, and it does not exist for the degree symbol.
    assert len(split_sentences(bullet)) == 2
    assert "*" not in "".join(split_sentences(bullet))


def test_degree_symbol_has_no_such_hazard():
    text = "° Rain falls. Rivers rise."
    assert v_exact_char_total(text, "°", 1).detail["observed"] == 1
    assert "°" in "".join(split_sentences(text))


@pytest.mark.parametrize("cid", ["X_DEGREE_FREE", "X_ASTERISK_FREE", "X_B_INC2", "X_B_INC1"])
def test_self_check_witnesses_behave(cid):
    from dci_exploratory.extensions import _SELF_CHECK
    passing, failing = _SELF_CHECK[cid]
    assert int(STATE.verify(passing, cid).binary_pass) == 1, (cid, passing)
    assert int(STATE.verify(failing, cid).binary_pass) == 0, (cid, failing)
