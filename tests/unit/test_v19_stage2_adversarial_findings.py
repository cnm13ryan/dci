"""S1-S13: the adversarial findings, now as regression tests for their repairs.

Each of these was a reproducer that pinned broken behaviour. Each now asserts the
repair and states what the old behaviour was, so a regression fails here with the
history attached instead of waiting to be rediscovered by another audit.

  composition integrity   S1  pair_id is checked against its clauses
                          S2  a composition with no target is refused
                          S3  load is exactly the number of active constraints
                          S4  an empty Conjunction is refused
  cross-layer semantics   S5  one text policy: one normalisation, one case rule,
                              one tokenisation, one label rule
                          S6  the unsound axiom is gone AND its root cause fixed
                          S7  the constructor cannot collide a mandatory word with
                              an item label
  fail-closed             S8  a missing solver produces SOLVER_UNAVAILABLE
  provenance              S9  the certificate hash is reproducible
                          S10 the certificate carries implementation and bundle
                              hashes
  registry validation     S11 slots are validated, not merely populated
                          S12 the mutation battery is regenerated, not asserted
  review integrity        S13 review verdicts must be booleans

Three findings were repaired by DECIDING rather than only by coding, and the tests
say which amendment decided them: the case rule and the segmentation come from
Stage 2 amendment A2, the Pair 1 label rule and the undeclared-item reading from A1.
`docs/v19_stage2_specification_amendments.md` is the record; this file is the
enforcement. The last section is the complement - what the amendments deliberately
did NOT change.
"""
import builtins
import dataclasses
import subprocess
import sys

import pytest
import v19_domain_values as stand_in

from dci.v19 import certification as C
from dci.v19 import encoding as E
from dci.v19 import mutation as M
from dci.v19 import pairs, stage2
from dci.v19 import reliability as R
from dci.v19 import solver as S
from dci.v19 import text as textlib
from dci.v19 import verifiers as V
from dci.v19 import witness as W
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation, parse_list, sentences
from dci.v19.registry import REGISTRY, declared_table
from dci.verifiers import rules

pytestmark = pytest.mark.cpu

TP = P.text
REL2 = OrderingRelation(items=("alfa", "bravo"), edges=(("alfa", "bravo"),))
ZERO_WIDTH = "\u200b"
CYRILLIC_A = "а"


def clause(constraint_id, **realisation):
    return E.encode_clause(constraint_id, {**realisation, "policy": P})


def background(family, background_id, **realisation):
    return E.encode_background(family, {**realisation, "policy": P},
                               background_id=background_id)


def p1_composition(n_items=2, cid="p1/1/B"):
    return E.encode_composition(cid, pair_id="p1", arm="B", load=2, realisations={
        pairs.PAIR_1.target.constraint_id: {"n_items": n_items, "policy": P},
        pairs.PAIR_1.focal.constraint_id: {"relation": REL2, "policy": P}})


def p2_composition(words=("alpha",), cid="p2/1/B"):
    return E.encode_composition(cid, pair_id="p2", arm="B", load=2, realisations={
        pairs.PAIR_2.target.constraint_id: {"mandatory_words": words, "policy": P},
        pairs.PAIR_2.focal.constraint_id: {"policy": P}})


def p1_with_backgrounds(cid, backgrounds, n_items=2):
    return E.encode_composition(
        cid, pair_id="p1", arm="B", load=5, realisations={
            pairs.PAIR_1.target.constraint_id: {"n_items": n_items, "policy": P},
            pairs.PAIR_1.focal.constraint_id: {"relation": REL2, "policy": P}},
        backgrounds=backgrounds)


def passing_review(composition):
    built = W.construct_witness(composition, P)
    return C.SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash,
        clause_ids=C.review_required(composition),
        reviews=(C.ReviewerVerdict("reviewer-a", True, "holds"),
                 C.ReviewerVerdict("reviewer-b", True, "independently holds")))


# ------------------------------------------------- S1..S4 composition integrity
def test_s1_a_composition_declared_for_one_pair_cannot_be_built_from_another():
    """Was: accepted, and certified. `pair_id` was never compared to the clauses."""
    with pytest.raises(E.EncodingError, match="not the pair's composition"):
        E.Composition(
            composition_id="mislabelled", pair_id="p1", arm="B", load=2,
            clauses=(clause(pairs.PAIR_2.target.constraint_id,
                            mandatory_words=("alpha",)),
                     clause(pairs.PAIR_2.focal.constraint_id)))


