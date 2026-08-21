"""Every registered v4r4 value, in one place (preregistration v4r4).

Where v4r4 gives a number this module gives that number and cites the section.
Values that adapt by model (§6.1 cross-replication firewall) are NOT here:
they live on the per-model gate records and reach the code only through them.

Grids, ladders, classes and the non-vacuity threshold are verifier
*semantics* -- they decide what a verifier returns -- so they live inside the
modules the canonical hash covers and are re-exported here, never redefined.

**What differs from v4r3.** Three things, and `protocol/revision.py`
enumerates all of them with their reasons: the class pool loses CP4 and CP7
(§7.0-R4), the measurement basis Gate 1 can write is the deterministic one
(§10.7), and `N_CLASS_FAMILIES` is derived from the pool instead of asserted.
Every other number here is v4r3's, carried unchanged, because v4r4 revises how
measurement validity is established and revises nothing about what the study
measures.
"""
from __future__ import annotations

# ------------------------------------------------------------- §6.2 topics
SUBJECT_AREAS = (
    "everyday science", "history", "geography", "food", "music", "sport",
    "work and organisations", "health and the body", "technology",
    "language and writing", "art and design", "the natural world",
)
TOPICS_PER_AREA = 52
PRESCREEN_PER_AREA = 2
SOLO_PER_AREA = 8
COMPOSED_PER_AREA = 2
#: §6.2, §16.2: 32, v4r2's split unchanged. An earlier v4r3 draft registered
#: 34 per area so that 408 blocks would meet every precision precondition at
#: M = 4. That allocation is **not executable**: the released bank holds 528
#: questions and the other 96 exist to this repository only as opaque
#: identities and content hashes (``dci1v4.topics.sequestered``), so the two
#: extra confirmatory topics per area could only come from text no v4-era
#: process can read. §16.2 reaches the same preconditions by raising M from 4
#: to 8 on v4r2's 384 blocks instead, which costs generations rather than the
#: sequestered set. §33 D1 records the finding.
CONFIRMATORY_PER_AREA = 32
SEQUESTERED_PER_AREA = (TOPICS_PER_AREA - PRESCREEN_PER_AREA - SOLO_PER_AREA
                        - COMPOSED_PER_AREA - CONFIRMATORY_PER_AREA)   # 8
MIN_SEQUESTERED_PER_AREA = 4

N_AREAS = len(SUBJECT_AREAS)
N_TOPICS = TOPICS_PER_AREA * N_AREAS                          # 624
N_PRESCREEN = PRESCREEN_PER_AREA * N_AREAS                    # 24
N_SOLO = SOLO_PER_AREA * N_AREAS                              # 96
N_COMPOSED = COMPOSED_PER_AREA * N_AREAS                      # 24
N_CONFIRMATORY = CONFIRMATORY_PER_AREA * N_AREAS              # 408
N_SEQUESTERED = SEQUESTERED_PER_AREA * N_AREAS                # 72
TOPIC_SETS = ("prescreen", "solo", "composed", "confirmatory", "sequestered")
SET_SIZES = {"prescreen": N_PRESCREEN, "solo": N_SOLO, "composed": N_COMPOSED,
             "confirmatory": N_CONFIRMATORY, "sequestered": N_SEQUESTERED}
assert sum(SET_SIZES.values()) == N_TOPICS

#: §12.5. The only topics any iterative or exploratory work may inspect.
DEVELOPMENT_TOPIC_SETS = ("prescreen", "solo")
RESERVED_TOPIC_SETS = ("composed", "confirmatory", "sequestered")

AUTHORING_RULES = (
    "answerable_from_general_knowledge",
    "no_single_correct_short_answer",
    "no_reused_public_dataset_or_examination_text",
    "no_form_requirement_in_the_question_text",
)

