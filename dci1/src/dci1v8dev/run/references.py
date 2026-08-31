"""Stage 8, ``GATE_3_REFERENCES``: per frame --- LOCAL and SPECTRUM validity,
the core references by the registered kernel, the deterministic spectrum
selection, the coverage gate and the admissible backups; then the frame's
explicit state. Approach A (``dci1/docs/V8_FRAME_CONDITIONING.md``).

No generation. For every frame Gate 2 supported it reads that frame's
§13.11 tables (three splits) and evaluates, against **that frame's**
ι_A(f), solo_A(f) and A's frame topic count:

* §13.7's folded stability per candidate (``dci1v7.stages.stability``,
  imported), with ι_A(f) and solo_A(f) on each split --- the LOCAL rule's
  V_stab; and ι_A(f)'s own equivalence across the splits;
* ``dci1v8dev.spectrum.validity.classify_pool`` --- every rung of the
  frame's pooled table under the LOCAL rule (v7's full V(R), unchanged) and
  under the SPECTRUM rule (V_coord, unfolded V_stab, V_pos);
* §13.8's core selection by v7's kernel ``admit_core_references`` with
  ``require_spectrum=False``;
* ``select_spectrum`` + ``selected_coverage`` at the frame's share of the
  registered confirmatory blocks (``rules.CONFIRMATORY_BLOCKS_PER_FRAME``),
  and ``admissible_backups`` (§13.15 on the admissible basis).

A reference is therefore LOCAL-valid *under a frame*; it may be valid under
one frame and not another, and nothing asks it to qualify under every
frame. Each frame ends in one of ``stages.FRAME_STATES``: ``UNSUPPORTED``
(no operating point at Gate 2), ``NEITHER``, ``LOCAL_ONLY``,
``SPECTRUM_ONLY``, ``LOCAL_AND_SPECTRUM``. The cross-frame block is
descriptive: which rung each frame chose, and where they agree.

Nothing here reads a composed outcome: the closed §13.11 schema refuses one
before any rule runs, and the pilot has none to offer. The eventual
estimands --- Δ_R(f) per frame, the difficulty-response slope per frame ---
are *stated* on the record and not computed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.stages import selection as v7_selection
from dci1v7.stages import stability as stability_stage
from dci1v7.stages.calibration_table import load_calibration_table

from dci1v8dev import rules as R
from dci1v8dev.run import FRAME_DOCUMENT
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.lifecycle import StageOutcome, run_stage
from dci1v8dev.run.regime import jsonable
from dci1v8dev.spectrum.backups import admissible_backups
from dci1v8dev.spectrum.coverage import FRAME_COVERAGE_RULE
from dci1v8dev.spectrum.selection import SelectionRule, select_spectrum
from dci1v8dev.spectrum.validity import DEFAULT_SPECTRUM_RULE, classify_pool

__all__ = ["gate3_payload", "run_gate3", "survival_summary",
           "frame_references", "frame_state", "cross_frame_summary",
           "ESTIMANDS", "FRAME_SELECTION_RULE"]

#: The v8 selection rule with the coverage projection at the frame's share
#: of the registered confirmatory blocks; every threshold unchanged.
FRAME_SELECTION_RULE = SelectionRule(coverage=FRAME_COVERAGE_RULE)

#: What the post-freeze experiment would estimate, stated here so the
#: pre-freeze record names the frame-specific quantities and no pooled one.
ESTIMANDS = {
    "primary": {
        "matched_reference_contrast": "Delta_R(f): per frame f and per core "
                                      "reference R of that frame, at n*(f) "
                                      "and m*(f), from the frame's own "
                                      "blocks of the confirmatory design",
        "difficulty_response": "the §11.8 slope per frame f, fitted on frame "
                               "f's selected spectrum points at frame f's "
                               "difficulty coordinates",
        "workflow": "frame-specific calibration -> frame-specific matching "
                    "-> frame-specific outcome estimate",
    },
    "secondary": {
        "cross_frame": "the four Delta_R(f) reported side by side; whether "
                       "their signs and magnitudes agree; an explicitly "
                       "registered average or a modelled frame term only "
                       "if a later registration defines one",
        "never": "a silent average of frame-specific estimates into one "
                 "number",
    },
    "pooled_over_frames": "descriptive only",
    "generated_here": False,
    "requires": "a freeze of the v8 design; this layer cannot produce a "
                "composed cell",
    "document": FRAME_DOCUMENT,
}


def survival_summary(pool: Mapping[str, Any], core: Mapping[str, Any],
                     selection: Mapping[str, Any], backups: Mapping[str, Any],
                     *, iota_a: float, frame: int) -> dict[str, Any]:
    """What the report reads: the four survival facts of one frame."""
    local_families = sorted({label.split(":")[0]
                             for label, v in pool["local"].items()
                             if v["passed"]})
    valid = {label: v for label, v in pool["spectrum"].items() if v["passed"]}
    below = sorted(label for label, v in valid.items() if v["side"] == "below")
    above = sorted(label for label, v in valid.items() if v["side"] == "above")
    fam_below = sorted({label.split(":")[0] for label in below})
    fam_above = sorted({label.split(":")[0] for label in above})
    coverage = selection["coverage"]
    return {
        "frame": frame,
        "local_valid_families": local_families,
        "n_local_valid_families": len(local_families),
        "meets_min_local_families": len(local_families) >= S.MIN_LOCAL_FAMILIES,
        "min_local_families": S.MIN_LOCAL_FAMILIES,
        "core_identified": bool(core["references_identified"]),
        "core_references": [{"family": e["family"], "severity": e["severity"],
                             "iota": e["iota"]}
                            for e in core["core_references"]],
        "spectrum_valid_below": below, "spectrum_valid_above": above,
        "spectrum_valid_families_below": fam_below,
        "spectrum_valid_families_above": fam_above,
        "spectrum_pool_ok": (len(below) >= C.SUPPORT_MIN_BELOW
                             and len(above) >= C.SUPPORT_MIN_ABOVE
                             and len(fam_below) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE
                             and len(fam_above) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE),
        "coverage_identified": bool(coverage["identified"]),
        "coverage_status": coverage["status"],
        "coverage_reasons": list(coverage["reasons"]),
        "projected_se_beta": coverage["projection"].get("se_beta"),
        "projected_se_beta_at_full_allocation":
            coverage.get("projection_at_full_allocation", {}).get("se_beta"),
        "n_blocks_projected": coverage["projection"].get("n_blocks"),
        "selected_families": list(selection["families"]),
        "n_spectrum_references": selection["n_spectrum_references"],
        "backups": list(backups["backups"]),
        "n_backups": len(backups["backups"]),
        "meets_min_backups": len(backups["backups"]) >= S.MIN_BACKUPS,
        "iota_a": iota_a,
    }


def wording_sensitive_rungs(gate2_record: Mapping[str, Any], *,
                            pool: Mapping[str, Any], core: Mapping[str, int],
                            selection: Mapping[str, Any],
                            backups: Mapping[str, Any], frame: int
                            ) -> dict[str, Any]:
    """Which rungs the frames disagree on (Gate 2's cross-frame comparison),
    and whether each is LOCAL-valid, spectrum-valid, a core reference, a
    selected spectrum point or a backup family's rung **under this frame**
    --- so a reader sees where wording sensitivity touches this frame's
    reference set. Descriptive: no rung is dropped here."""
    comparison = gate2_record.get("frame_comparison_pooled") or {}
    selected = {p["candidate"] for p in selection.get("points", ())}
    core_labels = {f"{f}:{q}" for f, q in core.items()}
    backup_families = set(backups.get("backups") or ())
    out: dict[str, list[dict[str, Any]]] = {"WORDING_SENSITIVE": [],
                                            "UNRESOLVED": []}
    for label, c in sorted(comparison.items()):
        klass = c.get("class")
        if klass not in out:
            continue
        kind = label.rpartition(":")[0]
        out[klass].append({
            "candidate": label, "spread": c.get("spread"),
            "max_abs_difference": c.get("max_abs_difference"),
            "max_abs_z": c.get("max_abs_z"),
            "iota_under_this_frame": (c.get("frames") or {}).get(str(frame), {}).get("iota"),
            "local_valid": bool((pool["local"].get(label) or {}).get("passed")),
            "spectrum_valid": bool((pool["spectrum"].get(label) or {}).get("passed")),
            "core_reference": label in core_labels,
            "selected_spectrum_point": label in selected,
            "backup_family": kind in backup_families})
    touching = {k: [e["candidate"] for e in v
                    if e["local_valid"] or e["spectrum_valid"]
                    or e["core_reference"] or e["selected_spectrum_point"]]
                for k, v in out.items()}
    return {"frame": frame, "by_class": out,
            "n_wording_sensitive": len(out["WORDING_SENSITIVE"]),
            "n_unresolved": len(out["UNRESOLVED"]),
            "touching_reference_set": touching,
            "reference_bound": S.WORDING_REFERENCE_BOUND,
            "selection_rule": None,
            "note": "descriptive; under Approach A the frame is the "
                    "condition and no rung is dropped for wording sensitivity"}


def frame_state(*, supported: bool, core_identified: bool | None,
                coverage_identified: bool | None) -> str:
    if not supported:
        return "UNSUPPORTED"
    if core_identified and coverage_identified:
        return "LOCAL_AND_SPECTRUM"
    if core_identified:
        return "LOCAL_ONLY"
    if coverage_identified:
        return "SPECTRUM_ONLY"
    return "NEITHER"


assert all(frame_state(supported=s, core_identified=c, coverage_identified=v)
           in S.FRAME_STATES
           for s in (True, False) for c in (True, False) for v in (True, False))


def frame_references(gate2_record: Mapping[str, Any], frame: int, *,
                     model_key: str, seed: int, resamples: int
                     ) -> dict[str, Any]:
    """Gate 3 for one supported frame, on that frame's Gate-2 block alone."""
    g2 = gate2_record["by_frame"][str(frame)]
    if g2.get("status") != S.FRAME_SUPPORTED:
        raise ProtocolError(f"frame {frame} is {g2.get('status')!r} at Gate 2; "
                            "Gate 3 evaluates supported frames only")
    m_star = int(g2["m_star"])
    iota_a = float(g2["iota_a"])
    solo_a = float(g2["solo_compliance_a"])
    n_topics_a = int(g2["n_topics_a"])
    tables = {split: load_calibration_table(
        g2["calibration_rows"][split], model_key=model_key,
        m_star=m_star, split=split)
        for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")}
    stability_stage.assert_not_pooled(tables[C.CALIBRATION_A],
                                      split=C.CALIBRATION_A)
    stability_stage.assert_not_pooled(tables[C.CALIBRATION_B],
                                      split=C.CALIBRATION_B)
    pairs = stability_stage.split_pair(tables[C.CALIBRATION_A],
                                       tables[C.CALIBRATION_B])
    folded = {label: stability_stage.stability_verdict(
        pair, iota_a_by_split=g2["iota_a_by_split"],
        solo_a_by_split=g2["solo_a_by_split"], seed=seed,
        resamples=resamples) for label, pair in sorted(pairs.items())}
    a_splits = g2.get("a_per_topic_by_split") or {}
    per_topic = a_splits.get("per_topic") or {}
    chance = a_splits.get("chance") or {}
    if (per_topic.get(C.CALIBRATION_A) and per_topic.get(C.CALIBRATION_B)
            and chance.get(C.CALIBRATION_A) is not None
            and chance.get(C.CALIBRATION_B) is not None):
        iota_a_stability = stability_stage.assert_iota_a_stable(
            per_topic_a=per_topic[C.CALIBRATION_A],
            per_topic_b=per_topic[C.CALIBRATION_B],
            chance_a=chance[C.CALIBRATION_A],
            chance_b=chance[C.CALIBRATION_B], seed=seed + 2,
            resamples=resamples)
    else:
        iota_a_stability = {"quantity": "iota_A", "passed": None,
                            "reason": "no per-topic vector for A on both splits"}
    pool = classify_pool(
        tables["pooled"], tables[C.CALIBRATION_A], tables[C.CALIBRATION_B],
        iota_a=iota_a, solo_compliance_a=solo_a, n_topics_a=n_topics_a,
        folded_stability=folded, seed=seed, resamples=resamples,
        rule=DEFAULT_SPECTRUM_RULE)
    core = v7_selection.admit_core_references(
        tables["pooled"], iota_a=iota_a, solo_compliance_a=solo_a,
        n_topics_a=n_topics_a, stability_by_candidate=folded,
        require_spectrum=False)
    core_refs = {e["family"]: int(e["severity"]) for e in core["core_references"]}
    by_label = {r.label: r for r in tables["pooled"]}
    valid_rows = [r for r in tables["pooled"] if pool["spectrum"][r.label]["passed"]]
    core_rows = [by_label[f"{f}:{q}"] for f, q in core_refs.items()
                 if f"{f}:{q}" in by_label]
    selection = select_spectrum(
        valid_rows + [r for r in core_rows if r not in valid_rows],
        iota_a=iota_a, core_references=core_refs, rule=FRAME_SELECTION_RULE)
    backups = admissible_backups(pool["local"], tables["pooled"], iota_a=iota_a,
                                 used_families=list(core_refs))
    summary = survival_summary(pool, core, selection, backups, iota_a=iota_a,
                               frame=frame)
    sensitive = wording_sensitive_rungs(gate2_record, pool=pool, core=core_refs,
                                        selection=selection, backups=backups,
                                        frame=frame)
    state = frame_state(supported=True,
                        core_identified=bool(core["references_identified"]),
                        coverage_identified=bool(selection["identified"]))
    return {
        "frame": frame, "status": S.FRAME_SUPPORTED, "state": state,
        "n_star": int(g2["n_star"]), "m_star": m_star,
        "iota_a": iota_a, "solo_compliance_a": solo_a, "n_topics_a": n_topics_a,
        "n_rows": {split: len(rows) for split, rows in tables.items()},
        "stability": folded,
        "n_folded_stable": pool["n_folded_stable"],
        "n_unfolded_stable": pool["n_unfolded_stable"],
        "iota_a_stability": iota_a_stability,
        "unfolded_stability": pool["unfolded_stability"],
        "local": pool["local"], "spectrum": pool["spectrum"],
        "n_local_valid": pool["n_local_valid"],
        "n_spectrum_valid": pool["n_spectrum_valid"],
        "n_spectrum_valid_beyond_v7_v_head":
            pool["n_spectrum_valid_beyond_v_head"],
        "core": {k: v for k, v in core.items() if k != "family_verdicts"},
        "core_family_verdicts": core["family_verdicts"],
        "core_references": core_refs,
        "spectrum_selection": {k: v for k, v in selection.items()
                               if k != "trace"},
        "selection_trace": selection["trace"],
        "coverage": selection["coverage"],
        "backups": backups,
        "survival": summary,
        "wording_sensitive_rungs": sensitive,
        "identification_statuses": sorted(
            set(core["identification_statuses"]) | {selection["status"]}),
    }


def cross_frame_summary(by_frame: Mapping[str, Mapping[str, Any]],
                        supported: list[int]) -> dict[str, Any]:
    """Descriptive: what each frame chose, side by side, and where the
    frames agree. Selects nothing; every selection above is per frame."""
    core_by_family: dict[str, dict[str, int | None]] = {}
    spectrum_by_family: dict[str, dict[str, list[str]]] = {}
    local_families: dict[str, list[str]] = {}
    for w in supported:
        block = by_frame[str(w)]
        for fam, q in block["core_references"].items():
            core_by_family.setdefault(fam, {})[str(w)] = int(q)
        for p in block["spectrum_selection"]["points"]:
            spectrum_by_family.setdefault(p["family"], {}).setdefault(
                str(w), []).append(p["candidate"])
        local_families[str(w)] = block["survival"]["local_valid_families"]
    n = len(supported)
    core_in_every_frame = sorted(f for f, m in core_by_family.items()
                                 if len(m) == n) if n else []
    same_rung_in_every_frame = sorted(
        f for f in core_in_every_frame
        if len({q for q in core_by_family[f].values()}) == 1)
    local_in_every_frame = (sorted(set.intersection(
        *[set(v) for v in local_families.values()])) if local_families else [])
    return {
        "supported_frames": supported,
        "states": {str(w): by_frame[str(w)]["state"] for w in supported},
        "core_reference_by_family": core_by_family,
        "core_family_in_every_supported_frame": core_in_every_frame,
        "core_same_rung_in_every_supported_frame": same_rung_in_every_frame,
        "local_valid_families_by_frame": local_families,
        "local_valid_family_in_every_supported_frame": local_in_every_frame,
        "spectrum_points_by_family": spectrum_by_family,
        "iota_a_by_frame": {str(w): by_frame[str(w)]["iota_a"] for w in supported},
        "n_star_by_frame": {str(w): by_frame[str(w)]["n_star"] for w in supported},
        "m_star_by_frame": {str(w): by_frame[str(w)]["m_star"] for w in supported},
        "standing": "descriptive; the frames are compared after each has its "
                    "own selection and nothing here selects",
    }


def gate3_payload(tree: ModelTree, *, producing_commit: str,
                  gate2_record: Mapping[str, Any], seed: int = 0,
                  resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
                  ) -> dict[str, Any]:
    supported = [int(w) for w in gate2_record["supported_frames"]]
    if not supported:
        raise ProtocolError("Gate 2 recorded no supported frame; Gate 3 has "
                            "nothing to evaluate (Gate 2 should have been "
                            "terminal)")
    by_frame: dict[str, Any] = {}
    for w in S.FRAMES:
        g2 = gate2_record["by_frame"][str(w)]
        if w in supported:
            by_frame[str(w)] = frame_references(
                gate2_record, w, model_key=tree.model_key, seed=seed,
                resamples=resamples)
        else:
            by_frame[str(w)] = {
                "frame": w, "status": S.FRAME_UNSUPPORTED,
                "state": frame_state(supported=False, core_identified=None,
                                     coverage_identified=None),
                "unsupported_reason": g2.get("unsupported_reason"),
                "survival": None, "local": {}, "spectrum": {},
                "core_references": {}, "backups": None,
                "wording_sensitive_rungs": None}
    states = {
        str(w): {
            "state": by_frame[str(w)]["state"],
            "operating_point": by_frame[str(w)]["status"],
            "local_identified": (bool(by_frame[str(w)]["survival"]["core_identified"])
                                 if w in supported else None),
            "spectrum_identified": (
                bool(by_frame[str(w)]["survival"]["coverage_identified"])
                if w in supported else None),
            "n_local_valid_families": (
                by_frame[str(w)]["survival"]["n_local_valid_families"]
                if w in supported else None),
            "meets_min_local_families": (
                by_frame[str(w)]["survival"]["meets_min_local_families"]
                if w in supported else None),
            "n_backups": (by_frame[str(w)]["survival"]["n_backups"]
                          if w in supported else None),
            "meets_min_backups": (by_frame[str(w)]["survival"]["meets_min_backups"]
                                  if w in supported else None),
        } for w in S.FRAMES}
    return jsonable({
        "stage": S.STAGE_GATE3,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE3],
        "outcome": "PASS",
        "inputs": {"gate2": {"stage": S.STAGE_GATE2,
                             "supported_frames": supported}},
        "producing_commit": producing_commit,
        "frame_conditioning": {
            **gate2_record["frame_conditioning"],
            "gate3": "every validity, selection and backup is evaluated per "
                     "frame on that frame's table against that frame's "
                     "iota_A(f); a reference may be LOCAL-valid under one "
                     "frame and not another; the coverage projection is at "
                     f"{R.CONFIRMATORY_BLOCKS_PER_FRAME} blocks per frame; "
                     "the coordinates come from the calibration topics per "
                     "frame this run's calibration_allocation block records, "
                     "carried here from Gate 2"},
        "frames": list(S.FRAMES),
        "supported_frames": supported,
        "unsupported_frames": gate2_record.get("unsupported_frames") or {},
        # The allocation the coordinates this stage admits were measured at,
        # carried from Gate 2: a LOCAL or SPECTRUM verdict is a statement
        # about a precision, and the precision is this number.
        "calibration_allocation": gate2_record.get("calibration_allocation"),
        "by_frame": by_frame,
        "frame_states": states,
        "frame_state_vocabulary": list(S.FRAME_STATES),
        "cross_frame": cross_frame_summary(by_frame, supported),
        "estimands": ESTIMANDS,
        "coverage_rule": {"n_blocks": FRAME_COVERAGE_RULE.n_blocks,
                          "max_se_beta": FRAME_COVERAGE_RULE.max_se_beta,
                          "max_se_iota": FRAME_COVERAGE_RULE.max_se_iota,
                          "d_below": FRAME_COVERAGE_RULE.d_below,
                          "d_above": FRAME_COVERAGE_RULE.d_above},
        "core_kernel": "dci1v7.stages.selection.admit_core_references "
                       "(§13.8, registered), require_spectrum=False, per "
                       "frame: the spectrum is selected by the v8 rule",
        "identification_statuses": sorted({
            s for w in supported
            for s in by_frame[str(w)]["identification_statuses"]}),
        "written_at_design_time": True,
        "no_composed_cells": S.NO_COMPOSED_CELLS,
        "seed": seed, "resamples": resamples,
    })


def run_gate3(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", seed: int = 0,
              resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_GATE3,
        compute=lambda previous: gate3_payload(
            tree, producing_commit=commit, gate2_record=previous, seed=seed,
            resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)
