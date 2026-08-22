# DCI-1 v4r4 — execution report, Gate 3 to confirmation

Produced 2026-08-22. Every number below is read from a signed stage record, from
a machine-readable artifact under `dci1/reports/dci1v4r4/`, or recomputed from
the raw scored rows; where a figure was recomputed rather than read, the report
says so. Sections 5–9 are written after the confirmatory generation completes.

The one-sentence version: **§13.10 ended two of the four replications, one of
them the only replication whose Gate 3 identified a difficulty spectrum, so no
spectrum-dependent estimand is identified anywhere in this study.**

---

## 1. Gate 3 final state

Four signed `GATE_3_REFERENCES` records, all reproducing field-for-field under
the current code when §13.4, §13.6 and §13.7 are re-derived from each model's
sealed `GATE_2_REGIME` record.

| model | design | variant | cells/block | core refs | spectrum | statuses beyond `COMPANION_CLASS_NOT_MATCHED` |
|---|---|---|---:|---:|---:|---|
| `gemma-3n-e2b-it` | full | full | 47 | 3 | 6 | — |
| `gemma-3n-e4b-it` | reduced | reduced | 8 | 0 | 0 | `EXCESS_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` |
| `qwen3-4b` | reduced | reduced | 8 | 2 | 0 | both |
| `qwen3-4b-instruct-2507` | reduced | reduced | 8 | 0 | 0 | both |

`gemma-3n-e2b-it`'s three references are `RF9:10` (t_initial), `CR5:2` (comma)
and `RF11:26` (vowel_initial), each straddling A with a spectrum pair.

**Why only one replication reached the full design.** Local sparsity of the
eligible reference pool immediately above ι_A, arriving by three routes:
`gemma-3n-e4b-it`'s nearest rungs carry high chance compliance, so they match A
on ι and miss it on raw solo compliance and §13.4's Newcombe interval; `qwen3-4b`
admits two straddling families and §13.4 wants three distinct feature groups;
`qwen3-4b-instruct-2507` has a gap in its ladder — eligible rungs run 0.122 →
0.592 then jump to 0.722, with nothing inside the 0.10 caliper above ι_A = 0.596.

**Superseded records.** Four Gate-3 records written before `7eb1947` are retained
at `evidence/dci1v4r4/<model>/superseded/7eb19472dfc4/` with a supersession note,
appear in each replication's transition log as `SUPERSEDED` between two `PASS`
rows, and are predecessors of nothing — `stage_record` never looks there. They
were retired because `design_variant_for` read `core_references` off an attribute
`SelectionResult` does not have, so every replication was assigned the reduced
design whatever Gate 3 had selected.

---

## 2. Gate 4 — composed-headroom validation (§13.10)

Every registered cell type of each replication's own design, on the 24 reserved
composed-validation topics, at `M_CAL = 4`, each cell's compliance rate evaluated
independently against `[0.05, 0.95]` for each of its constraints. 6,816
generations across both cards. First stage that composes two constraints in one
prompt and first that spends a reserved topic set.

| model | design | cells | rows | outcome |
|---|---|---:|---:|---|
| `gemma-3n-e2b-it` | full | 1,128 | 4,512 | **TERMINAL — `COMPOSED_HEADROOM_FAILURE`** |
| `gemma-3n-e4b-it` | reduced | 192 | 768 | PASS |
| `qwen3-4b` | reduced | 192 | 768 | PASS |
| `qwen3-4b-instruct-2507` | reduced | 192 | 768 | **TERMINAL — `COMPOSED_HEADROOM_FAILURE`** |

**The failing cells, recomputed independently from `scored.jsonl`** rather than
read off the record. Each rate is 96 observations over 24 topics at M = 4 —
balanced, so the flat mean and the topic mean coincide.

