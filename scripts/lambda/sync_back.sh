#!/usr/bin/env bash
# Copy Batch 1 evidence from the instance to the Mac and verify it (steps 8-10).
# On the instance: refuse any non-regular file, then write a SHA-256 manifest
# over every file under each synced directory. On the Mac: mirror it with
# rsync --delete, check every file against the manifest, and require the
# local file list to equal the manifest's exactly (third audit C4).
# Idempotent: rerunning re-hashes, re-syncs and re-verifies.
# Usage (on the Mac): sync_back.sh USER@HOST REMOTE_FS LOCAL_DIR [DIR ...]
#   REMOTE_FS  e.g. /lambda/nfs/dci; DIRs are relative to it
#              (default: runs logs locks)
# Run it while nothing is writing on the instance: a file written after its
# manifest makes the list check fail. SYNC_CHECKOUT_SHA is the instance
# checkout's commit at sync time, not the commit that produced a run; that is
# in each smoke report's "code" field and each pilot root's RUN.json.
# The SSH key comes from your ssh config or SSH_KEY (a path); nothing secret
# is passed on the command line or written to the manifests.
set -euo pipefail
HOST="${1:?usage: sync_back.sh USER@HOST REMOTE_FS LOCAL_DIR [DIR ...]}"
REMOTE="${2:?remote filesystem}"; LOCAL="${3:?local directory}"; shift 3
if [ $# -eq 0 ]; then DIRS=(runs logs locks); else DIRS=("$@"); fi
SSH=(ssh -o BatchMode=yes); [ -n "${SSH_KEY:-}" ] && SSH+=(-i "$SSH_KEY")
mkdir -p "$LOCAL"
for d in "${DIRS[@]}"; do
  "${SSH[@]}" "$HOST" "set -e; cd '$REMOTE/$d'
    odd=\$(find . ! -type f ! -type d | head -5)
    if [ -n \"\$odd\" ]; then echo \"non-regular files in $d: \$odd\" >&2; exit 3; fi
    (cd '$REMOTE/repo' 2>/dev/null && git rev-parse HEAD || echo unknown) > SYNC_CHECKOUT_SHA
    find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 -r sha256sum > MANIFEST.sha256"
  # --checksum: compare contents, not size and mtime, so a re-sync repairs
  # a same-size local corruption (openrsync on macOS skipped it).
  rsync -a --checksum --delete -e "${SSH[*]}" "$HOST:$REMOTE/$d/" "$LOCAL/$d/"
  (
    cd "$LOCAL/$d"
    odd="$(find . ! -type f ! -type d | head -5)"
    [ -z "$odd" ] || { echo "VERIFY FAILED: $d has non-regular files: $odd" >&2; exit 1; }
    shasum -a 256 -c --quiet MANIFEST.sha256 || { echo "VERIFY FAILED: $d hashes" >&2; exit 1; }
    listed="$(sed -E 's/^[0-9a-f]{64}  //' MANIFEST.sha256 | sort)"
    present="$(find . -type f ! -name MANIFEST.sha256 | sort)"
    [ "$listed" = "$present" ] || {
      echo "VERIFY FAILED: $d file list differs from its manifest:" >&2
      diff <(printf '%s\n' "$listed") <(printf '%s\n' "$present") >&2 || true
      exit 1; }
    echo "verified $d: $(printf '%s\n' "$listed" | grep -c .) files, all listed and all hashed; checkout at sync $(cat SYNC_CHECKOUT_SHA)"
  ) || exit 1
done
