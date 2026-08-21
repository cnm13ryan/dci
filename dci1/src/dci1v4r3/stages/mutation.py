"""§10.7-R5 component D: do the suites actually catch the defects that matter?

**The gap this closes.** §10.2 says the primary and the reimplementation agree
1.000 on 164 boundary cases and 700,800 verdicts. Perfect agreement is
consistent with two things: the instrument is correct, or the suites cannot
tell a correct instrument from a broken one. Mutation testing separates them.
For each registered defective reading it asks whether the corpus contains an
answer on which that reading records a **different verdict** -- because a suite
with no such answer would pass a verifier carrying the defect.

**Applicability is checked, not believed.** `specification.applicability`
records, per family, whether each reading is meaningful and why. This module
takes the other side of that claim: every reading called meaningful must be
*exhibited* by a discriminating case, and every reading called not meaningful
must discriminate **nowhere** in the corpus. A family that declared a reading
inapplicable and then turns out to have a case separating it is a
contradiction, and a contradiction fails the gate rather than being resolved in
whichever direction is convenient.

**The corpus is the frozen suites plus the constructed cases**, over every
severity of every declared range -- not a sample, and not the natural responses.
The natural-response defect sensitivity is a different measurement and is
carried beside this one under its own name: it says what a defect would cost on
real data, and a defect that costs nothing there (`vacuity_ignored` moves 0 of
27,840 verdicts) is a defect the natural corpus cannot validate, which is the
reason a constructed corpus exists at all.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r3.stages.microcase import DEFECT_KINDS
from dci1v4r3.stages.specification import (
    applicability, audit_severity, constraint, form_of, reading_source,
    reading_verdict, spec_cases, statistic_id_of,
)
from dci1v4r3.verifiers.boundary import ALL_CASES, instrument_population
from dci1v4r3.verifiers.compliance import passes
from dci1v4r3.verifiers.constraints import declared_range
from dci1v4r3.verifiers.statistics import STATISTICS, focal_statistic
from dci1v4.verifiers.target import s0_count

__all__ = ["mutation_corpus", "sensitivity", "run_mutation_validation",
           "mutation_hash"]

#: How many discriminating (severity, answer) pairs are counted before the scan
#: for that reading stops. A bound on cost, not a filter: the scan visits the
#: severities in declared order and the answers in corpus order, so the cap
#: changes the *count* reported for a well-detected reading and can never turn
#: a detected reading into an undetected one. It is recorded on the report.
DISCRIMINATION_CAP = 40


def _count(statistic_id: str, text: str) -> int:
    if statistic_id == "s0":
        return s0_count(text)
    if statistic_id == "focal":
        return focal_statistic(text)
    return STATISTICS[statistic_id](text)


def mutation_corpus(kind: str) -> list[dict[str, str]]:
    """The frozen boundary corpus plus this family's constructed cases."""
    corpus = [{"source": "boundary_suite", "label": case.get("case", ""),
               "text": case["text"]} for case in ALL_CASES]
    corpus += [{"source": "specification_audit", "label": case["case_kind"],
                "text": case["text"]}
               for case in spec_cases(kind) if case["text"] is not None]
    return corpus


def sensitivity(kind: str, defect: str, corpus: Sequence[Mapping[str, str]],
                *, cap: int = DISCRIMINATION_CAP) -> dict[str, Any]:
    """Where, in the corpus, this reading records a different verdict."""
    statistic_id = statistic_id_of(kind)
    hits: list[dict[str, Any]] = []
    scanned = 0
    for severity in declared_range(kind):
        rule = constraint(kind, severity)
        for entry in corpus:
            text = entry["text"]
            scanned += 1
            registered = passes(rule, _count(statistic_id, text), text)
            if reading_verdict(kind, severity, text, defect) != registered:
                hits.append({"severity": severity, "source": entry["source"],
                             "label": entry["label"], "text": text[:60],
                             "registered": registered, "defective":
                                 not registered})
                if len(hits) >= cap:
                    return {"discriminating": len(hits), "capped": True,
                            "scanned": scanned, "examples": hits[:3]}
    return {"discriminating": len(hits), "capped": False, "scanned": scanned,
            "examples": hits[:3]}


