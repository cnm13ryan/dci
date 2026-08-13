"""The Tier-1 reliability audit: manifest, blinded packets, fail-closed ingestion.

Section 10.4 certifies each of the six target and focal verifiers individually
against a 5% conditional error ceiling. Amendment A3 fixes the design: 72
human-adjudicated true failures and 72 true passes per unit, 864 labels in total,
exact two-sided 95% Clopper-Pearson, zero errors permitted, no extension.

This module is the apparatus for collecting that evidence. It does NOT contain the
evidence, and it cannot manufacture it.

WHAT A TRUTH CLASS IS, AND WHY IT IS NOT KNOWN IN ADVANCE
--------------------------------------------------------
Section 10.4: "A false-pass bound requires adjudicated examples that truly fail the
constraint. A false-fail bound requires adjudicated examples that truly pass."

So the denominator of each bound is a set of cases whose GROUND TRUTH the humans
establish. The verifier's own verdict is the thing being measured against that
truth; it plays no part in deciding which class a case belongs to. A case is
therefore authored with an INTENDED class - that is what the content-sufficiency
gate counts - and adjudication either confirms it or does not. A case whose
adjudicated class differs from its intended class is not a verifier error; it is a
case-authoring miss, and it counts toward the class the humans put it in.

That ordering has a consequence the protocol does not resolve, recorded as
ambiguity B in docs/v19_tier1_audit_handoff.md: because the class is known only
after adjudication, reaching EXACTLY 72 per class requires either a prospective
over-sample with a prospective selection rule, or an exact-authoring assumption
that every case lands in its intended class. Both are prospective; choosing
between them is not this module's decision, and `AUDIT_PROTOCOL_SLOT` stays a
PENDING_DECISION until it is made.

WHAT THIS MODULE REFUSES TO DO
------------------------------
It will not author cases. `pool.{pair}.audit` is a declared scientific split
(section 11.1) whose content is PENDING_CONTENT, authored by people "before freeze
under a versioned content procedure". Generating 864 plausible-looking cases here
would put unauthored scientific material into the artifact trail, where nothing
downstream could distinguish it from material a person wrote.

It will not supply reviewer judgements, and it will not read a missing judgement as
a correct one - `ingest` refuses an incomplete return rather than defaulting it.
"""
from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19.reliability import (
    AMENDED_TIER1_DESIGN,
    AuditDesign,
    TierCertificate,
    tier1_certificate_under,
)

MANIFEST_ID = "v19:tier1-audit-manifest.v1"
PROTOCOL_ID = "v19:tier1-audit-protocol.frozen-v1"
SELECTION_ID = "v19:tier1-selection.first-72-by-manifest-order"

# The frozen protocol's authoring budget: exactly this many candidates per unit per
# INTENDED class. 100 rather than 72 because a case's truth class is established by
# the reviewers, not by its author: authoring exactly 72 reaches 72 adjudicated
# cases with probability about 0.55 even when mis-adjudicated cases are credited to
# the other class, and essentially never when they are discarded - which this
# protocol does. 72 is the denominator; 100 is the budget.
CANDIDATES_PER_CLASS = 100
INDEPENDENT_REVIEWERS = 2
PANEL_SIZE = 3

# The accepted decision, recorded here so the registry value and the code cannot
# drift. Every field is enforced somewhere in this module and tested.
PROTOCOL: Mapping[str, Any] = {
    "protocol_id": PROTOCOL_ID,
    "candidates_per_class": CANDIDATES_PER_CLASS,
    "candidates_per_unit": CANDIDATES_PER_CLASS * 2,
    "independent_reviewers": INDEPENDENT_REVIEWERS,
    "panel_size": PANEL_SIZE,
    "adjudicator_resolves_disagreement": True,
    "reviewers_communicate_before_submitting": False,
    "blinded_to": ["intended_truth_class", "verifier_verdict", "arm",
                   "constraint_role", "constraint_identity", "verifier_identity"],
    "ground_truth_source": "human_adjudication",
    "cross_crediting_permitted": False,
    "unresolved_case": "excluded_unusable",
    "oversampling_rule": "prospective_oversample",
    "selection_rule": SELECTION_ID,
    "selection_size": 72,
    "top_up_permitted": False,
    "conditional_extension_permitted": False,
    "case_reuse_across_units_permitted": False,
    "insufficient_pool_outcome": "AUDIT_POOL_INSUFFICIENT",
    "citation": ("sections 10.4, 10.6, 11.1 + Stage 2 amendment A3; accepted as the "
                 "Tier-1 audit protocol by the investigator"),
}

