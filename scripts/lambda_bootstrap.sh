#!/usr/bin/env bash
# On-instance bootstrap, mode A: keep Lambda Stack's CUDA torch (venv with
# --system-site-packages), add the scientific core and pins on top, record the
# environment identity. No apt full-upgrade/dist-upgrade (Lambda documents
# these can break the image); no OS changes at all.
set -euo pipefail

# The persistent data root. environment_identity.json and pip_freeze.txt used to
# be written only into ~/dci, which is the INSTANCE ROOT DISK: it is erased on
# termination, so the runtime identity of the machine that produced the science
# did not survive the run it describes, and lambda_collect.sh never saw it
# because it is not under the collected tree.
DATA_ROOT="${DCI_DATA_ROOT:-}"
while [[ $# -gt 0 ]]; do case "$1" in
  --data-root) DATA_ROOT="$2"; shift 2;;
  *) echo "unknown arg $1"; exit 2;; esac; done
[[ -n "$DATA_ROOT" ]] || {
  echo "--data-root is required (or set DCI_DATA_ROOT): pass the persistent"
  echo "filesystem root the run will use, for example /lambda/nfs/<fs>/dci."
  echo "Environment provenance is written there so it survives termination and"
  echo "is collected with the results."
  exit 2; }
mkdir -p "$DATA_ROOT/provenance"
cd ~/dci
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -e . pytest
python -m pip install -q "transformers>=4.49" "accelerate>=1.4" "huggingface-hub>=0.29"
DATA_ROOT="$DATA_ROOT" python - <<'PY'
import hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path
import torch
freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                        capture_output=True, text=True).stdout
ident = {
    "mode": "A-system-site-packages",
    "image_hint": "lambda-stack-24-04",
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "platform": platform.platform(),
    "pip_freeze_sha256": hashlib.sha256(freeze.encode()).hexdigest(),
}
# Written to the DURABLE root first, so the identity of the runtime that
# produced the artifacts is stored beside them and is collected with them. The
# local copy is a convenience for on-instance debugging.
durable = Path(os.environ["DATA_ROOT"]) / "provenance"
durable.mkdir(parents=True, exist_ok=True)
ident["durable_provenance_dir"] = str(durable)
for name, text in (("environment_identity.json", json.dumps(ident, indent=2)),
                   ("pip_freeze.txt", freeze)):
    (durable / name).write_text(text)
    Path(name).write_text(text)
print(json.dumps(ident, indent=2))
print(f"environment provenance written to {durable} (survives termination)")
PY
python scripts/cloud_doctor.py
dci test
echo "bootstrap complete; environment identity recorded."
