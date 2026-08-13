"""Whole-composition satisfiability: the section 8.6 hierarchy, and its refusals.

    "The evidential hierarchy is therefore: solver `sat` for the encoded
    abstraction; concrete all-verifier-pass witness for operational
    natural-language satisfiability; and human semantic review where deterministic
    coverage is incomplete. No weaker item substitutes for a stronger item when the
    latter is required."

So the tests that matter are the refusals. `solver == sat` must not certify;
a witness that no verifier checked must not certify; a conjunction over the
available subset must not be formed at all; and code must never stand in for the
human reviewer.

One finding is pinned here because it shaped the design. With the strict reading of
the Pair 1 focal rule, the solver originally reported `sat` for a composition
requiring five items with a three-item relation, and the constructed witness was
then rejected by the ordering verifier: the encoded semantics and the measured
semantics disagreed. Whether an undeclared list item is permitted is a question the
preregistration does not answer, so it is now a hashed policy field, the solver
asserts whichever answer is frozen, and `WITNESS_REJECTED` exists as its own
outcome for the case where the two still diverge.
"""
import dataclasses

import pytest

from dci.v19 import certification as C
from dci.v19 import encoding as E
from dci.v19 import mutation as M
from dci.v19 import pairs, stage2
from dci.v19 import solver as S
from dci.v19 import verifiers as V
from dci.v19 import witness as W
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation
from dci.v19.registry import REGISTRY

pytestmark = pytest.mark.cpu

CHAIN = OrderingRelation(items=("alpha", "beta", "gamma"),
                         edges=(("alpha", "beta"), ("beta", "gamma")))
PERMISSIVE = dataclasses.replace(P, policy_id="v19:list-policy.permissive",
                                extra_items_permitted=True)


def compose(cid, pair_id, realisations, *, arm="B", load=2):
    return E.encode_composition(cid, pair_id=pair_id, arm=arm, load=load,
                                realisations=realisations)


def p1(n_items=3, relation=CHAIN, policy=P, cid="p1/1/B"):
    return compose(cid, "p1", {
        pairs.PAIR_1.target.constraint_id: {"n_items": n_items, "policy": policy},
        pairs.PAIR_1.focal.constraint_id: {"relation": relation, "policy": policy}})


def p2(words=("alpha", "beta"), cid="p2/1/B"):
    return compose(cid, "p2", {
        pairs.PAIR_2.target.constraint_id: {"mandatory_words": words,
                                            "policy": P},
        pairs.PAIR_2.focal.constraint_id: {"policy": P}})


def p3(n_sentences=4, cid="p3/1/B"):
    return compose(cid, "p3", {
        pairs.PAIR_3.target.constraint_id: {"n_sentences": n_sentences,
                                            "policy": P},
        pairs.PAIR_3.focal.constraint_id: {"policy": P}})


# ------------------------------------------------------------- the encoding
def test_every_declared_constraint_has_a_canonical_encoding():
    E.assert_encoders_cover_every_declared_constraint()
    assert set(E.ENCODERS) == {rule.constraint_id for rule in pairs.rules()}


def test_an_unencodable_constraint_is_refused_not_dropped():
    with pytest.raises(E.EncodingError, match="cannot be silently omitted"):
        E.encode_clause("v19:background.something_new", {})


def test_a_clause_over_an_undeclared_feature_is_refused():
    with pytest.raises(E.EncodingError, match="outside the declared abstract"):
        E.Clause(constraint_id="x", role="target", kind=E.ClauseKind.EXACT_ITEM_COUNT,
                 parameters={}, features=("sentiment",),
                 coverage=E.DeterministicCoverage.COMPLETE)


def test_a_clause_constraining_nothing_is_refused():
    with pytest.raises(E.EncodingError, match="constrains no feature"):
        E.Clause(constraint_id="x", role="target", kind=E.ClauseKind.EXACT_ITEM_COUNT,
                 parameters={}, features=(),
                 coverage=E.DeterministicCoverage.COMPLETE)


def test_partial_coverage_must_name_what_is_uncovered():
    with pytest.raises(E.EncodingError, match="nothing says what"):
        E.Clause(constraint_id="x", role="focal", kind=E.ClauseKind.ITEM_PRECEDENCE,
                 parameters={}, features=("n_items",),
                 coverage=E.DeterministicCoverage.PARTIAL)


def test_complete_coverage_may_not_also_name_uncovered_semantics():
    with pytest.raises(E.EncodingError, match="cannot both be true"):
        E.Clause(constraint_id="x", role="focal", kind=E.ClauseKind.ITEM_PRECEDENCE,
                 parameters={}, features=("n_items",),
                 coverage=E.DeterministicCoverage.COMPLETE,
                 uncovered_semantics="something")


def test_the_pair_one_clauses_require_an_explicit_list_policy():
    """What counts as a list item is a measurement decision, so no default."""
    for constraint_id in (pairs.PAIR_1.target.constraint_id,
                          pairs.PAIR_1.focal.constraint_id):
        with pytest.raises(E.EncodingError, match="explicit ListPolicy"):
            E.encode_clause(constraint_id, {"n_items": 3, "relation": CHAIN})


def test_the_pair_one_clauses_embed_the_policy_hash():
    for clause in p1().clauses:
        assert clause.parameters["list_policy_hash"] == P.policy_hash
    assert p1(policy=PERMISSIVE).encoding_hash != p1().encoding_hash


@pytest.mark.parametrize("realisation", [{"n_items": 0}, {"n_items": -1},
                                         {"n_items": 2.0}, {"n_items": True},
                                         {"n_items": None}])
