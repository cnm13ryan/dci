"""Qualification (§17, item 25): non-scientific, reads no behavioural rate.

Verifies clean tracked code, resolvable model revision, non-empty dependency
representation, prompt-plan schema, verifier and wording tests, cache and
durable-store reachability, environment and producing-commit hashability.
Any failure returns the QUALIFICATION_FAILURE terminal status.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dci1v3.engine.dispatch import Job, operation
from dci1v3.errors import TerminalStatus, V3Error
from dci1v3.generation.prompts import prompt_plan, solo_cells
from dci1v3.protocol import constants as C
from dci1v3.protocol.hashing import sha_obj
from dci1v3.topics.split import split_topics
from dci1v3.verifiers.boundary import evaluate_suite
from dci1v3.verifiers.witnesses import verify_all_witnesses
from dci1v3.verifiers.wording_suite import check_equivalence


def _resolve_revision(job: Job) -> dict[str, Any]:
    """The pinned revision must exist as a local snapshot (offline check)."""
    if job.context.namespace == "synthetic":
        return {"resolved": "synthetic", "snapshot": None}
    hf_home = Path(os.environ.get("HF_HOME",
                                  Path.home() / ".cache" / "huggingface"))
    slug = "models--" + job.spec.model_id.replace("/", "--")
    snapshot = hf_home / "hub" / slug / "snapshots" / job.spec.revision
    if not snapshot.exists():
        raise TerminalStatus("QUALIFICATION_FAILURE", {
            "criterion": "model revision resolvable",
            "observed": f"no local snapshot at {snapshot}"})
    return {"resolved": job.spec.revision, "snapshot": str(snapshot)}


def _hardware_class(job: Job) -> str:
    if job.context.namespace == "synthetic":
        return "synthetic"
    smi = Path("/sys/class/kfd/kfd/topology/nodes")
    return "gfx1100-rx7900xtx" if smi.exists() else "unknown-gpu"


@operation("qualify", stage=C.STAGE_QUALIFIED)
def qualify(job: Job) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    try:
        checks["model_revision"] = _resolve_revision(job)
        boundary = evaluate_suite()
        if boundary["handled_as_specified"] != C.BOUNDARY_CASES_REQUIRED:
            raise TerminalStatus("QUALIFICATION_FAILURE", {
                "criterion": "verifier boundary suite",
                "observed": boundary})
        checks["boundary_suite"] = {
            "handled": boundary["handled_as_specified"]}
        checks["wording_equivalence"] = check_equivalence()
        checks["witnesses"] = verify_all_witnesses()
        split = split_topics()
        plan = prompt_plan(solo_cells(
            "qualification-schema", split["prescreen"][:4],
            [("A", n) for n in C.TARGET_GRID], draws=1))
        checks["prompt_plan_schema"] = {"cells": len(plan["cells"]),
                                        "plan_hash": sha_obj(plan)}
        cache_probe = job.tree.data_dir("qualification") / "probe.txt"
        cache_probe.parent.mkdir(parents=True, exist_ok=True)
        cache_probe.write_text("reachable")
        durable_probe = job.tree.durable / "qualification" / "probe.txt"
        durable_probe.parent.mkdir(parents=True, exist_ok=True)
        durable_probe.write_text("reachable")
        checks["stores_reachable"] = True
        checks["environment"] = {
            "digest": job.environment_digest,
            "lockfile_hash": job.environment["lockfile_hash"],
            "export_hash": job.environment["export_hash"],
        }
        checks["producing_commit"] = job.producing_commit
    except TerminalStatus:
        raise
    except V3Error as error:
        raise TerminalStatus("QUALIFICATION_FAILURE", {
            "criterion": "qualification check",
            "observed": str(error)}) from error
    return {"status": "PASSED",
            "body": {"checks": checks,
                     "hardware_class": _hardware_class(job),
                     "environment_record": job.environment},
            "input_hashes": {"dependency_digest":
                             job.environment["dependency_digest"]},
            "output_hashes": {}}
