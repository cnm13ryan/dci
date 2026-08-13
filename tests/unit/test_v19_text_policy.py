"""The frozen v19 text semantics, and the five defects it corrects.

Section 10.6: "A demonstrated semantic or verifier defect requires repair and
re-audit before freeze." Each `INTENTIONAL_CORRECTIONS` row names a demonstrated
defect, so each row needs a test that the defect is gone and a test that the
inherited behaviour is what the row says it was. Both directions matter: a
correction nobody can reproduce the need for is indistinguishable from a preference.
"""
from __future__ import annotations

import re
import unicodedata

import pytest

from dci.v19.text import (
    CANONICAL_TEXT_POLICY,
    CASE_RULES,
    INTENTIONAL_CORRECTIONS,
    NORMALISATIONS,
    TextPolicy,
    TextPolicyError,
    fold,
    folded_tokens,
    normalise,
    require_policy,
    sentence_lengths,
    split_sentences,
    token_multiset,
    word_tokens,
)

POLICY = CANONICAL_TEXT_POLICY

# Written as escapes deliberately. A literal invisible character in the source is
# the exact hazard these tests are about, and a reviewer cannot see one.
ZERO_WIDTH_SPACE = "\u200b"
SOFT_HYPHEN = "\u00ad"
BYTE_ORDER_MARK = "\ufeff"


# --------------------------------------------------------- no hidden default
def test_every_entry_point_refuses_an_implicit_policy():
    for call in (normalise, word_tokens, folded_tokens, split_sentences):
        with pytest.raises(TextPolicyError, match="explicit TextPolicy"):
            call("- a", None)


def test_require_policy_returns_the_policy_unchanged():
    assert require_policy(POLICY) is POLICY


@pytest.mark.parametrize("bad", ["", "NFKC-ish", "nfkc", "utf8"])
def test_an_unknown_normalisation_is_refused(bad):
    with pytest.raises(TextPolicyError, match="not one of"):
        TextPolicy(policy_id="x", provenance="y", unicode_normalisation=bad,
                   removed_categories=(), case_rule="casefold",
                   word_pattern=r"\w+", sentence_boundary=r"\s+",
                   collapse_whitespace=True)


@pytest.mark.parametrize("bad", ["", "LOWER", "upper", "titlecase"])
def test_an_unknown_case_rule_is_refused(bad):
    with pytest.raises(TextPolicyError, match="not one of"):
        TextPolicy(policy_id="x", provenance="y", unicode_normalisation="NFKC",
                   removed_categories=(), case_rule=bad, word_pattern=r"\w+",
                   sentence_boundary=r"\s+", collapse_whitespace=True)


def test_an_unusable_pattern_is_refused_at_declaration():
    with pytest.raises(TextPolicyError, match="not a usable regular expression"):
        TextPolicy(policy_id="x", provenance="y", unicode_normalisation="NFKC",
                   removed_categories=(), case_rule="casefold",
                   word_pattern="[unclosed", sentence_boundary=r"\s+",
                   collapse_whitespace=True)


@pytest.mark.parametrize("bad", ["C", "Cfx", "cf", ""])
def test_a_non_category_is_refused(bad):
    with pytest.raises(TextPolicyError, match="Unicode general category"):
        TextPolicy(policy_id="x", provenance="y", unicode_normalisation="NFKC",
                   removed_categories=(bad,), case_rule="casefold",
                   word_pattern=r"\w+", sentence_boundary=r"\s+",
                   collapse_whitespace=True)


def test_an_anonymous_policy_is_refused():
    with pytest.raises(TextPolicyError, match="id and a provenance"):
        TextPolicy(policy_id="", provenance="", unicode_normalisation="NFKC",
                   removed_categories=(), case_rule="casefold",
                   word_pattern=r"\w+", sentence_boundary=r"\s+",
                   collapse_whitespace=True)


def test_the_declared_option_sets_are_the_ones_the_policy_uses():
    assert POLICY.unicode_normalisation in NORMALISATIONS
    assert POLICY.case_rule in CASE_RULES


# ------------------------------------------------------------- the policy hash
@pytest.mark.parametrize("field,value", [
    ("unicode_normalisation", "NFC"),
    ("removed_categories", ("Cf",)),
    ("case_rule", "lower"),
    ("word_pattern", r"[A-Za-z0-9]+"),
    ("sentence_boundary", r"(?<=[.!?])\s+"),
    ("collapse_whitespace", False),
])
def test_every_semantic_field_moves_the_policy_hash(field, value):
    import dataclasses
    other = dataclasses.replace(POLICY, **{field: value})
    assert other.policy_hash != POLICY.policy_hash


