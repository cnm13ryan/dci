# DCI-1 v5 — implementation status

What exists in `dci1/src/dci1v5/`, what it can and cannot do, and the ordered
list of researcher actions between here and a v5 that may measure anything.

> **v5 is ADOPTED AND REGISTERED.** All nineteen §34 decisions carry a value,
> U2 is resolved at A2, P1 is confirmed, `manifest.signing_blockers()` returns
> `[]`, and the registration manifest is signed. **No v5 instrument has been
> measured and no v5 generation exists**: adoption fixes the rules, it does not
> start the study. `protocol/decisions.py` and `protocol/open_items.py` both
> read the committed record at import, so what the code does and what the
> researcher decided are one fact rather than two that have to be kept equal.
>
> **The first registration was superseded on 2026-08-23**, before Stage 2 and
> with no observation under it. The pre-execution sweep found three defects
> that made the registered lifecycle unexecutable as committed — three of four
> models could not obtain a stage-1 record, the pinned backend was unreachable
> from four of the five generating stages, and a row's `synthetic` flag
> recorded the call shape rather than what wrote the text. No registered
> scientific value changed. See `CHANGES_SCIENTIFIC.md` and
> `tests_v5/test_amendment_pre_data.py`.

---

## 1. What runs today, and what it says

```
$ python3 -c "from dci1v5.stages.audit_prefreeze import run_prefreeze_audit
              from dci1v5.protocol.reuse_ledger import collect_artifact_texts
              a = run_prefreeze_audit(repo_root='..',
                                      artifact_texts=collect_artifact_texts('..'))
              print(a['outcome'], a['n_passed'], '/', a['n_checks'])"
PREFREEZE_AUDIT_FAILURE 13 / 15
```

`artifact_texts` is not optional decoration: with none supplied, check 15
scans nothing and returns `UNRESOLVED`, and the audit reports 12 of 15. The
stage runner (`run/prefreeze_run.py`) supplies them from
`reuse_ledger.collect_artifact_texts`, which refuses a missing named file ---
a text check that silently scans nothing is not a check.

Thirteen of §33's fifteen checks pass statically. Two return `UNRESOLVED`
because they need a run that has not happened: check 8 needs a Gate-4 record
and check 14 a final-report table. **An `UNRESOLVED` check is not a pass** —
"we did not establish this" and "this is false" are different facts and
neither licenses a freeze.

Beside them the audit now reports **zero** open decisions and **zero**
red-team findings whose mitigation is an open decision: all nineteen are
taken, and R1, R11, R14 and R16 are resolved by D18, D16, D17 and D6. R5 is
reported separately as a **permanent limitation**, which is a different thing
from a resolved finding and is why the two lists exist. `can_freeze` is still
`False`, and now for one reason only: check 8 has no Gate-4 record to read,
because no Gate 4 has run.

Gate 5 is unreachable and needs no special rule: §18 makes `PREFREEZE_AUDIT`
its registered predecessor, and `assert_predecessor_passed` refuses a
successor whose predecessor did not record `PASS`.

**Only check 14 is deferred.** It reads the final-report table and no table
exists at stage 12, so it is recorded `DEFERRED_TO_FINAL_REPORT` and is
mandatory at stage 18, where `run/final_report_checks.py` discharges it beside
thirteen traceability checks that only become checkable once the table exists
--- one of which is §34 D6's: no reported row may carry an estimate for a
member Gate 3C marked `NOT_IDENTIFIED`.
Check 15 is **not** deferred: it scans the v5 artifact texts, which exist from
stage 1, and `reuse_ledger.collect_artifact_texts` supplies them.

### The lifecycle has been walked end to end, with no model

`dci1/tests_v5/synthetic_lifecycle.py` executes all eighteen stages in the
`synthetic` namespace — study id `dci1v5-synthetic`, its own signing key, a
temporary evidence root, an isolated repository at a clean synthetic producing
commit — and writes eighteen signed records:

| | Stage | What the walk establishes |
|---|---|---|
| 1 | `PROTOCOL_REGISTERED` | the manifest binds; refuses to sign while a decision is open |
| 2 | `QUALIFIED` | all seventeen §19 checks, **none waived** |
| 3 | `GATE_0_APPARATUS` | §19's pilot: every cell and draw once, a mutated byte refused, a durable restore, a mask cycle |
| 4 | `REGIME_SCREEN` | cap selection, the §12.2 screen, retention, coverage, §12.7 priority |
| 5 | `GATE_1_MEASUREMENT` | the verifier **and** wording hashes frozen; §10.2's five provenance facts |
| 6 | `GATE_2_FOCAL_CALIBRATION` | n\*, m\*, both calibration splits, κ(R\|B) off the B-solo rows |
| 7 | `GATE_2_5_CANDIDATE_QUALIFICATION` | the qualified pool with every candidate's earliest failing component |
| 8 | `GATE_3A_REFERENCE_CALIBRATION` | the two split tables and §13.7's stability verdicts |
| 9 | `GATE_3B_REFERENCE_SELECTION` | the four pools and the slot map |
| 10 | `GATE_3C_IDENTIFICATION` | arms `base + core + spectrum`, 44 cells, support met, 3 Tier-1 core references |
| 11 | `GATE_4_COMPOSED_HEADROOM` | every registered cell type on every slot, inside the band |
| 12 | `PREFREEZE_AUDIT` | 26 artifact checks and §33's fifteen; `can_freeze` true |
| 13 | `GATE_5_FREEZE` | every §18.1 field from a signed source |
| 14 | `CONFIRMATORY_GENERATION` | the complete draw matrix: every (block, cell, draw) exactly once |
| 15 | `MASKED_ANALYSIS` | the sealed masked artifact, §20's withheld members recorded by name |
| 16 | `UNMASKING` | once; a second attempt is refused by the stage machine |
| 17 | `UNMASKED_ANALYSIS` | every registered quantity with a status, `NOT_IDENTIFIED` never zero |
| 18 | `FINAL_REPORT` | §31's table, every field traced, and stage 18's own thirteen checks |

**This is engineering evidence only.** The fixtures are engineered to be
satisfiable, which is what makes them useful for finding plumbing defects and
useless as evidence about a model. It says the v5 execution plumbing has been
exercised end to end on synthetic fixtures. It says nothing about whether v5's
matching procedure will work prospectively on a real model.

---

## 2. Modules

### New machinery (nine pieces the plan classed C, plus three the plan did not name)

| Module | § | What it is |
|---|---|---|
| `protocol/decisions.py` | §34 | D0–D18 as executable state; both branches of every choice exist and neither is reachable while the decision is open |
| `protocol/taxonomy.py` | §7.3, §7.4 | thirteen metadata fields, the tier rule computed from the record, the slot table |
| `protocol/reuse_ledger.py` | §30 | the five classifications, the seven invariants, the two measured ones, and the "validation" text check |
| `protocol/revision.py` | — | the sixteen v4r4 → v5 changes, eleven with executable checks that assert the change was actually made |
| `stages/validity.py` | §13.1 | `V(R)`: eight components, lexicographic **reason**, order-independent verdict, ι last |
| `stages/interaction.py` | §13.6 | κ(R\|B), displacement, projection, and seven hard source refusals |
| `stages/stability.py` | §13.7 | two splits, the equivalence rule, D16's two populations |
| `stages/calibration_table.py` | §13.11 | the closed schema, the forbidden-field list, the κ(R\|B) source validation |
| `stages/qualification_gate.py` | §18 s7 | Gate 2.5: the qualified pool with every candidate's earliest failing component |
| `stages/support.py` | §13.15, §26 | oversupply, frozen backups, the arm set, the success criterion |
| `stages/audit_prefreeze.py` | §18 s12, §33 | the fifteen checks, the open decisions, the unresolved red-team findings |
| `stages/final_report.py` | §18 s18, §31 | the result table, every number traced to a v5 stage record |
| `verifiers/realistic_witness.py` | §7.7 | the stem-band obligation, with padding and trimming that preserve sentence structure |
| `analysis/intervals.py` | §13.4, §13.7, §13.8 | Wilson, Newcombe, the percentile bootstrap over topics within split |
| `engine/guards.py` | §14.2 | positive admission, in both directions |
| `topics/__init__.py`, `topics/calibration_b.py` | §6.2 | the bank's shape, the authoring rules, and the 96 authored Calibration-B questions with their provenance |

