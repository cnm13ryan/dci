# vLLM TP=2 cross-model retry — decisions

Prospective record for the `VLLM_TP2_CROSS_MODEL` experiment. Every entry below
was written before the corresponding estimate existed; **V9 in particular fixes
the k=5 extension rule before any k=3 generation ran**, which is the whole point
of writing it down.

This experiment is labelled `VLLM_TP2_CROSS_MODEL` throughout. The earlier
experiment is `TRANSFORMERS_CROSS_MODEL`. They are different execution
conditions and their artefacts must never be merged.

---

## V1 — Correction: vLLM was on this machine all along

The previous run's decision **D2** asserted that "vLLM is **not installed
anywhere on this machine** — no package in any environment on the host, and no
ROCm build present." **That was wrong**, and the whole Transformers execution
condition rested on it.

vLLM was present in at least four places:

* `/home/cnm13ryan/git/inoculation-prompting/gcd_sycophancy/.venv/` — an
  installed `vllm 0.15.1+rocm720`;
* `/home/cnm13ryan/git/inoculation-prompting/gcd_sycophancy/vendor/vllm-0.15.1+rocm720-cp312-cp312-linux_x86_64.whl`
  — the vendored wheel it was installed from;
* four copies in the uv archive cache;
* `/home/cnm13ryan/git/vllm` — a source checkout at `v0.18.1rc0-23-ge74c17e15`.

The search that missed it was `find / -maxdepth 8 -name vllm -type d -path
"*site-packages*"`. The installed copy sits at depth 9. A negative result from a
depth-limited search was reported as "not present anywhere".

The Transformers cross-model results remain valid **as a description of that
execution condition**; what was wrong was the stated reason for choosing it.

---

## V2 — vLLM 0.27.1+rocm723, because it is the only build that carries all five

Qualification came before model generation, as required.

| build | Qwen3.5 | Gemma 4 | Kimi-VL | source |
|---|---|---|---|---|
| `0.15.1+rocm720` (installed, vendored) | ✘ | ✘ | ✔ | local wheel |
| `v0.18.1rc0-23-ge74c17e15` (source checkout, 2026-03-22) | ✔ | ✘ | ✔ | `/home/cnm13ryan/git/vllm` |
| **`0.27.1+rocm723`** | **✔** | **✔** | **✔** | `wheels.vllm.ai/rocm/` |

Checked by reading `vllm/model_executor/models/registry.py` out of each build,
not by assumption. The canonical run's own 0.15.1 recognises only
`KimiVLForConditionalGeneration`; it cannot serve as the common backend, so
"reuse the version the canonical run used" was not available.

`0.27.1+rocm723` is built from vLLM commit
`6e448d0ea9bf3d88d898b65449ca6dc2aec170ac`. Its compiled kernels contain
**gfx1100** code objects (checked directly in `_C.abi3.so`,
`_C_stable_libtorch.abi3.so`, `_moe_C_stable_libtorch.abi3.so`), so this host is
a supported target rather than a hopeful one.

**One build for all five checkpoints**, so backend, backend version and
distributed runtime are fixed across the comparison.

---

## V3 — A separate backend environment, and design-in / rows-out

vLLM 0.27.1 requires `torch==2.11.0+gitd0c8b1f`; the scientific environment pins
`torch==2.9.1+rocm7.2.0`. They cannot share a virtualenv.

So generation runs in `exploratory/.venv-vllm` and everything scientific stays in
`exploratory/.venv`. This is the repository's existing pattern, not an
invention: `vllm_backend/natural_reasoning.py` already states "generation
happened in the ROCm vLLM environment; scoring happens here".

`crossmodel/vllm_tp2.py` imports nothing from `crossmodel` or `dci`. It reads a
plan and a design and writes raw rows; `xm_vllm_ingest.py` rebuilds canonical
rows through `crossmodel.schema.build_row` in the scientific environment, so
`schema.py` remains the single authority on what a stored row is and the vLLM
rows are the same shape as the Transformers rows.

**Installation trap, recorded because it silently corrupted the first attempt.**
Running `uv pip install` from inside `exploratory/` applies that project's
`[tool.uv] override-dependencies`, which pins torch to the Radeon 2.9.1 wheel.
The vLLM wheel installed happily against the wrong torch and failed at import
with `undefined symbol: torch_call_dispatcher` — the same class of ABI break the
`vendor/README.md` documents. The fix is `uv pip install --no-config` from
outside the project. Reproduce with:

    uv venv --python 3.12 exploratory/.venv-vllm
    uv pip install --no-config --python exploratory/.venv-vllm/bin/python \
        <vllm-0.27.1+rocm723 wheel> \
        --extra-index-url https://wheels.vllm.ai/rocm/ \
        --index-strategy unsafe-best-match
    uv pip install --no-config --python exploratory/.venv-vllm/bin/python \
        torch==2.11.0+gitd0c8b1f triton==3.6.0 \
        torchvision==0.24.1+d801a34 torchaudio==2.9.0+eaa9e4e \
        --extra-index-url https://wheels.vllm.ai/rocm/ \
        --index-strategy unsafe-best-match

---

