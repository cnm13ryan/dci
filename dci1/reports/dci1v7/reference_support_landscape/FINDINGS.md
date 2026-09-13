# Why Δ_R is supported and the difficulty-response analysis is not — the reference-support landscape on the corrected chance basis

**Status: DIAGNOSTIC / EXPLORATORY.** Everything here is reconstructed read-only
from stored v6/v7 evidence (registered trees and development rehearsals) by
`dci1/tools/v7_reference_support_landscape.py`; the numbers are in
`landscape.json`, the tables in `REPORT.md`, the figures in `plots/`. No record,
verdict, threshold or rule was changed. Development-tree numbers are development
numbers. The chance column is §13.2's κ_c measured on the grid runs'
unconstrained cells (the 2026-08-29 correction); the recorded `0.0` column is used
only where a row is explicitly labelled `kappa0`.

Bases read: the four registered v7 replications, the four v6 replications, and
the four development rehearsals that reached Gate 3 (`dci1v7-development`
qwen3-4b; `-r3` qwen3-4b and gemma-3n-e2b-it; `-r4` qwen3-4b-instruct-2507, whose
confirmatory generation was 9/12 block-runs in when read). r4 gemma-3n-e4b-it had
no Gate-2 record yet. On the recorded (κ=0) tables the production kernels
reproduce every signed Gate 2.5/3A/3B record (see the chance-basis impact
report), which is what makes the reconstruction a statement about the study.

## 0. Answers in one screen

| # | Question | Answer |
|---|---|---|
| 1 | Reference support near A | Dense on the Qwens and on gemma-3n-e2b-it: within ±0.10 of ι_A, 17–33 §12.6-eligible rungs from 8–11 families, of which 7–21 pass the **full** V(R) from 5–8 families. Thin on v7 gemma-3n-e4b-it: 29 eligible rungs but only **6** pass full V(R) — three Tier-1 families (exactly the **3** used, zero spare) plus one Tier-3 class candidate. |
| 2 | Are R1/R2/R3 well matched? | Yes, at calibration: \|ι_R − ι_A\| ≤ 0.017 on 10/12 replications (max 0.050, gemma-e4b), all Tier-1 same-form, κ_R = 0.000–0.005, §13.7-stable on both splits. Realised on the confirmatory blocks the gaps are 0.004–0.090 (all < 0.15), and A's realised ι sits *above* all three references on 3 of 4 rehearsals. |
| 3 | Why does C4 fail? | Two different reasons by model family. **Qwens**: the spread exists in the measured pool (7–8 straddling groups if every measured rung counted) and is lost to §12.6's [0.10, 0.90] eligibility band, which removes the easy rungs (10–29 Tier-1/2 rungs at p_solo > 0.90 per replication); the families that fail (MK1, MK2, XC3 / MK1, MK5, MK6) have all-measured spans 0.43–0.51 and eligible spans 0.14–0.39. **Gemmas**: genuine lack of spread — the raw pool gives the same 1–4 groups; MK3/MK6/MK7/MK8 are flat ladders (all-measured span 0.05–0.27) sitting entirely below ι_A, and the straddling families (MK1/MK2/MK4/MK5) span only 0.20–0.34. |
| 4 | Quantity or spread? | Not quantity: C5 (≥16 eligible) is met with 54–104 rungs and C6 with 10–11 Tier-1/2 families everywhere. It is **within-family spread over eligible rungs** (SPAN_SHORT) plus **one-sidedness** (MISSING_SIDE). The chance-basis correction and the ι_A basis move C4 on no replication. |
| 5 | Responsible families | Qwen3-4b (4 runs): MK2 misses by 0.005–0.009, XC3 by 0.05–0.06, MK6 by 0.20, MK1 by 0.24–0.26 — MK1's rungs 3–7 are flat at ι 0.66–0.70 while rungs 1–2 are ineligible at p_solo 0.92–0.98. Qwen-2507 (3 runs): MK6 misses by 0.003–0.012, MK7 by 0.03–0.04, MK1, MK5. Gemmas: MK1/MK2/MK4/MK5 spans 0.20–0.34; MK3/MK6/MK7/MK8 never reach A. |
| 6 | What the plots show | Local density and global one-sidedness at once: a tight cluster of eligible, V(R)-passing Tier-1 rungs inside ±0.10 of ι_A; ladders that are steep on one side of A and flat or ineligible on the other; and (on the composed plot) four models' worth of D(B←X) points that all sit inside a 0.04–0.07-wide ι window per model. |
| 7 | Composed B+R data beyond R1–R3 | **None for any reference candidate.** What exists: B+R_j / R_j+B for the three core references on 384 blocks × 8 draws (dev qwen3-4b, r3 qwen3-4b, r3 gemma-e2b; r4 qwen-2507 at 320/384) and on Gate 4's 24 topics; B+CL / CL+B on r3 gemma-e2b; and Gate 2.75's probe stand-ins (PS1/PS2/PS3, 192 topics × 4 draws, both orders) — probe-only instruments, never selectable, with no unconstrained-cell κ and hence no registered ι. |
| 8 | Slope from existing data? | **No.** Per rehearsal the three composed references span a realised ι width of 0.037–0.067; a 3-point OLS slope has 95% half-widths of ±0.56–1.02 per unit ι; ι_A lies outside the realised range on 3 of 4 rehearsals; §13.13 (≥2 companions below and ≥2 above from ≥2 families each side) is unmet by construction. |
| 9 | What is missing | ≥ 4 composed companions (2 strictly below, 2 strictly above ι_A, two families per side) with B+X and X+B on the confirmatory blocks; the §13.12 design wants 6. The candidate rungs **already exist in the calibration tables** (solo, κ, κ^B, both-split stability measured) — they lack only composed generation. What does not exist anywhere is an admissible rung above ι_A + 0.15 when ι_A ≥ 0.68 (8 of 12 replications), because V_head's Wilson-upper ≤ 0.90 caps p_solo at ≈ 0.855. |
| 10 | Cheapest experiment | Per model, 6 already-calibrated Tier-1 rungs (two per core family where the family has them, otherwise the widest admissible same-tier rung), B+X and X+B on the existing 384 confirmatory blocks at 8 draws plus solo:X; the unconstrained cell is re-scored from text at zero generation cost. ≈ 9.2k generations per rung, ≈ 55k per model (a third of one confirmatory design). Fit §11.8's registered form with §17.2's refit bootstrap. Details in §10. |
| 11 | Does this change Δ_R? | No. Δ_R's identification rests on C1/C3/C5/C6, §13.7, §13.8 and §13.15, all met on the corrected basis; the dev core sets are unchanged; realised gaps < 0.15. Two caveats are recorded in §11: the three references are all slightly *easier* than A as realised (a one-sided mismatch of 0.02–0.09 a slope could adjust for but cannot be estimated), and §13.15's redundancy is weaker than it reads (at least one frozen backup is not an admissible core reference on 11/12 replications, both on 3; the "≥ 5 qualified families" count is Gate 2.5's, not the full V(R)'s). |

