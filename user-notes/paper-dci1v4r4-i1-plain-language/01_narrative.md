# Scientific narrative for the DCI v4r4 paper

## What this document is for

This document states the paper's scientific story in its clearest form. It explains the question, the comparison needed to answer it, the results v4r4 actually obtained, and the limits on their interpretation. The paper has two candidate contributions: directional estimates of compliance loss when instructions are composed, and an account of why the intended difficulty-matched companion comparison did not reach confirmatory estimation.

## The scientific question

Language-model prompts often ask for several things at once. The central question is what happens to compliance with one instruction when another instruction is added. A useful answer must separate two possibilities:

1. **Generic composition cost:** compliance changes because the prompt now contains two instructions rather than one.
2. **Companion-specific effect:** compliance changes because of the particular instruction that was added.

A solo-versus-composed comparison can measure the first quantity. It cannot, by itself, identify the second because adding a companion changes both the companion's identity and the number of instructions in the prompt. The study therefore attempted a second comparison in which the focal companion was replaced by alternative companions of similar difficulty while instruction count remained fixed.

The study obtained usable solo-versus-composed estimates on two checkpoint runs. It did not obtain a valid companion-specific estimate on any checkpoint run. That distinction is the paper's organising principle.

## Concepts and notation

### Directional delivery loss

Let $c$ be the instruction whose compliance is measured and $g$ the instruction added beside it. Define

\[
D(c\leftarrow g)
=
P(c\text{ passes when presented alone})
-
P(c\text{ passes when composed with }g).
\]

A positive value means that verifier-defined compliance with $c$ is lower when $g$ is present. A negative value means compliance is higher in the composed prompt. The arrow records direction: $D(A\leftarrow B)$ and $D(B\leftarrow A)$ are different quantities.

This measure is **solo-anchored**. It compares a one-instruction prompt with a two-instruction prompt, so it includes any generic cost or benefit of adding a second instruction. It does not show that the identity of $g$ caused the change.

### Difficulty and matched references

The study represents instruction difficulty by $\iota$, a chance-corrected measure of instructed compliance. Lower $\iota$ indicates lower compliance and therefore greater difficulty. A **matched reference** $R_j$ is an alternative companion selected to have difficulty close to the focal companion $A$, subject to the study's admission criteria.

The intended companion contrast was

\[
\Delta_R
=
D(B\leftarrow A)
-
\frac{1}{J}\sum_{j=1}^{J}D(B\leftarrow R_j).
\]

This compares the effect of composing $B$ with $A$ against the effect of composing $B$ with difficulty-matched alternatives. Both sides contain two instructions, so instruction count is held fixed. A positive $\Delta_R$ would mean that $A$ reduces compliance with $B$ more than the admitted references do.

The comparison would still have had an important limitation. $A$ is a production-form instruction, while the permitted reference pool contained budget-form instructions. Replacing $A$ with $R_j$ would therefore have changed both companion identity and structural class. Even a valid $\Delta_R$ would not have isolated identity while holding structural form fixed.

### Full and reduced designs

The **full design** contained the composed reference cells needed to estimate $D(B\leftarrow R_j)$, $\Delta_R$, and the other companion-specific quantities. It contained 47 cells per block.

The **reduced design** contained eight cells per block and omitted the composed reference cells. It could estimate directional solo-to-composed delivery losses for the focal pair and a class companion, but it could not estimate the intended matched-companion contrasts.

### Position matching

In every solo prompt, the measured instruction occupied the first position. A solo-to-composed estimate is therefore **position-matched** only when that instruction also appears first in the composed prompt. If it appears second, composition and position change together. Such a **position-shifted** estimate remains a measured difference, but it cannot be attributed to composition alone.

### What `NOT_IDENTIFIED` means

`NOT_IDENTIFIED` means that the study did not obtain the cells or support required for a valid estimate. It does not mean the effect is zero, absent, or statistically non-significant. No post-hoc estimate substitutes for a quantity marked this way.

## Main empirical result: directional composition effects

Two checkpoint runs completed confirmatory generation under the reduced design: `gemma-3n-e4b-it` and `qwen3-4b`. Together they produced 49,152 complete response rows, 24,576 per run, with no missing, duplicated, or unexpected rows. The analysis used 384 blocks, eight draws per cell, and 10,000 block-bootstrap resamples.

The confirmatory output contains **20 interval-bearing estimates** across two checkpoint runs and two prompt configurations. Of these, **12 are directional delivery-loss quantities** $D(c\leftarrow g)$, and **8 are derived contrasts**: four directional asymmetry contrasts $\Lambda$ and four class-companion contrasts $\Delta_{\text{class}}$. Calling all 20 "delivery-loss estimates" would be inaccurate.

