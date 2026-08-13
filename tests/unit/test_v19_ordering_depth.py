"""Amendment A4: ordering depth is longest-chain cardinality, under one generator.

Two claims need separate evidence.

The STATISTIC is well defined on any relation: depth is the number of items in the
longest chain, and the tests below pin it against hand-computed cases, against the
pre-existing edge-counting `chain_depth`, and against the closure (which must not
change it, because the closure of a chain adds precedences without deepening it).

The GENERATOR is what makes the statistic mean "how deep is the required order"
rather than "how constrained is the relation". Under A4 a depth-d relation is one
chain of d items with the other N - d explicitly unconstrained, so edge count,
constrained-item count and free-item count are all functions of d alone. Those are
the confounds the tests rule out, by showing that off the canonical form a single
depth admits relations that differ in every one of them.
"""
from __future__ import annotations

import json

import pytest

from dci.v19 import ordering as O
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation

pytestmark = pytest.mark.cpu

LABELS = tuple(f"item{i:03d}" for i in range(8))


def relation(items, edges):
    return OrderingRelation(items=tuple(items), edges=tuple(edges))


# ----------------------------------------------------------------- the statistic
@pytest.mark.parametrize("edges,expected", [
    ((), 1),
    ((("a", "b"),), 2),
    ((("a", "b"), ("b", "c")), 3),
    ((("a", "b"), ("b", "c"), ("c", "d")), 4),
    ((("a", "b"), ("c", "d")), 2),                       # two chains of two
    ((("a", "b"), ("a", "c"), ("a", "d")), 2),           # a star, depth 2
    ((("a", "d"), ("b", "d"), ("c", "d")), 2),           # a merge, depth 2
    ((("a", "b"), ("b", "d"), ("a", "c")), 3),           # longest path wins
])
def test_the_depth_is_the_longest_chain_counted_in_items(edges, expected):
    assert O.ordering_depth(relation("abcd", edges)) == expected


def test_depth_counts_items_where_chain_depth_counts_edges():
    """The distinction A4 turns on, asserted rather than left to be assumed."""
    for edges in ((), (("a", "b"),), (("a", "b"), ("b", "c"))):
        r = relation("abcd", edges)
        assert O.ordering_depth(r) == r.chain_depth + 1


def test_the_closure_does_not_change_the_depth():
    """A chain's closure adds precedences; it does not make the order deeper."""
    chain = relation("abcd", (("a", "b"), ("b", "c"), ("c", "d")))
    closed = relation("abcd", chain.closure())
    assert len(closed.edges) > len(chain.edges)
    assert O.ordering_depth(closed) == O.ordering_depth(chain) == 4


def test_the_depth_of_a_total_order_is_the_item_count():
    items = LABELS[:5]
    total = relation(items, tuple((items[i], items[i + 1]) for i in range(4)))
    assert O.ordering_depth(total) == len(items) == 5


@pytest.mark.parametrize("bad", [None, "a chain", 3, (), {"items": []}])
def test_the_statistic_refuses_anything_but_a_relation(bad):
    with pytest.raises(O.OrderingDepthError, match="OrderingRelation"):
        O.ordering_depth(bad)


# ------------------------------------------------------- constrained and free
def test_constrained_and_free_items_partition_the_declared_set():
    r = relation(LABELS[:6], (("item000", "item001"), ("item001", "item002")))
    assert O.constrained_items(r) == ("item000", "item001", "item002")
    assert O.free_items(r) == ("item003", "item004", "item005")
    assert set(O.constrained_items(r)) | set(O.free_items(r)) == set(r.items)
    assert not set(O.constrained_items(r)) & set(O.free_items(r))


def test_free_items_are_reported_in_declaration_order():
    r = relation(("d", "c", "b", "a"), (("a", "b"),))
    assert O.free_items(r) == ("d", "c")


# ------------------------------------------------------------ the canonical form
def test_the_chain_is_recovered_from_a_canonical_relation():
    r = relation(LABELS[:5], (("item002", "item000"), ("item000", "item004")))
    assert O.chain_of(r) == ("item002", "item000", "item004")
    assert O.assert_canonical_form(r) == ("item002", "item000", "item004")


@pytest.mark.parametrize("edges,why", [
    ((("a", "b"), ("a", "c")), "a branch"),
    ((("a", "c"), ("b", "c")), "a merge"),
    ((("a", "b"), ("c", "d")), "two disconnected chains"),
    ((("a", "b"), ("b", "c"), ("a", "c")), "a transitive shortcut, not a cover"),
    ((), "no precedence at all"),
])
def test_a_non_canonical_relation_is_refused_with_its_reason(edges, why):
    with pytest.raises(O.OrderingDepthError, match="one chain plus free items") as caught:
        O.assert_canonical_form(relation("abcd", edges))
    assert "one chain of d items" in str(caught.value), why


