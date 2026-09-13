# EVIDENCE_MAP

Every claim-supporting number in the outline, with its source. Commit `3d57ad2`;
bundle `paper/v4r4_bundle/` (MANIFEST: 53 PRESENT, 3 DERIVED, 6 MISSING, 0
OVERSIZE, all signature and content-hash checks passing).

**Record hashes.** The `record_hash` field of each signed record, truncated to
16 hex characters. In full:

| record | record_hash |
|---|---|
| `gemma-3n-e4b-it` UNMASKED_ANALYSIS | `1dbebbe2a02a1eedb5b3df7f77232ca516f71fda253bb7414ef0bd0e73a04372` |
| `gemma-3n-e4b-it` MASKED_ANALYSIS | `a02d1ecd569dcd75f4007e136679d5fc887173403e203d680737a27724599e7b` |
| `qwen3-4b` UNMASKED_ANALYSIS | `8de80e4eb032eee9e8900669437c00987dd194f971c64301fd6810fa63b3237c` |
| `qwen3-4b` MASKED_ANALYSIS | `5f21738f936db719cb47ec5e8188578503fbfc3d7de31c88f7309b1e3f49268e` |

`final_results.json` is an unsigned report; it carries a sha256 of
`c8f3a2e3942e8f62…` recorded in `paper/v4r4_bundle/inventory.json`, and every
value in it also appears in the signed records above.

---

## Table 1 — the twenty interval-bearing estimates

**Twelve are delivery-loss quantities and eight are derived contrasts.** Per
checkpoint run × configuration the five members are `D(B<-A)`, `D(A<-B)` and
`D(B<-CL)` — primitive `D(c←g)` quantities — plus `Lambda` = `D(B<-A)` −
`D(A<-B)` and `Delta_class` = `D(B<-A)` − `D(B<-CL)`, which are contrasts of
those. Over four cells that is 12 and 8. The paper must not describe all twenty
as delivery-loss estimates.

All from the signed UNMASKED_ANALYSIS records. Simultaneous intervals are 95%
studentised maximum-modulus over 10,000 block-bootstrap resamples within the
declared multiplicity family; marginal intervals are percentile at the same
resample count; the standard error is the bootstrap standard deviation.

