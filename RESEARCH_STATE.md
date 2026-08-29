# DCI — current scientific state

The 10-minute orientation. Everything here points at something else; primary
numbers live in the reports and the generated artifacts, not in this file.

Last reviewed: 2026-08-29.

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
| **v5** | **RUN AND CLOSED 2026-08-24. No replication reached `CONFIRMATORY_GENERATION`: two terminated at Gate 4 on §13.14 composed headroom, two are permanently blocked at `PREFREEZE_AUDIT` by an irreversible D6 non-identification. 459,312 behavioural rows exist and none is confirmatory.** [`dci1/reports/dci1v5/CLOSURE.md`](dci1/reports/dci1v5/CLOSURE.md) All nineteen §34 decisions closed, U2 resolved at A2, P1 confirmed, registration manifest signed; three closures went against the document's own standing proposal (D16, D17, D18). The registered design is five arms, four models, 56 cells, 1,172,544 generations. A standalone preregistration that rebuilds the reference-construction procedure v4r4 could not make work. The core reference pool inverts to production class and same-form with A; ι is demoted from the admission coordinate to the difficulty coordinate; a pre-composition interaction gate, two calibration splits, direct order estimands and the L4 fix are new. Its execution plumbing has been exercised end to end on synthetic fixtures, which is engineering evidence and not a result. A stage 3–18 execution-path audit then found twelve registered rules that the production path did not execute — four multiplicity families with no producer, three claim emitters with no caller, §12.6's expansion unreachable and its coverage criterion evaluated on an empty set — and one place, §12.6's eligibility predicate, where the preregistration did not determine the rule. That one was resolved at E2 — §13's band applied to the quantity §13 bands, $p_{\text{solo}}$ — and §18 step 14's raw-coordinate fit was implemented as §15 registers it, with no multiplicity family invented. 48 registered rules are now audited against the path a replication takes, all 48 reachable, over 15 conditional scenarios. §4q, §4r, §4s, §4t, §4u, §4v, §4w, §4x. [`user-notes/DCI1_preregistration_v5.md`](user-notes/DCI1_preregistration_v5.md), [`dci1/src/dci1v5/`](dci1/src/dci1v5/), [`dci1/reports/dci1v5/`](dci1/reports/dci1v5/) |
| **v6** | **RAN AND CLOSED 2026-08-27, zero survivors of four (§4ak).** `qwen3-4b` and `qwen3-4b-instruct-2507` terminated at Gate 2.75 `COMPOSED_HEADROOM_UNREACHABLE` because **B's compliance rose under A toward the ceiling** (0.747 → 0.891; 0.779 → 0.924); `gemma-3n-e4b-it` at Gate 4 `COMPOSED_HEADROOM_FAILURE` on `solo:CL` = 0.958, a companion's own solo cell; `gemma-3n-e2b-it` passed Gate 4 and terminated at `PREFREEZE_AUDIT` because A16/A17 had edited the registered document and the lifecycle could not bind a post-registration amendment. Both Gemmas had lost `Delta_R` at Gate 3C. All four verdicts stand. [`dci1/reports/dci1v6/CLOSURE.md`](dci1/reports/dci1v6/CLOSURE.md). *Registration history:* ADOPTED and REGISTERED 2026-08-26 (registration after amendment A15; §4ah). Zero behavioural rows at registration. All twenty-seven §34 decisions and all three blocking §33 items closed on [`dci1/reports/dci1v6/researcher_decisions.json`](dci1/reports/dci1v6/researcher_decisions.json); D0–D18 carried at v5's actually adopted values with v5's evidence and a `carried_from` block. Nineteen stages: a new `GATE_2_75_COMPOSED_PROBE` measures composed headroom at the **frozen** m\* two stages before Gate 4 and may terminate a replication `COMPOSED_HEADROOM_UNREACHABLE` but may never move the operating point. V6-E01/E02/E05 repair §12.6's reachability, expansion-row eligibility and `n_stable` prospectively. Three `probe_only` families PS1–PS3 are non-selectable by construction. §34 D23 = `projection_sd`, D26 = 0.0142 (measured). Registered design: five arms, four models, 56 cells, 1,174,080 generations. §18 stage 1's `REGISTRATION_INCOMPLETE` is a **readiness refusal**, not a §28 terminal status (A15); §12.6 drops a rung with no difficulty coordinate from its coverage conditions and records it (A16). Executing: all four registered, qualified and through Gate 1; §4aa–§4aj. [`user-notes/DCI1_preregistration_v6.md`](user-notes/DCI1_preregistration_v6.md), [`dci1/src/dci1v6/`](dci1/src/dci1v6/), [`dci1/reports/dci1v6/`](dci1/reports/dci1v6/) |
| **v7** | **ADOPTED, REGISTERED AND RUN 2026-08-28; CLOSED the same day with zero survivors of four (§4am).** Every replication passed the stages v7 changed — both Qwens the composed probe, both Gemmas Gate 4 — and every one lost `Delta_R` at Gate 3C on §12.6's C4 under the calibrated re-read, then ended `PREFREEZE_AUDIT_FAILURE` on `support_satisfied`. Drafted 2026-08-27 (§4ak); §13.14 boundary-audited 2026-08-28 and revised as V10 before adoption (§4al). A superseding registration, not a v6 amendment: v6's §32.3 froze §13 from the first Gate-2.5 record and §32.1 forbids weakening a criterion so that a gate passes. v7 **withdraws** the absolute composed-headroom criterion as a terminal requirement — `COMPOSED_HEADROOM_FAILURE` and `COMPOSED_HEADROOM_UNREACHABLE` leave the vocabulary and no module can raise them — and replaces it with readings of the **contrast**: a structural zero licenses nothing, an arm at an exact boundary widens the decision interval by the Wilson allowance in the open direction, and a direction compressed below the SESOI by the other arm's level is named on the statement. Gate 2.75 and `GATE_4_COMPOSED_CONTRAST` record the paired contrasts by the confirmatory estimators, bootstrapped over topics, and have one outcome. No threshold moves; the estimand layer is byte-identical to v6's. A post-registration amendment is now bindable (A4), the hole that ended `gemma-3n-e2b-it`. [`user-notes/DCI1_preregistration_v7.md`](user-notes/DCI1_preregistration_v7.md), [`dci1/src/dci1v7/`](dci1/src/dci1v7/), [`dci1/reports/dci1v7/READINESS.md`](dci1/reports/dci1v7/READINESS.md) **Amended in place 2026-08-28 (A6–A8, §4an) after the closure:** the pre-freeze check that ended every replication (`support_satisfied`, "support met") is withdrawn for the registered invariant (support *recorded*, D6's disposition, the exact non-identified set, the arm set, no rehabilitation path); §12.6's C2/C4 now gate the spectrum arm and C1/C3/C5/C6 the core arm, no value moving; D6 means one thing everywhere. Bound via the A4 chain; V11–V13 checked; the four terminal reports stand; re-running is an open researcher decision. **2026-08-29 (§4ao):** the §13.11 chance column had been 0.0 on every replication; corrected on the Gate-2 producer (V14), stored tables not comparable with corrected ones, no record re-verdicted. |
| **v4r4** | **adopted 2026-08-21; frozen at Gate 5 on 2026-08-22 for two of four replications, confirmatory data in hand.** The live protocol line. Gate 1 is deterministic-measurement by construction (§10.7 A–E) and `CP4`/`CP7` are removed. All four replications passed Gates 1–3; **§13.10 then ended two of them at `COMPOSED_HEADROOM_FAILURE`, including the only full-design replication**. Two survive to Gate 5, both on §8.6's 8-cell reduced design, so no spectrum-dependent estimand is identified anywhere in the study. Both survivors froze at `450a049`, generated 24,576 rows each, and are analysed through `UNMASKED_ANALYSIS`; **they disagree qualitatively** and one replication's L4 field is invalidated. §4m, §4n, §4o, §4p. `user-notes/DCI1_preregistration_v4r4.md`, `dci1/reports/dci1v4r4/final_results.json` |

v4r2 replaces target failure with the per-constraint compliance vector, makes
reciprocal delivery loss the primary estimand, matches references to A on solo
compliance rather than to B on solo failure, and makes instruction order a
cell-level factor. It is a different protocol: v3 and v4 numbers are not
comparable and are never compared. Nine registered open decisions (V1 to V9)
and seven pre-freeze checks remain open; the freeze and confirmatory generation
are implemented and deliberately not executed. **v7 (§4ak) is the live protocol line** as of 2026-08-27, drafted and not
adopted; it supersedes v6 (§4ag–§4aj, closed 2026-08-27), which superseded v5,
which superseded v4r4. v4r4 supersedes v4r3, which superseded v4r2. Each was adopted
and registered on 2026-08-21, and each is structurally prevented from reading
the others' artifacts: `dci1v4r4.engine.context.foreign_roots` names v4r3's
evidence, durable and source trees, and `assert_own_study` refuses a stage
record whose `study_id` is another revision's. No v4r2 and no v4r3 record was
edited by any of it.

### 4d. The canonical v8 candidate (2026-08-29, branch `dev/v8-canonical`)

One development branch reconciles the verifier unification, the §13.11
chance-column fix (7f89dae, merged here and not on the study branch), the
difficulty-spectrum diagnosis and the pre-screen/spectrum redesign. Design of
record: [`dci1/docs/V8_CANDIDATE.md`](dci1/docs/V8_CANDIDATE.md); which
definition belongs to which revision:
[`dci1/docs/VERSION_DRIFT.md`](dci1/docs/VERSION_DRIFT.md); code
`dci1/src/dci1v8dev/`, constants with provenance `dci1v8dev/rules.py`, tests
`dci1/tests_v8dev/`, reports `dci1/reports/dci1v8dev/`. Every replay on
stored evidence now reads §13.2's chance basis (the first v8 backtests read
the zero column and are superseded). What the corrected replays say: the
pre-screen's own chance rate is a biased basis for Tier-3 budget families;
most of the historical "retention artefacts" were chance mirages, ~5 of 32
are real; the new screen reaches precision 0.73 / recall 0.72 against 0.46 /
0.70 for the legacy certificate; 105 of 117 local caliper rungs are kept at
40–64 forwarded rungs (§12.7: 112–140); coverage offsets 0.10/0.10 and span
0.20 were chosen by simulation. Nothing is registered; no v8 evidence
exists; the next step is a solo/calibration pilot on one model under the
v8 frames, after a v8 run layer is built (§12 of the design note).

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
is adopted. §4t is where that stopped being true of D3; §4u is where it stopped
being true of the rest.

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
derives the recommended configuration's generation budget from the code's
own constants.

**Red team.** R1 is resolved by D18 and R11 mitigated by D16; R16 is an
accepted limitation *by* D6, with the resource-allocation cost explicitly
accepted; R5 remains a permanent limitation that no decision closes. R14 was
the only one of the five still open at this point, and it was open because
D17's threshold was — §4u closes it.

[`v5_adoption_checklist.md`](dci1/reports/dci1v5/v5_adoption_checklist.md)
states every remaining item as one plain question.

### 4u. v5 adopted and registered, and the estimator defect closing D17 surfaced (2026-08-23)

**v5 is formally adopted. Still no v5 observation of anything.** All nineteen
§34 decisions carry a value, U2 is resolved at A2, P1 is confirmed,
`manifest.signing_blockers()` returns `[]`, and the registration manifest is
signed from a clean commit into `dci1/evidence/dci1v5/`. No model has been
loaded, no prompt generated, no calibration measurement taken, and no gate run
on model output. Adoption fixes the rules; it does not start the study.

**Three of the nineteen went against the preregistration's own standing
proposal** — D16, D17 and D18 — which is the fact worth carrying, because a
register on which every proposal survives is a register nobody read.

- **D17 — a construct floor on $m^*$: $\kappa^{B}(m^{*}) \le 0.50$**, on the
  **point** estimate, with the Wilson bound reported beside it and
  `CONSTRUCT_FLOOR_MARGINAL` recorded when the interval straddles it. The
  derivation is the widest separation in the measured curve: no development
  model falls between 0.398 at $m = 12$ and 0.586 at $m = 13$, a gap of 0.188
  against a next-largest of 0.104. An $m^*$ that satisfies §12.3's compliance
  band and fails the floor ends the replication at `FOCAL_RANGE_EXHAUSTED`
  before anything confirmatory is generated — the accepted cost. **The number
  is not in the code**: it is a field of the D17 closure in
  `researcher_decisions.json`, which `construct_strength.registered_floor()`
  reads and the manifest binds by hash.
- **D1 — all five arms, four models, 56 cells, 384 blocks, $M = 8$**, which is
  **1,172,544** generations recomputed by `dci1v5.design.budget` from the
  code's own constants rather than quoted. The near-form arm is registered
  rather than merely permitted, so R1's only mitigation is in the design.
