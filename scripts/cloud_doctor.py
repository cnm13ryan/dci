#!/usr/bin/env python3
"""Lambda-instance preflight: CUDA tier of the same checks plus the frozen
hardware-class preview. Run on the instance after bootstrap, before any run."""
from __future__ import annotations

import json
import subprocess
import sys


def main() -> int:
    code = subprocess.call([sys.executable, "scripts/local_doctor.py", "--gpu"])
    if code != 0:
        return code
    print("\n== hardware execution class this instance would freeze")
    from dci.compat import torch
    from dci.provenance.hashes import sha
    props = torch.cuda.get_device_properties(0)
    fields = {
        "gpu_name": props.name,
        "compute_capability": f"{props.major}.{props.minor}",
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "torch_cuda_build": f"{torch.__version__}+cu{getattr(torch.version, 'cuda', 'na')}",
        "attn_implementation": "sdpa",
        "device_count": int(torch.cuda.device_count()),
    }
    fields["class"] = sha(fields)[:16]
    print(json.dumps(fields, indent=2))
    print("\nA scientific run frozen on this class refuses to resume anywhere "
          "else; interruption recovery must relaunch the SAME instance type.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