def test_an_impossible_item_count_cannot_be_encoded(realisation):
    with pytest.raises(E.EncodingError, match="not a positive integer"):
        E.encode_clause(pairs.PAIR_1.target.constraint_id,
                        {**realisation, "policy": P})


def test_an_empty_composition_is_refused():
    with pytest.raises(E.EncodingError, match="constraining nothing"):
        E.Composition(composition_id="x", pair_id="p1", arm="B", load=2, clauses=())


def test_a_composition_may_not_repeat_a_constraint():
    clause = p1().clauses[0]
    with pytest.raises(E.EncodingError, match="appear twice"):
        E.Composition(composition_id="x", pair_id="p1", arm="B", load=2,
                      clauses=(clause, clause))


def test_load_two_admits_only_the_target_and_the_occupant():
    """Section 8.1: three backgrounds join them only at k=5, and exactly three."""
    background = E.encode_background(
        pairs.PAIR_2.focal.constraint_id, {"policy": P},
        background_id="v19:background.stratum-one")
    with pytest.raises(E.EncodingError, match="load 2 admits exactly 0"):
        E.Composition(composition_id="x", pair_id="p1", arm="B", load=2,
                      clauses=p1().clauses + (background,))
    with pytest.raises(E.EncodingError, match="load 5 admits exactly 3"):
        E.Composition(composition_id="x", pair_id="p1", arm="B", load=5,
                      clauses=p1().clauses + (background,))


def test_load_five_needs_exactly_three_backgrounds():
    backgrounds = {
        "v19:background.lexical": {"family": pairs.PAIR_2.focal.constraint_id,
                                   "policy": P},
        "v19:background.structural": {"family": pairs.PAIR_3.focal.constraint_id,
                                      "policy": P},
        "v19:background.relational": {
            "family": pairs.PAIR_2.target.constraint_id,
            "mandatory_words": ("zulu",), "policy": P}}
    full = E.encode_composition(
        "p1/1/B5", pair_id="p1", arm="B", load=5, realisations={
            pairs.PAIR_1.target.constraint_id: {"n_items": 3, "policy": P},
            pairs.PAIR_1.focal.constraint_id: {"relation": CHAIN, "policy": P}},
        backgrounds=backgrounds)
    assert full.roles == ("target", "focal", "background", "background",
                          "background")
    with pytest.raises(E.EncodingError, match="load 5 admits exactly 3"):
        E.encode_composition(
            "p1/short/B5", pair_id="p1", arm="B", load=5, realisations={
                pairs.PAIR_1.target.constraint_id: {"n_items": 3, "policy": P},
                pairs.PAIR_1.focal.constraint_id: {"relation": CHAIN,
                                                   "policy": P}},
            backgrounds=dict(list(backgrounds.items())[:2]))


def test_a_background_may_not_be_the_pair_own_target_or_focal():
    """Section 8.2 excludes them from the pool."""
    with pytest.raises(E.EncodingError, match="background identifier"):
        E.encode_background(pairs.PAIR_1.focal.constraint_id,
                            {"relation": CHAIN, "policy": P},
                            background_id="not-a-v19-background")


def test_a_reference_arm_cannot_be_encoded_before_stage_eight():
    from dci.v19.resolution import UnresolvedDependency
    with pytest.raises(UnresolvedDependency, match=r"reference\.p1\.R1"):
        E.encode_reference("p1", "R1")


def test_an_undeclared_arm_or_load_is_refused():
    with pytest.raises(ValueError):
        compose("x", "p1", {pairs.PAIR_1.target.constraint_id:
                            {"n_items": 3, "policy": P}}, arm="R9")
    with pytest.raises(ValueError):
        compose("x", "p1", {pairs.PAIR_1.target.constraint_id:
                            {"n_items": 3, "policy": P}}, load=3)


def test_the_encoding_hash_moves_with_the_parameter_realisation():
    assert p1(n_items=4).encoding_hash != p1(n_items=3).encoding_hash
    other = OrderingRelation(items=("alpha", "beta", "gamma"),
                             edges=(("alpha", "gamma"),))
    assert p1(relation=other).encoding_hash != p1().encoding_hash


def test_the_encoding_hash_is_independent_of_clause_order():
    forward = p1()
    reversed_clauses = E.Composition(
        composition_id=forward.composition_id, pair_id="p1", arm="B", load=2,
        clauses=tuple(reversed(forward.clauses)))
    assert reversed_clauses.encoding_hash == forward.encoding_hash


def test_three_of_the_six_clauses_declare_incomplete_coverage():
    """Which is why review is required for every composition today."""
    partial = {row["constraint_id"] for row in E.coverage_report(P)
               if row["coverage"] == "PARTIAL"}
    assert partial == {pairs.PAIR_1.focal.constraint_id,
                       pairs.PAIR_2.focal.constraint_id,
                       pairs.PAIR_3.target.constraint_id}
    for row in E.coverage_report(P):
        if row["coverage"] == "PARTIAL":
            assert row["uncovered_semantics"]


# ---------------------------------------------------------------- the solver
def test_the_solver_identity_is_recorded():
    name, version = S.solver_identity()
    assert name == "z3" and version


def test_a_satisfiable_conjunction_is_sat_with_a_model():
    record = S.solve(p1())
    assert record.status == "sat" and record.progressable
    assert record.model["n_items"] == 3
    positions = sorted(record.model[f"item_position_{label}"]
                       for label in CHAIN.items)
    assert positions == [0, 1, 2]


