"""Pair 1: the two verifiers section 10.9 records as remaining to be built.

Each semantic fixture carries the reason its expected verdict follows from the
frozen rule, because a fixture without a reason is a regression lock rather than
evidence about semantics.

The ordering half is where the design decision shows. The focal rule is "place the
items in the correct transitive order", which is a relation, not a string. A
partial order can have several valid arrangements, so the test that matters is that
*all* of them pass - a verifier built on substring comparison against one expected
sequence would fail valid answers and the effect would look like interference.
"""
import pytest

from dci.v19 import verifiers as V
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation, parse_list
from dci.v19.verifiers import (
    Compliance,
    GenerationState,
    Scoring,
    Verdict,
    VerifierContractError,
)

pytestmark = pytest.mark.cpu

THREE = "- alpha\n- beta\n- gamma"
CHAIN = OrderingRelation(items=("alpha", "beta", "gamma"),
                         edges=(("alpha", "beta"), ("beta", "gamma")))


def count(text, n, **kw):
    return V.verify_exact_bullet_count(text, n_items=n, policy=P, **kw)


def order(text, relation=CHAIN, **kw):
    return V.verify_transitive_order(text, relation=relation, policy=P, **kw)


# ------------------------------------------------- the exact-count verifier
@pytest.mark.parametrize("text,n,verdict,why", [
    (THREE, 3, Verdict.PASS, "three markers, exactly three required"),
    ("- only one", 1, Verdict.PASS, "one marker, one required"),
    ("1. a\n2. b", 2, Verdict.PASS,
     "the candidate policy counts enumerated items as bullet-list items"),
    ("Here you go:\n- a\n- b", 2, Verdict.PASS,
     "a chat preamble is prose, not an item, so the count is unaffected"),
    (THREE, 2, Verdict.FAIL, "three observed against two required is not exact"),
    (THREE, 4, Verdict.FAIL, "three observed against four required is not exact"),
    ("alpha, beta, gamma", 3, Verdict.FAIL,
     "a comma-separated sentence has no list markers, so zero items are observed"),
    ("- a\n- \n- c", 3, Verdict.FAIL,
     "the candidate policy does not count a marker with no content"),
    ("-a\n-b\n-c", 3, Verdict.FAIL,
     "the candidate policy requires whitespace after the marker"),
])
def test_the_exact_count_semantic_fixtures(text, n, verdict, why):
    outcome = count(text, n)
    assert outcome.verdict is verdict, why
    assert outcome.scoring is Scoring.SCORED


@pytest.mark.parametrize("n_required", range(1, 8))
def test_the_count_boundary_at_n_minus_one_n_and_n_plus_one(n_required):
    """Exactly at, and immediately either side of, the decision boundary."""
    for observed in (n_required - 1, n_required, n_required + 1):
        if observed < 0:
            continue
        text = "\n".join(f"- item {i}" for i in range(observed))
        outcome = count(text, n_required)
        assert outcome.verdict is (Verdict.PASS if observed == n_required
                                   else Verdict.FAIL), (observed, n_required)
        assert outcome.evidence["observed_count"] == observed
        assert outcome.evidence["expected_count"] == n_required


def test_adding_one_bullet_flips_a_passing_answer_and_only_that():
    """Perturb one scientific feature; the expected change is pinned."""
    base = count(THREE, 3)
    added = count(THREE + "\n- delta", 3)
    removed = count("- alpha\n- beta", 3)
    assert base.verdict is Verdict.PASS
    assert added.verdict is Verdict.FAIL and added.evidence["observed_count"] == 4
    assert removed.verdict is Verdict.FAIL and removed.evidence["observed_count"] == 2


def test_the_compliance_field_distinguishes_partial_from_violation():
    """Section 10.1: for an exact target, PARTIAL still implies failure."""
    partial = count(THREE, 4)
    assert partial.compliance is Compliance.PARTIAL and partial.f_a == 1
    violation = count("no list here", 3)
    assert violation.compliance is Compliance.VIOLATION and violation.f_a == 1
    assert count(THREE, 3).compliance is Compliance.FULL


def test_a_missing_or_impossible_parameter_is_not_a_behavioural_failure():
    for bad in (None, 0, -1, 2.0, "3", True):
        outcome = count(THREE, bad)
        assert outcome.scoring is Scoring.MISSING_METADATA, bad
        assert outcome.verdict is None and outcome.compliance is None
        with pytest.raises(VerifierContractError, match="did not score"):
            _ = outcome.f_a