def test_s2_a_composition_with_no_target_constraint_is_refused():
    """Was: fully CERTIFIED.

    Section 8.6 certifies A+B+S and A+R_j+S arms, and every one of them contains the
    pair's own target - it is the primary outcome's constraint.
    """
    with pytest.raises(E.EncodingError, match="exactly one target"):
        E.Composition(composition_id="focal-only", pair_id="p2", arm="B", load=2,
                      clauses=(clause(pairs.PAIR_2.focal.constraint_id),))


def test_s2b_a_composition_with_two_targets_is_refused():
    with pytest.raises(E.EncodingError, match="target clause"):
        E.Composition(
            composition_id="two-targets", pair_id="p1", arm="B", load=2,
            clauses=(clause(pairs.PAIR_1.target.constraint_id, n_items=2),
                     clause(pairs.PAIR_2.target.constraint_id,
                            mandatory_words=("alpha",))))


def test_s2c_the_added_slot_holds_exactly_one_occupant():
    """The replacement contrast is a replacement, not an addition (section 2.1)."""
    with pytest.raises(E.EncodingError, match="added-slot occupant"):
        E.Composition(
            composition_id="no-occupant", pair_id="p1", arm="B", load=2,
            clauses=(clause(pairs.PAIR_1.target.constraint_id, n_items=2),
                     background(pairs.PAIR_2.focal.constraint_id,
                                "v19:background.x")))


def test_s2d_a_reference_arm_needs_an_admitted_reference():
    from dci.v19.resolution import UnresolvedDependency
    with pytest.raises(UnresolvedDependency, match=r"reference\.p1\.R1"):
        E.encode_reference("p1", "R1")
    with pytest.raises(E.EncodingError, match="replacement, not an addition"):
        E.Composition(
            composition_id="focal-in-reference-arm", pair_id="p1", arm="R1", load=2,
            clauses=(clause(pairs.PAIR_1.target.constraint_id, n_items=2),
                     clause(pairs.PAIR_1.focal.constraint_id, relation=REL2)))


@pytest.mark.parametrize("load,n_clauses", [(2, 1), (2, 3), (5, 2), (5, 3), (5, 6)])
def test_s3_load_is_exactly_the_number_of_active_constraints(load, n_clauses):
    """Was: load 5 accepted 1, 2, 3 or 5 clauses; only load 2 was bounded at all."""
    available = (clause(pairs.PAIR_1.target.constraint_id, n_items=2),
                 clause(pairs.PAIR_1.focal.constraint_id, relation=REL2)) + tuple(
        background(pairs.PAIR_2.focal.constraint_id, f"v19:background.s{i}")
        for i in range(4))
    with pytest.raises(E.EncodingError,
                       match="admits exactly|active constraint|added-slot occupant"):
        E.Composition(composition_id="wrong-load", pair_id="p1", arm="B", load=load,
                      clauses=available[:n_clauses])


def test_s3b_the_two_legal_shapes_are_accepted():
    assert len(p1_composition().clauses) == 2
    full = p1_with_backgrounds("p1/1/B5", {
        f"v19:background.s{i}": {"family": pairs.PAIR_2.focal.constraint_id,
                                 "policy": P} for i in range(3)})
    assert len(full.clauses) == 5 and full.roles.count("background") == 3


def test_s4_an_empty_conjunction_is_refused():
    """Was: `complete` True and `v_all` 1 - the empty product."""
    with pytest.raises(C.CertificationError, match="vacuously satisfied"):
        C.Conjunction(composition_id="x", witness_hash="h", required=(), outcomes={})


def test_s4b_a_conjunction_whose_outcomes_are_not_its_requirements_is_refused():
    with pytest.raises(C.CertificationError, match="not among the required"):
        C.Conjunction(composition_id="x", witness_hash="h", required=("a",),
                      outcomes={"b": None})
    with pytest.raises(C.CertificationError, match="repeats a constraint"):
        C.Conjunction(composition_id="x", witness_hash="h", required=("a", "a"),
                      outcomes={})


