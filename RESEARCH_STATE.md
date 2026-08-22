# DCI — current scientific state

The 10-minute orientation. Everything here points at something else; primary
numbers live in the reports and the generated artifacts, not in this file.

Last reviewed: 2026-08-22.

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
| **v4r2** | **implemented, not frozen, no confirmatory data**, terminal at Gate 2 as registered. `docs/v4_traceability.md`, `dci1/docs/v4_prefreeze/` |
| **v4r3** | **closed 2026-08-21, terminal at `GATE_1_MEASUREMENT`, no confirmatory data.** Adopted and registered, run through stage 3, and stopped where its registered criterion stopped it: §18 stage 4 required §10.2 plus §10.3 or §10.4, and neither pathway established that basis. Superseded by v4r4; its evidence is preserved unedited and its closure is hashed. §4h–§4l, §4m. `user-notes/DCI1_preregistration_v4r3.md`, `dci1/reports/dci1v4r3/closure.json` |
| **v5** | **drafted and implemented 2026-08-22; NOT adopted, no stage record, no instrument measured, no generation.** Four §34 decisions taken (D3, D6, D16, D18) and the 96 Calibration-B questions authored; fifteen decisions and one specification question remain, four with evidence-backed recommendations. A standalone preregistration that rebuilds the reference-construction procedure v4r4 could not make work. The core reference pool inverts to production class and same-form with A; ι is demoted from the admission coordinate to the difficulty coordinate; a pre-composition interaction gate, two calibration splits, direct order estimands and the L4 fix are new. Its execution plumbing has been exercised end to end on synthetic fixtures, which is engineering evidence and not a result. §4q, §4r, §4s, §4t. [`user-notes/DCI1_preregistration_v5.md`](user-notes/DCI1_preregistration_v5.md), [`dci1/src/dci1v5/`](dci1/src/dci1v5/), [`dci1/reports/dci1v5/`](dci1/reports/dci1v5/) |
| **v4r4** | **adopted 2026-08-21; frozen at Gate 5 on 2026-08-22 for two of four replications, confirmatory data in hand.** The live protocol line. Gate 1 is deterministic-measurement by construction (§10.7 A–E) and `CP4`/`CP7` are removed. All four replications passed Gates 1–3; **§13.10 then ended two of them at `COMPOSED_HEADROOM_FAILURE`, including the only full-design replication**. Two survive to Gate 5, both on §8.6's 8-cell reduced design, so no spectrum-dependent estimand is identified anywhere in the study. Both survivors froze at `450a049`, generated 24,576 rows each, and are analysed through `UNMASKED_ANALYSIS`; **they disagree qualitatively** and one replication's L4 field is invalidated. §4m, §4n, §4o, §4p. `user-notes/DCI1_preregistration_v4r4.md`, `dci1/reports/dci1v4r4/final_results.json` |

v4r2 replaces target failure with the per-constraint compliance vector, makes
reciprocal delivery loss the primary estimand, matches references to A on solo
compliance rather than to B on solo failure, and makes instruction order a
cell-level factor. It is a different protocol: v3 and v4 numbers are not
comparable and are never compared. Nine registered open decisions (V1 to V9)
and seven pre-freeze checks remain open; the freeze and confirmatory generation
are implemented and deliberately not executed. **v4r4 (§4m) is the live
protocol line**; it supersedes v4r3, which superseded v4r2. Each was adopted
and registered on 2026-08-21, and each is structurally prevented from reading
the others' artifacts: `dci1v4r4.engine.context.foreign_roots` names v4r3's
evidence, durable and source trees, and `assert_own_study` refuses a stage
record whose `study_id` is another revision's. No v4r2 and no v4r3 record was
edited by any of it.

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
**STEM works for its stated purpose but costs a replication**: a uniform
answer-length instruction removes B-solo vacuity and makes the raw and
length-restricted `D(B<-A)` converge, but drives Qwen replications to
`FOCAL_RANGE_EXHAUSTED` on the registered focal grid. That screen read the
effect as terminating *both* Qwens; §4d corrects it to one.

Nothing registered changed. Two amendment drafts sit in `user-notes/`, neither
adopted; Amendment B (reference form) is supported and blocked on
calibration-set confirmation, Amendment A (prompt stem) is blocked on the focal
grid. Full report: `dci1/reports/fs_screen_v4/REPORT.md`.

Gate 1 remains the binding constraint on everything downstream.

### 4d. The focal grid, and Gate 1's §10.2 evidence (2026-08-20)

A second non-confirmatory screen (B-grid, 2,112 rows, protocol hash
`6a63ba78...`) measured B's solo curve under the floored stem at m in
{7,...,12}. **An honest focal severity exists at m <= 12 on all four models**,
but the §1.4 verdict is **MARGINAL**: qwen3-4b-instruct-2507's only two in-band
rungs are both 0.667, within one clustered standard error of the band floor, so
a fresh-topic confirmation is required before any grid amendment.

It also **corrects §4c**. On an independently seeded redraw the floored stem
terminates qwen3-4b decisively (0.375 against a 0.60 floor, 2.3 SE, agreeing
with the earlier screen to within 0.042 at every registered rung) but
qwen3-4b-instruct-2507 does **not** terminate: 0.542 in the FORM x STEM draw,
0.667 here. The terminal-status call flipped between two single draws on the
same 24 topics. Two further quantities on that model sit on band edges under the
stem. Report: `dci1/reports/bgrid_screen_v4/REPORT.md`. Amendment C drafted, not
adopted; `FOCAL_GRID` unchanged.

Separately, **§10.2 is now met for A and B**. Three-process determinism, the
frozen boundary suites (48 A cases, 45 B cases), the prose-only reimplementation
and the carry-over record all pass over 13,953 distinct genuine responses.
C4 and C5 are complete. Gate 1 still cannot be approved: the family verifiers
have no §10.2 evidence and cannot get any until the reference pool is final.
Report: `dci1/reports/gate1_v4/REPORT.md`.

### 4e. The Gate-2 calibration screen, and what it settles (2026-08-20)

A third non-confirmatory screen (`dci1/src/cal_screen_v4/`, main-arm protocol
hash `fd49e5d4...`) ran §12.3, §12.4 and §13.2 on the **registered calibration
sample** — the 96 solo topics at M_cal = 4 — which is the sample §13.2 admits
against and which no earlier screen had used. The registered code does the
deciding: `cal_screen_v4/admission.py` is required to reproduce
`gates.admit_family` byte for byte, and the `current`-stem arm renders through
`dci1v4.design.prompts.render`, asserted identical.

Four things it settles, none of them adopted:

- **The registered prompt cannot start.** B's solo vacuity rate is **at least
  0.208 at every** rung of m in {7,...,12} on **all four** models, rising to
  0.870, against a §12.4 maximum of 0.10. `REGIME_NOT_FOUND` everywhere, before the reference question
  arises. Under the floored stem the same cells are 0.000–0.060.
- **The registered reference pool was length-falsified, not falsified.** Under
  the floored stem, registered families clearing §13.2's conditions 1 and 6 at
  the same severity: **E2B 3, E4B 4, qwen3-4b 1, qwen3-4b-instruct-2507 4** —
  against 0 of 64 under the current stem, at solo vacuity 0.000 at almost every
  crossing. The pool's condition-6 failure was a property of the responses the
  registered prompt elicits, not of the pool.
- **§13.2 is not ambiguous, and the earlier claim that it is has been
  withdrawn** (2026-08-20). §12.2 measures **all 94 rungs** on the 24 pre-screen
  topics and §13.2's feasible set is a subset of the shortlist §12.2 writes, so
  condition 2 always has its input — verified on all four registered
  `REGIME_SCREEN` records, 94 of 94 rungs measured, 0 shortlisted rungs without
  a value. Where the case is constructed anyway `gates.admit_family` rejects,
  and `regime.assert_shortlist_is_measured` now refuses to write a record that
  could produce it. The screens met the case because they ran §13.2 over rungs
  outside the shortlist on a partial floored-stem pre-screen — properties of the
  screens. **The registered §13.2 has not been run on any model, because Gate 2
  has not run**, so the screens' abstain/reject counts are not the registered
  pool's admission result. `dci1/reports/section_13_2_v4/REPORT.md`.
- **Three references exist on every model in the screen's enlarged pool** —
  5, 3, 3 and 5 admitted families, a screen result and not a Gate 3 outcome. But on E4B and
  qwen3-4b the third slot can only be filled by a **lower-bound
  (production-class)** family, so on those two models the class confound is
  unavoidable *inside the reference set* rather than being a separate arm.
- **Amendment C should be per-model.** Under the floored stem the registered
  focal grid supplies an in-band m\* on E2B (10), E4B (9) and
  qwen3-4b-instruct-2507 (10); only qwen3-4b is exhausted. On
  qwen3-4b-instruct-2507 a *global* extension moves m\* from 10 to 11 and off
  the only rung feasible under both readings of §12.4's graded clause. The
  B-grid screen's MARGINAL verdict is confirmed on fresh topics for the one
  model that needs the extension.
- **A new blocker, ahead of all of them.** §12.4's graded clause has two
  readings and the registered code fixes neither. Applied to B, the mean-graded
  reading fires on **every** in-band rung — §12.3 declares a rung eligible and
  §12.4 declares the same rung degenerate — and the share reading fires on none.
  Under the mean reading nothing runs on three of four models under either
  stem; the exception is qwen3-4b-instruct-2507 at m = 10 under the floored
  stem, which is the only rung on any model feasible under **both** readings.
  Under the registered stem nothing is feasible under either reading anywhere,
  because §12.4 already fails on vacuity. This is a preregistration defect and
  the choice is the researcher's.

Two read-only re-analyses of closed evidence landed with it and change what two
existing numbers mean without invalidating any row:
`dci1/reports/v3_reanalysis/` and `dci1/reports/pilot_reanalysis/`. The B+R
pilot's Δ = +0.34/+0.38 fails **two** independent checks. Under §17.4's
registered vacuity bound — every vacuous pass forced to a failure, no row
dropped — it is **+0.095** and **+0.068**, below the 0.10 generic-load
threshold, so §17.4's agreement rule puts the axis **unresolved with both
bounds**. (An earlier sensitivity analysis that tested vacuity by *restricting*
to ≥20-word responses reported it unmoved; that restriction drops 36% of one arm
and 0% of the other and is not the registered operation. It should not be
quoted.) Independently, its two cells are five-fold apart in response length and
overlap on 8–9% of one arm; at matched length the contrast is −0.057 and
−0.003. v3's Δ^A, the only same-topic registered
companion swap the study has executed, is +0.064 and +0.074 and **does** survive
length matching (+0.118, +0.059) with full common support — inside the
generic-load region of the registered thresholds and far from pair-specific.

Report: `dci1/reports/cal_screen_v4/REPORT.md`. Gate 1 remains the binding
constraint, and §12.4's reading now sits ahead of it.

### 4f. The pairwise-matrix screen: Δ_R is small, and three nuisance channels are larger (2026-08-20)

