"""Resolved engine configuration is golden-filed, per checkpoint.

`resolve_engine` is a pure function of (ModelCard, HostProfile, overrides), so
the exact kwargs every checkpoint resolves to can be asserted on CPU CI with no
GPU stack installed. Configuration drift becomes a failing diff rather than a
silently different run.

These goldens encode the configuration the archived runs used. Changing one is
a change of execution condition and should be a deliberate, reviewed edit.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vllm_backend.hardware import HostProfile                   # noqa: E402
from vllm_backend.plan import SamplingPlan                      # noqa: E402
from vllm_backend.registry import REGISTRY, ReasoningMode, get  # noqa: E402
from vllm_backend.resolve import (UnsupportedConfiguration,     # noqa: E402
                                  context_envelope, resolve_engine,
                                  resolve_run, resolve_sampling)

#: The workstation: two RX 7900 XTX (gfx1100). FP8/MX unavailable on RDNA3.
WORKSTATION = HostProfile(
    device_count=2, gcn_archs=("gfx1100", "gfx1100"),
    device_names=("Radeon RX 7900 XTX",) * 2, total_vram_gib=(23.98, 23.98),
    supports_fp8=False, supports_mx=False, use_custom_allreduce=False,
    is_navi=True, vllm_version="0.15.1", platform_class="RocmPlatform")

#: Every checkpoint resolves to this on the workstation at TP=2, differing only
#: in the fields the card genuinely owns.
EXPECTED_TP2 = {
    "Qwen/Qwen3.5-4B": {
        "model": "Qwen/Qwen3.5-4B", "dtype": "bfloat16",
        "tensor_parallel_size": 2, "max_model_len": 40960,
        "gpu_memory_utilization": 0.85, "disable_custom_all_reduce": True,
        "enforce_eager": True, "seed": 20260812, "trust_remote_code": False,
    },
    "Qwen/Qwen3.5-9B": {
        "model": "Qwen/Qwen3.5-9B", "dtype": "bfloat16",
        "tensor_parallel_size": 2, "max_model_len": 40960,
        "gpu_memory_utilization": 0.85, "disable_custom_all_reduce": True,
        "enforce_eager": True, "seed": 20260812, "trust_remote_code": False,
    },
    "google/gemma-4-E4B-it": {
        "model": "google/gemma-4-E4B-it", "dtype": "bfloat16",
        "tensor_parallel_size": 2, "max_model_len": 40960,
        "gpu_memory_utilization": 0.85, "disable_custom_all_reduce": True,
        "enforce_eager": True, "seed": 20260812, "trust_remote_code": False,
    },
    "google/gemma-4-12B-it": {
        "model": "google/gemma-4-12B-it", "dtype": "bfloat16",
        "tensor_parallel_size": 2, "max_model_len": 40960,
        "gpu_memory_utilization": 0.85, "disable_custom_all_reduce": True,
        "enforce_eager": True, "seed": 20260812, "trust_remote_code": False,
    },
    "moonshotai/Kimi-VL-A3B-Thinking-2506": {
        "model": "moonshotai/Kimi-VL-A3B-Thinking-2506", "dtype": "bfloat16",
        "tensor_parallel_size": 2, "max_model_len": 40960,
        "gpu_memory_utilization": 0.85, "disable_custom_all_reduce": True,
        "enforce_eager": True, "seed": 20260812, "trust_remote_code": True,
        "limit_mm_per_prompt": {"image": 0},
    },
}


@pytest.mark.parametrize("model_id", sorted(EXPECTED_TP2))
def test_resolved_engine_kwargs_match_the_golden(model_id: str) -> None:
    plan = resolve_engine(get(model_id), WORKSTATION,
                          {"tensor_parallel_size": 2})
    assert plan.engine_kwargs() == EXPECTED_TP2[model_id]


def test_every_registered_checkpoint_has_a_golden() -> None:
    """A new checkpoint must arrive with its configuration pinned."""
    assert set(REGISTRY) == set(EXPECTED_TP2), (
        "a checkpoint was added to or removed from the registry without "
        "updating the resolved-configuration goldens")


def test_revision_is_carried_into_the_engine_kwargs() -> None:
    plan = resolve_engine(get("Qwen/Qwen3.5-4B"), WORKSTATION,
                          {"model_revision": "a" * 40})
    assert plan.engine_kwargs()["revision"] == "a" * 40


def test_optional_kwargs_are_omitted_rather_than_passed_as_none() -> None:
    """vLLM distinguishes a missing kwarg from an explicit None, and the
    archived runs omitted these."""
    kwargs = resolve_engine(get("Qwen/Qwen3.5-4B"), WORKSTATION).engine_kwargs()
    assert "revision" not in kwargs
    assert "cpu_offload_gb" not in kwargs
    assert "limit_mm_per_prompt" not in kwargs


def test_tp_beyond_visible_devices_is_refused() -> None:
    single = HostProfile(device_count=1, gcn_archs=("gfx1100",))
    with pytest.raises(UnsupportedConfiguration, match="exceeds"):
        resolve_engine(get("Qwen/Qwen3.5-4B"), single,
                       {"tensor_parallel_size": 2})


def test_unknown_override_is_refused_rather_than_ignored() -> None:
    """A typo'd knob must not be silently dropped — that is how a run ends up
    executing a condition nobody chose."""
    with pytest.raises(UnsupportedConfiguration, match="unknown engine overrides"):
        resolve_engine(get("Qwen/Qwen3.5-4B"), WORKSTATION,
                       {"tensor_paralell_size": 2})


def test_bf16_is_forced_where_the_hardware_cannot_do_fp8() -> None:
    plan = resolve_engine(get("Qwen/Qwen3.5-4B"), WORKSTATION)
    assert plan.dtype == "bfloat16"
    assert plan.quantization == "none"


def test_declared_remote_code_must_match_the_probe() -> None:
    """A checkpoint that ships custom modeling code cannot be run with
    trust_remote_code=False by accident."""
    with pytest.raises(UnsupportedConfiguration, match="auto_map"):
        resolve_engine(get("Qwen/Qwen3.5-4B"), WORKSTATION,
                       capabilities={"needs_remote_code": True})


class TestSamplingDefaults:
    """The frozen DCI decoding condition, in one place."""

    def test_defaults(self) -> None:
        sampling = resolve_sampling(max_tokens=8192)
        assert (sampling.temperature, sampling.top_p) == (0.7, 0.9)
        # top-k OFF: vLLM disables it with <= 0, and Transformers' default of
        # 50 is NOT the canonical condition.
        assert sampling.top_k == -1
        assert sampling.answer_tokens == 512

    def test_single_phase_uses_no_stop_string(self) -> None:
        """One uninterrupted generation: the model closes its own reasoning."""
        assert resolve_sampling(max_tokens=8192).stop == ()

    def test_zero_budget_is_refused(self) -> None:
        with pytest.raises(UnsupportedConfiguration, match="no room"):
            resolve_sampling(max_tokens=0)


class TestRunPlan:
    def test_unsupported_mode_is_refused_not_emulated(self) -> None:
        """Kimi-VL has no non-thinking mode; its sibling is a different
        checkpoint. That cell must be missing, never fabricated."""
        card = get("moonshotai/Kimi-VL-A3B-Thinking-2506")
        with pytest.raises(UnsupportedConfiguration, match="does not natively support"):
            resolve_run(card, ReasoningMode.NO_THINKING)

    def test_unknown_strategy_is_refused(self) -> None:
        with pytest.raises(UnsupportedConfiguration, match="unknown strategy"):
            resolve_run(get("Qwen/Qwen3.5-4B"),
                        ReasoningMode.NATURAL_REASONING, strategy="splice")

    def test_template_kwargs_follow_the_mode(self) -> None:
        card = get("google/gemma-4-E4B-it")
        thinking = resolve_run(card, ReasoningMode.NATURAL_REASONING)
        not_thinking = resolve_run(card, ReasoningMode.NO_THINKING)
        assert thinking.chat_template_kwargs == {"enable_thinking": True}
        assert not_thinking.chat_template_kwargs == {"enable_thinking": False}


class TestContextEnvelope:
    def test_arithmetic_matches_the_documented_formula(self) -> None:
        # 40960 - 1000 - 512 - 8 - ceil(40960*0.02)=820  ->  38620
        assert context_envelope(40960, 1000, 512, 8, 0.02) == 38620

    def test_an_envelope_with_no_room_is_refused(self) -> None:
        with pytest.raises(UnsupportedConfiguration, match="no room"):
            context_envelope(2048, 2000, 512, 8, 0.02)


def test_sampling_plan_round_trips_through_json() -> None:
    """The plan crosses a process boundary as JSON; it must survive intact."""
    original = SamplingPlan(max_tokens=4096, answer_tokens=256,
                            stop=("</think>",))
    assert SamplingPlan.from_dict(original.to_dict()) == original


class TestPreflightFailsOpen:
    """A probe that cannot answer must NOT block a runnable checkpoint.

    Regression: the first version of `capabilities.probe` called
    `ModelRegistry.is_text_generation_model([arch])`, which on vLLM 0.15.1
    requires a fully built `ModelConfig` and therefore raised. The exception was
    swallowed per-architecture, leaving `supported == []`, and `vllm_supported`
    was set to `bool([]) == False`. Preflight then blocked
    Qwen2.5-0.5B-Instruct — a model that runs perfectly — as
    BACKEND_UNSUPPORTED. Only a DEFINITE negative may block.
    """

    def _card_and_plan(self):
        card = get("Qwen/Qwen3.5-4B")
        return card, resolve_engine(card, WORKSTATION)

    def test_unknown_support_does_not_block(self) -> None:
        from vllm_backend.capabilities import preflight

        card, plan = self._card_and_plan()
        ok, outcome, _ = preflight(card, plan, WORKSTATION,
                                   {"vllm_supported": None,
                                    "architectures": ["Qwen3ForCausalLM"]})
        assert ok, "an unanswerable probe must not block the run"

    def test_definite_negative_does_block(self) -> None:
        from vllm_backend.capabilities import preflight
        from vllm_backend.contract import Outcome

        card, plan = self._card_and_plan()
        ok, outcome, detail = preflight(card, plan, WORKSTATION,
                                        {"vllm_supported": False,
                                         "architectures": ["MadeUpForCausalLM"]})
        assert not ok
        assert outcome == Outcome.BACKEND_UNSUPPORTED.value
        assert "MadeUpForCausalLM" in detail

    def test_absent_probe_does_not_block(self) -> None:
        from vllm_backend.capabilities import preflight

        card, plan = self._card_and_plan()
        ok, _, _ = preflight(card, plan, WORKSTATION, None)
        assert ok

    def test_missing_parser_warns_but_does_not_block(self) -> None:
        """A card naming a parser the build lacks falls back to delimiters."""
        from vllm_backend.capabilities import preflight

        card, plan = self._card_and_plan()
        ok, _, detail = preflight(card, plan, WORKSTATION,
                                  {"vllm_supported": True,
                                   "reasoning_parser_available": False})
        assert ok
        assert "delimiters" in detail