### Adapted from v4r4

`protocol/constants.py` (every threshold, eighteen stages, F1–F11),
`protocol/wordings.py` (Tier-1 templates **derived** from A's rather than
retyped; B's four strings re-derived as `{m}` templates over the widened
grid), `verifiers/constraints.py` (37 families, thirteen metadata fields per
family, the counts asserted), `verifiers/statistics.py` (+ eight marker
numerators as one function with eight targets), `verifiers/compliance.py`
(+ `assert_presence_rule`), `verifiers/independent.py` (+ the eight markers,
transcribed line by line), `verifiers/boundary.py` (+ the v5 marker group and
the four marker phenomena), `verifiers/witnesses.py` (tier-based
realisability; `joint_witness` generalised — see the reconciliation report
F3), `design/cells.py` (arms → cells, no named variants), `stages/regime.py`
(high-recall screen, bracketing, coverage, expansion by restrictiveness),
`stages/selection.py` (the four pools, the tie-break, the role substitution),
`analysis/estimators.py` (+ five order contrasts, Δ_near, Δ_broad,
counterfactual chance), `analysis/observations.py` (presence-aware, so κ(c|B)
has a home), `analysis/spectrum.py` (+ the tier-indicator secondary),
`analysis/claims.py` (`emit_l4a` per named member, `emit_l4b`, §17.6's second
table), `engine/{context,paths,transitions}.py`, `stages/freeze.py`.

### Carried and re-tested unchanged

`verifiers/words.py`, `verifiers/boundary_r3.py`, `verifiers/adversarial.py`,
`verifiers/wording_suite.py`, `analysis/{bootstrap,masking}.py`,
`stages/{specification,mutation,gate1,verifier_audit,microcase}.py`,
`design/prompts.py`, `protocol/seeds.py`.

### Deliberately **not** carried

`stages/library.py`. It is keyed on v4r4's `role` field, which v5 replaces
with the structural tier, and everything it did is in `stages/regime.py` under
v5's rules.

### The `run/` layer

Thirteen modules driving a real evidence tree, all eighteen stages on one
driver — guard, verifier hash, compute, sign write-once, mirror, log — plus a
CLI. `run/cli.assert_every_stage_has_a_runner()` is asserted at import, so §18
gaining a stage without a runner is an import failure.

| Module | Stages | What it does |
|---|---|---|
| `run/lifecycle.py` | all | the five-step driver, terminal statuses, durable mirroring, the transition log (refusals logged too) |
| `run/contracts.py` | all | the producer/consumer contract: 95 fields over 17 artifacts, and the five defect classes it detects |
| `run/execute.py` | generative | prompt cell → plan → generate → score → row identity, §9.1 asserted per row |
| `run/registration_run.py` | 1 | plans without writing; refuses to build a payload while §34 is open |
| `run/qualification_run.py` | 2, 3 | the seventeen checks and §19's pilot |
| `run/regime_run.py` | 4, 5 | cap, screen, retention, coverage; Gate 1 freezes the verifier and wording hashes |
| `run/gates_run.py` | 6–11 | Gate 2 through Gate 4, in four separated stages with four records |
| `run/prefreeze_run.py` | 12 | 26 artifact checks over signed records, plus §33's checklist. **Nothing is waivable** |
| `run/freeze_run.py` | 13 | every §18.1 field assembled from a signed source, and the downstream assertion against it |
| `run/confirmatory_run.py` | 14 | the licensed design, batching, resume, completeness |
| `run/analysis_run.py` | 15–18 | mask, unmask, estimate, report |
| `run/final_report_checks.py` | 18 | §33's deferred check 14 and twelve traceability checks the table makes checkable |

Nothing in it can run today: `PROTOCOL_REGISTERED` depends on all nineteen
decisions and `assert_transition_legal` refuses a stage whose decisions are
open, so every runner refuses at stage 1.

---

## 3. What was measured rather than assumed

