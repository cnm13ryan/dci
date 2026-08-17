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


def judge_generate_fn(job: Job):
    """The autorater's generate function (A2). Synthetic namespace uses
    the mocked judge (test-injected disagree/invalid rates); the
    registered namespace runs the configured judge model for real."""
    if job.context.namespace == "synthetic":
        from dci1v3.generation.synthetic import synthetic_judge
        return functools.partial(
            synthetic_judge,
            disagree_rate=float(job.options.get("judge_disagree", 0.02)),
            invalid_rate=float(job.options.get("judge_invalid", 0.0)))
    from dci1v3.generation.backend import run_backend
    return functools.partial(run_backend,
                             device=int(job.options.get("device", 0)))
