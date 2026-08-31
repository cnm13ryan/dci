# DCI-1 v7 — Tier-1 scientific-validity audit

**Scope.** Whether the evidence now in the repository supports the paper's
central claim — that companion instruction *A* ("use the word `however`
exactly *n* times") harms compliance with target *B* ("every word at most *m*
letters") more than difficulty-matched alternatives do — and what wording each
result will bear.

**Status of this document.** An audit of existing artifacts. It runs no model,
computes no new estimate, and changes no protocol value. Every number is read
from a signature-verified stage record or from the derived tables in
`dci1/reports/dci1v7/dossier/`, whose block-level reconstruction is checked
against the record it must reproduce (`dci1/tools/v7_dossier.py:596-611`;
re-run 2026-08-30, all six lanes `verified`).

---

## 0. The evidence basis, stated once

**The registered v7 study produced no confirmatory data.** Every model tree
under `dci1/evidence/dci1v7/` stops at `GATE_4_COMPOSED_CONTRAST`; there is no
`GATE_5_FREEZE`, no `CONFIRMATORY_GENERATION`, no analysis and no final report
for any of the four models. All four replications ended
`PREFREEZE_AUDIT_FAILURE` on `support_satisfied`
(`dci1/reports/dci1v7/CLOSURE.md`).

**Everything quantitative below comes from six development-rehearsal lanes** in
the structurally separate `dci1v7-development` namespace, which the protocol's
own guards refuse to admit as study evidence. Each lane carries
`evidence_status = DEVELOPMENT_REHEARSAL_not_a_v7_replication`
(`dci1/reports/dci1v7/dossier/lanes.csv`). Four are canonical, one per model;
two are repeat lanes of the same model on later commits, held as
reproducibility evidence and never as a second replication.

| model | lane (canonical) | n\* | m\* | arms admitted | confirmatory rows | §26 |
|---|---|---:|---:|---|---:|---|
| qwen3-4b | `dci1v7-development-r3` | 2 | 12 | base + core | 79,872 | MET |
| qwen3-4b-instruct-2507 | `dci1v7-development-r4` | 5 | 11 | base + core | 79,872 | MET |
| gemma-3n-e2b-it | `dci1v7-development-r5` | 8 | 10 | base + core + class | 89,088 | MET |
| gemma-3n-e4b-it | `dci1v7-development-r4` | 6 | 9 | base + core + class | 89,088 | MET |

Design per lane: 384 blocks (topics) × 8 draws, both prompt orders, block
bootstrap of 10,000 resamples, studentised maximum-modulus simultaneous 95%
intervals, no p-values.

**Direction convention, verified against the implementation.**
`D(c←g) = P(c passes alone) − P(c passes composed with g)` — a *loss*, positive
= harm (`dci1/src/dci1v7/protocol/manifest.py:774`;
`dci1/src/dci1v7/analysis/estimators.py:76-82`). The primary contrast is
`Δ_R = D(B←A) − mean_j D(B←R_j)` (`manifest.py:776`), which is algebraically
the paper's `(1/3)Σ_j c(B|B+R_j) − c(B|B+A)` because the solo baseline cancels.
I verified the cancellation numerically from the reconstructed block table:
the two forms agree to `0.00e+00` in all four canonical lanes × both positions.
**Positive Δ_R = A more harmful than the references, as the paper states.**

---

## 1. Claim-to-evidence map

All rows below are `evidence_status = DEV_REHEARSAL_*` and `scope =`
*this model, this operating point (n\*, m\*), this position, the registered
384-topic confirmatory bank, temperature 0.7 / top-p 0.9 / top-k 50, verifier
`1ffd4044…`*. Scope is therefore omitted from the table and stated once here.
Source for every row: `dci1/reports/dci1v7/dossier/estimands_master.csv`, which
carries the originating `source_artifact` and `stage_record_hash` per row.

| estimand | model | position | estimate | simultaneous 95% CI | half-width | threshold | strongest wording supported |
|---|---|---|---:|---|---:|---|---|
| Delta_R | qwen3-4b | B first | -0.0030 | [-0.0244, +0.0184] | 0.0214 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions |
| Delta_R | qwen3-4b | B second | +0.0126 | [-0.0140, +0.0392] | 0.0266 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions |
| Delta_R | qwen3-4b-instruct-2507 | B first | +0.0063 | [-0.0150, +0.0275] | 0.0212 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions |
| Delta_R | qwen3-4b-instruct-2507 | B second | -0.0034 | [-0.0299, +0.0232] | 0.0266 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions |
| Delta_R | gemma-3n-e2b-it | B first | -0.0320 | [-0.0587, -0.0053] | 0.0267 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions (and A is *less* harmful, CI excludes 0) |
| Delta_R | gemma-3n-e2b-it | B second | -0.0852 | [-0.1189, -0.0515] | 0.0337 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions (and A is *less* harmful, CI excludes 0) |
| Delta_R | gemma-3n-e4b-it | B first | -0.0268 | [-0.0555, +0.0019] | 0.0287 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions |
| Delta_R | gemma-3n-e4b-it | B second | -0.0726 | [-0.1034, -0.0418] | 0.0308 | dir @0; L3a >0.10; L3b >0.25; L3c upper <0.10 | L3c, scope `same_form_only`: no excess ≥0.10 vs same-form companions (and A is *less* harmful, CI excludes 0) |
| D(B<-A) | qwen3-4b | B first | -0.1234 | [-0.1567, -0.0900] | 0.0333 | dir @0; SESOI 0.10 | negative, excludes 0 |
| D(B<-A) | qwen3-4b | B second | -0.0195 | [-0.0531, +0.0140] | 0.0335 | dir @0; SESOI 0.10 | equivalence: \|effect\| < 0.10 |
| D(B<-A) | qwen3-4b-instruct-2507 | B first | -0.1315 | [-0.1683, -0.0947] | 0.0368 | dir @0; SESOI 0.10 | negative, excludes 0 |
| D(B<-A) | qwen3-4b-instruct-2507 | B second | -0.1074 | [-0.1448, -0.0701] | 0.0374 | dir @0; SESOI 0.10 | negative, excludes 0 |
| D(B<-A) | gemma-3n-e2b-it | B first | -0.0231 | [-0.0534, +0.0072] | 0.0303 | dir @0; SESOI 0.10 | equivalence: \|effect\| < 0.10 |
| D(B<-A) | gemma-3n-e2b-it | B second | +0.2106 | [+0.1716, +0.2496] | 0.0390 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(B<-A) | gemma-3n-e4b-it | B first | +0.0355 | [+0.0004, +0.0705] | 0.0351 | dir @0; SESOI 0.10 | positive, excludes 0 |
| D(B<-A) | gemma-3n-e4b-it | B second | +0.3916 | [+0.3485, +0.4347] | 0.0431 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | qwen3-4b | B first | +0.3955 | [+0.3519, +0.4391] | 0.0436 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | qwen3-4b | B second | +0.3210 | [+0.2710, +0.3709] | 0.0499 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | qwen3-4b-instruct-2507 | B first | -0.0081 | [-0.0507, +0.0344] | 0.0425 | dir @0; SESOI 0.10 | equivalence: \|effect\| < 0.10 |
| D(A<-B) | qwen3-4b-instruct-2507 | B second | -0.0329 | [-0.0943, +0.0286] | 0.0614 | dir @0; SESOI 0.10 | equivalence: \|effect\| < 0.10 |
| D(A<-B) | gemma-3n-e2b-it | B first | +0.2783 | [+0.2404, +0.3163] | 0.0380 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | gemma-3n-e2b-it | B second | +0.2653 | [+0.2245, +0.3061] | 0.0408 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | gemma-3n-e4b-it | B first | +0.2139 | [+0.1751, +0.2526] | 0.0387 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| D(A<-B) | gemma-3n-e4b-it | B second | +0.1702 | [+0.1279, +0.2126] | 0.0424 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| Lambda | qwen3-4b | B first | -0.5189 | [-0.5765, -0.4613] | 0.0576 | dir @0; SESOI 0.10 | negative, excludes 0, beyond SESOI |
| Lambda | qwen3-4b | B second | -0.3405 | [-0.4036, -0.2774] | 0.0631 | dir @0; SESOI 0.10 | negative, excludes 0, beyond SESOI |
| Lambda | qwen3-4b-instruct-2507 | B first | -0.1234 | [-0.1758, -0.0710] | 0.0524 | dir @0; SESOI 0.10 | negative, excludes 0 |
| Lambda | qwen3-4b-instruct-2507 | B second | -0.0745 | [-0.1418, -0.0073] | 0.0672 | dir @0; SESOI 0.10 | negative, excludes 0 |
| Lambda | gemma-3n-e2b-it | B first | -0.3014 | [-0.3532, -0.2497] | 0.0517 | dir @0; SESOI 0.10 | negative, excludes 0, beyond SESOI |
| Lambda | gemma-3n-e2b-it | B second | -0.0547 | [-0.1143, +0.0049] | 0.0596 | dir @0; SESOI 0.10 | unresolved at achieved precision |
| Lambda | gemma-3n-e4b-it | B first | -0.1784 | [-0.2305, -0.1263] | 0.0521 | dir @0; SESOI 0.10 | negative, excludes 0, beyond SESOI |
| Lambda | gemma-3n-e4b-it | B second | +0.2214 | [+0.1597, +0.2830] | 0.0616 | dir @0; SESOI 0.10 | positive, excludes 0, beyond SESOI |
| Xi | qwen3-4b | B first | +0.1697 | [+0.1367, +0.2027] | 0.0330 | direction @0 only | positive, excludes 0, beyond SESOI |
| Xi | qwen3-4b | B second | +0.1070 | [+0.0685, +0.1456] | 0.0385 | direction @0 only | positive, excludes 0 |
| Xi | qwen3-4b-instruct-2507 | B first | -0.0711 | [-0.0996, -0.0426] | 0.0285 | direction @0 only | negative, excludes 0 |
| Xi | qwen3-4b-instruct-2507 | B second | -0.1429 | [-0.1802, -0.1056] | 0.0373 | direction @0 only | negative, excludes 0, beyond SESOI |
| Xi | gemma-3n-e2b-it | B first | +0.2330 | [+0.1953, +0.2707] | 0.0377 | direction @0 only | positive, excludes 0, beyond SESOI |
| Xi | gemma-3n-e2b-it | B second | +0.0065 | [-0.0361, +0.0490] | 0.0425 | direction @0 only | equivalence: \|effect\| < 0.10 |
| Xi | gemma-3n-e4b-it | B first | +0.0020 | [-0.0313, +0.0352] | 0.0333 | direction @0 only | equivalence: \|effect\| < 0.10 |
| Xi | gemma-3n-e4b-it | B second | -0.0056 | [-0.0406, +0.0293] | 0.0350 | direction @0 only | equivalence: \|effect\| < 0.10 |
| Delta_1 | qwen3-4b | B first | +0.0085 | [-0.0204, +0.0374] | 0.0289 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_1 | qwen3-4b | B second | +0.0413 | [+0.0087, +0.0740] | 0.0326 | dir @0 | positive, excludes 0 |
| Delta_1 | qwen3-4b-instruct-2507 | B first | -0.0273 | [-0.0540, -0.0006] | 0.0267 | dir @0 | negative, excludes 0 |
| Delta_1 | qwen3-4b-instruct-2507 | B second | -0.0208 | [-0.0510, +0.0093] | 0.0302 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_1 | gemma-3n-e2b-it | B first | -0.0566 | [-0.0894, -0.0238] | 0.0328 | dir @0 | negative, excludes 0 |
| Delta_1 | gemma-3n-e2b-it | B second | -0.1019 | [-0.1426, -0.0612] | 0.0407 | dir @0 | negative, excludes 0 |
| Delta_1 | gemma-3n-e4b-it | B first | +0.0137 | [-0.0179, +0.0452] | 0.0316 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_1 | gemma-3n-e4b-it | B second | -0.0221 | [-0.0586, +0.0143] | 0.0364 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_2 | qwen3-4b | B first | +0.0033 | [-0.0197, +0.0262] | 0.0229 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_2 | qwen3-4b | B second | -0.0029 | [-0.0332, +0.0273] | 0.0303 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_2 | qwen3-4b-instruct-2507 | B first | +0.0355 | [+0.0130, +0.0580] | 0.0225 | dir @0 | positive, excludes 0 |
| Delta_2 | qwen3-4b-instruct-2507 | B second | +0.0254 | [-0.0029, +0.0537] | 0.0283 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_2 | gemma-3n-e2b-it | B first | -0.0404 | [-0.0739, -0.0068] | 0.0335 | dir @0 | negative, excludes 0 |
| Delta_2 | gemma-3n-e2b-it | B second | -0.1175 | [-0.1574, -0.0776] | 0.0399 | dir @0 | negative, excludes 0 |
| Delta_2 | gemma-3n-e4b-it | B first | -0.0046 | [-0.0389, +0.0298] | 0.0344 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_2 | gemma-3n-e4b-it | B second | -0.0824 | [-0.1201, -0.0446] | 0.0377 | dir @0 | negative, excludes 0 |
| Delta_3 | qwen3-4b | B first | -0.0208 | [-0.0488, +0.0072] | 0.0280 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | qwen3-4b | B second | -0.0007 | [-0.0366, +0.0353] | 0.0359 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | qwen3-4b-instruct-2507 | B first | +0.0107 | [-0.0164, +0.0379] | 0.0272 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | qwen3-4b-instruct-2507 | B second | -0.0146 | [-0.0489, +0.0196] | 0.0342 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | gemma-3n-e2b-it | B first | +0.0010 | [-0.0269, +0.0288] | 0.0279 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | gemma-3n-e2b-it | B second | -0.0361 | [-0.0731, +0.0008] | 0.0369 | dir @0 | equivalence: \|effect\| < 0.10 |
| Delta_3 | gemma-3n-e4b-it | B first | -0.0895 | [-0.1260, -0.0531] | 0.0365 | dir @0 | negative, excludes 0 |
| Delta_3 | gemma-3n-e4b-it | B second | -0.1133 | [-0.1488, -0.0778] | 0.0355 | dir @0 | negative, excludes 0 |
| Delta^A | qwen3-4b | B first | +0.1875 | [+0.1463, +0.2287] | 0.0412 | dir @0 | positive, excludes 0, beyond SESOI |
| Delta^A | qwen3-4b | B second | +0.4128 | [+0.3652, +0.4604] | 0.0476 | dir @0 | positive, excludes 0, beyond SESOI |
| Delta^A | qwen3-4b-instruct-2507 | B first | -0.3543 | [-0.3911, -0.3174] | 0.0368 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta^A | qwen3-4b-instruct-2507 | B second | -0.3523 | [-0.3936, -0.3111] | 0.0412 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta^A | gemma-3n-e2b-it | B first | -0.1959 | [-0.2251, -0.1667] | 0.0292 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta^A | gemma-3n-e2b-it | B second | -0.2171 | [-0.2483, -0.1860] | 0.0311 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta^A | gemma-3n-e4b-it | B first | -0.2499 | [-0.2849, -0.2149] | 0.0350 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta^A | gemma-3n-e4b-it | B second | -0.2595 | [-0.2992, -0.2199] | 0.0396 | dir @0 | negative, excludes 0, beyond SESOI |
| Delta_broad | qwen3-4b | B first | — | — | — | direction @0 only | **no claim — CLASS_ARM_NOT_AVAILABLE** |
| Delta_broad | qwen3-4b | B second | — | — | — | direction @0 only | **no claim — CLASS_ARM_NOT_AVAILABLE** |
| Delta_broad | qwen3-4b-instruct-2507 | B first | — | — | — | direction @0 only | **no claim — CLASS_ARM_NOT_AVAILABLE** |
| Delta_broad | qwen3-4b-instruct-2507 | B second | — | — | — | direction @0 only | **no claim — CLASS_ARM_NOT_AVAILABLE** |
| Delta_broad | gemma-3n-e2b-it | B first | +0.0254 | [+0.0003, +0.0505] | 0.0251 | direction @0 only | positive, excludes 0 |
| Delta_broad | gemma-3n-e2b-it | B second | +0.2074 | [+0.1734, +0.2413] | 0.0339 | direction @0 only | positive, excludes 0, beyond SESOI |
| Delta_broad | gemma-3n-e4b-it | B first | +0.0986 | [+0.0685, +0.1288] | 0.0301 | direction @0 only | positive, excludes 0 |
| Delta_broad | gemma-3n-e4b-it | B second | +0.3161 | [+0.2783, +0.3538] | 0.0378 | direction @0 only | positive, excludes 0, beyond SESOI |
| Delta_near | qwen3-4b | B first | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | qwen3-4b | B second | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | qwen3-4b-instruct-2507 | B first | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | qwen3-4b-instruct-2507 | B second | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | gemma-3n-e2b-it | B first | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | gemma-3n-e2b-it | B second | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | gemma-3n-e4b-it | B first | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| Delta_near | gemma-3n-e4b-it | B second | — | — | — | dir @0; 0.10 | **no claim — NEAR_FORM_ARM_NOT_AVAILABLE** |
| delta_difficulty | qwen3-4b | B first | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | qwen3-4b | B second | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | qwen3-4b-instruct-2507 | B first | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | qwen3-4b-instruct-2507 | B second | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | gemma-3n-e2b-it | B first | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | gemma-3n-e2b-it | B second | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | gemma-3n-e4b-it | B first | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |
| delta_difficulty | gemma-3n-e4b-it | B second | — | — | — | dir @0; equiv ±0.10 | **no claim — DIFFICULTY_SUPPORT_NOT_IDENTIFIED** |

### 1.1 The headline contrast, read plainly

**Δ_R is never positive at any threshold, in any model, in either position.**
Its point estimate is negative in five of eight model × position cells, and the
simultaneous interval **excludes zero on the negative side** in three of them —
both Gemma positions for E2B and B-second for E4B. The registered claim rule
returns L3c in all eight cells (`dci1/src/dci1v7/analysis/claims.py:283-320`).

The hypothesis the study was built to test — that A is a *specifically*
harmful companion — is not supported anywhere. In the two Gemma models the
data support the **opposite** direction: the record's own reading field is
`"direction": "A_COMPARATIVELY_BETTER"`, *"the comparison companions cost B
more than A does"*
(`dci1/evidence/dci1v7-development-r5/evidence/dci1v7/gemma-3n-e2b-it/UNMASKED_ANALYSIS/unmasked_result.json`).

### 1.2 The raw compositional effects, and what they are effects *on*

Composition moves compliance a great deal — but the movement is concentrated on
**A**, not on B, and its sign is not consistent across models.

One composed generation serves both configurations: a configuration is *the
position of the outcome*, so the constraint stated first supplies
`outcome_first` and the other supplies `outcome_second`
(`dci1/src/dci1v7/design/cells.py:175-177`). The within-prompt pair is
therefore *cross*-configuration. Reading it that way (change in compliance vs
solo; **+ = composition improved that constraint**):

| model | prompt `B then A`: ΔB | ΔA | sum | prompt `A then B`: ΔB | ΔA | sum |
|---|---:|---:|---:|---:|---:|---:|
| qwen3-4b | **+0.1234** | −0.3210 | −0.1976 | +0.0195 | −0.3955 | −0.3760 |
| qwen3-4b-instruct-2507 | **+0.1315** | **+0.0329** | **+0.1644** | **+0.1074** | **+0.0081** | **+0.1156** |
| gemma-3n-e2b-it | +0.0231 | −0.2653 | −0.2422 | −0.2106 | −0.2783 | −0.4889 |
| gemma-3n-e4b-it | −0.0355 | −0.1702 | −0.2057 | −0.3916 | −0.2139 | −0.6055 |

Derived from `dossier/cell_compliance.csv`. Three readings follow, and they are
different readings:

- **qwen3-4b** shows a genuine trade-off in both orders: B improves, A collapses.
- **qwen3-4b-instruct-2507** shows **both constraints improving** in both orders.
  Composition is not costly for this model at its operating point at all. This
  is a direct counterexample to a competing-demands account.
- **The two Gemmas** mostly show **joint degradation**: in three of their four
  prompt conditions both constraints lose. That is not redistribution.

So "large raw compositional effects" is supportable; "large *and* directional
in a way that indicates redistribution" is supportable for **one model of
four**.

### 1.3 Asymmetry — what Λ does and does not measure

`Λ = D(B←A) − D(A←B)` within one configuration
(`dci1/src/dci1v7/analysis/estimators.py:95-99`). Its two terms are read from
**different cells and therefore different prompts** — the protocol says so
explicitly, and enforces it: *"`D(A<-B)|outcome_first` and
`D(B<-A)|outcome_first` are read from DIFFERENT cells and a statement that does
not say which is not checkable"* (`dci1/src/dci1v7/analysis/claims.py:144-148`,
`:735-739`).

