"""Gate 3: the immutable model freeze (§18.6, item 38).

The freeze record binds every frozen field, the six predecessor gate-record
hashes, and the complete confirmatory block plan. Confirmatory generation is
impossible until this record exists and verifies.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dci1v3.engine.dispatch import Job, operation
from dci1v3.engine.signing import verify_signed
from dci1v3.engine.transitions import load_stage_record
from dci1v3.errors import ProtocolError
from dci1v3.generation.prompts import arm_cells, prompt_plan
from dci1v3.protocol import constants as C
from dci1v3.protocol.codebook import GENERATION_CODEBOOK, validate_codebook
from dci1v3.protocol.hashing import sha_obj, sha_text
from dci1v3.protocol.wordings import (
    family_wordings,
    focal_wordings,
    target_wordings,
)
from dci1v3.stages.gate2b import gate2a_payload
from dci1v3.topics.split import confirmatory_blocks, split_topics
from dci1v3.verifiers import source_hashes


def frozen_parameters(job: Job) -> dict[str, Any]:
    record = load_stage_record(job.tree, C.STAGE_GATE2B)
    if record is None:
        raise ProtocolError("the freeze requires the Gate 2B record")
    body = verify_signed(record, job.context.signing_key_path,
                         where="gate2b_composed")["body"]
    return {"n": int(body["n_star"]), "m": int(body["m_star"]),
            "cap": int(body["cap"]),
            "references": [tuple(r) for r in body["final_references"]]}


def chat_template_hash(job: Job) -> str:
    if job.context.namespace == "synthetic":
        return sha_text("synthetic-template")
    hf_home = Path(os.environ.get("HF_HOME",
                                  Path.home() / ".cache" / "huggingface"))
    slug = "models--" + job.spec.model_id.replace("/", "--")
    snapshot = hf_home / "hub" / slug / "snapshots" / job.spec.revision
    for name in ("chat_template.jinja", "tokenizer_config.json"):
        path = snapshot / name
        if path.exists():
            if name.endswith(".json"):
                template = json.loads(path.read_text()).get("chat_template")
                if template:
                    return sha_text(json.dumps(template, sort_keys=True))
            else:
                return sha_text(path.read_text())
    raise ProtocolError(f"no chat template found for {job.spec.model_id} "
                        f"at {snapshot}; the freeze fails closed")


def confirmatory_plan(params: dict[str, Any]) -> dict[str, Any]:
    blocks = confirmatory_blocks()
    cells = arm_cells("confirmatory", blocks, n=params["n"], m=params["m"],
                      references=tuple(params["references"]),
                      draws=C.M_DRAWS)
    return prompt_plan(cells)


@operation("freeze", stage=C.STAGE_FREEZE)
def run_freeze(job: Job) -> dict[str, Any]:
    params = frozen_parameters(job)
    gate2a = gate2a_payload(job)
    split = split_topics()
    plan = confirmatory_plan(params)
    validate_codebook()

    gate_hashes = {}
    for stage in (C.STAGE_QUALIFIED, C.STAGE_GATE0, C.STAGE_REGIME,
                  C.STAGE_GATE1, C.STAGE_GATE2A, C.STAGE_GATE2B):
        record = load_stage_record(job.tree, stage)
        if record is None:
            raise ProtocolError(f"freeze requires the {stage} record")
        gate_hashes[stage] = record["record_hash"]

    wordings = {
        "target": target_wordings(params["n"]),
        "focal": focal_wordings(params["m"]),
        "references": {family: family_wordings(family, q)
                       for family, q in params["references"]},
    }
    body: dict[str, Any] = {
        "model_revision": job.spec.revision,
        "completion_cap": params["cap"],
        "n_star": params["n"], "m_star": params["m"],
        "final_references": [list(r) for r in params["references"]],
        "wordings": wordings,
        "wordings_hash": sha_obj(wordings),
        "topic_splits": {name: [t["topic_id"] for t in topics]
                         for name, topics in split.items()},
        "prompt_templates": {"two": C.PROMPT_TWO, "one": C.PROMPT_ONE,
                             "zero": C.PROMPT_ZERO},
        "chat_template_hash": chat_template_hash(job),
        "verifier_sources": source_hashes(),
        "scoring_rules": ["S0", "S1", "S2", "S3"],
        "decoding": C.DECODING,
        "greedy_decoding": C.GREEDY_DECODING,
        "seed_rules": {
            "generation_root": C.GENERATION_ROOT_SEED,
            "pseudo_run_root": C.PSEUDO_RUN_ROOT_SEED,
            "bootstrap_root": C.BOOTSTRAP_ROOT_SEED,
            "domains": [C.DOMAIN_GENERATION, C.DOMAIN_PSEUDO,
                        C.DOMAIN_BOOTSTRAP],
            "primary_draw_rule": 'H("primary-root", model-id, '
                                 'prompt-hash) mod 16',
        },
        "block_plan_hash": sha_obj(plan),
        "block_count": C.N_BLOCKS,
        "family_declarations": C.FAMILY_SIZES,
        "equivalence_regions": {
            "primary": list(C.EQUIVALENCE_REGION),
            "exchangeability": list(C.EXCHANGEABILITY_REGION)},
        "codebook_hash": sha_obj(
            {name: [str(part) for part in row]
             for name, row in GENERATION_CODEBOOK.items()}),
        "clean_tree": True,
        "hardware_class": _qualification_hardware(job),
        "gate_record_hashes": gate_hashes,
        "analysis_plan": {
            "order": ["load", "matrix", "select", "score", "checks",
                      "contrasts", "bootstrap", "intervals", "claims"],
            "resamples": C.BOOTSTRAP_RESAMPLES,
            "pseudo_runs": C.PSEUDO_RUNS,
            "families": C.FAMILY_SIZES,
            "sesoi": C.SESOI,
            "exchangeability_margin": C.EXCHANGEABILITY_MARGIN},
        "solo_calibration_summary": {
            "target_rate": gate2a["target_curve"][str(params["n"])],
            "focal_rate": gate2a["focal_curve"][str(params["m"])]},
        "measurement_basis": _measurement_basis(job),
    }
    return {"status": "PASSED", "body": body,
            "input_hashes": {"gate_records": sha_obj(gate_hashes)},
            "output_hashes": {"block_plan": body["block_plan_hash"]}}


def _measurement_basis(job: Job) -> dict[str, Any]:
    """Amendment A2: the freeze carries the measurement's evidence basis
    and claim scope verbatim from the Gate 1 record."""
    record = load_stage_record(job.tree, C.STAGE_GATE1)
    payload = verify_signed(record, job.context.signing_key_path,
                            where="gate1_measurement")
    body = payload["body"]
    return {"basis": body.get("basis"),
            "human_validation": body.get("human_validation"),
            "strongest_claim": body.get("strongest_claim"),
            "measurement_scope": body.get("measurement_scope")}


def _qualification_hardware(job: Job) -> str | None:
    record = load_stage_record(job.tree, C.STAGE_QUALIFIED)
    payload = verify_signed(record, job.context.signing_key_path,
                            where="qualification")
    return payload["body"].get("hardware_class")
