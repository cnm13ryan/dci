# The DCI Construct Decision

**Construct decision memo — pass 2 · read-only investigation · 14 August 2026**

124 run configurations · ~35,000 stored generations · 4 git worktrees.
Every load-bearing number recomputed from raw text via the project's own verifier registry.

Supersedes `dci-construct-pass1.md`, which is retained as a record of the revision.

---

What "constraint interaction" should mean, decided from the stored generations. The phenomenon survives;
the pairwise parameter used to measure it does not. Three independent sign reversals rule out the legacy
estimand as primary.

**Status labels used throughout.**
*Observation* = recorded and reproduced ·
*Holds* = stable across the conditions tested ·
*Reverses* = changes sign with a design variable ·
*Not identified* = estimate exists, interpretation does not ·
*Withdrawn* = claim retracted on this pass.

---

## A. Bottom line

> The robust phenomenon is **failure to compose**: across every configuration tested, the model reaches
> joint satisfaction rarely, and interventions redistribute which instruction is abandoned rather than
> raising joint success. The legacy target-damage contrast is not measuring that. It reverses sign under
> three separate design variables and is structurally zero on most checkpoints.

### What appears to be the phenomenon

Two facts recur in every dataset I could recompute, across two model families, six instruction orders, five
reasoning budgets and both backgrounds:

1. **Joint satisfaction is low and stays low.** P(both instructions satisfied) never exceeds 0.225 in 24
   order × budget × background cells, and is ≤ 0.138 in the cross-model replication.
2. **The sacrifice is one-sided.** The state "focal satisfied, target failed" is essentially never occupied
   — 0.000 to 0.025 everywhere, and 0.000 / 0.000 / 0.008 across a deliberately graded focal-difficulty
   ladder on held-out tasks. The model does not trade off; when it cannot do both, it keeps the target and
   drops the other instruction.

That asymmetry is the directional content of "constraint interaction" in this corpus — and it is visible
only in the joint outcome, never in target failure alone.

### What is ruled out

- **[Reverses] Target damage as a stable pairwise parameter.** The semicolon amplification Δ flips sign
  with instruction order (+0.275 at QAC, −0.537 at ACQ) and with checkpoint (+0.275 on Qwen3-4B, −0.463 on
  SmolLM3-3B), with intervals clear of zero in each case.
- **[Holds] The arbitration account.** An explicit priority instruction was run as a designed intervention.
  It does not change which instruction survives: all four intervals contain zero, three point estimates
  carry the wrong sign, and telling the model to prefer the focal instruction made the *target* more likely
  to survive. The cue was demonstrably read.
- **[Holds] Constraint identity as the whole story.** Neither the focal instruction alone nor the background
  alone damages the target; only their conjunction does (+0.312, interval clear of zero). The object is at
  least three-place, not two-place.

### What remains genuinely open

- Whether the delivery collapse is *target-specific* or generic compositional load. Composition costs the
  focal instruction 0.47 and the matched reference 0.31 — an asymmetry of only ~0.15, far smaller than the
  single-run figure suggests.
- Whether anything survives once the background mark cannot serve as a clause boundary. With a matched
  non-boundary mark, target damage is +0.100 at zero reasoning and −0.037 with reasoning.
- Whether the phenomenon is a property of the constraint pair or a capability threshold. One checkpoint
  composes the pair at 1.000.

### [Withdrawn] A claim from the earlier pass, retracted here

I previously argued that the headline semicolon effect was substantially a *segmentation-convention
artefact*, on the grounds that target damage reverses sign if a boundary-standing semicolon is counted as a
sentence boundary. **That reasoning was wrong, and the repository contains the evidence that refutes it.**

Two blinded human audits exist in `exploratory/verifier_audit/`. Scoring their 65 adjudicated cases with the
current segmenter: **the shipped convention matches the human sentence count on 65 of 65 cases**, including
all 44 answers containing a boundary-standing mark. The alternative convention matches on 0 of those 44.
Human annotators explicitly labelled 16 cases `one_semicolon_chain` with a human count of 1 — they read a
semicolon chain as one sentence, exactly as the verifier does.

The arithmetic sensitivity is real and still matters as a robustness fact. The interpretation was not.
Target failure under a semicolon background is genuine behavioural failure, and the effect it measures is
behavioural. The correct statement of the mechanism is in §D.3.

---

