"""Canonical structured encodings of the constraints, and of one composition.

Section 8.6 requires the conjunction of a whole composition to be encoded "for
machine-expressible clauses", and is careful about what that buys: "A `sat` result
establishes satisfiability only of the encoded abstract feature projection. It does
not establish that a natural-language answer satisfying the full intended semantics
exists."

Two things follow, and both are structural here rather than advisory.

FIRST, the encoding is over an EXPLICIT abstraction, declared once. A response is
projected onto a small vector of integer features - how many list items, how many
sentences, where each declared item sits, how long each sentence is, how many
tokens and how many distinct tokens - and every clause is a statement about that
vector. Natural language is never parsed inside the solver; the clause is built
from the frozen instantiated constraint and its parameter realisation.

SECOND, each clause declares how much of its intended semantics the abstraction
actually covers. `DeterministicCoverage.COMPLETE` means the projection loses
nothing that could make the clause false; `PARTIAL` means it does, and names what.
That field is what triggers the section 8.6 human review, so an incompletely
encoded clause cannot quietly ride a `sat` result into a frozen bank.

The mapping from a frozen instantiated constraint to its canonical clause is
deterministic and hashed, so a changed parameter realisation, a changed clause
kind, or a changed coverage declaration all move the composition's identity.
"""
from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19.parsing import OrderingRelation

# The abstract feature projection. Section 8.6's "encoded abstract feature
# projection" is exactly this list and nothing more, which is why it is written
# down rather than left implicit in whichever clauses happen to exist.
ABSTRACT_FEATURES: Mapping[str, str] = {
    "n_items": "number of list items in the response",
    "n_sentences": "number of sentences in the response",
    "item_position": "0-based position of each declared Pair 1 item among the items",
    "sentence_length": "word-token count of each sentence, in order",
    "n_tokens": "total word tokens in the response",
    "n_distinct_tokens": "distinct word tokens in the response",
    "token_multiplicity": "occurrence count of each distinguished token",
}


class ClauseKind(str, enum.Enum):
    """The machine-expressible clause families the three pairs need."""

    EXACT_ITEM_COUNT = "exact_item_count"
    ITEM_PRECEDENCE = "item_precedence"
    EXACT_SENTENCE_COUNT = "exact_sentence_count"
    INCREASING_SENTENCE_LENGTHS = "increasing_sentence_lengths"
    MANDATORY_TOKENS = "mandatory_tokens"
    ALL_TOKENS_DISTINCT = "all_tokens_distinct"


class DeterministicCoverage(str, enum.Enum):
    """How much of a clause's intended semantics the abstraction captures.

    Section 8.6 requires human semantic review "only for clauses whose intended
    semantics are not exhaustively covered by the frozen machine encoding and
    deterministic verifier". PARTIAL is that condition, declared per clause.
    """

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class EncodingError(ValueError):
    """A constraint that cannot be encoded as declared."""


@dataclass(frozen=True)
class Clause:
    """One instantiated constraint, projected onto the abstract features."""
    constraint_id: str
    role: str
    kind: ClauseKind
    parameters: Mapping[str, Any]
    features: tuple[str, ...]
    coverage: DeterministicCoverage
    uncovered_semantics: str = ""
    citation: str = ""

    def __post_init__(self):
        if not isinstance(self.kind, ClauseKind):
            raise EncodingError(f"{self.kind!r} is not a ClauseKind")
        if not isinstance(self.coverage, DeterministicCoverage):
            raise EncodingError(f"{self.coverage!r} is not a DeterministicCoverage")
        unknown = [f for f in self.features if f not in ABSTRACT_FEATURES]
        if unknown:
            raise EncodingError(
                f"{self.constraint_id}: feature(s) {unknown} are outside the "
                f"declared abstract projection {sorted(ABSTRACT_FEATURES)}; a "
                "clause over an undeclared feature is not part of what a sat "
                "result covers")
        if not self.features:
            raise EncodingError(
                f"{self.constraint_id}: a clause constrains no feature, so the "
                "solver would report sat without having considered it")
        if self.coverage is DeterministicCoverage.PARTIAL \
                and not self.uncovered_semantics:
            raise EncodingError(
                f"{self.constraint_id}: coverage is PARTIAL but nothing says what "
                "is uncovered, so the section 8.6 reviewer would have no question "
                "to answer")
        if self.coverage is DeterministicCoverage.COMPLETE \
                and self.uncovered_semantics:
            raise EncodingError(
                f"{self.constraint_id}: coverage is COMPLETE yet uncovered "
                f"semantics are named ({self.uncovered_semantics!r}); the two "
                "cannot both be true")

    def state(self) -> dict[str, Any]:
        return {"constraint_id": self.constraint_id, "role": self.role,
                "kind": self.kind.value,
                "parameters": _canonical(self.parameters),
                "features": list(self.features),
                "coverage": self.coverage.value,
                "uncovered_semantics": self.uncovered_semantics}

    @property
    def clause_hash(self) -> str:
        return sha(["v19/clause", self.state()])


