# Incident: the one replication that passed every scientific gate terminated at the pre-freeze audit on a document hash

**Status: RECORDED 2026-08-27. Not resolved in v6 and not resolvable in v6.
v7 A4 adds the mechanism v6 lacked. `gemma-3n-e2b-it`'s
`PREFREEZE_AUDIT_FAILURE` stands as a v6 outcome under v6's rule.**

## What happened

`gemma-3n-e2b-it` ran `GATE_4_COMPOSED_HEADROOM` on 2026-08-27 09:56 UTC and
passed — eight cell types on the base and class arms, every entry inside
[0.05, 0.95]. `PREFREEZE_AUDIT` then wrote a §28.3 terminal report at 09:56:25:

```
blocked: ['protocol_hashes_agree', 'support_satisfied']
protocol_hashes_agree: recorded  95db6df44f7c9b1f9233509cf64ff77d9671921d6c67755b298628e6d186cd4c
                       recomputed ef7d17871130636994874f0da13b037986d4c275f37182314ced31e0fc6dda92
```

The registration manifest (signed 2026-08-26, after A15) bound the
preregistration at `95db6df4…`. Amendments A16 (2026-08-26, after the first
`REGIME_SCREEN` rows) and A17 (2026-08-27, after the first probe refusal) were
adopted with full §32.2 disclosure and edited the preregistration; its hash
became `ef7d1787…`. The audit's rule was that the document on disk must be
the registered one, and it was not.

`support_satisfied` failed too, and that one is scientific: Gate 3C had
recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` under the calibrated coverage
re-read (V6-E04), so the replication carried only the base and class arms. The
hash failure is what this note is about; the support failure would have
blocked the freeze on its own and is a registered v6 outcome under §34 D6.

## Why the lifecycle could not say what had happened

v6 had two ways to change a registered document:

- `supersede_registration` (§32, v5 A7): admissible **only before any
  observation exists**, because a superseded registration with rows under it
  is a discarded experiment and §32 wants that said out loud.
- `retire_apparatus_fault` (v6 A15): retires **one stage-1 readiness verdict**,
  and refuses any gate but stage 1, any §28 status, an existing manifest, and
  any behavioural row anywhere in the study.

A16 and A17 fit neither. They were adopted after rows existed, they were
scientific rules rather than apparatus faults, and they were declared —
correctly — as adopted after observations. §32's own text describes *"a
single append-only register carrying the amendment text, its timing relative
to every affected artifact, what it supersedes, and what it leaves untouched"*,
and no v6 code implemented one. So the two amendments were recorded in prose,
the manifest could not be re-signed without discarding every row, and the
pre-freeze audit correctly refused the document it was handed.

## What it is not

Not a defect in A16 or A17: both were right and both are carried into v7. Not
a defect in the audit: `protocol_hashes_agree` did what it was registered to
do. It is a hole in the lifecycle's vocabulary — the third path §32 describes
did not exist — and the cost was the only v6 replication that had reached the
audit.

## What v7 does

v7 A4: `registration_run.amend_registration` writes a signed, append-only
amendment record linking the document hashes in force to the amended ones,
with the stage each replication had reached and its row count at adoption,
the declared direction and the §32.2 disclosure. `manifest.document_binding`
walks the chain and the pre-freeze audit reads its head. §32.3 is refused
executably: no amendment naming §13 once any replication holds a Gate-2.5
record. `dci1/tests_v7/test_amendment_chain.py` drives the v6 case — a
document edited under a registration with rows — to a passing audit once the
amendment is bound, and to the same failure it produced here when it is not.

## What was not done

No v6 record was edited, moved or retired. The terminal report, the transition
log, the registration manifest and the amended preregistration are all as they
were at 09:56:25 on 2026-08-27, and `dci1/reports/dci1v6/closure.json` records
the status.