## B. Empirical map

### B.0 Where the evidence is, and one thing that is wrong with it

The primary working directory holds **no raw generations** — `exploratory/runs/` is git-ignored and absent.
The generations live in three sibling git worktrees of the same repository (201 MB / 120 MB / 45 MB).

**[Observation] A committed analysis table is built from sources the project itself marks unusable.**
`exploratory/figures/reasoning_compute/data/reasoning_rows.csv` is tracked in git. Matching all 1,440 rows
by exact answer text: budgets 0/256/512/1024/4096 match `s18_reasoning.jsonl` at 1.000 (manifest status
**DEPRECATED**, 97.5% of replicate pairs byte-identical) and budgets 320/384/448/640 match
`s18_transition.jsonl` at 1.000 (**FOREIGN**, 98.4% identical). The canonical replacement
`s18_reseeded.jsonl` matches at 0.000. Effective independent sample size is about half the nominal, and its
bootstrap intervals are correspondingly narrow. It is not used here.

### B.1 Seeding, which determines what can be quoted at all

*Observation.* Rounds 1–10 seeded all requests in a batch identically: ~98% of nominal replicate pairs are
byte-identical. A repair in the tree seeds from the row's index in the design file, which removes the
duplicates but still is not a scientific seed — matched focal and reference rows draw different decoder
noise, so the paired contrast is not a common-random-number difference. Only one programme seeds from
experimental identity (`blake2b(master | task | replicate | phase)`): the **arbitration programme**, 6,282
generations, validated at 0 of 192 identical replicate pairs. **It is the only dataset in the corpus whose
replicate structure supports the intervals it quotes**, and it is weighted accordingly below.

### B.2 The regimes

A = "write exactly 4 sentences"; B = "each sentence strictly longer than the last"; R = "begin every
sentence with a word starting with S"; S = background mark instruction. τ = P(A fails | B) − P(A fails | R),
paired over 20 tasks.

| Regime | Model · condition | n | P(X_A) | Focal uptake | Ref uptake | P(both) | τ | Status |
|---|---|---|---|---|---|---|---|---|
| **2×2 factorial** A / A+B / A+S / A+B+S | Qwen3-4B-Instruct, no reasoning | 40–120 | 1.000 alone; 0.688 composed | 0.150 | 0.650 | 0.150 | 0.000 (load 2); 0.312 (load 3) | Identified |
| **Boundary control** semicolon vs degree sign | Qwen3-4B-Instruct, b=0 / 4096 | 640 | 0.887–0.963 (degree); 0.275–0.487 (semi) | 0.050–0.237 | 0.338–0.912 | 0.000–0.200 | degree −0.037; semicolon +0.475 | Identified |
| **Six-order map** | Qwen3-4B, per-unit seeds | 2560 | varies | ≤0.15 | — | 0.000–0.225 | Δ spans −0.537 → +0.550 | Reverses |
| **Priority intervention** | Qwen3-4B, 3 priority cues | 960 | 0.425–0.975 | 0.000–0.138 | — | low | Ψ ≈ 0, wrong sign | Clean null |
| **Cross-model** | SmolLM3-3B, same design | 1280 | 0.325–0.950 | 0.050–0.150 | 0.263–0.650 | ≤0.138 | Δ = −0.463 (QAC, b=0) | Reverses |
| **Focal ladder** 3 difficulty rungs | Qwen3-4B, held-out CAL tasks | 720 | 0.758–0.958 | 0.033→0.467 | — | 0.033→0.458 | — | Identified |
| **Five checkpoints** | Qwen3.5-4B/9B, gemma-4-12B/E4B | 80 / cell | 1.000 (4 of 5) | 0.175–1.000 | 1.000 | 0.175–1.000 | 0.000 | Target ceiling |
| **Bounded-thinking export** | 4 checkpoints incl. Kimi-VL | 640 | — | — | — | — | — | 19.2% missing, arm-differential |

### B.3 Solo baselines — the census the programme never assembled

*Observation.* Many runs contain a `primitive` condition in which a constraint is presented entirely alone.
Verified from the stored prompts. Pooling every such cell gives the marginal difficulty of each instruction,
which is what a "matched" reference must be matched on.