# ------------------------------------------------- S5..S7 cross-layer semantics
def test_s5_there_is_one_case_rule_and_every_layer_uses_it():
    """Was: the encoding folded with casefold, the verifiers compared with lower.

    The clause for the mandatory set ("ss", "SS") therefore required one distinct
    token where the verifier looked for two.
    """
    assert TP.case_rule == "casefold"
    encoded = E.encode_clause(pairs.PAIR_2.target.constraint_id,
                              {"mandatory_words": ("ß", "SS"), "policy": P})
    assert encoded.parameters["folded"] == ["ss", "ss"]
    assert encoded.parameters["distinct_required"] == 1
    assert V.verify_mandatory_words("ss", mandatory_words=("ß", "SS"),
                                    text_policy=TP).verdict is V.Verdict.PASS


def test_s5b_label_matching_and_token_matching_use_the_same_rule():
    from dci.v19.parsing import match_items_to_labels
    relation = OrderingRelation(items=("strasse", "other"),
                                edges=(("strasse", "other"),))
    identified = match_items_to_labels(parse_list("- STRAßE\n- other", P),
                                       relation, P)
    assert identified["sequence"] == ["strasse", "other"]
    assert textlib.folded_tokens("STRAßE", TP) == ["strasse"]
    assert identified["text_policy"] == TP.policy_id


def test_s5c_every_clause_records_the_policies_its_verifier_reads():
    """A cross-layer disagreement is now visible in a hash rather than in behaviour."""
    for encoded in p1_composition().clauses:
        assert encoded.parameters["list_policy_hash"] == P.policy_hash
    for encoded in p2_composition().clauses:
        assert encoded.parameters["text_policy_hash"] == TP.policy_hash


@pytest.mark.parametrize("text", ["- ЖЖЖ\n- ЩЩЩ",
                                  "- 日本語\n- 中文"])
def test_s6_a_non_ascii_item_is_a_sentence_so_the_axiom_premise_is_gone(text):
    """Was: 2 items and 0 sentences, which made n_sentences >= n_items unsound."""
    assert parse_list(text, P).count == 2
    assert len(sentences(text, P)) == 2
    assert rules.split_sentences(text) == []       # the inherited rule still says 0


def test_s6b_the_axiom_is_not_asserted_at_all():
    """Removed as well as repaired: the abstraction stays a conservative relaxation.

    Section 8.5 rejects the whole proposal on unsat, so a spurious unsat narrows the
    estimand's population, while a spurious sat is caught by the concrete
    all-verifier witness section 8.6 ranks above the solver.
    """
    import inspect
    source = inspect.getsource(S._conjunction)
    assert "NO AXIOM RELATING n_sentences TO n_items" in source
    mixed = p1_with_backgrounds("mixed", {
        "v19:background.sentences": {"family": pairs.PAIR_3.target.constraint_id,
                                     "n_sentences": 1, "policy": P},
        "v19:background.unique": {"family": pairs.PAIR_2.focal.constraint_id,
                                  "policy": P},
        "v19:background.increasing": {"family": pairs.PAIR_3.focal.constraint_id,
                                      "policy": P}})
    assert S.solve(mixed).status == "sat"          # was unsat


def test_s7_a_mandatory_word_cannot_collide_with_an_item_label():
    """Was: solver sat, witness built, ordering verifier rejected it.

    Two repairs meet here. Token equality means "alfaX" is not the label "alfa", and
    the constructor reserves labels and mandatory words by folded token.
    """
    composition = p1_with_backgrounds("collide", {
        "v19:background.words": {"family": pairs.PAIR_2.target.constraint_id,
                                 "mandatory_words": ("alfaX",), "policy": P},
        "v19:background.unique": {"family": pairs.PAIR_2.focal.constraint_id,
                                  "policy": P},
        "v19:background.more": {"family": pairs.PAIR_2.target.constraint_id,
                                "mandatory_words": ("zulu",), "policy": P}})
    assert S.solve(composition).status == "sat"
    certificate = C.certify_composition(composition, P,
                                        review=passing_review(composition))
    assert certificate.outcome is not C.Outcome.WITNESS_REJECTED
    assert certificate.conjunction.v_all == 1


