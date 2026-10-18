# Current paper-planning iteration

## What this document is for

This document records the current scientific position of the DCI v4r4 paper, the major corrections that now govern the narrative, the decisions that remain open, and the next actions. It replaces the earlier pass-by-pass audit history with a concise account of what the paper can presently claim.

## Current scientific position

The study asks what happens when a language model must satisfy two instructions simultaneously. It separates two questions:

1. How does compliance with one instruction change when another is added?
2. Does the particular companion instruction cause a change beyond the generic burden of satisfying two instructions?

The study obtained a bounded answer to the first question and no valid estimate for the second.

### What was estimated

Two checkpoint runs completed confirmatory generation under the reduced eight-cell design, producing 49,152 complete response rows. The analysis contains 20 interval-bearing quantities: 12 directional delivery losses and 8 derived contrasts.

The two clean position-matched results are:

- `gemma-3n-e4b-it`: $D(A\leftarrow B)=+0.1159$, simultaneous 95% interval [+0.0771,+0.1546];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3919$, [+0.3503,+0.4335].

Two additional interval-separated losses are position-shifted:

- `gemma-3n-e4b-it`: $D(B\leftarrow A)=+0.2832$, [+0.2485,+0.3179];
- `qwen3-4b`: $D(A\leftarrow B)=+0.3291$, [+0.2835,+0.3747].

The first pair supports clean solo-to-composed delivery-loss estimates with prompt position held fixed. In the second pair, composition and prompt position change together. All four are separately licensed statements; there is no study-level multiplicity-controlled conjunction.

### What was not estimated

The study did not obtain a valid estimate of the difficulty-matched companion comparison $\Delta_R$ or five related reference-side quantities. One checkpoint run admitted the required three core references and assembled the full 47-cell design, but it stopped at composed-headroom validation before confirmatory generation. The remaining runs used reduced designs that omitted reference-composition cells; two reached analysis and one later stopped.

`NOT_IDENTIFIED` therefore means “the study did not obtain a valid estimate.” It is not evidence of a zero or absent companion effect.

### Current contribution candidates

1. **Directional composition effects.** Quantify how adding one instruction changes verifier-defined compliance with another, with explicit separation of two position-matched estimates from two position-confounded estimates.
2. **Matched-companion identification.** Document why the intended difficulty-matched companion comparison did not reach confirmatory estimation, separating experimental stopping points from later descriptive diagnostics.

Provenance, freezing, masking, staged execution, and signed records support methodology and traceability. They are not a third scientific contribution.

## Essential concepts now fixed across the planning package

- $D(c\leftarrow g)$ is solo compliance with $c$ minus compliance with $c$ when $g$ is added. It changes instruction count from one to two.
- $\iota$ is the chance-corrected instructed-compliance coordinate used to represent difficulty. Lower $\iota$ means greater difficulty.
- A matched reference $R_j$ is an alternative companion selected to be close to $A$ on $\iota$, with adequate precision.
- $\Delta_R=D(B\leftarrow A)-J^{-1}\sum_jD(B\leftarrow R_j)$ compares two-instruction conditions and therefore holds instruction count fixed.
- The reference pool is budget-form while $A$ is production-form. $\Delta_R$ would match difficulty but not structural class.
- The full 47-cell design contains the reference compositions required for companion-specific estimates. The reduced eight-cell design does not.
- A position-matched estimate keeps the measured instruction in the same prompt position in solo and composed conditions. A position-shifted estimate changes composition and position together.
- `NOT_IDENTIFIED` records the absence of a valid estimate, not evidence of no effect.

## Major corrections that govern the paper

The following corrections are now incorporated across the narrative, introduction, paper outline, evidence map, figure plan, title options, and gaps register.

| Earlier problem | Correct scientific treatment |
|---|---|
| Describing $D(c\leftarrow g)$ as holding instruction count fixed | $D$ moves from one instruction to two. Only the companion-replacement contrast holds count fixed. |
| Attributing all four detected losses to composition alone | Two are position-matched; two also change the measured instruction's position. |
| Calling all 20 interval-bearing quantities delivery-loss estimates | Twelve are delivery losses and eight are derived contrasts. |
| Treating four separate findings as one study-level conjunction | Report four separately licensed statements. No procedure controls the four-cell conjunction. |
| Interpreting the absence of $\Delta_R$ as a null result | State that no valid estimate was obtained. |
| Claiming the library could not support any full design | One run assembled the full design, and another reached two of the required three references. This procedure did not carry a valid comparison through; general impossibility is unproven. |
| Treating all stopping events as causes of non-identification | Use only the actual temporal stopping points. The later headroom failure on the zero-reference run was not a cause of its missing companion estimate. |
| Presenting reference diagnostics as causal bottlenecks | Label them post-hoc and descriptive. No sensitivity analysis shows that relaxing one would identify $\Delta_R$. |
| Describing 65/84 as a whole-library result | The 84 are shortlisted calibrated rungs. The pre-screen measured 254 eligible rungs per run. |
| Reporting the shortlist skew as fixed | The same 84 moved from 54/30 below/above at pre-screen to 65/19 at calibration. Fourteen moved above-to-below, three below-to-above, and 17 changed side. |
| Attributing all 9 of 18 in-caliper refusals to precision | Eight failed the precision criterion; one failed the pre-screen criterion. |
| Saying both single-family runs had no eligible rung above $\iota_A$ | `gemma-3n-e4b-it` had one. Both runs failed to form a spectrum because their core rung was at the top of the measured family ladder. |
| Saying the companion comparison changes only identity | It also changes structural class because production-form references were excluded. This is a scope restriction, not a demonstrated cause. |
| Inferring model or prompt-order effects from differences between estimates | Cross-model and cross-configuration differences remain descriptive unless directly tested. |
| Treating provenance as a headline contribution | Keep it in Methods, Limitations, and the artifact statement. |
| Treating adoption of v4r4 as procedurally uncontroversial | Preserve the live objection that an earlier stopping rule may have required halting after the failed criterion. Report it without resolving it in the paper's favour. |
| Treating researcher-held HMAC signatures as proof of temporal priority | They support integrity against parties without the key, not authorship or pre-unmask existence. |
| Presenting the v5 development analysis as validation | It is design fitting conducted after v4r4 outcomes were known. It motivates prospective work. |

