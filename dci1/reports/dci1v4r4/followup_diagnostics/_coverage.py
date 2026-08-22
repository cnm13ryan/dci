"""Q5, second half: the §12.6 pre-screen coverage verdict for every model,
set beside what the independent 96-topic calibration then found.

Both sides are read from signed records: the coverage conditions and family
ranking from REGIME_SCREEN, the calibration verdicts from
02_admission_landscape.json (itself produced by the registered selection
functions). Nothing is re-screened. Writes 09_coverage_vs_calibration.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.models.registry import MODEL_KEYS
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record
from dci1v4r4.protocol import constants as C

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "09_coverage_vs_calibration.json"
LAND = json.loads((HERE / "02_admission_landscape.json").read_text())
ctx = registered_context()
rec = {"_provenance": "REGIME_SCREEN coverage verdicts and Gate-2 calibration "
                      "outcomes, both from signed records",
       "prescreen_scale": {"topics": C.N_PRESCREEN if hasattr(C, "N_PRESCREEN")
                           else 24, "draws_per_cell": 1,
                           "note": "§12.2's pre-screen measures the complete "
                                   "registered ladder at one draw per rung"},
       "calibration_scale": {"topics": C.N_SOLO, "draws_per_cell": C.M_CAL},
       "coverage_thresholds": {
           "COVERAGE_MIN_FAMILIES_PER_SIDE": C.COVERAGE_MIN_FAMILIES_PER_SIDE,
           "COVERAGE_MIN_STRADDLING_FAMILIES": C.COVERAGE_MIN_STRADDLING_FAMILIES,
           "COVERAGE_MIN_NEAR_FAMILIES": C.COVERAGE_MIN_NEAR_FAMILIES,
           "COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY":
               C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY,
           "COVERAGE_MIN_WITHIN_FAMILY_SPAN": C.COVERAGE_MIN_WITHIN_FAMILY_SPAN},
       "models": {}}
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    screen = read_stage_record(t, C.STAGE_REGIME)
    land = LAND["models"][m]
    exp = screen.get("expansion", {})
    cov = exp.get("coverage", {})
    # Two different pre-screen notions of "straddling", both reported:
    #   * C4's, over the COMPLETE registered ladder --- the registered
    #     coverage quantity, and the one the gate was decided on;
    #   * `family_ranking`'s, over the near set that feeds the shortlist.
    c4 = (cov.get("conditions", {}).get("C4_straddling_families", {})
          .get("observed", {}))
    prescreen_straddling = sorted(c4.get("straddling", []))
    prescreen_near_straddling = sorted(
        r["family"] for r in screen.get("family_ranking", [])
        if r.get("straddles"))
    cal_admitted = sorted(f for f, v in land["families"].items()
                          if v.get("admitted"))
    cal_straddling = sorted(f for f, v in land["families"].items()
                            if v.get("can_straddle_A"))
    rec["models"][m] = {
        "iota_a_prescreen": screen["iota_a_prescreen"],
        "iota_a_calibration": land["iota_a"],
        "iota_a_shift_prescreen_to_calibration":
            land["iota_a"] - screen["iota_a_prescreen"],
        "shortlist_sent_to_calibration": screen.get("shortlist"),
        "n_shortlisted_rungs": sum(len(v) for v in
                                   (screen.get("shortlist") or {}).values()),
        "prescreen_coverage_conditions": cov.get("conditions"),
        "prescreen_coverage_class_matched": cov.get("class_matched"),
        "prescreen_family_ranking": screen.get("family_ranking"),
        "prescreen_straddling_families_C4_full_ladder": prescreen_straddling,
        "n_prescreen_straddling_families_C4": len(prescreen_straddling),
        "prescreen_straddling_families_near_set": prescreen_near_straddling,
        "n_prescreen_straddling_families_near_set":
            len(prescreen_near_straddling),
        "calibration_admitted_families": cal_admitted,
        "calibration_straddling_families": cal_straddling,
        "n_calibration_straddling_families": len(cal_straddling),
        "n_core_references_admitted": land["n_core_references"],
        "design_variant": land["design_variant"],
        "collapse": {
            "families_straddling_at_prescreen_C4": len(prescreen_straddling),
            "families_straddling_at_prescreen_near_set":
                len(prescreen_near_straddling),
            "families_straddling_after_calibration": len(cal_straddling),
            "required": C.N_CORE_REFERENCES,
            "note": "the pre-screen ranks families at 24 topics x 1 draw; "
                    "Gate 2 re-measures the shortlist at 96 topics x "
                    f"{C.M_CAL} draws. A family counted as straddling at "
                    "pre-screen scale need not survive re-measurement."},
    }
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
