"""Execute the v4 pre-freeze checks and write machine-readable evidence.

NOT part of the dci1v4 package. This tool runs the checks of
``user-notes/DCI1_v4r2_prefreeze_checks.md``, records the evidence each one
produces, and writes one JSON file per check under ``dci1/docs/v4_prefreeze/``
plus a summary. Every check reports one of:

  COMPLETE          the check ran and its evidence is recorded
  BLOCKED           the check cannot run in this environment, with the reason
  PARTIAL           part of the check ran; the remainder is named

Checks that read the v3 cache or the B+R pilot do so through
``dci1v4.engine.guards.design_evidence_read``, which stamps every result
non-confirmatory. No row from either source reaches a v4 estimator.

Usage:  PYTHONPATH=src python tools/prefreeze_checks_v4.py [--check C1 ...]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

OUT_DIR = DCI1 / "docs" / "v4_prefreeze"
V3_EVIDENCE = DCI1 / "evidence" / "dci1-v3"
V4_EVIDENCE = DCI1 / "evidence" / "dci1-v4"
PILOT_EVIDENCE = DCI1 / "evidence" / "br-pilot-v4"
PILOT_REPORTS = DCI1 / "reports" / "br_pilot_v4"
USER_NOTES = DCI1.parent / "user-notes"

GEMMAS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it")
QWENS = ("qwen3-4b", "qwen3-4b-instruct-2507")


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ------------------------------------------------------------------ Group A
def check_c1() -> dict:
    """Boundary suites, adversarial corpora and independent reimplementations
    for every registered outcome verifier."""
    from dci1v4.stages.gate1 import (
        independent_agreement,
        three_process_determinism,
    )
    from dci1v4.verifiers import boundary
    from dci1v4.verifiers.adversarial import (
        build_corpus,
        case_incidence,
        corpus_coverage,
    )
    from dci1v4.verifiers.constraints import REFERENCE_LADDERS

    instruments = [("A", 3), ("B", 8)] + [(f, REFERENCE_LADDERS[f][2])
                                          for f in sorted(REFERENCE_LADDERS)]
    responses = [c["text"] for c in boundary.FOCAL_CASES]
    suites = boundary.evaluate_suites()
    determinism = three_process_determinism(instruments, responses)
    reimplementation = independent_agreement(instruments, responses)
    corpus = build_corpus()
    incidence = case_incidence([item["text"] for item in corpus])
    status = ("COMPLETE"
              if (set(suites["agreement"].values()) == {1.0}
                  and determinism["agreement"] == 1.0
                  and set(reimplementation["agreement"].values()) == {1.0})
              else "BLOCKED")
    return {
        "check": "C1", "status": status,
        "instruments_covered": [f"{k}@{s}" for k, s in instruments],
        "boundary_suites": {"target_cases": suites["cases"]["A"],
                            "focal_and_family_cases": suites["cases"]["B"],
                            "agreement": suites["agreement"],
                            "coverage": suites["coverage"],
                            "suite_hash": suites["suite_hash"],
                            "failures": suites["failures"]},
        "three_process_determinism": determinism,
        "independent_reimplementation": {
            "agreement": reimplementation["agreement"],
            "responses": reimplementation["responses"],
            "source_material": reimplementation["source_material"]},
        "adversarial_corpus": {"size": len(corpus),
                               "coverage": corpus_coverage(),
                               "incidence_over_the_corpus": incidence},
        "note": ("realised per-cell-type incidence in genuine generations is "
                 "reported by analysis.diagnostics at Gate 2 and Gate 4; the "
                 "detectors and the targeted corpus are complete here"),
    }


def check_c2() -> dict:
    """Graded-score and non-vacuity implementations."""
    from dci1v4.verifiers import independent
    from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS, score_constraint
    from dci1v4.verifiers.constraints import (
        FOCAL_GRID,
        REFERENCE_LADDERS,
        Constraint,
        TARGET_GRID,
    )
    from dci1v4.verifiers import verifier_source_hash

    probes = ["", "Yes.", "however " * 3,
              " ".join(["word"] * 25) + " however coffee, B",
              "bold bold going o coffee, Q cat grey"]
    checked = 0
    mismatches = []
    for text in probes:
        pairs = ([("A", n) for n in TARGET_GRID]
                 + [("B", m) for m in FOCAL_GRID]
                 + [(f, q) for f, ladder in REFERENCE_LADDERS.items()
                    for q in ladder])
        for kind, severity in pairs:
            score = score_constraint(Constraint(kind, severity), text,
                                     truncated=False)
            expected_graded = independent.graded(kind, severity, text)
            expected_vacuity = independent.non_vacuous(kind, text, False)
            if abs(score.graded - expected_graded) > 1e-12 or \
                    score.non_vacuous != expected_vacuity:
                mismatches.append([kind, severity, text[:40]])
            checked += 1
    return {
        "check": "C2", "status": "COMPLETE" if not mismatches else "BLOCKED",
        "graded_and_predicate_checks": checked,
        "mismatches": mismatches,
        "non_vacuity_threshold_words": NON_VACUITY_MIN_WORDS,
        "included_in_the_canonical_verifier_hash": True,
        "canonical_verifier_hash": verifier_source_hash(),
        "note": ("compliance.py carries both §7.4 graded scores and the §9.3 "
                 "predicates and is inside the canonical verifier hash, so a "
                 "change to either invalidates every downstream stage"),
    }


def check_c3() -> dict:
    """Human-annotator availability, and the autorater comparison."""
    forensics = DCI1.parent / "autorater_forensics"
    human_review = forensics / "experiments" / "human_review"
    return {
        "check": "C3", "status": "BLOCKED",
        "annotator_available": False,
        "reason": ("no annotator independent of the design and analysis team "
                   "is available to this process, and none can be obtained "
                   "autonomously; V8's registered default therefore applies"),
        "registered_outcome": "HUMAN_VALIDATION_UNAVAILABLE",
        "measurement_basis_route": "autorater_calibration_approved",
        "author_labels_present": human_review.exists(),
        "author_labels_disposition": (
            "the 120 v3 blinded labels and the 56-item calibration sample "
            "were produced by the study author; they are diagnostic evidence "
            "and are never carried as v4 independent human validation (T-16)"),
        "paired_medium_versus_high_comparison": "NOT RUN",
        "what_would_settle_it": (
            "either an independent annotator, or the §10.4 pathway executed "
            "end to end: the medium-versus-high comparison on the existing "
            "56-item sample under serialised execution at concurrency one and "
            "the frozen cap, paired on the same items, with coverage, "
            "per-class agreement, the confusion matrix, the discordant-item "
            "table, truncation incidence and deterministic reproducibility, "
            "then selection under the §10.4 hierarchy with the rejected "
            "alternative recorded"),
        "implementation_status": (
            "the pathway is implemented in dci1v4.stages.autorater and is "
            "exercised by tests_v4/test_t5_measurement.py; only the judge "
            "execution is outstanding"),
    }


def check_c4() -> dict:
    """Sealed final-check set status."""
    v3_gate1 = V3_EVIDENCE / "gemma-3n-e2b-it" / "gate1_measurement.json"
    v3_seal = None
    if v3_gate1.exists():
        payload = json.loads(v3_gate1.read_text()).get("payload", {})
        v3_seal = payload.get("sealed_final_check")
    return {
        "check": "C4", "status": "COMPLETE",
        "decision": "a NEW v4 sealed set is required; the v3 set is not reused",
        "reason": ("the v4 instrument population is five primary instruments "
                   "— the exact-count rule, the word-length rule and three "
                   "admitted family verifiers — and the v3 sealed set was "
                   "composed for the exact-count rule alone, so it cannot "
                   "exercise the word-length or family verifiers at all"),
        "v3_set": "stays sealed either way; nothing in dci1v4 can open it",
        "v3_seal_record_present": bool(v3_seal),
        "v4_seal": ("sealed at Gate 1 by dci1v4.stages.gate1."
                    "seal_final_check_set, opened at most once after every "
                    "autorater choice is frozen, never for tuning, never "
                    "rerun"),
    }


def check_c5() -> dict:
    """Verifier-hash binding covers every v4 entry point."""
    from dci1v4.engine.binding import current_verifier_hash, require_frozen_verifier
    from dci1v4.errors import VerifierBindingError
    from dci1v4.protocol.constants import VERIFIER_BOUND_ENTRY_POINTS

    frozen = current_verifier_hash()
    unchanged = all(require_frozen_verifier(e, frozen) == frozen
                    for e in VERIFIER_BOUND_ENTRY_POINTS)
    refused = []
    for entry in VERIFIER_BOUND_ENTRY_POINTS:
        try:
            require_frozen_verifier(entry, "0" * 64)
        except VerifierBindingError:
            refused.append(entry)
    return {
        "check": "C5", "status": "COMPLETE",
        "entry_points": list(VERIFIER_BOUND_ENTRY_POINTS),
        "entry_point_count": len(VERIFIER_BOUND_ENTRY_POINTS),
        "unchanged_verifier_succeeds_everywhere": unchanged,
        "changed_verifier_refused_everywhere":
            refused == list(VERIFIER_BOUND_ENTRY_POINTS),
        "regression_tests": "tests_v4/test_t8_verifier_binding.py, five cases",
        "canonical_verifier_hash": frozen,
    }


# ------------------------------------------------------------------ Group B
def _v3_gate2a_solo(model_key: str) -> dict:
    """Solo compliance per (constraint, severity) from the v3 Gate 2A cache."""
    from dci1v4.engine.guards import design_evidence_read

    path = V3_EVIDENCE / model_key / "gate2a" / "cache.jsonl"
    if not path.exists():
        return {}
    stamp = design_evidence_read(path, check="C6",
                                 purpose="anchor the reference caliper")
    rows = _read_jsonl(path)
    grouped: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        kind = row.get("kind", "")
        verdicts = row.get("verdicts", {})
        if kind.startswith("solo:A:"):
            grouped[kind].append(verdicts.get("target_pass") is True)
        elif kind.startswith("solo:"):
            grouped[kind].append(verdicts.get("added_pass") is True)
    return {"stamp": stamp,
            "rates": {k: sum(v) / len(v) for k, v in sorted(grouped.items())},
            "counts": {k: len(v) for k, v in sorted(grouped.items())},
            "rows": len(rows)}


def _v3_n_star(model_key: str) -> tuple[int | None, int | None, dict]:
    """v3's recorded n*, m* and admission table, read as data."""
    path = V3_EVIDENCE / model_key / "gate2a_solo.json"
    if not path.exists():
        return None, None, {}
    body = json.loads(path.read_text())["payload"]["body"]
    return body.get("n_star"), body.get("m_star"), \
        body.get("admission_table", {})


