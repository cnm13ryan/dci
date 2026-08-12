# Frozen Kimi-VL execution environment

The exact stack that passed qualification on 2026-08-12
(`runs/xmq_kimi_c/qualification.json`, verdict `QUALIFIED`, 8/8 reproducible).
Rebuild it from `kimi-env.lock.txt`; do not upgrade it to make something else
convenient.

## Why this is a separate environment

`config.json` for `moonshotai/Kimi-VL-A3B-Thinking-2506` declares
`transformers_version: 4.50.3`. The scientific environment runs 5.15.0, which
the other four checkpoints require, and three separate incompatibilities appear
between the checkpoint's own modeling code and 5.15.0:

| symptom on transformers 5.15.0 | on 4.50.3 |
|---|---|
| `is_torch_fx_available` removed; imported at module top level | present |
| `rope_scaling: null` synthesised into `{rope_type: 'default'}`; the code tests `is None` and takes the scaled branch | loads as `None` |
| `tie_weights(recompute_mapping=False)`; the method takes no arguments | signature is `(self)` |

Each was shimmed once. Running the checkpoint on the version it was published
against removes all three instead of accumulating a fourth, and the backend
records `compatibility_shims_applied: []` and `rope_scaling_as_loaded: null` as
evidence rather than as an assertion.

## The frozen stack

```
transformers  4.50.3
torch         2.9.1+rocm7.2.0.lw.git7e1940d4   (repo.radeon.com ROCm 7.2 wheel)
triton        3.5.1+rocm7.2.0.gita272dfa8      (same index; torch pins it exactly)
tokenizers    0.21.4
accelerate    1.14.0
tiktoken      0.13.0     blobfile 3.2.0        (the checkpoint's own tokenizer)
safetensors   0.8.0      numpy 2.5.2
```

The torch wheel is byte-identical to the one the scientific environment uses, so
the GPU stack is not a cross-model confound; only the transformers version
differs, and it differs because the checkpoint says so.

## Validated execution configuration

```
device_map          auto
max_memory_per_gpu  19GiB
batch_size          2
dtype               bfloat16
quantization        none
attn_implementation eager
generation ceiling  8192 tokens/request  (THINKING_ENABLED_BOUNDED)
```

Measured at qualification: weights **13.60 GiB on cuda:0, 16.97 GiB on cuda:1**,
30.56 GiB total, **nothing on meta/cpu/disk**, 5.67 / 9.75 GiB free per card
after load. One request 20.1 s; 8 rows at batch 2 in 689 s (0.70 rows/min);
repeat run 8/8 byte-identical.

**Do not lower the cap to 16 GiB** — 1.71 GiB then lands on the meta device and
streams from disk, which is a different execution condition and unusably slow.
The backend refuses to proceed if any parameter is placed off-GPU.

**Do not use the vLLM route.** vLLM TP=2 in BF16 without CPU offload does not fit
this checkpoint: six clean attempts (three context lengths × two utilisations,
each with 23.9 GiB free per card before launch) all failed at weight load. That
is a fact about that execution path, not about the checkpoint.

## Rebuilding

```
uv venv .venv-kimi --python 3.12
uv pip install --no-config --python .venv-kimi/bin/python -r kimi-env.lock.txt
```

Run `--no-config` from a directory outside this project: the project's
`override-dependencies` would otherwise install the scientific environment's
torch and produce an ABI mismatch.
