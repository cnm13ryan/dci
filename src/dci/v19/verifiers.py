"""Deterministic v19 verifiers: one contract, one text semantics, six constraints.

Section 10.1 records three *orthogonal* things about a delivered final-answer
segment, and the inherited code records them in one field. `VerifierOutcome` keeps
four apart, the fourth being whether scoring happened at all:

  * the constraint verdict, PASS or FAIL and nothing else;
  * the generation state, SCORABLE / UNPARSEABLE / TRUNCATED / EMPTY / REFUSAL;
  * the secondary compliance level, FULL / PARTIAL / VIOLATION;
  * whether deterministic scoring ran, which is not a behavioural field at all.

That last one does the real work. Section 10.1: "a technical failure before a
final-answer segment is delivered has no fabricated behavioural verdict." A verifier
that crashes and returns FAIL has fabricated one, and the failure is then
indistinguishable from the model breaking a rule - so `verdict` is None unless
scoring succeeded, `f_a` raises rather than returning a number, and
`Verifier.invoke` catches at one place instead of at every call site.

CORRECTED, NOT INHERITED UNCHANGED
----------------------------------
Section 14.2 permits reuse of the Pair 2/3 implementations "only after hash/semantic
audit"; section 10.6 says what an audit that finds something requires: "A
demonstrated semantic or verifier defect requires repair and re-audit before freeze;
collecting more confirmatory data is not a remedy for invalid measurement." Three
defects were demonstrated, so all six verifiers now read `dci.v19.text`, whose
`INTENTIONAL_CORRECTIONS` table records each difference and the defect it repairs.
The inherited module is untouched: the v15.1 pipeline and its regression fixtures
still depend on it, and `tests/unit/test_v19_inherited_verifier_audit.py` is the
differential audit that shows every disagreement is one of the recorded corrections.

WHAT IS HASHED
--------------
Appendix I requires "invariant model/tokenizer/template/controller/decoder/runtime/
verifier/inference hashes" across the run. Three hashes per verifier, all
load-bearing:

  * `spec_hash` covers the declared semantics INCLUDING the frozen text policy and
    the marker patterns, so changing normalisation changes the measurement's identity;
  * `implementation_hash` covers the source actually executed;
  * `bundle_hash` covers the whole set, and unlike before it travels inside the
    certificate rather than being computable only alongside it.

None is frozen here. Computing a hash is not certifying an artifact.
"""
from __future__ import annotations

import enum
import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import field_roles, pairs
from dci.v19 import text as textlib
from dci.v19.parsing import (
    CANONICAL_LIST_POLICY,
    ListPolicy,
    OrderingRelation,
    match_items_to_labels,
    parse_list,
    sentence_lengths,
    sentences,
)
from dci.v19.text import TextPolicy
from dci.verifiers import rules


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
    """Whether deterministic scoring happened. Not a behavioural field."""

    SCORED = "SCORED"
    MISSING_METADATA = "MISSING_METADATA"
    VERIFIER_ERROR = "VERIFIER_ERROR"


