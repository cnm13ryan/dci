"""Deterministic v19 verifiers: one contract, six constraints, hashed semantics.

Section 10.1 records three *orthogonal* things about a delivered final-answer
segment, and the inherited code records them in one field:

  * the primary constraint verdict, `PASS` or `FAIL`, and nothing else;
  * a generation/measurement state, one of `SCORABLE`, `UNPARSEABLE`,
    `TRUNCATED`, `EMPTY`, `REFUSAL`;
  * where the constraint admits a richer description, a secondary compliance
    field `FULL`, `PARTIAL`, `VIOLATION`, with "for an exact target, PARTIAL
    implies primary target failure".

`dci.verifiers.rules.OutcomeStatus` is `full | partial | violation | unscorable`,
which merges the second and third. `unscorable` is not a compliance level; it is a
statement about parsing. So every verifier here returns a `VerifierOutcome` whose
fields are separate, and the Pair 2/3 verifiers are thin audited adapters over the
inherited implementations rather than rewrites.

A fourth thing must also stay separate, from the section 10.8 distinction between
behavioural outcomes and technical failures: whether scoring *happened*. A missing
parameter and a verifier exception are not behavioural failures, and section 10.1
is explicit that "a technical failure before a final-answer segment is delivered
has no fabricated behavioural verdict". `Scoring` carries that, and `verdict` is
`None` unless `scoring is Scoring.SCORED`, enforced in `__post_init__` - so a
crash cannot arrive downstream wearing a `FAIL`.

WHAT IS HASHED
--------------
Appendix I requires "invariant model/tokenizer/template/controller/decoder/
runtime/verifier/inference hashes" across the run, and section 14.2 permits Pair
2/3 reuse "only after hash/semantic audit". Two hashes therefore exist per
verifier and both are load-bearing:

  * `spec_hash` covers the declared semantics, INCLUDING the literal regular
    expressions the inherited implementation segments with. Editing
    `rules.WORD_PATTERN` changes the measurement, so it changes this hash.
  * `implementation_hash` covers the source of the callables actually executed,
    the inherited ones included. Editing a function body changes this hash even if
    the declared semantics are unchanged.

Neither is frozen here. Computing a hash is not certifying an artifact: the
`verifiers.bundle_hash` slot stays pending until Stage 2 certification passes, and
for Pair 1 that is blocked on a list policy the preregistration does not fix.
"""
from __future__ import annotations

import enum
import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import field_roles, pairs
from dci.v19.parsing import (
    ListPolicy,
    OrderingRelation,
    match_items_to_labels,
    parse_list,
)


class Verdict(str, enum.Enum):
    """Section 10.1's primary constraint field. Two values, deliberately."""

    PASS = "PASS"
    FAIL = "FAIL"


class GenerationState(str, enum.Enum):
    """Section 10.1's orthogonal generation/measurement state."""

    SCORABLE = "SCORABLE"
    UNPARSEABLE = "UNPARSEABLE"
    TRUNCATED = "TRUNCATED"
    EMPTY = "EMPTY"
    REFUSAL = "REFUSAL"


class Compliance(str, enum.Enum):
    """Section 10.1's secondary compliance description."""

    FULL = "FULL"
    PARTIAL = "PARTIAL"
    VIOLATION = "VIOLATION"


class Scoring(str, enum.Enum):
    """Whether deterministic scoring happened at all.

    Not a behavioural field. `MISSING_METADATA` means a required parameter
    realisation was absent; `VERIFIER_ERROR` means the implementation raised.
    Section 10.8 repairs the latter by rerunning verification on the stored bytes,
    never by regenerating model output, so it must be distinguishable.
    """

    SCORED = "SCORED"
    MISSING_METADATA = "MISSING_METADATA"
    VERIFIER_ERROR = "VERIFIER_ERROR"


