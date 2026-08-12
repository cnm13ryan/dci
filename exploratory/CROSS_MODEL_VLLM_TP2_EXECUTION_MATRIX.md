# Cross-model execution matrix — vLLM tensor-parallel 2

**Experiment `VLLM_TP2_CROSS_MODEL`. Frozen before the k=3 factorial ran.**
Every entry comes from Stage A (`runs/xmv_smoke2_*`) and Stage B
(`runs/xmv_calib_*`); no k=3 or k=5 generation is read here.
Regenerate with `uv run python xm_vllm_matrix.py`.

Recorded 2026-08-12 01:07 UTC. Machine-readable twin:
`CROSS_MODEL_VLLM_TP2_EXECUTION_MATRIX.json`.

This table does **not** say whether a checkpoint shows DCI. It says
whether the checkpoint could be executed at all under the one common
condition this retry exists to impose.

## Backend

| field | value |
|---|---|
| vllm_version | `0.27.1` |
| vllm_build_commit | `6e448d0ea9bf3d88d898b65449ca6dc2aec170ac` |
| wheel | `vllm-0.27.1+rocm723-cp312-cp312-manylinux_2_34` |
| torch | `2.11.0+gitd0c8b1f` |
| tensor_parallel_size | `2` |
| dtype | `bfloat16` |
| disable_custom_all_reduce | `True` |
| NCCL_P2P_DISABLE | `1` |
| HIP_VISIBLE_DEVICES | `0,1` |
| gpus | `2 x AMD Radeon RX 7900 XTX (gfx1100), 23.98 GiB each` |
| rocm | `7.2.0 host; wheel built for 7.2.3` |

## Identity and numerical condition

| model | revision | weights | dtype | quant | TP | reasoning parser | chat-template kwargs |
|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3.5-4B` | `851bf6e806ef` | 8.7 GiB | bfloat16 | none | 2 | `qwen3` | `{'enable_thinking': True}` |
| `Qwen/Qwen3.5-9B` | `c20223623576` | 18.0 GiB | bfloat16 | none | 2 | `qwen3` | `{'enable_thinking': True}` |
| `google/gemma-4-E4B-it` | `ee0ef6023621` | 14.9 GiB | bfloat16 | none | 2 | `gemma4` | `{'enable_thinking': True}` |
| `google/gemma-4-12B-it` | `707f0a3b8a3c` | 22.3 GiB | bfloat16 | none | 2 | `gemma4` | `{'enable_thinking': True}` |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | `aa1730989e75` | 30.6 GiB | bfloat16 | none | 2 | `delimiters` | `{}` |

## Stage A — TP=2 load, both cards, parser, weight integrity

| model | status | both GPUs active | answers | reasoning emitted | closed | marker leak | control residue | weight integrity |
|---|---|---|---|---|---|---|---|---|
| `Qwen3.5-4B` | **TP2_REASONING_INVALID** | yes | 7/8 | 8 | 7 | 0 | 0 | 4/4 |
| `Qwen3.5-9B` | **TP2_LOAD_VALID** | yes | 8/8 | 8 | 8 | 0 | 0 | 4/4 |
| `gemma-4-E4B-it` | **TP2_BACKEND_BLOCKED** | no | —/— | — | — | — | — | —/— |
| `gemma-4-12B-it` | **TP2_BACKEND_BLOCKED** | no | —/— | — | — | — | — | —/— |
| `Kimi-VL-A3B-Thinking-2506` | **TP2_CAPACITY_BLOCKED** | no | —/— | — | — | — | — | —/— |

## Stage B — natural-reasoning calibration (DCI-shaped, disjoint tasks)

| model | n | ceiling | closure | cap-hit rate | empty | truncated | median | p90 | max |
|---|---|---|---|---|---|---|---|---|---|
| `Qwen3.5-4B` | — | — | — | — | — | — | — | — | — |
| `Qwen3.5-9B` | — | — | — | — | — | — | — | — | — |
| `gemma-4-E4B-it` | — | — | — | — | — | — | — | — | — |
| `gemma-4-12B-it` | — | — | — | — | — | — | — | — | — |
| `Kimi-VL-A3B-Thinking-2506` | — | — | — | — | — | — | — | — | — |

## Admission to the vLLM TP=2 NATURAL_REASONING slice

| model | admitted | reason if not |
|---|---|---|
| `Qwen/Qwen3.5-4B` | **no** | TP2_REASONING_INVALID: empty final answer; 1 trace(s) opened but never closed |
| `Qwen/Qwen3.5-9B` | **no** | no Stage B calibration |
| `google/gemma-4-E4B-it` | **no** | TP2_BACKEND_BLOCKED: transformers.integrations.heterogeneity.configuration_utils.AmbiguousGlobalPerLayerAttributeError: 'head_dim' is a per-layer attribute and may vary across layers. Access it via the |
| `google/gemma-4-12B-it` | **no** | TP2_BACKEND_BLOCKED: transformers.integrations.heterogeneity.configuration_utils.AmbiguousGlobalPerLayerAttributeError: 'head_dim' is a per-layer attribute and may vary across layers. Access it via the |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | **no** | TP2_CAPACITY_BLOCKED: RuntimeError: Engine core initialization failed. See root cause above. Failed core proc(s): {'EngineCore': 1} |

## Notes

* **Qwen3.5-4B** — template pre-opens <think>; enable_thinking=True is the documented native switch
* **gemma-4-E4B-it** — thinking defaults to FALSE in this template; the <|think|> directive is injected into the system turn when enabled
* **gemma-4-12B-it** — gemma4_unified architecture; 22.3 GiB of weights — the checkpoint TP=2 exists to rescue
* **Kimi-VL-A3B-Thinking-2506** — always-thinking checkpoint; no no-thinking toggle exists and its non-thinking sibling is a different checkpoint