- **D4 — all eight Tier-1 markers**, with four **accepted limitations**
  recorded by name (`though`'s near-synonymy and two syntactic frames,
  `namely`'s possible appositive interaction with word length, `overall`'s
  natural rate, and the vocabulary-wide natural-rate spread) and a population
  hash that makes a substitution detectable rather than merely forbidden.
- **U2 — A2**: §11.8's $\alpha_f$ ranges over the three *core* families. A4
  stays constructed and non-adopted, because the evidence for preferring A2 is
  computed from it on every test run.

**Closing D17 surfaced a real estimator defect, and it is the finding here.**
The threshold was derived from $\kappa^{B}$ measured on **load-zero** answers.
Gate 2's registered `chance` rate averages every row where the severity was
*absent* — which in the focal grid includes the $B$-solo cells at the other
seven severities, answers written under a stated length budget, which satisfy a
looser budget far more often than an unconstrained answer does. On the
synthetic fixture the two denominators differ by more than 0.4 at $m = 7$.
Applying the threshold to that rate would have been a threshold calibrated on
one estimator and applied to another, wearing the same number. Gate 2 now
computes and records both (`load_zero_chance_curves` beside `chance_curves`);
the floor reads the load-zero one, and every other chance quantity keeps the
denominator it was defined with — §13.6's $\kappa(R \mid B)$ is deliberately
measured *under* $B$. The synthetic harness had also been giving $\kappa^{B}$
no curve at all, flat at 0.67 across every severity, which is a fixture that
could not have exercised the floor either way.

**Red team.** R1 is resolved by D18, R11 by D16, R14 by D17 and R16 by D6. R2
and R13 are adopted *over* a recorded objection rather than answered by
evidence, and the objection stays beside the value. **R5 is an accepted
permanent limitation and is not resolved** — $\kappa^{B}$ is measured under
$B$, so the reference set is a function of how each model writes under its own
$B$ at its own $m^*$, no rule closes that, and it is why no cross-model scalar
carries a claim.

**Stage 1, `PROTOCOL_REGISTERED`, has run** — it is the stage that signs the
manifest, and a registration written outside the stage machine would have no
stage record and no transition-log entry. **Nothing after it has.** The next
action is stage 2, `QUALIFIED`, which reads no behavioural rate; the first
stage that generates a model response is stage 3, §19's procedural pilot
(R22's mitigation), and Gate 1 over the 650-instrument population (R23's) is
stage 5, reading the regime screen's own text.

### 4v. The registered study could not be executed as committed, and the registration was superseded before Stage 2 (2026-08-23)

**Three defects, all found in the pre-execution sweep, none of them a
scientific value.** The first registration was verified in full — signature,
every hash, the manifest byte-reproducible from its producing commit — and then
the sweep asked the question a verification does not: can the lifecycle
actually run? It could not.

- **Three of the four registered models had no legal path into the lifecycle.**
  Stage 1's runner re-signed the *study-level* manifest on every call, and
  `write_json_once` refused the second replication, while the predecessor check
  demands a *per-model* stage-1 record. D1's four-model design was unreachable.
- **The pinned backend was unreachable from four of the five generating
  stages.** Gate 0, the regime screen, Gate 2 and Gate 4 each read
  `generate or fake_backend(...)` — unconditional, no override — and the CLI
  passes no generator. The documented way to run Gate 0 would have signed
  fabricated text into the registered evidence tree, and nothing downstream
  refuses a synthetic row in the registered namespace.
- **A row's `synthetic` flag recorded how the runner was called**, not what
  wrote the text, so those rows were synthetic by definition and a real backend
  injected into one of them would still have been stamped synthetic.

All three were invisible for one reason: the integration harness walks a single
model and always injects its own generator, so neither the second registration
nor the production generation path had ever executed. That is the general
lesson — **an end-to-end harness that supplies the seam it is testing does not
test the seam** — and it is why the amendment's tests include a four-model
registration walk and a static check on the substitution shape.

The amendment changed no threshold, estimand, arm, prompt, wording, verifier,
seed, cap, decoding policy or selection rule; every registered scientific value
is byte-identical across it. Manifest
`2960a1fc…` is **superseded and retained**, not deleted, together with the
stage-1 record signed under it. The replacement, `70608e5d…` at commit
`5e35ca6`, names it and carries a stage-1 record for all four replications —
the first time that has been possible. No observation existed under the
superseded registration, so nothing is invalidated.
[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) ·
[`dci1/tests_v5/test_amendment_pre_data.py`](dci1/tests_v5/test_amendment_pre_data.py)

### 4w. The registered rules of stages 3–18 were audited against the path a replication takes, and twelve were not on it (2026-08-24)

**The question no instrument in the repository had asked.** Four defects in a
row had one shape — the preregistered rule exists, the helper implementing it
exists, the tests cover it, and the production runner does not call it. Every
instrument that could have caught them asked something else: the tests asked
*does this function behave*, the producer/consumer contract asked *is this
field declared*, and the eighteen-stage synthetic lifecycle asked *does the
happy path complete*. The audit added here asks **does the registered rule lie
on the path a replication takes**, and proves each answer four ways — the
implementation resolves, a frame of it executes during a real run, the field
it produces is on the signed record, and the declared consumer is *observed*
reading that field.

**Twelve more defects, three of them large.**

- **Fifty-eight of §15's seventy-eight family members had no producer.** F5,
  F6, F7 and F8 were computed nowhere and declared neither `NOT_IDENTIFIED`
  nor `NOT_COMPUTABLE`, so §31's table carried no row for them and no reason
  for its absence. F8 is §11.8's tier-indicator fit — the one U2 was resolved
  at A2 to make estimable. F6 gates §17.4's whole interpretation, and F5
  supplies the recomputation §17.4's licensing rule compares against, so that
  rule was **vacuously satisfied at every emitter**.
- **Three of the five claim emitters had no production caller.** A complete
  lifecycle emitted `{'L1': 2}`. L3 is where $\Delta_R$ lives and L3c is the
  refutation verdict D18 was closed at `precondition` to protect; as wired,
  the lifecycle could not emit it on any data.
- **§12.6's coverage criterion was evaluated on an empty row set, and its
  verdict was read by nothing.** `coverage_criterion` filters rows on an
  `eligible` flag that nothing in the repository ever set, so C1–C6 were False
  on every replication; and `decisive_met` is read only inside
  `run_expansion`, which had no caller. A replication whose criterion was
  unmet therefore proceeded **with** the core and spectrum arms and reported
  $\Delta_R$ and $\delta_{\text{diff}}$ — the outcome §12.6 registers as
  forbidden.

Also: `REGIME_NOT_FOUND` and `GRID_RESOLUTION_INSUFFICIENT` had no production
condition — the Gate-2 record carried a key named `adequacy` holding the two
thresholds and no verdict, and neither of §12.4's two graded *shares* was ever
computed, though `constants.py` has carried `GRADED_CLAUSE_READING = "share"`
from the beginning. §12.6's C7/C8 arm drops were computed and discarded.
§11.3, §11.7 and §11.8's three executable both-forms assertions never ran.
§23's projection audit was the empty list. §31's result table labelled every
per-configuration row `L1` and `pair:A+B`. §19's lexicographic check and
§13.7's $\iota_A$ equivalence ran only in tests. And $\iota_A$ itself was
read from the first row of the difficulty table rather than, as §12.6 states,
from the severity whose solo compliance is nearest §12.3's aim.

**Two more, from the researcher's own audit of the same week.** The sweep's
instruments ask whether a registered rule is *on* the production path; two
defects were rules that are on it and take the wrong branch, and finding those
needs the section read against the code. A was never measured on the
pre-screen — `_screen_rungs` iterates the candidate library, which excludes
the outcome constraints — so `iota_a_prescreen` was null on every real regime
record and §12.7's Tier-3 ordering ran against the literal `0.5`. And
`select_all` ran only the spectrum-coupled selection pass, so a family that
could not straddle $\iota_A$ lost its **core** slot, where §13.12 and §8.1
drop only the spectrum — the exact coupling that produced v4r4's F5 failure,
re-implemented. Restoring the pre-screen moves the registered budget from
1,172,544 to 1,174,080.

**And one that only the scenario matrix could find.** A3 had restored the
caller for §12.3's focal escalation, and the branch refused the moment
anything ran it: §7.2's {15, 16} sit outside B's registered grid by
construction and the instrument layer rejects them unless the caller says so.
A3's repair had never executed, because the synthetic fixture's focal curve
always found a rung inside the grid. *The caller exists* is not the same
claim as *the branch runs*, and only a scenario that forces the branch can
tell them apart.

**And one the rules caught themselves.** With F5 restored, §20's withheld set
— which matched a member's exact name — let a recoding of $\Delta_R$ be
computed in the masked phase, and the guard on the sealed record refused the
analysis. A registered safeguard firing on a registered repair is what a
working safeguard looks like; the withheld set now matches on the stem, the
way the guard always did.

**One thing the preregistration does not determine, and it is blocking.**
§12.6 makes eligibility *"§13's band on $\iota$ and its vacuity ceiling"* —
and §13 registers its band on $p_{\text{solo}}$, and no band on $\iota$ at
all. Two readings are admissible; they admit different rungs, so they can
differ on C1–C6, on the admitted arm set, and therefore on **whether
$\Delta_R$ is identified**. Nothing chose. Both constructions are built by
name, the code path fails closed, and open item **U4** blocked the registration
manifest until it was resolved. **U4 was closed at E2** (eligibility on
$p_{\text{solo}}$) in amendment A5, and every v5 regime record carries the
`E2` formulation.

**What this cost and what it bought.** The four gemma behavioural stages
signed under `d0485a6d…` are retained and no longer reusable — they were
produced under a screen whose coverage criterion evaluated nothing, whose
$\iota_A$ came from the wrong severity, and whose expansion could not run. No
reference had been selected, no freeze existed and no composed outcome had
been observed, so §32's pre-Gate-2.5 window was open and nothing that could
influence selection is affected. Six of the twelve repairs make a gate
strictly **harder** to pass than it was.
[`dci1/reports/dci1v5/execution_path_audit.md`](dci1/reports/dci1v5/execution_path_audit.md) ·
[`dci1/reports/dci1v5/amendment_register.md`](dci1/reports/dci1v5/amendment_register.md) ·
[`dci1/tests_v5/test_execution_path.py`](dci1/tests_v5/test_execution_path.py) ·
[`dci1/tests_v5/scenarios.py`](dci1/tests_v5/scenarios.py)

### 4x. §12.6's eligibility rule was resolved at E2, §18 step 14's raw-coordinate fit was implemented as §15 registers it, and v5 re-registered (2026-08-24)

**The one blocking question, answered.** §12.6 made a pre-screen rung's
eligibility *"§13's band on $\iota$ and its vacuity ceiling"*, and §13.4
registers that band — $[0.10, 0.90]$ — on the **raw solo compliance**
$p_{\text{solo}}(R)$; §13 bands $\iota$ nowhere, and §13.8 constrains it only
through calipers *relative to* $\iota_A$. The researcher adopted **E2**: a rung
is eligible when $p_{\text{solo}}(R) \in [0.10, 0.90]$ and its pre-screen solo
vacuity is at most $0.10$.

The ground for it is that the alternative would have invented a threshold.
Applying §13's band *numbers* to $\iota$ is an absolute band on $\iota$, and no
section registers one; under §33's classification that is an amendment to §13,
not a reading of §12.6. **The coverage criterion itself does not move** — C1–C8
are still stated in $\iota$ and still position every rung by $\iota$ relative to
$\iota_A$. E1 stays constructible by name so the comparison remains inspectable,
and no reporting path can reach it. The resolution lives in
[`researcher_decisions.json`](dci1/reports/dci1v5/researcher_decisions.json),
whose hash the registration manifest binds, and
`stages.regime.coverage_eligibility` reads the **resolution** rather than a
literal: a test reopens U4 and asserts the rule refuses rather than defaulting.

**The registered quantity that had no implementation, implemented — and only as
far as the protocol registers it.** §18 step 14 repeats steps 9 and 12 on the
raw-coordinate secondary fit, and nothing fitted anything on that coordinate.
A4 declined to write it because step 12 computes *simultaneous intervals within
each declared family* and §15 declares no family containing a raw-coordinate
member, so a multiplicity set would have had to be chosen. **It does not have to
be, and §15 says so itself**: its own list of quantities *"reported with
marginal intervals only and supporting no claim"* names the raw-coordinate
replication of the fit. So step 9 is now executed in full — the fit on the nine
non-$A$ points, $A$'s exclusion, §13.13's support, both algebraic forms, the
block bootstrap — and step 12 is recorded as `NOT_REGISTERED_FOR_INFERENCE`
with marginal percentile intervals in its place. **No family was invented**, and
a regression asserts §15's declared members still contain no raw-coordinate
member.

