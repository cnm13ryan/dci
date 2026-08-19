"""Every registered study value, in one place, with no hidden defaults.

The values here transcribe `user-notes/DCI-1_preregistration_v2.md` and the
registered amendments (task brief §1–§3), as resolved by the dated pre-freeze
decisions in `dci1/DECISIONS.md`. Nothing in this module is a tunable; a change
here after a model's protocol freeze is detected by the freeze record's hashes
and fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

PROTOCOL_ID = "DCI-1"
PROTOCOL_VERSION = "2.0"
#: The registered amendment set applied on top of v2.0 (task brief §1–§3).
AMENDMENT_ID = "A1-vllm-multimodel-cached-generation"

# ---------------------------------------------------------------- decoding §4
#: Preregistered decoding policy, preserved verbatim under the vLLM backend
#: (amendment §1.2 forbids adopting model-card decoding defaults).
DECODING = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,               # set explicitly, never a backend default
    "max_new_tokens": 400,
    "samples_per_cell": 1,     # one *accepted* response per block × arm (§2.9)
}
#: The greedy sensitivity replication (§8): deterministic decoding, no pools.
GREEDY_DECODING = {
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": -1,
    "max_new_tokens": 400,
    "samples_per_cell": 1,
}

# ------------------------------------------------------------------ topics §6
SUBJECT_AREAS = (
    "everyday science", "history", "geography", "food", "music", "sport",
    "work and organisations", "health and the body", "technology",
    "language and writing", "art and design", "the natural world",
)
TOPICS_PER_AREA = 48
CALIBRATION_PER_AREA = 8
CONFIRMATORY_PER_AREA = 32
SEQUESTERED_PER_AREA = 8
N_TOPICS = TOPICS_PER_AREA * len(SUBJECT_AREAS)              # 576
N_CALIBRATION = CALIBRATION_PER_AREA * len(SUBJECT_AREAS)    # 96
N_CONFIRMATORY = CONFIRMATORY_PER_AREA * len(SUBJECT_AREAS)  # 384
N_SEQUESTERED = SEQUESTERED_PER_AREA * len(SUBJECT_AREAS)    # 96

# ------------------------------------------------------------------ design §8
ARMS = ("focal", "ref1", "ref2", "ref3", "target_alone", "topic_alone")
PRIMARY_ARMS = ("focal", "ref1", "ref2", "ref3")
N_BLOCKS = N_CONFIRMATORY                                    # 384
BLOCKS_PER_ORDER = N_BLOCKS // 2                             # 192
N_WORDINGS = 4
GREEDY_BLOCKS = 96                                           # first 96 blocks

# ------------------------------------------------------- calibration/gates §18
N_GRID = (1, 2, 3)
M_GRID = (7, 8, 9, 10)
TARGET_SOLO_BAND = (0.15, 0.50)
FOCAL_SOLO_BAND = (0.15, 0.55)
SOLO_RATE_TARGET = 0.30
ADMISSION_RATE_WINDOW = 0.10
ADMISSION_LENGTH_TOLERANCE = 0.20
N_REFERENCES = 3

# -------------------------------------------------------------- estimands §11
SMALLEST_EFFECT_OF_INTEREST = 0.10
EXCHANGEABILITY_MARGIN = 0.05
EQUIVALENCE_REGION_PRIMARY = (-0.10, 0.10)
EQUIVALENCE_REGION_EXCHANGEABILITY = (-0.05, 0.05)

# --------------------------------------------------------------- analysis §20
BOOTSTRAP_RESAMPLES = 10_000
CONFIDENCE_LEVEL = 0.95

# ---------------------------------------------------------------- families §14
FAMILY_SIZES = {"F1": 2, "F2": 3, "F3": 6, "F4": 6, "F5": 9, "F6": 3}

# --------------------------------------------------------- arm symmetry §16
UPTAKE_DIFFERENCE_THRESHOLD = 0.25
NON_BEHAVIOURAL_DIFFERENCE_THRESHOLD = 0.05
SHORT_RESPONSE_WORDS = 3

# ------------------------------------------------------------------- pilot §17
PILOT_TOPICS = 12
PILOT_CELLS = PILOT_TOPICS * len(ARMS)                       # 72
PILOT_TRUNCATION_CEILING = 0.10
#: Pilot-only provisional parameters (D15). Discarded, never scientific.
PILOT_PROVISIONAL = {"n": 2, "m": 8, "references": ("C1", "C3", "C10")}

# ------------------------------------------------- amendment §2: cached pools
#: M — registered pre-freeze study value (D01). Provenance: the smallest pool
#: size used by Kim et al. (arXiv:2605.11209, 16 for Qwen2.5-Math-7B-Instruct),
#: adopted as a study-specific adaptation, NOT validated for Qwen3.5 / Gemma 4
#: and NOT an implementation default.
GENERATION_POOL_SIZE = 16
PRIMARY_SELECTION_RULE = "primary_pool_index=0"
POOL_TO_CELL_MAPPING = (
    "one cached response per (model, block, arm), sampled with replacement, "
    "never aggregated")
PSEUDO_RUN_COUNT = 1000
PSEUDO_RUN_FULL_ANALYSIS_COUNT = 50                          # D05

# --------------------------------------------------- randomness levels (D06)
TOPIC_SPLIT_SEED = 202608160
GENERATION_ROOT_SEED = 202608161
RESAMPLING_ROOT_SEED = 202608162
BOOTSTRAP_ROOT_SEED = 202608163

# ------------------------------------------------------------- release §24/§31
CANARY_STRING = "DCI1-CANARY-7f3a9c2e-2026-e5b1-d4a8-instruction-interference"

#: Design-defining resampling fields (amendment §2.10). Every per-model freeze
#: record must carry every one of these explicitly; a record missing any is
#: incomplete and fails closed.
RESAMPLING_FIELDS = (
    "generation_pool_size",
    "primary_selection_rule",
    "pool_to_cell_mapping",
    "pseudo_run_count",
    "generation_root_seed",
    "resampling_root_seed",
    "bootstrap_seed",
)


class ProtocolError(RuntimeError):
    """A protocol invariant was violated. The study fails closed."""


@dataclass(frozen=True)
class StudyConfig:
    """The design-defining resampling configuration (amendment §2.10).

    Every field is required: there is no default, no environment fallback, and
    no runtime inference. Construct it only through :func:`study_config` (the
    registered values) or explicitly in tests.
    """

    generation_pool_size: int
    primary_selection_rule: str
    pool_to_cell_mapping: str
    pseudo_run_count: int
    generation_root_seed: int
    resampling_root_seed: int
    bootstrap_seed: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StudyConfig:
        missing = [f.name for f in fields(cls) if f.name not in data]
        if missing:
            raise ProtocolError(
                f"StudyConfig is missing design-defining resampling fields "
                f"{missing}; every field of amendment §2.10 must be explicit "
                f"(no defaults, no inference). Fail closed.")
        return cls(**{f.name: data[f.name] for f in fields(cls)})

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


def study_config() -> StudyConfig:
    """The registered configuration of this study (D01–D08)."""
    return StudyConfig(
        generation_pool_size=GENERATION_POOL_SIZE,
        primary_selection_rule=PRIMARY_SELECTION_RULE,
        pool_to_cell_mapping=POOL_TO_CELL_MAPPING,
        pseudo_run_count=PSEUDO_RUN_COUNT,
        generation_root_seed=GENERATION_ROOT_SEED,
        resampling_root_seed=RESAMPLING_ROOT_SEED,
        bootstrap_seed=BOOTSTRAP_ROOT_SEED,
    )