# States that mean the caller already knows scoring cannot describe the segment
# behaviourally in the ordinary way. The verifier may narrow SCORABLE to EMPTY or
# UNPARSEABLE; it may never invent TRUNCATED or REFUSAL, because neither is
# recoverable from the text - one comes from the controller's finish reason and the
# other is a judgement.
CALLER_SUPPLIED_STATES = (GenerationState.TRUNCATED, GenerationState.REFUSAL)


class VerifierContractError(ValueError):
    """An outcome that cannot be a faithful record under section 10.1."""


@dataclass(frozen=True)
class VerifierSpec:
    """The frozen semantics of one deterministic verifier."""
    verifier_id: str
    constraint_id: str
    statement: str
    rule: str
    citation: str
    span: str
    parameters: tuple[str, ...]
    segmentation: Mapping[str, Any]
    inherited_from: str = ""
    audit: str = ""

    def __post_init__(self):
        for name in ("verifier_id", "constraint_id", "statement", "rule",
                     "citation", "span"):
            if not getattr(self, name):
                raise ValueError(f"{self.verifier_id or '<unnamed>'}: {name} is "
                                 "required; an unattributed verifier cannot be "
                                 "audited against the protocol")
        if not self.verifier_id.startswith("v19:"):
            raise ValueError(f"{self.verifier_id!r} is not a v19-native verifier "
                             "identifier (section 5.1)")

    def state(self) -> dict[str, Any]:
        """The canonical serialisation. `audit` is prose and stays out."""
        return {"verifier_id": self.verifier_id,
                "constraint_id": self.constraint_id,
                "statement": self.statement, "rule": self.rule,
                "span": self.span, "parameters": list(self.parameters),
                "segmentation": dict(self.segmentation),
                "inherited_from": self.inherited_from}

    @property
    def spec_hash(self) -> str:
        return sha(["v19/verifier-spec", self.state()])


@dataclass(frozen=True)
class VerifierOutcome:
    """One deterministic measurement, with its four fields kept apart."""
    verifier_id: str
    constraint_id: str
    spec_hash: str
    parameters: Mapping[str, Any]
    scoring: Scoring
    verdict: Verdict | None
    generation_state: GenerationState
    compliance: Compliance | None
    reason: str
    evidence: Mapping[str, Any]

    def __post_init__(self):
        if not isinstance(self.scoring, Scoring):
            raise VerifierContractError(f"{self.scoring!r} is not a Scoring")
        if not isinstance(self.generation_state, GenerationState):
            raise VerifierContractError(
                f"{self.generation_state!r} is not a GenerationState")
        scored = self.scoring is Scoring.SCORED
        if scored and not isinstance(self.verdict, Verdict):
            raise VerifierContractError(
                f"{self.verifier_id}: scoring succeeded but the verdict is "
                f"{self.verdict!r}; section 10.1 requires PASS or FAIL")
        if not scored and self.verdict is not None:
            raise VerifierContractError(
                f"{self.verifier_id}: scoring is {self.scoring.value} yet a "
                f"verdict {self.verdict!r} is recorded. A technical scoring "
                "failure must never arrive as a behavioural verdict "
                "(sections 10.1, 10.8)")
        if not scored and self.compliance is not None:
            raise VerifierContractError(
                f"{self.verifier_id}: scoring is {self.scoring.value} yet a "
                f"compliance level is recorded")
        if self.compliance is not None:
            if not isinstance(self.compliance, Compliance):
                raise VerifierContractError(
                    f"{self.compliance!r} is not a Compliance")
            full = self.compliance is Compliance.FULL
            if full is not (self.verdict is Verdict.PASS):
                raise VerifierContractError(
                    f"{self.verifier_id}: compliance {self.compliance.value} "
                    f"contradicts verdict {self.verdict.value if self.verdict else None}. "
                    "Section 10.1: for an exact target PARTIAL implies primary "
                    "failure, so FULL and PASS agree or the record is wrong")
        if not self.reason:
            raise VerifierContractError(
                f"{self.verifier_id}: every outcome states why, so a verdict can "
                "be re-derived from the record rather than re-run")

    @property
    def scored(self) -> bool:
        return self.scoring is Scoring.SCORED

    @property
    def f_a(self) -> int:
        """The section 11.1 failure indicator: 1 on FAIL, 0 on PASS.

        Refuses when scoring did not happen. Section 10.1 forbids a fabricated
        behavioural verdict, and returning 1 here would be exactly that.
        """
        if not self.scored:
            raise VerifierContractError(
                f"{self.verifier_id} did not score this segment "
                f"({self.scoring.value}: {self.reason}); it has no behavioural "
                "failure indicator. Rerun verification on the stored bytes "
                "(section 10.8) rather than coercing a value")
        return int(self.verdict is Verdict.FAIL)

    def describe(self) -> dict[str, Any]:
        return {"verifier_id": self.verifier_id,
                "constraint_id": self.constraint_id,
                "spec_hash": self.spec_hash,
                "parameters": dict(self.parameters),
                "scoring": self.scoring.value,
                "verdict": self.verdict.value if self.verdict else None,
                "generation_state": self.generation_state.value,
                "compliance": self.compliance.value if self.compliance else None,
                "reason": self.reason, "evidence": dict(self.evidence)}


