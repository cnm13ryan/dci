"""Gate 1: v4r4's measurement rule (§10.2 plus §10.7 A-E).

**What Gate 1 asks.** Two questions, kept apart because they have different
answers and different evidence:

1. **specification validity** -- does the sentence the model was shown pin
   down the formal predicate the study intends? (`stages.specification`)
2. **implementation validity** -- does the deterministic verifier compute that
   predicate, correctly and reproducibly? (this module, plus
   `stages.mutation`)

**Why the rule is built this way.** A registered DCI constraint is
*mechanically decidable*: the pipeline is `model response -> deterministic
verifier -> compliance outcome`, and the verifier's output is the outcome by
construction. There is no latent quantity for an external rater to estimate.
So an agreement rate between the verifier and a reviewer measures the
reviewer, and the development record says what it measures: human and LLM
reviewers alike introduced counting, arithmetic, segmentation, threshold and
convention errors of exactly the kind this instrument was designed to remove.
Reviewer agreement is therefore **not a criterion here, in either direction**,
and that is enforced rather than promised -- `gate1_payload` takes reviewer
evidence as an opaque mapping under `supplementary_diagnostics` and never
reads a number out of it.

**This is not the claim that deterministic code is automatically correct.**
It is the opposite claim: that deterministic code has to be validated by the
methods appropriate to deterministic code. So the rule requires an executable
formal specification that reproduces the verifier at every severity of every
declared range; an independent reimplementation written from prose alone,
agreeing exactly; adversarial, boundary and Unicode corpora; satisfiability
and non-entailment witnesses; and **mutation validation** -- for every
registered defect class, a case on which a verifier carrying that defect would
disagree, so that "the suites agree" cannot mean "the suites cannot tell".

**What a pass may be called.** `measurement_basis =
deterministic_measurement_validated`. That is not `human_validated`, so
§10.5's scope sentence attaches to every record downstream, permanently, and
§10.5's second question -- would an independent human reproduce these
verdicts? -- stays unanswered. v4r4's rule licenses the study to run. It does
not license a stronger claim than v4r3 could have made.

The five §10.2 collectors below are v4r3's, carried unchanged in substance:
determinism over three operating-system processes; the frozen boundary suites
over every registered instrument; the independent reimplementation with its
segmenter differential; the §24 adversarial corpus; and the carry-over record.
What changed is the rule that reads them.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError, TerminalStatus
from dci1v4.protocol.hashing import canonical_json, sha_text
from dci1v4.verifiers.target import s0_count

from dci1v7.protocol import constants as C
from dci1v7.stages.mutation import mutation_hash, run_mutation_validation
from dci1v7.stages.specification import (
    run_specification_audit, specification_hash, wording_review, wordings_hash,
)
from dci1v7.verifiers import verifier_source_hash
from dci1v7.verifiers import independent as I
from dci1v7.verifiers.adversarial import run_adversarial_corpus
from dci1v7.verifiers.boundary import (
    ALL_CASES, evaluate_suites, instrument_population, suite_hash,
)
from dci1v7.verifiers.carryover import carry_over_record
from dci1v7.verifiers.compliance import graded, non_vacuous, passes
from dci1v7.verifiers.constraints import Constraint, FAMILIES
from dci1v7.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)
from dci1v7.verifiers.witnesses import run_witness_suite
from dci1v7.verifiers.words import assert_single_splitter, case_folding_splitters
from dci1v7.verifiers.wording_suite import run_wording_suite

__all__ = ["verdict_digest", "determinism_report", "reimplementation_report",
           "segmenter_differential", "collect_evidence",
           "collect_specification_evidence", "MEASUREMENT_RULE",
           "measurement_rule_hash", "gate1_payload"]

_SRC = str(Path(__file__).resolve().parents[2])


def _constraint(kind: str, severity: int) -> Constraint:
    return (Constraint(kind, severity) if kind == "A"
            else Constraint(kind, severity, extended=True, reserve=True))


def _statistic(kind: str, text: str) -> int:
    if kind == "A":
        return s0_count(text)
    if kind == "B":
        return focal_statistic(text)
    return STATISTICS[FAMILIES[kind].statistic_id](text)


def verdict_digest(texts: Sequence[str]) -> str:
    """One hash over every verdict the population produces on ``texts``.

    A digest rather than a table because determinism is a statement about the
    whole vector: if any one verdict moved between processes the digest moves,
    and comparing 3 digests is the same evidence as comparing 3 tables of
    several million entries without holding them in memory three times.
    """
    rows = []
    for kind, severity in instrument_population():
        constraint = _constraint(kind, severity)
        for index, text in enumerate(texts):
            statistic = _statistic(kind, text)
            rows.append((kind, severity, index, statistic,
                         passes(constraint, statistic, text),
                         round(graded(constraint, statistic, text), 12),
                         non_vacuous(constraint, text, truncated=False)))
    return sha_text(canonical_json(rows))


def determinism_report(texts: Sequence[str], *,
                       processes: int = C.DETERMINISM_PROCESSES
                       ) -> dict[str, Any]:
    """§10.2: three separate processes, agreement exactly 1.000."""
    script = (
        "import sys, json;"
        f"sys.path.insert(0, {_SRC!r});"
        "from dci1v7.stages.gate1 import verdict_digest;"
        "texts = json.load(sys.stdin);"
        "print(verdict_digest(texts))"
    )
    payload = json.dumps(list(texts))
    digests = []
    for _ in range(processes):
        result = subprocess.run([sys.executable, "-c", script], input=payload,
                                capture_output=True, text=True, check=True)
        digests.append(result.stdout.strip())
    agreement = 1.0 if len(set(digests)) == 1 else 0.0
    return {"processes": processes, "responses": len(texts),
            "instruments": len(instrument_population()),
            "digests": digests, "agreement": agreement}


def segmenter_differential() -> dict[str, Any]:
    """The two segmenters admit exactly the same character class.

    Registered because a prose-only reimplementation that segmented on a
    regular-expression word class was found to admit 1,151 non-decimal
    numeric characters that §7.0's *alphabetic* excludes. The check is over
    the whole Unicode range, not a sample.
    """
    disagreements = []
    for codepoint in range(0x110000):
        ch = chr(codepoint)
        if bool(ch.isalpha()) != bool(I.words(ch)):
            disagreements.append(hex(codepoint))
            if len(disagreements) > 20:
                break
    return {"codepoints": 0x110000, "disagreements": disagreements,
            "agreement": 1.0 if not disagreements else 0.0,
            "case_folding_splitters": [hex(ord(c))
                                       for c in case_folding_splitters()]}


def statistic_report(texts: Sequence[str]) -> dict[str, Any]:
    """Every counted statistic, on **every** response, in both implementations.

    This is the half of §10.2 that is about *reading the text*, and it is the
    half where a segmentation defect lives -- the U+0130 finding surfaced
    exactly here. It runs over the whole corpus because it costs one pass per
    response per implementation, not one pass per response per instrument.
    """
    failures: list[str] = []
    checked = 0
    for index, text in enumerate(texts):
        checked += 1
        if word_count(text) != I.word_count(text):
            failures.append(f"row{index}:word_count")
        if s0_count(text) != I.s0(text):
            failures.append(f"row{index}:s0")
        if focal_statistic(text) != I.focal_statistic(text):
            failures.append(f"row{index}:focal")
        for name, function in STATISTICS.items():
            if function(text) != I.statistic(name, text):
                failures.append(f"row{index}:{name}")
    return {"responses": checked,
            "statistics_per_response": len(STATISTICS) + 3,
            "comparisons": checked * (len(STATISTICS) + 3),
            "agreement": 1.0 if not failures else 0.0,
            "failures": sorted(set(failures))[:20]}


def reimplementation_report(texts: Sequence[str], *,
                            verdict_sample: int | None = 1200
                            ) -> dict[str, Any]:
    """§10.2's independent-reimplementation evidence, in two tiers.

    **Tier 1, every response**: the fifteen counted statistics, the word count,
    the exact-count rule and B's statistic, in both implementations. This is
    where a text-reading defect can hide, and nothing is sampled.

    **Tier 2, a declared sample**: the full verdict vector -- pass, graded and
    non-vacuity -- for all 584 registered instrument instances. Tier 2 is 584
    times the work of tier 1 per response and can only disagree where tier 1
    does, or where the two implementations read the same statistic and apply a
    different predicate. The frozen boundary corpus is always inside the
    sample, so every enumerated phenomenon is covered at tier 2 whatever the
    sample size, and the sample is declared on the record rather than implied.
    """
    tier1 = statistic_report(texts)
    sample = texts if verdict_sample is None else texts[:verdict_sample]
    per_instrument: dict[str, float] = {}
    failures: list[str] = []
    checked = 0
    for kind, severity in instrument_population():
        constraint = _constraint(kind, severity)
        agree = total = 0
        for text in sample:
            statistic = _statistic(kind, text)
            total += 1
            checked += 1
            ok = (passes(constraint, statistic, text) == I.passes(kind, severity, text)
                  and abs(graded(constraint, statistic, text)
                          - I.graded(kind, severity, text)) < 1e-12
                  and non_vacuous(constraint, text, truncated=False)
                  == I.non_vacuous(kind, text, False))
            if ok:
                agree += 1
            else:
                failures.append(f"{kind}:{severity}")
        per_instrument[f"{kind}:{severity}"] = agree / total if total else 1.0
    worst = min(per_instrument.values()) if per_instrument else 1.0
    worst = min(worst, tier1["agreement"])
    return {"agreement": {"population": worst},
            "per_instrument_min": worst,
            "statistics_every_response": tier1,
            "verdicts_checked": checked,
            "verdict_sample": {"n": len(sample), "of": len(texts),
                               "rule": "the frozen boundary corpus in full, "
                                       "then the leading calibration "
                                       "responses in stored order"},
            "responses": len(texts),
            "failures": sorted(set(failures))[:20],
            "segmenter_differential": segmenter_differential()}


def collect_evidence(calibration_texts: Sequence[str], *,
                     determinism_sample: int | None = 400,
                     verdict_sample: int | None = 1200) -> dict[str, Any]:
    """Every §10.2 artifact, in one record.

    ``determinism_sample`` bounds the three-process check, which is quadratic
    in nothing but is 584 instruments wide; the *sample is declared on the
    record*, so a reader sees what was covered rather than assuming it was
    everything. The reimplementation check runs on the full corpus.
    """
    assert_single_splitter()
    # The boundary corpus goes FIRST so that it is inside every declared
    # sample: a sample that could exclude the frozen cases would be sampling
    # away the part of the corpus authored to be hard.
    texts = [case["text"] for case in ALL_CASES] + list(calibration_texts)
    sample = texts if determinism_sample is None else texts[:determinism_sample]
    return {
        "verifier_hash": verifier_source_hash(),
        "instrument_population": [f"{k}:{s}" for k, s in
                                  instrument_population()],
        "determinism": determinism_report(sample),
        "determinism_sample": {"n": len(sample), "of": len(texts),
                               "rule": "the frozen boundary corpus plus the "
                                       "leading calibration responses"},
        "suites": evaluate_suites(),
        "boundary_suite_hash": suite_hash(),
        "reimplementation": reimplementation_report(
            texts, verdict_sample=verdict_sample),
        "adversarial": run_adversarial_corpus(calibration_texts),
        "witnesses": run_witness_suite(),
        "wordings": run_wording_suite(),
        "carryover": carry_over_record(),
    }


#: §10.7. The rule itself, as data, hashed into every Gate-1 record so that
#: the question "which rule was this decided under?" is answered by the
#: artifact rather than by a document that may have moved since.
MEASUREMENT_RULE = {
    "section": "10.7",
    "revision": "v4r4",
    "title": "Deterministic-measurement validation",
    "criterion": ("§10.2 for every verifier in the final instrument "
                  "population, plus §10.7 A-E"),
    "components": {
        "A": "specification validity: an executable formal specification per "
             "family and form, and a prose-to-predicate invariant over every "
             "model-facing wording",
        "B": "implementation validity: determinism, frozen boundary suites, "
             "adversarial and Unicode corpora",
        "C": "independent reimplementation from prose alone, exact agreement",
        "D": "mutation validation: a discriminating case for every meaningful "
             "registered defect class, and a checked reason for every "
             "non-applicability",
        "E": "provenance: verifier hash, wording hash, specification hash, "
             "mutation hash, lifecycle chain and producing commit",
    },
    "measurement_basis": C.MEASUREMENT_BASIS,
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
        "8 wording equivalence passes and every model-facing wording exposes "
        "its comparison direction",
        "9 the verifier hash and the wording hash are bound and match",
        "10 lifecycle and provenance integrity passes",
    ),
    "no_reviewer_threshold": (
        "no human or autorater agreement rate, sample size, Wilson interval, "
        "accuracy, repeatability or judge verdict appears in this rule, in "
        "either direction. Reviewer evidence is carried as a diagnostic and "
        "is never read by the criterion"),
    "what_this_does_not_establish": (
        "that the verifier's verdicts are what an independent human would "
        "give. §10.5's second question is unanswered under this rule, the "
        "basis it writes is not human_validated, and the scope sentence "
        "attaches permanently because of that"),
}


def measurement_rule_hash() -> str:
    return sha_text(canonical_json(MEASUREMENT_RULE))


def collect_specification_evidence(
        *, specification: Mapping[str, Any] | None = None,
        mutation: Mapping[str, Any] | None = None,
        wordings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A, A' and D. B, C and E come from ``collect_evidence`` above."""
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
    if not provenance.get("no_gate1_record_exists_yet"):
        problems.append("this replication already has a Gate 1 record")
    return problems


