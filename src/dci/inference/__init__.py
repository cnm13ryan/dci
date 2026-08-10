"""Backend selection: dry runs use the oracle; real generation uses the frozen
engine. Selecting anything else for an evidence-producing run is a new
execution condition, which is exactly what the fingerprint enforces."""
from __future__ import annotations

from dci.inference.base import InferenceBackend  # noqa: F401


def make_backend() -> "InferenceBackend":
    from dci.config.loader import ACTIVE
    from dci.pipeline import state as S

    cfg = S.CFG
    choice = ACTIVE.backend
    if cfg.dry_run:
        if choice not in (None, "oracle"):
            raise RuntimeError(
                f"backend {choice!r} requested for a dry run; dry runs always "
                "use the synthetic oracle so that no output can be evidence.")
        from dci.inference.oracle import OracleBackend
        return OracleBackend()
    engine = choice or cfg.engine
    if engine == "hf_transformers":
        from dci.inference.hf_transformers import HFTransformersBackend
        return HFTransformersBackend()
    raise RuntimeError(
        f"unknown engine {engine!r}. Adding one (for example vLLM) is a new "
        "execution condition: implement the backend contract in "
        "dci/inference/, add parity tests, and freeze it deliberately.")
