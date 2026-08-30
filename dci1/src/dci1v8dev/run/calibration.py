"""Stage 7, ``GATE_2_CALIBRATION``: per frame --- n*(f), m*(f), ι_A(f), the
forwarded set at calibration precision on §13.2's chance basis, and one
extension round. Approach A (``dci1/docs/V8_FRAME_CONDITIONING.md``).

Two passes on the 192 calibration topics at M_cal = 4, as v7's Gate 2:

1. A's grid, B's grid and the unconstrained cell (``grid-A``, ``grid-B``),
   on every block; every block is rendered under one frame
   (``block.index % N_WORDINGS``), so each frame holds a quarter of the
   blocks of every cell. **Per frame**, §12.3 fixes n*(f) and m*(f) on that
   frame's own raw solo curves, §12.4 checks adequacy on that frame's own
   rates, and the frame's candidates take their chance compliance from the
   unconstrained cells of *that frame's blocks* --- the §13.2 basis ("the
   same topic set"), which the producer ``_calibration_rows`` (7f89dae)
   enforces by refusing a chance measured on other topics;
2. one solo cell per forwarded candidate (``candidates``) on every block,
   with B at every supported frame's m*(f) present as an *absent* instance,
   which is where each frame's kappa(R|B) comes from.

Then **one bounded extension round** (``extension-1``): per supported
frame, a spectrum-candidate family whose admissible rungs do not reach an
offset on one side of ι_A(f), with unmeasured reserve in that direction,
gets at most two reserve rungs on that side; the round measures the union
of the frames' plans on every block, and a rung measured for one frame is
data for every frame.

A frame with no operating point (§12.3 on its own curves, or §12.4 on its
own rates) is recorded ``UNSUPPORTED`` with the status it hit and takes no
further part; the other frames continue. The replication is terminal only
when **no** frame is supported. The frame-pooled curves are recorded under
``descriptive_pooled`` and read by nothing: no pooled ι_A, no pooled §13.11
table exists on this record.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.run.gates_run import (_calibration_rows, _chance_basis,
                                  _kappa_b_under_candidate, _kappa_columns,
                                  _prescreen_to_calibration,
                                  _withhold_degenerate, focal_constraint)
from dci1v7.stages import regime as regime_stage
from dci1v7.stages.calibration_table import instructed_compliance
from dci1v7.topics.bank import TopicBank, calibration_binding, load_bank
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev import rules as R
from dci1v8dev.prescreen.extension import ExtensionRule, calibration_extension_plan
from dci1v8dev.run import FRAME_DOCUMENT
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run import wording as W
from dci1v8dev.run.execute import (UNCONSTRAINED_ARM, SoloCell, blocks,
                                   cell_rates, generate_and_score,
                                   instance_rates, per_topic_compliance,
                                   prompt_cell, resolve_generate,
                                   row_accounting, rows_of_frame)
from dci1v8dev.run.lifecycle import (StageOutcome, TerminalStatus,
                                     protocol_identity, run_stage)
from dci1v8dev.run.regime import screen_responder

__all__ = ["gate2_payload", "run_gate2", "constraints_from_labels",
           "assert_synthetic_only", "reach_input", "frame_curves",
           "frame_operating_points", "frame_tables", "frame_a_coordinate",
           "supported_frame_block", "unsupported_frame_block",
           "gate2_frames_from_rows", "terminal_status_over_frames",
           "FRAME_CONDITIONING_STATEMENT"]

FRAME_CONDITIONING_STATEMENT = {
    "policy": S.FRAME_CONDITIONING,
    "document": FRAME_DOCUMENT,
    "frames": list(S.FRAMES),
    "frame_of_block": "block_index % N_WORDINGS; every constraint a block "
                      "states is rendered under the block's frame",
    "primary": "per frame: n*(f), m*(f), iota_A(f) with kappa_A(f) on the "
               "frame's own unconstrained cells, §13.11's table on the "
               "frame's own rows, kappa(R|B) at m*(f) on the frame's own "
               "B-solo cell, the extension reach at iota_A(f)",
    "pooled": "descriptive_pooled only (the frame-pooled solo curves and "
              "§12.3's reading of them); read by no stage; no pooled iota_A "
              "and no pooled §13.11 table exist on this record",
    "terminal_rule": "the replication is terminal only when no frame has an "
                     "operating point; an unsupported frame records the "
                     "§12.3/§12.4 status it hit and the other frames continue",
}


def assert_synthetic_only(tree: ModelTree, name: str, value: Any) -> None:
    if tree.context.namespace != "synthetic":
        raise ProtocolError(
            f"{name}={value!r} was passed in the {tree.context.namespace!r} "
            "namespace; a scale knob is admissible only in the synthetic "
            "namespace")


def constraints_from_labels(labels: Sequence[str]) -> list[Constraint]:
    out: list[Constraint] = []
    for label in labels:
        kind, _, severity = label.rpartition(":")
        out.append(Constraint(kind, int(severity), reserve=True))
    return out


def _split_of(bank: TopicBank, topic_id: str) -> str:
    for name in C.TOPIC_SETS:
        if any(t["topic_id"] == topic_id for t in bank.sets[name]):
            return name
    raise ProtocolError(f"{topic_id!r} is in no registered set")


def _unconstrained_rate(rows: Sequence[Mapping[str, Any]], *, kind: str,
                        severity: int, split: str | None = None
                        ) -> dict[str, Any]:
    return cell_rates(rows, kind=kind, severity=severity, present=False,
                      split=split, arm=UNCONSTRAINED_ARM)


def reach_input(pooled_rows: Sequence[Mapping[str, Any]], *,
                spectrum_families: Sequence[str], iota_a: float,
                rule: ExtensionRule) -> dict[str, dict[str, Any]]:
    """Per spectrum-candidate family: the measured severities and whether an
    admissible rung (guard band, chance ceiling, lift floor, defined
    coordinate) reaches each offset from ``iota_a`` --- the extension plan's
    input, evaluated on one frame's table against that frame's iota_A."""
    out: dict[str, dict[str, Any]] = {}
    for kind in spectrum_families:
        rows = [r for r in pooled_rows if r["kind"] == kind]
        adm = []
        for r in rows:
            kappa, solo = float(r["chance_compliance"]), float(r["solo_compliance"])
            if kappa >= C.CHANCE_DEGENERACY_MAX:
                continue
            if not (R.SPECTRUM_GUARD_BAND[0] <= solo <= R.SPECTRUM_GUARD_BAND[1]):
                continue
            if kappa > C.CHANCE_MAX or solo - kappa < C.INSTRUCTION_LIFT_MIN:
                continue
            adm.append(instructed_compliance(solo, kappa))
        out[kind] = {"measured": sorted({int(r["severity"]) for r in rows}),
                     "reaches_below": any(i <= iota_a - rule.d_below for i in adm),
                     "reaches_above": any(i >= iota_a + rule.d_above for i in adm),
                     "spectrum_candidate": True,
                     "n_admissible": len(adm)}
    return out


# ------------------------------------------------------------ per-frame rules
def frame_curves(frame_rows: Sequence[Mapping[str, Any]], *, kind: str,
                 grid: Sequence[int]) -> dict[str, dict[int, Any]]:
    """One frame's raw solo curve of ``kind`` over ``grid`` and, beside it,
    the chance on the frame's unconstrained cells (§13.2) and v7's
    all-absent basis; every quantity from the frame's own rows."""
    solo: dict[int, float] = {}
    load_zero: dict[int, float] = {}
    all_absent: dict[int, float] = {}
    n_topics: dict[int, int] = {}
    n_load_zero: dict[int, int] = {}
    for q in grid:
        rates = instance_rates(frame_rows, kind=kind, severity=q,
                               unconstrained_arm=UNCONSTRAINED_ARM)
        solo[q] = rates["solo"]
        all_absent[q] = rates["chance"]
        load_zero[q] = rates["chance_unconstrained"]
        n_topics[q] = rates["n_topics"]
        n_load_zero[q] = rates["n_topics_unconstrained"]
    return {"solo": solo, "chance_load_zero": load_zero,
            "chance_all_absent_v7_basis": all_absent, "n_topics": n_topics,
            "n_topics_load_zero": n_load_zero}


