"""statuses — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations


class GateStatus:
    PASS = "PASS"
    # The experiment cannot measure comparability precisely enough.
    PRECISION_INSUFFICIENT = "PRECISION_INSUFFICIENT"
    # Measurement is adequate; fewer than J admissible references exist.
    NOT_IDENTIFIED_SUPPORT = "NOT_IDENTIFIED_SUPPORT"
    # Screening cannot resolve a U candidate against the dynamic-range band.
    U_PRECISION_INSUFFICIENT = "U_PRECISION_INSUFFICIENT"
    # Enough precision; too few unrelated targets have usable dynamic range.
    U_BANK_NOT_IDENTIFIED = "U_BANK_NOT_IDENTIFIED"
    # The reference construction was evaluated and did not work.
    REFERENCE_VALIDATION_FAILED = "REFERENCE_VALIDATION_FAILED"
    # Too few pseudo-focals could be evaluated to judge it at all.
    REFERENCE_VALIDATION_NOT_EVALUABLE = "REFERENCE_VALIDATION_NOT_EVALUABLE"
    # Comparability does not transport to wordings never used to build it.
    WORDING_VALIDATION_FAILED = "WORDING_VALIDATION_FAILED"
    # Verifier reliability or paraphrase semantics not established.
    MEASUREMENT_VALIDITY_FAILED = "MEASUREMENT_VALIDITY_FAILED"
    # The frozen architecture did not generalise to the untouched targets.
    FINAL_FALSIFICATION_FAILED = "FINAL_FALSIFICATION_FAILED"

    # ---------------------------------------------------------------- v15
    # v14 collapsed four different measurement problems into one status, and
    # their remedies are not the same. A missing audit is clerical; an
    # underpowered audit needs more labels; a semantic paraphrase failure needs
    # new wordings; a demonstrated verifier defect needs new code and a new
    # protocol version, and more data can never resolve it.
    AUDIT_MISSING = "AUDIT_MISSING"
    AUDIT_UNDERPOWERED = "AUDIT_UNDERPOWERED"
    AUDIT_CLASS_SUPPORT_INSUFFICIENT = "AUDIT_CLASS_SUPPORT_INSUFFICIENT"
    PARAPHRASE_SEMANTICS_FAILED = "PARAPHRASE_SEMANTICS_FAILED"
    VERIFIER_RELIABILITY_FAILED = "VERIFIER_RELIABILITY_FAILED"
    # The joint reference-error certificate, not any single caliper, is binding.
    REFERENCE_BUDGET_EXCEEDED = "REFERENCE_BUDGET_EXCEEDED"
    # A sensitivity regression is rank deficient or too ill conditioned to read.
    SENSITIVITY_NOT_ESTIMABLE = "SENSITIVITY_NOT_ESTIMABLE"
    # A rendered scientific prompt does not fit inside the declared input cap.
    INPUT_TRUNCATION = "INPUT_TRUNCATION"
    # The declared output cap is plausibly dominating measured compliance.
    OUTPUT_CAP_DOMINATES = "OUTPUT_CAP_DOMINATES"
    # Resume would cross a hardware execution class boundary.
    HARDWARE_CLASS_MISMATCH = "HARDWARE_CLASS_MISMATCH"
    # A declared pilot/task allocation is short or overlapping.
    TASK_BANK_INSUFFICIENT = "TASK_BANK_INSUFFICIENT"
    # The confirmatory interval is too wide to support either claim.
    INCONCLUSIVE_PRECISION = "INCONCLUSIVE_PRECISION"
    # An anchor reference panel did not transport to a replicate model.
    TRANSPORT_FAILED = "TRANSPORT_FAILED"

    ALL = (PASS, PRECISION_INSUFFICIENT, NOT_IDENTIFIED_SUPPORT,
           U_PRECISION_INSUFFICIENT, U_BANK_NOT_IDENTIFIED,
           REFERENCE_VALIDATION_FAILED, REFERENCE_VALIDATION_NOT_EVALUABLE,
           WORDING_VALIDATION_FAILED, MEASUREMENT_VALIDITY_FAILED,
           FINAL_FALSIFICATION_FAILED,
           AUDIT_MISSING, AUDIT_UNDERPOWERED, AUDIT_CLASS_SUPPORT_INSUFFICIENT,
           PARAPHRASE_SEMANTICS_FAILED, VERIFIER_RELIABILITY_FAILED,
           REFERENCE_BUDGET_EXCEEDED, SENSITIVITY_NOT_ESTIMABLE,
           INPUT_TRUNCATION, OUTPUT_CAP_DOMINATES, HARDWARE_CLASS_MISMATCH,
           TASK_BANK_INSUFFICIENT, INCONCLUSIVE_PRECISION, TRANSPORT_FAILED)

    # Remedies that no amount of further data can supply. A semantic
    # contradiction and a demonstrated verifier defect are facts about the
    # design, so more_data_could_resolve is never true for them.
    NEVER_RESOLVED_BY_MORE_DATA = (
        NOT_IDENTIFIED_SUPPORT, U_BANK_NOT_IDENTIFIED,
        REFERENCE_VALIDATION_FAILED, WORDING_VALIDATION_FAILED,
        FINAL_FALSIFICATION_FAILED, PARAPHRASE_SEMANTICS_FAILED,
        VERIFIER_RELIABILITY_FAILED, REFERENCE_BUDGET_EXCEEDED,
        INPUT_TRUNCATION, HARDWARE_CLASS_MISMATCH, TRANSPORT_FAILED)
