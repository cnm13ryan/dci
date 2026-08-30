"""Stage 5, ``SECOND_PASS_SCREEN``: the targeted second pass, generated.

``dci1v8dev.prescreen.rescreen.run_rescreen`` decides *what* a batch
measures --- every family the first pass left in the middle band, its
measured rungs plus at most two reserve severities in the deficient
direction, A's grid --- and this stage supplies ``measure``: it renders the
batch's cells under the v8 frames on a fresh set of twenty-four topics,
generates them at the selected cap, scores them, and returns the counts in
the screen's schema with the chance count read on the batch's own
unconstrained cell. The loop stops by the registered rule (a family leaves
the middle band or spends three batches; the posterior majority resolves
what is left, recorded ``AMBIGUOUS_AT_MAX``), then ``retain`` forwards the
spaced set by role.

The topics come from Calibration-A, two per area per batch, disjoint across
batches (``stages.RESCREEN_TOPIC_SOURCE``); the ids are on the record.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v4.models.registry import get_model
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import TopicBank, load_bank
from dci1v7.verifiers.constraints import LADDERS, Constraint

from dci1v8dev.prescreen.rescreen import (RescreenBatch, RescreenConfig,
                                          run_rescreen)
from dci1v8dev.prescreen.retention import RetentionConfig, retain
from dci1v8dev.prescreen.schema import ARung, PrescreenRung
from dci1v8dev.prescreen.screen import ScreenConfig
from dci1v8dev.run import stages as S
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run.execute import generate_and_score, prompt_cell, resolve_generate
from dci1v8dev.run.instrument import frame_reliability
from dci1v8dev.run.lifecycle import StageOutcome, protocol_identity, run_stage
from dci1v8dev.run.regime import (jsonable, ladder_cells, prescreen_counts,
                                  prescreen_input, screen_record,
                                  screen_responder)
from dci1v8dev.run.seeds import screen_seed

__all__ = ["batch_topics", "measure_factory", "second_pass_payload",
           "run_second_pass"]


def batch_topics(bank: TopicBank, index: int) -> list[dict[str, Any]]:
    """Batch ``index``'s topics: per area, the next two of Calibration-A in
    topic-id order. Disjoint across batches; refuses past the source."""
    per = S.RESCREEN_TOPICS_PER_AREA
    out: list[dict[str, Any]] = []
    source = bank.topics(S.RESCREEN_TOPIC_SOURCE)
    for area in C.SUBJECT_AREAS:
        members = sorted((t for t in source if t["area"] == area),
                         key=lambda t: t["topic_id"])
        chosen = members[index * per:(index + 1) * per]
        if len(chosen) != per:
            raise ProtocolError(
                f"batch {index}: {S.RESCREEN_TOPIC_SOURCE} holds no {per} "
                f"unused topics for {area!r}")
        out.extend(chosen)
    return out


def measure_factory(tree: ModelTree, *, bank: TopicBank, cap: int,
                    device: int, generate: Callable[..., Any] | None,
                    log: list[dict[str, Any]]):
    identity = protocol_identity(tree, S.STAGE_SECOND_PASS)

    def measure(batch: RescreenBatch) -> tuple[list[PrescreenRung], list[ARung]]:
        topics = batch_topics(bank, batch.index)
        by_id = {t["topic_id"]: t for t in topics}
        rungs: list[Constraint] = []
        for kind, fam in sorted(batch.families.items()):
            for q in sorted(set(fam["severities"]) | set(fam["reserve_picks"])):
                rungs.append(Constraint(kind, q, reserve=True))
        if batch.a_grid:
            rungs.extend(Constraint("A", q) for q in C.TARGET_GRID)
        if batch.layout != "topics":
            raise ProtocolError("the pilot's second pass measures fresh "
                                "topics; the draws layout is not wired")
        cells, slot_map = ladder_cells(topics, rungs,
                                       prefix=f"batch{batch.index}",
                                       draws=batch.draws_per_topic)
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_map,
                               topic_split=S.RESCREEN_TOPIC_SOURCE)
                   for c in cells]
        rows = generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_SECOND_PASS, cap=cap,
            device=device,
            run_dir=tree.backend_runs(S.STAGE_SECOND_PASS)
            / f"batch-{batch.index}",
            instances=tuple(slot_map.values()), slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)
        counts = prescreen_counts(rows, rungs)
        for row in counts:
            row["reserve"] = (row["kind"] not in ("A", "B")
                              and row["severity"] not in LADDERS[row["kind"]])
        new_rungs, new_a = prescreen_input(counts)
        log.append({"index": batch.index,
                    "topic_ids": sorted(by_id),
                    "families": sorted(batch.families),
                    "rungs": [r.label for r in rungs],
                    "n_rows": len(rows),
                    "frame_reliability": frame_reliability(rows),
                    "counts": counts})
        return new_rungs, new_a

    return measure


def second_pass_payload(tree: ModelTree, *, producing_commit: str,
                        regime_record: Mapping[str, Any],
                        bank: TopicBank | None = None, device: int = 0,
                        generate: Callable[..., Any] | None = None,
                        rescreen_config: RescreenConfig | None = None,
                        retention_config: RetentionConfig | None = None
                        ) -> dict[str, Any]:
    bank = bank if bank is not None else load_bank()
    generate = resolve_generate(tree, generate, screen_responder,
                                where=S.STAGE_SECOND_PASS)
    cap = int(regime_record["selected_cap"])
    table, a_grid = prescreen_input(regime_record["prescreen_table"])
    config = ScreenConfig(base_seed=screen_seed(
        get_model(tree.model_key).model_id, S.STAGE_SECOND_PASS))
    rescreen_config = rescreen_config or RescreenConfig()
    retention_config = retention_config or RetentionConfig()
    batches: list[dict[str, Any]] = []
    result = run_rescreen(
        table, a_grid, screen_config=config, config=rescreen_config,
        measure=measure_factory(tree, bank=bank, cap=cap, device=device,
                                generate=generate, log=batches))
    retention = retain(result["screen"], config=retention_config)
    forwarded = [e["candidate"] for e in retention["forwarded"]]
    pooled_rows_reliability = _pooled_reliability(batches)
    return {
        "stage": S.STAGE_SECOND_PASS,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_SECOND_PASS],
        "outcome": "PASS",
        "inputs": {"regime": {"stage": S.STAGE_REGIME, "cap": cap}},
        "producing_commit": producing_commit,
        "selected_cap": cap,
        "topic_source": S.RESCREEN_TOPIC_SOURCE,
        "topics_per_area_per_batch": S.RESCREEN_TOPICS_PER_AREA,
        "batches": [{k: v for k, v in b.items() if k != "counts"}
                    for b in batches],
        "batch_counts": {str(b["index"]): b["counts"] for b in batches},
        "n_batches": len(batches),
        "batches_used": result["batches_used"],
        "resolved_at_max": result["resolved_at_max"],
        "history": jsonable(result["history"]),
        "cost_generations": result["cost_generations"],
        "rescreen_config": result["config"],
        "final_table": [_rung_dict(r) for r in result["table"]],
        "final_a_grid": [_a_dict(a) for a in result["a_grid"]],
        "screen": screen_record(result["screen"]),
        "screen_statuses": jsonable(result["screen"]["statuses"]),
        "screen_labels": jsonable(result["screen"]["labels"]),
        "retention": jsonable(retention),
        "forwarded_set": forwarded,
        "n_forwarded": len(forwarded),
        "frame_reliability": pooled_rows_reliability,
        "calibration_cost_generations": retention["calibration_cost_generations"],
        "vocabulary_frozen": True,
    }


def _pooled_reliability(batches: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The batches' frame reliabilities pooled by counts (the rows are
    already reduced; recomputing from them is the same statistic)."""
    by_frame: dict[str, dict[str, Any]] = {}
    for b in batches:
        for w, e in b["frame_reliability"]["by_frame"].items():
            acc = by_frame.setdefault(w, {"n_rows": 0, "marker_absent": 0,
                                          "by_family": {}})
            acc["n_rows"] += e["n_rows"]
            acc["marker_absent"] += e["marker_absent"]
            for fam, fe in e["by_family"].items():
                f = acc["by_family"].setdefault(fam, {"n_rows": 0,
                                                      "marker_absent": 0})
                f["n_rows"] += fe["n_rows"]
                f["marker_absent"] += fe["marker_absent"]
    for w in ("0", "1", "2", "3"):
        by_frame.setdefault(w, {"n_rows": 0, "marker_absent": 0,
                                "by_family": {}})
    total_n = sum(e["n_rows"] for e in by_frame.values())
    total_a = sum(e["marker_absent"] for e in by_frame.values())
    return {"by_frame": {w: {**e, "share": (e["marker_absent"] / e["n_rows"])
                             if e["n_rows"] else None,
                             "by_family": {k: {**v, "share":
                                               (v["marker_absent"] / v["n_rows"])
                                               if v["n_rows"] else None}
                                           for k, v in e["by_family"].items()}}
                         for w, e in sorted(by_frame.items())},
            "pooled": {"n_rows": total_n, "marker_absent": total_a,
                       "share": (total_a / total_n) if total_n else None},
            "families": sorted({k for e in by_frame.values()
                                for k in e["by_family"]}),
            "statistic": "share of A and MK1-8 load-1 rows whose marker "
                         "statistic is 0, per wording index (second pass)"}


def _rung_dict(r: PrescreenRung) -> dict[str, Any]:
    return {"kind": r.kind, "severity": r.severity, "solo_k": r.solo_k,
            "solo_n": r.solo_n, "chance_k": r.chance_k, "chance_n": r.chance_n,
            "vacuous_k": r.vacuous_k, "n_topics": r.n_topics,
            "draws_per_topic": r.draws_per_topic, "reserve": r.reserve}


def _a_dict(a: ARung) -> dict[str, Any]:
    return {"severity": a.severity, "solo_k": a.solo_k, "solo_n": a.solo_n,
            "chance_k": a.chance_k, "chance_n": a.chance_n,
            "n_topics": a.n_topics, "draws_per_topic": a.draws_per_topic}


def run_second_pass(tree: ModelTree, *, producing_commit: str | None = None,
                    environment_digest: str = "",
                    bank: TopicBank | None = None, device: int = 0,
                    generate: Callable[..., Any] | None = None
                    ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return run_stage(
        tree, S.STAGE_SECOND_PASS,
        compute=lambda previous: second_pass_payload(
            tree, producing_commit=commit, regime_record=previous, bank=bank,
            device=device, generate=generate),
        producing_commit=commit, environment_digest=environment_digest)
