# Gate 1 development review, round 2 (amendment A3.1) — researcher inspection material

Second real `gate1-dev` round, 2026-08-17, producing commit `214f93b`,
under **autorater-config/3** (hash `1b1b4df…`): openai/gpt-oss-20b @
`6cee5e81…`, prompt gate1-judge/2.0.0 and parser gate1-parse/2.0.0
**unchanged**, greedy, `skip_special_tokens=false`,
**reasoning_effort=medium** (now a hashed config key, validated
single-valued against the judge registry) and **cap 1024**. Round 1
(config/2, hash `881d789…`) is parked intact under each model's
`gate1/autorater/superseded/881d78927247/` with ledger entries — the
audited `--supersede-stale-judgments` pathway; nothing was deleted.
Same two-GPU TP=1 execution plan; pool/split hashes unchanged.
**No sign-off, no freeze, no calibration, no approval has been run.**

Complete residual cases (full responses, both labels, justifications,
`split_class`, `n`, source, mechanical cross-checks, classifications)
are in `reports/gate1_dev_cases_r2.json`.

## Why the protocol changed (verified cause, not the verifier)

Independent re-inspection of the round-1 evidence confirmed every
reported failure mode by hand recount: the +1 over-counts (exactly n
occurrences, judge claims n+1), −1 under-counts, saturation miscounts
on dense texts (judge claims exactly n when the true count is 9–12),
one verdict/justification contradiction, and the cap-truncated
enumeration loops. An operational A/B on synthetic discourse-style
items (scratchpad only) reproduced the field signature and tested
causes:

| Configuration (same 24 items) | Correct | Exact-n correct | Truncated |
|---|---|---|---|
| config/2: low effort, cap 512 (round 1) | 15/24 | 4/8 | 3 |
| + rule-line-exclusion prompt (marker variant) | 16/24 | — | 4 |
| + rule-line-exclusion prompt (minimal variant) | 15/24 | 3/8 | 5 |
| medium effort, cap 512 | 19/24 | 7/8 | 5 |
| **medium effort, cap 1024 (config/3)** | **23/24** | **8/8** | **1** |

The rule-line-inclusion hypothesis was **rejected**: instructing the
judge to exclude the rule line did not remove the bias and degraded the
instrument (more invalid outputs; case-pedantry). The cause is the
**reasoning budget** — at low effort the judge approximates counts; at
medium it counts correctly but needs the larger cap. The prompt text
therefore stays at gate1-judge/2.0.0.

## Execution summary (round 2)

| Model | GPU | Wall clock | Outcome |
|---|---|---|---|
| gemma-3n-e2b-it | 0 | 15 m 28 s | COMPLETED |
| qwen3-4b | 1 | 13 m 36 s | COMPLETED |
| qwen3-4b-instruct-2507 | 0 | 13 m 59 s | COMPLETED |
| gemma-3n-e4b-it | 1 | 16 m 02 s | COMPLETED |

Four-model phase: **29 m 41 s** wall (medium-effort transcripts are
~3× round 1, as predicted). No OOMs, crashes, hangs, retries, or
generation failures; every phase ran on one TP=1 GPU (plan-verified);
calibration untouched (no directory, record, or ledger entry; no
freeze).

## Stability

All four models: **0 label flips, 0 status changes** across the full
repeated greedy pass under config/3 (983 repeated judgments). Same
result as round 1: the instrument is deterministic under the fixed
configuration and composition.

## Round-1 → round-2 comparison

| Model | Disagreements | Rate | Invalid | Agreement interval |
|---|---|---|---|---|
| gemma-3n-e2b-it | 80 → **19** | 0.327 → **0.081** | 1 → 11 | [0.671,0.675] → [0.878,0.923] |
| qwen3-4b | 23 → **8** | 0.094 → **0.033** | 2 → 1 | [0.898,0.907] → [0.963,0.968] |
| qwen3-4b-instruct-2507 | 66 → **30** | 0.270 → **0.124** | 1 → 4 | [0.727,0.731] → [0.861,0.878] |
| gemma-3n-e4b-it | 66 → **12** | 0.269 → **0.050** | 1 → 7 | [0.728,0.732] → [0.923,0.951] |
| **Total** | **235 → 69 (−71%)** | | 5 → 23 | |

The invalid-output increase (all 23 are `finish_reason=length`) is the
predicted trade-off: medium-effort analyses on dense/degenerate
"however"-heavy responses exhaust even the 1024 cap. They stay distinct
operational statuses, never labels, and are visible in the coverage and
identification-interval accounting.

## Round-2 per-model metrics

### gemma-3n-e2b-it
items 246, valid 235, coverage 0.9553, invalid {invalid_output: 11};
marginals V{pass 150, fail 96} / A{pass 152, fail 83};
2×2: 141 / 8 / 11 / 75; disagreements 19 (0.081), directional
pass→VIOLATES 8, fail→SATISFIES 11; interval [0.8780, 0.9228] (a=216);
by n {2:1, 3:5, 5:4, 6:2, 7:1, 8:6}; by source {prescreen 12,
validation 7}.

### qwen3-4b
items 246, valid 245, coverage 0.9959, invalid {invalid_output: 1};
marginals V{174, 72} / A{168, 77}; 2×2: 167 / 7 / 1 / 70;
disagreements 8 (0.033), directional 7 / 1; interval
[0.9634, 0.9675] (a=237); by n {2:1, 3:3, 4:2, 5:1, 7:1}; by source
{prescreen 3, validation 5}.

### qwen3-4b-instruct-2507
items 245, valid 241, coverage 0.9837, invalid {invalid_output: 4};
marginals V{163, 82} / A{176, 65}; 2×2: 154 / 8 / 22 / 57;
disagreements 30 (0.124), directional 8 / 22; interval
[0.8612, 0.8776] (a=211); by n {3:2, 4:2, 5:8, 6:6, 7:6, 8:6};
by source {prescreen 11, validation 19}.

### gemma-3n-e4b-it
items 246, valid 239, coverage 0.9715, invalid {invalid_output: 7};
marginals V{193, 53} / A{189, 50}; 2×2: 183 / 6 / 6 / 44;
disagreements 12 (0.050), directional 6 / 6; interval
[0.9228, 0.9512] (a=227); by n {1:1, 2:1, 3:1, 4:1, 5:2, 6:1, 7:2,
8:3}; by source {prescreen 3, validation 9}.

## Residual disagreements — still no suspected verifier defect

On all **69** residual disagreements the frozen S0 verifier, the
independent reimplementation, and a word-boundary regex agree exactly
(69/69). Every case classifies as an autorater ±1 miscount
(over-count-by-one 41, under-count-by-one 27, one unparsed-count
miscount); the round-1 severe-miscount and contradiction modes are
gone. Residual disagreements concentrate at n ≥ 5 dense texts —
consistent with counting difficulty, not with any verifier semantics
issue. **Zero cases are flagged for verifier change.**

## Pending researcher decisions (nothing below has been run)

1. Accept the round-2 development evidence and confirm no verifier
   change is required.
2. Then: `gate1-signoff --phase development --notes …` →
   `verifier-freeze` → `gate1-calibrate` ×4 (one-shot) →
   `gate1-signoff --phase calibration` →
   `gate1 --model … --approve-autorater-calibration` ×4.
