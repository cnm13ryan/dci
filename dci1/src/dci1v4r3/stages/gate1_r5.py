"""Gate 1 under §10.7-R5: §10.2 plus the deterministic-measurement architecture.

`stages.gate1` is left exactly as it was. It carries the rule §18 stage 4
registered before amendment R5 -- §10.2 **plus §10.3 or §10.4** -- and the
record of what that rule returned is history that R5 does not rewrite. This
module carries the amended rule beside it, so a reader can run either and see
which one a record was decided under.

**The ten conditions are the amendment's, verbatim in structure**, and none of
them is a reviewer-agreement threshold. Human and autorater evidence is carried
in the record because it is real and was expensive, and it is carried under a
key that says what it is: `supplementary_diagnostics`. It can neither pass nor
fail this gate. That is the whole point of the amendment and it is enforced
here rather than promised: `gate1_r5_payload` takes the diagnostics as an
opaque mapping and never reads a number out of it.

**What a pass under this rule may be called.** `measurement_basis =
deterministic_measurement_validated`, which is not `human_validated`, so
§10.5's scope sentence attaches and is written into the record by construction.
A pass here is never described as a retroactive pass of §10.3 or §10.4; both
keep their own outcomes, and the record carries them.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError, TerminalStatus
from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r3.protocol import constants as C
from dci1v4r3.stages.mutation import mutation_hash, run_mutation_validation
from dci1v4r3.stages.specification import (
    run_specification_audit, specification_hash, wording_review, wordings_hash,
)
from dci1v4r3.verifiers import verifier_source_hash
from dci1v4r3.verifiers.boundary import instrument_population

__all__ = ["AMENDMENT_TEXT_FIELDS", "amendment_hash", "collect_r5_evidence",
           "gate1_r5_payload"]

#: The fields of §10.7-R5 that define the rule. Hashed into every record so
#: that a later reading of "which rule was this decided under?" is answered by
#: the artifact and not by a document that may have moved.
AMENDMENT_TEXT_FIELDS = {
    "section": "10.7-R5",
    "title": "Deterministic-measurement validation",
    "adopted": "2026-08-21",
    "supersedes": ("§18 stage 4: §10.2 for every verifier in the final "
                   "instrument population, plus §10.3 or §10.4"),
    "replaces_it_with": ("§10.2 for every verifier in the final instrument "
                         "population, plus §10.7-R5 A-E"),
    "reclassifies": ("§10.3, §10.4, §10.4-R and §10.4-R2 as supplementary "
                     "semantic diagnostics; their recorded outcomes stand and "
                     "neither is described as having succeeded"),
    "measurement_basis": C.MEASUREMENT_BASIS_R5,
    "scope_sentence_attaches": True,
    "conditions": (
        "1 every family and form carries a complete formal specification",
        "2 no unresolved prose-to-predicate ambiguity",
        "3 the primary verifier is deterministic",
        "4 the independent reimplementation agrees exactly, zero unexplained "
        "disagreement",
        "5 boundary, adversarial and Unicode tests pass and the boundary "
        "corpus meets its registered minimum",
        "6 mutation tests show sensitivity to every meaningful defect class, "
        "with every non-applicability explained",
        "7 satisfiability and non-entailment witnesses pass",
        "8 wording equivalence passes and no wording is genuinely ambiguous "
        "or requires correction",
        "9 the verifier hash and the wording hash are bound and match",
        "10 lifecycle and provenance integrity passes",
    ),
    "no_reviewer_threshold": ("no human or autorater agreement threshold "
                              "appears in this rule, in either direction"),
}


def amendment_hash() -> str:
    return sha_text(canonical_json(AMENDMENT_TEXT_FIELDS))


def collect_r5_evidence(*, specification: Mapping[str, Any] | None = None,
                        mutation: Mapping[str, Any] | None = None,
                        wordings: Mapping[str, Any] | None = None
                        ) -> dict[str, Any]:
    """A, A' and D. B, C and E come from `gate1.collect_evidence`."""
    specification = (dict(specification) if specification is not None
                     else run_specification_audit())
    mutation = (dict(mutation) if mutation is not None
                else run_mutation_validation())
    wordings = dict(wordings) if wordings is not None else wording_review()
    return {
        "specification_audit": specification,
        "mutation_validation": mutation,
        "wording_review": wordings,
        "specification_hash": specification_hash(specification),
        "mutation_hash": mutation_hash(mutation),
        "wordings_hash": wordings_hash(),
    }


