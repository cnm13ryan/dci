"""Read-only replay over stored evidence: the failure table, the backtest,
the emulated second pass, leave-one-model-out checks, and the spectrum
replay.

Every function here reads signed records from an evidence root and writes
nothing under it. The twelve replications with a pre-screen record and a
Gate-2 record (registered v7 x4, registered v6 x4, and the four completed
development rehearsals) are the population; a root whose Gate 2 is still
being written is not read.

**The honest backtest.** The historical pre-screen is applied *as if
calibration were unknown*; the calibrated verdict is then revealed from the
Gate-2 rows with the production kernels (``regime.calibration_coverage_rows``
+ ``regime.coverage_criterion`` at Gate 2's iota_A) and compared. The second
pass never ran historically, so it is **emulated** by carving batches of 24
topics x 1 draw out of Calibration-A's per-topic rows (a seeded Bernoulli
per topic from that topic's mean) and evaluating the calibrated verdict on
**Calibration-B alone**, which shares no topic with the carved batches.
Reserve rungs and A's grid were not measured on the splits, so the emulated
second pass gets neither --- it is a conservative emulation. The pooled
verdict (the study's own) is reported beside it.

**The chance basis.** The signed Gate-2 tables carry the zero chance column
(`CHANGES_SCIENTIFIC.md` 2026-08-29, "in force: §13.11's chance column");
``load_replication`` therefore reads the §13.2 unconstrained-cell basis from
the read-only cache ``dci1v8dev.chance_basis`` builds and replays every rule
on the corrected table, with ι_A restated on the same basis. A replay on the
recorded column is refused unless asked for by name (``allow_recorded_chance``),
because its V_chance and lift verdicts are vacuous and every ι is raw solo.

**Thresholds are prospective.** ``accept`` / ``reject`` come from the
simulation; the leave-one-model-out routine reports what threshold choice
on the other three models would have done on the held-out one, and is
labelled retrospective development.
"""
from __future__ import annotations

import json
import pathlib
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages import regime as regime_stage
from dci1v7.stages import stability as stability_stage
from dci1v7.stages.calibration_table import load_calibration_table
from dci1v7.verifiers.constraints import FAMILIES
from dci1v8dev import chance_basis as CB
from dci1v8dev.prescreen import legacy
from dci1v8dev.prescreen.geometry import Geometry, evaluate_draws
from dci1v8dev.prescreen.rescreen import RescreenBatch, RescreenConfig, run_rescreen

#: The emulated second pass gets no A-grid re-measurement (not on the splits).
EMULATED_RESCREEN_CONFIG = RescreenConfig(include_a_grid=False)
from dci1v8dev.prescreen.retention import (
    DEFAULT_RETENTION_CONFIG,
    RetentionConfig,
    retain,
)
from dci1v8dev.prescreen.schema import (
    ARung,
    PrescreenRung,
    a_rung_from_rates,
    rung_from_rates,
)
from dci1v8dev.prescreen.screen import (
    DEFAULT_SCREEN_CONFIG,
    ScreenConfig,
    screen_families,
)
from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.selection import (
    DEFAULT_SELECTION_RULE,
    SelectionRule,
    select_spectrum,
)
from dci1v8dev.spectrum.validity import SpectrumRule, classify_pool

__all__ = [
    "FAILURE_CAUSES",
    "REPLICATIONS",
    "backtest_replication",
    "calibrated_truth",
    "failure_cause",
    "leave_one_model_out",
    "load_replication",
    "metrics",
    "prescreen_input",
    "spectrum_backtest",
]

#: (tree label, model key, path relative to dci1/evidence)
REPLICATIONS: tuple[tuple[str, str, str], ...] = (
    ("v7", "gemma-3n-e2b-it", "dci1v7/gemma-3n-e2b-it"),
    ("v7", "gemma-3n-e4b-it", "dci1v7/gemma-3n-e4b-it"),
    ("v7", "qwen3-4b", "dci1v7/qwen3-4b"),
    ("v7", "qwen3-4b-instruct-2507", "dci1v7/qwen3-4b-instruct-2507"),
    ("v6", "gemma-3n-e2b-it", "dci1v6/gemma-3n-e2b-it"),
    ("v6", "gemma-3n-e4b-it", "dci1v6/gemma-3n-e4b-it"),
    ("v6", "qwen3-4b", "dci1v6/qwen3-4b"),
    ("v6", "qwen3-4b-instruct-2507", "dci1v6/qwen3-4b-instruct-2507"),
    ("dev", "qwen3-4b", "dci1v7-development/evidence/dci1v7/qwen3-4b"),
    ("r3", "qwen3-4b", "dci1v7-development-r3/evidence/dci1v7/qwen3-4b"),
    ("r3", "gemma-3n-e2b-it",
     "dci1v7-development-r3/evidence/dci1v7/gemma-3n-e2b-it"),
    ("r4", "qwen3-4b-instruct-2507",
     "dci1v7-development-r4/evidence/dci1v7/qwen3-4b-instruct-2507"),
)

