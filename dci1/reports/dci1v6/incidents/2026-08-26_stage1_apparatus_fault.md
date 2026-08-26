# Incident: stage 1 recorded `REGISTRATION_INCOMPLETE` on an apparatus fault

**Status: RESOLVED 2026-08-26 under amendment A15 — reading (B), apparatus
fault. See "Resolution" at the end. Everything below this line is the report
as written while the incident was open, and is left exactly as it was.**

Written 2026-08-26, after the first attempt to run `PROTOCOL_REGISTERED`.

## What happened

```
$ .venv/bin/python3 -m dci1v6.run.cli run \
      --stage PROTOCOL_REGISTERED --model gemma-3n-e2b-it
{"error": "TerminalStatus",
 "message": "PROTOCOL_REGISTERED: REGISTRATION_INCOMPLETE"}
```

The blocker recorded in
`evidence/dci1v6/gemma-3n-e2b-it/terminal_report.json` is:

| document | declared | required |
|---|---|---|
| `user-notes/DCI1_preregistration_v6.md` | **`missing`** | `ADOPTED` |
| `dci1/reports/dci1v6/reference_design_spec.json` | **`missing`** | `ADOPTED` |

**Neither document is missing.** Both are committed at the producing commit
the record itself names, `0ba60e4`, and both declare `ADOPTED`:

```
$ git show 0ba60e4:user-notes/DCI1_preregistration_v6.md | grep -m1 status:
    status: ADOPTED
$ git show 0ba60e4:dci1/reports/dci1v6/reference_design_spec.json  -> "_status": "ADOPTED"
```

`manifest.signing_blockers(repo_root=<repository root>)` returns `[]` and
`plan_registration` reports `can_register: true`.

## The defect chain

Three separate faults, all in the **documented entry point** and none in a
scientific rule. Two are repaired; the third is what this incident is about.

1. **The CLI created no signing key.** Every stage record is signed at write
   and verified at read, so `run --stage PROTOCOL_REGISTERED` failed on a
   missing key before reaching stage 1 at all. v4's runner created it
   explicitly; v6's had no equivalent. *Repaired:* `cli.ensure_signing_key`
   creates it once, and refuses to mint a replacement once a registration
   manifest exists — a key that vanishes after a study is registered is a
   lost key, and a new one would leave every signed record unverifiable.

2. **The CLI did not forward `--repo-root`.** `run_registration` takes
   `repo_root` and defaults it to `"."`, so the guard read the process's
   working directory. Invoked from `dci1/`, `user-notes/…` and
   `dci1/reports/…` do not exist, and `assert_documents_adopted` correctly
   reported them **missing**. *Repaired:* `cli.repo_root_of` defaults to the
   repository this package lives in, never the cwd, and `run` forwards it to
   every runner whose signature accepts it. A registration whose content
   depends on the caller's working directory is not a registration.

3. **Stage 1 is not retryable, and it has to be.** This one is **not**
   repaired and is the researcher's question.

## The question

`run.lifecycle.run_stage` writes a §28.3 `terminal_report.json` for **any**
`TerminalStatus`, and `transitions.assert_predecessor_passed` then refuses
every later stage for that replication, permanently. `REGISTRATION_INCOMPLETE`
is in `C.TERMINAL_STATUSES`, so it takes that path.

Two statements in the registered implementation cannot both be true:

> `protocol/decisions.choice()`: *"Close it with `decisions.close(...)` and
> record it in the signed registration manifest; §18 stage 1 returns
> `REGISTRATION_INCOMPLETE` **until then**."*

> `engine/transitions.assert_predecessor_passed`: *"{model} is terminal at
> {status}; every later stage is mechanically disabled."*

"Until then" presupposes a later attempt. If a stage-1 blocker is irreversible
then `signing_blockers`' whole vocabulary — open decision, unresolved
specification question, missing topic hash, unapproved candidate population,
unspecified floor, unpinned model revision, non-derivable design, draft
document — is unreachable: each names work a researcher has to do, and the
first invocation that finds any of it outstanding kills the replication.

**As things stand, `gemma-3n-e2b-it` cannot run v6.** §6.1 registers four
replications. One command, issued before any registration existed and before
any row was generated, has reduced that to three — on a fault in the caller,
not in the study.

## What has NOT been done

- The terminal report and the transition log are **preserved in place**,
  unedited, in both the evidence tree and the durable mirror.
- No lifecycle, transition or manifest rule has been amended.
- `registration_run.supersede_registration` is the registered §32 path for
  replacing a registration before any observation exists, and it is **not
  available here**: it retires records under `superseded/<old manifest
  hash>/` and no manifest exists to name.
