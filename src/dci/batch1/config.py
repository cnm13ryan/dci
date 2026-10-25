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

from dataclasses import asdict, dataclass, field, replace
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
    "engine_seed": 20261018,
    # Requests per llm.generate call (D12; researcher's decision of
    # 2026-10-25, was 64). 64 left the H100s at ~45% utilisation; 512 runs
    # 3.6-5.4x faster with the same finish reasons, truncation, empty rate
    # and answer length (docs/batch1/PILOT_ABORT_2026-10-25.md).
    "chunk_size": 512,
    # CUDA graphs off (D12, kept by the same decision): graphs added only
    # 10-50% speed but cut fresh-process regeneration agreement from 97%
    # to 11%. Bound here rather than hard-coded in the runner.
    "enforce_eager": True,
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
    # ---- protocol v2 (revision 2026-10; researcher's decisions R1-R13 of
    # 2026-10-26, docs/batch1/revision/APPROVALS_2026-10-26.md). The v1
    # defaults reproduce the pilot of 2026-10-25 exactly.
    protocol: str = "v1"              # v1: refine-and-pool; v2: screen T1, measure T2
    library_version: str = "v1"       # R1, R2 (library.LIBRARY_VERSIONS)
    topic_bank: str = "v1"            # R6
    fixed_a: str = ""                 # R3: v2 fixes A instead of selecting it
    # R7: the T1 -> T2 carry rule (posterior P(|p_X - p_A| <= tol) in at least
    # one configuration), its cap, and the Stage B forecast (R8 early stop).
    carry_min_posterior: float = 0.05
    carry_max_references: int = 110
    forecast_min_feasible: float = 0.20
    forecast_draws: int = 2000
    forecast_seed: int = 20261026
    max_total_rows: int = 30976       # R7: the run's response budget
    weights_mode: str = "variant"     # R10: "variant" (v1) or "word_then_count"
    truncation_review_min_rows: int = 1   # R11: v2 needs at least 2 rows
    # v2.1 (after the R12(d) audit, finding B1): "carry" sends the R7
    # carried set to T2; "all" measures every reference on T2, so G2, G4 and
    # G6 are drawn from the whole library and not from a matched-leaning
    # subset. The forecast and early stop are the same in both.
    carry_mode: str = "carry"

    def __post_init__(self):
        if self.pilot_topics != self.stage1_topics + self.stage2_topics:
            raise ValueError("pilot_topics must equal stage1_topics + "
                             "stage2_topics (the two stages are disjoint)")
        unknown = set(self.models) - set(MODEL_BY_KEY)
        if unknown:
            raise ValueError(f"unconfigured models {sorted(unknown)}")
        if not set(self.frames) <= set(L.FRAMES):
            raise ValueError(f"frames {self.frames}")
        if not set(self.a_counts) <= set(L.A_COUNTS) | set(L.A_COUNTS_V2) or \
                not set(self.b_limits) <= set(L.B_LIMITS):
            raise ValueError("A counts and B limits must come from the "
                             "library's candidates")
        if self.protocol not in ("v1", "v2") or \
                self.library_version not in L.LIBRARY_VERSIONS or \
                self.topic_bank not in ("v1", "v2", "v3") or \
                self.weights_mode not in ("variant", "word_then_count"):
            raise ValueError("unknown protocol, library, topic bank or "
                             "weights mode")
        if self.carry_mode not in ("carry", "all"):
            raise ValueError(f"carry mode {self.carry_mode!r}")
        if self.protocol == "v2" and not self.fixed_a:
            raise ValueError("protocol v2 fixes A (R3)")

    def activate(self) -> "PilotConfig":
        """Make this configuration's library the process's active one."""
        L.set_library_version(self.library_version)
        return self

    def state(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def config_hash(self) -> str:
        return sha(["batch1/config", self.state()])


DEFAULT_CONFIG = PilotConfig()

#: The revised protocol (revision 2026-10, R1-R13): library v2, fresh topic
#: bank v2 split into T1 (48 screening topics) and T2 (96 membership
#: topics), A fixed at however x 6 and B at 8 and 10 (screened A counts 4
#: and 5 are diagnostics), every other rule unchanged (D09-D11 as approved).
REVISION_CONFIG = PilotConfig(
    protocol="v2", library_version="v2", topic_bank="v2",
    a_counts=(4, 5, 6), b_limits=(8, 10), fixed_a="A.however.6",
    stage1_topics=48, stage1_draws=1, task_only_draws=1,
    stage2_topics=96, stage2_draws=1, stage2_max_cells=920, pilot_topics=144,
    max_total_rows=185000, weights_mode="word_then_count",
    truncation_review_min_rows=2, seed_domain="dci.batch1:gen:v2")

#: v2.1: protocol v2 with every reference measured on T2 (audit B1), no C'
#: top-up (R7 option b), a fresh topic bank v3 for T1 and T2 (the
#: researcher's condition of 2026-10-26), a budget of 192,000 for
#: 63,936 + (161 + 3) x 8 x 96 + 384 = 190,272 planned rows, and its own
#: seed domain.
REVISION_CONFIG_2_1 = replace(
    REVISION_CONFIG, topic_bank="v3", carry_mode="all",
    carry_max_references=161,
    stage2_max_cells=1320, max_total_rows=192000,
    seed_domain="dci.batch1:gen:v2.1")

CONFIGS = {"v1": DEFAULT_CONFIG, "v2": REVISION_CONFIG,
           "v2.1": REVISION_CONFIG_2_1}


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


def implementation(decision_id: str, extra: tuple[str, ...] = ()
                   ) -> dict[str, str]:
    """Package modules resolve under the package; ``dci/...`` under src."""
    names = IMPLEMENTATION[decision_id] + tuple(
        n for n in extra if n not in IMPLEMENTATION[decision_id])
    return {name: code_hash(_SRC.parent / name if name.startswith("dci/")
                            else _PKG / name)
            for name in names}


def _fields(cfg: PilotConfig, *names: str) -> dict[str, Any]:
    state = cfg.state()
    return {k: state[k] for k in names}


def _topic_payload(cfg: PilotConfig) -> dict[str, Any]:
    from dci.batch1 import topics as TOP
    split = TOP.split_for(cfg)
    if cfg.topic_bank in ("v2", "v3"):
        sources, review, semantic, _ = TOP.bank_paths(cfg.topic_bank)
        return {"bank": cfg.topic_bank, "bank_hash": split.bank_hash,
                "split_hash": split.split_hash,
                "historical_sources": sorted(sources),
                "screen": {"wordset": TOP.WORDSET_SCREEN,
                           "content": TOP.CONTENT_SCREEN,
                           "rare_stem_df": TOP.RARE_STEM_DF,
                           "rare_stem_min_shared": TOP.RARE_STEM_MIN_SHARED,
                           "rare_stem_min_letters": TOP.RARE_STEM_MIN_LETTERS},
                "review_hash": sha_file(review),
                "semantic_review_hash": sha_file(semantic)}
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
    v2 = cfg.protocol == "v2"

    def extra(*names: str, **values: Any) -> dict[str, Any]:
        """Protocol-v2 fields; v1 payloads are unchanged by the revision."""
        return {**_fields(cfg, *names), **values} if v2 else {}

    texts = _v2_texts(cfg) if v2 else {}

    def d(decision_id, title, origin, summary, payload):
        title, summary = texts.get(decision_id, (title, summary))
        return Decision(decision_id, title, origin, summary,
                        {**payload,
                         "implementation": implementation(
                             decision_id, extra=V2_IMPLEMENTATION.get(
                                 decision_id, ()) if v2 else ()),
                         "orchestrator_python": ORCHESTRATOR_PYTHON})

    return (
        d("D01", f"Parameters of the {len(proposed)} proposed variants",
          "proposed",
          f"Concrete targets, counts and minima for the {len(proposed)} "
          "slots the design left open"
          + (" (library v2: the v1 slots plus the R1 additions)." if v2
             else "."),
          {c.cid: c.spec_hash for c in proposed}),
        d("D02", "The two wording frames and the prompt", "proposed",
          "F0 imperative, F1 requirement; A's strings are v8.1 A "
          "frames 0/1, B's are historical B wordings 1/0; the carried "
          "DCI-1 prompt template with one numbered instruction.",
          {"templates": {k: f.state()["templates"]
                         for k, f in sorted(L.FAMILIES.items())},
           "frames": list(cfg.frames), "prompt_zero": PROMPT_ZERO,
           "prompt_one": PROMPT_ONE,
           **extra("library_version", quoted_targets=True,
                   renderings={c.cid: {f: c.render(f) for f in L.FRAMES}
                               for c in L.all_constraints()})}),
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
           "topics": _topic_payload(cfg), **extra("topic_bank")}),
        d("D06", "Stage 2 refinement rule and stage completeness", "proposed",
          "One bounded round, selected only from complete, authenticated "
          "Stage 1 evidence: boundary cells ranked by class, then by "
          "standardised distance to the boundary; 64 new-topic responses "
          "each; at most stage2_max_cells cells. Finalisation needs both "
          "stages complete; there is no partial-completion rule.",
          {**_fields(cfg, "stage2_topics", "stage2_draws", "stage2_max_cells",
                  "z", "a_headroom_band", "b_informative_band",
                  "eligibility_threshold", "extension_threshold",
                  "matching_tolerance", "min_cell_fraction"),
           **extra("protocol", "carry_mode", "carry_min_posterior",
                   "carry_max_references", "max_total_rows")}),
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
          {**_fields(cfg, "a_counts", "a_headroom_band",
                  "a_min_informative_model_frames",
                  "a_min_informative_models", "preferred_a_count"),
           **extra("fixed_a")}),
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
          {**_fields(cfg, "matching_tolerance"),
           **extra(reporting=V2_MATCHING_REPORTS)}),
        d("D11", "Coverage requirements", "design",
          "Design minima for G1, P1 and P2 and the 12-of-16 target; P3 "
          "needs 3 additional other-operation references (researcher's "
          "decision 2026-10-25; the design value was 2) and |G3| >= "
          "p3_min_g3.",
          {**_fields(cfg, "g1_min_distinct_words", "p1_min_additional",
                  "p2_min_additional_other_object",
                  "p3_min_additional_other_operation", "p3_min_g3",
                  "feasibility_min_configs", "feasibility_min_models"),
           **extra("forecast_min_feasible", "forecast_draws", "forecast_seed")}),
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
           "operations": {c.cid: c.operation for c in refs},
           **extra("weights_mode")}),
        d("D14", "Membership-stability diagnostics", "proposed",
          "Topic-cluster bootstrap of the pilot: inclusion frequency per "
          "reference, A/B selection and FEASIBLE shares, borderline "
          "matches, and feasibility on majority-stable members; a record "
          "(not a flag) of how close a FEASIBLE verdict's weakest contrast "
          "is to the target, within near_threshold_margin. Diagnostic "
          "only, never a gate: membership stays the point-estimate rule; "
          "instability is flagged for review, never auto-corrected.",
          {**_fields(cfg, "stability_replicates", "stability_seed",
                  "stability_unstable_band", "stability_stable_threshold",
                  "stability_min_feasible_share", "near_threshold_margin"),
           **extra("truncation_review_min_rows")}),
    )


