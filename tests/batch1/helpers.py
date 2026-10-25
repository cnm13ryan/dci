"""Shared fixtures for the Batch 1 tests: a reduced panel, approvals, a
stand-in execution environment, and run roots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci.batch1 import config as CFG
from dci.batch1 import environment as ENV
from dci.batch1 import freeze as F

#: The pilot at reduced size: 8 Stage 1 topics, 16 Stage 2 topics, at most
#: 20 refined cells. Every rule is the real one.
SMALL = CFG.PilotConfig(stage1_topics=8, stage2_topics=16, pilot_topics=24,
                        stage2_max_cells=20, stability_replicates=8)


def approved(cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG) -> dict[str, Any]:
    """Every decision APPROVED by a test reviewer (never written by code)."""
    a = F.approvals_template(cfg)
    for d in a["decisions"].values():
        d.update(status="APPROVED", approved_by="test reviewer",
                 approved_on="2026-10-19")
    return a


def fake_probe(**changes: Any) -> dict[str, Any]:
    """What ``environment.probe`` would report on a stand-in host."""
    gpu = {"name": "NVIDIA H100 80GB HBM3", "capability": "9.0",
           "memory_gib": 79}
    found = {"status": "AVAILABLE", "interpreter": "/opt/backend/bin/python",
             "executable": "/opt/backend/bin/python", "python": "3.12.3",
             "implementation": "cpython", "platform": "Linux-test",
             "hostname": "test-host", "kernel": "6.8.0-test",
             "packages": {"vllm": "0.15.1", "torch": "2.9.1+cu129",
                          "transformers": "4.99", "tokenizers": "0.21",
                          "triton": None, "xformers": None,
                          "flashinfer-python": None, "numpy": "2.1"},
             "distributions": 120, "distributions_hash": "d" * 64,
             "torch_cuda": "12.9", "torch_hip": None,
             "accelerators": ["NVIDIA H100 80GB HBM3"], "gpu_count": 2,
             "gpus": [dict(gpu, uuid="GPU-a"), dict(gpu, uuid="GPU-b")],
             "gpu_uuids": ["GPU-a", "GPU-b"], "driver": ["580.126.20"]}
    found.update(changes)
    return found


def fake_lock(**changes: Any) -> dict[str, Any]:
    return ENV.lock_from_probe(fake_probe(**changes))


def make_root(root: Path, cfg: CFG.PilotConfig = SMALL,
              approvals: dict[str, Any] | None = None,
              freeze1: dict[str, Any] | None = None) -> dict[str, Any]:
    approvals = approvals or F.approvals_template(cfg)
    freeze1 = freeze1 or F.freeze1_manifest(cfg, approvals)
    F.write_json(Path(root) / "freeze1.json", freeze1)
    F.write_json(Path(root) / "approvals.json", approvals)
    return {"root": Path(root), "freeze1": freeze1, "approvals": approvals}


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in Path(path).read_text().splitlines()
            if l.strip()]
