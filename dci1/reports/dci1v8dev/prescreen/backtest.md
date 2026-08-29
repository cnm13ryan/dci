# Pre-screen backtest on stored evidence (development candidate)

Screen configuration: {'source': '/home/cnm13ryan/git/dci-v8-canonical/dci1/reports/dci1v8dev/prescreen/simulation.json', 'event': 'support_both', 'd_below': 0.1, 'd_above': 0.1, 'accept': 0.8, 'reject': 0.2, 'final_accept_at': 0.5, 'fp': 0.146875, 'fn': 0.09312500000000001, 'objective': 0.24000000000000002, 'fraction_resampled': 0.4240625}

Chance basis of every calibrated verdict: unconstrained-cell (§13.2, corrected; dci1v8dev.chance_basis); pre-screen κ on the ladder run's unconstrained cell.

Read-only over the registered v7 and v6 trees and the completed development rehearsals. The second pass is EMULATED by carving 24-topic batches from Calibration-A's per-topic rows (no reserve rungs, no A-grid re-measurement); the 'Calibration-B only' truth shares no topic with the carved batches. Family-level rows: one per (replication, family).

## Family-level metrics

### Truth: calibrated C4 (production, pooled)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 93 | 47 | 40 | 53 | 7 | 0.43 | 0.85 | 0.13 |
| new stage 1 accept | 30 | 47 | 16 | 14 | 31 | 0.53 | 0.34 | 0.04 |
| new stage 1 accept-or-resample | 184 | 47 | 45 | 139 | 2 | 0.24 | 0.96 | 0.35 |
| new final accept (emulated second pass) | 60 | 47 | 31 | 29 | 16 | 0.52 | 0.66 | 0.07 |

### Truth: calibrated support-both (pooled)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 93 | 61 | 43 | 50 | 18 | 0.46 | 0.70 | 0.13 |
| new stage 1 accept | 30 | 61 | 25 | 5 | 36 | 0.83 | 0.41 | 0.01 |
| new stage 1 accept-or-resample | 184 | 61 | 57 | 127 | 4 | 0.31 | 0.93 | 0.33 |
| new final accept (emulated second pass) | 60 | 61 | 44 | 16 | 17 | 0.73 | 0.72 | 0.04 |

### Truth: calibrated support-both (Calibration-B only)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 93 | 62 | 46 | 47 | 16 | 0.49 | 0.74 | 0.12 |
| new stage 1 accept | 30 | 62 | 25 | 5 | 37 | 0.83 | 0.40 | 0.01 |
| new stage 1 accept-or-resample | 184 | 62 | 57 | 127 | 5 | 0.31 | 0.92 | 0.33 |
| new final accept (emulated second pass) | 60 | 62 | 45 | 15 | 17 | 0.75 | 0.73 | 0.04 |

### Truth: calibrated C4 (Calibration-B only)

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 93 | 47 | 41 | 52 | 6 | 0.44 | 0.87 | 0.13 |
| new stage 1 accept | 30 | 47 | 16 | 14 | 31 | 0.53 | 0.34 | 0.04 |
| new stage 1 accept-or-resample | 184 | 47 | 45 | 139 | 2 | 0.24 | 0.96 | 0.35 |
| new final accept (emulated second pass) | 60 | 47 | 32 | 28 | 15 | 0.53 | 0.68 | 0.07 |

## Replication level

| tree | model | legacy groups (pre-screen) | groups calibrated | C4 pre | C4 cal | pass→fail families | stage-1 accept | stage-1 resample | final accept | final accept & calibrated | forwarded new | forwarded legacy | re-screen gens | calibration gens new | legacy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | 8 | 2 | True | False | 6 | 1 | 13 | 2 | 1 | 45 | 132 | 10704 | 34560 | 101376 |
| v7 | gemma-3n-e4b-it | 12 | 4 | True | False | 8 | 4 | 8 | 7 | 4 | 64 | 140 | 6984 | 49152 | 107520 |
| v7 | qwen3-4b | 7 | 5 | True | False | 2 | 5 | 12 | 8 | 7 | 60 | 112 | 7368 | 46080 | 86016 |
| v7 | qwen3-4b-instruct-2507 | 9 | 4 | True | False | 5 | 2 | 14 | 4 | 2 | 51 | 112 | 8376 | 39168 | 86016 |
| v6 | gemma-3n-e2b-it | 7 | 3 | True | False | 6 | 1 | 9 | 2 | 1 | 50 | 134 | 7680 | 38400 | 102912 |
| v6 | gemma-3n-e4b-it | 9 | 3 | True | False | 6 | 4 | 14 | 6 | 4 | 56 | 132 | 11928 | 43008 | 101376 |
| v6 | qwen3-4b | 10 | 6 | True | True | 5 | 1 | 18 | 6 | 6 | 53 | 112 | 11568 | 40704 | 86016 |
| v6 | qwen3-4b-instruct-2507 | 0 | 5 | False | False | 0 | 0 | 14 | 3 | 3 | 49 | 119 | 10704 | 37632 | 91392 |
| dev | qwen3-4b | 7 | 5 | True | False | 2 | 5 | 13 | 8 | 7 | 56 | 112 | 8136 | 43008 | 86016 |
| r3 | qwen3-4b | 6 | 5 | True | False | 1 | 5 | 12 | 8 | 7 | 57 | 112 | 6696 | 43776 | 86016 |
| r3 | gemma-3n-e2b-it | 9 | 1 | True | False | 8 | 0 | 13 | 3 | 0 | 40 | 112 | 8472 | 30720 | 86016 |
| r4 | qwen3-4b-instruct-2507 | 8 | 4 | True | False | 4 | 2 | 14 | 3 | 2 | 50 | 112 | 9336 | 38400 | 86016 |

