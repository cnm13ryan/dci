# Claim–evidence matrix — Rounds 1–5

Canonical compact summary of the exploratory programme. Observations (**O**) are
things measured; interpretations (**I**) are things concluded; withdrawn items
(**W**) are kept, marked, and never cited as support.

Confidence is subjective, dated, and revised in place. "Causal status" is one of:
**descriptive** (measured, no manipulation), **intervention-supported** (a factor
was manipulated and a matched control did not move), **suggestive mechanism** (a
mediator-shaped relationship without a successful mediator manipulation), or
**unresolved**.

Model shorthand: **Q4** = `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f`;
**G9** = `google/gemma-2-9b-it` @ `11c9b309`. Tasks: **PLT** = 20 pilot topics,
**BRN** = 20 burned topics. All at bf16, T=0.7, top_p=0.9, 512 max new tokens.

---

## A. Observations

| # | observation | runs | models | tasks | status |
|---|---|---|---|---|---|
| **O1** | The sentence-count target alone is satisfied in **100%** of isolated rows at N=2,3,4,5,6 | A2, B, E1, E3×5, E4, E5a, E6 | Q4, G9 | PLT, BRN | descriptive, very stable |
| **O2** | A per-sentence semicolon rule's paired excess over `C_L3` is **positive in all 18 run-cells**, +0.125 to +1.000 | 18 runs | Q4 | PLT, BRN | descriptive |
| **O3** | A whole-answer floor of **≥4 semicolons** gives excess **0.975–1.000** and ~1.0 sentences | E4, E4b | Q4 | PLT | descriptive |
| **O4** | The same floor **in isolation** (no target, no background) gives **1.125** sentences; at ≥2 → 1.225; at ≥6 → 1.075 | E4b | Q4 | PLT | descriptive |
| **O5** | Per-sentence **colon** and **dash** rules give **0.000** excess; per-sentence comma 0.025–0.050 | E4 | Q4 | PLT | descriptive |
| **O6** | A whole-answer floor of ≥4 **commas** gives **−0.025 / +0.050** | E4b | Q4 | PLT | descriptive |
| **O7** | A whole-answer floor of ≥4 **colons** gives **0.850** (`o_A`) / 0.175 (`o_Q`); ≥4 dashes 0.275 / 0.475 | E4b | Q4 | PLT | descriptive |
| **O8** | Across N=2…6 the per-sentence semicolon excess is 0.375–0.925 with **no monotone trend**, largest at N=2 | E3×5 | Q4 | PLT | descriptive |
| **O9** | At N=6 the sentence count is **bimodal**: 1 or exactly 6, nothing between (0.47/0.53) | E3_N6 | Q4 | PLT | descriptive |
| **O10** | B's excess is **0.000** when the background has no colon-requiring member and **+0.125…+0.400** (`o_Q`) when it does | 18 run-cells, E4c matched pair | Q4 | PLT, BRN | descriptive |
| **O11** | Under a **paragraph**-count target the semicolon rule leaves the paragraph count at **4.000** while cutting the same responses' sentence count from 11.9 to 4.7 | E5a | Q4 | PLT | descriptive |
| **O12** | **G9** shows excess 0.000–0.125 and keeps 3.93–4.00 sentences, producing 2.0–2.6 semicolons where 4 are demanded | E6 | G9 | PLT | descriptive, **one run only** |
| **O13** | **G9 in isolation** gives 1.075–1.150 sentences under the same semicolon instructions — the same disposition as Q4 | E6 | G9 | PLT | descriptive |
| **O14** | Arm difficulty in isolation does **not** predict interference: the most damaging arm has 0.050 own-rule failure, the hardest arm (0.500) does less damage | E4b | Q4 | PLT | descriptive |
| **O15** | `chain_share` (fraction of clause boundaries realised by a non-terminal mark) orders failure across **all** marks: 0.000→0.01, 0.11–0.16→0.30–0.48, 0.24→0.23, 0.39→0.88, 0.47–0.60→0.98–1.00 | E4b | Q4 | PLT | descriptive |
| **O16** | 13,624 generations, **0 technical failures, 0 truncations** in any contrast row | all 27 | Q4, G9 | all | apparatus |

