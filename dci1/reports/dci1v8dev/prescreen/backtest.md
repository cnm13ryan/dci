# Pre-screen backtest on stored evidence (development candidate)

Screen configuration: {'source': '/home/cnm13ryan/git/dci-v8-prescreen/dci1/reports/dci1v8dev/prescreen/simulation.json', 'event': 'support_both', 'd_below': 0.15, 'd_above': 0.15, 'accept': 0.8, 'reject': 0.2, 'final_accept_at': 0.5, 'fp': 0.0763888888888889, 'fn': 0.13375, 'objective': 0.2101388888888889, 'fraction_resampled': 0.5604166666666666}

Read-only over the registered v7 and v6 trees and the completed development rehearsals. The second pass is EMULATED by carving 24-topic batches from Calibration-A's per-topic rows (no reserve rungs, no A-grid re-measurement); the 'Calibration-B only' truth shares no topic with the carved batches. Family-level rows: one per (replication, family).

## Family-level metrics

### Truth: calibrated C4 (production, pooled)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 47 | 41 | 49 | 6 | 0.46 | 0.87 | 0.12 |
| new stage 1 accept | 11 | 47 | 9 | 2 | 38 | 0.82 | 0.19 | 0.01 |
| new stage 1 accept-or-resample | 165 | 47 | 37 | 128 | 10 | 0.22 | 0.79 | 0.32 |
| new final accept (emulated second pass) | 37 | 47 | 25 | 12 | 22 | 0.68 | 0.53 | 0.03 |

### Truth: calibrated support-both (pooled)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 45 | 36 | 54 | 9 | 0.40 | 0.80 | 0.14 |
| new stage 1 accept | 11 | 45 | 9 | 2 | 36 | 0.82 | 0.20 | 0.01 |
| new stage 1 accept-or-resample | 165 | 45 | 40 | 125 | 5 | 0.24 | 0.89 | 0.31 |
| new final accept (emulated second pass) | 37 | 45 | 28 | 9 | 17 | 0.76 | 0.62 | 0.02 |

### Truth: calibrated support-both (Calibration-B only)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 46 | 36 | 54 | 10 | 0.40 | 0.78 | 0.14 |
| new stage 1 accept | 11 | 46 | 10 | 1 | 36 | 0.91 | 0.22 | 0.00 |
| new stage 1 accept-or-resample | 165 | 46 | 43 | 122 | 3 | 0.26 | 0.93 | 0.31 |
| new final accept (emulated second pass) | 37 | 46 | 29 | 8 | 17 | 0.78 | 0.63 | 0.02 |

### Truth: calibrated C4 (Calibration-B only)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 48 | 43 | 47 | 5 | 0.48 | 0.90 | 0.12 |
| new stage 1 accept | 11 | 48 | 9 | 2 | 39 | 0.82 | 0.19 | 0.01 |
| new stage 1 accept-or-resample | 165 | 48 | 38 | 127 | 10 | 0.23 | 0.79 | 0.32 |
| new final accept (emulated second pass) | 37 | 48 | 25 | 12 | 23 | 0.68 | 0.52 | 0.03 |

## Replication level

| tree | model | legacy groups (pre-screen) | groups calibrated | C4 pre | C4 cal | pass→fail families | stage-1 accept | stage-1 resample | final accept | final accept & calibrated | forwarded new | forwarded legacy | re-screen gens | calibration gens new | legacy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | 6 | 2 | True | False | 5 | 1 | 11 | 1 | 1 | 29 | 132 | 9792 | 22272 | 101376 |
| v7 | gemma-3n-e4b-it | 11 | 4 | True | False | 7 | 4 | 11 | 5 | 4 | 43 | 140 | 10128 | 33024 | 107520 |
| v7 | qwen3-4b | 6 | 5 | True | False | 1 | 0 | 16 | 5 | 3 | 36 | 112 | 10080 | 27648 | 86016 |
| v7 | qwen3-4b-instruct-2507 | 10 | 4 | True | False | 6 | 0 | 15 | 3 | 2 | 36 | 112 | 9864 | 27648 | 86016 |
| v6 | gemma-3n-e2b-it | 6 | 3 | True | False | 4 | 1 | 8 | 1 | 1 | 29 | 134 | 7368 | 22272 | 102912 |
| v6 | gemma-3n-e4b-it | 10 | 3 | True | False | 8 | 4 | 13 | 4 | 3 | 40 | 132 | 10848 | 30720 | 101376 |
| v6 | qwen3-4b | 9 | 6 | True | True | 4 | 0 | 14 | 3 | 3 | 35 | 112 | 9840 | 26880 | 86016 |
| v6 | qwen3-4b-instruct-2507 | 0 | 5 | False | False | 0 | 0 | 10 | 2 | 2 | 26 | 119 | 7152 | 19968 | 91392 |
| dev | qwen3-4b | 7 | 5 | True | False | 2 | 0 | 15 | 4 | 3 | 35 | 112 | 9840 | 26880 | 86016 |
| r3 | qwen3-4b | 6 | 5 | True | False | 1 | 1 | 14 | 6 | 4 | 38 | 112 | 9648 | 29184 | 86016 |
| r3 | gemma-3n-e2b-it | 7 | 1 | True | False | 7 | 0 | 10 | 0 | 0 | 25 | 112 | 6408 | 19200 | 86016 |
| r4 | qwen3-4b-instruct-2507 | 8 | 4 | True | False | 4 | 0 | 17 | 3 | 2 | 35 | 112 | 10464 | 26880 | 86016 |

## Local-reference recovery

Families with a rung inside the ±0.10 caliper at calibration: 135; kept by the new retention: 92; by §12.7: 135.

## Failure causes (pre-screen PASS → calibration FAIL, per family)

49 of 90 pre-screen passes failed at calibration.

| cause | families |
|---|---|
| NOISY_SPAN_INFLATION | 9 |
| ELIGIBILITY_TRIMMING | 7 |
| MISSING_SIDE | 1 |
| IOTA_A_MOVED | 2 |
| FLAT_LADDER | 0 |
| NON_MONOTONIC | 0 |
| RETENTION_ARTIFACT | 30 |
| OTHER | 0 |

## retrospective development (LOMO): stage1_p vs calibration_support_both

| held-out model | chosen accept | train precision | train recall | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.35 | 0.68 | 0.76 | 0.40 | 0.67 | 0.03 | 3 |
| gemma-3n-e4b-it | 0.3 | 0.62 | 0.79 | 0.70 | 1.00 | 0.04 | 7 |
| qwen3-4b | 0.25 | 0.56 | 0.82 | 0.69 | 0.96 | 0.08 | 23 |
| qwen3-4b-instruct-2507 | 0.4 | 0.69 | 0.82 | 0.62 | 0.42 | 0.03 | 12 |

## retrospective development (LOMO): stage1_p_c4 vs calibration_c4

| held-out model | chosen accept | train precision | train recall | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.8 | 0.74 | 0.76 | 0.40 | 0.33 | 0.03 | 6 |
| gemma-3n-e4b-it | 0.7 | 0.73 | 0.80 | 0.47 | 1.00 | 0.12 | 7 |
| qwen3-4b | 0.55 | 0.49 | 0.81 | 0.72 | 1.00 | 0.06 | 21 |
| qwen3-4b-instruct-2507 | 0.8 | 0.70 | 0.76 | 0.70 | 0.54 | 0.03 | 13 |