## Retention recovery: the historical RETENTION_ARTIFACT families

32 pre-screen passes were lost to §12.7's nearest-24 Tier-3 retention. Under the new screen: 6 are refuted at stage 1 (their spread rests on chance-inflated or lift-less rungs: a mirage, not a loss); 9 are accepted after the emulated second pass and forwarded with their spaced set (4 with a rung beyond each offset); 17 are rejected by the emulated pass, which could not measure their dropped extremes (never calibrated) — of these 1 have admissible rungs on both offsets at the screen, which the spaced retention would carry if the production pass accepted them; 0 are rejected with every rung measurable. Geometry retainable at the screen (an admissible rung at or beyond both offsets): 5/32.

| tree | model | family | tier | class | stage-1 (P) | final (P) | P(below)/P(above) | dropped by §12.7 | retainable | mirage rungs | forwarded (new) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | CL7 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.34) | SCREEN_REJECT (0.40) | 0.93/0.38 | CL7:10, CL7:100, CL7:130, CL7:20, CL7:30 | False | CL7:10, CL7:20, CL7:30 | CL7:45, CL7:60, CL7:80 |
| v7 | gemma-3n-e2b-it | CR5 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.06) | 1.00/0.29 | CR5:10, CR5:3, CR5:4, CR5:5, CR5:6 | False | CR5:10 | CR5:1, CR5:2, CR5:3, CR5:6 |
| v7 | gemma-3n-e2b-it | RF11 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.69) | SCREEN_ACCEPT (0.81) | 0.97/0.71 | RF11:0, RF11:12, RF11:16, RF11:21, RF11:4 | False |  | RF11:21, RF11:26, RF11:27, RF11:28, RF11:29, RF11:30, RF11:32 |
| v7 | gemma-3n-e2b-it | RF9 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.16) | SCREEN_REJECT (0.16) | 1.00/0.16 | RF9:0, RF9:10, RF9:16, RF9:17, RF9:18 | False | RF9:18, RF9:19, RF9:20 |  |
| v7 | gemma-3n-e4b-it | CL7 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.73) | SCREEN_ACCEPT (0.73) | 1.00/0.73 | CL7:10, CL7:100, CL7:130, CL7:20, CL7:30 | True | CL7:10, CL7:20, CL7:30 | CL7:100, CL7:60, CL7:80, CL7:85, CL7:90 |
| v7 | gemma-3n-e4b-it | CR5 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.03) | SCREEN_REJECT (0.03) | 0.03/1.00 | CR5:1, CR5:12, CR5:13, CR5:2, CR5:3 | False | CR5:11, CR5:12, CR5:13 |  |
| v7 | gemma-3n-e4b-it | RF10 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.07) | SCREEN_REJECT (0.06) | 0.53/0.17 | RF10:0, RF10:12, RF10:15, RF10:19, RF10:2 | False | RF10:22, RF10:23 | RF10:20 |
| v7 | gemma-3n-e4b-it | RF11 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.90) | 0.98/0.81 | RF11:0, RF11:12, RF11:16, RF11:21, RF11:26 | True |  | RF11:12, RF11:21, RF11:26, RF11:27, RF11:28, RF11:30, RF11:32 |
| v7 | gemma-3n-e4b-it | RF6 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.35) | SCREEN_REJECT (0.18) | 0.63/0.58 | RF6:0, RF6:1, RF6:10, RF6:11, RF6:12 | False | RF6:8, RF6:9, RF6:10, RF6:11 | RF6:1, RF6:2 |
| v7 | gemma-3n-e4b-it | RF9 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.63) | SCREEN_ACCEPT (0.84) | 1.00/0.63 | RF9:0, RF9:10, RF9:16, RF9:2, RF9:4 | False |  | RF9:11, RF9:12, RF9:13, RF9:14, RF9:15, RF9:4, RF9:8 |
| v7 | qwen3-4b | RF11 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.35) | SCREEN_REJECT (0.27) | 0.91/0.40 | RF11:0, RF11:26, RF11:32, RF11:4, RF11:8 | False | RF11:32 | RF11:12, RF11:16, RF11:21 |
| v7 | qwen3-4b-instruct-2507 | RF11 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.32) | SCREEN_REJECT (0.13) | 0.99/0.33 | RF11:0, RF11:12, RF11:16, RF11:32, RF11:4 | False | RF11:32 | RF11:12, RF11:16, RF11:21, RF11:26 |
| v7 | qwen3-4b-instruct-2507 | RF7 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) | 1.00/0.00 | RF7:0, RF7:1, RF7:10, RF7:11, RF7:12 | False |  |  |
| v6 | gemma-3n-e2b-it | CL7 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.07) | SCREEN_REJECT (0.39) | 0.98/0.08 | CL7:10, CL7:100, CL7:130, CL7:20, CL7:30 | False | CL7:10, CL7:20, CL7:30 | CL7:100, CL7:45, CL7:60, CL7:80 |
| v6 | gemma-3n-e2b-it | CR5 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.42) | SCREEN_REJECT (0.12) | 1.00/0.42 | CR5:10, CR5:2, CR5:3, CR5:4, CR5:5 | False |  | CR5:1, CR5:2, CR5:3, CR5:5 |
| v6 | gemma-3n-e2b-it | RF11 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.46) | SCREEN_ACCEPT (0.58) | 0.99/0.46 | RF11:0, RF11:12, RF11:16, RF11:21, RF11:26 | False |  | RF11:21, RF11:26, RF11:27, RF11:28, RF11:29, RF11:30, RF11:32 |
| v6 | gemma-3n-e2b-it | RF3 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.10) | SCREEN_REJECT (0.10) | 0.76/0.14 | RF3:0, RF3:1, RF3:2, RF3:3, RF3:4 | False | RF3:8 | RF3:5 |
| v6 | gemma-3n-e2b-it | RF9 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.39) | SCREEN_REJECT (0.31) | 1.00/0.39 | RF9:0, RF9:13, RF9:14, RF9:17, RF9:2 | False | RF9:18 | RF9:10, RF9:4, RF9:6, RF9:8 |
| v6 | gemma-3n-e4b-it | CL7 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.60) | SCREEN_ACCEPT (0.60) | 0.95/0.63 | CL7:10, CL7:100, CL7:130, CL7:20, CL7:30 | True | CL7:10, CL7:20, CL7:30 | CL7:100, CL7:60, CL7:80 |
| v6 | gemma-3n-e4b-it | CR5 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.48) | SCREEN_REJECT (0.43) | 0.48/1.00 | CR5:1, CR5:10, CR5:2, CR5:4, CR5:5 | False | CR5:10 | CR5:4, CR5:5, CR5:6, CR5:8 |
| v6 | gemma-3n-e4b-it | RF11 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.68) | SCREEN_ACCEPT (0.90) | 0.99/0.69 | RF11:0, RF11:12, RF11:16, RF11:21, RF11:4 | False |  | RF11:16, RF11:21, RF11:26, RF11:27, RF11:28, RF11:29, RF11:30 |
| v6 | gemma-3n-e4b-it | RF6 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.26) | 0.52/0.60 | RF6:0, RF6:1, RF6:10, RF6:11, RF6:12 | False | RF6:8, RF6:9, RF6:10, RF6:11 | RF6:1, RF6:2 |
| v6 | qwen3-4b | RF11 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.04) | SCREEN_REJECT (0.03) | 0.99/0.04 | RF11:0, RF11:12, RF11:16, RF11:26, RF11:32 | False | RF11:32 | RF11:12, RF11:16, RF11:21, RF11:8 |
| v6 | qwen3-4b | RF3 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.13) | SCREEN_REJECT (0.13) | 0.81/0.22 | RF3:0, RF3:2, RF3:3, RF3:4, RF3:5 | False | RF3:3, RF3:4, RF3:5, RF3:6 | RF3:0, RF3:1, RF3:2 |
| v6 | qwen3-4b | RF6 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.63) | SCREEN_REJECT (0.46) | 0.77/0.84 | RF6:10, RF6:11, RF6:12, RF6:2, RF6:3 | True | RF6:6, RF6:7, RF6:8, RF6:9 | RF6:1, RF6:2 |
| dev | qwen3-4b | RF11 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.33) | SCREEN_REJECT (0.22) | 0.95/0.35 | RF11:0, RF11:12, RF11:26, RF11:32, RF11:4 | False | RF11:32 | RF11:12, RF11:16, RF11:21, RF11:8 |
| r3 | gemma-3n-e2b-it | CL7 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.51) | SCREEN_ACCEPT (0.53) | 0.97/0.53 | CL7:10, CL7:100, CL7:130, CL7:20, CL7:30 | False | CL7:10, CL7:20, CL7:30 | CL7:100, CL7:45, CL7:60, CL7:80 |
| r3 | gemma-3n-e2b-it | CR5 | 3 | SECOND_PASS_ACCEPTED | SCREEN_RESAMPLE (0.61) | SCREEN_ACCEPT (0.58) | 1.00/0.61 | CR5:1, CR5:10, CR5:3, CR5:4, CR5:5 | True | CR5:10 | CR5:1, CR5:2, CR5:3, CR5:4, CR5:6 |
| r3 | gemma-3n-e2b-it | RF6 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.13) | SCREEN_REJECT (0.13) | 0.67/0.21 | RF6:0, RF6:11, RF6:12, RF6:2, RF6:3 | False | RF6:8, RF6:9, RF6:10, RF6:11 | RF6:1 |
| r3 | gemma-3n-e2b-it | RF9 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.24) | SCREEN_REJECT (0.24) | 0.99/0.24 | RF9:0, RF9:10, RF9:16, RF9:2, RF9:4 | False |  | RF9:10, RF9:13, RF9:6, RF9:8 |
| r4 | qwen3-4b-instruct-2507 | RF11 | 3 | SECOND_PASS_UNDECIDABLE | SCREEN_RESAMPLE (0.41) | SCREEN_REJECT (0.29) | 0.98/0.43 | RF11:0, RF11:12, RF11:32, RF11:4, RF11:8 | False | RF11:32 | RF11:12, RF11:16, RF11:21, RF11:26 |
| r4 | qwen3-4b-instruct-2507 | RF7 | 3 | REFUTED_AT_SCREEN | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) | 1.00/0.00 | RF7:0, RF7:1, RF7:10, RF7:11, RF7:12 | False |  |  |