---

## B. Interpretations

### I1 — Semicolon demand induces a clause-chain strategy

**Claim.** Instructing Q4 to produce semicolons causes it to realise clause
boundaries as semicolons rather than full stops.

* **Support:** O3, O4, O15. The strategy is present *in isolation* (O4), so it is
  not a response to conflict.
* **Limiting evidence:** the strategy measure had to be rebuilt. See §D.
* **Models:** Q4 ✔, G9 ✔ (O13). **Tasks:** PLT, BRN. **N:** 2–6. **Backgrounds:** 7.
* **Causal status: intervention-supported.** Dose was manipulated (q=2/4/6) with a
  wording-matched zero-semicolon control that did not move (O6).
* **Untested assumptions:** only one decoding configuration; only wordings 0 and 2;
  q ∈ {1,3,5} never tested.
* **Cheapest discriminating test:** greedy decoding (T=0) — near-free, and settles
  whether this is a mode of the distribution or a sampling artefact.
* **Confidence 2026-08-11: 0.90.**

### I2 — The clause-chain is the mediator of sentence-count failure

**Claim.** The failure of an exact-sentence-count target is produced *through* the
chaining, not alongside it.

* **Support:** O15 — `chain_share`, computed only from punctuation counts, orders
  failure across four different marks and both orders. O11 and O12 are the
  decisive independence checks: high chain share with **no** failure.
* **Contradictory / limiting:** **no mediator-blocking intervention has
  succeeded.** Two were tried and both failed their manipulation checks (W3, O-E7).
  A mediator relationship without a mediator manipulation is not established.
* **Causal status: suggestive mechanism.**
* **Untested assumption:** that a manipulation which lowered `chain_share` while
  leaving the semicolon demand intact would lower failure. Never achieved.
* **Cheapest discriminating test:** an instruction that *satisfies* the semicolon
  demand in a non-boundary position (e.g. "use semicolons only inside a list").
* **Confidence 2026-08-11: 0.55.**

### I3 — The trigger scales with the number of semicolons demanded (q)

* **Support:** O3 vs O4 vs E4b's q=2 cell — excess 0.20 (q=2) → 0.975 (q=4) →
  0.99 (q=6) at N=4.
* **Causal status: intervention-supported** (dose manipulation, matched control).
* **Confidence 2026-08-11: 0.85.**

### I4 — ~~The threshold sits at q ≈ N~~ **UNIDENTIFIED — see W7**

### I5 — Per-sentence scoping is *protective*, not causative

**Claim.** A per-sentence rule forces the demanded marks apart and thereby
protects the sentence count; a whole-answer floor permits concentration.

* **Support:** the colon at matched dose — per-sentence → 4.000 sentences, 0.000
  excess; whole-answer ≥4 → 1.775 sentences, 0.850 excess (O5, O7).
* **Limiting:** demonstrated for the **colon** at N=4 only. For the semicolon the
  ordering is the same (per-sentence 0.70 < whole-answer 0.975) but both are large.
* **Causal status: intervention-supported** (scope manipulated, dose held at 4).
* **Untested:** any mark at any N ≠ 4.
* **Confidence 2026-08-11: 0.75.**

### I6 — The operative property is the model's *deployment habit*, not the mark's grammatical class

* **Support:** colon and dash are boundary-capable in English and give 0.000
  per-sentence excess because Q4 uses them *within* sentences (O5); the same colon
  demanded of the whole answer *is* used at boundaries and does collapse (O7).
* **Causal status: descriptive**, but strongly constrained by the O5/O7 reversal.
* **Confidence 2026-08-11: 0.80.**

### I7 — B's directional interference is a B × background interaction, not a property of B

* **Support:** O10, and the E4c matched pair in which one background member was
  swapped and the control never moved.
