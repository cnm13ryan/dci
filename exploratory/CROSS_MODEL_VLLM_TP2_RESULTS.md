# vLLM TP=2 cross-model retry — results

**Experiment `VLLM_TP2_CROSS_MODEL`.** Status: exploratory. Companion documents:
`CROSS_MODEL_VLLM_TP2_EXECUTION_MATRIX.md` (admission),
`CROSS_MODEL_VLLM_DECISIONS.md` (V1–V14, prospective),
`CROSS_MODEL_VLLM_BACKEND_COMPARISON.md` (against the Transformers condition).

The earlier experiment is `TRANSFORMERS_CROSS_MODEL`. Its artefacts are
unchanged and must not be merged with these.

---

## 1. What this retry set out to do, and what it found

It set out to remove the Transformers-versus-vLLM backend confound by running
all five checkpoints through one BF16 vLLM engine with
`tensor_parallel_size=2`, native thinking enabled.

**The infrastructure worked. The result is that the confound cannot be removed
on this host.** Zero of five checkpoints reached the k=3 scientific slice, for
three distinct and separately evidenced reasons. No k=3 or k=5 generations
exist under this condition, so there are no τ, Δ_semicolon, four-state or joint
estimates to report.

That is a finding about the available software and hardware, not about the
models. It is stated first because every other sentence here depends on it.

---

## 2. The backend was qualified before anything was generated

| | |
|---|---|
| build | **vLLM 0.27.1+rocm723**, wheel `vllm-0.27.1+rocm723-cp312-cp312-manylinux_2_34_x86_64` |
| vLLM commit | `6e448d0ea9bf3d88d898b65449ca6dc2aec170ac` |
| torch | `2.11.0+gitd0c8b1f`, HIP 7.2.53211 |
| transformers | 5.15.0 |
| GPUs | 2 × AMD Radeon RX 7900 XTX, **gfx1100**, 23.98 GiB each; iGPU excluded |
| ROCm | 7.2.0 host; wheel built for 7.2.3 |
| dtype | bfloat16, no quantization anywhere |
| TP | `tensor_parallel_size=2`, `disable_custom_all_reduce=True`, `NCCL_P2P_DISABLE=1` |

**Version selection was forced, not chosen.** Reading each build's own
`registry.py`: the canonical run's `0.15.1+rocm720` carries only Kimi-VL; the
local source checkout `v0.18.1rc0` (2026-03-22) adds Qwen3.5 but predates Gemma
4; `0.27.1+rocm723` carries all five. Its compiled kernels contain **gfx1100**
code objects, checked directly in `_C.abi3.so`.

**TP=2 genuinely shards.** On both Qwen checkpoints the engine ran as an
`VLLM::EngineCore` plus **two** `VLLM::Worker_TP0/1` processes, with `rocm-smi`
showing **both cards at ~85–89 % VRAM and ~100 % utilisation** during
generation. This is the check that distinguishes tensor parallelism from a
single-GPU run wearing a TP label, and it passed.

---

## 3. Why each checkpoint did not reach the slice

### Gemma 4 — both checkpoints — `TP2_BACKEND_BLOCKED`

    vllm/transformers_utils/model_arch_config_convertor.py, get_head_size():
        head_dim = getattr(self.hf_text_config, "head_dim", 0)
    AmbiguousGlobalPerLayerAttributeError:
        'head_dim' is a per-layer attribute and may vary across layers.

vLLM asks for one global `head_dim`; transformers 5.15 refuses to answer for a
heterogeneous config. The exception documents an override
(`allow_global_per_layer_attribute_access=True`) and **it was refused on
evidence**, because the configs really are heterogeneous:

| checkpoint | layers | distinct `head_dim` | distinct `num_key_value_heads` |
|---|---|---|---|
| `gemma-4-E4B-it` | 42 | **256 and 512** | 2 |
| `gemma-4-12B-it` | 48 | **256 and 512** | **1 and 8** |

Forcing the global read would build roughly half the layers with the wrong head
size. The model would load and generate fluently and be wrong, and unlike a
randomly-initialised load it would very likely pass a coherence gate. This is
an integration gap between these two versions — not capacity, not gfx1100, not
TP.

### Kimi-VL-A3B-Thinking-2506 — `TP2_CAPACITY_BLOCKED`

**The previous Transformers blocker is gone.** Decision D21 recorded Kimi as
`BACKEND_BLOCKED` because its remote code imports `is_torch_fx_available`,
removed in transformers 5.x. Under vLLM that code is not used at all: vLLM has
its own `kimi_vl` implementation and the architecture is recognised. The
checkpoint got past architecture selection and into weight loading.

It then ran out of memory:

    Checkpoint size: 30.56 GiB
    Worker_TP1: CUDA out of memory, tried to allocate 374.00 MiB;
    GPU 1 has 23.98 GiB total, 146.00 MiB free, 15.44 GiB allocated by PyTorch.

Weights shard to ~15.3 GiB per card, so the weights themselves fit; what did not
fit was the rest at `max_model_len=40960, gpu_memory_utilization=0.85`. BF16 was
not abandoned for a quantized variant — the dual-GPU condition exists to supply
capacity, and a quantized run is a different numerical experiment.

