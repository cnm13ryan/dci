"""Secondary sensitivity operations (items 21, 42, §22): the 1,000
pseudo-runs and the 96-block greedy replication.

Pseudo-runs perform zero model inference, use the separate frozen pseudo-run
seed domain, live on a separate derived path, never mutate primary
selection, and support no confirmatory claim.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from dci1v3.analysis.estimators import from_primary_rows
from dci1v3.engine import fs
from dci1v3.engine.dispatch import Job, operation
from dci1v3.errors import IntegrityError
from dci1v3.generation.cache import cache_rows, fill_cache, rows_by_cell
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import arm_cells, prompt_plan
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_file, sha_obj
from dci1v3.protocol.seeds import pseudo_run_index
from dci1v3.stages.confirmatory import confirmatory_cells, frozen_body
from dci1v3.topics.split import confirmatory_blocks


@operation("pseudo-runs", stage=None)
def run_pseudo(job: Job) -> dict[str, Any]:
    frozen, cells, _plan = confirmatory_cells(job)
    stage_dir = job.tree.data_dir("confirmatory")
    if not (stage_dir / "primary_rows.jsonl").exists():
        raise IntegrityError("pseudo-runs run after primary selection")
    grouped = rows_by_cell(cache_rows(stage_dir))
    n = int(frozen["n_star"])

    taus = {order: [] for order in C.ORDERS}
    runs = int(job.options.get("runs", C.PSEUDO_RUNS))
    for run in range(runs):
        rows = []
        for cell in cells:
            index = pseudo_run_index(C.PSEUDO_RUN_ROOT_SEED, run,
                                     job.spec.model_id,
                                     cell.prompt_hash) % cell.draws
            row = dict(grouped[cell.cell_id][index])
            row["non_behavioural"] = (
                not row["raw_response"].strip()
                or row["finish_reason"] == "length")
            row["failure_category"] = ""
            rows.append(row)
        table = from_primary_rows(rows, n=n)
        d = table.f["s0"][:, 0] - table.f["s0"][:, 1:4].mean(axis=1)
        for order in C.ORDERS:
            taus[order].append(float(d[table.stratum(order)].mean()))

    summary = {}
    for order in C.ORDERS:
        values = np.array(taus[order])
        summary[order] = {
            "runs": runs,
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if runs > 1 else None,
            "quantiles": {q: float(np.quantile(values, q / 100))
                          for q in (5, 25, 50, 75, 95)},
            "sign_positive_share": float((values > 0).mean()),
        }
    body = {"summary": summary, "separate_selection_domain": True,
            "primary_selection_untouched": True}
    fs.write_json_once(job.tree.root / "pseudo_runs.json", body)
    return {"status": "COMPLETED", "body": body,
            "input_hashes": {"cache": sha_file(stage_dir / "cache.jsonl")},
            "output_hashes": {"summary": sha_obj(summary)}}


@operation("greedy", stage=None)
def run_greedy(job: Job) -> dict[str, Any]:
    frozen = frozen_body(job)
    blocks = confirmatory_blocks()[:C.GREEDY_BLOCKS]
    cells = [c for c in arm_cells(
        "greedy", blocks, n=int(frozen["n_star"]),
        m=int(frozen["m_star"]),
        references=tuple((f, int(q))
                         for f, q in frozen["final_references"]),
        draws=1) if c.arm in C.PRIMARY_ARMS]
    if len(cells) != C.GREEDY_GENERATIONS:
        raise IntegrityError(f"{len(cells)} greedy cells, expected "
                             f"{C.GREEDY_GENERATIONS}")
    stage_dir = job.tree.data_dir("confirmatory") / "greedy"
    stage_dir.mkdir(parents=True, exist_ok=True)
    if not (stage_dir / "prompt_plan.json").exists():
        fs.write_json_once(stage_dir / "prompt_plan.json",
                           prompt_plan(cells))
    from dci1v3.stages.inference import generate_fn
    generate = generate_fn(job)
    fill_cache(stage_dir, cells, spec=job.spec, stage="greedy",
               generation_root=C.GENERATION_ROOT_SEED,
               plan=backend_plan(job.spec,
                                 cap=int(frozen["completion_cap"]),
                                 decoding="greedy"),
               generate_fn=generate, environment=job.environment)
    rows = cache_rows(stage_dir)
    n = int(frozen["n_star"])
    per_block: dict[str, dict[str, int]] = {}
    for row in rows:
        per_block.setdefault(row["block_id"], {})[row["arm"]] = \
            0 if row["verdicts"]["s0"] == n else 1
    d = [b["AB"] - (b["AR1"] + b["AR2"] + b["AR3"]) / 3
         for b in per_block.values() if len(b) == 4]
    body = {"generations": len(rows), "blocks": len(d),
            "mean_contrast": float(np.mean(d)) if d else None,
            "sign_positive_share": float(np.mean([x > 0 for x in d]))
            if d else None}
    fs.write_json_once(job.tree.root / "greedy_run.json", body)
    return {"status": "COMPLETED", "body": body,
            "input_hashes": {"block_plan": frozen["block_plan_hash"]},
            "output_hashes": {"greedy": sha_obj(body)}}