STAGE_FILES = {
    "regime": ("REGIME_SCREEN", "regime_record.json"),
    "gate2": ("GATE_2_FOCAL_CALIBRATION", "gate2_focal_calibration.json"),
    "gate2_5": ("GATE_2_5_CANDIDATE_QUALIFICATION",
                "gate2_5_candidate_qualification.json"),
    "gate3a": ("GATE_3A_REFERENCE_CALIBRATION",
               "gate3a_reference_calibration.json"),
    "gate3b": ("GATE_3B_REFERENCE_SELECTION",
               "gate3b_reference_selection.json"),
    "gate3c": ("GATE_3C_IDENTIFICATION", "gate3c_identification.json"),
}

FAILURE_CAUSES = ("NOISY_SPAN_INFLATION", "ELIGIBILITY_TRIMMING",
                  "MISSING_SIDE", "IOTA_A_MOVED", "FLAT_LADDER",
                  "NON_MONOTONIC", "RETENTION_ARTIFACT", "OTHER")


def load_replication(evidence_root: pathlib.Path, rel: str, *,
                     chance_cache_dir: pathlib.Path | None = None,
                     tree: str | None = None, model: str | None = None,
                     allow_recorded_chance: bool = False) -> dict[str, Any]:
    """The stage records of one replication, with the Gate-2 table on the
    corrected chance basis when a cache directory is given (the default for
    every tool). ``gate2_recorded`` keeps the signed record as read."""
    model_dir = pathlib.Path(evidence_root) / rel
    out: dict[str, Any] = {"model_dir": str(model_dir)}
    for key, (stage, name) in STAGE_FILES.items():
        path = model_dir / stage / name
        if path.exists():
            with open(path) as f:
                out[key] = json.load(f)
        else:
            out[key] = None
    out["gate2_recorded"] = out["gate2"]
    out["chance_basis"] = None
    if out["gate2"] is not None:
        if chance_cache_dir is not None:
            if tree is None or model is None:
                raise ValueError("tree and model name the cache file")
            cache = CB.read_cache(pathlib.Path(chance_cache_dir), tree=tree, model=model)
            out["gate2"] = CB.corrected_gate2(out["gate2"], cache)
            out["chance_basis"] = "unconstrained-cell (§13.2, corrected; dci1v8dev.chance_basis)"
            out["regime_recorded"] = out["regime"]
            if out["regime"] is not None and cache.get("prescreen"):
                out["regime"] = CB.corrected_regime(out["regime"], cache["prescreen"])
                out["chance_basis"] += "; pre-screen κ on the ladder run's unconstrained cell"
        elif allow_recorded_chance:
            out["chance_basis"] = "RECORDED zero column (development only; V_chance/lift vacuous)"
        else:
            raise ProtocolError(
                "a v8 backtest reads the Gate-2 table on the §13.2 chance basis; "
                "pass chance_cache_dir (tools/v8_chance_basis_cache.py) or say "
                "allow_recorded_chance=True to replay the recorded zero column")
    return out


def prescreen_input(regime: Mapping[str, Any]
                    ) -> tuple[list[PrescreenRung], list[ARung]]:
    table, a_grid = [], []
    for row in regime["difficulty_table"]:
        if row["kind"] == "A":
            a_grid.append(a_rung_from_rates(
                row["severity"], solo=row["solo"], chance=row["chance"],
                n_topics=row["n_topics"]))
        elif row["kind"] == "B" or row["kind"] not in FAMILIES:
            continue
        else:
            table.append(rung_from_rates(
                row["kind"], row["severity"], solo=row["solo"],
                chance=row["chance"], vacuity=row["vacuity"],
                n_topics=row["n_topics"]))
    return table, a_grid


def _point_events(rows: Sequence[Mapping[str, Any]], *, iota_a: float,
                  geometry: Geometry, chance_max: float, lift_min: float
                  ) -> dict[str, dict[str, Any]]:
    """My geometry events on point estimates, per family, from rows in the
    ``calibration_coverage_rows`` shape (solo, iota, vacuity...)."""
    by_family: dict[str, list[Mapping[str, Any]]] = {}
    for r in rows:
        by_family.setdefault(r["family"], []).append(r)
    out = {}
    for fam, entries in sorted(by_family.items()):
        p = np.array([[e["solo"] for e in entries]])
        # kappa from the recorded iota: solo = kappa + iota (1 - kappa)
        kappa = np.array([[0.0 if e["iota"] is None or e["iota"] == 1.0
                           else max(0.0, (e["solo"] - e["iota"])
                                    / (1.0 - e["iota"]))
                           for e in entries]])
        vac = np.array([[e["vacuity"] if e["vacuity"] is not None else 1.0
                         for e in entries]])
        ia = np.array([iota_a])
        ev = evaluate_draws(p, kappa, vac, ia, geometry=geometry)
        extra = (kappa <= chance_max) & ((p - kappa) >= lift_min)
        lv = evaluate_draws(np.where(extra, p, -1.0), kappa, vac, ia,
                            geometry=geometry)
        av = evaluate_draws(np.where(extra, p, -1.0), kappa, vac, ia,
                            geometry=geometry, band=geometry.spectrum_band)
        ia0 = float(ia[0])
        adm = av.eligible[0]
        out[fam] = {"c4": bool(ev.c4[0]), "support_both": bool(av.support_both[0]),
                    "support_below": bool(av.support_below[0]),
                    "support_above": bool(av.support_above[0]),
                    "local": bool(lv.family_local[0]),
                    "n_eligible": int(ev.n_eligible[0]),
                    "span": float(ev.span[0]),
                    "eligible": [e["candidate"] for e, ok in
                                 zip(entries, ev.eligible[0]) if ok],
                    "local_rungs": [e["candidate"] for e, ok in
                                    zip(entries, lv.local[0]) if ok],
                    "admissible_below_d": [
                        e["candidate"] for e, ok, io in
                        zip(entries, adm, av.iota[0])
                        if ok and io <= ia0 - geometry.d_below],
                    "admissible_above_d": [
                        e["candidate"] for e, ok, io in
                        zip(entries, adm, av.iota[0])
                        if ok and io >= ia0 + geometry.d_above]}
    return out


