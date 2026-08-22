# DCI-1 v5 — implementation plan

Maps every section of [`DCI1_preregistration_v5.md`](../../../user-notes/DCI1_preregistration_v5.md)
onto the v4r4 modules that implement it today, and classifies each as **A**
reusable unchanged, **B** requiring adaptation, or **C** entirely new
machinery.

**This is a plan, not an implementation.** No v5 code exists. Nothing here
decides a scientific question; every scientific choice is in the
preregistration and in
[`reference_design_spec.json`](reference_design_spec.json), and a coding agent
following this plan should need to invent none.

**The v5 namespace is `dci1/src/dci1v5/`**, mirroring `dci1v4r4/`. §28 requires
it to write nothing inside any earlier evidence tree and to refuse any input
classified foreign, in both directions; `dci1v4r4/engine/context.foreign_roots`
and `assert_own_study` are the pattern.

---

## 0. Summary

| | Modules | Effort |
|---|---:|---|
| **A** reusable unchanged | 14 | copy, re-namespace, re-test |
| **B** requiring adaptation | 12 | edit against a named §-reference |
| **C** entirely new | 9 | write from the spec |

The heaviest new work is in three places: the split-calibration and
interaction machinery (§13.6, §13.7), the arm-derived design plan (§8.1), and
the order estimands with their family (§11.7, §15).

---

## 1. Reusable unchanged — class A

| v4r4 module | v5 §  | Note |
|---|---|---|
| `verifiers/words.py` | §9.2 | the lexical rule, segment-then-fold, and the U+0130 case |
| `verifiers/statistics.py` | §7.6 | every carried numerator; **six marker statistics are added** (class B) |
| `verifiers/boundary.py`, `boundary_r3.py` | §10.2 | frozen suites for carried instruments |
| `verifiers/independent.py` | §10.7 C | the prose-only reimplementation and the Unicode segmenter differential |
| `verifiers/adversarial.py` | §24 | the adversarial corpus |
| `verifiers/witnesses.py` | §7.7 | formal joint-satisfiability and non-entailment; **the realistic witness is new** (class C) |
| `verifiers/wording_suite.py` | §7.8, §10.7 A′ | wording equivalence and the direction lexicon |
| `verifiers/carryover.py` | §10.2, §30 | the carry-over record; v5 uses it for `MK1`, `XC1`, and the `comma` and `sentence` statistics |
| `stages/specification.py` | §10.7 A | the specification audit and its generic predicate evaluator |
| `stages/mutation.py` | §10.7 D | mutation testing over the six defect classes |
| `stages/gate1.py` | §10.7 | the ten-condition Gate-1 rule and the basis refusal |
| `analysis/masking.py` | §20 | the stratified mask, the effectiveness check, the one-shot unmask |
| `analysis/bootstrap.py` | §17.1 | the block bootstrap and the studentised maximum-modulus construction |
| `engine/paths.py`, `engine/context.py` | §28 | the frozen path function, `study_id`, foreign-root refusal |

**One thing to re-run rather than assume.** `statistics.assert_agrees_with_v4r2`
has a v5 analogue: every carried numerator must return v4r4's value on every
stored v4r4 response. §30's ledger requires it as a *measured* finding for the
two carried instruments.

---

## 2. Requiring adaptation — class B

### B1. `protocol/constants.py` → §6, §7, §11.9, §12, §13, §15, §16, §18, §28

Every threshold in the preregistration is a literal and belongs here. New or
moved values, with the section that fixes each:

```
# §6.2                        # §12.6 coverage, all raised
TOPICS_PER_AREA = 60          COVERAGE_MIN_STRADDLING_FAMILIES = 6   # was 4
CALIBRATION_A_PER_AREA = 8    COVERAGE_MIN_NEAR_RUNGS = 8            # was 6
CALIBRATION_B_PER_AREA = 8    COVERAGE_MIN_NEAR_FAMILIES = 4         # was 3
N_CALIBRATION = 192           COVERAGE_MIN_ELIGIBLE_RUNGS = 16       # was 12
                              COVERAGE_MIN_TIER12_FAMILIES = 8       # new
# §7.1                        COVERAGE_MIN_TIER12_GROUPS = 6         # new
FOCAL_GRID = (7,...,14)       COVERAGE_MIN_TIER2_RUNGS = 3           # new
FOCAL_EXTENSION = (15, 16)
                              # §13.4  NEW
# §13.4/§13.6/§13.7           HEADROOM_BAND = (0.10, 0.90)
CHANCE_MAX = 0.75             INSTRUCTION_LIFT_MIN = 0.20
CHANCE_WILSON_UPPER_MAX = 0.85
PROJECTED_COMPLIANCE_BAND = (0.10, 0.90)      # §13.6
DISPLACEMENT_MAX = 0.25                       # §13.6
STABILITY_EQUIVALENCE_BOUND = 0.20            # §13.7
SECONDARY_COORDINATE_CALIPER = 0.15           # §13.8
INTERACTION_DRIFT_MAX = 0.15                  # §13.8
MIN_QUALIFIED_FAMILIES = 5                    # §13.15
MIN_TIER1_CORE = 2                            # §13.15
N_BACKUP_FAMILIES = 2                         # §13.15
```

Unchanged and deliberately so: `REFERENCE_CALIPER = 0.10`,
`REFERENCE_NEWCOMBE_REGION = 0.05`, `REFERENCE_VACUITY_MAX = 0.10`,
`SPECTRUM_ELIGIBILITY_BAND = (0.10, 0.95)`, `SPECTRUM_OFFSET = 0.20`,
`N_CORE_REFERENCES = 3`, `COMPOSED_HEADROOM_BAND = (0.05, 0.95)`,
`N_BLOCKS = 384`, `M_DRAWS = 8`, `BOOTSTRAP_RESAMPLES = 10_000`, every §11.9
threshold, every §16.2 precondition.

**Removed:** `REFERENCE_PRESCREEN_CALIPER` (§12.2 deletes the rule).
**Retained but no longer an admission threshold:** `CHANCE_DEGENERACY_MAX`
(0.99), which §11.2 keeps as the point at which $\iota$ is undefined.

> **Fix while adapting.** v4r4's comments disagree with its computed values —
> `N_SEVERITIES` documented 190 against a computed 254, `N_DECLARED_SEVERITIES`
> 334 against 510, `N_CONFIRMATORY # 408` against 384, `N_SEQUESTERED # 72`
> against 96. The computed values are what the code used and what the records
> carry, so nothing scientific moves; the comments are wrong and v5's must
> assert rather than describe. §19's qualification checks the counts.

### B2. `verifiers/constraints.py` → §7.3, §7.4, §7.6, §7.10

The `Family` dataclass gains the twelve structural-metadata fields of §7.3 plus
`discourse_role`, each asserted in `__post_init__` against the predicate form —
the pattern `_FORM_CLASS` already uses for `constraint_class`. Add
`structural_tier` with `assert_tier_admits_slot(family, slot)` beside the
existing `assert_reference_slot_allowed`.

Families: add `MK1`–`MK8` (marker exact counts, ladder 1…8, reserve 1…12) and
`XC2`, `XC3`; rename `CX1` → `MK1` and `CX2` → `XC1` with a carry-over record;
retain `RF1`–`RF12`, `CR1`–`CR12`, `CL7`, `CL8` as Tier 3. Assert the counts of
§7.10: 37 families, 326 round-0 severities, 632 declared, 650 instruments in 39
verifiers.

### B3. `stages/selection.py` → §13

The largest single adaptation. `CalibrationRow` gains
`kappa_under_b`, `displacement`, `projected_compliance`, `structural_tier`,
`discourse_role` and the split identity; `FORBIDDEN_CALIBRATION_FIELDS` and the
closed-schema refusal stay exactly as they are and **§19 test 2 additionally
requires** that rows supplying `kappa_under_b` be load-one cells whose single
present constraint is $B$.

`eligible()` becomes the eight-component lexicographic `validity(row) ->
(bool, first_failing_component, reason)`. `admit_family` calls it and records
the earliest failing component. `admit_core_references` gains the Tier-1
minimum and the discourse-role spread. `select_spectrum_triple` is unchanged.
`admit_class_companion` splits into `admit_near_form_controls` (three, Tier 2)
and `admit_broad_class_control` (one, Tier 3 budget).

