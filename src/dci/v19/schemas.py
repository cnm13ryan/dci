"""Typed domains for the registry slots, so a frozen value is checked not trusted.

The adversarial audit's worst finding was that Stage 2 certified with every value
nonsense: `verifiers.p1.ordering_depth = None`, `inherited_reuse_decision = ""`,
`satisfiability.encoding_map = 12345`, `witness_constructor = 0`,
`semantic_reviews = "trust me"`, and an interval name that `frozen_interval` itself
rejects. `Slot.freeze` recorded them all and the gate reported them all as met,
because it asked whether a slot was RESOLVED and never whether its value was usable.

A domain is a named, auditable predicate. The name is part of the slot's declaration
fingerprint, so widening a domain is a change to the registry rather than to a
private helper, and `Slot.freeze` refuses a value its domain rejects. That is the
difference between populated and validated.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


class DomainError(ValueError):
    """A value that is not admissible for the slot it was offered to."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DomainError(message)


def _list_policy(value: Any) -> None:
    """The frozen grammar, as its canonical state.

    Only the grammar the code implements may be frozen: freezing a state the parser
    does not apply would put a measurement decision in the artifact trail that
    nothing enforces.
    """
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    _require(isinstance(value, Mapping), f"expected a mapping, got "
                                         f"{type(value).__name__}")
    _require(value == CANONICAL_LIST_POLICY.state(),
             "the frozen list grammar does not match the implemented one")


def _text_policy(value: Any) -> None:
    from dci.v19.text import CANONICAL_TEXT_POLICY
    _require(isinstance(value, Mapping), f"expected a mapping, got "
                                         f"{type(value).__name__}")
    _require(value == CANONICAL_TEXT_POLICY.state(),
             "the frozen text policy does not match the implemented one")


def _ordering_depth(value: Any) -> None:
    """The Pair 1 focal parameter's construct, its range, and its generator.

    Amendment A4 decides the CONSTRUCT, not the grid. Section 6.2's "predeclared
    ordered grid of at most five admissible settings" is the Stage 5 calibration
    output recorded in `parameters.p1.admissible_set` (register item D6), so a
    Stage 2 decision carrying a grid would pre-empt the procedure that selects it.
    An earlier version of this domain demanded one, which would have forced exactly
    that; it now refuses a grid instead.

    What it does require is that the recorded statistic and generator are the ones
    the code implements. A definition frozen in the registry that the construction
    path does not apply is a decision nothing enforces.
    """
    from dci.v19 import ordering
    _require(isinstance(value, Mapping), "expected a mapping")
    _require(bool(str(value.get("definition", "")).strip()),
             "'definition' must say what the parameter ranges over")
    _require(value.get("statistic") == ordering.STATISTIC_ID,
             f"'statistic' must be {ordering.STATISTIC_ID!r}, the statistic "
             f"dci.v19.ordering computes, got {value.get('statistic')!r}")
    _require(value.get("generator") == ordering.GENERATOR_ID,
             f"'generator' must be {ordering.GENERATOR_ID!r}, the generator "
             f"dci.v19.ordering implements, got {value.get('generator')!r}")
    _require(value.get("min_depth") == ordering.MIN_DEPTH,
             f"'min_depth' must be {ordering.MIN_DEPTH}: depth "
             f"{ordering.MIN_DEPTH - 1} states no precedence, so the focal "
             "constraint would be vacuous")
    _require(value.get("max_depth_rule") == "n_items",
             "'max_depth_rule' must be 'n_items': a chain cannot use items that do "
             "not exist")
    _require(value.get("harder_direction") == ordering.HARDER_DIRECTION,
             f"'harder_direction' must be {ordering.HARDER_DIRECTION!r}")
    _require(value.get("exposes") == ordering.EXPOSES,
             f"'exposes' must be {ordering.EXPOSES!r}: presenting the transitive "
             "closure would grow the number of stated precedences quadratically in "
             "the depth and confound depth with prompt length")
    _require(bool(str(value.get("generator_form", "")).strip()),
             "'generator_form' must state the form the generator produces")
    _require(value.get("grid") is None
             and bool(str(value.get("grid_rule", "")).strip()),
             "'grid' must be null with 'grid_rule' saying why: the ordered grid is "
             "the Stage 5 boundary-calibration output (D6), not a Stage 2 decision")