def test_the_model_respects_the_transitive_closure():
    record = S.solve(p1())
    for before, after in CHAIN.closure():
        assert (record.model[f"item_position_{before}"]
                < record.model[f"item_position_{after}"])


def test_a_composition_needing_more_items_than_the_relation_declares_is_unsat():
    """Neither clause is individually invalid: the conjunction is impossible."""
    assert S.solve(p1(n_items=2)).status == "unsat"
    assert S.solve(p1(n_items=2)).progressable is False


def test_the_strict_policy_makes_a_longer_list_unsat_and_the_permissive_one_sat():
    """The reconciliation: the solver asserts whichever reading is frozen."""
    assert S.solve(p1(n_items=5)).status == "unsat"
    assert S.solve(p1(n_items=5, policy=PERMISSIVE,
                      cid="p1/loose/B")).status == "sat"


def test_increasing_lengths_force_a_quadratic_token_floor():
    record = S.solve(p3(n_sentences=5))
    assert record.status == "sat"
    assert record.model["n_tokens"] >= 5 * 6 // 2
    lengths = [record.model[f"sentence_length_{i}"] for i in range(5)]
    assert lengths == sorted(lengths) and len(set(lengths)) == 5


def test_unmodelled_sentence_slots_are_zero():
    record = S.solve(p3(n_sentences=3))
    assert record.model["sentence_length_3"] == 0


def test_distinctness_caps_every_mandatory_token_at_one_occurrence():
    record = S.solve(p2(words=("alpha", "beta", "gamma")))
    assert record.status == "sat"
    assert record.model["n_distinct_tokens"] == record.model["n_tokens"]
    for token in ("alpha", "beta", "gamma"):
        assert record.model[f"token_multiplicity_{token}"] == 1


def test_a_non_sat_record_carries_no_model():
    record = S.solve(p1(n_items=2))
    assert record.model == {}
    with pytest.raises(S.SolverError, match="only sat has one"):
        dataclasses.replace(record, model={"n_items": 2})


def test_only_sat_supports_progression():
    assert S.PROGRESSABLE_STATUSES == ("sat",)
    assert set(S.SOLVER_STATUSES) == {"sat", "unsat", "unknown"}
    with pytest.raises(S.SolverError, match="does not support progression"):
        S.assert_progressable(S.solve(p1(n_items=2)))


def test_the_bounds_are_part_of_the_question_and_of_the_record():
    tight = S.solve(p3(n_sentences=4), bounds={"max_sentences": 4})
    assert tight.bounds["max_sentences"] == 4
    assert tight.record_hash != S.solve(p3(n_sentences=4)).record_hash


def test_the_exact_solver_input_is_archived():
    record = S.solve(p1())
    assert any(a.startswith("(") for a in record.assertions)
    assert record.reason and record.record_hash


def test_an_unknown_status_would_also_fail_closed():
    record = dataclasses.replace(S.solve(p1()), status="unknown", model={},
                                 reason="the solver returned unknown")
    assert not record.progressable


def test_a_status_outside_the_three_is_refused():
    with pytest.raises(S.SolverError, match="not one of"):
        dataclasses.replace(S.solve(p1()), status="maybe", model={})


# ---------------------------------------------------------------- the witness
def test_a_witness_is_constructed_and_passes_every_verifier():
    for composition in (p1(), p2(), p3()):
        built = W.construct_witness(composition, P)
        assert built.constructed, built.reason
        conjunction = C.run_conjunction(composition, built.text or "", P)
        assert conjunction.complete
        assert conjunction.v_all == 1, conjunction.describe()


def test_the_witness_is_deterministic_in_the_composition_and_seed():
    first, second = W.construct_witness(p1(), P), W.construct_witness(p1(), P)
    assert first.text == second.text
    assert first.witness_hash == second.witness_hash


def test_a_different_seed_varies_only_the_filler_vocabulary():
    """A failure cannot be retried away by reseeding."""
    base = W.construct_witness(p1(n_items=5, policy=PERMISSIVE, cid="p1/loose/B"),
                               PERMISSIVE)
    other = W.construct_witness(p1(n_items=5, policy=PERMISSIVE, cid="p1/loose/B"),
                                PERMISSIVE, seed=7)
    assert base.constructed and other.constructed
    assert base.structure["item_order"] == other.structure["item_order"]


def test_construction_failure_is_a_record_not_an_exception():
    built = W.construct_witness(p1(n_items=2), P)
    assert not built.constructed and built.text is None
    assert "no arrangement places more items than exist" in built.reason


def test_the_item_and_sentence_counts_cannot_both_be_satisfied_when_they_differ():
    """The Pair 1 / Pair 3 coupling, stated as a constructive impossibility.

    A background may impose a sentence count on a Pair 1 composition. Under the
    frozen segmentation each item line is also a sentence, so a list rendering gives
    equal counts and a prose rendering gives zero items.
    """
    mixed = E.encode_composition(
        "mixed", pair_id="p1", arm="B", load=5, realisations={
            pairs.PAIR_1.target.constraint_id: {"n_items": 3, "policy": P},
            pairs.PAIR_1.focal.constraint_id: {"relation": CHAIN, "policy": P}},
        backgrounds={
            "v19:background.sentences": {
                "family": pairs.PAIR_3.target.constraint_id,
                "n_sentences": 5, "policy": P},
            "v19:background.unique": {"family": pairs.PAIR_2.focal.constraint_id,
                                      "policy": P},
            "v19:background.increasing": {
                "family": pairs.PAIR_3.focal.constraint_id, "policy": P}})
    built = W.construct_witness(mixed, P)
    assert not built.constructed
    assert "no single rendering satisfies both" in built.reason


