# DCI paper — evidence and narrative review packet

**Status: REVIEW PACKET. No manuscript prose has been written. `neurips_2026.tex`
is untouched. No title or abstract is locked in.**

Prepared 2026-08-20 on branch `feat/dci1v4-fresh-study` at `6954dd6`, against a
worktree carrying substantial uncommitted work by a concurrent session (§1.3).

---

## 1. Repository and paper-guide state

### 1.1 Branch and commit

| | |
|---|---|
| branch | `feat/dci1v4-fresh-study` |
| HEAD | `6954dd6` *fix(screens): report the registered 17.4 vacuity bound beside the restriction* |
| main | `20c0a06` |
| other worktrees | `dci-cheapest-rocm-study`, `dci-cross-model`, `dci-natural-reasoning-headline` — all on the **legacy** `src/dci/` + `exploratory/` programme, not on DCI-1 |

### 1.2 Paper guides read in full

All fifteen files under `user-notes/paper-guides/`: `guidelines-{narrative-and-process,
bullet-point-outline, abstract, introduction, background, methods, results,
figures-and-tables, headline-figure, captions, discussion, conclusion,
related-works, appendix}.md`, plus `neurips_2026.tex`, `neurips_2026.sty`,
`neurips_2026_checklist.tex`.

**Binding constraints extracted** (see §8 for the full readiness map):

- **Nine content pages.** Figures count. Acknowledgments, references, checklist
  and technical appendices do not. *"Papers that exceed the page limit will not
  be reviewed."*
- **The checklist is mandatory.** *"The papers not including the checklist will
  be desk rejected."* It follows the references and the appendix. Sixteen items.
  Keep the question text and the guidance bullets; delete only the instruction
  preamble.
- **One PDF.** Code/video may go in a ZIP; a separate appendix PDF may not.
- **Double-blind by default.** `\usepackage{neurips_2026}` with no options is
  anonymous: author block replaced, `ack` environment silently swallowed, line
  numbers added. Anonymise artifact URLs (anonymised URL or ZIP).
- **Type 1 / embedded TrueType only.** Matplotlib Type 3 output is a fix
  request. Validate the *packaged* PDF with `pdffonts`, appendix included.
- **Minimum font sizes are enforced in the `.sty`** (6/7/8 pt floors). Tables
  cannot be shrunk out of the page limit.
- **No vertical rules in tables**; `booktabs`. Table caption *before* the table,
  figure caption *after* the figure. Figure widths as multiples of `\linewidth`.
- **Statistical reporting is stricter than usual** — see §8.2. The six lines
  that bite: name the factor of variability; name the estimator; say SD vs SEM
  explicitly; state the sigma level in words; no symmetric bars on bounded
  quantities; describe the calculation *in the prose*, not only the caption.
- **Project conventions** from `guidelines-appendix.md`: a **citation
  verification register** appendix, a **result-insertion map** appendix for
  papers whose experiments have not run (directly applicable here), and a
  structural companion note outside the PDF.
- **Process**: compressed narrative → introduction outline → full-paper outline
  → first-draft figures → prose. This packet is steps 1–4. 1–3 claims, no more.
  Verify ≥75% of experiments before writeup.
- **The stand-alone test**: proofs, hyperparameters and protocol detail may move
  to the appendix; **evidence may not**.

### 1.3 Active and incomplete experimental work

A concurrent session finished a large body of work at ~23:04 today. No
generation process is running now. Everything below is **uncommitted**:

| path | what it is | complete? |
|---|---|---|
| `dci1/src/matrix_screen_v4/`, `dci1/reports/matrix_screen_v4/` | the pairwise-matrix screen, 64,800 generations, four models | **complete**, results + report written |
| `dci1/src/cal_screen_v4/`, `dci1/reports/cal_screen_v4/` | the Gate-2 calibration screen, ~144k rows | **complete** |
| `dci1/reports/section_13_2_v4/` | §13.2 resolution, topic audit, instructed-compliance analysis | complete |
| `dci1/reports/v3_reanalysis/`, `dci1/reports/pilot_reanalysis/` | read-only re-analyses of closed evidence | complete |
| `dci1/reports/ENDPOINT_2026-08-20.md`, `INVESTIGATION_2026-08-20.md` | syntheses | complete |
| `dci1/tools/allocation_v4r3.py` | **the only v4r3 artifact** — a power/allocation planner | planner only |
| modified: `RESEARCH_STATE.md`, `CHANGES_SCIENTIFIC.md`, `dci1/src/dci1v4/stages/regime.py`, `verifiers/{boundary,independent}.py`, three test files | | |

**Late update — the v4r3 preregistration landed mid-review.** At 00:03 and 00:07
on 2026-08-21, after this packet's evidence review was complete, the concurrent
session wrote `user-notes/DCI1_preregistration_v4r3.md` (2,523 lines) and
`user-notes/DCI1_v4r2_to_v4r3_changelog.md` (846 lines). Both are untracked and
both are marked **"PROPOSED. Not adopted, not signed, not frozen."** There is
still **no v4r3 data**, and all four registered replications still stand at
`REGIME_SCREEN`. (A `dci1/src/dci1v4r3/` package — 21 modules, a sibling that
`dci1v4` neither imports nor can read — appeared at ~00:30 on 2026-08-21, after
this packet was drafted. It is unexecuted, and no v4r3 evidence tree exists.)

Four things in it change this packet, all in the paper's favour:

1. **It closes v4r2's open decision V5 in the spanning direction**, and promotes
   `δ_diff` (the difficulty residual) and `Ξ` to **primary** estimands — six per
   configuration, up from four. Narrative **N4 is precisely what v4r3 is powered
   to test**, which is what makes it a credible fallback rather than a hope.
2. **It adopts chance-corrected instructed compliance as the registered
   difficulty coordinate** (§13.3), demoting raw solo compliance to a reported
   secondary, on exactly the reasoning that is narrative N1's core — its own
   words: *"Netting out chance moves twelve of twelve matched companions in the
   matrix screen out of the caliper. A coordinate that makes matching harder is
   not a coordinate chosen to make a result appear."* **N1 is no longer only a
   diagnosis; it is the stated rationale for a successor design.** That is the
   strongest possible shape for a methodology paper — diagnosis, then the
   corrected instrument — and it should be reflected in §6 of the structure.
3. **It registers a temperature-0 sensitivity run** (3,264 further generations
   per model, reported as a separate generation population) — v4r3 responding to
   N7.
4. Size confirms the planner: **408 blocks, 47 cells, M = 4 → 76,704 per model,
   306,816 total.**

One caution: the changelog **reproduces the `0.208 to 0.659` transcription error
of §9.2 verbatim**, now inside a document offered for registration. See D3.

The remaining v4r3 artifacts are (a) the V5 spanning arm already executed inside
the matrix screen, and (b) `allocation_v4r3.py`, which sizes a 47-cell block: 6 spectrum solo + 12 spectrum composed + 1 class solo +
2 class composed + the §25 unconstrained cell on top of the 25-cell core, with
the primary family growing to six members (adding `delta_difficulty` and `Ξ`).
Its answer: **≥408 blocks at M = 4**, i.e. 76,704 generations per model,
**306,816 across four models**, before the precision preconditions are met at
φ = 0.37.

---

## 2. Strongest scientific verdict