* **Contradictory:** under wording 2 (E2b) B shows +0.525/+0.750 *with* the colon
  background — so wording also matters and the interaction may not be colon-specific.
* **Causal status: intervention-supported for the colon factor**, but the clean
  2×2 (`A`, `A+B`, `A+C`, `A+B+C`) has **never been run** — every existing
  comparison is across runs at fixed load.
* **Cheapest decisive test:** Experiment B.
* **Confidence 2026-08-11: 0.70.**

### I8 — τ is conditional on the background set

**Claim.** A background identical across arms cannot *bias* τ but can decide
whether τ exists; a τ reported without naming its background is underspecified.

* **Support:** O10 — a 4× swing in B's estimate with the matched control at 0.000
  throughout.
* **Causal status: intervention-supported.** This is the finding with the largest
  consequence for the DCI protocol itself.
* **Untested:** whether the same conditionality holds for the confirmatory pairs.
* **Confidence 2026-08-11: 0.85.**

### I9 — The mechanism is specific to targets whose unit the mark can stand in for

* **Support:** O11. Same instruction, same behaviour, no failure, because the
  target counts paragraphs.
* **Limiting:** the paragraph-side substitute (`X_LINEBREAK_EACH`) was **ignored**
  by the model, so the converse was never tested; and the numerical-family test
  (E5b) used a target that fails 0.725 unaided and is uninformative.
* **Causal status: intervention-supported** (target unit manipulated).
* **Confidence 2026-08-11: 0.75.**

### I10 — The disposition is model-general; the *arbitration* is model-specific

**Claim.** Both Q4 and G9 realise a bare semicolon demand as one chained sentence;
under conflict with a sentence count, Q4 keeps the semicolons and G9 keeps the count.

* **Support:** O12, O13.
* **Limiting:** **G9 was tested at one cell of every other factor** — one run, one
  N, one background, one wording, one split. n = 2 models.
* **Causal status: descriptive.**
* **Cheapest discriminating test:** Experiment C — more models, and a decomposition
  into disposition / competence / joint compliance / which instruction is sacrificed.
* **Confidence 2026-08-11: 0.50** (direction), **0.25** (that it is a *family*
  property rather than a checkpoint property).

### I11 — Not compositional difficulty, not ability

* **Support:** O14 (difficulty is anti-correlated with damage), O9 (bimodality).
* **Causal status: descriptive**, but both are strong exclusions.
* **Confidence 2026-08-11: 0.85.**

---

## C. Highest-consequence unresolved claims

| rank | claim | why it matters | test |
|---|---|---|---|
| 1 | Does the boundary depend on **q**, **N**, **q/N**, or **q − N**? | decides whether the mechanism is "many semicolons" or "as many semicolons as sentences" — a different theory | **Experiment A** |
| 2 | Is the apparent **B → A** effect really **B × S → A**? | the original v19 pair-3 headline; and if true, DCI's estimand needs restating | **Experiment B** |
| 3 | Is the arbitration difference a **family**, **generation** or **checkpoint** property? | decides whether any of this generalises beyond one model | **Experiment C** |
| 4 | Would lowering `chain_share` while keeping the semicolon demand lower failure? | the only missing leg of the mediation claim | not yet designed |
| 5 | Is any of it robust to decoding? | the whole programme is at one sampling configuration | greedy run, near-free |

---

## D. Withdrawn and superseded

