"""The canonical Pair 1 grammar, the shared parser, and the decisions behind both.

Section 4.2 names Pair 1's principal measurement risk as verifier coupling through
shared list parsing. The parser is therefore a separate object, and these tests are
about the parse itself rather than either verdict - so a later coupling audit can
attribute a joint change to the parse or to the behaviour.

The other half is about provenance. The preregistration fixes no parsing rule at all,
so Stage 2 amendment A1 fixes one, and every field of it is asserted to change the
grammar's hash: answering a decision differently has to be visible in the freeze
rather than absorbed silently. `RESOLVED_BY_AMENDMENT` carries the answer and the
reason for each, and `assert_policy_fields_are_accounted_for` keeps that table
exhaustive so a field added later cannot acquire a default.
"""
import dataclasses

import pytest

from dci.v19 import parsing
from dci.v19 import text as textlib
from dci.v19.parsing import (
    CANONICAL_LIST_POLICY,
    LABEL_MATCH_MODES,
    RESOLVED_BY_AMENDMENT,
    ListPolicy,
    ListPolicyError,
    OrderingRelation,
    RelationError,
    match_items_to_labels,
    parse_list,
    require_policy,
    sentence_lengths,
    sentences,
)
from dci.v19.text import CANONICAL_TEXT_POLICY

pytestmark = pytest.mark.cpu

P = CANONICAL_LIST_POLICY


def other(**changes) -> ListPolicy:
    return dataclasses.replace(P, policy_id="v19:list-policy.probe", **changes)


# ----------------------------------------------------------- no hidden default
def test_the_parser_refuses_to_run_without_an_explicit_grammar():
    for bad in (None, {}, "canonical", P.state()):
        with pytest.raises(TypeError, match="explicit ListPolicy"):
            parse_list("- a", bad)


def test_require_policy_returns_the_policy_unchanged():
    assert require_policy(P) is P


def test_every_grammar_decision_has_a_recorded_answer():
    parsing.assert_policy_fields_are_accounted_for()


def test_the_recorded_answers_cover_every_decision_field():
    decisions = {f.name for f in dataclasses.fields(ListPolicy)} - {
        "policy_id", "provenance", "text"}
    assert set(RESOLVED_BY_AMENDMENT) == decisions
    for field, reason in RESOLVED_BY_AMENDMENT.items():
        assert reason and len(reason) > 30, field


def test_a_new_decision_field_without_a_recorded_answer_is_caught():
    original = parsing.RESOLVED_BY_AMENDMENT
    try:
        parsing.RESOLVED_BY_AMENDMENT = {
            k: v for k, v in original.items() if k != "nested_items_count"}
        with pytest.raises(ListPolicyError, match="hidden default"):
            parsing.assert_policy_fields_are_accounted_for()
    finally:
        parsing.RESOLVED_BY_AMENDMENT = original
    parsing.assert_policy_fields_are_accounted_for()


def test_naming_a_field_that_does_not_exist_is_caught():
    original = parsing.RESOLVED_BY_AMENDMENT
    try:
        parsing.RESOLVED_BY_AMENDMENT = {**original, "tab_width": "?"}
        with pytest.raises(ListPolicyError, match="not ListPolicy fields"):
            parsing.assert_policy_fields_are_accounted_for()
    finally:
        parsing.RESOLVED_BY_AMENDMENT = original


# ---------------------------------------------------------- the grammar is hashed
@pytest.mark.parametrize("field,value", [
    ("bullet_markers", ("-", "*", "+")),
    ("numbered_forms", ("N.",)),
    ("numbered_max_digits", 2),
    ("require_space_after_marker", False),
    ("numbered_items_count", False),
    ("nested_items_count", False),
    ("continuation_joins_previous", False),
    ("empty_items_count", True),
    ("label_match", "leading_token"),
    ("extra_items_permitted", True),
])
def test_answering_any_decision_differently_changes_the_grammar_hash(field, value):
    assert field in RESOLVED_BY_AMENDMENT
    assert other(**{field: value}).policy_hash != P.policy_hash, field


