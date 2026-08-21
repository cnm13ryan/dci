# DCI-1 v4r4 — Gate 1 checkpoint

**Date:** 2026-08-21. **Status:** `GATE_1_MEASUREMENT` **PASS** on all four
replications. Not frozen. No confirmatory data. No DCI estimand computed.
**Next stage: Gate 2.**

Every number below is read out of a machine-produced artifact in this
directory. Where a claim rests on a check, the check's name is given so it can
be re-run.

---

## 1. What this revision is, and what v4r3 is now

**v4r3 is closed, at its own criterion.** Terminal state
`GATE_1_MEASUREMENT` / `MEASUREMENT_EVIDENCE_INSUFFICIENT`. §18 stage 4 as
registered required §10.2 plus §10.3 *or* §10.4: §10.3 had no independent
annotator, §10.4/§10.4-R/§10.4-R2 each failed their own registered criteria,
and the §10.7-R5 amendment then blocked on a `CP4`/`CP7` wording. That outcome
stands. Nothing under v4r3's source, test, evidence, durable or report trees
was edited to reach v4r4; `reports/dci1v4r3/closure.json` hashes the six
reports and 22 stage records it rests on — **closure hash
`930720a0945e06dd960a877cc1cb23ff9af4ef7048e9456525d18958b7f1b264`**.

**v4r4 is a prospective revision** under §31's designation test: a pre-freeze
change to an unfrozen protocol with no confirmatory data. It was evaluated from
scratch — register, qualify, Gate 0, regime screen, Gate 1 — and did not
re-read v4r3's outcome.

### Differences from v4r3

| id | area | v4r3 | v4r4 |
|---|---|---|---|
| **R4-1** | Gate 1 criterion | §10.2 + (§10.3 **or** §10.4) — reviewer agreement | §10.2 + **§10.7 A–E** — ten conditions, no reviewer threshold |
| **R4-2** | candidate population (§7.0-R4) | 30 families, 584 instruments | **28 families, 524 instruments**; `CP4`/`CP7` removed, `rate_lower_bound` leaves the study |
| **R4-3** | §10.7 A′ | wording direction not a gate condition | every model-facing wording must expose its comparison direction, or the gate blocks |
| **R4-4** | measurement basis | `human_validated` / `autorater_calibration_approved` / `human_validation_unavailable` | **`deterministic_measurement_validated`**; the three reviewer bases are refused before evidence is read |
| **R4-5** | stage records | study id not enforced on read | `assert_own_study` refuses a foreign `study_id` where the record is read |
| **R4-6** | evidence reuse | n/a | the §26-R4 ledger is the only path across the revision boundary |
| **R4-7** | `N_CLASS_FAMILIES` | literal `4` against a 6-family pool | derived from `CLASS_FAMILY_IDS` |

Machine-readable in `dci1v4r4.protocol.revision.DIFFERENCES`; narrated in
`user-notes/DCI1_v4r3_to_v4r4_changelog.md`; adopted in `DECISIONS_V4R4.md`
B0–B7.

**What the revision does not buy.** The basis is not `human_validated`, so
§10.5's scope sentence attaches permanently to every analysis record:

> the outcomes are verifier-defined and support no claim about compliance as an
> independent human would judge it

§10.5's second question — *would an independent human reproduce these
verdicts?* — is exactly as unanswered under v4r4 as under v4r3. R4-1 changes
whether the study executes, not what it may assert. §31-R4 registers that
objection inside the rule rather than answering around it.

---

## 2. Final instrument population and hashes

| | |
|---|---|
| families | **28** (`RF1`–`RF12`, `CR1`–`CR12`, `CL7`, `CL8`, `CX1`, `CX2`) |
| kinds audited | **30** — the 28 families plus `A` and `B` |
| predicate forms | **5** — `count_budget`, `rate_budget`, `count_lower_bound`, `exact_count`, `focal_budget` |
| instruments | **524** |
| model-facing wordings | **2,141** |

