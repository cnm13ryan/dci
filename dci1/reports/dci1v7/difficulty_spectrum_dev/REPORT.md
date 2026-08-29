# The v7 difficulty spectrum and C4: diagnosis, and a prototype redesign of the reference ladders

**Status: DEVELOPMENT-ONLY INVESTIGATION (2026-08-29).** Read-only over the
registered v7 evidence and the development rehearsals. No v7 record, verdict,
threshold, rule, registration or freeze state was changed; no GPU generation
was run; both cards stayed with the `dci1v7-development-r4` rehearsal lanes
throughout. Produced on branch `dev/v7-difficulty-spectrum` (worktree
`/home/cnm13ryan/git/dci-v7-spectrum-dev`, based on `7f89dae`, the unmerged
§13.11 chance-basis fix) by:

| artifact | produced by |
|---|---|
| `spectrum_dev.json`, `rung_table.csv`, `family_c4_table.csv`, `plots/plotA_*`, `plots/plotB_*` | `dci1/tools/v7_spectrum_dev_analysis.py` (production kernels: `regime.calibration_coverage_rows`, `regime.coverage_criterion`, `regime.family_c4_state/family_deficiency`, `qualification_gate.qualify_candidates`; corrected κ_c via `tools/v7_chance_basis_impact.py`) |
| `counts/counts_<model>.json` | `dci1/tools/v7_spectrum_dev_counts.py` (count distributions recomputed from the stored generations with the registered counters) |
| `counts/wordings_<model>.json`, `wording_sensitivity.json`, `robust_wording_ladders.json`, `plots/plotC_*` | `dci1/tools/v7_spectrum_dev_wordings.py`, `tools/v7_spectrum_dev_wording_summary.py`, `tools/v7_spectrum_dev_plot_wordings.py` |
| prior session's landscape (input, carried from the fix worktree where it is uncommitted) | `reports/dci1v7/reference_support_landscape/` |

Every number here is exploratory. §13.7 stability, full-V(R) and the
registered-spectrum verdicts per rung are joined from the prior session's
`landscape.json`; the join was checked rung by rung for ι and eligibility
agreement (0 mismatches on 4 × 112–140 rungs), and the reconstruction
reproduces the signed Gate-3A C1–C8 verdicts on every model (asserted in the
tool). Where this report disagrees with the prior diagnostic it says so (§3.5).

---

## 0. Answers to the fourteen deliverable questions

| # | Question | Answer (detail in the section given) |
|---|---|---|
| 1 | What does A look like? | *"Use the word however exactly n times."* — exact count of one marker word (`s0_count`: lower-case, alphabetic runs equal to `however`), n ∈ 1..8, rendered through one of **four frozen wordings** chosen per row; n\* = 8 / 6 / 2 / 5 on e2b / e4b / qwen3-4b / 2507 with ι_A = 0.617 / 0.725 / 0.683 / 0.540. §1.1 |
| 2 | What do the reference constraints look like? | Tier 1 (`MK1–MK8`): A's four templates with *thus, hence, though, whereas, indeed, namely, instead, overall* substituted, q ∈ 1..8 (reserve 1..12); Tier 2 (`XC1–XC3`): exact count of semicolons / commas / sentences; Tier 3: 26 budget/rate families (class control only). §1.2 |
| 3 | How many references exist near A? | Within ±0.10 of ι_A: 26 / 17 / 15 / 18 §12.6-eligible Tier-1/2 rungs from 6 / 6 / 7 / 8 families; passing the **full** V(R): 21 / 6 / 13 / 8 rungs from 6 / 4 / 6 / 7 families. §4.1 |
| 4 | Why is local Δ_R support good? | The exact-count form is chance-free (κ = 0.000–0.007 on every marker rung), so ι = raw solo compliance with no variance amplification; eight families × 8–12 rungs put 15–26 eligible rungs inside the caliper; R1–R3 sit within 0.017 of ι_A (0.05 on e4b) and pass §13.7 on both splits. §4.1 |
| 5 | Why does C4 fail? | Not for one reason. **e2b**: ladders are flat or floored (MK2/MK4 span 0.32 over 12 rungs; MK3/6/7/8 ≤ 0.46 at every q). **e4b**: ι_A = 0.725 is high and the families that do not meet C4 are *harder than A at every severity* (MK3/6/7/8, XC1/XC3, max ι 0.51–0.68). **qwen3-4b**: the easy rungs (q = 1–2 at 0.92–0.99) are trimmed by the [0.10, 0.90] band and the middles are flat (MK1 rungs 3–7 at 0.67–0.69; MK2 misses 0.40 by 0.009). **2507**: 28 Tier-1/2 rungs sit above 0.90 and the ladders only start falling at q ≈ 6–7 while the reserve 9–12 was never measured. Underneath all four, one mechanism dominates: **2–3 of the 4 frozen wordings are parsed with the marker modifying the instruction** (§5.2), which floors whole families independently of q. §3, §5 |
| 6 | Which families are flat? | Bucket A (straddle, whole measured ladder < 0.40): e2b MK2 (0.32), MK4 (0.32); qwen3-4b MK6 (0.31). Bucket D (pre-screen ≥ 0.40, calibration < 0.40): e2b MK1 (0.50 → 0.34), 2507 MK7 (0.42 → 0.37). §3.2 |
| 7 | Which lose extreme rungs to eligibility? | Bucket C: qwen3-4b MK1 (all-measured 0.43 → eligible 0.14), MK2 (0.50 → 0.39), XC3 (0.46 → 0.34); 2507 MK1 (0.45 → 0.26), MK5 (0.51 → 0.19), MK6 (0.49 → 0.39). All by the **0.90 ceiling** on the easy side. §3.2 |
| 8 | Which pre-screen successes disappear? | Certified straddling groups 6 / 11 / 6 / 10 became 2 / 4 / 5 / 4. Per family the 24×1 pre-screen span exceeded the 192×4 span on e2b MK1 (0.50 vs 0.34), MK8 (0.44 vs 0.24), XC1 (0.47 vs 0.44); e4b MK6 (0.46 vs 0.38), MK8 (0.46 vs 0.31); 2507 MK5 (0.63 vs 0.19 eligible), MK7 (0.42 vs 0.37); and ι_A itself moved −0.05 / +0.06 / −0.03 / **−0.13**. Tier-3 padding (groups like `letter_a`, `vowel_initial`, `comma`, `capital`, `y_final` certified at the screen) never reaches calibration in C4-usable form. §3.3 |
| 9 | Where is coverage missing? | Above A. Beyond ι_A + 0.10 the eligible Tier-1/2 rungs number 11 / 6 / 9 / 17 and beyond +0.20 they number **2 / 0 / 0 / 11**; V_head's Wilson-upper ≤ 0.90 caps admissible p_solo at 0.8575, so for ι_A ≥ 0.68 (e4b, qwen3-4b) the whole reachable region above A is 0.13–0.17 wide. Below A coverage is dense on all four (bins −0.1…−0.5: 57 / 69 / 41 / 22 rungs). §4.2 |
| 10 | Most promising new ladders? | **F1** the same eight marker families under the two *robust* frames (w0 "Use the word X exactly q times." / w3 "The word X must appear exactly q times.") with the full 1..12 ladder measured: on the stored rows this alone makes 5 / 7 / 5 / 3 Tier-1 families straddle with span ≥ 0.40 (vs 2 / 4 / 5 / 4 groups today) and the ladders monotone (Spearman −0.9 to −1.0). **F2** the ladder extended to q = 16 for the easy markers on the 2507 checkpoint. **F3** the three registered reserve markers (*albeit, notably, besides*) and the unregistered admissible *rather, further, still, yet, then* under the robust frames. **F4** a marker count lower bound ("at least q times") as a smooth, overshoot-free production ladder (a new form; comparability cost stated). §6 |
| 11 | Cheapest screening? | Solo-only, robust-frame ladders on 48 topics × 2 draws per rung, 12–16 rungs × 10–12 families plus the unconstrained cell: ≈ 12–20k generations per model ≈ 15–25 min on a Qwen lane, 45–70 min on a Gemma lane at the measured shared-card rates; existing w0/w3 rows already give half of MK1–MK8's rungs at calibration precision for free. §7 |
| 12 | The later B+R spectrum experiment? | Per model 6–9 companions (2–3 per core family, below/near/above, ≥ 2 families per side), each B+X and X+B on the frozen 384 blocks × 8 draws plus solo:X (≈ 9.2k gens/companion), fit §11.8's α_f + β d with family intercepts, §17.2 block bootstrap plus a family jackknife; ≈ 55–83k generations per model, ≈ 0.3–0.5 of one v7 replication. §8, §9 |
| 13 | Without changing/fixing/freezing v7? | Yes for everything in this report (diagnosis, screening design, development-namespace spectrum runs). Adopting F1–F4 confirmatorily is a wording-allocation / ladder / population change to §7.8, §7.10, §8.4 and §12.6 — a superseding registration (v8), not a v7 amendment, because §32.3 freezes §13 and A's wordings are carried byte-identically. §6.5, §9 |
| 14 | Untouched? | Verified before and after: registered v7 records, durable root, dev roots r1–r3 byte-identical; r4 changed only by its own running lanes; no process signalled; GPUs 0/1 never used; main and fix worktrees unchanged. `SAFETY_AND_ISOLATION.md` |