# Section 10.6's audit-material list, verbatim in substance. A manifest whose cases
# do not span these is not the audit section 10.6 describes, so `coverage_report`
# counts them and `assert_manifest_is_complete` refuses a gap.
REQUIRED_MATERIAL: tuple[str, ...] = (
    "boundary_cases", "parameter_extremes", "realistic_malformed_outputs",
    "chat_preambles", "truncation", "empty_output", "unicode_normalisation",
    "zero_width_characters", "homoglyphs", "non_breaking_spaces", "smart_quotes",
    "combining_marks", "code_fences", "line_ending_variants",
)

# What a Tier-1 packet must never carry, each with the reason section 10.6 gives.
# `intended_class` is ours rather than the protocol's: showing a reviewer which
# answer the author expected is priming, and it would make the adjudication a
# confirmation of the authoring rather than an independent judgement.
FORBIDDEN_IN_PACKET: Mapping[str, str] = {
    "arm": "section 10.6 blinds adjudication to arm",
    "verdict": "section 10.6 blinds adjudication to the automatic verdict",
    "automatic_verdict": "likewise",
    "verifier_verdict": "likewise",
    "role": "section 10.6 blinds adjudication to constraint role",
    "constraint_id": "names the pair and the role",
    "verifier_id": "names the role through the verifier that measures it",
    "unit": "the verifier unit is the constraint id",
    "intended_class": "the class the author intended primes the reviewer",
    "truth_class": "likewise",
    "compliance": "a secondary form of the automatic verdict",
}


class Tier1AuditError(ValueError):
    """An audit manifest, packet or return that cannot be used as evidence."""


class AuditPoolInsufficient(Tier1AuditError):
    """A stratum has fewer than 72 usable cases after adjudication.

    A terminal state, not a prompt to author more. The frozen protocol forbids a
    post-review top-up, and section 10.6 forbids treating more data as a remedy:
    "collecting more confirmatory data is not a remedy for invalid measurement."
    The remedy is a fresh prospectively specified audit.
    """

    def __init__(self, report: Mapping[str, Any]):
        self.report = dict(report)
        short = ", ".join(f"{k}: {v['usable']} usable"
                          for k, v in sorted(report.items()))
        super().__init__(
            f"AUDIT_POOL_INSUFFICIENT - {len(report)} stratum(s) below 72 after "
            f"adjudication ({short}). The protocol permits no post-review top-up "
            "and no conditional extension; the remedy is a fresh prospectively "
            "specified audit")


class TruthClass(str, enum.Enum):
    """The two denominators section 10.4 requires, named as it names them."""

    TRULY_FAILS = "truly_fails"      # supports the false-PASS bound
    TRULY_PASSES = "truly_passes"    # supports the false-FAIL bound


TRUTH_CLASS_BY_BOUND = {TruthClass.TRULY_FAILS: "true_failures",
                        TruthClass.TRULY_PASSES: "true_passes"}


def units() -> tuple[str, ...]:
    """The six Tier-1 verifier units, in declaration order."""
    return tuple(rule.constraint_id for rule in pairs.rules())


