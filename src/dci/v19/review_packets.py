"""Section 8.6 semantic-review packets: what a human is asked, and nothing more.

    "Human semantic review is required only for clauses whose intended semantics are
    not exhaustively covered by the frozen machine encoding and deterministic
    verifier. Such clauses receive two independent reviews, with a third reviewer
    adjudicating disagreement; unresolved disagreement fails certification."

Three clauses declare incomplete coverage, so three questions exist, and each is asked
against the concrete witness the verifiers accepted - the same witness, because a
review of a different text would certify something else.

BLINDING
--------
Section 10.6: "Human adjudication is blinded to arm, automatic verdict, and constraint
role where feasible." A packet therefore omits the arm, every verdict, the pair
identity, the role, and the composition identifier - which encodes the arm in its own
name. `assert_blinded` checks that, so a field added later cannot leak one back in.

What a packet must keep is the material the question cannot be answered without: the
constraint's statement, the parameter realisation, the uncovered semantics being
asked about, and the witness text. The statement does narrow what the constraint is;
that is the "where feasible" limit, and it is recorded rather than glossed.

WHAT THESE PACKETS ARE NOT
--------------------------
They are not reviews. Nothing in this module records a verdict, and
`dci.v19.certification.ReviewerVerdict` requires a real bool from a named reviewer
with a rationale. They are also not the whole set the study will need: the only
compositions that exist today are the three load-2 A+B arms, because admitted
references are a Stage 8 output and background pools are Stage 1/8 content. Every
composition Stage 10 accepts will need its own packet against its own witness.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19.certification import review_required
from dci.v19.encoding import Clause, Composition, DeterministicCoverage
from dci.v19.parsing import ListPolicy
from dci.v19.witness import construct_witness

# Fields a packet must never carry, each with the reason section 10.6 gives.
FORBIDDEN_IN_PACKET: Mapping[str, str] = {
    "arm": "blinded to arm",
    "role": "blinded to constraint role",
    "pair_id": "the pair identifies the arm's family and the role with it",
    "composition_id": "the identifier encodes the arm, for example 'p2/1/B'",
    "verdict": "blinded to the automatic verdict",
    "v_all": "the conjunction is the automatic verdict in aggregate",
    "vector": "likewise",
    "compliance": "the secondary compliance field is a verdict",
    "verifier_id": "names the role through the verifier that measures it",
    "constraint_id": "names the pair and the role",
}


class PacketError(ValueError):
    """A packet that would not be a fair or answerable question."""


def _statement_for(clause: Clause) -> str:
    """The requirement in the protocol's own words, found by clause KIND.

    Deliberately not by constraint id: a background occupant carries its own
    identity, and looking the statement up by kind keeps the packet from revealing
    whether the reviewer is looking at a pair's own rule or at a background.
    """
    from dci.v19.encoding import ClauseKind
    by_kind = {
        ClauseKind.EXACT_ITEM_COUNT: pairs.PAIR_1.target,
        ClauseKind.ITEM_PRECEDENCE: pairs.PAIR_1.focal,
        ClauseKind.MANDATORY_TOKENS: pairs.PAIR_2.target,
        ClauseKind.ALL_TOKENS_DISTINCT: pairs.PAIR_2.focal,
        ClauseKind.EXACT_SENTENCE_COUNT: pairs.PAIR_3.target,
        ClauseKind.INCREASING_SENTENCE_LENGTHS: pairs.PAIR_3.focal,
    }
    rule = by_kind.get(clause.kind)
    if rule is None:                              # pragma: no cover - guarded
        raise PacketError(f"{clause.kind!r} has no declared statement")
    return rule.statement


def _packet_id(composition: Composition, clause: Clause, witness_hash: str) -> str:
    """An opaque identifier: the reviewer learns nothing from it."""
    return sha(["v19/review-packet", composition.encoding_hash,
                clause.clause_hash, witness_hash])[:32]


def packet(composition: Composition, clause: Clause, policy: ListPolicy, *,
           seed: int = 0) -> dict[str, Any]:
    """The question about one incompletely covered clause, against one witness."""
    if clause.coverage is not DeterministicCoverage.PARTIAL:
        raise PacketError(
            f"{clause.constraint_id} declares {clause.coverage.value} coverage, so "
            "section 8.6 requires no human review of it; asking anyway would invite "
            "a reviewer to override a deterministic result")
    if clause not in composition.clauses:
        raise PacketError("the clause is not part of the composition")
    built = construct_witness(composition, policy, seed=seed)
    if not built.constructed or built.text is None:
        raise PacketError(
            f"no witness was constructed ({built.reason}), so there is nothing to "
            "review; certification already fails at the witness step")

    # The realisation, with anything naming a policy hash or an identity removed: the
    # reviewer needs the values, not the provenance.
    realisation = {key: value for key, value in clause.parameters.items()
                   if not key.endswith(("_hash", "_id"))
                   and key not in ("relation", "closure")}
    relation = clause.parameters.get("relation")
    if relation is not None:
        realisation["required_order"] = {
            "items": list(relation.items),
            "must_precede": [list(edge) for edge in relation.edges]}

    return {
        "packet_id": _packet_id(composition, clause, built.witness_hash),
        "protocol": "v19",
        "citation": "section 8.6; blinding per section 10.6",
        "question": (
            "Does the response below satisfy the stated requirement AS A READER "
            "WOULD JUDGE IT? The deterministic check and the machine encoding do not "
            "exhaust this requirement's intended meaning; the gap is described under "
            "'not_covered_deterministically'. Judge the requirement, not the "
            "formatting, and answer only about this response."),
        "requirement": _statement_for(clause),
        "parameter_realisation": realisation,
        "not_covered_deterministically": clause.uncovered_semantics,
        "response": built.text,
        "response_hash": built.witness_hash,
        "answer_schema": {
            "reviewer_id": "your identifier, distinct from the other reviewer's",
            "satisfied": "true or false; a boolean, not a word",
            "rationale": "why, in your own words; required",
        },
        "procedure": (
            "Two reviewers answer independently and do not see each other's answer. "
            "If they disagree a third reviewer adjudicates. An unresolved "
            "disagreement fails certification and is not resolved by preferring "
            "either answer (section 8.6)."),
        "caveats": [
            ("The parameter realisation is NOT calibrated: the admissible set and "
             "its distribution are a Stage 5 output (D6). Judge the semantics at "
             "the values shown, not whether the values are the right ones."),
            ("The response was built by a deterministic constructor, not by a "
             "model. It is the witness the deterministic verifiers accepted."),
        ],
    }


def assert_blinded(built: Mapping[str, Any]) -> Mapping[str, Any]:
    """No packet field may name the arm, the role, or any automatic verdict."""
    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key in FORBIDDEN_IN_PACKET:
                    raise PacketError(
                        f"{path}.{key} leaks a field section 10.6 blinds: "
                        f"{FORBIDDEN_IN_PACKET[key]}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, Sequence) and not isinstance(node, str):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(built, "packet")
    text = repr(built)
    for marker in ("PASS", "FAIL", "VIOLATION", "SCORABLE"):
        if marker in text:
            raise PacketError(f"the packet contains {marker!r}, which is a verdict")
    for pair_id in pairs.PAIR_IDS:
        if f"v19:{pair_id}." in text:
            raise PacketError(
                f"the packet names {pair_id}'s constraint identifiers, which carry "
                "the pair and the role")
    return built


def packets_for(composition: Composition, policy: ListPolicy, *,
                seed: int = 0) -> tuple[Mapping[str, Any], ...]:
    """One packet per incompletely covered clause of this composition."""
    needed = set(review_required(composition))
    return tuple(assert_blinded(packet(composition, clause, policy, seed=seed))
                 for clause in composition.clauses
                 if clause.constraint_id in needed)


def bundle(compositions: Sequence[Composition], policy: ListPolicy, *,
           seed: int = 0) -> dict[str, Any]:
    """Every packet the currently enumerable compositions require.

    The mapping from packet back to composition is kept OUT of the packets and in
    this index, so the reviewer's copy stays blinded while the investigator can still
    ingest an answer against the right composition.
    """
    index: list[dict[str, Any]] = []
    out: list[Mapping[str, Any]] = []
    for composition in compositions:
        for built in packets_for(composition, policy, seed=seed):
            out.append(built)
            index.append({"packet_id": built["packet_id"],
                          "composition_id": composition.composition_id,
                          "encoding_hash": composition.encoding_hash,
                          "response_hash": built["response_hash"]})
    return {"protocol": "v19", "citation": "section 8.6",
            "list_policy_hash": policy.policy_hash,
            "text_policy_hash": policy.text.policy_hash,
            "n_packets": len(out),
            "packets": out,
            "unblinding_index": index,
            "note": ("The index is for the investigator, not the reviewers. Send each "
                     "reviewer the 'packets' array only.")}


def outstanding(compositions: Sequence[Composition],
                recorded: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    """Which compositions still have no PASSED review recorded."""
    from dci.v19.certification import ReviewerVerdict, ReviewState, SemanticReview
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
                adjudication=None)
        except Exception:                          # noqa: BLE001 - any malformation
            missing.append(composition.composition_id)
            continue
        if review.state is not ReviewState.HUMAN_REVIEW_PASSED:
            missing.append(composition.composition_id)
    return tuple(missing)


# --------------------------------------------------- the published review set
#: The Pair 1 ordering used by the canonical review compositions.
REVIEW_RELATION_ITEMS = ("alfa", "bravo", "charlie")
REVIEW_RELATION_EDGES = (("alfa", "bravo"), ("bravo", "charlie"))


def canonical_review_compositions(policy: ListPolicy) -> tuple[Composition, ...]:
    """One minimal load-2 focal composition per pair, for the semantic review.

    This lives here rather than in the test that first needed it because
    `docs/v19_stage2_semantic_review_packets.json` is generated FROM it. While the
    definition sat in a test, the published artifact had no producer outside the
    test suite, so it could only be refreshed by hand - and a hand-refreshed
    artifact is exactly what the packet bundle exists to make unnecessary.
    """
    from dci.v19 import encoding as E
    from dci.v19.parsing import OrderingRelation

    relation = OrderingRelation(items=REVIEW_RELATION_ITEMS,
                                edges=REVIEW_RELATION_EDGES)
    return (
        E.encode_composition("p1/review/B", pair_id="p1", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_1.target.constraint_id: {
                                     "n_items": 3, "policy": policy},
                                 pairs.PAIR_1.focal.constraint_id: {
                                     "relation": relation, "policy": policy}}),
        E.encode_composition("p2/review/B", pair_id="p2", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_2.target.constraint_id: {
                                     "mandatory_words": ("alfa", "bravo"),
                                     "policy": policy},
                                 pairs.PAIR_2.focal.constraint_id: {
                                     "policy": policy}}),
        E.encode_composition("p3/review/B", pair_id="p3", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_3.target.constraint_id: {
                                     "n_sentences": 3, "policy": policy},
                                 pairs.PAIR_3.focal.constraint_id: {
                                     "policy": policy}}),
    )
