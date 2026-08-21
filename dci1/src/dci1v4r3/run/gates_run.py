"""Gate 2 and Gate 3: the solo calibration, and what it selects.

**Everything these stages generate is a solo or unconstrained cell.** §12.5 and
§13.9 forbid a composed outcome reaching regime selection or reference
selection, and the way that is guaranteed here is structural: `calibration_cells`
can only build load-0 and load-1 cells, and `calibration_table` assembles
`CalibrationRow`, whose schema has no field a composed outcome could occupy.

Gate 2 fixes the regime --- `n*`, `m*`, and whether §7.2's focal extension was
needed --- from A's and B's own curves. Gate 3 admits the three core references,
the six spectrum rungs and the class companion from the shortlist §12.6 closed,
and decides the design variant. Neither reads an interference quantity, and
neither can: the only rows in scope carry one constraint or none.
"""
from __future__ import annotations


from typing import Any, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.errors import ProtocolError

from dci1v4r3.engine.paths import ModelTree
from dci1v4r3.protocol import constants as C
from dci1v4r3.run.execute import (
    Cell, cell_rates, generate_and_score, solo_cell, unconstrained_cell,
)
from dci1v4r3.stages import gates, selection
from dci1v4r3.topics import split_topics
from dci1v4r3.verifiers.constraints import (
    Constraint, FAMILIES, TARGET_GRID, focal_severities,
)

__all__ = ["STAGE_CALIBRATION", "calibration_cells", "calibration_table",
           "run_gate2", "run_gate3", "design_variant_for"]

STAGE_CALIBRATION = "v4r3-solo-calibration"


def calibration_cells(topics: Sequence[dict[str, Any]],
                      shortlist: Mapping[str, Sequence[int]], *,
                      focal_extension: bool) -> list[Cell]:
    """§12.3's measured set: load 0, the two grids, and the shortlist.

    Load 1 and load 0 only. There is no branch here that builds a composed
    cell, which is what makes "reads no composed outcome" a property of the
    code rather than a claim about it.
    """
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        index = position % C.N_WORDINGS
        cells.append(unconstrained_cell(topic, arm="load0", prefix="cal"))
        for n in TARGET_GRID:
            cells.append(solo_cell(topic, Constraint("A", n), index,
                                   arm="A", prefix="cal"))
        for m in focal_severities(extended=focal_extension):
            cells.append(solo_cell(topic, Constraint("B", m,
                                                     extended=True),
                                   index, arm="B", prefix="cal"))
        for family, rungs in sorted(shortlist.items()):
            for q in rungs:
                cells.append(solo_cell(
                    topic, Constraint(family, q, reserve=True), index,
                    arm=FAMILIES[family].role, prefix="cal"))
    return cells


def calibration_table(rows: Sequence[Mapping[str, Any]],
                      shortlist: Mapping[str, Sequence[int]],
                      prescreen: Mapping[str, Mapping[str, Any]], *,
                      wording_caliper: Mapping[str, bool],
                      witnesses: Mapping[str, bool]) -> list[dict[str, Any]]:
    """§13.9's selection input, one row per shortlisted severity."""
    table: list[dict[str, Any]] = []
    for family, rungs in sorted(shortlist.items()):
        for q in rungs:
            label = f"{family}:{q}"
            measured = cell_rates(rows, kind=family, severity=q)
            pre = prescreen.get(label)
            if pre is None:
                raise ProtocolError(
                    f"§13.4 condition 2 reads the disjoint pre-screen value "
                    f"for {label} and the regime record carries none")
            table.append({
                "kind": family, "severity": q,
                "solo_compliance": measured["solo"],
                "chance_compliance": measured["chance"],
                "solo_vacuity": measured["vacuity"],
                "prescreen_solo_compliance": pre["solo"],
                "prescreen_chance_compliance": pre["chance"],
                "wording_within_caliper": bool(wording_caliper.get(label,
                                                                   False)),
                "witnesses_pass": bool(witnesses.get(family, False)),
                "median_words": measured.get("median_words"),
                "graded_mean": measured.get("graded_mean"),
            })
    return table