# States the caller already knows. The verifier may narrow SCORABLE to EMPTY or
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
    correction: str = ""
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
        """The canonical serialisation. `citation` and `audit` are prose."""
        return {"verifier_id": self.verifier_id,
                "constraint_id": self.constraint_id,
                "statement": self.statement, "rule": self.rule,
                "span": self.span, "parameters": list(self.parameters),
                "segmentation": dict(self.segmentation),
                "inherited_from": self.inherited_from,
                "correction": self.correction}

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
                f"{self.verifier_id}: scoring is {self.scoring.value} yet a verdict "
                f"{self.verdict!r} is recorded. A technical scoring failure must "
                "never arrive as a behavioural verdict (sections 10.1, 10.8)")
        if not scored and self.compliance is not None:
            raise VerifierContractError(
                f"{self.verifier_id}: scoring is {self.scoring.value} yet a "
                "compliance level is recorded")
        if self.compliance is not None:
            if not isinstance(self.compliance, Compliance):
                raise VerifierContractError(
                    f"{self.compliance!r} is not a Compliance")
            full = self.compliance is Compliance.FULL
            if full is not (self.verdict is Verdict.PASS):
                raise VerifierContractError(
                    f"{self.verifier_id}: compliance {self.compliance.value} "
                    f"contradicts verdict "
                    f"{self.verdict.value if self.verdict else None}. Section 10.1: "
                    "for an exact target PARTIAL implies primary failure, so FULL "
                    "and PASS agree or the record is wrong")
        if not self.reason:
            raise VerifierContractError(
                f"{self.verifier_id}: every outcome states why, so a verdict can be "
                "re-derived from the record rather than re-run")

    @property
    def scored(self) -> bool:
        return self.scoring is Scoring.SCORED

    @property
    def f_a(self) -> int:
        """The section 11.1 failure indicator: 1 on FAIL, 0 on PASS."""
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

    The risk is not that a diagnostic key is misclassified but that evidence starts
    carrying a key that IS legitimately primary - `arm`, `load`, `target_verdict` -
    after which a formula can consume the blob and pick the field up with it
    (section 11.8).
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
            f"{outcome.verifier_id} put {len(laundered)} primary-usable field(s) into "
            f"diagnostic verifier evidence: {'; '.join(laundered)}. Evidence is "
            "diagnostic only (section 11.8); a primary field reaching analysis "
            "through an evidence blob has bypassed the role registry")
    return outcome


# --------------------------------------------------------- the frozen semantics

def frozen_segmentation(text_policy: TextPolicy,
                        list_policy: ListPolicy | None = None) -> dict[str, Any]:
    """Everything about how a segment is read, for the specification hash.

    Includes the marker patterns when the verifier's span depends on them, which is
    how section 4.4's shared segmentation becomes visible in Pair 3's hash rather
    than hidden inside a helper.

    It also carries the abbreviation guard's substance, not merely its name. The
    policy declares WHICH guard runs; `abbreviation_guard_state` records what that
    guard decides with, because the guard now lives in `dci.verifiers.rules` and a
    change to its tables moves F_A without moving any v19 source. See that
    function for why delegation made this necessary.
    """
    state: dict[str, Any] = {"text_policy": text_policy.state(),
                             "text_policy_hash": text_policy.policy_hash,
                             "abbreviation_guard":
                                 textlib.abbreviation_guard_state(text_policy)}
    if list_policy is not None:
        state["list_policy_hash"] = list_policy.policy_hash
        state["marker_patterns"] = list(list_policy.marker_patterns())
    return state


def implementation_hash(*callables: Callable) -> str:
    """Hash of the source actually executed.

    Refuses a callable whose source cannot be read - a C function, a lambda built at
    a prompt, a partial. Appendix I wants an invariant hash over the code that ran,
    and a callable with no readable source cannot contribute one, so this fails closed
    rather than raising OSError from inside a certification.
    """
    sources = []
    for fn in callables:
        try:
            sources.append(inspect.getsource(fn))
        except (OSError, TypeError) as error:
            raise VerifierContractError(
                f"the source of {getattr(fn, '__qualname__', fn)!r} cannot be read "
                f"({type(error).__name__}), so it cannot enter the implementation "
                "hash Appendix I requires to be invariant across the run") from error
    return sha(["v19/verifier-implementation", sources])


def _delivered(text: Any, state: GenerationState) -> GenerationState:
    """Narrow SCORABLE to EMPTY when nothing was delivered; never widen."""
    if state in CALLER_SUPPLIED_STATES:
        return state
    return GenerationState.EMPTY if not str(text or "").strip() else state


def _unparseable(text: Any, state: GenerationState) -> GenerationState:
    """The span produced nothing, but bytes were delivered."""
    if state in CALLER_SUPPLIED_STATES or state is GenerationState.EMPTY:
        return state
    return GenerationState.UNPARSEABLE


def _missing(spec: VerifierSpec, parameters: Mapping[str, Any], text: Any,
             state: GenerationState, reason: str) -> VerifierOutcome:
    return VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash, parameters=dict(parameters),
        scoring=Scoring.MISSING_METADATA, verdict=None,
        generation_state=_delivered(text, state), compliance=None, reason=reason,
        evidence={})


