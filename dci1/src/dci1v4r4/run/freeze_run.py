"""Gate 5's runner: assemble §18.1's freeze record from what is already signed.

Nothing here decides anything. Every field is copied from a record that some
earlier stage wrote and signed, or from the registration manifest, and a field
with no such source is left ``UNKNOWN`` so that `check_completeness` names it.
That is the whole design: a freeze that could fill its own gaps would be a
freeze that binds a default rather than a decision.

The one field this module cannot source is `gate1_measurement_basis`. §10.3 and
§10.4 end in a person's signature, and until one exists the basis reads
`HUMAN_VALIDATION_UNAVAILABLE`, which is not a value §18.1 accepts. So the
freeze refuses, and it refuses by naming that field rather than by a general
complaint.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r4.protocol import constants as C
from dci1v4r4.stages import freeze as F
from dci1v4r4.verifiers import source_hashes, verifier_source_hash
from dci1v4r4.verifiers.constraints import (
    FAMILIES, LADDERS, RESERVES, declared_range,
)

DCI1 = Path(__file__).resolve().parents[3]
REPO = DCI1.parent

__all__ = ["AMENDMENT_DOCUMENTS", "amendment_hashes", "decision_record",
           "assemble", "run_freeze"]

#: §31: the documents an amendment lives in. Hashed into the freeze so that a
#: post-freeze edit to any of them is visible as a hash that no longer matches.
AMENDMENT_DOCUMENTS = (
    "user-notes/DCI1_preregistration_v4r3.md",
    "user-notes/DCI1_v4r2_to_v4r3_changelog.md",
    "dci1/DECISIONS_V4R3.md",
)


def amendment_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for relative in AMENDMENT_DOCUMENTS:
        path = REPO / relative
        out[relative] = (hashlib.sha256(path.read_bytes()).hexdigest()
                         if path.exists() else "MISSING")
    return out


#: §33's decisions and the standing each is closed at. The standing is quoted
#: from §33's own table; closing a decision here records that the registered
#: standing is what the study runs under, which is what §33 asks for. No entry
#: introduces a value §33 does not already name.
DECISION_STANDINGS: dict[str, str] = {
    "D0": "adopted; DECISIONS_V4R3.md A0",
    "D1": "384 blocks at M = 8, four models, 96 sequestered topics; A1",
    "D2": "no load-three arm; the §5 exclusion stands",
    "D3": "§12.4's share reading of the graded-degeneracy clause",
    "D4": "two extra rungs per family; §11.7's registered form",
    "D5": "direction and the registered smallest effect of interest only; no "
          "pair-specific magnitude threshold for delta_difficulty",
    "D6": "instructed compliance primary, raw solo secondary, "
          "DIFFICULTY_COORDINATE_DEPENDENT on disagreement",
    "D7": "the reference caliper at 0.10 on iota, with EXCESS_NOT_IDENTIFIED "
          "rather than widening",
    "D8": "the non-vacuity threshold at 20 words, stated to the model by the "
          "§8.5 stem",
    "D9": "UNKNOWN",
    "D10": "one class companion; COMPANION_CLASS_NOT_MATCHED stands and no "
           "class claim is made",
    "D11": "no second focal-like outcome constraint",
    "D12": "the class arm is CL7, CL8, CX1 and CX2; §7.0-R4 removed CP4 "
           "and CP7 on a specification-ambiguity finding, so the class pool "
           "carries no rate lower bound and CX1 is A's own predicate form; "
           "A2, and A-R4-2",
    "D13": "§12.6's seven coverage values, registered before any "
           "measurement; A4",
    "D14": "the feature groups of §7.0 as registered, extended by §7.0-R3 to "
           "thirteen; the witness suite is the check",
}


def decision_record(gate1_record: Mapping[str, Any] | None) -> dict[str, str]:
    """§33's table, with D9 filled from Gate 1's actual measurement basis.

    D9 asks whether an independent annotator is available, and that is not a
    thing this module may assert. It reads the basis Gate 1 recorded, and
    leaves the decision `UNKNOWN` --- which `check_completeness` reports as
    unclosed --- while the basis is `HUMAN_VALIDATION_UNAVAILABLE`.
    """
    out = dict(DECISION_STANDINGS)
    basis = (gate1_record or {}).get("measurement_basis")
    if basis and basis != "HUMAN_VALIDATION_UNAVAILABLE":
        out["D9"] = f"measurement basis {basis}, recorded at Gate 1"
    return out


def _vocabulary() -> dict[str, Any]:
    return {kind: {"statistic": f.statistic_id, "form": f.form,
                   "role": f.role, "class": f.constraint_class,
                   "feature_group": f.feature_group,
                   "ladder": list(LADDERS[kind]),
                   "reserve": list(RESERVES[kind])}
            for kind, f in FAMILIES.items()}


def assemble(*, model_key: str, manifest: Mapping[str, Any],
             regime: Mapping[str, Any], gate2: Mapping[str, Any],
             gate3: Mapping[str, Any], gate4: Mapping[str, Any],
             gate1: Mapping[str, Any] | None,
             durability: Mapping[str, Any] | None,
             producing_commit: str, environment_digest: str,
             dependency_digest: str, hardware_record: Mapping[str, Any],
             gate_record_hashes: Mapping[str, str]) -> dict[str, Any]:
    """One model's freeze record. Every value comes from a signed source."""
    from dci1v4r4.run.gates_run import full_slot_map

    spec = next(m for m in manifest["models"] if m["model_key"] == model_key)
    slot_map = full_slot_map(gate2, gate3)
    fields: dict[str, Any] = {
        "protocol_version": manifest["protocol_version"],
        "model_repository": spec["model_id"],
        "model_revision": spec["revision"],
        "prompt_template": manifest["design"]["prompt_template"],
        "completion_cap": regime["selected_cap"],
        "n_star": gate2["n_star"],
        "m_star": gate2["m_star"],
        "wordings": manifest["constraints"]["wording_word_counts"],
        "topic_splits": manifest["topics"],
        "chat_template_hash": spec.get("chat_template_hash", "UNKNOWN"),
        "verifier_sources": source_hashes(),
        "canonical_verifier_hash": verifier_source_hash(),
        "graded_score_definitions":
            manifest["instruments"]["graded_score_definitions"],
        "non_vacuity_predicates":
            manifest["instruments"]["non_vacuity_predicates"],
        "decoding_settings": manifest["decoding_policy_form"],
        "m_draws": C.M_DRAWS,
        "block_count": C.N_BLOCKS,
        "variance_reestimate": manifest["variance_model"],
        "seed_rules": manifest["seeds"],
        "cell_plan": {"design_variant": gate3["design_variant"],
                      "cells_per_block": gate3["cells_per_block"],
                      "slot_map": {k: list(v) for k, v in slot_map.items()}},
        "family_declarations": manifest["estimands_and_families"],
        "thresholds_and_regions": manifest["thresholds_and_regions"],
        "precision_preconditions": manifest["precision_preconditions"],
        "claim_ladder": manifest["claim_ladder"],
        "codebook": manifest["artifact_semantics"],
        "producing_commit": producing_commit,
        "clean_tree_assertion": True,
        "dependency_digest": dependency_digest,
        "environment_digest": environment_digest,
        "hardware_record": dict(hardware_record),
        "gate_record_hashes": dict(gate_record_hashes),
        "gate1_measurement_basis": (gate1 or {}).get(
            "measurement_basis", "UNKNOWN"),
        "analysis_plan": manifest["estimands_and_families"],
        # ---- new in v4r3
        "stem_sentence": C.STEM_SENTENCE,
        # §12.3 decides the escalation, so Gate 2's record is where it is
        # decided and this reads it there. It used to read the regime record,
        # which no code path writes, so the freeze would have recorded `false`
        # for a replication that had escalated --- a frozen value contradicting
        # the record it is supposed to freeze.
        "focal_extension_measured": bool(
            gate2.get("focal", {}).get("extension_measured", False)),
        "candidate_family_vocabulary": _vocabulary(),
        "candidate_declared_range": {kind: list(declared_range(kind))
                                     for kind in FAMILIES},
        "measured_vocabulary": regime["vocabulary_freeze"],
        "expansion_rule": manifest["selection_rules"]["expansion_rule"],
        "coverage_criterion": manifest["selection_rules"]["coverage_criterion"],
        "coverage_report": regime["expansion"]["coverage"],
        "lexical_rule": manifest["instruments"]["lexical_rule"],
        "family_class_labels": {k: f.constraint_class
                                for k, f in FAMILIES.items()},
        "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
        "chance_compliance_definition":
            manifest["selection_rules"]["difficulty_coordinate"],
        "eligibility_band": list(C.SPECTRUM_ELIGIBILITY_BAND),
        "core_reference_selection_rule":
            manifest["selection_rules"]["reference_admission_rule"],
        "core_references": gate3["core_references"],
        "spectrum_selection_rule":
            manifest["selection_rules"]["spectrum_selection_rule"],
        "spectrum_offset": C.SPECTRUM_OFFSET,
        "spectrum_severities": gate3["spectrum"],
        "class_admission_rule":
            manifest["selection_rules"]["class_admission_rule"],
        "class_companion": gate3.get("class_companion")
                           or "CLASS_ARM_NOT_AVAILABLE",
        "class_match_caliper": C.CLASS_MATCH_CALIPER,
        "design_variant": gate3["design_variant"],
        "support_rule": manifest["selection_rules"]["support_rule"],
        "calibration_table_hash": sha_text(
            canonical_json(gate2.get("calibration_table", []))),
        "difficulty_model_form":
            manifest["estimands_and_families"]["difficulty_model_form"],
        "bootstrap_refit_algorithm": manifest["bootstrap"],
        "joint_reading_table": manifest["claim_ladder"]["measurement_bases"],
        "graded_clause_reading": C.GRADED_CLAUSE_READING,
        "order_and_wording_allocation":
            {"wording_allocation": manifest["design"]["wording_allocation"],
             "order_is": manifest["design"]["order_is"]},
        "amendment_hashes": amendment_hashes(),
        "masking_rule": manifest["masking"],
        "durability_record": dict(durability or {}) or "UNKNOWN",
        # §13.10's outcome belongs to the freeze as the licence it is
        "blocks": [],
        "slot_map": {},
    }
    # `blocks` and `slot_map` are not §18.1 fields; the confirmatory plan reads
    # them from the record beside the frozen fields.
    record = F.build_freeze_record(
        **{k: v for k, v in fields.items()
           if k not in ("blocks", "slot_map")})
    record["slot_map"] = {k: list(v) for k, v in slot_map.items()}
    record["blocks"] = [t["topic_id"] for t in _blocks()]
    record["gate4_band"] = gate4["band"]
    record["model_key"] = model_key
    return record


