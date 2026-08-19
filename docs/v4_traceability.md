# DCI-1 v4 traceability

Every substantive requirement of `user-notes/DCI1_preregistration_v4r2.md`,
where it is implemented, which test pins it, and its status.

**The protocol is not frozen.** Gate 5 and confirmatory generation are
implemented and are not executed. Nine registered open decisions (V1 to V9)
remain the researcher's, and the pre-freeze checks that block are listed in
§7 below.

Source precedence, applied throughout: v4r2 first; the implementation brief
(`user-notes/Implement_DCI1_v4_as_a_Fresh_Fully_Isolated_Study.md`) only where
v4r2 leaves ordinary engineering detail unspecified; everything else as
history. Where v3, revision 1, the pilot, existing code or historical
artifacts disagree with v4r2, v4r2 is implemented.

## 1. Resolved paths

The brief names some documents by a filename that does not resolve. Resolved
by content:

| Named in the brief | Resolved path |
|---|---|
| `user-notes/DCI1_preregistration_v4.md` (revision 1) | `user-notes/DCI1_preregistration_v4r1.md` |
| `reports/br_pilot_v4/…` | `dci1/reports/br_pilot_v4/…` |
| `evidence/br-pilot-v4/<model>/` | `dci1/evidence/br-pilot-v4/<model>/` |
| `evidence/dci1-v3/<model>/` | `dci1/evidence/dci1-v3/<model>/` |
| `tools/br_pilot_v4.py`, `tests_v3/…` | `dci1/tools/…`, `dci1/tests_v3/…` |
| `reports/nearmiss_sensitivity_v3.json` | `dci1/reports/nearmiss_sensitivity_v3.json` |
| `reports/gate1_dev_review*.md` | `dci1/reports/gate1_dev_review*.md` |
| `autorater_forensics/experiments/human_review/` | repository root, as named |

## 2. Requirement to code to test

