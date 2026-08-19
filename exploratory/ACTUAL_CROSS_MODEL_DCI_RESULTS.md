# Cross-model DCI — the actual dataset

Recorded 2026-08-13 12:22 UTC. Machine-readable twins: `ACTUAL_CROSS_MODEL_DCI_ROWS.jsonl`, `ACTUAL_CROSS_MODEL_DCI_RUN_MANIFEST.json`.

`EXPLORATORY_NO_EVIDENCE`. One frozen design — target A, focal B, reference C_L3, order QAC, 20 pilot tasks, 2 replicates, two backgrounds — run against every checkpoint that could be made to execute it. **Backends differ per checkpoint** and that difference is recorded on every row; see §6 before comparing any two models.

Condition: `THINKING_ENABLED_BOUNDED`. Thinking is on, no budget is assigned, and a fixed ceiling bounds total generation. A request that reaches the ceiling is recorded `NO_FINAL_WITHIN_BUDGET` and kept — never force-closed, never given an invented answer, never counted as an A-failure.

| Model | Backend | k | Requested | Final answers | Final answers focal | Final answers ref | No-final | A-fail focal | A-fail ref | Cells | Identified | tau (identified only) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kimi-VL-A3B-Thinking-2506 | transformers | 3 | 160 | 138 | 71 | 67 | 22 | 0.296 | 0.149 | 2 | 0 | — |
| Qwen3.5-4B | vllm | 3 | 160 | 95 | 55 | 40 | 65 | 0.018 | 0.000 | 2 | 0 | — |
| Qwen3.5-9B | vllm | 3 | 160 | 124 | 67 | 57 | 36 | 0.015 | 0.000 | 2 | 0 | — |
| gemma-4-E4B-it | transformers | 3 | 160 | 160 | 80 | 80 | 0 | 0.000 | 0.000 | 2 | 0 | — |


τ = P(A fails | focal B) − P(A fails | reference C_L3), over rows that produced a final answer, pooled across backgrounds and weighted by those rows. Per-background detail and the identification verdict are in §1. The pooled τ column covers IDENTIFIED cells only; the count of cells and of identified cells is printed beside it.

## 1. k=3 results

| model | backend | load | background | requested | final_answers | no_final | technical_failures | A_fail_focal | A_fail_reference | focal_uptake | reference_uptake | cap_hit_rate | tau | lo | hi | n_tasks | joint_focal | identification | behavioural |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | vllm | 3 | control (+1 bracket pair) | 80 | 42 | 38 | 0 | 0.000 | 0.000 | 1.000 | 1.000 | 0.475 | 0.000 | 0.000 | 0.000 | 9 | 1.000 | EVIDENCE_INCOMPLETE | TARGET_CEILING |
| Qwen3.5-4B | vllm | 3 | +1 semicolon | 80 | 53 | 27 | 0 | 0.033 | 0.000 | 0.967 | 1.000 | 0.338 | 0.031 | 0.000 | 0.094 | 16 | 0.933 | EVIDENCE_INCOMPLETE | IDENTIFIED |
| Qwen3.5-9B | vllm | 3 | control (+1 bracket pair) | 80 | 56 | 24 | 0 | 0.000 | 0.000 | 1.000 | 1.000 | 0.300 | 0.000 | 0.000 | 0.000 | 16 | 1.000 | EVIDENCE_INCOMPLETE | TARGET_CEILING |
| Qwen3.5-9B | vllm | 3 | +1 semicolon | 80 | 68 | 12 | 0 | 0.028 | 0.000 | 0.972 | 1.000 | 0.150 | 0.026 | 0.000 | 0.079 | 19 | 0.972 | EVIDENCE_INCOMPLETE | IDENTIFIED |
| gemma-4-E4B-it | transformers | 3 | control (+1 bracket pair) | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.900 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.900 | EVIDENCE_INCOMPLETE | TARGET_CEILING |
| gemma-4-E4B-it | transformers | 3 | +1 semicolon | 80 | 80 | 0 | 0 | 0.000 | 0.000 | 0.875 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 | 0.875 | EVIDENCE_INCOMPLETE | TARGET_CEILING |
| Kimi-VL-A3B-Thinking-2506 | transformers | 3 | control (+1 bracket pair) | 80 | 69 | 11 | 0 | 0.054 | 0.000 | 0.405 | 0.531 | 0.138 | 0.050 | 0.000 | 0.125 | 20 | 0.351 | EVIDENCE_INCOMPLETE | FOCAL_NONUPTAKE |
| Kimi-VL-A3B-Thinking-2506 | transformers | 3 | +1 semicolon | 80 | 69 | 11 | 0 | 0.559 | 0.286 | 0.088 | 0.571 | 0.138 | 0.278 | 0.056 | 0.500 | 18 | 0.029 | EVIDENCE_INCOMPLETE | FOCAL_NONUPTAKE |


