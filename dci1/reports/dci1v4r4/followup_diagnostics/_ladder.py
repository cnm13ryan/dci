"""Q8: the claim-ladder audit table, and the scope of the L4 defect.

Every row is copied from the signed UNMASKED_ANALYSIS record. The frozen L4
artifact is NOT recomputed or repaired: what is added is a read-only
re-reading of §3.2's per-member gate from the record's own statements, so a
reader can see which emitted L4 statements the defect invalidates and which
lower-level estimates are untouched. Writes 08_claim_ladder_audit.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record
from dci1v4r4.protocol import constants as C

OUT = pathlib.Path(__file__).resolve().parent / "08_claim_ladder_audit.json"
SURVIVORS = ("qwen3-4b", "gemma-3n-e4b-it")
ctx = registered_context()

NOT_IDENTIFIED_REDUCED = ("D(B<-R_j)", "D(R_j<-B)", "Delta_j", "Delta_R",
                          "delta_difficulty", "Xi")

rec = {"_provenance": "rows copied from signed UNMASKED_ANALYSIS records; the "
                      "L4 re-reading is read-only and does not touch the "
                      "frozen artifact",
       "claim_levels": list(C.CLAIM_LEVELS),
       "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
       "l4_defect": {
           "what_it_does": "analysis.claims.emit_l4 compares the SET of claim "
                           "levels reached in each configuration. "
                           "run/analysis_run.py builds that input as "
                           "[s['claim_level'] for s in statements if emitted], "
                           "discarding the member identity before the emitter "
                           "sees it.",
           "registered_rule": "§3.2 licenses L1 on 'the named D(c <- g)', and "
                              "§28.1 pairs Replication ('the same "
                              "classification in every registered "
                              "configuration') with Configuration dependence "
                              "('the quantity is configuration-dependent; the "
                              "table is reported and no pooled scalar is "
                              "quoted'). Both rows are about a NAMED quantity, "
                              "so the gate is per member.",
           "failure_mode": "when the members that reach a level swap places "
                           "across configurations, the level sets match and "
                           "L4 emits, asserting replication for a result that "
                           "is configuration-dependent.",
           "scope": "L4 only. It reads emitted statements; it does not enter "
                    "any estimate, interval, bootstrap draw, precision "
                    "check, F6 gate, or L1/L2/L3 licensing decision.",
           "why_not_repaired": "run_unmasked_analysis refuses an unmasked "
                               "analysis under an analysis_code_hash differing "
                               "from the masked seal, and §20 forbids "
                               "regenerating a mask after semantic identities "
                               "are known."},
       "models": {}}
for model in SURVIVORS:
    t = model_tree(ctx, model)
    final = read_stage_record(t, C.STAGE_UNMASKED_ANALYSIS)
    freeze = read_stage_record(t, C.STAGE_GATE5)
    rows = []
    for cfg, e in sorted(final["result"].items()):
        prec = e.get("precision", {})
        for fam, f in sorted(e["families"].items()):
            for name, mem in sorted(f["members"].items()):
                key = f"{fam}:{name}"
                p = prec.get(key)
                st = [s for s in final["claims"].get(cfg, {}).get("statements", [])
                      if s.get("family") == fam and s.get("member") == name]
                rows.append({
                    "configuration": cfg, "family": fam, "estimand": name,
                    "estimate": mem["estimate"], "se": mem["se"],
                    "marginal_95": mem["marginal"],
                    "simultaneous": mem["simultaneous"],
                    "half_width": mem["half_width"],
                    "degenerate": mem["degenerate"],
                    "multiplicity": {
                        "critical_value": f["critical_value"],
                        "sidak_reference": f["sidak_reference"],
                        "family_size": len(f["members"]),
                        "interval_reported_as": "simultaneous"},
                    "precision_precondition": p,
                    "excludes_zero_simultaneous":
                        mem["simultaneous"][0] > 0 or mem["simultaneous"][1] < 0,
                    "claim_statements": [
                        {"claim_level": s.get("claim_level"),
                         "emitted": s.get("emitted"), "reason": s.get("reason"),
                         "identification_status": s.get("identification_status"),
                         "statement": s.get("statement")} for s in st],
                })
    # read-only re-reading of §3.2's per-member L4 gate
    per = {}
    for cfg, e in final["claims"].items():
        if cfg == "L4":
            continue
        for s in e.get("statements", []):
            if s.get("member") is None:
                continue
            per.setdefault(f"{s.get('family')}:{s['member']}", {})[cfg] = (
                s.get("claim_level") if s.get("emitted") else None)
    differing = sorted(k for k, v in per.items() if len(set(v.values())) > 1)
    replicating = sorted(k for k, v in per.items()
                         if len(set(v.values())) == 1 and next(iter(v.values())))
    emitted_l4 = final["claims"].get("L4", {})
    rec["models"][model] = {
        "design_variant": freeze["design_variant"],
        "identification_statuses": freeze["identification_statuses"],
        "not_identified_by_this_design": list(NOT_IDENTIFIED_REDUCED)
            if freeze["design_variant"] == "reduced" else [],
        "measurement_basis": final["measurement_basis"],
        "scope_sentence": final["scope_sentence"],
        "rows": rows,
        "L1_L2_L3_statements": {cfg: final["claims"][cfg]["statements"]
                                for cfg in final["claims"] if cfg != "L4"},
        "L4_as_emitted": emitted_l4,
        "L4_reread_per_member_READ_ONLY": {
            "classification_by_member": per,
            "members_differing_across_configurations": differing,
            "members_replicating": replicating,
            "licensed_by_the_registered_per_member_gate":
                bool(replicating) and not differing,
            "emitted_field_is_invalidated":
                emitted_l4.get("emitted") is True and bool(differing),
            "registered_reading":
                "Replication (§28.1)" if (replicating and not differing)
                else "Configuration dependence (§28.1): the quantity is "
                     "configuration-dependent; the table is reported and no "
                     "pooled scalar is quoted"},
    }
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
