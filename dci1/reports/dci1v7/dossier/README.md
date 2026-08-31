# DCI-1 v7 — visualisation / results dossier

Machine-readable extraction of every valid estimand and diagnostic, plus a
recommended figure and table set. **No publication figures here** — this is the
data layer and the argument for what to draw.

Regenerate with `python dci1/tools/v7_dossier.py`. The tool reads only signed
stage records, copies numbers rather than recomputing them, and for the
block-level tables reconstructs cell means from the masked rows plus the mask
key and **aborts unless the reconstruction reproduces the signed
`UNMASKED_ANALYSIS` point estimates exactly** (verified for all six lanes,
tolerance 1e-12).

---

## 0. Evidence status — the first thing the paper must say

| | |
|---|---|
| **Registered v7 study** | **zero confirmatory rows.** All four replications terminated `PREFREEZE_AUDIT_FAILURE` on 2026-08-28. No freeze, no confirmatory generation, no analysis, no final report. `dci1/reports/dci1v7/CLOSURE.md`, `evidence/dci1v7/<model>/terminal_report.json` |
| **Everything in this dossier** | **six completed development-rehearsal lanes** in the structurally separate `dci1v7-development` namespace, which the protocol's own guards refuse to admit as study evidence (`engine/guards.assert_no_foreign_manifest`). `dci1/reports/dci1v7/development_rehearsal/REHEARSAL.md` |
| **What a rehearsal lane is** | the registered stage sequence, on the registered model, through the pinned backend, with every registered rule, threshold, cap, seed, verifier and provenance check unweakened — run under a caller-supplied root outside the registered tree. It is evidence *about the apparatus*, not about any estimand. |

Every row of every table carries `evidence_status`. The ladder:

| `evidence_status` | Meaning | May a paper claim rest on it? |
|---|---|---|
| `DEV_REHEARSAL_primary` | F1/F11 member, IDENTIFIED, simultaneous interval | Only as *development* evidence, labelled |
| `DEV_REHEARSAL_secondary` | F2–F4, F7, F10 member | Secondary, cannot change a primary conclusion |
| `DEV_REHEARSAL_robustness` | F5 recodings (vacuity-forced, graded ≥0.99) | Robustness only |
| `DEV_REHEARSAL_degeneracy_gate` | F6 vacuity differences | Gates the §17.4 interpretation |
| `NOT_IDENTIFIED_never_a_null` | design could not identify it | **Never render as zero or as a null result** |
| `POST_HOC_diagnostic_licenses_nothing` | computed after outcomes | Diagnostic prose only |
| `DEV_REHEARSAL_selection_*` | prospective, pre-composition selection input | Method description / appendix |

**Lane roles.** Two models were run twice on different code roots. `canonical`
is the lane a per-model number should be quoted from; `repeat` lanes are
reproducibility evidence, **never a second replication**. The two roots re-ran
§12–§13 from scratch, so they selected *different reference severities* — the
difference between them is selection-plus-sampling variability, not measurement
noise.

| lane | model | role | n\* | m\* | arms | cells/block | conf. rows | §26 |
|---|---|---|---:|---:|---|---:|---:|---|
| `dci1v7-development` | qwen3-4b | repeat | 2 | 12 | base, core | 26 | 79,872 | MET |
| `dci1v7-development-r3` | qwen3-4b | **canonical** | 2 | 12 | base, core | 26 | 79,872 | MET |
| `dci1v7-development-r3` | gemma-3n-e2b-it | repeat | 8 | 10 | base, core, class | 29 | 89,088 | MET |
| `dci1v7-development-r4` | qwen3-4b-instruct-2507 | **canonical** | 5 | 11 | base, core | 26 | 79,872 | MET |
| `dci1v7-development-r4` | gemma-3n-e4b-it | **canonical** | 6 | 9 | base, core, class | 29 | 89,088 | MET |
| `dci1v7-development-r5` | gemma-3n-e2b-it | **canonical** | 8 | 10 | base, core, class | 29 | 89,088 | MET |

