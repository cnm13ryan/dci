# DCI-1 v8 — freeze-readiness report (2026-09-03)

**Status: FROZEN.** Four `FROZEN` records exist under
`dci1/evidence/dci1v8-confirm-r2` (05:45:36–05:45:38Z, 2026-09-03), each
written from a clean worktree at commit `f7af7f2` with the ten-item readiness
audit passing on every item. No `CONFIRMATORY_GENERATION` directory exists
under that root; no composed row has been generated for this design. The
study stops here, as instructed.

## Identities

| item | value |
|---|---|
| confirmatory root | `dci1/evidence/dci1v8-confirm-r2` |
| registration manifest | hash `98a2463eb20a…`, signed at commit `3bfcb12` (05:36Z) |
| preregistration bound | `dci1/docs/DCI1_preregistration_v8.md`, hash `9e3df7b12be5…` (`Status: FROZEN-READY`) |
| rule-table hash | `0acfed37912f…` |
| verifier / wording hash | `ea885b0db67e…` / `fe3b5be15759…` (identical on every pilot and confirm record) |
| membership lock | `dci1/reports/dci1v8dev/confirmatory_membership.{json,md}`, hash `00db0e1842f2…`, commit `f7af7f2` |
| freeze commit | `f7af7f2` (worktree `dci-v8-freeze`, clean, HEAD; `provenance.enforced = true`) |
| pilot roots bound | qwen3-4b → r9; qwen3-4b-instruct-2507 → r10; gemma-3n-e2b-it → r12; gemma-3n-e4b-it → r13 (all at four calibration passes, 192 topics per frame) |

| model | FROZEN record hash | LOCAL frames | SPECTRUM frames | generations planned |
|---|---|---|---|---:|
| `gemma-3n-e2b-it` | `9027e12bdb46…` | 0, 1, 3 | 0, 1, 3 | 562,176 |
| `gemma-3n-e4b-it` | `a9716189ad2d…` | 0, 1, 3 | 0, 1, 2, 3 | 669,696 |
| `qwen3-4b` | `5d5d7e55728c…` | 0, 3 | 0, 1, 2, 3 | 559,104 |
| `qwen3-4b-instruct-2507` | `b01917ca5024…` | none (one supported frame) | 1, 3 | 205,824 |
| total | | | | 1,996,800 |

384 blocks per entering frame, 8 draws per cell, completion cap 512 on every model.

## Frozen design per frame

| model | f | arms | cells/block | n*(f) | m*(f) | core R1..R3 | backups R4, R5 | spectrum slots | operating point |
|---|---|---|---:|---:|---:|---|---|---:|---|
| e2b | 0 | base, core, backup, spectrum, runner_up | 68 | 1 | 8 | MK1:4, MK8:3, MK5:6 | XC3:9, MK4:7 | 8 | UNSTABLE (A2 = 8, B2 = 9) |
| e2b | 1 | base, core, backup, spectrum | 56 | 3 | 10 | XC3:9, MK4:4, MK1:4 | MK5:9, MK2:3 | 8 | stable |
| e2b | 3 | base, core, backup, spectrum, runner_up | 59 | 7 | 11 | MK4:5, XC3:8, MK2:1 | MK5:6, MK8:3 | 8 | UNSTABLE (A2 = 8) |
| e4b | 0 | base, core, backup, spectrum, runner_up | 68 | 6 | 9 | MK2:6, MK1:5, MK4:8 | MK8:1, MK5:5 | 8 | UNSTABLE (A2 = 4, B2 = 10) |
| e4b | 1 | base, core, backup, spectrum, runner_up | 59 | 6 | 9 | XC3:9, MK3:3, MK5:6 | MK2:6, MK4:4 | 8 | UNSTABLE (A2 = 7) |
| e4b | 2 | base, spectrum | 35 | 7 | 9 | — | — | 10 | stable |
| e4b | 3 | base, core, backup, spectrum | 56 | 8 | 10 | MK2:8, MK3:1, XC3:10 | MK1:5, MK4:8 | 8 | stable |
| qwen3-4b | 0 | base, core, backup, spectrum, runner_up | 59 | 6 | 12 | MK1:4, XC3:10, MK8:2 | MK2:3, MK6:6 | 8 | UNSTABLE (A2 = 3) |
| qwen3-4b | 1 | base, spectrum | 32 | 7 | 12 | — | — | 9 | UNSTABLE (no LOCAL arm; no runner-up cells) |
| qwen3-4b | 2 | base, spectrum | 32 | 3 | 12 | — | — | 9 | UNSTABLE (same) |
| qwen3-4b | 3 | base, core, backup, spectrum, runner_up | 59 | 5 | 13 | MK2:6, XC3:8, MK7:2 | MK1:3, MK6:8 | 8 | UNSTABLE (A2 = 4) |
| 2507 | 1 | base, spectrum | 35 | 6 | 10 | — | — | 10 | UNSTABLE (no LOCAL arm) |
| 2507 | 3 | base, spectrum | 32 | 6 | 12 | — | — | 9 | stable |

The recovery shares and full selection distributions are in
`operating_point_stability.md` beside this file (deterministic seeds; 2000
topic resamples per frame). Six of the eight LOCAL frames carry
`OPERATING_POINT_UNSTABLE` on n*(f) (recovery 0.40–0.53); two also on m*(f).
Every such LOCAL frame carries the runner-up sensitivity arm.

## Freeze criteria