| Claim | How it was checked | Result |
|---|---|---|
| the library sizes | `constraints.assert_library_sizes()` | 37 families, 326 round-0, 632 declared, **650 instruments in 39 verifiers** |
| the carried numerators are v4r4's | both revisions run over the whole frozen corpus | 2,655 comparisons, agreement **1.000** |
| the boundary suite | primary verifiers against every frozen expectation | 2,076 checks, **0 failures** |
| the marker expectations | `tools/v5_freeze_marker_boundary.py`, each computed twice | primary and reimplementation agree on every case; the file reproduces exactly |
| §7.7's formal obligations | `witnesses.run_witness_suite()` | **20,332 realisable pairs, 0 joint and 0 non-entailment failures** |
| §7.7's realistic obligation | `realistic_witness.run_realistic_suite()` | `CL7:125, 130, 135, 140` unreachable; nothing else in the library |
| the sixteen registered changes | `revision.assert_changes_realised()` | eleven have executable checks; all realised |
| the wording caliper | `wordings.assert_caliper_feasible()` | every one of the 632 declared severities is inside 20% of A |

---

## 4. The nineteen decisions: all taken

**All nineteen are closed**, durably, in
[`researcher_decisions.json`](researcher_decisions.json) — read at import by
`protocol/decisions.py` and bound into the manifest by hash, together with
U2's and P1's resolutions, which `protocol/open_items.py` reads from the same
file. Every blocked stage and call is unblocked. The `blocks stage` and
`blocks call` columns below are kept because they are still live: reopening a
decision puts its stages back behind the refusal, and the tests provoke exactly
that rather than trusting a guard nothing exercises.

Three closures went **against** the document's own standing proposal: D16,
D17 and D18. Two more — D7 and D15 — were adopted *over* a recorded red-team
objection that the closure does not answer, and the objection stays beside the
value.

| # | Decision | Blocks stage | Blocks call | Red team |
|---|---|---|---|---|
| **D0** | **TAKEN**: `adopt` — whether to adopt v5 at all | — (closed) | — (closed) | — |
| **D1** | **TAKEN**: `four_models_56_cells` — the confirmatory compute budget | — (closed) | — (closed) | R1 |
| **D2** | **TAKEN**: `no_load_three` — whether a load-three arm is added | — (closed) | — (closed) | — |
| **D3** | **TAKEN**: author before adoption | — (closed) | — (closed) | — |
| **D4** | **TAKEN**: `approve_eight` — the Tier-1 marker vocabulary | — (closed) | — (closed) | — |
| **D5** | **TAKEN**: `lexicographic` — weighted composite score vs the lexicographic conjunction | — (closed) | — (closed) | — |
| **D6** | **TAKEN**: identification status, irreversible | — (closed) | — (closed) | **R16** |
| **D7** | **TAKEN**: `0.90` — the interaction ceiling of 0.90 | — (closed) | — (closed) | R13 |
| **D8** | **TAKEN**: `0.75` — the chance ceiling of 0.75 | — (closed) | — (closed) | — |
| **D9** | **TAKEN**: `unavailable` — whether an independent annotator will be available | — (closed) | — (closed) | — |
| **D10** | **TAKEN**: `one_companion` — whether the broad-class arm carries more than one companion | — (closed) | — (closed) | — |
| **D11** | **TAKEN**: `carry` — whether the confirmatory topics are re-authored | — (closed) | — (closed) | — |
| **D12** | **TAKEN**: `direction_and_sesoi_only` — whether δ_diff or an order contrast gets its own magnitude threshold | — (closed) | — (closed) | — |
| **D13** | **TAKEN**: `primary_tier` — whether F11 is primary-tier | — (closed) | — (closed) | — |
| **D14** | **TAKEN**: `iota_primary` — whether ι remains the difficulty coordinate | — (closed) | — (closed) | — |
| **D15** | **TAKEN**: `both_transfer` — whether the memo's 0.10 and 0.25 apply to a same-form Δ_R | — (closed) | — (closed) | R2 |
| **D16** | **TAKEN**: complete population | — (closed) | — (closed) | **R11** |
| **D17** | **TAKEN**: `floor` — whether a construct floor is registered for m* | — (closed) | — (closed) | **R14** |
| **D18** | **TAKEN**: precondition of the strong L3c | — (closed) | — (closed) | **R1** |