def _canonical(value: Any) -> Any:
    """A JSON-shaped, order-stable form so the hash is reproducible."""
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, OrderingRelation):
        return value.state()
    return value


@dataclass(frozen=True)
class Composition:
    """One prospective A+B+S or A+R_j+S arm, as a conjunction of clauses.

    Section 8.6: "Every prospective A+B+S and A+R_j+S composition must receive
    SATCERT before entering a frozen confirmatory bank. Individual constraint
    validity and pairwise compatibility are insufficient." So the unit of
    certification is the whole arm, and `clauses` is its conjunction.
    """
    composition_id: str
    pair_id: str
    arm: str
    load: int
    clauses: tuple[Clause, ...]

    def __post_init__(self):
        if not self.composition_id:
            raise EncodingError("a composition needs an identifier")
        pairs.assert_arm(self.arm)
        pairs.assert_load(self.load)
        if not self.clauses:
            raise EncodingError(
                f"{self.composition_id}: a composition with no clauses would be "
                "certified sat while constraining nothing")
        seen = [c.constraint_id for c in self.clauses]
        duplicated = sorted({c for c in seen if seen.count(c) > 1})
        if duplicated:
            raise EncodingError(
                f"{self.composition_id}: constraint(s) {duplicated} appear twice; "
                "a composition is a set of distinct active constraints")
        # Section 8.1: at k=2 the target and the added-slot occupant are active; at
        # k=5 exactly three backgrounds join them. A composition whose clause count
        # cannot correspond to its load is mis-declared rather than merely unusual.
        if self.load == 2 and len(self.constraint_ids) > 2:
            raise EncodingError(
                f"{self.composition_id}: load 2 admits the target and the "
                f"added-slot occupant only, but {len(self.constraint_ids)} "
                "constraints are active (section 8.1)")

    @property
    def constraint_ids(self) -> tuple[str, ...]:
        return tuple(c.constraint_id for c in self.clauses)

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(c.role for c in self.clauses)

    @property
    def partially_covered(self) -> tuple[Clause, ...]:
        """Clauses whose intended semantics the abstraction does not exhaust."""
        return tuple(c for c in self.clauses
                     if c.coverage is DeterministicCoverage.PARTIAL)

    def state(self) -> dict[str, Any]:
        return {"composition_id": self.composition_id, "pair_id": self.pair_id,
                "arm": self.arm, "load": self.load,
                "clauses": [c.state() for c in
                            sorted(self.clauses, key=lambda c: c.constraint_id)]}

    @property
    def encoding_hash(self) -> str:
        """Identity of the structured encoding, not of the natural-language arm."""
        return sha(["v19/composition-encoding", self.state()])

    def describe(self) -> dict[str, Any]:
        return {**self.state(), "encoding_hash": self.encoding_hash,
                "partially_covered": [c.constraint_id
                                      for c in self.partially_covered]}


# --------------------------------------------- the frozen constraint -> clause map
#
# One entry per declared v19 constraint. The map is keyed by constraint id rather
# than by family so that a renamed or added constraint fails to encode instead of
# silently reusing another rule's semantics.

