# DCI-1 v5 — reference design: the development analysis

> **DEVELOPMENT ONLY.** Everything in this document is retrospective analysis
> of the completed DCI-1 v4r4 study, run to choose v5's matching rule and its
> thresholds. It is **design fitting**. A rule chosen because it separates
> v4r4's known failures from v4r4's known passes has been fitted to those
> failures, and **retrospective performance on v4r4 is not prospective
> validation.** The prospective test is v5 itself.
>
> Nothing here licenses a scientific claim. No number here is a v5
> observation; none exists. No v4r4 record was modified, re-run, or
> re-interpreted.

Producer: [`dci1/tools/v5_reference_design_development.py`](../../tools/v5_reference_design_development.py).
Machine-readable outputs: [`development/`](development/) — `d1` … `d6`.
The rule these analyses select is frozen in
[`reference_design_spec.json`](reference_design_spec.json) and registered in
[`user-notes/DCI1_preregistration_v5.md`](../../../user-notes/DCI1_preregistration_v5.md).

---

## 0. What v4r4 left to explain

v4r4 completed. Two of four replications reached confirmation; both ran §8.6's
8-cell reduced design; six registered quantities — `Δ_R`, `Δ_j`,
`δ_difficulty`, `Ξ`, `D(B←R_j)`, `D(R_j←B)` — are `NOT_IDENTIFIED` study-wide.
The one replication that obtained a full matched-reference and spectrum design,
`gemma-3n-e2b-it`, was ended at Gate 4 before generating a confirmatory row.

So the study answered the compositional questions and did not reach the
companion-specificity question. Five separate failures produced that, and this
document measures each one rather than describing it.

| | What failed | Where it is measured |
|---|---|---|
| **F1** | a cheap point-estimate pre-screen used as a hard selector | §1 |
| **F2** | a single scalar (ι) used as the admission coordinate | §2 |
| **F3** | "production class" too coarse to say what a control shares with A | §3 |
| **F4** | solo-matched controls made trivial by the outcome constraint | §4 |
| **F5** | support calibrated to the minimum, with no allowance for attrition | §5 |
| **F6** | an operating-point grid that ends where the operating point is | §6 |

§7 states the rule these findings select, §8 its retrospective cost, and §9
what the analysis cannot establish.

---

## 1. F1 — the pre-screen could not select, and the collapse is quantified

**What v4r4 did.** §12.2's dense ladder screen measures the full 94-rung
reference ladder on **24 pre-screen topics at one draw**. §12.6's coverage
criterion C1–C7 is evaluated on that table. §12.3 shortlists from it. §13.4
then re-measures a ≤29-rung shortlist on **96 disjoint solo-calibration topics
at four draws** and applies a **0.10** caliper on ι.

**What happened.** All four replications passed all seven coverage conditions
at pre-screen. Then:

| Model | Straddling families at pre-screen (needs ≥ 4) | after calibration (needs ≥ 3) | attrition |
|---|---:|---:|---:|
| `gemma-3n-e2b-it` | 7 | 3 | −57% |
| `gemma-3n-e4b-it` | 5 | **0** | −100% |
| `qwen3-4b` | 4 | 2 | −50% |
| `qwen3-4b-instruct-2507` | 4 | **0** | −100% |

**Why, measured.** The two stages' ι estimates disagree by
(`d1_candidate_landscape.json`, `_pooled_iota_drift`):

| | median | p75 | p90 | max |
|---|---:|---:|---:|---:|
| \|ι(pre-screen) − ι(calibration)\| | **0.0709** | 0.1315 | 0.2262 | 1.0556 |

**35.7% of measured candidates move further between the two stages than the
whole width of the caliper they then have to clear.** ι_A itself moves by
0.018 to 0.048, so both ends of the distance are noisy. A screen whose
measurement error is the size of the decision boundary is not a screen; it is a
lottery with a coverage certificate attached.

**How much of that is the split and how much is the sample size.** The
pre-screen-to-calibration comparison confounds them, so §14 of the
preregistration is sized on a clean measurement instead: the 96 calibration
topics were split in half by hashed topic identity and ι recomputed on each
half at 48 topics × 4 draws (`d3_split_half_stability.json`).

| | median | p75 | p90 | max |
|---|---:|---:|---:|---:|
| \|ι(half A) − ι(half B)\| pooled | 0.0644 | 0.1203 | 0.2008 | 0.4521 |
| \|p_solo(half A) − p_solo(half B)\| pooled | 0.0434 | 0.0753 | 0.1029 | 0.1990 |

From the median of the split difference, SD(difference at 48 topics) = 0.0954,
so