def _blocks() -> list[dict[str, Any]]:
    from dci1v4r4.topics import split_topics
    return list(split_topics()["confirmatory"])


def run_freeze(model_key: str, *, manifest: Mapping[str, Any],
               records: Mapping[str, Mapping[str, Any]],
               gate1: Mapping[str, Any] | None,
               durability: Mapping[str, Any] | None,
               producing_commit: str, environment_digest: str = "-",
               dependency_digest: str = "-",
               hardware_record: Mapping[str, Any] | None = None
               ) -> dict[str, Any]:
    """Assemble, then put it to §18.1. Returns the record or the refusal."""
    gate_hashes = {stage: sha_text(canonical_json(payload))
                   for stage, payload in sorted(records.items())}
    record = assemble(
        model_key=model_key, manifest=manifest,
        regime=records[C.STAGE_REGIME], gate2=records[C.STAGE_GATE2],
        gate3=records[C.STAGE_GATE3], gate4=records[C.STAGE_GATE4],
        gate1=gate1, durability=durability,
        producing_commit=producing_commit,
        environment_digest=environment_digest,
        dependency_digest=dependency_digest,
        hardware_record=hardware_record or {},
        gate_record_hashes=gate_hashes)
    decisions = decision_record(gate1)
    status = F.check_completeness(record, decisions=decisions)
    if not status["can_freeze"]:
        return {"outcome": "REFUSED", "stage": C.STAGE_GATE5,
                "model_key": model_key, **status,
                "unclosed_decision_standings":
                    {d: decisions.get(d) for d in status["unclosed_decisions"]},
                "why": ("§18.1 binds every scientific degree of freedom and "
                        "refuses while any is missing. A freeze that filled "
                        "its own gaps would bind a default rather than a "
                        "decision.")}
    return F.freeze(record, decisions=decisions)