def assert_evidence_is_diagnostic(outcome: VerifierOutcome) -> VerifierOutcome:
    """Verifier evidence may not name a field a primary formula could consume.

    Section 11.8 gives every analysis field one pre-frozen role and rejects
    post-treatment and diagnostic fields as covariates, weights, filters, matching
    coordinates or denominator definitions. Structured verifier evidence is
    diagnostic by construction. The risk is not that a diagnostic key is
    misclassified but that evidence starts carrying a key that *is* legitimately
    primary - `arm`, `load`, `target_verdict` - after which a formula can consume
    the evidence blob and pick up a primary field with it.
    """
    laundered = []
    for key in outcome.evidence:
        try:
            role = field_roles.role_of(key)
        except field_roles.FieldRoleViolation:
            continue                       # not an analysis field at all: fine
        primary = [use for use in field_roles.PRIMARY_USES + ("outcome",)
                   if field_roles.permits(role, use)]
        if primary:
            laundered.append(f"{key!r} (role {role}, permitted as "
                             f"{', '.join(primary)})")
    if laundered:
        raise field_roles.FieldRoleViolation(
            f"{outcome.verifier_id} put {len(laundered)} primary-usable field(s) "
            f"into diagnostic verifier evidence: {'; '.join(laundered)}. Evidence "
            "is diagnostic only (section 11.8); a primary field reaching analysis "
            "through an evidence blob has bypassed the role registry")
    return outcome


# ------------------------------------------------- the inherited segmentation
#
# Read off the inherited module at import so a change there moves the spec hash.
# Section 14.2 permits reuse of the Pair 2/3 code "only after hash/semantic
# audit"; the hash half of that is meaningless if it covers a label rather than
# the regular expressions that decide what a word and a sentence are.

def inherited_segmentation() -> dict[str, str]:
    from dci.verifiers import rules
    return {"word_pattern": rules.WORD_PATTERN.pattern,
            "sentence_boundary": rules.SENTENCE_BOUNDARY.pattern,
            "list_marker_stripped_before_sentences": rules.LIST_MARKER.pattern,
            "whitespace_collapse": r"[^\S\n]+",
            "word_case_folding": "str.lower on each token"}


def implementation_hash(*callables: Callable) -> str:
    """Hash of the source actually executed, inherited functions included."""
    return sha(["v19/verifier-implementation",
                [inspect.getsource(fn) for fn in callables]])


# ----------------------------------------------------------------- Pair 1: new

def _p1_count_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.exact_bullet_count",
        constraint_id=pairs.PAIR_1.target.constraint_id,
        statement=pairs.PAIR_1.target.statement,
        rule=("PASS iff the number of list items parsed from the final-answer "
              "segment under the declared list policy equals n_items exactly"),
        citation="sections 4.1, 4.2, 14.2",
        span="list_segmentation",
        parameters=("n_items",),
        segmentation={"list_policy": policy.state(),
                      "list_policy_hash": policy.policy_hash},
        audit="new in v19; section 10.9 records that Pair 1 support had to be built")


