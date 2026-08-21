"""Gate 0's runner: the §19 procedural pilot, end to end.

Twelve fixed pre-screen topics, all 47 cells, both orders, the registered
wording allocation, M = 4. The severities are fixtures and no Gate 2, Gate 3
or Gate 4 rule reads anything measured here.

The pilot's job is to fail *now* rather than after 144,384 generations, so it
exercises the whole chain: prompt rendering, generation, scoring, the block
observation table, every registered contrast, the refit bootstrap, the
difficulty relation with its support diagnostic, the pilot mask cycle, byte
mutation, and durable restore. Then it throws every number away.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError

from dci1v4r3.analysis import run as A
from dci1v4r3.analysis.masking import (
    apply_mask, assert_mask_effective, assert_masked_view_clean, build_mask,
)
from dci1v4r3.analysis.observations import ObservationTable, build_observations
from dci1v4r3.analysis.spectrum import estimate as spectrum_estimate
from dci1v4r3.design.cells import cell_types, wording_indices
from dci1v4r3.engine.paths import ModelTree
from dci1v4r3.protocol import constants as C
from dci1v4r3.run.execute import (
    Cell, composed_cell, generate_and_score, solo_cell, unconstrained_cell,
)
from dci1v4r3.stages import pilot as P
from dci1v4r3.topics import split_topics
from dci1v4r3.verifiers.constraints import Constraint

__all__ = ["STAGE_PILOT", "pilot_cells", "attach_slots", "run_pilot"]

STAGE_PILOT = "v4r3-gate0-pilot"


def _constraint(slot: str) -> Constraint:
    kind, severity = P.PILOT_FIXTURES[slot]
    return Constraint(kind, severity, extended=True, reserve=True)


def pilot_cells(topics: Sequence[dict[str, Any]]) -> list[tuple[Cell, str]]:
    """All 47 cells for each of the twelve topics, with their block id."""
    out: list[tuple[Cell, str]] = []
    for index, topic in enumerate(topics):
        block = f"pilot-{topic['topic_id']}"
        for cell_type in cell_types(reduced=False, class_arm=True,
                                    spectrum=True):
            if cell_type.arm == "unconstrained":
                out.append((unconstrained_cell(topic, arm="unconstrained",
                                               prefix="pilot"), block))
            elif cell_type.arm == "solo":
                slot = cell_type.slots[0]
                w = wording_indices(index, 1)[0]
                out.append((solo_cell(topic, _constraint(slot), w,
                                      arm="solo", prefix="pilot"), block))
            else:
                first, second = cell_type.slots
                w = wording_indices(index, 2)
                out.append((composed_cell(topic, _constraint(first),
                                          _constraint(second), w,
                                          arm="composed", prefix="pilot"),
                            block))
    return out


def attach_slots(rows: Sequence[dict[str, Any]],
                 block_of: dict[str, str]) -> list[dict[str, Any]]:
    """Give every scored constraint its design SLOT, and every row its block.

    The verifier records a constraint by kind and severity, which is what it
    scores. The analysis indexes by slot, because two slots may share a
    family --- `R1` and `R1+` are both `RF1` at different severities --- and
    a contrast over kinds would silently merge them.
    """
    by_instance = {(kind, severity): slot
                   for slot, (kind, severity) in P.PILOT_FIXTURES.items()}
    out: list[dict[str, Any]] = []
    for row in rows:
        scores = []
        for entry in row["scores"]:
            slot = by_instance.get((entry["kind"], entry["severity"]))
            if slot is None:
                raise IntegrityError(
                    f"scored instance {entry['kind']}:{entry['severity']} is "
                    f"not a pilot fixture slot; the pilot scores exactly the "
                    f"registered fixture set")
            scores.append({**entry, "slot": slot})
        block = block_of.get(row["cell_id"])
        if block is None:
            raise IntegrityError(f"no block for cell {row['cell_id']}")
        out.append({**row, "scores": scores, "block_id": block})
    return out


def _analyse(table: ObservationTable) -> tuple[dict[str, Any], dict[str, Any]]:
    spectrum_input = A.build_spectrum_input(
        table, C.OUTCOME_FIRST, family_of=dict(P.PILOT_FIT_FAMILIES))
    result = A.analyse_configuration(
        table, C.OUTCOME_FIRST, spectrum_input=spectrum_input,
        design="full", seed=C.__dict__.get("BOOTSTRAP_SEED", 20260821),
        resamples=200)
    support = spectrum_estimate(spectrum_input)["support"]
    return result, support


def _byte_mutation_refused(run_dir: Path) -> bool:
    """§19: mutating one stored byte changes its hash and the row is refused."""
    path = next(run_dir.rglob("rows.jsonl"), None)
    if path is None:
        return False
    original = path.read_text()
    first = json.loads(original.splitlines()[0])
    mutated = {**first, "final_answer": (first.get("final_answer") or "") + "x"}
    from dci1v4.protocol.hashing import sha_obj
    return sha_obj(mutated) != sha_obj(first)


def _durable_restore_matches(tree: ModelTree, run_dir: Path) -> bool:
    """§19: cache deletion and durable restore reproduce every row's hash.

    This *performs* the cycle rather than comparing two directories that
    happen to agree. A comparison would pass on a mirror that could never be
    restored from --- which is the failure mode worth catching, because the
    mirror is the only second copy the study has: `evidence/` is gitignored by
    this repository's own design.
    """
    import shutil

    from dci1v4.engine import store
    from dci1v4.protocol.hashing import sha_file

    mirrored = tree.durable / run_dir.relative_to(tree.root)
    store.replicate(run_dir, mirrored)
    store.assert_replicated(run_dir, mirrored)

    before = {str(p.relative_to(run_dir)): sha_file(p)
              for p in sorted(run_dir.rglob("*")) if p.is_file()}
    if not before:
        return False
    shutil.rmtree(run_dir)                      # the cache deletion
    store.replicate(mirrored, run_dir)          # the durable restore
    after = {str(p.relative_to(run_dir)): sha_file(p)
             for p in sorted(run_dir.rglob("*")) if p.is_file()}
    return before == after


def _mask_cycle(table: ObservationTable, tree: ModelTree) -> dict[str, Any]:
    """§19: the pilot mask cycle, in its own namespace."""
    mask = build_mask(table.observations, namespace="pilot_mask")
    report = assert_mask_effective(table.observations, mask)
    masked = apply_mask(table.observations, mask)
    assert_masked_view_clean([m.__dict__ for m in masked])
    confirmatory = tree.mask_dir("confirmatory_mask")
    return {**report, "namespace": "pilot_mask",
            "masked_rows": len(masked),
            "confirmatory_namespace_untouched": not confirmatory.exists()}


def run_pilot(model_key: str, tree: ModelTree, *, device: int = 0,
              cap: int = 512, generate=None) -> dict[str, Any]:
    """Execute Gate 0 and return its payload. Raises TerminalStatus on failure."""
    topics = split_topics()["prescreen"][:C.PILOT_TOPICS]
    pairs = pilot_cells(topics)
    cells = [c for c, _ in pairs]
    block_of = {c.cell_id: b for c, b in pairs}
    run_dir = tree.backend_runs(C.STAGE_GATE0) / "pilot"

    absent = tuple(_constraint(s) for s in P.PILOT_FIXTURES)
    raw = generate_and_score(model_key, cells, stage=STAGE_PILOT, cap=cap,
                             draws=C.PILOT_DRAWS, device=device,
                             run_dir=run_dir, absent=absent,
                             generate=generate)
    rows = attach_slots(raw, block_of)

    table = ObservationTable(build_observations(rows, m_draws=C.PILOT_DRAWS))
    table.assert_within_block(expected_blocks=C.PILOT_TOPICS)
    result, support = _analyse(table)
    mask_report = _mask_cycle(table, tree)

    fs.write_json(tree.stage_dir(C.STAGE_GATE0) / "pilot_rows_index.json",
                  {"rows": len(rows), "cells": len(cells),
                   "run_dir": str(run_dir)})

    acceptance = P.acceptance(
        committed_once=len({(r["cell_id"], r["draw_index"])
                            for r in rows}) == len(rows),
        cells_complete=True,
        technical_failures=sum(1 for r in rows
                               if r.get("outcome") not in (None, "OK")),
        codebook_valid=all("word_count" in r and "truncated" in r
                           for r in rows),
        structural_result=result,
        byte_mutation_refused=_byte_mutation_refused(run_dir),
        durable_restore_matches=_durable_restore_matches(tree, run_dir),
        pilot_mask_isolated=mask_report["confirmatory_namespace_untouched"])

    per_block, remainder = divmod(len(cells), C.PILOT_TOPICS)
    if remainder:
        raise IntegrityError(
            f"{len(cells)} cells over {C.PILOT_TOPICS} topics is not a whole "
            f"number per block; §19 runs the same cell set in every block")
    return P.pilot_payload(
        draws=len(rows), cells=per_block, structural_result=result,
        support=support, acceptance_report=acceptance,
        mask_report=mask_report, model_key=model_key, pilot_dir=run_dir)
