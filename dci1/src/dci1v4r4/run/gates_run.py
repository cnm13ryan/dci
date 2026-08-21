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

from dci1v4r4.engine.paths import ModelTree
from dci1v4r4.protocol import constants as C
from dci1v4r4.run.execute import (
    Cell, generate_and_score, instance_rates, solo_cell,
    unconstrained_cell,
)
from dci1v4r4.stages import gates, selection
from dci1v4r4.topics import split_topics
from dci1v4r4.stages.gates import select_focal_severity
from dci1v4r4.verifiers.constraints import (
    Constraint, FAMILIES, FOCAL_EXTENSION, TARGET_GRID, focal_severities,
)

__all__ = ["STAGE_CALIBRATION", "STAGE_HEADROOM", "calibration_cells",
           "calibration_table", "run_gate2", "run_gate3", "run_gate4",
           "design_variant_for", "full_slot_map"]

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


def focal_extension_cells(topics: Sequence[dict[str, Any]]) -> list[Cell]:
    """§7.2's two rungs on the same 96 topics, and nothing else.

    A second design rather than a wider `calibration_cells`, for a reason that
    is about evidence and not tidiness: widening the registered design changes
    every row identity in it, and `_reusable_rows` would then redraw all
    17,280 registered generations in order to add 768. The topic order, the
    §8.4 wording index, the arm and the cell-id prefix are the ones
    `calibration_cells` uses, so each extension row has exactly the identity it
    would have had inside a widened design --- same prompt, same scientific
    seed --- and §12.3's union is measured on the same 96 topics the
    registered pass used, which is what §12.3 requires of it.

    Chance for m = 11 and m = 12 is *not* measured again: the registered pass
    already scores both against its load-0 rows under §25, so the union reads
    its present arm here and its absent arm there.
    """
    cells: list[Cell] = []
    for position, topic in enumerate(topics):
        index = position % C.N_WORDINGS
        for m in FOCAL_EXTENSION:
            cells.append(solo_cell(topic, Constraint("B", m, extended=True),
                                   index, arm="B", prefix="cal"))
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
            measured = instance_rates(rows, kind=family, severity=q)
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
    cells = calibration_cells(topics, shortlist, focal_extension=False)
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

    a_curve = {n: instance_rates(rows, kind="A", severity=n)["solo"]
               for n in TARGET_GRID}
    registered = {m: instance_rates(rows, kind="B", severity=m)["solo"]
                  for m in focal_severities()}

    # §7.2's escalation, decided here and nowhere else. `focal_severities`
    # says it: "only §12.3 sets it, and only when the registered grid supplies
    # no eligible severity". The flag used to be read off the regime record,
    # which no code path has ever written --- so a replication whose
    # registered grid was exhausted could only ever return
    # PENDING_FOCAL_EXTENSION, with no way forward. §12.3 registers the way
    # forward: measure {11, 12} on the same 96 topics, 768 generations, and
    # select over the union.
    extended: dict[int, float] | None = None
    extension_rows: list[dict[str, Any]] = []
    if select_focal_severity(registered)["m_star"] is None:
        extension_rows = generate_and_score(
            model_key, focal_extension_cells(topics), stage=STAGE_CALIBRATION,
            cap=regime_record["selected_cap"], draws=C.M_CAL, device=device,
            run_dir=tree.backend_runs(C.STAGE_GATE2) / "focal_extension",
            generate=generate)
        union_rows = [*rows, *extension_rows]
        extended = {m: instance_rates(union_rows, kind="B",
                                      severity=m)["solo"]
                    for m in FOCAL_EXTENSION}
    extension = extended is not None
    vacuity_rows = [*rows, *extension_rows]
    b_vacuity = max(instance_rates(vacuity_rows, kind="B",
                                   severity=m)["vacuity"]
                    for m in focal_severities(extended=extension))
    graded = {kind: [r["scores"][0]["graded"] for r in vacuity_rows
                     if r["scores"] and r["scores"][0]["kind"] == kind
                     and r["scores"][0]["present"]]
              for kind in ("A", "B")}
    payload = gates.gate2_payload(
        a_curve=a_curve, focal_registered_curve=registered,
        focal_extended_curve=extended, b_solo_vacuity=b_vacuity,
        graded_distributions=graded,
        a_chance=instance_rates(rows, kind="A",
                                severity=TARGET_GRID[0])["chance"],
        b_chance=instance_rates(rows, kind="B",
                                severity=min(focal_severities()))["chance"],
        truncation_by_cell={})
    if payload.get("outcome") != "PASS":
        return {**payload, "model_key": model_key,
                "calibration_rows": len(rows) + len(extension_rows)}

    # §13.9's selection input, built here because it is a function of the same
    # solo rows and of nothing else. Building it in Gate 3 would mean reading
    # Gate 2's rows again from disk after Gate 2 closed, and the table is the
    # only thing Gate 3 needs from them.
    table = calibration_table(
        rows, shortlist,
        prescreen={label: {"solo": entry["solo"], "chance": entry["chance"]}
                   for label, entry in regime_record["difficulty_table"].items()},
        wording_caliper=_wording_caliper(shortlist, payload["n_star"]),
        witnesses=_witness_pass(shortlist))
    return {**payload, "model_key": model_key,
            "calibration_rows": len(rows) + len(extension_rows),
            "focal_extension_rows": len(extension_rows),
            "calibration_table": table,
            "reads_no_composed_cell": True}


