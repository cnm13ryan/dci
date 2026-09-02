"""Stage 6, ``CONFIRMATORY_ANALYSIS``: the registered estimators, per frame.

For every entering frame the frame's rows become one ``ObservationTable``
(``dci1v7.analysis.observations``: one cell mean per (cell, constituent)
over all M draws, block-indexed and nothing else), and v7's estimators
form every registered contrast **inside a block**; the block bootstrap
(``dci1v7.analysis.bootstrap.bootstrap_family``) resamples that frame's
blocks and gives each family its studentised maximum-modulus critical
value; the boundary allowance (``dci1v7.analysis.boundary``) widens the
decision interval in the open direction where a constituent cell sits at
an exact boundary; ``claims.delta_r_reading`` and friends read the
intervals against the registered thresholds.

What frame conditioning adds --- the **joint family** --- is the one new
statistic: per configuration, every F1 member of every entering frame is
resampled **by topic** with one draw shared across frames (the same topic
underlies each frame's block), and the maximum-modulus over all of them is
the joint critical value. The decision interval of every primary claim is
the joint one; the per-frame F1 interval is beside it. A model-level LOCAL
verdict is the conjunction over entering frames (``precision.
MULTIPLICITY_RULE``). The pre-registered reference-sensitivity family
re-forms Delta_R(f) over every admissible triple of {R1..R5} and is
reported with its own simultaneous interval; it licenses no claim.

Nothing here chooses: every threshold is the frozen one, every input is
asserted against the freeze hash, and the stage runs once.
"""
from __future__ import annotations

import math
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import get_model
from dci1v7.analysis import boundary as B
from dci1v7.analysis import claims as CL
from dci1v7.analysis import estimators as E
from dci1v7.analysis import spectrum as SP
from dci1v7.analysis.bootstrap import (FamilyResult, bootstrap_family,
                                       sidak_critical)
from dci1v7.analysis.observations import ObservationTable, build_observations
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.design import cell_types, normalise_arms
from dci1v8dev.confirm.freeze import load_freeze
from dci1v8dev.confirm.generation import collect_rows
from dci1v8dev.run.seeds import bootstrap_seed

__all__ = ["frame_table", "assert_frame_table", "frame_members",
           "spectrum_input", "delta_r_over", "joint_members",
           "analyse_model", "analysis_payload", "run_analysis",
           "MODEL_VERDICTS", "local_model_verdict"]

MODEL_VERDICTS = ("LOCAL_SUPPORTED_L3a", "LOCAL_SUPPORTED_L3b",
                  "LOCAL_EQUIVALENT_L3c", "FRAME_HETEROGENEOUS",
                  "INSUFFICIENT_PRECISION", "INDETERMINATE",
                  "UNIDENTIFIED")


# ------------------------------------------------------------------ tables
def frame_table(rows: Sequence[Mapping[str, Any]], frame: int, *,
                m_draws: int) -> ObservationTable:
    frows = [dict(r) for r in rows if int(r.get("block_frame", -1)) == frame]
    if not frows:
        raise IntegrityError(f"no confirmatory rows for frame {frame}")
    return ObservationTable(build_observations(frows, m_draws=m_draws))


def assert_frame_table(table: ObservationTable, *, arms: Sequence[str],
                       n_spectrum: int, blocks_expected: int) -> dict[str, Any]:
    """Every block carries exactly the frozen cell set (the within-block
    guarantee, on the confirmatory rows)."""
    expected = cell_types(normalise_arms(arms), n_spectrum=n_spectrum)
    missing: list[str] = []
    for block in table.blocks:
        for cell in expected:
            if cell.arm == "unconstrained":
                continue
            if cell.arm == "solo":
                try:
                    table.solo(block, cell.slots[0])
                except IntegrityError:
                    missing.append(f"{cell.cell_id}@{block}")
                continue
            first, second = cell.slots
            for outcome, companion in ((first, second), (second, first)):
                cfg = C.OUTCOME_FIRST if outcome == first else C.OUTCOME_SECOND
                if not table.has_composed(outcome, companion, cfg):
                    missing.append(f"{outcome}+{companion}:{cfg}@{block}")
    if missing:
        raise IntegrityError(f"{len(missing)} cell(s) missing from the "
                             f"within-block set, first: {missing[0]}")
    if len(table.blocks) != blocks_expected:
        raise ProtocolError(f"{len(table.blocks)} blocks, expected "
                            f"{blocks_expected}")
    return {"blocks": len(table.blocks), "cells_per_block":
            len(table.observations) // len(table.blocks),
            "cross_block_terms": 0}


