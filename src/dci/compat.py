"""Optional-dependency shims.

The scientific core must import and run without torch or transformers: every
Gate 0 assertion, the whole dry-run pipeline and the integration self-test are
CPU-only by design, and CI exercises them in an environment where no GPU stack
is installed. Backends that genuinely need torch import it through here and
raise a diagnosable error only when real generation is requested.

The stub mirrors the one the notebook's run_headless harness used, so migrated
behavior under "torch absent" is identical to the validated notebook dry runs.
"""
from __future__ import annotations

import types


def _torch_stub() -> types.ModuleType:
    torch = types.ModuleType("torch")

    class _Cuda:
        OutOfMemoryError = type("OutOfMemoryError", (RuntimeError,), {})

        @staticmethod
        def is_available():
            return False

        @staticmethod
        def manual_seed_all(_):
            pass

        @staticmethod
        def empty_cache():
            pass

        @staticmethod
        def synchronize():
            pass

        @staticmethod
        def get_device_name():
            return None

        @staticmethod
        def device_count():
            return 0

    cuda = _Cuda()
    torch.cuda = cuda
    torch.OutOfMemoryError = _Cuda.OutOfMemoryError
    cuda.OutOfMemoryError = _Cuda.OutOfMemoryError
    torch.manual_seed = lambda _: None
    torch.float16 = "float16"
    torch.bfloat16 = "bfloat16"
    torch.version = types.SimpleNamespace(cuda=None, hip=None)
    torch.backends = types.SimpleNamespace(
        cuda=types.SimpleNamespace(matmul=types.SimpleNamespace(allow_tf32=False)))
    torch.inference_mode = lambda: __import__("contextlib").nullcontext()
    torch.Tensor = type("Tensor", (), {})
    torch.__version__ = "0.0.0-stub"

    def _missing(name):
        if name.startswith("__"):
            raise AttributeError(name)
        return type(name, (), {})

    torch.__getattr__ = _missing
    return torch


try:  # pragma: no cover - depends on environment
    import torch  # type: ignore
    TORCH_AVAILABLE = True
except Exception:  # ImportError or a broken GPU stack
    torch = _torch_stub()
    TORCH_AVAILABLE = False

try:  # pragma: no cover
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except Exception:
    AutoModelForCausalLM = object          # type: ignore
    AutoTokenizer = object                 # type: ignore

    def set_seed(_):                       # type: ignore
        return None

    TRANSFORMERS_AVAILABLE = False


def require_torch(context: str):
    """Raise a diagnosable environment error when real generation needs torch."""
    if not TORCH_AVAILABLE:
        raise EnvironmentError(
            f"{context} requires a real torch installation (ROCm locally, CUDA "
            "on Lambda). This environment has none, which is fine for dry runs "
            "and the integration self-test but not for model generation. "
            "Install one of environments/rocm or environments/cuda.")
    return torch
