"""POST-HOC DIAGNOSTIC. Not registered. Read-only.

Q4: Gate-4 composed-headroom anatomy for every replication, and the
trajectory of every selected companion from pre-screen through Gate-2
calibration and Gate-3 admission into Gate-4 composition.

Rates come from the signed Gate-4 record (surviving replications) or the
signed terminal report (terminated ones); calibration values from the signed
Gate-2 record; pre-screen values from the same calibration table's
pre-screen columns. Writes 03_gate4_anatomy.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.engine import fs
from dci1v4.models.registry import MODEL_KEYS
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record, terminal_status
from dci1v4r4.protocol import constants as C
from dci1v4r4.stages import selection as S

def _position(cell, slot, slot_map):
    if not cell.startswith("pair:"):
        return None
    body = cell[5:]
    names = sorted(slot_map, key=len, reverse=True)
    for first in names:
        if body.startswith(first + "+") and body[len(first) + 1:] in slot_map:
            second = body[len(first) + 1:]
            if slot == first:
                return 1
            if slot == second:
                return 2
            return None
    return None


OUT = pathlib.Path(__file__).resolve().parent / "03_gate4_anatomy.json"
ctx = registered_context()
lo, hi = C.COMPOSED_HEADROOM_BAND
rec = {"_provenance": "POST-HOC DIAGNOSTIC; every rate is read from a signed "
                      "record, none recomputed",
       "band": [lo, hi], "M_CAL": C.M_CAL,
       "n_composed_topics": len(__import__("dci1v4r4.topics", fromlist=["x"])
                                .split_topics()["composed"]),
       "models": {}}
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    term = terminal_status(t)
    if t.stage_record(C.STAGE_GATE4).exists():
        g4 = read_stage_record(t, C.STAGE_GATE4)
        table, outcome, failures = g4["table"], g4["outcome"], []
    else:
        p = fs.read_json(t.terminal_report); p = p.get("payload", p)
        table = p["table"]; outcome = "TERMINAL"; failures = p["failures"]
    g2 = read_stage_record(t, C.STAGE_GATE2)
    g3 = read_stage_record(t, C.STAGE_GATE3)
    rows = {r.label: r for r in S.load_calibration_table(g2["calibration_table"])}
    slot_map = dict(g3["slot_map"])
    slot_map["A"] = ["A", g2["n_star"]]; slot_map["B"] = ["B", g2["m_star"]]

    # every (cell, slot) rate, flagged against the band
    cells = []
    for cell, per_slot in sorted(table.items()):
        for slot, rate in sorted(per_slot.items()):
            fam, sev = (slot_map.get(slot) or [None, None])[:2]
            cells.append({
                "cell": cell, "slot": slot, "constraint":
                    (f"{fam}:{sev}" if fam else None),
                "composed_or_solo_rate": rate,
                "arm": ("solo" if cell.startswith("solo")
                        else "unconstrained" if cell == "unconstrained"
                        else "composed"),
                # `pair:{slot0}+{slot1}` where a slot name may itself end in
                # "+" (R3+), so a naive split on "+" mislabels the position.
                # Resolve against the known slot names instead.
                "position": _position(cell, slot, slot_map),
                "below_band": rate < lo, "above_band": rate > hi,
                "fails_band": rate < lo or rate > hi})
    # trajectory for every slot the design used
    traj = {}
    for slot, (fam, sev) in sorted(slot_map.items()):
        label = f"{fam}:{sev}"
        r = rows.get(label)
        g4_solo = table.get(f"solo:{slot}", {}).get(slot)
        composed = {c["cell"]: c["composed_or_solo_rate"] for c in cells
                    if c["slot"] == slot and c["arm"] == "composed"}
        traj[slot] = {
            "constraint": label, "family": fam, "severity": sev,
            "constraint_class": S.family_class(fam),
            "prescreen_solo_compliance": r.prescreen_solo_compliance if r else None,
            "prescreen_chance_compliance": r.prescreen_chance_compliance if r else None,
            "prescreen_iota": (r.prescreen_iota if r and r.prescreen_chance_compliance
                               < C.CHANCE_DEGENERACY_MAX else None),
            "calibration_solo_compliance": r.solo_compliance if r else None,
            "calibration_chance_compliance": r.chance_compliance if r else None,
            "calibration_iota": (r.iota if r and r.chance_compliance
                                 < C.CHANCE_DEGENERACY_MAX else None),
            "calibration_solo_vacuity": r.solo_vacuity if r else None,
            "calibration_median_words": r.median_words if r else None,
            "gate4_solo_compliance": g4_solo,
            "gate4_solo_minus_calibration_solo": (
                None if g4_solo is None or r is None
                else g4_solo - r.solo_compliance),
            "gate4_composed_rates": composed,
            "gate4_solo_fails_band": (None if g4_solo is None
                                      else g4_solo < lo or g4_solo > hi),
            "gate4_composed_cells_failing": sorted(
                k for k, v in composed.items() if v < lo or v > hi),
        }
    rec["models"][m] = {
        "gate4_outcome": outcome, "terminal_status": term,
        "n_cells_measured": len({c["cell"] for c in cells}),
        "n_rate_checks": len(cells),
        "n_failing": sum(1 for c in cells if c["fails_band"]),
        "registered_failures": failures,
        "design_variant": g3["design_variant"],
        "n_star": g2["n_star"], "m_star": g2["m_star"],
        "slot_map": slot_map,
        "cells": cells, "companion_trajectories": traj}
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