| claim | quantity | model | configuration | value | simultaneous 95% | marginal 95% | bootstrap SE | source path | field path | record hash |
|---|---|---|---|---:|---|---|---:|---|---|---|
| C1 | `D(B<-A)` | `gemma-3n-e4b-it` | outcome_first | +0.0062 | [-0.0182, +0.0306] | [-0.0143, +0.0267] | 0.0105 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.D(B<-A)` | `1dbebbe2a02a1eed…` |
| C1 | `D(A<-B)` | `gemma-3n-e4b-it` | outcome_first | +0.1159 | [+0.0771, +0.1546] | [+0.0833, +0.1481] | 0.0166 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.D(A<-B)` | `1dbebbe2a02a1eed…` |
| C1 | `Lambda` | `gemma-3n-e4b-it` | outcome_first | -0.1097 | [-0.1546, -0.0648] | [-0.1478, -0.0723] | 0.0193 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.Lambda` | `1dbebbe2a02a1eed…` |
| C1 | `Delta_class` | `gemma-3n-e4b-it` | outcome_first | -0.3102 | [-0.3498, -0.2706] | [-0.3464, -0.2738] | 0.0185 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F9.members.Delta_class` | `1dbebbe2a02a1eed…` |
| C1 | `D(B<-CL)` | `gemma-3n-e4b-it` | outcome_first | +0.3164 | [+0.2793, +0.3535] | [+0.2819, +0.3499] | 0.0173 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F9.members.D(B<-CL)` | `1dbebbe2a02a1eed…` |
| C1 | `D(B<-A)` | `gemma-3n-e4b-it` | outcome_second | +0.2832 | [+0.2485, +0.3179] | [+0.2542, +0.3125] | 0.0150 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.D(B<-A)` | `1dbebbe2a02a1eed…` |
| C1 | `D(A<-B)` | `gemma-3n-e4b-it` | outcome_second | -0.0322 | [-0.0734, +0.0089] | [-0.0664, +0.0026] | 0.0178 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.D(A<-B)` | `1dbebbe2a02a1eed…` |
| C1 | `Lambda` | `gemma-3n-e4b-it` | outcome_second | +0.3154 | [+0.2594, +0.3714] | [+0.2673, +0.3630] | 0.0242 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.Lambda` | `1dbebbe2a02a1eed…` |
| C1 | `Delta_class` | `gemma-3n-e4b-it` | outcome_second | -0.5114 | [-0.5495, -0.4733] | [-0.5443, -0.4775] | 0.0173 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F9.members.Delta_class` | `1dbebbe2a02a1eed…` |
| C1 | `D(B<-CL)` | `gemma-3n-e4b-it` | outcome_second | +0.7946 | [+0.7624, +0.8268] | [+0.7656, +0.8229] | 0.0146 | `paper/v4r4_bundle/tier0_results/gemma-3n-e4b-it/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F9.members.D(B<-CL)` | `1dbebbe2a02a1eed…` |
| C1 | `D(B<-A)` | `qwen3-4b` | outcome_first | -0.1227 | [-0.1536, -0.0918] | [-0.1494, -0.0970] | 0.0133 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.D(B<-A)` | `8de80e4eb032eee9…` |
| C1 | `D(A<-B)` | `qwen3-4b` | outcome_first | +0.3919 | [+0.3503, +0.4335] | [+0.3564, +0.4264] | 0.0179 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.D(A<-B)` | `8de80e4eb032eee9…` |
| C1 | `Lambda` | `qwen3-4b` | outcome_first | -0.5146 | [-0.5671, -0.4622] | [-0.5592, -0.4704] | 0.0225 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F1.members.Lambda` | `8de80e4eb032eee9…` |
| C1 | `Delta_class` | `qwen3-4b` | outcome_first | +0.0114 | [-0.0106, +0.0334] | [-0.0078, +0.0309] | 0.0099 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F9.members.Delta_class` | `8de80e4eb032eee9…` |
| C1 | `D(B<-CL)` | `qwen3-4b` | outcome_first | -0.1341 | [-0.1647, -0.1035] | [-0.1611, -0.1074] | 0.0137 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_first.families.F9.members.D(B<-CL)` | `8de80e4eb032eee9…` |
| C1 | `D(B<-A)` | `qwen3-4b` | outcome_second | -0.0120 | [-0.0450, +0.0209] | [-0.0404, +0.0160] | 0.0144 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.D(B<-A)` | `8de80e4eb032eee9…` |
| C1 | `D(A<-B)` | `qwen3-4b` | outcome_second | +0.3291 | [+0.2835, +0.3747] | [+0.2897, +0.3682] | 0.0200 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.D(A<-B)` | `8de80e4eb032eee9…` |
| C1 | `Lambda` | `qwen3-4b` | outcome_second | -0.3411 | [-0.3989, -0.2834] | [-0.3906, -0.2913] | 0.0253 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F1.members.Lambda` | `8de80e4eb032eee9…` |
| C1 | `Delta_class` | `qwen3-4b` | outcome_second | +0.0384 | [+0.0088, +0.0680] | [+0.0120, +0.0651] | 0.0134 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F9.members.Delta_class` | `8de80e4eb032eee9…` |
| C1 | `D(B<-CL)` | `qwen3-4b` | outcome_second | -0.0505 | [-0.0814, -0.0195] | [-0.0781, -0.0234] | 0.0140 | `paper/v4r4_bundle/tier0_results/qwen3-4b/UNMASKED_ANALYSIS.signed_record.json` | `payload.result.outcome_second.families.F9.members.D(B<-CL)` | `8de80e4eb032eee9…` |

**Reading note.** `Delta_class` = `D(B<-A)` − `D(B<-CL)` and is registered as a
*bound* on how much companion structural class could matter, never as an
estimate of a class effect. The two checkpoint runs' class companions are not the
same kind of constraint — `CL7:80` on `gemma-3n-e4b-it` and `CX1:4` on
`qwen3-4b` [`G3:<model>` → `class_companion`] — so the two `Delta_class` columns
are not comparable to each other, and the paper does not compare them.

---

## Table 2 — the six NOT_IDENTIFIED estimands

Source for the study-level list: `paper/v4r4_bundle/tier0_results/final_results.json`
→ `study_level_not_identified` and `analysed.<model>.not_identified`. Source for
the per-model reason: the signed Gate-3 records and the admission landscape.

Families **F2, F3, F4, F7 and F8 exist in no configuration of either survivor**
[`UA:<model>` → `payload.result.<configuration>.families`; keys present are F1,
F5, F6, F9 only]. These five families are where the six estimands below live.