#: R5(a): matching reported beside the primary +/-0.10 rule; never deciding.
V2_MATCHING_REPORTS = {"tolerances": [0.15, 0.20],
                       "confident": "Newcombe interval inside +/-0.10",
                       "iota": "task-only kappa corrected, +/-0.10",
                       "posterior_match": "Beta(k+1, n-k+1) draws on T2"}

#: Protocol v2's rule code, bound to the decisions it implements (audit M2):
#: an edit to it voids those approvals, not only Freeze 1.
V2_IMPLEMENTATION = {
    "D06": ("revision.py", "runner.py"), "D07": ("revision.py",),
    "D08": ("revision.py",), "D10": ("revision.py",),
    "D11": ("revision.py", "compatibility.py"), "D14": ("revision.py",),
}


def _v2_texts(cfg: PilotConfig) -> dict[str, tuple[str, str]]:
    """Titles and summaries that describe protocol v2 (audit M2: the v2
    approvals were given against v1's texts)."""
    measured = ("every reference in the library" if cfg.carry_mode == "all"
                else "the carried set (compatible, plausibly eligible "
                     "references with posterior P(match) >= "
                     "carry_min_posterior in some model-frame, at most "
                     "carry_max_references)")
    return {
        "D05": (f"Topic bank {cfg.topic_bank} and its split",
                (f"The 144 topics of bank v3, written fresh for v2.1 "
                 "(distinct from bank v1 with its 480 reserved topics, and "
                 "from bank v2, whose topics the v2 run of 2026-10-26 "
                 "measured)" if cfg.topic_bank == "v3" else
                 "The 144 topics of bank v2 (written for v2; distinct from "
                 "bank v1 and its 480 reserved topics)")
                + ", in 12 areas, split by a fixed seed into T1 (48 topics, "
                "Stage A screening; one response per stand-alone and "
                "task-only cell) and T2 (96 topics, Stage C membership); none "
                "reserved. Screened against the historical banks and every "
                "earlier Batch 1 bank, by word overlap and a blind semantic "
                "review; bank v1's 480 reserved topics stay unused, for the "
                "confirmatory study."),
        "D06": ("Stages A-D, forecast, early stop and what T2 measures",
                "Stage A measures every reference, A x 4/5/6, B 8 and 10 and "
                "the task alone on T1. Stage B draws each T1 cell from its "
                "Beta posterior and applies D08-D11 with the fixed-A and "
                "fixed-B gates. Early stop: if P(feasible) < "
                "forecast_min_feasible for any one contrast, the whole run "
                "stops before T2 (no T2 data for any contrast) and the "
                "verdict names the reason: EARLY_STOP_LIBRARY_LIMITED (the "
                "library cannot reach the target; R9 applies), "
                "EARLY_STOP_FIXED_A_OR_B (the fixed A or B fails its own "
                "gate), or EARLY_STOP_JOINT. Otherwise Stage C measures "
                f"{measured}, plus A x 6, B 8 and 10 and the task alone, one "
                "response per T2 topic. T2 alone decides eligibility, "
                "matching and membership; T1 never enters them. No C' "
                "top-up. Both stages must be complete (no partial-completion "
                "rule). Accounting: max_total_rows bounds every generation "
                "attempt in the pilot root, evidence and technical retries "
                "alike, in Stages A and C. The Stage C plan is refused if "
                "Stage A plus the plan does not fit, and every execute or "
                "resume is refused if the attempts already made plus the "
                "rows it would request exceed it; retries (at most "
                "max_technical_attempts per row) can use only the headroom "
                "left by the plan. The smoke test (its own root, at most 96 "
                "rows) is outside the bound and reported separately."),
        "D07": ("B fixed at 8 and 10, checked on T2",
                "B is fixed (R4), not selected. On T2 each limit must be "
                "informative (B-only compliance inside b_informative_band) "
                "in >= b_min_informative_model_frames model-frames, or the "
                "verdict is B_NOT_INFORMATIVE."),
        "D08": ("A fixed at however x 6, checked on T2",
                "A is fixed (R3), not selected; A x 4 and x 5 are measured "
                "on T1 as diagnostics only. On T2, A must be informative "
                "(p_A inside a_headroom_band) in >= "
                "a_min_informative_model_frames model-frames across >= "
                "a_min_informative_models models, or the verdict is "
                "A_NOT_ADMISSIBLE. Uninformative-A configurations never "
                "count toward feasibility; a G1 count below the target is "
                "flagged A_COVERAGE_INADEQUATE."),
        "D09": ("Eligibility operationalisation",
                "Point estimate >= 20% in at least one model-frame, on the "
                "T2 responses of that cell only; 10% extension reported "
                "separately. The OR over eight cells admits candidates whose "
                "true rate is below 20% (disclosed)."),
        "D10": ("Matching operationalisation",
                "|p_X - p_A| <= 0.10 per model-frame on raw T2 compliance, in "
                "exact arithmetic (primary, deciding). Reported beside it, "
                "never deciding (R5): posterior P(match) per reference and "
                "model-frame, and coverage under +/-0.15, +/-0.20, confident "
                "matching (Newcombe interval inside +/-0.10) and iota "
                "matching."),
        "D11": ("Coverage requirements",
                "Design minima for G1 (3 distinct words), P1 (G2 adds 2) and "
                "P2 (G3 adds 2 other-object references). P3 is stricter than "
                "the design (the researcher's decision of 2026-10-25): G5 "
                "adds 3 other-operation references, not 2, and |G3| >= "
                "p3_min_g3 (3). Feasibility needs 12 of 16 configurations, 3 "
                "models and both B limits (unchanged). Pools are eligible "
                "references logically compatible with the configuration's B "
                "limit. Stage B's forecast uses exactly these rules."),
        "D13": ("Object types and hierarchical weights",
                "Object types as in v1 plus library v2's (numerals, "
                "sentence and paragraph ladders, positional); weights equal "
                "over operations, then object types, then, inside an "
                "exact-word-count group, equal over target words and then "
                "over a word's count variants (R10)."),
        "D14": ("Membership-stability diagnostics, their review, and "
                "T1-T2 agreement",
                "Topic-cluster bootstrap on T2: inclusion frequency, "
                "FEASIBLE share, borderline matches, feasibility on "
                "majority-stable members; a near-threshold record; a "
                "truncation review of cells above truncation_review_share "
                "with >= truncation_review_min_rows truncated rows (R11). "
                "Also reported: T1-versus-T2 agreement (eligibility, "
                "matching, forecast against verdict). Review rule (the "
                "researcher's of 2026-10-25, DECISIONS_2026-10-25.md): every "
                "Freeze 2 flag blocks Batch 2 until the researcher reviews "
                "it, including FEASIBILITY_UNSTABLE and any truncation-review "
                "cell; only MEMBERSHIP_UNSTABLE proceeds, with disclosure. "
                "Nothing is auto-corrected and no threshold is changed in "
                "response to a result."),
    }


def decision_payloads(cfg: PilotConfig = DEFAULT_CONFIG) -> dict[str, str]:
    return {d.decision_id: d.payload_hash for d in decisions(cfg)}