A fourth non-confirmatory screen (`dci1/src/matrix_screen_v4/`, per-model
protocol hashes frozen before generation) ran the **whole registered §8.1 cell
set** — five solo cells, ten unordered pairs in both orders — plus a V5
difficulty-spanning arm, a production-class companion arm and the §25
unconstrained cell, on 120 blocks (24 pre-screen + 96 solo) at M = 4 under the
floored stem, on all four models. 64,800 generations. **Intervals in this
section are 95% percentile unless stated otherwise; §4g reads the same
estimates on the simultaneous scale, which is wider and is the scale the
registered rules apply to. Where the two disagree — E2B's `Δ_R` excludes zero
on the percentile scale and includes it on the simultaneous one — the
simultaneous reading governs.** Its three references were admitted under
§13.2's conditions 1 and 3–6 on the 96 calibration topics with condition 2
applied where its registered one-draw §12.2 input exists; that is **not** the
registered Gate 3 admission, which has never run on any model, and under a
stricter reading of condition 2 the admitted set changes (on E2B to three
production-class families, which would make `Δ_R` a different quantity).
It estimates `Δ_R`, `Ξ`,
`D(R_j←A)` and the companion-difficulty relation, none of which any earlier
stage of this study had measured in this constraint vocabulary. The readings
were fixed in the report's §7b **before any cell was scored**.

- **Δ_R is small and, for the first time, resolved.** +0.048 [+0.009, +0.087]
  (E2B), +0.101 [+0.056, +0.146] (E4B), +0.011 [−0.020, +0.044] (qwen3-4b),
  −0.024 [−0.067, +0.019] (qwen3-4b-instruct-2507). Three of four lie entirely
  inside the ±0.10 equivalence band; E4B spans the 0.10 generic-load threshold
  and is unresolved at this precision. **None approaches 0.25.** Compliance and
  §17.4-forced scales agree on all four, so §17.4's rule licenses the reading
  instead of voiding it — the first axis in the study to pass that test, and it
  passes only because the floored stem holds calibration vacuity at 0.000–0.060.
- **Constraint class dominates companion identity by an order of magnitude.** A
  production-class companion costs B **+0.601** (E2B) and **+0.632** (E4B) where
  A costs +0.086 and +0.228; Δ_class = −0.515 and −0.404. A is the *gentler*
  production companion, five- to seven-fold.
- **Focal position dominates it too.** B loses **0.288** (E2B) and **0.350**
  (E4B) of its compliance purely by being stated second; A shows none. So Δ_R
  computed within a single order **changes sign on all four models** (E2B +0.326
  vs −0.231). §8.1's both-orders requirement is what makes Δ_R well defined, not
  a robustness nicety — and prior single-order estimates in this vocabulary are
  not comparable to a pooled Δ_R.
- **Companion difficulty does not account for A, and the length account cannot
  be tested here.** A sits above the difficulty line by **+0.067** (E2B) and
  **+0.118** (E4B) — identified, because A's solo compliance is inside that
  fit's support — and below it on both Qwens. A's *length shift*, by contrast,
  lies outside the range every other companion spans on all four models, so the
  length line extrapolates to A and its residual is **not identified**:
  companion identity and length shift are collinear across this companion set,
  the same collinearity the B+R pilot showed between its arms. (An earlier pass
  fitted both lines *through* A and reported the length residual as ±0.010,
  concluding length explained A entirely. That is withdrawn — see
  `CHANGES_SCIENTIFIC.md`.)
- **An admitted reference out-damages A on E2B.** The paired swap
  `Δ_1 = D(B←A) − D(B←CR6:7)` is **−0.078, simultaneous [−0.134, −0.023]**,
  entirely below zero: `D(B←CR6:7)` = +0.165 against `D(B←A)` = +0.086. (The
  two *marginal* intervals overlap — [+0.121, +0.207] against [+0.031, +0.143]
  — so the paired contrast is what carries this, as it should be; an earlier
  wording called them disjoint and that was wrong.) On E4B `D(B←RF2:8)` = +0.206
  against A's +0.228, and there the paired Δ_3 = +0.022 [−0.044, +0.088]
  includes zero. A is not the most
  damaging companion its own reference pool contains.
- **Ξ does not support pair specificity.** −0.036 and −0.009 on the Gemmas —
  A damages the references about as much as it damages B. Positive on the Qwens
  (+0.131, +0.090) only because A *improves* reference compliance there while
  `D(B←A)` is itself negative. §25 accidental compliance is 0.52–0.89 for the
  references against **0.000 for A**, so the reference side is near-ceiling.

The screen cannot confirm or falsify anything confirmatory: 120 blocks,
calibration topics, Gate 1 unapproved, `claim_licensed` `False` by construction.
What it does establish is that **class and position each move focal compliance
more than companion identity does, a pool reference out-damages A, and the
length channel is collinear with identity on this companion set and so cannot be
separated from it at any number of blocks**. A confirmatory design that does not
fix all of that would measure it instead.

Report: `dci1/reports/matrix_screen_v4/REPORT.md`. The four screens, the two
re-analyses and the resulting decision boundary are drawn together in
`dci1/reports/INVESTIGATION_2026-08-20.md`, superseded in part by §4g.

### 4g. The endpoint: a researcher decision boundary, and §13.2 is not part of it (2026-08-20)

**The registered v4 design cannot start.** §12.4 caps B's realised solo vacuity
at 0.10; on the registered 96 solo-calibration topics at `M_cal = 4` under the
registered prompt it is **at least 0.208 — and as much as 0.870 — at every
rung of the focal grid and of the extended grid, on all four models**. (The
per-model *minima* run 0.208 to 0.659; the range of values is wider.) Gate 2 returns `REGIME_NOT_FOUND` for
every replication before the reference question is reached, so **no confirmatory
evidence on the companion-identity question exists or is licensed**. §28.3 fixes
what that means: a terminal pre-confirmatory status carries no evidence about
the effect, and the status is about the registered grid, never the model.

**Gate 2 has deliberately not been run.** A terminal record is write-once and
disables every later generation command; adopting a design change afterwards
would be adopting it *because a gate failed*, which §31 prohibits. The
amendment decision has to come first, and the option is still open.

**§13.2 is resolved and is not a blocker** — the earlier claim that it is a
preregistration gap is withdrawn (§4e). Two things were completed that no
decision was waiting on:

- **§10.2 now holds for all eight registered family verifiers**, over the whole
  94-rung ladder: determinism 1.000 across 1,311,582 verdicts per process in 672
  processes, boundary agreement 1.000 on 45 authored cases per family,
  independent reimplementation 1.000. It was never blocked on the pool —
  RF1–RF8 are registered and Amendment B adds families rather than removing
  these. `dci1/reports/gate1_v4/section_10_2_families.json`.
- **It found a defect, in the validation instrument and not the instrument under
  study.** The prose-only reimplementation segmented on `[^\W\d_]+`, which
  admits 1,151 non-decimal numerics and is not §7.2's alphabetic class. On the
  genuine response `Answer: H₂O` it read one word where the primary reads three,
  taking RF3 with it — invisible on A and B, which is why it had survived. The
  primary agrees with the prose and is unchanged; the canonical verifier hash,
  every stored verdict and every estimate are unaffected, and A and B's §10.2
  line re-verifies at exactly 1.000.

**The three reserved topic sets are unspent**, audited over 285,936 generated
rows rather than over source: zero on Gate 4's 24 composed-validation topics,
zero on the confirmatory 384, sequestered text still hash-only.

**And a seventh channel, not previously recorded: §13.2's caliper matches on a
quantity that is not comparable across the production/budget divide.** §13.2
matches references to A on **raw** solo compliance; §25 separately measures how
often an *unconstrained* answer satisfies each constraint by chance, and does
not feed it into admission. Netting it out, `(solo − chance)/(1 − chance)`, on
the matrix screen's own reference sets: A's instructed compliance equals its
solo compliance on all four models (A's chance rate is **0.000** — an
exact-count production constraint is never satisfied by accident), while the
references run 0.04–0.63 and two are **negative**, meaning stating the
constraint makes the model satisfy it *less* often than not stating it.
**Twelve of twelve references are matched to A on solo compliance and two of
twelve on instructed compliance.** It is structural — every family is a
prefix-closed budget — and it biases `Δ_R` **upward**, so it runs against the
positive reading rather than producing it. Decidable from §25's registered
measurement with no new generation.
`dci1/reports/section_13_2_v4/instructed_compliance.json`.

**On the exploratory `Δ_R` itself, the registered rules are more conservative
than §4f's percentile reading.** On the simultaneous scale the §16.2 precision
precondition (half-width ≤ 0.05) is met on **one** model of four at 120 blocks,
and §13.4's heterogeneity qualifier **fires on both Gemmas** — on E2B one
reference's `Δ_j` interval lies entirely below zero. Full report:
`dci1/reports/ENDPOINT_2026-08-20.md`.

### 4h. v4r3: adopted, registered, and run to the regime screen (2026-08-21)

**Adopted and registered.** The researcher adopted DCI-1 v4 revision 3 on
2026-08-21 (`dci1/DECISIONS_V4R3.md` A0), and every study-wide rule is bound
into a signed manifest at `dci1/evidence/dci1v4r3/registration/`.
`user-notes/DCI1_preregistration_v4r3.md` is the protocol;
`dci1/src/dci1v4r3/` is its executable form;
`user-notes/DCI1_v4r2_to_v4r3_changelog.md` records twenty-four changes with
their evidence. Nothing registered under v4r2 has been changed by any of it.
**The correct designation is a revision, not v5**: v4r2 §31 makes a pre-freeze
change a revision, and v4r2 is unfrozen with no confirmatory data.

**Not frozen, and Gate 1 cannot pass without the researcher.** §10.4 ends in an
explicit approval writing `measurement_basis = autorater_calibration_approved`,
which the adoption withholds and which no agent may write. Everything before
that boundary has been executed.

**What it is for.** §4g leaves the study at a decision boundary with the
registered design unable to start. v4r3 takes the four screens' findings as
design evidence and rebuilds the identification of the companion-identity
question on three layers instead of one:

- **local matching**, `Δ_R` against three close companions — kept, but on a new
  coordinate;
- **a difficulty spectrum**, `δ_diff = D(B←A)` minus a family-aware line fitted
  over **nine** non-A companions straddling A from both sides, with A excluded
  from the fit that predicts A and no residual reported outside support;
- **reciprocal specificity**, `Ξ`, promoted into the primary family because it
  now decides whether an L3 statement may say "specific to B" at all.

This closes v4r2's registered open decision **V5** in favour of both matching
and spanning, at linear rather than quadratic cost — a spectrum companion pairs
with B alone, so the arm costs 18 cells rather than 90.

