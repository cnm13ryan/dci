# DCI-1 v5 Readiness Audit

**What the confirmatory data actually support, whether v5's registered analyses can settle the
companion-specificity question, and three defects executing on the GPUs at the time of writing.**

| | |
|---|---|
| Audit date | 2026-08-23 |
| Repository | `dci`, branch `feat/dci1v4-fresh-study`, HEAD `b32c4b6`, working tree clean |
| Mode | Read-only. Nothing in the repository was changed. |
| v5 registration | manifest `70608e5d…` at `5e35ca6` — itself superseded by amendment A2 at `cd4b1b1` |
| Test state | `dci1/tests_v5` 383 passed |
| Companion documents | [`AUDIT_2026-08-23_v4r4_evidence.md`](AUDIT_2026-08-23_v4r4_evidence.md) · [`AUDIT_2026-08-23_v5_design_execution.md`](AUDIT_2026-08-23_v5_design_execution.md) |

> **Two audits, run independently.** This document and the companion pair above were produced
> in separate sessions against the same commit. They agree on every load-bearing finding — the
> non-identification of every companion-specific estimand in v4r4, the staleness of
> `RESEARCH_STATE.md`, and defects F1 and F2 below. The companion audit goes further on prior
> work (seven mandatory items retrieved and read) and on the executed-study defects, adding two
> this document does not carry: no core-without-spectrum path in `stages/selection.py`, and
> §7.2's focal extension {15, 16} never being measured. Where they differ in emphasis, read them
> together; where a number appears in both, they were derived independently and match.

---

## 0. Bottom line — five things, in the order they matter

1. **v5 is live and mid-flight, and `RESEARCH_STATE.md` says it is not.** §4b still reads "no
   stage record, no instrument measured, no generation." Both Gemma replications hold signed
   `GATE_0_APPARATUS`, `REGIME_SCREEN` and `GATE_1_MEASUREMENT` records, and Gate 2's candidate
   calibration was generating on both GPUs during this audit. **238,912 real generations** exist
   under the registered namespace.

2. **Gate 2 is going better than v4r4 did, on the two live models.** B's vacuity is 0.000 at
   every rung, the operating point is bracketed on both, and D17's construct floor passes with
   room. The κ^B cliff that D17 was derived from reproduced prospectively on models it
   was not fitted to.

3. **Three live defects, all of the repository's own signature class** — a producer whose
   consumer never reads it. One means §12.6's candidate expansion, which exists specifically to
   repair v4r4's F5, *has never run*; another means Gate 2 is generating 2.9× the registered
   calibration budget.

4. **The confirmatory data do not support a pair-specific claim, and the one companion contrast
   that exists points the other way.** On `qwen3-4b` the excess of A over a same-form,
   ι-matched marker companion is bounded inside ±0.07 — under the source memo's 0.10
   generic-load threshold. That is the closest thing in the dataset to an answer, and it favours
   H_difficulty / load over H_pair.

5. **The novelty claim is unverified from this repository.** No `.bib`, five scholarly citations
   in the whole tree, and the v5 preregistration cites no external literature at all. *(The
   companion Evidence Audit closes this gap by going outside the repository — see its §6, and
   §3 below.)*

---

## 1. Evidence map — where the answer to the core question lives

The core question is v5 §2.2 item 3: *is B's reduction specific to companion A, or is it what a
companion of A's difficulty and A's form would produce whatever its identity?* Ranked by how much
each artifact moves that question.

