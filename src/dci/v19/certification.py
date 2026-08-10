"""SATCERT: the section 8.6 evidential hierarchy, assembled and fail-closed.

    "The evidential hierarchy is therefore: solver `sat` for the encoded
    abstraction; concrete all-verifier-pass witness for operational
    natural-language satisfiability; and human semantic review where deterministic
    coverage is incomplete. No weaker item substitutes for a stronger item when the
    latter is required."

Three pieces of evidence, and this module's job is to refuse to accept any of them
in place of another. In particular `solver == sat` is never sufficient: it is
recorded, and then a concrete witness is constructed and run through *every*
applicable verifier, and only then does human review enter where the encoding
declared itself incomplete.

COMPLETENESS BEFORE CONJUNCTION
-------------------------------
The verifier conjunction is computed only when every active constraint produced a
scored outcome. A composition with three declared constraints and two available
results does not get a conjunction over the two: `v_all` stays None and
certification fails. Multiplying the available subset would report a number whose
meaning silently depends on which verifiers happened to run.

WHEN THE SOLVER AND THE VERIFIER DISAGREE
-----------------------------------------
`WITNESS_REJECTED` is its own outcome and not a variety of construction failure.
It means the solver said the conjunction was satisfiable, a witness was built, and
a deterministic verifier rejected it - so the encoded logical semantics and the
measured semantics do not agree. That is a scientific defect in the encoding or in
the measurement, never a composition to retry with a different seed, and it is
reported as such.
"""
from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import verifiers as V
from dci.v19.encoding import Clause, ClauseKind, Composition
from dci.v19.parsing import ListPolicy
from dci.v19.solver import SolverRecord, SolverUnavailable, solve
from dci.v19.witness import WitnessRecord, construct_witness


class ReviewState(str, enum.Enum):
    """Section 8.6's human-review states, with refusal as the default."""

    AUTO_CERTIFIED = "AUTO_CERTIFIED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    HUMAN_REVIEW_PASSED = "HUMAN_REVIEW_PASSED"
    HUMAN_REVIEW_FAILED = "HUMAN_REVIEW_FAILED"


class Outcome(str, enum.Enum):
    """Why a composition is or is not certified. One reason, never a boolean."""

    CERTIFIED = "CERTIFIED"
    SOLVER_UNAVAILABLE = "SOLVER_UNAVAILABLE"
    SOLVER_NOT_SAT = "SOLVER_NOT_SAT"
    WITNESS_NOT_CONSTRUCTED = "WITNESS_NOT_CONSTRUCTED"
    VERIFIER_INCOMPLETE = "VERIFIER_INCOMPLETE"
    VERIFIER_ERROR = "VERIFIER_ERROR"
    WITNESS_REJECTED = "WITNESS_REJECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REVIEW_FAILED = "REVIEW_FAILED"


class CertificationError(RuntimeError):
    """A certification could not be assembled as declared."""


# ------------------------------------------------------------ semantic review

@dataclass(frozen=True)
class ReviewerVerdict:
    """One human reviewer's judgement on the uncovered semantics."""
    reviewer_id: str
    satisfied: bool
    rationale: str

    def __post_init__(self):
        if not self.reviewer_id:
            raise CertificationError("a review needs an identified reviewer")
        if not self.rationale:
            raise CertificationError(
                f"{self.reviewer_id}: a semantic review states its rationale, or it "
                "is a vote rather than a review")

    def state(self) -> dict[str, Any]:
        return {"reviewer_id": self.reviewer_id, "satisfied": self.satisfied,
                "rationale": self.rationale}