## Local-reference recovery (detail)

117 family-replications calibrated a chance/lift-admissible rung inside the ±0.10 caliper. The new retention forwards that very rung for 105 (1 forward other rungs of the family, 10 are not labelled local at the screen, 1 labelled but not forwarded); §12.7 forwarded it for 117.


## Local-reference recovery

Families with a rung inside the ±0.10 caliper at calibration: 117; kept by the new retention: 106; by §12.7: 117.

## Failure causes (pre-screen PASS → calibration FAIL, per family)

53 of 93 pre-screen passes failed at calibration.

| cause | families |
|---|---|
| NOISY_SPAN_INFLATION | 9 |
| ELIGIBILITY_TRIMMING | 6 |
| MISSING_SIDE | 3 |
| IOTA_A_MOVED | 3 |
| FLAT_LADDER | 0 |
| NON_MONOTONIC | 0 |
| RETENTION_ARTIFACT | 32 |
| OTHER | 0 |

## retrospective development (LOMO): stage1_p vs calibration_support_both

| held-out model | chosen accept | train precision | train recall | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.5 | 0.74 | 0.76 | 0.22 | 0.33 | 0.07 | 6 |
| gemma-3n-e4b-it | 0.4 | 0.63 | 0.77 | 0.57 | 1.00 | 0.09 | 8 |
| qwen3-4b | 0.25 | 0.43 | 0.80 | 0.74 | 1.00 | 0.09 | 31 |
| qwen3-4b-instruct-2507 | 0.6 | 0.72 | 0.76 | 0.67 | 0.50 | 0.04 | 16 |

## retrospective development (LOMO): stage1_p_c4 vs calibration_c4

| held-out model | chosen accept | train precision | train recall | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.7 | 0.71 | 0.88 | 0.40 | 0.67 | 0.06 | 6 |
| gemma-3n-e4b-it | 0.7 | 0.72 | 0.82 | 0.47 | 1.00 | 0.12 | 7 |
| qwen3-4b | 0.7 | 0.54 | 0.77 | 0.83 | 0.95 | 0.03 | 21 |
| qwen3-4b-instruct-2507 | 0.8 | 0.68 | 0.76 | 0.70 | 0.54 | 0.03 | 13 |
