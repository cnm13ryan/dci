# DCI-1 v7 development rehearsals (2026-08-28 → 30) — development evidence only

Real-model, end-to-end rehearsals of the amended v7 lifecycle (A6–A8) in the
**development namespace** (`dci1v7.engine.context.development_context`,
study id `dci1v7-development`; `CHANGES_SCIENTIFIC.md` 2026-08-28 "v7
development namespace"). Nothing here is a v7 replication, a §28 outcome, or
evidence about any estimand; v7 is **not** frozen or re-registered by any of
it, and the registered v7 evidence (manifest `969a5b9f…`, four terminal
reports, closed 2026-08-28) is untouched. The `*_summary.json` files beside
this note are written by `tools/v7_replication_summary.py --dev-root` from
the signed records of each root; every number below is read from them.

## Lanes

| root (commit registered) | model | stages | Gate 3C | arms / cells | confirmatory rows | §26 | statements | Δ_R (first / second) | final report | wall |
|---|---|---|---|---|---|---|---|---|---|---|
| `dci1v7-development` (`67358c5`) | qwen3-4b | all 19, PASS | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (C4 lost on the 192-topic basis: 5 straddling groups), core kept | base + core / 26 | 79,872 complete | MET | L1×2 L3c×2 L4a×1 L4b×4 | −0.001 / +0.014 | 14/14 | 22:40Z → 02:48Z (4 h 8 min) |
| `dci1v7-development-r3` (`551cd93`, code = `13173db`) | qwen3-4b | all 19, PASS | same | base + core / 26 | 79,872 complete | MET | L1×2 L3c×2 L4a×1 L4b×4 | −0.003 / +0.013 | 14/14 | 10:20Z → 14:34Z |
| `dci1v7-development-r3` | gemma-3n-e2b-it | 19 stages; `UNMASKED_ANALYSIS` raised once (defect 5), passed under `aa226ca`; `FINAL_REPORT` recorded FAIL on one check (defect 6) | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`, core kept; `OPERATING_POINT_AT_GRID_BOUNDARY` from Gate 2 | base + core + class / 29 | 89,088 complete | MET | L1×3 L3c×2 L4b×4 | −0.024 / −0.071 | 13/14 as written (write-once); 14/14 re-checked read-only under `3ea82b2` | 10:21Z → 17:21Z |
| `dci1v7-development-r4` (`a1ed2a9`, pooled tree) | qwen3-4b-instruct-2507 | all 19, PASS | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (4 straddling groups), core kept | base + core / 26 | 79,872 complete | MET | L3c×2 L4a×1 L4b×1 | +0.006 / −0.003 | 14/14 | 14:35Z → 19:27Z |
| `dci1v7-development-r4` | gemma-3n-e4b-it | all 19, PASS (Gate 2 under `3ea82b2`; probe → freeze → report under `43bb22a`) | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (ι_A 0.725; C4 lost on the 192-topic basis: straddling `marker_hence`, `marker_indeed`, `marker_thus`, `marker_whereas`), core kept | base + core + class / 29 | 89,088 complete | MET | L1×3 L2×1 L3c×2 L4b×5 | −0.027 / −0.073 | 14/14 | 17:16Z → 07:18Z (Gate 2 6 h 48 min, confirmatory generation 5 h 48 min — the slowest model on the panel) |
| `dci1v7-development-r5` (`a18db3d`; Gate 2 under `6eac8e3`, Gate 2.5 onward under `43bb22a`) | gemma-3n-e2b-it (again, under both fixes and the final pools) | all 19, PASS | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (ι_A 0.589; C4 lost on the 192-topic basis: straddling `semicolon`, `sentence`), core kept; `OPERATING_POINT_AT_GRID_BOUNDARY` from Gate 2 | base + core + class / 29 | 89,088 complete | MET | L1×3 L3c×2 L4b×4 | −0.032 / −0.085 | 14/14 | 19:29Z → 05:08Z (Gate 2's first two attempts deadlocked in the interim pool and were retried by the driver, 21:11Z–23:06Z; the third ran under `6eac8e3`) |

A study root binds one registration commit, so each code change after a
root's first registration required a new root for later models (`r3` →
`r4` → `r5`); the refused attempts wrote no record. `dci1v7-development-r2`
was abandoned at `REGIME_SCREEN` when the forkserver pool hung (defect 4)
and is retained as that record.

## What the registered study could not reach, and the rehearsals did

Every registered v7 replication ended `PREFREEZE_AUDIT_FAILURE` on
`support_satisfied`. Under A6–A8 every rehearsed model passed the pre-freeze
audit (29/29 mandatory checks), froze on its identified estimands with the
core arm retained (A7: C4 lost on the calibration basis costs the spectrum
arm only), generated its confirmatory rows, and produced masked and
unmasked analyses and a final report. The base arm's contrasts and Δ_R were
estimated on every completed lane; the 20 spectrum-dependent members were
withheld irreversibly on every lane, as D6 registers.

## Defects found and fixed (each: diagnosed, fixed within v7, tested, changelog entry)

1. **No real-model path outside the registered tree** — the only
   non-registered namespace substituted a stand-in generator. Fixed:
   development namespace (`67358c5`).
2. **The freeze bound Gate 3B's selection for arms Gate 3C did not admit**
   (`freeze_run.assemble`); `assert_freeze_complete` now refuses a bound
   element without its arm and vice versa (`67358c5`).
3. **The manifest recorded `adoption: DRAFT`** by default (`67358c5`).
4. **Process pools**: a fork-based pool deadlocked the audit (8 h) and a
   forkserver pool hung a real stage; reverted, redesigned on spawned
   workers, proven byte-identical (unit tests; 336 real calibration rows in
   every column), landed as `e0006b4` (Gate 2's table 751 s → 16.6 s; the
   audit 1,250 s → 340 s). That pool's dispatch-all-then-collect deadlocked
   on full pipes in r5's Gate 2 (two attempts, retried by the driver);
   redesigned as its own spawned workers with one pipe each, one chunk in
   flight per worker, chunk-indexed reassembly, bounded waits and a serial
   fallback on a stall (`19aab65`, `6eac8e3`; `engine/parallel.py`), re-proven
   identical, and the audit re-run on it (`43bb22a`).
5. **§23's projection audit raised on a block with κ_c = 1** instead of
   recording `DIFFICULTY_COORDINATE_DEGENERATE` (§11.2); reachable only with
   the class arm admitted (`aa226ca`).
6. **The final report's status trace demanded `freeze == Gate 3C`** while
   §18.1's freeze binds Gate 2 ∪ Gate 3C; any Gate-2 status failed the
   report (`3ea82b2`).

## Finding recorded, not in force

**§13.11's `chance_compliance` column has been 0.0 on every replication of
v5–v7** (`_calibration_rows` reached its chance branch through a call that
raised for every non-outcome candidate). §13.2 defines κ_c on the
unconstrained cells; the correction touches the modules `revision.V9` pins
byte-for-byte (§13's frozen implementation) through the degenerate case,
so it is recorded (`CHANGES_SCIENTIFIC.md` 2026-08-29, finding) and left
for a researcher decision. On the rehearsal rows the three selected
references have κ_c = 0 and do not move; 7 of 112 candidates sit above
§13.4's ceiling and have been passing `V_chance` trivially.

## Validation state of the study tree

`43bb22a` (the tree both running lanes froze on): execution-path audit
80/80 rules, 24 scenarios, 0 contract defects; fast subset 661; synthetic
walk 25; D6 branches 4; producer/consumer 172 fields, 0 defects; the
pool's identity checks (scoring rows byte-identical; 336 real calibration
rows in every column; stalled-pool fallback) in `tests_v7/test_parallel.py`.
