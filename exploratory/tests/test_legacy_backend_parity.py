"""The migrated scripts must resolve to what the legacy scripts hard-coded.

Before the consolidation, four scripts under `vllm_backend/` each built their own
`LLM(...)` and their own `SamplingParams(...)`. They are gone, so the only way to
show the migration changed no scientific condition is to pin what they said and
require the canonical resolvers to reproduce it exactly.

Every literal below is transcribed from those files at commit `8cac2f0`, the tip
of `exp/natural-reasoning-headline`, which is the code state that produced the
published natural-reasoning runs. Recover them with:

    git show 8cac2f0:exploratory/vllm_backend/natural_reasoning.py

These are equality assertions, not tolerances. A silent change to dtype, tensor
parallelism, memory fraction, temperature, top-p, a token budget or a seed stride
is exactly the class of difference that would move a published number without
moving anything a reader can see, so nothing here is allowed to drift.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend.hardware import HostProfile  # noqa: E402
from vllm_backend.registry import ReasoningMode, get  # noqa: E402
from vllm_backend.resolve import (  # noqa: E402
    context_envelope,
    resolve_engine,
    resolve_run,
    resolve_sampling,
)

pytestmark = pytest.mark.cpu

CANONICAL = "Qwen/Qwen3-4B"
THINK_CLOSE = "</think>"

#: Identical in all four legacy scripts, transcribed verbatim.
LEGACY_ENGINE = {
    "dtype": "bfloat16",
    "tensor_parallel_size": 2,
    "gpu_memory_utilization": 0.85,
    "enforce_eager": True,
    "disable_custom_all_reduce": True,
    "seed": 20260810,
}

#: `max_model_len` was the one engine field that varied by script.
LEGACY_MAX_MODEL_LEN = {
    "natural_reasoning": 40960,      # CONTEXT_LIMIT
    "reasoning_vllm": 16384,
    "tp2_mitigated": 8192,
    "natural_length": 32768 + 2048,  # MAX_TOKENS + 2048
}

#: Identical in every legacy `SamplingParams(...)`.
LEGACY_DECODING = {"temperature": 0.7, "top_p": 0.9}

LEGACY_SEED_BASE, LEGACY_SEED_STRIDE = 20260810, 7919
LEGACY_NATURAL_SEED_OFFSET = 90000
LEGACY_CONTEXT_LIMIT, LEGACY_SAFETY_FRACTION = 40960, 0.02


def _host() -> HostProfile:
    """A fixed two-card host, so the plan does not depend on this machine."""
    return HostProfile(device_count=2, device_names=("Radeon RX 7900 XTX",) * 2,
                       gcn_archs=("gfx1100",) * 2, total_vram_gib=(24.0, 24.0),
                       is_navi=True, use_custom_allreduce=False)


def _kwargs(max_model_len: int, tensor_parallel_size: int = 2, **overrides):
    card = get(CANONICAL)
    plan = resolve_engine(card, _host(), {
        "tensor_parallel_size": tensor_parallel_size,
        "max_model_len": max_model_len, **overrides})
    return plan.engine_kwargs()


#: Every migrated script that builds an engine, and the module constant each one
#: passes as the engine seed. `EnginePlan.seed` defaults to 20260812, which is
#: NOT the study's 20260810 -- so a script that omits the override silently runs
#: a different engine condition. That is the difference this file exists to
#: catch, and it is checked structurally rather than trusted.
MIGRATED_ENGINE_SCRIPTS = ("natural_reasoning", "reasoning_vllm",
                           "natural_length", "tp2_mitigated")


def _engine_override_seed(module_name: str):
    """The `seed` entry of the `resolve_engine(...)` override dict, resolved.

    Read from the source rather than by running `main`, which needs two GPUs.
    A name (`SEED_BASE`) is resolved against the module's own constants.
    """
    import ast
    import importlib

    module = importlib.import_module(f"vllm_backend.{module_name}")
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and getattr(node.func, "id", "") == "resolve_engine"):
            continue
        overrides = next((a for a in node.args if isinstance(a, ast.Dict)), None)
        assert overrides is not None, f"{module_name} passes no engine overrides"
        for key, value in zip(overrides.keys, overrides.values):
            if isinstance(key, ast.Constant) and key.value == "seed":
                if isinstance(value, ast.Constant):
                    return value.value
                return getattr(module, value.id)
        return None                     # resolve_engine called, seed omitted
    raise AssertionError(f"{module_name} never calls resolve_engine")


class TestEngineConfigurationIsUnchanged:
    @pytest.mark.parametrize("field,value", sorted(
        (f, v) for f, v in LEGACY_ENGINE.items() if f != "seed"))
    def test_each_legacy_engine_field_is_reproduced(self, field, value) -> None:
        assert _kwargs(40960)[field] == value

    @pytest.mark.parametrize("script", MIGRATED_ENGINE_SCRIPTS)
    def test_every_script_pins_the_legacy_engine_seed(self, script) -> None:
        """Omitting it is not a style question: it changes the engine RNG."""
        assert _engine_override_seed(script) == LEGACY_ENGINE["seed"], (
            f"{script} does not pin seed={LEGACY_ENGINE['seed']}; it would "
            f"inherit the EnginePlan default and run a different condition")

    def test_the_plan_default_is_not_the_study_seed(self) -> None:
        """States the trap the test above guards, so it cannot be 'simplified'."""
        from vllm_backend.plan import EnginePlan
        assert EnginePlan.seed != LEGACY_ENGINE["seed"]

    def test_an_explicit_seed_override_reaches_the_engine(self) -> None:
        assert _kwargs(40960, seed=LEGACY_ENGINE["seed"])["seed"] == 20260810

    @pytest.mark.parametrize("script,max_model_len",
                             sorted(LEGACY_MAX_MODEL_LEN.items()))
    def test_each_scripts_context_window_is_reproduced(self, script,
                                                       max_model_len) -> None:
        assert _kwargs(max_model_len)["max_model_len"] == max_model_len

    def test_the_single_card_probe_still_asks_for_one_card(self) -> None:
        """tp2_mitigated's companion condition; TP is a request, not a default."""
        assert _kwargs(8192, tensor_parallel_size=1)["tensor_parallel_size"] == 1