@dataclass(frozen=True)
class AuditCase:
    """One authored audit example, with the provenance that makes it citable.

    `text` is the candidate model output a reviewer judges. `parameters` is the
    parameter realisation the constraint was instantiated at, because "produce
    exactly N items" cannot be judged without N.
    """
    case_id: str
    unit: str
    text: str
    parameters: Mapping[str, Any]
    intended_class: TruthClass
    material: tuple[str, ...]
    source_pool: str
    authored_by: str
    provenance: str

    def __post_init__(self):
        if not self.case_id or not self.source_pool or not self.authored_by:
            raise Tier1AuditError(
                f"{self.case_id or '<unnamed>'}: an audit case needs an id, the "
                "pool it came from and who authored it; an anonymous case cannot "
                "be traced back to the content procedure section 11.1 requires")
        if self.unit not in units():
            raise Tier1AuditError(
                f"{self.case_id}: {self.unit!r} is not one of the six Tier-1 "
                f"verifier units {units()}")
        if not isinstance(self.intended_class, TruthClass):
            raise Tier1AuditError(
                f"{self.case_id}: {self.intended_class!r} is not a TruthClass")
        if not self.material:
            raise Tier1AuditError(
                f"{self.case_id}: no material category recorded. Section 10.6 lists "
                "what audit material must include, and a case that claims none "
                "cannot be counted toward that coverage")
        unknown = sorted(set(self.material) - set(REQUIRED_MATERIAL))
        if unknown:
            raise Tier1AuditError(
                f"{self.case_id}: unknown material category {unknown}; section "
                f"10.6 lists {REQUIRED_MATERIAL}")
        if not self.provenance:
            raise Tier1AuditError(f"{self.case_id}: provenance is required")

    @property
    def case_hash(self) -> str:
        """Identity of the case as a MEASUREMENT OBJECT: what is judged, not its label.

        Excludes `case_id`, `authored_by` and `provenance`. Two cases carrying the
        same text at the same parameters in the same intended class are the same
        judgement however they are named, and including the id would make that
        collision invisible - `AuditManifest` catches it precisely because the hash
        ignores the label. It would also let a stratum be padded to 72 by copying
        one case under 72 ids, which is a denominator without evidence.

        Rewording the provenance is not a change to what is being judged, so that
        is excluded too.
        """
        return sha(["v19/tier1-audit-case", self.unit, self.text,
                    dict(self.parameters), self.intended_class.value,
                    sorted(self.material)])

    def state(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "unit": self.unit,
                "parameters": dict(self.parameters),
                "intended_class": self.intended_class.value,
                "material": sorted(self.material), "source_pool": self.source_pool,
                "authored_by": self.authored_by, "provenance": self.provenance,
                "case_hash": self.case_hash}


@dataclass(frozen=True)
class AuditManifest:
    """The complete set of cases for one audit run, in a deterministic order.

    Ordering is by (unit, intended class, case hash) rather than by insertion, so
    two people building the manifest from the same pool get the same manifest and
    the same packet ids. Insertion order would make the packet ids an artefact of
    how the pool happened to be iterated.
    """
    cases: tuple[AuditCase, ...]
    design: AuditDesign = AMENDED_TIER1_DESIGN
    pool_hashes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        seen = [c.case_id for c in self.cases]
        duplicated = sorted({c for c in seen if seen.count(c) > 1})
        if duplicated:
            raise Tier1AuditError(
                f"duplicate case id(s) {duplicated}; a case id identifies one "
                "judgement and cannot name two")
        hashes = [c.case_hash for c in self.cases]
        repeated = sorted({h for h in hashes if hashes.count(h) > 1})
        if repeated:
            colliding = sorted(c.case_id for c in self.cases
                               if c.case_hash in repeated)
            raise Tier1AuditError(
                f"{len(repeated)} distinct case hash(es) appear more than once, "
                f"across case ids {colliding[:6]}. Cases identical in text, "
                "parameters and intended class are the same judgement however they "
                "are named; counting them twice pads a denominator without adding "
                "evidence, and section 10.4 needs 72 pieces of evidence, not 72 "
                "rows")

    @property
    def ordered(self) -> tuple[AuditCase, ...]:
        return tuple(sorted(self.cases,
                            key=lambda c: (c.unit, c.intended_class.value,
                                           c.case_hash, c.case_id)))

    def for_unit(self, unit: str,
                 truth_class: TruthClass | None = None) -> tuple[AuditCase, ...]:
        return tuple(c for c in self.ordered
                     if c.unit == unit
                     and (truth_class is None or c.intended_class is truth_class))

    def counts(self) -> dict[str, dict[str, int]]:
        return {unit: {tc.value: len(self.for_unit(unit, tc))
                       for tc in TruthClass}
                for unit in units()}

    def coverage_report(self) -> dict[str, Any]:
        """Which of section 10.6's material categories the manifest actually spans."""
        seen: dict[str, int] = {name: 0 for name in REQUIRED_MATERIAL}
        for case in self.cases:
            for name in case.material:
                seen[name] += 1
        missing = sorted(name for name, n in seen.items() if n == 0)
        return {"by_category": dict(sorted(seen.items())),
                "missing": missing, "complete": not missing}

    @property
    def manifest_hash(self) -> str:
        return sha(["v19/tier1-audit-manifest", MANIFEST_ID,
                    self.design.design_hash,
                    [c.case_hash for c in self.ordered],
                    dict(sorted(self.pool_hashes.items()))])

    def state(self) -> dict[str, Any]:
        return {"manifest_id": MANIFEST_ID,
                "design": self.design.state(),
                "n_cases": len(self.cases),
                "counts": self.counts(),
                "coverage": self.coverage_report(),
                "pool_hashes": dict(sorted(self.pool_hashes.items())),
                "cases": [c.state() for c in self.ordered],
                "manifest_hash": self.manifest_hash}