---

## 1. Phase 1 — the v7 design as it actually is

### 1.1 A and B

| | A (target, production) | B (focal, budget) |
|---|---|---|
| rule | the answer uses the word *however* exactly n times | every word has at most m letters (longest alphabetic run ≤ m) |
| grid | n ∈ {1,…,8} | m ∈ {7,…,14}, extension {15, 16} |
| wordings (frozen, one drawn per row, §8.4) | w0 `Use the word however exactly n times.` · w1 `Your answer must contain however exactly n times.` · w2 `Include however exactly n times in your answer.` · w3 `The word however must appear exactly n times.` | `Every word in the answer must have at most m letters.` · `Use only words of m letters or fewer.` · `Do not use any word longer than m letters.` · `No word in your answer may exceed m letters.` |
| verifier | `dci1v4.verifiers.target.s0_count`: lower-case the text, take maximal alphabetic runs, count runs equal to `however` (so *However,* counts; *howeverso* does not) | longest alphabetic run ≤ m |
| chance | κ_A = P(exactly n *however* in an unconstrained answer): 0.000 at every n except n = 1 (0.026–0.089 natural P(≥ 1)) | κ^B(m) up to 0.50 (construct floor, §34 D17) |

Prompt (§8.5): `<topic question>\n\nAnswer in 60 to 120 words.\n\n1. <constraint>\n\nAnswer:`; composed cells list two numbered constraints; the unconstrained cell has no list.

Registered operating points (Gate 2, 192 calibration topics × 4 draws):

| model | n\* | m\* | p_solo(A) | ι_A (κ_A basis: all A-absent grid rows) | ι_A on the unconstrained cell alone | ι_A pre-screen (24 × 1) |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 8 | 10 | 0.621 | 0.6166 | 0.6211 | 0.663 |
| gemma-3n-e4b-it | 6 | 9 | 0.732 | 0.7252 | 0.7318 | 0.666 |
| qwen3-4b | 2 | 12 | 0.685 | 0.6827 | 0.6849 | 0.708 |
| qwen3-4b-instruct-2507 | 5 | 11 | 0.565 | 0.5399 | 0.5651 | 0.666 |

### 1.2 The reference families

The library is a grammar (§7.3): a counted statistic under a predicate form. What the spectrum can use:

| tier | families | form / template (index 0) | statistic | ladder (reserve) |
|---|---|---|---|---|
| 1 | MK1 thus · MK2 hence · MK3 though · MK4 whereas · MK5 indeed · MK6 namely · MK7 instead · MK8 overall | **A's four templates with the marker substituted** (`protocol/wordings._marker_templates`): `Use the word thus exactly q times.` … | `marker_count(text, word)` — same procedure as A | 1..8 (1..12) |
| 2 | XC1 semicolon · XC2 comma · XC3 sentence | `Your answer must use exactly q semicolons.` / `…commas.` / `Your answer must have exactly q sentences.` | `text.count(";")`, `text.count(",")`, `sentence_units` | 1..8 / 2,4,…,16 / 3..10 (reserves to 10 / 20 / 14) |
| 3 | RF1–RF12, CR1–CR12, CL7, CL8 | count budgets (`At most q words may begin with b.`), rate budgets (`Words beginning with b: at most q percent.`), two count lower bounds | 14 carried numerators | various; at most 24 rungs carried to calibration (§12.7) |

Slots: core R1–R3 (Tier 1/2, ≥ 2 Tier 1, three feature groups, §13.8: |ι_R − ι_A| ≤ 0.10, Newcombe region, |p_solo(R) − p_solo(A)| ≤ 0.15); spectrum R_{f,±} drawn from each core family's *own* ladder nearest ι_A ∓ 0.20 on strictly opposite sides (§13.12); near-form N1–N3 (Tier 2); class CL (Tier-3 budget); two frozen backups (§13.15).

### 1.3 The coordinate and the corrected chance definition

ι_c = (p_solo − κ_c)/(1 − κ_c), κ_c the constraint's pass rate on the **unconstrained** cell of the same topics (§13.2). On every v5/v6/v7 replication the recorded calibration table wrote κ_c = 0.0 (finding of 2026-08-29, fixed on `fix/v7-chance-basis` = `7f89dae`, not merged). This report uses the corrected κ_c throughout: for every marker rung it is 0.000–0.007, so ι = p_solo for the whole Tier-1 pool and the correction moves nothing in Phases 2–4 for the families that matter (it matters for Tier-3 rungs, whose κ reaches 0.98; `chance_basis_impact/REPORT.md`).

### 1.4 Eligibility and C1–C8, exactly as registered

Eligibility (§12.6, U4 = E2): raw **point** solo compliance in [0.10, 0.90] and solo vacuity ≤ 0.10; a rung with κ ≥ 0.99 has no coordinate and is dropped (v6 A16). V_head for *admission* is stricter: the 95 % Wilson interval inside [0.10, 0.90], which at n = 192 admits p_solo ≤ **0.8575**.

