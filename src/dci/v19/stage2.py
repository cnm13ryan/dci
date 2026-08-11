"""Stage 2 certification: what must be true before dependent measurement runs.

Four things are deliberately distinct, and section 14.2 depends on all four:

    code exists  !=  artifact certified  !=  slot frozen  !=  stage READY

`dci.v19.verifiers` makes the first true. This module decides the second, and it
does so by reading the registry rather than by inspecting itself: a verifier
bundle can be complete, hashed and exhaustively tested and still not be certified,
because the Pair 1 parsing semantics and the reliability interval are scientific
decisions the preregistration leaves open.

The report lists every requirement with the text that makes it one, so a failed
certification names what is missing instead of returning False.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dci.v19 import ordering, parsing, reliability, verifiers
from dci.v19.resolution import SlotTable

# Section 8.7: "Each constraint template also receives at least 1,000 automated
# boundary mutations covering applicable off-by-one, duplication, omission,
# forbidden-item, ordering, formatting, Unicode, and parser-edge cases."
MUTATIONS_PER_TEMPLATE = 1_000


@dataclass(frozen=True)
class Finding:
    """One Stage 2 requirement, and whether it currently holds."""
    requirement: str
    citation: str
    satisfied: bool
    detail: str

    def describe(self) -> dict[str, Any]:
        return {"requirement": self.requirement, "citation": self.citation,
                "satisfied": self.satisfied, "detail": self.detail}


@dataclass(frozen=True)
class Certification:
    """The Stage 2 verifier-certification result, fail-closed by construction."""
    findings: tuple[Finding, ...]
    bundle_hash: str = ""

    @property
    def certified(self) -> bool:
        return bool(self.findings) and all(f.satisfied for f in self.findings)

    @property
    def outstanding(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if not f.satisfied)

    def describe(self) -> dict[str, Any]:
        return {"certified": self.certified,
                "bundle_hash": self.bundle_hash,
                "n_outstanding": len(self.outstanding),
                "findings": [f.describe() for f in self.findings]}


def _slot_finding(slots: SlotTable, name: str, requirement: str,
                  citation: str) -> Finding:
    slot = slots[name]
    if slot.resolved:
        return Finding(requirement, citation, True,
                       f"{name} is {slot.resolution.value}, frozen by "
                       f"{slot.frozen_by!r}")
    return Finding(requirement, citation, False,
                   f"{name} is {slot.resolution.value} [{slot.status}]; produced "
                   f"by: {slot.rule}")


def certify_verifiers(slots: SlotTable) -> Certification:
    """Every section 14.2 verifier requirement, evaluated against the registry.

    Mutation evidence is no longer a parameter. The audit found the caller able to
    assert it - `certify_verifiers(slots, mutation_counts={...})` passed with any
    numbers the caller liked - so the evidence is read from the registry slot,
    where its typed domain has already refused a malformed record.
    """
    findings = [
        _slot_finding(
            slots, "verifiers.p1.list_policy",
            "the Pair 1 list-parsing semantics are frozen by a signed decision",
            "sections 4.1, 4.2, 14.2"),
        _slot_finding(
            slots, "verifiers.p1.ordering_depth",
            "the Pair 1 focal parameter has a declared domain",
            "sections 4.1, 6.1, 14.5"),
        _slot_finding(
            slots, "verifiers.inherited_reuse_decision",
            "the Pair 2/3 hash and semantic audit has been dispositioned",
            "sections 10.6, 14.2"),
        _slot_finding(
            slots, "verifiers.binomial_interval_implementation",
            "the two-sided binomial reliability interval is frozen",
            "section 10.4"),
        _slot_finding(
            slots, "verifiers.tier1_audit_design",
            "the Tier-1 audit design - sample size, error budget, and whether the "
            "sample may be extended - is fixed prospectively",
            "section 10.4 + amendment A3, register row D45"),
    ]

    policy_slot = slots["verifiers.p1.list_policy"]
    if policy_slot.resolved:
        findings.append(_bundle_finding(policy_slot.get()))
    else:
        findings.append(Finding(
            "every declared target and focal constraint has a v19 verifier whose "
            "semantics are bound to a hash",
            "section 14.2 / Appendix I", False,
            "not evaluable: the Pair 1 verifier specification hashes contain the "
            "list-policy hash, so the bundle has no identity until the policy is "
            "frozen. The implementation exists and is tested; it is the "
            "measurement decision under it that is missing"))

    findings.append(_battery_finding(slots))
    findings.append(_slot_finding(
        slots, "verifiers.tier1_reliability",
        "each of the six target and focal verifier units is certified against the "
        "5% Tier-1 conditional error ceiling on 72 human-adjudicated labels per "
        "truth class, with zero observed errors",
        "section 10.4 + amendment A3"))
    return Certification(findings=tuple(findings))


def _bundle_finding(policy_state: Any) -> Finding:
    """The bundle, built from the grammar the registry actually froze.

    The frozen value is the grammar's canonical STATE, not a live object: a
    registry value must have a reproducible serialisation, and `sha` refuses
    anything with no canonical form rather than hashing object identity. So the
    state is compared with the implemented grammar rather than used as one. A
    state that does not match means the registry and the parser disagree, which is
    the one case where a complete bundle would still be the wrong evidence.
    """
    citation = "section 14.2 / Appendix I"
    requirement = ("every declared target and focal constraint has a v19 verifier "
                   "whose semantics are bound to a hash")
    canonical = parsing.CANONICAL_LIST_POLICY
    if policy_state != canonical.state():
        return Finding(requirement, citation, False,
                       "the frozen list grammar does not match the implemented one, "
                       "so the bundle would be built under semantics the registry "
                       "did not freeze")
    try:
        built = verifiers.assert_bundle_is_complete(canonical)
    except (verifiers.VerifierContractError, TypeError) as error:
        return Finding(requirement, citation, False, str(error))
    return Finding(requirement, citation, True,
                   f"{len(built)} verifiers, bundle hash "
                   f"{verifiers.bundle_hash(canonical)}")


def _battery_finding(slots: SlotTable) -> Finding:
    """Section 8.7 evidence, read from the registry rather than from the caller.

    The domain on `verifiers.boundary_mutations` has already refused a record that
    is not a per-constraint mapping carrying a sha-256 records_hash, a count at or
    above the floor, and an equal number of distinct texts. What this adds is that
    the record must EXIST and must cover every declared constraint: an unfrozen
    battery is not part of the artifact trail Appendix J archives.

    Whether the recorded hashes match a battery the harness regenerates is a
    separate check, and it lives with the harness. Section 8.7's "each constraint
    template" is read as each declared CONSTRAINT, the stricter of the two
    readings the earlier code used inconsistently.
    """
    from dci.v19 import pairs
    required = [rule.constraint_id for rule in pairs.rules()]
    requirement = (f"each of the {len(required)} constraint templates has at least "
                   f"{MUTATIONS_PER_TEMPLATE} distinct boundary mutations recorded")
    citation = "section 8.7"
    slot = slots["verifiers.boundary_mutations"]
    if not slot.resolved:
        return Finding(
            requirement, citation, False,
            f"{slot.name} is {slot.resolution.value}: an unfrozen battery is not "
            "part of the artifact trail, and an absent count is not a zero-defect "
            f"result. Produced by: {slot.rule}")
    recorded = slot.get()
    missing = sorted(set(required) - set(recorded))
    if missing:
        return Finding(requirement, citation, False,
                       f"no battery evidence for template(s) {missing}")
    stray = sorted(set(recorded) - set(required))
    if stray:
        return Finding(requirement, citation, False,
                       f"battery evidence for undeclared template(s) {stray}")
    return Finding(requirement, citation, True,
                   f"{len(required)} template batteries recorded, each at or above "
                   f"{MUTATIONS_PER_TEMPLATE} distinct mutations")


def certify_satisfiability(slots: SlotTable) -> Certification:
    """Every section 8.6 satisfiability requirement, against the registry."""
    findings = [
        _slot_finding(
            slots, "satisfiability.encoding_map",
            "the canonical structured encoding and the abstract feature "
            "projection are frozen", "sections 8.6, 14.2"),
        _slot_finding(
            slots, "satisfiability.solver_identity",
            "the solver's name and exact version are recorded", "section 8.6"),
        _slot_finding(
            slots, "satisfiability.witness_constructor",
            "the deterministic witness constructor is frozen", "section 8.6"),
        _slot_finding(
            slots, "satisfiability.review_trigger",
            "the semantic-review trigger is demonstrated: it fires on incomplete "
            "coverage, stays silent on complete coverage, rejects a review of the "
            "wrong witness, and requires adjudication of disagreement",
            "section 14.2; section 8.6"),
        _review_boundary_finding(),
        _solver_finding(),
        _battery_regeneration_finding(slots),
    ]
    return Certification(findings=tuple(findings))


def _battery_regeneration_finding(slots: SlotTable) -> Finding:
    """Run the harness and compare it with what was recorded.

    This is deliberately SEPARATE from the `boundary_mutations` domain and from
    `_battery_finding`, and the separation is the point.

    The domain states what a section 8.7 record must look like. Its meaning has to
    stay stable, because the domain name is part of the slot's declaration
    fingerprint - a domain that silently tightened between two commits would leave
    the slot with a fingerprint that no longer described it. So the domain checks
    the record schema and nothing else, in both halves of this stack.

    Whether the recorded hashes match a battery the harness actually produces is a
    different question, and it can only be asked where the harness exists. That is
    here. A well-formed record with invented hashes passes the domain and fails
    this check, which is exactly the split that keeps a stable schema from being a
    weak one.
    """
    from dci.v19.mutation import (
        MUTATIONS_PER_TEMPLATE as FLOOR,
    )
    from dci.v19.mutation import (
        frozen_battery_evidence,
    )
    requirement = ("the recorded boundary-mutation evidence matches a battery the "
                   "harness regenerates, so it was generated rather than asserted")
    citation = "section 8.7"
    slot = slots["verifiers.boundary_mutations"]
    if not slot.resolved:
        return Finding(requirement, citation, False,
                       f"{slot.name} is {slot.resolution.value}: there is nothing "
                       "to compare a regenerated battery against")
    regenerated = frozen_battery_evidence()
    short = sorted(name for name, row in regenerated.items()
                   if row["n_mutations"] < FLOOR
                   or row["distinct_texts"] != row["n_mutations"])
    if short:
        return Finding(requirement, citation, False,
                       f"the harness itself produces insufficient evidence for "
                       f"{short}")
    recorded = slot.get()
    mismatched = sorted(name for name, row in regenerated.items()
                        if recorded.get(name, {}).get("records_hash")
                        != row["records_hash"])
    if mismatched:
        return Finding(requirement, citation, False,
                       f"the recorded battery for {mismatched} does not match the "
                       "battery the harness regenerates, so the evidence was "
                       "asserted rather than generated")
    return Finding(requirement, citation, True,
                   f"{len(regenerated)} template batteries regenerated and matched, "
                   f"each at or above {FLOOR} distinct mutations")


def _review_boundary_finding() -> Finding:
    """Moving the reviews to Stage 10 must not let anything escape review.

    The boundary correction is only sound if certification still refuses a
    composition with an incompletely covered clause and no review. That is
    demonstrated here rather than argued, because it is the single load-bearing
    claim the correction rests on.
    """
    from dci.v19.parsing import CANONICAL_LIST_POLICY
    from dci.v19.review_trigger import unreviewable_certification_is_impossible
    requirement = ("a composition with an incompletely covered clause cannot be "
                   "certified without a passing review, so deferring the reviews "
                   "to Stage 10 defers WHEN they are checked and not WHETHER")
    citation = "sections 8.6, 14.2, 14.10"
    if not unreviewable_certification_is_impossible(CANONICAL_LIST_POLICY):
        return Finding(requirement, citation, False,
                       "a composition with an uncovered clause certified with no "
                       "review, so the Stage 2 / Stage 10 division would let a "
                       "composition through unreviewed")
    return Finding(requirement, citation, True,
                   "certification refuses with Outcome.REVIEW_REQUIRED")


def _solver_finding() -> Finding:
    """A missing solver is missing required output, never a skipped step."""
    requirement = "a frozen solver is available to decide the conjunction"
    citation = "section 8.6"
    from dci.v19 import solver
    try:
        name, version = solver.solver_identity()
    except solver.SolverUnavailable as error:
        return Finding(requirement, citation, False, str(error))
    return Finding(requirement, citation, True, f"{name} {version}")


def certify_stage2(slots: SlotTable) -> Certification:
    """Both halves of Stage 2 as one report: verifiers and satisfiability."""
    verifier_half = certify_verifiers(slots)
    satisfiability_half = certify_satisfiability(slots)
    return Certification(
        findings=verifier_half.findings + satisfiability_half.findings)


def assert_stage2_certified(slots: SlotTable) -> Certification:
    """Fail closed unless BOTH halves of Stage 2 are certified.

    This is what a dependent stage calls. It reports every outstanding
    requirement at once with its citation, because discovering them one exception
    at a time is how a dependency order stops being mandatory.
    """
    report = certify_stage2(slots)
    if report.certified:
        return report
    lines = [("Stage 2 certification is incomplete: "
              f"{len(report.outstanding)} of {len(report.findings)} "
              "requirements are unmet.")]
    for finding in report.outstanding:
        lines.append(f"  - {finding.requirement} ({finding.citation})")
        lines.append(f"      {finding.detail}")
    raise verifiers.VerifierContractError("\n".join(lines))


def open_scientific_decisions() -> tuple[dict[str, Any], ...]:
    """The Stage 2 questions the preregistration does not answer.

    Reported rather than resolved. Each row names the exact governing text, what
    the repository can recover, and the minimum decision required, so the blocker
    list in a completion report is derived from the code rather than retyped.
    """
    recovery = reliability.recover_inherited_interval()
    return (
        {"decision": "verifiers.p1.list_policy",
         "governing_text": ("section 4.1 table row 1 and section 4.2 fix the two "
                            "Pair 1 statements and the coupling risk; section 14.2 "
                            "requires the support to be built"),
         "what_is_recoverable": ("dci.verifiers.rules.LIST_MARKER, already "
                                 "load-bearing because split_sentences strips it; "
                                 "it settles the marker set and three other "
                                 "fields and none of the remaining five"),
         "open_questions": {},
         "resolved_by_amendment": dict(parsing.RESOLVED_BY_AMENDMENT),
         "minimum_decision": ("sign one ListPolicy; "
                              "CANONICAL_LIST_POLICY is the candidate closest "
                              "to the inherited behaviour")},
        {"decision": "verifiers.p1.ordering_depth",
         "governing_text": ("section 6.1 lists ordering depth among the "
                            "family-specific parameter quantities; pairs.PAIR_1 "
                            "declares it as the focal parameter"),
         "what_is_recoverable": "nothing; the protocol never defines it",
         "open_questions": {},
         "resolved_by_amendment": {
             "construct": ordering.DEFINITION,
             "generator": ordering.DECISION["generator_form"],
             "harder_direction": ordering.DECISION["harder_direction"],
             "grid": ordering.DECISION["grid_rule"]},
         "minimum_decision": ("state the construct, its admissible range and the "
                              "monotone direction; the ordered grid itself is the "
                              "Stage 5 calibration output D6")},
        {"decision": "verifiers.inherited_reuse_decision",
         "governing_text": ("section 14.2 permits Pair 2/3 reuse only after a "
                            "hash and semantic audit; section 10.6 requires a "
                            "demonstrated defect to be repaired and re-audited "
                            "before freeze"),
         "what_is_recoverable": ("the audit itself: the inherited semantics are "
                                 "fully recoverable and are hashed by "
                                 "verifiers.inherited_segmentation()"),
         "open_questions": {
             "pair_2_uniqueness": ("a zero-width space or a homoglyph splits a "
                                   "repeated word into distinct ASCII tokens, so "
                                   "the focal rule passes while a word repeats"),
             "pair_2_mandatory_words": ("a mandatory word containing a non-ASCII "
                                        "letter can never be matched, making that "
                                        "parameter realisation impossible rather "
                                        "than failing"),
             "pair_3_segmentation": ("the frozen segmentation strips list markers "
                                     "and treats each line as a segment, so a "
                                     "bullet list of N lines scores as exactly N "
                                     "sentences and Pair 1 shares the span")},
         "minimum_decision": ("reuse unchanged with the scope restriction stated, "
                              "or repair the tokenisation and re-audit; either "
                              "way record it against a new scientific hash")},
        {"decision": "verifiers.binomial_interval_implementation",
         "governing_text": ("section 10.4: recover and freeze the exact two-sided "
                            "binomial interval implementation used by the "
                            "inherited gate, or resolve its choice as a "
                            "pre-freeze decision"),
         "what_is_recoverable": recovery["identified_implementation"],
         "open_questions": {"conflict": recovery["conflict"],
                            "register_row": ("section 10.4 cites D9, which is the "
                                             "construction bootstrap; no register "
                                             "row covers this decision")},
         "minimum_decision": ("freeze 'wilson_score', preserving the 73 and 876 "
                              "counts section 10.4 states, or 'clopper_pearson', "
                              "satisfying 'exact' and changing them to 72 and "
                              "864; and add the missing register row")},
    )


# Kept as the name dependent stages already call. It now covers both halves, because
# certifying the verifiers while the satisfiability evidence is absent was never a
# meaningful state.
assert_verifiers_certified = assert_stage2_certified
