"""The Batch 1 pilot configuration and its register of scientific decisions.

Everything a pilot decision depends on is here, as data, so that the
selection code takes it as input instead of hard-coding it, and so that the
Freeze 1 manifest can hash it. ``PilotConfig`` is the whole configuration;
``DECISIONS`` lists every choice that needs the researcher's approval before
the real pilot may run. A decision's payload is hashed, and an approval
names the hash it approves, so editing a decision after approval voids it.

Carried values, each checked against its source by a test:

* the model panel, revisions and per-model engine settings
  (``dci1/src/dci1v4/models/registry.py``);
* decoding --- temperature 0.7, top-p 0.9, top-k 50, thinking off
  (``dci1v4/generation/backend.py::build_plan``, prereg v8.1 §decoding);
* the prompt template and its stem sentence
  (``dci1/src/dci1v7/protocol/constants.py``).

The completion cap is not carried: v8.1 selected it per study in its regime
screen. 512 is proposed (D12) because the v8 pilot's screen ran at 512
(``dci1/docs/V8_PILOT.md``) and a 60-120 word answer is about 160 tokens.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from dci.batch1 import library as L
from dci.batch1 import text as T
from dci.batch1 import verifiers as V
from dci.batch1.store import SOURCE_HASH_SCHEME, code_hash
from dci.provenance.hashes import sha, sha_file

_PKG = Path(__file__).resolve().parent
_SRC = _PKG.parent
_REPO = _PKG.parents[2]

__all__ = ["STUDY_ID", "PROTOCOL_VERSION", "ORCHESTRATOR_PYTHON",
           "BACKEND_PYTHON", "ModelConfig", "MODELS",
           "MODEL_BY_KEY", "DECODING", "STEM_SENTENCE", "PROMPT_ZERO",
           "PROMPT_ONE", "PilotConfig", "DEFAULT_CONFIG", "Decision",
           "decisions", "decision_payloads"]

STUDY_ID = "dci-batch1-pilot"
PROTOCOL_VERSION = "batch1-pilot/0.1-proposed"

# ------------------------------------------------------------------ prompts
#: Carried byte-identically from dci1v7/protocol/constants.py (v4r3 §8.5).
STEM_SENTENCE = "Answer in 60 to 120 words."
PROMPT_ZERO = "{question}\n\n" + STEM_SENTENCE + "\n\nAnswer:"
PROMPT_ONE = "{question}\n\n" + STEM_SENTENCE + "\n\n1. {c1}\n\nAnswer:"


# ------------------------------------------------------------------- models
@dataclass(frozen=True)
class ModelConfig:
    key: str
    model_id: str
    revision: str
    family: str
    thinking_policy: str
    chat_template_kwargs: dict[str, Any]
    gpu_memory_utilization: float
    max_model_len: int = 4096
    dtype: str = "bfloat16"
    tensor_parallel_size: int = 1
    #: Rows per second on one AMD RX 7900 XTX during the v8.1 confirmatory
    #: run (two-lane feasibility audit, 2026-10-18; inferred from run
    #: timestamps, ~130 response tokens per row). A starting point for the
    #: estimate, not a property of any other hardware.
    historical_rows_per_second: float = 0.0


MODELS: tuple[ModelConfig, ...] = (
    ModelConfig("gemma-3n-e2b-it", "google/gemma-3n-E2B-it",
                "5e092ebca197cdcd8d8b195040accf22693501bc", "gemma3n",
                "unavailable", {}, 0.85, historical_rows_per_second=9.7),
    ModelConfig("gemma-3n-e4b-it", "google/gemma-3n-E4B-it",
                "c1221e9c62e34a43ab7ffacd1be0ea71f126ef10", "gemma3n",
                "unavailable", {}, 0.95, historical_rows_per_second=4.94),
    ModelConfig("qwen3-4b", "Qwen/Qwen3-4B",
                "1cfa9a7208912126459214e8b04321603b3df60c", "qwen3",
                "disabled", {"enable_thinking": False}, 0.85,
                historical_rows_per_second=17.4),
    ModelConfig("qwen3-4b-instruct-2507", "Qwen/Qwen3-4B-Instruct-2507",
                "cdbee75f17c01a7cc42f958dc650907174af0554", "qwen3",
                "unavailable", {}, 0.85, historical_rows_per_second=10.1),
)
MODEL_BY_KEY = {m.key: m for m in MODELS}

#: D12. The interpreter that runs this package: it computes every payload
#: and code hash, writes and validates both freezes, and drives the backend.
#: Python 3.12, the researcher's decision of 2026-10-25 (it replaces the
#: 3.11 approved on 2026-10-19): native on Lambda's GPU Base 24.04 image, so
#: the orchestrator and the backend share one interpreter version there.
#: The code hash does not depend on it (``store.code_hash``); it is pinned so
#: that what was reviewed is what runs.
ORCHESTRATOR_PYTHON = "3.12"
#: D12. The backend interpreter that runs vLLM, in a separate process
#: (environments/cuda-vllm). The CUDA vllm 0.15.1 wheel is cp38-abi3, so the
#: wheel does not force a version; 3.12 is vLLM's Docker default and native on
#: GPU Base 24.04.
BACKEND_PYTHON = "3.12"
#: D12 (researcher's conditions, 2026-10-25). What an attested environment
#: must be before it can be locked or frozen: these are checked, not merely
#: recorded (``environment.requirement_problems``). The driver is a minimum:
#: torch 2.9.1+cu129 needs a CUDA 12.9 driver.
EXECUTION_REQUIREMENTS: dict[str, Any] = {
    "backend_python": BACKEND_PYTHON,
    "packages": {"vllm": "0.15.1", "torch": "2.9.1+cu129"},
    "torch_cuda": "12.9",
    "gpu_name": "NVIDIA H100 80GB HBM3",
    "gpu_count": 2,
    "gpu_compute_capability": "9.0",
    "min_driver": "575.51.03",
}

DECODING: dict[str, Any] = {
    "temperature": 0.7, "top_p": 0.9, "top_k": 50,
    "max_new_tokens": 512,           # D12, proposed
    "reasoning_mode": "NO_THINKING", "skip_special_tokens": True,
    "engine_seed": 20261018, "chunk_size": 64,
}


# ------------------------------------------------------------ configuration
@dataclass(frozen=True)
class PilotConfig:
    models: tuple[str, ...] = tuple(m.key for m in MODELS)
    frames: tuple[str, ...] = L.FRAMES
    a_counts: tuple[int, ...] = L.A_COUNTS
    b_limits: tuple[int, ...] = L.B_LIMITS
    # Stage 1 (D05): every stand-alone cell on the same 32 stage-1 topics.
    stage1_topics: int = 32
    stage1_draws: int = 1
    task_only_draws: int = 2          # task-only: 32 topics x 2 per model
    # Stage 2 (D06): 64 new topics per refined cell, at most this many cells.
    stage2_topics: int = 64
    stage2_draws: int = 1
    stage2_max_cells: int = 240
    pilot_topics: int = 96            # stage1 + stage2, disjoint
    # Interval used for every boundary decision and report.
    z: float = 1.959963984540054
    # Eligibility and matching (design values; D09, D10).
    eligibility_threshold: float = 0.20
    extension_threshold: float = 0.10
    matching_tolerance: float = 0.10
    # A and B selection (D07, D08; revised after the 2026-10-19 audit and
    # proposed, not approved).
    a_headroom_band: tuple[float, float] = (0.10, 0.90)
    a_min_informative_model_frames: int = 6
    a_min_informative_models: int = 3
    preferred_a_count: int = 4
    b_informative_band: tuple[float, float] = (0.15, 0.85)
    b_min_gap: int = 2
    b_min_median_separation: float = 0.15
    b_min_separated_models: int = 3
    b_min_informative_model_frames: int = 4
    # Coverage (design minima; the G3 minimum for P3 is proposed, D11).
    g1_min_distinct_words: int = 3
    p1_min_additional: int = 2
    p2_min_additional_other_object: int = 2
    # D11, researcher's decision 2026-10-25 (COVERAGE_SIMULATION_REVIEW.md
    # §8, rule P3k3); the design value was 2.
    p3_min_additional_other_operation: int = 3
    p3_min_g3: int = 3
    feasibility_min_configs: int = 12
    feasibility_min_models: int = 3
    # A cell with fewer behavioural rows than this share of its plan is
    # incomplete and decides nothing. (The D06 completeness gate already
    # refuses any stage with a missing row; this guards direct table use.)
    min_cell_fraction: float = 0.9
    # A cell whose truncated share exceeds this is listed for review of the
    # completion cap (D12, proposed); it is never dropped or re-run.
    truncation_review_share: float = 0.02
    # A row whose own outcome was TECHNICAL this many times is not sent again
    # (D04, proposed; re-audit R4.4): the stage stays incomplete and the run
    # reports it, instead of retrying a deterministic failure for ever.
    max_technical_attempts: int = 3
    # Membership-stability diagnostics (D14, proposed).
    stability_replicates: int = 200
    stability_seed: int = 20261019
    stability_unstable_band: tuple[float, float] = (0.2, 0.8)
    # Members included in at least this share of resamples are "stable" for
    # the stable-member feasibility sensitivity (majority inclusion; the
    # precision review shows stricter cuts reject truly feasible pilots).
    stability_stable_threshold: float = 0.5
    stability_min_feasible_share: float = 0.8
    # Freeze 2 flags a FEASIBLE verdict whose weakest contrast is supported
    # in at most feasibility_min_configs + this many configurations (D14,
    # proposed; for review, not a gate; re-audit R4.5).
    near_threshold_margin: int = 2
    generation_root_seed: int = 202610180
    seed_domain: str = "dci.batch1:gen:v1"

    def __post_init__(self):
        if self.pilot_topics != self.stage1_topics + self.stage2_topics:
            raise ValueError("pilot_topics must equal stage1_topics + "
                             "stage2_topics (the two stages are disjoint)")
        unknown = set(self.models) - set(MODEL_BY_KEY)
        if unknown:
            raise ValueError(f"unconfigured models {sorted(unknown)}")
        if not set(self.frames) <= set(L.FRAMES):
            raise ValueError(f"frames {self.frames}")
        if not set(self.a_counts) <= set(L.A_COUNTS) or \
                not set(self.b_limits) <= set(L.B_LIMITS):
            raise ValueError("A counts and B limits must come from the "
                             "library's candidates")

    def state(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def config_hash(self) -> str:
        return sha(["batch1/config", self.state()])


DEFAULT_CONFIG = PilotConfig()


# ---------------------------------------------------------------- decisions
@dataclass(frozen=True)
class Decision:
    decision_id: str
    title: str
    origin: str          # "design" (operationalises the brief) | "proposed"
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def payload_hash(self) -> str:
        return sha(["batch1/decision", self.decision_id, self.payload])


#: The code each decision's rule is executed by. An approval binds these
#: hashes (``store.code_hash``: docstrings and comments excluded), so a change
#: to the implementing code voids the approval of every decision it touches,
#: and a documentation edit voids none.
IMPLEMENTATION = {
    "D01": ("library.py", "verifiers.py"),
    "D02": ("library.py", "design.py"),
    "D03": ("text.py", "dci/verifiers/rules.py"),
    "D04": ("verifiers.py", "outcomes.py", "scoring.py"),
    "D05": ("design.py", "topics.py"),
    "D06": ("calibration.py", "evidence.py", "pipeline.py", "intervals.py"),
    "D07": ("calibration.py",),
    "D08": ("calibration.py", "references.py"),
    "D09": ("references.py", "intervals.py"),
    "D10": ("references.py", "intervals.py"),
    "D11": ("references.py",),
    "D12": ("runner.py", "environment.py", "outcomes.py", "design.py"),
    "D13": ("references.py", "library.py"),
    "D14": ("stability.py",),
}


def implementation(decision_id: str) -> dict[str, str]:
    """Package modules resolve under the package; ``dci/...`` under src."""
    return {name: code_hash(_SRC.parent / name if name.startswith("dci/")
                            else _PKG / name)
            for name in IMPLEMENTATION[decision_id]}


def _fields(cfg: PilotConfig, *names: str) -> dict[str, Any]:
    state = cfg.state()
    return {k: state[k] for k in names}


def _topic_payload(cfg: PilotConfig) -> dict[str, Any]:
    from dci.batch1 import topics as TOP
    bank = TOP.load_bank()
    split = TOP.split_bank(bank, pilot_topics=cfg.pilot_topics,
                           stage1_topics=cfg.stage1_topics)
    return {"bank_hash": split.bank_hash, "split_hash": split.split_hash,
            "historical_sources": sorted(TOP.HISTORICAL_SOURCES),
            "screen": {"wordset": TOP.WORDSET_SCREEN,
                       "content": TOP.CONTENT_SCREEN,
                       "rare_stem_df": TOP.RARE_STEM_DF,
                       "rare_stem_min_shared": TOP.RARE_STEM_MIN_SHARED,
                       "rare_stem_min_letters": TOP.RARE_STEM_MIN_LETTERS},
            "review_hash": sha_file(TOP.REVIEW_PATH),
            "semantic_review_hash": sha_file(TOP.SEMANTIC_REVIEW_PATH)}


def _backend_source_hash() -> str:
    from dci.batch1 import environment as ENV
    return ENV.backend_source()["hash"]


def decisions(cfg: PilotConfig = DEFAULT_CONFIG) -> tuple[Decision, ...]:
    refs = L.reference_library()
    proposed = [c for c in refs if c.status == L.STATUS_PROPOSED]

    def d(decision_id, title, origin, summary, payload):
        return Decision(decision_id, title, origin, summary,
                        {**payload,
                         "implementation": implementation(decision_id),
                         "orchestrator_python": ORCHESTRATOR_PYTHON})

    return (
        d("D01", "Parameters of the 29 proposed variants", "proposed",
          "Concrete targets, counts and minima for the 29 slots the "
          "design left open.",
          {c.cid: c.spec_hash for c in proposed}),
        d("D02", "The two wording frames and the prompt", "proposed",
          "F0 imperative, F1 requirement; A's strings are v8.1 A "
          "frames 0/1, B's are historical B wordings 1/0; the carried "
          "DCI-1 prompt template with one numbered instruction.",
          {"templates": {k: f.state()["templates"]
                         for k, f in sorted(L.FAMILIES.items())},
           "frames": list(cfg.frames), "prompt_zero": PROMPT_ZERO,
           "prompt_one": PROMPT_ONE}),
        d("D03", "Text semantics", "proposed",
          "Historical alpha-run words for every family; certified "
          "sentence segmentation; A folded per word (differs from "
          "historical S0 only on U+0130).",
          {"text": T.TEXT_SEMANTICS, "hash": T.text_semantics_hash()}),
        d("D04", "Outcomes, compliance and vacuity", "proposed",
          "Compliant = PASS on a non-empty, untruncated, non-vacuous "
          "answer. A completed blank generation (the seam's "
          "CHANNEL_INVALID under NO_THINKING) is an EMPTY answer: in n, "
          "never compliant, not regenerated. A technical failure is "
          "never evidence and stays open for resume, up to "
          "max_technical_attempts per row. Literal passes and "
          "the reason a pass is excluded are recorded.",
          {"min_words": V.NON_VACUITY_MIN_WORDS,
           "rules": {k: f.vacuity for k, f in sorted(L.FAMILIES.items())},
           "verifier_bundle_hash": V.verifier_bundle_hash(),
           **_fields(cfg, "max_technical_attempts")}),
        d("D05", "Stage 1 allocation and pilot topics", "proposed",
          "32 responses per stand-alone cell on one shared set of 32 "
          "new topics; task-only 64 per model; 96 pilot topics; the "
          "topic bank and its split as reviewed.",
          {**_fields(cfg, "stage1_topics", "stage1_draws", "task_only_draws",
                     "pilot_topics"),
           "topics": _topic_payload(cfg)}),
        d("D06", "Stage 2 refinement rule and stage completeness", "proposed",
          "One bounded round, selected only from complete, authenticated "
          "Stage 1 evidence: boundary cells ranked by class, then by "
          "standardised distance to the boundary; 64 new-topic responses "
          "each; at most stage2_max_cells cells. Finalisation needs both "
          "stages complete; there is no partial-completion rule.",
          _fields(cfg, "stage2_topics", "stage2_draws", "stage2_max_cells",
                  "z", "a_headroom_band", "b_informative_band",
                  "eligibility_threshold", "extension_threshold",
                  "matching_tolerance", "min_cell_fraction")),
        d("D07", "Selecting the two B limits", "proposed",
          "Admissible pairs: gap >= b_min_gap; median B-only separation "
          ">= b_min_median_separation; that separation in >= "
          "b_min_separated_models models; each limit informative in >= "
          "b_min_informative_model_frames model-frames. Rank by "
          "informative cells, the worse limit, then separation. No "
          "admissible pair fails B selection.",
          _fields(cfg, "b_limits", "b_informative_band", "b_min_gap",
                  "b_min_median_separation", "b_min_separated_models",
                  "b_min_informative_model_frames")),
        d("D08", "Selecting the global A count", "proposed",
          "Admissible N: p_A inside a_headroom_band in >= "
          "a_min_informative_model_frames model-frames across >= "
          "a_min_informative_models models. Then maximise configurations "
          "with G1 support and an informative A, then headroom, then "
          "prefer N=4, then the smaller N. Uninformative-A configurations "
          "never count toward feasibility. No admissible N fails A "
          "selection; no per-model fallback.",
          _fields(cfg, "a_counts", "a_headroom_band",
                  "a_min_informative_model_frames",
                  "a_min_informative_models", "preferred_a_count")),
        d("D09", "Eligibility operationalisation", "design",
          "Point estimate >= 20% in at least one model-frame, on all "
          "stand-alone responses of that cell (Stage 1 + 2); 10% "
          "extension reported separately. The OR over eight cells admits "
          "candidates whose true rate is below 20% (disclosed).",
          _fields(cfg, "eligibility_threshold", "extension_threshold",
                  "min_cell_fraction")),
        d("D10", "Matching operationalisation", "design",
          "|p_X - p_A| <= 0.10 per model-frame on raw compliance; iota "
          "uses task-only kappa per model (frame-invariant prompt); "
          "undefined iota is unmatched and flagged. Matching is a noisy "
          "classification at pilot sample sizes (see D14).",
          _fields(cfg, "matching_tolerance")),
        d("D11", "Coverage requirements", "design",
          "Design minima for G1, P1, P2, P3 and the 12-of-16 target; "
          "proposed: P3 also needs |G3| >= p3_min_g3.",
          _fields(cfg, "g1_min_distinct_words", "p1_min_additional",
                  "p2_min_additional_other_object",
                  "p3_min_additional_other_operation", "p3_min_g3",
                  "feasibility_min_configs", "feasibility_min_models")),
        d("D12", "Model panel, decoding, cap, seeds and backend", "proposed",
          "Historical four-model panel and decoding; cap 512 tokens, with "
          "any cell truncating above truncation_review_share listed for "
          "review; the seed derivation; the vLLM seam source; Python 3.12 "
          "for the orchestrator and the vLLM backend (the CUDA vllm 0.15.1 "
          "wheel is cp38-abi3; 3.12 is vLLM's Docker default and native on "
          "GPU Base 24.04); the execution requirements (vllm 0.15.1, torch "
          "2.9.1+cu129, 2x H100 SXM, driver >= 575.51.03), one worker per "
          "GPU, TP as configured. The execution environment is attested "
          "on the host, checked against the requirements and bound by "
          "Freeze 1; a bounded, authorised smoke test (never evidence) "
          "measures load time, throughput and truncation first.",
          {"models": [asdict(MODEL_BY_KEY[k]) for k in cfg.models],
           "decoding": DECODING,
           **_fields(cfg, "generation_root_seed", "seed_domain",
                     "truncation_review_share"),
           "backend_source_hash": _backend_source_hash(),
           "backend_python": BACKEND_PYTHON,
           "orchestrator_python": ORCHESTRATOR_PYTHON,
           "execution_requirements": EXECUTION_REQUIREMENTS,
           "source_hash_scheme": SOURCE_HASH_SCHEME}),
        d("D13", "Object types and hierarchical weights", "proposed",
          "Commas and semicolons share the object type punctuation; "
          "weights equal over operations, then object types, then "
          "parameter variants (so a word with three count variants "
          "carries three variant shares).",
          {"objects": {c.cid: c.object_type for c in refs},
           "operations": {c.cid: c.operation for c in refs}}),
        d("D14", "Membership-stability diagnostics", "proposed",
          "Topic-cluster bootstrap of the pilot: inclusion frequency per "
          "reference, A/B selection and FEASIBLE shares, borderline "
          "matches, and feasibility on majority-stable members; a flag "
          "when a FEASIBLE verdict's weakest contrast is within "
          "near_threshold_margin of the target. Diagnostic "
          "only, never a gate: membership stays the point-estimate rule; "
          "instability is flagged for review, never auto-corrected.",
          _fields(cfg, "stability_replicates", "stability_seed",
                  "stability_unstable_band", "stability_stable_threshold",
                  "stability_min_feasible_share", "near_threshold_margin")),
    )


def decision_payloads(cfg: PilotConfig = DEFAULT_CONFIG) -> dict[str, str]:
    return {d.decision_id: d.payload_hash for d in decisions(cfg)}
