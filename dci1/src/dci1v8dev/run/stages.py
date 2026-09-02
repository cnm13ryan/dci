"""The pilot's nine stages, their records, and the four prospective criteria.

Nine stages where v7 has nineteen: the pilot stops where the candidate's
open questions are answered --- before any composed cell exists --- and the
sequence has no stage that could render one. Order is enforced by
``transitions.PREDECESSOR``; every stage owns exactly one record file and one
artifact type, asserted at import.

The criteria are the ones ``dci1/docs/V8_CANDIDATE.md`` §12 names for the
pilot, stated here as constants with their provenance so the report stage
evaluates registered-in-advance thresholds and never a number chosen after
seeing the pilot's rows. ``dci1v8dev.rules`` holds the rule layer's
constants; this module holds only what the execution layer adds.
"""
from __future__ import annotations

from dci1v7.protocol import constants as C
from dci1v8dev import rules as R

__all__ = [
    "STAGE_REGISTERED", "STAGE_QUALIFIED", "STAGE_GATE0", "STAGE_REGIME",
    "STAGE_SECOND_PASS", "STAGE_GATE1", "STAGE_GATE2", "STAGE_GATE3",
    "STAGE_REPORT", "STAGE_SEQUENCE", "STAGE_RECORD_FILES",
    "STAGE_ARTIFACT_TYPE", "ARTIFACT_TYPES", "GENERATION_STAGES",
    "TERMINAL_STATUSES", "TERMINAL_SENTENCE", "NAMESPACES",
    "PILOT_CRITERIA", "DECIDED_CRITERIA", "WORDING_REFERENCE_BOUND",
    "WORDING_POLICY_OPTIONS", "WORDING_POLICY_STATUS", "WORDING_POLICY",
    "FRAME_CONDITIONING", "FRAMES", "FRAME_STATES", "FRAME_SUPPORTED",
    "FRAME_UNSUPPORTED", "FRAME_FAILURE_STATUSES",
    "CONFIRMATORY_BLOCKS_PER_FRAME", "CONFIRMATORY_FRAME_OFFSETS",
    "CONFIRMATORY_FRAME_PASSES", "CONFIRMATORY_BLOCKS_TOTAL",
    "CONFIRMATORY_MAX_PASSES", "CONFIRMATORY_MAX_BLOCKS_PER_FRAME",
    "confirmatory_allocation", "REPORT_AGGREGATION",
    "CALIBRATION_FRAME_OFFSETS", "CALIBRATION_FRAME_PASSES",
    "CALIBRATION_TOPICS_PER_FRAME", "CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT",
    "CALIBRATION_FRAME_OFFSETS_BY_MODEL", "calibration_frame_offsets",
    "calibration_passes", "calibration_topics_per_frame",
    "calibration_topics_per_frame_per_split",
    "calibration_generations_per_rung",
    "RESCREEN_TOPIC_SOURCE", "RESCREEN_TOPICS_PER_AREA", "GATE0_TOPICS",
    "GATE0_DRAWS", "MIN_LOCAL_FAMILIES", "MIN_CORE_REFERENCES",
    "MIN_BACKUPS", "LOCAL_ELIGIBILITY_MIN_FRAMES", "NO_COMPOSED_CELLS",
]

# ------------------------------------------------------------------ stages
STAGE_REGISTERED = "PILOT_REGISTERED"
STAGE_QUALIFIED = "QUALIFIED"
STAGE_GATE0 = "GATE_0_APPARATUS"
STAGE_REGIME = "REGIME_SCREEN"
STAGE_SECOND_PASS = "SECOND_PASS_SCREEN"
STAGE_GATE1 = "GATE_1_INSTRUMENT"
STAGE_GATE2 = "GATE_2_CALIBRATION"
STAGE_GATE3 = "GATE_3_REFERENCES"
STAGE_REPORT = "PILOT_REPORT"

STAGE_SEQUENCE = (
    STAGE_REGISTERED, STAGE_QUALIFIED, STAGE_GATE0, STAGE_REGIME,
    STAGE_SECOND_PASS, STAGE_GATE1, STAGE_GATE2, STAGE_GATE3, STAGE_REPORT,
)
assert len(STAGE_SEQUENCE) == 9

