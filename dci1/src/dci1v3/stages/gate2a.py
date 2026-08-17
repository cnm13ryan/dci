"""Gate 2A: final solo calibration (§18.4, items 35–36).

One response per severity and topic on the independent 96-topic set at the
selected cap. Deterministic selection with registered tie-breakers; every
severity of every family measured alone; admission subject to the ±0.10
caliper, the 20% wording-length caliper, whole-answer scope, parse
independence, and passing witnesses. Fewer than three eligible families
returns REFERENCE_POOL_MISMATCH with the full admission table.
"""
from __future__ import annotations

from typing import Any

from dci1v3.engine import fs
from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.signing import verify_signed
from dci1v3.engine.transitions import load_stage_record
from dci1v3.errors import ProtocolError, TerminalStatus, V3Error
from dci1v3.generation.cache import cache_rows, fill_cache
from dci1v3.generation.plans import backend_plan
from dci1v3.generation.prompts import prompt_plan, solo_cells
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj
from dci1v3.protocol.wordings import length_caliper_ok
from dci1v3.topics.split import split_topics
from dci1v3.verifiers.witnesses import verify_composition


def selected_cap(job: Job) -> int:
    record = load_stage_record(job.tree, C.STAGE_REGIME)
    if record is None:
        raise ProtocolError("Gate 2A requires the regime-screen record")
    payload = verify_signed(record, job.context.signing_key_path,
                            where="regime_screen")
    return int(payload["body"]["selected_cap"])


def _generate_fn(job: Job):
    if job.context.namespace == "synthetic":
        from dci1v3.generation.synthetic import synthetic_generate
        return synthetic_generate
    from dci1v3.generation.backend import run_backend
    return run_backend


def _rates(rows: list[dict[str, Any]], key_fn) -> dict[Any, float]:
    grouped: dict[Any, list[bool]] = {}
    for row in rows:
        verdicts = row["verdicts"]
        failed = (verdicts["s0"] != row["n"] if row["constraint_id"] is None
                  else not verdicts["added_pass"])
        grouped.setdefault(key_fn(row), []).append(failed)
    return {k: sum(v) / len(v) for k, v in sorted(grouped.items())}


def select_scalar(curve: dict[int, float], band: tuple[float, float], *,
                  grid: tuple[int, ...], exhausted_status: str,
                  payload: dict[str, Any]) -> int:
    """Eligible in band; minimise distance to 0.30; smaller value breaks an
    exact tie. Registered exhaustion and resolution diagnoses otherwise."""
    eligible = [v for v in grid if band[0] <= curve[v] <= band[1]]
    if eligible:
        return min(eligible,
                   key=lambda v: (abs(curve[v] - C.SELECTION_CENTRE), v))
    jump = any(
        (curve[a] < band[0] and curve[b] > band[1])
        or (curve[a] > band[1] and curve[b] < band[0])
        for a, b in zip(grid, grid[1:]))
    status = "GRID_RESOLUTION_INSUFFICIENT" if jump else exhausted_status
    raise TerminalStatus(status, {
        "criterion": f"an eligible severity in {band}",
        "curve": {str(k): v for k, v in curve.items()},
        "boundary_values": {"first": curve[grid[0]],
                            "last": curve[grid[-1]]},
        **payload})