def _list_policy(realisation: Mapping[str, Any]):
    """The Pair 1 clauses are bound to the measurement semantics, not just the rule.

    Section 14's certification has to establish that the encoded logic and the
    deterministic verifier agree. What a "list item" is comes from the list policy,
    so an encoding that did not name the policy could agree with the verifier under
    one policy and disagree under another while keeping the same hash. There is no
    default, exactly as in `parse_list`.
    """
    from dci.v19.parsing import ListPolicy
    policy = realisation.get("policy")
    if not isinstance(policy, ListPolicy):
        raise EncodingError(
            "a Pair 1 clause must be encoded against an explicit ListPolicy: what "
            "counts as a list item is a measurement decision the preregistration "
            f"does not fix, and {type(policy).__name__} was supplied")
    return policy


def _p1_target(realisation: Mapping[str, Any]) -> Clause:
    policy = _list_policy(realisation)
    n_items = realisation.get("n_items")
    if isinstance(n_items, bool) or not isinstance(n_items, int) or n_items < 1:
        raise EncodingError(
            f"n_items={n_items!r} is not a positive integer, so the Pair 1 target "
            "has no parameter realisation to encode")
    return Clause(
        constraint_id=pairs.PAIR_1.target.constraint_id, role="target",
        kind=ClauseKind.EXACT_ITEM_COUNT,
        parameters={"n_items": n_items, "list_policy_hash": policy.policy_hash},
        features=("n_items",), coverage=DeterministicCoverage.COMPLETE,
        citation="section 4.1 table row 1")


def _p1_focal(realisation: Mapping[str, Any]) -> Clause:
    policy = _list_policy(realisation)
    relation = realisation.get("relation")
    if not isinstance(relation, OrderingRelation):
        raise EncodingError(
            "the Pair 1 focal clause needs an OrderingRelation realisation, got "
            f"{type(relation).__name__}")
    return Clause(
        constraint_id=pairs.PAIR_1.focal.constraint_id, role="focal",
        kind=ClauseKind.ITEM_PRECEDENCE,
        parameters={"relation": relation,
                    "closure": [list(e) for e in relation.closure()],
                    "list_policy_hash": policy.policy_hash,
                    "extra_items_permitted": policy.extra_items_permitted},
        features=("n_items", "item_position"),
        coverage=DeterministicCoverage.PARTIAL,
        uncovered_semantics=(
            "the abstraction places each declared item at an integer position and "
            "checks the closure over those positions; it does not establish that a "
            "reader would identify the item at that position AS that item, which "
            "is the identification the list policy's label rule decides"),
        citation="sections 4.1, 4.2")


def _p2_target(realisation: Mapping[str, Any]) -> Clause:
    words = realisation.get("mandatory_words")
    if not isinstance(words, (list, tuple)) or not words:
        raise EncodingError(
            "the Pair 2 target clause needs a non-empty mandatory word set")
    if any(not isinstance(w, str) or not w for w in words):
        raise EncodingError(f"mandatory words must be non-empty strings: {words!r}")
    folded = [w.casefold() for w in words]
    return Clause(
        constraint_id=pairs.PAIR_2.target.constraint_id, role="target",
        kind=ClauseKind.MANDATORY_TOKENS,
        parameters={"mandatory_words": list(words),
                    "folded": folded,
                    "distinct_required": len(set(folded))},
        features=("token_multiplicity", "n_tokens", "n_distinct_tokens"),
        coverage=DeterministicCoverage.COMPLETE,
        citation="sections 4.1, 4.3")


def _p2_focal(realisation: Mapping[str, Any]) -> Clause:
    return Clause(
        constraint_id=pairs.PAIR_2.focal.constraint_id, role="focal",
        kind=ClauseKind.ALL_TOKENS_DISTINCT, parameters={},
        features=("n_tokens", "n_distinct_tokens", "token_multiplicity"),
        coverage=DeterministicCoverage.PARTIAL,
        uncovered_semantics=(
            "the abstraction equates distinctness with the token counts agreeing "
            "under the frozen tokenisation; the audit demonstrated that a "
            "zero-width character or a homoglyph makes two identical words into "
            "distinct tokens, so a projection satisfying this clause can still "
            "repeat a word as a reader would count words"),
        citation="sections 4.1, 4.3, 10.6")


