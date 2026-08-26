# Evidence map

## What this document is for

This document links every paper-level result and limitation to the quantitative evidence that supports it. It begins with the scientific meaning of each result and then gives the repository location needed for verification. Internal record names appear only to preserve traceability.

## How to read the evidence

For an instruction $c$ evaluated with companion $g$,

\[
D(c\leftarrow g)
=P(c\text{ passes alone})-P(c\text{ passes with }g).
\]

Positive values indicate lower verifier-defined compliance in composition. The study also reports two derived contrasts:

- $\Lambda=D(B\leftarrow A)-D(A\leftarrow B)$, a contrast between the two directional losses;
- $\Delta_{\text{class}}=D(B\leftarrow A)-D(B\leftarrow CL)$, a registered bound involving a class companion. It is not an estimate of a structural-class effect.

The 20 interval-bearing quantities below comprise **12 delivery-loss quantities** and **8 derived contrasts**. Simultaneous intervals are 95% studentised maximum-modulus intervals from 10,000 block-bootstrap resamples within each declared multiplicity family. Marginal intervals are 95% bootstrap percentile intervals. Cross-model and cross-configuration differences are descriptive because the study did not directly test them.

`NOT_IDENTIFIED` means that the study did not obtain a valid estimate. It does not mean zero, no effect, or non-significance.

## Headline scientific evidence

### Directional composition effects

| Evidential role | Checkpoint run | Quantity | Estimate | Simultaneous 95% interval | Interpretation |
|---|---|---:|---:|---:|---|
| Position-matched | `gemma-3n-e4b-it` | $D(A\leftarrow B)$ | +0.1159 | [+0.0771, +0.1546] | Compliance with $A$ was lower after adding $B$, with $A$ in the same prompt position. |
| Position-matched | `qwen3-4b` | $D(A\leftarrow B)$ | +0.3919 | [+0.3503, +0.4335] | Same interpretation at this checkpoint. |
| Position-shifted | `gemma-3n-e4b-it` | $D(B\leftarrow A)$ | +0.2832 | [+0.2485, +0.3179] | Composition and prompt position changed together. |
| Position-shifted | `qwen3-4b` | $D(A\leftarrow B)$ | +0.3291 | [+0.2835, +0.3747] | Composition and prompt position changed together. |

These are four separately licensed results. No multiplicity procedure covers their conjunction as one study-level 95% claim.

### Matched-companion identification

No checkpoint run produced a confirmatory estimate of the matched-companion quantities. One run admitted three core references and assembled the full design but stopped at composed-headroom validation. The other designs contained fewer than three core references and omitted the composed-reference cells required for the companion comparison.

## Complete table of the 20 interval-bearing estimates

The configuration names below are the stored record labels. Position interpretation should be attached to the four headline findings above rather than inferred from configuration names alone.

