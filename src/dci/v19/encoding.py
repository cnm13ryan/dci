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

import dataclasses
import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19 import text as textlib
from dci.v19.parsing import ListPolicy, OrderingRelation, require_policy
from dci.v19.resolution import UnresolvedDependency

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


# The roles a clause may occupy inside one composition. `reference` is the
# added-slot occupant of an A+R_j+S arm; its identity is a Stage 8 output, so no
# reference clause can be encoded yet and `encode_reference` says so.
CLAUSE_ROLES = ("target", "focal", "reference", "background")


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
        if self.role not in CLAUSE_ROLES:
            raise EncodingError(
                f"{self.constraint_id}: role {self.role!r} is not one of "
                f"{CLAUSE_ROLES}; a clause with no declared role cannot be checked "
                "against the composition's load")
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
        pair = pairs.pair(self.pair_id)
        if not self.clauses:
            raise EncodingError(
                f"{self.composition_id}: a composition with no clauses would be "
                "certified sat while constraining nothing")
        seen = [c.constraint_id for c in self.clauses]
        duplicated = sorted({c for c in seen if seen.count(c) > 1})
        if duplicated:
            raise EncodingError(
                f"{self.composition_id}: constraint(s) {duplicated} appear twice; a "
                "composition is a set of distinct active constraints")

        # Section 2.1 and section 8.1: every certified composition is A+B+S or
        # A+R_j+S. It therefore has exactly one target - the pair's own - exactly one
        # added-slot occupant, and exactly the backgrounds its load admits.
        targets = [c for c in self.clauses if c.role == "target"]
        if len(targets) != 1:
            raise EncodingError(
                f"{self.composition_id}: {len(targets)} target clause(s). Every "
                "A+B+S and A+R_j+S composition has exactly one target, which is the "
                "primary outcome's own constraint (sections 2.1, 8.6)")
        if targets[0].constraint_id != pair.target.constraint_id:
            raise EncodingError(
                f"{self.composition_id}: declared for {self.pair_id} but its target "
                f"is {targets[0].constraint_id!r}, not "
                f"{pair.target.constraint_id!r}. A composition labelled with one "
                "pair and built from another's constraints is not the pair's "
                "composition")
        occupants = [c for c in self.clauses if c.role in ("focal", "reference")]
        if len(occupants) != 1:
            raise EncodingError(
                f"{self.composition_id}: {len(occupants)} added-slot occupant(s). "
                "The replacement contrast puts exactly one occupant in the added "
                "slot - B in the focal arm, R_j in a reference arm (section 2.1)")
        occupant = occupants[0]
        if self.arm == "B":
            if occupant.role != "focal" \
                    or occupant.constraint_id != pair.focal.constraint_id:
                raise EncodingError(
                    f"{self.composition_id}: the focal arm's occupant must be "
                    f"{pair.focal.constraint_id!r}, got {occupant.constraint_id!r} "
                    f"with role {occupant.role!r}")
        elif occupant.role != "reference":
            raise EncodingError(
                f"{self.composition_id}: arm {self.arm} replaces the focal with a "
                f"reference, but its occupant {occupant.constraint_id!r} has role "
                f"{occupant.role!r}. A+R_j+S is a replacement, not an addition "
                "(section 2.1)")
        backgrounds = [c for c in self.clauses if c.role == "background"]
        expected = 0 if self.load == 2 else 3
        if len(backgrounds) != expected:
            raise EncodingError(
                f"{self.composition_id}: load {self.load} admits exactly {expected} "
                f"background constraint(s), got {len(backgrounds)}. Section 8.1: at "
                "k=2 only the target and the added-slot occupant are active; at k=5 "
                "the same two are accompanied by exactly three backgrounds")
        if len(self.clauses) != self.load:
            raise EncodingError(
                f"{self.composition_id}: load {self.load} with "
                f"{len(self.clauses)} active constraint(s). The compositional load "
                "IS the number of simultaneously active constraints (section 8.1)")
        for clause in backgrounds:
            if clause.constraint_id in (pair.target.constraint_id,
                                        pair.focal.constraint_id):
                raise EncodingError(
                    f"{self.composition_id}: {clause.constraint_id!r} occupies a "
                    "background slot and is also the pair's own target or focal; "
                    "section 8.2 excludes the pair's own constraints from its "
                    "background pool")

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

def _policy(realisation: Mapping[str, Any]) -> ListPolicy:
    """Every clause is bound to the frozen measurement semantics, not just the rule.

    Section 14's certification has to establish that the encoded logic and the
    deterministic verifier agree. What a "list item", a "word" and a "sentence" are
    all come from the frozen grammar and the text policy it carries, so an encoding
    that did not name them could agree with the verifier under one policy and
    disagree under another while keeping the same hash. There is no default here,
    exactly as in `parse_list`.
    """
    try:
        return require_policy(realisation.get("policy"))
    except TypeError as error:
        raise EncodingError(str(error)) from error