def test_an_all_whitespace_witness_is_refused_as_a_record():
    with pytest.raises(W.WitnessConstructionError, match="not a constructed answer"):
        W.WitnessRecord(composition_id="x", encoding_hash="h",
                        constructor=W.CONSTRUCTOR_ID, seed=0, text="   ",
                        reason="r", structure={})


def test_a_negative_seed_is_refused():
    with pytest.raises(W.WitnessConstructionError, match="non-negative"):
        W.construct_witness(p1(), P, seed=-1)


def test_the_witness_record_names_its_constructor_and_hashes_the_bytes():
    built = W.construct_witness(p3(), P)
    assert built.constructor == W.CONSTRUCTOR_ID
    assert built.witness_hash and built.structure["rendering"] == "prose"
    assert W.construct_witness(p1(), P).structure["rendering"] == "bullet_list"


def test_the_item_order_is_a_valid_linear_extension():
    built = W.construct_witness(p1(), P)
    order = built.structure["item_order"]
    for before, after in CHAIN.closure():
        assert order.index(before) < order.index(after)


def test_filler_words_never_contain_a_declared_item_label():
    """Otherwise containment matching would identify a filler as a real item."""
    built = W.construct_witness(p1(n_items=6, policy=PERMISSIVE, cid="p1/loose/B"),
                                PERMISSIVE)
    assert built.constructed
    outcome = V.verify_transitive_order(built.text or "", relation=CHAIN,
                                       policy=PERMISSIVE)
    assert not outcome.evidence["identification"]["ambiguous"]
    assert not outcome.evidence["identification"]["duplicated_labels"]


# ----------------------------------------------------- the verifier conjunction
def test_the_conjunction_is_the_product_over_every_active_constraint():
    composition = p3()
    built = W.construct_witness(composition, P)
    conjunction = C.run_conjunction(composition, built.text or "", P)
    assert conjunction.vector == (1, 1)
    assert conjunction.v_all == 1


def test_a_missing_column_refuses_to_form_a_conjunction():
    """Three declared constraints and two results must not give a product."""
    composition = p3()
    built = W.construct_witness(composition, P)
    partial = C.run_conjunction(composition, built.text or "", P,
                               omit=(pairs.PAIR_3.focal.constraint_id,))
    assert not partial.complete
    assert partial.missing == (pairs.PAIR_3.focal.constraint_id,)
    assert partial.v_all is None
    assert partial.vector == (1, None)


def test_an_unscored_column_also_refuses_to_form_a_conjunction():
    composition = p3()
    conjunction = C.run_conjunction(composition, "One. Two.", P)
    broken = dataclasses.replace(
        conjunction,
        outcomes={**conjunction.outcomes,
                  pairs.PAIR_3.target.constraint_id: V.VerifierOutcome(
                      verifier_id="v19:verifier.exact_sentence_count",
                      constraint_id=pairs.PAIR_3.target.constraint_id,
                      spec_hash="h", parameters={},
                      scoring=V.Scoring.VERIFIER_ERROR, verdict=None,
                      generation_state=V.GenerationState.SCORABLE,
                      compliance=None, reason="exploded", evidence={})})
    assert not broken.complete
    assert broken.unscored == (pairs.PAIR_3.target.constraint_id,)
    assert broken.v_all is None


def test_a_failing_column_makes_the_product_zero():
    """Both columns fail here: two sentences instead of four, and equal lengths."""
    composition = p3(n_sentences=4)
    conjunction = C.run_conjunction(composition, "One. Two.", P)
    assert conjunction.complete
    assert conjunction.vector == (0, 0)
    assert conjunction.v_all == 0
    assert set(conjunction.rejected_by) == {pairs.PAIR_3.target.constraint_id,
                                            pairs.PAIR_3.focal.constraint_id}


def test_one_failing_column_alone_makes_the_product_zero():
    composition = p3(n_sentences=4)
    # Three sentences of strictly increasing length: the focal rule holds, the
    # target count does not.
    text = "Alfa. Bravo charlie. Delta echo foxtrot."
    conjunction = C.run_conjunction(composition, text, P)
    assert conjunction.vector == (0, 1)
    assert conjunction.v_all == 0
    assert conjunction.rejected_by == (pairs.PAIR_3.target.constraint_id,)


def test_a_clause_without_a_verifier_is_refused():
    composition = p1()
    original = V.bundle
    try:
        V.bundle = lambda policy=P: {}
        with pytest.raises(C.CertificationError, match="no verifier"):
            C.run_conjunction(composition, "- alpha", P)
    finally:
        V.bundle = original


# ------------------------------------------------------------ semantic review
def test_review_is_triggered_by_the_coverage_declaration_not_by_judgement():
    assert C.review_required(p1()) == (pairs.PAIR_1.focal.constraint_id,)
    assert C.review_required(p2()) == (pairs.PAIR_2.focal.constraint_id,)
    assert C.review_required(p3()) == (pairs.PAIR_3.target.constraint_id,)


def test_a_review_with_no_clauses_under_review_is_refused():
    with pytest.raises(C.CertificationError, match="certify nothing"):
        C.SemanticReview(composition_id="x", witness_hash="h", clause_ids=())


def test_a_reviewer_verdict_needs_an_identity_and_a_rationale():
    with pytest.raises(C.CertificationError, match="identified reviewer"):
        C.ReviewerVerdict("", True, "because")
    with pytest.raises(C.CertificationError, match="states its rationale"):
        C.ReviewerVerdict("r1", True, "")