These corrections narrow the interpretation. They do not change any estimate, interval, or experimental stopping outcome.

## Current state of the planning materials

| Document | Current purpose |
|---|---|
| `01_narrative.md` | Contribution-led scientific story and claim boundaries |
| `02_intro_outline.md` | Introduction organised as problem → identification gap → result → contributions → limits |
| `03_paper_outline.md` | Section-by-section plan centred on the scientific question each section answers |
| `EVIDENCE_MAP.md` | All quantitative evidence and exact traceability |
| `GAPS.md` | Remaining scientific, literature, writing, visualisation, and release issues |
| `FIGURE_PLAN.md` | Result-led figures and tables with interpretive guardrails |
| `TITLES.md` | Contribution-based title options and a post-literature decision rule |

The planning package is ready for literature positioning and figure construction. Full prose, final title, and final figure order remain deliberately open.

## Unresolved decisions

### Literature scope and novelty

The primary-source review must determine:

- whether prior composition studies estimate directional, solo-anchored per-instruction loss;
- whether any use difficulty-matched companion replacement at fixed instruction count;
- how position and order effects are already treated;
- which construct-validity principles apply to companion controls.

This decision determines the paper's novelty, genre, title, and whether v4r4 should stand alone.

### Standalone v4r4 paper or diagnostic section of v5

The two contribution candidates should be assessed independently. If either is distinct, v4r4 may support a standalone paper. If both are already established, its strongest role may be as the diagnostic motivation for a prospective design that successfully estimates the companion contrast.

### Additional sensitivity analyses

Three possible reanalyses remain open:

1. reference re-selection under wider difficulty calipers;
2. a minimum-detectable-effect analysis for the headroom band;
3. evaluation of excluded production-form families as possible structurally matched references.

None has been run. Each answers a different objection and must remain absent from the paper unless completed and clearly labelled.

### Qualitative examples

Decide whether response examples materially improve understanding. If included, define a reproducible selection rule before choosing examples. Otherwise remove the qualitative appendix.

### Final shortlist visualisation

The preferred Figure 3 design shows both pre-screen and calibration difficulty for the same 84 rungs. This makes the 54/30 to 65/19 movement visible and reduces the risk that readers interpret calibration skew as a fixed library property.

### Release preparation

Open release tasks are:

- write a per-variable codebook;
- add `02_admission_landscape.json` to the evidence bundle with a post-hoc label;
- document why terminal reports replace successful headroom-stage records for stopped runs;
- preserve the lifecycle coverage boundary and known stale-value cautions;
- decide whether to publish a forward-looking external anchor for the current artifacts.

## Next steps

The recommended order is:

1. **Complete the literature review** using primary sources.
2. **Decide the paper's contribution emphasis and standalone status.**
3. **Decide whether any sensitivity analyses will be added.**
4. **Fix the final title and display order.**
5. **Build the three planned figures and the complete results tables.**
6. **Draft the paper from the contribution-led narrative and outline.**
7. **Complete the codebook, bundle update, and artifact statement before release.**

## Evidence and traceability snapshot

The planning documents were grounded in repository commit `3d57ad2cd93321658f20d1afa87420205d89fc59` and rechecked against a later state that did not alter v4r4 artifacts or these paper files. The evidence bundle reports 53 present items, 3 derived items, 6 missing items, and no oversize items. All available signature and content-hash checks passed.

One claim-supporting file, `dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json`, currently sits outside the bundle. It supports the post-hoc shortlist and precision diagnostics and should be added before release. Its aggregate decompositions must remain labelled post-hoc.

The clean v5 reference-design report is tracked, but its analysis remains design fitting because it was developed after observing v4r4. Other modified v5 files should not be cited without an explicit version and status check.

## What the reader should understand after reading this

The reader should understand the paper's present scientific position, the corrections that now constrain every claim, and the decisions required before prose drafting. The empirical result is a set of directional composition-related losses with two clean position-matched estimates. The intended matched-companion comparison has no valid estimate, and the later reference diagnostics remain descriptive. Literature positioning is the next decisive step.