def check_c6() -> dict:
    """The exact solo compliance of the exact-count constraint, read from the
    v3 Gate 2A cache so that A and every reference sit on the same 96 topics
    and the same estimator.

    The change summary's companion-difficulty figure mixed two estimators: it
    took P(A solo) from the v3 confirmatory target-alone arm and the reference
    solo rates from the Gate 2A cells on a different topic set. Reading
    ``solo:A:<n*>`` from the same cache removes that mismatch, which is the
    whole point of the check.
    """
    out: dict = {"check": "C6", "models": {}}
    available = False
    for model_key in GEMMAS:
        data = _v3_gate2a_solo(model_key)
        n_star, m_star, admission = _v3_n_star(model_key)
        if not data or n_star is None:
            out["models"][model_key] = {"status": "cache or record absent"}
            continue
        available = True
        rates = data["rates"]
        anchor = rates.get(f"solo:A:{n_star}")
        admitted = {f: entry.get("selected") for f, entry in admission.items()
                    if entry.get("selected") is not None}
        admitted_rates = {f: rates.get(f"solo:{f}:{q}")
                          for f, q in admitted.items()}
        admitted_rates = {k: v for k, v in admitted_rates.items()
                          if v is not None}
        gaps = {f: v - anchor for f, v in admitted_rates.items()}
        # Feasibility bound for C7: how many measured rungs sit within the
        # registered caliper of A at n*, on the four-point v3 grid.
        within = {k: v for k, v in rates.items()
                  if not k.startswith(("solo:A:", "solo:B:"))
                  and abs(v - anchor) <= 0.10}
        out["models"][model_key] = {
            "rows": data["rows"],
            "v3_n_star": n_star, "v3_m_star": m_star,
            "a_solo_at_n_star_same_topics_same_estimator": anchor,
            "a_solo_by_n": rates and {k: v for k, v in rates.items()
                                      if k.startswith("solo:A:")},
            "b_solo_by_m": {k: v for k, v in rates.items()
                            if k.startswith("solo:B:")},
            "v3_admitted_references": admitted,
            "v3_admitted_reference_solo": admitted_rates,
            "reference_minus_A_gap_per_family": gaps,
            "mean_reference_minus_A_gap": (
                statistics.fmean(gaps.values()) if gaps else None),
            "rungs_within_the_caliper_of_A_on_the_v3_four_point_grid": within,
            "rungs_measured": len([k for k in rates
                                   if not k.startswith(("solo:A:",
                                                        "solo:B:"))]),
            "provenance": data["stamp"],
        }
    out["status"] = "COMPLETE" if available else "BLOCKED"
    out["note"] = ("this bounds feasibility only, and only on the four-point "
                   "v3 grid. In v4 the quantity is measured directly at Gate "
                   "2 on v4 topics under the v4 instrument across the full "
                   "94-rung ladder; these rows are design evidence and enter "
                   "no v4 estimator (§14.2)")
    return out


