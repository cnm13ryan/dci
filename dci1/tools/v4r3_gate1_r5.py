"""Run the amended Gate 1 (§10.7-R5) and write its artifacts.

Four reports and one decision:

    reports/dci1v4r3/specification_audit.json     A  and A.2's severity sweep
    reports/dci1v4r3/wording_review.json          A'
    reports/dci1v4r3/mutation_validation.json     D
    reports/dci1v4r3/gate1_r5_decision.json       the ten conditions applied

B, C and E's evidence is **reused, not recomputed**: `gate1_evidence.json`
already carries §10.2 over the final population at the canonical verifier
hash, and the amendment permits reuse exactly when the population is unchanged,
the hash matches, and the artifact tests the amended criterion. All three are
checked here and refused on mismatch rather than assumed.

Nothing in this tool decides anything. `stages.gate1_r5.gate1_r5_payload`
applies the rule; a failure raises `TerminalStatus` and the tool writes what it
raised. The supplementary human and autorater evidence is loaded and attached
because it is real, and it is attached under a key the rule never reads.

    python3 tools/v4r3_gate1_r5.py
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.errors import TerminalStatus                      # noqa: E402
from dci1v4.protocol.hashing import canonical_json, sha_text  # noqa: E402
from dci1v4r3 import CLASSIFICATION                           # noqa: E402
from dci1v4r3.engine.paths import ModelTree                   # noqa: E402
from dci1v4r3.engine.transitions import read_stage_record     # noqa: E402
from dci1v4r3.protocol import constants as C                  # noqa: E402
from dci1v4r3.stages.gate1_r5 import (                        # noqa: E402
    amendment_hash, collect_r5_evidence, gate1_r5_payload,
)
from dci1v4r3.stages.mutation import run_mutation_validation  # noqa: E402
from dci1v4r3.stages.specification import (                   # noqa: E402
    run_specification_audit, wording_review, wordings_hash,
)
from dci1v4r3.verifiers import verifier_source_hash           # noqa: E402
from dci1v4r3.verifiers.boundary import instrument_population  # noqa: E402

REPORTS = DCI1 / "reports" / "dci1v4r3"
EVIDENCE = REPORTS / "gate1_evidence.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=DCI1,
                          capture_output=True, text=True,
                          check=False).stdout.strip()


def _write(name: str, payload: dict[str, Any]) -> Path:
    path = REPORTS / name
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return path


def reusable(evidence: dict[str, Any]) -> dict[str, Any]:
    """The amendment's three conditions for reusing §10.2's evidence."""
    population = [f"{k}:{s}" for k, s in instrument_population()]
    return {
        "population_unchanged": evidence["instrument_population"] == population,
        "verifier_hash_matches": (evidence["verifier_hash"]
                                  == verifier_source_hash()),
        "tests_the_amended_criterion": all(
            key in evidence for key in
            ("determinism", "suites", "reimplementation", "adversarial",
             "witnesses", "wordings", "carryover")),
        "population": len(population),
        "verifier_hash": evidence["verifier_hash"],
    }


def provenance() -> dict[str, Any]:
    """Condition 10, measured rather than asserted."""
    from dci1v4r3.engine.context import registered_context  # noqa: PLC0415
    context = registered_context()
    verified: dict[str, str] = {}
    problems: list[str] = []
    for model in MODELS:
        tree = ModelTree(context=context, model_key=model)
        try:
            record = read_stage_record(tree, C.STAGE_REGIME)
            verified[model] = record.get("outcome", "?")
        except Exception as error:                       # noqa: BLE001
            problems.append(f"{model}: {error}")
    evidence = json.loads(EVIDENCE.read_text())
    carry = evidence["carryover"]
    return {
        "predecessor_stage": C.STAGE_REGIME,
        "predecessor_records_verified": verified,
        "predecessor_verified": (len(verified) == len(MODELS)
                                 and set(verified.values()) == {"PASS"}),
        "predecessor_problems": problems,
        # §10.2's composition equivalence is an assertion that raises: its
        # presence with a non-zero `checked` is the evidence that it held.
        "carry_over_passed": bool(
            carry["a_carry_over_survives"]
            and carry["composition_equivalence"]["checked"] > 0),
        "composition_equivalence_checked":
            carry["composition_equivalence"]["checked"],
        "reserved_sets_unspent": bool(
            evidence["topic_audit"]["reserved_sets_unspent"]),
        "producing_commit": _commit(),
        "no_gate1_record_exists_yet": not any(
            ModelTree(context=context, model_key=m)
            .stage_record(C.STAGE_GATE1).exists() for m in MODELS),
    }


def supplementary() -> dict[str, Any]:
    """§10.3 and §10.4, preserved and labelled. Never read by the rule."""
    def _load(name: str) -> dict[str, Any] | None:
        path = REPORTS / name
        return json.loads(path.read_text()) if path.exists() else None

    r2 = _load("section_10_4R2_outcome.json")
    r1 = _load("section_10_4R_outcome.json")
    decision = _load("gate1_decision.json")
    diagnosis = _load("validator_diagnosis.json")
    sensitivity = _load("defect_sensitivity.json")
    return {
        "role": "supplementary semantic diagnostics (§10.7-R5). They may "
                "reveal confusing wording, undocumented assumptions or "
                "specification ambiguity, and they neither pass nor fail this "
                "gate",
        "section_10_3": {
            "status": "HUMAN_VALIDATION_UNAVAILABLE",
            "reason": "no annotator independent of the design and analysis "
                      "team has completed it. The frozen sampling plan stays "
                      "unspent and a completed §10.3 would supersede this "
                      "basis rather than be blocked by it",
            "author_performed_labels": (decision or {}).get(
                "human_annotations"),
            "author_performed_labels_are_not_independent_validation": True,
        },
        "section_10_4R": {
            "outcome": (r1 or {}).get("outcome"),
            "full_artifact": "reports/dci1v4r3/section_10_4R_outcome.json",
        },
        "section_10_4R2": {
            "outcome": (r2 or {}).get("outcome", "FAIL"),
            "criteria": (r2 or {}).get("criteria"),
            "full_artifact": "reports/dci1v4r3/section_10_4R2_outcome.json",
            "stopping_rule": "§10.4-R2: on failure the LLM-validator pathway "
                             "stops, is not prompt-tuned, and no threshold "
                             "moves. That stop stands",
        },
        "validator_diagnosis": {
            "finding": (diagnosis or {}).get("finding"),
            "contrast": (diagnosis or {}).get("contrast"),
            "full_artifact": "reports/dci1v4r3/validator_diagnosis.json",
        },
        "natural_response_defect_sensitivity": {
            "verdict_bands": (sensitivity or {}).get("verdict_bands"),
            "overall": ((sensitivity or {}).get("stated") or {}).get("overall"),
            "full_artifact": "reports/dci1v4r3/defect_sensitivity.json",
            "read_as": "practical consequence on real answers only. Where a "
                       "defect moves no natural label the reading is that the "
                       "natural corpus cannot validate that convention, never "
                       "that the convention was validated",
        },
        "superseded_decision_under_the_former_rule": {
            "decision": (decision or {}).get("decision"),
            "rule": (decision or {}).get("registered_rule"),
            "preserved_at": "reports/dci1v4r3/gate1_decision.json",
            "note": "decided under §18 stage 4 before amendment R5. It is not "
                    "rewritten and this record does not describe it as having "
                    "passed",
        },
    }


def _compact(payload: dict[str, Any]) -> dict[str, Any]:
    """The decision record, with the three audits referenced not duplicated.

    The rule reads the audits in full -- `gate1_r5_payload` is handed the whole
    objects -- and the hashes bound into this record are computed over those
    whole objects. What is trimmed here is only the *copy*: the per-case tables
    and the 2,336 wording rows live in their own artifacts beside this one,
    which is where a reader should read them anyway. Nothing that the rule
    tested is removed from the record without a hash that still covers it.
    """
    out = dict(payload)
    audit = out.get("specification_audit")
    if audit:
        families = {kind: {k: v for k, v in family.items()
                           if k not in ("cases", "specification")}
                    for kind, family in audit["families"].items()}
        out["specification_audit"] = {
            **{k: v for k, v in audit.items() if k != "families"},
            "families": families,
            "full_artifact": "reports/dci1v4r3/specification_audit.json",
            "cases_and_specifications_are_in_the_full_artifact": True}
    mutation = out.get("mutation_validation")
    if mutation:
        families = {kind: {**{k: v for k, v in family.items()
                              if k != "defects"},
                           "defects": {d: {k: v for k, v in row.items()
                                           if k != "examples"}
                                       for d, row in family["defects"].items()}}
                    for kind, family in mutation["families"].items()}
        out["mutation_validation"] = {
            **{k: v for k, v in mutation.items() if k != "families"},
            "families": families,
            "full_artifact": "reports/dci1v4r3/mutation_validation.json"}
    review = out.get("wording_review")
    if review:
        blocking = review["genuinely_ambiguous"] + review["requires_correction"]
        out["wording_review"] = {
            **{k: v for k, v in review.items() if k != "findings"},
            "distinct_blocking_wordings": sorted({
                (row["kind"], row["wording"].replace(str(row["severity"]),
                                                     "{q}"))
                for row in blocking}),
            "blocking_severities": {
                kind: sorted({row["severity"] for row in blocking
                              if row["kind"] == kind})
                for kind in sorted({row["kind"] for row in blocking})},
            "full_artifact": "reports/dci1v4r3/wording_review.json"}
    return out


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text())
    reuse = reusable(evidence)
    if not all(reuse[key] for key in ("population_unchanged",
                                      "verifier_hash_matches",
                                      "tests_the_amended_criterion")):
        print(json.dumps({"refused": "§10.2 evidence is not reusable",
                          "reuse": reuse}, indent=1))
        return 2

    specification = run_specification_audit()
    mutation = run_mutation_validation()
    wordings = wording_review()
    _write("specification_audit.json",
           {"artifact_type": "v4r3-specification-audit",
            "classification": CLASSIFICATION, "component": "§10.7-R5 A",
            "producing_commit": _commit(), **specification})
    _write("wording_review.json",
           {"artifact_type": "v4r3-wording-review",
            "classification": CLASSIFICATION, "component": "§10.7-R5 A'",
            "wordings_hash": wordings_hash(),
            "producing_commit": _commit(), **wordings})
    _write("mutation_validation.json",
           {"artifact_type": "v4r3-mutation-validation",
            "classification": CLASSIFICATION, "component": "§10.7-R5 D",
            "producing_commit": _commit(), **mutation})

    r5_evidence = collect_r5_evidence(specification=specification,
                                      mutation=mutation, wordings=wordings)
    prov = provenance()
    diagnostics = supplementary()

    header = {
        "artifact_type": "v4r3-gate1-r5-decision",
        "classification": CLASSIFICATION,
        "gate": C.STAGE_GATE1,
        "rule": "§10.7-R5: §10.2 for every verifier in the final instrument "
                "population, plus A-E. No human or autorater agreement "
                "threshold appears in it",
        "superseded_rule": "§18 stage 4 before R5: §10.2 plus §10.3 or §10.4",
        "amendment_hash": amendment_hash(),
        "canonical_verifier_hash": verifier_source_hash(),
        "wordings_hash": wordings_hash(),
        "instrument_population": len(instrument_population()),
        "evidence_reuse": reuse,
        "producing_commit": _commit(),
        "generated_at": _dt.datetime.now(_dt.timezone.utc)
                           .isoformat(timespec="seconds"),
    }
    try:
        record = gate1_r5_payload(evidence=evidence, r5_evidence=r5_evidence,
                                  provenance=prov,
                                  supplementary_diagnostics=diagnostics)
        payload = {**header, "decision": "PASS", **record}
    except TerminalStatus as terminal:
        payload = {**header, "decision": terminal.status,
                   **dict(terminal.record)}
        payload["supplementary_diagnostics"] = diagnostics

    # Hash what is *written*, so the file verifies itself. The three component
    # hashes above cover the full audits, which the rule read in full and which
    # sit beside this file; between them nothing the gate tested is unhashed.
    payload = _compact(payload)
    payload["decision_hash_covers"] = ("this file as written. The full audits "
                                       "are covered by specification_hash, "
                                       "mutation_hash and wordings_hash")
    payload["decision_hash"] = sha_text(canonical_json(
        {k: v for k, v in payload.items() if k != "generated_at"}))
    path = _write("gate1_r5_decision.json", payload)

    summary = {
        "decision": payload["decision"],
        "specification_audit": {
            "families": len(specification["families"]),
            "forms": specification["forms"],
            "ambiguous": specification["ambiguous_kinds"],
            "passed": specification["passed"]},
        "wording_review": {"checked": wordings["wordings_checked"],
                           **wordings["counts"],
                           "passed": wordings["passed"]},
        "mutation_validation": {
            "passed": mutation["passed"],
            "by_defect": {d: {"meaningful": v["families_where_meaningful"],
                              "detected": v["families_detected"],
                              "not_applicable": v["families_not_applicable"]}
                          for d, v in mutation["by_defect"].items()}},
        "failed_conditions": payload.get("failed_conditions"),
        "observed": payload.get("observed"),
        "report": str(path.relative_to(DCI1)),
    }
    print(json.dumps(summary, indent=1)[:4000])
    return 0 if payload["decision"] == "PASS" else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
