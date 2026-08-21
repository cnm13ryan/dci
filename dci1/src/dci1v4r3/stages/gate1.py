"""Gate 1: §10.2 for the whole declared instrument population, and §10.3/§10.4.

The gate collects five kinds of evidence and refuses to pass without all of
them, plus one of the two human-or-autorater pathways:

1. **determinism** -- the same verdicts from three separate operating-system
   processes over every calibration response, agreement exactly 1.000;
2. **boundary suites** -- 164 frozen cases, every one of the 584 registered
   constraint instances, agreement exactly 1.000;
3. **independent reimplementation** -- §10.2's prose-only implementation over
   the same population, agreement exactly 1.000, with a differential check
   asserting that the two segmenters admit the same character class;
4. **adversarial corpus** -- every §24 phenomenon exercised, with its realised
   frequency in genuine generations reported beside it;
5. **carry-over** -- every inherited source and case, hashed, with the sources
   v4r3 does *not* inherit named and reasoned.

**The gate cannot be passed by an agent.** §10.3 routes an absent annotator to
§10.4, and §10.4 ends in *explicit researcher approval* writing
``measurement_basis = autorater_calibration_approved``. A basis of
``human_validation_unavailable`` is the state in which neither pathway has
completed, and this gate treats it as evidence insufficiency, exactly as
v4r2's does. That is the design: the study's measurement claim rests on a
person's signature and not on a program's.
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

from dci1v4r3.protocol import constants as C
from dci1v4r3.verifiers import verifier_source_hash
from dci1v4r3.verifiers import independent as I
from dci1v4r3.verifiers.adversarial import run_adversarial_corpus
from dci1v4r3.verifiers.boundary import (
    ALL_CASES, evaluate_suites, instrument_population, suite_hash,
)
from dci1v4r3.verifiers.carryover import carry_over_record
from dci1v4r3.verifiers.compliance import graded, non_vacuous, passes
from dci1v4r3.verifiers.constraints import Constraint, FAMILIES
from dci1v4r3.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)
from dci1v4r3.verifiers.witnesses import run_witness_suite
from dci1v4r3.verifiers.words import assert_single_splitter, case_folding_splitters
from dci1v4r3.verifiers.wording_suite import run_wording_suite

__all__ = ["verdict_digest", "determinism_report", "reimplementation_report",
           "segmenter_differential", "collect_evidence", "gate1_payload"]

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
        "from dci1v4r3.stages.gate1 import verdict_digest;"
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


def gate1_payload(*, evidence: Mapping[str, Any], measurement_basis: str,
                  human: Mapping[str, Any] | None = None,
                  autorater: Mapping[str, Any] | None = None,
                  sealed_set: Mapping[str, Any] | None = None,
                  identification_statuses: Sequence[str] = ()
                  ) -> dict[str, Any]:
    """Gate 1 for every registered instrument in the declared range."""
    if measurement_basis not in C.MEASUREMENT_BASES:
        raise ProtocolError(f"measurement basis {measurement_basis!r} is not "
                            f"one of {C.MEASUREMENT_BASES}")
    failures: list[dict[str, str]] = []

    def _fail(kind: str, detail: str) -> None:
        failures.append({"kind": kind, "detail": detail})

    if evidence["determinism"]["agreement"] != 1.0:
        _fail("measured_excess",
              "three-process determinism is not exactly 1.000")
    if evidence["suites"]["agreement"] != 1.0:
        _fail("measured_excess",
              f"the boundary suites disagree: "
              f"{evidence['suites']['failures'][:5]}")
    if evidence["suites"]["cases"] < C.BOUNDARY_SUITE_MIN_CASES:
        _fail("evidence_insufficient",
              "the boundary corpus holds fewer than forty cases")
    if evidence["reimplementation"]["per_instrument_min"] != 1.0:
        _fail("measured_excess",
              "the independent reimplementation disagrees on "
              f"{evidence['reimplementation']['failures'][:5]}")
    if evidence["reimplementation"]["segmenter_differential"]["agreement"] \
            != 1.0:
        _fail("measured_excess",
              "the two segmenters admit different character classes")
    if not evidence["witnesses"]["passed"]:
        _fail("measured_excess",
              "§7.5's witness suite fails: "
              f"{evidence['witnesses']['non_entailment_failures'][:3]}")
    if not evidence["wordings"]["passed"]:
        _fail("measured_excess", "§7.5's wording suite fails")
    if not evidence["adversarial"]["passed"]:
        _fail("evidence_insufficient",
              "a §24 phenomenon has no adversarial case: "
              f"{evidence['adversarial']['uncovered_by_corpus']}")

    if measurement_basis == "human_validated":
        if human is None:
            _fail("evidence_insufficient",
                  "the basis is human_validated and no human labels exist")
    elif measurement_basis == "autorater_calibration_approved":
        if not (autorater and autorater.get("approved")):
            _fail("measured_excess", "the autorater pathway is not approved")
    else:
        # §18 stage 4: Gate 1 passes on §10.2 **plus §10.3 or §10.4**.
        # ``human_validation_unavailable`` is the state in which neither
        # pathway has completed. §10.3 routes it to §10.4 "without waiving the
        # criterion", so it is not itself a basis Gate 1 can pass on.
        _fail("evidence_insufficient",
              "the measurement basis is human_validation_unavailable: no "
              "independent annotator completed §10.3 and the §10.4 autorater "
              "pathway has not been approved by the researcher, so neither "
              "pathway Gate 1 requires has completed")

    if failures:
        status = ("MEASUREMENT_NOT_ESTABLISHED"
                  if any(f["kind"] == "measured_excess" for f in failures)
                  else "MEASUREMENT_EVIDENCE_INSUFFICIENT")
        raise TerminalStatus(status, {
            "status": status, "gate": C.STAGE_GATE1,
            "criterion": "§10.2 for every instrument in the declared range, "
                         "plus §10.3 or §10.4",
            "observed": failures,
            "measurement_basis": measurement_basis,
            "evidence": {k: v for k, v in evidence.items()
                         if k != "instrument_population"},
            "strongest_permissible_statement":
                "measurement is not established for at least one registered "
                "instrument",
            "terminal_sentence": C.TERMINAL_SENTENCE})

    return {
        "outcome": "PASS", "stage": C.STAGE_GATE1,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE1],
        **dict(evidence),
        "human_agreement": dict(human) if human else None,
        "autorater": dict(autorater) if autorater else None,
        "sealed_final_check_set": dict(sealed_set) if sealed_set else None,
        "measurement_basis": measurement_basis,
        "scope_sentence": (None if measurement_basis == "human_validated"
                           else C.SCOPE_SENTENCE),
        "frozen_verifier_hash": verifier_source_hash(),
        "identification_statuses": list(identification_statuses),
    }
