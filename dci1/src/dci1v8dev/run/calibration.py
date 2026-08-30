"""Stage 7, ``GATE_2_CALIBRATION``: n*, m*, the forwarded set at calibration
precision, §13.11's table on §13.2's chance basis, and one extension round.

Two passes on the 192 calibration topics at M_cal = 4, as v7's Gate 2:

1. A's grid, B's grid and the unconstrained cell (``grid-A``, ``grid-B``),
   which fix n* and m* by §12.3 on the pooled raw solo curves, check §12.4's
   adequacy, and supply every candidate's chance compliance --- **read on
   the unconstrained cell**, the §13.2 basis, by the producer the v7 fix
   7f89dae introduced (``dci1v7.run.gates_run._calibration_rows``, imported);
2. one solo cell per forwarded candidate (``candidates``) with B at m*
   present as an *absent* instance, which is where kappa(R|B) comes from.

Then **one bounded extension round** (``extension-1``): a spectrum-candidate
family whose admissible rungs do not reach an offset on one side, with
unmeasured reserve in that direction, gets at most two reserve rungs on that
side at the same precision (``prescreen.extension.calibration_extension_plan``).

The v7 record's iota_A was formed with a chance rate averaged over the
grid's other target severities as well as the unconstrained cell (the
recorded basis discrepancy); here iota_A is on the unconstrained cell, and
the all-absent value is recorded beside it, read by nothing.
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
from dci1v7.verifiers.constraints import FAMILIES, Constraint

from dci1v8dev import rules as R
from dci1v8dev.prescreen.extension import ExtensionRule, calibration_extension_plan
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run import wording as W
from dci1v8dev.run.execute import (UNCONSTRAINED_ARM, SoloCell, blocks,
                                   cell_rates, generate_and_score,
                                   instance_rates, per_topic_compliance,
                                   prompt_cell, resolve_generate,
                                   row_accounting)
from dci1v8dev.run.lifecycle import (StageOutcome, TerminalStatus,
                                     protocol_identity, run_stage)
from dci1v8dev.run.regime import screen_responder

__all__ = ["gate2_payload", "run_gate2", "constraints_from_labels",
           "assert_synthetic_only", "reach_input"]


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
    coordinate) reaches each offset --- the extension plan's input."""
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

    grids = {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID)}
    curves: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    chance_all_absent: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    load_zero: dict[str, dict[int, float]] = {"A": {}, "B": {}}
    n_load_zero: dict[str, int] = {}
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
        for q in grid:
            rates = instance_rates(rows, kind=kind, severity=q,
                                   unconstrained_arm=UNCONSTRAINED_ARM)
            curves[kind][q] = rates["solo"]
            chance_all_absent[kind][q] = rates["chance"]
            load_zero[kind][q] = rates["chance_unconstrained"]
            n_load_zero[kind] = rates["n_topics_unconstrained"]

    for kind, grid in grids.items():
        measure_grid(kind, grid, f"grid-{kind}")

    target = regime_stage.select_target(curves["A"])
    focal = regime_stage.select_focal(curves["B"])
    extension_measured = False
    if focal.get("extension_required"):
        measure_grid("B", list(C.FOCAL_EXTENSION), "grid-B-extension")
        extension_measured = True
        focal = regime_stage.select_focal(
            {q: curves["B"][q] for q in C.FOCAL_GRID},
            {q: curves["B"][q] for q in C.FOCAL_EXTENSION})
    resolution = {
        "A": regime_stage.grid_resolution(curves["A"], band=C.TARGET_BAND,
                                          grid=C.TARGET_GRID),
        "B": regime_stage.grid_resolution(
            curves["B"], band=C.FOCAL_BAND,
            grid=(list(C.FOCAL_GRID) + list(C.FOCAL_EXTENSION)
                  if extension_measured else list(C.FOCAL_GRID)))}
    for kind, result, status in (("A", target, "TARGET_RANGE_EXHAUSTED"),
                                 ("B", focal, "FOCAL_RANGE_EXHAUSTED")):
        if result.get("selected") is not None:
            continue
        if resolution[kind]["insufficient"]:
            raise TerminalStatus(
                "GRID_RESOLUTION_INSUFFICIENT", gate=S.STAGE_GATE2,
                criterion="§12.3: two adjacent registered severities lie on "
                          "opposite sides of a whole band",
                observed={"constraint": kind, "curve": result.get("curve"),
                          "straddling_pairs":
                              resolution[kind]["straddling_pairs"]},
                strongest_permissible_statement=S.TERMINAL_SENTENCE)
        raise TerminalStatus(
            result.get("terminal_status", status), gate=S.STAGE_GATE2,
            criterion="§12.3: an eligible severity inside the registered band",
            observed={"curve": result.get("curve")},
            strongest_permissible_statement=S.TERMINAL_SENTENCE)
    m_star, n_star = int(focal["selected"]), int(target["selected"])

    a_rates = instance_rates(grid_rows, kind="A", severity=n_star)
    b_rates = instance_rates(grid_rows, kind="B", severity=m_star)
    adequacy = regime_stage.regime_adequacy(
        solo_a=a_rates["solo"], solo_b=b_rates["solo"],
        vacuity_b=b_rates["vacuity"],
        graded_shares={
            "A": {"graded_share_above": a_rates["graded_share_above"],
                  "graded_share_below": a_rates["graded_share_below"]},
            "B": {"graded_share_above": b_rates["graded_share_above"],
                  "graded_share_below": b_rates["graded_share_below"]}})
    if not adequacy["adequate"]:
        raise TerminalStatus(
            "REGIME_NOT_FOUND", gate=S.STAGE_GATE2,
            criterion="§12.4: the three regime-adequacy conditions",
            observed=adequacy["failures"],
            strongest_permissible_statement=S.TERMINAL_SENTENCE)

    b_star = focal_constraint(m_star)
    kappa_by_severity = _kappa_columns(grid_rows, non_outcome,
                                       severities=[m_star],
                                       model_key=tree.model_key)
    prescreen_by_candidate = {
        row["candidate"]: row
        for row in (regime_record.get("difficulty_table") or ())
        if not row.get("is_outcome")}
    b_solo_rows = [r for r in grid_rows
                   if r["cell_id"] == f"solo:{b_star.label}"]

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
            instances=tuple(cands) + (b_star,), slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)

    candidate_rows = measure_candidates(non_outcome, "candidates")
    measured_tables = _calibration_rows(
        tree.model_key, non_outcome, m_star=m_star, solo_rows=candidate_rows,
        chance_rows=grid_rows, b_solo_rows=b_solo_rows,
        kappa_column=kappa_by_severity[str(m_star)],
        prescreen=prescreen_by_candidate)
    tables, withheld = _withhold_degenerate(measured_tables)

    # iota_A on §13.2's basis, per split and pooled.
    kappa_a = load_zero["A"][n_star]
    iota_a = instructed_compliance(curves["A"][n_star], kappa_a)
    iota_a_by_split, solo_a_by_split, a_per_topic = {}, {}, {"per_topic": {},
                                                             "chance": {}}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        try:
            solo = instance_rates(grid_rows, kind="A", severity=n_star,
                                  split=split)["solo"]
            kappa = _unconstrained_rate(grid_rows, kind="A", severity=n_star,
                                        split=split)["compliance"]
        except ProtocolError:
            continue
        solo_a_by_split[split] = solo
        iota_a_by_split[split] = instructed_compliance(solo, kappa)
        a_per_topic["per_topic"][split] = list(per_topic_compliance(
            grid_rows, kind="A", severity=n_star, split=split))
        a_per_topic["chance"][split] = kappa

    # ---------------------------------------------- the extension round
    retention = second_pass_record.get("retention") or {}
    spectrum_families = list(retention.get("spectrum_families") or ())
    reach = reach_input(tables["pooled"], spectrum_families=spectrum_families,
                        iota_a=iota_a, rule=extension_rule)
    # a family's measured severities include the withheld (degenerate) rows
    for split_rows in withheld.values():
        for row in split_rows:
            if row["kind"] in reach:
                reach[row["kind"]]["measured"] = sorted(
                    set(reach[row["kind"]]["measured"]) | {int(row["severity"])})
    plan = calibration_extension_plan(reach, rule=extension_rule)
    extension_labels = [f"{k}:{q}" for k, qs in sorted(plan["picks"].items())
                        for q in qs]
    extension_rows: list[dict[str, Any]] = []
    extension_withheld: dict[str, list[dict[str, Any]]] = {}
    if extension_labels:
        new = constraints_from_labels(extension_labels)
        extension_rows = measure_candidates(new, "extension-1")
        # kappa(R|B) for the new rungs: they were not scored absent on the
        # grid's B-solo cells (they did not exist then), so the column is
        # measured on the same B-solo rows by the per-candidate reference
        # path (`kappa_column=None`) --- the grid rows carry every
        # registered instance only for the round-0 candidates.
        ext_tables = _calibration_rows(
            tree.model_key, new, m_star=m_star, solo_rows=extension_rows,
            chance_rows=grid_rows, b_solo_rows=b_solo_rows,
            kappa_column=None, prescreen=prescreen_by_candidate)
        kept, extension_withheld = _withhold_degenerate(ext_tables)
        for split in tables:
            tables[split].extend(kept[split])
            withheld[split].extend(extension_withheld.get(split, []))
    statuses = sorted(set(target.get("identification_statuses", [])
                          + focal.get("identification_statuses", [])))
    # The wording diagnostic at calibration precision: every load-1 row of
    # the grids, the candidates and the extension, per (frame, family, q),
    # per split and pooled; each frame's ladder; each frame's stability
    # between the two disjoint splits; the dependence of ι on the frame.
    all_rows = grid_rows + candidate_rows + extension_rows
    wording_by_frame = {
        C.CALIBRATION_A: W.frame_table(all_rows, split=C.CALIBRATION_A),
        C.CALIBRATION_B: W.frame_table(all_rows, split=C.CALIBRATION_B),
        "pooled": W.frame_table(all_rows)}
    comparison_pooled = W.frame_comparison(wording_by_frame["pooled"])
    return {
        "stage": S.STAGE_GATE2,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE2],
        "outcome": "PASS",
        "inputs": {"second_pass": {"stage": S.STAGE_SECOND_PASS,
                                   "n_forwarded": len(forwarded)},
                   "regime": {"stage": S.STAGE_REGIME, "cap": cap}},
        "producing_commit": producing_commit,
        "n_star": n_star, "m_star": m_star,
        "target_selection": target, "focal_selection": focal,
        "focal_extension_measured": extension_measured,
        "adequacy": adequacy, "grid_resolution": resolution,
        "construct_floor": {"applied": False,
                            "why": "§34 D17's floor selects a confirmatory "
                                   "operating point; the pilot selects none "
                                   "and reads m* only for kappa(R|B)"},
        "solo_curves": {k: {str(q): v for q, v in c.items()}
                        for k, c in curves.items()},
        "chance_curves_all_absent_v7_basis": {
            k: {str(q): v for q, v in c.items()}
            for k, c in chance_all_absent.items()},
        "load_zero_chance_curves": {k: {str(q): v for q, v in c.items()}
                                    for k, c in load_zero.items()},
        "n_topics_load_zero": dict(n_load_zero),
        "iota_a": iota_a, "kappa_a": kappa_a,
        "iota_a_basis": "§13.2: A's chance on the unconstrained cell of "
                        "grid-A, the same basis as every candidate's",
        "iota_a_all_absent_v7_basis": instructed_compliance(
            curves["A"][n_star], chance_all_absent["A"][n_star]),
        "solo_compliance_a": curves["A"][n_star],
        "solo_compliance_b": curves["B"][m_star],
        "iota_a_by_split": iota_a_by_split,
        "solo_a_by_split": solo_a_by_split,
        "a_per_topic_by_split": a_per_topic,
        "calibration_population": {
            "forwarded": forwarded, "n_measured": len(non_outcome),
            "rule": "the second pass's retention (spaced by role for "
                    "spectrum families, caliper-likely for local families, "
                    "class and near-form arms), not §12.7's tier budget"},
        "kappa_under_b_by_severity": kappa_by_severity,
        "calibration_binding": binding,
        "calibration_topic_ids": sorted(by_id),
        "calibration_rows": tables,
        "calibration_rows_withheld": withheld,
        "n_candidates_withheld_degenerate": {s: len(r) for s, r in withheld.items()},
        "chance_basis": _chance_basis(grid_rows),
        "extension": {"reach": reach, "plan": plan,
                      "measured": extension_labels,
                      "n_rows": len(extension_rows),
                      "withheld": {s: [f"{r['kind']}:{r['severity']}"
                                       for r in rows]
                                   for s, rows in extension_withheld.items()},
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
        "kappa_b_under_candidate": _kappa_b_under_candidate(
            candidate_rows + extension_rows, m_star=m_star,
            model_key=tree.model_key),
        "prescreen_to_calibration": _prescreen_to_calibration(
            measured_tables["pooled"]),
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
