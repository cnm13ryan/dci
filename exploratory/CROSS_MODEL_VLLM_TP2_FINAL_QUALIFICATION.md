# vLLM TP=2 final qualification — five checkpoints

Recorded 2026-08-12 08:10 UTC. Machine-readable twin:
`CROSS_MODEL_VLLM_TP2_FINAL_QUALIFICATION.json`.

Fixed condition: vLLM 0.27.1+rocm723, BF16, `tensor_parallel_size=2`,
2 × RX 7900 XTX (gfx1100), `disable_custom_all_reduce=True`,
`NCCL_P2P_DISABLE=1`, native thinking enabled, no quantization.

**Result: 0/5 `TP2_THINKING_VALID`.**

| model | loads TP=2 | BF16 | thinking enabled | DCI-shaped closure | parser valid | final status |
|---|---|---|---|---|---|---|
| `Qwen3.5-4B` | yes | yes | yes | — | yes | **TP2_REASONING_UNCLOSED** |
| `Qwen3.5-9B` | yes | yes | yes | — | yes | **TP2_DCI_SHAPED_NOT_MEASURED** |
| `gemma-4-E4B-it` | **no** | yes | **no** | — | — | **TP2_BACKEND_BLOCKED** |
| `gemma-4-12B-it` | **no** | yes | **no** | — | — | **TP2_BACKEND_BLOCKED** |
| `Kimi-VL-A3B-Thinking-2506` | **no** | yes | — | — | — | **TP2_CAPACITY_BLOCKED** |

## Evidence

* **Qwen3.5-4B** — loads and parses, but 1/8 composed-constraint smoke prompts ran to the ceiling without closing
  * simple smoke: 7/8 answers, 7/8 closed, weights 4/4
* **Qwen3.5-9B** — simple smoke passed; the DCI-shaped probe did not complete, so DCI-shaped closure is UNMEASURED — not a closure failure and not a pass
  * simple smoke: 8/8 answers, 8/8 closed, weights 4/4
* **gemma-4-E4B-it** — engine cannot build the model; see execution matrix for the exception
* **gemma-4-12B-it** — engine cannot build the model; see execution matrix for the exception
* **Kimi-VL-A3B-Thinking-2506** — BF16 weights did not load in 6 tested envelope(s); failure is at weight load, not KV

## Gate

The DCI k=3 slice runs only at 5/5. Anything less means at least one
checkpoint would enter the comparison under a different execution
condition from the others, which is the confound this whole retry
exists to remove.

## Diagnostics behind each status

### Gemma 4 (both) — needs a vLLM newer than 0.27.1, not a local patch

The installed 0.27.1 converter has **no per-layer config machinery at all** —
no `per_layer_config`, no `get_per_layer_hf_configs`, no `config_het`. Upstream
`main` has all three, and its `get_head_size` is guarded accordingly. So the
proper fix already exists upstream, and the ROCm rolling index
(`wheels.vllm.ai/rocm/`) still publishes only `0.27.1+rocm723`
(commit `6e448d0ea`).

Backporting is **not** a small patch: per-layer `head_dim` implies per-layer KV
cache specs, per-layer attention construction and backend support. Attempting it
here would risk silently building the wrong architecture — the failure mode this
gate exists to prevent. The override
`allow_global_per_layer_attribute_access=True` remains refused: `head_dim` is
genuinely {256, 512} across layers, and 12B also varies `num_key_value_heads`
{1, 8}.

**What would fix it:** a ROCm gfx1100 build of vLLM at a commit containing the
heterogeneous-config subsystem. That is a source build, not a setting.

### Kimi-VL — capacity, measured across a 6-point grid

| `max_model_len` | 0.85 | 0.92 |
|---|---|---|
| 32,768 | fail | fail |
| 16,384 | fail | fail |
| 8,192 | fail | fail |

Every attempt started from genuinely free cards (23.95 / 23.94 GiB), so this is
not contamination from a previous engine. The failure is at **weight load**, not
KV allocation, which is why shrinking the envelope does not move it:

    Checkpoint size 30.56 GiB; Worker_TP1 OOM allocating 374 MiB;
    15.44 GiB allocated by PyTorch, 164 MiB free of 23.98 GiB.

About 8 GiB per card is held outside PyTorch's allocator during load. BF16 was
not abandoned for a quantized variant, which would be a different numerical
experiment.

### Qwen3.5 — the reasoning interface is correct; the reasoning does not stop

The single-request probe (**concurrency 1**, so head-of-line blocking is ruled
out by construction) verified the interface directly:

| check | result |
|---|---|
| `enable_thinking=True` prompt tail | `<\|im_start\|>assistant\n<think>\n` |
| `enable_thinking=False` prompt tail | `<think>\n\n</think>\n\n` |
| template actually differs | **true** |
| `<think>` / `</think>` token ids | 248068 / 248069 (single tokens) |
| eos token id | 248046 |
| reasoning parser | `qwen3` |

So the template is right, thinking is genuinely on, the close marker is a single
token vLLM can stop on, and the parser is the documented one. **None of the
candidate mechanical causes survives**: not a chat-template mismatch, not
stop-token handling, not parser misconfiguration, not batch scheduling.

The first DCI-shaped request then ran past 25 minutes at concurrency 1 without
emitting `</think>`, and was stopped. Combined with Stage A — where the same
checkpoints closed 8/8 *simple* prompts — the remaining explanation is that
Qwen3.5 does not terminate its reasoning on composed-constraint prompts within
any envelope this hardware can serve.

`Qwen3.5-9B` is recorded `TP2_DCI_SHAPED_NOT_MEASURED` rather than
`TP2_REASONING_UNCLOSED`: its DCI-shaped probe never ran, and an unmeasured cell
is not a failed one.

**What would fix it:** nothing about capacity or configuration. Either a
declared `LIMITED_REASONING` treatment (a different experiment, requiring its own
answer-legitimacy validation) or these checkpoints are reported as having no
establishable natural-reasoning condition on this hardware.