def test_the_closure_of_a_chain_is_not_canonical_because_it_is_not_covers():
    """A4 exposes covers; the closure of a 4-chain has six edges for four items."""
    chain = relation("abcd", (("a", "b"), ("b", "c"), ("c", "d")))
    O.assert_canonical_form(chain)
    with pytest.raises(O.OrderingDepthError):
        O.assert_canonical_form(relation("abcd", chain.closure()))


# ------------------------------------------------------------- the generator
@pytest.mark.parametrize("n_items", [2, 3, 5, 8])
def test_the_generator_realises_exactly_the_requested_depth(n_items):
    for depth in range(O.MIN_DEPTH, n_items + 1):
        built = O.generate(LABELS[:n_items], depth, P, seed=0)
        assert O.ordering_depth(built) == depth
        assert len(built.items) == n_items


@pytest.mark.parametrize("depth", [2, 3, 4, 5, 6, 7, 8])
def test_edge_count_constrained_and_free_are_functions_of_depth_alone(depth):
    """The whole point of freezing the generator with the statistic."""
    built = O.generate(LABELS, depth, P, seed=0)
    assert len(built.edges) == depth - 1
    assert len(O.constrained_items(built)) == depth
    assert len(O.free_items(built)) == len(LABELS) - depth


def test_every_generated_relation_is_in_the_canonical_form():
    for depth in range(O.MIN_DEPTH, len(LABELS) + 1):
        for seed in range(6):
            built = O.generate(LABELS, depth, P, seed=seed)
            assert len(O.assert_canonical_form(built)) == depth


def test_the_generator_exposes_covers_and_not_the_closure():
    built = O.generate(LABELS, 5, P, seed=3)
    assert len(built.edges) == 4
    assert len(built.closure()) == 10          # 5 choose 2, computed internally
    assert set(built.edges) < set(built.closure())


def test_the_verifier_may_still_compute_the_closure_internally():
    from dci.v19 import verifiers as V
    from dci.v19.verifiers import Verdict
    built = O.generate(("alfa", "bravo", "charlie"), 3, P, seed=0)
    chain = O.chain_of(built)
    text = "\n".join(f"- {label}" for label in chain)
    outcome = V.verify_transitive_order(text, relation=built, policy=P)
    assert outcome.verdict is Verdict.PASS
    # The closure is what was evaluated, even though only covers were exposed.
    assert len(outcome.evidence["required_closure"]) == 3


# ---------------------------------------------------- determinism and variation
def test_the_generator_is_deterministic_in_labels_depth_and_seed():
    a = O.generate(LABELS, 4, P, seed=7)
    b = O.generate(LABELS, 4, P, seed=7)
    assert a.state() == b.state()
    assert a.relation_hash == b.relation_hash


def test_a_different_seed_gives_a_different_realisation_at_the_same_depth():
    built = [O.generate(LABELS, 4, P, seed=s) for s in range(12)]
    assert all(O.ordering_depth(r) == 4 for r in built)
    assert len({r.relation_hash for r in built}) > 1


def test_the_generator_randomises_chain_membership():
    chains = {O.chain_of(O.generate(LABELS, 3, P, seed=s)) for s in range(30)}
    members = {frozenset(chain) for chain in chains}
    assert len(members) > 1, "membership never varied"


def test_the_generator_randomises_the_chain_order():
    """Otherwise the chain is always the declared order and depth is not tested."""
    seen = set()
    for seed in range(30):
        built = O.generate(LABELS, 4, P, seed=seed)
        chain = O.chain_of(built)
        seen.add(tuple(sorted(chain)) == chain)
    assert seen == {True, False} or False in seen


def test_the_generator_randomises_the_presentation_order():
    """A prompt that lists the items already in the required order tests nothing."""
    copied = 0
    for seed in range(40):
        built = O.generate(LABELS, 4, P, seed=seed)
        chain = O.chain_of(built)
        shown = [i for i in built.items if i in set(chain)]
        if tuple(shown) == chain:
            copied += 1
    assert copied < 40, "the presentation order always matched the required order"


def test_the_declared_items_are_a_permutation_of_the_labels_given():
    built = O.generate(LABELS, 5, P, seed=2)
    assert sorted(built.items) == sorted(LABELS)


# ------------------------------------------------------------ the admissible range
@pytest.mark.parametrize("depth", [1, 0, -1])
def test_a_depth_below_two_is_refused_because_the_constraint_would_be_vacuous(depth):
    with pytest.raises(O.OrderingDepthError, match="vacuous"):
        O.generate(LABELS, depth, P, seed=0)


def test_a_depth_above_the_item_count_is_refused():
    with pytest.raises(O.OrderingDepthError, match="items that do not exist"):
        O.generate(LABELS[:4], 5, P, seed=0)


@pytest.mark.parametrize("bad", [None, "3", 3.0, True])
def test_a_non_integer_depth_is_refused(bad):
    with pytest.raises(O.OrderingDepthError):
        O.generate(LABELS, bad, P, seed=0)