def test_s7b_a_mandatory_word_that_is_a_label_is_placed_once():
    """Placing it twice would put the label in two items and make both ambiguous."""
    composition = p1_with_backgrounds("same", {
        "v19:background.words": {"family": pairs.PAIR_2.target.constraint_id,
                                 "mandatory_words": ("alfa",), "policy": P},
        "v19:background.unique": {"family": pairs.PAIR_2.focal.constraint_id,
                                  "policy": P},
        "v19:background.other": {"family": pairs.PAIR_2.target.constraint_id,
                                 "mandatory_words": ("bravo",), "policy": P}})
    built = W.construct_witness(composition, P)
    assert built.constructed, built.reason
    assert built.structure["mandatory_placed"] == []
    assert C.run_conjunction(composition, built.text or "", P).v_all == 1


def test_s7c_a_witness_built_under_another_grammar_is_refused():
    permissive = dataclasses.replace(P, policy_id="v19:list-policy.permissive",
                                     extra_items_permitted=True)
    with pytest.raises(W.WitnessConstructionError, match="not a cross-check"):
        W.construct_witness(p1_composition(), permissive)


# ------------------------------------------------------------ S8 fail-closed
def test_s8_a_missing_solver_produces_solver_unavailable():
    """Was: a bare ImportError, because `solve` imported z3 before identifying it."""
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "z3":
            raise ImportError("simulated: no z3 installed")
        return real_import(name, *args, **kwargs)

    saved = sys.modules.pop("z3", None)
    builtins.__import__ = blocked
    try:
        certificate = C.certify_composition(p2_composition(), P)
        assert certificate.outcome is C.Outcome.SOLVER_UNAVAILABLE
        assert not certificate.certified and "missing" in certificate.reason
        with pytest.raises(S.SolverUnavailable):
            S.solve(p2_composition())
        finding = next(f for f in stage2.certify_satisfiability(
            REGISTRY.slots).findings if "frozen solver is available" in f.requirement)
        assert not finding.satisfied
    finally:
        builtins.__import__ = real_import
        if saved is not None:
            sys.modules["z3"] = saved


def test_s8b_a_solver_timeout_fails_closed():
    labels = tuple(f"i{n:03d}" for n in range(30))
    relation = OrderingRelation(
        items=labels, edges=tuple((labels[i], labels[i + 1]) for i in range(29)))
    composition = E.encode_composition(
        "p1/big/B", pair_id="p1", arm="B", load=2, realisations={
            pairs.PAIR_1.target.constraint_id: {"n_items": 30, "policy": P},
            pairs.PAIR_1.focal.constraint_id: {"relation": relation, "policy": P}})
    record = S.solve(composition, bounds={"timeout_ms": 1})
    assert record.status == "unknown" and not record.progressable
    certificate = C.certify_composition(composition, P, bounds={"timeout_ms": 1})
    assert certificate.outcome is C.Outcome.SOLVER_NOT_SAT


def test_s8c_a_solver_exception_is_its_own_outcome():
    import z3
    original = z3.Solver.check
    try:
        z3.Solver.check = lambda self, *a, **k: (_ for _ in ()).throw(
            RuntimeError("simulated solver failure"))
        assert C.certify_composition(
            p2_composition(), P).outcome is C.Outcome.SOLVER_ERROR
    finally:
        z3.Solver.check = original


# ------------------------------------------------------- S9..S10 provenance
def test_s9_the_certificate_hash_is_reproducible_within_a_process():
    """Was: four certifications of one composition gave four hashes.

    Two causes. `Solver.to_smt2()` varied between calls, so the recorded input is now
    the sorted s-expressions; and the model varied for variables the conjunction does
    not pin, so the record commits to a status over a canonical question and archives
    the model without hashing it.
    """
    assert len({C.certify_composition(p2_composition(), P).certificate_hash
                for _ in range(8)}) == 1
    records = [S.solve(p2_composition()) for _ in range(4)]
    assert len({r.record_hash for r in records}) == 1
    assert len({tuple(r.assertions) for r in records}) == 1
    assert all(r.model for r in records)           # archived, not hashed
    assert "model" not in records[0].state()
    assert "model" in records[0].describe()