def calibrated_truth(gate2: Mapping[str, Any], regime: Mapping[str, Any], *,
                     geometry: Geometry, chance_max: float, lift_min: float,
                     split: str = "pooled") -> dict[str, Any]:
    """The calibrated verdict per family with the production kernels, on
    ``split`` (pooled = the study's own basis)."""
    formulation = regime.get("coverage_eligibility_formulation") or "E2"
    rows = regime_stage.calibration_coverage_rows(
        gate2["calibration_rows"][split], formulation=formulation)
    iota_a = (float(gate2["iota_a"]) if split == "pooled"
              else float(gate2["iota_a_by_split"][split]))
    states = legacy.family_c4_states(rows, iota_a=iota_a)
    coverage = regime_stage.coverage_criterion(rows, iota_a=iota_a)
    events = _point_events(rows, iota_a=iota_a, geometry=geometry,
                           chance_max=chance_max, lift_min=lift_min)
    per_family = {}
    for fam in sorted(set(states) | set(events)):
        st = states.get(fam, {})
        per_family[fam] = {**events.get(fam, {}),
                           "c4_production": bool(st.get("c4_met", False)),
                           "deficiency": st.get("deficiency"),
                           "span_production": st.get("span"),
                           "n_rungs_production": st.get("n_rungs"),
                           "has_below": st.get("has_below"),
                           "has_above": st.get("has_above"),
                           "calibrated_rungs": [r["candidate"] for r in rows
                                                if r["family"] == fam],
                           "eligible_rungs_calibrated": [
                               r["candidate"] for r in rows
                               if r["family"] == fam and r["eligible"]]}
    return {"split": split, "iota_a": iota_a, "coverage": coverage,
            "families": per_family, "rows": rows}


def failure_cause(pre: Mapping[str, Any], cal: Mapping[str, Any], *,
                  pre_same_rungs: Mapping[str, Any] | None,
                  pre_at_cal_iota_a: Mapping[str, Any] | None,
                  ladder_class: str | None, carried: bool) -> str | None:
    """Classify a pre-screen PASS that became a calibration FAIL."""
    if not pre.get("c4_met") or cal.get("c4_production"):
        return None
    if not carried or (pre_same_rungs is not None
                       and not pre_same_rungs.get("c4_met")
                       and pre_same_rungs.get("n_rungs", 0)
                       < pre.get("n_rungs", 0)):
        return "RETENTION_ARTIFACT"
    deficiency = cal.get("deficiency")
    if deficiency == "MISSING_SIDE":
        if pre_at_cal_iota_a is not None and \
                pre_at_cal_iota_a.get("deficiency") == "MISSING_SIDE":
            return "IOTA_A_MOVED"
        return "MISSING_SIDE"
    if deficiency == "TOO_FEW_RUNGS":
        return "ELIGIBILITY_TRIMMING"
    if deficiency == "SPAN_SHORT":
        lost = pre.get("n_rungs", 0) - cal.get("n_rungs_production", 0)
        pre_span = (pre_same_rungs or pre).get("span", 0.0)
        cal_span = cal.get("span_production", 0.0) or 0.0
        if lost > 0 and pre_span >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN \
                and cal_span < C.COVERAGE_MIN_WITHIN_FAMILY_SPAN:
            return "ELIGIBILITY_TRIMMING"
        if ladder_class == "NON_MONOTONIC_LADDER":
            return "NON_MONOTONIC"
        if cal_span < 0.20:
            return "FLAT_LADDER"
        if pre_span - cal_span > 0.10:
            return "NOISY_SPAN_INFLATION"
        return "NOISY_SPAN_INFLATION" if pre_span >= cal_span else "OTHER"
    return "OTHER"