| # | Artifact | Tier | What it carries |
|---:|---|---|---|
| 1 | `dci1/reports/dci1v4r4/final_results.json` | confirmatory | The only signed confirmatory estimates in the programme. 22 estimands × 2 replications, block bootstrap, simultaneous intervals. Also the register of the six quantities that are `NOT_IDENTIFIED`. |
| 2 | `dci1/evidence/dci1v5/*/GATE_2_FOCAL_CALIBRATION/` | live, unsigned | The only prospective test of v5's matching machinery. Grid-A and grid-B complete on both Gemmas (6,912 rows each); the candidate pass part-done. No stage record yet. |
| 3 | `user-notes/DCI1_preregistration_v5.md` | protocol | §7.5, §13.1–§13.15, §16, §29. The registered answer to the question, and where §12.6's stage-ordering defect is visible. |
| 4 | `dci1/reports/dci1v5/reference_design_development.md` | design | F1–F6, each measured on v4r4's own records. The diagnosis v5 is built on. |
| 5 | `dci1/evidence/dci1v5/*/REGIME_SCREEN/regime_record.json` | live | 326-rung difficulty table per model. Enough to project the reference pool before it is measured — see §4. |
| 6 | `dci1/src/dci1v5/run/{regime_run,gates_run,contracts}.py` | defect site | All three findings in §5 are in these three files. |
| 7 | `dci1/reports/dci1v5/v5_prereg_redteam.md` | design | R1–R24. R5 is the one no decision closes and the right place to look for what v5 still cannot do. |
| 8 | `dci1/reports/dci1v4r4/EXECUTION_REPORT.md` §8.3 | confirmatory | The L4 emitter defect and its registered reading. Load-bearing for how v4r4's disagreement is described. |
| 9 | `exploratory/CLAIM_EVIDENCE_MATRIX.md` | exploratory | I1–I11 with confidences. Different constraint vocabulary entirely — mechanism intuition, not evidence about A and B. |
| 10 | `user-notes/DCI_paper_review_packet_2026-08-20.md` §9.8 | gap | The related-work audit. States in the repository's own words that the novelty claim is unverified. |

Deliberately excluded as not load-bearing for this question: v2, v3 and v4r3 (different protocol,
terminal before confirmation, never comparable by their own rules); `src/dci/` and the eleven
exploratory families (different constraint vocabulary); the four v4 screens (superseded by v5's
library).

---

## 2. What the data support today

Everything below is from `final_results.json`: two replications, reduced 8-cell design, T = 384
blocks, M = 8 draws, 24,576 rows each, 10,000-resample block bootstrap, Šidák-corrected
simultaneous intervals within declared families. Both replications were analysed under one sealed
analysis-code hash (`dffb5a86…`), which is what makes them comparable.

### 2.1 v4r4 confirmatory estimates

**`gemma-3n-e4b-it`** — n\* = 4, m\* = 10, CL = `CL7:80` (*at least 80 words contain letter a*;
ι = 0.708 against a pre-screen ι_A = 0.667)

| Estimand | Configuration | Fam | est | SE | simultaneous 95% | ½-width | req | Reading |
|---|---|---|---:|---:|---|---:|---:|---|
| D(A←B) | outcome_first | F1 | +0.116 | 0.017 | [+0.077, +0.155] | 0.039 | 0.05 | **L1 emitted** |
| D(B←A) | outcome_first | F1 | +0.006 | 0.011 | [−0.018, +0.031] | 0.024 | 0.05 | spans 0 |
| Λ | outcome_first | F1 | −0.110 | 0.019 | [−0.155, −0.065] | 0.045 | 0.08 | L2 gated off |
| D(A←B) | outcome_second | F1 | −0.032 | 0.018 | [−0.073, +0.009] | 0.041 | 0.05 | spans 0 |
| D(B←A) | outcome_second | F1 | +0.283 | 0.015 | [+0.249, +0.318] | 0.035 | 0.05 | **L1 emitted** |
| Λ | outcome_second | F1 | +0.315 | 0.024 | [+0.259, +0.371] | 0.056 | 0.08 | L2 gated off |
| D(B←CL) | outcome_first | F9 | +0.316 | 0.017 | [+0.279, +0.354] | 0.037 | 0.05 | — |
| Δ_class | outcome_first | F9 | −0.310 | 0.019 | [−0.350, −0.271] | 0.040 | 0.06 | **CL > A** |
| D(B←CL) | outcome_second | F9 | +0.795 | 0.015 | [+0.762, +0.827] | 0.032 | 0.05 | — |
| Δ_class | outcome_second | F9 | −0.511 | 0.017 | [−0.550, −0.473] | 0.038 | 0.06 | **CL ≫ A** |

**`qwen3-4b`** — n\* = 2, m\* = 12, CL = `CX1:4` (*use the word "thus" exactly 4 times*;
ι = 0.695 against a pre-screen ι_A = 0.750)

