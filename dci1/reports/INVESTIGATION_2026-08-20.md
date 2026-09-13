# Does A cause excess loss of B? — investigation report

> **SUPERSEDED IN PART, later on 2026-08-20.** §7 named the §13.2 condition-2
> disposition the smallest remaining blocker. **It is not a blocker: §13.2 is
> not ambiguous** — see `dci1/reports/section_13_2_v4/REPORT.md` and the
> `CHANGES_SCIENTIFIC.md` entry withdrawing it. §7 is corrected below; every
> other section stands. The current endpoint report is
> `dci1/reports/ENDPOINT_2026-08-20.md`.

**Revision 2, 2026-08-20.** Revision 1 is superseded on two points, both
recorded in `CHANGES_SCIENTIFIC.md`: A's residual from the response-length line
was computed from a line fitted *through* A and is in fact **not identified**;
and the "Amendment B is unnecessary" reading depends on a §13.2 disposition the
protocol does not fix. Branch `feat/dci1v4-fresh-study`. Nothing committed, no
registered stage executed, no confirmatory generation.

---

## Verdict

**No. Under the conditions actually tested, companion identity is not shown to
affect focal compliance beyond generic two-instruction difficulty — and one of
the six rival explanations turns out not to be separable from identity at all on
this design.**

`Δ_R` lies **entirely inside the ±0.10 equivalence band on three of four
models**, spans the 0.10 generic-load threshold on the fourth, and approaches
the 0.25 pair-specific threshold nowhere. The compliance scale and §17.4's
vacuity-forced recomputation agree on all four, so the axis is **resolved by the
protocol's own rule** rather than left indeterminate. Ranking the six candidate
explanations against the effect they compete with:

| | channel | magnitude | status |
|---|---|---|---|
| 4 | constraint **class** | 0.40–0.60 | **larger than identity**, and A is the *gentler* production companion |
| 6a | focal **position** (order) | 0.29–0.35 | **larger than identity**; flips Δ_R's sign on all four models |
| — | *companion identity* (Δ_R) | **0.05–0.10** | the effect under test |
| 3 | companion **difficulty** | A sits +0.067/+0.118 above the line | insufficient alone on the Gemmas |
| 5 | response **length** | — | **not identified** — collinear with identity on this companion set |
| 2 | A **broadly disruptive** | Ξ ≤ 0 on both Gemmas | supported over pair-specificity |
| 6b | **model** dependence | `D(B←A)` +0.23 → −0.10 across families | real in the levels, not in Δ_R |

Two findings sharpen this beyond "the effect is small":

- **An admitted reference out-damages A.** On E2B the paired swap
  `Δ_1 = D(B←A) − D(B←CR6:7)` is **−0.078, simultaneous [−0.134, −0.023]**,
  entirely below zero, from `D(B←CR6:7)` = +0.165 against `D(B←A)` = +0.086.
  (The two marginal intervals overlap, so the paired contrast is the estimator
  that carries this; an earlier wording called them disjoint and that was
  wrong.) A is not the most damaging companion its own registered pool
  contains.
- **The length channel cannot be separated from identity here.** A is the only
  companion that substantially changes response length, so its length shift lies
  outside the range every other companion spans, on all four models. No number
  of blocks fixes this; only a companion matched to A on length would.

**Endpoint: C — a researcher decision boundary, every executable prerequisite
complete.** Gate 1 is unapproved and its blocking item is the reference pool,
which is now a decision rather than a measurement.

---

## 1. Current repository and gate state

**Gate 1: NOT approved.** The peer session's track (committed at `6954dd6` and
five preceding commits) closed §10.2 for A and B, executed the §10.4 autorater
development phase, and completed pre-freeze checks C4 and C5. Its report lists
**seven** items remaining, of which #1 is binding: *"The reference pool must be
final."* Items 2, 3 and 6 are mechanical once the pool is fixed; items 4, 5 and
7 need the pool plus explicit approval.

**Human validation is unavailable and stays that way.** The only annotator is
the study author, so §10.3's independence criterion cannot be met. The
registered consequence — identification status `HUMAN_VALIDATION_UNAVAILABLE`,
criterion **not waived** but routed to §10.4, measurement basis
`autorater_calibration_approved` on explicit researcher approval, §10.5 scope
sentence on every claim — is a permitted outcome and is what the record carries.
No independent validation has been fabricated anywhere.