def _p1_order_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.transitive_order",
        constraint_id=pairs.PAIR_1.focal.constraint_id,
        statement=pairs.PAIR_1.focal.statement,
        rule=("PASS iff every declared item is identified exactly once among the "
              "parsed list items and every pair in the transitive closure of the "
              "declared precedence relation appears in that order"),
        citation="sections 4.1, 4.2, 14.2",
        span="list_segmentation+relation_evaluation",
        parameters=("relation",),
        segmentation={"list_policy": policy.state(),
                      "list_policy_hash": policy.policy_hash},
        audit="new in v19; shares list_segmentation with the target verifier, "
              "which is the coupling section 4.2 names")


def _delivered(text: Any, state: GenerationState) -> GenerationState:
    """Narrow SCORABLE to EMPTY when nothing was delivered; never widen."""
    if state in CALLER_SUPPLIED_STATES:
        return state
    return GenerationState.EMPTY if not str(text or "").strip() else state


def verify_exact_bullet_count(text: Any, *, n_items: Any, policy: ListPolicy,
                              delivered_state: GenerationState
                              = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 1 target: exactly `n_items` list items under an explicit policy."""
    spec = _p1_count_spec(policy)
    if isinstance(n_items, bool) or not isinstance(n_items, int) or n_items < 1:
        return VerifierOutcome(
            verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
            spec_hash=spec.spec_hash, parameters={"n_items": n_items},
            scoring=Scoring.MISSING_METADATA, verdict=None,
            generation_state=_delivered(text, delivered_state), compliance=None,
            reason=(f"n_items={n_items!r} is not a positive integer, so the "
                    "target has no parameter realisation to verify against"),
            evidence={})
    parsed = parse_list(text, policy)
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not parsed.items and not parsed.text.strip():
        state = GenerationState.EMPTY
    observed = parsed.count
    passed = observed == n_items
    return assert_evidence_is_diagnostic(VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash, parameters={"n_items": n_items},
        scoring=Scoring.SCORED,
        verdict=Verdict.PASS if passed else Verdict.FAIL,
        generation_state=state,
        compliance=Compliance.FULL if passed else (
            Compliance.PARTIAL if observed else Compliance.VIOLATION),
        reason=(f"observed {observed} list item(s), required exactly {n_items}"),
        evidence={"expected_count": n_items, "observed_count": observed,
                  "parse": parsed.describe()}))


def verify_transitive_order(text: Any, *, relation: OrderingRelation,
                            policy: ListPolicy,
                            delivered_state: GenerationState
                            = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 1 focal: the declared items appear in a valid linear extension.

    Any arrangement consistent with the relation passes. A partial order can have
    several, and comparing against one expected sequence would fail valid answers
    - which is why the check is over the relation, not over a string.
    """
    spec = _p1_order_spec(policy)
    if not isinstance(relation, OrderingRelation):
        return VerifierOutcome(
            verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
            spec_hash=spec.spec_hash, parameters={},
            scoring=Scoring.MISSING_METADATA, verdict=None,
            generation_state=_delivered(text, delivered_state), compliance=None,
            reason=(f"the instantiated ordering relation is {relation!r}, not an "
                    "OrderingRelation; the focal parameter realisation is absent"),
            evidence={})
    parsed = parse_list(text, policy)
    identification = match_items_to_labels(parsed, relation, policy)
    state = _delivered(text, delivered_state)
    closure = relation.closure()

    structural: list[str] = []
    if identification["missing_labels"]:
        structural.append(
            f"item(s) {identification['missing_labels']} never appear")
    if identification["duplicated_labels"]:
        structural.append(
            f"item(s) {identification['duplicated_labels']} appear more than once")
    if identification["ambiguous"]:
        structural.append(
            f"{len(identification['ambiguous'])} list item(s) match more than one "
            "declared item, so their identity is not determined")
    extra = identification["unmatched_ordinals"]
    if extra:
        structural.append(f"{len(extra)} list item(s) match no declared item")

    position = {}
    for index, label in enumerate(identification["sequence"]):
        if label is not None and label not in position:
            position[label] = index
    violated = [[before, after] for before, after in closure
                if before in position and after in position
                and position[before] > position[after]]

    passed = not structural and not violated
    if violated:
        reason = (f"{len(violated)} required precedence(s) violated, first "
                  f"{violated[0][0]} before {violated[0][1]}")
    elif structural:
        reason = "; ".join(structural)
    else:
        reason = (f"all {len(closure)} required precedence(s) hold in the "
                  f"observed arrangement")
    return assert_evidence_is_diagnostic(VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash,
        parameters={"relation_hash": relation.relation_hash,
                    "declared_items": list(relation.items),
                    "declared_edges": [list(e) for e in relation.edges]},
        scoring=Scoring.SCORED,
        verdict=Verdict.PASS if passed else Verdict.FAIL,
        generation_state=state,
        compliance=Compliance.FULL if passed else (
            Compliance.VIOLATION if structural else Compliance.PARTIAL),
        reason=reason,
        evidence={"identification": identification,
                  "required_closure": [list(e) for e in closure],
                  "violated_precedences": violated,
                  "structural_problems": structural,
                  "chain_depth": relation.chain_depth,
                  "parse": parsed.describe()}))


