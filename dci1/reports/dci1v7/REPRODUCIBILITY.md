# DCI-1 v7 — reproducibility audit

Everything a third party needs to re-run the directional matched-reference
study as closely as the repository permits, read out of the code, configs,
signed records and analysis scripts at repository HEAD `906a88d`.

**Companion documents.** `METHODS.md` (design and estimand reconstruction),
`VALIDITY_AUDIT.md` (what the numbers will bear), `dossier/README.md` (the
data layer), `paper_figures/README.md` (figures and Table 1). This file does
not restate their scientific argument; it records what must be *fixed* to
reproduce them.

Every factual row cites the file, and where practical the line, function or
config key it was read from. Paths are repository-relative. Claims are
labelled:

| Label | Meaning |
|---|---|
| **[P]** | Preregistered — bound by the signed manifest before any outcome was seen |
| **[D]** | Development-time — a code default, an operational setting, or a value realised only in the non-confirmatory rehearsal lanes |
| **[H]** | Post-hoc — computed after outcomes; licenses no claim |
| **[!]** | Discrepancy, defect, or unrecoverable information |

---

## 0. What is being reproduced — read before anything else

**The registered v7 study produced zero confirmatory rows.** All four
replications terminated `PREFREEZE_AUDIT_FAILURE` on `support_satisfied`
on 2026-08-28; no model has a `GATE_5_FREEZE`, `CONFIRMATORY_GENERATION`,
`MASKED_ANALYSIS`, `UNMASKED_ANALYSIS` or `FINAL_REPORT` record
(`reports/dci1v7/CLOSURE.md`; `evidence/dci1v7/<model>/terminal_report.json`).

**Every complete estimate in this repository — including every number in
Figures 2–4 and Table 1 — comes from six development-rehearsal lanes** in the
structurally separate `dci1v7-development` namespace, which the protocol's own
guards refuse to admit as study evidence
(`dci1/src/dci1v7/engine/guards.py:56-116`). Each lane carries
`evidence_status = DEVELOPMENT_REHEARSAL_not_a_v7_replication`
(`reports/dci1v7/dossier/lanes.csv`).

A rehearsal lane is the registered nineteen-stage sequence, on the registered
model, through the pinned backend, with every registered rule, threshold, cap,
seed, verifier and provenance check unweakened, run under a caller-supplied
root outside the registered tree. Reproducing it reproduces the apparatus and
the reported numbers; it does not produce a confirmatory result.

| | |
|---|---|
| Repository HEAD for this audit | `906a88dfb776a384e2aecdea3c78f2b195475f29` |
| HEAD for `METHODS.md` / dossier extraction | `87a6c185a9bd7e0496548e5c3e0c44c63752bca3` |
| Registered manifest hash | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` |
| Registration commit (registered study) | `ed0446ff58d0efc70b7703c162997863a9530768` |
| Protocol version | 7.0, adopted 2026-08-28; amended in place A6–A8, 2026-08-28 |
| Registered protocol hash, after A6–A8 | `2e91a1c0aa83a11573678df22c37ec3ef316c6606af2fa885ba10028ba9b5d2d` |
| Confirmatory rows, registered study | **0** |
| Complete end-to-end lanes | **6**, development namespace (4 canonical + 2 repeat) |

---

## 1. Models and inference

### 1.1 Exact models and pinned revisions

**[P]** All four defined once, in `dci1/src/dci1v4/models/registry.py:50-99`
(`MODELS`, a frozen `tuple[ModelSpec, ...]`). Revisions are re-pinned in the
signed registration manifest before qualification and asserted at every
generation; they are not inherited from earlier studies
(`registry.py:12-19`).

| `model_key` | Hugging Face `model_id` | Pinned `revision` | Exec. order | Family |
|---|---|---|---:|---|
| `gemma-3n-e2b-it` | `google/gemma-3n-E2B-it` | `5e092ebca197cdcd8d8b195040accf22693501bc` | 1 | `gemma3n` |
| `gemma-3n-e4b-it` | `google/gemma-3n-E4B-it` | `c1221e9c62e34a43ab7ffacd1be0ea71f126ef10` | 2 | `gemma3n` |
| `qwen3-4b` | `Qwen/Qwen3-4B` | `1cfa9a7208912126459214e8b04321603b3df60c` | 3 | `qwen3` |
| `qwen3-4b-instruct-2507` | `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` | 4 | `qwen3` |

A judge registry (`gpt-oss-20b`, revision `6cee5e81ee83917806bbde320786a8fb61efebee`)
exists at `registry.py:104-118` and is disjoint from the replications. **It is
not used anywhere in v7's measurement path** — see §7.6.

### 1.2 Loading, dtype, parallelism, context length

**[P]** `ModelSpec` field defaults, `registry.py:41-44`; overridden per model
only where the table below says so.

| Setting | Value | Source |
|---|---|---|
| dtype | `bfloat16` | `registry.py:43` (`dtype`) |
| quantization | `"none"` | `dci1/src/dci1v4/generation/backend.py:188` |
| `tensor_parallel_size` | **1** for every model | `registry.py:42`; `backend.py:189` |
| `max_model_len` | 4096 | `registry.py:44` |
| `gpu_memory_utilization` | 0.85 for three models; **0.95 for `gemma-3n-e4b-it`** ("measured envelope on the 24 GiB card") | `registry.py:41`, `registry.py:74` |
| `enforce_eager` | `True` | `backend.py:192` |
| `disable_custom_all_reduce` | `True` | `backend.py:191` |
| `cpu_offload_gb` | 0.0 | `backend.py:193` |
| `trust_remote_code` | `False` | `backend.py:196` |
| `limit_mm_per_prompt` | `None` | `backend.py:197` |
| tokenizer | the engine's own tokenizer for the pinned snapshot; chat template applied with `add_generation_prompt=True` | `exploratory/vllm_backend/engine.py:222-227` |
| snapshot resolution | `HF_HUB_OFFLINE=1` — the engine reads exactly the pinned local snapshot and is immune to network state | `backend.py:53-62` (`backend_env`) |

Two independent TP=1 lanes are the only supported multi-GPU mode. Card
placement is by `--device N`, which clears inherited `ROCR_`/`HIP_`/`CUDA_`
visibility variables and sets `HIP_VISIBLE_DEVICES` itself, so a shell export
cannot move a lane (`backend.py:53-57`; `dci1/src/dci1v7/run/cli.py:31-40`).
`--device` is *refused* on a stage that generates nothing rather than ignored.

### 1.3 Inference engine and version

**[P]/[D]** vLLM **0.15.1+rocm720**, from a vendored wheel, run in a separate
interpreter (§2). Recorded in every freeze record as
`freeze.decoding_settings.backend = "vLLM 0.15.1+rocm720"`
(verified in `evidence/dci1v7-development-r5/.../GATE_5_FREEZE/gate5_freeze.json`).

The scientific process never imports vLLM: it writes `plan.json` +
`design.jsonl`, launches
`<backend venv>/bin/python -u -m vllm_backend --plan … --design … --out …`
as a detached process group and reads `rows.jsonl` back
(`dci1/src/dci1v4/generation/backend.py:226-291`). Backend entry point
`exploratory/vllm_backend/__main__.py`; backend cwd is `exploratory/`
(`backend.py:38-40`).

### 1.4 Decoding parameters

**[P]** One registered policy for every stage and every model
(`backend.py:169-221`, `build_plan`). Nothing is left to a backend default:
"a default that changed on the far side of the seam would be an unlogged
change of experimental condition" (`backend.py:178-181`).

| Parameter | Value | Source |
|---|---|---|
| `temperature` | 0.7 | `backend.py:170` |
| `top_p` | 0.9 | `backend.py:170` |
| `top_k` | 50 (passed as 0 only if `temperature == 0`) | `backend.py:171`, `backend.py:200-202` |
| presence / frequency / repetition penalties | **not passed** | `exploratory/vllm_backend/engine.py:65-81` |
| stop sequences | **none** | `exploratory/vllm_backend/plan.py:117`; `engine.py:9-12` |
| `decoding_policy` | `"stochastic"` | `backend.py:213` |
| `skip_special_tokens` | `True` | `backend.py:214` |
| `strategy` | `"single_phase"` | `backend.py:207` |
| draws | **M separate requests**, not `n>1` sampling — one design row per `(cell, draw)`, each with its own seed | `dci1/src/dci1v7/run/execute.py:216-245` (`design_rows`); `engine.py:289-296` |
| `engine_seed` | 20260819 — engine state only, never a scientific seed | `backend.py:162-166`, `backend.py:195` |
| per-request seed | see §3 | `dci1/src/dci1v7/protocol/seeds.py:58-65` |

A greedy sensitivity regime is *declared* (`GREEDY_BLOCKS = 96`,
`GREEDY_DRAWS = 1`, `GREEDY_TEMPERATURE = 0.0`,
`dci1/src/dci1v7/protocol/constants.py:145-147`) and **was not run** in any
lane.

### 1.5 Max tokens and stopping rules

**[P]** The completion cap is selected per model from
`COMPLETION_CAPS = (512, 768, 1024)` (`constants.py:165`) as the smallest cap
whose truncation share is ≤ `CAP_TRUNCATION_MAX = 0.10` (`constants.py:166`),
measured on `CAP_SELECTION_PROMPTS = 96` prompts across
`CAP_SET_LOADS = (0, 1, 2)` (`constants.py:167-169`); selection code in
`dci1/src/dci1v7/run/regime_run.py:140-150`.

**[D]** All four models selected **cap = 512** (`reports/dci1v7/dossier/lanes.csv`
and each lane's `GATE_5_FREEZE.freeze.completion_cap`). The cap is passed as
both `generation_ceiling` and `answer_tokens` (`backend.py:203-204`). There
are no stop strings, so a generation ends at EOS or at the cap.

### 1.6 System / user message structure

**[P]** **No system prompt is ever sent.** A system turn is appended only if
`system_message` is non-empty; it defaults to `""` and no v7 module sets it
(`exploratory/vllm_backend/engine.py:222-225`;
`exploratory/vllm_backend/contract.py:66`). Every request is a **single user
turn**, zero-shot, containing exactly the rendered prompt of §4.4.

### 1.7 Thinking / reasoning settings

**[P]** `reasoning_mode = "NO_THINKING"` for every registered model
(`backend.py:208`), `reasoning_parser = None`, `think_open`/`think_close`
empty (`backend.py:209-211`).

- `gemma-3n-e2b-it`, `gemma-3n-e4b-it`, `qwen3-4b-instruct-2507`:
  `thinking_policy = "unavailable"`, `chat_template_kwargs = {}`,
  `switch_expectation = "inert"` (`registry.py:57-99`).
- `qwen3-4b` is a hybrid checkpoint: `thinking_policy = "disabled"` via its own
  supported mechanism, `chat_template_kwargs = {"enable_thinking": False}`,
  `switch_expectation = "live"` (`registry.py:78-84`). The backend renders the
  template declared-versus-negated and **refuses to run if the kwarg is inert**
  (`engine.py:230-280`).
- Leakage markers per model (`<think>`, `</think>`, and for Gemma
  `<start_of_turn>`/`<end_of_turn>`) are declared at `registry.py:60-62, 71-73,
  85, 97`.

### 1.8 Retry, error and truncation behaviour

**[P]** **There are no scientific retries and no exclusions.**

| Situation | Behaviour | Source |
|---|---|---|
| Truncated at the cap | scored normally; forces `non_vacuous = False`; `truncated` recorded on the row | `dci1/src/dci1v7/verifiers/compliance.py:177-193` (esp. `:186`), `:245` |
| Empty answer | scored normally; word budgets **pass vacuously** (max word length 0 ≤ m); exact counts and rate forms fail; `empty` recorded, never a filter | `compliance.py:129-135`, `:244` |
| `finish_reason` | recorded on the row; **no predicate reads it** | `dci1/src/dci1v7/run/execute.py:539, :555` |
| Refusals | no detector, no special scoring — scored as any other text | `constants.py:830-832` |
| Verifier exception | fails closed: `passed=False, graded=0.0, processing_failure=True` | `compliance.py:196-203` (`_score_one`) |
| Backend crash (`returncode == 3`) | `IntegrityError`, **no rows trusted** | `backend.py:277-279` |
| Backend produced no rows / blocked | `IntegrityError` | `backend.py:280-287` |
| Stage timeout | default 12 h for confirmatory generation (`timeout_seconds=60*60*12`), 24 h default in `run_backend`; the whole process group is killed and the exception re-raised | `execute.py:477-478`; `backend.py:229, :258-276` |
| Resume after an interrupted stage | rows are reused **only** on exact generation-identity match (study, protocol identity, stage, decoding policy, model revision, topic, split, block, cell, constituents, wording, prompt, seed); any mismatch regenerates and the reason is recorded, never silent | `execute.py:255-300` (`_reusable_rows`) |
| Completeness | every `(block, cell, draw)` identity exactly once; missing, duplicate and unexpected rows are all refusals | `dci1/src/dci1v7/run/confirmatory_run.py:166-190` |

**Operational retries exist at the driver level only** and change nothing
measured: `dci1/tools/run_v7_replication.sh` re-runs a stage after a GPU-lock
refusal (60 s) or an unexplained failure (120 s, at most twice) and stops for
a person after that. Every attempt writes its own log; a stage that succeeded
is never re-run because the CLI refuses out-of-order, repeated and
post-terminal attempts itself.

---

## 2. Compute and software environment

### 2.1 Two interpreters, by design

| | Scientific environment | Backend environment |
|---|---|---|
| Location | `dci1/.venv` | `dci1/environments/backend/.venv` |
| Spec | `dci1/pyproject.toml` | `dci1/environments/backend/pyproject.toml` |
| Lock | `dci1/uv.lock`, `dci1/requirements-frozen.txt` (`uv export --frozen`) | `dci1/environments/backend/uv.lock` |
| Python | `>=3.13` (measured: 3.13.x) | `==3.12.*` |
| Runtime deps | `numpy==2.5.2` **only**; no GPU stack | vLLM/torch/ROCm stack, below |
| Dev deps | `pytest==9.1.1`, `pyarrow==25.0.1`, `pytest-xdist>=3.8.0` | — |
| Build | `cd dci1 && uv sync` | `cd dci1/environments/backend && uv sync` |

The backend spec is deliberately duplicated from another project because
"the newest vLLM/PyTorch stacks do not run reliably on this workstation, so the
study pins the stack that does" (`environments/backend/pyproject.toml:1-12`).

### 2.2 Backend package versions

From `dci1/environments/backend/pyproject.toml:18-33` and
`[tool.uv] override-dependencies` at `:36-47`:

| Package | Pin |
|---|---|
| vllm | `0.15.1` — vendored wheel `vendor/vllm-0.15.1+rocm720-cp312-cp312-linux_x86_64.whl` |
| torch | `2.9.1` → `torch-2.9.1+rocm7.2.0.lw.git7e1940d4-cp312-cp312-linux_x86_64.whl` (repo.radeon.com, rocm-rel-7.2) |
| torchvision | `0.24.1` → `torchvision-0.24.0+rocm7.2.0.gitb919bd0c-…` |
| torchaudio | → `torchaudio-2.9.0+rocm7.2.0.gite3c6ee2b-…` |
| triton | `3.5.1` → `triton-3.5.1+rocm7.2.0.gita272dfa8-…`; `triton_kernels-1.0.0-py3-none-any.whl` |
| transformers | `>=4.49.0,<5` |
| numpy | `>=2.0.0,<=2.1.3` |
| huggingface-hub | `>=0.29.2` |
| accelerate | `>=1.4.0` |
| amdsmi | `>=26.0.0` — vendored wheel `vendor/amdsmi-26.2.1+fc0010cf6a-py3-none-any.whl`; a hard dependency because vLLM's ROCm platform autodetection falls back silently without it (`pyproject.toml:20-27`) |
| amd-aiter, flash-attn | from index `https://wheels.vllm.ai/rocm/` |

