# Batch 1 calibration precision review (audit F6)

**Everything here is simulated.** The compliance surfaces are invented, and the
selection rules are the real Batch 1 code. Nothing here is a measured model
rate or an empirical finding. The numbers say how reliable the proposed
procedure would be *if* models behaved like these surfaces.

- **Machine-readable result:** [`calibration_precision.json`](calibration_precision.json).
- **Code:** `src/dci/batch1/simulate.py` (offline; not part of Freeze 1).
- **Command:** `python -m dci.batch1.simulate --reps 100 --workers 9 --d14-pilots 60 --d14-boot 100 --out docs/batch1/calibration_precision.json`.
- **Runtime:** about 8 minutes on 9 CPU cores.

## 1. Simulation design

**Each replicate** is a simulated pilot, run through the real code in this
order:

1. Stage 1 counts;
2. `calibration.select_stage2`;
3. Stage 2 counts on the selected cells;
4. `calibration.finalize`.

This covers eligibility, ±0.10 matching, D07, D08, G1–G6, P1–P3 and the
12-of-16 target. Only the data are simulated.

**Responses share topics.** Response *j* of cell *c* (model *m*) on topic *t*
complies with probability `expit(logit(p_c) + u_mt + e_ct)`:

- `u_mt ~ N(0, 0.5)` is shared by every condition of model *m* on topic *t*;
- `e_ct ~ N(0, 0.3)` is specific to the cell.

Responses on the same topic are therefore dependent, as they are in the pilot,
where every cell of a stage sees the same topics.

**The truth** of a cell is its population mean over topics (Gauss–Hermite). The
noise-free reference result is `finalize` run on those means.

**Metrics,** against the noise-free result:

- **Verdict:** false FEASIBLE and false INFEASIBLE rates.
- **Selections:** agreement of the selected A and B.
- **Membership:** with the true A and B held fixed, the G1, G3 and G5 Jaccard
  overlap, and G1's false inclusions and exclusions per configuration.
- **Matching error:** for references near the edge (true |p_X − p_A| within
  0.05 of 0.10) and far from it.
- **Coverage:** the number of configurations supporting P1, P2 and P3.

## 2. Compliance surfaces

