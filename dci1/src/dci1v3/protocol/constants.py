"""Every registered value of DCI-1 v3, transcribed from
``user-notes/DCI-1_preregistration_v3.md`` (the sole scientific authority).

Nothing here is a default: each value is either stated in the preregistration
or is a registration-manifest value fixed by this module before any v3
artifact exists (root seeds, model revisions), recorded in DECISIONS_V3.md.
"""
from __future__ import annotations

from dci1v3.errors import ProtocolError  # noqa: F401  (re-exported)

# --------------------------------------------------------------- identity
PROTOCOL = "DCI-1"
PROTOCOL_VERSION = "3.0"
STUDY_ID = "dci1-v3"
SYNTHETIC_STUDY_ID = "dci1-v3-synthetic"   # structurally separate namespace
HASH_FUNCTION = "sha256"                   # the study-wide manifest hash H

# --------------------------------------------------------------- topics (§6)
SUBJECT_AREAS = (
    "everyday science", "history", "geography", "food", "music", "sport",
    "work and organisations", "health and the body", "technology",
    "language and writing", "art and design", "the natural world",
)
TOPICS_PER_AREA = 52
SEQUESTERED_PER_AREA = 8
RELEASED_PER_AREA = TOPICS_PER_AREA - SEQUESTERED_PER_AREA       # 44
CALIBRATION_PER_AREA = 12
PRESCREEN_PER_AREA = 2
SOLO_PER_AREA = 8
COMPOSED_PER_AREA = 2
CONFIRMATORY_PER_AREA = 32
N_TOPICS = TOPICS_PER_AREA * len(SUBJECT_AREAS)                  # 624
N_PRESCREEN = PRESCREEN_PER_AREA * len(SUBJECT_AREAS)            # 24
N_SOLO = SOLO_PER_AREA * len(SUBJECT_AREAS)                      # 96
N_COMPOSED = COMPOSED_PER_AREA * len(SUBJECT_AREAS)              # 24
N_CONFIRMATORY = CONFIRMATORY_PER_AREA * len(SUBJECT_AREAS)      # 384
N_SEQUESTERED = SEQUESTERED_PER_AREA * len(SUBJECT_AREAS)        # 96
assert CALIBRATION_PER_AREA == (PRESCREEN_PER_AREA + SOLO_PER_AREA
                                + COMPOSED_PER_AREA)
assert RELEASED_PER_AREA == CALIBRATION_PER_AREA + CONFIRMATORY_PER_AREA

# ------------------------------------------------- constraints and grids (§5)
TARGET_WORD = "however"
TARGET_GRID = (1, 2, 3, 4, 5, 6, 7, 8)             # n
FOCAL_GRID = (7, 8, 9, 10)                          # m

#: The eight reference families: identifier -> severity grid, least to most
#: restrictive (§5). Wording templates live in protocol/wordings.py; verdict
#: functions in verifiers/families.py.
REFERENCE_FAMILIES: dict[str, tuple[int, ...]] = {
    "RF1": (8, 5, 2, 0),    # words beginning with b
    "RF2": (8, 5, 2, 0),    # words ending with ing
    "RF3": (8, 5, 2, 0),    # one-letter words
    "RF4": (6, 4, 2, 0),    # words with identical adjacent letters
    "RF5": (12, 8, 4, 0),   # comma characters
    "RF6": (12, 8, 4, 0),   # upper-case English letters
    "RF7": (24, 16, 8, 0),  # words containing a
    "RF8": (8, 5, 2, 0),    # words ending with y
}
FAMILY_IDS = tuple(REFERENCE_FAMILIES)              # tie-break order (§18.5)
N_FINAL_REFERENCES = 3

# ------------------------------------------------------------- design (§8)
ARMS = ("AB", "AR1", "AR2", "AR3", "A", "TOPIC")
PRIMARY_ARMS = ("AB", "AR1", "AR2", "AR3")
DIAGNOSTIC_ARMS = ("A", "TOPIC")
N_BLOCKS = 384
BLOCKS_PER_ORDER = 192
M_DRAWS = 16
N_CELLS = N_BLOCKS * len(ARMS)                      # 2,304
N_CACHED_DRAWS = N_CELLS * M_DRAWS                  # 36,864
N_PRIMARY = N_CELLS                                  # 2,304
GREEDY_BLOCKS = 96                                   # first confirmatory 96
GREEDY_GENERATIONS = GREEDY_BLOCKS * len(PRIMARY_ARMS)  # 384