Vendored wheel SHA-256, `dci1/environments/backend/vendor/MANIFEST.sha256`:

```
ddd51af0f3a3f7804d023e79f8078652bd0297d8f6bfffbec564d27a8200186c  amdsmi-26.2.1+fc0010cf6a-py3-none-any.whl
c1cbdee67f40556982d6e98a242beea2db89a6d73b3b1b93f0d037a7b2ffafc9  vllm-0.15.1+rocm720-cp312-cp312-linux_x86_64.whl
```

`METHODS.md` §14.3 additionally names transformers 4.57.6, numpy 2.1.3,
huggingface-hub 0.36.2 and torchvision 0.24.0+rocm7.2.0 as the resolved
versions in the built environment; the authoritative record is
`dci1/environments/backend/uv.lock`.

Backend-mandated environment variables, set by `backend_env`
(`dci1/src/dci1v4/generation/backend.py:53-62`):
`HIP_VISIBLE_DEVICES=<device>`, `VLLM_WORKER_MULTIPROC_METHOD=spawn`,
`NCCL_P2P_DISABLE=1`, `HF_HUB_OFFLINE=1`; `ROCR_`/`HIP_`/`CUDA_` visibility
variables inherited from the shell are stripped first.

### 2.3 Figure environment

**[!] Not covered by either lock file.** `dci1/tools/v7_paper_figures.py:38-42`
imports `matplotlib`, which is absent from `dci1/pyproject.toml`. On this
machine it resolves through the repository-root venv
(`/…/dci/.venv`, matplotlib **3.11.1**, Python 3.13.12), whose spec is the
root `pyproject.toml` (`matplotlib>=3.8`, `numpy`, `pandas`, `scipy`, `tqdm`,
`psutil`, `z3-solver`). A releasable artifact needs an explicit figure
environment (see the checklist).

`dci1/tools/v7_dossier.py` and `dci1/tools/v7_paper_figures_check.py` are
stdlib-only and run in either interpreter.

### 2.4 Hardware

**[D]** 2 × AMD Radeon RX 7900 XTX (gfx1100, 24 GB), used as two independent
TP=1 lanes with a per-card `flock` (`backend.py:130-160`, `GpuLock`) plus a
driver-level lock at `evidence/.gpu-locks/gpu<N>.driver.lock`
(`tools/run_v7_replication.sh:47-49`). Recorded in the freeze record only as
`freeze.hardware = {"tensor_parallel_size": 1, "gpu_memory_utilization": 0.85}`.

The backend measures a richer `HostProfile` — `device_count`, `gcn_archs`,
`device_names`, `total_vram_gib`, `torch_version`, `torch_hip`,
`vllm_version`, `platform_class`, `supports_fp8`, `is_navi`, and the
`NCCL_*`/`RCCL_*`/`HIP_*`/`HSA_*`/`VLLM_*`/`ROCR_*`/`PYTORCH_*`/`TORCH_*`/
`FLASH_ATTENTION_*` environment variables
(`exploratory/vllm_backend/hardware.py:13-52`) — and returns it in the run
provenance beside `rows.jsonl` (`backend.py:284-288`).

### 2.5 Runtime

**[D]** Measured on the rehearsal lanes
(`reports/dci1v7/development_rehearsal/REHEARSAL.md`):
4 h 08 m to 14 h per model, end to end on one card.
`gemma-3n-e4b-it` is the slowest: Gate 2 6 h 48 m, confirmatory generation
5 h 48 m for 89,088 rows. Validation-suite timings are in
`memory`-independent form in `tools/v7_validate.sh:9-16` (a synthetic walk
≈ 8 min and ≈ 5.5 GB RSS per process; phase B's six heavy processes ≈ 34 GB on
24 CPUs).

### 2.6 [!] Environment facts that are **not recoverable**

Stated rather than guessed:

1. **Host CPU model, RAM, OS distribution and kernel are not recorded in any
   committed v7 artifact.** `dci1/src/dci1v4/engine/environment.py:53-70`
   defines `environment_record()`, which captures `platform.uname()` OS and
   kernel, the interpreter identity, the command line and registered
   environment variables — **v7 never calls it** (grep over
   `dci1/src/dci1v7/`: zero references). The only environment field on a v7
   record is `environment_digest`.
2. **`environment_digest` is free text supplied on the command line**, not a
   computed digest: `tools/run_v7_replication.sh:45-46` passes
   `rocm7.2/vllm0.15.1` (CPU stages) or `rocm7.2/vllm0.15.1/gpu<N>` (GPU
   stages), and the freeze record stores exactly that string
   (verified: `GATE_5_FREEZE.environment_digest == "rocm7.2/vllm0.15.1"`).
   `freeze_run.py:367-368` falls back to `sha_obj(interpreter_identity())`
   only when the flag is empty, and `interpreter_identity()` is just
   `{python_executable, python_version}` (`environment.py:45-50`).
3. **`dependency_digest` hashes the *path string* of the lock file, not its
   contents**: `sha_obj({"uv_lock": str(repo_root / "dci1" / "uv.lock")})`
   (`dci1/src/dci1v7/run/freeze_run.py:365-366`). The recorded value
   `822063f7…0223` therefore identifies a filesystem location, not a
   dependency set. **[!] Disclose or fix before release.**
4. **The backend's measured `HostProfile` is not carried into the signed
   stage record** — it lives in the per-stage run directory beside
   `rows.jsonl`, which is under the gitignored evidence tree.
5. **The backend lives outside the governed tree** (`exploratory/vllm_backend/`),
   so its behaviour is pinned by lock file and vendored wheel hash rather than
   by the signed manifest.

---

## 3. Randomness and execution

### 3.1 Seed scheme, complete

**[P]** `dci1/src/dci1v7/protocol/seeds.py`. Root seeds were drawn fresh for
v4r3 on 2026-08-21 and carried; what separates one revision's draws from
another's is the **domain string**, and every v7 domain names `dci1v7`
(`seeds.py:1-13`).