| Instruction | Runs | Rows | P(satisfied) alone | Range |
|---|---|---|---|---|
| **A** — exactly 4 sentences (target) | 28 | 1164 | 0.964 | 0.000–1.000 |
| **B** — increasing sentence lengths (focal) | 25 | 1044 | 0.541 | 0.125–0.714 |
| **R** — sentence-initial S (reference) | 34 | 1404 | 0.716 | 0.000–1.000 |

Paired within the 19 runs that contain all three, the gap R − B is **+0.193 (sd 0.212)**, with B easier than
R in only 2 of 19 runs.

**[Not identified] The matched reference is not matched on realised difficulty.** Every estimand that
compares P(X_B) against P(X_R) — joint-satisfaction loss and the four-state redistribution vector alike —
inherits this ~0.19 confound, and it has never been measured or reported.

---

## C. Candidate phenomenon → construct → estimand

Notation, fixed for the rest of the memo. For a prompt containing instructions `c₁…c_k`, let `X_c ∈ {0,1}`
be realised compliance with instruction `c` and `G_c ∈ [0,1]` the verifier's graded score on it. Write `A`
for the designated target, `B` for the focal instruction, `R` for the matched reference, `S` for the
background. A *configuration* is the tuple (checkpoint, instruction order, load, reasoning condition,
decoding settings, background).

### Candidate 1 — Target-specific damage · **Not primary**

- **Phenomenon.** Changing one instruction changes compliance with a designated target.
- **Primitive.** `X_A` alone.
- **Estimand.** `τ = P(X_A=0 | A+B+S) − P(X_A=0 | A+R+S)`, paired over tasks.
- **Assumes.** R matched to B on everything but the property of interest, *including marginal difficulty* —
  false by 0.193 (§B.3).
- **Degenerate.** When P(X_A) ≈ 1 in both arms; when the reference itself damages the target; when the
  damage lands on S.
- **Scope.** Silent on everything that happened to B, R and S.

### Candidate 2 — Joint-satisfaction loss · **Confounded**

- **Phenomenon.** Substituting the focal instruction changes the probability everything is satisfied at once.
- **Primitive.** `X_A ∧ X_slot`.
- **Estimand.** `Δ_joint = P(X_A=1, X_B=1 | A+B+S) − P(X_A=1, X_R=1 | A+R+S)`.
- **Assumes.** That `X_B` and `X_R` are commensurable. They are two different predicates with marginal rates
  differing by 0.19.
- **Degenerate.** Never structurally — which is the flaw. It returns a large number whenever B is simply
  harder, with or without interaction.

### Candidate 3 — Redistribution among joint states · **Primitive layer**

- **Phenomenon.** An intervention moves probability between the four ways two instructions can come out.
- **Primitive.** `p = [P(0,0), P(0,1), P(1,0), P(1,1)]`.
- **Estimand.** Within a single arm: `p` itself, and `p(intervention) − p(control)` where the intervention
  does not change which instructions are present.
- **Strength.** The only representation in which the two replicating facts — low P(both), empty "focal only"
  — are visible at all.
- **Caveat.** When used *across arms* it inherits Candidate 2's confound. Use within-arm.

### Candidate 4 — Reciprocal delivery loss · **Primary**

- **Phenomenon.** Adding context to an instruction degrades compliance with that instruction itself.
- **Primitive.** Each `X_c` against its own solo baseline.
- **Estimand.** `D(c ← G) = P(X_c=1 | c alone) − P(X_c=1 | c with G)`, reported for every instruction
  present; asymmetry `Λ = D(B←A) − D(A←B)`.
- **Assumes.** Solo and composed conditions are comparably scorable. Violated where unscorability is
  treatment-dependent (B alone: 17.5% unscorable).
- **Degenerate.** When the instruction is at ceiling or floor *in isolation*.
- **Strength.** No reference constraint needed; no commensurability assumption; survives target ceiling.

### Candidate 5 — Higher-order interaction · **Secondary**

- **Phenomenon.** Non-additivity: B matters only when S is present.
- **Estimand.** `Γ = [F(A+S+B) − F(A+S)] − [F(A+B) − F(A)]`, count-matched with an inert filler.
- **Evidence.** **+0.312 [+0.188, +0.438]** from a genuine 2×2 with all cells in one matched design.
- **Caveat.** Measured with a colon background. The matched non-boundary control gives near-zero (§D.3), so
  Γ's scope is "backgrounds supplying a clause-boundary resource".

