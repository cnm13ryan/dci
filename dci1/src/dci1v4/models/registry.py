"""The four registered v4 model replications (§6.1) and the judge registry.

Execution order places the two Gemma models first, because their operating
points are known from v3 and the B+R pilot and running them first exercises
the apparatus where prior operating points exist.

**No replication is blocked by the outcome of another.** The v3 early-stop
rule is withdrawn (§6.1, U11): no per-model outcome can invalidate a design
whose primary estimands need no cross-model quantity. There is deliberately no
analogue of v3's ``E2B_STOP_STATUSES`` in this module, and no function here
reads another model's record.

Revisions are re-pinned for v4 in the signed registration manifest before
qualification and asserted at every generation. They are **not** inherited
from the v3 manifest: the values below are the revisions this workstation
actually holds, recorded for v4 on its own authority, and a missing or
unavailable registered repository blocks v4 rather than triggering a
substitution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dci1v4.errors import ProtocolError


@dataclass(frozen=True)
class ModelSpec:
    """One registered model replication."""

    execution_order: int
    model_key: str
    model_id: str
    revision: str
    family: str
    thinking_policy: str            # disabled | unavailable
    chat_template_kwargs: dict[str, Any]
    switch_expectation: str         # "live" | "inert"
    leakage_markers: tuple[str, ...]
    gpu_memory_utilization: float = 0.85
    tensor_parallel_size: int = 1
    dtype: str = "bfloat16"
    max_model_len: int = 4096
    extra: dict[str, Any] = field(default_factory=dict)


#: §6.1, in registered execution order.
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
        model_key="gemma-3n-e4b-it",
        model_id="google/gemma-3n-E4B-it",
        revision="c1221e9c62e34a43ab7ffacd1be0ea71f126ef10",
        family="gemma3n",
        thinking_policy="unavailable",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>", "<start_of_turn>",
                         "<end_of_turn>"),
        gpu_memory_utilization=0.95,   # measured envelope on the 24 GiB card
    ),
    ModelSpec(
        execution_order=3,
        model_key="qwen3-4b",
        model_id="Qwen/Qwen3-4B",
        revision="1cfa9a7208912126459214e8b04321603b3df60c",
        family="qwen3",
        # Hybrid checkpoint; thinking disabled through its own supported
        # mechanism, the chat template's enable_thinking switch (§6.1).
        thinking_policy="disabled",
        chat_template_kwargs={"enable_thinking": False},
        switch_expectation="live",
        leakage_markers=("<think>", "</think>"),
    ),
    ModelSpec(
        execution_order=4,
        model_key="qwen3-4b-instruct-2507",
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="cdbee75f17c01a7cc42f958dc650907174af0554",
        family="qwen3",
        thinking_policy="unavailable",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>"),
    ),
)

MODEL_BY_KEY = {m.model_key: m for m in MODELS}
MODEL_KEYS = tuple(m.model_key for m in
                   sorted(MODELS, key=lambda m: m.execution_order))

#: §10.4: the judge registry is DISJOINT from the registered replications, so
#: an autorater never rates the verifier that scores it. Judges are proxy
#: instruments, never scored, never substituted for a replication, and their
#: revisions are pinned exactly like the replications'.
JUDGE_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        execution_order=0,
        model_key="gpt-oss-20b",
        model_id="openai/gpt-oss-20b",
        revision="6cee5e81ee83917806bbde320786a8fb61efebee",
        family="gpt-oss",
        thinking_policy="high",
        chat_template_kwargs={"reasoning_effort": "high"},
        switch_expectation="live",
        leakage_markers=(),
    ),
)
JUDGE_BY_KEY = {m.model_key: m for m in JUDGE_MODELS}


def get_model(model_key: str) -> ModelSpec:
    if model_key not in MODEL_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is not a registered v4 replication; registered: "
            f"{MODEL_KEYS}")
    return MODEL_BY_KEY[model_key]


def get_judge(model_key: str) -> ModelSpec:
    """Resolve a judge. The four study replications are deliberately not
    valid judges (§10.4)."""
    if model_key in MODEL_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is a registered study replication and can never "
            f"be its own judge; the judge registry is disjoint (§10.4)")
    if model_key not in JUDGE_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is not a registered judge; registered judges: "
            f"{tuple(JUDGE_BY_KEY)}")
    return JUDGE_BY_KEY[model_key]


def registration_models() -> list[dict[str, Any]]:
    """The model block of the signed v4 registration manifest."""
    return [{"execution_order": m.execution_order, "model_key": m.model_key,
             "model_id": m.model_id, "revision": m.revision,
             "thinking_policy": m.thinking_policy,
             "chat_template_kwargs": dict(m.chat_template_kwargs)}
            for m in sorted(MODELS, key=lambda m: m.execution_order)]


def assert_disjoint_judges() -> None:
    """Executable §10.4 invariant, checked at qualification."""
    overlap = set(MODEL_BY_KEY) & set(JUDGE_BY_KEY)
    if overlap:
        raise ProtocolError(f"judge registry overlaps the study models: "
                            f"{sorted(overlap)}")