**Two verdict columns, because two different questions are being asked.** `identification` answers *may this contrast be read causally?* — and it alone governs whether a cell enters the pooled τ. `behavioural` answers *what was observed?* — the verdict the same classifier returns once any missing prerequisite feed is supplied, holding every measured constituent fixed. Where nothing was missing the two coincide.

The distinction matters because the classifier returns the FIRST verdict that applies. A cell blocked on evidence it was never given reports `EVIDENCE_INCOMPLETE` and would otherwise say nothing at all about the model — the ceiling, the floor and the undelivered focal instruction would all disappear behind the block. Failing closed is right for pooling and wrong for reading, so both are printed.

A `TARGET_CEILING` reading means the target instruction essentially never fails in either arm, so τ is 0 **by construction** rather than by absence of interference. `FOCAL_NONUPTAKE` means the focal instruction was not followed often enough to count as delivered, so τ estimates the effect of *presenting* it. `EVIDENCE_INCOMPLETE` is not a statement about the model at all: it means a prerequisite — execution admission, verifier certification, satisfiability, channel validity — was never recorded for this cell. Every number is reported, not withheld; none of them may be pooled.

### Who is missing from the scored subsample

Every rate above is conditional on the row having produced a final answer. That is only harmless if rows go missing at the same rate on both sides of a contrast.

| model | load | background | arm | requested | answered | answer_rate |
|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | control (+1 bracket pair) | focal B | 40 | 25 | 0.625 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 17 | 0.425 |
| Qwen3.5-4B | 3 | +1 semicolon | focal B | 40 | 30 | 0.750 |
| Qwen3.5-4B | 3 | +1 semicolon | reference C_L3 | 40 | 23 | 0.575 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | focal B | 40 | 31 | 0.775 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 25 | 0.625 |
| Qwen3.5-9B | 3 | +1 semicolon | focal B | 40 | 36 | 0.900 |
| Qwen3.5-9B | 3 | +1 semicolon | reference C_L3 | 40 | 32 | 0.800 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | focal B | 40 | 40 | 1.000 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 40 | 1.000 |
| gemma-4-E4B-it | 3 | +1 semicolon | focal B | 40 | 40 | 1.000 |
| gemma-4-E4B-it | 3 | +1 semicolon | reference C_L3 | 40 | 40 | 1.000 |
| Kimi-VL-A3B-Thinking-2506 | 3 | control (+1 bracket pair) | focal B | 40 | 37 | 0.925 |
| Kimi-VL-A3B-Thinking-2506 | 3 | control (+1 bracket pair) | reference C_L3 | 40 | 32 | 0.800 |
| Kimi-VL-A3B-Thinking-2506 | 3 | +1 semicolon | focal B | 40 | 34 | 0.850 |
| Kimi-VL-A3B-Thinking-2506 | 3 | +1 semicolon | reference C_L3 | 40 | 35 | 0.875 |


* **Kimi-VL-A3B-Thinking-2506** (k=3) — answer rate ranges 80% (control (+1 bracket pair), reference C_L3) to 92% (control (+1 bracket pair), focal B); spread 12%, **differential**.
* **Qwen3.5-4B** (k=3) — answer rate ranges 42% (control (+1 bracket pair), reference C_L3) to 75% (+1 semicolon, focal B); spread 32%, **differential**.
* **Qwen3.5-9B** (k=3) — answer rate ranges 62% (control (+1 bracket pair), reference C_L3) to 90% (+1 semicolon, focal B); spread 28%, **differential**.

