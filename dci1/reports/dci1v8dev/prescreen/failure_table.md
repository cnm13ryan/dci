# Pre-screen vs calibration, family by family (read-only reconstruction)

Spans are §12.6's per-family C4 span over eligible rungs (raw max−min of ι); 'same rungs' restricts the pre-screen to the rungs calibration measured. Straddle = an eligible rung on each side of ι_A.

## v7 / gemma-3n-e2b-it — ι_A pre-screen 0.652, calibrated 0.621; legacy C4 groups 8 → 2

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.67 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:80 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.34) | SCREEN_REJECT (0.40) |
| CR5 | 3 | 1.79 | 0.21 | 0.09 | True | True | True | False | RETENTION_ARTIFACT | CR5:10, CR5:3, CR5:4, CR5:5, CR5:6 | 6 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.06) |
| MK1 | 1 | 0.50 | 0.50 | 0.34 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.20) | SCREEN_REJECT (0.20) |
| MK5 | 1 | 0.50 | 0.50 | 0.50 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.99) | SCREEN_ACCEPT (0.99) |
| RF11 | 3 | 0.45 | 0.16 | 0.25 | True | True | True | False | RETENTION_ARTIFACT | RF11:21 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.69) | SCREEN_ACCEPT (0.81) |
| RF9 | 3 | 0.57 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF9:10, RF9:16, RF9:2, RF9:6, RF9:8 | 11 | STRONG_LADDER | SCREEN_RESAMPLE (0.16) | SCREEN_REJECT (0.16) |
| XC1 | 2 | 0.52 | 0.52 | 0.44 | True | False | True | False | MISSING_SIDE |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| XC3 | 2 | 0.74 | 0.74 | 0.46 | True | True | True | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.31) | SCREEN_REJECT (0.15) |

## v7 / gemma-3n-e4b-it — ι_A pre-screen 0.667, calibrated 0.732; legacy C4 groups 12 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.54 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:85, CL7:90, CL7:95 | 10 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.73) | SCREEN_ACCEPT (0.73) |
| CR5 | 3 | 0.86 | 0.35 | 0.24 | True | True | True | False | RETENTION_ARTIFACT | CR5:5, CR5:9 | 8 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.03) | SCREEN_REJECT (0.03) |
| MK1 | 1 | 0.50 | 0.50 | 0.47 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (1.00) | SCREEN_ACCEPT (1.00) |
| MK2 | 1 | 0.58 | 0.58 | 0.48 | True | True | True | True |  | MK2:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.99) | SCREEN_ACCEPT (0.99) |
| MK4 | 1 | 0.62 | 0.62 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (1.00) | SCREEN_ACCEPT (1.00) |
| MK5 | 1 | 0.46 | 0.46 | 0.49 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.97) | SCREEN_ACCEPT (0.97) |
| MK6 | 1 | 0.46 | 0.46 | 0.38 | True | False | True | False | IOTA_A_MOVED |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.03) | SCREEN_REJECT (0.03) |
| RF10 | 3 | 0.73 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF10:12, RF10:15, RF10:19, RF10:21 | 11 | STRONG_LADDER | SCREEN_RESAMPLE (0.07) | SCREEN_REJECT (0.06) |
| RF11 | 3 | 0.67 | 0.07 | 0.08 | True | True | True | False | RETENTION_ARTIFACT | RF11:12, RF11:16, RF11:21, RF11:26, RF11:30 | 9 | STRONG_LADDER | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.90) |
| RF6 | 3 | 5.83 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:1, RF6:6, RF6:7, RF6:8 | 12 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.35) | SCREEN_REJECT (0.18) |
| RF9 | 3 | 0.67 | 0.08 | 0.07 | True | False | True | False | RETENTION_ARTIFACT | RF9:10, RF9:4, RF9:6, RF9:8 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_ACCEPT (0.84) |
| XC3 | 2 | 0.52 | 0.52 | 0.70 | True | False | True | False | IOTA_A_MOVED |  | 0 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |

## v7 / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.685; legacy C4 groups 7 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.74 | 0.74 | 0.75 | True | True | True | True |  | MK3:6 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.62) | SCREEN_ACCEPT (0.65) |
| MK4 | 1 | 0.71 | 0.71 | 0.69 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.88) |
| MK5 | 1 | 0.75 | 0.75 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.84) | SCREEN_ACCEPT (0.84) |
| MK7 | 1 | 0.54 | 0.54 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.48) | SCREEN_REJECT (0.05) |
| RF11 | 3 | 0.63 | 0.30 | 0.33 | True | True | True | False | RETENTION_ARTIFACT | RF11:8 | 5 | STRONG_LADDER | SCREEN_RESAMPLE (0.35) | SCREEN_REJECT (0.27) |
| XC1 | 2 | 0.71 | 0.71 | 0.60 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.62) | SCREEN_ACCEPT (0.87) |
| XC3 | 2 | 0.42 | 0.42 | 0.34 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:3, XC3:5, XC3:6 | 0 | USABLE_NOISY_LADDER | SCREEN_ACCEPT (0.80) | SCREEN_ACCEPT (0.80) |
| MK1 | 1 | 0.21 | 0.21 | 0.14 | True | True | False | False |  | MK1:2 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.95) | SCREEN_ACCEPT (0.95) |
| MK2 | 1 | 0.38 | 0.38 | 0.39 | True | True | False | False |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.86) | SCREEN_ACCEPT (0.86) |
| RF6 | 3 | 7.38 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_ACCEPT (0.83) | SCREEN_ACCEPT (0.83) |

## v7 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.667, calibrated 0.565; legacy C4 groups 9 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.71 | 0.71 | 0.76 | True | True | True | True |  | MK3:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.60) | SCREEN_ACCEPT (0.84) |
| MK4 | 1 | 0.67 | 0.67 | 0.61 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.84) | SCREEN_ACCEPT (0.84) |
| MK5 | 1 | 0.62 | 0.62 | 0.19 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.90) | SCREEN_ACCEPT (0.90) |
| MK6 | 1 | 0.50 | 0.50 | 0.39 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.45) | SCREEN_REJECT (0.26) |
| MK7 | 1 | 0.42 | 0.42 | 0.37 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.74) | SCREEN_ACCEPT (0.81) |
| MK8 | 1 | 0.62 | 0.62 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_REJECT (0.36) |
| RF11 | 3 | 0.69 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF11:12, RF11:16, RF11:8 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.32) | SCREEN_REJECT (0.13) |
| RF7 | 3 | 0.56 | 0.10 | 0.22 | True | True | True | False | RETENTION_ARTIFACT | RF7:10, RF7:13, RF7:14, RF7:16, RF7:17 | 21 | STRONG_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| XC1 | 2 | 0.71 | 0.71 | 0.56 | True | True | True | True |  | XC1:7 | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.28) | SCREEN_REJECT (0.12) |

## v6 / gemma-3n-e2b-it — ι_A pre-screen 0.708, calibrated 0.634; legacy C4 groups 7 → 3

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.67 | 0.17 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:45, CL7:80 | 6 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.07) | SCREEN_REJECT (0.39) |
| CR5 | 3 | 0.96 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:10, CR5:2, CR5:3, CR5:4, CR5:5 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.42) | SCREEN_REJECT (0.12) |
| MK2 | 1 | 0.42 | 0.42 | 0.22 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.52) | SCREEN_REJECT (0.00) |
| MK5 | 1 | 0.62 | 0.62 | 0.43 | True | True | True | True |  | MK5:2, MK5:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.97) | SCREEN_ACCEPT (0.97) |
| RF11 | 3 | 0.47 | 0.03 | 0.07 | True | False | True | False | RETENTION_ARTIFACT | RF11:21, RF11:26, RF11:30 | 8 | STRONG_LADDER | SCREEN_RESAMPLE (0.46) | SCREEN_ACCEPT (0.58) |
| RF3 | 3 | 0.48 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF3:2, RF3:3, RF3:4, RF3:6, RF3:7 | 8 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.10) | SCREEN_REJECT (0.10) |
| RF9 | 3 | 0.56 | 0.10 | 0.08 | True | False | True | False | RETENTION_ARTIFACT | RF9:13, RF9:14, RF9:4, RF9:6, RF9:8 | 8 | STRONG_LADDER | SCREEN_RESAMPLE (0.39) | SCREEN_REJECT (0.31) |
| MK1 | 1 | 0.50 | 0.50 | 0.41 | False | True | False | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.04) | SCREEN_REJECT (0.04) |
| XC3 | 2 | 0.88 | 0.88 | 0.54 | False | True | False | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.01) | SCREEN_REJECT (0.01) |