def _failure(step: int, status: str, detail: Mapping[str, Any]
             ) -> dict[str, Any]:
    if status not in S.FRAME_FAILURE_STATUSES:
        raise ProtocolError(f"{status!r} is not a frame failure status")
    return {"status": status, "step": step, **dict(detail)}


def frame_operating_points(frame_rows: Sequence[Mapping[str, Any]], *,
                           extension_measured: bool) -> dict[str, Any]:
    """§12.3 and §12.4 on one frame's own grid rows.

    Returns the frame's target and focal selections, its grid resolutions,
    its adequacy, and ``status`` (``SUPPORTED`` / ``UNSUPPORTED`` with the
    §12.3/§12.4 status it hit and the step it hit it at), or
    ``extension_required`` when §7.2's extension {15, 16} must be measured
    before the focal selection can re-run for this frame.
    """
    a = frame_curves(frame_rows, kind="A", grid=C.TARGET_GRID)
    b_grid = list(C.FOCAL_GRID) + (list(C.FOCAL_EXTENSION)
                                   if extension_measured else [])
    b = frame_curves(frame_rows, kind="B", grid=b_grid)
    target = regime_stage.select_target(a["solo"])
    focal = regime_stage.select_focal(
        {q: b["solo"][q] for q in C.FOCAL_GRID},
        ({q: b["solo"][q] for q in C.FOCAL_EXTENSION}
         if extension_measured else None))
    resolution = {
        "A": regime_stage.grid_resolution(a["solo"], band=C.TARGET_BAND,
                                          grid=C.TARGET_GRID),
        "B": regime_stage.grid_resolution(b["solo"], band=C.FOCAL_BAND,
                                          grid=b_grid)}
    out: dict[str, Any] = {
        "curves": {"A": a, "B": b}, "target_selection": target,
        "focal_selection": focal, "grid_resolution": resolution,
        "adequacy": None, "extension_required": bool(
            focal.get("extension_required")) and not extension_measured}
    if out["extension_required"]:
        out["status"] = None
        return out
    for step, (kind, result, exhausted) in enumerate(
            (("A", target, "TARGET_RANGE_EXHAUSTED"),
             ("B", focal, "FOCAL_RANGE_EXHAUSTED")), start=1):
        if result.get("selected") is not None:
            continue
        if resolution[kind]["insufficient"]:
            out["status"] = S.FRAME_UNSUPPORTED
            out["failure"] = _failure(step, "GRID_RESOLUTION_INSUFFICIENT", {
                "constraint": kind, "curve": result.get("curve"),
                "straddling_pairs": resolution[kind]["straddling_pairs"],
                "criterion": "§12.3: two adjacent registered severities lie "
                             "on opposite sides of a whole band"})
            return out
        out["status"] = S.FRAME_UNSUPPORTED
        out["failure"] = _failure(step, result.get("terminal_status", exhausted), {
            "constraint": kind, "curve": result.get("curve"),
            "criterion": "§12.3: an eligible severity inside the registered "
                         "band"})
        return out
    n_star, m_star = int(target["selected"]), int(focal["selected"])
    a_rates = instance_rates(frame_rows, kind="A", severity=n_star)
    b_rates = instance_rates(frame_rows, kind="B", severity=m_star)
    adequacy = regime_stage.regime_adequacy(
        solo_a=a_rates["solo"], solo_b=b_rates["solo"],
        vacuity_b=b_rates["vacuity"],
        graded_shares={
            "A": {"graded_share_above": a_rates["graded_share_above"],
                  "graded_share_below": a_rates["graded_share_below"]},
            "B": {"graded_share_above": b_rates["graded_share_above"],
                  "graded_share_below": b_rates["graded_share_below"]}})
    out["adequacy"] = adequacy
    out["n_star"], out["m_star"] = n_star, m_star
    out["n_topics_a"] = int(a_rates["n_topics"])
    if not adequacy["adequate"]:
        out["status"] = S.FRAME_UNSUPPORTED
        out["failure"] = _failure(3, "REGIME_NOT_FOUND", {
            "failures": adequacy["failures"],
            "criterion": "§12.4: the three regime-adequacy conditions"})
        return out
    out["status"] = S.FRAME_SUPPORTED
    out["identification_statuses"] = sorted(
        set(target.get("identification_statuses", []))
        | set(focal.get("identification_statuses", [])))
    return out