All six: 384 blocks, M = 8, `measurement_basis = deterministic_measurement_validated`.
Every lane lost the **spectrum** arm (`DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, §12.6 C4
on the calibration basis) and the **near-form** arm
(`NEAR_FORM_ARM_NOT_AVAILABLE`, C8). So `δ_difficulty`, `β`, `α_f`, `γ_tier`,
`Δ_near` and the six spectrum losses are `NOT_IDENTIFIED` **on every lane** —
21 members, listed in `not_identified.csv`.

---

## 1. Tables in this directory

| File | Rows | What it is |
|---|---:|---|
| `lanes.csv` | 6 | lane provenance: operating points, arms, hashes, commits, statuses |
| `estimands_master.csv` | 810 | **the full flat table.** `model \| outcome position \| estimand \| point \| simultaneous 95% \| marginal 95% \| decision interval \| threshold \| N blocks \| evidence status \| source artifact` |
| `not_identified.csv` | 345 | the members no lane could identify, with the reason |
| `cell_compliance.csv` | 666 | every constituent cell's compliance rate, weight and boundary reading, per member |
| `cell_means_blocklevel.csv.gz` | 109,440 | **per-block cell means**, unmasked and verified (compliance, graded, vacuity, truncation, response words) |
| `block_contrasts.csv.gz` | 4,608 | per-block values of `D(B←A)`, `D(A←B)`, `Λ`, `Δ_R`, `Δ_j`, `Δ_broad` and every constituent rate |
| `references_selected.csv` | 21 | R1/R2/R3/CL identity, ι, ι_A, caliper distance, tier, group, discourse role, split stability |
| `reference_candidates.csv` | 833 | every candidate rung's earliest failing `V(R)` component and its values |
| `iota_a_stability.csv` | 6 | §13.7's two-split equivalence test on ι_A |
| `coverage_c1_c8.csv` | 48 | §12.6 C1–C8 on both bases, which arm each gates, and which moved |
| `calibration_curves.csv` | 96 | A's n-grid and B's m-grid: solo, chance, load-zero chance, band, eligibility, selection |
| `operating_points.csv` | 6 | realised n\*, m\*, bracketing, admissible set |
| `robustness_f5.csv` | 108 | vacuity-forced and graded-≥0.99 recodings of the F1 members |
| `vacuity_f6.csv` | 168 | the F6 degeneracy-symmetry family that gates §17.4's reading |
| `projection_audit.csv` | 54 | §23's projected vs realised composed compliance — **post-hoc** |
| `posthoc_confirmatory_difficulty.csv` | 27 | **post-hoc**: κ, ι and instruction lift recomputed on the confirmatory unconstrained cells. Reads on the chance-column defect (§4) |
| `statements.csv` | 81 | every emitted / withheld claim with its reason |
| `fig*.csv` | — | tidy one-row-per-mark views, one per proposed visual (§5) |

---

## 2. The results, in brief

### 2.1 Δ_R — all twelve estimates

`fig1_delta_r_forest.csv`. Simultaneous 95% intervals, F1, 384 blocks.

| lane | position | Δ_R | simultaneous 95% | reading | direction | compressed |
|---|---|---:|---|---|---|---|
| dev / qwen3-4b | first | −0.0009 | [−0.0219, +0.0201] | L3c | unresolved | — |
| dev / qwen3-4b | second | +0.0144 | [−0.0128, +0.0416] | L3c | unresolved | — |
| r3 / qwen3-4b | first | −0.0030 | [−0.0244, +0.0184] | L3c | unresolved | **+ direction** |
| r3 / qwen3-4b | second | +0.0126 | [−0.0140, +0.0392] | L3c | unresolved | — |
| r3 / gemma-3n-e2b-it | first | −0.0244 | [−0.0478, −0.0010] | L3c | **A comparatively better** | — |
| r3 / gemma-3n-e2b-it | second | −0.0712 | [−0.1047, −0.0377] | L3c | **A comparatively better** | — |
| r4 / qwen3-4b-instruct-2507 | first | +0.0063 | [−0.0150, +0.0275] | L3c | unresolved | **both directions** |
| r4 / qwen3-4b-instruct-2507 | second | −0.0034 | [−0.0299, +0.0232] | L3c | unresolved | — |
| r4 / gemma-3n-e4b-it | first | −0.0268 | [−0.0555, +0.0019] | L3c | unresolved | — |
| r4 / gemma-3n-e4b-it | second | −0.0726 | [−0.1034, −0.0418] | L3c | **A comparatively better** | — |
| r5 / gemma-3n-e2b-it | first | −0.0320 | [−0.0587, −0.0053] | L3c | **A comparatively better** | — |
| r5 / gemma-3n-e2b-it | second | −0.0852 | [−0.1189, −0.0515] | L3c | **A comparatively better** | — |

Every interval's upper bound is below +0.10 and every realised half-width
(0.021–0.034) meets the registered 0.05 precondition, so **L3c is licensed in
all twelve cells**: no pair-specific excess above the generic-load threshold,
locally. `L3b` (0.25) is nowhere near reached. Five cells have an upper bound
below 0 → `A_COMPARATIVELY_BETTER`: the same-form matched companions cost B
*more* than A does. That is a named v7 §28.1 outcome, not an absence.

> **Compression, which must appear on the plot.** On `r3/qwen3-4b` at
> `outcome_first`, B's compliance is 0.901 under A and 0.898 under the
> reference mean, so by arithmetic Δ_R could not have exceeded +0.099
> regardless of the model: the positive (excess) direction was closed by the
> arm's level. On `r4/qwen3-4b-instruct-2507` at `outcome_first` **both**
> directions are compressed (arms at 0.901 and 0.907; attainable range
> [−0.093, +0.099]). In those two cells the L3c reading followed from an arm's
> level rather than from a comparison that could have gone the other way
> (v7 §13.14 reading 3, `analysis/boundary.py`). Columns
> `positive_direction_compressed`, `negative_direction_compressed`,
> `attainable_min/max`, `l3c_bounded_by_arm_level`.

### 2.2 The raw-loss confound the design exists to remove

`fig2_loss_decomposition.csv`. `D(B←R̄)` is the unweighted mean of the three F2
members; it is **not** a registered estimand and has no simultaneous interval of
its own. `Δ_R = D(B←A) − D(B←R̄)` exactly.

| lane | pos | solo B | B\|A | B\|R̄ | D(B←A) | D(B←R̄) | Δ_R |
|---|---|---:|---:|---:|---:|---:|---:|
| r3 / qwen3-4b | first | 0.778 | 0.901 | 0.898 | −0.123 | −0.120 | −0.003 |
| r3 / qwen3-4b | second | 0.778 | 0.797 | 0.810 | −0.020 | −0.032 | +0.013 |
| r4 / qwen-instr-2507 | first | 0.770 | 0.901 | 0.907 | −0.132 | −0.138 | +0.006 |
| r4 / qwen-instr-2507 | second | 0.770 | 0.877 | 0.874 | −0.107 | −0.104 | −0.003 |
| r4 / gemma-3n-e4b-it | first | 0.745 | 0.709 | 0.683 | +0.035 | +0.062 | −0.027 |
| r4 / gemma-3n-e4b-it | second | 0.745 | 0.353 | 0.281 | **+0.392** | **+0.464** | −0.073 |
| r5 / gemma-3n-e2b-it | first | 0.788 | 0.811 | 0.779 | −0.023 | +0.009 | −0.032 |
| r5 / gemma-3n-e2b-it | second | 0.788 | 0.577 | 0.492 | **+0.211** | **+0.296** | −0.085 |

This is the paper's central quantitative point: where the raw loss is largest
(gemma-3n-e4b-it, B second, +0.392), the matched-reference loss is **larger
still** (+0.464), so the companion-specific component is −0.073. And on both
Qwens composition *raises* B's compliance (negative D), equally under A and
under the references.

### 2.3 Direction and outcome position

`fig3_direction_and_position.csv`. Both are large and both flip.

- **`D(A←B)`** — A is heavily damaged by B on three of four models
  (+0.17 to +0.40) and untouched on `qwen3-4b-instruct-2507` (−0.008, −0.033).
- **`D(B←A)`** — ranges from −0.13 (a resolved delivery **gain**) to +0.39.
- **`Λ`** — negative in eleven of twelve cells (A pays more), and **reverses
  sign** on `gemma-3n-e4b-it` between positions (−0.178 → +0.221), both
  intervals excluding zero.
- **Order contrasts (F11)** — `Ord_B` excludes zero on three of four models,
  reaching −0.356 on `gemma-3n-e4b-it`; `Ord_R̄` reaches −0.402 there.
  `Ord_A` is small everywhere (+0.006 to +0.075).

> **Do not read a non-emitted L1 as "no effect".** `emit_l1` requires the
> lower bound above 0, so a resolved delivery *gain* (upper bound below 0,
> e.g. `D(B←A)` = −0.132 [−0.168, −0.095] on qwen-instruct) shows as
> `emitted=False`. §28.1's "Delivery gain resolved" row is the correct
> reading; `statements.csv` carries the machine reason.

### 2.4 Same-form versus broad-class — **flagged**

`fig4_same_form_vs_broad_class.csv`. Class arm on the three Gemma lanes only.

| lane | pos | Δ_R (same-form) | Δ_broad (Tier-3 budget) |
|---|---|---|---|
| r3 / gemma-3n-e2b-it | first | −0.024 [−0.048, −0.001] | +0.016 [−0.008, +0.041] |
| r3 / gemma-3n-e2b-it | second | −0.071 [−0.105, −0.038] | **+0.212 [+0.177, +0.247]** |
| r4 / gemma-3n-e4b-it | first | −0.027 [−0.056, +0.002] | +0.099 [+0.069, +0.129] |
| r4 / gemma-3n-e4b-it | second | −0.073 [−0.103, −0.042] | **+0.316 [+0.278, +0.354]** |
| r5 / gemma-3n-e2b-it | first | −0.032 [−0.059, −0.005] | +0.025 [+0.000, +0.051] |
| r5 / gemma-3n-e2b-it | second | −0.085 [−0.119, −0.051] | **+0.207 [+0.173, +0.241]** |

Read naively this says "A costs B less than a broad-class companion does but
about as much as a same-form one" — a clean form/class story. **It is not safe
to draw it that way.** See §4.

### 2.5 Robustness

`robustness_f5.csv`, `vacuity_f6.csv`.

- The **vacuity-forced** recomputation leaves Δ_R's L3c reading unchanged on
  every lane. It moves the point materially on **one** lane:
  `qwen3-4b-instruct-2507`, where Δ_R goes +0.006 [−0.015, +0.028] → −0.048
  [−0.079, −0.018] (first) and −0.003 → −0.036 (second).
- The **graded ≥0.99** recoding moves Δ_R on the Gemmas (r5 second:
  −0.085 → −0.144; e4b second: −0.073 → −0.035) but never across the 0.10
  threshold. Sign is preserved except on `gemma-3n-e4b-it` first (−0.027 → +0.004).
- **F6 fires on `qwen3-4b-instruct-2507`**: `vac(B|B+R2) − vac(B solo)` =
  +0.147 [+0.117, +0.177] (first) and +0.061 [+0.039, +0.082] (second) — above
  the 0.05 gate with intervals excluding zero. Under §17.4 that lane's primary
  estimands carry the fixed vacuity block and are read jointly with the F5
  bounds: **L3c is licensed under both, the direction is not**.
- F6 is exactly 0 with a degenerate bootstrap on all three Gemma lanes (no
  vacuous passes at all).

---

## 3. What is *not* available, and must never be drawn as zero

`NOT_IDENTIFIED` on **every** lane, 21 members (`not_identified.csv`):

- `δ_difficulty` (and its two F5 recodings), `β`, `α_1..α_3`, `γ_tier` — the
  whole difficulty-response fit;
- the six spectrum losses `D(B←R_{f,±})` and their F6 vacuity rows;
- `Δ_near` and `D(B←N_k)` — the near-form arm qualified on no lane;
- `Δ_broad`, `D(B←CL)`, `Ord_CL` on the two Qwen lanes (no class arm).

The cause is registered and design-time: §12.6 condition **C4** (six feature
groups straddling ι_A with ≥3 eligible rungs spanning ≥0.40 in ι) was certified
on the 24-topic pre-screen and **lost on the 192-topic calibration basis** on
all six lanes — 2 to 5 straddling groups against 6 (`coverage_c1_c8.csv`,
`conditions_moved_by_the_basis`). Under v7 A7 that costs the spectrum arm only;
the core arm is retained.

---

## 4. Two defects a figure could launder — both must be disclosed

### 4.1 The chance column has been 0.0 on every replication

`CHANGES_SCIENTIFIC.md` 2026-08-29 ("finding, not yet in force");
`run/gates_run.py:673-691`. The §13.11 calibration table wrote
`chance_compliance = 0.0` for **every** candidate on every v5/v6/v7
replication, so admission used **raw solo compliance** as ι(R) while ι_A was
chance-corrected. The fix is on `wip/v7-cpu-pools` and is not in force.

`posthoc_confirmatory_difficulty.csv` recomputes κ and ι on the confirmatory
unconstrained cells — the only place the realised coordinate can be read.

**For the three core references the defect is harmless.** Marker families
genuinely have κ = 0 on every lane, so ι(R) = raw solo compliance is the
correct value, and the realised confirmatory gap |ι_{R_j} − ι_A| runs 0.004 to
0.090 — inside §13.8's 0.15 realised-gap qualifier on every reference of every
lane. **Δ_R's matching is sound.**

**For the broad-class control it is not.** `CL` is `RF12` — a sentence budget —
and its true chance compliance is large:

| lane | CL | κ recorded | κ confirmatory | ι used for admission | ι confirmatory | \|ι−ι_A\| confirmatory | lift confirmatory |
|---|---|---:|---:|---:|---:|---:|---:|
| r3 / gemma-3n-e2b-it | RF12:6 | 0.000 | 0.349 | 0.583 | 0.400 | **0.217** | +0.260 |
| r5 / gemma-3n-e2b-it | RF12:6 | 0.000 | 0.350 | 0.592 | 0.406 | **0.213** | +0.264 |
| r4 / gemma-3n-e4b-it | RF12:7 | 0.000 | **0.807** | 0.781 | **−0.093** | **0.816** | **−0.018** |

On `gemma-3n-e4b-it` the broad-class companion's solo compliance (0.789) is
*below* its own chance rate (0.807): stating it did nothing. Under a correct
chance column it would have failed §13.4's `V_head` lift floor
(H_R ≥ 0.20) outright, and on both e2b lanes §13.10's matching caliper
(|ι_CL − ι_A| ≤ 0.15) would have recorded `CLASS_ARM_NOT_MATCHED`. **No lane
raised that status** — the defect is why.

**Consequence for figures.** Δ_broad may be shown only as what §13.10 registers
it as — a *bound*, with one companion, carrying `COMPANION_CLASS_NOT_MATCHED` —
**and** with the difficulty mismatch stated. A "same-form vs broad-class at
matched difficulty" figure is not supportable: the broad-class companion was
not difficulty-matched on the registered coordinate.

### 4.2 The repeat lanes re-selected different references

`figA1_repeat_lane_agreement.csv`, `references_selected.csv`.

| model | contrast | position | canonical | repeat | diff |
|---|---|---|---:|---:|---:|
| qwen3-4b | Δ_R | first | −0.0030 | −0.0009 | −0.0021 |
| qwen3-4b | Δ_R | second | +0.0126 | +0.0144 | −0.0018 |
| gemma-3n-e2b-it | Δ_R | first | −0.0320 | −0.0244 | −0.0076 |
| gemma-3n-e2b-it | Δ_R | second | −0.0852 | −0.0712 | −0.0140 |

The two roots picked **the same families at different severities** — qwen3-4b
`MK1:6` vs `MK1:7`; gemma-3n-e2b-it `MK2:1/MK1:4/MK5:7` vs `MK2:7/MK1:1/MK5:8` —
and ι_A itself moved (0.589 vs 0.609 on e2b). The Δ_R differences (0.002–0.014)
are therefore *selection plus sampling* variability and are smaller than the
realised half-widths (0.021–0.034). Useful appendix evidence about the
procedure's stability; **not** a test–retest reliability estimate and not a
second replication.

---

## 5. Recommended visuals

`claim supported | exact data | visual type | axes/rows/cols | uncertainty | threshold/baseline | models/conditions | why figure vs table | placement`

### Main paper — four visuals, one table

**M1. Δ_R forest.** *(the candidate you asked about — recommended, with two changes)*

| | |
|---|---|
| **Claim** | On no model and in no position does A cost B more than same-form difficulty-matched companions do by the generic-load threshold; L3c is licensed everywhere. |
| **Data** | `fig1_delta_r_forest.csv`, 12 rows (or 8 canonical-only) |
| **Visual** | Horizontal forest, point + simultaneous 95% interval |
| **Rows** | model × outcome position, grouped by model; **canonical lanes only** in the main paper |
| **X axis** | Δ_R, compliance units, fixed to [−0.30, +0.30] so the 0.25 threshold is on-canvas |
| **Uncertainty** | Simultaneous 95% (F1, studentised max-modulus). Marginal 95% as a thin inner tick — the columns are in the CSV |
| **Threshold** | Vertical rules at 0, +0.10 (L3a/L3c), +0.25 (L3b) |
| **Included** | 4 models × 2 positions = 8 marks |
| **Figure vs table** | Figure: the point is that twelve intervals sit in a narrow band far from +0.10, which a table makes the reader compute |
| **Placement** | **Main** |
| **Two required changes** | (a) **shade the attainable range** (`attainable_min/max`) or mark the two compressed cells — otherwise the plot implies the +0.10 threshold was reachable when arithmetic had closed it; (b) label the axis *"Δ_R (compliance)"* and the caption *"development rehearsal, not confirmatory"*. |

**M2. Loss decomposition: raw vs matched.**

| | |
|---|---|
| **Claim** | The solo→composed loss is large and model/position dependent, and it is almost entirely generic: the matched companions produce the same loss or more. |
| **Data** | `fig2_loss_decomposition.csv` (+ `cell_compliance.csv` for the four cell levels) |
| **Visual** | Slope/dumbbell panel: per model×position, a mark for `D(B←A)` and one for `D(B←R̄)`, joined, with Δ_R as the annotated gap |
| **Rows/cols** | Rows = model; columns = outcome position |
| **Uncertainty** | Simultaneous 95% on `D(B←A)` and on Δ_R. **None on `D(B←R̄)`** — it is a derived mean with no registered interval; draw it as a bare tick and say so |
| **Baseline** | Horizontal rule at 0 (no loss); optionally the solo rate as a secondary axis |
| **Included** | 4 canonical models × 2 positions |
| **Figure vs table** | Figure: it is a comparison of two quantities whose *difference* is the estimand |
| **Placement** | **Main** — this is the design's argument in one picture |

**M3. Direction × outcome position.**

| | |
|---|---|
| **Claim** | Which instruction pays, and how much, depends on both direction and position; Λ reverses sign on one model. |
| **Data** | `fig3_direction_and_position.csv` |
| **Visual** | Small-multiple dot-and-interval: 2×2 grid of models; within each, three rows (`D(B←A)`, `D(A←B)`, `Λ`) × two positions |
| **Axes** | X = estimate (compliance); Y = member × position |
| **Uncertainty** | Simultaneous 95% (F1) |
| **Baseline** | Rule at 0; band at ±0.10 (SESOI) |
| **Included** | 4 canonical models, both positions |
| **Figure vs table** | Figure: the sign reversal is a visual fact |
| **Placement** | **Main** |
| **Required annotation** | Mark `outcome_second` rows `POSITION_CONFOUNDED` (§11.4) and note that a negative `D` is a resolved delivery **gain**, not a failure to detect a loss |

**M4. Order contrasts (F11).** Optional fourth figure; fold into M3 if space is
tight — `Ord_A`, `Ord_B`, `Ord_Λ`, `Ord_R̄` from `fig_order_contrasts.csv`, one
row per member per model, simultaneous 95% (F11), rule at 0 and band at ±0.10.
`Ord_CL` is `NOT_IDENTIFIED` on the two Qwens and must be shown as absent, not
as zero. **Main or appendix.**

**T1. Full numerical results table.** *(the candidate you asked about — recommended, restricted)*

| | |
|---|---|
| **Claim** | Every licensed number, auditable |
| **Data** | `estimands_master.csv` filtered to `family ∈ {F1, F11}` and `status = IDENTIFIED` → 4 models × (5 F1 + 4–5 F11) ≈ 60 rows |
| **Visual** | Table. Columns: model, position, member, cell, estimate, simultaneous 95%, marginal 95%, half-width, precision met, threshold, N blocks, identification statuses |
| **Placement** | **Main**, with the *full* 810-row table in the appendix |
| **Why table** | Exact values are the deliverable; the plots carry the shape |

### Appendix

**A1. Per-reference Δ_j.** *(candidate — recommended as a figure, appendix)*
`fig_delta_j.csv`. Forest, rows = model × position × j, simultaneous 95% (F2, k=6),
rules at 0 and ±0.10. Shows the heterogeneity that Δ_R averages over — and it is
real: on `gemma-3n-e4b-it` at position two the three Δ_j run −0.022, −0.082,
−0.113. **Why appendix:** it is a secondary family (F2) and cannot change a
primary conclusion (§23). **Why figure not table:** the spread across j is the
message.

**A2. Same-form vs broad-class.** *(candidate — recommended, appendix only, with a caveat block)*
`fig4_same_form_vs_broad_class.csv`. Paired dots per Gemma lane × position:
Δ_R and Δ_broad with simultaneous intervals (F1 and F10 respectively — **two
different families, say so**). **Must carry** `COMPANION_CLASS_NOT_MATCHED` and
the §4.1 difficulty-mismatch table. **Flagged: this figure is statistically
misleading in the main paper** — it would read as a difficulty-matched
form-versus-class contrast, and the broad-class companion was not
difficulty-matched (|ι_CL − ι_A| = 0.21–0.82 on the confirmatory coordinate).
Alternative: show it as *one Tier-3 budget companion behaved very differently*,
descriptive, with the companion's own κ and lift on the same panel.

**A3. Reference-matching diagnostics.** *(candidate — recommended, appendix, as a figure)*
`references_selected.csv` + `posthoc_confirmatory_difficulty.csv`.
Dot plot: X = ι, one row per lane; ι_A as a vertical rule, the three R_j and CL
as points, the ±0.10 caliper as a shaded band, and **a second, differently
styled point per companion for the post-hoc confirmatory ι**. Uncertainty: none
on the calibration ι (point estimates by construction — §13.8 selects on the
point); the two-split equivalence interval is available in
`iota_split_diff_*`. This is the figure that makes §4.1 visible.

**A4. Candidate attrition.** `reference_candidates.csv`. Stacked bar per lane of
the earliest failing `V(R)` component: across six lanes, `V_head` 357,
`V_stab` 339, `V_inter` 51, admitted 86. **Table would also do**; a bar chart is
better because the ordering is lexicographic and the point is where the pool is
lost. **Appendix.**

**A5. Calibration curves for n\* and m\*.** *(candidate — recommended, appendix)*
`calibration_curves.csv`. Two panels (A over n = 1..8; B over m = 7..14), one
line per model, points shaded by eligibility, selected severity ringed, the
registered band `[0.50, 0.85]` / `[0.60, 0.95]` as a horizontal band and the
aim (0.70 / 0.80) as a rule. Add the load-zero chance curve for B as a dashed
line — it is what §34 D17's construct floor reads. **Uncertainty:** none is
recorded per rung; say "192 topics, 4 draws, point estimates". **Why figure:**
it shows both the selection rule and why `n*` sat at the grid top on the e2b
lanes (`OPERATING_POINT_AT_GRID_BOUNDARY`).

**A6. Robustness panel.** `robustness_f5.csv` + `vacuity_f6.csv`. Three marks per
model×position for Δ_R: primary, vacuity-forced, graded ≥0.99, on one row, with
simultaneous intervals; a second small panel for the F6 differences against the
0.05 gate. **Appendix.** Required: name `qwen3-4b-instruct-2507` as the lane
where F6 fires and where the vacuity-forced Δ_R changes direction.

**A7. Coverage C1–C8 and why the spectrum arm was lost.** `coverage_c1_c8.csv`.
Small heat-grid: rows = lane, columns = C1..C8, two cells each (pre-screen
basis, calibration basis), with C4 highlighted. **Table is acceptable**; the
grid is better because the story is "certified on one basis, lost on the other".
**Appendix.**

**A8. Per-block heterogeneity.** *(optional candidate — recommended as appendix, with a constraint)*
`block_contrasts.csv.gz`, 4,608 rows. Per model×position, a histogram or ECDF of
the per-block Δ_R together with the block-mean and its interval. **Flag:** a
per-block Δ_R takes values on a coarse lattice (multiples of 1/24 given M = 8
and three references), so a smooth density is misleading — use a histogram with
lattice-aligned bins or a beeswarm. **Do not** compute any interval from the
per-block spread other than the registered block bootstrap; the CSV is for
display only.

**A9. Projection audit.** `projection_audit.csv`. §13.6's projected vs realised
composed compliance, per companion. **Post-hoc, licenses nothing** — label it so.
Notable: on `r5/gemma-3n-e2b-it` `pair:B+A@outcome_first`, projected 0.618 vs
realised 0.340. **Appendix, small.**

**A10. Full 810-row estimand table** and **the not-identified inventory**
(`estimands_master.csv`, `not_identified.csv`) as supplementary CSV, with a
short table in the appendix listing the 21 permanently unidentified members and
the single registered cause (§12.6 C4 on the calibration basis).

### Candidates assessed and *not* recommended

| Candidate | Verdict |
|---|---|
| Δ_R forest **pooled across models** | **No.** §6.1's firewall: no cross-model scalar carries a claim, and there is no cross-model multiplicity family. Facet, never pool. |
| Any Δ_R vs ι scatter / difficulty-response line | **No.** `δ_difficulty`, `β` and `α_f` are `NOT_IDENTIFIED` on every lane. Drawing a line through three same-difficulty references would be the construct §11.8 warns collapses to a different quantity. |
| Δ_near / form-tier comparison | **No data.** The near-form arm qualified on no lane. |
| A "no effect" / equivalence-to-zero panel | **No.** §17.3: L3c says the interval's upper bound is below 0.10, not that Δ_R = 0. Five cells actively exclude zero on the negative side. |
| Joint-success or joint-state panels | **No producer.** §11.5 registers them; nothing in the v7 code computes them. |
| Repeat lanes plotted as independent replications | **No.** They are the same model re-run with re-selected references. |

---

## 6. Provenance

| | |
|---|---|
| Repository HEAD at extraction | `87a6c18` |
| Registered v7 manifest | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` (zero confirmatory rows) |
| Methods reconstruction | `dci1/reports/dci1v7/METHODS.md` |
| Rehearsal narrative | `dci1/reports/dci1v7/development_rehearsal/REHEARSAL.md` |
| Extractor | `dci1/tools/v7_dossier.py` |
| Per-lane producing commits, freeze and verifier hashes | `lanes.csv` |
