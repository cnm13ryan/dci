# Cross-model DCI transport — results

Generated 2026-08-11 23:01 UTC by `xm_results.py` from `analysis/*.csv`, which
`xm_analysis.py` produced from the raw generation rows and
`xm_verify_independently.py` reproduced with separate arithmetic.
This document is a view; it is never an input.

**Status: exploratory.** No claim here is confirmatory, and the
execution condition differs from the canonical Qwen3-4B result in a way
that matters — see the backend note below.

## The estimand

For model *m*, background *c* and reasoning condition *r*:

> τ(m,c,r) = P(F_A = 1 | B, m, c, r) − P(F_A = 1 | R, m, c, r)

> Δ_semicolon(m,r) = τ(m, semicolon, r) − τ(m, control, r)

where A is *"Write exactly 4 sentences."*, B is *"Make each sentence
strictly longer than the preceding sentence when measured by word
count."* and R is the matched reference *"Begin every sentence with a
word whose first letter is S."* F_A = 1 means A failed.

Both raw components are printed beside every difference. A reader shown
only a difference-of-differences cannot tell amplification from two
floors.

## Execution condition, and what it is NOT comparable with

Every checkpoint here ran on **Transformers**, because vLLM is not
installed on this machine and no ROCm build of it is present. The
canonical +0.400 semicolon result was produced by vLLM 0.15.1+rocm720 on
`Qwen/Qwen3-4B` @ `1cfa9a720891`, a
checkpoint that is not in this study. The five-way comparison below is
internally consistent; a comparison against that number would be
backend-confounded and is not made.

## 1. τ(B→A) by model, background and reasoning condition

| model | reasoning | background | focal_A_failure | reference_A_failure | tau | lo | hi | n_tasks | n_rows |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | NO_THINKING | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| Qwen3.5-4B | NO_THINKING | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| Qwen3.5-9B | NO_THINKING | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| Qwen3.5-9B | NO_THINKING | + one semicolon | +0.100 | +0.250 | -0.150 | -0.300 | +0.000 | 20 | 80 |
| gemma-4-12B-it | NO_THINKING | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| gemma-4-12B-it | NO_THINKING | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| gemma-4-E4B-it | NATURAL_REASONING | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| gemma-4-E4B-it | NATURAL_REASONING | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| gemma-4-E4B-it | NO_THINKING | + one bracket pair (control) | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |
| gemma-4-E4B-it | NO_THINKING | + one semicolon | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 | 80 |


> **τ is not estimable in some cells above.** Where the target
> instruction never fails in EITHER arm, τ is zero by construction
> and cannot detect interference — "no extra failures" and "no
> failures to add to" are different findings. The affected cells:

> * `Qwen3.5-4B` / NO_THINKING / + one bracket pair (control) — TARGET_CEILING
> * `Qwen3.5-4B` / NO_THINKING / + one semicolon — TARGET_CEILING
> * `Qwen3.5-9B` / NO_THINKING / + one bracket pair (control) — TARGET_CEILING
> * `gemma-4-12B-it` / NO_THINKING / + one bracket pair (control) — TARGET_CEILING
> * `gemma-4-12B-it` / NO_THINKING / + one semicolon — TARGET_CEILING
> * `gemma-4-E4B-it` / NATURAL_REASONING / + one bracket pair (control) — TARGET_CEILING
> * `gemma-4-E4B-it` / NATURAL_REASONING / + one semicolon — TARGET_CEILING
> * `gemma-4-E4B-it` / NO_THINKING / + one bracket pair (control) — TARGET_CEILING
> * `gemma-4-E4B-it` / NO_THINKING / + one semicolon — TARGET_CEILING


## 2. Semicolon-minus-control contrast

| model | reasoning | tau_control | tau_semicolon | delta_semicolon | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | NO_THINKING | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 |
| Qwen3.5-9B | NO_THINKING | +0.000 | -0.150 | -0.150 | -0.300 | +0.000 | 20 |
| gemma-4-12B-it | NO_THINKING | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 |
| gemma-4-E4B-it | NATURAL_REASONING | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 |
| gemma-4-E4B-it | NO_THINKING | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | 20 |


## 2b. Joint satisfaction — SECONDARY and exploratory

Reported because the primary estimand degenerates on every checkpoint
tested: the target instruction is satisfied almost always, so a
contrast between two target-failure rates has no room to move. This
asks whether the semicolon context costs anything at all, of the
outcome that does move — both instructions satisfied in the focal arm:

> Δ_J(m,r) = P(both | semicolon) − P(both | control), focal arm only

It was **not pre-registered** and was chosen after seeing that τ
degenerated. Paired over tasks and bootstrapped identically.

| model | reasoning | joint_control | joint_semicolon | delta_joint | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | NO_THINKING | +0.175 | +0.200 | +0.025 | -0.150 | +0.200 | 20 |
| Qwen3.5-9B | NO_THINKING | +0.275 | +0.200 | -0.075 | -0.301 | +0.150 | 20 |
| gemma-4-12B-it | NO_THINKING | +1.000 | +0.900 | -0.100 | -0.200 | -0.025 | 20 |
| gemma-4-E4B-it | NATURAL_REASONING | +0.900 | +0.875 | -0.025 | -0.175 | +0.100 | 20 |
| gemma-4-E4B-it | NO_THINKING | +0.200 | +0.175 | -0.025 | -0.175 | +0.125 | 20 |


