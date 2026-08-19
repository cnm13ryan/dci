# Gate 1 development-phase review (amendment A3) — researcher inspection material

Real `gate1-dev` execution, 2026-08-17, producing commit `3d8318d`,
autorater config hash `881d789…` (openai/gpt-oss-20b @ `6cee5e81…`,
prompt gate1-judge/2.0.0, parser gate1-parse/2.0.0, greedy, cap 512,
`skip_special_tokens=false`, `reasoning_effort=low`). Serving
architecture per the workstation benchmark: two independent TP=1
engines, one model phase per GPU at a time, production sorted request
order, chunk 32. **Provisional classifications only — the autorater
never changes verifier semantics. This phase stops before
`gate1-signoff`, `verifier-freeze`, and everything downstream, pending
explicit researcher decisions.**

Complete cases (every disagreement with the full response text, both
labels, justification, split_class, n, source, and the mechanical
cross-checks) are in `reports/gate1_dev_cases.json`.

## Execution summary

| Model | GPU | Wall clock | Judge passes (dev / repeat) | Outcome |
|---|---|---|---|---|
| gemma-3n-e2b-it | 0 | 5 m 06 s | 151 s / 151 s | COMPLETED |
| qwen3-4b | 1 | 5 m 04 s | 153 s / 148 s | COMPLETED |
| qwen3-4b-instruct-2507 | 0 | 5 m 14 s | 156 s / 154 s | COMPLETED |
| gemma-3n-e4b-it | 1 | 6 m 26 s | 191 s / 191 s | COMPLETED |

Whole four-model development phase: **11 m 33 s** wall
(17:27:16 → 17:38:49). No OOMs, crashes, hangs, retries, or generation
failures: every backend run produced all its rows OK on `attempt0`;
throughput (~150–190 s per 246-item TP=1 pass including the ~16 s
engine load) is consistent with the benchmark. Each model phase ran
entirely on one TP=1 GPU (plan `tensor_parallel_size=1`; device routing
via `--device`; per-card GpuLock). No calibration directory, record, or
ledger entry exists for any model — the held-out halves are untouched.

## Stability (registered development-only repeated pass)

All four models: **0 label flips and 0 operational-status changes**
across the full repeated greedy pass (identical configuration and batch
composition; separate engine launch). 983 repeated judgments, 983
identical results. No reproducibility investigation is required.

## Per-model development metrics

### gemma-3n-e2b-it
- development items 246; valid 245; invalid {invalid_output: 1};
  coverage 0.9959
- verifier marginal {pass 150, fail 96}; autorater marginal (valid)
  {pass 134, fail 111}
- contingency: pass/SATISFIES 102, pass/VIOLATES 48,
  fail/SATISFIES 32, fail/VIOLATES 63
- disagreements 80 (rate 0.327 of valid); directional:
  verifier-pass→VIOLATES 48 (0.196), verifier-fail→SATISFIES 32 (0.131)
- identification interval [0.6707, 0.6748] (a = 165)
- disagreements by n: {2:1, 3:8, 4:20, 5:18, 6:16, 7:4, 8:13};
  by source: {prescreen 36, validation 44}
- classifications: over-count-by-one 64, under-count-by-one 13,
  severe miscount 3

### qwen3-4b
- items 246; valid 244; invalid {invalid_output: 2}; coverage 0.9919
- verifier marginal {pass 174, fail 72}; autorater marginal
  {pass 168, fail 76}
- contingency: 159 / 14 / 9 / 62
- disagreements 23 (0.094); directional: pass→VIOLATES 14 (0.057),
  fail→SATISFIES 9 (0.037)
- identification interval [0.8984, 0.9065] (a = 221)
- by n: {2:2, 3:1, 4:5, 5:3, 6:2, 7:3, 8:7};
  by source: {prescreen 9, validation 14}
- classifications: over-count-by-one 15, under-count-by-one 4,
  severe miscount 4