| model | cell | slot | rate |
|---|---|---|---:|
| `gemma-3n-e2b-it` | `pair:B+R3` | B | 0.9583 |
| `gemma-3n-e2b-it` | `pair:B+R3` | R3 | 0.9688 |
| `gemma-3n-e2b-it` | `pair:B+R3+` | R3+ | 1.0000 |
| `gemma-3n-e2b-it` | `pair:R3++B` | R3+ | 1.0000 |
| `gemma-3n-e2b-it` | `pair:R3+B` | R3 | 0.9583 |
| `qwen3-4b-instruct-2507` | `solo:CL` | CL | 0.9896 |

`R3` is `RF11:26` and `R3+` is `RF11:32` — the vowel-initial family, whose chance
compliance is high, so its ι sat inside the eligibility band on the 96 solo
calibration topics (0.633 and 0.679) while its **raw** compliance on the composed
set is at the ceiling. §13.10 checks the raw rate, because a constraint that is
nearly always satisfied has no room to register interference.
`qwen3-4b-instruct-2507` fails on one cell: its class companion `CL8:3` at
0.9896 solo. Both are ceiling effects on a **companion**, not on an outcome
constraint.

**Nothing was revised in response.** §13.10: "Gate 4 runs after the spectrum and
the class companion are already fixed, and its outcomes never revise them. A
headroom failure is a terminal status for the replication, not an instruction to
choose different rungs." No reference replaced, no family added, no caliper
widened, no rung re-chosen. Both terminal records are signed, mirrored to
`durable_root/`, carry §28.3's sentence, and mechanically disable every later
stage — `assert_predecessor_passed` refuses Gate 5 on them by name.

---

## 3. Pre-freeze audit

`reports/dci1v4r4/prefreeze_audit.json`, reconstructed from signed records alone.

- **Surviving replications**: `gemma-3n-e4b-it`, `qwen3-4b`. Both `reduced`.
- **Design**: 8 cells/block (1 unconstrained, 3 solo A/B/CL, 4 composed A+B, B+A, B+CL, CL+B), 384 blocks, M = 8.
- **Confirmatory budget, recomputed**: 8 × 384 × 8 = **24,576 per replication, 49,152 total**. The ~577,536 figure in earlier planning assumed four replications on the 47-cell design; neither the count nor the design survived Gates 3 and 4, and the audit records the superseded estimate beside the recomputed one.
- **Regime**: `gemma-3n-e4b-it` n\* = 4, m\* = 10, no §7.2 extension. `qwen3-4b` n\* = 2, m\* = **12**, §7.2 extension measured.
- **Precision, projected at the registered variance model** (T = 384, M = 8), at the worse φ = 0.37 and the largest registered Šidák constant (k = 6): D 0.0452 against 0.05, Λ 0.0639 against 0.08, Δ_j 0.0452 against 0.06 — every applicable precondition met. Δ_R and δ_difficulty carry preconditions that do not apply, because the surviving design does not identify them. v4r2 §16.2's published row reproduces from the same formulas to four decimals, so the variance model has not drifted.
- **Topic integrity**: the confirmatory and sequestered sets untouched at audit time, over every `rows.jsonl` in both roots; `composed` spent by Gate 4 alone, which §6.2 licenses.
- **Integrity**: every stage record verifies under the study key, round-trips through the wire form, matches its reader copy and matches its durable mirror byte for byte. §26's durability gate passes, with its stated limitation recorded rather than implied: both roots are on one device and no off-machine copy exists.
- **Tests and lint**: 1,773 passed, 10 skipped across all five suites. Ruff E,F,W over the v4r4 subtree: the 15 inherited E501.

---

## 4. Gate 5 — the scientific freeze

PASS on both survivors, at producing commit `450a049`.