### Candidate 6 — Configuration-indexed surface · **Scope condition**

- **Phenomenon.** Any interaction value is a function of the whole configuration, not of the pair.
- **Evidence.** Three independent sign reversals: order (+0.275 → −0.537), checkpoint (+0.275 → −0.463),
  reasoning budget (τ_control +0.412 → +0.037).
- **Why not an estimand.** It constrains the *scope* of every other estimand rather than defining one. Its
  content is a prohibition: no scalar may be quoted without its configuration.

---

## D. Discriminating evidence

### D.1 The 2×2 factorial: the interaction is at least three-place

*Observation.* Runs `stageR6B_load2` / `load3`, Qwen3-4B-Instruct, 20 tasks, both orders. Recomputation from
raw text reproduces the stored target-failure column to three decimals in every cell.

| Cell | n | A-failure | What it rules out |
|---|---|---|---|
| F(A) — target alone | 40 | 0.000 | — |
| F(A + B) | 120 | 0.000 | Focal identity alone |
| F(A + ctrl) | 120 | 0.000 | Generic load alone |
| F(A + colon) | 120 | 0.013 | Background alone |
| **F(A + colon + B)** | 120 | **0.312** | — |
| F(A + colon + ctrl) | 120 | 0.000 | Load at k=3 |

Count-matched Γ = **+0.312 [+0.188, +0.438]**, cluster bootstrap over 20 tasks. **[Identified]** Favours
Candidate 5 and refutes any two-place reading. Note that the legacy estimand is **exactly 0.000** in the
load-2 cell where a real effect on B is present.

### D.2 Delivery loss: real, directional, but much smaller than one run suggests

*Observation.* Pairing solo and composed cells *within the same run*, across the 21 runs that contain both:

| Instruction | Solo | Composed | Mean loss |
|---|---|---|---|
| Focal **B** | 0.529 | 0.060 | **+0.469** |
| Reference **R** | 0.722 | 0.408 | **+0.314** |
| Target **A** | 1.000 | 0.803 (with B) / 0.965 (with R) | **+0.197** / **+0.035** |

**What holds.** Composition degrades every instruction. The target is the least damaged (loss 0.197 from B,
0.035 from R); the focal is the most damaged (0.469). The ordering is consistent, and the direction — the
target survives, the companion is dropped — matches the four-state result exactly.

**What does not follow.** The reference instruction also loses 0.314. So the asymmetry attributable to
*focal identity* is only about **0.155**, not the 0.517 visible in the single load-2 run highlighted in the
earlier pass. The bulk of B's collapse is shared with a constraint that is supposed to be the null
condition. **Generic compositional load is not ruled out and is the leading rival explanation.** §G.1 is the
test that separates them.

### D.3 The boundary control: the mechanism is specific and the project already tested it

*Observation.* `mechanism_and_focal_repair/boundary_main`: 640 generations, order QAC, load 3, two
backgrounds matched on count, scope and wording — differing only in whether the demanded mark can stand
where a sentence could end. A semicolon can; a degree sign cannot.

| Background | b | τ | Focal uptake (graded) | Mean segments, focal arm |
|---|---|---|---|---|
| degree sign — cannot end a sentence | 0 | +0.100 [+0.025, +0.188] | −0.083 | 3.67 |
| **degree sign** | **4096** | **−0.037 [−0.150, +0.062]** | **+0.202** | **3.92** |
| semicolon — can end a sentence | 0 | +0.688 [+0.537, +0.825] | −0.440 | 2.29 |
| semicolon | 4096 | +0.475 [+0.375, +0.575] | −0.013 | 3.31 |

Δ_boundary = τ(semicolon) − τ(degree) = **+0.588 [+0.438, +0.738]** at b=0 and **+0.512 [+0.375, +0.662]**
at b=4096. "Focal uptake (graded)" is the graded verifier score on the focal rule with the instruction
present, minus the same score on the opposite arm's answers where it is absent — a manipulation check
computable from existing data and computed by no shipped analysis.

**The single most consequential row in the corpus.** **[Identified]** The *only cell in which the focal
instruction is genuinely delivered* — degree background, b=4096, graded uptake +0.202, binary uptake 0.237 —
is also the cell in which **target damage is zero** (τ = −0.037, interval containing zero). Everywhere
target damage is large, graded focal uptake is at or below zero.

