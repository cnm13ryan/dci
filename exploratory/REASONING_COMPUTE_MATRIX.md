# Reasoning-compute matrix

Every reasoning condition run in this study, with the execution condition that
produced it. Invalid and blocked conditions are kept with an explicit status
rather than deleted.

---

## Part 0 — the infrastructure decision record

### 0.1 Where the known-good ROCm vLLM environment was found

`/home/cnm13ryan/git/inoculation-prompting/gcd_sycophancy` — the
`selective_generalisation` project. Its `.venv` is installed and importable, and
both vendored wheels are present:

| asset | size | sha256 |
|---|---|---|
| `vendor/vllm-0.15.1+rocm720-cp312-cp312-linux_x86_64.whl` | 52,856,199 B | `c1cbdee67f40556982d6e98a242beea2db89a6d73b3b1b93f0d037a7b2ffafc9` |
| `vendor/amdsmi-26.2.1+fc0010cf6a-py3-none-any.whl` | 1,174,110 B | `ddd51af0f3a3f7804d023e79f8078652bd0297d8f6bfffbec564d27a8200186c` |

### 0.2 Environment comparison

| component | previous project (`gcd_sycophancy`) | current DCI exploratory venv |
|---|---|---|
| Python | 3.12.0 | 3.12.3 |
| ROCm | 7.2 (`rocm-smi-lib` 7.8.0) | same host, same ROCm |
| PyTorch | `2.9.1+rocm7.2.0.git7e1940d4` | `2.9.1+rocm7.2.0.git7e1940d4` (**identical build**) |
| Transformers | 4.57.6 | 5.15.0 |
| vLLM | **0.15.1** (vendored ROCm wheel) | absent |
| Triton | `3.5.1+rocm7.2.0.gita272dfa8` | `3.5.1+rocm7.2.0.gita272dfa8` (identical) |
| amd-aiter | absent (declared as an override, not installed) | absent |
| amdsmi | **26.2.1+fc0010cf6a** | absent |
| flash-attn | absent | absent |
| accelerate | 1.13.0 | 1.14.0 |
| GPU visibility | 2 × RX 7900 XTX (gfx1100, 23.98 GiB each) + gfx1036 iGPU | identical |

The two PyTorch builds are byte-identical in version string, which is why the
vLLM environment can be used for generation without changing the numerical
stack. The DCI venv was **not** modified: no `uv sync`, no dependency copy, no
wheel install. vLLM was used by invoking the other project's interpreter
directly, read-only.

### 0.3 Does vLLM detect ROCm?

Yes, with no intervention.

```
platform class: RocmPlatform      is_rocm: True
torch devices: 2                  import amdsmi: ok
```

The historical `UnspecifiedPlatform` / `Device string must not be empty` failure
mode is **absent**. `amdsmi` imports cleanly, which is the dependency the
previous project's note identified as the cause.

### 0.4 Does `tensor_parallel_size=2` work?

**Yes — but only with mitigations, and the default configuration hangs.**

| attempt | configuration | result |
|---|---|---|
| 1 | `tensor_parallel_size=2`, defaults | **HANG.** Killed at 16 min. Both cards held VRAM (22.3 / 21.3 GB) but GPU 0 sat at 100% and GPU 1 at 0% with SCLK at 10 MHz — a stalled collective, not progress. |
| 2 | `tensor_parallel_size=1` | Loaded in **14.1 s**, generated 112 tokens in 3.61 s. So vLLM startup on this stack is fast, and attempt 1 was a genuine hang rather than slow initialisation. |
| 3 | `tensor_parallel_size=2` + `disable_custom_all_reduce=True` + `NCCL_P2P_DISABLE=1` | **WORKS.** Loaded in 26.8 s, decoded 120 tokens in 1.86 s. |

This reproduces, and then resolves, a failure the previous project had already
documented in `projects/experiment_utils.py`:

> "consumer ROCm GPUs without a fast peer link, where NCCL collectives during
> decode stall indefinitely on `tp>1` (observed on 2× RX 7900 XTX)"

That project worked around it by capping TP at 1 (`MAX_TENSOR_PARALLEL_SIZE`).
It never tried disabling the custom all-reduce and P2P, which is what makes TP=2
work here. **The stall is a peer-link problem, not a hardware-capability limit.**

### 0.5 Evidence that both GPUs serve one request

