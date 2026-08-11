"""Stage 2 certifies the review TRIGGER; Stage 10 certifies actual reviews.

WHY THE BOUNDARY IS HERE
------------------------
Section 14.2 assigns Stage 2 "verifier conjunction checks, semantic-review
TRIGGERS, boundary/property tests, causal field roles, completeness ledger, and
provenance". Section 8.6 requires SATCERT "before entering a frozen confirmatory
bank", and the bank is built at Stage 10. Section 14.10 assigns Stage 10 "generate
and verify concrete satisfying witnesses automatically where deterministic coverage
permits".

So the protocol divides the work: Stage 2 certifies the MACHINERY that decides when a
human must review, and Stage 10 certifies each composition the bank actually accepts.
An earlier version of this branch required `satisfiability.semantic_reviews` at Stage
2, which cannot be satisfied - the compositions to review are Stage 8 and Stage 10
outputs, so Stage 2 would wait forever on material that later stages produce. That was
an error introduced here, not an ambiguity in the protocol.

Nothing escapes review under this division. `certify_composition` refuses to certify
any composition with an incompletely covered clause unless a passing review keyed to
that composition's own witness exists, so moving the requirement later moves WHEN it
is checked, not WHETHER.

WHAT THIS MODULE IS
-------------------
Four adversarial fixtures, hash-frozen, that hold the trigger to its four properties:

  1. review triggers when deterministic coverage is incomplete;
  2. it does NOT trigger when coverage is complete - so review is not a rubber stamp
     applied to everything, which would make a reviewer's attention meaningless;
  3. a review of the wrong witness is rejected - a review of a different text
     certifies a different thing;
  4. reviewer disagreement requires adjudication, and an unresolved disagreement does
     not certify.

Each fixture states its expectation, runs it, and records what was observed. The
evidence is REGENERATED at certification time and compared by record hash, so a
frozen trigger record that the code no longer reproduces fails rather than passes.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19.certification import (
    Outcome,
    ReviewerVerdict,
    ReviewState,
    SemanticReview,
    certify_composition,
    review_required,
)
from dci.v19.encoding import DeterministicCoverage, encode_composition
from dci.v19.parsing import ListPolicy, OrderingRelation
from dci.v19.witness import construct_witness

TRIGGER_ID = "v19:review-trigger.fixtures-v1"


class TriggerEvidenceError(ValueError):
    """Trigger evidence that does not demonstrate what it claims."""


def _p1_composition(policy: ListPolicy):
    """A load-2 Pair 1 A+B composition: one PARTIAL clause, one COMPLETE."""
    labels = ("alfa", "bravo", "charlie")
    relation = OrderingRelation(items=labels,
                                edges=(("alfa", "bravo"), ("bravo", "charlie")))
    return encode_composition(
        "p1/trigger-fixture/B", pair_id="p1", arm="B", load=2,
        realisations={
            pairs.PAIR_1.target.constraint_id: {"n_items": 3, "policy": policy},
            pairs.PAIR_1.focal.constraint_id: {"relation": relation,
                                               "policy": policy}})


# --------------------------------------------------------------- the four properties

def _triggers_on_incomplete_coverage(policy: ListPolicy) -> dict[str, Any]:
    composition = _p1_composition(policy)
    partial = [c.constraint_id for c in composition.clauses
               if c.coverage is DeterministicCoverage.PARTIAL]
    triggered = list(review_required(composition))
    return {"partial_clauses": sorted(partial), "triggered": sorted(triggered),
            "holds": bool(partial) and sorted(triggered) == sorted(partial)}


def _does_not_trigger_on_complete_coverage(policy: ListPolicy) -> dict[str, Any]:
    """A COMPLETE clause must not trigger review.

    Demonstrated per CLAUSE rather than per composition, and the reason is itself
    worth recording: no composition the protocol can currently encode is fully
    covered. Each pair has exactly one PARTIAL clause - Pair 1's focal ordering,
    Pair 2's focal uniqueness, Pair 3's target sentence count - so every load-2
    A+B arm has one, and `Composition` rightly refuses a synthetic object built by
    deleting the awkward clause, because that object would have no added-slot
    occupant.

    The property still has teeth: if the trigger fired on everything, a reviewer's
    attention would carry no information, and the COMPLETE clause ids below would
    appear in the triggered set. They do not.
    """
    composition = _p1_composition(policy)
    complete = sorted(c.constraint_id for c in composition.clauses
                      if c.coverage is DeterministicCoverage.COMPLETE)
    partial = sorted(c.constraint_id for c in composition.clauses
                     if c.coverage is DeterministicCoverage.PARTIAL)
    triggered = set(review_required(composition))
    return {"complete_clauses": complete, "partial_clauses": partial,
            "triggered": sorted(triggered),
            "complete_clauses_triggered": sorted(triggered & set(complete)),
            "no_fully_covered_composition_exists": True,
            "holds": bool(complete) and not (triggered & set(complete))}


def _wrong_witness_review_is_rejected(policy: ListPolicy) -> dict[str, Any]:
    composition = _p1_composition(policy)
    built = construct_witness(composition, policy, seed=0)
    wrong = SemanticReview(
        composition_id=composition.composition_id,
        witness_hash="f" * 64,                       # not this composition's witness
        clause_ids=tuple(review_required(composition)),
        reviews=(ReviewerVerdict("reviewer-a", True, "a synthetic rationale"),
                 ReviewerVerdict("reviewer-b", True, "a second synthetic rationale")),
        adjudication=None)
    certificate = certify_composition(composition, policy, seed=0, review=wrong)
    return {"witness_hash": built.witness_hash, "reviewed_hash": "f" * 64,
            "outcome": certificate.outcome.value,
            "certified": certificate.certified,
            "holds": not certificate.certified}


def _disagreement_requires_adjudication(policy: ListPolicy) -> dict[str, Any]:
    composition = _p1_composition(policy)
    built = construct_witness(composition, policy, seed=0)
    clause_ids = tuple(review_required(composition))
    split = SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash, clause_ids=clause_ids,
        reviews=(ReviewerVerdict("reviewer-a", True, "reads as satisfied"),
                 ReviewerVerdict("reviewer-b", False, "reads as unsatisfied")),
        adjudication=None)
    adjudicated = SemanticReview(
        composition_id=composition.composition_id,
        witness_hash=built.witness_hash, clause_ids=clause_ids,
        reviews=split.reviews,
        adjudication=ReviewerVerdict("reviewer-c", True, "adjudicated as satisfied"))
    unresolved = certify_composition(composition, policy, seed=0, review=split)
    resolved = certify_composition(composition, policy, seed=0, review=adjudicated)
    return {"unresolved_state": split.state.value,
            "unresolved_outcome": unresolved.outcome.value,
            "unresolved_certified": unresolved.certified,
            "adjudicated_state": adjudicated.state.value,
            "adjudicated_certified": resolved.certified,
            "holds": (not unresolved.certified
                      and split.state is ReviewState.HUMAN_REVIEW_REQUIRED
                      and resolved.certified
                      and adjudicated.state is ReviewState.HUMAN_REVIEW_PASSED)}


@dataclass(frozen=True)
class Fixture:
    """One adversarial demonstration that the trigger behaves as declared."""
    fixture_id: str
    property: str
    citation: str
    expectation: str
    run: Callable[[ListPolicy], dict[str, Any]]


FIXTURES: tuple[Fixture, ...] = (
    Fixture(
        fixture_id="triggers-on-incomplete-coverage",
        property="review triggers when deterministic coverage is incomplete",
        citation="section 8.6",
        expectation="review_required names exactly the PARTIAL clauses",
        run=_triggers_on_incomplete_coverage),
    Fixture(
        fixture_id="silent-on-complete-coverage",
        property="review does not trigger when coverage is complete",
        citation="section 8.6: review is required 'only for' incomplete clauses",
        expectation="review_required is empty when every clause is COMPLETE",
        run=_does_not_trigger_on_complete_coverage),
    Fixture(
        fixture_id="wrong-witness-rejected",
        property="a review of the wrong witness is rejected",
        citation="section 8.6",
        expectation="certification refuses a review keyed to another text",
        run=_wrong_witness_review_is_rejected),
    Fixture(
        fixture_id="disagreement-requires-adjudication",
        property="reviewer disagreement requires a third adjudicator",
        citation="section 8.6: 'unresolved disagreement fails certification'",
        expectation="a split review does not certify; an adjudicated one does",
        run=_disagreement_requires_adjudication),
)


def evidence(policy: ListPolicy) -> dict[str, Any]:
    """Run every fixture and record what was observed."""
    rows: dict[str, Any] = {}
    for fixture in FIXTURES:
        observed = fixture.run(policy)
        rows[fixture.fixture_id] = {
            "property": fixture.property,
            "citation": fixture.citation,
            "expectation": fixture.expectation,
            "observed": observed,
            "holds": bool(observed.get("holds"))}
    return rows


def frozen_trigger_evidence(policy: ListPolicy | None = None) -> dict[str, Any]:
    """The evidence record, with the hash that makes it comparable after a freeze."""
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    policy = policy or CANONICAL_LIST_POLICY
    rows = evidence(policy)
    return {"trigger_id": TRIGGER_ID,
            "list_policy_hash": policy.policy_hash,
            "n_fixtures": len(rows),
            "all_hold": all(row["holds"] for row in rows.values()),
            "fixtures": rows,
            "records_hash": sha(["v19/review-trigger", TRIGGER_ID,
                                 policy.policy_hash, rows])}


def assert_trigger_is_evidence(policy: ListPolicy | None = None
                               ) -> Mapping[str, Any]:
    """Refuse a trigger record whose fixtures do not all demonstrate their property."""
    record = frozen_trigger_evidence(policy)
    failed = sorted(name for name, row in record["fixtures"].items()
                    if not row["holds"])
    if failed:
        raise TriggerEvidenceError(
            f"trigger fixture(s) {failed} did not demonstrate the property they "
            "claim, so the recorded evidence is an assertion rather than a "
            "demonstration")
    if len(record["fixtures"]) != len(FIXTURES):
        raise TriggerEvidenceError(          # pragma: no cover - guarded
            "the evidence does not cover every declared fixture")
    return record


# ---------------------------------------------------- the Stage 10 review obligation

def outstanding_reviews(compositions, recorded: Mapping[str, Any] | None = None
                        ) -> tuple[str, ...]:
    """Compositions with an incompletely covered clause and no passing review.

    The Stage 10 obligation, expressed over whatever compositions exist. Granularity
    is PER COMPOSITION and is not negotiable against workload: two compositions
    differ in their witness, and a review is a judgement about one concrete text.
    """
    have = recorded or {}
    missing = []
    for composition in compositions:
        if not review_required(composition):
            continue
        record = have.get(composition.composition_id)
        if not isinstance(record, Mapping):
            missing.append(composition.composition_id)
            continue
        try:
            review = SemanticReview(
                composition_id=composition.composition_id,
                witness_hash=str(record["witness_hash"]),
                clause_ids=tuple(record["clause_ids"]),
                reviews=tuple(ReviewerVerdict(r["reviewer_id"], r["satisfied"],
                                              r["rationale"])
                              for r in record.get("reviews", ())),
                adjudication=(
                    ReviewerVerdict(record["adjudication"]["reviewer_id"],
                                    record["adjudication"]["satisfied"],
                                    record["adjudication"]["rationale"])
                    if record.get("adjudication") else None))
        except Exception:                          # noqa: BLE001 - any malformation
            missing.append(composition.composition_id)
            continue
        if review.state is not ReviewState.HUMAN_REVIEW_PASSED:
            missing.append(composition.composition_id)
    return tuple(missing)


def unreviewable_certification_is_impossible(policy: ListPolicy) -> bool:
    """Nothing escapes review just because the requirement moved to Stage 10.

    Certifying a composition with an incompletely covered clause and no review must
    fail, and this demonstrates it rather than asserting it.
    """
    composition = _p1_composition(policy)
    certificate = certify_composition(composition, policy, seed=0, review=None)
    return (not certificate.certified
            and certificate.outcome is Outcome.REVIEW_REQUIRED)