def _family(kind: str, *, cap: int = DISCRIMINATION_CAP) -> dict[str, Any]:
    corpus = mutation_corpus(kind)
    applies = applicability(kind)
    rows: dict[str, Any] = {}
    for defect in DEFECT_KINDS:
        found = sensitivity(kind, defect, corpus, cap=cap)
        meaningful = applies[defect]["meaningful"]
        rows[defect] = {
            "meaningful": meaningful,
            "why": applies[defect]["reason"],
            **found,
            "detected": bool(meaningful and found["discriminating"]),
            "not_applicable_and_silent": bool(
                not meaningful and not found["discriminating"]),
            "contradiction": bool(
                (meaningful and not found["discriminating"])
                or (not meaningful and found["discriminating"])),
        }
    return {
        "kind": kind,
        "form": form_of(kind),
        "audit_severity": audit_severity(kind),
        "severities": len(declared_range(kind)),
        "corpus": len(corpus),
        "reading_source": reading_source(kind),
        "defects": rows,
        "undetected": sorted(d for d, r in rows.items()
                             if r["meaningful"] and not r["detected"]),
        "contradictions": sorted(d for d, r in rows.items()
                                 if r["contradiction"]),
    }


def run_mutation_validation(kinds: Iterable[str] | None = None, *,
                            cap: int = DISCRIMINATION_CAP) -> dict[str, Any]:
    """D, over every family and form in the final instrument population."""
    population = sorted({k for k, _ in instrument_population()})
    audited = sorted(kinds) if kinds is not None else population
    families = {kind: _family(kind, cap=cap) for kind in audited}

    by_defect: dict[str, Any] = {}
    for defect in DEFECT_KINDS:
        rows = [f["defects"][defect] for f in families.values()]
        by_defect[defect] = {
            "families_where_meaningful": sum(1 for r in rows
                                             if r["meaningful"]),
            "families_detected": sum(1 for r in rows if r["detected"]),
            "families_not_applicable": sum(1 for r in rows
                                           if not r["meaningful"]),
            "not_applicable_kinds": sorted(
                k for k, f in families.items()
                if not f["defects"][defect]["meaningful"]),
            "reasons_for_non_applicability": sorted({
                f["defects"][defect]["why"] for f in families.values()
                if not f["defects"][defect]["meaningful"]}),
            "undetected_kinds": sorted(
                k for k, f in families.items()
                if f["defects"][defect]["meaningful"]
                and not f["defects"][defect]["detected"]),
        }

    by_form: dict[str, Any] = {}
    for form in sorted({f["form"] for f in families.values()}):
        members = [f for f in families.values() if f["form"] == form]
        by_form[form] = {
            "kinds": sorted(f["kind"] for f in members),
            "detected": {d: sum(1 for f in members
                                if f["defects"][d]["detected"])
                         for d in DEFECT_KINDS},
            "meaningful": {d: sum(1 for f in members
                                  if f["defects"][d]["meaningful"])
                           for d in DEFECT_KINDS},
        }

    undetected = sorted(k for k, f in families.items() if f["undetected"])
    contradictions = sorted(k for k, f in families.items()
                            if f["contradictions"])
    return {
        "population_kinds": population,
        "audited_kinds": audited,
        "uncovered_kinds": sorted(set(population) - set(audited)),
        "defect_kinds": list(DEFECT_KINDS),
        "discrimination_cap": cap,
        "families": families,
        "by_defect": by_defect,
        "by_form": by_form,
        "kinds_with_an_undetected_defect": undetected,
        "kinds_with_a_contradiction": contradictions,
        "passed": (not undetected and not contradictions
                   and not set(population) - set(audited)),
        "criterion": "every reading the applicability rule calls meaningful is "
                     "exhibited by a discriminating case somewhere in the "
                     "frozen suites or the constructed cases, at some declared "
                     "severity; every reading it calls not meaningful "
                     "discriminates nowhere, and its reason is recorded",
        "what_this_does_not_measure":
            "practical consequence on real answers. A defect detected here may "
            "move no natural label, and one that moves many may be detected "
            "here by a single constructed case. The natural-response defect "
            "sensitivity is reported separately and is never read as semantic "
            "validation",
    }


def mutation_hash(report: Mapping[str, Any] | None = None) -> str:
    report = report if report is not None else run_mutation_validation()
    return sha_text(canonical_json(report))