| measurement | TP=1 | TP=2 (mitigated) |
|---|---|---|
| VRAM, card 0 | 21,925 MiB | 22,481 MiB |
| VRAM, card 1 | 27 MiB | 21,547 MiB |
| **GPU utilisation during one generation** | card 0 only | **card 0 = 86%, card 1 = 86%** |
| **KV-cache capacity** | 4,993 blocks → **79,888 tokens** | 13,502 blocks → **216,032 tokens** |
| decode, 120 tokens | 3.61 s (112 tok) | **1.86 s** |

Both cards are busy *within the same request*, KV capacity rises 2.7×, and decode
gets faster rather than slower. This is capacity mode, not two replicas.

### 0.6 Was capacity ever the blocker? No.

Round 8 concluded the reasoning programme was infeasible after a `b = 8192` run
OOM'd. That run was **batch 8 on one card**. Its own sibling run recorded
`peak_allocated_bytes = 12,899,124,224` at `b = 4096`, batch 4, against 8.4 GB of
weights — so non-weight memory was ≈ 4.5 GB for 4 × 4096, and batch 8 × 8192
predicts ≈ 26.4 GB on a 24 GB card. The OOM is fully explained by batch size.

Confirmed empirically: **one card already affords 79,888 KV tokens.** The Round 8
blocker was a configuration error, and the inference drawn from it is withdrawn.

### 0.7 Maximum tested reasoning horizon and natural closure

Measured on the **real stored DCI prompts** (π = QAC, k = 3, 40 prompts), not toy
questions, with the budget deliberately non-binding:

| model | revision | max_tokens | natural `</think>` closure | reasoning tokens among closed | non-empty answers |
|---|---|---|---|---|---|
| `Qwen/Qwen3-4B-Thinking-2507` | `768f209d` | 32,768 | **40/40 = 1.000** | min 219, p25 333, **median 435**, p75 567, p90 2,493, max 5,846 | 40/40 |
| `Qwen/Qwen3-4B` | `1cfa9a72` | 16,384 | **39/40 = 0.975** | min 170, p25 306, **median 437**, p75 544, p90 1,096, max 3,361 | 39/40 |

Both runs took ≈ 2 minutes. The reasoning distribution is **fully observable** —
there is no censoring left to work around. Round 8's censoring was a property of
`Qwen/Qwen3.5-4B`, a hybrid linear-attention checkpoint that is also **not
supported by vLLM 0.15.1** (`Qwen3_5ForCausalLM` is absent from the registry).

### 0.8 Is there a native reasoning-budget control?

**No graded one.** `SamplingParams` in vLLM 0.15.1 has no `max_think_tokens`,
`thinking_budget` or `reasoning_effort` field, and the Qwen3 chat template exposes
only the binary `enable_thinking`. What exists and is used:

* `enable_thinking=False` — the model's **own** non-thinking mode, used as the
  `b = 0` arm. This is a native condition, not a zero-length truncation.
* `vllm.reasoning.qwen3_reasoning_parser` — authoritative `<think>` channel
  separation, confirming the split this harness performs by hand.

Intermediate budgets are therefore **budget-forced**, and are labelled as such
everywhere. Their validity is not assumed; it is measured in §0.9.

### 0.9 Are the final answers valid at every budget?

This is the gate Round 8 failed. It now passes:

| assigned b | n | cap-hit | natural closure | realised M | answer tokens | truncated | empty | **scratch markers in answer** |
|---|---|---|---|---|---|---|---|---|
| 0 (native) | 160 | 0.000 | 1.000 | 0.0 | 96.7 | 0.000 | 0.000 | **0.000** |
| 256 | 160 | 0.950 | 0.050 | 255.1 | 114.9 | 0.000 | 0.000 | **0.000** |
| 512 | 160 | 0.556 | 0.444 | 446.5 | 118.0 | 0.000 | 0.000 | **0.000** |
| 1024 | 160 | 0.225 | 0.775 | 636.8 | 116.5 | 0.000 | 0.000 | **0.000** |
| 4096 | 160 | 0.025 | 0.975 | 769.4 | 116.0 | 0.000 | 0.000 | **0.000** |