# ------------------------------ §7 grids, ladders, classes, vacuity threshold
from dci1v4r4.verifiers.compliance import (     # noqa: E402,F401
    NON_VACUITY_MIN_WORDS,
)
from dci1v4r4.verifiers.constraints import (    # noqa: E402,F401
    STATISTIC_IDS,
    FORMS,
    RATE_FORMS,
    LOWER_BOUND_FORMS,
    N_DECLARED_SEVERITIES,
    N_REFERENCE_SEVERITIES,
    N_CLASS_SEVERITIES,
    RESERVES,
    CLASS_BUDGET,
    CLASS_FAMILY_IDS,
    CLASS_LADDERS,
    CLASS_PRODUCTION,
    FAMILY_IDS,
    FOCAL_EXTENSION,
    FOCAL_GRID,
    KINDS,
    N_SEVERITIES,
    REFERENCE_FAMILY_IDS,
    REFERENCE_LADDERS,
    TARGET_GRID,
    TARGET_WORD,
)

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20     # §7.5: within 20% of A, not of B

# ---------------------------------------------------------------- §8 design
#: §8.1's arms. "core" is v4r2's five-constraint matrix unchanged.
CORE_SLOTS = ("A", "B", "R1", "R2", "R3")
#: §13.6: two straddling rungs per core reference family, one strictly
#: harder than A and one strictly easier.
SPECTRUM_SLOTS = ("R1-", "R1+", "R2-", "R2+", "R3-", "R3+")
CLASS_SLOT = "CL"
#: §8.4's registered slot order, which fixes which constituent is "first".
REGISTERED_SLOT_ORDER = CORE_SLOTS + SPECTRUM_SLOTS + (CLASS_SLOT,)

N_UNCONSTRAINED_CELLS = 1                                    # §8.1, §25
N_CORE_SOLO_CELLS = len(CORE_SLOTS)                          # 5
N_UNORDERED_CORE_PAIRS = 10
N_ORDERS = 2
N_CORE_COMPOSED_CELLS = N_UNORDERED_CORE_PAIRS * N_ORDERS    # 20
N_SPECTRUM_SOLO_CELLS = len(SPECTRUM_SLOTS)                  # 6
N_SPECTRUM_COMPOSED_CELLS = len(SPECTRUM_SLOTS) * N_ORDERS   # 12
N_CLASS_SOLO_CELLS = 1
N_CLASS_COMPOSED_CELLS = N_ORDERS                            # 2
N_CELLS_FULL = (N_UNCONSTRAINED_CELLS + N_CORE_SOLO_CELLS
                + N_CORE_COMPOSED_CELLS + N_SPECTRUM_SOLO_CELLS
                + N_SPECTRUM_COMPOSED_CELLS + N_CLASS_SOLO_CELLS
                + N_CLASS_COMPOSED_CELLS)                    # 47
#: §13.7: when no class severity is eligible the arm is dropped.
N_CELLS_FULL_NO_CLASS = N_CELLS_FULL - N_CLASS_SOLO_CELLS - N_CLASS_COMPOSED_CELLS
#: §8.6, §12.6: the core matrix intact and the spectrum arm dropped. What a
#: model runs when §13.4 admits three core references but §12.6's coverage
#: criterion fails: Delta_R, Xi, Lambda and the reciprocal matrix stay
#: identified and only delta_difficulty does not.
N_CELLS_NO_SPECTRUM = (N_CELLS_FULL - N_SPECTRUM_SOLO_CELLS
                       - N_SPECTRUM_COMPOSED_CELLS)                  # 29
N_CELLS_NO_SPECTRUM_NO_CLASS = (N_CELLS_NO_SPECTRUM - N_CLASS_SOLO_CELLS
                                - N_CLASS_COMPOSED_CELLS)            # 26
#: §8.6 reduced design: unconstrained, A solo, B solo, A+B in each order.
REDUCED_SLOTS = ("A", "B")
N_CELLS_REDUCED = 1 + 2 + 2                                  # 5
N_CELLS_REDUCED_NO_CLASS = N_CELLS_REDUCED
N_CELLS_REDUCED_WITH_CLASS = N_CELLS_REDUCED + 3             # 8