def test_s9b_the_hash_is_reproducible_across_processes_too():
    code = ("from dci.v19 import encoding as E, certification as C, pairs;"
            "from dci.v19.parsing import CANONICAL_LIST_POLICY as P;"
            "c=E.encode_composition('p2/1/B',pair_id='p2',arm='B',load=2,"
            "realisations={pairs.PAIR_2.target.constraint_id:"
            "{'mandatory_words':('alpha',),'policy':P},"
            "pairs.PAIR_2.focal.constraint_id:{'policy':P}});"
            "print(C.certify_composition(c,P).certificate_hash)")
    seen = {subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, check=True).stdout.strip()
            for _ in range(2)}
    assert seen == {C.certify_composition(p2_composition(), P).certificate_hash}


def test_s9c_the_solver_remained_a_plain_solver():
    """An intermediate repair used Optimize to canonicalise the model. Reverted.

    Minimising forty variables can time out where a satisfiability check would not,
    and a timeout is `unknown`, which section 8.5 turns into rejection of the whole
    proposal - so the solver would have been answering a harder question than the
    science asked, to serve a hash.
    """
    import inspect
    source = inspect.getsource(S.solve)
    assert "z3.Solver()" in source and "z3.Optimize()" not in source
    assert "wrong trade" in source


def test_s10_the_certificate_carries_the_implementation_and_bundle_hashes():
    """Was: only `spec_hash`, so a code change with no declared-semantics effect was
    invisible in the certificate."""
    state = C.certify_composition(p2_composition(), P).state()
    assert state["verifier_bundle_hash"] == V.bundle_hash(P)
    built = V.bundle(P)
    for constraint_id, row in state["verifier_bundle"].items():
        assert row["implementation_hash"] == built[constraint_id].implementation_hash
        assert row["spec_hash"] == built[constraint_id].spec.spec_hash
    assert state["witness_constructor"] == W.CONSTRUCTOR_ID


def test_s10b_the_three_identities_separate_what_from_how_from_observed():
    certificate = C.certify_composition(p2_composition(), P)
    assert len({certificate.semantic_id, certificate.implementation_id,
                certificate.evidence_id}) == 3
    assert certificate.certificate_hash


def _behaviour_preserving_replacement(text, policy):
    """Same behaviour, different source. Defined at module level so it HAS source."""
    return list(textlib.word_tokens(text, policy) and
                [textlib.fold(token, policy)
                 for token in textlib.word_tokens(text, policy)])


def test_s10c_a_code_change_moves_the_implementation_identity_and_not_the_semantic():
    # The identities are lazy properties, so they must be materialised BEFORE the
    # swap - otherwise both are computed against the replacement and compare equal.
    before = C.certify_composition(p2_composition(), P)
    baseline = (before.semantic_id, before.implementation_id, before.evidence_id,
                before.certificate_hash)
    original = textlib.folded_tokens
    try:
        textlib.folded_tokens = _behaviour_preserving_replacement
        after = C.certify_composition(p2_composition(), P)
        assert after.semantic_id == baseline[0]
        assert after.implementation_id != baseline[1]
        assert after.evidence_id == baseline[2]        # behaviour unchanged
        assert after.certificate_hash != baseline[3]
    finally:
        textlib.folded_tokens = original


def test_s10e_a_callable_with_no_readable_source_is_refused():
    """Appendix I wants an invariant hash over the code that ran."""
    with pytest.raises(V.VerifierContractError, match="cannot be read"):
        V.implementation_hash(len)


def test_s7d_a_second_mandatory_word_clause_is_not_dropped():
    """Found by this suite: `_requirements` assigned where it had to accumulate.

    Two background constraints may each require mandatory words. The first set was
    silently lost, so the witness failed a verifier it should have satisfied.
    """
    composition = p1_with_backgrounds("two-word-sets", {
        "v19:background.first": {"family": pairs.PAIR_2.target.constraint_id,
                                 "mandatory_words": ("kilo",), "policy": P},
        "v19:background.second": {"family": pairs.PAIR_2.target.constraint_id,
                                  "mandatory_words": ("lima",), "policy": P},
        "v19:background.unique": {"family": pairs.PAIR_2.focal.constraint_id,
                                  "policy": P}})
    built = W.construct_witness(composition, P)
    assert built.constructed, built.reason
    assert set(built.structure["mandatory_placed"]) == {"kilo", "lima"}
    assert C.run_conjunction(composition, built.text or "", P).v_all == 1