| Root | Value | Domain | Line |
|---|---:|---|---|
| `GENERATION_ROOT_SEED` | 202608240 | `dci1v7:gen:v1` | `seeds.py:29, 38` |
| `BOOTSTRAP_ROOT_SEED` | 202608241 | `dci1v7:boot:v1` | `seeds.py:30, 39` |
| `GATE1_SAMPLE_SEED` | 202608242 | `dci1v7:gate1:v1` | `seeds.py:31, 40` |
| `AUTORATER_SPLIT_SEED` | 202608243 | `dci1v7:autorater-split:v1` | `seeds.py:32, 41` |
| `ADVERSARIAL_SEED` | 202608244 | `dci1v7:adversarial:v1` | `seeds.py:33, 44` |
| `MASK_ROOT_SEED` | 202608245 | `dci1v7:mask:v1` | `seeds.py:34, 45` |
| `CARRIED_TOPIC_SPLIT_SEED` | **202608192** (deliberately v4r2's, not re-drawn) | — | `seeds.py:52-54` |

Derivation primitive (`dci1/src/dci1v4/protocol/hashing.py:44-52`):

```
domain_digest(domain, *parts) = SHA256( "\x1f".join([domain, *map(str, parts)]) )
domain_int(domain, *parts, bits=63) = int.from_bytes(digest[:8], "big") % 2**63
```

**Generation seed** (`seeds.py:64-72`):

```
generation_seed(stage, model_id, prompt_hash, draw_index)
  = domain_int("dci1v7:gen:v1", 202608240, stage, model_id, prompt_hash, draw_index)
```

`prompt_hash = sha_text(prompt)` (`dci1/src/dci1v7/design/prompts.py:41-42`).

**Bootstrap seed** (`seeds.py:75-78`):
`bootstrap_seed(estimand, model_id) = domain_int("dci1v7:boot:v1", 202608241, estimand, model_id)`.
Called with `("unmasked", model_key)` for the unmasked analysis
(`dci1/src/dci1v7/run/analysis_run.py:1121-1122`) and per-family in the masked
phase (`analysis_run.py:975-977`).

Also: `gate1_sample_seed(instrument, stratum)` (`seeds.py:81-83`) and
`adversarial_seed(instrument)` (`seeds.py:86-88`). Every derivation names its
inputs and raises on a missing one — "there are no hidden seed defaults"
(`seeds.py:57-62`, `_require`).

### 3.2 What the generation seed does and does not depend on

**Depends on:** the study revision (domain string), the stage label, the
model id, the *prompt text* (via its SHA-256), and the draw index.

**Does not depend on:** the model *revision* (revision enters through
`model_id` only in the sense that a different id is a different model — a
re-pinned revision of the same repository yields the same seed), the block or
condition *directly*, batch position, scheduler order, or wall-clock time.

Block, cell, condition, order, wording and topic reach the seed **only through
the prompt text**: two cells that render the same prompt would share a seed at
the same draw index, and two cells that differ anywhere in the prompt do not.
This is deliberate — the per-request seed is "a pure function of scientific
identity and never of batch position, so a seed derived from position would
make results depend on scheduler order"
(`exploratory/vllm_backend/contract.py:58-62`).

**Consequence for pairing:** draws are **not** paired across cells. Draw *k*
of `solo:B` and draw *k* of `pair:B+A` share no random state, because the
prompts differ (`METHODS.md` §6.3). Pairing is at the block level only — which
is exactly the level the bootstrap resamples (§8.3).

The engine-level seed is a separate constant, `ENGINE_SEED = 20260819`
(`backend.py:162-166`), which fixes engine state only.

### 3.3 Batching and concurrency

| Property | Value | Source |
|---|---|---|
| Requests per generate call | `chunk_size = 64` for every scientific stage | `dci1/src/dci1v7/run/execute.py:463` |
| Serialised mode | `max_concurrency = 1`, `chunk_size = 1` — **autorater paths only**, not used in v7's measurement path | `backend.py:219-221` |
| Draws | M separate requests per prompt | `execute.py:216-245` |
| GPU exclusivity | non-blocking per-device `flock`; a second run is refused, not queued | `backend.py:130-160` |
| Two lanes | two TP=1 processes, one per card, arbitrated by the device lock plus a blocking driver lock | `tools/run_v7_replication.sh:14-25, 47-49` |
| CPU scoring pools | `DCI1_V7_CPU_WORKERS` sizes spawned worker pools for row scoring and calibration-table construction; **`=1` is the serial reference path** and the pools are tested byte-identical against it | `dci1/src/dci1v7/engine/parallel.py`; `execute.py:494-500`; `tests_v7/test_parallel.py` |

### 3.4 Can changing batching or order change outputs?

**Yes, for generation; no, for anything downstream.**

- **Generation.** The seed does not depend on batch position, so the *intended*
  sample for each request is fixed. But the repository makes **no claim** that
  vLLM's continuous batching is bitwise-invariant to chunk composition:
  batching affects kernel-level reduction order and thus can change logits at
  the last bit. No docstring in the repository claims bitwise reproducibility
  of generation.
- **Scoring, calibration, analysis.** Deterministic and order-invariant by
  construction. Row scoring is a pure function of the row, its cell, the
  instance set and the frozen verifier hash; the process pool returns units in
  index order and is proven byte-identical to the serial path
  (`execute.py:494-500`; `REHEARSAL.md`, defect 4). Gate 1 requires verifier
  determinism across three OS processes to be **exactly 1.000**
  (`dci1/src/dci1v7/stages/gate1.py:376-518`).
- **Bootstrap.** Pure Python `random.Random(seed)` with no numpy anywhere in
  `dci1/src/dci1v7/` (verified by grep): the resample sequence is a
  deterministic function of the seed alone
  (`dci1/src/dci1v7/analysis/bootstrap.py:119-131`).

### 3.5 Level of reproducibility claimed

State this honestly in the paper:

1. **Bitwise reproduction of generations is not claimed and is not expected.**
   Sampling at `temperature=0.7` on a ROCm vLLM engine, with continuous
   batching, is reproducible only up to floating-point non-determinism in the
   kernels; the repository pins the engine, wheel hashes, dtype, engine seed,
   TP degree and per-request seed, which is what makes a *re-run* comparable,
   not identical.
2. **Everything downstream of the raw text is exactly reproducible.** Given the
   stored `raw_response` strings, the verifier verdicts, cell means, estimands,
   bootstrap replicates and intervals reproduce bitwise: the verifier is
   deterministic and hash-bound, the analysis layer is stdlib-only, and the
   bootstrap is seeded from experimental identity.
3. **The design is reproducible without any model.** Topic splits, cell sets,
   wording allocation, prompts, seeds and thresholds are all pure functions of
   committed code and the split seed.

---

## 4. Data and prompts

### 4.1 Task bank

**[P]** 720 questions = 12 subject areas × 60 (`constants.py:38-56`,
`SUBJECT_AREAS`, `TOPICS_PER_AREA`; `assert sum(SET_SIZES.values()) == N_TOPICS == 720`
at `constants.py:74`).

Subject areas (`constants.py:38-42`): everyday science, history, geography,
food, music, sport, work and organisations, health and the body, technology,
language and writing, art and design, the natural world.

Authoring rules, enforced as a declared tuple (`constants.py:81-86`,
`AUTHORING_RULES`):
`answerable_from_general_knowledge`, `no_single_correct_short_answer`,
`no_reused_public_dataset_or_examination_text`,
`no_form_requirement_in_the_question_text`.

Provenance: 624 carried from v4's released split
(`dci1/src/dci1v4/topics/data/topics_v4.json`); 96 newly authored for
Calibration-B on 2026-08-22, before any v5 measurement
(`dci1/src/dci1v7/topics/data/calibration_b_v6.json`;
`dci1/src/dci1v7/topics/calibration_b.py:41-74`). Disjointness is checked over
both ids and normalised question text
(`dci1/src/dci1v7/topics/bank.py:171-230`).

### 4.2 Splits and split seed

**[P]** A seeded per-area shuffle-and-cut with the **deliberately reused** seed
`202608192` (`dci1/src/dci1v4/topics/split.py:58-74`; `seeds.py:52-54` — "a
fresh seed would cut the bank differently and make the two studies'
development sets non-comparable for no gain").

| Split | Per area | Total | Used for | Constant |
|---|---:|---:|---|---|
| Pre-screen | 2 | 24 | cap selection, ladder screen (1 draw), §12.6 certificate | `N_PRESCREEN` |
| Calibration-A | 8 | 96 | difficulty table, split-A admissibility | `N_CALIBRATION_A` |
| Calibration-B | 8 | 96 | split-B admissibility, `V_stab` equivalence | `N_CALIBRATION_B` |
| Composed validation | 2 | 24 | Gate 4 composed contrast | `N_COMPOSED` |
| **Confirmatory** | 32 | **384** | the 384 blocks of the primary analysis | `N_CONFIRMATORY` |
| Sequestered | 8 | 96 | **never used** | `N_SEQUESTERED` |

`constants.py:44-73`. Development work may inspect only
`DEVELOPMENT_TOPIC_SETS = ("prescreen", "calibration_a", "calibration_b")`;
`RESERVED_TOPIC_SETS = ("composed", "confirmatory", "sequestered")`
(`constants.py:77-79`).

Split content hashes are bound into every freeze record
(`GATE_5_FREEZE.freeze.topic_splits`), e.g. for the r5 gemma-e2b lane:

```
prescreen      54df3616e191e372c32b30f0263722b5435235c7a851ccf3f5acfba1f7acd536
calibration_a  57850f1ce0217afed96f40494c44031a3fe4d192794f0596323d9d8c5206a59e
calibration_b  bc7a7350624c38b828adf5181cad426e05c9c9c51fac14bf8c9aa40088217c73
composed       e2f4badfce247acdcb716b2ed40a3d31267ba0408cd4d74e2bf775a8496b9763
confirmatory   5b54bfeff2ec9691cca076e213bce99a8146202d09096aca8ea39d237cb9313d
sequestered    null   (never materialised)
```

### 4.3 Where the prompt and task files live

| Artefact | Path |
|---|---|
| Topic bank (624 carried) | `dci1/src/dci1v4/topics/data/topics_v4.json` |
| Calibration-B (96 authored) | `dci1/src/dci1v7/topics/data/calibration_b_v6.json` |
| Sequestered set | `dci1/src/dci1v4/topics/data/sequestered_v4.json` |
| Bank assembly / disjointness | `dci1/src/dci1v7/topics/bank.py` |
| Split algorithm and seed | `dci1/src/dci1v4/topics/split.py:58-74` |
| Prompt templates | `dci1/src/dci1v7/protocol/constants.py:158-163`; renderer `dci1/src/dci1v7/design/prompts.py:28-38` |
| All wordings | `dci1/src/dci1v7/protocol/wordings.py` |
| Instrument library (families, ladders, forms) | `dci1/src/dci1v7/verifiers/constraints.py` |
| Cell construction and wording allocation | `dci1/src/dci1v7/design/cells.py` |

Rendered prompts are **not** committed for v7 (they live in the gitignored
evidence tree beside each stage's `design.jsonl`), but are exactly
reconstructible from the bank, the split seed and `design/prompts.py`.

### 4.4 Base prompt template

**[P]** `constants.py:158-163`. Four parts, no system message, single user
turn, zero-shot:

```python
STEM_SENTENCE = "Answer in 60 to 120 words."
PROMPT_ZERO = "{question}\n\n" + STEM_SENTENCE + "\n\nAnswer:"
PROMPT_ONE  = "{question}\n\n" + STEM_SENTENCE + "\n\n1. {c1}\n\nAnswer:"
PROMPT_TWO  = "{question}\n\n" + STEM_SENTENCE + "\n\n1. {c1}\n2. {c2}\n\nAnswer:"
```

Load > 2 is refused (`prompts.py:37-38`). The stem sentence must appear
**exactly once** in every prompt, asserted on the mandatory path
(`prompts.py:50-59`, `assert_stem_present`). Two composed prompts sharing a
constituent are asserted to differ only in the other constituent's line
(`prompts.py:63-79`, `assert_shared_constituent_identity`). Nothing in the
prompt marks which instruction is "the outcome" — that is an analysis-side
label.

### 4.5 A, B and reference templates — all wording variants

**[P]** Four wordings per instrument, verified by execution of
`dci1/src/dci1v7/protocol/wordings.py`.

**A — exact marker count on *however*, severity n ∈ {1,…,8}**
(`constraints.TARGET_GRID = (1,…,8)`, `TARGET_WORD = "however"`). Carried
byte-identically from v4r2 (`wordings.py:56-59`). At n = 6:

```
1. Use the word however exactly 6 times.
2. Your answer must contain however exactly 6 times.
3. Include however exactly 6 times in your answer.
4. The word however must appear exactly 6 times.
```

**B — maximum word-length budget, severity m ∈ {7,…,14}** with conditional
extension `{15, 16}` (`constraints.FOCAL_GRID`, `FOCAL_EXTENSION`). Templates
are re-derived from two v4 renderings and refused if they differ by more than
the numeral (`wordings.py:61-90`). At m = 10:

```
1. Every word in the answer must have at most 10 letters.
2. Use only words of 10 letters or fewer.
3. Do not use any word longer than 10 letters.
4. No word in your answer may exceed 10 letters.
```

The floor m ≥ 7 exists because *however* has seven letters: below it A and B
are jointly unsatisfiable (`constraints.py:82-84`).

**Tier-1 references (MK1–MK8)** carry **A's own four templates with the marker
word substituted**, generated at import rather than retyped
(`wordings.py:227-253`, `_marker_templates`), so the same-form claim is a
property of the instrument. Markers
(`constraints.MARKER_WORDS`): MK1 *thus*, MK2 *hence*, MK3 *though*,
MK4 *whereas*, MK5 *indeed*, MK6 *namely*, MK7 *instead*, MK8 *overall*.
Ladders 1–8, frozen reserves 1–12 (`constraints.LADDERS`, `RESERVES`).
At q = 3, MK1 reads:

```
1. Use the word thus exactly 3 times.
2. Your answer must contain thus exactly 3 times.
3. Include thus exactly 3 times in your answer.
4. The word thus must appear exactly 3 times.
```

Marker eligibility: *however* excluded by name; at most
`MARKER_MAX_LETTERS = 7`; natural occurrence probability ≤
`MARKER_NATURAL_FREQUENCY_MAX = 0.15`. Rejections are recorded with reasons in
`constraints.REJECTED_MARKERS` (e.g. *moreover*, *likewise* — 8 letters;
*therefore*, *meanwhile*, *otherwise* — 9; *conversely* — 10).

**Tier-2 (near-form)** — XC1 semicolon, XC2 comma, XC3 sentence. XC1 at q = 3:

```
1. Your answer must use exactly 3 semicolons.
2. Use exactly 3 semicolon characters in your answer.
3. Exactly 3 semicolons must appear in your answer.
4. Include exactly 3 semicolon characters in your answer.
```

**Tier-3 (broad class)** — 28 families. The class control actually selected in
every class-arm lane is **RF12**, rule "The answer may contain at most q
sentences", ladder 1–8. At q = 6:

```
1. Your answer may use at most 6 sentences.
2. Your answer must have at most 6 sentences.
3. No more than 6 sentences may appear.
4. Do not write more than 6 sentences.
```

**Library size**, from `constraints.py` module constants (verified by import):

| Constant | Value |
|---|---:|
| `N_FAMILIES` | 40 (Tier 1: 8, Tier 2: 4, Tier 3: 28) |
| `PROBE_ONLY_FAMILY_IDS` | `("PS1", "PS2", "PS3")` — non-selectable stand-ins |
| `N_INSTRUMENTS` | 674 |
| `N_SEVERITIES` (round-0 ladders) | 350 |
| `N_DECLARED_SEVERITIES` (with reserves) | 656 |
| `N_SELECTABLE_SEVERITIES` / `N_SELECTABLE_DECLARED` | 326 / 632 |
| `N_PROBE_ONLY_SEVERITIES` | 24 |
| `N_VERIFIERS` | 42 |

The wording set is content-hashed into every freeze record as
`freeze.wording_hash` (r5 lane: `476dbaa7e516ad6c4f8db866a9694a627eb0184784c7033c13e655f1a74800f0`).

### 4.6 Severity grids and per-model selected n\*, m\*

**[P]** grids: A `1–8`; B `7–14` with conditional extension to `{15, 16}`.

**[D]** Selected operating points. **The registered study and the development
rehearsals selected identical `(n*, m*)` for every model** — a reproducibility
fact worth reporting. Source: each lane's
`GATE_2_FOCAL_CALIBRATION/gate2_focal_calibration.json`, tabulated in
`reports/dci1v7/dossier/operating_points.csv`; registered-study values in
`reports/dci1v7/CLOSURE.md`.

| Model | cap | m\* | n\* | solo(A) | solo(B) | ι_A | bracketed? |
|---|---:|---:|---:|---:|---:|---:|---|
| `gemma-3n-e2b-it` (canonical lane r5) | 512 | 10 | 8 | 0.5938 | 0.8047 | 0.5891 | n\* **not** bracketed → `OPERATING_POINT_AT_GRID_BOUNDARY` |
| `gemma-3n-e4b-it` (r4) | 512 | 9 | 6 | 0.7318 | 0.7513 | 0.7252 | yes |
| `qwen3-4b` (r3) | 512 | 12 | 2 | 0.6875 | 0.7643 | 0.6855 | yes |
| `qwen3-4b-instruct-2507` (r4) | 512 | 11 | 5 | 0.5664 | 0.7786 | 0.5397 | yes |

The B (focal) extension to `{15, 16}` was **not** measured on any lane
(`focal_extension_measured = False` on all six rows).

---

## 5. Experimental design

### 5.1 Conditions generated

**[P]** The full five-arm design is **56 cells per block**; the rehearsal lanes
admitted **26** (base + core) or **29** (base + core + class). Cell types are
derived from the admitted arm set (`dci1/src/dci1v7/design/cells.py:138-142,
187-215`), never listed by hand.

| Cell | Prompt | Measured on | Required for |
|---|---|---|---|
| `unconstrained` | question + stem only (load 0) | every instruction, absent | chance κ; κ(c\|B) source |
| `solo:B` | B alone | B | D(B←·); ι_B |
| `solo:A` | A alone | A | D(A←·); **ι_A, the matching target** |
| `pair:B+A` | B first, A second | B and A | **Δ_R** (B first); D(A←B) (A second) |
| `pair:A+B` | A first, B second | A and B | **Δ_R** (B second); D(A←B) (A first) |
| `pair:B+R_j`, `pair:R_j+B` | both orders, j = 1,2,3 | B and R_j | **Δ_R** reference term |
| `solo:R_j` | R_j alone | R_j | D(R_j←·) for Ξ |
| `pair:A+R_j`, `pair:R_j+A` | both orders | A and R_j | D(R̄←A) for Ξ; Δ^A |
| `pair:R_j+R_k` | all 6 ordered pairs | both | D(R̄←R̄′) for Ξ |
| `pair:B+CL`, `pair:CL+B` | both orders | B and CL | Δ_broad (class arm only) |
| `pair:B+N_k`, `pair:N_k+B` | both orders | B and N_k | Δ_near (near-form arm — **never ran**) |

### 5.2 Prompt orders and outcome positions — two distinct things

**[P]** `"B+A"` is an **ordered presentation**, not an unordered pair:
`pair:B+A` and `pair:A+B` are distinct cells, both generated in every block,
and `CellType.slots` is documented as "(first, second) in PROMPT order"
(`cells.py:154-166`, esp. `:158`).

A **configuration** is the position of the **outcome** constraint, not the slot
order: `CONFIGURATIONS = ("outcome_first", "outcome_second")`
(`constants.py:140-145`). One generation therefore serves two configurations
at once, one per constituent (`cells.py:181-184`).

Mapping (`dci1/src/dci1v7/analysis/observations.py:9-19, 47-48, 132-142`):
D(B←A) in `outcome_first` reads `pair:B+A`; in `outcome_second` it reads
`pair:A+B`. D(A←B) in `outcome_first` reads `pair:A+B`. **Within one
configuration the two directions are read from different prompts** — state
this explicitly; it is the misreading the design warns about, and it is why
Figure 4 panel A groups by prompt order rather than by "outcome position"
(`paper_figures/README.md`, design decision 2).

### 5.3 Wording allocation — balanced, not randomised

**[P]** Wording is a block-level factor assigned deterministically
(`cells.py:271-287`; recorded in the freeze as
`freeze.wording_allocation = "w(c1) = i mod 4; w(c2) = (i + floor(i/4)) mod 4; solo uses i mod 4"`):

```
first  = block_index mod 4
second = (block_index + floor(block_index / 4)) mod 4
```

Solo cells use `first`; composed cells give `first` to the constituent earlier
in the registered slot order, applied **identically to both order variants**.
Because the order variant does not depend on the block index, wording and
order are **orthogonal by construction**, each (cell, slot, wording)
combination occurs 96 times, and structural zeros or skews are refused
(`cells.py:278-279, 361-389`).

`freeze.order_allocation` records: "order is a cell-level factor; every block
runs both order variants of every composed cell (§8.4)".

### 5.4 Blocks, draws, units

**[P]**

- **A block is one confirmatory topic** → `N_BLOCKS = N_CONFIRMATORY = 384`
  (`constants.py:147`; enforced at `confirmatory_run.py:72-75`).
- **M = 8 draws per cell** (`M_DRAWS`, `constants.py:148`). All M enter the
  cell mean; none is selected or discarded
  (`confirmatory_run.py:186-189, 247-249`). Calibration stages use
  `M_CAL = 4` (`constants.py:149`); the ladder screen uses
  `LADDER_SCREEN_DRAWS = 1` (`constants.py:150`).
- **Experimental unit** — the **cell mean over the M draws of one block**.
  `build_observations` requires exactly the M registered draw indices, refuses
  a partial cell and imputes nothing; no draw-level index is reachable from
  the observation table (`observations.py:82-108, 173-178`).
- **Resampling unit** — the **block**: "the assignment, pairing, clustering and
  generalisation unit … the only index" (`observations.py:3-7`). Every
  registered contrast is formed *inside* one block;
  `assert_within_block` checks each block carries exactly the cells the
  admitted arms require (`observations.py:297-337`).

### 5.5 What is held fixed within a matched comparison

**[P]** Across the matched cells the following are byte-identical: the base
question, the answer-length sentence, both wording indices, the prompt order,
m\*, n\*, the completion cap, decoding settings, model revision, and M.
**Exactly one thing varies: the identity of the companion instruction**
(`prompts.py:63-79` asserts it structurally).

All 56 cells of a block share one question, in both configurations, at all 8
draws. Blocks congruent mod 4 share the solo wording index.

### 5.6 Exclusions, retries, missing data

**[P] There are none.** No generation is discarded for what it says, no draw
is selected, and there is no retry path. Truncated and empty responses are
scored, not dropped. Completeness is verified over the union of batches: every
`(block, cell, draw)` identity exactly once, with missing, duplicate and
unexpected rows all refusals (`confirmatory_run.py:166-190`).
`MISSINGNESS_REPORT_THRESHOLD = 0.01` (`constants.py:805`) governs reporting,
not exclusion.

### 5.7 Exact row counts

**Registered design budget** (`dci1/src/dci1v7/design/budget.py`, reported by
`tools/v7_compute_budget.py` → `reports/dci1v7/development/d1_compute_budget.json`):

| Option | Cells | Models | Generations |
|---|---:|---:|---:|
| `384_blocks_m4` | 56 | 4 | 830,016 |
| `four_models_47_cells` | 47 | 4 | 1,054,848 |
| **`four_models_56_cells`** (adopted) | 56 | 4 | **1,174,080** |
| `two_models_56_cells` | 56 | 2 | 587,040 |

Of the adopted option, the **confirmatory** portion is
`56 × 384 × 8 = 172,032` per replication, **688,128** across four models; the
remainder is calibration, screen, probe and expansion burden.

**Realised rows.**

| Lane | Model | Role | Cells/block | Confirmatory rows |
|---|---|---|---:|---:|
| `dci1v7-development` | qwen3-4b | repeat | 26 | 79,872 |
| `dci1v7-development-r3` | qwen3-4b | **canonical** | 26 | 79,872 |
| `dci1v7-development-r3` | gemma-3n-e2b-it | repeat | 29 | 89,088 |
| `dci1v7-development-r4` | qwen3-4b-instruct-2507 | **canonical** | 26 | 79,872 |
| `dci1v7-development-r4` | gemma-3n-e4b-it | **canonical** | 29 | 89,088 |
| `dci1v7-development-r5` | gemma-3n-e2b-it | **canonical** | 29 | 89,088 |

(`reports/dci1v7/dossier/lanes.csv`, columns `cells_per_block`,
`confirmatory_rows`; `prefreeze_run.py:497-500`.)

**Registered study:** 118,176–142,320 **pre-confirmatory** rows per
replication, **0 confirmatory** (`reports/dci1v7/CLOSURE.md`).

---

## 6. Calibration and reference selection

### 6.1 Operating-point selection

**[P]** Both severities are chosen per model from measured solo-compliance
curves, **on raw solo compliance, not on ι** — the code says so in terms
(`dci1/src/dci1v7/stages/regime.py:192-194`):

```
eligible(q)  <=>  measured solo compliance at q lies inside the band
selected     =   argmin over eligible q of ( |curve[q] - aim|,  q )   # ties to SMALLER q

A:  band (0.50, 0.85)  aim 0.70   grid 1-8        # TARGET_BAND, TARGET_AIM
B:  band (0.60, 0.95)  aim 0.80   grid 7-14 (+15,16)  # FOCAL_BAND, FOCAL_AIM
```

(`constants.py:171-174`.) The selection must be **bracketed** — both grid
neighbours measured at calibration precision — else
`OPERATING_POINT_AT_GRID_BOUNDARY` is recorded (`regime.py:206-219`).
Exhaustion yields `TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED`.
**m\* is frozen at Gate 2** and no later stage may move it; the composed probe
may stop a replication but never steer it
(`dci1/src/dci1v7/stages/composed_probe.py:802-882`).

Three further preconditions at (n\*, m\*), else `REGIME_NOT_FOUND`
(`regime.py:246-307`): both solo rates inside their bands; B's solo vacuity ≤
`REGIME_VACUITY_MAX = 0.10`; and the graded shares above 0.99 and below 0.01
each ≤ 0.99, read as a **share** (`GRADED_CLAUSE_READING = "share"`,
`constants.py:175-179`). Plus §34 D17's construct floor: chance compliance for
B at m\* on the load-zero cells ≤ **0.50**, a point estimate with the Wilson
interval reported beside it (recorded per lane as
`construct_floor_quantity = chance_compliance`, `construct_floor_value = 0.5`).

### 6.2 Candidate pool

**[P]** The §12.7 calibration population: **all** Tier-1 and Tier-2 rungs
unconditionally, plus at most `CALIBRATION_TIER3_CAP = 24` Tier-3 rungs
ordered by ascending pre-screen |ι − ι_A| (`constants.py:188-193`;
`stages/regime.py:151-182`). "That ordering is the one place a pre-screen
point estimate still decides anything, and it decides only which Tier-3 rungs
are *measured*, never admission." There is **no pre-screen distance caliper**:
v4r4's was deleted (`constants.py:23-29, 182-187`) because the two stages' ι
estimates disagree by a median of 0.071 and 35.7 % of candidates move further
between them than the whole caliper width. Pre-screen retention is a Wilson
interval intersecting `PRESCREEN_RETENTION_BAND = (0.05, 0.95)`.

The population is 674 instruments over 40 families; the measured pool is
recorded per lane in `reports/dci1v7/dossier/reference_candidates.csv`
(833 rows, each with its earliest failing `V(R)` component and values).

### 6.3 The difficulty coordinate

**[P]** (`dci1/src/dci1v7/stages/calibration_table.py:77-99`)

```
kappa_c = chance compliance: P(c passes | unconstrained cell, same topics, same M)
iota_c  = (P_solo(c) - kappa_c) / (1 - kappa_c)
undefined and refused when kappa_c >= 0.99  (CHANCE_DEGENERACY_MAX)
```

ι is the registered **primary** matching coordinate; raw solo compliance is
the registered **secondary** coordinate under §34 D14, reported for agreement
only and never used to select.

### 6.4 The eight validity components

**[P]** `V(R) = V_spec ∧ V_sat ∧ V_head ∧ V_chance ∧ V_struct ∧ V_inter ∧
V_stab ∧ V_diff`, evaluated in that lexicographic order; the order fixes only
which failure is *recorded*, and an unevaluated component is never a pass
(`dci1/src/dci1v7/stages/validity.py:11-19, 116-143`). **No composite score
exists.**

| Component | Rule | Thresholds | Source |
|---|---|---|---|
| `V_spec` | complete structural record; wording length within tolerance of A's; parse independence | ±20 % word count | `validity.py:167-183` |
| `V_sat` | formal joint-satisfiability and non-entailment witnesses, plus a *realistic* witness against B at m\* inside the 60–120-word stem band | — | `validity.py:185-210`; `verifiers/witnesses.py:278-333, 407-431`; `verifiers/realistic_witness.py:8-15, 45-49` |
| `V_head` | 95 % Wilson interval for raw solo compliance wholly inside the headroom band; instruction lift; solo vacuity ceiling | band (0.10, 0.90); lift ≥ 0.20; vacuity ≤ 0.10 | `validity.py:213-251` |
| `V_chance` | chance rate and its Wilson upper bound below ceilings | κ ≤ 0.75; upper ≤ 0.85 | `validity.py:254-279` |
| `V_struct` | the family's declared tier admits the slot | core {1,2}; near-form {2}; class {3} | `validity.py:282-304`; `taxonomy.py:126-130, 216-249` |
| `V_inter` | projected composed compliance p̂ = κ(R\|B) + ι(1−κ(R\|B)) inside a band; displacement bounded. A missing κ(R\|B) is a **failure**, never "unevaluated" | p̂ ∈ (0.10, 0.90); \|Σ\| ≤ 0.25 | `validity.py:307-329` |
| `V_stab` | independently admissible on Calibration-A *and* Calibration-B; 95 % percentile-bootstrap interval for the split difference of ι **and** of raw solo compliance wholly inside a bound; **10,000 resamples over topics** | ±0.20 (`STABILITY_BOOTSTRAP_RESAMPLES = 10_000`, `constants.py:296`) | `validity.py:332-345`; `stages/stability.py:173-201` |
| **`V_diff`** | **the caliper**: (1) \|ι_R − ι_A\| within caliper; (2) 95 % Newcombe interval for the paired solo-rate difference intersects a region; (3) raw-coordinate secondary check | (1) `REFERENCE_CALIPER = 0.10`; (2) ±0.05; (3) `SECONDARY_COORDINATE_CALIPER = 0.15` | `validity.py:348-390`; `constants.py:304, 309` |

Spectrum rungs run every component **except** `V_diff` — by design, since their
purpose is to sit ±0.20 away from ι_A (`stages/selection.py:62-63`;
`validity.py:410-415`).

### 6.5 Selection algorithm and deterministic tie-breaking

**[P]** `dci1/src/dci1v7/stages/selection.py:121-593`, `K = N_CORE_REFERENCES = 3`
(`constants.py:333`).

```
pool = pooled 192-topic calibration rows          # Calibration-A (96) + B (96), M_CAL = 4

for each Tier-1/Tier-2 family f:
    for each measured rung: evaluate all 8 components of V(R), slot = core
    if no rung passes: f not admitted             # every rung's failure reason retained
    else: best_rung(f) = argmin( round(|iota_R - iota_A|, 12), restrictiveness_key )

ranked = sort admitted families by
         ( |iota - iota_A|, structural_tier, registered feature-group order,
           restrictiveness_key, family_id )       # fully deterministic

chosen = []; groups = {}
while ranked and len(chosen) < 3:
    v = pop(ranked)
    if v.feature_group in groups:                             continue  # group exclusivity
    if v.tier != 1 and lookahead cannot still reach 2 Tier-1: continue
    triple = select_spectrum_triple(v)     # needs rungs strictly below AND above iota_A
    if triple is None:                                        continue
    chosen += v; groups += v.feature_group

if distinct discourse roles in chosen < 2:
    replace the LOWEST-ranked member with the highest-ranked qualifying family
    of a different role (new group, triple exists, Tier-1 count preserved)

identified = (len(chosen) == 3) and assert_core_set_structure(chosen)
if not identified:
    re-run with require_spectrum = False
    if that identifies: core stands, spectrum arm dropped,
                        status += DIFFICULTY_SUPPORT_NOT_IDENTIFIED
    else:               status += EXCESS_NOT_IDENTIFIED     # irreversible; core arm lost
status += REFERENCE_POOL_SAME_FORM                          # always, unconditionally
```

Other arms: spectrum targets ι_A ± 0.20 within the same family, strictly one
below and one above, nearest each target; near-form takes Tier-2 families
*excluding* the core families, 3 distinct groups, full `V(R)` — fewer than 3 →
`NEAR_FORM_ARM_NOT_AVAILABLE`; the class control takes Tier-3 **and**
`constraint_class == "budget"`, minimum |ι − ι_A|, ties by family id — none →
`CLASS_ARM_NOT_AVAILABLE`, distance > `CLASS_MATCH_CALIPER = 0.15` →
`CLASS_ARM_NOT_MATCHED`, and `COMPANION_CLASS_NOT_MATCHED` is recorded always.
Backups are the first 2 spare qualified families in registered order and
**never substitute**: `BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 = False`
(`constants.py:338-341`) and the guarantee is that no substitution *function*
exists (`selection.py:596-622`; `run/gates_run.py:2376-2398`).

Selection precedes any composed outcome (the §6 firewall): the calibration
table schema refuses composed columns before any value is read
(`calibration_table.py:56-68, 103-148`), and the manifest walker refuses
model-adaptive values (`n_star`, `m_star`, `admitted_references`, …) anywhere
in the registration payload (`protocol/manifest.py:86-94, 940-960`).
Model-specificity is enforced: every calibration row carries `model_key` and
the loader refuses a foreign one; κ(R|B) refuses cross-model transfer by name
(`calibration_table.py:264-267`; `stages/interaction.py:114-119`).
References are **not** position-specific: one slot map serves both
configurations (`cells.py:172-184`).

### 6.6 Exact selected references, per lane

**[D]** From each lane's `GATE_3B_REFERENCE_SELECTION` record, tabulated in
`reports/dci1v7/dossier/references_selected.csv` (21 rows). Canonical lanes in
bold.

| Lane | Model | R1 | R2 | R3 | CL |
|---|---|---|---|---|---|
| `dci1v7-development` | qwen3-4b (repeat) | MK1:7 (thus) | MK7:2 (instead) | MK6:8 (namely) | — |
| **`-r3`** | **qwen3-4b** | **MK1:6** (thus) | **MK7:2** (instead) | **MK6:8** (namely) | — |
| `-r3` | gemma-3n-e2b-it (repeat) | MK2:7 (hence) | MK1:1 (thus) | MK5:8 (indeed) | RF12:6 |
| **`-r4`** | **qwen3-4b-instruct-2507** | **MK4:5** (whereas) | **MK3:3** (though) | **MK8:4** (overall) | — |
| **`-r4`** | **gemma-3n-e4b-it** | **MK5:6** (indeed) | **MK4:7** (whereas) | **MK6:3** (namely) | **RF12:7** |
| **`-r5`** | **gemma-3n-e2b-it** | **MK2:1** (hence) | **MK1:4** (thus) | **MK5:7** (indeed) | **RF12:6** |

All core references are Tier 1, `constraint_class = production`. Realised
caliper distances |ι_R − ι_A| run 0.0006–0.049, all well inside 0.10.

**[!] The two repeat lanes re-selected different reference severities**
(e.g. qwen3-4b MK1:7 vs MK1:6; gemma-e2b MK2:7/MK1:1/MK5:8 vs MK2:1/MK1:4/MK5:7).
The two roots re-ran §12–§13 from scratch, so the difference between a repeat
and its canonical lane is **selection-plus-sampling variability, not
measurement noise**. Repeat lanes are never plotted as independent
observations; `v7_paper_figures_check.py` fails if one reaches an output.

### 6.7 Calibration sample sizes

| Quantity | n | Draws | Source |
|---|---:|---:|---|
| Pre-screen ladder | 24 topics | 1 | `N_PRESCREEN`, `LADDER_SCREEN_DRAWS` |
| Cap selection | 96 prompts across loads 0/1/2 | — | `CAP_SELECTION_PROMPTS` |
| Calibration-A | 96 topics | 4 | `N_CALIBRATION_A`, `M_CAL` |
| Calibration-B | 96 topics | 4 | `N_CALIBRATION_B`, `M_CAL` |
| Pooled selection table | **192 topics** | 4 | `N_CALIBRATION` |
| Composed validation (Gate 4) | 24 topics | 4 | `N_COMPOSED` |
| Confirmatory | 384 topics | 8 | `N_CONFIRMATORY`, `M_DRAWS` |

`V_stab` bootstrap: 10,000 percentile resamples **over topics**
(`stability.py:173-201`). Per-lane ι_A stability results, with `n_qualified`
(44–84) and `n_stable` (9–18), are in `dossier/iota_a_stability.csv`.

### 6.8 Coverage conditions C1–C8

**[P]** Evaluated on eligible rungs only; a rung with no ι (κ ≥ 0.99) is
dropped and recorded (`regime.py:545-714`).

| Cond. | Rule | Gates (after amendment A7) |
|---|---|---|
| C1 | ≥1 eligible rung strictly below and one strictly above ι_A | core arm |
| C2 | ≥3 Tier-1/2 feature groups below and ≥3 above | spectrum arm |
| C3 | ≥8 rungs within 0.15 of ι_A, from ≥4 groups | core arm |
| **C4** | ≥6 feature groups whose family straddles ι_A with ≥3 rungs spanning ≥0.40 in ι | spectrum arm |
| C5 | ≥16 eligible rungs | core arm |
| C6 | ≥8 Tier-1/2 families from ≥6 groups | core arm |
| C7 | ≥1 Tier-3 budget rung within 0.15 of ι_A | class arm |
| C8 | ≥3 Tier-2 rungs from three groups | near-form arm |

Two bases: a **certificate** on the 24-topic pre-screen at 1 draw, and the
**gating re-read** on the 192-topic calibration table at Gate 2's measured ι_A
(`stages/feasibility.py:466-569`). A bounded expansion loop
(`EXPANSION_MAX_ROUNDS = 2`, `EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND = 4`,
`constants.py:196-198`; picks only from the frozen reserve) may repair a
failure before it is final.

**[D] All four registered replications and all six rehearsal lanes passed C4
at the screen and lost it on the calibration basis** (`feasibility.py:496-500`;
per-lane detail in `dossier/coverage_c1_c8.csv`, 48 rows). This is what cost
the spectrum arm everywhere.

### 6.9 [!] Known implementation departures

**(a) The chance column is 0.0 for every candidate.** On the executed code the
calibration table's chance column reproduces "the measured chance over every
grid row where the candidate is absent *when some grid row states it*, and 0.0
otherwise", which for a non-outcome candidate is always the second branch — "a
defect against §13.2 … deliberately NOT corrected here"
(`dci1/src/dci1v7/run/gates_run.py:673-691`). So **each candidate's ι collapses
to its raw solo compliance**. Verified directly on the signed Gate-3B records
(`references_selected.csv`, columns `iota_reference` vs `solo_compliance`:
identical to all recorded digits on every row).

**ι_A, by contrast, is genuinely chance-corrected**, taking its κ from a
different code path (`gates_run.py:546-548`). Measured target shift:

| Model | solo(A) | ι_A | shift |
|---|---:|---:|---:|
| `qwen3-4b` | 0.6875 | 0.6855 | 0.002 |
| `gemma-3n-e2b-it` | 0.5938 | 0.5891 | 0.005 |
| `gemma-3n-e4b-it` | 0.7318 | 0.7252 | 0.007 |
| `qwen3-4b-instruct-2507` | 0.5664 | 0.5397 | 0.027 |

All are well inside the 0.10 caliper. **The paper must say the matching was
executed on raw solo compliance for candidates, and must not claim
chance-corrected matching on both sides.**

**(b) The measured consequence — the broad-class control was not
difficulty-matched.** Recomputing κ and ι on the confirmatory unconstrained
cells (the cells §13.2 defines κ on) from the signed masked rows plus the mask
key gives (`CHANGES_SCIENTIFIC.md`, entry 2026-08-30;
`dossier/posthoc_confirmatory_difficulty.csv`):

| Lane / model | CL | κ recorded | κ confirmatory | ι used | ι confirmatory | \|ι−ι_A\| conf. | lift conf. |
|---|---|---:|---:|---:|---:|---:|---:|
| `-r3` / gemma-3n-e2b-it | RF12:6 | 0.000 | 0.349 | 0.583 | 0.400 | 0.217 | +0.260 |
| `-r5` / gemma-3n-e2b-it | RF12:6 | 0.000 | 0.350 | 0.592 | 0.406 | 0.213 | +0.264 |
| `-r4` / gemma-3n-e4b-it | RF12:7 | 0.000 | 0.807 | 0.781 | −0.093 | 0.816 | −0.018 |

§13.10's caliper is 0.15, so **all three class-arm lanes would have recorded
`CLASS_ARM_NOT_MATCHED`; none did**. On `gemma-3n-e4b-it` the companion's solo
compliance (0.789) is *below* its own chance rate (0.807) — instruction lift
−0.018 against `V_head`'s floor of +0.20 — so under a correct chance column
that severity would have been rejected before selection.

**The three core references are unaffected.** Every Tier-1 marker family has
κ = 0.000 on the confirmatory blocks on every lane, so ι(R) = raw solo
compliance *is* the correct value there; realised |ι_{R_j} − ι_A| runs
0.004–0.090. **Δ_R, Δ_j, D(B←A), D(A←B), Λ, Ξ and the F11 order contrasts are
unaffected.** `Δ_broad`, `D(B←CL)` and `Ord_CL` may be read only as a bound
from one companion, carrying `COMPANION_CLASS_NOT_MATCHED` **and** the
difficulty mismatch.

**(c) The composed proximity band (0.05, 0.95) selects nothing in v7.** v5/v6
registered it as a terminating criterion; v7 amendment A1 withdrew that, and
it is descriptive only (`constants.py:347-353`;
`freeze.thresholds.composed_proximity_band_is_descriptive = true`).

**(d) The fix for (a) is out of force.** It touches modules that revision V9
pins byte-for-byte, so it is recorded and left for a researcher decision, and
is **not** applied in any lane reported here.

---

## 7. Measurement

### 7.1 Word segmentation — the primitive everything rests on

**[P]** **No regular expression.** A word is a **maximal run of
Unicode-alphabetic characters**, accumulated by a loop over `str.isalpha()`;
every non-alphabetic character is a boundary
(`dci1/src/dci1v4/verifiers/words.py:15-27`, `alpha_runs`;
`words_lower(text) = alpha_runs(text.lower())` at `:30-32`). The prose
specification states the class as Unicode general category L, and Gate 1
proves `str.isalpha()` ≡ category-L over all 1,114,112 codepoints
(`dci1/src/dci1v7/stages/gate1.py:145-163`).

Consequences, all verified by probe, all needing a sentence in the paper:

- Digits, underscores and symbols split: `abc123def` → two words;
  `**bold**` → one.
- **Hyphenated forms split**: `state-of-the-art` → four words.
  **Apostrophes split**: `don't` → `don`, `t`.
- URLs split into alphabetic pieces: `https://example.com/thus` → four words —
  including a countable `thus`.
- Soft hyphen, zero-width space and non-breaking space are boundaries.
- Precomposed `café` is one 4-letter word; **NFD-decomposed `naïve` splits**,
  because the combining mark is not alphabetic.
- CJK and fullwidth text count as alphabetic runs.

### 7.2 The three predicate forms in use

**[P]** (`dci1/src/dci1v7/verifiers/statistics.py:13-19`;
`verifiers/compliance.py:118-140`)

```
B (focal, budget)      statistic = max(len(run) for run in alpha_runs(text)), 0 if none
                       pass  <=>  statistic <= m         # casing irrelevant; no tolerance
                       graded = 1 - (#words longer than m)/(#words), 0.0 if no words

A (exact count)        statistic = count of alpha_runs(text.lower()) == "however"
                       pass  <=>  statistic == n         # FOLD-then-segment

MK1-MK8 (exact count)  statistic = count of w in [run.lower() for run in alpha_runs(text)]
                       equal to the marker
                       pass  <=>  statistic == q         # SEGMENT-then-fold
```

**Whole-word equality after folding**, so substrings never count
(`thusly` → 0), case is irrelevant, and adjacent punctuation is irrelevant
(`hence hence, hence; hence.` → 4). But hyphens and zero-width characters
**create** occurrences: `though-provoking though` → 2
(`verifiers/boundary_v5.py`).

**[!] Two counting conventions — registered and quantified.** A folds first
then segments; the marker families segment first then fold
(`statistics.py:13-19`; `dci1/src/dci1v4/verifiers/words.py:14-32`). The code
enumerates the whole Unicode range to prove the two conventions differ on
**U+0130 (İ) alone**, "which occurs zero times in the 285,936 rows this
programme has generated" (`words.py:31-32, 51-75`). Report it as a stated
design fact, not a bug.

Other library forms: `count_budget` (S ≤ q), `rate_budget`
(100·S/W ≤ q, denominator always *words*), `count_lower_bound` (S ≥ q) and
`exact_count` over semicolons, commas or sentences. Sentence segmentation
counts maximal runs of `.` `!` `?`, adding one if non-whitespace follows the
last run; the docstring registers the consequence verbatim: *"a decimal point
and an abbreviation's full stop both terminate a sentence under this rule: a
registered over-count, stated rather than discovered"* (`words.py:78-105`).

### 7.3 Scoring pipeline and invalid outputs

**[P]** Evaluation is **binary**; a graded score in [0,1] is recorded alongside
but is never the primary outcome. **Every registered instance is scored on
every row**, not only the stated ones — a verdict on an unstated constraint is
a chance observation with `present=False`, and a guard refuses chance
observations inside any treated estimand (`run/execute.py:536-540`;
`verifiers/compliance.py:260-271`). That is where κ(R|B) comes from at zero
extra generation cost. See §1.8 for the empty / truncated / refusal /
exception table.

Vacuity: `NON_VACUITY_MIN_WORDS` marks a budget pass under 20 words vacuous;
an exact count and a lower bound carry no word-count clause (their own rules
force production); truncated or blank text is never non-vacuous
(`compliance.py:57`, `:177-193`). A vacuous pass **stays a pass**; §17.4 recomputes
claims under a forced non-vacuous scale (`compliance.py:75`, `:210`).

Row fields recorded (`freeze.codebook.row_fields`, 28 fields):
`area, arm, block_id, cell_id, classification, draw_index, empty,
finish_reason, in_stem_band, load, model_id, model_key, model_revision,
prompt_hash, raw_response, row_id, scores, seed, slots, stage, study_id,
token_count, topic_id, topic_split, truncated, verifier_hash, word_count,
wording_indices`.

### 7.4 Verifier validation — Gate 1's ten conditions

**[P]** All-or-terminal (`dci1/src/dci1v7/stages/gate1.py:376-518`):

1. **Determinism across three OS processes must be exactly 1.000.**
2. An **independent reimplementation written from prose alone** (stdlib only, a
   deliberately different route — `unicodedata.category`, `groupby`,
   `re.split`) must agree on all 22 statistics for every response and on
   pass/graded/vacuity for a declared sample of 1,200
   (`dci1/src/dci1v7/verifiers/independent.py`).
3. A frozen **boundary suite of 177 cases over 674 instruments** must agree
   exactly and cover 34 required phenomena.
4. An **adversarial corpus** must cover 18 named phenomena (zero-width, soft
   hyphen, combining marks, İ case-folding, fullwidth, markdown …) with
   realised frequencies reported beside them.
5. **Mutation validation** must detect six seeded defect kinds, including a
   segmentation-order drift.
6. **Joint-satisfiability witnesses** must pass.
7. **Wording invariance**: verdicts must be invariant across all four wordings
   of each instrument (20 responses × 674 instruments × 4 wordings).

The gate is bound to the canonical verifier hash, re-verified at 18 registered
entry points before any work (`constants.py:585-593`,
`VERIFIER_BOUND_ENTRY_POINTS`), and again *after* a stage's generation — if
the hash moved mid-stage the rows cannot be placed and the stage fails closed
(`execute.py:482-486`).

### 7.5 Verifier hash

`verifier_source_hash() = sha_obj(source_hashes())`
(`dci1/src/dci1v7/verifiers/__init__.py:51-62`), covering seven files by path:

```
dci1v4/words.py       edafc17e19711eb277af2a97d54ae553d14b330d87e2ab0c98373b65226ef726
dci1v4/target.py      aa221381cb6141e8d2d5f75e2695e109a6952035d724a8c5710b0fe8e43addf4
dci1v4/statistics.py  db5eeb21d5296efab444d76e56a543e116cadf527c682431d4f0cca0c8014371
dci1v7/words.py       17ccbb9533e4898f3318ede23740e1b07cdadcb1035ee17ebe4e5b95d3efda22
dci1v7/statistics.py  c557edb3e25f8f9c0d8369bcf52adb2eb6de94b2609b656c67bb8fe002736a57
dci1v7/constraints.py 890e418496257977ea1f2551189abc3808ffc817c083aa311286529e16fb750a
dci1v7/compliance.py  0848c1db5b1a03ec7716d60689f2a5298551bc25c63a0916926a333d6b57661a
```

(from `GATE_5_FREEZE.freeze.verifier_sources`; the composite is
`1ffd4044063506b379c97f4f0ef42c7532c843a6847f52ea1344d82b15830fb3`, identical
across **all six lanes** — `dossier/lanes.csv`, column `verifier_hash`.)

Carried sources are hashed at their own location, not re-exported, so a change
underneath cannot drift silently (`verifiers/__init__.py:1-24`).

### 7.6 [!] Answer quality and human-judged compliance are NOT measured

**There is no human labelling anywhere in v7.** The measurement basis
`human_validated` is explicitly *refused* (`constants.py:461-463`;
`gate1.py:385-394`); the strongest basis Gate 1 can record is
`deterministic_measurement_validated`, which is what all six lanes record
(`dossier/lanes.csv`, column `measurement_basis`).

A verifier-audit module exists for building operationalisation cards, but it
carries its own standing note: *"it shows the verdict, so it measures nothing
about human-verifier agreement and its output must never be reported as an
agreement rate"* (`dci1/src/dci1v7/stages/verifier_audit.py:38-41`).

A registered scope sentence attaches permanently to every analysis record,
every claim at every rung, and the final report (`constants.py:464-465`):

> "the outcomes are verifier-defined and support no claim about compliance as
> an independent human would judge it"

**No estimand in this study measures answer quality, helpfulness,
truthfulness, or compliance as a human would judge it.** The paper must carry
that sentence, or its equivalent, in the Methods and again beside the results.

---

## 8. Statistical analysis

### 8.1 Scale and sign convention

**[P]** The primary scale is **compliance**, not failure
(`dci1/src/dci1v7/analysis/estimators.py:51`, `PRIMARY_SCALE = "compliance"`).
No estimand operates on a failure rate. All contrasts are **differences of
proportions in [−1, 1]**; the registered thresholds 0.10 and 0.25 are on that
scale.

```
P(c)     = compliance probability of c, estimated by a block-mean of binary verdicts
D(c<-g)  = P(c | c alone) - P(c | c with g, in the named configuration)
           positive => composition REDUCED delivery of c
```

### 8.2 Exact estimand definitions

All per-block, then averaged over the 384 blocks.

| Symbol | Formula | Positive means | Family | Source |
|---|---|---|---|---|
| `D(B<-A)` | P(B\|solo) − P(B\|composed with A) | A reduces B's delivery | F1 | `estimators.py:76-83` |
| `D(A<-B)` | P(A\|solo) − P(A\|composed with B) | B reduces A's delivery | F1 | `estimators.py:76-83` |
| `D(B<-R_j)` | P(B\|solo) − P(B\|composed with R_j) | R_j reduces B | F2 | `estimators.py:76-83` |
| `D̄(B<-R)` | (1/3) Σ_j D(B←R_j), elementwise over blocks | — | F2 | `estimators.py:86-92` |
| **`Δ_R`** | **(1/3) Σ_j P(B\|B+R_j) − P(B\|B+A)** | **A costs B more than matched companions** | **F1** | `estimators.py:138-152` |
| `Δ_j` | D(B←A) − D(B←R_j), one per reference | — | F2 | `estimators.py:195-201` |
| `Λ` | D(B←A) − D(A←B) | B loses more under A than A under B | F1 | `estimators.py:95-100` |
| `Ξ` | Δ_R − [D(R̄←A) − D(R̄←R̄′)] | the excess is specific to outcome B | F1 (direction-only gate) | `estimators.py:238-244` |
| `Δ^A` | D(A←B) − (1/3) Σ_j D(A←R_j) | — | F3 (demoted diagnostic) | `estimators.py:204-211` |
| `D(R̄<-g)` | (1/3) Σ_j D(R_j←g), g outside the set | — | F4 | `estimators.py:214-223` |
| `D(R̄<-R̄′)` | mean over the 6 ordered pairs (j≠k) of D(R_j←R_k) | — | F4 | `estimators.py:226-235` |
| `Δ_near` | (1/3) Σ_k P(B\|B+N_k) − P(B\|B+A) | — | F9 — **never available** | `estimators.py:247-268` |
| `Δ_broad` | P(B\|B+CL) − P(B\|B+A) | — | F10, bounding only | `estimators.py:271-287` |
| `Ord_A`, `Ord_B` | composed(outcome second) − composed(outcome first) | loss larger with the outcome stated first | F11 | `estimators.py:330-364` |
| `Ord_Λ`, `Ord_R̄`, `Ord_CL` | Ord_B − Ord_A; mean over references; class control | — | F11 | `estimators.py:367-402` |
| `δ_difficulty` | D(B←A) − [ᾱ + β·ι_A], OLS with family intercepts on 9 non-A points | — | F1 — **never identified** | `analysis/spectrum.py:168-181, 343-354` |
| `α_k`, `β`, `γ_tier` | secondary fit Y = α_f + β·d + γ·1[Tier 2] on 12 points | — | F8 — **never identified** | `spectrum.py:374-390, 596-611` |
| `vac(·)` | vacuity difference, composed − solo | — | F6 gate | `estimators.py:460-467` |

F5 duplicates the F1 estimators on two alternative scales
(`non_vacuous_compliance`; `graded_threshold` at
`GRADED_ROBUSTNESS_THRESHOLD = 0.99`) as robustness variants
(`run/analysis_run.py:201-228`). **Eleven declared multiplicity families,
F1–F11.**

**[!] The definition to write.** Do **not** write
`D(B←A) = (1/K) Σ_j D(B←R_j)` — that asserts the null. The registered object
is their difference, and both forms are computed and asserted equal:

```
definitional (uncancelled)   Δ_R = D(B←A) − (1/K) Σ_j D(B←R_j),  K = 3
                                                        # estimators.py:155-162
cancelled (actually computed) Δ_R = (1/K) Σ_j P(B|B+R_j) − P(B|B+A)
                                                        # estimators.py:138-152
```

The solo cell cancels exactly. Agreement is asserted every run to
`ALGEBRAIC_FORM_TOLERANCE = 1e-9` (`estimators.py:186-192`,
`assert_delta_r_forms`; `constants.py:451`); worst observed discrepancy across
the signed records is 1.1 × 10⁻¹⁶, and re-derivation from the reconstructed
block table agrees to `0.00e+00` in all four canonical lanes × both positions
(`VALIDITY_AUDIT.md` §0). `Δ_R` **raises** if the reference count is not 3
(`estimators.py:143-147`).

### 8.3 Block averaging and bootstrap

**[P]** `dci1/src/dci1v7/analysis/bootstrap.py`.

| Element | Specification | Line |
|---|---|---|
| Point estimate | mean over the 384 blocks of the estimator's per-block value | `:114-119` |
| Method | nonparametric **block bootstrap**: blocks drawn with replacement, carrying *every* cell mean of each drawn block. Cells are never resampled | `:1-8, 119-131` |
| Resampling unit | the block (= one confirmatory topic); both configurations travel together | `:1-8` |
| Replicates | **10,000** (`BOOTSTRAP_RESAMPLES`, `constants.py:448`) | `:122` |
| Shared draw | **one index draw per replicate**, applied to every member of a family | `:122-131` |
| Refit inside replicates | **yes, for the difficulty members**: every replicate recomputes κ, the difficulty coordinates, the losses, refits the non-A relation, predicts at that replicate's ι_A and recomputes the residual. Δ_R is a per-block vector and needs no refit | `:15-29, 115-119` |
| Studentisation | each member standardised by its bootstrap standard error (sample SD, n−1) | `:133-141` |
| RNG | `random.Random(seed)`, pure stdlib — no numpy anywhere in `dci1/src/dci1v7/` | `:120` |
| Seeds | `bootstrap_seed(phase, model_key)`, root 202608241, domain `dci1v7:boot:v1` | `seeds.py:26-39, 75-78` |

### 8.4 Simultaneous intervals and families

**[P]** **Studentised maximum-modulus.** Per replicate take
`max over members of |rep − est| / se`; the critical value is the 95th
percentile of that maximum; bounds are `est ∓ critical · se`
(`bootstrap.py:143-156, 170-172`). **Decisions read the simultaneous interval.**
Marginal 2.5/97.5 percentiles of each member's own replicates are reported
alongside and are **not** used for decisions (`bootstrap.py:164-169`).

A degenerate member (`se ≤ 0`) or a replicate whose refit was not identified
is retained, reported, and contributes no deviation
(`bootstrap.py:146-152`, `:174`).

- Confidence level 95 %.
- Eleven declared families **F1–F11**, per configuration, except F11 which is
  declared **across** configurations.
- **No cross-model family and no cross-model pooling.** A Šidák value is
  reported beside but never used.
- **No p-value is computed anywhere.** Inference is interval-versus-threshold
  throughout.

### 8.5 Thresholds and precision criteria

**[P]** All on the compliance-difference scale
(`freeze.thresholds`, `freeze.precision_preconditions`; `constants.py:372-385`).

| Threshold | Value | Applies to | Rule | Licenses |
|---|---:|---|---|---|
| SESOI | 0.10 | all contrasts | — | smallest difference treated as meaningful |
| Δ_R generic-load | 0.10 | Δ_R | lower > 0.10 → **L3a** | "A costs B at least the generic-load threshold more than matched same-form companions" |
| Δ_R pair-specific | 0.25 | Δ_R | lower > 0.25 → **L3b** | pair-specific excess |
| Δ_R upper bound | 0.10 | Δ_R | **upper < 0.10 → L3c** | "the local excess is bounded below the generic-load threshold" — **one-sided** |
| Equivalence region | ±0.10 | δ_difficulty (L3e) | interval wholly inside ±0.10 *and* precision met | — |
| Precision precondition | D 0.05; Δ_R 0.05; Δ_near 0.05; δ_diff 0.05; Ord_A/Ord_B 0.05; Δ_j 0.06; Λ 0.08; Ord_Λ 0.08 | — | half-width above it → `INSUFFICIENT_PRECISION` | direction may still be reported; threshold and equivalence statements withheld |
| L1 solo headroom floor | 0.05 | D(·←·) | solo compliance ≤ 0.05 → L1 not emitted | — |

**[!] "Equivalent to zero" is not what L3c says.** L3c is a **one-sided upper
bound**, `upper < 0.10` (`analysis/claims.py:313-314`). An interval lying
wholly *below* zero also satisfies it. Two-sided equivalence
(`wholly_inside(±0.10)`) is a different predicate applied in v7 only to
δ_difficulty at L3e (`claims.py:182-183, 390-391`) — an estimand never
identified. **No equivalence claim about Δ_R was licensed in any lane.**
The defensible sentence is "the companion-specific excess is bounded above by
0.10 with 95 % simultaneous confidence", plus the direction where resolved.

### 8.6 Boundary and degenerate-interval handling

**[P]**, revised pre-adoption by the boundary audit of 2026-08-28 with zero v7
rows in existence (`analysis/boundary.py:256-370`):

1. **Structural zero** — every differenced cell at the same exact boundary in
   every block; se = 0 and the simultaneous interval degenerates to [0,0], so
   the decision interval becomes the Wilson allowance about zero, ±h_n, with
   h_384 = 0.0099 and h_24 = 0.138. No directional level is reachable by
   construction.
2. **Arm at a boundary** — the simultaneous interval is widened *in the open
   direction only*, by each boundary constituent's absolute weight × 0.0099
   (a third of it per reference in Δ_R's mean). Conservative by construction.
3. **Compressed direction** — when an arm sits above 0.90 or below 0.10 the
   attainable range is recorded and a status attached; **no verdict changes**
   (`boundary.py:41-45`).

The revision's own justification, worth a limitations sentence: the earlier
blanket veto "made 3072/3072 perfect draws weaker evidence than 3071/3072"
(`boundary.py:19-25`).

### 8.7 The claim ladder as coded

| Level | Member | Gate and rule | Source |
|---|---|---|---|
| L1 | D(B←A), D(A←B) | solo headroom, not a structural zero, vacuity-forced recomputation agrees, decision lower > 0 | `claims.py:804-847` |
| L2 | Λ | both L1s licensed; interval excludes 0 | `claims.py:856-897` |
| L3a/b/c | Δ_R | precision precondition, then the three threshold comparisons | `claims.py:283-320` |
| L3d/e | δ_difficulty | support must hold first, else `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and L3a–c only | `claims.py:355-392` |
| L4a | the six named F1 members | identical classification in *both* configurations of one model | `claims.py:1040-1131` |
| L4b | F11 order contrasts | both configurations analysed, not a structural zero, precision met, interval excludes 0. **An interval containing zero is not order-invariance** | `claims.py:1134-1197` |
| L5 | — | **no emitter exists; permanently withheld** | `claims.py:1200-1205` |

Every L3 statement carries `REFERENCE_POOL_SAME_FORM` and a fixed qualifying
sentence, appended unconditionally (`constants.py:474-478`), and every L3c
carries scope `same_form_only` with: *"no excess relative to same-form
exact-count companions; this is not the refutation verdict, which requires the
near-form arm (§34 D18)"* (`constants.py:494-496`).

Two joint-reading rules suppress a level rather than resolve a conflict:
`LOCAL_TIER_DISAGREE` and `LOCAL_AND_SPECTRUM_DISAGREE`
(`claims.py:409-451, 616-635`).

### 8.8 Masking / blinding

**[P]** After confirmatory generation and before any analysis, the **companion
label** of every composed observation is permuted within
(outcome, configuration, block); solo and unconstrained cells pass through,
and companion *difficulties* are not permuted since they were fixed at Gate 3
(`analysis/masking.py:1-27, 278-310`). Mask seed root 202608245, domain
`dci1v7:mask:v1`.

Six members are **forbidden** in the masked phase — δ_difficulty, **Δ_R**, β,
α_1..3, γ_tier (`masking.py:104-107`). The **analysis code hash** over eight
modules is sealed into the masked record and re-verified at unmasking; a
mismatch raises "the analysis code moved between the seal and the unmask"
(`analysis_run.py:67-75, 998, 1062-1068`). The mask key opens exactly once and
there is deliberately no re-unmasking path.

### 8.9 No-pooling and no-p-value rules

- **Models are never pooled**; there is no cross-model multiplicity family and
  no cross-model scalar (`bootstrap.py`; `METHODS.md` §11.1). Enforced in the
  figure audit as well (`v7_paper_figures_check.py`).
- **No p-values anywhere.**
- Repeat lanes are never treated as independent observations.
- Mediation claims, length adjustment, and any statement about *why* an order
  effect occurs are forbidden.
- *"Failure to exclude zero is never reported as absence."*

### 8.10 Scripts and commands that reproduce the tables and figures

```bash
# 1. the data layer: reads only signed records; aborts unless the block-level
#    reconstruction reproduces the signed UNMASKED_ANALYSIS point estimates
#    (tolerance 1e-12, all six lanes verified)
python dci1/tools/v7_dossier.py            # -> dci1/reports/dci1v7/dossier/

# 2. Figures 2-4 and Table 1 (needs matplotlib; see §2.3)
python dci1/tools/v7_paper_figures.py      # -> dci1/reports/dci1v7/paper_figures/

# 3. independent audit: does NOT import the generator; re-reads the signed
#    FINAL_REPORT records and parses table1_primary_results.tex back out of
#    LaTeX to compare digit for digit (265 checks)
python dci1/tools/v7_paper_figures_check.py
```

Outputs: `figure2_delta_r_forest.{pdf,svg,png}` (forest of Δ_R),
`figure3_loss_decomposition.{pdf,svg,png}` (raw loss vs matched-reference
loss), `figure4_direction_position.{pdf,svg,png}` (direction, panel A; order,
panel B), `table1_primary_results.tex` (booktabs, percentage points), plus the
exact per-figure CSVs and `captions.md`.

---

## 9. Provenance and integrity

### 9.1 Commits and hashes

| Item | Value |
|---|---|
| Repository HEAD (this audit) | `906a88dfb776a384e2aecdea3c78f2b195475f29` |
| HEAD for METHODS/dossier | `87a6c185a9bd7e0496548e5c3e0c44c63752bca3` |
| Registration commit (registered study) | `ed0446ff58d0efc70b7703c162997863a9530768` |
| Registered manifest hash | `969a5b9f1947faddc42809a62377c6a725382e93b8f098f7d6ae98b5eb91ca14` |
| Registered protocol hash → after A6–A8 | `15fa1786…82dc` → `2e91a1c0aa83a11573678df22c37ec3ef316c6606af2fa885ba10028ba9b5d2d` |
| Reference design spec hash (r5 lane) | `af5416524293d209a5798a1394f29d894976dc3a2ca71bd4550ec79761703e9e` |
| Canonical verifier hash (all six lanes) | `1ffd4044063506b379c97f4f0ef42c7532c843a6847f52ea1344d82b15830fb3` |
| Wording hash (r5) | `476dbaa7e516ad6c4f8db866a9694a627eb0184784c7033c13e655f1a74800f0` |
| Analysis code hash (r5, sealed at masking) | `5ca907f6342c94b2b77a6c45e70a45fd3a6664a2d4d8d8c0738c06cac71c4feb` |
| Calibration table hashes (A / B) | `57850f1c…a59e` / `bc7a7350…2c73` |

**Per-lane producing commits and freeze hashes** (`dossier/lanes.csv`):

| Lane | Model | Producing commit | Freeze hash |
|---|---|---|---|
| `dci1v7-development` | qwen3-4b | `13173db970e6e6c793319d7b20319181e4d68918` | `2683f680232aa3f2…8017` |
| `-r3` | qwen3-4b | `e0006b491118f4c60b3fef38e5ca7f7e15be10cd` | `9cfc245058bed3c1…b013` |
| `-r3` | gemma-3n-e2b-it | `aa226ca14fb6e42fd70b0f0543e4f9ee7f8f1082` | `fd8792b5dced9aeb…b702` |
| `-r4` | qwen3-4b-instruct-2507 | `3ea82b28122ba30ea0c0b23435fabfe84fbde495` | `0c11810fa264cd96…3ceb` |
| `-r4` | gemma-3n-e4b-it | `43bb22a533b0d57c2ff7486d5ea0af858ef972a0` | `3e9cb35987bed073…5b24d` |
| `-r5` | gemma-3n-e2b-it | `43bb22a533b0d57c2ff7486d5ea0af858ef972a0` | `4fd019c72f00628e…b7d0b` |

### 9.2 What a registration binds

**[P]** Two documents are hashed by content — the preregistration
(`user-notes/DCI1_preregistration_v7.md`) and a machine-readable reference
design spec (`dci1/reports/dci1v7/reference_design_spec.json`) — and both must
declare themselves adopted; silence reads as draft
(`protocol/manifest.py:116-136, 162-219`). The manifest binds 43 required
keys, closes all 26 §34 decisions, and is signed **HMAC-SHA256 over the
SHA-256 content hash** with a write-once 0600 key
(`dci1/src/dci1v4/engine/signing.py:22-65`). One registration commit binds a
whole study: a second commit is refused as needing formal supersession
(`manifest.py:1117-1175`).

Records are write-once (`O_CREAT|O_EXCL` + fsync), mirrored to a durable root
and byte-verified, and every read verifies hash **and** signature
(`dci1/src/dci1v4/engine/fs.py:43-56`;
`dci1/src/dci1v7/engine/transitions.py:140-155`).

### 9.3 Signed artifacts used for the paper

Every reported number traces to a **signed `FINAL_REPORT` record** in a
development-lane evidence tree:

```
dci1/evidence/<root>/evidence/dci1v7/<model>/FINAL_REPORT/final_report.json
```

for the four canonical `(root, model)` pairs listed in §5.7. Intermediate
signed records used: `GATE_2_FOCAL_CALIBRATION`, `GATE_3A_REFERENCE_CALIBRATION`,
`GATE_3B_REFERENCE_SELECTION`, `GATE_3C_IDENTIFICATION`,
`GATE_4_COMPOSED_CONTRAST`, `PREFREEZE_AUDIT`, `GATE_5_FREEZE`,
`CONFIRMATORY_GENERATION`, `MASKED_ANALYSIS`, `UNMASKING`,
`UNMASKED_ANALYSIS`. Every dossier row carries `source_artifact` and
`stage_record_hash`.

**[!] `dci1/evidence/` and `dci1/durable_root/` are gitignored**
(`dci1/.gitignore:4-5`) and **do not survive a clone**. The dossier CSVs,
figure CSVs, `lanes.csv`, `replication_summary.json`, `closure.json` and the
`*_summary.json` rehearsal files are the committed, self-describing extracts.
Releasing the study requires promoting the underlying evidence trees (see the
checklist).

### 9.4 Rebuild commands

```bash
# results dossier (all 28 tables)
python dci1/tools/v7_dossier.py

# Figures 2-4 + Table 1
python dci1/tools/v7_paper_figures.py

# independent numeric audit of the figures and table   (265 checks)
python dci1/tools/v7_paper_figures_check.py

# per-replication summary from signed records only
python3 dci1/tools/v7_replication_summary.py                 # registered study
python3 dci1/tools/v7_replication_summary.py --dev-root <root>  # a rehearsal lane

# study-level closure record
python3 dci1/tools/v7_closure.py [--check]

# registered generation budget, from the code's own constants
python3 dci1/tools/v7_compute_budget.py [--check]

# machine-readable reference design spec (hash-chain-bound: regenerate only
# deliberately, and follow with a §32 chain record)
python3 dci1/tools/v7_reference_design_spec.py

# execution-path audit and producer/consumer contract audit
python3 dci1/tools/v7_execution_path_audit.py --workers 5
python3 dci1/tools/v7_producer_consumer.py
```

### 9.5 Checks that verify generated paper numbers against source records

1. **`v7_dossier.py:596-611`** — the block-level reconstruction (masked rows +
   mask key) must reproduce the signed `UNMASKED_ANALYSIS` point estimates
   exactly (tolerance 1e-12) or the tool aborts. Re-run 2026-08-30: all six
   lanes `verified`.
2. **`v7_paper_figures_check.py`** — **265 checks, all passing** (re-run
   2026-08-30; `paper_figures/README.md` quotes a stale count of 260). Deliberately does
   not import the generator; re-reads the signed `FINAL_REPORT` records,
   re-derives every plotted number, and parses `table1_primary_results.tex`
   back out of LaTeX to compare digit for digit. Also asserts that **no repeat
   lane reached an output**, that every figure carries exactly eight canonical
   configurations, that the vector outputs exist and are non-trivial, and that
   Figure 4 panel A's rows are prompt orders with exactly one
   position-confounded mark per row.
3. **`assert_delta_r_forms`** (`estimators.py:186-192`) — the two algebraic
   forms of Δ_R agree to 1e-9 on every run.
4. **Analysis code hash** sealed at masking and re-verified at unmasking
   (`analysis_run.py:67-75, 998, 1062-1068`).
5. **Verifier hash** re-verified at 18 registered entry points and again after
   each stage's generation (`constants.py:585-593`; `execute.py:482-486`).
6. **Execution-path audit** on `43bb22a`: 80/80 rules reachable, 24 scenarios,
   0 contract defects (`reports/dci1v7/execution_path_audit.{json,md}`;
   `reports/dci1v7/v7_producer_consumer.md`: 172 fields, 0 defects).
7. **Test suites** (`dci1/tests_v7/`, 46 files): fast subset 661 tests,
   synthetic walk 25, D6 branches 4, plus `test_parallel.py`'s byte-identity
   checks against the serial reference path.

### 9.6 Namespaces and their isolation

**[P]** Three (`dci1/src/dci1v7/engine/context.py:49-57`): `registered`
(dci1v7), `synthetic` (stand-in generator and scale knobs permitted), and
`development` (dci1v7-development; real backend, real rules, no knobs, added
2026-08-28). Roots may not overlap, and **four independent mechanisms** keep
development evidence out of the registered tree — a foreign-manifest guard, a
positive admission rule, a study-id check at read time, and a different
signing key per root (`engine/guards.py:56-116`;
`engine/transitions.py:118-137`).

### 9.7 Amendments

| ID | Change | Timing | Direction |
|---|---|---|---|
| A1 | withdraws the absolute composed-headroom criterion as terminal | pre-outcome | loosening |
| A2 | new §13.14 boundary readings | pre-outcome | neutral |
| A3 | §26 restated on the estimand | pre-outcome | neutral |
| A4 | signed append-only post-registration amendment chain | pre-outcome | neutral |
| A5 | withdraws D23, D26; adds D27 | pre-outcome | neutral |
| **A6** | pre-freeze audit *records* §13.15 rather than requiring success; the unregistered `support_satisfied` check withdrawn by name | **post-outcome** | **loosening** |
| **A7** | C1/C3/C5/C6 gate the core arm; C2/C4 gate the spectrum arm only. "No number moves" | **post-outcome** | **loosening** |
| **A8** | D6 means irreversible-and-continue everywhere | **post-outcome** | neutral |

The A6–A8 chain record is signed and self-disclosing
(`evidence/dci1v7/registration/amendments/001_A6_A7_A8.json`): it names the
sections (§12.6, §18, §19, §28.2, §33, §34 — *no* §13), records that all four
replications stood at `PREFREEZE_AUDIT_FAILURE` with 118,176–142,320
pre-freeze rows at adoption, states what would have followed under A6 and A7,
and concludes that "the four v7 terminal reports stand under the rule they
ran". §32.3 is executable: an amendment naming any §13 section is refused once
any replication holds a Gate-2.5 record
(`run/registration_run.py:413-419`).

**[!] The paper needs its own paragraph on this.** The four registered
replications terminated on a pre-freeze check, `support_satisfied`, that **was
never in the preregistration** and contradicted §13.15, §28.2, §18, §26 and D6
(`run/prefreeze_run.py:28-44`). The same unregistered check had ended two v5
and one v6 replication. A6 withdrew it **after the fact**, as a declared
loosening, with outcomes visible.

---

## 10. Evidence status

### 10.1 Development / rehearsal versus the incomplete confirmatory study

| | Registered v7 study | Development rehearsals |
|---|---|---|
| Namespace / study id | `registered` / `dci1v7` | `development` / `dci1v7-development` |
| Roots | `dci1/evidence/dci1v7`, `dci1/durable_root/dci1v7` | `dci1/evidence/dci1v7-development{,-r2..-r5}` |
| Manifest | `969a5b9f…`, commit `ed0446f`, **zero rows at registration** | per-root registration in the development namespace |
| Furthest stage | `GATE_4_COMPOSED_CONTRAST` (all four) | `FINAL_REPORT` (all six) |
| Terminal status | `PREFREEZE_AUDIT_FAILURE` on `support_satisfied` (all four) | none — §26 **MET** on all six |
| Confirmatory rows | **0** | 79,872 or 89,088 per lane |
| Δ_R | **not identified** on any replication (`REFERENCE_SUPPORT_NOT_IDENTIFIED` at Gate 3C) | identified on every lane |
| May a paper claim rest on it? | it is the *protocol* record, not a result | only as **development** evidence, labelled |

`evidence_status` ladder (`dossier/README.md` §0):
`DEV_REHEARSAL_primary` → `DEV_REHEARSAL_secondary` →
`DEV_REHEARSAL_robustness` → `DEV_REHEARSAL_degeneracy_gate` →
`DEV_REHEARSAL_selection_*` (prospective, method description) →
`POST_HOC_diagnostic_licenses_nothing` →
**`NOT_IDENTIFIED_never_a_null`** (never render as zero or as a null).

### 10.2 Canonical versus repeat lanes

**Canonical** is the lane a per-model number must be quoted from — one per
model. **Repeat** lanes are the same model re-run on a later commit and exist
as reproducibility evidence, **never as a second replication**.

| Model | Canonical lane | Repeat lane |
|---|---|---|
| `qwen3-4b` | `dci1v7-development-r3` | `dci1v7-development` |
| `qwen3-4b-instruct-2507` | `dci1v7-development-r4` | — |
| `gemma-3n-e4b-it` | `dci1v7-development-r4` | — |
| `gemma-3n-e2b-it` | `dci1v7-development-r5` | `dci1v7-development-r3` |

A study root binds one registration commit, so each code change after a root's
first registration required a new root (`r3` → `r4` → `r5`); refused attempts
wrote no record. `dci1v7-development-r2` was abandoned at `REGIME_SCREEN` when
a forkserver pool hung and is retained as that record.

The paper's eight canonical configurations = 4 models × 2 prompt orders, 384
topic blocks and M = 8 draws per cell each.

### 10.3 What was unavailable or not identified — never a null

**Twenty-one members are `NOT_IDENTIFIED` on every lane**, 31 distinct members
across 345 rows in `dossier/not_identified.csv`. Recorded with a reason, never
as zero, never as an omission (`run/analysis_run.py:26-30`).

| Control / estimand | Status on every lane | Why |
|---|---|---|
| **Near-form arm** — `Δ_near`, `D(B←N_1..3)`, their vacuity members | `NEAR_FORM_ARM_NOT_AVAILABLE` | fewer than three qualifying Tier-2 families (C8); **the cells were never generated** |
| **Difficulty spectrum** — `δ_difficulty` (+ its two F5 recodings), `β`, `α_1..3`, `γ_tier`, the six spectrum losses `D(B←R_j±)` and their vacuity members | `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` | §12.6 C4 lost on the calibration basis; withheld irreversibly under D6 |
| **Broad-class arm** — `Δ_broad`, `D(B←CL)`, `Ord_CL` | `CLASS_ARM_NOT_AVAILABLE` on **both Qwens** (never generated); available on the Gemmas but permanently carrying `COMPANION_CLASS_NOT_MATCHED` **and** the §6.9(b) difficulty mismatch | Tier-3 budget rung within caliper |
| `Ord_CL` | identified **only** on the two Gemma lanes | class arm |
| **L5** (mechanism, generalisation, class attribution) | **no emitter exists; permanently withheld** | `claims.py:1200-1205` |
| Response length as a mediator | registered, never conditioned on, **not identified** | v5 §22, §29 |
| Joint-success / joint-state panels | **no producer** — registered in §11.5, nothing in the v7 code computes them | `dossier/README.md` §5 |
| Human-judged compliance | **not measured at all** | §7.6 |
| Ablation over K (number of references) | **none** — K = 3 is fixed; Δ_R raises if the count differs | do not describe K as tuned or explored |
| Greedy sensitivity regime | declared, **not run** | `constants.py:145-147` |

**Two of the design's four discriminating controls — the near-form arm and the
difficulty spectrum — were never identified in any lane.** The strong
refutation verdict (D18's precondition) was not reached. Do not present an
unavailable arm as tested, and do not draw an unidentified estimand as zero.

### 10.4 What the rehearsals do support, stated at the right strength

**[D]** From `dossier/estimands_master.csv` and `VALIDITY_AUDIT.md` §1;
canonical lanes, simultaneous 95 % intervals, F1, 384 blocks.

- **Δ_R is never positive at any threshold, in any model, in either
  position.** The registered claim rule returns **L3c in all eight canonical
  cells**, every realised half-width (0.021–0.034) meeting the 0.05
  precondition. L3a (0.10) and L3b (0.25) are nowhere approached.
- In three of the eight cells the interval lies **entirely below zero** →
  `A_COMPARATIVELY_BETTER`, the record's own reading field: the matched
  companions cost B *more* than A does. That is a named §28.1 outcome, **not**
  an absence.
- **[!] Arithmetic compression must be shown, not hidden.** On
  `r3/qwen3-4b` at `outcome_first`, B's compliance is ≈0.90 in *both* composed
  arms, so Δ_R could not have exceeded +0.099 whatever the model did. On
  `r4/qwen3-4b-instruct-2507` at `outcome_first` **both** directions are
  compressed (attainable range [−0.093, +0.099]). Figure 2 draws the hatched
  apron and stop bar for exactly this reason.
- The raw-loss confound the design exists to remove is large and real: for
  `gemma-3n-e2b-it` with B stated second, `D(B←A) = +0.211` while
  `Δ_R = −0.085`.
- **The three references often disagree** (e.g. gemma-e2b, B second:
  Δ_1 = −0.102, Δ_2 = −0.117, Δ_3 = −0.036), which attaches a heterogeneity
  qualifier to L3a/L3b only.

---

## Minimum reproduction recipe

The shortest ordered sequence from a clean environment to the reported numbers.
Steps 1–7 reproduce the study; steps 8–10 reproduce the tables and figures from
evidence you have. Times are the measured wall-clock on the reference host.

```bash
# ---- 0. prerequisites -------------------------------------------------------
#   Linux + ROCm 7.2, 2x AMD RX 7900 XTX (24 GB, gfx1100), >= 24 CPU cores,
#   ~40 GB RAM headroom for the validation suite, uv >= 0.5.3, git.
git clone <repo> dci && cd dci
git checkout 906a88dfb776a384e2aecdea3c78f2b195475f29     # or the release tag

# ---- 1. the two environments -----------------------------------------------
cd dci1 && uv sync                                # scientific: Python 3.13, numpy 2.5.2
cd environments/backend && uv sync && cd ../..    # backend: Python 3.12, vLLM 0.15.1+rocm720
sha256sum -c environments/backend/vendor/MANIFEST.sha256

# ---- 2. model snapshots at the pinned revisions -----------------------------
#   Fetch each of the four repositories at its exact revision into the HF cache
#   (generation runs with HF_HUB_OFFLINE=1, so the snapshot must be local):
#     google/gemma-3n-E2B-it        @ 5e092ebca197cdcd8d8b195040accf22693501bc
#     google/gemma-3n-E4B-it        @ c1221e9c62e34a43ab7ffacd1be0ea71f126ef10
#     Qwen/Qwen3-4B                 @ 1cfa9a7208912126459214e8b04321603b3df60c
#     Qwen/Qwen3-4B-Instruct-2507   @ cdbee75f17c01a7cc42f958dc650907174af0554

# ---- 3. validate the apparatus before spending a GPU-hour (~30 min) ---------
tools/v7_validate.sh 5              # audit + full test suite, parallel
#   expect: 80/80 execution-path rules, 24 scenarios, 0 contract defects;
#           fast subset 661; synthetic walk 25; D6 branches 4; 172 fields, 0 defects

# ---- 4. drive one replication per model, two cards in parallel --------------
#   Registered namespace (the confirmatory study):
tools/run_v7_replication.sh gemma-3n-e2b-it 0 logs/
#   Development rehearsal (what every reported number comes from) — pick a
#   fresh root per code revision; the driver adds --root/--namespace itself:
DCI1_V7_DEV_ROOT=evidence/dci1v7-development-r5 \
  tools/run_v7_replication.sh gemma-3n-e2b-it 0 logs/ &
DCI1_V7_DEV_ROOT=evidence/dci1v7-development-r4 \
  tools/run_v7_replication.sh gemma-3n-e4b-it 1 logs/ &
wait
#   The driver walks all 19 stages in order, holds a per-card lock for every
#   generating stage, and stops at FINAL_REPORT or at a registered terminal
#   status. 4 h 08 m - 14 h per model. DCI1_V7_CPU_WORKERS=N sizes the CPU
#   scoring pools (=1 is the serial reference; changes no recorded value).

# ---- 5. repeat for the other two models -------------------------------------
#   qwen3-4b and qwen3-4b-instruct-2507, same form.

# ---- 6. per-replication summaries from signed records only ------------------
python3 tools/v7_replication_summary.py                       # registered study
python3 tools/v7_replication_summary.py --dev-root evidence/dci1v7-development-r5

# ---- 7. study-level closure (registered study) ------------------------------
python3 tools/v7_closure.py

# ---- 8. results dossier (aborts unless it reproduces the signed estimates) --
cd .. && python dci1/tools/v7_dossier.py

# ---- 9. Figures 2-4 and Table 1 (needs matplotlib >= 3.8) -------------------
python dci1/tools/v7_paper_figures.py

# ---- 10. independent audit of every generated number -----------------------
python dci1/tools/v7_paper_figures_check.py       # 265 checks, all must pass
```

**Reproduce only the analysis, from someone else's evidence trees:** unpack the
released `dci1/evidence/dci1v7-development*` trees into place and run steps 8,
9, 10 alone. That path is exactly reproducible; step 4 is not (§3.5).

---

## Missing reproducibility information

Everything a third party would need that this repository does not record.
Nothing here is guessed.

1. **A confirmatory run.** The registered study has no freeze and no
   confirmatory rows. Any Methods section describing results must either
   describe the development rehearsals **as such**, or wait for a registered
   run under the amended rules.
2. **Host CPU model, RAM, OS distribution and kernel** are not recorded in any
   committed file. `dci1v4/engine/environment.py:53-70` can capture OS and
   kernel; **v7 never calls it**. Only the two GPUs are documented, and only
   in prose.
3. **`environment_digest` is free text** supplied on the command line
   (`"rocm7.2/vllm0.15.1"`), not a computed digest.
4. **`dependency_digest` hashes the lock file's *path string*, not its
   contents** (`freeze_run.py:365-366`). The recorded digest identifies a
   filesystem location.
5. **The backend's measured `HostProfile`** (device names, VRAM, `torch_hip`,
   `vllm_version`, ROCm/HIP environment variables) is produced by
   `vllm_backend/hardware.py` but is not carried into any signed stage record.
6. **The figure environment is unpinned.** `v7_paper_figures.py` needs
   matplotlib, which is in neither `dci1/pyproject.toml` nor
   `dci1/uv.lock`; it resolves through the repository-root venv by accident of
   layout.
7. **No LICENSE file exists at any depth**; no licence identifier is stored for
   any model checkpoint; the topic bank carries authoring rules but no licence
   term. All three are needed for release.
8. **The chance-column decision is open.** Candidate ι is raw solo compliance
   on the executed code while ι_A is chance-corrected (§6.9). The fix touches
   modules that revision V9 pins byte-for-byte, so it is recorded and out of
   force. Settle it before any confirmatory claim about difficulty matching.
9. **Nine documented preregistration inconsistencies** in the v7 → v6 → v5
   chain, including C4's core-versus-spectrum scope, the open-versus-closed
   composed-band notation, and §26's "both splits" versus §13.15's "pooled and
   both splits". Decide which reading the paper reports for each.
10. **Rendered prompts and raw generations are not committed.** Both evidence
    roots are gitignored and do not survive a clone; only the derived dossier
    and figure CSVs are in the repository. Reproducing §10.4's numbers from
    scratch therefore requires either re-running generation or obtaining the
    released evidence trees.
11. **The backend lives outside the governed tree** and is pinned by lock file
    and vendored wheel hash rather than by the signed manifest. State the
    pinning mechanism explicitly rather than implying manifest coverage.
12. **The registered study's `support_satisfied` termination and the
    post-outcome A6–A8 amendments** are fully disclosed in the signed chain
    record; the paper needs its own reviewer-facing paragraph.
13. **The exact HF snapshot bytes** are pinned by revision hash only; no
    per-file checksum of the downloaded weights is stored. A revision that is
    force-pushed or withdrawn upstream is not detectable from these records.

---

## Main-text essentials vs appendix detail

### Must appear in the Methods (main text)

**Evidence status, first.** Registered study = zero confirmatory rows; every
number is development-rehearsal evidence in a separate namespace; four
canonical lanes, one per model; models never pooled.

1. **Models**: the four checkpoints **with revision hashes**, bfloat16, TP=1,
   `max_model_len` 4096, thinking disabled or unavailable per model.
2. **Inference**: vLLM 0.15.1+rocm720; temperature 0.7 / top-p 0.9 / top-k 50;
   cap 512, no stop strings; **no system prompt, single user turn, zero-shot**;
   M = 8 separate requests per prompt.
3. **Design**: 384 topic blocks × 8 draws; both prompt orders in every block;
   configuration = position of the **outcome** constraint; the experimental
   unit is the cell mean over 8 draws, the resampling unit is the block; **no
   exclusions, no retries, no draw selection**.
4. **Prompt template** verbatim, including the byte-identical
   "Answer in 60 to 120 words." stem, and one worked example prompt per cell
   type (solo, B+A, R+B).
5. **A, B and the matched references**: A = exact count of *however*; B = word
   length ≤ m; R_j = the same four templates with the marker substituted;
   n\* and m\* per model.
6. **Matching**: seven structural identity fields; caliper |ι_R − ι_A| ≤ 0.10;
   selection at Gate 3B, **before any composed outcome**; K = 3, distinct
   feature groups, ≥ 2 Tier-1, ≥ 2 discourse roles; deterministic ranking.
   **Plus the chance-basis discrepancy in one sentence** (§6.9a).
7. **The estimand**: Δ_R in the cancelled form, with the statement that the
   solo baseline cancels exactly so no solo ceiling distorts it.
8. **Measurement**: deterministic verifier; word = maximal run of
   Unicode-alphabetic characters; hyphens and apostrophes split; empty answers
   pass a word budget vacuously; truncated answers are scored, not dropped.
   **And the scope sentence: outcomes are verifier-defined and support no
   claim about compliance as a human would judge it.**
9. **Inference**: block bootstrap, 10,000 replicates, studentised
   maximum-modulus simultaneous 95 % intervals over declared families, no
   p-values, thresholds 0.10 / 0.25, precision precondition 0.05 for Δ_R.
   **L3c is an upper bound, not equivalence.**
10. **Not identified**: the near-form arm and the difficulty spectrum were
    unavailable on every lane; the class control carries
    `COMPANION_CLASS_NOT_MATCHED` and was not difficulty-matched. Say this in
    the Methods, not only in Limitations.
11. **Masking**: companion labels permuted before analysis; Δ_R withheld in the
    masked phase; analysis code hash sealed and re-verified.
12. **The A6–A8 paragraph**: what ended the registered study, that the check
    was unregistered, and that the amendment was adopted post-outcome.

### Can move to the appendix

- Full validity components `V_spec … V_diff` with all thresholds (§6.4).
- The complete selection pseudocode and tie-breaking key (§6.5).
- The full reference library taxonomy: 40 families, 674 instruments, tiers,
  ladders, reserves, marker eligibility and the rejection list (§4.5).
- Coverage conditions C1–C8 and the two evaluation bases (§6.8).
- Per-lane selected references with ι, distances and split stability (§6.6).
- The complete estimand catalogue including Ξ, Δ^A, D(R̄←·), F5/F6 members
  (§8.2).
- Boundary readings 1–3 and the Wilson allowance derivation (§8.6).
- The claim ladder L1–L5 with gates and disagreement rules (§8.7).
- Gate 1's ten validation conditions in full, the independent
  reimplementation, the 177-case boundary suite, the 18 adversarial phenomena
  and the six mutation classes (§7.4).
- The İ / U+0130 counting-convention note and the sentence-segmentation
  over-count note (§7.2).
- Seed derivation formulas, root seeds and domain strings (§3.1).
- Wording allocation formula and the orthogonality argument (§5.3).
- Environment: package pins, wheel hashes, the two-interpreter split, the
  known provenance defects (§2).
- All hashes, per-lane commits, freeze/verifier/analysis hashes (§9.1).
- Repeat-lane agreement (`dossier/figA1_repeat_lane_agreement.csv`) and the
  observation that repeats re-selected different reference severities (§6.6).
- Post-hoc diagnostics: projection audit, the raw-coordinate secondary fit,
  `posthoc_confirmatory_difficulty.csv` — each labelled as licensing nothing.
- The broad-class comparison in full, given it is not a main-paper figure.

---

## Artifact-release checklist

### Code

- [ ] `dci1/src/dci1v7/` — protocol, design, stages, verifiers, analysis,
      engine, run layer (the whole study implementation)
- [ ] `dci1/src/dci1v4/` — carried instrument sources
      (`verifiers/words.py`, `target.py`, `statistics.py`), the model registry,
      the topic split, the generation seam (`generation/backend.py`), the
      signing and filesystem engine
- [ ] `exploratory/vllm_backend/` — the serving backend (`__main__.py`,
      `engine.py`, `plan.py`, `contract.py`, `hardware.py`, `resolve.py`,
      `registry.py`, `records.py`, `io.py`), with its README
- [ ] `dci1/tools/v7_*.py` and `dci1/tools/*.sh` — dossier, paper figures,
      figure audit, replication summary, closure, compute budget, reference
      design spec, execution-path audit, producer/consumer audit, the
      replication driver, the validation driver
- [ ] `dci1/tests_v7/` (46 files) + `dci1/conftest.py` — the executable
      safeguards
- [ ] **[!] Add a LICENSE file** (none exists at any depth)

### Task data and prompts

- [ ] `dci1/src/dci1v4/topics/data/topics_v4.json` (624 carried questions)
- [ ] `dci1/src/dci1v7/topics/data/calibration_b_v6.json` (96 authored)
- [ ] `dci1/src/dci1v4/topics/data/sequestered_v4.json`
- [ ] `dci1/src/dci1v7/topics/bank.py`, `topics/calibration_b.py`,
      `dci1/src/dci1v4/topics/split.py` (split algorithm + seed 202608192)
- [ ] `dci1/src/dci1v7/protocol/wordings.py` and
      `dci1/src/dci1v7/verifiers/constraints.py` — every wording variant and
      the whole instrument library
- [ ] A rendered-prompt sample per cell type (the full set is derivable, but a
      sample makes review possible without running code)
- [ ] **[!] A licence term for the topic bank** — authoring rules are recorded,
      a licence is not

### Configs and protocol documents

- [ ] `user-notes/DCI1_preregistration_v7.md` (and the v6/v5 chain it
      incorporates)
- [ ] `dci1/reports/dci1v7/reference_design_spec.json` (hash-bound)
- [ ] `dci1/reports/dci1v7/researcher_decisions.json` (all §34 decisions)
- [ ] `dci1/src/dci1v7/protocol/constants.py` — the single source of every
      threshold, band, grid, cap and count
- [ ] The signed registration manifest and the A6–A8 amendment chain record

### Model revisions

- [ ] The four `(model_id, revision)` pairs of §1.1, quoted in the paper
- [ ] **[!] A licence identifier per checkpoint** (none is stored)
- [ ] Optionally: per-file checksums of the downloaded snapshots, so a
      force-pushed upstream revision is detectable

### Analysis and figure scripts

- [ ] `dci1/tools/v7_dossier.py` (+ the 28 generated tables under
      `dci1/reports/dci1v7/dossier/`)
- [ ] `dci1/tools/v7_paper_figures.py` and `v7_paper_figures_check.py`
      (+ `dci1/reports/dci1v7/paper_figures/`: PDF/SVG/PNG, per-figure CSVs,
      `table1_primary_results.tex`, `captions.md`, the grayscale and
      paper-size accessibility renders)
- [ ] `dci1/reports/dci1v7/METHODS.md`, `VALIDITY_AUDIT.md`, this file,
      `CLOSURE.md`, `READINESS.md`, `development_rehearsal/REHEARSAL.md`,
      `execution_path_audit.{json,md}`, `v7_producer_consumer.md`

### Evidence

- [ ] **[!] Promote the six development-lane evidence trees**
      (`dci1/evidence/dci1v7-development{,-r3,-r4,-r5}`) — currently gitignored
      and lost on clone. Minimum for the paper: the signed `FINAL_REPORT`,
      `UNMASKED_ANALYSIS`, `MASKED_ANALYSIS`, `UNMASKING`, `GATE_5_FREEZE`,
      `GATE_3B_REFERENCE_SELECTION`, `GATE_3C_IDENTIFICATION` and
      `GATE_2_FOCAL_CALIBRATION` records per canonical lane
- [ ] The four registered-study terminal reports under `dci1/evidence/dci1v7/`
- [ ] Raw `rows.jsonl` for at least the canonical confirmatory stages, so a
      third party can re-verify verdicts from text without a GPU
- [ ] The signing public material needed to verify the records (documenting
      that per-root keys differ)

### Environment files

- [ ] `dci1/pyproject.toml`, `dci1/uv.lock`, `dci1/requirements-frozen.txt`
- [ ] `dci1/environments/backend/pyproject.toml`,
      `environments/backend/uv.lock`
- [ ] `dci1/environments/backend/vendor/MANIFEST.sha256` **and the two vendored
      wheels** (vLLM 0.15.1+rocm720, amdsmi 26.2.1) — or a documented mirror
- [ ] **[!] A pinned figure environment** (matplotlib) — add it to
      `dci1/pyproject.toml` as an optional group, or ship a separate
      `figures/pyproject.toml` + lock
- [ ] The exact `uv sync` commands and the required host ROCm version

### README

- [ ] A top-level artifact README stating, in this order: (1) the registered
      study produced zero confirmatory rows; (2) every number is
      development-rehearsal evidence; (3) which lane is canonical per model;
      (4) the two-interpreter build; (5) the minimum reproduction recipe of
      this document; (6) which analyses were never identified and must not be
      read as nulls; (7) the chance-column discrepancy and the post-outcome
      A6–A8 amendments; (8) that no human evaluation exists.
