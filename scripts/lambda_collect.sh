#!/usr/bin/env bash
# Collect run exports and verify SHA-256 before anyone terminates anything.
set -euo pipefail
HOST="" KEY="" DEST="lambda-results" REMOTE='~/dci/artifacts'
while [[ $# -gt 0 ]]; do case "$1" in
  --host) HOST="$2"; shift 2;; --key) KEY="$2"; shift 2;;
  --destination) DEST="$2"; shift 2;; --remote) REMOTE="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 2;; esac; done
[[ -n "$HOST" && -n "$KEY" ]] || { echo "--host and --key required"; exit 2; }
mkdir -p "$DEST"
rsync -az -e "ssh -i $KEY -o IdentitiesOnly=yes" \
  "ubuntu@$HOST:$REMOTE/" "$DEST/artifacts/"
python3 - "$DEST/artifacts" <<'PY'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
bad = checked = 0
for manifest in root.rglob("sha256_manifest.json"):
    entries = json.loads(manifest.read_text())
    base = manifest.parent
    for rel, expect in (entries.items() if isinstance(entries, dict) else []):
        p = base / rel
        if not p.exists():
            print("MISSING", p); bad += 1; continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        checked += 1
        if got != expect:
            print("HASH MISMATCH", p); bad += 1
print(f"verified {checked} files against manifests; {bad} problems")
sys.exit(1 if bad else 0)
PY
echo "collected into $DEST and verified. Only now is termination safe."