def terminal_status_over_frames(failures: Mapping[int, Mapping[str, Any]]
                                ) -> str:
    """The run-level status when no frame is supported: the status of the
    earliest §12.3 → §12.4 step at which some frame failed, the lowest
    frame index breaking a tie between statuses at that step. Deterministic
    and recorded beside every frame's own status."""
    if not failures:
        raise ProtocolError("no frame failure to summarise")
    step = min(f["step"] for f in failures.values())
    frame = min(w for w, f in failures.items() if f["step"] == step)
    return failures[frame]["status"]


def frame_a_coordinate(frame_rows: Sequence[Mapping[str, Any]], *,
                       n_star: int, curves: Mapping[str, Any],
                       pooled_grid_rows: Sequence[Mapping[str, Any]]
                       ) -> dict[str, Any]:
    """ι_A(f) on §13.2's basis: A's solo rate under frame f against A's
    chance on the unconstrained cells of frame f's blocks; per split and
    pooled, with the per-topic vectors §13.7 resamples. The chance pooled
    over every frame's blocks is recorded beside it as a check (the
    unconstrained cell states no wording), and v7's all-absent basis too;
    both are read by nothing."""
    a = curves["A"]
    kappa_a = a["chance_load_zero"][n_star]
    solo_a = a["solo"][n_star]
    iota_a = instructed_compliance(solo_a, kappa_a)
    iota_by_split, solo_by_split = {}, {}
    per_topic: dict[str, Any] = {"per_topic": {}, "chance": {}}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        try:
            solo = instance_rates(frame_rows, kind="A", severity=n_star,
                                  split=split)["solo"]
            kappa = _unconstrained_rate(frame_rows, kind="A", severity=n_star,
                                        split=split)["compliance"]
        except ProtocolError:
            continue
        solo_by_split[split] = solo
        iota_by_split[split] = instructed_compliance(solo, kappa)
        per_topic["per_topic"][split] = list(per_topic_compliance(
            frame_rows, kind="A", severity=n_star, split=split))
        per_topic["chance"][split] = kappa
    kappa_all_frames = _unconstrained_rate(pooled_grid_rows, kind="A",
                                           severity=n_star)["compliance"]
    return {
        "iota_a": iota_a, "kappa_a": kappa_a, "solo_compliance_a": solo_a,
        "iota_a_basis": "§13.2: A's chance on the unconstrained cells of "
                        "this frame's blocks in grid-A, the same basis as "
                        "every candidate's on this frame",
        "kappa_a_all_frames_blocks": kappa_all_frames,
        "iota_a_all_frames_chance_basis": instructed_compliance(
            solo_a, kappa_all_frames),
        "iota_a_all_absent_v7_basis": instructed_compliance(
            solo_a, a["chance_all_absent_v7_basis"][n_star]),
        "iota_a_by_split": iota_by_split, "solo_a_by_split": solo_by_split,
        "a_per_topic_by_split": per_topic,
        "n_topics_a": int(a["n_topics"][n_star]),
    }


