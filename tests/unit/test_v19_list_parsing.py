"""The Pair 1 shared parser, and the decisions it refuses to make for anyone.

Section 4.2 names Pair 1's principal measurement risk as verifier coupling through
shared list parsing. The parser is therefore a separate object, and these tests are
about the parse itself rather than about either verdict - so a later coupling audit
can attribute a joint change to the parse or to the behaviour.

The other half of this file is about what the preregistration does NOT fix. Every
one of the eleven `UNDETERMINED_BY_PREREGISTRATION` fields changes verdicts, so
each is asserted to change the policy hash: answering one differently has to be
visible in the freeze rather than absorbed silently.
"""
import dataclasses

import pytest

from dci.v19 import parsing
from dci.v19.parsing import (
    INHERITED_MARKER_POLICY,
    LABEL_MATCH_MODES,
    NORMALISATIONS,
    UNDETERMINED_BY_PREREGISTRATION,
    ListPolicy,
    OrderingRelation,
    RelationError,
    match_items_to_labels,
    parse_list,
    require_policy,
)

pytestmark = pytest.mark.cpu

P = INHERITED_MARKER_POLICY


def other(**changes) -> ListPolicy:
    return dataclasses.replace(P, **changes)


# ----------------------------------------------------------- no hidden default
def test_the_parser_refuses_to_run_without_an_explicit_policy():
    """The whole design rests on this: there is nothing to fall back on."""
    for bad in (None, {}, "inherited", INHERITED_MARKER_POLICY.state()):
        with pytest.raises(TypeError, match="explicit ListPolicy"):
            parse_list("- a", bad)


def test_require_policy_returns_the_policy_unchanged():
    assert require_policy(P) is P


def test_every_parsing_decision_is_either_fixed_or_declared_open():
    parsing.assert_policy_fields_are_accounted_for()


def test_the_open_questions_cover_every_decision_field():
    decisions = {f.name for f in dataclasses.fields(ListPolicy)} - {
        "policy_id", "provenance"}
    assert set(UNDETERMINED_BY_PREREGISTRATION) == decisions
    for field, question in UNDETERMINED_BY_PREREGISTRATION.items():
        assert question and len(question) > 20, field


def test_a_new_decision_field_without_a_stated_status_is_caught():
    """A parsing decision with no recorded status is a hidden default."""
    original = parsing.UNDETERMINED_BY_PREREGISTRATION
    try:
        parsing.UNDETERMINED_BY_PREREGISTRATION = {
            k: v for k, v in original.items() if k != "nested_items_count"}
        with pytest.raises(ValueError, match="hidden default"):
            parsing.assert_policy_fields_are_accounted_for()
    finally:
        parsing.UNDETERMINED_BY_PREREGISTRATION = original
    parsing.assert_policy_fields_are_accounted_for()


def test_naming_a_field_that_does_not_exist_is_caught():
    original = parsing.UNDETERMINED_BY_PREREGISTRATION
    try:
        parsing.UNDETERMINED_BY_PREREGISTRATION = {**original, "tab_width": "?"}
        with pytest.raises(ValueError, match="not ListPolicy fields"):
            parsing.assert_policy_fields_are_accounted_for()
    finally:
        parsing.UNDETERMINED_BY_PREREGISTRATION = original


# ---------------------------------------------------------- the policy is hashed
@pytest.mark.parametrize("field,value", [
    ("bullet_markers", ("-", "*", "+")),
    ("numbered_forms", ("N.",)),
    ("numbered_max_digits", 3),
    ("require_space_after_marker", False),
    ("numbered_items_count", False),
    ("nested_items_count", False),
    ("continuation_joins_previous", False),
    ("empty_items_count", True),
    ("unicode_normalisation", "NFKC"),
    ("label_match", "leading_label"),
    ("label_case_sensitive", True),
])
def test_answering_any_open_question_differently_changes_the_policy_hash(field, value):
    """Eleven decisions, eleven distinguishable freezes."""
    assert field in UNDETERMINED_BY_PREREGISTRATION
    assert other(**{field: value}).policy_hash != P.policy_hash, field


def test_the_policy_id_is_part_of_the_hash():
    assert other(policy_id="v19:list-policy.other").policy_hash != P.policy_hash


def test_rewording_the_provenance_is_not_a_change_of_measurement():
    assert other(provenance="a different citation").policy_hash == P.policy_hash


def test_an_identical_policy_hashes_identically():
    assert dataclasses.replace(P).policy_hash == P.policy_hash


