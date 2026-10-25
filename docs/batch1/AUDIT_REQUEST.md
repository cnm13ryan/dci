# Batch 1: independent audit request (third audit)

**Date:** 2026-10-25. **Requested by:** the researcher, before any work on the
GPU instance (the step-5 stop of the Lambda run plan). **Branch:**
`feat/batch1-pilot-calibration`. **What is asked:** an independent check
that the changes since the last audit are correct, keep every earlier
safeguard, and are safe to take to the instance. Treat every claim in
`docs/batch1/`, including this file, as untrusted.

**Rules for the auditor:**

- do not modify the repository;
- run no model inference;
- do not touch the Lambda instance;
- write no approvals;
- put temporary probes outside the repository.

## 1. What the last audit saw, and what changed since

The last audit was the re-audit of 2026-10-19, which found R1-R4. The code it
read was uncommitted then. It is now in commit `101426c`, together with the
remediation of R1-R4, which **no auditor has seen yet**.

| commit | what it adds | audited? |
|---|---|---|
| `101426c` | all of Batch 1 as of 2026-10-19 15:11, including the remediation of R1-R4 (`REMEDIATION_REPORT.md` §R): 88 topic rewrites and the semantic review, the portable code hash, provenance binding in Freeze 2, per-attempt logs, the retry limit, the non-focal smoke test, the near-threshold flag, and the coverage study | the remediation part: **no** |
| `bc80cc2` | `dci1/environments/backend-cuda` (torch +cu128), built by another session; superseded below and not to be attested | no; check only that nothing uses it |
| this round (`101426c..HEAD`) | the researcher's decisions of 2026-10-25 and the CUDA path (§2) | **no** |

Diff to read: `git diff 101426c..HEAD`, plus the R-remediation inside
`101426c`. The researcher's decisions are in `DECISIONS_2026-10-25.md`.

## 2. Changes in this round, and what to check

**Topics (D05).** Files: `src/dci/batch1/data/topics_source.json`,
`topics_semantic_review.json`, `report.py` (`topic_replacements`,
`splice_generated`), `cli.py`, `TOPIC_REVIEW.md` §2a and §3c.

- The containment rule was applied to all 67 kept CLOSE pairs by two blind
  judges. The 24 judged a restatement by either were rewritten.
- `b1-history-28` and `b1-technology-20` now carry an 11+-letter word.
- 26 new questions; a fresh second and third review pass.
- **Check:**
  - that no new question restates a historical or bank question (read them
    against the 1,472 historical questions);
  - that the rewrites keep id, opening word, b/z and length within one word;
  - that the split is unchanged;
  - that the 24 old questions are recorded as RESTATEMENT and would make the
    report unclean;
  - that the generator cites partners as they stood at review time;
  - whether rewriting the union of both judges' verdicts, rather than their
    intersection, was justified.

**D11.** `config.py`: `p3_min_additional_other_operation` = 3.

- **Check:** that `references.coverage` and the feasibility verdict use it,
  and that nothing still assumes 2.

**Python 3.12 (D12).** `config.py` (`ORCHESTRATOR_PYTHON`), `.python-version`,
`.github/workflows/cpu-tests.yml`.

- **Check:**
  - that every command refuses another minor version;
  - that payloads and Freeze 1 record 3.12;
  - that CI's job now matches;
  - that code hashes are still identical across 3.11-3.13
    (`test_every_frozen_source_hashes_the_same_under_3_11_and_3_13`).

**Execution requirements and the lock decision (D12).** `config.py`
(`EXECUTION_REQUIREMENTS`, in the D12 payload), `environment.py`
(`PROBE_SCRIPT`, `identity_of`, `requirement_problems`, `HOST_FIELDS`, lock
schema v2), `freeze.py` (`_environment`).

- The identity now binds GPU count, compute capabilities and per-device
  memory (GiB). Hostname, kernel, GPU UUIDs and driver are recorded only.
  A host outside the requirements cannot be locked, and an edited lock blocks
  Freeze 1.