## v6 / gemma-3n-e4b-it — ι_A pre-screen 0.708, calibrated 0.716; legacy C4 groups 9 → 3

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.58 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:60 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.60) | SCREEN_ACCEPT (0.60) |
| CR5 | 3 | 0.86 | 0.12 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:10, CR5:3, CR5:4, CR5:5, CR5:8 | 6 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.48) | SCREEN_REJECT (0.43) |
| MK1 | 1 | 0.50 | 0.50 | 0.49 | True | True | True | True |  | MK1:1 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.98) | SCREEN_ACCEPT (0.98) |
| MK2 | 1 | 0.54 | 0.54 | 0.45 | True | True | True | True |  | MK2:1, MK2:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (1.00) | SCREEN_ACCEPT (1.00) |
| MK4 | 1 | 0.58 | 0.58 | 0.55 | True | True | True | True |  | MK4:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (1.00) | SCREEN_ACCEPT (1.00) |
| MK5 | 1 | 0.42 | 0.42 | 0.32 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.99) | SCREEN_ACCEPT (0.99) |
| RF11 | 3 | 0.66 | 0.10 | 0.09 | True | True | True | False | RETENTION_ARTIFACT | RF11:16, RF11:21 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.68) | SCREEN_ACCEPT (0.90) |
| RF6 | 3 | 2.83 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:1, RF6:6, RF6:7, RF6:8 | 12 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.26) |
| XC3 | 2 | 0.78 | 0.78 | 0.70 | True | False | True | False | MISSING_SIDE |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.09) | SCREEN_REJECT (0.00) |

## v6 / qwen3-4b — ι_A pre-screen 0.750, calibrated 0.706; legacy C4 groups 10 → 6

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK2 | 1 | 0.42 | 0.42 | 0.43 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.82) |
| MK3 | 1 | 0.71 | 0.71 | 0.77 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.39) | SCREEN_ACCEPT (0.78) |
| MK4 | 1 | 0.75 | 0.75 | 0.68 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.67) | SCREEN_ACCEPT (0.70) |
| MK5 | 1 | 0.50 | 0.50 | 0.62 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.38) | SCREEN_REJECT (0.40) |
| MK7 | 1 | 0.46 | 0.46 | 0.52 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.23) | SCREEN_REJECT (0.11) |
| RF11 | 3 | 0.60 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF11:12, RF11:16, RF11:26, RF11:8 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.04) | SCREEN_REJECT (0.03) |
| RF12 | 3 | 2.88 | 2.88 | 0.00 | True | False | True | False | MISSING_SIDE | RF12:1, RF12:5, RF12:6, RF12:8 | 4 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.01) | SCREEN_REJECT (0.01) |
| RF3 | 3 | 0.64 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF3:0, RF3:2, RF3:3 | 8 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.13) | SCREEN_REJECT (0.13) |
| RF6 | 3 | 5.88 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:10, RF6:11, RF6:12, RF6:2, RF6:4 | 11 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_REJECT (0.46) |
| XC1 | 2 | 0.70 | 0.70 | 0.58 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.66) | SCREEN_ACCEPT (0.82) |
| XC3 | 2 | 0.41 | 0.41 | 0.37 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:5 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.41) | SCREEN_ACCEPT (0.55) |
| MK1 | 1 | 0.29 | 0.29 | 0.36 | True | True | False | False |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.84) | SCREEN_ACCEPT (0.84) |

## v6 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.875, calibrated 0.591; legacy C4 groups 0 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.50 | 0.50 | 0.75 | False | True | False | True |  | MK3:8 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.69) | SCREEN_ACCEPT (0.75) |
| MK4 | 1 | 0.58 | 0.58 | 0.62 | False | True | False | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.66) | SCREEN_ACCEPT (0.68) |
| MK5 | 1 | 0.29 | 0.29 | 0.22 | False | True | False | False |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.77) | SCREEN_ACCEPT (0.58) |
| MK6 | 1 | 0.25 | 0.25 | 0.42 | False | True | False | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.35) |
| MK8 | 1 | 0.58 | 0.58 | 0.55 | False | True | False | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.22) | SCREEN_REJECT (0.27) |
| XC1 | 2 | 0.62 | 0.62 | 0.59 | False | True | False | True |  | XC1:7 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.22) | SCREEN_REJECT (0.25) |

## dev / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.690; legacy C4 groups 7 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK2 | 1 | 0.46 | 0.46 | 0.39 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.89) | SCREEN_ACCEPT (0.89) |
| MK3 | 1 | 0.74 | 0.74 | 0.76 | True | True | True | True |  | MK3:6 | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.62) | SCREEN_ACCEPT (0.78) |
| MK4 | 1 | 0.71 | 0.71 | 0.69 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_ACCEPT (0.80) | SCREEN_ACCEPT (0.80) |
| MK5 | 1 | 0.58 | 0.58 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.83) |
| MK7 | 1 | 0.50 | 0.50 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.34) | SCREEN_REJECT (0.14) |
| RF11 | 3 | 0.58 | 0.17 | 0.20 | True | True | True | False | RETENTION_ARTIFACT | RF11:12, RF11:8 | 6 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.33) | SCREEN_REJECT (0.22) |
| XC1 | 2 | 0.75 | 0.75 | 0.61 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.82) | SCREEN_ACCEPT (0.82) |
| MK1 | 1 | 0.25 | 0.25 | 0.16 | True | True | False | False |  | MK1:2 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.96) | SCREEN_ACCEPT (0.96) |
| RF6 | 3 | 7.38 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_ACCEPT (0.82) | SCREEN_ACCEPT (0.82) |
| XC3 | 2 | 0.38 | 0.38 | 0.34 | True | True | False | False |  | XC3:3, XC3:5 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.55) | SCREEN_ACCEPT (0.65) |