def assert_manifest_is_complete(manifest: AuditManifest) -> AuditManifest:
    """Refuse a manifest the frozen protocol does not admit.

    Checked BEFORE anything is sent to a reviewer. Discovering a defect after 1,200
    candidates have been judged wastes every judgement: the protocol permits no
    top-up, so a fresh prospectively specified audit is the only remedy.

    Exactly `CANDIDATES_PER_CLASS`, not "at least". An under-authored stratum cannot
    reach 72 usable cases once mis-adjudicated candidates are discarded; an
    over-authored one would mean the authoring budget was not the frozen one, and
    the surplus would sit outside the hash-bound pool.
    """
    wrong: list[str] = []
    for unit in units():
        for truth_class in TruthClass:
            have = len(manifest.for_unit(unit, truth_class))
            if have != CANDIDATES_PER_CLASS:
                wrong.append(f"{unit}/{truth_class.value}: {have} candidates, the "
                             f"protocol fixes {CANDIDATES_PER_CLASS}")
    if wrong:
        raise Tier1AuditError(
            f"{len(wrong)} unit/class stratum(s) are not the frozen authoring "
            "budget:\n  " + "\n  ".join(wrong))

    assert_no_case_serves_two_units(manifest)

    coverage = manifest.coverage_report()
    if not coverage["complete"]:
        raise Tier1AuditError(
            f"the manifest spans no case for material category/categories "
            f"{coverage['missing']}. Section 10.6 states what audit material "
            "includes, and those categories are where verifiers actually break")
    return manifest


def assert_no_case_serves_two_units(manifest: AuditManifest) -> None:
    """A case may serve only one verifier unit.

    Checked on the content rather than on `case_hash`, which includes the unit: the
    same response at the same parameters registered under two units would hash
    differently and slip through. Reuse would halve the authoring budget and
    correlate two units' error estimates that section 10.4 certifies independently.
    """
    # Keyed on (unit, case_id) TUPLES, not on a joined string: a constraint id is
    # itself colon-separated ("v19:p1.target.exact_bullet_count"), so splitting a
    # joined key on the first colon collapsed every unit to "v19" and the check
    # could never fire. The tests caught it.
    seen: dict[str, list[tuple[str, str]]] = {}
    for case in manifest.ordered:
        content = sha(["v19/tier1-audit-content", case.text,
                       dict(case.parameters)])
        seen.setdefault(content, []).append((case.unit, case.case_id))
    shared = {content: where for content, where in seen.items()
              if len({unit for unit, _ in where}) > 1}
    if shared:
        examples = sorted(f"{unit}:{case_id}" for where in shared.values()
                          for unit, case_id in where)[:6]
        raise Tier1AuditError(
            f"{len(shared)} case content(s) appear under more than one verifier "
            f"unit, for example {examples}. A case may serve only one unit: reuse "
            "correlates error estimates that section 10.4 certifies individually")


# ------------------------------------------------------------ the review packets

def packet(case: AuditCase, index: int) -> dict[str, Any]:
    """The one question a Tier-1 reviewer is asked about one case.

    Deliberately NOT "did the verifier get this right?" - that would show the
    automatic verdict section 10.6 blinds. The reviewer establishes ground truth
    and never sees what the machine said.
    """
    rule = _rule_for(case.unit)
    return {
        "packet_id": sha(["v19/tier1-packet", MANIFEST_ID, case.case_hash])[:32],
        "ordinal": index,
        "protocol": "v19",
        "citation": "section 10.4; blinding per section 10.6",
        "question": (
            "Does the response below satisfy the stated requirement, as a careful "
            "reader would judge it? Answer about the requirement only - not about "
            "whether the response is good, helpful, or well written, and not about "
            "any other requirement it might also be under."),
        "requirement": rule.statement,
        "parameter_realisation": {k: v for k, v in case.parameters.items()
                                  if not k.endswith(("_hash", "_id"))},
        "response": case.text,
        "response_hash": case.case_hash,
        "answer_schema": {
            "packet_id": "copy it back unchanged",
            "reviewer_id": "your identifier",
            "satisfied": "true or false; a boolean, not a word",
            "rationale": "why, in your own words; required",
        },
        "caveats": [
            ("You are establishing what is TRUE of this response. You are not "
             "checking a machine's answer, and you are not shown one."),
            ("The parameter values are not calibrated: the admissible set is a "
             "Stage 5 output. Judge the requirement at the values shown."),
        ],
    }