@dataclass(frozen=True)
class SemanticReview:
    """The section 8.6 review of the clauses the encoding does not exhaust.

    "Such clauses receive two independent reviews, with a third reviewer
    adjudicating disagreement; unresolved disagreement fails certification."
    """
    composition_id: str
    witness_hash: str
    clause_ids: tuple[str, ...]
    reviews: tuple[ReviewerVerdict, ...] = ()
    adjudication: ReviewerVerdict | None = None

    def __post_init__(self):
        if not self.clause_ids:
            raise CertificationError(
                f"{self.composition_id}: a semantic review with no clauses under "
                "review would certify nothing while looking like evidence")
        identities = [r.reviewer_id for r in self.reviews]
        if len(set(identities)) != len(identities):
            raise CertificationError(
                f"{self.composition_id}: reviewer(s) appear twice ({identities}); "
                "section 8.6 requires two INDEPENDENT reviews")
        if len(self.reviews) > 2:
            raise CertificationError(
                f"{self.composition_id}: {len(self.reviews)} reviews recorded; "
                "section 8.6 specifies two plus an adjudicator, and a larger panel "
                "would change the decision rule")
        if self.adjudication is not None:
            if self.adjudication.reviewer_id in identities:
                raise CertificationError(
                    f"{self.composition_id}: the adjudicator "
                    f"{self.adjudication.reviewer_id!r} is one of the two original "
                    "reviewers, so the third opinion is not independent")
            if len(self.reviews) < 2:
                raise CertificationError(
                    f"{self.composition_id}: an adjudication was recorded before "
                    "two reviews existed, so there was no disagreement to resolve")

    @property
    def state(self) -> ReviewState:
        if len(self.reviews) < 2:
            return ReviewState.HUMAN_REVIEW_REQUIRED
        first, second = self.reviews
        if first.satisfied == second.satisfied:
            return (ReviewState.HUMAN_REVIEW_PASSED if first.satisfied
                    else ReviewState.HUMAN_REVIEW_FAILED)
        if self.adjudication is None:
            # Unresolved disagreement. Section 8.6 fails certification here; it
            # does not average the two or prefer the earlier reviewer.
            return ReviewState.HUMAN_REVIEW_REQUIRED
        return (ReviewState.HUMAN_REVIEW_PASSED if self.adjudication.satisfied
                else ReviewState.HUMAN_REVIEW_FAILED)

    @property
    def reason(self) -> str:
        if len(self.reviews) < 2:
            return (f"{len(self.reviews)} of 2 independent reviews recorded for "
                    f"{len(self.clause_ids)} incompletely encoded clause(s)")
        first, second = self.reviews
        if first.satisfied != second.satisfied and self.adjudication is None:
            return ("the two independent reviews disagree and no third reviewer "
                    "has adjudicated; unresolved disagreement fails certification")
        if self.state is ReviewState.HUMAN_REVIEW_FAILED:
            return "the review concluded the uncovered semantics are not satisfied"
        return "both reviews, or the adjudication, found the semantics satisfied"

    def describe(self) -> dict[str, Any]:
        return {"composition_id": self.composition_id,
                "witness_hash": self.witness_hash,
                "clause_ids": list(self.clause_ids),
                "state": self.state.value, "reason": self.reason,
                "reviews": [r.state() for r in self.reviews],
                "adjudication": (self.adjudication.state()
                                 if self.adjudication else None)}


def review_required(composition: Composition) -> tuple[str, ...]:
    """Which clauses trigger human review, by their own coverage declaration.

    Section 8.6: review is required "only for clauses whose intended semantics are
    not exhaustively covered by the frozen machine encoding and deterministic
    verifier". So the trigger is data, not judgement, and the coding model is never
    the reviewer.
    """
    return tuple(c.constraint_id for c in composition.partially_covered)


# ------------------------------------------------------- the verifier conjunction

@dataclass(frozen=True)
class Conjunction:
    """(V_1, ..., V_m) and their product, or an explicit refusal to form one."""
    composition_id: str
    witness_hash: str
    required: tuple[str, ...]
    outcomes: Mapping[str, V.VerifierOutcome]

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(c for c in self.required if c not in self.outcomes)

    @property
    def unscored(self) -> tuple[str, ...]:
        return tuple(c for c in self.required
                     if c in self.outcomes and not self.outcomes[c].scored)

    @property
    def complete(self) -> bool:
        return not self.missing and not self.unscored

    @property
    def vector(self) -> tuple[int | None, ...]:
        """Per-constraint pass indicators in the composition's own order."""
        return tuple(
            None if constraint not in self.outcomes
            or not self.outcomes[constraint].scored
            else int(self.outcomes[constraint].verdict is V.Verdict.PASS)
            for constraint in self.required)

    @property
    def v_all(self) -> int | None:
        """The product, or None when the conjunction may not be formed.

        None is the whole point: a conjunction over the available subset would be
        a number whose meaning depends on which verifiers happened to run.
        """
        if not self.complete:
            return None
        product = 1
        for value in self.vector:
            product *= int(value or 0)
        return product

    @property
    def rejected_by(self) -> tuple[str, ...]:
        return tuple(c for c, outcome in self.outcomes.items()
                     if outcome.scored and outcome.verdict is V.Verdict.FAIL)

    def describe(self) -> dict[str, Any]:
        return {"composition_id": self.composition_id,
                "witness_hash": self.witness_hash,
                "required": list(self.required), "vector": list(self.vector),
                "complete": self.complete, "v_all": self.v_all,
                "missing": list(self.missing), "unscored": list(self.unscored),
                "rejected_by": list(self.rejected_by),
                "outcomes": {c: o.describe() for c, o in self.outcomes.items()}}


