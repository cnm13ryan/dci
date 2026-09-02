"""Stage 7, ``FINAL_REPORT``: what the frozen design licenses, per model.

Reads the signed analysis record and restates it as claims: per entering
frame and configuration the Delta_R(f) estimate with its per-frame and
joint decision intervals, the reading and its statuses; the model-level
LOCAL verdict (the conjunction); the spectrum arm's delta_difficulty(f)
and slope with their support; the reference-sensitivity range; the
precision preconditions met or not; and every deviation the freeze
declared. It computes nothing new.

Beside the estimates it restates every **gate** the analysis recorded: the
L1 solo-headroom reading and the L2 precondition that reads it, Xi's
wording qualifier on Delta_R, the within-frame reference heterogeneity,
§17.4's vacuity family and its two halves, §23's projection audit, the
§34 D6 identification ledger, L4a's per-member cross-configuration
consistency, F7's reciprocal losses, the runner-up sensitivity contrast
beside the frozen operating point, and §26's methodological success
verdict.

Then its own **traceability checks** (v7's ``run/final_report_checks``, in
the form this layer can establish): every frame the freeze carries has an
analysis entry, every registered member is ESTIMATED or ledgered, every
rendered estimate equals the analysis record's own value, the analysis was
signed under this freeze, and no verdict is the strong L3c this design
cannot license. A mandatory failure records ``outcome`` ``FAIL`` ---
``FINAL_REPORT`` has no successor to refuse, so the failure has to be on
the record itself.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import analysis as A
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.freeze import load_freeze

__all__ = ["report_payload", "run_report", "frame_claims", "report_checks",
           "REPORT_CHECKS", "REPORT_FAILURE"]

REPORT_FAILURE = "FINAL_REPORT_FAILURE"

#: id, what it establishes, mandatory.
REPORT_CHECKS: tuple[tuple[str, str, bool], ...] = (
    ("every_frame_has_an_analysis_entry",
     "every frame the freeze carries was analysed", True),
    ("every_registered_member_is_estimated_or_ledgered",
     "§34 D6: every registered member carries ESTIMATED, NOT_ASKED or "
     "NOT_IDENTIFIED, and every estimated member is recorded ESTIMATED", True),
    ("estimates_trace_to_the_analysis_record",
     "every estimate this report renders equals the analysis record's own "
     "value", True),
    ("analysis_signed_under_this_freeze",
     "the analysis record's freeze hash is this freeze's", True),
    ("no_strong_l3c_verdict",
     "§34 D18: no model verdict is the strong L3c this design cannot "
     "license without the near-form arm", True),
    ("projection_audit_recorded",
     "§23's projection audit is recorded for every frame", True),
    ("methodological_success_recorded",
     "§26's criterion carries a registered verdict", True),
)


def _iv(m: Mapping[str, Any]) -> dict[str, Any]:
    return {"estimate": m["estimate"], "se": m["standard_error"],
            "lower": m["decision_lower"], "upper": m["decision_upper"],
            "half_width": m["decision_half_width"],
            "meets_precondition": m.get("meets_precondition"),
            "reading": m.get("reading")}


def frame_claims(analysis: Mapping[str, Any], frame: int,
                 frozen: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One frame's claims table. ``frozen`` is the freeze's entry for the
    frame, which the runner-up block reads for the operating point the
    sensitivity contrast is a sensitivity *to*."""
    fr = analysis["frames"][str(frame)]
    frozen = frozen or {}
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
            c["degenerate_replicates"] = fams["F_SPECTRUM"].get(
                "degenerate_replicates")
        for fam in ("F2", "F3", "F4", "F5", "F6", "F7"):
            if fam in fams:
                c[fam] = {k: _iv(v) for k, v in fams[fam]["members"].items()}
        if "F_RUNNER_UP" in fams:
            # The runner-up sensitivity contrast, beside the frozen point it
            # does not replace: the arm licenses no claim (freeze
            # ``operating_point_rule``).
            c["runner_up"] = {
                "frozen_operating_point": {
                    "n_star": frozen.get("n_star"),
                    "m_star": frozen.get("m_star")},
                "runner_up": frozen.get("runner_up"),
                "critical_value": fams["F_RUNNER_UP"]["critical_value"],
                "delta_r_frozen": f1.get("Delta_R", {}).get("estimate"),
                "members": {k: _iv(v) for k, v in
                            fams["F_RUNNER_UP"]["members"].items()},
                "licenses": "nothing; the frozen n*(f), m*(f) stand"}
        # The gates, restated: they are what says what the number means.
        gates = (fr.get("gates") or {}).get(cfg) or {}
        c["l1"] = gates.get("l1")
        c["l2"] = gates.get("l2")
        c["xi_gate"] = gates.get("xi")
        c["reference_heterogeneity"] = gates.get("reference_heterogeneity")
        c["vacuity"] = gates.get("vacuity")
        c["identification_ledger"] = ((fr.get("identification_ledger") or {})
                                      .get("configurations", {}).get(cfg))
        out["configurations"][cfg] = c
    out["solo_headroom"] = fr.get("solo_headroom")
    out["projection_audit"] = fr.get("projection_audit")
    out["l4a"] = fr.get("l4a")
    out["algebraic_forms"] = fr.get("algebraic_forms")
    out["identification_ledger_cross_configuration"] = (
        (fr.get("identification_ledger") or {}).get("cross_configuration"))
    out["F11"] = {k: {"estimate": v["estimate"],
                      "lower": v["simultaneous_lower"],
                      "upper": v["simultaneous_upper"],
                      "meets_precondition": v.get("meets_precondition")}
                  for k, v in fr["F11"]["members"].items()}
    return out