#: §11.1. A configuration is the POSITION OF THE OUTCOME CONSTRAINT, not the
#: registered slot order: only that reading makes a Delta-type quantity
#: position-clean, because it is what puts the outcome in the same position
#: in both cells being differenced.
OUTCOME_FIRST = "outcome_first"
OUTCOME_SECOND = "outcome_second"
CONFIGURATIONS = (OUTCOME_FIRST, OUTCOME_SECOND)

N_BLOCKS = N_CONFIRMATORY            # 384, §16.2
#: §8.2, §16.2. Eight, not v4r2's four. With the bank fixed at 384 accessible
#: confirmatory topics, M is the only lever left that meets every precision
#: precondition under phi = 0.37 once F1 carries six members; at M = 4 three
#: members project 0.0515 against a 0.05 precondition.
M_DRAWS = 8
M_CAL = 4                            # §12.3, §13.10
LADDER_SCREEN_DRAWS = 1              # §12.2
GREEDY_BLOCKS = 96                   # §8.3 sensitivity run
GREEDY_DRAWS = 1
GREEDY_TEMPERATURE = 0.0
PILOT_TOPICS = 12                    # §19
PILOT_DRAWS = 4

# ------------------------------------------------------- §8.5 prompt template
#: §8.5. Four parts, not v4r2's three. The stem is byte-identical in every
#: cell, is never scored, never enters a compliance vector and never counts
#: toward load. It is registered because §9.3's vacuity threshold rested on a
#: premise the v4r2 instrument never put to the model.
STEM_SENTENCE = "Answer in 60 to 120 words."
PROMPT_ZERO = "{question}\n\n" + STEM_SENTENCE + "\n\nAnswer:"
PROMPT_ONE = "{question}\n\n" + STEM_SENTENCE + "\n\n1. {c1}\n\nAnswer:"
PROMPT_TWO = ("{question}\n\n" + STEM_SENTENCE
              + "\n\n1. {c1}\n2. {c2}\n\nAnswer:")
#: §8.5's diagnostic band, recorded per row and per load. Gates nothing.
STEM_BAND = (60, 120)

# ------------------------------------------------------- §12 operating regime
COMPLETION_CAPS = (512, 768, 1024)
CAP_TRUNCATION_MAX = 0.10            # §12.1
CAP_SELECTION_PROMPTS = 96
CAP_SET_LOADS = (0, 1, 2)
TRUNCATION_BOUND_THRESHOLD = 0.10    # §12.1, §25

TARGET_BAND = (0.50, 0.85)           # §12.3, on RAW solo compliance
TARGET_AIM = 0.70
FOCAL_BAND = (0.60, 0.95)            # §12.3, on RAW solo compliance
FOCAL_AIM = 0.80
REGIME_VACUITY_MAX = 0.10            # §12.4 condition 2
#: §12.4 condition 3, read as a SHARE. v4r2 left the reading open and its code
#: fixed neither; read as a mean the clause fires on every severity §12.3
#: declares eligible, so §12.4 would contradict its own neighbour on every
#: model under every prompt. §33 D3 asks the researcher to confirm.
GRADED_DEGENERACY_HIGH = 0.99        # a graded score above this is "at ceiling"
GRADED_DEGENERACY_LOW = 0.01
GRADED_DEGENERACY_SHARE_MAX = 0.99   # ...and at most this share may be there
GRADED_CLAUSE_READING = "share"