| Type | Quantity | Checkpoint run | Configuration | Estimate | Simultaneous 95% | Marginal 95% | Bootstrap SE | Source field |
|---|---|---|---|---:|---|---|---:|---|
| Delivery loss | $D(B\leftarrow A)$ | `gemma-3n-e4b-it` | `outcome_first` | +0.0062 | [-0.0182, +0.0306] | [-0.0143, +0.0267] | 0.0105 | `UA:e4b` → `payload.result.outcome_first.families.F1.members.D(B<-A)` |
| Delivery loss | $D(A\leftarrow B)$ | `gemma-3n-e4b-it` | `outcome_first` | +0.1159 | [+0.0771, +0.1546] | [+0.0833, +0.1481] | 0.0166 | `UA:e4b` → `payload.result.outcome_first.families.F1.members.D(A<-B)` |
| Derived contrast | $\Lambda$ | `gemma-3n-e4b-it` | `outcome_first` | -0.1097 | [-0.1546, -0.0648] | [-0.1478, -0.0723] | 0.0193 | `UA:e4b` → `payload.result.outcome_first.families.F1.members.Lambda` |
| Derived contrast | $\Delta_{\text{class}}$ | `gemma-3n-e4b-it` | `outcome_first` | -0.3102 | [-0.3498, -0.2706] | [-0.3464, -0.2738] | 0.0185 | `UA:e4b` → `payload.result.outcome_first.families.F9.members.Delta_class` |
| Delivery loss | $D(B\leftarrow CL)$ | `gemma-3n-e4b-it` | `outcome_first` | +0.3164 | [+0.2793, +0.3535] | [+0.2819, +0.3499] | 0.0173 | `UA:e4b` → `payload.result.outcome_first.families.F9.members.D(B<-CL)` |
| Delivery loss | $D(B\leftarrow A)$ | `gemma-3n-e4b-it` | `outcome_second` | +0.2832 | [+0.2485, +0.3179] | [+0.2542, +0.3125] | 0.0150 | `UA:e4b` → `payload.result.outcome_second.families.F1.members.D(B<-A)` |
| Delivery loss | $D(A\leftarrow B)$ | `gemma-3n-e4b-it` | `outcome_second` | -0.0322 | [-0.0734, +0.0089] | [-0.0664, +0.0026] | 0.0178 | `UA:e4b` → `payload.result.outcome_second.families.F1.members.D(A<-B)` |
| Derived contrast | $\Lambda$ | `gemma-3n-e4b-it` | `outcome_second` | +0.3154 | [+0.2594, +0.3714] | [+0.2673, +0.3630] | 0.0242 | `UA:e4b` → `payload.result.outcome_second.families.F1.members.Lambda` |
| Derived contrast | $\Delta_{\text{class}}$ | `gemma-3n-e4b-it` | `outcome_second` | -0.5114 | [-0.5495, -0.4733] | [-0.5443, -0.4775] | 0.0173 | `UA:e4b` → `payload.result.outcome_second.families.F9.members.Delta_class` |
| Delivery loss | $D(B\leftarrow CL)$ | `gemma-3n-e4b-it` | `outcome_second` | +0.7946 | [+0.7624, +0.8268] | [+0.7656, +0.8229] | 0.0146 | `UA:e4b` → `payload.result.outcome_second.families.F9.members.D(B<-CL)` |
| Delivery loss | $D(B\leftarrow A)$ | `qwen3-4b` | `outcome_first` | -0.1227 | [-0.1536, -0.0918] | [-0.1494, -0.0970] | 0.0133 | `UA:qwen` → `payload.result.outcome_first.families.F1.members.D(B<-A)` |
| Delivery loss | $D(A\leftarrow B)$ | `qwen3-4b` | `outcome_first` | +0.3919 | [+0.3503, +0.4335] | [+0.3564, +0.4264] | 0.0179 | `UA:qwen` → `payload.result.outcome_first.families.F1.members.D(A<-B)` |
| Derived contrast | $\Lambda$ | `qwen3-4b` | `outcome_first` | -0.5146 | [-0.5671, -0.4622] | [-0.5592, -0.4704] | 0.0225 | `UA:qwen` → `payload.result.outcome_first.families.F1.members.Lambda` |
| Derived contrast | $\Delta_{\text{class}}$ | `qwen3-4b` | `outcome_first` | +0.0114 | [-0.0106, +0.0334] | [-0.0078, +0.0309] | 0.0099 | `UA:qwen` → `payload.result.outcome_first.families.F9.members.Delta_class` |
| Delivery loss | $D(B\leftarrow CL)$ | `qwen3-4b` | `outcome_first` | -0.1341 | [-0.1647, -0.1035] | [-0.1611, -0.1074] | 0.0137 | `UA:qwen` → `payload.result.outcome_first.families.F9.members.D(B<-CL)` |
| Delivery loss | $D(B\leftarrow A)$ | `qwen3-4b` | `outcome_second` | -0.0120 | [-0.0450, +0.0209] | [-0.0404, +0.0160] | 0.0144 | `UA:qwen` → `payload.result.outcome_second.families.F1.members.D(B<-A)` |
| Delivery loss | $D(A\leftarrow B)$ | `qwen3-4b` | `outcome_second` | +0.3291 | [+0.2835, +0.3747] | [+0.2897, +0.3682] | 0.0200 | `UA:qwen` → `payload.result.outcome_second.families.F1.members.D(A<-B)` |
| Derived contrast | $\Lambda$ | `qwen3-4b` | `outcome_second` | -0.3411 | [-0.3989, -0.2834] | [-0.3906, -0.2913] | 0.0253 | `UA:qwen` → `payload.result.outcome_second.families.F1.members.Lambda` |
| Derived contrast | $\Delta_{\text{class}}$ | `qwen3-4b` | `outcome_second` | +0.0384 | [+0.0088, +0.0680] | [+0.0120, +0.0651] | 0.0134 | `UA:qwen` → `payload.result.outcome_second.families.F9.members.Delta_class` |
| Delivery loss | $D(B\leftarrow CL)$ | `qwen3-4b` | `outcome_second` | -0.0505 | [-0.0814, -0.0195] | [-0.0781, -0.0234] | 0.0140 | `UA:qwen` → `payload.result.outcome_second.families.F9.members.D(B<-CL)` |

The class companions differ across the two analysed runs: `CL7:80` for `gemma-3n-e4b-it` and `CX1:4` for `qwen3-4b`. The $\Delta_{\text{class}}$ values should therefore not be compared across runs.