def carve_measure(gate2: Mapping[str, Any], table: Sequence[PrescreenRung], *,
                  split: str = C.CALIBRATION_A, seed: int = 11,
                  batch_topics: int = 24) -> Callable[[RescreenBatch], Any]:
    """A ``measure`` for ``run_rescreen`` that draws batches out of one
    calibration split's per-topic rows (see module docstring)."""
    rows = {f"{r['kind']}:{r['severity']}": r
            for r in gate2["calibration_rows"][split]}
    pre = {r.label: r for r in table}
    rng = np.random.default_rng(seed)
    used: dict[str, int] = {}
    unavailable: list[str] = []

    def measure(batch: RescreenBatch):
        new: list[PrescreenRung] = []
        for kind, fam in batch.families.items():
            for q in list(fam["severities"]) + list(fam["reserve_picks"]):
                label = f"{kind}:{q}"
                row = rows.get(label)
                if row is None:
                    unavailable.append(label)
                    continue
                per_topic = row["per_topic_solo"]
                start = used.get(label, 0)
                if start + batch_topics > len(per_topic):
                    unavailable.append(label)
                    continue
                used[label] = start + batch_topics
                means = np.array(per_topic[start:start + batch_topics])
                k = int(rng.binomial(1, means).sum().item())
                base = pre.get(label)
                chance_rate = (base.chance_rate if base is not None
                               else float(row.get("prescreen_chance_compliance")
                                          or 0.0))
                vac = round(float(row.get("solo_vacuity") or 0.0) * batch_topics)
                new.append(PrescreenRung(
                    kind=kind, severity=q, solo_k=k, solo_n=batch_topics,
                    chance_k=chance_rate * batch_topics,
                    chance_n=float(batch_topics), vacuous_k=min(vac, k),
                    n_topics=batch_topics, draws_per_topic=1,
                    reserve=q not in {r.severity for r in table
                                      if r.kind == kind}))
        return new, []

    measure.unavailable = unavailable        # type: ignore[attr-defined]
    return measure