def _scored(spec: VerifierSpec, parameters: Mapping[str, Any], *, passed: bool,
            compliance: Compliance, state: GenerationState, reason: str,
            evidence: Mapping[str, Any]) -> VerifierOutcome:
    return assert_evidence_is_diagnostic(VerifierOutcome(
        verifier_id=spec.verifier_id, constraint_id=spec.constraint_id,
        spec_hash=spec.spec_hash, parameters=dict(parameters),
        scoring=Scoring.SCORED,
        verdict=Verdict.PASS if passed else Verdict.FAIL,
        generation_state=state, compliance=compliance, reason=reason,
        evidence=dict(evidence)))


def _count_compliance(observed: int, required: int) -> Compliance:
    """Section 10.1: PARTIAL where the constraint admits a richer description."""
    if observed == required:
        return Compliance.FULL
    if observed and abs(observed - required) == 1:
        return Compliance.PARTIAL
    return Compliance.VIOLATION


def _fraction_compliance(satisfied: int, total: int) -> Compliance:
    if total and satisfied == total:
        return Compliance.FULL
    return Compliance.PARTIAL if satisfied else Compliance.VIOLATION


# ----------------------------------------------------------------- Pair 1

def _p1_count_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.exact_bullet_count",
        constraint_id=pairs.PAIR_1.target.constraint_id,
        statement=pairs.PAIR_1.target.statement,
        rule=("PASS iff the number of list items parsed from the final-answer "
              "segment under the frozen list grammar equals n_items exactly"),
        citation="sections 4.1, 4.2, 14.2",
        span="list_segmentation",
        parameters=("n_items",),
        segmentation=frozen_segmentation(policy.text, policy),
        audit="new in v19; section 10.9 records that Pair 1 support had to be built")


def _p1_order_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.transitive_order",
        constraint_id=pairs.PAIR_1.focal.constraint_id,
        statement=pairs.PAIR_1.focal.statement,
        rule=("PASS iff every declared item is identified exactly once among the "
              "parsed list items by word-token equality, no item is unidentified, "
              "and every pair in the transitive closure of the declared precedence "
              "relation appears in that order"),
        citation="sections 4.1, 4.2, 14.2",
        span="list_segmentation+relation_evaluation",
        parameters=("relation",),
        segmentation=frozen_segmentation(policy.text, policy),
        audit="new in v19; shares list_segmentation with the target verifier, which "
              "is the coupling section 4.2 names")