def gate1_payload(*, evidence: Mapping[str, Any],
                  specification_evidence: Mapping[str, Any],
                  provenance: Mapping[str, Any],
                  supplementary_diagnostics: Mapping[str, Any] | None = None,
                  measurement_basis: str = C.MEASUREMENT_BASIS,
                  sealed_set: Mapping[str, Any] | None = None,
                  identification_statuses: Sequence[str] = ()
                  ) -> dict[str, Any]:
    """v4r4's Gate 1. Ten conditions, none of them about a reviewer."""
    if measurement_basis in C.MEASUREMENT_BASES_REFUSED:
        raise ProtocolError(
            f"{measurement_basis!r} is a reviewer-derived basis. v4r4's Gate 1 "
            f"writes {C.MEASUREMENT_BASIS!r} and nothing else; a reviewer "
            "basis would have to be established by the rule that registers "
            "it, and §10.7 is not that rule")
    if measurement_basis != C.MEASUREMENT_BASIS:
        raise ProtocolError(
            f"§10.7 writes {C.MEASUREMENT_BASIS!r}; {measurement_basis!r} is "
            "not a registered v4r4 measurement basis")

    specification = specification_evidence["specification_audit"]
    mutation = specification_evidence["mutation_validation"]
    wordings = specification_evidence["wording_review"]
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
              "mutation validation does not cover "
              f"{mutation['uncovered_kinds']}")

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
              f"{len(blocking)} model-facing wordings on {kinds} do not "
              "expose the comparison direction of the predicate that scores "
              f"them: {sorted({row['wording'] for row in blocking})[:4]}")

    frozen = verifier_source_hash()
    if evidence["verifier_hash"] != frozen:
        _fail(9, "measured_excess",
              f"the evidence was produced at verifier hash "
              f"{evidence['verifier_hash'][:12]} and the current hash is "
              f"{frozen[:12]}")
    if specification_evidence["wordings_hash"] != wordings_hash():
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
            "criterion": MEASUREMENT_RULE["criterion"],
            "measurement_rule_hash": measurement_rule_hash(),
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
                "direction",
            "strongest_permissible_statement":
                "measurement is not established for at least one registered "
                "instrument",
            "terminal_sentence": C.TERMINAL_SENTENCE})

    return {
        "outcome": "PASS", "stage": C.STAGE_GATE1,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE1],
        "criterion": MEASUREMENT_RULE["criterion"],
        "measurement_rule": dict(MEASUREMENT_RULE),
        "measurement_rule_hash": measurement_rule_hash(),
        **dict(evidence),
        "specification_audit": specification,
        "mutation_validation": mutation,
        "wording_review": wordings,
        "specification_hash": specification_evidence["specification_hash"],
        "mutation_hash": specification_evidence["mutation_hash"],
        "wordings_hash": specification_evidence["wordings_hash"],
        "frozen_verifier_hash": frozen,
        "instruments": len(instrument_population()),
        "provenance": dict(provenance),
        "supplementary_diagnostics": (dict(supplementary_diagnostics)
                                      if supplementary_diagnostics else None),
        "supplementary_diagnostics_are_not_a_criterion":
            "no number under this key was read by the rule. v4r3's §10.4-R2 "
            "FAILED under its own stopping rule and its §10.3 stands "
            "unavailable; a pass here is not a retroactive pass of either, "
            "and neither is described as having succeeded",
        "measurement_basis": C.MEASUREMENT_BASIS,
        "scope_sentence": C.SCOPE_SENTENCE,
        "scope_sentence_is_permanent":
            "the basis is not human_validated, so §10.5's scope sentence "
            "attaches to every analysis record, every claim at every rung and "
            "the final report, and no later stage removes it",
        "sealed_final_check_set": dict(sealed_set) if sealed_set else None,
        "identification_statuses": list(identification_statuses),
    }