# ------------------------------------------------------- policy well-formedness
def test_a_policy_that_can_open_no_item_is_refused():
    with pytest.raises(ValueError, match="no marker can open an item"):
        other(bullet_markers=(), numbered_forms=())
    with pytest.raises(ValueError, match="no marker can open an item"):
        other(bullet_markers=(), numbered_items_count=False)


def test_a_multi_character_bullet_marker_is_refused():
    with pytest.raises(ValueError, match="not a single character"):
        other(bullet_markers=("--",))


def test_a_numbered_form_must_name_the_digits_exactly_once():
    for bad in ("1.", "N.N", ""):
        with pytest.raises(ValueError, match="exactly one 'N'"):
            other(numbered_forms=(bad,))


def test_an_unknown_normalisation_or_match_mode_is_refused():
    with pytest.raises(ValueError, match="not one of"):
        other(unicode_normalisation="NFKX")
    with pytest.raises(ValueError, match="not one of"):
        other(label_match="fuzzy")


def test_an_anonymous_policy_is_refused():
    with pytest.raises(ValueError, match="id and a provenance"):
        other(policy_id="")
    with pytest.raises(ValueError, match="id and a provenance"):
        other(provenance="")


def test_the_digit_cap_is_bounded():
    with pytest.raises(ValueError, match="outside 1..9"):
        other(numbered_max_digits=0)


# -------------------------------------------- the candidate matches the regex
@pytest.mark.parametrize("line,is_item", [
    ("- a", True), ("* a", True), ("• a", True), ("‣ a", True), ("▪ a", True),
    ("1. a", True), ("1) a", True), ("(1) a", True), ("99. a", True),
    ("100. a", False),                       # the two-digit cap
    ("-a", False),                           # the required space
    ("+ a", False),                          # not in the inherited class
    ("  - a", True),                         # any indent
    ("a", False),
])
def test_the_candidate_policy_reproduces_the_inherited_marker_regex(line, is_item):
    """The one recoverable candidate, field by field, against its source."""
    from dci.verifiers.rules import LIST_MARKER
    parsed = parse_list(line, P)
    assert bool(parsed.items) is is_item, line
    if is_item:                       # and the inherited regex agrees
        assert LIST_MARKER.match(line)


def test_the_two_digit_cap_is_recorded_as_an_open_question():
    """`100.` not being a marker matters if a calibrated n_items exceeds 99."""
    assert "two digits" in UNDETERMINED_BY_PREREGISTRATION["numbered_max_digits"]
    assert parse_list("100. a", P).count == 0
    assert parse_list("100. a", other(numbered_max_digits=3)).count == 1


# ---------------------------------------------------------------- the parse
def test_a_plain_three_item_list_parses_to_three_items_with_spans():
    parsed = parse_list("- alpha\n- beta\n- gamma", P)
    assert parsed.count == 3
    assert parsed.contents == ("alpha", "beta", "gamma")
    for item in parsed.items:
        start, end = item.span
        assert parsed.text[start:end].endswith(item.content)
    assert [i.ordinal for i in parsed.items] == [1, 2, 3]


def test_the_parse_records_the_policy_it_used():
    assert parse_list("- a\n- b", P).policy_hash == P.policy_hash


@pytest.mark.parametrize("n", range(1, 9))
def test_the_observed_count_tracks_the_number_of_markers(n):
    text = "\n".join(f"- item {i}" for i in range(n))
    assert parse_list(text, P).count == n


def test_numbered_items_count_or_do_not_according_to_the_policy():
    text = "1. alpha\n2. beta"
    assert parse_list(text, P).count == 2
    strict = parse_list(text, other(numbered_items_count=False))
    assert strict.count == 0
    assert [i.excluded_because for i in strict.excluded] == [
        "numbered_not_counted"] * 2


def test_nested_items_count_or_do_not_according_to_the_policy():
    text = "- alpha\n  - nested\n- beta"
    assert parse_list(text, P).count == 3
    flat = parse_list(text, other(nested_items_count=False))
    assert flat.count == 2
    assert [i.excluded_because for i in flat.excluded] == ["nested_not_counted"]
    assert flat.excluded[0].indent == 2


def test_a_continuation_line_joins_the_previous_item_or_is_prose():
    text = "- alpha\n  continues here\n- beta"
    joined = parse_list(text, P)
    assert joined.count == 2
    assert joined.contents == ("alpha continues here", "beta")
    assert joined.items[0].continuation_lines == 1
    split = parse_list(text, other(continuation_joins_previous=False))
    assert split.count == 2
    assert split.contents == ("alpha", "beta")
    assert len(split.prose_spans) == 1