# -------------------------------------------------- Pairs 2 and 3: adapted

def _inherited_outcome(spec: VerifierSpec, parameters: Mapping[str, Any],
                       result, text: Any, delivered_state: GenerationState,
                       exact: bool) -> VerifierOutcome:
    """Map one `rules.VerificationResult` onto section 10.1's separate fields.

    The inherited `binary_pass` is authoritative for the verdict: section 10.1
    says "an exact requirement that cannot be demonstrated as satisfied receives
    FAIL", and `_unscorable` already returns `binary_pass=0`. What changes is that
    `unscorable` moves out of the compliance field, where it never belonged, and
    becomes a generation state.

    If `binary_pass` and `status` disagree - which the inherited scoring should
    make impossible - that is a verifier defect and is reported as
    VERIFIER_ERROR rather than resolved by preferring one of them.
    """
    state = _delivered(text, delivered_state)
    if result.status == "unscorable":
        if state not in CALLER_SUPPLIED_STATES and state is not GenerationState.EMPTY:
            state = GenerationState.UNPARSEABLE
        if result.binary_pass:
            return _defect(spec, parameters, state,
                           "the inherited verifier reported unscorable with "
                           "binary_pass=1, which cannot both hold", result)
        return assert_evidence_is_diagnostic(VerifierOutcome(
            verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
            spec_hash=spec.spec_hash, parameters=dict(parameters),
            scoring=Scoring.SCORED, verdict=Verdict.FAIL,
            generation_state=state, compliance=Compliance.VIOLATION,
            reason=("the segment yielded nothing the frozen span could parse, so "
                    "the requirement cannot be demonstrated as satisfied "
                    "(section 10.1)"),
            evidence={"inherited_status": result.status,
                      "inherited_score": float(result.continuous_score),
                      "detail": dict(result.detail)}))

    passed = bool(result.binary_pass)
    if passed is not (result.status == "full"):
        return _defect(spec, parameters, state,
                       f"the inherited verifier reported status "
                       f"{result.status!r} with binary_pass={result.binary_pass}, "
                       "so its own verdict and compliance disagree", result)
    compliance = {"full": Compliance.FULL, "partial": Compliance.PARTIAL,
                  "violation": Compliance.VIOLATION}[result.status]
    if exact and compliance is Compliance.PARTIAL and passed:
        return _defect(spec, parameters, state,
                       "PARTIAL on an exact requirement must imply failure "
                       "(section 10.1)", result)
    return assert_evidence_is_diagnostic(VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash, parameters=dict(parameters),
        scoring=Scoring.SCORED,
        verdict=Verdict.PASS if passed else Verdict.FAIL,
        generation_state=state, compliance=compliance,
        reason=f"inherited verifier returned {result.status}",
        evidence={"inherited_status": result.status,
                  "inherited_score": float(result.continuous_score),
                  "detail": dict(result.detail)}))