**No version of DCI-1 has produced a licensed claim that companion identity
affects focal compliance beyond generic two-instruction difficulty, and the
accumulated evidence now explains why: the control condition the design depends
on cannot be built out of the available constraint vocabulary.** v2 terminated
at Gate 2 on all four models with zero confirmatory generations. v3 reached
confirmatory analysis on two of four models and returned four of four primary
estimands direction-unresolved, with the identity-level claim structurally
unavailable because reference exchangeability failed in all four analyses. Its
two magnitude claims are marginal and phase-specific in opposite directions —
E2B's equivalence holds unmasked and not masked, E4B's holds masked and not
unmasked, the latter inside the band by 0.00012 — and its registered estimator
used one of sixteen generated draws per cell, a selection under which the same
contrast is positive in 99.5% of alternative draws and negative in the one that
was registered. v4r2 cannot start: on its
own registered calibration sample, under its own prompt, the focal constraint's
solo *vacuity* rate is 0.208–0.870 against a registered ceiling of 0.10, at
every rung of the focal grid on every model. Where the effect *has* been
measured at screen scale under a repaired prompt — 64,800 generations, all four
models, the full 25-cell pairwise matrix, both instruction orders, pre-specified
reading rules — the companion-swap excess `Δ_R` is **+0.048, +0.101, +0.011,
−0.024**, reaching the registered pair-specific threshold of 0.25 on no model
and lying wholly inside the ±0.10 generic-load band on three of four. Meanwhile
three channels the design does not control each move focal compliance three to
ten times more: the companion's **structural class** (`Δ_class` = −0.515,
−0.404 on the Gemmas), the focal constraint's **position** in the prompt (0.288,
0.350, and enough to flip `Δ_R`'s sign within every single order stratum), and
**prompt-induced vacuity** (under the registered stem, 21–87% of the focal
constraint's "passes" are the model declining to answer). The deepest finding is
structural and is supported by five independent lines: the matching criterion
that makes a companion a valid control — equality of marginal solo pass rate —
**equates companions that do all of their own work with companions that do
almost none**, because every reference in the pool is a prefix-closed `S ≤ q`
budget that an unconstrained answer satisfies by chance 2.5–89% of the time,
while the target is an exact-count production constraint whose chance rate is
**0.000 on all four models**. Twelve of twelve admitted references are matched
to the target on solo compliance; **two of twelve** are matched on
chance-corrected instructed compliance, and two are *anti*-productive.

---

## 3. Ranked paper narratives

Ranked by scientific validity × evidential strength × distinctiveness ×
importance × clarity — not by positivity.

### N1 (recommended). Matched-difficulty controls do not identify pair-specific instruction interference

**Thesis.** Isolating an instruction pair's specific interference requires a
companion counterfactual, the field's natural counterfactual is a companion
matched on marginal pass rate, and that match is not a valid one: marginal pass
rate conflates instructed compliance with accidental compliance, is confounded
with response length, and — because the caliper collapses the very variation a
difficulty account needs — cannot be checked from inside a matched-point design.

**Evidence chain** (five independent lines, four of them measured):

1. **Structural.** Every registered reference family and the focal constraint
   are `S ≤ q` monotone budgets with prefix-closed pass sets; the target is an
   exact-count production constraint. The empty string scores 94/94 on the
   reference ladder, 4/4 on the focal constraint, **0/8** on the target.
   *(`user-notes/DCI1_v4_amendment_B_reference_pool.md` §2; FORM × STEM screen.)*
2. **Chance-corrected matching.** `(solo − chance)/(1 − chance)` on the matrix
   screen's own reference sets: target chance rate **0.000 on all four models**;
   references 0.025–0.890. **12/12 matched on solo, 2/12 on instructed**, two
   anti-productive (−0.550 on E4B, −2.321 on Qwen3-4B-Inst).
   *(`dci1/reports/section_13_2_v4/instructed_compliance.json`, verified.)*
3. **Independent confirmation in closed v3 data.** v3's admitted references had
   solo cells that were **49–90% vacuous at 9–45 words**, against the target's
   **0.000 vacuous at 269–323 words** — and were satisfied in **2–8%** of
   composed responses on E4B. A control admitted because a nine-word answer
   satisfies it stops being satisfied the moment a second instruction forces
   prose. *(`dci1/reports/v3_reanalysis/`.)*
4. **The caliper destroys the difficulty check.** On E2B, v3's three admitted
   references have identical solo compliance to four decimal places — the
   difficulty regression's x-axis has zero variance and no slope exists. On E4B
   three points span 0.021 in x and the fit extrapolates a full x-range to reach
   the focal companion. *(`dci1/reports/v3_reanalysis/`.)*
5. **Length is collinear with identity across the whole companion set.** On all
   four models the target's response-length shift lies outside the range every
   other companion spans, so the length line extrapolates to it and its residual
   is not a measurement. **No number of blocks fixes this** — it needs a
   companion matched on length shift, and the pool contains none.
   *(matrix screen `length_channel`, verified: `inside_support = False` ×4.)*

**Tier.** Lines 1, 2, 4, 5 are EXPLORATORY / DESIGN SCREEN and DERIVED. Line 3
is DERIVED from REGISTERED/CONFIRMATORY v3 rows. The *structural* argument
(line 1) is a property of the constraint definitions, not of any dataset.

**Novelty.** The repository's related-work map (§9.8) shows nothing in the
cited literature that formalises a companion counterfactual at all, let alone
diagnoses its failure. Requires external verification — flag as `TODO(CITE)`.

**Strengths.** Survives every robustness axis because it is largely structural.
Independent of which reference set Gate 3 would eventually admit. Generalises
beyond DCI: any constraint-composition benchmark that matches controls on pass
rate inherits it.

**Weaknesses.** It is a negative/methodological contribution; reviewers who want
a phenomenon will ask what the effect *is*. Mitigated by pairing with N2.

**v4r3 sensitivity.** **None.** No v4r3 outcome weakens this chain. That is
what makes it the safe anchor.

### N2 (recommended companion). Structure beats identity: class, position and vacuity dominate the pairwise effect

**Thesis.** At screen scale on four models, the excess loss attributable to
*which* companion instruction is present is small, and three structural
properties of the composition — the companion's constraint class, the focal
constraint's position, and whether the prompt lets the model satisfy a budget
constraint by writing almost nothing — each move focal compliance by three to
ten times more.

**Evidence.** `Δ_R` = +0.048 [−0.002,+0.098], +0.101 [+0.043,+0.158], +0.011
[−0.029,+0.052], −0.024 [−0.079,+0.030] (simultaneous, four models). Against:
`Δ_class` = −0.515 [−0.582,−0.447] and −0.404 [−0.471,−0.337] on the Gemmas — a
production-class companion costs the focal constraint **+0.601 / +0.632** where
the target costs +0.086 / +0.228. Focal position costs 0.288 / 0.350 and flips
`Δ_R`'s sign inside every order stratum (E2B +0.326 vs −0.231; E4B +0.450 vs
−0.249). Vacuity: 0.208–0.870 of focal "passes" under the registered prompt.

**Tier.** EXPLORATORY / DESIGN SCREEN throughout, with pre-specified reading
rules fixed before any cell was scored (`matrix_screen_v4/REPORT.md` §7b).

**Strengths.** Pre-registered interpretation table for an exploratory screen is
unusually strong practice and should be foregrounded. Four models, both orders,
paired within block, dual (raw and vacuity-forced) scales that agree.

**Weaknesses.** The §16.2 precision precondition (half-width ≤ 0.05) is met on
**one** model of four at 120 blocks; the §13.4 heterogeneity qualifier fires on
both Gemmas. On E2B an admitted reference out-damages the target
(paired `Δ_1` = −0.078 [−0.134,−0.023]). `Ξ` ≤ 0 on both Gemmas. Qwen3-4B's
`Δ_R` averages one production and two budget companions and is not comparable to
the others.

**v4r3 sensitivity.** A v4r3 run at 408+ blocks would sharpen every interval and
could move E4B's `Δ_R` (currently spanning 0.10) to either side. It cannot
plausibly move any of them to 0.25.

### N3. The reversal: the study's largest positive result is an artifact of its own design

**Thesis.** The result that motivated promoting the companion swap to a primary
estimand — `Δ` = +0.343 / +0.375, classified `H1_PAIR_SPECIFIC` — does not
survive the protocol's own bounds.

**Evidence.** Its two cells come from **different topic sets** (96 calibration
vs 384 confirmatory) and differ **five-fold** in response length (24.8 vs
127.9/139.1 words). Under §17.4's registered vacuity forcing it is **+0.095 and
+0.068**, below the 0.10 generic-load threshold; since raw and forced license
different claims, §17.4's own rule reports the axis **unresolved with both
bounds**. At matched response length the contrast is **−0.057 and −0.003**.

**Tier.** DERIVED / POST-HOC re-analysis of closed evidence.

**Weaknesses as a headline.** "Our own pilot was wrong" is a section, not a
paper. It belongs inside N1 as the motivating episode.

### N4. Difficulty-spectrum result

**Thesis.** Companion difficulty explains part of the loss; the target's
residual above the difficulty line is where companion-specific effects live.

