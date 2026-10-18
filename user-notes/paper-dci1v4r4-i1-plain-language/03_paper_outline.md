# Full paper outline

## What this document is for

This document assigns each paper section a scientific question, the evidence needed to answer it, and the limits that must accompany the answer. The paper should be readable without knowledge of the DCI project, its protocol labels, or its repository. The main body should foreground two candidate contributions: directional composition effects and the failure to obtain a valid difficulty-matched companion estimate.

## Paper-level thesis

When a model was asked to satisfy two instructions simultaneously, verifier-defined compliance with one instruction fell in two clean position-matched comparisons and in two additional position-shifted comparisons. A solo-to-composed difference cannot determine whether the particular companion caused the change. The study attempted that stronger comparison using difficulty-matched alternative companions, but no checkpoint run carried the required reference design through to confirmatory estimation. The paper therefore contributes measured composition-related delivery losses and a carefully bounded account of failed companion-specific identification.

The final novelty claim and title remain provisional until the literature review establishes how these two contributions relate to prior work.

## Section 1. Introduction: what did the study ask and learn?

**Scientific question.** What changes when a model must satisfy two instructions, and what comparison is required to attribute the change to a particular companion?

**Content.** Follow `02_intro_outline.md`:

1. Introduce the practical problem of multi-instruction prompts.
2. Distinguish a generic composition-related change from a companion-specific effect.
3. Define directional delivery loss informally.
4. Explain why replacing the companion at fixed instruction count is needed for stronger attribution.
5. State the empirical answer: two position-matched losses, two position-confounded losses, and no valid matched-companion estimate.
6. State the two candidate contributions and the principal limits.

**Evidence introduced.** The four headline loss estimates and the fact that all six companion-specific quantities are `NOT_IDENTIFIED`.

**Do not include.** File paths, hashes, protocol labels, the detailed reference funnel, or a claim that the paper is novel before the literature review.

**Reader takeaway.** The reader can distinguish the result the study estimated from the stronger causal question it could not estimate.

## Section 2. Scientific setup: what do the quantities mean?

### 2.1 Instructions and verifier-defined compliance

Introduce the focal pair in ordinary language. Instruction $A$ is an exact-count production constraint. Instruction $B$ is a word-length budget constraint. Each response receives a deterministic pass/fail verdict for every instruction present.

Define (X_c\in\{0,1\}) as the verifier result for instruction $c$. State early that these are verifier-defined outcomes and were not independently human-validated.

### 2.2 Directional delivery loss

Define

\[
D(c\leftarrow g)
=P(X_c=1\mid c\text{ alone})
-P(X_c=1\mid c+g).
\]

Explain that positive values indicate lower compliance in composition and that direction matters. State the central limitation: $D(c\leftarrow g)$ changes instruction count from one to two, so it contains generic composition effects.

### 2.3 Difficulty and matched references

Define $\iota$ as the chance-corrected instructed-compliance coordinate used to match difficulty. Lower $\iota$ means greater difficulty. Define a matched reference $R_j$ as an alternative companion close to $A$ on this coordinate and admitted with sufficient precision.

Define the intended average companion contrast:

\[
\Delta_R
=D(B\leftarrow A)
-\frac{1}{J}\sum_{j=1}^{J}D(B\leftarrow R_j).
\]

Explain that this holds instruction count fixed at two. It does not hold structural class fixed because $A$ is production-form and the eligible references are budget-form.

Define the remaining companion quantities in plain language before notation:

- $\Delta_j$: the companion contrast for one reference rather than the reference average;
- $\Xi$: a reciprocal-specificity contrast that asks whether the effect is specific in both directions rather than only for $B$;
- $\delta_{\text{difficulty}}$: a contrast adjusted using a fitted relation between difficulty and delivery loss;
- $D(B\leftarrow R_j)$ and $D(R_j\leftarrow B)$: the two directional reference-composition losses required by the stronger design.

### 2.4 Full and reduced designs

Define the **full design** as the 47-cell design containing the composed-reference cells required for the quantities above. Define the **reduced design** as the eight-cell design that retains focal and class-companion solo/composed comparisons but omits composed-reference cells.

### 2.5 Position matching

Explain that the measured instruction appears first in every solo prompt. A composed estimate is position-matched only if it also appears first there. If it moves to second position, composition and position are confounded.

### 2.6 Meaning of `NOT_IDENTIFIED`

Define `NOT_IDENTIFIED` as “the study did not obtain a valid estimate.” State that it is neither a zero estimate nor evidence of no effect.

### 2.7 Sampling and uncertainty

