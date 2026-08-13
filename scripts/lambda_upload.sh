#!/usr/bin/env bash
# Upload the source tree (never artifacts, never caches: a generation cache
# from another hardware class must not exist on the instance at all).
set -euo pipefail
HOST="" KEY=""
while [[ $# -gt 0 ]]; do case "$1" in
  --host) HOST="$2"; shift 2;; --key) KEY="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 2;; esac; done
[[ -n "$HOST" && -n "$KEY" ]] || { echo "--host and --key required"; exit 2; }
rsync -az -e "ssh -i $KEY -o IdentitiesOnly=yes" \
  --exclude artifacts --exclude .git --exclude '__pycache__' \
  --exclude 'uv.lock' --exclude '.venv' \
  ./ "ubuntu@$HOST:~/dci/"
echo "uploaded to ubuntu@$HOST:~/dci"