| # | item | round | why |
|---|---|---|---|
| **W1** | r = 0.998 correlation between collapse and A-failure | 1, withdrawn R2 | partly definitional — collapse ⊂ A-failure |
| **W2** | κ = −0.132 coupling statistic | 3, withdrawn R4 | Cohen's kappa reported under a name the preregistration defines as a rate in [0,1] |
| **W3** | D2's anti-collapse scaffold as **causal** evidence | 2, withdrawn R5 | a length- and form-matched sham reproduced most of the effect |
| **W4** | "Per-sentence scoping causes substitution" | 2 (D3), inverted R5 | scoping is protective (I5) |
| **W5** | "Boundary-capable marks collapse the count" | R5 prediction, refuted R5 | colon and dash give 0.000 per sentence (O5) |
| **W6** | "Ordinary references fail by overshoot" | 1, withdrawn R4 | after the verifier repair they barely fail at all |
| **W7** | **"The threshold sits at about the target sentence count"** | R5, **withdrawn here** | **q and N were never crossed.** Free q was varied only at N=4, where q≥4, q≥N and q/N≥1 are the same hypothesis. See the coverage matrix §0. |
| **W8** | E7's prohibition outcomes as intervention evidence | R5, withdrawn R5 | manipulation checks failed: one instruction ignored, the other over-applied into a total comma ban |
| **W9** | `severe_collapse` (n_sentences == 1) as the **mediator** variable | R2–R5, superseded here | it is a sentence-count quantity and therefore a subset of the outcome; replaced by `splice_share` / `chain_share`, which are punctuation-only |

### D-bis. A measurement defect found while building this matrix

`extensions.splice_count` matched only `[;,]`, so **colon and dash splice counts
silently returned 0 for every input**. No published claim rested on them (the
first use was the E7 manipulation check, which concerns semicolons and commas),
but the mark-agnostic `chain_share` in O15 would have been wrong. Fixed to
`(--|[;,:—–])` and re-verified; the corrected values are what O15 reports.

---

## E. Current confidence summary

| | claim | confidence |
|---|---|---|
| strongest | I1 semicolon demand → clause chaining (incl. in isolation) | 0.90 |
| | I8 τ is background-conditional | 0.85 |
| | I3 dose-dependence in q | 0.85 |
| | I11 not difficulty, not ability | 0.85 |
| | I6 deployment habit, not grammatical class | 0.80 |
| | I5 per-sentence scoping is protective | 0.75 |
| | I9 specific to targets whose unit the mark replaces | 0.75 |
| | I7 B's effect is a background interaction | 0.70 |
| weakest | I2 chaining mediates the failure | 0.55 |
| | I10 arbitration is model-specific | 0.50 / 0.25 |


---

## F. Round 6 revisions

### New and revised claims

| # | claim | evidence | causal status | confidence |
|---|---|---|---|---|
| **I3′** | The trigger has an **absolute threshold at q ≈ 3 semicolons, invariant in N over 2–6** | R6-A, full 6 × 5 grid: the q = 3 row is 0.775–0.988 at every N; every q ≤ 2 row is 0.05–0.81 | intervention-supported | **0.90** |
| **I4′** | ~~q ≈ N~~ **refuted.** A ratio (q/N) and a difference (q − N) account are refuted with it | at N = 6, q = 3, 4, 5 are all < N and all collapse (0.887–1.000) | intervention-supported | **0.90** (as a refutation) |
| **I2′** | The mediator threshold is in **`chain_share` ≈ 0.30–0.36**, and it is the same at every N | R6-A: chain_share 0.219–0.296 at q = 2 and 0.360–0.510 at q = 3, across all five N | suggestive mechanism (still no successful mediator block) | 0.70 |
| **I7′** | The B → A effect is a **pure higher-order interaction** with no main effects | R6-B: F(A+B) = 0.000, F(A+C) = 0.013, F(A+B+C) = 0.312; interaction **+0.312 [+0.188, +0.438]** count-matched, +0.300 raw; load-3 control cell 0.000 | intervention-supported | **0.90** |
| **I7″** | The amplifier is **not B-specific**: the colon raises the semicolon arm 0.287 → 0.812 in the same design, and the colon instruction alone gives 1.150 sentences | R6-B | intervention-supported | 0.85 |
| **I10′** | The **disposition is universal** (4/4 models → ~1 sentence from a bare 4-semicolon demand); the **arbitration is a checkpoint property** | R6-C, four models | descriptive | 0.75 |
| **I10″** | ~~"Qwen vs Gemma"~~ is the wrong axis: per-sentence failure varies 0.713 / 0.263 / **0.025** *within* the Qwen family | R6-C | descriptive | 0.80 |
| **I5′** | Scoping-as-protection reproduces in a second model generation: Qwen3.5-9B fails the per-sentence form 0.025 and the whole-answer floor 0.787 | R6-C | intervention-supported | 0.85 |

