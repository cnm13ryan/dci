"""Every registered v4 value, in one place (preregistration v4r2).

Nothing here is inferred from v3, from v4 revision 1, or from the B+R pilot.
Where v4r2 gives a number this module gives that number and cites the
section; where v4r2 leaves ordinary engineering detail open the choice is
marked as such. Values that adapt by model (§6.1 cross-replication firewall)
are NOT here: they live on the per-model gate records and reach the code only
through them.
"""
from __future__ import annotations

# --------------------------------------------------------------- §6.2 topics
SUBJECT_AREAS = (
    "everyday_science", "history", "geography", "food", "music", "sport",
    "work_and_organisations", "health_and_the_body", "technology",
    "language_and_writing", "art_and_design", "the_natural_world",
)
TOPICS_PER_AREA = 52
PRESCREEN_PER_AREA = 2
SOLO_PER_AREA = 8
COMPOSED_PER_AREA = 2
CONFIRMATORY_PER_AREA = 32
SEQUESTERED_PER_AREA = 8

N_TOPICS = TOPICS_PER_AREA * len(SUBJECT_AREAS)                   # 624
N_PRESCREEN = PRESCREEN_PER_AREA * len(SUBJECT_AREAS)             # 24
N_SOLO = SOLO_PER_AREA * len(SUBJECT_AREAS)                       # 96
N_COMPOSED = COMPOSED_PER_AREA * len(SUBJECT_AREAS)               # 24
N_CONFIRMATORY = CONFIRMATORY_PER_AREA * len(SUBJECT_AREAS)       # 384
N_SEQUESTERED = SEQUESTERED_PER_AREA * len(SUBJECT_AREAS)         # 96
TOPIC_SETS = ("prescreen", "solo", "composed", "confirmatory", "sequestered")
SET_SIZES = {"prescreen": N_PRESCREEN, "solo": N_SOLO,
             "composed": N_COMPOSED, "confirmatory": N_CONFIRMATORY,
             "sequestered": N_SEQUESTERED}

#: §6.2, the four authoring rules every question is verified against.
AUTHORING_RULES = (
    "answerable_from_general_knowledge",
    "no_single_correct_short_answer",
    "no_reused_public_dataset_or_examination_text",
    "no_form_requirement_in_the_question_text",
)

# ------------------------------- §7.1-§7.2 grids, ladders, vacuity threshold
# Re-exported, not redefined. The registered grids and the non-vacuity word
# threshold are verifier SEMANTICS: they decide what a verifier returns, so
# they live inside the modules the canonical verifier hash covers
# (verifiers/constraints.py, verifiers/compliance.py) and are read from there.
# Defining them here instead would let a grid change slip past the §10.6
# binding, because this module is deliberately outside that hash.
from dci1v4.verifiers.compliance import (           # noqa: E402
    NON_VACUITY_MIN_WORDS,
)
from dci1v4.verifiers.constraints import (          # noqa: E402
    FAMILY_IDS,
    FOCAL_GRID,
    N_LADDER_SEVERITIES,
    REFERENCE_LADDERS,
    TARGET_GRID,
    TARGET_WORD,
)

CONSTRAINT_KINDS = ("A", "B") + FAMILY_IDS

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20     # §7.3: within 20% of A, not of B

# --------------------------------------------------------------- §8 design
#: The five registered constraint slots of a full-design replication, in the
#: registered order that fixes which constituent is "first" (§8.4).
REGISTERED_SLOTS = ("A", "B", "R1", "R2", "R3")
N_SOLO_CELLS = 5
N_UNORDERED_PAIRS = 10
N_ORDERS = 2
N_COMPOSED_CELLS = N_UNORDERED_PAIRS * N_ORDERS                    # 20
N_CELLS_FULL = N_SOLO_CELLS + N_COMPOSED_CELLS                     # 25
#: §8.6 reduced design: A solo, B solo, A+B in each order.
REDUCED_SLOTS = ("A", "B")
N_CELLS_REDUCED = 4

#: Order is a CELL-level factor (§8.4). "c1_first" states the constituent
#: earlier in REGISTERED_SLOTS first. These names are deliberately not v3's
#: block-level ``target_first`` / ``added_first``.
ORDER_C1_FIRST = "c1_first"
ORDER_C2_FIRST = "c2_first"
ORDERS = (ORDER_C1_FIRST, ORDER_C2_FIRST)