def frame_tables(frame_rows: Sequence[Mapping[str, Any]], *,
                 candidate_rows: Sequence[Mapping[str, Any]],
                 candidates: Sequence[Constraint], m_star: int,
                 model_key: str, prescreen: Mapping[str, Mapping[str, Any]],
                 kappa_column: Mapping[str, Any] | None
                 ) -> tuple[dict[str, list[dict[str, Any]]],
                            dict[str, list[dict[str, Any]]],
                            dict[str, list[dict[str, Any]]]]:
    """§13.11's table for one frame: the candidates' solo rows of that
    frame, the chance column on the frame's own unconstrained cells (the
    producer refuses any other topic set), kappa(R|B) at the frame's m*.
    Returns (kept, withheld, measured) per split."""
    b_star = focal_constraint(m_star)
    b_solo_rows = [r for r in frame_rows if r["cell_id"] == f"solo:{b_star.label}"]
    measured = _calibration_rows(
        model_key, list(candidates), m_star=m_star, solo_rows=list(candidate_rows),
        chance_rows=list(frame_rows), b_solo_rows=b_solo_rows,
        kappa_column=kappa_column, prescreen=prescreen)
    kept, withheld = _withhold_degenerate(measured)
    return kept, withheld, measured


def _n_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {"total": len(rows),
            "load_0": sum(1 for r in rows if r.get("load") == 0),
            "load_1": sum(1 for r in rows if r.get("load") == 1),
            "topics": len({r["topic_id"] for r in rows})}


def _curve_dicts(p: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "solo_curves": {k: {str(q): v for q, v in p["curves"][k]["solo"].items()}
                        for k in ("A", "B")},
        "load_zero_chance_curves": {
            k: {str(q): v for q, v in p["curves"][k]["chance_load_zero"].items()}
            for k in ("A", "B")},
        "chance_curves_all_absent_v7_basis": {
            k: {str(q): v
                for q, v in p["curves"][k]["chance_all_absent_v7_basis"].items()}
            for k in ("A", "B")},
        "n_topics_load_zero": {
            k: {str(q): v for q, v in p["curves"][k]["n_topics_load_zero"].items()}
            for k in ("A", "B")}}


def supported_frame_block(frame: int, points: Mapping[str, Any], *,
                          frame_grid_rows: Sequence[Mapping[str, Any]],
                          frame_candidate_rows: Sequence[Mapping[str, Any]],
                          candidates: Sequence[Constraint], model_key: str,
                          prescreen: Mapping[str, Mapping[str, Any]],
                          pooled_grid_rows: Sequence[Mapping[str, Any]]
                          ) -> dict[str, Any]:
    """One supported frame's Gate-2 block from its own rows (round 0)."""
    n_star, m_star = int(points["n_star"]), int(points["m_star"])
    kappa_by_severity = _kappa_columns(frame_grid_rows, list(candidates),
                                       severities=[m_star], model_key=model_key)
    kept, withheld, measured = frame_tables(
        frame_grid_rows, candidate_rows=frame_candidate_rows,
        candidates=candidates, m_star=m_star, model_key=model_key,
        prescreen=prescreen, kappa_column=kappa_by_severity[str(m_star)])
    coordinate = frame_a_coordinate(frame_grid_rows, n_star=n_star,
                                    curves=points["curves"],
                                    pooled_grid_rows=pooled_grid_rows)
    return {
        "frame": frame, "status": S.FRAME_SUPPORTED,
        "n_star": n_star, "m_star": m_star,
        "target_selection": points["target_selection"],
        "focal_selection": points["focal_selection"],
        "grid_resolution": points["grid_resolution"],
        "adequacy": points["adequacy"],
        "identification_statuses": points["identification_statuses"],
        **_curve_dicts(points),
        **coordinate,
        "solo_compliance_b": points["curves"]["B"]["solo"][m_star],
        "kappa_under_b_by_severity": kappa_by_severity,
        "calibration_rows": kept,
        "calibration_rows_withheld": withheld,
        "n_candidates_withheld_degenerate": {s: len(r) for s, r in withheld.items()},
        "chance_basis": _chance_basis(frame_grid_rows),
        "prescreen_to_calibration": _prescreen_to_calibration(measured["pooled"]),
        "n_rows": {"grid": _n_rows(frame_grid_rows),
                   "candidates": _n_rows(frame_candidate_rows)},
    }


