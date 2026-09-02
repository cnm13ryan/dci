"""Stage 2, ``LOCAL_TOPUP``: the frame-aware rung top-up, by a stated rule.

**The mechanism it tests** (audit of 2026-09-01, `V8_CONFIRMATORY.md`
§3). The pilot's screen and second pass rank and forward rungs by a
difficulty **pooled over the four frames**, while every later step is
frame-specific; the cross-frame spread of a rung's iota is 1.7-2.7x the
0.10 caliper, so a rung that sits inside frame f's caliper can be left
unmeasured because its pooled coordinate sits elsewhere. §13.15 needs five
LOCAL-valid families per frame, and several frames end one family short.

**The rule (prospective, symmetric over every model and frame).** For each
frame f that Gate 2 supported, with V(f) the LOCAL-valid families on f and
need(f) = max(0, 5 - |V(f)|): a candidate rung is any Tier-1/2 rung the
first-pass screen measured under f whose frame-f screen iota lies inside
[iota_A(f) - 0.10, iota_A(f) + 0.10], whose family is not in V(f), and
which the pilot did not forward to calibration. The top-up runs on f iff
need(f) >= 1 and the candidate families number at least need(f) --- i.e.
iff measuring them *could* close the gap. Every candidate rung is then
measured on f's own calibration topics at M_cal draws (the same blocks,
splits and draws as the pilot's table), the frame's stored load-0 and
B-solo answers are re-scored for the new instances (scoring is a pure
function of stored text; the verifier hash is asserted unchanged), the
§13.11 producer forms the rows, and Gate 3 is **re-verdicted for every
supported frame** of the model by the pilot's own kernel on the augmented
table --- frames with no top-up reproduce the pilot's verdicts exactly, and
that equality is asserted.

What it is not: no threshold, caliper, operating point, validity component
or frame moves; nothing is read from a composed cell (none exists); the
rule never *adds* a family --- it measures one the frame-blind budget left
out, and §13's full V(R) then admits it or does not.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.run.gates_run import (_calibration_rows, _kappa_columns,
                                  _withhold_degenerate)
from dci1v7.stages.selection import FAMILIES
from dci1v7.verifiers.constraints import Constraint

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.design import Cell
from dci1v8dev.confirm.execute import (generate_and_score, prompt_cell,
                                       resolve_generate)
from dci1v8dev.confirm.pilot_import import PilotSource, open_pilot
from dci1v8dev.run import eligibility as EL
from dci1v8dev.run import references as REF
from dci1v8dev.run import stages as PS
from dci1v8dev.run.execute import frame_of_block, rows_of_frame
from dci1v8dev.verifiers import verifier_source_hash
from dci1v8dev.verifiers.compliance import score_generation

__all__ = ["TOPUP_RULE", "topup_plan", "rescore_absent", "augment_gate2",
           "reverdict_gate3", "topup_payload", "run_topup"]

TOPUP_RULE = (
    "per supported frame f: need(f) = max(0, MIN_LOCAL_FAMILIES - |LOCAL-"
    "valid families on f|); candidates = Tier-1/2 rungs measured by the "
    "first-pass screen under f with frame-f screen iota inside "
    "iota_A(f) +/- REFERENCE_CALIPER, from families not LOCAL-valid on f, "
    "not forwarded to calibration; the top-up measures every candidate rung "
    "on f's own calibration topics at M_cal iff need(f) >= 1 and the "
    "candidate families >= need(f); Gate 3 is re-verdicted on the augmented "
    "table by the pilot's kernel for every supported frame")


def _label(kind: str, q: int) -> str:
    return f"{kind}:{q}"


def topup_plan(source: PilotSource) -> dict[str, Any]:
    """The rule applied to one model's pilot records. Reads solo/screen
    quantities only."""
    g1, g2, g3 = source.gate1, source.gate2, source.gate3
    fc = g1.get("frame_comparison_screen") or {}
    forwarded = set((g2.get("calibration_population") or {})
                    .get("forwarded") or [])
    caliper = C.REFERENCE_CALIPER
    plan: dict[str, Any] = {}
    for w in PS.FRAMES:
        f2 = g2["by_frame"][str(w)]
        if f2.get("status") != PS.FRAME_SUPPORTED:
            plan[str(w)] = {"frame": w, "supported": False, "runs": False,
                            "reason": "no operating point"}
            continue
        f3 = g3["by_frame"][str(w)]
        valid = set(f3["survival"]["local_valid_families"])
        need = max(0, PS.MIN_LOCAL_FAMILIES - len(valid))
        iota_a = float(f2["iota_a"])
        candidates: dict[str, list[dict[str, Any]]] = {}
        for label, entry in sorted(fc.items()):
            kind, _, q = label.rpartition(":")
            fam = FAMILIES.get(kind)
            if fam is None or fam.structural_tier not in (1, 2):
                continue
            if kind in valid or label in forwarded:
                continue
            fr = (entry.get("frames") or {}).get(str(w)) or {}
            iota = fr.get("iota")
            if iota is None or abs(float(iota) - iota_a) > caliper:
                continue
            candidates.setdefault(kind, []).append(
                {"candidate": label, "severity": int(q),
                 "screen_iota_under_frame": float(iota),
                 "screen_se_iota": fr.get("se_iota"),
                 "structural_tier": fam.structural_tier,
                 "discourse_role": fam.discourse_role})
        runs = need >= 1 and len(candidates) >= need
        plan[str(w)] = {
            "frame": w, "supported": True, "iota_a": iota_a,
            "local_valid_families": sorted(valid), "need": need,
            "candidate_families": {k: v for k, v in sorted(candidates.items())},
            "n_candidate_families": len(candidates),
            "n_candidate_rungs": sum(len(v) for v in candidates.values()),
            "runs": runs,
            "reason": ("rule met: measuring the candidates could close the "
                       "gap" if runs else
                       ("no shortfall" if need == 0 else
                        "fewer candidate families than the shortfall")),
        }
    return {"rule": TOPUP_RULE, "caliper": caliper,
            "min_local_families": PS.MIN_LOCAL_FAMILIES, "by_frame": plan,
            "frames_running": [int(w) for w, p in plan.items() if p["runs"]]}


def rescore_absent(rows: Sequence[Mapping[str, Any]],
                   instances: Sequence[Constraint]) -> list[dict[str, Any]]:
    """The stored rows with the new instances scored ABSENT on them, from
    their stored text. Scoring is deterministic; the verifier hash on every
    row must be the running one."""
    current = verifier_source_hash()
    labels = {c.label for c in instances}
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("verifier_hash") != current:
            raise ProtocolError(
                f"row {row.get('row_id')} was scored under verifier "
                f"{row.get('verifier_hash')}; the running verifier is "
                f"{current} and a mixed table is refused")
        have = {f"{s['kind']}:{s['severity']}" for s in row["scores"]}
        wanted = [c for c in instances if c.label not in have]
        new = dict(row)
        if wanted:
            scores = score_generation(row.get("raw_response") or "",
                                      present=(), absent=wanted,
                                      truncated=bool(row.get("truncated")))
            new["scores"] = list(row["scores"]) + [
                {"kind": s.kind, "severity": s.severity,
                 "slot": f"{s.kind}:{s.severity}", "statistic": s.statistic,
                 "passed": s.passed, "graded": s.graded,
                 "non_vacuous": s.non_vacuous, "vacuous_pass": s.vacuous_pass,
                 "present": False, "position": None, "configuration": None,
                 "processing_failure": s.processing_failure}
                for s in scores.scores]
        out.append(new)
    _ = labels
    return out


def _frame_blocks_from_rows(rows: Sequence[Mapping[str, Any]], frame: int
                            ) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for r in rows:
        if frame_of_block(r) != frame or r.get("arm") != "unconstrained":
            continue
        seen.setdefault(str(r["block_id"]), {
            "block_id": str(r["block_id"]),
            "block_index": int(r["block_index"]) if r.get("block_index")
            is not None else int(str(r["block_id"]).rpartition("-")[2]),
            "topic_id": r["topic_id"], "topic_split": r["topic_split"],
            "area": r.get("area")})
    return sorted(seen.values(), key=lambda b: b["block_index"])


def augment_gate2(source: PilotSource, frame: int,
                  new_solo_rows: Sequence[Mapping[str, Any]],
                  candidates: Sequence[Constraint],
                  gate2: dict[str, Any]) -> dict[str, Any]:
    """Append the new rungs' §13.11 rows to frame ``frame`` of ``gate2``
    (a deep copy is the caller's job), from the rescored grid rows."""
    f2 = gate2["by_frame"][str(frame)]
    grid = source.scored_rows(PS.STAGE_GATE2, "grid-A") + \
        source.scored_rows(PS.STAGE_GATE2, "grid-B")
    frame_grid = rescore_absent(rows_of_frame(grid, frame), candidates)
    m_star = int(f2["m_star"])
    kappa = _kappa_columns(frame_grid, list(candidates), severities=[m_star],
                           model_key=source.model_key)
    b_label = f"solo:B:{m_star}"
    # The producer's reference rule returns nothing for a candidate that
    # every solo row of the split states, so the new rows are placed beside
    # the frame's stored candidate rows exactly as the pilot placed them.
    stored_solo = rows_of_frame(source.scored_rows(PS.STAGE_GATE2, "candidates"),
                                frame)
    measured = _calibration_rows(
        source.model_key, list(candidates), m_star=m_star,
        solo_rows=list(stored_solo) + list(new_solo_rows), chance_rows=frame_grid,
        b_solo_rows=[r for r in frame_grid if r["cell_id"] == b_label],
        kappa_column=kappa[str(m_star)], prescreen={})
    kept, withheld = _withhold_degenerate(measured)
    for split, rows in kept.items():
        f2["calibration_rows"][split] = list(f2["calibration_rows"][split]) + \
            [dict(r) for r in rows]
    for split, rows in withheld.items():
        f2["calibration_rows_withheld"][split] = \
            list(f2["calibration_rows_withheld"].get(split, [])) + \
            [dict(r) for r in rows]
    for split, col in kappa[str(m_star)].items():
        f2["kappa_under_b_by_severity"][str(m_star)].setdefault(split, {})
        f2["kappa_under_b_by_severity"][str(m_star)][split].update(col)
    return {"frame": frame, "n_new_rows_kept": {s: len(r) for s, r in kept.items()},
            "n_new_rows_withheld": {s: len(r) for s, r in withheld.items()},
            "candidates": [c.label for c in candidates]}


def reverdict_gate3(source: PilotSource, gate2: Mapping[str, Any]
                    ) -> dict[str, Any]:
    """Gate 3 on the (augmented) Gate-2 record, by the pilot's own kernel,
    for every supported frame; the same seed and resamples the pilot used."""
    g3 = source.gate3
    seed, resamples = int(g3["seed"]), int(g3["resamples"])
    supported = [w for w in PS.FRAMES
                 if gate2["by_frame"][str(w)].get("status") == PS.FRAME_SUPPORTED]
    by_frame: dict[str, Any] = {}
    for w in PS.FRAMES:
        if w in supported:
            by_frame[str(w)] = REF.frame_references(
                gate2, w, model_key=source.model_key, seed=seed,
                resamples=resamples)
        else:
            by_frame[str(w)] = dict(g3["by_frame"][str(w)])
    states = {str(w): {"state": by_frame[str(w)].get("state", "UNSUPPORTED")}
              for w in PS.FRAMES}
    eligibility = EL.local_eligibility(by_frame, frames=PS.FRAMES)
    return {"by_frame": by_frame, "frame_states": states,
            "supported_frames": supported,
            "local_eligibility": eligibility, "seed": seed,
            "resamples": resamples, "kernel": "dci1v8dev.run.references."
                                               "frame_references (pilot)"}


def _survival_view(g3_frame: Mapping[str, Any]) -> dict[str, Any]:
    s = g3_frame.get("survival")
    if not s:
        return {"state": g3_frame.get("state")}
    return {"state": g3_frame.get("state"),
            "local_valid_families": list(s["local_valid_families"]),
            "n_backups": s["n_backups"],
            "core": [f"{c['family']}:{c['severity']}" for c in s["core_references"]],
            "backups": list(s["backups"]),
            "local_supported": bool(s.get("local_supported")),
            "coverage_identified": bool(s["coverage_identified"])}


def topup_payload(tree: L.ConfirmTree, registration: Mapping[str, Any], *,
                  producing_commit: str, device: int = 0,
                  generate: Callable[..., dict[str, Any]] | None = None
                  ) -> dict[str, Any]:
    source = open_pilot(Path(registration["pilot_source"]["root"]),
                        tree.model_key, synthetic=tree.synthetic)
    if source.as_record()["record_hashes"] != \
            registration["pilot_source"]["record_hashes"]:
        raise ProtocolError("the pilot records moved since registration")
    plan = topup_plan(source)
    generate = resolve_generate(tree, generate, where=L.STAGE_TOPUP)
    gate2 = copy.deepcopy(source.gate2)
    generated: dict[str, Any] = {}
    n_rows = 0
    identity = L.protocol_identity(tree, L.STAGE_TOPUP)
    from dci1v7.topics.bank import load_bank
    bank = load_bank()
    by_topic = {t["topic_id"]: t for name in (C.CALIBRATION_A, C.CALIBRATION_B)
                for t in bank.topics(name)}
    for w in plan["frames_running"]:
        fp = plan["by_frame"][str(w)]
        labels = [r["candidate"] for fam in fp["candidate_families"].values()
                  for r in fam]
        candidates = [Constraint(lab.rpartition(":")[0],
                                 int(lab.rpartition(":")[2]), reserve=True)
                      for lab in labels]
        slot_map = {c.label: c for c in candidates}
        grid_a = source.scored_rows(PS.STAGE_GATE2, "grid-A")
        blocks = _frame_blocks_from_rows(grid_a, w)
        cells: list[Cell] = []
        for b in blocks:
            for c in candidates:
                cells.append(Cell(
                    cell_id=f"solo:{c.label}", arm="solo",
                    block_id=b["block_id"], block_index=b["block_index"],
                    frame=w, topic_id=b["topic_id"], slots=(c.label,),
                    wording_by_slot={c.label: w}, draws=C.M_CAL))
        prompts = [prompt_cell(c, by_topic[c.topic_id], slot_map=slot_map,
                               topic_split=next(
                                   b["topic_split"] for b in blocks
                                   if b["block_id"] == c.block_id))
                   for c in cells]
        rows = generate_and_score(
            tree.model_key, prompts, stage=L.STAGE_TOPUP,
            cap=source.selected_cap, device=device,
            run_dir=tree.backend_runs(L.STAGE_TOPUP) / f"frame-{w}",
            instances=tuple(candidates), slot_map=slot_map,
            study_id=tree.context.study_id, protocol_identity=identity,
            generate=generate)
        n_rows += len(rows)
        generated[str(w)] = augment_gate2(source, w, rows, candidates, gate2)
        generated[str(w)]["n_generated"] = len(rows)
        generated[str(w)]["n_blocks"] = len(blocks)
    reverdict = reverdict_gate3(source, gate2)
    # Frames the top-up did not touch must reproduce the pilot's verdicts.
    untouched_agree: dict[str, bool] = {}
    for w in reverdict["supported_frames"]:
        if w in plan["frames_running"]:
            continue
        before = _survival_view(source.gate3["by_frame"][str(w)])
        after = _survival_view(reverdict["by_frame"][str(w)])
        untouched_agree[str(w)] = before == after
        if before != after:
            raise ProtocolError(
                f"frame {w} was not topped up and its Gate-3 verdict moved "
                f"under the same kernel and seed: {before} -> {after}")
    changes = {str(w): {"before": _survival_view(source.gate3["by_frame"][str(w)]),
                        "after": _survival_view(reverdict["by_frame"][str(w)])}
               for w in plan["frames_running"]}
    pilot_elig = EL.local_eligibility(source.gate3["by_frame"], frames=PS.FRAMES)
    return {
        "stage": L.STAGE_TOPUP,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_TOPUP],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"registration_manifest_hash": registration["manifest_hash"],
                   "pilot_record_hashes": source.as_record()["record_hashes"]},
        "plan": plan, "generated": generated, "n_generated_rows": n_rows,
        "topped_up": bool(plan["frames_running"]),
        "augmented_gate2": gate2,
        "reverdicted_gate3": reverdict,
        "untouched_frames_reproduce_pilot": untouched_agree,
        "changes_on_topped_up_frames": changes,
        "local_eligibility_before": {
            "supported": pilot_elig["local_supported_frames"],
            "eligible": pilot_elig["local_eligible"]},
        "local_eligibility_after": {
            "supported": reverdict["local_eligibility"]["local_supported_frames"],
            "eligible": reverdict["local_eligibility"]["local_eligible"]},
        "no_composed_cells": True,
        "reads": "solo, chance and counterfactual-chance rows only; the "
                 "§13.11 schema is closed and unchanged",
    }


def run_topup(tree: L.ConfirmTree, *, producing_commit: str | None = None,
              environment_digest: str = "", device: int = 0,
              generate: Callable[..., dict[str, Any]] | None = None
              ) -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_TOPUP,
        compute=lambda prev: topup_payload(tree, prev, producing_commit=commit,
                                           device=device, generate=generate),
        producing_commit=commit, environment_digest=environment_digest)