### B4. `design/cells.py`, `design/prompts.py` → §8.1

Replace the named-variant enumeration with an admitted **arm set** and a
derived cell count: `cells_for(arms) -> tuple[Cell, ...]`, with
`arms ⊆ {"core", "spectrum", "nearform", "class"}` over the always-present
base. Delete `VARIANT_EXEMPTIONS`; §18.1's freeze refuses an empty field that
no identification status explains, which is the general form of what that patch
did specially.

### B5. `stages/regime.py` → §12.2, §12.3

The retention rule becomes high-recall: rule 2 carries every Tier-1/Tier-2 rung
unconditionally; rule 1 carries a Tier-3 rung whose pre-screen Wilson interval
for raw solo compliance intersects $[0.05, 0.95]$ **and** which passes the
structural checks. Delete the pre-screen distance shortlist. Add §12.3's
bracketing rule and `OPERATING_POINT_AT_GRID_BOUNDARY`.

### B6. `analysis/estimators.py` → §11.2, §11.5, §11.7

Add `counterfactual_chance`, `displacement`, `projected_compliance`,
`delta_near`, `delta_broad`, and the five order contrasts with the dual
algebraic form and its $10^{-9}$ agreement assertion — the pattern
`delta_difficulty` already uses.

### B7. `analysis/claims.py` → §3.2, §17.7

`emit_l4` → `emit_l4a(*, per_member: Mapping[str, Mapping[str, str | None]],
...)`, keyword-only, validating a mapping of mappings. New `emit_l4b` reading
F11. `LEVEL_MEMBERS` gains L4b's members. `assert_no_l5_emitter` unchanged.

### B8. `analysis/run.py`, `run/analysis_run.py` → §21

Build `per_member` from the emitted statements **with member identity
retained** — the single line that caused v4r4's defect. Add steps 8 and 17 of
§21: the order contrasts, and the projection audit.

### B9. `analysis/spectrum.py` → §11.8

Add the tier-indicator secondary fit over twelve points. The $A$-exclusion
assertion and the refit loop are unchanged.

### B10. `stages/freeze.py`, `run/freeze_run.py` → §18.1

New required fields: the spec hash, both calibration-table hashes, the
qualified pool with earliest failing components, the tier and discourse role of
every admitted companion, the near-form controls, the two frozen backups with
the never-substituted statement, the admitted arm set and derived cell count,
F1–F11. Replace `VARIANT_EXEMPTIONS` with the status-explains-emptiness rule.

### B11. `engine/transitions.py` → §18

Twelve stages become eighteen. `PROTOCOL_REGISTERED` first; Gate 2 renamed;
Gate 2.5 and Gate 3A/3B/3C inserted; `PREFREEZE_AUDIT` and `FINAL_REPORT`
become stages with records rather than tools. `STAGE_ARTIFACT_TYPE` extends;
`GENERATION_STAGES` gains `GATE_2_5_CANDIDATE_QUALIFICATION` only if
$\kappa^{B}$ needs its own generation — it does **not**, which is the point of
§9.1.

### B12. `stages/confirmatory.py`, `run/confirmatory_run.py` → §9.1

Enforce the presence rule at **every** generative stage, not only the
confirmatory one. This is what makes §13.6 free and it is v4r4's silent gap.

---

## 3. Entirely new — class C

### C1. `stages/interaction.py` → §13.6

```
kappa_under_b(rows, candidate, m_star) -> float
displacement(kappa, kappa_b)          -> float
projected_compliance(kappa_b, iota)   -> float
interaction_verdict(...)              -> (bool, reason)
```

Reads only load-one rows whose single present constraint is $B$ at $m^*$, and
asserts that on entry. No generation.

### C2. `stages/stability.py` → §13.7

Per candidate, per split: the full validity verdict; and the percentile
bootstrap over topics within split for $\iota^A - \iota^B$ and
$p_{\text{solo}}^A - p_{\text{solo}}^B$, with the equivalence test against
$\pm 0.20$.