| estimand | family | gate that failed to identify it | measured reason |
|---|---|---|---|
| `Delta_R` | F1 | GATE_3_REFERENCES | Requires three admitted core references. Admitted: `gemma-3n-e2b-it` 3 (full design), `qwen3-4b` 2, `gemma-3n-e4b-it` 0, `qwen3-4b-instruct-2507` 0 [`ADM` → `n_core_references`]. The one checkpoint run with three was ended at GATE_4_COMPOSED_HEADROOM before generating a confirmatory row [`TERM:gemma-3n-e2b-it` → `status`]. Recorded as `EXCESS_NOT_IDENTIFIED` on all three reduced checkpoint runs [`G3:<model>` → `identification_statuses`]. |
| `Delta_j` | F2 | GATE_3_REFERENCES | Per-reference contrast `D(B<-A)` − `D(B<-R_j)`; needs at least one admitted reference in the running design. The reduced design of §8.6 composes no reference cell, so F2 is absent from every configuration. |
| `Xi` | F1 | GATE_3_REFERENCES | Reciprocal specificity needs the reference-side matrix `D(Rbar<-A)` and `D(Rbar<-Rbar')`, which live in F4. F4 is absent from every configuration. |
| `delta_difficulty` | F1 | GATE_3_REFERENCES | Needs a fitted difficulty relation over straddling spectrum triples. Triples available: `gemma-3n-e2b-it` 3, `qwen3-4b` 2, `gemma-3n-e4b-it` 0, `qwen3-4b-instruct-2507` 0 [`ADM` → `spectrum_triples_available`]. Recorded as `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` [`G3:<model>` → `identification_statuses`]. On the two models with zero, the sole admitted family could not straddle ι_A — `RF9` and `RF7` respectively [`G3:<model>` → `dropped_for_no_triple`]. |
| `D(B<-R_j)` | F2 | GATE_3_REFERENCES | The reduced design has no `R_j` cell to compose. `qwen3-4b` selected `RF11:21` and `CR5:8` at Gate 3 [`G3:qwen3-4b` → `core_references`], and §8.6's reduced design never composed them, so the field is populated on the freeze record while the estimand stays unidentified [`G5:qwen3-4b` → `core_references`, with the declared exemption `core_references → EXCESS_NOT_IDENTIFIED` for the `reduced` variant]. |
| `D(R_j<-B)` | F7 | GATE_3_REFERENCES | Same cause as `D(B<-R_j)`; F7 is the reference-as-outcome family and is absent from every configuration. |

**The registered sentence that must accompany this table**, quoted verbatim from
`final_results.json` → `not_identified_note`:

> these are registered quantities this design does not identify. They are not
> null results, not zero, and not missing by accident, and no post-hoc estimate
> of them exists

---

## Table 3 — the C2 attrition counts

**Provenance, stated once.** The **gate outcomes** in rows 5 and 5b are on signed
Gate-3 records. The **aggregate decompositions** in rows 1, 2a–2c, 3 and 6 come
from `02_admission_landscape.json`, a post-hoc diagnostic outside the evidence
bundle whose verdicts were computed with the registered `stages.selection`
functions on the signed Gate-2 tables. The paper must not describe the
decompositions as "recorded in the signed gate records".

