"""(ModelCard, HostProfile, overrides) -> EnginePlan. A PURE function.

No torch, no vLLM, no I/O — which is the point. Because resolution is pure,
`test_engine_config.py` can golden-file the exact configuration every checkpoint
resolves to and run on CPU CI with no GPU stack present. Configuration drift
becomes a failing diff instead of a silently different run.

This is also where "model-specific" claims get demoted. Anything that is really
a hardware decision (TP size, memory utilisation, eager mode, dtype) or a
capability decision (multimodal cache limits) is decided HERE from the host and
the probe, not from the checkpoint's name.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from vllm_backend.hardware import HostProfile
from vllm_backend.plan import EnginePlan, RunPlan, SamplingPlan
from vllm_backend.registry import ModelCard

#: Fields a caller may legitimately override per run. Anything outside this set
#: is a mistake rather than a knob, and `resolve_engine` says so.
ALLOWED_OVERRIDES = frozenset({
    "tensor_parallel_size", "gpu_memory_utilization", "max_model_len",
    "cpu_offload_gb", "seed", "enforce_eager", "dtype", "model_revision",
    "disable_custom_all_reduce",
})


class UnsupportedConfiguration(ValueError):
    """A configuration this host or build cannot serve. Caller records an
    outcome; it is not a crash."""


def resolve_engine(card: ModelCard, host: HostProfile,
                   overrides: dict[str, Any] | None = None,
                   capabilities: dict[str, Any] | None = None) -> EnginePlan:
    """Build the engine plan for one checkpoint on one host.

    `capabilities` is the output of `capabilities.probe()` when available. It is
    optional so plan-building works in the scientific environment, which has no
    vLLM to ask.
    """
    overrides = dict(overrides or {})
    unknown = set(overrides) - ALLOWED_OVERRIDES
    if unknown:
        raise UnsupportedConfiguration(
            f"unknown engine overrides {sorted(unknown)}; "
            f"allowed: {sorted(ALLOWED_OVERRIDES)}")

    plan = EnginePlan(
        model_id=card.model_id,
        max_model_len=card.max_model_len,
        trust_remote_code=card.trust_remote_code,
    )

    # -- multimodal cache: a CAPABILITY decision, not a per-model exception ---
    # The card carries the limit, but it is only applied when something
    # actually knows the architecture is multimodal. Where no probe ran we keep
    # the card's value, because omitting it only costs VRAM and never changes
    # numerics.
    if card.limit_mm_per_prompt:
        if capabilities is None or capabilities.get("is_multimodal", True):
            plan = replace(plan, limit_mm_per_prompt=dict(card.limit_mm_per_prompt))

    # -- dtype: a HARDWARE decision on this host -----------------------------
    # FP8/MX are unavailable on RDNA3 (vLLM gates them on gfx94/gfx95/gfx12),
    # so bf16 is not a preference here, it is the only option. Stated rather
    # than assumed so a future gfx950 host does not silently inherit it.
    if host.gcn_archs and not host.supports_fp8:
        plan = replace(plan, dtype="bfloat16", quantization="none")

    # -- remote code: derived, then asserted against the declaration ----------
    if capabilities is not None and "needs_remote_code" in capabilities:
        needed = bool(capabilities["needs_remote_code"])
        if needed and not card.trust_remote_code:
            raise UnsupportedConfiguration(
                f"{card.model_id} declares auto_map (custom modeling code) but "
                f"its ModelCard sets trust_remote_code=False")
        plan = replace(plan, trust_remote_code=needed or card.trust_remote_code)

    for key, value in overrides.items():
        plan = replace(plan, **{key: value})

    if plan.tensor_parallel_size > max(host.device_count, 1):
        raise UnsupportedConfiguration(
            f"tensor_parallel_size={plan.tensor_parallel_size} exceeds the "
            f"{host.device_count} visible device(s)")
    if plan.max_model_len <= 0:
        raise UnsupportedConfiguration(
            f"max_model_len={plan.max_model_len} is not a usable envelope")
    return plan


def resolve_sampling(max_tokens: int, answer_tokens: int = 512,
                     stop: tuple[str, ...] = (),
                     overrides: dict[str, Any] | None = None) -> SamplingPlan:
    """Decoding parameters. Defaults are the frozen DCI condition."""
    plan = SamplingPlan(max_tokens=int(max_tokens),
                        answer_tokens=int(answer_tokens),
                        stop=tuple(stop),
                        include_stop_str_in_output=False)
    for key, value in (overrides or {}).items():
        plan = replace(plan, **{key: value})
    if plan.max_tokens <= 0:
        raise UnsupportedConfiguration(
            f"max_tokens={plan.max_tokens} leaves no room to generate")
    return plan


def resolve_run(card: ModelCard, reasoning_mode: str,
                strategy: str = "single_phase",
                chunk_size: int = 32,
                deadline_seconds: float | None = None) -> RunPlan:
    """Execution policy plus the checkpoint's template kwargs for this mode."""
    if not card.supports(reasoning_mode):
        raise UnsupportedConfiguration(
            f"{card.model_id} does not natively support {reasoning_mode}; "
            f"supported: {list(card.supported_modes)}. An unsupported mode is "
            f"a missing cell, never something to emulate.")
    if strategy not in ("single_phase", "two_phase_splice"):
        raise UnsupportedConfiguration(f"unknown strategy {strategy!r}")
    return RunPlan(chunk_size=int(chunk_size),
                   deadline_seconds=deadline_seconds,
                   chat_template_kwargs=card.template_kwargs(reasoning_mode),
                   strategy=strategy,
                   reasoning_mode=reasoning_mode)


def context_envelope(max_model_len: int, longest_prompt_tokens: int,
                     answer_tokens: int, control_tokens: int = 0,
                     safety_fraction: float = 0.02) -> int:
    """The non-binding ceiling the context window allows.

    Deliberately NOT rounded to a power of two: a round number would be a guess
    about how much room is enough, and what this condition requires is a limit
    derived from the envelope that the model almost never touches.
    """
    import math

    safety = math.ceil(max_model_len * safety_fraction)
    ceiling = (max_model_len - longest_prompt_tokens - answer_tokens
               - control_tokens - safety)
    if ceiling <= 0:
        raise UnsupportedConfiguration(
            f"context envelope leaves no room for reasoning: "
            f"{max_model_len} - {longest_prompt_tokens} - {answer_tokens} - "
            f"{control_tokens} - {safety} = {ceiling}")
    return ceiling