## 1. What was reconstructed, and on what basis

For each replication: the Gate-2 pooled and split calibration tables with the
corrected κ_c; §12.6 eligibility under the registered formulation (U4 = E2: raw
solo compliance in [0.10, 0.90] and vacuity ≤ 0.10; a κ ≥ 0.99 rung has no
coordinate and is dropped, A16); C1–C8 through `regime.coverage_criterion` at
the Gate-2 ι_A (the reading that gates, v6 A3 / v7 A7); Gate 2.5 qualification;
§13.7 stability on the corrected split tables (10,000 resamples, seed 0); Gate
3B selection (`selection.select_all`), including the per-family §13.12 spectrum
attempt; Gate 3C support. Per rung, every V(R) component is evaluated for the
rung's natural slot. Two diagnostic what-ifs are computed beside the registered
reading and labelled as such: C4 with every measured rung treated as eligible
("raw pool"), and §13.7 condition 1 *without* V_diff folded in ("unfolded";
same bootstrap intervals, per-split admissibility re-read on V_head, V_chance,
V_inter alone). Composed outcomes are read from the scored rows of Gate 4, the
confirmatory block-runs and the Gate-2.75 probe; D(B←X) = P(B | B solo) −
P(B | B+X) per block, paired; the values reproduce the final reports' production
estimates to four decimals (`REPORT.md`, "Final-report rows").

## 2. Local support near A (corrected basis)