### Newly withdrawn

| # | item | why |
|---|---|---|
| **W10** | "The interference is Qwen-specific / model-family-specific" (R5) | tested on one non-Qwen model with one arm form. With four models and two forms, the whole-answer floor interferes in 3 of 4, and the per-sentence form varies more *within* Qwen than between Qwen and Gemma. |
| **W11** | The first `Qwen/Qwen3.5-4B` run | invalid: run under the model's default reasoning template, so it measured a `<think>` trace, not the answer. Run kept and marked; re-run under `enable_thinking=False`. |


---

## G. Round 7 revisions

| # | claim | evidence for | evidence against | manipulation | causal status | conf. | updated this round |
|---|---|---|---|---|---|---|---|
| **I3″** | The q ≈ 3 transition **survives greedy decoding**; it is the model's preferred completion, not a sampling artefact | Stage 1: q=3 → 1.000 at T=0 vs 0.988 at T=0.7; **97.5%** of greedy rows at exactly 1 sentence; `chain_share` 0.706 vs 0.714 | none | decoding temperature manipulated, controls at 0.000 throughout | intervention-supported | **0.90** | **yes, new** |
| **I12** | Temperature changes **mixture proportions**, not strategy identity | Stage 1: q=2 sits at n=4 in 0.70 / 0.54 / 0.64 of rows across T = 0 / 0.3 / 0.7, with identical strategies present at all three | — | same | intervention-supported | 0.75 | yes, new |
| **I13** | Ordering matters: Δ spans **0.525** across the six permutations, organised by the **focal instruction's position** (+0.400 / +0.287 / +0.012) | Stage 2, all six orderings, matched within (task, π, variant, replicate) | the gradient does not survive to k=5 (I15) | ordering manipulated with both replacement controls | intervention-supported | 0.85 | yes, new |
| **I13a** | **B-first architecture** supported (+0.350 vs +0.117); **colon priming refuted** with the opposite sign; **adjacency refuted**; **co-presence refuted** | Stage 2 | — | as above | intervention-supported | 0.80 | yes, new |
| **I14** | The amplification is caused by the colon **instruction**, not by the colon **mark** | Stage 2: colon production ranges 0.150–0.950 across orderings and does not track Δ (`CQA` 0.225 colons → Δ +0.325; `ACQ` 0.950 colons → Δ −0.125). Within-condition, paired by task, rows containing a colon fail **−0.049 [−0.134, +0.033]** | — | observational within an intervened design | suggestive → **falsifies the mark-supply account** | 0.80 | yes, new |
| **I15** | The ordering effect **attenuates under load** and its monotone structure is lost | Stage 3: `QAC` +0.400 → +0.250; `AQC` +0.250 → +0.075; `ACQ` −0.125 → **+0.125** | — | load manipulated, control at 0.004–0.006 both loads | intervention-supported | 0.75 | yes, new |
| **I16** | B and the semicolon demand reach the **same endpoint by different routes** — option (2), not mechanism identity | Stage 6 on existing matched data: failing rows both at ~1.15 sentences and chain 0.71–0.77, but B at 149 words/sentence and 8.28 comma splices against 51 and 1.02; arbitration **opposite** (B sacrifices its own rule 0.600, semicolon sacrifices the target 0.750) | — | none (re-analysis) | observation | 0.80 | yes, new |

### Newly withdrawn