def _rule_for(unit: str):
    for rule in pairs.rules():
        if rule.constraint_id == unit:
            return rule
    raise Tier1AuditError(f"{unit!r} is not a Tier-1 verifier unit")


def assert_blinded(built: Mapping[str, Any]) -> Mapping[str, Any]:
    """No packet field may name the arm, the role, the verdict or the intended class."""
    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key in FORBIDDEN_IN_PACKET:
                    raise Tier1AuditError(
                        f"{path}.{key} leaks a field section 10.6 blinds: "
                        f"{FORBIDDEN_IN_PACKET[key]}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, Sequence) and not isinstance(node, str):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(built, "packet")
    text = repr(built)
    for marker in ("PASS", "FAIL", "truly_fails", "truly_passes", "target", "focal"):
        if marker in text:
            raise Tier1AuditError(
                f"the packet contains {marker!r}, which reveals a verdict, a "
                "constraint role or the class the author intended")
    for pair_id in pairs.PAIR_IDS:
        if f"v19:{pair_id}." in text:
            raise Tier1AuditError(
                f"the packet names {pair_id}'s constraint identifiers, which carry "
                "the pair and the role")
    return built


def packets(manifest: AuditManifest) -> tuple[Mapping[str, Any], ...]:
    """Every packet, blinded, in the manifest's deterministic order."""
    return tuple(assert_blinded(packet(case, index))
                 for index, case in enumerate(manifest.ordered, start=1))


def reviewer_bundle(manifest: AuditManifest) -> dict[str, Any]:
    """What a reviewer receives, plus the index that stays with the investigator."""
    built = packets(manifest)
    index = [{"packet_id": p["packet_id"], "case_id": c.case_id, "unit": c.unit,
              "intended_class": c.intended_class.value, "case_hash": c.case_hash}
             for p, c in zip(built, manifest.ordered, strict=True)]
    return {
        "protocol": "v19",
        "citation": "section 10.4; blinding per section 10.6",
        "manifest_hash": manifest.manifest_hash,
        "n_packets": len(built),
        "packets": list(built),
        "unblinding_index": index,
        "note": ("Send reviewers the 'packets' array ONLY. The unblinding index "
                 "maps a packet back to its unit and intended class and is for the "
                 "investigator; a reviewer who saw it would be primed."),
    }


# ------------------------------------------------------ the returned judgements

@dataclass(frozen=True)
class Judgement:
    """One reviewer's ground-truth answer about one case."""
    packet_id: str
    reviewer_id: str
    satisfied: bool
    rationale: str

    def __post_init__(self):
        if not self.packet_id or not self.reviewer_id:
            raise Tier1AuditError("a judgement names its packet and its reviewer")
        if not isinstance(self.satisfied, bool):
            raise Tier1AuditError(
                f"{self.packet_id}: 'satisfied' is {self.satisfied!r}. It must be a "
                "real boolean - 'yes', 1 and 'true' are refused, because a string "
                "that happens to be truthy is not a judgement")
        if not self.rationale.strip():
            raise Tier1AuditError(
                f"{self.packet_id}: a rationale is required. An unexplained "
                "judgement cannot be adjudicated against a disagreeing one")


@dataclass(frozen=True)
class AdjudicatedCase:
    """One case's established ground truth, with the reviewers who established it."""
    case_id: str
    unit: str
    adjudicated_class: TruthClass
    intended_class: TruthClass
    judgements: tuple[Judgement, ...]
    adjudication: Judgement | None
    unanimous: bool
    usable: bool = True
    unusable_because: str = ""

    @property
    def matched_intent(self) -> bool:
        """Whether the humans put the case where its author intended.

        Under the frozen protocol a case that did NOT is discarded rather than
        credited to the other class, so this is the retention test.
        """
        return self.usable and self.adjudicated_class is self.intended_class

    def state(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "unit": self.unit,
                "adjudicated_class": self.adjudicated_class.value,
                "intended_class": self.intended_class.value,
                "matched_intent": self.matched_intent,
                "usable": self.usable,
                "unusable_because": self.unusable_because,
                "unanimous": self.unanimous,
                "reviewers": [j.reviewer_id for j in self.judgements],
                "adjudicator": self.adjudication.reviewer_id
                if self.adjudication else None}


@dataclass(frozen=True)
class ReviewerPanel:
    """The three-person panel, frozen before review begins.

    The PROTOCOL fixes that there is a panel of three with two independent
    reviewers and one adjudicator; WHO they are is a fact about one audit run, so
    it is recorded here and hashed alongside the manifest rather than baked into
    the protocol decision.
    """
    reviewers: tuple[str, ...]
    adjudicator: str

    def __post_init__(self):
        if len(self.reviewers) != INDEPENDENT_REVIEWERS:
            raise Tier1AuditError(
                f"the protocol fixes {INDEPENDENT_REVIEWERS} independent reviewers, "
                f"the panel names {len(self.reviewers)}")
        if len(set(self.reviewers)) != len(self.reviewers):
            raise Tier1AuditError("a reviewer cannot occupy two seats")
        if not self.adjudicator:
            raise Tier1AuditError("the panel must name its adjudicator")
        if self.adjudicator in self.reviewers:
            raise Tier1AuditError(
                f"{self.adjudicator} is both an independent reviewer and the "
                "adjudicator; adjudicating one's own judgement is not adjudication")
        if len(set(self.reviewers) | {self.adjudicator}) != PANEL_SIZE:
            raise Tier1AuditError(       # pragma: no cover - implied by the above
                f"the panel must have {PANEL_SIZE} distinct members")

    @property
    def panel_hash(self) -> str:
        return sha(["v19/tier1-panel", sorted(self.reviewers), self.adjudicator])

    def state(self) -> dict[str, Any]:
        return {"reviewers": sorted(self.reviewers),
                "adjudicator": self.adjudicator, "panel_hash": self.panel_hash}


def _protocol_or_refuse(slots) -> Mapping[str, Any]:
    """The audit protocol decision, or a fail-closed explanation.

    Section 10.4 says the examples are "human-adjudicated" and never says by how
    many reviewers, nor how disagreement is resolved. Section 8.6's two-reviewers-
    plus-adjudicator rule is scoped to SEMANTIC REVIEW of compositions, not to this
    audit, so reusing it here would be an implementer inventing a protocol detail.
    """
    slot = slots["verifiers.tier1_audit_protocol"]
    if not slot.resolved:
        raise Tier1AuditError(
            "the Tier-1 audit protocol is not decided, so returned judgements "
            "cannot be adjudicated.\n"
            "  Section 10.4 requires 'human-adjudicated' examples and does not say "
            "how many reviewers judge each case, how disagreement is resolved, or "
            "how exactly 72 per class are reached when the class is only known "
            "after adjudication.\n"
            "  Section 8.6's two-plus-adjudicator rule governs semantic review of "
            "compositions and does not extend here by itself.\n"
            f"  Minimum decision required: {slot.rule}")
    return slot.get()


def ingest(manifest: AuditManifest, returned: Sequence[Any], slots,
           panel: ReviewerPanel) -> tuple[AdjudicatedCase, ...]:
    """Turn returned judgements into established ground truth, or refuse.

    Fail-closed at every step. A missing judgement is never read as agreement with
    the author's intent, an unknown packet is never ignored, and a case short of
    the required number of reviewers is never adjudicated by the reviewers who did
    answer.
    """
    protocol = _protocol_or_refuse(slots)
    required_reviewers = int(protocol["independent_reviewers"])

    by_packet = {p["packet_id"]: case
                 for p, case in zip(packets(manifest), manifest.ordered,
                                    strict=True)}

    grouped: dict[str, list[Judgement]] = {}
    for entry in returned:
        judgement = entry if isinstance(entry, Judgement) else _as_judgement(entry)
        if judgement.packet_id not in by_packet:
            raise Tier1AuditError(
                f"{judgement.packet_id} is not a packet in this manifest "
                f"({manifest.manifest_hash[:16]}). A judgement about an unknown "
                "packet is evidence about something else")
        grouped.setdefault(judgement.packet_id, []).append(judgement)

    missing = sorted(set(by_packet) - set(grouped))
    if missing:
        raise Tier1AuditError(
            f"{len(missing)} packet(s) have no judgement, first {missing[:3]}. A "
            "missing judgement is missing evidence and is never read as the class "
            "the author intended")

    out: list[AdjudicatedCase] = []
    for packet_id, judgements in grouped.items():
        case = by_packet[packet_id]
        reviewers = [j.reviewer_id for j in judgements]
        if len(set(reviewers)) != len(reviewers):
            raise Tier1AuditError(
                f"{case.case_id}: reviewer(s) judged it twice ({reviewers}). Two "
                "answers from one reviewer are not two independent reviews")
        stray = sorted({j.reviewer_id for j in judgements}
                       - set(panel.reviewers) - {panel.adjudicator})
        if stray:
            raise Tier1AuditError(
                f"{case.case_id}: judgement(s) from {stray}, who are not on the "
                f"frozen panel {panel.state()['reviewers']} + "
                f"{panel.adjudicator}. A judgement from outside the panel is not "
                "the evidence the protocol specifies")
        independent = [j for j in judgements if j.reviewer_id in panel.reviewers]
        adjudication = next((j for j in judgements
                             if j.reviewer_id == panel.adjudicator), None)
        if len(independent) != required_reviewers:
            raise Tier1AuditError(
                f"{case.case_id}: {len(independent)} independent judgement(s), the "
                f"protocol requires {required_reviewers}")
        answers = {j.satisfied for j in independent}
        unanimous = len(answers) == 1
        usable, unusable_because = True, ""
        if unanimous:
            satisfied = answers.pop()
        elif adjudication is not None:
            satisfied = adjudication.satisfied
        else:
            # The protocol's answer to an unresolved case: mark it unusable and
            # exclude it. NOT an exception, because a panel that could not agree is
            # an expected outcome of judging hard material - and NOT resolved by
            # preferring either reviewer, which would invent a ground truth.
            satisfied = False
            usable = False
            unusable_because = (
                "reviewers disagreed and no adjudication was returned, so no human "
                "ground truth was established; the case is excluded rather than "
                "resolved by preferring either answer")
        out.append(AdjudicatedCase(
            case_id=case.case_id, unit=case.unit,
            adjudicated_class=(TruthClass.TRULY_PASSES if satisfied
                               else TruthClass.TRULY_FAILS),
            intended_class=case.intended_class,
            judgements=tuple(independent), adjudication=adjudication,
            unanimous=unanimous, usable=usable,
            unusable_because=unusable_because))
    return tuple(sorted(out, key=lambda a: a.case_id))


def _as_judgement(entry: Any) -> Judgement:
    if not isinstance(entry, Mapping):
        raise Tier1AuditError(
            f"expected a Judgement or a mapping, got {type(entry).__name__}")
    missing = sorted({"packet_id", "reviewer_id", "satisfied", "rationale"}
                     - set(entry))
    if missing:
        raise Tier1AuditError(f"a returned judgement is missing {missing}")
    return Judgement(packet_id=str(entry["packet_id"]),
                     reviewer_id=str(entry["reviewer_id"]),
                     satisfied=entry["satisfied"],
                     rationale=str(entry["rationale"]))


# --------------------------------------------- deterministic post-hoc selection

@dataclass(frozen=True)
class Selection:
    """The 72 cases one stratum contributes, and what was set aside to get them."""
    unit: str
    truth_class: TruthClass
    selected: tuple[str, ...]
    usable: int
    discarded_cross_class: int
    discarded_unusable: int
    reserve_ignored: int

    def state(self) -> dict[str, Any]:
        return {"unit": self.unit, "truth_class": self.truth_class.value,
                "selection_rule": SELECTION_ID,
                "n_selected": len(self.selected),
                "usable": self.usable,
                "discarded_cross_class": self.discarded_cross_class,
                "discarded_unusable": self.discarded_unusable,
                "reserve_ignored": self.reserve_ignored,
                "selected": list(self.selected)}


def select(manifest: AuditManifest, adjudicated: Sequence[AdjudicatedCase],
           size: int = 72) -> dict[tuple[str, str], Selection]:
    """Take the first `size` retained cases per stratum, in frozen manifest order.

    The order is `AuditManifest.ordered` - (unit, intended class, case hash, case
    id) - fixed by the manifest hash before any reviewer saw anything, and a
    function of case content only. It therefore cannot respond to a verifier
    verdict, which is what makes this selection prospective rather than the
    conditional selection amendment A3 forbids.

    Retention is strict: a case is kept only if it is usable AND its adjudicated
    class matches its intended class. There is no cross-crediting - a candidate
    authored as truly-passing and adjudicated as failing is discarded, not moved.

    Raises `AuditPoolInsufficient` if any stratum falls short. It does not report
    how many more cases would be needed, because authoring them after seeing the
    reviews is exactly what the protocol forbids.
    """
    by_case = {a.case_id: a for a in adjudicated}
    out: dict[tuple[str, str], Selection] = {}
    short: dict[str, Any] = {}
    for unit in units():
        for truth_class in TruthClass:
            ordered = manifest.for_unit(unit, truth_class)
            retained, unusable, cross = [], 0, 0
            for case in ordered:                      # frozen manifest order
                verdict = by_case.get(case.case_id)
                if verdict is None:
                    raise Tier1AuditError(
                        f"{case.case_id} is in the manifest but was not "
                        "adjudicated; a case with no human judgement is missing "
                        "evidence, not a discard")
                if not verdict.usable:
                    unusable += 1
                elif not verdict.matched_intent:
                    cross += 1
                else:
                    retained.append(case.case_id)
            key = (unit, truth_class.value)
            if len(retained) < size:
                short[f"{unit}/{truth_class.value}"] = {
                    "usable": len(retained), "required": size,
                    "discarded_cross_class": cross,
                    "discarded_unusable": unusable}
                continue
            out[key] = Selection(
                unit=unit, truth_class=truth_class,
                selected=tuple(retained[:size]), usable=len(retained),
                discarded_cross_class=cross, discarded_unusable=unusable,
                reserve_ignored=len(retained) - size)
    if short:
        raise AuditPoolInsufficient(short)
    return out


# ------------------------------------------------ scoring against the A3 design

def certify_unit(unit: str, selection: Mapping[tuple[str, str], Selection],
                 adjudicated: Sequence[AdjudicatedCase],
                 verifier_verdicts: Mapping[str, bool],
                 design: AuditDesign = AMENDED_TIER1_DESIGN) -> TierCertificate:
    """One unit's Tier-1 certificate over exactly the selected cases.

    `verifier_verdicts` maps case id to what the verifier said (True = PASS). The
    error counted in each class is the disagreement with established human truth: a
    false PASS among cases that truly fail, a false FAIL among cases that truly
    pass.

    Only selected cases contribute. Cases discarded for cross-class adjudication or
    marked unusable are excluded before the bound is computed, and the reserve
    beyond 72 is ignored - so the denominator is exactly 72 and A3's design check
    has nothing to reject.
    """
    by_case = {a.case_id: a for a in adjudicated}
    counts: dict[TruthClass, tuple[int, int]] = {}
    for truth_class in TruthClass:
        chosen = selection[(unit, truth_class.value)].selected
        missing = sorted(set(chosen) - set(verifier_verdicts))
        if missing:
            raise Tier1AuditError(
                f"{unit}: no verifier verdict recorded for {missing[:3]}; a case "
                "with no machine verdict cannot contribute to a conditional error "
                "rate")
        errors = sum(
            1 for case_id in chosen
            if verifier_verdicts[case_id]
            is not (by_case[case_id].adjudicated_class is TruthClass.TRULY_PASSES))
        counts[truth_class] = (errors, len(chosen))
    false_passes, true_failures = counts[TruthClass.TRULY_FAILS]
    false_fails, true_passes = counts[TruthClass.TRULY_PASSES]
    return tier1_certificate_under(
        design, unit,
        false_passes=false_passes, true_failures=true_failures,
        false_fails=false_fails, true_passes=true_passes)


def certify_all(manifest: AuditManifest, adjudicated: Sequence[AdjudicatedCase],
                verifier_verdicts: Mapping[str, bool],
                design: AuditDesign = AMENDED_TIER1_DESIGN) -> dict[str, Any]:
    """The record `verifiers.tier1_reliability` expects, over the selected cases."""
    selection = select(manifest, adjudicated, size=design.n_per_truth_class)
    return {unit: certify_unit(unit, selection, adjudicated, verifier_verdicts,
                               design).describe()
            for unit in units()}