**What the raw fit is licensed to do, it now does.** §17.6's coordinate-agreement
paragraph and §34 D14's closure — *"$\iota$ remains primary, raw solo secondary,
`DIFFICULTY_COORDINATE_DEPENDENT` on disagreement"* — both needed a
raw-coordinate fit, so with none in existence the status was unreachable and
D14's closure bound nothing. The comparison now returns a **status and never a
level**: a scenario drives a real disagreement, primary L3e against raw L3d, and
asserts the emitted level is still the primary's.

**Two more defects of the same class, found by wiring it.**
`run/analysis_run._strip_vectors` builds the record from an explicit key list
and dropped the replication before it reached the artifact — the same function
that had already lost §11.3/§11.7's agreement checks once. And a second
`SECONDARY_DIFFICULTY_COORDINATE` constant was defined shadowing the registered
one, which would have made two names for one registered quantity. Both repaired,
both with regressions.

**The evidence.** The two gemma behavioural chains signed under `d0485a6d…` are
**retained in full and invalidated**: each was produced under a screen whose
coverage criterion evaluated an empty set, whose $\iota_A$ came from the wrong
severity, whose §7.2 escalation refused on its first instruction, and under an
eligibility rule nobody had taken. They move under `superseded/`, which is the
path §26's reuse ledger cannot read, so no restarted stage can resume into them.

**Zero new real model generations were produced.** No signed Gate-2 record has
ever existed on any model, no reference has been selected, no freeze exists and
no confirmatory row has been generated, so §32's pre-Gate-2.5 window was open
throughout.

**One more defect, and the re-registration is what found it (V5-E29).** The
first re-qualification refused on §19's `clean_worktree` apparatus
precondition — untracked paper-drafting directories in the repository root,
which is an apparatus condition and nothing scientific — and the machinery
correctly wrote a signed `QUALIFICATION_FAILURE`. That verdict then could not
be retired: the terminal report is write-once, `assert_predecessor_passed`
refuses every stage while it exists, and `supersede_registration` moved the
stage records and left it on the live path. A replication that had terminated
could therefore be superseded and **never re-run** — the replacement
registration's first stage disabled by a verdict about the registration it
replaced. The report now moves with the records it belongs to, retained and
not deleted; the precondition is unchanged and still refuses any uncommitted
change to tracked code.

**Where v5 stands.** Closed. Manifest
`af5fa4bcfd125f936cade49cf45304737c6367b6bd7106a6ec372a6735340c98` at commit
`5ed1854` (A6 and A7 superseded `e2721b17…` in turn). All four replications
ran to a scientific end and none reached `CONFIRMATORY_GENERATION`:
`gemma-3n-e4b-it` and `qwen3-4b-instruct-2507` are terminal
`COMPOSED_HEADROOM_FAILURE`; `gemma-3n-e2b-it` and `qwen3-4b` are blocked at
`PREFREEZE_AUDIT`. Three carry irreversible D6 non-identification. 48 registered rules audited
against the path a replication takes, 48 reachable, 15 conditional scenarios,
111 contract fields with 329 checks against real payloads and 0 defects.
[`dci1/reports/dci1v5/execution_path_audit.md`](dci1/reports/dci1v5/execution_path_audit.md) ·
[`dci1/reports/dci1v5/amendment_register.md`](dci1/reports/dci1v5/amendment_register.md) ·
[`dci1/reports/dci1v5/researcher_decisions.json`](dci1/reports/dci1v5/researcher_decisions.json)

### 4y. v5 ran, and no replication reached confirmatory generation

Two bottlenecks, independent of each other, ended it.

**§12.6 C4.** C4 asks for six feature groups holding a family that straddles
$\iota_A$ with three eligible rungs spanning 0.40 in $\iota$. Three
replications got four or five. Only 14–21 eligible rungs sit *above* $\iota_A$
against 143–163 below, so most families are one-sided and cannot straddle at
all; and on every model three or four families straddle with enough rungs and
miss only on span, at 0.21–0.38. The marker families recur, their ladders being
compressed in $\iota$. C4 false drops the core and spectrum arms, which is D6
`REFERENCE_SUPPORT_NOT_IDENTIFIED`, irreversible, 48 estimand members
unidentified, and a failed mandatory `support_satisfied` prefreeze check.

**§13.14 composed headroom.** Gate 4 was marginal on *all four*, not only the
two it killed: the survivors cleared their worst cell by 0.054. $m^*$ is chosen
at Gate 2 from solo curves, and composition lifts the B slot by up to +0.104,
which is not measured until Gate 4 — after references are fixed. The two models
with the higher baseline compliance crossed 0.95 and terminated.

The one replication that survived D6 identified is one of the two that then
failed Gate 4. Neither fix would have saved the other group.
[`dci1/reports/dci1v5/survival_diagnosis.md`](dci1/reports/dci1v5/survival_diagnosis.md) ·
[`dci1/reports/dci1v5/CLOSURE.md`](dci1/reports/dci1v5/CLOSURE.md)

### 4z. V5-E32, and a follow-up that is only a proposal

`PREFREEZE_AUDIT_FAILURE` is a registered §28 terminal status that the runner
recorded in a payload field and never raised, so the two blocked replications
have no §28.3 report and report `terminal_status: None` — terminal in fact,
non-terminal on the record. An audit of all thirteen statuses in force found
exactly this one hole; the runner now raises it and an AST test asserts every
registered status is reachable. No v5 evidence was mutated or re-run (A8).

[`user-notes/DCI1_v6_proposal.md`](user-notes/DCI1_v6_proposal.md) sketches the
minimal prospective follow-up — extend the candidate library so C4 is
satisfiable, probe composed headroom before $m^*$ is fixed, relax no threshold.
**It is a proposal, not a registered protocol**, and no row may be generated
against it.

### 4aa. V6-E01: the expansion rule could not reach the reserve, and what a probe would have to absorb (2026-08-25)

The v6 readiness audit
([`dci1/reports/dci1v6/READINESS.md`](dci1/reports/dci1v6/READINESS.md), numbers
in `readiness_evidence.json` from signed v5 records) found three things.

**§12.6's expansion admits no Tier-1 reserve rung, on any replication, in
either round.** Replayed on all four signed pre-screen tables, the pick set is
empty for every marker family: a straddling family takes the bracketing branch,
whose picks lie strictly between two edges with every intervening rung already
measured; a one-sided family is one-sided *below* and the branch goes easier
while the unmeasured reserve is harder. §7.10 widened that reserve from 1..10
to 1..12 **for C4's span specifically**, and 32 rungs per replication were
never reachable. And since C4's span is `max(iota) − min(iota)` over eligible
rungs, an interpolated rung cannot raise a span at all. No v5 verdict changes;
the diagnosis narrows — part of what `survival_diagnosis.md` attributes to
library shape is the rule being unable to use the library it has.

**The v6 proposal's `delta = 0.05` is smaller than the error a probe must
absorb.** The worst B cell decomposes exactly into calibration solo at $m^*$ +
the calibration→composed split transfer + the composition term; the totals are
+0.090, +0.112, +0.126 and +0.216. Across all 13 solo slot measurements the
split transfer alone reaches **+0.189** (`gemma-3n-e4b-it`, its class reference
admitted at 0.770 on 192 calibration topics and measured 0.958 on the 24
composed topics). None of δ ∈ {0.025, 0.05, 0.075} covers it.

**A probe at $m^*$ cannot see the failure that ended `gemma-3n-e4b-it`.** Its
`solo:CL` = 0.958 is a companion slot in a solo cell, decided two stages after
the probe. And success at the library change multiplies Gate-4 exposure: the
entries audited against the hard band go 6 → 95 as arms are admitted.

Six researcher decisions are open and none is taken. Nothing is registered, no
v6 code exists, and no row may be generated.

### 4ab. V6-E02, and a v6 implementation that cannot run (2026-08-25)

Implementing the repair found the **larger half of the same defect**.
`stages/regime.run_expansion` extended its working table with the rows
`measure()` returned, and the production `measure_reserve` returned raw
`difficulty_table` rows — which carry no `eligible` field.
`coverage_criterion` filters on `eligible` before anything else, so **every
rung the expansion measured was counted as ineligible by the criterion it was
measured to satisfy.** The three replications that ran an expansion measured
93, 96 and 99 reserve rungs across two rounds; their recorded coverage was
evaluated over 174, 179 and 174 eligible rungs against 208, 211 and 229
actually measured and carried. Recomputing the registered rule over the
*pre-expansion* table reproduces each signed verdict exactly — the tool aborts
unless it does — and over the full measured table `qwen3-4b` reaches
`C4 = True` and `decisive_met = True`, where its signed record has both False.
[`dci1/tools/v6_expansion_dryrun.py`](dci1/tools/v6_expansion_dryrun.py),
[`expansion_dryrun.json`](dci1/reports/dci1v6/expansion_dryrun.json).

**This is not a re-verdict and may not be cited as one.** v5's coverage is
what v5's registered code computed over the rows that code passed it; the
record is signed, D6 is irreversible, and `qwen3-4b`'s
`REFERENCE_SUPPORT_NOT_IDENTIFIED` remains that replication's terminal
outcome. It is development evidence about the v5 *implementation*, obtained
after closure. What it changes is the diagnosis, in the same direction as
V6-E01 and further: the two defects compound — one stopped the expansion
reaching the reserve C4 needed, the other stopped anything it did reach from
counting.

