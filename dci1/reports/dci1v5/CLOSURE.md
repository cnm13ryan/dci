# DCI-1 v5 — closure

**Manifest** `af5fa4bcfd125f936cade49cf45304737c6367b6bd7106a6ec372a6735340c98`,
producing commit `5ed18543db89c3c5275d1303865a450c599bb18b`, signature verified,
worktree clean. Machine-readable form: [`closure.json`](closure.json).

## Outcome

**No replication reached `CONFIRMATORY_GENERATION`.** The masking specification
was never opened, no confirmatory row exists, no unmasking occurred, and
`FINAL_REPORT` is not legally reachable for any model. 459,312 behavioural rows
were generated across stages 2–10 and they are development and gate evidence
only: none of them is confirmatory, and none supports a claim about the effect.

| replication | ends at | recorded terminal | D6 | rows |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | PREFREEZE_AUDIT (FAIL) | *none written* — V5-E32 | NOT_IDENTIFIED, irreversible | 114,792 |
| `gemma-3n-e4b-it` | GATE_4 | `COMPOSED_HEADROOM_FAILURE` | NOT_IDENTIFIED, irreversible | 116,400 |
| `qwen3-4b` | PREFREEZE_AUDIT (FAIL) | *none written* — V5-E32 | NOT_IDENTIFIED, irreversible | 114,648 |
| `qwen3-4b-instruct-2507` | GATE_4 | `COMPOSED_HEADROOM_FAILURE` | identified | 113,472 |

**All four are scientifically terminal.** Two by a registered §28 status. Two
because `PREFREEZE_AUDIT` recorded `FAIL` on the mandatory `support_satisfied`
check: that record is write-once, so the audit cannot be re-run, and
`GATE_5_FREEZE` refuses a predecessor that did not record `PASS`. Nothing
further is reachable for them by any legal action.

The one replication that survived D6 with its estimands identified —
`qwen3-4b-instruct-2507`, the only model admitting the core arm, 26 derived
cells — is the one that failed Gate 4. `gemma-3n-e4b-it` failed both.

## What is *not* concluded

A terminal pre-confirmatory status carries no evidence about the effect. That
is the registered sentence on both terminal reports and it governs the other
two as well. In particular:

- **`NOT_IDENTIFIED` is not a null result.** Three replications did not fail to
  find an effect; the design could not identify the estimands on them at all.
- Nothing here licenses any statement about `Delta_j`, `Delta_R`, `Xi`, or any
  order estimand, on any model. 48 estimand members are marked not identified
  on each of the three, including every primary contrast.
- The Gate 4 compliance figures are gate measurements, not effect estimates.

## What was not done, deliberately

No reselection, no reference repair, no threshold, grid, model or topic change,
no re-expansion, and no conversion of a `NOT_IDENTIFIED` verdict into a null.
§31 and §34 D6 forbid all of these after the fact, and D6 records
`irreversible: true` on each of the three.

Current v5 evidence is **not** re-run to obtain cleaner terminal bookkeeping.
The V5-E32 fix below changes future executions only; every signed record here
stands exactly as produced.

## V5-E32 — a registered terminal status with no raise path

`PREFREEZE_AUDIT_FAILURE` is a member of §28's `TERMINAL_STATUSES`.
`run/prefreeze_run.py` computed it and wrote it into a `failure_status` payload
field while returning `outcome="FAIL"`; it contained no `raise` at all. So no
§28.3 terminal report was written, `transitions.terminal_status` returned
`None`, and `status --model` described a replication that can never take
another step as live with `GATE_5_FREEZE` next.

This is lifecycle bookkeeping. It did not change a measurement, a gate verdict,
a selection, or an estimand. The `support_satisfied` failure that produced it
is correctly computed and correctly recorded in the signed `PREFREEZE_AUDIT`
record, which carries all 26 artifact checks and the blocking list.

**A full audit of all thirteen registered terminal statuses in force found
exactly one such hole**, this one. `TARGET_RANGE_EXHAUSTED` and
`FOCAL_RANGE_EXHAUSTED` raise at `run/gates_run.py:352`;
`SPECIFICATION_AMBIGUOUS`, `MEASUREMENT_NOT_ESTABLISHED` and
`MEASUREMENT_EVIDENCE_INSUFFICIENT` at `stages/gate1.py:496` via a computed
status; `REGISTRATION_INCOMPLETE` at `run/registration_run.py:83` via
`manifest.REGISTRATION_INCOMPLETE`; the rest as literals.

The fix and its regression tests are recorded as amendment A8. A test now walks
the AST of every module in `dci1/src/dci1v5/` and fails if any status in force
lacks a reachable `raise`, so the class of defect cannot recur silently.