**The change that matters most is the coordinate.** §13.2 matched references to
A on **raw solo compliance**; §2.3(b) of the new document records why that
cannot work across the production/budget divide. A's chance rate is 0.000 and
the matched budget rungs' are 0.52–0.89, so twelve of twelve references are
matched to A on solo compliance and **two of twelve** on instructed compliance,
`(solo − chance)/(1 − chance)`. v4r3 registers instructed compliance as the
coordinate, keeps raw solo as a reported secondary with a full parallel fit, and
promotes §25's accidental compliance from an unused diagnostic to a registered
design input with its own load-zero cell in every block. It is the **harder**
criterion, not the convenient one.

**Two v4r2 defects are resolved and one limitation is made explicit.** §12.4's
graded clause is read as a **share** — the mean reading declares degenerate
exactly the severities §12.3 declares eligible, on every model under every
prompt. The focal grid **escalates** rather than widening, because a flat
extension moves m\* on a model whose registered grid already works. And because
the reference pool is budget class while A is production class,
`COMPANION_CLASS_NOT_MATCHED` attaches to **every** L3 statement with a fixed
sentence, with a one-companion class arm bounding how much that could matter.
The length account of A remains **not identified at any block count**, and
v4r3 says so rather than reporting an extrapolated residual.

**Cost.** 47 cells per block, 408 blocks, M = 4 — **306,816 generations across
four models**, twice v4r2's 153,600, with the sequestered set falling from 96
topics to 72 because a 624-question bank cannot supply both. The binding
constraint is `D`'s precision precondition once the primary family carries six
members. `dci1/tools/allocation_v4r3.py` reproduces v4r2's published §16.2 row
exactly under an executable assertion.

**State.** 127 new tests, `dci1` suite 831 pass against a 705 baseline. A
plan-only dry run walks §12.2 → §12.3 → Gate 2 → Gate 3 → the 47-cell plan →
the refitting bootstrap → §17.6's joint reading and generates nothing:
`dci1/reports/v4r3_dry_run.json`. Change map and blast radius:
`dci1/reports/v4r3_change_map.md`. **No confirmatory generation has been run
under any protocol version, and none is authorised.**

### 4i. v4r3 stage 3: the stem works, and the spectrum is identified on one model of four (2026-08-21)

The registered regime screen ran on all four models on the 24 pre-screen
topics — §12.1's cap, §12.2's 190-rung dense ladder, §12.6's expansion loop —
for **4,920–6,048 generations per model**. Report:
`dci1/reports/dci1v4r3/REPORT.md`.

- **§8.5's answer-length stem fixes the v4r2 blocker, on v4r3's own
  instrument.** B's realised solo vacuity over m ∈ {7,…,12} is **0.000, 0.000,
  0.000 and 0.042** against §12.4's 0.10 ceiling, where the v4r2 prompt
  produced 0.208–0.870 at every rung on every model. Completion cap 512
  everywhere, truncation 0.000 at every cap tested. The registered focal grid
  supplies an in-band pre-screen severity on three models; qwen3-4b needs
  §12.3's escalation, which is exactly the per-model behaviour §7.2 registered
  the escalation to produce.
- **§12.6's coverage criterion passes on gemma-3n-e2b-it and fails on the other
  three**, binding on C4 — four feature groups must contain a family straddling
  ι_A with three eligible rungs spanning 0.40. E2B has four; qwen3-4b has three
  (so the *spare* binds, not feasibility); E4B has one and
  qwen3-4b-instruct-2507 has two. The three record
  `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` **at design time** and run the reduced
  spectrum arm.
- **The reason is structural.** A character-budget family's ι curve rarely
  crosses ι_A with density on both sides: most families top out below it, the
  comma budget sits uniformly above it, and `b_initial` supplies no eligible
  rung at all on either Qwen in either predicate form.
- **The coordinate finding is the one that matters.** On the registered
  coordinate coverage passes on one model; on §13.3's *secondary* coordinate,
  raw solo compliance, it passes on **all four**. That is not an argument for
  switching. The rungs that sit above A on the raw coordinate carry mean chance
  compliance **0.635–0.728**, and 12–44 of them are **anti-productive** (ι ≤ 0
  — stating the constraint does not raise compliance above chance). A spectrum
  built on the secondary coordinate would have its upper arm made of
  instructions that do nothing. Across the whole measured vocabulary
  **31%–42%** of instances are anti-productive.
- **The class arm is difficulty-matched on all four models** — CL7:80, CL8:25,
  CL7:30, CL7:40, all inside §13.7's 0.15 caliper of ι_A — which v4r2 had no
  arm for at all. The rate lower bounds registered for that purpose appear
  among the matched candidates on three of four.
- **§10.4's autorater pathway is not ready, and the reason is the new pool.**
  The development phase ran on v4r3's own 22,968-item pool at concurrency one.
  Both registered conditions are exactly repeatable, and **neither survives
  criterion 2**: truncation 23/72 and 40/72 where the same `v4prompt-medium`
  configuration truncated **0 of 48** on the v4r2 pool of A and B alone.
  Truncation is absent on the outcome constraints and rises with how much
  counting the rule demands — rate lower bounds truncate 9/12 and 12/12 — so
  the judge exhausts its 2,048-token cap enumerating words to evaluate a rate.
  The repair is a further registered condition with a larger cap or a prompt
  that does not require enumeration; the single-shot freeze is unclaimed and
  the held-out half is hashed and never judged.
- **Gate 1: every §10.2 criterion passes and the gate still refuses.**
  Three-process determinism 1.000; 136 frozen boundary cases over 348
  instrument instances at 1.000; the prose-only reimplementation at 1.000; the
  segmenter differential at 1.000 over the whole Unicode range; 25,337 witness
  pairs with no failure; the wording suite clean; A's v3 carry-over intact. The
  recorded outcome is `MEASUREMENT_EVIDENCE_INSUFFICIENT`. Two things stand in
  front of it, in order: §10.4's criterion 2 above, and then the researcher's
  explicit approval, which no agent may write.

Nothing here licenses a claim about companion identity: no composed cell
exists, and none may exist before Gate 1.

### 4j. v4r3's repair pass: provenance, the stage machine, and §10.4-R (2026-08-21)

An evidence audit of the v4r3 state found four defects, three of them the same
shape — a rule the preregistration states in prose with nothing on the
execution path enforcing it.

- **The implementation was untracked**, so every v4r3 record named a producing
  commit that did not contain `src/dci1v4r3` at all, and §18's
  `tracked_implementation` and `clean_worktree` checks refused the study for
  exactly that reason. Committed; qualification now **PASSES** and binds.
- **There was no stage machine.** `STAGE_SEQUENCE` existed as a list of strings
  and nothing read it. That is how the §12.2 regime screen came to run before
  `QUALIFIED` and before `GATE_0_APPARATUS` — not by a decision, but because no
  guard existed to refuse it. `dci1v4r3/engine/transitions.py` now enforces
  in-order, once, terminal-is-terminal and §18.1's post-freeze rule against the
  predecessor's verified hash and signature, and logs every *attempted*
  transition including refusals. The existing screen evidence is recorded as
  `ADOPTED_OUT_OF_ORDER`, which does not satisfy any later stage's predecessor
  requirement: it is registered diagnostic evidence and the stage must be re-run
  in order under the bound commit.
- **§12.1's cap probe leaked a composed outcome.** The probe must generate
  composed `A + B` prompts — the cap has to be adequate where the answer is
  hardest to write — so 72 composed generations per replication went through the
  shared scorer and their rows carry `passed` for both constituents. Nothing read
  it and no record contained it, but `D(B ← A)` at `A:8 + B:7` was derivable from
  stored evidence. The probe is now projected onto §12.1's three registered
  fields before the cap decision sees it, a restricted durable artifact is what
  later stages read, and the selection modules are checked by parsing rather
  than by running that they cannot name the field at all.
- **The analysis stack did not exist.** `spectrum.py` and `claims.py` had nothing
  to feed them: no observation table, no estimators, no bootstrap, no masking.
  All four are now implemented and Gate 0 walks the whole chain end to end.

**§10.4 is replaced prospectively, not weakened.** Its original task asked the
judge whether a response obeys a rule; for a rate predicate that is an
enumeration, and the judge exhausted its 2,048-token cap doing arithmetic
without reaching a verdict. §10.4-R (C26, `DECISIONS_V4R3.md` A5) asks instead
whether the *operationalization* — segmentation convention, numerator,
denominator, derived quantity, direction, threshold, verdict — faithfully
implements the written instruction, with the arithmetic shown rather than
requested. **The deterministic verifier remains the study's scorer throughout.**
Half the judged cards carry one planted defect from a registered closed list of
six, because a validator handed a correct derivation and asked whether it is
correct can score perfectly by always agreeing; sensitivity has a registered
floor per defect kind as well as overall. Every threshold was registered at
commit `f657de2`, before any card was judged.

The original §10.4 evidence is retained. It is the record of why the amendment
exists, it judges a different question, and the two must never be pooled.

**§10.4-R ran, and failed four of five criteria — the amendment's own diagnosis
was wrong.** On 96 cards (48 faithful, 48 with one planted defect) against
thresholds registered before any card was judged: truncation **0.3125** against
a 0.10 threshold, parse validity 0.688 against 0.95, specificity **0.613**
against 0.90, sensitivity 0.771 against 0.80.

Truncation is *unchanged* from the original pathway's 0.319 at the same
reasoning effort. R1 argued the task was too much arithmetic; removing the
arithmetic changed nothing, because what binds is the reasoning chain the judge
emits — median output about 800 tokens against a 2,048 cap.

Two things the planted-defect arm made visible that an agreement check would
have hidden. **The judge recounted anyway**: twelve of thirty-one parsed
faithful cards were called incorrect, eight of them `A`, each justified "Wrong
count of however", against a prompt that says *do not recount, judge the
method*. And it is **blind to the wordless-answer rule**: `vacuity_ignored`
caught 0 of 5, with no justification offered, while `numerator_swap` and
`off_by_one` were caught 9/9 each — so the arm discriminates and the blind spot
is readable.

The two registered contingencies were not completed: `v4r-low` was stopped at
58 of 96 cards and no metric was computed from it, and `v4r-high` and the
8,192-token `v4r-medium-8k` were not run. Both address truncation; criteria 4
and 5 failed for reasons a larger cap does not touch. Researcher decision of
2026-08-21, recorded in `dci1/reports/dci1v4r3/section_10_4R_outcome.json`.

The strongest reading the evidence supports is not that the amendment needs
another turn of the crank, but that **an external LLM judge at this scale
performed neither version of the §10.4 task**: it would not do the arithmetic
when asked, and would not leave it alone when asked. `measurement_basis` stays
`human_validation_unavailable`; §10.3 remains the only untried registered
route, and no independent annotator exists.

### 4k. v4r3: R3 restores coverage, R2 fails, and Gate 1 is blocked on §10.3 alone (2026-08-21)

Two amendments, both registered before the evidence they govern existed, and
one of them worked.

