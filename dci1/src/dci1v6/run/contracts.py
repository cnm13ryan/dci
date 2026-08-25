"""Who writes each field, who reads it, and the audit that they match.

This repository has been bitten more than once by a **reader with no
producer**: a downstream function that reads ``record["x"]`` where nothing
upstream ever writes ``x``. The defect is invisible until the path first
executes, which for a confirmatory study is after the expensive part. v4r4's
first real execution found several, and its L4 emitter was found after the
mask was sealed --- too late to repair under §20.

So the contract is written down and audited **statically**, before anything
runs, and again **at runtime** against the real payloads the synthetic
lifecycle produces.

Each entry is one field of one artifact: the stage that produces it, the
stages that read it, whether it is required, and the test that covers it.
``audit_contracts`` then establishes four things:

1. every reader names a stage that exists and comes **after** the producer;
2. every declared field has exactly one producer;
3. no required field is read by a stage the producer cannot precede;
4. given real payloads, every required field is actually present.

A required field with no producer is a blocking implementation defect and is
reported as one, not deferred to first execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C

__all__ = ["Field", "CONTRACT", "NEIGHBOURS", "SEMANTIC_CHECKS",
           "audit_contracts", "assert_contracts_clean", "matrix_rows",
           "matrix_markdown"]

_S = C
R, Q = _S.STAGE_REGISTERED, _S.STAGE_QUALIFIED
G0, RG, G1 = _S.STAGE_GATE0, _S.STAGE_REGIME, _S.STAGE_GATE1
G2, G25 = _S.STAGE_GATE2, _S.STAGE_GATE2_5
G275 = _S.STAGE_GATE2_75
G3A, G3B, G3C = _S.STAGE_GATE3A, _S.STAGE_GATE3B, _S.STAGE_GATE3C
G4, PF, G5 = _S.STAGE_GATE4, _S.STAGE_PREFREEZE_AUDIT, _S.STAGE_GATE5
CONF = _S.STAGE_CONFIRMATORY
MA, UN, UA = (_S.STAGE_MASKED_ANALYSIS, _S.STAGE_UNMASKING,
              _S.STAGE_UNMASKED_ANALYSIS)
FR = _S.STAGE_FINAL_REPORT


@dataclass(frozen=True)
class Field:
    artifact: str            # the producing stage's record
    field: str
    producer: str
    readers: tuple[str, ...]
    required: bool
    test: str

    def as_dict(self) -> dict[str, Any]:
        return {"artifact": self.artifact, "field": self.field,
                "producer": self.producer, "readers": list(self.readers),
                "stage_introduced": self.producer,
                "required": self.required, "test": self.test}


def _f(stage: str, field: str, readers: Sequence[str], *, required: bool = True,
       test: str = "tests_v6/test_run_contracts.py") -> Field:
    return Field(artifact=stage, field=field, producer=stage,
                 readers=tuple(readers), required=required, test=test)


#: Every field one v5 stage writes that another v5 stage reads. Fields a stage
#: writes purely for the record --- provenance, counts, the statements a
#: reader needs --- are not listed: this registry is about *contracts*, and a
#: field nobody reads cannot have a missing producer.
CONTRACT: tuple[Field, ...] = (
    # -------------------------------------------------- PROTOCOL_REGISTERED
    _f(R, "manifest_hash", (Q, G5, PF)),
    _f(R, "protocol_hash", (G5, PF)),
    _f(R, "reference_design_spec_hash", (G5, PF)),
    _f(R, "protocol_version", (G5,)),
    _f(R, "decisions", (PF,)),
    _f(R, "open_items", (PF,)),
    _f(R, "topic_hashes", (G5, PF)),
    _f(R, "calibration_a_hash", (G3A, G5)),
    _f(R, "calibration_b_hash", (G3A, G5)),
    _f(R, "split_hash", (G5,)),
    _f(R, "models", (G5, PF)),
    _f(R, "measurement_basis", (G1, G5, UA)),

    # ------------------------------------------------------------ QUALIFIED
    _f(Q, "canonical_verifier_hash", (G1,)),
    _f(Q, "instrument_population", (G1,)),
    _f(Q, "checks", (PF,)),
    _f(Q, "topic_split_identity", (G2, G3A)),

    # ------------------------------------------------------ GATE_0_APPARATUS
    _f(G0, "acceptance", (PF,)),
    _f(G0, "admitted_arms_exercised", (), required=False),

    # ---------------------------------------------------------- REGIME_SCREEN
    _f(RG, "selected_cap", (G1, G2, G4, CONF, G5)),
    # §12.2's high-recall carried set. Gate 2 is NOT a reader: §12.7's
    # calibration population is `calibration_priority`, and this registry
    # declaring G2 here is what V5-E6 looked like from the contract's side.
    # Gate 2 is a reader of the SIZE and of nothing else: `calibration_
    # population.carried_by_the_screen` puts §12.2's high-recall total beside
    # §12.7's measured population so a reader can see the difference. That it
    # does not SELECT from it is enforced by value, in `_audit_semantics`,
    # because a read is not what went wrong in V5-E6 --- the population was.
    _f(RG, "carried_set", (G2, G25, G3A, G3C, G5)),
    _f(RG, "n_carried", (G1, G2, PF)),
    # Gate 2 joins §12.2's measurement of each candidate onto §13.11's
    # table, so the two measurements of one instrument can be compared.
    _f(RG, "difficulty_table", (G2, G25, G3A)),
    _f(RG, "vocabulary_frozen", (PF, G5)),
    _f(RG, "coverage", (G5,)),
    # §12.7's calibration population, which Gate 2 measures.
    _f(RG, "calibration_priority", (G2, G3A)),
    # §12.6's expansion and the disposition it reached. The statuses are
    # design-time: Gate 3C admits no arm §12.6 dropped.
    # G3A reads the certified coverage as the baseline for its recorded
    # iota_A-drift diagnostic. A read, not a rule: nothing downstream of
    # the diagnostic exists.
    _f(RG, "expansion", (G3A, G5), required=False),
    _f(RG, "identification_statuses", (G3C, G5)),
    _f(RG, "iota_a_prescreen", (G3A,), required=False),

    # ----------------------------------------------------- GATE_1_MEASUREMENT
    _f(G1, "canonical_verifier_hash", (CONF, PF, G5)),
    _f(G1, "wording_hash", (PF, G5)),
    _f(G1, "measurement_basis", (UA, FR, G5)),
    _f(G1, "scope_sentence", (UA, FR)),
    _f(G1, "instrument_population", (G5,)),

    # ----------------------------------------------- GATE_2_FOCAL_CALIBRATION
    _f(G2, "n_star", (G25, G3B, G4, G5, CONF)),
    _f(G2, "m_star", (G25, G275, G3A, G3B, G4, G5, CONF)),
    _f(G2, "iota_a", (G3A, G3B, G5)),
    _f(G2, "solo_compliance_a", (G3A, G3B, G5)),
    _f(G2, "solo_compliance_b", (G5,)),
    _f(G2, "chance_curves", (G5,)),
    # The probe reads B's own solo curve: at a probed severity that value
    # is the same case Gate 2 measured, so it is read and not re-drawn.
    _f(G2, "solo_curves", (G275, G5)),
    _f(G2, "construct_strength", ()),
    _f(G2, "identification_statuses", (G3C, G5, UA)),
    _f(G2, "calibration_binding", (G3A, G5)),
    # §12.7's realised population, so a reader can see the 112 measured and
    # the Tier-3 rungs the budget dropped beside the screen's larger set.
    _f(G2, "calibration_population", (G5, PF)),
    _f(G2, "calibration_rows", (G25, G3A, G4)),
    # §12.4's three conditions and §12.3's grid-resolution diagnosis, as
    # verdicts rather than as the thresholds they are judged against.
    _f(G2, "adequacy", (G5,)),
    _f(G2, "grid_resolution", (G5,), required=False),
    # §13.7 subjects iota_A to the same equivalence rule as every candidate,
    # and the rule resamples topics, so Gate 3A needs A's per-topic vector.
    _f(G2, "a_per_topic_by_split", (G3A,)),
    _f(G2, "iota_a_by_split", (G3A,)),
    _f(G2, "solo_a_by_split", (G3A,)),
    _f(G2, "focal_extension_measured", (G5,)),
    # P3.1 probes the severities Gate 2 recorded as *eligible*, and P3.4
    # re-selects over Gate 2's own solo curve. Both are read by the probe and
    # by nothing else; declaring them is what makes the probe's inputs
    # auditable rather than incidental.
    _f(G2, "focal_selection", (G275, G5)),
    # §12.3's eligible set narrowed by §12.4 and §34 D17 evaluated at each
    # severity, and the kappa(R|B) column for each. Gate 2.75 re-selects
    # over the first; a stage after it reads §13.11's table through the
    # second. Both are computed before the probe observes anything.
    _f(G2, "focal_admissible", (G25, G275, G5)),
    _f(G2, "focal_admissibility", (G5,)),
    _f(G2, "kappa_under_b_by_severity", (G25, G3A)),
    # The operating-point search order, frozen before any composed row.
    _f(G2, "operating_point_search_order", (G25,)),
    _f(G2, "operating_point_search_rule", ()),
    # The topics this stage measured, against which a later stage checks
    # whether reusing one of its cells is the same case or a different one.
    _f(G2, "calibration_topic_ids", (G275,)),
    # Free from rows already scored, read by nothing, and deliberately off
    # §13.11's closed table so that it cannot reach a selection rule.
    _f(G2, "kappa_b_under_candidate", ()),
    # The two measurements of one instrument, joined. Read by nothing.
    _f(G2, "prescreen_to_calibration", ()),

    # ------------------------------------- GATE_2_5_CANDIDATE_QUALIFICATION
    _f(G25, "m_star", (G3A,)),
    _f(G25, "qualification", (G5,)),
    # The top-level pool is Gate 2's m*, which is this stage's own
    # predecessor's. Every stage after Gate 2.75 reads the by-severity
    # map instead, through `stages.feasibility.qualification_at`, because
    # the probe may have moved the operating point.
    _f(G25, "qualified_pool", ()),
    _f(G25, "qualified_families", ()),
    _f(G25, "earliest_failing_components", ()),
    _f(G25, "qualification_by_severity", (G3A, G3C, G5)),
    _f(G25, "qualified_at_severities", (G5,)),
    # Severities only. The family names behind the restriction stay here.
    _f(G25, "operating_point_order", (G275,)),
    _f(G25, "operating_point_order_reason", ()),
    _f(G25, "operating_point_support", ()),
    _f(G25, "operating_point_order_generates_nothing", ()),
    _f(G25, "interaction", (G3B, G5)),

    # ---------------------------------------------- GATE_2_75_COMPOSED_PROBE
    # The probe writes exactly one value a later stage reads --- m* --- and
    # m* is B's own severity, not a reference. Everything else on the record
    # is evidence for the freeze and for §33 check 8's name scan.
    _f(G275, "m_star", (G3A, G3B, G4, G5, CONF)),
    _f(G275, "m_star_in", (G5,)),
    # Gate 3A records whether the operating point it calibrates against was
    # re-selected, so a reader of its record does not have to go two stages
    # back to find out.
    _f(G275, "reselected", (G3A, G5)),
    _f(G275, "disposition", (G5,)),
    _f(G275, "margin", (G5,)),
    _f(G275, "margin_band", (G5,)),
    _f(G275, "band", (G5,)),
    _f(G275, "topic_split", (G5,)),
    _f(G275, "standins", (G5,)),
    _f(G275, "probe_cell_types", (G5,)),
    # Which cells were read off Gate 2 rather than drawn again, and why.
    _f(G275, "probe_cell_types_generated", ()),
    _f(G275, "shared_with_gate2", ()),
    _f(G275, "rows_not_drawn", ()),
    _f(G275, "scope_limits", (G5,)),
    _f(G275, "admissible_severities", (G5,)),
    _f(G275, "declared_refusals", (PF,)),

    # ------------------------------------- GATE_3A_REFERENCE_CALIBRATION
    _f(G3A, "m_star", (G3B, G4)),
    _f(G3A, "pooled_table", (G3B,)),
    _f(G3A, "stability", (G3B, G5, PF)),
    _f(G3A, "split_tables", (G5, PF)),
    _f(G3A, "calibration_b_population", (G5,)),
    _f(G3A, "iota_a_stability", (G5,), required=False),
    # The pool this stage used, named with the severity it qualified at.
    _f(G3A, "qualified_pool", (G5,)),
    _f(G3A, "qualified_families", ()),
    _f(G3A, "n_qualified", ()),
    _f(G3A, "qualified_at_m_star", (G5,)),
    # §12.6 re-read on the **calibration** basis at the iota_A selection
    # matches on --- the reading where iota(R), the eligibility coordinate,
    # the vacuity and iota_A all come from the same 192 topics at the same
    # four draws. It gates: Gate 3C takes its failures as design-time
    # failures, under §34 D6's existing disposition.
    _f(G3A, "coverage_at_calibrated_iota_a", ()),
    _f(G3A, "calibrated_coverage_failures", (G3C,)),

    # ---------------------------------------- GATE_3B_REFERENCE_SELECTION
    _f(G3B, "m_star", (G3C,)),
    _f(G3B, "selection", (G3C, G4, G5, PF, CONF)),
    _f(G3B, "iota_a", (G5,)),

    # ------------------------------------------- GATE_3C_IDENTIFICATION
    _f(G3C, "admitted_arms", (G4, G5, CONF, UA, FR, PF)),
    _f(G3C, "derived_cell_count", (G4, G5, CONF, PF)),
    _f(G3C, "slots", (G4, CONF)),
    _f(G3C, "identification_statuses", (G4, G5, UA, FR, PF)),
    _f(G3C, "support", (G5, FR, PF)),
    _f(G3C, "m_star", (G4, G5)),
    # §34 D6, closed at `identification_status`. Null when §13.15 was met, and
    # the key is present either way, so a reader can tell "the support held"
    # from "this record predates the decision".
    _f(G3C, "non_identification", (G5, FR)),
    _f(G3C, "not_identified_members", (G5, PF)),

    # ------------------------------------------- GATE_4_COMPOSED_HEADROOM
    _f(G4, "headroom_table", (G5, PF)),
    _f(G4, "admitted_arms", (G5, PF)),
    _f(G4, "failures", (G5, PF)),
    _f(G4, "expected_rows", (PF,)),
    _f(G4, "rows", (PF,)),
    _f(G4, "n_cell_types", (PF,)),
    # The operating point headroom was validated at. Gate 2.75 may have
    # moved it, and "was headroom checked at the severity the freeze
    # binds?" must be answerable from the records alone.
    _f(G4, "m_star", (PF, G5)),
    _f(G4, "slot_map", (PF,)),
    # Each bound instrument here against at Gate 2, paired.
    # Recorded; §13.14's verdict does not read it.
    _f(G4, "split_transfer", ()),
    # §33 check 8 requires the record to *declare* §13.14's refusal, not
    # merely to lack a field that names a substitution.
    _f(G4, "declared_refusals", (PF, FR)),

    # -------------------------------------------------------- PREFREEZE_AUDIT
    _f(PF, "can_freeze", (G5,)),
    _f(PF, "artifact_checks", (G5,)),
    _f(PF, "checklist", (G5, FR)),

    # ---------------------------------------------------------- GATE_5_FREEZE
    _f(G5, "freeze", (CONF, MA, UN, UA, FR)),
    _f(G5, "freeze_hash", (CONF, MA, UA, FR)),
    _f(G5, "blocks", (CONF,)),
    _f(G5, "cells_per_block", (CONF,)),
    _f(G5, "M", (CONF, MA, UA)),
    # §11.7's family grouping: the unmasked analysis reduces the slot map to
    # slot -> family, which is the one input `estimate_all` gets only after
    # the unmask.
    _f(G5, "slot_map", (CONF, UA)),
    _f(G5, "admitted_arms", (CONF, UA, FR)),
    _f(G5, "identification_statuses", (MA, UA, FR)),
    # §34 D6's irreversibility: the frozen non-identification, which the
    # unmasked analysis and the final report assert against rather than
    # re-deriving. A later stage that offered an estimate for a member named
    # here would be lifting a status the freeze bound.
    _f(G5, "non_identification", (UA, FR)),
    _f(G5, "selected_cap", (CONF,)),

    # ------------------------------------------------ CONFIRMATORY_GENERATION
    _f(CONF, "rows_path", (MA,)),
    _f(CONF, "n_rows", (MA, UA, FR)),
    _f(CONF, "completeness", (MA, FR), required=True),
    _f(CONF, "freeze_hash", (MA, UA)),

    # ---------------------------------------------------------- MASKED_ANALYSIS
    _f(MA, "mask_namespace", (UN,)),
    _f(MA, "masked_result_hash", (UN, UA)),
    _f(MA, "analysis_code_hash", (UN, UA)),
    _f(MA, "sealed", (UN,)),

    # ------------------------------------------------------------- UNMASKING
    _f(UN, "unmasked", (UA, FR)),
    _f(UN, "mask_key_hash", (UA,)),
    _f(UN, "unmask_event", (UA, FR)),

    # ------------------------------------------------------ UNMASKED_ANALYSIS
    _f(UA, "statements", (FR,)),
    _f(UA, "identification_statuses", (FR,)),
    _f(UA, "success_criterion", (FR,)),
    _f(UA, "estimands", (FR,)),
    _f(UA, "projection_audit", (FR,), required=False),
    # §18 step 14's raw-coordinate replication, read by §31's report as one
    # of §23's secondary analyses. Not required: the masked phase has no
    # value for it, and neither does a replication whose spectrum was never
    # identified.
    _f(UA, "raw_coordinate_secondary", (FR,), required=False),
)


def audit_contracts(payloads: Mapping[str, Mapping[str, Any]] | None = None,
                    reads: Mapping[str, Mapping[str, Sequence[str]]] | None
                    = None) -> dict[str, Any]:
    """The static audit, the payload audit, and the consumption audit.

    ``reads`` is ``run/field_access.observed()`` from a run of the synthetic
    scenario suite: reader stage -> producing artifact -> the fields that
    stage actually looked at. Without it this function can only check that a
    declared field was *produced*, which is what let a contract report 98
    fields and 0 defects while Gate 2 read the wrong one of two neighbours.
    """
    order = {stage: i for i, stage in enumerate(C.STAGE_SEQUENCE)}
    defects: list[dict[str, Any]] = []
    producers: dict[tuple[str, str], str] = {}

    for entry in CONTRACT:
        key = (entry.artifact, entry.field)
        if key in producers:
            defects.append({"kind": "DUPLICATE_PRODUCER",
                            "artifact": entry.artifact, "field": entry.field})
        producers[key] = entry.producer
        if entry.producer not in order:
            defects.append({"kind": "UNKNOWN_PRODUCER",
                            "artifact": entry.artifact, "field": entry.field,
                            "producer": entry.producer})
            continue
        for reader in entry.readers:
            if reader not in order:
                defects.append({"kind": "UNKNOWN_READER",
                                "artifact": entry.artifact,
                                "field": entry.field, "reader": reader})
            elif order[reader] <= order[entry.producer]:
                defects.append({"kind": "READER_PRECEDES_PRODUCER",
                                "artifact": entry.artifact,
                                "field": entry.field, "reader": reader,
                                "producer": entry.producer})

    checked = 0
    if payloads is not None:
        for entry in CONTRACT:
            payload = payloads.get(entry.artifact)
            if payload is None:
                continue
            checked += 1
            if entry.required and entry.field not in payload:
                defects.append({"kind": "REQUIRED_FIELD_NOT_PRODUCED",
                                "artifact": entry.artifact,
                                "field": entry.field,
                                "producer": entry.producer,
                                "readers": list(entry.readers)})

    consumption = semantic_run = 0
    relayed: list[dict[str, Any]] = []
    unconsumed: list[dict[str, Any]] = []
    if payloads is not None and reads is not None:
        consumption, consumption_defects, relayed, unconsumed = (
            _audit_consumption(payloads, reads))
        defects.extend(consumption_defects)
        semantic_run, semantic_defects = _audit_semantics(payloads, reads)
        defects.extend(semantic_defects)
        consumption += semantic_run

    return {
        "n_fields": len(CONTRACT),
        "n_artifacts": len({e.artifact for e in CONTRACT}),
        "n_checked_against_payloads": checked + consumption,
        "n_field_presence_checks": checked,
        "n_consumption_checks": consumption,
        "n_semantic_checks": semantic_run,
        "relayed": relayed,
        "n_relayed": len(relayed),
        # A declared reader with no observed read is REPORTED, not failed.
        # It is one of two things and the audit cannot yet tell them apart: a
        # declaration with nothing behind it, or a rule that is not on the
        # path. Separating them needs the field read at the place the value
        # is used, and the tracker sees top-level keys --- a value taken from
        # inside a nested block, or from a copy a later stage made, reads as
        # unconsumed here. What it is NOT is the V5-E6 shape: that is
        # `UNDECLARED_READ` and the semantic checks, and both fail.
        "unconsumed": unconsumed,
        "n_unconsumed": len(unconsumed),
        "defects": defects,
        "n_defects": len(defects),
        "clean": not defects,
    }


#: Pairs of neighbouring fields where reading the wrong one is a scientific
#: defect rather than a style question, with the rule that decides. This is
#: the registry V5-E6 would have been caught by: `carried_set` and
#: `calibration_priority` are both on the regime record, both are lists of
#: candidate labels, and only one of them is §12.7's calibration population.
NEIGHBOURS: tuple[tuple[str, str, str, str], ...] = (
    (RG, "calibration_priority", "carried_set",
     "§12.7: Gate 2 measures the calibration population --- every Tier-1/2 "
     "rung plus at most 24 Tier-3 --- and NOT §12.2's high-recall carried "
     "set. Reading `carried_set` here puts the Tier-3 rungs §12.7 drops for "
     "budget into candidate qualification and from there into reference "
     "selection"),
)


#: Stages that read **every** record by construction, so an undeclared read
#: by one of them is not a finding: the pre-freeze audit iterates
#: `STAGE_SEQUENCE` to check the artifacts, and the final report hashes every
#: signed record to make §31's table traceable.
WHOLESALE_READERS: tuple[str, ...] = (PF, FR)

#: Provenance carried on every stage record and read by every generating
#: stage through `protocol_identity`. Not a scientific consumer relationship.
PROVENANCE_FIELDS: tuple[str, ...] = ("manifest_hash", "protocol_hash",
                                      "producing_commit")


def _audit_consumption(payloads: Mapping[str, Mapping[str, Any]],
                       reads: Mapping[str, Mapping[str, Sequence[str]]]
                       ) -> tuple[int, list[dict[str, Any]],
                                  list[dict[str, Any]],
                                  list[dict[str, Any]]]:
    """Observed reads against declared ones, both directions.

    A field a declared reader never touched is a declaration with nothing
    behind it. A field a stage read without a declaration is the shape of
    V5-E6: the runner reached for a neighbour and nothing said it may.
    """
    defects: list[dict[str, Any]] = []
    unconsumed: list[dict[str, Any]] = []
    declared: dict[tuple[str, str], set[str]] = {}
    for entry in CONTRACT:
        for reader in entry.readers:
            declared.setdefault((reader, entry.artifact),
                                set()).add(entry.field)
    checked = 0
    ran = set(payloads)
    relayed: list[dict[str, Any]] = []
    for entry in CONTRACT:
        if entry.artifact not in ran:
            continue
        for reader in entry.readers:
            if reader not in ran:
                continue
            checked += 1
            by_artifact = reads.get(reader) or {}
            if entry.field in set(by_artifact.get(entry.artifact) or ()):
                continue
            # A value can reach its consumer **relayed**: §18's later stages
            # copy n*, m*, the arm set and the identification statuses onto
            # their own records, and Gate 4 reads n* from the freeze rather
            # than from Gate 2. The contract's readers are the stages that
            # CONSUME the value, so a relayed read satisfies the declaration
            # --- and is recorded as relayed, because the relay is a place a
            # value could change and nobody would see it.
            via = sorted(artifact for artifact, fields in by_artifact.items()
                         if entry.field in set(fields)
                         and artifact != entry.artifact)
            if via:
                relayed.append({"artifact": entry.artifact,
                                "field": entry.field, "reader": reader,
                                "via": via})
                continue
            unconsumed.append({
                "kind": "UNCONSUMED_DECLARATION",
                "artifact": entry.artifact, "field": entry.field,
                "reader": reader,
                "detail": "the contract declares this reader and no read of "
                          "the field was observed on any record"})
    for reader, by_artifact in sorted(reads.items()):
        for artifact, fields in sorted(by_artifact.items()):
            if artifact not in ran or reader not in ran:
                continue
            if reader in WHOLESALE_READERS:
                continue
            known = {e.field for e in CONTRACT if e.artifact == artifact}
            allowed = declared.get((reader, artifact), set())
            for field in sorted(set(fields)):
                if (field in allowed or field not in known
                        or field in PROVENANCE_FIELDS):
                    continue
                defects.append({
                    "kind": "UNDECLARED_READ",
                    "artifact": artifact, "field": field, "reader": reader,
                    "detail": "this stage read a contracted field the "
                              "contract does not declare it a reader of"})
    return checked, defects, relayed, unconsumed


#: Value-level assertions on the real payloads, each naming the section it
#: enforces. A presence check cannot tell 326 from 112.
SEMANTIC_CHECKS: tuple[str, ...] = (
    "gate2_measures_the_calibration_population",
    "gate2_did_not_measure_the_carried_set",
    "coverage_verdict_reaches_gate3c",
    "every_registered_family_member_is_accounted_for",
)


def _audit_semantics(payloads: Mapping[str, Mapping[str, Any]],
                     reads: Mapping[str, Mapping[str, Sequence[str]]]
                     ) -> tuple[int, list[dict[str, Any]]]:
    """The value-level checks named in ``SEMANTIC_CHECKS``.

    Returns how many of them had the payloads they need **and ran**, beside
    what they found. A check with no payload to inspect is not a check that
    passed, and counting it as one is how an audit reports coverage it does
    not have.
    """
    defects: list[dict[str, Any]] = []
    ran = 0
    regime, gate2 = payloads.get(RG), payloads.get(G2)

    if regime is not None and gate2 is not None:
        ran += 2
        priority = regime.get("calibration_priority") or {}
        expected = (len(priority.get("tier12") or ())
                    + len(priority.get("tier3_measured") or ()))
        population = gate2.get("calibration_population") or {}
        measured = population.get("n_measured")
        if measured != expected:
            defects.append({
                "kind": "WRONG_INPUT_FIELD",
                "check": "gate2_measures_the_calibration_population",
                "artifact": G2, "field": "calibration_population",
                "expected": expected, "observed": measured,
                "detail": NEIGHBOURS[0][3]})
        carried = len(regime.get("carried_set") or ())
        if measured is not None and carried != expected \
                and measured == carried:
            defects.append({
                "kind": "WRONG_INPUT_FIELD",
                "check": "gate2_did_not_measure_the_carried_set",
                "artifact": G2, "field": "calibration_population",
                "expected": expected, "observed": measured,
                "detail": NEIGHBOURS[0][3]})
    gate3c = payloads.get(G3C)
    if regime is not None and gate3c is not None:
        ran += 1
        screen = set(regime.get("identification_statuses") or ())
        recorded = set(gate3c.get("identification_statuses") or ())
        missing = sorted(screen - recorded)
        if missing:
            defects.append({
                "kind": "OUTPUT_DROPPED",
                "check": "coverage_verdict_reaches_gate3c",
                "artifact": RG, "field": "identification_statuses",
                "reader": G3C, "missing": missing,
                "detail": "§12.6 decides at the screen which arms the "
                          "replication runs; a status the screen recorded "
                          "and Gate 3C does not carry is a rule computed "
                          "and dropped"})

    analysis = payloads.get(UA)
    if analysis is not None:
        ran += 1
        estimands = analysis.get("estimands") or {}
        accounted = set(estimands.get("not_identified") or ()) | set(
            estimands.get("not_computable") or ())
        for bucket in (estimands.get("configurations") or {}).values():
            accounted |= set(bucket)
        accounted |= set(estimands.get("cross_configuration") or {})
        for family, members in C.FAMILY_MEMBERS.items():
            missing = sorted(set(members) - accounted)
            if missing:
                defects.append({
                    "kind": "OUTPUT_DROPPED",
                    "check": "every_registered_family_member_is_accounted_for",
                    "artifact": UA, "field": "estimands", "family": family,
                    "missing": missing,
                    "detail": "§15 registers this member; the analysis record "
                              "neither estimates it nor declares why not, so "
                              "it is absent rather than unidentified"})
    return ran, defects


def assert_contracts_clean(payloads: Mapping[str, Mapping[str, Any]] | None
                           = None,
                           reads: Mapping[str, Mapping[str, Sequence[str]]]
                           | None = None) -> dict[str, Any]:
    result = audit_contracts(payloads, reads)
    if payloads is not None and not result["n_checked_against_payloads"]:
        raise ProtocolError(
            "the producer/consumer audit checked nothing against a real "
            "payload. A run that validates declarations against declarations "
            "reports zero defects whatever the runner does")
    if result["defects"]:
        raise ProtocolError(
            f"the producer/consumer contract has {result['n_defects']} "
            f"defect(s): {result['defects'][:5]}. A required field with no "
            "producer is a blocking implementation defect")
    return result


def matrix_rows(payloads: Mapping[str, Mapping[str, Any]] | None = None
                ) -> list[dict[str, Any]]:
    """The audit matrix, one row per (artifact, field)."""
    rows = []
    for entry in CONTRACT:
        row = entry.as_dict()
        if payloads is not None and entry.artifact in payloads:
            present = entry.field in payloads[entry.artifact]
            row["status"] = ("PRODUCED" if present
                             else "MISSING" if entry.required
                             else "ABSENT_OPTIONAL")
            row["exercised"] = present
        else:
            row["status"] = "NOT_EXERCISED"
            row["exercised"] = False
        rows.append(row)
    return rows


def matrix_markdown(payloads: Mapping[str, Mapping[str, Any]] | None = None
                    ) -> str:
    """The same matrix as a Markdown table, for the status report."""
    head = ("| artifact | field | producer | reader(s) | stage introduced | "
            "required | test | exercised | status |\n"
            "|---|---|---|---|---|---|---|---|---|")
    lines = [head]
    for row in matrix_rows(payloads):
        lines.append(
            f"| `{row['artifact']}` | `{row['field']}` | "
            f"`{row['producer']}` | "
            f"{', '.join('`' + r + '`' for r in row['readers']) or '—'} | "
            f"`{row['stage_introduced']}` | "
            f"{'yes' if row['required'] else 'no'} | "
            f"`{row['test']}` | "
            f"{'yes' if row.get('exercised') else 'no'} | "
            f"{row['status']} |")
    return "\n".join(lines)