## V4 — TP=2 for every checkpoint, with the machine's known ROCm mitigations

`tensor_parallel_size=2` for all five, BF16, no exceptions. A checkpoint that
cannot run this way is `TP2_BACKEND_BLOCKED`; there is no fallback to
Transformers inside the scientific run.

Mitigations carried over from this machine's previously working TP=2 runs and
**verified to still exist in 0.27.1** rather than dropped because an API moved:

* `disable_custom_all_reduce=True` — still a real engine argument
  (`vllm/config/parallel.py`, `vllm/engine/arg_utils.py`, `vllm/entrypoints/llm.py`).
* `NCCL_P2P_DISABLE=1` in the environment.

**Both cards must hold model state.** `torch.cuda.memory_allocated` sees only
the calling process, and vLLM runs one worker process per rank, so TP sharding
is verified through `rocm-smi` — the only view that sees every worker. A run
where rank 0 holds the weights and rank 1 is idle is not tensor parallelism and
is not admitted.

---

## V5 — One uninterrupted generation; the splice is not reintroduced

No stop string, no two-phase splice, no forced close. Reasoning and answer share
one budget and the model closes its own reasoning.

The previous attempt's splice produced a documented artefact: when the ceiling
cut a trace short, the model continued thinking into the answer phase, emitted a
**second** close marker, and re-answered, putting `</think>` and a duplicated
answer into the scored channel. This experiment is about *natural* reasoning, so
that mechanism is gone entirely and `forced_close_artefact` is structurally
False for every vLLM row.

The cost, recorded rather than hidden: the 512-token answer allowance is no
longer separately enforced. The budget is `engineering_ceiling + 512` for the
whole response, and truncation is measured.

---

## V6 — Native thinking is requested explicitly, never defaulted

| checkpoint | switch | parser |
|---|---|---|
| `Qwen/Qwen3.5-4B`, `Qwen/Qwen3.5-9B` | `enable_thinking=True` | vLLM `qwen3` |
| `google/gemma-4-E4B-it`, `google/gemma-4-12B-it` | `enable_thinking=True` | vLLM `gemma4` |
| `moonshotai/Kimi-VL-A3B-Thinking-2506` | none — always thinks | `◁think▷ … ◁/think▷` |

Gemma 4's template defaults thinking **off**
(`enable_thinking | default(false)`), so relying on a backend default would have
silently run the wrong condition. It is passed explicitly for every request.

vLLM 0.27.1 registers `qwen3` and `gemma4` reasoning parsers and **none for
Kimi-VL** — its `kimi_k2` / `kimi_k3` entries are the K-series text models, not
this vision-language checkpoint. Kimi therefore uses the delimiters its own
model card documents, with one deliberate difference from the card's reference
implementation: where the card returns the whole text as the summary when no
marker is present, this returns an empty answer, because a scored scratchpad is
worse than a missing datum.

No no-thinking arm is run in this retry, and none is invented for Kimi.

---

## V7 — The decoder is the canonical one, verified against the artefact

`temperature = 0.7`, `top_p = 0.9`, `top_k` disabled, single sequence, no beams.

Read from the canonical run's own generator, `vllm_backend/natural_reasoning.py`:
`SamplingParams(temperature=0.7, top_p=0.9, ...)`. The brief for this retry said
"approximately … top_p = 0.95" and instructed that the exact value be verified
from the artefacts; the artefact says **0.9**, so 0.9 is used.

`top_k` is passed as `-1` to vLLM, which disables it. The canonical run left it
unset. (Transformers defaults it to 50, which is why the previous experiment had
to disable it explicitly; vLLM does not have that default.)

No speculative decoding, no draft model, no MTP, no best-of, no penalties.

---

## V8 — The engineering ceiling is a guard, never a dose

`reasoning_mode = NATURAL_REASONING` carries `assigned_reasoning_budget = None`
by construction. The ceiling is recorded separately as `engineering_ceiling`,
and realised length as `reasoning_tokens`.

`max_model_len` is **not** the advertised context. Qwen3.5 and gemma-4-12B
advertise 262,144; allocating that as KV on two 24 GiB cards would be a guess
dressed as a limit. The envelope starts at 40,960 and is raised only on measured
evidence from calibration.

---

## V9 — The k=5 extension rule, FROZEN BEFORE ANY k=3 GENERATION

The previous experiment found nine of ten model × background cells with zero
target failure in **both** arms, where τ = 0 is arithmetic rather than a finding.
This retry therefore fixes the extension rule in advance so it cannot be chosen
after seeing which way τ pointed.

**Rule.** For a checkpoint m and background c at k = 3, classify the cell:

    TARGET_CEILING   if P(F_A=1 | B) <= 0.02 AND P(F_A=1 | R) <= 0.02
    TARGET_FLOOR     if P(F_A=1 | B) >= 0.98 AND P(F_A=1 | R) >= 0.98
    ESTIMABLE        otherwise

**Threshold: 0.02**, on both arms, in the same cell.

**Trigger.** Any checkpoint with at least one `TARGET_CEILING` cell at k = 3 is
rerun at k = 5.

