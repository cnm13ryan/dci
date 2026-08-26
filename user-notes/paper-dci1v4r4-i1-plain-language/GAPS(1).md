# Unresolved issues for the DCI v4r4 paper

## What this document is for

This document identifies the scientific, literature, writing, visualisation, and release issues that remain before the paper can be drafted and submitted. Each issue is stated in terms of why it matters for the paper's claims. Repository details appear only where they affect evidence or release readiness.

## Current position

The paper can already state two bounded results. First, two position-matched comparisons show composition-related delivery loss, while two position-shifted comparisons require an explicit position caveat. Second, the intended difficulty-matched companion comparison did not reach confirmatory estimation.

The principal unresolved question is whether either result constitutes a sufficiently distinct contribution relative to prior work. That literature question should be resolved before the title, headline figure, and full prose are fixed.

## Scientific issues that constrain the claims

### No valid companion-specific estimate

The study has no valid estimate of $\Delta_R$, $\Delta_j$, $\Xi$, $\delta_{\text{difficulty}}$, $D(B\leftarrow R_j)$, or $D(R_j\leftarrow B)$. The full reference design did not reach confirmatory analysis, and the reduced design omitted the required reference-composition cells.

**Why this matters.** The paper can quantify solo-to-composed changes. It cannot determine whether the particular companion instruction caused those changes beyond the generic cost of adding a second instruction.

**Required treatment.** Define `NOT_IDENTIFIED` as “the study did not obtain a valid estimate.” Never interpret it as zero or no effect. A valid companion-specific estimate requires a prospective design that carries suitable reference compositions through confirmatory generation.

### The reference comparison would not hold structural class fixed

The focal companion $A$ is production-form, while the permitted references are budget-form. The intended comparison would therefore change companion identity and structural class together.

**Why this matters.** Even a valid $\Delta_R$ from this design would identify excess effect relative to difficulty-matched budget-form companions, not an identity-only effect.

**Required treatment.** Present this as a scope restriction on the estimand. Do not treat structural exclusion as an observed cause of non-identification. A stronger future design would need structurally matched alternatives.

### No direct test of cross-model or cross-configuration differences

The study registered no contrast between checkpoint runs and no contrast between prompt configurations. Stored outputs do not contain the bootstrap draws needed to construct those tests retrospectively.

**Why this matters.** The observed losses differ in identity and magnitude across cells, but those differences are descriptive.

**Required treatment.** Avoid sentences such as “the effect differs by model” or “position significantly changes the effect.” State only the separately estimated results and their position status.

### No companion-specific quantity cleanly resolves position

The position-matched $D(A\leftarrow B)$ estimates cleanly compare solo and composed prompts with respect to position. The companion-specific quantities intended to separate identity from generic composition, including $\Delta_R$ and $\delta_{\text{difficulty}}$, were not estimated.

**Why this matters.** The paper has clean composition estimates, but it has no position-clean companion-specific estimate.

### The reference-pool diagnostics are post-hoc and descriptive

The shortlist distribution and the precision decomposition were computed after the main experiment from `02_admission_landscape.json`. They use the study's selection functions on signed calibration tables, but the aggregate diagnostic artifact itself is post-hoc.

**Why this matters.** These analyses describe why the candidate pool became small under the implemented rules. They do not prove that any single feature caused non-identification.

**Required treatment.** Keep three facts attached to the 65/84 result:

- 84 means the shortlisted rungs calibrated across four runs, not the whole library;
- the pre-screen measured 254 eligible rungs per run;
- the same 84 moved from 54 below and 30 above $\iota_A$ at pre-screen to 65 below and 19 above at calibration. Fourteen moved above-to-below, three moved below-to-above, and 17 changed side.

Also preserve the correct precision count: of 18 in-caliper rungs, nine were refused, eight by the precision criterion and one by the pre-screen criterion.

### No sensitivity analysis resolves the alternative explanations

Three plausible objections remain open:

| Open explanation | Analysis needed to address it | Current evidential status |
|---|---|---|
| The 0.10 calibration caliper was too narrow | Re-run reference selection under wider calipers and record what becomes admissible | Not run |
| The [0.05, 0.95] headroom band was too strict | Compute the minimum detectable effect and remaining informative headroom under alternative bands | Not run |
| The reference families were poorly chosen | Evaluate whether excluded production-form families could supply structurally and statistically acceptable references | Not run |

