"""The four registered execution conditions (amendment A2) and their plans.

Each model is configured through an explicit, study-owned adapter object;
nothing is inherited from the exploratory registry at run time. The adapter
emits the complete ``plan.json`` the shared backend consumes, pinning every
field the backend would otherwise default: revision, dtype, decoding, template
kwargs, parser, delimiters, context envelope. `vllm_backend.io.load_plan`
gives an explicit plan field precedence over its own registry, so these plans
are self-describing across all four models.

No-thinking (task §1.3) per model is documented in DECISIONS.md (A2); the
adapter's ``switch_expectation`` states, per model, whether the
``enable_thinking`` template kwarg must be live ("live") or provably inert
("inert"); qualification verifies the expectation against the real template.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dci1.protocol.constants import DECODING, GREEDY_DECODING, ProtocolError

#: One engine-level seed for every run, recorded in every plan (D23).
ENGINE_SEED = 20260812
#: Equal context envelope across all four models (an engineering ceiling,
#: never a scientific variable). Prompts are < 600 tokens; outputs <= 400.
MAX_MODEL_LEN = 4096


@dataclass(frozen=True)
class ModelSpec:
    """One registered execution condition."""

    model_key: str                 # study-internal slug (dir names, records)
    model_id: str                  # exact HF repository
    revision: str                  # exact pinned commit
    family: str
    #: kwargs handed to apply_chat_template for the no-thinking condition.
    chat_template_kwargs: dict[str, Any]
    #: "live": negating the boolean kwarg MUST change the rendered prompt.
    #: "inert": rendering with/without the kwarg MUST be byte-identical
    #: (the checkpoint has no thinking switch; no-thinking is native).
    switch_expectation: str
    #: Markers whose presence in any scored answer is a leakage failure.
    leakage_markers: tuple[str, ...]
    trust_remote_code: bool = False
    limit_mm_per_prompt: dict[str, int] | None = None
    tensor_parallel_size: int = 1
    dtype: str = "bfloat16"
    gpu_memory_utilization: float = 0.85
    max_model_len: int = MAX_MODEL_LEN
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        model_key="qwen3-4b",
        model_id="Qwen/Qwen3-4B",
        revision="1cfa9a7208912126459214e8b04321603b3df60c",
        family="qwen3",
        chat_template_kwargs={"enable_thinking": False},
        switch_expectation="live",
        leakage_markers=("<think>", "</think>"),
        notes="hybrid checkpoint; enable_thinking=False injects a pre-closed "
              "<think>\\n\\n</think> block into the prompt, so the generation "
              "carries no reasoning channel",
    ),
    ModelSpec(
        model_key="qwen3-4b-instruct-2507",
        model_id="Qwen/Qwen3-4B-Instruct-2507",
        revision="cdbee75f17c01a7cc42f958dc650907174af0554",
        family="qwen3",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>"),
        notes="no reasoning channel exists; the template takes no thinking "
              "argument (enable_thinking verified inert)",
    ),
    ModelSpec(
        model_key="gemma-3n-e2b-it",
        model_id="google/gemma-3n-E2B-it",
        revision="5e092ebca197cdcd8d8b195040accf22693501bc",
        family="gemma3n",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>", "<start_of_turn>",
                         "<end_of_turn>"),
        # limit_mm_per_prompt deliberately UNSET (D26): zeroing every
        # modality flips vLLM 0.15.1 into text-only mode, whose runner passes
        # inputs_embeds=None — and this wheel's gemma-3n forward()
        # dereferences inputs_embeds unconditionally, crashing engine init.
        # Prompts remain text-only; the unused multimodal path stays enabled.
        notes="non-thinking instruction checkpoint (MatFormer E2B); "
              "text-only prompts with the multimodal path left enabled (D26)",
    ),
    ModelSpec(
        model_key="gemma-3n-e4b-it",
        model_id="google/gemma-3n-E4B-it",
        revision="c1221e9c62e34a43ab7ffacd1be0ea71f126ef10",
        family="gemma3n",
        chat_template_kwargs={},
        switch_expectation="inert",
        leakage_markers=("<think>", "</think>", "<start_of_turn>",
                         "<end_of_turn>"),
        # limit_mm_per_prompt deliberately UNSET — same wheel bug as E2B (D26).
        # 0.85 utilization left the KV cache at −0.71 GiB on a 24 GiB card
        # (weights 14.93 GiB + multimodal towers + profile peak); 0.95 is the
        # measured envelope that fits. Engineering ceiling, not science (D26).
        gpu_memory_utilization=0.95,
        notes="non-thinking instruction checkpoint (MatFormer E4B); "
              "text-only prompts with the multimodal path left enabled (D26)",
    ),
)

MODEL_BY_KEY = {m.model_key: m for m in MODELS}
MODEL_KEYS = tuple(m.model_key for m in MODELS)


def get_model(model_key: str) -> ModelSpec:
    if model_key not in MODEL_BY_KEY:
        raise ProtocolError(
            f"{model_key!r} is not a registered model; known: {MODEL_KEYS}")
    return MODEL_BY_KEY[model_key]


def backend_plan(spec: ModelSpec, *, decoding: str = "stochastic",
                 chunk_size: int = 32,
                 deadline_seconds: float | None = None) -> dict[str, Any]:
    """The complete plan.json payload for one run of one model.

    ``decoding`` is "stochastic" (the registered §4 policy) or "greedy" (the
    §8 sensitivity replication). Every backend-consumed field is explicit; the
    backend registry supplies nothing.
    """
    if decoding == "stochastic":
        policy = DECODING
        top_k = policy["top_k"]
    elif decoding == "greedy":
        policy = GREEDY_DECODING
        top_k = 0                    # legacy plan spelling of "off" (-> -1)
    else:
        raise ProtocolError(f"unknown decoding policy {decoding!r}")
    plan: dict[str, Any] = {
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "model_family": spec.family,
        "dtype": spec.dtype,
        "quantization": "none",
        "tensor_parallel_size": spec.tensor_parallel_size,
        "gpu_memory_utilization": spec.gpu_memory_utilization,
        "disable_custom_all_reduce": True,
        "enforce_eager": True,
        "cpu_offload_gb": 0.0,
        "max_model_len": spec.max_model_len,
        "engine_seed": ENGINE_SEED,
        "trust_remote_code": spec.trust_remote_code,
        "limit_mm_per_prompt": spec.limit_mm_per_prompt,
        # ---- decoding: the preregistered policy, never a backend default ----
        "temperature": policy["temperature"],
        "top_p": policy["top_p"],
        "top_k": top_k,
        "generation_ceiling": policy["max_new_tokens"],
        "answer_tokens": policy["max_new_tokens"],
        # ---- run policy -----------------------------------------------------
        "chunk_size": chunk_size,
        "deadline_seconds": deadline_seconds,
        "strategy": "single_phase",
        "reasoning_mode": "NO_THINKING",
        "chat_template_kwargs": dict(spec.chat_template_kwargs),
        # No reasoning channel is ever scored in this study; the NO_THINKING
        # mode uses the backend's NullParser regardless, and pinning None here
        # makes that structural rather than incidental.
        "reasoning_parser": None,
        "think_open": "",
        "think_close": "",
        "decoding_policy": decoding,
    }
    return plan
