# DCI-1 v4 revision 2: what changed scientifically, and the element-by-element change table

**Date:** 19 August 2026 · **Status:** prospective design record for a
preregistration that has not been frozen · **Companions:**
`DCI1_preregistration_v4r2.md`, `DCI1_v4r2_unresolved_decisions.md`,
`DCI1_v4r2_changelog.md`, `DCI1_v4r2_prefreeze_checks.md`.

**Standing conditions.** DCI-1 v3 is closed and is not modified,
reinterpreted, or re-analysed as confirmatory evidence here. The B+R pilot
(`reports/br_pilot_v4/`) is **non-confirmatory**: it motivates the redesign
and supplies exploratory variance and effect-size information for power
planning, and it licenses no scientific claim. v4 revision 1 was never
registered, never frozen, and produced no data; replacing it is a
prospective act.

---

## A. What changed scientifically

### A.1 The discriminating question was recovered, and it is a companion swap

Revision 1 inferred the "B+R / B+S" recommendation from a one-line
reference in the v3 results report and reconstructed it as a crossed
design in which the **outcome constraint** was swapped between the target
A and a surrogate target S. The source is now available. The construct
memo `dci-construct-pass2.md` §G row 1 specifies the opposite crossing:
hold the **outcome** fixed at the focal constraint B and swap the
**companion** between A and a matched reference R:

> Generate B+R and B+S without the sentence-count instruction, beside the
> existing B-alone and B-with-A cells.
> D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct.
> < 0.10 supports H2 and refutes the pairwise framing entirely.

Revision 1's surrogate crossing, its estimand ι, its surrogate constraint
*hence*, and the four open decisions that depended on them are withdrawn
in full. Nothing in the uploaded corpus contradicts the memo, so the memo
governs.

### A.2 The primitive is the compliance vector, and the outcome is B

The memo settles the primitive: for a prompt containing instructions
c₁…c_k, the observation is the vector X = (X_{c₁} … X_{c_k}) of realised
compliance with every instruction present, reported with the graded vector
G and with degeneracy diagnostics. Target failure F_A is one marginal of
that vector. v4 records the whole vector and makes the delivery of every
constraint an outcome.

The consequence for the constraint under study is decisive. In the v3
architecture the outcome was compliance with A and the treatment was the
identity of the companion. Under the recovered question the outcome is
compliance with **B** and the treatment is the identity of the companion.

### A.3 v3's registered estimand is the near-zero side of an asymmetric phenomenon

Write D(c ← G) = P(X_c = 1 | c alone) − P(X_c = 1 | c with G). Two
companion-swap contrasts exist at load two, one per outcome:

    Δ^B = D(B←A) − mean_j D(B←R_j)        the B-side companion swap
    Δ^A = D(A←B) − mean_j D(A←R_j)        the A-side companion swap

Δ^A is algebraically identical to v3's registered pooled swap effect
re-expressed on the compliance scale, and it reproduces the v3 record
exactly: −0.0095 for E2B against the recorded `pooled_swap_effect`
−0.009549, and +0.0651 for E4B against the recorded +0.065104. Δ^B, from
the pilot, is +0.3433 and +0.3751.

The v3 study measured the side of the phenomenon on which the effect is
near zero. That is the clearest available explanation of why four of four
v3 primary estimands failed to resolve in direction while its
pseudo-selection and greedy diagnostics pointed positive at +0.04 to
+0.11. It does not explain the per-reference diagnostics, which split
sign in the E2B target-first stratum, +0.135 against one reference and a
resolved −0.130 against another, and which v3 itself read as a matching
problem rather than a clean null. The asymmetry is direct: from the v3 rows,
D(A←B) = +0.099 (E2B) and +0.177 (E4B) against D(B←A) = +0.468 and +0.316,
giving Λ = D(B←A) − D(A←B) = +0.369 and +0.139. The model keeps the
exact-count target and drops the word-length constraint, which is the
memo's one-sided sacrifice observed in a second constraint vocabulary.