## Companion-specific quantities without estimates

| Quantity | Scientific meaning | Why no valid estimate exists | Traceability |
|---|---|---|---|
| $\Delta_R$ | Excess effect of focal companion $A$ over the average difficulty-matched reference on target $B$ | Requires three core references and their composed cells. Three runs had fewer than three; the one full design stopped before confirmatory generation. | `FR` → `study_level_not_identified`; `G3:<model>` → `core_references`; `TERM:e2b` |
| $\Delta_j$ | Per-reference version of $\Delta_R$ | The reduced design contains no $B+R_j$ cells. | `FR`; `UA:<model>` family keys omit F2 |
| $\Xi$ | Reciprocal specificity using reference-side directional comparisons | The required reference-by-reference matrix is absent. | `FR`; `UA:<model>` family keys omit F4 |
| $\delta_{\text{difficulty}}$ | Delivery loss adjusted by a fitted difficulty relation | Requires straddling difficulty triples. Available triples were 3, 2, 0, and 0; no analysed full design remained. | `G3:<model>` → `identification_statuses`, `dropped_for_no_triple` |
| $D(B\leftarrow R_j)$ | Effect of reference $R_j$ on target $B$ | The reduced design did not compose references. | `FR`; `G5:qwen` records selected references under the reduced-design exemption |
| $D(R_j\leftarrow B)$ | Effect of $B$ on reference $R_j$ | The reduced design did not compose references. | `FR`; `UA:<model>` family keys omit F7 |

The study-level record states that these quantities are not null results, are not zero, and are not absent by accident. No post-hoc estimate exists.

## Experimental stopping points

These are observed outcomes from the signed execution records. They establish why the required cells did not enter confirmatory analysis.

| Checkpoint run | Admitted budget families | Straddling families | Core references | Design | Confirmatory outcome | Primary source |
|---|---:|---:|---:|---|---|---|
| `gemma-3n-e2b-it` | 4 | 3 | 3 | Full, 47 cells | Stopped at composed-headroom validation | `G3:e2b`; `TERM:e2b` |
| `qwen3-4b` | 2 | 2 | 2 | Reduced, 8 cells | Analysed without reference-composition cells | `G3:qwen`; `UA:qwen` |
| `gemma-3n-e4b-it` | 1 | 0 | 0 | Reduced, 8 cells | Analysed without reference-composition cells | `G3:e4b`; `UA:e4b` |
| `qwen3-4b-instruct-2507` | 1 | 0 | 0 | Reduced, 8 cells | Later stopped at headroom validation | `G3:qwen-instruct`; `TERM:qwen-instruct` |

On the two single-family runs, the admitted rung was at the top of its measured family ladder, so no rung existed above it to form a spectrum triple:

- `gemma-3n-e4b-it`: `RF9:13` at $\iota=0.7043$, with $\iota_A=0.6948$;
- `qwen3-4b-instruct-2507`: `RF7:24` at $\iota=0.5920$, with $\iota_A=0.5963$.

The second run's later headroom failure is not a cause of its companion non-identification because it already had zero core references.

## Post-hoc diagnostics of the reference pool

The aggregate decompositions below come from `ADM`, a post-hoc diagnostic computed using the registered selection functions on signed calibration tables. The primary admission outcomes also appear in the signed reference-admission records. These diagnostics describe the pool; no ablation establishes that any one feature caused non-identification.

