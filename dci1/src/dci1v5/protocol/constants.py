"""Every registered v5 value, in one place (preregistration v5).

Where the preregistration gives a number this module gives that number and
cites the section. Values that adapt by model (§6.1's cross-replication
firewall) are **not** here: they live on the per-model gate records and reach
the code only through them.

Grids, ladders, tiers, classes and the non-vacuity threshold are verifier
*semantics* --- they decide what a verifier returns --- so they live inside
the modules the canonical hash covers and are re-exported here, never
redefined.

**Nothing in this module is binding yet.** §34's nineteen decisions are open
and ``protocol/decisions.py`` blocks every stage that depends on one. A
threshold here is the preregistration's proposed value: it becomes registered
when the signed registration manifest binds it, and ``assert_binding()`` says
so where a caller might forget.

**What differs from v4r4's constants, and why each moved.** The new §13
thresholds are in this file with their derivations beside them;
``protocol/revision.py`` enumerates every change against its section.
``REFERENCE_PRESCREEN_CALIPER`` is **removed** --- §12.2 deletes the rule that
read it --- and ``CHANCE_DEGENERACY_MAX`` is **retained at 0.99 and is no
longer an admission threshold**: §11.2 keeps it as the point at which iota is
undefined, and §13.4's ceiling of 0.75 is what decides admission.

**One v4r4 defect is not repeated.** v4r4's comments disagreed with its
computed values --- ``N_SEVERITIES`` documented 190 against a computed 254,
``N_DECLARED_SEVERITIES`` 334 against 510, ``N_CONFIRMATORY`` 408 against 384,
``N_SEQUESTERED`` 72 against 96. The computed values are what that code used
and what its records carry, so nothing scientific moved and no v4r4 number is
wrong; the comments were. Here every derived count is asserted.
"""
from __future__ import annotations

# ------------------------------------------------------------- §6.2 topics
SUBJECT_AREAS = (
    "everyday science", "history", "geography", "food", "music", "sport",
    "work and organisations", "health and the body", "technology",
    "language and writing", "art and design", "the natural world",
)
N_AREAS = len(SUBJECT_AREAS)
#: §6.2: the v4 bank of 624 plus 96 newly authored questions, 8 per area.
#: The 96 are §34 D3 and do not exist yet.
TOPICS_PER_AREA = 60
PRESCREEN_PER_AREA = 2
CALIBRATION_A_PER_AREA = 8
CALIBRATION_B_PER_AREA = 8
COMPOSED_PER_AREA = 2
CONFIRMATORY_PER_AREA = 32
SEQUESTERED_PER_AREA = (TOPICS_PER_AREA - PRESCREEN_PER_AREA
                        - CALIBRATION_A_PER_AREA - CALIBRATION_B_PER_AREA
                        - COMPOSED_PER_AREA - CONFIRMATORY_PER_AREA)   # 8

N_TOPICS = TOPICS_PER_AREA * N_AREAS                          # 720
N_PRESCREEN = PRESCREEN_PER_AREA * N_AREAS                    # 24
N_CALIBRATION_A = CALIBRATION_A_PER_AREA * N_AREAS            # 96
N_CALIBRATION_B = CALIBRATION_B_PER_AREA * N_AREAS            # 96
N_CALIBRATION = N_CALIBRATION_A + N_CALIBRATION_B             # 192
N_COMPOSED = COMPOSED_PER_AREA * N_AREAS                      # 24
N_CONFIRMATORY = CONFIRMATORY_PER_AREA * N_AREAS              # 384
N_SEQUESTERED = SEQUESTERED_PER_AREA * N_AREAS                # 96
#: §6.2's newly authored half. It is Calibration-B in full.
N_NEWLY_AUTHORED = N_CALIBRATION_B

CALIBRATION_A = "calibration_a"
CALIBRATION_B = "calibration_b"
TOPIC_SETS = ("prescreen", CALIBRATION_A, CALIBRATION_B, "composed",
              "confirmatory", "sequestered")
SET_SIZES = {"prescreen": N_PRESCREEN, CALIBRATION_A: N_CALIBRATION_A,
             CALIBRATION_B: N_CALIBRATION_B, "composed": N_COMPOSED,
             "confirmatory": N_CONFIRMATORY, "sequestered": N_SEQUESTERED}
assert sum(SET_SIZES.values()) == N_TOPICS == 720
assert N_CALIBRATION == 192