`decisions.close(id, value, evidence=..., decided_by=..., decided_on=...)`
requires all four arguments, refuses a value the decision does not offer, and
is write-once: a closure without evidence is a default with a signature on it.

**D17's `floor` branch refuses even when closed**, because a construct floor
is a registered value with a derivation and this implementation does not invent
one. The closure supplied the four things it needs — quantity
(`chance_compliance`), value (0.50), semantics
(`point_estimate_refuses_wilson_reported`) and derivation — as the `spec` field
of the D17 entry in the record; `construct_strength.registered_floor()` reads
them and the module carries no number. `manifest.signing_blockers()` reports
`FLOOR_NOT_SPECIFIED` if a `floor` closure ever arrives without them.

**A closure is durable and it is not a module literal.**
`decisions.RECORD_PATH` is a committed file carrying every closure with its
evidence, who took it and when; the registry applies it at import, refuses a
record that disagrees with a closure already in force (that is a §32
amendment), and `reopen_all_for_testing` restores *that* state rather than a
blank one. `override_for_testing` exists so the branch the researcher did not
adopt stays executed by a test rather than merely present in the source; it
writes nothing to the record and cannot reach a run.

**The four decision packets are adopted**: [D1](d1_arm_compute_decision.md),
[D4](d4_marker_audit.md), [D17](d17_b_strength_decision.md),
[U2](u2_tier_model_decision.md). Each carries its status at the top and its
final section says what was taken and what was given up. The three non-adopted
D1 options, D17's `no_floor` branch and U2's A4 all remain constructed and are
named as non-adopted in the manifest — a retained branch is not a live option,
and the distinction is bound rather than described.
[`v5_adoption_checklist.md`](v5_adoption_checklist.md) is the one-page record
of what was taken and what comes next.

---

## 5. The minimum ordered list before v5 may measure anything

**Every researcher approval on this list is done.** What remains is execution:
stage 1 has run, stage 2 reads no behavioural rate, and stage 3 is the first
that generates a model response.

**Done.**

- ~~Author the 96 Calibration-B questions (D3).~~ Authored, audited, hashed,
  committed: `src/dci1v5/topics/data/calibration_b_v5.json`, 96 questions,
  eight per area, disjoint from all five other sets in id and in text.
- ~~Close D6, D16 and D18.~~ Taken 2026-08-22; R1 is resolved by D18, R11
  mitigated by D16, R16 an accepted limitation by D6.
- ~~Close D4 and D17.~~ Taken 2026-08-23. D4 at `approve_eight` with four
  accepted limitations and a population hash; D17 at `floor`,
  $\kappa^{B}(m^{*}) \le 0.50$ on the point estimate, which resolves R14.
- ~~Resolve U2.~~ A2, and §11.8's sentence amended to name the three core
  families explicitly.
- ~~Close D1 and D2.~~ `four_models_56_cells` and `no_load_three`: five arms,
  four models, 56 cells, 384 blocks, $M = 8$, **1,172,544** generations
  derived by `dci1v5.design.budget` from the code's own constants.
- ~~Close the remaining eleven and confirm P1.~~ Each at the document's own
  standing proposal, with R13's and R2's objections recorded beside D7 and D15.
- ~~Sign the registration manifest.~~ `manifest.signing_blockers()` returns
  `[]`.

**Remaining — execution, in order.** Stage 1 has run; it is the stage that
signs the manifest.

1. **Stage 2, `QUALIFIED`.** Non-scientific, reads no behavioural rate.
2. **Stage 3, `GATE_0_APPARATUS`** — §19's procedural pilot at $M = 4$ on
   twelve pre-screen topics. R22's mitigation, and the first stage that
   generates a model response.
3. **Stage 4, `REGIME_SCREEN`**, then **stage 5, Gate 1** over the
   650-instrument population — R23's mitigation, computed over the regime
   screen's own generated text.
4. Stages 6–18, one model at a time in §6.1's registered execution order.

**The pre-adoption list, kept as history.**

1. **Close D4** (the marker vocabulary), which the regime screen needs before
   it measures a marker rung, and **D17** (the construct floor), which Gate 2
   needs. Both have packets: [`d4_marker_audit.md`](d4_marker_audit.md) audits
   all eight markers item by item and
   [`d17_b_strength_decision.md`](d17_b_strength_decision.md) recommends a
   quantity and a threshold on a recomputed curve.
