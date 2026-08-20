# DCI — current scientific state

The 10-minute orientation. Everything here points at something else; primary
numbers live in the reports and the generated artifacts, not in this file.

Last reviewed: 2026-08-13.

---

## 1. The question

Does adding instruction **B** to a prompt causally degrade compliance with
instruction **A**, over and above the generic cost of one more instruction?

The design removes that confound by *replacement* rather than addition — compare
a composition containing B against one where B is swapped for a comparable
reference R, holding the background set S and the instruction count fixed:

```
A + B + S     versus     A + R + S
τ(B→A | S,R) = P(fail A | A+B+S) − P(fail A | A+R+S)
```

Positive τ is directional interference.

## 2. Two arms, different rules

| | `src/dci/` + `configs/` + `notebook_source/` | `exploratory/` |
|---|---|---|
| what | the preregistered v15/v19 protocol | fast, cheap, local-GPU probing |
| changes | ledgered amendments (`docs/migration_ledger.csv`, `src/dci/v19/stage2_frozen.json`) | free; interfaces break by design |
| output | a **gate status**, not a number (`src/dci/statuses.py`) | estimates stamped `EXPLORATORY_NO_EVIDENCE` |
| status | Stage 2 frozen; the confirmatory run has **not** been executed | eleven rounds completed |

They are coupled in one direction: `exploratory/dci_exploratory/harvest.py`
executes confirmatory stages `c112…c212` at runtime to obtain the constraint
definitions, wordings, verifiers and task bank, so the exploratory arm invents no
scientific content — and a change in `src/dci/` changes what an exploratory design
means. Each run records the definition hashes it used.

## 3. Experiment families

Eleven, indexed with entrypoints, analysis code, reports and per-family status in
**[`exploratory/EXPERIMENTS.md`](exploratory/EXPERIMENTS.md)**.

## 4. What is currently believed

Scope for essentially all of it: one target/focal pair, the Qwen3-4B lineage,
20 pilot tasks, exploratory inference. Full ledgers with evidence and limitations
in [`exploratory/CLAIM_EVIDENCE_MATRIX.md`](exploratory/CLAIM_EVIDENCE_MATRIX.md)
and [`exploratory/HYPOTHESES.md`](exploratory/HYPOTHESES.md).

- **The effect is real but not pair-specific.** Certain added instructions cause
  large target failure that matched references do not — but the registered focal
  B has essentially no effect on its own. Its effect is a higher-order interaction
  with the background. *(`FINDINGS.md`, `ROUND5_REPORT.md`)*
- **The failure has a shape.** The model satisfies a punctuation demand by writing
  one multi-clause sentence, destroying the unit the target counts. *(`METRIC_SPEC.md`)*
- **The trigger is a property of the instruction, not the output.** Emission of
  the mark does not track the effect; receiving the instruction does.
  *(`AMPLIFIER_MECHANISM_MATRIX.md`)*
- **Leading mechanism: clause-boundary affordance.** Marks that can stand where a
  sentence boundary stands amplify; matched marks that cannot do not. Supported
  predictively; the causal crossing was designed and **not run**.
  *(`BOUNDARY_MECHANISM_REPORT.md`)*
- **Order is a treatment.** The same instructions span amplification to reversal
  depending on order. No simple positional rule survives. *(`CLAIM_EVIDENCE_MATRIX.md`)*
- **Reasoning re-prioritises; it does not compose.** Thinking removes the
  control-context interference but leaves the amplified context largely intact,
  and joint satisfaction stays rare. Explicit priority cues are attended to in the
  traces and do not change the answer. *(`NATURAL_REASONING_RESULTS.md`, `ROUND11_ARBITRATION_REPORT.md`)*
- **Transport decomposes.** The disposition is universal; the arbitration is
  checkpoint-specific. On 2026 checkpoints the target saturates, so τ = 0 − 0 by
  construction — a structural zero, never a behavioural null.
  *(`ACTUAL_CROSS_MODEL_DCI_RESULTS.md`)*
- **The execution condition is part of the result.** Checkpoint+revision, backend,
  dtype, chat template, reasoning mode, decoding, seeds, parser and answer
  extraction. Results from materially different conditions are reported side by
  side, never pooled. *(`CROSS_MODEL_EXECUTION_MATRIX.md`)*

## 4b. DCI-1: the registered study line

`dci1/` is a separate, isolated study module with its own preregistrations and
its own evidence tree. It does not share code with `src/dci/` or
`exploratory/`.

| Version | Status |
|---|---|
| v2 | closed |
| v3 | closed. Two Gemma replications reached UNMASKED_ANALYSIS; both Qwen replications terminated at Gate 2A. `dci1/RESULTS_V3.md` |
| B+R pilot | non-confirmatory design evidence for v4. `dci1/reports/br_pilot_v4/` |
| **v4** | **implemented, not frozen, no confirmatory data.** `docs/v4_traceability.md`, `dci1/docs/v4_prefreeze/` |