**No v4 confirmatory generation exists** and none may occur before the protocol,
reference set, instruments, estimands, claim rules, topic allocation and seeds
are prospectively frozen. Stage 4 has not been passed; every later stage is
blocked behind it.

**Two preregistration gaps now sit ahead of Gate 1** — §5.

## 2. Work executed

**Read-only re-analyses of closed evidence.** `tools/v3_reciprocal_reanalysis.py`
→ `reports/v3_reanalysis/`; `tools/pilot_length_channel.py` →
`reports/pilot_reanalysis/`. Nothing in `runs/`, `evidence/` or any frozen
artifact was altered.

**New generation — 234,432 completions, all non-confirmatory, outside the v4
namespace, every arm frozen under a SHA-256 protocol hash before it ran.**

| screen / arm | scope | generations |
|---|---|---:|
| calibration, four arms | §12.3 / §12.4 / §13.2 on the **registered** sample — 96 solo topics at M_cal = 4 — plus the registered-pool, lower-bound and pre-screen-at-M_cal arms | 169,632 |
| pairwise matrix | the registered §8.1 25-cell matrix **in both orders**, + V5 difficulty-spanning arm + production-class arm + §25 unconstrained cell, 120 blocks, M = 4 | 64,800 |

**Analysis completed this pass** (the matrix screens were already generated;
their artifacts were analysed, not re-run):

- added the `focal_losses` family so `D(B←R_j)` is reported, not only the swap;
- corrected the V5 and length fits, which had included A in the line used to
  predict A, and added an explicit support check;
- computed the §13.2 admission under all four condition-2 dispositions;
- measured focal-constraint position directly across all composed cells;
- measured per-cell vacuity on the matrix.

**Discipline.** `cal_screen_v4.admission` is required by test to reproduce
`gates.admit_family` byte for byte; §12.3 selection *is* `gates.select_severity`;
the `current`-stem renderer is asserted byte-identical to
`dci1v4.design.prompts.render`. The matrix's reading rules were fixed in
`reports/matrix_screen_v4/REPORT.md` §7b **before any matrix cell was scored**.
**692 tests pass**, including 28 isolation tests.

## 3. Key estimates, by evidential tier

### Tier: EXPLORATORY DESIGN EVIDENCE — the matrix screen
120 blocks, calibration topics, floored stem, M = 4, pooled over both orders,
10,000-resample block bootstrap. `claim_licensed: False` by construction.

**Reference sets selected by the registered §13.2 procedure** (not chosen for
their result; the choice was frozen before generation):

| model | A | B | R₁ | R₂ | R₃ | class C₁ |
|---|---|---|---|---|---|---|
| E2B | A:7 | B:10 | CR6:7 | RF3:4 | RF2:6 | CL7:80 |
| E4B | A:6 | B:9 | RF8:8 | RF3:4 | RF2:8 | CL8:25 |
| Qwen3-4B | A:2 | B:12 | CR7:44 | **CL8:5** | RF7:24 | none — R₂ *is* the class contrast |
| Qwen3-4B-Inst | A:5 | B:10 | CR7:44 | RF1:5 | RF7:24 | CL8:10 |

**Focal losses, and the primary contrast:**

| model | `D(B←A)` | `D(B←R₁)` | `D(B←R₂)` | `D(B←R₃)` | **Δ_R** | Δ_R §17.4-forced |
|---|---|---|---|---|---|---|
| E2B | +0.086 [+0.031, +0.143] | **+0.165 [+0.121, +0.207]** | −0.045 [−0.099, +0.008] | −0.003 [−0.055, +0.047] | **+0.048 [+0.009, +0.087]** | +0.048 |
| E4B | +0.228 [+0.174, +0.282] | +0.126 [+0.079, +0.172] | +0.050 [+0.003, +0.097] | +0.206 [+0.151, +0.261] | **+0.101 [+0.056, +0.146]** | +0.101 |
| Qwen3-4B | −0.039 [−0.085, +0.009] | −0.033 [−0.075, +0.007] | −0.082 [−0.128, −0.037] | −0.034 [−0.077, +0.009] | **+0.011 [−0.020, +0.044]** | +0.007 |
| Qwen3-4B-Inst | −0.095 [−0.151, −0.040] | −0.080 [−0.128, −0.032] | −0.090 [−0.141, −0.041] | −0.042 [−0.094, +0.009] | **−0.024 [−0.067, +0.019]** | −0.053 |