| sample | SE(ι) | v4r4's 0.10 caliper, in SE |
|---|---:|---:|
| 48 topics × 4 | 0.0675 | 1.48 |
| **96 topics × 4** (v4r4's calibration) | **0.0477** | **2.10** |
| 192 topics × 4 | 0.0337 | 2.96 |

**The finding.** v4r4's caliper is about two standard errors wide. Selecting the
nearest candidate inside a two-SE window is selection substantially on noise,
and the winner's curse it produces is exactly the pre-screen-to-calibration
collapse in the first table. The repair is **not** a tighter caliper — that
moves in the wrong direction. It is more calibration data, an independent split
to detect instability, and a pre-screen demoted to high recall.

---

## 2. F2 — ι alone is neither sufficient nor stable

### 2.1 It is not sufficient: the qwen-instruct termination

`qwen3-4b-instruct-2507` terminated at Gate 4 on **one** failing cell, and that
cell is `solo:CL` — a solo cell, with no composition in it.

| stage | `CL8:3` — *"At least 3 words must end with y."* |
|---|---|
| Gate-2 calibration (96 × 4) | solo **0.9740**, chance **0.9323**, ι 0.6154, vacuity 0.0026 |
| Gate-3 admission (§13.7) | **ADMITTED**: \|ι − ι_A\| = 0.0191, the smallest of any eligible production rung |
| Gate-4 headroom (24 × 4) | solo **0.9896** → above the 0.95 ceiling → **TERMINAL** |

§13.7 admits on ι. §13.10 checks the raw rate. **Nothing between them checks
the raw rate.** `CHANCE_DEGENERACY_MAX` is 0.99, so a chance rate of 0.9323 is
legal; `SPECTRUM_ELIGIBILITY_BAND` is (0.10, 0.95) on ι, not on compliance. The
Gate-4 failure was fully determined one gate earlier and merely observed at
Gate 4.

It is not an isolated case. Across the four replications, **six rungs sat
inside the 0.10 ι caliper with raw solo compliance above 0.90**
(`d1_candidate_landscape.json`):

| model | rung | \|ι − ι_A\| | p_solo | κ |
|---|---|---:|---:|---:|
| `gemma-3n-e2b-it` | `RF3:8` | 0.0818 | 0.9453 | 0.8411 |
| `gemma-3n-e4b-it` | `RF1:6` | 0.0852 | 0.9714 | 0.8698 |
| `qwen3-4b` | `RF2:6` | **0.0060** | 0.9453 | 0.8203 |
| `qwen3-4b` | `RF11:26` | 0.0832 | 0.9036 | 0.5521 |
| `qwen3-4b` | `CR5:10` | 0.0955 | 0.9245 | 0.6276 |
| `qwen3-4b-instruct-2507` | `CL8:3` | 0.0191 | **0.9740** | **0.9323** |

`RF2:6` on `qwen3-4b` is the *closest* reference candidate on that model by ι
and is satisfied 82% of the time unasked.

### 2.2 It is not stable: the variance amplification is measurable

ι = (p_solo − κ)/(1 − κ) carries a 1/(1 − κ) amplification that raw compliance
does not. It is visible in the data (`d3`, `by_chance_band`; 48-topic halves):

| chance band | n | median \|Δι\| | p90 | 1/(1−κ) at the band midpoint |
|---|---:|---:|---:|---:|
| κ < 0.05 (chance-free) | 42 | **0.0439** | 0.1172 | 1.03 |
| 0.05 ≤ κ < 0.25 | 21 | 0.0505 | 0.1012 | 1.18 |
| 0.25 ≤ κ < 0.75 | 32 | 0.1095 | 0.2144 | 2.0 |
| κ ≥ 0.75 | 16 | **0.1954** | 0.4000 | ≥ 4.0 |

And by predicate form:

| form | n | median \|Δι\| | p90 |
|---|---:|---:|---:|
| **exact count** | 16 | **0.0381** | 0.0915 |
| count lower bound | 12 | 0.0458 | 0.0946 |
| count budget | 69 | 0.0764 | 0.2144 |
| rate budget | 14 | 0.0915 | 0.3750 |

**The exact-count form is the most stable predicate form in the entire v4r4
library**, by a factor of two against count budgets and 2.4 against rate
budgets — because it is chance-free, and for a chance-free constraint ι *is*
raw solo compliance and inherits none of the amplification.

### 2.3 The rules this selects

- a **raw solo headroom** gate, on the Wilson interval and not on the point;
- a **chance ceiling** far below 0.99;
- an **instruction-lift floor**, because `D(R←B) ≤ p_solo(R) − κ(R)`: a
  reference cannot lose more compliance under composition than stating it ever
  bought, so a reference with lift below 0.20 has its reciprocal loss bounded
  below two SESOI by construction rather than by the model;
- ι **demoted** from the admission coordinate to the difficulty coordinate,
  reached only after the validity gates pass.

**Thresholds and how they were chosen.**

| threshold | value | chosen from |
|---|---|---|
| raw solo headroom, on the 95% Wilson interval | ⊂ [0.10, 0.90] | Gate 4's (0.05, 0.95) contracted by 0.05 a side, applied to the interval so an imprecise candidate cannot sit on the boundary |
| instruction lift `H = p_solo − κ` | ≥ 0.20 | two SESOI; below it the reciprocal estimand is bounded by the design rather than by the model |
| chance ceiling, point | ≤ 0.75 | where measured split-half instability reaches ≈3× the chance-free value while the amplification factor is still single digit (§2.2) |
| chance ceiling, Wilson upper | ≤ 0.85 | the same margin logic as the headroom gate |

Candidate values considered and rejected: a chance ceiling of **0.50** — it
costs a further family on `gemma-3n-e2b-it` and `gemma-3n-e4b-it`
(`d5`, third stack row) for no measured stability gain, since the 0.25–0.75
band's instability (0.1095) is much closer to the chance-free band's (0.0439)
than to the ≥0.75 band's (0.1954). A **point-estimate** headroom rule rather
than an interval rule — rejected because it reproduces exactly the defect §1
measures, deciding on a coordinate whose error is the size of the margin.

---

## 3. F3 — "production class" says almost nothing about what a control shares with A

v4r4's class arm admitted **one production-class companion**, chosen as the
eligible production rung minimising \|ι − ι_A\|. What it actually admitted:

| model | CL | constraint | what it is |
|---|---|---|---|
| `gemma-3n-e2b-it` | `CX2:1` | *exactly 1 semicolon* | exact count, punctuation |
| `gemma-3n-e4b-it` | `CL7:80` | *at least 80 words must contain letter a* | count lower bound, **forces a long answer** |
| `qwen3-4b` | `CX1:4` | *use the word thus exactly 4 times* | **A's own form, A's own ladder, one word changed** |
| `qwen3-4b-instruct-2507` | `CL8:3` | *at least 3 words must end with y* | count lower bound, near-vacuous |

`CX1:4` and `CL7:80` are in the same declared class and are not the same kind
of object. The registered estimands say so:

| | `qwen3-4b` (`CX1:4`) | `gemma-3n-e4b-it` (`CL7:80`) |
|---|---|---|
| `Δ_class`, outcome_first | **+0.0114** [−0.011, +0.033] | **−0.3102** [−0.350, −0.271] |
| `Δ_class`, outcome_second | +0.0384 [+0.009, +0.068] | **−0.5114** [−0.550, −0.473] |

On one model the class companion is indistinguishable from A in its effect on
B; on the other it damages B by half a compliance point more than A does. Both
are "one production-class companion matched on ι". ι is blind to form, and
`Δ_class` is not one quantity measured twice.

Median words in the solo cell make the mechanism visible (`d1`,
`median_words`), against an unconstrained median of 107 on the Gemmas and 83 on
`qwen3-4b`:

| | `CL7` | `CX1` | budget families (`RF9`, `RF11`) |
|---|---:|---:|---:|
| `gemma-3n-e2b-it` | 119–127 | 104–125 | 80–82 |
| `gemma-3n-e4b-it` | 127 | 125–130 | 78–85 |
| `qwen3-4b` | 88–90 | 66–68 | 56–62 |

A count lower bound lengthens; a budget shortens; the exact-count marker family
tracks **A's own length behaviour** — A's solo median is 123 words on
`gemma-3n-e4b-it` and 77 on `qwen3-4b`, against `CX1` at 125–130 and 66–68.

**The rule this selects.** Replace one declared class with a structural
taxonomy carrying operator, statistic type, count-or-rate, denominator,
lexical-or-structural, length dependence, length direction, production burden
and natural frequency; and define **tiers** relative to A: Tier 1 same-form
(exact count of a marker word), Tier 2 near-form (exact count, other
statistic), Tier 3 broad. The core reference pool takes Tier 1 and Tier 2 only.

---

## 4. F4 — the outcome constraint made solo-matched controls trivial, and the shift is measurable before composing

### 4.1 The e2b termination

All five of `gemma-3n-e2b-it`'s Gate-4 failures involve `RF11` — *"at most q
words may begin with a vowel"* — paired with **B**, *"every word at most 10
letters"*:

| cell | slot | rate | band |
|---|---|---:|---|
| `pair:B+R3` | `B:10` | 0.9583 | **FAIL** |
| `pair:B+R3` | `RF11:26` | 0.9688 | **FAIL** |
| `pair:R3+B` | `RF11:26` | 0.9583 | **FAIL** |
| `pair:B+R3+` | `RF11:32` | 1.0000 | **FAIL** |
| `pair:R3++B` | `RF11:32` | 1.0000 | **FAIL** |

Composing with B cuts the vowel-initial count from ≈24 to ≈17 because B forces
shorter words and shorter answers; `RF11`'s budget of 26 becomes trivially
satisfiable. Pairing the same `RF11` rung with `RF9:10` or `CR5:2` barely moves
it. **The ceiling is produced by B specifically — the outcome constraint of the
whole study.**

### 4.2 The quantity that sees it coming, without composing

Every generation is scored on every registered instance (§9.1), so **`R`'s
verifier can be run on responses written under `B` alone**. Define

> **κ(R | B)** = P(R's verifier passes │ B alone stated at m\*, R absent).

`R` is never stated in those prompts. This is a chance verdict under a
different load-one treatment, it reads no composed cell and no contrast between
composed cells, and it costs **zero extra generations**.

Recomputed with the registered v4r4 verifiers on the stored Gate-2 B-solo
responses (`d2_kappa_under_b.json`), against the unconstrained baseline on the
same topics:

| model | median words, unconstrained → B solo | selected rows: κ → κ(R\|B) |
|---|---|---|
| `gemma-3n-e2b-it` | 107 → 84 | `RF11:26` 0.148 → **0.833**; `RF11:32` 0.445 → **0.964**; `RF11:21` 0.008 → 0.615; `RF9:10` 0.240 → 0.401; `CR5:2` 0.003 → 0.034 |
| `gemma-3n-e4b-it` | 107 → 82 | `RF11:26` 0.109 → **0.914**; `RF1:7` 0.925 → **0.958**; `CR5:8` 0.432 → 0.656 |
| `qwen3-4b` | 83 → 56 | `RF11:21` 0.162 → **0.904**; `RF3:6` 0.977 → **0.997**; `RF2:6` 0.820 → **0.971**; `CL7:30` 0.849 → **0.122** |
| `qwen3-4b-instruct-2507` | 81 → 52 | `RF11:26` 0.578 → **1.000**; `RF7:24` 0.023 → **0.857**; `CL8:3` 0.932 → 0.505 |

Two directions appear, and both matter. `RF11` and the other word-shaped count
budgets are made **trivial**; `CL7:30`, a count lower bound, is made much
**harder** (0.849 → 0.122). And the one exact-count marker family in the
library, `CX1`, has κ = 0.0000 and κ(R\|B) = 0.0000 on **every** model — B does
not move it at all.

### 4.3 The projection, and what it predicted

The natural extension of ι is to evaluate it at the counterfactual baseline
rather than at the unconstrained one:

> **p̂(R │ B+R) = κ(R│B) + ι_R · (1 − κ(R│B))**

Both inputs are pre-composition. Against `gemma-3n-e2b-it`'s **observed**
Gate-4 composed rates — 20 rate checks, the only full design that reached
Gate 4 (`d4_interaction_projection.json`):

| cell | R | κ(R\|B) | ι | **p̂** | observed | error | Gate 4 |
|---|---|---:|---:|---:|---:|---:|---|
| `pair:B+R3+` | `RF11:32` | 0.9635 | 0.854 | **0.9947** | 1.0000 | −0.005 | **FAIL** |
| `pair:R3++B` | `RF11:32` | 0.9635 | 0.854 | **0.9947** | 1.0000 | −0.005 | **FAIL** |
| `pair:B+R3` | `RF11:26` | 0.8333 | 0.633 | **0.9388** | 0.9688 | −0.030 | **FAIL** |
| `pair:R3+B` | `RF11:26` | 0.8333 | 0.633 | **0.9388** | 0.9583 | −0.020 | **FAIL** |
| `pair:B+R1+` | `RF9:13` | 0.6745 | 0.643 | 0.8836 | 0.8125 | +0.071 | pass |
| `pair:B+R3-` | `RF11:21` | 0.6146 | 0.336 | 0.7441 | 0.8229 | −0.079 | pass |
| `pair:B+R1` | `RF9:10` | 0.4010 | 0.534 | 0.7210 | 0.7396 | −0.019 | pass |
| … 13 further checks, all projected ≤ 0.72 and all passing | | | | | | | |

Absolute error: median **0.067**, mean 0.084, max 0.313.

| projected ceiling | failures caught | failures missed | false alarms |
|---|---:|---:|---:|
| 0.85 | 4 / 4 | 0 | 2 of 16 |
| **0.90** | **4 / 4** | **0** | **0 of 16** |
| 0.92 | 4 / 4 | 0 | 0 of 16 |
| 0.95 | 2 / 4 | 2 | 0 of 16 |

**Perfect separation at 0.90, from pre-composition quantities alone.**

**And the honest caveat.** Twenty rate checks on one model. 0.90 sits inside the
observed gap between the highest passing projection (0.8836) and the lowest
failing one (0.9388), and a threshold chosen from an observed gap on twenty
points is fitted to those twenty points. v5 therefore **derives** the value
instead: Gate 4's band ceiling is 0.95, the projection is a point prediction
with error, and the registered error allowance is 0.05 — the same number as
§16.2's precision precondition for `D`, and close to the realised median
absolute error of 0.067. The rule is `p̂ + 0.05 ≤ 0.95`. That the derivation and
the gap agree is recorded as a coincidence, not used as evidence.

One property is worth stating because it makes the gate robust where it
matters: as κ(R│B) → 1 the projection → 1 whatever ι is, so the projection is
**least** sensitive to the transfer assumption exactly where it binds.

### 4.4 Why this is not outcome-based selection

`Δ_R = D(B←A) − mean_j D(B←R_j)`. The B-solo baseline cancels, so `Δ_R` is a
contrast among **composed** cells and reads `X_B` in the `B+R_j` cells.
`κ(R│B)` reads `X_R` in the **B-solo** cell. Different verdict, different rows,
and `κ(R│B)` observes B's compliance nowhere.

The residual-bias direction is checkable rather than asserted: a reference B
makes trivial would show a **small** `D(B←R_j)`, which would make
`mean_j D(B←R_j)` small and `Δ_R` **large**. Excluding such references is
therefore conservative with respect to the pairwise hypothesis, not favourable
to it.

### 4.5 The rules this selects

- **`V_interaction`**: `0.10 ≤ p̂(R│B+R) ≤ 0.90`.
- **displacement**: `|Σ(R│B)| = |κ(R│B) − κ(R)| ≤ 0.25`, a signed two-sided
  measure that catches the floor direction the projection does not.
- **a realistic joint witness**: v4r4's §7.5 witness obligation is formal, and
  a formal witness certifies that a pair is not contradictory rather than that
  it is satisfiable by a response of the length the task asks for. `CL7`'s
  frozen reserve runs to 140, and *at least 130 words must contain the letter
  a* cannot be met by any answer of at most 120 words. v5 requires the witness
  to lie inside §8.5's stem band.

  **This check is narrow and it is not the main defence.** An earlier draft of
  this document claimed `CL7:80` was unreachable under B; **the signed records
  contradict that** — on `gemma-3n-e4b-it` its composed compliance was 0.609
  and 0.662. `CL7:80`'s problem is comparability, not reachability, and the
  structural tier rather than the witness rule is what excludes it from a core
  reference slot.

**Generality, and the rule this document refuses to write.** Not *"exclude
RF11"*. The rule names a property of the pair (statistic, focal constraint) and
measures it: exclude a family whose verifier statistic has strong monotonic
dependence on a response feature the focal companion predictably shifts. `RF11`
is excluded on `gemma-3n-e2b-it` because its vowel-initial count falls with
answer length and B shortens answers, and the same rule excludes no family by
name anywhere.

---

## 5. F5 — the support was calibrated to the minimum, and the library was the wrong library

### 5.1 What v4r4 admitted

| model | families admitted | straddling | core refs | design | why |
|---|---|---:|---:|---|---|
| `gemma-3n-e2b-it` | `CR5:2`, `RF9:10`, `RF11:26`, `RF6:1` | 3 | **3** | **full** | `RF6` admitted but cannot straddle |
| `qwen3-4b` | `RF11:21`, `CR5:8` | 2 | 2 | reduced | both straddle and both supply a valid triple; §13.4 requires **three** |
| `gemma-3n-e4b-it` | `RF9:13` | 0 | 0 | reduced | no eligible rung strictly above ι_A |
| `qwen3-4b-instruct-2507` | `RF7:24` | 0 | 0 | reduced | same shape |

Rejection reasons pooled over the four models: ι distance above the caliper
**66**; pre-screen distance above its caliper 47; Newcombe interval missing the
region 42; ι outside the eligibility band 7; solo vacuity 2. **The wording
caliper, the witnesses and parse independence rejected nothing.** The binding
constraint was entirely distance-after-re-measurement, which is §1.

### 5.2 The attrition of the proposed stack, measured

`d5_gate_attrition.json` applies each proposed gate to v4r4's own library and
its own measurements. Families qualifying, by role:

**Reference-role families (budget class — v4r4's reference pool):**

| stack | e2b | e4b | qwen3-4b | qwen-instruct |
|---|---:|---:|---:|---:|
| v4r4 rule (ι caliper + vacuity) | 6 | 3 | 3 | 1 |
| + raw solo headroom CI ⊂ [0.10, 0.90] | 5 | 2 | 2 | 1 |
| + chance ≤ 0.75 and lift ≥ 0.20 | 5 | 2 | 2 | 1 |
| **+ interaction gates (full v5 stack)** | **3** | **0** | **0** | **0** |

**Class-control-role families (production class — the pool v4r3 *forbade* to be
references):**

| stack | e2b | e4b | qwen3-4b | qwen-instruct |
|---|---:|---:|---:|---:|
| v4r4 rule | 4 | 4 | 2 | 3 |
| + raw solo headroom | 4 | 4 | 2 | 3 |
| + chance ≤ 0.75 and lift ≥ 0.20 | 4 | 4 | 2 | 3 |
| **+ interaction gates (full v5 stack)** | **4** | **4** | **2** | **3** |

**The single most consequential finding in this document.** Every v5 validity
gate is free on the production pool and expensive on the budget pool. Not one
production-class family is lost at any stage of the stack on any model. The
budget pool loses everything on three of four.

### 5.3 Why, structurally

The outcome constraint B is a **maximum word length**. Satisfying it shortens
words and shortens answers. Every count budget over a word-shaped numerator has
a statistic that scales roughly with the word count, so B moves it — always in
the direction that makes the budget easier. A rate budget divides by the word
count and is length-normalised to first order, which is why `CR5` survives
where `RF5`, `RF8` and `RF11` do not. An exact count of a short marker word is
invariant to length in either direction, and its chance rate is zero under
both distributions.

**v4r3 §13.1 says the reference must resemble A**, because it occupies A's
slot. **v4r3 §7.3 then forbids production families from the reference pool**,
on the argument that a lower bound imposes a length floor while B imposes a
ceiling. That argument is correct for count lower bounds and does not reach
exact counts of a short marker at small q, which impose essentially no length
floor — three occurrences of a four-letter word. So v4r4's actual reference
pool contradicts its own §13.1 rationale, and the pool §7.3 excluded is the one
that passes every v5 gate.

### 5.4 The library and the support thresholds this selects

**Tier 1 — same-form marker families.** Exact count of one fixed word,
registered vocabulary `thus`, `hence`, `though`, `whereas`, `indeed`,
`namely`, `instead`, `overall`. Eight families, ladders 1…8 with reserve 1…12.
§5.5 is the measurement that chose them; `however` is reserved as A's own
marker.

The one marker family v4r4 carried supports the ladder design. `CX1`'s ι
spans, at pre-screen, and where ι_A sits:

| model | `CX1` ι range over q = 1…8 | ι_A | straddles? |
|---|---|---:|---|
| `gemma-3n-e2b-it` | 0.33 – 0.71 | 0.556 | yes |
| `gemma-3n-e4b-it` | 0.50 – 0.96 | 0.667 | yes |
| `qwen3-4b` | 0.42 – 0.95 | 0.750 | yes |
| `qwen3-4b-instruct-2507` | 0.50 – 1.00 | 0.625 | yes |

A marker family's difficulty is **continuously tunable through q**, so unlike a
budget over a rare numerator it does not have to be lucky to land near ι_A.

### 5.5 The marker vocabulary, measured rather than asserted

An earlier draft of this analysis chose the eight Tier-1 markers on three
rules, two of them asserted. `d6_marker_frequency.json` measures
$P(\text{at least one occurrence} \mid \text{unconstrained})$ for every
candidate on the four v4r4 replications' unconstrained development responses.

**The benchmark is $A$'s own marker, not zero.** `however` appears in 1.3% to
**10.4%** of unconstrained responses, so a rule demanding "near zero" would
reject $A$. The registered ceiling is **0.15**, about 1.5 times $A$'s measured
maximum.

| marker | letters | role | max $P(\ge 1)$ | length | frequency |
|---|---:|---|---:|---|---|
| hence, indeed, namely, notably, besides | 5–7 | consecutive / emphatic / exemplifying / additive | 0.000 | ok | ok |
| albeit, though, whereas | 6–7 | contrastive | 0.013 | ok | ok |
| instead | 7 | substitutive | 0.021 | ok | ok |
| **thus** | 4 | consecutive | 0.057 | ok | ok |
| **however** | **7** | **contrastive** | **0.104** | — | *A's marker, reserved* |
| overall | 7 | summative | 0.112 | ok | ok |
| **finally** | 7 | summative | **0.185** | ok | **FAILS** |
| **also** | 4 | additive | **0.419** | ok | **FAILS** |
| moreover, likewise (8); therefore, meanwhile, otherwise (9); conversely (10); nonetheless (11) | >7 | — | ≤ 0.133 | **FAILS** | ok |

**Two corrections the measurement forced.**

1. The earlier draft rejected `also`, `then`, `next`, `yet` and `still` on an
   assertion of high natural frequency. **The measurement supports that for
   `also` alone** (0.419); `then` 0.039, `next` 0.021, `yet` 0.005 and `still`
   0.018 are all *below* $A$'s own rate. Those four are admissible and are
   excluded on a different, stated ground — duplicated discourse role, or a
   common non-connective sense.
2. The earlier draft registered `finally`, which the measurement rejects at
   0.185.

**A property worth recording: $B$ suppresses markers.** `however` falls from
0.102 to 0.008 under $B$ alone on `gemma-3n-e2b-it`, and `finally` from 0.185
to 0.031, because $B$ shortens answers and shifts the register. The
displacement is negative and small in absolute terms for every admitted marker,
so §7's interaction gate is satisfied comfortably — but the direction is the
opposite of the count budgets', and it is a fact about the marker family rather
than an assumption.

**Discourse role.** $A$ is a **contrastive** connective. The registered eight
span six roles and include **two** contrastive markers (`though`, `whereas`),
so a role-matched core reference set is reachable. §13.8 requires two distinct
roles among the three core references and records
`REFERENCE_ROLE_NOT_MATCHED` when none is contrastive. Role is a **declared**
label, not a measured property, and §9 item 7 records what that does not
establish.

**Tier 2 — near-form.** Exact count of a non-marker statistic: `semicolon`,
`comma_character`, `sentence`. Three families.

**Tier 3 — broad.** v4r4's 26 budget and lower-bound families, carried, and
admissible to the **spectrum** and the **broad-class** arm only.

**Support thresholds.** Historical attrition from "eligible at pre-screen" to
"qualified at calibration" was 50–100% of straddling families, and the
interaction gate then removed most survivors of the budget pool. Against a
library that is interaction-robust by construction the dominant attrition is
the caliper and the stability rule. v5 registers:

| requirement | value | why |
|---|---:|---|
| structurally eligible Tier-1/2 families before calibration | ≥ 8 | the whole registered Tier-1 vocabulary, so the requirement is a real screen and not a formality |
| qualified families after calibration | ≥ 5 | three core references plus two frozen backups |
| core references | 3 | unchanged |
| of which Tier 1 | ≥ 2 | the primary local estimand is a same-form contrast |
| distinct feature groups | 3 | unchanged from §13.4 |
| backups frozen and never substituted | 2 | v4r4 had none |
| terminal status when unmet | `REFERENCE_SUPPORT_NOT_IDENTIFIED` | |

---

## 6. F6 — the operating point sat at the edge of the measured grid on every model

`m*` was the **last measured rung** on all four replications, not only on the
one that needed the registered extension.

| | e2b | e4b | `qwen3-4b` | qwen-instruct |
|---|---|---|---|---|
| m\* | 10 | 10 | **12** | 10 |
| focal extension used | no | no | **yes** | no |
| m\* is the last rung measured | **yes** | **yes** | **yes** | **yes** |

`qwen3-4b`'s complete B curve over the registered grid and its extension:

| m | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---:|---:|---:|---:|---:|---:|
| B solo compliance | 0.031 | 0.107 | 0.245 | 0.411 | 0.659 | **0.742** |

`FOCAL_BAND` is (0.60, 0.95) and the aim is 0.80. Only m = 11 and 12 are in
band; **12 is the top of the extension**. Had B:12 also fallen short, the
replication would have recorded `FOCAL_RANGE_EXHAUSTED` with no information
about where the band begins.

**The rule this selects.** Extend the focal grid to {7, …, 14} with an
extension to {15, 16}, and require both neighbouring severities of the selected
`m*` to be measured **at calibration precision**. Cost: two rungs × 96 topics ×
4 draws per split. For `n*` the construct has a genuine floor at n = 1 — n = 0
is a well-formed exact count whose chance rate is near 1 and is therefore
chance-degenerate — so where `n* = 1` the record carries
`OPERATING_POINT_AT_GRID_BOUNDARY` with that reason rather than a manufactured
terminal status.

---

## 7. The rule this document selects

Frozen in [`reference_design_spec.json`](reference_design_spec.json); the
preregistration is the binding statement.

```
V(R) = V_specification    (Gate 1 A–E, carried unchanged from v4r4 §10.7)
   AND V_satisfiability   (formal witnesses + a realistic witness in the stem band)
   AND V_headroom         (Wilson95(p_solo) ⊂ [0.10, 0.90]; lift ≥ 0.20; vacuity ≤ 0.10)
   AND V_chance           (κ ≤ 0.75; Wilson95 upper ≤ 0.85)
   AND V_structure        (Tier 1 or 2 for a core reference; ≥ 2 of 3 Tier 1)
   AND V_interaction      (0.10 ≤ κ(R|B) + ι(1−κ(R|B)) ≤ 0.90; |Σ| ≤ 0.25)
   AND V_stability        (admissible on Calibration-A and Calibration-B separately;
                           95% bootstrap CI for each split difference inside ±0.20)
   AND V_difficulty       (|ι_R − ι_A| ≤ 0.10 pooled; Newcombe ∩ ±0.05;
                           |p_solo(R) − p_solo(A)| ≤ 0.15 as a secondary check)
```

Evaluated **lexicographically** in that order. The first failing component is
the recorded rejection reason and later components are not evaluated. **No
weighted composite score exists**, and none is registered, because the
development data are four models and could not fix weights that would
generalise.

**Two thresholds did not move, deliberately.** The ι caliper stays at **0.10**
and the Newcombe region stays at **0.05**. Tightening the caliper would select
harder on a coordinate whose standard error is 0.048; what changes is the
sample it is evaluated on, which takes the caliper from 2.10 SE to 2.96 SE.
`REFERENCE_VACUITY_MAX` stays at 0.10, having rejected two rungs in v4r4 and
mis-rejected none.

---

## 8. What the rule would have done to v4r4, stated in full

**It would have prevented both terminations.**

- `qwen3-4b-instruct-2507`: `CL8:3` at p_solo 0.9740 has a Wilson interval of
  roughly [0.954, 0.987] at n = 384, outside [0.10, 0.90]. Rejected at
  `V_headroom`, three gates before the caliper. Its κ of 0.9323 also fails
  `V_chance`. The replication does not reach Gate 4 with that companion.
- `gemma-3n-e2b-it`: `RF11:26` projects to 0.9388 and `RF11:32` to 0.9947,
  both above the 0.90 ceiling. Rejected at `V_interaction`.

**And it would have cost `gemma-3n-e2b-it` its full design.** `RF11` was one of
its three core references and supplied one of its three spectrum triples.
Without it, `CR5`, `RF9` and `RF6` remain, `RF6` cannot straddle, and two
qualifying families is one short of three. On v4r4's library, e2b runs the
reduced design instead of terminating.

That trade is the honest summary: **under v4r4's library the v5 rule turns two
terminations into two survivals and one full design into one reduced design.**
The answer is not to relax the rule. It is that the library was the wrong
library, which §5.2's second table measures directly — every v5 gate is free on
the production pool, and v4r3 excluded exactly that pool from the reference
slots.

---

## 9. What this analysis does **not** establish

1. **It is not validation.** Every threshold above was chosen after seeing
   which v4r4 candidates failed. The interaction projection's perfect
   separation is measured on the twenty rate checks that motivated it.

2. **The new library has never been measured.** Seven of the eight Tier-1
   marker families and two of the three Tier-2 families do not exist in the
   v4r4 codebase and have no compliance measurement on any model. Every
   quantitative claim about them in §5.4 is an extrapolation from the one
   family that does exist, `CX1` over `thus`. The support thresholds of §5.4
   are therefore sized on an argument, not on a measured attrition rate for the
   pool they govern.

3. **n = 4 models, and the two that matter most are one model each.** The
   interaction projection is validated on `gemma-3n-e2b-it` alone, because it
   is the only replication that ever composed a reference with B. The headroom
   rule is motivated by `qwen3-4b-instruct-2507` alone.

4. **The stability rule is sized on a split at half its registered size.**
   §1's split-half measurement is at 48 topics; v5's Calibration-A and
   Calibration-B are 96 each. The extrapolation from one to the other assumes
   the √n scaling that the same measurement is used to establish.

5. **`κ(R│B)` is measured under B at m\*, and m\* is model-specific.** The
   interaction gate is therefore a property of the pair (R, B at m\*) on that
   model, not of R. That is correct for its purpose and it means no
   cross-model transfer of the verdict is licensed.

6. **The discourse-role labels are declarations.** Nothing in the historical
   data measures whether a model treats *though* and *however* as the same kind
   of connective, and a marker's role in an informational answer under two
   simultaneous constraints may not be its role in ordinary prose.

7. **Nothing here bears on the scientific question.** No estimand was
   computed, no composed contrast was formed, and the one composed table read —
   `gemma-3n-e2b-it`'s Gate-4 rates — is viability material on a terminated
   replication under §28.3's sentence: *a terminal pre-confirmatory status
   carries no evidence about the effect.*