The clearest empirical result comes from the two position-matched conditions:

| Checkpoint run | Position-matched quantity | Estimate | Simultaneous 95% interval |
|---|---:|---:|---:|
| `gemma-3n-e4b-it` | $D(A\leftarrow B)$ | +0.1159 | [+0.0771, +0.1546] |
| `qwen3-4b` | $D(A\leftarrow B)$ | +0.3919 | [+0.3503, +0.4335] |

In both cases, verifier-defined compliance with $A$ was lower when $B$ was added, with the measured instruction occupying the same prompt position in the solo and composed conditions. These are clean estimates of a solo-to-composed delivery difference. They still include the generic effect of moving from one instruction to two and therefore do not identify a companion-specific effect of $B$.

Two further conditions also showed interval-separated delivery losses, but the measured instruction moved from first position in the solo prompt to second position in the composed prompt:

| Checkpoint run | Position-shifted quantity | Estimate | Simultaneous 95% interval |
|---|---:|---:|---:|
| `gemma-3n-e4b-it` | $D(B\leftarrow A)$ | +0.2832 | [+0.2485, +0.3179] |
| `qwen3-4b` | $D(A\leftarrow B)$ | +0.3291 | [+0.2835, +0.3747] |

These are observed differences in verifier-defined compliance. Because composition and prompt position changed together, the paper must retain that caveat whenever reporting them.

The four intervals were licensed separately within one configuration of one checkpoint run. The analysis did not control error for a study-level conjunction across all four conditions. The paper therefore reports four separate findings rather than claiming a single 95% statement that a loss occurs across every configuration and checkpoint.

The identity and magnitude of the affected instruction vary across the observed cells. Those variations are descriptive. The study registered no direct cross-model or cross-configuration contrast, and the saved records do not contain the bootstrap draws needed to construct one retrospectively. The study also did not establish directional asymmetry: the relevant higher-level test was withheld in every configuration because its prerequisites were not met.

### Scientific contribution candidate 1: directional composition effects

The first candidate contribution is a precise, directional account of how adding one instruction changes compliance with another. Its strongest evidence is the pair of position-matched delivery-loss estimates above. The two position-shifted findings broaden the observed pattern but must remain explicitly position-confounded. Whether the directional, solo-anchored estimand is novel relative to prior work remains unresolved until the literature review is complete.

## Main identification result: no valid matched-companion estimate

The study attempted to form matched companion comparisons on four checkpoint runs. The confirmatory analysis required three admitted core references and the composed reference cells of the full design. The experimental outcomes were:

| Checkpoint run | Core references admitted | Design reached | Confirmatory outcome |
|---|---:|---|---|
| `gemma-3n-e2b-it` | 3 | Full, 47 cells | Stopped at composed-headroom validation before confirmatory generation |
| `qwen3-4b` | 2 | Reduced, 8 cells | Confirmatory generation completed, without reference-composition cells |
| `gemma-3n-e4b-it` | 0 | Reduced, 8 cells | Confirmatory generation completed, without reference-composition cells |
| `qwen3-4b-instruct-2507` | 0 | Reduced, 8 cells | Later stopped at headroom validation; the companion contrast was already unavailable |

Three experimental facts explain why no confirmatory companion estimate exists:

1. Three of the four runs admitted fewer than the required three core references.
2. The reduced design composed no reference cells, so it could not estimate reference-side delivery losses.
3. The only run that assembled the full design failed the composed-headroom criterion before confirmatory generation.

Consequently, six planned quantities have no interval anywhere in the study: $\Delta_R$, the per-reference contrast $\Delta_j$, the reciprocal-specificity contrast $\Xi$, the difficulty-adjusted contrast $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, and $D(R_j\leftarrow B)$. Each is `NOT_IDENTIFIED`, meaning that the study obtained no valid estimate.

The second headroom failure, on `qwen3-4b-instruct-2507`, is not an additional explanation for the missing companion estimate on that run. It occurred after reference admission had already returned zero core references. The paper should report the later stopping event without treating it as a cause of non-identification.

### What the later diagnostics show

Post-hoc diagnostics describe the reference pool that passed through the selection procedure. They do not establish which feature caused the companion comparison to fail or whether changing one rule would have repaired it.

First, the shortlisted candidate rungs were concentrated on the harder side of $A$ at calibration. Across the four runs, the study calibrated 84 shortlisted severity rungs, comprising 21, 20, 23, and 20 rungs from six budget-class families. Of these, 65 lay below $\iota_A$ and 19 above it. Eligible rungs strictly above $\iota_A$ numbered 2, 1, 1, and 0 across the four runs.

