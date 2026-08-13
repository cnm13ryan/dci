# Root cause and engineering fixes — Gemma 4 12B and Kimi-VL

`EXPLORATORY_NO_EVIDENCE`. Recorded 2026-08-12. Machine: 2 × AMD Radeon RX 7900
XTX (gfx1100, 24 GiB each), ROCm 7.2, 91 GiB host RAM.

**Headline.** Neither checkpoint was ever incapable. Every Gemma 12B failure was
a configuration error or concurrent-run interference. Every Kimi failure was a
configuration error, contamination, or a dependency-version incompatibility that
disappears when the checkpoint runs on the transformers version its own
`config.json` declares. Both now pass a qualification ladder on a clean machine.

| | previous verdict | verdict now |
|---|---|---|
| `google/gemma-4-12B-it` | unusable, ~55 h ETA, 160 technical failures | **rungs 1–3 passed**, 0 technical failures, ~23 h for 160 rows |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | `TP2_CAPACITY_BLOCKED`, then `BACKEND_BLOCKED` | **QUALIFIED**, 8/8 reproducible, ~3.8 h for 160 rows, zero shims |

---

## 1. Gemma 4 12B — root cause of every failure

| # | attempt | observed | classification |
|---|---|---|---|
| 1 | `device_map=cuda:0`, batch 8 | 22.3 GiB of weights on one 24 GiB card; PyTorch held **23.40 GiB**, 22 MiB free; OOM-split 8→4→2→1, then 160 technical failures | **configuration error** |
| 2 | `device_map=auto`, default 18 GiB cap, batch 4 | GPU0 19.4 GiB / GPU1 25.4 GiB; repeated OOM-splits; 0.1 rows/min | **configuration error** |
| 3 | `max_memory=13GiB`, batch 2 | PyTorch held only **11.3–11.6 GiB per card** yet **0 bytes free**; 6 rows in 85 min | **concurrent-run interference** |
| 4 | clean ladder, `max_memory=13GiB`, batch 2 | even split **11.16 / 11.12 GiB**, **12.09 / 12.55 GiB free**, 0 technical failures | passes |

**Attempt 1** is straightforward: the weights alone leave ~1.6 GiB for a KV
cache that a multi-thousand-token trace needs.

**Attempt 2** is the subtle one. `max_memory` is a per-card **cap**, not a
target: accelerate fills card 0 up to the cap before spilling. An 18 GiB cap on
a 22.3 GiB model puts ~18 GiB on card 0 and ~4 GiB on card 1, so card 0 has
almost no headroom while card 1 sits half empty. `device_map="auto"` is a
request, not a guarantee, which is why rung 1 of the ladder now *measures* where
the weights land.

**Attempt 3** was two identical processes — pids 1198381 and 1198611, both
`xm_run.py --model google/gemma-4-12B-it`, both writing
`runs/xmA_gemma12B_k3` — each holding ~12 GiB per card. `11.5 + 11.5 + overhead
≈ 24 GiB` exactly accounts for "0 bytes free" while PyTorch reported only
11.5 GiB. Its output (6 rows, **4 unique `row_id`s**) is quarantined at
`runs/_quarantine/gemma12B_k3_partial_CORRUPT_two_writers.jsonl` and must not be
used.

### What is actually true about this checkpoint

It is **not** memory-blocked, and it is **not** pathological. It is slow because
it reasons far more than its sibling:

| | median generated tokens | max | ceiling hit |
|---|---|---|---|
| `gemma-4-E4B-it` | 375 | 842 | never |
| `gemma-4-12B-it` | **6320** | **8190** | 1 of 8 rows |

That is ~17× more tokens on identical prompts, and 12B occasionally exhausts the
8192-token budget that E4B never approaches. At 0.12 rows/min this projects to
**~23 hours** for 160 rows. That is a throughput fact about the hardware and the
model, not a defect.

---

## 2. Kimi-VL — root cause of every failure