**`dci1/src/dci1v6` now exists and cannot run.** Twenty-six §34 decisions are
UNRESOLVED (v5's D0–D18 plus v6's D19–D25, which are READINESS's R1–R6 plus
the single-survivor statement D22's recommended branch needs registered);
the v6 preregistration and reference-design spec are not written, so
`manifest.document_hashes` raises; and `assert_transition_legal` refuses every
stage whose decisions are open. Zero v6 rows exist. What the package carries,
each with an executable check in `protocol/revision.py`: the V6-E01 and V6-E02
repairs; `GATE_2_75_COMPOSED_PROBE` as a nineteenth stage with
`COMPOSED_HEADROOM_UNREACHABLE` as a registered terminal status; `probe_only`
instruments excluded by construction from every selectable pool; §33 check 8's
name scan extended to the probe record; L4a's configuration scope made
executable as within-replication; and **no threshold moved**, checked rather
than asserted.

**One definitional question the memo left open is closed by the registered
text, not by a decision.** §15 declares every multiplicity family per
configuration, F11 "across the two configurations of one model", and "no
cross-model multiplicity family, because this protocol licenses no
pooled-across-model estimand"; §3.2's L4b gate says "both configurations";
§11.1 says there are two configurations per model; §6.1 forbids pooling and
L5 is never licensed. So L4a is within-replication, `CONFIGURATIONS` and the
glossary agree once the model index is read as the `ModelTree`, and
`claims.assert_configuration_scope` refuses a caller who widens it.

### 4ac. V6-E03: the probe could move the operating point and nothing after it could follow (2026-08-25)

An audit of whether v6 can actually deliver a credible prospective test —
matched-companion counterfactual, reference support **and** composed headroom
surviving together on the same replication — found that v6's central repair
could not execute.

`GATE_2_75_COMPOSED_PROBE` exists so composed headroom is measured **while the
operating point can still move**, and P3.4 lets it re-select m\* once. Driving
that branch for the first time showed it ended in an unhandled
`ProtocolError`, not in a replication:

- §13.6's kappa(R|B) is a property of (R, B **at the operating point**), §13.11
  makes its source travel with the value, and `assert_kappa_under_b_source`
  refuses a table read at another m\*. That refusal is right. But Gate 2
  recorded the column at its own m\* only, so Gate 3A raised *"measured at
  m=8 and the replication's operating point is m\*=10"*. Gate 2 now records a
  column, and Gate 2.5 a §13.1 qualified pool, for **every admissible
  severity** — from B-solo cells pass 1 already scored every candidate as
  absent on, so it costs no generation — and computing them before the probe
  observes a composed cell is what keeps §30 intact: the probe's verdict moves
  the operating point and never the pool.
- §12.3's `eligible` set is a band test on the solo curve; §12.4's regime
  adequacy and §34 D17's construct floor were applied at m\* alone, so the
  probe could have moved B to a severity Gate 2 would have refused outright.
  Both are now evaluated **at** each eligible severity and the probe is
  confined to what survives. On the synthetic harness that removes two of
  eight, so the narrowing is not vacuous.
- The freeze's slot map bound `B` at Gate 2's m\* while the same record
  declared the probe's — and confirmatory generation renders every cell from
  that slot map. A re-selected replication would have spent its whole
  confirmatory budget at the severity the probe rejected.
- `licensed_design` rebuilt B with a bare `Constraint`, which the instrument
  layer refuses at §7.2's extension rungs 15 and 16. Inherited from v5, where
  it never fired because nothing escalated and nothing reached confirmatory
  generation.

`scenarios.scenario_probe_reselects_the_operating_point` now drives the branch
end to end: m\* 8 → 10, and Gate 3A, Gate 4 and the freeze all at 10.
[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) V6-E03.

**Nothing in the causal comparison moved, and that is now checked file by
file.** `revision.V9` compares the twelve modules that define Delta_R,
Delta_j, Xi, delta_difficulty, the matched-companion selection, the design
cells, the observation table, masking, the intervals, the bootstrap, §13.15's
support, §13.7's stability, §13.6's interaction guard, §13.11's closed schema
and D6's identification rule against v5's, and they are byte-identical modulo
the namespace token. Every v6 repair is upstream of estimation.

**One structural gap is recorded rather than closed.** §12.6 certifies the
coverage criterion, spends its expansion and freezes the vocabulary at
`iota_a_prescreen`; references are matched at Gate 2's `iota_a`, measured two
stages later. On the four v5 replications those differ by 0.015, 0.046, 0.073
and 0.092 — and re-reading each round-0 table at the Gate-2 value flips **no**
decisive condition on any of them. Gate 3A recorded the recomputation as
`coverage_at_measured_iota_a`, a diagnostic with no consumer that gated
nothing. **Superseded by V6-E04 (§4ad):** that reading compared an iota(R)
table measured on one sample against an iota_A measured on another, so its
number confounded the reference point with the two samples. It is replaced by
`coverage_at_calibrated_iota_a` — the same criterion on the calibration basis,
where every quantity in it is paired — and that one gates, through §34 D6's
existing disposition. Whether §12.6 should *certify* over an interval of
iota_A at the screen remains READINESS **R7** and is the researcher's.

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
- **Resolved, and the ground is on the record.** §12.6's eligibility
  predicate — open item **U4**, which blocked the v5 registration — is
  closed at **E2**: a rung is eligible when $p_{\text{solo}}(R) \in
  [0.10, 0.90]$ with the registered vacuity ceiling. §13.4 bands
  $p_{\text{solo}}$ and bands $\iota$ nowhere, so the alternative would
  have invented an absolute threshold on $\iota$. The coverage criterion
  is unchanged and still positions rungs by $\iota$. §4x.
- **Registered, not licensing anything.** §18 step 14's raw-coordinate
  replication of the §11.8 fit is computed, and step 12's simultaneous
  interval is recorded `NOT_REGISTERED_FOR_INFERENCE`: §15 gives the
  replication marginal intervals only and declares no family containing a
  raw-coordinate member. Its one consequence is §17.6's
  `DIFFICULTY_COORDINATE_DEPENDENT`. §4x.
- **Retained, and not reusable.** Every behavioural row produced under a
  *superseded* v5 registration — 478,464, under six of them —
  is preserved under `superseded/` and invalidated. Each was produced under
  a screen whose coverage criterion evaluated an empty set, whose
  $\iota_A$ came from the wrong severity, whose §7.2 escalation refused on
  its first instruction, and whose expansion could not run. The live
  evidence path under `af5fa4bc…` holds none of them, and no restarted stage
  can resume into them. Separately, the 459,312 rows produced under
  `af5fa4bc…` itself are live but **pre-confirmatory**: gate and development
  evidence only, supporting no claim about the effect. §4w, §4x, §4y.
- **Open, and most valuable next:** the boundary-affordance causal crossing; a
  pair with a genuine trade-off region; finishing the cross-model dataset on one
  backend.

### 4ad. V6-E04: development asked an easier question, and two bases were never compared on the same cases (2026-08-25)

A second audit asked what the v6 stages actually score, and whether anything
was being sampled twice. Two findings, both about measurements that existed and
were not used.

**Development was evaluating a proxy.** READINESS §7 step 3 specified a pilot
asking whether the reserve rungs land inside $p_{\rm solo}\in[0.10,0.90]$. That
is one clause of one component of §13.1's V(R), and the registered gate is a
conjunction over §13.4, §13.6, §13.7, §13.8 and §13.15's counts. A prescreen
that evaluates a proxy for the gate cannot predict the gate — which is what v5
demonstrated. §13.7's calibration, §13.8–§13.12's selection and §13.15's counts
now live in `stages/feasibility.py`, and Gate 3A, Gate 3B, Gate 3C, the
operating-point search and `tools/v6_reference_feasibility.py` all call it.
Characterization tests reproduce all four **signed v5 records** exactly.

Running the real criterion over the closed study says something the boolean did
not: on **4 of 4** replications the binding §13.15 requirement is
`min_tier1_core` — two Tier-1 core references, cleared by 0 or 1 — while the
qualified-family count clears by 6 to 7. A library extension aimed at family
count would move the requirement that is not binding.

**§12.6 was certified on one sample and re-read against another.** The
criterion is certified on the pre-screen table at `iota_a_prescreen` (24 topics,
one draw). Reference selection matches on Gate 2's `iota_a` (192 topics, four
draws). The previous diagnostic compared the *pre-screen* table against the
*calibration* $\iota_A$, so whatever it reported was part real and part the two
samples. Gate 2 measures every calibrated candidate's solo compliance, chance
compliance and vacuity on exactly the cases it measures A on, so the criterion
is now re-evaluated where every quantity in it is paired — and it **gates**: a
lost decisive condition is a §13.15 design-time failure taking §34 D6's
existing disposition. No drift threshold, no new status, and no route back to
the candidate library.

**Sampling went down, not up.** A full-slot composed-headroom stage was drafted
and deliberately **not built**: it would have been a second sample of what Gate
4 already measures, on a different topic set, carrying the very transfer error
(§4.a: mean absolute 0.064, maximum 0.189) it was meant to remove. What was
built instead reuses controlled cases — a severity that cannot muster §13.15's
five qualifying families is no longer probed at all, and the probe reads the
unconstrained cell and `solo:B` off Gate 2's record whenever the topic
identifiers and draw count are identical, which also makes the composed lift a
difference from the number m\* was selected on rather than from a second
estimate of it.

Three quantities that were in the rows and had never been read are now
recorded, all free and all read by no rule: the pre-screen↔calibration movement
per instrument (`CalibrationRow` has carried the columns since v5 and **nothing
ever filled them**), B's compliance while R is instructed, and Gate 4's
split transfer per bound instrument — the quantity §4.a built by hand.

**One defect fell out of the extraction and it is worth knowing (V6-E05).**
The characterization test that runs the extracted §13.7 kernel against the four
signed v5 records reproduced every candidate verdict and disagreed on one
summary number: `n_stable` counted `v.get("stable")` and `stability_verdict`
returns `passed`, so the count read **0 on every replication**. All four signed
v5 records say `n_stable: 0` beside 9 to 16 candidates whose own verdict says
`passed`. Nothing reads the field — it is not in the contract and has no
consumer — so no result of v5 or v6 depends on it, and v5 is not touched. A
reader of those records was being told something untrue and now is not.

`stages/feasibility.py` selects nothing and gates nothing; the stages that call
it decide. No estimand, threshold, band, margin, population or seed moved, and
`revision.V9` still checks the twelve estimand-layer modules byte-identical to
v5. Detail: `CHANGES_SCIENTIFIC.md` (V6-E04), `reports/dci1v6/READINESS.md`
§11, `reports/dci1v6/reference_feasibility.json`.

---

### 4ae. The probe protected one slot, and its margin was absorbing sampling noise (2026-08-25)

A third pass asked the two questions §§3–7 of the readiness memo had left
unmeasured: **what does Gate 4 actually audit, and how precise is it?**

**Scope.** `GATE_2_75_COMPOSED_PROBE` probed the B slot. §13.14 audits 95
cell × slot entries falling into **ten** slot-and-order classes, and the class
`gemma-3n-e4b-it` terminated in — a *companion* slot in a *solo* cell — was one
the probe could not see. The probe's shape is now derived from
`design.cells.cell_types` rather than listed: one cell per class, A and B where
the class names them and a frozen `probe_only` stand-in where it names a
companion, and `assert_probe_covers_gate4_classes` refuses a shape leaving one
uncovered. Eleven cell types become eighteen; three are read off the Gate-2
record, so fifteen are generated per severity.

**Precision, measured rather than assumed.** `tools/v6_precision_design.py`
recomputes all 73 realised Gate-4 entries from the retained rows of all four
replications, checked against the signed tables and terminal reports (21
checks, all agreeing). Three findings:

- **the calibration→composed "split transfer" is not a bias.** Observed
  variance of the thirteen realised transfers 0.00430, against 0.00515 from
  sampling alone — §6.2 cuts those sets from **one seeded per-area shuffle**,
  so they are exchangeable by construction. The one component that is not is
  §34 D3's newly authored `calibration_b`: paired by instrument, residual sd
  **0.0284**, halved to **0.0142** by pooling. That is the entire non-sampling
  error budget;
- **the topic-level ICC is 0.35**, so a fourth draw inside a topic buys little
  and only topics buy precision;
- **§13.14 fires on a replication that is in band about one time in six.** A
  joint topic bootstrap over the two replications whose entries were all inside
  the band gives 0.121 and 0.190 at the registered 24 topics.

**What changed as a result.** The margin `delta` is replaced by a **projected
Gate-4 interval** computed per entry from that entry's own between-topic
variance, at §13.4's registered level and by §13.4's own device — contract the
band, apply it to the interval. Entries whose constituents are all real
instruments gate through the projection; entries containing a stand-in gate
against §13.14's registered band with **no margin**, because no evidence bounds
the difference between a stand-in and the reference that replaces it and a
margin there would be a projection of the wrong instrument. §34 D23 is restated
as the residual allowance beyond those two measured terms, derived value 0.0.

**And one registered option turned out not to exist.** The memo recommended
enlarging §6.2's composed set 24 → 48 from the sequestered eighth. The
sequestered eighth **was never materialised in this repository** — identities
and content hashes only, texts retained outside it, and
`assert_no_materialisation` refuses a collision on every load. Enlarging is an
act of authoring topics, not a change to a constant. §13.14 stays exactly as
registered and exactly comparable with v5's Gate 4.

Three `probe_only` families are authored so the probe can run at all — library
37 → 40, verifier hash moved, no v6 record exists at the old one — and the
selectable population is unmoved at v5's 37 families, 326 round-0 and 632
declared severities, which `assert_library_sizes` now asserts as separate
counts. Detail: `CHANGES_SCIENTIFIC.md` (the three 2026-08-25 v6 entries),
`reports/dci1v6/READINESS.md` §12, `reports/dci1v6/precision_design.json`.

### 4af. The v6 decision set was audited, and two of its entries did not mean what they said (2026-08-26)

A red team of D0–D25 before adoption found two blocking defects.

**The register proposed three branches v5's researcher had rejected.**
`protocol/decisions` carried v5's *pre-adoption draft* text for D16, D17 and
D18 — `a_survivors`, `no_floor`, `not_a_precondition` — while
`reports/dci1v5/researcher_decisions.json` records `complete_population`,
`floor` and `precondition`. In all three the register proposed the **weaker**
branch, the v6 preregistration asserted the stronger one was carried, and
`budget.calibration_burden` already costed it. D17 compounds it: the floor is
one of the three conditions `focal_admissible` conjoins, so `no_floor` would
have *enlarged* the severities Gate 2.75 may re-select among.

**§34 D23 was passed into the projection as the very term it claimed to sit
beyond.** Four documents described it as an allowance beyond the measured
`RESIDUAL_SD = 0.0142`; `entry_verdict` used its value *as* that sd, so the
proposed `D23 = 0.0` would have deleted the measured term from every
determinate verdict. It is now two decisions — **D23** the reading, **D26** the
magnitude, range-checked at closure — and §34 carries twenty-seven entries.

**And δ = 0's derivation does not survive.** It established that the
calibration-to-composed transfer's *dispersion* is consistent with sampling.
What an allowance guards against is a common shift of one replication's
entries, which `precision_design.json` names and does not estimate: **+0.045**
over thirteen observations, 95% interval about (−0.025, +0.104) on the four
per-model means, against an assumed 0.0142.
[`residual_sensitivity.json`](dci1/reports/dci1v6/residual_sensitivity.json)
sweeps the grid instead — every replication retains an operating point at every
policy, so feasibility does not discriminate, but at 0.0687 all four would
re-select m\* rather than three of four keeping v5's. **No value is proposed.**

**One decision was taken** — and its reselection half was withdrawn later the
same day; see §4ag. *Focal-only reselection*: only the six determinate
entries — `solo:A`, `solo:B`, both orders of `pair:A+B` — may make a severity
inadmissible. `PS1`–`PS3` are recorded and gate nothing, so an instrument that
can never be a reference can no longer choose the operating point at which
`Delta_j` and `Delta_R` are estimated. Preregistration A13 registers it and
declares it a **loosening** of the rule it replaces.

