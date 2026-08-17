# What DCI Should Actually Measure

**Construct diagnosis — pass 1 · exploratory, no confirmatory claims · 14 August 2026**

Evidence base: 4 git worktrees, ~35k stored generations. All headline numbers independently
recomputed from raw text.

---

> **SUPERSEDED IN PART.** The central claim of §6.1 below — that the headline semicolon effect is
> substantially a *segmentation-convention artefact* — was **retracted** in the follow-up pass
> (`dci-construct-pass2.md`, §A). Two blinded human audits in `exploratory/verifier_audit/` show the
> shipped segmenter matches human sentence counts on **65 of 65** adjudicated cases, including all 44
> splice-bearing answers; the alternative convention used below matches on **0 of 44**. The arithmetic
> sensitivity documented in §6.1 is real and still worth knowing. The interpretation placed on it was
> not. §5.2's delivery-asymmetry figure (+0.517) is also corrected in pass 2 to **+0.155** once the
> whole corpus is pooled rather than one run. Everything else below stands and was reconfirmed.
> This file is retained as a record of the revision.

---

A re-examination of the constraint-interaction construct from the stored generations, verifier code and
run manifests — not from the write-ups. The phenomenon is real, but the quantity the programme has been
estimating is not the one that carries it.

**Evidence classes used throughout.** *Observation* = recorded in the data. *Measurement* = produced by
a verifier. *Identification* = what the contrast can support. *Interpretation* = reading of the pattern.
*Hypothesis* = not yet tested. *Recommendation* = proposed decision.

Every empirical statement was recomputed from the stored raw generations using the project's own
verifier registry, unless explicitly marked as resting on prose.

---

## 1. Bottom line

> There is a real, large, directional constraint-interaction phenomenon in this corpus. It is *not* the
> one the historical estimand measures. In the single cleanest experiment, the historical target-damage
> contrast reads exactly `0.000` while the phenomenon is present at `+0.52`.
>
> *(Corrected in pass 2: the pooled asymmetry is +0.155, not +0.52.)*

### What appears to be the phenomenon

**Composition degrades the delivery of individual constraints, asymmetrically, and the loss lands on
whichever constraint is not carrying the model's chosen surface strategy.**

Two instructions that a model can each follow reasonably well on their own become, when placed in the
same prompt, a situation in which one is followed and the other is largely abandoned. Which one survives
is not predictable from how hard each is alone. In the sharpest case measured here, the two competing
instructions were *almost exactly equally difficult in isolation* — 0.667 versus 0.625 — yet composing
each with the target left one untouched and destroyed the other.

The phenomenon is therefore about **reciprocal delivery under composition**, not about damage to a
designated target.

### What remains unresolved

- **Whether a large part of the historical signal is a measurement-convention artefact.** *(This is the
  claim retracted in pass 2.)*
- **Whether any regime exists where both constraints are genuinely in play.** On present evidence,
  essentially none. The project's own held-out calibration reached the same verdict independently (§8).
- **Whether the asymmetry generalises beyond one constraint pair on one checkpoint.** Untested. It rests
  on a single 2×2 factorial (§6).

### What DCI should provisionally measure

The primitive outcome should be the **full joint compliance vector** over all instructions present, not
target failure. The primary estimand should be a **reciprocal delivery-loss contrast** comparing each
constraint's compliance when composed against its compliance when presented alone — a
difference-in-differences on delivery, with the constraint's own solo rate as its baseline.

The historical `τ(B→A)` target-damage contrast should be **demoted to a secondary diagnostic**. It is not
wrong; it is blind in exactly the regimes this corpus occupies. The matched-reference design remains
sound in principle but is currently matched on the wrong quantity (§7).

---

## 2. Empirical reality

### 2.0 Where the evidence lives, and one provenance failure

The primary working directory `/home/cnm13ryan/git/dci` contains **no raw generations at all**:
`exploratory/runs/` is git-ignored and absent from disk. The generations exist in three sibling *git
worktrees* of the same repository — `dci-cheapest-rocm-study` (201 MB, 69 runs),
`dci-natural-reasoning-headline` (120 MB, 62 runs) and `dci-cross-model` (45 MB, 43 runs).

#### The committed row-level reasoning table is built entirely from data the project itself classifies as unusable

*Observation.* `exploratory/figures/reasoning_compute/data/reasoning_rows.csv` is tracked in git (commit
`cba7c8d`) and is the row-level input to the reasoning-compute figures. Matching every one of its 1,440
rows against the raw generation files by exact answer text:

| Budgets in the table | Source file it actually matches | Text match | Manifest status | Duplicate replicate pairs |
|---|---|---|---|---|
| 0, 256, 512, 1024, 4096 | `s18_reasoning.jsonl` | 1.000 | **DEPRECATED** | 0.975 |
| 320, 384, 448, 640 | `s18_transition.jsonl` | 1.000 | **FOREIGN** | 0.984 |
| — | `s18_reseeded.jsonl` (the replacement) | 0.000 | **CANONICAL** | 0.000 |

"Duplicate replicate pairs" is the fraction of nominal replicate pairs whose two answers are
byte-identical, because one shared seed was used for all 160 requests. The project's own
`CANONICAL_RUN_MANIFEST.json` records this and says the deprecated file is "retained, never loaded". It is
loaded. Effective independent sample size in that table is roughly half its nominal *n*, and its bootstrap
intervals are correspondingly too narrow. **Only the canonical files are used below.**

