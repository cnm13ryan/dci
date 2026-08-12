# Cross-model DCI — the actual dataset

Recorded 2026-08-12 21:49 UTC. Machine-readable twins: `ACTUAL_CROSS_MODEL_DCI_ROWS.jsonl`, `ACTUAL_CROSS_MODEL_DCI_RUN_MANIFEST.json`.

`EXPLORATORY_NO_EVIDENCE`. One frozen design — target A, focal B, reference C_L3, order QAC, 20 pilot tasks, 2 replicates, two backgrounds — run against every checkpoint that could be made to execute it. **Backends differ per checkpoint** and that difference is recorded on every row; see §6 before comparing any two models.

Condition: `THINKING_ENABLED_BOUNDED`. Thinking is on, no budget is assigned, and a fixed ceiling bounds total generation. A request that reaches the ceiling is recorded `NO_FINAL_WITHIN_BUDGET` and kept — never force-closed, never given an invented answer, never counted as an A-failure.

| Model | Backend | k | Requested | Final answers | Final answers focal | Final answers ref | No-final | A-fail focal | A-fail ref | tau |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | transformers | 3 | 160 | 160 | 80 | 80 | 0 | 0.000 | 0.000 | 0.000 |
| Qwen3.5-9B | transformers | 3 | 160 | 160 | 80 | 80 | 0 | 0.050 | 0.125 | -0.075 |
| gemma-4-12B-it | transformers | 3 | 160 | 160 | 80 | 80 | 0 | 0.000 | 0.000 | 0.000 |
| gemma-4-E4B-it | transformers | 3 | 320 | 320 | 160 | 160 | 0 | 0.000 | 0.000 | 0.000 |


τ = P(A fails | focal B) − P(A fails | reference C_L3), over rows that produced a final answer, pooled across backgrounds and weighted by those rows. Per-background detail and the degeneracy label are in §1.

## 1. k=3 results

| model | backend | load | background | requested | final_answers | no_final | technical_failures | A_fail_focal | A_fail_reference | tau | lo | hi | n_tasks | joint_focal | degeneracy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | transformers | 3 | control (+1 bracket pair) | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.175 | TARGET_CEILING |
| Qwen3.5-4B | transformers | 3 | +1 semicolon | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.200 | TARGET_CEILING |
| Qwen3.5-9B | transformers | 3 | control (+1 bracket pair) | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.275 | TARGET_CEILING |
| Qwen3.5-9B | transformers | 3 | +1 semicolon | 80 | 80 | 0 | 0 | 0.100 | 0.250 | -0.150 | -0.300 | 0.000 | 20 | 0.200 | estimable |
| gemma-4-12B-it | transformers | 3 | control (+1 bracket pair) | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 1.000 | TARGET_CEILING |
| gemma-4-12B-it | transformers | 3 | +1 semicolon | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.900 | TARGET_CEILING |
| gemma-4-E4B-it | transformers | 3 | control (+1 bracket pair) | 160 | 160 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.550 | TARGET_CEILING |
| gemma-4-E4B-it | transformers | 3 | +1 semicolon | 160 | 160 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.525 | TARGET_CEILING |


A `TARGET_CEILING` label means the target instruction essentially never fails in either arm, so τ is 0 **by construction** rather than by absence of interference. The number is reported, not withheld; it simply cannot carry the signal the design was built to detect.

### Who is missing from the scored subsample

Every rate above is conditional on the row having produced a final answer. That is only harmless if rows go missing at the same rate on both sides of a contrast.

| model | load | background | arm | requested | answered | answer_rate |
|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | control (+1 bracket pair) | focal B | 40 | 40 | 1.000 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 40 | 1.000 |
| Qwen3.5-4B | 3 | +1 semicolon | focal B | 40 | 40 | 1.000 |
| Qwen3.5-4B | 3 | +1 semicolon | reference C_L3 | 40 | 40 | 1.000 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | focal B | 40 | 40 | 1.000 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 40 | 1.000 |
| Qwen3.5-9B | 3 | +1 semicolon | focal B | 40 | 40 | 1.000 |
| Qwen3.5-9B | 3 | +1 semicolon | reference C_L3 | 40 | 40 | 1.000 |
| gemma-4-12B-it | 3 | control (+1 bracket pair) | focal B | 40 | 40 | 1.000 |
| gemma-4-12B-it | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 40 | 1.000 |
| gemma-4-12B-it | 3 | +1 semicolon | focal B | 40 | 40 | 1.000 |
| gemma-4-12B-it | 3 | +1 semicolon | reference C_L3 | 40 | 40 | 1.000 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | focal B | 80 | 80 | 1.000 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | reference C_L3 | 80 | 80 | 1.000 |
| gemma-4-E4B-it | 3 | +1 semicolon | focal B | 80 | 80 | 1.000 |
| gemma-4-E4B-it | 3 | +1 semicolon | reference C_L3 | 80 | 80 | 1.000 |


* No checkpoint lost a row; every contrast is between complete cells.

Where the spread is marked **differential**, the τ and Δ below compare two differently-selected subsamples and the bootstrap intervals do not account for it. Treat those estimates as descriptive of the rows that finished, not of the design as specified.

### Semicolon-minus-control contrast

| model | load | tau_control | tau_semicolon | delta_semicolon | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 |
| Qwen3.5-9B | 3 | 0.000 | -0.150 | -0.150 | -0.300 | 0.000 | 20 |
| gemma-4-12B-it | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 |
| gemma-4-E4B-it | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 |


### Secondary, exploratory: joint satisfaction in the focal arm

