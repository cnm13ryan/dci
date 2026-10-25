"""Freeze 1 (the pilot protocol), Freeze 2 (pilot-derived membership), the
researcher's approvals, and the gate that authorises real generation.

**Freeze 1** binds, by hash, everything the pilot will do: configuration,
library and verifier specifications, verifier and text-semantics source,
the logical and full-length compatibility results, the topic bank, split,
overlap and hygiene reports, models and decoding, the Stage 1 design
digest, the code of every module that generates, scores, gates or selects
(``store.code_hash``: docstrings and comments do not count), the vLLM seam
source, the execution-environment lock, the seed derivation, and the
decision register, and the orchestrating interpreter's Python version and
source-hash scheme (D12). Validation recomputes all of it from the running
code and reports every mismatch; it refuses under a Python minor version
other than the one D12 names.

**Authorisation.** Real generation needs a valid Freeze 1 whose every
decision is APPROVED against its current payload hash (each payload binds
the code that implements it, ``config.IMPLEMENTATION``), an environment
lock attested on the execution host, a live environment identical to that
lock, and the manifest's hash passed as the token. Anything less refuses.
Approvals are data the researcher writes (``approvals.json``); this code
never writes an APPROVED status, and it never fabricates an environment.

**Freeze 2** binds the evidence itself: per stage, the design digest, the
canonical hash of every accepted response record, of every full score
vector, the outcome classes, the separately kept technical attempts, and
every backend-run provenance event (generator and environment identity);
the Stage 2 selection and the Stage 1 evidence it was computed from; the
pooled tables; the calibration result; and the D14 stability diagnostics.
Validation rebuilds all of it from the run root, re-scoring every response,
so an edited response, verdict or duplicated row is detected. It records
that no prompt in the pilot carried more than one instruction, read from
the prompt bytes. A result marked infeasible freezes as
``REVISION_REQUIRED``, never as ready for confirmation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import environment as ENV
from dci.batch1 import evidence as EV
from dci.batch1 import library as L
from dci.batch1 import stability as STAB
from dci.batch1 import text as T
from dci.batch1 import topics as TOP
from dci.batch1 import verifiers as V
from dci.batch1.store import SOURCE_HASH_SCHEME, code_hash, record_hash
from dci.provenance.hashes import sha, sha_file

__all__ = ["FreezeError", "AuthorizationError", "RULE_MODULES",
           "EXTERNAL_RULE_MODULES", "approvals_template", "load_approvals",
           "freeze1_manifest", "validate_freeze1", "assert_authorized",
           "freeze2_manifest", "validate_freeze2", "write_json", "read_json",
           "rule_sources", "near_threshold"]


class FreezeError(RuntimeError):
    """A frozen artifact that does not match what the code reproduces."""


class AuthorizationError(RuntimeError):
    """Generation was requested without a valid, approved, named protocol."""


_PKG = Path(__file__).resolve().parent

#: Package modules that do not decide what is generated, scored, gated or
#: selected: presentation and the offline precision simulation.
NOT_FROZEN = ("coverage_study.py", "report.py", "simulate.py")


def _rule_modules() -> tuple[str, ...]:
    return tuple(sorted(p.name for p in _PKG.glob("*.py")
                        if p.name not in NOT_FROZEN))


RULE_MODULES = _rule_modules()
#: Shared modules outside the package that Batch 1 executes.
EXTERNAL_RULE_MODULES = {"dci/verifiers/rules.py": _PKG.parent / "verifiers"
                         / "rules.py",
                         "dci/provenance/hashes.py": _PKG.parent / "provenance"
                         / "hashes.py"}


def rule_sources() -> dict[str, str]:
    out = {name: code_hash(_PKG / name) for name in _rule_modules()}
    out.update({name: code_hash(path)
                for name, path in EXTERNAL_RULE_MODULES.items()})
    return out


def write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True,
                              ensure_ascii=False) + "\n")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------- approvals

def approvals_template(cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG
                       ) -> dict[str, Any]:
    """Every decision PROPOSED, with the payload hash an approval must name."""
    return {"schema": "dci.batch1/approvals/v2",
            "orchestrator_python": CFG.ORCHESTRATOR_PYTHON,
            "source_hash_scheme": SOURCE_HASH_SCHEME,
            "instructions": "Set status to APPROVED, and fill approved_by and "
                            "approved_on (YYYY-MM-DD), only for a decision "
                            "whose payload you have reviewed. Editing a "
                            "decision, or the code that implements it, "
                            "changes its payload hash and voids its "
                            "approval.",
            "decisions": {d.decision_id: {
                "title": d.title, "origin": d.origin, "summary": d.summary,
                "payload_hash": d.payload_hash, "status": "PROPOSED",
                "approved_by": "", "approved_on": "", "note": ""}
                for d in CFG.decisions(cfg)}}


def load_approvals(path: Path | None) -> dict[str, Any]:
    return approvals_template() if path is None else read_json(path)


def _decision_state(cfg: CFG.PilotConfig, approvals: Mapping[str, Any]
                    ) -> tuple[dict[str, Any], list[str]]:
    blocking: list[str] = []
    out: dict[str, Any] = {}
    for key, want in (("orchestrator_python", CFG.ORCHESTRATOR_PYTHON),
                      ("source_hash_scheme", SOURCE_HASH_SCHEME)):
        if approvals.get(key) != want:
            blocking.append(f"approvals record {key} "
                            f"{approvals.get(key)!r}, not {want!r}: "
                            "regenerate them from the current template")
    given = approvals.get("decisions", {})
    for d in CFG.decisions(cfg):
        a = given.get(d.decision_id, {})
        status = a.get("status", "MISSING")
        valid = (status == "APPROVED" and a.get("payload_hash") == d.payload_hash
                 and bool(a.get("approved_by")) and bool(a.get("approved_on")))
        if status == "APPROVED" and not valid:
            status = "APPROVAL_VOID"
        if not valid:
            blocking.append(f"{d.decision_id} {d.title}: {status}")
        out[d.decision_id] = {"title": d.title, "origin": d.origin,
                              "payload_hash": d.payload_hash, "status": status,
                              "approved_by": a.get("approved_by", ""),
                              "approved_on": a.get("approved_on", ""),
                              "implementation": d.payload["implementation"]}
    return out, blocking


# ------------------------------------------------------------------ freeze 1

def _environment(lock: Mapping[str, Any] | None, blocking: list[str]
                 ) -> dict[str, Any]:
    if not lock or lock.get("status") != "ATTESTED":
        blocking.append("execution environment UNATTESTED: run "
                        "`attest-environment` on the generation host and "
                        "freeze with --environment-lock")
        return {"status": "UNATTESTED"}
    lock = json.loads(json.dumps(lock))
    if record_hash(lock["identity"]) != lock.get("identity_hash"):
        blocking.append("environment lock: identity_hash does not match")
    if lock["identity"].get("backend_source_hash") != \
            ENV.backend_source()["hash"]:
        blocking.append("environment lock: attested against another vLLM "
                        "seam source; re-attest")
    if ENV.python_minor(lock["identity"].get("python")) != CFG.BACKEND_PYTHON:
        blocking.append(f"environment lock: the backend is Python "
                        f"{lock['identity'].get('python')}, not "
                        f"{CFG.BACKEND_PYTHON} (D12)")
    for problem in ENV.requirement_problems(lock["identity"],
                                            lock.get("host") or {}):
        blocking.append(f"environment lock: {problem} (D12 execution "
                        "requirements)")
    return lock


def _orchestrator(recorded: Mapping[str, Any] | None) -> dict[str, Any]:
    """D12's interpreter pin. ``frozen_with`` is the minor version and
    implementation of the interpreter that wrote the manifest (not its path
    or patch release, which differ between machines and would make the
    manifest machine-specific); validation carries it over and checks the
    running interpreter separately."""
    found = recorded or ENV.orchestrator()
    return {"required_python": CFG.ORCHESTRATOR_PYTHON,
            "source_hash_scheme": SOURCE_HASH_SCHEME,
            "frozen_with": {"minor": found.get("minor"),
                            "implementation": found.get("implementation")}}


def _body1(cfg: CFG.PilotConfig, approvals: Mapping[str, Any],
           environment_lock: Mapping[str, Any] | None,
           orchestrator: Mapping[str, Any] | None = None) -> dict[str, Any]:
    library = L.library_manifest()
    matrix = COMPAT.compatibility_matrix()
    bank = TOP.load_bank()
    split = TOP.split_bank(bank, pilot_topics=cfg.pilot_topics,
                           stage1_topics=cfg.stage1_topics)
    overlap = TOP.overlap_report(bank)
    hygiene = TOP.hygiene_report(bank, split)
    cells = D.stage1_cells(cfg)
    rows = D.rows_for_cells(cells, split, cfg)
    decisions, blocking = _decision_state(cfg, approvals)
    unresolved = [(cid, m) for cid, row in matrix["cells"].items()
                  for m, cell in row.items() if cell["status"] == COMPAT.UNRESOLVED]
    if unresolved:
        blocking.append(f"unresolved compatibility: {unresolved}")
    task = matrix["task_level"]
    if task["unresolved"]:
        blocking.append("compatible cells without a 60-120 word witness: "
                        f"{task['unresolved'][:10]}")
    if not overlap["clean"]:
        blocking.append("topic overlap report is not clean")
    if not hygiene["clean"]:
        blocking.append("topic hygiene report is not clean")
    environment = _environment(environment_lock, blocking)
    interpreter = _orchestrator(orchestrator)
    if interpreter["frozen_with"].get("minor") != CFG.ORCHESTRATOR_PYTHON:
        blocking.append(f"frozen under Python "
                        f"{interpreter['frozen_with'].get('minor')}, not "
                        f"{CFG.ORCHESTRATOR_PYTHON} (D12)")
    return {
        "schema": "dci.batch1/freeze1/v2", "study_id": CFG.STUDY_ID,
        "protocol_version": CFG.PROTOCOL_VERSION,
        "config": cfg.state(), "config_hash": cfg.config_hash,
        "library": {"hash": L.library_hash(),
                    "n_references": len(library["references"]),
                    "spec_hashes": {c["cid"]: c["spec_hash"] for c in
                                    library["focal_a"] + library["focal_b"]
                                    + library["references"]}},
        "verifier_bundle_hash": V.verifier_bundle_hash(),
        "text_semantics_hash": T.text_semantics_hash(),
        "compatibility": {"hash": COMPAT.matrix_hash(matrix),
                          "counts": matrix["counts"],
                          "unresolved": unresolved,
                          "task_level_counts": task["counts"],
                          "task_level_unresolved": task["unresolved"]},
        "topics": {"bank_hash": split.bank_hash,
                   "source_file_hash": sha_file(TOP.SOURCE_PATH),
                   "split_hash": split.split_hash,
                   "counts": split.manifest()["counts"],
                   "overlap_clean": overlap["clean"],
                   "overlap_hash": record_hash(overlap),
                   "historical_sources": overlap["historical_sources"],
                   "overlap_max_jaccard": {
                       "historical": overlap["max_jaccard_historical"]["value"],
                       "internal": overlap["max_jaccard_internal"]["value"]},
                   "hygiene_clean": hygiene["clean"],
                   "hygiene_hash": record_hash(hygiene)},
        "models": [CFG.MODEL_BY_KEY[k].__dict__ for k in cfg.models],
        "decoding": CFG.DECODING,
        "prompts": {"zero": CFG.PROMPT_ZERO, "one": CFG.PROMPT_ONE},
        "stage1": {"cells": len(cells), "rows": len(rows),
                   "design_hash": D.design_digest(rows)},
        "stage2_bound": {"max_cells": cfg.stage2_max_cells,
                         "rows_per_cell": cfg.stage2_topics * cfg.stage2_draws},
        "seed_derivation": {"domain": cfg.seed_domain,
                            "root": cfg.generation_root_seed,
                            "inputs": ["stage", "model_id", "model_revision",
                                       "prompt_hash", "draw"]},
        "rule_sources": rule_sources(),
        "backend_source": ENV.backend_source(),
        "orchestrator": interpreter,
        "execution_environment": environment,
        "decisions": decisions,
        "authorization": {"pilot_authorizable": not blocking,
                          "blocking": blocking},
    }


def freeze1_manifest(cfg: CFG.PilotConfig = CFG.DEFAULT_CONFIG,
                     approvals: Mapping[str, Any] | None = None, *,
                     environment_lock: Mapping[str, Any] | None = None
                     ) -> dict[str, Any]:
    ENV.require_orchestrator()
    body = _body1(cfg, approvals or approvals_template(cfg), environment_lock)
    return {**body, "manifest_hash": sha(["batch1/freeze1", body])}


def _diff(stored: Any, fresh: Any, path: str = "$") -> list[str]:
    if isinstance(stored, dict) and isinstance(fresh, dict):
        out = []
        for k in sorted(set(stored) | set(fresh)):
            if k not in stored or k not in fresh:
                out.append(f"{path}.{k}: present on one side only")
            else:
                out += _diff(stored[k], fresh[k], f"{path}.{k}")
        return out
    return [] if stored == fresh else [f"{path}: stored {str(stored)[:80]!r} "
                                       f"!= recomputed {str(fresh)[:80]!r}"]


def validate_freeze1(manifest: Mapping[str, Any],
                     approvals: Mapping[str, Any]) -> list[str]:
    """Every difference between the stored manifest and a recomputation.

    The environment lock is an attested input, not something this machine
    can re-derive: it is carried over and its own consistency is checked."""
    body = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    problems = []
    try:
        ENV.require_orchestrator()
    except ENV.PythonMismatch as error:
        problems.append(str(error))
    if sha(["batch1/freeze1", body]) != manifest.get("manifest_hash"):
        problems.append("manifest_hash does not match the manifest body")
    cfg = EV.config_of(manifest)
    lock = manifest.get("execution_environment")
    fresh = _body1(cfg, approvals,
                   lock if (lock or {}).get("status") == "ATTESTED" else None,
                   (manifest.get("orchestrator") or {}).get("frozen_with"))
    problems += _diff(json.loads(json.dumps(body)),
                      json.loads(json.dumps(fresh)))
    return problems


LiveEnvironment = Mapping[str, Any] | Callable[[], Mapping[str, Any]] | None


def assert_authorized(manifest: Mapping[str, Any],
                      approvals: Mapping[str, Any], token: str | None, *,
                      live_environment: LiveEnvironment = None) -> None:
    problems = validate_freeze1(manifest, approvals)
    if problems:
        raise AuthorizationError("the Freeze 1 manifest does not validate: "
                                 + "; ".join(problems[:10]))
    if not manifest["authorization"]["pilot_authorizable"]:
        raise AuthorizationError(
            "the pilot protocol is not authorisable: "
            + "; ".join(manifest["authorization"]["blocking"]))
    if token != manifest["manifest_hash"]:
        raise AuthorizationError(
            "pass the Freeze 1 manifest hash as the authorisation token "
            "(--authorize <manifest_hash>) to run real generation")
    live = live_environment() if callable(live_environment) else live_environment
    if not live or live.get("status") != "AVAILABLE":
        raise AuthorizationError(
            "the live execution environment could not be checked: "
            f"{(live or {}).get('reason', 'no probe')}")
    locked = manifest["execution_environment"]["identity"]
    now = ENV.identity_of(live)
    if now != locked:
        changed = sorted(k for k in set(now) | set(locked)
                         if now.get(k) != locked.get(k))
        raise AuthorizationError("the live execution environment differs from "
                                 f"the attested lock in {changed}")
    # The driver and the rest of D12's requirements are re-checked live, not
    # only when the lock was made (third audit C6b).
    problems = ENV.requirement_problems(now, live)
    if problems:
        raise AuthorizationError("the live execution environment does not "
                                 "meet D12's execution requirements: "
                                 + "; ".join(problems))


# ------------------------------------------------------------------ freeze 2

def tables_hash(tables: Any) -> str:
    return sha(["batch1/tables", tables.state()])


def _pilot_record(stages: Mapping[str, EV.StageEvidence]) -> dict[str, Any]:
    by_id = L.constraint_by_id()
    rows = [r for ev in stages.values() for r in ev.design]
    labels = sorted({r["condition"] for r in rows})
    bad = [c for c in labels if c != D.TASK_ONLY and c not in by_id]
    composed = [r["row_id"] for r in rows
                if D.instruction_lines(r["user_prompt"]) > 1]
    if bad or composed:
        raise FreezeError(f"composed or unknown conditions in the pilot "
                          f"record: {bad[:5]} {composed[:5]}")
    return {"rows": len(rows), "composed_rows": 0,
            "max_instruction_lines": max(
                (D.instruction_lines(r["user_prompt"]) for r in rows),
                default=0),
            "conditions": labels}


def near_threshold(result: Mapping[str, Any], cfg: CFG.PilotConfig
                   ) -> dict[str, Any] | None:
    """D14's near-threshold record: for a FEASIBLE verdict, how many
    configurations support the weakest contrast and whether that is within
    ``near_threshold_margin`` of the target. Recorded in Freeze 2, never a
    flag or a gate (the researcher's decision of 2026-10-25)."""
    feas = result.get("feasibility")
    if result.get("status") != "FEASIBLE" or not feas:
        return None
    support = {p: feas[p]["supported_configurations"] for p in ("P1", "P2", "P3")}
    weakest = min(support.values())
    return {"supported_configurations": support, "weakest": weakest,
            "target": cfg.feasibility_min_configs,
            "margin": cfg.near_threshold_margin,
            "within_margin": weakest <= cfg.feasibility_min_configs
            + cfg.near_threshold_margin}


def freeze2_manifest(freeze1: Mapping[str, Any], bundle: Mapping[str, Any], *,
                     approvals: Mapping[str, Any] | None = None,
                     allow_synthetic: bool = False,
                     replicates: int | None = None) -> dict[str, Any]:
    """``bundle``: ``{"stages": {stage: StageEvidence}, "selection": dict,
    "synthetic": bool}`` as ``pipeline.evidence_bundle`` builds it."""
    synthetic = bool(bundle["synthetic"])
    if synthetic and not allow_synthetic:
        raise FreezeError("synthetic evidence cannot be frozen as pilot "
                          "evidence")
    if not synthetic:
        problems = validate_freeze1(freeze1, approvals or {})
        if problems:
            raise FreezeError("Freeze 1 does not validate: "
                              + "; ".join(problems[:10]))
    stages: Mapping[str, EV.StageEvidence] = bundle["stages"]
    if set(stages) != {D.STAGE1, D.STAGE2}:
        raise FreezeError("Freeze 2 needs complete evidence of both stages")
    selection = bundle["selection"]
    if selection["stage1_evidence_hash"] != stages[D.STAGE1].evidence_hash:
        raise FreezeError("the Stage 2 selection does not belong to this "
                          "Stage 1 evidence")
    cfg = EV.config_of(freeze1)
    matrix = COMPAT.compatibility_matrix()
    tables = EV.tables_for(stages.values(), synthetic=synthetic)
    result = CAL.finalize(tables, cfg, matrix)
    scored = [r for ev in stages.values() for r in ev.scored.values()]
    stability = STAB.diagnostics(scored, result, cfg, matrix,
                                 synthetic=synthetic, replicates=replicates)
    stability["stage1_only"] = STAB.stage1_only(
        stages[D.STAGE1], result, cfg, matrix, synthetic=synthetic)
    feasible = result["status"] == "FEASIBLE"
    configs = {}
    for rep in result["configurations"]:
        key = f"{rep['model']}|{rep['frame']}|B{rep['b_limit']}"
        configs[key] = {"populations": rep["populations"],
                        "weights": rep["weights"],
                        "a_informative": rep["a_informative"],
                        "supported": {p: rep["coverage"][p]["supported"]
                                      for p in ("P1", "P2", "P3")},
                        "reasons": {p: rep["coverage"][p]["reasons"]
                                    for p in ("P1", "P2", "P3")}}
    a = result.get("a") or {}
    namespaces = {ev.provenance.get("namespace") for ev in stages.values()}
    if namespaces != {"synthetic" if synthetic else "real"}:
        raise FreezeError(f"the evidence's provenance is {sorted(map(str, namespaces))}"
                          f", but the bundle is {'synthetic' if synthetic else 'real'}")
    flags = a.get("flags", []) + stability["flags"]
    body = {
        "schema": "dci.batch1/freeze2/v4",
        "freeze1_hash": freeze1["manifest_hash"],
        "synthetic": synthetic,
        "namespace": "synthetic" if synthetic else "real",
        "state": "FROZEN" if feasible else "REVISION_REQUIRED",
        "calibration_status": result["status"],
        "evidence": {stage: ev.manifest() for stage, ev in sorted(stages.items())},
        "stage2_selection_hash": record_hash(selection),
        "stage2_selection_reads": selection["stage1_evidence_hash"],
        "tables_hash": tables_hash(tables),
        "pilot_record": _pilot_record(stages),
        "selected": {"a": a.get("selected"),
                     "b_limits": result["b"]["selected"]},
        "eligible_20": result.get("eligible_20", []),
        "extension_10_only": result.get("extension_10_only", []),
        "configurations": configs,
        "feasibility": result["feasibility"],
        "flags": flags,
        "near_threshold": near_threshold(result, cfg),
        "calibration_hash": sha(["batch1/calibration", result]),
        "stability": stability,
        "confirmatory_interface": {
            "models": list(cfg.models), "frames": list(cfg.frames),
            "orders": ["B_then_X", "X_then_B"],
            "membership_shared_across_orders": True,
            "primary_contrasts": {"P1": ["G1", "G2"], "P2": ["G1", "G3"],
                                  "P3": ["G3", "G5"]},
            "sign": "delta = Delta_restricted - Delta_relaxed",
            "confirmatory_topic_split_hash": freeze1["topics"]["split_hash"],
        },
        "note": ("pilot-derived; not a preregistered decision until the "
                 "researcher approves it" if not synthetic else
                 "SYNTHETIC demonstration; not evidence"),
    }
    return {**body, "manifest_hash": sha(["batch1/freeze2", body])}


def validate_freeze2(manifest: Mapping[str, Any], freeze1: Mapping[str, Any],
                     bundle_fn: Callable[[], Mapping[str, Any]], *,
                     approvals: Mapping[str, Any] | None = None) -> list[str]:
    """Rebuild Freeze 2 from the run root (``bundle_fn`` re-reads and
    re-scores it) and report every difference."""
    body = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    problems = []
    if sha(["batch1/freeze2", body]) != manifest.get("manifest_hash"):
        problems.append("manifest_hash does not match the manifest body")
    try:
        bundle = bundle_fn()
        fresh = freeze2_manifest(freeze1, bundle, approvals=approvals,
                                 allow_synthetic=bool(bundle["synthetic"]),
                                 replicates=manifest.get("stability", {})
                                 .get("replicates"))
    except (EV.RunError, FreezeError) as error:
        return problems + [f"the evidence cannot be rebuilt: {error}"]
    problems += _diff(json.loads(json.dumps(body)), json.loads(json.dumps(
        {k: v for k, v in fresh.items() if k != "manifest_hash"})))
    return problems