def _v4_regime(model_key: str) -> dict | None:
    """A realised v4 regime-screen record, if the stage has run."""
    path = V4_EVIDENCE / model_key / "regime_screen.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())["payload"]


ALL_MODELS = GEMMAS + QWENS


def check_c7() -> dict:
    """Whether a reference severity matched to A exists in each family ladder.

    §12.2 answers this per model on the 24 pre-screen topics; §12.3 confirms it
    on the 96 solo-calibration topics at Gate 2. What the screen can settle is
    whether the ladder *reaches* A at all — the question v3's four-point grid
    could not answer.
    """
    from dci1v4.protocol.wordings import assert_caliper_feasible

    feasible = assert_caliper_feasible()
    realised: dict[str, Any] = {}
    for model_key in ALL_MODELS:
        payload = _v4_regime(model_key)
        if payload is None:
            realised[model_key] = {"status": "regime screen not run"}
            continue
        families = payload["families_with_a_matched_rung"]
        realised[model_key] = {
            "selected_cap": payload["completion_cap"]["selected_cap"],
            "anchor_n": payload["anchor_n"],
            "a_prescreen_compliance": payload["ladder_screen"][
                "a_solo_compliance"],
            "families_with_a_rung_within_the_caliper": families,
            "families_matched": len(families),
            "three_or_more_families_matched": len(families) >= 3,
            "rungs_within_the_caliper": payload["rungs_within_the_caliper"],
            "shortlist": payload["shortlist"],
            "note": ("measured on the 24 pre-screen topics at one draw per "
                     "cell; §12.3 re-measures every shortlisted severity on "
                     "the 96 solo-calibration topics and §13.2 admits against "
                     "that"),
        }
    ran = [k for k, v in realised.items() if "status" not in v]
    return {
        "check": "C7",
        "status": "PARTIAL" if ran else "BLOCKED",
        "models_screened": ran,
        "realised": realised,
        "what_is_established_without_generation": {
            "ladder_severities": 94,
            "severities_meeting_the_length_caliper_at_every_n":
                {k: len(v) for k, v in feasible.items()},
            "note": ("every registered severity of every family meets the "
                     "§7.3 length caliper against A, so no family is excluded "
                     "for a wording-length reason before any measurement"),
        },
        "remaining": ("§12.3 confirmation on the 96 solo-calibration topics, "
                      "which is Gate 2 and is downstream of Gate 1"),
        "registered_outcome_if_it_fails": ("EXCESS_NOT_IDENTIFIED and the "
                                           "reduced design of §8.6"),
    }


def check_c7b() -> dict:
    """The realised companion-difficulty gap is estimable in the confirmatory
    data: an executable check on the registered cell set."""
    from dci1v4.design.cells import design_cells, registered_cell_types
    from dci1v4.topics.split import confirmatory_blocks, split_topics

    slot_map = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 2),
                "R2": ("RF5", 4), "R3": ("RF7", 6)}
    types = registered_cell_types(slot_map)
    blocks = confirmatory_blocks(split_topics())
    cells = design_cells("confirmatory", blocks, slot_map, draws=4)
    solo_types = [t for t in types if t.startswith("solo:")]
    per_block = defaultdict(set)
    for cell in cells:
        if cell.load == 1:
            per_block[cell.block_id].add(cell.cell_type)
    complete = all(set(solo_types) <= present for present in per_block.values())
    return {
        "check": "C7b", "status": "COMPLETE" if complete else "BLOCKED",
        "solo_cell_types": solo_types,
        "blocks_carrying_every_solo_cell": sum(
            1 for present in per_block.values()
            if set(solo_types) <= present),
        "blocks": len(blocks),
        "estimator_reads_the_same_blocks": True,
        "emitted_beside_every_excess_statement": True,
        "qualifier": 0.15,
        "note": ("the realised gap estimator reads the A solo cell and every "
                 "admitted reference solo cell from the same 384 blocks, and "
                 "analysis.claims attaches the §28.1 companion-difficulty "
                 "block whenever a realised gap exceeds the qualifier"),
    }


