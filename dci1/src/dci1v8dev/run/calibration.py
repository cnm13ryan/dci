"""Stage 7, ``GATE_2_CALIBRATION``: per frame --- n*(f), m*(f), ι_A(f), the
forwarded set at calibration precision on §13.2's chance basis, and one
extension round. Approach A (``dci1/docs/V8_FRAME_CONDITIONING.md``).

Two backend rounds on the 192 calibration topics at M_cal = 4, as v7's
Gate 2, each laid out over **one calibration pass per frame offset**
(``rules.calibration_frame_offsets(model_key)``): a pass renders every
calibration topic under one frame and pass p shifts the frame by
``offsets[p]``, so a topic is met under one frame per pass and every frame
is measured on ``passes / N_WORDINGS`` of the topics, half from each §13.7
split. Nothing is pooled and no topic recurs inside a frame; what grows
with the pass count is one frame's own information.

Every model runs four passes at (0, 1, 2, 3) --- all 192 topics per frame,
96 per split, the ceiling the topic bank permits (universal since the
pre-freeze audit of 2026-09-02; two passes were the default from 2026-08-30
and a per-model raise to four existed from 2026-08-31, both recorded in
``rules``). The allocation is measurement; no admission threshold depends
on it, and this stage's record states which one produced its numbers.

1. A's grid, B's grid and the unconstrained cell (``grid-A``, ``grid-B``),
   on every block of every pass; every block is rendered under one frame
   (``block.index % N_WORDINGS``), so each frame holds its share of the
   topics of every cell. **Per frame**, §12.3 fixes n*(f) and m*(f) on that
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
from dci1v7.verifiers.constraints import RESERVES, Constraint

from dci1v4.models.registry import get_model
from dci1v8dev import rules as R
from dci1v8dev.prescreen.evidence import counts_to_input
from dci1v8dev.prescreen.extension import ExtensionRule, calibration_extension_plan
from dci1v8dev.prescreen.policy import (TARGET_CALIBRATION, ForwardingPlan,
                                        FrameAwarePolicy)
from dci1v8dev.prescreen.retention import RetentionConfig
from dci1v8dev.prescreen.screen import (ScreenConfig, coordinate_target,
                                        screen_families)
from dci1v8dev.run import FRAME_DOCUMENT
from dci1v8dev.run.seeds import screen_seed
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree
from dci1v8dev.run import wording as W
from dci1v8dev.run.execute import (UNCONSTRAINED_ARM, Block, SoloCell, blocks,
                                   cell_rates, generate_and_score,
                                   instance_rates, per_topic_compliance,
                                   prompt_cell, resolve_generate,
                                   row_accounting, rows_of_frame)
from dci1v8dev.run.lifecycle import (StageOutcome, TerminalStatus,
                                     protocol_identity, run_stage)
from dci1v8dev.run.regime import screen_responder
from dci1v8dev.run.topic_replicate import bank_for

__all__ = ["gate2_payload", "run_gate2", "constraints_from_labels",
           "assert_synthetic_only", "reach_input", "frame_curves",
           "frame_target", "frame_forwarding", "FORWARDING_RULE",
           "extension_instances", "calibration_blocks",
           "calibration_allocation", "assert_allocation_realised",
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
    "calibration_allocation": "rules.calibration_frame_offsets(model_key): "
                              "Gate 2 lays each of its runs out over one pass "
                              "per frame offset, so a frame's table is "
                              "measured on one distinct topic per pass; the "
                              "passes add information inside a frame and pool "
                              "no frame with another. This run's realised "
                              "numbers are the calibration_allocation block "
                              "on this record, not a constant repeated here",
    "primary": "per frame: n*(f), m*(f), iota_A(f) with kappa_A(f) on the "
               "frame's own unconstrained cells; the forwarded set decided "
               "against iota_A(f) from the frame's own screen evidence "
               "(FORWARDING_RULE) and measured on the frame's own blocks; "
               "§13.11's table on the frame's own rows, kappa(R|B) at m*(f) "
               "on the frame's own B-solo cell, the extension reach at "
               "iota_A(f)",
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


def extension_instances(candidates: Sequence[Constraint],
                        spectrum_families: Sequence[str]
                        ) -> list[Constraint]:
    """Every reserve rung the calibration extension could pick, declared as a
    scored instance on the grid runs.

    **The defect this exists for** (pilot r4, 2026-08-30): the extension
    round measures a reserve rung's *solo* cell, but §13.2's chance column
    and §13.6's kappa(R|B) are read on cells generated earlier --- the grid
    runs' unconstrained cells and their B-solo cells --- where a rung is
    counted only if it was declared an instance when those rows were scored.
    The round-0 candidates are declared there (``non_outcome``); the
    extension's rungs did not exist yet, so on the first replication to reach
    the round the producer refused (``kappa_c for MK6:9 ... has no
    unconstrained cell to be measured in``) --- and had it not, kappa(R|B)
    would have been ``None`` and §13.6 admits no candidate whose interaction
    quantity is missing, so every extension rung would have been inadmissible
    by construction and the round scientifically inert.

    Declaring them costs **no generation**: an instance is a scoring
    obligation on rows that are generated anyway (§9.1 scores every carried
    candidate as absent wherever it is not stated), which is the same reason
    the kappa(R|B) column at every admissible severity is free. The set is
    the frozen reserve (§7.10) of every spectrum-candidate family, minus the
    severities already carried --- a superset of what
    ``extension.calibration_extension_plan`` can pick, computed before any
    calibration value exists so that no measurement decides it.
    """
    carried = {(c.kind, c.severity) for c in candidates}
    out: list[Constraint] = []
    for kind in sorted(set(spectrum_families)):
        if kind not in RESERVES:
            continue
        for q in RESERVES[kind]:
            if (kind, q) not in carried:
                out.append(Constraint(kind, q, reserve=True))
    return out


def calibration_blocks(topics: Sequence[Mapping[str, Any]], prefix: str, *,
                       model_key: str | None = None) -> list[Block]:
    """Gate 2's blocks: one pass over ``topics`` per frame offset.

    ``rules.calibration_frame_offsets(model_key)`` names the passes. Pass p
    is laid out
    at a block index base that is (a) past every earlier pass's indices, so
    the block ids and the row identities are disjoint, and (b) congruent to
    the pass's offset modulo ``N_WORDINGS``, so the topic at position i is
    met under frame ``(i + offset_p) % N_WORDINGS`` and the invariant every
    reader relies on --- ``frame = block_index % N_WORDINGS``
    (``execute.frame_of_block``) --- keeps holding on every row.

    At the default offsets (0, 2) each of the 192 calibration topics is met
    under two frames and each frame is measured on 96 distinct topics, 48
    from each §13.7 split. At ``qwen3-4b``'s four offsets (0, 1, 2, 3) every
    topic is met under every frame and each frame is measured on all 192, 96
    per split --- the ceiling, since a fifth pass would have to repeat an
    offset. No topic recurs within a frame at either value: the offsets are
    distinct modulo ``N_WORDINGS`` (asserted in ``rules``), so a frame's
    per-topic vector has one entry per topic and its length is the number
    the standard error is formed at.
    """
    out: list[Block] = []
    cursor = 0
    for offset in R.calibration_frame_offsets(model_key):
        cursor += (offset - cursor) % C.N_WORDINGS
        out.extend(blocks(topics, prefix, index_base=cursor))
        cursor += len(topics)
    return out


def calibration_allocation(topics: Sequence[Mapping[str, Any]], *,
                           model_key: str | None = None) -> dict[str, Any]:
    """What Gate 2 measures each frame on, as a record block.

    Model-scoped: ``rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL`` overrides the
    default for the models whose allocation the researcher has raised, and
    the record says which value this run used and whether it was the
    default. Nothing about *admission* varies with it.
    """
    n = len(topics)
    offsets = R.calibration_frame_offsets(model_key)
    passes = len(offsets)
    per_frame = n * passes // C.N_WORDINGS
    return {
        "model_key": model_key,
        "frame_offsets": list(offsets),
        "passes": passes,
        "is_default_allocation": offsets == R.CALIBRATION_FRAME_OFFSETS,
        "default_frame_offsets": list(R.CALIBRATION_FRAME_OFFSETS),
        "calibration_topics": n,
        "blocks_per_run": n * passes,
        "topics_per_frame": per_frame,
        "topics_per_frame_per_split": per_frame // 2,
        "at_topic_ceiling": per_frame == n,
        "max_passes": C.N_WORDINGS,
        "draws": C.M_CAL,
        "generations_per_rung": n * C.M_CAL * passes,
        "rule": "a calibration pass renders every calibration topic under "
                "one frame; pass p offsets the frame by frame_offsets[p]. "
                "The offsets are distinct modulo N_WORDINGS, so every frame "
                "is measured on passes/N_WORDINGS of the calibration topics, "
                "no topic recurs within a frame, and each frame's own "
                "information grows with the pass count at proportional "
                "Gate-2 generation. No frame is pooled with another "
                "(rules.calibration_frame_offsets)",
        "amendment": "CHANGES_SCIENTIFIC.md 2026-09-02 (pre-freeze audit): "
                     "four passes, 192 topics per frame, universal for every "
                     "model (rules.CALIBRATION_POLICY); supersedes the two "
                     "passes of 2026-08-30 and the per-model raise of "
                     "2026-08-31. No threshold moved at any step.",
    }


def assert_allocation_realised(rows_by_frame: Mapping[int, Sequence[Mapping[str, Any]]],
                               *, expected_topics_per_frame: int, where: str
                               ) -> dict[str, Any]:
    """The allocation as *measured on the rows that exist*, refused if it is
    not the design's: every frame on the intended number of **distinct**
    topics (a repeated topic would count twice and inflate the per-topic
    vector the standard error is formed at, so the distinct count is what is
    checked), balanced over §13.7's two splits.

    An allocation that is asserted only in the plan is an allocation nobody
    checked; this runs on the generated rows, on the mandatory path.
    """
    realised: dict[str, Any] = {}
    for frame, rows in sorted(rows_by_frame.items()):
        by_split: dict[str, set[str]] = {}
        for row in rows:
            by_split.setdefault(str(row.get("topic_split")), set()).add(
                str(row["topic_id"]))
        topics = set().union(*by_split.values()) if by_split else set()
        counts = {s: len(v) for s, v in sorted(by_split.items())}
        realised[str(frame)] = {"n_topics": len(topics), "by_split": counts}
        if len(topics) != expected_topics_per_frame:
            raise ProtocolError(
                f"{where}: frame {frame} is measured on {len(topics)} "
                f"distinct topics and the calibration allocation is "
                f"{expected_topics_per_frame} "
                f"(rules.CALIBRATION_FRAME_OFFSETS)")
        if len(counts) != 2 or len(set(counts.values())) != 1:
            raise ProtocolError(
                f"{where}: frame {frame}'s topics are split {counts}; "
                "§13.7 compares two halves and the allocation balances them")
    return realised


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


# ---------------------------------------------------------- the forwarding
FORWARDING_RULE = (
    "per supported frame f, after the grids and before any candidate is "
    "generated: the frame's own second-pass screen evidence (its table and "
    "A-grid, every batch absorbed on its own blocks) is screened by "
    "prescreen.screen.screen_families against Gate 2's own iota_A(f) at its "
    "topic-level SE (coordinate_target), and prescreen.retention.retain "
    "forwards the frame's set with the registered budgets; the union of "
    "the frames' sets is generated once, each rung on the blocks of the "
    "frames whose evidence selected it (selected_by_frames), and each "
    "frame's §13.11 table holds its own set only. The legacy pooled "
    "comparator's extra rungs are generated on every supported frame's "
    "blocks and kept in comparator_rows, never in a frame's table "
    "(rules.RETENTION_POLICY, RETENTION_TARGET_BASIS, RETENTION_COMPARATOR)")


def frame_target(coordinate: Mapping[str, Any], *, frame: int, n_star: int,
                 draws: int, seed: int) -> dict[str, Any]:
    """Gate 2's ι_A(f) as a screen target: the coordinate at the topic-level
    SE of A's per-topic solo vector at n*(f) over both splits, divided by
    (1 - kappa_A(f)) --- the sampling distribution of the number every
    later caliper on this frame is measured against."""
    import math
    import statistics
    per_topic: list[float] = []
    for vec in (coordinate.get("a_per_topic_by_split") or {}).get("per_topic", {}).values():
        per_topic += [float(v) for v in vec]
    kappa = float(coordinate["kappa_a"])
    if len(per_topic) > 1 and kappa < C.CHANCE_DEGENERACY_MAX:
        se = statistics.stdev(per_topic) / math.sqrt(len(per_topic)) / (1.0 - kappa)
    else:
        se = 0.0
    target = coordinate_target(float(coordinate["iota_a"]), se, n_star=int(n_star),
                               draws=draws, seed=seed, basis=f"gate2:frame{frame}")
    target["se_iota_a"] = se
    target["n_topics_a"] = len(per_topic)
    return target


def frame_forwarding(second_pass_record: Mapping[str, Any],
                     coordinates: Mapping[int, Mapping[str, Any]], *,
                     n_stars: Mapping[int, int], model_key: str,
                     screen_config: ScreenConfig | None = None,
                     retention_config: RetentionConfig | None = None
                     ) -> tuple[ForwardingPlan, dict[int, dict[str, Any]],
                                dict[int, dict[str, Any]]]:
    """The forwarding plan of the supported frames (FORWARDING_RULE): one
    screen per frame on the frame's second-pass evidence against the
    frame's own ι_A(f), one retention per frame. Returns the plan, the
    per-frame screens and the per-frame targets."""
    config = screen_config or ScreenConfig(base_seed=screen_seed(
        get_model(model_key).model_id, S.STAGE_GATE2))
    retention = retention_config or RetentionConfig(
        generations_per_rung=R.calibration_generations_per_rung(model_key))
    tables = {int(f): counts_to_input(rows) for f, rows in
              second_pass_record["final_table_by_frame"].items()}
    screens: dict[int, dict[str, Any]] = {}
    targets: dict[int, dict[str, Any]] = {}
    n_topics: dict[int, int] = {}
    for w in sorted(coordinates):
        table, _grid = tables[w]
        targets[w] = frame_target(coordinates[w], frame=w, n_star=n_stars[w],
                                  draws=config.draws, seed=config.base_seed)
        screens[w] = screen_families(table, (), config=config, target=targets[w])
        n_topics[w] = max((r.n_topics for r in table), default=0)
    plan = FrameAwarePolicy(screen_config=config, retention_config=retention
                            ).plan_from_screens(
        screens, n_topics=n_topics, target_basis=TARGET_CALIBRATION,
        provenance={"stage": S.STAGE_GATE2, "rule": FORWARDING_RULE,
                    "targets": {str(w): {"iota_a": t["iota_a_mean"],
                                         "se_iota_a": t["se_iota_a"],
                                         "n_topics_a": t["n_topics_a"],
                                         "n_star": n_stars[w]}
                                for w, t in targets.items()}})
    return plan, screens, targets


# ------------------------------------------------------------------ the stage
def gate2_payload(tree: ModelTree, *, producing_commit: str,
                  second_pass_record: Mapping[str, Any],
                  regime_record: Mapping[str, Any],
                  bank: TopicBank | None = None, device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None,
                  topic_limit: int | None = None,
                  extension_rule: ExtensionRule | None = None
                  ) -> dict[str, Any]:
    bank = bank_for(tree.context, bank=bank)
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
    extension_rule = extension_rule or ExtensionRule()
    # The candidate population is decided below, per frame, once the
    # frames' operating points exist (FORWARDING_RULE). The comparator's
    # union and the provisional plan are read now so the reserve instances
    # can be declared on the grids before any calibration value exists.
    comparator_plan = second_pass_record.get("comparator_plan") or {}
    comparator_union = [str(x) for x in comparator_plan.get("union") or ()]
    provisional_plan = second_pass_record.get("provisional_plan") or {}
    candidate_families_possible = sorted({
        lab.rpartition(":")[0] for lab in comparator_union}
        | {lab.rpartition(":")[0] for lab in provisional_plan.get("union") or ()}
        | {k for f in (second_pass_record.get("final_table_by_frame") or {}).values()
           for k in {row["kind"] for row in f} if k not in ("A", "B")})
    grid_rows: list[dict[str, Any]] = []

    def measure_grid(kind: str, grid: Sequence[int], run_name: str) -> None:
        extended = any(q in C.FOCAL_EXTENSION for q in grid)
        slot_map = {f"{kind}{q}": Constraint(kind, q, extended=extended)
                    for q in grid}
        cells: list[Any] = []
        for block in calibration_blocks(topics, f"g2{run_name}",
                                        model_key=tree.model_key):
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
        instances = (tuple(slot_map.values())
                     + tuple(c for c in grid_instances if c.kind != kind))
        rows = generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_GATE2, cap=cap,
            device=device, run_dir=tree.backend_runs(S.STAGE_GATE2) / run_name,
            instances=instances, slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)
        grid_rows.extend(rows)

    # Every rung any policy could forward, plus every reserve rung the
    # extension could pick from any candidate family, declared as scored
    # instances on the grids: the chance column (§13.2) and kappa(R|B)
    # (§13.6) are then read on the same cells for every rung that can
    # reach a table. A scoring obligation, no generation.
    possible_labels = sorted(
        {lab for lab in comparator_union}
        | {lab for lab in provisional_plan.get("union") or ()}
        | {f"{row['kind']}:{row['severity']}"
           for f in (second_pass_record.get("final_table_by_frame") or {}).values()
           for row in f if row["kind"] not in ("A", "B")})
    possible = [c for c in constraints_from_labels(possible_labels)
                if c.kind not in ("A", "B")]
    reserve_instances = extension_instances(possible, candidate_families_possible)
    grid_instances = list(possible) + list(reserve_instances)
    grids = {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID)}
    for kind, grid in grids.items():
        measure_grid(kind, grid, f"grid-{kind}")

    # ---------------------------------------- §12.3 / §12.4, per frame
    frame_grid_rows = {w: rows_of_frame(grid_rows, w) for w in S.FRAMES}
    allocation = calibration_allocation(topics, model_key=tree.model_key)
    allocation["realised"] = {"grids": assert_allocation_realised(
        frame_grid_rows, expected_topics_per_frame=allocation["topics_per_frame"],
        where=f"{S.STAGE_GATE2}: the grids")}
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

    # ------------------------- the forwarding, per frame, against iota_A(f)
    m_stars = sorted({int(points[w]["m_star"]) for w in supported})
    b_stars = tuple(focal_constraint(m) for m in m_stars)
    prescreen_by_candidate = {
        row["candidate"]: row
        for row in (regime_record.get("difficulty_table") or ())
        if not row.get("is_outcome")}
    coordinates = {w: frame_a_coordinate(frame_grid_rows[w],
                                         n_star=int(points[w]["n_star"]),
                                         curves=points[w]["curves"],
                                         pooled_grid_rows=grid_rows)
                   for w in supported}
    forwarding, forwarding_screens, forwarding_targets = frame_forwarding(
        second_pass_record, coordinates,
        n_stars={w: int(points[w]["n_star"]) for w in supported},
        model_key=tree.model_key)
    cands_by_frame = {w: [c for c in constraints_from_labels(forwarding.forwarded(w))
                          if c.kind not in ("A", "B")] for w in supported}
    # The comparator arms: the legacy pooled set (one set for every frame)
    # and the provisional frame-aware set against the screen-proxy target
    # (per frame). Their rungs beyond the frame's own set are generated on
    # the frame's blocks and kept in comparator_rows, so Gate 3 can state
    # every policy's identification on the same calibration rows.
    comparator_sets = {w: {
        R.RETENTION_COMPARATOR: sorted(comparator_union),
        "frame_aware_screen_proxy": sorted(
            ((provisional_plan.get("by_frame") or {}).get(str(w)) or {}
             ).get("forwarded") or ())} for w in supported}
    comparator_extra = {w: [c for c in constraints_from_labels(sorted(
        set().union(*comparator_sets[w].values()) - set(forwarding.forwarded(w))))
        if c.kind not in ("A", "B")] for w in supported}

    def measure_candidates(by_frame_cands: Mapping[int, Sequence[Constraint]],
                           run_name: str) -> list[dict[str, Any]]:
        """One backend run: on every block of every pass, the solo cells of
        the rungs the block's frame carries in ``by_frame_cands``; every
        rung of the run scored absent on every cell (§9.1), B at every
        supported frame's m*(f) likewise."""
        union = {c.label: c for cs in by_frame_cands.values() for c in cs}
        if not union:
            return []
        ordered = [union[k] for k in sorted(union)]
        slot_map = {f"S{i}": c for i, c in enumerate(ordered)}
        slot_of = {c.label: slot for slot, c in slot_map.items()}
        cells = []
        for block in calibration_blocks(topics, f"g2{run_name}",
                                        model_key=tree.model_key):
            for rung in by_frame_cands.get(block.index % C.N_WORDINGS, ()):
                cells.append(SoloCell(cell_id=f"solo:{rung.label}", arm="solo",
                                      block=block, slot=slot_of[rung.label],
                                      draws=C.M_CAL))
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_map,
                               topic_split=_split_of(bank, c.topic_id))
                   for c in cells]
        return generate_and_score(
            tree.model_key, prompts, stage=S.STAGE_GATE2, cap=cap,
            device=device, run_dir=tree.backend_runs(S.STAGE_GATE2) / run_name,
            instances=tuple(ordered) + b_stars, slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)

    def _rows_of(rows: Sequence[Mapping[str, Any]], cands: Sequence[Constraint]
                 ) -> list[dict[str, Any]]:
        labels = {f"solo:{c.label}" for c in cands}
        return [dict(r) for r in rows if r.get("cell_id") in labels]

    generated_by_frame = {w: list(cands_by_frame[w]) + list(comparator_extra[w])
                          for w in supported}
    candidate_rows = measure_candidates(generated_by_frame, "candidates")
    frame_candidate_rows = {w: _rows_of(rows_of_frame(candidate_rows, w),
                                        cands_by_frame[w]) for w in supported}
    frame_comparator_rows = {w: _rows_of(rows_of_frame(candidate_rows, w),
                                         comparator_extra[w]) for w in supported}
    if any(cands_by_frame[w] for w in supported):
        allocation["realised"]["candidates"] = assert_allocation_realised(
            {w: r for w, r in frame_candidate_rows.items() if cands_by_frame[w]},
            expected_topics_per_frame=allocation["topics_per_frame"],
            where=f"{S.STAGE_GATE2}: the candidate run")
    if any(comparator_extra[w] for w in supported):
        allocation["realised"]["comparator"] = assert_allocation_realised(
            {w: r for w, r in frame_comparator_rows.items() if comparator_extra[w]},
            expected_topics_per_frame=allocation["topics_per_frame"],
            where=f"{S.STAGE_GATE2}: the comparator arm")

    # ------------------------------------------ §13.11 per frame, round 0
    by_frame: dict[int, dict[str, Any]] = {}
    for w in supported:
        by_frame[w] = supported_frame_block(
            w, points[w], frame_grid_rows=frame_grid_rows[w],
            frame_candidate_rows=frame_candidate_rows[w],
            candidates=cands_by_frame[w], model_key=tree.model_key,
            prescreen=prescreen_by_candidate, pooled_grid_rows=grid_rows)
        # The comparator arm: the legacy pooled set's extra rungs, tabled on
        # the same basis and kept beside the frame's table, never in it.
        if comparator_extra[w]:
            kappa_cmp = _kappa_columns(frame_grid_rows[w], list(comparator_extra[w]),
                                       severities=[int(points[w]["m_star"])],
                                       model_key=tree.model_key)
            kept_c, withheld_c, _m = frame_tables(
                frame_grid_rows[w], candidate_rows=frame_comparator_rows[w],
                candidates=comparator_extra[w], m_star=int(points[w]["m_star"]),
                model_key=tree.model_key, prescreen=prescreen_by_candidate,
                kappa_column=kappa_cmp[str(int(points[w]["m_star"]))])
        else:
            kept_c, withheld_c = ({s: [] for s in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")},
                                  {})
        by_frame[w]["comparator_rows"] = kept_c
        by_frame[w]["comparator_rows_withheld"] = withheld_c
        by_frame[w]["comparator"] = {
            "policies": comparator_sets[w],
            "extra_labels": [c.label for c in comparator_extra[w]],
            "n_extra": len(comparator_extra[w]),
            "standing": "measured beside the frame's table for the "
                        "retention comparison (Gate 3 comparator block); "
                        "enters no admission, selection or membership"}
        by_frame[w]["forwarding"] = {
            "forwarded": forwarding.forwarded(w),
            "n_forwarded": len(forwarding.forwarded(w)),
            "spectrum_families": forwarding.spectrum_families(w),
            "local_families": list(forwarding.by_frame[str(w)]["retention"]["local_families"]),
            "target": {"iota_a": forwarding_targets[w]["iota_a_mean"],
                       "se_iota_a": forwarding_targets[w]["se_iota_a"],
                       "n_topics_a": forwarding_targets[w]["n_topics_a"],
                       "basis": TARGET_CALIBRATION},
            "screen_statuses": forwarding.by_frame[str(w)]["screen_statuses"],
            "screen_labels": forwarding.by_frame[str(w)]["screen_labels"],
            "n_rows": {"candidates": _n_rows(frame_candidate_rows[w]),
                       "comparator": _n_rows(frame_comparator_rows[w])}}

    # ---------------------------------------------- the extension round
    reach_by_frame: dict[int, dict[str, Any]] = {}
    plan_by_frame: dict[int, dict[str, Any]] = {}
    picks_by_frame: dict[int, list[Constraint]] = {}
    for w in supported:
        reach = reach_input(by_frame[w]["calibration_rows"]["pooled"],
                            spectrum_families=forwarding.spectrum_families(w),
                            iota_a=by_frame[w]["iota_a"], rule=extension_rule)
        for split_rows in by_frame[w]["calibration_rows_withheld"].values():
            for row in split_rows:
                if row["kind"] in reach:
                    reach[row["kind"]]["measured"] = sorted(
                        set(reach[row["kind"]]["measured"]) | {int(row["severity"])})
        plan = calibration_extension_plan(reach, rule=extension_rule)
        reach_by_frame[w], plan_by_frame[w] = reach, plan
        picks_by_frame[w] = constraints_from_labels(
            [f"{k}:{q}" for k, qs in sorted(plan["picks"].items()) for q in sorted(qs)])
    extension_labels = sorted({c.label for cs in picks_by_frame.values() for c in cs})
    extension_rows: list[dict[str, Any]] = []
    extension_withheld_by_frame: dict[int, dict[str, list[str]]] = {}
    if extension_labels:
        # each frame's picks on that frame's blocks (a rung measured for
        # one frame is that frame's data)
        extension_rows = measure_candidates(picks_by_frame, "extension-1")
        allocation["realised"]["extension"] = assert_allocation_realised(
            {w: rows_of_frame(extension_rows, w) for w in supported
             if picks_by_frame[w]},
            expected_topics_per_frame=allocation["topics_per_frame"],
            where=f"{S.STAGE_GATE2}: the extension round")
        for w in supported:
            if not picks_by_frame[w]:
                continue
            ext_rows_w = rows_of_frame(extension_rows, w)
            # kappa(R|B) for the new rungs: not scored absent on the grid's
            # B-solo cells (they did not exist then), so the column is
            # measured on the frame's B-solo rows by the per-candidate
            # path (`kappa_column=None`).
            kept, withheld, _measured = frame_tables(
                frame_grid_rows[w],
                candidate_rows=frame_candidate_rows[w] + ext_rows_w,
                candidates=picks_by_frame[w], m_star=by_frame[w]["m_star"],
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
        by_frame[w]["extension_measured"] = [c.label for c in picks_by_frame[w]]
        by_frame[w]["extension_withheld"] = extension_withheld_by_frame.get(w, {})
        by_frame[w]["kappa_b_under_candidate"] = _kappa_b_under_candidate(
            frame_candidate_rows[w] + rows_of_frame(extension_rows, w),
            m_star=by_frame[w]["m_star"], model_key=tree.model_key)
    for w in failures:
        by_frame[w] = unsupported_frame_block(
            w, points[w], frame_grid_rows=frame_grid_rows[w],
            frame_candidate_rows=rows_of_frame(candidate_rows, w))
    union_forwarded = list(forwarding.union)
    provisional_agreement = {}
    for w in supported:
        prov = set((provisional_plan.get("by_frame") or {}).get(str(w), {}).get("forwarded") or ())
        final = set(forwarding.forwarded(w))
        provisional_agreement[str(w)] = {
            "jaccard": (len(prov & final) / len(prov | final)) if (prov | final) else None,
            "n_provisional": len(prov), "n_final": len(final),
            "only_provisional": sorted(prov - final),
            "only_final": sorted(final - prov)}

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
                                   "n_forwarded_provisional":
                                       len(provisional_plan.get("union") or ())},
                   "regime": {"stage": S.STAGE_REGIME, "cap": cap}},
        "producing_commit": producing_commit,
        "frame_conditioning": FRAME_CONDITIONING_STATEMENT,
        "frames": list(S.FRAMES),
        "supported_frames": supported,
        "unsupported_frames": {str(w): f for w, f in failures.items()},
        "by_frame": {str(w): by_frame[w] for w in S.FRAMES},
        "descriptive_pooled": descriptive_pooled,
        "calibration_allocation": allocation,
        "grids": {"A": list(C.TARGET_GRID), "B": list(C.FOCAL_GRID),
                  "B_extension": list(C.FOCAL_EXTENSION),
                  "focal_extension_measured": extension_measured,
                  "draws": C.M_CAL, "n_topics": len(by_id),
                  "topics_per_frame": {str(w): len({r["topic_id"] for r in
                                                    frame_grid_rows[w]})
                                       for w in S.FRAMES},
                  "blocks_per_frame": {str(w): len({r["block_id"] for r in
                                                    frame_grid_rows[w]})
                                       for w in S.FRAMES},
                  "blocks_per_frame_reading": "block ids, summed over the "
                  "grid runs and the calibration passes; topics_per_frame "
                  "is the number a per-frame rate and its SE are formed at"},
        "construct_floor": {"applied": False,
                            "why": "§34 D17's floor selects a confirmatory "
                                   "operating point; the pilot selects none "
                                   "and reads m*(f) only for kappa(R|B)"},
        "calibration_population": {
            "policy": R.RETENTION_POLICY,
            "target_basis": TARGET_CALIBRATION,
            "comparator": R.RETENTION_COMPARATOR,
            "forwarded": union_forwarded,
            "n_measured": len(union_forwarded),
            "by_frame": {str(w): {"forwarded": forwarding.forwarded(w),
                                  "n_forwarded": len(forwarding.forwarded(w)),
                                  "spectrum_families": forwarding.spectrum_families(w),
                                  "comparator_extra": [c.label for c in comparator_extra[w]]}
                         for w in supported},
            "selected_by_frames": {k: list(v) for k, v in
                                   sorted(forwarding.selected_by_frames.items())},
            "forwarding_plan": forwarding.as_record(),
            "provisional_agreement": provisional_agreement,
            "comparator_union": comparator_union,
            "n_comparator_union": len(comparator_union),
            "comparator_policies": [R.RETENTION_COMPARATOR, "frame_aware_screen_proxy"],
            "n_candidate_rows": sum(len(r) for r in frame_candidate_rows.values()),
            "n_comparator_rows": sum(len(r) for r in frame_comparator_rows.values()),
            "unsupported_frames_generate_nothing": True,
            "measured_under_every_frame": False,
            "rule": FORWARDING_RULE},
        "b_instances_scored_absent_on_candidate_cells": [b.label for b in b_stars],
        "reserve_instances_declared_on_the_grids": {
            "labels": [c.label for c in reserve_instances],
            "n": len(reserve_instances),
            "families": sorted({c.kind for c in reserve_instances}),
            "candidate_instances": [c.label for c in possible],
            "rule": "every rung any policy could forward (the provisional "
                    "and comparator unions and every rung on the frames' "
                    "second-pass tables) and §7.10's frozen reserve of every "
                    "candidate family, minus the carried severities: scored "
                    "as absent instances on the grids' unconstrained and "
                    "B-solo cells so that the chance column (§13.2) and "
                    "kappa(R|B) (§13.6) of whatever the per-frame forwarding "
                    "and the extension then measure are read on the same "
                    "cells as every other candidate's; costs no generation",
        },
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
                      "measured_by_frame": {str(w): [c.label for c in cs]
                                            for w, cs in picks_by_frame.items()},
                      "measured_rule": "each supported frame's own plan, "
                                       "bounded by the rule, measured on that "
                                       "frame's blocks only",
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
        "n_candidates_measured": len(union_forwarded) + len(extension_labels),
        "n_candidates_measured_by_frame": {
            str(w): len(cands_by_frame[w]) + len(picks_by_frame[w]) for w in supported},
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