Where the spread is marked **differential**, the τ and Δ below compare two differently-selected subsamples and the bootstrap intervals do not account for it. Treat those estimates as descriptive of the rows that finished, not of the design as specified.

### Semicolon-minus-control contrast

| model | load | tau_control | tau_semicolon | delta_semicolon | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 0.000 | 0.031 | 0.062 | 0.000 | 0.188 | 8 |
| Qwen3.5-9B | 3 | 0.000 | 0.026 | 0.033 | 0.000 | 0.100 | 15 |
| gemma-4-E4B-it | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 20 |
| Kimi-VL-A3B-Thinking-2506 | 3 | 0.050 | 0.278 | 0.222 | 0.000 | 0.472 | 18 |


### Secondary, exploratory: joint satisfaction in the focal arm

Not pre-registered, and reported because the primary estimand is degenerate wherever the target is at ceiling. J = P(A and B both satisfied | focal arm).

| model | load | joint_control | joint_semicolon | delta_joint | lo | hi | n_tasks |
|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 1.000 | 0.921 | -0.033 | -0.100 | 0.000 | 15 |
| Qwen3.5-9B | 3 | 1.000 | 0.974 | -0.028 | -0.083 | 0.000 | 18 |
| gemma-4-E4B-it | 3 | 0.900 | 0.875 | -0.025 | -0.175 | 0.125 | 20 |
| Kimi-VL-A3B-Thinking-2506 | 3 | 0.350 | 0.028 | -0.361 | -0.528 | -0.194 | 18 |


## 2. Four-state outcomes in the focal arm

| model | k | background | both satisfied | target only | focal only | neither | no final answer |
|---|---|---|---|---|---|---|---|
| Kimi-VL-A3B-Thinking-2506 | 3 | +1 semicolon | 0.025 | 0.350 | 0.050 | 0.425 | 0.150 |
| Kimi-VL-A3B-Thinking-2506 | 3 | control (+1 bracket pair) | 0.325 | 0.550 | 0.050 | 0.000 | 0.075 |
| Qwen3.5-4B | 3 | +1 semicolon | 0.700 | 0.025 | 0.025 | 0.000 | 0.250 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | 0.625 | 0.000 | 0.000 | 0.000 | 0.375 |
| Qwen3.5-9B | 3 | +1 semicolon | 0.875 | 0.000 | 0.000 | 0.025 | 0.100 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | 0.775 | 0.000 | 0.000 | 0.000 | 0.225 |
| gemma-4-E4B-it | 3 | +1 semicolon | 0.875 | 0.125 | 0.000 | 0.000 | 0.000 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | 0.900 | 0.100 | 0.000 | 0.000 | 0.000 |


### In-context compliance with each instruction

| model | load | A_in_focal_arm | A_in_reference_arm | B_compliance | R_compliance | background_compliance |
|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | 0.982 | 1.000 | 0.982 | 1.000 | 0.979 |
| Qwen3.5-9B | 3 | 0.985 | 1.000 | 0.985 | 1.000 | 0.992 |
| gemma-4-E4B-it | 3 | 1.000 | 1.000 | 0.887 | 1.000 | 0.994 |
| Kimi-VL-A3B-Thinking-2506 | 3 | 0.704 | 0.851 | 0.254 | 0.552 | 0.384 |


## 3. Reasoning length and termination

Per model only. Token counts index different tokenizers and are never summed, averaged or ranked across families.

| model | load | backend | ceiling | n | median | p90 | max | closed | hit_ceiling | answered | answer_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | vllm | 8192.0 | 160 | 7307.5 | 8192.0 | 8193 | 0.6 | 65 | 0.6 | 35.2 |
| Qwen3.5-9B | 3 | vllm | 8192.0 | 160 | 6418.0 | 8192.0 | 8192 | 0.8 | 36 | 0.8 | 53.2 |
| gemma-4-E4B-it | 3 | transformers | 8192.0 | 160 | 309.5 | 400.7 | 842 | 1.0 | 0 | 1.0 | 65.8 |
| Kimi-VL-A3B-Thinking-2506 | 3 | transformers | 8192.0 | 160 | 678.5 | 8187.0 | 8187 | 0.9 | 22 | 0.9 | 80.4 |


