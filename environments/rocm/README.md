# Local ROCm environment (2x RX 7900 XTX)

```bash
cd environments/rocm
uv sync                       # resolves ROCm wheels from repo.radeon.com
uv run python ../../scripts/local_doctor.py --gpu --expect-devices 2
uv run dci test
uv run dci validate --profile integration_pass
uv run dci run --profile dev_fast --data-root ~/dci-artifacts   # dry run
# real dev_fast smoke on GPU 0 (non-evidence):
uv run dci run --profile dev_fast_gpu --device 0 --data-root ~/dci-artifacts
```

Notes.
- ROCm PyTorch exposes the HIP device through `torch.cuda`; `--device 0/1`
  selects between the two 7900 XTX cards. 24 GB VRAM per card holds every
  v15 profile (0.5B/1.5B/3B fp16) with wide margin; the two cards are used as
  independent workers (`--shard 0/2 --device 0` + `--shard 1/2 --device 1`),
  never as one pooled 48 GB device.
- Host prerequisites (kernel driver, `amdgpu-dkms`, user in `render`/`video`
  groups) follow AMD's Radeon-on-Linux install guide for your distribution;
  the doctor verifies the result rather than assuming it.
- vLLM is NOT part of this environment: v15's frozen engine is
  hf_transformers, and adding vLLM is a new execution condition (see
  docs/MIGRATION.md, inference section). The exemplar project's vendored
  vLLM/aiter/flash-attn wheels are the starting point if that work is ever
  scheduled.
- Local runs are development tiers only: `dev_fast*` and `integration_pass`.
  The hardware class recorded here can never resume on Lambda, by design.