def _p1_target(realisation: Mapping[str, Any]) -> Clause:
    policy = _policy(realisation)
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
    policy = _policy(realisation)
    relation = realisation.get("relation")
    if not isinstance(relation, OrderingRelation):
        raise EncodingError(
            "the Pair 1 focal clause needs an OrderingRelation realisation, got "
            f"{type(relation).__name__}")
    # Refuse a relation whose labels the frozen tokenisation cannot identify, rather
    # than encode a clause no witness could ever satisfy.
    relation.assert_labels_are_tokens(policy)
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
    policy = _policy(realisation)
    words = realisation.get("mandatory_words")
    if not isinstance(words, (list, tuple)) or not words:
        raise EncodingError(
            "the Pair 2 target clause needs a non-empty mandatory word set")
    if any(not isinstance(w, str) or not w.strip() for w in words):
        raise EncodingError(f"mandatory words must be non-empty strings: {words!r}")
    # Folded through the frozen text policy, not with a locally chosen rule. The
    # audit found the encoding using str.casefold where the verifier used str.lower,
    # so the clause could require one distinct token where the verifier sought two.
    folded = [textlib.fold(w, policy.text) for w in words]
    split = {w: textlib.word_tokens(w, policy.text) for w in words
             if len(textlib.word_tokens(w, policy.text)) != 1}
    if split:
        raise EncodingError(
            f"mandatory word(s) are not single word tokens under "
            f"{policy.text.policy_id}: {split}. Presence of a word the tokeniser "
            "splits is not decidable as the rule states")
    return Clause(
        constraint_id=pairs.PAIR_2.target.constraint_id, role="target",
        kind=ClauseKind.MANDATORY_TOKENS,
        parameters={"mandatory_words": list(words), "folded": folded,
                    "distinct_required": len(set(folded)),
                    "text_policy_hash": policy.text.policy_hash},
        features=("token_multiplicity", "n_tokens", "n_distinct_tokens"),
        coverage=DeterministicCoverage.COMPLETE,
        citation="sections 4.1, 4.3")


def _p2_focal(realisation: Mapping[str, Any]) -> Clause:
    policy = _policy(realisation)
    return Clause(
        constraint_id=pairs.PAIR_2.focal.constraint_id, role="focal",
        kind=ClauseKind.ALL_TOKENS_DISTINCT,
        parameters={"text_policy_hash": policy.text.policy_hash},
        features=("n_tokens", "n_distinct_tokens", "token_multiplicity"),
        coverage=DeterministicCoverage.PARTIAL,
        uncovered_semantics=(
            "the abstraction equates distinctness with the token counts agreeing "
            "under the frozen tokenisation. Invisible characters no longer defeat "
            "it - they are removed before tokenising - but confusables remain "
            "outside any automated rule: a Cyrillic look-alike is a different "
            "string and NFKC does not merge it, so a projection satisfying this "
            "clause can still look to a reader like a repeated word. Section 10.6 "
            "assigns homoglyphs to human audit material, not to code"),
        citation="sections 4.1, 4.3, 10.6")


def _p3_target(realisation: Mapping[str, Any]) -> Clause:
    policy = _policy(realisation)
    n_sentences = realisation.get("n_sentences")
    if (isinstance(n_sentences, bool) or not isinstance(n_sentences, int)
            or n_sentences < 1):
        raise EncodingError(
            f"n_sentences={n_sentences!r} is not a positive integer, so the Pair 3 "
            "target has no parameter realisation to encode")
    return Clause(
        constraint_id=pairs.PAIR_3.target.constraint_id, role="target",
        kind=ClauseKind.EXACT_SENTENCE_COUNT,
        parameters={"n_sentences": n_sentences,
                    "list_policy_hash": policy.policy_hash},
        features=("n_sentences",),
        coverage=DeterministicCoverage.PARTIAL,
        uncovered_semantics=(
            "the abstraction counts sentences as the frozen segmentation does, and "
            "that segmentation strips the list grammar\'s own markers and treats "
            "each remaining line as a sentence, so a projection satisfying this "
            "clause need not contain that many sentences as a reader would count "
            "them. The coupling is now explicit - the marker patterns are inside "
            "this clause\'s hash - but it is not removed"),
        citation="sections 4.1, 4.4")