#: §12.5. The only topics any iterative or exploratory work may inspect.
DEVELOPMENT_TOPIC_SETS = ("prescreen", CALIBRATION_A, CALIBRATION_B)
RESERVED_TOPIC_SETS = ("composed", "confirmatory", "sequestered")

AUTHORING_RULES = (
    "answerable_from_general_knowledge",
    "no_single_correct_short_answer",
    "no_reused_public_dataset_or_examination_text",
    "no_form_requirement_in_the_question_text",
)

# ------------------------- §7 grids, ladders, tiers, vacuity threshold
from dci1v5.verifiers.compliance import (     # noqa: E402,F401
    NON_VACUITY_MIN_WORDS, STEM_BAND,
)
from dci1v5.verifiers.constraints import (    # noqa: E402,F401
    CLASS_BUDGET, CLASS_PRODUCTION, FAMILY_IDS, FOCAL_EXTENSION, FOCAL_GRID,
    FORMS, KINDS, LADDERS, LOWER_BOUND_FORMS, MARKER_MAX_LETTERS,
    MARKER_NATURAL_FREQUENCY_MAX, MARKER_WORDS, N_DECLARED_SEVERITIES,
    N_FAMILIES, N_INSTRUMENTS, N_SEVERITIES, N_VERIFIERS, RATE_FORMS,
    RESERVES, STATISTIC_IDS, TARGET_GRID, TARGET_WORD, TIER1_FAMILY_IDS,
    TIER2_FAMILY_IDS, TIER3_FAMILY_IDS,
)
from dci1v5.protocol.taxonomy import (        # noqa: E402,F401
    DISCOURSE_ROLES, METADATA_FIELDS, SLOT_BROAD_CLASS, SLOT_CORE,
    SLOT_NEAR_FORM, SLOT_SPECTRUM, SLOTS, TIERS,
)

N_WORDINGS = 4
WORDING_LENGTH_TOLERANCE = 0.20     # §7.7: within 20% of A, not of B
#: §7.6. A's own declared discourse role; §13.8 records
#: REFERENCE_ROLE_NOT_MATCHED when no core reference shares it.
A_DISCOURSE_ROLE = "contrastive"

# ---------------------------------------------------------------- §8 design
#: §8.1's arms. The base arm is always present; every other arm is admitted
#: independently by §13 and the cell count is **derived** from the admitted
#: set. v4r4's named full/no-spectrum/reduced variants and its
#: VARIANT_EXEMPTIONS patch are gone.
ARM_BASE = "base"
ARM_CORE = "core"
ARM_SPECTRUM = "spectrum"
ARM_NEAR_FORM = "nearform"
ARM_CLASS = "class"
OPTIONAL_ARMS = (ARM_CORE, ARM_SPECTRUM, ARM_NEAR_FORM, ARM_CLASS)
ARMS = (ARM_BASE,) + OPTIONAL_ARMS

BASE_SLOTS = ("A", "B")
CORE_SLOTS = ("R1", "R2", "R3")
SPECTRUM_SLOTS = ("R1-", "R1+", "R2-", "R2+", "R3-", "R3+")
NEAR_FORM_SLOTS = ("N1", "N2", "N3")
CLASS_SLOT = "CL"
#: §8.4's registered slot order, which fixes which constituent is "first".
REGISTERED_SLOT_ORDER = (BASE_SLOTS + CORE_SLOTS + SPECTRUM_SLOTS
                         + NEAR_FORM_SLOTS + (CLASS_SLOT,))

#: §8.1's derived counts, asserted in `design/cells.py` against the cell set
#: the arms actually build rather than defined here.
N_CELLS_BY_ARM = {ARM_BASE: 5, ARM_CORE: 21, ARM_SPECTRUM: 18,
                  ARM_NEAR_FORM: 9, ARM_CLASS: 3}
N_CELLS_FULL = sum(N_CELLS_BY_ARM.values())                    # 56
assert N_CELLS_FULL == 56

#: §11.1. A configuration is the POSITION OF THE OUTCOME CONSTRAINT, not the
#: registered slot order: only that reading makes a Delta-type quantity
#: position-clean.
OUTCOME_FIRST = "outcome_first"
OUTCOME_SECOND = "outcome_second"
CONFIGURATIONS = (OUTCOME_FIRST, OUTCOME_SECOND)