def test_the_text_policy_is_inside_the_grammar_hash():
    """One text semantics for every layer, so the grammar commits to it."""
    assert P.text is CANONICAL_TEXT_POLICY
    assert P.state()["text_policy"] == CANONICAL_TEXT_POLICY.state()
    weakened = dataclasses.replace(CANONICAL_TEXT_POLICY, policy_id="probe",
                                   removed_categories=())
    assert other(text=weakened).policy_hash != P.policy_hash


@pytest.mark.parametrize("field,value", [
    ("unicode_normalisation", "NFC"),
    ("removed_categories", ("Cf",)),
    ("case_rule", "lower"),
    ("word_pattern", r"[A-Za-z0-9]+"),
    ("sentence_boundary", r"(?<=[.!?])\s+"),
    ("collapse_whitespace", False),
])
def test_every_text_decision_changes_the_text_policy_hash(field, value):
    mutated = dataclasses.replace(CANONICAL_TEXT_POLICY, policy_id="probe",
                                  **{field: value})
    assert mutated.policy_hash != CANONICAL_TEXT_POLICY.policy_hash, field


def test_the_policy_id_is_part_of_the_hash():
    assert dataclasses.replace(P, policy_id="v19:list-policy.other").policy_hash \
        != P.policy_hash


def test_rewording_the_provenance_is_not_a_change_of_measurement():
    assert dataclasses.replace(P, provenance="a different citation").policy_hash \
        == P.policy_hash


def test_an_identical_grammar_hashes_identically():
    assert dataclasses.replace(P).policy_hash == P.policy_hash


# ------------------------------------------------------- grammar well-formedness
def test_a_grammar_that_can_open_no_item_is_refused():
    with pytest.raises(ListPolicyError, match="no marker can open an item"):
        other(bullet_markers=(), numbered_forms=())
    with pytest.raises(ListPolicyError, match="no marker can open an item"):
        other(bullet_markers=(), numbered_items_count=False)


def test_a_multi_character_bullet_marker_is_refused():
    with pytest.raises(ListPolicyError, match="not a single character"):
        other(bullet_markers=("--",))


def test_a_numbered_form_must_name_the_digits_exactly_once():
    for bad in ("1.", "N.N", ""):
        with pytest.raises(ListPolicyError, match="exactly one 'N'"):
            other(numbered_forms=(bad,))


def test_an_unknown_match_mode_is_refused():
    with pytest.raises(ListPolicyError, match="not one of"):
        other(label_match="fuzzy")


def test_an_anonymous_grammar_is_refused():
    with pytest.raises(ListPolicyError, match="id and a provenance"):
        dataclasses.replace(P, policy_id="")
    with pytest.raises(ListPolicyError, match="id and a provenance"):
        dataclasses.replace(P, provenance="")


def test_the_grammar_requires_a_real_text_policy():
    from dci.v19.text import TextPolicyError
    with pytest.raises(TextPolicyError, match="explicit TextPolicy"):
        other(text={"policy_id": "not a policy"})


def test_the_digit_cap_is_bounded():
    with pytest.raises(ListPolicyError, match="outside 1..9"):
        other(numbered_max_digits=0)


# ------------------------------------------------------- marker recognition
@pytest.mark.parametrize("line,is_item", [
    ("- a", True), ("* a", True), ("• a", True), ("‣ a", True), ("▪ a", True),
    ("1. a", True), ("1) a", True), ("(1) a", True), ("99. a", True),
    ("100. a", True),                        # A1 raised the cap from two digits
    ("1000. a", False),
    ("-a", False),                           # the required space
    ("+ a", False),                          # not in the inherited class
    ("  - a", True),                         # any indent
    ("a", False),
])
def test_the_canonical_marker_set(line, is_item):
    assert bool(parse_list(line, P).items) is is_item, line