def _invoke(clause: Clause, text: str, policy: ListPolicy) -> V.VerifierOutcome:
    """Run the deterministic verifier for one clause on the witness."""
    built = V.bundle(policy)
    verifier = built.get(clause.constraint_id)
    if verifier is None:
        raise CertificationError(
            f"{clause.constraint_id} has a clause but no verifier, so its column "
            "of the conjunction cannot be filled")
    if clause.kind is ClauseKind.EXACT_ITEM_COUNT:
        return verifier.invoke(text, n_items=clause.parameters["n_items"])
    if clause.kind is ClauseKind.ITEM_PRECEDENCE:
        return verifier.invoke(text, relation=clause.parameters["relation"])
    if clause.kind is ClauseKind.EXACT_SENTENCE_COUNT:
        return verifier.invoke(text, n_sentences=clause.parameters["n_sentences"])
    if clause.kind is ClauseKind.MANDATORY_TOKENS:
        return verifier.invoke(
            text, mandatory_words=tuple(clause.parameters["mandatory_words"]))
    return verifier.invoke(text)


def run_conjunction(composition: Composition, text: str, policy: ListPolicy,
                    *, omit: Sequence[str] = ()) -> Conjunction:
    """Every applicable verifier on the same witness.

    `omit` exists for the tests that must demonstrate the fail-closed path: a
    conjunction missing a column has to be refused, and the only honest way to show
    that is to withhold a column on purpose.
    """
    outcomes = {}
    for clause in composition.clauses:
        if clause.constraint_id in omit:
            continue
        outcomes[clause.constraint_id] = _invoke(clause, text, policy)
    return Conjunction(composition_id=composition.composition_id,
                       witness_hash=sha(["v19/witness", text]),
                       required=composition.constraint_ids, outcomes=outcomes)


# --------------------------------------------------------------- the certificate

@dataclass(frozen=True)
class SatCertificate:
    """One composition's complete satisfiability evidence, or its refusal.

    Everything section 8.6 says to archive is a field: the encoding, the solver
    input and output, the witness and its construction procedure, the verifier
    results, the semantic review where applicable, and the hashes that tie them
    together.
    """
    composition: Composition
    outcome: Outcome
    reason: str
    solver: SolverRecord | None
    witness: WitnessRecord | None
    conjunction: Conjunction | None
    review: SemanticReview | None
    review_state: ReviewState

    @property
    def certified(self) -> bool:
        return self.outcome is Outcome.CERTIFIED

    def state(self) -> dict[str, Any]:
        return {"composition": self.composition.describe(),
                "outcome": self.outcome.value,
                "solver": self.solver.describe() if self.solver else None,
                "witness": self.witness.state() if self.witness else None,
                "conjunction": (self.conjunction.describe()
                                if self.conjunction else None),
                "review": self.review.describe() if self.review else None,
                "review_state": self.review_state.value}

    @property
    def certificate_hash(self) -> str:
        return sha(["v19/sat-certificate", self.state()])

    def describe(self) -> dict[str, Any]:
        return {**self.state(), "reason": self.reason,
                "certified": self.certified,
                "certificate_hash": self.certificate_hash}