Reading, per §7b fixed in advance: **equivalence** (interval inside ±0.10) on
E2B, Qwen3-4B and Qwen3-4B-Inst; **unresolved at this precision** (spans 0.10)
on E4B. Both scales land in the same row on all four models, so §17.4's
agreement rule licenses the reading rather than voiding it.

**Reference heterogeneity** — reported, never averaged away (§13.4). Δ_j on E2B
is −0.078, +0.131, +0.090: no shared sign, and the pooled +0.048 describes none
of them. This repeats v3's pattern (+0.056, +0.142, −0.006) on a different
reference set.

**Outcome specificity and asymmetry:**

| model | Ξ | `D(R̄←A)` | `D(R̄←R̄′)` | Λ |
|---|---|---|---|---|
| E2B | −0.036 [−0.082, +0.010] | +0.179 [+0.135, +0.223] | +0.095 [+0.065, +0.125] | −0.092 [−0.177, −0.005] |
| E4B | −0.009 [−0.063, +0.047] | +0.073 [+0.018, +0.128] | −0.036 [−0.071, −0.001] | +0.005 [−0.071, +0.080] |
| Qwen3-4B | +0.131 [+0.094, +0.167] | −0.095 [−0.125, −0.065] | +0.024 [−0.005, +0.053] | −0.396 [−0.470, −0.322] |
| Qwen3-4B-Inst | +0.090 [+0.038, +0.142] | −0.180 [−0.221, −0.137] | −0.065 [−0.102, −0.029] | −0.040 [−0.126, +0.047] |

Ξ is read as sign and rough size only. Negative on both Gemmas — A damages the
references at least as much as it damages B. Positive on the Qwens **only
because A improves reference compliance there**, while `D(B←A)` is itself
negative: not support for pair specificity.

**Class-matched contrast** `Δ_class = D(B←A) − D(B←CL)`:

| model | companion | `D(B←CL)` | **Δ_class** |
|---|---|---|---|
| E2B | CL7:80 | +0.601 [+0.544, +0.657] | **−0.515 [−0.564, −0.464]** |
| E4B | CL8:25 | +0.632 [+0.578, +0.686] | **−0.404 [−0.453, −0.355]** |
| Qwen3-4B | — (R₂ = CL8:5 carries it) | — | Δ_R₂ = +0.044 [+0.008, +0.080] |
| Qwen3-4B-Inst | CL8:10 | −0.182 [−0.244, −0.124] | +0.087 [+0.046, +0.130] |

**V5 difficulty→loss, and A's residual.** Lines fitted on the budget companions
**excluding A**, then used to predict A:

| model | slope | A observed | A predicted | **A residual** | A inside fitted range? |
|---|---:|---:|---:|---:|---|
| E2B | +0.025 | −0.044 | −0.110 | **+0.067** | yes, [0.335, 0.735] ∋ 0.562 |
| E4B | −0.100 | +0.054 | −0.064 | **+0.118** | yes, [0.531, 0.838] ∋ 0.719 |
| Qwen3-4B | −0.068 | −0.098 | −0.047 | **−0.050** | yes |
| Qwen3-4B-Inst | −0.060 | −0.127 | −0.079 | **−0.048** | yes |

**Order-stratified** — the largest effect in the screen:

| model | `D(B←A)` reg-first | `D(B←A)` reg-second | Δ_R reg-first | Δ_R reg-second | B position effect |
|---|---|---|---|---|---:|
| E2B | +0.217 [+0.150, +0.283] | −0.044 [−0.104, +0.017] | +0.326 | −0.231 | **+0.288** |
| E4B | +0.402 [+0.331, +0.473] | +0.054 [+0.000, +0.108] | +0.450 | −0.249 | **+0.350** |
| Qwen3-4B | +0.021 [−0.025, +0.071] | −0.098 [−0.156, −0.040] | +0.083 | −0.060 | +0.047 |
| Qwen3-4B-Inst | −0.062 [−0.129, +0.004] | −0.127 [−0.190, −0.067] | +0.035 | −0.083 | +0.056 |