N_BLOCKS = 384                       # §8.3, the registered allocation
M_DRAWS = 4                          # §8.2, all M enter the cell mean
M_CAL = 4                            # §12.3, §13.6 calibration draws
LADDER_SCREEN_DRAWS = 1              # §12.2
GREEDY_BLOCKS = 96                   # §8.3 sensitivity run
GREEDY_DRAWS = 1
GREEDY_TEMPERATURE = 0.0
PILOT_TOPICS = 12                    # §19 procedural pilot
PILOT_DRAWS = 4

# ------------------------------------------------------- §8.5 prompt template
PROMPT_ZERO = "{question}\n\nAnswer:"
PROMPT_ONE = "{question}\n\n1. {c1}\n\nAnswer:"
PROMPT_TWO = "{question}\n\n1. {c1}\n2. {c2}\n\nAnswer:"

# ------------------------------------------------------- §12 operating regime
COMPLETION_CAPS = (512, 768, 1024)
CAP_TRUNCATION_MAX = 0.10            # §12.1
CAP_SELECTION_PROMPTS = 96           # §12.1, subject-balanced
#: §12.1 requires zero-, one- and two-constraint prompts in the cap set.
CAP_SET_LOADS = (0, 1, 2)
TRUNCATION_BOUND_THRESHOLD = 0.10    # §12.1, §25: above this, emit a bound

TARGET_BAND = (0.50, 0.85)           # §12.3 eligible solo compliance of A
TARGET_AIM = 0.70
FOCAL_BAND = (0.60, 0.95)            # §12.3 eligible solo compliance of B
FOCAL_AIM = 0.80
REGIME_VACUITY_MAX = 0.10            # §12.4, B solo vacuity
GRADED_DEGENERACY_HIGH = 0.99        # §12.4
GRADED_DEGENERACY_LOW = 0.01

# --------------------------------------------------- §13 reference admission
REFERENCE_CALIPER = 0.10             # §13.2 condition 1, calibration topics
REFERENCE_NEWCOMBE_REGION = 0.05     # §13.2 condition 1, interval must meet it
REFERENCE_PRESCREEN_CALIPER = 0.15   # §13.2 condition 2, disjoint pre-screen
REFERENCE_VACUITY_MAX = 0.10         # §13.2 condition 6
REALISED_GAP_QUALIFIER = 0.15        # §13.2, §28.1 companion-difficulty block
N_FINAL_REFERENCES = 3
LADDER_SHORTLIST_MAX = 3             # §12.2, per family
COMPOSED_HEADROOM_BAND = (0.05, 0.95)   # §13.6

# ------------------------------------------------------ §16 variance and menu
P_ONE_MINUS_P = 0.215
PHI_PRIMARY = 0.27                   # among-reference correlation 1
PHI_ALTERNATE = 0.37                 # among-reference correlation 0.5
RHO = 0.5                            # §16.1, assumed; check C12 estimates it
#: §16.3, every row live and selectable by the registered menu rule.
ALLOCATION_MENU = (
    {"blocks": 288, "M": 4},
    {"blocks": 384, "M": 4},
    {"blocks": 480, "M": 4},
    {"blocks": 384, "M": 8},
    {"blocks": 480, "M": 8},
)
SIDAK_K4 = 2.4909                    # §16.2, reference values; the bootstrap
SIDAK_K6 = 2.6310                    # supplies the exact critical value

# ---------------------------------------------- §11.6 thresholds and regions
DELTA_R_GENERIC_THRESHOLD = 0.10
DELTA_R_PAIR_SPECIFIC_THRESHOLD = 0.25
SMALLEST_EFFECT_OF_INTEREST = 0.10
EQUIVALENCE_REGION = 0.10
PRECISION_PRECONDITIONS = {"D": 0.05, "Delta_R": 0.05, "Lambda": 0.08,
                           "Delta_j": 0.06}

