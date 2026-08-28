# 01 — Research question, estimands and experimental design (all versions)

Consolidated 2026-08-27 from the repository at HEAD `76ae840`. Self-contained; every claim links to the artifact it comes from. Paths are relative to the repository root unless prefixed `../../`. Companion documents: [00_SCIENTIFIC_STORY](00_SCIENTIFIC_STORY.md) · [02_LIFECYCLE_AND_RESULTS](02_LIFECYCLE_AND_RESULTS.md) · [03_FAILURE_MODES_LIMITATIONS_INTEGRITY](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) · [04_CONTEXT_PRIOR_WORK_PAPER_STATE](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md).

---

## 1. The question

Does adding a second instruction **B** to a prompt causally degrade compliance with instruction **A**, *over and above the generic cost of one more instruction*? The confound (more instructions → worse compliance) is removed by **replacement** rather than addition: compare a composition containing B against one where B is swapped for a comparable reference R, holding the background set S and the instruction count fixed.

```
A + B + S   versus   A + R + S
τ(B→A | S,R) = P(fail A | A+B+S) − P(fail A | A+R+S)      (Arc 1 formulation)
```

From DCI-1 v4r2 onward the primitive is the **per-constraint compliance vector** X (one verdict per instruction in the prompt) and the primary quantity is **reciprocal delivery loss**

```
D(c←g) = P(X_c = 1 | c alone) − P(X_c = 1 | c with g)
```

paired within topic blocks, with the companion question carried by the **companion swap** Δ_R = D(B←A) − ⅓ Σ_j D(B←R_j) over references matched to A on difficulty. Sources: [`RESEARCH_STATE.md`](../../RESEARCH_STATE.md) §1; [`user-notes/DCI1_preregistration_v4r3.md`](../DCI1_preregistration_v4r3.md) §1, §11; [`user-notes/dci-construct-pass2.md`](../dci-construct-pass2.md) (the construct memo that demoted τ).

## 2. Two arcs, one question

| | Arc 1 — `src/dci/` + `exploratory/` | Arc 2 — `dci1/` (DCI-1) |
|---|---|---|
| Period | 2026-08-10 → 08-13 (merged to `main` 08-19) | 2026-08-16 → 08-27 (branch `feat/dci1v4-fresh-study`, not on `main`) |
| Protocol | v15 notebook → v19 preregistration ([`docs/preregistration/DCI_Pilot_Preregistration_v19_REVISED_FINAL.tex`](../../docs/preregistration/DCI_Pilot_Preregistration_v19_REVISED_FINAL.tex)); Stage 2 frozen ([`src/dci/v19/stage2_frozen.json`](../../src/dci/v19/stage2_frozen.json)); **confirmatory run never executed** | Seven registered states: v2 → v3 → v4r2 → v4r3 → v4r4 → v5 → v6 |
| Vocabulary | Pair 1 "exactly N bullet items" ← "transitive order"; Pair 2 "mandatory words" ← "every word unique"; Pair 3 "exactly N sentences" ← "increasing sentence lengths"; exploratory: sentence-count target vs punctuation focal | A = "use the word *however* exactly n times" (production class); B = "every word in the answer must have at most m letters" (budget class); reference families from a candidate library |
| Output | gate statuses ([`src/dci/statuses.py`](../../src/dci/statuses.py), 24 values); exploratory estimates stamped `EXPLORATORY_NO_EVIDENCE` | signed stage records, terminal reports, claim-ladder statements |
| Coupling | none — `dci1/` imports nothing from `src/dci` or `exploratory` ([`dci1/README.md`](../../dci1/README.md)) | |

Why Arc 2 started: the exploratory arm found that the reference-admission procedure of v19 was unsafe (a blind-admitted reference with verifier coupling κ = 0.00 was the strongest interferer; "the reference-admission procedure needs a collapse-aware screen before any confirmatory run is worth its compute", [`exploratory/FINDINGS.md`](../../exploratory/FINDINGS.md) §7) and that order was a large moderator ([`user-notes/DCI-1_preregistration_v2.md`](../DCI-1_preregistration_v2.md) §30). No document states that v19 was formally abandoned; it is simply never listed as live. Arc 1 detail is in [04](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md) §1.