def _p3_focal(realisation: Mapping[str, Any]) -> Clause:
    policy = _policy(realisation)
    return Clause(
        constraint_id=pairs.PAIR_3.focal.constraint_id, role="focal",
        kind=ClauseKind.INCREASING_SENTENCE_LENGTHS,
        parameters={"list_policy_hash": policy.policy_hash},
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

    Refuses an unknown identifier rather than guessing from its family: section 5.1
    says existing identifiers "are not treated as authoritative where they collide
    or are unverified", and an unencodable constraint must fail closed rather than be
    dropped from the conjunction.
    """
    if constraint_id not in ENCODERS:
        raise EncodingError(
            f"{constraint_id!r} has no canonical encoding. A constraint with no "
            "machine encoding cannot be silently omitted from the conjunction: "
            f"encodable constraints are {sorted(ENCODERS)}")
    return ENCODERS[constraint_id](realisation)


def encode_background(constraint_id: str, realisation: Mapping[str, Any], *,
                      background_id: str) -> Clause:
    """The same rule family, occupying a background slot under its own identity.

    Section 8.2 gives every background entry "a unique constraint ID" and excludes
    the pair's own target, focal and admitted references from the pool. The frozen
    pools are a Stage 1/8 content output, so this is how a load-5 composition is
    assembled from a rule family whose background identity already exists.
    """
    if not background_id.startswith("v19:background."):
        raise EncodingError(
            f"{background_id!r} is not a v19-native background identifier; section "
            "8.2 requires a unique constraint ID per background entry")
    base = encode_clause(constraint_id, realisation)
    return dataclasses.replace(base, constraint_id=background_id, role="background")


def encode_reference(pair_id: str, arm: str) -> Clause:
    """The added-slot occupant of an A+R_j+S arm - which does not exist yet.

    Section 14.8 admits the four references only after the hard gates, the coupling
    and wording audits, the simultaneous calipers, the joint certificate,
    deterministic ranking and independent validation. Encoding a reference clause
    before that would invent the counterfactual class, so this refuses and names the
    slot the caller is waiting on.
    """
    pairs.pair(pair_id)
    pairs.assert_arm(arm)
    if arm == "B":
        raise EncodingError("arm B carries the focal constraint, not a reference")
    raise UnresolvedDependency(
        f"the occupant of {pair_id}/{arm} is an admitted reference identity, which "
        f"is a Stage 8 output (reference.{pair_id}.{arm}). A reference arm cannot be "
        "encoded until that slot is frozen; certifying one now would invent the "
        "counterfactual class the whole design rests on")


def encode_composition(composition_id: str, *, pair_id: str, arm: str, load: int,
                       realisations: Mapping[str, Mapping[str, Any]],
                       backgrounds: Mapping[str, Mapping[str, Any]] | None = None
                       ) -> Composition:
    """Encode every active constraint of one arm into one conjunction.

    `backgrounds` maps a v19 background identity to `{"family": <constraint id>,
    ...realisation}`, so a load-5 composition names its backgrounds explicitly
    rather than inferring them from the order of a dict.
    """
    pairs.pair(pair_id)
    clauses = [encode_clause(cid, realisations[cid]) for cid in realisations]
    for background_id, spec in (backgrounds or {}).items():
        family = spec.get("family")
        if not isinstance(family, str):
            raise EncodingError(
                f"{background_id}: a background entry names the rule family it "
                "instantiates")
        clauses.append(encode_background(
            family, {k: v for k, v in spec.items() if k != "family"},
            background_id=background_id))
    return Composition(composition_id=composition_id, pair_id=pair_id, arm=arm,
                       load=load, clauses=tuple(clauses))


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


def encoding_map_state(policy: ListPolicy) -> dict[str, Any]:
    """The frozen encoding map, as the registry slot must carry it.

    Naming the abstract projection, every clause family and its coverage
    declaration, so freezing `satisfiability.encoding_map` freezes what a solver
    `sat` result actually covers rather than a label for it.
    """
    return {"abstract_features": dict(ABSTRACT_FEATURES),
            "clause_kinds": [kind.value for kind in ClauseKind],
            "list_policy_hash": policy.policy_hash,
            "text_policy_hash": policy.text.policy_hash,
            "clauses": list(coverage_report(policy))}


def coverage_report(policy: ListPolicy) -> tuple[dict[str, Any], ...]:
    """Per-constraint coverage, so the review trigger is auditable up front."""
    rows = []
    example = {"n_items": 3, "n_sentences": 3, "mandatory_words": ("alpha",),
               "policy": policy,
               "relation": OrderingRelation(items=("alfa", "bravo"),
                                            edges=(("alfa", "bravo"),))}
    for constraint_id in sorted(ENCODERS):
        clause = encode_clause(constraint_id, example)
        rows.append({"constraint_id": constraint_id, "kind": clause.kind.value,
                     "coverage": clause.coverage.value,
                     "uncovered_semantics": clause.uncovered_semantics,
                     "features": list(clause.features)})
    return tuple(rows)
