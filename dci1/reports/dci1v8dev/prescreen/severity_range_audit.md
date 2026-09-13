# Severity-range audit (read-only, exploratory)

Logit-linear extrapolation of each repaired MK ladder to the severity at which it reaches ι_A − 0.15 (hard side) and ι_A + 0.10 (easy side). Ladder = 1..8, reserve = ..12.

## Per model

- **gemma-3n-e2b-it**: not reaching the hard side within the measured rungs: ['MK2', 'MK5']; reserve would reach: ['MK2', 'MK5']; beyond the reserve: ['MK2']; max q needed ≈ 104.9
- **gemma-3n-e4b-it**: not reaching the hard side within the measured rungs: []; reserve would reach: []; beyond the reserve: []; max q needed ≈ 31.2
- **qwen3-4b**: not reaching the hard side within the measured rungs: ['MK6']; reserve would reach: ['MK6']; beyond the reserve: []; max q needed ≈ 8.2
- **qwen3-4b-instruct-2507**: not reaching the hard side within the measured rungs: ['MK1', 'MK2', 'MK5', 'MK6', 'MK7']; reserve would reach: ['MK1', 'MK2', 'MK5', 'MK6', 'MK7']; beyond the reserve: []; max q needed ≈ 9.8

| tree | model | family | ι_A | class | min ι | max ι | measured to q | reaches hard | reaches easy | q for hard | in reserve | q for easy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | MK1 | 0.617 | MONOTONE_USABLE | 0.41 | 0.90 | 8 | True | True | 6.38 | True | 3.29 |
| v7 | gemma-3n-e2b-it | MK2 | 0.617 | MONOTONE_TOO_EASY | 0.48 | 0.90 | 12 | False | True | 14.05 | False | 2.40 |
| v7 | gemma-3n-e2b-it | MK3 | 0.617 | MONOTONE_ALL_BELOW_A | 0.33 | 0.53 | 8 | True | False | 0.74 | False | -15.45 |
| v7 | gemma-3n-e2b-it | MK4 | 0.617 | MONOTONE_USABLE | 0.30 | 0.80 | 12 | True | True | 9.27 | True | 1.50 |
| v7 | gemma-3n-e2b-it | MK5 | 0.617 | MONOTONE_USABLE | 0.28 | 0.98 | 12 | True | True | 9.48 | True | 6.07 |
| v7 | gemma-3n-e2b-it | MK6 | 0.617 | NON_MONOTONIC | 0.15 | 0.86 | 8 | True | True | -1.88 | False | 5.98 |
| v7 | gemma-3n-e2b-it | MK7 | 0.617 | NON_MONOTONIC | 0.05 | 0.26 | 12 | True | False | 104.94 | False | 176.37 |
| v7 | gemma-3n-e2b-it | MK8 | 0.617 | MONOTONE_USABLE | 0.25 | 0.76 | 8 | True | True | 3.83 | True | -1.82 |
| v7 | gemma-3n-e4b-it | MK1 | 0.725 | MONOTONE_USABLE | 0.41 | 0.93 | 12 | True | True | 8.48 | True | 3.97 |
| v7 | gemma-3n-e4b-it | MK2 | 0.725 | MONOTONE_USABLE | 0.46 | 0.97 | 12 | True | True | 9.71 | True | 5.60 |
| v7 | gemma-3n-e4b-it | MK3 | 0.725 | MONOTONE_USABLE | 0.31 | 0.78 | 8 | True | False | 2.48 | True | -2.46 |
| v7 | gemma-3n-e4b-it | MK4 | 0.725 | MONOTONE_USABLE | 0.30 | 0.98 | 12 | True | True | 9.00 | True | 6.13 |
| v7 | gemma-3n-e4b-it | MK5 | 0.725 | MONOTONE_USABLE | 0.41 | 0.99 | 12 | True | True | 8.72 | True | 6.08 |
| v7 | gemma-3n-e4b-it | MK6 | 0.725 | MONOTONE_ALL_BELOW_A | 0.21 | 0.51 | 12 | True | False | 0.50 | False | -8.47 |
| v7 | gemma-3n-e4b-it | MK7 | 0.725 | FLAT | 0.07 | 0.17 | 8 | True | False | 31.20 | False | 46.32 |
| v7 | gemma-3n-e4b-it | MK8 | 0.725 | MONOTONE_USABLE | 0.30 | 0.96 | 8 | True | True | 5.07 | True | 2.50 |
| v7 | qwen3-4b | MK1 | 0.683 | MONOTONE_USABLE | 0.49 | 0.99 | 8 | True | True | 6.77 | True | 4.25 |
| v7 | qwen3-4b | MK2 | 0.683 | MONOTONE_USABLE | 0.45 | 0.98 | 8 | True | True | 6.32 | True | 3.93 |
| v7 | qwen3-4b | MK3 | 0.683 | MONOTONE_USABLE | 0.05 | 0.93 | 8 | True | True | 1.58 | True | -0.34 |
| v7 | qwen3-4b | MK4 | 0.683 | MONOTONE_USABLE | 0.14 | 0.99 | 8 | True | True | 4.12 | True | 2.78 |
| v7 | qwen3-4b | MK5 | 0.683 | MONOTONE_USABLE | 0.12 | 0.84 | 8 | True | True | 3.28 | True | 0.72 |
| v7 | qwen3-4b | MK6 | 0.683 | MONOTONE_TOO_EASY | 0.59 | 0.99 | 8 | False | True | 7.96 | True | 5.40 |
| v7 | qwen3-4b | MK7 | 0.683 | MONOTONE_USABLE | 0.15 | 0.74 | 8 | True | False | 2.93 | True | -0.01 |
| v7 | qwen3-4b | MK8 | 0.683 | MONOTONE_USABLE | 0.18 | 0.80 | 8 | True | True | 2.19 | True | -1.19 |
| v7 | qwen3-4b-instruct-2507 | MK1 | 0.540 | MONOTONE_TOO_EASY | 0.56 | 0.98 | 8 | False | True | 9.74 | True | 7.82 |
| v7 | qwen3-4b-instruct-2507 | MK2 | 0.540 | MONOTONE_TOO_EASY | 0.57 | 0.99 | 8 | False | True | 9.19 | True | 7.63 |
| v7 | qwen3-4b-instruct-2507 | MK3 | 0.540 | MONOTONE_USABLE | 0.04 | 0.95 | 8 | True | True | 4.35 | True | 3.13 |
| v7 | qwen3-4b-instruct-2507 | MK4 | 0.540 | MONOTONE_USABLE | 0.29 | 0.99 | 8 | True | True | 6.45 | True | 5.23 |
| v7 | qwen3-4b-instruct-2507 | MK5 | 0.540 | MONOTONE_TOO_EASY | 0.53 | 0.99 | 8 | False | True | 8.23 | True | 6.68 |
| v7 | qwen3-4b-instruct-2507 | MK6 | 0.540 | MONOTONE_TOO_EASY | 0.48 | 1.00 | 8 | False | True | 7.97 | True | 6.85 |
| v7 | qwen3-4b-instruct-2507 | MK7 | 0.540 | MONOTONE_TOO_EASY | 0.51 | 0.98 | 8 | False | True | 7.99 | True | 6.18 |
| v7 | qwen3-4b-instruct-2507 | MK8 | 0.540 | MONOTONE_USABLE | 0.25 | 0.87 | 8 | True | True | 7.05 | True | 3.70 |
| v6 | gemma-3n-e2b-it | MK1 | 0.629 | MONOTONE_USABLE | 0.38 | 0.90 | 12 | True | True | 8.51 | True | 2.05 |
| v6 | gemma-3n-e2b-it | MK2 | 0.629 | MONOTONE_TOO_EASY | 0.49 | 0.92 | 8 | False | True | 8.25 | True | 2.80 |
| v6 | gemma-3n-e2b-it | MK3 | 0.629 | MONOTONE_ALL_BELOW_A | 0.34 | 0.53 | 8 | True | False | -4.25 | False | -34.15 |
| v6 | gemma-3n-e2b-it | MK4 | 0.629 | MONOTONE_USABLE | 0.32 | 0.78 | 12 | True | True | 9.12 | True | -0.23 |
| v6 | gemma-3n-e2b-it | MK5 | 0.629 | MONOTONE_USABLE | 0.34 | 0.97 | 12 | True | True | 9.68 | True | 6.02 |
| v6 | gemma-3n-e2b-it | MK6 | 0.629 | NON_MONOTONIC | 0.15 | 0.79 | 8 | True | True | 0.01 | False | 7.06 |
| v6 | gemma-3n-e2b-it | MK7 | 0.629 | NON_MONOTONIC | 0.04 | 0.30 | 12 | True | False | 36.77 | False | 59.35 |
| v6 | gemma-3n-e2b-it | MK8 | 0.629 | MONOTONE_USABLE | 0.23 | 0.85 | 8 | True | True | 3.88 | True | -0.18 |
| v6 | gemma-3n-e4b-it | MK1 | 0.709 | MONOTONE_USABLE | 0.39 | 0.94 | 12 | True | True | 8.47 | True | 4.26 |
| v6 | gemma-3n-e4b-it | MK2 | 0.709 | MONOTONE_USABLE | 0.51 | 0.95 | 12 | True | True | 10.22 | True | 6.06 |
| v6 | gemma-3n-e4b-it | MK3 | 0.709 | MONOTONE_USABLE | 0.32 | 0.77 | 8 | True | False | 2.59 | True | -2.37 |
| v6 | gemma-3n-e4b-it | MK4 | 0.709 | MONOTONE_USABLE | 0.33 | 0.99 | 12 | True | True | 9.14 | True | 6.30 |
| v6 | gemma-3n-e4b-it | MK5 | 0.709 | MONOTONE_USABLE | 0.51 | 0.99 | 8 | True | True | 7.32 | True | 5.56 |
| v6 | gemma-3n-e4b-it | MK6 | 0.709 | MONOTONE_ALL_BELOW_A | 0.20 | 0.52 | 12 | True | False | 1.20 | True | -7.14 |
| v6 | gemma-3n-e4b-it | MK7 | 0.709 | NON_MONOTONIC | 0.04 | 0.20 | 8 | True | False | 22.89 | False | 33.06 |
| v6 | gemma-3n-e4b-it | MK8 | 0.709 | MONOTONE_USABLE | 0.34 | 0.96 | 8 | True | True | 5.27 | True | 2.72 |
| v6 | qwen3-4b | MK1 | 0.704 | MONOTONE_USABLE | 0.43 | 0.99 | 8 | True | True | 6.70 | True | 1.75 |
| v6 | qwen3-4b | MK2 | 0.704 | MONOTONE_USABLE | 0.40 | 0.99 | 8 | True | True | 6.10 | True | 3.91 |
| v6 | qwen3-4b | MK3 | 0.704 | MONOTONE_USABLE | 0.03 | 0.94 | 8 | True | True | 1.31 | True | -0.59 |
| v6 | qwen3-4b | MK4 | 0.704 | MONOTONE_USABLE | 0.15 | 0.99 | 8 | True | True | 3.19 | True | 0.97 |
| v6 | qwen3-4b | MK5 | 0.704 | MONOTONE_USABLE | 0.17 | 0.83 | 8 | True | True | 3.00 | True | -0.11 |
| v6 | qwen3-4b | MK6 | 0.704 | MONOTONE_TOO_EASY | 0.61 | 0.98 | 8 | False | True | 8.18 | True | 5.23 |
| v6 | qwen3-4b | MK7 | 0.704 | MONOTONE_USABLE | 0.18 | 0.72 | 8 | True | False | 2.58 | True | -0.96 |
| v6 | qwen3-4b | MK8 | 0.704 | MONOTONE_USABLE | 0.19 | 0.80 | 8 | True | False | 1.80 | True | -2.02 |
| v6 | qwen3-4b-instruct-2507 | MK1 | 0.565 | MONOTONE_TOO_EASY | 0.57 | 0.98 | 8 | False | True | 9.50 | True | 7.59 |
| v6 | qwen3-4b-instruct-2507 | MK2 | 0.565 | MONOTONE_TOO_EASY | 0.60 | 0.99 | 8 | False | True | 9.03 | True | 7.43 |
| v6 | qwen3-4b-instruct-2507 | MK3 | 0.565 | MONOTONE_USABLE | 0.05 | 0.94 | 8 | True | True | 4.27 | True | 3.00 |
| v6 | qwen3-4b-instruct-2507 | MK4 | 0.565 | MONOTONE_USABLE | 0.27 | 0.99 | 8 | True | True | 6.25 | True | 4.97 |
| v6 | qwen3-4b-instruct-2507 | MK5 | 0.565 | MONOTONE_TOO_EASY | 0.51 | 0.99 | 8 | False | True | 7.85 | True | 6.33 |
| v6 | qwen3-4b-instruct-2507 | MK6 | 0.565 | MONOTONE_TOO_EASY | 0.44 | 1.00 | 8 | False | True | 7.77 | True | 6.65 |
| v6 | qwen3-4b-instruct-2507 | MK7 | 0.565 | MONOTONE_TOO_EASY | 0.50 | 0.98 | 8 | False | True | 7.82 | True | 5.94 |
| v6 | qwen3-4b-instruct-2507 | MK8 | 0.565 | MONOTONE_USABLE | 0.25 | 0.83 | 8 | True | True | 6.66 | True | 3.14 |
| dev | qwen3-4b | MK1 | 0.688 | MONOTONE_USABLE | 0.46 | 0.98 | 8 | True | True | 6.73 | True | 4.09 |
| dev | qwen3-4b | MK2 | 0.688 | MONOTONE_USABLE | 0.45 | 0.98 | 8 | True | True | 6.33 | True | 3.85 |
| dev | qwen3-4b | MK3 | 0.688 | MONOTONE_USABLE | 0.05 | 0.94 | 8 | True | True | 1.63 | True | -0.22 |
| dev | qwen3-4b | MK4 | 0.688 | MONOTONE_USABLE | 0.14 | 0.99 | 8 | True | True | 4.11 | True | 2.71 |
| dev | qwen3-4b | MK5 | 0.688 | MONOTONE_USABLE | 0.12 | 0.84 | 8 | True | True | 3.23 | True | 0.56 |
| dev | qwen3-4b | MK6 | 0.688 | MONOTONE_TOO_EASY | 0.59 | 0.99 | 8 | False | True | 7.85 | True | 5.38 |
| dev | qwen3-4b | MK7 | 0.688 | MONOTONE_USABLE | 0.15 | 0.74 | 8 | True | False | 2.87 | True | -0.08 |
| dev | qwen3-4b | MK8 | 0.688 | MONOTONE_USABLE | 0.17 | 0.81 | 8 | True | True | 2.13 | True | -1.14 |
| r3 | qwen3-4b | MK1 | 0.685 | MONOTONE_USABLE | 0.47 | 0.99 | 8 | True | True | 6.74 | True | 4.32 |
| r3 | qwen3-4b | MK2 | 0.685 | MONOTONE_USABLE | 0.46 | 0.98 | 8 | True | True | 6.39 | True | 3.96 |
| r3 | qwen3-4b | MK3 | 0.685 | MONOTONE_USABLE | 0.05 | 0.94 | 8 | True | True | 1.70 | True | -0.10 |
| r3 | qwen3-4b | MK4 | 0.685 | MONOTONE_USABLE | 0.14 | 0.99 | 8 | True | True | 3.24 | True | 1.19 |
| r3 | qwen3-4b | MK5 | 0.685 | MONOTONE_USABLE | 0.13 | 0.84 | 8 | True | True | 3.24 | True | 0.56 |
| r3 | qwen3-4b | MK6 | 0.685 | MONOTONE_TOO_EASY | 0.59 | 0.98 | 8 | False | True | 7.96 | True | 5.27 |
| r3 | qwen3-4b | MK7 | 0.685 | MONOTONE_USABLE | 0.16 | 0.74 | 8 | True | False | 2.83 | True | -0.22 |
| r3 | qwen3-4b | MK8 | 0.685 | MONOTONE_USABLE | 0.17 | 0.81 | 8 | True | True | 2.28 | True | -1.01 |
| r3 | gemma-3n-e2b-it | MK1 | 0.609 | MONOTONE_USABLE | 0.40 | 0.87 | 8 | True | True | 6.62 | True | 3.19 |
| r3 | gemma-3n-e2b-it | MK2 | 0.609 | MONOTONE_USABLE | 0.45 | 0.92 | 8 | True | True | 8.47 | True | 3.50 |
| r3 | gemma-3n-e2b-it | MK3 | 0.609 | MONOTONE_ALL_BELOW_A | 0.31 | 0.54 | 8 | True | False | 2.22 | True | -9.95 |
| r3 | gemma-3n-e2b-it | MK4 | 0.609 | NON_MONOTONIC | 0.41 | 0.78 | 8 | True | True | 49.21 | False | -21.48 |
| r3 | gemma-3n-e2b-it | MK5 | 0.609 | MONOTONE_TOO_EASY | 0.56 | 0.98 | 8 | False | True | 9.65 | True | 6.22 |
| r3 | gemma-3n-e2b-it | MK6 | 0.609 | NON_MONOTONIC | 0.12 | 0.85 | 8 | True | True | -0.78 | False | 6.25 |
| r3 | gemma-3n-e2b-it | MK7 | 0.609 | NON_MONOTONIC | 0.03 | 0.31 | 8 | True | False | 21.08 | False | 33.40 |
| r3 | gemma-3n-e2b-it | MK8 | 0.609 | MONOTONE_USABLE | 0.28 | 0.82 | 8 | True | True | 4.24 | True | -0.92 |
| r4 | qwen3-4b-instruct-2507 | MK1 | 0.540 | MONOTONE_TOO_EASY | 0.56 | 0.99 | 8 | False | True | 9.75 | True | 7.86 |
| r4 | qwen3-4b-instruct-2507 | MK2 | 0.540 | MONOTONE_TOO_EASY | 0.58 | 0.99 | 8 | False | True | 9.43 | True | 7.73 |
| r4 | qwen3-4b-instruct-2507 | MK3 | 0.540 | MONOTONE_USABLE | 0.04 | 0.94 | 8 | True | True | 4.30 | True | 3.11 |
| r4 | qwen3-4b-instruct-2507 | MK4 | 0.540 | MONOTONE_USABLE | 0.29 | 0.99 | 8 | True | True | 6.44 | True | 5.18 |
| r4 | qwen3-4b-instruct-2507 | MK5 | 0.540 | MONOTONE_TOO_EASY | 0.53 | 0.99 | 8 | False | True | 8.18 | True | 6.63 |
| r4 | qwen3-4b-instruct-2507 | MK6 | 0.540 | MONOTONE_TOO_EASY | 0.45 | 1.00 | 8 | False | True | 7.88 | True | 6.79 |
| r4 | qwen3-4b-instruct-2507 | MK7 | 0.540 | MONOTONE_TOO_EASY | 0.51 | 0.98 | 8 | False | True | 7.98 | True | 6.14 |
| r4 | qwen3-4b-instruct-2507 | MK8 | 0.540 | MONOTONE_USABLE | 0.26 | 0.85 | 8 | True | True | 7.01 | True | 3.58 |
