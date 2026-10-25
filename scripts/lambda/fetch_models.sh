#!/usr/bin/env bash
# Download the four Batch 1 models at their pinned revisions (config.MODELS)
# into HF_HOME on the persistent filesystem, then check every snapshot.
# Idempotent: files already present are not fetched again.
# Usage: HF_HOME=/lambda/nfs/dci/hf fetch_models.sh REPO_DIR
# The two Gemma 3n models are gated. Authenticate beforehand with
# `hf auth login` (the token is read from HF_HOME, never from the command
# line) or export HF_TOKEN in the shell; this script never prints it.
set -euo pipefail
REPO="${1:?usage: HF_HOME=... fetch_models.sh REPO_DIR}"
: "${HF_HOME:?set HF_HOME to a directory on the persistent filesystem}"
export HF_HOME HF_HUB_OFFLINE=0
cd "$REPO"
.venv/bin/python -c 'from dci.batch1 import config as C; [print(m.model_id, m.revision) for m in C.MODELS]' > "$HF_HOME/batch1_models.txt"
environments/cuda-vllm/.venv/bin/python - "$HF_HOME/batch1_models.txt" <<'PY'
import sys
from huggingface_hub import snapshot_download
for line in open(sys.argv[1]):
    model, revision = line.split()
    path = snapshot_download(model, revision=revision)
    assert path.rstrip("/").endswith(revision), (model, path)
    print("ok", model, revision, path)
PY
echo "done; from now on: export HF_HOME=$HF_HOME HF_HUB_OFFLINE=1"