| | condition (evaluated on the calibrated basis at Gate 2's ι_A; v6 A3, v7 A7) | arm |
|---|---|---|
| C1 | an eligible rung strictly below and one strictly above ι_A | core |
| C2 | ≥ 3 eligible Tier-1/2 feature groups on each side | spectrum |
| C3 | ≥ 8 eligible rungs within 0.15 of ι_A from ≥ 4 groups | core |
| **C4** | **≥ 6 feature groups contain a family that straddles ι_A with ≥ 3 eligible rungs spanning ≥ 0.40 in ι** | **spectrum** |
| C5 | ≥ 16 eligible rungs | core |
| C6 | ≥ 8 eligible Tier-1/2 families from ≥ 6 groups | core |
| C7 / C8 | Tier-3 budget rung within 0.15 / three Tier-2 rungs from three groups | class / near-form |

`regime.coverage_criterion` evaluates C4 per family as: has_below ∧ has_above (first deficiency `MISSING_SIDE`), n_eligible ≥ 3 (`TOO_FEW_RUNGS`), max ι − min ι over the family's eligible rungs ≥ 0.40 (`SPAN_SHORT`); a group counts once. Under v7 A7 a lost C2/C4 with the core conditions met is `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and costs the spectrum arm only.

### 1.5 The evidence read

Registered v7 (manifest `969a5b9f…`, closed 2026-08-28): four replications through Gate 4, 141k–142k behavioural rows each; Gate 2 carries 112–140 calibrated candidates per model on 192 topics × 4 draws (solo cells) plus 1,536 unconstrained rows per model (grid-A/B). Development rehearsals: `dci1v7-development` (qwen3-4b, complete), `-r3` (qwen3-4b, gemma-e2b complete), `-r4` (2507 in `CONFIRMATORY_GENERATION` on GPU 1 and gemma-e4b in `GATE_2_FOCAL_CALIBRATION` on GPU 0 at the time of writing — untouched). Phases 2–5 use the registered trees only; the prior session's landscape covers the rehearsals and agrees where they overlap.

---

## 2. Phase 2 — every reference ladder, reconstructed

`rung_table.csv` (476 rows) carries, per rung: model, family, tier, feature group, form, severity, solo, κ (corrected), ι, lift, vacuity, κ(R|B), median words, eligibility and its reason, side of ι_A and signed distance, Gate-2.5 qualification and first failing component, §13.7 stability, full V(R) and its first failing component, registered/unfolded spectrum eligibility, the signed slot, whether the family is a frozen backup, whether the rung entered by §12.6's expansion, and the pre-screen solo/κ/ι/vacuity.

Plots per model (`plots/`):

- **Plot A** `plotA_landscape_<model>.png` — every rung on the corrected ι axis by family (Tier 1 blue, Tier 2 green, Tier 3 grey, severity labelled): filled = eligible and full V(R), faded = eligible only, hollow = ineligible; ι_A (black), the §13.8 caliper (gold), the §13.12 targets ι_A ± 0.20 (purple dotted), the V_head ceiling 0.8575 and the 0.10 floor (red dashed); signed slots starred (R1–R3, R±, CL), frozen backups labelled.
- **Plot B** `plotB_ladders_<model>.png` — severity → ι per family with ι_A, the caliper and the band; expansion rungs boxed; title = eligible span, below/above counts, C4's first deficiency and the Phase-3 bucket.
- **Plot C** `plotC_wordings_<model>.png` — P(S = q) by wording index (Phase 5).

What the plots show at a glance: a dense column of eligible, admitted Tier-1 rungs inside the caliper on every model; to its left a long tail of harder rungs; to its right almost nothing that is both eligible and far from A. On e2b and e4b the reserve rungs 9–12 of MK2/MK4/MK5/MK7 (boxed) extend the ladders *downward* as §12.6 intended, but only MK5 (e2b) and MK1/MK2/MK4/MK5 (e4b) reach 0.40.

---

## 3. Phase 3 — C4 diagnosed family by family

### 3.1 The registered criterion on the calibrated basis (reproduces the signed records)

| model | ι_A | eligible rungs (Tier 1/2) | below / above | straddling Tier-1/2 families | C4 groups (need 6) | C1 C2 C3 C5 C6 |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.617 | 100 (80) | 69 / 31 | MK1 MK2 MK4 MK5 XC3 | **2** (marker_indeed, sentence) | all met |
| gemma-3n-e4b-it | 0.725 | 104 (85) | 87 / 17 | MK1 MK2 MK4 MK5 | **4** (thus, hence, whereas, indeed) | all met |
| qwen3-4b | 0.683 | 81 (69) | 60 / 21 | MK1–MK7, XC1, XC3 | **5** (though, whereas, indeed, instead, semicolon) | all met |
| qwen3-4b-instruct-2507 | 0.540 | 65 (49) | 32 / 33 | MK1 MK3–MK8 XC1 | **4** (though, whereas, overall, semicolon) | all met |

### 3.2 Every Tier-1/2 family, with its first deficiency and bucket

Span = max − min ι over the family's **eligible** rungs; "all" = over every measured rung; "pre" = the 24 × 1 pre-screen on the same rungs at the pre-screen ι_A. Buckets: **A** flat ladder · **B** missing one side · **C** eligibility cutoff · **D** pre-screen noise · **E** other · MET.

**gemma-3n-e2b-it (ι_A 0.617)** — the expansion ran one round (MK2/MK4/MK5/MK7 got 9–12)

| family | n meas / elig | eligible ι range | span | below/above | first deficiency | all-measured span | pre span | bucket |
|---|---|---|---|---|---|---|---|---|
| MK1 thus | 8 / 8 | 0.378–0.717 | 0.340 | 5 / 3 | SPAN_SHORT | 0.340 | 0.501 | **D** — certified at the screen (so not expanded), 0.34 at calibration |
| MK2 hence | 12 / 12 | 0.454–0.772 | 0.318 | 7 / 5 | SPAN_SHORT | 0.318 | 0.376 | **A** — flat even with q = 12 (ι 0.45–0.49 at q = 11–12) |
| MK3 though | 8 / 8 | 0.180–0.242 | 0.062 | 8 / 0 | MISSING_SIDE | 0.062 | 0.085 | **B** — floored at 0.2 at every q |
| MK4 whereas | 12 / 12 | 0.414–0.730 | 0.316 | 6 / 6 | SPAN_SHORT | 0.316 | 0.379 | **A** |
| MK5 indeed | 12 / 11 | 0.395–0.896 | 0.501 | 5 / 6 | — | 0.546 | 0.504 | MET (after expansion) |
| MK6 namely | 8 / 7 | 0.229–0.306 | 0.077 | 7 / 0 | MISSING_SIDE | 0.264 | 0.167 | **B** — floored |
| MK7 instead | 12 / 0 | — | 0 | 0 / 0 | MISSING_SIDE | 0.052 | 0 | **B** — no eligible rung, ι ≤ 0.07 at every q |
| MK8 overall | 8 / 8 | 0.229–0.464 | 0.235 | 8 / 0 | MISSING_SIDE | 0.235 | 0.444 | **B** (pre-screen 0.44 was noise) |
| XC1 semicolon | 8 / 6 | 0.102–0.541 | 0.439 | 6 / 0 | MISSING_SIDE | 0.489 | 0.474 | **B** — harder than A at q = 1 already |
| XC2 comma | 12 / 0 | — | 0 | — | MISSING_SIDE | 0.188 | 0 | **B** — ι ≈ 0 (the model writes 7–9 extra commas) |
| XC3 sentence | 8 / 8 | 0.205–0.664 | 0.459 | 6 / 2 | — | 0.459 | 0.481 | MET (inverted ladder: more sentences is easier) |

> **e2b: C4 fails mainly because the exact-count ladders are flat or floored — severity barely moves difficulty on this model** (A's own ladder is flat too: p_solo 0.43–0.62 across n = 1..8). Two of the three extended families (MK2, MK4) stay inside 0.32 over twelve rungs; four marker families never rise above 0.46.

**gemma-3n-e4b-it (ι_A 0.725)** — expansion ran one round

| family | n meas / elig | eligible ι range | span | below/above | first deficiency | all span | pre span | bucket |
|---|---|---|---|---|---|---|---|---|
| MK1 thus | 12 / 10 | 0.406–0.880 | 0.474 | 7 / 3 | — | 0.521 | 0.502 | MET |
| MK2 hence | 12 / 10 | 0.417–0.896 | 0.479 | 7 / 3 | — | 0.503 | 0.586 | MET |
| MK3 though | 8 / 8 | 0.224–0.508 | 0.284 | 8 / 0 | MISSING_SIDE | 0.284 | 0.359 | **B** |
| MK4 whereas | 12 / 9 | 0.314–0.897 | 0.583 | 5 / 4 | — | 0.668 | 0.627 | MET |
| MK5 indeed | 12 / 8 | 0.370–0.857 | 0.487 | 7 / 1 | — | 0.594 | 0.461 | MET |
| MK6 namely | 12 / 12 | 0.292–0.676 | 0.384 | 12 / 0 | MISSING_SIDE | 0.384 | 0.459 | **B** — max 0.676 < 0.725 even at q = 1 |
| MK7 instead | 8 / 0 | — | 0 | — | MISSING_SIDE | 0.051 | 0 | **B** |
| MK8 overall | 8 / 8 | 0.257–0.565 | 0.309 | 8 / 0 | MISSING_SIDE | 0.309 | 0.457 | **B** |
| XC1 semicolon | 8 / 8 | 0.210–0.511 | 0.301 | 8 / 0 | MISSING_SIDE | 0.301 | 0.363 | **B** |
| XC2 comma | 12 / 0 | — | 0 | — | MISSING_SIDE | 0.220 | 0 | **B** |
| XC3 sentence | 12 / 12 | −0.063–0.636 | 0.699 | 12 / 0 | MISSING_SIDE | 0.699 | 0.397 | **B** — wide but entirely below A |

> **e4b: C4 fails mainly because ι_A is high (0.725) and every family that is not already a C4 group is harder than A at every severity** — its easy end never reaches 0.73. The four families that do straddle only do so because the expansion measured q = 9–12.

**qwen3-4b (ι_A 0.683)** — no expansion (the pre-screen certified six groups)

| family | n meas / elig | eligible ι range | span | below/above | first deficiency | all span | pre span | bucket |
|---|---|---|---|---|---|---|---|---|
| MK1 thus | 8 / 6 | 0.552–0.693 | 0.141 | 4 / 2 | SPAN_SHORT | 0.434 | 0.209 | **C** — q = 1, 2 at 0.99 / 0.92 trimmed; q = 3–7 flat at 0.67–0.69 |
| MK2 hence | 8 / 7 | 0.469–0.859 | 0.391 | 6 / 1 | SPAN_SHORT | 0.504 | 0.375 | **C** — q = 1 (0.97) trimmed; misses 0.40 by 0.009 |
| MK3 though | 8 / 7 | 0.113–0.865 | 0.752 | 6 / 1 | — | 0.770 | 0.749 | MET |
| MK4 whereas | 8 / 7 | 0.173–0.863 | 0.690 | 6 / 1 | — | 0.822 | 0.710 | MET |
| MK5 indeed | 8 / 8 | 0.193–0.831 | 0.638 | 6 / 2 | — | 0.638 | 0.751 | MET |
| MK6 namely | 8 / 6 | 0.664–0.866 | 0.202 | 2 / 4 | SPAN_SHORT | 0.312 | 0.292 | **A** — shallow: 0.98 → 0.67 over q = 1..8 |
| MK7 instead | 8 / 8 | 0.223–0.802 | 0.579 | 7 / 1 | — | 0.579 | 0.542 | MET |
| MK8 overall | 8 / 8 | 0.118–0.468 | 0.350 | 8 / 0 | MISSING_SIDE | 0.350 | 0.417 | **B** |
| XC1 semicolon | 8 / 7 | 0.164–0.768 | 0.604 | 6 / 1 | — | 0.759 | 0.710 | MET |
| XC2 comma | 8 / 1 | 0.053 | 0 | 1 / 0 | MISSING_SIDE | 0.158 | 0 | **B** |
| XC3 sentence | 8 / 4 | 0.507–0.847 | 0.341 | 2 / 2 | SPAN_SHORT | 0.456 | 0.456 | **C** — q = 3–6 at 0.90–0.96 trimmed |

> **qwen3-4b: C4 fails mainly because the eligibility band trims the easy end of otherwise-straddling ladders and their middles are flat**; one group short, and MK2 misses by 0.009 (one standard error).

**qwen3-4b-instruct-2507 (ι_A 0.540)** — no expansion (the pre-screen certified ten groups at a pre-screen ι_A of 0.666)

| family | n meas / elig | eligible ι range | span | below/above | first deficiency | all span | pre span | bucket |
|---|---|---|---|---|---|---|---|---|
| MK1 thus | 8 / 3 | 0.533–0.797 | 0.264 | 1 / 2 | SPAN_SHORT | 0.449 | 0.042 | **C** — q ≤ 5 at 0.90–0.98 trimmed |
| MK2 hence | 8 / 3 | 0.560–0.842 | 0.283 | 0 / 3 | MISSING_SIDE | 0.432 | 0 | **B** — easier than A at every q ≤ 8; q ≥ 9 never measured |
| MK3 though | 8 / 6 | 0.118–0.878 | 0.759 | 4 / 2 | — | 0.837 | 0.709 | MET |
| MK4 whereas | 8 / 6 | 0.273–0.885 | 0.612 | 3 / 3 | — | 0.706 | 0.668 | MET |
| MK5 indeed | 8 / 4 | 0.474–0.663 | 0.189 | 1 / 3 | SPAN_SHORT | 0.505 | 0.625 | **C** |
| MK6 namely | 8 / 4 | 0.507–0.895 | 0.388 | 1 / 3 | SPAN_SHORT | 0.492 | 0.501 | **C** — misses by 0.012 |
| MK7 instead | 8 / 8 | 0.471–0.844 | 0.372 | 2 / 6 | SPAN_SHORT | 0.372 | 0.417 | **D** |
| MK8 overall | 8 / 8 | 0.219–0.798 | 0.579 | 5 / 3 | — | 0.579 | 0.625 | MET |
| XC1 semicolon | 8 / 6 | 0.168–0.726 | 0.558 | 5 / 1 | — | 0.663 | 0.701 | MET |
| XC2 comma | 8 / 0 | — | 0 | — | MISSING_SIDE | 0.150 | 0.046 | **B** |
| XC3 sentence | 8 / 1 | 0.842 | 0 | 0 / 1 | MISSING_SIDE | 0.156 | 0 | **B** — p_solo = 1.00 at every q ≤ 10 |

> **2507: C4 fails mainly because the registered ladder 1..8 is too easy for this checkpoint** — 28 Tier-1/2 rungs sit above 0.90, the ladders start to fall only at q = 6–7, and the reserve that would have supplied the hard side was never generated because a noisy pre-screen (ι_A_pre 0.666 vs calibrated 0.540) certified C4 with ten groups.

Tier-3 families (bucket E everywhere): §12.7 carries at most 24 Tier-3 rungs, the nearest to the pre-screen ι_A, so a Tier-3 family arrives at calibration with 1–5 rungs clustered near A (or, for the rate budgets, with κ_c up to 0.98 and a coordinate near 0 or undefined); 16 / 15 / 12 / 11 of them are one-sided, none spans 0.40 with three eligible rungs. The groups they contributed to the pre-screen certificate (`letter_a`, `vowel_initial`, `comma`, `capital`, `y_final`, `s_final`, `t_initial`) are why the certificate reads 6–11.

### 3.3 Pre-screen noise, quantified on the same rungs

Per family the 24 × 1 pre-screen span minus the 192 × 4 span over the same measured rungs (Tier 1/2, positive = inflated): e2b MK1 +0.16, MK8 +0.21, MK6 −0.10; e4b MK2 +0.08, MK6 +0.08, MK8 +0.15, XC3 −0.30; qwen3-4b MK5 +0.11, MK1 −0.22; 2507 MK5 +0.12, MK7 +0.05, MK1 −0.41. The sign is not systematic — the pre-screen is simply noisy (SE ≈ 0.10 per rung) — but its **certificate** also includes rungs and families that never reach calibration in C4-usable form, and the reference point moved by up to 0.13. Bucket D (a family whose own rungs looked wide and are not) applies to e2b MK1 and 2507 MK7 only; the larger effect of the pre-screen is that its false certificate **stopped the expansion** on both Qwens, so the reserve 9–12 — the only rungs that could carry MK1/MK2/MK5/MK6 past 0.40 on the hard side — was never measured there.

### 3.4 Summary per model

| model | C4 fails mainly because | secondary |
|---|---|---|
| gemma-3n-e2b-it | the exact-count form is **flat in q** on this model (A's own ladder included) and four markers are **floored** below 0.5 at every q | MK1 not expanded (false certificate) |
| gemma-3n-e4b-it | **ι_A = 0.725 sits above the easy end** of every family that is not already a group; six families are harder than A at q = 1 | the 0.8575 ceiling leaves 0.13 of room above A |
| qwen3-4b | **the 0.90 band trims the easy rungs** and the middles are flat (constant ≈ 30 % overshoot) | reserve unmeasured; MK2 short by 0.009 |
| qwen3-4b-instruct-2507 | **the ladder 1..8 is too easy** for this checkpoint (28 rungs > 0.90) and the hard side was never generated | ι_A moved −0.13 from the screen |

### 3.5 Where this differs from the prior diagnostic

`reference_support_landscape/FINDINGS.md` states that "§12.6's expansion never ran on any replication (`expansion.rounds` is empty on all twelve)". On the registered v7 trees that is **false for both Gemmas**: `REGIME_SCREEN/regime_record.json` carries one round (`expansion-0`, 1,896 and 2,352 rows) admitting MK2/MK4/MK5/MK7 (e2b) and MK1/MK2/MK4/MK5/MK6 (e4b) at q = 9–12 plus Tier-3 reserve rungs, and those rungs were calibrated (Gate 2 tables carry 12 rungs for those families; `MK4:9` is e2b's signed R1−). It is true for both Qwens. The prior diagnostic's mechanism ranking (folded V_diff ≫ ceiling ≫ span floor) and its local-support numbers are confirmed here.

---

## 4. Phase 4 — local support versus spectrum support

These are different requirements: Δ_R needs several *matched* companions inside a ±0.10 caliper; the difficulty-response fit needs companions *spread* over ≥ 0.40 with both sides of A populated, from more than one family.

### 4.1 Local support (for Δ_R) — good on three models, thin on gemma-e4b

| model | eligible rungs within ±0.05 / ±0.10 / ±0.15 (families) | of which Tier 1/2 within ±0.10 (families) | passing full V(R) within ±0.10 (families) | R1 / R2 / R3 and distance |
|---|---|---|---|---|
| e2b | 18 (8) / 33 (10) / 47 (12) | 26 (6) | 21 (6) | MK4:8 −0.002 · MK1:1 +0.002 · XC3:10 −0.017 |
| e4b | 15 (8) / 29 (11) / 35 (11) | 17 (6) | **6 (4)** | MK5:6 −0.031 · MK4:7 +0.031 · MK6:3 −0.049 |
| qwen3-4b | 11 (6) / 18 (10) / 26 (10) | 15 (7) | 13 (6) | MK1:6 +0.003 · MK6:8 −0.011 · MK7:2 −0.012 |
| 2507 | 10 (9) / 23 (11) / 30 (13) | 18 (8) | 8 (7) | MK1:7 −0.007 · MK3:3 +0.012 · MK4:5 +0.017 |

> Yes — there are plenty of good references close to A on e2b, qwen3-4b and 2507 (6–21 rungs passing every admission rule, from 6–7 families), and just enough on e4b (six rungs from three Tier-1 families plus one Tier-3, zero spare). The reason is structural: the exact-count form is chance-free, so ι equals raw compliance without the 1/(1 − κ) amplification, and eight same-form families at 8–12 severities each lay 15–26 eligible rungs into the caliper.

### 4.2 Spectrum support (for D(B←R) vs ι(R)) — insufficient on all four, and *where*

| model | eligible Tier-1/2 ι range | rungs by bin of ι − ι_A: −0.5…−0.4 / −0.4…−0.3 / −0.3…−0.2 / −0.2…−0.1 / −0.1…0 / 0…+0.1 / +0.1…+0.2 / +0.2…+0.3 / +0.3…+0.4 | families straddling | families meeting C4 | ι_A + 0.20 reachable under V_head? |
|---|---|---|---|---|---|
| e2b (0.617) | 0.102–0.896 | 9 / 18 / 7 / 8 / 15 / 11 / 9 / 2 / 0 | 5 | 2 | yes (0.817 < 0.858) |
| e4b (0.725) | −0.063–0.897 | 15 / 14 / 15 / 13 / 12 / 5 / 6 / 0 / 0 | 4 | 4 | **no** (0.925) |
| qwen3-4b (0.683) | 0.053–0.866 | 9 / 6 / 11 / 6 / 9 / 6 / 9 / 0 / 0 | 9 | 5 | **no** (0.883) |
| 2507 (0.540) | 0.118–0.895 | 1 / 5 / 6 / 2 / 8 / 10 / 6 / 5 / 6 | 8 | 4 | yes (0.740) |

Coverage is missing **above A**: beyond +0.20 there are 2 / 0 / 0 / 11 eligible Tier-1/2 rungs, and for ι_A ≥ 0.68 the admissible ceiling 0.8575 leaves 0.13–0.17 of room, so an upper spectrum rung at ι_A + 0.20 does not exist and cannot be authored. Below A coverage is dense everywhere (41–69 rungs below −0.10). The registered spectrum pool (V_diff folded into V_stab, §13.7) spans only 0.10–0.15 on every model (e.g. qwen3-4b 13 rungs in [0.620, 0.767]); with V_diff unfolded the same tables hold rungs from ≈ 0.22 to 0.77–0.82.

> No — we do not have enough reliable references spread across easy-to-hard difficulty. The pool is one-sided (easy rungs trimmed or nonexistent) and the registered selection rule confines the spectrum to the caliper anyway.

---

## 5. Phase 5 — what the constraints look like to the model, and why q barely moves difficulty

### 5.1 The forms

A and every Tier-1 family are the same instrument: *exact count of one word*, four frozen frames, the marker substituted. Tier 2 is exact count of a punctuation character or of sentences. Tier 3 is `S ≤ q` / `100 S/W ≤ q` budgets. The exact-count form can fail in exactly three ways — the word is produced fewer times than q (undershoot), more times (overshoot), or the instruction is not taken up at all (S = 0) — and the stored generations separate them (`counts/counts_<model>.json`, P(S = q) | P(S < q) | P(S > q) | mean S − q per rung):

| mechanism | where it is measured | what it does to the ladder |
|---|---|---|
| **zero production (S = 0 at any q)** | e2b: *instead* 0.90–0.96 at every q, *namely* 0.96 at q = 1, *though* 0.78, *overall* 0.70; e4b: *instead* 0.91–0.94, *though* 0.48–0.71; both Qwens: *overall* 0.47–0.48 at q = 1; qwen3-4b: *however* 0.06–0.20 | a q-independent floor — the family is flat and below A (buckets A/B on the Gemmas) |
| **overshoot** | qwen3-4b: *though* P(S > q) 0.78–0.82 at q ≥ 3 (mean S − q up to +4.2), *whereas* 0.78–0.81 (+1.8…+3.2), *thus* ≈ 0.30 at q = 3–7 (+0.3…+0.6); 2507: *though* 0.68–0.89 (+1.3…+8.9), *whereas* 0.56–0.66 | a cliff between q = 1 and q = 3 then a flat floor at 0.1–0.2 (*though*, *whereas*); a flat middle (*thus*: 0.67–0.69 from q = 3 to 7) |
| **slow count-control decay** | e4b: *thus/hence/whereas/indeed* 0.93–0.98 at q = 1 → 0.31–0.42 at q = 12 (≈ 0.05 per rung, overshoot rising to 0.3–0.45 at q ≥ 9); 2507: *thus/hence/namely/indeed* ≥ 0.90 until q = 5–6 then ≈ 0.1 per rung | the genuine ladder — but it needs q up to 12 (and beyond 8 on 2507), and its easy half sits above 0.90 |
| **answer-length compensation** | Gemmas: median words 105–111 at q = 1 → 131–155 at q = 8–12 (the stem asks 60–120); Qwens: 65–96, flat | on the Gemmas high q is bought by leaving the length band, which is what §13.6's B-interaction later punishes |
| **easy-end trimming** | Tier-1/2 rungs with p_solo > 0.90: 1 / 11 / 11 / 28 | removes the rungs that made the ladder straddle (bucket C) |
| **hard end unmeasured** | reserve 9–12 not generated on either Qwen | the side that could have supplied the span never existed |

### 5.2 The wording-parse artefact (new; Plot C)

§8.4 draws one of the four frozen wordings per row. Splitting the solo cells by the wording that was drawn (192 topics × 1 draw per wording per rung; `counts/wordings_<model>.json`, `wording_sensitivity.json`) shows that **2–3 of the 4 frames are read, for particular markers, with the marker modifying the instruction rather than naming the word**. Mean over the ladder of P(S = q), with mean P(S = 0) in brackets:

| model | family | w0 `Use the word X exactly q times.` | w1 `Your answer must contain X exactly q times.` | w2 `Include X exactly q times in your answer.` | w3 `The word X must appear exactly q times.` |
|---|---|---|---|---|---|
| e2b | **A (however)** | 0.59 [0.02] | **0.36 [0.42]** | 0.53 [0.04] | 0.62 [0.06] |
| e2b | MK3 though | 0.38 [0.07] | **0.01 [0.98]** | **0.03 [0.95]** | 0.41 [0.09] |
| e2b | MK6 namely | **0.13 [0.69]** | **0.04 [0.94]** | **0.14 [0.81]** | 0.67 [0.14] |
| e2b | MK8 overall | 0.55 [0.04] | **0.25 [0.52]** | **0.09 [0.79]** | 0.44 [0.08] |
| e2b | MK7 instead | 0.01 [0.93] | 0.03 [0.89] | 0.01 [0.95] | 0.18 [0.60] |
| e4b | MK6 namely | **0.02 [0.82]** | 0.59 [0.21] | 0.68 [0.10] | 0.74 [0.00] |
| e4b | MK3 though | 0.46 [0.02] | **0.16 [0.73]** | **0.23 [0.62]** | 0.44 [0.07] |
| e4b | MK8 overall | 0.63 [0.02] | **0.32 [0.49]** | **0.17 [0.65]** | 0.55 [0.03] |
| qwen3-4b | **A (however)** | 0.66 [0.00] | **0.40 [0.36]** | 0.41 [0.00] | 0.74 [0.00] |
| qwen3-4b | MK8 overall | 0.46 [0.01] | **0.04 [0.86]** | **0.28 [0.50]** | 0.25 [0.09] |
| qwen3-4b | MK5 indeed | 0.53 [0.00] | **0.40 [0.53]** | 0.59 [0.02] | 0.29 [0.20] |
| 2507 | MK8 overall | 0.80 [0.00] | **0.28 [0.59]** | **0.24 [0.70]** | 0.64 [0.01] |
| 2507 | MK7 instead | 0.71 [0.00] | 0.74 [0.00] | **0.46 [0.37]** | 0.80 [0.00] |

The raw generations confirm the parse rather than a counting failure: under *"Use the word namely exactly 3 times."* gemma-e2b writes **Exactly** in bold three times (it read "namely" as introducing the word to use); under *"Include though exactly 3 times in your answer."* it bolds three arbitrary words; under *"Your answer must contain however exactly 1 time."* it writes a normal answer with no *however*. *instead* is the one marker that fails under every frame on both Gemmas (P(S = 0) ≥ 0.60 even for w3) — a genuine word-specific floor, not a parse.

Three consequences:

1. **It is what floors the Gemma families.** Restricting each family to its robust frames (mean P(S = 0) ≤ 0.15; `robust_wording_ladders.json`) the ladders become monotone (Spearman(q, ι) −0.90 to −1.00 for MK1/MK4/MK5/MK6/MK8 on e2b, seven of eight families on e4b) and the number of Tier-1 families that straddle ι_A with ≥ 3 eligible rungs and span ≥ 0.40 becomes **5 (e2b), 7 (e4b), 5 (qwen3-4b), 3 (2507)** against 2 / 4 / 5 / 4 groups on the registered basis (2507's shortfall is the unmeasured hard side, §3.4). e2b MK6 *namely* under w3 alone runs 0.80 → 0.69 over q = 2..8 where the all-wording ladder reads 0.23 → 0.27.
2. **It sits inside A itself.** On e2b and qwen3-4b wording w1 of A produces no *however* in 36–42 % of rows; A's operating point n\* and ι_A were selected on the four-wording mixture, so part of "A's difficulty" on those models is prose-level uptake, not counting.
3. **It is not a verifier or a counting problem, and it is not random noise**: the failing frames are the ones where the marker sits between the verb and *exactly* (`contain X exactly`, `Include X exactly`, and `Use the word X` for *namely*), and the robust frame everywhere is w3, where *The word* precedes the marker.

### 5.3 Why changing nominal severity fails to move difficulty — per model

- **gemma-3n-e2b-it**: the uptake floor (§5.2) plus a flat exact-hit rate: for *hence* and *whereas* P(S = q) sits at 0.6–0.7 from q = 2 to 10 with a constant ≈ 30 % undershoot — the model drops one occurrence whatever q is — and only at q = 11–12 does overshoot begin to bite. The same is true of A (p_solo 0.43–0.62 over n = 1..8). Severity is not a difficulty knob on this model until q ≥ 11.
- **gemma-3n-e4b-it**: severity *does* move difficulty for the robust families (0.95 → 0.4 over 1..12, ≈ 0.05 per rung, overshoot growing at high q), but A is at 0.725 and the parse-floored families cannot reach it.
- **qwen3-4b**: two regimes — *though* / *whereas* collapse by q = 3 through overshoot (the model writes the word 2–4 times more than asked) and then sit at 0.1–0.2; *thus* / *hence* / *namely* are flat in the middle because a constant ≈ 30 % of rows overshoot by one regardless of q. The informative region of each ladder is 2–3 rungs wide.
- **qwen3-4b-instruct-2507**: the best counter of the four (P(S = q) ≥ 0.90 up to q = 5 for six markers, overshoot small) — the ladder simply starts too low: difficulty appears only from q ≈ 6, and the registered ladder ends at 8.

Answer-length compensation is real on the Gemmas and absent on the Qwens; no rung's median leaves the 60–120 band on the Qwens, while on the Gemmas every marker rung above q ≈ 4 does.

---

## 6. Phase 6 — better reference ladders (prototype)

Design principle kept throughout: a reference differs from A in the **identity of the marker** (and severity), and in nothing else that can be avoided. Everything below stays inside §7.3's grammar except F4, which is a new predicate form and is labelled as such.

### F1 — the same marker families under the robust frames, full ladder 1..12

| | |
|---|---|
| template | the two frames that are robust for every marker and for A: w0 `Use the word X exactly q times.` and w3 `The word X must appear exactly q times.` (both already frozen wordings; allocation restricted to them), **or** all four frames with the marker **quoted** (`Use the word "namely" exactly q times.`) if the researcher prefers four wordings — quoting is a one-character change to each frozen string and must be screened, not assumed |
| verifier | unchanged (`marker_count`, `s0_count`) |
| severity | q ∈ 1..12 measured in full at calibration (the reserve is *not* left to §12.6's expansion, whose trigger the noisy pre-screen defeats) |
| expected easy end | q = 1–2: 0.85–0.99 on every model except *instead* (Gemma floor) and *though* / *whereas* on the Qwens (0.87–0.99 at q = 1, collapsing by q = 3) |
| expected hard end | q = 12: 0.31–0.42 on e4b (measured), 0.38–0.49 on e2b (measured for MK2/MK4/MK5), extrapolated ≈ 0.3 on qwen3-4b and ≈ 0.4–0.5 on 2507 (needs F2) |
| why severity moves difficulty | with the uptake floor removed the failure mode is count control, whose miss distribution widens with q (overshoot 0.0 → 0.3–0.45 from q = 1 to 12 on e4b) |
| comparability to A | same instrument, same frames — but A's own rows would have to be allocated the same way (A's four wordings are carried byte-identically from v3; restricting *allocation* leaves the strings untouched, quoting does not). Either way A's solo numbers change and v7's ι_A values are not comparable |
| vacuity / chance | κ = 0.000–0.007 (unchanged); vacuity 0 |
| evidence on stored rows | 5 / 7 / 5 / 3 Tier-1 families C4-like (§5.2) |

### F2 — the ladder extended to q = 16 on the easy checkpoint

Same as F1 with q ∈ 1..16 for *thus, hence, namely, indeed, instead* on `qwen3-4b-instruct-2507` (and *hence* on qwen3-4b), where P(S = q) is still 0.80–0.94 at q = 6 and ≈ 0.55–0.65 at q = 8. Mechanical expectation from the measured decay (≈ 0.1 per rung beyond 6): ≈ 0.2–0.3 at q = 14–16. Cost of the length: 16 occurrences of a 4–6-letter word in a 60–120-word answer is 13–27 % of the words, so the stem band starts to bind — check median words at screening; a family whose q = 16 rung leaves the band is capped at the last in-band rung. B-interaction: κ(R|B) stays 0 (the marker must be produced, B does not produce it).

### F3 — more markers with the same syntax

Registered reserves *albeit* (6, contrastive), *notably* (7, emphatic), *besides* (7, additive) — all zero natural frequency, all admissible only by §32 amendment today — and the eight unregistered admissible words (`d6_marker_frequency.json`): *yet, still, then, next, rather, further, equally, granted*. Two groups by mechanism:

- **zero-frequency, single-sense words** (*albeit, notably, besides, equally, granted*): expected to behave like *indeed* / *hence* — clean count-control ladders, ι from ≈ 0.95 to ≈ 0.4 over 1..12; *albeit* adds a second contrastive marker (A's role) beside *though*, whose overshoot makes it a poor ladder on the Qwens.
- **common short words with non-connective senses** (*yet, still, then, next, rather, further*): natural P(≥ 1) 0.005–0.10 and mean natural count ≤ 0.10, so still chance-free at q ≥ 2; the verifier counts every sense, so the model must *suppress* natural uses as well as produce — a mechanically different and probably steeper source of difficulty at low q. These are the candidates most likely to give rungs *above* A on the high-ι_A models (easy at q = 1–2 because the word is natural) and *below* A quickly.

Both groups keep A's template and length caliper (all ≤ 7 letters). Risk for F3b: §7.7's semantic-neutrality audit (*still water*, *not yet*) was the registered reason for leaving them out; the screening (§7) measures rather than assumes it.

### F4 — a marker count lower bound (new form; comparability cost stated)

`Use the word X at least q times.` (form `count_lower_bound`, class production, statistic `marker_occurrence`). Overshoot cannot fail it, so difficulty is undershoot only and the ladder is monotone by construction and smooth in q (no cliff at q = 3 for *though*). Chance: κ at q = 1 equals natural P(≥ 1) ≤ 0.11, 0 beyond. Under §7.4 this is **not Tier 1** (operator ≠ `==`), so it cannot occupy a core or spectrum slot without amending the tier rule; its value is as a *diagnostic* ladder that separates "can the model produce X q times" from "can it stop at exactly q" — the two halves of exact-count difficulty that §5.1 shows are model-specific. Recommended for the screen, not for the spectrum, unless the researcher accepts a lower-bound spectrum as a secondary.

### Families examined and not recommended

- *instead* (MK7) on the Gemmas: floored under every frame; keep only on the Qwens.
- *though* / *whereas* on the Qwens as **ladders**: 2–3 informative rungs then a floor; they remain good *hard* references (ι 0.1–0.4 at q ≥ 3) and are already C4 groups, so keep them for the hard side, not for a within-family span.
- XC3 (sentence count): trivial on 2507 (1.00 at every q ≤ 10), easy on qwen3-4b until q = 8, inverted on the Gemmas (more sentences is easier). XC2 (comma count): ι ≈ 0 everywhere. XC1 (semicolons) is the one Tier-2 ladder that works on all four (span 0.30–0.60, straddling on the Qwens).
- High-frequency markers (*also* 0.34–0.42, *finally* 0.17–0.19): fail §7.6's frequency rule and would carry κ ≈ 0.2–0.4 at q = 1; not worth the chance amplification when F3 offers chance-free alternatives.

### 6.5 What any of this touches

F1's allocation change touches §8.4 (and A's rows), F1-quoted touches §7.8's frozen strings, F2 touches §7.10's declared ranges, F3 touches §7.6/§7.10's vocabulary and population hash, F4 adds a form to §7.3. All are candidate-population and wording changes that §12.5 freezes "by this document"; none is a v7 amendment (§32.3 refuses §13 after Gate 2.5 and the wordings are bound into the manifest). They are v8 design inputs.

---

## 7. Phase 7 — the cheapest screen that answers "does this ladder span?"

Question screened, and nothing else: *does family F under frame set W produce a wide, monotone, reliable range of ι(R) on model M?* No composed cell is generated, so no outcome can leak into the selection (§12.5's sequence).

**Design (development namespace, per model).**

| element | choice | why |
|---|---|---|
| topics | the registered 24 pre-screen topics + 24 further calibration-A topics = 48 | SE(p) ≈ 0.05 at 96 rows per rung, enough to see a 0.40 span and a monotone trend, not enough to admit anything (admission stays with 192 × 4 at calibration) |
| draws | 2 per topic per rung, temperature/decoding as registered | |
| cells | solo:F:q for every rung; one unconstrained cell per topic × draw (96 rows) scored on every candidate — supplies κ_c for all families at once (§13.2) | chance compliance and vacuity for free |
| frames | F1: w0 and w3 (48 rows each per rung) so the two robust frames are compared, not pooled; F1-quoted as a separate arm on 2–3 families only | isolates the parse effect from the count effect |
| ladders | q = 1..12 (1..16 on 2507 for F2) | |
| families | MK1–MK8 (F1), albeit/notably/besides + rather/further/still/yet/then (F3), 2 lower-bound families (F4: *hence*, *thus*) | 8 + 8 + 2 = 18 families; drop MK7 on the Gemmas |
| rows | ≈ 18 × 12 × 96 + 96 ≈ 20.8k (qwen3-4b, Gemmas), ≈ 25k with F2 on 2507 | at the measured shared-card rates (15.5 rows/s qwen3-4b, 4.7 rows/s gemma-e4b during v7's Gate 2) ≈ 22–27 min on a Qwen lane, ≈ 75 min on a Gemma lane |
| what is already free | every existing Gate-2 row whose drawn wording is w0 or w3 is a valid F1 measurement of MK1–MK8 at q = 1..8 (and 9–12 on the Gemmas) at 192 topics × 2 draws | the screen's MK1–MK8 arm can be skipped on the four registered models; only F2/F3/F4 rungs are new |

**Per-family statistics** (all from solo and unconstrained rows): Spearman(q, ι) and the number of adjacent inversions > 0.05 (monotonicity); calibrated span over rungs with p_solo ∈ [0.10, 0.90] (eligibility survival), and span over the Wilson-admissible rungs (p ≤ 0.8575 at n = 192 — at the screen's n = 96, p ≤ 0.82); straddling: whether rungs fall strictly below and above the model's *expected* ι_A (the registered v7 value for the four models, recomputed under the same frame set for A); κ_c at every rung; vacuity; median words vs the 60–120 band; P(S = 0) per frame (uptake).

**Ranking rule** (declared before the screen, cheap to apply): a family is *promising* when Spearman ≤ −0.8, eligible span ≥ 0.45, it straddles the expected ι_A with ≥ 2 rungs on each side, κ_c ≤ 0.05 everywhere, vacuity 0, and no rung's median words exceeds 130. Rank by eligible span among promising families; ties by the number of eligible rungs. From the stored rows the expected ranking is: e4b — MK4, MK1/MK2, MK5, MK6(w3), MK8; e2b — MK5, MK6(w3), MK8, MK1, MK4; qwen3-4b — MK7, MK5, MK8, MK4(hard side only), MK1/MK2/MK6 (need F2); 2507 — MK3, MK4, MK8, then MK1/MK2/MK5/MK6 only with F2.

**Non-leakage.** The screen reads solo, unconstrained and structural quantities only; it selects *families and rungs to calibrate*, never references; admission and selection remain §13's on a fresh 192 × 4 calibration.

---

## 8. Phase 8 — the future spectrum experiment (design only)

**Question.** How does D(B←R) change with ι(R), within same-form marker constraints, and does A's loss exceed what its difficulty predicts (δ_diff)?

**Companions.** Per model, from the families that survived §7 and §13 (V_head, V_chance, V_inter, V_stab; V_diff *not* applied to spectrum rungs — the §13.7 folding is the tension RESEARCH_STATE §4an already records for v8):

- three core families f₁–f₃ as today (matched within 0.10);
- per core family two spectrum rungs strictly below and above ι_A, targets ι_A ∓ 0.20 clipped to the admissible band (so on e4b/qwen3-4b the upper target is ≈ ι_A + 0.12, the widest admissible; on 2507 and e2b ± 0.20 is reachable);
- one further *below* rung per family at ι_A − 0.35 where the ladder has it (F1/F2 make this available on all four), so each family contributes 4 points spanning ≈ 0.45–0.50 rather than 3 points in 0.16;
- ≥ 2 families on each side of A (§13.13), never dozens of near-identical rungs: 9–12 companions per model.

Illustration from the stored calibrated rungs (what already qualifies under everything but the caliper): qwen3-4b — MK7 {3: 0.48, 2: 0.67, 1: 0.80}, MK5 {5: 0.52, 3: 0.59, 1: 0.83}, MK1 {8: 0.55, 6: 0.69, 3: 0.70} + F2 rungs for the hard side of MK1; 2507 — MK4 {6: 0.33, 5: 0.56, 4: 0.66, 3: 0.89}, MK3 {5: 0.27, 4: 0.32, 3: 0.55, 2: 0.88}, MK8 {6: 0.46, 4: 0.57, 3: 0.60, 2: 0.79}; e2b — MK5 {12: 0.39, 8: 0.59, 3: 0.94→ineligible, 4: 0.86}, MK6-w3 {8: 0.69, 3: 0.86, 1: 0.15}, MK1-w0 {8: 0.45, 5: 0.65, 2: 0.89}.

**Cells generated per companion R_i** on the frozen 384 blocks × 8 draws, both registered orders: `pair:B+R_i`, `pair:R_i+B` (6,144 rows) and `solo:R_i` (3,072) for the realised ι; the unconstrained cell is re-scored from stored text (§26 identity). `pair:A+B` / `pair:B+A` / `solo:A` are regenerated only if A's frame allocation changes (F1), 15.4k rows once.

**Estimation.** Per configuration (outcome_first / outcome_second): Y_i = D(B←R_i) = mean over blocks of X_B(B solo) − X_B(B+R_i), paired; d_i = realised ι(R_i) on the same blocks. Primary form §11.8: Y_{f,s} = α_f + β d_{f,s} + ε, OLS with family intercepts, prediction at A through the mean intercept, δ_diff = D(B←A) − Ŷ_A; secondary on raw solo. **Clustering:** rungs of one family share α_f and share the family's idiosyncrasies (its parse robustness, its overshoot regime), so (i) β is identified from *within-family* variation only — that is why each family must span ≥ 0.40 on its own, which is C4's actual purpose; (ii) uncertainty by §17.2's topic-block bootstrap refitting every replicate, **plus** a leave-one-family-out jackknife on β and δ_diff reported beside it — with 3–4 families the jackknife is the honest statement of how much one family drives the slope; (iii) a family-specific slope β_f is reported descriptively (three points per family cannot license it). Support check §13.13 on the realised coordinates, and the share of bootstrap replicates in which it holds.

**Precision.** SE(D) ≈ 0.013 per companion at 384 × 8; with 10 points of ι-sd ≈ 0.15, SE(β) ≈ 0.03 per unit ι: a slope of 0.25 (one SESOI of extra loss per 0.40 of difficulty) is ≈ 8 SE, β = 0.10 ≈ 3 SE; the realised-gap bias bound on Δ_R, β × 0.05–0.09, becomes measurable.

---

## 9. Phase 9 — the minimal experiment

| | recommendation |
|---|---|
| model first | **qwen3-4b-instruct-2507**: both ±0.20 targets admissible (ι_A 0.540), the cleanest counter (least overshoot, least parse artefact: only *overall* w1/w2 and *instead* w2), 3.3× the Gemma throughput, and its r4 rehearsal freezes blocks that B+R_i can be generated on. Second: qwen3-4b (three completed rehearsals). The Gemmas last — e2b's flatness and e4b's high ι_A make them the hardest cases, and F1 is a prerequisite there |
| step 1 — screen (§7) | 2507: F2 on MK1/MK2/MK5/MK6/MK7 at q = 9..16 (8 rungs × 5 × 96 = 3.8k) + F3 eight markers at 1..12 (9.2k) + F4 two families (2.3k) + unconstrained (96): **≈ 15.5k generations ≈ 17 min**. MK1–MK8 at 1..8 need nothing (stored rows) |
| step 2 — calibrate (both splits, 192 × 4) the 3–4 families and ≈ 6 rungs each the screen ranks first | ≈ 4 × 6 × 3,072 ≈ **74k generations ≈ 1.3 h** (less by the rungs already calibrated in v7 under w0/w3) |
| step 3 — spectrum composition (§8) | 9–12 companions × 9.2k ≈ **83–110k generations ≈ 1.5–2 h** |
| total for one model | ≈ 170–200k generations, ≈ 3–3.5 h on one Qwen lane; against v7's ≈ 101k pre-confirmatory + 80k confirmatory (base + core) per replication: **≈ 1× one v7 replication, of which only the last third produces composed outcomes**. On a Gemma lane ×3.3 in wall time |
| new reference families | 3 registered reserves + 5 unregistered markers screened (F3); 2 lower-bound diagnostics (F4); expected to *adopt* 1–3 |
| rungs per family | 12 (16 on 2507) screened; 4–6 calibrated; 3–4 composed |
| solo calibration rows | ≈ 74k per model (step 2) |
| spectrum references composed with B | 9–12 per model |
| do not launch | nothing here is authorised to run; the r4 lanes own both cards |

---

## 10. Phase 10 — isolation

See `SAFETY_AND_ISOLATION.md` beside this file: before/after SHA-256 of every stage-record JSON in the registered v7 tree (54 files), the durable root (378 files) and the three completed development roots (134 files); size/mtime of every registered row file; process and GPU listings; the main and fix worktrees' HEAD and status. Everything this investigation wrote lives under `/home/cnm13ryan/git/dci-v7-spectrum-dev/` (its own venv) and the session scratchpad.

---

## Appendix — regenerating

```
cd /home/cnm13ryan/git/dci-v7-spectrum-dev/dci1
.venv/bin/python tools/v7_spectrum_dev_counts.py   --tree /home/cnm13ryan/git/dci/dci1/evidence/dci1v7 --model <m> --out reports/dci1v7/difficulty_spectrum_dev/counts
.venv/bin/python tools/v7_spectrum_dev_wordings.py --tree /home/cnm13ryan/git/dci/dci1/evidence/dci1v7 --model <m> --out reports/dci1v7/difficulty_spectrum_dev/counts
.venv/bin/python tools/v7_spectrum_dev_analysis.py --tree /home/cnm13ryan/git/dci/dci1/evidence/dci1v7 --landscape reports/dci1v7/reference_support_landscape/landscape.json --out reports/dci1v7/difficulty_spectrum_dev
.venv/bin/python tools/v7_spectrum_dev_plot_wordings.py reports/dci1v7/difficulty_spectrum_dev
```
```
.venv/bin/python tools/v7_spectrum_dev_wording_summary.py reports/dci1v7/difficulty_spectrum_dev
```
(`wording_sensitivity.json`, `robust_wording_ladders.json` — pure functions of `counts/wordings_<model>.json` and `spectrum_dev.json`.)