| # | component | quantity | value | source |
|---|---|---|---|---|
| 1 | structural-class scope restriction — **not a cause of non-identification** | production-class families refused from the core pool before measurement | 4 of 10 on `gemma-3n-e2b-it`, `gemma-3n-e4b-it`, `qwen3-4b-instruct-2507` (`CL7`, `CL8`, `CX1`, `CX2`); 3 of 9 on `qwen3-4b` (`CL7`, `CX1`, `CX2`) | `ADM` → `models.<model>.families.<F>.refused_before_measurement` |
| 2a | ladder skew, **unconditional** — report this first | the rungs Gate 2 calibrated, by side of ι_A | 84 total: **65 below ι_A, 19 above**. Per checkpoint run (below/above): e2b 14/7, e4b 14/6, qwen3-4b 19/4, qwen-instruct 18/2 | `ADM` → `...rungs[*].iota` vs `models.<model>.iota_a` |
| 2b | eligible rungs strictly above ι_A | how few sat above the target — **descriptive; no counterfactual shows this is what bound the design** | **2, 1, 1, 0** on e2b, e4b, qwen3-4b, qwen-instruct | `ADM` → `...rungs[*].iota`, `.admissible_13_4` |
| 2c | caliper misses, **conditional on refusal** — secondary, label as conditional | rungs refused for lying outside the 0.10 ι-caliper, split by side of ι_A | 66 total: **58 below ι_A, 8 above**. Per model (below/above): e2b 11/2, e4b 14/3, qwen3-4b 16/1, qwen-instruct 17/2. The denominator is the refused set, so this is not the share of the library that is harder | `ADM` → `...rungs[*].distance_from_iota_A`; caliper from `thresholds.REFERENCE_CALIPER` = 0.1 |
| 2d | **what the 84 are** — mandatory whenever 65/84 is quoted | the population the skew is measured on | The severity rungs of the six budget-class families §12.3 shortlisted on each checkpoint run, pooled over four runs: **21 + 20 + 23 + 20 = 84**. Six families with rungs on every run; the class families (`CL`/`CX`) carry none, being refused from the core pool before measurement. Not 84 distinct constraints — the same family recurs across runs at a run-specific ι | `ADM` → `models.<model>.families.<F>.rungs`; family counts recomputed per run |
| 2e | how the 84 relate to the measured library | the funnel above the shortlist | Pre-screen (`REGIME_SCREEN`) measured **254 eligible rungs per checkpoint run** from a **28-family** population (2 removed in v4r4), of which **67 / 69 / 73 / 46** were eligible as reference rungs across **18 / 18 / 18 / 17** families. §12.3 carries **6** reference families forward to Gate-2 calibration. **65/84 is a statement about the shortlist, never about the 254** | `COV` → `models.<model>.eligible_rungs_measured`, `support.eligible_reference_rungs`, `support.core_reference_availability`, `population.families` |
| 2f | the shortlist is not skewed by construction | why 65/84 is not an artefact of selection | §12.3 picks, per family, the rung nearest ι_A, the eligible rung nearest ι_A − 0.20, **the eligible rung nearest ι_A + 0.20**, and the second-nearest to ι_A — so a slot above *A* is reserved wherever the pre-screen has one. The skew is therefore measured on a set built to reach above *A* | `dci1v4r4.stages.regime.shortlist`; offsets from `ADM` → `thresholds.SPECTRUM_OFFSET` = 0.2 |
| 2g | caveat that must travel with 65/84 | the shortlist was chosen at pre-screen ι and re-measured at calibration ι | On the **same 84 rungs**, the pre-screen split is **54 below / 30 above** ι_A and the Gate-2 calibration split is **65 below / 19 above**. The full transition: **51 stayed below, 16 stayed above, 14 moved above→below, 3 moved below→above — 17 rungs changed side**, netting the 11 that turns 54 into 65. Per checkpoint run (above→below / below→above): e2b 4/2, e4b 3/1, qwen3-4b 2/0, qwen-instruct 5/0. **14 is the one-way count, never the total that crossed.** Part of the measured skew is this pre-screen-to-calibration shift, not a fixed property of the library, and the paper says so wherever the count appears | `ADM` → `...rungs[*].prescreen_iota` vs `models.<model>.prescreen_iota_a`, and `...rungs[*].iota` vs `.iota_a`; recounted independently |
| 3 | equivalence precision | rungs inside the 0.10 caliper, and why the refused ones were refused | 18 inside, 9 admitted, **9 refused**. Of the 9 refused, **8 by the Newcombe interval not intersecting ±0.05** (e2b 4, e4b 1, qwen3-4b 3, qwen-instruct 0) and **1 on the pre-screen caliper alone** — `RF11:26` on `gemma-3n-e4b-it`, whose only recorded reason is `pre-screen distance 0.197 above the 0.15 caliper` | `ADM` → `...rungs[*].rejection_reasons`, `.newcombe_interval`, `.admissible_13_4`; region from `thresholds.REFERENCE_NEWCOMBE_REGION` = 0.05 |
| 3b | calibration sample | the sample the Newcombe intervals were formed on | 96 solo topics at `M_CAL` = 4 | `ADM` → `thresholds.N_SOLO`, `.M_CAL` |
| 4 | composed ceiling | failing cell-slots at Gate 4, with rates and band | `gemma-3n-e2b-it`: 5 failures, 0.9583–1.0000, all involving `RF11:26` (`R3`) or `RF11:32` (`R3+`) composed with *B*. `qwen3-4b-instruct-2507`: 1 failure, `solo:CL` at 0.9896. Band [0.05, 0.95] | `TERM:<model>` → `failures`, `band`; slot identities from `G3:gemma-3n-e2b-it` → `slot_map` |
| 4b | the shift that produced it | `RF11:26` solo vs composed | 0.6875 at calibration → 0.9688 composed with *B* | `G2:gemma-3n-e2b-it` → `calibration_table` (`kind` `RF11`, `severity` 26, `solo_compliance`); `TERM:gemma-3n-e2b-it` → `failures` |
| 5 | admission outcome | admitted budget families / straddling / core references / design | e2b 4/3/3/full · qwen3-4b 2/2/2/reduced · e4b 1/0/0/reduced · qwen-instruct 1/0/0/reduced | `ADM` → `families.<F>.admitted`, `.can_straddle_A`, `n_core_references`, `design_variant`; `G3:<model>` |
| 5b | why the single-family checkpoints could not straddle | the admitted rung was the top of its family's measured ladder | e4b: `RF9` rungs at ι 0.4270 / 0.5396 / 0.5907 / **0.7043**, admissible rung `RF9:13` = 0.7043 is the highest, ι_A = 0.6948. qwen-instruct: `RF7` rungs at 0.3646 / 0.4256 / 0.4644 / **0.5920**, admissible rung `RF7:24` = 0.5920 is the highest, ι_A = 0.5963. The spectrum needs eligible rungs on both sides of the **core rung**, and neither family has one above it | `ADM` → `models.<model>.families.<F>.rungs`; `G3:<model>` → `dropped_for_no_triple` |
| 6 | pooled rejection reasons | across all four checkpoint runs | ι distance above the caliper 66; pre-screen distance above its caliper 47; Newcombe interval missing the region 42; ι outside the eligibility band 7; solo vacuity 2. The wording caliper, the witnesses and parse independence rejected nothing | `ADM` → `...rungs[*].rejection_reasons`, recounted independently; the same five counts appear in `dci1/reports/dci1v5/reference_design_development.md` §5.1 |
| 7 | thin margin | families whose removal breaks C4 | 3 load-bearing on `gemma-3n-e2b-it`, 4 on `qwen3-4b`, 4 on `qwen3-4b-instruct-2507`, **0 on `gemma-3n-e4b-it`** | `COV` → `models.<model>.leave_one_family_out.load_bearing_families` |

