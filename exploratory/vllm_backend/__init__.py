"""Canonical vLLM inference backend for the DCI study.

ONE engine, ONE schema, ONE place for model-specific facts.

    from vllm_backend import engine, io, registry, resolve

Import discipline, enforced by `tests/test_single_engine_site.py`:

* `contract`, `plan`, `registry`, `records`, `resolve`, `io`, `hardware` are
  stdlib-only and import in ANY environment, including CPU CI with no GPU stack.
  The plan builders that run in the scientific environment depend on this.
* `engine`, `reasoning`, `capabilities` import vLLM/torch lazily, inside
  functions, so merely importing this package never pulls in a GPU stack.
* `engine.build_engine` is the only `LLM(...)` call in the repository.

This package must NOT import `dci`, `crossmodel` or `dci_exploratory`: it is
executed by a different interpreter from the scientific code (vLLM's ROCm wheels
pin a torch the scientific environment cannot hold), so the process boundary is
load-bearing rather than stylistic.
"""
from __future__ import annotations

__all__ = [
    "capabilities", "contract", "engine", "hardware", "io", "plan",
    "reasoning", "records", "registry", "resolve",
]