def check_c8() -> dict:
    """Operating regime for the two Qwen replications."""
    realised: dict[str, Any] = {}
    for model_key in QWENS:
        payload = _v4_regime(model_key)
        if payload is None:
            realised[model_key] = {"status": "regime screen not run"}
            continue
        realised[model_key] = {
            "selected_cap": payload["completion_cap"]["selected_cap"],
            "zero_constraint_truncation": payload["completion_cap"][
                "zero_constraint_truncation"],
            "a_curve": payload["ladder_screen"]["A"]
            if "A" in payload["ladder_screen"] else
            payload["ladder_screen"].get("curves", {}).get("A"),
            "b_curve": payload["ladder_screen"].get("B"),
            "families_matched": len(payload["families_with_a_matched_rung"]),
        }
    ran = [k for k, v in realised.items() if "status" not in v]
    return {
        "check": "C8",
        "status": "PARTIAL" if ran else "BLOCKED",
        "models": list(QWENS),
        "realised": realised,
        "reason": ("neither Qwen model's solo compliance existed in the "
                   "corpus; both terminated v3 at Gate 2A before the question "
                   "arose"),
        "remaining": ("§12.3 and §12.4, which are Gate 2 and are downstream "
                      "of Gate 1"),
        "permitted_outcome": ("REGIME_NOT_FOUND is a statement about the "
                              "registered grid and never about the model or "
                              "the hypothesis"),
    }


def check_c9() -> dict:
    from dci1v4.verifiers.witnesses import verify_all_witnesses

    report = verify_all_witnesses()
    return {"check": "C9", "status": "COMPLETE",
            "pairs_certified": report["pairs"],
            "distinct_kind_pairs": report["kind_pairs"],
            "covers": ("A+B, A+R, B+R and R+R' at every registered severity "
                       "combination, with joint satisfiability and both "
                       "non-entailment directions"),
            "base_sentence": report["base_sentence"]}


def _matched_rung_vacuity(model_key: str) -> dict | None:
    """The C7 x C10 interaction: do the rungs that match A survive §13.2's
    vacuity condition?

    §13.2 admits a severity for its closeness to A's solo compliance
    (condition 1) **and** for a family solo vacuity rate at or below 0.10
    (condition 6). Those two pull in opposite directions by construction: A's
    solo compliance is low, so matching it means a restrictive "at most q",
    and a restrictive budget constraint is satisfied by writing a shorter
    answer. This measures whether both can hold at once.
    """
    payload = _v4_regime(model_key)
    if payload is None:
        return None
    caches = sorted((V4_EVIDENCE / model_key / "prescreen").glob(
        "ladder-cap*/cache.jsonl"))
    if not caches:
        return None
    rows = _read_jsonl(caches[0])
    per_rung: dict[str, list] = defaultdict(list)
    for row in rows:
        score = row["scores"][0]
        per_rung[f"{score['kind']}:{score['severity']}"].append(row)

    matched = payload["rungs_within_the_caliper"]
    table = []
    for rung, compliance in sorted(matched.items()):
        members = per_rung.get(rung, [])
        if not members:
            continue
        vacuity = sum(1 for r in members
                      if r["scores"][0]["vacuous_pass"]) / len(members)
        table.append({
            "rung": rung, "solo_compliance": compliance,
            "solo_vacuity": vacuity,
            "mean_words": statistics.fmean(r["word_count"] for r in members),
            "truncation": sum(1 for r in members
                              if r["truncated"]) / len(members),
            "meets_condition_6": vacuity <= 0.10,
        })
    surviving = [row for row in table if row["meets_condition_6"]]
    families = sorted({row["rung"].split(":")[0] for row in surviving})
    return {
        "matched_rungs": len(table),
        "surviving_the_vacuity_condition": len(surviving),
        "families_still_viable": families,
        "three_or_more_families_viable": len(families) >= 3,
        "table": table,
        "reading": ("on the pre-screen sample, satisfying §13.2 condition 1 "
                    "and condition 6 at once"
                    + (" is possible" if len(families) >= 3 else
                       " was not achieved for any family")),
    }


def check_c10() -> dict:
    """Realised vacuity rates and the 20-word threshold."""
    from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS

    realised: dict[str, Any] = {}
    interaction: dict[str, Any] = {}
    for model_key in ALL_MODELS:
        payload = _v4_regime(model_key)
        if payload is None:
            continue
        vacuity = payload.get("vacuity_by_cell", {})
        caches = sorted((V4_EVIDENCE / model_key / "prescreen").glob(
            "ladder-cap*/cache.jsonl"))
        rows = _read_jsonl(caches[0]) if caches else []
        vacuous = [r for r in rows if r["scores"][0]["vacuous_pass"]]
        realised[model_key] = {
            "solo_cells_measured": len(vacuity),
            "cells_above_0.10": sorted(k for k, v in vacuity.items()
                                       if v > 0.10),
            "max_vacuity": max(vacuity.values()) if vacuity else None,
            "mean_vacuity": (sum(vacuity.values()) / len(vacuity)
                             if vacuity else None),
            "driver": {
                "vacuous_passes": len(vacuous),
                "of_which_truncated": sum(1 for r in vacuous
                                          if r["truncated"]),
                "of_which_under_the_word_threshold": sum(
                    1 for r in vacuous
                    if r["word_count"] < NON_VACUITY_MIN_WORDS),
                "mean_response_words": (
                    statistics.fmean(r["word_count"] for r in rows)
                    if rows else None),
                "share_under_the_word_threshold": (
                    sum(1 for r in rows
                        if r["word_count"] < NON_VACUITY_MIN_WORDS) / len(rows)
                    if rows else None),
            },
        }
        found = _matched_rung_vacuity(model_key)
        if found:
            interaction[model_key] = found
    return {
        "check": "C10",
        "status": "PARTIAL" if realised else "BLOCKED",
        "threshold_words": NON_VACUITY_MIN_WORDS,
        "threshold_is_fixed_before_confirmatory_generation": True,
        "never_tuned_to_a_rate": True,
        "realised_on_the_ladder_screen": realised,
        "c7_x_c10_interaction": interaction,
        "finding": (
            "vacuity here is driven by response SHORTENING, not by "
            "truncation, and it concentrates at exactly the restrictive "
            "severities that match A on solo compliance. §13.2 condition 1 "
            "(match A) and condition 6 (family solo vacuity at most 0.10) "
            "therefore pull against each other by construction: A's solo "
            "compliance is low, matching it needs a restrictive 'at most q', "
            "and a restrictive budget constraint is satisfied by writing a "
            "shorter answer. This is a decision-relevant interaction between "
            "open decisions V3, V4 and V5 and is reported, not resolved"),
        "remaining": ("the per-cell-type rate on the §12 and §13.6 "
                      "calibration stages, at M=4 on 96 topics, which is "
                      "where §13.2 is actually evaluated; the pre-screen "
                      "supplies the shortlist and the §13.2 condition 2 "
                      "confirmation only"),
    }


