# DCI-1 v3 — final results report

**Date:** 2026-08-19 · **Protocol:** DCI-1 v3.0 · **Study id:** `dci1-v3`
**Question:** does adding a focal constraint B ("every word ≤ m letters")
increase failure on a target constraint A ("use the word *however*
exactly n times"), relative to nuisance-matched reference constraints R?
**Authority:** `user-notes/DCI-1_preregistration_v3.md` as amended
(`DECISIONS_V3.md`); readiness report `REPORT_V3.md`. All record hashes
below are the first 12 hex of signed records under `evidence/dci1-v3/`;
the durable mirror is byte-identical.

Evidence categories used throughout, kept strictly separate:

* **REGISTERED** — preregistered confirmatory results, read from signed
  stage records under the registered claim rules.
* **DIAGNOSTIC** — registered secondary diagnostics (pseudo-runs, greedy
  runs, per-reference/uptake patterns). Never claims.
* **CAVEAT** — measurement-validity evidence bounding what the outcome
  measure supports.
* **SENSITIVITY** — unregistered, read-only re-analysis of registered
  rows. Never changes a registered outcome.

## 1. Study status

Execution is complete; no registered operation remains.

| Replication | Final state | Closing record |
|---|---|---|
| `gemma-3n-e2b-it` | `UNMASKED_ANALYSIS` (complete) | `unmasked_result.json` `2b9c3b286601` |
| `qwen3-4b` | terminal `REFERENCE_POOL_MISMATCH` at Gate 2A | `terminal_report.json` `bdd603e31603` |
| `qwen3-4b-instruct-2507` | terminal `REFERENCE_POOL_MISMATCH` at Gate 2A | `terminal_report.json` `6497c4bc9e07` |
| `gemma-3n-e4b-it` | `UNMASKED_ANALYSIS` (complete) | `unmasked_result.json` `cb6f57dd9b62` |

Both Gemma trees pass `verify-evidence` (status VERIFIED, all integrity
checks, durable mirror intact). The masked-phase analysis was reproduced
bit-for-bit at unmasking for both (`masked_reproduced: true`). Verifier
freeze `334bb2b18079` held unchanged through every post-Gate-1 stage
(enforced at the dispatcher since commit `685dc05`). Human
verifier-validation (120 blind labels) is complete and committed
(`7ead292`); §5.

## 2. Registered primary results (REGISTERED)

Estimand (§11–§14): per block i, D_i = F_i(AB) − ⅓·ΣF_i(AR1..AR3), where
F is exact-count target failure under frozen rule S0;
τ_target_first and τ_added_first are the stratum means (family F1).
384 blocks per model (192 per order stratum), one registered primary draw
per cell (`primary_selection.json`: `H("primary-root", model-id,
prompt-hash) mod 16`), order-stratified block bootstrap, 10,000
resamples. Claims are read from the family-simultaneous 95% interval;
SESOI = 0.10; equivalence region ±0.10 (licensed emitter only).

| Model | Stratum | τ̂ | 95% simultaneous | 95% marginal | Direction | Magnitude |
|---|---|---:|---:|---:|---|---|
| E2B (n\*=5, m\*=7) | target-first | +0.007 | [−0.080, +0.094] | [−0.068, +0.083] | unresolved | **equivalence** (\|τ\| < 0.10) |
| E2B | added-first | −0.026 | [−0.117, +0.065] | [−0.106, +0.054] | unresolved | unresolved |
| E4B (n\*=7, m\*=7) | target-first | +0.090 | [−0.003, +0.184] | [+0.007, +0.172] | unresolved | unresolved |
| E4B | added-first | +0.040 | [−0.047, +0.127] | [−0.047, +0.116] | unresolved | unresolved |

The single resolved registered claim is the licensed **equivalence** for
E2B target-first: the simultaneous interval lies inside ±0.10, so any
interference effect there is smaller than the registered
smallest-effect-size-of-interest. E4B target-first misses direction
resolution by its simultaneous lower bound (−0.003); its *marginal*
interval excludes zero, but the registered claim rule reads the
simultaneous interval. Full family tables (F1–F6):
`<model>/analysis/unmasked/result.json`.

### Design selected per replication (Gates 2A/2B)

| Model | n\* | m\* | Focal rate @ m\* | Matched references (family@severity → arm) | Records |
|---|---:|---:|---:|---|---|
| E2B | 5 | 7 | 0.188 | RF1@5 (≤5 words starting "b") → AR1 · RF2@5 (≤5 "-ing" words) → AR2 · RF6@4 (≤4 capitals) → AR3 | 2A `57986a4e3676` · 2B `e5aa5ae1b5fa` · freeze `2e44601714b3` |
| E4B | 7 | 7 | 0.240 | RF2@2 (≤2 "-ing" words) → AR1 · RF6@4 (≤4 capitals) → AR2 · RF4@4 (≤4 double-letter words) → AR3 | 2A `9853efca70c3` · 2B `2ced8a24fcb8` · freeze `99a5693c4693` |

Confirmatory manifests: E2B `d4e8ce9b88ce`, E4B `76dd5aa0521f`
(36,864 generations each; masked records `1c5882ce2f0a` / `1a24dd19fa9d`).

### Consistency across references and strata

* **E2B — resolved reference heterogeneity.** Exchangeability fails:
  AR2−AR3 = −0.154, simultaneous [−0.234, −0.073]; AR1−AR3 = −0.083,
  [−0.164, −0.003] (F2). Per-reference contrasts split sign in the
  target-first stratum: vs AR2 **+0.135** [+0.011, +0.260] (resolved
  positive) but vs AR3 **−0.130** [−0.254, −0.007] (resolved negative)
  (F3). The E2B answer depends on which reference is compared against —
  a matching problem, not a clean null.
* **E4B — homogeneous but unresolved.** All six per-reference contrasts
  positive (+0.010 … +0.120); none resolves. Exchangeability also fails,
  by interval width rather than separation.
* **Manipulation check (uptake) flags (CAVEAT).** Demonstrated
  compliance with the *added* constraint itself: E2B — AB 36%, AR1 54%,
  AR2 32%, AR3 2% (`uptake_diff_AR3` flagged). E4B — AB 44% vs
  references 7% / 4% / 10% (**all three flagged**). The E4B references
  match on solo failure rate but not on demonstrated uptake; E4B's
  positive point estimates carry this caveat.
* **Robustness rules S1–S3** (case-sensitive, substring,
  restatement-stripped counting; F4) broadly track S0. Resolved members:
  small positive E2B S1 contrasts (+0.017 target-first, +0.052
  added-first) and E4B S1 added-first +0.075 [+0.029, +0.120].

### Secondary diagnostics (DIAGNOSTIC)

| Model | Diagnostic | target-first | added-first | Note |
|---|---|---|---|---|
| E2B | Pseudo-selection, 1,000 alternative primary draws | mean +0.089 · 99.5% > 0 | mean +0.038 · 85.4% > 0 | Registered draw (+0.007) is *below the 5th percentile* (+0.030) of its own draw distribution |
| E2B | Greedy (96 blocks, temperature 0) | pooled mean +0.104 · 40.6% of blocks > 0 | | no draw lottery |
| E4B | Pseudo-selection, 1,000 draws | mean +0.065 · 94.9% > 0 | mean +0.081 · 98.8% > 0 | registered draws near the pseudo means |
| E4B | Greedy (96 blocks) | pooled mean +0.111 · 50.0% of blocks > 0 | | |

Every diagnostic mean is positive, in the +0.04 … +0.11 range. Primary-
draw luck moved E2B's registered target-first estimate by ≈ −0.08
relative to its across-draw mean. Diagnostics inform design, not claims.

## 3. Qwen replications: not identified under the registered design

Both stopped at Gate 2A with the registered terminal status
`REFERENCE_POOL_MISMATCH`: fewer than three reference family/severity
pairs had solo failure rates within the ±0.10 caliper of the focal rate
at m\*.

| Model | m\* | Focal rate | Caliper window | Eligible pairs (≥ 3 required) |
|---|---:|---:|---:|---|
| `qwen3-4b` (`bdd603e31603`) | 10 | 0.313 | [0.213, 0.413] | RF4@2 (0.240), RF6@0 (0.323) — 2 |
| `qwen3-4b-instruct-2507` (`6497c4bc9e07`) | 8 | 0.260 | [0.160, 0.360] | RF3@2 (0.281), RF4@4 (0.323) — 2 |

The cause is structural: at every registered non-zero severity the Qwen
models comply with most reference families almost perfectly (solo
failure ≤ 0.10) while their focal failure sits at 0.26–0.31; the fixed
severity grids cannot produce difficulty-matched references for these
models. **Licensed:** "the estimand is not identified for these models
under this design." **Not licensed:** any claim that interference is
absent, small, or different in Qwen models. These outcomes carry no
evidence about the effect.

## 4. Cross-model synthesis

* **Does adding B increase failure on A relative to matched
  references?** REGISTERED: not resolved in either identified
  replication. DIAGNOSTIC: pseudo-selection distributions, greedy runs,
  the E4B marginal intervals, and E4B per-reference homogeneity
  consistently point to a small positive effect, roughly +0.04 … +0.11
  absolute failure-rate increase.
* **Directional?** Unresolved under the registered rule, 4 of 4
  estimands. Closest call: E4B target-first (simultaneous lower bound
  −0.003).
* **Replicated?** No. At the registered level E2B (compatible with
  zero; equivalence licensed in one stratum) and E4B (positive trend)
  diverge. Diagnostics soften but do not remove the discrepancy: E2B's
  across-draw mean (+0.089 target-first) resembles E4B's (+0.065), and
  its registered draw is a low-tail draw.
* **Practically large?** No, by the study's own standard. Nothing
  approaches a resolved magnitude above SESOI 0.10; the one resolved
  magnitude statement is that E2B target-first is *smaller* than 0.10
  in absolute value.
* **Confirmatory vs exploratory.** Confirmatory: the four τ claims, the
  equivalence claim, the exchangeability failures, the two terminal
  outcomes. Everything else in this report is diagnostic, caveat, or
  sensitivity.

## 5. Measurement validity (CAVEAT)

Outcome measure status: **verifier-defined** (frozen deterministic rule
S0), Gate 1 basis `autorater_calibration_approved`,
`HUMAN_VALIDATION_UNAVAILABLE` at gate time (amendment A2). Subsequent
human validation (author-annotator, blind, chained + hash-pinned
records; committed `7ead292`;
`autorater_forensics/experiments/human_review/validation_report.{md,json}`):
120 labels, overall agreement 116/120 = 96.7%.

| Slice | Cases | Disagreements | Rate | 95% Wilson upper | Registered ≤ 10% |
|---|---:|---:|---:|---:|---|
| Representative, verifier-pass | 52 | 0 | 0.0% | 4.9% | met (also ≤ 5%) |
| Representative, verifier-fail | 52 | 4 | 7.7% | 16.1% | **not met** |
| Boundary stress probe | 16 | 0 | 0.0% | — | n/a |

All four disagreements: human SATISFIES where the true count is exactly
n+1; four independent recounts reproduced the verifier on each. The
bound therefore measures *unaided human counting reliability at the
off-by-one boundary* (4/44 = 9.1% on |s0−n| = 1 fail items; 0/16 at
larger margins), not verifier error. Consequences: "human-validated" may
be claimed for the pass class only; the fail-class criterion is unmet;
the outcome remains verifier-defined. Blind labels are preserved
verbatim; no adjudication was run; the sealed 40-item reserved set
(sha256 `f8831598…d7a3`) is untouched. This annotator is the study
author; the labels are diagnostic evidence, not registered independent
A1 validation.

## 6. Near-miss sensitivity (SENSITIVITY — unregistered, read-only)

Motivation: §5 shows humans cannot reliably distinguish count = n from
n+1, and near-miss failures (|s0−n\*| = 1) are **67–85% of all failures
in every arm**. The failure indicator decomposes exactly:
τ_exact = τ_near-miss + τ_far-miss, where the far-miss ("tolerant")
rule counts only |s0−n\*| > 1 as failure. Derived entirely from the
registered rows (`analysis/unmasked/unmasked_rows.jsonl`); the script
(`tools/nearmiss_sensitivity_v3.py`, output
`reports/nearmiss_sensitivity_v3.json`) first reproduces the registered
point estimates exactly under the exact rule, then computes:

| Model | Stratum | τ registered (exact) | τ tolerant (±1 passes) | tolerant 95% CI\* | near-miss component |
|---|---|---:|---:|---:|---:|
| E2B | target-first | +0.007 | −0.040 | [−0.094, +0.014] | +0.047 |
| E2B | added-first | −0.026 | +0.036 | [−0.009, +0.085] | −0.062 |
| E4B | target-first | +0.090 | +0.056 | [+0.007, +0.106] | +0.035 |
| E4B | added-first | +0.040 | +0.123 | [+0.057, +0.191] | −0.083 |

\* Unregistered stratified block bootstrap (10,000 resamples, fresh
seed 0), marginal percentile intervals — not the registered
simultaneous machinery.

**Reading.** E2B: the near-zero estimates are boundary-fragile — signs
flip under the tolerant rule in both strata and nothing resolves either
way; the E2B conclusion is unchanged. E4B: the positive tendency
*survives discounting near-misses* — tolerant estimates stay positive in
both strata and both unregistered intervals exclude zero (added-first
strengthens to +0.123). No conclusion in this report reverses when
near-miss failures are excluded or separated. The registered outcome is
untouched by construction.

## 7. Bottom line

**DCI-1 v3 did not find a confirmable directional interference
effect.** In the two replications where the registered design was
identified (gemma-3n-e2b-it, gemma-3n-e4b-it), adding the composed
focal constraint changed exact-count target failure by an amount the
study could not resolve in direction; the one resolved registered claim
is that for E2B in the target-first stratum the effect is *equivalent
to zero within ±0.10*. E4B's estimates are positive (+0.09
target-first, +0.04 added-first) but fall just short of resolution
under the registered simultaneous rule.