| # | item | why |
|---|---|---|
| **W12** | *"The colon-requiring background instruction was supplying B with a boundary-capable mark"* (Round 6, I7″) | **Falsified by Stage 2.** The mark need not appear: Δ is large where colons are rarely produced and negative where they almost always are, and within the colon condition producing one is if anything slightly protective. |
| **W13** | `severe_collapse` and, retrospectively, the closed-list-only `splice_count` as *graded* measures | The Stage 0.3 audit found precision 18/18 but style-dependent recall — a six-join answer scoring 0.000. Magnitudes computed under that rule are not comparable across conditions; the shape-test revision replaces it. |
| **W14** | Any claim that greedy decoding is bit-reproducible in this harness | 112/160 replicate pairs identical in text (96.2% in outcome). bf16 matmuls are not associative across batch padding widths. |


---

## H. Round 8 revisions

| # | claim | evidence for | evidence against | manipulation | causal status | conf. | updated |
|---|---|---|---|---|---|---|---|
| **I17** | The amplifier property is **a single free-floating character**, not the colon | S14: `X_SEMI_EXACT1` τ = **+0.950** [+0.875,+1.000], `U_FMT_COLON1` +0.450 [+0.275,+0.625], `U_FMT_QUOTE1` +0.050, `U_FMT_PAREN1` 0.000; all four exactly-one, global, formatting; compliance 0.950–1.000 | free placement and single-character-ness are not yet separated | object type manipulated with count, scope, family and wording held | intervention-supported | **0.80** | new |
| **I18** | **Exact-count bookkeeping, global scope and formatting identity are each insufficient** | all four S14 variants have all three properties; two amplify, two do not | — | as above | intervention-supported | 0.85 | new |
| **I19** | **Colon-specific identity is refuted** | the semicolon amplifies >2× as strongly under a byte-matched wording | — | as above | intervention-supported | 0.85 | new |
| **I20** | `chain_share` does not order the amplifier variants | semicolon 0.345 share / 0.950 failure against colon 0.414 / 0.450; sentence counts *do* order them (1.95 vs 2.90) | — | — | observation; a limit on the measure | 0.80 | new |
| **I21** | **Qwen3.5-4B does not terminate its reasoning within any budget this hardware affords** | S1_natural2: mean realised M = 4063 at b = 4096, median 4096, **2/16 closed naturally**; b = 8192 OOMs at batch 8 | — | budget manipulated | observation | 0.90 | new |

### Newly withdrawn / blocked

| # | item | why |
|---|---|---|
| **W15** | Any hard-budget reasoning result for this checkpoint | Every affordable budget lands inside the reasoning phase, so a grid would measure **interruption**. Stages 2–13 not run; harness complete and validated on criteria 1 and 3, failing 2 and 4 for this model/hardware pair. |
| **W16** | The first `S1_natural` run | Invalid: 48/48 OOM. Retained and marked. It also exposed a harness defect — a failed batch wrote no row at all — now fixed to record null rows as `runner.run` always has. |

---

# Round 10 — claim register

Labels: **Established within tested conditions** · **Intervention-supported but
narrow** · **Mechanistically suggestive** · **Falsified** · **Unidentified**.

