"""Stage 3, ``MEMBERSHIP``: what this model would run, decided before any
composed row exists, from pre-freeze evidence only.

Per frame, from the (top-up-augmented) Gate-3 verdicts and the pilot's
Gate-2 record:

* **LOCAL**: the frame enters iff it is ``LOCAL_SUPPORTED`` (the full
  §13.15 survival on its own table) *and* the model is ``LOCAL_ELIGIBLE``
  (>= ``rules.LOCAL_ELIGIBILITY_MIN_FRAMES`` supported frames). Every
  supported frame of an eligible model enters; there is no best-two.
* **SPECTRUM**: the frame enters iff Gate 2 supported it and the v8
  coverage gate identified its selected set (``coverage_identified``),
  whatever the model's LOCAL standing.

For every entering frame the record carries the frozen operating points,
the slot map (A at n*(f); B at m*(f); R1..R3 the core rungs; R4, R5 the
frozen backups; S1..Sk the selected spectrum points, a point that is a
core or backup rung aliased to that slot), the stability bootstrap of
n*(f)/m*(f) (``confirm.stability``), and the pre-registered
reference-sensitivity plan: every admissible triple over the five frozen
families {R1..R5} under §13.8's own structural rules, so that Delta_R(f)
can be reported over each of them from the same generated cells.

Nothing here is a threshold, and the record reads no composed quantity.
"""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.run.gates_run import focal_constraint
from dci1v7.stages.selection import FAMILIES
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev import rules as R
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.design import (ARM_BACKUP, ARM_BASE, ARM_CORE,
                                      ARM_RUNNER_UP, ARM_SPECTRUM,
                                      MAX_SPECTRUM_POINTS, n_cells_for,
                                      spectrum_slot_names)
from dci1v8dev.confirm.pilot_import import frame_inputs, open_pilot
from dci1v8dev.confirm.stability import frame_stability
from dci1v8dev.run import seeds
from dci1v8dev.run import stages as PS

__all__ = ["admissible_triples", "frame_membership", "membership_payload",
           "run_membership", "slot_map_of"]


def admissible_triples(references: Sequence[Mapping[str, Any]]
                       ) -> list[dict[str, Any]]:
    """Every 3-subset of the frozen families {R1..R5} meeting §13.8's
    structural rules (three feature groups, >= MIN_TIER1_CORE Tier-1
    members, >= MIN_CORE_DISCOURSE_ROLES declared roles)."""
    out: list[dict[str, Any]] = []
    for tri in itertools.combinations(references, 3):
        fams = [FAMILIES[r["family"]] for r in tri]
        groups = {f.feature_group for f in fams}
        if len(groups) < 3:
            continue
        if sum(1 for f in fams if f.structural_tier == 1) < C.MIN_TIER1_CORE:
            continue
        roles = {f.discourse_role for f in fams if f.discourse_role != "none"}
        if len(roles) < C.MIN_CORE_DISCOURSE_ROLES:
            continue
        out.append({"slots": [r["slot"] for r in tri],
                    "families": [r["family"] for r in tri],
                    "is_frozen_core": [r["slot"] for r in tri]
                    == list(C.CORE_SLOTS),
                    "contains_contrastive": any(
                        f.discourse_role == "contrastive" for f in fams)})
    return out


def slot_map_of(fi: Mapping[str, Any], *, local: bool, spectrum: bool,
                runner_up: Mapping[str, int] | None = None
                ) -> tuple[dict[str, list], dict[str, str], list[dict[str, Any]]]:
    """(slot -> [kind, severity, flags], spectrum aliases, spectrum slots).

    ``runner_up`` maps "A2" and/or "B2" to the runner-up severity of an
    OPERATING_POINT_UNSTABLE coordinate; the slots exist only on a LOCAL
    frame (the arm re-forms Delta_R(f) against the frozen core)."""
    slots: dict[str, list] = {
        "A": ["A", int(fi["n_star"]), {}],
        "B": ["B", int(fi["m_star"]),
              {"extended": int(fi["m_star"]) in C.FOCAL_EXTENSION}]}
    label_to_slot: dict[str, str] = {}
    if local:
        for ref in fi["core"] + fi["backups"]:
            slots[ref["slot"]] = [ref["family"], int(ref["severity"]),
                                  {"reserve": True}]
            label_to_slot[ref["label"]] = ref["slot"]
        for slot, q in sorted((runner_up or {}).items()):
            if slot == "A2":
                slots["A2"] = ["A", int(q), {"runner_up": True}]
            elif slot == "B2":
                slots["B2"] = ["B", int(q), {"runner_up": True,
                                            "extended": int(q) in C.FOCAL_EXTENSION}]
            else:
                raise ProtocolError(f"{slot!r} is not a runner-up slot")
    aliases: dict[str, str] = {}
    spectrum_slots: list[dict[str, Any]] = []
    if spectrum:
        points = [p for p in fi["spectrum"]
                  if p.get("side") in ("below", "above", "core")]
        fresh = [p for p in points if p["candidate"] not in label_to_slot]
        if len(fresh) > MAX_SPECTRUM_POINTS:
            raise ProtocolError(f"{len(fresh)} spectrum points; the design "
                                f"carries at most {MAX_SPECTRUM_POINTS}")
        names = spectrum_slot_names(len(fresh))
        for name, p in zip(names, fresh):
            kind, _, q = p["candidate"].rpartition(":")
            slots[name] = [kind, int(q), {"reserve": True}]
            label_to_slot[p["candidate"]] = name
        for p in points:
            spectrum_slots.append({
                "slot": label_to_slot[p["candidate"]],
                "candidate": p["candidate"], "family": p["family"],
                "iota": p["iota"], "role": p.get("role"),
                "side": p.get("side"),
                "aliased": label_to_slot[p["candidate"]] not in names})
            if label_to_slot[p["candidate"]] not in names:
                aliases[p["candidate"]] = label_to_slot[p["candidate"]]
    return slots, aliases, spectrum_slots


