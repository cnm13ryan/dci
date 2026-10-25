# Batch 1 pilot: generation-count and cost estimate

Generated from `estimate.json`. Historical rates are not a measurement of any cloud instance.

- Stage 1 generations: **63,936** (A 1,152, B 768, reference 61,824, task_only 192)
- Stage 2 ceiling: **88,320** (920 cells × 64)
- Total ceiling: **152,256**
- Storage ceiling: ~1,218 MB (generated rows plus scored records)
- Generation time at historical rates: Stage 1 2.052 h; Stage 2 2.833 h if spread evenly, at most 3.381 h

| model | Stage 1 rows | Stage 2 rows (even / max) | rows/s (7900 XTX, v8.1) | Stage 1 h | Stage 2 h (even / max) |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | 15,984 | 22,080 / 31,872 | 9.7 | 0.458 | 0.632 / 0.913 |
| gemma-3n-e4b-it | 15,984 | 22,080 / 31,872 | 4.94 | 0.899 | 1.242 / 1.792 |
| qwen3-4b | 15,984 | 22,080 / 31,872 | 17.4 | 0.255 | 0.352 / 0.509 |
| qwen3-4b-instruct-2507 | 15,984 | 22,080 / 31,872 | 10.1 | 0.44 | 0.607 / 0.877 |

## Caveats

- rates are v8.1 confirmatory rows/s on one AMD RX 7900 XTX at chunk size 64 and ~130 response tokens; they exclude model load (~2-5 min per backend run) and are not a property of any NVIDIA or Lambda instance
- Stage 2 is bounded by stage2_max_cells; its split across models is decided by Stage 1 data, so 'if_even' is illustrative and 'max' is the per-model ceiling
- a cloud estimate needs an authorised throughput smoke test on the chosen instance type (rows/s per model at this cap and chunk size, model load time, and truncation share)