# -------------------------------------------------------------- estimators
def delta_r_over(table: ObservationTable, slots: Sequence[str],
                 configuration: str) -> list[float]:
    """Delta_R re-formed over an arbitrary reference triple (the
    reference-sensitivity family); the cancelled form."""
    with_refs = E.mean_vectors([E.composed_vector(table, "B", r, configuration)
                                for r in slots])
    with_a = E.composed_vector(table, "B", "A", configuration)
    return [r - a for r, a in zip(with_refs, with_a)]


def spectrum_input(table: ObservationTable, frozen: Mapping[str, Any],
                   configuration: str) -> SP.SpectrumInput | None:
    points = frozen.get("spectrum_points") or []
    if not points:
        return None
    family_of = {p["slot"]: p["family"] for p in points}
    for s in family_of:
        if not table.has_composed("B", s, configuration):
            return None
    if not table.has_composed("B", "A", configuration):
        return None
    b_with = {s: E.composed_vector(table, "B", s, configuration) for s in family_of}
    b_with["A"] = E.composed_vector(table, "B", "A", configuration)
    return SP.SpectrumInput(
        blocks=tuple(table.blocks), family_of=family_of,
        b_solo=E.solo_vector(table, "B"), b_with=b_with,
        companion_solo={s: E.solo_vector(table, s) for s in family_of},
        companion_chance={s: E.chance_vector(table, s) for s in family_of},
        a_solo=E.solo_vector(table, "A"), a_chance=E.chance_vector(table, "A"))


def frame_members(table: ObservationTable, frozen: Mapping[str, Any],
                  configuration: str) -> dict[str, dict[str, Any]]:
    """Every registered member this frame supports, by family, as per-block
    vectors or refit callables."""
    local = bool(frozen["enters_local"])
    spectrum = bool(frozen["enters_spectrum"])
    fam: dict[str, dict[str, Any]] = {}
    f1: dict[str, Any] = {
        "D(B<-A)": E.delivery_loss(table, "B", "A", configuration),
        "D(A<-B)": E.delivery_loss(table, "A", "B", configuration),
        "Lambda": E.asymmetry(table, configuration)}
    if local:
        f1["Delta_R"] = E.delta_r(table, configuration)
        f1["Xi"] = E.xi(table, configuration)
        refs = E.reference_slots(table)
        fam["F2"] = {**{f"D(B<-{r})": E.delivery_loss(table, "B", r, configuration)
                        for r in refs},
                     **{f"Delta_{i + 1}": E.delta_j(table, r, configuration)
                        for i, r in enumerate(refs)}}
        fam["F3"] = {**{f"D(A<-{r})": E.delivery_loss(table, "A", r, configuration)
                        for r in refs},
                     "Delta^A": E.delta_a(table, configuration)}
        fam["F4"] = {"D(Rbar<-A)": E.d_rbar_from(table, "A", configuration),
                     "D(Rbar<-B)": E.d_rbar_from(table, "B", configuration),
                     "D(Rbar<-Rbar')": E.d_rbar_rbar(table, configuration)}
        sens = frozen.get("reference_sensitivity") or {}
        fam["F_REFSENS"] = {
            "Delta_R[" + "+".join(t["slots"]) + "]":
                delta_r_over(table, t["slots"], configuration)
            for t in sens.get("admissible_triples", ())}
    if spectrum:
        data = spectrum_input(table, frozen, configuration)
        if data is not None:
            f1["delta_difficulty"] = (lambda picks, d=data:
                                      float(SP.estimate(d, picks)["delta_difficulty"]))
            fam["F_SPECTRUM"] = {"slope": (lambda picks, d=data:
                                           float(SP.estimate(d, picks).get(
                                               "slope", float("nan"))))}
            fam["_spectrum_point"] = {"data": data}
    fam["F1"] = f1
    return fam