def test_s7e_two_clauses_fixing_one_count_differently_are_a_contradiction():
    """Not last-one-wins: the composition is infeasible and says so."""
    composition = E.Composition(
        composition_id="contradiction", pair_id="p3", arm="B", load=5,
        clauses=(clause(pairs.PAIR_3.target.constraint_id, n_sentences=3),
                 clause(pairs.PAIR_3.focal.constraint_id),
                 background(pairs.PAIR_3.target.constraint_id,
                            "v19:background.other-count", n_sentences=5),
                 background(pairs.PAIR_2.focal.constraint_id,
                            "v19:background.unique"),
                 background(pairs.PAIR_2.target.constraint_id,
                            "v19:background.words", mandatory_words=("zulu",))))
    built = W.construct_witness(composition, P)
    assert not built.constructed
    assert "contradicts itself" in built.reason


def test_s10d_a_semantics_change_moves_the_semantic_identity():
    permissive = dataclasses.replace(P, policy_id="v19:list-policy.permissive",
                                     extra_items_permitted=True)
    loose = C.certify_composition(
        E.encode_composition("p1/loose/B", pair_id="p1", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_1.target.constraint_id: {
                                     "n_items": 2, "policy": permissive},
                                 pairs.PAIR_1.focal.constraint_id: {
                                     "relation": REL2, "policy": permissive}}),
        permissive)
    assert C.certify_composition(p1_composition(), P).semantic_id != loose.semantic_id


# ------------------------------------------------- S11..S12 registry validation
NONSENSE = [
    ("verifiers.p1.ordering_depth", None),
    ("verifiers.p1.ordering_depth", {}),
    ("satisfiability.semantic_reviews", "trust me"),
    ("verifiers.bundle_hash", "0" * 64),
    ("verifiers.specification_bundle", {"protocol": "v19"}),
    ("verifiers.tier1_reliability", {}),
    ("satisfiability.certified_compositions", {}),
    ("verifiers.boundary_mutations", {}),
]


@pytest.mark.parametrize("name,bad", NONSENSE)
def test_s11_a_nonsense_value_is_refused_where_it_is_recorded(name, bad):
    """Was: every one of these froze silently and the gate reported it as met."""
    with pytest.raises(ValueError, match="not admissible for domain"):
        declared_table().freeze(name, bad, by="an adversarial probe")


# The three artifacts that have since been produced are refused by the domain too -
# on a table that has not yet recorded them - and by AlreadyFrozen on the live one.
PRODUCED_NONSENSE = [
    ("satisfiability.encoding_map", 12345),
    ("satisfiability.solver_identity", "z3 0.0.0-does-not-exist"),
    ("satisfiability.witness_constructor", 0),
]


@pytest.mark.parametrize("name,bad", PRODUCED_NONSENSE)
def test_s11f_a_produced_artifact_refuses_nonsense_and_refuses_overwriting(name, bad):
    from dci.v19.resolution import AlreadyFrozen
    from dci.v19.schemas import DomainError, validate
    # The domain still rejects the value on its own terms...
    with pytest.raises(DomainError):
        validate(REGISTRY.slots[name].domain, bad)
    # ...and the live table refuses any overwrite at all, valid or not.
    with pytest.raises(AlreadyFrozen):
        REGISTRY.slots.freeze(name, stand_in.for_domain(REGISTRY.slots[name].domain),
                              by="an adversarial probe")


def test_s11b_the_amended_slots_cannot_be_overwritten_at_all():
    from dci.v19.resolution import AlreadyFrozen
    for name in ("verifiers.p1.list_policy", "verifiers.inherited_reuse_decision",
                 "verifiers.binomial_interval_implementation"):
        with pytest.raises(AlreadyFrozen):
            REGISTRY.slots.freeze(name, "anything", by="probe")


def test_s11c_the_interval_domain_and_its_consumer_now_agree():
    """Was: certification accepted a name `frozen_interval` itself rejected."""
    from dci.v19.resolution import Resolution, SlotTable, pending
    table = SlotTable.of(pending(
        "verifiers.binomial_interval_implementation", "section 10.4",
        Resolution.PENDING_DECISION, "rule", domain="binomial_interval"))
    with pytest.raises(ValueError, match="not admissible for domain"):
        table.freeze("verifiers.binomial_interval_implementation", "agresti_coull",
                     by="probe")
    assert R.frozen_interval(REGISTRY.slots).name == R.AMENDED_INTERVAL