| v4r2 | Requirement | Implementation | Test | Status |
|---|---|---|---|---|
| §3 | Five claim levels, one guarded emitter each, L5 permanently withheld | `analysis/claims.py` | T10 | done |
| §3, §28.1 | Fifteen-row outcome vocabulary as a fixed mapping | `claims.OUTCOME_VOCABULARY` | T10 | done |
| §4 | The block is the unit; order balanced within block | `topics/split.py`, `design/cells.py` | T4, T9 | done |
| §5 | Excluded phenomena; no L5 code path | `claims.assert_no_l5_emitter` | T10 | done |
| §6.1 | Four replications, registered order, no early stop | `models/registry.py` | T2, anti-regression | done |
| §6.1 | Signed study-wide registration manifest, before the first qualification | `stages/registration.py` | T12 | done |
| §6.1 | A model-adaptive value never appears in a study-wide rule | `registration.assert_no_model_adaptive_values` | T12 | done |
| §6.1 | Cross-replication firewall, asserted statically | `protocol/constants.py` (no filesystem access), `models/registry.py` (reads no record) | T1 | done |
| §6.2 | 624 newly authored topics, 52 per area, four authoring rules | `topics/bank.py`, `tools/build_topics_v4.py` | T4 | done |
| §6.2 | Seeded five-way split 2/8/2/32/8; all disjoint | `topics/split.py` | T4 | done |
| §6.2 | Sequestered text inaccessible | `topics/sequestered.py` | T4 | done |
| §7.1 | A and B, grids n∈1..8 and m∈{7,8,9,10} | `verifiers/constraints.py` | T3 | done |
| §7.2 | Eight families, complete integer ladders, 94 severities | `verifiers/constraints.py` | T3 | done |
| §7.2 | Registered lexical convention | `verifiers/words.py` | T3, T5 | done |
| §7.3 | Parse independence, checked on signatures | `verifiers/wording_suite.py` | T5 | done |
| §7.3 | Joint satisfiability and non-entailment, all pairs | `verifiers/witnesses.py` | T3 | done (4,910 pairs) |
| §7.3 | Four frozen wordings, identical verdicts on twenty responses | `protocol/wordings.py`, `verifiers/wording_suite.py` | T3, T5 | done |
| §7.3 | Wording length within 20% of **A**, severity-invariant | `wordings.length_caliper_ok`, `assert_severity_invariance` | T3 | done — see §3 |
| §7.4 | Graded score per constraint form | `verifiers/compliance.py` | T3 | done |
| §8.1 | 25 cells: 5 solo, 10 pairs × 2 orders | `design/cells.py` | T4 | done |
| §8.2 | M = 4, all draws enter the cell mean, no selector | `analysis/observations.py`, `protocol/seeds.py` | T7, anti-regression | done |
| §8.3 | 384 blocks; 38,400 per model; greedy 1,920 at temperature 0 | `stages/confirmatory.py` | T7 | done, not executed |
| §8.4 | Order cell-level; wording block-level with the offset formula | `design/cells.py`, `topics/split.py` | T4 | done |
| §8.4 | Allocation assertion refuses a structural zero | `cells.assert_allocation` | T4 | done |
| §8.5 | Prompt template; byte-identity outside the other constituent | `design/prompts.py` | T4 | done |
| §8.6 | Reduced design when references are not identified | `cells.full_slots`, `stages/gates.gate3_payload` | T6, T7 | done |
| §9.1 | The compliance vector is the primitive; nothing marginalised | `generation/cache.compliance_row` | T4 | done |
| §9.2 | S0 and the three registered alternatives | `verifiers/target.py` | T3 | done |
| §9.3 | Degeneracy record; non-vacuity predicates; vacuous passes stay passes | `verifiers/compliance.py` | T3 | done |
| §10.1 | No language model produces a behavioural score | `stages/autorater.py` (separate artifacts) | T5 | done |
| §10.2 | Determinism 1.000 over three processes | `stages/gate1.three_process_determinism` | T5 | done |
| §10.2 | Boundary suite per verifier, ≥40 cases, §24 coverage | `verifiers/boundary.py` | T5 | done (A 48, others 45) |
| §10.2 | Independent reimplementation from the prose alone | `verifiers/independent.py` | T5 | done |
| §10.2 | Carry-over: construct string, both function sources, forty cases | `verifiers/carryover.py` | T1, T5 | done |
| §10.3 | Wilson bound with the fail-class margin split | `analysis/intervals.py`, `gate1.human_agreement` | T5 | done |
| §10.3 | Blinded annotation interface, five instruments | `annotation/packets.py` | T5 | done |
| §10.4 | Autorater pathway: split, judge registry, serialised, one-shot | `stages/autorater.py` | T5 | done, judge not executed |
| §10.4 | A v4 reserved final-check set sealed at Gate 1 | `gate1.seal_final_check_set` | T5 | done |
| §10.5 | Three-value measurement basis; scope sentence verbatim | `protocol/constants.py`, `analysis/claims.py` | T5, T10 | done |
| §10.6 | One canonical verifier hash, eleven bound entry points | `verifiers/__init__.py`, `engine/binding.py` | T8 | done |
| §11.1 | Cell mean over all M draws; configuration semantics | `analysis/observations.py` | T9 | done — see §4 |
| §11.2 | Delivery loss, paired within block | `analysis/estimators.py` | T9 | done |
| §11.3 | Four primary estimands; Δ_R in the cancelled form | `estimators.delta_r`, `assert_delta_r_forms` | T9 | done |
| §11.4 | The position caveat on every L1 | `claims.emit_l1` | T10 | done |
| §11.5 | Secondary estimands; both R̄ aggregation rules asserted | `analysis/estimators.py` | T9 | done |
| §11.6 | Thresholds and regions with their four distinct provenances | `protocol/constants.py`, `stages/freeze.THRESHOLD_PROVENANCE` | T13, anti-regression | done |
| §12.1 | Cap set at loads 0/1/2; zero-constraint rate separate; bound rule | `stages/regime.py`, `analysis/diagnostics.bounded` | T6 | done |
| §12.2 | Dense ladder screen, 2,544; shortlist before Gate 2 | `stages/regime.py` | T6 | done |
| §12.3 | n\* and m\* with the exact-tie rule | `stages/gates.select_severity` | T6 | done — see §5 |
| §12.4 | Regime adequacy; REGIME_NOT_FOUND | `gates.gate2_payload` | T6 | done |
| §13.2 | Admission: matched to A on compliance, six conditions | `gates.admit_family` | T6 | done |
| §13.2 | Newcombe interval for the paired difference | `analysis/intervals.newcombe_paired` | T5 | done — see §6 |
| §13.4 | Reference heterogeneity qualifier | `claims._l3_qualifiers` | T10 | done |
| §13.5 | Fewer than three references is not terminal | `gates.gate3_payload` | T6 | done |
| §13.6 | Composed headroom, cell by cell, no contrast | `gates.gate4_payload` | T6 | done |
| §14.1 | Block bootstrap; no draw-level index in any estimator | `analysis/bootstrap.py` | T9 | done |
| §14.2 | No exclusions; retry; fail closed; missingness; duplicates | `generation/cache.py`, `analysis/diagnostics.py` | T7, T13 | done |
| §14.2 | Deprecated-and-foreign guard | `engine/guards.py` | T1 | done |
| §15 | Seven families; simultaneous intervals per configuration | `estimators.family_members`, `bootstrap.bootstrap_family` | T9 | done |
| §16.1 | The variance model | `analysis/variance.py` | T9 | done, reproduces §16.2/§16.3 |
| §16.3 | The menu rule; every row live | `variance.select_allocation` | T9, anti-regression | done, reports only |
| §17.1 | 10,000 resamples, studentised maximum modulus | `analysis/bootstrap.py` | T9 | done |
| §17.3 | Equivalence guard with its precondition; abort | `claims.emit_equivalence` | T10 | done |
| §17.4 | F6 gate; vacuity-forced recomputation; both-bounds rule | `analysis/run.f6_gate`, `claims._partial_identification_agrees` | T9 | done |
| §17.5 | Seven machine fields; the two refusal checks | `analysis/claims.py` | T10 | done |
| §18 | The stage machine; predecessor hash and signature | `engine/transitions.py`, `engine/dispatch.py` | T6 | done |
| §18.1 | The freeze record and its completeness check | `stages/freeze.py` | T12 | implemented, not executed |
| §19 | The procedural pilot and its eight acceptance conditions | `stages/pilot.py` | T13 | done |
| §20 | Companion-label masking; one-way unmask; declared limitation | `analysis/masking.py` | T11 | done |
| §21 | The analysis in its fixed order; fail closed | `analysis/run.py` | T14 | done |
| §22 | Prohibited and mediating quantities | `protocol/codebook.py`, `diagnostics.length_strata_description` | T9, T12 | done |
| §23 | Secondary analyses and the failure taxonomy split by margin | `analysis/diagnostics.py` | T11, T13 | done |
| §23 | The primary estimands recomputed under S1, S2 and S3 | `run.alternative_rule_recomputation` | T9 | done |
| §23, §11.5 | Δ^A behind its three gates, withheld when any fails | `diagnostics.report_delta_a` | T9 | done |
| §11.5 | Joint-state redistribution across configurations | `diagnostics.joint_state_redistribution` | T11 | done |
| §24 | Segmentation and construct-validity checks | `verifiers/boundary.py`, `verifiers/adversarial.py` | T5 | done |
| §25 | Contamination controls; accidental compliance | `stages/release.py`, `diagnostics.accidental_compliance` | T13 | done |
| §26 | Artifact states; the closed vocabulary; one path function | `engine/{artifacts,paths,verify}.py` | T12 | done |
| §27 | Codebook and its four checks; the environment record | `protocol/codebook.py`, `engine/environment.py` | T12 | done |
| §28 | Terminal and identification statuses; the verbatim sentence | `protocol/constants.py`, `engine/transitions.py` | T6 | done |
| §30 | The machine-readable result table | `analysis/results.py` | T12 | done |
| §31 | The append-only amendment register | `stages/amendments.py` | T12 | done |
| §33 | The nine open decisions | `stages/freeze.OPEN_DECISIONS` | anti-regression | not decided, by design |