| hash | value |
|---|---|
| canonical verifier | `09f0675c3018485e95fbb0aca627f13a06739ef5cd83606f76cf9458143d416f` |
| wordings | `b9b258c5cc8280402520184fdef00c9d3823c55ede72f434cb50344b548848f0` |
| specification | `1704ddc3d126af0f1c9ec99d100fda0a20f0a5020818f8674a7055e0a748fd6c` |
| mutation suite | `a91f6220c63149baadecddec1ce29dd403882f49cc5c9dec522796d324c054c1` |
| measurement rule (§10.7) | `4f59182f07768257e27e2216343dba1608a203e5f2ba874c0254ce16b71839f4` |
| boundary suite | `1794d55f6e86c6b1996c122131b554c3b45a2b7fa87861a6981f1a97ff2ef55b` |
| protocol, **as sealed by Gate 1** | `1e7a7b2dae58b429c8e558f9a1e0501631c240cfa749c3574fa7737a0dc111c1` |
| protocol, after B6/B7 entered the register | `63f558b62f500489a340fba8418afea2a05b706988af00ac636b68f33af0fe3b` |
| Gate-1 decision | `df630decc5333430808a896bbb5487a6750e5335698e7d4841afd278b989c446` |
| registration manifest | `093cac952c4ac87885d7f60f9559a106f183cd16047e860573bcc2bea4db4b60` |
| evidence reuse ledger | `f68f528fcdbc871ba1f50d438b9b7473b241d19607984c0b649da1929ac42c33` |

The verifier hash moved from v4r3's `41edc84c` because `constraints.py` changed.
§10.6 forbids carrying a stale hash forward on the grounds that behaviour looks
unchanged, so the behavioural equivalence was **measured**, not asserted — see
§5.

---

## 3. CP4 / CP7

**Decision: `REMOVE_CP4_AND_CP7`**, under §10.2's registered removal rule.
`cp4_cp7_analysis.json`, `DECISIONS_V4R4.md` B3.

**The defect.** Four wordings state the severity as a target and name no bound
— *"Give {q} percent of words doubled letters."*, *"Make {q} percent of words
carry letter a."* and their pairs. They do not distinguish the registered
`100·S/W ≥ q` from an `== q` reading. The two agree at `q` and disagree on
every answer past it, where the verifier records a pass: a one-sided leniency
in the **treatment**, which no amount of §10.2 implementation evidence could
have found.

**The analysis was outcome-safe.** It reads only the §12.2 pre-screen
difficulty table on the four regime records — solo compliance, chance
compliance, solo vacuity. `reads_no_composed_outcome: true`. No composed DCI
outcome was inspected, and none exists.

**Coverage consequences: none.** §12.6's C1–C6 read rows whose `role` is
`reference`; both families are `class_control`, so removal *cannot* move them.
That is a property of the criterion, and the run confirms it rather than
resting on it. C7 holds on all four models, ι_A moves on none:
`no_condition_changed_on_any_model: true`,
`class_arm_still_matched_on_every_model: true`.

**Rows invalidated: 0. Rows regenerated: 0.** Because the families were removed
rather than reworded, v4r4 declares no instrument their rows could score. Those
generations remain real v4r3 evidence, classified `HISTORICAL_ONLY`.

**The alternative, costed and explicitly not decisive.** Rewriting the four
wordings would have invalidated every measurement taken under them — 16 round-0
rungs × 24 topics × 4 replications = **1,536 generations**, not only the 768
rows carrying the two defective wordings. The rule applied is prospective and
reads coverage only; `not_chosen_for_cost` records that the comparison is
published because a reader is entitled to see it, not because it entered the
decision.

**What removal costs.** `CP4`/`CP7` were the only `rate_lower_bound` families,
so the class arm becomes {count lower bound, exact count}. §7.4-R3's own
argument is why that is tolerable: `A` is an exact-count production constraint
and `CX1` is `A`'s rule over a different marker word — the tightest class
companion the grammar can build. The removed families were the loosest.

---

## 4. Evidence reuse and invalidation

`evidence_reuse_ledger.json`, ledger hash `f68f528f`. Reuse requires **all
seven** invariants — verifier semantics, model-facing prompt, instrument
identity, severity, sampling regime, model and revision, decoding configuration.

| class | n | what |
|---|---|---|
| `REUSED_UNCHANGED` | 0 | — |
| `RECOMPUTED_FROM_EXISTING_RAW_DATA` | 2 | v4r3 regime-screen and Gate-0 pilot **generations**, four replications |
| `INVALIDATED_AND_REGENERATED` | **0** | R4-2 removed rather than reworded, so nothing is owed |
| `HISTORICAL_ONLY` | 6 | v4r3's QUALIFIED record, its Gate-1 decision, the §10.3/§10.4/§10.4-R/§10.4-R2 reviewer evidence, the natural-response defect sensitivity, the `CP4`/`CP7` rows, the v4r3 registration manifest |
| `NOT_APPLICABLE` | 2 | §10.2 suites and corpora (native to v4r4); Gate 2 onward (does not exist) |

