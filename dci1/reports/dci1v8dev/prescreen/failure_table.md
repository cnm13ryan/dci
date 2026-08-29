# Pre-screen vs calibration, family by family (read-only reconstruction)

Spans are §12.6's per-family C4 span over eligible rungs (raw max−min of ι); 'same rungs' restricts the pre-screen to the rungs calibration measured. Straddle = an eligible rung on each side of ι_A.

## v7 / gemma-3n-e2b-it — ι_A pre-screen 0.663, calibrated 0.617; legacy C4 groups 6 → 2

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.65 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:80 | 7 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.36) | SCREEN_REJECT (0.37) |
| CR5 | 3 | 0.84 | 0.22 | 0.09 | True | True | True | False | RETENTION_ARTIFACT | CR5:10, CR5:3, CR5:4, CR5:5, CR5:6 | 6 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.10) | SCREEN_REJECT (0.04) |
| MK1 | 1 | 0.50 | 0.50 | 0.34 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.03) | SCREEN_REJECT (0.03) |
| MK5 | 1 | 0.50 | 0.50 | 0.50 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.97) | SCREEN_ACCEPT (0.97) |
| RF11 | 3 | 0.51 | 0.23 | 0.28 | True | False | True | False | RETENTION_ARTIFACT | RF11:21 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.20) | SCREEN_REJECT (0.25) |
| RF12 | 3 | 0.46 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF12:3, RF12:4, RF12:5 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.00) | SCREEN_REJECT (0.00) |
| XC3 | 2 | 0.48 | 0.48 | 0.50 | True | True | True | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.07) | SCREEN_REJECT (0.03) |

## v7 / gemma-3n-e4b-it — ι_A pre-screen 0.666, calibrated 0.725; legacy C4 groups 11 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.54 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:85, CL7:90, CL7:95 | 10 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.52) | SCREEN_ACCEPT (0.52) |
| CR5 | 3 | 0.48 | 0.23 | 0.14 | True | False | True | False | RETENTION_ARTIFACT | CR5:5, CR5:9 | 8 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| MK1 | 1 | 0.50 | 0.50 | 0.47 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.97) | SCREEN_ACCEPT (0.97) |
| MK2 | 1 | 0.59 | 0.59 | 0.48 | True | True | True | True |  | MK2:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.93) | SCREEN_ACCEPT (0.93) |
| MK4 | 1 | 0.63 | 0.63 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.96) | SCREEN_ACCEPT (0.96) |
| MK5 | 1 | 0.46 | 0.46 | 0.49 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.91) | SCREEN_ACCEPT (0.91) |
| MK6 | 1 | 0.46 | 0.46 | 0.38 | True | False | True | False | IOTA_A_MOVED |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| RF10 | 3 | 0.79 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF10:12, RF10:15, RF10:19, RF10:21 | 11 | STRONG_LADDER | SCREEN_RESAMPLE (0.05) | SCREEN_REJECT (0.05) |
| RF11 | 3 | 0.66 | 0.10 | 0.09 | True | False | True | False | RETENTION_ARTIFACT | RF11:12, RF11:16, RF11:21, RF11:26, RF11:30 | 9 | STRONG_LADDER | SCREEN_RESAMPLE (0.25) | SCREEN_REJECT (0.33) |
| RF6 | 3 | 0.77 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:1, RF6:6, RF6:7, RF6:8 | 12 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.21) | SCREEN_REJECT (0.19) |
| RF9 | 3 | 0.64 | 0.12 | 0.13 | True | False | True | False | RETENTION_ARTIFACT | RF9:10, RF9:4, RF9:6, RF9:8 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.12) | SCREEN_REJECT (0.16) |

## v7 / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.683; legacy C4 groups 6 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.75 | 0.75 | 0.75 | True | True | True | True |  | MK3:6 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.40) | SCREEN_REJECT (0.47) |
| MK4 | 1 | 0.71 | 0.71 | 0.69 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.66) | SCREEN_ACCEPT (0.63) |
| MK5 | 1 | 0.75 | 0.75 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.45) | SCREEN_REJECT (0.17) |
| MK7 | 1 | 0.54 | 0.54 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.23) | SCREEN_REJECT (0.03) |
| XC1 | 2 | 0.71 | 0.71 | 0.60 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.35) | SCREEN_ACCEPT (0.74) |
| XC3 | 2 | 0.46 | 0.46 | 0.35 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:3, XC3:5, XC3:6 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.62) | SCREEN_REJECT (0.42) |
| MK1 | 1 | 0.21 | 0.21 | 0.14 | True | True | False | False |  | MK1:2 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.72) | SCREEN_ACCEPT (0.57) |
| MK2 | 1 | 0.38 | 0.38 | 0.39 | True | True | False | False |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.60) | SCREEN_ACCEPT (0.59) |
| RF6 | 3 | 5.95 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.71) | SCREEN_ACCEPT (0.62) |