Answer length is flat at 115–118 tokens across every thinking budget, nothing is
truncated or empty, and **no answer at any budget contains scratchpad language**
(`wait`, `let me count`, `recount`, `actually no`, …). Randomly inspected raw
answers at `b = 256` are ordinary prose. The Round 8 failure — a forced close
producing continued scratch work in the answer channel — does not occur here.

### 0.10 Which configuration the science now uses

| purpose | configuration |
|---|---|
| reasoning-compute experiment | `Qwen/Qwen3-4B` @ `1cfa9a72`, vLLM 0.15.1+rocm720, **TP=2** with `disable_custom_all_reduce=True`, `NCCL_P2P_DISABLE=1`, bf16, T=0.7, top-p 0.9, `max_model_len=16384`, fixed answer budget 512 |
| amplifier experiments | unchanged Transformers path, `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f`, one card, so every Round 1–8 comparison stays exact |
| scoring | always the study venv, against the same registry, from the **answer field only** |

Capacity mode and throughput mode are kept distinct: the amplifier runs were
executed on card 1 while card 0 ran vLLM, and that is recorded as throughput
scheduling, never as evidence about the reasoning horizon.

---

## Part 1 — the reasoning conditions

`Qwen/Qwen3-4B` @ `1cfa9a72` · vLLM 0.15.1+rocm720 · TP=2 · bf16 · T=0.7 ·
π = QAC · k = 3 · 20 tasks × 2 replicates · answer budget 512 · 800 generations
in ≈ 7 minutes.

| b | control mechanism | realised M | closure | valid answers | τ(B→A) amplifier | τ(B→A) control | Δ amplification |
|---|---|---|---|---|---|---|---|
| 0 | **native** `enable_thinking=False` | 0.0 | n/a | 160/160 | +0.600 [+0.400, +0.800] | +0.400 [+0.200, +0.600] | +0.200 [−0.150, +0.550] |
| 256 | budget-forced | 255.1 | 0.050 | 160/160 | +0.075 [−0.225, +0.375] | +0.150 [0.000, +0.300] | −0.075 [−0.376, +0.250] |
| 512 | budget-forced | 446.5 | 0.444 | 160/160 | +0.375 [+0.100, +0.650] | **0.000** | **+0.375 [+0.100, +0.650]** |
| 1024 | budget-forced | 636.8 | 0.775 | 160/160 | +0.450 [+0.200, +0.700] | **0.000** | **+0.450 [+0.200, +0.700]** |
| 4096 | effectively non-binding | 769.4 | 0.975 | 160/160 | +0.500 [+0.300, +0.700] | **0.000** | **+0.500 [+0.300, +0.700]** |

### Compliance against assigned budget, focal (B) arm

| b | A, amplifier | A, control | B, amplifier | B, control | C, amplifier | C, control |
|---|---|---|---|---|---|---|
| 0 | 0.400 | 0.600 | 0.000 | 0.000 | 1.000 | 1.000 |
| 256 | 0.725 | 0.850 | 0.150 | 0.000 | 0.850 | 0.850 |
| 512 | 0.375 | **1.000** | 0.150 | 0.200 | 0.800 | 0.850 |
| 1024 | 0.400 | **1.000** | 0.000 | 0.100 | 0.800 | 0.900 |
| 4096 | 0.450 | **1.000** | 0.050 | 0.100 | 0.850 | 0.900 |

### Arbitration, focal (B) arm

| background | b | both | target only | focal only | neither |
|---|---|---|---|---|---|
| control | 0 | 0.000 | 0.600 | 0.000 | 0.400 |
| control | 4096 | 0.100 | **0.900** | 0.000 | **0.000** |
| amplifier | 0 | 0.000 | 0.400 | 0.000 | 0.600 |
| amplifier | 4096 | 0.000 | 0.450 | 0.050 | **0.500** |

Reasoning moves the control condition out of "neither" entirely and into "target
only". Under the amplifier, half the responses stay in "neither" no matter how
much reasoning is allowed.

### Descriptive only — realised reasoning by cell (post-treatment, never conditioned on)

| b | amp · B | amp · C_L3 | ctl · B | ctl · C_L3 |
|---|---|---|---|---|
| 512 | 506.4 | 443.9 | 487.2 | 348.4 |
| 1024 | 776.6 | 701.5 | 660.0 | 409.1 |

At matched budgets the **focal arm spends more reasoning than the reference**,
and the amplifier raises reasoning expenditure further — most visibly in the
reference arm (701.5 against 409.1 at b = 1024).

