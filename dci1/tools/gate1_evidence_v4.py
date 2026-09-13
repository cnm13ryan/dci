"""Execute the §10.2 evidence for A and B against the real v4 response pool.

NOT part of the dci1v4 package and NOT a stage: this runs the registered
§10.2 procedures and writes their results to ``reports/gate1_v4/`` for review.
It approves nothing. Gate 1 remains unapproved and no registered evidence is
written.

**Scope: A and B only.** §10.2 requires the full evidence set for every family
verifier Gate 3 could admit, but the reference pool is under revision, so
family verifier work would be spent on families that may not exist. A's
exact-count rule and B's word-length rule are done here in full. Extending the
focal grid changes B's severity grid and not B's rule, so B's evidence is safe
to produce before the B-grid screen reports.

**The response pool.** §10.2 says "every calibration response". Gate 1 is stage
4 and Gate 2's solo calibration has not run, so no calibration response exists
yet. The pool used here is every genuine v4 generation on disk -- the §12.2
dense ladder screen, all three §12.1 cap screens and the Gate 0 pilot, on all
four models -- deduplicated by exact text. That is the largest natural response
population that exists at Gate 1, and it is far larger than the §10.3 sample.
The determinism and reimplementation lines must be re-run over the
solo-calibration pool when it exists; this establishes them over everything
available now, and says so.

Usage:
  PYTHONPATH=src python tools/gate1_evidence_v4.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.protocol import constants as C                       # noqa: E402
from dci1v4.protocol.hashing import sha_obj                      # noqa: E402
from dci1v4.stages.gate1 import (independent_agreement,          # noqa: E402
                                 three_process_determinism)
from dci1v4.verifiers import boundary, carryover                 # noqa: E402
from dci1v4.verifiers import verifier_source_hash                # noqa: E402
from dci1v4.verifiers.adversarial import (build_corpus,          # noqa: E402
                                          case_incidence,
                                          corpus_coverage)
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID  # noqa: E402

EVIDENCE = DCI1 / "evidence" / "dci1-v4"
OUT = DCI1 / "reports" / "gate1_v4"

#: A's exact-count rule and B's word-length rule, at every registered severity.
INSTRUMENTS = ([("A", n) for n in TARGET_GRID]
               + [("B", m) for m in FOCAL_GRID])

#: Batch size for the determinism payload. Every batch runs three separate
#: processes, so every response is covered by three separate executions.
DETERMINISM_BATCH = 500


# ------------------------------------------------------------- the pool
def response_pool() -> dict:
    """Every genuine v4 generation on disk, deduplicated by exact text."""
    sources = []
    texts: dict[str, dict] = {}
    for path in sorted(EVIDENCE.rglob("cache.jsonl")):
        rows = 0
        for line in path.open():
            row = json.loads(line)
            text = row.get("raw_response")
            if text is None:
                continue
            rows += 1
            texts.setdefault(text, {
                "first_seen": str(path.relative_to(DCI1)),
                "model_key": row.get("model_key"),
                "stage": row.get("stage")})
        sources.append({"path": str(path.relative_to(DCI1)), "rows": rows})
    ordered = sorted(texts)
    return {
        "sources": sources,
        "rows_read": sum(s["rows"] for s in sources),
        "distinct_texts": len(ordered),
        "pool_hash": sha_obj(ordered),
        "texts": ordered,
        "provenance": ("the §12.2 dense ladder screen, the three §12.1 cap "
                       "screens and the Gate 0 pilot, on all four registered "
                       "models, read from evidence/dci1-v4 without "
                       "regeneration"),
        "limitation": ("Gate 2 has not run, so no solo-calibration response "
                       "exists. The §10.2 determinism and reimplementation "
                       "lines must be re-run over the calibration pool when it "
                       "exists; this establishes them over every natural "
                       "response that exists at Gate 1."),
    }


# ------------------------------------------------------------ the evidence
def determinism_over(texts: list[str]) -> dict:
    """§10.2: three executions on three separate processes, agreement 1.000."""
    started = time.monotonic()
    batches = []
    for start in range(0, len(texts), DETERMINISM_BATCH):
        chunk = texts[start:start + DETERMINISM_BATCH]
        batches.append(three_process_determinism(INSTRUMENTS,
                                                 chunk)["agreement"])
    agreements = set(batches)
    return {
        "line": "determinism",
        "processes_per_batch": C.DETERMINISM_PROCESSES,
        "batches": len(batches),
        "processes_total": len(batches) * C.DETERMINISM_PROCESSES,
        "responses": len(texts), "instruments": len(INSTRUMENTS),
        "verdicts_per_process": len(texts) * len(INSTRUMENTS),
        "agreement": min(agreements) if agreements else 0.0,
        "all_batches_exactly_one": agreements == {1.0},
        "seconds": round(time.monotonic() - started, 1),
        "note": ("batched only to bound the subprocess payload; every response "
                 "is still covered by three separate processes, and the "
                 "reported agreement is the minimum over batches"),
    }


def boundary_evidence() -> dict:
    """§10.2: the frozen boundary suites for A and B."""
    suites = boundary.evaluate_suites()
    a_cases = list(boundary.TARGET_CASES)
    return {
        "line": "boundary suite",
        "A": {
            "cases": len(a_cases),
            "carried_from_v3": sum(1 for c in a_cases
                                   if c["origin"] == "carried_v3"),
            "authored_for_v4": sum(1 for c in a_cases
                                   if c["origin"] == "authored_v4"),
            "minimum_required": C.BOUNDARY_SUITE_MIN_CASES,
            "meets_minimum": len(a_cases) >= C.BOUNDARY_SUITE_MIN_CASES,
            "agreement": suites["agreement"].get("A"),
            "coverage_categories": sorted(boundary.TARGET_COVERAGE),
        },
        "B": {
            "cases": len(boundary.FOCAL_CASES),
            "carried_from_v3": 0,
            "authored_for_v4": len(boundary.FOCAL_CASES),
            "minimum_required": C.BOUNDARY_SUITE_MIN_CASES,
            "meets_minimum": (len(boundary.FOCAL_CASES)
                              >= C.BOUNDARY_SUITE_MIN_CASES),
            "agreement": suites["agreement"].get("B"),
            "coverage_categories": sorted(boundary.FOCAL_COVERAGE),
        },
        "suite_hash": suites["suite_hash"],
        "carried_specification_hash": boundary.carried_specification_hash(),
        "failures": suites["failures"],
        "coverage_counts": boundary.assert_coverage(),
        "frozen_before": ("qualification; the case texts and expected verdicts "
                          "are literals in verifiers/boundary.py and are inside "
                          "the canonical verifier hash"),
    }


def reimplementation_over(texts: list[str]) -> dict:
    """§10.2: the prose-only second implementation, agreement 1.000."""
    started = time.monotonic()
    result = independent_agreement(INSTRUMENTS, texts)
    values = set(result["agreement"].values())
    return {"line": "independent reimplementation",
            "responses_including_suites": result["responses"],
            "agreement": result["agreement"],
            "minimum_agreement": min(values) if values else 0.0,
            "all_exactly_one": values == {1.0},
            "disagreements": result["disagreements"],
            "source_material": result["source_material"],
            "seconds": round(time.monotonic() - started, 1)}


def adversarial_over(texts: list[str]) -> dict:
    """§10.2 / §24: the targeted corpus, and the realised frequency of every
    enumerated case in genuine generations.

    C1 deferred the realised-incidence half to Gate 2. It is computed here over
    the whole pre-screen pool instead, because the pool already exists.
    """
    corpus = build_corpus()
    return {
        "line": "adversarial corpus",
        "corpus_size": len(corpus),
        "coverage": corpus_coverage(),
        "incidence_over_the_targeted_corpus":
            case_incidence([item["text"] for item in corpus]),
        "realised_incidence_in_genuine_generations": case_incidence(texts),
        "genuine_generations": len(texts),
        "note": ("realised incidence is over the deduplicated natural pool; a "
                 "case with zero natural incidence is exercised by the "
                 "targeted corpus and by the frozen boundary suite, which is "
                 "what §10.2 requires of it"),
    }


def carry_over_evidence() -> dict:
    """§10.2: A's carry-over record. Refuses on any mismatch."""
    try:
        record = carryover.carry_over_record()
        boundary_record = carryover.boundary_carry_over()
        refused, detail = False, None
    except Exception as error:                      # CarryOverMismatch
        record, boundary_record, refused = None, None, True
        detail = f"{type(error).__name__}: {error}"
    return {
        "line": "carry-over",
        "applies_to": "A only; B is authored for v4 in full and carries nothing",
        "refused": refused, "refusal_detail": detail,
        "symbol_record": record, "boundary_record": boundary_record,
        "rule": ("A's instrument may supply carried evidence only when the "
                 "construct string, the segmentation source, the counting "
                 "source and the forty case texts with their expectations are "
                 "byte-identical to the v3 artifacts"),
    }


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
    print(f"pool: {len(texts)} distinct texts from {pool['rows_read']} rows",
          file=sys.stderr)

    suites = boundary.evaluate_suites()
    payload = {
        "artifact": "§10.2 verifier-correctness evidence for A and B",
        "classification": ("Gate 1 input evidence. Gate 1 is NOT approved by "
                           "this artifact and remains unapproved."),
        "scope": {
            "instruments": [f"{k}@{s}" for k, s in INSTRUMENTS],
            "in_scope": ["A: the exact-count rule", "B: the word-length rule"],
            "out_of_scope": ("every reference family verifier; the pool is "
                             "under revision and Gate 1 cannot be approved "
                             "until it is final"),
        },
        "response_pool": pool_meta,
        "determinism": determinism_over(texts),
        "boundary_suite": boundary_evidence(),
        "independent_reimplementation": reimplementation_over(texts),
        "adversarial_corpus": adversarial_over(texts),
        "carry_over": carry_over_evidence(),
        "canonical_verifier_hash": verifier_source_hash(),
    }
    payload["summary"] = {
        "determinism_exactly_one":
            payload["determinism"]["all_batches_exactly_one"],
        "boundary_agreement_exactly_one": (
            {v for k, v in suites["agreement"].items() if k in ("A", "B")}
            == {1.0}),
        "reimplementation_exactly_one":
            payload["independent_reimplementation"]["all_exactly_one"],
        "carry_over_refused": payload["carry_over"]["refused"],
        "A_and_B_meet_10_2": (
            payload["determinism"]["all_batches_exactly_one"]
            and payload["independent_reimplementation"]["all_exactly_one"]
            and not payload["carry_over"]["refused"]
            and payload["boundary_suite"]["A"]["agreement"] == 1.0
            and payload["boundary_suite"]["B"]["agreement"] == 1.0
            and payload["boundary_suite"]["A"]["meets_minimum"]
            and payload["boundary_suite"]["B"]["meets_minimum"]),
        "still_outstanding_before_gate_1": [
            "§10.2 for every family verifier the final pool admits",
            "§10.4 judge selection and one-shot calibration",
            "explicit researcher approval of the measurement basis",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("section_10_2_smoke.json" if args.limit
                  else "section_10_2.json")
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=1))
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
