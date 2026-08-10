#!/usr/bin/env bash
# On-instance bootstrap, mode A: keep Lambda Stack's CUDA torch (venv with
# --system-site-packages), add the scientific core and pins on top, record the
# environment identity. No apt full-upgrade/dist-upgrade (Lambda documents
# these can break the image); no OS changes at all.
set -euo pipefail
cd ~/dci
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -e . pytest
python -m pip install -q "transformers>=4.49" "accelerate>=1.4" "huggingface-hub>=0.29"
python - <<'PY'
import hashlib, json, platform, subprocess, sys
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
open("environment_identity.json", "w").write(json.dumps(ident, indent=2))
open("pip_freeze.txt", "w").write(freeze)
print(json.dumps(ident, indent=2))
PY
python scripts/cloud_doctor.py
dci test
echo "bootstrap complete; environment identity recorded."
