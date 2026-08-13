# Execution-condition comparison — Transformers versus vLLM TP=2

Generated 2026-08-12 01:09 UTC by `xm_vllm_compare.py` from the two experiments'
analysis outputs. Both are read; neither is modified.

## What separates the two columns

| | `TRANSFORMERS_CROSS_MODEL` | `VLLM_TP2_CROSS_MODEL` |
|---|---|---|
| backend | Transformers 5.15.0 | vLLM 0.27.1+rocm723 |
| torch | 2.9.1+rocm7.2.0 | 2.11.0+gitd0c8b1f |
| devices | one card per checkpoint (`device_map`) | tensor-parallel 2 |
| reasoning mechanism | two-phase splice (Qwen) / single-phase (Gemma) | one uninterrupted generation |
| answer allowance | 512 enforced separately (Qwen) | shared budget |
| reasoning parser | hand-written per family | vLLM `qwen3` / `gemma4` |
| dtype | bfloat16 | bfloat16 |
| decoding | T 0.7, top-p 0.9, top-k off | identical |
| tasks, arms, backgrounds, order, seeds, verifiers | identical | identical |

**More than the backend differs.** A difference between columns is
*execution-condition sensitivity*, not a causal backend effect. A
matched experiment varying only the backend was not run.

## τ and its raw components

| condition | model | reasoning | load | background | focal_A_failure | reference_A_failure | tau | lo | hi | degeneracy |
|---|---|---|---|---|---|---|---|---|---|---|
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-4B | NO_THINKING | 3 | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-4B | NO_THINKING | 3 | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-9B | NO_THINKING | 3 | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-9B | NO_THINKING | 3 | + one semicolon | +0.100 | +0.250 | -0.150 | -0.300 | +0.000 | estimable |
| TRANSFORMERS_CROSS_MODEL | gemma-4-12B-it | NO_THINKING | 3 | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | gemma-4-12B-it | NO_THINKING | 3 | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NATURAL_REASONING | 3 | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NATURAL_REASONING | 3 | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NO_THINKING | 3 | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NO_THINKING | 3 | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | TARGET_CEILING |


## Joint satisfaction

| condition | model | reasoning | load | joint_control | joint_semicolon | delta_joint | lo | hi |
|---|---|---|---|---|---|---|---|---|
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-4B | NO_THINKING | 3 | +0.175 | +0.200 | +0.025 | -0.150 | +0.200 |
| TRANSFORMERS_CROSS_MODEL | Qwen3.5-9B | NO_THINKING | 3 | +0.275 | +0.200 | -0.075 | -0.301 | +0.150 |
| TRANSFORMERS_CROSS_MODEL | gemma-4-12B-it | NO_THINKING | 3 | +1.000 | +0.900 | -0.100 | -0.200 | -0.025 |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NATURAL_REASONING | 3 | +0.900 | +0.875 | -0.025 | -0.175 | +0.100 |
| TRANSFORMERS_CROSS_MODEL | gemma-4-E4B-it | NO_THINKING | 3 | +0.200 | +0.175 | -0.025 | -0.175 | +0.125 |


## Coverage differs, and that is the main finding of the comparison

The two conditions do not cover the same cells, so most rows have no
counterpart:

| checkpoint | Transformers | vLLM TP=2 |
|---|---|---|
| `Qwen/Qwen3.5-4B` | NO_THINKING only — natural reasoning never established | see matrix |
| `Qwen/Qwen3.5-9B` | NO_THINKING only | see matrix |
| `google/gemma-4-E4B-it` | both modes | **TP2_BACKEND_BLOCKED** |
| `google/gemma-4-12B-it` | NO_THINKING only (single-card OOM) | **TP2_BACKEND_BLOCKED** |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | **BACKEND_BLOCKED** | see matrix |

No single execution condition on this host covers all five
checkpoints. Removing the backend confound for one family introduces
it for another, and that is a property of the available software, not
of the models.
