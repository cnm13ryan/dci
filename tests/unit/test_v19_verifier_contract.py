"""The common verifier contract: four fields that section 10.1 keeps apart.

The inherited `OutcomeStatus` is `full | partial | violation | unscorable`, which
merges section 10.1's secondary compliance field with part of its generation state.
Section 10.1 records three orthogonal things and the directive adds a fourth:

  * the constraint verdict, PASS or FAIL and nothing else;
  * the generation state, SCORABLE / UNPARSEABLE / TRUNCATED / EMPTY / REFUSAL;
  * the secondary compliance level, FULL / PARTIAL / VIOLATION;
  * whether scoring happened at all.

The last is the one that bites. Section 10.1: "a technical failure before a
final-answer segment is delivered has no fabricated behavioural verdict". A
verifier that crashes and returns FAIL has fabricated one, and the failure would be
indistinguishable from the model breaking a rule. So `verdict` is None unless
scoring succeeded, and `f_a` raises rather than returning a number.
"""
import dataclasses

import pytest

from dci.v19 import field_roles, pairs
from dci.v19 import verifiers as V
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation
from dci.v19.verifiers import (
    CALLER_SUPPLIED_STATES,
    Compliance,
    GenerationState,
    Scoring,
    Verdict,
    Verifier,
    VerifierContractError,
    VerifierOutcome,
)

pytestmark = pytest.mark.cpu

SPEC = V.bundle(P)[pairs.PAIR_3.target.constraint_id].spec


def outcome(**changes) -> VerifierOutcome:
    base = {"verifier_id": SPEC.verifier_id, "constraint_id": SPEC.constraint_id,
            "spec_hash": SPEC.spec_hash, "parameters": {},
            "scoring": Scoring.SCORED, "verdict": Verdict.PASS,
            "generation_state": GenerationState.SCORABLE,
            "compliance": Compliance.FULL, "reason": "because", "evidence": {}}
    return VerifierOutcome(**{**base, **changes})


# --------------------------------------------- the four fields stay orthogonal
def test_the_four_field_vocabularies_are_section_ten_ones():
    assert {v.value for v in Verdict} == {"PASS", "FAIL"}
    assert {v.value for v in GenerationState} == {
        "SCORABLE", "UNPARSEABLE", "TRUNCATED", "EMPTY", "REFUSAL"}
    assert {v.value for v in Compliance} == {"FULL", "PARTIAL", "VIOLATION"}
    assert {v.value for v in Scoring} == {
        "SCORED", "MISSING_METADATA", "VERIFIER_ERROR"}


def test_unscorable_is_not_a_compliance_level_in_v19():
    """The inherited field had a fourth value; the v19 compliance field has three."""
    from dci.verifiers.rules import OutcomeStatus
    assert "unscorable" in getattr(OutcomeStatus, "__args__", ())
    assert "unscorable" not in {c.value.lower() for c in Compliance}


def test_a_technical_scoring_failure_may_not_carry_a_verdict():
    for scoring in (Scoring.MISSING_METADATA, Scoring.VERIFIER_ERROR):
        with pytest.raises(VerifierContractError, match="never arrive as a "
                                                       "behavioural verdict"):
            outcome(scoring=scoring, verdict=Verdict.FAIL, compliance=None)


def test_a_technical_scoring_failure_may_not_carry_a_compliance_level():
    with pytest.raises(VerifierContractError, match="compliance level is recorded"):
        outcome(scoring=Scoring.VERIFIER_ERROR, verdict=None,
                compliance=Compliance.VIOLATION)


def test_a_scored_outcome_must_carry_a_verdict():
    with pytest.raises(VerifierContractError, match="requires PASS or FAIL"):
        outcome(verdict=None, compliance=None)


def test_full_compliance_and_a_passing_verdict_must_agree():
    """Section 10.1: for an exact target, PARTIAL implies primary failure."""
    with pytest.raises(VerifierContractError, match="contradicts verdict"):
        outcome(verdict=Verdict.PASS, compliance=Compliance.PARTIAL)
    with pytest.raises(VerifierContractError, match="contradicts verdict"):
        outcome(verdict=Verdict.FAIL, compliance=Compliance.FULL)
    outcome(verdict=Verdict.FAIL, compliance=Compliance.PARTIAL)
    outcome(verdict=Verdict.FAIL, compliance=Compliance.VIOLATION)


def test_an_outcome_with_no_reason_is_refused():
    with pytest.raises(VerifierContractError, match="every outcome states why"):
        outcome(reason="")


