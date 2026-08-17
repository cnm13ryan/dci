"""Primary-draw selection (item 40/41): response-blind, frozen hash rule.

``primary_index_for_cell`` receives only the model identifier and the exact
prompt hash — response content and verifier outcomes are structurally
unavailable to the selector. Exactly one accepted primary observation exists
per logical cell; pseudo-run data can never replace a primary row.
"""
from __future__ import annotations

from typing import Any

from dci1v3.analysis.taxonomy import classify_failure
from dci1v3.errors import IntegrityError
from dci1v3.generation.cache import rows_by_cell
from dci1v3.generation.prompts import Cell
from dci1v3.protocol.seeds import primary_draw_index


def primary_index_for_cell(model_id: str, prompt_hash: str) -> int:
    """j_c = H("primary-root", model-id, prompt-hash) mod 16 — the selector
    reads nothing else."""
    return primary_draw_index(model_id, prompt_hash)


def _non_behavioural(row: dict[str, Any]) -> bool:
    if not row["raw_response"].strip():
        return True
    if row["finish_reason"] == "length":
        return True
    return "s0" not in row.get("verdicts", {})     # processing failure


def select_primary(cells: list[Cell], cache_rows: list[dict[str, Any]], *,
                   model_id: str) -> list[dict[str, Any]]:
    """One primary observation per cell, annotated with the deterministic
    §23 failure category and the §16 non-behavioural flag."""
    grouped = rows_by_cell(cache_rows)
    primaries: list[dict[str, Any]] = []
    for cell in cells:
        members = grouped.get(cell.cell_id)
        if members is None or set(members) != set(range(cell.draws)):
            raise IntegrityError(
                f"{cell.cell_id}: incomplete cache; primary selection runs "
                f"only over a complete verified cache")
        index = primary_index_for_cell(model_id, cell.prompt_hash) \
            % cell.draws
        row = dict(members[index])
        row["primary_index"] = index
        row["non_behavioural"] = _non_behavioural(row)
        verdicts = row["verdicts"]
        if cell.n is not None and verdicts["s0"] != cell.n:
            row["failure_category"] = classify_failure(
                response=row["raw_response"],
                finish_reason=row["finish_reason"],
                s0=verdicts["s0"], s2=verdicts["s2"], n=cell.n,
                instruction_text=" ".join(cell.active_wordings))
        else:
            row["failure_category"] = ""
        primaries.append(row)
    ids = [p["row_id"] for p in primaries]
    if len(set(ids)) != len(ids):
        raise IntegrityError("duplicate primary observations selected")
    return primaries