def test_an_empty_item_counts_or_does_not_according_to_the_policy():
    text = "- alpha\n- \n- beta"
    assert parse_list(text, P).count == 2
    assert [i.excluded_because for i in parse_list(text, P).excluded] == ["empty_item"]
    assert parse_list(text, other(empty_items_count=True)).count == 3


def test_leading_and_trailing_prose_are_recorded_separately():
    parsed = parse_list("Here is the list:\n- a\n- b\nHope that helps!",
                        other(continuation_joins_previous=False))
    assert parsed.count == 2
    assert parsed.leading_prose and parsed.trailing_prose
    assert len(parsed.prose_spans) == 2


def test_a_chat_preamble_alone_is_no_items_and_all_prose():
    parsed = parse_list("Sure, I can help with that.", P)
    assert parsed.count == 0
    assert parsed.leading_prose


@pytest.mark.parametrize("text", ["", "   ", "\n\n", None])
def test_an_empty_segment_parses_to_nothing(text):
    parsed = parse_list(text, P)
    assert parsed.count == 0 and not parsed.excluded


def test_unicode_normalisation_is_applied_and_recorded():
    """A combining-mark item is one item either way; the record says which form."""
    decomposed = "- café"
    assert parse_list(decomposed, P).contents == ("café",)
    folded = parse_list(decomposed, other(unicode_normalisation="NFC"))
    assert folded.contents == ("café",)
    assert folded.normalisation == "NFC"
    assert parse_list(decomposed, P).normalisation == "none"


def test_the_marker_may_be_reached_by_compatibility_normalisation():
    """NFKC maps the fullwidth hyphen-minus onto '-', which the policy admits."""
    fullwidth = "－ item"
    assert parse_list(fullwidth, P).count == 0
    assert parse_list(fullwidth, other(unicode_normalisation="NFKC")).count == 1


def test_the_marker_and_its_kind_are_in_the_evidence():
    parsed = parse_list("- a\n1. b", P)
    assert [(i.marker, i.marker_kind) for i in parsed.items] == [
        ("-", "bullet"), ("1.", "numbered")]


def test_the_description_is_serialisable_and_complete():
    import json
    described = parse_list("Intro:\n- a\n  - b\n- \n- c", P).describe()
    json.dumps(described)
    assert set(described) == {"policy_hash", "normalisation", "observed_count",
                              "items", "excluded", "prose_spans",
                              "leading_prose", "trailing_prose"}
    assert described["observed_count"] == len(described["items"])


def test_dropping_the_space_requirement_admits_tight_markers():
    tight = other(require_space_after_marker=False)
    assert parse_list("-a\n-b", tight).count == 2
    assert parse_list("-a\n-b", P).count == 0


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


def test_a_self_edge_is_refused():
    with pytest.raises(RelationError, match="cannot precede itself"):
        OrderingRelation(items=("a", "b"), edges=(("a", "a"),))


def test_a_duplicate_edge_is_refused():
    with pytest.raises(RelationError, match="duplicate edges"):
        OrderingRelation(items=("a", "b"), edges=(("a", "b"), ("a", "b")))


def test_a_cyclic_specification_is_impossible_not_merely_failing():
    """Section 8.6: an impossible composition is outside the estimand."""
    with pytest.raises(RelationError, match="contain a cycle"):
        OrderingRelation(items=("a", "b"), edges=(("a", "b"), ("b", "a")))
    with pytest.raises(RelationError, match="contain a cycle"):
        OrderingRelation(items=("a", "b", "c"),
                         edges=(("a", "b"), ("b", "c"), ("c", "a")))


def test_the_closure_adds_the_implied_precedences():
    """x2 before x4 and x4 before x1 imply x2 before x1."""
    relation = OrderingRelation(items=("x1", "x2", "x4"),
                                edges=(("x2", "x4"), ("x4", "x1")))
    assert relation.closure() == (("x2", "x1"), ("x2", "x4"), ("x4", "x1"))


def test_the_closure_of_a_chain_is_every_forward_pair():
    chain = OrderingRelation(items=("a", "b", "c", "d"),
                             edges=(("a", "b"), ("b", "c"), ("c", "d")))
    assert len(chain.closure()) == 6
    assert ("a", "d") in chain.closure()


