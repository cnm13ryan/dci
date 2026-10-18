# Figure and table plan

## What this document is for

This document specifies the scientific takeaway, visual form, source data, and interpretive boundary for every planned display. The figures should help a reader understand the results and their limitations. They should not reproduce the experiment's internal workflow or elevate provenance machinery into a headline contribution.

## Display strategy

The main paper needs three visual moves:

1. show the directional composition effects and separate position-matched evidence from position-confounded evidence;
2. show why the matched-companion question has no confirmatory estimate;
3. show what the post-hoc reference diagnostics describe, while preventing readers from treating them as proven causal explanations.

The final ordering may change after the literature review establishes which contribution is most distinctive. The scientific content of each display can be specified now.

## Figure 1. Directional delivery losses under instruction composition

### Scientific takeaway

Two solo-to-composed delivery losses are cleanly position-matched. Two further losses are interval-separated from zero but composition and prompt position change together.

### Form

Use a two-panel forest plot:

- **Panel A: position-matched estimates.** One row for each analysed checkpoint run.
- **Panel B: position-shifted estimates.** One row for each analysed checkpoint run, with the panel title “Composition and position change together.”

The horizontal axis is the change in verifier-defined compliance, $D(c\leftarrow g)$. Draw a zero line. Plot point estimates with simultaneous 95% intervals. Use marker shape and panel placement to encode position status. Do not connect checkpoint runs or draw a pooled estimate.

### Values

| Panel | Checkpoint run | Quantity | Estimate | Simultaneous 95% interval |
|---|---|---:|---:|---:|
| Position-matched | `gemma-3n-e4b-it` | $D(A\leftarrow B)$ | +0.1159 | [+0.0771, +0.1546] |
| Position-matched | `qwen3-4b` | $D(A\leftarrow B)$ | +0.3919 | [+0.3503, +0.4335] |
| Position-shifted | `gemma-3n-e4b-it` | $D(B\leftarrow A)$ | +0.2832 | [+0.2485, +0.3179] |
| Position-shifted | `qwen3-4b` | $D(A\leftarrow B)$ | +0.3291 | [+0.2835, +0.3747] |

### Interpretation guardrails

- Positive values are solo-to-composed delivery losses. They do not identify a companion-specific effect.
- The four results are separately licensed; the figure must not imply a single multiplicity-controlled four-cell conjunction.
- Rows may share an axis for readability, but no visual connector or annotation should imply a tested cross-model difference.
- The panel labels must make the position caveat readable without consulting the caption.

### Source

`EVIDENCE_MAP.md`, headline table and complete 20-estimate table; signed unmasked analysis records under `paper/v4r4_bundle/tier0_results/<model>/`.

### Draft caption

“Adding a second instruction reduced verifier-defined compliance in two position-matched comparisons (left). Two additional losses were observed when the measured instruction also moved from first to second position (right), so composition and position change together in those conditions. Points show directional solo-to-composed differences and bars show simultaneous 95% intervals from 10,000 block-bootstrap resamples; no pooled or cross-checkpoint comparison is estimated.”

## Figure 2. Availability of the matched-companion estimate

### Scientific takeaway

None of the four checkpoint runs carried the difficulty-matched companion comparison through to confirmatory estimation. The two analysed runs used a reduced design without reference-composition cells.

### Form

Use an **estimand-availability matrix**, not a gate-flow diagram. Rows are checkpoint runs. Columns answer four scientific questions:

1. Were three core references available?
2. Did the design include reference-composition cells?
3. Did the run reach confirmatory analysis?
4. Does a valid $\Delta_R$ interval exist?

Show the number of admitted references in the first column, “full” or “reduced” in the second, and a clearly labelled status in the third and fourth. Use symbols plus text, so colour is never the sole channel.

Below the matrix, include a narrow band listing the six planned quantities without estimates: $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, and $D(R_j\leftarrow B)$. Draw no point at zero. Label the band “No valid estimate obtained.”

### Values

| Checkpoint run | Core references | Design | Confirmatory result | Companion-specific interval |
|---|---:|---|---|---|
| `gemma-3n-e2b-it` | 3 | Full, 47 cells | Stopped at composed-headroom validation | None |
| `qwen3-4b` | 2 | Reduced, 8 cells | Analysed | None |
| `gemma-3n-e4b-it` | 0 | Reduced, 8 cells | Analysed | None |
| `qwen3-4b-instruct-2507` | 0 | Reduced, 8 cells | Later stopped at headroom validation | None |