def test_the_three_digit_cap_is_a_recorded_departure_from_the_inherited_regex():
    """The inherited `\\d{1,2}` was an artefact, not a decision."""
    from dci.verifiers.rules import LIST_MARKER
    assert not LIST_MARKER.match("100. a")
    assert parse_list("100. a", P).count == 1
    assert "100 and 999" in RESOLVED_BY_AMENDMENT["numbered_max_digits"]
    assert parse_list("100. a", other(numbered_max_digits=2)).count == 0


def test_a_tab_after_the_marker_is_a_marker_after_normalisation():
    """The text policy collapses every non-newline whitespace run to one space."""
    assert parse_list("-\ta", P).count == 1


# ---------------------------------------------------------------- the parse
def test_a_plain_three_item_list_parses_with_spans():
    parsed = parse_list("- alpha\n- beta\n- gamma", P)
    assert parsed.count == 3
    assert parsed.contents == ("alpha", "beta", "gamma")
    for item in parsed.items:
        start, end = item.span
        assert parsed.text[start:end].endswith(item.content)
    assert [i.ordinal for i in parsed.items] == [1, 2, 3]


def test_the_parse_records_both_policies_it_used():
    parsed = parse_list("- a\n- b", P)
    assert parsed.policy_hash == P.policy_hash
    assert parsed.text_policy_hash == P.text.policy_hash


@pytest.mark.parametrize("n", range(1, 9))
def test_the_observed_count_tracks_the_number_of_markers(n):
    text = "\n".join(f"- item {i}" for i in range(n))
    assert parse_list(text, P).count == n


def test_numbered_items_count_under_the_canonical_grammar():
    text = "1. alpha\n2. beta"
    assert parse_list(text, P).count == 2
    strict = parse_list(text, other(numbered_items_count=False))
    assert strict.count == 0
    assert [i.excluded_because for i in strict.excluded] == [
        "numbered_not_counted"] * 2


def test_nested_items_count_under_the_canonical_grammar():
    text = "- alpha\n  - nested\n- beta"
    assert parse_list(text, P).count == 3
    flat = parse_list(text, other(nested_items_count=False))
    assert flat.count == 2
    assert [i.excluded_because for i in flat.excluded] == ["nested_not_counted"]
    assert flat.excluded[0].indent >= 1


def test_a_continuation_line_joins_the_previous_item():
    text = "- alpha\n  continues here\n- beta"
    joined = parse_list(text, P)
    assert joined.count == 2
    assert joined.contents == ("alpha continues here", "beta")
    assert joined.items[0].continuation_lines == 1
    split = parse_list(text, other(continuation_joins_previous=False))
    assert split.contents == ("alpha", "beta")
    assert len(split.prose_spans) == 1


@pytest.mark.parametrize("text", ["- alpha\n- \n- beta", "- alpha\n-\n- beta"])
def test_a_marker_alone_is_an_empty_item_not_a_continuation(text):
    """It was joined to the previous item, whose content became "alpha -"."""
    parsed = parse_list(text, P)
    assert parsed.count == 2
    assert parsed.contents == ("alpha", "beta")
    assert [i.excluded_because for i in parsed.excluded] == ["empty_item"]
    assert parse_list(text, other(empty_items_count=True)).count == 3


def test_an_item_of_punctuation_alone_is_empty_for_the_same_reason_it_is_not_a_sentence():
    text = "- ---\n- +++"
    assert parse_list(text, P).count == 0
    assert sentences(text, P) == []


def test_leading_and_trailing_prose_are_recorded_separately():
    parsed = parse_list("Here is the list:\n- a\n- b\nHope that helps!",
                        other(continuation_joins_previous=False))
    assert parsed.count == 2
    assert parsed.leading_prose and parsed.trailing_prose
    assert len(parsed.prose_spans) == 2


def test_a_chat_preamble_alone_is_no_items_and_all_prose():
    parsed = parse_list("Sure, I can help with that.", P)
    assert parsed.count == 0 and parsed.leading_prose


