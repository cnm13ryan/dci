#!/usr/bin/env bash
# Copy Batch 1 evidence from the instance to the Mac and verify it (steps 8-10).
# On the instance: write SHA-256 manifests over every file under each synced
# directory. On the Mac: rsync, then check every file against its manifest.
# Idempotent: rerunning re-hashes, re-syncs and re-verifies.
# Usage (on the Mac): sync_back.sh USER@HOST REMOTE_FS LOCAL_DIR [DIR ...]
#   REMOTE_FS  e.g. /lambda/nfs/dci; DIRs are relative to it
#              (default: runs logs locks)
# The SSH key comes from your ssh config or SSH_KEY (a path); nothing secret
# is passed on the command line or written to the manifests.
set -euo pipefail
HOST="${1:?usage: sync_back.sh USER@HOST REMOTE_FS LOCAL_DIR [DIR ...]}"
REMOTE="${2:?remote filesystem}"; LOCAL="${3:?local directory}"; shift 3
if [ $# -eq 0 ]; then DIRS=(runs logs locks); else DIRS=("$@"); fi
SSH=(ssh -o BatchMode=yes); [ -n "${SSH_KEY:-}" ] && SSH+=(-i "$SSH_KEY")
mkdir -p "$LOCAL"
for d in "${DIRS[@]}"; do
  "${SSH[@]}" "$HOST" "set -e; cd '$REMOTE/$d' && find . -type f ! -name MANIFEST.sha256 ! -name SYNC_SOURCE_SHA -print0 | sort -z | xargs -0 -r sha256sum > MANIFEST.sha256 && (cd '$REMOTE/repo' 2>/dev/null && git rev-parse HEAD || echo unknown) > SYNC_SOURCE_SHA && sha256sum SYNC_SOURCE_SHA >> MANIFEST.sha256"
  rsync -a -e "${SSH[*]}" "$HOST:$REMOTE/$d/" "$LOCAL/$d/"
  (cd "$LOCAL/$d" && shasum -a 256 -c --quiet MANIFEST.sha256) \
    && echo "verified $d: $(grep -c . "$LOCAL/$d/MANIFEST.sha256") files, source $(cat "$LOCAL/$d/SYNC_SOURCE_SHA")" \
    || { echo "VERIFY FAILED: $d" >&2; exit 1; }
done
