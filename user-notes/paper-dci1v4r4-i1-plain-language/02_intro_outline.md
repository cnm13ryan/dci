# Introduction outline

## What this document is for

This document plans the paper's introduction paragraph by paragraph. The introduction should let a technically literate reader understand the problem, the identification gap, the main results, the two candidate contributions, and the limits of the evidence without knowing the DCI project or its internal protocol.

## Paragraph 1: the scientific problem and the answer in brief

Open with the practical setting: language models are routinely asked to satisfy several instructions in one response, yet compliance with one instruction may change when another is added. State the two questions a useful study must separate:

- Does adding a second instruction change compliance with the first?
- Is any change caused by the particular companion instruction, beyond the generic burden of satisfying two instructions?

Give the answer immediately. In v4r4, two position-matched solo-to-composed comparisons showed detectable delivery loss. Two additional comparisons also showed loss, but composition and prompt position changed together. The study did not obtain a valid difficulty-matched companion estimate, so it cannot attribute any loss to the identity of the companion instruction.

End on significance: a benchmark can measure a composition-related change while still failing to identify why that change occurred.

## Paragraph 2: what a solo-to-composed comparison measures

Introduce the directional delivery-loss quantity in ordinary language before notation. Let $c$ be the instruction being evaluated and $g$ the added instruction:

\[
D(c\leftarrow g)
=
P(c\text{ passes alone})
-
P(c\text{ passes when }g\text{ is also present}).
\]

Explain the sign. A positive value means verifier-defined compliance with $c$ is lower in the composed prompt; a negative value means it is higher. The direction matters because $D(A\leftarrow B)$ and $D(B\leftarrow A)$ need not agree.

State the identification boundary in the same paragraph. This comparison moves from one instruction to two. It therefore contains any generic composition cost and cannot show that the particular identity of $g$ caused the change.

## Paragraph 3: the comparison needed for companion-specific attribution

Explain the replacement logic. To ask whether companion $A$ affects target instruction $B$ more than another equally difficult companion would, compare two-instruction prompts on both sides:

\[
\Delta_R
=
D(B\leftarrow A)
-
\frac{1}{J}\sum_{j=1}^{J}D(B\leftarrow R_j).
\]

Define $R_j$ as an alternative companion and $\iota$ as a chance-corrected measure of instructed compliance used as a difficulty coordinate. Lower $\iota$ means lower compliance and therefore greater difficulty. A **matched reference** is an alternative whose measured difficulty lies sufficiently close to $A$, with uncertainty small enough to support the match.

Explain what $\Delta_R$ would and would not isolate. It holds instruction count fixed at two, but the v4r4 reference pool contained budget-form instructions while $A$ was production-form. Companion identity and structural class would therefore have changed together. The intended contrast was difficulty-matched, not structure-matched.

## Paragraph 4: the design needed to estimate the two questions

Define the two study designs without introducing internal gate labels. The **full design** contained 47 cells per block, including the reference-composition cells required for $D(B\leftarrow R_j)$, $\Delta_R$, and related companion-specific contrasts. The **reduced design** contained eight cells and omitted those reference compositions. It could estimate focal solo-to-composed delivery losses but could not estimate the matched-companion question.

Define position matching. In solo prompts, the measured instruction appeared first. A composed comparison is clean with respect to position only when that instruction remains first. If it appears second, composition and position change together. This distinction must precede the results because it determines which estimates support a composition-only interpretation.

## Paragraph 5: the matched-companion comparison was not estimated

Report the outcome in scientific terms. Four checkpoint runs attempted the design. The numbers of admitted core references were 3, 2, 0, and 0, against a requirement of three. The run with three references assembled the full 47-cell design but stopped at composed-headroom validation before confirmatory generation. The two runs that completed confirmatory generation used the eight-cell reduced design and contained no reference-composition cells. The fourth run had no core references before its later headroom failure.

Define `NOT_IDENTIFIED` explicitly: the study did not obtain a valid estimate. It is not evidence of a zero effect, no effect, or a failed significance test. Name the six quantities left without intervals: $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, and $D(R_j\leftarrow B)$.