def _provenance_failures(provenance: Mapping[str, Any]) -> list[str]:
    """Condition 10, read off the record the caller assembled."""
    problems: list[str] = []
    if not provenance.get("predecessor_verified"):
        problems.append("the predecessor stage record does not verify")
    if not provenance.get("carry_over_passed"):
        problems.append("the carry-over record does not hold")
    if not provenance.get("reserved_sets_unspent"):
        problems.append("a reserved topic set has been spent")
    if not provenance.get("producing_commit"):
        problems.append("no producing commit is recorded")
    return problems


def gate1_r5_payload(*, evidence: Mapping[str, Any],
                     r5_evidence: Mapping[str, Any],
                     provenance: Mapping[str, Any],
                     supplementary_diagnostics: Mapping[str, Any] | None = None,
                     measurement_basis: str = C.MEASUREMENT_BASIS_R5,
                     sealed_set: Mapping[str, Any] | None = None,
                     identification_statuses: Sequence[str] = ()
                     ) -> dict[str, Any]:
    """The amended Gate 1. Ten conditions, none of them about a reviewer."""
    if measurement_basis != C.MEASUREMENT_BASIS_R5:
        raise ProtocolError(
            f"§10.7-R5 writes {C.MEASUREMENT_BASIS_R5!r} and nothing else; "
            f"{measurement_basis!r} belongs to a different pathway and must "
            "be decided by the rule that registers it")

    specification = r5_evidence["specification_audit"]
    mutation = r5_evidence["mutation_validation"]
    wordings = r5_evidence["wording_review"]
    failures: list[dict[str, str]] = []

    def _fail(condition: int, kind: str, detail: str) -> None:
        failures.append({"condition": str(condition), "kind": kind,
                         "detail": detail})

    incomplete = sorted(k for k, f in specification["families"].items()
                        if not f["specification_complete"])
    if incomplete or specification["uncovered_kinds"]:
        _fail(1, "evidence_insufficient",
              f"no complete specification for {incomplete or []}; "
              f"uncovered families {specification['uncovered_kinds']}")

    if specification["ambiguous_kinds"]:
        unresolved = {k: f["unresolved_readings"]
                      for k, f in specification["families"].items()
                      if f["ambiguous"]}
        _fail(2, "specification_ambiguous",
              f"the prose does not pin down the predicate for "
              f"{specification['ambiguous_kinds']}: {unresolved}")

    if evidence["determinism"]["agreement"] != 1.0:
        _fail(3, "measured_excess",
              "three-process determinism is not exactly 1.000")

    if evidence["reimplementation"]["per_instrument_min"] != 1.0:
        _fail(4, "measured_excess",
              "the independent reimplementation disagrees on "
              f"{evidence['reimplementation']['failures'][:5]}")
    if evidence["reimplementation"]["segmenter_differential"]["agreement"] \
            != 1.0:
        _fail(4, "measured_excess",
              "the two segmenters admit different character classes")

    if evidence["suites"]["agreement"] != 1.0:
        _fail(5, "measured_excess",
              f"the boundary suites disagree: "
              f"{evidence['suites']['failures'][:5]}")
    if evidence["suites"]["cases"] < C.BOUNDARY_SUITE_MIN_CASES:
        _fail(5, "evidence_insufficient",
              "the boundary corpus holds fewer than "
              f"{C.BOUNDARY_SUITE_MIN_CASES} cases")
    if not evidence["adversarial"]["passed"]:
        _fail(5, "evidence_insufficient",
              "a §24 phenomenon has no adversarial case: "
              f"{evidence['adversarial']['uncovered_by_corpus']}")

    if mutation["kinds_with_an_undetected_defect"]:
        _fail(6, "evidence_insufficient",
              "no discriminating case exists for a meaningful defect in "
              f"{mutation['kinds_with_an_undetected_defect']}")
    if mutation["kinds_with_a_contradiction"]:
        _fail(6, "measured_excess",
              "a family declared a reading inapplicable and the corpus "
              f"separates it: {mutation['kinds_with_a_contradiction']}")
    if mutation["uncovered_kinds"]:
        _fail(6, "evidence_insufficient",
              f"mutation validation does not cover {mutation['uncovered_kinds']}")

    if not evidence["witnesses"]["passed"]:
        _fail(7, "measured_excess",
              "§7.5's witness suite fails: "
              f"{evidence['witnesses']['non_entailment_failures'][:3]}")

    if not evidence["wordings"]["passed"]:
        _fail(8, "measured_excess", "§7.5's wording-equivalence suite fails")
    blocking = (wordings["genuinely_ambiguous"]
                + wordings["requires_correction"])
    if blocking:
        kinds = sorted({row["kind"] for row in blocking})
        _fail(8, "specification_ambiguous",
              f"{len(blocking)} model-facing wordings on {kinds} are "
              "classified genuinely_ambiguous or requires_correction: "
              f"{sorted({row['wording'] for row in blocking})[:4]}")

    frozen = verifier_source_hash()
    if evidence["verifier_hash"] != frozen:
        _fail(9, "measured_excess",
              f"the evidence was produced at verifier hash "
              f"{evidence['verifier_hash'][:12]} and the current hash is "
              f"{frozen[:12]}")
    if r5_evidence["wordings_hash"] != wordings_hash():
        _fail(9, "measured_excess",
              "the recorded wording hash does not match the wordings the "
              "population renders now")

    for problem in _provenance_failures(provenance):
        _fail(10, "evidence_insufficient", problem)

    if failures:
        status = ("SPECIFICATION_AMBIGUOUS"
                  if any(f["kind"] == "specification_ambiguous"
                         for f in failures)
                  else "MEASUREMENT_NOT_ESTABLISHED"
                  if any(f["kind"] == "measured_excess" for f in failures)
                  else "MEASUREMENT_EVIDENCE_INSUFFICIENT")
        raise TerminalStatus(status, {
            "status": status, "gate": C.STAGE_GATE1,
            "rule": "§10.7-R5: §10.2 for every verifier in the final "
                    "instrument population, plus A-E",
            "amendment_hash": amendment_hash(),
            "observed": failures,
            "failed_conditions": sorted({int(f["condition"])
                                         for f in failures}),
            "measurement_basis": None,
            "specification_audit": specification,
            "mutation_validation": mutation,
            "wording_review": wordings,
            "evidence": {k: v for k, v in evidence.items()
                         if k != "instrument_population"},
            "supplementary_diagnostics": (dict(supplementary_diagnostics)
                                          if supplementary_diagnostics
                                          else None),
            "supplementary_diagnostics_are_not_a_criterion":
                "no number under this key was read by the rule, in either "
                "direction. §10.3 and §10.4 keep their own recorded outcomes "
                "and neither is described here as having succeeded",
            "strongest_permissible_statement":
                "measurement is not established for at least one registered "
                "instrument under the amended rule",
            "terminal_sentence": C.TERMINAL_SENTENCE})

    return {
        "outcome": "PASS", "stage": C.STAGE_GATE1,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE1],
        "rule": "§10.7-R5: §10.2 for every verifier in the final instrument "
                "population, plus A-E",
        "amendment": dict(AMENDMENT_TEXT_FIELDS),
        "amendment_hash": amendment_hash(),
        **dict(evidence),
        "specification_audit": specification,
        "mutation_validation": mutation,
        "wording_review": wordings,
        "specification_hash": r5_evidence["specification_hash"],
        "mutation_hash": r5_evidence["mutation_hash"],
        "wordings_hash": r5_evidence["wordings_hash"],
        "frozen_verifier_hash": frozen,
        "instruments": len(instrument_population()),
        "provenance": dict(provenance),
        "supplementary_diagnostics": (dict(supplementary_diagnostics)
                                      if supplementary_diagnostics else None),
        "supplementary_diagnostics_are_not_a_criterion":
            "no number under this key was read by the rule. §10.4-R2 FAILED "
            "under its own stopping rule and §10.3 stands unavailable; this "
            "record does not change either, and a pass here is not a "
            "retroactive pass of either",
        "measurement_basis": C.MEASUREMENT_BASIS_R5,
        "scope_sentence": C.SCOPE_SENTENCE,
        "scope_sentence_is_permanent":
            "the basis is not human_validated, so §10.5's scope sentence "
            "attaches to every analysis record, every claim at every rung and "
            "the final report, and no later stage removes it",
        "sealed_final_check_set": dict(sealed_set) if sealed_set else None,
        "identification_statuses": list(identification_statuses),
    }
