# `dci1/evidence/dci1v8-confirm` — SUPERSEDED (2026-09-02)

The confirmatory root frozen at commit `5870ddf` (four `FROZEN` records,
10:11Z) began protected composed generation at 10:11:44Z on two cards and
was **stopped by the operator at 13:09Z** when the pre-freeze audit of the
same day began. Nothing under it is deleted; nothing under its protected
stages has been read. This note records what exists there, from metadata
only, so that the supersession is auditable.

## Why superseded

The audit found four defects in what those freezes bound (details:
`dci1/reports/dci1v8dev/freeze_readiness/VERIFICATION_LEDGER.md`):

- two active allocations (the rule layer's 288 blocks per frame inside the
  signed rule table; the precision module's 384 in the same manifest);
- a model-specific calibration allocation (both Qwens at four passes, both
  Gemmas at two) adopted after seeing reference survival on the study
  checkpoints;
- the operating-point stability bootstrap seeded with the process-salted
  builtin `hash()`, so the recorded distributions are not reproducible;
- no clean-worktree requirement on any confirmatory stage.

A frozen design with those properties is not the design the v8
preregistration describes, so the root is superseded rather than resumed.

## What exists (metadata only)

| model | stages present | protected batch directories | scored files | first / last write (local, +0100) |
|---|---|---|---|---|
| `qwen3-4b` | CONFIRM_REGISTERED, LOCAL_TOPUP, MEMBERSHIP, FROZEN, CONFIRMATORY_GENERATION | 14 (`frame-0-blocks-0000-0032` … `frame-0-blocks-0352-0384`, `frame-1-blocks-0000-0032`, `frame-1-blocks-0032-0064`) | 13 | 11:25:52 / 14:06:26 |
| `gemma-3n-e2b-it` | same | 13 (frame 0 complete, `frame-1-blocks-0000-0032`) | 12 | 11:26:34 / 14:05:38 |
| `gemma-3n-e4b-it` | CONFIRM_REGISTERED, LOCAL_TOPUP, MEMBERSHIP, FROZEN | none | 0 | — |
| `qwen3-4b-instruct-2507` | same | none | 0 | — |

No `CONFIRMATORY_ANALYSIS` or `FINAL_REPORT` record exists for any model.
No `confirmatory_generation.json` record exists (generation was incomplete on
both running models). The operator stop is appended to
`logs/<model>.confirm.driver.log` at 13:09Z.

## What the successor does with it

- The successor root (`dci1/evidence/dci1v8-confirm-r2`) **adopts no row**
  from this root: `confirm.execute` reuses a stored batch only from its own
  root, and the successor's design differs (allocation, calibration basis,
  runner-up arm), so the identities would not match in any case.
- The pre-freeze records here (registration, top-up, membership, freeze)
  remain valid historical evidence of the 2026-09-02 morning design and are
  cited as such in `CHANGES_SCIENTIFIC.md`.
- The composed rows here are protected outcomes of a superseded design:
  they are never analysed, never inspected, and never cited as evidence
  for or against any v8 claim.