N_BLOCKS = N_CONFIRMATORY            # 384, §16.2
M_DRAWS = 8                          # §8.2, §16.2
M_CAL = 4                            # §12.3, §13.7, §13.14
LADDER_SCREEN_DRAWS = 1              # §12.2
GREEDY_BLOCKS = 96                   # §8.3 sensitivity run
GREEDY_DRAWS = 1
GREEDY_TEMPERATURE = 0.0
PILOT_TOPICS = 12                    # §19
PILOT_DRAWS = 4

# ------------------------------------------------------- §8.5 prompt template
STEM_SENTENCE = "Answer in 60 to 120 words."
PROMPT_ZERO = "{question}\n\n" + STEM_SENTENCE + "\n\nAnswer:"
PROMPT_ONE = "{question}\n\n" + STEM_SENTENCE + "\n\n1. {c1}\n\nAnswer:"
PROMPT_TWO = ("{question}\n\n" + STEM_SENTENCE
              + "\n\n1. {c1}\n2. {c2}\n\nAnswer:")

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
GRADED_DEGENERACY_HIGH = 0.99
GRADED_DEGENERACY_LOW = 0.01
GRADED_DEGENERACY_SHARE_MAX = 0.99
GRADED_CLAUSE_READING = "share"

#: §12.2's high-recall screen. Rule 1's Wilson interval for raw solo
#: compliance must intersect this band; rule 2 carries **every** Tier-1 and
#: Tier-2 rung unconditionally. There is no pre-screen distance caliper:
#: v4r4's is deleted, because the two stages' iota estimates disagree by a
#: median of 0.071 and 35.7% of candidates move further between them than the
#: whole width of the caliper they then have to clear.
PRESCREEN_RETENTION_BAND = (0.05, 0.95)
#: §12.7's calibration budget. Calibration-A measures all 88 Tier-1/Tier-2
#: rungs plus at most this many Tier-3 rungs, ordered by ascending pre-screen
#: |iota - iota_A| when more are carried. That ordering is the one place a
#: pre-screen point estimate still decides anything, and it decides only
#: which Tier-3 rungs are *measured*, never admission.
CALIBRATION_TIER3_CAP = 24

# ------------------------------------ §12.6 candidate expansion and coverage
EXPANSION_MAX_ROUNDS = 2
EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND = 4
#: §12.6's identification-coverage criterion. C1-C6 are decisive for the core
#: and spectrum arms; C7 and C8 are not --- failing them drops the
#: broad-class and near-form arms with their own statuses and stops nothing.
COVERAGE_MIN_FAMILIES_PER_SIDE = 3            # C2
COVERAGE_NEAR_CALIPER = 0.15                  # C3, C7
COVERAGE_MIN_NEAR_RUNGS = 8                   # C3   (v4r4: 6)
COVERAGE_MIN_NEAR_FAMILIES = 4                # C3   (v4r4: 3)
COVERAGE_MIN_STRADDLING_FAMILIES = 6          # C4   (v4r4: 4)
COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY = 3  # C4
COVERAGE_MIN_WITHIN_FAMILY_SPAN = 0.40        # C4, two spectrum offsets
COVERAGE_MIN_ELIGIBLE_RUNGS = 16              # C5   (v4r4: 12)
COVERAGE_MIN_TIER12_FAMILIES = 8              # C6   new
COVERAGE_MIN_TIER12_GROUPS = 6                # C6   new
COVERAGE_MIN_TIER2_RUNGS = 3                  # C8   new
COVERAGE_CONDITIONS = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8")
COVERAGE_DECISIVE = ("C1", "C2", "C3", "C4", "C5", "C6")

# --------------------------- §13 validity, admission, spectrum, support
DIFFICULTY_COORDINATE = "instructed_compliance"
SECONDARY_DIFFICULTY_COORDINATE = "raw_solo_compliance"

#: §13.1's eight components, in the registered **lexicographic** order. The
#: order decides which rejection reason is recorded, never which candidates
#: pass: a conjunction's truth value does not depend on evaluation order.
VALIDITY_COMPONENTS = ("V_spec", "V_sat", "V_head", "V_chance", "V_struct",
                       "V_inter", "V_stab", "V_diff")