def constraint_of(entry: Sequence[Any]) -> Constraint:
    kind, severity, flags = entry[0], int(entry[1]), dict(entry[2] or {})
    if kind == "B":
        return focal_constraint(severity)
    if kind == "A":
        return Constraint("A", severity)
    return Constraint(kind, severity, reserve=bool(flags.get("reserve", True)))


def frame_membership(fi: Mapping[str, Any], *, model_eligible: bool,
                     stability: Mapping[str, Any] | None) -> dict[str, Any]:
    if not fi.get("supported"):
        return {"frame": fi["frame"], "supported": False, "enters": False,
                "enters_local": False, "enters_spectrum": False,
                "gate2_status": fi.get("gate2_status"),
                "state": fi.get("state"), "arms": [],
                "reason": "no operating point at Gate 2"}
    local = bool(fi["local_supported"]) and model_eligible
    spectrum = bool(fi["coverage_identified"])
    runner_up: dict[str, int] = {}
    if local and stability is not None:
        runner_up = {k: int(v) for k, v in
                     (stability.get("runner_up_values") or {}).items()}
    arms = [ARM_BASE]
    if local:
        arms += [ARM_CORE, ARM_BACKUP]
    if spectrum:
        arms.append(ARM_SPECTRUM)
    if runner_up:
        arms.append(ARM_RUNNER_UP)
    slots, aliases, spectrum_slots = slot_map_of(fi, local=local,
                                                 spectrum=spectrum,
                                                 runner_up=runner_up)
    n_spec = len([s for s in spectrum_slots if not s["aliased"]])
    ru_slots = tuple(sorted(runner_up))
    out = {
        "frame": fi["frame"], "supported": True, "state": fi["state"],
        "enters_local": local, "enters_spectrum": spectrum,
        "enters": local or spectrum,
        "local_supported_on_own_table": bool(fi["local_supported"]),
        "model_local_eligible": model_eligible,
        "coverage_identified": spectrum,
        "n_star": fi["n_star"], "m_star": fi["m_star"], "iota_a": fi["iota_a"],
        "solo_compliance_b": fi["solo_compliance_b"],
        "local_valid_families": fi["local_valid_families"],
        "core": fi["core"] if local else [],
        "backups": fi["backups"] if local else [],
        "spectrum_points": spectrum_slots if spectrum else [],
        "spectrum_aliases": aliases,
        "n_spectrum_slots": n_spec if spectrum else 0,
        "arms": arms if (local or spectrum) else [],
        "runner_up_slots": list(ru_slots),
        "runner_up": ({"slots": list(ru_slots), "values": dict(runner_up),
                       "status": stability.get("status"),
                       "rule": "an OPERATING_POINT_UNSTABLE coordinate (frozen "
                               "value re-selected on < OPERATING_POINT_MIN_"
                               "RECOVERY of the topic resamples) adds its "
                               "runner-up as a sensitivity slot; Delta_R(f) at "
                               "the runner-up is descriptive and licenses no "
                               "claim; the frozen n*(f), m*(f) stand"}
                      if runner_up else None),
        "cells_per_block": (n_cells_for(arms, n_spectrum=n_spec,
                                        runner_up=ru_slots)
                            if (local or spectrum) else 0),
        "slot_map": slots if (local or spectrum) else {},
        "identification_statuses": fi["identification_statuses"],
        "stability": stability,
        "reference_sensitivity": ({
            "families": [r["family"] for r in fi["core"] + fi["backups"]],
            "distances": {r["slot"]: {"family": r["family"], "label": r["label"],
                                      "iota": r["iota"],
                                      "distance": abs(float(r["iota"]) - float(fi["iota_a"]))}
                          for r in fi["core"] + fi["backups"]},
            "admissible_triples": admissible_triples(fi["core"] + fi["backups"]),
            "rule": "Delta_R(f) is re-formed over every admissible triple "
                    "of the five frozen families from the same cells; a "
                    "descriptive family with its own simultaneous interval, "
                    "not a claim family"} if local else None),
        "reason": ("enters" if (local or spectrum) else
                   "LOCAL not supported or model ineligible; spectrum not "
                   "identified"),
    }
    return out


