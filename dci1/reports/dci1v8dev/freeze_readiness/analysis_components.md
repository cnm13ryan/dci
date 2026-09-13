# Finding 10 — analysis narrowing (v7 → v8), verified 2026-09-02

Citations: `AR` = dci1/src/dci1v7/run/analysis_run.py; `CL` = dci1/src/dci1v7/analysis/claims.py; `V8` = dci1/src/dci1v8dev/confirm/analysis.py; `V8R` = dci1/src/dci1v8dev/confirm/report.py; `FZ` = dci1/src/dci1v8dev/confirm/freeze.py (state at commit 11697e9).

## A. Claim ladder

| component | v7 definition | what it safeguarded | v8 at 11697e9 | declared? / relevance |
|---|---|---|---|---|
| L1 D(B←A), D(A←B) | `CL.emit_l1`:798, called `AR`:1469 | gated on solo headroom, identification statuses, §17.4 vacuity agreement | estimates + intervals `V8`:145-147; no emitter | not declared; relevant |
| L1 headroom gate | `AR:_has_headroom`:1196 (`L1_SOLO_HEADROOM_FLOOR` 0.05) | a B at the floor cannot exhibit a loss | absent | not declared; relevant |
| L2 Λ | `CL.emit_l2`:850, called `AR`:1485; conditional on L1 licensed | order asymmetry only where a loss exists | Λ estimated `V8`:147; no precondition | not declared; relevant |
| L3a/L3b | `CL.delta_r_reading`:283-310 inside `emit_l3`:900 | pair-specific excess above 0.10 / 0.25 | `CL.delta_r_reading` called `V8`:220 | retained; emitter guards omitted |
| L3c | `CL`:314; `l3c_requires_near_form`:454, `l3c_disposition`:477 | strong refutation needs the near-form arm | `V8`:275 maps L3c → LOCAL_EQUIVALENT_L3c without the guard | near-form absence declared (`FZ`:49-55) but the guard not applied; relevant |
| L3d/L3e | `CL.delta_difficulty_reading`:355 | difficulty reading conditioned on §13.8 support | called `V8`:222 with support from `SP.estimate` | retained |
| L4a | `CL.emit_l4a`:1040, called `AR`:1550 | same classification in both configurations | none; conjunction is across frames only | not declared; relevant |
| L4b | `CL.emit_l4b`:1134, called `AR`:1561 | order contrasts, gated on both configurations analysed | F11 members + intervals `V8`:363-372; no emitter | not declared; relevant |
| L5 | `CL.assert_no_l5_emitter`:1200 | refuses generalisation | no emitters; scope sentence `V8R`:105 | obsolete |

## B. Families

| family | v7 | v8 |
|---|---|---|
| F1 | six members (constants:410) | all six per frame + JOINT_F1 across frames (`V8`:145-175, 376) |
| F2 | D(B←R_j), Δ_j | `V8`:154-157 |
| F3 | D(A←R_j), Δ^A | `V8`:158-159 |
| F4 | D(R̄←A), D(R̄←B), D(R̄←R̄′) | `V8`:160-162 |
| F5 | nine vacuity-forced / graded-0.99 recodings (`AR`:453-462) | omitted, undeclared; relevant |
| F6 | fourteen vacuity-rate differences vs B solo (`AR`:445) | omitted, undeclared; relevant (it is §17.4's gate) |
| F7 | reciprocal losses D(R_j←B), D(R_j←A) | omitted, undeclared; rows exist |
| F8 | spectrum losses + tier fit (`AR:_record_tier_fit`:709) | replaced by F_SPECTRUM slope; deviation declared `FZ`:59-63 |
| F9/F10 | near-form, class arms | not run; declared `FZ`:49-55 |
| F11 | Ord_A, Ord_B, Ord_Λ, Ord_R̄, Ord_CL | Ord_CL omitted (no class arm); rest `V8`:182-187 |

## C. Gates, audits and safeguards

| component | v7 | v8 | declared / relevance |
|---|---|---|---|
| §17.4 vacuity gate + both-bounds rule | `AR:_vacuity_gate_binds`:1294, `CL.l3_vacuity_agrees`:704 | absent | not declared; relevant (highest-value omission) |
| Ξ direction gate | `CL.xi_gate`:395 | Ξ estimated `V8`:151, gate never called | not declared; relevant |
| Projection audit | `AR:_projection_audit`:1337 | absent | not declared; relevant |
| Raw-coordinate secondary | `AR:_raw_coordinate_secondary`:513, `CL.coordinate_agreement`:652 | absent | not declared; relevant to δ_difficulty(f) only |
| Masking / unmasking | `AR`:944/1051/1103, analysis/masking.py | absent | declared `FZ`:42-48; obsolete (no analyst decision point) |
| Prefreeze audit (§33) | stages/audit_prefreeze.py | none | not declared; relevant |
| final_report_checks | run/final_report_checks.py | none | not declared; relevant |
| Degenerate-replicate ceiling | `SP.bootstrap_spectrum`:532 (`DEGENERATE_REPLICATE_MAX`) | point-dropping retained; ceiling omitted | not declared; relevant |
| Boundary allowance | analysis/boundary.py; `AR:_intervals`:875 | applied to every member `V8`:198-207; projected-vs-realised summary omitted | partly; summary undeclared |
| Studentised max-modulus block bootstrap | `bootstrap_family`:93 | retained + topic-level joint family | retained |
| Precision precondition / INSUFFICIENT_PRECISION | `CL.Interval.meets_precondition` | retained, escalated to a model verdict `V8`:259-271 | retained |
| Within-frame Δ_j heterogeneity | `AR:_heterogeneity_disagrees`:1315 | omitted (F2 computed, unused); FRAME_HETEROGENEOUS is a different, cross-frame test | not declared; relevant |
| Algebraic form checks | `E.assert_delta_r_forms`, `E.assert_order_forms`, `SP.assert_algebraic_forms_agree` | first two called `V8`:318/363; spectrum one omitted | not declared; relevant to δ_difficulty(f) |
| NOT_IDENTIFIED ledger (§34 D6) | `AR:_licensed`:96, `identification.assert_not_rehabilitated` | absent members simply missing | not declared; relevant |
| §26 methodological success | `AR`:1151 | absent | not declared; relevant |
| Analysis-code seal | `AR.analysis_code_hash`:73, re-verified pre-unmask | hashed into manifest and freeze | declared in substance |
| Configuration scope assertion | `CL.assert_configuration_scope`:106 | not called | low relevance |

## D. v8 additions absent from v7

Frame conditioning (`V8:frame_table`), JOINT_F1 cross-frame family (`V8:joint_members`), per-model LOCAL conjunction verdict (`V8:local_model_verdict`), F_REFSENS over admissible triples (`V8:delta_r_over`), F_SPECTRUM slope family, per-frame allocation/precision record, operating-point stability, frame-scoped strongest-permissible statement.

Verdict: **CONFIRMED.** Resolution recorded in the v8 preregistration §Analysis and implemented in `confirm/analysis.py` (see CHANGES_SCIENTIFIC 2026-09-02).
