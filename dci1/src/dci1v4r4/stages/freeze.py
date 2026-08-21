"""Gate 5: the freeze record and its completeness rule (v4r3 §18.1).

The freeze has to bind **every** scientific degree of freedom, and v4r3 has
more of them than v4r2 did: a difficulty coordinate, a chance-compliance
definition, an eligibility band, a spectrum-selection rule with a registered
offset, six spectrum severities, a class companion, a support rule, a fitted
functional form, a bootstrap that refits, and a joint-reading table.

``FREEZE_FIELDS`` is the list, and ``check_completeness`` refuses to freeze
while any of them is missing, empty or ``"UNKNOWN"``. ``build_freeze_record``
fills an absent field with ``"UNKNOWN"`` rather than a default, so a gap is
visible instead of being papered over by a plausible value.
"""
from __future__ import annotations

from typing import Any, Mapping

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C

__all__ = ["FREEZE_FIELDS", "V4R2_FREEZE_FIELDS", "NEW_IN_V4R3",
           "OPEN_DECISIONS", "THRESHOLD_PROVENANCE", "check_completeness",
           "build_freeze_record", "freeze"]

#: v4r2 §18.1's fields, carried so that a reader can see what is inherited.
V4R2_FREEZE_FIELDS = (
    "protocol_version", "model_repository", "model_revision",
    "prompt_template", "completion_cap", "n_star", "m_star",
    "wordings", "topic_splits", "chat_template_hash", "verifier_sources",
    "canonical_verifier_hash", "graded_score_definitions",
    "non_vacuity_predicates", "decoding_settings", "m_draws", "block_count",
    "variance_reestimate", "seed_rules", "cell_plan", "family_declarations",
    "thresholds_and_regions", "precision_preconditions", "claim_ladder",
    "codebook", "producing_commit", "clean_tree_assertion",
    "dependency_digest", "environment_digest", "hardware_record",
    "gate_record_hashes", "gate1_measurement_basis", "analysis_plan",
)

#: What v4r3 adds. Each is a degree of freedom that did not exist in v4r2 and
#: that a post-hoc change would otherwise be able to move.
NEW_IN_V4R3 = (
    "stem_sentence",                    # §8.5, byte-for-byte
    "focal_extension_measured",         # §7.2's escalation, per model
    "candidate_family_vocabulary",      # §7.0 + §7.3 + §7.4, all twenty
    "candidate_declared_range",         # §7.0, every ladder and every reserve
    "measured_vocabulary",              # §12.6, what the expansion closed
    "expansion_rule",                   # §12.6, rounds and per-family cap
    "coverage_criterion",               # §12.6's C1-C7 with their values
    "coverage_report",                  # the report that stopped the loop
    "lexical_rule",                     # §7.0's corrected composition order
    "family_class_labels",              # §7.5
    "difficulty_coordinate",            # §13.3
    "chance_compliance_definition",     # §13.3, §25
    "eligibility_band",                 # §13.5
    "core_reference_selection_rule",    # §13.4
    "core_references",                  # the three admitted, with severities
    "spectrum_selection_rule",          # §13.6
    "spectrum_offset",                  # §13.6
    "spectrum_severities",              # the six admitted
    "class_admission_rule",             # §13.7
    "class_companion",                  # or CLASS_ARM_NOT_AVAILABLE
    "class_match_caliper",              # §13.7
    "design_variant",                   # §8.6: full, no-spectrum or reduced
    "support_rule",                     # §13.8
    "calibration_table_hash",           # what the selections read
    "difficulty_model_form",            # §11.7
    "bootstrap_refit_algorithm",        # §17.2
    "joint_reading_table",              # §17.6
    "graded_clause_reading",            # §12.4
    "order_and_wording_allocation",     # §8.4
    # Added 2026-08-21 with amendment R1, before freeze. Each names something
    # the freeze must bind that the original list left implicit.
    "amendment_hashes",                 # §31: R1 and any successor, by hash
    "masking_rule",                     # §20: what is permuted, and the
                                        # declarations that travel with it
    "durability_record",                # §26: the pre-freeze durability gate,
                                        # with its stated limitation
)

FREEZE_FIELDS = V4R2_FREEZE_FIELDS + NEW_IN_V4R3

#: §33. Every one is closed by recording the decision and its evidence in the
#: signed manifest before study-wide freeze.
OPEN_DECISIONS = ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
                  "D10", "D11", "D12", "D13", "D14")

