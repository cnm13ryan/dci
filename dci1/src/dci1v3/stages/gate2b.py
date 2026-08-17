"""Gate 2B: composed-reference validation and reachability (§18.5, item 37).

Every eligible family runs as A+R_f on the independent 24-topic set with the
selected n* and q_f*. A+B is never generated or estimated. Composed target
failure in [0.15, 0.85] is an eligibility predicate only; the final three
are the composed-valid families with smallest solo distance from B, family
identifier breaking exact ties. Fewer than three returns
COMPOSED_HEADROOM_FAILURE.
"""
from __future__ import annotations

from typing import Any

from dci1v3.engine import fs
from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.signing import verify_signed
from dci1v3.engine.transitions import load_stage_record
from dci1v3.errors import ProtocolError, TerminalStatus
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import composed_cells, prompt_plan
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj
from dci1v3.topics.split import split_topics


def gate2a_payload(job: Job) -> dict[str, Any]:
    record = load_stage_record(job.tree, C.STAGE_GATE2A)
    if record is None:
        raise ProtocolError("Gate 2B requires the Gate 2A record")
    return verify_signed(record, job.context.signing_key_path,
                         where="gate2a_solo")["body"]


def _generate_fn(job: Job):
    if job.context.namespace == "synthetic":
        from dci1v3.generation.synthetic import synthetic_generate
        return synthetic_generate
    from dci1v3.generation.backend import run_backend
    return run_backend


@operation("gate2b", stage=C.STAGE_GATE2B)
def run_gate2b(job: Job) -> dict[str, Any]:
    gate2a = gate2a_payload(job)
    n_star, m_star = int(gate2a["n_star"]), int(gate2a["m_star"])
    cap = int(gate2a["cap"])
    admission = gate2a["admission_table"]
    eligible = list(gate2a["eligible_families"])
    split = split_topics()

    stage_dir = job.tree.data_dir("gate2b")
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    all_cells = []
    for family in eligible:
        q_star = int(admission[family]["selected"])
        cells = composed_cells("gate2b", split["composed"], n=n_star,
                               family=family, q=q_star,
                               draws=C.CALIBRATION_DRAWS_PER_CELL)
        all_cells.extend(cells)
    if not (stage_dir / "prompt_plan.json").exists():
        fs.write_json_once(stage_dir / "prompt_plan.json",
                           prompt_plan(all_cells))
    fill_cache(stage_dir, all_cells, spec=job.spec, stage="gate2b",
               generation_root=C.GENERATION_ROOT_SEED,
               plan=backend_plan(job.spec, cap=cap),
               generate_fn=_generate_fn(job),
               environment=job.environment)
    rows = cache_rows(stage_dir)

    composed_valid: list[tuple[float, str]] = []
    for family in eligible:
        family_rows = [r for r in rows if r["constraint_id"] == family]
        failures = sum(1 for r in family_rows
                       if r["verdicts"]["s0"] != n_star)
        rate = failures / len(family_rows)
        passes = C.COMPOSED_BAND[0] <= rate <= C.COMPOSED_BAND[1]
        results[family] = {
            "q_star": int(admission[family]["selected"]),
            "composed_target_failure": rate,
            "composed_valid": passes,
            "solo_distance": admission[family]["distance"]}
        if passes:
            composed_valid.append((admission[family]["distance"], family))
    if len(composed_valid) < C.N_FINAL_REFERENCES:
        raise TerminalStatus("COMPOSED_HEADROOM_FAILURE", {
            "criterion": "three composed-valid families in "
                         f"{C.COMPOSED_BAND}",
            "composed_results": results,
            "solo_matched_failures": [f for f, r in results.items()
                                      if not r["composed_valid"]]})

    final = sorted(composed_valid)[:C.N_FINAL_REFERENCES]
    references = [(family, results[family]["q_star"])
                  for _distance, family in final]
    body = {"n_star": n_star, "m_star": m_star, "cap": cap,
            "composed_results": results,
            "final_references": [list(r) for r in references]}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"gate2a_selection": sha_obj(
                {"n": n_star, "m": m_star})},
            "output_hashes": {"references": sha_obj(references)}}