**Interpretation.** The mechanism is narrow and now well evidenced: requiring a mark that can serve as a
clause boundary changes how the model realises its sentence structure, and the sentence-count instruction
then fails. The focal instruction's role is to push toward long sentences, which is what makes the mark land
at a boundary. Human adjudication confirms those answers genuinely contain fewer sentences (§A). **This is a
real constraint interaction with an identified mechanism — but it is an interaction between the focal
instruction and a shared surface resource, not between two instructions' semantic demands.**

### D.4 Three sign reversals

Δ = τ(semicolon) − τ(brackets). Order map: 2,560 generations, per-unit seeds; recomputation reproduces all
eight programme cells exactly.

| Reversing variable | Condition 1 | Δ | Condition 2 | Δ |
|---|---|---|---|---|
| **Instruction order** (Qwen3-4B, b=0) | QAC — focal first | +0.275 [+0.013, +0.525] | ACQ — focal last | −0.537 [−0.700, −0.362] |
| **Checkpoint** (QAC, b=0) | Qwen3-4B | +0.275 | SmolLM3-3B | −0.463 [−0.637, −0.287] |
| **Reasoning** (τ_control, QAC) | b = 0 | +0.412 | b = 4096 | +0.037 |

The order reversal is not explained by any positional rule: fourteen partitions were compared and the best
separates one quantity at a ratio of 1.16×. The checkpoint reversal carries a caveat that cannot be analysed
away — SmolLM3's background compliance is 0.125–0.713, so the manipulation frequently did not land.
**[Reverses]** Either way, **the sign of the legacy estimand is not a property of the constraint pair.**

### D.5 The arbitration account tested directly, and refuted

*Observation.* A designed intervention added an explicit priority cue in three levels — prefer A, prefer B,
equal — holding everything else fixed. 960 generations. Define S = P(target only) − P(focal only) and
Ψ = S(A over B) − S(B over A). A working arbitration mechanism predicts Ψ > 0.

- **Result.** All four Ψ intervals contain zero. Three point estimates carry the *wrong* sign (−0.013 to
  −0.113). The one directional effect clearing zero runs against the prediction: at the semicolon with
  reasoning, "prefer B" minus "equal" is **+0.163 [+0.013, +0.312]** — instructing the model to favour the
  focal made the *target* more likely to survive.
- **The null is not inattention.** Reasoning traces mention priority, preference or a trade-off in
  **0.54–0.69** of directed rows against **0.21–0.39** under equal priority. The model reads the cue and
  cannot act on it.

**[Clean null]** This rules out reading the four-state distribution as *arbitration* in any controllable
sense, and with it the framing in which "which constraint the model chooses to sacrifice" is a disposition
that an instruction can address. It does not rule out the redistribution itself, which is observed; it rules
out one mechanism hypothesis for it.

### D.6 Where target damage and joint compliance disagree

*Observation.* On `gemma-4-E4B-it`, switching from no-thinking to natural reasoning raises focal delivery
from 0.19 to 0.89 and joint compliance from ~0.19 to ~0.89 — while τ is **0.000 in all four cells**, because
the target never fails in either arm. On `gemma-4-12B-it`, uptake is 1.000 and joint compliance 1.000: the
pair composes perfectly. On four of five checkpoints, P(X_A) ≈ 1 in both arms.

**[Not identified]** A τ of 0.000 on those checkpoints is produced by construction. Candidate 1 records
nothing; Candidate 3 records a 70-point change. **This is the clearest single case where the choice of
construct changes the scientific conclusion.**

### D.7 The focal-only state, and why no two-sided regime exists

*Observation.* A purpose-built ladder shortened the focal instruction's required chain from three increases
to two to one, on 20 held-out calibration tasks, 720 generations. Recomputation reproduces the report's
table exactly.

Four-state occupancy by focal difficulty, non-boundary (bracket) background, n = 120 per rung:

| Rung | Focal pass | both | target only | focal only | neither |
|---|---|---|---|---|---|
| B — three increases | 0.033 | 0.033 | 0.725 | 0.000 | 0.242 |
| two increases | 0.258 | 0.258 | 0.550 | 0.000 | 0.192 |
| one increase | 0.467 | 0.458 | 0.500 | 0.008 | 0.033 |