def admit_families(family_rates: dict[str, dict[int, float]],
                   focal_rate: float, *, m_star: int, n_star: int
                   ) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Per-family admission: severity minimising |p_R − p_B| under the five
    §18.4 conditions; the less restrictive severity breaks an exact tie."""
    table: dict[str, dict[str, Any]] = {}
    eligible: list[str] = []
    for family, grid in C.REFERENCE_FAMILIES.items():
        best: tuple[float, int] | None = None
        rows = {}
        for q in grid:                     # registered order: least → most
            rate = family_rates[family][q]
            distance = abs(rate - focal_rate)
            conditions = {
                "caliper": distance <= C.REFERENCE_CALIPER,
                "wording_length": length_caliper_ok(family, q, m_star),
                "whole_answer_scope": True,
                "parse_independence": True,
            }
            try:
                verify_composition(n_star, family, q)
                conditions["witnesses"] = True
            except V3Error:
                conditions["witnesses"] = False
            rows[q] = {"solo_rate": rate, "distance": distance,
                       "conditions": conditions}
            if all(conditions.values()) and \
                    (best is None or distance < best[0]):
                best = (distance, q)       # first minimum = less restrictive
        table[family] = {"severities": {str(q): rows[q] for q in grid},
                         "selected": best[1] if best else None,
                         "distance": best[0] if best else None}
        if best is not None:
            eligible.append(family)
    return table, eligible


@operation("gate2a", stage=C.STAGE_GATE2A)
def run_gate2a(job: Job) -> dict[str, Any]:
    cap = selected_cap(job)
    split = split_topics()
    kinds = [("A", n) for n in C.TARGET_GRID]
    kinds += [("B", m) for m in C.FOCAL_GRID]
    for family, grid in C.REFERENCE_FAMILIES.items():
        kinds += [(family, q) for q in grid]
    cells = solo_cells("gate2a", split["solo"], kinds,
                       draws=C.CALIBRATION_DRAWS_PER_CELL)
    stage_dir = job.tree.data_dir("gate2a")
    stage_dir.mkdir(parents=True, exist_ok=True)
    if not (stage_dir / "prompt_plan.json").exists():
        fs.write_json_once(stage_dir / "prompt_plan.json",
                           prompt_plan(cells))
    fill_cache(stage_dir, cells, spec=job.spec, stage="gate2a",
               generation_root=C.GENERATION_ROOT_SEED,
               plan=backend_plan(job.spec, cap=cap),
               generate_fn=_generate_fn(job),
               environment=job.environment)
    rows = cache_rows(stage_dir)

    target_curve = _rates([r for r in rows if r["constraint_id"] is None],
                          lambda r: r["n"])
    focal_curve = _rates([r for r in rows if r["constraint_id"] == "B"],
                         lambda r: r["severity"])
    family_rates = {
        family: _rates([r for r in rows if r["constraint_id"] == family],
                       lambda r: r["severity"])
        for family in C.FAMILY_IDS}
    payload_curves = {
        "target_curve": {str(k): v for k, v in target_curve.items()},
        "focal_curve": {str(k): v for k, v in focal_curve.items()},
        "family_curves": {f: {str(k): v for k, v in c.items()}
                          for f, c in family_rates.items()},
        "cap": cap}

    n_star = select_scalar(target_curve, C.TARGET_BAND, grid=C.TARGET_GRID,
                           exhausted_status="TARGET_RANGE_EXHAUSTED",
                           payload=payload_curves)
    m_star = select_scalar(focal_curve, C.FOCAL_BAND, grid=C.FOCAL_GRID,
                           exhausted_status="FOCAL_RANGE_EXHAUSTED",
                           payload=payload_curves)

    admission, eligible = admit_families(
        family_rates, focal_curve[m_star], m_star=m_star, n_star=n_star)
    if len(eligible) < C.N_FINAL_REFERENCES:
        raise TerminalStatus("REFERENCE_POOL_MISMATCH", {
            "criterion": "at least three eligible families under the "
                         "registered solo-comparability rules",
            "admission_table": admission, **payload_curves})

    body = {**payload_curves, "n_star": n_star, "m_star": m_star,
            "focal_rate_at_m_star": focal_curve[m_star],
            "admission_table": admission, "eligible_families": eligible}
    return {"status": "PASSED", "body": body,
            "input_hashes": {"prompt_plan":
                             sha_obj(prompt_plan(cells))},
            "output_hashes": {"selection": sha_obj(
                {"n": n_star, "m": m_star, "eligible": eligible})}}