| replication | ι_A | eligible (below/above) | ±0.05: elig. rungs / families / full-V(R) | ±0.10 | ±0.15 | families passing full V(R) |
|---|---:|---|---|---|---|---|
| v7 gemma-e2b | 0.617 | 100 (69/31) | 18 / 8 / 14 | 33 / 10 / 21 | 47 / 12 / 21 | MK4, MK1, MK2, XC3, MK5 |
| v7 gemma-e4b | 0.725 | 104 (87/17) | 15 / 8 / 6 | 29 / 11 / 6 | 35 / 11 / 6 | **MK5, MK4, MK6 only** |
| v7 qwen3-4b | 0.683 | 81 (60/21) | 11 / 6 / 10 | 18 / 10 / 13 | 26 / 10 / 13 | MK1, MK6, MK7, MK2, MK5, XC3 |
| v7 qwen-2507 | 0.540 | 65 (32/33) | 10 / 9 / 6 | 23 / 11 / 8 | 30 / 13 / 8 | MK1, MK3, MK4, MK2, MK6, MK7, MK8 |
| v6 gemma-e2b | 0.629 | 98 (71/27) | 13 / 7 / 10 | 29 / 8 / 20 | 41 / 11 / 20 | MK5, XC3, MK4, MK1, MK2 |
| v6 gemma-e4b | 0.709 | 95 (76/19) | 12 / 7 / 6 | 22 / 10 / 7 | 33 / 12 / 7 | MK1, MK5, MK4, MK6, MK2, XC3 |
| v6 qwen3-4b | 0.704 | 82 (62/20) | 13 / 8 / 10 | 20 / 10 / 14 | 27 / 11 / 14 | MK1, MK6, MK5, MK7, XC3, XC1, MK2 |
| v6 qwen-2507 | 0.565 | 54 (27/27) | 11 / 8 / 8 | 17 / 8 / 8 | 23 / 9 / 8 | MK5, MK6, MK8, MK4, MK3, MK2, MK7 |
| dev qwen3-4b | 0.688 | 83 (60/23) | 11 / 6 / 10 | 19 / 10 / 13 | 24 / 10 / 13 | MK1, MK7, MK6, MK2, MK5, XC3 |
| r3 gemma-e2b | 0.609 | 87 (63/24) | 15 / 8 / 12 | 28 / 11 / 16 | 36 / 13 / 16 | MK2, MK1, XC3, MK5, MK4 |
| r3 qwen3-4b | 0.685 | 82 (61/21) | 11 / 6 / 10 | 18 / 10 / 14 | 25 / 10 / 14 | MK1, MK7, MK6, MK5, MK2, XC3 |
| r4 qwen-2507 | 0.540 | 66 (34/32) | 11 / 9 / 8 | 23 / 11 / 14 | 32 / 15 / 14 | MK4, MK3, MK8, MK1, MK6, MK2, MK5, MK7 |

Read: the ±0.10 neighbourhood of A holds 6–21 rungs that pass every registered
admission rule, from 4–8 families (Tier-1/2 families: 3–8). That is *local*
support — the statement "there are many plausible references near A" is
supported on 11 of 12 replications (gemma-e4b v7 excepted). It says nothing
about global spread: the eligible population is 69–84 % *below* A on every
replication but the 2507 checkpoint (≈ 50 %), and the eligible Tier-1/2 range
tops out at ι ≈ 0.86–0.90 — the [0.10, 0.90] band, applied to the Wilson
interval, admits nothing above p_solo ≈ 0.855.

## 3. R1/R2/R3: tightly matched at calibration; a little easier than A as realised

Distances |ι_R − ι_A| on the corrected pooled table (all §13.7-stable, all κ ≤ 0.005):

| replication | R1 | R2 | R3 |
|---|---|---|---|
| v7 gemma-e2b | MK4:8 0.002 | MK1:1 0.002 | MK2:7 0.012 (signed record: XC3:10 0.014, re-ordered by κ = 0.007) |
| v7 gemma-e4b | MK5:6 0.031 | MK4:7 0.031 | MK6:3 0.050 |
| v7 qwen3-4b | MK1:6 0.004 | MK6:8 0.011 | MK7:2 0.012 |
| v7 qwen-2507 | MK1:7 0.007 | MK3:3 0.012 | MK4:5 0.017 |
| dev qwen3-4b | MK1:7 0.001 | MK7:2 0.007 | MK6:8 0.015 |
| r3 gemma-e2b | MK2:7 0.002 | MK1:1 0.013 | MK5:8 0.021 |
| r3 qwen3-4b | MK1:6 0.001 | MK7:2 0.002 | MK6:8 0.012 |
| r4 qwen-2507 | MK4:5 0.006 | MK3:3 0.010 | MK8:4 0.016 |

Realised on the confirmatory blocks (solo and unconstrained cells of every slot
on all 384 blocks): dev qwen3-4b gaps 0.023 / 0.053 / 0.090 with ι_A realised at
0.719 (calibration 0.688) and all three references at 0.630–0.697; r3 qwen3-4b
0.062 / 0.049 / 0.086 (ι_A 0.717, refs 0.631–0.668); r3 gemma-e2b 0.050 / 0.010
/ 0.037 (ι_A 0.617, refs 0.566–0.607); r4 qwen-2507 0.004 / 0.017 / 0.022 (ι_A
0.565, refs 0.543–0.582). All under §13.8's 0.15, so no companion-difficulty
block attaches. But the pattern is the one a nearest-neighbour selection on a
noisy coordinate produces: a calibration distance of ≤ 0.015 becomes a realised
distance of 0.02–0.09, and on three of four rehearsals every reference lands on
the *easy* side of A. Statement 2 is supported with that caveat, and statement 3
follows from it: Δ_R is a comparison of A against three same-form Tier-1 marker
constraints of the same difficulty to within ≈ 0.05–0.09, on the same blocks and
in the same order. It is not, and does not claim to be, a statement about how
delivery loss varies with difficulty.

