# Pre-screen simulation (development candidate)

n_sims per archetype = 120; every number is synthetic. Legacy = the v7 per-family C4 certificate on 24-topic point estimates; New = the posterior-predictive screen with the targeted second pass. FP/FN are against the TRUE event on the true parameters.

## Chosen thresholds (prospective)

Rule: minimise FP + FN over archetypes (equal weight, both A curves); tie-break: smaller resample fraction, larger d_below, lower accept

| rank | event | d_below | d_above | accept | reject | final at | FP | FN | resampled |
|---|---|---|---|---|---|---|---|---|---|
| 1 | support_both | 0.15 | 0.15 | 0.8 | 0.2 | 0.5 | 0.076 | 0.134 | 0.56 |
| 2 | support_both | 0.2 | 0.1 | 0.75 | 0.15 | 0.75 | 0.088 | 0.134 | 0.53 |
| 3 | support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.5 | 0.115 | 0.111 | 0.48 |
| 4 | support_both | 0.2 | 0.1 | 0.85 | 0.2 | 0.7 | 0.087 | 0.155 | 0.61 |
| 5 | support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.5 | 0.140 | 0.104 | 0.56 |
| 6 | support_both | 0.2 | 0.1 | 0.7 | 0.15 | 0.5 | 0.157 | 0.088 | 0.49 |
| 7 | support_both | 0.15 | 0.1 | 0.7 | 0.15 | 0.5 | 0.142 | 0.103 | 0.43 |
| 8 | support_both | 0.15 | 0.15 | 0.7 | 0.15 | 0.5 | 0.102 | 0.145 | 0.45 |
| 9 | support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.8 | 0.070 | 0.177 | 0.56 |
| 10 | support_both | 0.15 | 0.1 | 0.85 | 0.2 | 0.7 | 0.078 | 0.173 | 0.52 |
| 11 | support_both | 0.15 | 0.15 | 0.85 | 0.2 | 0.7 | 0.041 | 0.232 | 0.65 |
| 12 | support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.8 | 0.067 | 0.207 | 0.48 |

## Per archetype, at the chosen configuration

### A curve: qwen3-4b-like (iota_A~0.68)

| archetype | true event | true C4 | legacy pass | legacy FP | legacy FN | new accept | new FP | new FN | resampled | mean batches | P(cal C4 \| legacy pass) | P(cal event \| new accept) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | True | True | 0.89 | 0.00 | 0.11 | 1.00 | 0.00 | 0.00 | 0.39 | 0.62 | 1.00 | 1.00 |
| narrow_noisy | False | False | 0.11 | 0.11 | 0.00 | 0.01 | 0.01 | 0.00 | 0.63 | 1.18 | 0.00 | 0.00 |
| borderline | True | False | 0.33 | 0.33 | 0.00 | 0.81 | 0.00 | 0.19 | 0.86 | 2.02 | 0.10 | 0.76 |
| one_sided | False | False | 0.30 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — |
| flat | False | False | 0.03 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.22 | 0.23 | 0.00 | — |
| outlier | True | True | 0.84 | 0.00 | 0.16 | 1.00 | 0.00 | 0.00 | 0.57 | 0.93 | 1.00 | 0.97 |
| ceiling | True | True | 0.88 | 0.00 | 0.12 | 1.00 | 0.00 | 0.00 | 0.46 | 0.68 | 1.00 | 1.00 |
| too_easy_reserve | True | True | 0.00 | 0.00 | 1.00 | 0.71 | 0.00 | 0.29 | 1.00 | 2.67 | — | 1.00 |

### A curve: qwen-2507-like (iota_A~0.55)

| archetype | true event | true C4 | legacy pass | legacy FP | legacy FN | new accept | new FP | new FN | resampled | mean batches | P(cal C4 \| legacy pass) | P(cal event \| new accept) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | True | True | 0.88 | 0.00 | 0.12 | 0.99 | 0.00 | 0.01 | 0.55 | 0.88 | 1.00 | 1.00 |
| narrow_noisy | False | False | 0.14 | 0.14 | 0.00 | 0.02 | 0.02 | 0.00 | 0.81 | 1.67 | 0.00 | 0.00 |
| borderline | False | False | 0.28 | 0.28 | 0.00 | 0.58 | 0.58 | 0.00 | 0.90 | 2.44 | 0.09 | 0.03 |
| one_sided | False | True | 0.41 | 0.00 | 0.59 | 0.00 | 0.00 | 0.00 | 0.02 | 0.02 | 0.82 | — |
| flat | False | False | 0.07 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.25 | 0.33 | 0.00 | — |
| outlier | True | True | 0.89 | 0.00 | 0.11 | 1.00 | 0.00 | 0.00 | 0.68 | 1.17 | 1.00 | 0.99 |
| ceiling | True | True | 0.85 | 0.00 | 0.15 | 1.00 | 0.00 | 0.00 | 0.63 | 0.97 | 1.00 | 0.98 |
| too_easy_reserve | True | True | 0.00 | 0.00 | 1.00 | 0.33 | 0.00 | 0.68 | 1.00 | 2.69 | — | 0.90 |