def unsupported_frame_block(frame: int, points: Mapping[str, Any], *,
                            frame_grid_rows: Sequence[Mapping[str, Any]],
                            frame_candidate_rows: Sequence[Mapping[str, Any]]
                            ) -> dict[str, Any]:
    return {
        "frame": frame, "status": S.FRAME_UNSUPPORTED,
        "unsupported_reason": points["failure"],
        "target_selection": points["target_selection"],
        "focal_selection": points["focal_selection"],
        "grid_resolution": points["grid_resolution"],
        "adequacy": points["adequacy"],
        **_curve_dicts(points),
        "n_rows": {"grid": _n_rows(frame_grid_rows),
                   "candidates": _n_rows(frame_candidate_rows)},
    }


def gate2_frames_from_rows(grid_rows: Sequence[Mapping[str, Any]],
                           candidate_rows: Sequence[Mapping[str, Any]], *,
                           candidates: Sequence[Constraint], model_key: str,
                           prescreen: Mapping[str, Mapping[str, Any]] | None = None,
                           extension_measured: bool = False) -> dict[str, Any]:
    """The per-frame Gate-2 blocks as a pure function of scored rows (no
    generation, no extension round): what ``gate2_payload`` computes between
    its two backend passes, exposed so the frame contracts can be tested on
    constructed rows. Raises nothing when no frame is supported; the caller
    decides the terminal."""
    frame_grid = {w: rows_of_frame(grid_rows, w) for w in S.FRAMES}
    frame_cand = {w: rows_of_frame(candidate_rows, w) for w in S.FRAMES}
    points = {w: frame_operating_points(frame_grid[w],
                                        extension_measured=extension_measured)
              for w in S.FRAMES}
    supported = [w for w in S.FRAMES if points[w]["status"] == S.FRAME_SUPPORTED]
    failures = {w: points[w]["failure"] for w in S.FRAMES
                if points[w]["status"] == S.FRAME_UNSUPPORTED}
    by_frame: dict[int, dict[str, Any]] = {}
    for w in S.FRAMES:
        if w in supported:
            by_frame[w] = supported_frame_block(
                w, points[w], frame_grid_rows=frame_grid[w],
                frame_candidate_rows=frame_cand[w], candidates=candidates,
                model_key=model_key, prescreen=prescreen or {},
                pooled_grid_rows=grid_rows)
        elif w in failures:
            by_frame[w] = unsupported_frame_block(
                w, points[w], frame_grid_rows=frame_grid[w],
                frame_candidate_rows=frame_cand[w])
    return {"points": points, "supported": supported, "failures": failures,
            "by_frame": by_frame}


