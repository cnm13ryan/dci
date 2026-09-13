# DCI-1 v8.1 — freeze and confirmatory generation, provenance record

Written 2026-09-10 so the pre-freeze and freeze state is recoverable
without reconstructing the session that produced it. No composed outcome is
read, summarised or computed from here; the registered analysis stage
(`CONFIRMATORY_ANALYSIS`) is the first place those may be touched.

## Identities

| what | value |
|---|---|
| confirmatory root | `dci1/evidence/dci1v8p1-confirm` |
| bound commit (freeze and generation) | `034fc7214762b6848d5d904b14fd82b317830667` |
| registration manifest commit | `c0b52ca203b7179b90bbbf088a6952fcc2b8a805` |
| preregistration | `dci1/docs/DCI1_preregistration_v8.1.md`, hash `d3552f9f47e3f00800622f033cfad579dcd6085b1068f0bcb35c643e8bb1908d` |
| membership lock | `dci1/reports/dci1v8dev/confirmatory_membership.json`, hash `31af521c…` |
| confirm manifest | hash `8cfa20827b3f46fc…` |
| verifier / wording | `ea885b0db67e3c7c…` / `fe3b5be15759af1c…` |
| protocol version | `8.1-confirmatory` |

A differing manifest commit and freeze commit is normal and has precedent:
the v8 root `dci1v8-confirm-r2` registered at `3bfcb12` and froze at
`f7af7f2`. Here the gap is the membership-lock commit, which must exist in
a clean worktree before the freeze can read it.

## Bound pilots

| model | pilot root | pilot commit |
|---|---|---|
| qwen3-4b | `dci1v8-pilot-r14` | `025e138` |
| qwen3-4b-instruct-2507 | `dci1v8-pilot-r15` | `025e138` |
| gemma-3n-e2b-it | `dci1v8-pilot-r16` | `025e138` |
| gemma-3n-e4b-it | `dci1v8-pilot-r23` | `7d8e1d9` |

The two commits differ only in the backend wall-clock cap, audited as
operational-only (preregistration Appendix B). No topic-replicate root
(`dci1v8-pilot-t1-*`, study id `dci1v8-topicrep`) is or can be bound:
`confirm/pilot_import` admits study id `dci1v8` only.

## Membership and readiness

| model | LOCAL frames | SPECTRUM frames | runner-up arms | freeze record |
|---|---|---|---|---|
| qwen3-4b | 0, 1, 2, 3 | 0, 1, 2, 3 | 0, 1, 2, 3 | `7902b05f12a2bb60` |
| qwen3-4b-instruct-2507 | 1, 3 | 1, 3 | — | `4d72e728af137746` |
| gemma-3n-e2b-it | 0, 1, 3 | 0, 1, 2, 3 | 0 | `33595b8078525a12` |
| gemma-3n-e4b-it | 0, 1, 3 | 0, 1, 2, 3 | 0, 1 | `70bcb5da77f2cbca` |

12 LOCAL frames, 14 SPECTRUM frames, 384 blocks per frame. Runner-up arms
sit exactly where §12.3's re-selection bootstrap marks a LOCAL frame's
coordinate unstable — including gemma-3n-e2b-it frame 0, the frame the
topic-resampled validation showed selecting three different operating
points across three samples. Readiness: **11 of 11 items passed for every
model**; `LOCAL_TOPUP` generated 768 rows for gemma-3n-e4b-it and none for
the others.

## Generation

Started 2026-09-08 15:48:13Z, two models at a time, one per card.

| model | planned rows | status | record hash |
|---|---:|---|---|
| qwen3-4b | 715,776 | PASS 2026-09-09 03:15Z | `287e507ed9b1dc86` |
| qwen3-4b-instruct-2507 | 344,064 | PASS 2026-09-09 12:42Z | `a98dc7aa45f75ed0` |
| gemma-3n-e4b-it | 669,696 | PASS 2026-09-10 05:28Z | `e4dd54ff8575dcee` |
| gemma-3n-e2b-it | 623,616 | PASS 2026-09-10 06:33Z | `117e95aa9a8b2ae1` |
| **total** | **2,353,152** | **all four PASS** | |

Confirmatory generation is **complete** for every entering model, all four
records signed at the frozen commit `034fc72`. The next registered stage is
`CONFIRMATORY_ANALYSIS`, which is the first stage permitted to read a
composed outcome; nothing before it has read, summarised or computed from
one.

## Confirmatory analysis and final report (2026-09-10)

Both remaining registered stages ran once, from the same clean worktree at
the same bound commit, CPU only, and returned `PASS` for every model. Each
analysis record re-read the rows on disk, matched the count against the
generation record, and asserted its inputs against the freeze hash it was
signed under.

| model | analysis record hash | recorded at | final report hash |
|---|---|---|---|
| qwen3-4b | `5591cb46c64c127a` | 2026-09-10T13:54:01Z | `af7138f534420738` |
| qwen3-4b-instruct-2507 | `31f1b46be5e6416e` | 2026-09-10T13:49:50Z | `3dfab3cd8904acfa` |
| gemma-3n-e2b-it | `5edcd5730bc4c031` | 2026-09-10T13:53:39Z | `2fad8b4cab4cbaaa` |
| gemma-3n-e4b-it | `e90e0f7d6606bd8d` | 2026-09-10T13:56:09Z | `c6666bdbabcdd2ee` |

Bootstrap resamples 10,000, as registered. `FINAL_REPORT` is the last stage
of the lifecycle; the root is complete and every stage is write-once, so a
re-analysis would need a fresh root and re-generation.

The results, their registered readings, every registered sensitivity and the
manuscript rewrite map are in
`V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md` at the repository root, with the
machine-readable tables under `reports/dci1v8dev/postconfirm/data/`.

## Where the pre-freeze evidence lives

- `reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md` — the
  methodology-validation record: §3.5 decoding re-executions, §3.6 the
  v8-design control, §3.7 the topic-resampled replicates, §4 validation and
  the reuse defect, §5 the verdict, decisions and limitations.
- `docs/V8_TOPIC_RESAMPLED_VALIDATION.md` — the replicate's prespecified
  plan, committed before any replicate row was generated.
- `docs/DCI1_preregistration_v8.1.md` Appendix C (DRAFT→final change
  record) and Appendix D (the three kinds of evidence and what each
  licenses).
- The superseded v8 lock is archived at
  `reports/dci1v8dev/confirmatory/confirmatory_membership.f7af7f2.v8.{json,md}`.

## Limitations carried into the confirmatory study

1. qwen3-4b-instruct-2507's LOCAL eligibility ({1, 3}) is sensitive to
   which pre-freeze topics land in which role: a resampled partition gives
   {3} alone and no eligibility. The registered rule decides on the bound
   pilot, so the model enters; the sensitivity is reported beside its
   result.
2. gemma-3n-e2b-it frame 0 and qwen3-4b-instruct-2507 frame 0 have
   knife-edge operating points. The registered instrument is the runner-up
   arm, which carries no claim.
3. What the pre-freeze estimator *selects* (forwarded rungs, references) is
   much less stable than what it *decides* (LOCAL/SPECTRUM verdicts).