REUSE_DISPOSITIONS = ("reused_unchanged", "corrected", "reimplemented")


def _reuse_disposition(value: Any) -> None:
    _require(isinstance(value, Mapping), "expected a mapping")
    _require(value.get("disposition") in REUSE_DISPOSITIONS,
             f"'disposition' must be one of {REUSE_DISPOSITIONS}")
    _require(bool(str(value.get("rationale", "")).strip()),
             "'rationale' is required: section 14.2 permits reuse only after an audit")
    corrections = value.get("corrections")
    if value.get("disposition") != "reused_unchanged":
        _require(isinstance(corrections, Sequence) and not isinstance(corrections, str)
                 and bool(corrections),
                 "a corrected or reimplemented verifier names its corrections")


def _binomial_interval(value: Any) -> None:
    from dci.v19.reliability import INTERVAL_IMPLEMENTATIONS
    _require(isinstance(value, str) and value in INTERVAL_IMPLEMENTATIONS,
             f"expected one of {sorted(INTERVAL_IMPLEMENTATIONS)}, got {value!r}")


def _specification_bundle(value: Any) -> None:
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    from dci.v19.verifiers import bundle_state
    _require(value == bundle_state(CANONICAL_LIST_POLICY),
             "the frozen specification bundle does not match the implemented "
             "verifiers' declared and executed hashes")


def _bundle_hash(value: Any) -> None:
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    from dci.v19.verifiers import bundle_hash
    _require(value == bundle_hash(CANONICAL_LIST_POLICY),
             "the frozen bundle hash does not match the implemented bundle")


def _boundary_mutations(value: Any) -> None:
    """The RECORD SCHEMA for section 8.7 battery evidence. Deliberately stable.

    This domain says what a battery record must look like, and nothing about which
    templates exist or what their hashes are. That is a division of labour, not a
    weakness:

      * the domain is a property of the registry, and its meaning must not shift
        as the stack advances - a slot whose declared domain silently tightens
        between two commits has a fingerprint that no longer describes it;
      * whether the recorded hashes match a battery the harness actually produces
        is a CERTIFICATION question, answered by regenerating the battery and
        comparing. `dci.v19.stage2` does that, because that is where evidence is
        checked against the procedure that made it.

    So a well-formed record with invented hashes passes here and fails there. The
    audit's `{"not-a-real-template": {"n_mutations": 1000}}` fails both: it has no
    records_hash at all.
    """
    from dci.v19.stage2 import MUTATIONS_PER_TEMPLATE
    _require(isinstance(value, Mapping) and bool(value),
             "expected a non-empty mapping of constraint template to evidence")
    for template, offered in sorted(value.items()):
        _require(isinstance(template, str) and template.startswith("v19:"),
                 f"{template!r} is not a v19 constraint id; section 8.7's template "
                 "is a declared constraint")
        _require(isinstance(offered, Mapping), f"{template}: expected a mapping")
        digest = offered.get("records_hash")
        _require(isinstance(digest, str) and len(digest) == 64
                 and all(c in "0123456789abcdef" for c in digest),
                 f"{template}: 'records_hash' must be a sha-256 digest of the "
                 "battery, so the evidence can be re-derived rather than asserted")
        count = offered.get("n_mutations")
        _require(isinstance(count, int) and not isinstance(count, bool)
                 and count >= MUTATIONS_PER_TEMPLATE,
                 f"{template}: section 8.7 requires at least "
                 f"{MUTATIONS_PER_TEMPLATE} mutations, got {count!r}")
        distinct = offered.get("distinct_texts")
        _require(isinstance(distinct, int) and not isinstance(distinct, bool)
                 and distinct == count,
                 f"{template}: {distinct!r} distinct texts for {count!r} mutations. "
                 "A numeric floor reached by repeating one edit is not coverage")

def _encoding_map(value: Any) -> None:
    """Only the encoding the code actually implements may be frozen."""
    from dci.v19.encoding import encoding_map_state
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    _require(isinstance(value, Mapping), "expected a mapping")
    _require(value == encoding_map_state(CANONICAL_LIST_POLICY),
             "the frozen encoding map does not match the implemented one; freezing "
             "a map the code does not implement would certify an abstraction nobody "
             "computes")