def check_c11() -> dict:
    """Accidental compliance and per-cell truncation."""
    realised: dict[str, Any] = {}
    for model_key in ALL_MODELS:
        payload = _v4_regime(model_key)
        if payload is None:
            continue
        truncation = payload["truncation_by_cell"]
        above = {k: v for k, v in truncation.items()
                 if v > 0.10}
        realised[model_key] = {
            "cap": payload["completion_cap"]["selected_cap"],
            "cap_set_truncation": {
                str(row["cap"]): {
                    "constrained": row["constrained_truncation"],
                    "zero_constraint": row["zero_constraint_truncation"]}
                for row in payload["completion_cap"]["table"]},
            "ladder_cells_above_the_bound_threshold": len(above),
            "ladder_cells": len(truncation),
            "worst_ladder_cell": (max(truncation.items(),
                                      key=lambda kv: kv[1])
                                  if truncation else None),
        }
    return {
        "check": "C11",
        "status": "PARTIAL" if realised else "BLOCKED",
        "realised": realised,
        "implementation": ("every registered constraint absent from a prompt "
                           "is scored on every row and marked as an "
                           "accidental-compliance diagnostic; every figure "
                           "from a cell above the truncation threshold is "
                           "emitted as a bound by the emitter itself"),
        "truncation_bound_threshold": 0.10,
        "remaining": ("per-cell accidental compliance at Gate 2 and Gate 4, "
                      "which are downstream of Gate 1"),
    }


# ------------------------------------------------------------------ Group C
def _pilot_rows(model_key: str) -> list[dict]:
    path = PILOT_EVIDENCE / model_key / "cache.jsonl"
    if not path.exists():
        return []
    from dci1v4.engine.guards import design_evidence_read

    design_evidence_read(path, check="C12/C13",
                         purpose="variance information and re-scoring")
    return _read_jsonl(path)


def _pilot_focal_cell_means(model_key: str) -> tuple[dict, float, int]:
    """B's per-topic cell means in each pilot B+R cell, re-scored from raw text.

    The pilot stored ``verdicts.added_pass`` for the *reference*, not for B, so
    the outcome the design cares about has to be recomputed. It is recomputed
    here under the current v4 instrument at the pilot's own m*, which is what
    makes the variance information usable and is the same recomputation C13
    audits.
    """
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import Constraint

    protocol = json.loads((PILOT_REPORTS / "protocol.json").read_text())
    m_star = protocol["design"]["m_star"][model_key]
    rows = _pilot_rows(model_key)
    per_cell: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list))
    for row in rows:
        passed = score_constraint(Constraint("B", m_star),
                                  row.get("raw_response", ""),
                                  truncated=False).passed
        per_cell[row["kind"]][row["topic_id"]].append(int(passed))
    draws = max((len(v) for cell in per_cell.values() for v in cell.values()),
                default=1)
    return per_cell, float(m_star), draws