---

## Part 2 — conditions recorded as invalid or blocked

| condition | status | reason |
|---|---|---|
| `S1_natural` (Qwen3.5-4B, b=8192, batch 8, Transformers) | **invalid, retained** | OOM 48/48. Now known to be a batch-size artefact, not a capacity limit. |
| `S1_natural2` (Qwen3.5-4B, b=4096, batch 4) | **valid but censored** | 14/16 cap-hit; unusable for a dose-response, and the basis of Round 8's withdrawn blocker. |
| Round 8 forced-close answers on Qwen3.5-4B | **invalid** | answer channel contained continued scratch work. Not repeated; not plotted. |
| `Qwen/Qwen3.5-4B` under vLLM | **blocked** | `Qwen3_5ForCausalLM` is not in vLLM 0.15.1's model registry. No substitution was made silently — the reasoning programme moved to `Qwen3-4B`, and the reason is recorded here. |
| `Qwen3.6` | **blocked** (Round 6) | 27B ≈ 55.6 GB bf16 against 48 GB total; FP8 unsupported on gfx1100; Int4 would change the numerical condition. |
| TP=2 with default all-reduce | **failed, documented** | indefinite collective stall; see §0.4. |

---

## Part 3 — Round 10 conditions

All on `Qwen/Qwen3-4B` @ `1cfa9a72`, vLLM 0.15.1+rocm720, TP = 2 (mitigated),
bf16, T = 0.7, top-p 0.9, fixed 512-token answer budget. **Effective one draw per
cell** — see the seeding defect in `DECISIONS.md` R10.2.

### The full QAC k=3 grid (S18 + Round 10 transition budgets)

| b | mode | cap-hit | closure | realised M | answer tok | truncated | leaked | τ control | τ amplifier | Δ |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **native non-thinking** | — | — | 0.0 | 96.7 | 0.000 | 0.000 | +0.400 | +0.600 | +0.200 |
| 256 | budget-forced | 0.950 | 0.050 | 255.1 | 114.9 | 0.000 | 0.000 | +0.150 | +0.075 | −0.075 |
| 320 | budget-forced | 0.812 | 0.188 | 313.2 | 120.0 | 0.000 | 0.025 | +0.050 | +0.325 | +0.275 |
| 384 | budget-forced | 0.750 | 0.250 | 364.9 | 116.4 | 0.000 | 0.013 | +0.050 | +0.425 | +0.375 |
| 448 | budget-forced | 0.650 | 0.350 | 407.9 | 115.1 | 0.000 | 0.000 | +0.050 | +0.350 | +0.300 |
| 512 | budget-forced | 0.556 | 0.444 | 446.5 | 118.0 | 0.000 | 0.000 | **0.000** | +0.375 | +0.375 |
| 640 | budget-forced | 0.381 | 0.619 | 508.5 | 117.6 | 0.000 | 0.000 | 0.000 | +0.475 | +0.475 |
| 1024 | budget-forced | 0.225 | 0.775 | 636.8 | 116.5 | 0.000 | 0.000 | 0.000 | +0.450 | +0.450 |
| 4096 | near-unconstrained | 0.025 | 0.975 | 769.4 | 116.0 | 0.000 | 0.000 | 0.000 | +0.500 | +0.500 |

### S25 — placement × reasoning (QAC, k = 3)

Backgrounds are the free and anchored semicolon wordings; there is no
non-amplifying control in this design, so it speaks to placement only.

| b | cap-hit | closure | realised M | τ free | τ anchored | Δ placement | anchored compliance |
|---|---|---|---|---|---|---|---|
| 0 | — | — | 0.0 | +0.450 | +0.450 | **+0.000** | 0.750 |
| 256 | 0.963 | 0.037 | 254.9 | −0.050 | 0.000 | −0.050 | 0.875 |
| 1024 | 0.300 | 0.700 | 674.7 | +0.350 | +0.400 | −0.050 | 0.575 |
| 4096 | 0.031 | 0.969 | 1066.8 | +0.350 | +0.350 | **+0.000** | 0.575 |

### S26 — reasoning × ACQ order (k = 3)