*(Δ^A, D(A←B) and Λ are computed here from v3 registered rows and pilot
rows as exploratory design evidence. They are not v3 registered quantities
and they change nothing in the v3 record.)*

### A.4 The pilot's headline is confounded by companion difficulty, and v4 must fix it

The pilot reused the v3 reference set, which was selected under the v3
rule: matched to **B** on solo failure rate. **That rule succeeded on its
own terms.** The mean reference-minus-$B$ solo-compliance gap is $+0.052$
for E2B and $+0.028$ for E4B. Under the recovered question the reference
stands in for **A**, so it must be matched to **A**, and on that criterion
the same set is badly mismatched. Computed from the pinned Gate 2A solo
counts and the v3 target-alone arm:

| Model | P(A solo) | mean P(R solo) | gap | P(B solo) |
|---|---:|---:|---:|---:|
| gemma-3n-e2b-it | ≈ 0.667 | 0.8646 | **+0.198** | 0.8125 |
| gemma-3n-e4b-it | ≈ 0.578 | 0.7882 | **+0.210** | 0.7604 |

P(A solo) here comes from the v3 confirmatory target-alone arm at one
selected draw per cell, while P(R solo) and P(B solo) come from the v3
Gate 2A solo cells on a different topic set, so the gap is an approximate
design figure rather than a matched estimate; the v4 design measures it
directly and precisely on its own solo cells (change 5 in the table
below).

A is a harder companion than every reference by about 0.20 in solo
compliance. Part of the pilot's Δ is therefore attributable to companion
difficulty rather than to companion identity. v4 inverts the
reference-matching target to A and registers a caliper on it.

**The construct memo's related finding concerns a different constraint
vocabulary and a different contrast, and is not the same number.** The
memo's constraints are A = "write exactly 4 sentences", B = "each sentence
strictly longer than the last", R = "begin every sentence with a word
starting with S", with pooled solo compliance 0.964, 0.541 and 0.716. Its
§B.3 gap of +0.193 is reference minus **focal**, and it is that gap the
memo classifies `[Not identified]` for every estimand comparing P(X_B)
against P(X_R). In the memo's vocabulary the reference-minus-target gap is
−0.248, of the opposite sign to the v3 figure. What transfers is the
lesson, that companion difficulty is a live confound no shipped analysis
had measured, not the number.

One piece of pilot evidence bears against the pure difficulty explanation
and is recorded without overclaiming. Within each model the three
references have almost identical solo compliance (range 0.0000 for E2B,
0.0208 for E4B) while D(B←R_j) varies across them by 0.177 and 0.188. At
constant companion difficulty, companion identity still moves delivery
loss by roughly 0.18. The constancy is measured at one draw per topic over
96 topics, so each solo rate carries a standard error near 0.035 and the
observed range understates the true spread. That constrains, and does not
remove, the difficulty explanation for the A-versus-R gap.

### A.5 Configuration dependence is the largest single moderator

Instruction order changes the pilot quantities by more than the quantities
themselves. Recomputed from the pilot diagnostics with B's position held
in view. The Δ column is fully order-stratified because the solo baseline
cancels; the D columns divide an order-stratified composed rate by the
pooled P(B solo), because the pilot reports no order-stratified solo rate,
and the two strata come from different topic sets and different
order-assignment mechanisms. Both caveats are removed in v4, where every
cell runs on the same blocks and order is a within-block factor:

| Model | B's position | P(B\|R̄) | P(B\|A) | Δ | D(B←A) | D(B←R̄) |
|---|---|---:|---:|---:|---:|---:|
| E2B | first | 0.8854 | 0.4661 | +0.4193 | +0.3464 | −0.0729 |
| E2B | second | 0.4896 | 0.2223 | +0.2673 | +0.5902 | +0.3229 |
| E4B | first | 0.9236 | 0.6217 | +0.3019 | +0.1387 | −0.1632 |
| E4B | second | 0.7153 | 0.2669 | +0.4484 | +0.4935 | +0.0451 |