## 3. Authoring decision: the family wordings are not the §7.2 table strings

§7.3 and §13.2 condition 3 require every reference wording to be within 20% of
**A**'s wording of the same index in alphabetic-run word count. A's canonical
wording is six words. The family templates printed in the §7.2 table are eleven
to twelve words, so **no family stated in the table's own words could ever be
admitted**, at any severity, for any model.

The four frozen wordings per family are therefore authored to state each
family's registered rule compactly enough for the caliper to be satisfiable.
The §7.2 table text is retained verbatim in
`wordings.FAMILY_RULE_STATEMENTS` as the definition of what each family means,
and `assert_rule_vocabulary` checks every authored wording against it, at every
severity. `assert_caliper_feasible` proves that every one of the 94 registered
severities meets the caliper at every registered n.

**This is visible and is for the researcher to confirm**: wording index 0 is
the §7.2 table string for A and for B, and is not for the eight families.

## 4. Interpretation: what a configuration is

§11.1 defines a configuration as (model checkpoint, instruction order). Two
readings are possible once order is a cell-level factor, and §11.4 decides
between them: "Δ-type quantities difference two composed cells with c in the
same position and are position-clean **in both configurations**."

Under a registered-slot-order reading, Δ_R would difference `D(B ← A)` with B
second against `D(B ← R_j)` with B first, and would not be position-clean. So
the configuration fixes the **position of the outcome constraint**:
`outcome_first` and `outcome_second`. Every pair runs both order variants in
every block, so each configuration is estimated on all 384 blocks, and the
position-shifted configuration is the one that carries `POSITION_CONFOUNDED`.