**§7.0-R3 (C27, DECISIONS A6) restored the difficulty coordinate's support.**
Six counted statistics, six feature groups, a fifth predicate form and ten
families join the candidate library; no criterion, caliper or admission rule
moves. All four regime screens now pass §12.6's coverage criteria at **round
zero** — ι_A of 0.556, 0.667, 0.750 and 0.625 — where before R3 the machine-checked
counterfactual fails C4 on all four, with 3, 3, 3 and 1 well-formed straddling
groups against 4 required. Leave-one-out shows C4 with **zero spare capacity**
on three of the four, and `RF11` load-bearing on three.
`dci1/reports/dci1v4r3/candidate_landscape.json`.

**§10.4-R2 (C28, DECISIONS A7) failed its own criterion 5, and the
LLM-validator pathway stops.** The microcase audit fixed what it set out to
fix — truncation 0.3125 → 0.0119, parse validity 0.6875 → 0.9881, specificity
0.613 → 0.9125, overall sensitivity 0.771 → 0.8140 — and then failed on a floor
no earlier version had reached: per-kind sensitivity **0.231 on
`denominator_swap`** against 0.50. Seven of the ten items that decide that kind
have answers with no words at all, so their verdict turns on §7.3's
wordless-rate rule, which the deciding arm deliberately withholds; the same
cases in the conventions arm agree 9 of 11. The registered contingencies
`mc-high` and `mc-low` were not run, because raising reasoning effort cannot
supply a convention a prompt does not state, and the calibration half is
untouched. `DECISIONS_V4R3.md` A8,
`dci1/reports/dci1v4r3/section_10_4R2_outcome.json`.

**Twenty-five human annotations exist and are not §10.3.** Blinded microcases
over eight of the ten families R3 added, 23/25 agreement, no UNSURE, both
disagreements at severity 1 and both coinciding with the `inequality_flip`
reading; neither is a verifier implementation error — the primary and the
independent reimplementation agree on both. They are **human semantic
evidence**, not registered independent human validation: the annotator is the
researcher, the unit is a microcase rather than a natural response, one packet
is not min(150, N_c) per verifier class, and the Wilson bound is 0.2152 against
0.10. Twenty-five items clear 0.10 only at zero disagreements (0.0977, against
0.1013 at twenty-four), so the two disagreements are what fail it.

**A defect-sensitivity diagnostic sizes each semantic choice.** Over 30,720
real load-0 and load-1 responses and 27,840 stated verdicts per reading:
`inequality_flip` changes 95.5%, `denominator_swap` 21.8% (rate shift +0.163),
`numerator_swap` 32.8%, `off_by_one` 11.1% overall but **71% of exact-count
verdicts**, `segmentation_drift` 1.5% — every single change in `CR6` — and
`vacuity_ignored` **zero**. The last is the load-bearing one: natural-response
agreement cannot validate the vacuity convention, because the case that would
distinguish the readings does not occur. Absence of a natural counterexample is
not a passed test, and it is very likely why §10.4-R's judge scored 0 of 5
there. `dci1/reports/dci1v4r3/defect_sensitivity.json`.

**A signing defect had made every transition out of `REGIME_SCREEN` illegal.**
`canonical_json` sorts integer dict keys numerically and string keys
lexicographically; §12.2's payload carries `completion_cap.table`, keyed by
completion cap, so all four regime records failed `verify_signed` with no
tampering anywhere. Gate 1 could not have written a stage record even had its
measurement basis been licensed. Fixed on the writing path, the eight files
re-sealed under proof, and a regression test added.
`dci1/reports/dci1v4r3/record_signature_repair.json`.

**A §10.3-shaped audit now exists for the author to run.**
`tools/v4r3_human_audit.py` freezes 300 natural responses into 12 blinded
batches of 25 — 150 pass, 75 fail-at-margin-one, 75 fail-at-larger-margin,
seeded round-robin over 212 distinct instruments, all four models and all six
predicate forms, plan hash `08a9cbbf`. All three §10.3 bounds are reachable at
zero disagreements. It is
`author_performed_human_validation` by construction and cannot write a
measurement basis; `DECISIONS_V4R3.md` A9 records the six choices §10.3 leaves
open and how each was fixed before the first item was drawn.

**And a faster route to trusting the verifier itself.**
`tools/v4r3_verifier_audit.py` builds 128 §10.4-R operationalization cards —
the instruction, the answer, the word list, *the tokens the numerator matched*,
the arithmetic, the predicate, the verdict, and what each of the six registered
misreadings would have recorded. The question is "did this count the right
things?", answerable in seconds, rather than "what is the right label?", which
means counting a hundred words by hand. The matched tokens are decided by the
registered statistic itself and the decomposition declares itself unfaithful
rather than guess. It covers all 32 numerator-and-form pairs, eight phenomena,
both margin classes and five of the six misreadings — the sixth,
`vacuity_ignored`, discriminates on no natural response at all. Output is a
defect worklist, never an agreement rate; `DECISIONS_V4R3.md` A10.

**The card audit ran, and the verifier came through it.** 128 of 128
derivations assessed correct, zero wrong, zero unsure, at card set `ad0a2a55`.
All five misreadings that discriminate on natural responses were on the
displayed surface and none was objected to. Its structural limit is stated
rather than glossed: 1,741 matched tokens against 18,130 units, so a wrongly
*included* token is visible and a silently *omitted* one is not.

**What it surfaced is a construct question, not a defect.** Fourteen cards
showed bare `t` and `s` tokens inside matched lists, which is §7.3 working as
registered — a word is a maximal run of Unicode category L, so `don't` is `don`
and `t`. Measured against a reader's word
(`dci1/reports/dci1v4r3/lexical_footprint.json`): the rate denominator inflates
by **1.67%**, **1.10%** of verdicts change — *detectable*, below §11.8's
smallest effect of interest — and it concentrates in the one-letter families
`CR3` (7.9%) and `RF3` (6.9%), because `don`+`t` manufactures a one-letter word
no reader sees. Both are on live reference shortlists. §10.5's third question,
which the preregistration does not resolve; nothing is changed and nothing
proposed. `DECISIONS_V4R3.md` A11.

**Gate 1 under the original rule: `GATE_1_BLOCKED_MEASUREMENT`.** Every §10.2
prerequisite passes at the R3 verifier hash `41edc84c` over all **584**
instruments — three-process determinism 1.000, 164 boundary cases 1.000,
independent reimplementation 1.000 over 16,604 responses and 700,800 verdicts,
one segmenter-differential splitter, 92,988 witness pairs, 46,720 wording
verdicts, reserved sets unspent. Neither pathway §18 stage 4 then required had
completed: §10.4 closed by its own stopping rule and §10.3 has no independent
annotator. That record stands, unrewritten, at
`dci1/reports/dci1v4r3/gate1_decision.json`. §10.7-R5 below changes the rule
Gate 1 is decided under; it does not change what this one recorded.

**Why the §10.4-R2 failure means less than it looked like.** R2 runs both arms
over the same cases, and the conventions arm states §7.3's rules identically
for every case, so it carries no per-case information. The arm difference is
convention-access with judge, configuration and items held fixed. Agreement on
answers containing words: 0.929 → 0.943 (+0.014). On answers containing **no
words at all**: 0.231 → 0.692 (+0.462). The judge is not failing to count — the
exact-count form, the most arithmetic-heavy, scored 1.000. It is failing to
guess a stipulation. §10.4-R2 names that exact hazard and assigns
`segmentation_drift` and `vacuity_ignored` to the conventions arm for it, then
assigns `denominator_swap` to the instruction-only arm although 8 of its 14
deciding items have wordless answers — and `denominator_swap` is the kind that
failed criterion 5. This does **not** re-score R2, which failed under its
registered arm assignment and stops. Only the interpretation changes.
`DECISIONS_V4R3.md` A12, `dci1/reports/dci1v4r3/validator_diagnosis.json`.

### 4l. §10.7-R5 replaces Gate 1's measurement criterion, and the amended gate fails on a wording

**The amendment.** §18 stage 4 required *§10.2 plus §10.3 or §10.4*. It now
requires *§10.2 plus §10.7-R5 A–E*: a specification audit, deterministic
implementation validation, independent reimplementation, adversarial/boundary/
**mutation** validation, and provenance/hash binding — ten conditions, none of
them a reviewer-agreement threshold. §10.3, §10.4, §10.4-R and §10.4-R2 are
reclassified **supplementary/diagnostic**; their outcomes stand and neither is
described as having succeeded. Adopted before Gate 2, before any freeze, with
all four replications at `REGIME_SCREEN` and no estimand computed.

§31's objection — that an amendment is never used to weaken a criterion to make
a gate pass — is registered inside the amendment rather than answered around
it. What is offered against it is checkable: the basis R5 creates is not
`human_validated`, so §10.5's scope sentence attaches permanently and question
2, *can an independent human reproduce it?*, stays unanswered exactly as
before. R5 changes whether the study executes, not what it may assert.

**The amended gate returns `SPECIFICATION_AMBIGUOUS`.** Nine of ten conditions
pass: 32 families and forms carry a complete specification whose **recorded
predicate is executed** and reproduces the verifier at every severity of every
declared range; mutation validation exhibits a separating case for every
meaningful reading, with 0 undetected and 0 contradictions; the §10.2 evidence
above satisfies conditions 3–5 and 7; the verifier hash `41edc84c` and the new
wording hash `0f8a162e` bind; provenance verifies.

Condition 8 fails. Two of the four wordings of `CP4` and `CP7` state the
severity as a **target and name no bound** — *"Give {q} percent of words
doubled letters"*, *"Make {q} percent of words carry letter a"* — so the prose
does not distinguish the registered `>= q` from an `== q` reading. The two
readings agree at `q` and disagree on every answer past it, where the verifier
records a pass: a one-sided leniency in the *treatment*, which no amount of
§10.2 evidence could have found. The other 124 wordings name their direction,
and the `q = 1` plural mismatch (*"Exactly 1 semicolons…"*, 45 wordings) is
classified awkward-but-unambiguous and does not block.

Two remediation paths, neither taken here: correct the four wordings and
regenerate the **768** regime-screen rows taken under them (192 per model, 2.7%
of the screen), or remove `CP4` and `CP7` from the vocabulary under §10.2's
registered removal rule at no regeneration cost — both are class-control
families and `CL7`/`CL8` pass intact. `DECISIONS_V4R3.md` A14,
`dci1/reports/dci1v4r3/gate1_r5_decision.json`.

### 4m. v4r4: v4r3 closes at Gate 1, and a revision whose Gate 1 is deterministic passes it (2026-08-21)

**v4r3 is closed, not rescued.** Its registered §18 stage 4 required §10.2 plus
§10.3 or §10.4. §10.3 had no independent annotator; §10.4, §10.4-R and §10.4-R2
each failed their own registered criteria. Under §10.7-R5, adopted as an
amendment inside v4r3, the gate then blocked on a wording (§4l). The terminal
state is `GATE_1_MEASUREMENT` / `MEASUREMENT_EVIDENCE_INSUFFICIENT`, and it
stands: `dci1/reports/dci1v4r3/closure.json` records it, hashes the six reports
it rests on and the 22 stage records, and edits nothing —
`closure_hash 930720a0`. No v4r3 file was rewritten to reach v4r4, and a v4r3
stage record cannot satisfy a v4r4 predecessor check: `assert_own_study` raises
on the `study_id`, and the refusal is performed rather than asserted in
`dci1/reports/dci1v4r4/lifecycle_integrity.json`.