---

## Table 4 — provenance and integrity counts *(was: the C3 device counts)*

| quantity | value | source |
|---|---|---|
| Gate 1 registered conditions | 10 | `G1D` → `measurement_rule.conditions` |
| final instrument population | 524 | `G1D` → `instrument_population`, `instruments` |
| determinism | agreement 1.0, 3 processes, 400 responses, identical digests | `G1D` → `determinism` |
| independent reimplementation | agreement 1.0, 36,164 responses, 650,952 statistic comparisons, 0 failures | `G1D` → `reimplementation` |
| witnesses | 92,148 pairs, 0 joint-satisfiability and 0 non-entailment failures | `G1D` → `witnesses` |
| frozen boundary suite | 164 cases, 1,280 checks, 0 failures | `G1D` → `suites` |
| calibration responses read by Gate 1 | 36,000 | `G1D` → `calibration_responses` |
| measurement basis | `deterministic_measurement_validated` | `G1D` → `measurement_basis` |
| freeze commit | `450a0499e05fc780d20b8f3a8139a2879a8589c2` on both survivors | `G5:<model>` → `producing_commit` |
| §18.1 fields bound | 66 of 66 present; 2 empty by declared exemption on the `reduced` variant (`core_references → EXCESS_NOT_IDENTIFIED`, `spectrum_severities → DIFFICULTY_SUPPORT_NOT_IDENTIFIED`) | `G5:<model>`; field list `dci1v4r4.stages.freeze.FREEZE_FIELDS` (33 + 32 + 1) |
| analysis code hash | `dffb5a861a497cc24e57017d4c97b4260dccb03dc29063fb3c02fca46bc7e9ca`, identical in masked and unmasked on both survivors | `MA:<model>`, `UA:<model>` → `analysis_code_hash` |
| masked artifact hash agreement | `6ca030d9…` (e4b), `3368b857…` (qwen3-4b), matching between masked and unmasked | `MA`/`UA` → `masked_artifact_hash` |
| bit-identical recomputation | `identical_computation_as_masked: true` on both | `UA:<model>` |
| confirmatory rows | 24,576 per checkpoint run, 49,152 total; complete, 0 missing / duplicated / unexpected | `CONFIRMATORY_GENERATION.signed_record.json` → `payload.completeness` |
| structurally unmaskable groups | 4 (outcome, configuration) groups on the reduced design, including `D(A<-B)` | `MA:<model>` → `mask_effectiveness.structurally_unmaskable` |
| derived block-mean grain | 11,520 rows, 384 blocks per checkpoint run, `draws = 8` on every row | `paper/v4r4_bundle/tier2_data/per_block_cell_means.csv`, header stamped `DERIVED_AGGREGATION_ONLY` with the eight source sha256 |