def order_members(table: ObservationTable, local: bool) -> dict[str, Any]:
    out = {"Ord_A": E.ord_a(table), "Ord_B": E.ord_b(table),
           "Ord_Lambda": E.ord_lambda(table)}
    if local:
        out["Ord_Rbar"] = E.ord_rbar(table)
    return out


# --------------------------------------------------------------- intervals
def _member_dict(m: Any) -> dict[str, Any]:
    d = asdict(m)
    return {k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in d.items()}


def _interval(table: ObservationTable, member: str, configuration: str | None,
              estimate: float, se: float, critical: float,
              references: Sequence[str]) -> tuple[CL.Interval, dict[str, Any] | None]:
    try:
        bound = B.contrast_boundary_from_table(table, member, configuration,
                                               references=references)
    except (ProtocolError, IntegrityError, KeyError, ValueError):
        bound = None
    lo, hi = estimate - critical * se, estimate + critical * se
    lo, hi = B.apply_allowance(lo, hi, bound)
    return CL.Interval(member=member, estimate=estimate, lower=lo, upper=hi,
                       boundary=bound), bound


def _precondition(iv: CL.Interval) -> bool | None:
    try:
        return bool(iv.meets_precondition())
    except ProtocolError:
        return None


def _reading(member: str, iv: CL.Interval, *, support: Mapping[str, Any] | None
             ) -> dict[str, Any]:
    if member == "Delta_R":
        return CL.delta_r_reading(iv)
    if member == "delta_difficulty":
        return CL.delta_difficulty_reading(iv, support or {"holds": False})
    direction = CL.contrast_direction(iv)
    return {"levels": [], "markers": ([] if _precondition(iv) in (True, None)
                                      else ["INSUFFICIENT_PRECISION"]),
            "direction": direction, "statuses": CL.boundary_statuses(iv)}


def joint_members(per_frame: Mapping[int, Mapping[str, Any]],
                  block_positions: Mapping[int, Sequence[int]],
                  n_positions: int) -> dict[str, Callable[[Sequence[int]], float]]:
    """Every (frame, F1 member) as a function of a TOPIC resample."""
    out: dict[str, Callable[[Sequence[int]], float]] = {}
    for frame, members in sorted(per_frame.items()):
        pos_to_idx = {p: i for i, p in enumerate(block_positions[frame])}
        for name, member in members.items():
            def f(picks, member=member, pos_to_idx=pos_to_idx):
                idx = [pos_to_idx[p] for p in picks if p in pos_to_idx]
                if not idx:
                    return float("nan")
                if callable(member):
                    return float(member(idx))
                return sum(member[i] for i in idx) / len(idx)
            out[f"f{frame}:{name}"] = f
    return out


def local_model_verdict(readings: Mapping[int, Mapping[str, Any]]
                        ) -> dict[str, Any]:
    """The conjunction over entering LOCAL frames of the Delta_R readings on
    the joint interval (one configuration)."""
    if not readings:
        return {"verdict": "UNIDENTIFIED", "frames": {},
                "rule": P.MULTIPLICITY_RULE}
    per = {}
    for w, r in readings.items():
        levels = set(r.get("levels", ()))
        markers = set(r.get("markers", ()))
        if "INSUFFICIENT_PRECISION" in markers:
            per[w] = "INSUFFICIENT_PRECISION"
        elif "L3b" in levels:
            per[w] = "L3b"
        elif "L3a" in levels:
            per[w] = "L3a"
        elif "L3c" in levels:
            per[w] = "L3c"
        else:
            per[w] = "INDETERMINATE"
    values = set(per.values())
    if "INSUFFICIENT_PRECISION" in values:
        verdict = "INSUFFICIENT_PRECISION"
    elif len(values) == 1:
        v = next(iter(values))
        verdict = {"L3a": "LOCAL_SUPPORTED_L3a", "L3b": "LOCAL_SUPPORTED_L3b",
                   "L3c": "LOCAL_EQUIVALENT_L3c",
                   "INDETERMINATE": "INDETERMINATE"}[v]
    elif values <= {"L3a", "L3b"}:
        verdict = "LOCAL_SUPPORTED_L3a"      # every frame beyond the generic threshold
    else:
        verdict = "FRAME_HETEROGENEOUS"
    return {"verdict": verdict, "frames": {str(w): v for w, v in per.items()},
            "rule": "conjunction over entering LOCAL frames on the joint "
                    "decision interval; heterogeneity is a verdict, not a "
                    "support claim"}