| # | claim | status | evidence for | evidence against / limits | boundaries |
|---|---|---|---|---|---|
| W10.1 | Amplification arises because the model must decide **where to place** an unattached mark (P7) | **FALSIFIED** | — | S25: Δ_placement = +0.000 / −0.050 / −0.050 / +0.000 at b = 0/256/1024/4096, with focal A-failure off ceiling (0.15–0.45) and identical between arms | Qwen3-4B, Pair 3, QAC, k = 3; anchored compliance 0.575–0.875 |
| W10.2 | A compliable fixed-placement manipulation can be built | **Established** | lexical anchor + worked example reaches 0.700–0.875 compliance, against 0.000–0.338 for all ten counting wordings | it is **not inert**: raises reference-arm A-failure to 0.333 pooled | as above |
| W10.3 | Ordinary B→A interference falls to zero with reasoning | **Established within tested conditions** | τ_control +0.400 → 0.000 by b = 512, holding at 0 through 4096; nine budgets | one checkpoint, one order, k = 3 | Qwen3-4B, QAC |
| W10.4 | That is a **reasoning-dose** effect, not just thinking-on/off | **Established within tested conditions** | τ_control = +0.150 at b = 256 vs 0.000 at b ≥ 512, both positive budgets | b = 0 → b > 0 additionally mixes in mode activation and is reported separately | as above |
| W10.5 | The decline is gradual, not a sharp threshold | **Established within tested conditions** | +0.400 → +0.150 → +0.050 (×3 budgets) → 0.000 | b = 256 is 95% censored; the shape near zero is fine-grained | as above |
| W10.6 | Amplified interference is more **compute-resistant** than ordinary interference | **Established within tested conditions** | Δ grows +0.200 → +0.500 at QAC; τ_amp stays 0.35–0.50 while τ_control reaches 0 | the amplifier's own τ *falls* from +0.600 to +0.500 — the gap widens because the control is repaired | Qwen3-4B, QAC, k = 3 |
| W10.7 | Compute resistance is **order-dependent** | **Established within tested conditions** | Δ at ACQ: −0.450 (b=0) → +0.250 (b≥1024); at QAC: +0.200 → +0.500 | ACQ Δ intervals touch 0.000 at the high budgets | k = 3 |
| W10.8 | Without reasoning, the semicolon background is **protective** at ACQ | **Established within tested conditions** | Δ = −0.450 [−0.650, −0.250] at b = 0 | single order pair; ACQ vs QAC varies the whole permutation | native non-thinking only |
| W10.9 | Compute-resistant amplification survives k = 5 | **Established within tested conditions** | Δ = +0.575 [+0.350, +0.775] at b = 4096, k = 5 | the k = 5 low-budget column is 99.2% censored, so only the high budget is informative | QAC |
| W10.10 | Reasoning improves **prioritisation**, not joint satisfaction | **Established within tested conditions** | P(both) ≤ 0.150 everywhere while P(target only) reaches 0.85–0.95; joint satisfiability independently certified | B compliance is near its floor throughout, which limits how much room "both" ever had | all Round 10 conditions |
| W10.11 | Single-character atomicity is required | **FALSIFIED** (Round 9) | — | 3-character ellipsis amplifies at 1.000 compliance | — |
| W10.12 | The unattached/enclosing distinction predicts amplification | **Intervention-supported but narrow** | every complied unattached variant amplifies, every enclosing one does not, across two wordings | *why* it does is now unexplained: not placement, not atomicity, not mark production | Qwen3-4B-Instruct, QAC |
| W10.13 | An unattached mark amplifies because it can **substitute for a sentence boundary** while a wrapping construct cannot | **Mechanistically suggestive** | consistent with the semicolon's chain_share 0.43 and 1.3 sentences | the ellipsis amplifies with chain_share 0.03 — so this cannot be the whole account | untested by intervention |
| W10.14 | `chain_share` mediates amplification | **Unidentified** (unchanged) | — | semicolon and ellipsis dissociate on it | — |

---

# Round 11 — the arbitration programme (`runs/arbitration_program_20260811T185546Z`)

6,282 generations, correct per-unit seeds, 4 replicates. Labels as in Round 10.
Every claim here is estimated by a 10,000-draw cluster bootstrap over the 20
tasks and was recomputed independently from the raw JSONL (282 quantities, no
disagreements).