def backtest_replication(rep: Mapping[str, Any], *, label: str, model: str,
                         screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                         rescreen_config: RescreenConfig = EMULATED_RESCREEN_CONFIG,
                         retention_config: RetentionConfig = DEFAULT_RETENTION_CONFIG,
                         emulate_rescreen: bool = True) -> dict[str, Any]:
    regime = rep["regime"]
    gate2 = rep["gate2"]
    table, a_grid = prescreen_input(regime)
    geometry = screen_config.geometry
    cert = legacy.legacy_certificate(table, a_grid)
    pre_families = cert["families"]
    iota_a_pre = cert["iota_a_prescreen"]
    truth = calibrated_truth(gate2, regime, geometry=geometry,
                             chance_max=screen_config.chance_max,
                             lift_min=screen_config.lift_min, split="pooled")
    truth_b = calibrated_truth(gate2, regime, geometry=geometry,
                               chance_max=screen_config.chance_max,
                               lift_min=screen_config.lift_min,
                               split=C.CALIBRATION_B)
    iota_a_cal = truth["iota_a"]
    # the pre-screen table restricted to the calibrated rungs, at both
    # reference points --- what separates retention from noise from drift
    calibrated_labels = {r["candidate"] for r in truth["rows"]}
    pre_rows_same = [r for r in cert["rows"] if r["candidate"] in calibrated_labels]
    pre_same = legacy.family_c4_states(pre_rows_same, iota_a=iota_a_pre)
    pre_same_at_cal = legacy.family_c4_states(pre_rows_same, iota_a=iota_a_cal)
    stage1 = screen_families(table, a_grid, config=screen_config)
    rescreen = None
    final = stage1
    measure = None
    if emulate_rescreen:
        measure = carve_measure(gate2, table, split=C.CALIBRATION_A)
        rescreen = run_rescreen(table, a_grid, screen_config=screen_config,
                                config=rescreen_config, measure=measure)
        final = rescreen["screen"]
    retention = retain(final, config=retention_config)
    forwarded = {e["candidate"] for e in retention["forwarded"]}
    legacy_kept = legacy.legacy_retention(table, iota_a=iota_a_pre)
    legacy_forwarded = set(legacy_kept["tier12"]) | set(legacy_kept["tier3_measured"])
    families = sorted(set(pre_families) | set(truth["families"]))
    rows = []
    for fam in families:
        pre = pre_families.get(fam, {})
        cal = truth["families"].get(fam, {})
        calb = truth_b["families"].get(fam, {})
        v1 = stage1["families"].get(fam)
        vf = final["families"].get(fam)
        carried = bool(cal.get("calibrated_rungs"))
        cause = failure_cause(
            pre, cal, pre_same_rungs=pre_same.get(fam),
            pre_at_cal_iota_a=pre_same_at_cal.get(fam),
            ladder_class=(vf or {}).get("ladder", {}).get("ladder_class"),
            carried=carried)
        rows.append({
            "tree": label, "model": model, "family": fam,
            "structural_tier": FAMILIES[fam].structural_tier,
            "feature_group": FAMILIES[fam].feature_group,
            "prescreen_span": pre.get("span"),
            "prescreen_n_eligible": pre.get("n_rungs"),
            "prescreen_straddle": bool(pre.get("has_below")
                                       and pre.get("has_above")),
            "prescreen_c4": bool(pre.get("c4_met", False)),
            "prescreen_span_same_rungs": (pre_same.get(fam) or {}).get("span"),
            "calibration_span": cal.get("span_production"),
            "calibration_n_eligible": cal.get("n_rungs_production"),
            "calibration_straddle": bool(cal.get("has_below")
                                         and cal.get("has_above")),
            "calibration_c4": bool(cal.get("c4_production", False)),
            "calibration_deficiency": cal.get("deficiency"),
            "calibration_support_both": bool(cal.get("support_both", False)),
            "calibration_local": bool(cal.get("local", False)),
            "calibration_b_c4": bool(calb.get("c4_production", False)),
            "calibration_b_support_both": bool(calb.get("support_both", False)),
            "calibration_b_local": bool(calb.get("local", False)),
            "rungs_disappeared": sorted(
                {r["candidate"] for r in cert["rows"]
                 if r["family"] == fam and r["eligible"]}
                - set(cal.get("eligible_rungs_calibrated", []))),
            "rungs_not_calibrated": sorted(
                {r["candidate"] for r in cert["rows"] if r["family"] == fam}
                - set(cal.get("calibrated_rungs", []))),
            "failure_cause": cause,
            "stage1_status": v1["status"] if v1 else None,
            "stage1_p": v1["p_spectrum"] if v1 else None,
            "stage1_p_c4": v1["probabilities"]["c4"] if v1 else None,
            "stage1_p_local": v1["probabilities"]["local"] if v1 else None,
            "final_status": vf["status"] if vf else None,
            "final_p": vf["p_spectrum"] if vf else None,
            "final_p_c4": vf["probabilities"]["c4"] if vf else None,
            "final_labels": list(vf["labels"]) if vf else [],
            "ladder_class": (vf or {}).get("ladder", {}).get("ladder_class"),
            "batches": (rescreen or {}).get("batches_used", {}).get(fam, 0),
            "forwarded_new": sorted(c for c in forwarded
                                    if c.split(":")[0] == fam),
            "forwarded_roles": {e["candidate"]: list(e["roles"])
                                for e in retention["forwarded"]
                                if e["family"] == fam},
            "forwarded_legacy": sorted(c for c in legacy_forwarded
                                       if c.split(":")[0] == fam),
            "calibration_local_rungs": list(cal.get("local_rungs", [])),
            "calibration_admissible_below_d": list(cal.get("admissible_below_d", [])),
            "calibration_admissible_above_d": list(cal.get("admissible_above_d", [])),
            "stage1_probabilities": dict(v1["probabilities"]) if v1 else None,
            "final_probabilities": dict(vf["probabilities"]) if vf else None,
            "stage1_rungs": [{k: r[k] for k in ("candidate", "iota_mean",
                                                 "p_admissible", "p_local",
                                                 "p_below_d", "p_above_d",
                                                 "p_chance_over_ceiling")}
                             for r in v1["rungs"]] if v1 else [],
            "final_rungs": [{k: r[k] for k in ("candidate", "iota_mean",
                                                "p_admissible", "p_local",
                                                "p_below_d", "p_above_d",
                                                "p_chance_over_ceiling")}
                            for r in vf["rungs"]] if vf else [],
            "unavailable_in_emulation": sorted(
                c for c in set(getattr(measure, "unavailable", []))
                if c.split(":")[0] == fam) if emulate_rescreen else [],
            "comparators": (v1 or {}).get("comparators"),
        })
    return {
        "tree": label, "model": model, "model_dir": rep["model_dir"],
        "chance_basis": rep.get("chance_basis"),
        "iota_a_recorded": gate2.get("iota_a_recorded"),
        "iota_a_prescreen": iota_a_pre, "iota_a_calibrated": iota_a_cal,
        "iota_a_calibration_b": truth_b["iota_a"],
        "iota_a_screen_posterior": {k: v for k, v in stage1["iota_a"].items()
                                    if k != "severities"},
        "legacy_c4_groups_prescreen": sorted(
            cert["coverage"]["realised"]["straddling_groups"]),
        "legacy_c4_prescreen": bool(cert["coverage"]["conditions"]["C4"]),
        "c4_groups_calibrated": sorted(
            truth["coverage"]["realised"]["straddling_groups"]),
        "c4_calibrated": bool(truth["coverage"]["conditions"]["C4"]),
        "n_families_prescreen_pass": sum(1 for r in rows if r["prescreen_c4"]),
        "n_families_calibrated_pass": sum(1 for r in rows
                                          if r["calibration_c4"]),
        "n_pass_to_fail": sum(1 for r in rows
                              if r["prescreen_c4"] and not r["calibration_c4"]),
        "failure_causes": {c: sorted(r["family"] for r in rows
                                     if r["failure_cause"] == c)
                           for c in FAILURE_CAUSES},
        "stage1_statuses": dict(stage1["statuses"]),
        "final_statuses": dict(final["statuses"]),
        "rescreen": None if rescreen is None else {
            "batches_used": rescreen["batches_used"],
            "cost_generations": rescreen["cost_generations"],
            "resolved_at_max": rescreen["resolved_at_max"],
            "unavailable_in_emulation": sorted(set(
                getattr(measure, "unavailable", [])))},
        "retention": {"n_forwarded": retention["n_forwarded"],
                      "spectrum_families": retention["spectrum_families"],
                      "local_families": retention["local_families"],
                      "forwarded": [e["candidate"]
                                    for e in retention["forwarded"]],
                      "calibration_cost_generations":
                          retention["calibration_cost_generations"]},
        "legacy_retention": {"n_measured": legacy_kept["n_measured"],
                             "tier3_dropped": len(
                                 legacy_kept["tier3_dropped_for_budget"])},
        "families": rows,
    }