### C3. `stages/qualification_gate.py` → §18 stage 7

Gate 2.5: evaluates $V_{\text{spec}}$ … $V_{\text{inter}}$ on the pooled
calibration and writes the qualified pool with every candidate's earliest
failing component. Not terminal; may write an empty pool.

### C4. `stages/support.py` → §13.15, §18 stage 10

Gate 3C: the support counts, the admitted arm set, the frozen backups, every
identification status at design time, and §26's `MET` / `NOT_MET`.

### C5. `stages/audit_prefreeze.py` → §18 stage 12, §33

The fifteen-item checklist as executable checks with a verdict each, including
the §10.7 text diff against v4r4's and the "validation" text check.

### C6. `stages/final_report.py` → §18 stage 18, §31

The machine-readable result table, every number traced to a stage record and a
hash.

### C7. `protocol/taxonomy.py` → §7.3, §7.4

The metadata vocabulary, the tier rule, the slot table, and
`assert_metadata_consistent(family)`.

### C8. `protocol/reuse_ledger.py` → §30

The five classifications, the seven invariants, the two measured ones.

### C9. `topics/` → §6.2

The 720-question bank: the v4 624 carried on v4's split seed, plus 96 newly
authored allocated to Calibration-B, with the four authoring rules asserted per
question and the bank hash entering the registration manifest.

---

## 4. Tests that must exist before qualification

§19 registers six by name; each maps to a file.

| Test | §19 | File |
|---|---|---|
| L4a refuses v4r4's `gemma-3n-e4b-it` pattern | 1 | `tests_v5/test_l4a_per_member.py` |
| L4a emits on v4r4's `qwen3-4b` pattern | 1 | same |
| an L4 emitter cannot be called with a bare level sequence | 1 | same |
| the calibration loader refuses composed and unknown fields, and validates `kappa_under_b`'s source | 2 | `tests_v5/test_selection_schema.py` |
| $V(R)$ is lexicographic and records the **earliest** failing component | 3 | `tests_v5/test_validity_order.py` |
| no Gate-4 table reaches a selection function; the backup-substitution path does not exist | 4 | `tests_v5/test_gate4_nonadaptive.py` |
| every family's metadata agrees with its predicate; every slot refuses an inadmissible tier | 5 | `tests_v5/test_taxonomy.py` |
| `assert_no_l5_emitter` holds | 6 | `tests_v5/test_claims.py` |

Plus, carried from `tests_v4r4/` and re-namespaced: the seed-regime, canonical-evidence
admission, metric-spec, verifier-audit and manifest-identity suites, and
`test_l4_replication_defect.py` — which stays in `tests_v4r4/` **unchanged**,
pinning v4r4's sealed behaviour so that a v5 fix cannot silently rewrite what
v4r4 did.

---

## 5. Order of work

1. **C9 topics** and **B1 constants** — nothing else can be asserted without
   them, and §34 D3 gates adoption on the bank.
2. **C7 taxonomy**, **B2 constraints**, **B4 cells** — the library and the
   design plan.
3. **A-class verifier modules** re-namespaced, then Gate 1 evidence
   regenerated over the 650-instrument population. This is the long pole in
   wall-clock and it does not depend on any model.
4. **B5 regime**, **B12 presence rule** — the screen and the row schema.
5. **C1 interaction**, **C2 stability**, **B3 selection**, **C3/C4 gates** —
   the reference machinery, in that order, because each feeds the next.
6. **B6 estimators**, **B9 spectrum**, **B7 claims**, **B8 analysis order** —
   the analysis, with the §19 tests written *before* the pilot, because §20's
   commitment device means a claim-emitter defect found after the mask is
   sealed cannot be repaired.
7. **B10 freeze**, **B11 transitions**, **C5 pre-freeze audit**, **C6 final
   report**, **C8 ledger**.
8. §19's procedural pilot over the full 56-cell plan.

**Step 6's ordering is the one lesson from v4r4 that costs nothing to apply.**
v4r4's L4 defect was sealed into two replications' masked artifacts because the
emitter was first exercised after the freeze. §19 requires the claim-ladder
tests to pass at qualification.