STAGE_RECORD_FILES = {
    STAGE_REGISTERED: "pilot_registration.json",
    STAGE_QUALIFIED: "qualification_record.json",
    STAGE_GATE0: "gate0_apparatus.json",
    STAGE_REGIME: "regime_record.json",
    STAGE_SECOND_PASS: "second_pass_record.json",
    STAGE_GATE1: "gate1_instrument.json",
    STAGE_GATE2: "gate2_calibration.json",
    STAGE_GATE3: "gate3_references.json",
    STAGE_REPORT: "pilot_report.json",
}
assert set(STAGE_RECORD_FILES) == set(STAGE_SEQUENCE)

ARTIFACT_TYPES = ("registration_record", "qualification_record",
                  "pilot_record", "gate_record", "screen_record",
                  "calibration_record", "selection_record", "pilot_report")
STAGE_ARTIFACT_TYPE = {
    STAGE_REGISTERED: "registration_record",
    STAGE_QUALIFIED: "qualification_record",
    STAGE_GATE0: "pilot_record",
    STAGE_REGIME: "screen_record",
    STAGE_SECOND_PASS: "screen_record",
    STAGE_GATE1: "gate_record",
    STAGE_GATE2: "calibration_record",
    STAGE_GATE3: "selection_record",
    STAGE_REPORT: "pilot_report",
}
assert set(STAGE_ARTIFACT_TYPE) == set(STAGE_SEQUENCE)
assert set(STAGE_ARTIFACT_TYPE.values()) <= set(ARTIFACT_TYPES)

#: The stages that generate model responses. Every one of them generates
#: load-0 and load-1 cells only: ``NO_COMPOSED_CELLS`` is asserted by
#: ``execute.prompt_cell`` on every cell it renders.
GENERATION_STAGES = (STAGE_GATE0, STAGE_REGIME, STAGE_SECOND_PASS,
                     STAGE_GATE2)
#: The pilot renders no composed cell. Not a setting: a cell with two slots
#: is refused at rendering, and no stage builds one.
NO_COMPOSED_CELLS = True

#: v7's apparatus and operating-regime terminals, unchanged in meaning. The
#: pilot's four scientific questions never terminate: each is *recorded* on
#: the stage that measures it and summarised by ``PILOT_REPORT``.
TERMINAL_STATUSES = (
    "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
    "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
    "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
    "REGIME_NOT_FOUND",
)
TERMINAL_SENTENCE = ("a terminal pilot status is a statement about the "
                     "apparatus or the operating regime and carries no "
                     "evidence about the effect or about the v8 candidate")

NAMESPACES = ("pilot", "synthetic", "confirm", "confirm-synthetic")
#: The two confirmatory namespaces (``dci1v8dev.confirm``): the pinned
#: backend under a signed freeze, and the stand-in generator for the
#: synthetic walk. A confirm root carries the same study id as a pilot
#: root and is refused by every pilot stage (``confirm.lifecycle``).
CONFIRM_NAMESPACES = ("confirm", "confirm-synthetic")

# ---------------------------------------------------------------- criteria
#: The four questions the pilot exists to answer (V8_CANDIDATE.md §12),
#: evaluated by ``report.pilot_payload`` on the signed records alone.
PILOT_CRITERIA = ("WORDING_DIAGNOSTIC", "LADDER_COVERAGE", "CHANCE_BASIS",
                  "REFERENCE_SURVIVAL")
#: The criteria with a registered pass/fail rule. WORDING_DIAGNOSTIC has
#: none (researcher decision, 2026-08-30): the report shows the per-frame
#: measurements and the judgment is left explicit.
DECIDED_CRITERIA = ("LADDER_COVERAGE", "CHANCE_BASIS", "REFERENCE_SURVIVAL")