§8.4's registered order places the focal constraint **second** in the A-cell and
**first** in the R-cells under one configuration, and swaps both under the other.
So a single-order Δ_R contrasts cells in which B occupies different positions,
and B loses 0.29–0.35 of its compliance on the Gemmas purely by being stated
second (A loses nothing: |effect| ≤ 0.063). Pooling over orders balances this;
**a single-order Δ_R is not a well-defined identity contrast.**

**Length and vacuity sensitivities.** Vacuous-pass rates under the floored stem
are **0.000 on both Gemmas in every focal cell**, ≤0.005 on Qwen3-4B, and
0.024–0.090 on Qwen3-4B-Inst — all inside §12.4's 0.10 maximum, which is why
§17.4 forcing moves Δ_R by ≤0.029. The **length** sensitivity cannot be
computed: A's length shift (+15, +8, −8, −16 words) lies outside the range every
other companion spans on all four models, so the length line extrapolates to A.

**Selection-clean subgroup** — the 24 pre-screen blocks, disjoint from the 96
that informed selection: Δ_R = +0.059, +0.122, +0.012, −0.075. Agrees in sign
and size throughout at roughly half the precision.

**§25 accidental compliance** — A **0.000 on all four models**; B 0.000–0.406;
references 0.52–0.89. The reference outcomes are near-ceiling, so reference-side
delivery loss is measured against a saturated outcome.

### Tier: REGISTERED DIAGNOSTIC — Δ^A on v3's confirmatory rows
The only same-topic registered companion swap the study has executed. §11.5's
three gates hold.

| quantity | E2B | E4B |
|---|---|---|
| **Δ^A** | **+0.064 [+0.041, +0.087]** | **+0.074 [+0.052, +0.095]** |
| per reference (simultaneous) | +0.056, +0.142, **−0.006** | +0.076, +0.068, +0.077 |
| under §17.4 forcing | +0.0634 | +0.0720 |
| length-matched, length-balanced order | +0.047 | +0.048 |

### Tier: DERIVED / POST-HOC — the B+R pilot re-analysis
| quantity | E2B | E4B |
|---|---|---|
| Δ as recorded | +0.343 [+0.281, +0.405] | +0.375 [+0.319, +0.430] |
| **under §17.4 forcing** | **+0.095** | **+0.068** |
| at matched length | −0.057 | −0.003 |
| overlap on the mediator | 9.1% | 7.8% |

§17.4's disposition: **axis unresolved, both bounds reported.** The raw Δ must
never be quoted alone. Length-matched contrasts are collider-conditioned
sub-population descriptions, not causal decompositions.

### Tier: REGISTERED CONFIRMATORY
v3 only, and it resolves nothing: both Gemmas at `UNMASKED_ANALYSIS` with all
four primary τ claims direction-unresolved, one equivalence,
`exchangeability_holds: false`; both Qwens terminated at Gate 2A with
`REFERENCE_POOL_MISMATCH` — non-identification, not a null. **v4: none.**

### Does the calibration admit three valid references?

**Yes — on every model, under every disposition**, from the enlarged pool: 5, 3,
3, 5 families admitted under full §13.2 on the registered 96-topic M_cal = 4
sample under the floored stem. Two qualifications:

- **From the *registered* pool alone the answer depends on an unfixed reading.**
  With condition 2 applied where its §12.2 one-draw input exists: **3, 4, 1, 4**
  → three of four models. With an unmeasurable condition 2 counted as a failure:
  **1, 2, 1, 2** → no model. §13.2 does not say which.
- **On E4B and Qwen3-4B the third slot can only be filled by a lower-bound
  (production-class) family**, so on those two the class confound moves *inside*
  the reference set instead of sitting beside it as a control.

### Does the Gemma/Qwen split persist?

