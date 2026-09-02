"""Stage 7, ``FINAL_REPORT``: what the frozen design licenses, per model.

Reads the signed analysis record and restates it as claims: per entering
frame and configuration the Delta_R(f) estimate with its per-frame and
joint decision intervals, the reading and its statuses; the model-level
LOCAL verdict (the conjunction); the spectrum arm's delta_difficulty(f)
and slope with their support; the reference-sensitivity range; the
precision preconditions met or not; and every deviation the freeze
declared. It computes nothing new.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.freeze import load_freeze

__all__ = ["report_payload", "run_report", "frame_claims"]


def _iv(m: Mapping[str, Any]) -> dict[str, Any]:
    return {"estimate": m["estimate"], "se": m["standard_error"],
            "lower": m["decision_lower"], "upper": m["decision_upper"],
            "half_width": m["decision_half_width"],
            "meets_precondition": m.get("meets_precondition"),
            "reading": m.get("reading")}


def frame_claims(analysis: Mapping[str, Any], frame: int
                 ) -> dict[str, Any]:
    fr = analysis["frames"][str(frame)]
    out: dict[str, Any] = {"frame": frame, "blocks": fr["blocks"],
                           "enters_local": fr["enters_local"],
                           "enters_spectrum": fr["enters_spectrum"],
                           "configurations": {}}
    for cfg in C.CONFIGURATIONS:
        fams = fr["configurations"][cfg]
        joint = analysis["joint"][cfg]["members"]
        c: dict[str, Any] = {}
        f1 = fams.get("F1", {}).get("members", {})
        for name in ("D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "Xi",
                     "delta_difficulty"):
            if name in f1:
                jname = f"f{frame}:{name}"
                c[name] = {"frame_interval": _iv(f1[name]),
                           "joint_interval": _iv(joint[jname])
                           if jname in joint else None}
        if "F_REFSENS" in fams:
            ests = [m["estimate"] for m in fams["F_REFSENS"]["members"].values()]
            c["reference_sensitivity"] = {
                "n_triples": len(ests), "min": min(ests), "max": max(ests),
                "frozen_core": f1.get("Delta_R", {}).get("estimate"),
                "critical_value": fams["F_REFSENS"]["critical_value"],
                "members": {k: _iv(v) for k, v in
                            fams["F_REFSENS"]["members"].items()}}
        if "F_SPECTRUM" in fams:
            c["slope"] = _iv(fams["F_SPECTRUM"]["members"]["slope"])
            c["spectrum_fit"] = fr.get("spectrum_fit", {}).get(cfg)
        for fam in ("F2", "F3", "F4"):
            if fam in fams:
                c[fam] = {k: _iv(v) for k, v in fams[fam]["members"].items()}
        out["configurations"][cfg] = c
    out["F11"] = {k: {"estimate": v["estimate"],
                      "lower": v["simultaneous_lower"],
                      "upper": v["simultaneous_upper"],
                      "meets_precondition": v.get("meets_precondition")}
                  for k, v in fr["F11"]["members"].items()}
    return out


def report_payload(tree: L.ConfirmTree, analysis: Mapping[str, Any], *,
                   producing_commit: str) -> dict[str, Any]:
    freeze, freeze_hash = load_freeze(tree)
    if analysis.get("freeze_hash") != freeze_hash:
        raise IntegrityError("the analysis record was signed under a "
                             "different freeze")
    frames = {w: frame_claims(analysis, int(w)) for w in analysis["frames"]}
    return {
        "stage": L.STAGE_REPORT,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_REPORT],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"freeze_hash": freeze_hash,
                   "analysis_record_hash":
                       fs.read_json(tree.stage_record(L.STAGE_ANALYSIS))["record_hash"]},
        "freeze_hash": freeze_hash, "protected": True,
        "frames_entering_local": freeze["design"]["frames_entering_local"],
        "frames_entering_spectrum": freeze["design"]["frames_entering_spectrum"],
        "blocks_per_frame": freeze["design"]["blocks_per_frame"],
        "model_verdict": analysis["model_verdict"],
        "joint_critical_values": {cfg: analysis["joint"][cfg]["critical_value"]
                                  for cfg in C.CONFIGURATIONS},
        "joint_family_size": {cfg: analysis["joint"][cfg]["family_size"]
                              for cfg in C.CONFIGURATIONS},
        "frames": frames,
        "deviations": freeze["deviations"],
        "estimands": freeze["estimands"],
        "thresholds": freeze["thresholds"],
        "stability": {w: e.get("stability") for w, e in
                      freeze["design"]["frames"].items()},
        "strongest_permissible_statement":
            "each Delta_R(f) is a statement about this model under this "
            "wording frame at the frozen n*(f), m*(f) and reference triple; "
            "the model-level verdict is the conjunction over its entering "
            "frames; nothing here generalises across wordings or models",
    }


def run_report(tree: L.ConfirmTree, *, producing_commit: str | None = None,
               environment_digest: str = "") -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_REPORT,
        compute=lambda prev: report_payload(tree, prev, producing_commit=commit),
        producing_commit=commit, environment_digest=environment_digest)