# §13.4 --- raw compliance rules, evaluated BEFORE the difficulty caliper
#: The band is §13.14's composed-headroom band (0.05, 0.95) contracted by
#: 0.05 on each side, applied to the **interval** and not the point, so an
#: imprecisely measured candidate cannot sit on the boundary.
HEADROOM_BAND = (0.10, 0.90)
#: D(R <- B) <= H_R. The registered smallest effect of interest is 0.10, so a
#: reference with H < 0.20 cannot exhibit a reciprocal loss of two SESOI
#: however the model behaves, and F7 would be bounded by the design.
INSTRUCTION_LIFT_MIN = 0.20
REFERENCE_VACUITY_MAX = 0.10
#: iota's sampling variance carries a 1/(1-kappa) amplification: 4 at 0.75,
#: 10 at 0.90. The measured split-half |Delta iota| rises from 0.044 for
#: chance-free candidates through 0.110 in [0.25, 0.75) to 0.195 at >= 0.75.
CHANCE_MAX = 0.75
CHANCE_WILSON_UPPER_MAX = 0.85
#: §11.2, retained from v4r4 and **no longer an admission threshold**: the
#: point at which iota is undefined and DIFFICULTY_COORDINATE_DEGENERATE is
#: recorded.
CHANCE_DEGENERACY_MAX = 0.99

# §13.6 --- the interaction rule
#: §13.14's band contracted by one registered projection-error allowance of
#: 0.05 on each side. The allowance is §16.2's precision precondition for D,
#: and is close to the realised median absolute projection error of 0.067
#: measured on the one v4r4 replication that ever composed a reference with B.
PROJECTED_COMPLIANCE_BAND = (0.10, 0.90)
PROJECTION_ERROR_ALLOWANCE = 0.05
#: Catches the FLOOR direction, which the projection does not: on qwen3-4b,
#: CL7:30 moved from kappa 0.849 to kappa(R|B) 0.122.
DISPLACEMENT_MAX = 0.25

# §13.7 --- two independent calibration splits
#: Twice the registered matching caliper. A coordinate that cannot be pinned
#: to twice the caliper across two independent 96-topic splits cannot support
#: matching at the caliper. It is an EQUIVALENCE bound and not a threshold on
#: the point difference, because a threshold on the point rewards an
#: imprecisely measured candidate.
STABILITY_EQUIVALENCE_BOUND = 0.20
STABILITY_BOOTSTRAP_RESAMPLES = 10_000

# §13.8 --- the difficulty caliper and core admission
#: Unchanged from v4r4 **deliberately**. The paired standard error of iota
#: over 192 topics at M_cal = 4 is about 0.034, so 0.10 is about 2.96 SE
#: where v4r4's was 2.10. What changed is the sample, not the number:
#: tightening the caliper would select harder on a coordinate whose error is
#: the size of the window.
REFERENCE_CALIPER = 0.10
REFERENCE_NEWCOMBE_REGION = 0.05
#: §13.8 condition 3, new: the secondary coordinate is meaningful inside a
#: same-form, same-class pool and is roughly 1.5 times more stable than iota.
#: A check on the primary, never the selector.
SECONDARY_COORDINATE_CALIPER = 0.15
#: §13.8's realised qualifiers, measured on the confirmatory data.
REALISED_GAP_QUALIFIER = 0.15
INTERACTION_DRIFT_MAX = 0.15

# §13.12 --- the spectrum
SPECTRUM_ELIGIBILITY_BAND = (0.10, 0.95)
SPECTRUM_OFFSET = 0.20
N_SPECTRUM_PER_FAMILY = 2

# §13.9 / §13.10 --- the near-form and broad-class arms
N_NEAR_FORM_CONTROLS = 3
CLASS_MATCH_CALIPER = 0.15

# §13.13 --- difficulty support on the confirmatory data
SUPPORT_MIN_BELOW = 2
SUPPORT_MIN_ABOVE = 2
SUPPORT_MIN_FAMILIES_PER_SIDE = 2
SUPPORT_BOOTSTRAP_SHARE_MIN = 0.95
DEGENERATE_REPLICATE_MAX = 0.01

# §13.15 --- support oversupply and the frozen backups
MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES = 8
MIN_QUALIFIED_FAMILIES = 5
N_CORE_REFERENCES = 3
MIN_TIER1_CORE = 2
N_CORE_FEATURE_GROUPS = 3
MIN_CORE_DISCOURSE_ROLES = 2
N_BACKUP_FAMILIES = 2
#: §13.14: a frozen backup is **never** substituted into an admitted slot
#: after Gate 4. The constant exists so the freeze record can carry the
#: statement; the guarantee is that no substitution function exists.
BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 = False

N_SPECTRUM_COMPANIONS = N_CORE_REFERENCES * N_SPECTRUM_PER_FAMILY   # 6
N_FIT_POINTS = N_CORE_REFERENCES * (1 + N_SPECTRUM_PER_FAMILY)      # 9
N_TIER_FIT_POINTS = N_FIT_POINTS + N_NEAR_FORM_CONTROLS             # 12