def _ledgers(analysis: Mapping[str, Any]) -> list[tuple[str, str, str, str]]:
    """(where, family, member, status) for every ledger entry on the
    record --- per frame per configuration, the F11 one, and the joint."""
    out: list[tuple[str, str, str, str]] = []
    for w, fr in (analysis.get("frames") or {}).items():
        ledger = fr.get("identification_ledger") or {}
        for cfg, families in (ledger.get("configurations") or {}).items():
            for family, members in families.items():
                for member, entry in members.items():
                    out.append((f"f{w}:{cfg}", family, member,
                                entry.get("status")))
        for family, members in (ledger.get("cross_configuration") or {}).items():
            for member, entry in members.items():
                out.append((f"f{w}:cross", family, member, entry.get("status")))
    for cfg, joint in (analysis.get("joint") or {}).items():
        for family, members in (joint.get("identification_ledger") or {}).items():
            for member, entry in members.items():
                out.append((f"joint:{cfg}", family, member,
                            entry.get("status")))
    return out


def report_checks(analysis: Mapping[str, Any], freeze: Mapping[str, Any],
                  frames: Mapping[str, Any], *, freeze_hash: str
                  ) -> list[dict[str, Any]]:
    """v7's ``final_report_checks``, in the form this layer can establish.

    Each check re-opens the analysis record rather than trusting the table
    built from it: a report that merely reprints the analysis proves
    nothing, and a report that cannot establish its own traceability is not
    a report.
    """
    detail: dict[str, Any] = {}
    frozen_frames = set(freeze["design"]["frames"])
    analysed = set(analysis.get("frames") or {})
    detail["every_frame_has_an_analysis_entry"] = {
        "frozen": sorted(frozen_frames), "analysed": sorted(analysed),
        "missing": sorted(frozen_frames - analysed)}
    ledger = _ledgers(analysis)
    bad = [f"{w}:{fam}:{m}" for w, fam, m, s in ledger
           if s not in A.LEDGER_STATUSES]
    estimated = {(w, fam, m) for w, fam, m, s in ledger if s == "ESTIMATED"}
    unledgered: list[str] = []
    for w, fr in (analysis.get("frames") or {}).items():
        for cfg, families in (fr.get("configurations") or {}).items():
            for family, entry in families.items():
                for member in (entry.get("members") or {}):
                    if (f"f{w}:{cfg}", family, member) not in estimated:
                        unledgered.append(f"f{w}:{cfg}:{family}:{member}")
        for member in (fr.get("F11") or {}).get("members", {}):
            if (f"f{w}:cross", "F11", member) not in estimated:
                unledgered.append(f"f{w}:cross:F11:{member}")
    detail["every_registered_member_is_estimated_or_ledgered"] = {
        "entries": len(ledger), "unregistered_status": bad,
        "estimated_but_not_ledgered": sorted(unledgered),
        "by_status": {s: sum(1 for e in ledger if e[3] == s)
                      for s in A.LEDGER_STATUSES}}
    mismatched: list[str] = []
    for w, claims in frames.items():
        source = analysis["frames"][str(w)]["configurations"]
        for cfg, c in claims["configurations"].items():
            for name, entry in c.items():
                if not isinstance(entry, Mapping) or "frame_interval" not in entry:
                    continue
                got = entry["frame_interval"]["estimate"]
                want = source[cfg]["F1"]["members"][name]["estimate"]
                if got != want:
                    mismatched.append(f"f{w}:{cfg}:{name}")
    detail["estimates_trace_to_the_analysis_record"] = {
        "mismatched": mismatched}
    detail["analysis_signed_under_this_freeze"] = {
        "analysis": analysis.get("freeze_hash"), "freeze": freeze_hash}
    verdicts = dict(analysis.get("model_verdict") or {})
    detail["no_strong_l3c_verdict"] = {
        "verdicts": verdicts,
        "disposition": A.L3C_DISPOSITION,
        "offending": sorted(cfg for cfg, v in verdicts.items()
                            if v == "LOCAL_EQUIVALENT_L3c")}
    detail["projection_audit_recorded"] = {
        "missing": sorted(w for w, fr in (analysis.get("frames") or {}).items()
                          if fr.get("projection_audit") is None)}
    success = analysis.get("methodological_success") or {}
    detail["methodological_success_recorded"] = {
        "verdict": success.get("verdict"), "reasons": success.get("reasons")}
    verdict_of = {
        "every_frame_has_an_analysis_entry":
            not detail["every_frame_has_an_analysis_entry"]["missing"],
        "every_registered_member_is_estimated_or_ledgered":
            not bad and not unledgered,
        "estimates_trace_to_the_analysis_record": not mismatched,
        "analysis_signed_under_this_freeze":
            analysis.get("freeze_hash") == freeze_hash,
        "no_strong_l3c_verdict":
            not detail["no_strong_l3c_verdict"]["offending"],
        "projection_audit_recorded":
            not detail["projection_audit_recorded"]["missing"],
        "methodological_success_recorded":
            success.get("verdict") in C.SUCCESS_CRITERION_VALUES,
    }
    return [{"check": check, "establishes": establishes,
             "mandatory": mandatory,
             "verdict": "PASS" if verdict_of[check] else "FAIL",
             "detail": detail[check]}
            for check, establishes, mandatory in REPORT_CHECKS]