Describe the block structure: 384 topics or blocks, eight draws per cell, and common wording assignments within a block. Explain the block bootstrap, 10,000 resamples, and simultaneous 95% intervals within each declared family. Place detailed algebra and multiplicity rules in Appendix A.

**Reader takeaway.** The reader can interpret every result and understand why $D$ and $\Delta_R$ answer different questions.

## Section 3. Related work: what is the actual novelty?

This section remains blocked until primary sources are reviewed. It should answer four focused questions:

1. Do existing instruction-composition benchmarks report directional, per-instruction solo-to-composed losses, or mainly aggregate and symmetric measures?
2. Do any existing studies replace a focal companion with difficulty-matched alternatives at fixed instruction count?
3. How have prior studies handled order and position effects in multi-instruction prompts?
4. What construct-validity standards already exist for controlling the difficulty and structure of benchmark companions?

Preregistration practice may be discussed briefly as methodological context only if the relevant literature supports it. Provenance is not a scientific contribution.

**Decision rule.** If the directional estimand is new but the matched-companion lesson is known, foreground the first contribution. If the matched-companion identification account is new but the estimand is known, foreground the second. If both are known, reconsider whether v4r4 should stand alone or become a diagnostic section of a later paper.

**Reader takeaway.** The reader can identify exactly what this paper adds beyond the closest prior studies. This sentence cannot be finalised before the literature review.

## Section 4. Study design: how was each scientific question tested?

### 4.1 Checkpoint runs and focal conditions

Describe the four checkpoint runs and the common candidate-library construction. Call them **checkpoint runs**, not independent replications, because they share the same library design.

Describe the two prompt orders and the solo cells needed to anchor each directional loss. State which conditions are position-matched and which move the measured instruction.

### 4.2 Building the reference comparison

Explain the scientific logic of the reference-selection sequence:

1. validate deterministic measurement;
2. locate a usable operating point for the focal instructions;
3. screen and calibrate alternative companions on solo difficulty;
4. admit sufficiently close and precise references, including difficulty support on both sides where required;
5. test whether relevant solo and composed cells retain enough headroom for an informative confirmatory comparison;
6. run either the full or reduced design determined by the available references.

Internal gate numbers may appear once in a traceability parenthesis or in Appendix B. The main text should describe the scientific purpose of each stage.

### 4.3 Structural scope of the references

State that production-class families were excluded from the core reference pool before measurement, whereas $A$ was production-class. This means the intended companion comparison matched difficulty but not structural class. Present this as a design scope condition, not as an observed cause of non-identification.

### 4.4 Analysis integrity as supporting methodology

Summarise the frozen analysis, masking, and signed-record sequence in one paragraph. Explain what they support and what they cannot prove. The detailed record hashes, code hashes, and bundle inventory belong in Appendix G and `EVIDENCE_MAP.md`.

**Reader takeaway.** The reader understands how the design attempted to separate generic composition from companion-specific effects, and why the full design was necessary.

## Section 5. Directional composition effects: what changed when a second instruction was added?

### 5.1 Data that reached confirmatory analysis

Report that `gemma-3n-e4b-it` and `qwen3-4b` completed the reduced design. Each contributed 24,576 complete rows, for 49,152 total, with no missing, duplicated, or unexpected rows.

### 5.2 The 20 interval-bearing estimates

Explain the count before displaying it:

- 12 directional delivery-loss quantities $D(c\leftarrow g)$;
- 4 directional asymmetry contrasts $\Lambda=D(B\leftarrow A)-D(A\leftarrow B)$;
- 4 class-companion contrasts $\Delta_{\text{class}}=D(B\leftarrow A)-D(B\leftarrow CL)$.

The last eight are derived contrasts, so the paper must not call all 20 delivery-loss estimates. Place all estimates, simultaneous intervals, marginal intervals, and bootstrap standard errors in Table 1.

### 5.3 Position-matched results

Lead with the clean findings:

- `gemma-3n-e4b-it`: $D(A\leftarrow B)=+0.1159$, simultaneous 95% interval [+0.0771,+0.1546];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3919$, [+0.3503,+0.4335].

Interpret them as reductions in verifier-defined compliance when a second instruction is added while the measured instruction remains in the same position. State immediately that these are solo-to-composed effects, not companion-specific effects.

### 5.4 Position-shifted results

Report with the caveat attached:

- `gemma-3n-e4b-it`: $D(B\leftarrow A)=+0.2832$, [+0.2485,+0.3179];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3291$, [+0.2835,+0.3747].

Use the fixed interpretation: **composition and position change together**.

### 5.5 What the comparisons do not establish

State that the four findings are separately licensed within their own uncertainty families. No study-level multiplicity procedure covers their conjunction. Cross-model and cross-configuration differences are descriptive, and the study did not establish directional asymmetry.

