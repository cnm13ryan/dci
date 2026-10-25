# Batch 1 generation throughput on 2x H100: why the pilot was stopped, and what to change

**Date:** 2026-10-25. **Written by:** Claude (session independent-ef), which drove the
Lambda instance, at the researcher's request. **Status:** a recommendation for a D12
amendment. Nothing in the repository has been changed. Benchmark data, scripts and
the GPU log are in this directory (the GPU log stays on the instance and in the synced copy).

## 1. Summary

- The pilot (`runs/pilot-2026-10-25`, Freeze 1 `d8172697…f6fb`, commit `c174be8`) was
  stopped at the researcher's instruction at 09:45:12 UTC.
  - Stage 1 was `INCOMPLETE`: 7,808 of 15,616 rows accepted, both Gemma groups done,
    both Qwen groups interrupted, 0 technical failures.
  - The root is abandoned, not failed. It is kept as a record and must not be resumed
    or reused: an amended D12 means a new Freeze 1 and a new root.
- **Cause.** Two D12-bound values, `enforce_eager=True` and `chunk_size=64`, kept the
  GPUs at about 45% utilisation and 200 W of 700 W. Gemma ran at 10–12 rows/s, about
  the rate of the old RX 7900 XTX workstation.
- **Recommendation.** Keep `enforce_eager=True` and raise `chunk_size` from 64 to
  **512**. Measured on this instance, that is **3.6–5.4× faster**, does not change
  output length, finish reasons, truncation or empty answers, and keeps fresh-process
  reproducibility at 97% (the current setting: 95.5%).
- **Do not turn CUDA graphs on.** They add only 10–35% on top of chunk 512, and they
  make regeneration irreproducible: 11% of answers identical across fresh processes.
- **Disclosure needed regardless of the choice.** The *approved* settings are not
  bit-reproducible either: regenerating 1,024 Gemma E2B rows in a fresh process gave
  978 identical answers (95.5%). The 72-of-72 identity seen in the smoke tests was too
  small a sample to show this.

## 2. Reference point: what an H100 should deliver

`pre-emission-thought-anchors/anchor_reliability_v2/docs/compute_budget.md` measured
DeepSeek-R1-Distill-Qwen-14B on one H100 PCIe 80 GB:

- setup: vLLM, 32 concurrent requests, prefix caching, CUDA graphs;
- result: **907 tok/s** on ~3,900-token answers.

Decoding is bound by memory bandwidth. Two things move that figure for Batch 1:

- the Batch 1 models carry about a quarter of the weight bytes per step;
- the H100 SXM has ~1.7× the PCIe card's bandwidth (3.35 vs 2.0 TB/s).

That puts a well-batched ceiling in the region of 5,000–10,000 tok/s per GPU. The
pilot reached 1,400–1,700 tok/s on Gemma. The benchmark below confirms the gap and
reaches 8,000–16,000 tok/s once batches are large.

## 3. Benchmark

**Scope and limits:**

- **Prompts:** synthetic ("In 60 to 120 words, explain one interesting fact about …").
  No pilot or reserved topics, and no run root, so it is not evidence.
- **Decoding:** the pilot's: T 0.7, top-p 0.9, top-k 50, cap 512, thinking off for
  Qwen3-4B, per-request seeds, engine seed 20261018, bf16, `max_model_len` 4096.
  `gpu_memory_utilization` is 0.85, or 0.95 for E4B.
- **Backend:** the attested one, `environments/cuda-vllm` (vLLM 0.15.1, torch
  2.9.1+cu129), called directly through `LLM.chat`. That is the same engine the
  seam builds, but not the seam itself.
- **GPU figures:** utilisation and power are means over generation, from `nvidia-smi`
  at 1 Hz. Peak memory is not reported, because vLLM reserves the configured fraction
  up front; what matters is that every setting loaded, including E4B at 0.95 with CUDA
  graphs, which peaked at 80,319 of 81,559 MiB.
- **Size:** 3,904 prompts per run, the size of one Stage 1 model group.

### 3a. Throughput

| model | setting | rows/s | tok/s | × pilot setting | load s | GPU util | power W |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3-4B | eager, chunk 64 (**pilot**) | 39.2 | 4,047 | 1.0 | 25 | 66% | 297 |
| Qwen3-4B | eager, chunk 512 (**recommended**) | 142.7 | 14,736 | 3.6 | 23 | 85% | 494 |
| Qwen3-4B | graphs, chunk 64 | 66.2 | 6,848 | 1.7 | 52 | 90% | 414 |
| Qwen3-4B | graphs, chunk 512 | 157.2 | 16,266 | 4.0 | 40 | 85% | 481 |
| Qwen3-4B | graphs, one call (3,904) | 155.3 | 16,061 | 4.0 | 41 | 76% | 452 |
| Gemma 3n E4B | eager, chunk 64 (**pilot**) | 10.7 | 1,548 | 1.0 | 39 | 47% | 208 |
| Gemma 3n E4B | eager, chunk 512 (**recommended**) | 58.1 | 8,386 | 5.4 | 40 | 82% | 415 |
| Gemma 3n E4B | graphs, chunk 64 | 33.4 | 4,859 | 3.1 | 111 | 92% | 359 |
| Gemma 3n E4B | graphs, chunk 512 | 79.2 | 11,443 | 7.4 | 75 | 86% | 455 |
| Gemma 3n E4B | graphs, one call (3,904) | 76.0 | 11,061 | 7.1 | 74 | 76% | 434 |
| Gemma 3n E2B | eager, chunk 64 (**pilot**)¹ | 12.4 | 1,693 | 1.0 | 40 | 43% | 186 |
| Gemma 3n E2B | eager, chunk 512 (**recommended**)¹ | 64.2 | 8,751 | 5.2 | 39 | 80% | 373 |
| Gemma 3n E2B | graphs, chunk 512 | 95.4 | 13,037 | 7.7 | 123 | 84% | 415 |