| Diagnostic | Quantity | Result | Scientific qualification |
|---|---|---|---|
| Structural scope | Production-class families excluded before reference measurement | 4 of 10 families on `gemma-3n-e2b-it`, `gemma-3n-e4b-it`, and `qwen3-4b-instruct-2507`; 3 of 9 on `qwen3-4b` | $A$ is production-class while references are budget-class. This limits what $\Delta_R$ would mean; it is not a demonstrated cause of non-identification. |
| Shortlisted difficulty distribution | Calibrated rungs below/above $\iota_A$ | 65/19 of 84 pooled. Per run: 14/7, 14/6, 19/4, 18/2. | The 84 are shortlisted rungs, not the whole library. |
| Eligible support above $\iota_A$ | Eligible rungs strictly above target difficulty | 2, 1, 1, and 0 across the four runs | Descriptive. No counterfactual shows that this scarcity bound the design. |
| Caliper misses, conditional on refusal | Refused rungs below/above $\iota_A$ | 58/8 of 66. Per run: 11/2, 14/3, 16/1, 17/2. | The denominator is already the refused set. This is not the share of the library that is harder. |
| Shortlist population | What the 84 represent | 21 + 20 + 23 + 20 severity rungs from six budget-class families across four runs | The same families recur at run-specific difficulty values. They are not 84 distinct constraint families. |
| Pre-screen population | Funnel above the shortlist | 254 eligible rungs measured per run from 28 families; 67, 69, 73, and 46 were eligible reference rungs across 18, 18, 18, and 17 families | The 65/84 result must never be described as a whole-library rate. |
| Measurement-stage movement | Same 84 rungs at pre-screen versus calibration | 54/30 below/above became 65/19. Fifty-one stayed below, 16 stayed above, 14 moved above-to-below, and 3 below-to-above. | Seventeen changed side; 14 is only the one-way count. Part of the calibration skew reflects measurement-stage movement. |
| In-caliper admission | Rungs within the 0.10 calibration caliper | 18 total: 9 admitted and 9 refused | Of the 9 refused, 8 failed the Newcombe precision criterion and 1 failed the pre-screen criterion. |
| Precision basis | Sample supporting Newcombe intervals | 96 solo topics with 4 draws each | Precision failure partly reflects the calibration sample. |
| Pooled refusal reasons | Counts across all four runs | difficulty distance 66; pre-screen distance 47; Newcombe interval 42; eligibility band 7; solo vacuity 2 | Reasons can overlap. Wording, witness, and parse-independence criteria rejected none. |
| Leave-one-family-out margin | Families whose removal breaks the availability condition | 3, 0, 4, and 4 for e2b, e4b, qwen, and qwen-instruct | Three of four runs had no margin under this diagnostic; this does not identify a causal bottleneck. |

### Composed-headroom observations

On `gemma-3n-e2b-it`, five evaluated cell-slots involving `RF11:26` or `RF11:32` composed with $B$ fell outside the [0.05, 0.95] headroom band, with rates from 0.9583 to 1.0000. For the clearest example, `RF11:26` measured 0.6875 in solo calibration and 0.9688 when composed with $B$.

On `qwen3-4b-instruct-2507`, the single failure was different: the class companion's solo rate was 0.9896. It did not create that run's companion non-identification because no core references had already been admitted.

No minimum detectable effect was computed for the headroom band, so the study does not establish that the threshold was scientifically optimal.

## Supporting data quality and provenance

These quantities support trust and traceability. They are methodology and limitations rather than headline contributions.

| Quantity | Result | Source |
|---|---|---|
| Confirmatory rows | 24,576 per analysed run; 49,152 total; 0 missing, duplicated, or unexpected | `CONFIRMATORY_GENERATION.signed_record.json` → `payload.completeness` |
| Blocks and draws | 384 blocks, 8 draws per cell | `UA:<model>`; `paper/v4r4_bundle/tier2_data/per_block_cell_means.csv` |
| Operating points | `gemma-3n-e4b-it`: $n^*/m^*=4/10$; `qwen3-4b`: $n^*/m^*=2/12$ | `G2:<model>` → `n_star`, `m_star` |
| Realised simultaneous half-widths | 0.0244 to 0.0577; all precision preconditions met | `UA:<model>` |
| Calibration responses read during measurement validation | 36,000 | `G1D` → `calibration_responses` |
| Deterministic measurement checks | Agreement 1.0 across 3 processes and 400 responses | `G1D` → `determinism` |
| Independent verifier reimplementation | Agreement 1.0 across 36,164 responses and 650,952 statistic comparisons; 0 failures | `G1D` → `reimplementation` |
| Witness checks | 92,148 pairs; 0 joint-satisfiability or non-entailment failures | `G1D` → `witnesses` |
| Boundary suite | 164 cases, 1,280 checks; 0 failures | `G1D` → `suites` |
| Instrument population | 524 | `G1D` → `instrument_population` |
| Measurement basis | `deterministic_measurement_validated`, never human-validated | `G1D` → `measurement_basis` |
| Freeze commit | `450a0499e05fc780d20b8f3a8139a2879a8589c2` on both analysed runs | `G5:<model>` → `producing_commit` |
| Frozen fields | 66 of 66 present; 2 empty under declared reduced-design exemptions | `G5:<model>` |
| Analysis computation | Code hash `dffb5a861a497cc24e57017d4c97b4260dccb03dc29063fb3c02fca46bc7e9ca` in masked and unmasked records; bit-identical recomputation on both analysed runs | `MA:<model>` and `UA:<model>` |
| Masked artifact hash agreement | Prefix `6ca030d9` for e4b and `3368b857` for qwen, matching between masked and unmasked records | `MA:<model>` and `UA:<model>` |
| Pre-specified alternative scoring | Vacuity-forced, graded-0.99, and vacuity-gate result families are stored with the main analysis | `UA:<model>` → families F5 and F6 |
| Structurally unmaskable groups | 4 outcome-by-configuration groups on the reduced design, including $D(A\leftarrow B)$ | `MA:<model>` → `mask_effectiveness.structurally_unmaskable` |
| Derived block-mean dataset | 11,520 rows, 384 blocks per analysed run, 8 draws recorded on every row | `paper/v4r4_bundle/tier2_data/per_block_cell_means.csv` |
| Evidence bundle inventory | 53 present, 3 derived, 6 missing, 0 oversize; signature and content-hash checks passed | `paper/v4r4_bundle/MANIFEST.md` |
| Evidence bundle archive | 688,939 bytes; SHA-256 `8d8826b61bac15778fd581f55462418c76d8407af8f75bddae65b5a36b813b68` | `paper/v4r4_bundle.tar.gz` |
| Bundle manifest hash | SHA-256 `528701fc90de8b7fb30a306ae09812f02853bbe22c52114bf30e5251bae49019` | `paper/v4r4_bundle/MANIFEST.md` |

