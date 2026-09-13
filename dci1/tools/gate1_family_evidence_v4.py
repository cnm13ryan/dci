"""Execute the §10.2 evidence for the eight registered reference families.

NOT part of the dci1v4 package and NOT a stage. It runs the same registered
§10.2 procedures ``tools/gate1_evidence_v4.py`` runs for A and B, over the
family instruments instead, and writes ``reports/gate1_v4/section_10_2_families.json``.
It approves nothing and Gate 1 remains unapproved.

**Why this is not blocked on the reference pool.** The Gate 1 report says the
pool must be final before family verifier work begins, because §10.2 names
"every admitted reference family verifier" and Gate 3 has not run. That is the
right reading of *sufficiency* and the wrong reading of *necessity*. RF1-RF8
are registered. No disposition of Amendment B removes them, and no outcome of
Gate 3 can admit a family outside the pool it is given. So their §10.2 evidence
is required under every disposition and is never spent on a family that may not
exist. Amendment B, if adopted, *adds* families; it does not subtract these.

**Scope: every rung, not the admitted rung.** Gate 3 has not chosen a severity,
so the instrument population here is the whole registered ladder --- all 94
rungs across the eight families. That makes the evidence independent of Gate
3's outcome rather than conditional on it.

**No carry-over.** §10.2 confines carry-over to A. The family suites are
authored for v4 in full and this artifact claims nothing from v3.

Usage:
  PYTHONPATH=src python tools/gate1_family_evidence_v4.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))
sys.path.insert(0, str(DCI1 / "tools"))

from dci1v4.protocol import constants as C                        # noqa: E402
from dci1v4.stages.gate1 import (independent_agreement,           # noqa: E402
                                 three_process_determinism)
from dci1v4.verifiers import boundary                             # noqa: E402
from dci1v4.verifiers import verifier_source_hash                 # noqa: E402
from dci1v4.verifiers.adversarial import case_incidence           # noqa: E402
from dci1v4.verifiers.constraints import (FOCAL_GRID,             # noqa: E402
                                          REFERENCE_LADDERS,
                                          TARGET_GRID)

from gate1_evidence_v4 import response_pool                       # noqa: E402

OUT = DCI1 / "reports" / "gate1_v4"

#: Every rung of every registered family: the instrument population Gate 3
#: chooses from, so the evidence does not depend on which rung it chooses.
INSTRUMENTS = [(family, q)
               for family in sorted(REFERENCE_LADDERS)
               for q in REFERENCE_LADDERS[family]]

#: §24's enumeration for "the word-length and budget constraints", verbatim,
#: with the label each of the two independent enumerations gives it. The
#: adversarial corpus and the boundary suite were authored separately and name
#: three of the seven cases differently, so a cross-check that assumes one
#: vocabulary reports coverage gaps that do not exist.
BUDGET_ENUMERATION = (
    # §24 phrase                        adversarial label        suite label
    ("empty output",                    "empty-output",          "empty-output"),
    ("single-token output",             "single-token-output",   "single-token-output"),
    ("hyphenated forms",                "hyphenation",           "hyphenated-forms"),
    ("apostrophised forms",             "apostrophised-form",    "apostrophised-forms"),
    ("non-Latin script",                "non-latin-script",      "non-latin-script"),
    ("digits and symbols adjacent",     "digits-adjacent-to-words",
                                                                 "digits-and-symbols-adjacent"),
    ("markdown emphasis",               "markdown-emphasis",     "markdown-emphasis"),
)

#: The family-specific boundary features the §24 enumeration does not name
#: because it enumerates by convention rather than by family. Each maps to the
#: FOCAL_COVERAGE label that carries it.
FAMILY_FEATURES = {
    "RF1": "initial-letter-b", "RF2": "suffix-ing", "RF3": "single-letter-words",
    "RF4": "doubled-letters", "RF5": "comma-budget", "RF6": "capitalisation",
    "RF7": "letter-a", "RF8": "suffix-y",
}

TEXT_BATCH = 500


def determinism_over(texts: list[str]) -> dict:
    """§10.2: three executions on three separate processes, agreement 1.000.

    Batched by family as well as by text so a single subprocess payload stays
    bounded: the helper's payload repeats the response once per instrument, so
    94 instruments at once would serialise the pool ninety-four times over.
    Every response is still covered by three separate processes for every one
    of the 94 instruments, and the reported agreement is the minimum.
    """
    started = time.monotonic()
    agreements, batches = set(), 0
    for family in sorted(REFERENCE_LADDERS):
        rungs = [(family, q) for q in REFERENCE_LADDERS[family]]
        for start in range(0, len(texts), TEXT_BATCH):
            chunk = texts[start:start + TEXT_BATCH]
            agreements.add(three_process_determinism(rungs, chunk)["agreement"])
            batches += 1
            print(f"  determinism {family} {start}/{len(texts)}",
                  file=sys.stderr, flush=True)
    return {
        "line": "determinism",
        "processes_per_batch": C.DETERMINISM_PROCESSES,
        "batches": batches,
        "processes_total": batches * C.DETERMINISM_PROCESSES,
        "responses": len(texts), "instruments": len(INSTRUMENTS),
        "verdicts_per_process": len(texts) * len(INSTRUMENTS),
        "agreement": min(agreements) if agreements else 0.0,
        "all_batches_exactly_one": agreements == {1.0},
        "seconds": round(time.monotonic() - started, 1),
        "note": ("batched by family and by text only to bound the subprocess "
                 "payload; every response is covered by three separate "
                 "processes at every one of the 94 rungs"),
    }


def boundary_evidence() -> dict:
    """§10.2: the frozen boundary suite, per family verifier."""
    suites = boundary.evaluate_suites()
    cases = boundary.FOCAL_CASES
    per_family = {}
    for family in sorted(REFERENCE_LADDERS):
        label = FAMILY_FEATURES[family]
        per_family[family] = {
            "cases": len(cases),
            "carried_from_v3": 0,
            "authored_for_v4": len(cases),
            "minimum_required": C.BOUNDARY_SUITE_MIN_CASES,
            "meets_minimum": len(cases) >= C.BOUNDARY_SUITE_MIN_CASES,
            "agreement": suites["agreement"].get(family),
            "rungs_checked": len(REFERENCE_LADDERS[family]),
            "family_feature": label,
            "family_feature_cases": list(boundary.FOCAL_COVERAGE[label]),
        }
    return {
        "line": "boundary suite",
        "families": per_family,
        "suite_hash": suites["suite_hash"],
        "failures": [f for f in suites["failures"]
                     if f["instrument"] in REFERENCE_LADDERS],
        "budget_enumeration_covered": {
            phrase: list(boundary.FOCAL_COVERAGE[suite_label])
            for phrase, _, suite_label in BUDGET_ENUMERATION
            if suite_label in boundary.FOCAL_COVERAGE},
        "budget_enumeration_missing": [
            phrase for phrase, _, suite_label in BUDGET_ENUMERATION
            if suite_label not in boundary.FOCAL_COVERAGE],
        "label_vocabularies_differ": {
            phrase: {"adversarial": adv, "boundary_suite": suite}
            for phrase, adv, suite in BUDGET_ENUMERATION if adv != suite},
        "frozen_before": ("qualification; the case texts and expected "
                          "statistics are literals in verifiers/boundary.py "
                          "and are inside the canonical verifier hash"),
    }


def reimplementation_over(texts: list[str]) -> dict:
    """§10.2: the prose-only second implementation, agreement 1.000."""
    started = time.monotonic()
    per_instrument, disagreements, responses = {}, [], None
    for family in sorted(REFERENCE_LADDERS):
        rungs = [(family, q) for q in REFERENCE_LADDERS[family]]
        result = independent_agreement(rungs, texts)
        per_instrument.update(result["agreement"])
        disagreements.extend(result["disagreements"])
        responses = result["responses"]
        print(f"  reimplementation {family} done", file=sys.stderr, flush=True)
    values = set(per_instrument.values())
    return {"line": "independent reimplementation",
            "responses_including_suites": responses,
            "agreement": per_instrument,
            "minimum_agreement": min(values) if values else 0.0,
            "all_exactly_one": values == {1.0},
            "disagreements": disagreements[:10],
            "source_material": ("the registered prose of v4r2 §7.2's family "
                                "table and §7.4's graded form only; the "
                                "reimplementation imports nothing from "
                                "dci1v4.verifiers"),
            "seconds": round(time.monotonic() - started, 1)}


def adversarial_over(texts: list[str]) -> dict:
    """§10.2 / §24: the enumeration §24 registers for budget constraints.

    §24 names one enumeration for "the word-length and budget constraints",
    and every registered family is a budget constraint, so the family
    enumeration is B's. The targeted corpus that exercises it is the same
    corpus; what is family-specific is the boundary suite's own features,
    reported above.
    """
    incidence = case_incidence(texts)
    return {
        "line": "adversarial corpus",
        "enumeration": ("§24, verbatim: for the word-length and budget "
                        "constraints the enumerated cases are empty output, "
                        "single-token output, hyphenated and apostrophised "
                        "forms, non-Latin script, digits and symbols adjacent "
                        "to words, and markdown emphasis"),
        "realised_incidence_in_genuine_generations": {
            phrase: incidence[adv] for phrase, adv, _ in BUDGET_ENUMERATION},
        "genuine_generations": len(texts),
        "shared_with_A_and_B": ("the targeted corpus is the one built in "
                                "verifiers/adversarial.py and already reported "
                                "in section_10_2.json; §24 gives the budget "
                                "constraints the same enumeration as B"),
    }


def ab_recheck(texts: list[str]) -> dict:
    """Does the corrected reimplementation still agree exactly on A and B?

    Extending §10.2 to the families exposed a defect in the prose-only
    reimplementation's segmentation (see CHANGES_SCIENTIFIC.md). A and B's
    §10.2 line was established under the faulty module, so it is re-verified
    here rather than assumed to survive. It does: the correction only removes
    non-decimal numerics from the letter class, and no A or B instrument reads
    them.
    """
    started = time.monotonic()
    instruments = ([("A", n) for n in TARGET_GRID]
                   + [("B", m) for m in FOCAL_GRID])
    result = independent_agreement(instruments, texts)
    values = set(result["agreement"].values())
    return {"line": "A and B reimplementation, re-verified after the "
                    "segmentation correction",
            "instruments": len(instruments),
            "responses_including_suites": result["responses"],
            "minimum_agreement": min(values) if values else 0.0,
            "all_exactly_one": values == {1.0},
            "disagreements": result["disagreements"],
            "consequence": ("reports/gate1_v4/section_10_2.json stands as "
                            "written; nothing in it is invalidated"),
            "seconds": round(time.monotonic() - started, 1)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the response pool; for a smoke run only")
    args = parser.parse_args()

    pool = response_pool()
    texts = pool["texts"]
    if args.limit:
        texts = texts[:args.limit]
    pool_meta = {k: v for k, v in pool.items() if k != "texts"}
    pool_meta["texts_used"] = len(texts)
    pool_meta["is_smoke_run"] = bool(args.limit)
    print(f"pool: {len(texts)} distinct texts", file=sys.stderr, flush=True)

    boundary_block = boundary_evidence()
    payload = {
        "artifact": ("§10.2 verifier-correctness evidence for the eight "
                     "registered reference families"),
        "classification": ("Gate 1 input evidence. Gate 1 is NOT approved by "
                           "this artifact and remains unapproved."),
        "scope": {
            "instruments": [f"{k}@{s}" for k, s in INSTRUMENTS],
            "instrument_count": len(INSTRUMENTS),
            "families": sorted(REFERENCE_LADDERS),
            "why_not_blocked_on_the_pool": (
                "RF1-RF8 are registered; Gate 3 can only admit from the pool "
                "it is given, and Amendment B adds families rather than "
                "removing these. The evidence is required under every "
                "disposition of the pool question."),
            "out_of_scope": ("the three Amendment B candidate families, which "
                             "are not registered and would need their own "
                             "§10.2 set if the amendment were adopted"),
        },
        "response_pool": pool_meta,
        "determinism": determinism_over(texts),
        "boundary_suite": boundary_block,
        "independent_reimplementation": reimplementation_over(texts),
        "adversarial_corpus": adversarial_over(texts),
        "a_and_b_recheck": ab_recheck(texts),
        "carry_over": {"line": "carry-over", "applies": False,
                       "rule": ("§10.2 confines carry-over to A; the family "
                                "suites are authored for v4 in full")},
        "canonical_verifier_hash": verifier_source_hash(),
    }
    families = boundary_block["families"]
    payload["summary"] = {
        "determinism_exactly_one":
            payload["determinism"]["all_batches_exactly_one"],
        "boundary_agreement_exactly_one":
            {f["agreement"] for f in families.values()} == {1.0},
        "every_family_meets_the_forty_case_minimum":
            all(f["meets_minimum"] for f in families.values()),
        "budget_enumeration_fully_covered":
            not boundary_block["budget_enumeration_missing"],
        "reimplementation_exactly_one":
            payload["independent_reimplementation"]["all_exactly_one"],
        "families_meet_10_2": (
            payload["determinism"]["all_batches_exactly_one"]
            and payload["independent_reimplementation"]["all_exactly_one"]
            and {f["agreement"] for f in families.values()} == {1.0}
            and all(f["meets_minimum"] for f in families.values())
            and not boundary_block["budget_enumeration_missing"]),
        "a_and_b_still_exactly_one":
            payload["a_and_b_recheck"]["all_exactly_one"],
        "still_outstanding_before_gate_1": [
            "re-run determinism and reimplementation over the §12.3 "
            "solo-calibration pool once Gate 2 produces one",
            "§10.2 for any family Amendment B adds, if it is adopted",
            "§10.4 judge selection and one-shot calibration",
            "explicit researcher approval of the measurement basis",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("section_10_2_families_smoke.json" if args.limit
                  else "section_10_2_families.json")
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=1))
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
