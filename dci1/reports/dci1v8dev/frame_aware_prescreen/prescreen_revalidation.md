# DCI-1 v8.1 — revalidation of the frame-aware pre-screen on fresh successor pilots

**Status.** Deliverable 5 of the redesign (2026-09-03). Section 1 (the
invalidation boundary) is proved from code and contracts and is final.
Sections 2–5 are filled from the successor pilot roots as they complete;
until every model has a `PILOT_REPORT` (or a terminal status) this
document says so and the freeze-readiness verdict at the end is
provisional.

## 1. The invalidation boundary, from the code

A changed retention rule changes which rungs a frame's calibration table
holds, and every later stage is a function of that table. Reading the
producer/consumer contract (`run/contracts.py`) and the stage code:

| artifact | reusable from a v8 root? | why |
|---|---|---|
| `PILOT_REGISTERED`, `QUALIFIED`, `GATE_0_APPARATUS` | no — a root registers under one commit and one manifest (`manifest.ensure_registration` refuses a different commit or binding) | the successor's manifest binds new rule constants, a new document and protocol version `8.1-pilot` |
| `REGIME_SCREEN` | no | the screen is laid out over four passes (`regime.screen_blocks`), the per-frame counts and screens are new record fields, the cap selection is rerun |
| `SECOND_PASS_SCREEN` | no | the batches are planned per frame and rendered under every frame; the record's `final_table_by_frame`, `provisional_plan` and `comparator_plan` are what Gate 2 reads |
| `GATE_1_INSTRUMENT` | no (reads the new screen rows) | descriptive, but formed on the new rows |
| forwarded candidate calibration (`GATE_2_CALIBRATION` candidate run) | **no** | the candidate population is decided per frame at Gate 2 (`FORWARDING_RULE`) and generated per frame; the v8 rows were one set on every frame |
| operating points n\*(f), m\*(f) | recomputed (same rule, fresh grid rows) | the grids are regenerated in the fresh root; the rule is unchanged, so agreement with v8 is expected up to sampling and is reported |
| chance coordinates κ(X, f), ι_A(f) | recomputed | read on the fresh root's own unconstrained cells |
| LOCAL validity, SPECTRUM validity / selection, core references, backups | recomputed | functions of the frame's new table |
| operating-point stability, reference sensitivity | recomputed at `MEMBERSHIP` of a successor confirm root | read the fresh Gate-2 grid rows and Gate-3 records |
| model eligibility, membership, confirmatory manifest | recomputed / new root | `confirm/pilot_import` binds the pilot records by hash; a v8 pilot is refused by readiness item 11 |

So the boundary is `REGIME_SCREEN`: nothing after `GATE_0_APPARATUS` of a
v8 root can be reused, and the successor pilots are fresh roots run from
registration. The v8 roots and the frozen root `dci1v8-confirm-r2` are not
overwritten, not resumed and not read by any successor stage.

## 2. Successor pilot roots

Run from a clean worktree at the successor commit (the lifecycle gate
refuses otherwise), every stage `PILOT_REGISTERED → PILOT_REPORT`, roots
under `dci1/evidence/` of the canonical worktree:

| model | root | card | commit | status |
|---|---|---|---|---|
| qwen3-4b | `dci1v8-pilot-r14` | 0 | — | pending |
| qwen3-4b-instruct-2507 | `dci1v8-pilot-r15` | 1 | — | pending |
| gemma-3n-e2b-it | `dci1v8-pilot-r16` | 1 | — | pending |
| gemma-3n-e4b-it | `dci1v8-pilot-r17` | 0 | — | pending |

## 3. Old versus successor: model × frame status

Filled from `GATE_3_REFERENCES` (`frame_states`, `local_eligibility`,
`retention_comparison`) of each successor root beside the v8 roots
(r9/r10/r12/r13). Every change is attributed to one of: the screen
allocation (24 vs 6 topics per frame), the forwarding target (ι_A(f) vs
the pooled ι_A), the per-frame candidate population, or fresh-sample
variation of the operating point (the comparator arm separates the last
two on identical rows).

*Pending.*

## 4. Validation

*Pending: the fast and slow suites at the successor commit, the
producer/consumer walk, the contract audit, and the pre-existing unrelated
failure `tests_v7/test_isolation.py::test_v5_cannot_adopt_a_v4r4_evidence_root`
(reproduced at `f7af7f2` without the redesign; disk-dependent; not fixed
here).*

## 5. Freeze-readiness verdict

*Pending.*