Report the registered robustness analyses involving alternative vacuity scoring in a short subsection or Appendix C. Do not introduce post-hoc robustness claims.

**Primary display.** Figure 1 should foreground the four focal losses and visually separate position-matched from position-shifted conditions. Table 1 should contain all 20 estimates.

**Reader takeaway.** The reader can quote the two clean delivery-loss estimates, report the two position-confounded estimates responsibly, and explain why none identifies companion specificity.

## Section 6. Matched-companion identification: why is there no companion-specific estimate?

### 6.1 Experimental outcomes across the four checkpoint runs

Present a compact table:

| Checkpoint run | Core references | Design | Confirmatory status |
|---|---:|---|---|
| `gemma-3n-e2b-it` | 3 | Full, 47 cells | Stopped at composed-headroom validation |
| `qwen3-4b` | 2 | Reduced, 8 cells | Analysed without reference-composition cells |
| `gemma-3n-e4b-it` | 0 | Reduced, 8 cells | Analysed without reference-composition cells |
| `qwen3-4b-instruct-2507` | 0 | Reduced, 8 cells | Later stopped at headroom validation |

Explain the actual stopping points:

- three runs had fewer than the required three core references;
- the reduced design omitted every composed reference cell;
- the only full design stopped before confirmatory generation because relevant rates exceeded the headroom band.

Clarify that the later `qwen3-4b-instruct-2507` headroom failure did not cause its companion non-identification because the run already had zero core references.

### 6.2 Quantities without valid estimates

List $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, and $D(R_j\leftarrow B)$. Label each `NOT_IDENTIFIED` and repeat the definition in prose. Table 2 should pair each quantity with the missing design component.

### 6.3 Post-hoc diagnostic 1: the shortlisted difficulty landscape

Report 65 of 84 shortlisted calibrated rungs below $\iota_A$, with eligible-above counts 2, 1, 1, and 0. Carry both mandatory qualifications:

- the 84 are the 21, 20, 23, and 20 shortlisted rungs from six budget-class families, not the 254 eligible rungs measured per run at pre-screen;
- the same 84 moved from a 54/30 pre-screen split to a 65/19 calibration split. Fourteen moved above-to-below, three below-to-above, and 17 changed side in total.

The plot and prose must label this as a post-hoc description. No counterfactual shows that this distribution bound the design.

### 6.4 Post-hoc diagnostic 2: proximity versus precision

Report that 18 rungs lay inside the 0.10 calibration caliper and nine were refused: eight because their Newcombe intervals did not intersect the ±0.05 equivalence region and one because of the pre-screen criterion. Explain that the precision result depends partly on the calibration sample of 96 solo topics with four draws.

### 6.5 Composed-headroom outcome

Report the observed full-design failure without turning it into a general explanation. On `gemma-3n-e2b-it`, `RF11:26` moved from 0.6875 solo compliance to 0.9688 when composed with $B$, exceeding the [0.05, 0.95] headroom band. Five evaluated slots involving the `RF11` family failed, with rates from 0.9583 to 1.0000.

Report the distinct `qwen3-4b-instruct-2507` outcome separately: its one failure was the class companion's solo rate of 0.9896.

### 6.6 Interpretive boundary

State that no sensitivity analysis shows that widening the caliper, changing reference admission, allowing production-class families, or changing the headroom band would have produced a valid $\Delta_R$. The selection rules show what this procedure did; they do not establish that it was the only viable procedure.

**Primary displays.** Figure 2 should show which scientific quantities each checkpoint design could estimate. Figure 3 should show the two post-hoc diagnostics and the observed headroom breach without implying causality.

**Reader takeaway.** The reader can distinguish the experimental facts that prevented estimation from the later diagnostics that merely describe the candidate pool.

## Section 7. Discussion: what follows, and what remains unknown?

### 7.1 Synthesis

Join the contributions in one sentence: v4r4 measured directional composition-related losses but did not identify whether the focal companion caused them beyond generic two-instruction difficulty.

### 7.2 Scientific limitations

Lead with the major limits:

1. Confirmatory estimates come from two of four checkpoint runs, one constraint pair, load two, one topic space, and one decoding policy.
2. Outcomes are deterministic-verifier judgments rather than independently human-validated compliance judgments.
3. The reference comparison did not hold structural class fixed.
4. Cross-model and cross-configuration differences were not directly tested.
5. No sensitivity analysis establishes that alternative thresholds or reference classes would identify the companion comparison.
6. The attrition diagnostics are post-hoc and do not support causal explanations.
7. The two surviving runs used different operating points and different class companions and should not be pooled as interchangeable replications.

