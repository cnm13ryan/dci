"""Synthetic row builder shared by the pre-freeze check runner.

Not part of the dci1v4 package and never a source of scientific values: it
builds a structurally complete synthetic confirmatory row set so that
executable structural checks (C16) can run without a GPU.
"""
from __future__ import annotations

import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

SLOT_MAP = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 2), "R2": ("RF5", 4),
            "R3": ("RF7", 6)}


def synthetic_confirmatory_rows(blocks: int = 8) -> list[dict]:
    import tempfile

    from dci1v4 import SYNTHETIC_STUDY_ID
    from dci1v4.design.cells import design_cells
    from dci1v4.generation.backend import build_plan
    from dci1v4.generation.cache import cache_rows, fill_cache
    from dci1v4.generation.synthetic import synthetic_generate
    from dci1v4.models.registry import get_model
    from dci1v4.topics.split import confirmatory_blocks, split_topics

    spec = get_model("gemma-3n-e2b-it")
    cells = design_cells("confirmatory",
                         confirmatory_blocks(split_topics())[:blocks],
                         SLOT_MAP, draws=4)
    with tempfile.TemporaryDirectory() as tmp:
        stage_dir = Path(tmp) / "confirmatory"
        fill_cache(stage_dir, cells, spec=spec, stage="confirmatory",
                   slot_map=SLOT_MAP, study_id=SYNTHETIC_STUDY_ID,
                   plan=build_plan(spec, stage="confirmatory",
                                   max_new_tokens=768),
                   generate_fn=synthetic_generate,
                   environment={"python_executable": "python",
                                "dependency_digest": "d"})
        return cache_rows(stage_dir)