| Estimand | Configuration | Fam | est | SE | simultaneous 95% | ½-width | req | Reading |
|---|---|---|---:|---:|---|---:|---:|---|
| D(A←B) | outcome_first | F1 | +0.392 | 0.018 | [+0.350, +0.434] | 0.042 | 0.05 | **L1 emitted** |
| D(B←A) | outcome_first | F1 | −0.123 | 0.013 | [−0.154, −0.092] | 0.031 | 0.05 | B *gains* |
| Λ | outcome_first | F1 | −0.515 | 0.023 | [−0.567, −0.462] | 0.052 | 0.08 | L2 gated off |
| D(A←B) | outcome_second | F1 | +0.329 | 0.020 | [+0.284, +0.375] | 0.046 | 0.05 | **L1 emitted** |
| D(B←A) | outcome_second | F1 | −0.012 | 0.014 | [−0.045, +0.021] | 0.033 | 0.05 | spans 0 |
| Λ | outcome_second | F1 | −0.341 | 0.025 | [−0.399, −0.283] | 0.058 | 0.08 | L2 gated off |
| D(B←CL) | outcome_first | F9 | −0.134 | 0.014 | [−0.165, −0.104] | 0.031 | 0.05 | — |
| Δ_class | outcome_first | F9 | +0.011 | 0.010 | [−0.011, +0.033] | 0.022 | 0.06 | **A ≈ CL** |
| D(B←CL) | outcome_second | F9 | −0.051 | 0.014 | [−0.081, −0.020] | 0.031 | 0.05 | — |
| Δ_class | outcome_second | F9 | +0.038 | 0.013 | [+0.009, +0.068] | 0.030 | 0.06 | **A ≈ CL** |

### 2.2 Primary claim — the only one licensed

**Composing two verifiable instructions costs one of them a measurable delivery loss, and which
one pays is not stable across models or across position.** L1 is emitted in every one of the four
registered configurations, but never for the same member: on `qwen3-4b` A pays in both
configurations (+0.392, +0.329); on `gemma-3n-e4b-it` A pays first and B pays second (+0.116,
then +0.283), and Λ reverses sign between them. Every precision precondition is met — the widest
realised half-width is 0.058 against a 0.08 requirement.

What that claim **is not**: D(c←g) is solo compliance minus composed compliance, so it contains
the generic cost of a second instruction. §1's whole point — that addition confounds identity
with count — applies to it in full. Every emitted L1 carries `COMPANION_CLASS_NOT_MATCHED`,
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and `EXCESS_NOT_IDENTIFIED` for exactly this reason.

### 2.3 Secondary claim — and it points away from the pairwise framing

The reduced design contains one companion contrast: Δ_class = D(B←A) − D(B←CL). The two
models' CL are **not the same kind of companion**, and that changes what each contrast means:

- On **`qwen3-4b`**, CL = `CX1:4` is `marker_thus`, `exact_count` — **A's structural twin**: same
  form, same class, a different marker word, matched on ι under v4r4's class rule. Δ_class
  is therefore effectively a *same-form* contrast, the very comparison v5's Δ_R is built
  to make. It comes out at **+0.011 [−0.011, +0.033] and +0.038 [+0.009, +0.068]** — half-widths
  0.022 and 0.030, well inside the 0.06 precondition.
- On **`gemma-3n-e4b-it`**, CL = `CL7:80` is a budget-class letter-count requirement — a genuine
  cross-class control. Δ_class is **−0.310 and −0.511**: the non-A companion damages B
  *far more* than A does.

**The honest reading.** Neither replication produces a signal of pair-specificity, and one
produces a signal against it. On `qwen3-4b` a same-form marker companion matched on ι damages B
indistinguishably from A, bounding the difference inside ±0.07 — below the source memo's 0.10
generic-load threshold. That is a preview of Δ_R at confirmatory precision, on one
model, from data already in hand.

It still cannot license L3c. It is one companion, not the registered three; v4r4's §5 registers
Δ_class as *a bound on how much class could matter*, never an estimate of anything;
the two models' CL are not comparable to each other; and `COMPANION_CLASS_NOT_MATCHED` attaches
to it. But it is the strongest companion-side evidence in the programme, and it favours the
load-and-capacity account.

### 2.4 What is not identified, and is not a null