This **65/84 result concerns the shortlist, not the whole constraint library**. The pre-screen measured 254 eligible rungs per run from a 28-family population, then carried six reference families forward. The shortlist was also selected using pre-screen difficulty and described using calibration difficulty. For the same 84 rungs, the split changed from 54 below and 30 above at pre-screen to 65 below and 19 above at calibration. Fifty-one stayed below, 16 stayed above, 14 moved from above to below, and 3 moved from below to above. Thus 17 changed side, producing a net movement of 11 toward the harder side. Part of the observed calibration skew therefore reflects movement between measurement stages.

Second, proximity in point difficulty did not always yield sufficiently precise equivalence. Eighteen rungs lay inside the 0.10 calibration caliper. Nine were admitted and nine were refused. Of the nine refusals, **eight failed the precision criterion** because their Newcombe intervals did not intersect the registered ±0.05 equivalence region, while **one failed the pre-screen criterion**. The precision refusals describe uncertainty in the calibration sample of 96 solo topics with four draws each, rather than an immutable property of the library.

Third, the reference pool differed structurally from the focal instruction. Production-class families were excluded from the core pool before measurement, while $A$ was production-class. This is a scope restriction on what $\Delta_R$ would have meant. It was not a measured cause of the failure to obtain $\Delta_R$.

No sensitivity analysis shows that widening the caliper, changing the equivalence rule or admission order, lowering the headroom threshold, or admitting production-class references would have made the companion comparison identifiable. The registered selection procedure rules out discretionary cherry-picking under that procedure; it does not prove that the procedure was optimal.

### Scientific contribution candidate 2: matched-companion identification

The second candidate contribution is a documented case in which a difficulty-matched companion design failed to reach confirmatory estimation. The contribution consists of the observed experimental stopping points and the resulting absence of the planned estimates. The later diagnostics provide a descriptive account of the candidate pool and motivate improved designs. They are not causal explanations of non-identification. Whether prior composition benchmarks have already reported comparable reference-construction failures remains an open literature question.

## Why the two contributions belong together

The directional delivery-loss estimates answer a limited but important question: what changed when a second instruction was added? The missing matched-companion estimates mark the boundary of that answer: the study cannot say whether the particular companion caused the change beyond the generic burden of composition.

This yields a coherent paper if the distinction itself or one of the two empirical components is novel. The paper should therefore present the clean directional estimates and the failed companion identification as mutually constraining results, rather than converting the identification failure into a general claim about all reference libraries or all multi-instruction benchmarks.

## Supporting methodology and provenance

The deterministic verifiers, staged admission procedure, frozen analysis, masking, signed records, and evidence bundle support traceability. They should appear in Methods, Limitations, and the artifact statement rather than as a third scientific contribution.

Several qualifications must remain visible:

- Compliance is verifier-defined and was not independently human-validated.
- The 49,152 confirmatory rows come from two of four checkpoint runs, one focal instruction pair, load two, one topic space, and one decoding policy.
- The two surviving runs used different operating points and different class companions and should not be pooled as scientifically interchangeable replications.
- Cross-model and cross-configuration differences are descriptive unless directly tested.
- A live protocol objection remains: an earlier stopping rule can be read as requiring the study to halt after a failed criterion rather than adopt v4r4. The paper should report this objection without resolving it in its own favour.
- One emitted cross-configuration classification on `gemma-3n-e4b-it` was invalid under the registered member-wise reading; the unmasked result was not repaired. A separate classification on `qwen3-4b` was licensed for one member. Neither supports a study-wide replication claim.
- HMAC signatures under a researcher-held symmetric key support integrity against parties without that key. They do not establish authorship or prove that a record existed before unmasking.
- The post-hoc v5 development analysis may motivate a future design. Its thresholds were chosen after observing v4r4, so it is design fitting rather than validation.

## Claims the paper must not make

The paper does not establish:

- that $A$ or $B$ has a companion-specific interference effect;
- that companion identity does not matter;
- that the directional losses differ significantly across models or prompt orders;
- that the observed directional loss is asymmetric;
- that the excluded structural classes, a wider caliper, a different admission rule, or a different headroom threshold would have yielded an identifiable comparison;
- that the candidate library cannot support any executable matched-companion design;
- that the post-hoc attrition diagnostics caused non-identification;
- that the results generalise beyond the two analysed checkpoints and the tested task setting; or
- that the paper's novelty or final title has been established before the relevant literature review.

## What the reader should understand after reading this

The reader should understand that v4r4 provides two clean, position-matched estimates of composition-related delivery loss and two additional position-confounded estimates. The study did not obtain a valid difficulty-matched companion estimate, so it cannot attribute those losses to the particular companion instruction. The experimental stopping points establish why the planned estimates are absent; the later diagnostics describe the candidate pool without proving a causal explanation. The paper's final novelty claim and title remain open pending the literature review.
