# v8 candidate pipeline: end-to-end validation (synthetic + retrospective gather)

Synthetic worlds run the whole chain with seeded draws at the registered sample sizes; the truth is the same rule set on the true parameters over each family's declared range. Retrospective numbers are read from the replay tools' JSON (development-level; see each file).

## Synthetic cases

| world | identified | truth | family accept TP/FP/FN | selected families | points | offset below/above | span | SE(β̂) | local found/true | forwarded rungs | reserve picks (2nd pass) | extension | gens to freeze |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | True | True | 5/0/0 | MK2, MK1, XC1, MK3 | 8 | 0.22/0.20 | 0.42 | 0.018 | 6/6 | 37 | {0: {'MK3': [9, 10]}} | {} | 36384 |
| narrow | False | True | 1/0/3 | MK4 | 2 | 0.18/0.15 | 0.34 | 0.034 | 4/4 | 19 | {0: {'MK1': [9, 10], 'MK2': [9, 10], 'MK3': [9, 10], 'MK4': [9, 10]}, 1: {'MK2': [11, 12]}, 2: {}} | {} | 23904 |
| flat | False | False | 0/0/0 |  | 0 | —/— | 0.00 | — | 4/4 | 16 | {} | {} | 19416 |
| one_sided | False | False | 0/0/0 | MK2, MK1, MK4, MK3 | 8 | 0.31/— | 0.00 | 0.025 | 3/4 | 16 | {} | {} | 19416 |
| outlier | True | True | 3/0/0 | MK2, MK1, MK3 | 6 | 0.30/0.16 | 0.46 | 0.019 | 4/4 | 23 | {} | {} | 24792 |
| too_easy_reserve | True | True | 4/0/0 | MK3, MK4, MK2, MK1 | 8 | 0.39/0.16 | 0.55 | 0.014 | 2/4 | 25 | {0: {'MK1': [9, 10], 'MK2': [9, 10], 'MK3': [9, 10]}, 1: {'MK1': [11, 12], 'MK2': [11, 12], 'MK3': [11, 12]}, 2: {}} | {} | 29136 |
| extremes | True | True | 3/0/0 | MK1, XC1, MK2 | 6 | 0.16/0.17 | 0.34 | 0.023 | 3/3 | 16 | {} | {} | 20328 |
| wording_confusion_v7 | True | True | 2/0/0 | MK1, MK2 | 4 | 0.15/0.12 | 0.27 | 0.032 | 2/2 | 15 | {} | {} | 18648 |
| wording_confusion_v8 | True | True | 4/0/0 | MK3, MK1, MK2, MK6 | 8 | 0.15/0.16 | 0.31 | 0.023 | 4/4 | 25 | {} | {} | 26328 |
- wide: first failing spectrum component — MK1:5:V_pos, MK2:5:V_pos, MK3:10:V_stab, MK3:5:V_pos, MK3:6:V_pos, MK5:5:V_pos, MK5:6:V_pos, MK5:8:V_pos, MK6:1:V_coord, MK6:4:V_stab, MK6:5:V_pos, XC1:4:V_pos
- narrow: coverage reasons — 1 points below A; 2 required; 1 families below A; 2 required; 1 families above A; 2 required
- narrow: first failing spectrum component — MK1:5:V_pos, MK1:6:V_pos, MK1:7:V_pos, MK1:8:V_stab, MK2:5:V_pos, MK2:6:V_pos, MK3:5:V_pos, MK3:6:V_pos, MK3:7:V_pos, MK4:4:V_pos, MK4:5:V_pos, MK4:6:V_pos
- flat: coverage reasons — 0 points below A; 2 required; 0 points above A; 2 required; 0 families below A; 2 required; 0 families above A; 2 required; no point at or beyond 0.1 below A; no point at or beyond 0.1 above A; total span 0.000 below 0.2; projected SE(beta) None above 0.05 (within-family leverage 0.0000)
- flat: first failing spectrum component — MK1:3:V_pos, MK1:4:V_pos, MK1:5:V_pos, MK1:6:V_stab, MK2:1:V_pos, MK2:3:V_pos, MK2:5:V_pos, MK2:8:V_pos, MK3:2:V_pos, MK3:6:V_pos, MK3:7:V_pos, XC1:2:V_pos
- one_sided: coverage reasons — 0 points above A; 2 required; 0 families above A; 2 required; no point at or beyond 0.1 above A; total span 0.000 below 0.2
- one_sided: first failing spectrum component — MK3:1:V_stab, MK4:1:V_pos, MK4:3:V_stab
- outlier: first failing spectrum component — MK1:5:V_pos, MK2:5:V_pos, MK3:5:V_pos, MK5:5:V_pos, MK5:6:V_pos, MK5:8:V_pos
- too_easy_reserve: first failing spectrum component — MK3:10:V_stab, MK3:11:V_stab, MK4:4:V_pos, MK4:5:V_pos, MK4:6:V_pos
- extremes: first failing spectrum component — MK1:5:V_pos, MK2:5:V_pos, XC1:4:V_pos
- wording_confusion_v7: first failing spectrum component — MK1:5:V_pos, MK2:5:V_pos
- wording_confusion_v8: first failing spectrum component — MK1:5:V_pos, MK2:5:V_pos, MK3:5:V_pos, MK3:7:V_stab, MK6:1:V_coord, MK6:5:V_pos