#: WORDING_DIAGNOSTIC: the four v8 frames measured separately per (family,
#: q) --- sample, exact compliance, chance on the unconstrained cell, ι, SE,
#: and the comparison across frames (``run/wording.py``). Two frames'
#: difference in ι is described against the registered §13.7 equivalence
#: bound (the bound two independent measurements of one instrument must
#: satisfy); it is a descriptive reference and decides nothing. v7's frame
#: statistics affect no v8 verdict (they remain in
#: reports/dci1v8dev/frame_reference.json as a descriptive report only).
WORDING_REFERENCE_BOUND = C.STABILITY_EQUIVALENCE_BOUND
#: The wording policy: the three options the pilot's diagnostic was written
#: to inform, and the decision. Researcher decision of 2026-08-30 (after
#: pilot r3; dci1/docs/V8_FRAME_CONDITIONING.md): the wording frame is part
#: of the experimental condition --- the ``model_frame_variation`` option in
#: its strongest form. No frame is retained or discarded on the diagnostic;
#: every frame is calibrated, matched and selected on its own. The
#: diagnostic itself keeps no pass/fail rule.
WORDING_POLICY_OPTIONS = ("retain_all_frames", "retain_specified_subset",
                          "model_frame_variation")
WORDING_POLICY = "model_frame_variation"
WORDING_POLICY_STATUS = "DECIDED"
assert WORDING_POLICY in WORDING_POLICY_OPTIONS

# ------------------------------------------------------- frame conditioning
#: Approach A: the wording frame f in 0..N_WORDINGS-1 (one per block,
#: ``block.index % N_WORDINGS``) is part of the experimental condition.
#: Difficulty is ι(X, f); the operating points n*(f), m*(f), every validity,
#: every selection and every eventual estimand (Δ_R(f), the
#: difficulty-response slope) are per frame; frames are compared only after
#: the frame-specific quantities exist. Pooling over frames is descriptive
#: and decides nothing (``GATE_2_CALIBRATION.descriptive_pooled``).
FRAME_CONDITIONING = "frame_is_experimental_condition"
FRAMES = tuple(range(C.N_WORDINGS))
#: A frame with n*(f), m*(f) and §12.4 adequacy on its own rates; an
#: unsupported frame records which §12.3/§12.4 status it hit and takes no
#: further part. The replication is terminal only when no frame is supported.
FRAME_SUPPORTED = "SUPPORTED"
FRAME_UNSUPPORTED = "UNSUPPORTED"
FRAME_FAILURE_STATUSES = ("TARGET_RANGE_EXHAUSTED", "FOCAL_RANGE_EXHAUSTED",
                          "GRID_RESOLUTION_INSUFFICIENT", "REGIME_NOT_FOUND")
assert set(FRAME_FAILURE_STATUSES) <= set(TERMINAL_STATUSES)
#: Gate 3's explicit per-frame state: LOCAL = the three core references are
#: identified by §13.8's kernel; SPECTRUM = ``selected_coverage`` identified.
FRAME_STATES = ("UNSUPPORTED", "NEITHER", "LOCAL_ONLY", "SPECTRUM_ONLY",
                "LOCAL_AND_SPECTRUM")
#: The confirmatory blocks a frame-specific estimate rests on: the
#: registered blocks times the confirmatory passes, divided by the wordings
#: (rules.py; derived). Three passes, 288 per frame, since the amendment of
#: 2026-08-31; one pass and 96 before it. It sets the precision of every
#: frame-specific estimate and of the design-time projections that quote
#: one, and it decides no admission.
CONFIRMATORY_BLOCKS_PER_FRAME = R.CONFIRMATORY_BLOCKS_PER_FRAME
CONFIRMATORY_FRAME_OFFSETS = R.CONFIRMATORY_FRAME_OFFSETS
CONFIRMATORY_FRAME_PASSES = R.CONFIRMATORY_FRAME_PASSES
CONFIRMATORY_BLOCKS_TOTAL = R.CONFIRMATORY_BLOCKS_TOTAL
CONFIRMATORY_MAX_PASSES = R.CONFIRMATORY_MAX_PASSES
CONFIRMATORY_MAX_BLOCKS_PER_FRAME = R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME
confirmatory_allocation = R.confirmatory_allocation
assert CONFIRMATORY_BLOCKS_PER_FRAME * C.N_WORDINGS == (
    C.N_BLOCKS * CONFIRMATORY_FRAME_PASSES)