| surface | what it varies | noise-free verdict |
|---|---|---|
| `moderate` | the synthetic default surface | FEASIBLE (A.4, B 10/12) |
| `model_differences` | model shifts of −0.16 to +0.20 | FEASIBLE (A.4, B 9/11) |
| `frame_differences` | F1 shifts references and A by −0.10 to +0.06, per constraint | FEASIBLE |
| `boundary_cluster` | every word-count reference within ±0.04 of p_A ± 0.10 | FEASIBLE |
| `low_followability` | references 0.15 lower (the audit's harder surface) | FEASIBLE, but P3 holds in only 14 of 16 |
| `other_operation_harder` | references of other operations 0.20 lower | **INFEASIBLE**: P3 holds in 0 of 16, because G5 adds 1 other-operation reference and 2 are needed |

## 3. Sampling allocations compared

Every allocation keeps 96 pilot topics: 32 in Stage 1 and 64 in Stage 2.

| allocation | what changes | maximum generations | vs current |
|---|---|---|---|
| **current** | 32 per cell; Stage 2 refines ≤ 240 cells × 64 | **30,976** | — |
| focal96 | A and B cells use all 96 topics in Stage 1; Stage 2 refines references only | 35,584 | +4,608 (+15%) |
| cap 360 | Stage 2 refines ≤ 360 cells | 38,656 | +7,680 (+25%) |
| focal96 + cap 360 | both | 43,264 | +12,288 (+40%) |
| cap 480 | Stage 2 refines ≤ 480 cells | 46,336 | +15,360 (+50%) |
| cap 240 × 2 draws | Stage 2 draws twice on the same 64 topics | 46,336 | +15,360 (+50%) |
| uniform 96 | every cell 96, no Stage 2 (an upper reference) | 46,336 | +15,360 (+50%) |

## 4. Results (100 simulated pilots per surface and allocation)

### Membership and matching accuracy, with the true A and B fixed

| surface | allocation | G1 Jaccard | G3 | G5 | G1 false in / out per config | near-edge error | far error |
|---|---|---|---|---|---|---|---|
| moderate | current | 0.51 | 0.49 | 0.52 | 3.5 / 3.0 | 0.39 | 0.14 |
| moderate | focal96 | 0.53 | 0.52 | 0.54 | 3.3 / 2.7 | 0.38 | 0.13 |
| moderate | cap 480 | 0.57 | 0.56 | 0.58 | 3.2 / 2.4 | 0.37 | 0.10 |
| moderate | uniform 96 | 0.56 | 0.55 | 0.57 | 3.4 / 2.4 | 0.37 | 0.10 |
| boundary_cluster | current | 0.43 | 0.43 | 0.47 | 3.4 / 5.2 | 0.44 | 0.06 |
| boundary_cluster | uniform 96 | 0.46 | 0.47 | 0.51 | 3.5 / 4.6 | 0.40 | 0.04 |
| frame_differences | current | 0.56 | 0.55 | 0.56 | 2.7 / 3.2 | 0.38 | 0.13 |
| frame_differences | uniform 96 | 0.62 | 0.61 | 0.62 | 2.5 / 2.5 | 0.36 | 0.10 |
| model_differences | current | 0.54 | 0.53 | 0.55 | 3.0 / 2.3 | 0.38 | 0.12 |
| model_differences | uniform 96 | 0.58 | 0.57 | 0.59 | 3.0 / 1.9 | 0.37 | 0.10 |
| low_followability | current | 0.57 | 0.56 | 0.51 | 1.8 / 2.1 | 0.39 | 0.09 |
| low_followability | uniform 96 | 0.65 | 0.64 | 0.58 | 1.5 / 1.6 | 0.36 | 0.06 |
| other_operation_harder | current | 0.51 | 0.50 | 0.46 | 3.4 / 3.0 | 0.38 | 0.13 |
| other_operation_harder | uniform 96 | 0.57 | 0.56 | 0.52 | 3.3 / 2.3 | 0.36 | 0.10 |

Every allocation and surface is in the JSON. The other allocations fall
between *current* and *uniform 96*.

### Selection and verdict stability

| surface (truth) | allocation | FEASIBLE share | false FEASIBLE | false INFEASIBLE | A agrees | B agrees | P1 / P2 / P3 supported (mean of 16) |
|---|---|---|---|---|---|---|---|
| moderate (F) | current | 1.00 | — | 0.00 | 0.99 | 0.88 | 16.0 / 15.4 / 15.8 |
| model_differences (F) | current | 0.99 | — | 0.01 | 0.99 | 0.80 | 16.0 / 15.2 / 15.7 |
| frame_differences (F) | current | 0.98 | — | 0.02 | 1.00 | 0.88 | 16.0 / 14.7 / 15.8 |
| boundary_cluster (F) | current | 0.99 | — | 0.01 | 0.98 | 0.93 | 16.0 / 15.5 / 15.8 |
| low_followability (F) | current | 0.74 | — | **0.26** | **0.52** | 0.83 | 15.0 / 10.0 / 13.2 |
| low_followability (F) | focal96 | 0.66 | — | 0.34 | 0.66 | 0.89 | 15.3 / 10.4 / 12.9 |
| low_followability (F) | cap 240 × 2 | 0.70 | — | 0.30 | 0.82 | 0.94 | 15.7 / 11.9 / 13.8 |
| low_followability (F) | uniform 96 | 0.73 | — | 0.27 | 0.63 | 0.88 | 15.2 / 10.9 / 13.1 |
| other_operation_harder (**I**) | current | 0.89 | **0.89** | — | 0.99 | 0.93 | 16.0 / 15.5 / **13.4** |
| other_operation_harder (**I**) | focal96 | 0.85 | 0.85 | — | 1.00 | 0.90 | 16.0 / 15.6 / 13.0 |
| other_operation_harder (**I**) | uniform 96 | 0.87 | 0.87 | — | 1.00 | 0.90 | 16.0 / 15.7 / 13.5 |

In the truth column, F is FEASIBLE and I is INFEASIBLE.

## 5. What the simulation shows

**1. Membership precision is limited by topics, not by the Stage 2 budget.**
- **Membership:** G1 overlaps the noise-free G1 by about 0.43–0.65 (Jaccard)
  in every allocation. Going from 30,976 to 46,336 generations raises it by
  only 0.03–0.08. Even *uniform 96*, every cell at the pilot's full 96
  topics, is no better than a 360- or 480-cell Stage 2.
- **Why:** more draws on the same topics (cap 240 × 2 draws) buy no more than
  more cells.
- **What limits it:** the pilot has 96 topics. The estimand is the topic
  population, and topic heterogeneity cannot be averaged away within one
  topic set.

**2. Near the ±0.10 edge, matching is close to a coin toss at any affordable
size.**
- **The rate:** a reference whose true distance from p_A lies within 0.05 of
  0.10 is misclassified 35–44% of the time under every allocation.
- **The cause:** with a standard error of about 0.07 for a difference at
  96/96, this is expected. Halving it would need roughly 1,000 responses per
  cell.
- **Far from the edge:** the error falls from 0.06–0.14 under *current* to
  0.04–0.10 under 46k-generation allocations.

**3. The verdict is reliable far from the 12-of-16 threshold and unreliable
near it, in both directions.**
- **Far from the threshold:** the four surfaces whose truth is comfortably
  FEASIBLE are reported FEASIBLE in 98–100% of pilots.
- **Low followability:** true P3 support is only 14 of 16, so the verdict
  flips to INFEASIBLE in 26–39% of pilots, and the selected A flips between
  N = 4 and N = 6.
- **Other operations harder (true P3 support 0 of 16):**
  - **Anti-conservative:** 85–89% of pilots report FEASIBLE, under every
    allocation including *uniform 96*.
  - **Mechanism:** P3 needs G5 to add two references from another operation.
    Several sit just outside the window, and classification noise pulls two
    of them in. A minimum-count rule over a fuzzy classification is
    anti-conservative when candidates crowd the edge. More data at pilot
    scale does not fix it.

**4. A and B stability.**
- **A:** stable (≥ 0.98 agreement) everywhere except *low_followability*,
  where it is 0.52–0.82; the two-draw allocation helps most.
- **B:** agreement is 0.76–0.94, and the pairs that alternate are both valid.
  Model heterogeneity lowers B agreement to about 0.8.
- **focal96:** it changes A and B agreement only marginally, because the A
  ranking is driven by the reference cells' noise rather than by p_A's.

**5. Cross-model and cross-frame heterogeneity**, at the sizes simulated, do
not reduce membership accuracy: G1 overlap is 0.54–0.56, against 0.51 for
*moderate*. B agreement is what they lower. Per-model P1 support is in the JSON,
under `p1_support_by_model`.

## 6. D14 validation: does the stability diagnostic catch the bad verdicts?

This is `d14_validation` in the JSON. For each surface, 40 simulated pilots
(current allocation) each got D14's topic-cluster bootstrap (60 resamples).
Each cell below is the share of pilots that are point-FEASIBLE *and* pass the
check.

| surface (truth) | point FEASIBLE | stable members ≥ 0.5 | ≥ 0.6 | ≥ 0.7 | bootstrap FEASIBLE share ≥ 0.65 | ≥ 0.8 |
|---|---|---|---|---|---|---|
| moderate (F) | 1.00 | 1.00 | 0.78 | 0.00 | 1.00 | 1.00 |
| model_differences (F) | 1.00 | 1.00 | 0.88 | 0.15 | 1.00 | 1.00 |
| frame_differences (F) | 1.00 | 1.00 | 0.75 | 0.03 | 1.00 | 0.98 |
| boundary_cluster (F) | 1.00 | 1.00 | 0.85 | 0.03 | 1.00 | 1.00 |
| low_followability (F) | 0.83 | 0.75 | 0.50 | 0.08 | 0.73 | 0.43 |
| **other_operation_harder (I)** | **0.75** | **0.73** | 0.28 | 0.00 | **0.75** | **0.70** |

**D14 is not a reliable gate.**
- **Bootstrap FEASIBLE share:** it does not detect the anti-conservative
  case. Its mean is 0.90 on the INFEASIBLE surface, against 0.75–0.98 on the
  FEASIBLE ones. The resamples are centred on the observed data, and those
  already contain the spurious matches.
- **Stable-member feasibility:** it trades the two errors and separates
  neither.
  - At 0.5 (majority inclusion) it keeps every truly feasible pilot and
    removes almost none of the false ones.
  - At 0.6 it cuts false FEASIBLE from 0.75 to 0.28, but rejects 12–25% of
    pilots on the clearly feasible surfaces, and passes only half of the
    *low_followability* pilots.
  - At 0.7 or above it rejects nearly everything.

**What changed as a result:**
- D14 is kept as a *diagnostic*: the inclusion frequencies, borderline
  matches, Stage-1-only sensitivity and majority-stable feasibility are
  reported and bound in Freeze 2.
- The earlier proposal to gate Freeze 2 on the stable-member verdict at 0.8
  inclusion is withdrawn. At that cut, 0 of 200 truly feasible pilots would
  have passed.
- The `FEASIBILITY_RESTS_ON_UNSTABLE_MEMBERS` flag uses the 0.5 cut, and is
  for review only.

## 7. D07 threshold sensitivity (B-pair separation)

This is `d07_sensitivity` in the JSON. Each surface was run on 200 simulated
B-only panels, with B cells at n = 96 (Stage 1 plus refinement, as B cells near
the band are refined) and at n = 32 (Stage 1 only). The surfaces add the
synthetic model shifts.

**Share of panels in which a pair is selected, by threshold:**

| B surface | true median p_B, B8 to B13 | n | 10 pp | **15 pp** | 20 pp |
|---|---|---|---|---|---|
| default | .13 .28 .43 .57 .71 .86 | 96 | 1.00 | **1.00** | 1.00 |
| steep | .10 .28 .45 .62 .80 .97 | 96 | 1.00 | **1.00** | 1.00 |
| shallow | .35 .39 .43 .46 .50 .54 | 96 | 0.99 | **0.83** | 0.11 |
| shallow | (same) | 32 | 0.97 | **0.67** | 0.29 |
| plateau (audit F9) | .22 .22 .23 .91 .96 .98 | 96 | 0.01 | **0.01** | 0.01 |

**True separation of the selected pairs:**

| B surface | n | mean | minimum |
|---|---|---|---|
| default | 96 | 0.33 | 0.28 |
| steep | 96 | 0.34 | 0.34 |
| shallow | 96 | 0.18 | 0.11 (at 10 or 15 pp) |
| shallow | 32 | 0.15–0.17 | **0.07** |

**Reading:**
- **Typical surfaces:** the threshold does not bind. The selected pairs are
  truly 0.28–0.34 apart at every threshold.
- **Shallow surface:** this is where it matters. The largest true gap is only
  0.186.
  - At 15 pp, a pair is selected in 83% of panels at n = 96 and 67% at
    n = 32.
  - At n = 32, noise can admit a pair whose true separation is 0.07.
  - At 20 pp, the rule fails a surface whose largest true gap is 0.186,
    which is correct but strict.
- **Plateau:** the per-limit headroom requirement, not the separation rule, is
  what makes the counterexample fail. The permissive limits sit above the
  0.85 band edge.

**Recommendation for D07:**
- **Threshold:** keep 15 pp as the proposed default. It removes degenerate
  pairs without failing surfaces that have a real strict/permissive contrast.
- **Headroom:** the researcher should decide whether a permissive limit above
  0.85 may serve as the permissive arm. Under the current rule, the plateau
  surface fails B selection.

## 8. Recommendation

1. **Keep the proposed allocation.** That is 32 per cell in Stage 1, and a
   Stage 2 of at most 240 cells × 64 new-topic responses: 30,976
   generations at most.
   - **Effect of more generations:** every tested increase (+15% to +50%)
     improves G1 overlap by at most 0.08 and near-edge errors by at most
     0.04, and leaves the near-threshold verdict errors in place.
   - **What limits precision:** the 96 pilot topics, not the Stage 2
     budget.
   - **If a cheap improvement is wanted anyway:**
     - *focal96* (+4,608 generations, +15%) gives small, non-negative gains
       in B stability;
     - *two draws per refined cell* (+50%) is the only option that clearly
       stabilised A on the hardest surface.

   Neither is recommended as necessary. **Allocation is unchanged in the
   code. D05 and D06 still need approval.**
2. **Keep ±0.10 raw point-estimate matching (D10)**, with the disclosure that
   near-edge classification is close to chance. The interval-based fields
   already reported (`diff_ci`, `within_tolerance_with_confidence`) and D14's
   inclusion frequencies are the sensitivity. D14 is reported, never
   gating.
3. **The researcher should decide about D11's minimum-count coverage near
   the threshold.** It is the one unresolved weakness the simulation exposes.
   The options are:
   - (a) accept and disclose the bias;
   - (b) raise the P2/P3 minima from 2 to 3;
   - (c) count, for coverage only, references whose Newcombe interval lies
     inside ±0.10 (a change to the coverage rule, not to membership).

   Each is a scientific decision, and none is made here. Options (b) and (c)
   would reduce false FEASIBLE verdicts at the cost of more false INFEASIBLE
   ones, and should be simulated with `simulate.py` before adoption.
4. **Treat the real pilot's FEASIBLE verdict as provisional** when D14 shows
   a FEASIBLE share below 0.8, or when the supported counts sit within two
   configurations of 12.

## 9. Unresolved scientific trade-offs

- **The ±0.10 tolerance and point-estimate matching.** These are design
  values and were not changed. The simulation shows they classify the
  near-edge references by chance. A banded rule (match only when the interval
  lies inside ±0.10, already reported as `within_tolerance_with_confidence`)
  would be more stable but would shrink G1. That is a scientific decision for
  the researcher, not a remediation.
- **Minimum-count coverage near the threshold.** The rule is
  anti-conservative there. The options are:
  - raise the minima;
  - count, for coverage only, references whose interval lies inside ±0.10;
  - accept the bias and report it, with D14's diagnostics.

  The simulation shows that D14's stable-member verdict is not a reliable gate
  (§6).
- **Topic count.** Membership precision is topic-limited. More pilot topics
  (for example a 128-topic Stage 2) would shrink the reserved confirmatory
  bank from 480 to 448. This was not simulated as a design option, because
  it changes the split.
- **The surfaces are invented.** Real models may have larger topic effects,
  stronger frame effects, or many more references near the edge. The pilot's
  own D14 report is the empirical check.