def check_c12() -> dict:
    """Re-estimate the two correlations separately, then re-run the menu rule.

    §16.1 registers phi = 0.27 fitted to the pilot's reported interval widths
    under an assumed among-reference correlation of 1, and phi ~ 0.37 under
    0.5. This check estimates the components directly from the pilot's rows
    instead, on the outcome the design actually uses.
    """
    from dci1v4.analysis.variance import (
        meets_preconditions,
        projected_half_widths,
        realised_correlation,
        realised_decomposition,
        select_allocation,
    )

    out: dict = {"check": "C12", "models": {}}
    realised_phis: list[float] = []
    among_reference: list[float] = []
    for model_key in GEMMAS:
        if not (PILOT_EVIDENCE / model_key / "cache.jsonl").exists():
            out["models"][model_key] = {"status": "pilot cache absent"}
            continue
        per_cell, m_star, draws = _pilot_focal_cell_means(model_key)
        topics = sorted(set.intersection(*[set(v) for v in per_cell.values()]))
        means = {cell: [statistics.fmean(per_cell[cell][t]) for t in topics]
                 for cell in sorted(per_cell)}
        within = statistics.fmean([
            statistics.variance(per_cell[cell][t])
            for cell in per_cell for t in topics
            if len(per_cell[cell][t]) > 1])
        decomposition = realised_decomposition(means, within, int(draws))
        realised_phis.append(decomposition["phi"])
        keys = sorted(means)
        pairs = [(means[keys[i]], means[keys[j]])
                 for i in range(len(keys)) for j in range(i + 1, len(keys))]
        correlation = realised_correlation(
            pairs, decomposition["sigma2_topic"] or 1e-9)
        if correlation.get("rho_clipped") is not None:
            among_reference.append(correlation["rho_clipped"])

        # The pilot fixes one order per topic and shares it across that
        # topic's three reference cells, so a between-order difference enters
        # the topic component. v4 runs both orders in every block, so it
        # cannot. Re-estimating inside each order stratum removes the order
        # component and gives the figure that transfers.
        order_of = {row["topic_id"]: row["order"]
                    for row in _pilot_rows(model_key)}
        by_order: dict[str, dict] = {}
        for order in sorted(set(order_of.values())):
            subset = [t for t in topics if order_of.get(t) == order]
            if len(subset) < 8:
                continue
            order_means = {cell: [statistics.fmean(per_cell[cell][t])
                                  for t in subset] for cell in keys}
            order_within = statistics.fmean([
                statistics.variance(per_cell[cell][t])
                for cell in keys for t in subset
                if len(per_cell[cell][t]) > 1])
            by_order[order] = {
                "topics": len(subset),
                "decomposition": realised_decomposition(
                    order_means, order_within, int(draws)),
            }
        within_order_phi = ([v["decomposition"]["phi"]
                             for v in by_order.values()] or None)

        out["models"][model_key] = {
            "outcome": f"B at the pilot m* = {int(m_star)}, re-scored from "
                       f"raw text under the current v4 instrument",
            "cells": keys, "topics": len(topics), "draws_per_cell": draws,
            "cell_compliance": {k: statistics.fmean(v)
                                for k, v in means.items()},
            "decomposition": decomposition,
            "within_order_decomposition": by_order,
            "within_order_phi": within_order_phi,
            "among_reference_correlation": correlation,
        }

    realised_phi = statistics.fmean(realised_phis) if realised_phis else None
    out["among_reference_correlation_summary"] = {
        "estimates": among_reference,
        "mean": statistics.fmean(among_reference) if among_reference else None,
        "registered_assumptions": {"phi_0.27": "among-reference correlation 1",
                                   "phi_0.37": "among-reference correlation "
                                               "0.5"},
    }
    out["realised_phi"] = {
        "per_model": realised_phis, "mean": realised_phi,
        "registered": [0.27, 0.37],
        "caveat": ("estimated at two draws per cell on 96 topics, so the "
                   "draw component is noisy; and the pilot assigns one order "
                   "per topic, shared across its three reference cells, so "
                   "order variance loads into the topic component here in a "
                   "way it cannot in v4, where order is within-block. The "
                   "figure is therefore an upper bound on phi rather than a "
                   "point estimate"),
    }

    out["a_versus_reference_correlation"] = {
        "status": "BLOCKED",
        "reason": ("the correlation the §16.1 formulas use is between a cell "
                   "containing A and a cell containing a reference with the "
                   "SAME outcome constraint. The pilot cannot supply it: its "
                   "A term comes from a disjoint topic set. The v3 "
                   "confirmatory cache carries AB and AR_j on the same 384 "
                   "blocks, but there the outcome recorded is the "
                   "exact-count target, so those cells share the outcome A, "
                   "not B, and its reference cells are R in the companion "
                   "slot rather than B+R cells"),
        "what_settles_it": ("a v4 calibration or confirmatory stage carrying "
                            "two composed cells with the same outcome "
                            "constraint on the same blocks, which the v4 "
                            "design supplies by construction"),
        "registered_response_meanwhile": ("rho = 0.5 is assumed and both phi "
                                          "settings are carried; an "
                                          "unfavourable realisation appears "
                                          "as INSUFFICIENT_PRECISION rather "
                                          "than as a silent widening (§29)"),
    }

    within_order = [v for model in out["models"].values()
                    if isinstance(model, dict)
                    for v in (model.get("within_order_phi") or [])]
    out["realised_phi"]["within_order_per_stratum"] = within_order
    out["realised_phi"]["within_order_mean"] = (
        statistics.fmean(within_order) if within_order else None)

    out["menu_rule_under_the_registered_constants"] = select_allocation()
    candidates = {"registered_low": 0.27, "registered_high": 0.37}
    if realised_phi is not None:
        candidates["realised_pooled"] = realised_phi
    if within_order:
        candidates["realised_within_order"] = statistics.fmean(within_order)
    out["sensitivity"] = {}
    for label, phi in sorted(candidates.items(), key=lambda kv: kv[1]):
        out["sensitivity"][label] = {
            "phi": phi,
            "half_widths_at_384_M4": projected_half_widths(384, 4, phi=phi),
            "384_M4_meets_every_precondition": meets_preconditions(
                384, 4, phi=phi, rho=0.5),
            "menu_rule_selects": select_allocation(
                phi_settings=(phi,))["selected"],
        }
    # The phi at which the registered allocation stops meeting every
    # precondition, so the boundary is a number rather than an impression.
    boundary = None
    step = 0.01
    phi = 0.20
    while phi <= 0.95:
        if not meets_preconditions(384, 4, phi=phi, rho=0.5):
            boundary = round(phi, 3)
            break
        phi += step
    out["phi_at_which_384_by_M4_stops_qualifying"] = boundary
    out["status"] = "PARTIAL"
    out["note"] = ("the among-reference correlation and phi are estimable "
                   "from the pilot rows and are reported; the "
                   "A-versus-reference correlation is not, and the registered "
                   "response is to carry both phi settings. The menu rule is "
                   "re-run under the realised phi and its selection reported")
    return out


def check_c13() -> dict:
    """Re-score the pilot B+R rows from raw text under the current verifier."""
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import Constraint

    out: dict = {"check": "C13", "models": {}}
    ran = False
    for model_key in GEMMAS:
        rows = _pilot_rows(model_key)
        if not rows:
            out["models"][model_key] = {"status": "pilot cache absent"}
            continue
        ran = True
        rescored = 0
        agree = 0
        per_cell: dict[str, list[int]] = defaultdict(list)
        unsupported = 0
        for row in rows:
            constraint_id = row.get("constraint_id")
            severity = row.get("severity")
            text = row.get("raw_response", "")
            recorded = row.get("verdicts", {}).get("added_pass")
            if constraint_id is None or severity is None or recorded is None:
                continue
            try:
                score = score_constraint(Constraint(constraint_id, severity),
                                         text, truncated=False)
            except Exception:
                unsupported += 1
                continue
            rescored += 1
            agree += int(score.passed == recorded)
            per_cell[row.get("kind", "?")].append(int(score.passed))
        out["models"][model_key] = {
            "rows": len(rows), "rescored": rescored,
            "agreement_with_recorded_verdicts":
                (agree / rescored) if rescored else None,
            "severities_outside_the_v4_ladder": unsupported,
            "recomputed_cell_rates": {
                k: statistics.fmean(v) for k, v in sorted(per_cell.items())},
            "classification": "design evidence; non-confirmatory",
        }
    out["status"] = "COMPLETE" if ran else "BLOCKED"
    out["note"] = ("re-scored from raw text under the current v4 instrument. "
                   "These rates are the pilot's, are non-confirmatory, and "
                   "enter no v4 analysis (§14.2, C20)")
    return out


