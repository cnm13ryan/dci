# Incident: §12.6's coverage criterion met a rung with no difficulty coordinate

**Status: OPEN. Awaiting a researcher decision. Nothing has been repaired,
changed or deleted, and no `REGIME_SCREEN` record exists for any replication.**

Written 2026-08-26, after `REGIME_SCREEN` failed on both replications that ran
it. Registration is complete and valid; this is the stage after Gate 0.

## What happened

```
$ python -m dci1v6.run.cli run --stage REGIME_SCREEN --model gemma-3n-e2b-it --device 0
{"error": "TypeError", "message": "type NoneType doesn't define __round__ method"}
```

Identically for `gemma-3n-e4b-it` on device 1. Traceback:

```
regime_run.regime_payload            line 382   run_expansion(...)
stages/regime.run_expansion          line 936   coverage_criterion(rows, iota_a=iota_a)
stages/regime.coverage_criterion     line 566   below = [r for r in rows
                                                        if tie_key(r["iota"]) < tie_key(iota_a)]
stages/calibration_table.tie_key     line  74   return round(value, 12)
TypeError: type NoneType doesn't define __round__ method
```

## The rung

Reconstructed from the rows already on disk, without regenerating anything.
The first `coverage_criterion` call is clean; the failure is the call after
§12.6's expansion round 0 measured its reserve rungs.

| replication | eligible rows | with `iota is None` | the rung | solo | vacuity |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | 219 | **1** | `CR7:56` | 0.8750 | 0.0 |
| `gemma-3n-e4b-it` | 213 | **1** | `CR7:56` | 0.8333 | 0.0 |

`CR7:56` — Tier 3, constraint class `budget`, feature group `letter_a`,
`iota_A` ≈ 0.708 on both. Same rung on both replications, so this is a
property of the reserve rung the expansion admits and not of a model.

Its `iota` is `None` because its **measured chance compliance is at or above
`CHANCE_DEGENERACY_MAX = 0.99`**. That is a real measurement, not a missing
one: `run/regime_run.difficulty_table` sets `iota = None` exactly on that
condition, and `calibration_table.instructed_compliance` refuses to compute a
coordinate there — "iota is not defined and §11.2 records
`DIFFICULTY_COORDINATE_DEGENERATE` instead". Unconstrained text already
satisfies `CR7:56` almost always.

## Why it is reachable now and was not in v5

`stages/regime.coverage_criterion` is byte-identical in v5 and v6
(v5 line 493, v6 line 566). What changed is which rungs reach it.

§33's **U4** asks which quantity §13's band applies to in §12.6, and the two
registered constructions are closed:

```
E1: iota inside [0.10, 0.90]                  and pre-screen solo vacuity <= 0.10
E2: raw solo compliance inside [0.10, 0.90]   and pre-screen solo vacuity <= 0.10
```

Under **E1** the eligibility coordinate *is* `iota`, so a rung with no `iota`
is never eligible and never reaches the dereference. Under **E2** the
coordinate is raw solo, which is measured whatever the chance level does — so
a rung can be eligible and have no position on the `iota` axis at all.

v5 also ran E2 and did not hit this. Its `iota is None` rungs exist — 8, 7 and
3 of them on three replications — but every one has `solo >= 0.958`, outside
`[0.10, 0.90]`, so E2 made them ineligible for a different reason. `CR7:56` is
the first rung to have an in-band solo *and* a degenerate chance level.

**This is a latent defect since v5, first triggered by data.** It is not
caused by amendment A15 and touches nothing A15 changed.

## The scientific question, which the repository does not settle

Every one of §12.6's conditions C1–C8 is a statement about **position relative
to `iota_A`**: below, above, near within the caliper, straddling within a
family, feature groups on each side. A rung whose difficulty coordinate is
undefined has no position on that axis. So what does §12.6 do with it?

At least three readings, and they are not equivalent:

- **(i) not an eligible coverage rung at all.** Every condition it could serve
  is defined by a coordinate it does not have.
- **(ii) eligible, but absent from the `iota`-indexed sets only.** It still
  counts toward the conditions that do not reference `iota` — the Tier-1/2
  family and feature-group counts, C7's class arm, C8's near-form arm.
- **(iii) an identification event.** §11.2 registers
  `DIFFICULTY_COORDINATE_DEGENERATE` for exactly this measurement; record it
  for the rung and drop the rung from the selectable pool.

C4 counts rungs per straddling family and C2/C3 count feature groups on each
side, so whether `CR7:56` counts can change C1–C6, which changes whether the
expansion runs another round, which changes whether the replication records
`REFERENCE_SUPPORT_NOT_IDENTIFIED` **at design time** and runs without the
core and spectrum arms. That is a registered design-time outcome, not a
presentation detail.

**What the registered text says, and where it stops.** §13.4 registers a
chance ceiling — `V_chance`: `kappa_R <= 0.75`, Wilson upper bound `<= 0.85` —
and §13.4's closing paragraph says `CHANCE_DEGENERACY_MAX` "is not an
admission threshold in v5 and §13.4's ceiling is", adding that the ceiling
"makes this unreachable for an admitted companion without contradicting the
admission record". So the protocol *does* have a rule that would exclude
`CR7:56` — but it is §13's **reference-admission** rule, applied at Gate 2.5
on calibration data, and §12.6's pre-screen coverage eligibility is U4's
predicate, whose two registered constructions carry a band and a vacuity
ceiling **and no chance ceiling**. The consistency argument §13.4 offers
therefore does not reach the §12.6 pre-screen basis, which is where this
fired.

**I will not choose between the readings.** Adding §13.4's chance ceiling to
`coverage_eligibility` would be a third construction of U4's predicate,
adopted after a gate ran, changing which rungs are eligible and therefore the
expansion and the admitted arm set — an amendment to a registered criterion,
and one whose direction the outcome would visibly depend on. §32.1 and the
standing instruction against repairing a criterion after seeing data both
apply.

## State, preserved

No `REGIME_SCREEN` record and no terminal report exists for any replication;
all four are at `GATE_0_APPARATUS` with `terminal=None`. The failure was a
`TypeError` inside `compute`, so `run_stage` wrote nothing — not a record, not
a §28.3 report, not a transition row.

Every generated row is on the evidence tree, unmodified:

| replication | ladder | cap-512 | cap-768 | cap-1024 | expansion-0 |
|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | 8,232 | 72 | 72 | 72 | 2,040 |
| `gemma-3n-e4b-it` | 8,232 | 72 | 72 | 72 | 1,896 |

`qwen3-4b` and `qwen3-4b-instruct-2507` have not been started on this stage;
they hold Gate 0 and nothing further. They were not started because the
expansion's later rounds are among the things the resolution can change, and
generating under an unresolved rule is what this stop exists to avoid.

The diagnosis above was obtained by re-running `regime_payload` against the
rows already on disk. It regenerated nothing — every `rows.jsonl` mtime is
from the original run — and wrote nothing.

## What the researcher has to decide

Which of (i), (ii), (iii) — or another construction — §12.6 applies to an
eligible rung whose difficulty coordinate is undefined; and whether that is
recorded as a resolution of a new §33 item, a further construction of U4, or a
§32 amendment. The registration at manifest
`36f1fb3b6dfcedeadc2cd8cbaa4832204148c6851bd6dd5dd5c5a9eada7c5662` stands
either way: no behavioural row has entered any estimator, and this stage has
produced no record to supersede.