TARGET_FIRST = "target_first"
ADDED_FIRST = "added_first"
ORDERS = (TARGET_FIRST, ADDED_FIRST)

# ------------------------------------------------------------ inference (§4)
DECODING = {"temperature": 0.7, "top_p": 0.9, "top_k": 50}
GREEDY_DECODING = {"temperature": 0.0, "top_p": 1.0, "top_k": 0}
DTYPE = "bfloat16"
CAP_GRID = (512, 768, 1024)                          # completion-token caps
CALIBRATION_DRAWS_PER_CELL = 1
PRESCREEN_CAP_PROMPTS = 96                           # subject-balanced set
PRESCREEN_CAP_PER_AREA = PRESCREEN_CAP_PROMPTS // len(SUBJECT_AREAS)  # 8

# ------------------------------------------------------ procedural pilot (§17)
PILOT_TOPICS = 12
PILOT_N = 3
PILOT_M = 9
#: Fixed reference fixtures: (family, severity), in arm order AR1, AR2, AR3.
PILOT_REFERENCES = (("RF1", 5), ("RF2", 5), ("RF5", 8))
PILOT_CAP = 1024
PILOT_CELLS = PILOT_TOPICS * len(ARMS)               # 72
PILOT_DRAWS = PILOT_CELLS * M_DRAWS                  # 1,152

# ----------------------------------------------- gates and bands (§18, §11)
TRUNCATION_MAX = 0.10
TARGET_BAND = (0.15, 0.50)
FOCAL_BAND = (0.15, 0.55)
COMPOSED_BAND = (0.15, 0.85)
SELECTION_CENTRE = 0.30
REFERENCE_CALIPER = 0.10                             # |p_R - p_B| <= 0.10
WORDING_LENGTH_TOLERANCE = 0.20                      # ±20% word count
PRESCREEN_FOCAL_BAND = (0.15, 0.55)
PRESCREEN_NEWCOMBE_BAND = (-0.10, 0.10)
SESOI = 0.10
EQUIVALENCE_REGION = (-SESOI, SESOI)
EXCHANGEABILITY_MARGIN = 0.05
EXCHANGEABILITY_REGION = (-EXCHANGEABILITY_MARGIN, EXCHANGEABILITY_MARGIN)
UPTAKE_DIFFERENCE_FLAG = 0.25                        # §16 manipulation check
F6_ASYMMETRY_FLAG = 0.05                             # §16 arm symmetry
SHORT_RESPONSE_WORDS = 3                             # §16 compliance flag

# ------------------------------------------------------- measurement (§10)
GATE1_DISAGREEMENT_MAX = 0.10        # one-sided 95% Wilson upper bound
GATE1_CLASS_TARGET = 150             # natural cases per verifier class
GATE1_EXTRA_RESPONSES_MAX = 300      # frozen additional validation set
GATE1_ANNOTATORS = 3
DETERMINISM_PROCESSES = 3
DETERMINISM_REQUIRED = 1.0
BOUNDARY_CASES_REQUIRED = 40
WORDING_SUITE_SIZE = 20              # responses per wording-equivalence suite

# ---------------------------------------------------------- analysis (§13-14)
BOOTSTRAP_RESAMPLES = 10_000
PSEUDO_RUNS = 1_000
CONFIDENCE = 0.95
FAMILY_SIZES = {"F1": 2, "F2": 3, "F3": 6, "F4": 6, "F5": 9, "F6": 3}
FAILURE_CATEGORIES = (
    "empty", "cut_off", "refusal", "restatement",
    "target_inside_longer_word", "zero_occurrences", "too_few", "too_many",
    "other",
)
RESTATEMENT_SIMILARITY = 0.60
MASK_MIN_CHANGED_FRACTION = 0.5      # §19 executable check 1

# ---------------------------------------------------------- stages (item 6)
STAGE_QUALIFIED = "QUALIFIED"
STAGE_GATE0 = "GATE_0_APPARATUS_PASS"
STAGE_REGIME = "REGIME_SCREEN_PASS"
STAGE_GATE1 = "GATE_1_MEASUREMENT_PASS"
STAGE_GATE2A = "GATE_2A_SOLO_CALIBRATION_PASS"
STAGE_GATE2B = "GATE_2B_COMPOSED_VALIDATION_PASS"
STAGE_FREEZE = "GATE_3_FREEZE"
STAGE_CONFIRMATORY = "CONFIRMATORY_GENERATION"
STAGE_PRIMARY_SELECTION = "PRIMARY_SELECTION"
STAGE_MASK = "CONFIRMATORY_MASK"
STAGE_MASKED_ANALYSIS = "MASKED_ANALYSIS"
STAGE_UNMASK = "UNMASKING"
STAGE_UNMASKED_ANALYSIS = "UNMASKED_ANALYSIS"