D(B←A) spans 0.139 to 0.590 across four configurations, a factor of four.
D(B←R̄) changes sign with order in both models: a reference companion
**facilitates** B when B is stated first and damages it when B is stated
second. Δ stays positive and above 0.25 in all four configurations, and
its ordering across models reverses with order. The memo's Candidate 6
prohibition applies directly: no scalar may be quoted without its
configuration. v4 makes every primary estimand order-conditional and
reports no pooled scalar as a claim.

A methodological consequence follows that the pilot did not state. The
solo cell places its single constraint at position one. D(c ← G) is
therefore position-matched to its baseline only in the stratum where c is
stated first; in the other stratum it confounds added load with a change
of position. Δ differences two composed cells with c in the same position,
so Δ is position-clean in both strata. v4 registers this distinction and
makes Δ-type quantities the ones that carry the companion-identity claim.

### A.6 References stop being a prerequisite and become a control arm

Under the memo, "the reference is needed for τ, not for Candidate 4", and
"building the final reference pool ceases to be a blocking prerequisite".
D(B←A), D(A←B) and Λ need only solo baselines and the A+B cell. A
reference pool is needed only for the excess-damage claim.

The structural consequence is large: reference-pool failure no longer
terminates a replication. The two Qwen replications that ended at v3 Gate
2A with `REFERENCE_POOL_MISMATCH` become estimable for the delivery-loss
and asymmetry claims, and lose only the excess-damage claim if no matched
reference exists. v4 replaces the terminal status with a per-claim
identification status.

### A.7 Vacuous passing becomes a first-order validity threat

B and every reference family are non-violation constraints of the form
"at most q …" or "every word at most m letters". An empty or very short
answer satisfies them mechanically. In v3 these verifiers scored a
secondary manipulation check, so vacuity was a footnote. Under the new
primitive they are the primary instruments and vacuity can move the
primary estimand in either direction: composition shortens answers, and
shorter answers pass length-style constraints more easily. The pilot
recorded 13/576 and 8/576 answers under three words, with zero
truncations, so the realised rate is low and non-zero.

v4 registers a non-vacuity predicate per constraint, reports the vacuity
rate per cell, and treats vacuous passes with the partial-identification
device v3 already uses for non-behavioural failures. It does not filter
them out of the primary estimand, because response shortening is a
candidate mechanism rather than a nuisance.

### A.8 The measurement-validity programme has to cover the family verifiers

v3 already required the 40-case boundary suite and three-process
determinism of **every** verifier. Everything else was S0-only: the 120
blinded human labels, the autorater development and calibration, the
independent reimplementation, and the four validity arguments. The
`added_verifier` family functions therefore carry partial evidence,
sufficient for a secondary manipulation check and not for a primary
instrument. Under the new primitive they are primary. v4 extends the rest
of the Gate 1 programme to every outcome verifier it uses, re-authors the
boundary suites against a wider enumeration, and refuses to freeze until
that evidence exists.

### A.9 What did not change

The deterministic-verifier architecture, the verifier source-hash freeze
and its downstream binding, the autorater as a validation-only proxy that
never writes a behavioural score, the prohibition on describing
author-performed labels as independent validation, the sealed reserved
set, the artifact-state and provenance machinery, the exclusion of
deprecated and foreign sources from registered evidence, block-level
clustering with a bootstrap over blocks, draw-averaged cell means, masked
analysis, and the guarded claim emitter.

---

## B. v4 revision 1 → v4 revision 2 change table

Every row: old element → evidence or problem → revised element →
rationale.