### qwen3-4b-instruct-2507
- items 245; valid 244; invalid {invalid_output: 1}; coverage 0.9959
- verifier marginal {pass 163, fail 82}; autorater marginal
  {pass 196, fail 48}
- contingency: 146 / 16 / 50 / 32
- disagreements 66 (0.270); directional: pass→VIOLATES 16 (0.066),
  fail→SATISFIES 50 (0.205)
- identification interval [0.7265, 0.7306] (a = 178)
- by n: {2:6, 3:1, 4:3, 5:9, 6:15, 7:12, 8:20};
  by source: {prescreen 24, validation 42}
- classifications: over-count-by-one 48, under-count-by-one 12,
  severe miscount 6

### gemma-3n-e4b-it
- items 246; valid 245; invalid {invalid_output: 1}; coverage 0.9959
- verifier marginal {pass 193, fail 53}; autorater marginal
  {pass 165, fail 80}
- contingency: 146 / 47 / 19 / 33
- disagreements 66 (0.269); directional: pass→VIOLATES 47 (0.192),
  fail→SATISFIES 19 (0.078)
- identification interval [0.7276, 0.7317] (a = 179)
- by n: {1:2, 2:4, 3:6, 4:17, 5:10, 6:8, 7:7, 8:12};
  by source: {prescreen 26, validation 40}
- classifications: over-count-by-one 46, under-count-by-one 14,
  severe miscount 4, verdict-contradicts-own-count 1

## Disagreement analysis — no suspected verifier defect

**Mechanical verification, all 235 disagreements:** the frozen S0
verifier, the independent reimplementation
(`verifiers/reimplementation.py`), and a case-insensitive word-boundary
regex agree **exactly** on every disagreement item (235/235). Every
verifier verdict in dispute is mechanically correct under the
registered plain whole-word reading. **Zero cases are flagged as
plausible verifier defects.**

Every disagreement is provisionally classified **autorater error
(miscount)**; none required the semantic-ambiguity category — the
disputed responses contain ordinary standalone uses of
"However/however" (no glued, hyphenated, or quoted-mention forms
surfaced in any disagreement).

The dominant, characterizable judge failure mode is a **systematic
over-count by exactly one** (173/235, 74%): the judge's justification
states a count one higher than the true occurrence count. This single
bias explains both directional patterns — exact-n responses judged
VIOLATES ("appears six times, exceeding the required five" on a
five-occurrence text) and (n−1)-responses judged SATISFIES ("appears
exactly four times" on a three-occurrence text). A plausible mechanism
is the judge including the rule sentence's own "however" in its count.
The remainder: under-count by one 35 (15%), larger miscounts on
high-density texts (s0 ≥ 6, judge saturates or loses count) 17, one
E4B case whose SATISFIES verdict contradicts its own justification.
Disagreements concentrate at n ≥ 4 in every model — long counting
tasks — and split across both source pools roughly in proportion to
pool sizes.

## Invalid outputs (5 of 983 primary judgments)

All five are cap-truncated analyses (`finish_reason=length`) on
pathological fail-class responses that are essentially long runs of
repeated "However," — the judge's analysis entered an enumeration loop
and never reached its final channel. Correctly recorded as
`invalid_output`, never converted to a label. Classification:
operational failure (bounded, understood).

## Confirmations

- No calibration item was accessed; no verifier freeze exists.
- Registered protocol, autorater configuration, and verifier semantics
  are unchanged (worktree clean at `3d8318d` throughout execution).
- Greedy outputs reproduced exactly across independent engine launches
  under the fixed registered composition.

## Pending researcher decisions (nothing below has been run)

1. Whether any verifier change is required (the evidence above supports
   "no": every disputed verdict is mechanically confirmed).
2. Then, in order: `gate1-signoff --phase development --notes …` →
   `verifier-freeze` → `gate1-calibrate` ×4 → `gate1-signoff --phase
   calibration` → `gate1 --model … --approve-autorater-calibration` ×4.