def test_s11d_every_stage_two_slot_declares_a_domain():
    finding = next(f for f in stage2.certify_satisfiability(REGISTRY.slots).findings
                   if "typed domain" in f.requirement)
    assert finding.satisfied, finding.detail


def test_s11e_a_slot_frozen_with_none_no_longer_counts_as_a_decision():
    with pytest.raises(ValueError, match="not admissible for domain"):
        declared_table().freeze("verifiers.p1.ordering_depth", None, by="probe")
    valid = stand_in.resolve(REGISTRY.slots, "verifiers.p1.ordering_depth")
    finding = next(f for f in stage2.certify_verifiers(valid).findings
                   if "focal parameter has a declared domain" in f.requirement)
    assert finding.satisfied


def test_s12_the_battery_is_regenerated_rather_than_asserted():
    """Was: `{"not-a-real-template": {"n_mutations": 1000}}` satisfied section 8.7."""
    from dci.v19.schemas import DomainError, validate
    with pytest.raises(DomainError):
        validate("boundary_mutations",
                 {cid: {"n_mutations": 1000, "records_hash": "0" * 64}
                  for cid in M.template_ids()})
    with pytest.raises(DomainError, match="not a v19 constraint id"):
        validate("boundary_mutations", {"nonsense": {"n_mutations": 1000}})
    validate("boundary_mutations", stand_in.battery_evidence())


def test_s12b_the_regenerated_battery_meets_the_floor_for_all_six_templates():
    from dci.v19.mutation import frozen_battery_evidence
    evidence = frozen_battery_evidence()
    assert set(evidence) == set(M.template_ids()) and len(evidence) == 6
    for template, row in sorted(evidence.items()):
        assert row["n_mutations"] >= M.MUTATIONS_PER_TEMPLATE, template
        assert row["distinct_texts"] == row["n_mutations"], template
        assert len(row["boundaries"]) >= 5, template


def test_s12c_the_battery_is_deterministic_so_a_frozen_hash_can_be_rechecked():
    from dci.v19.mutation import frozen_battery_evidence
    first, second = frozen_battery_evidence(), frozen_battery_evidence()
    assert {k: v["records_hash"] for k, v in first.items()} == \
        {k: v["records_hash"] for k, v in second.items()}


def test_s12d_a_template_is_a_declared_constraint_which_settles_the_ambiguity():
    """Section 8.7 says "each constraint template"; the two halves disagreed."""
    assert set(M.template_ids()) == {rule.constraint_id for rule in pairs.rules()}
    assert len(M.template_ids()) == 6


# ------------------------------------------------------- S13 review integrity
@pytest.mark.parametrize("value", ["no", "false", "0", 0.0, [], 1, None])
def test_s13_a_review_verdict_must_be_a_boolean(value):
    """Was: the string "no" was truthy, so it certified a composition."""
    with pytest.raises(C.CertificationError, match="is not a bool"):
        C.ReviewerVerdict("reviewer-a", value, "a rationale")


def test_s13b_only_a_genuine_pass_certifies():
    composition = p2_composition()
    assert C.certify_composition(composition, P,
                                 review=passing_review(composition)).certified
    built = W.construct_witness(composition, P)
    failed = C.SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash,
        clause_ids=C.review_required(composition),
        reviews=(C.ReviewerVerdict("a", False, "the reading does not hold"),
                 C.ReviewerVerdict("b", False, "agreed")))
    assert C.certify_composition(
        composition, P, review=failed).outcome is C.Outcome.REVIEW_FAILED


def test_s13c_duplicate_clause_ids_are_refused():
    """Was: the coverage check compared sets, so one review covered two clauses."""
    with pytest.raises(C.CertificationError, match="appear twice"):
        C.SemanticReview(
            composition_id="x", witness_hash="h",
            clause_ids=(pairs.PAIR_2.focal.constraint_id,
                        pairs.PAIR_2.focal.constraint_id),
            reviews=(C.ReviewerVerdict("a", True, "x"),
                     C.ReviewerVerdict("b", True, "y")))