### Qwen3.5 — both checkpoints — natural reasoning does not close on DCI prompts

Stage A, on **simple** prompts, is clean for both:

| checkpoint | envelope | answers | reasoning emitted | closed | cap hits | weight integrity | marker leak | control residue | median tokens | max |
|---|---|---|---|---|---|---|---|---|---|---|
| `Qwen3.5-9B` | 40,960 | 8/8 | 8 | **8** | **0** | 4/4 | 0 | 0 | 1,257 | 5,391 |
| `Qwen3.5-4B` | 8,192 | 8/8 | 8 | 7 | 1 | 4/4 | 0 | 0 | 1,247 | 7,680 |

The vLLM `qwen3` parser separated reasoning from answer cleanly on every row,
the template pre-opened `<think>` with `enable_thinking=True`, and both models
answered every trivial question correctly.

**On composed-constraint prompts the picture reverses.** Qwen3.5-4B was re-run
at the 40,960 envelope and two of its eight prompts had still not closed after
roughly 45 minutes of generation, each consuming the full 40,448-token budget;
the run was stopped. This is the repository's existing finding **I21** —
*"Qwen3.5-4B does not terminate its reasoning within any budget this hardware
affords"* — reproduced under a different backend, with tensor-parallel headroom,
and on the actual DCI prompt shape.

**Qwen3.5-9B Stage B, on DCI-shaped prompts, shows the same split.** The pilot
(3 disjoint calibration tasks x 2 arms x 2 backgrounds x 2 replicates = 24 rows,
ceiling 39,321) was stopped after **6 of 24 rows had completed in 4m26s while
the remaining 18 were still generating** at a measured ~76 tok/s aggregate.
Finishing would have required roughly a further 2.5 hours for those 18 rows
alone. So a minority of DCI rows close quickly and the majority run to the
ceiling, and no complete pilot exists.

That is a partial measurement and is reported as one: it is **not** a cap-hit
rate, and the run directory holds no `generations.jsonl`. What it establishes is
weaker and still decisive for admission — natural reasoning could not be
established for this checkpoint within a feasible wall-clock envelope on this
host.

The gap between the simple-prompt table and this one is exactly why calibration
must use DCI-shaped prompts: a smoke set of trivial questions certified
Qwen3.5-9B as closing 8/8 naturally, and on the real prompt shape most rows do
not close at all.

---

## 4. There are no behavioural results, and none may be inferred

No k=3 or k=5 generation exists under `VLLM_TP2_CROSS_MODEL`. Therefore:

* no τ, no Δ_semicolon, no four-state distribution, no Δ_J;
* **no statement of the form "under vLLM TP=2, checkpoint X shows/does not show
  DCI"** is available for any checkpoint;
* the previous experiment's conclusions are **not** superseded, revised or
  confirmed by this retry. For Gemma 4 the Transformers condition remains the
  only one in which these checkpoints have ever generated DCI rows.

A technical failure is not a behavioural result. Three different technical
failures are not three nulls.

---

## 5. What the retry does establish

1. **vLLM TP=2 works on 2 × RX 7900 XTX under ROCm 7.2** with the machine's
   known mitigations, verified by two worker processes and both cards loaded.
2. **A single build covering all five architectures exists** (0.27.1+rocm723)
   and was found, installed and qualified. The blockers are per-family
   integration and capacity limits inside that build, not the absence of one.
3. **Kimi-VL's Transformers blocker is removed by vLLM**, moving it from
   "architecture unsupported" to "does not fit at this envelope" — a different
   and more tractable problem.
4. **Qwen3.5's non-termination is backend-independent.** It was previously
   observed under capped budgets on Transformers; it reproduces under vLLM with
   TP=2 headroom and a ~39.3K ceiling on DCI-shaped prompts.
5. **No single execution condition on this host covers all five checkpoints.**
   Transformers runs Gemma 4 and not Kimi; vLLM runs Kimi's architecture and not
   Gemma 4; neither establishes Qwen3.5 natural reasoning. Removing the backend
   confound for one family introduces it for another.

---

## 6. What would change this

* **Gemma 4** — a vLLM revision whose config converter reads `head_dim`
  per layer, or a transformers version whose heterogeneity guard vLLM's
  converter predates. Neither is a setting; both are version work.
* **Kimi-VL** — a smaller `max_model_len` and a higher
  `gpu_memory_utilization` are the measured next step, still BF16 and still
  TP=2. This is the cheapest remaining path to any vLLM TP=2 scientific data.
* **Qwen3.5** — nothing about capacity. The checkpoint does not stop on these
  prompts; a larger ceiling makes the run longer, not more natural, and TP=2
  headroom did not change that. Either the condition is redefined (a declared
  LIMITED_REASONING treatment, which is a different experiment and would have to
  be validated for answer legitimacy first) or these checkpoints are reported as
  having no establishable natural-reasoning condition on this hardware.

  A 160-row k=3 slice at the observed rate would need on the order of a day per
  checkpoint, most of it spent generating reasoning that never terminates. That
  is the practical reason the slice was not attempted, and it is downstream of
  the scientific reason: a condition whose ceiling binds on most rows is not
  natural reasoning.