## 4. Why C4 fails, family by family

C4 as registered: at least six feature groups contain a family that straddles
ι_A with at least three §12.6-eligible rungs spanning ≥ 0.40 in ι. The
reconstruction evaluates it on eight bases per replication (`REPORT.md`, "C4
diagnostic"). The gating count on the calibrated corrected basis, and what it
becomes when one ingredient is changed:

| replication | gating | κ=0 table | unconstrained-basis ι_A | pre-screen certificate | pre-screen, same rungs | raw pool (ignore eligibility) | first deficiency of the near misses |
|---|---:|---:|---:|---:|---:|---:|---|
| v7 gemma-e2b | **2** | 2 | 2 | 6 | 3 | 2 | SPAN_SHORT MK1 0.34, MK2 0.32, MK4 0.32 |
| v7 gemma-e4b | **4** | 4 | 4 | 11 | 5 | 4 | SPAN_SHORT CR5 0.24; 16 families one-sided |
| v7 qwen3-4b | **5** | 5 | 5 | 6 | 6 | 8 | SPAN_SHORT MK2 0.391, XC3 0.34, MK6 0.20, MK1 0.14 |
| v7 qwen-2507 | **4** | 4 | 4 | 10 | 7 | 7 | SPAN_SHORT MK6 0.388, MK7 0.37, MK1 0.26, MK5 0.19 |
| v6 gemma-e2b | **3** | 3 | 3 | 6 | 3 | 3 | SPAN_SHORT MK4 0.34, MK2 0.22 |
| v6 gemma-e4b | **3** | 3 | 3 | 10 | 6 | 4 | SPAN_SHORT MK5 0.32 |
| v6 qwen3-4b | **6 (met)** | 6 | 6 | 9 | 7 | 8 | — |
| v6 qwen-2507 | **5** | 5 | 5 | 0 | 0 | 7 | SPAN_SHORT MK7 0.36, MK1 0.25, MK5 0.22 |
| dev qwen3-4b | **5** | 5 | 5 | 7 | 7 | 8 | SPAN_SHORT MK2 0.395, XC3 0.34, MK6 0.20, MK1 0.16 |
| r3 gemma-e2b | **1** | 1 | 1 | 7 | 4 | 1 | SPAN_SHORT MK1 0.32, MK4 0.32, MK5 0.30, MK2 0.20 |
| r3 qwen3-4b | **5** | 5 | 5 | 6 | 6 | 8 | SPAN_SHORT MK2 0.392, XC3 0.35, MK6 0.20, MK1 0.15 |
| r4 qwen-2507 | **4** | 4 | 4 | 8 | 6 | 8 | SPAN_SHORT MK6 0.397, MK7 0.36, MK1 0.29, MK5 0.19 |

The five hypotheses, adjudicated:

- **Genuine lack of difficulty spread — yes on the Gemmas.** Treating every
  measured rung as eligible changes nothing (2→2, 4→4, 3→3, 1→1; v6 e4b 3→4).
  Four of the eight marker families (MK3, MK6, MK7, MK8) are flat — all-measured
  spans 0.05–0.27 — and lie entirely below ι_A (0.05–0.45 against ι_A
  0.61–0.73); the four that straddle (MK1, MK2, MK4, MK5) span 0.20–0.34 over
  their eligible rungs. On gemma-e4b only three families pass the full V(R)
  at all. Monotonicity is weak: on gemma-e2b only 2–3 of 11 Tier-1/2 ladders
  have Spearman(restrictiveness, ι) ≤ −0.8, and XC3 (exact sentence count) runs
  the wrong way (ρ = +0.6 to +0.85: more sentences is *easier* for this model).
- **Spread exists in the raw pool but is lost after eligibility — yes on the
  Qwens.** Ignoring eligibility gives 7–8 straddling groups on every Qwen
  replication; the loss is the [0.10, 0.90] band removing the easy rungs
  (p_solo > 0.90): 10–11 Tier-1/2 rungs on qwen3-4b, 27–29 on the 2507
  checkpoint, in families MK1, MK2, MK4, MK6, XC1, XC3 (and MK3, MK5 on 2507).
  The families that fail C4 are exactly the ones trimmed: MK1 0.43–0.46
  all-measured → 0.14–0.29 eligible; MK2 0.50–0.51 → 0.39; XC3 0.45–0.48 →
  0.34–0.35; on 2507 MK5 0.51 → 0.19, MK6 0.49–0.50 → 0.39–0.40. The qwen3-4b
  ladders are also flat in the middle (MK1 rungs 3–7 at ι 0.66–0.70, ρ = −0.71
  to −0.79) so the eligible span collapses once the extremes are removed.
- **Pre-screen overstated the spread through noise — partly, on every
  replication.** The certificate counts 6–11 groups (0 on v6 qwen-2507, whose
  pre-screen ι_A was 0.875). Restricting the pre-screen table to the rungs the
  calibration table actually carries already drops it to 3–7 (Tier-3 ladders
  beyond §12.7's 24-rung cap, and pre-screen-only rungs, pad the certificate:
  gemma-e4b 11 → 5). On the *same* rungs, the 24-topic × 1-draw span exceeds the
  192 × 4 span by +0.02 to +0.10 per family on average, and 1–3 families per
  replication have a pre-screen span ≥ 0.40 that calibrates below 0.40 (the
  reverse happens 0–1 times). ι_A itself moved between the two bases by −0.13
  (qwen-2507 v7), −0.31 (v6 qwen-2507), −0.05 to −0.08 (gemma-e2b), +0.06
  (gemma-e4b v7).
- **Severity does not produce monotone difficulty — partly, model-dependent.**
  Qwens: 7–8 of 11 Tier-1/2 ladders are cleanly monotone (ρ ≤ −0.8); the
  exceptions are MK1/MK2 (flat middles) and XC2 (comma count, flat at ι ≈ 0.0–0.2,
  ineligible). Gemmas: 2–3 of 11 on gemma-e2b, 8 of 11 on gemma-e4b; MK7 has a
  span of 0.05 on every Gemma replication; XC3 is inverted.
- **Chance-compliance filtering — no.** κ_c is 0.000 for every Tier-1 marker
  rung; the corrected column changes the C4 count on no replication, nor does
  the ι_A basis (blend vs unconstrained cell). The correction matters for
  Tier-3 candidates only (κ up to 0.98), which C4 rarely leans on (RF11, CR5,
  RF7 near misses).
- **The C4 construction itself — restrictive in a specific way, and not the
  binding constraint for the spectrum (§5).** Descriptively, with the span floor
  at 0.30 instead of 0.40 the count reaches 6 on qwen3-4b (all four runs: 7–8),
  qwen-2507 (6–7) and v6 e2b–e4b reach 4; at 0.20 the Gemmas reach 4–6. This is
  reported as a description of where the near misses sit (MK2 by 0.005–0.009,
  MK6 by 0.003–0.012 — sampling-noise-sized), not as a proposal.

One more mechanism, on the design path rather than in the data: §12.6's
expansion — the only rule that measures the frozen reserve rungs 9–12 of the
marker families — never ran on any replication (`expansion.rounds` is empty on
all twelve), because the noisy pre-screen certified C1–C6 every time. The
ladders were therefore never extended on the deficient side, and the only rungs
that could have carried a Tier-1 family's span past 0.40 without leaving the
band (the harder end) were never generated.

## 5. The registered spectrum could not have been drawn even where C4 holds

Two registered facts interact (RESEARCH_STATE §4an records the first as a
tension left standing for v8):

1. §13.7 condition 1 requires independent admissibility on each split under
   V_head, V_chance, V_inter **and V_diff**, and §13.12 requires a spectrum rung
   to pass V_stab. A spectrum rung must therefore sit inside §13.8's ±0.10
   caliper *on both splits*. The registered spectrum pool is 5–21 rungs and
   spans 0.06–0.16 in ι (e.g. dev qwen3-4b: 13 rungs in [0.622, 0.768];
   gemma-e4b v7: 5 rungs in [0.676, 0.757]). The registered triples that exist
   have outer rungs within 0.03–0.10 of A (dev qwen3-4b: MK1 0.663 / 0.697, MK6
   0.661 / 0.768). §13.12's ±0.20 targets are unreachable by construction.
2. The upper target ι_A + 0.20 also exceeds the admissible ceiling whenever
   ι_A > 0.655: V_head's Wilson upper ≤ 0.90 at n = 192 admits p_solo ≲ 0.855,
   so a chance-free family's ι cannot exceed ≈ 0.86. That is 8 of 12
   replications (ι_A 0.68–0.73).

Consequence: **C4 is neither necessary nor sufficient for the spectrum arm.**
v6 qwen3-4b meets C4 (6/6) and binds zero triples — every qualified family has
its admissible rungs on one side of A — so §13.12 exhausts and the spectrum arm
is not generated anyway. Conversely, C4 gates the spectrum on a within-family
span (≥ 0.40 over eligible rungs) that the spectrum is not allowed to use
(≤ 0.20 under the folded V_stab). On the eleven failing replications the
ranking of causes is therefore: §13.7's folding (removes ≥ 0.10 rungs) ≫ the
0.90 ceiling on the upper side ≫ C4's span floor. With V_diff unfolded
(diagnostic), the same tables hold 35–77 spectrum-eligible rungs spanning
[0.20–0.26, 0.77–0.83], and the three core families could each supply a rung
strictly below and strictly above A on dev/r3 qwen3-4b and r4 qwen-2507 (not on
the Gemmas' MK5, which has nothing admissible above).

## 6. What the plots show

- `plots/landscape_<tree>_<model>.png` — every measured rung on the corrected ι
  axis by family (Tier 1 blue, Tier 2 green, Tier 3 grey), severity labelled;
  filled = eligible and passes full V(R), diamond = spectrum-eligible under the
  registered rule, faded = eligible only, hollow = ineligible; ι_A with the ±0.10
  caliper and ±0.15 band; R1–R3 starred; frozen backups boxed (with "fails full
  V(R)" where true). Reads as a dense column of admissible Tier-1 rungs at A
  with everything else to the left.
- `plots/ladders_<tree>_<model>.png` — severity → ι per family with ι_A and the
  caliper: the flat middle of MK1 on qwen3-4b, the steep monotone ladders of
  MK3/MK4/MK5/MK7, the ineligible easy rungs above 0.90, the flat Gemma
  families below A, the inverted XC3 on Gemma, and per panel the eligible span
  and C4's first deficiency.
- `plots/c4_spans_all_replications.png` — eligible span per family across all
  twelve replications (green = C4 group met, red = straddles but fails, grey =
  one side only): the Qwens fail by span, the Gemmas by side.
- `plots/nearby_support_vs_spread.png` — local support (eligible and
  full-V(R) rungs within ±0.05/0.10/0.15) against the total eligible spread
  and the registered spectrum pool's spread: high bars, low crosses.
- `plots/composed_D_vs_iota_confirmatory_blocks.png` and
  `…_gate4_24_topics.png` — D(B←X) for the companions that have composed rows,
  by configuration and model, A hollow: per model a 0.04–0.07-wide cluster.
  The order effect dwarfs any difficulty effect (gemma-e2b: D(B←A) −0.03 with
  B first, +0.21 with B second; the references +0.22 to +0.32 with B second).
- `plots/composed_D_vs_raw_solo.png` — the same on §13.2's secondary coordinate,
  where the probe stand-ins (no registered ι) can be shown, faded.

## 7. Composed B+R data that exist beyond R1/R2/R3

For reference *candidates*: none. Every replication that generated a core arm
composed exactly the three admitted references. The complete inventory of
composed cells with B:

| replication | A | R1–R3 | other |
|---|---|---|---|
| dev qwen3-4b | 384 blk × 8 dr, both orders | same | probe PS2:3, PS3:6 (192 topics × 4 draws, both orders) |
| r3 qwen3-4b | same | same | probe PS2:3, PS3:6 |
| r3 gemma-e2b | same | same | CL = RF12:6 (384 × 8), probe PS1:8, PS2:5, PS3:10 |
| r4 qwen-2507 | 320 of 384 blocks so far | same | probe PS2, PS3 |
| v7 registered (4) | Gate 4 only, 24 topics | **none** (core arm dropped pre-A7) | CL on the Gemmas (24 topics); probe stand-ins |
| v6 registered (4) | — | none | probe stand-ins on the Gemmas |

The probe stand-ins carry composed outcomes at 192 topics (D(B←P) e.g. dev
qwen3-4b: P2 −0.055 / +0.065, P3 −0.165 / −0.031; gemma-e2b: P1 +0.29 / +0.66, P2
+0.18 / +0.38, P3 0.00 / +0.42), but they are probe-only instruments (v6 A10),
never selectable, and were never scored on the unconstrained cell, so they have
raw solo compliance and no ι. They are shown on the secondary-coordinate plot
and nowhere else.

## 8. Can the existing data estimate a difficulty-response slope? No

Per rehearsal and configuration, the three composed references span a realised
ι width of 0.037–0.067; the 3-point OLS slope of D(B←R) on realised ι has a
95 % half-width of ±0.56 to ±1.02 per unit ι (dev qwen3-4b: −0.53 ± 0.56 and
−0.58 ± 0.58; r3 gemma-e2b +1.34 ± 0.66 and 0.00 ± 1.02; r3 qwen3-4b −0.71 ±
0.93 and −0.14 ± 1.00; r4 qwen-2507 −0.44 ± 0.96 and −0.82 ± 0.99). ι_A lies
outside the realised range on three of the four, so a prediction at A would be
an extrapolation; and §13.13 requires two companions strictly below and two
strictly above from two families each side, which three references cannot
provide. β and δ_diff are not identified from any stored data, and no
combination of calibration-only rows, Gate-4 rows and probe rows changes that:
calibration rows carry no composed outcome by construction (§13.11), Gate 4's
24 topics give D half-widths of ±0.06–0.13 on the same three references, and
the probe stand-ins have no coordinate.

## 9. Exactly what is missing

- **Points**: at least 4 composed companions beyond the core set (2 strictly
  below, 2 strictly above ι_A, two families per side, §13.13), realistically 6
  (one below and one above per core family, §13.12's shape), each with B+X and
  X+B on the confirmatory blocks and a solo:X cell for the realised coordinate.
- **Regions**: below A, the target ι_A − 0.20 is available in every calibrated
  Qwen table (qwen3-4b: MK7:3 0.48, MK1:8 0.54; 2507: MK4:6 0.34, MK3:4 0.32,
  MK8:8 0.28); above A, the target ι_A + 0.20 ≈ 0.88–0.89 is unreachable on qwen3-4b
  and the Gemmas, and the widest admissible rungs sit at 0.79–0.80 (MK7:1,
  MK6:5) — about +0.11 above A. On the 2507 checkpoint (ι_A 0.54) both targets
  are reachable (MK4:4 0.66, MK8:2 0.79 above; MK4:6 0.34, MK3:4 0.32 below). On
  gemma-e2b the *lower* side is thin (MK1:8 0.39 is the only core-family rung
  far below; MK2 and MK5 have nothing measured below A except MK2:1 at 0.594).
- **Already calibrated**: every rung named above has solo, κ, κ^B, vacuity and
  both-split stability on the Gate-2 record and passes every V(R) component
  except the caliper (`rungs[*].spectrum_eligible_unfolded_diagnostic` in
  `landscape.json`). They lack only B+X generation.
- **Not calibrated anywhere**: the reserve rungs 9–12 of the marker families,
  which are what a Gemma ladder would need to reach below A within its core
  families.

## 10. The smallest follow-up that would answer the difficulty-response question

Scope: a development-namespace experiment on the completed rehearsals (dev/r3
qwen3-4b, r4 qwen-2507, r3 gemma-e2b), reusing their frozen m\*, n\*, blocks and
wordings, and their already-calibrated candidates. It is not an amendment of the
registered v7 rule set — under §13.7 as registered these rungs are not spectrum
rungs, and RESEARCH_STATE §4an already records that tension for v8.

| model | core (existing) | add below A (ι) | add above A (ι) |
|---|---|---|---|
| qwen3-4b (dev / r3) | MK1:7 or :6, MK7:2, MK6:8 | MK7:3 (0.48), MK1:8 (0.54), MK6:7 (0.66) | MK7:1 (0.80), MK6:5 (0.79), MK1:3 (0.69–0.70) |
| qwen-2507 (r4) | MK4:5, MK3:3, MK8:4 | MK4:6 (0.34), MK3:4 (0.32), MK8:8 (0.28) or MK8:6 (0.46) | MK4:4 (0.66), MK8:2 (0.79); MK3 has no admissible rung above → use MK7:1 (0.81) or MK2:6 (0.83) as a fourth-family point |
| gemma-e2b (r3) | MK2:7, MK1:1, MK5:8 | MK1:8 (0.39), MK1:6 (0.47); MK2:1 (0.59, barely below) — the lower side needs reserve rungs 9–12 of MK2/MK5 calibrated first (≈ 1.5k generations per rung on 192 × 4 × 2 splits) | MK2:2 (0.80), MK1:3 (0.71), MK5:5 (0.76) |

- **Cells**: pair:B+X and pair:X+B on all 384 confirmatory blocks at 8 draws
  (6,144 generations per companion) plus solo:X (3,072) for the realised ι; the
  unconstrained cell already exists on every block and is re-scored for X from
  the stored text at zero generation cost (§26 identity; scoring is redone from
  text on every pass). ≈ 9.2k generations per companion, ≈ 55k for six, against
  ≈ 80k for the existing 26-cell core design and 172k for a full design.
- **Both orders: yes.** The order effect is the largest thing in the composed
  data (gemma-e2b: D(B←A) −0.03 vs +0.21; qwen3-4b −0.12 vs −0.02), §11.8 is
  fitted per configuration, and F11's order contrasts are registered.
- **Model**: §11.8's registered primary form Y_{f,s} = α_f + β d_{f,s} on the
  nine points (three core families × three severities) per configuration, OLS
  with family intercepts, predicted at ι_A through the mean intercept; §17.2's
  block bootstrap that refits every replicate and re-evaluates §13.13; the
  secondary fit on raw solo compliance; where a family contributes only one side,
  the same form with the fourth-family point and a stated intercept convention
  (reported, not licensed).
- **Precision**: D(B←X) has SE ≈ 0.013 per configuration at 384 blocks; with
  nine points whose ι spread has sd ≈ 0.12–0.16, SE(β) ≈ 0.03 per unit ι. A
  slope of 0.25 (one SESOI of loss across a 0.40 difficulty span) would be ≈ 8
  SE; β = 0.10 would be ≈ 3 SE.
- **What it would newly allow**: an estimate of β (does difficulty predict
  delivery loss at all, within same-form marker constraints?) and of δ_diff =
  D(B←A) − Ŷ_A with §13.13's support satisfied — i.e. statement 6, "A has an
  effect beyond what generic difficulty predicts", at development level; and a
  measurement of how far a ±0.10 caliper mismatch could bias Δ_R (β × 0.05–0.09).
  It cannot license a confirmatory claim under v7 as registered.

## 11. Does any of this change the interpretation of the existing Δ_R results?

No number moves. The dev qwen3-4b Δ_R (−0.0009 / +0.0144), r3 qwen3-4b (−0.0030 /
+0.0126) and r3 gemma-e2b (−0.0244 / −0.0712, A comparatively better than its
references) rest on core sets that the corrected basis re-selects unchanged,
on C1/C3/C5/C6 met, on §13.7 stability met, and on realised gaps under 0.15.
Two caveats belong beside them:

1. **Direction of the residual mismatch.** On three of four rehearsals all
   three references are easier than A as realised (by 0.02–0.09). If delivery
   loss rises with difficulty (β > 0), Δ_R is biased *toward* "A harms more"
   by β × (0.02–0.09); if β < 0, the other way. The existing data cannot bound
   β better than ±0.6, so the bias is unbounded in principle but small in
   practice unless β is large; the follow-up in §10 would bound it.
2. **§13.15's redundancy is weaker than it reads.** The "two frozen backups"
   are drawn from Gate 2.5's qualified families in sorted order without a tier
   filter: on every Gemma replication the first backup is **CR5**, a Tier-3
   budget family structurally ineligible for the core slot; the second is
   admissible on the two v6 Gemma runs (MK1, MK2) and not on the three v7 Gemma
   runs (MK3 at ι ≈ 0.24–0.25 twice, MK1 on e4b — each fails V_stab). On the
   Qwens one backup (MK2) is admissible and the other (MK3 at ι ≈ 0.38–0.40, or
   MK5 / MK1 on the 2507 checkpoint) is not. Only r4 qwen-2507 freezes two
   admissible backups (MK1, MK2). Likewise the "≥ 5 families passing the full
   V(R)" count is implemented as Gate 2.5's qualified-family count
   (V_spec…V_inter, no V_stab or V_diff): on v7 gemma-e4b exactly three
   families pass the full V(R) while the record counts 13 qualified (10–13 on
   every replication, against 3–8 admitted for the core slot). Neither
   observation changes a verdict — the
   core sets stand on their own admissions — but "sufficiently redundant" is
   carried by Gate 2.5's count, not by admissible spares. Reported for the
   researcher; not changed here.

## 12. The six statements

| statement | supported by existing data? | basis |
|---|---|---|
| 1. Many plausible references near A | Yes on 11/12 (7–21 full-V(R) rungs from 5–8 families within ±0.10); no on v7 gemma-e4b (6 rungs, 3 Tier-1 families, zero spare) | §2 |
| 2. R1/R2/R3 tightly matched to A | Yes at calibration (≤ 0.017 on 10/12); as realised, 0.004–0.09, one-sided on 3/4 | §3 |
| 3. Δ_R is a meaningful local matched-reference contrast | Yes, with the §11 caveats | §3, §11 |
| 4. The references span enough difficulty for a reliable slope | No: realised width 0.04–0.07; even the registered spectrum, had it been drawn, ≤ 0.16 | §5, §8 |
| 5. We can estimate how D(B←R) changes with difficulty | No: 3-point slopes ±0.6–1.0; ι_A outside range on 3/4 | §8 |
| 6. A has an effect beyond what generic difficulty predicts | Not identifiable now; §10 is the smallest experiment that would identify it at development level | §9, §10 |

C4 was registered to protect statements 4–6 (§13.12's triples), not statement 3;
its failure costs the spectrum arm and nothing else under v7 A7, and this
reconstruction finds nothing in it that bears on the core arm.

## Files

- `dci1/tools/v7_reference_support_landscape.py` — the reconstruction (read-only
  over evidence; `--replot` re-renders from `landscape.json`).
- `landscape.json` — every number: per rung, per family, per basis, per composed
  cell; `REPORT.md` — generated tables; `plots/` — 29 figures listed in §6.
- Companion: `dci1/reports/dci1v7/chance_basis_impact/` (the corrected-column
  impact on the signed records).