Λ excludes zero in 7 of 8 cells (all but gemma-3n-e2b-it, B second:
−0.0547 [−0.1143, +0.0049]). It is therefore strong evidence that **the two
constraints are not symmetrically affected**. It is *not* evidence of a
within-prompt trade-off, because it differences two prompts. The within-prompt
table in §1.2 is the quantity that speaks to redistribution, and it is not what
Λ estimates.

Λ also reverses sign across models: −0.52/−0.34 (qwen3-4b) against +0.22
(gemma-3n-e4b-it, B second). "Which constraint pays" is model-dependent and, on
E4B, position-dependent.

### 1.3b Δ^A — the mirror estimand, and why it is not the counter-evidence it looks like

`Δ^A = D(A←B) − mean_j D(A←R_j)`, *"a gated diagnostic (§11.5)"*
(`dci1/src/dci1v7/analysis/estimators.py:204-211`). It asks of A what Δ_R asks
of B: does the companion's identity matter?

It is large and excludes zero in **8/8** cells — +0.188 and +0.413 (qwen3-4b),
−0.354 and −0.352 (2507), −0.196 and −0.217 (E2B), −0.250 and −0.260 (E4B).
Every one exceeds the SESOI. Read naively this says "companion identity matters
enormously" and appears to contradict Δ_R ≈ 0.