**Generations carry; every derived quantity is recomputed.** The model at its
pinned revision, the decoding configuration and the rendered prompt determine a
generation and none of those changed. Verdicts, compliance, vacuity, the §12.2
table, §12.6 coverage and §12.3's shortlist are computed again under v4r4's
verifier hash.

**The two invariants that could have been assumed were measured:**

- **verifier semantics** — both revisions' predicates over 524 instruments ×
  164 frozen cases: **85,936 verdicts, 0 disagreements**, 0 instruments not
  declared in v4r3;
- **model-facing prompt** — **42,240 constraint sentences** stored on carried
  rows across 20 runs, checked byte-identical to the wordings v4r4 renders:
  **0 mismatched, 0 unparsed**.

**Two consequences counted rather than hidden.** v4r4's seed domain carries its
study id, so carried rows are reproducible from v4r3's preserved seed schedule
and not from v4r4's alone; every carry note counts the divergence. And a
carried Gate 0 runs every §19 check under v4r4's code **except the backend call
itself** — the stage record says so on its face.

---

## 5. Coverage, C1–C7

`coverage.json`. `every_model_passes: true`, round zero, **no expansion**.

| model | ι_A | cap | eligible reference rungs | eligible families | C4 well-formed groups | nearest class candidate |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.5556 | 512 | 67 | 18 | 4 | `CX1:1` |
| gemma-3n-e4b-it | 0.6667 | 512 | 69 | 18 | 5 | `CL7:80` |
| qwen3-4b | 0.7500 | 512 | 73 | 18 | 4 | `CX1:5` |
| qwen3-4b-instruct-2507 | 0.6250 | 512 | 46 | 17 | 4 | `CL7:45` |

C1 bracketed, C2 ≥3 feature groups per side, C3 ≥6 rungs within 0.15 of ι_A
from ≥3 groups, C4 ≥4 well-formed straddling groups, C5 ≥12 eligible rungs,
C6 shortlist feasible: **met on all four**. C7 class-matched: **met on all
four**, and it is not terminal either way.

**Counterfactual.** Recomputing the same table on v4r3's 30-family population
returns `conditions_that_moved: []` on every model — the removal is invisible
to coverage.

---

## 6. Gate 1

`gate1_decision.json`, decision hash `df630dec`. **Ten of ten conditions met.**

| # | condition | evidence |
|---|---|---|
| 1 | every family and form carries a complete formal specification | 30 kinds, 5 forms, `specification_complete` on all |
| 2 | no unresolved prose-to-predicate ambiguity | 0 ambiguous kinds, 0 uncovered, 0 unresolved readings |
| 3 | the primary verifier is deterministic | agreement **1.000**, 3 processes × 400 responses × 524 instruments, identical digests |
| 4 | the independent reimplementation agrees exactly | `per_instrument_min` **1.000** over **628,800 verdicts** on 36,164 responses; 650,952 per-response statistic comparisons; segmenter differential 1.000 over all **1,114,112 codepoints** (one case-folding splitter, `U+0130`, named) |
| 5 | boundary, adversarial and Unicode tests pass | 164 frozen cases over 524 instruments — **144,381 verdicts** (59,670 pass / 26,266 fail / 58,445 vacuous pass), **0 failures**; 1,280 labelled checks against 112 labels; 18 adversarial classes covered |
| 6 | mutation sensitivity to every meaningful defect class | see table below — **0 undetected, 0 contradictions** |
| 7 | satisfiability and non-entailment witnesses pass | **92,148 pairs**, 0 failures |
| 8 | wording equivalence, and every wording exposes its direction | 41,920 wording verdicts; **0 genuinely ambiguous, 0 requiring correction** |
| 9 | verifier hash and wording hash bind and match | `09f0675c` / `b9b258c5`, both bound into the record |
| 10 | lifecycle and provenance integrity passes | §7 below |

### Mutation validation (§10.7 D)

