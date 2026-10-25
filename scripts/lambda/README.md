# Lambda scripts for the Batch 1 pilot

For the 2x H100 SXM instance on GPU Base 24.04 (D12, researcher's conditions of
2026-10-25). Every script is idempotent. None of them upgrades packages,
changes the driver, shuts the machine down, installs anything outside the two
lockfiles, uses `--torch-backend=auto` or runs `vllm download-kernels`.
Secrets never go on a command line: the Hugging Face token comes from
`hf auth login` or a shell-exported `HF_TOKEN`, and the SSH key from your ssh
config or `SSH_KEY` (a path).

| step | where | script |
|---|---|---|
| 6 host gate | instance | `preflight.sh /lambda/nfs/dci` (read-only; exit 0 only if every check passes) |
| 7 build | instance | `bootstrap.sh /lambda/nfs/dci/repo /lambda/nfs/dci` (expects `2.9.1+cu129 12.9 True 0.15.1`) |
| 7 models | instance | `HF_HOME=/lambda/nfs/dci/hf fetch_models.sh /lambda/nfs/dci/repo`, then `export HF_HUB_OFFLINE=1` |
| 8, 9 memory | instance, own tmux window | `gpu_monitor.sh /lambda/nfs/dci/logs/gpu.csv`; afterwards `gpu_peaks.sh LOG [FROM] [TO]` |
| 8-10 evidence | Mac | `sync_back.sh ubuntu@HOST /lambda/nfs/dci LOCAL_DIR [runs logs locks]` |

Long jobs (`smoke`, `execute`, `resume`) run in tmux with output tee'd to
`/lambda/nfs/dci/logs/`, for example:

```bash
tmux new -s stage1
P="/lambda/nfs/dci/repo/.venv/bin/python -m dci.batch1"
B=/lambda/nfs/dci/repo/environments/cuda-vllm/.venv/bin/python
$P execute --root /lambda/nfs/dci/runs/R --stage stage1 --authorize <freeze1 hash> \
  --accelerator cuda --devices 0,1 --backend-python $B 2>&1 | tee -a /lambda/nfs/dci/logs/stage1.log
```

`sync_back.sh` writes `MANIFEST.sha256` (and the instance checkout's commit,
`SYNC_SOURCE_SHA`) in each directory on the instance, copies it with rsync,
and checks every file on the Mac with `shasum -a 256 -c`.
