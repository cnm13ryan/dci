"""Backups that are backups: only a fully admissible reference counts.

§13.15 asks for "families passing the full V(R) on the pooled calibration
and both splits >= 5: three core references plus two frozen backups". v7's
``support.evaluate_support`` counts ``qualified_families`` --- Gate 2.5's
list, which evaluates V_spec, V_sat, V_head, V_chance, V_struct and V_inter
on the pooled table and **no** V_stab and **no** V_diff --- and
``freeze_backups`` takes the first two unused families of that list in
sorted order, with no tier filter. On the twelve stored replications at
least one frozen backup is not an admissible core reference on eleven.

Here a backup is a family, not used in the core set, with a rung that
passes the **LOCAL** rule in full (``validity.local_validity``: every
registered component including the folded stability and V_diff), from a
tier the core slot admits. The count §13.15 registers is recomputed on that
basis and the Gate-2.5 count is reported beside it as what it is: the set
that was worth calibrating, not the set that could stand in.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from dci1v7.protocol import constants as C
from dci1v7.protocol.taxonomy import SLOT_ADMISSIBLE_TIERS, SLOT_CORE
from dci1v7.stages.calibration_table import CalibrationRow, tie_key
from dci1v7.stages.selection import _group_order, restrictiveness_key

__all__ = ["admissible_backups"]


def admissible_backups(local_verdicts: Mapping[str, Mapping[str, Any]],
                       pooled: Sequence[CalibrationRow], *, iota_a: float,
                       used_families: Sequence[str],
                       gate2_5_qualified: Sequence[str] = (),
                       recorded_backups: Sequence[str] = ()) -> dict[str, Any]:
    by_label = {r.label: r for r in pooled}
    tiers = SLOT_ADMISSIBLE_TIERS[SLOT_CORE]
    best: dict[str, dict[str, Any]] = {}
    for label, v in local_verdicts.items():
        if not v.get("passed"):
            continue
        row = by_label[label]
        if row.structural_tier not in tiers:
            continue
        entry = {"family": row.kind, "candidate": label, "iota": row.iota,
                 "distance": abs(row.iota - iota_a),
                 "structural_tier": row.structural_tier,
                 "feature_group": row.feature_group}
        cur = best.get(row.kind)
        if cur is None or (tie_key(entry["distance"]),
                           restrictiveness_key(row.kind, row.severity)) < (
                tie_key(cur["distance"]),
                restrictiveness_key(row.kind, by_label[cur["candidate"]].severity)):
            best[row.kind] = entry
    used = set(used_families)
    spare = sorted((e for f, e in best.items() if f not in used),
                   key=lambda e: (tie_key(e["distance"]), e["structural_tier"],
                                  _group_order(e["family"]), e["family"]))
    fully_admissible_families = sorted(best)
    n_required = C.MIN_QUALIFIED_FAMILIES
    recorded = list(recorded_backups)
    recorded_admissible = [f for f in recorded if f in best]
    return {
        "fully_admissible_families": fully_admissible_families,
        "n_fully_admissible": len(fully_admissible_families),
        "backups": [e["family"] for e in spare[:C.N_BACKUP_FAMILIES]],
        "backup_entries": spare[:C.N_BACKUP_FAMILIES],
        "n_spare_admissible": len(spare),
        "support_count_basis": "families with a rung passing the full LOCAL "
                               "rule (folded V_stab and V_diff included) "
                               "from a core-admissible tier",
        "meets_min_qualified": len(fully_admissible_families) >= n_required,
        "min_qualified": n_required,
        "gate2_5_qualified": sorted(set(gate2_5_qualified)),
        "n_gate2_5_qualified": len(set(gate2_5_qualified)),
        "recorded_backups": recorded,
        "recorded_backups_admissible": recorded_admissible,
        "recorded_backups_inadmissible": [f for f in recorded
                                          if f not in best],
    }