| | `gemma-3n-e4b-it` | `qwen3-4b` |
|---|---|---|
| freeze record sha256 | `228abf8d79c474fe…` | `5533fdb6c4309527…` |
| durable copy | identical | identical |
| design variant | reduced, 8 cells/block | reduced, 8 cells/block |
| n\*, m\* | 4, 10 | 2, 12 (§7.2 extension) |
| slot map | A:4, B:10, CL = CL7:80 | A:2, B:12, CL = CX1:4, R1 = RF11:21, R2 = CR5:8 |
| calibration table hash | `bb4bc2ae3826f5ea…` | `280203f88b1414d9…` |
| chat template hash | `ac03dcb3b09726f1…` | `a55ee1b1660128b7…` |
| canonical verifier hash | `09f0675c3018485e…` | `09f0675c3018485e…` |
| Gate 1 basis | `deterministic_measurement_validated` | same |
| unclosed §33 decisions | none | none |

`qwen3-4b`'s frozen slot map carries `R1` and `R2` — two references §13.4 admitted
but the reduced design does not use. They generate no cell; they are scored as
§25 chance verdicts on the unconstrained rows and no estimand reads them.

Write-once is enforced and `assert_no_post_freeze_mutation` refuses every stage
at or before the freeze.

**Two defects were found below the freeze after it passed**, and §18.1 refuses
the obvious remedy: `supersede_stage_records` calls `assert_no_post_freeze_mutation`
on every stage it is asked to retire, so a passed `GATE_5_FREEZE` cannot be
retired and re-run. `reports/dci1v4r4/post_freeze_delta.json` answers it the way
the protocol requires — by re-assembling both records from the same signed inputs
under current code and comparing all 66 §18.1 fields. `producing_commit` is the
only field that moved.

---

## 5. Confirmatory generation

Licensed by the Gate 5 freeze at `450a049` and by nothing else.
`assert_generation_licensed` is the only door, and until this revision it
demanded a field named `verifier_source_hash` that §18.1 does not register and
`freeze_run.assemble` does not write — so no freeze record could license any
generation and the path had never run. It now reads `canonical_verifier_hash`,
the name the freeze actually binds.

Both survivors carry §8.6's **reduced** design: 8 cells per block, 384 blocks,
`M_DRAWS = 8`.

| | qwen3-4b | gemma-3n-e4b-it |
|---|---|---|
| Rows generated | 24,576 | 24,576 |
| Distinct row identities | 24,576 | 24,576 |
| Distinct prompts | 3,072 | 3,072 |
| Distinct scientific seeds | 24,576 | 24,576 |
| Missing / duplicated / unexpected | 0 / 0 / 0 | 0 / 0 / 0 |
| `finish_reason = length` | 6 (0.0244%) | 1 (0.0041%) |
| Empty final answers | 0 | 0 |
| Processing failures | 0 | 0 |

**49,152 confirmatory generations in total.** That figure is recomputed from
the signed Gate 3 and Gate 4 records, not carried from planning: the earlier
~577k estimate assumed four replications on the 47-cell full design, and Gate 3
left one replication on that design while Gate 4 made it terminal.

Generation ran in four shards of 96 blocks per model, on two GPUs in parallel.
The batches partition the registered block list in registered order, every
batch is generated whole, and completeness is evaluated over the union — so
batching is not selection. `assert_no_selective_rerun` — which was documented
and never called until this revision — now runs before the completeness check
on every resume, and refuses a row set carrying a duplicated or out-of-plan
identity.

Each cell carries exactly one `prompt_hash` across its eight draws, every
`row_id` is `{cell}:{draw}`, and no seed is reused. Nothing about companion
identity or preliminary effect direction was inspected while generation ran.

## 6. Masked analysis

Both replications: 10,000 bootstrap resamples, 384 blocks, `spectrum_fit_ran`
false (a reduced design builds no spectrum input).

§20-R4's stratified permutation fixes `ceil(N × MASK_MIN_DIFFERING_FRACTION)`
non-identity blocks, because independent permutation over two companions moves
a label with probability exactly 0.5 — the bound it was asked to clear. Both
replications report a realised differing share of exactly 0.5 over 6 (outcome,
configuration) groups, of which 2 are maskable.