**Yes, in the levels; no, in the contrast.** `D(B←A)` is +0.086 and +0.228 on
the Gemmas (A damages B) and −0.039 and −0.095 on the Qwens (A helps B); Λ is
−0.09/+0.01 against −0.40/−0.04; Ξ is negative on the Gemmas and positive on the
Qwens; the position effect is 0.29–0.35 against 0.05–0.06. But **Δ_R is small on
all four**. Whether A interferes with B at all is model-family-dependent;
whether *identity beyond difficulty* matters is uniformly unsupported.

## 4. Alternative explanations: weakened, ruled out, still viable

| # | explanation | status |
|---|---|---|
| 1 | **Genuine A→B pair-specific interference** | **weakened to unsupported.** Δ_R inside ±0.10 on 3 of 4 models, never near 0.25, agreeing on both scales; and an admitted pool reference out-damages A on E2B |
| 2 | **A broadly disruptive** | **supported over (1) on the Gemmas.** Ξ ≤ 0 on both: A costs the references +0.179 and +0.073 while costing B +0.086 and +0.228 |
| 3 | **Companion difficulty** | **viable but insufficient alone.** A sits +0.067 and +0.118 above the difficulty line on the Gemmas — identified, A inside the fit's support — and −0.050/−0.048 below it on the Qwens |
| 4 | **Constraint class** | **the largest identified channel.** Δ_class −0.515 and −0.404: a production companion costs B +0.60/+0.63 against A's +0.086/+0.228. A is the *gentler* production companion, 5–7× |
| 5 | **Response length / vacuity** | **split.** Vacuity is **ruled out** on this screen (rates 0.000–0.090, §17.4 moves Δ_R ≤0.029) — though it remains decisive for the *pilot*. Length is **not identified**: collinear with identity across this companion set on all four models |
| 6 | **Order / position** | **confirmed, and larger than the effect.** B loses 0.29–0.35 by being stated second on the Gemmas; A loses nothing; single-order Δ_R changes sign on all four models |
| 7 | **Model dependence** | **confirmed in the levels, absent in the contrast** — see §3 |
| 8 | **Reference heterogeneity** | **confirmed.** Δ_j do not share a sign on E2B; §13.4's qualifier fires |
| 9 | **Selection** | **ruled out.** The 24 selection-disjoint blocks agree throughout |
| 10 | **Accidental compliance** | **ruled out for A** (0.000 everywhere); **live for the references** (0.52–0.89, near-ceiling) |

## 5. The explicit answer

> **Does companion identity affect focal compliance beyond the generic
> difficulty of satisfying two instructions?**

**Not on the evidence available, and on three of four models the data are
consistent with no such effect at the registered equivalence margin.**

- The excess-loss contrast the study exists to measure, `Δ_R`, is **+0.048,
  +0.101, +0.011 and −0.024** — inside ±0.10 on three models, spanning 0.10 on
  the fourth, nowhere near 0.25, on both the compliance and the §17.4-forced
  scale.
- Where a positive focal loss does exist (the Gemmas), **it is not specific to
  A**: A damages the references as much or more (Ξ ≤ 0), a class-matched
  production companion damages B five- to sevenfold more, and on E2B an admitted
  reference out-damages A outright.
- **Two nuisance channels are larger than the effect** — constraint class
  (0.40–0.60) and focal position (0.29–0.35) — and a third, response length, is
  **collinear with identity on this companion set and cannot be separated from
  it at any sample size**.
- The one same-topic *registered* companion swap the study has executed, Δ^A =
  **+0.064** and **+0.074**, is positive and excludes zero but sits **below the
  0.10 generic-load threshold** on both models — generic load, not pair
  specificity.

**No confirmatory claim is licensed.** Everything above is exploratory design
evidence or a registered diagnostic, and none of it may be upgraded.

## 6. The strongest scientifically defensible claim now licensed

At its registered evidential level and no higher:

> On two Gemma checkpoints, in the v3 constraint vocabulary, on the 384 v3
> confirmatory topics with same-topic pairing and all sixteen cached draws,
> replacing the companion *B* by a companion matched to *B* on solo failure
> raises compliance with the exact-count focal constraint by **+0.064
> [+0.041, +0.087]** and **+0.074 [+0.052, +0.095]**. The effect survives
> matching on response length and §17.4 forcing. It lies **below the 0.10
> threshold the construct memo sets for generic load** on both models, and far
> below the 0.25 that would support a pair-specific reading. On one of the two
> it is heterogeneous across the three companions it is defined over — +0.056,
> +0.142, −0.006.