def _solver_identity(value: Any) -> None:
    """The frozen solver must be the installed solver."""
    from dci.v19.solver import solver_identity
    _require(isinstance(value, Mapping), "expected a mapping with name and version")
    name, version = solver_identity()
    _require(value.get("name") == name and value.get("version") == version,
             f"the frozen solver is {value.get('name')!r} {value.get('version')!r} "
             f"and the installed solver is {name!r} {version!r}; section 8.6 needs "
             "the solver that produced the evidence, not a remembered one")


def _witness_constructor(value: Any) -> None:
    from dci.v19.witness import CONSTRUCTOR_ID
    _require(value == CONSTRUCTOR_ID,
             f"expected {CONSTRUCTOR_ID!r}, got {value!r}")


def _review_trigger(value: Any) -> None:
    """The section 14.2 review TRIGGER, demonstrated rather than asserted.

    Every fixture must hold, and the record hash must match evidence the code
    regenerates now - a frozen demonstration the code no longer reproduces is not
    a demonstration.
    """
    from dci.v19.review_trigger import TRIGGER_ID, frozen_trigger_evidence
    _require(isinstance(value, Mapping), "expected a mapping")
    _require(value.get("trigger_id") == TRIGGER_ID,
             f"'trigger_id' must be {TRIGGER_ID!r}, got {value.get('trigger_id')!r}")
    regenerated = frozen_trigger_evidence()
    _require(value.get("records_hash") == regenerated["records_hash"],
             "the recorded trigger evidence does not match the evidence the code "
             "regenerates, so it was asserted rather than demonstrated")
    _require(value.get("all_hold") is True,
             "a trigger fixture that does not hold is not evidence that the trigger "
             "works")


def _semantic_reviews(value: Any) -> None:
    """Every recorded review must reconstruct, and must have PASSED.

    Granularity is PER COMPOSITION. Two compositions differ in their witness, and a
    review is a judgement about one concrete text, so a review record shared across
    compositions is refused by the witness binding rather than by a policy note.
    """
    from dci.v19.certification import ReviewerVerdict, ReviewState, SemanticReview
    _require(isinstance(value, Mapping) and bool(value),
             "expected a non-empty mapping of composition id to review record")
    for composition_id, record in value.items():
        _require(isinstance(record, Mapping),
                 f"{composition_id}: expected a review record mapping")
        try:
            review = SemanticReview(
                composition_id=composition_id,
                witness_hash=str(record["witness_hash"]),
                clause_ids=tuple(record["clause_ids"]),
                reviews=tuple(ReviewerVerdict(r["reviewer_id"], r["satisfied"],
                                              r["rationale"])
                              for r in record.get("reviews", ())),
                adjudication=(ReviewerVerdict(record["adjudication"]["reviewer_id"],
                                              record["adjudication"]["satisfied"],
                                              record["adjudication"]["rationale"])
                              if record.get("adjudication") else None))
        except Exception as error:
            raise DomainError(
                f"{composition_id}: the review record does not reconstruct "
                f"({type(error).__name__}: {error})") from error
        _require(review.state is ReviewState.HUMAN_REVIEW_PASSED,
                 f"{composition_id}: review state is {review.state.value}, not "
                 "HUMAN_REVIEW_PASSED")


def _certified_compositions(value: Any) -> None:
    """Each entry must carry the three certificate identities and be certified."""
    _require(isinstance(value, Mapping) and bool(value),
             "expected a non-empty mapping of composition id to certificate record")
    for composition_id, record in sorted(value.items()):
        _require(isinstance(record, Mapping), f"{composition_id}: expected a mapping")
        for field in ("semantic_id", "implementation_id", "evidence_id",
                      "certificate_hash"):
            _require(bool(record.get(field)),
                     f"{composition_id}: {field} is missing, so the certificate "
                     "cannot be re-derived")
        _require(record.get("certified") is True,
                 f"{composition_id}: the record is not a certification")


def _tier1_audit_design(value: Any) -> None:
    """The A3 fixed audit design, as the state the code implements."""
    from dci.v19.reliability import AMENDED_TIER1_DESIGN
    _require(isinstance(value, Mapping), "expected a mapping")
    _require(value == AMENDED_TIER1_DESIGN.state(),
             "the frozen audit design does not match the implemented one; a design "
             "the gate does not apply is a decision nothing enforces")