#: §12.3's shortlist. Six reference families is twice the three the design
#: needs, so a family failing at calibration what it passed at pre-screen does
#: not by itself force the reduced design.
SHORTLIST_REFERENCE_FAMILIES = 6
SHORTLIST_MAX_PER_REFERENCE_FAMILY = 4
SHORTLIST_MAX_PER_CLASS_FAMILY = 2
#: Derived, not asserted. v4r3 carried this as the literal 4 while its pool
#: held six class families, so the registration record it fed disagreed with
#: the pool it described. §7.0-R4's removal makes the true count four; taking
#: it from the pool means the record cannot disagree with the pool again.
N_CLASS_FAMILIES = len(CLASS_FAMILY_IDS)

# ------------------------------------ §12.6 candidate library and coverage
#: §12.6. Expansion draws from the frozen reserve of §7.0 and from nowhere
#: else, at most this many rounds, at most this many new rungs per family per
#: round. Both numbers are registered before any measurement.
EXPANSION_MAX_ROUNDS = 2
EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND = 4
#: §12.6's identification-coverage criterion, evaluated on the §12.2
#: pre-screen table alone. Every number is either carried from an existing
#: registered rule or is the minimum the downstream rule needs.
COVERAGE_MIN_FAMILIES_PER_SIDE = 3        # §13.6 needs three straddling triples
COVERAGE_MIN_STRADDLING_FAMILIES = 4      # one spare, as §12.3's shortlist has
COVERAGE_NEAR_CALIPER = 0.15              # §13.4 condition 2's pre-screen value
COVERAGE_MIN_NEAR_RUNGS = 6
COVERAGE_MIN_NEAR_FAMILIES = 3
COVERAGE_MIN_ELIGIBLE_RUNGS = 12          # §13.6 delivers nine; twelve is a floor
COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY = 3
COVERAGE_MIN_WITHIN_FAMILY_SPAN = 2 * 0.20   # two registered spectrum offsets
#: §13.7. A class companion is *matched* when it is inside this caliper of A.
CLASS_MATCH_CALIPER = 0.15

# --------------------------- §13 difficulty, admission, spectrum, class arm
#: §13.3. The registered coordinate is instructed compliance; raw solo
#: compliance is computed alongside and reported, and §17.6 registers what a
#: disagreement between them means.
DIFFICULTY_COORDINATE = "instructed_compliance"
SECONDARY_DIFFICULTY_COORDINATE = "raw_solo_compliance"

REFERENCE_CALIPER = 0.10             # §13.4 condition 1, on iota
REFERENCE_NEWCOMBE_REGION = 0.05     # §13.4 condition 1
REFERENCE_PRESCREEN_CALIPER = 0.15   # §13.4 condition 2, disjoint pre-screen
REFERENCE_VACUITY_MAX = 0.10         # §13.4 condition 6
REALISED_GAP_QUALIFIER = 0.15        # §13.4, §28.1
N_CORE_REFERENCES = 3
#: §13.5. The floor is the registered smallest effect of interest: a
#: constraint whose stating changes compliance by less than that is not
#: distinguishable from an absent instruction. The ceiling is §12.3's focal
#: band maximum. Neither number is new to v4r3.
SPECTRUM_ELIGIBILITY_BAND = (0.10, 0.95)
#: §13.6. Symmetric, so the fit is centred on A: a centred fit is the one
#: whose prediction at A carries least leverage (§16.1).
SPECTRUM_OFFSET = 0.20
N_SPECTRUM_PER_FAMILY = 2
N_SPECTRUM_COMPANIONS = N_CORE_REFERENCES * N_SPECTRUM_PER_FAMILY   # 6
N_FIT_POINTS = N_CORE_REFERENCES * (1 + N_SPECTRUM_PER_FAMILY)      # 9
#: §11.2: iota is undefined at kappa = 1; at or above this the point is
#: dropped from the fit and DIFFICULTY_COORDINATE_DEGENERATE is recorded.
CHANCE_DEGENERACY_MAX = 0.99

#: §13.8's support rule.
SUPPORT_MIN_BELOW = 2
SUPPORT_MIN_ABOVE = 2
SUPPORT_MIN_FAMILIES_PER_SIDE = 2
SUPPORT_BOOTSTRAP_SHARE_MIN = 0.95
DEGENERATE_REPLICATE_MAX = 0.01

