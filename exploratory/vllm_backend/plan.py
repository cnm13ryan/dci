"""Engine and sampling configuration as pure, JSON-round-trippable data.

Stdlib only. This is the payload that crosses the process boundary: the
scientific environment writes an `EnginePlan` to `plan.json`, and the backend
environment reconstructs it. Keeping it a dataclass rather than a loose dict is
what lets `test_engine_config.py` golden-file the resolved configuration.

Every knob that used to be re-typed at eight call sites lives here exactly once.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

#: Decoding constants shared by every DCI generation. These were duplicated
#: verbatim in all eight backend scripts; a drift in any one of them would have
#: been an unlogged change of experimental condition.
TEMPERATURE = 0.7
TOP_P = 0.9
#: vLLM disables top-k with <= 0. Transformers defaults it to 50 and vLLM does
#: not, so the canonical run leaves it OFF and says so rather than relying on a
#: backend default.
TOP_K = -1


@dataclass(frozen=True)
class EnginePlan:
    """Everything `LLM(...)` is constructed from. Hardware + envelope, no science."""

    model_id: str
    model_revision: str = ""

    # ---- dtype and numerics -------------------------------------------------
    #: BF16 throughout. On gfx1100 this is not a preference: vLLM's
    #: `RocmPlatform.supports_fp8()` gates on gfx94/gfx95/gfx12 and
    #: `supports_mx()` on gfx95, so FP8 and MX are unavailable on RDNA3 and a
    #: quantised run would be a different numerical experiment anyway.
    dtype: str = "bfloat16"
    quantization: str = "none"

    # ---- hardware -----------------------------------------------------------
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.85
    #: Kept True to preserve the recorded engine kwargs of every prior run.
    #: NOTE (verified against the installed wheel):
    #: `RocmPlatform.use_custom_allreduce()` returns True only for gfx94/gfx95,
    #: so on this gfx1100 host custom all-reduce is already off and this flag is
    #: a no-op. It is retained because it appears in archived provenance, not
    #: because it does anything here.
    disable_custom_all_reduce: bool = True
    #: Eager on RDNA3. Also what every prior run used.
    enforce_eager: bool = True
    #: Per-GPU weight offload. 0 disables. BF16 either way — this trades
    #: bandwidth for VRAM, it does not change the numbers the model holds.
    cpu_offload_gb: float = 0.0

    # ---- envelope -----------------------------------------------------------
    #: PRACTICAL context envelope, never the architecture's advertised maximum.
    max_model_len: int = 40960
    #: Engine-level seed. Per-request seeds live on the request, not here.
    seed: int = 20260812

    # ---- checkpoint-specific, declarative ----------------------------------
    trust_remote_code: bool = False
    #: Text-only knob for multimodal checkpoints: stops vLLM reserving
    #: multimodal cache the DCI prompts never use. vLLM's own supported option.
    limit_mm_per_prompt: dict[str, int] | None = None

    def engine_kwargs(self) -> dict[str, Any]:
        """The exact kwargs handed to `LLM(...)`. The only place they are built."""
        kwargs: dict[str, Any] = {
            "model": self.model_id,
            "dtype": self.dtype,
            "tensor_parallel_size": self.tensor_parallel_size,
            "max_model_len": self.max_model_len,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "disable_custom_all_reduce": self.disable_custom_all_reduce,
            "enforce_eager": self.enforce_eager,
            "seed": self.seed,
            "trust_remote_code": self.trust_remote_code,
        }
        # Optional kwargs are omitted rather than passed as None: vLLM treats a
        # missing kwarg and an explicit None differently for some options, and
        # the archived runs omitted them.
        if self.model_revision:
            kwargs["revision"] = self.model_revision
        if self.cpu_offload_gb:
            kwargs["cpu_offload_gb"] = float(self.cpu_offload_gb)
        if self.limit_mm_per_prompt:
            kwargs["limit_mm_per_prompt"] = dict(self.limit_mm_per_prompt)
        return kwargs

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnginePlan:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True)
class SamplingPlan:
    """Decoding parameters. Per-request seeds are supplied at generate time."""

    temperature: float = TEMPERATURE
    top_p: float = TOP_P
    top_k: int = TOP_K
    #: Total tokens a request may produce. For the single-phase strategy this
    #: covers reasoning AND answer together.
    max_tokens: int = 8192
    #: Answer allowance for the two-phase splice strategy. Identical in every
    #: treatment so the verifier sees a comparable surface at every budget.
    answer_tokens: int = 512
    #: Stop strings. The single-phase strategy uses NONE by design: one
    #: uninterrupted generation, the model closes its own reasoning.
    stop: tuple[str, ...] = ()
    include_stop_str_in_output: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stop"] = list(self.stop)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SamplingPlan:
        known = {f.name for f in fields(cls)}
        payload = {k: v for k, v in data.items() if k in known}
        if "stop" in payload and payload["stop"] is not None:
            payload["stop"] = tuple(payload["stop"])
        return cls(**payload)


@dataclass(frozen=True)
class RunPlan:
    """Execution policy: how the run is paced and when it gives up.

    Chunking and the deadline are engineering, not science. They decide which
    rows get attempted, never what a generated row contains.
    """

    #: Requests per `llm.generate` call; each chunk is appended as it finishes
    #: so a stopped run still leaves every completed row on disk.
    chunk_size: int = 32
    #: Whole-run wall-clock backstop. Rows past it are recorded NOT_GENERATED.
    deadline_seconds: float | None = None
    #: Kwargs forwarded to `apply_chat_template`.
    chat_template_kwargs: dict[str, Any] = field(default_factory=dict)
    #: Generation strategy: "single_phase" or "two_phase_splice".
    strategy: str = "single_phase"
    #: The experimental condition. Decides how output is split: a NO_THINKING
    #: run has NO reasoning channel, so the whole generation is the answer and
    #: applying a delimiter parser to it would mark every row CHANNEL_INVALID.
    reasoning_mode: str = "NATURAL_REASONING"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunPlan:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