**[Holds]** Making the focal instruction fourteen times easier moves all the mass into *both* and none into
*focal only*. The project's own verdict — `NONDEGENERATE_FOCAL_NOT_IDENTIFIED` — is correct and is confirmed
here. Whenever this model can satisfy the focal rule, it can also satisfy the target. There is no regime in
which it must choose, so **a two-sided trade-off construct has no empirical referent in this corpus.**

---

## E. Assessment of the legacy estimand

### What it genuinely answers

τ answers a real and well-posed question: *holding the number of instructions fixed, does putting B in the
focal slot rather than R make the target fail more often, in this configuration?* It is an estimate of the
effect of **presenting** B rather than R — not of satisfying B — and on that reading it is arithmetically
sound. The count-matched design does successfully remove generic load: F(A+ctrl) = F(A) = 0.000 and
F(A+colon+ctrl) = 0.000 establish that directly.

### Assumptions, and where they fail

| Assumption | Where it holds | Where it fails |
|---|---|---|
| Target has headroom in at least one arm | Qwen3-4B with a boundary-capable background | **4 of 5 cross-model checkpoints**; the bracket background at every reasoning budget above zero |
| R is matched to B on realised difficulty | By coincidence in one load-2 run (0.625 vs 0.667) | **Corpus-wide: gap +0.193, sd 0.212**, B harder in 17 of 19 runs |
| The reference arm is a null condition | Load 2, no background | R's own compliance drops 0.314 under composition; on SmolLM3 the reference arm's target failure reaches 0.675, making τ negative |
| The estimate is a property of (A, B) | Nowhere established | **Sign reverses with order and with checkpoint** (§D.4) |
| Damage lands on the target | Boundary-capable backgrounds | Raw generations show cases where attempting B breaks the *background* instead; τ records nothing |

### What it discards

τ is a marginal of the joint outcome. It cannot see: whether the focal instruction was satisfied, whether
joint success occurred, which instruction was sacrificed, or whether the reference arm was itself damaged.
Both facts that replicate across model families in this corpus — low P(both), empty "focal only" — are
invisible to it.

### Classification

**Useful only as a diagnostic or secondary estimand.**

Not "unsuitable": where the target has genuine headroom, the reference is difficulty-matched, and the
configuration is stated, τ answers a legitimate question and the matched-reference design is the right
instrument for it. But those conditions co-occur in a small minority of the corpus, and the quantity's sign
is not stable across two design variables that a benchmark would have to fix arbitrarily. **It cannot carry
the programme's primary claim.**

---

## F. Remaining decision frontier

| Question | Classification | Why the evidence stops here |
|---|---|---|
| **Is the delivery collapse target-specific or generic compositional load?** | Not distinguishable | Composition costs the focal 0.469 and the reference 0.314. No cell composes the focal instruction with a companion that is *not* the target, so the shared component cannot be subtracted. |
| **Does any interaction survive without a boundary-capable background?** | Strongly constrained, unresolved | One matched control exists (degree sign), giving τ = +0.100 at b=0 and −0.037 at b=4096, on one checkpoint and one order. Suggestive of near-zero; a single cell cannot settle it. |
| **Is the phenomenon a pair property or a capability threshold?** | Not distinguishable | gemma-4-12B composes the pair at 1.000; Qwen3-4B at ≤0.23. Only two families have been run on a shared design, and one had a failed manipulation check. |
| **Is the effect a mode of the distribution or an artefact of sampling?** | Not distinguishable | Greedy and T=0.3 runs exist (`stageS1_Tgreedy`, `stageS1_Tt03`) but use a different focal instruction, so they do not bear on the B-versus-R contrast. |
| **Should the primary estimand need a matched reference at all?** | **Settled — no** | Solo baselines exist in 25–34 runs and give each instruction its own counterfactual. The reference is needed for τ, not for Candidate 4. |
| **Is joint satisfaction achievable?** | **Settled — yes** | Hand-authored witnesses pass all three verifiers for every background tested. Low P(both) is a model failure, not a property of the task. Witnesses re-scored and confirmed. |
| **Is the verifier valid?** | **Settled — yes, for segmentation** | 65 of 65 blinded human-adjudicated cases agree with the current segmenter, including all 44 splice-bearing answers. This is the strongest measurement-validity evidence in the repository and it is not cited in the analyses that depend on it. |

---

## G. Minimal next analyses

Ranked by information gain per unit cost. The first three require no new generation.