def run_gate2(model_key: str, tree: ModelTree, *, regime_record: Mapping,
              device: int = 0, generate=None) -> dict[str, Any]:
    """§12.3's selection and §12.4's adequacy, on the 96 calibration topics."""
    topics = split_topics()["solo"]
    shortlist = dict(regime_record["shortlist"])
    extension = bool(regime_record.get("focal_extension_measured"))
    cells = calibration_cells(topics, shortlist, focal_extension=extension)
    run_dir = tree.backend_runs(C.STAGE_GATE2) / "calibration"
    absent = (tuple(Constraint("A", n) for n in TARGET_GRID)
              + tuple(Constraint("B", m, extended=True)
                      for m in focal_severities(extended=True))
              + tuple(Constraint(f, q, reserve=True)
                      for f, rungs in shortlist.items() for q in rungs))
    rows = generate_and_score(model_key, cells, stage=STAGE_CALIBRATION,
                              cap=regime_record["selected_cap"],
                              draws=C.M_CAL, device=device, run_dir=run_dir,
                              absent=absent, generate=generate)
    fs.write_json(tree.stage_dir(C.STAGE_GATE2) / "calibration_rows.json",
                  {"rows": len(rows), "run_dir": str(run_dir)})

    a_curve = {n: cell_rates(rows, kind="A", severity=n)["solo"]
               for n in TARGET_GRID}
    registered = {m: cell_rates(rows, kind="B", severity=m)["solo"]
                  for m in focal_severities()}
    extended = ({m: cell_rates(rows, kind="B", severity=m)["solo"]
                 for m in focal_severities(extended=True)}
                if extension else None)
    b_vacuity = max(cell_rates(rows, kind="B", severity=m)["vacuity"]
                    for m in focal_severities(extended=extension))
    graded = {kind: [r["scores"][0]["graded"] for r in rows
                     if r["scores"] and r["scores"][0]["kind"] == kind
                     and r["scores"][0]["present"]]
              for kind in ("A", "B")}
    payload = gates.gate2_payload(
        a_curve=a_curve, focal_registered_curve=registered,
        focal_extended_curve=extended, b_solo_vacuity=b_vacuity,
        graded_distributions=graded,
        a_chance=cell_rates(rows, kind="A", severity=TARGET_GRID[0])["chance"],
        b_chance=cell_rates(rows, kind="B",
                            severity=min(focal_severities()))["chance"],
        truncation_by_cell={})
    return {**payload, "model_key": model_key,
            "calibration_rows": len(rows),
            "reads_no_composed_cell": True}


def design_variant_for(result: Any) -> str:
    """§8.6: the variant a Gate 3 outcome puts in force.

    Never chosen from a composed effect --- none exists at this stage and none
    may. Fewer than three admitted core references gives the reduced design; a
    coverage failure withholds `delta_difficulty` and gives the no-spectrum
    design, which keeps `Delta_R`, `Xi`, `Lambda` and the reciprocal matrix.
    """
    if len(getattr(result, "core_references", ()) or ()) < C.N_CORE_REFERENCES:
        return "reduced"
    if not getattr(result, "spectrum", None):
        return "no_spectrum"
    return "full"


def run_gate3(model_key: str, tree: ModelTree, *, gate2_record: Mapping,
              regime_record: Mapping, calibration: Sequence[Mapping[str, Any]]
              ) -> dict[str, Any]:
    """§13.4, §13.6 and §13.7, from the solo calibration table alone."""
    rows = selection.load_calibration_table(calibration)
    result = selection.select_all(rows, iota_a=gate2_record["iota_a"])
    payload = gates.gate3_payload(result)
    variant = design_variant_for(result)
    return {**payload, "model_key": model_key, "design_variant": variant,
            "reads_no_composed_cell": True,
            "variant_rule": ("§8.6, decided by reference admission and "
                             "§12.6 coverage only; no composed effect exists "
                             "at this stage and none may be read")}
