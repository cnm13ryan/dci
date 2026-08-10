"""The three fixed target-focal pairs and their four reference slots each.

Preregistration section 5 and register rows D2 and D3. The rule *semantics* are
\\FIXED scientific commitments: three pairs, and exactly four independently
admitted references per pair, with primitive effects remaining reference-specific
and no primary averaging or weighting.

Two things are deliberately NOT fixed here and must not be invented:

  * the identities of the four admitted references. Section 14.8 admits them only
    after 24 authored candidates pass every hard gate, the coupling audit, the
    wording audit, the simultaneous calipers and the joint certificate, then
    survive deterministic ranking and an independent validation split. So a
    ReferenceSlot carries a pending identity, and asking for it before Stage 8
    raises rather than returning a placeholder.
  * the canonical wordings and parameter realisations. Section 10.7 makes the
    canonical wording part of the instruction-level treatment, frozen with a
    hash at Stage 7; section 6 freezes each parameter's admissible set and
    distribution at Stage 5. This module declares which fields are parameterised
    and leaves their populations to those stages.

Section 5.1 also says existing registry identifiers "are not treated as
authoritative where they collide or are unverified" and requires "a pre-freeze
identifier reconciliation" assigning unique v19-native constraint identifiers
"without changing the rule semantics". Hence the `v19:` identifiers below, each
recording the v15.1 identifier it descends from for provenance only. The bare
v15.1 ids `A` and `B` were pair-agnostic and could not survive three pairs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from dci.v19.families import N_PAIRS, N_REFERENCES
from dci.v19.identity import ARMS, LOADS, ORDERS, strict_member
from dci.v19.resolution import Resolution, Slot, SlotTable, pending

# Roles an instantiated constraint can occupy. `reference` is a slot occupant,
# not an identity: which constraint fills it is a Stage 8 output.
ROLES = ("target", "focal", "reference", "background", "unrelated_target")

GENERATIVE_SCOPES = ("sentence", "whole_text")


@dataclass(frozen=True)
class VerifierBinding:
    """A deterministic verifier the protocol requires for one rule.

    `callable_name` names the function in `dci.verifiers.rules`. It is empty when
    the verifier has not been built: section 10.9 records that "Pair 1
    bullet-count and transitive-order verifier support remains to be built",
    and pretending otherwise would let an unimplemented measurement into a
    registry that later stages trust.
    """
    verifier_id: str
    callable_name: str = ""
    v15_lineage: str = ""
    span: str = ""

    @property
    def implemented(self) -> bool:
        """Whether the named callable actually resolves today."""
        if not self.callable_name:
            return False
        from dci.verifiers import rules as verifier_rules
        return hasattr(verifier_rules, self.callable_name)

    def resolve(self):
        """The verifier callable, or refuse."""
        if not self.implemented:
            why = ("has no implementation yet" if not self.callable_name
                   else f"names {self.callable_name}, which does not exist")
            raise NotImplementedError(
                f"verifier {self.verifier_id} is declared by the protocol but "
                f"{why}; Stage 2 must build it before any dependent measurement "
                "runs")
        from dci.verifiers import rules as verifier_rules
        return getattr(verifier_rules, self.callable_name)


@dataclass(frozen=True)
class ConstraintRule:
    """One constraint identity whose semantics the preregistration fixes.

    `statement` is the semantic rule, which is fixed. It is NOT the canonical
    wording: section 10.7 freezes one canonical wording plus eleven certified
    paraphrases per identity at Stage 7, and a wording that changes the semantic
    rule is a different intervention rather than a paraphrase.
    """
    constraint_id: str
    role: str
    name: str
    statement: str
    family: str
    generative_scope: str
    verifier: VerifierBinding
    parameters: tuple[str, ...] = ()
    v15_lineage: str = ""
    note: str = ""

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(f"{self.constraint_id}: role {self.role!r} is not "
                             f"one of {ROLES}")
        if self.generative_scope not in GENERATIVE_SCOPES:
            raise ValueError(f"{self.constraint_id}: generative scope "
                             f"{self.generative_scope!r} is not one of "
                             f"{GENERATIVE_SCOPES}")
        if not self.constraint_id.startswith("v19:"):
            raise ValueError(
                f"{self.constraint_id!r} is not a v19-native identifier; "
                "section 5.1 requires unique v19 ids rather than inherited ones")

    @property
    def parameterised(self) -> bool:
        return bool(self.parameters)


@dataclass(frozen=True)
class ReferenceSlot:
    """One of a pair's four admitted-reference positions.

    The arm label is fixed (R1..R4) because it indexes the primitive family; the
    occupant is a Stage 8 output. Section 3.3 is explicit that the comparison
    with R1 is not interchangeable with the comparison with R2, so the slots are
    distinguishable positions rather than an unordered set.
    """
    pair: str
    index: int
    arm: str
    identity: Slot

    def __post_init__(self):
        if not 1 <= self.index <= N_REFERENCES:
            raise ValueError(
                f"{self.pair}: reference index {self.index} is outside 1.."
                f"{N_REFERENCES}; exactly four references per pair is a fixed "
                "scientific commitment (D3)")
        if self.arm != f"R{self.index}":
            raise ValueError(f"{self.pair}: slot {self.index} must occupy arm "
                             f"R{self.index}, not {self.arm!r}")
        if self.identity.resolved:
            raise ValueError(
                f"{self.pair}/{self.arm} already carries a reference identity "
                f"({self.identity.value!r}). Admitted references are a Stage 8 "
                "output; a registry that ships identities has pre-empted the "
                "construction procedure")

    @property
    def admitted(self) -> bool:
        return self.identity.resolved


@dataclass(frozen=True)
class Pair:
    """One target-focal pair: the replacement contrast A+B+S versus A+R_j+S."""
    pair_id: str
    ordinal: int
    target: ConstraintRule
    focal: ConstraintRule
    family_combination: str
    measurement_risk: str
    references: tuple[ReferenceSlot, ...]
    candidate_pool: Slot
    reserve_pool: Slot

    def __post_init__(self):
        if self.target.role != "target" or self.focal.role != "focal":
            raise ValueError(f"{self.pair_id}: target and focal roles are wrong")
        if len(self.references) != N_REFERENCES:
            raise ValueError(
                f"{self.pair_id} declares {len(self.references)} reference "
                f"slots; exactly {N_REFERENCES} is fixed (D3)")
        if [r.arm for r in self.references] != [f"R{i}" for i in
                                                range(1, N_REFERENCES + 1)]:
            raise ValueError(f"{self.pair_id}: reference arms must be "
                             f"R1..R{N_REFERENCES} in order")
        if any(r.pair != self.pair_id for r in self.references):
            raise ValueError(f"{self.pair_id}: a reference slot names another pair")

    @property
    def arms(self) -> tuple[str, ...]:
        """The focal arm plus the four reference arms, in frozen order."""
        return ARMS

    @property
    def admitted_references(self) -> tuple[str, ...]:
        return tuple(r.identity.get() for r in self.references)

    def require_admitted_references(self) -> tuple[str, ...]:
        """The four identities, or a fail-closed report of what is missing."""
        table = SlotTable.of(*(r.identity for r in self.references))
        table.require(*(r.identity.name for r in self.references),
                      what=f"{self.pair_id} reference-dependent analysis")
        return self.admitted_references


def _reference_slots(pair_id: str) -> tuple[ReferenceSlot, ...]:
    return tuple(
        ReferenceSlot(
            pair=pair_id, index=i, arm=f"R{i}",
            identity=pending(
                f"reference.{pair_id}.R{i}", "D12 / section 14.8",
                Resolution.PENDING_EMPIRICAL,
                "Stage 8 simultaneous admission: caliper-normalised ranking of "
                "already-eligible candidates, joint reference-error certificate, "
                "exactly four admitted, then independent validation",
                depends_on=(f"pool.{pair_id}.candidate_references",
                            "exact_epsilon",
                            f"matching.{pair_id}.constants")))
        for i in range(1, N_REFERENCES + 1))


def _candidate_pool(pair_id: str) -> Slot:
    return pending(
        f"pool.{pair_id}.candidate_references", "D8 / section 7.2",
        Resolution.PENDING_CONTENT,
        "24 authored candidates under the frozen rubric, plus at most one blind "
        "tranche of 12 if fewer than 12 survive the hard gates",
        note="fewer than 12 hard-eligible of a maximum 36 emits REFPOOL and the "
             "pair is not frozen")


def _reserve_pool(pair_id: str) -> Slot:
    return pending(
        f"pool.{pair_id}.reserve_items", "section 6.2",
        Resolution.PENDING_CONTENT,
        "prespecified reserve target/focal items, authored before freeze",
        note="a required target or focal item that fails boundary calibration is "
             "replaced only by a prespecified reserve item, and only before freeze")


# --------------------------------------------------------------- the three pairs
#
# Section 5.1's table, verbatim in substance. The descriptive family labels are
# metadata: section 5.5 stresses that because each family combination is
# represented by one selected pair, cross-pair differences cannot support
# family-level inference, so nothing downstream may treat these as a factor.

PAIR_1 = Pair(
    pair_id="p1", ordinal=1,
    target=ConstraintRule(
        constraint_id="v19:p1.target.exact_bullet_count", role="target",
        name="Exact bullet-list item count",
        statement="Produce exactly N bullet-list items.",
        family="format", generative_scope="whole_text",
        parameters=("n_items",),
        verifier=VerifierBinding(
            verifier_id="v19:verifier.exact_bullet_count",
            callable_name="",                     # Stage 2 must build it
            span="list_segmentation"),
        note="no v15.1 lineage: bullet-count verifier support is new in v19"),
    focal=ConstraintRule(
        constraint_id="v19:p1.focal.transitive_order", role="focal",
        name="Transitive ordering of items",
        statement="Place the items in the correct transitive order.",
        family="relational/order", generative_scope="whole_text",
        parameters=("ordering_depth",),
        verifier=VerifierBinding(
            verifier_id="v19:verifier.transitive_order",
            callable_name="",                     # Stage 2 must build it
            span="list_segmentation+relation_evaluation"),
        note="no v15.1 lineage: transitive-order verifier support is new in v19"),
    family_combination="relational/order -> format",
    measurement_risk=(
        "verifier coupling: both the count and the ordering verifier may parse "
        "the same list representation, so a malformed list could change both "
        "verdicts through shared parsing rather than genuine interference "
        "(section 5.2)"),
    references=_reference_slots("p1"),
    candidate_pool=_candidate_pool("p1"),
    reserve_pool=_reserve_pool("p1"))

PAIR_2 = Pair(
    pair_id="p2", ordinal=2,
    target=ConstraintRule(
        constraint_id="v19:p2.target.mandatory_words", role="target",
        name="Mandatory word inclusion",
        statement="Include all specified mandatory words.",
        family="lexical inclusion", generative_scope="whole_text",
        parameters=("mandatory_word_count", "mandatory_word_set"),
        v15_lineage="U_REQ",
        verifier=VerifierBinding(
            verifier_id="v19:verifier.require_word_set",
            callable_name="v_require_word_set", v15_lineage="U_REQ",
            span="word_normalisation")),
    focal=ConstraintRule(
        constraint_id="v19:p2.focal.all_words_unique", role="focal",
        name="All words unique",
        statement=("Every word in the final answer must be unique under the "
                   "frozen normalisation and tokenisation-for-verification rule."),
        family="word-level/global uniqueness", generative_scope="whole_text",
        v15_lineage="L_UNIQ",
        verifier=VerifierBinding(
            verifier_id="v19:verifier.unique_words",
            callable_name="v_unique_words", v15_lineage="L_UNIQ",
            span="word_normalisation"),
        note="unparameterised: the rule quantifies over every word, and section "
             "6.1 forbids constructing a scalar severity coordinate to make "
             "whole-response uniqueness commensurable with a count"),
    family_combination="word-level/global uniqueness -> lexical inclusion",
    measurement_risk=(
        "logical incompatibility and floor effects: a parameter realisation that "
        "forces repeated mandatory tokens is outside the DCI estimand because the "
        "composition is impossible, and a focal regime that is almost never "
        "satisfiable is uninformative as a manipulation (section 5.3)"),
    references=_reference_slots("p2"),
    candidate_pool=_candidate_pool("p2"),
    reserve_pool=_reserve_pool("p2"))

PAIR_3 = Pair(
    pair_id="p3", ordinal=3,
    target=ConstraintRule(
        constraint_id="v19:p3.target.exact_sentence_count", role="target",
        name="Exact sentence count",
        statement="Produce exactly N sentences.",
        family="structural sentence count", generative_scope="sentence",
        parameters=("n_sentences",),
        v15_lineage="A / S2",
        verifier=VerifierBinding(
            verifier_id="v19:verifier.exact_sentence_count",
            callable_name="v_exact_sentence_count", v15_lineage="A / S2",
            span="sentence_segmentation")),
    focal=ConstraintRule(
        constraint_id="v19:p3.focal.increasing_lengths", role="focal",
        name="Increasing sentence lengths",
        statement=("Successive sentence lengths must increase monotonically "
                   "under the frozen sentence segmentation and length unit."),
        family="ordering", generative_scope="sentence",
        v15_lineage="B / O1",
        verifier=VerifierBinding(
            verifier_id="v19:verifier.increasing_lengths",
            callable_name="v_increasing_lengths", v15_lineage="B / O1",
            span="sentence_segmentation+word_counts"),
        note="unparameterised: monotone increase is defined by the frozen length "
             "unit rather than by a threshold"),
    family_combination="ordering -> structural sentence count",
    measurement_risk=(
        "shared sentence segmentation: boundary errors and conversational "
        "preambles can affect both the target and the focal verdict, so "
        "pair-specific coupling audits remain mandatory (section 5.4)"),
    references=_reference_slots("p3"),
    candidate_pool=_candidate_pool("p3"),
    reserve_pool=_reserve_pool("p3"))

PAIRS: tuple[Pair, ...] = (PAIR_1, PAIR_2, PAIR_3)
PAIR_IDS: tuple[str, ...] = tuple(p.pair_id for p in PAIRS)


def pair(pair_id: str) -> Pair:
    for candidate in PAIRS:
        if candidate.pair_id == pair_id:
            return candidate
    raise KeyError(f"{pair_id!r} is not a v19 pair; the three fixed pairs are "
                   f"{PAIR_IDS}")


def rules() -> tuple[ConstraintRule, ...]:
    """Every target and focal rule across the three pairs, in frozen order."""
    return tuple(rule for p in PAIRS for rule in (p.target, p.focal))


def verifiers() -> tuple[VerifierBinding, tuple[str, ...]]:
    """Every declared verifier and the constraint ids that require it."""
    seen: dict[str, list[str]] = {}
    bindings: dict[str, VerifierBinding] = {}
    for rule in rules():
        bindings[rule.verifier.verifier_id] = rule.verifier
        seen.setdefault(rule.verifier.verifier_id, []).append(rule.constraint_id)
    return tuple((bindings[v], tuple(seen[v])) for v in bindings)  # type: ignore


def rule_definitions() -> dict[str, dict[str, object]]:
    """The complete fixed rule semantics of all three pairs, for hashing.

    Section 14.1 freezes the three rule definitions and D2 makes them a fixed
    scientific commitment, but nothing hashed them: a changed statement, verifier
    binding or parameter name altered no fingerprint anywhere in the registry.
    Excludes the descriptive prose - `measurement_risk` and `note` - because those
    are commentary rather than the frozen rule, and including them would make
    editorial rewording look like a protocol change.
    """
    def described(rule: ConstraintRule) -> dict[str, object]:
        return {"constraint_id": rule.constraint_id, "role": rule.role,
                "statement": rule.statement, "family": rule.family,
                "generative_scope": rule.generative_scope,
                "parameters": list(rule.parameters),
                "verifier_id": rule.verifier.verifier_id,
                "verifier_callable": rule.verifier.callable_name,
                "verifier_span": rule.verifier.span,
                "v15_lineage": rule.v15_lineage}

    return {p.pair_id: {"ordinal": p.ordinal,
                        "family_combination": p.family_combination,
                        "target": described(p.target),
                        "focal": described(p.focal),
                        "reference_arms": [r.arm for r in p.references]}
            for p in PAIRS}


def unimplemented_verifiers() -> tuple[VerifierBinding, ...]:
    """Declared verifiers with no implementation, in frozen pair order.

    Section 10.9's readiness snapshot expects exactly the two Pair 1 verifiers
    here until Stage 2 builds them. Reporting this rather than asserting it keeps
    the registry honest as that work lands.
    """
    return tuple(rule.verifier for rule in rules()
                 if not rule.verifier.implemented)


def assert_pair_structure() -> None:
    """The fixed scientific commitments of section 5 and rows D2, D3, D5."""
    if len(PAIRS) != N_PAIRS:
        raise ValueError(f"{len(PAIRS)} pairs declared; {N_PAIRS} is fixed (D2)")
    if len({p.pair_id for p in PAIRS}) != N_PAIRS:
        raise ValueError("pair identifiers collide")
    if [p.ordinal for p in PAIRS] != list(range(1, N_PAIRS + 1)):
        raise ValueError("pair ordinals must be 1..3")
    ids = [rule.constraint_id for rule in rules()]
    if len(set(ids)) != len(ids):
        raise ValueError(f"v19 constraint identifiers collide: {ids}")
    for p in PAIRS:
        if len(p.references) != N_REFERENCES:
            raise ValueError(f"{p.pair_id} does not have {N_REFERENCES} slots")
        if p.target.constraint_id == p.focal.constraint_id:
            raise ValueError(f"{p.pair_id}: target and focal are the same rule")


def declared_slots() -> SlotTable:
    """Every pending pair-level output: reference identities and pools."""
    slots: list[Slot] = []
    for p in PAIRS:
        slots.append(p.candidate_pool)
        slots.append(p.reserve_pool)
        slots.extend(r.identity for r in p.references)
    return SlotTable(slots=tuple(slots))


def assert_load(load: int) -> int:
    """Only the preregistered paired loads exist (D5).

    Delegates to the same strict check the identity hierarchy uses, so the
    registry and cell_id cannot disagree about what counts as load 2.
    """
    return strict_member(load, LOADS, "load")


def assert_order(order: str) -> str:
    """Only the two preregistered presentation orders exist (D5).

    o_A places the target before the added-slot occupant; o_Q reverses those two
    positions. No primary analysis averages them (section 4.2).
    """
    return strict_member(order, ORDERS, "presentation order")


def assert_arm(arm: str) -> str:
    """The focal arm plus exactly four reference arms."""
    return strict_member(arm, ARMS, "arm")


def cells(n_retained_budgets: Optional[Sequence[str]] = None):
    """Every (pair, load, order, arm) combination the design crosses.

    Budget is deliberately not defaulted: the retained set is a Stage 4 output,
    so a caller wanting the full cell list must supply it and cannot silently
    enumerate against an invented grid.
    """
    if n_retained_budgets is None:
        raise ValueError(
            "the retained budget set B_ret is a Stage 4 output (D25); pass it "
            "explicitly rather than enumerating cells against an assumed grid")
    for p in PAIRS:
        for budget in n_retained_budgets:
            for load in LOADS:
                for order in ORDERS:
                    for arm in ARMS:
                        yield (p.pair_id, budget, load, order, arm)
