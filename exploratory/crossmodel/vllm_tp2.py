"""Backward-compatible entrypoint. The implementation now lives in `vllm_backend`.

This file used to carry its own `LLM(...)` construction, chat rendering,
sampling, record schema, chunking and deadline logic — one of eight such copies.
All of that moved to the canonical backend; what remains is the command line,
because `xm_vllm_smoke.py` shells out to this path and `crossmodel.runlock`
matches on it when hunting orphaned processes that still hold VRAM.

    python crossmodel/vllm_tp2.py --plan P --design D --out O

is exactly

    python -m vllm_backend --plan P --design D --out O

Behaviour preserved verbatim: one uninterrupted generation (no stop string, no
splice), per-request scientific seeds, chunked appending, whole-run deadline
producing NOT_GENERATED rows, and the `_engine.json` provenance sidecar.

`DelimiterParser` and `split` moved to `vllm_backend.reasoning`; import them
from there.
"""
from __future__ import annotations

import sys
from pathlib import Path

# The backend package sits beside `crossmodel/` in `exploratory/`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vllm_backend.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