# ----------------------------------------------------------------- driver
def analyse_model(rows: Sequence[Mapping[str, Any]], freeze: Mapping[str, Any],
                  *, model_id: str, resamples: int) -> dict[str, Any]:
    design = freeze["design"]
    m_draws = int(design["draws"])
    frames = {int(w): e for w, e in design["frames"].items()}
    tables: dict[int, ObservationTable] = {}
    checks: dict[str, Any] = {}
    for w, e in frames.items():
        t = frame_table(rows, w, m_draws=m_draws)
        checks[str(w)] = assert_frame_table(
            t, arms=e["arms"], n_spectrum=int(e["n_spectrum_slots"]),
            blocks_expected=len({r["block_id"] for r in rows
                                 if int(r.get("block_frame", -1)) == w}))
        tables[w] = t
    references = list(C.CORE_SLOTS)
    result: dict[str, Any] = {"frames": {}, "joint": {}, "model_verdict": {},
                              "within_block": checks}
    joint_f1: dict[str, dict[int, dict[str, Any]]] = {c: {} for c in C.CONFIGURATIONS}
    positions: dict[int, list[int]] = {}
    for w, t in tables.items():
        positions[w] = [int(b.rpartition("-")[2]) // C.N_WORDINGS for b in t.blocks]
        fr: dict[str, Any] = {"frame": w, "blocks": len(t.blocks),
                              "enters_local": frames[w]["enters_local"],
                              "enters_spectrum": frames[w]["enters_spectrum"],
                              "configurations": {}, "algebraic_forms": {}}
        for cfg in C.CONFIGURATIONS:
            members = frame_members(t, frames[w], cfg)
            point = members.pop("_spectrum_point", None)
            if frames[w]["enters_local"]:
                fr["algebraic_forms"][cfg] = {
                    "Delta_R": E.assert_delta_r_forms(t, cfg)}
            families: dict[str, Any] = {}
            support = None
            if point is not None:
                est = SP.estimate(point["data"])
                support = est["support"]
                fr.setdefault("spectrum_fit", {})[cfg] = {
                    k: est[k] for k in ("degenerate", "difficulty_a",
                                        "D_B_from_A", "delta_difficulty",
                                        "support", "dropped_points")
                    if k in est}
                if not est.get("degenerate"):
                    fr["spectrum_fit"][cfg].update({
                        "slope": est["slope"], "intercepts": est["intercepts"],
                        "predicted_at_A": est["predicted_at_A"],
                        "residuals": est["residuals"]})
            for fname, fmembers in members.items():
                if not fmembers:
                    continue
                res: FamilyResult = bootstrap_family(
                    fmembers, seed=bootstrap_seed(f"{fname}:{cfg}:f{w}", model_id),
                    configuration=cfg, family=fname, n_blocks=len(t.blocks),
                    resamples=resamples)
                fam_out: dict[str, Any] = {
                    "critical_value": res.critical_value,
                    "sidak_reference": sidak_critical(len(fmembers)),
                    "resamples": res.resamples, "blocks": res.blocks,
                    "members": {}}
                for name, m in res.members.items():
                    iv, bound = _interval(t, name, cfg, m.estimate,
                                          m.standard_error, res.critical_value,
                                          references)
                    fam_out["members"][name] = {
                        **_member_dict(m),
                        "decision_lower": iv.lower, "decision_upper": iv.upper,
                        "decision_half_width": iv.half_width,
                        "boundary": bound,
                        "meets_precondition": _precondition(iv),
                        "reading": _reading(name, iv, support=support),
                        "per_block": (None if callable(fmembers[name])
                                      else list(fmembers[name]))}
                families[fname] = fam_out
            fr["configurations"][cfg] = families
            joint_f1[cfg][w] = dict(members["F1"])
        ords = order_members(t, frames[w]["enters_local"])
        fr["algebraic_forms"]["order"] = E.assert_order_forms(t)
        res = bootstrap_family(ords, seed=bootstrap_seed(f"F11:f{w}", model_id),
                               configuration="cross-configuration",
                               family="F11", n_blocks=len(t.blocks),
                               resamples=resamples)
        fr["F11"] = {"critical_value": res.critical_value,
                     "members": {name: {**_member_dict(m),
                                        "meets_precondition": _precondition(
                                            CL.Interval(name, m.estimate,
                                                        m.simultaneous_lower,
                                                        m.simultaneous_upper))}
                                 for name, m in res.members.items()}}
        result["frames"][str(w)] = fr
    # -------------------------------------------------------- joint family
    n_positions = 1 + max(p for ps in positions.values() for p in ps)
    for cfg in C.CONFIGURATIONS:
        jm = joint_members(joint_f1[cfg], positions, n_positions)
        res = bootstrap_family(jm, seed=bootstrap_seed(f"JOINT_F1:{cfg}", model_id),
                               configuration=cfg, family="JOINT_F1",
                               n_blocks=n_positions, resamples=resamples)
        joint: dict[str, Any] = {
            "critical_value": res.critical_value,
            "sidak_reference": sidak_critical(len(jm)),
            "family_size": len(jm), "topics": n_positions,
            "members": {}}
        delta_readings: dict[int, dict[str, Any]] = {}
        for name, m in res.members.items():
            w = int(name.partition(":")[0][1:])
            member = name.partition(":")[2]
            t = tables[w]
            iv, bound = _interval(t, member, cfg, m.estimate, m.standard_error,
                                  res.critical_value, references)
            support = (result["frames"][str(w)].get("spectrum_fit", {})
                       .get(cfg, {}).get("support"))
            reading = _reading(member, iv, support=support)
            joint["members"][name] = {
                **_member_dict(m), "frame": w, "member": member,
                "decision_lower": iv.lower, "decision_upper": iv.upper,
                "decision_half_width": iv.half_width,
                "meets_precondition": _precondition(iv), "reading": reading}
            if member == "Delta_R":
                delta_readings[w] = reading
        joint["local_model_verdict"] = local_model_verdict(delta_readings)
        result["joint"][cfg] = joint
        result["model_verdict"][cfg] = joint["local_model_verdict"]["verdict"]
    return result


def analysis_payload(tree: L.ConfirmTree, *, producing_commit: str,
                     resamples: int | None = None) -> dict[str, Any]:
    freeze, freeze_hash = load_freeze(tree)
    gen = L.read_stage_record(tree, L.STAGE_GENERATION)
    if gen.get("freeze_hash") != freeze_hash:
        raise IntegrityError("the generation record was signed under a "
                             "different freeze")
    if resamples is not None and not tree.synthetic:
        raise ProtocolError("resamples is a synthetic-namespace knob")
    resamples = resamples or C.BOOTSTRAP_RESAMPLES
    rows = collect_rows(tree)
    if len(rows) != int(gen["n_rows"]):
        raise IntegrityError(f"{len(rows)} rows on disk; the generation "
                             f"record counted {gen['n_rows']}")
    spec = get_model(tree.model_key)
    result = analyse_model(rows, freeze, model_id=spec.model_id,
                           resamples=resamples)
    return {
        "stage": L.STAGE_ANALYSIS,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_ANALYSIS],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"freeze_hash": freeze_hash,
                   "generation_record_hash":
                       fs.read_json(tree.stage_record(L.STAGE_GENERATION))["record_hash"]},
        "freeze_hash": freeze_hash, "resamples": resamples,
        "n_rows": len(rows), "protected": True,
        "multiplicity_rule": P.MULTIPLICITY_RULE,
        **result,
    }


def run_analysis(tree: L.ConfirmTree, *, producing_commit: str | None = None,
                 environment_digest: str = "", resamples: int | None = None
                 ) -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_ANALYSIS,
        compute=lambda _prev: analysis_payload(tree, producing_commit=commit,
                                               resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)