## 5. Implementation detail: the exact-tie rule and floating point

§12.3 and §13.2 register tie-breaks that fire on an **exact** tie. Binary
floating point does not represent 0.70 or 0.05 exactly, so two mathematically
equal distances can compare unequal in the twelfth decimal and silently decide
a selection the protocol says a tie-break decides. Every selection key is
rounded at `gates.TIE_PRECISION` before comparison, far below any rate the
design can measure. Without this, an A curve of 0.75 and 0.65 selects the
larger n rather than the smaller one.

## 6. Implementation detail: the Newcombe pairing

§13.2 condition 1 requires the 95% Newcombe interval for the paired difference
to intersect ±0.05. Newcombe's method needs a paired 2×2 table and the
calibration data are cell means over M draws. The registered pairing is stated
in `analysis/intervals.py`: a draw of the A solo cell is paired with the draw
of the same index on the same topic, giving 96 × M paired observations. Draws
are exchangeable within a cell, so the index is a labelling convention rather
than a scientific choice, and the clustered paired standard error is reported
beside the interval so the dependence the pairing ignores stays visible.

## 7b. Interpretation: the anchor the ladder shortlist is built against

§12.2 produces "the shortlist of at most three ladder severities per family
whose solo compliance is nearest the pre-screen solo compliance of A". A has
eight registered severities and n\* is not selected until Gate 2, so "the
pre-screen solo compliance of A" needs an n. The runner uses the n whose
pre-screen compliance is nearest the §12.3 aim of 0.70 — the value Gate 2 will
itself minimise distance from — and records it as `anchor_n` on the regime
record, so the anchor is auditable rather than implicit. The shortlist is a
screening device: §12.3 re-measures every shortlisted severity on the 96
calibration topics against A at the selected n\*, and §13.2 admits against
that.

## 7c. A measured tension between two §13.2 conditions

On the E2B pre-screen, **every** rung that matches A on solo compliance
(condition 1) fails the family solo vacuity condition (condition 6): 0 of 13
survive, 0 of 8 families remain viable. The mechanism is structural rather than
incidental — A's solo compliance is low, so matching it needs a restrictive
"at most q", and a restrictive budget constraint is satisfied by writing a
shorter answer. 1,150 of the 1,153 vacuous passes are short answers, not
truncations.

This is a screening sample, not the admission decision: §13.2 is evaluated at
Gate 2 on 96 topics at M = 4. But it is decision-relevant for V3 (the caliper),
V4 (the 20-word threshold) and V5 (matched versus difficulty-spanning
references), and it is recorded rather than resolved. See
`dci1/docs/v4_prefreeze/C10.json`.

## 7. What blocks the freeze

Every item here is recorded in `dci1/docs/v4_prefreeze/` with its evidence.

**Registered open decisions, all nine.** V1 to V9 are the researcher's and
none may be decided after any confirmatory generation. The implementation runs
each registered default so the system is executable, and reports what the
registered rule selects; it decides only V6, which Gate 3 decides
mechanically per model.

**Pre-freeze checks not COMPLETE.**

| Check | Status | What is missing |
|---|---|---|
| C3 | BLOCKED | No annotator independent of the design and analysis team; and the judge comparison has not been executed |
| C7 | BLOCKED | Whether a reference severity matched to A exists in each family ladder is empirical and needs the §12.2 screen per model |
| C8 | BLOCKED | Neither Qwen model's operating regime exists yet |
| C10 | BLOCKED | Realised vacuity rates at the 20-word threshold need real calibration cells |
| C11 | BLOCKED | Accidental compliance and per-cell truncation need real generations |
| C12 | PARTIAL | The A-versus-reference correlation is not recoverable from any existing corpus |
| C14 | PARTIAL | The realised v4 duplicate rate needs v4 generations |

## 8. What is deliberately not executed

* **Gate 5, the freeze.** Implemented in `stages/freeze.py` with the
  completeness check that refuses while any required field, any open decision
  or any blocking check is unresolved. `dci1v4 freeze` exits with that message.
* **Confirmatory generation.** Implemented in `stages/confirmatory.py` and
  refuses without a Gate 5 record.
* **The v3 sealed final-check set.** Not opened, and unreachable from this
  package.
* **The v4 sequestered 96.** Held as opaque identities and content hashes; the
  authoring source is retained outside version control.
