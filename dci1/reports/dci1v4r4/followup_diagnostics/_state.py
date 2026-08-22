"""POST-HOC DIAGNOSTIC. Not registered. Read-only.

Dumps the final v4r4 lifecycle state for every model from signed records.
Writes followup_diagnostics/01_final_state.json.
"""
import json, sys, pathlib
DCI1 = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DCI1 / "src"))
from dci1v4.engine import fs
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4r4.engine.context import registered_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.engine.transitions import read_stage_record, stage_reached, terminal_status
from dci1v4r4.protocol import constants as C

OUT = pathlib.Path(__file__).resolve().parent / "01_final_state.json"
ctx = registered_context()
rec = {"_provenance": "POST-HOC DIAGNOSTIC, read-only, not preregistered",
       "stage_sequence": list(C.STAGE_SEQUENCE), "models": {}}
for m in MODEL_KEYS:
    t = model_tree(ctx, m)
    spec = get_model(m)
    e = {"model_id": spec.model_id, "model_revision": spec.revision,
         "stage_reached": stage_reached(t), "terminal_status": terminal_status(t),
         "records_present": [s for s in C.STAGE_SEQUENCE if t.stage_record(s).exists()]}
    if t.terminal_report.exists():
        p = fs.read_json(t.terminal_report); e["terminal_report"] = p.get("payload", p)
    for stage, keys in [
        (C.STAGE_REGIME, ("selected_cap", "iota_a_prescreen", "a_anchor")),
        (C.STAGE_GATE2, ("n_star", "m_star", "iota_a", "iota_b", "a_solo_compliance",
                         "b_solo_compliance", "a_chance_compliance",
                         "b_chance_compliance", "b_solo_vacuity", "focal",
                         "difficulty_coordinate")),
        (C.STAGE_GATE3, ("design", "design_variant", "cells_per_block",
                         "core_references", "spectrum", "class_arm",
                         "class_companion", "slot_map", "identification_statuses",
                         "spectrum_triples", "dropped_for_no_triple", "variant_rule")),
        (C.STAGE_GATE4, ("outcome", "band", "failures", "cells_checked")),
        (C.STAGE_GATE5, ("outcome", "producing_commit", "canonical_verifier_hash",
                         "blocks", "m_draws", "completion_cap", "design_variant",
                         "focal_extension_measured", "identification_statuses")),
        (C.STAGE_CONFIRMATORY, ("outcome", "rows", "blocks_generated", "completeness")),
        (C.STAGE_MASKED_ANALYSIS, ("masked_artifact_hash", "mask_key_hash",
                          "analysis_code_hash", "resamples", "spectrum_fit_ran",
                          "mask_effectiveness")),
        (C.STAGE_UNMASKING, ("mask_key_hash", "masked_outputs_hash")),
        (C.STAGE_UNMASKED_ANALYSIS, ("design_variant", "blocks", "resamples",
                                     "analysis_code_hash", "measurement_basis",
                                     "identical_computation_as_masked")),
    ]:
        if not t.stage_record(stage).exists():
            continue
        r = read_stage_record(t, stage)
        e[stage] = {k: r.get(k) for k in keys if k in r}
    rec["models"][m] = e
OUT.write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
print("wrote", OUT.name)