Thirteen further entries offered alternatives with no implementation and became
acceptances; D0's `do_not_adopt` now blocks signing; D25 acquired a caller
(`tools/v6_closure.py`). At the end of this pass **v6 still could not run**:
`reports/dci1v6/researcher_decisions.json` did not exist and all twenty-seven of
D0–D26 were UNRESOLVED at import. Detail: `CHANGES_SCIENTIFIC.md`
(2026-08-26), `reports/dci1v6/READINESS.md` §13.

### 4ag. m\* is frozen at Gate 2, the decisions are closed, and v6 is adopted (2026-08-26)

**The probe may stop a replication. It may not steer one.** The researcher
withdrew the reselection half of §4af's decision. m\* is selected once, by
§12.3's focal rule on B's solo curve at `GATE_2_FOCAL_CALIBRATION`, and frozen
there; `GATE_2_75_COMPOSED_PROBE` measures composed headroom **at m\* and at
no other severity** and either passes or terminates the replication
`COMPOSED_HEADROOM_UNREACHABLE`. `Delta_j` and `Delta_R` are defined at an
operating point, so a stage that could move it from composed outcomes would be
choosing *where* the estimand is measured after §12.3 had chosen. Headroom
decides **whether** the frozen design is viable, never **where**. This is a
**tightening**: a replication whose m\* lacks composed headroom now stops where
it previously relocated. Preregistration A13; `READINESS.md` §14.1.

**And on v5's own curves it stops the replication v5's Gate 4 stopped.**
Recomputed under the frozen rule,
[`residual_sensitivity.json`](dci1/reports/dci1v6/residual_sensitivity.json)
finds one of the four closed replications' m\* failing the projection at 0.0
and at 0.0142 — `gemma-3n-e4b-it`, which v5 terminated
`COMPOSED_HEADROOM_FAILURE` at Gate 4 with every earlier gate passed — and all
four failing at 0.0687. §4af's reading, that feasibility does not discriminate,
was true of a search that no longer exists; §13.3's table is marked superseded
by §14.2 rather than rewritten.

**§34 D23 = `projection_sd` and §34 D26 = 0.0142.** The measured
authored-sub-split residual, entering the projection's quadrature as itself,
with §13.14's band exactly as registered. It is v5 DEVELOPMENT_EVIDENCE under
§30 and v6 tests it prospectively through §34 D20's measured sub-split
transfer.

**v6 is adopted.** All twenty-seven §34 decisions and all three blocking §33
items are closed on `reports/dci1v6/researcher_decisions.json`; D0–D18 carry
v5's actually adopted values with v5's own evidence and a `carried_from` block.
Both governed documents declare `ADOPTED`. **Zero v6 behavioural rows existed at
adoption.** v5's records, verdicts, terminal statuses and §34 D6 irreversibility
stand exactly as signed. Detail: `CHANGES_SCIENTIFIC.md` (2026-08-26, middle
entry), `reports/dci1v6/READINESS.md` §14.

> **Correction, same day.** This section was written at adoption and its
> heading and this paragraph originally said v6 was *registered*. It was not:
> the registration attempt that followed failed on three defects in the CLI,
> one of which wrote a §28.3 terminal report on `gemma-3n-e2b-it` for a
> readiness verdict. Registration succeeded only after amendment A15. See
> **§4ah**, which supersedes this paragraph and nothing else here — no
> scientific statement above it moved.

### 4ah. Stage 1 could refuse a study once and end a replication (2026-08-26)

**The first execution of the registered protocol could not run a single
stage**, and the third of three defects had already cost a replication. All
three were in the documented entry point:

1. the v6 CLI created no study signing key, and every record is signed at
   write;
2. it did not forward `--repo-root` to `run_registration`, whose default is
   `"."`, so `assert_documents_adopted` read the process's working directory —
   from `dci1/`, both governed documents are one level up and the guard
   correctly reported them **missing**;
3. the readiness verdict that produced was written as a §28.3 terminal report,
   and `assert_predecessor_passed` disabled `gemma-3n-e2b-it` permanently.

**It was a hole, not an inconvenience.** Every entry `signing_blockers` can
report — an open §34 decision, an unresolved §33 question, a missing topic
hash, an unapproved candidate population, an unspecified floor, an unpinned
model revision, a non-derivable design, a draft document — names work a
*researcher* has to do, and `decisions.choice()` had always said stage 1
returns `REGISTRATION_INCOMPLETE` **until then**. If the first invocation to
find any of it outstanding kills the replication, "until then" is false and the
whole vocabulary is unreachable by construction.

**Amendment A15.** §18 stage 1's `REGISTRATION_INCOMPLETE` is a readiness
refusal, not a §28 terminal status: it fails closed, writes no record and no
terminal report, logs a `REFUSED` transition carrying the blockers, and leaves
the replication retryable. The two vocabularies are disjoint, asserted at
import, and three structural refusals keep the change from spreading to a
scientific gate. **The criterion is untouched** — `signing_blockers` decides
readiness exactly as it did, and every §28 terminal outcome is as irreversible
as it was. Declared under §32.2 as adopted after adoption and before any
behavioural row; preregistration §A15, `READINESS.md` §15.

**The record already written is retained.** `retire_apparatus_fault` moves it
byte-identical under `superseded/apparatus_fault/<record hash>/` in both roots
and refuses six ways — a hash mismatch, an unverifiable signature, any gate but
stage 1, any §28 status, an existing manifest, any behavioural row anywhere in
the study. The registration signed afterwards binds the retirement in its own
payload. Nothing about the incident reads as though it did not happen:
`dci1/reports/dci1v6/incidents/2026-08-26_stage1_apparatus_fault.md`.

**Nothing scientific moved.** No threshold, estimand, criterion, population,
model, reference family, arm, seed, verifier, wording, claim ladder or headroom
band; not m\*; D23 stays `projection_sd` and D26 stays 0.0142; §6.1's four
replications are four. Zero v6 behavioural rows existed at any point in this.

**v6 is registered.** All four replications hold a signed
`PROTOCOL_REGISTERED` record under one manifest, at producing commit
`c59fa75508ea3c055b31f9ec1d7e53220389bd6c`:

| binding | value |
|---|---|
| manifest hash | `36f1fb3b6dfcedeadc2cd8cbaa4832204148c6851bd6dd5dd5c5a9eada7c5662` |
| preregistration | `sha256(path+bytes) = 95db6df44f7c9b1f9233509cf64ff77d9671921d6c67755b298628e6d186cd4c` |
| reference-design spec | `sha256(path+bytes) = c532279edaf38f84454009b26005da4fe9740e5c800a9f824f60fa1770ab3eee` |
| decision record | `eefb32513b4f1095d83e4912abfe806c0220071f153413470faeb93ec3c5d482`, 27 closed, 0 open |
| retired apparatus fault | `fb9b4353b50ec2221b6a1de33465427ae3ab3a4aac81189645e5520711ed6122`, bound in the manifest |
| topic split | `c10f17bc5846e1858705af3c8daa21c450b1c63f00618ce0d414181fc8861f10` |

**Zero v6 behavioural rows existed at the moment of registration**, verified by
counting `rows.jsonl` under both roots.

### 4ai. §12.6 had no rule for a rung with no difficulty coordinate (2026-08-26)