It does not, and the paper must not use it that way, for two reasons:

1. **B is not a matched reference.** Δ_R compares A against companions selected
   to sit within 0.10 of A on the difficulty coordinate. Δ^A compares **B** — a
   word-length budget, a different constraint class, never difficulty-matched to
   the markers — against those same markers. A large Δ^A is close to what the
   design guarantees; it measures "an unmatched companion behaves differently
   from matched ones", not companion-specificity in the study's sense.
2. **F3 is secondary tier.** Δ^A licenses no claim level:
   `PRIMARY_TIER_FAMILIES = ("F1", "F11")`
   (`dci1/src/dci1v7/protocol/constants.py:446`), and Δ^A sits in F3
   (`constants.py:414`). Its rows carry no `claim_level` on any lane.

Report it as a diagnostic that the apparatus can detect companion-identity
differences of this size when they exist — which is a useful sensitivity
statement about the design, and is *not* a finding about A.

### 1.4 Claims supported across **all** tested configurations

1. **No pair-specific excess at the registered threshold.** Δ_R's upper
   simultaneous bound is below +0.10 in 8/8 cells — indeed below +0.05 in 8/8.
   Registered wording: L3c at scope `same_form_only` (see §2).
2. **Δ_R is small in absolute terms.** |Δ_R| ≤ 0.0852 everywhere; the realised
   half-width (0.021–0.034) met the 0.05 precondition in 8/8 cells, so this is
   a measured smallness, not an underpowered one.
3. **Composition moves at least one instruction's compliance by more than the
   SESOI**, in every model × position: in 8/8 cells at least one of `D(B←A)`,
   `D(A←B)` has |estimate| > 0.10 with a simultaneous interval excluding zero.
   The *direction* varies — for both Qwen models `D(B←A)` is **negative**, i.e.
   B improves.
4. **Reference-order position matters.** `Ord_B` and `Ord_Λ` exclude zero in
   3 of 4 models; `Ord_Rbar` excludes zero in 4 of 4.
5. **Reproducibility of the pipeline.** Repeat lanes reproduce Δ_R to within
   0.002 (qwen3-4b) and 0.014 (E2B) — inside the half-widths
   (`dossier/figA1_repeat_lane_agreement.csv`).

### 1.5 Claims supported only in **some** models or positions

| claim | where it holds | where it fails |
|---|---|---|
| A is *less* harmful than matched references (Δ_R < 0, CI excludes 0) | E2B both positions; E4B B-second | qwen3-4b and 2507 (CI spans 0), E4B B-first (upper +0.0019) |
| B loses under composition (`D(B←A)` > 0, CI excludes 0) | E2B B-second (+0.211); E4B B-second (+0.392), E4B B-first (+0.036, lower +0.0004) | qwen3-4b and 2507 — `D(B←A)` is **negative**, i.e. B *improves* |
| A loses under composition (`D(A←B)` > 0) | qwen3-4b, E2B, E4B (all positions) | 2507: −0.008 and −0.033, both CIs span 0 |
| Redistribution (one gains, one loses, same prompt) | qwen3-4b both orders; E2B `B then A` | 2507 (both gain); E4B (both lose) |
| Λ ≠ 0 | 7 of 8 cells | E2B B-second |
| Δ_broad > 0 | E2B and E4B (class arm admitted) | **not estimable** for qwen3-4b and 2507 |

### 1.6 Unavailable or unidentified analyses — *not* null results

These are recorded as `NOT_IDENTIFIED` with a reason. The protocol is explicit
that this "is not a null" and that no later stage converts it into one
(`user-notes/DCI1_preregistration_v7.md:610`). Counts from
`dossier/not_identified.csv` (345 rows):

| analysis | status | lanes affected | what it would have decided |
|---|---|---|---|
| `Δ_near` and `D(B←N_k)` | `NEAR_FORM_ARM_NOT_AVAILABLE` | **all 4 models, both positions** | whether Δ_R ≈ 0 is a property of A or of the *same-form* control design |
| `δ_difficulty`, `β`, `α_1..3`, `γ_tier`, `D(B←R_j±)` | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | **all 4 models** | whether A's loss is what its difficulty alone predicts |
| `Δ_broad`, `D(B←CL)`, `Ord_CL` | `CLASS_ARM_NOT_AVAILABLE` | qwen3-4b, 2507 | bound on how much companion *class* could matter |
| Human-judged compliance | `HUMAN_VALIDATION_UNAVAILABLE`; basis is `deterministic_measurement_validated` | all | whether verifier verdicts track human judgement |

**The near-form arm is the consequential one.** It is the arm the red team's R1
asks for, and the study's own code says why: *"if the mechanism by which A
damages B is a property of the form, every Tier-1 control reproduces it and
Δ_R goes to zero for a reason that belongs to the design rather than to A"*
(`dci1/src/dci1v7/analysis/claims.py:414-418`). Δ_R ≈ 0 with no near-form arm
cannot distinguish "A is not special" from "the controls were built to be too
much like A". Nothing in the current evidence resolves that.

### 1.7 Claims that must be weakened or dropped