def metrics(rows: Sequence[Mapping[str, Any]], *, pred: Callable[[Mapping[str, Any]], bool],
            truth: Callable[[Mapping[str, Any]], bool]) -> dict[str, Any]:
    tp = sum(1 for r in rows if pred(r) and truth(r))
    fp = sum(1 for r in rows if pred(r) and not truth(r))
    fn = sum(1 for r in rows if not pred(r) and truth(r))
    tn = sum(1 for r in rows if not pred(r) and not truth(r))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "n_predicted_positive": tp + fp, "n_true_positive": tp + fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "false_positive_rate": fp / (fp + tn) if fp + tn else None}


def leave_one_model_out(rows: Sequence[Mapping[str, Any]], *,
                        p_key: str = "stage1_p",
                        truth_key: str = "calibration_support_both",
                        grid: Sequence[float] = tuple(round(0.05 * i, 2)
                                                      for i in range(1, 20)),
                        min_recall: float = 0.75) -> dict[str, Any]:
    """RETROSPECTIVE DEVELOPMENT: choose the accept threshold on the other
    models (highest precision subject to recall >= min_recall, then
    smallest threshold), report it on the held-out model."""
    models = sorted({r["model"] for r in rows})
    out = {}
    for held in models:
        train = [r for r in rows if r["model"] != held and r[p_key] is not None]
        test = [r for r in rows if r["model"] == held and r[p_key] is not None]
        best = None
        for t in grid:
            m = metrics(train, pred=lambda r, t=t: r[p_key] >= t,
                        truth=lambda r: bool(r[truth_key]))
            if m["recall"] is None or m["recall"] < min_recall:
                continue
            key = (m["precision"] or 0.0, -t)
            if best is None or key > best[0]:
                best = (key, t, m)
        if best is None:
            best = ((0.0, 0.0), 0.5, None)
        t = best[1]
        out[held] = {"chosen_accept": t, "train": best[2],
                     "test": metrics(test, pred=lambda r, t=t: r[p_key] >= t,
                                     truth=lambda r: bool(r[truth_key]))}
    return {"label": "retrospective development (LOMO)", "p_key": p_key,
            "truth_key": truth_key, "min_recall": min_recall,
            "per_held_out_model": out}


# ------------------------------------------------------------- spectrum replay