def report_payload(tree: L.ConfirmTree, analysis: Mapping[str, Any], *,
                   producing_commit: str) -> dict[str, Any]:
    freeze, freeze_hash = load_freeze(tree)
    if analysis.get("freeze_hash") != freeze_hash:
        raise IntegrityError("the analysis record was signed under a "
                             "different freeze")
    frozen_frames = freeze["design"]["frames"]
    frames = {w: frame_claims(analysis, int(w), frozen_frames.get(str(w)))
              for w in analysis["frames"]}
    checks = report_checks(analysis, freeze, frames, freeze_hash=freeze_hash)
    failed = [c for c in checks if c["mandatory"] and c["verdict"] != "PASS"]
    return {
        "stage": L.STAGE_REPORT,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_REPORT],
        "outcome": "PASS" if not failed else "FAIL",
        "failure_status": None if not failed else REPORT_FAILURE,
        "traceability_checks": checks,
        "traceability_failed": [c["check"] for c in failed],
        "producing_commit": producing_commit,
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
        "methodological_success": analysis.get("methodological_success"),
        "l3c_disposition": {
            "disposition": A.L3C_DISPOSITION,
            "rule": "§34 D18 is closed at 'precondition' and v8 runs no "
                    "near-form arm, so the strong L3c refutation verdict is "
                    "unreachable; an L3c-level reading is reported and the "
                    "model verdict is the narrower same-form-only one",
            "by_configuration": {cfg: (analysis["joint"][cfg]
                                       ["local_model_verdict"].get("l3c"))
                                 for cfg in C.CONFIGURATIONS}},
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