2. **Resolve U2**, §11.8's tier-indicator formulation. `open_items.py` holds
   the four mathematically identified alternatives with what each estimates
   and what each gives up; `fit_with_tier_indicator` fails closed until one is
   adopted, and the registration manifest refuses while it is open.
   [`u2_tier_model_decision.md`](u2_tier_model_decision.md) recommends A2 and
   shows why the alternatives are not reparameterisations of each other.
3. **Close D1** — the compute budget — and **D2** with it, since a load-three
   arm changes the cell set.
   [`d1_arm_compute_decision.md`](d1_arm_compute_decision.md) costs every
   registered option from the code's own constants. Under D18's closure the
   47-cell option cannot emit the strong L3c on any model, so it is a different
   study rather than a cheaper one.
4. **Close the remaining eleven** (D0, D5, D7–D15) and record every closure,
   with its evidence, in the signed registration manifest
   (`protocol/manifest.sign_registration`, which calls `assert_signable`
   before it creates any file or key).
5. **Confirm P1**, §7.10's corrected Tier-3 sentence, at adoption.
6. **Regenerate Gate 1 evidence over the 650-instrument population.** The long
   pole in wall-clock and it depends on no model.
7. **Run §19's procedural pilot** on twelve pre-screen topics over the full
   admitted cell plan, with the claim-ladder tests passing *before*
   qualification — §20's commitment device means an emitter defect found after
   the mask is sealed cannot be repaired, which is exactly what happened to
   v4r4's L4.

Only then does `PROTOCOL_REGISTERED` become reachable.

---

## 6. Tests

`dci1/tests_v5/`, **379 tests**, all passing: the fast ones in about two
seconds and 25 `slow` ones that share one eighteen-stage walk, in about three
minutes. The categories
the implementation prompt registers, and the file each is in:

| | Category | File |
|---|---|---|
| A | namespace and provenance, both directions | `test_isolation.py` |
| B | carried verifiers, measured against v4r4 | `test_carried_verifiers.py` |
| C | taxonomy, and §19 test 5 | `test_taxonomy.py` |
| D | reference validity, and §19 test 3 | `test_validity_order.py` |
| E | interaction, and the seven source refusals | `test_interaction.py` |
| F | stability | `test_stability.py` |
| G | support, and §19 test 4 | `test_support.py` |
| H | design cells, every admissible arm set | `test_design_cells.py` |
| I | order estimands | `test_order_estimands.py` |
| J | L4, and §19 test 1 | `test_l4a_per_member.py` |
| K | lifecycle | `test_lifecycle.py` |
| L | open decisions block execution | `test_lifecycle.py` |
| — | §19 test 2, the closed schema | `test_selection_schema.py` |
| — | §19 test 6, and the claim ladder | `test_claims.py` |
| — | the library and §12's screen | `test_library_and_regime.py` |
| — | selection end to end | `test_selection.py` |
| — | §30's ledger and §31's table | `test_reuse_and_revision.py` |
| — | specification questions as executable state | `test_open_items.py` |
| — | §11.8's tier fit fails closed, and U2's comparison | `test_tier_fit.py` |
| — | the topic bank, and the authored Calibration-B content | `test_topics_calibration_b.py` |
| — | the registration manifest and its refusals | `test_manifest.py` |
| — | §26/§34 D16's reuse key, seven ways it must move | `test_reuse_identity.py` |
| — | D17's construct-strength interface | `test_construct_strength.py` |
| — | the producer/consumer contract, statically | `test_run_contracts.py` |
| — | the pre-data amendment: three defects, one per failure mode | `test_amendment_pre_data.py` |
| — | the run layer refuses while §34 is open | `test_run_layer.py` |
| — | §9.1's verdicts, indexed | `test_row_indexing.py` |
| — | the eighteen-stage walk (`slow`) | `test_synthetic_lifecycle.py` |

`tests_v4r4/` is unchanged and still passes 594 with 6 skips, including
`test_l4_replication_defect.py`, which pins v4r4's sealed behaviour so that
v5's fix cannot silently rewrite what v4r4 did.