## r3 / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.688; legacy C4 groups 6 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.70 | 0.70 | 0.76 | True | True | True | True |  | MK3:6 | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_ACCEPT (0.83) |
| MK4 | 1 | 0.67 | 0.67 | 0.69 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.75) | SCREEN_ACCEPT (0.88) |
| MK5 | 1 | 0.71 | 0.71 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.82) | SCREEN_ACCEPT (0.82) |
| MK7 | 1 | 0.54 | 0.54 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.45) | SCREEN_REJECT (0.12) |
| XC1 | 2 | 0.75 | 0.75 | 0.61 | True | True | True | True |  | XC1:1 | 0 | NON_MONOTONIC_LADDER | SCREEN_ACCEPT (0.88) | SCREEN_ACCEPT (0.88) |
| XC3 | 2 | 0.46 | 0.46 | 0.35 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:3, XC3:5 | 0 | USABLE_NOISY_LADDER | SCREEN_ACCEPT (0.86) | SCREEN_ACCEPT (0.86) |
| MK1 | 1 | 0.25 | 0.25 | 0.15 | True | True | False | False |  | MK1:2 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.97) | SCREEN_ACCEPT (0.97) |
| MK2 | 1 | 0.37 | 0.37 | 0.39 | True | True | False | False |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.75) | SCREEN_ACCEPT (0.82) |
| RF6 | 3 | 11.38 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_ACCEPT (0.83) | SCREEN_ACCEPT (0.83) |

## r3 / gemma-3n-e2b-it — ι_A pre-screen 0.571, calibrated 0.613; legacy C4 groups 9 → 1

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.54 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:60 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.51) | SCREEN_ACCEPT (0.53) |
| CR5 | 3 | 1.83 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:1, CR5:10, CR5:3, CR5:4, CR5:5 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.61) | SCREEN_ACCEPT (0.58) |
| MK1 | 1 | 0.58 | 0.58 | 0.32 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.60) | SCREEN_REJECT (0.18) |
| MK2 | 1 | 0.46 | 0.46 | 0.20 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.41) | SCREEN_REJECT (0.23) |
| MK5 | 1 | 0.46 | 0.46 | 0.30 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.75) | SCREEN_REJECT (0.43) |
| RF6 | 3 | 0.77 | 0.30 | 0.50 | True | False | True | False | RETENTION_ARTIFACT | RF6:2, RF6:6 | 9 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.13) | SCREEN_REJECT (0.13) |
| RF9 | 3 | 0.51 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF9:10, RF9:6, RF9:8 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.24) | SCREEN_REJECT (0.24) |
| XC1 | 2 | 0.47 | 0.47 | 0.43 | True | False | True | False | IOTA_A_MOVED |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| XC3 | 2 | 0.79 | 0.79 | 0.44 | True | True | True | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.15) | SCREEN_REJECT (0.11) |
| RF11 | 3 | 0.41 | 0.00 | 0.00 | True | False | False | False |  | RF11:21 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.53) | SCREEN_ACCEPT (0.53) |

## r4 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.667, calibrated 0.566; legacy C4 groups 8 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.75 | 0.75 | 0.79 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.79) | SCREEN_ACCEPT (0.91) |
| MK4 | 1 | 0.67 | 0.67 | 0.60 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.86) | SCREEN_ACCEPT (0.86) |
| MK5 | 1 | 0.58 | 0.58 | 0.19 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.89) | SCREEN_ACCEPT (0.89) |
| MK6 | 1 | 0.50 | 0.50 | 0.40 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.46) | SCREEN_REJECT (0.12) |
| MK8 | 1 | 0.71 | 0.71 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.50) | SCREEN_REJECT (0.31) |
| RF11 | 3 | 0.70 | 0.16 | 0.32 | True | True | True | False | RETENTION_ARTIFACT | RF11:12, RF11:8 | 5 | STRONG_LADDER | SCREEN_RESAMPLE (0.41) | SCREEN_REJECT (0.29) |
| RF7 | 3 | 0.56 | 0.10 | 0.22 | True | True | True | False | RETENTION_ARTIFACT | RF7:10, RF7:13, RF7:14, RF7:16, RF7:17 | 21 | STRONG_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| XC1 | 2 | 0.74 | 0.74 | 0.57 | True | True | True | True |  | XC1:7 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.51) | SCREEN_REJECT (0.14) |