def _defect(spec: VerifierSpec, parameters: Mapping[str, Any],
            state: GenerationState, why: str, result) -> VerifierOutcome:
    return VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash, parameters=dict(parameters),
        scoring=Scoring.VERIFIER_ERROR, verdict=None, generation_state=state,
        compliance=None,
        reason=f"verifier defect: {why}",
        evidence={"inherited_status": result.status,
                  "inherited_binary_pass": int(result.binary_pass),
                  "detail": dict(result.detail)})


def _inherited_spec(verifier_id: str, rule_side: str, rule: str, span: str,
                    parameters: tuple[str, ...], audit: str) -> VerifierSpec:
    pair_id, side = rule_side.split(".")
    rule_object = getattr(pairs.pair(pair_id), side)
    return VerifierSpec(
        verifier_id=verifier_id, constraint_id=rule_object.constraint_id,
        statement=rule_object.statement, rule=rule,
        citation="sections 4.1, 10.1, 14.2", span=span, parameters=parameters,
        segmentation=inherited_segmentation(),
        inherited_from=rule_object.verifier.v15_lineage, audit=audit)


P2_TARGET_SPEC = _inherited_spec(
    "v19:verifier.require_word_set", "p2.target",
    rule=("PASS iff every mandatory word occurs at least once among the "
          "case-folded ASCII word tokens of the final-answer segment"),
    span="word_normalisation", parameters=("mandatory_word_set",),
    audit=("reused unchanged in verdict; the ASCII-only word pattern means a "
           "mandatory word containing a non-ASCII letter can never be matched, "
           "which under section 4.3 makes that parameter realisation an "
           "impossible composition outside the estimand rather than a failing "
           "answer"))

P2_FOCAL_SPEC = _inherited_spec(
    "v19:verifier.unique_words", "p2.focal",
    rule=("PASS iff the case-folded ASCII word tokens of the final-answer "
          "segment are pairwise distinct"),
    span="word_normalisation", parameters=(),
    audit=("reused unchanged in verdict; the word pattern matches only "
           "[A-Za-z0-9] runs and the whitespace collapse does not remove U+200B, "
           "so a zero-width space or a homoglyph splits a repeated word into "
           "tokens that are distinct - section 10.6 names both as required audit "
           "material"))

P3_TARGET_SPEC = _inherited_spec(
    "v19:verifier.exact_sentence_count", "p3.target",
    rule=("PASS iff the number of segments produced by the frozen sentence "
          "segmentation equals n_sentences exactly"),
    span="sentence_segmentation", parameters=("n_sentences",),
    audit=("reused unchanged in verdict; the frozen segmentation strips list "
           "markers and treats each line as a segment, so a bullet list of N "
           "lines scores as exactly N sentences - the shared-segmentation risk "
           "section 4.4 names, and the span Pair 1 also reads"))

P3_FOCAL_SPEC = _inherited_spec(
    "v19:verifier.increasing_lengths", "p3.focal",
    rule=("PASS iff successive segment lengths, counted in ASCII word tokens, "
          "strictly increase"),
    span="sentence_segmentation+word_counts", parameters=(),
    audit=("reused unchanged in verdict; strict increase, not non-decreasing - "
           "`v_nondecreasing_lengths` exists in the inherited module and is a "
           "different rule that must not be substituted"))