| # | Test | Competing hypotheses | Discriminating result | Cost |
|---|---|---|---|---|
| **1** | **The focal-with-a-non-target companion cell.** Generate B+R and B+S without the sentence-count instruction, beside the existing B-alone and B-with-A cells. | H1: the target specifically degrades the focal. H2: any composition degrades it. | D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct. < 0.10 supports H2 and **refutes the pairwise framing entirely**, redirecting the programme to a load-and-capacity account. | ~800 generations |
| **2** | **Solo-baseline audit of the reference pool.** Recompute marginal compliance for every constraint ever used as focal, reference or background, from the `primitive` cells already stored. | H1: references are difficulty-matched. H2: they are systematically easier. | Already partly done here: the gap is +0.193. Completing it per-constraint determines whether any existing reference is usable and whether published joint-based numbers must be re-reported. | Re-analysis |
| **3** | **Graded manipulation check on every stored cell.** Compute uptake as the graded score with the instruction present minus the same score on the opposite arm. | H1: the focal is weakly delivered. H2: not delivered at all. | Cells with uptake ≤ 0 cannot support a "competing demands" reading whatever τ says. On present evidence that is *most* cells with a large τ. | Re-analysis |
| 4 | **Boundary control replicated across order and checkpoint.** Repeat the degree-versus-semicolon contrast at ACQ and on a second model family. | H1: near-zero τ without a boundary-capable mark is general. H2: it is a QAC/Qwen3-4B coincidence. | If τ(non-boundary) stays within ±0.10 across orders and models, the phenomenon is *specifically* a shared-surface-resource interaction and the construct should say so. | ~1,280 generations; constraints already registered |
| 5 | **Decoding replication of one canonical cell** at greedy and T=0.3, using the B-versus-R design rather than the semicolon-total design. | H1: the clause-chain strategy is a distributional mode. H2: an artefact of T=0.7. | Chain rate at T=0 under half the T=0.7 rate makes every effect size decoding-conditional. | ~320 generations |
| 6 | **Complete the blinded human audit** to the remaining 132 of 175 sampled cases. | H1: 65/65 agreement generalises. H2: agreement degrades in under-sampled strata. | Below ~0.90 in any stratum would reopen measurement validity, which is currently the programme's strongest link. | Annotation only |

**Assumptions that persist even if all six succeed:** 20 pilot topics shared across nearly every run; one
wording index for almost all runs; a constraint vocabulary built almost entirely on sentence segmentation,
so "constraint interaction" is currently operationalised as "interaction among rules that read the same
segmenter". None of the six addresses that, and it is the largest threat to external validity.

---

## H. Provisional recommendation

### Phenomenon

**Compositional non-composition.** When instructions that address the same surface of the output are
presented together, the model realises a single structure that satisfies some of them and abandons others.
Joint satisfaction is rare, the abandonment is one-sided — the designated target survives, the companion
instruction is dropped — and the magnitude and even the sign of any pairwise summary depend on the full
configuration.

### Construct

The **compliance profile** of a prompt: for every instruction present, the probability it is realised,
measured on its own verifier and referenced to its own solo baseline, reported jointly.

### Primitive outcome

```
X = (X_A, X_B, X_S₁ … X_S_m)   reported with the graded vector   G = (G_A, G_B, G_S₁ … G_S_m)
```

The full joint state. Graded scores are already computed by every verifier and discarded by every shipped
analysis; they carry the manipulation check that decides whether any cell is interpretable.

### Primary estimands — two, not one

**1 · Reciprocal delivery loss.** `D(c ← G) = P(X_c=1 | c alone) − P(X_c=1 | c with G)`, reported for every
instruction, with asymmetry `Λ = D(B←A) − D(A←B)`. Needs no reference constraint, makes no commensurability
assumption, and survives target ceiling. **Conditional on test G.1**: if the generic component dominates,
this becomes a load measure rather than an interaction measure, and should be renamed accordingly.

**2 · Within-arm state redistribution.** The four-state vector `p`, and its change under interventions that
do not alter which instructions are present — reasoning budget, order, decoding, checkpoint. Used *within*
an arm, it avoids the B-versus-R commensurability problem entirely, and it is the only representation in
which the two replicating facts are visible.

### Retained, demoted, rejected

- **Γ, the higher-order interaction** — retained as the secondary estimand of record. It is the
  best-evidenced interaction quantity in the corpus (+0.312 [+0.188, +0.438]) and the only one estimated
  from a complete matched factorial.
