"""The four registered model replications (§4) and their execution order.

E2B runs first (§4); `REFERENCE_POOL_MISMATCH` or `COMPOSED_HEADROOM_FAILURE`
for E2B prevents the later replications from starting. Every revision is
fixed in the signed study-wide registration manifest before qualification;
model substitution is prohibited.

Engine settings that are operational rather than scientific (multimodal-path
workaround for the pinned ROCm wheel, per-card memory envelope) are recorded
in DECISIONS_V3.md and carried in every plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dci1v3.errors import ProtocolError


@dataclass(frozen=True)
class ModelSpec:
    """One registered model replication."""

    execution_order: int
    model_key: str
    model_id: str
    revision: str
    family: str
    thinking_policy: str            # §4 registered interpretation
    chat_template_kwargs: dict[str, Any]
    switch_expectation: str         # "live" | "inert"
    leakage_markers: tuple[str, ...]
    gpu_memory_utilization: float = 0.85
    tensor_parallel_size: int = 1
    dtype: str = "bfloat16"
    max_model_len: int = 4096
    extra: dict[str, Any] = field(default_factory=dict)


MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        execution_order=1,
        model_key="gemma-3n-e2b-it",
        model_id="google/gemma-3n-E2B-it",
        revision="5e092ebca197cdcd8d8b195040accf22693501bc",
        family="gemma3n",
        thinking_policy="unavailable",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>", "<start_of_turn>",
                         "<end_of_turn>"),
    ),
    ModelSpec(
        execution_order=2,
        model_key="qwen3-4b",
        model_id="Qwen/Qwen3-4B",
        revision="1cfa9a7208912126459214e8b04321603b3df60c",
        family="qwen3",
        thinking_policy="disabled",   # hybrid model, thinking disabled (§4)
        chat_template_kwargs={"enable_thinking": False},
        switch_expectation="live",
        leakage_markers=("<think>", "</think>"),
    ),
    ModelSpec(
        execution_order=3,
        model_key="qwen3-4b-instruct-2507",
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="cdbee75f17c01a7cc42f958dc650907174af0554",
        family="qwen3",
        thinking_policy="unavailable",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>"),
    ),
    ModelSpec(
        execution_order=4,
        model_key="gemma-3n-e4b-it",
        model_id="google/gemma-3n-E4B-it",
        revision="c1221e9c62e34a43ab7ffacd1be0ea71f126ef10",
        family="gemma3n",
        thinking_policy="unavailable",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>", "<start_of_turn>",
                         "<end_of_turn>"),
        gpu_memory_utilization=0.95,   # measured envelope on 24 GiB card
    ),
)

MODEL_BY_KEY = {m.model_key: m for m in MODELS}
MODEL_KEYS = tuple(m.model_key for m in
                   sorted(MODELS, key=lambda m: m.execution_order))
FIRST_MODEL_KEY = MODEL_KEYS[0]        # gemma-3n-e2b-it: E2B runs first

#: E2B terminal statuses that stop the remaining v3 replications (§4).
E2B_STOP_STATUSES = ("REFERENCE_POOL_MISMATCH", "COMPOSED_HEADROOM_FAILURE")


#: Judge models (amendment A2/A3): deliberately DISJOINT from the four
#: registered replications, so the autorater is never one of the models
#: it develops or evaluates the verifier against. Judges are proxy
#: instruments — never scored, never substituted for a replication, and
#: their revisions are pinned exactly like the replications'.
#: gpt-oss-20b emits harmony transcripts; the registered judging
#: condition is the checkpoint's own low reasoning effort, selected
#: through its chat template.
JUDGE_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        execution_order=0,                 # not part of the replication order
        model_key="gpt-oss-20b",
        model_id="openai/gpt-oss-20b",
        revision="6cee5e81ee83917806bbde320786a8fb61efebee",
        family="gpt-oss",
        # Medium effort: the pre-freeze A/B showed low-effort counting
        # mislabels exact-n items (systematic ±1) while medium counts
        # correctly; the judging condition is registered in the hashed
        # autorater config, which load_config validates against this spec.
        thinking_policy="medium",
        chat_template_kwargs={"reasoning_effort": "medium"},
        switch_expectation="live",
        leakage_markers=(),
    ),
)
JUDGE_BY_KEY = {m.model_key: m for m in JUDGE_MODELS}


def get_judge(model_key: str) -> ModelSpec:
    """Resolve a judge. Registered replications are deliberately NOT
    valid judges: a model must never rate the verifier that scores it."""
    if model_key not in JUDGE_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is not a registered judge model; registered "
            f"judges: {tuple(JUDGE_BY_KEY)} (the four study replications "
            f"are deliberately excluded)")
    return JUDGE_BY_KEY[model_key]


def get_model(model_key: str) -> ModelSpec:
    if model_key not in MODEL_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is not a registered model replication; "
            f"registered: {MODEL_KEYS}")
    return MODEL_BY_KEY[model_key]


def registration_models() -> list[dict[str, Any]]:
    """The model block of the signed study-wide registration manifest."""
    return [{"execution_order": m.execution_order, "model_key": m.model_key,
             "model_id": m.model_id, "revision": m.revision,
             "thinking_policy": m.thinking_policy} for m in MODELS]