**The first v6 measurement broke the stage that reads it.**
`GATE_0_APPARATUS` passed on all four replications — 2,688 real rows each, both
discrete cards at TP=1. `REGIME_SCREEN` then died on both replications that ran
it, identically, on `tie_key(r["iota"])` in §12.6's coverage criterion:
`CR7:56`'s measured chance compliance had reached `CHANCE_DEGENERACY_MAX =
0.99`, the registered point at which iota is undefined and §11.2 records
`DIFFICULTY_COORDINATE_DEGENERATE`.

**Latent since v5, byte-identical code.** U4 resolved at **E2**, whose
eligibility coordinate is raw solo compliance — so a rung can be eligible on a
measured solo and have no position on the iota axis at all. Under **E1** the
coordinate *is* iota and the case cannot arise. v5 ran E2 too and never met it:
all its coordinate-less rungs had solo above 0.9166 and were ineligible for a
different reason. Of the eighteen coordinate-less rungs the two v6
replications measured, exactly one per replication is E2-eligible
([`degenerate_iota_rungs.json`](dci1/reports/dci1v6/degenerate_iota_rungs.json)).

**Amendment A16.** §12.6 evaluates C1–C8 over the eligible rungs whose
coordinate is defined; a rung without one is dropped from every condition and
recorded with its status, solo and chance. U4 is not reopened and §13.4's
chance ceiling is not imported into §12.6. Declared under §32.2 as adopted
after this observation, with the offending measurements already readable.

**Why that direction could be adopted after the fact.** Every one of C1–C8 is
an existence or a count, so removing a rung can only make a condition harder to
meet. The rule cannot be what buys a replication a pass, whichever rungs turn
out degenerate; the alternative reading — keeping the rung in the counts that
do not reference iota — is the direction that could, and is rejected for that
reason rather than for what either produces. A test asserts the property
executably.

**What it returned.** Both replications: `REGIME_SCREEN` PASS, **all eight
conditions met**, no identification status, one rung dropped (218/219 and
212/213 eligible rungs placed), cap 512, 410 and 404 rungs carried. The drop
changed no verdict on either — stated because it is the honest reading, not
because it was the aim.

**No model output was regenerated.** The corrected criterion ran on the rows
the failed run had already signed onto the evidence tree; every `rows.jsonl`
verified byte-identical afterwards and no new backend run directory was
created. Detail: `CHANGES_SCIENTIFIC.md` (2026-08-26, first entry),
`reports/dci1v6/READINESS.md` §16,
`reports/dci1v6/incidents/2026-08-26_regime_screen_undefined_iota.md`.

### 4aj. A probe stand-in had no admissible severity, and ended the stage (2026-08-27)

**The study's first composed probe refused.** `GATE_2_75_COMPOSED_PROBE` on
`gemma-3n-e2b-it`, at the frozen m\* = 10, raised a `ProtocolError`: no
severity of the stand-in `PS1` has solo compliance inside §13.4's [0.10, 0.90]
on that replication. PS1's measured ladder is 0.0 at severities 1–6, 0.0833 at
7 and 0.0417 at 8 — it is `exact_count` (*"exactly q words that use a capital
letter"*), hard by construction, and the model essentially never hits it. The
instrument is sound: §19's witness suites certified all 674 instruments at
qualification.

**The gap.** A5 registered *where* a stand-in is placed and not what happens
when no severity is placeable. PS1–PS3 are new in v6 and no v5 rows exist for
them, so placeability had never been measured. Meanwhile the stage's own
declared refusals — `no_standin_entry_ends_a_replication`,
`standin_findings_gate_nothing` — say a stand-in decides nothing, and a hard
raise let an unplaceable `probe_only` instrument end the stage.

**Amendment A17.** `STANDIN_UNPLACEABLE` for the stand-in, with its ladder and
reason recorded; `NOT_MEASURED_STANDIN_UNPLACEABLE` for every cell requiring
it, not generated and not entering the feasibility verdict; the stage
continues on the genuine determinate entries at the frozen m\*. Neither status
is terminal. **The set that cannot be measured and the set that could never
have entered the verdict are the same set** — A13 made the verdict
determinate-only, and a test asserts it over the whole cell shape. What is lost
is diagnostic breadth, and the record names it. Declared under §32.2: written
after the refusal, with PS1's ladder already measured.

**No model output was regenerated** — the 576 ladder rows were reused and
verified byte-identical. Detail: `CHANGES_SCIENTIFIC.md` (2026-08-27),
`reports/dci1v6/READINESS.md` §17,
`reports/dci1v6/incidents/2026-08-27_standin_unplaceable.md`.

---

### 4ak. v6 closed with zero survivors, and v7 withdraws the composed-headroom criterion (2026-08-27)

**All four v6 replications reached a §28 terminal status within a day of
A17, and none reached confirmatory generation.** Both Qwens at
`GATE_2_75_COMPOSED_PROBE`, `COMPOSED_HEADROOM_UNREACHABLE`: at the frozen m\*
B's compliance **rose** under A — from a solo 0.747 to 0.891 (`pair:B+A`) on
`qwen3-4b`, and from 0.779 to 0.875/0.924 on the 2507 checkpoint — and the
projected Gate-4 interval crossed 0.95, while A's own compliance under B fell
by 0.2–0.35. `gemma-3n-e4b-it` at Gate 4, `COMPOSED_HEADROOM_FAILURE` on
`solo:CL` = 0.958, the broad-class control's own solo compliance on 24 topics,
against a calibrated 0.686. `gemma-3n-e2b-it` passed Gate 4 with every entry
inside the band and terminated at `PREFREEZE_AUDIT`: the preregistration on
disk was not the one registered — A16 and A17 had edited it, correctly and
with disclosure, after rows existed — and v6 had no mechanism to bind a
post-registration amendment (`supersede_registration` needs zero observations,
`retire_apparatus_fault` needs zero rows). Both Gemmas had recorded
`REFERENCE_SUPPORT_NOT_IDENTIFIED` at Gate 3C under V6-E04's calibrated
re-read, so `Delta_R` was unidentified on both before Gate 4 ran. The closure
record is `dci1/reports/dci1v6/closure.json`; the reading is `CLOSURE.md`; the
audit incident is `incidents/2026-08-27_prefreeze_protocol_hash.md`. **Every
verdict stands and no v6 record was edited.**

**What the audit of the criterion found.** Neither v6 gate computed a
contrast. Gate 4 tested every cell × slot compliance against [0.05, 0.95]
independently; Gate 2.75 projected each determinate entry forward and tested
the projection against the same band. The estimand is a paired within-block
contrast between composed cells, and a rate near 0 or 1 in one arm is a
property of that arm — it does not make a difference of rates undefined. A
delivery **gain** on the treated arm is a measurement of `D(B<-A)` with a
sign, and under the criterion it was a reason to stop measuring.

**v7 is a superseding registration, drafted and not adopted.** A v6 amendment
is illegal under v6's own §32.3 (§13 frozen from the first Gate-2.5 record;
all four hold one) and §32.1 (never weaken a criterion so that a gate passes;
three replications terminated on this one). `dci1/src/dci1v7/` is v6's package
re-namespaced with nine enumerated, executable changes (`protocol/revision.py`
V1–V9), and `user-notes/DCI1_preregistration_v7.md` incorporates v6's document
by hash and states every difference:

- **A1.** The criterion is **withdrawn**, not relaxed. Both statuses leave
  the terminal vocabulary; the converse of A8 is asserted — no module can
  raise either. Gate 2.75 and `GATE_4_COMPOSED_CONTRAST` have one outcome each
  and record. Eleven terminal statuses remain, none about a composed rate.
- **A2.** New §13.14 (`analysis/boundary.py`), one function run at Gate 2.75,
  Gate 4 and the unmasked analysis: a **structural zero** (every differenced
  cell at the same exact boundary) licenses nothing; an **arm at a boundary**
  widens the decision interval, open side only, by the Wilson half-width at
  the block count (0.0099 at 384); a **compressed direction** (an arm above
  1 − SESOI or below it) is named on the statement with the arm that closes
  it. Licensing rules read the widened interval as registered. `Delta_R`'s
  direction is a named outcome. Gate 4 forms every registered contrast by the
  confirmatory estimators on its 24 topics, bootstraps them with §17.1's
  construction, and records each member's reading and projected precision;
  the freeze binds it. No precision gate is added.
- **A3.** §26's Gate-4 clause is restated on the estimand.
- **A4.** A post-registration amendment is bindable: a signed, append-only
  chain from the registered hashes, with the stage reached and row count per
  replication, the declared direction and the §32.2 disclosure; the pre-freeze
  audit and the freeze read its head; §32.3 refuses §13 executably.
- **A5.** §34 D23 and D26 withdrawn with their consumer; D27 added; 26
  decisions, all open until the researcher closes them.

**No threshold moves** (`revision.V8`); **the estimand layer is byte-identical
to v6's** (`revision.V9`); `dci1v6` is a foreign study to v7 and its records
enter only as `HISTORICAL_OUTCOME` and `DEVELOPMENT_EVIDENCE`. Withdrawing the
criterion opens nothing for the Gemmas — their Gate-3C non-identification is
§34 D6 and irreversible — and opens the Qwens' path to Gate 3, where §13's
unchanged machinery decides whether a reference set exists. Detail:
`CHANGES_SCIENTIFIC.md` (2026-08-27, first entry), `dci1/reports/dci1v7/READINESS.md`.

*(Corrected by v7 A8, 2026-08-28 — §4an. "Opens nothing for the Gemmas" conflated Δ_R's irreversible non-identification with the end of the replication; §34 D6 registers that a non-identified replication continues on its base and class arms, which v6's and v7's pre-freeze check prevented and A6 restores.)*

### 4al. The v7 boundary machinery audited statistically; the structural-zero veto withdrawn (2026-08-28)

Before adoption, §13.14 was audited for the validity of the *rule* rather than
of the implementation: `dci1/tools/v7_boundary_audit.py` ran the production
interval procedure — the registered estimators, `bootstrap_family` at 10,000
resamples with the F1 studentised maximum-modulus critical value, the boundary
reading and its allowance, `claims.delta_r_reading` — on 39,000 simulated
paired 384 × 8 experiments across 39 data-generating processes (interior,
0.90–0.9995, exact 0/1 on one or both arms, clustered blocks, true effects
from −0.30 to +0.30), with sensitivity runs at independent draws and at heavy
clustering, deterministic sign checks, and a consumer-by-consumer trace of
the Gate 4 and Gate 2.75 records.
`dci1/reports/dci1v7/boundary_audit/DECISION_MEMO.md`.

**Findings.** The decision interval for $\Delta_R$ covered the true contrast
in 97.6–100% of experiments in every baseline scenario and in 95.2–100%
under a heavy-clustering stress run; the one-member calibration is 0.93–0.95
in the interior and no worse at any boundary, with one recorded limitation
that is not the boundary rule's: a near-ceiling arm whose failures sit in a
handful of blocks under-covers at the one-member level (0.89–0.93), and the
registered interval is held at nominal there by the F1 family inflation. **The Wilson allowance
is necessary and is kept:** without it, family simultaneous coverage falls to
0.905–0.929 whenever a cell sits at an exact boundary, and with it every such
case recovers to 0.941–0.968, at a width cost ≤ 0.02 that moved no verdict.
**The structural-zero veto was not a safeguard and is withdrawn (V10):** at a
shared exact boundary the allowance interval $\pm 0.0099$ is a valid
$\geq 95\%$ interval by construction (1,000/1,000 in every such process), an
equivalence false positive there needs all 3,072 draws perfect while
$|\Delta_R| \geq 0.10$, and the veto made 3,072/3,072 perfect draws license
less than 3,071/3,072. A structural zero is now read on its allowance
interval like any other reading — no direction by construction, L3c at 384
blocks, nothing at Gate 4's 24 topics — carrying the status and a registered
sentence that the excess is bounded, not measured; §26's `NOT_MET` for a
Gate 4 structural zero is unchanged. **Gate 4 is non-adaptive:** no consumer
of its record feeds reference choice, severity, m\*, n\*, order, model, the
admitted set, the sample size or whether the confirmatory arm is generated;
the freeze now binds m\* through the checked Gate 2 = Gate 2.75 equality
rather than a copy of the probe record's field. **Sign convention verified**
end to end: $\Delta_R > 0$ is `A_HARMS_MORE`; L3c is one-sided by
registration and is read, with `A_COMPARATIVELY_BETTER` on the statement,
when A is better than its references. No threshold moves. Detail:
`CHANGES_SCIENTIFIC.md` (2026-08-28).

### 4am. v7 adopted, registered, and executed as the prospective confirmatory study (2026-08-28)

**Adopted.** On the researcher's instruction of 2026-08-28 the v7 draft — as
revised by the boundary audit (§4al, V10) — was adopted without any further
change to a registered rule. `dci1/reports/dci1v7/researcher_decisions.json`
closes all twenty-six §34 decisions and the three blocking §33 items: D0–D22,
D24 and D25 re-taken at the values v6's researcher adopted, each with a
`carried_from` block naming v6's record (and through it v5's), and D27
(retain the probe as a recording stage, A5) on v7's own evidence; D23 and D26
are withdrawn with their consumer (A5). Every proposal value was checked one
by one against v6's adopted record before being re-taken. Both governed
documents declare `ADOPTED`, the reference-design spec derives `ADOPTED`,
`CLASSIFICATION` moved, and `plan_registration` reported `can_register` with
zero blockers. Validation on the adopted tree: `tests_v7` 642 passed,
`tests_v6` 613 passed, the producer/consumer contract current at 169 fields
and 0 defects. Adoption commit `ed0446f`.

**Registered.** All four replications hold a signed `PROTOCOL_REGISTERED`
record under one manifest, at producing commit
`ed0446ff58d0efc70b7703c162997863a9530768`:

| binding | value |
|---|---|
| manifest hash | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` |
| preregistration | `sha256(path+bytes) = 15fa1786ffbd536253464a486e78f85e338514094e8b8e24df32cdb7c00b82dc` |
| reference-design spec | `sha256(path+bytes) = 110170d7514f2d1aa20ec2f7a5d33c1f0e4c650f6b683fa301407e9b018708db` |
| decision record | `82660e5fb2ca398b0240cb5d9b0aefdb91c6fec34e9496bcba5b50fa00354de3`, 26 closed, 0 open; U2 = A2, P1 = confirmed, U4 = E2 |
| revision changes | V1–V10, 10 of 10 checked and realised |
| topic split | `c10f17bc5846e1858705af3c8daa21c450b1c63f00618ce0d414181fc8861f10` |
| amendment chain | empty; `registration/amendments/` is the append-only location the freeze binds (A4) |

**Zero v7 behavioural rows existed at the moment of registration**, verified
by counting `rows.jsonl` under both roots. v6's evidence enters nowhere:
`dci1v6` is a foreign study to v7 and no v6 record satisfies a v7 stage.

**Execution.** `dci1/tools/run_v7_replication.sh` drives one replication
through §18's nineteen stages in registered order on one card, asking the CLI
for the next stage and stopping only where the lifecycle stops — a §28
terminal report, or `FINAL_REPORT` written. Two replications share each RX
7900 XTX as two independent TP=1 lanes (`gemma-3n-e2b-it` and `qwen3-4b` on
card 0, `gemma-3n-e4b-it` and `qwen3-4b-instruct-2507` on card 1); the
backend's per-device flock is the arbiter. Nothing in the driver reads an
outcome or passes an argument that changes what is measured. Per-replication
outcomes are recorded here as they are reached and closed in
`dci1/reports/dci1v7/closure.json` at the end.

**Executed and closed, 2026-08-28.** The four drivers ran from 05:04 to
17:31 UTC. Every replication passed `QUALIFIED`, Gate 0, the regime screen,
Gate 1, Gate 2, Gate 2.5, **the composed probe** (both Qwens, where v6 ended
them: B under A 0.88 / 0.78 on `qwen3-4b` and 0.92 / 0.60 on the 2507
checkpoint against solo 0.77–0.78, recorded, the second as a compressed excess
direction), Gates 3A–3C and **Gate 4** (both Gemmas, where v6 ended
`gemma-3n-e4b-it`). None reached the freeze:

| replication | m\* | last stage | terminal status | Δ_R |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | 10 | `GATE_4_COMPOSED_CONTRAST` (base + class) | `PREFREEZE_AUDIT_FAILURE` — `support_satisfied` | not identified (C4: 2 straddling groups of 6) |
| `gemma-3n-e4b-it` | 9 | `GATE_4_COMPOSED_CONTRAST` (base + class) | `PREFREEZE_AUDIT_FAILURE` — `support_satisfied` | not identified (C4: 4 of 6) |
| `qwen3-4b` | 12 | `GATE_4_COMPOSED_CONTRAST` (base) | `PREFREEZE_AUDIT_FAILURE` — `support_satisfied` | not identified (C4: 5 of 6) |
| `qwen3-4b-instruct-2507` | 11 | `GATE_4_COMPOSED_CONTRAST` (base) | `PREFREEZE_AUDIT_FAILURE` — `support_satisfied` | not identified (C4: 4 of 6) |