¹ 1,024 prompts (the determinism runs); the other rows use 3,904.

The benchmark reproduces the pilot's own rates: E4B 10.7 rows/s here against 9.6 in
the pilot, and E2B 12.4 against 11.7. Qwen3-4B-Instruct-2507 was not benchmarked; in
the smoke tests it ran at Qwen3-4B's rate.

**Outcome sanity:** every setting is the same on every model.

- every answer finished with `stop`;
- 0 truncated at 512 tokens;
- 0 empty;
- mean length unchanged within 1 token per model: Qwen3-4B 103, E4B 145, E2B 136.

**Why chunk 512 and not one call:** above about 256 prompts, vLLM's own scheduler cap
(`max_num_seqs`, 256 by default) sets the batch. One call is therefore no faster than
512. Chunking only bounds what a crash loses, because the seam writes rows per chunk
and `resume` regenerates the rest. So 512 keeps fine-grained save points at no cost.

### 3b. Reproducibility (Gemma 3n E2B, 1,024 prompts)

**Fresh process** means the same prompts and seeds in a second, separate process.
That is what `resume`, or any re-run from the frozen design, does.

**Same engine** means a second pass inside the same engine. That never happens in the
pilot. It is shown because it isolates vLLM's prefix cache and scheduler state.

| setting | fresh process: identical answers | same engine, second pass |
|---|---:|---:|
| eager, chunk 64 (**pilot**) | 978 / 1,024 (95.5%) | 153 / 1,024 |
| eager, chunk 512 (**recommended**) | **995 / 1,024 (97.2%)** | 507 / 1,024 |
| graphs, chunk 512 | 114 / 1,024 (11.1%) | 390 / 1,024 |

Changing the batch size or the graph mode changes the generated texts against each
other: the text hashes differ between every pair of settings. That is expected,
because vLLM is not batch-invariant here (`VLLM_BATCH_INVARIANT` off, as D12 states).
Seeds are per request, so it is the arithmetic that changes, not the sampling stream.

The cause of the CUDA-graph irreproducibility was not isolated. A plausible
explanation is padding to captured batch sizes that differ with scheduler timing. It
is a hypothesis, not a finding.

## 4. Projected pilot time with the recommendation

At the eager / chunk 512 rates, with `--devices 0,1` and each model group as one
worker:

| | rows | ≈ generation | + model load (4 × ~40 s, over 2 GPUs) |
|---|---:|---:|---:|
| Stage 1 | 15,616 | ~2 min | ~1.5 min |
| Stage 2 (at most) | 15,360 | ~2 min | ~1.5 min |

Compare roughly 35–40 minutes at the current setting. Real pilot prompts carry an
instruction and may produce longer answers than the synthetic ones, so the smoke test
under the amended D12 should confirm the rate.

## 5. What the change touches

| item | value now | proposed | where | consequence |
|---|---|---|---|---|
| `chunk_size` | 64 | **512** | `config.DECODING` | D12 payload hash changes |
| `enforce_eager` | True | **True (unchanged)** | `runner.seam_plan` | none; record why it stays |
| `disable_custom_all_reduce` | True | True | `runner.seam_plan` | has no effect at TP = 1; leave it |

According to independent-f6, the seam reads only plan fields. The seam hash and the
environment lock are therefore unchanged, and no re-attestation is needed. What is
needed:

1. the code change, a `CHANGES_SCIENTIFIC.md` entry, and an abort note for
   `pilot-2026-10-25` in `docs/batch1`;
2. the researcher re-signs **D12** against its new payload hash. The other 13
   approvals stand if their hashes are unchanged; `freeze-protocol` checks this;
3. a new smoke test (D12's condition) at the new commit;
4. a new Freeze 1 and a new run root, then Stage 1 and Stage 2.

**Disclosure for `CHANGES_SCIENTIFIC.md` and D12, whatever is chosen:** Batch 1
evidence is the stored response record, not something regenerated from seeds.

- Regenerating any row, whether by `resume` after a technical failure or by an
  independent re-run, reproduces the same text in about 95–97% of rows, not all.
- Freeze 2 binds the accepted records by hash, so the evidence itself is fixed.
- The claim that is not supported is "re-running the frozen design reproduces the
  responses byte for byte".

## 6. For Batch 2 and later studies

Batch 2 (composed instructions) is not implemented yet. When its D12 successor is
written:

- **Batching:** start from eager mode with chunk 512 or larger, not 64.
- **CUDA graphs:** turn them on only with a determinism check like §3b first, and
  only if bit-reproducible regeneration is not needed.
- **Reproducibility:** if it is needed, evaluate vLLM's batch-invariant mode
  (`VLLM_BATCH_INVARIANT`) on this stack before freezing. It is currently off, and its
  throughput cost is unmeasured here.
- **Scaling to two GPUs:** schedule more model groups than GPUs. `execute --devices
  0,1` runs one group per GPU, so 4 models on 2 GPUs finish in two rounds.