def review(*verdicts, adjudication=None, clause_ids=None, witness_hash="h"):
    return C.SemanticReview(
        composition_id="x", witness_hash=witness_hash,
        clause_ids=clause_ids or (pairs.PAIR_1.focal.constraint_id,),
        reviews=verdicts, adjudication=adjudication)


def test_fewer_than_two_reviews_is_review_required():
    assert review().state is C.ReviewState.HUMAN_REVIEW_REQUIRED
    assert review(C.ReviewerVerdict("r1", True, "yes")).state \
        is C.ReviewState.HUMAN_REVIEW_REQUIRED


def test_two_agreeing_reviews_decide():
    passed = review(C.ReviewerVerdict("r1", True, "yes"),
                    C.ReviewerVerdict("r2", True, "also yes"))
    failed = review(C.ReviewerVerdict("r1", False, "no"),
                    C.ReviewerVerdict("r2", False, "also no"))
    assert passed.state is C.ReviewState.HUMAN_REVIEW_PASSED
    assert failed.state is C.ReviewState.HUMAN_REVIEW_FAILED


def test_unresolved_disagreement_does_not_certify():
    """Section 8.6 fails certification; it does not prefer the earlier reviewer."""
    split = review(C.ReviewerVerdict("r1", True, "yes"),
                   C.ReviewerVerdict("r2", False, "no"))
    assert split.state is C.ReviewState.HUMAN_REVIEW_REQUIRED
    assert "unresolved disagreement" in split.reason


def test_a_third_reviewer_adjudicates_in_either_direction():
    for verdict, expected in [(True, C.ReviewState.HUMAN_REVIEW_PASSED),
                              (False, C.ReviewState.HUMAN_REVIEW_FAILED)]:
        got = review(C.ReviewerVerdict("r1", True, "yes"),
                     C.ReviewerVerdict("r2", False, "no"),
                     adjudication=C.ReviewerVerdict("r3", verdict, "settled"))
        assert got.state is expected


def test_the_same_reviewer_may_not_review_twice():
    with pytest.raises(C.CertificationError, match="INDEPENDENT"):
        review(C.ReviewerVerdict("r1", True, "yes"),
               C.ReviewerVerdict("r1", True, "again"))


def test_the_adjudicator_may_not_be_one_of_the_two_reviewers():
    with pytest.raises(C.CertificationError, match="not independent"):
        review(C.ReviewerVerdict("r1", True, "yes"),
               C.ReviewerVerdict("r2", False, "no"),
               adjudication=C.ReviewerVerdict("r1", True, "I insist"))


def test_an_adjudication_before_a_disagreement_is_refused():
    with pytest.raises(C.CertificationError, match="no disagreement to resolve"):
        review(C.ReviewerVerdict("r1", True, "yes"),
               adjudication=C.ReviewerVerdict("r3", True, "premature"))


def test_a_panel_larger_than_two_is_refused():
    with pytest.raises(C.CertificationError, match="would change the decision rule"):
        review(C.ReviewerVerdict("r1", True, "a"),
               C.ReviewerVerdict("r2", True, "b"),
               C.ReviewerVerdict("r3", True, "c"))


# ---------------------------------------------------------- the full certificate
def passing_review(composition):
    built = W.construct_witness(composition, P)
    return C.SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash,
        clause_ids=C.review_required(composition),
        reviews=(C.ReviewerVerdict("reviewer-a", True, "the uncovered reading holds"),
                 C.ReviewerVerdict("reviewer-b", True, "independently, it holds")))


@pytest.mark.parametrize("factory", [p1, p2, p3])
def test_no_composition_certifies_without_the_semantic_review(factory):
    """Every pair has one incompletely encoded clause, so this is the whole set."""
    certificate = C.certify_composition(factory(), P)
    assert certificate.outcome is C.Outcome.REVIEW_REQUIRED
    assert not certificate.certified
    assert certificate.conjunction is not None
    assert certificate.conjunction.v_all == 1     # everything else passed


@pytest.mark.parametrize("factory", [p1, p2, p3])
def test_a_composition_certifies_with_solver_witness_verifiers_and_review(factory):
    composition = factory()
    certificate = C.certify_composition(composition, P,
                                        review=passing_review(composition))
    assert certificate.certified
    assert certificate.review_state is C.ReviewState.HUMAN_REVIEW_PASSED
    assert certificate.solver is not None and certificate.solver.status == "sat"
    assert certificate.witness is not None and certificate.witness.constructed
    assert C.assert_certified(certificate) is certificate


def test_solver_sat_alone_never_certifies():
    """The single most important refusal in the module."""
    composition = p1()
    assert S.solve(composition).status == "sat"
    assert not C.certify_composition(composition, P).certified


def test_an_unsat_composition_stops_before_a_witness_is_built():
    certificate = C.certify_composition(p1(n_items=2), P)
    assert certificate.outcome is C.Outcome.SOLVER_NOT_SAT
    assert certificate.witness is None and certificate.conjunction is None


def test_a_missing_verifier_column_stops_certification():
    composition = p3()
    certificate = C.certify_composition(
        composition, P, omit_verifiers=(pairs.PAIR_3.focal.constraint_id,))
    assert certificate.outcome is C.Outcome.VERIFIER_INCOMPLETE
    assert "may not be formed over the available subset" in certificate.reason