def _wording_caliper(shortlist: Mapping[str, Sequence[int]],
                     n_star: int) -> dict[str, bool]:
    """§13.4 condition 3, per shortlisted rung, against A at n*."""
    from dci1v4r4.protocol.wordings import length_caliper_ok
    return {f"{family}:{q}": length_caliper_ok(family, q, n_star)
            for family, rungs in shortlist.items() for q in rungs}


def _witness_pass(shortlist: Mapping[str, Sequence[int]]) -> dict[str, bool]:
    """§7.5's witnesses, per shortlisted family.

    The suite is discharged over the whole registered population at Gate 1 and
    is re-derived here for exactly the families §12.3 shortlisted, so a family
    that lost its witnesses between the two stages cannot be admitted on the
    strength of an earlier run.
    """
    from dci1v4r4.verifiers.witnesses import realisable_pairs, run_witness_suite
    families = set(shortlist)
    pairs = [(a, b) for a, b in realisable_pairs()
             if a.kind in families or b.kind in families]
    report = run_witness_suite(pairs)
    broken = {label.split("+")[0].split(":")[0]
              for label in (report["joint_satisfiability_failures"]
                            + report["non_entailment_failures"])}
    broken |= {label.split("+")[1].split(":")[0]
               for label in (report["joint_satisfiability_failures"]
                             + report["non_entailment_failures"])}
    return {family: family not in broken for family in families}


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
    """§13.4, §13.6 and §13.7, from the solo calibration table alone.

    Three quantities enter and all three come from a stage that has already
    closed: `iota_A` and `A`'s solo compliance from Gate 2's own record, and
    the disjoint pre-screen `iota_A` from the regime screen. §13.4 condition 2
    is stated over the pre-screen value precisely so that admission does not
    rest on the same measurement twice.
    """
    rows = selection.load_calibration_table(calibration)
    result = selection.select_all(
        rows, iota_a=gate2_record["iota_a"],
        prescreen_iota_a=regime_record["iota_a_prescreen"],
        solo_compliance_a=gate2_record["a_solo_compliance"])
    payload = gates.gate3_payload(result)
    variant = design_variant_for(result)
    return {**payload, "model_key": model_key, "design_variant": variant,
            "reads_no_composed_cell": True,
            "variant_rule": ("§8.6, decided by reference admission and "
                             "§12.6 coverage only; no composed effect exists "
                             "at this stage and none may be read")}


# ------------------------------------------------------------------ Gate 4
STAGE_HEADROOM = "v4r3-composed-headroom"


def run_gate4(model_key: str, tree: ModelTree, *, gate2_record: Mapping,
              gate3_record: Mapping, regime_record: Mapping,
              device: int = 0, generate=None) -> dict[str, Any]:
    """§13.10: every registered cell type, on the 24 composed topics, M_cal.

    A viability predicate and nothing else. It runs *after* Gate 3 has fixed
    the spectrum and the class companion, and a failure is terminal for the
    replication rather than an instruction to choose different rungs --- which
    is why this function computes no contrast, ranks nothing, and hands
    `gate4_payload` a table of per-cell per-slot rates with no ordering in it.
    """
    from dci1v4r4.run.design_run import (
        absent_instances, attach_slots, design_cells_for,
    )

    slot_map = full_slot_map(gate2_record, gate3_record)
    variant = gate3_record["design_variant"]
    topics = split_topics()["composed"]
    pairs = design_cells_for(topics, slot_map, variant=variant,
                             prefix="headroom", block_prefix="headroom")
    cells = [c for c, _, _ in pairs]
    block_of = {c.cell_id: b for c, b, _ in pairs}
    design_cell_of = {c.cell_id: d for c, _, d in pairs}
    run_dir = tree.backend_runs(C.STAGE_GATE4) / "headroom"
    rows = generate_and_score(model_key, cells, stage=STAGE_HEADROOM,
                              cap=regime_record["selected_cap"],
                              draws=C.M_CAL, device=device, run_dir=run_dir,
                              absent=absent_instances(slot_map),
                              generate=generate)
    rows = attach_slots(rows, block_of, slot_map, design_cell_of)

    # cell type -> slot -> compliance, over the stated constraints only.
    tally: dict[str, dict[str, list[int]]] = {}
    for row in rows:
        cell_type = row["design_cell_id"]
        for score in row["scores"]:
            if not score["present"]:
                continue
            tally.setdefault(cell_type, {}).setdefault(
                score["slot"], []).append(int(score["passed"]))
    rates_by_cell = {cell: {slot: sum(v) / len(v)
                            for slot, v in by_slot.items()}
                     for cell, by_slot in tally.items()}
    payload = gates.gate4_payload(rates_by_cell)
    return {**payload, "model_key": model_key, "rows": len(rows),
            "cells": len(cells), "design_variant": variant,
            "topic_set": "composed", "draws": C.M_CAL,
            "run_dir": str(run_dir)}


def full_slot_map(gate2_record: Mapping, gate3_record: Mapping
                  ) -> dict[str, tuple[str, int]]:
    """§13's slot map plus the two outcome slots Gate 2 fixed.

    Gate 3 decides the companions; `A` and `B` are not companions and are not
    in its map. Every stage downstream needs all of them, and assembling that
    union in one place is what stops Gate 4 and the confirmatory run from
    disagreeing about which severity `A` is.
    """
    out: dict[str, tuple[str, int]] = {
        "A": ("A", int(gate2_record["n_star"])),
        "B": ("B", int(gate2_record["m_star"]))}
    for slot, entry in dict(gate3_record["slot_map"]).items():
        kind, severity = (entry["family"], entry["severity"]) \
            if isinstance(entry, Mapping) else tuple(entry)
        out[slot] = (kind, int(severity))
    return out
