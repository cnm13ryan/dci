# Gate 1 held-out calibration review — researcher inspection material

One-shot held-out calibration, 2026-08-17, under the signed verifier
freeze (record `334bb2b…`, producing commit `66232a7`) and the frozen
**autorater-config/4** (hash `dc8e5b8…`: openai/gpt-oss-20b @
`6cee5e81…`, prompt gate1-judge/2.0.0, parser gate1-parse/2.0.0,
greedy, `skip_special_tokens=false`, reasoning_effort=high, cap 2048,
TP=1, sorted order, chunk 32). Every run verified non-exposure
(ledger-first), the freeze binding (realised pool/split/dev hashes),
and configuration identity before judging; each model's phase ran
entirely on one GPU. Ledger state: `committed` ×4, single `attempt0`
everywhere, verifier sources still byte-identical to the freeze.
**Descriptive evidence only — no acceptance threshold exists, and
nothing here is human validation, ground truth, or human-semantic
accuracy. `gate1-signoff --phase calibration` and the approvals have
NOT been run.** Complete cases: `reports/gate1_calibration_cases.json`.

## Per-model held-out results

| Model | Items | Valid | Coverage | Disagree | Rate (valid) | Directional P→V / F→S | Invalid (all length) | Identification interval | Judge pass |
|---|---|---|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 246 | 230 | 0.935 | 12 | 0.052 | 1 / 11 | 16 | [0.886, 0.951] | 15 m 53 s |
| qwen3-4b | 246 | 241 | 0.980 | 3 | 0.012 | 3 / 0 | 5 | [0.968, 0.988] | 13 m 41 s |
| qwen3-4b-instruct-2507 | 247 | 245 | 0.992 | 7 | 0.029 | 5 / 2 | 2 | [0.964, 0.972] | 11 m 01 s |
| gemma-3n-e4b-it | 246 | 232 | 0.943 | 9 | 0.039 | 1 / 8 | 14 | [0.907, 0.963] | 15 m 34 s |
| **Overall** | **985** | **948** | **0.962** | **31** | **0.033** | 10 / 21 | **37** | **[0.931, 0.968]** | 51 m (two GPUs) |

2×2 tables (verifier pass/fail × autorater SATISFIES/VIOLATES):
E2B 141/1/11/77 · qwen3-4b 168/3/0/70 · instruct 158/5/2/80 ·
E4B 180/1/8/43. Marginals, by-`n`/by-source breakdowns for both
disagreements and invalids, and every complete case (constraint, full
response, both verdicts, justification, `n`, source, `split_class`,
mechanical cross-checks) are in the cases file. Invalid outputs: 37,
all `invalid_output` with `finish_reason=length` (no refusals, no
generation failures), concentrated at n ∈ {7, 8} on dense texts. No
backend anomalies, OOMs, retries, or crashes; throughput consistent
with the development rounds.

## Development (high) vs calibration — descriptive comparison

- **Same residual pattern:** 26 of 31 disagreements are ±1 counting
  errors (under-count 20, over-count 6; plus 4 with unparsed counts and
  one severe under-count claiming 8 on a 10-occurrence text — the known
  saturation mode, single case). Direction remains predominantly
  fail→SATISFIES on the gemma models, mixed on the qwens — as in
  development.
- **Same high-`n` concentration:** disagreements and truncations
  concentrate at n ≥ 5; invalids at n ∈ {7, 8}.
- **Invalid pattern:** 37 vs development's 42 on a same-sized set;
  same status, same finish reason, same concentration. Not materially
  different.
- **New qualitative failure modes:** none observed.
- **Verifier defects:** none — the frozen S0 verifier, the independent
  reimplementation, and a word-boundary regex agree on **31/31**
  disagreement cases; every case classifies as a judge-side miscount.
- **Distribution shift:** none of note — per-model rates (0.052 /
  0.012 / 0.029 / 0.039) sit within the development-round ranges
  (0.035 / 0.004 / 0.050 / 0.030), and the overall identification
  interval [0.931, 0.968] is nearly identical to development's
  [0.929, 0.972].

## Cases warranting researcher attention (none blocking, all preserved)

1. E2B `fail→SATISFIES` lean (11 of 12): under-counting on near-miss
   fail items — consistent with development; relevant when reading the
   fail-class column of the contingency table.
2. The one severe case (E2B, claimed 8 vs actual 10, n=8 stratum) —
   the saturation mode surviving at high effort, single occurrence.
3. Coverage on the gemma replications (0.935 / 0.943) — truncation
   abstentions on dense texts, transparent in the statuses and priced
   into the interval lower bounds.

## Suitability assessment

The calibration evidence is, in my assessment, suitable for researcher
sign-off **under the registered weaker autorater-calibration claim**:
it was produced one-shot on the untouched halves under a verified
freeze; it reproduces the development-characterized instrument behavior
with no new failure modes, no distribution shift, and no case
suggesting a deterministic-verifier defect; coverage and the
identification intervals transparently carry the truncation trade-off.
The strongest supported claim remains, verbatim: *"The frozen
deterministic verifier was developed and evaluated on held-out
responses against the specified autorater under the registered
configuration. Independent human validation is unavailable."*

## Pending researcher actions (not run)

1. `gate1-signoff --phase calibration --notes <inspection.json>`
2. `gate1 --model <each> --approve-autorater-calibration`