The rule depends only on whether the primary outcome has measurement headroom.
It does **not** depend on the sign, size, or interest of τ, and it is not
conditioned on Δ_semicolon at all.

**k = 5 is the repository's existing construction, not new difficulty.** Taken
verbatim from `runs/stageS27_reasoning_k5_20260811T155951Z/config.json`:

    --target A --focal B --arms C_L3
    --background X_SEMICOLON_FREE,X_ELLIPSIS_FREE,X_PAREN_FREE --load 5
    --permute QAC --fixed-tail U_LEX_FORBID3,U_NUM_MAXINT
    --tasks 20 --replicates 2

i.e. the same QAC focal/reference contrast under the same two backgrounds, with
`U_LEX_FORBID3` and `U_NUM_MAXINT` pinned in a fixed tail position so that
raising the load does not also permute instructions the design is not studying.

---

## V10 — Uncertainty is unchanged

The repository's paired task-cluster bootstrap, **4,000 draws**
(`dci_exploratory.plotstyle.BOOTSTRAP_DRAWS`), 2.5/97.5 percentiles, task as the
resampling cluster, focal/reference pairing preserved. Not changed to 10,000:
that number appears in briefs, not in the implementation, and changing it would
make these intervals incomparable with every existing figure.

---

## V11 — Joint satisfaction is prespecified here

In the previous experiment `Δ_J` was introduced *after* seeing τ degenerate, and
was labelled exploratory for that reason. In this retry it is **prespecified**,
because target saturation is now a known property of these checkpoints rather
than a surprise:

    J(m,c,k) = P(A and B both satisfied | focal arm, m, c, k)
    Δ_J(m,k) = J(semicolon) − J(control)

It is a secondary outcome and does not replace τ. Both are always reported.

---

## V12 — Gemma 4 is TP2_BACKEND_BLOCKED, and the override is refused on evidence

**Recorded 2026-08-12, from the Stage A gate, before any Gemma 4 vLLM
generation.**

Both `google/gemma-4-E4B-it` and `google/gemma-4-12B-it` fail identically at
engine construction under vLLM 0.27.1+rocm723:

    vllm/transformers_utils/model_arch_config_convertor.py, get_head_size():
        head_dim = getattr(self.hf_text_config, "head_dim", 0)
    transformers.integrations.heterogeneity.configuration_utils
        .AmbiguousGlobalPerLayerAttributeError:
        'head_dim' is a per-layer attribute and may vary across layers.

vLLM's config converter asks for one global `head_dim`; transformers 5.15
refuses to answer for a heterogeneous config. This is an integration gap between
those two versions for the Gemma 4 family. It is **not** capacity, **not**
gfx1100, **not** tensor parallelism, and it is not the single-card OOM that
blocked the 12B under Transformers.

**The documented override was considered and refused.** The exception names an
escape hatch — `allow_global_per_layer_attribute_access=True` — and warns it is
safe only "if the caller can safely handle heterogeneous configs". So the
configs were inspected directly:

| checkpoint | layers | distinct `head_dim` | distinct `num_key_value_heads` |
|---|---|---|---|
| `gemma-4-E4B-it` | 42 | **256 and 512** | 2 |
| `gemma-4-12B-it` | 48 | **256 and 512** | **1 and 8** |

These checkpoints are genuinely heterogeneous. Forcing the global read would
build roughly half the layers with the wrong head size — a model that loads,
generates fluently, and is wrong. That is the same class of silent corruption
the previous experiment caught when a mismatched Gemma class loaded with
randomly initialised weights, and the weight-integrity gate would very likely
not catch it, because attention with a wrong head_dim can still produce
plausible text.

The transformers error is protective and correct. Gemma 4 is recorded
`TP2_BACKEND_BLOCKED` under this build.

**Consequence for the retry's purpose.** The backend confound cannot be removed
for Gemma 4 on this host: there is no build that runs Gemma 4 under vLLM here,
and the Transformers condition is the only one in which these checkpoints have
ever generated. Their Transformers results are not superseded — they are the
only measurement that exists.

---

## V13 — Kimi-VL is capacity-blocked at the first envelope, and gets a measured retry

**Recorded 2026-08-12, Stage A.**

`moonshotai/Kimi-VL-A3B-Thinking-2506` loads under vLLM 0.27.1 — the
Transformers blocker (`is_torch_fx_available`, decision D21) is **gone**, which
answers the retry's Kimi question at the architecture level. It then fails on
memory:

    Checkpoint size: 30.56 GiB
    Worker_TP1: CUDA out of memory. Tried to allocate 374.00 MiB.
    GPU 1 has 23.98 GiB total, 146.00 MiB free;
    15.44 GiB allocated by PyTorch.

Weights shard to ~15.3 GiB per card, so the weights themselves fit; the failure
is in what is left for activations and cache at
`max_model_len=40960, gpu_memory_utilization=0.85`.

Per the "measure first, do not inflate context" rule, the retry lowers the
envelope rather than reaching for quantization: BF16 is unchanged and no
quantized variant is substituted. If a modest envelope still cannot hold the
model, the checkpoint is `TP2_CAPACITY_BLOCKED` and that is the result.