Six registered quantities are `NOT_IDENTIFIED` study-wide: Δ_R, Δ_j,
δ_diff, Ξ, D(B←R_j), D(R_j←B). Both survivors ran §8.6's 8-cell
design; the one replication that obtained a full 47-cell design (`gemma-3n-e2b-it`) was ended at
Gate 4 before generating a confirmatory row. L2 is withheld everywhere (its gate is L1 in both
directions, which no configuration achieves), L3 is unreachable, and `gemma-3n-e4b-it`'s L4 field
is invalidated by the `emit_l4` set-comparison defect — the registered reading is *Configuration
dependence*.

### 2.5 On "statistical power"

There is no power calculation anywhere in this programme, and that is deliberate rather than an
omission. §16 registers **precision preconditions** — absolute half-width ceilings derived from
the smallest effect of interest — and §16.4 explicitly excludes every effect estimate from the
sizing, including v4r4's own realised D and Λ. So "adequately powered" is not a property the
design claims.

What it claims is that a projected Δ_R half-width of 0.043 resolves the 0.10 threshold
whenever the quantity is at least about 0.143 or at most about 0.057, and reports `INDETERMINATE`
otherwise. That is a weaker and more honest promise — and it means an inconclusive
Δ_R in the 0.057–0.143 band is a *registered outcome* of the full 1.14M-generation
study, not a failure of it.