COMPOSED_HEADROOM_BAND = (0.05, 0.95)   # §13.10

# ------------------------------------------------------ §16 variance and menu
P_ONE_MINUS_P = 0.215
PHI_PRIMARY = 0.27
PHI_ALTERNATE = 0.37
RHO = 0.5
#: §16.1. Conservative: five times the largest slope magnitude any
#: non-confirmatory screen produced, on five points with no interval attached.
#: It enters the projection and nothing else (§16.5).
BETA_PLANNING = 0.5
#: §16.1. 1/9 for a fit centred on A, plus a leverage allowance for realised
#: rungs that miss their targets by up to 0.05 with Sxx from three families
#: straddling by the registered offset.
SUM_W_SQUARED_PLANNING = 1.0 / 9.0 + 0.05 ** 2 / (3 * 2 * SPECTRUM_OFFSET ** 2)

#: §16.3. Every entry is a whole number of confirmatory topics per area.
ALLOCATION_MENU = (
    {"blocks": 384, "M": 4}, {"blocks": 384, "M": 8},
    {"blocks": 408, "M": 4}, {"blocks": 408, "M": 8},
    {"blocks": 432, "M": 4}, {"blocks": 456, "M": 4},
)
SIDAK_K3 = 2.3877
SIDAK_K4 = 2.4909
SIDAK_K6 = 2.6310
SIDAK_K9 = 2.7729
SIDAK_K10 = 2.8070
SIDAK_K11 = 2.8377

# ---------------------------------------------- §11.8 thresholds and regions
DELTA_R_GENERIC_THRESHOLD = 0.10
DELTA_R_PAIR_SPECIFIC_THRESHOLD = 0.25
SMALLEST_EFFECT_OF_INTEREST = 0.10
EQUIVALENCE_REGION = 0.10
#: §11.8. delta_difficulty licenses a DIRECTION claim and an EQUIVALENCE claim
#: against the registered smallest effect of interest, and no pair-specific
#: claim at any magnitude. The memo's 0.25 is defined for a different
#: quantity and is deliberately not transferred; §33 D5 is the decision.
DELTA_DIFFICULTY_THRESHOLDS = {"direction": 0.0,
                               "equivalence": EQUIVALENCE_REGION}
#: Xi is a direction-only gate (§11.6, §3.2) and has no magnitude threshold.
XI_HAS_MAGNITUDE_THRESHOLD = False
PRECISION_PRECONDITIONS = {"D": 0.05, "Delta_R": 0.05,
                           "delta_difficulty": 0.05,
                           "Lambda": 0.08, "Delta_j": 0.06}

# ---------------------------------------------------------- §15 families
FAMILY_MEMBERS: dict[str, tuple[str, ...]] = {
    "F1": ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "delta_difficulty",
           "Xi"),
    "F2": ("D(B<-R1)", "D(B<-R2)", "D(B<-R3)",
           "Delta_1", "Delta_2", "Delta_3"),
    "F3": ("D(A<-R1)", "D(A<-R2)", "D(A<-R3)", "Delta^A"),
    "F4": ("D(Rbar<-A)", "D(Rbar<-B)", "D(Rbar<-Rbar')"),
    "F5": ("D(B<-A)|vacuity_forced", "D(A<-B)|vacuity_forced",
           "Lambda|vacuity_forced", "Delta_R|vacuity_forced",
           "delta_difficulty|vacuity_forced", "Xi|vacuity_forced",
           "D(B<-A)|graded_0.99", "Delta_R|graded_0.99",
           "delta_difficulty|graded_0.99"),
    "F6": ("vac(B|A+B)-vac(B solo)",
           "vac(B|B+R1)-vac(B solo)", "vac(B|B+R2)-vac(B solo)",
           "vac(B|B+R3)-vac(B solo)",
           "vac(B|B+R1-)-vac(B solo)", "vac(B|B+R1+)-vac(B solo)",
           "vac(B|B+R2-)-vac(B solo)", "vac(B|B+R2+)-vac(B solo)",
           "vac(B|B+R3-)-vac(B solo)", "vac(B|B+R3+)-vac(B solo)",
           "vac(B|B+CL)-vac(B solo)"),
    "F7": ("D(R1<-B)", "D(R2<-B)", "D(R3<-B)",
           "D(R1<-A)", "D(R2<-A)", "D(R3<-A)"),
    "F8": ("D(B<-R1-)", "D(B<-R1+)", "D(B<-R2-)", "D(B<-R2+)",
           "D(B<-R3-)", "D(B<-R3+)",
           "beta", "alpha_1", "alpha_2", "alpha_3"),
    "F9": ("D(B<-CL)", "Delta_class"),
}
PRIMARY_FAMILY = "F1"
BOOTSTRAP_RESAMPLES = 10_000         # §17.1
F6_VACUITY_GATE = 0.05               # §17.4
GRADED_ROBUSTNESS_THRESHOLD = 0.99   # §15 F5