#: Gate 2's calibration allocation (rules.py): one pass over the calibration
#: topics per frame offset, so a frame's own table is measured on
#: ``calibration_topics_per_frame(model_key)`` distinct topics --- 96 of the
#: 192 at the two default offsets, 48 from each §13.7 split; 192 and 96 at
#: ``qwen3-4b``'s four, which is the ceiling. The amendment of 2026-08-30
#: after r5/r6 measured SE(iota) on the precision floor, and that of
#: 2026-08-31 after r8 measured §13.7 condition 1 refusing rungs on the
#: *split* coordinate; both change how much is measured within a frame and
#: no threshold.
#:
#: **The constants below are the default allocation.** A stage that measures
#: or asserts anything about a particular replication must call the resolver
#: with that run's ``model_key``; these are for the paths with no model in
#: scope.
CALIBRATION_FRAME_OFFSETS = R.CALIBRATION_FRAME_OFFSETS
CALIBRATION_FRAME_PASSES = R.CALIBRATION_FRAME_PASSES
CALIBRATION_TOPICS_PER_FRAME = R.CALIBRATION_TOPICS_PER_FRAME
CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT = R.CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT
CALIBRATION_FRAME_OFFSETS_BY_MODEL = R.CALIBRATION_FRAME_OFFSETS_BY_MODEL
calibration_frame_offsets = R.calibration_frame_offsets
calibration_passes = R.calibration_passes
calibration_topics_per_frame = R.calibration_topics_per_frame
calibration_topics_per_frame_per_split = R.calibration_topics_per_frame_per_split
calibration_generations_per_rung = R.calibration_generations_per_rung
assert CALIBRATION_TOPICS_PER_FRAME * C.N_WORDINGS == (
    C.N_CALIBRATION * CALIBRATION_FRAME_PASSES)
for _m, _o in CALIBRATION_FRAME_OFFSETS_BY_MODEL.items():
    assert calibration_topics_per_frame(_m) * C.N_WORDINGS == (
        C.N_CALIBRATION * len(_o))
    assert calibration_topics_per_frame_per_split(_m) * 2 == \
        calibration_topics_per_frame(_m)
#: The report's run-level aggregate over frames (V8_FRAME_CONDITIONING.md
#: §7): a decided criterion ``passed`` when at least one supported frame
#: passes it, every frame's verdict recorded beside it. Not a freeze rule.
REPORT_AGGREGATION = "any_supported_frame"

#: SECOND_PASS_SCREEN measures each batch on fresh topics. §12.5 admits only
#: the three development sets to iterative work, the pre-screen set is spent
#: at round 0, so the batches are cut from **Calibration-A** --- two topics
#: per area per batch, disjoint across batches (three batches use 72 of its
#: 96) --- and Calibration-B is left untouched by every selection step, so
#: §13.7's split equivalence still has one selection-free half to compare
#: against. Recorded per batch on the stage record.
RESCREEN_TOPIC_SOURCE = C.CALIBRATION_A
RESCREEN_TOPICS_PER_AREA = R.RESCREEN_BATCH_TOPICS // C.N_AREAS
assert RESCREEN_TOPICS_PER_AREA * C.N_AREAS == R.RESCREEN_BATCH_TOPICS
assert (RESCREEN_TOPICS_PER_AREA * R.RESCREEN_MAX_BATCHES
        <= C.CALIBRATION_A_PER_AREA)

#: GATE_0_APPARATUS: §19's shape --- twelve pre-screen topics, M = 4 ---
#: over the pilot's own cell plan (load 0 and load 1 only).
GATE0_TOPICS = C.PILOT_TOPICS
GATE0_DRAWS = C.PILOT_DRAWS

#: REFERENCE_SURVIVAL: §13.15's requirement on the admissible basis.
MIN_LOCAL_FAMILIES = C.MIN_QUALIFIED_FAMILIES          # 5
MIN_CORE_REFERENCES = C.N_CORE_REFERENCES               # 3
MIN_BACKUPS = C.N_BACKUP_FAMILIES                       # 2

#: The LOCAL inclusion rule (rules.py; researcher decision of 2026-08-31).
#: A frame is LOCAL-supported iff it meets *all three* of the above on its
#: own table; a model is LOCAL-eligible iff at least this many frames are.
#: Deliberately separate from ``FRAME_STATES``: ``LOCAL_AND_SPECTRUM`` says
#: the core was identified and the coverage gate passed, which a frame can
#: reach on four LOCAL-valid families and one backup --- §13.15 unsatisfied.
LOCAL_ELIGIBILITY_MIN_FRAMES = R.LOCAL_ELIGIBILITY_MIN_FRAMES