End with the scientific implication: the study measured composition-related changes but did not identify companion-specific effects.

## Paragraph 6: what the reference diagnostics do and do not explain

Present the later diagnostics as descriptive context, separate from the experimental stopping points.

First, 65 of the 84 severity rungs calibrated after shortlisting lay below $\iota_A$, on the harder side. Eligible rungs strictly above $\iota_A$ numbered 2, 1, 1, and 0 across the four checkpoint runs. Carry both qualifications with the count:

- the 84 are shortlisted rungs from six budget-class families, pooled as 21, 20, 23, and 20 across runs; they are not the whole library, for which the pre-screen measured 254 eligible rungs per run;
- the shortlist was chosen using pre-screen difficulty and described using calibration difficulty. On the same 84 rungs, the split moved from 54 below and 30 above to 65 below and 19 above. Fourteen moved above-to-below and three below-to-above, so 17 changed side.

Second, of 18 rungs inside the 0.10 calibration caliper, nine were refused: eight by the precision criterion and one by the pre-screen criterion. The precision result partly reflects the calibration sample rather than a fixed property of the candidate library.

State the evidential limit directly. No sensitivity analysis establishes that changing the caliper, the admission procedure, the structural-class restriction, or the headroom threshold would have produced an identifiable companion comparison. These diagnostics describe the pool; they are not proven causal explanations.

## Paragraph 7: the directional composition results

Report the confirmatory evidence from the two surviving reduced-design runs. Together they produced 49,152 complete response rows and 20 interval-bearing estimates: 12 directional delivery-loss quantities and 8 derived contrasts.

Lead with the two position-matched findings:

- `gemma-3n-e4b-it`: $D(A\leftarrow B)=+0.1159$, simultaneous 95% interval [+0.0771,+0.1546];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3919$, simultaneous 95% interval [+0.3503,+0.4335].

Then give the position-shifted findings with the caveat in the same sentence:

- `gemma-3n-e4b-it`: $D(B\leftarrow A)=+0.2832$, [+0.2485,+0.3179];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3291$, [+0.2835,+0.3747].

Clarify the inferential grain. These are four separately licensed statements, not one study-wide 95% conjunction. Cross-model and cross-configuration differences are descriptive because the study did not directly test them. The study also did not establish directional asymmetry.

## Paragraph 8: the two candidate contributions

End the substantive introduction with two reader-facing contributions:

1. **Directional composition effects.** The paper quantifies how adding an instruction changes verifier-defined compliance with another, with simultaneous uncertainty intervals and an explicit separation between two clean position-matched estimates and two position-confounded estimates.
2. **Matched-companion identification.** The paper documents that the intended difficulty-matched companion comparison did not reach confirmatory estimation, distinguishes the actual experimental stopping points from later descriptive diagnostics, and names the companion-specific quantities for which no valid estimate exists.

State that provenance, masking, freezing, and staged execution support the credibility and traceability of these results. They are methodology and limitations rather than a third contribution.

## Paragraph 9: scope, novelty, and roadmap

Close with the boundaries that control the rest of the paper:

- the evidence comes from two analysed checkpoint runs, one focal instruction pair, load two, one topic space, one decoding policy, and deterministic verifiers that were not independently human-validated;
- the reference pool did not hold structural class fixed;
- no cross-model or cross-configuration difference was directly tested;
- `NOT_IDENTIFIED` is an absence of a valid estimate, not a null result;
- the post-hoc reference diagnostics do not establish causal explanations;
- novelty and the final title remain provisional until the relevant literature review is complete.

Provide a short roadmap: formalise the two estimands, position the work against prior instruction-composition studies, describe the full and reduced designs, present the directional results, explain the failed matched-companion identification, and conclude with limitations and requirements for a prospective follow-up.

## What the reader should understand after reading this

The reader should enter the paper knowing the central distinction between a solo-to-composed delivery change and a companion-specific effect. They should know that v4r4 found two clean position-matched losses, two additional position-confounded losses, and no valid matched-companion estimate. They should also understand that the later reference-pool diagnostics are descriptive, while the paper's novelty and final title remain open pending literature review.