v4 replaces target failure with the per-constraint compliance vector, makes
reciprocal delivery loss the primary estimand, matches references to A on solo
compliance rather than to B on solo failure, and makes instruction order a
cell-level factor. It is a different protocol: v3 and v4 numbers are not
comparable and are never compared. Nine registered open decisions (V1 to V9)
and seven pre-freeze checks remain open; the freeze and confirmatory generation
are implemented and deliberately not executed.

### 4c. The reference-pool tension, and what was screened against it (2026-08-20)

A read-only diagnostic established that the §13.2 reference criterion fails for
a **structural** reason, not a statistical one: every registered reference
family is an `S <= q` monotone count budget whose pass set is downward-closed
under prefix, so the empty string scores 94/94 on the pool, 4/4 on B, and 0/8
on A. Only 3-6 of 94 rungs per model meet the vacuity condition and **none**
fall inside the caliper. B carries the same defect and B is the primary
outcome, so `D(B<-A)` itself carries a length channel.

A non-confirmatory FORM x STEM screen (13,392 rows, protocol hash
`98f8ee0d...`) tested two answers. **FORM works**: candidate non-budget
families reach the condition-1 ∧ condition-6 conjunction on three of four
models, with bootstrap P(>=3) of 0.41-0.88 against 0.000-0.001 for the
registered pool, and the result is insensitive to the non-vacuity threshold.
**STEM works for its stated purpose but is not adoptable**: a uniform
answer-length instruction removes B-solo vacuity and makes the raw and
length-restricted `D(B<-A)` converge, but drives **both Qwen replications to
`FOCAL_RANGE_EXHAUSTED`**.

Nothing registered changed. Two amendment drafts sit in `user-notes/`, neither
adopted; Amendment B (reference form) is supported and blocked on
calibration-set confirmation, Amendment A (prompt stem) is blocked on the focal
grid. Full report: `dci1/reports/fs_screen_v4/REPORT.md`.

Gate 1 remains the binding constraint on everything downstream.

## 5. Provisional, superseded, broken, unresolved

- **Superseded.** The capped reasoning-curve exports under
  `exploratory/figures/reasoning_compute/data/` were built by a figure path that
  bypassed the canonical-evidence guard. Marked, retained, not regenerable in this
  checkout — `PROVENANCE.json` there says exactly what and why. The natural-endpoint
  headline is unaffected.
- **Void.** The anti-splice intervention failed its own manipulation check
  (`ANTI_SPLICE_MANIPULATION_FAILED`). A failed manipulation check voids an
  estimate; it does not weaken it into a null.
- **Blocked.** The five-checkpoint vLLM TP=2 qualification gate passed 0/5, for
  three unrelated reasons (`ROOT_CAUSE_ANALYSIS.md`). The Transformers-vs-vLLM
  backend confound on the transport question is therefore unresolved.
- **Withdrawn.** Several early quantitative claims — a nested correlation, a
  mislabelled statistic, a buggy sentence counter, a shared-seed replicate regime.
  Kept and marked in section D of `CLAIM_EVIDENCE_MATRIX.md`; never cited as support.
- **Not reproducible from a clone.** `runs/` is gitignored and absent. The run
  manifests hash files a fresh checkout does not have. See
  `exploratory/evidence/README.md` for the promotion path that fixes this per claim.
- **Open, and most valuable next:** the boundary-affordance causal crossing; a
  pair with a genuine trade-off region; finishing the cross-model dataset on one
  backend.

## 6. Recent consequential changes

[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) — measurement-affecting changes
only, newest first, each stating what changed, which results are affected, and
whether old and new remain comparable. Most recent: the figure-data admission
fix noted in §5.

## 7. Where to look

| To see | Go to |
|---|---|
| what each experiment family did | `exploratory/EXPERIMENTS.md` |
| the claim ledger with evidence | `exploratory/CLAIM_EVIDENCE_MATRIX.md` |
| why an experiment was chosen | `exploratory/DECISIONS.md` (written before each run) |
| what the metrics mean exactly | `exploratory/METRIC_SPEC.md` |
| which data files are admissible | `exploratory/REASONING_DATA_PROVENANCE.md` |
| what was actually covered | `exploratory/EXPERIMENT_COVERAGE_MATRIX.md` (rebuilt from run configs) |
| the confirmatory protocol | `README.md`, `docs/MIGRATION.md`, `docs/preregistration/` |
| the frozen Stage 2 decisions | `src/dci/v19/stage2_frozen.json`, `docs/v19_stage2_specification_amendments.md` |

## 8. Keeping this file honest

It is derivative by design: claims link to reports, reports link to runs, runs
carry their own configuration. Update §4–§6 when `CHANGES_SCIENTIFIC.md` gains an
entry; if a statement here cannot be traced to a linked artifact, delete it rather
than maintain it.
