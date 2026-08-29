# Pre-screen simulation (development candidate)

n_sims per archetype = 200; every number is synthetic. Legacy = the v7 per-family C4 certificate on 24-topic point estimates; New = the posterior-predictive screen with the targeted second pass. FP/FN are against the TRUE event on the true parameters.

## Chosen thresholds (prospective)

Rule: minimise FP + FN over archetypes (equal weight, both A curves); tie-break: smaller resample fraction, larger d_below, lower accept

| rank | event | d_below | d_above | accept | reject | final at | FP | FN | resampled |
|---|---|---|---|---|---|---|---|---|---|
| 1 | support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | 0.147 | 0.093 | 0.42 |
| 2 | support_both | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | 0.166 | 0.086 | 0.37 |
| 3 | support_both | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | 0.121 | 0.141 | 0.46 |
| 4 | support_both | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | 0.131 | 0.142 | 0.39 |
| 5 | support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | 0.119 | 0.171 | 0.42 |
| 6 | c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | 0.224 | 0.287 | 0.48 |
| 7 | c4 | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | 0.207 | 0.306 | 0.51 |
| 8 | c4 | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | 0.227 | 0.287 | 0.46 |
| 9 | c4 | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | 0.220 | 0.301 | 0.49 |
| 10 | c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | 0.215 | 0.307 | 0.48 |

## Per archetype, at the chosen configuration

### A curve: qwen3-4b-like (iota_A~0.68)

| archetype | true event | true C4 | legacy pass | legacy FP | legacy FN | new accept | new FP | new FN | resampled | mean batches | P(cal C4 \| legacy pass) | P(cal event \| new accept) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | True | True | 0.90 | 0.00 | 0.10 | 1.00 | 0.00 | 0.00 | 0.04 | 0.04 | 1.00 | 1.00 |
| narrow_noisy | True | False | 0.12 | 0.12 | 0.00 | 0.32 | 0.00 | 0.69 | 0.88 | 2.02 | 0.00 | 0.37 |
| borderline | True | False | 0.28 | 0.28 | 0.00 | 0.99 | 0.00 | 0.01 | 0.65 | 0.91 | 0.07 | 0.96 |
| one_sided | False | False | 0.34 | 0.34 | 0.00 | 0.00 | 0.00 | 0.00 | 0.09 | 0.09 | 0.06 | — |
| flat | False | False | 0.06 | 0.06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.47 | 0.60 | 0.00 | — |
| outlier | True | True | 0.90 | 0.00 | 0.10 | 1.00 | 0.00 | 0.00 | 0.07 | 0.07 | 1.00 | 1.00 |
| ceiling | True | True | 0.89 | 0.00 | 0.11 | 1.00 | 0.00 | 0.00 | 0.04 | 0.04 | 0.99 | 1.00 |
| too_easy_reserve | True | True | 0.01 | 0.00 | 0.99 | 0.97 | 0.00 | 0.03 | 1.00 | 2.43 | 1.00 | 1.00 |

### A curve: qwen-2507-like (iota_A~0.55)

| archetype | true event | true C4 | legacy pass | legacy FP | legacy FN | new accept | new FP | new FN | resampled | mean batches | P(cal C4 \| legacy pass) | P(cal event \| new accept) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | True | True | 0.86 | 0.00 | 0.14 | 1.00 | 0.00 | 0.00 | 0.08 | 0.10 | 1.00 | 0.99 |
| narrow_noisy | False | False | 0.04 | 0.04 | 0.00 | 0.20 | 0.20 | 0.00 | 0.82 | 2.02 | 0.00 | 0.00 |
| borderline | False | False | 0.34 | 0.34 | 0.00 | 0.96 | 0.96 | 0.00 | 0.73 | 1.31 | 0.07 | 0.21 |
| one_sided | False | True | 0.43 | 0.00 | 0.57 | 0.01 | 0.01 | 0.00 | 0.10 | 0.15 | 0.90 | 1.00 |
| flat | False | False | 0.09 | 0.09 | 0.00 | 0.01 | 0.01 | 0.00 | 0.58 | 0.94 | 0.00 | 0.00 |
| outlier | True | True | 0.83 | 0.00 | 0.17 | 1.00 | 0.00 | 0.00 | 0.15 | 0.18 | 1.00 | 0.99 |
| ceiling | True | True | 0.86 | 0.00 | 0.14 | 1.00 | 0.00 | 0.00 | 0.10 | 0.10 | 0.99 | 1.00 |
| too_easy_reserve | True | True | 0.00 | 0.00 | 1.00 | 0.73 | 0.00 | 0.27 | 1.00 | 2.67 | — | 1.00 |

## Whole grid (pooled over archetypes)