**Evidence.** With the target excluded from the fit, its residual is **+0.067**
(E2B) and **+0.118** (E4B) and is *identified* — the target's solo compliance
lies inside the fit's support on all four models — but **−0.050 / −0.048** on
the Qwens. Five fit points per model.

**Tier.** DERIVED / POST-HOC (the V5 arm inside an exploratory screen).

**Why not primary now.** Five points, two of four models negative, no
preregistered claim rule, and `delta_difficulty` is exactly the estimand v4r3
would register. **This is the fallback narrative** (§4.4).

### N5. Scientific-process narrative

**Thesis.** Four preregistered redesigns, each failing at the same place, expose
why conventional pairwise-compliance analysis misattributes compositional
degradation.

**Assessment.** True, well-documented, and *the sequence is genuinely
instructive* — v2 Gate 2 (pool too hard), v3 Gate 2A (pool mismatched on two
models, exchangeability failed on the other two), v4r1 (superseded: the wrong
crossing was inferred from a one-line reference), v4r2 Gate 2 (the focal
constraint's own vacuity). But NeurIPS is not a venue for a process memoir. Use
it as §6 of the paper (one page, one figure), not as the thesis.

### N6. A-general rather than pair-specific disruption

**Thesis.** The target is a broadly disruptive companion, not a specifically
anti-focal one.

**Evidence.** `Ξ` = −0.036 and −0.009 on the Gemmas — the target damages the
references about as much as it damages the focal constraint. Positive on the
Qwens (+0.131, +0.090) **only because the target *improves* reference compliance
there while `D(B←A)` is itself negative**, which supports nothing.

**Assessment.** `Ξ`'s half-width is ~0.11 against thresholds of 0.10 and 0.25.
It can show sign and rough size and nothing more. Report it; do not build on it.

### N7 (methodological side-finding, strong enough to name)

**One draw per cell throws away the effect.** v3 generated 16 draws per cell and
its registered estimator used **one**, hash-selected. Four measurements of the
same contrast on the same 36,864 rows per model:

| how the draws are used | E2B | E4B | source |
|---|---:|---:|---|
| the registered single hash-selected draw | **−0.0095** | +0.0651 | signed v3 result |
| all sixteen draws, cell mean (v4's registered estimator) | **+0.0639** | +0.0737 | `C18.json` |
| mean over 1,000 alternative draw selections | **+0.0889** | +0.0655 | `pseudo_runs.json` |
| greedy, T = 0, 96 blocks (unregistered, no interval) | **+0.1042** | +0.1111 | `greedy_run.json` |

Every one verified. The registered value is the *only* one of the four that is
negative on E2B, and it sits **below the 5th percentile of its own re-selection
distribution**, which is positive in **99.5%** of 1,000 draws. The draw-lottery
SD is 0.0354–0.0391 against a block SE of 0.039–0.042 — i.e. **the selection of
which sample to score contributes as much variance as the entire topic sample**.
v3's own change record quantifies ≈85% of the per-block variance of the
registered contrast as single-draw decoding noise.

Two honest caveats to carry: the all-draws estimator is post-hoc *relative to
v3*, though it is exactly what v4 registers prospectively; and the greedy row is
96 blocks with no interval and a per-block positive share of only 0.41/0.50, so
it is suggestive and not a result.

This deserves a subsection and possibly a figure. It is a concrete, quantified
warning about preregistered evaluation of stochastic decoders — and it is the
most portable single finding in the repository.

---

## 4. Recommended primary story

### 4.1 The recommendation

**Fuse N1 and N2, motivated by N3, with N7 as a named side-finding and N5
compressed into a design-evolution section.**

Working shape of the contribution (wording not locked in):

> A pairwise instruction-composition study on four small instruction-following
> models. We define an estimand set that separates generic compositional load,
> companion difficulty, companion class, focal position and pair-specific
> excess; we show that the standard control — a companion matched on marginal
> solo pass rate — is not a valid counterfactual for any of them; and we measure
> the pair-specific excess at 64,800 generations under pre-specified reading
> rules, finding it small relative to three structural channels the design does
> not control.

### 4.2 Why it dominates

- **It is the only narrative whose core does not depend on an unrun
  experiment.** N1's evidence chain is structural and already measured.
- **It converts the study's central obstacle into its contribution.** The
  reference pool has failed to admit valid controls in every version since v2.
  That is not a project setback to be apologised for; it is the result.
- **It is honest about tier.** Every number is exploratory or derived, and the
  paper can say so without losing its claim, because the claim is about
  identification rather than about an effect size.
- **It generalises.** Any benchmark composing verifiable constraints and
  matching controls on pass rate inherits the diagnosis.

### 4.3 Strongest defensible headline claim

> On four instruction-following models, companions matched to a target
> instruction on marginal solo pass rate to within 0.10 differ from it by up to
> 0.66 on chance-corrected instructed compliance, because the reference
> vocabulary consists of prefix-closed budget constraints that an unconstrained
> answer satisfies 2.5–89% of the time while the target's chance rate is 0.000.
> Under a companion-swap design using such controls, the excess loss
> attributable to companion identity is small — never reaching the
> pre-registered pair-specific threshold of 0.25 on any model, and lying wholly
> inside the ±0.10 generic-load band on three of four — while constraint class,
> focal position and prompt-induced vacuity each move focal compliance more.

Calibration: **systematic** for the identification claim (structural + measured
on four models); **hedged / narrow** for the effect-size claim (exploratory
scale, precision precondition met on one model of four).

### 4.4 Fallback narrative

The proposed v4r3 makes this fallback concrete rather than speculative: it
registers `δ_diff` as a **primary** estimand with its own precision precondition
(half-width ≤ 0.05) and its own claim rule, and §13.8 registers a
difficulty-support rule — the constraint that made the matrix screen's length
residual unidentifiable.

**If v4r3's difficulty-spectrum arm returns a robustly positive, identified
`delta_difficulty` for the target on three or four models**, promote N4 to
co-primary: *companion-specific interference is real but only visible as a
residual against a companion-difficulty surface, and matched-point designs
cannot see it by construction.* N1's chain is unchanged — indeed strengthened,
because the matched-point failure becomes the reason the effect was missed.

**If v4r3 returns a residual indistinguishable from zero**, N1+N2 stands
unchanged and gains a confirmatory-scale null on the difficulty axis.

### 4.5 The claim that would be too strong

Any of these would overstate the evidence:

- "Companion identity does not affect compliance." *(Never report "no effect"
  where the evidence is unresolved. Three of four models show equivalence at
  120 blocks with the precision precondition unmet on three.)*
- "Replicated across four models." *(Qwen3-4B's `Δ_R` averages one production
  and two budget companions; its class arm does not exist.)*
- "Matched controls." *(Only with "matched on marginal solo compliance to within
  0.10 on the calibration sample, and not matched on instructed compliance,
  response length or constraint class" attached.)*
- "Preregistered result." *(Nothing here is confirmatory. The reading rules were
  pre-specified; the experiment was not the registered one.)*
- "The pilot's effect was a vacuity artifact." *(§17.4's disposition is
  unresolved-with-both-bounds, which is stronger and different.)*
- "Δ_R is resolved." *(Resolved in the §17.4 agreement sense only. On the
  simultaneous scale E2B includes zero and E4B spans the 0.10 threshold.)*

---

## 5. Claim–evidence matrix

Models: **E2B** = `google/gemma-3n-E2B-it`, **E4B** = `google/gemma-3n-E4B-it`,
**Q4B** = `Qwen/Qwen3-4B`, **Q4BI** = `Qwen/Qwen3-4B-Instruct-2507`.
Uncertainty: block bootstrap, 10,000 resamples, the topic block as unit;
"sim" = studentised maximum-modulus simultaneous 95% interval within the named
family; "pct" = percentile 95%.

| # | Candidate claim | Evidence | Tier | Models | Estimator | Uncertainty | Supports | Limits / counterevidence | Placement | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| K1 | An unconstrained answer satisfies every registered reference by chance 2.5–89% of the time; the target's chance rate is 0.000 | matrix screen §25 cell, `results.json:accidental_compliance` | EXPLORATORY | all 4 | cell mean over 480 rows/model | reported as rates | N1 | screen topics, 120 blocks | Main | **STRONG** |
| K2 | 12/12 references matched to target on solo compliance; 2/12 on chance-corrected instructed compliance; 2 anti-productive | `section_13_2_v4/instructed_compliance.json` | DERIVED | all 4 | `(solo−chance)/(1−chance)` | none reported (point) | N1 | normalisation inflates magnitudes when chance is high; no CI computed | Main | **DEFENSIBLE WITH QUALIFICATION** — add intervals |
| K3 | Every reference family and the focal constraint are prefix-closed budgets; the target is not. Empty string: 94/94, 4/4, 0/8 | Amendment B §2; verifier definitions | REGISTERED DIAGNOSTIC (definitional) | all | enumeration over the 94-rung ladder | n/a | N1 | none found | Main | **STRONG** |
| K4 | v3's admitted references had 49–90% vacuous solo passes at 9–45 words vs target 0.000 at 269–323 words, and were satisfied in 2–8% of composed responses on E4B | `v3_reanalysis/`, Gate 2A cache | DERIVED from CONFIRMATORY rows | E2B, E4B | §9.3 predicate applied retrospectively | n/a | N1 | v3 registered no vacuity predicate — this is a re-description, not a v3 criterion | Main | **STRONG** (state the re-description) |
| K5 | The solo-compliance caliper destroys the variance needed to fit a difficulty relation (E2B: three references identical to 4 dp) | `v3_reanalysis/` | DERIVED | E2B, E4B | descriptive | n/a | N1, N4 | 3 points/model | Main | **STRONG** |
| K6 | Companion identity and response-length shift are collinear across the available companion set on all four models; the length residual is not identified | matrix screen `length_channel.A_within_support_of_fit.inside = False` ×4 | DERIVED | all 4 | OLS on 5 non-target companions | none | N1 | it is a support statement, not a test | Main | **STRONG** |
| K7 | `Δ_R` = +0.048 / +0.101 / +0.011 / −0.024; reaches 0.25 on no model; sim interval wholly inside ±0.10 on 3 of 4 | matrix screen `compliance.pooled_over_orders.families.primary` | EXPLORATORY | all 4 | paired block contrast, solo baseline cancels | sim over F1 = {D(B←A), D(A←B), Λ, Δ_R} | N2 | §16.2 half-width ≤0.05 met on Q4B only; §13.4 fires on both Gemmas; Q4B mixes classes | Main | **EXPLORATORY ONLY** |
| K8 | Raw and §17.4 vacuity-forced scales license the same reading on all four models (Δ_R moves ≤0.029) | matrix screen §17.4 recomputation | EXPLORATORY | all 4 | vacuous pass → failure, no row dropped | same | N2 | holds only under the floored stem | Main | **DEFENSIBLE WITH QUALIFICATION** |
| K9 | A production-class companion costs the focal constraint +0.601/+0.632 where the target costs +0.086/+0.228; `Δ_class` = −0.515 / −0.404 | matrix screen `class_control` | EXPLORATORY | E2B, E4B (+Q4BI, sign reversed) | paired block contrast | sim over the class family | N2 | **sign reverses on Q4BI (+0.088)**; Q4B has no class arm; class control is one-sided, target two-sided | Main | **DEFENSIBLE WITH QUALIFICATION** |
| K10 | Focal position costs 0.288/0.350; `Δ_R` changes sign between order strata on all four models | matrix screen order arms | EXPLORATORY | all 4 | within-block order factor | sim | N2 | a design property (the registered order puts the focal second in the target cell and first in the reference cells) as much as a model property | Main | **STRONG** (as a design finding) |
| K11 | Under the registered prompt, focal solo vacuity is 0.208–0.870 at every rung on all four models, against a registered ceiling of 0.10 | `cal_screen_v4/results.json:regime_adequacy_by_rung` | EXPLORATORY on REGISTERED inputs | all 4 | rate over 96 registered calibration topics at M=4 | none (rates) | N2, N5 | measured by a screen, not by a registered Gate 2 record | Main | **STRONG** |
| K12 | Under the registered §13.2 on the calibration sample and the repaired prompt, the registered reference pool admits **1, 2, 1, 2** families — fewer than the required three on every model | `cal_screen_v4/results.json:admission.registered_control` | EXPLORATORY | all 4 | registered `gates.admit_family`, byte-reproduced | Newcombe intervals inside the rule | N1 | not a Gate 3 result; Gate 3 has never run | Main | **STRONG** — and currently under-reported in the repo |
| K13 | On E2B an admitted reference out-damages the target: paired `Δ_1` = −0.078 [−0.134,−0.023] | matrix screen `per_reference_swap` | EXPLORATORY | E2B | paired block contrast | sim over {Δ_1,Δ_2,Δ_3} | N2, N6 | **the "disjoint intervals" gloss in the repo is arithmetically false** (§9.1) | Main | **DEFENSIBLE** via the paired estimator only |
| K14 | `Ξ` ≤ 0 on both Gemmas — the target damages references about as much as the focal constraint | matrix screen `reciprocal` | EXPLORATORY | E2B, E4B | DiD of delivery losses | sim, half-width ~0.11 | N6 | half-width exceeds both thresholds; positive on Qwens for a degenerate reason | Appendix | **EXPLORATORY ONLY** |
| K15 | The pilot's Δ = +0.343/+0.375 becomes +0.095/+0.068 under §17.4, and −0.057/−0.003 at matched length; its cells come from different topic sets and differ 5× in length | `pilot_reanalysis/` | DERIVED | E2B, E4B | forcing; bin-weighted matching | pct on raw only | N3 | length matching conditions on a post-treatment variable — reported as description | Main (as motivation) | **STRONG** |
| K16 | v3's registered contrast used 1 of 16 draws per cell; on all 16 it changes sign on E2B (−0.0095 → +0.0639) | `docs/v4_prefreeze/C18.json` | REGISTERED DIAGNOSTIC (pre-freeze check) | E2B, E4B | same estimator, different draw set | draw-lottery SD 0.036–0.039 vs block SE 0.039–0.042 | N7 | the all-draws estimator is post-hoc *relative to v3*, though preregistered in v4 | Main | **STRONG** |
| K16b | Over 1,000 alternative primary-draw selections, E2B `τ_target_first` has mean **+0.0889** and is positive in **99.5%** of them; the registered draw's +0.0069 sits **below the 5th percentile (+0.0295) of its own selection distribution**. E4B: mean +0.0655, 94.9% positive | `evidence/dci1-v3/*/pseudo_runs.json`, verified | REGISTERED DIAGNOSTIC (recorded, self-labelled unregistered sensitivity) | E2B, E4B | re-selection of the primary draw, selection domain kept separate | SD 0.0354 / 0.0391, vs block SE 0.039–0.042 | N7 | a sensitivity analysis, not an estimator; it does not license a positive reading | Main | **STRONG** |
| K16c | At temperature 0 on 96 blocks the same contrast is **+0.104** (E2B) and **+0.111** (E4B) — above the 0.10 SESOI on both | `evidence/dci1-v3/*/greedy_run.json`, verified | EXPLORATORY | E2B, E4B | one greedy draw per cell | **none computed**; per-block positive share 0.406 / 0.500 | N7 | 96 blocks, no interval, unregistered, and the per-block sign share is ~balanced — suggestive only | Appendix | **EXPLORATORY ONLY** |
| K17 | v3 returned 4/4 primary estimands direction-unresolved; exchangeability failed in **all four analyses**; both Qwens terminal at Gate 2A | `dci1/RESULTS_V3.md`; signed `analysis/{masked,unmasked}/result.json` | **REGISTERED / CONFIRMATORY** | all 4 | registered v3 estimator | sim | N5 | this is the only confirmatory tier in the study | Main | **STRONG** |
| K17b | v3's two equivalence emissions are **phase-specific in opposite directions and marginal**: E2B `τ_target_first` is equivalence unmasked ([−0.0799,+0.0938]) but not masked ([−0.1037,+0.0759], missing by 0.0037); E4B `τ_added_first` is equivalence masked ([−0.09988,+0.05474], inside by **0.00012**) but not unmasked | signed v3 `result.json`, recomputed | **REGISTERED / CONFIRMATORY** | E2B, E4B | `licensed_equivalence` on the simultaneous interval | sim | N5, N7 | neither survives the other analysis phase; both hang on <0.004 of interval width | Main | **STRONG** — and materially qualifies K17 |
| K17c | v3's composed uptake of the companion collapses for references: E2B AB 0.357 vs AR3 **0.021**; E4B AB 0.438 vs 0.073 / 0.042 / 0.099, **all three flagged** | signed v3 `uptake_intervals`, `per_arm` | **REGISTERED / CONFIRMATORY** | E2B, E4B | paired block contrast | sim | N1 | uptake is an outcome, so this diagnoses the control rather than adjusting it | Main | **STRONG** — independent confirmation of K4 from signed records |
| K18 | Δ^A = +0.064 [+0.041,+0.087] / +0.074 [+0.052,+0.095] (all draws); below the 0.10 generic-load threshold; survives §17.4 and length matching | `v3_reanalysis/result.json` | DERIVED from CONFIRMATORY rows | E2B, E4B | paired block contrast, 384 blocks, 16 draws | pct + sim per reference | N1, N4 | per-reference values on E2B are +0.056, +0.142, **−0.006** — the pooled number describes none of them | Main | **DEFENSIBLE WITH QUALIFICATION** |
| K19 | In the one configuration where the arms are naturally length-balanced, Δ^A = +0.047 on **both** models | `v3_reanalysis/` | DERIVED | E2B, E4B | order-split, bin-matched | 5 of 6 bins supported | N1, N4 | a sub-population description, not a causal decomposition | Main | **DEFENSIBLE WITH QUALIFICATION** |
| K20 | The target's residual above the companion-difficulty line is +0.067 / +0.118 and identified; −0.050 / −0.048 on the Qwens | matrix screen `companion_difficulty_v5` | DERIVED | all 4 | OLS on 5 companions excluding the target | **no interval computed** | N4 | 5 points; 2 of 4 negative; no preregistered rule | Main (as open question) | **EXPLORATORY ONLY** — needs an interval |
| K21 | Verifier §10.2 holds for the target, the focal constraint and all eight registered families: determinism 1.000 over 1,311,582 verdicts/process × 672 processes; boundary 1.000 on 45 cases/family; independent reimplementation 1.000 over 14,046 texts | `gate1_v4/section_10_2*.json` | REGISTERED DIAGNOSTIC | all | three-process determinism, authored boundary suites, prose-only reimplementation | exact rates | methods | §10.3 human validation **unavailable**; §10.4 not run | Main + Appendix | **STRONG** |
| K22 | A defect was found in the *validation* instrument, not the instrument under study (`[^\W\d_]+` admits 1,151 non-decimal numerics) | `ENDPOINT` §4 | REGISTERED DIAGNOSTIC | all | differential test over the BMP + astral letter blocks | n/a | methods | none | Appendix | **STRONG** |
| K23 | Companion identity affects focal compliance beyond generic difficulty | — | — | — | — | — | — | no design has produced it at any tier | — | **UNSUPPORTED** |
| K23b | v2's two Qwen pilots "found equivalence" | v2 `derived/primary/analysis.parquet` | TERMINAL / NON-IDENTIFIED | Q4B, Q4BI | v2 pilot estimator | CI [0,0] | — | **28 of 29 estimands are exactly 0.0 with CI [0,0] and the failure taxonomy is empty over all 336 rows.** These are degenerate artifacts and must never be cited as equivalence | — | **FALSIFIED as a reading** |
| K24 | The pilot's Δ is pair-specific (`H1_PAIR_SPECIFIC`) | pilot `result.json` | EXPLORATORY | E2B, E4B | cross-topic-set difference | pct | — | K15 | — | **FALSIFIED** as a licensed reading |
| K25 | `delta_difficulty` for the target is positive and identified at confirmatory precision | v4r3 | NOT RUN | — | — | — | N4 | — | — | **PENDING CURRENT EXPERIMENT** |

---

## 6. Proposed paper structure

Nine content pages. Target allocation in parentheses.

**1. Abstract** (one paragraph — the `.sty` enforces it).
Field → the gap (composition is measured by load, not by counterfactual) →
contribution (an identification framework + a diagnosis of control failure +
a measurement) → evidence with numbers → impact. *Must not* assert a confirmatory
result or "no effect".

**2. Introduction** (1 p.).
Claims named and previewed; contributions list at the end pairing each claim with
its strongest evidence. Must state, in the introduction, that the measurement is
screen-scale and licenses no confirmatory claim — `guidelines-narrative-and-process`
and checklist Q1 both require the scope to be in the abstract/intro, not buried.

**3. Related work** (0.75 p.).
**Currently unwritable — see §9.8.** The repo has no `.bib` and five ML
citations. Needs a fresh literature search. Deltas to write: vs load evaluation
(IFEval, ComplexBench, FollowBench-class); vs constraint-saturation work
(Vasileva 2026); vs symmetric co-failure statistics; vs LLM-as-judge evaluation.

**4. Problem definition and identification framework** (1.25 p.).
The compliance vector as primitive. Delivery loss `D(c←g)`. The five confounded
quantities and the estimand that isolates each: `Λ` (asymmetry), `Δ_j`/`Δ_R`
(companion swap), `Ξ` (outcome specificity), `Δ_class` (class), the order factor
(position), `delta_difficulty` (difficulty residual). **What each estimator
identifies and under what assumption** — this section is where the paper earns
its contribution, and it must not conflate swap effect, co-failure, and pairwise
interaction. *Claims not to make: that `Ξ` separates the pair-specific from the
A-general reading at this precision.*

**5. Experimental design** (1.25 p.).
Four models with pinned revisions; 25-cell block; both orders within block; the
topic construction and the five reserved sets; verifiers and their §10.2
evidence; the block bootstrap and the simultaneous-interval family structure;
the pre-specified reading rules; the vacuity predicate and the dual scale.
*Claims not to make: that this is the registered confirmatory design.*

**6. Why the control fails** (1.75 p. — the core).
The five-line chain of N1. Figure 1 lives here or in §1. *Claims not to make:
that a corrected caliper is proposed and validated — it is not.*

**7. Measurement** (1.5 p.).
`Δ_R` and the three dominating channels. Table 3. Figures 3–5. Dual bounds.
*Claims not to make: replication across four models; resolution at the
registered precision.*

**8. Design evolution** (0.5 p. + appendix).
v2 → v3 → v4r1 → v4r2 as a table: what each could identify, what ran, what
failed, what it taught. Include N7 (the draw lottery) here or as its own
subsection in §7. This is where the honest history goes, compressed.

**9. Limitations** (0.5 p., named section — the checklist explicitly encourages
one).
No confirmatory data; precision precondition met on one model of four; four
models, two families, 2–4B, one backend, one workstation; human verifier
validation unavailable; length channel unidentified; Qwen3-4B's mixed-class
`Δ_R`; evidence not version-controlled (§9.7).

**10. Broader implications** (0.25 p.).
For benchmark builders: pass-rate matching is not difficulty matching; report
chance-corrected compliance; balance constraint position; check vacuity.

**11. Conclusion** — *omit* unless space allows. `guidelines-conclusion.md`:
prefer omission to padding when the Discussion closes the paper.

**Appendices** (no page limit), in the canonical order from
`guidelines-appendix.md`: A derivations (estimand algebra, why the solo baseline
cancels in `Δ_R`); B protocol detail, seeds, decoding, compute; C additional
results (full estimand tables, per-model admission tables, the four screens);
D qualitative samples with the selection protocol; **E citation verification
register**; **F result-insertion map** (v4r3); G reproducibility and artifact
statement; H tacit knowledge (the four failure modes, the validator defect).

---

## 7. Figure and table plan

Every entry states: question → source → tier → variables → uncertainty → why
visual → placement.

### Figure 1 (headline) — "Matched on what?"
- **Question.** Are companions matched on solo pass rate matched on the thing
  the counterfactual needs?
- **Form.** Two-panel composite. **Left:** scatter, x = solo compliance,
  y = chance-corrected instructed compliance, one marker per companion per model
  (16 references + 4 targets + 4 focal constraints), the ±0.10 caliper drawn as
  a vertical band around each model's target and a horizontal band at the same
  width. **Right:** effect ladder — |Δ_R|, |Δ_class|, position effect, vacuity
  share, per model, with 0.10 and 0.25 marked.
- **Takeaway sentence.** *Twelve of twelve references fall inside the caliper on
  the axis the design matches on, two of twelve on the axis the counterfactual
  needs — and the companion-identity effect is the smallest of the four
  channels.*
- **Source.** `section_13_2_v4/instructed_compliance.json`;
  `matrix_screen_v4/results.json`.
- **Tier.** EXPLORATORY / DERIVED — label on the figure.
- **Uncertainty.** Right panel: simultaneous intervals. Left panel: points; add
  bootstrap intervals (currently missing — see K2).
- **Placement.** Main, page 1.

### Figure 2 — Identification diagram
- **Question.** What does the companion swap hold fixed, and what does it not?
- **Form.** Schematic: the 25-cell matrix, the two cells `Δ_R` differences, and
  four annotated arrows for the channels that move between them (class,
  position, length, accidental compliance).
- **Placement.** Main, §4. **Necessary** — the estimand set is the contribution
  and prose alone will not carry it.

### Figure 3 — Difficulty and length surfaces
- **Question.** Does companion difficulty explain the loss, and can the length
  account be tested?
- **Form.** 2×4 small multiples. Top row: `D(B←g)` vs companion solo compliance,
  fit on non-target companions, target highlighted, fit support shaded. Bottom
  row: same against companion length shift, with the target **outside** the
  shaded support on every model.
- **Takeaway.** *The target's difficulty residual is identified and positive on
  the Gemmas; its length residual is not identified on any model.*
- **Source.** `matrix_screen_v4/results.json:{companion_difficulty_v5,
  length_channel}`.
- **Uncertainty.** Bootstrap the residual — **currently not computed** (K20).
- **Placement.** Main, §7.

### Figure 4 — Per-reference heterogeneity and reciprocity
- **Form.** Forest plot: `Δ_1, Δ_2, Δ_3, Δ_R, Ξ` by model, simultaneous
  intervals, zero and ±0.10/0.25 marked.
- **Takeaway.** *On E2B one reference out-damages the target; `Ξ` ≤ 0 on both
  Gemmas.*
- **Note.** Use the **paired** `Δ_j`, not a comparison of marginal `D(B←·)`
  intervals — see §9.1.
- **Placement.** Main, §7.

### Figure 5 — Position dominates identity
- **Form.** Slope chart: `D(B←·)` and `D(A←·)` by focal position, per model;
  inset showing `Δ_R` by order stratum with the sign flip.
- **Placement.** Main, §7.

### Figure 6 (appendix) — Vacuity
- **Form.** Heatmap: focal solo vacuity by rung × model × stem, 0.10 ceiling
  marked; plus a three-bar panel for the pilot Δ (raw / §17.4-forced / ≥20-word
  restricted) making the point that the restriction is the wrong operation.
- **Placement.** Appendix C, referenced from §5 and §6.

### Table 1 — Models, protocol versions, evidential status
Model key, HF id, pinned revision, family, thinking policy, dtype, TP, max len;
per model: v2 outcome, v3 outcome, v4 status, which screens include it.
**Tier column mandatory.**

### Table 2 — Estimands
Symbol, definition, what it identifies, what it does not, registered threshold,
family membership. Includes the warning that `τ` (v2/v3), `ι` (v4r1) and
`Δ^A`/`Δ_R` (v4r2) are different quantities under partly shared symbols.

### Table 3 — Main estimates
Four models × {`D(B←A)`, `D(A←B)`, `Λ`, `Δ_R`, `Δ_j`, `Ξ`, `Δ_class`}, point +
simultaneous interval + half-width + whether the §16.2 precondition is met.
Both scales (compliance and §17.4-forced). **Blocks, draws per cell, and the
resampling unit in the caption.**

### Table 4 — Alternative explanations and discriminating tests
Adapted from `ENDPOINT_2026-08-20.md` §6: explanation, status, discriminating
evidence, what would change it. Nine rows.

### Table 5 (appendix) — Reference admission
Per model per pool: families admitted under the full registered §13.2, under
conditions 1∧6 only, and under the relaxed criterion the matrix screen used —
because the three differ and the difference is scientifically load-bearing.

---

## 8. NeurIPS readiness

### 8.1 Checklist readiness map

| # | Item | Status | What is needed |
|---:|---|---|---|
| 1 | Claims match contributions/scope | **needs paper text** | The scope sentence ("exploratory, screen scale, licenses no confirmatory claim") must appear in the abstract and intro |
| 2 | Limitations discussed | **needs paper text** | Named section; §6 above lists the content |
| 3 | Theory assumptions/proofs | **ready (N/A)** | No theorems. If the estimand algebra is stated formally, number it and put the derivation in Appendix A |
| 4 | Reproducibility disclosure | **ready** | Pinned revisions, dtype, TP=1, `max_model_len=4096`, gpu-mem-util, temperature 0.7 / top_p 0.9 / per-row seeds, topic construction, verifier definitions, block bootstrap. All exists |
| 5 | Open access to data and code | **UNRESOLVED — highest risk** | `dci1/evidence/` (1.85 GB) is **gitignored by design**; nothing is committed. Needs a decision on release, an anonymised artifact, and per-experiment scripts. See §9.7 |
| 6 | Experimental settings in the core of the paper | **needs paper text** | §5 |
| 7 | Error bars defined and correct | **partly ready** | Bootstrap over topic blocks, 10k resamples, simultaneous within named families — all recorded. **Missing:** intervals for K2 (instructed compliance) and K20 (difficulty residual). Also must state SD-vs-SEM explicitly and avoid symmetric bars on bounded rates |
| 8 | Compute resources | **needs artifact** | Per-run wall clock is not currently aggregated. Also required: total across the project **including unreported/failed runs** — v2's four terminal replications, v4r1 (no data), the four screens, and the superseded FORM×STEM reading |
| 9 | Code of ethics | **ready** | |
| 10 | Broader impacts | **needs paper text** | Evaluation methodology; low direct-harm surface; the honest impact is on benchmark construction |
| 11 | Safeguards | **ready (N/A)** | No dual-use release |
| 12 | Licenses for existing assets | **needs artifact** | Gemma Terms of Use and Qwen licence per checkpoint, **plus `openai/gpt-oss-20b`** (the pinned §10.4/v3 autorater, revision `6cee5e81…`), plus vLLM 0.15.1+rocm720 / ROCm / PyTorch versions with licences |
| 13 | New assets documented | **needs artifact** | The topic bank, the constraint ladder, the verifiers and the boundary suites are new assets. A datasheet must ship *with* them |
| 14 | Crowdsourcing / human subjects | **UNRESOLVED** | Depends on whether the 692-item author-annotation session runs. If any human labels appear in the paper, this triggers: verbatim instructions, interface screenshots, compensation |
| 15 | IRB | **likely N/A** | Only if 14 triggers |
| 16 | LLM usage declaration | **needs paper text** | **Yes.** LLMs are the object of study *and* an LLM is the measurement instrument: v3's signed `verifier_freeze.json` pins `openai/gpt-oss-20b` @ `6cee5e81…`, greedy, 2,048 new tokens, `reasoning_effort: high`, `prompt_version gate1-judge/2.0.0`, as the autorater whose calibration is v3's `measurement_basis`. Must be declared at methods level, with the judge's own validation status |

### 8.2 Statistical-reporting requirements the paper must meet

NeurIPS asks for six things the repository can supply but the manuscript must
state explicitly:

1. **The factor of variability.** Here it is the topic block, not the seed and
   not the draw. Say so.
2. **The estimator.** Block bootstrap, 10,000 resamples, studentised
   maximum-modulus for simultaneous coverage within a named family.
3. **SD vs SEM.** The tables report clustered SE and interval bounds; state it.
4. **Sigma level in words.** These are 95% bootstrap intervals, not ±kσ; state
   that Normality is not assumed, which is exactly why a bootstrap is used.
5. **No symmetric bars on bounded rates.** Compliance rates are in [0,1]; the
   percentile bootstrap already respects this — do not substitute mean ± k·SE.
6. **Describe the calculation in the prose.** Not only in captions.

Plus the repository's own standard, which is stricter and should be kept: every
estimate carries its block count, its draws per cell, its order stratum, its
reference identities, and whether those references met their registered validity
criteria.

---

## 9. Contradictions, errors and risks

Found by reading artifacts against reports. **Numbers were re-extracted from
`results.json` and recomputed where feasible; nothing below was taken on the
reports' word.**

> **Update, 2026-08-21.** §9.1 through §9.5 were **corrected on the
> researcher's instruction** after this packet was first delivered. Seventeen
> edits across `RESEARCH_STATE.md`, `CHANGES_SCIENTIFIC.md`,
> `ENDPOINT_2026-08-20.md`, `INVESTIGATION_2026-08-20.md`,
> `DCI1_v4r2_to_v4r3_changelog.md` and `DCI1_preregistration_v4r3.md`, recorded
> in a `CHANGES_SCIENTIFIC.md` entry rather than made silently. No artifact,
> estimate or verdict moved: `matrix_screen_v4/results.json` was regenerated and
> diffed key-by-key with **0 values changed, 0 keys added, 0 keys removed**.
> The findings below are retained as the record of what was wrong. §9.6 through
> §9.11 are **not** fixed and remain open.

### 9.1 "Intervals disjoint" is arithmetically false (two documents)

**FIXED.** All four sites now quote the paired `Δ_1` = −0.078 [−0.134, −0.023] and state explicitly that the marginal intervals overlap. A fifth site missed on the first pass (`INVESTIGATION_2026-08-20.md:47`) was corrected too.

`RESEARCH_STATE.md` §4f and `ENDPOINT_2026-08-20.md` §5 both assert that on E2B,
`D(B←R_1)` and `D(B←A)` have **disjoint** intervals. They do not, on either
scale:

| | `D(B←A)` | `D(B←R_1)` | overlap |
|---|---|---|---|
| percentile | [+0.0312, +0.1427] | [+0.1208, +0.2073] | **yes**, 0.022 wide |
| simultaneous | [+0.0164, +0.1565] | [+0.1132, +0.2160] | **yes**, 0.043 wide |

The *claim* is nonetheless correct, via the right estimator: the paired
contrast `Δ_1` = −0.0781, simultaneous [−0.1337, −0.0226], lies entirely below
zero. **Impact on the paper:** use the paired estimator and delete the
marginal-interval gloss. Comparing two marginal intervals is the wrong test
regardless, and a reviewer will catch it.

### 9.2 "0.208–0.659" is a range of minima, not a range of values

**FIXED** at all nine sites, including the two v4r3 documents. The corrected phrasing is "at least 0.208, and as much as 0.870, at every rung", which preserves the point that no rung could pass.

The vacuity figure is quoted as a range in four documents (`RESEARCH_STATE.md`
§4e and §4g, `ENDPOINT` §1 and §9, `CHANGES_SCIENTIFIC.md`,
`INVESTIGATION_2026-08-20.md`). The source table
(`cal_screen_v4/REPORT.md:85`) is correct and labels its last column **min**.
Recomputed from `results.json`, over all 24 rungs × 4 models under the
registered stem: **min 0.2083, max 0.8698**. `0.208–0.659` is the range of the
four **per-model minima** (0.339, 0.208, 0.312, 0.659). The conclusion is
unaffected and in fact strengthened; the number as published is wrong.

### 9.3 "Under the mean reading nothing runs on any model under any stem" is false

**FIXED** in both documents.

`RESEARCH_STATE.md` §4e and `INVESTIGATION` §7 state this. Recomputed:
`qwen3-4b-instruct-2507`, floored stem, m = 10 has
`feasible_mean_reading = true`. The calibration screen's own report says the
same thing from the other side — *"m = 10 is the only rung on any model feasible
under **both** readings of the graded clause"*. The correct statement is:
**under the mean reading nothing runs on three of four models; on the fourth,
exactly one rung survives.** This matters because it changes the framing of
researcher decision 1.

### 9.4 Two interval conventions circulate under the same estimand

**FIXED.** Both sections now name their convention and state that the simultaneous scale governs where the two disagree.

`RESEARCH_STATE.md` §4f quotes **percentile** intervals for `Δ_R`
(E2B [+0.009,+0.087]); `ENDPOINT` §5 quotes **simultaneous** ones
(E2B [−0.002,+0.098]). Both are in the artifact and both labels are honest, but
E2B's `Δ_R` **excludes zero on one and includes it on the other**, and §4f is
the document a reader reaches first. §4g flags the discrepancy; §4f does not
carry the flag. **The paper must fix one convention** — the simultaneous one,
since the estimands are read as a family.

### 9.5 The matrix screen's reference sets are not the registered pool

**FIXED.** Scope notes carrying the disposition and both sensitivities were added to `RESEARCH_STATE.md` §4f and `ENDPOINT` §5.

`admission.matrix_reference_set.disposition` reads: *"conditions 1 and 3-6 as
registered on the 96 calibration topics; condition 2 with its registered
one-draw §12.2 input, applied where that input exists."* Sensitivities in the
same artifact:

- `strict_registered_precision` on E2B admits `{CR6, RF3, CL7, CL8, CR4}` — and
  **RF2, one of the three references actually used, is not in it**.
- `sensitivity_condition_2_at_M_cal` on E2B admits only `{CL7, CL8, CR4}` —
  **all three production-class**, which would make `Δ_R` a different quantity.
- Condition 2's own input has a median paired SE of **0.104** at one draw
  against a caliper of **0.15**; it is noise-limited.

**Impact:** every `Δ_R` number is conditional on a reference-admission reading,
and the paper must say which and show Table 5.

### 9.6 A stronger result than the repo currently headlines

Under the **full registered §13.2** on the registered calibration sample with
the repaired prompt, the registered reference pool admits **1, 2, 1, 2**
families across the four models — below the three the design requires, on every
model (`admission.registered_control`). The Amendment-B candidate families admit
**2, 0, 1, 2**. Only the *enlarged* pool (registered + candidates + production
class) reaches three (5, 3, 3, 5). `RESEARCH_STATE.md` §4e reports the enlarged
count; the registered-pool count is the one that speaks to identification and it
is not headlined anywhere. It belongs in the paper as K12.

### 9.7 The evidence is not version-controlled

`dci1/.gitignore` line 4 excludes `evidence/`, deliberately (*"runs must never
dirty the Git worktree"*). **`git ls-files dci1/evidence` returns zero files**
against **1.85 GB on disk**. Generation is stochastic (temperature 0.7,
top_p 0.9, per-row seeds) on a pinned vLLM/ROCm stack, so re-generation is
statistically equivalent, not byte-identical.

The durable mirror does not cover the work the paper would rest on. Verified
file counts:

| tree | `evidence/` | `durable_root/` |
|---|---:|---:|
| `dci1-v3` | 654 | 630 (626 of 630 common files byte-identical; the 4 that differ are lock files) |
| `dci1-v4` | 158 | 158 |
| `dci1-v2` | 235 | 272 (partial replica of `{cache, prompts, selection}` only, plus an orphan test tree) |
| `fs-screen-v4` | 28 | **0** |
| `bgrid-screen-v4` | 28 | **0** |
| `cal-screen-v4` | 112 | **0** |
| `matrix-screen-v4` | 28 | **0** |
| `br-pilot-v4` | 14 | **0** |

**Every one of the four screens and the pilot — the source of every headline
number in narratives N1, N2 and N3 — has no mirror, no manifest, one copy, on
one machine, on an unpushed branch.** Combined with checklist Q5, this is the
single largest publication risk: **every number in the proposed paper rests on
artifacts that do not survive a clone or a disk failure.**

The v3 tree is the counter-example and should be the model: its HMAC-SHA256
signature chain verifies end to end (8 signatures recomputed, predecessor chains
intact on all four models), `body.result_hash` in each signed record equals the
sha256 of the corresponding `analysis/*/result.json` (4/4), and the confirmatory
`cache.jsonl` sha256 `f74402e8…` equals `output_hashes.cache` in the signed
manifest. τ recomputed from the raw rows matches the signed values to twelve
decimal places. **The confirmatory tier is cryptographically bound to its
numbers; the exploratory tier is not bound to anything.**

### 9.8 Related work is effectively absent

No `.bib` file exists anywhere in the repository. Five scholarly
instruction-following citations exist in total: Vasileva 2026 (the one close
paper, cited once with no engagement with its findings), IFEval and ComplexBench
(cited only as *verifier precedents*, never as results), Bean et al. 2025
(construct validity), Geirhos et al. 2020 (shortcut learning). **Zero hits** for
FollowBench, InfoBench, CoDI, Multi-IF, CELLO, FollowEval, SysBench, RuleBench,
CFBench, IFBench. There is no direct DCI-vs-IFEval comparison anywhere. Every
novelty claim in §3 therefore **requires external verification** and belongs in
the citation verification register until checked.

### 9.9 Remaining risks

- **No confirmatory tier for any headline number.** The only
  REGISTERED/CONFIRMATORY evidence in the study is v3's, and it is four
  unresolved estimands plus a failed exchangeability check.
- **Precision.** §16.2's half-width ≤ 0.05 is met on one model of four at 120
  blocks. §17.3's guarded emitter would refuse the equivalence statement on the
  other three.
- **Qwen3-4B's `Δ_R` mixes classes** (one production, two budget companions) and
  is not comparable to the other three.
- **Human verifier validation is unavailable.** §10.3 cannot be met — the only
  annotator is the study author. Author labels are §10.4 diagnostic input and
  **must never be described as independent validation** in any artifact.
- **Model scope.** Four checkpoints, two families, 2–4B parameters, one
  workstation, one backend, TP = 1.
- **The measurement instrument is itself an LLM.** v3's `measurement_basis` is
  `autorater_calibration_approved` with a pinned `openai/gpt-oss-20b` judge.
  Calibration agreement was 0.935–0.992 with 3–12 disagreements per model, and
  the 56-item author-performed blind calibration is recorded in the sign-off as
  **"NOT registered A1 validation"**. A reviewer will ask what validates the
  validator.
- **Symbol drift across versions.** `τ`, `D`, `Δ`, `S` and `F2` denote different
  quantities in v2/v3, v4r1 and v4r2. A reader tracking symbols rather than
  definitions will conclude v3 and v4 measured the same thing. Table 2 must
  prevent that.
- **Which Δ^A to quote.** The v3-registered value (one draw) and the all-draws
  value differ in sign on E2B. Whichever is quoted must be labelled.

---

### 9.10 A committed derived artifact is stale and contradicts the evidence

`dci1/reports/readiness_v3.json` is **tracked** and records all four models at
`"state": "REGIME_SCREEN_PASS", "terminal": null`, with `test_results` and
`synthetic_lifecycle` both `null`. The signed evidence shows the two Gemmas at
`UNMASKED_ANALYSIS` and both Qwens **terminal at Gate 2A**. It is one of only
two committed v3 report files, so anything reading it for current state gets the
wrong answer. Per `CLAUDE.md` it must be **regenerated by its script**, not
hand-edited.

### 9.11 Dangling and unsigned artifacts in the v4 tree

Flagged by the inventory sweep and worth resolving before any artifact release:
`gate1_v4/` content is hashed but **not signed** (unlike v3);
`annotation/key_sealed.json` is plaintext; `section_10_4_probe.json` names a run
directory that does not exist; `judge_runs/carried-medium-rep0/` is missing
`plan.json`, `design.jsonl` and `backend.log` and names a `plan_source` that is
absent; `qwen3-4b` appears in no Gate-1 judge run; and
`gate1_v4/section_10_2_families.json` — the only §10.2 evidence for RF1–RF8 — is
untracked. Also: `gemma-3n-e4b-it` has **no v2 calibration evidence at all**
(a 1,824-row run aborted at 64 rows on a vLLM engine-init failure), which is why
v2's E4B numbers are absent rather than negative.

## 10. What can be written now

Sections whose evidence is stable and complete:

- **§4 Problem definition and identification framework** — the estimand set is
  implemented, tested and documented.
- **§5 Experimental design** — models, revisions, decoding, topics, verifiers,
  §10.2 evidence, bootstrap, family structure, pre-specified reading rules.
- **§6 Why the control fails** — the entire N1 chain (K1–K6, K12), plus K15 as
  motivation.
- **§7 Measurement** — K7–K11, K13, K14 with exploratory labelling, and K16–K19.
- **§8 Design evolution** — v2/v3/v4r1/v4r2 are closed and fully documented.
- **§9 Limitations**, **§10 Broader implications**.
- **Table 1, Table 2, Table 4, Table 5**; **Figures 1, 2, 4, 5, 6**.
- Checklist items 1, 2, 3, 4, 6, 9, 10, 11, 16.

Two small analyses would make §6 and §7 publication-grade and are cheap
(recomputation only, no generation):

- bootstrap intervals for chance-corrected instructed compliance (K2);
- a bootstrap interval for the difficulty residual (K20), which Figure 3 needs.

## 11. What must wait

- **Any claim that `Δ_R` is confirmatory**, or that the axis is resolved at the
  registered precision. Requires 384 blocks under a frozen protocol, which
  requires Gate 1 approval, which requires the reference pool to be final.
- **`delta_difficulty` as an estimand with a claim rule** (K25). Now
  *specified* — v4r3 §11.7 and §13.6–13.8 — but not run: **408 blocks at M = 4,
  76,704 generations per model, 306,816 total**. Preregistration proposed and
  unsigned; **no code, no data**. The result-insertion map (Appendix F) can now
  be built against a concrete design, which is worth doing early because it makes
  the eventual insertion mechanical.
- **Figure 3's headline framing.** It can be drawn now as an open question; it
  cannot be framed as a result until the residual carries an interval and
  ideally a spectrum arm at confirmatory scale.
- **Checklist Q14/Q15** — depend on whether the 692-item annotation session runs.
- **Checklist Q5 and Q13** — depend on the artifact-release decision (§9.7).
- **Any statement about the registered pool's admission result.** Gate 3 has
  never run on any model; the screens' tables are not a substitute and the
  paper must not present them as one.
- **Related work** — blocked on a literature search that has not been done.

---

## 12. Researcher decisions requested

Only the decisions that genuinely require judgement. Everything else in this
packet is either measured or mechanical.

**D1 — The paper's genre.** Submit as a *measurement and identification study*
that openly carries no confirmatory tier (recommended: N1+N2), or hold the paper
until v4r3 produces confirmatory-scale evidence on the difficulty axis. This is
the biggest call and everything else follows from it. Cost of waiting: ~307k
generations plus a preregistration. Cost of not waiting: every headline number
is labelled exploratory.

**D2 — Whether to run v4r3 before writing**, and at which allocation (408 blocks
at M = 4 is the minimum that meets the preconditions at φ = 0.37; 384 at M = 8
also meets them at 144,384 generations per model).

**D3 — ~~The reporting errors~~ DONE (2026-08-21).** §9.1–§9.5 corrected on
your instruction, recorded in `CHANGES_SCIENTIFIC.md`, artifacts verified
unmoved. §9.6–§9.11 remain open; of those, **§9.7 (single-copy evidence) is the
one that is urgent independently of the paper** — see D4.

**D4 — Artifact durability and release (§9.7).** Two decisions, and the first is
urgent independently of the paper. **(a) Backup:** the four screens and the
pilot — 210 files carrying every headline number in N1–N3 — exist as a single
copy, with no durable mirror, no manifest, on one machine, on an unpushed
branch. v3's signed-and-mirrored tree shows the pattern that should be applied.
**(b) Release:** full release, a scored-row release (verdicts, word counts and
hashes without raw generations), or a documented regeneration path stating that
byte-reproduction is not claimed. (b) determines checklist Q5 and Q13; (a)
determines whether there is anything left to release.

**D5 — Which `Δ^A` the paper quotes** (v3-registered single-draw, or all-draws),
and whether N7 (the draw lottery) is promoted from a subsection to a named
contribution. It is a strong, self-contained methodological result.

**D6 — Adopt v4r3, and in what order relative to the paper.** The proposed
revision is complete and closes V5, changes the difficulty coordinate, and
resizes the study. Adopting it makes N4 testable and makes N1 part of a
diagnosis-and-repair arc; not adopting it leaves the paper as N1+N2 alone.
Adoption is also the gate on Gate 1, since the reference vocabulary changes.

**D7 — Scope of the related-work search.** N1's novelty claim is unverified
against the literature. Whether to commission a proper search now or draft §6–§7
first and position afterwards.

---

STOPPING POINT: narrative/evidence review complete; manuscript drafting has not begun.
