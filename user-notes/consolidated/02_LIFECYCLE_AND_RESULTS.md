# 02 — Lifecycle, attrition and results, version by version

Consolidated 2026-08-27 at HEAD `76ae840`. Numbers are quoted from signed records or the machine-produced reports that were verified against them (verification notes in [03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §3). Evidence class is stated for every block: **REGISTERED** (signed stage record / terminal report / registered analysis), **SCREEN** (non-confirmatory design evidence, protocol hashed before generation), **POST-HOC** (read-only re-analysis of closed evidence), **DEVELOPMENT** (design-fitting on a predecessor), **EXPLORATORY** (Arc 1, `EXPLORATORY_NO_EVIDENCE`). Companion documents: [00](00_SCIENTIFIC_STORY.md) · [01](01_RESEARCH_QUESTION_AND_DESIGN.md) · [03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) · [04](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md).

Note on locations: signed stage records live under `dci1/evidence/<study>/<model>/` and their byte-identical mirror `dci1/durable_root/`; **both are gitignored**, so they exist only on the producing workstation. Committed surrogates are under `dci1/reports/`.

---

## 1. The attrition table (28 model-replications, 7 registered states)

| Protocol state | gemma-3n-e2b-it | gemma-3n-e4b-it | qwen3-4b | qwen3-4b-instruct-2507 | Confirmatory rows |
|---|---|---|---|---|---|
| **v2** (16 Aug) | Gate 0 FAIL — truncation 0.1389 > 0.10 ceiling; Gate 2 0 admitted references | Gate 0 FAIL — truncation 0.1502 | Gate 2 FAIL — A solo failure 0.125 at n=3 outside (0.15, 0.50); 0 admitted | Gate 2 FAIL — 0.073 at n=3; 0 admitted | 0 |
| **v3** (16–19 Aug) | **UNMASKED_ANALYSIS** PASSED (n*=5, m*=7, cap 512) | **UNMASKED_ANALYSIS** PASSED (n*=7, m*=7) | `REFERENCE_POOL_MISMATCH` (m*=10; 2 eligible rungs, 3 required) | `REFERENCE_POOL_MISMATCH` (m*=8; 2 eligible) | 36,864 × 2 |
| **v4r2** (19–20 Aug) | REGIME_SCREEN PASS; Gate 2 **deliberately not run** — would return `REGIME_NOT_FOUND` (B solo vacuity ≥ 0.208 vs cap 0.10) | same | same | same | 0 |
| **v4r3** (21 Aug) | REGIME_SCREEN PASS (coverage PASS) | REGIME_SCREEN PASS (coverage fail C2, C4) | REGIME_SCREEN PASS (fail C4) | REGIME_SCREEN PASS (fail C4) | 0 — closed study-wide at `GATE_1_MEASUREMENT` / `MEASUREMENT_EVIDENCE_INSUFFICIENT` |
| **v4r4** (21–22 Aug) | Gate 4 **`COMPOSED_HEADROOM_FAILURE`** on the only **full** design (RF11 companion cells 0.958–1.000) | **UNMASKED_ANALYSIS** on the 8-cell reduced design | **UNMASKED_ANALYSIS** on the reduced design (2 core refs admitted, 3 required) | Gate 4 **`COMPOSED_HEADROOM_FAILURE`** (`solo:CL` 0.9896) | 24,576 × 2 |
| **v5** (23–24 Aug) | Gate 3C D6 `REFERENCE_SUPPORT_NOT_IDENTIFIED` (C4 4 of 6) → PREFREEZE_AUDIT FAIL (`support_satisfied`); terminal status never raised (V5-E32) | Gate 4 **`COMPOSED_HEADROOM_FAILURE`** (`solo:CL` 0.9583, `pair:B+CL` B 0.9792) | D6 (C4 5 of 6) → PREFREEZE_AUDIT FAIL | Gate 4 **`COMPOSED_HEADROOM_FAILURE`** (`pair:B+R1` B 0.9896, `pair:R1+B` B 0.9583) | 0 (459,312 pre-confirmatory rows) |
| **v6** (26–27 Aug) | **`PREFREEZE_AUDIT_FAILURE`** (`support_satisfied` after calibrated C4 False; also `protocol_hashes_agree`) | Gate 4 **`COMPOSED_HEADROOM_FAILURE`** (`solo:CL` 0.9583; `pair:B+CL` CL slot 0.0417) | Gate 2.75 **`COMPOSED_HEADROOM_UNREACHABLE`** (`pair:B+A` B 0.8906, projected [0.779, **1.002**]) | Gate 2.75 **`COMPOSED_HEADROOM_UNREACHABLE`** (`pair:B+A` B 0.9245 → [0.825, 1.024]) | 0 (516,240 rows) |

Sources: v2 `dci1/evidence/dci1-v2/<model>/prefreeze-apparatus/{pilot_report,calibration/gate2}.json`; v3 [`dci1/RESULTS_V3.md`](../../dci1/RESULTS_V3.md); v4r2 [`dci1/reports/ENDPOINT_2026-08-20.md`](../../dci1/reports/ENDPOINT_2026-08-20.md); v4r3 [`dci1/reports/dci1v4r3/closure.json`](../../dci1/reports/dci1v4r3/closure.json); v4r4 [`dci1/reports/dci1v4r4/final_results.json`](../../dci1/reports/dci1v4r4/final_results.json), `dci1/evidence/dci1v4r4/<model>/terminal_report.json`; v5 [`dci1/reports/dci1v5/closure.json`](../../dci1/reports/dci1v5/closure.json); v6 `dci1/evidence/dci1v6/<model>/terminal_report.json` (2026-08-27 09:51–10:11 UTC; **not yet reflected in any committed document**).

Reading: the companion-swap estimand Δ_R was **never identified** under the v4+ definition. The two mechanisms that stopped it — reference support (§12.6/§13.4) and composed headroom (§13.10/§13.14/Gate 2.75) — each fired in every design that reached them.

## 2. v2 — the fixed reference pool is uniformly harder than A or B (REGISTERED, pre-freeze)

- Candidates C1–C12 fail 47–100 % solo versus A 2–33 %; closest candidate distance 0.146/0.167 (Qwen, C10) and 0.583 (E2B, C1) against a ±0.10 window; 86.5 % of calibration topics at the target ceiling on the Qwens. Gemmas exceeded the 400-token cap (truncation 13.9 %/15.0 %). Gate 1 human labels never closed (`PENDING_HUMAN`; fail-class starvation: Qwen packets 75 pass + all 17 fails).
- Reasons v2 was superseded: [`dci1/REPORT.md`](../../dci1/REPORT.md) §15–20; [`dci1/reports/inspection/2026-08-16_promptmd_redteam.md`](../../dci1/reports/inspection/2026-08-16_promptmd_redteam.md) (CLI confirmatory path bypassed the evidence tree; `unmask` did not exist); provenance defects (`dci1/` untracked, empty environment digest, E4B calibration fragment generated pre-qualification — marked `SUPERSEDED_NON_EVIDENCE` in v3 §33).

## 3. v3 — two Gemma replications analysed; direction unresolved everywhere (REGISTERED)

Design: E2B refs RF1@5, RF2@5, RF6@4; E4B refs RF2@2, RF6@4, RF4@4; 36,864 generations each; verifier freeze `334bb2b1…`; Gate 1 basis `autorater_calibration_approved` / `HUMAN_VALIDATION_UNAVAILABLE`.

| Model | Stratum | τ̂ | 95 % simultaneous | Direction / magnitude claim |
|---|---|---:|---|---|
| E2B | target-first | +0.0069 | [−0.080, +0.094] | unresolved / **equivalence** (inside ±0.10) |
| E2B | added-first | −0.0260 | [−0.117, +0.065] | unresolved / unresolved |
| E4B | target-first | +0.0903 | [−0.004, +0.184] | unresolved / unresolved |
| E4B | added-first | +0.0399 | [−0.047, +0.127] | unresolved / unresolved |

- Exchangeability fails on both (`exchangeability_holds: False`; E2B δ₂₃ = −0.154 [−0.234, −0.073]); uptake mismatch (E4B refs delivered 4–10 % vs B 44 %).
- The one resolved claim turns on the **draw lottery**: 15 of 16 cached draws unused; E2B target-first registered draw (+0.007) sits below the 5th percentile of its own pseudo-selection distribution (mean +0.089, 99.5 % > 0).
- Human fail-class criterion unmet: 4/52 = 7.7 %, Wilson upper 16.1 % vs ≤ 10 %; pass class 0/52 (upper 4.9 %). "`human-validated` may be claimed for the pass class only".
- Qwen non-identification: qwen3-4b m*=10, focal 0.3125, caliper-eligible only RF4@2 (0.2396), RF6@0 (0.3229); instruct m*=8, focal 0.2604, RF3@2 (0.2813), RF4@4 (0.3229). "Not licensed: any claim that interference is absent, small, or different in Qwen models."
- **POST-HOC re-analysis** ([`dci1/reports/v3_reanalysis/REPORT.md`](../../dci1/reports/v3_reanalysis/REPORT.md)): on confirmatory rows only D(A←B), D(A←R_j), Δ^A, uptake and joint success are identified; D(B←A), Λ, Δ_R, Ξ are not (no solo B/R cells on confirmatory topics). Δ^A on all 16 draws = **+0.0639 [+0.0405, +0.0871]** (E2B), **+0.0737 [+0.0519, +0.0951]** (E4B); survives length matching (+0.118/+0.059) with full common support — the generic-load region. Per-reference E2B +0.056, +0.142, −0.006. A quantity quoted in [`dci1/reports/companion_identity_review.md`](../../dci1/reports/companion_identity_review.md) §7 as D(B←A) = 0.468/0.316 is a cross-set difference and "may not be quoted as either" delivery loss.

Sources: [`dci1/RESULTS_V3.md`](../../dci1/RESULTS_V3.md); `dci1/evidence/dci1-v3/<model>/analysis/unmasked/result.json`; [`dci1/DECISIONS_V3.md`](../../dci1/DECISIONS_V3.md); [`user-notes/DCI1_v3_to_v4r1_change_summary.md`](../DCI1_v3_to_v4r1_change_summary.md) C1–C11.

## 4. B+R pilot — a "pair-specific" effect that dissolves under the registered vacuity bound (SCREEN + POST-HOC)

[`dci1/reports/br_pilot_v4/result.json`](../../dci1/reports/br_pilot_v4/result.json) (Gemmas only, 576 rows/model, refs matched to B; protocol `229eeae8…`):

| | E2B | E4B |
|---|---:|---:|
| D(B←A) | +0.468 [+0.384, +0.549] | +0.316 [+0.222, +0.403] |
| D(B←R̄) | +0.125 | −0.059 |
| **Δ = D(B←A) − D(B←R̄)** | **+0.343 [+0.282, +0.405]** → `H1_PAIR_SPECIFIC` | **+0.375 [+0.319, +0.430]** |

[`dci1/reports/pilot_reanalysis/REPORT.md`](../../dci1/reports/pilot_reanalysis/REPORT.md): B+R̄ cells average 24.8 words vs A+B 128–139 (five-fold). Under §17.4's registered bound (every vacuous pass forced to failure) Δ = **+0.095 / +0.068** — below the 0.10 generic-load threshold; at matched length over common support **−0.057 / −0.003**. The ≥ 20-word restriction that had reported Δ unmoved (+0.348/+0.360) drops 36 % of one arm and is not the registered operation — "It should not be quoted." Disposition: unresolved with both bounds.

## 5. v4r2 — four design screens, one withdrawn dispute, and a decision boundary (SCREEN)

All four screens are `claim_licensed: False` by construction; Gate 1 was unapproved; none is a registered admission.

**FORM × STEM** ([report](../../dci1/reports/fs_screen_v4/REPORT.md), 13,392 rows, hash `98f8ee0d…`): the registered pool (monotone `S ≤ q` budgets, downward-closed under prefix — the empty string passes 94/94) meets §13.2 conditions 1∧6 on **0** rungs on all four models; candidate non-budget families reach it on three of four (bootstrap P(≥3) 0.41–0.88). A uniform stem removes B-solo vacuity (0.47/0.39/1.00/0.94 → 0.00/0.00/0.00/0.17). D(B←A) raw / §17.4-forced: E2B +0.375 / **0.000** (current stem), +0.208 / +0.208 (floored).

**B-grid** ([report](../../dci1/reports/bgrid_screen_v4/REPORT.md), 2,112 rows): verdict **MARGINAL** — instruct's only in-band rungs both 0.667; a terminal call flipped between two single draws (0.542 → 0.667); qwen3-4b `FOCAL_RANGE_EXHAUSTED` replicated (0.375 vs 0.60).

**Gate-2 calibration screen** ([report](../../dci1/reports/cal_screen_v4/REPORT.md), 169,632 generations, registered 96 topics × M_cal = 4): B solo vacuity under the registered prompt **0.208–0.870 at every rung on all four models** (cap 0.10) → `REGIME_NOT_FOUND` everywhere; the pool is "length-falsified, not falsified" (under the stem 3/4/1/4 families clear conditions 1∧6); §12.4's graded clause has two readings — mean fires on every in-band rung, share on none.

**Pairwise matrix** ([report](../../dci1/reports/matrix_screen_v4/REPORT.md), 64,800 generations, 120 blocks, M = 4, per-model hashes frozen; readings fixed in §7b before scoring):

| Model (A:n, B:m; refs; CL) | D(B←A) | D(A←B) | **Δ_R** (95 % percentile) | Δ_R simultaneous | Ξ | Δ_class |
|---|---|---|---|---|---|---|
| E2B (7, 10; CR6:7, RF3:4, RF2:6; CL7:80) | +0.086 [+0.031, +0.143] | +0.178 | **+0.048 [+0.009, +0.087]** | [−0.002, +0.098] | −0.036 | **−0.515 [−0.564, −0.464]** |
| E4B (6, 9; RF8:8, RF3:4, RF2:8; CL8:25) | +0.228 | +0.223 | **+0.101 [+0.056, +0.146]** | [+0.043, +0.158] | −0.009 | **−0.404** |
| qwen3-4b (2, 12; CR7:44, CL8:5, RF7:24) | −0.039 | +0.357 | **+0.011 [−0.020, +0.044]** | [−0.029, +0.052] | +0.131 | — |
| instruct (5, 10; CR7:44, RF1:5, RF7:24; CL8:10) | −0.095 | −0.055 | **−0.024 [−0.067, +0.019]** | [−0.079, +0.030] | +0.090 | +0.087 |

- Δ_R "reaches the registered pair-specific threshold of 0.25 on no model"; simultaneous interval inside ±0.10 on three of four; precision precondition met on one model.
- **Class dominates identity by an order of magnitude**: a production-class companion costs B +0.601 (E2B) / +0.632 (E4B) where A costs +0.086 / +0.228.
- **Position dominates too**: B loses 0.288 / 0.350 by being stated second; single-order Δ_R changes sign on all four (E2B +0.326 vs −0.231).
- An admitted reference out-damages A on E2B: paired Δ₁ = D(B←A) − D(B←CR6:7) = **−0.078, simultaneous [−0.134, −0.023]**.
- Difficulty residual of A identified (+0.067 / +0.118 / −0.050 / −0.048); **length residual not identified** (A's length shift outside every other companion's range — collinear). An earlier pass that fitted through A and reported ±0.010 is withdrawn.
- §25 accidental compliance: A 0.000 on all four; references 0.52–0.89.

**§13.2 dispute** ([report](../../dci1/reports/section_13_2_v4/REPORT.md)): the claim that §13.2's condition 2 was ambiguous (abstain vs reject) was withdrawn — §12.2 measures all 94 rungs, `gates.admit_family` rejects, `researcher_decision_required: false`. Standing: "The registered §13.2 has not been run on any model, because Gate 2 has not run." The seventh channel: 12/12 references matched to A on raw solo compliance, **2/12** on instructed compliance ([`instructed_compliance.json`](../../dci1/reports/section_13_2_v4/instructed_compliance.json)).

**Endpoint** ([`dci1/reports/ENDPOINT_2026-08-20.md`](../../dci1/reports/ENDPOINT_2026-08-20.md)): "Endpoint reached: C — researcher decision boundary … the registered design cannot produce any [confirmatory evidence] as written." Gate 2 not run because a terminal record is write-once and §31 forbids amending because a gate failed. §10.2 completed for A, B and RF1–RF8 (determinism 1,311,582 verdicts per process × 672 processes; reimplementation 1.000 over 14,046 texts after fixing the reimplementation's own segmenter defect, `[^\W\d_]+`).

## 6. v4r3 — adopted, run to the regime screen, closed at Gate 1 (REGISTERED)

- Regime screen ([REPORT](../../dci1/reports/dci1v4r3/REPORT.md) §1): cap 512 all models; ι_A 0.526/0.750/0.750/0.542; §12.6 coverage PASS on E2B only; B solo vacuity under the stem ≤ 0.042; **anti-productive instances 31–42 %** of the library (stating the constraint lowers compliance).
- Gate 1 ([`gate1_decision.json`](../../dci1/reports/dci1v4r3/gate1_decision.json), [`gate1_r5_decision.json`](../../dci1/reports/dci1v4r3/gate1_r5_decision.json)): §10.2 PASS (determinism 1.0 over 584 instruments; reimplementation 1.0 over 37,700 responses / 700,800 verdicts; boundary 164 cases, 1,280 checks, 0 failures; witnesses 92,988 pairs). §10.3: no annotator independent of the design team. §10.4-R (`v4r-medium`, 96 cards): truncation 0.3125 (≤ 0.10 required), parse validity 0.6875 (≥ 0.95), specificity 0.613 (≥ 0.90), sensitivity 0.771 (≥ 0.80) — `MEASUREMENT_EVIDENCE_INSUFFICIENT`. §10.4-R2 (microcases): `denominator_swap` sensitivity 0.231 vs floor 0.50 → FAIL; diagnosis "convention-access, not competence" ([`validator_diagnosis.json`](../../dci1/reports/dci1v4r3/validator_diagnosis.json): wordless answers 0.231 → 0.692 with conventions). §10.7-R5 (A14): `SPECIFICATION_AMBIGUOUS` — 120 wordings genuinely ambiguous, all in CP4/CP7.
- Human evidence, all by the author ("Bryan", `independent_of_design_team: false`): 128/128 verifier-operationalisation cards correct with the verdict visible ([`verifier_audit/report_Bryan.json`](../../dci1/reports/dci1v4r3/verifier_audit/report_Bryan.json)); 23/25 microcases (Wilson upper 0.215 vs 0.10); A9 300-item plan frozen, 5 unsealed labels.
- Defect sensitivity over 30,720 real responses ([`defect_sensitivity.json`](../../dci1/reports/dci1v4r3/defect_sensitivity.json)): `inequality_flip` 0.955, `denominator_swap` 0.218, `numerator_swap` 0.328, `off_by_one` 0.111, `vacuity_ignored` 0.0.
- Closure ([`closure.json`](../../dci1/reports/dci1v4r3/closure.json)): `CLOSED`, `closed_at_stage GATE_1_MEASUREMENT`, `terminal_status MEASUREMENT_EVIDENCE_INSUFFICIENT`, hash `930720a0…`, superseded by v4r4; nothing under v4r3's trees edited.

## 7. v4r4 — the only confirmatory data (REGISTERED unless marked)

### 7.1 Gate 1 (deterministic; all four PASS; decision hash `df630dec`)
Determinism 1.000 (3 processes, 400 responses, 524 instruments); independent reimplementation `per_instrument_min` 1.000 over **628,800 verdicts** on 36,164 responses; boundary/adversarial/Unicode 164 cases, 85,936 verdicts, 0 failures; witnesses 92,148 pairs; specification audit 30 kinds, 0 ambiguous; mutation validation 0 undetected (`inequality_flip`, `numerator_swap`, `off_by_one` 30/30; `segmentation_drift` 22/22; `vacuity_ignored` 17/17; `denominator_swap` 12/12); 2,141 wordings, 0 ambiguous. CP4/CP7 removed before Gate 1 without reading a composed outcome ([`cp4_cp7_analysis.json`](../../dci1/reports/dci1v4r4/cp4_cp7_analysis.json)). Coverage at round zero ([`coverage.json`](../../dci1/reports/dci1v4r4/coverage.json)): C4 groups 4/5/4/4 — met with **no leave-one-family-out margin on three models** (B7 declined the expansion).

### 7.2 Gate 2 (62,976 + 768 calibration generations)

| Model | n* | m* | ι_A (as recorded) | ι_A recomputed at n* | Calibration rows |
|---|---:|---:|---:|---:|---:|
| e2b | 1 | 10 | 0.574 | 0.574 | 16,128 |
| e4b | 4 | 10 | 0.695 | 0.727 | 14,976 |
| qwen3-4b | 2 | **12** (§7.2 extension) | 0.702 | 0.719 | 16,896 |
| instruct | 5 | 10 | 0.596 | 0.602 | 15,744 |

The recorded ι_A uses κ_A at severity 1 rather than n* (see [03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §3.2); qwen's B curve m = 7..12 is {0.031, 0.107, 0.245, 0.411, 0.659, 0.742}, so m* = 12 is the last rung of the extended grid.

### 7.3 Gate 3 — the spectrum is identified on one replication of four

| Model | Design | Cells/block | Core refs (need 3) | Spectrum | Statuses |
|---|---|---:|---|---|---|
| e2b | **full** | 47 | 3 (RF9:10, CR5:2, RF11:26) | 6 rungs | COMPANION_CLASS_NOT_MATCHED |
| e4b | reduced | 8 | 0 | — | + EXCESS_NOT_IDENTIFIED, DIFFICULTY_SUPPORT_NOT_IDENTIFIED |
| qwen3-4b | reduced | 8 | 2 (RF11:21, CR5:8) | — | same three |
| instruct | reduced | 8 | 0 | — | same three |

Unifying cause: local sparsity of eligible rungs immediately above ι_A — e4b's nearest rungs carry high chance compliance (RF9:13 ι 0.704 vs 0.695 but solo 0.857 vs 0.727, Newcombe [0.148, 0.343]); qwen has two straddling families where three feature groups are needed (RF2:6 near miss); instruct has a ladder gap (0.592 → 0.722 across ι_A = 0.596). Coverage that passed at pre-screen (C4 groups 7/5/4/4) collapsed at calibration to **3/0/2/0** ([`09_coverage_vs_calibration.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/09_coverage_vs_calibration.json), POST-HOC).

### 7.4 Gate 4 — §13.10 ends two replications (6,816 generations)

| Model | Design | Checks | Outcome | Failing cells (24 topics × M = 4) |
|---|---|---:|---|---|
| e2b | full (1,128 cells) | 80 | **TERMINAL** | `pair:B+R3` B 0.9583, R3 0.9688; `pair:B+R3+` R3+ 1.000; `pair:R3++B` R3+ 1.000; `pair:R3+B` R3 0.9583 (R3 = RF11:26, R3+ = RF11:32, vowel-initial) |
| e4b | reduced | 11 | PASS | — |
| qwen3-4b | reduced | 11 | PASS (narrowest: B in `B+CL` 0.9479) | — |
| instruct | reduced | 11 | **TERMINAL** | `solo:CL` 0.9896 (CL8:3, admitted on ι = 0.615 with solo 0.974 / chance 0.932) |

Both terminals carry "a terminal pre-confirmatory status carries no evidence about the effect". Consequence: "No surviving replication identifies a spectrum-dependent quantity." Δ_R, Δ_j, δ_difficulty, Ξ, D(B←R_j), D(R_j←B) are `NOT_IDENTIFIED` for the study.

### 7.5 Freeze and confirmatory generation
Gate 5 at commit `450a0499…` binding 66 §18.1 fields; 8 cells × 384 blocks × M = 8 = **24,576 rows per replication** (3,072 distinct prompts, 24,576 distinct seeds; truncation 6 rows qwen, 1 row e4b; 0 empty/failed). Masked → unmask → final once each under analysis code hash `dffb5a86…`; `post_freeze_delta.json` `scientific_state_unchanged: true`. Evidence: 355 files, 769.7 MB, 155,712 scored rows, mirrored byte-identical.

### 7.6 Every registered estimate (simultaneous 95 % intervals; F1 as computed, k = 3)

**qwen3-4b** (A:2, B:12, CL = CX1:4 "thus ×4", A's structural twin)

| Family | Estimand | outcome_first | outcome_second (POSITION_CONFOUNDED) |
|---|---|---|---|
| F1 | **D(A←B)** | **+0.392 [+0.350, +0.434]** | **+0.329 [+0.284, +0.375]** |
| F1 | D(B←A) | −0.123 [−0.154, −0.092] (delivery *gain*) | −0.012 [−0.045, +0.021] |
| F1 | Λ | −0.515 [−0.567, −0.462] | −0.341 [−0.399, −0.283] |
| F5 | D(A←B)\|vacuity_forced | +0.392 [+0.349, +0.434] | +0.329 [+0.282, +0.376] |
| F6 | vac(B\|B+CL) − vac(B solo) | **+0.129 [+0.098, +0.160]** (F6 gate binds) | +0.008 |
| F9 | D(B←CL) | −0.134 [−0.165, −0.104] | −0.050 [−0.081, −0.020] |
| F9 | Δ_class | +0.011 [−0.011, +0.033] | +0.038 [+0.009, +0.068] |

**gemma-3n-e4b-it** (A:4, B:10, CL = CL7:80)

| Family | Estimand | outcome_first | outcome_second (POSITION_CONFOUNDED) |
|---|---|---|---|
| F1 | **D(A←B)** | **+0.116 [+0.077, +0.155]** | −0.032 [−0.073, +0.009] |
| F1 | **D(B←A)** | +0.006 [−0.018, +0.031] | **+0.283 [+0.249, +0.318]** |
| F1 | Λ | −0.110 [−0.155, −0.065] | +0.315 [+0.259, +0.371] |
| F5 | D(B←A)\|graded_0.99 | −0.010 | +0.186 [+0.151, +0.221] |
| F6 | vacuity differences | 0.0 (degenerate) | 0.0 |
| F9 | D(B←CL) | +0.316 [+0.279, +0.354] | **+0.795 [+0.762, +0.827]** |
| F9 | Δ_class | −0.310 [−0.350, −0.271] | −0.511 [−0.549, −0.473] |

Raw cell means ([`06_effects_and_order.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/06_effects_and_order.json), reproducing every estimate to 1e-9):

| cell | qwen A | qwen B | e4b A | e4b B |
|---|---:|---:|---:|---:|
| solo | 0.720 | 0.779 | 0.772 | 0.851 |
| A first, B second | 0.328 | 0.791 | 0.656 | 0.568 |
| B first, A second | 0.391 | 0.902 | 0.804 | 0.845 |
| B in B+CL / B in CL+B | 0.913 / 0.830 | | 0.535 / **0.057** | |

### 7.7 Claims emitted
- qwen: **L1 for D(A←B) in both configurations**; L1 withheld for D(B←A) (both); L2 withheld ("L2's gate is L1 for both directions"); L3 unreachable; L4 licensed for `F1:D(A<-B)`.
- e4b: L1 for D(A←B) in outcome_first, for D(B←A) in outcome_second; L2 withheld; L3 unreachable; **L4 emitted but invalidated** — `emit_l4` compared the *set* of levels reached, not the level per named member; registered reading "Configuration dependence (§28.1)". Not repaired because the sealed code hash forbids a re-run and §20 forbids re-masking; pinned by `tests_v4r4/test_l4_replication_defect.py`.
- "The two replications disagree qualitatively": on qwen the loss falls on A in both orders and B is undamaged (gains when first); on e4b in the A-first cell both constraints lose and in the B-first cell neither does — Λ flips sign with both intervals excluding zero. Model dependence is described, not estimated (n = 2, no pooled estimand).
- Every statement carries `identification_status: [COMPANION_CLASS_NOT_MATCHED, DIFFICULTY_SUPPORT_NOT_IDENTIFIED, EXCESS_NOT_IDENTIFIED]`, the §10.5 scope sentence, and `not_identified: [D(B<-R_j), D(R_j<-B), Delta_j, Delta_R, delta_difficulty, Xi]`.

### 7.8 Post-hoc diagnostics (POST-HOC; [`SCIENTIFIC_FOLLOWUP_EVIDENCE.md`](../../dci1/reports/dci1v4r4/SCIENTIFIC_FOLLOWUP_EVIDENCE.md), "nothing in it was preregistered")
- Order contrasts (first − second, paired block bootstrap, no claim): e4b D(A←B) +0.148 [+0.120, +0.176], D(B←A) −0.277 [−0.304, −0.250]; qwen D(A←B) +0.063 [+0.028, +0.098].
- Length is not the account: at matched word-count bins B-first cells on qwen sit 0.09–0.14 above B-solo; e4b CL-first gives B 0.069 vs 0.881 solo in the 80–110-word bin ([`05_length_strategy.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/05_length_strategy.json); length is post-treatment).
- Admission landscape ([`02_admission_landscape.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json), shortlisted rungs only): 65 of 84 calibrated rungs lie below ι_A; eligible rungs strictly above 2/1/1/0; 17 rungs changed side between pre-screen and calibration; of 18 rungs inside the caliper 9 refused (8 Newcombe, 1 pre-screen caliper).
- Unreported quantities that exist in `resolved.jsonl`: realised κ_B on the confirmatory unconstrained cell (qwen **0.386**, so ι_B = 0.641 not 0.742); joint success P(both) (qwen A+B 0.270, B+A 0.360; e4b A+B 0.376, B+A 0.681, **CL+B 0.026**); D(CL←B) (+0.276/+0.231; +0.106/+0.053); subject-area heterogeneity (qwen D(A←B)|first 0.203–0.539); the §8.3 greedy replication and the §22 length-stratified decomposition were registered and never produced.

## 8. v5 — run and closed with no confirmatory generation (REGISTERED; manifest `af5fa4bc…`, commit `5ed18543…`)

| | e2b | e4b | qwen3-4b | instruct |
|---|---|---|---|---|
| live rows | 114,792 | 116,400 | 114,648 | 113,472 |
| n* / m* / ι_A | 6 / 10 / 0.594 | 6 / 10 / 0.723 | 2 / 12 / 0.713 | 5 / 11 / 0.532 |
| C4 straddling groups (need 6) | **4** | **5** | **5** | 8 |
| eligible rungs above / below ι_A | 19 / 155 | 14 / 163 | 20 / 154 | 21 / 143 |
| span near-misses (need 0.40) | marker_thus 0.376, letter_a 0.363, marker_hence 0.333 | hence 0.333, namely 0.292, thus 0.209 | sentence 0.366, thus 0.334, namely 0.333 | — |
| admitted arms / cells | base, class / 8 | base, class / 8 | base / 5 | base, core / 26 |
| D6 | NOT_IDENTIFIED, irreversible, 48 members | same | same | identified |
| Gate 4 worst cell | PASS — `pair:B+CL` B 0.8958 (margin 0.054; `solo:B` 0.792, lift +0.104) | **TERMINAL** — `solo:CL` 0.9583, `pair:B+CL` B 0.9792 | PASS — `pair:A+B` B 0.8958 (0.054) | **TERMINAL** — `pair:B+R1` B 0.9896, `pair:R1+B` B 0.9583 |
| PREFREEZE_AUDIT | FAIL (`support_satisfied`; 25/26 pass) | — | FAIL | — |

Closure ([`CLOSURE.md`](../../dci1/reports/dci1v5/CLOSURE.md), [`closure.json`](../../dci1/reports/dci1v5/closure.json)): `NO_REPLICATION_REACHED_CONFIRMATORY_GENERATION`, `masking_opened: false`, 459,312 behavioural rows, all pre-confirmatory; 478,464 further rows under six superseded registrations retained and invalidated. The one replication that survived D6 (instruct) is one of the two Gate 4 killed; "Neither fix would have saved the other group" ([`survival_diagnosis.md`](../../dci1/reports/dci1v5/survival_diagnosis.md)). §13.15's family counts were met on all four (12/12/11 qualified vs ≥ 5); the binding requirement was §12.6 coverage.

What the 459,312 rows support: solo compliance/chance/ι curves for A and B (solo B at m*: 0.806/0.867/0.770/0.773), per-candidate V(R) verdicts and κ(R|B), Gate-4 headroom tables, topic-level ICC 0.35, calibration→composed transfer (mean |Δ| 0.064, max **0.189**). They support no statement about any estimand.

DEVELOPMENT evidence behind v5 ([`reference_design_development.md`](../../dci1/reports/dci1v5/reference_design_development.md)): pre-screen→calibration median |Δι| = 0.0709 and **35.7 % of candidates move further than the whole 0.10 caliper**; straddling support 7→3, 5→0, 4→2, 4→0; RF11 0.635 solo → 0.969 composed; applying v5's validity stack to v4r4's measurements leaves 3/0/0/0 qualifying budget-class families and 4/4/2/3 production-class ones; the v5 rule on v4r4's library "turns two terminations into two survivals and one full design into one reduced design" (n = 4, retrospective).

## 9. v6 — registered 2026-08-26, all four terminal 2026-08-27 (REGISTERED; uncommitted)

Registration manifest `36f1fb3b…` at `c59fa75`, protocol hash `95db6df4…`, 27 §34 decisions closed (D23 `projection_sd`, D26 0.0142), A15's retired apparatus fault bound in the manifest. 516,240 rows.

| | e2b | e4b | qwen3-4b | instruct |
|---|---|---|---|---|
| REGIME_SCREEN | PASS, C1–C8 all True (1 rung dropped, A16) | PASS, all True | PASS, all True, 0 expansion | PASS but C1, C2, C4, C7, C8 **False**; `n_above: 0` → design-time REFERENCE_SUPPORT_NOT_IDENTIFIED |
| Gate 2 n*/m*/ι_A | 8 / 10 / 0.629 (`OPERATING_POINT_AT_GRID_BOUNDARY`) | 6 / 9 / 0.709 | 2 / 12 / 0.704 | 5 / 11 / 0.565 |
| Gate 2.75 | PASS on determinate entries (PS1 `STANDIN_UNPLACEABLE`, A17) | PASS (stand-ins flagged companion saturation, gate nothing) | **TERMINAL** `COMPOSED_HEADROOM_UNREACHABLE`: `pair:B+A` B 0.8906 → [0.779, 1.002] | **TERMINAL**: `pair:A+B` B 0.875 → [0.756, 0.994]; `pair:B+A` B 0.9245 → [0.825, 1.024] |
| Gate 3A calibrated-basis re-read | C4, C8 **False** (ι_A moved −0.079) → D6 NOT_IDENTIFIED, arms base+class | C4, C8 False → D6 | — | — |
| Gate 4 | PASS, `pair:B+CL` B 0.9375 (margin 0.0125) | **TERMINAL** `solo:CL` 0.9583 (CL = RF12:7), `pair:B+CL` CL slot **0.0417** | — | — |
| Terminal | `PREFREEZE_AUDIT_FAILURE`, 2 checks failed (`support_satisfied`, `protocol_hashes_agree`) | `COMPOSED_HEADROOM_FAILURE` | `COMPOSED_HEADROOM_UNREACHABLE` | `COMPOSED_HEADROOM_UNREACHABLE` |

Incidents ([`dci1/reports/dci1v6/incidents/`](../../dci1/reports/dci1v6/incidents/)): stage-1 CLI wrote a readiness verdict as a terminal report (A15); REGIME_SCREEN died on a rung with undefined ι (CR7:56 at chance ≥ 0.99; A16); the first composed probe raised on an unplaceable stand-in (PS1 ladder 0.0 at severities 1–6; A17). Reading: v6's repairs made pre-screen coverage pass on 3/4 (vs 1/4 in v5), but the calibrated re-read (V6-E04's A3) then failed C4 on both gemmas; the frozen-m* probe stopped both Qwens where v5's Gate 4 had cleared by 0.054; e4b's Gate 4 fired on the companion slot — the class the probe covers only through non-gating stand-ins.

## 10. Key findings, with evidence grade

| # | Finding | Grade | Where |
|---|---|---|---|
| 1 | Compositional delivery loss exists (L1) on qwen3-4b for D(A←B) in both orders (+0.39, +0.33) and on e4b position-dependently (+0.12 first; D(B←A) +0.28 second); verifier-defined; reduced design | REGISTERED | §7.6–7.7 |
| 2 | Which constraint pays is model- and position-dependent; Λ flips sign on e4b; no pooled scalar is licensed | REGISTERED (described, not estimated) | §7.7 |
| 3 | The companion-swap estimand Δ_R was never identified in any registered run; six quantities `NOT_IDENTIFIED` study-wide | REGISTERED (v4r4, v5, v6) | §1, §7.4, §8, §9 |
| 4 | Two mechanisms recur across three designs: reference support below ι_A collapses between pre-screen and calibration; composed headroom saturates on companion slots after m* is fixed on solo curves | REGISTERED outcomes + DEVELOPMENT diagnosis | §7.3–7.4, §8, §9; [03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §1 |
| 5 | Companion identity moves focal compliance by 0.05–0.10, class by 0.40–0.60, position by 0.29–0.35; single-order Δ_R flips sign | SCREEN | §5 |
| 6 | Screen-level "pair-specific" Δ (+0.34/+0.38) collapses to +0.095/+0.068 under the registered vacuity bound and to ≈0 at matched length | SCREEN + POST-HOC | §4 |
| 7 | Class contrast Δ_class ≈ 0 on qwen (A vs its structural twin) and −0.31/−0.51 on e4b (CL7:80 destroys B) | REGISTERED (F9 secondary) | §7.6 |
| 8 | v3's same-topic companion swap Δ^A = +0.064/+0.074 sits in the generic-load region and survives length matching | POST-HOC (v3 protocol) | §3 |
| 9 | Gate 4 at 24 topics falsely terminates an in-band replication with probability 0.12–0.19; the calibration→composed transfer reaches +0.189 | DEVELOPMENT (v6) | [`precision_design.json`](../../dci1/reports/dci1v6/precision_design.json) |
| 10 | Outcomes are verifier-defined; author-performed blind agreement 116/120 with the fail-class bound unmet; no version reached `human_validated` | REGISTERED basis + diagnostic | §6; [01](01_RESEARCH_QUESTION_AND_DESIGN.md) §8 |