The remaining 4 groups are **structurally unmaskable**, and the note the
analysis attaches to them was corrected during this run. It had asserted the
full-design case unconditionally — that no registered estimand reads a
singleton-companion outcome. Under §8.6's reduced design that is false: B has
two companions and is masked among them, but A and CL each have only B, so
`D(A←B)` — a registered reduced-design estimand, and the one that carries both
replications' L1 — is analysed with its companion identity visible. The masked
phase protects `D(B←A)`, `D(B←CL)` and `Λ` on this design and does not protect
the reciprocal direction. That is now stated in the record rather than implied.

Both masked artifacts were sealed under `analysis_code_hash`
`dffb5a861a497cc2…`. The hash is identical across the two replications, which
is what makes them comparable; the analysis code was held still between them
for exactly that reason.

| | masked artifact | mask key |
|---|---|---|
| qwen3-4b | `3368b857…` | sealed in record |
| gemma-3n-e4b-it | `6ca030d9…` | `b2520830…` |

## 7. Unmasking

Once per replication, after its masked artifact was complete, signed and
mirrored byte-for-byte into the durable root. Each unmask record's
`masked_outputs_hash` equals the artifact hash it was bound to, so the unmask
names the sealed object and not a recomputation of it. No mask was regenerated
at any point.

`run_unmasked_analysis` refuses to run under an analysis code hash that differs
from the masked seal: *"an unmasked analysis under different code is not the
analysis the mask protected."* That guard held for both replications — and it
is also the reason the defect in §8 below could not be repaired.

## 8. Final scientific results

Two replications survive of four. Both are reduced-design, both met every
applicable §16.2 precision precondition, and all point estimates below were
**independently recomputed from raw `scored.jsonl` rows** — no estimator, no
`ObservationTable`, no bootstrap — and reproduced to four decimals.

### 8.1 qwen3-4b (n\* = 2, m\* = 12, focal extension used)

| Estimand | outcome_first | outcome_second |
|---|---|---|
| D(A←B) | **+0.3919** [+0.3503, +0.4335] | **+0.3291** [+0.2835, +0.3747] |
| D(B←A) | −0.1227 [−0.1536, −0.0918] | −0.0120 [−0.0450, +0.0209] |
| Λ | −0.5146 [−0.5671, −0.4622] | −0.3411 [−0.3989, −0.2834] |
| D(B←CL) | −0.1341 [−0.1647, −0.1035] | −0.0505 [−0.0814, −0.0195] |
| Δ_class | +0.0114 [−0.0106, +0.0334] | +0.0384 [+0.0088, +0.0680] |

Composing A with B costs A a large delivery loss in both configurations. B is
not damaged by A; in `outcome_first` it *gains*. §17.4's vacuity gate binds in
`outcome_first` (worst upper 0.1604, driven by `vac(B|B+CL) − vac(B solo)` =
+0.1292) and not in `outcome_second` (0.0158), so the F5 partial-identification
block is attached to the first configuration only.

**Ladder:** L1 emitted for D(A←B) in both configurations. L1 withheld for
D(B←A) — its interval is not above zero. L2 withheld: its gate is L1 in *both*
directions. L3 unreachable — the reduced design does not estimate Δ_R. L4
emitted, and licensed under the registered per-member reading as well (§8.3).

### 8.2 gemma-3n-e4b-it (n\* = 4, m\* = 10, no focal extension)

| Estimand | outcome_first | outcome_second |
|---|---|---|
| D(A←B) | **+0.1159** [+0.0771, +0.1546] | −0.0322 [−0.0734, +0.0089] |
| D(B←A) | +0.0062 [−0.0182, +0.0306] | **+0.2832** [+0.2485, +0.3179] |
| Λ | −0.1097 [−0.1546, −0.0648] | +0.3154 [+0.2594, +0.3714] |
| D(B←CL) | +0.3164 [+0.2793, +0.3535] | +0.7946 [+0.7624, +0.8268] |
| Δ_class | −0.3102 [−0.3498, −0.2706] | −0.5114 [−0.5495, −0.4733] |