## 3. How the estimand changed, version by version

| Version (date, prereg) | Primitive / primary estimands | Reference construction and matching | Claim rule | Registered non-identification / terminal vocabulary |
|---|---|---|---|---|
| **v19** (Arc 1) [tex](../../docs/preregistration/DCI_Pilot_Preregistration_v19_REVISED_FINAL.tex) | τ_{p,j}(b,k,o) per pair p, reference j, budget b, load k ∈ {2,5}, order o; R_p = min_j τ_{p,j}; headline Θ_crit = max_s min_j τ; SESOI ε ≥ 0.06 | 24 authored candidates (+12 blind), four matching coordinates (difficulty d, outgoing burden, incoming vulnerability, wording instability W), joint reference-error certificate, four smallest d_C | simultaneous one-sided lower bounds at FWER 0.05 (MP-EB or WSR-PP chosen by simulation); ROBUST_POSITIVE_SESOI / ROBUST_POSITIVE / NOT_ESTABLISHED | REFPOOL, NOTID, FEASIBILITY_MEASUREMENT_PILOT, … ; never run |
| **v2** (16 Aug) [md](../DCI-1_preregistration_v2.md) | τ_target-first, τ_added-first; block contrast D_i = F_B − ⅓ΣF_Rj over 384 blocks; SESOI 0.10; exchangeability margin 0.05 | fixed 12-candidate pool C1–C12; admit if within ±0.10 solo failure of **B** and ±20 % length; ≥ 3 admitted | Level 1 (swap effect) / Level 2 (identity-specific: all δ_jk inside ±0.05) | "Regime not found", "Apparatus not established" |
| **v3** (16 Aug) [md](../DCI-1_preregistration_v3.md), [changelog](../DCI-1_v2-to-v3_changelog.md) | same τ; reachability τ ∈ [−p̄_R, 1−p̄_R]; composed-reference rate in [0.15, 0.85]; family-simultaneous 95 % intervals | 8 tunable families RF1–RF8 × 4 severities (32 rungs), matched to **B** on solo failure; 624 topics (144 calibration = 24 pre-screen / 96 solo / 24 composed; 384 confirmatory; 96 sequestered) | direction / magnitude / equivalence per stratum | TARGET_RANGE_EXHAUSTED, FOCAL_RANGE_EXHAUSTED, GRID_RESOLUTION_INSUFFICIENT, REFERENCE_POOL_MISMATCH, COMPOSED_HEADROOM_FAILURE, RESPONSE_LENGTH_INCOMPATIBLE, MEASUREMENT_NOT_ESTABLISHED, MEASUREMENT_EVIDENCE_INSUFFICIENT |
| **v4r1** (19 Aug, withdrawn) [md](../DCI1_preregistration_v4r1.md) | τ, τ_S on a surrogate target, ι = τ − τ_S | — | — | never registered; superseded by v4r2 because the recovered design memo specified a *companion* swap on the focal outcome |
| **v4r2** (19 Aug) [md](../DCI1_preregistration_v4r2.md), [change summary](../DCI1_v4r2_scientific_change_summary.md) | compliance vector X; **D(B←A), D(A←B), Λ = D(B←A) − D(A←B), Δ_R**; secondary Δ^A (v3's quantity, demoted), Ξ, D(R_j←B), D(R_j←A); configuration = (model, outcome position), never pooled | references matched to **A** on solo compliance ±0.10 with a Newcombe condition; 25 cells/block (5 solo + 10 pairs × 2 orders), 384 blocks, M = 4 | claim ladder L1–L5 (§3) | EXCESS_NOT_IDENTIFIED (not terminal → §8.6 reduced design); §12.4 B solo vacuity ≤ 0.10; §17.4 vacuity-forced recomputation |
| **v4r3** (21 Aug, adopted/registered) [md](../DCI1_preregistration_v4r3.md), [changelog](../DCI1_v4r2_to_v4r3_changelog.md), [register](../../dci1/DECISIONS_V4R3.md) | adds δ_diff (difficulty residual from the §11.7 fit Y_{f,s} = α_f + β d_{f,s}, A excluded), Ξ promoted into F1, Δ_class (F9); difficulty coordinate **ι_c = (solo − κ_c)/(1 − κ_c)** with κ_c from the unconstrained cell | uniform stem "Answer in 60 to 120 words."; candidate library grammar (15 statistics × 5 forms → 30 families, 570 severities after R3); §12.6 coverage criterion C1–C7 with registered expansion; §13.4 admission on ι (caliper 0.10, pre-screen caliper 0.15, Newcombe ±0.05, band [0.10, 0.90]); difficulty spectrum (three rungs per family straddling ι_A); class arm CL7/CL8; 47 cells/block, 384 blocks, M = 8 (144,384 generations/model) | L1–L5 with L3a–L3e | DIFFICULTY_SUPPORT_NOT_IDENTIFIED; §13.10 COMPOSED_HEADROOM_FAILURE (terminal); Gate 1 = §10.2 + (§10.3 human or §10.4 autorater) |
| **v4r4** (21 Aug) [md](../DCI1_preregistration_v4r4.md), [changelog](../DCI1_v4r3_to_v4r4_changelog.md), [register](../../dci1/DECISIONS_V4R4.md) | as v4r3 (incorporated by reference) | as v4r3; **CP4/CP7 removed** (30 → 28 families, 584 → 524 instruments) | as v4r3 | Gate 1 replaced by **§10.7 A–E deterministic measurement validation** (ten conditions, no reviewer threshold); basis `deterministic_measurement_validated`, never `human_validated` |
| **v5** (23 Aug, adopted/registered; re-registered A1–A7) [md](../DCI1_preregistration_v5.md), [changelog](../DCI1_v4r4_to_v5_changelog.md), [decisions](../../dci1/reports/dci1v5/researcher_decisions.json) | F1 = {D(B←A), D(A←B), Λ, Δ_R, δ_diff, Ξ}; **direct order estimands** Ord_A, Ord_B, Ord_Λ, Ord_R̄, Ord_CL (F11, licenses L4b); new nuisance quantities κ^B_c (c's verdict on the B-solo cell), Σ_c, p̂_c | **core references inverted to production class, same-form with A** (exact count of a marker word: MK1–MK8 Tier-1, Tier-2 near-form, Tier-3 budget); validity V(R) = lexicographic conjunction of eight components with ι evaluated last; **interaction gate κ(R\|B)** (0.10 ≤ p̂ ≤ 0.90, \|Σ\| ≤ 0.25); two 96-topic calibration splits with ±0.20 stability; §12.6 C4 requires **≥ 6** straddling feature groups; 5 arms, 56 cells, 384 blocks, M = 8 (1,174,080 generations after A4); 18 stages | L1–L5 + L4b; thresholds Δ_R 0.10 generic / 0.25 pair-specific; precision preconditions D 0.05, Δ_R 0.05, Δ_j 0.06, Λ 0.08 | §28.2 **REFERENCE_SUPPORT_NOT_IDENTIFIED (D6, irreversible for the replication)**; §28.3 COMPOSED_HEADROOM_FAILURE, PREFREEZE_AUDIT_FAILURE; §30 design-fitting declaration; §26 methodological success criterion |
| **v6** (26 Aug, adopted/registered after A15) [md](../DCI1_preregistration_v6.md), [decisions](../../dci1/reports/dci1v6/researcher_decisions.json), [READINESS](../../dci1/reports/dci1v6/READINESS.md) | as v5 (estimand layer byte-identical, `revision.V9`) | as v5 plus: **GATE_2_75_COMPOSED_PROBE** measures composed headroom at the **frozen** m* two stages before Gate 4 over all ten §13.14 exposure classes, gating on a per-entry projected interval (§34 D23 = `projection_sd`, D26 = 0.0142); three `probe_only` stand-ins PS1–PS3 (non-selectable); §12.6 expansion repaired (V6-E01/E02); 19 stages | as v5 | adds COMPOSED_HEADROOM_UNREACHABLE (terminal, Gate 2.75); STANDIN_UNPLACEABLE (A17, non-terminal); §18 stage-1 REGISTRATION_INCOMPLETE is a readiness refusal (A15); coordinate-less rung dropped from coverage (A16) |

Non-comparability is registered explicitly: v3 and v4 numbers "are never compared" ([`RESEARCH_STATE.md`](../../RESEARCH_STATE.md) §4b); v5 §30 and v6 §4 declare every threshold fitted to the predecessor.

## 4. The claim ladder and the registered readings (v4r3 §3.2, in force for v4r4–v6)

| Level | Claim | Licensing rule | Identification gate |
|---|---|---|---|
| L1 | Compositional delivery loss exists | F1 simultaneous interval for the **named** D(c←g) has lower bound > 0 | c has solo headroom; §11.4 position caveat stated |
| L2 | Loss is directionally asymmetric | F1 simultaneous interval for Λ excludes 0 | L1 for **both** D(B←A) and D(A←B) |
| L3a / L3b / L3c | Δ_R lower bound > 0.10 / > 0.25 / upper bound < 0.10 (generic load) | | three core references (§13.4), else EXCESS_NOT_IDENTIFIED |
| L3d / L3e | δ_diff lower bound > 0 / interval inside ±0.10 at precision | | §13.8 support, else DIFFICULTY_SUPPORT_NOT_IDENTIFIED |
| L4 | Result replicates across configurations | same L1/L2/L3 classification in **every** registered configuration (per named member) | all configurations reached the level |
| L5 | Semantic identity-specificity, mechanism, generalisation | **never licensed by this design** | permanently withheld (`assert_no_l5_emitter`) |

Registered readings that travel with every statement ([`user-notes/DCI1_preregistration_v4r3.md`](../DCI1_preregistration_v4r3.md) §11.4, §17.3, §28):
- **§17.3**: "Failure to exclude zero is never reported as absence"; equivalence needs the simultaneous interval wholly inside ±0.10 **and** half-width ≤ precondition (D 0.05, Λ 0.08, Δ_R 0.05, δ_diff 0.05, Δ_j 0.06). SESOI = 0.10.
- **§28.1** outcome classes: Replication; **Configuration dependence** ("the quantity is configuration-dependent; the table is reported and no pooled scalar is quoted"); Delivery gain resolved (upper bound < 0); Meaningful magnitude (wholly beyond ±0.10); Equivalence.
- **§28.2** identification statuses: COMPANION_CLASS_NOT_MATCHED ("the reference pool is budget class and A is production class, so this excess is … not an excess relative to companions of A's own structural class"), EXCESS_NOT_IDENTIFIED, DIFFICULTY_SUPPORT_NOT_IDENTIFIED, REFERENCE_SUPPORT_NOT_IDENTIFIED (v5+), CLASS_ARM_NOT_AVAILABLE, NEAR_FORM_ARM_NOT_AVAILABLE, REFERENCE_POOL_SAME_FORM (v5+).
- **§28.3** terminal sentence: "**a terminal pre-confirmatory status carries no evidence about the effect**" (on every terminal report in v4r4, v5, v6).
- **§11.4**: D(c←g) is position-matched to its solo baseline only when c is stated first; every L1 in the shifted configuration carries `POSITION_CONFOUNDED` ("composition and position change together").
- **§10.5** scope sentence (on every analysis record): "the outcomes are verifier-defined and support no claim about compliance as an independent human would judge it".
- **`not_identified_note`** ([`dci1/reports/dci1v4r4/final_results.json`](../../dci1/reports/dci1v4r4/final_results.json)): "these are registered quantities this design does not identify. They are not null results, not zero, and not missing by accident, and no post-hoc estimate of them exists".

Multiplicity (v4r3 §15): F1 primary, **6 members**; F4 matrix completion 3; F5 robustness 9; F6 vacuity 11; F9 class 2; simultaneous intervals by studentised maximum modulus over 10,000 block-bootstrap resamples; Šidák for planning only. (The v4r4 signed records apply F1 at size 3 — see [03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §3.)

## 5. The gate sequence (v4r4; v5/v6 additions in brackets)

| # | Stage | Decides | Statuses it can write |
|---|---|---|---|
| 1 | QUALIFIED / PROTOCOL_REGISTERED | backend, model revision, topic hashes, signing key; v5+ signs the study manifest | REGISTRATION_INCOMPLETE (v6 A15: refusal, not terminal) |
| 2 | GATE_0_APPARATUS | §19 procedural pilot: every cell type on 12 topics × 4 draws (2,688 rows) | APPARATUS failure |
| 3 | REGIME_SCREEN | §12.2 pre-screen: every candidate rung on 24 topics × 1 draw; completion cap ∈ {512, 768, 1024}; §12.6 coverage C1–C7/C8 with ≤ 2 expansion rounds | DIFFICULTY_SUPPORT_NOT_IDENTIFIED (design-time); v5+ REFERENCE_SUPPORT_NOT_IDENTIFIED |
| 4 | GATE_1_MEASUREMENT | §10.2 (determinism, boundary suites, independent reimplementation) + §10.7 A–E (v4r4) | MEASUREMENT_EVIDENCE_INSUFFICIENT, SPECIFICATION_AMBIGUOUS |
| 5 | GATE_2_REGIME / FOCAL_CALIBRATION | A over n and B over m on the 96 (v5: 192) solo-calibration topics × M_CAL = 4; select n* (§12.3 aim) and m* (FOCAL_BAND (0.60, 0.95)); §12.4 vacuity; unconstrained cell κ | REGIME_NOT_FOUND, FOCAL_RANGE_EXHAUSTED, GRID_RESOLUTION_INSUFFICIENT |
| [v5] 5a | GATE_2_5_CANDIDATE_QUALIFICATION | V(R) components on the calibration splits | — |
| [v6] 5b | GATE_2_75_COMPOSED_PROBE | composed headroom at frozen m* over ten exposure classes | COMPOSED_HEADROOM_UNREACHABLE (terminal); STANDIN_UNPLACEABLE |
| 6 | GATE_3_REFERENCES (v5: 3A calibration / 3B selection / 3C identification) | §13.4 admission on ι; spectrum straddling; class companion; design variant full / no-spectrum / reduced (§8.6) | EXCESS_NOT_IDENTIFIED, DIFFICULTY_SUPPORT_NOT_IDENTIFIED, COMPANION_CLASS_NOT_MATCHED; v5 D6 irreversible |
| 7 | GATE_4_COMPOSED_HEADROOM | §13.10/§13.14: every registered cell type on the 24 reserved composed topics × M_CAL = 4; each constraint's raw compliance in [0.05, 0.95] | **COMPOSED_HEADROOM_FAILURE** (terminal; "its outcomes never revise" the references) |
| 8 | PREFREEZE_AUDIT (v5+) | mandatory artifact checks incl. `support_satisfied`, `protocol_hashes_agree`, `clean_worktree` | PREFREEZE_AUDIT_FAILURE (terminal) |
| 9 | GATE_5_FREEZE | binds all 66 §18.1 fields to a commit | — |
| 10 | CONFIRMATORY_GENERATION | 8 (reduced) / 47 (full) cells × 384 blocks × M = 8 on the reserved 384 topics | — |
| 11–12 | MASKED_ANALYSIS → UNMASKING → UNMASKED_ANALYSIS | once each, under one analysis code hash; §20 stratified permutation mask | — |

Sources: v4r3 §18; v5 §18; v6 §18; [`dci1/reports/dci1v5/execution_path_audit.md`](../../dci1/reports/dci1v5/execution_path_audit.md) (48 rules × 15 scenarios); [`dci1/reports/dci1v6/execution_path_audit.md`](../../dci1/reports/dci1v6/execution_path_audit.md) (73 rules).

## 6. Reference construction and difficulty matching — the identification machinery

This is where every registered design after v3 stopped, so its definitions are reproduced.

**Difficulty coordinate.** ι_c = (p_solo − κ_c)/(1 − κ_c), κ_c the compliance of an *unconstrained* answer with c's verifier; undefined (`DIFFICULTY_COORDINATE_DEGENERATE`) when κ_c ≥ 0.99. v4r3 C4 adopted it because raw solo compliance is not comparable across the production/budget divide: A's chance rate is exactly 0.000 (an exact count is never met by accident) while budget references run 0.52–0.89 ([`dci1/reports/section_13_2_v4/instructed_compliance.json`](../../dci1/reports/section_13_2_v4/instructed_compliance.json)).

**Coverage (§12.6), evaluated on the pre-screen table.** C1–C6 decisive, C7/C8 arm drops. **C4** (v4r3/v4r4): ≥ 4 well-formed feature groups each containing a family that *straddles* ι_A with ≥ 3 eligible rungs; **v5/v6: ≥ 6 groups with ≥ 3 eligible rungs spanning ≥ 0.40 in ι**. Eligibility (v5 U4 resolved at **E2**): p_solo(R) ∈ [0.10, 0.90] with vacuity ≤ 0.10. Registered expansion: up to two rounds of measuring reserve rungs.

**Admission (§13.4, v4r3/v4r4), on the 96-topic calibration split.** |ι_R − ι_A| ≤ 0.10 (pre-screen caliper 0.15), Newcombe 95 % interval of the solo-compliance difference intersects ±0.05, solo band [0.10, 0.90], vacuity ceiling, ≥ 3 core references from distinct feature groups, each with a spectrum pair straddling ι_A. Fewer than three → §8.6 **reduced design** (8 cells: 3 solo + unconstrained + A+B both orders + B+CL both orders), estimating only D(B←A), D(A←B), Λ, Δ_class.

**v5 validity stack V(R).** Lexicographic conjunction: raw headroom (Wilson95(p_solo) ⊂ [0.10, 0.90], lift ≥ 0.20), chance ceiling 0.75 point / 0.85 Wilson, vacuity, **interaction gate κ(R|B)** (R's verifier on B-solo responses; 0.10 ≤ p̂ ≤ 0.90, |Σ| ≤ 0.25 — free under the presence rule), split-half stability ±0.20, then ι last. §13.15 counts: ≥ 5 qualifying families, ≥ 2 Tier-1 core.

**Composed headroom.** §13.10 (v4r4) / §13.14 (v5/v6): on 24 reserved composed topics × 4 draws, every constraint in every registered cell type must have raw compliance in [0.05, 0.95]. It "runs after the spectrum and the class companion are already fixed, and its outcomes never revise them" (v4r3 §13.10). v6 moved a probe of the same band to the frozen m* before references are selected (Gate 2.75), gating on a per-entry projected interval with residual sd 0.0142 (§34 D26) — and forbade the probe from moving m* (A13).

**Focal operating point.** m* chosen by §12.3 on B's solo curve inside FOCAL_BAND (0.60, 0.95) over FOCAL_GRID {7..12} (+ v5 extension {13..16}); n* nearest the §12.3 aim on A's curve. Selected on **solo** curves — the mechanism behind every Gate-4 failure ([`dci1/reports/dci1v5/survival_diagnosis.md`](../../dci1/reports/dci1v5/survival_diagnosis.md)).

## 7. Fixed design constants (DCI-1 v3 → v6)

| Constant | Value | Source |
|---|---|---|
| Topics | 624 authored; 144 calibration (24 pre-screen / 96 solo / 24 composed; v5: two 96 splits), 384 confirmatory, 96 sequestered (hash-only, never materialised) | v3 §6; v5 §6.2; [`dci1/tools/build_topics_v4.py`](../../dci1/tools/build_topics_v4.py) |
| Blocks × draws | 384 × M = 8 confirmatory (v4r3 A1); M_CAL = 4 | v4r3 §8 |
| Decoding | T = 0.7, top-p 0.9, top-k 50 (v2), completion cap ∈ {512, 768, 1024} chosen at REGIME_SCREEN (512 on every replication) | v3 §7; regime records |
| Backend | vLLM 0.15.1 + ROCm 7.2, two RX 7900 XTX as independent TP=1 lanes | `environment_digest rocm7.2/vllm0.15.1` on every record |
| Models (pinned revisions) | Qwen/Qwen3-4B `1cfa9a72…`; Qwen/Qwen3-4B-Instruct-2507 `cdbee75f…`; google/gemma-3n-E2B-it `5e092ebc…`; google/gemma-3n-E4B-it `c1221e9c…` (amended from Qwen3.5/gemma-4 under A2, unservable on the pinned stack) | [`dci1/DECISIONS.md`](../../dci1/DECISIONS.md) A2 |
| Verifier | deterministic rule library; v4r4 hash `09f0675c…`, wordings `b9b258c5…`, specification `1704ddc3…`, mutation `a91f6220…` | [`dci1/reports/dci1v4r4/gate1_decision.json`](../../dci1/reports/dci1v4r4/gate1_decision.json) |
| Masking | §20 stratified permutation of companion identity; on the reduced design B's two companions are masked among two and A's/CL's only companion is visible | v4r3 §20-R4; [`RESEARCH_STATE.md`](../../RESEARCH_STATE.md) §4o |
| Analysis | 10,000 block-bootstrap resamples; analysis code hash sealed into the masked artifact (`dffb5a86…` for both v4r4 survivors) | UNMASKED records |

## 8. Measurement validity: what each version required and what was ever obtained

| Version | Gate-1 requirement | What was obtained | Basis written |
|---|---|---|---|
| v2 | 40 boundary cases, determinism, human ≤ 2/75 errors per class | determinism 1.000; human labels PENDING | — (all terminal before Gate 1 closed) |
| v3 | A1 one independent annotator → A2 autorater-assisted (`openai/gpt-oss-20b`, high effort, cap 2048) | dev rounds 235 → 69 → 28 disagreements, all verifier-correct; held-out 948 valid / 31 disagreements (0.033); author-performed blind labels 56/56 and 116/120 ([`autorater_forensics/experiments/FINDINGS.md`](../../autorater_forensics/experiments/FINDINGS.md)) — fail-class Wilson upper 16.1 % vs registered ≤ 10 % | `autorater_calibration_approved`, `HUMAN_VALIDATION_UNAVAILABLE` |
| v4r2/v4r3 | §10.2 for every verifier + §10.3 (independent human) or §10.4 (LLM validator) | §10.2 complete (reimplementation 1.000 over 37,700 responses; 128/128 verifier cards by the author with verdict visible); §10.3 no annotator; §10.4-R/R2 failed their own criteria (truncation 0.31, parse validity 0.69, `denominator_swap` sensitivity 0.23 vs 0.50 floor) | `human_validation_unavailable`; closed MEASUREMENT_EVIDENCE_INSUFFICIENT |
| v4r4–v6 | §10.7 A–E: specification validity, implementation validity, independent reimplementation, adversarial/boundary/mutation validation, provenance binding | all ten conditions PASS on four replications (determinism 1.000; reimplementation 1.000 over 628,800 verdicts; mutation 0 undetected; 2,141 wordings 0 ambiguous) | `deterministic_measurement_validated` — "not `human_validated` … no later stage may remove it" |

§10.5's second question — would an independent human reproduce these verdicts? — is recorded unavailable in every version.
