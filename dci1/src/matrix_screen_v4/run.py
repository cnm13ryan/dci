"""Generate and score one model's pairwise-matrix screen.

Reads the calibration screen's §13.2 output for the constraint set, freezes the
whole design including that constraint set, then generates. Writes only under
evidence/matrix-screen-v4/<model>/ and reports/matrix_screen_v4/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from dci1v4.engine import fs
from dci1v4.generation.backend import build_plan, run_backend
from dci1v4.models.registry import MODEL_KEYS, get_model
from dci1v4.topics.split import split_topics
from dci1v4.verifiers.words import alpha_runs

from cal_screen_v4.run import score_cell
from cal_screen_v4.lowerbound_run import LOWER_BOUND_FAMILIES
from fs_screen_v4.constraints import CANDIDATES
from matrix_screen_v4 import CLASSIFICATION, STUDY_ID
from matrix_screen_v4 import plan as pl
from matrix_screen_v4 import protocol as proto
from matrix_screen_v4 import witnesses as wit

DCI1 = Path(__file__).resolve().parent.parent.parent
EVIDENCE = DCI1 / "evidence" / "matrix-screen-v4"
CAL_RESULTS = DCI1 / "reports" / "cal_screen_v4" / "results.json"

#: Topic sets this screen may use, and the reason each is or is not permitted.
#: composed(24) is EXCLUDED: §13.6 evaluates every registered composed cell
#: type on exactly those topics at exactly this M, so generating composed cells
#: there first would make Gate 4 a check of cells it had already seen and
#: COMPOSED_HEADROOM_FAILURE unfalsifiable.
TOPIC_SETS = {"prescreen": "the declared development sample; §13.2 condition 2 "
                           "already prices its reuse in at a widened caliper",
              "solo": "no registered gate reads a composed cell from this set: "
                      "gates.gate2_payload takes only solo quantities, and "
                      "gates.admit_family's own docstring says its calibration "
                      "argument is 'per-topic solo-compliance cell means'. "
                      "Gate 4, the one stage that does read composed cells, "
                      "runs on the composed-validation set"}

#: Where the authority to use solo(96) for composed cells comes from. Recorded
#: because it is a preregistration-touching judgement and the reader should be
#: able to audit who made it, not merely that it was made.
SOLO_TOPIC_AUTHORITY = (
    "§6.2 lists the permitted use of the 96 solo-calibration topics as solo "
    "curves and severity selection, so generating COMPOSED cells there is "
    "outside its literal wording even for a non-registered screen. Two checks "
    "and one decision stand behind doing it anyway: (1) the registered gate "
    "code was read and no gate reads a composed cell from this set; (2) a "
    "second Claude session working the Gate 1 track independently traced the "
    "same code and reached the same reading; (3) that session reports its user "
    "ratified it, conditional on the reference set being hashed into this "
    "frozen protocol before generation with the no-revision bar attached, "
    "which it is. The ratification reached this session RELAYED BY A PEER "
    "SESSION and not directly, so it is recorded as such and the researcher "
    "should confirm it. The screen is designed so the confirmation is not "
    "load-bearing: every quantity is reported on the 24 pre-screen blocks "
    "alone as well as on all 120, the pre-screen half needs no ratification, "
    "and evidence/matrix-screen-v4 can be deleted without touching anything "
    "else.")
EXCLUDED_TOPIC_SETS = {"composed": "Gate 4's own evidence set (§13.6)",
                       "confirmatory": "reserved for the frozen experiment",
                       "sequestered": "inaccessible by construction (§6.2)"}


def calibration_design(model: str) -> dict[str, Any]:
    """The constraint set, taken from the calibration screen and nowhere else."""
    results = json.loads(CAL_RESULTS.read_text())
    entry = results["models"].get(model)
    if not entry or "unavailable" in entry:
        raise SystemExit(f"{model}: no calibration-screen result; neither "
                         f"design is defined")
    admission = entry.get("admission", {})
    if "anchor" not in admission:
        raise SystemExit(f"{model}: no focal severity; the calibration screen "
                         f"selected no n* under this stem, so neither design "
                         f"is defined")
    # §13.2 selects "the final three ... the admitted families with the
    # smallest solo distance from A" from whatever pool exists. Under
    # Amendment B that pool is the eight registered families PLUS the adopted
    # candidates, and the amendment is explicit that "nothing in the selection
    # logic changes". So the screen selects from the enlarged pool rather than
    # from the candidates alone: excluding an admitted registered family
    # because of its FORM would be a selection rule the protocol does not have,
    # and it would hide the case where the registered pool works.
    # The disposition the calibration screen names, so the choice is auditable
    # on its artifact rather than made here. `strict_registered_precision`
    # travels with it and is recorded in the frozen protocol below.
    pool = admission.get("matrix_reference_set") or {}
    chosen_all = (pool.get("admitted") or pool.get("chosen")
                  or admission["enlarged_pool"].get("admitted")
                  or admission["enlarged_pool"]["chosen"])
    # The three references are BUDGET families and the class control is a
    # production one. If a lower-bound family were also taken as a reference,
    # Delta_R would itself be a mixed-class contrast and would blur the exact
    # distinction the class arm exists to draw -- and on some models the same
    # family would fill both slots. So the R slots are drawn from the budget
    # families in §13.2's own order, and the lower-bound families are reserved
    # for the class arm. Recorded in the frozen protocol.
    budgets = [c for c in chosen_all
               if c["family"] not in LOWER_BOUND_FAMILIES]
    if len(budgets) >= 3:
        chosen = budgets[:3]
        slot_rule = ("three budget families, lower-bound families reserved for "
                     "the class arm")
    else:
        # Reserving a lower-bound family would cost this model its third
        # reference, and §13.2's own rule does not know about class. Fall back
        # to the registered ordering and record that the class arm is
        # unavailable here rather than quietly running a mixed-class Delta_R
        # and calling it the same quantity as the others.
        chosen = chosen_all[:3]
        slot_rule = (f"§13.2's plain ordering: only {len(budgets)} budget "
                     f"families were admitted, so reserving a lower-bound "
                     f"family for the class arm would cost the third reference")
    n_star = admission["anchor"]["n_star"]
    # Minimum amendment: take m* from the REGISTERED focal grid wherever the
    # registered grid supplies one, and fall back to the extended grid only
    # where the registered grid is exhausted. Amendment C is then invoked per
    # model, only where it is necessary, and the calibration screen shows the
    # fallback is not free: on qwen3-4b-instruct-2507 the extended grid moves
    # m* from 10 to 11 and 11 fails §12.4's graded clause under one of its two
    # readings while 10 passes under both.
    q2 = entry["verdicts"]["Q2_honest_focal_severity"]
    m_star = q2["registered_grid_m_star"] or q2["extended_grid_m_star"]
    m_star_source = ("registered focal grid" if q2["registered_grid_m_star"]
                     else "extended focal grid (Amendment C), because the "
                          "registered grid returned "
                          + str(q2.get("registered_grid_diagnosis")))
    if m_star is None:
        raise SystemExit(f"{model}: no focal severity; neither design is "
                         f"defined")
    constraints = [pl.Constituent("A", "A", n_star),
                   pl.Constituent("B", "B", m_star)]
    reduced = len(chosen) < 3
    if reduced:
        # §8.6 and §13.5: fewer than three admitted references is an
        # identification status, not a terminal one. The replication still runs
        # and still estimates D(B<-A), D(A<-B) and Lambda.
        return {"constraints": constraints, "spanning": [], "reduced": True,
                "admission_status": "EXCESS_NOT_IDENTIFIED",
                "m_star_source": m_star_source, "class_control": None,
                "admission_disposition": (
                    f"{pool.get('disposition', 'registered rule as data allows')}"
                    f"; fewer than three references admitted, so §8.6's reduced "
                    f"design applies (§13.5: an identification status, not a "
                    f"terminal one). The strict registered-precision "
                    f"disposition admits "
                    f"{admission['enlarged_pool']['n_admitted']} families."),
                "pool": "the eight registered families plus CR7, CR4 and CR6",
                "admitted_families": (pool or admission["enlarged_pool"]).get(
                    "admitted_families", []),
                "n_admitted": len(chosen)}
    for index, ref in enumerate(chosen, start=1):
        constraints.append(pl.Constituent(f"R{index}", ref["family"],
                                          ref["severity"]))

    class_control = None
    used = {c["family"] for c in chosen}
    picked = [c for c in (pool.get("class_matched")
                          or (admission.get("class_matched_companion", {}) or {}
                              ).get("selected") or [])
              if c["family"] not in used]
    if picked:
        class_control = pl.Constituent("C1", picked[0]["family"],
                                       picked[0]["severity"])

    # ---- the V5 spanning arm
    #
    # A spanning companion is by definition NOT difficulty-matched, so §13.2's
    # caliper does not apply to it and it need not be an admitted reference. It
    # needs a measured calibration curve, low solo vacuity, valid wordings and
    # certified witnesses -- which the three rate families have over their full
    # ladders on every model. Drawing the arm from a rate family rather than
    # from whichever families happened to be admitted is what lets **every**
    # model carry a difficulty axis: on gemma-3n-E4B all three admitted
    # references are registered families, which carry only the three-rung §12.2
    # shortlist and cannot span anything.
    #
    # One family, chosen for the widest measured span around the anchor, two
    # rungs at the registered offsets. One family rather than three keeps the
    # arm at four cells per block and keeps the difficulty regression from
    # being dominated by whichever family happens to have the longest ladder.
    anchor_compliance = admission["anchor"]["A_solo_compliance"]
    curves = {t["family"]: ({c["severity"]: c["solo_compliance"]
                             for c in t["candidates"]},
                            {c["severity"]: c["vacuity"]
                             for c in t["candidates"]})
              for t in entry["admission"]["candidate_table"]}
    spanning: list[pl.Constituent] = []
    spanning_family = None
    best_span = -1.0
    for family, (curve, vac) in sorted(curves.items()):
        usable = [q for q in curve if vac.get(q, 1.0) <= 0.10]
        if len(usable) < 3:
            continue
        span = max(curve[q] for q in usable) - min(curve[q] for q in usable)
        brackets = (min(curve[q] for q in usable) <= anchor_compliance
                    <= max(curve[q] for q in usable))
        score = span + (1.0 if brackets else 0.0)
        if score > best_span:
            best_span, spanning_family = score, family
    if spanning_family is not None:
        curve, vac = curves[spanning_family]
        matched = min(curve, key=lambda q: abs(curve[q] - anchor_compliance))
        for label, q in enumerate(pl.spanning_rungs(
                spanning_family, CANDIDATES[spanning_family].ladder, curve,
                vac, matched, curve[matched]), start=1):
            spanning.append(pl.Constituent(f"S{label}", spanning_family, q))
    return {"constraints": constraints, "spanning": spanning,
            "class_control": class_control,
            "reduced": False, "n_admitted": len(chosen),
            "admission_status": (
                (pool or admission["enlarged_pool"]).get(
                    "identification_status") or "three references admitted"),
            "admission_disposition": (
                f"{pool.get('disposition', 'registered rule as data allows')}; "
                f"every other condition exactly as registered on the 96 "
                f"calibration topics. The strict registered-precision "
                f"disposition admits "
                f"{admission['enlarged_pool']['n_admitted']} families."),
            "m_star_source": m_star_source,
            "reference_slot_rule": slot_rule,
            "class_arm_available": bool(picked),
            "spanning_family": spanning_family,
            "spanning_rule": ("one rate family, chosen for the widest measured "
                              "calibration span that brackets A's compliance; "
                              "a spanning companion is deliberately unmatched, "
                              "so §13.2's caliper does not apply to it"),
            "pool": "the eight registered families plus CR7, CR4 and CR6",
            "admitted_families": (pool or admission["enlarged_pool"])[
                "admitted_families"]}


def build_design(model: str, *, topic_sets: Sequence[str], stem: str
                 ) -> dict[str, Any]:
    for name in topic_sets:
        if name not in TOPIC_SETS:
            raise SystemExit(f"topic set {name!r} is not permitted here: "
                             f"{EXCLUDED_TOPIC_SETS.get(name, 'unknown set')}")
    chosen = calibration_design(model)
    split = split_topics()
    topics = [t for name in topic_sets for t in split[name]]
    cells = pl.build_cells(topics, chosen["constraints"], chosen["spanning"],
                           stem=stem, reduced=chosen["reduced"],
                           class_control=chosen["class_control"])
    allocation = pl.assert_allocation(cells, len(topics))
    return {
        "constraints": chosen["constraints"], "spanning_c": chosen["spanning"],
        "class_control_c": chosen["class_control"],
        "cells": cells, "stem": stem,
        "constraint_set": [{"role": c.role, "kind": c.kind,
                            "severity": c.severity}
                           for c in chosen["constraints"]],
        "spanning": [{"role": c.role, "kind": c.kind, "severity": c.severity}
                     for c in chosen["spanning"]],
        "spanning_family": chosen.get("spanning_family"),
        "spanning_rule": chosen.get("spanning_rule", "no spanning arm"),
        "class_control": (None if chosen["class_control"] is None else
                          {"role": chosen["class_control"].role,
                           "kind": chosen["class_control"].kind,
                           "severity": chosen["class_control"].severity}),
        "admission_status": chosen["admission_status"],
        "m_star_source": chosen["m_star_source"],
        "reference_slot_rule": chosen.get("reference_slot_rule", "reduced"),
        "admitted_families": chosen["admitted_families"],
        "admission_disposition": chosen["admission_disposition"],
        "design": "§8.6 reduced" if chosen["reduced"] else "§8.1 full matrix",
        "n_references_admitted": chosen["n_admitted"],
        "plan_summary": pl.plan_summary(cells), "allocation": allocation,
        "witnesses": wit.verify_set(
            model,
            [{"role": c.role, "kind": c.kind, "severity": c.severity}
             for c in list(chosen["constraints"]) + list(chosen["spanning"])
             + ([chosen["class_control"]] if chosen["class_control"] else [])],
            pairs=sorted({tuple(sorted(c.roles)) for c in cells
                          if len(c.roles) == 2})),
        "topics": {"sets": list(topic_sets), "blocks": len(topics),
                   "blocks_by_set": {name: len(split[name])
                                     for name in topic_sets},
                   "why_permitted": {k: TOPIC_SETS[k] for k in topic_sets},
                   "excluded": EXCLUDED_TOPIC_SETS},
        "topic_set_authority": (SOLO_TOPIC_AUTHORITY if "solo" in topic_sets
                                else "pre-screen only; no ratification needed"),
    }


def run(model: str, device: int, *, topic_sets: Sequence[str], stem: str,
        limit: int | None = None) -> dict[str, Any]:
    spec = get_model(model)
    design = build_design(model, topic_sets=topic_sets, stem=stem)
    frozen = proto.freeze(model, design)
    cells = design["cells"]

    design_rows: list[dict[str, Any]] = []
    for cell in cells:
        for draw in range(pl.DRAWS):
            design_rows.append({
                "cell_id": cell.cell_id, "draw_index": draw,
                "row_id": f"{cell.cell_id}:{draw}",
                "prompt_hash": cell.prompt_hash,
                "scientific_seed": pl.screen_seed(spec.model_id,
                                                  cell.prompt_hash, draw),
                "user_prompt": cell.prompt})
    if limit:
        design_rows = design_rows[:limit]

    cap = json.loads(
        (DCI1 / "evidence" / "dci1-v4" / model / "regime_screen.json").read_text()
    )["payload"]["completion_cap"]["selected_cap"]
    run_dir = EVIDENCE / model / f"screen-cap{cap}" / "backend_runs" / "round0"
    plan = build_plan(spec, stage=pl.STAGE, max_new_tokens=cap)
    plan["chunk_size"] = 64
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 12)

    by_cell = {c.cell_id: c for c in cells}
    all_constituents = (list(design["constraints"]) + list(design["spanning_c"])
                        + ([design["class_control_c"]]
                           if design["class_control_c"] else []))
    cache = []
    for raw, row in zip(outcome["rows"], design_rows):
        cell = by_cell[row["cell_id"]]
        text = raw.get("final_answer") or ""
        truncated = bool(raw.get("answer_truncated"))
        scores = []
        # An unconstrained cell is scored on EVERY constraint in the design:
        # that is what makes it an accidental-compliance measurement.
        scored_against = (cell.constituents if cell.constituents
                          else tuple(all_constituents))
        for constituent in scored_against:
            scored = score_cell(constituent.kind, constituent.severity, text,
                                truncated=truncated)
            scores.append({"role": constituent.role, "kind": constituent.kind,
                           "severity": constituent.severity, **scored})
        cache.append({
            "row_id": row["row_id"], "cell_id": cell.cell_id,
            "cell_key": ("|".join(sorted(cell.roles)) if len(cell.roles) > 1
                         else cell.roles[0] if cell.roles else "none"),
            "arm": cell.arm, "order_label": cell.order_label,
            "roles": list(cell.roles), "stem": cell.stem,
            "topic_id": cell.topic_id, "block_index": cell.block_index,
            "draw_index": row["draw_index"],
            "wording_indices": list(cell.wording_indices),
            "prompt_hash": cell.prompt_hash, "seed": row["scientific_seed"],
            "raw_response": text, "finish_reason": raw.get("finish_reason"),
            "token_count": raw.get("total_generated_tokens"),
            "truncated": truncated,
            "word_count": len(alpha_runs(text)),
            "stem_satisfied": pl.stem_satisfied(len(alpha_runs(text))),
            "model_key": model, "model_id": spec.model_id,
            "model_revision": spec.revision, "study_id": STUDY_ID,
            "classification": CLASSIFICATION,
            "screen_protocol_hash": frozen["screen_protocol_hash"],
            "scores": scores})

    out_dir = EVIDENCE / model / f"screen-cap{cap}"
    (out_dir / "cache.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in cache))
    report = {"study_id": STUDY_ID, "classification": CLASSIFICATION,
              "model_key": model, "selected_cap": cap,
              "screen_protocol_hash": frozen["screen_protocol_hash"],
              "constraint_set": design["constraint_set"],
              "spanning": design["spanning"],
              "class_control": design["class_control"],
              "topics": design["topics"],
              "plan": design["plan_summary"], "rows": len(cache),
              "truncated": sum(1 for r in cache if r["truncated"])}
    fs.write_json(out_dir / "screen_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_KEYS)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--topics", nargs="+", default=["prescreen"],
                        choices=sorted(TOPIC_SETS))
    parser.add_argument("--stem", default="floored")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    if args.plan_only:
        design = build_design(args.model, topic_sets=args.topics, stem=args.stem)
        print(json.dumps({k: design[k] for k in
                          ("constraint_set", "spanning", "plan_summary",
                           "topics", "admission_status")}, indent=1))
        return 0
    print(json.dumps(run(args.model, args.device, topic_sets=args.topics,
                         stem=args.stem, limit=args.limit), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