# ------------------------------------------------------------ §3 claim ladder
CLAIM_LEVELS = ("L1", "L2", "L3a", "L3b", "L3c", "L3d", "L3e", "L4", "L5")
WITHHELD_CLAIM_LEVELS = ("L5",)
#: §10.5. The bases an analysis record may declare. v4r4's Gate 1 writes
#: exactly one of them, and it is not the first: see `MEASUREMENT_BASIS`.
#: The reviewer-derived bases stay legal *labels* because v4r3's preserved
#: records carry them and a reader must be able to place one; no v4r4 stage
#: can write either.
MEASUREMENT_BASES = ("human_validated", "autorater_calibration_approved",
                     "human_validation_unavailable",
                     "deterministic_measurement_validated")
#: §10.7. The **native** v4r4 measurement basis, written by a Gate 1 that
#: passed the deterministic-measurement architecture (A-E). It is not
#: `human_validated`, so `SCOPE_SENTENCE` attaches under it permanently and no
#: later stage may remove it: v4r4's criterion buys the study its execution,
#: not a stronger claim.
MEASUREMENT_BASIS = "deterministic_measurement_validated"
#: The bases a v4r4 Gate 1 refuses to write. `human_validated` is here because
#: v4r4 never establishes it: §10.5's second question is unanswered under this
#: revision exactly as it was under v4r3.
MEASUREMENT_BASES_REFUSED = ("human_validated",
                             "autorater_calibration_approved",
                             "human_validation_unavailable")
SCOPE_SENTENCE = ("the outcomes are verifier-defined and support no claim "
                  "about compliance as an independent human would judge it")
TERMINAL_SENTENCE = ("a terminal pre-confirmatory status carries no evidence "
                     "about the effect")
POSITION_WORDING = "composition and position change together"
#: §28.2, attached verbatim to every L3 statement at every sub-level.
CLASS_SENTENCE = (
    "the reference pool is budget class and A is production class, so this "
    "excess is relative to budget-class companions matched on instructed "
    "compliance and is not an excess relative to companions of A's own "
    "structural class")

# ------------------------------------------- §10.3, §10.4: DIAGNOSTIC ONLY
#: Retained so that v4r3's preserved reviewer artifacts stay readable and so
#: that a v4r4 diagnostic run reproduces their arithmetic. **No v4r4 gate
#: reads either number.** §10.7 replaced the reviewer-agreement criterion, and
#: `stages/gate1.py` refuses a payload that offers a reviewer quantity as a
#: criterion input.
HUMAN_DISAGREEMENT_MAX = 0.10
HUMAN_SAMPLE_CAP = 150
VERIFIER_CLASSES = ("pass", "fail")
FAIL_CLASS_STRATA = ("margin_one", "margin_larger")
BOUNDARY_SUITE_MIN_CASES = 40
DETERMINISM_PROCESSES = 3

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
GENERATION_STAGES = (STAGE_GATE0, STAGE_REGIME, STAGE_GATE2, STAGE_GATE4,
                     STAGE_CONFIRMATORY)