# ---------------------------------------------------------- §15 families
FAMILY_MEMBERS: dict[str, tuple[str, ...]] = {
    "F1": ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R"),
    "F2": ("D(B<-R1)", "D(B<-R2)", "D(B<-R3)",
           "Delta_1", "Delta_2", "Delta_3"),
    "F3": ("D(A<-R1)", "D(A<-R2)", "D(A<-R3)", "Delta^A"),
    "F4": ("D(Rbar<-A)", "D(Rbar<-B)", "D(Rbar<-Rbar')", "Xi"),
    "F5": ("D(B<-A)|vacuity_forced", "D(A<-B)|vacuity_forced",
           "Lambda|vacuity_forced", "Delta_R|vacuity_forced",
           "D(B<-A)|graded_0.99", "Delta_R|graded_0.99"),
    "F6": ("vac(B|A+B)-vac(B solo)", "vac(B|B+R1)-vac(B solo)",
           "vac(B|B+R2)-vac(B solo)", "vac(B|B+R3)-vac(B solo)"),
    "F7": ("D(R1<-B)", "D(R2<-B)", "D(R3<-B)",
           "D(R1<-A)", "D(R2<-A)", "D(R3<-A)"),
}
PRIMARY_FAMILY = "F1"
BOOTSTRAP_RESAMPLES = 10_000         # §17.1
F6_VACUITY_GATE = 0.05               # §17.4
GRADED_ROBUSTNESS_THRESHOLD = 0.99   # §15 F5

# ------------------------------------------------------------ §3 claim ladder
CLAIM_LEVELS = ("L1", "L2", "L3a", "L3b", "L3c", "L4", "L5")
#: §3: L5 is permanently withheld and no code path emits it.
WITHHELD_CLAIM_LEVELS = ("L5",)
MEASUREMENT_BASES = ("human_validated", "autorater_calibration_approved",
                     "human_validation_unavailable")
#: §10.5, attached verbatim while the basis is not ``human_validated``.
SCOPE_SENTENCE = ("the outcomes are verifier-defined and support no claim "
                  "about compliance as an independent human would judge it")
#: §28.3, attached verbatim to every terminal record.
TERMINAL_SENTENCE = ("a terminal pre-confirmatory status carries no evidence "
                     "about the effect")
#: §11.4, the registered wording for a position-shifted L1.
POSITION_WORDING = "composition and position change together"

# --------------------------------------------------------- §10.3 measurement
HUMAN_DISAGREEMENT_MAX = 0.10        # one-sided 95% Wilson upper bound
HUMAN_SAMPLE_CAP = 150               # min(150, N_c) per verifier class
VERIFIER_CLASSES = ("pass", "fail")
#: §10.3 addition: the fail class splits on whether the margin is exactly one.
FAIL_CLASS_STRATA = ("margin_one", "margin_larger")
BOUNDARY_SUITE_MIN_CASES = 40        # §10.2
DETERMINISM_PROCESSES = 3            # §10.2 three-process determinism

# --------------------------------------------------------- §18 stage sequence
STAGE_QUALIFIED = "QUALIFIED"
STAGE_GATE0 = "GATE_0_APPARATUS"
STAGE_REGIME = "REGIME_SCREEN"
STAGE_GATE1 = "GATE_1_MEASUREMENT"
STAGE_GATE2 = "GATE_2_REGIME"
STAGE_GATE3 = "GATE_3_REFERENCES"
STAGE_GATE4 = "GATE_4_COMPOSED_HEADROOM"
STAGE_GATE5 = "GATE_5_FREEZE"
STAGE_CONFIRMATORY = "CONFIRMATORY_GENERATION"
STAGE_MASKED_ANALYSIS = "MASKED_ANALYSIS"
STAGE_UNMASKING = "UNMASKING"
STAGE_UNMASKED_ANALYSIS = "UNMASKED_ANALYSIS"

STAGE_SEQUENCE = (
    STAGE_QUALIFIED, STAGE_GATE0, STAGE_REGIME, STAGE_GATE1, STAGE_GATE2,
    STAGE_GATE3, STAGE_GATE4, STAGE_GATE5, STAGE_CONFIRMATORY,
    STAGE_MASKED_ANALYSIS, STAGE_UNMASKING, STAGE_UNMASKED_ANALYSIS,
)
#: Stages that put prompts through the model.
GENERATION_STAGES = (STAGE_GATE0, STAGE_REGIME, STAGE_GATE2, STAGE_GATE4,
                     STAGE_CONFIRMATORY)