def _tier1_audit_protocol(value: Any) -> None:
    """The human procedure for the Tier-1 audit, which section 10.4 leaves open.

    Deliberately does NOT default to section 8.6's two-plus-adjudicator rule. That
    rule governs semantic review of compositions; extending it here would be an
    implementer deciding a protocol question, which is what a PFD exists to
    prevent. What this domain requires is that whatever is decided is COMPLETE
    enough to execute: a reviewer count, a disagreement rule, and an answer to the
    over-sampling question that arises because a case's truth class is established
    by the reviewers rather than by its author.
    """
    _require(isinstance(value, Mapping), "expected a mapping")
    reviewers = value.get("independent_reviewers")
    _require(isinstance(reviewers, int) and not isinstance(reviewers, bool)
             and reviewers >= 2,
             "'independent_reviewers' must be an integer of at least 2: a single "
             "judgement cannot disagree with anything, so nothing could be "
             "adjudicated and 'human-adjudicated' would be a misnomer")
    _require(value.get("adjudicator_resolves_disagreement") is True,
             "'adjudicator_resolves_disagreement' must be true; an unresolved "
             "disagreement resolved by preferring one reviewer is not adjudication")
    _require(bool(str(value.get("adjudicator_id", "")).strip()),
             "'adjudicator_id' must name the adjudicator, who must be "
             "distinguishable from the independent reviewers")
    _require(value.get("unresolved_disagreement") == "fails",
             "'unresolved_disagreement' must be 'fails'")
    rule = value.get("oversampling_rule")
    _require(rule in ("exact_authoring", "prospective_oversample"),
             "'oversampling_rule' must be 'exact_authoring' (every case is assumed "
             "to land in its intended class, and any that does not fails the audit) "
             "or 'prospective_oversample' (more cases are authored than needed and "
             "a prospectively fixed rule selects which count)")
    if rule == "prospective_oversample":
        factor = value.get("oversample_factor")
        _require(isinstance(factor, (int, float)) and not isinstance(factor, bool)
                 and factor > 1,
                 "'oversample_factor' must exceed 1 for a prospective over-sample")
        _require(bool(str(value.get("selection_rule", "")).strip()),
                 "'selection_rule' must state which adjudicated cases count, fixed "
                 "BEFORE any judgement is seen; a rule chosen afterwards is the "
                 "conditional selection amendment A3 forbids")
    _require(bool(str(value.get("citation", "")).strip()),
             "'citation' must record the governing text and the decision record")


def _tier1_certificates(value: Any) -> None:
    """One passing Tier-1 certificate per target and focal verifier unit."""
    from dci.v19.pairs import rules
    _require(isinstance(value, Mapping), "expected a mapping keyed by verifier unit")
    required = {rule.constraint_id for rule in rules()}
    missing = sorted(required - set(value))
    _require(not missing, f"no Tier-1 certificate for {missing}")
    for unit, record in sorted(value.items()):
        _require(isinstance(record, Mapping), f"{unit}: expected a mapping")
        _require(record.get("passed") is True,
                 f"{unit}: the certificate does not record a pass")
        _require(not record.get("unavailable"),
                 f"{unit}: truth class(es) {record.get('unavailable')} are "
                 "unavailable, and a missing denominator is missing evidence")


DOMAINS: Mapping[str, Callable[[Any], None]] = {
    "list_policy": _list_policy,
    "text_policy": _text_policy,
    "ordering_depth": _ordering_depth,
    "reuse_disposition": _reuse_disposition,
    "binomial_interval": _binomial_interval,
    "tier1_audit_design": _tier1_audit_design,
    "specification_bundle": _specification_bundle,
    "bundle_hash": _bundle_hash,
    "boundary_mutations": _boundary_mutations,
    "tier1_audit_protocol": _tier1_audit_protocol,
    "tier1_certificates": _tier1_certificates,
    "encoding_map": _encoding_map,
    "solver_identity": _solver_identity,
    "witness_constructor": _witness_constructor,
    "review_trigger": _review_trigger,
    "semantic_reviews": _semantic_reviews,
    "certified_compositions": _certified_compositions,
}


def validate(domain: str, value: Any) -> None:
    """Check a value against a named domain, or refuse the domain itself."""
    if domain not in DOMAINS:
        raise DomainError(
            f"{domain!r} is not a declared slot domain; known: {sorted(DOMAINS)}")
    DOMAINS[domain](value)