The registered secondary diagnostics and the unregistered sensitivity
consistently indicate a **real but small positive interference effect —
roughly +0.04 … +0.12 absolute failure increase, below the study's own
0.10 practical-significance threshold** — clearest in E4B and in
across-draw averages, and not attributable to off-by-one counting
noise. The two Qwen replications produced no estimate: a
design-identification failure that says nothing about the effect. All
outcomes are verifier-defined; human validation certifies the
verifier-pass class (0/52) while the verifier-fail class missed the
registered ≤ 10% criterion (Wilson upper 16.1%), every disagreement
being a human off-by-one miscount, not a verifier error.

## 8. Remaining scientific blockers, ranked

1. **Run the B+R / B+S discriminating experiment** (registered as the
   natural next step; not executed). It is the only design on the table
   that separates *target-specific* interference from *generic
   constraint load* — the distinction on which E2B's resolved
   per-reference sign flips and the E4B uptake imbalance currently cast
   doubt.
2. **Fix the power/selection-stability gap before any v4 confirmatory
   run.** The primary-draw lottery has an SD (≈ 0.036–0.039) comparable
   to the block-level SE, and E2B's registered draw landed below its
   own 5th percentile. Averaging over draws as the registered estimand
   (or ≥ 2–3× blocks) would resolve effects of the observed
   ≈ +0.05–0.09 size; the current design cannot.