| b | cap-hit | closure | realised M | τ control | τ amplifier | Δ | truncated | leaked |
|---|---|---|---|---|---|---|---|---|
| 0 | — | — | 0.0 | +0.600 | +0.150 | **−0.450** | 0.000 | 0.013 |
| 256 | 0.825 | 0.175 | 251.6 | +0.050 | −0.050 | −0.100 | 0.000 | 0.013 |
| 1024 | 0.113 | 0.887 | 527.9 | +0.050 | +0.300 | **+0.250** | 0.000 | 0.000 |
| 4096 | 0.025 | 0.975 | 644.4 | +0.050 | +0.300 | **+0.250** | 0.013 | 0.000 |

### S27 — reasoning × load (QAC, k = 5)

| b | cap-hit | closure | realised M | τ control | τ amplifier | Δ | truncated | leaked |
|---|---|---|---|---|---|---|---|---|
| 256 | **0.992** | 0.008 | 256.0 | 0.000 | +0.050 | +0.050 | 0.017 | 0.017 |
| 4096 | 0.008 | 0.992 | 1043.3 | +0.050 | +0.625 | **+0.575** | 0.000 | 0.000 |

The b = 256 column is censored on 99.2% of rows and is a *cut-short* condition
rather than a low-reasoning one; it is reported, flagged, and not used to
characterise a dose.

### Arbitration across every Round 10 condition

`A ∧ B ∧ C` is certified satisfiable (`satisfiability_certificate.py`), so these
are model failures on an achievable task.

**P(both) never exceeds 0.150 anywhere.** Reasoning moves probability from
"neither" to "target only", not to "both". Under the amplifier at ACQ it moves
the wrong way: "neither" rises 0.100 → 0.350 as the budget grows.

---

## Part 3 — the NATURAL_REASONING condition (Round 11)

`Qwen/Qwen3-4B` @ `1cfa9a72` · vLLM 0.15.1+rocm720 · TP=2 · bf16 · T=0.7 ·
top-p 0.9 · answer allowance 512 · π = QAC, k = 3 · 20 tasks × 2 replicates ·
**per-row seeds** `20260810 + 90000 + 7919·i`.

| field | value |
|---|---|
| reasoning-control mechanism | **none** — the model emits its own `</think>` and then answers |
| engineering ceiling | **39,550** tokens, derived from the context envelope (§R11.2) |
| ceiling reached | **0 / 160** — the ceiling never binds |
| natural closure | 160 / 160 |
| realised reasoning | min 173 · p25 354 · median **511** · p75 745 · p90 1,445 · max **5,888** |
| rows above 4,096 | 1 (the tail a 4,096 cap truncates) |
| final-answer validity | 0 empty · 0 truncated · mean 119.0 tokens |
| scratchpad leakage | 2/160 flagged, **0 genuine** on inspection (regex false positives on the ordinary word *wait*) |
| replicate pairs identical | 0 / 80 |
| latency | reasoning phase 161.2 s · answer phase 24.6 s for 160 rows, batched |
| τ, bracket-pair background | **0.000** [0.000, 0.000] |
| τ, semicolon background | **+0.400** [+0.225, +0.550] |
| Δ amplification | **+0.400** |

### The capped grid, regenerated under per-row seeding

`s18_reseeded.jsonl` supersedes `s18_reasoning.jsonl` for every figure. The
original is retained, not deleted, and the loader records which file it used.

| b | cap-hit | realised mean | τ bracket | τ semicolon |
|---|---|---|---|---|
| 0 (native non-thinking) | — | 0.0 | +0.450 | +0.525 |
| 256 | 0.900 | 253.4 | +0.025 | +0.325 |
| 512 | 0.481 | 423.0 | **0.000** | +0.625 |
| 1,024 | 0.181 | 580.4 | −0.025 | +0.550 |
| 4,096 | 0.025 | 751.8 | −0.025 | +0.375 |
| **natural** | **0.000** | 592.4 | **0.000** | **+0.400** |

### Status of `b = 4096`

**Retained in the deliberate reasoning-limit experiment. Never labelled
unlimited, unconstrained, natural, or full reasoning.** Its cap-hit rate is 2.5%
overall but **10.0% in the semicolon × reference cell**, and the natural run
shows traces reaching 5,888 tokens.

### Conditions recorded as invalid

| condition | status | reason |
|---|---|---|
| first natural attempt (shared seed) | **invalid, not evidence** | written with the R10.2 seed defect; terminated at 157/160 and never completed. Superseded, not reported. |