def test_the_field_types_are_checked():
    with pytest.raises(VerifierContractError, match="not a Scoring"):
        outcome(scoring="SCORED")
    with pytest.raises(VerifierContractError, match="not a GenerationState"):
        outcome(generation_state="SCORABLE")
    with pytest.raises(VerifierContractError, match="not a Compliance"):
        outcome(verdict=Verdict.FAIL, compliance="PARTIAL")


# ------------------------------------------------------------- the f_a bridge
def test_f_a_is_one_on_failure_and_zero_on_pass():
    assert outcome(verdict=Verdict.PASS, compliance=Compliance.FULL).f_a == 0
    assert outcome(verdict=Verdict.FAIL, compliance=Compliance.VIOLATION).f_a == 1


@pytest.mark.parametrize("scoring", [Scoring.MISSING_METADATA,
                                     Scoring.VERIFIER_ERROR])
def test_f_a_refuses_when_scoring_did_not_happen(scoring):
    unscored = outcome(scoring=scoring, verdict=None, compliance=None)
    assert not unscored.scored
    with pytest.raises(VerifierContractError, match="Rerun verification on the "
                                                   "stored bytes"):
        _ = unscored.f_a


# ------------------------------------------------------ a crash is not a FAIL
def test_a_crashing_verifier_returns_verifier_error_not_a_failure():
    def explode(text, **kwargs):
        raise ZeroDivisionError("scoring blew up")

    broken = Verifier(spec=SPEC, run=explode, implementation=(explode,),
                      status="new")
    got = broken.invoke("some text", n_sentences=3)
    assert got.scoring is Scoring.VERIFIER_ERROR
    assert got.verdict is None and got.compliance is None
    assert "ZeroDivisionError" in got.reason
    with pytest.raises(VerifierContractError):
        _ = got.f_a


def test_a_crash_preserves_the_caller_supplied_generation_state():
    def explode(text, **kwargs):
        raise RuntimeError("boom")

    broken = Verifier(spec=SPEC, run=explode, implementation=(explode,),
                      status="new")
    got = broken.invoke("x", delivered_state=GenerationState.TRUNCATED)
    assert got.generation_state is GenerationState.TRUNCATED
    assert "delivered_state" not in got.parameters


def test_invoke_passes_a_working_verifier_through_untouched():
    built = V.bundle(P)[pairs.PAIR_3.target.constraint_id]
    assert built.invoke("One. Two.", n_sentences=2).verdict is Verdict.PASS


def test_the_caller_supplied_states_are_the_two_the_text_cannot_show():
    assert CALLER_SUPPLIED_STATES == (GenerationState.TRUNCATED,
                                      GenerationState.REFUSAL)


# ------------------------------------------------- evidence stays diagnostic
def test_evidence_may_not_carry_a_field_a_primary_formula_could_consume():
    """Section 11.8: a primary field arriving through an evidence blob has
    bypassed the role registry."""
    for laundered in ("arm", "load", "task", "target_verdict", "f_a"):
        with pytest.raises(field_roles.FieldRoleViolation,
                           match="primary-usable field"):
            V.assert_evidence_is_diagnostic(outcome(evidence={laundered: 1}))


def test_evidence_may_carry_declared_diagnostic_fields():
    for allowed in ("generation_state", "exploit_suspected", "u_r"):
        V.assert_evidence_is_diagnostic(outcome(evidence={allowed: 1}))


def test_evidence_may_carry_names_that_are_not_analysis_fields_at_all():
    V.assert_evidence_is_diagnostic(
        outcome(evidence={"observed_count": 3, "parse": {}}))


RELATION = OrderingRelation(items=("alpha", "beta"), edges=(("alpha", "beta"),))

# One legal invocation per declared constraint, so every real verifier's evidence
# is checked rather than only the hand-built outcomes above.
CALLS = {
    pairs.PAIR_1.target.constraint_id: {"n_items": 2},
    pairs.PAIR_1.focal.constraint_id: {"relation": RELATION},
    pairs.PAIR_2.target.constraint_id: {"mandatory_words": ("alpha",)},
    pairs.PAIR_2.focal.constraint_id: {},
    pairs.PAIR_3.target.constraint_id: {"n_sentences": 2},
    pairs.PAIR_3.focal.constraint_id: {},
}
# The bundle binds each verifier's policy, so a caller passes only the parameter
# realisation. That is the S5 repair: no call site chooses its own text semantics.