## Invariances

- same seed → identical record: True
- family order permuted → identical record: True
- composed outcome changed in the world → identical record: True
- new seed → same verdict and selected families: True (Monte Carlo numbers move: True)
- a composed column in a calibration table is refused by the loader: True
- composed identifiers named in the rule modules: none

## Wording instrument

v8 wording hash `fe3b5be15759af1c…`; renderings checked: 2696; differences from v7: 273 ({'the_word': 208, 'number': 65}).

## Retrospective (stored evidence, corrected chance basis)

Chance basis: unconstrained-cell (§13.2, corrected; dci1v8dev.chance_basis); pre-screen κ on the ladder run's unconstrained cell

| screen | precision | recall | FPR | predicted + | true + |
|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 0.46 | 0.70 | 0.13 | 93 | 61 |
| new stage 1 accept | 0.83 | 0.41 | 0.01 | 30 | 61 |
| new stage 1 accept-or-resample | 0.31 | 0.93 | 0.33 | 184 | 61 |
| new final accept (emulated second pass) | 0.73 | 0.72 | 0.04 | 60 | 61 |

Failure causes of pre-screen passes: {'NOISY_SPAN_INFLATION': 9, 'ELIGIBILITY_TRIMMING': 6, 'MISSING_SIDE': 3, 'IOTA_A_MOVED': 3, 'FLAT_LADDER': 0, 'NON_MONOTONIC': 0, 'RETENTION_ARTIFACT': 32, 'OTHER': 0}.
Retention artefacts: 32; refuted at the screen 6, accepted after the emulated second pass 9, undecidable (extremes never calibrated) 17; geometry retainable at the screen 5; chance mirages 19.
Local references: 105/117 calibrated-caliper rungs forwarded (§12.7: 117); why not: {'KEPT': 105, 'NOT_LABELLED_LOCAL': 10, 'FAMILY_NOT_FORWARDED': 1, 'OTHER_RUNGS_FORWARDED': 1}.
Rungs forwarded per replication: new [45, 64, 60, 51, 50, 56, 53, 49, 56, 57, 40, 50] vs §12.7 [132, 140, 112, 112, 134, 132, 112, 119, 112, 112, 112, 112]; calibration generations new [34560, 49152, 46080, 39168, 38400, 43008, 40704, 37632, 43008, 43776, 30720, 38400] vs [101376, 107520, 86016, 86016, 102912, 101376, 86016, 91392, 86016, 86016, 86016, 86016]; re-screen generations [10704, 6984, 7368, 8376, 7680, 11928, 11568, 10704, 8136, 6696, 8472, 9336].