| criterion | outcome | where |
|---|---|---|
| every suspected issue verified or rejected against repository evidence | PASS | `VERIFICATION_LEDGER.md` (12 findings; 9 confirmed, 2 partially, 1 confirmed by measurement) |
| dedicated v8 preregistration exists | PASS | `dci1/docs/DCI1_preregistration_v8.md`, bound by hash in the manifest and every freeze |
| preregistration and executable protocol agree | PASS | `test_every_active_source_of_the_allocation_agrees`, `test_rules_provenance`, readiness item 1 (hash equality), the synthetic seven-stage walk |
| allocation unambiguous | PASS | one value, 384; rules, precision, coverage, lock, freeze, preregistration; readiness item 2 |
| calibration policy universal and prospectively fixed | PASS | `CALIBRATION_FRAME_OFFSETS = (0,1,2,3)` committed at `957e5d7` before r12/r13 were generated; readiness item 3 on every model |
| eligibility / top-up rules deterministic and prospectively fixed | PASS | `run/eligibility.py`, `confirm/topup.py::TOPUP_RULE`, preregistration §15; the r2 top-up fired only on qwen3-4b f2 (768 rows) and moved no verdict; every untouched frame reproduced its pilot |
| operating-point uncertainty recorded | PASS | status, distribution, runner-up on every entering frame; runner-up arm where required; readiness item 4 |
| reference-set sensitivity pre-registered | PASS | five frozen families with distances and every admissible triple on every LOCAL frame (8–10 triples); F_REFSENS; readiness item 5; `reference_sensitivity/REPORT.md` |
| LOCAL scope limited to identified model × frame combinations | PASS | preregistration §16; membership lock; `frame_screen_diagnostic/REPORT.md` |
| retained robustness checks implemented, omitted ones registered | PASS | `analysis_components.md`; preregistration §18.6–§18.7, §20; `test_confirm_safeguards.py` (27) |
| deterministic seed / provenance defects fixed | PASS | `seeds.bootstrap_seed` in membership; `test_provenance_gate.py` (byte-identical across `PYTHONHASHSEED`s) |
| clean-worktree enforcement works | PASS | `stage_provenance` on both lifecycles, no bypass; every r2 record `worktree_clean: true, enforced: true`; failure cases tested |
| protected composed outcomes have not influenced the design | PASS | §Protected-outcome check below |
| relevant validation and tests pass | PASS | fast v8 386 passed / 2 skipped; slow v8 17 passed; fast v7 292 passed + 1 pre-existing disk-dependent failure (`test_v5_cannot_adopt_a_v4r4_evidence_root`, unrelated); readiness 10 × 4 models |

## Consequential pre-freeze changes and the evidence behind them

1. One allocation (384) — the signed rule table said 288 while the freezes
   bound 384 (`rules.py` at `11697e9`, `confirm/precision.py`).
2. Universal four-pass calibration — `CALIBRATION_FRAME_OFFSETS_BY_MODEL`
   at `11697e9`; r12/r13 re-measured; e2b gained f0, e4b gained f0 and f1
   and became LOCAL-eligible.
3. Operating-point status and runner-up arm — recovery 0.40–0.56 on three
   of four LOCAL frames in the superseded root; 0.40–0.53 on six of eight
   in r2.
4. Provenance gate and environment record — no clean check existed; the
   CLI accepted an operator commit.
5. Deterministic stability seed — `hash(model_key)` at `membership.py:198`.
6. The registered analysis restored per frame — `analysis_components.md`.
7. Freeze-readiness audit on the mandatory path.
8. Top-up reproduction check split into LOCAL (exact) and spectrum
   (recorded with both allocations) views — r9 projected coverage at 96
   blocks; r2 records 96 → 384 with every verdict agreeing.

## Remaining limitations

- Δ_R(f) is conditional on n*(f), m*(f) that six of eight LOCAL frames
  re-select on fewer than 2/3 of topic resamples; the runner-up contrast is
  descriptive. `gemma-3n-e2b-it` f0 sits at the grid floor (n* = 1) with the
  ceiling (8) as its runner-up: A's curve on that frame is nearly flat
  across the band.
- The frozen core triple is one draw from practically tied controls on every
  LOCAL frame (P(primary re-selected) 0.09–0.64); F_REFSENS bounds the
  effect over the five frozen families only.
- The pre-screen is frame-pooled; up to five near-ι_A(f) Tier-1/2 rungs per
  frame were never calibrated; the scope restriction of §16 applies.
- `qwen3-4b-instruct-2507` supports LOCAL on one frame only and enters no
  LOCAL arm; its Δ_R(f) is unidentified under the universal rule.
- The strong L3c refutation, the raw-coordinate secondary and the
  projected-vs-realised boundary summary are not available (declared).
- Generated text is not bit-reproducible on this backend (94/96 fresh vs
  fresh, 66/96 vs the stored batch).
- Precision at the joint constant is projected to meet the precondition for
  the three-frame models under the adverse scenarios (k = 18), and the
  realised interval decides.

## Protected-outcome check (metadata only)

Protected artifacts exist only under the superseded root
`dci1/evidence/dci1v8-confirm` (25 scored batches, 10:11–13:06Z on
2026-09-02, generation stopped 13:09Z, never analysed). Every decision above
traces to a code fact, a git fact, a signed pre-freeze pilot record or a
development report listed in `VERIFICATION_LEDGER.md`; no file under a
protected stage was opened by the audit, its agents or its tools (the
diagnostic tools refuse protected run directories by path); r2 adopts no row
from the superseded root (`confirm.execute` reuses within its own root only,
and the design differs). No `CONFIRMATORY_GENERATION`, `CONFIRMATORY_ANALYSIS`
or `FINAL_REPORT` directory exists under r2.

## Freeze blockers

None. Generation has not been started and will not be started by this task.