def _p3_target(realisation: Mapping[str, Any]) -> Clause:
    n_sentences = realisation.get("n_sentences")
    if (isinstance(n_sentences, bool) or not isinstance(n_sentences, int)
            or n_sentences < 1):
        raise EncodingError(
            f"n_sentences={n_sentences!r} is not a positive integer, so the Pair 3 "
            "target has no parameter realisation to encode")
    return Clause(
        constraint_id=pairs.PAIR_3.target.constraint_id, role="target",
        kind=ClauseKind.EXACT_SENTENCE_COUNT,
        parameters={"n_sentences": n_sentences}, features=("n_sentences",),
        coverage=DeterministicCoverage.PARTIAL,
        uncovered_semantics=(
            "the abstraction counts sentences as the frozen segmentation does, and "
            "the audit demonstrated that segmentation strips list markers and "
            "treats each line as a sentence, so a projection satisfying this "
            "clause need not contain that many sentences as a reader would count "
            "them"),
        citation="sections 4.1, 4.4")


def _p3_focal(realisation: Mapping[str, Any]) -> Clause:
    return Clause(
        constraint_id=pairs.PAIR_3.focal.constraint_id, role="focal",
        kind=ClauseKind.INCREASING_SENTENCE_LENGTHS, parameters={},
        features=("n_sentences", "sentence_length", "n_tokens"),
        coverage=DeterministicCoverage.COMPLETE,
        citation="sections 4.1, 4.4")


ENCODERS = {
    pairs.PAIR_1.target.constraint_id: _p1_target,
    pairs.PAIR_1.focal.constraint_id: _p1_focal,
    pairs.PAIR_2.target.constraint_id: _p2_target,
    pairs.PAIR_2.focal.constraint_id: _p2_focal,
    pairs.PAIR_3.target.constraint_id: _p3_target,
    pairs.PAIR_3.focal.constraint_id: _p3_focal,
}


def encode_clause(constraint_id: str, realisation: Mapping[str, Any]) -> Clause:
    """The canonical clause for one instantiated constraint.

    Refuses an unknown identifier rather than guessing from its family: section
    5.1 says existing identifiers "are not treated as authoritative where they
    collide or are unverified", and an unencodable constraint must fail closed
    rather than be dropped from the conjunction.
    """
    if constraint_id not in ENCODERS:
        raise EncodingError(
            f"{constraint_id!r} has no canonical encoding. A constraint with no "
            "machine encoding cannot be silently omitted from the conjunction: "
            f"encodable constraints are {sorted(ENCODERS)}")
    return ENCODERS[constraint_id](realisation)


def encode_composition(composition_id: str, *, pair_id: str, arm: str, load: int,
                       realisations: Mapping[str, Mapping[str, Any]]
                       ) -> Composition:
    """Encode every active constraint of one arm into one conjunction."""
    pairs.pair(pair_id)
    clauses = tuple(encode_clause(cid, realisations[cid])
                    for cid in realisations)
    return Composition(composition_id=composition_id, pair_id=pair_id, arm=arm,
                       load=load, clauses=clauses)


def assert_encoders_cover_every_declared_constraint() -> None:
    """Every target and focal constraint has a canonical encoding.

    A missing encoder would mean a composition silently certified on a subset of
    its clauses, which is exactly what section 8.6 rules out.
    """
    required = {rule.constraint_id for rule in pairs.rules()}
    missing = sorted(required - set(ENCODERS))
    if missing:
        raise EncodingError(
            f"{len(missing)} declared constraint(s) have no canonical encoding: "
            f"{missing}")
    stray = sorted(set(ENCODERS) - required)
    if stray:
        raise EncodingError(f"encoders exist for undeclared constraint(s) {stray}")


def coverage_report() -> tuple[dict[str, Any], ...]:
    """Per-constraint coverage, so the review trigger is auditable up front."""
    rows = []
    from dci.v19.parsing import INHERITED_MARKER_POLICY
    example = {"n_items": 3, "n_sentences": 3, "mandatory_words": ("alpha",),
               "policy": INHERITED_MARKER_POLICY,
               "relation": OrderingRelation(items=("a", "b"),
                                            edges=(("a", "b"),))}
    for constraint_id in sorted(ENCODERS):
        clause = encode_clause(constraint_id, example)
        rows.append({"constraint_id": constraint_id, "kind": clause.kind.value,
                     "coverage": clause.coverage.value,
                     "uncovered_semantics": clause.uncovered_semantics,
                     "features": list(clause.features)})
    return tuple(rows)