Spectrum replay (unconstrained-cell (§13.2, corrected; dci1v8dev.chance_basis); pre-screen κ on the ladder run's unconstrained cell): {'n_replications': 12, 'v7_spectrum_identified': 2, 'new_spectrum_identified': 12, 'recorded_backup_inadmissible_replications': 10, 'meets_min_qualified_on_admissible_basis': 11}

| tree | model | identified | v7 | families | points | offset below/above | SE(β̂) | spectrum-valid (range) | admissible families | recorded backups inadmissible |
|---|---|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | True | True | MK5, MK4, MK2, MK1 | 8 | 0.22/0.15 | 0.018 | 59 (0.21–0.94) | 5 | CR5 |
| v7 | gemma-3n-e4b-it | True | False | MK1, MK4, MK2, MK5 | 8 | 0.21/0.17 | 0.017 | 81 (0.22–0.93) | 3 | MK1, MK2 |
| v7 | qwen3-4b | True | False | MK3, MK4, MK2, MK1 | 8 | 0.29/0.23 | 0.014 | 44 (0.22–0.93) | 6 | CR6 |
| v7 | qwen3-4b-instruct-2507 | True | False | MK3, MK8, MK4, XC1 | 8 | 0.28/0.31 | 0.013 | 37 (0.22–0.94) | 7 | CR6 |
| v6 | gemma-3n-e2b-it | True | True | MK5, MK4, MK1, MK2 | 8 | 0.21/0.16 | 0.020 | 57 (0.22–0.91) | 5 | CR5, CR6 |
| v6 | gemma-3n-e4b-it | True | False | MK1, MK2, MK4, MK5 | 8 | 0.22/0.17 | 0.016 | 70 (0.26–0.93) | 6 | CR6 |
| v6 | qwen3-4b | True | None | MK3, MK4, XC1, XC3 | 8 | 0.31/0.21 | 0.013 | 45 (0.22–0.93) | 7 |  |
| v6 | qwen3-4b-instruct-2507 | True | None | MK3, MK4, XC1, MK8 | 8 | 0.27/0.28 | 0.015 | 39 (0.22–0.94) | 8 |  |
| dev | qwen3-4b | True | False | MK3, MK4, MK2, MK1 | 8 | 0.31/0.23 | 0.013 | 45 (0.23–0.92) | 7 | CR6 |
| r3 | qwen3-4b | True | False | MK3, MK4, MK2, XC3 | 8 | 0.29/0.18 | 0.014 | 45 (0.23–0.92) | 6 | CR6 |
| r3 | gemma-3n-e2b-it | True | False | MK4, MK1 | 4 | 0.18/0.13 | 0.028 | 45 (0.20–0.94) | 5 | CR5, MK3 |
| r4 | qwen3-4b-instruct-2507 | True | False | MK3, MK8, MK4, XC1 | 8 | 0.29/0.32 | 0.013 | 37 (0.21–0.94) | 7 | CR6, MK1 |

Pre-screen simulation choice: {'event': 'support_both', 'd_below': 0.1, 'd_above': 0.1, 'accept': 0.8, 'reject': 0.2, 'final_accept_at': 0.5, 'fp': 0.146875, 'fn': 0.09312500000000001, 'objective': 0.24000000000000002, 'fraction_resampled': 0.4240625}
Coverage-gate simulation choice: {'d_below': 0.1, 'd_above': 0.1, 'min_total_span': 0.2, 'max_se_iota': 0.05, 'ppv': 0.9536915683704674, 'recall': 0.6332124728063815, 'n_gate_identified': 9156, 'n_truly_identifiable': 13790, 'acceptable': True} (current rule: {'d_below': 0.15, 'd_above': 0.1, 'min_total_span': 0.25, 'max_se_iota': 0.05, 'ppv': 0.9749401436552274, 'recall': 0.442929659173314, 'n_gate_identified': 6265, 'n_truly_identifiable': 13790, 'acceptable': True})

## Constants in force (dci1v8dev.rules)

```
{
"SPECTRUM_GUARD_BAND": [
0.1,
0.95
],
"SPECTRUM_D_MIN": 0.05,
"SPECTRUM_OFFSET_BELOW": 0.1,
"SPECTRUM_OFFSET_ABOVE": 0.1,
"SPECTRUM_MIN_TOTAL_SPAN": 0.2,
"SPECTRUM_MAX_SE_IOTA": 0.05,
"SPECTRUM_MAX_SE_BETA": 0.05,
"SPECTRUM_MIN_POINTS_BELOW": 2,
"SPECTRUM_MIN_POINTS_ABOVE": 2,
"SPECTRUM_MIN_FAMILIES_PER_SIDE": 2,
"SELECTION_TARGET_BELOW": 0.2,
"SELECTION_TARGET_ABOVE": 0.15,
"SELECTION_MAX_FAMILIES": 4,
"SELECTION_MIN_SEPARATION": 0.05,
"CONFIRMATORY_FRAME_OFFSETS": [
0,
1,
2,
3
],
"CONFIRMATORY_FRAME_PASSES": 4,
"CONFIRMATORY_BLOCKS_PER_FRAME": 384,
"CONFIRMATORY_BLOCKS_TOTAL": 1536,
"CONFIRMATORY_MAX_PASSES": 4,
"CONFIRMATORY_MAX_BLOCKS_PER_FRAME": 384,
"CALIBRATION_FRAME_OFFSETS": [
0,
1,
2,
3
],
"CALIBRATION_POLICY": "universal: every study model calibrates at CALIBRATION_FRAME_OFFSETS; no per-model override exists",
"CALIBRATION_FRAME_PASSES": 4,
"CALIBRATION_TOPICS_PER_FRAME": 192,
"CALIBRATION_TOPICS_PER_FRAME_PER_SPLIT": 96,
"CALIBRATION_GENERATIONS_PER_RUNG": 3072,
"CALIBRATION_MAX_PASSES": 4,
"CALIBRATION_MAX_TOPICS_PER_FRAME": 192,
"LOCAL_ELIGIBILITY_MIN_FRAMES": 2,
"OPERATING_POINT_BOOTSTRAP_RESAMPLES": 2000,
"OPERATING_POINT_MIN_RECOVERY": 0.6666666666666666,
"OPERATING_POINT_STABLE": "OPERATING_POINT_STABLE",
"OPERATING_POINT_UNSTABLE": "OPERATING_POINT_UNSTABLE",
"SCREEN_FRAME_OFFSETS": [
0,
1,
2,
3
],
"SCREEN_FRAME_PASSES": 4,
"SCREEN_TOPICS_PER_FRAME": 24,
"RETENTION_POLICY": "frame_aware",
"RETENTION_TARGET_BASIS": "calibration_iota_a",
"RETENTION_COMPARATOR": "legacy_pooled",
"RESCREEN_BATCH_LAYOUT": "topics",
"SCREEN_ACCEPT": 0.8,
"SCREEN_REJECT": 0.2,
"RESCREEN_FINAL_ACCEPT_AT": 0.5,
"LOCAL_LABEL_MIN": 0.25,
"RESCREEN_MAX_BATCHES": 3,
"RESCREEN_BATCH_TOPICS": 24,
"RESCREEN_RESERVE_PICKS_PER_BATCH": 2,
"EXTENSION_P_REACH": 0.8,
"EXTENSION_CALIBRATION_PICKS": 2,
"RETENTION_SPECTRUM_RUNGS": 5,
"RETENTION_LOCAL_RUNGS": 4,
"RETENTION_MAX_SPECTRUM_FAMILIES": 8,
"RETENTION_MAX_LOCAL_FAMILIES": 12,
"RETENTION_ADMISSIBLE_MIN": 0.5,
"RETENTION_CLASS_ARM_RUNGS": 2,
"RETENTION_NEAR_FORM_RUNGS": 3
}
```

Spectrum confirmatory cost: 55296 generations for 6 references, 73728 for 8 (solo:X, B+X, X+B on 384 blocks × 8).

