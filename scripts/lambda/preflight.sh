#!/usr/bin/env bash
# Batch 1 host gate (step 6), read-only and idempotent: x86_64, 2x H100 SXM,
# NVIDIA driver >= 575.51.03, the persistent filesystem mounted, Python 3.12.
# Usage: preflight.sh FS_DIR        e.g. preflight.sh /lambda/nfs/dci
# Exit 0 only when every check passes; prints one line per check.
set -u
FS="${1:?usage: preflight.sh FS_DIR}"
MIN_DRIVER="575.51.03"
WANT_GPU="NVIDIA H100 80GB HBM3"
WANT_COUNT=2
fail=0
check() { if [ "$2" = ok ]; then echo "PASS $1: $3"; else echo "FAIL $1: $3"; fail=1; fi; }
version_ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]; }

arch="$(uname -m)"
check arch "$([ "$arch" = x86_64 ] && echo ok)" "$arch"

if command -v nvidia-smi >/dev/null 2>&1; then
  names="$(nvidia-smi --query-gpu=name --format=csv,noheader)"
  count="$(printf '%s\n' "$names" | grep -c .)"
  other="$(printf '%s\n' "$names" | grep -vxF "$WANT_GPU" | head -1)"
  check gpus "$([ "$count" = "$WANT_COUNT" ] && [ -z "$other" ] && echo ok)" \
    "$count x $(printf '%s\n' "$names" | sort -u | paste -sd, -)"
  driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | sort -u | head -1)"
  check driver "$(version_ge "$driver" "$MIN_DRIVER" && echo ok)" "$driver (need >= $MIN_DRIVER)"
else
  check gpus "" "nvidia-smi not found"
  check driver "" "nvidia-smi not found"
fi

if command -v findmnt >/dev/null 2>&1 && findmnt -T "$FS" >/dev/null 2>&1; then
  mnt="$(findmnt -T "$FS" -no TARGET,FSTYPE | head -1)"
  [ "$(findmnt -T "$FS" -no TARGET)" != / ] && ok=ok || ok=""
  check filesystem "$ok" "$FS on $mnt"
else
  check filesystem "" "$FS not found"
fi
[ -d "$FS" ] && [ -w "$FS" ] && check writable ok "$FS" || check writable "" "$FS"

py="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)"
check python3 "$([ "$py" = 3.12 ] && echo ok)" "system python3 is ${py:-missing}"
check uv "$(command -v uv >/dev/null 2>&1 && echo ok)" "$(uv --version 2>/dev/null || echo 'not on PATH')"
echo "disk: $(df -h "$FS" 2>/dev/null | tail -1)"
exit $fail