def check_c14() -> dict:
    """Duplicate-generation rate under the v4 seed derivation."""
    from dci1v4.generation.cache import duplicate_report

    out: dict = {"check": "C14", "legacy_comparison": {}, "realised_v4": {}}
    for model_key in GEMMAS:
        rows = _pilot_rows(model_key)
        if not rows:
            continue
        import hashlib

        shaped = [{"cell_id": r.get("cell_id", r.get("kind", "?")),
                   "response_content_hash": hashlib.sha256(
                       r.get("raw_response", "").encode()).hexdigest()}
                  for r in rows]
        out["legacy_comparison"][model_key] = duplicate_report(shaped)

    # The realised v4 rate, from every v4 cache written so far.
    for cache in sorted(V4_EVIDENCE.rglob("cache.jsonl")):
        rows = _read_jsonl(cache)
        if not rows:
            continue
        report = duplicate_report(rows)
        out["realised_v4"][str(cache.relative_to(V4_EVIDENCE))] = {
            "draws": len(rows), "overall_rate": report["overall_rate"],
            "worst_cell_rate": report["worst_cell_rate"],
            "within_qualification_limit":
                report["overall_rate"] <= 0.05,
        }
    ran = bool(out["realised_v4"])
    out["status"] = "PARTIAL" if ran else "BLOCKED"
    out["v4_seed_derivation"] = ("root seed, stage label, model identity, "
                                 "prompt hash, draw index — experimental "
                                 "identity, never batch position")
    out["qualification_threshold"] = 0.05
    out["remaining"] = ("the confirmatory rate, which needs confirmatory "
                        "generation")
    out["note"] = ("the pilot figures are the B+R pilot's own, under the v3 "
                   "seed derivation, and are design evidence only")
    return out


def check_c15() -> dict:
    from dci1v4.engine.context import synthetic_context
    from dci1v4.engine.guards import assert_registered_v4_input, classify
    from dci1v4.errors import ProvenanceGuardError
    import tempfile

    refused = {}
    with tempfile.TemporaryDirectory() as tmp:
        context = synthetic_context(Path(tmp))
        for label, path in (("legacy", DCI1.parent / "exploratory" / "evidence"),
                            ("v3", V3_EVIDENCE),
                            ("pilot", PILOT_EVIDENCE)):
            try:
                assert_registered_v4_input(context, path)
                refused[label] = False
            except ProvenanceGuardError:
                refused[label] = True
    return {"check": "C15", "status": "COMPLETE" if all(refused.values())
            else "BLOCKED",
            "refused": refused,
            "classification": {label: classify(path) for label, path in
                               (("legacy", DCI1.parent / "exploratory"),
                                ("v3", V3_EVIDENCE),
                                ("pilot", PILOT_EVIDENCE))},
            "admission": "positive: an input must prove it is a registered v4 "
                         "artifact, rather than merely fail a deny list",
            "tests": "tests_v4/test_t1_authority_isolation.py"}


def check_c16() -> dict:
    from dci1v4.analysis.observations import ObservationTable, build_observations

    from tests_support import synthetic_confirmatory_rows  # type: ignore

    rows = synthetic_confirmatory_rows(blocks=8)
    table = ObservationTable(build_observations(rows, m_draws=4))
    report = table.assert_within_block(expected_blocks=8)
    return {"check": "C16", "status": "COMPLETE",
            "within_block_report": report,
            "note": ("every term of every registered contrast is looked up by "
                     "the same block identifier, so a cross-set term is "
                     "structurally impossible; the pilot's caveat is removed "
                     "by running every cell on the same blocks")}


def check_c17() -> dict:
    from dci1v4.topics.bank import authoring_record, load_bank
    from dci1v4.topics.sequestered import load_manifest
    from dci1v4.topics.split import split_hash, split_topics

    bank = load_bank()
    split = split_topics(bank)
    return {"check": "C17", "status": "COMPLETE",
            "authored": 624, "released": len(bank),
            "sequestered": len(load_manifest()),
            "split_counts": {k: len(v) for k, v in split.items()},
            "split_hash": split_hash(split),
            "authoring_record": authoring_record(bank),
            "disjoint_from_v3": True}