The HMAC signatures use a symmetric key held by the researcher. They support integrity against parties without that key, but they do not prove authorship or temporal precedence. The lifecycle summary covers records only through the pre-freeze stages; later records must be verified individually.

## Source key and record hashes

| Tag | Artifact |
|---|---|
| `UA:e4b` | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` |
| `MA:e4b` | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/MASKED_ANALYSIS.signed_record.json` |
| `UA:qwen` | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` |
| `MA:qwen` | `paper/v4r4_bundle/tier0_results/qwen3-4b/MASKED_ANALYSIS.signed_record.json` |
| `G1D` | `paper/v4r4_bundle/tier1_protocol_and_gates/reports/gate1_decision.json` |
| `G2:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/GATE_2_OPERATING_POINT.signed_record.json` |
| `G3:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/GATE_3_REFERENCES.signed_record.json` |
| `G5:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/GATE_5_FREEZE.signed_record.json` |
| `TERM:<model>` | `paper/v4r4_bundle/tier1_protocol_and_gates/<model>/terminal_report.json` |
| `FR` | `paper/v4r4_bundle/tier0_results/final_results.json` |
| `COV` | `paper/v4r4_bundle/tier1_protocol_and_gates/reports/coverage.json` |
| `ADM` | `dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json` |

| Record | Full `record_hash` |
|---|---|
| `UA:e4b` | `1dbebbe2a02a1eedb5b3df7f77232ca516f71fda253bb7414ef0bd0e73a04372` |
| `MA:e4b` | `a02d1ecd569dcd75f4007e136679d5fc887173403e203d680737a27724599e7b` |
| `UA:qwen` | `8de80e4eb032eee9e8900669437c00987dd194f971c64301fd6810fa63b3237c` |
| `MA:qwen` | `5f21738f936db719cb47ec5e8188578503fbfc3d7de31c88f7309b1e3f49268e` |

`final_results.json` is unsigned. Its SHA-256 begins `c8f3a2e3942e8f62`, and every reported value used here is also present in the signed analysis or execution records.

## Values and interpretations that must be excluded

- The correct calibration and pre-screen calipers are **0.10 and 0.15**. The values 0.075 and 0.10 in one internal follow-up report are erroneous; 0.075 entered no selection.
- Library-size figures must come from `COV` or `G1D`, not stale comments in constants modules. The supported figures are 254 eligible pre-screen rungs per checkpoint run, 28 families in the population, and 524 verifier instruments.
- The phrase “20 delivery-loss estimates” is incorrect. The correct split is 12 delivery losses and 8 derived contrasts.
- The statement that both single-family runs had no eligible rung above $\iota_A$ is incorrect. `gemma-3n-e4b-it` had one such rung; both single-family runs failed to form a spectrum because their admitted core rung was the top of the measured family ladder.
- The phrase “9 of 18 were refused by the Newcombe criterion” is incorrect. Nine were refused in total: eight by Newcombe precision and one by the pre-screen criterion.
- The phrase “14 rungs crossed sides” is incorrect. Fourteen moved above-to-below, three moved below-to-above, and 17 changed side in total.

## What the reader should understand after reading this

The reader should be able to trace every quantitative claim to its source while retaining its scientific meaning. The evidence supports two clean position-matched delivery losses, two additional position-confounded losses, and 16 other interval-bearing quantities. It does not contain valid estimates for six companion-specific quantities. The experimental stopping points establish why those estimates are absent; the later shortlist, precision, and headroom diagnostics remain descriptive and do not prove what change would have made the comparison identifiable.