## v7 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.666, calibrated 0.540; legacy C4 groups 10 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL8 | 3 | 0.56 | 0.09 | 0.19 | True | False | True | False | RETENTION_ARTIFACT | CL8:14, CL8:19, CL8:25 | 4 | STRONG_LADDER | SCREEN_RESAMPLE (0.17) | SCREEN_REJECT (0.06) |
| CR6 | 3 | 0.64 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR6:6, CR6:7 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.06) | SCREEN_REJECT (0.06) |
| MK3 | 1 | 0.71 | 0.71 | 0.76 | True | True | True | True |  | MK3:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.29) | SCREEN_ACCEPT (0.77) |
| MK4 | 1 | 0.67 | 0.67 | 0.61 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_ACCEPT (0.81) |
| MK5 | 1 | 0.62 | 0.62 | 0.19 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.74) | SCREEN_ACCEPT (0.62) |
| MK6 | 1 | 0.50 | 0.50 | 0.39 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.16) | SCREEN_REJECT (0.01) |
| MK7 | 1 | 0.42 | 0.42 | 0.37 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.38) | SCREEN_REJECT (0.02) |
| MK8 | 1 | 0.63 | 0.63 | 0.58 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.39) | SCREEN_REJECT (0.19) |
| RF11 | 3 | 0.63 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF11:12, RF11:16, RF11:8 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.02) | SCREEN_REJECT (0.01) |
| XC1 | 2 | 0.70 | 0.70 | 0.57 | True | True | True | True |  | XC1:7 | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.12) | SCREEN_REJECT (0.12) |

## v6 / gemma-3n-e2b-it — ι_A pre-screen 0.708, calibrated 0.629; legacy C4 groups 6 → 3

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.66 | 0.02 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:45, CL7:80 | 6 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.04) | SCREEN_REJECT (0.46) |
| CR5 | 3 | 0.98 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:10, CR5:2, CR5:3, CR5:4, CR5:5 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.18) | SCREEN_REJECT (0.01) |
| MK1 | 1 | 0.50 | 0.50 | 0.41 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.01) | SCREEN_REJECT (0.01) |
| MK2 | 1 | 0.42 | 0.42 | 0.22 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.03) | SCREEN_REJECT (0.03) |
| MK5 | 1 | 0.63 | 0.63 | 0.43 | True | True | True | True |  | MK5:2, MK5:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.81) | SCREEN_ACCEPT (0.81) |
| RF11 | 3 | 0.52 | 0.04 | 0.08 | True | False | True | False | RETENTION_ARTIFACT | RF11:21, RF11:26, RF11:30 | 8 | STRONG_LADDER | SCREEN_RESAMPLE (0.09) | SCREEN_REJECT (0.21) |
| XC3 | 2 | 0.51 | 0.51 | 0.60 | False | True | False | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |

## v6 / gemma-3n-e4b-it — ι_A pre-screen 0.708, calibrated 0.709; legacy C4 groups 10 → 3

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.58 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:60 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.36) | SCREEN_REJECT (0.35) |
| CR5 | 3 | 0.50 | 0.09 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:10, CR5:3, CR5:4, CR5:5, CR5:8 | 6 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.24) | SCREEN_REJECT (0.20) |
| MK1 | 1 | 0.50 | 0.50 | 0.49 | True | True | True | True |  | MK1:1 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.89) | SCREEN_ACCEPT (0.89) |
| MK2 | 1 | 0.54 | 0.54 | 0.45 | True | True | True | True |  | MK2:1, MK2:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.99) | SCREEN_ACCEPT (0.99) |
| MK4 | 1 | 0.59 | 0.59 | 0.55 | True | True | True | True |  | MK4:3 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.96) | SCREEN_ACCEPT (0.96) |
| MK5 | 1 | 0.42 | 0.42 | 0.32 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.87) | SCREEN_ACCEPT (0.87) |
| MK6 | 1 | 0.42 | 0.42 | 0.38 | True | False | True | False | IOTA_A_MOVED |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| RF11 | 3 | 0.66 | 0.18 | 0.12 | True | False | True | False | RETENTION_ARTIFACT | RF11:16, RF11:21 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.24) | SCREEN_REJECT (0.31) |
| RF12 | 3 | 0.48 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF12:3, RF12:4, RF12:5, RF12:6 | 7 | STRONG_LADDER | SCREEN_RESAMPLE (0.06) | SCREEN_REJECT (0.03) |
| RF6 | 3 | 0.74 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:1, RF6:6, RF6:7, RF6:8 | 12 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.20) | SCREEN_REJECT (0.20) |
| XC3 | 2 | 0.56 | 0.56 | 0.33 | True | False | True | False | MISSING_SIDE |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.01) | SCREEN_REJECT (0.00) |