**One condition ended all four, and it is upstream of everything v7
changed.** §12.6's decisive coverage condition C4 was certified on the
24-topic pre-screen and lost on the 192-topic calibration basis (v6 A3's
paired re-read) on every replication, with §13.15's own counts met on every
replication (3 core references, 11–12 qualified families, 2 backups). Gate 3C
recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` under §34 D6 and dropped the
core and spectrum arms; the pre-freeze audit's mandatory `support_satisfied`
check — support *met*, not recorded — then refused the freeze, as it did on
v5's two D6 replications and v6's `gemma-3n-e2b-it`. The withdrawn headroom
criterion would have ended nothing that reached it. No `Delta_R`, `Delta_j`
or `Xi` is identified on any model; the study makes no claim about the
effect at any level (`dci1/reports/dci1v7/closure.json`). **Standing tension
for the researcher, not amended mid-study** *(resolved the same day by A6–A8,
§4an; retained as written on closure)***:** §13.15's prose and D6's closure
say a non-identified replication continues to the freeze with its base-arm
estimands, while `support_satisfied` makes it terminal one stage later, so
D(B←A), D(A←B) and Λ have never been generated confirmatorily on any
replication of v5–v7. The execution-path audit's non-identification scenario
stops at Gate 3C and never exercised the audit. Reading:
`dci1/reports/dci1v7/CLOSURE.md`; numbers: `replication_summary.json`; logs:
`execution_logs/`.

### 4an. v7 amended in place after the closure: D6 reaches the freeze, C4 gates the spectrum (2026-08-28)

**What the diagnosis found.** All four v7 replications passed Gate 4 and
terminated at `PREFREEZE_AUDIT` on one mandatory artifact check,
`support_satisfied`, implemented as `bool(support_met)` — "§13.15 was met"
— against a registration that says the opposite four times over (§13.15,
§18 stage 10, §28.2, §34 D6 closed at `identification_status`: "the
replication continues"). The check's own description said "recorded". The
same check had ended two v5 and one v6 replication; each closure read it as
correct because "Δ_R is irreversibly not identified" was read as "the
replication ends". The execution-path audit's D6 scenario stopped at Gate 3C
and never walked the audit. And the condition that made §13.15 "unmet" was
never §13.15's own counts — all met on all four — but §12.6's **C4** on the
calibrated basis (5 / 4 / 2 / 4 straddling groups against 6), a
within-family-span condition whose registered rationale is §13.12's
spectrum triples, while C1/C3/C5/C6 held and three core references sat
within 0.017 of ι_A. §13.12 and §8.1 already registered that a family that
cannot straddle costs the spectrum, not the core; §12.6 said both. The
pre-screen certificate of C4 (24 topics × 1 draw) is noise-inflated, trimmed
by the 0.90 ceiling at calibration and padded by Tier-3 ladders that §12.7's
cap removes from the calibration table.

**What was done, on the researcher's instruction, as an in-place v7
amendment under §32 and A4's chain (no v8).** A6: the pre-freeze audit
establishes the *record* — `support_recorded`, `d6_disposition_registered`
(disposition = D6's closed value; the `non_identification` block irreversible
and naming exactly the derived set), `arms_match_identification` (every
unsupported arm absent, every supported arm retained, base always present),
`no_rehabilitation_path`, `freeze_fields_explained` (the §18.1 record
assembled unwritten) — and the reference-specific checks are
`NOT_APPLICABLE` when the core arm is absent. A7: C1/C3/C5/C6 gate the core
arm, C2/C4 gate the spectrum arm; a lost C2/C4 with the core conditions met
is `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` with the spectrum-dependent members
(20 of the 48) on their own irreversible block, and the core arm and Δ_R
stand when §13.8, §13.7 and §13.15 hold; C4's numbers do not move. A8: D6's
meaning stated once; the conflating sentences in v7 §3/§5/§8, READINESS
§4.3 and §4ak corrected with markers; the base arm asserted unconditional.
`protocol/revision.py` V11–V13 check each; the estimand layer is compared
against v6 with the two amended functions excluded by name and the
identification rule compared on its derived sets (V9).

**Verified.** The D6 scenario now runs the production path from a signed
prefix to `FINAL_REPORT` under a calibration with no matched companion
(base arm only: D(B←A), D(A←B), Λ `IDENTIFIED`, Δ_R `NOT_IDENTIFIED`
irreversibly, pre-freeze `PASS`), and a second scenario reproduces v7's own
shape — C4 lost alone on the calibrated basis — with the core arm retained,
Δ_R `IDENTIFIED` and δ_diff `NOT_IDENTIFIED`; four further scenarios pin
the full design, the unconditional base arm, both blocks' refusal of a later
estimate and the conditional audit checks. `tests_v7/test_d6_continuation.py`
and `test_identification_scope.py` carry them into the suite; the signed v5
Gate-3C records still reproduce. The first walk also exposed one latent
analysis defect (an empty §11.8 ladder built for a design without the nine
spectrum slots crashed the identity check), fixed in
`analysis_run.spectrum_inputs`. `CHANGES_SCIENTIFIC.md` (2026-08-28,
"amended in place").

**What did not change.** The four v7 terminal reports, the v6 and v5
verdicts, every threshold, the calibrated basis, the estimands, D6's value.
Whether replications are re-run under the amended v7 is the researcher's
decision and no lifecycle path re-opens a terminal tree.

**One registered tension found and left standing (frozen §13).** §13.7
condition 1 folds $V_{\text{diff}}$ into $V_{\text{stab}}$ for every
candidate, and §13.12 exempts spectrum rungs from $V_{\text{diff}}$; read
together, a spectrum rung is selectable only inside the 0.10 caliper, so
§13.12's ±0.20 targets are unreachable and the difficulty relation is
fitted over a compressed range (`gemma-3n-e2b-it`'s real triples: within
0.08 of ι_A). §32.3 refuses a §13 amendment after Gate 2.5; recorded for
v8, and the full-design scenario is built to the rule as registered.


### 4ao. The §13.11 chance column had been zero on every replication; corrected on the Gate-2 producer, outside §13's pin (2026-08-29)

**What was found.** Every candidate row of every §13.11 calibration table
written by v5, v6 and v7 — and by every development rehearsal started
before this date — carried `chance_compliance = 0.0`. The producer asked
`instance_rates` for a candidate no grid row states, the call raised, and
the fallback was written. §11.2 and §13.2 register κ_c as the candidate's
compliance in the **unconstrained cell** of the same topic set at the same
M; Gate 2's grid runs generate exactly that cell on every calibration block,
with every carried candidate scored absent on it, and the column never read
it. Reproduced on the registered `qwen3-4b` Gate-2 rows: the recorded column
is `{0.0}` on all three splits, `instance_rates` raises `no rows for MK1:1
(present=True…)`, and `cell_rates(..., arm="unconstrained")` on the same
rows gives 0.0475 for that candidate.

**What it meant while it was zero.** ι(R) was raw solo compliance beside a
chance-corrected ι_A; H_R was p_solo; §13.4's chance ceiling could not fire;
§13.6's displacement was measured against zero (which also *rejected*
candidates whose κ^B_R sat within 0.25 of a real κ_R); §13.8's caliper,
§13.7's ι bootstrap and §12.6's calibrated re-read all ran on the
uncorrected coordinate. Δ_R itself differences composed cells and reads no
κ_c, so a Δ_R estimate is affected only through *which* references were
selected.

**What was done, and where.** `revision.V9` pins twelve estimand-layer
modules byte-for-byte against v6, and two of them (`stages/stability`,
`stages/selection`) read `.iota` on every row — which raises at κ ≥ 0.99 —
so the correction lives upstream of the pin, on the Gate-2 producer: κ_c is
measured on the grid runs' unconstrained cells per split by the one
`cell_rates` every chance rate uses (192 topics × 8 independent draws on the
pooled table), the denominator is named on the record (`chance_basis`), a
split with no unconstrained cell or a different topic set refuses, and a
candidate whose κ_c reaches `CHANCE_DEGENERACY_MAX` is **withheld** from the
table §13 reads and recorded with its values (`calibration_rows_withheld`,
`DIFFICULTY_COORDINATE_DEGENERATE`; §11.2, and v6 A16's rule on the
calibrated basis — the re-read still counts it under `coordinate_undefined`).
The record seam `feasibility.calibration_rows_at` refuses a table carrying a
degenerate row. `V14` checks it; the contract, the audit ledger and
`tests_v7/test_chance_basis.py` carry it. No pinned file changes a byte, `V9`
still passes, no threshold moves (`V8`); `stages/validity.py` and
`stages/qualification_gate.py` are not pinned and were not changed.

**Measured on the stored tables** (read-only recomputation through the
production kernels; `dci1/tools/v7_chance_basis_impact.py`,
`dci1/reports/dci1v7/chance_basis_impact/REPORT.md`):

| tree | model | m\* | candidates | κ>0 | >0.75 | withheld ≥0.99 | qualified rec→cor | flipped | core references (R1–R3) | κ_c of the recorded core refs | class control (CL) | arms rec→cor | kernels reproduce the signed records |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---|---|---|
| v7 | `gemma-3n-e2b-it` | 10 | 132 | 45 | 8 | 0 | 76→74 | 4 | **changed** {'R1': 'MK4:8', 'R2': 'MK1:1', 'R3': 'XC3:10'} → {'R1': 'MK4:8', 'R2': 'MK1:1', 'R3': 'MK2:7'} | MK1:1 0.003, MK4:8 0.000, XC3:10 0.007 | **changed** RF12:6 → CR5:2 | unchanged ['base', 'core', 'class'] | Gate 3C predates A7, not compared |
| v7 | `gemma-3n-e4b-it` | 9 | 140 | 44 | 6 | 0 | 84→84 | 8 | unchanged | MK4:7 0.000, MK5:6 0.000, MK6:3 0.000 | **changed** RF12:7 → RF9:12 | unchanged ['base', 'core', 'class'] | Gate 3C predates A7, not compared |
| v7 | `qwen3-4b` | 12 | 112 | 42 | 8 | 1 | 49→48 | 1 | unchanged | MK1:6 0.000, MK6:8 0.000, MK7:2 0.000 | — | unchanged ['base', 'core'] | Gate 3C predates A7, not compared |
| v7 | `qwen3-4b-instruct-2507` | 11 | 112 | 46 | 9 | 0 | 44→43 | 1 | unchanged | MK1:7 0.000, MK3:3 0.000, MK4:5 0.000 | — | unchanged ['base', 'core'] | Gate 3C predates A7, not compared |
| v6 | `gemma-3n-e2b-it` | 10 | 134 | 50 | 5 | 1 | 78→73 | 9 | **changed** {'R1': 'XC3:10', 'R2': 'MK4:8', 'R3': 'MK2:8'} → {'R1': 'MK5:7', 'R2': 'XC3:10', 'R3': 'MK4:8'} | MK2:8 0.000, MK4:8 0.000, XC3:10 0.005 | unchanged CR5:1 | unchanged ['base', 'core', 'class'] | Gate 3C predates A7, not compared |
| v6 | `gemma-3n-e4b-it` | 9 | 132 | 47 | 9 | 0 | 74→71 | 5 | unchanged | MK1:6 0.000, MK4:8 0.000, MK5:6 0.000 | **changed** RF12:7 → None | **changed** ['base', 'core', 'class'] → ['base', 'core'] | Gate 3C predates A7, not compared |
| v6 | `qwen3-4b` | 12 | 112 | 42 | 5 | 1 | 50→50 | 0 | unchanged | MK1:3 0.000, MK5:2 0.000, MK6:7 0.000 | — | unchanged ['base', 'core'] | yes |
| v6 | `qwen3-4b-instruct-2507` | 11 | 119 | 50 | 14 | 7 | 43→43 | 0 | unchanged | MK5:6 0.000, MK6:8 0.000, MK8:4 0.000 | — | unchanged ['base'] | yes |
| v7-development | `qwen3-4b` | 12 | 112 | 43 | 7 | 0 | 50→49 | 1 | unchanged | MK1:7 0.000, MK6:8 0.000, MK7:2 0.000 | — | unchanged ['base', 'core'] | yes |
| v7-development-r3 | `gemma-3n-e2b-it` | 10 | 112 | 42 | 9 | 0 | 64→60 | 6 | unchanged | MK1:1 0.004, MK2:7 0.000, MK5:8 0.000 | **changed** RF12:6 → None | **changed** ['base', 'core', 'class'] → ['base', 'core'] | yes |
| v7-development-r3 | `qwen3-4b` | 12 | 112 | 43 | 9 | 1 | 52→51 | 1 | unchanged | MK1:6 0.000, MK6:8 0.000, MK7:2 0.000 | — | unchanged ['base', 'core'] | yes |

Read: on every replication 42–50 candidates carry a non-zero κ, 5–14 sit
above §13.4's ceiling and had passed `V_chance` trivially, 0–7 are
degenerate and withheld; §12.6's calibrated C1–C8 verdicts and "core met,
C4 lost" are unchanged on every v7 replication, so no terminal verdict's
basis moves; the core reference set changes on `gemma-3n-e2b-it` (v7 and
v6: `XC3:10`'s κ = 0.007 re-orders the third-nearest family by 0.003) and on
no other; the broad-class control (`RF12`, satisfied unprompted 0.2–0.5 of
the time on the Gemmas) moves or disappears on four; qualification flips
0–9 candidates in both directions. The completed `qwen3-4b` development
rehearsal's three references have κ = 0.000 and are re-selected unchanged,
so its Δ_R reading (−0.0009 / +0.0144, a development number) stands; so do
r3 `qwen3-4b`'s and r3 `gemma-3n-e2b-it`'s core-arm rows, while the
latter's class companion (`RF12:6`) is not one the corrected rule admits.

**What did not change.** Every stored record, every verdict, the four v7
terminal reports, the registered rules and thresholds. Tables from before
this date are not comparable number for number with tables after it
(`CHANGES_SCIENTIFIC.md`, 2026-08-29 "in force"). Rehearsals under the
corrected code go into fresh development roots
(`dci1/reports/dci1v7/development_rehearsal/README.md`). **One related
discrepancy is reported and left standing:** ι_A on the Gate-2 record uses
A's chance over every A-absent grid-A row (the unconstrained cell and the
other target severities' solo cells) rather than the unconstrained cell
alone; the two ι_A values differ by +0.002 to +0.007 on three models and
by +0.025 (v7) / +0.026 (v6) on `qwen3-4b-instruct-2507`, a quarter of
§13.8's caliper; moving it is a researcher decision.

### 4ao. Development-only diagnosis of the v7 difficulty spectrum: C4's causes, and a wording-parse artefact inside the exact-count instrument (2026-08-29)

**Not a change to v7; nothing registered, frozen or re-run; no GPU used.**
Branch `dev/v7-difficulty-spectrum` (worktree `../dci-v7-spectrum-dev`, from
the unmerged chance-basis fix `7f89dae`), report
`dci1/reports/dci1v7/difficulty_spectrum_dev/REPORT.md` with its
`SAFETY_AND_ISOLATION.md`. Read-only over the four registered v7 trees on
the corrected κ_c basis, with the production kernels (the reconstruction
reproduces the signed Gate-3A C1–C8 verdicts on every model).

**C4 fails for a different reason on each model** (2 / 4 / 5 / 4 groups of
6): `gemma-3n-e2b-it` — the exact-count ladders are flat or floored
(MK2/MK4 span 0.32 over twelve rungs; A's own solo curve is 0.43–0.62 over
n = 1..8); `gemma-3n-e4b-it` — ι_A = 0.725 sits above the easy end of
every family that is not already a group; `qwen3-4b` — the [0.10, 0.90]
band trims the easy rungs and the middles are flat (MK2 misses 0.40 by
0.009); `qwen3-4b-instruct-2507` — the ladder 1..8 is too easy (28
Tier-1/2 rungs above 0.90) and the reserve was never generated because the
24 × 1 pre-screen (ι_A_pre 0.666 vs calibrated 0.540) certified ten groups.
Correction to the 2026-08-29 landscape diagnostic: §12.6's expansion **did**
run on both Gemmas (one round, MK2/MK4/MK5/MK7 at q = 9–12 calibrated); it
did not on the Qwens. Local Δ_R support is dense on three models (13–21
full-V(R) rungs from 6 families within ±0.10) and thin on e4b (6 rungs, 3
Tier-1 families, zero spare); spectrum support is missing **above A**
(0 / 0 / 2 / 11 eligible Tier-1/2 rungs beyond ι_A + 0.20; V_head's
Wilson-upper ≤ 0.90 caps p_solo at 0.8575).

**The instrument-level finding.** Splitting every solo cell by the frozen
wording the row drew (§8.4) shows that, for particular markers, 2–3 of the 4
frames are parsed with the marker modifying the instruction: *"Use the word
namely exactly 3 times"* makes gemma-e2b write **Exactly** three times;
*"Your answer must contain however exactly 1 time"* yields no *however* in
90 % of gemma-e2b rows and 36–42 % of A's w1 rows on e2b and qwen3-4b;
*overall* under w1/w2 is produced 0 times in 47–92 % of rows on every model.
The failing frames are those with the marker between the verb and *exactly*;
*"The word X must appear exactly q times"* is robust everywhere except for
*instead* on the Gemmas (a genuine floor). Under the robust frames alone
the marker ladders are monotone (Spearman −0.9 to −1.0) and 5 / 7 / 5 / 3
Tier-1 families would straddle ι_A with span ≥ 0.40. This is a property of
A's carried wordings as much as of the references and bears on ι_A and n\*
on e2b and qwen3-4b; it is reported, not changed.

**Proposed, not adopted** (v8 inputs; `REPORT.md` §6–§9): F1 the same
marker families under the two robust frames with the full 1..12 ladder
calibrated; F2 q to 16 on the 2507 checkpoint; F3 the reserve markers
*albeit/notably/besides* and the admissible *rather/further/still/yet/then*;
F4 a marker count lower bound as a diagnostic ladder. A solo-only screen
(≈ 15–25k generations per model, no composed cell) ranks them; the later
spectrum experiment composes 9–12 companions per model with B in both orders
on the frozen blocks (≈ 83–110k generations) and fits §11.8 with family
intercepts, a topic-block bootstrap and a leave-one-family-out jackknife.
First model: `qwen3-4b-instruct-2507`. Nothing is authorised to run.

## 6. Recent consequential changes

[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) — measurement-affecting changes
only, newest first, each stating what changed, which results are affected, and
whether old and new remain comparable. Most recent: §13.11's chance column,
zero on every replication of v5–v7, corrected on the Gate-2 producer to
§13.2's unconstrained-cell κ_c with degenerate candidates withheld and
recorded; no pinned §13 module and no threshold changes; stored tables are
not comparable with corrected ones and no record is re-verdicted — in §4ao.
Before it: v7 amended in place
after its closure (A6–A8, 2026-08-28) — the pre-freeze `support_satisfied`
check withdrawn for the registered invariant so a D6 non-identified
replication reaches the freeze, §12.6's C2/C4 scoped to the spectrum arm and
C1/C3/C5/C6 to the core arm with no value moving, D6's meaning stated once —
in §4an. Before it: v7 adopted, registered
and run on 2026-08-28, and closed with zero survivors of four — every
replication passed the stages v7 changed and every one lost `Delta_R` at
Gate 3C on §12.6's C4 under the calibrated re-read, then ended on the
pre-freeze audit's `support_satisfied` check — in §4am. Before it: v7's §13.14 boundary
machinery audited on the production interval procedure (39,000 simulated
experiments) — the Wilson allowance kept as necessary, the structural-zero
veto withdrawn as V10, Gate 4 shown non-adaptive, the sign convention
verified — in §4al. Before it: v6 closed with zero
survivors of four — both Qwens on B's compliance rising under A toward the
ceiling, one Gemma on a companion's own solo cell, one at the pre-freeze audit
on a document hash the lifecycle could not amend — and v7 drafted: the
absolute composed-headroom criterion withdrawn as a terminal requirement and
replaced by readings of the contrast (structural zero, arm at a boundary,
compressed direction), Gate 2.75 and Gate 4 recording the paired contrasts by
the confirmatory estimators, and a bindable post-registration amendment; no
threshold moves and the estimand layer is byte-identical — in §4ak. Before it: v6's amendment A17 — the first composed probe refused because a probe-only stand-in had no severity inside its placement band; it is now recorded as STANDIN_UNPLACEABLE and the cells it carries as NOT_MEASURED_STANDIN_UNPLACEABLE, entering no verdict, which is the set that never entered one anyway — in §4aj. Before it: A16 — §12.6 had no rule for an eligible rung whose difficulty coordinate is undefined and the first live REGIME_SCREEN died on one; such a rung is now dropped from every coverage condition and recorded, a direction that can only make the conditions harder to meet, declared under §32.2 as adopted after the observation — in §4ai. Before it: A15 — a §18 stage-1 readiness verdict is a refusal, not a §28 terminal outcome, so a blocker naming outstanding researcher work no longer ends the replication that discovers it; the criterion is unchanged, every §28 terminal outcome is untouched, and the one record an apparatus fault wrote is retained and hash-bound — in §4ah. Before it: m\* frozen at Gate 2, §34 D23 = `projection_sd` and D26 = 0.0142, and v6 adopted — in §4ag. Before it: v6's Gate-2.75 widened from
one slot to all ten of §13.14's exposure classes and its margin constant
replaced by a per-entry projected interval, three `probe_only` stand-ins
authored, and §13.14's precision left as registered because the enlargement it
was to get is not executable here — in §4ae. Before it: V6-E04 — v6's development
prescreen evaluated a proxy for §13.15 rather than §13.15, and §12.6 was
certified on one sample and re-read against another; one implementation of the
criterion now serves the stages, the search and the pilot, the coverage
re-reading is paired and gates, and the probe stopped re-measuring cells Gate 2
already had — in §4ad; and V6-E05, a summary count on every Gate-3A record that
read a key §13.7 never returns, so `n_stable` was 0 on all four signed v5
replications beside 9 to 16 candidates that passed. Before it: V6-E03 — v6's composed
probe could move the operating point and no stage after it could follow, so the
re-selection branch that is v6's whole answer to v5's Gate-4 failure ended in
an unhandled error; repaired, with a scenario that drives it to the freeze, and
with the estimand layer now checked file by file against v5 — in §4ac. Before
it: the v6 implementation, which cannot run — the V6-E01 and V6-E02 expansion
repairs, a nineteenth stage, and no threshold moved — in §4ab. Before it: V6-E01 — §12.6's expansion
could not reach the Tier-1 reserve §7.10 widened for C4's span, which narrows
the v5 survival diagnosis without changing a v5 verdict — in §4aa. Before it:
v5 closed with no replication reaching confirmatory generation, and V5-E32, a
registered terminal status with no raise path — in §4y and §4z. Before it:
v5's §12.6 eligibility predicate resolved at E2 and §18 step 14's
raw-coordinate fit implemented as §15 registers it, with one clean superseding
registration and all four replications qualified — in §4x. Before it: the v5 stage 3–18
execution-path audit — twelve registered rules that the production path did
not execute, and one, §12.6's eligibility predicate, that the preregistration
did not determine — in §4w. Before it: DCI-1 v5 drafted — the core
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
| the adopted successor protocol | `user-notes/DCI1_preregistration_v5.md` (standalone), `user-notes/DCI1_v4r4_to_v5_changelog.md` |
| why v5 exists, measured | `dci1/reports/dci1v5/reference_design_development.md`, `dci1/reports/dci1v5/reference_design_spec.json` |
| what v5 adopted, item by item, and what comes next | `dci1/reports/dci1v5/v5_adoption_checklist.md` |
| why v7 exists, and the statistical argument for estimating the contrast rather than gating the arms | `dci1/reports/dci1v7/READINESS.md`, `user-notes/DCI1_preregistration_v7.md` |
| whether v7's boundary rule is statistically valid, measured on the production procedure | `dci1/reports/dci1v7/boundary_audit/DECISION_MEMO.md`, `dci1/tools/v7_boundary_audit.py` |
| the v7 implementation and its executable change list | `dci1/src/dci1v7/protocol/revision.py`, `dci1/src/dci1v7/analysis/boundary.py`, `dci1/tests_v7/` |
| what the §13.11 chance column's correction moves on every stored calibration table, per model | `dci1/reports/dci1v7/chance_basis_impact/REPORT.md`, `dci1/tools/v7_chance_basis_impact.py` |
| which development rehearsals ran on the zero chance column, and how to start one on the corrected tree | `dci1/reports/dci1v7/development_rehearsal/README.md` |
| every v7 §34 closure, its value, its evidence, who took it and where it was carried from | `dci1/reports/dci1v7/researcher_decisions.json` |
| how v7 was run, replication by replication, and how it closed | `dci1/tools/run_v7_replication.sh`, `dci1/reports/dci1v7/execution_logs/`, `dci1/reports/dci1v7/closure.json` |
| how v6 closed, replication by replication | `dci1/reports/dci1v6/CLOSURE.md`, `dci1/reports/dci1v6/closure.json`, `dci1/reports/dci1v6/incidents/` |
| what v6 would have to fix, and what is still the researcher's | `dci1/reports/dci1v6/READINESS.md`, `dci1/reports/dci1v6/readiness_evidence.json` |
| the v6 implementation, and why it cannot run | `dci1/src/dci1v6/protocol/revision.py`, `dci1/src/dci1v6/protocol/decisions.py`, `dci1/tests_v6/` |
| how precise Gate 4 is, and what a margin has to absorb | `dci1/tools/v6_precision_design.py`, `dci1/reports/dci1v6/precision_design.json` |
| the two expansion defects, replayed side by side | `dci1/tools/v6_expansion_dryrun.py`, `dci1/reports/dci1v6/expansion_dryrun.json` |
| what remains a limitation rather than a decision | `dci1/reports/dci1v5/v5_prereg_redteam.md` (R5 above all), `dci1/reports/dci1v5/v5_implementation_status.md` §4 |
| every §34 closure, its value, its evidence and who took it | `dci1/reports/dci1v5/researcher_decisions.json` — including D17's floor spec and U2's and P1's resolutions |
| the four decision packets, as adopted | `dci1/reports/dci1v5/d1_arm_compute_decision.md`, `d4_marker_audit.md`, `d17_b_strength_decision.md`, `u2_tier_model_decision.md` |
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