- **τ, target damage** — *demoted to secondary diagnostic*, with three mandatory gates: target headroom in
  at least one arm; reference difficulty-matched on measured solo compliance; and the configuration quoted
  with the number.
- **Δ_joint across arms** — *rejected as primary* until the reference pool is difficulty-matched. It cannot
  currently separate "B is harder" from "B conflicts".
- **The matched-reference design** — sound in principle, retained as a control arm, but no longer
  load-bearing. Since the primary estimand uses solo baselines, building the final reference pool ceases to
  be a blocking prerequisite.

### The honest summary of the decision's status

The *primitive* is settled: the joint vector, not target failure. The *demotion* of τ is settled by three
sign reversals and by structural degeneracy on most checkpoints. What is **not** settled is whether the
surviving phenomenon should be called constraint *interaction* at all, or compositional *load* — because the
matched reference loses two-thirds as much delivery as the focal instruction does, and no experiment in the
corpus separates them. **Test G.1 should be run before the construct is fixed.** It is roughly 800
generations and one afternoon.

### Decision table

| Decision | Existing evidence | Current status | What would resolve it |
|---|---|---|---|
| Primitive outcome: joint vector or target failure? | Reasoning moves joint compliance ~70 points with τ = 0.000 in all four cells; P(focal only) ≈ 0 across a 14× focal-difficulty range | **Settled** — joint vector | Nothing further; adopt joint reporting as mandatory |
| Should τ remain the primary estimand? | Sign reverses with order (+0.275 → −0.537) and checkpoint (+0.275 → −0.463); structurally 0.000 on 4 of 5 checkpoints; reference not difficulty-matched (+0.193) | **Settled** — demote to gated diagnostic | Nothing further; a headroom-bearing, difficulty-matched, boundary-safe cell would reinstate it locally |
| Is the interaction two-place or higher-order? | F(A+B) = F(A+ctrl) = 0.000, F(A+colon) = 0.013, F(A+colon+B) = 0.312; Γ = +0.312 [+0.188, +0.438] | **Settled** — at least three-place | Nothing further for existence; scope needs test G.4 |
| Is the phenomenon interaction or generic load? | D(focal) = +0.469, D(reference) = +0.314 across 21 runs; asymmetry only +0.155 | **Not distinguishable** | **Test G.1** — compose the focal instruction with a non-target companion |
| Does the effect need a boundary-capable background? | Matched control: τ = +0.100 (b=0), −0.037 (b=4096); Δ_boundary = +0.512 [+0.375, +0.662] | **Strongly constrained, unresolved** | **Test G.4** — replicate the control across order and model family |
| Is the four-state pattern arbitration? | Priority intervention: all four Ψ intervals contain zero, three wrong-signed; "prefer focal" made the target survive (+0.163); cue read in 0.54–0.69 of rows | **Settled** — not arbitration | Nothing further; the redistribution stands, the mechanism hypothesis does not |
| Does a two-sided trade-off regime exist? | Focal-only occupancy 0.000 / 0.000 / 0.008 across three difficulty rungs on held-out tasks; project verdict `NONDEGENERATE_FOCAL_NOT_IDENTIFIED`, reproduced exactly | **Settled** — no, in this corpus | Publish as a negative result; a harder target or a different constraint family would be a new search, not a re-analysis |
| Is the segmentation measurement valid? | 65 of 65 blinded human-adjudicated cases match the current segmenter, including 44 splice-bearing answers | **Settled** — valid | Complete the remaining 132 sampled cases to confirm across strata (test G.6) |
| Which datasets may be quoted? | Only the arbitration programme has per-unit seeding (0/192 identical pairs); earlier rounds ~98% duplicates; one committed analysis table is built entirely from DEPRECATED and FOREIGN sources | **Settled** — restrict, and regenerate that table | Re-seed any dataset whose intervals will be quoted; rebuild `reasoning_rows.csv` from the canonical file |

---

**Scope note.** This pass concerns the scientific definition only. Verifier architecture, the final
reference pool, the confirmatory protocol, effect-size estimation and cross-model campaigns are downstream.
The construct decision changes two of them materially: the reference pool ceases to be a blocking
prerequisite, and every future design must include an `instruction alone` cell for each instruction it uses.