def spectrum_backtest(rep: Mapping[str, Any], *, label: str, model: str,
                      rule: SelectionRule = DEFAULT_SELECTION_RULE, seed: int = 0,
                      resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES,
                      d_min: float = 0.05) -> dict[str, Any] | None:
    gate2, gate3a, gate3b, gate3c = (rep["gate2"], rep["gate3a"],
                                     rep["gate3b"], rep["gate3c"])
    gate2_5 = rep["gate2_5"]
    if gate2 is None:
        return None
    m_star = int(gate2["m_star"])
    model_key = gate2["model_key"]
    tables = {s: load_calibration_table(gate2["calibration_rows"][s],
                                        model_key=model_key, m_star=m_star,
                                        split=s)
              for s in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")}
    iota_a = float(gate2["iota_a"])
    solo_a = float(gate2["solo_compliance_a"])
    folded = None
    corrected = bool(rep.get("chance_basis")) and "corrected" in str(rep.get("chance_basis"))
    if gate3a is not None and gate3a.get("stability") and not corrected:
        folded = dict(gate3a["stability"])
        folded_source = "gate3a record (recorded chance basis)"
    else:
        pairs = stability_stage.split_pair(tables[C.CALIBRATION_A],
                                           tables[C.CALIBRATION_B])
        folded = {lab: stability_stage.stability_verdict(
            pair, iota_a_by_split=gate2["iota_a_by_split"],
            solo_a_by_split=gate2["solo_a_by_split"], seed=seed,
            resamples=resamples) for lab, pair in pairs.items()}
        folded_source = (f"recomputed on the corrected chance basis "
                         f"({resamples} resamples)" if corrected
                         else f"recomputed ({resamples} resamples)")
    pool = classify_pool(tables["pooled"], tables[C.CALIBRATION_A],
                         tables[C.CALIBRATION_B], iota_a=iota_a,
                         solo_compliance_a=solo_a, n_topics_a=C.N_CALIBRATION,
                         folded_stability=folded, seed=seed,
                         resamples=resamples, rule=SpectrumRule(d_min=d_min))
    core: dict[str, int] = {}
    recorded_backups: list[str] = []
    v7_spectrum_identified = None
    if gate3b is not None:
        for e in (gate3b.get("selection", {}).get("core", {})
                  .get("core_references", []) or []):
            core[e["family"]] = int(e["severity"])
        v7_spectrum_identified = bool(gate3b.get("selection", {}).get("core", {})
                                      .get("spectrum_identified", False))
    if gate3c is not None:
        recorded_backups = list((gate3c.get("support", {}).get("realised", {})
                                 or {}).get("frozen_backups", []))
    valid_rows = [r for r in tables["pooled"]
                  if pool["spectrum"][r.label]["passed"]]
    # core rungs may sit inside d_min: hand the selection the pooled rows of
    # selected families for the centre point
    by_label = {r.label: r for r in tables["pooled"]}
    core_rows = [by_label[f"{f}:{q}"] for f, q in core.items()
                 if f"{f}:{q}" in by_label]
    selection = select_spectrum(valid_rows + [r for r in core_rows
                                              if r not in valid_rows],
                                iota_a=iota_a, core_references=core, rule=rule)
    backups = admissible_backups(
        pool["local"], tables["pooled"], iota_a=iota_a,
        used_families=list(core),
        gate2_5_qualified=(gate2_5 or {}).get("qualified_families", []),
        recorded_backups=recorded_backups)
    spectrum_valid = sorted(valid_rows, key=lambda r: r.iota)
    return {
        "tree": label, "model": model, "iota_a": iota_a, "m_star": m_star,
        "iota_a_recorded": gate2.get("iota_a_recorded"),
        "chance_basis": rep.get("chance_basis"),
        "folded_stability_source": folded_source,
        "n_rows": len(tables["pooled"]),
        "n_folded_stable": pool["n_folded_stable"],
        "n_unfolded_stable": pool["n_unfolded_stable"],
        "n_local_valid": pool["n_local_valid"],
        "n_spectrum_valid": pool["n_spectrum_valid"],
        "n_spectrum_valid_inside_v_head": pool["n_spectrum_valid_inside_v_head"],
        "n_spectrum_valid_beyond_v_head": pool["n_spectrum_valid_beyond_v_head"],
        "spectrum_valid_range": ([spectrum_valid[0].iota, spectrum_valid[-1].iota]
                                 if spectrum_valid else None),
        "spectrum_valid_below": sum(1 for r in spectrum_valid if r.iota < iota_a),
        "spectrum_valid_above": sum(1 for r in spectrum_valid if r.iota > iota_a),
        "spectrum_valid_families": sorted({r.kind for r in spectrum_valid}),
        "folded_pool_range": _folded_pool_range(tables["pooled"], folded, pool),
        "core_references": core,
        "v7_spectrum_identified": v7_spectrum_identified,
        "v7_gate3c_spectrum_met": (None if gate3c is None
                                   else gate3c.get("spectrum_met")),
        "selection": {k: v for k, v in selection.items() if k != "trace"},
        "selection_trace": selection["trace"],
        "backups": backups,
    }


def _folded_pool_range(pooled, folded, pool) -> dict[str, Any]:
    """The v7 spectrum pool: rungs stable under the FOLDED verdict and
    passing the other spectrum components --- what §13.12 could draw from."""
    labels = [r.label for r in pooled
              if (folded.get(r.label) or {}).get("passed")
              and all(c["passed"] for c in pool["spectrum"][r.label]["components"]
                      if c["component"] not in ("V_stab", "V_pos"))]
    iotas = sorted(r.iota for r in pooled if r.label in set(labels))
    return {"n": len(labels), "range": [iotas[0], iotas[-1]] if iotas else None,
            "span": (iotas[-1] - iotas[0]) if iotas else 0.0}


# ------------------------------------------------------ retention recovery

RETENTION_RECOVERY_CLASSES = (
    "REFUTED_AT_SCREEN",              # stage-1 REJECT: the posterior (chance, lift, band) says no support
    "SECOND_PASS_ACCEPTED",           # final ACCEPT: forwarded as a spectrum family with its spaced set
    "SECOND_PASS_UNDECIDABLE",        # final REJECT, but its extreme rungs were never calibrated, so the
                                      #   emulated pass could not measure them (production would)
    "SECOND_PASS_REJECTED",           # final REJECT with every measured rung available to the pass
)


def retention_recovery(rows: Sequence[Mapping[str, Any]], *,
                       d_below: float, d_above: float) -> dict[str, Any]:
    """What the new pipeline does with every historical RETENTION_ARTIFACT.

    A family is a retention artefact when its pre-screen C4 rested on rungs
    §12.7 then dropped (Tier-3 rungs not among the 24 nearest ι_A). The
    calibrated truth for those rungs does not exist --- they were never
    calibrated --- so recovery is stated in three parts: (1) whether the
    screen's posterior already refutes the family (its spread rests on
    chance-inflated or lift-less rungs: a mirage, not a loss); (2) whether
    the family, if accepted, has admissible rungs on both offsets whose
    retention the spaced rule guarantees (``geometry_retainable``); (3) what
    the emulated second pass decided, and whether that decision could have
    been informed at all (the extremes are unavailable to the emulation
    exactly when they were dropped historically).
    """
    out = []
    for r in rows:
        if r.get("failure_cause") != "RETENTION_ARTIFACT":
            continue
        rungs = r.get("stage1_rungs") or []
        below = [x["candidate"] for x in rungs
                 if x["p_admissible"] >= 0.5 and x["p_below_d"] >= 0.5]
        above = [x["candidate"] for x in rungs
                 if x["p_admissible"] >= 0.5 and x["p_above_d"] >= 0.5]
        mirage = [x["candidate"] for x in rungs if x["p_chance_over_ceiling"] >= 0.5]
        roles = r.get("forwarded_roles") or {}
        extremes = {c for c, rl in roles.items()
                    if "HARD_EXTREME" in rl or "EASY_EXTREME" in rl}
        s1, fin = r.get("stage1_status"), r.get("final_status")
        if s1 == "SCREEN_REJECT":
            klass = "REFUTED_AT_SCREEN"
        elif fin == "SCREEN_ACCEPT":
            klass = "SECOND_PASS_ACCEPTED"
        elif r.get("unavailable_in_emulation"):
            klass = "SECOND_PASS_UNDECIDABLE"
        else:
            klass = "SECOND_PASS_REJECTED"
        out.append({
            "tree": r["tree"], "model": r["model"], "family": r["family"],
            "structural_tier": r["structural_tier"],
            "class": klass,
            "stage1_status": s1, "stage1_p": r.get("stage1_p"),
            "stage1_p_below": (r.get("stage1_probabilities") or {}).get("support_below"),
            "stage1_p_above": (r.get("stage1_probabilities") or {}).get("support_above"),
            "final_status": fin, "final_p": r.get("final_p"),
            "rungs_dropped_by_12_7": list(r.get("rungs_not_calibrated", [])),
            "unavailable_in_emulation": list(r.get("unavailable_in_emulation", [])),
            "admissible_below_offset_at_screen": below,
            "admissible_above_offset_at_screen": above,
            "geometry_retainable": bool(below and above),
            "chance_mirage_rungs": mirage,
            "forwarded_new": list(r.get("forwarded_new", [])),
            "extremes_forwarded": sorted(extremes),
            "spectrum_geometry_forwarded": bool(
                extremes and any(c in extremes for c in below)
                and any(c in extremes for c in above)),
        })
    by_class = {k: sum(1 for x in out if x["class"] == k)
                for k in RETENTION_RECOVERY_CLASSES}
    return {
        "n": len(out),
        "by_class": by_class,
        "n_geometry_retainable": sum(1 for x in out if x["geometry_retainable"]),
        "n_geometry_forwarded": sum(1 for x in out if x["spectrum_geometry_forwarded"]),
        "n_mirage_only": sum(1 for x in out if x["chance_mirage_rungs"]
                             and not x["geometry_retainable"]),
        "n_recovered": sum(1 for x in out if x["class"] == "SECOND_PASS_ACCEPTED"
                           and x["spectrum_geometry_forwarded"]),
        "n_undecidable_but_retainable": sum(
            1 for x in out if x["class"] == "SECOND_PASS_UNDECIDABLE"
            and x["geometry_retainable"]),
        "d_below": d_below, "d_above": d_above,
        "families": out,
    }


def local_recovery_detail(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every family that calibrated a rung inside the caliper (chance and
    lift admissible): was that rung forwarded, and if not, why."""
    out = []
    for r in rows:
        cal_local = list(r.get("calibration_local_rungs", []))
        if not cal_local:
            continue
        fwd = set(r.get("forwarded_new", []))
        s1_rungs = {x["candidate"]: x for x in (r.get("stage1_rungs") or [])}
        best = max((x["p_local"] for x in s1_rungs.values()), default=0.0)
        kept = sorted(c for c in cal_local if c in fwd)
        if kept:
            why = "KEPT"
        elif not r.get("forwarded_new"):
            why = ("NOT_LABELLED_LOCAL" if "LOCAL_REFERENCE_CANDIDATE"
                   not in (r.get("final_labels") or []) else "FAMILY_NOT_FORWARDED")
        else:
            why = "OTHER_RUNGS_FORWARDED"
        out.append({"tree": r["tree"], "model": r["model"], "family": r["family"],
                    "structural_tier": r["structural_tier"],
                    "calibrated_local_rungs": cal_local,
                    "kept": kept, "why": why,
                    "best_p_local_at_screen": best,
                    "p_local_of_calibrated": {c: s1_rungs[c]["p_local"]
                                              for c in cal_local if c in s1_rungs},
                    "forwarded_new": sorted(fwd),
                    "forwarded_legacy": list(r.get("forwarded_legacy", []))})
    return {"n_families": len(out),
            "n_kept": sum(1 for x in out if x["kept"]),
            "n_family_forwarded": sum(1 for x in out if x["forwarded_new"]),
            "n_kept_legacy": sum(1 for x in out
                                 if set(x["calibrated_local_rungs"]) & set(x["forwarded_legacy"])),
            "why": {w: sum(1 for x in out if x["why"] == w)
                    for w in ("KEPT", "NOT_LABELLED_LOCAL", "FAMILY_NOT_FORWARDED",
                              "OTHER_RUNGS_FORWARDED")},
            "families": out}