### 2.1 The experimental object

One constraint family dominates the corpus. Read from the stored prompts, not from documentation:

| Slot | Instruction |
|---|---|
| **A** — target | "Write exactly 4 sentences." |
| **B** — focal | "Make each sentence strictly longer than the preceding sentence when measured by word count." |
| **R** — matched reference (`C_L3`) | "Begin every sentence with a word whose first letter is S." |
| **S** — background | "Use exactly 1 semicolon…" / "Use exactly 1 pair of round brackets… and place it wherever you judge best." |

*Observation.* **A, B and R are all computed from one shared primitive.** The verifier `split_sentences`
segments the answer at `[.!?]` followed by whitespace, and at newlines. A counts those segments; B compares
word counts across them; R checks their initial letters. Nothing separates the three measurements from a
single segmentation decision. This is the root of most of what follows.

### 2.2 The observations that constrain any definition

1. **Treatment delivery is extremely asymmetric.** Across the canonical reasoning grid, P(B satisfied) runs
   0.00–0.15 while P(R satisfied) runs 0.43–0.95.
2. **But B and R are nearly equally hard on their own** — 0.667 versus 0.625 *(in the one run examined;
   corrected corpus-wide in pass 2 to 0.529 vs 0.722)*.
3. **The target is at ceiling almost everywhere.** On four of five cross-model checkpoints, and in the
   bracket background at every reasoning budget above zero, P(A satisfied) ≈ 1 in both arms.
4. **A clean higher-order interaction exists.** Neither B alone nor a colon background alone damages A;
   together they produce 31% target failure.
5. **The background is not a nuisance.** A semicolon or colon requirement changes what "a sentence" means,
   and it does so differently in the two arms.
6. **Interventions move joint compliance while leaving target failure fixed.** On one checkpoint, turning
   reasoning on moves joint compliance from 0.19 to 0.89 with τ = 0.000 in both conditions.
7. **The "focal only" state barely exists.** Under the convention-safe background, it occupies 0.000–0.008
   of rows across a deliberately-graded difficulty ladder.
8. **Missingness is treatment-dependent** in the newest cross-model dataset — up to a 20-point spread in
   answer rate between arms.

---

## 3. Primitive outcome space

For a prompt containing instructions `c₁…c_k`, write `X_c ∈ {0,1}` for realised compliance with instruction
`c`, and `G_c ∈ [0,1]` for the verifier's graded score on the same instruction. The complete behavioural
outcome is the vector `X = (X_A, X_B or X_R, X_S₁ … X_S_m)`.

| Variable | Meaning | How obtained | Status | Reliability / caveat |
|---|---|---|---|---|
| `X_A` | Target satisfied: exactly 4 segments | `v_exact_sentence_count` over `split_sentences` | Derived | Convention-dependent whenever the prompt requires a boundary-capable mark (§7). *Pass 2: the convention is human-validated.* |
| `X_B` | Every adjacent segment pair strictly increases in words | `v_increasing_lengths` | Derived | Unscorable below 2 segments — and unscorability is treatment-dependent (17.5% when B is presented alone, 0% when composed with A). |
| `X_R` | Every segment starts with "S" | `v_sentence_initial` | Derived | Reliable; shares the segmenter but is insensitive to segment count. |
| `X_S` | Background mark count correct | character-stream counters | Derived | Reliable. Never reads the segmentation. |
| `G_c` | *Graded* score: fraction of adjacent pairs increasing, fraction of segments starting with S, etc. | `VerificationResult.continuous_score` | Derived | **Computed by every verifier and discarded by every shipped analysis.** The single most useful unused observable in the repository. |
| segments, splices | Terminal-delimited segment count; count of semicolons/colons standing where a sentence could end | `split_sentences`, `splice_count` | Derived | Reliable and instruction-independent. |
| final answer present | Non-empty answer channel | recorded at generation | Observed | **Treatment-dependent** in the newest cross-model export: 19.2% missing overall, arm spreads up to 20 points. |
| technical failure | Backend/capacity/parse outcome | `Outcome` enum, recorded | Observed | Well designed. Non-behavioural outcomes explicitly excluded from scoring. |
| reasoning tokens, cap hit, natural closure | Realised reasoning; whether the budget bound | recorded at generation | Observed | Reliable, but **post-treatment**. Assigned budget is the treatment. |
| task, replicate, order, load, model, revision, backend | Design and execution identity | recorded per row | Observed | Reliable and unusually complete — chat-template SHA is recorded per row. |