def test_rewording_the_provenance_is_not_a_change_of_measurement():
    import dataclasses
    other = dataclasses.replace(POLICY, provenance="reworded, same rule")
    assert other.policy_hash == POLICY.policy_hash


def test_the_policy_id_is_inside_the_hash():
    import dataclasses
    other = dataclasses.replace(POLICY, policy_id="v19:text-policy.other")
    assert other.policy_hash != POLICY.policy_hash


def test_the_state_is_serialisable_and_carries_every_decision():
    import json
    state = POLICY.state()
    assert json.loads(json.dumps(state)) == state
    assert set(state) == {"policy_id", "unicode_normalisation",
                          "removed_categories", "case_rule", "word_pattern",
                          "sentence_boundary", "collapse_whitespace"}


# ------------------------------------- correction 1: the Unicode word pattern
def test_the_inherited_ascii_pattern_really_did_truncate_an_accented_word():
    inherited = r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*"
    assert re.findall(inherited, "café") == ["caf"]


def test_an_accented_word_is_one_whole_token():
    assert word_tokens("café", POLICY) == ["café"]


@pytest.mark.parametrize("text,expected", [
    ("naïve", ["naïve"]),
    ("Привет мир", ["Привет", "мир"]),
    ("日本語", ["日本語"]),
    ("don't", ["don't"]),
    ("well-known", ["well-known"]),
])
def test_the_word_pattern_is_script_agnostic(text, expected):
    assert word_tokens(text, POLICY) == expected


def test_an_underscore_does_not_join_a_word():
    assert word_tokens("alfa_bravo", POLICY) == ["alfa", "bravo"]


def test_a_non_ascii_mandatory_word_is_matchable_which_the_inherited_rule_denied():
    # The defect the row names: the realisation was impossible rather than failing.
    assert "café" in folded_tokens("I drank a café today", POLICY)


# --------------------------- correction 2: strip format and control characters
@pytest.mark.parametrize("invisible", [ZERO_WIDTH_SPACE, SOFT_HYPHEN,
                                       BYTE_ORDER_MARK])
def test_an_invisible_character_cannot_split_a_word(invisible):
    text = f"al{invisible}fa"
    assert word_tokens(text, POLICY) == ["alfa"]


def test_the_zero_width_space_defeated_the_inherited_collapse():
    # \s does not match U+200B, which is why collapsing whitespace was not enough.
    assert re.sub(r"\s+", " ", f"al{ZERO_WIDTH_SPACE}fa") == f"al{ZERO_WIDTH_SPACE}fa"


def test_a_repeated_word_stays_repeated_under_the_corrected_rule():
    # The demonstrated defect: the Pair 2 focal rule passed while a word repeated.
    counts = token_multiset(f"alfa al{ZERO_WIDTH_SPACE}fa", POLICY)
    assert counts == {"alfa": 2}


def test_the_removed_categories_are_format_and_control():
    assert POLICY.removed_categories == ("Cf", "Cc")
    assert unicodedata.category(ZERO_WIDTH_SPACE) == "Cf"
    assert unicodedata.category("\n") == "Cc"


def test_whitespace_is_never_removed_even_though_newline_is_a_control_character():
    # The regression that collapsed "- a\n- b\n- c" into one line.
    assert normalise("- a\n- b\n- c", POLICY) == "- a\n- b\n- c"
    assert normalise("- a\n- b\n- c", POLICY).count("\n") == 2


# ----------------------------------------- correction 3: exactly one case rule
def test_there_is_one_case_rule_and_it_is_casefold():
    assert POLICY.case_rule == "casefold"


def test_the_two_inherited_rules_genuinely_disagree():
    # The row's example: the encoding required one distinct token, the verifier two.
    assert "ß".casefold() == "ss"
    assert "ß".lower() == "ß"
    assert "ß".casefold() == "SS".casefold()
    assert "ß".lower() != "SS".lower()


def test_the_sharp_s_and_the_double_s_are_one_token_under_the_frozen_rule():
    assert token_multiset("ß SS", POLICY) == {"ss": 2}