@pytest.mark.parametrize("text", ["", "   ", "\n\n", None])
def test_an_empty_segment_parses_to_nothing(text):
    parsed = parse_list(text, P)
    assert parsed.count == 0 and not parsed.excluded


def test_crlf_lines_survive_normalisation_as_separate_lines():
    assert parse_list("- alpha\r\n- beta", P).count == 2


def test_the_description_is_serialisable_and_complete():
    import json
    described = parse_list("Intro:\n- a\n  - b\n- \n- c", P).describe()
    json.dumps(described)
    assert set(described) == {"policy_hash", "text_policy_hash", "observed_count",
                              "items", "excluded", "prose_spans", "leading_prose",
                              "trailing_prose"}
    assert described["observed_count"] == len(described["items"])


def test_dropping_the_space_requirement_admits_tight_markers():
    tight = other(require_space_after_marker=False)
    assert parse_list("-a\n-b", tight).count == 2
    assert parse_list("-a\n-b", P).count == 0


# ------------------------------------------------- one segmentation, two spans
def test_the_grammar_supplies_its_markers_to_the_sentence_segmenter():
    """Section 4.4's shared segmentation, made explicit rather than hard-coded."""
    assert P.marker_patterns()
    assert sentences("- alpha\n- beta gamma", P) == ["alpha", "beta gamma"]
    assert sentence_lengths("- alpha\n- beta gamma", P) == [1, 2]


def test_changing_the_marker_set_changes_the_sentence_count():
    plus = other(bullet_markers=("-", "+"))
    assert sentences("+ alpha", P) == ["+ alpha"]
    assert sentences("+ alpha", plus) == ["alpha"]


@pytest.mark.parametrize("text,items,segments", [
    ("- alpha\n- beta", 2, 2),
    ("- ЖЖЖ\n- ЩЩЩ", 2, 2),                 # non-ASCII items ARE sentences now
    ("- 日本語\n- 中文", 2, 2),
    ("One. Two. Three.", 0, 3),
    ("- a\n  cont\n- b", 2, 3),
])
def test_the_two_spans_agree_about_what_a_marker_is(text, items, segments):
    assert parse_list(text, P).count == items, text
    assert len(sentences(text, P)) == segments, text


def test_a_non_ascii_item_is_a_sentence_which_the_inherited_rule_denied():
    """The root cause of the unsound solver axiom, repaired at its source."""
    from dci.verifiers import rules
    assert rules.split_sentences("- ЖЖЖ\n- ЩЩЩ") == []
    assert len(sentences("- ЖЖЖ\n- ЩЩЩ", P)) == 2


# --------------------------------------------------------- unicode normalisation
def test_invisible_characters_are_removed_before_anything_reads_the_text():
    for invisible in ("\u200b", "­", "‌", "﻿"):
        assert textlib.word_tokens(f"wo{invisible}rd", P.text) == ["word"]


def test_normalisation_reaches_a_compatibility_marker():
    """NFKC maps the fullwidth hyphen-minus onto '-', which the grammar admits."""
    assert parse_list("－ item", P).count == 1
    assert parse_list("－ item", other(
        text=dataclasses.replace(CANONICAL_TEXT_POLICY, policy_id="probe",
                                 unicode_normalisation="none"))).count == 0


def test_normalisation_is_idempotent():
    for probe in ("- café\n- naïve", "－ a", "wo\u200brd", "a b"):
        once = textlib.normalise(probe, P.text)
        assert textlib.normalise(once, P.text) == once


def test_indentation_survives_normalisation_because_nesting_reads_it():
    assert parse_list("- a\n  - b", P).items[1].indent >= 1


# ------------------------------------------------------- the ordering relation
def test_a_relation_needs_at_least_two_items():
    with pytest.raises(RelationError, match="at least two items"):
        OrderingRelation(items=("a",), edges=())


def test_duplicate_labels_are_refused():
    with pytest.raises(RelationError, match="duplicate item labels"):
        OrderingRelation(items=("a", "b", "a"), edges=())