- No registration has been signed. **Zero v6 behavioural rows exist.**

## What the researcher has to decide

Whether a `REGISTRATION_INCOMPLETE` recorded before any registration exists,
by a mis-invoked caller, on a study whose blockers were already clear, is:

**(A) a §28 terminal outcome.** `gemma-3n-e2b-it` is dead for v6 and the
study runs three replications. Nothing is amended. The cost is one
replication of four, lost to a CLI defect.

**(B) an apparatus fault.** The record is retained and labelled as one, the
replication is re-run, and `run_stage` is amended so a readiness verdict at
stage 1 logs a refusal instead of writing a §28.3 terminal report — which is
what makes "until then" true. This is a §32 amendment to a governed path,
adopted after a gate ran, so §32.2 requires it be declared as such. It is
**not** a §32.1 weakening: the criterion `signing_blockers` applies is
untouched and was already satisfied when the fault occurred; what changes is
whether a readiness verdict is irreversible.

Either way the incident, the fault, and the record stay on the evidence tree.

---

## Resolution (2026-08-26)

The researcher ruled **(B): an apparatus fault**, retained the full four-model
panel, and adopted amendment **A15** — a prospective §32 amendment, taken after
adoption, before any v6 behavioural row, and declared under §32.2 in
`user-notes/DCI1_preregistration_v6.md` §4. `READINESS.md` §15 records the pass.

### The preserved artifacts, by hash

Computed before anything moved, so a later reader can prove what was retained:

| artifact | sha256 |
|---|---|
| `evidence/dci1v6/gemma-3n-e2b-it/terminal_report.json` | `fb9b4353b50ec2221b6a1de33465427ae3ab3a4aac81189645e5520711ed6122` |
| `durable_root/dci1v6/gemma-3n-e2b-it/terminal_report.json` | `fb9b4353b50ec2221b6a1de33465427ae3ab3a4aac81189645e5520711ed6122` |
| `evidence/dci1v6/gemma-3n-e2b-it/transition_log.jsonl` | `27fe38ba22f144ceabd77b3eb9259a6be3199f796139786a611d2fac627993d2` |
| this report, as written while open | `9f3b86506758603aba9a482543f7388ea6aefce59a479d594c2a7a5b7258a65c` |

The `record_hash` **inside** the signed report is
`bf66cdd54401533bbd88dc22a9d74052409e7891f05f7e29766537bdf7d34805`; the two
transition rows the failed attempt wrote are
`92a7e1a4552168a5cda66e62d6b2e27088b027990ba20017488e9673f6b43aaf` (TERMINAL)
and `097d2400087bbcb50818178a3edabc8751beaf5ee3f247d564ec4ff2c8a5add5`
(REFUSED). The retirement names the **file** hash, because that is what
identifies the record a reader would open.

### What changed

**Prospectively.** §18 stage 1's `REGISTRATION_INCOMPLETE` is a readiness
refusal, not a §28 terminal status. `run/lifecycle.ReadinessRefusal` fails
closed, writes no stage record and no terminal report, logs a `REFUSED`
transition carrying the blockers and the remedy, and leaves the replication
retryable. `C.READINESS_REFUSAL_STATUSES` and `C.TERMINAL_STATUSES` are
disjoint, asserted at import; `TerminalStatus` refuses a readiness status,
`write_terminal_report` refuses one, and `ReadinessRefusal` refuses any gate
but `PROTOCOL_REGISTERED`. **The criterion is untouched** — `signing_blockers`
decides readiness exactly as it did — and no §28 terminal outcome became
retryable.

**For this record.** `run/registration_run.retire_apparatus_fault` retired it
under `superseded/apparatus_fault/<record hash>/`, in the evidence tree and in
the durable mirror, byte-identical. It refuses on a hash mismatch, an
unverifiable signature, any gate but stage 1, any §28 status, an existing
manifest, any behavioural row anywhere in the study, and a replication that
already holds a stage record. The transition log kept every row. The
registration signed afterwards binds the retirement in its own payload, and
`closure.json` reports it separately from the terminal statuses.

### What did not change

No threshold, estimand, criterion, population, model, reference family, arm,
seed, verifier, prompt, wording, claim ladder or headroom band. Not `m*`. §34
D23 remains `projection_sd`, D26 remains `0.0142`. §6.1's four replications are
four.

### The two engineering repairs

`cli.ensure_signing_key` creates the study key once through the documented
entry point and refuses to mint a replacement after a manifest exists;
`cli.repo_root_of` defaults `--repo-root` to the repository the package lives
in, never the working directory, and `run` forwards it to every runner whose
signature accepts it. Both carry regression tests in
`tests_v6/test_run_layer.py`.