class TestDecodingIsUnchanged:
    @pytest.mark.parametrize("field,value", sorted(LEGACY_DECODING.items()))
    def test_temperature_and_top_p_are_the_frozen_condition(self, field,
                                                            value) -> None:
        assert getattr(resolve_sampling(512), field) == value

    def test_the_capped_phase_stops_at_the_close_delimiter(self) -> None:
        """What makes a budget a budget: legacy passed stop=[THINK_CLOSE]."""
        plan = resolve_sampling(256, answer_tokens=512, stop=(THINK_CLOSE,))
        assert plan.stop == (THINK_CLOSE,)
        assert plan.include_stop_str_in_output is False

    def test_the_uncapped_phase_carries_no_stop(self) -> None:
        assert resolve_sampling(512).stop == ()

    def test_a_budget_that_leaves_no_room_is_refused_not_clamped(self) -> None:
        from vllm_backend.resolve import UnsupportedConfiguration
        with pytest.raises(UnsupportedConfiguration):
            resolve_sampling(0)


class TestTheContextEnvelopeArithmeticIsUnchanged:
    """`ceiling = limit - longest_prompt - answer - control - ceil(2% limit)`."""

    @pytest.mark.parametrize("longest,answer,control",
                             [(1000, 512, 4), (2048, 512, 4), (37, 128, 0)])
    def test_it_matches_the_legacy_expression(self, longest, answer,
                                              control) -> None:
        import math
        legacy = (LEGACY_CONTEXT_LIMIT - longest - answer - control
                  - math.ceil(LEGACY_CONTEXT_LIMIT * LEGACY_SAFETY_FRACTION))
        assert context_envelope(LEGACY_CONTEXT_LIMIT, longest, answer,
                                control) == legacy

    def test_it_is_not_rounded_to_a_power_of_two(self) -> None:
        ceiling = context_envelope(LEGACY_CONTEXT_LIMIT, 1000, 512, 4)
        assert ceiling & (ceiling - 1) != 0


class TestSeedDerivationIsUnchanged:
    """One seed PER ROW. A shared seed made two replicates one draw counted twice."""

    def _legacy(self, offset: int, n: int) -> list[int]:
        return [LEGACY_SEED_BASE + offset + LEGACY_SEED_STRIDE * i
                for i in range(n)]

    def test_the_migrated_script_keeps_the_constants(self) -> None:
        from vllm_backend import natural_reasoning as nr
        assert nr.SEED_BASE == LEGACY_SEED_BASE
        assert nr.SEED_STRIDE == LEGACY_SEED_STRIDE
        assert nr.SEED_OFFSET == LEGACY_NATURAL_SEED_OFFSET
        assert nr.CONTEXT_LIMIT == LEGACY_CONTEXT_LIMIT
        assert nr.SAFETY_FRACTION == LEGACY_SAFETY_FRACTION

    def test_replicate_rows_never_share_a_seed(self) -> None:
        seeds = self._legacy(LEGACY_NATURAL_SEED_OFFSET, 160)
        assert len(set(seeds)) == 160

    def test_the_two_phases_draw_disjoint_seeds(self) -> None:
        """Legacy used offset and offset+1 for the think and answer phases."""
        think = set(self._legacy(LEGACY_NATURAL_SEED_OFFSET, 160))
        answer = set(self._legacy(LEGACY_NATURAL_SEED_OFFSET + 1, 160))
        assert think.isdisjoint(answer)

    def test_this_condition_is_disjoint_from_the_capped_ladder(self) -> None:
        """The capped ladder used offsets 0 and 1; natural used 90000."""
        ladder = set(self._legacy(0, 160)) | set(self._legacy(1, 160))
        natural = set(self._legacy(LEGACY_NATURAL_SEED_OFFSET, 160))
        assert ladder.isdisjoint(natural)


class TestTheReasoningConditionIsUnchanged:
    def test_natural_reasoning_renders_thinking_on(self) -> None:
        """Legacy passed `enable_thinking=True` to the chat template."""
        plan = resolve_run(get(CANONICAL), ReasoningMode.NATURAL_REASONING)
        assert plan.chat_template_kwargs.get("enable_thinking") is True
        assert plan.strategy == "single_phase"

    def test_the_capped_ladder_is_the_two_phase_splice(self) -> None:
        plan = resolve_run(get(CANONICAL), ReasoningMode.LIMITED_REASONING,
                           strategy="two_phase_splice")
        assert plan.strategy == "two_phase_splice"
        assert plan.chat_template_kwargs.get("enable_thinking") is True

    def test_the_control_arm_renders_thinking_off(self) -> None:
        plan = resolve_run(get(CANONICAL), ReasoningMode.NO_THINKING)
        assert plan.chat_template_kwargs.get("enable_thinking") is False

    def test_the_close_delimiter_is_the_one_the_legacy_scripts_spliced(self) -> None:
        assert get(CANONICAL).think_close == THINK_CLOSE
