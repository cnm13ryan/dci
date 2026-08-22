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

*(pending)*

## 6. Masked analysis

*(pending)*

## 7. Unmasking

*(pending)*

## 8. Final scientific results

*(pending)*

## 9. Limitations

*(pending)*

## 10. Artifacts and commits

*(pending)*