def verify_mandatory_words(text: Any, *, mandatory_words: Any,
                           delivered_state: GenerationState
                           = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 2 target, over the audited inherited implementation."""
    from dci.verifiers import rules
    spec = P2_TARGET_SPEC
    words = tuple(mandatory_words) if isinstance(
        mandatory_words, (list, tuple)) else None
    if not words or any(not isinstance(w, str) or not w for w in words):
        return VerifierOutcome(
            verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
            spec_hash=spec.spec_hash,
            parameters={"mandatory_word_set": mandatory_words},
            scoring=Scoring.MISSING_METADATA, verdict=None,
            generation_state=_delivered(text, delivered_state), compliance=None,
            reason=(f"mandatory_words={mandatory_words!r} is not a non-empty "
                    "sequence of words, so the target has no realisation"),
            evidence={})
    return _inherited_outcome(
        spec, {"mandatory_word_set": list(words)},
        rules.v_require_word_set(text, words), text, delivered_state, exact=False)


def verify_all_words_unique(text: Any, *, delivered_state: GenerationState
                            = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 2 focal, over the audited inherited implementation."""
    from dci.verifiers import rules
    return _inherited_outcome(P2_FOCAL_SPEC, {}, rules.v_unique_words(text),
                              text, delivered_state, exact=False)


def verify_exact_sentence_count(text: Any, *, n_sentences: Any,
                                delivered_state: GenerationState
                                = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 3 target, over the audited inherited implementation."""
    from dci.verifiers import rules
    spec = P3_TARGET_SPEC
    if (isinstance(n_sentences, bool) or not isinstance(n_sentences, int)
            or n_sentences < 1):
        return VerifierOutcome(
            verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
            spec_hash=spec.spec_hash, parameters={"n_sentences": n_sentences},
            scoring=Scoring.MISSING_METADATA, verdict=None,
            generation_state=_delivered(text, delivered_state), compliance=None,
            reason=(f"n_sentences={n_sentences!r} is not a positive integer, so "
                    "the target has no parameter realisation"),
            evidence={})
    return _inherited_outcome(
        spec, {"n_sentences": n_sentences},
        rules.v_exact_sentence_count(text, n_sentences), text, delivered_state,
        exact=True)


def verify_increasing_lengths(text: Any, *, delivered_state: GenerationState
                              = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 3 focal, over the audited inherited implementation."""
    from dci.verifiers import rules
    return _inherited_outcome(P3_FOCAL_SPEC, {},
                              rules.v_increasing_lengths(text), text,
                              delivered_state, exact=False)


# ------------------------------------------------------------- the bundle

@dataclass(frozen=True)
class Verifier:
    """One constraint's deterministic measurement, spec and callable together."""
    spec: VerifierSpec
    run: Callable[..., VerifierOutcome]
    implementation: tuple[Callable, ...]
    status: str                      # "new" or "inherited_audited"

    @property
    def implementation_hash(self) -> str:
        return implementation_hash(*self.implementation)

    def invoke(self, text: Any, **kwargs: Any) -> VerifierOutcome:
        """Run the verifier, turning an exception into VERIFIER_ERROR.

        A crash is a technical scoring failure (section 10.8), never a
        behavioural FAIL, so it is caught at exactly one place instead of at
        every call site where it could be forgotten.
        """
        state = kwargs.get("delivered_state", GenerationState.SCORABLE)
        try:
            return self.run(text, **kwargs)
        except Exception as error:                     # noqa: BLE001 - deliberate
            return VerifierOutcome(
                verifier_id=self.spec.verifier_id,
                constraint_id=self.spec.constraint_id,
                spec_hash=self.spec.spec_hash,
                parameters={k: v for k, v in kwargs.items()
                            if k != "delivered_state"},
                scoring=Scoring.VERIFIER_ERROR, verdict=None,
                generation_state=state if isinstance(state, GenerationState)
                else GenerationState.SCORABLE,
                compliance=None,
                reason=(f"{type(error).__name__} while scoring: {error}. This is "
                        "a technical scoring failure; rerun verification on the "
                        "stored bytes (section 10.8)"),
                evidence={})


def _pair_one_verifiers(policy: ListPolicy) -> dict[str, Verifier]:
    return {
        pairs.PAIR_1.target.constraint_id: Verifier(
            spec=_p1_count_spec(policy),
            run=lambda text, **kw: verify_exact_bullet_count(
                text, policy=policy, **kw),
            implementation=(verify_exact_bullet_count, parse_list),
            status="new"),
        pairs.PAIR_1.focal.constraint_id: Verifier(
            spec=_p1_order_spec(policy),
            run=lambda text, **kw: verify_transitive_order(
                text, policy=policy, **kw),
            implementation=(verify_transitive_order, parse_list,
                            match_items_to_labels),
            status="new"),
    }


def bundle(policy: ListPolicy) -> dict[str, Verifier]:
    """Every target and focal verifier the three pairs require.

    The list policy is an argument for the same reason `parse_list` takes one:
    the bundle's identity depends on the Pair 1 parsing semantics, and those are
    not fixed by the preregistration.
    """
    from dci.verifiers import rules
    out = _pair_one_verifiers(policy)
    out[pairs.PAIR_2.target.constraint_id] = Verifier(
        spec=P2_TARGET_SPEC, run=verify_mandatory_words,
        implementation=(verify_mandatory_words, rules.v_require_word_set,
                        rules.word_tokens, rules.normalize_text),
        status="inherited_audited")
    out[pairs.PAIR_2.focal.constraint_id] = Verifier(
        spec=P2_FOCAL_SPEC, run=verify_all_words_unique,
        implementation=(verify_all_words_unique, rules.v_unique_words,
                        rules.word_tokens, rules.normalize_text),
        status="inherited_audited")
    out[pairs.PAIR_3.target.constraint_id] = Verifier(
        spec=P3_TARGET_SPEC, run=verify_exact_sentence_count,
        implementation=(verify_exact_sentence_count,
                        rules.v_exact_sentence_count, rules.split_sentences,
                        rules.count_status, rules.normalize_text),
        status="inherited_audited")
    out[pairs.PAIR_3.focal.constraint_id] = Verifier(
        spec=P3_FOCAL_SPEC, run=verify_increasing_lengths,
        implementation=(verify_increasing_lengths, rules.v_increasing_lengths,
                        rules.split_sentences, rules.word_tokens,
                        rules.normalize_text),
        status="inherited_audited")
    return out


def bundle_state(policy: ListPolicy) -> dict[str, Any]:
    """The complete verifier bundle as hashable state.

    Both hashes per verifier: declared semantics and executed source. This is the
    value `verifiers.bundle_hash` will carry once Stage 2 certification passes -
    it is computed here and frozen nowhere, because computing a hash is not
    certifying an artifact.
    """
    built = bundle(policy)
    return {"protocol": "v19", "list_policy_hash": policy.policy_hash,
            "verifiers": {cid: {"verifier_id": v.spec.verifier_id,
                                "status": v.status,
                                "spec_hash": v.spec.spec_hash,
                                "implementation_hash": v.implementation_hash,
                                "inherited_from": v.spec.inherited_from}
                          for cid, v in sorted(built.items())}}


def bundle_hash(policy: ListPolicy) -> str:
    return sha(["v19/verifier-bundle", bundle_state(policy)])


def assert_bundle_is_complete(policy: ListPolicy) -> dict[str, Verifier]:
    """Every declared target and focal constraint has a v19 verifier.

    Section 10.9's readiness snapshot listed the two Pair 1 verifiers as missing.
    This is the assertion that says so from the registry rather than from prose,
    and it is what `certify_verifiers` calls first.
    """
    built = bundle(policy)
    required = [rule.constraint_id for rule in pairs.rules()]
    missing = [cid for cid in required if cid not in built]
    if missing:
        raise VerifierContractError(
            f"{len(missing)} declared constraint(s) have no v19 verifier: "
            f"{missing}. Section 14.2 requires every deterministic verifier to "
            "exist before dependent measurement runs")
    stray = sorted(set(built) - set(required))
    if stray:
        raise VerifierContractError(
            f"the bundle carries verifier(s) for undeclared constraint(s) "
            f"{stray}; the bundle hash would then cover measurements no pair uses")
    return built