Solo compliance: A 0.7718, B 0.8512, CL7 0.7152 — all with headroom. The
vacuity gate does not bind in either configuration (worst upper 0.00098 and
0.0), so no F5 block is attached.

**The direction of the loss flips with position.** In `outcome_first` the
constraint that loses is A; in `outcome_second` it is B, and by more. Λ reverses
sign. This replication is *configuration-dependent*, and the registered
consequence (§28.1) is that the table is reported and no pooled scalar is
quoted.

**Ladder:** L1 emitted for D(A←B) in `outcome_first` and for D(B←A) in
`outcome_second`, each withheld in the other configuration. L2 withheld in both
(its gate is L1 in both directions, and no configuration has both). L3
unreachable.

### 8.3 A post-freeze defect in the L4 emitter, recorded and not repaired

§3.2 licenses L1 on **"the named** $D(c \leftarrow g)$**"**, and §28.1 pairs
*Replication* — "the same classification in every registered configuration" —
with *Configuration dependence* — "**the quantity** is configuration-dependent;
the table is reported and no pooled scalar is quoted." Both rows are about a
named quantity, so L4's gate is per member.

`analysis.claims.emit_l4` compares the **set of levels any member reached**.
`run/analysis_run.py` hands it `[s["claim_level"] for s in statements if
emitted]`, with the member identity already discarded, so the emitter cannot
see the difference even in principle.

For gemma-3n-e4b-it both configurations reach L1, so the sets match and L4 is
emitted — while every named member's classification *flips*. The emitted L4
therefore asserts replication for the one replication that most clearly does
not replicate. **gemma-3n-e4b-it's emitted L4 is invalidated.** The registered
reading is *Configuration dependence*.

qwen3-4b is unaffected: D(A←B) reaches L1 in both configurations, so the
emitted and registered readings agree.

**It is not repaired, and the protocol is why.** `run_unmasked_analysis`
refuses an unmasked analysis under code that differs from the masked seal, and
§20 forbids regenerating a mask once semantic identities are known. Correcting
`emit_l4` would therefore either strand both replications — their unmasked
analyses could never be recomputed — or require a mask regenerated after
unmasking, which is prohibited outright. The commitment device worked as
designed and it has bound the author of the defect. The correction belongs to
the next revision.

What is done instead: `tools/v4r4_final_report.py` recomputes the registered
per-member reading from each record's own statements and writes it beside the
emitted field as `l4_registered_reading`, with
`agrees_with_the_emitted_field: false` for gemma-3n-e4b-it. A characterization
test (`tests_v4r4/test_l4_replication_defect.py`) pins the sealed behaviour so
that a silent "fix" — which would break both replications — fails loudly.

### 8.4 What the study does and does not say

**Says.** Composing two instructions imposes a delivery loss on at least one of
them in every surviving replication and configuration, with simultaneous
intervals wholly above zero. On qwen3-4b that loss falls on A in both
configurations and is large. On gemma-3n-e4b-it which constraint pays depends
on which one is asked first.

**Does not say.** Nothing about *pair-specific* excess: Δ_R is not identified on
either replication. Nothing about broader difficulty-response: δ_diff and Ξ are
not identified on either. Nothing about A being generally disruptive versus
specifically disruptive to B. Nothing about family or structural effects. And
no claim rests on a non-significant interval: `D(B←A)`'s interval containing
zero on qwen3-4b in `outcome_second` is unresolved direction, **not** evidence
of no effect.

**Model dependence** is observed but not estimated: two replications differ
qualitatively, and two of four models never reached confirmation at all. With
n = 2 the study reports the two tables and does not pool them.

## 9. Limitations

**Reference-pool sparsity is the binding limitation of this revision.** §13.4
admits a core reference only from a family supplying a straddling severity
triple. Three of four models admitted none, so they run §8.6's reduced design,
which carries `EXCESS_NOT_IDENTIFIED` and `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`
from the freeze onward. Six registered quantities are **NOT_IDENTIFIED** for
every surviving replication — `Δ_R`, `Δ_j`, `δ_difficulty`, `Ξ`, `D(B←R_j)`,
`D(R_j←B)`. They are listed by name in `final_results.json` rather than omitted,
because a reader who cannot see the absence cannot tell it from a null. No
post-hoc estimate of any of them exists.