**Behavioural state versus measurement procedure.** *Observation.* These are not the same object here. A
model can write four discourse units, believe it has written four sentences, say so explicitly in its
reasoning trace, and be scored as having written three — because one of its boundaries was a semicolon.
`X_A` is a measurement, not the behavioural state. §7 quantifies how far apart they are. *(Pass 2: the
human audit shows the measurement is the correct one; the model's belief is wrong.)*

---

## 4. Candidate phenomena and constructs

### Candidate A — Target-specific damage · **Demote**

- **Phenomenon.** Changing one instruction changes compliance with a designated target.
- **Primitive.** `X_A` only.
- **Estimand.** `τ = P(X_A=0 | A+B+S) − P(X_A=0 | A+R+S)`
- **Treatment.** Identity of the focal-slot instruction, B versus R.
- **Unit.** Task; paired over tasks, cluster-bootstrapped.
- **Assumes.** R is matched to B on everything except the property of interest — including *realised
  difficulty*, which is never checked.
- **Degenerate when.** A is at ceiling or floor; B is not taken up; the damage lands on S rather than A;
  the target's measurement is convention-dependent.
- **Excludes.** Everything about what happened to B, R or S.

### Candidate B — Joint satisfaction loss · **Reject as primary**

- **Phenomenon.** Substituting one instruction for another changes the probability that everything is
  satisfied at once.
- **Primitive.** `X_A ∧ X_slot`.
- **Estimand.** `Δ_joint = P(X_A=1, X_B=1 | A+B+S) − P(X_A=1, X_R=1 | A+R+S)`
- **Assumes.** Far more than is recognised: that `X_B` and `X_R` are commensurable outcomes. They are
  different predicates on different texts.
- **Degenerate when.** Never structurally — which is the problem. It returns a large number whenever B is
  simply harder than R, with or without any interaction.
- **Excludes.** Any separation of "B is hard" from "B and A conflict".

### Candidate C — Redistribution among joint states · **Keep as reporting layer**

- **Phenomenon.** Substituting the focal instruction moves probability mass between the four ways two
  instructions can come out.
- **Primitive.** The vector `p = [P(0,0), P(0,1), P(1,0), P(1,1)]`.
- **Estimand.** `ρ = p_focal − p_reference`, a 4-vector summing to zero.
- **Strength.** Retains the distinction between "sacrificed A", "sacrificed the other", "kept both", "lost
  both" — which τ destroys. Empirically far more convention-stable than τ.
- **Degenerate when.** States are unoccupied. In this corpus "focal only" is empty under the safe
  background, so ρ collapses to a two-state contrast.
- **Limit.** Inherits Candidate B's commensurability problem: ρ is dominated by the B-versus-R difficulty
  gap unless that gap is separately controlled.

### Candidate D — Trade-off between two delivered constraints · **Right idea, wrong operationalisation**

- **Phenomenon.** Interaction is only meaningful where both instructions are genuinely in play.
- **Problem.** "Delivered" has been read as *satisfied*. That is wrong. In the largest measured effects the
  focal instruction is unsatisfied in 90% of rows and is nevertheless demonstrably driving behaviour.
- **Repair.** Define delivery as a *graded manipulation check*: `U_c = E[G_c | c present] − E[G_c | c
  absent]`, using the opposite arm as the absent condition. Computable from existing data today.
- **Status.** Delivery is an **identification condition**, not part of the construct. A treatment can act
  without being satisfied.

### Candidate E — Configuration-dependent interaction surface · **True but not an estimand**

- **Phenomenon.** The effect is a function `f(B, A, S, π, k, r, m)` over background, order, load, reasoning
  and checkpoint; a single τ is one slice.
- **Evidence.** Overwhelming. The same design gives τ = 0.000 and τ = +0.625 at different reasoning budgets
  under the same background, and 0.000 versus +0.400 across backgrounds.
- **Why not primary.** It describes the *scope* of any estimand rather than defining one. Its real content
  is a warning: no scalar generalises across configurations, so the operating point must be part of the
  claim.

### Candidate F — Higher-order (non-additive) interaction · **Strong secondary**

- **Phenomenon.** Neither instruction damages the target alone; together they do.
- **Estimand.** `Γ = [F(A+S+B) − F(A+S)] − [F(A+B) − F(A)]`, count-matched by using an inert filler in
  place of B.
- **Evidence.** The best-supported interaction quantity in the corpus: **+0.312 [+0.188, +0.438]** from a
  genuine 2×2 with all four cells run in one matched design.
- **Limit.** Still expressed in target failure, so it inherits the convention problem of §7 whenever S is a
  boundary-capable mark — which, in the one run available, it is.

### Candidate G — Reciprocal delivery loss under composition · **The one the data forced**

*Recommendation.* No candidate in the brief captures what the factorial data actually show.

- **Phenomenon.** Placing instruction `c` alongside a context `G` reduces the model's compliance with `c`
  itself, relative to presenting `c` alone. The scientific object is that loss, measured for every
  instruction in the prompt, on its own verifier, against its own solo baseline.
- **Construct.** For instruction `c` and context set `G`:

  ```
  D(c ← G)  =  P(X_c = 1 | c alone)  −  P(X_c = 1 | c together with G)
  ```

- **Directional interaction** for a pair is the reciprocal pair `(D(A←B), D(B←A))`, and empirical asymmetry
  is `D(B←A) − D(A←B)` — a quantity *defined* reciprocally, so directionality is measured rather than
  assumed by choosing a target.
- **Why it survives where τ fails.** Each constraint is compared with itself, not with a reference
  constraint. This removes the commensurability assumption entirely, removes the need for a matched
  reference in the primary estimand, and stays informative when the target is at ceiling.
- **Degenerate when** a constraint is at ceiling or floor *in isolation*, or when solo and composed
  conditions are not comparably scorable.

---

## 5. Evidence for and against each candidate

### 5.1 The decisive case: the 2×2 factorial

*Observation.* Runs `stageR6B_load2` and `stageR6B_load3`, Qwen3-4B-Instruct-2507, 20 pilot tasks, both
instruction orders, n = 40–120 per cell. This is the only design in the corpus that runs the target alone,
each constraint alone, and the compositions, in one matched setting. My recomputation from the raw
`response` text reproduces the stored `a_failure` column to three decimals in every cell.

| Cell | n | A-failure | Reading |
|---|---|---|---|
| F(A) — target alone | 40 | 0.000 | No headroom at all |
| F(A + B) | 120 | 0.000 | Focal alone does nothing to the target |
| F(A + ctrl) | 120 | 0.000 | Load alone does nothing |
| F(A + colon) | 120 | 0.013 | Background alone does nothing |
| **F(A + colon + B)** | 120 | **0.312** | Together: substantial failure |
| F(A + colon + ctrl) | 120 | 0.000 | Not a load effect |

Count-matched interaction `Γ = +0.312, 95% CI [+0.188, +0.438]`, cluster bootstrap over 20 tasks. This is
**Candidate F** in its purest form and is the strongest evidence in the repository that the relevant object
is non-additive.

### 5.2 The same experiment refutes Candidate A

The `primitive` condition presents each constraint *entirely alone* — verified from the stored prompts,
e.g. `"Describe why potholes form after a cold winter.\n\nSatisfy every constraint below simultaneously:\n1.
Make each sentence strictly longer…"`.

| Constraint | Alone | Composed with the other | Delivery loss D |
|---|---|---|---|
| **A** — exactly 4 sentences | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | +0.000 |
| **B** — increasing lengths | 0.667 [0.515, 0.818] | 0.150 [0.075, 0.237] | **+0.517** |
| **R** — sentence-initial S | 0.625 [0.475, 0.775] | 0.650 [0.537, 0.750] | −0.025 |

> **Corrected in pass 2.** This is a single run (load 2, no background) and is an outlier. Pooled over the
> 21 runs containing both solo and composed cells, D(B) = +0.469 and D(R) = +0.314 — an asymmetry of
> **+0.155**, not +0.517.

Three things follow *as stated in this pass*:

1. **B and R are matched on marginal difficulty** — 0.667 versus 0.625, overlapping intervals. *(Pass 2:
   corpus-wide the gap is +0.193 and B is harder in 17 of 19 runs.)*
2. **The asymmetry is real and directional.** Adding B costs A nothing (0.000). Adding A costs B 52 points.
3. **τ is exactly blind to it.** F(A+B) = F(A+ctrl) = 0.000, so `τ = 0.000` with a zero-width interval,
   while `D(B←A) = +0.517`.

**Robustness of the reciprocal result**

- *Missingness.* B-alone has 17.5% unscorable rows (answers under two segments). Counting every one as a
  failure gives B-alone = 0.550 and `D(B←A) = +0.400`. The finding survives the worst case.
- *Comparison-count confound, and it runs the wrong way.* B-alone answers average 4.83 segments, so B must
  win ~3.8 adjacent comparisons; composed with A they average exactly 4.00 segments, so only 3. B succeeds
  *more* often in the harder condition.
- *Order.* Both instruction orders were run. B-with-A is 0.175 and 0.125 across the two orders.

### 5.3 Where Candidate B breaks

*Identification.* `Δ_joint` compares `P(X_A ∧ X_B)` against `P(X_A ∧ X_R)`. In the natural-reasoning corpus
this returns `ρ_both = −0.825` (bracket) and `−0.775` (semicolon). But it is dominated by the term
`P(X_R) − P(X_B) ≈ 0.825`. It would return almost exactly the same number if B were simply a harder
instruction with no interaction whatsoever. **It cannot separate difficulty from interaction.**

### 5.4 Where τ is not merely blind but misleading

*Observation.* Canonical reasoning grid, five budgets, two backgrounds, n = 40 per cell. Under the bracket
background at every budget ≥ 512, P(X_A) = 0.975–1.000 in *both* arms, so τ ∈ [−0.025, 0.000]. In the same
cells, the focal instruction is satisfied 0.10–0.15 of the time against the reference's 0.90–0.93. A reader
given τ alone would conclude the configuration is benign; the joint outcome differs by 75 points.

### 5.5 The intervention that moves everything except τ

Cross-model NO-THINKING / NATURAL runs, n = 80 per model × background, recomputed from
`runs/xm_main_*/generations.jsonl`.

| Checkpoint · condition | Background | P(X_A) focal | τ | Focal uptake | Ref uptake | ρ_both |
|---|---|---|---|---|---|---|
| gemma-4-E4B-it · no thinking | bracket | 1.000 | 0.000 | 0.200 | 1.000 | −0.800 |
| **gemma-4-E4B-it · natural reasoning** | bracket | 1.000 | 0.000 | 0.900 | 1.000 | −0.100 |
| gemma-4-E4B-it · no thinking | semicolon | 1.000 | 0.000 | 0.175 | 1.000 | −0.825 |
| **gemma-4-E4B-it · natural reasoning** | semicolon | 1.000 | 0.000 | 0.875 | 1.000 | −0.125 |
| gemma-4-12B-it · no thinking | bracket | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| Qwen3.5-4B · no thinking | bracket | 1.000 | 0.000 | 0.175 | 1.000 | −0.825 |
| Qwen3.5-9B · no thinking | semicolon | 0.900 | −0.150 | 0.275 | 1.000 | −0.550 |

On one checkpoint, turning reasoning on raises focal delivery from 0.19 to 0.89 and lifts joint compliance
by ~70 points. **τ = 0.000 in all four of those cells.** Note also gemma-4-12B-it: uptake 1.000, joint
1.000, ρ = 0.000 — a checkpoint that simply *composes the pair successfully*. The constraint pair is not
intrinsically incompatible.

### 5.6 Where Candidate D's naive form fails

*Measurement.* A graded manipulation check, built by scoring each arm's answers against *both* slot
constraints — so the opposite arm supplies the "instruction absent" baseline.
`U_c = E[G_c | c present] − E[G_c | c absent]`.

| Background | Budget | B off | B on | U_B | U_R |
|---|---|---|---|---|---|
| bracket | 0 | 0.400 | 0.369 | −0.031 | +0.801 |
| bracket | 512 | 0.300 | 0.517 | +0.217 | +0.919 |
| bracket | 4096 | 0.306 | 0.521 | +0.215 | +0.919 |
| bracket | natural | 0.375 | 0.550 | +0.175 | +0.950 |
| **semicolon** | 0 | 0.533 | 0.183 | **−0.350** | +0.781 |
| **semicolon** | 512 | 0.417 | 0.346 | **−0.071** | +0.938 |
| **semicolon** | 4096 | 0.429 | 0.375 | **−0.054** | +0.942 |
| **semicolon** | natural | 0.408 | 0.483 | +0.075 | +0.944 |

*Observation.* The reference instruction is delivered overwhelmingly (U_R ≈ +0.78 to +0.95) in every cell.
The focal instruction is weakly delivered under the bracket background (+0.18 to +0.22) and **negatively
delivered under the semicolon background**: instructing "make each sentence longer" produces answers whose
length ordering is *worse* than answers where that instruction was absent. A treatment with negative
measured uptake cannot support the interpretation "the demands of B compete with A".

---

## 6. Construct collisions in the current design

### 6.1 The dominant collision: the target's measurement is not background-independent

> **This section's interpretation is retracted in pass 2.** The arithmetic below is correct; the inference
> that the shipped convention is one of two equally defensible readings is not. Human adjudication favours
> the shipped convention 65/65.

*Observation.* The segmenter splits at `[.!?]` and at newlines. It does *not* split at a semicolon or
colon. So when the background instruction requires exactly one semicolon, every answer contains a mark
whose boundary status is ambiguous — and the target constraint is defined by counting boundaries.

*Measurement.* Recomputing the natural-reasoning endpoint (160 rows) under two conventions: the shipped
one, and one that additionally counts a boundary-standing semicolon as a sentence boundary.

| Background | Terminals only (shipped) | Semicolon counts as a boundary | Either reading (lenient) |
|---|---|---|---|
| bracket | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| **semicolon** | **+0.400 [+0.225, +0.550]** | **−0.225 [−0.350, −0.100]** | **+0.200 [+0.075, +0.325]** |

The shipped value reproduces the project's `SCIENTIFIC_CLAIM_AUDIT.md` §1.2 exactly, as do the ρ vectors.

**How far apart the conventions are**

| Cell | Rows where the conventions disagree |
|---|---|
| Focal arm, semicolon bg | **30 of 40** |
| Reference arm, semicolon bg | **39 of 40** |
| Either arm, bracket bg | **0 of 80** |

Under the semicolon background, 80% of focal answers and 100% of reference answers read as exactly four
sentences under *one* convention — but only 5% and 2.5% under *both*. Of the 20 measured target failures in
the focal arm, **12 are answers containing exactly four clause units in which one boundary was written as a
semicolon**.

**The models say what they are doing.** *Observation.* Reasoning traces from both arms, semicolon
background, same task:

- *Focal arm* — "The first sentence is 20, second 32, third 44, fourth 56. The semicolon is in the third
  sentence. That should satisfy all the requirements." The verifier scores three segments and a decreasing
  sequence: **both A and B recorded as failures**.
- *Reference arm* — "So the answer should be four sentences, each starting with S, one semicolon in the
  third sentence." It places the semicolon *inside* a segment. The verifier scores four segments: **both A
  and R recorded as passes**.

*Interpretation (retracted).* Both models are producing four discourse units and are internally consistent.
B drives the model toward long sentences, and a long sentence containing a semicolon is exactly the
ambiguous case; R drives it toward short sentences, where the semicolon lands harmlessly inside one.

**The same collision across an entire 5 × 6 grid.** Runs `stageR6A_N2…N6` cross target sentence count
N ∈ {2…6} with demanded semicolon count q ∈ {1…6}, n = 80 per cell.

P(the whole answer is a single terminal-delimited sentence). Rows q, columns N:

| q ↓ / N → | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| 1 | 0.812 | 0.025 | 0.000 | 0.000 | 0.000 |
| 2 | 0.350 | 0.512 | 0.087 | 0.050 | 0.013 |
| **3** | **0.775** | **0.713** | **0.963** | **0.925** | **0.575** |
| **4** | **0.975** | **0.700** | **0.963** | **1.000** | **0.938** |
| **5** | **0.988** | **0.812** | **1.000** | **1.000** | **0.988** |
| **6** | **0.988** | **0.863** | **0.963** | **1.000** | **1.000** |

*Interpretation.* This is a **regime switch, not a gradient**, with threshold at q ≈ 3 almost independently
of N. Counting segments plus boundary-standing semicolons, total clause units track `N + q` for q ≤ 2 and
`q + 1` for q ≥ 3. Below the threshold the model writes N sentences and tucks the semicolons inside them;
above it, it writes one sentence of q semicolon-joined clauses. A raw generation at N=4, q=4:

> "A stapler binds sheets of paper by driving a metal staple through the edges with a spring-loaded
> mechanism; this holds the papers together securely; the staple is typically inserted at a 90-degree angle
> to the surface; (each sheet is aligned and pressed firmly before the staple is fired)."

— four clauses, one segment.

*Observation.* This also resolves a question the repository's own `EXPERIMENT_COVERAGE_MATRIX.md` records
as **UNIDENTIFIED and "the highest-priority gap in the programme"**: whether the threshold is absolute in q,
a ratio q/N, or the boundary q = N. The R6A runs cross free q with N and were evidently made after that
matrix was written. The answer is *approximately absolute in q*: collapse at q = 3 occurs at N = 5 and
N = 6, where q < N and q/N ≤ 0.6.

### 6.2 The remaining collisions

| Component | Which contrast contains it | Why τ cannot separate it | What would |
|---|---|---|---|
| Focal identity vs generic load | A+B+S vs A+R+S | Partly solved: the matched reference does hold instruction count fixed, and F(A+ctrl) = 0.000 confirms load alone is inert here. | Already adequate. Keep the count-matched filler. |
| **Reference identity / realised difficulty** | A+B+S vs A+R+S | R is matched on wording and slot but not on solo compliance. | Measure each candidate reference's solo rate and match on it explicitly. |
| Realised uptake | every arm contrast | τ conditions on assignment, not delivery. Uptake ranges 0.075–1.000 across cells. | The graded manipulation check U_c of §5.6, reported as a gate. |
| Target headroom | every arm contrast | τ ≈ 0 is produced by construction when P(X_A) ≈ 1 in both arms — 4 of 5 checkpoints. | Estimands that do not use A as the outcome; solo-baselined delivery loss. |
| Background-induced target damage | A+S vs A | Only estimable where the S-alone cell was run. It was, in R6B: F(A+colon) = 0.013. | Always run the A+S cell. Cheap. |
| Background-gated focal damage | the Γ interaction | Estimable and estimated: +0.312. But confounded with 6.1 whenever S is boundary-capable. | Repeat Γ with a non-boundary-capable background. |
| **Segmentation convention** | any contrast where S demands a boundary-capable mark | Sign-reversing (§6.1). | Report every target estimate under both conventions. *(Pass 2: the human audit settles which convention is correct.)* |
| Post-treatment selection | THINKING_ENABLED_BOUNDED cross-model export | 19.2% of rows produce no answer, with up to 20-point arm spreads. Rows that finish are selected on success. | Report answer rate per cell as a gate. Already documented correctly in `ACTUAL_CROSS_MODEL_DCI_RESULTS.md`. |
| Measurement error | all | Small: the project audited a verifier repair across 25,290 answers and found 0 sentence-count changes. | Nothing needed. |

---

## 7. Informative regimes already present in the data

> **No configuration in the corpus satisfies the necessary conditions.** The project reached the same
> conclusion independently, on held-out data, and stopped — correctly.

### 7.1 The project's own calibration

*Observation.* Run `mechanism_and_focal_repair/focal_calibration`: a graded ladder of focal difficulty
(B → three increases; `X_B_INC2` → two; `X_B_INC1` → one), on 20 held-out calibration tasks disjoint from
all evaluation tasks, 720 generations. My recomputation reproduces its four-state table exactly.

| Background | Rung | both | target only | focal only | neither | P(X_A) shipped | P(X_A) alt convention |
|---|---|---|---|---|---|---|---|
| bracket | B (hardest) | 0.033 | 0.725 | 0.000 | 0.242 | 0.758 | 0.758 |
| bracket | X_B_INC2 | 0.258 | 0.550 | 0.000 | 0.192 | 0.808 | 0.808 |
| bracket | X_B_INC1 (easiest) | 0.458 | 0.500 | 0.008 | 0.033 | 0.958 | 0.958 |
| **semicolon** | X_B_INC1 | 0.725 | 0.050 | 0.158 | 0.067 | 0.775 | 0.283 |

Under the bracket background, making the focal instruction fourteen times easier moves all the mass into
*both* and none into *focal only* (0.000 → 0.000 → 0.008). Quoted from the project's own report and
confirmed by recomputation: *"Under the parenthetical background, A and B do not compete… whenever this
model can satisfy the length ordering, it can also write four sentences."*

### 7.2 Scoring the corpus against the nine conditions

| Requirement | Bracket bg, Qwen3-4B | Semicolon bg, Qwen3-4B | Kimi-VL, bracket | Kimi-VL, semicolon |
|---|---|---|---|---|
| 1. Target has headroom | ✗ ceiling ≥512 | ✓ 0.28–0.55 | ✗ 0.946 | ✓ 0.441 |
| 2. Focal uptake substantial | ✗ 0.10–0.15 | ✗ 0.05–0.10 | ~ 0.405 | ✗ 0.088 |
| 3. Comparable reference uptake | ✗ 0.90 vs 0.13 | ✗ 0.93 vs 0.08 | ✓ 0.531 vs 0.405 | ✗ 0.571 vs 0.088 |
| 4. All four states achievable | ✗ focal-only 0.000 | ~ focal-only 0.05 | ✗ 3 of 4 | ✓ 4 of 4 both arms |
| 5. Outcome measurement reliable | ✓ convention-invariant | ✗ sign-reversing | ✓ | ✗ sign-reversing |
| 6. Missingness low / non-differential | ✓ 0% | ✓ 0% | ✗ 8–20% differential | ✗ differential |
| 7. Genuine replicate variation | ✓ canonical files only | ✓ | ✓ | ✓ |
| 8. Reproducible across tasks/seeds | ~ one base seed throughout | ~ one base seed | ~ | ~ |
| 9. Not verifier/execution-dominated | ✓ | ✗ | ~ transformers backend | ✗ |

**The structural bind.** *Identification.* The corpus contains exactly two kinds of cell. Where the target
measurement is trustworthy (bracket background), **the constraints do not compete**. Where the constraints
appear to compete (semicolon or colon background), **the target measurement is not convention-stable**.

*Hypothesis (retracted in pass 2).* The programme may have been studying its own segmentation convention.

**This is an important negative result and should be reported as one.** It should not be dissolved by
relaxing a condition after seeing which cell passes.

### 7.3 The one thing that does survive

*Identification.* The R6B factorial's *reciprocal delivery* result (§5.2) is not subject to either horn. It
uses the mark-free load-2 condition where the segmenter is unambiguous (P(X_A) = 1.000, mean segments
exactly 4.00), it compares each constraint against its own solo baseline, and it survives the worst-case
treatment of missingness.

---

## 8. Critical unresolved questions

1. **Is the reciprocal delivery collapse specific to the target, or does any second instruction do it?**
   There is no cell in the corpus composing B with a *non-target* instruction. *This is the single most
   important gap.*
2. **Does the interaction survive a non-boundary-capable background?** The registry already contains matched
   marks that cannot stand at a boundary (`X_DEGREE_FREE`, `X_ASTERISK_FREE`, brackets). *(Pass 2: this
   experiment already exists — `boundary_main`.)*
3. **Which segmentation convention is correct?** *(Pass 2: settled — the shipped one, 65/65.)*
4. **Is the asymmetry a property of the constraint pair or of the checkpoint?** gemma-4-12B-it composes A
   and B at 1.000/1.000. Qwen3-4B-Instruct cannot.
5. **Is the clause-chain strategy a mode of the distribution or an artefact of sampling?** Every generation
   is at T = 0.7, top-p 0.9. *(Pass 2: greedy and T=0.3 runs exist but use a different focal instruction.)*

---

## 9. Minimal discriminating analyses and experiments

| # | Test | Competing hypotheses | Decision rule | Cost |
|---|---|---|---|---|
| **1** | **Dual-convention re-scoring of every stored estimate.** | H1: effects are behavioural. H2: effects are convention artefacts. | Any estimate whose sign or zero-exclusion flips is reclassified `CONVENTION_DEPENDENT`. | Re-analysis, hours |
| **2** | **Graded manipulation check on every stored cell.** | H1: focal is delivered weakly. H2: focal is not delivered, or anti-delivered. | Cells with U_focal ≤ 0 cannot support a "constraint competition" reading. | Re-analysis, hours |
| 3 | **Solo-baseline census.** Extract the `primitive` condition wherever it was run. | H1: B and R are matched on difficulty. H2: the reference is systematically easier. | If solo rates differ by > 0.15, every joint-based estimand is confounded. | Re-analysis, hours |
| **4** | **The B-with-a-non-target companion cell.** | H1: A specifically destroys B. H2: any composition destroys B. | Difference > 0.25 supports target-specific interaction; < 0.10 *refutes the pairwise framing entirely*. | ~800 generations |
| 5 | **Γ with a boundary-safe background.** | H1: the higher-order interaction is behavioural. H2: it requires a boundary-capable mark. | Γ > +0.15 with a boundary-safe mark establishes Candidate F. | ~960 generations |
| 6 | **Complete the blinded human sentence count.** | H1: the shipped convention matches human reading. H2: it does not. | Agreement below ~0.85 disqualifies the semicolon background. | Annotation only |
| 7 | **Greedy replication of one canonical cell.** | H1: clause chaining is a distributional mode. H2: a sampling artefact. | Chain rate at T = 0 under half the T = 0.7 rate makes every effect size decoding-conditional. | 160 generations |

**Assumptions that remain even if all seven succeed:** one task family (20 pilot topics); one base seed; one
wording index for almost all runs; and a constraint vocabulary built around sentence segmentation.

---

## 10. Recommended provisional phenomenon, construct and estimand

**Phenomenon.** *Compositional delivery loss.* When several instructions are presented together, the model
selects a single surface realisation strategy for the shared substrate they all address. Instructions
compatible with that strategy are delivered; instructions that are not are degraded or abandoned.

**Construct.** The compliance profile of a prompt: for every instruction present, the probability that it is
realised, measured on its own verifier, referenced to its own solo baseline, and reported jointly.

**Primitive outcome representation.**

```
X = (X_A, X_B, X_S₁ … X_S_m)   together with the graded vector   G = (G_A, G_B, G_S₁ … G_S_m)
```

**Primary estimand.** *Reciprocal delivery loss.* For instruction `c` and companion context `G`, at a stated
operating point:

```
D(c ← G)  =  P(X_c = 1 | c presented alone)  −  P(X_c = 1 | c presented with G)
```

reported as the reciprocal pair `(D(A←B), D(B←A))`, with the **asymmetry** `Λ = D(B←A) − D(A←B)` as the
directional summary. Unit of analysis: the task, paired across conditions, cluster-bootstrapped over tasks.
Requires an `A alone` and a `B alone` cell in every design.

**Secondary estimands, retained.** Γ (count-matched higher-order interaction); ρ (four-state redistribution
vector) as the *reporting* layer.

**Gates, not estimands.** Graded manipulation check `U_c ≥ 0.15`; convention stability ≥ 90% of rows; answer
rate ≥ 0.90 in every arm with arm spread ≤ 0.05.

**What this replaces, and what it does not**

- *τ(B→A) — target damage.* **Demoted to secondary diagnostic.** Not withdrawn: it is the right quantity
  when the target genuinely has headroom, the background is boundary-safe, and delivery is confirmed. Those
  three conditions co-occur in no cell of the current corpus.
- *The matched-reference design.* **Sound in principle, retained as a control arm.** Two changes: references
  must be matched on measured *solo compliance*; and the reference arm's own compliance must always be
  reported. It is no longer load-bearing for the primary estimand, so building a matched reference pool
  becomes a secondary, not blocking, task.
- *Candidate B — joint satisfaction loss.* **Rejected as primary.** It cannot separate "B is harder than R"
  from "B and A conflict".

---

## 11. Revision criteria

- If test #4 shows D(B←R) ≈ D(B←A), the phenomenon is generic compositional load, not pairwise interaction,
  and the whole A/B/R/S framing should be replaced by a load-and-capacity account.
- If test #5 shows Γ ≈ 0 with a boundary-safe background, higher-order constraint interaction is not
  established at all in this corpus.
- If human adjudication (#6) endorses the shipped segmentation convention on semicolon-bearing text, the
  convention-dependence in §6.1 becomes a robustness caveat rather than a construct problem. *(This is what
  happened.)*
- If a checkpoint is found with target headroom, focal uptake above 0.3, and a boundary-safe background, the
  informative regime exists after all and τ can be reinstated as primary at that operating point.
- If greedy decoding removes the clause-chain strategy, every effect in the programme is
  decoding-conditional.

---

## 12. Decision table

| Question | Current status | Evidence | Remaining uncertainty | Decision required |
|---|---|---|---|---|
| What is the primitive outcome? | **Settled** — the joint vector X, plus graded G | Interventions move ρ by 70–83 points with τ = 0.000 (§5.4, §5.5) | None material | Adopt joint reporting as mandatory; stop publishing bare τ |
| Should τ(B→A) remain the primary estimand? | **No** — demote to secondary | τ = 0.000 while D(B←A) = +0.517 in the one clean factorial (§5.2); τ ≈ 0 by construction on 4 of 5 checkpoints | Whether a headroom-bearing, boundary-safe cell exists anywhere | Approve demotion; keep τ as a conditional diagnostic with stated gates |
| Is the phenomenon real? | **Yes, and directional** | B: 0.667 alone → 0.150 composed; A: 1.000 → 1.000. Λ = +0.517, worst-case +0.400 | Rests on one 2×2, one checkpoint, one pair | Fund test #4 before generalising |
| Is the headline semicolon effect behavioural? | **Partly — sign-reversing under a defensible alternative convention** | τ = +0.400 → −0.225 → +0.200 across three conventions | Which convention matches human reading | Complete the human adjudication *(done in pass 2: shipped convention is correct)* |
| Is the focal constraint "not delivered"? | **Depends on the definition, and satisfaction is the wrong one** | Binary uptake 0.05–0.15; graded uptake +0.18 to +0.22 (bracket) but −0.35 to −0.05 (semicolon) | Whether negative graded uptake reflects strategy switching or scoring interaction | Adopt the graded manipulation check as an identification gate |
| Are B and R matched? | **Fortuitously yes on difficulty; never verified** | Solo compliance 0.667 vs 0.625 | Whether this holds for other reference candidates | Add measured solo compliance to the reference-matching criteria |
| Does an informative two-sided regime exist? | **No** — report as a negative result | Focal-only state 0.000/0.000/0.008 across a 14× difficulty ladder on held-out tasks | Kimi-VL under a bracket background is untested at a calibrated operating point | Publish the negative result; authorise one Kimi calibration run |
| Is higher-order interaction established? | **Provisionally** — Γ = +0.312 [+0.188, +0.438] | Genuine 2×2, all cells matched, recomputed from raw text (§5.1) | Measured only with a boundary-capable background | Repeat with a boundary-safe mark before treating Γ as established |
| Is the background a nuisance variable? | **No** — treatment, effect modifier, and measurement modifier | F(A+colon) = 0.013 alone but Γ = +0.312 in composition | None material | Reclassify S as a design factor; never pool across backgrounds |
| Are the analysis inputs trustworthy? | **Mostly yes; one committed table is not** | Verifier labels reproduce exactly on canonical files; `reasoning_rows.csv` matches DEPRECATED and FOREIGN sources at 1.000 | Which downstream figures used it | Regenerate that table from `s18_reseeded.jsonl` |
| Is missingness safe? | **Not in the newest cross-model dataset** | 19.2% empty answers, arm spreads to 20 points | Whether a bounded-thinking rerun fixes it | Adopt answer-rate gates before any cross-model estimate is interpreted |

---

**Scope note.** This pass concerns the scientific definition only. Verifier architecture, the
matched-reference pool, the confirmatory protocol, effect-size estimation and cross-model robustness are
downstream, and are touched above only where the construct decision changes them.