COMPOSED_HEADROOM_BAND = (0.05, 0.95)   # §13.14

# ------------------------------------------------------ §16 variance and menu
P_ONE_MINUS_P = 0.215
PHI_PRIMARY = 0.27
PHI_ALTERNATE = 0.37
RHO = 0.5
BETA_PLANNING = 0.5
SUM_W_SQUARED_PLANNING = 1.0 / 9.0 + 0.05 ** 2 / (3 * 2 * SPECTRUM_OFFSET ** 2)
SIDAK_K2 = 2.2414
SIDAK_K3 = 2.3877
SIDAK_K4 = 2.4909
SIDAK_K5 = 2.5697
SIDAK_K6 = 2.6310
SIDAK_K9 = 2.7729
SIDAK_K11 = 2.8377
SIDAK_K14 = 2.9134

# ---------------------------------------------- §11.9 thresholds and regions
DELTA_R_GENERIC_THRESHOLD = 0.10
DELTA_R_PAIR_SPECIFIC_THRESHOLD = 0.25
SMALLEST_EFFECT_OF_INTEREST = 0.10
EQUIVALENCE_REGION = 0.10
#: §11.9: the memo's 0.25 is defined for a matched-reference contrast and is
#: transferred to neither delta_difficulty, Delta_near, Delta_broad nor any
#: order contrast. §34 D12 and D15 are the decisions.
DELTA_NEAR_THRESHOLDS = {"direction": 0.0,
                         "generic": DELTA_R_GENERIC_THRESHOLD}
DELTA_BROAD_THRESHOLDS = {"direction": 0.0}
DELTA_DIFFICULTY_THRESHOLDS = {"direction": 0.0,
                               "equivalence": EQUIVALENCE_REGION}
ORDER_THRESHOLDS = {"direction": 0.0, "equivalence": EQUIVALENCE_REGION}
XI_HAS_MAGNITUDE_THRESHOLD = False
PRECISION_PRECONDITIONS = {"D": 0.05, "Delta_R": 0.05, "Delta_near": 0.05,
                           "delta_difficulty": 0.05, "Lambda": 0.08,
                           "Delta_j": 0.06, "Ord_A": 0.05, "Ord_B": 0.05,
                           "Ord_Lambda": 0.08}

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
           "vac(B|B+N1)-vac(B solo)", "vac(B|B+N2)-vac(B solo)",
           "vac(B|B+N3)-vac(B solo)", "vac(B|B+CL)-vac(B solo)"),
    "F7": ("D(R1<-B)", "D(R2<-B)", "D(R3<-B)",
           "D(R1<-A)", "D(R2<-A)", "D(R3<-A)"),
    "F8": ("D(B<-R1-)", "D(B<-R1+)", "D(B<-R2-)", "D(B<-R2+)",
           "D(B<-R3-)", "D(B<-R3+)",
           "beta", "alpha_1", "alpha_2", "alpha_3", "gamma_tier"),
    "F9": ("D(B<-N1)", "D(B<-N2)", "D(B<-N3)", "Delta_near"),
    "F10": ("D(B<-CL)", "Delta_broad"),
    #: §11.7, §15. The one family declared ACROSS configurations, because its
    #: members are cross-configuration contrasts. Primary tier: it licenses a
    #: claim level, so it carries a simultaneous interval and a precision
    #: precondition. Ord_Lambda = Ord_B - Ord_A exactly, and §11.7 declares
    #: the dependence rather than hiding it.
    "F11": ("Ord_A", "Ord_B", "Ord_Lambda", "Ord_Rbar", "Ord_CL"),
}
PRIMARY_FAMILY = "F1"
#: Families whose interval licenses a claim level. F11 is primary tier
#: despite not being in F1 (§34 D13).
PRIMARY_TIER_FAMILIES = ("F1", "F11")
CROSS_CONFIGURATION_FAMILIES = ("F11",)
BOOTSTRAP_RESAMPLES = 10_000         # §17.1
F6_VACUITY_GATE = 0.05               # §17.4
GRADED_ROBUSTNESS_THRESHOLD = 0.99   # §15 F5
ALGEBRAIC_FORM_TOLERANCE = 1e-9      # §11.7, §11.8

# ------------------------------------------------------------ §3 claim ladder
CLAIM_LEVELS = ("L1", "L2", "L3a", "L3b", "L3c", "L3d", "L3e", "L4a", "L4b",
                "L5")