THRESHOLD_PROVENANCE: dict[str, str] = {
    "DELTA_R_GENERIC_THRESHOLD":
        "dci-construct-pass2.md §G row 1, 14 August 2026, verbatim",
    "DELTA_R_PAIR_SPECIFIC_THRESHOLD":
        "dci-construct-pass2.md §G row 1, 14 August 2026, verbatim",
    "SMALLEST_EFFECT_OF_INTEREST":
        "carried from v3 §11: a change of 0.10 moves a system prompt from "
        "80% to 70% compliance",
    "EQUIVALENCE_REGION": "the smallest effect of interest",
    "DELTA_DIFFICULTY_THRESHOLDS":
        "§11.8: direction against 0, equivalence against the smallest effect "
        "of interest. The memo's 0.25 is NOT transferred: it was defined for "
        "a difference between two observed losses, and delta_difficulty "
        "differences an observed loss against a fitted prediction",
    "XI": "§11.6, §11.8: a direction-only gate. No magnitude threshold is "
          "registered and none is invented",
    "REFERENCE_CALIPER":
        "§13.4: what the calibration sample supports -- the paired standard "
        "error of a solo difference over 96 topics at M_cal=4 is about 0.038",
    "REFERENCE_PRESCREEN_CALIPER": "§13.4 condition 2, disjoint confirmation",
    "REALISED_GAP_QUALIFIER": "§13.4, §28.1",
    "REFERENCE_VACUITY_MAX": "§13.4 condition 6",
    "REGIME_VACUITY_MAX": "§12.4 condition 2",
    "SPECTRUM_ELIGIBILITY_BAND":
        "§13.5: the floor is the registered smallest effect of interest, the "
        "ceiling is §12.3's focal band maximum. Neither number is new",
    "SPECTRUM_OFFSET":
        "§13.6: symmetric so the fit is centred on A, which is also the "
        "configuration whose prediction at A carries least leverage (§16.1)",
    "PRECISION_PRECONDITIONS":
        "§16.2: half the smallest effect of interest for D, Delta_R and "
        "delta_difficulty; v4r2's values for Lambda and Delta_j",
    "GRADED_DEGENERACY_SHARE_MAX":
        "§12.4, read as a share. The mean reading declares degenerate exactly "
        "the severities §12.3 declares eligible",
    "BETA_PLANNING":
        "§16.1: five times the largest slope magnitude any non-confirmatory "
        "screen produced. It enters the projection and nothing else (§16.5)",
}


def check_completeness(record: Mapping[str, Any], *,
                       decisions: Mapping[str, Any],
                       checks: Mapping[str, str] | None = None
                       ) -> dict[str, Any]:
    """Can this record be frozen? Every reason it cannot, listed."""
    missing = [f for f in FREEZE_FIELDS
               if f not in record or record[f] in (None, "", [], {}, "UNKNOWN")]
    unclosed = [d for d in OPEN_DECISIONS
                if d not in decisions or decisions[d] in (None, "", "UNKNOWN")]
    failing = sorted(k for k, v in (checks or {}).items() if v != "COMPLETE")
    return {
        "can_freeze": not (missing or unclosed or failing),
        "missing_fields": missing,
        "unclosed_decisions": unclosed,
        "incomplete_checks": failing,
        "fields_new_in_v4r3": list(NEW_IN_V4R3),
    }


def build_freeze_record(**supplied: Any) -> dict[str, Any]:
    """Assemble the record, marking every gap ``UNKNOWN`` rather than
    defaulting it."""
    unexpected = sorted(set(supplied) - set(FREEZE_FIELDS))
    if unexpected:
        raise ProtocolError(
            f"§18.1's field list is closed; {unexpected} is not in it. A new "
            "scientific degree of freedom must be added to FREEZE_FIELDS so "
            "that the freeze binds it, not passed through beside it.")
    record = {field: supplied.get(field, "UNKNOWN") for field in FREEZE_FIELDS}
    record["threshold_provenance"] = dict(THRESHOLD_PROVENANCE)
    record["stage"] = C.STAGE_GATE5
    record["artifact_type"] = C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE5]
    return record


def freeze(record: Mapping[str, Any], *, decisions: Mapping[str, Any],
           checks: Mapping[str, str] | None = None) -> dict[str, Any]:
    status = check_completeness(record, decisions=decisions, checks=checks)
    if not status["can_freeze"]:
        raise ProtocolError(
            "§18.1 refuses an incomplete freeze: "
            f"missing {status['missing_fields']}, "
            f"unclosed {status['unclosed_decisions']}, "
            f"incomplete {status['incomplete_checks']}")
    return {**dict(record), "outcome": "PASS", "frozen": True,
            "decisions": dict(decisions)}
