#!/usr/bin/env python3
"""A frame where ι_A sits high: is the reference pool short, or is A's operating point?

r8 left two supported frames LOCAL-unsupported with a high difficulty
coordinate --- `qwen3-4b-instruct-2507` f0 at ι_A ≈ 0.844 and
`gemma-3n-e2b-it` f2 at ι_A ≈ 0.794 --- while every other supported frame's
LOCAL failure was precision (`reports/dci1v8dev/bottleneck.*`). Those two are
a different question, and this tool answers it from the signed records.

**The geometry, which is the whole story.** §13.8 matches a LOCAL reference
to A inside `REFERENCE_CALIPER`, so a candidate must have ι within ±0.10 of
ι_A. §13.4's `V_head` requires the 95% Wilson interval for the candidate's
*raw solo compliance* to lie inside `HEADROOM_BAND`, which at a given topic
count admits raw solo compliance only up to some ceiling --- 0.8395 at 96
topics, 0.8150 at 48, 0.8575 at 192. When ι_A approaches that ceiling the
caliper window and the headroom band stop overlapping, and the design cannot
express a matched reference *however many candidates exist*. This tool
measures where the two meet on the run's own numbers.

**What it reports per frame.** The candidate ι distribution relative to
ι_A; how many candidates and families sit inside the caliper; how many of
those `V_head` and `V_diff` refuse; and three counterfactuals ---

* precision free (`V_stab` and `V_coord`'s SE clause satisfied),
* `V_head` ignored,
* `V_diff` ignored,

each counted against §13.15's `MIN_QUALIFIED_FAMILIES`. **The
counterfactuals are diagnosis and nothing reads them**: no selection,
admission or record consults them and no threshold changes anywhere. They
say which of several repairs could possibly work, not that any would.

**And A's own grid.** §12.3 picks n* as A's eligible severity nearest
`TARGET_AIM` inside `TARGET_BAND`; the tool prints the frame's whole A solo
curve, which rungs fall in the band, and what ι_A each would give --- the
prospective question "is there a nearby already-measured rung that would put
ι_A in a healthier matching region?". It changes no operating point: n*,
the band and A's grid are registered and untouched.

    python3 tools/v8_operating_point_diagnosis.py --root <pilot root> \\
        --model <key> [--frame N]

Reads `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` only. Names no composed
or interference quantity. Writes
`reports/dci1v8dev/operating_point.<root>.<model>.{md,json}`.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v7.analysis.intervals import wilson                        # noqa: E402
from dci1v7.protocol import constants as C                          # noqa: E402
from dci1v8dev import rules as R                                    # noqa: E402
from dci1v8dev.run import stages as S                               # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
#: A `V_coord` failure counts as precision only when every clause is the SE
#: clause --- the same convention `v8_bottleneck_diagnosis.py` uses.
PRECISION_COMPONENTS = ("V_stab",)
VERDICTS = ("ACCEPT_LOCAL_UNSUPPORTED", "GRID_REDESIGN_WORTH_CONSIDERING",
            "INSUFFICIENT_EVIDENCE")


def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dir(root: pathlib.Path, model: str) -> pathlib.Path:
    for base in (root / "evidence" / "dci1v8", root / "dci1v8"):
        if (base / model).is_dir():
            return base / model
    raise SystemExit(f"no evidence for {model} under {root}")


def headroom_ceiling(n_topics: int) -> tuple[float, float]:
    """The raw solo compliance `V_head` admits at this topic count.

    `V_head` asks that the whole Wilson interval lie inside HEADROOM_BAND, so
    the admissible range is strictly inside the band and widens with n. Found
    by scanning, because the inverse of the Wilson bound is not worth writing.
    """
    lo = hi = None
    p = 0.0
    while p <= 1.0:
        w = wilson(p, n_topics)
        if C.HEADROOM_BAND[0] <= w[0] and w[1] <= C.HEADROOM_BAND[1]:
            lo = p if lo is None else lo
            hi = p
        p += 0.0005
    return (lo, hi)


def _is_precision(component: Mapping[str, Any]) -> bool:
    name = component.get("component")
    if name in PRECISION_COMPONENTS:
        return True
    if name != "V_coord":
        return False
    problems = [p.strip() for p in (component.get("reason") or "").split(";")
                if p.strip()]
    return bool(problems) and all(p.startswith("SE(iota)") for p in problems)


def _family(label: str) -> str:
    return label.split(":", 1)[0]


def _counterfactual(local: Mapping[str, Any], ignore: Sequence[str]) -> set[str]:
    """Families whose rungs pass every LOCAL component except those ignored."""
    out: set[str] = set()
    for label, verdict in local.items():
        failing = [c for c in verdict.get("components") or []
                   if c.get("passed") is False]
        if all(c["component"] in ignore or _is_precision(c) and "precision" in ignore
               for c in failing):
            out.add(_family(label))
    return out


def _frame(g2f: Mapping[str, Any], g3f: Mapping[str, Any], *,
           n_topics: int) -> dict[str, Any]:
    iota_a = g3f["iota_a"]
    solo_a = g3f["solo_compliance_a"]
    local = g3f["local"]
    rows = {f"{r['kind']}:{r['severity']}": r
            for r in (g2f.get("calibration_rows") or {}).get("pooled") or []}
    lo, hi = headroom_ceiling(n_topics)

    entries = []
    for label, verdict in sorted(local.items()):
        row = rows.get(label) or {}
        solo, kap = row.get("solo_compliance"), row.get("chance_compliance")
        iota = (None if solo is None or kap is None or kap >= 1.0
                else (solo - kap) / (1.0 - kap))
        failing = [c["component"] for c in verdict.get("components") or []
                   if c.get("passed") is False]
        entries.append({
            "candidate": label, "family": _family(label),
            "iota": iota, "solo_compliance": solo, "kappa": kap,
            "distance": None if iota is None else iota - iota_a,
            "inside_caliper": None if iota is None
            else abs(iota - iota_a) <= C.REFERENCE_CALIPER,
            "inside_headroom": None if solo is None else lo <= solo <= hi,
            "failing": failing, "passed": not failing})

    caliper = [e for e in entries if e["inside_caliper"]]
    def _fams(items):
        return sorted({e["family"] for e in items})
    counts = collections.Counter(
        c for e in entries for c in e["failing"])
    return {
        "frame": g3f["frame"], "state": g3f["state"],
        "iota_a": iota_a, "solo_compliance_a": solo_a,
        "n_star": g2f["n_star"], "m_star": g2f["m_star"],
        "n_topics": n_topics,
        "headroom_band": list(C.HEADROOM_BAND),
        "headroom_admits_raw_solo": [lo, hi],
        "iota_a_above_headroom_ceiling": solo_a > hi,
        "caliper": C.REFERENCE_CALIPER,
        "caliper_window": [iota_a - C.REFERENCE_CALIPER,
                           iota_a + C.REFERENCE_CALIPER],
        # Where the two rules overlap: the ι a matched, headroom-admissible
        # reference could have at all. Empty means no candidate could.
        "matchable_window": [max(iota_a - C.REFERENCE_CALIPER, lo),
                             min(iota_a + C.REFERENCE_CALIPER, hi)],
        "matchable_window_width": max(
            0.0, min(iota_a + C.REFERENCE_CALIPER, hi)
            - max(iota_a - C.REFERENCE_CALIPER, lo)),
        "caliper_window_width": 2 * C.REFERENCE_CALIPER,
        "n_candidates": len(entries),
        "n_inside_caliper": len(caliper),
        "families_inside_caliper": _fams(caliper),
        "n_inside_caliper_and_headroom": sum(
            1 for e in caliper if e["inside_headroom"]),
        "families_inside_caliper_and_headroom": _fams(
            [e for e in caliper if e["inside_headroom"]]),
        "failing_component_counts": dict(counts),
        "n_failing_v_head": sum(1 for e in entries if "V_head" in e["failing"]),
        "n_failing_v_diff": sum(1 for e in entries if "V_diff" in e["failing"]),
        "n_caliper_failing_v_head": sum(
            1 for e in caliper if "V_head" in e["failing"]),
        "n_caliper_failing_v_diff": sum(
            1 for e in caliper if "V_diff" in e["failing"]),
        "realised_local_families": g3f["survival"]["local_valid_families"],
        "n_realised_local_families": g3f["survival"]["n_local_valid_families"],
        "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
        "counterfactuals": {
            "precision_free": sorted(_counterfactual(local, ("precision",))),
            "v_head_ignored": sorted(_counterfactual(local, ("V_head",))),
            "v_diff_ignored": sorted(_counterfactual(local, ("V_diff",))),
            "v_head_and_precision": sorted(
                _counterfactual(local, ("V_head", "precision"))),
            "v_diff_and_precision": sorted(
                _counterfactual(local, ("V_diff", "precision"))),
            "note": "a diagnosis read by nothing; no selection, admission or "
                    "record consults these and no threshold changed",
        },
        "iota_distribution": {
            "below_a": sum(1 for e in entries
                           if e["iota"] is not None and e["iota"] < iota_a),
            "above_a": sum(1 for e in entries
                           if e["iota"] is not None and e["iota"] > iota_a),
            "median": statistics.median(
                [e["iota"] for e in entries if e["iota"] is not None]) or None,
            "max": max((e["iota"] for e in entries
                        if e["iota"] is not None), default=None),
        },
        "a_grid": _a_grid(g2f, iota_a=iota_a),
        "candidates": entries,
    }


def _a_grid(g2f: Mapping[str, Any], *, iota_a: float) -> dict[str, Any]:
    """A's own solo curve under this frame, and what each rung would give.

    §12.3 selects n* as the eligible severity nearest TARGET_AIM inside
    TARGET_BAND. The prospective question is whether a *different already
    measured* rung would put ι_A in a healthier matching region; this is the
    evidence for it, and it selects nothing.
    """
    curve = {int(k): v for k, v in (g2f.get("solo_curves") or {}).get("A", {}).items()}
    kappa_a = g2f.get("kappa_a") or 0.0
    rungs = []
    for q in sorted(curve):
        solo = curve[q]
        iota = (solo - kappa_a) / (1.0 - kappa_a) if kappa_a < 1 else None
        rungs.append({"severity": q, "solo_compliance": solo, "iota": iota,
                      "in_target_band": C.TARGET_BAND[0] <= solo <= C.TARGET_BAND[1],
                      "distance_from_aim": abs(solo - C.TARGET_AIM)})
    in_band = [r for r in rungs if r["in_target_band"]]
    return {
        "curve": rungs, "target_band": list(C.TARGET_BAND),
        "target_aim": C.TARGET_AIM, "target_grid": list(C.TARGET_GRID),
        "n_rungs_in_band": len(in_band),
        "rungs_in_band": [r["severity"] for r in in_band],
        "selected_iota_a": iota_a,
        # A's severity scale is the integers 1..8 and the grid is all of
        # them: there is no rung to add between two adjacent severities.
        "grid_is_exhaustive_over_the_construct":
            list(C.TARGET_GRID) == list(range(1, 9)),
        "largest_gap_in_band_neighbourhood": _largest_gap(rungs),
    }


def _largest_gap(rungs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """The widest step between adjacent severities on A's curve."""
    best = None
    for a, b in zip(rungs, rungs[1:]):
        gap = abs(a["solo_compliance"] - b["solo_compliance"])
        if best is None or gap > best["gap"]:
            best = {"from_severity": a["severity"], "to_severity": b["severity"],
                    "from_solo": a["solo_compliance"],
                    "to_solo": b["solo_compliance"], "gap": gap}
    return best