- **Check:**
  - that the probe reads these fields correctly on CUDA; in particular
    `nvidia-smi` parsing, and torch's `uuid` property;
  - that comparing per-device memory rounded to GiB is stable on one SKU;
  - that the visible GPU count at attestation and at `execute` cannot
    differ by accident (both probes inherit the shell's
    `CUDA_VISIBLE_DEVICES`);
  - that nothing in the identity varies between two probes of one host.

**One worker per GPU.** `runner.py` (`execute(devices=...)`) and `cli.py`
(`execute/resume --devices 0,1`).

- `(stage, model)` groups run on a thread pool, one worker per device. Each
  worker is a seam subprocess with its own `CUDA_VISIBLE_DEVICES`; the root
  lock, design authentication and the live check stay in the parent. Each
  `backend_run` event records `device`.
- **Check:**
  - thread safety: groups write disjoint directories, and nothing shared is
    written concurrently;
  - error handling: one group's failure does not lose another's rows, the
    first error is raised, and resume completes;
  - that results do not depend on device assignment;
  - that Freeze 2 and the evidence checks accept the new `device` field and
    still bind provenance;
  - that the smoke test (single `--device`) is unaffected.

**CUDA backend.** `environments/cuda-vllm/pyproject.toml` and `uv.lock`.

- Python ==3.12.*, vllm 0.15.1 (cp38-abi3), and torch, torchvision and
  torchaudio from the explicit cu129 index, with resolution limited to Linux
  x86_64.
- **Check:**
  - that the lock pins `torch 2.9.1+cu129` from that index and nothing else
    resolves torch from PyPI;
  - that the seam (`exploratory/vllm_backend`) runs unchanged under it: its
    hash is unchanged, and it imports no ROCm-only module on the Batch 1
    path;
  - that `rocm_smi_memory` failing quietly on NVIDIA is harmless.

**Lambda scripts.** `scripts/lambda/*.sh`, README:

- `preflight.sh`, `bootstrap.sh`, `fetch_models.sh` and `sync_back.sh`;
- `gpu_monitor.sh` and `gpu_peaks.sh`, which measure peak memory with
  `nvidia-smi`.

- **Check:**
  - that they are idempotent;
  - that they do nothing the run rules forbid: apt upgrades, driver changes,
    shutdown, installs outside the locks, `--torch-backend=auto`,
    `vllm download-kernels`, or secrets on command lines;
  - that `sync_back.sh` really verifies every file on the Mac.

**Documents.** `DECISIONS_2026-10-25.md` (the D10 disclosure, the D14
flag-to-action rule, the D12 wording and conditions), `README.md` §9-10,
`CHANGES_SCIENTIFIC.md`, `RESEARCH_STATE.md`.

- **Check:** that they match the code.

## 3. Known facts about the instance

These were reported by another session; not verified here, and not to be
acted on:

- **Hardware:** 2x NVIDIA H100 80GB HBM3, driver 580.126.20, Ubuntu 24.04.4,
  NFS at `/lambda/nfs/dci`.
- **What exists there:**
  - a clone at `bc80cc2` from a git bundle (the box has no GitHub access);
  - a Python 3.11 repo `.venv`;
  - the +cu128 backend;
  - all four models at their pinned revisions in `/lambda/nfs/dci/hf`.
- **What has not run:** no generation, no run roots, no attestation, no
  smoke test.
- **Consequence:** both environments there must be rebuilt for this commit
  (Python 3.12, cu129) before attestation.

## 4. How to reproduce the tests

On the Mac, CPython 3.12. The DCI-1 suite has its own `dci1/.venv`.

```bash
P=.venv/bin/python
$P -m pytest tests/batch1 -q -m "not slow"                      # Batch 1 CPU tier
$P -m pytest tests/batch1 -q -m slow                            # full synthetic demo
$P -m pytest tests --ignore=tests/batch1 -q -m "not slow and not gpu and not rocm and not cuda and not cloud"
$P -m pytest exploratory/tests -q                               # 6 pre-existing failures (test_runlock_ownership)
(cd dci1 && .venv/bin/python -m pytest tests_v8dev -q -p no:cacheprovider -m "not slow and not gpu")  # 5 failed + 3 errors pre-existing
$P -m dci.batch1 write-review-artifacts --out "$(mktemp -d)"   # compare with docs/batch1
```

The results for this commit are in the commit message, and in the report
that accompanied the push.
