# DCI — current scientific state

The 10-minute orientation. Everything here points at something else; primary
numbers live in the reports and the generated artifacts, not in this file.

Last reviewed: 2026-08-20.

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
| **v4r3** | **adopted and registered 2026-08-21, not frozen, no confirmatory data.** Run through stage 3; §7.0-R3 (C27) restores coverage on all four models at round zero. Gate 1 is `GATE_1_BLOCKED_MEASUREMENT`: every §10.2 criterion passes over 584 instruments, and **both** registered pathways are unavailable — §10.4-R2 (C28) failed its own criterion 5 and stops by rule, §10.3 has no independent annotator. §4h, §4i, §4j, §4k. `user-notes/DCI1_preregistration_v4r3.md`, `dci1/reports/dci1v4r3/gate1_decision.json` |

v4r2 replaces target failure with the per-constraint compliance vector, makes
reciprocal delivery loss the primary estimand, matches references to A on solo
compliance rather than to B on solo failure, and makes instruction order a
cell-level factor. It is a different protocol: v3 and v4 numbers are not
comparable and are never compared. Nine registered open decisions (V1 to V9)
and seven pre-freeze checks remain open; the freeze and confirmatory generation
are implemented and deliberately not executed. **v4r3 (§4h, §4i) supersedes
v4r2 as the live protocol line**: it was adopted and registered on 2026-08-21
and has been executed through the regime screen. The two are structurally
prevented from reading each other's artifacts, and no v4r2 record was edited.

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
0.10 — which 25 items cannot reach even at zero disagreements.

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

**Gate 1: `GATE_1_BLOCKED_MEASUREMENT`.** Every §10.2 prerequisite passes at
the R3 verifier hash `41edc84c` over all **584** instruments — three-process
determinism 1.000, 164 boundary cases 1.000, independent reimplementation
1.000 over 16,604 responses and 700,800 verdicts, one segmenter-differential
splitter, 92,988 witness pairs, 46,720 wording verdicts, reserved sets unspent.
Neither pathway §18 stage 4 requires has completed: §10.4 is closed by its own
stopping rule and §10.3 has no independent annotator. **The single remaining
blocker is §10.3 performed by someone independent of the design and analysis
team.** It is not a governance block — a signature cannot be applied to a
pathway whose criteria failed. `dci1/reports/dci1v4r3/gate1_decision.json`.

## 5. Provisional, superseded, broken, unresolved

- **Superseded.** The capped reasoning-curve exports under
  `exploratory/figures/reasoning_compute/data/` were built by a figure path that
  bypassed the canonical-evidence guard. Marked, retained, not regenerable in this
  checkout — `PROVENANCE.json` there says exactly what and why. The natural-endpoint
  headline is unaffected.
- **Void.** The anti-splice intervention failed its own manipulation check
  (`ANTI_SPLICE_MANIPULATION_FAILED`). A failed manipulation check voids an
  estimate; it does not weaken it into a null.
- **Blocked.** DCI-1 v4r3 stands at `GATE_1_BLOCKED_MEASUREMENT`. Both
  registered measurement pathways are closed: §10.4-R2 failed its own criterion
  5 and stops by rule, and §10.3 has never been performed by an annotator
  independent of the design and analysis team. Everything from Gate 2 onward is
  downstream of that one requirement. §4k.
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
whether old and new remain comparable. Most recent: §10.4-R2's failure and
the four re-sealed regime records, in §4k.

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
| the live DCI-1 protocol | `user-notes/DCI1_preregistration_v4r3.md` |
| what v4r3 changed and why | `user-notes/DCI1_v4r2_to_v4r3_changelog.md` (C1–C25) |
| the v4r3 adoption record and its open decisions | `dci1/DECISIONS_V4R3.md` |
| what v4r3 has measured so far | `dci1/reports/dci1v4r3/REPORT.md` |
| the v4r3 implementation and how to run it | `dci1/src/dci1v4r3/README.md` |

## 8. Keeping this file honest

It is derivative by design: claims link to reports, reports link to runs, runs
carry their own configuration. Update §4–§6 when `CHANGES_SCIENTIFIC.md` gains an
entry; if a statement here cannot be traced to a linked artifact, delete it rather
than maintain it.