def test_folding_uses_the_declared_rule_not_a_hard_coded_one():
    import dataclasses
    lowering = dataclasses.replace(POLICY, case_rule="lower")
    assert fold("ß", POLICY) == "ss"
    assert fold("ß", lowering) == "ß"
    assert fold("ß", dataclasses.replace(POLICY, case_rule="none")) == "ß"


# -------------------------------- correction 4: a non-ASCII segment is a sentence
def test_the_inherited_survival_rule_dropped_a_cyrillic_segment():
    assert re.search(r"[A-Za-z0-9]", "Привет мир") is None


@pytest.mark.parametrize("text", ["Привет мир", "日本語のテキスト", "café crème"])
def test_a_non_ascii_segment_is_a_sentence(text):
    assert split_sentences(text, POLICY) == [text]


def test_a_segment_of_punctuation_alone_is_not_a_sentence():
    assert split_sentences("!!! ??? ...", POLICY) == []


def test_sentence_lengths_count_word_tokens_under_the_same_pattern():
    assert sentence_lengths("One. Two words. Three words here.", POLICY) == [1, 2, 3]


def test_a_non_ascii_sentence_has_a_length_rather_than_being_invisible():
    assert sentence_lengths("Привет мир.", POLICY) == [2]


# --------------------------- correction 5: the marker definition is supplied
def test_the_segmenter_strips_only_the_markers_it_is_given():
    text = "- alfa\n- bravo"
    assert split_sentences(text, POLICY) == ["- alfa", "- bravo"]
    assert split_sentences(text, POLICY, [r"^\s*[-]\s+"]) == ["alfa", "bravo"]


def test_a_marker_is_stripped_once_so_a_repeated_marker_survives():
    assert split_sentences("- - alfa", POLICY, [r"^\s*[-]\s+"]) == ["- alfa"]


def test_no_marker_pattern_is_hard_coded_in_the_module():
    # The defect: LIST_MARKER lived inside split_sentences, so changing the list
    # grammar silently changed Pair 3's sentence count.
    import inspect

    import dci.v19.text as textlib
    source = inspect.getsource(textlib.split_sentences)
    for marker in ("•", "‣", "▪", "LIST_MARKER"):
        assert marker not in source


# ---------------------------------------------------- normalisation properties
def test_normalisation_is_idempotent():
    messy = f"  a\t\tb{ZERO_WIDTH_SPACE}  \n\t c  \n"
    once = normalise(messy, POLICY)
    assert normalise(once, POLICY) == once


def test_normalisation_reaches_a_compatibility_variant():
    assert normalise("ﬁre", POLICY) == "fire"
    assert normalise("１．", POLICY) == "1."


def test_indentation_survives_because_the_nesting_rule_reads_it():
    assert normalise("- a\n    - b", POLICY) == "- a\n - b"
    assert normalise("- a\n    - b", POLICY).splitlines()[1].startswith(" ")


def test_trailing_whitespace_is_removed_per_line():
    assert normalise("- a   \n- b\t\t\n", POLICY) == "- a\n- b\n"


def test_a_tab_and_a_non_breaking_space_collapse_to_one_space():
    assert normalise("a\tb", POLICY) == "a b"
    assert normalise("a\u00a0b", POLICY) == "a b"
    assert normalise("a\u3000b", POLICY) == "a b"


def test_none_normalises_to_the_empty_string_rather_than_the_word_none():
    assert normalise(None, POLICY) == ""
    assert word_tokens(None, POLICY) == []
    assert split_sentences(None, POLICY) == []


# ------------------------------------------------------ the correction record
def test_every_correction_names_a_defect_and_both_behaviours():
    assert INTENTIONAL_CORRECTIONS
    for row in INTENTIONAL_CORRECTIONS:
        assert set(row) == {"id", "inherited", "corrected", "defect"}
        for key, value in row.items():
            assert value.strip(), f"{row['id']}: {key} is empty"


def test_the_correction_ids_are_unique():
    ids = [row["id"] for row in INTENTIONAL_CORRECTIONS]
    assert len(set(ids)) == len(ids)


def test_the_five_corrections_are_the_ones_this_file_covers():
    # A correction added later without a regression test here is a correction with
    # no demonstrated defect, which is what section 10.6 does not permit.
    assert {row["id"] for row in INTENTIONAL_CORRECTIONS} == {
        "unicode-word-pattern", "strip-format-characters", "single-case-rule",
        "unicode-sentence-survival", "shared-marker-definition"}
