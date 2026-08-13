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
    if ACTIVE.planning_only:
        # Checked before every other branch, including the dry-run oracle: a
        # planning command must not emit synthetic text either, because
        # synthetic output written into a run directory is exactly what later
        # gets mistaken for evidence.
        from dci.inference.planning import PlanningBackend
        return PlanningBackend()
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