| # | claim | status | evidence for | evidence against / limits | boundaries |
|---|---|---|---|---|---|
| W11.1 | The Round 9/10 phenomenon survives correct decoder seeds | **Established within tested conditions** | all six headlines reproduce; per-replicate Δ agrees in sign in all four replicates of all four Experiment 1 cells | per-replicate spread 0.15–0.35, so cell-level differences below ~0.2 stay unresolvable | Qwen3-4B, Pair 3, k = 3 |
| W11.2 | Reasoning abolishes ordinary interference | **Established within tested conditions** | τ_control falls to −0.025…+0.087 at b = 4096 in **all six** orders and on **both** models | b = 0 → 4096 mixes mode activation with dose; the nine-budget dose curve is Round 10's | both models, six orders |
| W11.3 | Semicolon-conditioned interference is not abolished | **Established within tested conditions** | τ_amp = +0.550 [+0.450, +0.650] at QAC, b = 4096; Δ positive in all six orders at b = 4096, five intervals excluding zero | **fails to transport** to SmolLM3-3B (Δ = −0.062) | Qwen3-4B |
| W11.4 | The sign of the semicolon's effect is set by instruction **order**, not by the mark | **Established within tested conditions** | Δ at b = 0 spans −0.537 (ACQ) to +0.388 (CQA) across the six permutations of the same three strings | — | Qwen3-4B, b = 0 |
| W11.5 | A simple positional rule explains the order effect | **FALSIFIED** | — | 14 partitions tested; 3 separate one quantity each, by 1.16–1.33× their own within-group spread; none separates all three | six orders, 20 tasks |
| W11.6 | ACQ's protection is a positional special case of a gradient | **Unidentified** | — | the three orders sharing each of ACQ's features give Δ = +0.000, +0.013, +0.175 | — |
| W11.7 | Reasoning raises joint satisfaction | **FALSIFIED** | — | P(both) ≤ 0.113 in Experiment 1's 8 cells and ≥ 0.15 in only 1 of the order map's 24; reasoning moves 0.2–0.6 of mass between "neither" and "target only" | all conditions, both models |
| W11.8 | An explicit priority cue changes which instruction survives | **FALSIFIED** | — | Ψ = +0.037 / −0.013 / −0.087 / −0.113, every interval containing zero; the one contrast clearing zero is `B>A − equal` = **+0.163**, the wrong direction | Qwen3-4B, QAC, k = 3 |
| W11.9 | The priority null is inattention to the cue | **FALSIFIED** | — | reasoning traces mention priority/preference/trade-off in 0.54–0.69 of directed rows vs 0.21–0.39 under equal priority | as above |
| W11.10 | A stated priority produces general assistance instead | **FALSIFIED** | — | `both(A>B) − both(equal)` = −0.062 [−0.125, −0.013] at the semicolon, b = 4096; every other contrast contains zero | as above |
| W11.11 | The reasoning effect transports to a second lineage | **Established within tested conditions** | SmolLM3-3B: Γ = +0.400 [+0.113, +0.688] (QAC), +0.300 [+0.075, +0.537] (ACQ); τ_control +0.263 → +0.025 | one second model | byte-identical prompts |
| W11.12 | The semicolon amplification transports | **FALSIFIED (within this comparison)** | — | Δ at b = 4096 is −0.062 (QAC) and −0.013 (ACQ) on SmolLM3-3B; Δ at b = 0 is **negative in both orders** | weakened by SmolLM3 background compliance 0.194–0.575 and a reference arm reaching 0.675 A-failure |
| W11.13 | The order interaction transports | **FALSIFIED (within this comparison)** | — | Γ_QAC ≈ Γ_ACQ on SmolLM3 (+0.400 vs +0.300, overlapping) where Qwen3-4B differs threefold | as above |
| W11.14 | The amplifier acts through the **sentence boundary** | **Mechanistically suggestive** (unchanged from W10.13) | the semicolon shortens answers by 0.35–0.72 sentences on Qwen3-4B and 0.42–1.17 on SmolLM3-3B; two hand-found degenerate satisfactions place the mark where a boundary would go (`…itself.; The`, a free-standing `;`) | both are incidental observations, not manipulations | untested by intervention — this is the recommended next experiment |
| W11.15 | The arbitration observed is target-versus-focal | **Unidentified** | — | B is satisfied in 0.000–0.138 of focal-arm rows and "focal only" occurs in 7 of 640; the contest measured is target-versus-nothing | limits every arbitration reading in Rounds 9–11 |