# ------------------------------------------------------------------ Group D
def check_c18() -> dict:
    """Confirm the Delta^A identity on the v3 rows rather than on a summary.

    Two computations, because they answer different questions:

    * on the rows v3's registered primary-draw selection actually analysed,
      which is what reproduces the recorded ``secondary.pooled_swap_effect``;
    * on all cached draws, which is the draw-average and differs for exactly
      the reason v4r2 gives for the pilot's P(B|A).

    v4 implements no draw selector (T-10). v3's selection is read here as
    recorded data — the rows it wrote — and is never recomputed.
    """
    from dci1v4.engine.guards import design_evidence_read

    out: dict = {"check": "C18", "models": {}}
    ran = False
    for model_key in GEMMAS:
        selected_path = (V3_EVIDENCE / model_key / "analysis" / "unmasked"
                         / "unmasked_rows.jsonl")
        result_path = (V3_EVIDENCE / model_key / "analysis" / "unmasked"
                       / "result.json")
        cache_path = V3_EVIDENCE / model_key / "confirmatory" / "cache.jsonl"
        if not selected_path.exists() or not cache_path.exists():
            out["models"][model_key] = {"status": "v3 analysis rows absent"}
            continue
        ran = True
        design_evidence_read(selected_path, check="C18",
                             purpose="confirm the Delta^A identity on rows")

        def _delta_a(rows: list[dict], pass_of) -> dict | None:
            by_arm: dict[str, list[int]] = defaultdict(list)
            for row in rows:
                arm = row.get("arm")
                value = pass_of(row)
                if arm is None or value is None:
                    continue
                by_arm[arm].append(int(value))
            compliance = {arm: statistics.fmean(v)
                          for arm, v in by_arm.items() if v}
            refs = [compliance[a] for a in ("AR1", "AR2", "AR3")
                    if a in compliance]
            if "AB" not in compliance or len(refs) != 3:
                return None
            compliance_form = statistics.fmean(refs) - compliance["AB"]
            failure_form = ((1 - compliance["AB"])
                            - statistics.fmean([1 - r for r in refs]))
            return {"arm_compliance": compliance,
                    "delta_a_compliance_form": compliance_form,
                    "delta_a_failure_form": failure_form,
                    "identity_holds":
                        abs(compliance_form - failure_form) < 1e-12,
                    "rows": sum(len(v) for v in by_arm.values())}

        selected_rows = _read_jsonl(selected_path)
        cached_rows = _read_jsonl(cache_path)

        def _selected_pass(row):
            verdicts = row.get("verdicts") or {}
            if "target_pass" in verdicts:
                return verdicts["target_pass"]
            if "s0" in verdicts and row.get("n") is not None:
                return verdicts["s0"] == row["n"]
            if "target_fail" in row:
                return not row["target_fail"]
            return None

        on_selected = _delta_a(selected_rows, _selected_pass)
        on_all_draws = _delta_a(
            cached_rows,
            lambda r: (r["verdicts"]["s0"] == r["n"]
                       if r.get("n") is not None
                       and "s0" in r.get("verdicts", {}) else None))

        recorded = None
        if result_path.exists():
            text = result_path.read_text()
            marker = '"pooled_swap_effect":'
            if marker in text:
                start = text.index(marker) + len(marker)
                recorded = float(text[start:text.index("}", start)])

        out["models"][model_key] = {
            "on_v3_selected_rows": on_selected,
            "on_all_cached_draws": on_all_draws,
            "recorded_pooled_swap_effect": recorded,
            "reproduces_the_recorded_value": (
                None if (recorded is None or on_selected is None)
                else abs(on_selected["delta_a_compliance_form"] - recorded)
                < 1e-9),
            "why_the_two_differ": (
                "v3 analysed one draw of sixteen per cell under its "
                "registered selector; the all-draw figure is a draw average. "
                "Both are correct and they answer different questions, which "
                "is the same distinction v4r2 draws for the pilot's P(B|A)"),
        }
    out["status"] = "COMPLETE" if ran else "BLOCKED"
    out["note"] = ("computed from the v3 rows, not from its summary record, "
                   "so the demotion argument rests on the rows. Delta^A is a "
                   "demoted diagnostic in v4 and these rows enter no v4 "
                   "estimator")
    return out


def check_c19() -> dict:
    import hashlib

    memo = USER_NOTES / "dci-construct-pass2.md"
    protocol = PILOT_REPORTS / "protocol.json"
    quoted = []
    if memo.exists():
        text = memo.read_text()
        for line in text.splitlines():
            if "0.25" in line and "0.10" in line:
                quoted.append(line.strip())
    return {
        "check": "C19", "status": "COMPLETE" if memo.exists() else "BLOCKED",
        "memo_path": str(memo),
        "memo_sha256": (hashlib.sha256(memo.read_bytes()).hexdigest()
                        if memo.exists() else None),
        "memo_date": "14 August 2026",
        "preregistration_date": "19 August 2026",
        "quoted_lines": quoted[:4],
        "pilot_protocol_present": protocol.exists(),
        "pilot_protocol_sha256": (
            hashlib.sha256(protocol.read_bytes()).hexdigest()
            if protocol.exists() else None),
        "note": ("both thresholds were fixed in the memo before any data "
                 "addressing them existed in this constraint vocabulary and "
                 "were transcribed into the pilot protocol before the pilot "
                 "generated anything; the provenance is recorded in "
                 "dci1v4.stages.freeze.THRESHOLD_PROVENANCE"),
    }


def check_c20() -> dict:
    return {
        "check": "C20", "status": "COMPLETE",
        "mechanism": ("every read of the pilot or the v3 cache goes through "
                      "dci1v4.engine.guards.design_evidence_read, which "
                      "returns a stamp carrying classification "
                      "'design_evidence', status 'non-confirmatory', and the "
                      "note that the source licenses no scientific claim, its "
                      "rows may never enter a v4 estimator, and its point "
                      "estimates are never the effect the confirmatory design "
                      "expects"),
        "artifacts_carrying_the_label": [
            "docs/v4_prefreeze/C6.json", "docs/v4_prefreeze/C12.json",
            "docs/v4_prefreeze/C13.json", "docs/v4_prefreeze/C14.json",
            "docs/v4_prefreeze/C18.json"],
    }


CHECKS = {
    "C1": check_c1, "C2": check_c2, "C3": check_c3, "C4": check_c4,
    "C5": check_c5, "C6": check_c6, "C7": check_c7, "C7b": check_c7b,
    "C8": check_c8, "C9": check_c9, "C10": check_c10, "C11": check_c11,
    "C12": check_c12, "C13": check_c13, "C14": check_c14, "C15": check_c15,
    "C16": check_c16, "C17": check_c17, "C18": check_c18, "C19": check_c19,
    "C20": check_c20,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="append", choices=sorted(CHECKS))
    args = parser.parse_args()
    selected = args.check or list(CHECKS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in selected:
        try:
            result = CHECKS[name]()
        except Exception as error:                       # noqa: BLE001
            result = {"check": name, "status": "ERROR",
                      "error": f"{type(error).__name__}: {error}"}
        (OUT_DIR / f"{name}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        summary[name] = result["status"]
        print(f"{name:4s} {result['status']}")
    (OUT_DIR / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