| Member | precondition | φ = 0.27 | φ = 0.37 |
|---|---:|---:|---:|
| D | 0.05 | 0.0421 | 0.0452 |
| Δ_R, Δ_near (at F1's constant) | 0.05 | 0.0402 | 0.0429 |
| δ_diff | 0.05 | 0.0440 | 0.0471 |
| Λ | 0.08 | 0.0595 | 0.0639 |
| Δ_j | 0.06 | 0.0421 | 0.0452 |
| Ord_A, Ord_B | 0.05 | 0.0421 | 0.0452 |
| Ord_Λ | 0.08 | 0.0595 | 0.0639 |

---

## 3. Novelty — not assessable from this repository alone

I checked what the repository actually cites, because that is what "compare against the cited
prior work" can mean from inside it. The answer is close to nothing:

- **The v5 preregistration cites no external literature at all.** Zero URLs, zero DOIs, zero
  author–year references across 239 KB and 34 sections. The only `arxiv` string hits are
  incidental words.
- **Five scholarly citations exist in the whole tree.** Bean et al. 2025 (construct validity,
  arXiv:2511.04703) in v2/v3/v4r1 and the benchmark memo; Geirhos et al. 2020 (shortcut learning)
  in the shortcuts memo; IFEval and ComplexBench named only as verifier precedents, never as
  results; "Vasileva 2026" named twice, both in the review packet, never engaged with.
- **No `.bib` file exists.** Zero occurrences of FollowBench, InfoBench, CoDI, Multi-IF, CELLO,
  FollowEval, SysBench, RuleBench, CFBench, IFBench. There is no DCI-vs-IFEval comparison
  anywhere.

The repository already knows this — §9.8 of the review packet states it and files the novelty
claim under "requires external verification," and D7 of that packet leaves the literature search
unscoped. This confirms the finding rather than discovering it.

On the merits, from inside the repository: the **methodological** move — replacing the added
instruction with a difficulty-matched, form-matched reference rather than comparing against its
absence — is the part with a real claim to novelty, and the part that generalises. Any
constraint-composition benchmark that matches controls on pass rate inherits the F2 defect v5
measured (six rungs inside the caliper with raw solo above 0.90; one at solo 0.9740 / chance
0.9323 terminating a replication on its own solo cell). That is a transferable negative result
about benchmark construction and it does not depend on any DCI effect being real. The
**phenomenon** claim has no such standing yet: with Δ_R unidentified everywhere, what
has been measured is that composing two instructions degrades one of them.

> **Closed by the companion audit.** `AUDIT_2026-08-23_v4r4_evidence.md` §6 went outside the repository and retrieved
> six of seven mandatory prior-work items in full. Its finding sharpens this one considerably:
> generic compositional degradation **is already established** (Vasileva 2026, 15 models,
> k = 1…12; Anand & Chattaraj 2026, 3 models, k = 1…20), and order sensitivity is likewise
> already reported (Zeng et al. 2025, not cited anywhere in this repository). DCI's
> differentiation is the identification strategy at k = 2 — directional, solo-anchored,
> chance-corrected, both orders inside every block, with matched-difficulty replacement — and the
> demonstration that the naive version of it fails for measurable structural reasons. The honest
> priority statement is *"no prior work in this set identifies companion effects beyond
> difficulty"*, not *"first to show interference"*. See that document in full.

**Recommendation.** Fold the retrieved prior work into the preregistration's own framing before
Gate 5. If Δ_R resolves below 0.10 — which §4 argues is the modal outcome — the paper's
contribution becomes the methodology, and a methodology paper must engage Vasileva directly.

---

## 4. What v5 tests, and whether it can settle the question

v5's answer to "is the reduction specific to A" is a six-layer stack rather than one scalar:
Δ_R against three same-form, difficulty-matched core references; Δ_near
against operator-sharing controls; δ_diff against a difficulty relation fitted on nine
points with A excluded; Ξ for outcome specificity; Δ_broad as a class bound; and
Ord_A / Ord_B / Ord_Λ as direct order contrasts. Five arms, 56
cells, 384 blocks, M = 8, four models — 172,032 confirmatory generations per model, 1,144,896 in
total including calibration.

### 4.1 Live lifecycle state

| Replication | Stages with a signed PASS record | Currently |
|---|---|---|
| `gemma-3n-e2b-it` | `PROTOCOL_REGISTERED`, `QUALIFIED`, `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_1_MEASUREMENT` | Gate 2 candidate pass generating |
| `gemma-3n-e4b-it` | same five | Gate 2 candidate pass generating |
| `qwen3-4b` | `PROTOCOL_REGISTERED`, `QUALIFIED` | not started |
| `qwen3-4b-instruct-2507` | `PROTOCOL_REGISTERED`, `QUALIFIED` | not started |

Gate 1 passed on both Gemmas over the full 650-instrument population across 39 verifiers, basis
`deterministic_measurement_validated` — which discharges red-team item R23 ("the Tier-1 pool has
never been measured") for those two models.

### 4.2 What the live Gate 2 data already show

Recomputed from `scored.jsonl`, 768 observations per rung (192 pooled calibration topics ×
M_cal = 4). **Not yet a signed record** — Gate 2's selection functions have not run, so
read these as a projection of what the record will say.

| m | B solo · e2b | κ^B · e2b | B solo · e4b | κ^B · e4b | Band (0.60–0.95) | Floor κ^B ≤ 0.50 |
|---:|---:|---:|---:|---:|---|---|
| 7 | 0.461 | 0.000 | 0.517 | 0.000 | out | pass |
| 8 | 0.591 | 0.000 | 0.665 | 0.000 | e4b only | pass |
| 9 | 0.685 | 0.000 | 0.729 | 0.000 | both | pass |
| 10 | 0.805 | 0.000 | 0.867 | 0.005 | both · **nearest 0.80** | pass |
| 11 | 0.884 | 0.059 | 0.908 | 0.079 | both | pass |
| 12 | 0.939 | 0.197 | 0.930 | 0.212 | both | pass |
| 13 | 0.974 | 0.589 | 0.982 | 0.549 | out | **fail** |
| 14 | 0.984 | 0.840 | 0.988 | 0.811 | out | **fail** |

Three things this settles that were open the day before:

- **D17's threshold replicated prospectively.** The floor was derived from a development-model gap
  between κ^B = 0.398 at m = 12 and 0.586 at m = 13. On two models it was not fitted to,
  κ^B jumps 0.197 → 0.589 and 0.212 → 0.549 across the same boundary. A threshold chosen
  after seeing v4r4 landed on the right side of a real cliff. That is the strongest available
  answer to §29's "fitted to v4r4's failures" limitation.
- **§7.2's grid widening did its job.** v4r4's F6 was that m\* was the last measured rung on all
  four replications. Here m\* projects to 10 on both models, with 9 and 11 in band on either side
  — bracketed, no `OPERATING_POINT_AT_GRID_BOUNDARY`.
- **The vacuity failure that stopped v4r4 is gone.** Vacuous-pass rate is 0.000 at every rung on
  both models, against v4r4's ≥ 0.208 everywhere under the un-floored stem. §12.4 will not return
  `REGIME_NOT_FOUND`.

A's grid projects n\* = 6 on both models (solo 0.603 and 0.728 against a [0.50, 0.85] band aiming
at 0.70), bracketed on both, with load-zero chance ≈ 0.000 at n ≥ 2 — so the core pool really is
chance-free, as §7.5 argued it would be.

### 4.3 Can it resolve the core question? — a qualified yes, with one live risk

The machinery is sound where it has been exercised. The risk is **support**, and it is measurable
now rather than at Gate 3. Taking each Tier-1/Tier-2 family's pre-screen ι and asking how many
have at least one rung inside the 0.10 caliper of the projected ι_A:

| Model | ι_A at n\* | Tier-1/2 families with an in-caliper rung | §26 requires | Spare | Families with none |
|---|---:|---:|---:|---:|---|
| `gemma-3n-e2b-it` | 0.603 | 6 | 5 | +1 | MK3 *though*, MK6 *namely*, MK7 *instead*, MK8 *overall*, XC2 |
| `gemma-3n-e4b-it` | 0.728 | 5 | 5 | **0** | MK3, MK7, MK8, XC1, XC2, XC3 |

That is v4r4's F5 recurring — support at the minimum — and it is worse than it looks, because the
pre-screen is exactly the point-estimate instrument F1 measured as unreliable: median |Δι| of
0.071 between pre-screen and calibration, with 35.7% of candidates moving further than the whole
caliper. On `gemma-3n-e4b-it`, five families with no spare, screened by an instrument that
historically loses half of them, is a coin-flip on whether the core arm is admitted at all.

v5 has a designed answer to this and it is **§12.6's candidate expansion**: while C1–C6 fail,
admit reserve rungs from the frozen ladders (every MK family has rungs 9–12 in reserve,
unmeasured), up to four per family per round, two rounds. C4 was written specifically as "three
groups plus three spare, against v4r4's one." The expansion is implemented, unit-tested, and —
per finding F1 below — **has never been called**.

*(`AUDIT_2026-08-23_v5_design_execution.md` reaches the same conclusion from a different direction, counting
marker absence rates in the in-flight calibration rows: `instead` absent from 90.6% of answers,
`namely` 64.9%, `though` 48.1%, `overall` 38.0% at q = 3 on e2b — three or four of the eight
Tier-1 markers ignored rather than failed. Two independent routes to "the Tier-1 pool is smaller
than registered.")*

### 4.4 Limitations that survive perfect execution

These are correctly registered, not defects:

- **R5, accepted and permanent.** κ^B is measured under B, so the reference set is a
  function of how each model writes under its own B at its own m\*. No cross-model Δ_R
  comparison is licensed, and no rule closes it.
- **The length channel is not identified at any block count.** Tier-1 controls are chosen to move
  length as little as possible, which is precisely why they cannot test whether A's effect
  operates *through* length.
- **The measurement basis is `deterministic_measurement_validated`, never `human_validated`.**
  §10.5's scope sentence attaches to every claim permanently.
- **D18 means dropping the near-form arm changes the study** rather than making it cheaper — the
  strong L3c becomes unreachable.
- **The question v5 answers is narrower than the original, and v5 says so.** §5 and §29:
  Δ_R asks whether *however* is special among discourse markers at matched difficulty,
  not whether A is special among companions in general.

---

## 5. Live findings — three defects, currently executing

All three are the repository's own signature failure mode — a field with a producer and no real
consumer — and all three were invisible for the reason §4v of `RESEARCH_STATE.md` already
identified: the synthetic harness walks the same runners, so a check never reached in production
is never reached in the harness either.

### F1 — §12.6's candidate expansion has never run, on either live replication · *scientific*

`stages/regime.py` implements `expansion_round()` and `run_expansion()`. `run/regime_run.py` —
the production runner, whose own docstring says it "applies §12.6's expansion to its stopping
rule" — never calls either. There is no test on `run_expansion` at all; `expansion_round` is
unit-tested against a hand-built table with ι_A injected.

The proximate cause is a **stage-ordering problem in the protocol**, not only in the code. §12.6
says "write ι_A for the *pre-screen* instructed compliance of A," but `_screen_rungs()`
iterates `FAMILIES`, which contains the 37 candidate families and neither A nor B. So A is
structurally never measured at the regime screen, `iota_a` is always `None`, and the runner
substitutes `{"holds": False, "reason": "iota_A is not measured on the pre-screen"}` and records
`outcome: "PASS"` anyway. §18 stage 4's registered exit condition — "§12.6's expansion run to its
stopping rule and the candidate vocabulary frozen" — is half met: the vocabulary froze, the
expansion did not run.

- **Evidence** — `coverage: {"holds": false, …}` on both signed `regime_record.json` files;
  `grep run_expansion dci1/src/dci1v5/run/` returns nothing.
- **Consequence** — the reserve ladders are unmeasured and the support projection in §4.3 stands
  as-is: five families, zero spare, on `gemma-3n-e4b-it`. This is the exact defect C4 was written
  to prevent. `REFERENCE_SUPPORT_NOT_IDENTIFIED` at design time and `CANDIDATE_RESERVE_EXHAUSTED`
  are unreachable.
- **Compounding** — `coverage` is declared in `contracts.py` as read by `GATE_3C` and `GATE_5`.
  Neither `gate3c_payload` nor `freeze_run` references it, so the failed criterion never surfaces
  downstream either.
- **Window** — open. The vocabulary froze at the regime screen, so re-running it means re-running
  Gate 0 → Gate 2 for both Gemmas. Still pre-composition, so §32's pre-data amendment route
  applies — that closes at Gate 2.5 for §13 components and at Gate 4 generally.

### F2 — Gate 2 is generating 2.9× the registered calibration budget · *budget + selection set*

§12.7 registers that calibration measures "all 88 Tier-1 and Tier-2 rungs … **plus at most 24
Tier-3 rungs**," ordered by ascending pre-screen |ι − ι_A| when the budget binds.
`regime_stage.calibration_priority()` computes that plan correctly and both regime records carry
it: `n_measured: 112`, with 214 Tier-3 rungs listed under `tier3_dropped_for_budget`.

`gates_run.gate2_payload` does not read it. It takes `regime_record["carried_set"]` — all 326
rungs — and generates one solo cell for each over the 192 pooled topics at M_cal = 4.
`contracts.py` declares `calibration_priority` as consumed by `GATE_3A_REFERENCE_CALIBRATION`;
`gate3a_payload` reads `gate2_record["calibration_rows"]` and never touches it. **The field has
no consumer anywhere.**

- **Arithmetic** — registered: 112 × 96 × 4 × 2 splits = **86,016** per model. Executing:
  326 × 192 × 4 = **250,368** per model, confirmed by `plan.json → expected_rows: 250368`. Excess
  **+164,352 per model, +657,408 over four**. The registered 1,144,896 total becomes ≈ 1,802,304.
- **Not merely cost** — §13.10 selects CL as the qualifying Tier-3 budget severity minimising
  |ι_CL − ι_A|. Over 238 measured Tier-3 rungs instead of 24, that argmin
  ranges over a ~10× larger set. The direction is favourable — a better-matched CL, and C7 more
  likely to hold — but it is a change in what a registered selection rule ranges over, which is
  scientifically consequential under this repository's own definition.
- **Why the contract missed it** — `tools/v5_producer_consumer.py` enforces one direction only,
  stated in its own header: *"no consumer field without a producer."* A declared consumer that
  never reads the field passes as `PRODUCED / exercised: yes`. Both F1's `coverage` and F2's
  `calibration_priority` are green in that report.
- **Interaction with F1** — the two mask each other. `calibration_priority` is called with
  `iota_a_prescreen = iota_a if iota_a is not None else 0.5` — an unregistered literal, directly
  beneath a comment claiming the budget is "a function of measured quantities rather than of a
  caller's argument." That 0.5 is currently inert only because the cap never binds. Fix F2 alone
  and an unregistered constant starts selecting Tier-3 rungs.
- **Window** — closing. About 97% of the excess was still unspent at audit time: the two Qwen
  replications had not started, and both Gemma candidate passes were part-done.

### F3 — `RESEARCH_STATE.md` describes a study that has not started · *documentation*

§4b's v5 row reads "ADOPTED AND REGISTERED 2026-08-23; **no stage record, no instrument measured,
no generation**," and §4u repeats "Stage 1 has run. Nothing after it has." At the time of writing,
five stage records exist per Gemma, Gate 1 has certified 650 instruments across 39 verifiers on
both, and 238,912 generations sit under `dci1/evidence/dci1v5/`. The file was last written at
12:07; Gate 1 signed at 12:20.

There is also a supersession the register does not carry:
`dci1/evidence/dci1v5/*/superseded/70608e5d…/` exists, so the A1 replacement manifest has itself
been superseded (by A2, commit `cd4b1b1`) — and §4v still presents `70608e5d…` as the current
registration. The amendment register's A2 entry is present; the state file has not caught up.

§8 of that file is explicit that a statement which cannot be traced to a linked artifact should be
deleted rather than maintained. This is the inverse — an artifact that exists and is not described
— and it is the one an outside reader would rely on to decide whether v5 has data.

> **Additional defects found only by the companion audit** (`AUDIT_2026-08-23_v5_design_execution.md` §4), listed here so this document's F-list
> is not read as complete: no core-without-spectrum path (`stages/selection.py::select_all` calls
> `admit_core_references` with `require_spectrum=True` and never falls back, against §8.1 and
> §13.12); §7.2's focal extension {15, 16} is never measured (`gates_run.py` reads `FOCAL_GRID`
> only); §12.4's adequacy statuses are raised nowhere; the environment digest is empty on every
> live record; and Gate 2's ι_A/ι_B were computed with chance taken at n = 1
> and m = 7 rather than at n\*/m\* in v4r4. 

---

## 6. Recommended sequence

1. **Decide on F2 while the excess is unspent.** Either amend §12.7 to register measuring the
   complete carried set on both splits — defensible, consistent with D16's reasoning, and it
   improves CL matching — or stop the candidate pass and wire `calibration_priority` into
   `gate2_payload`. What is not defensible is finishing under an unrecorded deviation from a
   budget that was formally amended twice on the same morning.
2. **Resolve F1 before Gate 2.5.** The support projection says the core arm is at genuine risk on
   `gemma-3n-e4b-it`, and the mechanism designed to fix it is not on the execution path. Either
   measure A's grid at the regime screen so ι_A exists there, or amend §12.6 to evaluate
   coverage at Gate 2 where ι_A is known. The second is cheaper and probably more
   correct, since the pre-screen ι_A was always going to be the unreliable instrument F1
   measured.
3. **Add the reverse contract check.** A consumer declared in `contracts.py` that no payload
   function references should fail a test. That single check catches F1's `coverage`, F2's
   `calibration_priority`, and the next one.
4. **Update `RESEARCH_STATE.md`** and add a `CHANGES_SCIENTIFIC.md` entry for whatever F2 is
   resolved as — it changes what a registered selection rule ranges over.
5. **Fold the retrieved prior work into the preregistration's framing** before the reference pool
   freezes, for the reason in §3.

---

## 7. Scope of this audit

**Checked.** `RESEARCH_STATE.md` §1–§8; v4r4 `final_results.json` in full; the v5 preregistration
§2–§3, §5, §7, §12, §13, §16, §26, §29, §34; `v5_prereg_redteam.md`; `amendment_register.md`;
`researcher_decisions.json`; the v5 source under `run/`, `stages/`, `analysis/`, `protocol/`;
`contracts.py` against the payload functions; the live v5 evidence tree including transition logs,
regime records, Gate 1 records and Gate 2 raw rows.

**Recomputed independently.** A's and B's solo, chance and load-zero curves from raw
`scored.jsonl`; the reference-support projection from `regime_record.json`; the Gate 2 budget
arithmetic; `dci1v5.design.budget.registered_budget()`; the class-companion identities and ι
values from `freeze_<model>.json`.

**Not checked, and flagged as such.** Record signatures and durable mirrors were not verified.
v4r4's estimates were not re-derived from raw `scored.jsonl` — the repository states it did so to
four decimals, and the numbers in §2 are read from `final_results.json`. The 96 Calibration-B
questions were not audited. `tests_v4r4` was not run. `dci1/tests_v5` passes 383/383 on this tree.

**Provenance caveat.** `dci1/evidence/` is gitignored and does not survive a clone, so every
number in §4 is reproducible only on this machine. §2's numbers come from
`dci1/reports/dci1v4r4/final_results.json`, which is committed. Projected n\*, m\* and reference
support are projections — Gate 2's selection functions have not run and no Gate 2 stage record
exists.
