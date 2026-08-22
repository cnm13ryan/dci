"""The pre-freeze audit: the final design, reconstructed from signed records.

Nothing here is taken from a report, a note or an earlier estimate. Every value
is read from a stage record that verifies under this study's signing key, from
the registration manifest, or from a constant the protocol registers --- and
where an earlier document stated a number, this recomputes it and says whether
the record reproduces it. The confirmatory budget in particular: the ~577k
figure was for four replications on the 47-cell design, and neither the count
of replications nor the design survived Gate 3 and Gate 4.

Sections, in the order §18.1 needs them:

1. **Population** --- which replications survive, which are terminal and at
   what registered status, and the evidence each terminal rests on.
2. **Design** --- per surviving replication: n*, m*, whether §7.2's extension
   was measured, the §8.6 variant, the core references, the spectrum rungs,
   the class companion, the exact cells per block, the blocks, M, and the
   exact total confirmatory generation count.
3. **Topics** --- the split, what each stage spent, and that the sets no stage
   may touch are untouched.
4. **Precision** --- §16.2's projection at the registered variance model for
   the estimands the surviving design identifies, against the registered
   preconditions.
5. **Estimands** --- what each design licenses and what it does not, by name.
6. **Hashes** --- protocol, verifier, wordings, specification, mutation,
   calibration table, chat template, dependency and environment digests, and
   every stage record hash.
7. **Integrity** --- signatures, durable copies, ordering, the producing
   commit and the worktree.

    ./.venv/bin/python tools/v4r4_prefreeze_audit.py
"""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
REPO = DCI1.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                    # noqa: E402
from dci1v4.models.registry import MODEL_KEYS, get_model        # noqa: E402
from dci1v4.protocol.hashing import (                           # noqa: E402
    canonical_json, sha_file, sha_text,
)

from dci1v4r4.engine.context import registered_context          # noqa: E402
from dci1v4r4.engine.paths import STAGE_RECORD_FILES, model_tree  # noqa: E402
from dci1v4r4.engine.transitions import (                       # noqa: E402
    read_stage_record, stage_reached, terminal_status,
)
from dci1v4r4.protocol import constants as C                    # noqa: E402
from dci1v4r4.protocol.revision import (                        # noqa: E402
    PROTOCOL_DOCUMENTS, document_hashes, protocol_hash,
)
from dci1v4r4.run.gates_run import full_slot_map                # noqa: E402
from dci1v4r4.stages import audit as topic_audit                # noqa: E402
from dci1v4r4.stages import registration                        # noqa: E402
from dci1v4r4.stages.confirmatory import DESIGN_VARIANTS        # noqa: E402
from dci1v4r4.topics import split_topics                        # noqa: E402
from dci1v4r4.verifiers import source_hashes, verifier_source_hash  # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "prefreeze_audit.json"
PROVENANCE = DCI1 / "reports" / "dci1v4r4" / "backend_provenance.json"
DURABILITY = DCI1 / "reports" / "dci1v4r4" / "durability.json"
GATE1 = DCI1 / "reports" / "dci1v4r4" / "gate1_decision.json"

#: §8.6, by name. What a variant licenses, and what it withholds and why.
ESTIMANDS_BY_VARIANT: dict[str, dict[str, list[str]]] = {
    "full": {
        "identified": ["D(B<-A)", "D(A<-B)", "D(B<-R_j)", "D(R_j<-B)",
                       "Delta_j", "Delta_R", "delta_difficulty", "Xi",
                       "Lambda", "Delta_class"],
        "not_identified": [],
    },
    "no_spectrum": {
        "identified": ["D(B<-A)", "D(A<-B)", "D(B<-R_j)", "D(R_j<-B)",
                       "Delta_j", "Delta_R", "Xi", "Lambda", "Delta_class"],
        "not_identified": ["delta_difficulty"],
    },
    "reduced": {
        "identified": ["D(B<-A)", "D(A<-B)", "Lambda", "Delta_class"],
        "not_identified": ["D(B<-R_j)", "D(R_j<-B)", "Delta_j", "Delta_R",
                           "delta_difficulty", "Xi"],
    },
}