def membership_payload(tree: L.ConfirmTree, topup: Mapping[str, Any], *,
                       producing_commit: str, resamples: int = 2000
                       ) -> dict[str, Any]:
    registration = L.read_stage_record(tree, L.STAGE_REGISTERED)
    source = open_pilot(Path(registration["pilot_source"]["root"]),
                        tree.model_key, synthetic=tree.synthetic)
    gate3 = topup["reverdicted_gate3"]
    elig = gate3["local_eligibility"]
    model_eligible = bool(elig["local_eligible"])
    grid_a = source.scored_rows(PS.STAGE_GATE2, "grid-A")
    grid_b = source.scored_rows(PS.STAGE_GATE2, "grid-B")
    by_frame: dict[str, Any] = {}
    for w in PS.FRAMES:
        fi = frame_inputs(source, w, gate3_override=gate3)
        stab = None
        if fi.get("supported"):
            # Deterministic and domain-separated: the builtin hash() this
            # once used is salted per process (PYTHONHASHSEED), so the
            # distribution was not reproducible across runs.
            stab = frame_stability(grid_a, grid_b, frame=w,
                                   n_star=fi["n_star"], m_star=fi["m_star"],
                                   resamples=resamples,
                                   seed=seeds.bootstrap_seed(
                                       f"operating_point_stability:frame{w}",
                                       tree.model_key))
        by_frame[str(w)] = frame_membership(fi, model_eligible=model_eligible,
                                            stability=stab)
    local_frames = [int(w) for w, e in by_frame.items() if e["enters_local"]]
    spectrum_frames = [int(w) for w, e in by_frame.items()
                       if e["enters_spectrum"]]
    entering = sorted(set(local_frames) | set(spectrum_frames))
    projection = P.precision_at(max(1, len(local_frames)))
    return {
        "stage": L.STAGE_MEMBERSHIP,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_MEMBERSHIP],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"topup_record_hash": None,
                   "registration_manifest_hash": registration["manifest_hash"],
                   "pilot_record_hashes": source.as_record()["record_hashes"]},
        "local_eligibility": {
            "rule": elig["rule"], "min_frames": R.LOCAL_ELIGIBILITY_MIN_FRAMES,
            "supported_frames": elig["local_supported_frames"],
            "eligible": model_eligible,
            "after_topup": topup["topped_up"]},
        "by_frame": by_frame,
        "frames_entering_local": local_frames,
        "frames_entering_spectrum": spectrum_frames,
        "frames_entering": entering,
        "enters_study": bool(entering),
        "allocation_projection": {
            "n_local_frames": len(local_frames),
            "joint_family_size": projection["joint_family_size"],
            "blocks_per_frame": projection["blocks_per_frame"],
            "source": "rules.CONFIRMATORY_BLOCKS_PER_FRAME",
            "precondition_met_adverse": projection["precondition_met_adverse"],
            "precondition_met_planning": projection["precondition_met_planning"],
            "table": {s: {k: t[k] for k in
                          ("half_width_joint", "half_width_frame",
                           "meets_precondition_joint", "mde_80_joint")}
                      for s, t in projection["table"].items()}},
        "operating_point_stability": {
            "rule": "confirm.stability: §12.3 re-run on "
                    f"{R.OPERATING_POINT_BOOTSTRAP_RESAMPLES} topic-level "
                    "resamples per supported frame; status OPERATING_POINT_"
                    "UNSTABLE below OPERATING_POINT_MIN_RECOVERY; the frozen "
                    "point is never replaced",
            "min_recovery": R.OPERATING_POINT_MIN_RECOVERY,
            "by_frame": {w: ((e.get("stability") or {}).get("status"))
                         for w, e in by_frame.items()},
            "seed_rule": "seeds.bootstrap_seed('operating_point_stability:"
                         "frame<f>', model_key)"},
        "multiplicity_rule": P.MULTIPLICITY_RULE,
        "precision_rule": P.PRECISION_RULE,
        "estimands": {
            "primary": "Delta_R(f) per entering LOCAL frame and "
                       "configuration; delta_difficulty(f) and the §11.8 "
                       "slope per entering SPECTRUM frame and configuration",
            "conditional_on": "the frozen n*(f), m*(f), core references and "
                              "spectrum points; the stability block states "
                              "how reproducible each n*(f) was under the "
                              "calibration topics",
            "cross_frame": "reported side by side; a model-level LOCAL "
                           "claim is the conjunction over entering frames"},
        "no_composed_cells": True,
    }


def run_membership(tree: L.ConfirmTree, *, producing_commit: str | None = None,
                   environment_digest: str = "",
                   resamples: int = R.OPERATING_POINT_BOOTSTRAP_RESAMPLES
                   ) -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_MEMBERSHIP,
        compute=lambda prev: membership_payload(
            tree, prev, producing_commit=commit, resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)