WITHHELD_CLAIM_LEVELS = ("L5",)
MEASUREMENT_BASES = ("human_validated", "autorater_calibration_approved",
                     "human_validation_unavailable",
                     "deterministic_measurement_validated")
MEASUREMENT_BASIS = "deterministic_measurement_validated"
MEASUREMENT_BASES_REFUSED = ("human_validated",
                             "autorater_calibration_approved",
                             "human_validation_unavailable")
SCOPE_SENTENCE = ("the outcomes are verifier-defined and support no claim "
                  "about compliance as an independent human would judge it")
TERMINAL_SENTENCE = ("a terminal pre-confirmatory status carries no evidence "
                     "about the effect")
POSITION_WORDING = "composition and position change together"
#: §28.2, attached verbatim to every L3 statement. v5's analogue of v4r4's
#: CLASS_SENTENCE, pointing the **opposite** way: v4r4's reference pool was
#: budget class where A is production, so its excess was relative to
#: companions of a different class; v5's core pool is same-form by
#: construction, so its excess is relative to companions that are very like A.
REFERENCE_POOL_SAME_FORM_SENTENCE = (
    "the core reference pool is same-form with A --- an exact count of a "
    "marker word, differing only in which word and how many --- so this "
    "excess is an excess relative to companions that share A's predicate "
    "form and is not an excess relative to companions in general")
#: §28.2, retained and attached only to statements about Delta_broad.
CLASS_SENTENCE = (
    "the broad-class control is budget class where A is production, so this "
    "comparison bounds how much the companion's structural class could "
    "matter and does not estimate a class effect")
#: §17.6: an L3c emitted without the near-form arm carries this verbatim,
#: because L3c is the source memo's refutation verdict and v5's core pool is
#: chosen to resemble A. §34 D18 records whether the arm should instead be a
#: precondition of emitting L3c at all.
L3C_WITHOUT_NEAR_FORM_SENTENCE = (
    "the local excess is below the generic-load threshold against companions "
    "that share A's predicate form, and no companion of a different form was "
    "available to test whether the absence is a property of the form rather "
    "than of A")
VACUITY_QUALIFICATION_SENTENCE = (
    "composition changed how often the outcome constraint could bind, so the "
    "primary estimand is reported with the F5 vacuity-forced recomputation "
    "beside it as partial-identification bounds")

# ------------------------------------------- §10.3, §10.4: DIAGNOSTIC ONLY
HUMAN_DISAGREEMENT_MAX = 0.10
HUMAN_SAMPLE_CAP = 150
VERIFIER_CLASSES = ("pass", "fail")
FAIL_CLASS_STRATA = ("margin_one", "margin_larger")
BOUNDARY_SUITE_MIN_CASES = 40
DETERMINISM_PROCESSES = 3

# --------------------------------------------------------- §18 stage sequence
STAGE_REGISTERED = "PROTOCOL_REGISTERED"
STAGE_QUALIFIED = "QUALIFIED"
STAGE_GATE0 = "GATE_0_APPARATUS"
STAGE_REGIME = "REGIME_SCREEN"
STAGE_GATE1 = "GATE_1_MEASUREMENT"
STAGE_GATE2 = "GATE_2_FOCAL_CALIBRATION"
STAGE_GATE2_5 = "GATE_2_5_CANDIDATE_QUALIFICATION"
STAGE_GATE3A = "GATE_3A_REFERENCE_CALIBRATION"
STAGE_GATE3B = "GATE_3B_REFERENCE_SELECTION"
STAGE_GATE3C = "GATE_3C_IDENTIFICATION"
STAGE_GATE4 = "GATE_4_COMPOSED_HEADROOM"
STAGE_PREFREEZE_AUDIT = "PREFREEZE_AUDIT"
STAGE_GATE5 = "GATE_5_FREEZE"
STAGE_CONFIRMATORY = "CONFIRMATORY_GENERATION"
STAGE_MASKED_ANALYSIS = "MASKED_ANALYSIS"
STAGE_UNMASKING = "UNMASKING"
STAGE_UNMASKED_ANALYSIS = "UNMASKED_ANALYSIS"
STAGE_FINAL_REPORT = "FINAL_REPORT"