def test_a_padded_or_empty_label_is_refused():
    for bad in ((" a", "b"), ("", "b")):
        with pytest.raises(RelationError, match="non-empty and unpadded"):
            OrderingRelation(items=bad, edges=())


def test_an_edge_outside_the_declared_set_is_refused():
    with pytest.raises(RelationError, match="outside the declared set"):
        OrderingRelation(items=("a", "b"), edges=(("a", "c"),))


def test_a_self_edge_and_a_duplicate_edge_are_refused():
    with pytest.raises(RelationError, match="cannot precede itself"):
        OrderingRelation(items=("a", "b"), edges=(("a", "a"),))
    with pytest.raises(RelationError, match="duplicate edges"):
        OrderingRelation(items=("a", "b"), edges=(("a", "b"), ("a", "b")))


def test_a_malformed_edge_is_refused_rather_than_unpacked():
    with pytest.raises(RelationError, match="not a precedence pair"):
        OrderingRelation(items=("a", "b"), edges=(("a", "b", "c"),))


def test_a_cyclic_specification_is_impossible_not_merely_failing():
    with pytest.raises(RelationError, match="contain a cycle"):
        OrderingRelation(items=("a", "b"), edges=(("a", "b"), ("b", "a")))
    with pytest.raises(RelationError, match="contain a cycle"):
        OrderingRelation(items=("a", "b", "c"),
                         edges=(("a", "b"), ("b", "c"), ("c", "a")))


def test_the_closure_adds_the_implied_precedences():
    relation = OrderingRelation(items=("x1", "x2", "x4"),
                                edges=(("x2", "x4"), ("x4", "x1")))
    assert relation.closure() == (("x2", "x1"), ("x2", "x4"), ("x4", "x1"))


def test_the_closure_of_a_chain_is_every_forward_pair():
    chain = OrderingRelation(items=("a", "b", "c", "d"),
                             edges=(("a", "b"), ("b", "c"), ("c", "d")))
    assert len(chain.closure()) == 6 and ("a", "d") in chain.closure()


def test_the_closure_is_empty_when_nothing_is_required():
    assert OrderingRelation(items=("a", "b"), edges=()).closure() == ()


@pytest.mark.parametrize("edges,depth", [
    ((), 0), ((("a", "b"),), 1), ((("a", "b"), ("b", "c")), 2),
    ((("a", "b"), ("a", "c")), 1), ((("a", "b"), ("b", "c"), ("c", "d")), 3),
])
def test_the_chain_depth_is_the_longest_required_chain(edges, depth):
    assert OrderingRelation(items=("a", "b", "c", "d"),
                            edges=edges).chain_depth == depth


def test_the_chain_depth_is_not_the_declared_ordering_depth_parameter():
    from dci.v19 import pairs
    assert pairs.PAIR_1.focal.parameters == ("ordering_depth",)
    assert "ordering_depth" not in OrderingRelation(items=("a", "b"),
                                                    edges=()).state()


def test_the_relation_hash_moves_with_the_items_and_the_edges():
    base = OrderingRelation(items=("a", "b", "c"), edges=(("a", "b"),))
    assert OrderingRelation(items=("a", "b", "c"),
                            edges=(("b", "c"),)).relation_hash != base.relation_hash
    assert OrderingRelation(items=("a", "b", "d"),
                            edges=(("a", "b"),)).relation_hash != base.relation_hash
    assert OrderingRelation(items=("a", "b", "c"),
                            edges=(("a", "b"),)).relation_hash == base.relation_hash


def test_the_relation_hash_covers_the_closure_not_only_the_edges():
    assert "closure" in OrderingRelation(items=("a", "b"),
                                         edges=(("a", "b"),)).state()


# ------------------------------------------------- labels must be single tokens
def test_a_label_the_tokeniser_would_split_is_refused():
    """Token membership cannot identify a label that is not a token."""
    relation = OrderingRelation(items=("two words", "other"), edges=())
    with pytest.raises(RelationError, match="not single word tokens"):
        relation.assert_labels_are_tokens(P)