## v6 / qwen3-4b — ι_A pre-screen 0.750, calibrated 0.704; legacy C4 groups 9 → 6

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK2 | 1 | 0.42 | 0.42 | 0.43 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.57) | SCREEN_ACCEPT (0.63) |
| MK3 | 1 | 0.71 | 0.71 | 0.77 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.20) | SCREEN_REJECT (0.20) |
| MK4 | 1 | 0.75 | 0.75 | 0.68 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.50) | SCREEN_ACCEPT (0.67) |
| MK5 | 1 | 0.50 | 0.50 | 0.62 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.15) | SCREEN_REJECT (0.15) |
| MK7 | 1 | 0.46 | 0.46 | 0.52 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.07) | SCREEN_REJECT (0.07) |
| RF12 | 3 | 1.03 | 0.09 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF12:1, RF12:5, RF12:6, RF12:8 | 3 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| RF5 | 3 | 0.75 | 0.25 | 0.15 | True | False | True | False | RETENTION_ARTIFACT | RF5:5, RF5:8 | 6 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.00) | SCREEN_REJECT (0.00) |
| RF6 | 3 | 6.01 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | RF6:10, RF6:11, RF6:12, RF6:2, RF6:4 | 11 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.46) | SCREEN_REJECT (0.39) |
| XC1 | 2 | 0.71 | 0.71 | 0.58 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.45) | SCREEN_ACCEPT (0.65) |
| XC3 | 2 | 0.44 | 0.44 | 0.38 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:5 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.25) | SCREEN_REJECT (0.38) |

## v6 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.875, calibrated 0.565; legacy C4 groups 0 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.50 | 0.50 | 0.75 | False | True | False | True |  | MK3:8 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.53) | SCREEN_ACCEPT (0.55) |
| MK4 | 1 | 0.58 | 0.58 | 0.62 | False | True | False | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.51) | SCREEN_ACCEPT (0.58) |
| MK6 | 1 | 0.25 | 0.25 | 0.42 | False | True | False | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.06) | SCREEN_REJECT (0.00) |
| MK8 | 1 | 0.58 | 0.58 | 0.55 | False | True | False | True |  |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.12) | SCREEN_REJECT (0.12) |
| XC1 | 2 | 0.62 | 0.62 | 0.60 | False | True | False | True |  | XC1:7 | 0 | STRONG_LADDER | SCREEN_REJECT (0.10) | SCREEN_REJECT (0.10) |

## dev / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.688; legacy C4 groups 7 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK2 | 1 | 0.46 | 0.46 | 0.39 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.73) | SCREEN_ACCEPT (0.74) |
| MK3 | 1 | 0.75 | 0.75 | 0.76 | True | True | True | True |  | MK3:6 | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.42) | SCREEN_REJECT (0.43) |
| MK4 | 1 | 0.71 | 0.71 | 0.69 | True | True | True | True |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.67) | SCREEN_ACCEPT (0.70) |
| MK5 | 1 | 0.58 | 0.58 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.40) | SCREEN_REJECT (0.13) |
| MK7 | 1 | 0.50 | 0.50 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.12) | SCREEN_REJECT (0.12) |
| XC1 | 2 | 0.75 | 0.75 | 0.61 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.58) | SCREEN_ACCEPT (0.55) |
| XC3 | 2 | 0.41 | 0.41 | 0.39 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:3, XC3:5 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.33) | SCREEN_REJECT (0.33) |
| RF6 | 3 | 6.09 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.71) | SCREEN_ACCEPT (0.57) |