**The only full-design replication did not survive Gate 4.** gemma-3n-e2b-it
admitted three core references and was the sole replication identifying the
difficulty spectrum. Gate 4 found five composed cells above the 0.95 headroom
band on `RF11:26`/`RF11:32` (rates 0.9583–1.0000) and terminated it. §13.10 is
explicit that a headroom failure is a terminal status and not an instruction to
choose different rungs, and no rung was changed. **The consequence is that the
difficulty-spectrum estimands are identified by no surviving replication.**

**qwen3-4b's focal severity comes from the final focal-extension rung.**
`focal_extension_measured` is true and m\* = 12 is the last rung the extension
reached. Its Gate 2 selection therefore sits at the edge of the measured range
rather than inside it, and there is no evidence about how the replication would
behave at a rung beyond it.

**Configuration confounding.** §11.4's position caveat attaches to every
`outcome_second` statement as `POSITION_CONFOUNDED`: in that configuration the
outcome constraint is also the second-mentioned constraint, and the design does
not separate the two.

**Two survivors of four.** qwen3-4b-instruct-2507 also terminated at Gate 4
(`solo:CL` = CL8:3 at 0.9896). Neither terminal outcome was revisited.

**Precision.** Every applicable precondition was met, so no estimand carries
`INSUFFICIENT_PRECISION`. But precision preconditions bound half-widths, not
inference across replications: nothing here supports an equivalence statement
between the two survivors.

**Durability is local.** Both roots sit on one device and no off-machine copy
exists. What survives in version control is the manifest, the hashes, the
producing commit and the reproduction commands — enough to make loss
*detectable* and the run repeatable, not enough to make it recoverable.

**The L4 defect of §8.3** is a limitation of this revision's analysis code, not
of its data.

## 10. Artifacts and commits

| Artifact | Path |
|---|---|
| Final results | `reports/dci1v4r4/final_results.json` |
| Pre-freeze audit | `reports/dci1v4r4/prefreeze_audit.json` |
| Post-freeze delta | `reports/dci1v4r4/post_freeze_delta.json` |
| Backend provenance | `reports/dci1v4r4/backend_provenance.json` |
| Evidence manifest | `reports/dci1v4r4/evidence_manifest.json` |
| Durability record | `reports/dci1v4r4/durability.json` |
| Signed stage records | `evidence/dci1v4r4/<model>/<STAGE>/records/` |
| Durable mirrors | `durable_root/dci1v4r4/<model>/<STAGE>/records/` |
| Superseded records | `durable_root/dci1v4r4/<model>/superseded/` |

**Evidence tree:** 355 files, 769.7 MB, 155,712 scored rows, byte-identical in
both roots. 149 critical artifacts, none missing from and none diverged in the
mirror. Restore rehearsal 8/8.

**Sealing commit** for both freezes: `450a0499e05fc780d20b8f3a8139a2879a8589c2`.
The post-freeze delta re-assembles both freeze records under current code and
compares all 66 §18.1 fields. Four moved; `producing_commit` is expected to,
and `hardware_record`, `environment_digest` and `durability_record` enumerate
the evidence tree and therefore move as evidence accrues. Each of the three was
re-compared on its substantive content — the hardware the evidence came off,
the environment digest recomputed without the accreting sub-record, and whether
§26's gate still passes with no critical artifact missing or diverged — and all
three are unchanged. `scientific_state_unchanged: true` for both replications.

**Tests:** 1,649 passed, 10 skipped in the dci1 suite. Lint: 15 pre-existing
E501 in files this work did not touch, none introduced.

Superseded Gate-3 records remain in `durable_root/…/superseded/` as historical
evidence and cannot satisfy predecessor checks.