def test_labels_that_collide_once_folded_are_refused():
    relation = OrderingRelation(items=("Alfa", "alfa"), edges=())
    with pytest.raises(RelationError, match="collide once folded"):
        relation.assert_labels_are_tokens(P)


def test_single_token_labels_are_accepted():
    OrderingRelation(items=("alfa", "bravo"),
                     edges=(("alfa", "bravo"),)).assert_labels_are_tokens(P)


# ------------------------------------------------------------ label matching
RELATION = OrderingRelation(items=("alpha", "beta", "gamma"),
                            edges=(("alpha", "beta"), ("beta", "gamma")))


def test_matching_reports_the_observed_label_sequence():
    got = match_items_to_labels(parse_list("- gamma\n- alpha\n- beta", P),
                                RELATION, P)
    assert got["sequence"] == ["gamma", "alpha", "beta"]
    assert not got["unmatched_ordinals"] and not got["ambiguous"]
    assert not got["duplicated_labels"] and not got["missing_labels"]


def test_matching_folds_case_through_the_one_text_rule():
    got = match_items_to_labels(parse_list("- ALPHA\n- Beta\n- gamma", P),
                                RELATION, P)
    assert got["sequence"] == ["alpha", "beta", "gamma"]
    assert got["text_policy"] == P.text.policy_id


def test_token_membership_replaced_substring_containment():
    """The audit's two collisions, both gone."""
    overlap = OrderingRelation(items=("item1", "item10"),
                               edges=(("item1", "item10"),))
    got = match_items_to_labels(parse_list("- item1\n- item10", P), overlap, P)
    assert got["sequence"] == ["item1", "item10"]
    assert not got["ambiguous"]

    pair = OrderingRelation(items=("alfa", "bravo"), edges=(("alfa", "bravo"),))
    carried = match_items_to_labels(parse_list("- alfa\n- bravo alfaX", P), pair, P)
    assert carried["sequence"] == ["alfa", "bravo"]
    assert not carried["duplicated_labels"]


def test_the_four_ways_identification_can_be_unclear_stay_separate():
    missing = match_items_to_labels(parse_list("- alpha\n- beta", P), RELATION, P)
    assert missing["missing_labels"] == ["gamma"]

    duplicated = match_items_to_labels(
        parse_list("- alpha\n- beta\n- beta\n- gamma", P), RELATION, P)
    assert duplicated["duplicated_labels"] == ["beta"]

    unmatched = match_items_to_labels(
        parse_list("- alpha\n- beta\n- gamma\n- delta", P), RELATION, P)
    assert unmatched["unmatched_ordinals"] == [4]

    ambiguous = match_items_to_labels(parse_list("- alpha beta\n- gamma", P),
                                      RELATION, P)
    assert ambiguous["ambiguous"] == [{"ordinal": 1,
                                       "candidates": ["alpha", "beta"]}]


def test_leading_token_matching_is_the_other_implemented_candidate():
    leading = other(label_match="leading_token")
    got = match_items_to_labels(parse_list("- alpha first\n- beta\n- gamma", P),
                                RELATION, leading)
    assert got["sequence"] == ["alpha", "beta", "gamma"]
    trailing = match_items_to_labels(parse_list("- first alpha\n- beta\n- gamma", P),
                                     RELATION, leading)
    assert trailing["sequence"][0] is None
    assert got["label_match"] in LABEL_MATCH_MODES


def test_token_membership_finds_a_label_inside_a_sentence_shaped_item():
    parsed = parse_list("- First the alpha stage\n- Then beta\n- Finally gamma", P)
    assert match_items_to_labels(parsed, RELATION, P)["sequence"] == [
        "alpha", "beta", "gamma"]


def test_an_invisible_character_no_longer_hides_a_label():
    parsed = parse_list("- al\u200bpha\n- beta\n- gamma", P)
    assert match_items_to_labels(parsed, RELATION, P)["sequence"] == [
        "alpha", "beta", "gamma"]