## 3. Four-state outcomes in the focal arm

Identical target-failure rates can arise through different behavioural
strategies, so the arbitration states are reported separately. Where the
focal instruction B is near floor for a checkpoint, this table mostly
distinguishes *neither* from *target only* and does **not** identify
arbitration between two live constraints — see the execution matrix's
Stage D column before reading it as arbitration.

| index | model | reasoning | background | both satisfied | target only | focal only | neither |
|---|---|---|---|---|---|---|---|
| 0 | Qwen3.5-4B | NO_THINKING | + one bracket pair (control) | 0.175 | 0.825 | 0.000 | 0.000 |
| 1 | Qwen3.5-4B | NO_THINKING | + one semicolon | 0.200 | 0.800 | 0.000 | 0.000 |
| 2 | Qwen3.5-9B | NO_THINKING | + one bracket pair (control) | 0.275 | 0.725 | 0.000 | 0.000 |
| 3 | Qwen3.5-9B | NO_THINKING | + one semicolon | 0.200 | 0.700 | 0.075 | 0.025 |
| 4 | gemma-4-12B-it | NO_THINKING | + one bracket pair (control) | 1.000 | 0.000 | 0.000 | 0.000 |
| 5 | gemma-4-12B-it | NO_THINKING | + one semicolon | 0.900 | 0.100 | 0.000 | 0.000 |
| 6 | gemma-4-E4B-it | NATURAL_REASONING | + one bracket pair (control) | 0.900 | 0.100 | 0.000 | 0.000 |
| 7 | gemma-4-E4B-it | NATURAL_REASONING | + one semicolon | 0.875 | 0.125 | 0.000 | 0.000 |
| 8 | gemma-4-E4B-it | NO_THINKING | + one bracket pair (control) | 0.200 | 0.800 | 0.000 | 0.000 |
| 9 | gemma-4-E4B-it | NO_THINKING | + one semicolon | 0.175 | 0.825 | 0.000 | 0.000 |


## 4. In-context compliance with each instruction

The same question the Stage D gate asks in isolation, asked of the
scientific rows.

| model | reasoning | A_in_focal_arm | A_in_reference_arm | B_compliance | R_compliance | background_compliance |
|---|---|---|---|---|---|---|
| Qwen3.5-4B | NO_THINKING | +1.000 | +1.000 | +0.188 | +0.988 | +0.544 |
| Qwen3.5-9B | NO_THINKING | +0.950 | +0.875 | +0.275 | +1.000 | +0.887 |
| gemma-4-12B-it | NO_THINKING | +1.000 | +1.000 | +0.950 | +1.000 | +1.000 |
| gemma-4-E4B-it | NATURAL_REASONING | +1.000 | +1.000 | +0.887 | +1.000 | +0.994 |
| gemma-4-E4B-it | NO_THINKING | +1.000 | +1.000 | +0.188 | +1.000 | +0.981 |


## 5. Natural reasoning — descriptive, per model only

**Reasoning tokens are not a universal unit of compute.** A Qwen token, a
Gemma token and a Kimi token index different tokenizers, different
training and different reasoning formats. These distributions are
reported per checkpoint and are never summed, averaged or ranked across
families. Realised length is post-treatment and no mediation is claimed.

| model | background | arm | n | median | p25 | p75 | p90 | p95 | max | closure_rate | ceiling_hits | answer_tokens | latency_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma-4-E4B-it | + one bracket pair (control) | focal B | 40 | 314.0 | 295.2 | 347.2 | 379.6 | 453.4 | 792 | 1.0 | 0 | 70.9 | 4.2 |
| gemma-4-E4B-it | + one bracket pair (control) | reference R | 40 | 287.0 | 217.0 | 339.0 | 417.6 | 426.2 | 484 | 0.9 | 0 | 55.7 | 4.0 |
| gemma-4-E4B-it | + one semicolon | focal B | 40 | 318.5 | 283.2 | 339.2 | 389.2 | 409.7 | 842 | 1.0 | 0 | 77.1 | 4.3 |
| gemma-4-E4B-it | + one semicolon | reference R | 40 | 308.0 | 221.8 | 340.8 | 424.7 | 465.8 | 516 | 0.9 | 0 | 59.4 | 4.5 |


## What this does not establish

* Nothing about model families in general — these are single
  checkpoints, one instruction pair, 20 tasks, 2 replicates.
* No parameter-count claim. Qwen3.5-4B and 9B differ in training and
  post-training as well as scale, and E4B and 12B are different
  architectures, not one architecture at two sizes.
* No claim that longer realised reasoning causes anything. It is chosen
  by the model, not assigned.
* No claim that semicolons universally amplify instruction conflict.
* Where a checkpoint's focal instruction sits near floor, no claim that
  it "has less DCI" — the contrast cannot be estimated there.

Models covered: Qwen3.5-4B, Qwen3.5-9B, gemma-4-12B-it, gemma-4-E4B-it.
