"""§18.1's freeze record, and the rule that replaced VARIANT_EXEMPTIONS.

The freeze binds the scientific state. Everything a later stage may read about
what the study *is* comes from here, and after it passes
``assert_no_post_freeze_mutation`` refuses any write at or before it.

**v4r4 patched its freeze with a table and v5 states the rule instead.**
v4r4's ``VARIANT_EXEMPTIONS`` named, per design variant, the fields that
variant was allowed to leave empty --- which works only for the variants the
table enumerates and explains an absence by a lookup. §18.1's general form is:

> A field a variant legitimately leaves empty is declared empty, **with the
> identification status that explains it**, and the freeze refuses an empty
> field that no status explains.

``assert_field_emptiness_explained`` is that rule. It needs no per-variant
table because the thing that makes a field legitimately empty is always an
identification status §13 wrote at design time onto a signed record ---
``REFERENCE_SUPPORT_NOT_IDENTIFIED`` empties the core references,
``DIFFICULTY_SUPPORT_NOT_IDENTIFIED`` the spectrum,
``NEAR_FORM_ARM_NOT_AVAILABLE`` the near-form controls,
``CLASS_ARM_NOT_AVAILABLE`` the broad-class companion.

**§34 D6's non-identification is frozen here too.** The freeze carries Gate
3C's ``non_identification`` block verbatim, so the estimand set a replication
may no longer identify is part of the signed scientific state rather than a
fact only the Gate-3C record remembers. Everything downstream reads it through
``protocol/identification.assert_not_rehabilitated``. v7 A7: the block may
carry ``DIFFICULTY_SUPPORT_NOT_IDENTIFIED`` and name only the
spectrum-dependent members, in which case ``core_references`` is non-empty
and ``spectrum_severities`` is the field the status explains. v7 A6: the
pre-freeze audit assembles this record without writing it, so an empty field
no status explains is refused one stage earlier than here --- and a
replication that lost its reference set under D6 actually reaches this stage,
which until 2026-08-28 none did.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.design.cells import n_cells_for, normalise_arms
from dci1v7.protocol import constants as C

__all__ = ["REQUIRED_FIELDS", "EMPTIABLE_FIELDS", "NEVER_EMPTY",
           "assert_field_emptiness_explained", "assert_freeze_complete",
           "build_freeze_record"]

#: §18.1, in the order the section states them.
REQUIRED_FIELDS: tuple[str, ...] = (
    "protocol_version", "protocol_hash", "reference_design_spec_hash",
    "model_repository", "model_revision", "prompt_template", "stem_sentence",
    "completion_cap", "n_star", "m_star", "focal_extension_measured",
    "bracketing_status", "candidate_family_vocabulary", "ladders", "reserves",
    "structural_metadata", "tiers", "wordings",
    "difficulty_coordinate_definition", "chance_definition",
    "counterfactual_chance_definition", "validity_components",
    "validity_thresholds", "calibration_a_table_hash",
    "calibration_b_table_hash", "qualified_pool",
    "earliest_failing_components", "core_references", "spectrum_severities",
    "near_form_controls", "broad_class_control", "frozen_backup_families",
    "backups_never_substituted", "support_rule", "support_realised",
    "non_identification",
    "admitted_arms", "derived_cell_count", "order_allocation",
    "wording_allocation", "topic_splits", "split_seed", "seed_rules",
    "m_draws", "n_blocks", "variance_reestimate", "verifier_sources",
    "canonical_verifier_hash", "wording_hash", "graded_score_definitions",
    "non_vacuity_predicates", "decoding_settings", "family_declarations",
    "difficulty_model_form", "tier_indicator_secondary", "bootstrap_algorithm",
    "thresholds", "regions", "precision_preconditions", "claim_ladder",
    "l4_emitters", "disagreement_rules", "codebook", "producing_commit",
    "clean_tree", "dependency_digest", "environment_digest", "hardware",
    "gate_record_hashes", "measurement_basis", "reuse_ledger_hash",
    "analysis_plan", "open_decisions",
    # New in v6. §18.1 binds the operating point the study runs. m* is
    # §12.3's choice at Gate 2 and the probe cannot move it; binding the
    # probe's record beside m* is what lets a reader see the composed
    # contrast the frozen operating point was found to have.
    "composed_probe",
    # New in v7. Gate 4's projection of every registered contrast on the
    # composed set, with its boundary readings, bound so that the
    # qualification the analysis attaches at the end was on a signed record
    # before the freeze.
    "composed_contrast_projection",
    # New in v7 (A4). The signed amendment chain the bound document hashes
    # were reached through. Empty for a study amended nowhere.
    "amendments", "registered_protocol_hash",
)

#: Which identification status makes each field legitimately empty. A field
#: not listed here may **never** be empty, whatever happened.
EMPTIABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "core_references": ("REFERENCE_SUPPORT_NOT_IDENTIFIED",
                        "EXCESS_NOT_IDENTIFIED"),
    "spectrum_severities": ("DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
                            "REFERENCE_SUPPORT_NOT_IDENTIFIED"),
    "near_form_controls": ("NEAR_FORM_ARM_NOT_AVAILABLE",),
    "broad_class_control": ("CLASS_ARM_NOT_AVAILABLE",),
    "frozen_backup_families": ("REFERENCE_SUPPORT_NOT_IDENTIFIED",),
    "qualified_pool": ("REFERENCE_SUPPORT_NOT_IDENTIFIED",),
    "earliest_failing_components": (),
    "focal_extension_measured": (),
    "open_decisions": (),
    # §34 D6. Null is the *normal* state --- §13.15 was met and nothing is
    # unidentified --- so no status is required to explain the emptiness.
    # What may not happen is the reverse: a record that is non-null here and
    # a later stage that estimates one of the members it names.
    "non_identification": (),
    "amendments": (),
}
NEVER_EMPTY = tuple(f for f in REQUIRED_FIELDS if f not in EMPTIABLE_FIELDS)

#: The design elements each optional arm binds at the freeze. A6's invariant
#: is that the frozen design is exactly Gate 3C's identification state, and
#: ``assert_field_emptiness_explained`` checks only one direction of it ---
#: an *empty* field needs a status. This is the other direction: a field
#: that is bound while its arm is not admitted binds a design the
#: replication does not run, and a field that is empty while its arm is
#: admitted freezes an arm with nothing in it. Both refuse (2026-08-28).
ARM_BOUND_FIELDS: dict[str, str] = {
    "core_references": C.ARM_CORE,
    "frozen_backup_families": C.ARM_CORE,
    "spectrum_severities": C.ARM_SPECTRUM,
    "near_form_controls": C.ARM_NEAR_FORM,
    "broad_class_control": C.ARM_CLASS,
}


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, dict, set)):
        return len(value) == 0
    return False


def assert_field_emptiness_explained(record: Mapping[str, Any], *,
                                     identification_statuses: Sequence[str]
                                     ) -> dict[str, Any]:
    """§18.1: an empty field is declared empty with the status that explains it.

    The general form of what v4r4's ``VARIANT_EXEMPTIONS`` did specially.
    """
    statuses = set(identification_statuses)
    unexplained: list[dict[str, Any]] = []
    explained: list[dict[str, Any]] = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            continue
        if not _is_empty(record[field]):
            continue
        allowed = EMPTIABLE_FIELDS.get(field)
        if allowed is None:
            unexplained.append({"field": field,
                                "reason": "no identification status can make "
                                          "this field empty"})
            continue
        matching = sorted(statuses & set(allowed))
        if allowed and not matching:
            unexplained.append({"field": field, "admissible_statuses":
                                list(allowed), "recorded": sorted(statuses)})
            continue
        explained.append({"field": field, "explained_by": matching or
                          ["empty by construction"]})
    if unexplained:
        raise ProtocolError(
            f"§18.1: these freeze fields are empty and no identification "
            f"status explains them: {unexplained}")
    return {"explained_empty": explained, "unexplained_empty": []}


def assert_freeze_complete(record: Mapping[str, Any], *,
                           identification_statuses: Sequence[str] = ()
                           ) -> dict[str, Any]:
    """Every §18.1 field present, and every empty one explained."""
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise ProtocolError(
            f"§18.1: the freeze record is missing {len(missing)} required "
            f"field(s): {missing[:12]}"
            f"{'...' if len(missing) > 12 else ''}")
    emptiness = assert_field_emptiness_explained(
        record, identification_statuses=identification_statuses)
    arms = normalise_arms(record["admitted_arms"])
    mismatched = [
        {"field": field, "arm": arm,
         "admitted": arm in arms, "bound": not _is_empty(record.get(field))}
        for field, arm in ARM_BOUND_FIELDS.items()
        if (arm in arms) != (not _is_empty(record.get(field)))]
    if mismatched:
        raise ProtocolError(
            "§18.1 / v7 A6: the freeze binds the design elements of exactly "
            "the arms Gate 3C admitted, and this record does not: "
            f"{mismatched}")
    if record["derived_cell_count"] != n_cells_for(arms):
        raise ProtocolError(
            f"§8.1: the admitted arm set {list(arms)} derives "
            f"{n_cells_for(arms)} cells and the freeze records "
            f"{record['derived_cell_count']}")
    if record.get("backups_never_substituted") is not True:
        raise ProtocolError(
            "§13.14: the freeze carries the statement that the frozen "
            "backups are never substituted into an admitted slot after "
            "Gate 4; this record does not")
    if record.get("measurement_basis") != C.MEASUREMENT_BASIS:
        raise ProtocolError(
            f"§10.5: v5's Gate 1 writes {C.MEASUREMENT_BASIS!r} and refuses "
            f"every other basis; this record declares "
            f"{record.get('measurement_basis')!r}")
    if record.get("open_decisions"):
        raise ProtocolError(
            f"§34: {record['open_decisions']} are still open, so the "
            "registration manifest cannot have been signed and nothing "
            "downstream of stage 1 may have run")
    return {"fields": len(REQUIRED_FIELDS), **emptiness,
            "admitted_arms": list(arms),
            "derived_cell_count": record["derived_cell_count"]}


def build_freeze_record(**fields: Any) -> dict[str, Any]:
    """Assemble a §18.1 record, filling the invariants this module knows.

    Deliberately thin: everything scientific comes from the caller's signed
    upstream records, and what is filled here is what the protocol fixes for
    every replication.
    """
    record: dict[str, Any] = {
        "stage": C.STAGE_GATE5,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE5],
        "protocol_version": "7.0",
        "stem_sentence": C.STEM_SENTENCE,
        "prompt_template": {"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                            "two": C.PROMPT_TWO},
        "difficulty_coordinate_definition":
            "(p_solo - kappa) / (1 - kappa), §13.2",
        "chance_definition": "P(X_c = 1 | unconstrained cell), §11.2",
        "counterfactual_chance_definition":
            "P(X_c = 1 | B alone at m*, c absent), §13.6",
        "validity_components": list(C.VALIDITY_COMPONENTS),
        "backups_never_substituted": True,
        "support_rule": {
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "n_backup_families": C.N_BACKUP_FAMILIES},
        "stage_sequence": list(C.STAGE_SEQUENCE),
        "m_draws": C.M_DRAWS, "n_blocks": C.N_BLOCKS,
        "bootstrap_algorithm": {
            "resamples": C.BOOTSTRAP_RESAMPLES, "unit": "block",
            "refit_every_replicate": True},
        "family_declarations": {k: list(v)
                                for k, v in C.FAMILY_MEMBERS.items()},
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "claim_ladder": list(C.CLAIM_LEVELS),
        "l4_emitters": ["emit_l4a (per named member)", "emit_l4b (F11)"],
        "measurement_basis": C.MEASUREMENT_BASIS,
        "graded_score_definitions": "§7.9, per constraint form",
        "non_vacuity_predicates": "§9.3, per constraint form",
        "difficulty_model_form": "Y = alpha_f + beta*d, OLS, nine points",
        "tier_indicator_secondary":
            "Y = alpha_f + beta*d + gamma*1[Tier 2], twelve points, F8",
    }
    record.update(fields)
    return record