A **registered diagnostic** (§11.5 demotes Δ^A and gates it on three conditions,
all of which hold). Not an L3 statement, not about B as an outcome, not about
the Qwen family, which produced no confirmatory data.

The matrix screen licenses no claim about the world. Its standing is as evidence
about the **design**: the primary estimand, as currently specified, is dominated
by channels the protocol does not control, and one of them is not identifiable
on the current companion set at all.

## 7. The smallest remaining blocker

**CORRECTED.** This section named §13.2's condition-2 disposition the smallest
remaining blocker. **§13.2 is not ambiguous and is not a blocker.** §12.2
measures all 94 rungs on the 24 pre-screen topics and §13.2's feasible set is a
subset of the shortlist §12.2 writes, so condition 2 always has its input;
where the case is constructed anyway, `gates.admit_family` rejects. Verified on
all four registered `REGIME_SCREEN` records. The screens met an unmeasurable
condition 2 because they ran §13.2 over rungs outside the shortlist and on a
partial floored-stem pre-screen — properties of the screens.
`dci1/reports/section_13_2_v4/REPORT.md`.

**The blocker is item 2 below**, and the list is otherwise unchanged.

Researcher decisions, in order:

1. **§12.4's graded-degeneracy clause has two readings and the registered code
   fixes neither.** Applied to B, the mean-graded reading fires on **every**
   in-band rung — §12.3 declares a rung eligible and §12.4 declares the same
   rung degenerate — while the share reading fires on none. Under the mean
   reading nothing runs on three of four models under either stem; the one
   exception is qwen3-4b-instruct-2507 at m = 10 under the floored stem, which
   is the only rung on any model feasible under both readings. This also sits
   ahead of Gate 1.
2. **Amendment A (the floored stem): adopt or reject.** The registered prompt
   cannot start — B's solo vacuity is *at least* 0.208, and up to 0.870, at
   *every* rung of the focal grid on *all four* models against a §12.4 maximum
   of 0.10. A uniform length
   instruction takes the same cells to 0.000–0.060.
3. **Amendment C per-model, not global** — a global focal-grid extension moves
   m\* off the only rung feasible under both §12.4 readings on
   qwen3-4b-instruct-2507.
4. **Whether a class-matched production companion enters the reference pool.**
   This changes what Δ_R means, so it is an amendment, not a robustness check —
   and on E4B and Qwen3-4B a production-class family is already the only way to
   fill the third slot.
5. **Whether the pool must contain a companion matched to A on length shift.**
   Without one the length channel is unidentified no matter how many blocks are
   run; §22's mediator treatment reports length, it does not identify it.

Then, mechanically and only afterwards: §10.2 for every admitted family
verifier, re-run over a real calibration pool, the §10.4 fourth criterion,
the single-shot freeze against a final verifier hash, a sealed v4 final-check
set, and explicit researcher approval writing
`measurement_basis = autorater_calibration_approved` with
`HUMAN_VALIDATION_UNAVAILABLE` as the identification status.

---

## Provenance

`dci1/src/{cal_screen_v4,matrix_screen_v4}/` · `dci1/evidence/{cal-screen-v4,matrix-screen-v4}/` ·
`dci1/reports/{v3_reanalysis,pilot_reanalysis,cal_screen_v4,matrix_screen_v4}/` ·
`dci1/tools/{v3_reciprocal_reanalysis,pilot_length_channel,cal_screen_report_v4,matrix_screen_report_v4}.py` ·
`dci1/tests_v4/test_cal_and_matrix_screen_isolation.py` (28 tests).
`CHANGES_SCIENTIFIC.md` carries six entries from this investigation, including
the two corrections this revision records. `RESEARCH_STATE.md` §4e and §4f.

**Not modified**: `dci1/src/dci1v4/`, `dci1/src/dci1v3/`, `configs/`,
`notebook_source/`, `user-notes/`, every registered constant, every frozen
artifact, every existing evidence tree, and the 24 composed-validation topics
Gate 4 depends on. 692 tests pass. Nothing staged, committed or pushed.