3. **Redesign reference matching.** Match on demonstrated uptake as
   well as solo failure rate, and use adaptive severity grids — one
   change addressing both the E4B manipulation-check flags and the Qwen
   identification failures.
4. **Close the fail-class human-validation gap** with an independent
   second annotator and a tool-assisted counting protocol (34 further
   zero-error fail-class labels meet ≤ 10%; the observed unaided rate
   makes ≤ 5% unreachable). The sealed 40-item set stays sealed until a
   future judge-configuration freeze.

## Appendix: evidence index

| Artifact | gemma-3n-e2b-it | gemma-3n-e4b-it |
|---|---|---|
| Gate 2A `gate2a_solo.json` | `57986a4e3676` | `9853efca70c3` |
| Gate 2B `gate2b_composed.json` | `e5aa5ae1b5fa` | `2ced8a24fcb8` |
| Gate 3 `gate3_freeze.json` | `2e44601714b3` | `99a5693c4693` |
| Confirmatory manifest | `d4e8ce9b88ce` | `76dd5aa0521f` |
| Masked result | `1c5882ce2f0a` | `1a24dd19fa9d` |
| Unmasked result | `2b9c3b286601` | `cb6f57dd9b62` |

Family tables and rows: `<model>/analysis/unmasked/result.json`,
`analysis/unmasked/unmasked_rows.jsonl` (2,304 rows each). Diagnostics:
`<model>/pseudo_runs.json`, `<model>/greedy_run.json` (unsigned summary
artifacts inside verified trees). Qwen terminals:
`<model>/terminal_report.json` `bdd603e31603` / `6497c4bc9e07`.
Study-level: `verifier_freeze.json` `334bb2b18079`;
`gate1_calibration_signoff.json`; registration manifest
`ba1a3a369493`. Human validation:
`autorater_forensics/experiments/human_review/` (report, chained
records, pins). Sensitivity: `tools/nearmiss_sensitivity_v3.py` →
`reports/nearmiss_sensitivity_v3.json`.