#: §10.6 + check C5: the eleven entry points that re-verify the frozen
#: verifier hash before any mutation.
VERIFIER_BOUND_ENTRY_POINTS = (
    "ladder_screen", "solo_calibration", "reference_admission",
    "composed_headroom", "freeze", "confirmatory_generation", "scoring",
    "resume_restart", "analysis", "unmasking", "report_generation",
)

# ------------------------------------------------------------ §28 statuses
TERMINAL_STATUSES = (
    "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
    "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
    "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
    "REGIME_NOT_FOUND", "COMPOSED_HEADROOM_FAILURE",
    "MEASUREMENT_NOT_ESTABLISHED", "MEASUREMENT_EVIDENCE_INSUFFICIENT",
)
IDENTIFICATION_STATUSES = ("EXCESS_NOT_IDENTIFIED", "POSITION_CONFOUNDED",
                           "HUMAN_VALIDATION_UNAVAILABLE")
RESULT_MARKERS = ("INSUFFICIENT_PRECISION", "INDETERMINATE")
#: §15 of the implementation brief: correct HISTORICAL labels for the two v3
#: Qwen terminations and the withdrawn revision 1 gate. v4 never EMITS them.
WITHDRAWN_STATUSES = ("REFERENCE_POOL_MISMATCH", "COMPOSED_UPTAKE_MISMATCH")

# -------------------------------------------------------- §26 artifact model
ARTIFACT_STATES = ("generated", "committed", "accepted", "superseded")
ARTIFACT_TYPES = (
    "qualification_record", "prefreeze_plan", "pilot_record", "gate_record",
    "calibration_record", "registered_freeze", "confirmatory_evidence",
    "masked_result", "unmasked_result", "superseded_non_evidence",
)
STAGE_ARTIFACT_TYPE = {
    STAGE_QUALIFIED: "qualification_record",
    STAGE_GATE0: "pilot_record",
    STAGE_REGIME: "gate_record",
    STAGE_GATE1: "gate_record",
    STAGE_GATE2: "calibration_record",
    STAGE_GATE3: "calibration_record",
    STAGE_GATE4: "calibration_record",
    STAGE_GATE5: "registered_freeze",
    STAGE_CONFIRMATORY: "confirmatory_evidence",
    STAGE_MASKED_ANALYSIS: "masked_result",
    STAGE_UNMASKING: "unmasked_result",
    STAGE_UNMASKED_ANALYSIS: "unmasked_result",
}

# ------------------------------------------------------------- §20 masking
MASK_NAMESPACES = ("pilot_mask", "confirmatory_mask")
MASK_MIN_DIFFERING_FRACTION = 0.5     # §20 executable check

# ------------------------------------------------- §14.2 missingness/duplicates
MISSINGNESS_REPORT_THRESHOLD = 0.01
DUPLICATE_QUALIFICATION_MAX = 0.05

# --------------------------------------------------------------- §22 mediator
#: §22, §27: recorded on every row, never a covariate, filter, stratifier or
#: weight. The codebook check reads this set.
POST_TREATMENT_FIELDS = (
    "word_count", "token_count", "truncated", "finish_reason", "graded",
    "vacuous_pass", "non_vacuous", "accidental_s0", "joint_state",
    "response_length_words", "processing_failure",
)
CAUSAL_ROLES = ("identity", "treatment", "design", "outcome",
                "post-treatment", "provenance")

# ------------------------------------------------------------- §9.2 S-rules
EXACT_COUNT_RULES = ("S0", "S1", "S2", "S3")
PRIMARY_EXACT_COUNT_RULE = "S0"

# ---------------------------------------------------------- §23 failure taxonomy
#: Applied in this priority order, to the exact-count outcome only (T-18).
FAILURE_TAXONOMY = ("empty", "cut_off", "refusal", "restatement",
                    "target_inside_longer_word", "zero_occurrences",
                    "too_few", "too_many", "other")
FAILURE_MARGIN_STRATA = ("margin_one", "margin_larger")