def diagnose(root: pathlib.Path, model: str,
             frames: Sequence[int] | None = None) -> dict[str, Any]:
    d = _model_dir(root, model)
    g2 = _payload(d / S.STAGE_GATE2 / "gate2_calibration.json")
    g3 = _payload(d / S.STAGE_GATE3 / "gate3_references.json")
    alloc = g2.get("calibration_allocation") or {}
    n_topics = int(alloc.get("topics_per_frame")
                   or R.calibration_topics_per_frame(model))
    want = list(frames) if frames else list(g3["supported_frames"])
    out = [_frame(g2["by_frame"][str(w)], g3["by_frame"][str(w)],
                  n_topics=n_topics)
           for w in want if w in g3["supported_frames"]]
    return {
        "artifact_type": "v8_operating_point_diagnosis", "root": root.name,
        "model_key": model, "producing_commit": g3.get("producing_commit"),
        "stages_read": [S.STAGE_GATE2, S.STAGE_GATE3],
        "calibration_allocation": alloc,
        "reads_no_composed_quantity": True, "changes_no_threshold": True,
        "changes_no_operating_point": True,
        "frames": out,
    }


def render(diag: Mapping[str, Any]) -> str:
    a = diag["calibration_allocation"]
    L = [f"# DCI-1 v8 — A's operating point and LOCAL headroom on "
         f"`{diag['model_key']}`", "",
         "> Generated by `dci1/tools/v8_operating_point_diagnosis.py`. Do not "
         "edit by hand.", "",
         "> Reads the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` "
         "records only. The counterfactual columns are a **diagnosis read by "
         "nothing**; no threshold, operating point, band or grid is changed.",
         "",
         f"Root `{diag['root']}`; calibration at "
         f"**{a.get('topics_per_frame')} topics per frame**.", "",
         "§13.8 matches a LOCAL reference inside ±"
         f"{C.REFERENCE_CALIPER} of ι_A. §13.4's `V_head` needs the whole "
         f"Wilson interval for the candidate's raw solo compliance inside "
         f"{list(C.HEADROOM_BAND)}, which at this topic count admits raw solo "
         "compliance only in the range below. Where those two windows stop "
         "overlapping, no candidate can be a matched reference — however many "
         "the pool holds.", "",
         "| frame | state | ι_A | `V_head` admits | caliper window | "
         "matchable | in caliper | of those, headroom-OK | LOCAL families |",
         "|---|---|---:|---|---|---:|---:|---:|---:|"]
    for f in diag["frames"]:
        lo, hi = f["headroom_admits_raw_solo"]
        cw = f["caliper_window"]
        L.append(
            f"| f{f['frame']} | {f['state']} | {f['iota_a']:.3f} | "
            f"[{lo:.3f}, {hi:.3f}] | [{cw[0]:.3f}, {cw[1]:.3f}] | "
            f"{f['matchable_window_width']:.3f} of "
            f"{f['caliper_window_width']:.2f} | {f['n_inside_caliper']} | "
            f"{f['n_inside_caliper_and_headroom']} | "
            f"{f['n_realised_local_families']} / "
            f"{f['min_qualified_families']} |")
    L.append("")
    for f in diag["frames"]:
        cf = f["counterfactuals"]
        g = f["a_grid"]
        L += [f"### f{f['frame']} — {f['state']}, ι_A = {f['iota_a']:.4f}", "",
              f"- n* = {f['n_star']}, m* = {f['m_star']}; A's raw solo "
              f"compliance {f['solo_compliance_a']:.4f}",
              f"- `V_head` admits raw solo in "
              f"[{f['headroom_admits_raw_solo'][0]:.4f}, "
              f"{f['headroom_admits_raw_solo'][1]:.4f}] at "
              f"{f['n_topics']} topics; **A itself is "
              f"{'above' if f['iota_a_above_headroom_ceiling'] else 'inside'}"
              f"** that ceiling",
              f"- the caliper window and the headroom band overlap on "
              f"{f['matchable_window_width']:.4f} of the caliper's "
              f"{f['caliper_window_width']:.2f} — "
              f"{100 * f['matchable_window_width'] / f['caliper_window_width']:.0f}% "
              f"of the matching region survives `V_head` by geometry alone",
              f"- candidates: {f['n_candidates']}; inside the caliper "
              f"{f['n_inside_caliper']} from "
              f"{len(f['families_inside_caliper'])} families "
              f"{f['families_inside_caliper']}",
              f"- of those, inside the headroom band too: "
              f"{f['n_inside_caliper_and_headroom']} from "
              f"{len(f['families_inside_caliper_and_headroom'])} families "
              f"{f['families_inside_caliper_and_headroom']}",
              f"- failing `V_head` {f['n_failing_v_head']} "
              f"({f['n_caliper_failing_v_head']} of them inside the caliper); "
              f"failing `V_diff` {f['n_failing_v_diff']} "
              f"({f['n_caliper_failing_v_diff']} inside)",
              f"- realised LOCAL-valid families "
              f"{f['n_realised_local_families']} "
              f"{f['realised_local_families']} against §13.15's "
              f"{f['min_qualified_families']}", "",
              "**Counterfactuals (read by nothing).** Families that would be "
              "LOCAL-valid if one requirement were satisfied:", "",
              f"| relaxed | families | meets §13.15's "
              f"{f['min_qualified_families']} |", "|---|---:|---|"]
        for key, name in (("precision_free", "precision only"),
                          ("v_head_ignored", "`V_head` only"),
                          ("v_diff_ignored", "`V_diff` only"),
                          ("v_head_and_precision", "`V_head` + precision"),
                          ("v_diff_and_precision", "`V_diff` + precision")):
            fams = cf[key]
            L.append(f"| {name} | {len(fams)} {fams} | "
                     f"{'yes' if len(fams) >= f['min_qualified_families'] else 'no'} |")
        L += ["", f"**A's own grid under this frame.** §12.3 picks n* nearest "
              f"{g['target_aim']} inside {g['target_band']}; A's severity "
              f"scale is {g['target_grid']} and the grid covers "
              f"{'every integer in it (exhaustive over the construct)' if g['grid_is_exhaustive_over_the_construct'] else 'a subset'}.",
              "", "| n | raw solo | ι | in target band |", "|---:|---:|---:|---|"]
        for r in g["curve"]:
            mark = "**selected**" if r["severity"] == f["n_star"] else (
                "yes" if r["in_target_band"] else "—")
            L.append(f"| {r['severity']} | {r['solo_compliance']:.4f} | "
                     f"{r['iota']:.4f} | {mark} |")
        gap = g["largest_gap_in_band_neighbourhood"]
        L += ["", f"- rungs inside the target band: {g['n_rungs_in_band']} "
              f"{g['rungs_in_band']}",
              f"- widest step between adjacent severities: n={gap['from_severity']} "
              f"→ n={gap['to_severity']}, raw solo {gap['from_solo']:.4f} → "
              f"{gap['to_solo']:.4f} (a gap of {gap['gap']:.4f})", ""]
    return "\n".join(L) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--frame", type=int, action="append", default=None)
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    diag = diagnose(root, args.model, args.frame)
    out = pathlib.Path(args.out_dir) if args.out_dir else REPORTS
    out.mkdir(parents=True, exist_ok=True)
    stem = f"operating_point.{root.name}.{args.model}"
    slim = {**diag, "frames": [{k: v for k, v in f.items() if k != "candidates"}
                               for f in diag["frames"]]}
    (out / f"{stem}.json").write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n")
    (out / f"{stem}.md").write_text(render(slim))
    print(f"wrote {out / (stem + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
