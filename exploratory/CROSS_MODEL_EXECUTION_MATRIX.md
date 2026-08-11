# Cross-model execution matrix

**Frozen before the main cross-model factorial ran.** Every entry comes
from the Stage A–E artefacts (`runs/xm_validate_*`,
`runs/xm_calibrate_*`); no generation from the scientific run is read
here. Regenerate with `uv run python xm_matrix.py`.

Recorded 2026-08-11 23:01 UTC. Machine-readable twin:
`CROSS_MODEL_EXECUTION_MATRIX.json`.

The question this table answers is not whether a checkpoint shows DCI.
It is whether the checkpoint was executed in a way that preserves the
same scientific treatment, so that a behavioural comparison is even
admissible.

## Identity and numerical condition

| model | family | revision | weights | dtype | quant | backend | GPU layout | BF16 load |
|---|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3.5-4B` | qwen3.5 | `851bf6e806ef` | 8.7 GiB | bfloat16 | none | transformers 5.15.0 | cuda:1 | yes |
| `Qwen/Qwen3.5-9B` | qwen3.5 | `c20223623576` | 18.0 GiB | bfloat16 | none | transformers 5.15.0 | cuda:1 | yes |
| `google/gemma-4-E4B-it` | gemma4 | `ee0ef6023621` | 14.9 GiB | bfloat16 | none | transformers 5.15.0 | cuda:0 | yes |
| `google/gemma-4-12B-it` | gemma4 | `707f0a3b8a3c` | 22.3 GiB | bfloat16 | none | transformers 5.15.0 | cuda:0 | yes |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | kimi-vl | `—` | 30.6 GiB | bfloat16 | none | transformers  | — | no |

## Reasoning interface

| model | strategy | parser | no-thinking supported | validated | natural supported | validated | ceiling | closure | ceiling hits |
|---|---|---|---|---|---|---|---|---|---|
| `Qwen3.5-4B` | splice | `<think> … </think>` | yes | yes | yes | suspect | — | — | — |
| `Qwen3.5-9B` | splice | `<think> … </think>` | yes | yes | yes | yes | — | — | — |
| `gemma-4-E4B-it` | single_phase | `<|channel>thought … <channel|>` | yes | yes | yes | yes | 39515 | 0.938 | 0.000 |
| `gemma-4-12B-it` | single_phase | `<|channel>thought … <channel|>` | yes | yes | yes | no | — | — | — |
| `Kimi-VL-A3B-Thinking-2506` | single_phase | `◁think▷ … ◁/think▷` | no | not supported | yes | not run | — | — | — |

## Primitive competence (Stage D, isolated, disjoint tasks)

Each instruction presented ALONE. A focal instruction near floor makes
the four-state table a report on *neither* versus *target only* rather
than on arbitration between two live constraints — recorded here, before
the main result was looked at, so the limit cannot be fitted to it.

| model | A (target) | B (focal) | R (reference) | semicolon bg | control bg | classification |
|---|---|---|---|---|---|---|
| `Qwen3.5-4B` | — | — | — | — | — | NOT MEASURED |
| `Qwen3.5-9B` | — | — | — | — | — | NOT MEASURED |
| `gemma-4-E4B-it` | 1.00 | 0.75 | 1.00 | 1.00 | 0.75 | PRIMITIVE_VALID |
| `gemma-4-12B-it` | — | — | — | — | — | NOT MEASURED |
| `Kimi-VL-A3B-Thinking-2506` | — | — | — | — | — | NOT MEASURED |

## Admission

Admission is per (checkpoint, reasoning condition). A checkpoint whose
native non-thinking mode is validated is admissible in that condition
whatever its natural-reasoning calibration does, and the reverse.

| model | NO_THINKING | reason if not | NATURAL_REASONING | reason if not |
|---|---|---|---|---|
| `Qwen3.5-4B` | **yes** | — | **no** | no Stage E natural-reasoning calibration |
| `Qwen3.5-9B` | **yes** | — | **no** | no Stage E natural-reasoning calibration |
| `gemma-4-E4B-it` | **yes** | — | **yes** | — |
| `gemma-4-12B-it` | **yes** | — | **no** | NATURAL_REASONING failed: OutOfMemoryError: HIP out of memory. Tried to allocate 72.00 MiB. GPU 0 has a total capacity of 23.98 GiB of which 80.00 MiB is free. Of the allocated memory 23.18 GiB is allocated |
| `Kimi-VL-A3B-Thinking-2506` | **no** | not natively supported by this checkpoint | **no** | no Stage B/C record — never validated |

## Execution notes

* **Qwen3.5-4B** — text-only causal-LM class; multimodal tower not loaded
* **Qwen3.5-9B** — text-only causal-LM class; multimodal tower not loaded
* **gemma-4-E4B-it** — text-only load impossible: the checkpoint stores `model.language_model.*` with vision AND audio towers, so the full conditional-generation class is used and those towers are allocated
* **gemma-4-12B-it** — distinct architecture from E4B (`gemma4_unified`), not merely larger
* **Kimi-VL-A3B-Thinking-2506** — custom modeling code (trust_remote_code); `kimi_vl` is absent from transformers 5.15.0's registry
