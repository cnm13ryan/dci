"""POST-HOC DIAGNOSTIC. Not registered. Read-only.

Q5: the complete Gate-3 reference-admission landscape for all four models.

Every rung's verdict is produced by calling the REGISTERED selection
functions (`stages.selection.admit_family`, `eligible`,
`select_spectrum_triple`) on the signed Gate-2 calibration table. Nothing is
reimplemented, so a rejection reason here is the reason the study used.
Writes 02_admission_landscape.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.models.registry import MODEL_KEYS
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record
from dci1v4r4.protocol import constants as C
from dci1v4r4.stages import selection as S

OUT = pathlib.Path(__file__).resolve().parent / "02_admission_landscape.json"
ctx = registered_context()
rec = {"_provenance": "POST-HOC DIAGNOSTIC; verdicts computed by the registered "
                      "stages.selection functions on the signed Gate-2 table",
       "thresholds": {
           "REFERENCE_CALIPER": C.REFERENCE_CALIPER,
           "REFERENCE_PRESCREEN_CALIPER": C.REFERENCE_PRESCREEN_CALIPER,
           "REFERENCE_NEWCOMBE_REGION": C.REFERENCE_NEWCOMBE_REGION,
           "REFERENCE_VACUITY_MAX": C.REFERENCE_VACUITY_MAX,
           "CHANCE_DEGENERACY_MAX": C.CHANCE_DEGENERACY_MAX,
           "SPECTRUM_ELIGIBILITY_BAND": list(C.SPECTRUM_ELIGIBILITY_BAND),
           "SPECTRUM_OFFSET": C.SPECTRUM_OFFSET,
           "N_CORE_REFERENCES": C.N_CORE_REFERENCES,
           "N_SOLO": C.N_SOLO, "M_CAL": C.M_CAL},
       "models": {}}
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    g2 = read_stage_record(t, C.STAGE_GATE2)
    g3 = read_stage_record(t, C.STAGE_GATE3)
    screen = read_stage_record(t, C.STAGE_REGIME)
    rows = S.load_calibration_table(g2["calibration_table"])
    iota_a = g2["iota_a"]
    pre_a = screen["iota_a_prescreen"]
    solo_a = g2["a_solo_compliance"]
    families = sorted({r.kind for r in rows})
    fam_out = {}
    for fam in families:
        try:
            adm = S.admit_family(fam, rows, iota_a=iota_a,
                                 prescreen_iota_a=pre_a,
                                 solo_compliance_a=solo_a)
        except Exception as exc:                     # not a budget-class family
            fam_out[fam] = {"admitted": False, "refused_before_measurement":
                            f"{type(exc).__name__}: {exc}",
                            "constraint_class": S.family_class(fam)}
            continue
        rungs = []
        for r in [r for r in rows if r.kind == fam]:
            ok, reasons = S.eligible(r)
            cand = next((c for c in adm.rungs if c["severity"] == r.severity), {})
            lo, hi = S.newcombe_interval(r.solo_compliance, r.n_topics,
                                         solo_a, r.n_topics)
            rungs.append({
                "severity": r.severity, "label": r.label,
                "solo_compliance": r.solo_compliance,
                "chance_compliance": r.chance_compliance,
                "iota": (r.iota if r.chance_compliance < C.CHANCE_DEGENERACY_MAX
                         else None),
                "solo_vacuity": r.solo_vacuity,
                "prescreen_solo_compliance": r.prescreen_solo_compliance,
                "prescreen_chance_compliance": r.prescreen_chance_compliance,
                "prescreen_iota": (r.prescreen_iota
                                   if r.prescreen_chance_compliance
                                   < C.CHANCE_DEGENERACY_MAX else None),
                "prescreen_distance_from_A": (
                    abs(r.prescreen_iota - pre_a)
                    if r.prescreen_chance_compliance < C.CHANCE_DEGENERACY_MAX
                    else None),
                "distance_from_iota_A": cand.get("distance"),
                "newcombe_interval": [lo, hi],
                "median_words": r.median_words, "graded_mean": r.graded_mean,
                "wording_within_caliper": r.wording_within_caliper,
                "witnesses_pass": r.witnesses_pass,
                "parse_independent": r.parse_independent,
                "eligible_13_5": ok, "eligibility_reasons": reasons,
                "admissible_13_4": cand.get("admissible"),
                "rejection_reasons": cand.get("reasons", []),
            })
        triple = None
        if adm.admitted:
            triple = S.select_spectrum_triple(fam, rows,
                                              core_severity=adm.severity,
                                              iota_a=iota_a)
        fam_out[fam] = {
            "constraint_class": S.family_class(fam),
            "admitted": adm.admitted, "chosen_severity": adm.severity,
            "chosen_iota": adm.iota, "chosen_distance": adm.distance,
            "n_rungs_measured": len(rungs),
            "n_rungs_admissible": sum(1 for r in rungs if r["admissible_13_4"]),
            "can_straddle_A": triple is not None,
            "spectrum_triple": triple,
            "rungs": sorted(rungs, key=lambda r: r["severity"]),
        }
    rec["models"][m] = {
        "iota_a": iota_a, "prescreen_iota_a": pre_a, "a_solo_compliance": solo_a,
        "a_chance_compliance": g2["a_chance_compliance"],
        "design": g3["design"], "design_variant": g3["design_variant"],
        "core_references_admitted": g3["core_references"],
        "n_core_references": len(g3["core_references"]),
        "spectrum": g3["spectrum"],
        "spectrum_triples_available": g3["spectrum_triples"],
        "dropped_for_no_triple": g3["dropped_for_no_triple"],
        "identification_statuses": g3["identification_statuses"],
        "class_companion": g3["class_companion"],
        "families": fam_out,
    }
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
