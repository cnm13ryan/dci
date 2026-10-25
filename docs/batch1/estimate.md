# Batch 1 pilot: generation-count and cost estimate

Generated from `estimate.json`. Historical rates are not a measurement of any cloud instance.

- Stage 1 generations: **15,616** (A 768, B 1,536, reference 13,056, task_only 256)
- Stage 2 ceiling: **15,360** (240 cells × 64)
- Total ceiling: **30,976**
- Storage ceiling: ~248 MB (generated rows plus scored records)
- Generation time at historical rates: Stage 1 0.501 h; Stage 2 0.493 h if spread evenly, at most 0.652 h

| model | Stage 1 rows | Stage 2 rows (even / max) | rows/s (7900 XTX, v8.1) | Stage 1 h | Stage 2 h (even / max) |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | 3,904 | 3,840 / 7,680 | 9.7 | 0.112 | 0.11 / 0.22 |
| gemma-3n-e4b-it | 3,904 | 3,840 / 7,680 | 4.94 | 0.22 | 0.216 / 0.432 |
| qwen3-4b | 3,904 | 3,840 / 7,680 | 17.4 | 0.062 | 0.061 / 0.123 |
| qwen3-4b-instruct-2507 | 3,904 | 3,840 / 7,680 | 10.1 | 0.107 | 0.106 / 0.211 |

## Caveats

- rates are v8.1 confirmatory rows/s on one AMD RX 7900 XTX at chunk size 64 and ~130 response tokens; they exclude model load (~2-5 min per backend run) and are not a property of any NVIDIA or Lambda instance
- Stage 2 is bounded by stage2_max_cells; its split across models is decided by Stage 1 data, so 'if_even' is illustrative and 'max' is the per-model ceiling
- a cloud estimate needs an authorised throughput smoke test on the chosen instance type (rows/s per model at this cap and chunk size, model load time, and truncation share)