def verify_exact_bullet_count(text: Any, *, n_items: Any, policy: ListPolicy,
                              delivered_state: GenerationState
                              = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 1 target: exactly `n_items` list items under the frozen grammar."""
    spec = _p1_count_spec(policy)
    if isinstance(n_items, bool) or not isinstance(n_items, int) or n_items < 1:
        return _missing(spec, {"n_items": n_items}, text, delivered_state,
                        f"n_items={n_items!r} is not a positive integer, so the "
                        "target has no parameter realisation to verify against")
    parsed = parse_list(text, policy)
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not parsed.items and not parsed.excluded:
        state = _unparseable(text, state)
    observed = parsed.count
    return _scored(spec, {"n_items": n_items}, passed=observed == n_items,
                   compliance=_count_compliance(observed, n_items), state=state,
                   reason=f"observed {observed} list item(s), required exactly "
                          f"{n_items}",
                   evidence={"expected_count": n_items, "observed_count": observed,
                             "parse": parsed.describe()})


def verify_transitive_order(text: Any, *, relation: OrderingRelation,
                            policy: ListPolicy,
                            delivered_state: GenerationState
                            = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 1 focal: the declared items appear in a valid linear extension.

    Any arrangement consistent with the relation passes. A partial order can have
    several, and comparing against one expected sequence would fail valid answers.
    """
    spec = _p1_order_spec(policy)
    if not isinstance(relation, OrderingRelation):
        return _missing(spec, {}, text, delivered_state,
                        f"the instantiated ordering relation is {relation!r}, not an "
                        "OrderingRelation; the focal parameter realisation is absent")
    parsed = parse_list(text, policy)
    identification = match_items_to_labels(parsed, relation, policy)
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not parsed.items:
        state = _unparseable(text, state)
    closure = relation.closure()

    structural: list[str] = []
    if identification["missing_labels"]:
        structural.append(f"item(s) {identification['missing_labels']} never appear")
    if identification["duplicated_labels"]:
        structural.append(
            f"item(s) {identification['duplicated_labels']} appear more than once")
    if identification["ambiguous"]:
        structural.append(
            f"{len(identification['ambiguous'])} list item(s) match more than one "
            "declared item, so their identity is not determined")
    extra = identification["unmatched_ordinals"]
    if extra and not policy.extra_items_permitted:
        structural.append(
            f"{len(extra)} list item(s) match no declared item, and the frozen "
            "grammar does not permit undeclared items")

    position: dict[str, int] = {}
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
        reason = (f"all {len(closure)} required precedence(s) hold in the observed "
                  "arrangement")
    return _scored(
        spec, {"relation_hash": relation.relation_hash,
               "declared_items": list(relation.items),
               "declared_edges": [list(e) for e in relation.edges],
               "extra_items_permitted": policy.extra_items_permitted},
        passed=passed,
        compliance=Compliance.FULL if passed else (
            Compliance.VIOLATION if structural else Compliance.PARTIAL),
        state=state, reason=reason,
        evidence={"identification": identification,
                  "required_closure": [list(e) for e in closure],
                  "violated_precedences": violated,
                  "structural_problems": structural,
                  "chain_depth": relation.chain_depth,
                  "parse": parsed.describe()})


# --------------------------------------------------------- Pairs 2 and 3

CORRECTION_NOTE = ("corrected under sections 10.6 and 14.2 onto the frozen v19 text "
                   "policy; see dci.v19.text.INTENTIONAL_CORRECTIONS")


def _p2_target_spec(text_policy: TextPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.require_word_set",
        constraint_id=pairs.PAIR_2.target.constraint_id,
        statement=pairs.PAIR_2.target.statement,
        rule=("PASS iff every mandatory word occurs at least once among the word "
              "tokens of the final-answer segment, compared under the frozen text "
              "policy's normalisation and case rule"),
        citation="sections 4.1, 4.3, 10.1, 14.2",
        span="word_normalisation",
        parameters=("mandatory_word_set",),
        segmentation=frozen_segmentation(text_policy),
        inherited_from="U_REQ (v_require_word_set)",
        correction=CORRECTION_NOTE,
        audit="a mandatory word containing a non-ASCII letter could never be matched "
              "under the inherited ASCII pattern, making that parameter realisation "
              "an impossible composition rather than a failing answer (section 4.3)")


def _p2_focal_spec(text_policy: TextPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.unique_words",
        constraint_id=pairs.PAIR_2.focal.constraint_id,
        statement=pairs.PAIR_2.focal.statement,
        rule=("PASS iff the word tokens of the final-answer segment are pairwise "
              "distinct under the frozen text policy's normalisation and case rule"),
        citation="sections 4.1, 4.3, 10.1, 14.2",
        span="word_normalisation",
        parameters=(),
        segmentation=frozen_segmentation(text_policy),
        inherited_from="L_UNIQ (v_unique_words)",
        correction=CORRECTION_NOTE,
        audit="a zero-width space or soft hyphen split a repeated word into distinct "
              "tokens under the inherited pattern, so the rule passed while a word "
              "repeated; section 10.6 names both as required audit material")


def _p3_target_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.exact_sentence_count",
        constraint_id=pairs.PAIR_3.target.constraint_id,
        statement=pairs.PAIR_3.target.statement,
        rule=("PASS iff the number of segments produced by the frozen sentence "
              "segmentation equals n_sentences exactly"),
        citation="sections 4.1, 4.4, 10.1, 14.2",
        span="sentence_segmentation",
        parameters=("n_sentences",),
        segmentation=frozen_segmentation(policy.text, policy),
        inherited_from="A / S2 (v_exact_sentence_count)",
        correction=CORRECTION_NOTE,
        audit="the segmentation strips the list grammar's own markers and treats "
              "each remaining line as a segment, so a list of N lines is N "
              "sentences - the shared-segmentation risk section 4.4 names, now "
              "explicit in this hash because the marker patterns are inside it")