| defect | meaningful | detected | not applicable |
|---|---|---|---|
| `numerator_swap` | 30 | **30** | 0 |
| `inequality_flip` | 30 | **30** | 0 |
| `off_by_one` | 30 | **30** | 0 |
| `segmentation_drift` | 22 | **22** | 8 |
| `vacuity_ignored` | 17 | **17** | 13 |
| `denominator_swap` | 12 | **12** | 18 |

Every non-applicability carries a mechanically checked reason — e.g. *"a
count_budget compares a count and has no denominator, so there is nothing to
swap"*. Discrimination cap 40. `uncovered_kinds: []`.

**What mutation validation does not measure**, on the artifact's own face:
practical consequence on real answers. A defect detected here may move no
natural label. The natural-response defect sensitivity is reported separately
and is never read as semantic validation.

### Wording review (§10.7 A′)

| classification | n |
|---|---|
| `unambiguous_explicit` — names an operator from the direction lexicon | 2,040 |
| `unambiguous_documented` — the registered `requirement_verb` construction | 56 |
| `awkward_unambiguous` — the `q = 1` plural (*"Exactly 1 semicolons…"*) | 45 |
| **`genuinely_ambiguous`** | **0** |
| **`requires_correction`** | **0** |

`unmatched_wordings() == []`, and `assert_direction_lexicon_is_exhaustive`
runs on the mandatory path.

### Provenance (§10.7 E)

All four models: predecessor `REGIME_SCREEN`, signature **verified**, study id
`dci1v4r4`, outcome PASS. `predecessor_verified: true`,
`reserved_sets_unspent: true`, `no_gate1_record_exists_yet: true`,
`direction_lexicon_exhaustive: true`, `carry_over_passed: true`. Topic audit:
36,000 rows, `topics_not_in_released_split: []`, `unresolved_stage_labels: []`,
composed/confirmatory/sequestered splits unspent.

### The exact basis for `GATE_1_PASS`

> §18 stage 4 as registered in v4r4: **§10.2 for every verifier in the final
> instrument population, plus §10.7 A–E.** All ten conditions above are met;
> `measurement_basis = deterministic_measurement_validated`; the verifier hash
> `09f0675c` and the wording hash `b9b258c5` are frozen into the record.

Reviewer agreement is **not** part of it and could not have moved it. The
§10.3/§10.4 artifacts travel in the record as `supplementary_diagnostics`,
labelled with their own outcomes (§10.4-R2 as FAILED, §10.3 as *not independent
validation*), and `supplementary_diagnostics_are_not_a_criterion` is on the
record. `gate1_payload` refuses `human_validated`,
`autorater_calibration_approved` and `human_validation_unavailable` **before**
it reads any evidence.

---

## 7. Lifecycle and provenance integrity

`lifecycle_integrity.json`: **`passed: true`, `problems: []`,
`gate_2_may_run: true`.** Nine checks, each failing closed.

- Every current stage record **verifies under the study's signing key** and
  recomputes its content hash. Four models × four stages.
- **Round trip**: the signed payload equals what a reader gets back from the
  file. The integer-key canonicalisation defect that invalidated v4r3's four
  regime signatures is reconstructed here and shown fixed —
  `integer_key_canonicalisation.holds: true`, `wire_form_is_idempotent: true`.
- **Durable mirror** matches byte for byte. `evidence/` is gitignored by
  design, so the mirror is the study's only second copy.
- **Ordering**: every stage's `STAGE_SEQUENCE` predecessor has a verified PASS;
  three transitions logged per model.
- **Write-once**: re-running a stage that has a record raises.
- **Study binding**: a record carrying `study_id: dci1v4r3` is **refused where
  it is read**, and the refusal is *performed* in the report, not asserted.
- **Historical evidence untouched**: `holds: true` — six v4r3 reports and 22
  superseded stage records hash to what `closure.json` says, `drifted: {}`.
- **Producing commit** present on the qualification records:
  `d11e41c7104775890cf7420062c02531ffa33966`.
- **Dirty worktree**: reported, not asserted. §18 stage 1 checks
  `clean_worktree` and fails closed *at qualification*; reports are written
  after qualification by design, so a dirty tree at report time is expected and
  is not a finding.

### The register amendment

`register_amendment.json`: **`passed: true`, `problems: []`.**

B6 and B7 were entered in `DECISIONS_V4R4.md` after Gate 1 returned PASS and
before Gate 2 began. That file is a protocol document, so the protocol hash
moved `1e7a7b2d` → `63f558b6`. The delta is recorded rather than absorbed:

- **only** `dci1/DECISIONS_V4R4.md` moved; the other three protocol documents —
  both preregistrations and the changelog — are byte-identical to what Gate 1
  sealed;
- **no measurement hash moved**: verifier, wordings, specification, mutation
  and measurement-rule hashes are identical to what the gate certified;
- **no Gate-1 record was rewritten and no gate was re-run**; the four sealed
  records still name `1e7a7b2d` and still verify.

Neither decision changes a rule Gate 1 applied. B6 ratifies a classification the
specification module already produced when the gate ran; B7 declines an option.

---

## 8. Remaining robustness limitations

These are carried forward, not repaired.

1. **C4 is identified but fragile on three models.** `gemma-3n-e2b-it`,
   `qwen3-4b` and `qwen3-4b-instruct-2507` satisfy C4 with **exactly four**
   well-formed straddling feature groups, so every one is load-bearing and
   there is no leave-one-family-out margin. `gemma-3n-e4b-it` has five and is
   robust. Load-bearing families: `CR5`, `RF11`, `RF8` (e2b); `CR5`, `RF11`,
   `RF3`, `RF6` (qwen3-4b); `RF10`, `RF11`, `RF8`, `RF9` (qwen3-4b-instruct).
   **Inherited, not introduced** — the same sweep on v4r3's 30-family
   population returns the same families, so R4-2 did not cause it. §12.6's
   registered candidate expansion is **deliberately not invoked** (B7), because
   widening the pool after seeing a coverage result would be an adaptive design
   choice. Any Gate-3 or Gate-4 result on those three models is conditional on
   all four of its straddling groups holding.
2. **The measurement basis is not `human_validated`, permanently.** §10.5's
   scope sentence attaches to every analysis record downstream of this gate.
   Whether an independent human reproduces these verdicts is unanswered.
3. **Nine adversarial corpus classes are tested but never sampled.**
   `case_folding_split`, `combining_mark`, `empty`, `fullwidth`,
   `non_breaking_space`, `single_word`, `soft_hyphen`, `wordless` and
   `zero_width` appear in the frozen corpus but were never observed in a real
   generation. Their verifier behaviour is proven, not exercised in the wild.
4. **A carried Gate 0 does not exercise the backend call.** Every other §19
   check runs under v4r4's code in v4r4's tree; the stage record names the
   exception.
5. **Carried rows are reproducible from v4r3's seed schedule, not v4r4's.**
   The seed domain carries the study id. v4r3's schedule is preserved; the
   divergence is counted on every carry note.
6. **`B` still carries `focal_budget` alone**, and `denominator_swap` is
   meaningful for only the 12 `rate_budget` families. Mutation coverage is
   complete relative to the applicability rule, which is itself a registered
   judgement about which readings are meaningful.

---

## 9. Where the artifacts are

| artifact | path |
|---|---|
| Gate-1 decision | `dci1/reports/dci1v4r4/gate1_decision.json` |
| Gate-1 §10.2 evidence | `dci1/reports/dci1v4r4/gate1_evidence.json` |
| specification audit | `dci1/reports/dci1v4r4/specification_audit.json` |
| mutation validation | `dci1/reports/dci1v4r4/mutation_validation.json` |
| wording review | `dci1/reports/dci1v4r4/wording_review.json` |
| coverage | `dci1/reports/dci1v4r4/coverage.json` |
| CP4/CP7 analysis | `dci1/reports/dci1v4r4/cp4_cp7_analysis.json` |
| evidence reuse ledger | `dci1/reports/dci1v4r4/evidence_reuse_ledger.json` |
| lifecycle integrity | `dci1/reports/dci1v4r4/lifecycle_integrity.json` |
| register amendment | `dci1/reports/dci1v4r4/register_amendment.json` |
| qualification | `dci1/reports/dci1v4r4/qualification.json` |
| v4r3 closure | `dci1/reports/dci1v4r3/closure.json` |
| signed stage records | `dci1/evidence/dci1v4r4/<model>/<STAGE>/records/` (gitignored), mirrored to `dci1/durable_root/dci1v4r4/` |
| protocol | `user-notes/DCI1_preregistration_v4r4.md` |
| changelog | `user-notes/DCI1_v4r3_to_v4r4_changelog.md` |
| decisions register | `dci1/DECISIONS_V4R4.md` |