@pytest.mark.parametrize("constraint_id", sorted(CALLS))
def test_every_real_verifier_produces_diagnostic_only_evidence(constraint_id):
    got = V.bundle(P)[constraint_id].invoke("- alpha\n- beta",
                                            **CALLS[constraint_id])
    assert got.scoring is Scoring.SCORED, got.reason
    V.assert_evidence_is_diagnostic(got)


def test_the_call_table_covers_every_declared_constraint():
    assert set(CALLS) == {rule.constraint_id for rule in pairs.rules()}


# --------------------------------------------------------------- the spec hash
def test_a_spec_needs_every_attribution_field():
    for field in ("verifier_id", "constraint_id", "statement", "rule",
                  "citation", "span"):
        with pytest.raises(ValueError, match="is required"):
            dataclasses.replace(SPEC, **{field: ""})


def test_a_spec_identifier_must_be_v19_native():
    with pytest.raises(ValueError, match="not a v19-native"):
        dataclasses.replace(SPEC, verifier_id="verifier.exact_sentence_count")


@pytest.mark.parametrize("field,value", [
    ("verifier_id", "v19:verifier.other"),
    ("constraint_id", "v19:p3.target.renamed"),
    ("statement", "Produce exactly N+1 sentences."),
    ("rule", "PASS iff the count is at least n_sentences"),
    ("span", "word_normalisation"),
    ("parameters", ("n_paragraphs",)),
    ("inherited_from", "S3"),
])
def test_changing_any_declared_semantic_changes_the_spec_hash(field, value):
    assert dataclasses.replace(SPEC, **{field: value}).spec_hash != SPEC.spec_hash


def test_the_citation_and_the_audit_prose_are_not_part_of_the_hash():
    """Rewording why a rule is cited is not a change of measurement."""
    for field in ("citation", "audit"):
        assert dataclasses.replace(
            SPEC, **{field: "rewritten"}).spec_hash == SPEC.spec_hash


def test_the_segmentation_regexes_are_inside_the_spec_hash():
    """Section 14.2's hash audit is meaningless if it covers only a label."""
    segmentation = V.frozen_segmentation(P.text, P)
    assert segmentation["text_policy"]["word_pattern"] == P.text.word_pattern
    assert segmentation["text_policy_hash"] == P.text.policy_hash
    assert segmentation["marker_patterns"] == list(P.marker_patterns())
    mutated = dataclasses.replace(
        SPEC, segmentation={**segmentation, "text_policy_hash": "0" * 64})
    assert mutated.spec_hash != SPEC.spec_hash


def test_the_pair_one_spec_hashes_contain_the_list_policy_hash():
    built = V.bundle(P)
    for constraint_id in (pairs.PAIR_1.target.constraint_id,
                          pairs.PAIR_1.focal.constraint_id):
        spec = built[constraint_id].spec
        assert spec.segmentation["list_policy_hash"] == P.policy_hash


def test_changing_the_list_policy_changes_both_pair_one_spec_hashes():
    other = dataclasses.replace(P, numbered_items_count=False)
    before, after = V.bundle(P), V.bundle(other)
    for constraint_id in (pairs.PAIR_1.target.constraint_id,
                          pairs.PAIR_1.focal.constraint_id):
        assert (before[constraint_id].spec.spec_hash
                != after[constraint_id].spec.spec_hash), constraint_id


def test_changing_the_list_policy_moves_pair_three_and_not_pair_two():
    """Section 4.4's shared segmentation, now visible in a hash.

    The sentence segmenter strips the list grammar\'s own markers, so a change to
    the marker set changes what a sentence is. Before the repair each span carried
    its own marker regex and the coupling was invisible; now Pair 3\'s specification
    hash moves with the grammar and Pair 2\'s, which reads only words, does not.
    """
    other = dataclasses.replace(P, policy_id="v19:list-policy.probe",
                                numbered_items_count=False)
    before, after = V.bundle(P), V.bundle(other)
    for rule in (pairs.PAIR_2.target, pairs.PAIR_2.focal):
        assert (before[rule.constraint_id].spec.spec_hash
                == after[rule.constraint_id].spec.spec_hash), rule.constraint_id
    for rule in (pairs.PAIR_3.target, pairs.PAIR_3.focal):
        assert (before[rule.constraint_id].spec.spec_hash
                != after[rule.constraint_id].spec.spec_hash), rule.constraint_id


