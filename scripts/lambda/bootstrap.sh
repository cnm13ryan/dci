#!/usr/bin/env bash
# Build both Batch 1 environments from their committed lockfiles (step 7).
# Idempotent: `uv sync --frozen` installs exactly the lock, never resolves.
# Usage: bootstrap.sh REPO_DIR FS_DIR
#   REPO_DIR  the checkout of the pushed SHA (for example FS_DIR/repo)
#   FS_DIR    the persistent filesystem; the uv cache lives there
# Uses the system Python 3.12 only (no interpreter download), never
# --torch-backend=auto, and installs nothing outside the two lockfiles.
set -euo pipefail
REPO="${1:?usage: bootstrap.sh REPO_DIR FS_DIR}"
FS="${2:?usage: bootstrap.sh REPO_DIR FS_DIR}"
EXPECT="2.9.1+cu129 12.9 True 0.15.1"
command -v uv >/dev/null || { echo "uv is not on PATH; install it first" >&2; exit 2; }
export UV_CACHE_DIR="$FS/uv-cache" UV_PYTHON_PREFERENCE=only-system UV_PYTHON=3.12
cd "$REPO"
echo "repo $(git rev-parse HEAD) $(git status --porcelain | wc -l | tr -d ' ') uncommitted"
uv sync --frozen
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
(cd environments/cuda-vllm && uv sync --frozen)
got="$(environments/cuda-vllm/.venv/bin/python -c 'import torch, vllm; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), vllm.__version__)' 2>/dev/null | tail -1)"
echo "backend: $got"
[ "$got" = "$EXPECT" ] || { echo "expected: $EXPECT" >&2; exit 1; }
echo "backend python: $REPO/environments/cuda-vllm/.venv/bin/python"