## Whole grid (pooled over archetypes)

| event | d_below | d_above | accept | reject | final at | A curve | legacy FP | legacy FN | new FP | new FN | resampled | mean re-screen gens | survival legacy | survival new |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| support_both | 0.15 | 0.1 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.35 | 0.05 | 0.06 | 0.41 | 398 | 0.46 | 0.80 |
| support_both | 0.15 | 0.1 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.24 | 0.15 | 0.46 | 466 | 0.57 | 0.64 |
| support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.33 | 0.03 | 0.05 | 0.44 | 433 | 0.45 | 0.80 |
| support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.18 | 0.42 | 0.20 | 0.17 | 0.51 | 525 | 0.57 | 0.64 |
| support_both | 0.15 | 0.1 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.34 | 0.03 | 0.14 | 0.42 | 417 | 0.46 | 0.81 |
| support_both | 0.15 | 0.1 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.17 | 0.41 | 0.18 | 0.21 | 0.46 | 488 | 0.57 | 0.66 |
| support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.33 | 0.01 | 0.17 | 0.44 | 433 | 0.45 | 0.80 |
| support_both | 0.15 | 0.1 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.18 | 0.42 | 0.12 | 0.25 | 0.51 | 525 | 0.57 | 0.62 |
| support_both | 0.15 | 0.1 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.34 | 0.01 | 0.12 | 0.49 | 472 | 0.46 | 0.81 |
| support_both | 0.15 | 0.1 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.41 | 0.14 | 0.23 | 0.56 | 567 | 0.55 | 0.64 |
| support_both | 0.2 | 0.1 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.35 | 0.19 | 0.17 | 0.46 | 466 | 0.54 | 0.73 |
| support_both | 0.2 | 0.1 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.14 | 0.40 | 0.12 | 0.00 | 0.52 | 530 | 0.63 | 0.54 |
| support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.19 | 0.20 | 0.51 | 498 | 0.52 | 0.72 |
| support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.38 | 0.10 | 0.01 | 0.61 | 600 | 0.57 | 0.63 |
| support_both | 0.2 | 0.1 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.17 | 0.34 | 0.13 | 0.22 | 0.49 | 486 | 0.53 | 0.88 |
| support_both | 0.2 | 0.1 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.14 | 0.39 | 0.04 | 0.05 | 0.56 | 572 | 0.62 | 0.67 |
| support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.10 | 0.25 | 0.51 | 498 | 0.52 | 0.87 |
| support_both | 0.2 | 0.1 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.38 | 0.04 | 0.10 | 0.61 | 600 | 0.57 | 0.62 |
| support_both | 0.2 | 0.1 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.33 | 0.14 | 0.23 | 0.55 | 534 | 0.46 | 0.71 |
| support_both | 0.2 | 0.1 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.14 | 0.38 | 0.03 | 0.08 | 0.66 | 662 | 0.60 | 0.72 |
| support_both | 0.15 | 0.15 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.18 | 0.35 | 0.01 | 0.10 | 0.40 | 371 | 0.45 | 0.79 |
| support_both | 0.15 | 0.15 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.42 | 0.19 | 0.19 | 0.50 | 474 | 0.60 | 0.56 |
| support_both | 0.15 | 0.15 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.35 | 0.00 | 0.10 | 0.52 | 476 | 0.44 | 0.79 |
| support_both | 0.15 | 0.15 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.40 | 0.15 | 0.17 | 0.60 | 579 | 0.56 | 0.65 |
| support_both | 0.15 | 0.15 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.01 | 0.23 | 0.46 | 437 | 0.43 | 0.78 |
| support_both | 0.15 | 0.15 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.11 | 0.25 | 0.54 | 505 | 0.60 | 0.55 |
| support_both | 0.15 | 0.15 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.35 | 0.00 | 0.29 | 0.52 | 476 | 0.44 | 0.94 |
| support_both | 0.15 | 0.15 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.40 | 0.06 | 0.28 | 0.60 | 579 | 0.56 | 0.65 |
| support_both | 0.15 | 0.15 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.33 | 0.00 | 0.22 | 0.61 | 582 | 0.51 | 0.95 |
| support_both | 0.15 | 0.15 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.17 | 0.41 | 0.08 | 0.24 | 0.70 | 691 | 0.62 | 0.79 |
| c4 | 0.15 | 0.1 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.23 | 0.22 | 0.50 | 427 | 0.45 | 0.58 |
| c4 | 0.15 | 0.1 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.18 | 0.40 | 0.28 | 0.35 | 0.52 | 484 | 0.61 | 0.68 |
| c4 | 0.15 | 0.1 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.34 | 0.21 | 0.22 | 0.51 | 427 | 0.52 | 0.64 |
| c4 | 0.15 | 0.1 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.42 | 0.30 | 0.34 | 0.55 | 490 | 0.57 | 0.71 |
| c4 | 0.15 | 0.1 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.37 | 0.22 | 0.22 | 0.52 | 426 | 0.45 | 0.58 |
| c4 | 0.15 | 0.1 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.14 | 0.41 | 0.25 | 0.38 | 0.55 | 507 | 0.60 | 0.67 |
| c4 | 0.15 | 0.1 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.34 | 0.20 | 0.24 | 0.51 | 427 | 0.52 | 0.67 |
| c4 | 0.15 | 0.1 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.42 | 0.30 | 0.38 | 0.55 | 490 | 0.57 | 0.69 |
| c4 | 0.15 | 0.1 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.21 | 0.34 | 0.20 | 0.24 | 0.52 | 444 | 0.52 | 0.60 |
| c4 | 0.15 | 0.1 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.40 | 0.28 | 0.36 | 0.59 | 516 | 0.57 | 0.71 |

