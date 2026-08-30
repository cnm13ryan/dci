#!/usr/bin/env python3
"""What the per-frame calibration allocation would buy: a projection, not evidence.

Approach A (`docs/V8_FRAME_CONDITIONING.md`) measures every difficulty
within a wording frame. At the registered allocation (192 calibration
topics x M_cal draws, one frame per block) a frame holds 48 topics --- 24
per split --- and the pilot measured what that costs: a per-frame
coordinate's SE(iota) sits on the registered 0.05 precision floor, so
`V_coord` and the two-split `V_stab` refuse most rungs and the
frame-specific LOCAL and SPECTRUM rules find little. The design note's
first open researcher decision is therefore the *allocation*: keep the
registered total (accept per-frame precision) or render every block under
every frame (4x the Gate-2 generation, giving each frame all 192 topics).

This tool answers that question arithmetically from a completed pilot's own
rows, by running the **production** Gate-3 rules --- `classify_pool`,
`admit_core_references`, `select_spectrum`, `selected_coverage`,
`admissible_backups`, unchanged --- on tables whose per-topic vectors are
repeated ``k`` times and whose topic counts are multiplied by ``k``.

**What that assumes, stated plainly.** Repeating a frame's measured
per-topic vector k times leaves every rate exactly where it is and divides
every standard error by sqrt(k): it is the arithmetic of "the same
behaviour, measured on k times as many topics". So the projection answers
*"if the rates are what this pilot measured, does the extra precision let
the registered rules admit references?"* --- and nothing else. It cannot
create a rung at a difficulty the ladder does not reach, it cannot predict
how a rate would move on fresh topics (the pilot measures that separately:
each frame's ι is stable across its two splits), and it is not a
measurement. Every number it prints is a projection and is labelled one.

    python3 tools/v8_allocation_projection.py --root <pilot root> --model <key>

Reads the signed Gate-2 and Gate-3 records only, writes
`reports/dci1v8dev/allocation_projection.<model>.{md,json}`. No composed outcome is
read, no frame is chosen, nothing is frozen.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import statistics
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v7.protocol import constants as C  # noqa: E402
from dci1v8dev.run import references as REF  # noqa: E402
from dci1v8dev.run import stages as S  # noqa: E402
from dci1v8dev.run import transitions  # noqa: E402
from dci1v8dev.run.context import model_tree, pilot_context, synthetic_context  # noqa: E402
from dci1v8dev.spectrum.coverage import CoverageRule, selected_coverage  # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
#: Calibration-allocation multipliers: 1 = the registered allocation (one
#: frame per block, 48 topics per frame), 2 = every block under two frames,
#: 4 = every block under every frame (each frame sees all 192 topics).
FACTORS = (1, 2, 4)
STAGES_READ = (S.STAGE_GATE2, S.STAGE_GATE3)


def _scale_rows(rows: Sequence[Mapping[str, Any]], k: int) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        r = dict(row)
        per_topic = list(r.get("per_topic_solo") or ())
        if per_topic:
            r["per_topic_solo"] = per_topic * k
        r["n_topics"] = int(r["n_topics"]) * k
        source = r.get("kappa_under_b_source")
        if isinstance(source, Mapping):
            s = dict(source)
            s["n_topics"] = int(s["n_topics"]) * k
            r["kappa_under_b_source"] = s
        out.append(r)
    return out


def scaled_record(gate2: Mapping[str, Any], k: int) -> dict[str, Any]:
    """The Gate-2 record as it would read if every frame had been measured on
    k times as many topics with the same per-topic behaviour."""
    record = copy.deepcopy(dict(gate2))
    for w in record["supported_frames"]:
        block = record["by_frame"][str(w)]
        for split in block["calibration_rows"]:
            block["calibration_rows"][split] = _scale_rows(
                block["calibration_rows"][split], k)
        block["n_topics_a"] = int(block["n_topics_a"]) * k
        per_topic = (block.get("a_per_topic_by_split") or {}).get("per_topic") or {}
        for split, values in per_topic.items():
            per_topic[split] = list(values) * k
    return record


def _se_iotas(gate3_frame: Mapping[str, Any]) -> list[float]:
    out = []
    for verdict in gate3_frame["spectrum"].values():
        comp = next((c for c in verdict["components"]
                     if c["component"] == "V_coord"), None)
        if comp and comp["values"].get("se_iota") is not None:
            out.append(float(comp["values"]["se_iota"]))
    return out


def _first_failing(gate3_frame: Mapping[str, Any], rule: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for verdict in gate3_frame[rule].values():
        name = verdict["first_failing_component"] or "PASSED"
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def project(tree, gate2: Mapping[str, Any], gate3: Mapping[str, Any], *,
            factors: Sequence[int], resamples: int) -> dict[str, Any]:
    supported = [int(w) for w in gate2["supported_frames"]]
    topics = len(gate2["calibration_topic_ids"])
    per_frame_topics = topics // C.N_WORDINGS
    out: dict[str, Any] = {
        "model_key": tree.model_key,
        "stages_read": list(STAGES_READ),
        "is_projection": True,
        "assumption": "each frame's measured per-topic vector repeated k "
                      "times: every rate unchanged, every SE divided by "
                      "sqrt(k). Not a measurement.",
        "registered_calibration_topics": topics,
        "topics_per_frame_at_the_registered_allocation": per_frame_topics,
        "supported_frames": supported,
        "precision_floor": {"max_se_iota": REF.DEFAULT_SPECTRUM_RULE.max_se_iota,
                            "stability_bound": C.STABILITY_EQUIVALENCE_BOUND},
        "by_factor": {},
    }
    for k in factors:
        record = scaled_record(gate2, k) if k != 1 else dict(gate2)
        frames: dict[str, Any] = {}
        for w in supported:
            block = (gate3["by_frame"][str(w)] if k == 1 else
                     REF.frame_references(record, w, model_key=tree.model_key,
                                          seed=0, resamples=resamples))
            survival = block["survival"]
            points = [{"candidate": p["candidate"], "family": p["family"],
                       "iota": p["iota"], "se_iota": p.get("se_iota")}
                      for p in block["spectrum_selection"]["points"]]
            full = (selected_coverage(points, iota_a=block["iota_a"],
                                      rule=CoverageRule(n_blocks=C.N_BLOCKS))
                    if points else None)
            ses = _se_iotas(block)
            frames[str(w)] = {
                "state": block["state"],
                "n_star": block["n_star"], "m_star": block["m_star"],
                "iota_a": block["iota_a"],
                "topics_per_frame": per_frame_topics * k,
                "topics_per_split": per_frame_topics * k // 2,
                "se_iota_median": statistics.median(ses) if ses else None,
                "n_coordinates": len(ses),
                "n_coordinates_within_floor": sum(
                    1 for s in ses if s <= REF.DEFAULT_SPECTRUM_RULE.max_se_iota),
                "n_local_valid_families": survival["n_local_valid_families"],
                "local_valid_families": survival["local_valid_families"],
                "core_identified": survival["core_identified"],
                "core_references": block["core_references"],
                "n_backups": survival["n_backups"],
                "n_spectrum_valid_below": len(survival["spectrum_valid_below"]),
                "n_spectrum_valid_above": len(survival["spectrum_valid_above"]),
                "spectrum_families_below": survival["spectrum_valid_families_below"],
                "spectrum_families_above": survival["spectrum_valid_families_above"],
                "coverage_identified": survival["coverage_identified"],
                "coverage_reasons": survival["coverage_reasons"],
                "projected_se_beta_at_frame_blocks": survival["projected_se_beta"],
                "projected_se_beta_at_full_blocks": (full["projection"]["se_beta"]
                                                     if full else None),
                "n_spectrum_references": survival["n_spectrum_references"],
                "local_first_failing": _first_failing(block, "local"),
                "spectrum_first_failing": _first_failing(block, "spectrum"),
            }
        out["by_factor"][str(k)] = {
            "calibration_multiplier": k,
            "topics_per_frame": per_frame_topics * k,
            "gate2_generation_multiplier": k,
            "by_frame": frames,
            "n_frames_local": sum(1 for f in frames.values() if f["core_identified"]),
            "n_frames_spectrum": sum(1 for f in frames.values()
                                     if f["coverage_identified"]),
        }
    return out


def render(rep: Mapping[str, Any]) -> str:
    L: list[str] = []
    p = L.append
    p("# DCI-1 v8 — what the per-frame calibration allocation would buy\n")
    p("> Generated by `dci1/tools/v8_allocation_projection.py`. Do not edit by hand.\n")
    p("> **A PROJECTION, NOT EVIDENCE.** " + rep["assumption"] + " It answers "
      "one question --- *if the rates are what this pilot measured, does more "
      "precision let the registered rules admit references?* --- and nothing "
      "else. No threshold is changed; no frame is chosen; nothing is frozen.\n")
    p(f"Model `{rep['model_key']}`; registered allocation "
      f"{rep['registered_calibration_topics']} calibration topics, "
      f"{rep['topics_per_frame_at_the_registered_allocation']} per frame "
      f"(one frame per block, §8.4). Supported frames {rep['supported_frames']}. "
      f"Precision floor SE(ι) ≤ {rep['precision_floor']['max_se_iota']} "
      f"(`rules.SPECTRUM_MAX_SE_IOTA`), split-equivalence bound "
      f"±{rep['precision_floor']['stability_bound']} (§13.7). Both unchanged here.\n")
    p("## Summary\n")
    p("| calibration allocation | topics per frame | Gate-2 generation | frames with LOCAL identified | frames with SPECTRUM identified |")
    p("|---|---:|---:|---:|---:|")
    for k, block in sorted(rep["by_factor"].items(), key=lambda kv: int(kv[0])):
        label = {"1": "registered (one frame per block)",
                 "2": "every block under two frames",
                 "4": "every block under every frame"}.get(k, f"{k}x")
        p(f"| {label} | {block['topics_per_frame']} | "
          f"{block['gate2_generation_multiplier']}× | "
          f"{block['n_frames_local']} / {len(block['by_frame'])} | "
          f"{block['n_frames_spectrum']} / {len(block['by_frame'])} |")
    p("")
    for k, block in sorted(rep["by_factor"].items(), key=lambda kv: int(kv[0])):
        p(f"## Calibration allocation ×{k} — {block['topics_per_frame']} topics "
          f"per frame ({block['topics_per_frame'] // 2} per split)\n")
        p("| frame | state | ι_A(f) | median SE(ι) | coords within the floor | "
          "LOCAL families | core | backups | spectrum below/above | coverage | SE(β̂) frame / full |")
        p("|---|---|---:|---:|---|---:|---|---:|---|---|---|")
        for w, f in sorted(block["by_frame"].items()):
            se = f["se_iota_median"]
            p(f"| f{w} | {f['state']} | {f['iota_a']:.3f} | "
              f"{se:.4f} | {f['n_coordinates_within_floor']}/{f['n_coordinates']} | "
              f"{f['n_local_valid_families']} | "
              f"{'yes ' + str(f['core_references']) if f['core_identified'] else 'no'} | "
              f"{f['n_backups']} | {f['n_spectrum_valid_below']}/{f['n_spectrum_valid_above']} | "
              f"{'yes' if f['coverage_identified'] else 'no'} | "
              f"{f['projected_se_beta_at_frame_blocks'] or '—'} / "
              f"{f['projected_se_beta_at_full_blocks'] or '—'} |")
        p("")
        for w, f in sorted(block["by_frame"].items()):
            p(f"- f{w} first-failing component — LOCAL {f['local_first_failing']}; "
              f"SPECTRUM {f['spectrum_first_failing']}")
        p("")
    p("## Reading it\n")
    p("The two columns that decide the allocation question are *coords within "
      "the floor* (how many per-frame difficulty coordinates the design can "
      "pin at all) and *state*. A frame whose coordinates clear the floor can "
      "still fail SPECTRUM for a reason precision cannot fix --- no admissible "
      "rung on one side of A --- and the first-failing lists say which of the "
      "two it is. `SE(β̂) frame / full` is the projected precision of §11.8's "
      "slope at the frame's share of the registered confirmatory blocks and at "
      "the full allocation: the *second* open allocation decision, which this "
      "table informs but does not take.\n")
    return "\n".join(L) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", default="qwen3-4b")
    ap.add_argument("--namespace", default="pilot", choices=("pilot", "synthetic"))
    ap.add_argument("--factors", type=int, nargs="+", default=list(FACTORS))
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    context = (pilot_context if args.namespace == "pilot" else synthetic_context)(
        pathlib.Path(args.root).resolve())
    tree = model_tree(context, args.model)
    gate2 = transitions.read_stage_record(tree, S.STAGE_GATE2)
    gate3 = transitions.read_stage_record(tree, S.STAGE_GATE3)
    rep = project(tree, gate2, gate3, factors=args.factors,
                  resamples=args.resamples)
    out = (pathlib.Path(args.out) if args.out else
           REPORTS / f"allocation_projection.{args.model}.md")
    machine = out.with_suffix(".json")
    out.write_text(render(rep))
    machine.write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    print(f"wrote {out} and {machine.name}; factors {args.factors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