def test_an_empty_segment_fails_the_exact_target_and_records_why():
    """Section 10.1: an exact requirement that cannot be demonstrated FAILs."""
    outcome = count("", 3)
    assert outcome.scoring is Scoring.SCORED
    assert outcome.verdict is Verdict.FAIL and outcome.f_a == 1
    assert outcome.generation_state is GenerationState.EMPTY
    assert outcome.compliance is Compliance.VIOLATION


def test_a_caller_supplied_state_is_never_overwritten():
    """TRUNCATED and REFUSAL are not recoverable from the text."""
    for state in (GenerationState.TRUNCATED, GenerationState.REFUSAL):
        assert count("", 3, delivered_state=state).generation_state is state
        assert count(THREE, 3, delivered_state=state).generation_state is state


def test_the_count_evidence_carries_the_parse():
    outcome = count("Intro:\n- a\n  - b\n- \n- c", 4)
    parse = outcome.evidence["parse"]
    assert parse["policy_hash"] == P.policy_hash
    assert len(parse["items"]) == parse["observed_count"]
    assert [e["excluded_because"] for e in parse["excluded"]] == ["empty_item"]


# ---------------------------------------------------- the ordering verifier
@pytest.mark.parametrize("text,verdict,why", [
    (THREE, Verdict.PASS, "the observed order matches every required precedence"),
    ("- alpha\n- gamma\n- beta", Verdict.FAIL,
     "beta must precede gamma and does not"),
    ("- gamma\n- beta\n- alpha", Verdict.FAIL, "every edge is reversed"),
    ("- alpha\n- beta", Verdict.FAIL, "gamma never appears"),
    ("- alpha\n- beta\n- beta\n- gamma", Verdict.FAIL,
     "beta appears twice, so its position is not determined"),
    ("- alpha\n- beta\n- gamma\n- delta", Verdict.FAIL,
     "an item outside the declared set is present"),
    ("", Verdict.FAIL, "no item appears at all"),
])
def test_the_ordering_semantic_fixtures(text, verdict, why):
    assert order(text).verdict is verdict, why


def test_direct_and_transitive_precedence_are_both_checked():
    relation = OrderingRelation(items=("x1", "x2", "x4"),
                               edges=(("x2", "x4"), ("x4", "x1")))
    assert order("- x2\n- x4\n- x1", relation).verdict is Verdict.PASS
    violated = order("- x1\n- x2\n- x4", relation)
    assert violated.verdict is Verdict.FAIL
    # x2 before x1 is implied, never declared, and is what fails here.
    pairs_violated = {tuple(e) for e in violated.evidence["violated_precedences"]}
    assert ("x2", "x1") in pairs_violated
    assert ("x2", "x1") not in relation.edges


def test_reversing_exactly_one_edge_is_reported_as_exactly_one_violation():
    outcome = order("- alpha\n- gamma\n- beta")
    assert outcome.evidence["violated_precedences"] == [["beta", "gamma"]]
    assert outcome.compliance is Compliance.PARTIAL


def test_every_valid_linear_extension_of_a_partial_order_passes():
    """The design point: a relation, not an expected string."""
    partial = OrderingRelation(items=("a", "b", "c"), edges=(("a", "b"),))
    for text in ("- a\n- b\n- c", "- a\n- c\n- b", "- c\n- a\n- b"):
        assert order(text, partial).verdict is Verdict.PASS, text
    assert order("- b\n- a\n- c", partial).verdict is Verdict.FAIL


def test_an_unconstrained_relation_accepts_every_permutation():
    import itertools
    free = OrderingRelation(items=("a", "b", "c"), edges=())
    for permutation in itertools.permutations("abc"):
        text = "\n".join(f"- {label}" for label in permutation)
        assert order(text, free).verdict is Verdict.PASS, text


def test_structural_problems_are_a_violation_and_ordering_errors_are_partial():
    """A missing item is a different failure from a misplaced one."""
    assert order("- alpha\n- beta").compliance is Compliance.VIOLATION
    assert order("- alpha\n- gamma\n- beta").compliance is Compliance.PARTIAL


def test_prefix_overlapping_labels_are_no_longer_ambiguous():
    """S5/S7: token equality replaced substring containment.

    "cat" is no longer found inside "cataract", so a relation whose labels share a
    prefix is ordinary. The audit found this pair ambiguous under the old rule.
    """
    overlap = OrderingRelation(items=("cat", "cataract"),
                               edges=(("cat", "cataract"),))
    good = order("- cat\n- cataract", overlap)
    assert good.verdict is Verdict.PASS
    assert not good.evidence["identification"]["ambiguous"]
    assert order("- cataract\n- cat", overlap).verdict is Verdict.FAIL