#: §10.6. Thirteen entry points: v4r2's eleven plus the two the spectrum and
#: the class arm add.
VERIFIER_BOUND_ENTRY_POINTS = (
    "ladder_screen", "solo_calibration", "reference_admission",
    "spectrum_selection", "class_admission", "composed_headroom", "freeze",
    "confirmatory_generation", "scoring", "resume_restart", "analysis",
    "unmasking", "report_generation",
)

# ------------------------------------------------------------ §28 statuses
TERMINAL_STATUSES = (
    "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
    "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
    "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
    "REGIME_NOT_FOUND", "COMPOSED_HEADROOM_FAILURE",
    "MEASUREMENT_NOT_ESTABLISHED", "MEASUREMENT_EVIDENCE_INSUFFICIENT",
    # §10.7: the prose of a family does not pin down its predicate. A
    # distinct status because it is a defect in the *specification*, which no
    # amount of implementation evidence can repair. Native to v4r4's Gate 1.
    "SPECIFICATION_AMBIGUOUS",
)
IDENTIFICATION_STATUSES = (
    "EXCESS_NOT_IDENTIFIED", "DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
    "CANDIDATE_RESERVE_EXHAUSTED", "CLASS_ARM_NOT_MATCHED",
    "DIFFICULTY_SUPPORT_MARGINAL", "A_GENERAL_NOT_EXCLUDED",
    "LOCAL_AND_SPECTRUM_DISAGREE", "DIFFICULTY_COORDINATE_DEPENDENT",
    "DIFFICULTY_COORDINATE_DEGENERATE", "COMPANION_CLASS_NOT_MATCHED",
    "CLASS_ARM_NOT_AVAILABLE", "POSITION_CONFOUNDED",
    "HUMAN_VALIDATION_UNAVAILABLE",
)
RESULT_MARKERS = ("INSUFFICIENT_PRECISION", "INDETERMINATE")
#: Correct HISTORICAL labels for earlier terminations. v4r3 never EMITS them.
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
MASK_MIN_DIFFERING_FRACTION = 0.5

# ------------------------------------------- §14.2 missingness / duplicates
MISSINGNESS_REPORT_THRESHOLD = 0.01
DUPLICATE_QUALIFICATION_MAX = 0.05

# --------------------------------------------------------------- §22 mediator
POST_TREATMENT_FIELDS = (
    "word_count", "token_count", "truncated", "finish_reason", "graded",
    "vacuous_pass", "non_vacuous", "joint_state", "response_length_words",
    "processing_failure", "in_stem_band",
)
#: §22. kappa is pre-treatment FOR THE COMPANION -- it is measured where the
#: companion is absent -- so it may enter the difficulty coordinate. It is
#: post-treatment for the topic, so it may never be a covariate on the
#: outcome, a block weight, or a selection criterion.
CHANCE_FIELDS = ("chance_compliance", "instructed_compliance",
                 "instruction_lift")
CAUSAL_ROLES = ("identity", "treatment", "design", "outcome",
                "post-treatment", "provenance", "difficulty-coordinate")

# ------------------------------------------------------------- §9.2 S-rules
EXACT_COUNT_RULES = ("S0", "S1", "S2", "S3")
PRIMARY_EXACT_COUNT_RULE = "S0"

# -------------------------------------------------------- §23 failure taxonomy
FAILURE_TAXONOMY = ("empty", "cut_off", "refusal", "restatement",
                    "target_inside_longer_word", "zero_occurrences",
                    "too_few", "too_many", "other")
FAILURE_MARGIN_STRATA = ("margin_one", "margin_larger")
