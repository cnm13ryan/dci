"""C4 (the sealed final-check set), C5 (verifier-hash binding), and the
annotation sample sizing the author has to agree before any labelling session.

NOT a stage. Writes only to ``reports/gate1_v4/``. Seals nothing, approves
nothing, and starts no labelling session.

Usage:
  PYTHONPATH=src python tools/gate1_readiness_v4.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))
sys.path.insert(0, str(DCI1 / "tools"))

from dci1v4.analysis.intervals import wilson_upper_bound          # noqa: E402
from dci1v4.protocol import constants as C                        # noqa: E402
from dci1v4.protocol.hashing import sha_obj                       # noqa: E402
from dci1v4.protocol.seeds import GATE1_SAMPLE_SEED               # noqa: E402
from dci1v4.verifiers import verifier_source_hash                 # noqa: E402

import gate1_autorater_v4 as ar                                   # noqa: E402

OUT = DCI1 / "reports" / "gate1_v4"

#: The v3 reserved set, recorded in RESULTS_V3.md and in the v3 Gate 1
#: calibration sign-off notes. Verified by file digest only: no item id from it
#: is read, displayed or used anywhere in this tool.
V3_SEALED_PATH = (DCI1.parent / "autorater_forensics" / "experiments"
                  / "reserved_final_check_ids.json")
V3_SEALED_SHA = ("f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b"
                 "881d7a3")
FINAL_CHECK_ITEMS = 40


# ------------------------------------------------------------------- C4
def check_c4() -> dict[str, Any]:
    """The v3 seal, and a v4 candidate set that is prepared but NOT sealed."""
    present = V3_SEALED_PATH.exists()
    digest = (hashlib.sha256(V3_SEALED_PATH.read_bytes()).hexdigest()
              if present else None)

    items = ar.build_items()
    reserved = ar.subsample(sorted(items, key=lambda i: i["item_id"]),
                            FINAL_CHECK_ITEMS)
    reserved_ids = sorted(i["item_id"] for i in reserved)
    remainder = [i for i in items if i["item_id"] not in set(reserved_ids)]
    return {
        "check": "C4",
        "v3_sealed_set": {
            "path": str(V3_SEALED_PATH),
            "present": present,
            "expected_sha256": V3_SEALED_SHA,
            "measured_sha256": digest,
            "untouched": digest == V3_SEALED_SHA,
            "verification_method": ("file digest only; no item id was read, "
                                    "displayed or used"),
            "disposition": ("stays sealed. Nothing in dci1v4 can open it, and "
                            "it is not reused for v4."),
        },
        "why_a_new_set": (
            "the v4 instrument population differs from v3's -- v3's set was "
            "composed for the exact-count rule alone and cannot exercise the "
            "word-length rule or any family verifier -- so per C4 a new sealed "
            "set is required rather than reuse"),
        "v4_candidate_set": {
            "state": "PREPARED, NOT SEALED",
            "items": len(reserved_ids),
            "content_hash": sha_obj(reserved_ids),
            "derivation": ("deterministic round-robin over the six "
                           "instrument x class x fail-margin strata in item-id "
                           "order over the registered §12.2 ladder screen pool"),
            "reserved_before_the_split": True,
            "remaining_pool_after_reservation": len(remainder),
            "covers_instruments": sorted({i["instrument"] for i in reserved}),
            "strata": {s: sum(1 for i in reserved if ar.stratum(i) == s)
                       for s in sorted({ar.stratum(i) for i in reserved})},
            "not_sealed_because": (
                "sealing is a Gate 1 act and Gate 1 is not approved. The set is "
                "also provisional: it covers A and B only, and must be "
                "re-derived once the reference pool is final and the family "
                "verifiers exist, because a final-check set that cannot "
                "exercise an admitted instrument is not a final check of it."),
            "rules_when_it_is_sealed": [
                "sealed at Gate 1 and its hash recorded",
                "opened at most once, after every autorater choice is frozen",
                "never used for tuning",
                "never rerun after a failure to obtain a better result",
            ],
        },
    }


# ------------------------------------------------------------------- C5
_C5_CASES = {
    "test_case_one_an_unchanged_verifier_succeeds_at_every_entry_point":
        "an unchanged verifier succeeds",
    "test_case_two_a_semantic_change_fails_every_protected_stage_closed":
        "a committed semantic change fails every protected stage closed",
    "test_case_three_reverting_succeeds_again": "reverting succeeds",
    "test_case_four_an_irrelevant_source_change_produces_no_false_mismatch":
        "an irrelevant source change produces no false mismatch",
    "test_case_five_stored_verdict_provenance_stays_traceable":
        "stored verdict provenance traces to the verifier that produced it",
}


def check_c5() -> dict[str, Any]:
    """Run the verifier-binding regression suite and report every case."""
    completed = subprocess.run(
        [str(DCI1 / ".venv" / "bin" / "python"), "-m", "pytest",
         "tests_v4/test_t8_verifier_binding.py", "-v", "--no-header"],
        cwd=str(DCI1), capture_output=True, text=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": "src"})
    lines = completed.stdout.splitlines()
    outcomes = {}
    for line in lines:
        for name in list(_C5_CASES) + [
                "test_the_protected_set_is_the_union_of_eleven_entry_points",
                "test_an_unregistered_entry_point_is_refused",
                "test_before_gate1_the_binding_records_rather_than_compares",
                "test_the_semantic_module_set_covers_graded_scores_and_predicates",
                "test_the_frozen_hash_is_never_silently_updated"]:
            if name in line:
                outcomes[name] = ("PASSED" if "PASSED" in line
                                  else "FAILED" if "FAILED" in line else "?")
    return {
        "check": "C5",
        "regression_test_file": "tests_v4/test_t8_verifier_binding.py",
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "entry_points": list(C.VERIFIER_BOUND_ENTRY_POINTS),
        "entry_point_count": len(C.VERIFIER_BOUND_ENTRY_POINTS),
        "five_required_cases": {v: outcomes.get(k, "not reported")
                                for k, v in _C5_CASES.items()},
        "additional_cases": {k: v for k, v in outcomes.items()
                             if k not in _C5_CASES},
        "canonical_verifier_hash": verifier_source_hash(),
        "summary_line": lines[-1] if lines else "",
    }


# ------------------------------------------------- the annotation sizing
#: Measured from this annotator's own v3 sessions: 56 items in 52.4 minutes and
#: 64 items in 69.2 minutes, median inter-item gaps 49.2 s and 27.7 s.
SECONDS_PER_ITEM_LOW = 30
SECONDS_PER_ITEM_HIGH = 60


def _min_n_for_bound(maximum: float) -> int:
    """The smallest n whose one-sided 95% Wilson upper bound at ZERO
    disagreements is at most ``maximum``. Below this the criterion is
    unreachable however well the annotator performs."""
    n = 1
    while wilson_upper_bound(0, n) > maximum and n < 10_000:
        n += 1
    return n


def sizing() -> dict[str, Any]:
    items = ar.build_items()
    strata: dict[str, int] = {}
    classes: dict[str, int] = {}
    for item in items:
        strata[ar.stratum(item)] = strata.get(ar.stratum(item), 0) + 1
        key = f"{item['instrument']}:{item['verifier_class']}"
        classes[key] = classes.get(key, 0) + 1

    floor = _min_n_for_bound(C.HUMAN_DISAGREEMENT_MAX)
    per_class = {k: min(C.HUMAN_SAMPLE_CAP, v)
                 for k, v in sorted(classes.items())}
    s103 = sum(per_class.values())

    stratum_plan = {}
    for name, n in sorted(strata.items()):
        target = min(C.HUMAN_SAMPLE_CAP, n)
        stratum_plan[name] = {
            "population": n, "registered_sample": target,
            "minimum_n_for_the_criterion_to_be_reachable": floor,
            "reachable": n >= floor,
            "note": (None if n >= floor else
                     f"the natural population is smaller than {floor}, so the "
                     f"§10.3 bound cannot be met even with zero disagreements; "
                     f"the registered outcome is "
                     f"MEASUREMENT_EVIDENCE_INSUFFICIENT for this stratum"),
        }
    s103_stratified = sum(v["registered_sample"] for v in stratum_plan.values())

    def hours(n):
        return {"low": round(n * SECONDS_PER_ITEM_LOW / 3600, 1),
                "high": round(n * SECONDS_PER_ITEM_HIGH / 3600, 1)}

    return {
        "sampling_seed": GATE1_SAMPLE_SEED,
        "pool": {"items": len(items), "by_stratum": strata,
                 "by_instrument_and_class": classes},
        "rate": {
            "seconds_per_item": [SECONDS_PER_ITEM_LOW, SECONDS_PER_ITEM_HIGH],
            "measured_from": ("this annotator's own v3 sessions: 56 items in "
                              "52.4 min and 64 items in 69.2 min; median "
                              "inter-item gaps 49.2 s and 27.7 s"),
        },
        "option_1_section_10_3": {
            "rule": f"min({C.HUMAN_SAMPLE_CAP}, N_c) per class per "
                    f"instrument, with the fail class additionally split by "
                    f"realised margin",
            "per_class": per_class,
            "per_stratum": stratum_plan,
            "items_by_class": s103,
            "items_by_stratum": s103_stratified,
            "estimated_hours": hours(s103_stratified),
            "what_it_buys": ("nothing that Gate 1 can use. §10.3 requires an "
                             "annotator INDEPENDENT of the design and analysis "
                             "team; the annotator here is the study author, so "
                             "the basis is HUMAN_VALIDATION_UNAVAILABLE however "
                             "many items are labelled. This is the size needed "
                             "for a human_validated basis that is unreachable."),
        },
        "option_2_section_10_4": {
            "rule": ("enough paired items to separate the judging conditions "
                     "under the §10.4 hierarchy's fourth criterion"),
            "driver": ("the discordant set between the two conditions, plus a "
                       "matched concordant control sample of the same size"),
            "items": "computed from the paired comparison; see section_10_4",
            "what_it_buys": ("the fourth criterion of the §10.4 selection "
                             "hierarchy, which is the only criterion the judge "
                             "run cannot decide on its own"),
        },
        "invariant": (
            "author-performed labels are diagnostic evidence and §10.4 "
            "hierarchy input. They are NEVER described as independent "
            "validation, in any artifact, at any point. The v3 record already "
            "carries the same disposition for its 120 author labels."),
        "protocol_properties_required_of_any_session": [
            "blind: no arm, model label, companion, verifier verdict or other "
            "annotator's work visible",
            "tool-assisted: the annotator marks each qualifying feature and the "
            "interface tallies the annotator's OWN marks; no automatic "
            "detection, highlighting, counting or normalisation",
            "chained, hash-pinned records",
            "seeded stratified sample, per instrument",
            "fail-class stratification by realised margin: exactly one against "
            "larger, reported separately",
        ],
        "why_tool_assisted_and_not_automatic": (
            "all four v3 human-to-verifier disagreements were unaided "
            "off-by-one counting errors at margin one, and four independent "
            "recounts reproduced the verifier every time. Automatic counting "
            "would remove the disagreement by removing the measurement."),
        "not_started": ("no labelling session has been started. §2.5 requires "
                        "the author to size and agree one first."),
    }


def main() -> int:
    payload = {
        "artifact": "Gate 1 readiness: C4, C5 and the annotation sizing",
        "classification": ("Gate 1 input evidence. Gate 1 is NOT approved, "
                           "nothing is sealed, and no labelling session was "
                           "started."),
        "c4_sealed_final_check_set": check_c4(),
        "c5_verifier_hash_binding": check_c5(),
        "annotation_sizing": sizing(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "readiness_c4_c5_sizing.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    c4, c5, sz = (payload["c4_sealed_final_check_set"],
                  payload["c5_verifier_hash_binding"],
                  payload["annotation_sizing"])
    print(json.dumps({
        "v3_seal_untouched": c4["v3_sealed_set"]["untouched"],
        "v4_candidate_hash": c4["v4_candidate_set"]["content_hash"][:16],
        "v4_candidate_state": c4["v4_candidate_set"]["state"],
        "c5_passed": c5["passed"], "c5_entry_points": c5["entry_point_count"],
        "c5_five_cases": c5["five_required_cases"],
        "section_10_3_items": sz["option_1_section_10_3"]["items_by_stratum"],
        "section_10_3_hours": sz["option_1_section_10_3"]["estimated_hours"],
        "unreachable_strata": [k for k, v in
                               sz["option_1_section_10_3"]["per_stratum"].items()
                               if not v["reachable"]],
    }, indent=1))
    print(f"written: {path.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