#: §18: eighteen stages where v4r4 had twelve. PROTOCOL_REGISTERED is first;
#: Gate 2 is renamed; Gate 2.5 and Gate 3A/3B/3C are inserted; PREFREEZE_AUDIT
#: and FINAL_REPORT are **stages with records** where v4r4 had tools --- a
#: check that runs beside the lifecycle can be skipped, a stage cannot.
STAGE_SEQUENCE = (
    STAGE_REGISTERED, STAGE_QUALIFIED, STAGE_GATE0, STAGE_REGIME, STAGE_GATE1,
    STAGE_GATE2, STAGE_GATE2_5, STAGE_GATE3A, STAGE_GATE3B, STAGE_GATE3C,
    STAGE_GATE4, STAGE_PREFREEZE_AUDIT, STAGE_GATE5, STAGE_CONFIRMATORY,
    STAGE_MASKED_ANALYSIS, STAGE_UNMASKING, STAGE_UNMASKED_ANALYSIS,
    STAGE_FINAL_REPORT,
)
assert len(STAGE_SEQUENCE) == 18

#: Stages that generate model responses. **Gate 2.5 is deliberately absent**:
#: kappa(R|B) needs no generation of its own, which is the whole point of
#: §9.1's presence rule and of §13.6 being free.
GENERATION_STAGES = (STAGE_GATE0, STAGE_REGIME, STAGE_GATE2, STAGE_GATE3A,
                     STAGE_GATE4, STAGE_CONFIRMATORY)
#: §10.6's entry points, each of which re-verifies the frozen verifier hash
#: before any work and fails closed on mismatch.
VERIFIER_BOUND_ENTRY_POINTS = (
    "ladder_screen", "focal_calibration", "candidate_qualification",
    "reference_calibration", "reference_selection", "spectrum_selection",
    "near_form_admission", "broad_class_admission", "composed_headroom",
    "prefreeze_audit", "freeze", "confirmatory_generation", "scoring",
    "resume_restart", "analysis", "unmasking", "report_generation",
)

# ------------------------------------------------------------ §28 statuses
TERMINAL_STATUSES = (
    "REGISTRATION_INCOMPLETE", "QUALIFICATION_FAILURE", "APPARATUS_FAILURE",
    "RESPONSE_LENGTH_INCOMPATIBLE", "TARGET_RANGE_EXHAUSTED",
    "FOCAL_RANGE_EXHAUSTED", "GRID_RESOLUTION_INSUFFICIENT",
    "REGIME_NOT_FOUND", "COMPOSED_HEADROOM_FAILURE",
    "PREFREEZE_AUDIT_FAILURE", "MEASUREMENT_NOT_ESTABLISHED",
    "MEASUREMENT_EVIDENCE_INSUFFICIENT", "SPECIFICATION_AMBIGUOUS",
)
IDENTIFICATION_STATUSES = (
    "REFERENCE_SUPPORT_NOT_IDENTIFIED", "EXCESS_NOT_IDENTIFIED",
    "DIFFICULTY_SUPPORT_NOT_IDENTIFIED", "CANDIDATE_RESERVE_EXHAUSTED",
    "DIFFICULTY_SUPPORT_MARGINAL", "A_GENERAL_NOT_EXCLUDED",
    "LOCAL_AND_SPECTRUM_DISAGREE", "LOCAL_TIER_DISAGREE",
    "DIFFICULTY_COORDINATE_DEPENDENT", "DIFFICULTY_COORDINATE_DEGENERATE",
    "INTERACTION_ESTIMATE_DRIFTED", "REFERENCE_ROLE_NOT_MATCHED",
    "REFERENCE_POOL_SAME_FORM", "COMPANION_CLASS_NOT_MATCHED",
    "NEAR_FORM_ARM_NOT_AVAILABLE", "CLASS_ARM_NOT_AVAILABLE",
    "CLASS_ARM_NOT_MATCHED", "OPERATING_POINT_AT_GRID_BOUNDARY",
    "POSITION_CONFOUNDED", "HUMAN_VALIDATION_UNAVAILABLE",
)
#: New in v5, named so a reader can see what the revision added.
NEW_IDENTIFICATION_STATUSES = (
    "REFERENCE_SUPPORT_NOT_IDENTIFIED", "LOCAL_TIER_DISAGREE",
    "INTERACTION_ESTIMATE_DRIFTED", "REFERENCE_ROLE_NOT_MATCHED",
    "REFERENCE_POOL_SAME_FORM", "NEAR_FORM_ARM_NOT_AVAILABLE",
    "OPERATING_POINT_AT_GRID_BOUNDARY",
)
assert set(NEW_IDENTIFICATION_STATUSES) <= set(IDENTIFICATION_STATUSES)
RESULT_MARKERS = ("INSUFFICIENT_PRECISION", "INDETERMINATE")
#: Correct HISTORICAL labels for earlier revisions' terminations. v5 never
#: emits them.
WITHDRAWN_STATUSES = ("REFERENCE_POOL_MISMATCH", "COMPOSED_UPTAKE_MISMATCH")