### Interpretation guardrails

- “None” means `NOT_IDENTIFIED`: no valid estimate exists. It must not be encoded as a point at zero.
- The later headroom failure on `qwen3-4b-instruct-2507` did not cause its missing companion estimate; the run already had zero core references.
- The figure shows the outcome of this procedure on this library. It does not show that the library could never support another executable design.
- Internal gate numbers can appear in a footnote for traceability. They should not structure the visual.

### Source

Signed reference-admission records, signed terminal reports, signed unmasked analysis records, and `final_results.json`; exact paths in `EVIDENCE_MAP.md`.

### Draft caption

“No checkpoint run produced a confirmatory matched-companion estimate. One run assembled the full 47-cell design but stopped before confirmatory generation; two analysed runs used the eight-cell reduced design without reference compositions; the fourth run had no core references before its later stopping event. The six quantities shown below the matrix have no markers because the study obtained no valid estimate of them.”

## Figure 3. What the post-hoc reference diagnostics describe

### Scientific takeaway

The shortlisted reference pool shifted toward the harder side between pre-screen and calibration, precision excluded eight otherwise in-caliper candidates, and one admitted reference breached composed headroom. These observations describe the implemented design; they are not proven causes of non-identification.

### Form

Use a three-panel composite with a shared label across the top: **“Post-hoc diagnostics; descriptive, not causal.”**

### Panel A: shortlisted difficulty support

Use four small multiples, one per checkpoint run. The horizontal axis is $\iota$, with lower values labelled “harder.” For every shortlisted rung:

- plot the pre-screen value as a faint open marker;
- plot the calibration value as a filled marker;
- connect the same rung with a thin line;
- draw $\iota_A$ at both stages;
- shade the ±0.10 calibration caliper;
- use marker shape for admission or refusal status.

Annotate each panel with the number of eligible calibrated rungs strictly above $\iota_A$: 2, 1, 1, and 0. Also show the pooled change from 54 below/30 above at pre-screen to 65 below/19 above at calibration, with 14 above-to-below and 3 below-to-above movements. State that 17 rungs changed side.

The subtitle must read “84 shortlisted rungs calibrated across four runs.” The words “whole library” or an unqualified “measured rungs” must not appear. A footnote should state that the pre-screen measured 254 eligible rungs per run before six reference families were shortlisted.

### Panel B: proximity and precision

Use a compact count display for the 18 candidates inside the 0.10 calibration caliper:

- 9 admitted;
- 8 refused by the Newcombe precision criterion;
- 1 refused by the pre-screen criterion.

Avoid a pie chart. Use three aligned bars or unit counts so the denominator and categories remain exact. Note that the Newcombe intervals were based on 96 solo topics with four draws.

### Panel C: composed-headroom observation

Use a slope plot for `gemma-3n-e2b-it`. Plot solo calibration on the left and the corresponding composed rate on the right for each evaluated reference slot. Shade the accepted [0.05, 0.95] band. Emphasise the five failing slots involving the `RF11` family.

Label the clearest case directly: `RF11:26`, 0.6875 solo to 0.9688 composed with $B$. Add a separate inset for `qwen3-4b-instruct-2507` showing its distinct solo class-companion failure at 0.9896. Do not merge that outcome with the composed-reference breach.

### Interpretation guardrails

- Panel A concerns shortlisted rungs, not the full library.
- The shift between measurement stages is part of the result and should be visible in the plot rather than hidden in the caption.
- Panel B must preserve the 8-plus-1 refusal decomposition.
- Panel C requires composed cells and is therefore different from the pre-composition diagnostics in Panels A and B.
- No arrow, causal label, or funnel should imply that these observations caused non-identification.
- No caption should claim that changing a threshold would have produced a valid companion estimate; no such sensitivity analysis exists.

### Source

Panels A and B: post-hoc `02_admission_landscape.json`, with its registered-function provenance noted. Panel C: signed operating-point records and signed terminal reports. Exact fields are listed in `EVIDENCE_MAP.md`.

### Draft caption