### 7.3 Methodological and provenance limitations

Briefly report the structurally unmaskable groups, the invalid emitted cross-configuration field on `gemma-3n-e4b-it`, the live protocol-amendment objection, the evidence-bundle coverage boundary, and the limits of researcher-held HMAC signatures. These support calibrated reporting and auditability; they are not a separate scientific contribution.

### 7.4 Implications

For composition studies, report direction, anchor, and prompt position. For matched-control designs, verify that reference candidates can populate the required composed cells before interpreting a focal pair as companion-specific. Phrase these as lessons from this implementation rather than universal requirements unless the literature review justifies broader claims.

### 7.5 Prospective follow-up

Describe a future design with structurally matched companions, adequate difficulty support, and pre-composition checks defined before observing confirmatory outcomes. The existing v5 development analysis is design fitting: it can motivate such a study but does not validate its proposed quantities or thresholds. A future experiment could establish whether its own design obtains valid companion estimates; it could not settle general estimability for every constraint library.

**Reader takeaway.** The reader knows the strongest warranted interpretation, the most important unresolved alternatives, and what a prospective study would need to test.

## Section 8. Conclusion: what should the reader remember?

Keep this section short or omit it if the Discussion closes cleanly. If retained, state three points:

1. Adding a second instruction coincided with lower compliance in two clean position-matched comparisons.
2. Two additional losses were position-confounded.
3. The study obtained no valid matched-companion estimate, so the particular companion cannot be identified as the cause.

Do not introduce a novelty claim or a new future-work programme here.

## Planned figures and tables

| Display | Scientific question | Main takeaway |
|---|---|---|
| Figure 1 | What directional composition effects were estimated? | Two focal losses are position-matched; two further losses change position and require that caveat. |
| Figure 2 | Which checkpoint designs could estimate the companion comparison? | None carried the full reference comparison through to confirmatory analysis. |
| Figure 3 | What do the later reference diagnostics describe? | The shortlist shifted toward the harder side, precision rejected eight in-caliper candidates, and one admitted reference breached composed headroom; these observations are descriptive rather than proven causes. |
| Table 1 | What are all interval-bearing results? | Twenty estimates comprise 12 delivery losses and 8 derived contrasts. |
| Table 2 | Which planned quantities lack estimates? | Six companion-specific quantities are `NOT_IDENTIFIED`, meaning no valid estimate exists. |
| Table 3 | How did reference support differ across runs? | Reference admission produced one full design and three reduced designs, with only two reduced designs reaching analysis. |
| Appendix table | How is the evidence traceable? | Record, code, bundle, and completeness details support verification without becoming a headline contribution. |

## Appendix plan

- **Appendix A: estimand algebra and uncertainty.** Full definitions of $D$, $\Lambda$, $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, and the simultaneous interval procedure.
- **Appendix B: design and execution detail.** Internal stage labels, thresholds, full and reduced cell maps, decoding policy, model revisions, seed scheme, and freeze fields.
- **Appendix C: complete results.** All 20 estimates, alternative vacuity scorings, per-cell rates, and full headroom tables.
- **Appendix D: qualitative examples, only if a selection rule is fixed first.** Delete this appendix if no defensible selection protocol is adopted.
- **Appendix E: citation verification register.** Every provisional literature claim, its source, and verification status.
- **Appendix F: broader related-work coverage.** Coverage by scientific question rather than repository topic.
- **Appendix G: artifact and reproducibility statement.** Bundle inventory, verification checks, missing items, post-hoc diagnostic location, and provenance limits.
- **Appendix H: reproduction cautions.** Known stale comments, the incorrect caliper values in an internal report, and other traps that should not enter the scientific narrative.

## Claim checks before prose drafting

Before writing the full paper, verify that:

- every occurrence of 65/84 says that 84 is the shortlist and carries the pre-screen-to-calibration shift;
- every occurrence of 9/18 attributes eight refusals to precision and one to the pre-screen criterion;
- every position-shifted result says that composition and position changed together;
- all cross-model and cross-configuration comparisons are labelled descriptive;
- `NOT_IDENTIFIED` is never paraphrased as no effect;
- the structural-class mismatch is presented as a scope condition rather than a cause;
- no sensitivity analysis is implied where none was run;
- provenance machinery remains supporting methodology; and
- novelty and title language remain provisional until the literature review is complete.

## What the reader should understand after reading this

The reader should understand how every paper section advances one of the two candidate contributions, what evidence belongs in each section, and where the interpretation must stop. The planned paper measures directional composition effects, explains the absence of a matched-companion estimate, and keeps post-hoc diagnostics, provenance, and novelty claims in their appropriate supporting roles.