def test_ambiguous_item_identity_is_reported_rather_than_guessed():
    """One item carrying two declared labels is genuinely undetermined."""
    outcome = order("- alpha beta\n- gamma")
    assert outcome.verdict is Verdict.FAIL
    assert outcome.evidence["identification"]["ambiguous"] == [
        {"ordinal": 1, "candidates": ["alpha", "beta"]}]
    assert "identity is not determined" in outcome.reason


def test_a_missing_relation_is_missing_metadata_not_a_failure():
    for bad in (None, {"items": ["a", "b"]}, "alpha<beta"):
        outcome = V.verify_transitive_order("- a", relation=bad, policy=P)
        assert outcome.scoring is Scoring.MISSING_METADATA
        assert outcome.verdict is None


def test_the_ordering_evidence_records_the_closure_and_the_depth():
    outcome = order(THREE)
    assert [tuple(e) for e in outcome.evidence["required_closure"]] == list(
        CHAIN.closure())
    assert outcome.evidence["chain_depth"] == 2
    assert outcome.parameters["relation_hash"] == CHAIN.relation_hash


def test_the_relation_identity_is_in_the_parameters_not_the_evidence():
    """Parameters are the realisation; evidence is how the answer was read."""
    outcome = order(THREE)
    assert set(outcome.parameters) == {"relation_hash", "declared_items",
                                       "declared_edges", "extra_items_permitted"}
    assert outcome.parameters["extra_items_permitted"] is P.extra_items_permitted


@pytest.mark.parametrize("swap", [(0, 1), (1, 2), (0, 2)])
def test_swapping_any_two_ordered_elements_fails(swap):
    labels = ["alpha", "beta", "gamma"]
    i, j = swap
    labels[i], labels[j] = labels[j], labels[i]
    text = "\n".join(f"- {label}" for label in labels)
    assert order(text).verdict is Verdict.FAIL, text


# --------------------------------------------------- the shared parser itself
def test_both_verdicts_read_the_same_parse_and_say_so():
    """Section 4.2's coupling, made explicit rather than hidden."""
    text = "- alpha\n- beta\n- gamma"
    count_parse = count(text, 3).evidence["parse"]
    order_parse = order(text).evidence["parse"]
    assert count_parse == order_parse
    assert count_parse["policy_hash"] == order_parse["policy_hash"] == P.policy_hash


@pytest.mark.parametrize("mangled,items", [
    ("-alpha\n-beta\n-gamma", 0),        # markers lost: a parser effect
    ("alpha\nbeta\ngamma", 0),           # no markers at all
    ("- alpha\n- beta\n- gamma\n- ", 3),  # a trailing empty marker
    ("- alpha beta gamma", 1),           # one item holding all three labels
])
def test_a_parser_level_perturbation_moves_both_verdicts_together(mangled, items):
    """Exactly the confound section 4.2 names, isolated so it is attributable.

    The parse is asserted directly, so a later coupling audit can show that both
    verdicts moved because the *parse* changed rather than because the model's
    behaviour did.
    """
    parsed = parse_list(mangled, P)
    assert parsed.count == items
    count_outcome, order_outcome = count(mangled, 3), order(mangled)
    if items != 3:
        assert count_outcome.verdict is Verdict.FAIL
    if items in (0, 1):
        assert order_outcome.verdict is Verdict.FAIL
        assert order_outcome.evidence["identification"]["missing_labels"]


def test_the_one_item_case_shows_why_the_parse_must_be_inspectable():
    """"- alpha beta gamma" contains all three labels in the required order.

    Containment matching therefore finds all three inside one item, so the label
    sequence is a single ambiguous entry rather than three ordered ones. The
    ordering verdict is FAIL for a *structural* reason, and the parse is what
    distinguishes that from the model having ordered the items wrongly.
    """
    outcome = order("- alpha beta gamma")
    assert outcome.verdict is Verdict.FAIL
    assert outcome.evidence["parse"]["observed_count"] == 1
    identification = outcome.evidence["identification"]
    assert identification["ambiguous"] or identification["missing_labels"]
    assert not outcome.evidence["violated_precedences"]


def test_a_formatting_only_change_leaves_both_verdicts_alone():
    """Trailing spaces and CRLF are not scientific features."""
    tidy = "- alpha\n- beta\n- gamma"
    untidy = "- alpha  \n- beta\t\n- gamma "
    assert count(untidy, 3).verdict is count(tidy, 3).verdict is Verdict.PASS
    assert order(untidy).verdict is order(tidy).verdict is Verdict.PASS