| # | v4r1 element | Evidence / problem | v4r2 element | Rationale |
|---|---|---|---|---|
| 1 | "B+R / B+S" inferred as a crossed design over outcome constraints (A vs surrogate S) × companions (B vs R), with ι = τ_A − τ_S as a primary estimand | The source is now available. `dci-construct-pass2.md` §G row 1 specifies B+R and B+S **without** the target A, holding the outcome at B and swapping the companion | Companion swap on the focal outcome: Δ_R = D(B←A) − mean_j D(B←R_j); the outcome-crossing design is withdrawn | The memo is the design authority the v3 report was pointing to, and the pilot has already executed its B+R half; the B+S half generated nothing because v3 registers the background set as empty, so B+S coincides with B-alone |
| 2 | Surrogate target constraint S = "use the word *hence* exactly k times", four wordings, its own grid, its own solo and composed arms | S existed only to carry the withdrawn crossing. It is not required by any recovered question, and it added five arms and a full witness and wording suite | Removed. No surrogate outcome constraint is registered. A second focal-like constraint is recorded as an optional exploratory extension and is not registered | Nothing in the corpus asks whether B is specifically *vulnerable*; the recovered question asks whether A is specifically *damaging* |
| 3 | Primitive observation: target failure F_A under S0, plus uptake as a manipulation check | Memo §H: the primitive is the joint vector; §D.6 shows a checkpoint where reasoning moves joint compliance by ~70 points while τ is 0.000 in all four cells | Primitive: the full per-constraint compliance vector X, the graded vector G, and per-constraint degeneracy flags, recorded for every constraint present in every prompt | Target failure is one marginal of the vector and is degenerate wherever the target is at ceiling |
| 4 | Primary estimands τ (swap effect on A), τ_S (surrogate), ι = τ − τ_S | τ is Δ^A re-expressed, which reproduces the v3 record at −0.0095 and +0.0651. It is the near-zero side of the phenomenon | Primary estimands per configuration: D(B←A), D(A←B), Λ = D(B←A) − D(A←B), Δ_R = D(B←A) − mean_j D(B←R_j) | Reciprocal delivery loss needs no commensurability assumption, needs no reference for existence, and survives target ceiling |
| 5 | Reference set selected by matching R to **B** on solo failure rate; three families required; failure is terminal | Under the companion swap R stands in for **A**. Realised gap mean P(R solo) − P(A solo) = +0.198 and +0.210 | References matched to **A** on solo compliance within a 0.10 caliper whose 95% Newcombe interval intersects ±0.05, three distinct families, plus the 20% instruction-length caliper measured against A. The realised gap is re-measured on the confirmatory solo cells and reported beside every excess-damage statement. Failure yields `EXCESS_NOT_IDENTIFIED` for the excess-damage claim only | The reference estimates the generic-composition counterfactual for the companion slot; matching it to the outcome constraint answers a different question |
| 6 | Reference-pool failure terminates the replication (`REFERENCE_POOL_MISMATCH`) | Memo §F: "Should the primary estimand need a matched reference at all? **Settled — no**" | Reference identification is a per-claim gate. L1 and L2 proceed without references; only L3 is withheld | Two of four v3 replications produced no evidence at all because a control condition could not be built; the primary estimand does not need it |
| 7 | Composed-uptake admission predicate, caliper 0.15, with terminal status `COMPOSED_UPTAKE_MISMATCH` | Composed uptake of B **is** the primary outcome under the new estimand. Selecting references on it is conditioning on the outcome | Removed as a selection criterion. Composed compliance is reported per cell and enters headroom gates only, never reference ranking | Selecting a control on the outcome it is meant to counterfactual is circular |
| 8 | Composed response length as a reported comparability quantity with an interpretation block | Composition shortens answers and shorter answers pass length-style constraints more readily, so length is on the causal path from companion to outcome | Registered **mediator**: reported per cell, entering a registered mediation-diagnostic and the vacuity sensitivity, never a matching criterion, filter, covariate or gate | Conditioning on a mediator would silently change the estimand |
| 9 | Dense integer severity ladder over all eight families, screened on 24 topics, confirmed at M_cal = 4, to find references matched to B | The machinery is sound and its target changes. Matching to A requires **harder** reference severities than v3 used, because references sit ~0.20 above A in solo compliance | Retained with the matching target changed to A, and extended to select n\* and m\* on solo-compliance bands for the two outcome constraints | The v3 non-identifications were caused by unmeasured severities; the same fix applies to the new matching target |
| 10 | Order handled by pooling into one estimand with an interaction gate, to buy precision | Pilot: D(B←A) spans 0.139 to 0.590 across four (model × order) cells and D(B←R̄) changes sign with order in both models | Order is a stratification variable. Every primary estimand is order-conditional; each (model, order) configuration is a separate replication with its own multiplicity family; no pooled scalar carries a claim | Memo Candidate 6 is a prohibition, and the pilot shows the prohibition binds in this vocabulary |
| 11 | Design: 11 arms per block (A-side and S-side composed cells, two solo arms, one no-constraint arm) | The surrogate arms are withdrawn; the recovered question needs the companion dimension instead | Design: the complete pairwise composition matrix over the five registered constraints {A, B, R₁, R₂, R₃}: 5 solo cells and 10 unordered pairs × 2 orders = 25 cells per block, each composed generation scored on both of its constraints | Yields every reciprocal pair, both companion-swap contrasts, and the outcome × companion table, from one non-arbitrary design |
| 12 | M = 8 draws per cell, 384 blocks, sized so that a projected detectable effect of 0.064 covered the 0.04 to 0.11 range of the v3 diagnostics | That justification was built on the withdrawn estimand. A variance model fitted to the pilot interval widths reproduces the observed standard error for both models at a topic-variance share of 0.27, and at 0.37 under a less favourable correlation assumption | 384 blocks with order as a **within-block** factor, M = 4, 25 cells: 38,400 generations per model and 153,600 across four models. Projected simultaneous half-widths 0.047 for D, 0.042 for Δ_R, 0.066 for Λ, 0.050 for Δ_j | The requirement is absolute precision rather than power against an assumed effect; running both orders inside each block puts all 384 blocks behind every configuration and pairs the order contrast within topic |
| 13 | SESOI 0.10 for every primary estimand, with an equivalence rule and a precision precondition at 0.05 | The memo supplies two prospectively available decision thresholds for Δ, quoted verbatim in the pilot protocol before generation | Δ_R decision thresholds 0.10 and 0.25 from the memo; SESOI 0.10 retained for D and Λ; precision preconditions 0.05 for D and Δ_R, 0.08 for Λ, 0.06 for Δ_j, all met under both fitted variance settings | The thresholds predate all pilot data and are not post-hoc; the preconditions are set at half the smallest effect of interest and are met with margin rather than by construction |
| 14 | Five-tier claim ladder ending at an identity-specific claim licensed by ι plus exchangeability plus uptake matching | Identity-specific attribution needs companion matching, order stability and load generality, none of which this design delivers in full | Claim ladder L1 delivery loss exists, L2 directional asymmetry, L3 excess damage relative to matched companions, L4 replication across configurations, L5 semantic identity-specificity and universal pair properties **explicitly withheld** | The design identifies excess damage relative to a matched companion set, which is weaker than semantic specificity and is what the memo licenses |
| 15 | Gate 1 measurement programme applied to the exact-count rule S0 | Under the new primitive every family verifier is a primary instrument, and none carries boundary-suite, human, or autorater evidence | Gate 1 extended to every registered outcome verifier: boundary suite, three-process determinism, independent reimplementation, human agreement where an annotator exists, autorater calibration otherwise | An instrument that produces a primary score needs primary-instrument evidence |
| 16 | Non-behavioural failure handled by arm-symmetry checks and partial identification | Non-violation constraints pass vacuously on empty or degenerate output, and this is now an outcome-side threat | Non-vacuity predicate registered per constraint; vacuity rate reported per cell; partial-identification recomputation with vacuous passes forced to fail; primary estimand computed on the full population | Vacuity is a validity threat and shortening is a candidate mechanism; the two must not be conflated |
| 17 | Masking permutes added-constraint labels within block on each outcome side | The design is now a companion matrix | Masking permutes the **companion label** within (outcome constraint, order, block). Solo cells are unmasked. Joint-state quantities are computed after unmasking under the registered plan and are labelled as such | The primary contrasts are companion swaps, so the companion dimension is the one that must be masked |
| 18 | Terminal statuses centred on reference-pool and uptake failures | Reference failure no longer blocks the primary estimands | Terminal statuses reduced to apparatus, measurement, and regime failures; reference failure becomes a per-claim identification status | A study that can answer its primary question should not stop because a control arm is unavailable |
