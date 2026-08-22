# DCI-1 v5 — implementation status

What exists in `dci1/src/dci1v5/`, what it can and cannot do, and the ordered
list of researcher actions between here and a v5 that may measure anything.

> **v5 is DRAFTED, NOT ADOPTED.** No v5 stage record exists, no v5 topic has
> been authored, no v5 instrument has been measured, no v5 generation exists.
> `protocol/decisions.py` carries §34's nineteen decisions, every one
> `UNRESOLVED`, and `engine/transitions.assert_transition_legal` refuses a
> stage whose decisions are open. `PROTOCOL_REGISTERED` depends on **all**
> nineteen, so the lifecycle is closed at stage 1 by construction. That is the
> intended state and `REGISTRATION_INCOMPLETE` is its registered name.

---

## 1. What runs today, and what it says

```
$ python3 -c "from dci1v5.stages.audit_prefreeze import run_prefreeze_audit
              a = run_prefreeze_audit(repo_root='..')
              print(a['outcome'], a['n_passed'], '/', a['n_checks'])"
PREFREEZE_AUDIT_FAILURE 12 / 15
```

Twelve of §33's fifteen checks pass statically. Three return `UNRESOLVED`
because they need a run that has not happened: check 8 needs a Gate-4 record,
check 14 a final-report table, check 15 the v5 artifact texts. **An
`UNRESOLVED` check is not a pass** — "we did not establish this" and "this is
false" are different facts and neither licenses a freeze. Beside them the
audit reports nineteen open decisions and five unresolved red-team findings,
and `can_freeze` is `False`.

Gate 5 is unreachable and needs no special rule: §18 makes `PREFREEZE_AUDIT`
its registered predecessor, and `assert_predecessor_passed` refuses a
successor whose predecessor did not record `PASS`.

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
| `topics/__init__.py` | §6.2 | the bank's shape, the authoring rules, and the 96 questions that do not exist |

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

### Not written

The `run/` layer — the CLI runners that drive a real evidence tree, generate
rows and write signed stage records. Nothing above needs it to be checked, and
writing it would produce the one thing this pass must not produce: a path that
looks ready to spend model data. It is the first item of §5 below.

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

## 4. The nineteen open decisions, and what each blocks

| # | Decision | Blocks stage | Blocks call | Red team |
|---|---|---|---|---|
| **D0** | whether to adopt v5 at all | `PROTOCOL_REGISTERED` | — | — |
| **D1** | the confirmatory compute budget | `PROTOCOL_REGISTERED` | `design.cells.admitted_arms_from_decision` | R1 |
| **D2** | whether a load-three arm is added | `PROTOCOL_REGISTERED` | — | — |
| **D3** | whether the 96 Calibration-B questions are authored before adoption | `PROTOCOL_REGISTERED`, `QUALIFIED` | `topics.calibration_b_bank` | — |
| **D4** | the Tier-1 marker vocabulary | `PROTOCOL_REGISTERED`, `REGIME_SCREEN` | `constraints.assert_marker_vocabulary_approved` | — |
| **D5** | weighted composite score vs the lexicographic conjunction | `PROTOCOL_REGISTERED` | — | — |
| **D6** | is `REFERENCE_SUPPORT_NOT_IDENTIFIED` terminal? | `PROTOCOL_REGISTERED`, `GATE_3C_IDENTIFICATION` | `support.support_disposition` | **R16** |
| **D7** | the interaction ceiling of 0.90 | `PROTOCOL_REGISTERED` | — | R13 |
| **D8** | the chance ceiling of 0.75 | `PROTOCOL_REGISTERED` | — | — |
| **D9** | whether an independent annotator will be available | `PROTOCOL_REGISTERED` | — | — |
| **D10** | whether the broad-class arm carries more than one companion | `PROTOCOL_REGISTERED` | — | — |
| **D11** | whether the confirmatory topics are re-authored | `PROTOCOL_REGISTERED` | — | — |
| **D12** | whether δ_diff or an order contrast gets its own magnitude threshold | `PROTOCOL_REGISTERED` | — | — |
| **D13** | whether F11 is primary-tier | `PROTOCOL_REGISTERED` | — | — |
| **D14** | whether ι remains the difficulty coordinate | `PROTOCOL_REGISTERED` | — | — |
| **D15** | whether the memo's 0.10 and 0.25 apply to a same-form Δ_R | `PROTOCOL_REGISTERED` | — | R2 |
| **D16** | which population Calibration-B measures | `PROTOCOL_REGISTERED`, `GATE_3A_REFERENCE_CALIBRATION` | `stability.calibration_b_population` | **R11** |
| **D17** | whether a construct floor is registered for m* | `PROTOCOL_REGISTERED`, `GATE_2_FOCAL_CALIBRATION` | `regime.assert_construct_floor` | **R14** |
| **D18** | whether the near-form arm is a precondition of L3c | `PROTOCOL_REGISTERED`, `UNMASKED_ANALYSIS` | `claims.l3c_requires_near_form` | **R1** |

`decisions.close(id, value, evidence=..., decided_by=..., decided_on=...)`
requires all four arguments, refuses a value the decision does not offer, and
is write-once: a closure without evidence is a default with a signature on it.

**D17's `floor` branch refuses even when closed**, because a construct floor
is a registered value with a derivation and this implementation does not
invent one — the closure must supply the threshold and the quantity it applies
to.

---

## 5. The minimum ordered list before v5 may measure anything

1. **Write the `run/` layer.** Stage runners over a real evidence tree,
   signing, durable mirroring, cache and restore. Everything above is
   exercised by it and nothing above needs it to be *checked*.
2. **Author the 96 Calibration-B questions** (D3). §13.7 — v5's whole answer
   to the winner's curse §12.2 measures — does not work without them. This is
   the largest non-compute prerequisite in the protocol.
3. **Close D4** (the marker vocabulary), which the regime screen needs before
   it measures a marker rung, and **D17** (the construct floor), which Gate 2
   needs.
4. **Close D6, D16 and D18**, which the red team's R16, R11 and R1 turn on.
   D18 is the one that decides whether v5 can emit the source memo's
   refutation verdict against a control pool chosen to resemble A.
5. **Close D1** — the compute budget. If it drops the near-form arm, R1 loses
   its only mitigation, and D18 should then be closed at `precondition`.
6. **Close the remaining decisions** and record every closure, with its
   evidence, in the signed registration manifest.
7. **Regenerate Gate 1 evidence over the 650-instrument population.** The long
   pole in wall-clock and it depends on no model.
8. **Run §19's procedural pilot** on twelve pre-screen topics over the full
   admitted cell plan, with the claim-ladder tests passing *before*
   qualification — §20's commitment device means an emitter defect found after
   the mask is sealed cannot be repaired, which is exactly what happened to
   v4r4's L4.

Only then does `PROTOCOL_REGISTERED` become reachable.

---

## 6. Tests

`dci1/tests_v5/`, 225 tests, all passing, in about two seconds. The categories
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

`tests_v4r4/` is unchanged and still passes 594 with 6 skips, including
`test_l4_replication_defect.py`, which pins v4r4's sealed behaviour so that
v5's fix cannot silently rewrite what v4r4 did.