By arm and background — where an answer-rate gap comes from:

| model | load | background | arm | median_reasoning | p90 | max | hit_ceiling | of |
|---|---|---|---|---|---|---|---|---|
| Qwen3.5-4B | 3 | control (+1 bracket pair) | focal B | 7596.0 | 8192.0 | 8192 | 15 | 40 |
| Qwen3.5-4B | 3 | control (+1 bracket pair) | reference C_L3 | 8192.0 | 8192.0 | 8192 | 23 | 40 |
| Qwen3.5-4B | 3 | +1 semicolon | focal B | 6547.0 | 8192.0 | 8192 | 10 | 40 |
| Qwen3.5-4B | 3 | +1 semicolon | reference C_L3 | 6899.0 | 8192.0 | 8193 | 17 | 40 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | focal B | 6798.5 | 8192.0 | 8192 | 9 | 40 |
| Qwen3.5-9B | 3 | control (+1 bracket pair) | reference C_L3 | 4573.0 | 8192.0 | 8192 | 15 | 40 |
| Qwen3.5-9B | 3 | +1 semicolon | focal B | 6700.0 | 8152.4 | 8192 | 4 | 40 |
| Qwen3.5-9B | 3 | +1 semicolon | reference C_L3 | 4908.5 | 8192.0 | 8192 | 8 | 40 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | focal B | 314.0 | 379.6 | 792 | 0 | 40 |
| gemma-4-E4B-it | 3 | control (+1 bracket pair) | reference C_L3 | 287.0 | 417.6 | 484 | 0 | 40 |
| gemma-4-E4B-it | 3 | +1 semicolon | focal B | 318.5 | 389.2 | 842 | 0 | 40 |
| gemma-4-E4B-it | 3 | +1 semicolon | reference C_L3 | 308.0 | 424.7 | 516 | 0 | 40 |
| Kimi-VL-A3B-Thinking-2506 | 3 | control (+1 bracket pair) | focal B | 701.0 | 1869.0 | 8187 | 3 | 40 |
| Kimi-VL-A3B-Thinking-2506 | 3 | control (+1 bracket pair) | reference C_L3 | 513.5 | 8187.0 | 8187 | 8 | 40 |
| Kimi-VL-A3B-Thinking-2506 | 3 | +1 semicolon | focal B | 883.5 | 8187.0 | 8187 | 6 | 40 |
| Kimi-VL-A3B-Thinking-2506 | 3 | +1 semicolon | reference C_L3 | 412.0 | 8187.0 | 8187 | 5 | 40 |


## 4. k=5 results

Not run. See §6.

## 5. Technical failures

None. Every requested row was attempted and returned a generation.

## 6. Backend and execution limitations

* **Qwen3.5-4B** (k=3) — `vllm 0.27.1`, bfloat16, none, tensor_parallel_size=2 (cuda:0+cuda:1); thinking via `chat_template({'enable_thinking': True}) · parser=vllm:qwen3`; ceiling 8,192 tokens/request; revision `851bf6e806ef`
* **Qwen3.5-9B** (k=3) — `vllm 0.27.1`, bfloat16, none, tensor_parallel_size=2 (cuda:0+cuda:1); thinking via `chat_template({'enable_thinking': True}) · parser=vllm:qwen3`; ceiling 8,192 tokens/request; revision `c20223623576`
* **gemma-4-E4B-it** (k=3) — `transformers 5.15.0`, bfloat16, none, cuda:0; thinking via `chat_template(enable_thinking=True)`; ceiling 8,192 tokens/request; revision `ee0ef6023621`
* **Kimi-VL-A3B-Thinking-2506** (k=3) — `transformers 4.50.3`, bfloat16, none, device_map=auto max_memory=19GiB/gpu (cuda:0+cuda:1); thinking via `chat_template({}) · parser=delimiters(◁think▷ … ◁/think▷)`; ceiling 8,192 tokens/request; revision `aa1730989e75`

Cross-model differences must be read against this table. Two checkpoints executed on different backends differ in more than their weights: attention kernel, batching, KV layout and sampler implementation all move together with the backend. Nothing here licenses attributing a between-model difference to the models.