def test_the_closure_is_empty_when_nothing_is_required():
    assert OrderingRelation(items=("a", "b"), edges=()).closure() == ()


@pytest.mark.parametrize("edges,depth", [
    ((), 0),
    ((("a", "b"),), 1),
    ((("a", "b"), ("b", "c")), 2),
    ((("a", "b"), ("a", "c")), 1),
    ((("a", "b"), ("b", "c"), ("c", "d")), 3),
])
def test_the_chain_depth_is_the_longest_required_chain(edges, depth):
    items = ("a", "b", "c", "d")
    assert OrderingRelation(items=items, edges=edges).chain_depth == depth


def test_the_chain_depth_is_not_the_declared_ordering_depth_parameter():
    """`pairs.PAIR_1` declares `ordering_depth`; v19 never defines it."""
    from dci.v19 import pairs
    assert pairs.PAIR_1.focal.parameters == ("ordering_depth",)
    assert "ordering_depth" not in OrderingRelation(
        items=("a", "b"), edges=()).state()


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


# ------------------------------------------------------------ label matching
RELATION = OrderingRelation(items=("alpha", "beta", "gamma"),
                            edges=(("alpha", "beta"), ("beta", "gamma")))


def test_matching_reports_the_observed_label_sequence():
    parsed = parse_list("- gamma\n- alpha\n- beta", P)
    got = match_items_to_labels(parsed, RELATION, P)
    assert got["sequence"] == ["gamma", "alpha", "beta"]
    assert not got["unmatched_ordinals"] and not got["ambiguous"]
    assert not got["duplicated_labels"] and not got["missing_labels"]


def test_matching_is_case_insensitive_or_not_according_to_the_policy():
    parsed = parse_list("- ALPHA\n- Beta\n- gamma", P)
    assert match_items_to_labels(parsed, RELATION, P)["sequence"] == [
        "alpha", "beta", "gamma"]
    strict = match_items_to_labels(parsed, RELATION,
                                   other(label_case_sensitive=True))
    assert strict["sequence"] == [None, None, "gamma"]
    assert strict["missing_labels"] == ["alpha", "beta"]


def test_the_four_ways_identification_can_be_unclear_stay_separate():
    """Missing, duplicated, ambiguous and unmatched are different facts."""
    missing = match_items_to_labels(parse_list("- alpha\n- beta", P), RELATION, P)
    assert missing["missing_labels"] == ["gamma"]

    duplicated = match_items_to_labels(
        parse_list("- alpha\n- beta\n- beta\n- gamma", P), RELATION, P)
    assert duplicated["duplicated_labels"] == ["beta"]

    unmatched = match_items_to_labels(
        parse_list("- alpha\n- beta\n- gamma\n- delta", P), RELATION, P)
    assert unmatched["unmatched_ordinals"] == [4]

    overlap = OrderingRelation(items=("cat", "cataract"), edges=(("cat", "cataract"),))
    ambiguous = match_items_to_labels(parse_list("- cataract\n- cat", P),
                                      overlap, P)
    assert ambiguous["ambiguous"] == [{"ordinal": 1,
                                       "candidates": ["cat", "cataract"]}]


def test_leading_label_matching_resolves_the_containment_ambiguity():
    """The other implemented candidate; which one is frozen is a decision."""
    overlap = OrderingRelation(items=("cat", "cataract"),
                               edges=(("cat", "cataract"),))
    leading = other(label_match="leading_label")
    got = match_items_to_labels(parse_list("- cat sleeps\n- cataract forms", P),
                                overlap, leading)
    assert got["sequence"] == ["cat", "cataract"] or got["ambiguous"]
    assert got["label_match"] == "leading_label"


def test_containment_finds_a_label_inside_a_sentence_shaped_item():
    parsed = parse_list("- First, the alpha stage.\n- Then beta.\n- Finally gamma.",
                        P)
    assert match_items_to_labels(parsed, RELATION, P)["sequence"] == [
        "alpha", "beta", "gamma"]


def test_the_match_record_names_the_rule_it_applied():
    got = match_items_to_labels(parse_list("- alpha\n- beta\n- gamma", P),
                                RELATION, P)
    assert got["label_match"] in LABEL_MATCH_MODES
    assert got["label_case_sensitive"] is False


def test_every_declared_normalisation_form_is_usable():
    for form in NORMALISATIONS:
        assert parse_list("- a", other(unicode_normalisation=form)).count == 1