## Archetypes

- **wide** (MK1): retained with high probability; true p = {'1': 0.98, '2': 0.92, '3': 0.86, '4': 0.78, '5': 0.68, '6': 0.56, '7': 0.44, '8': 0.3, '9': 0.22, '10': 0.16, '11': 0.11, '12': 0.08}
- **narrow_noisy** (MK2): raw max-min passes often by noise; new method rejects or resamples; true p = {'1': 0.82, '2': 0.79, '3': 0.76, '4': 0.73, '5': 0.7, '6': 0.67, '7': 0.64, '8': 0.62, '9': 0.61, '10': 0.6, '11': 0.6, '12': 0.59}
- **borderline** (MK3): routed to the second pass; true p = {'1': 0.88, '2': 0.85, '3': 0.81, '4': 0.76, '5': 0.7, '6': 0.64, '7': 0.58, '8': 0.54, '9': 0.53, '10': 0.52, '11': 0.52, '12': 0.51}
- **one_sided** (MK4): wide but not spectrum support: no rung above A; true p = {'1': 0.62, '2': 0.55, '3': 0.48, '4': 0.42, '5': 0.35, '6': 0.28, '7': 0.22, '8': 0.16, '9': 0.13, '10': 0.11, '11': 0.09, '12': 0.07}
- **flat** (MK5): rejected early; true p = {'1': 0.7, '2': 0.69, '3': 0.68, '4': 0.67, '5': 0.67, '6': 0.66, '7': 0.65, '8': 0.64, '9': 0.64, '10': 0.63, '11': 0.63, '12': 0.62}
- **outlier** (MK6): not discarded: the rest of the ladder is strong; true p = {'1': 0.96, '2': 0.9, '3': 0.84, '4': 0.4, '5': 0.68, '6': 0.57, '7': 0.46, '8': 0.33, '9': 0.25, '10': 0.18, '11': 0.13, '12': 0.09}
- **ceiling** (MK7): recognised as fragile: extremes sit at the band edges; true p = {'1': 0.93, '2': 0.91, '3': 0.89, '4': 0.8, '5': 0.7, '6': 0.55, '7': 0.35, '8': 0.12, '9': 0.09, '10': 0.07, '11': 0.05, '12': 0.04}
- **too_easy_reserve** (MK8): the reserve extension recovers the hard side; the round-0 ladder alone cannot; true p = {'1': 0.99, '2': 0.98, '3': 0.96, '4': 0.93, '5': 0.9, '6': 0.85, '7': 0.79, '8': 0.72, '9': 0.64, '10': 0.55, '11': 0.46, '12': 0.38}