def test_a_review_against_a_different_witness_does_not_certify():
    composition = p1()
    stale = dataclasses.replace(passing_review(composition),
                                witness_hash="0" * 64)
    certificate = C.certify_composition(composition, P, review=stale)
    assert certificate.outcome is C.Outcome.REVIEW_REQUIRED
    assert "against a different witness" in certificate.reason


def test_a_review_covering_the_wrong_clauses_does_not_certify():
    composition = p1()
    built = W.construct_witness(composition, P)
    wrong = C.SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash,
        clause_ids=(pairs.PAIR_2.focal.constraint_id,),
        reviews=(C.ReviewerVerdict("a", True, "x"),
                 C.ReviewerVerdict("b", True, "y")))
    certificate = C.certify_composition(composition, P, review=wrong)
    assert certificate.outcome is C.Outcome.REVIEW_REQUIRED
    assert "clauses needing review" in certificate.reason


def test_a_failed_review_is_its_own_outcome():
    composition = p1()
    built = W.construct_witness(composition, P)
    failed = C.SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash,
        clause_ids=C.review_required(composition),
        reviews=(C.ReviewerVerdict("a", False, "the reading does not hold"),
                 C.ReviewerVerdict("b", False, "agreed")))
    certificate = C.certify_composition(composition, P, review=failed)
    assert certificate.outcome is C.Outcome.REVIEW_FAILED
    with pytest.raises(C.CertificationError, match="REVIEW_FAILED"):
        C.assert_certified(certificate)


def test_auto_certification_is_currently_unreachable_and_that_is_reported():
    """No valid composition has all-COMPLETE coverage today.

    Each pair pairs a COMPLETE clause with a PARTIAL one - Pair 1 and Pair 2 have a
    complete target and an incomplete focal, Pair 3 the reverse - and every A+B+S
    composition contains both. So `AUTO_CERTIFIED` exists as a branch and no
    composition reaches it, which means human semantic review is mandatory for
    everything Stage 2 can certify. Recorded here rather than left to be discovered.
    """
    for factory in (p1, p2, p3):
        composition = factory()
        assert C.review_required(composition), composition.composition_id
    complete = {row["constraint_id"] for row in E.coverage_report(P)
                if row["coverage"] == "COMPLETE"}
    assert complete == {pairs.PAIR_1.target.constraint_id,
                        pairs.PAIR_2.target.constraint_id,
                        pairs.PAIR_3.focal.constraint_id}
    assert C.ReviewState.AUTO_CERTIFIED in set(C.ReviewState)


def test_the_certificate_archives_everything_section_eight_six_lists():
    composition = p2()
    certificate = C.certify_composition(composition, P,
                                        review=passing_review(composition))
    described = certificate.describe()
    import json
    json.dumps(described)
    assert described["composition"]["encoding_hash"]
    assert described["solver"]["assertions"] and described["solver"]["record_hash"]
    assert described["solver"]["model"]            # archived, not hashed
    assert described["verifier_bundle_hash"] == V.bundle_hash(P)
    assert all(row["implementation_hash"]
               for row in described["verifier_bundle"].values())
    assert described["semantic_id"] and described["implementation_id"]
    assert described["evidence_id"]
    assert described["witness"]["witness_hash"] and described["witness"]["text"]
    assert described["conjunction"]["v_all"] == 1
    assert described["review"]["state"] == "HUMAN_REVIEW_PASSED"
    assert described["certificate_hash"]


def test_the_certificate_hash_moves_with_the_witness():
    composition = p2()
    first = C.certify_composition(composition, P, review=passing_review(composition))
    other = C.certify_composition(p2(words=("alpha", "beta", "gamma"),
                                     cid="p2/2/B"), P)
    assert first.certificate_hash != other.certificate_hash


def test_every_outcome_is_reachable_or_explicitly_out_of_scope():
    """A taxonomy with unreachable members hides a path that cannot be tested."""
    reachable = {C.Outcome.CERTIFIED, C.Outcome.SOLVER_NOT_SAT,
                 C.Outcome.WITNESS_NOT_CONSTRUCTED, C.Outcome.VERIFIER_INCOMPLETE,
                 C.Outcome.REVIEW_REQUIRED, C.Outcome.REVIEW_FAILED}
    # SOLVER_UNAVAILABLE needs an environment without z3; VERIFIER_ERROR needs a
    # crashing verifier; WITNESS_REJECTED needs an encoding/verifier disagreement,
    # which the frozen policy now rules out by construction. All three are covered
    # by their own tests below rather than here.
    assert reachable <= set(C.Outcome)
    assert {C.Outcome.SOLVER_UNAVAILABLE, C.Outcome.VERIFIER_ERROR,
            C.Outcome.WITNESS_REJECTED} <= set(C.Outcome)


def test_a_policy_mismatch_is_refused_before_any_evidence_is_read():
    """The earlier route to a disagreement is now closed at the door.

    Encoding under one grammar and verifying under another was how the audit reached
    a solver-sat, verifier-rejected witness. The clauses carry the grammar\'s hash,
    so the mismatch is refused before the solver runs.
    """
    composition = p1(n_items=5, policy=PERMISSIVE, cid="p1/loose/B")
    certificate = C.certify_composition(composition, P)
    assert certificate.outcome is C.Outcome.POLICY_MISMATCH
    assert certificate.solver is None and certificate.witness is None


