# Batch 1 on Lambda Cloud: read-only recon

**Date:** 2026-10-25, revised for the 2x H100 SXM brief and the decisions
recorded that day. **Scope:** step 1. Read-only on the Mac: no code, protocol
value, environment or approval was changed. The only network access was
public metadata: four Hugging Face model pages and the PyPI page for
vllm 0.15.1. **Not covered:** I have not independently re-verified the
remediation made after the 2026-10-19 re-audit.

## 0. Step 1 gate: STOP

| STOP condition | holds? | evidence |
|---|---|---|
| the lock cannot follow the lock decision without a protocol change | **no** | a code change in `environment.py` (D12's implementing module) is needed, but no protocol value changes (§7) |
| the runner cannot use two GPUs through configuration alone | **YES** | one `execute` process holds a root-wide lock and runs every model group in sequence on one `--device` (§6) |
| a decision cannot be applied as written | no | each decision checked (§8) |

Open items carried forward, none of them a STOP:

| # | item | effect |
|---|---|---|
| 1 | **No Batch 1 code is committed or pushed** (§5) | "clone the pushed SHA" needs step 5 first |
| 2 | The orchestrator must be CPython **3.11**; Ubuntu 24.04 ships 3.12 | uv would fetch a managed CPython 3.11, which no lockfile pins. Is that allowed under "no installs outside the lockfile"? |
| 3 | The current lock does **not record the NVIDIA driver, GPU count, compute capability, memory, UUIDs or hostname** (§1) | the lock decision adds these (§7) |
| 4 | The smoke report has **no peak-memory figure** on NVIDIA (§2) | step 8 asks for it; it must be measured outside the protocol code, for example by sampling `nvidia-smi` in tmux |
| 5 | **Both Gemma 3n models are gated** (§4) | the HF account whose token `fetch_models` uses must have accepted the Gemma licence |
| 6 | Runtime kernel fetches by vLLM 0.15.1 / FlashInfer on CUDA: **not verified** | `HF_HUB_OFFLINE=1` does not stop them; check the smoke logs for network fetches or JIT builds |
| 7 | `--accelerator cuda` already exists (§2) | step 3's "add it if missing" does not apply. Editing `runner.py`, `environment.py`, `outcomes.py`, `design.py` or `exploratory/vllm_backend/*.py` changes D12's payload hash or the seam hash |

## 1. What `attest-environment` records and how it is compared

`attest-environment --backend-python P --out environment_lock.json`
(`src/dci/batch1/cli.py:144`):

1. It runs `PROBE_SCRIPT` in `P` with `-I` (`environment.py:117-133`), using the shell's environment.
2. It refuses unless the probe succeeds, vLLM is installed and the backend is Python 3.12 (`environment.py:149-165`).
3. It writes `{schema, status: ATTESTED, identity, identity_hash, host}`.

Two checks use the lock:

- **validate-freeze** (`freeze.py:166-184`, `302-326`). The lock is carried over, not re-probed. The check:
  - requires `status == ATTESTED`, otherwise Freeze 1 records UNATTESTED and is blocked;
  - recomputes `identity_hash`;
  - requires `backend_source_hash` to equal the current seam tree;
  - requires the backend's Python minor version to be 3.12.
- **execute / resume** (`freeze.py:329-357`, `runner.py:381-385`). It re-probes the backend interpreter live. `identity_of(live)` must equal the locked `identity` **field for field**; otherwise it exits 3 and launches nothing.

| field | tag | where | validate-freeze | execute / resume |
|---|---|---|---|---|
| `python` (full version, e.g. 3.12.x) | software | identity | in `identity_hash`; minor must be 3.12 | exact match |
| `implementation` | software | identity | in `identity_hash` | exact |
| `packages`: vllm, torch, transformers, tokenizers, triton, xformers, flashinfer-python, numpy (None when absent) | software | identity | in `identity_hash`; vllm must be non-null at attest | exact |
| `distributions_hash` (SHA-256 of every `name==version` in the backend venv) | software | identity | in `identity_hash` | exact: **any** install after attestation blocks execution |
| `torch_cuda` (`torch.version.cuda`) | software (build) | identity | in `identity_hash` | exact |
| `torch_hip` | software (build) | identity | in `identity_hash` | exact (None on CUDA) |
| `accelerators`: the **sorted set of device names**, not the count, index, UUID or VRAM | hardware | identity | in `identity_hash` | exact |
| `backend_source_hash`: code hashes of `exploratory/vllm_backend/**/*.py`, `__pycache__` excluded; currently `e4e5f103…43c9b1` over 18 files | software (seam code) | identity | must equal the live seam tree | exact; live value recomputed from the checkout |
| `identity_hash` | (consistency) | top level | recomputed | none |
| `interpreter`, `executable` (paths) | host identity | host | recorded only | not compared |
| `platform` (`platform.platform()`: kernel, glibc) | host identity | host | recorded only | not compared |
| `distributions` (count) | software | host | recorded only | not compared (the hash is) |
| `accelerator_error` | hardware | host | recorded only | not compared |

**Not recorded anywhere in the lock:**

- the NVIDIA driver version and the CUDA driver API version;
- GPU count, UUID and serial number;
- instance id and hostname;
- environment variables (`VLLM_*`, `CUDA_VISIBLE_DEVICES`, `HF_*`);
- model-weight file hashes (the plan carries only the revision SHA);
- the orchestrator's packages. Freeze 1 records only its Python minor version and implementation; the root `uv.lock` is the control.

The seam's own per-run provenance (`hardware.probe`) does record device names, VRAM and `VLLM_` / `TORCH_` / `PYTORCH_` / `NCCL_` environment variables.

**Practical consequences:**

- **Attest and execute from the same shell environment.** For example, if `CUDA_VISIBLE_DEVICES=""` at attestation, `accelerators` would be `[]` and every later run would be refused.
- **Install nothing in the backend venv after attestation.**

## 2. Accelerator handling and ROCm-only branches

**`--accelerator`.** It accepts `rocm` or `cuda`, and **defaults to `rocm`**. It exists on `smoke`, `execute` and `resume` (`cli.py:373`, `382`). `attest-environment` has no accelerator flag.

**`--device`.** One integer, default 0, so a run uses one GPU. With `cuda`, `BackendSpec.env()` (`runner.py:102-110`):

- clears any inherited `ROCR_` / `HIP_` / `CUDA_VISIBLE_DEVICES`;
- sets `CUDA_VISIBLE_DEVICES=<device>`;
- always sets `VLLM_WORKER_MULTIPROC_METHOD=spawn`;
- sets `HF_HUB_OFFLINE=1` unless the shell already sets it.

**The backend process.** It is started as `<backend python> -u -m vllm_backend --plan … --design … --out …`, with `cwd=exploratory/` (`runner.py:185-189`). The seam therefore runs from the checkout; the backend venv does not need `dci` installed.

| ROCm-only or ROCm-default item | file | effect on NVIDIA |
|---|---|---|
| `--accelerator` default `rocm` | `cli.py:373`, `382` | **pass `--accelerator cuda` on every smoke, execute and resume.** If it is forgotten, `HIP_VISIBLE_DEVICES` is set, `CUDA_VISIBLE_DEVICES` is cleared and every GPU is visible |
| `BackendSpec.python` default is `dci1/environments/backend/.venv/bin/python` (the ROCm stack) | `runner.py:96` | **pass `--backend-python` on attest, smoke, execute and resume** |
| `hardware.rocm_smi_memory()` calls `rocm-smi` | `exploratory/vllm_backend/hardware.py:99` | returns `{}`: seam provenance has no VRAM-use figure. `torch_memory_this_process` covers only the parent process |
| `gcn_archs` / `is_rdna3` | `hardware.py:33`, `72` | empty or False; nothing on the Batch 1 path branches on them. Preflight checks only architecture support, the reasoning parser, and TP against visible devices |
| `torch_hip` in the lock | `environment.py:103`, `144` | None |
| `enforce_eager=True`, `disable_custom_all_reduce=True` (ROCm workarounds) | `runner.py:121` | apply on CUDA too. Eager mode disables CUDA graphs, so expect slower throughput than vLLM's default. These are bound protocol values, not to be changed |

## 3. Models (`src/dci/batch1/config.py:75-89`, `runner.py:113-134`)

Common to all four models:

| setting | value |
|---|---|
| dtype | bfloat16 |
| max_model_len | 4096 |
| tensor-parallel size | 1 |
| quantization | none |
| `trust_remote_code` | False |
| CPU offload | 0 |
| engine seed | 20261018 |
| decoding | temperature 0.7, top-p 0.9, top-k 50, cap 512 tokens, chunk 64, `NO_THINKING` |

| key | HF id | revision | GPU memory fraction | GPUs | thinking / template kwargs | gated |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | `google/gemma-3n-E2B-it` | `5e092ebca197cdcd8d8b195040accf22693501bc` | 0.85 | 1 (`--device`) | unavailable / `{}` | **yes (manual, Gemma licence)** |
| gemma-3n-e4b-it | `google/gemma-3n-E4B-it` | `c1221e9c62e34a43ab7ffacd1be0ea71f126ef10` | 0.95 | 1 | unavailable / `{}` | **yes (manual, Gemma licence)** |
| qwen3-4b | `Qwen/Qwen3-4B` | `1cfa9a7208912126459214e8b04321603b3df60c` | 0.85 | 1 | disabled / `{"enable_thinking": false}` | no (Apache-2.0) |
| qwen3-4b-instruct-2507 | `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` | 0.85 | 1 | unavailable / `{}` | no (Apache-2.0) |

Notes:

- **Revisions:** on 2026-10-25 all four pinned revisions equalled each repository's current `main` SHA on Hugging Face.
- **GPU memory fraction:** it is a fraction of total VRAM. On an 80 GB card, 0.95 reserves about 76 GB. The workstation cards had 24 GB, so any card of 24 GB or more that supports bf16 fits. A V100 does not support bf16.
- **One GPU suffices.** Models run one per backend process, in sequence, and the run lock refuses a second process on the same root, so extra GPUs would sit idle.
- **Throughput estimates don't transfer.** The figures in `estimate.md` are RX 7900 XTX rates; the smoke test is the first measurement on NVIDIA.

## 4. Gated models

- Both Gemma 3n checkpoints are `gated: manual`; both Qwen checkpoints are open.
- A token is needed only while `fetch_models` runs. After that, `HF_HUB_OFFLINE=1` and the runner's own default keep the hub offline.
- Loading uses `model=<id>, revision=<sha>`, so the snapshot for that exact SHA must be in `HF_HOME`.

## 5. Git state

| item | state |
|---|---|
| branch | `feat/batch1-pilot-calibration`, **no upstream; not on origin** |
| HEAD | `0d85a8e2e507c1d7b45f37fd75b9d5d102749b9f`, the `main` merge of PR #44. It contains **no Batch 1 code** |
| untracked | 79 files under `src/dci/batch1/`, `tests/batch1/`, `docs/batch1/`, and the root `.python-version` (`3.11`), which `require_orchestrator`'s instructions rely on |
| modified, uncommitted | `CHANGES_SCIENTIFIC.md`, `README.md`, `RESEARCH_STATE.md` (+68 lines) |

So **Batch 1 is neither committed nor pushed, and there is no SHA to give.**

Freeze 1 binds code hashes, not a git commit. The pushed SHA the instance clones therefore has to be recorded alongside the freeze, for example by the Lambda scripts and `sync_back` manifests.

## 6. How the runner places work on GPUs (the STOP)

`execute` and `resume` (`runner.py:367-422`, `cli.py:207-224`) work like this:

1. Probe the backend once and check authorisation.
2. Take `run_lock(root)`, a non-blocking exclusive `flock` on `<root>/RUN.lock` (`store.py:156-171`). A second process on the same root is refused: "concurrent runs on one root are refused".
3. Group the design by `(stage, model)` and run the groups **one after another** (`runner.py:401-412`). Each group is one blocking `subprocess.run` of the seam.
4. Every subprocess gets the same `BackendSpec`, so the same single `--device` (`CUDA_VISIBLE_DEVICES=<device>`).

| way to use a second GPU | possible by configuration alone? | why |
|---|---|---|
| `--device 0,1` | no | `--device` is an `int` (`cli.py:384`) |
| TP=2 | no, and excluded by the decision | TP stays as configured (1); TP is in the model config, bound by D12 |
| two `execute` processes on the same root, `--device 0` and `--device 1` | no | `RUN.lock` refuses the second; `execute` also has no model filter, so both would run every group |
| two roots, one per GPU | no | each root needs its own Freeze 1 and the full stage design; Freeze 2 binds one root's evidence |

**Using the second GPU needs a code change.** One shape fits "one worker per GPU" and keeps every existing invariant:

- `execute` gains `--devices 0,1`;
- while holding the single root lock, it runs the `(stage, model)` groups on a pool of one worker per device;
- each worker is one seam subprocess with its own `CUDA_VISIBLE_DEVICES`.

The groups already write disjoint directories (`generation/<stage>/<model>/`), and authentication, the live environment check and Freeze 1 stay in the parent process.

This edits `runner.py` and `cli.py`:

- `runner.py` is D12's implementing module, so D12's payload hash changes;
- both files are in Freeze 1's rule modules;
- it changes the gated execute path, which the independent audit must then cover.

**The alternative needs no code change: run on GPU 0 only.** The pilot is at most 30,976 responses of at most 512 tokens. At the historical RX 7900 XTX rates that is about 1.2 GPU-hours; an H100 should be faster, but the smoke test measures it. The second GPU would sit idle.

## 7. Can the lock follow the lock decision?

**Yes, with a code change and no protocol-value change.** The decision binds software identity plus GPU class: model, count, compute capability and memory. It records hostname, GPU UUIDs, driver build and kernel without binding them.

| decision item | today | change needed |
|---|---|---|
| software identity | bound (§1) | none |
| GPU model | bound as a set of names | keep |
| GPU count | not recorded (the set hides it) | add `torch.cuda.device_count()` to `PROBE_SCRIPT` and `identity_of` |
| compute capability | not recorded | add `torch.cuda.get_device_capability(i)` per device |
| memory | not recorded | add `total_memory` per device, rounded to whole GiB so the same SKU compares equal |
| hostname, GPU UUIDs, driver build, kernel | kernel only (`host.platform`) | add to `host` (recorded, not compared). UUIDs and driver come from `nvidia-smi --query-gpu=uuid,driver_version` (NVML); torch 2.9 also exposes `get_device_properties(i).uuid` |

Where the change lands and what it affects:

- **Files:** all of it is in `environment.py` (`PROBE_SCRIPT`, `identity_of`, `lock_from_probe`), D12's implementing module.
- **Hashes:** D12's payload hash changes, which is expected before approval. The seam source and its hash do not change.
- **Lock schema:** it moves to a new version.

The rule has three consequences:

- **The count is the visible count.** `attest-environment` and the live probe in `execute` must therefore run with the same `CUDA_VISIBLE_DEVICES` (unset, so both H100s are visible).
- **A restarted instance has the same hostname and GPUs,** so the lock still matches. The driver and UUIDs are recorded but not compared, so a change in them would not block a run.
- **A different instance of the same class would also pass the lock.** The data-loss rule, not the lock, keeps everything on one instance.

## 8. Can each decision be applied as written?

| decision | check | result |
|---|---|---|
| D05 (a) containment rule on every kept CLOSE case | 67 kept close cases are listed in `topic_screen_report.md`; the rule is the semantic review's own "restatement" definition, applied in both directions | applicable |
| D05 (b) restore an 11+-letter word in 1-2 Stage 1 replacements | `TOPIC_REVIEW.md` §4: Stage 1 went from 3 of 32 to 1 of 32 questions with an 11+-letter word; replacements keep id, category and opening word | applicable |
| D05 (c) work-and-organisations-36 cites the partner as it stood at review | confirmed: `TOPIC_REVIEW.md` §3b cites the partner `b1-work-and-organisations-43` by its current text ("…two signatures on large payments?"); at review time it read "Why do some organisations hold a short daily meeting standing up?" (`topics_semantic_review.json`, first pass) | applicable (report-generator fix) |
| D05 (d), (e) fresh second pass; split unchanged | a test already checks that the split is unchanged | applicable |
| D11 P3 minimum 3; confirm against §8 | `COVERAGE_SIMULATION_REVIEW.md` §8 recommends exactly this (P3k3), keeps the 12-of-16 target and P1/P2/G1 minima unchanged, and reports about 1 point of extra false INFEASIBLE in typical scenarios | meets the target; applicable |
| D01 follow PROTOCOL_REVIEW | the recommendation is "approve", with an *optional* swap of `pro.word.the`; following it means no swap, so the content-word condition does not arise. **There is no model-compliance evidence for any reference:** nothing has been generated, and the review's evidence is verifier witnesses plus "do not use *the* is extreme in English" | applicable; the evidence to report is that there is none |
| D07 keep limits > 85% inadmissible | `b_informative_band = (0.15, 0.85)` (`config.py:142`) | already so |
| D12 wording "the CUDA vLLM 0.15.1 wheel is cp38-abi3" | PyPI lists only `vllm-0.15.1-cp38-abi3-manylinux_2_31_{x86_64,aarch64}.whl`; it requires `torch==2.9.1` and Python `>=3.10,<3.14` | true; applicable. `config.py:100-104` currently justifies 3.12 by the ROCm wheel being cp312 |
| batch invariance off | nothing in the seam sets `VLLM_BATCH_INVARIANT` | already so |
| TP as configured | TP = 1 for all four models | already so; this is why two GPUs need §6 |
