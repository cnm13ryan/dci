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
    "PILOT_CRITERIA", "FRAME_RELIABILITY_MARGIN", "FRAME_REFERENCE_SOURCE",
    "RESCREEN_TOPIC_SOURCE", "RESCREEN_TOPICS_PER_AREA", "GATE0_TOPICS",
    "GATE0_DRAWS", "MIN_LOCAL_FAMILIES", "MIN_CORE_REFERENCES",
    "MIN_BACKUPS", "NO_COMPOSED_CELLS",
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

NAMESPACES = ("pilot", "synthetic")

# ---------------------------------------------------------------- criteria
#: The four questions the pilot exists to answer (V8_CANDIDATE.md §12),
#: evaluated by ``report.pilot_payload`` on the signed records alone.
PILOT_CRITERIA = ("FRAME_RELIABILITY", "LADDER_COVERAGE", "CHANCE_BASIS",
                  "REFERENCE_SURVIVAL")

#: FRAME_RELIABILITY: every v8 frame's marker-absent share (A and MK rows of
#: the regime screen, per wording index) is at most the **best v7 frame's
#: share on the same model** plus this margin. The reference shares are read
#: from the v7 wording audit at registration and bound in the manifest
#: (``manifest.frame_reference``); the margin is half the smallest effect of
#: interest on a rate (§11.9: 0.10), against a per-frame sampling SE of
#: ≈ 0.015 at 24 topics × 72 A/MK rungs. Without a margin the criterion is
#: unattainable on qwen3-4b-instruct-2507, whose best v7 frame had 0 absent
#: rows in 1,536.
FRAME_RELIABILITY_MARGIN = 0.05
FRAME_REFERENCE_SOURCE = "dci1/reports/dci1v8dev/frame_reference.json"

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