def certify_composition(composition: Composition, policy: ListPolicy, *,
                        seed: int = 0,
                        review: SemanticReview | None = None,
                        bounds: Mapping[str, int] | None = None,
                        omit_verifiers: Sequence[str] = ()) -> SatCertificate:
    """Assemble SATCERT for one composition, refusing at the first missing item.

    The order is the evidential hierarchy's own: solver, then witness, then the
    complete verifier conjunction, then human review. Each step's failure has its
    own `Outcome`, so a rejection says which kind of evidence was absent rather
    than only that certification did not happen.
    """
    def refuse(outcome: Outcome, reason: str, **parts: Any) -> SatCertificate:
        return SatCertificate(
            composition=composition, outcome=outcome, reason=reason,
            solver=parts.get("solver"), witness=parts.get("witness"),
            conjunction=parts.get("conjunction"), review=parts.get("review"),
            review_state=parts.get("review_state",
                                   ReviewState.HUMAN_REVIEW_REQUIRED
                                   if review_required(composition)
                                   else ReviewState.AUTO_CERTIFIED))

    try:
        record = solve(composition, bounds=bounds)
    except SolverUnavailable as error:
        return refuse(Outcome.SOLVER_UNAVAILABLE,
                      f"required solver output is missing: {error}")
    if not record.progressable:
        return refuse(Outcome.SOLVER_NOT_SAT,
                      f"solver status {record.status!r}: {record.reason}",
                      solver=record)

    built = construct_witness(composition, seed=seed)
    if not built.constructed:
        return refuse(Outcome.WITNESS_NOT_CONSTRUCTED,
                      f"witness construction failed: {built.reason}",
                      solver=record, witness=built)

    conjunction = run_conjunction(composition, built.text or "", policy,
                                 omit=omit_verifiers)
    if not conjunction.complete:
        detail = []
        if conjunction.missing:
            detail.append(f"no result for {list(conjunction.missing)}")
        if conjunction.unscored:
            detail.append(f"unscored result for {list(conjunction.unscored)}")
        return refuse(
            Outcome.VERIFIER_ERROR if conjunction.unscored
            else Outcome.VERIFIER_INCOMPLETE,
            f"the verifier conjunction is incomplete ({'; '.join(detail)}), so it "
            "may not be formed over the available subset",
            solver=record, witness=built, conjunction=conjunction)
    if conjunction.v_all != 1:
        return refuse(
            Outcome.WITNESS_REJECTED,
            f"the solver reported sat but the constructed witness is rejected by "
            f"{list(conjunction.rejected_by)}. The encoded logical semantics and "
            "the deterministic verifier semantics disagree; this is a defect in "
            "one of them, not a composition to retry with another seed",
            solver=record, witness=built, conjunction=conjunction)

    triggered = review_required(composition)
    if not triggered:
        return SatCertificate(
            composition=composition, outcome=Outcome.CERTIFIED,
            reason=("solver sat, a constructed witness, and every applicable "
                    "verifier passing; the encoding declares complete "
                    "deterministic coverage, so no human review is required"),
            solver=record, witness=built, conjunction=conjunction, review=None,
            review_state=ReviewState.AUTO_CERTIFIED)

    if review is None:
        return refuse(
            Outcome.REVIEW_REQUIRED,
            f"{len(triggered)} clause(s) declare incomplete deterministic "
            f"coverage ({list(triggered)}) and no semantic review is recorded. "
            "Section 8.6 requires two independent reviews with a third "
            "adjudicating disagreement",
            solver=record, witness=built, conjunction=conjunction,
            review_state=ReviewState.HUMAN_REVIEW_REQUIRED)
    if set(review.clause_ids) != set(triggered):
        return refuse(
            Outcome.REVIEW_REQUIRED,
            f"the recorded review covers {sorted(review.clause_ids)} but the "
            f"clauses needing review are {sorted(triggered)}",
            solver=record, witness=built, conjunction=conjunction, review=review,
            review_state=ReviewState.HUMAN_REVIEW_REQUIRED)
    if review.witness_hash != built.witness_hash:
        return refuse(
            Outcome.REVIEW_REQUIRED,
            "the recorded review is against a different witness "
            f"({review.witness_hash[:12]} rather than "
            f"{built.witness_hash[:12]}); section 8.6 runs the review on the same "
            "witness the verifiers passed",
            solver=record, witness=built, conjunction=conjunction, review=review,
            review_state=ReviewState.HUMAN_REVIEW_REQUIRED)
    if review.state is ReviewState.HUMAN_REVIEW_PASSED:
        return SatCertificate(
            composition=composition, outcome=Outcome.CERTIFIED,
            reason=("solver sat, a constructed witness, every applicable verifier "
                    "passing, and human semantic review of the incompletely "
                    "encoded clauses"),
            solver=record, witness=built, conjunction=conjunction, review=review,
            review_state=review.state)
    return refuse(
        Outcome.REVIEW_FAILED if review.state is ReviewState.HUMAN_REVIEW_FAILED
        else Outcome.REVIEW_REQUIRED,
        f"semantic review is {review.state.value}: {review.reason}",
        solver=record, witness=built, conjunction=conjunction, review=review,
        review_state=review.state)


def assert_certified(certificate: SatCertificate) -> SatCertificate:
    """Fail closed unless the composition holds full SATCERT."""
    if certificate.certified:
        return certificate
    raise CertificationError(
        f"{certificate.composition.composition_id} is not certified "
        f"[{certificate.outcome.value}]: {certificate.reason}")
