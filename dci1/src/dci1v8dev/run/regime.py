"""Stage 4, ``REGIME_SCREEN``: the cap, the broad ladder screen under the v8
frames, and the uncertainty-aware first pass.

§12.1's cap selection and §12.2's dense screen are v7's in cost and shape
(every selectable family's round-0 ladder, A's grid, B's grid and one
unconstrained cell, on the twenty-four pre-screen topics at one draw). Two
things are v8's: the prompt is rendered under the v8 instrument, and the
**chance rate of every rung is read on the unconstrained cell** ---
§13.2's basis, the one calibration uses --- not over every row in which the
rung was absent (v7's ``instance_rates`` denominator, recorded beside it for
the comparison). The record carries the difficulty table, the counts the
screen consumes (``prescreen_table``, ``a_grid``), the frame-reliability
measurement, and the first-pass verdicts of ``dci1v8dev.prescreen.screen``
(ACCEPT / REJECT / RESAMPLE, labels, per-rung posteriors).

Nothing here decides admission: the screen's verdicts steer the second pass
and the retention; the LOCAL/SPECTRUM rules run at calibration precision.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v4.models.registry import get_model
from dci1v7.protocol import constants as C
from dci1v7.run.regime_run import select_cap
from dci1v7.stages.calibration_table import instructed_compliance
from dci1v7.topics.bank import (TopicBank, assert_no_reserved_topic_spent,
                                load_bank)
from dci1v7.verifiers.constraints import (FAMILIES, SELECTABLE_FAMILY_IDS,
                                          Constraint, assert_selectable,
                                          registered_severities)

from dci1v8dev.prescreen.legacy import prescreen_iota_a
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import ScreenConfig, screen_families
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.execute import (UNCONSTRAINED_ARM, SoloCell, blocks,
                                   generate_and_score, instance_rates,
                                   prompt_cell, resolve_generate)
from dci1v8dev.run.instrument import frame_reliability
from dci1v8dev.run.lifecycle import (StageOutcome, TerminalStatus,
                                     protocol_identity, run_stage)
from dci1v8dev.run.seeds import screen_seed

__all__ = ["cap_cells", "select_cap", "screen_rungs", "ladder_cells",
           "prescreen_counts", "difficulty_table", "prescreen_input",
           "jsonable", "regime_payload", "run_regime_screen",
           "screen_responder"]


def cap_cells(topics: Sequence[Mapping[str, Any]], *, cap: int,
              draws: int = 1) -> tuple[list[Any], dict[str, Constraint]]:
    """§12.1's cap-selection set: loads 0 and 1 (no composed cell)."""
    a = Constraint("A", C.TARGET_GRID[len(C.TARGET_GRID) // 2])
    b = Constraint("B", C.FOCAL_GRID[len(C.FOCAL_GRID) // 2])
    slot_map = {"A": a, "B": b}
    cells: list[Any] = []
    for block in blocks(topics, f"cap{cap}"):
        cells.append(SoloCell(cell_id="unconstrained", arm=UNCONSTRAINED_ARM,
                              block=block, slot=None, draws=draws))
        cells.append(SoloCell(cell_id=f"solo:{a.label}", arm="solo",
                              block=block, slot="A", draws=draws))
        cells.append(SoloCell(cell_id=f"solo:{b.label}", arm="solo",
                              block=block, slot="B", draws=draws))
    return cells, slot_map


def screen_rungs() -> list[Constraint]:
    """Every selectable family's round-0 ladder, then A's and B's grids."""
    rungs: list[Constraint] = []
    for kind in SELECTABLE_FAMILY_IDS:
        assert_selectable(kind, where="the v8 screen")
        rungs.extend(Constraint(kind, q) for q in registered_severities(kind))
    rungs.extend(Constraint("A", q) for q in C.TARGET_GRID)
    rungs.extend(Constraint("B", q) for q in C.FOCAL_GRID)
    return rungs


def ladder_cells(topics: Sequence[Mapping[str, Any]],
                 rungs: Sequence[Constraint], *, prefix: str = "screen",
                 draws: int = C.LADDER_SCREEN_DRAWS
                 ) -> tuple[list[Any], dict[str, Constraint]]:
    slot_map = {f"S{i}": rung for i, rung in enumerate(rungs)}
    cells: list[Any] = []
    for block in blocks(topics, prefix):
        cells.append(SoloCell(cell_id="unconstrained", arm=UNCONSTRAINED_ARM,
                              block=block, slot=None, draws=draws))
        for slot, rung in slot_map.items():
            cells.append(SoloCell(cell_id=f"solo:{rung.label}", arm="solo",
                                  block=block, slot=slot, draws=draws))
    return cells, slot_map


def prescreen_counts(rows: Sequence[Mapping[str, Any]],
                     rungs: Sequence[Constraint]) -> list[dict[str, Any]]:
    """Per rung: solo, vacuity and unconstrained-cell chance **counts** over
    the rows, in draws --- the schema ``dci1v8dev.prescreen.schema`` reads.
    ``chance_k`` is the count of passes on the unconstrained cell, so the
    stated basis ``chance_n`` is that cell's row count."""
    wanted = {r.label: r for r in rungs}
    solo: dict[str, dict[str, list[int]]] = {}
    vac: dict[str, int] = {}
    chance: dict[str, list[int]] = {}
    for row in rows:
        for s in row["scores"]:
            label = f"{s['kind']}:{s['severity']}"
            if label not in wanted:
                continue
            if s["present"]:
                per = solo.setdefault(label, {})
                per.setdefault(row["topic_id"], []).append(int(bool(s["passed"])))
                vac[label] = vac.get(label, 0) + int(bool(s["vacuous_pass"]))
            elif row.get("arm") == UNCONSTRAINED_ARM:
                chance.setdefault(label, []).append(int(bool(s["passed"])))
    out = []
    for rung in rungs:
        per = solo.get(rung.label, {})
        if not per:
            raise ProtocolError(f"{rung.label}: no solo row on the screen")
        draws = {len(v) for v in per.values()}
        if len(draws) != 1:
            raise ProtocolError(f"{rung.label}: unequal draws per topic")
        n_topics, dpt = len(per), draws.pop()
        ch = chance.get(rung.label)
        if not ch:
            raise ProtocolError(
                f"{rung.label}: not scored on the unconstrained cell; "
                "§13.2's chance basis is missing")
        out.append({"kind": rung.kind, "severity": rung.severity,
                    "solo_k": int(sum(sum(v) for v in per.values())),
                    "solo_n": int(n_topics * dpt),
                    "chance_k": float(sum(ch)), "chance_n": float(len(ch)),
                    "vacuous_k": int(vac.get(rung.label, 0)),
                    "n_topics": int(n_topics), "draws_per_topic": int(dpt),
                    "reserve": bool(rung.reserve)})
    return out


def difficulty_table(rows: Sequence[Mapping[str, Any]],
                     rungs: Sequence[Constraint]) -> list[dict[str, Any]]:
    """§12.2's table with the chance rate on the unconstrained cell and v7's
    all-absent denominator beside it, for the record."""
    table = []
    for rung in rungs:
        rates = instance_rates(rows, kind=rung.kind, severity=rung.severity,
                               unconstrained_arm=UNCONSTRAINED_ARM)
        kappa = rates["chance_unconstrained"]
        iota = (instructed_compliance(rates["solo"], kappa)
                if kappa < C.CHANCE_DEGENERACY_MAX else None)
        family = FAMILIES.get(rung.kind)
        table.append({"candidate": rung.label, "kind": rung.kind,
                      "severity": rung.severity, "solo": rates["solo"],
                      "chance": kappa,
                      "chance_all_absent_v7_basis": rates["chance"],
                      "vacuity": rates["vacuity"],
                      "graded_mean": rates["graded_mean"],
                      "median_words": rates["median_words"],
                      "truncation": rates["truncation"],
                      "n_topics": rates["n_topics"],
                      "n_topics_unconstrained": rates["n_topics_unconstrained"],
                      "iota": iota,
                      "tier": family.structural_tier if family else None,
                      "is_outcome": family is None,
                      "family": rung.kind if family else None,
                      "reserve": bool(rung.reserve)})
    return table


def prescreen_input(counts: Sequence[Mapping[str, Any]]
                    ) -> tuple[list[PrescreenRung], list[ARung]]:
    """The screen's input from the recorded counts (B is not screened)."""
    table, a_grid = [], []
    for row in counts:
        if row["kind"] == "A":
            a_grid.append(ARung(severity=row["severity"], solo_k=row["solo_k"],
                                solo_n=row["solo_n"], chance_k=row["chance_k"],
                                chance_n=row["chance_n"],
                                n_topics=row["n_topics"],
                                draws_per_topic=row["draws_per_topic"]))
        elif row["kind"] == "B" or row["kind"] not in FAMILIES:
            continue
        else:
            table.append(PrescreenRung(
                kind=row["kind"], severity=row["severity"],
                solo_k=row["solo_k"], solo_n=row["solo_n"],
                chance_k=row["chance_k"], chance_n=row["chance_n"],
                vacuous_k=min(row["vacuous_k"], row["solo_k"]),
                n_topics=row["n_topics"],
                draws_per_topic=row["draws_per_topic"],
                reserve=bool(row.get("reserve"))))
    return table, a_grid


def jsonable(value: Any) -> Any:
    """Numpy scalars and arrays to plain Python, recursively."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and value != value:
        return None
    return value


def screen_record(screen: Mapping[str, Any]) -> dict[str, Any]:
    """The screen's output as a record: the draws themselves are dropped
    (they are a function of the counts and the seed), everything else kept."""
    out = jsonable(dict(screen))
    out["iota_a"] = {k: v for k, v in out["iota_a"].items()
                     if k not in ("iota_a", "n_star")}
    for fam in out["families"].values():
        fam.pop("params", None)
    return out


def screen_responder(row: Mapping[str, Any]) -> str:
    words = ["thus", "hence", "though", "whereas", "indeed", "namely",
             "instead", "overall", "answer", "text", "reply", "words"]
    seed = sum(ord(ch) for ch in str(row["row_id"]))
    return " ".join(words[(seed + i) % len(words)]
                    for i in range(70)).capitalize() + "."


def _by_id(topics: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {t["topic_id"]: t for t in topics}


def regime_payload(tree: ModelTree, *, producing_commit: str,
                   bank: TopicBank | None = None, device: int = 0,
                   generate: Callable[..., dict[str, Any]] | None = None,
                   caps: Sequence[int] = C.COMPLETION_CAPS,
                   rungs: Sequence[Constraint] | None = None,
                   screen_config: ScreenConfig | None = None
                   ) -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    prescreen = list(bank.topics("prescreen"))
    assert_no_reserved_topic_spent([t["topic_id"] for t in prescreen],
                                   bank.sets, stage=S.STAGE_REGIME)
    generate = resolve_generate(tree, generate, screen_responder,
                                where=S.STAGE_REGIME)
    identity = protocol_identity(tree, S.STAGE_REGIME)

    truncation: dict[int, float] = {}
    for cap in caps:
        cells, slot_map = cap_cells(prescreen, cap=cap)
        prompts = [prompt_cell(c, _by_id(prescreen)[c.topic_id],
                               slot_map=slot_map, topic_split="prescreen")
                   for c in cells]
        rows = generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_REGIME, cap=cap,
            device=device, run_dir=tree.backend_runs(S.STAGE_REGIME)
            / f"cap-{cap}", instances=tuple(slot_map.values()),
            slot_map=slot_map, study_id=tree.context.study_id,
            protocol_identity=identity, generate=generate)
        truncation[cap] = (sum(1 for r in rows if r["truncated"])
                           / max(1, len(rows)))
    cap_result = select_cap(truncation)
    if cap_result["selected_cap"] is None:
        raise TerminalStatus(
            "RESPONSE_LENGTH_INCOMPATIBLE", gate=S.STAGE_REGIME,
            criterion=f"§12.1: truncation <= {C.CAP_TRUNCATION_MAX} at some "
                      "registered cap",
            observed=cap_result["truncation_by_cap"],
            strongest_permissible_statement=S.TERMINAL_SENTENCE)
    cap = cap_result["selected_cap"]

    measured = list(rungs) if rungs is not None else screen_rungs()
    cells, slot_map = ladder_cells(prescreen, measured)
    prompts = [prompt_cell(c, _by_id(prescreen)[c.topic_id],
                           slot_map=slot_map, topic_split="prescreen")
               for c in cells]
    screen_rows = generate_and_score(
        tree.model_key, prompts, stage=S.STAGE_REGIME, cap=cap, device=device,
        run_dir=tree.backend_runs(S.STAGE_REGIME) / "ladder",
        instances=tuple(slot_map.values()), slot_map=slot_map,
        study_id=tree.context.study_id, protocol_identity=identity,
        generate=generate)
    table = difficulty_table(screen_rows, measured)
    counts = prescreen_counts(screen_rows, measured)
    reliability = frame_reliability(screen_rows)
    rung_table, a_grid = prescreen_input(counts)
    config = screen_config or ScreenConfig(
        base_seed=screen_seed(get_model(tree.model_key).model_id,
                              S.STAGE_REGIME))
    screen = screen_families(rung_table, a_grid, config=config)
    iota_a_point, n_star_point = prescreen_iota_a(a_grid)
    return {
        "stage": S.STAGE_REGIME,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_REGIME],
        "outcome": "PASS",
        "inputs": {"gate0": {"stage": S.STAGE_GATE0}},
        "producing_commit": producing_commit,
        "selected_cap": cap,
        "cap_selection": cap_result,
        "difficulty_table": table,
        "prescreen_table": counts,
        "n_rungs_measured": len(measured),
        "chance_basis": {
            "cell": UNCONSTRAINED_ARM,
            "rule": "§13.2: kappa on the screen's unconstrained cell (24 "
                    "pre-screen topics × 1 draw), every rung scored absent "
                    "on it; v7's all-absent denominator is recorded beside "
                    "it as chance_all_absent_v7_basis and read by nothing",
            "n_unconstrained_rows": sum(
                1 for r in screen_rows if r.get("arm") == UNCONSTRAINED_ARM)},
        "frame_reliability": reliability,
        "screen": screen_record(screen),
        "screen_statuses": jsonable(screen["statuses"]),
        "screen_labels": jsonable(screen["labels"]),
        "iota_a_prescreen": (float(iota_a_point)
                             if iota_a_point is not None else None),
        "iota_a_prescreen_severity": (int(n_star_point)
                                      if n_star_point is not None else None),
        "vocabulary_frozen": True,
        "vocabulary_frozen_statement":
            "the second pass and the calibration extension pick from §7.10's "
            "frozen reserve and never author; every rung a later stage "
            "measures is on prescreen_table or admitted by a recorded batch",
        "topic_split_used": "prescreen",
        "no_composed_cells": S.NO_COMPOSED_CELLS,
    }


def run_regime_screen(tree: ModelTree, *, producing_commit: str | None = None,
                      environment_digest: str = "",
                      bank: TopicBank | None = None, device: int = 0,
                      generate: Callable[..., dict[str, Any]] | None = None,
                      caps: Sequence[int] = C.COMPLETION_CAPS,
                      rungs: Sequence[Constraint] | None = None
                      ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_REGIME,
        compute=lambda _prev: regime_payload(
            tree, producing_commit=commit, bank=bank, device=device,
            generate=generate, caps=caps, rungs=rungs),
        producing_commit=commit, environment_digest=environment_digest)