## r3 / qwen3-4b — ι_A pre-screen 0.708, calibrated 0.685; legacy C4 groups 6 → 5

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MK3 | 1 | 0.71 | 0.71 | 0.76 | True | True | True | True |  | MK3:6 | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.41) | SCREEN_ACCEPT (0.61) |
| MK4 | 1 | 0.67 | 0.67 | 0.69 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.63) | SCREEN_ACCEPT (0.56) |
| MK5 | 1 | 0.71 | 0.71 | 0.64 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.37) | SCREEN_REJECT (0.25) |
| MK7 | 1 | 0.54 | 0.54 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_REJECT (0.19) | SCREEN_REJECT (0.19) |
| XC1 | 2 | 0.75 | 0.75 | 0.61 | True | True | True | True |  | XC1:1 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.68) | SCREEN_ACCEPT (0.65) |
| XC3 | 2 | 0.50 | 0.50 | 0.36 | True | True | True | False | ELIGIBILITY_TRIMMING | XC3:3, XC3:5 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.74) | SCREEN_REJECT (0.40) |
| MK1 | 1 | 0.25 | 0.25 | 0.15 | True | True | False | False |  | MK1:2 | 0 | STRONG_LADDER | SCREEN_ACCEPT (0.80) | SCREEN_ACCEPT (0.80) |
| MK2 | 1 | 0.38 | 0.38 | 0.39 | True | True | False | False |  |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.45) | SCREEN_ACCEPT (0.60) |
| RF6 | 3 | 5.29 | 0.00 | 0.00 | False | False | False | False |  | RF6:10, RF6:11, RF6:12, RF6:2, RF6:5 | 11 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.71) | SCREEN_ACCEPT (0.58) |

## r3 / gemma-3n-e2b-it — ι_A pre-screen 0.577, calibrated 0.609; legacy C4 groups 7 → 1

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CL7 | 3 | 0.53 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CL7:100, CL7:60 | 7 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.44) | SCREEN_REJECT (0.45) |
| CR5 | 3 | 0.87 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR5:1, CR5:10, CR5:3, CR5:4, CR5:5 | 7 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.33) | SCREEN_REJECT (0.30) |
| MK1 | 1 | 0.58 | 0.58 | 0.32 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.29) | SCREEN_REJECT (0.03) |
| MK2 | 1 | 0.46 | 0.46 | 0.20 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_REJECT (0.14) | SCREEN_REJECT (0.14) |
| MK5 | 1 | 0.46 | 0.46 | 0.30 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.48) | SCREEN_REJECT (0.37) |
| RF12 | 3 | 0.48 | 0.02 | 0.28 | True | True | True | False | RETENTION_ARTIFACT | RF12:3, RF12:4, RF12:5 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.00) | SCREEN_REJECT (0.00) |
| RF6 | 3 | 0.42 | 0.07 | 0.16 | True | True | True | False | RETENTION_ARTIFACT | RF6:2, RF6:6 | 9 | NON_MONOTONIC_LADDER | SCREEN_REJECT (0.16) | SCREEN_REJECT (0.16) |
| XC3 | 2 | 0.55 | 0.55 | 0.49 | True | True | True | True |  |  | 0 | NON_MONOTONIC_LADDER | SCREEN_RESAMPLE (0.02) | SCREEN_REJECT (0.02) |

## r4 / qwen3-4b-instruct-2507 — ι_A pre-screen 0.666, calibrated 0.540; legacy C4 groups 8 → 4

| family | tier | pre span | same rungs | cal span | pre straddle | cal straddle | pre C4 | cal C4 | cause | rungs disappeared | not calibrated | ladder | stage-1 | final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CR6 | 3 | 0.76 | 0.00 | 0.00 | True | False | True | False | RETENTION_ARTIFACT | CR6:6, CR6:7 | 6 | STRONG_LADDER | SCREEN_RESAMPLE (0.08) | SCREEN_REJECT (0.09) |
| MK3 | 1 | 0.75 | 0.75 | 0.79 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.56) | SCREEN_ACCEPT (0.80) |
| MK4 | 1 | 0.67 | 0.67 | 0.60 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.68) | SCREEN_ACCEPT (0.84) |
| MK5 | 1 | 0.58 | 0.58 | 0.19 | True | True | True | False | ELIGIBILITY_TRIMMING | MK5:4 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.72) | SCREEN_ACCEPT (0.50) |
| MK6 | 1 | 0.50 | 0.50 | 0.40 | True | True | True | False | NOISY_SPAN_INFLATION |  | 0 | USABLE_NOISY_LADDER | SCREEN_RESAMPLE (0.19) | SCREEN_REJECT (0.00) |
| MK8 | 1 | 0.71 | 0.71 | 0.57 | True | True | True | True |  |  | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.28) | SCREEN_REJECT (0.27) |
| RF11 | 3 | 0.63 | 0.16 | 0.36 | True | True | True | False | RETENTION_ARTIFACT | RF11:12, RF11:8 | 5 | STRONG_LADDER | SCREEN_RESAMPLE (0.03) | SCREEN_REJECT (0.00) |
| XC1 | 2 | 0.75 | 0.75 | 0.58 | True | True | True | True |  | XC1:7 | 0 | STRONG_LADDER | SCREEN_RESAMPLE (0.32) | SCREEN_REJECT (0.17) |