def test_s13d_an_unresolved_disagreement_still_does_not_certify():
    split = C.SemanticReview(
        composition_id="x", witness_hash="h",
        clause_ids=(pairs.PAIR_2.focal.constraint_id,),
        reviews=(C.ReviewerVerdict("a", True, "yes"),
                 C.ReviewerVerdict("b", False, "no")))
    assert split.state is C.ReviewState.HUMAN_REVIEW_REQUIRED
    assert "unresolved disagreement" in split.reason


# ------------------------------------------- what the amendments did NOT change
def test_solver_sat_alone_still_never_certifies():
    composition = p1_composition()
    assert S.solve(composition).status == "sat"
    assert not C.certify_composition(composition, P).certified


def test_a_missing_verifier_column_still_refuses_to_form_a_conjunction():
    certificate = C.certify_composition(
        p2_composition(), P, omit_verifiers=(pairs.PAIR_2.focal.constraint_id,))
    assert certificate.outcome is C.Outcome.VERIFIER_INCOMPLETE


def test_the_three_clauses_with_incomplete_coverage_still_need_human_review():
    partial = {row["constraint_id"] for row in E.coverage_report(P)
               if row["coverage"] == "PARTIAL"}
    assert partial == {pairs.PAIR_1.focal.constraint_id,
                       pairs.PAIR_2.focal.constraint_id,
                       pairs.PAIR_3.target.constraint_id}
    assert REGISTRY.slots["satisfiability.semantic_reviews"].pending


def test_the_bullet_list_as_sentences_coupling_is_declared_not_repaired():
    """Section 4.4 defers to the frozen segmentation, so this is not a defect to fix.

    What changed is that it is declared: the marker patterns are inside Pair 3's
    specification hash, and the clause declares incomplete coverage, which is what
    triggers human semantic review.
    """
    bullets = "- alpha\n- beta gamma\n- delta epsilon zeta"
    assert V.verify_exact_sentence_count(bullets, n_sentences=3,
                                         policy=P).verdict is V.Verdict.PASS
    row = next(r for r in E.coverage_report(P)
               if r["constraint_id"] == pairs.PAIR_3.target.constraint_id)
    assert row["coverage"] == "PARTIAL"
    spec = V.bundle(P)[pairs.PAIR_3.target.constraint_id].spec
    assert spec.segmentation["marker_patterns"] == list(P.marker_patterns())


def test_a_homoglyph_is_still_outside_any_automated_rule():
    """The split is gone; the confusable is human audit material (section 10.6)."""
    assert textlib.word_tokens(f"{CYRILLIC_A}pple apple", TP) == [
        f"{CYRILLIC_A}pple", "apple"]
    assert V.verify_all_words_unique(f"{CYRILLIC_A}pple apple",
                                     text_policy=TP).verdict is V.Verdict.PASS


def test_ordering_depth_is_now_decided_by_a4_and_carries_no_grid():
    """A4 settled the construct; the grid stays a Stage 5 output (D6)."""
    slot = REGISTRY.slots["verifiers.p1.ordering_depth"]
    assert slot.resolved and slot.domain == "ordering_depth"
    assert slot.get()["grid"] is None
    assert not declared_table()["verifiers.p1.ordering_depth"].resolved

def test_stage_two_is_certified_on_everything_except_human_adjudication():
    """The gate is READY; certification still fails closed on the Tier-1 audit."""
    row = REGISTRY.stage_status("stage_2_verifiers")
    assert row["status"] == "READY"
    report = stage2.certify_stage2(REGISTRY.slots)
    assert not report.certified
    assert len(report.outstanding) == 1
    assert "human-adjudicated" in report.outstanding[0].requirement

def test_the_registry_still_reports_nothing_fabricated():
    from dci.v19 import registry
    registry.assert_nothing_fabricated()


def test_a_zero_width_space_now_defeats_nothing():
    """The standing check on the removal that repaired three measurements at once."""
    assert V.verify_all_words_unique(f"wo{ZERO_WIDTH}rd word",
                                     text_policy=TP).verdict is V.Verdict.FAIL
    assert V.verify_mandatory_words(f"wo{ZERO_WIDTH}rd", mandatory_words=("word",),
                                    text_policy=TP).verdict is V.Verdict.PASS
    assert V.verify_transitive_order(f"- al{ZERO_WIDTH}fa\n- bravo", relation=REL2,
                                     policy=P).verdict is V.Verdict.PASS