| # | attempt | observed | classification |
|---|---|---|---|
| 1 | vLLM TP=2, BF16, 6-point grid | all 6 failed at weight load; `free_before` **[23.95, 23.94]** on every attempt | **genuine GPU capacity problem** (vLLM without offload) |
| 2 | vLLM `a`/`b`/`c` | refused in 5 s at the plan step: `max_model_len 8192` equalled the generation ceiling, leaving no room for the prompt | **configuration error** |
| 3 | vLLM `d` | engine OOM at weight load — but a 14-hour orphan and 42 GiB of leaked shared memory were present | **stale-process interference; not evidence** |
| 4 | vLLM `e` | exit 3, exception; same contamination | **contaminated; unresolved** |
| 5 | vLLM `f`, `g` | killed by **signal 9** within seconds | **concurrent-run interference** (another driver's reap matched `crossmodel/vllm_tp2.py`) |
| 6 | Transformers 5.15, shim 1 | `KeyError: 'type'` in `_init_rope` | **dependency incompatibility** |
| 7 | Transformers 5.15, shims 1–2 | `tie_weights() got an unexpected keyword argument 'recompute_mapping'` | **dependency incompatibility** |
| 8 | `.venv-kimi`, first try | `__init__() got an unexpected keyword argument 'dtype'` | **configuration error** (5.x spelling in a 4.x environment) |
| 9 | `.venv-kimi`, 16 GiB cap | loaded, but **1.71 GiB pushed to `meta`/disk** | **configuration error** (cap too low) |
| 10 | `.venv-kimi`, 19 GiB cap | **all 30.56 GiB resident**, QUALIFIED | passes |

Only row 1 is a real statement about capacity, and it is narrower than it was
recorded as: **vLLM TP=2 in BF16 without CPU offload cannot fit this checkpoint**
at any of the three context lengths tested. Rows 3–5 were contaminated and
prove nothing. Rows 6–7 are properties of transformers 5.15.0, not of the model.

### The dependency route, and why the shims were retired

`config.json` declares `transformers_version: 4.50.3`. Three separate breakages
appear on 5.15.0, and each vanishes on the declared version:

| symptom on 5.15.0 | on 4.50.3 |
|---|---|
| `is_torch_fx_available` removed at import | **present** |
| `rope_scaling: null` synthesised into `{rope_type: 'default'}` | **loads as `None`** |
| `tie_weights(recompute_mapping=False)` | **signature is `(self)`** |

`.venv-kimi` carries transformers 4.50.3 on the identical ROCm torch 2.9.1
wheel. The qualification run applied **zero** compatibility shims and records
that fact (`compatibility_shims_applied: []`, `rope_scaling_as_loaded: null`)
rather than asserting it. Per the instruction to prefer a compatible environment
over accumulating shims, the three shims are superseded for this route.

---

## 3. Previous conclusions this invalidates

1. **`TP2_CAPACITY_BLOCKED` as a statement about the Kimi checkpoint** — wrong.
   True only of vLLM-without-offload. The checkpoint runs on both cards with
   room to spare under Transformers.
2. **`BACKEND_BLOCKED` for Kimi under Transformers** — real for transformers
   5.15.0, but not a property of the checkpoint.
3. **"Gemma 12B is effectively unusable, ~55 h"** — that was two runs contending.
4. **My claim that vLLM attempt `e` proved the weights load with
   `cpu_offload_gb=6`** — wrong. It exited 3 with an exception; I misread the
   driver's exit code.
5. **My claim that `f`/`g` died of host memory pressure** — wrong. They were
   SIGKILLed by a concurrent driver's reap.
6. **My reported "~2 rows/min, ~90 minutes" for Gemma 12B** — wrong by 15×; the
   true rate was 0.13 rows/min. Reported to the user and corrected.
7. **An 18.8% replicate-duplication alarm on Qwen3.5-4B** — an artefact of
   comparing empty answers. Among pairs where both replicates answered, 0.

The three completed k=3 datasets (Qwen3.5-4B, Qwen3.5-9B, gemma-4-E4B-it) are
**not** invalidated: each has 160 rows, 160 unique ids, one revision, and
gemma-4-E4B-it reproduces byte-identically against a run from a different
session, which is direct evidence that contention changed throughput and not
output.

---

## 4. Fixes implemented

**Execution safety** (`crossmodel/runlock.py`, `8ad14ae`)

* exclusive `flock` on a machine-wide GPU lock **and** on the output directory;
  a second run refuses to start rather than sharing
* the GPU lock is taken **first**, which is what makes "any live runner is an
  orphan" sound rather than a race
* stale-process patterns now cover `crossmodel/vllm_tp2.py`, `xm_run.py`,
  `xm_vllm_run.py` and the probes — not only the renamed `VLLM::*` children,
  which is how one orphan survived fourteen hours
* `/dev/shm` inspected and stale `psm_*` segments removed at acquisition
* locks released and child runners reaped on success, on exception, and on
  SIGINT/SIGTERM — verified live: a SIGTERM mid-run left
  `state: terminated_by_signal_15`, no orphans, and VRAM freed
* run manifest written atomically (temp + `os.replace`) with pid, run id, model,
  revision and GPU allocation
* free VRAM per card recorded at acquisition, with a warning when a card starts
  dirty, so a memory verdict can prove what the cards held
* writing into a directory that already holds output is refused without
  `--resume`

**Data integrity**

* `assert_unique_rows` refuses to publish a file whose row ids are not exactly
  the design's — called on both backends before writing
* incremental persistence on both paths, so completed rows survive interruption
* the vLLM driver removes a stale raw file before generating and checks the row
  count, so a SIGKILLed generation reports as a failed generation instead of an
  ingest provenance error
* `replicate_duplication` excludes pairs where either replicate produced no
  answer, and reports how many it set aside

**Configuration**

* `--max-memory-per-gpu` on `xm_run.py`, because the weight cap is what decides
  whether the KV cache has anywhere to go
* the Kimi backend **refuses** any placement on `meta`/`cpu`/`disk`: a cap too
  small silently streams weights from disk, which is a different execution
  condition and unusably slow
* `.venv-kimi` — transformers 4.50.3 on the same ROCm torch wheel

**Validation** — 147 tests pass, including 15 new regression tests in
`tests/test_runlock.py`, one per failure above, with a cross-process test that a
genuinely separate process cannot take a held lock.

---

## 5. Qualification evidence

### `google/gemma-4-12B-it` — `runs/xmq_gemma12B_a`

| rung | result |
|---|---|
| 1 load | **pass** — 17.3 s; weights **11.16 / 11.12 GiB**; free **12.09 / 12.55 GiB** |
| 2 one request | **pass** — 1/1 answered, 0 cap hits, 685 s |
| 3 small batch | **pass** — 8 rows, 7/8 answered, **0 technical failures**, 0.12 rows/min |
| 4 repeatability | **not run** — stopped by operator request during rung 4 |

### `moonshotai/Kimi-VL-A3B-Thinking-2506` — `runs/xmq_kimi_c`

| rung | result |
|---|---|
| 1 load | **pass** — 19.4 s; weights **13.60 / 16.97 GiB** (30.56 total, none off-GPU); free 5.67 / 9.75 GiB; 0 unexpected keys |
| 2 one request | **pass** — 1/1 answered, 0 cap hits, 20.1 s |
| 3 small batch | **pass** — 8 rows, 7/8 answered, 1 cap hit, 0.70 rows/min |
| 4 repeatability | **pass** — **8/8 identical** |

Both ran as the sole locked process on cards verified free
(23.3–24.0 GiB) with no runner processes and no shared-memory segments.

---

## 6. Remaining blockers

* **Gemma 12B: none technical.** The cost is time — ~23 h for 160 rows. Rung 4
  was not run, so reproducibility is unverified for this checkpoint; it should
  be confirmed before the scientific run, or accepted as a known gap.
* **Kimi under vLLM: still blocked without CPU offload**, on the clean 6-point
  grid. Whether offload works on a clean machine is **untested** — every offload
  attempt was contaminated. This is not on the critical path, because the
  Transformers route qualifies.
* **Gemma 12B batch size above 2 is untested.** At batch 2 there is 8–11 GiB
  free per card, so a larger batch may cut the 23 h materially.

---

## 7. Recommended configuration

### `google/gemma-4-12B-it`

```
uv run python xm_run.py --model google/gemma-4-12B-it \
    --mode NATURAL_REASONING --device-map auto \
    --max-memory-per-gpu 13GiB --batch-size 2 \
    --generation-ceiling 8192 --out runs/<dir>
```

Environment `.venv` (transformers 5.15.0). Weights split 11.16/11.12 GiB,
~12 GiB free per card. Expect ~23 h and roughly 1 in 8 rows to reach the
ceiling. **Do not** use a single card, and **do not** raise the cap above
13 GiB — a higher cap fills card 0 first and starves the KV cache.

### `moonshotai/Kimi-VL-A3B-Thinking-2506`

```
uv run python xm_qualify_kimi.py --device-map auto \
    --max-memory-per-gpu 19GiB --batch-size 2 --generation-ceiling 8192
```

Environment `.venv-kimi` (transformers **4.50.3**, ROCm torch 2.9.1), zero
shims. All 30.56 GiB resident, ~5.7/9.8 GiB free per card. Expect ~3.8 h.
**Do not** drop the cap to 16 GiB — 1.71 GiB then streams from disk. **Do not**
use the vLLM route without CPU offload; it does not fit.

A full-run backend for Kimi on this path does not exist yet: `xm_qualify_kimi.py`
runs the ladder only. Generating its 160 rows needs the same design-in/rows-out
backend the vLLM path has, which is the next piece of work.