#: The only permitted scientific stage sequence. Every stage verifies its
#: immediate predecessor's PASS record (hash + signature) before mutation.
STAGE_SEQUENCE = (
    STAGE_QUALIFIED, STAGE_GATE0, STAGE_REGIME, STAGE_GATE1, STAGE_GATE2A,
    STAGE_GATE2B, STAGE_FREEZE, STAGE_CONFIRMATORY, STAGE_PRIMARY_SELECTION,
    STAGE_MASK, STAGE_MASKED_ANALYSIS, STAGE_UNMASK,
    STAGE_UNMASKED_ANALYSIS,
)

#: Stages that generate model output (a terminal state disables all of them).
GENERATION_STAGES = (STAGE_QUALIFIED, STAGE_GATE0, STAGE_REGIME, STAGE_GATE1,
                     STAGE_GATE2A, STAGE_GATE2B, STAGE_CONFIRMATORY)

# --------------------------------------------- terminal statuses (item 60)
TERMINAL_STATUSES = (
    "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
    "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
    "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
    "REFERENCE_POOL_MISMATCH", "COMPOSED_HEADROOM_FAILURE",
    "MEASUREMENT_NOT_ESTABLISHED", "MEASUREMENT_EVIDENCE_INSUFFICIENT",
)

# ------------------------------------------------ artifact semantics (§27)
ARTIFACT_STATES = ("generated", "committed", "accepted", "superseded")
ARTIFACT_TYPES = (
    "qualification_record", "prefreeze_plan", "pilot_record", "gate_record",
    "calibration_record", "registered_freeze", "confirmatory_evidence",
    "masked_result", "unmasked_result", "superseded_non_evidence",
)

#: Stage -> the artifact type its stage record carries (item 55 vocabulary).
STAGE_ARTIFACT_TYPE = {
    STAGE_QUALIFIED: "qualification_record",
    STAGE_GATE0: "pilot_record",
    STAGE_REGIME: "gate_record",
    STAGE_GATE1: "gate_record",
    STAGE_GATE2A: "calibration_record",
    STAGE_GATE2B: "calibration_record",
    STAGE_FREEZE: "registered_freeze",
    STAGE_CONFIRMATORY: "confirmatory_evidence",
    STAGE_PRIMARY_SELECTION: "confirmatory_evidence",
    STAGE_MASK: "confirmatory_evidence",
    STAGE_MASKED_ANALYSIS: "masked_result",
    STAGE_UNMASK: "unmasked_result",
    STAGE_UNMASKED_ANALYSIS: "unmasked_result",
}

# -------------------------------------------------------------- seeds
#: Registration-manifest root seeds, fixed before any v3 artifact
#: (DECISIONS_V3 V02). Three separated randomness levels plus design seeds.
GENERATION_ROOT_SEED = 202608170
PSEUDO_RUN_ROOT_SEED = 202608171
BOOTSTRAP_ROOT_SEED = 202608172
TOPIC_SPLIT_SEED = 202608173
GATE1_SAMPLE_SEED = 202608174
ENGINE_SEED = 20260817

DOMAIN_GENERATION = "dci1v3:gen:v1"
DOMAIN_PSEUDO = "dci1v3:pseudo:v1"
DOMAIN_BOOTSTRAP = "dci1v3:boot:v1"
DOMAIN_TOPIC_SPLIT = "dci1v3:topics:v1"
DOMAIN_GATE1_SAMPLE = "dci1v3:gate1:v1"
PRIMARY_SELECTION_DOMAIN = "primary-root"            # item 40, verbatim

# ---------------------------------------------------------- prompt template
#: §7: topic question, numbered list of active constraints, ``Answer:``.
PROMPT_TWO = "{question}\n\n1. {c1}\n2. {c2}\n\nAnswer:"
PROMPT_ONE = "{question}\n\n1. {c1}\n\nAnswer:"
PROMPT_ZERO = "{question}\n\nAnswer:"
