"""Q6: the calibrated operating point of each of the four replications, from
signed Gate-2 / REGIME_SCREEN records only. Read-only, no new generation.

Neighbouring-rung values are reported only where they were actually
measured. No composed effect is estimated at any n or m whose cells were
never generated. Writes 07_operating_points.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.models.registry import MODEL_KEYS
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record
from dci1v4r4.protocol import constants as C
from dci1v4r4.protocol import wordings as W

OUT = pathlib.Path(__file__).resolve().parent / "07_operating_points.json"
ctx = registered_context()
rec = {"_provenance": "signed Gate-2 and REGIME_SCREEN records only",
       "focal_grid": list(C.FOCAL_GRID),
       "focal_extension": list(C.FOCAL_EXTENSION),
       "focal_band": list(C.FOCAL_BAND) if hasattr(C, "FOCAL_BAND") else None,
       "difficulty_coordinate": C.DIFFICULTY_COORDINATE,
       "models": {}}
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    g2 = read_stage_record(t, C.STAGE_GATE2)
    g3 = read_stage_record(t, C.STAGE_GATE3)
    screen = read_stage_record(t, C.STAGE_REGIME)
    n, mm = g2["n_star"], g2["m_star"]
    cl = g3["class_companion"]
    rec["models"][m] = {
        "n_star": n, "m_star": mm,
        "A_wording": W.wording("A", 0, n), "B_wording": W.wording("B", 0, mm),
        "completion_cap": screen["selected_cap"],
        "focal_extension_measured": bool(g2["focal"]["extension_measured"]),
        "focal_grid_used": g2["focal"]["grid_used"],
        "m_star_is_last_measured_rung":
            mm == max(g2["focal"]["grid_used"]),
        "B_solo_compliance_curve_by_m": g2["focal"]["curve"],
        "a_solo_compliance": g2["a_solo_compliance"],
        "a_chance_compliance": g2["a_chance_compliance"],
        "iota_a": g2["iota_a"],
        "b_solo_compliance": g2["b_solo_compliance"],
        "b_chance_compliance": g2["b_chance_compliance"],
        "iota_b": g2["iota_b"],
        "b_solo_vacuity": g2["b_solo_vacuity"],
        "prescreen_iota_a": screen["iota_a_prescreen"],
        "a_anchor": screen["a_anchor"],
        "graded_clause_reading": g2.get("graded_clause_reading"),
        "class_companion": cl,
        "class_companion_wording": W.wording(cl["family"], 0, cl["severity"]),
        "design_variant": g3["design_variant"],
        "core_references": [
            {**r, "wording": W.wording(r["family"], 0, r["severity"])}
            for r in g3["core_references"]],
        "spectrum": [
            {**r, "wording": W.wording(r["family"], 0, r["severity"])}
            for r in g3["spectrum"]],
        "truncation_by_cell_gate2": g2.get("truncation_by_cell"),
    }
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