# ------------------------------------------------------------------ the stage
def gate2_payload(tree: ModelTree, *, producing_commit: str,
                  second_pass_record: Mapping[str, Any],
                  regime_record: Mapping[str, Any],
                  bank: TopicBank | None = None, device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None,
                  topic_limit: int | None = None,
                  extension_rule: ExtensionRule | None = None
                  ) -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    binding = calibration_binding(bank, split="pooled", draws=C.M_CAL)
    topics = list(bank.topics(C.CALIBRATION_A)) + \
        list(bank.topics(C.CALIBRATION_B))
    if topic_limit is not None:
        assert_synthetic_only(tree, "topic_limit", topic_limit)
        per_split = max(1, topic_limit // 2)
        topics = (list(bank.topics(C.CALIBRATION_A))[:per_split]
                  + list(bank.topics(C.CALIBRATION_B))[:per_split])
    by_id = {t["topic_id"]: t for t in topics}
    generate = resolve_generate(tree, generate, screen_responder,
                                where=S.STAGE_GATE2)
    identity = protocol_identity(tree, S.STAGE_GATE2)
    cap = int(regime_record["selected_cap"])
    forwarded = list(second_pass_record["forwarded_set"])
    non_outcome = [c for c in constraints_from_labels(forwarded)
                   if c.kind not in ("A", "B")]
    extension_rule = extension_rule or ExtensionRule()
    grid_rows: list[dict[str, Any]] = []

    def measure_grid(kind: str, grid: Sequence[int], run_name: str) -> None:
        extended = any(q in C.FOCAL_EXTENSION for q in grid)
        slot_map = {f"{kind}{q}": Constraint(kind, q, extended=extended)
                    for q in grid}
        cells: list[Any] = []
        for block in blocks(topics, f"g2{run_name}"):
            cells.append(SoloCell(cell_id="unconstrained",
                                  arm=UNCONSTRAINED_ARM, block=block,
                                  slot=None, draws=C.M_CAL))
            for slot, constraint in slot_map.items():
                cells.append(SoloCell(cell_id=f"solo:{constraint.label}",
                                      arm="solo", block=block, slot=slot,
                                      draws=C.M_CAL))
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_map,
                               topic_split=_split_of(bank, c.topic_id))
                   for c in cells]
        instances = tuple(slot_map.values()) + tuple(
            c for c in non_outcome if c.kind != kind)
        rows = generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_GATE2, cap=cap,
            device=device, run_dir=tree.backend_runs(S.STAGE_GATE2) / run_name,
            instances=instances, slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)
        grid_rows.extend(rows)

    grids = {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID)}
    for kind, grid in grids.items():
        measure_grid(kind, grid, f"grid-{kind}")

    # ---------------------------------------- §12.3 / §12.4, per frame
    frame_grid_rows = {w: rows_of_frame(grid_rows, w) for w in S.FRAMES}
    extension_measured = False
    points = {w: frame_operating_points(frame_grid_rows[w],
                                        extension_measured=False)
              for w in S.FRAMES}
    if any(p["extension_required"] for p in points.values()):
        measure_grid("B", list(C.FOCAL_EXTENSION), "grid-B-extension")
        extension_measured = True
        frame_grid_rows = {w: rows_of_frame(grid_rows, w) for w in S.FRAMES}
        points = {w: frame_operating_points(frame_grid_rows[w],
                                            extension_measured=True)
                  for w in S.FRAMES}
    supported = [w for w in S.FRAMES if points[w]["status"] == S.FRAME_SUPPORTED]
    failures = {w: points[w]["failure"] for w in S.FRAMES
                if points[w]["status"] == S.FRAME_UNSUPPORTED}
    pooled_a = frame_curves(grid_rows, kind="A", grid=C.TARGET_GRID)
    pooled_b = frame_curves(grid_rows, kind="B", grid=(
        list(C.FOCAL_GRID) + (list(C.FOCAL_EXTENSION) if extension_measured
                              else [])))
    descriptive_pooled = {
        "solo_curves": {"A": {str(q): v for q, v in pooled_a["solo"].items()},
                        "B": {str(q): v for q, v in pooled_b["solo"].items()}},
        "target_selection": regime_stage.select_target(pooled_a["solo"]),
        "focal_selection": regime_stage.select_focal(
            {q: pooled_b["solo"][q] for q in C.FOCAL_GRID},
            ({q: pooled_b["solo"][q] for q in C.FOCAL_EXTENSION}
             if extension_measured else None)),
        "grid_resolution": {
            "A": regime_stage.grid_resolution(pooled_a["solo"], band=C.TARGET_BAND,
                                              grid=C.TARGET_GRID),
            "B": regime_stage.grid_resolution(
                pooled_b["solo"], band=C.FOCAL_BAND,
                grid=(list(C.FOCAL_GRID) + list(C.FOCAL_EXTENSION)
                      if extension_measured else list(C.FOCAL_GRID)))},
        "read_by": [],
        "standing": "descriptive only: what §12.3 would have said on the "
                    "frame-pooled instrument (v7's reading of §7.8); "
                    "selects nothing under Approach A",
    }
    if not supported:
        raise TerminalStatus(
            terminal_status_over_frames(failures), gate=S.STAGE_GATE2,
            criterion="§12.3 / §12.4 on every frame's own curves: no frame "
                      "has an operating point (docs/V8_FRAME_CONDITIONING.md "
                      "§6: the replication is terminal only when no frame is "
                      "supported)",
            observed={"by_frame": {str(w): f for w, f in failures.items()},
                      "descriptive_pooled_curves": descriptive_pooled["solo_curves"]},
            strongest_permissible_statement=S.TERMINAL_SENTENCE)

    # ------------------------------------- the candidates, on every block
    m_stars = sorted({int(points[w]["m_star"]) for w in supported})
    b_stars = tuple(focal_constraint(m) for m in m_stars)
    prescreen_by_candidate = {
        row["candidate"]: row
        for row in (regime_record.get("difficulty_table") or ())
        if not row.get("is_outcome")}

    def measure_candidates(cands: Sequence[Constraint], run_name: str
                           ) -> list[dict[str, Any]]:
        if not cands:
            return []
        slot_map = {f"S{i}": c for i, c in enumerate(cands)}
        cells = []
        for block in blocks(topics, f"g2{run_name}"):
            for slot, rung in slot_map.items():
                cells.append(SoloCell(cell_id=f"solo:{rung.label}", arm="solo",
                                      block=block, slot=slot, draws=C.M_CAL))
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_map,
                               topic_split=_split_of(bank, c.topic_id))
                   for c in cells]
        return generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_GATE2, cap=cap,
            device=device, run_dir=tree.backend_runs(S.STAGE_GATE2) / run_name,
            instances=tuple(cands) + b_stars, slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)

    candidate_rows = measure_candidates(non_outcome, "candidates")
    frame_candidate_rows = {w: rows_of_frame(candidate_rows, w) for w in supported}

    # ------------------------------------------ §13.11 per frame, round 0
    by_frame: dict[int, dict[str, Any]] = {}
    for w in supported:
        by_frame[w] = supported_frame_block(
            w, points[w], frame_grid_rows=frame_grid_rows[w],
            frame_candidate_rows=frame_candidate_rows[w],
            candidates=non_outcome, model_key=tree.model_key,
            prescreen=prescreen_by_candidate, pooled_grid_rows=grid_rows)

    # ---------------------------------------------- the extension round
    retention = second_pass_record.get("retention") or {}
    spectrum_families = list(retention.get("spectrum_families") or ())
    reach_by_frame: dict[int, dict[str, Any]] = {}
    plan_by_frame: dict[int, dict[str, Any]] = {}
    union_picks: dict[str, set[int]] = {}
    for w in supported:
        reach = reach_input(by_frame[w]["calibration_rows"]["pooled"],
                            spectrum_families=spectrum_families,
                            iota_a=by_frame[w]["iota_a"], rule=extension_rule)
        for split_rows in by_frame[w]["calibration_rows_withheld"].values():
            for row in split_rows:
                if row["kind"] in reach:
                    reach[row["kind"]]["measured"] = sorted(
                        set(reach[row["kind"]]["measured"]) | {int(row["severity"])})
        plan = calibration_extension_plan(reach, rule=extension_rule)
        reach_by_frame[w], plan_by_frame[w] = reach, plan
        for kind, qs in plan["picks"].items():
            union_picks.setdefault(kind, set()).update(int(q) for q in qs)
    extension_labels = [f"{k}:{q}" for k, qs in sorted(union_picks.items())
                        for q in sorted(qs)]
    extension_rows: list[dict[str, Any]] = []
    extension_withheld_by_frame: dict[int, dict[str, list[str]]] = {}
    if extension_labels:
        new = constraints_from_labels(extension_labels)
        extension_rows = measure_candidates(new, "extension-1")
        for w in supported:
            ext_rows_w = rows_of_frame(extension_rows, w)
            # kappa(R|B) for the new rungs: not scored absent on the grid's
            # B-solo cells (they did not exist then), so the column is
            # measured on the frame's B-solo rows by the per-candidate
            # path (`kappa_column=None`).
            kept, withheld, _measured = frame_tables(
                frame_grid_rows[w],
                candidate_rows=frame_candidate_rows[w] + ext_rows_w,
                candidates=new, m_star=by_frame[w]["m_star"],
                model_key=tree.model_key, prescreen=prescreen_by_candidate,
                kappa_column=None)
            for split in by_frame[w]["calibration_rows"]:
                by_frame[w]["calibration_rows"][split].extend(kept[split])
                by_frame[w]["calibration_rows_withheld"][split].extend(
                    withheld.get(split, []))
            by_frame[w]["n_candidates_withheld_degenerate"] = {
                s: len(r) for s, r in by_frame[w]["calibration_rows_withheld"].items()}
            by_frame[w]["n_rows"]["extension"] = _n_rows(ext_rows_w)
            extension_withheld_by_frame[w] = {
                s: [f"{r['kind']}:{r['severity']}" for r in rows]
                for s, rows in withheld.items()}
    for w in supported:
        by_frame[w]["extension_reach"] = reach_by_frame[w]
        by_frame[w]["extension_plan"] = plan_by_frame[w]
        by_frame[w]["extension_withheld"] = extension_withheld_by_frame.get(w, {})
        by_frame[w]["kappa_b_under_candidate"] = _kappa_b_under_candidate(
            frame_candidate_rows[w] + rows_of_frame(extension_rows, w),
            m_star=by_frame[w]["m_star"], model_key=tree.model_key)
    for w in failures:
        by_frame[w] = unsupported_frame_block(
            w, points[w], frame_grid_rows=frame_grid_rows[w],
            frame_candidate_rows=rows_of_frame(candidate_rows, w))

    # The wording diagnostic at calibration precision: every load-1 row of
    # the grids, the candidates and the extension, per (frame, family, q),
    # per split and pooled over the splits; each frame's ladder; each
    # frame's stability between the two disjoint splits; the dependence of
    # ι on the frame. "pooled" here pools the two SPLITS, never the frames.
    all_rows = grid_rows + candidate_rows + extension_rows
    wording_by_frame = {
        C.CALIBRATION_A: W.frame_table(all_rows, split=C.CALIBRATION_A),
        C.CALIBRATION_B: W.frame_table(all_rows, split=C.CALIBRATION_B),
        "pooled": W.frame_table(all_rows)}
    comparison_pooled = W.frame_comparison(wording_by_frame["pooled"])
    statuses = sorted({s for w in supported
                       for s in by_frame[w]["identification_statuses"]})
    return {
        "stage": S.STAGE_GATE2,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE2],
        "outcome": "PASS",
        "inputs": {"second_pass": {"stage": S.STAGE_SECOND_PASS,
                                   "n_forwarded": len(forwarded)},
                   "regime": {"stage": S.STAGE_REGIME, "cap": cap}},
        "producing_commit": producing_commit,
        "frame_conditioning": FRAME_CONDITIONING_STATEMENT,
        "frames": list(S.FRAMES),
        "supported_frames": supported,
        "unsupported_frames": {str(w): f for w, f in failures.items()},
        "by_frame": {str(w): by_frame[w] for w in S.FRAMES},
        "descriptive_pooled": descriptive_pooled,
        "grids": {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID),
                  "B_extension": list(C.FOCAL_EXTENSION),
                  "focal_extension_measured": extension_measured,
                  "draws": C.M_CAL, "n_topics": len(by_id),
                  "blocks_per_frame": {str(w): len({r["block_id"] for r in
                                                    frame_grid_rows[w]})
                                       for w in S.FRAMES}},
        "construct_floor": {"applied": False,
                            "why": "§34 D17's floor selects a confirmatory "
                                   "operating point; the pilot selects none "
                                   "and reads m*(f) only for kappa(R|B)"},
        "calibration_population": {
            "forwarded": forwarded, "n_measured": len(non_outcome),
            "measured_under_every_frame": True,
            "rule": "the second pass's retention (spaced by role for "
                    "spectrum families, caliper-likely for local families, "
                    "class and near-form arms), not §12.7's tier budget; "
                    "pooled over frames as a measurement budget "
                    "(V8_FRAME_CONDITIONING.md §5); every forwarded rung is "
                    "calibrated on every block, hence under every frame"},
        "b_instances_scored_absent_on_candidate_cells": [b.label for b in b_stars],
        "calibration_binding": binding,
        "calibration_topic_ids": sorted(by_id),
        "chance_basis": {**_chance_basis(grid_rows),
                         "per_frame": "each frame's table reads kappa on the "
                                      "unconstrained cells of its own blocks "
                                      "(by_frame[f].chance_basis); the "
                                      "producer refuses any other topic set"},
        "extension": {"reach_by_frame": {str(w): r for w, r in reach_by_frame.items()},
                      "plan_by_frame": {str(w): p for w, p in plan_by_frame.items()},
                      "measured": extension_labels,
                      "measured_rule": "the union of the supported frames' "
                                       "plans, each bounded by the rule; a "
                                       "rung measured for one frame is data "
                                       "for every frame",
                      "n_rows": len(extension_rows),
                      "withheld_by_frame": {str(w): v for w, v in
                                            extension_withheld_by_frame.items()},
                      "rule": {"calibration_picks": extension_rule.calibration_picks,
                               "d_below": extension_rule.d_below,
                               "d_above": extension_rule.d_above,
                               "rounds": 1}},
        "wording_by_frame": wording_by_frame,
        "frame_comparison_pooled": comparison_pooled,
        "ladders_by_frame_pooled": W.ladders_by_frame(wording_by_frame["pooled"]),
        "wording_dependence_pooled": W.wording_dependence(comparison_pooled),
        "split_stability_by_frame": W.stability_by_frame(
            wording_by_frame[C.CALIBRATION_A], wording_by_frame[C.CALIBRATION_B],
            names=(C.CALIBRATION_A, C.CALIBRATION_B)),
        "rungs_by_wording_class": W.sensitive_rungs(comparison_pooled),
        "row_accounting": {
            run.name: row_accounting(run)
            for run in sorted(tree.backend_runs(S.STAGE_GATE2).iterdir())
            if run.is_dir()},
        "n_candidates_measured": len(non_outcome) + len(extension_labels),
        "identification_statuses": statuses,
        "selected_on": C.SECONDARY_DIFFICULTY_COORDINATE,
        "no_composed_cells": S.NO_COMPOSED_CELLS,
    }


def run_gate2(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "", bank: TopicBank | None = None,
              device: int = 0,
              generate: Callable[..., dict[str, Any]] | None = None,
              topic_limit: int | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    regime = transitions.read_stage_record(tree, S.STAGE_REGIME)
    second_pass = transitions.read_stage_record(tree, S.STAGE_SECOND_PASS)
    return run_stage(
        tree, S.STAGE_GATE2,
        compute=lambda _previous: gate2_payload(
            tree, producing_commit=commit, second_pass_record=second_pass,
            regime_record=regime, bank=bank, device=device,
            generate=generate, topic_limit=topic_limit),
        producing_commit=commit, environment_digest=environment_digest)