@pytest.mark.parametrize("bad", [-1, "0", None, True, 1.5])
def test_a_bad_seed_is_refused_rather_than_coerced(bad):
    with pytest.raises(O.OrderingDepthError, match="seed"):
        O.generate(LABELS, 3, P, seed=bad)


def test_duplicate_labels_are_refused():
    with pytest.raises(O.OrderingDepthError, match="duplicate"):
        O.generate(("a", "b", "a"), 2, P, seed=0)


def test_a_label_the_tokeniser_would_split_is_refused_at_generation():
    from dci.v19.parsing import RelationError
    with pytest.raises(RelationError, match="single word tokens"):
        O.generate(("alfa bravo", "charlie", "delta"), 2, P, seed=0)


def test_the_generator_requires_an_explicit_grammar():
    with pytest.raises(TypeError, match="explicit ListPolicy"):
        O.generate(LABELS, 3, None, seed=0)


# ------------------------------------------------------- confound demonstrations
def test_off_the_canonical_form_one_depth_admits_wildly_different_relations():
    """Why the generator had to be frozen alongside the statistic.

    All three of these have depth 2 and differ in edge count, constrained-item
    count and free-item count. If the protocol could generate any of them,
    "ordering depth" would not name a single manipulation.
    """
    items = LABELS[:6]
    minimal = relation(items, ((items[0], items[1]),))
    star = relation(items, tuple((items[0], items[i]) for i in range(1, 6)))
    paired = relation(items, ((items[0], items[1]), (items[2], items[3]),
                              (items[4], items[5])))
    for r in (minimal, star, paired):
        assert O.ordering_depth(r) == 2
    # Three different edge counts at one depth: 1, 5 and 3.
    assert {len(r.edges) for r in (minimal, star, paired)} == {1, 5, 3}
    # And two different free-item counts: the minimal relation leaves four items
    # unconstrained, the other two leave none.
    assert {len(O.free_items(r)) for r in (minimal, star, paired)} == {4, 0}
    # Only the minimal one is what A4 generates.
    O.assert_canonical_form(minimal)
    for r in (star, paired):
        with pytest.raises(O.OrderingDepthError):
            O.assert_canonical_form(r)


def test_the_canonical_form_removes_the_confound_at_every_depth():
    signatures = {}
    for depth in range(O.MIN_DEPTH, len(LABELS) + 1):
        for seed in range(5):
            built = O.generate(LABELS, depth, P, seed=seed)
            signature = (len(built.edges), len(O.constrained_items(built)),
                         len(O.free_items(built)))
            signatures.setdefault(depth, set()).add(signature)
    for depth, seen in signatures.items():
        assert len(seen) == 1, (depth, seen)


# --------------------------------------------------------------- the realisation
def test_the_realisation_record_is_auditable_and_serialisable():
    record = O.realisation(LABELS, 4, P, seed=1)
    assert record["ordering_depth"] == 4
    assert record["statistic"] == O.STATISTIC_ID
    assert record["generator"] == O.GENERATOR_ID
    assert len(record["chain"]) == 4
    assert len(record["free_items"]) == len(LABELS) - 4
    assert record["n_cover_edges"] == 3
    serialisable = {k: v for k, v in record.items() if k != "relation"}
    assert json.loads(json.dumps(serialisable)) == serialisable


# ------------------------------------------------------------ the decision value
def test_the_decision_names_the_statistic_and_the_generator_the_code_implements():
    assert O.DECISION["statistic"] == O.STATISTIC_ID
    assert O.DECISION["generator"] == O.GENERATOR_ID
    assert O.DECISION["min_depth"] == O.MIN_DEPTH == 2
    assert O.DECISION["max_depth_rule"] == "n_items"
    assert O.DECISION["exposes"] == O.EXPOSES == "cover_relations"


def test_larger_depth_is_the_nominal_harder_direction():
    assert O.DECISION["harder_direction"] == "increasing" == O.HARDER_DIRECTION


def test_the_decision_carries_no_grid_because_the_grid_is_a_stage_five_output():
    """Section 6.2's ordered grid is D6, reached by boundary calibration."""
    assert O.DECISION["grid"] is None
    assert "Stage 5" in O.DECISION["grid_rule"]
    assert "D6" in O.DECISION["grid_rule"]


def test_the_rejected_alternatives_are_recorded_with_reasons():
    rejected = O.DECISION["rejected_alternatives"]
    assert set(rejected) == {"n_items", "edge_count", "linear_extension_count"}
    for name, reason in rejected.items():
        assert reason.strip(), name


def test_item_count_is_rejected_for_a_stated_reason_not_a_preference():
    assert "n_items" in O.DECISION["rejected_alternatives"]["n_items"]
    assert "confound" in O.DECISION["rejected_alternatives"]["n_items"]


def test_the_decision_is_serialisable_because_it_is_frozen_into_the_registry():
    assert json.loads(json.dumps(O.DECISION)) == O.DECISION
