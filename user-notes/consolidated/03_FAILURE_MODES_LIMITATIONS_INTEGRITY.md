# 03 — Failure modes, implementation-vs-science ledger, limitations and record integrity

Consolidated 2026-08-27 at HEAD `76ae840`. This document separates three things the repository keeps apart but scatters: (1) the *scientific* mechanisms that stopped identification, (2) the *implementation* defects that changed what ran, and (3) deviations, limitations and stale statements a paper must declare or avoid. Companion documents: [00](00_SCIENTIFIC_STORY.md) · [01](01_RESEARCH_QUESTION_AND_DESIGN.md) · [02](02_LIFECYCLE_AND_RESULTS.md) · [04](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md).

---

## 1. Recurring scientific failure mechanisms

### 1.1 Reference support collapses between pre-screen and calibration (stopped v2, v3-Qwens, v4r4 ×3, v5 ×3, v6 ×3)

| Version | Evidence |
|---|---|
| v2 | fixed pool 47–100 % solo failure vs A 2–33 %; 0 admitted on all four ([`dci1/REPORT.md`](../../dci1/REPORT.md) §15) |
| v3 | Qwens 2 eligible rungs of 3 required at 4 severities per family (grid coarseness) ([`RESULTS_V3.md`](../../dci1/RESULTS_V3.md) §1) |
| v4r4 | core references 3/0/2/0; C4 straddling groups 7/5/4/4 at pre-screen → **3/0/2/0** at calibration; 65 of 84 shortlisted rungs below ι_A, strictly above 2/1/1/0; 17 rungs changed side ([`followup_diagnostics/09_*.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/09_coverage_vs_calibration.json), [`02_admission_landscape.json`](../../dci1/reports/dci1v4r4/followup_diagnostics/02_admission_landscape.json)) |
| v5 | C4 groups 4/5/5 vs 6 required; eligible rungs above ι_A 14–21 vs 143–163 below; 23–27 of ~35 families one-sided; marker ladders compressed (span 0.21–0.38 vs 0.40) ([`survival_diagnosis.md`](../../dci1/reports/dci1v5/survival_diagnosis.md)) |
| v6 | pre-screen coverage passed on 3/4, then the calibrated-basis re-read (192 topics × 4 draws, paired with ι_A) failed C4/C8 on both Gemmas (ι_A moved −0.079 on e2b); instruct `n_above: 0` at pre-screen (`dci1/evidence/dci1v6/<model>/GATE_3A_REFERENCE_CALIBRATION/`, `REGIME_SCREEN/`) |

Measured drivers ([`dci1/reports/dci1v5/reference_design_development.md`](../../dci1/reports/dci1v5/reference_design_development.md) F1–F2, F5–F6): a point-estimate pre-screen on 24 topics × 1 draw used as a hard selector — median |Δι| pre-screen→calibration 0.0709, **35.7 % of candidates move further than the 0.10 caliper**; rungs inside the caliper with raw solo above 0.90 (one at 0.974/0.932 terminated a replication on its own solo cell); support calibrated to the minimum (C4 met with zero margin on three v4r4 models, [`DECISIONS_V4R4.md`](../../dci1/DECISIONS_V4R4.md) B7); the operating-point grid ends where the operating point is (m* the last measured rung on all four v4r4 replications). A v6 audit (V6-E04) adds that the binding §13.15 requirement is `min_tier1_core` (cleared by 0 or 1) rather than family count (cleared by 6–7), so a library extension aimed at family count "would move the requirement that is not binding" ([`READINESS.md`](../../dci1/reports/dci1v6/READINESS.md) §11).

### 1.2 Composed headroom saturates on companion slots after m* is fixed on solo curves (stopped v4r4 ×2, v5 ×2, v6 ×3)

| Version | Cell that fired | Rate |
|---|---|---|
| v4r4 e2b (full design) | RF11:26 / RF11:32 vowel-initial references in composition with B | 0.958–1.000 (solo ι 0.633/0.679 inside band) |
| v4r4 instruct | `solo:CL` CL8:3 | 0.9896 (admitted on ι = 0.615 with solo 0.974, chance 0.932) |
| v5 e4b | `solo:CL` / `pair:B+CL` B | 0.9583 / 0.9792 |
| v5 instruct | `pair:B+R1` B / `pair:R1+B` B | 0.9896 / 0.9583 |
| v5 survivors | worst B cell | 0.8958 — margin 0.054; composition lifts the B slot by up to +0.104 |
| v6 e4b | `solo:CL` RF12:7 / `pair:B+CL` CL slot | 0.9583 / **0.0417** (floor side) |
| v6 qwen3-4b, instruct | `pair:B+A` B, projected interval | 0.8906 → [0.779, 1.002]; 0.9245 → [0.825, 1.024] |

Precision of the gate ([`dci1/reports/dci1v6/precision_design.json`](../../dci1/reports/dci1v6/precision_design.json)): the calibration→composed "split transfer" is sampling, not bias (observed variance 0.00430 vs 0.00515 expected; sets cut from one seeded shuffle), except the authored `calibration_b` sub-split (residual sd 0.0284, pooled 0.0142); topic ICC 0.35; a replication with every entry in band still fires §13.14 with probability **0.121 / 0.190** at 24 topics; the transfer reaches +0.189 on one slot. The sequestered eighth that would enlarge the composed set was never materialised (identities and hashes only), so §13.14's precision cannot be raised in this repository (§34 D21).

### 1.3 Vacuity and response length masquerade as interference

- The registered v4r2 prompt cannot start: B's solo vacuity ≥ 0.208 (up to 0.870) at every rung on all four models vs §12.4's 0.10 ([`cal_screen_v4/REPORT.md`](../../dci1/reports/cal_screen_v4/REPORT.md)).
- B+R pilot Δ +0.343/+0.375 → **+0.095/+0.068** under §17.4's forced recomputation; five-fold length gap between arms; matched-length −0.057/−0.003 ([`pilot_reanalysis/REPORT.md`](../../dci1/reports/pilot_reanalysis/REPORT.md)).
- FS screen: E2B D(B←A) +0.375 raw → 0.000 forced under the registered stem ([`fs_screen_v4/REPORT.md`](../../dci1/reports/fs_screen_v4/REPORT.md)).
- v4r4 qwen outcome_first: F6 gate binds (vac(B|B+CL) − vac(B solo) = +0.129 [+0.098, +0.160]), so the primary is reported beside the F5 vacuity-forced bounds.
- Length is a registered mediator, never conditioned on; A's length residual is not identified (collinear with identity across every companion set measured).

### 1.4 Nuisance channels are larger than companion identity

Matrix screen ([`matrix_screen_v4/REPORT.md`](../../dci1/reports/matrix_screen_v4/REPORT.md) §10): constraint class 0.40–0.60; focal position 0.29–0.35; companion identity (Δ_R) 0.05–0.10; length not identified; difficulty alone insufficient (A sits above the difficulty line by +0.067/+0.118 on the Gemmas). An admitted reference out-damages A on E2B (Δ₁ = −0.078 [−0.134, −0.023]). Single-order Δ_R changes sign on all four models — §8.1's both-orders requirement is what makes Δ_R well defined.

### 1.5 Instrument and construct

- Wording non-equivalence: solo-A compliance on qwen3-4b is 0.29 / 0.69 / 0.93 / 0.97 across the four registered paraphrases; e4b CL7's requirement-verb wording 0.31 — "§12.3 headroom gates hold only on average" ([`user-notes/AUDIT_2026-08-23_v4r4_evidence.md`](../AUDIT_2026-08-23_v4r4_evidence.md)).
- B is a weak construct at qwen's m* = 12: realised κ_B = 0.386 on the confirmatory unconstrained cell, so ι_B ≈ 0.64 (recorded 0.742 — see §3.2).
- 31–42 % of v4r3's library instances are anti-productive (stating the constraint lowers compliance) ([`dci1/reports/dci1v4r3/REPORT.md`](../../dci1/reports/dci1v4r3/REPORT.md) §1).
- Raw solo compliance is not a comparability coordinate across the production/budget divide: 12/12 references matched to A on solo, **2/12** on instructed compliance; A's chance rate is exactly 0.000 ([`section_13_2_v4/instructed_compliance.json`](../../dci1/reports/section_13_2_v4/instructed_compliance.json)).
- v5's own red team (R5): κ^B is measured at each model's own m*, so the reference set — and Δ_R's meaning — is not exchangeable across models; "no cross-model scalar carries a claim" ([`v5_prereg_redteam.md`](../../dci1/reports/dci1v5/v5_prereg_redteam.md); carried into v6's manifest as `not_closeable_by_rule`).

### 1.6 Measurement basis

No version obtained `human_validated`: v3 A1 (independent annotator) was replaced by A2 (autorater) when no annotator was available; v4r3's §10.4 LLM-validator pathway failed its own registered criteria (truncation 0.31, parse validity 0.69, `denominator_swap` sensitivity 0.23); v4r4 replaced the criterion with deterministic §10.7 A–E. §10.5's scope sentence therefore attaches permanently. The only human labels are the author's: 56/56 and 116/120 blind (fail class 4/52, Wilson upper 16.1 % vs ≤ 10 %; all four discordances at |s₀ − n| = 1), 128/128 verifier cards with the verdict visible ([`autorater_forensics/experiments/FINDINGS.md`](../../autorater_forensics/experiments/FINDINGS.md); [`dci1/reports/dci1v4r3/verifier_audit/report_Bryan.json`](../../dci1/reports/dci1v4r3/verifier_audit/report_Bryan.json)).

## 2. Implementation defects versus scientific outcomes — the ledger

The repository's own rule: a defect that changes what existing evidence means gets a [`CHANGES_SCIENTIFIC.md`](../../CHANGES_SCIENTIFIC.md) entry stating what changed, which results are affected and whether old and new remain comparable. The entries, grouped by what they did.

| Version | Defect (id) | Class | Effect on a number or verdict | Source |
|---|---|---|---|---|
| v2 | `dci1/` untracked; empty environment digest; E4B calibration fragment generated pre-qualification (D27) | provenance | none on estimates (all terminal pre-freeze); fragment marked `SUPERSEDED_NON_EVIDENCE` | v3 §33; [`DCI-1_v2-to-v3_changelog.md`](../DCI-1_v2-to-v3_changelog.md) |
| v3 | judge label flips are batch-composition nondeterminism (serialized 0/61 flips) | instrument (autorater) | diagnostic; verifier unaffected (235/235, 69/69, 28/28, 31/31 mechanical agreement) | [`autorater_forensics/experiments/FINDINGS.md`](../../autorater_forensics/experiments/FINDINGS.md) E3 |
| v4r2 | prose-only reimplementation segmented on `[^\W\d_]+` (admits numerics); §13.2 "ambiguity" claimed then withdrawn; §12.4 graded clause underdetermined; five reported quantities misdescribed (vacuity range; "intervals disjoint"; mean-reading feasibility; matrix refs not registered admission; two interval conventions) | validation instrument / documentation | no verdict moved; the §13.2 abstain/reject tables are "properties of the screens"; corrected statements in CHANGES 2026-08-20/21 | [`section_13_2_v4/REPORT.md`](../../dci1/reports/section_13_2_v4/REPORT.md); CHANGES "five reported quantities" |
| v4r3 | integer-key canonicalisation made signed regime records unverifiable; §10.4-R2 arm assignment contradicted the amendment (8 of 14 deciding items wordless but assigned to instruction-only) | record integrity / validator design | records re-sealed (`record_signature_repair.json`); R2 verdict stands, diagnosis "convention-access" | [`dci1/reports/dci1v4r3/validator_diagnosis.json`](../../dci1/reports/dci1v4r3/validator_diagnosis.json) |
| v4r4 | **nineteen defects, mostly "a reader with no producer"**: Gate 2 read `cell_rates` keys that do not exist (crashed after 16,128 generations); §7.2 escalation flag had readers and no writer (qwen's m* = 12 would have been unreachable); `design_variant_for` read a non-existent attribute so **every replication was reduced whatever Gate 3 selected** (four Gate-3 records superseded at `7eb1947`); `stages/gates.py` declared its own `TerminalStatus` so a Gate-4 terminal would have escaped as a traceback; five §18.1 fields with no producer; §26 durability gate with no caller; durable-mirror check compared zero bytes and reported `passed`; `cmd_qualify` never mirrored; `assert_generation_licensed` demanded an unregistered field; a test fixture (`FakeSelection`) encoded the variant defect as expected behaviour; **`emit_l4` compared level sets, not per-member levels** (sealed; e4b's L4 invalidated) | execution path | one design variant and one emitted claim moved; every estimate reproduces from raw rows to 1e-9 | CHANGES 2026-08-22 "nineteen defects"; [`EXECUTION_REPORT.md`](../../dci1/reports/dci1v4r4/EXECUTION_REPORT.md) §8.3 |
| v5 | E1–E3 (A1): three of four models had no legal path into the lifecycle; four generating stages read `generate or fake_backend(...)` so the documented entry point would have signed fabricated text; `synthetic` flag recorded how the runner was called. E4 (A2): budget 1,135,104 → 1,144,896. E6–E8 (A3): Gate 2 calibrated the carried set (326 rungs) instead of §12.7's 112 (274,944 rows discarded); budget → 1,172,544; §12.3 escalation had no caller. **E9–E28 (A4): twelve registered rules not on the execution path** — 58/78 family members had no producer; 3/5 claim emitters uncalled (a complete lifecycle emitted `{'L1': 2}`); §12.6's coverage criterion evaluated on an empty set and read by nothing (a replication with unmet coverage would have proceeded with the core arm and reported Δ_R — "the outcome §12.6 registers as forbidden"); REGIME_NOT_FOUND had no condition; ι_A read from the wrong severity; A never measured on pre-screen (budget → **1,174,080**); a non-straddling family lost its core slot (v4r4's F5 failure re-implemented); §12.6's eligibility predicate underdetermined (U4 → E2). E29–E32 (A5–A8): terminal report could not be retired after supersession; `--device` unreachable (e2b Gate 0 discarded); `--supersedes` not passable; **`PREFREEZE_AUDIT_FAILURE` computed but never raised** (two blocked replications report `terminal_status: None`) | execution path / registration | 478,464 rows invalidated across six superseded manifests (`2960a1fc → 70608e5d → b040b343 → d0485a6d → faa034bd → e2721b17 → f19b5e88 → af5fa4bc`); no v5 verdict on the live manifest moved; six repairs made a gate strictly harder | [`amendment_register.md`](../../dci1/reports/dci1v5/amendment_register.md); [`execution_path_audit.md`](../../dci1/reports/dci1v5/execution_path_audit.md) |
| v6 (design) | **V6-E01**: §12.6's expansion admits no Tier-1 reserve rung on any replication in either round (interpolation cannot raise a span; 32 rungs/replication unreachable). **V6-E02**: expansion rows carried no `eligible` field so the criterion never saw 34/32/55 measured rungs — over the full table **qwen3-4b's C4 is True**. V6-E03: the probe's re-selection branch was unexecutable (moot after A13). V6-E04: development prescreen evaluated a proxy for §13.15; coverage certified on 24 topics × 1 draw and matched on 192 × 4. V6-E05: `n_stable` read a nonexistent key (0 on every signed v5 record; actual 11/14/16/9) | execution path (v5 code, found by v6) | narrows the v5 diagnosis ("part of what survival_diagnosis attributes to library shape is the expansion rule being unable to use the library it has"); no v5 verdict changed | CHANGES 2026-08-25; [`expansion_dryrun.json`](../../dci1/reports/dci1v6/expansion_dryrun.json) |
| v6 (run) | A15: CLI created no signing key, did not forward `--repo-root`, and wrote a readiness verdict as a §28.3 terminal report (e2b retired, bound in the manifest). A16: `tie_key(r["iota"])` on a rung with undefined ι (CR7:56 at chance ≥ 0.99). A17: an unplaceable `probe_only` stand-in raised and ended the stage. **Undocumented**: `protocol_hashes_agree` cannot pass after A16/A17 edited the bound document (recomputed `ef7d1787…` vs registered `95db6df4…`) | apparatus / registration | A16 changed no verdict (drop makes conditions harder); A17 loses diagnostic breadth only; the hash failure co-occurs with `support_satisfied` on e2b so its verdict is unchanged, but it would fail any v6 replication reaching PREFREEZE_AUDIT | [`incidents/`](../../dci1/reports/dci1v6/incidents/); `dci1/evidence/dci1v6/gemma-3n-e2b-it/terminal_report.json` |

The general lesson the repository draws ([`RESEARCH_STATE.md`](../../RESEARCH_STATE.md) §4v–§4w): "an end-to-end harness that supplies the seam it is testing does not test the seam"; tests asked *does this function behave*, the contract asked *is this field declared*, the synthetic lifecycle asked *does the happy path complete*, and none asked *does the registered rule lie on the path a replication takes*.

## 3. Undocumented deviations from the registered analysis (must be declared or resolved)

| # | Deviation | Where verified | Moves a number? | Moves a verdict? |
|---|---|---|---|---|
| 3.1 | **F1 intervals computed at family size 3** (members D(A←B), D(B←A), Λ; `sidak_reference` 2.388) where §15 registers F1 = 6 | signed `UNMASKED_ANALYSIS` records; [`DCI1_preregistration_v4r3.md`](../DCI1_preregistration_v4r3.md) §15 line 2627 | yes — intervals would be wider at k = 6 (critical ≈ 2.63 vs 2.33) | no L1 verdict flips (every emitted interval clears zero by ≥ 0.077); no rule for shrinking on the reduced design is written anywhere |
| 3.2 | **Gate-2 chance compliance at the wrong severity**: κ_A at severity 1 and κ_B at severity 7 regardless of n*/m* | [`dci1/src/dci1v4r4/run/gates_run.py`](../../dci1/src/dci1v4r4/run/gates_run.py) lines 187–190; recomputed from signed load-0 rows | yes — ι_A 0.702 → 0.719 (qwen), 0.695 → 0.727 (e4b), 0.596 → 0.602 (instruct); qwen ι_B 0.742 → ≈ 0.571 | first-order check: class companion argmin and design variants unchanged; RF11:21 (qwen), RF11:26 and RF9:13 (e4b) change side relative to A. Propagates to `prefreeze_audit.json`, followup §2.1/§7, EXECUTION_REPORT §1, `d17_b_strength_decision.md` §2(a) |
| 3.3 | Claim-ladder emitters committed **after** the Gate-5 freeze, during confirmatory generation (`8c86f23` 01:11, `ab9e993` 01:15 on 2026-08-22; generation 00:59–02:15) | [`AUDIT_2026-08-23_v4r4_evidence.md`](../AUDIT_2026-08-23_v4r4_evidence.md) §1(i) | no | the freeze bound rules, the masked seal bound code; on the reduced design the mask protects D(B←A), D(B←CL), Λ but not D(A←B) |
| 3.4 | §28.1 outcome classes never emitted (equivalence, delivery gain resolved, meaningful magnitude); §17.3's equivalence rule has no emitter | records contain no such strings | no | three D members satisfy equivalence (e4b D(B←A)\|first [−0.018, +0.031]; qwen D(B←A)\|second [−0.045, +0.021]; e4b D(A←B)\|second [−0.073, +0.009]) and are reported only as "unresolved direction" |
| 3.5 | Confirmatory rows carry `classification: "… (ADOPTED, NOT FROZEN)"` and `stage: "v4r3-confirmatory"`; freeze records `protocol_version "4.0 revision 3"` | `dci1v4r4/__init__.py:56`, `run/confirmatory_run.py:35` | no | labels only |
| 3.6 | v6 protocol hash not re-bound after A16/A17 (§2 last row) | e2b terminal report | no | structural: no v6 replication can pass `protocol_hashes_agree` |
| 3.7 | `lifecycle_integrity.json` covers stage records only through Gate 4 (head `bbe5b8f2`); later records verified only by `tools/v4r4_evidence_manifest.py --verify` | [`paper/v4r4_bundle/MANIFEST.md`](../../paper/v4r4_bundle/MANIFEST.md) V1 (gitignored) | no | scope of the integrity claim |
| 3.8 | Registered but never produced: §8.3 greedy replication (96 blocks, T = 0); §22 length-stratified descriptive decomposition; §23 realised variance decomposition; §11.5 confirmatory κ/ι re-estimation | no artifacts | — | absent registered secondaries |

## 4. Permanent limitations (stated by the protocol itself)

1. **Verifier-defined outcomes.** §10.5: "support no claim about compliance as an independent human would judge it"; §10.7: "no later stage may remove it".
2. **No cross-model or cross-configuration estimand.** Four replications are never pooled (§6.1); v4r4 registers no order contrast; the records store no bootstrap replicates, so none can be formed after the fact; R5 forbids a cross-model scalar by construction.
3. **Reduced design → no spectrum-dependent quantity.** Δ_R, Δ_j, δ_diff, Ξ, D(B←R_j), D(R_j←B) `NOT_IDENTIFIED`; L3 unreachable; "One companion cannot identify a class effect" (§13.7).
4. **Position confound.** Every outcome_second L1 is `POSITION_CONFOUNDED`; the study has no position-clean estimand at all (`GAPS.md` G7).
5. **Design fitting.** Every v5 threshold was chosen after observing all of v4r4 (§30); v6 fits four quantities to v5 (§4); "retrospective performance is not prospective validation".
6. **C4 without margin** on three v4r4 models — every straddling group load-bearing; Gate-3/4 results conditional on all four holding.
7. **Gate-4 precision** cannot be raised here (24 composed topics; sequestered eighth never materialised).
8. **Two model families, four checkpoints**; the 2026-08-23 audit: cannot say "four models".
9. **Single-device, single-workstation evidence**; no off-machine copy (`durability.json` `off_machine_copy: false`).
10. **Length account of A not identified** by any companion set this pool can produce (v5 §34 closing sentence).
11. **Adopted over objection**: D7 (R13), D15 (R2), D17's floor fitted to four models; Calibration-A non-naive.

## 5. Withdrawn, superseded and stale statements — do not quote

| Statement | Status | Where the correction lives |
|---|---|---|
| "B+R pilot Δ = +0.34/+0.38 is pair-specific and robust to vacuity (holds at ≥ 20 words)" | withdrawn | [`pilot_reanalysis/REPORT.md`](../../dci1/reports/pilot_reanalysis/REPORT.md); CHANGES 2026-08-20 |
| "A's excess is a length effect within ±0.010" (matrix screen first pass, fitted through A) | withdrawn | CHANGES 2026-08-20 "V5 and length lines were fitted through A" |
| "§13.2 is a preregistration gap / the smallest remaining blocker" | withdrawn | [`section_13_2_v4/REPORT.md`](../../dci1/reports/section_13_2_v4/REPORT.md) |
| "The vacuity range is 0.208–0.659"; "the E2B intervals are disjoint"; "under the mean reading nothing runs on any model" | corrected | CHANGES 2026-08-21 "five reported quantities were misdescribed" |
| `companion_identity_review.md` §7 "D(B←A) = 0.468/0.316 vs D(R̄←A) = 0.582/0.727" | not a delivery loss (cross-set) | [`v3_reanalysis/REPORT.md`](../../dci1/reports/v3_reanalysis/REPORT.md) |
| "Three of four models admitted none" | false (qwen3-4b admitted two) | `EXECUTION_REPORT.md` line 343 vs `final_results.json` |
| Calipers 0.075 / 0.10 in `SCIENTIFIC_FOLLOWUP_EVIDENCE.md` §6 | wrong (registered 0.10 / 0.15) | CHANGES 2026-08-22 "v5 drafted" item 6 |
| "one analysis code hash … makes the two replications comparable" | too strong — the paper planning rejects it | [`paper-dci1v4r4-i1/01_narrative.md`](../paper-dci1v4r4-i1/01_narrative.md) |
| `dci1/README.md`: "The live protocol line is v4 revision 3 … blocked on §10.4's researcher approval alone" | stale (closed; "the missing thing is evidence, not authorisation") | [`dci1/reports/dci1v4r3/gate1_decision.json`](../../dci1/reports/dci1v4r3/gate1_decision.json) |
| `RESEARCH_STATE.md` §4b v4r4 row "The live protocol line"; line 95 "v6 … Executing"; `dci1/reports/dci1v6/closure.json` `PROTOCOL_REGISTERED` ×4 | stale (v6 is live-line-then-terminal as of 2026-08-27) | `dci1/evidence/dci1v6/<model>/terminal_report.json` |
| "1,172,544 generations" (v5/v6 budget) | superseded by A4/E25 → 1,174,080 | [`dci1/reports/dci1v5/development/d1_compute_budget.json`](../../dci1/reports/dci1v5/development/d1_compute_budget.json) |
| `paper-dci1v4r4-i1/04_v5_prospective_followup.md` §7: v6 "is a proposal, not a registered protocol"; v5 "run without amendment to its scientific rules" | stale / overstated (v6 registered and run; v5 amended A1–A8 with one underdetermined rule resolved at E2) | [02](02_LIFECYCLE_AND_RESULTS.md) §8–9 |
| Exploratory: "any thinking at all fixes this one"; "2 of 8 cross-model cells identified"; the capped reasoning-curve CSVs; Round-10 register numbers (shared-seed defect) | withdrawn / superseded | [`exploratory/SCIENTIFIC_CLAIM_AUDIT.md`](../../exploratory/SCIENTIFIC_CLAIM_AUDIT.md); `figures/reasoning_compute/data/PROVENANCE.json` |
| Anti-splice intervention (`ANTI_SPLICE_MANIPULATION_FAILED`) | void — "a failed manipulation check voids an estimate; it does not weaken it into a null" | `RESEARCH_STATE.md` §5 |

## 6. Evidence durability and reproducibility

- **Gitignored**: `dci1/evidence/` (v4r4 736 MB, v5 21 GB, v6 17 GB), `dci1/durable_root/`, `paper/`, `exploratory/runs/`. Signed records, raw rows and the paper bundle exist only on the producing workstation. Committed surrogates: `dci1/reports/` (322 files) including `final_results.json`, `closure.json` ×3, terminal-outcome copies in reports for v4r3/v5 only.
- **Branch state**: `feat/dci1v4-fresh-study` is 134 commits ahead of `main`; `main` (2026-08-19) contains none of v4r2 → v6. The freeze commit `450a049` is on no remote ref.
- **Promotion path**: `exploratory/evidence/README.md` defines it; nothing is promoted ("Currently promoted: None yet"). Under [`CLAUDE.md`](../../CLAUDE.md), "a cited unpromoted run is a broken citation".
- **Integrity tooling that exists**: HMAC-signed stage records (note: a key-holder can sign any content at any time — the signature proves integrity, not precedence); `tools/v4r4_evidence_manifest.py --verify`; `lifecycle_integrity.json` (through Gate 4 only); `post_freeze_delta.json`; v5/v6 registration manifests with content hashes; `paper/v4r4_bundle/MANIFEST.md` (53 present / 3 derived / 6 missing: two terminal Gate-4 stage records by design, the §27 codebook, Related Work, `.bib`, figure code).
- **Worktree rule**: v5 §19's `clean_worktree` precondition reads `git status --porcelain`; untracked files in the worktree (including these consolidated documents, until committed) will refuse any future registration that carries the rule.