| as currently framed | verdict | replacement |
|---|---|---|
| "A specifically harms B more than comparable companions" | **drop** — the data point the other way in 2 of 4 models | "no pair-specific excess was detected; in two models the matched companions cost B *more* than A did" |
| "The pairwise framing is refuted" (the memo's verdict) | **drop** — requires the near-form arm, which no lane had | the registered `same_form_only` sentence, verbatim |
| "Raw compositional effects are large, indicating redistribution" | **weaken** | "large, but concentrated on A; consistent with redistribution in qwen3-4b only, and contradicted in 2507 where both constraints improve" |
| "Δ_R is small, so composition is benign" | **weaken** | "Δ_R is small; the *absolute* losses are not — `D(A←B)` reaches +0.40" |
| "Δ_broad shows companion class matters" | **drop** | the class control is not difficulty-matched on the confirmatory topics (§3.5); the design's own sentence calls it a bound, not an estimate |
| Any claim quantified as a confirmatory result | **drop** | development-rehearsal evidence; the registered study has no confirmatory rows |

> **A framing trap worth naming.** Every lane records `§26 = MET`. §26 is the
> *methodological* success criterion — "the counterfactual Δ_R requires is
> identified and can carry a nonzero value" — and the implementation states in
> terms that **"It is not the scientific effect claim"**
> (`dci1/src/dci1v7/stages/support.py:231-254`). A paper that reports "the
> registered success criterion was met" without that sentence will be read as
> claiming the hypothesis succeeded. (I checked the apparent conflict with
> amendment A8's "§26 records `NOT_MET` on such a replication",
> `user-notes/DCI1_preregistration_v7.md:605-615`: A8 refers to
> `REFERENCE_SUPPORT_NOT_IDENTIFIED`, which breaks core support; the lanes
> failed only `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, which drops the spectrum arm
> and L3d/L3e. `MET` is correct. No code/preregistration discrepancy here.)

---

## 2. The +0.10 threshold

### 2.1 Where it came from

The threshold traces to a single line in a pre-study construct memo:

> `user-notes/dci-construct-pass2.md:415`, §G row 1, dated **14 August 2026**:
> *"D(B←A) − D(B←R) > 0.25 supports H1 and licenses a pairwise construct.
> **< 0.10 supports H2 and refutes the pairwise framing entirely**, redirecting
> the programme to a load-and-capacity account."*

Both numbers are **asserted in that memo, not derived**. There is no power
calculation, no cost model, no elicitation and no external source attached to
either value at its point of origin. The v4r3 changelog is candid about this:
*"The 0.10 and 0.25 thresholds are quoted verbatim from `dci-construct-pass2.md`
§G row 1 … and **their provenance is the protection they carry**"*
(`user-notes/DCI1_v4r2_to_v4r3_changelog.md:492-496`).

### 2.2 Was it fixed before the relevant outcomes?

**Yes, unambiguously, and by a wide margin.**

- Memo: 14 Aug 2026. First code constant: commit `85fe950` (17 Aug 2026,
  `dci1/src/dci1/protocol/constants.py:72`). Carried unchanged through v4,
  v4r3, v4r4, v5, v6 into `dci1/src/dci1v7/protocol/constants.py:372-375`.
- The v7 development rehearsals ran **28–30 Aug 2026**.
- The threshold is *upstream of the design*: the confirmatory topic count was
  chosen from it. *"Reaching a simultaneous detectable effect of 0.10 requires
  roughly 320 to 470 topics … and 384 sits inside that range"*
  (`user-notes/DCI-1_preregistration_v2.md:375`; planning quantities at `:355`).

This is genuine preregistration. It also means the design cannot independently
corroborate the threshold — the sample size was derived *from* it.

### 2.3 Its stated rationale

One rationale exists, and it is practical, not empirical:

> *"The smallest effect of interest is a risk difference of 0.10. A change of
> that size converts a system prompt with 80% target compliance into one with
> 70% target compliance, which is one additional failure in every ten
> responses."* — `user-notes/DCI-1_preregistration_v2.md:316` (repeated at
> `:747`).

That is a statement about the *interpretability of the compliance scale*. It is
a defensible reason to care about a 10-point move. It is **not** a derivation of
0.10 as the boundary between "pairwise construct licensed" and "pairwise
framing refuted" — which is the job §G row 1 gives it.

**For 0.25 I found no stated rationale anywhere in the repository.** The v4r3
changelog transfers 0.10 to `δ_difficulty` on the strength of the
compliance-scale argument and explicitly **refuses to transfer 0.25**, on the
ground that doing so would be *"inventing a threshold and dressing it in
someone else's provenance"* (`DCI1_v4r2_to_v4r3_changelog.md:497-500`). The
same objection applies to 0.25 wherever it is used; it is simply never made
about 0.25's own origin.

### 2.4 Were alternatives considered?

Alternatives to the *scope* of the thresholds were considered and recorded;
alternatives to the *values* were not.

| decision | question | outcome |
|---|---|---|
| **D12** (`dci1/src/dci1v7/protocol/decisions.py:255-262`) | does `δ_difficulty` or an order contrast get its own magnitude threshold? | no — direction and SESOI only; 0.25 not transferred |
| **D15** (`:279-287`) | do the memo's 0.10 and 0.25 apply to a **same-form** Δ_R? | *"Both transfer, on the ground that the memo defined them for the shape of the contrast. **Recorded as contestable**"*, `redteam="R2"`; unimplemented alternatives `neither_transfers`, `generic_only` |
| **D18** (`constants.py:484-503`) | is the near-form arm a precondition of the *strong* L3c? | closed at `precondition` |

D15 is the load-bearing one and the protocol itself flags it as contestable.
The memo's contrast was `D(B←A) − D(B←R)` with an unspecified R; v7's R is a
pool deliberately built to resemble A. Whether a threshold calibrated for a
generic companion still marks the same scientific boundary for a
maximally-similar one is exactly the open question, and the repository records
it as open rather than settled.

### 2.5 What "upper simultaneous CI < +0.10" actually licenses

Two different statements, and the study has evidence for only the weaker one.

`L3C_SCOPES = ("strong", "same_form_only")` (`constants.py:489`). The **strong**
scope is the memo's refutation verdict and **requires the near-form arm**;
§34 D18 is closed at `precondition`, and the docstring is explicit that the
researcher *"took the strong version"* precisely because *"v5's core pool is
chosen to resemble A closely enough that Δ_R ≈ 0 is a plausible consequence of
the **design**"* (`dci1/src/dci1v7/analysis/claims.py:454-470`).

No lane had the near-form arm. Every L3c emitted therefore carries scope
`same_form_only` and these two sentences, verbatim from the signed records:

> **`l3c_scope_sentence`:** *"no excess relative to same-form exact-count
> companions; **this is not the refutation verdict**, which requires the
> near-form arm (§34 D18)"*
>
> **`near_form_absent_sentence`:** *"the local excess is below the generic-load
> threshold against companions that share A's predicate form, and **no
> companion of a different form was available to test whether the absence is a
> property of the form rather than of A**"*

So `upper < 0.10` licenses: *against three exact-count marker companions
matched to A on difficulty, A's extra cost to B is below 0.10.* It does **not**
license: *A is not a special companion*, *the pairwise framing is refuted*, or
*any composition is equally harmful.*

### 2.6 Descriptive sensitivity at nearby thresholds

Not a new analysis — the same eight intervals read against four other numbers,
reported because a reader will ask.

| model | position | Δ_R | sim. upper | <0.05 | <0.075 | <0.10 | <0.125 | <0.15 |
|---|---|---:|---:|:-:|:-:|:-:|:-:|:-:|
| qwen3-4b | B first | −0.0030 | +0.0184 | ✓ | ✓ | ✓ | ✓ | ✓ |
| qwen3-4b | B second | +0.0126 | +0.0392 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2507 | B first | +0.0063 | +0.0275 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2507 | B second | −0.0034 | +0.0232 | ✓ | ✓ | ✓ | ✓ | ✓ |
| E2B | B first | −0.0320 | −0.0053 | ✓ | ✓ | ✓ | ✓ | ✓ |
| E2B | B second | −0.0852 | −0.0515 | ✓ | ✓ | ✓ | ✓ | ✓ |
| E4B | B first | −0.0268 | +0.0019 | ✓ | ✓ | ✓ | ✓ | ✓ |
| E4B | B second | −0.0726 | −0.0418 | ✓ | ✓ | ✓ | ✓ | ✓ |

**The verdict is insensitive to the threshold over 0.05–0.15**: 8/8 cells clear
every one, because the largest upper bound anywhere is +0.0392. The threshold's
weak justification is therefore *not* what the L3c conclusion rests on — the
intervals are far inside it. What the threshold's provenance does undermine is
any claim phrased as *"below the preregistered boundary for a pairwise
construct, therefore the construct is refuted"*, and that claim is blocked
independently by §2.5.

---

## 3. Reference heterogeneity

### 3.1 Identity, per-reference losses, spread, leave-one-out

Every reference is an exact-count marker instruction ("use the word *X* exactly
*s* times") — Tier 1, `constraint_class = production`, identical to A on all
seven §7.4 identity fields. Sources: `dossier/references_selected.csv`,
`dossier/estimands_master.csv`, `dossier/cell_compliance.csv`.

| model | position | slot | instance (marker, severity) | ι_R | \|ι_R−ι_A\| | c(B\|B+R_j) | D(B←R_j) | Δ_j | Δ_j sim CI | Δ_R dropping this R |
|---|---|---|---|---:|---:|---:|---:|---:|---|---:|
| qwen3-4b | B first | R1 | MK1:6 (marker_thus) | 0.6849 | 0.0006 | 0.9095 | -0.1318 | +0.0085 | [-0.0204, +0.0374] | -0.0088 |
| qwen3-4b | B first | R2 | MK7:2 (marker_instead) | 0.6836 | 0.0019 | 0.9043 | -0.1266 | +0.0033 | [-0.0197, +0.0262] | -0.0062 |
| qwen3-4b | B first | R3 | MK6:8 (marker_namely) | 0.6732 | 0.0123 | 0.8802 | -0.1025 | -0.0208 | [-0.0488, +0.0072] | +0.0059 |
| qwen3-4b | B first | **all 3** | spread of Δ_j = 0.0293 | | | | mean D(B←R)= -0.1203 | **Δ_R = -0.0030** | [-0.0244, +0.0184] | LOO range -0.0088 … +0.0059 |
| qwen3-4b | B second | R1 | MK1:6 (marker_thus) | 0.6849 | 0.0006 | 0.8385 | -0.0609 | +0.0413 | [+0.0087, +0.0740] | -0.0018 |
| qwen3-4b | B second | R2 | MK7:2 (marker_instead) | 0.6836 | 0.0019 | 0.7943 | -0.0166 | -0.0029 | [-0.0332, +0.0273] | +0.0203 |
| qwen3-4b | B second | R3 | MK6:8 (marker_namely) | 0.6732 | 0.0123 | 0.7965 | -0.0189 | -0.0007 | [-0.0366, +0.0353] | +0.0192 |
| qwen3-4b | B second | **all 3** | spread of Δ_j = 0.0443 | | | | mean D(B←R)= -0.0321 | **Δ_R = +0.0126** | [-0.0140, +0.0392] | LOO range -0.0018 … +0.0203 |
| qwen3-4b-instruct-2507 | B first | R1 | MK4:5 (marker_whereas) | 0.5339 | 0.0059 | 0.8737 | -0.1042 | -0.0273 | [-0.0540, -0.0006] | +0.0231 |
| qwen3-4b-instruct-2507 | B first | R2 | MK3:3 (marker_though) | 0.5495 | 0.0097 | 0.9365 | -0.1670 | +0.0355 | [+0.0130, +0.0580] | -0.0083 |
| qwen3-4b-instruct-2507 | B first | R3 | MK8:4 (marker_overall) | 0.5560 | 0.0163 | 0.9118 | -0.1423 | +0.0107 | [-0.0164, +0.0379] | +0.0041 |
| qwen3-4b-instruct-2507 | B first | **all 3** | spread of Δ_j = 0.0628 | | | | mean D(B←R)= -0.1378 | **Δ_R = +0.0063** | [-0.0150, +0.0275] | LOO range -0.0083 … +0.0231 |
| qwen3-4b-instruct-2507 | B second | R1 | MK4:5 (marker_whereas) | 0.5339 | 0.0059 | 0.8561 | -0.0866 | -0.0208 | [-0.0510, +0.0093] | +0.0054 |
| qwen3-4b-instruct-2507 | B second | R2 | MK3:3 (marker_though) | 0.5495 | 0.0097 | 0.9023 | -0.1328 | +0.0254 | [-0.0029, +0.0537] | -0.0177 |
| qwen3-4b-instruct-2507 | B second | R3 | MK8:4 (marker_overall) | 0.5560 | 0.0163 | 0.8623 | -0.0928 | -0.0146 | [-0.0489, +0.0196] | +0.0023 |
| qwen3-4b-instruct-2507 | B second | **all 3** | spread of Δ_j = 0.0462 | | | | mean D(B←R)= -0.1041 | **Δ_R = -0.0034** | [-0.0299, +0.0232] | LOO range -0.0177 … +0.0054 |
| gemma-3n-e2b-it | B first | R1 | MK2:1 (marker_hence) | 0.5911 | 0.0020 | 0.7546 | +0.0335 | -0.0566 | [-0.0894, -0.0238] | -0.0197 |
| gemma-3n-e2b-it | B first | R2 | MK1:4 (marker_thus) | 0.5924 | 0.0033 | 0.7708 | +0.0173 | -0.0404 | [-0.0739, -0.0068] | -0.0278 |
| gemma-3n-e2b-it | B first | R3 | MK5:7 (marker_indeed) | 0.6133 | 0.0241 | 0.8122 | -0.0241 | +0.0010 | [-0.0269, +0.0288] | -0.0485 |
| gemma-3n-e2b-it | B first | **all 3** | spread of Δ_j = 0.0576 | | | | mean D(B←R)= +0.0089 | **Δ_R = -0.0320** | [-0.0587, -0.0053] | LOO range -0.0485 … -0.0197 |
| gemma-3n-e2b-it | B second | R1 | MK2:1 (marker_hence) | 0.5911 | 0.0020 | 0.4756 | +0.3125 | -0.1019 | [-0.1426, -0.0612] | -0.0768 |
| gemma-3n-e2b-it | B second | R2 | MK1:4 (marker_thus) | 0.5924 | 0.0033 | 0.4600 | +0.3281 | -0.1175 | [-0.1574, -0.0776] | -0.0690 |
| gemma-3n-e2b-it | B second | R3 | MK5:7 (marker_indeed) | 0.6133 | 0.0241 | 0.5413 | +0.2467 | -0.0361 | [-0.0731, +0.0008] | -0.1097 |
| gemma-3n-e2b-it | B second | **all 3** | spread of Δ_j = 0.0814 | | | | mean D(B←R)= +0.2958 | **Δ_R = -0.0852** | [-0.1189, -0.0515] | LOO range -0.1097 … -0.0690 |
| gemma-3n-e4b-it | B first | R1 | MK5:6 (marker_indeed) | 0.6940 | 0.0312 | 0.7230 | +0.0218 | +0.0137 | [-0.0179, +0.0452] | -0.0470 |
| gemma-3n-e4b-it | B first | R2 | MK4:7 (marker_whereas) | 0.7565 | 0.0313 | 0.7048 | +0.0400 | -0.0046 | [-0.0389, +0.0298] | -0.0379 |
| gemma-3n-e4b-it | B first | R3 | MK6:3 (marker_namely) | 0.6758 | 0.0495 | 0.6198 | +0.1250 | -0.0895 | [-0.1260, -0.0531] | +0.0046 |
| gemma-3n-e4b-it | B first | **all 3** | spread of Δ_j = 0.1032 | | | | mean D(B←R)= +0.0623 | **Δ_R = -0.0268** | [-0.0555, +0.0019] | LOO range -0.0470 … +0.0046 |
| gemma-3n-e4b-it | B second | R1 | MK5:6 (marker_indeed) | 0.6940 | 0.0312 | 0.3311 | +0.4137 | -0.0221 | [-0.0586, +0.0143] | -0.0978 |
| gemma-3n-e4b-it | B second | R2 | MK4:7 (marker_whereas) | 0.7565 | 0.0313 | 0.2708 | +0.4740 | -0.0824 | [-0.1201, -0.0446] | -0.0677 |
| gemma-3n-e4b-it | B second | R3 | MK6:3 (marker_namely) | 0.6758 | 0.0495 | 0.2399 | +0.5049 | -0.1133 | [-0.1488, -0.0778] | -0.0522 |
| gemma-3n-e4b-it | B second | **all 3** | spread of Δ_j = 0.0911 | | | | mean D(B←R)= +0.4642 | **Δ_R = -0.0726** | [-0.1034, -0.0418] | LOO range -0.0978 … -0.0522 |

### 3.2 Does one reference drive the average?

Yes, in half the cells — and in one it drives the *sign*.

- **gemma-3n-e4b-it, B first.** Δ_R = −0.0268 [−0.0555, +0.0019]. Δ_3
  (`MK6:3`, `marker_namely`) is −0.0895, while Δ_1 = +0.0137 and Δ_2 = −0.0046.
  Dropping R3 gives leave-one-out Δ_R = **+0.0046** — a sign reversal. One of
  three references carries the whole effect in that cell.
- **gemma-3n-e2b-it, B second.** Δ_R = −0.0852; dropping R3 (`MK5:7`) moves it
  to −0.1097, dropping R1 to −0.0768. Range across leave-one-out: 0.033.
- **qwen3-4b, B second.** Δ_R = +0.0126, but Δ_1 = +0.0413 (its own CI excludes
  zero) against Δ_2 = −0.0029 and Δ_3 = −0.0007. Dropping R1 gives −0.0018.
- **qwen3-4b-instruct-2507, B first.** Δ_1 = −0.0273 and Δ_2 = +0.0355 have
  **opposite signs and both CIs exclude zero.** The mean, +0.0063, describes
  neither.

Between-reference spread of Δ_j runs 0.029 to 0.103. It exceeds the Δ_R
half-width in **8 of 8** cells and exceeds |Δ_R| itself in **7 of 8** (the
exception is E2B B-second, spread 0.081 against |Δ_R| = 0.085). **The variation
among nominally matched references is generally bigger than the quantity the
study is trying to measure.**

### 3.3 Is the Δ_R interval conditional on these three references, or does it generalize over a reference population?

**Conditional. It carries no reference-sampling uncertainty whatsoever.**

Three independent confirmations:

1. **The estimator.** The block bootstrap resamples *topics* only:
   *"resampling blocks with replacement and carrying every cell mean of each
   drawn block. **Cells are never resampled**"*
   (`dci1/src/dci1v7/analysis/bootstrap.py:3-5`). R1, R2, R3 are fixed cells.
   Every replicate uses the same three references.
2. **The selection is not a random draw.** `admit_core_references` takes, per
   family, the instance with the **smallest |ι_R − ι_A|**, then breaks ties on
   structural tier, feature-group order and discourse role
   (`dci1/src/dci1v7/stages/selection.py:210-226`, `:152-157`). The three
   references are an extreme order statistic of the candidate pool — the three
   *closest possible* matches — not a sample from it.
3. **The protocol says so in the emitted statement.** Every L3c carries
   `reference_pool_sentence`: *"the core reference pool is same-form with A —
   an exact count of a marker word, differing only in which word and how many —
   so this excess is an excess relative to companions that share A's predicate
   form and **is not an excess relative to companions in general**."*

Consequently the reported Δ_R interval is the answer to *"how much would this
number move if I redrew 384 topics?"* and to nothing else. It is silent on
*"how much would it move if I redrew three references?"* — and §3.2 shows that
second source of variation is the larger one.

### 3.4 Two direct empirical measurements of reference-selection sensitivity

The rehearsals happen to contain the experiment that answers the question the
interval cannot.

**The E2B repeat lane selected different severities of the same three
families.** `dci1v7-development-r3` chose `MK2:7`, `MK1:1`, `MK5:8`;
`dci1v7-development-r5` chose `MK2:1`, `MK1:4`, `MK5:7`
(`dossier/references_selected.csv`). Δ_R moved from −0.0244 → −0.0320 (B first)
and −0.0712 → −0.0852 (B second): **0.008 and 0.014 from changing severities
within the same marker families**, comparable to a third of the half-width, on
the same model.

**Only 6–14% of candidates survive the two-split stability check.** Counting
directly from the Gate-3A records (`gate3a_reference_calibration.json`,
`stability` block):

| model | candidates checked | passed §13.7 stability | share |
|---|---:|---:|---:|
| qwen3-4b | 112 | 14 | 12% |
| qwen3-4b-instruct-2507 | 112 | 16 | 14% |
| gemma-3n-e2b-it | 112 | 16 | 14% |
| gemma-3n-e4b-it | 140 | 9 | **6%** |

So the "reference population" a generalizing interval would have to average
over is, empirically, 9–16 admissible instances per model — and it is
model-specific. No lane generated any second reference set, so **the study
contains no basis for a reference-random interval**, and one must not be
implied.

### 3.5 The severity-perturbed and class references

`D(B←R_j−)` and `D(B←R_j+)` — the six severity-perturbed companions that would
have measured within-family sensitivity directly — are `NOT_IDENTIFIED` on
**every lane** (`DIFFICULTY_SUPPORT_NOT_IDENTIFIED`,
`dossier/not_identified.csv`). They were never generated.

The broad-class control (CL, `RF12`, a budget constraint) was admitted on the
two Gemmas only, and the post-hoc check on the confirmatory topics shows it is
**not difficulty-matched there**
(`dossier/posthoc_confirmatory_difficulty.csv`):

| model | CL instance | ι on confirmatory topics | ι_A | gap | exceeds realised-gap qualifier (0.15)? |
|---|---|---:|---:|---:|:-:|
| gemma-3n-e2b-it | RF12:6 | +0.4056 | 0.6182 | 0.213 | **yes** |
| gemma-3n-e4b-it | RF12:7 | **−0.0926** | 0.7233 | **0.816** | **yes** |

On E4B the class control is satisfied by chance 80.7% of the time
(`kappa_confirmatory_unconstrained = 0.807`) and its instruction lift is
*negative* (−0.018). `Δ_broad` on E4B (+0.099, +0.316) is a contrast against a
degenerate companion.

`CHANGES_SCIENTIFIC.md` (entry 2026-08-30) draws the consequence explicitly, and
it is sharper than "not matched": **§13.10's matching caliper is 0.15, so all
three class-arm lanes would have recorded `CLASS_ARM_NOT_MATCHED` and none
did**; and on E4B the companion's solo compliance (0.789) sits *below* its own
chance rate (0.807), so against §13.4's `V_head` lift floor of +0.20 that
severity **would have been rejected before selection** under a correct chance
column, and the class arm dropped or filled differently.

The core references, by contrast, hold up out of sample: their realised
confirmatory gaps are 0.004–0.086 across the canonical lanes (0.004–0.090 across
all six), all inside the 0.10 admission caliper and the 0.15 qualifier, and
every Tier-1 marker family has κ_c = 0.000 on the confirmatory blocks — so for
the core pool raw solo compliance *is* the correct ι(R) and Δ_R's matching is
sound.

### 3.6 A ceiling effect that partly manufactures the L3c verdict

§13.14 registers that a contrast whose negative arm sits above `1 − SESOI = 0.90`
**cannot be positive by a SESOI, by arithmetic**
(`dci1/src/dci1v7/protocol/constants.py:386-391`). Two cells are in that
regime, and the record names them:

| model | position | c(B\|B+A) | mean c(B\|B+R) | max attainable Δ_R | positive direction compressed? |
|---|---|---:|---:|---:|---|
| qwen3-4b | B first | 0.9010 | 0.8980 | **+0.0990** | **YES — L3a unreachable** |
| qwen3-4b | B second | 0.7972 | 0.8098 | +0.2028 | no |
| qwen3-4b-instruct-2507 | B first | 0.9010 | 0.9073 | **+0.0990** | **YES — L3a unreachable** |
| qwen3-4b-instruct-2507 | B second | 0.8770 | 0.8736 | +0.1230 | no |
| gemma-3n-e2b-it | B first | 0.8112 | 0.7792 | +0.1888 | no |
| gemma-3n-e2b-it | B second | 0.5775 | 0.4923 | +0.4225 | no |
| gemma-3n-e4b-it | B first | 0.7093 | 0.6825 | +0.2907 | no |
| gemma-3n-e4b-it | B second | 0.3532 | 0.2806 | +0.6468 | no |

**In the two B-first Qwen cells, no possible data could have produced L3a.**
The recorded bound is `contrast <= 1 - 0.9010 = 0.0990`. For 2507 B-first the
negative direction is compressed as well (`contrast >= -0.0927`), so that cell
cannot exhibit a SESOI-sized effect in *either* direction. The L3c verdict there
is guaranteed by the operating point, not earned from the data.

Two of eight cells are affected; six have real headroom. Any table reporting
"8/8 cells returned L3c" must mark these two, and the honest count of cells
where L3c was *empirically at risk* is **six**.

---

## 4. Construct validity and limitations

| # | issue | what is actually measured | possible mistaken interpretation | effect on headline claim | mitigation in place | remaining limitation |
|---|---|---|---|---|---|---|
| 1 | **Verifier-defined compliance** | a deterministic string predicate over letter-runs; `measurement_basis = deterministic_measurement_validated`, never `human_validated` (Gate-1 records) | "the model complied" as a reader would judge | none numerically | Gate 1 passes 674 instruments, boundary suite, 3-process determinism; a **permanent** scope sentence is attached to every claim and cannot be removed by a later stage | no human-agreement rate exists for v7; `HUMAN_VALIDATION_UNAVAILABLE` (`dci1/DECISIONS_V3.md` A2). Quote the scope sentence verbatim |
| 2 | **Compliance ≠ answer quality** | constraint satisfaction only. Row fields are `word_count, token_count, truncated, finish_reason, graded, vacuous_pass, non_vacuous, joint_state, response_length_words` (`constants.py:810-811`) — **no relevance, correctness or usefulness measure exists** | "composition degrades the model's answers" | none numerically | vacuity (F6) and a graded score (F5) partially proxy degeneracy | a response can satisfy both constraints and be useless. The study cannot see it. Nothing licenses a quality claim |
| 3 | **Same-form-only reference pool** | A vs three exact-count marker instructions differing only in word and count | "A is not special among companions" | **decisive** — it is the difference between the memo's refutation verdict and the narrow one | the registered `reference_pool_sentence` and scope `same_form_only` | Δ_R ≈ 0 may be a property of the *control design*, not of A. Unresolvable without the near-form arm |
| 4 | **Near-form arm unavailable** | nothing — `NEAR_FORM_ARM_NOT_AVAILABLE` in 4/4 models | "we tested and found no form effect" | blocks the strong claim entirely (§34 D18 `precondition`) | `near_form_absent_sentence` on every L3c | **not a null result.** The arm was never generated |
| 5 | **Difficulty-spectrum arm unidentified** | nothing — `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` in 4/4; 20 members withheld irreversibly | "A's loss is / is not what its difficulty predicts" | removes the only test that A's effect is not just its difficulty | D6/A7: status is irreversible and recorded; L3d/L3e withheld | `δ_difficulty`, `β`, `α_f`, `γ_tier` have no value on any lane |
| 6 | **Difficulty-matching discrepancy** | §13.11's `chance_compliance` column was **0.0 for every candidate on every v5/v6/v7 replication**, so admission used *raw solo compliance* as ι(R) while ι_A was chance-corrected (`CHANGES_SCIENTIFIC.md` 2026-08-29; `dossier/posthoc_confirmatory_difficulty.csv`) | "references were matched on the registered coordinate" | **small for the core pool**: all core references and A have κ = 0 on the confirmatory topics, so the two coordinates coincide there. Target shift ≤ 0.027 (2507), inside the 0.10 caliper | recorded as a finding, left for a researcher decision; not silently repaired | the class control is *not* κ-free (κ = 0.35 / 0.81) and is badly mismatched out of sample — see §3.5 |
| 7 | **Lexical differences among references** | eight markers, all ≤ 7 letters, unconstrained frequency ≤ 0.15 (`constraints.py:180-182`); `however` excluded as "A under another name"; `yet`/`still` admissible but dropped because "the vocabulary is capped at eight" (`:155-179`) | "references are interchangeable with A but for the word" | unquantified | rejections stated with reasons, incl. one measurement that contradicted an earlier assertion | **checked and cleared:** every marker is ≤ 7 letters and every realised m\* is ≥ 9, so no reference marker is differentially penalised by B at any operating point used. But per-word discourse effects are uncontrolled, and §3.2 shows they are large |
| 8 | **Response length** | `median_words` is computed and stored (`run/execute.py:695`, `run/gates_run.py:714`) but **read by no stage, gate, validity component or analysis module** — grep returns only writers | "answers were length-matched" | unquantified | none | v7 has **no length-matching criterion**. Reference median words differ by up to 18 within a lane (E2B: 107/125/123; qwen3-4b: 68/79/82, spread 14; 2507 and E4B: spread 2). Do not claim length control |
| 9 | **Vacuous passes** | F6 measures vacuity change vs B solo | "compliance rates are comparable across arms" | **material for 2507**: R2 (`MK3:3`) adds **+0.1468** [+0.1169, +0.1767] vacuity vs B solo where A adds only +0.0218. Under the `vacuity_forced` recomputation 2507's Δ_R moves from +0.0063 → **−0.0484** [−0.0785, −0.0183] | F5 recomputes every primary estimand with vacuity forced; F6 is a registered family | Gemmas show exactly 0.0000 vacuity change, so this is a 2507-specific confound. Report the F5 value beside the primary for 2507 |
| 10 | **Truncation** | share of responses hitting the cap: 0.000% (E4B), 0.001% (E2B), 0.039% (qwen3-4b), **1.262% (2507)** — all under the 0.10 ceiling | — | negligible | `CAP_TRUNCATION_MAX = 0.10` enforced; caps 512 on all lanes | none material |
| 11 | **Boundary / ceiling effects** | §13.14 compression readings | "L3c was earned everywhere" | **decisive in 2 of 8 cells** (§3.6) | compression is computed, recorded and named on the statement | qwen3-4b and 2507 at B-first could not have produced L3a at any effect size |
| 12 | **Order / position dependence** | `Ord_*` cross-configuration contrasts | "the effect is a property of the pair" | Λ reverses sign across position on E4B (−0.178 → +0.221); `Ord_B` reaches −0.356 | both orders are run and reported separately; results are never pooled across position | a single headline number for "the" effect does not exist. Report by position |
| 13 | **Development, not confirmatory, evidence** | six rehearsal lanes in the `development` namespace | "the preregistered study found X" | **decisive for status, not for values** | the namespace is structurally separate and the protocol's guards refuse it as study evidence; every row is labelled | the registered v7 study has **zero** confirmatory rows. No number here may be reported as a confirmatory result |
| 14 | **One (A, B) pair** | one exact-count production constraint against one word-length budget | "instruction interference behaves like this" | unquantified | parse independence and joint satisfiability were established by inspection before generation | n = 1 pair. No basis for a class-level claim about companion instructions |
| 15 | **Four models, two families, 2B–4B** | gemma-3n-{E2B,E4B}-it, qwen3-4b, qwen3-4b-instruct-2507 | "small open models behave this way" | results already disagree *within* this set | four models are run, none blocks another | two architecture families, one size band, one workstation. The sign of `D(B←A)` differs by family |
| 16 | **No identified mechanism** | response text only; `"no model internals are read"` (`user-notes/DCI-1_preregistration_v2.md:140`) | "A competes with B for a shared resource" | none numerically | none — the design deliberately excludes it | every mechanistic word ("competition", "capacity", "redistribution") is interpretation, not measurement |

### 4.1 Which of these could change the numerical result

1. **Ceiling compression (#11).** Two of eight Δ_R cells are arithmetically
   barred from the positive verdict. Changing m\* would change the number.
2. **Differential vacuity on 2507 (#9).** The registered robustness
   recomputation moves that model's Δ_R by 0.055 and flips its interval from
   spanning zero to excluding it.
3. **Which three references were drawn (#3, §3.2–3.4).** Leave-one-out flips
   the sign of E4B B-first; a re-run with different severities of the same
   families moved E2B's Δ_R by 0.008–0.014.
4. **Scoring rule.** Under `graded_0.99` (a registered F5 alternative), E4B
   B-first's Δ_R moves +0.0044 vs −0.0268 (sign flip) and E2B B-second moves to
   −0.1443 vs −0.0852. *All* F5 upper bounds still sit below +0.10, so the L3c
   conclusion survives; the point estimates do not.
5. **The chance-column defect (#6)** — bounded and small for the core pool
   (≤0.027 target shift), but it moved which candidates were admitted.

### 4.2 Which only restrict interpretation or generalization

Same-form-only pool (#3), missing near-form arm (#4), missing spectrum arm (#5),
lexical narrowness (#7), unmeasured length (#8), position dependence (#12),
development status (#13), one pair (#14), four models (#15), no mechanism (#16),
verifier-defined outcome (#1), and no quality measure (#2). None of these
changes a printed number; each changes the sentence the number may appear in.

---

## 5. Why these cases?

| choice | rationale as recorded | category |
|---|---|---|
| **A = "use the word `however` exactly *n* times"** | Chosen for *measurement* properties, established by inspection **before any generation**: (a) **parse independence** — the target verifier reads only letter-runs and whether `however` occupies a whole run, and no pool constraint and no value of B mentions that sequence or any of the letters h, o, w, e, v, r, so *"the treatment cannot alter the meaning of the outcome measurement"*; (b) **joint satisfiability** — `however` has seven letters, no doubled letter, begins with h, ends in `er`, so it satisfies every pool constraint and every admissible m; (c) **non-entailment**, certified in both directions with written witnesses (`user-notes/DCI-1_preregistration_v2.md:175-181`) | **scientific** (measurement validity) |
| …but the **specific word** `however`, as against any other word with those properties | **No document states why this word.** The properties above are necessary conditions it satisfies, not a selection argument | **not documented** |
| **B = "every word at most *m* letters"** | Same rationale: *"character-level lexical rules chosen so that a fixed program decides compliance without ambiguity"*, with the cost named — *"Exact verifiability costs realism"* (`:691`, `:296`) | **scientific**, with a recorded realism cost |
| **Was the pair chosen because it represents a broader class?** | **No.** The preregistration says the opposite: *"Created for this study. No prior instrument for this construct is reused"* (`:274`), and generalisation to other constraint families is listed among the **excluded phenomena** (`:103-125`) | — |
| **Was it chosen because an earlier experiment found an interesting effect?** | **No, and this is explicitly ruled out**: *"No effect estimate from any earlier work in this programme sets the sample size. No effect estimate from the calibration run sets the sample size, and no focal-to-reference contrast is computed on calibration data at any point"* (`:373`). The earlier exploratory programme used a different, segmentation-based constraint vocabulary (`user-notes/dci-construct-pass2.md`), whose own stated weakness was that interaction was operationalised as *"interaction among rules that read the same segmenter"* — a confound the `however` × word-length pair does not have. That the new pair escapes it is a fact; **no document claims it as the reason for the choice** | **scientific** for the pair-class; the escape from the segmenter confound is **not documented** as the motive |
| **Severity ranges: n ∈ 1..8** | v2 registered n ∈ {1,2,3}; the operative grid is `tuple(range(1, 9))` (`dci1/src/dci1v7/verifiers/constraints.py:80`), carried unchanged since v4r2. No rationale document for the widening was found | **not documented** |
| **Severity ranges: m ∈ 7..14, extension 15,16** | Two documented drivers: (a) **m ≥ 7 is forced** — *"`however` has seven letters, so m ≥ 7 is required for A+B to be jointly satisfiable at all"* (`constraints.py:82-84`); (b) the grid was widened **because calibration exhausted it** — the Gate-2 calibration screen found the registered grid gave an in-band m\* on three of four models and `FOCAL_RANGE_EXHAUSTED` on qwen3-4b (`user-notes/DCI1_v4_amendment_C_focal_grid.md:6-24`) | **engineering** (a), **selected from earlier development** (b) |
| **The eight marker references (MK1–MK8)** | Rules are stated and their rejections recorded: `MARKER_MAX_LETTERS = 7` (structural ceiling); `MARKER_NATURAL_FREQUENCY_MAX = 0.15`, *"about 1.5 times A's own measured maximum of 0.104"* (measured); `however` itself excluded because *"a companion counting A's word would be A under another name"*; eight words rejected for length; `also`/`finally` rejected on **measured** unconstrained frequency; and the note that *"an earlier draft of the preregistration rejected five of these on an assertion the measurement contradicted"* (`constraints.py:155-182`) | **scientific** (the ceiling and the frequency rule) |
| …but `yet` and `still` | *"admissible on both measured rules; not registered because the vocabulary is capped at eight"* (`constraints.py:164-168`) | **engineering/convenience**, stated plainly |
| **Which three of the pool become R1–R3** | Deterministic, per replication: smallest \|ι_R − ι_A\|, then lower structural tier, then registered feature-group order, then discourse role, with at least two discourse roles required (`dci1/src/dci1v7/stages/selection.py:210-226`) | **scientific**, but an extreme order statistic — see §3.3 |
| **The four models** | Execution order is justified (*"their operating points are known from v3 and the B+R pilot"*); the identities are not. The registry says the revisions *"are the values this workstation actually holds"* (`dci1/src/dci1v4/models/registry.py:1-18`). Two RX 7900 XTX cards at TP=1 bound the feasible size band | **engineering/convenience** |
| **The 720-topic bank** | 384 confirmatory topics derived from the SESOI power calculation (`DCI-1_preregistration_v2.md:375`); splits carried from v4 unchanged; 96 Calibration-B topics **newly authored for v5** because §13.7's two-split stability rule needs two disjoint sets. Calibration-A is declared **not naive** — 29 rungs per model were measured on it and the researcher has seen the measurements (`dci1/src/dci1v7/topics/__init__.py:1-30`) | **scientific** (size), **carried from earlier development** (composition), with contamination declared rather than hidden |

**Summary of §5.** The (A, B) pair was chosen for **exact decidability and
measurement stability under the treatment** — a real scientific rationale, and a
good one. It was *not* chosen to represent a broader class, and not because an
earlier experiment found an effect with it. The **operating points** were
selected from earlier development measurement. The **model set** is a
convenience sample bounded by the available hardware. The identity of the
target word itself is undocumented.

---

## 6. Verdict

### 6.1 Claims we can safely make

1. **Under a deterministic verifier, at each model's calibrated operating
   point, composing the two instructions moves at least one of them by more
   than the smallest effect of interest.** In 8/8 model × position cells at
   least one of `D(B←A)`, `D(A←B)` exceeds 0.10 in magnitude with a
   simultaneous interval excluding zero; the largest is `D(B←A)` = +0.392
   [+0.349, +0.435] on gemma-3n-e4b-it at B-second. The *sign* is not uniform:
   on both Qwen models `D(B←A)` is negative — composition **improves** B.
2. **Composition's cost falls asymmetrically between the two instructions, and
   which one pays depends on the model and on presentation order.** Λ excludes
   zero in 7/8 cells and reverses sign between model families (−0.519 on
   qwen3-4b, +0.221 on gemma-3n-e4b-it at B-second).
3. **Against three same-form, difficulty-matched exact-count marker companions,
   A carries no pair-specific excess cost to B at the registered threshold.**
   Δ_R ∈ [−0.085, +0.013]; every simultaneous upper bound is below +0.0392 and
   hence below +0.10; the 0.05 precision precondition was met in 8/8 cells.
   Report with the registered scope sentence attached and with the two
   ceiling-compressed cells marked.
4. **In the two Gemma models, the matched companions cost B *more* than A
   does.** Δ_R = −0.032 [−0.059, −0.005] and −0.085 [−0.119, −0.052] (E2B);
   −0.073 [−0.103, −0.042] (E4B, B-second).
5. **Presentation order is a first-order factor.** `Ord_B` = −0.356
   [−0.396, −0.316] on E4B; `Ord_Rbar` excludes zero in 4/4 models.
6. **The pipeline is reproducible.** Independent re-runs agree on Δ_R to
   ≤0.014, inside every half-width.

**Every one of these must carry, verbatim:** *"the outcomes are verifier-defined
and support no claim about compliance as an independent human would judge it"* —
the protocol makes that sentence permanent and unremovable
(`GATE_1_MEASUREMENT` records, `scope_sentence_is_permanent`).

### 6.2 Claims needing weaker wording

| instead of | say |
|---|---|
| "Raw compositional effects are large and directional" | "large, and concentrated on the marker-count instruction A; the direction differs by model — in qwen3-4b-instruct-2507 **both** instructions improve under composition" |
| "The asymmetry supports a redistribution account" | "Λ shows the two instructions are not symmetrically affected. Λ differences two *different prompts*, so it does not estimate a within-prompt trade-off. Read within a prompt, redistribution appears in qwen3-4b (both orders) and E2B (one order), and is contradicted in 2507 and E4B" |
| "Δ_R is small, so A is not unusually harmful" | "Δ_R is small **relative to same-form exact-count companions**. Whether it is small relative to companions in general was not tested" |
| "Δ_R = −0.085 to +0.013 across models" | correct as stated for the four canonical lanes — but add that the between-reference spread of Δ_j (0.029–0.103) exceeds the Δ_R half-width in 8/8 cells and \|Δ_R\| itself in 7/8 |
| "8/8 configurations returned L3c" | "8/8; in 2 of the 8 the positive verdict was arithmetically unreachable because the composed arm sat above 0.90. L3c was empirically at risk in six" |
| "The registered success criterion was met" | quote §26's own words: it establishes *"that the counterfactual Δ_R requires is identified and can carry a nonzero value"* and *"is not the scientific effect claim"* |
| "Difficulty-matched references" | "matched on instructed compliance to within 0.086 on the confirmatory topics; admission used raw solo compliance because §13.11's chance column was 0.0 for every candidate — a recorded defect whose effect on the core pool is ≤0.027" |

### 6.3 Claims we should not make

1. **"A is more harmful to B than comparable companions."** Not supported in any
   model or position; contradicted in three of eight cells.
2. **"The pairwise framing is refuted"** / any invocation of the memo's
   refutation verdict. It requires the near-form arm (§34 D18, closed at
   `precondition`); no lane had it. The signed statement says so in terms.
3. **"There is no companion-specific interference."** The design tested one
   companion class. `Δ_near` is `NEAR_FORM_ARM_NOT_AVAILABLE`, which **is not a
   null result**.
4. **"A's effect is what its difficulty predicts"** (or is not).
   `δ_difficulty`, `β`, `α_f`, `γ_tier` are `NOT_IDENTIFIED` on every lane.
5. **"Companion structural class matters"** from `Δ_broad`. Estimable on two
   models only, against a control that is not difficulty-matched on the
   confirmatory topics (gap 0.213 and **0.816**; κ = 0.807 on E4B) and that
   would have been refused admission under a correct chance column
   (`CHANGES_SCIENTIFIC.md`, 2026-08-30).
6. **Any mechanism claim** — competition, capacity, attention, redistribution as
   a *process*. No model internals are read, by design.
7. **Any claim about answer quality or task success.** No such quantity is
   measured anywhere in the pipeline.
8. **Any presentation of these numbers as confirmatory results of the
   preregistered study.** The registered v7 study has zero confirmatory rows.
9. **Any claim of length control.** `median_words` is stored and read by nothing.
10. **Any implication that Δ_R's interval generalizes over references.** It is
    conditional on three fixed cells (`bootstrap.py:3-5`).

### 6.4 Issues that could change the headline number

1. **Ceiling compression at m\*** — 2 of 8 cells cannot produce a positive
   verdict at any effect size (max attainable Δ_R = +0.0990).
2. **Which three references were drawn** — leave-one-out flips E4B B-first's
   sign; a same-family severity change moved E2B's Δ_R by 0.008–0.014; only
   6–14% of candidates survive the stability screen.
3. **Differential vacuity on 2507** — R2 adds +0.147 vacuity against A's +0.022;
   the registered `vacuity_forced` recomputation moves that lane's Δ_R from
   +0.006 (spans 0) to −0.048 (excludes 0).
4. **Scoring rule** — `graded_0.99` flips the sign of E4B B-first and nearly
   doubles E2B B-second's magnitude. (The L3c *conclusion* survives both
   recomputations; the point estimates do not.)
5. **The §13.11 chance-column defect** — bounded at ≤0.027 for the core pool,
   but it determined which candidates were admitted.

### 6.5 Issues that only restrict scope or generalization

Same-form-only reference pool; missing near-form arm; missing difficulty-spectrum
arm; verifier-defined rather than human-judged compliance; no answer-quality
measure; lexical narrowness of the marker vocabulary (≤7 letters, ≤0.15
frequency, capped at eight, one undocumented target word); unmeasured response
length; position dependence; one (A, B) pair; four models in two families in one
size band on one workstation; no mechanism; and the development-namespace status
of all six lanes. None of these moves a number. Each of them decides which
sentence the number is allowed to appear in.

---

## 7. What would most improve the evidence

In descending order of what it would buy per unit of compute:

1. **Generate the near-form arm.** It is the single change that converts the
   narrow `same_form_only` statement into the study's intended conclusion, and
   it is the mitigation the protocol's own red-team item R1 asks for.
2. **Move at least the two B-first Qwen cells off the 0.90 ceiling** so the
   positive verdict is reachable, or state the ceiling explicitly beside those
   two results.
3. **Vary the reference set deliberately** — a second admissible triple per
   model would convert §3.4's accidental evidence into a measured
   reference-selection sensitivity, which is currently the largest unquantified
   source of variation in Δ_R.
4. **Resolve the §13.11 chance-column finding** (recorded, not in force) so the
   admission coordinate and ι_A are computed on the same basis.
5. **Run the registered study.** Everything above is rehearsal evidence.

---

*Compiled 2026-08-30 from signature-verified stage records and from
`dci1/reports/dci1v7/dossier/`, whose block-level reconstruction was re-verified
against the records it must reproduce on all six lanes. No estimate in this
document was recomputed by hand; the Δ_R cancellation identity and the
`mean_j c(B|B+R_j) − c(B|B+A)` form were checked independently from the block
table and agree with the records to 0.00e+00. This audit changed no protocol
value, no threshold and no artifact.*