---

## Numbers explicitly excluded

- **0.075 and 0.10 as the calipers.** These appear at
  `dci1/reports/dci1v4r4/SCIENTIFIC_FOLLOWUP_EVIDENCE.md:491-492` and are a
  confirmed uncorrected error. The registered values are **0.10 and 0.15**
  [`dci1/src/dci1v4r4/protocol/constants.py:233,235`; `ADM` →
  `thresholds.REFERENCE_CALIPER`, `.REFERENCE_PRESCREEN_CALIPER`]. `0.075` never
  entered any selection and does not appear in this paper.
- **Library sizes from any constants module.** Four constants in `dci1v4r4`
  carry stale v4r3-era trailing comments that disagree with their computed
  values. Library-size figures in this paper come from `COV`
  (`eligible_rungs_measured` = 254 per model, `population.families` = 28) and
  `G1D` (`instrument_population` = 524).


---

## Correction log

**2026-08-24, third pass — a clarification, not a correction.** "65 of 84
measured rungs" was accurate against the record and misleading in isolation,
because "measured" invites reading 84 as the constraint library. The 84 are the
shortlisted rungs Gate 2 calibrated, 21/20/23/20 pooled over four checkpoint
runs; the pre-screen measured 254 eligible rungs per run. Rows 2d–2g above now
carry what the 84 are, how they relate to the library, why the shortlist is not
selected for being below *A*, and the pre-screen-to-calibration shift. **No count
changed.**

**2026-08-24, fourth pass — a fourth error, in that clarification.** The shift
was first written as "14 rungs crossed", treating the one-way count as the total.
Recomputed from `...rungs[*].prescreen_iota` and `.iota`: **14 moved above→below
and 3 moved below→above, so 17 changed side**, and the net 11 is what turns 54
into 65. 51 stayed below and 16 stayed above; the four counts sum to 84.
Corrected in `01_narrative.md`, `02_intro_outline.md`, `03_paper_outline.md`,
`FIGURE_PLAN.md`, `GAPS.md`, `ITERATION.md` and row 2g above. No estimate,
interval or gate outcome is touched.

**2026-08-24, second review pass.** A third error, caught by the review's
arithmetic check.

3. **"9 of 18 in-caliper rungs refused by the Newcombe rule."** The per-checkpoint
   breakdown summed to 8, not 9. Recomputed from
   `models.<model>.families.<F>.rungs`: of the 18 rungs inside the 0.10 caliper,
   **9 were refused — 8 by the Newcombe rule and one, `RF11:26` on
   `gemma-3n-e4b-it`, on the pre-screen caliper alone.** The count of refusals
   was right; the attribution of all nine to Newcombe was wrong. Corrected in
   `01_narrative.md`, `03_paper_outline.md` and Table 3 above.

**2026-08-24, first review pass.** Two statements in the first draft of this
folder were wrong and are corrected above.

1. **"Twenty delivery-loss estimates."** Twelve of the twenty are `D(c←g)`
   delivery-loss quantities; eight are derived contrasts (`Lambda`,
   `Delta_class`). Corrected in `01_narrative.md`, `02_intro_outline.md`,
   `03_paper_outline.md` and `FIGURE_PLAN.md`.

2. **"On `gemma-3n-e4b-it` and `qwen3-4b-instruct-2507` no eligible rung sits
   strictly above ι_A."** False for `gemma-3n-e4b-it`: `RF9:13` sits at
   ι = 0.7043 against ι_A = 0.6948, and is both eligible (`eligible_13_5`) and
   admissible (`admissible_13_4`). The straddle test is against the family's
   **core rung**, not against ι_A, and on both checkpoints the core rung was the
   top of that family's measured ladder. The claim as first written also appears
   in `dci1/reports/dci1v5/reference_design_development.md` §5.1 and was inherited
   from there rather than derived; it is not carried forward.
   `qwen3-4b-instruct-2507` is the only checkpoint with nothing eligible above
   ι_A.

Both corrections narrow the claim. Neither changes an estimate, an interval or a
gate outcome.