**Why this matters.** Registered selection prevents discretionary cherry-picking under the implemented procedure. It does not establish that the procedure was optimal or that changing it would have made $\Delta_R$ estimable.

### Confirmatory evidence comes from two checkpoint runs

Only `gemma-3n-e4b-it` and `qwen3-4b` produced confirmatory rows. The other two terminal outcomes provide no evidence about the magnitude of a composition effect.

**Why this matters.** Generalisation is limited to two checkpoint runs, one focal instruction pair, load two, one topic space, one decoding policy, and verifier-defined compliance.

### The measurement basis is not human-validated

The deterministic verifiers passed extensive consistency and reimplementation checks, but no independent human study validates that their pass/fail judgments capture the broader concept of instruction compliance.

**Why this matters.** Every empirical claim should say “verifier-defined compliance” where readers might otherwise infer a human judgment of success.

### The v5 development analysis is design fitting

The v5 reference-design report defines a pre-composition quantity (\kappa(R\mid B)), constructs a projection, and checks it against v4r4 outcomes after those outcomes were known. Its thresholds were fitted to the same evidence, and the comparison covers one full-design checkpoint run.

**Why this matters.** The report can motivate a prospective design. It does not validate the proposed predictor or thresholds.

**Required treatment.** Separate what v4r4 directly establishes, namely the shortlisted difficulty pattern and the observed headroom breach, from what v5 proposes. If the v5 report is removed, the motivating observations remain; the (\kappa)-based remedy does not.

## Literature and positioning issues

### Related work has not been written or verified

There is no completed Related Work draft or bibliography. The following questions need primary-source review:

| Literature question | Why it matters |
|---|---|
| How do existing multi-instruction benchmarks measure degradation as instruction count rises? | Establishes the broader problem and whether composition loss is already well characterised. |
| Does prior work use difficulty-matched companion replacement at fixed instruction count? | Determines the novelty of the matched-companion identification contribution. |
| Are prior interaction measures directional and solo-anchored, or symmetric and aggregate? | Determines the novelty of $D(c\leftarrow g)$. |
| How are instruction order and prompt position handled? | Prevents claiming or conceding novelty incorrectly. |
| What construct-validity requirements exist for matched controls? | Positions the structural and difficulty matching problem. |
| How should the block bootstrap, simultaneous intervals, Newcombe intervals, and multiplicity correction be attributed? | Required for accurate method citation. |
| How common is inspectable preregistration in comparable ML studies? | Optional context only; provenance is not a paper contribution. |

**Priority.** The first three questions are load-bearing. They determine whether v4r4 is a standalone paper, a methods-oriented negative result, or a diagnostic section of a later paper.

### Novelty and genre remain provisional

The two contribution candidates can stand independently. A known reference-construction problem would not eliminate a novel directional estimand, and a known directional estimand would not eliminate a novel matched-companion account. Only if both are already established does the standalone case weaken substantially.

**Required decision after the literature review.** Decide whether v4r4 should stand alone or be integrated into a prospective v5 paper.

### The final title remains open

The title should follow the contribution a reader ought to remember. It must not claim “instruction interference” as an identified effect. `TITLES.md` provides provisional options and a decision rule tied to the literature review.

## Writing and visualisation issues

### Headline figure depends on the final contribution emphasis

The clean directional estimates are ready to visualise. The identification display depends more strongly on whether the matched-companion account is novel.

**Action.** Build the main directional forest plot now if desired, but defer the final figure order and headline caption until Related Work is settled. All figures must distinguish position-matched from position-shifted evidence.

### The shortlist figure must show measurement-stage movement

A figure displaying only the calibration split of 65/19 would invite readers to interpret the skew as a fixed property of the library.

**Action.** Show pre-screen and calibration positions for the same rungs, or provide an equally visible annotation of 54/30 becoming 65/19 through 14 above-to-below and 3 below-to-above movements. Label the plot as a post-hoc diagnostic of shortlisted rungs.

### No decision on qualitative examples

No selection protocol for response examples is fixed.

**Why this matters.** Hand-picked examples could overstate a quantitative pattern.

**Action.** Either define a reproducible selection rule before examining examples or omit the qualitative appendix.

### Figure code and publication style remain to be created