#: §26's methodological success criterion, judged before any confirmatory
#: composed outcome is seen and reported whether or not any L3 is emitted.
SUCCESS_CRITERION_VALUES = ("MET", "NOT_MET")

# -------------------------------------------------------- §28 artifact model
ARTIFACT_STATES = ("generated", "committed", "accepted", "superseded")
ARTIFACT_TYPES = (
    "registration_record", "qualification_record", "prefreeze_plan",
    "pilot_record", "gate_record", "calibration_record", "selection_record",
    "identification_record", "audit_record", "registered_freeze",
    "confirmatory_evidence", "masked_result", "unmasked_result",
    "final_report", "superseded_non_evidence",
)
STAGE_ARTIFACT_TYPE = {
    STAGE_REGISTERED: "registration_record",
    STAGE_QUALIFIED: "qualification_record",
    STAGE_GATE0: "pilot_record",
    STAGE_REGIME: "gate_record",
    STAGE_GATE1: "gate_record",
    STAGE_GATE2: "calibration_record",
    STAGE_GATE2_5: "calibration_record",
    STAGE_GATE3A: "calibration_record",
    STAGE_GATE3B: "selection_record",
    STAGE_GATE3C: "identification_record",
    STAGE_GATE4: "calibration_record",
    STAGE_PREFREEZE_AUDIT: "audit_record",
    STAGE_GATE5: "registered_freeze",
    STAGE_CONFIRMATORY: "confirmatory_evidence",
    STAGE_MASKED_ANALYSIS: "masked_result",
    STAGE_UNMASKING: "unmasked_result",
    STAGE_UNMASKED_ANALYSIS: "unmasked_result",
    STAGE_FINAL_REPORT: "final_report",
}
assert set(STAGE_ARTIFACT_TYPE) == set(STAGE_SEQUENCE)
assert set(STAGE_ARTIFACT_TYPE.values()) <= set(ARTIFACT_TYPES)

# ------------------------------------------------------------- §20 masking
MASK_NAMESPACES = ("pilot_mask", "confirmatory_mask")
MASK_MIN_DIFFERING_FRACTION = 0.5

# ------------------------------------------- §14.2 missingness / duplicates
MISSINGNESS_REPORT_THRESHOLD = 0.01
DUPLICATE_QUALIFICATION_MAX = 0.05

# --------------------------------------------------------------- §22 mediators
POST_TREATMENT_FIELDS = (
    "word_count", "token_count", "truncated", "finish_reason", "graded",
    "vacuous_pass", "non_vacuous", "joint_state", "response_length_words",
    "processing_failure", "in_stem_band", "longest_word", "register_statistic",
)
#: §22. kappa is pre-treatment FOR THE COMPANION --- it is measured where the
#: companion is absent --- so it may enter the difficulty coordinate.
#: kappa_under_b has the same standing with one difference stated plainly: it
#: is measured on rows produced under B, so it is not pre-treatment with
#: respect to the pair (c, B). §13.6 registers its ONLY use.
CHANCE_FIELDS = ("chance_compliance", "instructed_compliance",
                 "instruction_lift", "kappa_under_b", "displacement",
                 "projected_compliance")
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

# --------------------------------------------------------------- §30 ledger
REUSE_CLASSIFICATIONS = ("HISTORICAL_OUTCOME", "DEVELOPMENT_EVIDENCE",
                         "REUSED_IMPLEMENTATION", "RECOMPUTED_DIAGNOSTIC",
                         "NEW_V5_EVIDENCE")


def assert_binding() -> None:
    """Refuse a caller that treats these values as registered while §34 is open.

    Every number above is the preregistration's **proposed** value. It becomes
    registered when the signed registration manifest binds it, which §18 stage
    1 does and which cannot happen while a §34 decision is unresolved. Any
    code path that would write a threshold into an evidence record calls this
    first, so the distinction between "in the source" and "registered" is
    enforced rather than remembered.
    """
    from dci1v5.protocol import decisions

    decisions.assert_decisions_closed_for_stage(STAGE_REGISTERED)
