"""Host facts. The dataclass is pure; only the probe touches torch/vLLM.

Splitting the description of the host from the act of measuring it is what lets
`resolve.py` be a pure function and therefore golden-file testable on CPU CI
with no GPU stack installed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass(frozen=True)
class HostProfile:
    """What the machine is. Measured once, then passed around as data."""

    device_count: int = 0
    gcn_archs: tuple[str, ...] = ()
    device_names: tuple[str, ...] = ()
    total_vram_gib: tuple[float, ...] = ()
    torch_version: str = ""
    torch_hip: str = ""
    vllm_version: str = ""
    platform_class: str = ""
    #: vLLM's own answers, not our guesses.
    supports_fp8: bool = False
    supports_mx: bool = False
    use_custom_allreduce: bool = False
    is_navi: bool = False
    env: dict[str, str] = field(default_factory=dict)

    @property
    def is_rdna3(self) -> bool:
        return any("gfx11" in a for a in self.gcn_archs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HostProfile:
        known = {f.name for f in fields(cls)}
        payload = {k: v for k, v in data.items() if k in known}
        for key in ("gcn_archs", "device_names", "total_vram_gib"):
            if key in payload and payload[key] is not None:
                payload[key] = tuple(payload[key])
        return cls(**payload)


#: Environment variables worth recording with a run: they change execution
#: conditions and are invisible in the engine kwargs.
RECORDED_ENV_PREFIXES = ("NCCL_", "RCCL_", "HIP_", "HSA_", "VLLM_", "ROCR_",
                         "PYTORCH_", "TORCH_", "FLASH_ATTENTION_")


def probe() -> HostProfile:
    """Measure the host. Imports torch/vLLM lazily so this module stays
    importable in the scientific environment."""
    import os

    profile: dict[str, Any] = {
        "env": {k: v for k, v in os.environ.items()
                if k.startswith(RECORDED_ENV_PREFIXES)},
    }
    try:
        import torch

        profile["torch_version"] = torch.__version__
        profile["torch_hip"] = torch.version.hip or ""
        count = torch.cuda.device_count()
        profile["device_count"] = count
        props = [torch.cuda.get_device_properties(i) for i in range(count)]
        profile["gcn_archs"] = tuple(getattr(p, "gcnArchName", "") for p in props)
        profile["device_names"] = tuple(p.name for p in props)
        profile["total_vram_gib"] = tuple(
            round(p.total_memory / 2 ** 30, 2) for p in props)
    except Exception:
        pass

    try:
        import vllm
        from vllm.platforms import current_platform

        profile["vllm_version"] = vllm.__version__
        profile["platform_class"] = type(current_platform).__name__
        for name in ("supports_fp8", "supports_mx", "use_custom_allreduce",
                     "is_navi"):
            method = getattr(current_platform, name, None)
            if method is not None:
                try:
                    profile[name] = bool(method())
                except Exception:
                    pass
    except Exception:
        pass

    return HostProfile(**profile)


def rocm_smi_memory() -> dict:
    """Per-GPU VRAM from rocm-smi — the only view that sees ALL TP workers.

    `torch.cuda.memory_allocated` reports the calling process only. Under
    tensor parallelism vLLM runs one worker process per rank, so the driver's
    own accounting is what shows whether rank 1 actually holds weights. "Is the
    12B really sharded, or is GPU 1 idle?" cannot be answered any other way.
    """
    import json
    import re
    import subprocess

    try:
        out = subprocess.run(["rocm-smi", "--showmemuse", "--json"],
                             capture_output=True, text=True, timeout=60).stdout
        return json.loads(out)
    except Exception:
        try:
            out = subprocess.run(["rocm-smi", "--showmemuse"],
                                 capture_output=True, text=True,
                                 timeout=60).stdout
            found = re.findall(r"GPU\[(\d+)\].*?(\d+)\s*$", out, re.MULTILINE)
            return {f"GPU[{i}]": v for i, v in found}
        except Exception:
            return {}


def torch_memory() -> dict:
    """Resident VRAM per visible device in THIS process, for the capacity record."""
    try:
        import torch

        if not torch.cuda.is_available():
            return {}
        return {f"cuda:{i}": round(torch.cuda.memory_allocated(i) / 2 ** 30, 3)
                for i in range(torch.cuda.device_count())}
    except Exception:
        return {}