Not pre-registered, and reported because the primary estimand is degenerate wherever the target is at ceiling. J = P(A and B both satisfied | focal arm).

| model | load | joint_control | joint_semicolon | delta_joint | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 0.175 | 0.200 | 0.025 | -0.150 | 0.200 | 20 |
| Qwen3.5-9B | 3 | 0.275 | 0.200 | -0.075 | -0.300 | 0.150 | 20 |
| gemma-4-12B-it | 3 | 1.000 | 0.900 | -0.100 | -0.200 | -0.025 | 20 |
| gemma-4-E4B-it | 3 | 0.550 | 0.525 | -0.025 | -0.150 | 0.087 | 20 |


## 2. Four-state outcomes in the focal arm

| model | k | background | both satisfied | target only | focal only | neither | no final answer |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | +1 semicolon | 0.200 | 0.800 | 0.000 | 0.000 | 0.000 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | 0.175 | 0.825 | 0.000 | 0.000 | 0.000 |
| Qwen3.5-9B | 3 | +1 semicolon | 0.200 | 0.700 | 0.075 | 0.025 | 0.000 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | 0.275 | 0.725 | 0.000 | 0.000 | 0.000 |
| gemma-4-12B-it | 3 | +1 semicolon | 0.900 | 0.100 | 0.000 | 0.000 | 0.000 |
| gemma-4-12B-it | 3 | control (+1 bracket pair) | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| gemma-4-E4B-it | 3 | +1 semicolon | 0.525 | 0.475 | 0.000 | 0.000 | 0.000 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | 0.550 | 0.450 | 0.000 | 0.000 | 0.000 |


### In-context compliance with each instruction

| model | load | A_in_focal_arm | A_in_reference_arm | B_compliance | R_compliance | background_compliance |
|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 1.000 | 1.000 | 0.188 | 0.988 | 0.544 |
| Qwen3.5-9B | 3 | 0.950 | 0.875 | 0.275 | 1.000 | 0.887 |
| gemma-4-12B-it | 3 | 1.000 | 1.000 | 0.950 | 1.000 | 1.000 |
| gemma-4-E4B-it | 3 | 1.000 | 1.000 | 0.537 | 1.000 | 0.988 |


## 3. Reasoning length and termination

Per model only. Token counts index different tokenizers and are never summed, averaged or ranked across families.

| model | load | backend | ceiling | n | median | p90 | max | closed | hit_ceiling | answered | answer_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | transformers | — | 160 | 0.0 | 0.0 | 0 | 0.0 | 0 | 1.0 | 72.8 |
| Qwen3.5-9B | 3 | transformers | — | 160 | 0.0 | 0.0 | 0 | 0.0 | 0 | 1.0 | 77.0 |
| gemma-4-12B-it | 3 | transformers | — | 160 | 0.0 | 0.0 | 0 | 0.0 | 0 | 1.0 | 45.6 |
| gemma-4-E4B-it | 3 | transformers | 39517.0 | 320 | 0.0 | 349.2 | 842 | 0.5 | 0 | 1.0 | 73.4 |


By arm and background — where an answer-rate gap comes from:

| model | load | background | arm | median_reasoning | p90 | max | hit_ceiling | of |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | control (+1 bracket pair) | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-4B | 3 | +1 semicolon | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-4B | 3 | +1 semicolon | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-9B | 3 | +1 semicolon | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| Qwen3.5-9B | 3 | +1 semicolon | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| gemma-4-12B-it | 3 | control (+1 bracket pair) | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| gemma-4-12B-it | 3 | control (+1 bracket pair) | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| gemma-4-12B-it | 3 | +1 semicolon | focal B | 0.0 | 0.0 | 0 | 0 | 40 |
| gemma-4-12B-it | 3 | +1 semicolon | reference C_L3 | 0.0 | 0.0 | 0 | 0 | 40 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | focal B | 78.5 | 349.7 | 792 | 0 | 80 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | reference C_L3 | 0.0 | 351.6 | 484 | 0 | 80 |
| gemma-4-E4B-it | 3 | +1 semicolon | focal B | 80.0 | 344.4 | 842 | 0 | 80 |
| gemma-4-E4B-it | 3 | +1 semicolon | reference C_L3 | 0.0 | 343.1 | 516 | 0 | 80 |


## 4. k=5 results

Not run. See §6.

## 5. Technical failures

None. Every requested row was attempted and returned a generation.

## 6. Backend and execution limitations

* **Qwen3.5-4B** (k=3) — `transformers 5.15.0`, bfloat16, none, cuda:0; thinking via `chat_template(enable_thinking=False)`; generation ceiling NOT RECORDED for this run; revision `851bf6e806ef`
* **Qwen3.5-9B** (k=3) — `transformers 5.15.0`, bfloat16, none, cuda:0; thinking via `chat_template(enable_thinking=False)`; generation ceiling NOT RECORDED for this run; revision `c20223623576`
* **gemma-4-12B-it** (k=3) — `transformers 5.15.0`, bfloat16, none, cuda:0; thinking via `chat_template(enable_thinking=False)`; generation ceiling NOT RECORDED for this run; revision `707f0a3b8a3c`
* **gemma-4-E4B-it** (k=3) — `transformers 5.15.0`, bfloat16, none, cuda:0; thinking via `chat_template(enable_thinking=True)`; ceiling 39,517 tokens/request; revision `ee0ef6023621`

Cross-model differences must be read against this table. Two checkpoints executed on different backends differ in more than their weights: attention kernel, batching, KV layout and sampler implementation all move together with the backend. Nothing here licenses attributing a between-model difference to the models.