def _p3_focal_spec(policy: ListPolicy) -> VerifierSpec:
    return VerifierSpec(
        verifier_id="v19:verifier.increasing_lengths",
        constraint_id=pairs.PAIR_3.focal.constraint_id,
        statement=pairs.PAIR_3.focal.statement,
        rule=("PASS iff there are at least two segments and successive segment "
              "lengths, counted in word tokens under the frozen text policy, "
              "strictly increase"),
        citation="sections 4.1, 4.4, 10.1, 14.2",
        span="sentence_segmentation+word_counts",
        parameters=(),
        segmentation=frozen_segmentation(policy.text, policy),
        inherited_from="B / O1 (v_increasing_lengths)",
        correction=CORRECTION_NOTE,
        audit="strict increase, not non-decreasing: `v_nondecreasing_lengths` exists "
              "in the inherited module and is a different rule that must not be "
              "substituted")


def verify_mandatory_words(text: Any, *, mandatory_words: Any,
                           text_policy: TextPolicy,
                           delivered_state: GenerationState
                           = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 2 target, on the frozen text policy."""
    spec = _p2_target_spec(text_policy)
    words = tuple(mandatory_words) if isinstance(
        mandatory_words, (list, tuple)) else None
    if not words or any(not isinstance(w, str) or not w.strip() for w in words):
        return _missing(spec, {"mandatory_word_set": mandatory_words}, text,
                        delivered_state,
                        f"mandatory_words={mandatory_words!r} is not a non-empty "
                        "sequence of words, so the target has no realisation")
    required = [textlib.fold(w, text_policy) for w in words]
    if any(len(textlib.word_tokens(w, text_policy)) != 1 for w in words):
        return _missing(spec, {"mandatory_word_set": list(words)}, text,
                        delivered_state,
                        f"mandatory word(s) in {list(words)} are not single word "
                        "tokens under the frozen text policy, so presence is not "
                        "decidable as stated")
    observed = textlib.token_multiset(text, text_policy)
    present = {word: observed.get(word, 0) >= 1 for word in dict.fromkeys(required)}
    hits = sum(present.values())
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not observed:
        state = _unparseable(text, state)
    return _scored(spec, {"mandatory_word_set": list(words), "folded": required},
                   passed=all(present.values()),
                   compliance=_fraction_compliance(hits, len(present)), state=state,
                   reason=f"{hits} of {len(present)} mandatory word(s) present",
                   evidence={"present": present, "n_tokens": sum(observed.values()),
                             "n_distinct_tokens": len(observed)})


def verify_all_words_unique(text: Any, *, text_policy: TextPolicy,
                            delivered_state: GenerationState
                            = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 2 focal, on the frozen text policy."""
    spec = _p2_focal_spec(text_policy)
    tokens = textlib.folded_tokens(text, text_policy)
    state = _delivered(text, delivered_state)
    if not tokens:
        # Section 10.1: an exact requirement that cannot be demonstrated as
        # satisfied receives FAIL, and the state field preserves why.
        return _scored(spec, {}, passed=False, compliance=Compliance.VIOLATION,
                       state=_unparseable(text, state),
                       reason="the segment yielded no word token, so distinctness "
                              "cannot be demonstrated (section 10.1)",
                       evidence={"n_tokens": 0, "n_distinct_tokens": 0,
                                 "repeated": {}})
    counts = textlib.token_multiset(text, text_policy)
    repeated = {token: n for token, n in sorted(counts.items()) if n > 1}
    return _scored(spec, {}, passed=not repeated,
                   compliance=_fraction_compliance(len(counts), len(tokens)),
                   state=state,
                   reason=(f"{len(counts)} distinct token(s) among {len(tokens)}"
                           + (f"; repeated {sorted(repeated)}" if repeated else "")),
                   evidence={"n_tokens": len(tokens),
                             "n_distinct_tokens": len(counts),
                             "repeated": repeated})


def verify_exact_sentence_count(text: Any, *, n_sentences: Any, policy: ListPolicy,
                                delivered_state: GenerationState
                                = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 3 target, on the frozen segmentation the list grammar also feeds."""
    spec = _p3_target_spec(policy)
    if (isinstance(n_sentences, bool) or not isinstance(n_sentences, int)
            or n_sentences < 1):
        return _missing(spec, {"n_sentences": n_sentences}, text, delivered_state,
                        f"n_sentences={n_sentences!r} is not a positive integer, so "
                        "the target has no parameter realisation")
    segments = sentences(text, policy)
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not segments:
        state = _unparseable(text, state)
    observed = len(segments)
    return _scored(spec, {"n_sentences": n_sentences},
                   passed=observed == n_sentences,
                   compliance=_count_compliance(observed, n_sentences), state=state,
                   reason=f"observed {observed} sentence(s), required exactly "
                          f"{n_sentences}",
                   evidence={"expected_count": n_sentences,
                             "observed_count": observed,
                             "segments": list(segments)})


def verify_increasing_lengths(text: Any, *, policy: ListPolicy,
                              delivered_state: GenerationState
                              = GenerationState.SCORABLE) -> VerifierOutcome:
    """Pair 3 focal, on the same segmentation and the same length unit."""
    spec = _p3_focal_spec(policy)
    lengths = sentence_lengths(text, policy)
    state = _delivered(text, delivered_state)
    if state is GenerationState.SCORABLE and not lengths:
        state = _unparseable(text, state)
    if len(lengths) < 2:
        return _scored(spec, {}, passed=False, compliance=Compliance.VIOLATION,
                       state=state,
                       reason=(f"{len(lengths)} segment(s): a monotone increase "
                               "cannot be demonstrated with fewer than two, so the "
                               "requirement is not satisfied (section 10.1)"),
                       evidence={"word_counts": lengths, "checks": []})
    checks = [later > earlier for earlier, later in zip(lengths, lengths[1:])]
    satisfied = sum(checks)
    return _scored(spec, {}, passed=all(checks),
                   compliance=_fraction_compliance(satisfied, len(checks)),
                   state=state,
                   reason=f"{satisfied} of {len(checks)} adjacent pair(s) strictly "
                          f"increase; lengths {lengths}",
                   evidence={"word_counts": lengths, "checks": checks})


# ------------------------------------------------------------------- the bundle

@dataclass(frozen=True)
class Verifier:
    """One constraint's deterministic measurement, spec and callable together."""
    spec: VerifierSpec
    run: Callable[..., VerifierOutcome]
    implementation: tuple[Callable, ...]
    status: str                      # "new" or "inherited_corrected"

    @property
    def implementation_hash(self) -> str:
        return implementation_hash(*self.implementation)

    def invoke(self, text: Any, **kwargs: Any) -> VerifierOutcome:
        """Run the verifier, turning an exception into VERIFIER_ERROR.

        A crash is a technical scoring failure (section 10.8), never a behavioural
        FAIL, so it is caught at exactly one place instead of at every call site.
        """
        state = kwargs.get("delivered_state", GenerationState.SCORABLE)
        try:
            return self.run(text, **kwargs)
        except Exception as error:            # noqa: BLE001 - deliberate
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
                reason=(f"{type(error).__name__} while scoring: {error}. This is a "
                        "technical scoring failure; rerun verification on the stored "
                        "bytes (section 10.8)"),
                evidence={})


def bundle(policy: ListPolicy = CANONICAL_LIST_POLICY) -> dict[str, Verifier]:
    """Every target and focal verifier the three pairs require.

    The grammar is an argument because the Pair 1 and Pair 3 spans depend on it and
    the bundle's identity therefore does too. It defaults to the canonical grammar
    frozen by the Stage 2 amendment - unlike `parse_list`, where a default would let
    a call site inherit an unreviewed decision, here the default IS the frozen
    decision and the registry still gates whether it may be relied on.
    """
    text_policy = policy.text
    built = {
        pairs.PAIR_1.target.constraint_id: Verifier(
            spec=_p1_count_spec(policy),
            run=lambda t, **kw: verify_exact_bullet_count(t, policy=policy, **kw),
            implementation=(verify_exact_bullet_count, parse_list,
                            textlib.normalise),
            status="new"),
        pairs.PAIR_1.focal.constraint_id: Verifier(
            spec=_p1_order_spec(policy),
            run=lambda t, **kw: verify_transitive_order(t, policy=policy, **kw),
            implementation=(verify_transitive_order, parse_list,
                            match_items_to_labels, textlib.folded_tokens),
            status="new"),
        pairs.PAIR_2.target.constraint_id: Verifier(
            spec=_p2_target_spec(text_policy),
            run=lambda t, **kw: verify_mandatory_words(
                t, text_policy=text_policy, **kw),
            implementation=(verify_mandatory_words, textlib.token_multiset,
                            textlib.word_tokens, textlib.normalise, textlib.fold),
            status="inherited_corrected"),
        pairs.PAIR_2.focal.constraint_id: Verifier(
            spec=_p2_focal_spec(text_policy),
            run=lambda t, **kw: verify_all_words_unique(
                t, text_policy=text_policy, **kw),
            implementation=(verify_all_words_unique, textlib.token_multiset,
                            textlib.folded_tokens, textlib.normalise, textlib.fold),
            status="inherited_corrected"),
        pairs.PAIR_3.target.constraint_id: Verifier(
            spec=_p3_target_spec(policy),
            run=lambda t, **kw: verify_exact_sentence_count(t, policy=policy, **kw),
            # `rules.split_line` and `rules.ends_sentence` are the delegated
            # boundary decision. They execute on every scored answer, so their
            # source belongs in the hash of "the code that ran" exactly as much
            # as the v19 helpers do.
            implementation=(verify_exact_sentence_count, sentences,
                            textlib.split_sentences, textlib.normalise,
                            rules.split_line, rules.ends_sentence,
                            rules._opens_with_capital),
            status="inherited_corrected"),
        pairs.PAIR_3.focal.constraint_id: Verifier(
            spec=_p3_focal_spec(policy),
            run=lambda t, **kw: verify_increasing_lengths(t, policy=policy, **kw),
            implementation=(verify_increasing_lengths, sentence_lengths,
                            textlib.sentence_lengths, textlib.split_sentences,
                            textlib.word_tokens, textlib.normalise,
                            rules.split_line, rules.ends_sentence,
                            rules._opens_with_capital),
            status="inherited_corrected"),
    }
    return built


def bundle_state(policy: ListPolicy = CANONICAL_LIST_POLICY) -> dict[str, Any]:
    """The complete verifier bundle as hashable state.

    Three identities: the declared semantics, the executed source, and the frozen
    policies both rest on. This is the value `verifiers.specification_bundle` will
    carry once Stage 2 certification passes; it is computed here and frozen nowhere.
    """
    built = bundle(policy)
    return {"protocol": "v19", "list_policy_hash": policy.policy_hash,
            "text_policy_hash": policy.text.policy_hash,
            "verifiers": {cid: {"verifier_id": v.spec.verifier_id,
                                "status": v.status,
                                "spec_hash": v.spec.spec_hash,
                                "implementation_hash": v.implementation_hash,
                                "inherited_from": v.spec.inherited_from,
                                "correction": v.spec.correction}
                          for cid, v in sorted(built.items())}}


def bundle_hash(policy: ListPolicy = CANONICAL_LIST_POLICY) -> str:
    return sha(["v19/verifier-bundle", bundle_state(policy)])


def assert_bundle_is_complete(policy: ListPolicy = CANONICAL_LIST_POLICY
                              ) -> dict[str, Verifier]:
    """Every declared target and focal constraint has a v19 verifier."""
    built = bundle(policy)
    required = [rule.constraint_id for rule in pairs.rules()]
    missing = [cid for cid in required if cid not in built]
    if missing:
        raise VerifierContractError(
            f"{len(missing)} declared constraint(s) have no v19 verifier: {missing}. "
            "Section 14.2 requires every deterministic verifier to exist before "
            "dependent measurement runs")
    stray = sorted(set(built) - set(required))
    if stray:
        raise VerifierContractError(
            f"the bundle carries verifier(s) for undeclared constraint(s) {stray}; "
            "the bundle hash would then cover measurements no pair uses")
    return built
