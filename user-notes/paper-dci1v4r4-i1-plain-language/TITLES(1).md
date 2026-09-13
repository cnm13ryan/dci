# Provisional title options

## What this document is for

This document evaluates titles by the scientific contribution a reader should remember. No title is final until the literature review determines whether the distinctive contribution is the directional composition result, the matched-companion identification account, or their combination.

## What the title must communicate

The current paper has a bounded result and a bounded limitation:

- adding a second instruction was associated with detectable delivery loss in two clean position-matched comparisons, with two further position-confounded findings;
- the study obtained no valid difficulty-matched companion estimate, so it cannot attribute the loss to the particular companion instruction.

An effective title should therefore be:

1. **Contribution-led.** It should name the scientific idea or result a reader can reuse.
2. **Accurate.** It must not claim that companion-specific “interference” was identified.
3. **Legible without project context.** Avoid `DCI`, `v4r4`, $\Delta_R$, internal design labels, and repository language.
4. **Calibrated to the evidence.** Avoid implying broad generality across models, tasks, or reference libraries.
5. **Memorable.** Prefer a short phrase that remains clear in a citation list.
6. **Stable under review.** The title should survive the paper's principal limitation rather than conceal it.

## Current leading option: balanced across both contributions

> **Composed Instructions: Directional Losses Without Companion-Specific Estimates**

**What the reader remembers.** The paper measures directional composition-related losses and draws a firm boundary around companion-specific attribution.

**Strengths.** It is concise, cold-readable, and scientifically accurate. “Without companion-specific estimates” describes the evidential state without treating non-identification as no effect. It avoids protocol-centred language.

**Risk.** “Directional losses” may already be well established in prior work, while “companion-specific estimates” may sound technical. The literature review must determine whether the two-part framing reflects a genuine contribution.

**Current status.** Best provisional title because it captures both candidate contributions. It is not final.

## Directional-result option

> **Directional Compliance Losses Under Instruction Composition**

**What the reader remembers.** The paper quantifies whose compliance changes when instructions are combined.

**Strengths.** Short, precise, and focused on the clean empirical result. “Directional” distinguishes $D(A\leftarrow B)$ from $D(B\leftarrow A)$.

**Risk.** It omits the paper's central identification limit and may overstate the breadth of the empirical result, which rests on two analysed checkpoint runs and one instruction pair. Use this option only if the literature review establishes the directional estimand as the stronger novel contribution.

## Identification-led option

> **What Solo-to-Composed Comparisons Leave Unidentified**

**What the reader remembers.** A solo-to-composed difference cannot, on its own, identify the effect of a particular companion.

**Strengths.** Conceptually memorable and directly tied to the paper's identification argument. It avoids presenting the missing companion estimate as a null result.

**Risk.** The subject matter is not fully cold-readable: the title does not say “instructions” or “language models.” It also sounds general, while v4r4 establishes the limitation for one implemented design. A scoped variant is safer:

> **Composed Instructions: What Solo-to-Composed Comparisons Leave Unidentified**

Use this family only if the literature review establishes the identification distinction as the more reusable contribution.

## Empirical-result option in plain language

> **Adding an Instruction Can Reduce Compliance with Another**

**What the reader remembers.** Composition can lower delivery of an existing instruction.

**Strengths.** Accessible, direct, and faithful to the two position-matched findings. “Can” makes an existence claim rather than a universal claim.

**Risk.** It hides the matched-companion limitation and could be read as broader than two checkpoint runs and one focal pair. It also says little about what the paper adds if composition loss is already well documented.

## Matched-companion option

> **Matched Companions for Studying Composed Instructions**

**What the reader remembers.** Companion-specific attribution requires an explicit alternative-companion comparison.

**Strengths.** Focuses on the design principle and remains understandable without internal notation.

**Risk.** It sounds like a successful methods paper, while v4r4 did not carry the matched-companion comparison through to estimation. A more accurate but less elegant variant is:

> **Matched Companions for Composed Instructions: An Unestimated Contrast**

This title family should be used only if prior work leaves a clear methodological gap and the paper can articulate a contribution beyond documenting one failed implementation.

## Titles to avoid

- **Directional Constraint Interference in Composed Instructions.** This asserts the companion-specific phenomenon the study did not identify.
- **Instruction Interference Across Models and Prompt Orders.** Cross-model and cross-configuration differences were not directly tested.
- **A Preregistered Study of Instruction Interference.** It foregrounds protocol rather than contribution and still implies identified interference.
- **Why Matched Controls Fail.** The study shows that this procedure failed to produce a confirmatory matched comparison. It does not establish a general failure of matched controls.
- **Four Filters for Measuring Instruction Interference.** The evidence does not support a homogeneous four-filter taxonomy or universal necessary conditions.
- **Composition Costs Delivery: Evidence from 49,152 Generations.** The row count is supporting evidence rather than the contribution, and the title omits the identification boundary.
- **DCI-1 or v4r4** in any title. These are internal project labels with no value to a new reader.

## Decision rule after the literature review

| Literature outcome | Title emphasis |
|---|---|
| Directional, solo-anchored per-instruction loss is novel; matched-companion difficulty is known | Use the directional-result family. |
| Matched-companion identification problem is novel; directional loss is known | Use the identification-led family. |
| Both are distinct | Use the balanced leading option. |
| Neither is distinct | Reconsider a standalone v4r4 paper and integrate the study into a prospective follow-up. |

The final title should also be checked against the completed abstract. If the title promises a design contribution, the abstract must state the reusable design insight. If it promises an empirical result, the abstract must lead with the two position-matched estimates and state the missing companion comparison immediately.

## What the reader should understand after reading this

The reader should understand why no title is final yet, which scientific contribution each candidate foregrounds, and which formulations would overclaim. The current balanced leader is **Composed Instructions: Directional Losses Without Companion-Specific Estimates**, subject to revision after the literature review.
