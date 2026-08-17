"""The masked-analysis entrypoint (Addendum A R42).

Accepts ONLY a masked-view root. It has no import, path constant, accessor or
utility through which the mask key or the permutation function is reachable:
nothing under ``dci1.analysis`` imports ``dci1.masking`` (tested by
`tests/test_addendum_masking_custody.py::test_no_analysis_module_imports_masking`),
and this module derives no path outside the root it is handed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dci1.analysis.run import analyze
from dci1.design.blocks import Block
from dci1.protocol.constants import ProtocolError


def run_masked_analysis(masked_view_root: Path, blocks: list[Block], *,
                        n: int, m: int, references: tuple[str, str, str],
                        bootstrap_seed_value: int,
                        n_resamples: int = 10_000) -> dict[str, Any]:
    root = Path(masked_view_root)
    rows_path = root / "masked_rows.jsonl"
    if not rows_path.exists():
        raise ProtocolError(f"no masked view at {rows_path}")
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()
            if line.strip()]
    for row in rows:
        row.setdefault("pool_index", 0)
    return analyze(rows, blocks, n=n, m=m, references=references,
                   bootstrap_seed_value=bootstrap_seed_value,
                   n_resamples=n_resamples, masked=True)