# ------------------------------------------------------ the implementation hash
def test_the_implementation_hash_covers_the_source_actually_executed():
    from dci.verifiers import rules
    one = V.implementation_hash(rules.v_unique_words)
    two = V.implementation_hash(rules.v_unique_words, rules.word_tokens)
    assert one != two
    assert V.implementation_hash(rules.v_unique_words) == one


def test_every_corrected_verifier_hashes_the_text_layer_it_now_reads():
    """The corrected verifiers execute `dci.v19.text`, so that is what is hashed.

    The inherited helpers are deliberately absent: amendment A2 moved the Pair 2 and
    Pair 3 verifiers off them, and an implementation hash still covering
    `rules.word_tokens` would claim code that no longer runs.
    """
    from dci.v19 import text as textlib
    from dci.verifiers import rules
    focal = V.bundle(P)[pairs.PAIR_2.focal.constraint_id]
    assert textlib.folded_tokens in focal.implementation
    assert textlib.normalise in focal.implementation
    assert rules.v_unique_words not in focal.implementation
    assert focal.status == "inherited_corrected"
    assert focal.spec.inherited_from.startswith("L_UNIQ")
    assert focal.spec.correction


def test_the_spec_hash_and_the_implementation_hash_are_different_things():
    """One can move without the other, which is why both are recorded."""
    built = V.bundle(P)[pairs.PAIR_3.target.constraint_id]
    assert built.spec.spec_hash != built.implementation_hash


# ------------------------------------------------------------------ the bundle
def test_the_bundle_covers_exactly_the_six_declared_constraints():
    built = V.assert_bundle_is_complete(P)
    assert set(built) == {rule.constraint_id for rule in pairs.rules()}
    assert len(built) == 6


def test_the_bundle_reports_which_verifiers_are_new_and_which_inherited():
    built = V.bundle(P)
    new = {cid for cid, v in built.items() if v.status == "new"}
    assert new == {pairs.PAIR_1.target.constraint_id,
                   pairs.PAIR_1.focal.constraint_id}
    assert all(built[cid].status == "inherited_corrected"
               for cid in set(built) - new)


def test_a_bundle_missing_a_declared_constraint_is_refused():
    original = V.bundle
    try:
        V.bundle = lambda policy=P: {
            cid: v for cid, v in original(policy).items()
            if not cid.startswith("v19:p1")}
        with pytest.raises(VerifierContractError, match="have no v19 verifier"):
            V.assert_bundle_is_complete(P)
    finally:
        V.bundle = original
    V.assert_bundle_is_complete(P)


def test_a_bundle_carrying_an_undeclared_constraint_is_refused():
    original = V.bundle
    try:
        V.bundle = lambda policy=P: {
            **original(policy),
            "v19:p9.target.invented": original(policy)[
                pairs.PAIR_1.target.constraint_id]}
        with pytest.raises(VerifierContractError, match="undeclared constraint"):
            V.assert_bundle_is_complete(P)
    finally:
        V.bundle = original


def test_the_bundle_state_records_both_hashes_per_verifier():
    state = V.bundle_state(P)
    assert state["list_policy_hash"] == P.policy_hash
    assert set(state["verifiers"]) == {r.constraint_id for r in pairs.rules()}
    for row in state["verifiers"].values():
        assert row["spec_hash"] and row["implementation_hash"]
        assert row["status"] in ("new", "inherited_corrected")


def test_the_bundle_hash_is_deterministic_across_processes():
    """A verifier hash that drifts between runs cannot be an invariant."""
    import subprocess
    import sys
    code = ("from dci.v19.parsing import CANONICAL_LIST_POLICY as P; "
            "from dci.v19.verifiers import bundle_hash; print(bundle_hash(P))")
    seen = {subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, check=True).stdout.strip()
            for _ in range(2)}
    assert seen == {V.bundle_hash(P)}


def test_the_bundle_hash_moves_with_the_list_policy():
    assert V.bundle_hash(dataclasses.replace(
        P, empty_items_count=True)) != V.bundle_hash(P)


def test_the_bundle_state_is_serialisable():
    import json
    json.dumps(V.bundle_state(P))


def test_the_registry_binding_still_reports_pair_one_as_unbuilt():
    """`pairs.VerifierBinding` names a callable in the v15 module and Pair 1 has
    none, which is a fact about the inherited module rather than about v19."""
    unimplemented = {b.verifier_id for b in pairs.unimplemented_verifiers()}
    assert unimplemented == {"v19:verifier.exact_bullet_count",
                             "v19:verifier.transitive_order"}
    assert set(V.bundle(P)) == {r.constraint_id for r in pairs.rules()}