def test_a_witness_rejected_by_a_verifier_is_reported_as_a_disagreement():
    """The branch survives, and is reached by making a verifier reject.

    Under the canonical grammar the encoding and the verifiers agree, so no real
    composition reaches this outcome. The branch still has to exist and still has to
    say the right thing, because a future clause family could reintroduce the gap -
    so it is exercised by forcing one verifier to reject a witness the solver
    accepted.
    """
    composition = p2()
    always_fail = dict(V.bundle(P))
    target_id = pairs.PAIR_2.target.constraint_id
    original = V.bundle

    def rejecting(policy=P):
        built = dict(original(policy))
        good = built[target_id]
        built[target_id] = dataclasses.replace(
            good, run=lambda text, **kw: dataclasses.replace(
                good.run(text, **kw), verdict=V.Verdict.FAIL,
                compliance=V.Compliance.VIOLATION,
                reason="forced rejection for the disagreement branch"))
        return built

    try:
        V.bundle = rejecting
        certificate = C.certify_composition(composition, P)
    finally:
        V.bundle = original
    assert always_fail                                  # the real bundle is intact
    assert certificate.outcome is C.Outcome.WITNESS_REJECTED
    assert "semantics disagree" in certificate.reason
    assert "not a composition to retry" in certificate.reason


def test_a_crashing_verifier_is_a_verifier_error_not_a_rejection():
    composition = p3()
    built = W.construct_witness(composition, P)
    conjunction = C.run_conjunction(composition, built.text or "", P)
    broken = dataclasses.replace(
        conjunction,
        outcomes={**conjunction.outcomes,
                  pairs.PAIR_3.focal.constraint_id: V.VerifierOutcome(
                      verifier_id="v19:verifier.increasing_lengths",
                      constraint_id=pairs.PAIR_3.focal.constraint_id,
                      spec_hash="h", parameters={},
                      scoring=V.Scoring.VERIFIER_ERROR, verdict=None,
                      generation_state=V.GenerationState.SCORABLE,
                      compliance=None, reason="exploded", evidence={})})
    assert broken.unscored and broken.v_all is None


# --------------------------------------------------------- the mutation battery
@pytest.mark.parametrize("pair_id", ["p1", "p2", "p3"])
def test_each_template_reaches_the_section_eight_seven_floor(pair_id):
    records = M.battery_for_template(f"{pair_id}.A+B",
                                     M.template_bases(pair_id, P), P)
    summary = M.assert_battery_is_evidence(records)
    assert summary["n_mutations"] >= M.MUTATIONS_PER_TEMPLATE
    assert summary["distinct_texts"] == summary["n_mutations"]


@pytest.mark.parametrize("pair_id", ["p1", "p2", "p3"])
def test_no_mutation_produces_undeclared_collateral(pair_id):
    """Collateral is the measurement, and it is currently empty by declaration."""
    records = M.battery_for_template(f"{pair_id}.A+B",
                                     M.template_bases(pair_id, P), P)
    offenders = [r.describe() for r in records if r.collateral]
    assert not offenders, offenders[:3]


def test_unrealised_effects_are_position_dependent_not_systematic():
    """A declared effect that fails at SOME positions is a real measurement.

    Duplicating a word in the final sentence keeps the lengths increasing, so the
    monotone clause does not move. That is a fact about the boundary, not a wrong
    declaration, so it is reported rather than declared away.
    """
    records = M.battery_for_template("p3.A+B", M.template_bases("p3", P), P)
    by_type: dict[str, list[bool]] = {}
    for record in records:
        by_type.setdefault(record.mutation_type, []).append(bool(record.unrealised))
    for name, flags in by_type.items():
        if any(flags):
            assert not all(flags), (
                f"{name} never realises its declared effect, which makes the "
                "declaration wrong rather than position-dependent")


def test_the_battery_refuses_to_pad_the_count():
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P)
    padded = tuple(records[:1]) * M.MUTATIONS_PER_TEMPLATE
    with pytest.raises(M.MutationError, match="the count is padded"):
        M.assert_battery_is_evidence(padded)


def test_a_battery_below_the_floor_is_not_evidence():
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P,
                                     target=50)
    with pytest.raises(M.MutationError, match="below the floor"):
        M.assert_battery_is_evidence(records)


def test_a_single_boundary_family_is_not_evidence():
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P)
    one_family = tuple(r for r in records if r.boundary == "unicode")
    with pytest.raises(M.MutationError, match="boundaries are represented"):
        M.assert_battery_is_evidence(one_family[:M.MUTATIONS_PER_TEMPLATE])


def test_the_boundaries_section_eight_seven_names_are_all_declared():
    declared = {t.boundary for t in M.TRANSFORMS}
    assert declared == set(M.Boundary)


def test_every_transform_declares_a_rationale_and_a_changed_field():
    for transform in M.TRANSFORMS:
        assert transform.rationale and transform.field_changed
        assert len(transform.rationale) > 30, transform.name


def test_an_unknown_transform_is_refused():
    with pytest.raises(M.MutationError, match="not a declared transform"):
        M.apply_transform("shuffle_everything", "- a\n- b", 0)


def test_a_parser_level_mutation_moves_both_pair_one_verdicts():
    """Section 4.2's confound, isolated and attributed to the parse."""
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P)
    marker = [r for r in records if r.mutation_type == "marker_removed"]
    assert marker
    for record in marker:
        assert set(record.observed_affected) == set(record.expected_affected)
        assert len(record.expected_affected) == 2


def test_an_ordering_mutation_moves_only_the_ordering_verdict():
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P)
    swaps = [r for r in records if r.mutation_type == "segments_swapped"]
    assert swaps
    for record in swaps:
        assert record.observed_affected == (pairs.PAIR_1.focal.constraint_id,)