| event | d_below | d_above | accept | reject | final at | A curve | legacy FP | legacy FN | new FP | new FN | resampled | mean re-screen gens | survival legacy | survival new |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| support_both | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.34 | 0.01 | 0.11 | 0.34 | 305 | 0.45 | 0.75 |
| support_both | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.33 | 0.07 | 0.40 | 383 | 0.61 | 0.59 |
| support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.33 | 0.00 | 0.12 | 0.40 | 369 | 0.52 | 0.89 |
| support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.40 | 0.29 | 0.07 | 0.44 | 443 | 0.57 | 0.65 |
| support_both | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.00 | 0.15 | 0.36 | 333 | 0.52 | 0.77 |
| support_both | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.17 | 0.42 | 0.26 | 0.14 | 0.42 | 426 | 0.56 | 0.68 |
| support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.33 | 0.00 | 0.18 | 0.40 | 369 | 0.52 | 0.89 |
| support_both | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.40 | 0.24 | 0.17 | 0.44 | 443 | 0.57 | 0.65 |
| support_both | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.35 | 0.00 | 0.16 | 0.42 | 395 | 0.44 | 0.92 |
| support_both | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.39 | 0.24 | 0.12 | 0.49 | 499 | 0.62 | 0.65 |
| c4 | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.33 | 0.20 | 0.22 | 0.46 | 374 | 0.51 | 0.58 |
| c4 | 0.1 | 0.1 | 0.7 | 0.15 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.15 | 0.41 | 0.25 | 0.35 | 0.47 | 425 | 0.61 | 0.71 |
| c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.34 | 0.19 | 0.23 | 0.47 | 381 | 0.51 | 0.61 |
| c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.5 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.26 | 0.35 | 0.50 | 438 | 0.55 | 0.69 |
| c4 | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.19 | 0.23 | 0.48 | 384 | 0.51 | 0.58 |
| c4 | 0.1 | 0.1 | 0.75 | 0.15 | 0.75 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.25 | 0.37 | 0.50 | 449 | 0.61 | 0.70 |
| c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | qwen3-4b-like (iota_A~0.68) | 0.19 | 0.34 | 0.18 | 0.24 | 0.47 | 381 | 0.51 | 0.62 |
| c4 | 0.1 | 0.1 | 0.8 | 0.2 | 0.8 | qwen-2507-like (iota_A~0.55) | 0.16 | 0.41 | 0.25 | 0.38 | 0.50 | 438 | 0.55 | 0.66 |
| c4 | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | qwen3-4b-like (iota_A~0.68) | 0.20 | 0.34 | 0.18 | 0.24 | 0.49 | 405 | 0.51 | 0.59 |
| c4 | 0.1 | 0.1 | 0.85 | 0.2 | 0.7 | qwen-2507-like (iota_A~0.55) | 0.18 | 0.40 | 0.24 | 0.37 | 0.54 | 478 | 0.57 | 0.71 |

## Archetypes

- **wide** (MK1): retained with high probability; true p = {'1': 0.98, '2': 0.92, '3': 0.86, '4': 0.78, '5': 0.68, '6': 0.56, '7': 0.44, '8': 0.3, '9': 0.22, '10': 0.16, '11': 0.11, '12': 0.08}
- **narrow_noisy** (MK2): raw max-min passes often by noise; new method rejects or resamples; true p = {'1': 0.82, '2': 0.79, '3': 0.76, '4': 0.73, '5': 0.7, '6': 0.67, '7': 0.64, '8': 0.62, '9': 0.61, '10': 0.6, '11': 0.6, '12': 0.59}
- **borderline** (MK3): routed to the second pass; true p = {'1': 0.88, '2': 0.85, '3': 0.81, '4': 0.76, '5': 0.7, '6': 0.64, '7': 0.58, '8': 0.54, '9': 0.53, '10': 0.52, '11': 0.52, '12': 0.51}
- **one_sided** (MK4): wide but not spectrum support: no rung above A; true p = {'1': 0.62, '2': 0.55, '3': 0.48, '4': 0.42, '5': 0.35, '6': 0.28, '7': 0.22, '8': 0.16, '9': 0.13, '10': 0.11, '11': 0.09, '12': 0.07}
- **flat** (MK5): rejected early; true p = {'1': 0.7, '2': 0.69, '3': 0.68, '4': 0.67, '5': 0.67, '6': 0.66, '7': 0.65, '8': 0.64, '9': 0.64, '10': 0.63, '11': 0.63, '12': 0.62}
- **outlier** (MK6): not discarded: the rest of the ladder is strong; true p = {'1': 0.96, '2': 0.9, '3': 0.84, '4': 0.4, '5': 0.68, '6': 0.57, '7': 0.46, '8': 0.33, '9': 0.25, '10': 0.18, '11': 0.13, '12': 0.09}
- **ceiling** (MK7): recognised as fragile: extremes sit at the band edges; true p = {'1': 0.93, '2': 0.91, '3': 0.89, '4': 0.8, '5': 0.7, '6': 0.55, '7': 0.35, '8': 0.12, '9': 0.09, '10': 0.07, '11': 0.05, '12': 0.04}
- **too_easy_reserve** (MK8): the reserve extension recovers the hard side; the round-0 ladder alone cannot; true p = {'1': 0.99, '2': 0.98, '3': 0.96, '4': 0.93, '5': 0.9, '6': 0.85, '7': 0.79, '8': 0.72, '9': 0.64, '10': 0.55, '11': 0.46, '12': 0.38}
