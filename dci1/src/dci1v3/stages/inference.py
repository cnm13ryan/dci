"""Inference routing shared by every generative stage.

Synthetic namespace -> the synthetic adapter (tests only). Registered
namespace -> the real backend, on the GPU device selected by the
operational ``--device`` option (default 0). Device selection is execution
routing, never a scientific variable: both cards are the same registered
hardware class, and the per-device GpuLock still serialises each card.
"""
from __future__ import annotations

import functools

from dci1v3.engine.dispatch import Job


def generate_fn(job: Job):
    if job.context.namespace == "synthetic":
        from dci1v3.generation.synthetic import synthetic_generate
        return synthetic_generate
    from dci1v3.generation.backend import run_backend
    return functools.partial(run_backend,
                             device=int(job.options.get("device", 0)))