def _allocation():
    spec = importlib.util.spec_from_file_location(
        "allocation_v4r3", DCI1 / "tools" / "allocation_v4r3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


def population(context) -> dict[str, Any]:
    out: dict[str, Any] = {"surviving": [], "terminal": {}}
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        status = terminal_status(tree)
        if status is None:
            out["surviving"].append(model_key)
            continue
        payload = fs.read_json(tree.terminal_report)
        payload = payload.get("payload", payload)
        out["terminal"][model_key] = {
            "status": status, "gate": payload.get("gate"),
            "criterion": payload.get("criterion"),
            "failures": payload.get("failures"),
            "band": payload.get("band"),
            "stage_reached": stage_reached(tree),
            "terminal_sentence": payload.get("terminal_sentence"),
            "evidence": str(
                (tree.root / C.STAGE_GATE4 / "backend_runs" / "headroom"
                 / "scored.jsonl").relative_to(DCI1)),
            "durable_terminal_copy": (
                tree.durable / "terminal_report.json").exists(),
        }
    return out


def design(context, model_key: str) -> dict[str, Any]:
    tree = model_tree(context, model_key)
    regime = read_stage_record(tree, C.STAGE_REGIME)
    gate2 = read_stage_record(tree, C.STAGE_GATE2)
    gate3 = read_stage_record(tree, C.STAGE_GATE3)
    gate4 = read_stage_record(tree, C.STAGE_GATE4)
    variant = gate3["design_variant"]
    reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
    from dci1v4r4.design.cells import cell_types
    types = cell_types(reduced=reduced, class_arm=class_arm, spectrum=spectrum)
    blocks = split_topics()["confirmatory"]
    spec = get_model(model_key)
    return {
        "model_key": model_key,
        "model_id": spec.model_id, "model_revision": spec.revision,
        "protocol_version": registration.PROTOCOL_VERSION,
        "completion_cap": regime["selected_cap"],
        "n_star": gate2["n_star"], "m_star": gate2["m_star"],
        "iota_a": gate2["iota_a"],
        "a_solo_compliance": gate2["a_solo_compliance"],
        "focal_extension_measured": bool(
            gate2.get("focal", {}).get("extension_measured", False)),
        "focal_grid": list(C.FOCAL_GRID),
        "focal_extension": list(C.FOCAL_EXTENSION),
        "m_star_is_last_rung_measured": (
            gate2["m_star"] == max(C.FOCAL_GRID + C.FOCAL_EXTENSION)),
        "design": gate3["design"], "design_variant": variant,
        "design_and_variant_agree": gate3["design"] == variant
        or variant == "no_spectrum",
        "core_references": gate3["core_references"],
        "spectrum": gate3["spectrum"],
        "class_arm": gate3["class_arm"],
        "class_companion": gate3["class_companion"],
        "identification_statuses": gate3["identification_statuses"],
        "slot_map": {k: list(v) for k, v in
                     full_slot_map(gate2, gate3).items()},
        "slots_the_variant_uses": sorted({s for t in types for s in t.slots}),
        "cells_per_block_recorded": gate3["cells_per_block"],
        "cells_per_block_derived": len(types),
        "cell_ids": [t.cell_id for t in types],
        "blocks": len(blocks),
        "m_draws": C.M_DRAWS,
        "confirmatory_generations": len(blocks) * len(types) * C.M_DRAWS,
        "gate4": {"outcome": gate4["outcome"], "rows": gate4["rows"],
                  "cells": gate4["cells"], "band": gate4["band"],
                  "cell_types_evaluated": len(gate4["table"])},
        "estimands": ESTIMANDS_BY_VARIANT[variant],
    }


def precision(variant: str) -> dict[str, Any]:
    A = _allocation()
    applicable = {"full": ("D", "Delta_R", "delta_difficulty", "Lambda",
                           "Delta_j"),
                  "no_spectrum": ("D", "Delta_R", "Lambda", "Delta_j"),
                  "reduced": ("D", "Lambda")}[variant]
    rows: dict[str, Any] = {}
    for phi_name, phi in (("primary", A.PHI_PRIMARY),
                          ("alternate", A.PHI_ALTERNATE)):
        for k in (1, 4, 6):
            hw = {
                "D": A.sidak(k) * math.sqrt(A.var_D(C.N_BLOCKS, C.M_DRAWS,
                                                    phi)),
                "Lambda": A.sidak(k) * math.sqrt(
                    A.var_Lambda(C.N_BLOCKS, C.M_DRAWS, phi)),
            }
            hw["Delta_j"] = hw["D"]
            rows[f"phi_{phi_name}|k={k}"] = {
                "sidak": A.sidak(k),
                **{q: {"half_width": hw[q],
                       "required": C.PRECISION_PRECONDITIONS[q],
                       "met": hw[q] <= C.PRECISION_PRECONDITIONS[q] + 1e-12}
                   for q in ("D", "Lambda", "Delta_j") if q in
                   C.PRECISION_PRECONDITIONS},
            }
    return {
        "blocks": C.N_BLOCKS, "m_draws": C.M_DRAWS,
        "variance_model": {"p_one_minus_p": C.P_ONE_MINUS_P,
                           "phi": [C.PHI_PRIMARY, C.PHI_ALTERNATE],
                           "rho": C.RHO},
        "preconditions": dict(C.PRECISION_PRECONDITIONS),
        "applicable_to_this_variant": list(applicable),
        "projection": rows,
        "v4r2_table_reproduces": {k: round(v, 4)
                                  for k, v in A.verify_v4r2_table().items()},
        "all_applicable_met_at_worst_case": all(
            entry[q]["met"] for entry in rows.values()
            for q in ("D", "Lambda", "Delta_j") if q in entry),
        "note": "a projection, not a guarantee; an unfavourable realisation "
                "is reported as INSUFFICIENT_PRECISION at analysis time "
                "(§16.1). Delta_R and delta_difficulty carry preconditions "
                "that do not apply here because the reduced design does not "
                "identify them",
    }


def topics() -> dict[str, Any]:
    report = topic_audit.assert_reserved_sets_unspent(
        topic_audit.audit_evidence_tree(DCI1 / "evidence" / "dci1v4r4"))
    spent: dict[str, dict[str, int]] = {}
    for label, tally in sorted(report["by_stage"].items()):
        spent[label] = {"stage": topic_audit.resolve_stage(label),
                        **{k: v for k, v in sorted(tally.items())}}
    split = split_topics()
    touched = {name for tally in report["by_stage"].values() for name in tally}
    return {
        "split": {name: len(rows) for name, rows in sorted(split.items())},
        "registered_sizes": dict(C.SET_SIZES),
        "development_sets": list(C.DEVELOPMENT_TOPIC_SETS),
        "reserved_sets": list(C.RESERVED_TOPIC_SETS),
        "spent_by_stage": spent,
        "reserved_sets_unspent": report["reserved_sets_unspent"],
        "untouched": sorted(set(C.TOPIC_SETS) - touched),
        "confirmatory_untouched": "confirmatory" not in touched,
        "sequestered_untouched": "sequestered" not in touched,
        "sequestered_are_hash_only": (
            "the 72 sequestered topics exist to this repository as identities "
            "and content hashes only, so they cannot be spent by construction "
            "and cannot appear in this tally"),
    }


def hashes(context, surviving: list[str]) -> dict[str, Any]:
    provenance = json.loads(PROVENANCE.read_text())
    gate1 = json.loads(GATE1.read_text()) if GATE1.exists() else {}
    out: dict[str, Any] = {
        "protocol_hash": protocol_hash(),
        "protocol_documents": document_hashes(),
        "protocol_document_list": list(PROTOCOL_DOCUMENTS),
        "canonical_verifier_hash": verifier_source_hash(),
        "verifier_sources": source_hashes(),
        "gate1_hashes": {k: gate1.get(k) for k in
                         ("canonical_verifier_hash", "wordings_hash",
                          "specification_hash", "mutation_hash",
                          "measurement_rule_hash", "protocol_hash")},
        "dependency_digest": provenance["dependencies"]["dependency_digest"],
        "dependency_files": provenance["dependencies"]["files"],
        "environment_digest": provenance["environment_digest"],
        "chat_template_hashes": {k: v["chat_template_hash"]
                                 for k, v in
                                 provenance["chat_templates"].items()},
        "registration_manifest_hash":
            registration.load_manifest(context)["manifest_hash"],
        "per_model": {},
    }
    for model_key in surviving:
        tree = model_tree(context, model_key)
        gate2 = read_stage_record(tree, C.STAGE_GATE2)
        out["per_model"][model_key] = {
            "stage_record_hashes": {
                stage: sha_file(tree.stage_record(stage))
                for stage in C.STAGE_SEQUENCE
                if tree.stage_record(stage).exists()},
            "calibration_table_hash": sha_text(
                canonical_json(gate2.get("calibration_table", []))),
        }
    return out


def integrity(context, surviving: list[str]) -> dict[str, Any]:
    per_model: dict[str, Any] = {}
    problems: list[str] = []
    for model_key in MODEL_KEYS:
        tree = model_tree(context, model_key)
        reached = stage_reached(tree)
        stages = C.STAGE_SEQUENCE[:C.STAGE_SEQUENCE.index(reached) + 1]
        entry: dict[str, Any] = {"stage_reached": reached, "records": {}}
        for stage in stages:
            path = tree.stage_record(stage)
            payload = read_stage_record(tree, stage)     # verifies signature
            durable = (tree.durable / stage / "records"
                       / STAGE_RECORD_FILES[stage])
            mirrored = durable.exists() and sha_file(durable) == sha_file(path)
            entry["records"][stage] = {
                "outcome": payload.get("outcome"),
                "signature_verifies": True,
                "durable_mirror_matches": mirrored,
            }
            if not mirrored:
                problems.append(f"{model_key}:{stage}:durable_mirror")
            if payload.get("outcome") != "PASS":
                problems.append(f"{model_key}:{stage}:{payload.get('outcome')}")
        superseded = tree.root / "superseded"
        entry["superseded_records"] = sorted(
            str(p.relative_to(DCI1))
            for p in superseded.rglob("records/*.json")) \
            if superseded.exists() else []
        entry["superseded_are_predecessors_of_nothing"] = all(
            "superseded" not in tree.stage_record(s).parts for s in stages)
        per_model[model_key] = entry
    durability = json.loads(DURABILITY.read_text()) if DURABILITY.exists() \
        else {"passed": False, "why": "no durability record"}
    if not durability.get("passed"):
        problems.append("durability")
    changed = _git("status", "--porcelain")
    return {
        "per_model": per_model,
        "durability": {k: durability.get(k) for k in
                       ("passed", "manifest_tracked_in_git",
                        "roots_on_one_device", "off_machine_copy",
                        "stated_limitation")},
        "producing_commit": _git("rev-parse", "HEAD"),
        "worktree_clean": changed == "",
        "worktree_changed_paths": [line for line in changed.splitlines()][:20],
        "problems": problems,
        "passed": not problems,
    }


def main() -> int:
    context = registered_context()
    pop = population(context)
    surviving = pop["surviving"]
    designs = {m: design(context, m) for m in surviving}
    variants = sorted({d["design_variant"] for d in designs.values()})
    record = {
        "artifact_type": "v4r4-prefreeze-audit",
        "revision": "v4r4",
        "population": pop,
        "design": designs,
        "confirmatory_budget": {
            "per_model": {m: d["confirmatory_generations"]
                          for m, d in designs.items()},
            "total": sum(d["confirmatory_generations"]
                         for d in designs.values()),
            "recomputed_from": "the signed GATE_3_REFERENCES design variant, "
                               "the registered confirmatory topic split and "
                               "C.M_DRAWS; no earlier estimate is carried",
            "superseded_estimate": {
                "value": C.N_CELLS_FULL * C.N_BLOCKS * C.M_DRAWS
                * len(MODEL_KEYS),
                "why_it_no_longer_applies":
                    "it assumed four replications on the 47-cell design; Gate "
                    "3 left one replication on that design and Gate 4 made it "
                    "terminal",
            },
        },
        "precision": {v: precision(v) for v in variants},
        "topics": topics(),
        "hashes": hashes(context, surviving),
        "integrity": integrity(context, surviving),
        "claim_ladder": registration.load_manifest(context)["claim_ladder"],
        "masking": registration.load_manifest(context)["masking"],
        "bootstrap": registration.load_manifest(context)["bootstrap"],
    }
    # A replication that has already frozen and generated has *spent* the
    # confirmatory topic set, so `confirmatory_untouched` goes false and
    # `can_freeze` with it. That is the audit refusing to license a second
    # freeze, not a pre-freeze condition failing --- and a bare `false` reads
    # as the second. `status` says which it is, so re-running this after
    # confirmation does not look like a failed audit.
    already = [m for m in surviving
               if model_tree(context, m).stage_record(
                   C.STAGE_CONFIRMATORY).exists()]
    record["already_generated"] = sorted(already)
    record["can_freeze"] = bool(
        surviving and record["integrity"]["passed"]
        and record["topics"]["reserved_sets_unspent"]
        and record["topics"]["confirmatory_untouched"]
        and all(p["all_applicable_met_at_worst_case"]
                for p in record["precision"].values())
        and all(d["cells_per_block_recorded"] == d["cells_per_block_derived"]
                for d in designs.values()))
    record["status"] = (
        "FREEZE_LICENSED" if record["can_freeze"] else
        "ALREADY_FROZEN_AND_GENERATED" if (
            record["already_generated"]
            and record["integrity"]["passed"]
            and record["topics"]["reserved_sets_unspent"]
            and not record["topics"]["confirmatory_untouched"])
        else "PRE_FREEZE_CONDITIONS_NOT_MET")
    record["status_note"] = {
        "FREEZE_LICENSED":
            "every pre-freeze condition holds and no confirmatory topic is "
            "spent",
        "ALREADY_FROZEN_AND_GENERATED":
            "the confirmatory topic set is spent because this study has "
            "already frozen and generated. `can_freeze` is false because a "
            "second freeze is not licensed, not because an audit condition "
            "failed; the audit that licensed the freeze is the one recorded "
            "at the sealing commit",
        "PRE_FREEZE_CONDITIONS_NOT_MET":
            "at least one pre-freeze condition does not hold; the fields "
            "above say which",
    }[record["status"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, record)
    print(json.dumps({
        "written": str(OUT.relative_to(DCI1)),
        "status": record["status"],
        "surviving": surviving,
        "terminal": {k: v["status"] for k, v in pop["terminal"].items()},
        "variants": {m: d["design_variant"] for m, d in designs.items()},
        "cells_per_block": {m: d["cells_per_block_derived"]
                            for m, d in designs.items()},
        "confirmatory_generations": record["confirmatory_budget"],
        "reserved_sets_unspent": record["topics"]["reserved_sets_unspent"],
        "integrity_passed": record["integrity"]["passed"],
        "integrity_problems": record["integrity"]["problems"],
        "worktree_clean": record["integrity"]["worktree_clean"],
        "can_freeze": record["can_freeze"],
    }, indent=1))
    return 0 if record["can_freeze"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