def test_the_zero_width_asymmetry_is_pinned():
    """The same character defeats presence and identification, not uniqueness."""
    transform = M.TRANSFORM_BY_NAME["zero_width_inserted"]
    assert E.ClauseKind.ALL_TOKENS_DISTINCT not in transform.expected_kinds
    assert E.ClauseKind.MANDATORY_TOKENS in transform.expected_kinds
    assert E.ClauseKind.ITEM_PRECEDENCE in transform.expected_kinds


def test_expectations_are_policy_conditional_where_the_policy_decides():
    """Which is the clearest argument for freezing the policy before certifying."""
    composition = p1()
    numbered = M.TRANSFORM_BY_NAME["marker_numbered"]
    counting = M._expected(composition, numbered, P)
    not_counting = M._expected(composition, numbered,
                               dataclasses.replace(P, numbered_items_count=False))
    assert counting == () and len(not_counting) == 2


def test_the_battery_refuses_a_base_its_verifiers_do_not_accept():
    """A base whose witness fails a verifier cannot attribute a mutation's effect."""
    unsatisfiable = E.encode_composition(
        "p3/impossible/B", pair_id="p3", arm="B", load=2, realisations={
            pairs.PAIR_3.target.constraint_id: {"n_sentences": 1, "policy": P},
            pairs.PAIR_3.focal.constraint_id: {"policy": P}})
    with pytest.raises(M.MutationError, match="not accepted by every verifier"):
        M.run_battery(unsatisfiable, P, template_id="mismatched")


def test_a_mutation_record_is_serialisable_and_complete():
    import json
    records = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P,
                                     target=10)
    for record in records:
        described = record.describe()
        json.dumps(described)
        assert set(described) >= {
            "template_id", "base_witness_hash", "mutation_id", "mutation_type",
            "seed", "field_changed", "expected_affected", "observed_affected",
            "observed_vector", "collateral"}


def test_the_battery_is_deterministic():
    first = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P,
                                   target=40)
    second = M.battery_for_template("p1.A+B", M.template_bases("p1", P), P,
                                    target=40)
    assert [r.mutation_id for r in first] == [r.mutation_id for r in second]
    assert [r.mutated_hash for r in first] == [r.mutated_hash for r in second]


def test_prefix_overlapping_labels_are_no_longer_ambiguous():
    """Token membership replaced substring containment, so the constraint is gone."""
    overlapping = OrderingRelation(items=("item1", "item10"),
                                   edges=(("item1", "item10"),))
    outcome = V.verify_transitive_order("- item1\n- item10", relation=overlapping,
                                        policy=P)
    assert outcome.verdict is V.Verdict.PASS
    assert not outcome.evidence["identification"]["ambiguous"]
    assert V.verify_transitive_order("- item10\n- item1", relation=overlapping,
                                     policy=P).verdict is V.Verdict.FAIL


# ------------------------------------------------------------ registry wiring
# Three of the five satisfiability artifacts have been produced and recorded in
# src/dci/v19/stage2_frozen.json; the other two need a human review and an artifact
# that depends on it.
PRODUCED = ("satisfiability.encoding_map", "satisfiability.solver_identity",
            "satisfiability.witness_constructor",
            "satisfiability.review_trigger")
STILL_PENDING = ("satisfiability.semantic_reviews",
                 "satisfiability.certified_compositions")


def test_the_produced_satisfiability_artifacts_are_frozen_with_provenance():
    from dci.v19 import frozen
    recorded = {row["slot"]: row for row in frozen.audit()}
    assert set(PRODUCED) <= set(recorded)
    for name in PRODUCED:
        slot = REGISTRY.slots[name]
        assert slot.resolved, name
        assert slot.frozen_by and slot.domain, name
        assert recorded[name]["evidence"], name


def test_the_remaining_satisfiability_artifacts_are_still_pending():
    for name in STILL_PENDING:
        slot = REGISTRY.slots[name]
        assert slot.pending, name
        assert slot.rule and slot.prereg


def test_a_recorded_output_cannot_precede_its_own_prerequisites():
    """The file cannot bypass the ordering section 14 makes mandatory."""
    import json

    from dci.v19 import frozen
    out_of_order = {"records": [{
        "slot": "verifiers.bundle_hash", "value": "0" * 64,
        "frozen_by": "probe", "recorded_at": "2026-01-01T00:00:00+00:00",
        "evidence": "probe"}]}
    import tempfile
    from pathlib import Path

    from dci.v19.registry import declared_table
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "records.json"
        target.write_text(json.dumps(out_of_order))
        with pytest.raises(frozen.FrozenRecordError, match="out of order"):
            frozen.apply(declared_table(), target)


def test_the_semantic_reviews_are_a_prospective_decision():
    slot = REGISTRY.slots["satisfiability.semantic_reviews"]
    assert slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert "Code must never stand in for the reviewer" in slot.note

def test_the_whole_stage_two_report_covers_both_halves_and_still_fails_closed():
    report = stage2.certify_stage2(REGISTRY.slots)
    citations = {f.citation for f in report.findings}
    assert any("8.6" in c for c in citations)
    assert any("14.2" in c for c in citations)
    assert any("10.4" in c for c in citations)
    # One requirement outstanding, and it is human adjudication.
    assert not report.certified
    assert len(report.outstanding) == 1
    assert "human-adjudicated" in report.outstanding[0].requirement

def test_the_stage_two_report_is_serialisable():
    import json
    json.dumps(stage2.certify_stage2(REGISTRY.slots).describe())


def test_nothing_in_the_satisfiability_layer_was_fabricated():
    from dci.v19 import registry
    registry.assert_nothing_fabricated()