No v4r4-specific figure scripts or plotting style exist.

**Action.** Build figures from stored estimates rather than recomputing estimands. Use embedded non-Type-3 fonts, colourblind-safe encodings, a second visual channel besides colour, and a grayscale legibility check.

## Release and traceability issues

### The release lacks a per-variable codebook

The released data do not yet have a table defining every variable's name, type, allowed values, units, causal role, and meaning.

**Why this matters.** This blocks release compliance and a complete reproducibility checklist, although it does not block prose drafting.

**Action.** Create a codebook covering at least `per_block_cell_means.csv` and every field used in the results table.

### A claim-supporting diagnostic sits outside the evidence bundle

`02_admission_landscape.json` supports both post-hoc reference diagnostics, the structural-class description, and the planned shortlist figure, but it is outside the current bundle.

**Action.** Add it to the next bundle revision with a clear post-hoc label and provenance note. Do not imply that its aggregate decompositions are themselves signed gate outcomes.

### Two terminal runs lack a successful headroom-stage record

The terminal runs have signed terminal reports rather than successful headroom-stage records. The reports contain the status, band, failures, and per-cell table needed by the paper.

**Why this matters.** This is an expected consequence of termination rather than lost evidence.

**Action.** Explain the record convention once in the methods appendix and cite the terminal reports for the results.

### Provenance coverage has defined limits

The bundle contains 53 present items, 3 derived items, and 6 missing items. The lifecycle summary covers records only through the pre-freeze stages. Later records require individual verification. The freeze commit has no external timestamped anchor, and HMAC signatures use a researcher-held symmetric key.

**Why this matters.** The records support internal consistency and integrity against parties without the key. They do not establish authorship or prove that a record existed before unmasking.

**Action.** State these limits in the artifact appendix. Publishing the commit or a timestamped digest would anchor the current state from publication onward; it cannot retroactively prove pre-unmask existence.

### A protocol-amendment objection remains live

An earlier protocol provision can be read as forbidding an amendment that weakens a criterion after that criterion fails. v4r4 was adopted after such a failure, so a reader can reasonably argue that the registered response was to halt.

**Why this matters.** The paper should not use its own protocol machinery as evidence of unusually strong commitment while leaving this objection unaddressed.

**Action.** Quote the relevant provision and state the sequence in Limitations. Record the objection without adjudicating it in the paper's favour.

### One emitted cross-configuration field is invalid under the intended reading

On `gemma-3n-e4b-it`, the emitter compared the set of attained levels rather than each named member across configurations. It emitted a replication-style field even though each named member changed classification. The registered member-wise reading invalidates that field. On `qwen3-4b`, one member's cross-configuration classification remains licensed.

**Action.** Report the defect and the registered interpretation in Limitations. Do not repair the unmasked output or make a study-wide replication claim.

### Known reproduction traps must remain excluded

- One internal report gives incorrect calipers of 0.075 and 0.10. The correct values are 0.10 and 0.15.
- Several constants contain stale comments. Library-size figures should come from verified coverage records.
- A reduced-design freeze record can list selected references even though no reference-composition estimand is identified.

**Action.** Record these cautions in a reproduction appendix and keep them out of the main scientific story.

## Prioritised next actions

| Priority | Action | Decision or deliverable unlocked |
|---:|---|---|
| 1 | Complete the primary-source literature review | Novelty, paper genre, standalone status, title, and final figure order |
| 2 | Decide whether to run the three sensitivity analyses | Stronger answers to alternative explanations |
| 3 | Fix the paper's final contribution emphasis and title | Stable abstract, introduction, and headline caption |
| 4 | Build figures and the full 20-estimate table | Results drafting |
| 5 | Decide on qualitative examples | Appendix scope |
| 6 | Add the post-hoc diagnostic to the evidence bundle and write the variable codebook | Release readiness |
| 7 | Publish a forward-looking provenance anchor if desired | Stronger public traceability from publication onward |
| 8 | Draft the full paper after the above framing decisions | Coherent prose without avoidable rewrites |

## What the reader should understand after reading this

The reader should understand which unresolved issues alter the scientific claims, which affect only writing or release, and what evidence would close each gap. The most consequential open work is the literature review and the decision about a prospective companion design. The current paper must keep companion non-identification, position confounding, structural mismatch, and post-hoc diagnostics explicit throughout.
