"""Execute the v15 notebook's code cells headlessly in DRY_RUN.

Stubs torch and transformers: the dry-run path never touches a GPU, and the
logic under test is pandas/numpy/scipy. Redirects the Colab output roots into a
local scratch directory.
"""
import json
import sys
import traceback
import types
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import os

ROOT = Path(__file__).parent
SCRATCH = ROOT / os.environ.get("V14_SCRATCH", "scratch")
# Validation-only overrides. They resize a dry-run fixture so the pass branches
# of the later gates can be exercised. They never ship in the notebook.
_ENV_OVERRIDES = [
    ('MODEL_PROFILE: Literal["dev_fast", "integration_pass", "pilot", "study"] = "dev_fast"',
     'MODEL_PROFILE: Literal["dev_fast", "integration_pass", "pilot", "study"] = "{}"',
     "V15_PROFILE"),
    ('RUN_MODE: Literal["smoke", "full"] = "smoke"',
     'RUN_MODE: Literal["smoke", "full"] = "{}"', "V14_RUN_MODE"),
    ("    smoke_calibration_tasks: int = 12",
     "    smoke_calibration_tasks: int = {}", "V14_CAL_TASKS"),
    ("    full_calibration_tasks: int = 16",
     "    full_calibration_tasks: int = {}", "V14_CAL_TASKS"),
    ("    smoke_screening_tasks: int = 8",
     "    smoke_screening_tasks: int = {}", "V14_SCREEN_TASKS"),
    ("    full_screening_tasks: int = 8",
     "    full_screening_tasks: int = {}", "V14_SCREEN_TASKS"),
    ("    smoke_wording_tasks: int = 4",
     "    smoke_wording_tasks: int = {}", "V14_WORD_TASKS"),
    ("    smoke_confirmatory_tasks: int = 6",
     "    smoke_confirmatory_tasks: int = {}", "V14_CONF_TASKS"),
]
OVERRIDES = [(find, tmpl.format(os.environ[key]))
             for find, tmpl, key in _ENV_OVERRIDES if os.environ.get(key)]


# ------------------------------------------------------------- stub torch
def _stub_torch() -> types.ModuleType:
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

    cuda = _Cuda()
    torch.cuda = cuda
    torch.OutOfMemoryError = _Cuda.OutOfMemoryError
    cuda.OutOfMemoryError = _Cuda.OutOfMemoryError
    torch.manual_seed = lambda _: None
    torch.float16 = "float16"
    torch.bfloat16 = "bfloat16"
    torch.version = types.SimpleNamespace(cuda=None)
    backends = types.SimpleNamespace(
        cuda=types.SimpleNamespace(matmul=types.SimpleNamespace(allow_tf32=False)))
    torch.backends = backends
    torch.inference_mode = lambda: __import__("contextlib").nullcontext()
    torch.Tensor = type("Tensor", (), {})
    torch.__version__ = "0.0.0-stub"

    def _missing(name):
        if name.startswith("__"):
            raise AttributeError(name)
        return type(name, (), {})

    torch.__getattr__ = _missing
    return torch


def _stub_transformers() -> types.ModuleType:
    tf = types.ModuleType("transformers")
    tf.AutoModelForCausalLM = object
    tf.AutoTokenizer = object
    tf.set_seed = lambda _: None
    return tf


sys.modules.setdefault("torch", _stub_torch())
sys.modules.setdefault("transformers", _stub_transformers())

try:
    from IPython.display import display  # noqa: F401
except Exception:  # pragma: no cover
    pass


def main() -> int:
    nb = json.loads((ROOT / "directional_constraint_interference_v15.ipynb")
                    .read_text(encoding="utf-8"))
    code = [(i, "".join(c["source"])) for i, c in enumerate(nb["cells"])
            if c["cell_type"] == "code"]
    namespace: dict = {"__name__": "__main__"}
    for index, source in code:
        if source.lstrip().startswith("%pip"):
            print(f"[cell {index:02d}] skipped (%pip)")
            continue
        source = source.replace("/content/drive/MyDrive/directional_interference",
                                str(SCRATCH / "drive"))
        source = source.replace("/content/directional_interference_local",
                                str(SCRATCH / "local"))
        source = source.replace('_gdrive.mount("/content/drive")',
                                f'Path({str(SCRATCH / "drive")!r}).mkdir(parents=True, exist_ok=True)')
        source = source.replace('Path("/content/drive/MyDrive").exists()',
                                "True")
        for _find, _repl in OVERRIDES:
            source = source.replace(_find, _repl)
        import time as _t
        _t0 = _t.time()
        print(f"\n{'=' * 72}\n[cell {index:02d}] executing\n{'=' * 72}", flush=True)
        try:
            exec(compile(source, f"<cell {index}>", "exec"), namespace)
            print(f"[cell {index:02d}] done in {_t.time() - _t0:.1f}s", flush=True)
        except Exception:
            print(f"\n!!! cell {index} raised:")
            traceback.print_exc()
            return index
    print("\nALL CELLS EXECUTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