“Post-hoc diagnostics describe the reference pool without establishing why the companion comparison failed. Across 84 shortlisted rungs, the pre-screen split of 54 below and 30 above target difficulty became 65 below and 19 above at calibration, with 17 rungs changing side $A$. Of 18 candidates inside the calibration caliper, nine were admitted, eight failed the precision criterion, and one failed the pre-screen criterion $B$. In the only full design to reach composed-headroom validation, `RF11:26` moved from 0.6875 solo compliance to 0.9688 when composed with $B$, above the 0.95 ceiling (C).”

## Table 1. Complete interval-bearing results

### Scientific takeaway

The confirmatory analysis contains 20 interval-bearing quantities: 12 directional delivery losses and 8 derived contrasts.

### Structure

Rows are checkpoint run × configuration × quantity. Columns are:

- quantity type: delivery loss or derived contrast;
- estimate;
- simultaneous 95% interval;
- marginal 95% interval;
- bootstrap standard error;
- position status for the headline focal finding in that condition;
- whether the relevant confirmatory statement was licensed.

Use four decimal places and tabular numerals. Do not use colour. Source the table directly from `EVIDENCE_MAP.md` and the signed analysis records.

## Table 2. Companion-specific quantities without estimates

### Scientific takeaway

Six planned companion-specific quantities have no valid estimate, and the missing design component is known for each.

### Structure

Rows are $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, and $D(R_j\leftarrow B)$. Columns are:

- plain-language scientific meaning;
- required comparison;
- missing cell or support;
- status: `NOT_IDENTIFIED`;
- primary source.

Include the sentence: “No valid estimate was obtained; this is not evidence of no effect.”

## Table 3. Reference support across checkpoint runs

### Scientific takeaway

Reference admission produced one full design and three reduced designs; the full design stopped before confirmatory generation.

### Structure

Rows are checkpoint runs. Columns are $\iota_A$, admitted families, straddling families, core references, full or reduced design, confirmatory status, and one-sentence reason. This table provides exact values behind Figure 2 without reproducing internal workflow labels.

## Appendix table. Measurement and provenance support

### Scientific takeaway

Deterministic measurement, frozen computation, completeness checks, and record verification support traceability, with explicit limits on what signatures and masking establish.

### Content

Include verifier agreement, independent reimplementation counts, witness and boundary-suite checks, instrument population, confirmatory row completeness, analysis-code hash agreement, structurally unmaskable groups, bundle inventory, and the coverage boundary. Keep full hashes and repository paths in the appendix or evidence map.

This display supports Methods and Limitations. It is not a scientific contribution.

## Production requirements for every figure

- **No new estimand computation.** Read point estimates and intervals from stored records or `EVIDENCE_MAP.md`. Figure code may reshape data but must not recompute scientific quantities.
- **Embedded fonts.** Set PDF and PostScript font types to 42 or use a LaTeX backend. Validate the packaged paper with `pdffonts`; no Type 3 row may remain.
- **Accessible encoding.** Use a colourblind-safe palette and a second channel such as marker shape, line style, or direct labels. No red-green-only distinctions.
- **Grayscale test.** Every display must remain interpretable after desaturation.
- **Deployment-size check.** Inspect each figure at its final single-column or full-width size.
- **No implied unsupported comparisons.** Avoid connecting checkpoint estimates, pooled summaries, or visual rankings that suggest tested cross-model or cross-configuration differences.
- **Caption order.** Lead with the scientific takeaway, then explain the setup, then state the evidential boundary.

## Displays deliberately omitted

- No plot of all 11,520 derived block-cell means. It would encourage readers to infer estimands from a verification dataset.
- No pooled cross-model effect plot. The study did not estimate such a contrast.
- No workflow diagram centred on internal gate numbers. Figure 2 communicates estimand availability directly.
- No figure claiming a causal decomposition of reference attrition. The necessary sensitivity analyses were not run.
- No exploratory-arm figure. It uses a different constraint vocabulary and lies outside this paper.

## What the reader should understand after reading this

The reader should understand what each display is meant to teach and which interpretations it must prevent. Figure 1 communicates the directional composition results, Figure 2 communicates the absence of a valid matched-companion estimate, and Figure 3 communicates the descriptive reference diagnostics without turning them into causal explanations. The tables preserve all quantitative detail and traceability.