**v4r4 is a prospective revision, and §31's designation test is what makes it
one**: a pre-freeze change to an unfrozen protocol with no confirmatory data is
a revision. `user-notes/DCI1_preregistration_v4r4.md` incorporates v4r3's by
reference and changes four things, enumerated in
`user-notes/DCI1_v4r3_to_v4r4_changelog.md` and machine-readable in
`dci1v4r4.protocol.revision.DIFFERENCES`:

- **R4-1 — Gate 1's criterion is deterministic by construction.** §18 stage 4
  is §10.2 plus **§10.7 A–E**: specification validity, implementation validity,
  independent reimplementation, adversarial/boundary/**mutation** validation,
  provenance binding. Ten conditions, none a reviewer-agreement threshold.
  §10.3/§10.4 artifacts travel as labelled diagnostics that can move no gate in
  either direction; `gate1_payload` refuses `human_validated`,
  `autorater_calibration_approved` and `human_validation_unavailable` *before*
  it reads any evidence.
- **R4-2 — `CP4` and `CP7` are removed** under §10.2's registered removal rule,
  taking the vocabulary from 30 families to **28** and the instrument
  population from 584 to **524**.
- **R4-3 — the prose-to-predicate invariant (§10.7 A′)** is a Gate-1 condition:
  every model-facing wording must expose the comparison direction of the
  predicate that scores it, by naming an operator from a registered lexicon or
  by a construction registered as entailing one. A target quantity with no
  operator fails.
- **R4-4 — evidence crosses the revision boundary only through a ledger**
  (§26-R4), and the measurement basis v4r4 can write is
  `deterministic_measurement_validated`.

**What the revision does not buy.** The basis is not `human_validated`, so
§10.5's scope sentence attaches permanently to every analysis record under it:
*the outcomes are verifier-defined and support no claim about compliance as an
independent human would judge it.* §10.5's second question — would an
independent human reproduce these verdicts? — is exactly as unanswered in v4r4
as in v4r3. R4-1 changes whether the study executes, not what it may assert,
and §31-R4 registers the objection rather than answering around it.

**`CP4`/`CP7` were resolved before Gate 1 ran and without reading a composed
outcome.** The analysis reads only the §12.2 pre-screen difficulty table on the
four regime records — solo compliance, chance compliance, solo vacuity. §12.6's
C1–C6 read rows whose role is `reference` and both families are
`class_control`, so removal *cannot* move them; that is a property of the
criterion, and the run confirms it rather than resting on it. C7 holds on all
four models, ι_A moves on none, and `no_condition_changed_on_any_model` is
true. The alternative remedy — reword and regenerate — would have cost 1,536
generations, which is recorded because a reader is entitled to see it and
explicitly did not enter the decision.
`dci1/reports/dci1v4r4/cp4_cp7_analysis.json`, `DECISIONS_V4R4.md` B3.

**Gate 1 returns PASS on all four replications**, with all ten conditions met.
`dci1/reports/dci1v4r4/gate1_decision.json`, decision hash `df630dec`:

- **determinism** 1.000 across 3 processes over 400 responses and 524
  instruments, identical digests;
- **independent reimplementation** agrees exactly — `per_instrument_min` 1.000
  over **628,800 verdicts** on 36,164 responses, with 650,952 per-response
  statistic comparisons and a segmenter differential over the whole
  1,114,112-codepoint space (one case-folding splitter, `U+0130`, and it is
  named);
- **boundary/adversarial/Unicode** 164 cases, 85,936 verdicts, zero failures;
  **witnesses** 92,148 satisfiability and non-entailment pairs;
- **specification audit** 30 kinds — the 28 families plus A and B — across
  5 predicate forms complete, the recorded
  predicate executed and reproducing the verifier at every declared severity,
  0 ambiguous, 0 uncovered;
- **mutation validation** exhibits a separating case for every meaningful
  reading of every family: `inequality_flip`, `numerator_swap` and `off_by_one`
  30/30; `segmentation_drift` 22/22; `vacuity_ignored` 17/17;
  `denominator_swap` 12/12 — **0 undetected, 0 contradictions**, and every
  non-applicability carries a mechanical reason;
- **wordings** 2,141 classified: 2,040 explicit, 56 by the one registered
  construction, 45 awkward-but-unambiguous (the `q = 1` plural, §4k), **0
  genuinely ambiguous and 0 requiring correction**;
- **hashes bind**: verifier `09f0675c`, wordings `b9b258c5`, specification
  `1704ddc3`, mutation `a91f6220`, protocol `1e7a7b2d`;
- **provenance** verifies on all four models — predecessor `REGIME_SCREEN`,
  signature verified, reserved sets unspent, no prior Gate-1 record.

**Evidence is carried, and every derived quantity is recomputed.** The pilot
and regime-screen *generations* cross from v4r3 as
`RECOMPUTED_FROM_EXISTING_RAW_DATA`; verdicts, the §12.2 table, coverage and
the shortlist are computed again under v4r4's verifier hash. The two invariants
that could have made that illegitimate are measured, not asserted: both
packages' predicates agree on **85,936** verdicts, and **42,240** constraint
sentences stored on carried rows are byte-identical to the wordings v4r4
renders. Six v4r3 artifacts are `HISTORICAL_ONLY`, two `NOT_APPLICABLE`, and
**nothing is `INVALIDATED_AND_REGENERATED`** — because R4-2 removed the two
families rather than rewording them, so v4r4 declares no instrument their rows
could score. `dci1/reports/dci1v4r4/evidence_reuse_ledger.json`, hash
`f68f528f`.

**Coverage holds on all four models at round zero**, no expansion:

| model | ι_A | eligible reference rungs | families | C4 groups | nearest class candidate |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.5556 | 67 | 18 | 4 | `CX1:1` |
| gemma-3n-e4b-it | 0.6667 | 69 | 18 | 5 | `CL7:80` |
| qwen3-4b | 0.7500 | 73 | 18 | 4 | `CX1:5` |
| qwen3-4b-instruct-2507 | 0.6250 | 46 | 17 | 4 | `CL7:45` |

`dci1/reports/dci1v4r4/coverage.json`.

**Two researcher decisions were taken on the record and neither moved a
threshold.** **B6** accepts the requirement-verb construction, so *"Your answer
needs {q} words with letter a"* reads as `≥ q` and the 1,536 rows behind
`CL7`/`CL8`'s fourth templates are not regenerated; the derivation and every
affected wording are in `wording_review.json` because this is the class of
finding a reader should be able to disagree with. **B7** declines to invoke
§12.6's registered candidate expansion: C4 passes as registered, and widening
the pool because a passing solution has no spare margin would be an adaptive
choice made after seeing a coverage result.

**The limitation B7 preserves instead.** C4 is identified but **fragile on
three models**: `gemma-3n-e2b-it`, `qwen3-4b` and `qwen3-4b-instruct-2507`
satisfy it with exactly four well-formed straddling feature groups, so every
one is load-bearing and there is no leave-one-family-out margin.
`gemma-3n-e4b-it` has five and is robust. The same sweep on v4r3's 30-family
population returns the same families, so R4-2 did not cause it — it is a
property of the reference pool the study has had since §7.0-R3. Any Gate-3 or
Gate-4 result on those three models is conditional on all four groups holding.

**Three further limitations, recorded on the artifacts themselves.** A carried
Gate 0 runs every §19 check under v4r4's code except the backend call itself,
and the stage record says so. Carried rows are reproducible from v4r3's seed
schedule, not v4r4's, because the seed domain carries the study id; every carry
note counts the divergence. And nine adversarial corpus classes — zero-width,
soft hyphen, combining mark and six others — are exercised by the frozen corpus
but never observed in a real generation, so their verifier behaviour is tested
and not sampled.

**One consequence of taking B6 and B7 after the gate.** `DECISIONS_V4R4.md` is
a protocol document, so entering them moved the protocol hash away from the
`1e7a7b2d` Gate 1 sealed. That is the binding working, and it is recorded
rather than absorbed: no record was rewritten and no gate re-run.
`dci1/reports/dci1v4r4/register_amendment.json` carries both protocol hashes,
shows the register was the **only** document that moved, and shows that the
verifier, wordings, specification, mutation and measurement-rule hashes are
byte-identical to what the gate certified.

**State.** `dci1/evidence/dci1v4r4/` holds four signed records per model
through `GATE_1_MEASUREMENT`, mirrored to `dci1/durable_root/`; lifecycle
integrity passes with `problems: []`, and the integer-key canonicalisation
defect that broke v4r3's regime signatures (§4j) is reconstructed and shown
fixed. Assembling the checkpoint also exposed a defect in the integrity tool
itself: the durable-mirror check looked one directory too deep, then forgave
itself for finding nothing, so it compared zero bytes on all 16 records while
reporting `passed`; and §18 stage 1's qualification command never mirrored at
all, leaving four signed records with one copy under a gitignored directory.
The checker now fails closed, `cmd_qualify` mirrors on every run, the four
records were replicated byte-verified, and two tests hold it there. **No
freeze, no confirmatory generation, no estimand computed.** Gate 2 is licensed
and is the next stage: 62,976 calibration generations across the four
replications, on the 96 solo topics. `dci1/reports/dci1v4r4/`,
`dci1/DECISIONS_V4R4.md`.

### 4n. v4r4 Gates 2 and 3: all four replications pass, and the spectrum is identified on one (2026-08-22)

**What ran.** 62,976 registered calibration generations plus 768 from §7.2's
conditional extension, on the 96 solo topics at `M_CAL = 4`, across both RX
7900 XTXs as two independent TP=1 lanes. Then §13's selection, which reads that
table and nothing composed.

| model | n\* | m\* | ι_A | calibration rows | §7.2 extension |
|---|---:|---:|---:|---:|---|
| `gemma-3n-e2b-it` | 1 | 10 | 0.574 | 16,128 | no |
| `gemma-3n-e4b-it` | 4 | 10 | 0.695 | 14,976 | no |
| `qwen3-4b` | 2 | **12** | 0.702 | 16,896 | **yes** |
| `qwen3-4b-instruct-2507` | 5 | 10 | 0.596 | 15,744 | no |

| model | design | cells/block | core refs | spectrum | statuses beyond `COMPANION_CLASS_NOT_MATCHED` |
|---|---|---:|---:|---:|---|
| `gemma-3n-e2b-it` | **full** | 47 | 3 | 6 | — |
| `gemma-3n-e4b-it` | reduced | 8 | 0 | 0 | `EXCESS_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` |
| `qwen3-4b` | reduced | 8 | 2 | 0 | both |
| `qwen3-4b-instruct-2507` | reduced | 8 | 0 | 0 | both |

`gemma-3n-e2b-it`'s three references are `RF9:10` (t_initial), `CR5:2` (comma)
and `RF11:26` (vowel_initial), each straddling A with a spectrum pair.

**The difficulty spectrum is identified on one replication of four, which is
what the v4r3 screen found at screen scale (§4i).** The unifying cause is
**local sparsity of the eligible reference pool immediately above ι_A**, and it
arrives by three different routes:

- `gemma-3n-e4b-it` — the rungs nearest ι_A carry high chance compliance, so
  they match A on ι and miss it on raw solo compliance. `RF9:13` sits at
  ι 0.704 against A's 0.695 with solo 0.857 against A's 0.727, and §13.4's
  Newcombe interval `[0.148, 0.343]` does not intersect ±0.05. The one admitted
  family then cannot straddle. `RF11:26` was a near-exact ι match (0.699) and
  failed §13.4 condition 2 at pre-screen distance 0.197 > 0.15.
- `qwen3-4b` — `RF11` and `CR5` are both admitted and both straddle, and §13.4
  wants three *feature groups*. `RF2:6` is the near miss: ι 0.696 against
  A's 0.702, solo 0.945 against A's 0.719.
- `qwen3-4b-instruct-2507` — a gap in the ladder. Its 16 eligible rungs run
  0.122 → 0.592 and then jump to 0.722, so nothing lies within the 0.10 caliper
  above ι_A = 0.596; `RF7` is admitted at 0.592 and its other eligible rungs
  (0.365, 0.426, 0.464) are all below A, so it cannot straddle.

**Coverage passed at pre-screen and did not survive re-measurement.** §12.6's
C1–C7 are assessed on the 24-topic pre-screen; §13.4 admits on the 96-topic
calibration split. Three of four models met C1–C6 at pre-screen and then failed
to yield three straddling families on the larger, disjoint sample. That is the
C4 zero-margin finding of `DECISIONS_V4R4.md` B7 arriving one stage later with
teeth, and no threshold was moved in response — §12.6's registered expansion
was not invoked and no caliper was widened.

**`qwen3-4b` sits on the last rung of the extended focal grid.** m\* = 12 is
the maximum of `FOCAL_GRID + FOCAL_EXTENSION`. Its B curve is
{7: 0.031, 8: 0.107, 9: 0.245, 10: 0.411, 11: 0.659, 12: 0.742}, so 11 and 12
are the only rungs inside `FOCAL_BAND = (0.60, 0.95)`. Had B:12 also fallen
below the band the replication would have recorded `FOCAL_RANGE_EXHAUSTED`.
There is no headroom above the selected severity on that model.

**Executing these stages for the first time found seven defects, all of one
class.** A reader with no producer: code reading a key, an attribute or an
exception class that nothing on the path actually writes or raises. Gate 2
asked `cell_rates` for keys it does not return and crashed after 16,128
generations; §7.2's escalation flag had three readers and no writer, so the
extension was unreachable and `qwen3-4b` would have gone terminal on a rung the
protocol registers; `design_variant_for` read an attribute `SelectionResult`
does not have and assigned every replication the reduced design whatever Gate 3
had selected; and `stages/gates.py` declared its own `TerminalStatus`, unrelated
to the one the stage driver catches, so a Gate 2, 3 or 4 terminal would have
escaped as a traceback with no terminal record written. The first four Gate-3
records were superseded through the registered restart mechanism at `7eb1947`
and are retained at `evidence/dci1v4r4/<model>/superseded/7eb19472dfc4/`; they
are predecessors of nothing. `CHANGES_SCIENTIFIC.md`, 2026-08-22.

**One test fixture had encoded a defect as the expected behaviour.**
`FakeSelection` carried `core_references` as a plain attribute, which is what
the `getattr` call wanted and not what `SelectionResult` has, so three tests
asserted the wrong variant and passed. Repaired to use the certified object.

**State.** Six signed records per model through `GATE_3_REFERENCES`, mirrored
byte-for-byte to `dci1/durable_root/`; lifecycle integrity passes with
`problems: []`; the four Gate-3 records reproduce exactly under the current code
from their sealed Gate-2 inputs. The reserved topic sets — composed,
confirmatory, sequestered — are still unspent, audited over every `rows.jsonl`
in both roots. Gate 4 is next: §13.10's composed-headroom predicate on the 24
reserved composed topics at `M_CAL = 4`, 4,512 generations for the full design
and 768 for each reduced one, 6,816 in total. It is the first stage that
composes two constraints in one prompt. **No freeze, no confirmatory
generation, no estimand computed.**


### 4o. v4r4 Gate 4: the composed-headroom predicate ends two replications, one of them the only full design (2026-08-22)

**§13.10, run exactly as registered.** Every registered cell type of each
replication's own design, on the 24 reserved composed-validation topics, at
`M_CAL = 4`, each cell's compliance rate evaluated independently against
`[0.05, 0.95]` for each of its constraints. 6,816 generations: 4,512 for the
47-cell design and 768 for each 8-cell one. It is the first stage that composes
two constraints in one prompt and the first that spends a reserved topic set.

| model | design | cells | rows | outcome |
|---|---|---:|---:|---|
| `gemma-3n-e2b-it` | full | 1,128 | 4,512 | **TERMINAL — `COMPOSED_HEADROOM_FAILURE`** |
| `gemma-3n-e4b-it` | reduced | 192 | 768 | PASS |
| `qwen3-4b` | reduced | 192 | 768 | PASS |
| `qwen3-4b-instruct-2507` | reduced | 192 | 768 | **TERMINAL — `COMPOSED_HEADROOM_FAILURE`** |

**What failed, recomputed from the raw scored rows rather than read off the
record.** Each rate below is 96 observations over 24 topics at M = 4, balanced,
so the flat mean and the topic mean coincide.

| model | cell | slot | rate |
|---|---|---|---:|
| `gemma-3n-e2b-it` | `pair:B+R3` | B | 0.9583 |
| `gemma-3n-e2b-it` | `pair:B+R3` | R3 | 0.9688 |
| `gemma-3n-e2b-it` | `pair:B+R3+` | R3+ | 1.0000 |
| `gemma-3n-e2b-it` | `pair:R3++B` | R3+ | 1.0000 |
| `gemma-3n-e2b-it` | `pair:R3+B` | R3 | 0.9583 |
| `qwen3-4b-instruct-2507` | `solo:CL` | CL | 0.9896 |

`R3` is `RF11:26` and `R3+` is `RF11:32` — the vowel-initial family, whose
chance compliance is high, so its ι sat inside the eligibility band on the 96
solo calibration topics (0.633 and 0.679) while its **raw** compliance on the
composed set is at the ceiling. §13.10 checks the raw rate, and a constraint
that is nearly always satisfied has no room to register interference.
`qwen3-4b-instruct-2507`'s failure is one cell: its class companion `CL8:3` at
0.9896 solo. Both are ceiling effects on a **companion**, not on an outcome
constraint.

**Nothing was revised in response, because §13.10 forbids it.** "Gate 4 runs
after the spectrum and the class companion are already fixed, and its outcomes
never revise them. A headroom failure is a terminal status for the replication,
not an instruction to choose different rungs." No reference was replaced, no
family added, no caliper widened, no rung re-chosen. Both terminal records are
signed, mirrored, and carry the §28.3 sentence; every later stage is
mechanically disabled for those two replications, and `assert_predecessor_passed`
refuses Gate 5 on them by name.

**The scientific consequence, stated plainly.** The difficulty spectrum was
identified on one replication of four at Gate 3, and that replication is the one
Gate 4 ended. **No surviving replication identifies a spectrum-dependent
quantity.** The confirmatory study is two reduced-design replications —
`gemma-3n-e4b-it` and `qwen3-4b` — estimating D(B←A), D(A←B), Λ and Δ_class.
`delta_difficulty`, Ξ, Δ_R, Δ_j and every D(B←R_j) are `NOT_IDENTIFIED` for the
study as a whole, not merely unresolved. §13.8 withholds L3a–L3e accordingly.

**The confirmatory budget, recomputed from the signed records.** 8 cells/block ×
384 blocks × M = 8 = **24,576 generations per replication, 49,152 in total**.
The ~577k figure that appeared in earlier planning assumed four replications on
the 47-cell design; neither the count nor the design survived Gates 3 and 4, and
`reports/dci1v4r4/prefreeze_audit.json` records the superseded estimate beside
the recomputed one rather than dropping it.

**Precision, projected at the registered variance model.** T = 384, M = 8. At
the worse φ = 0.37 and the largest registered Šidák constant (k = 6): D 0.0452
against a 0.05 precondition, Λ 0.0639 against 0.08, Δ_j 0.0452 against 0.06.
`Delta_R` and `delta_difficulty` carry preconditions that do not apply, because
the surviving design does not identify them. The v4r2 §16.2 published row
reproduces from the same formulas to four decimals, so the model has not
drifted.

**The masked phase protects less on this design, and now says so.** §8.6's
8-cell block gives B exactly two companions (A and the class companion), so
D(B←A), D(B←CL) and Λ are masked among two; A's and CL's only companion is B,
so D(A←B) is analysed with its companion identity visible. §20-R4's stratified
permutation already handled the arithmetic — an independent permutation would
move a label with probability exactly 0.5 on this design and fail the mask's own
effectiveness check about half the time by chance. The declaration that travels
with every masked record asserted the full-design case unconditionally and was
false here; it states both cases now.

**Gate 4 also found the last of the reader-with-no-producer defects, and one of
them is why there is a terminal record at all.** `stages/gates.py` declared its
own `TerminalStatus`, unrelated to the class `_run_stage` catches, so a
`COMPOSED_HEADROOM_FAILURE` would have escaped as an unhandled traceback with no
terminal report written and no transition logged. It was fixed before Gate 4
ran, on a path that had never executed, and two replications used it within the
hour. Six further defects — five §18.1 fields with readers and no producer,
§26's durability gate with no caller, and a durable-mirror path where two
artifacts collided — are in `CHANGES_SCIENTIFIC.md` for 2026-08-22.

**State.** `reports/dci1v4r4/prefreeze_audit.json` reconstructs the final design
from signed records alone and reports `can_freeze: true`: signatures and durable
mirrors verify on all 26 stage records, §26's durability gate passes with its
stated single-device limitation, the confirmatory and sequestered topic sets are
untouched, and the recomputed budget is 49,152. Gate 5 is next, for two
replications.


### 4p. v4r4 confirmation: two replications freeze, generate, mask, unmask and analyse — and they disagree (2026-08-22)

**Gate 5 froze both survivors at `450a049`**, binding all 66 §18.1 fields.
Five of those fields had readers and no producer and accepted `"-"` as a
value; `tools/v4r4_backend_provenance.py` now produces them from the backend's
own sidecars. §8.6's reduced design could not freeze at all — three fields it
legitimately leaves empty were read as missing — until `VARIANT_EXEMPTIONS`
tied each exemption to a declared identification status. §26's durability gate,
which had no caller, is now wired into `run_freeze`.

**Confirmatory generation: 24,576 rows per replication, 49,152 in total.**
Complete on both — zero missing, duplicated or out-of-plan identities, 3,072
distinct prompts, 24,576 distinct scientific seeds, no empty output and no
processing failure. Truncation 6 rows on `qwen3-4b` and 1 on
`gemma-3n-e4b-it`. `assert_generation_licensed` had demanded a field §18.1 does
not register, so no freeze could license any generation; the path had never
run, and the test fixture carried the same non-existent name.

**Masked → unmask → final, once each, under one analysis code hash.**
`dffb5a86…` is sealed into both masked artifacts, which is what makes the two
replications comparable. Every point estimate below was independently
recomputed from raw `scored.jsonl` with no estimator and no bootstrap, and
reproduced to four decimals.

| | qwen3-4b, outcome_first | qwen3-4b, outcome_second | e4b, outcome_first | e4b, outcome_second |
|---|---|---|---|---|
| D(A←B) | **+0.392** | **+0.329** | **+0.116** | −0.032 |
| D(B←A) | −0.123 | −0.012 | +0.006 | **+0.283** |
| Λ | −0.515 | −0.341 | −0.110 | +0.315 |

**The two replications disagree qualitatively.** On `qwen3-4b` the loss falls
on A in both configurations and is large; B is undamaged and in `outcome_first`
gains. On `gemma-3n-e4b-it` which constraint pays *flips with position* and Λ
reverses sign. L1 is emitted somewhere in every configuration of both
replications. L2 is withheld everywhere (its gate is L1 in both directions).
L3 is unreachable — neither design estimates Δ_R.

**A defect in the L4 emitter is recorded and deliberately not repaired.**
§3.2 gates L4 per named member; `emit_l4` compares the set of levels any member
reached, and is handed input with the member identity already discarded. For
`gemma-3n-e4b-it` both configurations reach L1 while each member's
classification flips, so the emitted L4 asserts replication for the replication
that least replicates. **That field is invalidated; §28.1's *Configuration
dependence* is the registered reading.** It is not repaired because
`run_unmasked_analysis` refuses an unmasked analysis under a moved code hash
and §20 forbids re-masking after unmasking — the commitment device worked and
bound the author of the defect. `final_results.json` carries the registered
per-member reading beside the emitted field; a characterization test pins the
sealed behaviour so a silent fix fails loudly. See
`CHANGES_SCIENTIFIC.md` items 18–19 and
`dci1/reports/dci1v4r4/EXECUTION_REPORT.md` §8.3.

**State.** Both replications complete through `UNMASKED_ANALYSIS`. Evidence:
355 files, 769.7 MB, 155,712 scored rows, byte-identical in both roots, 149
critical artifacts with none missing or diverged. The post-freeze delta
compares all 66 fields under current code and reports
`scientific_state_unchanged: true` for both. Six registered quantities — Δ_R,
Δ_j, δ_difficulty, Ξ, D(B←R_j), D(R_j←B) — are `NOT_IDENTIFIED` study-wide and
are listed by name rather than omitted. `dci1/reports/dci1v4r4/final_results.json`,
`dci1/reports/dci1v4r4/EXECUTION_REPORT.md`.


### 4q. v5: drafted, and what v4r4's failure was measured to be (2026-08-22)

**v4r4 answered the compositional questions and did not reach the
companion-specificity one.** Every companion-specific estimand — `Δ_R`, `Δ_j`,
`δ_difficulty`, `Ξ`, `D(B←R_j)`, `D(R_j←B)` — is `NOT_IDENTIFIED` on both
survivors, because both ran the 8-cell reduced design, and the one replication
that obtained a full design was ended at Gate 4 before generating a
confirmatory row. v5 is a standalone preregistration that rebuilds the
reference-construction procedure. **It is drafted and not adopted**; nineteen
registered decisions and five red-team findings are open.

**Five failures, each measured rather than described**
([`reference_design_development.md`](dci1/reports/dci1v5/reference_design_development.md)):

| | Failure | The measurement |
|---|---|---|
| F1 | a point-estimate pre-screen used as a hard selector | pre-screen→calibration median \|Δι\| = 0.0709; **35.7% of candidates move further than the whole 0.10 caliper**; straddling support fell 7→3, 5→0, 4→2, 4→0 |
| F2 | ι alone as the admission coordinate | six rungs sat inside the caliper with raw solo above 0.90; one at solo 0.9740 / chance 0.9323 terminated a replication **on its own solo cell** |
| F3 | "production class" too coarse | two companions in one declared class gave Δ_class of +0.011 and −0.511 |
| F4 | solo-matched controls made trivial by B | `RF11` went 0.635 solo → 0.969 composed; recomputed κ(R\|B) = 0.833 and 0.964 for the two failing rungs |
| F5, F6 | support at the minimum; an operating-point grid that ends where the operating point is | three of four finished below three core references; **m\* was the last measured rung on all four** |

**The finding that drives v5's library.** Applying v5's full validity stack to
v4r4's own measurements leaves **3, 0, 0 and 0** qualifying families in the
budget-class reference pool and **4, 4, 2 and 3** in the production-class pool
v4r3's §7.3 forbade to be references — unchanged at every stage of the stack. A
maximum-word-length outcome constraint systematically shifts every word-shaped
budget numerator; an exact count of a short marker word is chance-free,
interaction-free, same-form with A and tunable in difficulty. **v4r4's
reference pool contradicted v4r3 §13.1's own rationale**, and v5 §7.5 resolves
it in favour of §13.1.

**The quantity that makes the interaction gate free.** `κ(R|B)` — R's verifier
on responses written under B alone, R absent — costs no generations under
§9.1's presence rule. On the one replication that composed a reference with B
it separated 4 of 4 Gate-4 failures from 16 passing checks with no false alarm.
v4r4's calibration scored load-one rows on the present instance only, so the
quantity did not exist in its records and had to be recomputed; v5 makes the
presence rule mandatory at every generative stage.

**Two documentation corrections, neither moving a number.** The v4r4 follow-up
report's §6 quotes caliper values (0.075, 0.10) that the code and that
package's own machine-readable artifact contradict (0.10, 0.15); no admission
verdict is affected, because every verdict called the registered selection
functions. And four constants in `dci1v4r4` carry stale v4r3-era comments that
disagree with their computed values. `CHANGES_SCIENTIFIC.md` records both.

**Status.** Five red-team findings unresolved
([`v5_prereg_redteam.md`](dci1/reports/dci1v5/v5_prereg_redteam.md)), the
sharpest being that a same-form control pool may make L3c — the source memo's
*refutation* verdict — near-automatic. Every v5 threshold was chosen after
observing all of v4r4, which is design fitting; v5 is the prospective test and
no artifact may call the retrospective analysis validation.


### 4r. v5 implemented, and what running the carried code over a new library found (2026-08-22)

**The protocol now has an implementation and it cannot run.** `dci1/src/dci1v5/`
is a v5 namespace beside the closed v4r4 one; `dci1/tests_v5/` holds 225 tests
that pass in about two seconds. `protocol/decisions.py` carries §34's
**nineteen** open decisions as executable state, every one `UNRESOLVED`, and
`engine/transitions.assert_transition_legal` refuses a stage whose decisions
are open. `PROTOCOL_REGISTERED` depends on all nineteen, so no v5 stage can
run — which is `REGISTRATION_INCOMPLETE`, and is the intended state.

The pre-freeze audit is a **stage** in v5 where it was a tool in v4r4, and it
is Gate 5's registered predecessor, so a failing audit makes the freeze
unreachable with no special case. Run today it reports
`PREFREEZE_AUDIT_FAILURE`: twelve of §33's fifteen checks pass statically,
three return `UNRESOLVED` because they need a run that has not happened, and
beside them sit nineteen open decisions and five unresolved red-team findings.

**Where both branches of a researcher decision exist in the source.** D6
(is `REFERENCE_SUPPORT_NOT_IDENTIFIED` terminal), D16 (which population
Calibration-B measures), D17 (a construct floor for m\*), D18 (is the
near-form arm a precondition of L3c), D3 (the 96 questions that do not exist)
and D4 (the marker vocabulary) each reach a `decisions.choice(...)` that
raises until the decision is closed. D17's `floor` branch refuses **even when
closed**, because a construct floor is a registered value with a derivation
and the implementation does not invent one.

**Three latent defects in carried verifier code, found by running it over v5's
library rather than by reading it.** The sharpest: `joint_witness` satisfied
only the *first* exact-count constraint of a pair and built an exact sentence
count as loose terminators followed by filler, which §9.2 counts as one
sentence too many. Neither path is reachable in v4r4, whose library held one
exact-count reference family and no sentence-exact family. Run unfixed over
v5's population the carried suite reported **2,016 non-entailment failures**,
every one a witness the constructor built wrongly rather than a pair whose
obligation cannot be discharged. Generalised, it discharges **20,332
realisable pairs with zero failures of either kind**. The other two are in
[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md); none affects a v4r4 result.

**What the implementation measured rather than assumed.** The library computes
to exactly §7.10's four counts — 37 families, 326 round-0 severities, 632
declared, **650 instruments in 39 verifiers**. The carried numerators agree
with v4r4's on **2,655 comparisons** over the frozen corpus. The boundary
suite reproduces every frozen expectation over 2,076 checks. §7.7's realistic
witness finds `CL7:125, 130, 135, 140` unreachable inside the 60–120 word stem
band and nothing else in the library, which is the registered finding computed
instead of asserted.

[`v5_implementation_status.md`](dci1/reports/dci1v5/v5_implementation_status.md)
carries the ordered list of what a researcher must do before v5 may measure
anything; [`v5_reconciliation.md`](dci1/reports/dci1v5/v5_reconciliation.md)
classifies every document discrepancy the implementation found.

### 4s. v5's execution plumbing exercised end to end, and eleven defects that only appear when a stage runs (2026-08-22)

**Still not adopted, and nothing here is scientific evidence.** No v5 stage
record exists under `dci1/evidence/dci1v5/`, no Calibration-B question has been
authored, no v5 topic has been consumed, no model has generated a v5 response,
and §34's nineteen decisions are all `UNRESOLVED`. What exists now is the
`run/` layer — thirteen modules, all eighteen stages on one driver, plus a CLI
— and an engineering harness that walks every stage with **no model**, in the
`synthetic` namespace, under a temporary evidence root, against an isolated
repository it builds and commits.

The walk produces eighteen signed records: a design derived from an admitted
arm set (`base + core + spectrum`, 44 cells, three Tier-1 core references), a
complete confirmatory draw matrix, a sealed mask, a one-shot unmask, and a §31
result table every field of which traces to a stage record and a hash. It is
**engineering evidence only** — the fixtures are engineered to be satisfiable,
which is what makes them useful for finding plumbing defects and useless as
evidence about a model. The right sentence is *the v5 execution plumbing has
been exercised end to end on synthetic fixtures*, and it says nothing about
whether v5's matching procedure will work prospectively on a real model.

**Eleven defects, nine of them in code that would have produced or read v5's
numbers.** The four that would have changed a result:

- **§9.1's absent verdicts carried no slot.** κ(R|B) — §13.6's whole input, and
  the reason v5 scores every instance on every row — is indexed by slot, so it
  was unreadable; and §25's load-0 cell, where every verdict is absent by §9.1,
  collapsed onto one key per block, so the difficulty coordinate's chance term
  could not be formed from real rows at all.
- **`delta_difficulty` was registered and never computed.** §11.7 defines its
  estimator, §17.2 its refit-per-replicate bootstrap, and `bootstrap_family`
  already accepted the callable member for exactly this case. F1's simultaneous
  critical value was therefore taken over **five members instead of six**, so
  every F1 interval was narrower than §15 registers.
- **§20 names `Delta_R` as not computable in the masked phase and the code
  computed it**, so the masked record carried an estimate of the study's
  primary quantity formed against permuted companions. The guard that was meant
  to catch this read a key no estimate record has ever carried, so it had never
  checked anything.
- **§31's result table emitted six of its twenty-one fields**, and the bootstrap
  computed the standard error and the marginal bounds and discarded them.

Two rules were **unsatisfiable rather than strict** and were repaired: the
pre-freeze audit's `can_freeze` could not be reached however the study went, and
`producing_commit_clean` was waived in the synthetic namespace — which made
provenance the one rule the integration test never exercised. The waiver is
gone; the harness builds a real clean repository instead.

The producer/consumer contract is now checked against the payloads a real walk
produced, not only against the declaration:
[`v5_producer_consumer.md`](dci1/reports/dci1v5/v5_producer_consumer.md) —
**98 fields, 17 artifacts, 98 exercised, 0 defects**, regenerated by
`dci1/tools/v5_producer_consumer.py`. `dci1/tests_v5/` holds 343 tests, all
passing; `tests_v4r4/` is unchanged at 594 passed with 6 skips and
`tools/v4r4_evidence_manifest.py --verify` reports `OK`.

**What remains is researcher work, not implementation.** Authoring the 96
Calibration-B questions (D3), closing D0–D18, and resolving U2 — §11.8's
tier-indicator formulation, whose four mathematically identified alternatives
are recorded in `protocol/open_items.py` and whose fit fails closed until one
is adopted. §4t is where that stopped being true of D3.

### 4t. Four §34 decisions taken, the Calibration-B bank authored, and what each remaining decision now asks (2026-08-22)

**Still not adopted, and still no v5 observation of anything.** The
registration manifest refuses on four separate grounds, `dci1/evidence/dci1v5/`
does not exist, and no model has generated a v5 response. What changed is that
the repository moved from *pre-adoption engineering complete* to *scientific
design finalisation complete*: every remaining barrier is a researcher
approval, and none is missing analysis or unwritten code.

**Four decisions were taken, and two went against the preregistration's own
standing proposal.** They are recorded with their evidence in
[`researcher_decisions.json`](dci1/reports/dci1v5/researcher_decisions.json),
which `protocol/decisions.py` reads at import — so `value_of("D18")` answers
with what the researcher decided rather than with a module literal, and the
manifest binds the record by hash.

- **D18 — the strong L3c requires the near-form arm.** L3c carries a registered
  scope: `strong` is the source memo's refutation verdict and needs the arm;
  `same_form_only` is what a same-form Tier-1 pool alone licenses. The strong
  conclusion is *unreachable* without the arm, which is the gate R1 asked for
  in place of a qualifying sentence — and it makes the 47-cell compute option
  a different study rather than a cheaper one.
- **D16 — Calibration-B measures the complete carried population.** §13.7
  becomes a test of the candidate landscape's stability instead of a
  re-confirmation of an already-selected set. About 35,000 further generations
  per replication, accepted; *accidental* repetition is not, so a row's reuse
  key is now its complete scientific identity, with the **split** in it
  explicitly.
- **D6 — an unbuildable reference set is non-terminal and irreversible.** The
  affected estimand set is derived from §15's families by one rule — 48 of 70
  registered members — frozen, and four rehabilitation paths are refused by
  name, including an observed composed outcome read as evidence the pool was
  adequate after all.
- **D3 — the 96 Calibration-B questions exist**, authored before any v5
  measurement or selection outcome, disjoint from all five other topic sets in
  id *and* in question text, hashed into the manifest.

**Four decision packets, each with a recommendation nothing has adopted.**
[D17](dci1/reports/dci1v5/d17_b_strength_decision.md) recomputed B's
chance-compliance curve over the whole v5 grid from v4r4's load-zero answers
and found the thing R14 warned about, measured: $\kappa^{B}$ is 0.000 at every
$m \le 10$ — which is why v4r4 recorded the quantity as useless — and
**0.59–0.73 at $m = 13$**, where the median natural answer already complies
without changing a word. [D4](dci1/reports/dci1v5/d4_marker_audit.md) audits all
eight markers: five approve outright, and `though`, `namely` and `overall` each
carry one judgement the rules do not settle.
[U2](dci1/reports/dci1v5/u2_tier_model_decision.md) demonstrates rather than
argues — under the pooled formulation A4, $\gamma$ ranges 0.024 to 0.134 across
placements of the same three controls generated from one fixed 0.08, while A2
returns 0.08 every time. [D1](dci1/reports/dci1v5/d1_arm_compute_decision.md)
derives 1,135,104 generations for the recommended configuration from the code's
own constants.

**Red team.** R1 is resolved by D18 and R11 mitigated by D16; R16 is an
accepted limitation *by* D6, with the resource-allocation cost explicitly
accepted; R5 remains a permanent limitation that no decision closes. R14 is the
only one of the five still open, and it is open because D17's threshold is.

[`v5_adoption_checklist.md`](dci1/reports/dci1v5/v5_adoption_checklist.md)
states every remaining item as one plain question.

## 5. Provisional, superseded, broken, unresolved

- **Superseded.** The capped reasoning-curve exports under
  `exploratory/figures/reasoning_compute/data/` were built by a figure path that
  bypassed the canonical-evidence guard. Marked, retained, not regenerable in this
  checkout — `PROVENANCE.json` there says exactly what and why. The natural-endpoint
  headline is unaffected.
- **Void.** The anti-splice intervention failed its own manipulation check
  (`ANTI_SPLICE_MANIPULATION_FAILED`). A failed manipulation check voids an
  estimate; it does not weaken it into a null.
- **Closed, and preserved.** DCI-1 v4r3 is terminal at `GATE_1_MEASUREMENT`
  with `MEASUREMENT_EVIDENCE_INSUFFICIENT`. Its registered criterion asked
  whether external reviewers reproduce the verifier and neither pathway
  established that; the later §10.7-R5 amendment then blocked on a `CP4`/`CP7`
  wording. Both records stand, neither pathway is described as having
  succeeded, and nothing under v4r3's source, test, evidence, durable or report
  trees was edited to reach v4r4. `dci1/reports/dci1v4r3/closure.json`. §4l,
  §4m.
- **Superseded, and preserved.** The earlier `GATE_1_BLOCKED_MEASUREMENT`
  decision was correct under the rule then in force — §10.2 plus §10.3 or
  §10.4, neither of which completed. §10.7-R5 changed the rule, not that
  record, and v4r4 changes it again prospectively; neither describes either
  pathway as having succeeded. §4k, §4l, §4m.
- **Live, and limiting.** Under v4r4, §12.6's C4 is met on all four models but
  with **no leave-one-family-out margin on three of them** — exactly four
  well-formed straddling feature groups, every one load-bearing. Inherited from
  v4r3's reference pool, not created by removing `CP4`/`CP7`. The registered
  expansion is deliberately not invoked (`DECISIONS_V4R4.md` B7), so any
  Gate-3 or Gate-4 result on those three models is conditional on all four
  groups holding. §4m.
- **Unanswered, permanently scoped.** v4r4's measurement basis is
  `deterministic_measurement_validated`, never `human_validated`. §10.5's scope
  sentence therefore attaches to every analysis record: the outcomes are
  verifier-defined and support no claim about compliance as an independent
  human would judge it. §4m.
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
whether old and new remain comparable. Most recent: DCI-1 v5 drafted — the core
reference pool inverts to production class and same-form with A, a
pre-composition interaction gate is added, and two v4r4 documentation values
are corrected without moving a number — in §4q. Before it: the whole pipeline
below Gate 1 executed for the first time and nineteen defects, most of one
class — a reader with no producer — moved what a v4r4 record says, in §4n, §4o
and §4p.

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
| the completed DCI-1 protocol | `user-notes/DCI1_preregistration_v4r4.md` (incorporates v4r3's by reference) |
| the drafted successor, not adopted | `user-notes/DCI1_preregistration_v5.md` (standalone), `user-notes/DCI1_v4r4_to_v5_changelog.md` |
| why v5 exists, measured | `dci1/reports/dci1v5/reference_design_development.md`, `dci1/reports/dci1v5/reference_design_spec.json` |
| what is still open in v5, as one question each | `dci1/reports/dci1v5/v5_adoption_checklist.md` |
| what is still open in v5, in full | `dci1/reports/dci1v5/v5_prereg_redteam.md`, `dci1/reports/dci1v5/v5_implementation_status.md` §4 |
| which §34 decisions the researcher has taken, and on what evidence | `dci1/reports/dci1v5/researcher_decisions.json` |
| the four decision packets awaiting approval | `dci1/reports/dci1v5/d1_arm_compute_decision.md`, `d4_marker_audit.md`, `d17_b_strength_decision.md`, `u2_tier_model_decision.md` |
| every v5 field, its producer and its readers | `dci1/reports/dci1v5/v5_producer_consumer.md` |
| what v5's implementation is, and what it cannot do | `dci1/src/dci1v5/`, `dci1/tests_v5/`, `dci1/reports/dci1v5/v5_implementation_status.md` |
| every v5 document discrepancy and its classification | `dci1/reports/dci1v5/v5_reconciliation.md` |
| what v4r4 changed and why | `user-notes/DCI1_v4r3_to_v4r4_changelog.md` (R4-1–R4-7) |
| the v4r4 decisions register | `dci1/DECISIONS_V4R4.md` (B0–B7, E0–E7) |
| what v4r4 measured, and its follow-up | `dci1/reports/dci1v4r4/` — `final_results.json`, `EXECUTION_REPORT.md`, `SCIENTIFIC_FOLLOWUP_EVIDENCE.md` |
| why v4r3 stopped, and what it left | `dci1/reports/dci1v4r3/closure.json`, `dci1/reports/dci1v4r3/REPORT.md` |
| the superseded v4r3 protocol and register | `user-notes/DCI1_preregistration_v4r3.md`, `dci1/DECISIONS_V4R3.md` |
| the v4r3 implementation, preserved | `dci1/src/dci1v4r3/README.md` |

## 8. Keeping this file honest

It is derivative by design: claims link to reports, reports link to runs, runs
carry their own configuration. Update §4–§6 when `CHANGES_SCIENTIFIC.md` gains an
entry; if a statement here cannot be traced to a linked artifact, delete it rather
than maintain it.
