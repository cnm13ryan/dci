"""The registered final result, assembled from signed records only.

One row per estimand per configuration per replication, with its interval, its
realised precision against §16.2's precondition, and the claim §17.6's ladder
emits or withholds. Nothing is computed here: every number is read from the
signed `UNMASKED_ANALYSIS` record, and the quantities a replication's design
does not identify are listed **by name** as `NOT_IDENTIFIED` rather than left
out, because a reader who cannot see the absence cannot tell it from a null.

    ./.venv/bin/python tools/v4r4_final_report.py

Writes `dci1/reports/dci1v4r4/final_results.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                    # noqa: E402
from dci1v4.models.registry import MODEL_KEYS                   # noqa: E402

from dci1v4r4.engine.context import registered_context          # noqa: E402
from dci1v4r4.engine.paths import model_tree                    # noqa: E402
from dci1v4r4.engine.transitions import (                       # noqa: E402
    read_stage_record, stage_reached, terminal_status,
)
from dci1v4r4.protocol import constants as C                    # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "final_results.json"

#: §8.6, by name. Which registered quantities a variant identifies, and which
#: it does not. Listed rather than inferred so a reader gets the absence.
NOT_IDENTIFIED_BY_VARIANT = {
    "full": (),
    "no_spectrum": ("delta_difficulty",),
    "reduced": ("D(B<-R_j)", "D(R_j<-B)", "Delta_j", "Delta_R",
                "delta_difficulty", "Xi"),
}


def _members(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for configuration, entry in sorted(result.items()):
        precision = entry.get("precision", {})
        for family_name, family in sorted(entry["families"].items()):
            for name, member in sorted(family["members"].items()):
                key = f"{family_name}:{name}"
                rows.append({
                    "configuration": configuration,
                    "family": family_name,
                    "estimand": name,
                    "estimate": member["estimate"],
                    "se": member["se"],
                    "marginal": member["marginal"],
                    "simultaneous": member["simultaneous"],
                    "half_width": member["half_width"],
                    "degenerate": member["degenerate"],
                    "refit_per_replicate": member["refit_per_replicate"],
                    "precision": precision.get(key),
                    "critical_value": family["critical_value"],
                    "sidak_reference": family["sidak_reference"],
                    "family_size": len(family["members"]),
                })
    return rows


def _claims(ladder: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for configuration, entry in sorted(ladder.items()):
        for statement in entry.get("statements", []):
            rows.append({
                "configuration": configuration,
                "claim_level": statement.get("claim_level"),
                "family": statement.get("family"),
                "member": statement.get("member"),
                "emitted": statement.get("emitted"),
                "reason": statement.get("reason"),
                "statement": statement.get("statement"),
                "identification_status":
                    statement.get("identification_status"),
                "interval_type": statement.get("interval_type"),
                "outcome_position": statement.get("outcome_position"),
            })
    return rows


def replication(context, model_key: str) -> dict[str, Any]:
    tree = model_tree(context, model_key)
    final = read_stage_record(tree, C.STAGE_UNMASKED_ANALYSIS)
    masked = read_stage_record(tree, C.STAGE_MASKED_ANALYSIS)
    unmask = read_stage_record(tree, C.STAGE_UNMASKING)
    freeze = read_stage_record(tree, C.STAGE_GATE5)
    confirmatory = read_stage_record(tree, C.STAGE_CONFIRMATORY)
    variant = final["design_variant"]
    return {
        "model_key": model_key,
        "design_variant": variant,
        "n_star": freeze["n_star"], "m_star": freeze["m_star"],
        "focal_extension_measured": freeze["focal_extension_measured"],
        "slot_map": freeze["slot_map"],
        "blocks": final["blocks"], "m_draws": freeze["m_draws"],
        "rows_generated": confirmatory["rows"],
        "completeness": confirmatory["completeness"],
        "resamples": final["resamples"],
        "measurement_basis": final["measurement_basis"],
        "scope_sentence": final["scope_sentence"],
        "identification_statuses": freeze["identification_statuses"],
        "not_identified": list(NOT_IDENTIFIED_BY_VARIANT[variant]),
        "not_identified_note":
            "these are registered quantities this design does not identify. "
            "They are not null results, not zero, and not missing by "
            "accident, and no post-hoc estimate of them exists",
        "estimates": _members(final["result"]),
        "claims": _claims(final["claims"]),
        "f6_gate": {k: v.get("f6_gate")
                    for k, v in sorted(final["result"].items())},
        "masking": {
            "mask_key_hash": masked["mask_key_hash"],
            "masked_artifact_hash": masked["masked_artifact_hash"],
            "mask_effectiveness": masked["mask_effectiveness"],
            "spectrum_fit_ran_masked": masked["spectrum_fit_ran"],
            "analysis_code_hash": masked["analysis_code_hash"],
        },
        "unmasking": {
            "mask_key_hash": unmask["mask_key_hash"],
            "masked_outputs_hash": unmask["masked_outputs_hash"],
            "binds_the_sealed_artifact":
                unmask["masked_outputs_hash"] == masked["masked_artifact_hash"],
        },
        "analysis_code_hash": final["analysis_code_hash"],
        "identical_computation_as_masked":
            final["identical_computation_as_masked"],
        "hashes": {
            "canonical_verifier_hash": freeze["canonical_verifier_hash"],
            "calibration_table_hash": freeze["calibration_table_hash"],
            "chat_template_hash": freeze["chat_template_hash"],
            "producing_commit": freeze["producing_commit"],
        },
    }


def main() -> int:
    context = registered_context()
    analysed, terminal, incomplete = [], {}, {}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        status = terminal_status(tree)
        if status is not None:
            payload = fs.read_json(tree.terminal_report)
            payload = payload.get("payload", payload)
            terminal[model_key] = {
                "status": status, "gate": payload.get("gate"),
                "failures": payload.get("failures"),
                "band": payload.get("band"),
                "terminal_sentence": payload.get("terminal_sentence"),
                "stage_reached": stage_reached(tree)}
            continue
        if not tree.stage_record(C.STAGE_UNMASKED_ANALYSIS).exists():
            incomplete[model_key] = stage_reached(tree)
            continue
        analysed.append(model_key)
    record = {
        "artifact_type": "v4r4-final-results",
        "revision": "v4r4",
        "analysed": {m: replication(context, m) for m in analysed},
        "terminal": terminal,
        "not_yet_analysed": incomplete,
        "study_level_not_identified": sorted(
            set().union(*[set(NOT_IDENTIFIED_BY_VARIANT[
                read_stage_record(model_tree(context, m),
                                  C.STAGE_UNMASKED_ANALYSIS)["design_variant"]])
                for m in analysed]) if analysed else set()),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, record)
    print(json.dumps({
        "written": str(OUT.relative_to(DCI1)),
        "analysed": analysed,
        "terminal": {k: v["status"] for k, v in terminal.items()},
        "not_yet_analysed": incomplete,
        "study_level_not_identified": record["study_level_not_identified"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
