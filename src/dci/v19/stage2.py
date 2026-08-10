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

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dci.v19 import parsing, reliability, verifiers
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


def certify_verifiers(slots: SlotTable, *,
                      mutation_counts: Mapping[str, int] | None = None
                      ) -> Certification:
    """Every section 14.2 verifier requirement, evaluated against the registry.

    `mutation_counts` maps constraint template id to the number of boundary
    mutations executed. Passing `None` is not the same as passing an empty
    mapping: `None` means no mutation evidence was offered at all, and both fail.
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

    findings.append(_mutation_finding(mutation_counts))
    return Certification(findings=tuple(findings))


def _bundle_finding(policy: Any) -> Finding:
    citation = "section 14.2 / Appendix I"
    requirement = ("every declared target and focal constraint has a v19 verifier "
                   "whose semantics are bound to a hash")
    try:
        resolved = policy if isinstance(policy, parsing.ListPolicy) else None
        if resolved is None:
            return Finding(requirement, citation, False,
                           f"the frozen list policy is {type(policy).__name__}, "
                           "not a ListPolicy, so no bundle can be built from it")
        built = verifiers.assert_bundle_is_complete(resolved)
    except (verifiers.VerifierContractError, TypeError) as error:
        return Finding(requirement, citation, False, str(error))
    return Finding(requirement, citation, True,
                   f"{len(built)} verifiers, bundle hash "
                   f"{verifiers.bundle_hash(resolved)}")


def _mutation_finding(counts: Mapping[str, int] | None) -> Finding:
    requirement = (f"each constraint template has at least "
                   f"{MUTATIONS_PER_TEMPLATE} automated boundary mutations")
    citation = "section 8.7"
    if counts is None:
        return Finding(requirement, citation, False,
                       "no mutation evidence was offered; section 8.7 requires it "
                       "per template, and an absent count is not a zero-defect "
                       "result")
    from dci.v19 import pairs
    required = [rule.constraint_id for rule in pairs.rules()]
    short = {cid: counts.get(cid, 0) for cid in required
             if counts.get(cid, 0) < MUTATIONS_PER_TEMPLATE}
    if short:
        return Finding(requirement, citation, False,
                       f"{len(short)} template(s) below the floor: "
                       + ", ".join(f"{cid}={n}" for cid, n in sorted(short.items())))
    return Finding(requirement, citation, True,
                   f"all {len(required)} templates at or above the floor")


def assert_verifiers_certified(slots: SlotTable, *,
                               mutation_counts: Mapping[str, int] | None = None
                               ) -> Certification:
    """Fail closed unless Stage 2's verifier half is certified.

    This is what a dependent stage calls. It reports every outstanding
    requirement at once with its citation, because discovering them one exception
    at a time is how a dependency order stops being mandatory.
    """
    report = certify_verifiers(slots, mutation_counts=mutation_counts)
    if report.certified:
        return report
    lines = [("Stage 2 verifier certification is incomplete: "
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
         "open_questions": dict(parsing.UNDETERMINED_BY_PREREGISTRATION),
         "minimum_decision": ("sign one ListPolicy; "
                              "INHERITED_MARKER_POLICY is the candidate closest "
                              "to the inherited behaviour")},
        {"decision": "verifiers.p1.ordering_depth",
         "governing_text": ("section 6.1 lists ordering depth among the "
                            "family-specific parameter quantities; pairs.PAIR_1 "
                            "declares it as the focal parameter"),
         "what_is_recoverable": "nothing; the protocol never defines it",
         "open_questions": {"domain": "what the parameter ranges over, and its "
                                      "easier/harder direction for the section "
                                      "6.2 ordered grid"},
         "minimum_decision": ("state the domain and the monotone direction so "
                              "Stage 5 has at most five admissible settings to "
                              "calibrate")},
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
