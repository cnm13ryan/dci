#!/usr/bin/env bash
# Collect run artifacts and verify SHA-256 before anyone terminates anything.
#
# Three things this script must never do, all of which it used to do:
#
#   1. resolve manifest entries against the manifest's own directory. c402
#      writes RUN_ROOT/exports/<label>/sha256_manifest.json with entries
#      relative to RUN_ROOT, so "manifest.parent / rel" pointed two levels too
#      deep. Every entry looked MISSING, or - if a same-named file happened to
#      exist under exports/ - was verified against the wrong bytes.
#   2. report success when nothing was verified. Zero manifests found meant
#      checked=0, bad=0, exit 0, and the script printed that termination was
#      safe. Deleting the instance then destroyed the run.
#   3. guess the remote data root. The runbook launches with a persistent
#      filesystem root such as /lambda/nfs/<fs>/dci while the default here was
#      ~/dci/artifacts, so a user following the documented commands verbatim
#      rsynced an empty or stale directory and verified nothing. --remote is
#      required: there is no safe default, only a plausible one.
set -euo pipefail
HOST="" KEY="" DEST="lambda-results" REMOTE=""
while [[ $# -gt 0 ]]; do case "$1" in
  --host) HOST="$2"; shift 2;; --key) KEY="$2"; shift 2;;
  --destination) DEST="$2"; shift 2;; --remote) REMOTE="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 2;; esac; done
[[ -n "$HOST" && -n "$KEY" ]] || { echo "--host and --key required"; exit 2; }
[[ -n "$REMOTE" ]] || {
  echo "--remote is required: pass the persistent data root the run actually"
  echo "used, for example --remote /lambda/nfs/<filesystem>/dci. It must match"
  echo "the --data-root given to \`dci run\`; the instance root disk is erased"
  echo "on termination, so a guess here can collect nothing and still succeed."
  exit 2; }
mkdir -p "$DEST"
rsync -az -e "ssh -i $KEY -o IdentitiesOnly=yes" \
  "ubuntu@$HOST:$REMOTE/" "$DEST/artifacts/"
python3 - "$DEST/artifacts" <<'PY'
import hashlib, json, sys
from pathlib import Path

root = Path(sys.argv[1])


def resolve_base(manifest: Path, entries: dict) -> Path | None:
    """The directory the manifest's relative paths are anchored to.

    Walk upward from the manifest, bounded by the collection root, and take the
    first ancestor under which a sample of the declared entries actually
    resolves. This handles the in-tree layout (manifest three levels below
    RUN_ROOT) and the zip-extracted layout (manifest beside its entries) without
    hard-coding either depth.
    """
    sample = [rel for rel in list(entries)[:5]]
    if not sample:
        return None
    for base in [manifest.parent, *manifest.parents]:
        if all((base / rel).exists() for rel in sample):
            return base
        if base == root:
            break
    return None


manifests = sorted(root.rglob("sha256_manifest.json"))
bad = checked = unresolved = 0
for manifest in manifests:
    try:
        entries = json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"UNREADABLE MANIFEST {manifest}: {exc}")
        bad += 1
        continue
    if not isinstance(entries, dict) or not entries:
        print(f"EMPTY MANIFEST {manifest}")
        bad += 1
        continue
    base = resolve_base(manifest, entries)
    if base is None:
        # Cannot anchor the entries, so nothing in this manifest is verified.
        # That is a failure, not a manifest to skip.
        print(f"UNANCHORED MANIFEST {manifest}: none of its declared entries "
              "resolve under any ancestor directory")
        unresolved += 1
        bad += 1
        continue
    print(f"manifest {manifest} anchored at {base}")
    for rel, expect in entries.items():
        p = base / rel
        if not p.exists():
            print("MISSING", p)
            bad += 1
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        checked += 1
        if got != expect:
            print("HASH MISMATCH", p)
            bad += 1

print(f"manifests found: {len(manifests)}; entries verified: {checked}; "
      f"problems: {bad}")
if not manifests:
    print("FAIL: no sha256_manifest.json anywhere under the collected tree. "
          "Nothing was verified, so nothing is known to have been collected.")
    sys.exit(1)
if not checked:
    print("FAIL: zero manifest entries were verified.")
    sys.exit(1)
if bad:
    print("FAIL: manifest verification found problems.")
    sys.exit(1)
print("OK: every declared artifact is present and matches its recorded hash.")
PY
echo "collected into $DEST and verified. Only now is termination safe."
