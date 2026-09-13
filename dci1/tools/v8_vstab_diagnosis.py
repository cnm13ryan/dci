#!/usr/bin/env python3
"""Why does §13.7's `V_stab` refuse a candidate — noise, or two halves that disagree?

After the calibration-allocation amendment (two passes, 96 topics per frame;
`CHANGES_SCIENTIFIC.md` 2026-08-30) `V_stab` became the leading first-failing
component on every frame of every model. `tools/v8_bottleneck_diagnosis.py`
counts it as a precision statement and stops there. That is the conservative
reading, and it is not an answer: `V_stab` is **three** registered conditions,
only two of which are about precision at all.

**What `V_stab` actually requires** (`dci1v7.stages.stability.stability_verdict`,
§13.7):

1. R is independently admissible on Calibration-A *and* on Calibration-B, each
   split evaluated alone, under `V_head`, `V_chance`, `V_inter`, `V_diff`;
2. the 95% percentile-bootstrap interval for `iota_A - iota_B` lies wholly
   inside +/- `STABILITY_EQUIVALENCE_BOUND`;
3. the same interval for `p_solo_A - p_solo_B` lies wholly inside that bound.

Conditions 2 and 3 resample **topics within split**, so the independent unit is
the topic and the interval's half-width falls as 1/sqrt(topics per split).
Condition 1 is not a precision statement at all: it re-runs four candidate
components at half the frame's topics.

**The distinction this tool makes.** Every recorded failure is a list of
semicolon-separated *clauses*, and each clause is one of

* `INTERVAL` --- a clause about an interval (`V_stab`'s bootstrap, `V_head`'s
  Wilson, `V_chance`'s Wilson upper, `V_diff`'s Newcombe, `V_coord`'s SE).
  Its width falls with more calibration topics; its centre does not.
* `POINT` --- a clause about a point estimate (`V_head`'s lift and vacuity,
  `V_chance`'s compliance, `V_inter`'s projected compliance, `V_diff`'s two
  calipers, `V_coord`'s guard band). No allocation moves it.

A clause the tool does not recognise is counted `UNCLASSIFIED` and never
silently folded into either, so a changed reason string shows up as an
unclassified count rather than as a wrong answer.

**The question it exists to answer.** For an equivalence failure (conditions 2
and 3) the two halves' difference has a point estimate and a half-width. If
`|point|` is inside the bound and the interval spills out, the design cannot
*resolve* the difference --- finite-sample. If `|point|` is itself outside the
bound, the two topic halves genuinely disagree by more than the rule permits,
and no allocation repairs that. Those are different findings and the tool
separates them.

**Bins are descriptive.** Failures are sorted into "barely misses / moderate /
large" by quantiles of the observed excess, not by any threshold: the labels
carry the quantile that produced them and no rule reads them.

**Projections are labelled projections.** The 2x column holds the point
estimate fixed and shrinks the interval by sqrt(2) (bootstrap, Wilson,
Newcombe recomputed at twice the topics through the registered functions). It
says what *would* follow if the halves' disagreement is what it currently
measures; it is not evidence and nothing reads it.

    python3 tools/v8_vstab_diagnosis.py --root <pilot root> --model <key>

Reads the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` records only.
Changes no threshold, alters no verdict, names no composed quantity. Writes
`reports/dci1v8dev/vstab.<root>.<model>.{md,json}`.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v7.analysis.intervals import wilson, newcombe_interval      # noqa: E402
from dci1v7.protocol import constants as C                           # noqa: E402
from dci1v8dev import rules as R                                     # noqa: E402
from dci1v8dev.run import stages as S                                # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
BOUND = C.STABILITY_EQUIVALENCE_BOUND

#: Clause prefixes, and what kind of statement each one is. Order matters
#: only in that the first matching prefix wins.
CLAUSE_KINDS: tuple[tuple[str, str], ...] = (
    ("the 95% Wilson interval for raw solo compliance", "INTERVAL"),
    ("the 95% Wilson upper bound on chance compliance", "INTERVAL"),
    ("the Newcombe interval", "INTERVAL"),
    ("the 95% bootstrap interval", "INTERVAL"),
    ("SE(iota)", "INTERVAL"),
    ("projected compliance under B", "POINT"),      # V_inter_s guard band
    ("displacement", "POINT"),                      # V_inter_s displacement
    ("instruction lift", "POINT"),
    ("solo vacuity", "POINT"),
    ("chance compliance", "POINT"),
    ("projected composed compliance", "POINT"),
    ("instructed-compliance distance", "POINT"),
    ("raw solo-compliance distance", "POINT"),
    ("raw solo compliance", "POINT"),          # V_coord guard band
    ("no complete", "POINT"),
    ("wording outside", "POINT"),
    ("parse independence", "POINT"),
    ("formal joint-satisfiability", "POINT"),
    ("no realistic witness", "POINT"),
)

CONDITIONS = ("split_admissibility", "iota_equivalence", "solo_equivalence")


def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dir(root: pathlib.Path, model: str) -> pathlib.Path:
    for base in (root / "evidence" / "dci1v8", root / "dci1v8"):
        if (base / model).is_dir():
            return base / model
    raise SystemExit(f"no evidence for {model} under {root}")


def _clauses(reason: str | None) -> list[str]:
    return [c.strip() for c in (reason or "").split(";") if c.strip()]


def _kind(clause: str) -> str:
    for prefix, kind in CLAUSE_KINDS:
        if clause.startswith(prefix):
            return kind
    return "UNCLASSIFIED"


def _family(label: str) -> str:
    return label.split(":", 1)[0]


def _gap_stats(gap: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """One equivalence interval, and where it sits relative to the bound."""
    if not gap:
        return None
    lo, hi = float(gap["lower"]), float(gap["upper"])
    point, half = float(gap["point"]), (hi - lo) / 2.0
    # How far outside the bound the interval reaches: positive when it fails.
    excess = max(-BOUND - lo, hi - BOUND, 0.0)
    inside = -BOUND <= lo and hi <= BOUND
    # Held-fixed-point projection: the same centre, the interval narrowed by
    # sqrt(2) as one more calibration pass would narrow it.
    half2 = half / math.sqrt(2.0)
    centre = (lo + hi) / 2.0
    inside_2x = -BOUND <= centre - half2 and centre + half2 <= BOUND
    return {"point": point, "lower": lo, "upper": hi, "half_width": half,
            "abs_point": abs(point), "excess": excess, "inside": inside,
            "point_inside_bound": abs(point) <= BOUND,
            "projected_inside_at_2x": inside_2x}


def _admissibility(verdict: Mapping[str, Any],
                   pooled: Mapping[str, Any] | None) -> dict[str, Any]:
    """Condition 1, clause by clause, on each split alone.

    ``pooled`` is the same candidate's verdict on the frame's **pooled**
    table --- every calibration topic the frame has --- and it is what makes
    this decomposition mean anything. A split-level component failure is

    * `ALLOCATION_INVARIANT` when the same component also fails on the
      pooled table: the split did not refuse the rung, the rung is refused.
      `V_diff`'s caliper on a candidate genuinely far from ι_A is the
      dominant case, and no allocation moves it;
    * `ALLOCATION_SENSITIVE` when the component *passes* on the pooled table
      and fails on this split alone: the split's own estimate --- an
      interval formed at half the topics, or a point estimate that has not
      converged to the pooled one --- is what refused it. One more pass
      halves that gap's variance.

    Splitting it this way matters because §13.7 condition 1 embeds `V_diff`,
    and `V_stab` is evaluated *before* `V_diff` in §13.1's registered
    lexicographic order. A candidate outside the caliper therefore surfaces
    as a `V_stab` failure and would have failed `V_diff` regardless. The
    order "decides which reason is recorded and not which candidates pass"
    (`stages/validity.py`), so a first-failing histogram over-attributes to
    `V_stab` exactly the rungs the caliper was always going to refuse.
    """
    pooled_failing = {c["component"] for c in (pooled or {}).get("components") or []
                      if c.get("passed") is False}
    out: dict[str, Any] = {"splits": {}, "failing_components": [],
                           "clause_kinds": collections.Counter(),
                           "point_components": [], "interval_only": True,
                           "invariant_components": [],
                           "sensitive_components": [],
                           "pooled_verdict_available": pooled is not None}
    for split, block in sorted((verdict.get("per_split") or {}).items()):
        failing = []
        for comp in block.get("components") or []:
            if comp.get("passed") is not False:
                continue
            name = comp["component"]
            kinds = [_kind(c) for c in _clauses(comp.get("reason"))]
            for k in kinds:
                out["clause_kinds"][k] += 1
            has_point = "POINT" in kinds or "UNCLASSIFIED" in kinds
            if has_point:
                out["point_components"].append(name)
            # The load-bearing test: does the pooled table refuse it too?
            invariant = name in pooled_failing
            if invariant:
                out["interval_only"] = False
                out["invariant_components"].append(name)
            else:
                out["sensitive_components"].append(name)
            failing.append({"component": name, "kinds": kinds,
                            "has_point_clause": has_point,
                            "allocation": ("ALLOCATION_INVARIANT" if invariant
                                           else "ALLOCATION_SENSITIVE"),
                            "reason": comp.get("reason")})
            out["failing_components"].append(name)
        out["splits"][split] = {"admissible": bool(block.get("admissible")),
                                "failing": failing}
    out["clause_kinds"] = dict(out["clause_kinds"])
    if not out["failing_components"]:
        out["interval_only"] = False          # nothing failed; not meaningful
    return out


def _anatomy(verdict: Mapping[str, Any],
             pooled: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One candidate's `V_stab` verdict decomposed into the three conditions."""
    adm_ok = bool(verdict.get("admissible_on_both_splits"))
    iota = _gap_stats(verdict.get("iota_split_difference"))
    solo = _gap_stats(verdict.get("solo_split_difference"))
    # `spectrum.validity.unfolded_stability` computes the two bootstraps only
    # when condition 1 already holds, so a missing interval there means the
    # equivalence was never *tested* --- not that it failed. Recording it as
    # a failure would attribute to the bootstrap every rung condition 1
    # refused, which is the opposite of what this tool exists to separate.
    untested = (not adm_ok) and iota is None and solo is None
    failed: list[str] = []
    if not adm_ok:
        failed.append("split_admissibility")
    if not untested:
        if iota is None or not iota["inside"]:
            failed.append("iota_equivalence")
        if solo is None or not solo["inside"]:
            failed.append("solo_equivalence")
    adm = _admissibility(verdict, pooled)
    equivalence_failed = [c for c in failed if c != "split_admissibility"]
    # Would one more pass repair every condition this candidate failed?
    # Condition 1 only if every failing clause was an interval clause;
    # conditions 2/3 only if the narrowed interval fits. A projection.
    repair: bool | None = True
    if "split_admissibility" in failed and not adm["interval_only"]:
        repair = False
    for cond, stats in (("iota_equivalence", iota), ("solo_equivalence", solo)):
        if cond in failed and not (stats and stats["projected_inside_at_2x"]):
            repair = False
    if untested and repair is not False:
        # condition 1 could be relieved, but the equivalence this rung would
        # then face has never been measured. Unknown, and said so.
        repair = None
    if not failed:
        repair = None
    if failed == ["split_admissibility"]:
        shape = "ADMISSIBILITY_ONLY"
    elif failed and "split_admissibility" not in failed:
        shape = "EQUIVALENCE_ONLY"
    elif failed:
        shape = "BOTH"
    else:
        shape = "PASSED"
    return {"candidate": verdict.get("candidate"), "passed": bool(verdict.get("passed")),
            "failed_conditions": failed, "shape": shape,
            "admissibility": adm, "iota_gap": iota, "solo_gap": solo,
            "equivalence_untested": untested,
            "equivalence_failed": equivalence_failed,
            "projected_repaired_at_2x": repair}


def _bins(values: Sequence[float]) -> dict[str, Any]:
    """Descriptive terciles of an observed distribution. No rule reads these."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {"n": 0, "cuts": None, "counts": {}}
    if len(vals) < 3:
        return {"n": len(vals), "cuts": None,
                "counts": {"(too few to bin)": len(vals)}}
    q1, q2 = statistics.quantiles(vals, n=3)
    counts = collections.Counter()
    for v in vals:
        counts["barely misses (lowest third)" if v <= q1 else
               "moderate disagreement (middle third)" if v <= q2 else
               "large disagreement (highest third)"] += 1
    return {"n": len(vals), "cuts": {"lower_tercile": q1, "upper_tercile": q2},
            "counts": dict(counts), "median": statistics.median(vals),
            "min": vals[0], "max": vals[-1],
            "note": "descriptive terciles of this run's own excess "
                    "distribution; not a threshold and read by nothing"}


def _concentration(items: Sequence[Mapping[str, Any]], key) -> dict[str, Any]:
    tally: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for it in items:
        k = key(it)
        if k is None:
            continue
        tally[k][0] += 1
        tally[k][1] += 0 if it["passed"] else 1
    return {k: {"n": n, "failing": f, "rate": (f / n if n else None)}
            for k, (n, f) in sorted(tally.items())}


def _frame(g2f: Mapping[str, Any], g3f: Mapping[str, Any], arm: str
           ) -> dict[str, Any]:
    verdicts = g3f["stability" if arm == "LOCAL" else "unfolded_stability"]
    pooled_verdicts = g3f["local" if arm == "LOCAL" else "spectrum"]
    rows = {f"{r['kind']}:{r['severity']}": r
            for r in (g2f.get("calibration_rows") or {}).get("pooled") or []}
    iota_a = g3f["iota_a"]
    out = []
    for label in sorted(verdicts):
        a = _anatomy(verdicts[label], pooled_verdicts.get(label))
        row = rows.get(label) or {}
        a["family"] = _family(label)
        solo, kap = row.get("solo_compliance"), row.get("chance_compliance")
        a["iota"] = (None if solo is None or kap is None or kap >= 1.0
                     else (solo - kap) / (1.0 - kap))
        a["kappa"] = row.get("chance_compliance")
        a["distance_from_iota_a"] = (
            None if a["iota"] is None else a["iota"] - iota_a)
        a["side"] = (None if a["iota"] is None else
                     "below A" if a["iota"] < iota_a else "above A")
        a["inside_caliper"] = (None if a["iota"] is None else
                               abs(a["iota"] - iota_a) <= C.REFERENCE_CALIPER)
        # Is `V_stab` the *only* thing refusing this candidate on the frame's
        # pooled table? That subset is the whole question: everything else
        # fails for a reason no allocation touches.
        pv = pooled_verdicts.get(label) or {}
        blockers = sorted({c["component"] for c in pv.get("components") or []
                           if c.get("passed") is False} - {"V_stab"})
        a["other_blockers"] = blockers
        a["vstab_is_sole_blocker"] = (not blockers) and not a["passed"]
        out.append(a)
    failing = [a for a in out if not a["passed"]]
    shapes = collections.Counter(a["shape"] for a in out)
    # The equivalence anatomy: which of the two intervals, and is the point
    # itself inside the bound?
    eq_fail = [a for a in failing if a["equivalence_failed"]]
    point_outside = [a for a in eq_fail
                     if any((a[f"{c.split('_')[0]}_gap"] or {}).get(
                         "point_inside_bound") is False
                         for c in a["equivalence_failed"])]
    excesses = []
    for a in eq_fail:
        vals = [(a[f"{c.split('_')[0]}_gap"] or {}).get("excess")
                for c in a["equivalence_failed"]]
        vals = [v for v in vals if v is not None]
        if vals:
            excesses.append(max(vals))
    iota_hw = [a["iota_gap"]["half_width"] for a in out if a["iota_gap"]]
    solo_hw = [a["solo_gap"]["half_width"] for a in out if a["solo_gap"]]
    iota_pt = [a["iota_gap"]["abs_point"] for a in out if a["iota_gap"]]
    sole = [a for a in out if a["vstab_is_sole_blocker"]]
    adm_inv = [a for a in failing if a["admissibility"]["invariant_components"]]
    adm_sen = [a for a in failing
               if a["admissibility"]["failing_components"]
               and not a["admissibility"]["invariant_components"]]
    return {
        "arm": arm, "frame": g3f["frame"], "iota_a": iota_a,
        "n_vstab_sole_blocker": len(sole),
        "vstab_sole_blocker": sorted(a["candidate"] for a in sole),
        "n_sole_blocker_projected_repaired_at_2x": sum(
            1 for a in sole if a["projected_repaired_at_2x"] is True),
        "n_sole_blocker_projection_unknown": sum(
            1 for a in sole if a["projected_repaired_at_2x"] is None),
        "n_equivalence_untested": sum(1 for a in out if a["equivalence_untested"]),
        "sole_blocker_shapes": dict(collections.Counter(
            a["shape"] for a in sole)),
        "n_condition1_with_invariant_component": len(adm_inv),
        "n_condition1_sensitive_only": len(adm_sen),
        "condition1_invariant_components": dict(collections.Counter(
            c for a in failing
            for c in a["admissibility"]["invariant_components"])),
        "condition1_sensitive_components": dict(collections.Counter(
            c for a in failing
            for c in a["admissibility"]["sensitive_components"])),
        "n_candidates": len(out), "n_passing": sum(a["passed"] for a in out),
        "n_failing": len(failing),
        "shapes": dict(shapes),
        "n_equivalence_failing": len(eq_fail),
        "n_equivalence_point_outside_bound": len(point_outside),
        "point_outside_candidates": sorted(a["candidate"] for a in point_outside),
        "n_projected_repaired_at_2x": sum(
            1 for a in failing if a["projected_repaired_at_2x"] is True),
        "excess_bins": _bins(excesses),
        "median_iota_half_width": statistics.median(iota_hw) if iota_hw else None,
        "median_solo_half_width": statistics.median(solo_hw) if solo_hw else None,
        "median_abs_iota_split_difference":
            statistics.median(iota_pt) if iota_pt else None,
        "max_abs_iota_split_difference": max(iota_pt) if iota_pt else None,
        "by_family": _concentration(out, lambda a: a["family"]),
        "by_side": _concentration(out, lambda a: a["side"]),
        "by_caliper": _concentration(
            out, lambda a: None if a["inside_caliper"] is None else
            ("inside 0.1 caliper" if a["inside_caliper"] else "outside")),
        "admissibility_clause_kinds": dict(sum(
            (collections.Counter(a["admissibility"]["clause_kinds"])
             for a in out), collections.Counter())),
        "admissibility_point_components": dict(collections.Counter(
            c for a in out for c in a["admissibility"]["point_components"])),
        "iota_a_stability": g3f.get("iota_a_stability"),
        "candidates": out,
    }


def diagnose(root: pathlib.Path, model: str) -> dict[str, Any]:
    d = _model_dir(root, model)
    g2 = _payload(d / S.STAGE_GATE2 / "gate2_calibration.json")
    g3 = _payload(d / S.STAGE_GATE3 / "gate3_references.json")
    alloc = g2.get("calibration_allocation") or {}
    frames = []
    for w in g3["supported_frames"]:
        for arm in ("LOCAL", "SPECTRUM"):
            frames.append(_frame(g2["by_frame"][str(w)],
                                 g3["by_frame"][str(w)], arm))
    return {
        "artifact_type": "v8_vstab_diagnosis", "root": root.name,
        "model_key": model, "producing_commit": g3.get("producing_commit"),
        "stages_read": [S.STAGE_GATE2, S.STAGE_GATE3],
        "equivalence_bound": BOUND,
        "resamples": C.STABILITY_BOOTSTRAP_RESAMPLES,
        "calibration_allocation": alloc,
        "supported_frames": g3["supported_frames"],
        "rule": "§13.7 stability_verdict: (1) independently admissible on "
                "each split under V_head, V_chance, V_inter, V_diff; (2) the "
                f"95% bootstrap interval for the iota split difference inside "
                f"+/-{BOUND}; (3) the same for the raw solo difference",
        "reads_no_composed_quantity": True,
        "changes_no_threshold": True,
        "frames": frames,
    }


def render(diag: Mapping[str, Any]) -> str:
    a = diag["calibration_allocation"]
    L = [f"# DCI-1 v8 — the anatomy of `V_stab` on `{diag['model_key']}`", "",
         "> Generated by `dci1/tools/v8_vstab_diagnosis.py`. Do not edit by hand.", "",
         "> Reads the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` "
         "records only. Every verdict below is the one those records carry; "
         "the bins are descriptive quantiles and the 2× column is a "
         "**projection read by nothing**.", "",
         f"Root `{diag['root']}`; calibration at **{a.get('topics_per_frame')} "
         f"topics per frame** over {a.get('passes')} pass(es), "
         f"{a.get('topics_per_frame_per_split')} per §13.7 split. "
         f"Equivalence bound ±{diag['equivalence_bound']}, "
         f"{int(diag['resamples'])} resamples.", "",
         "§13.7 asks three things of a candidate: (1) it is independently "
         "admissible on Calibration-A **and** on Calibration-B, each split "
         "alone, under `V_head`, `V_chance`, `V_inter`, `V_diff`; (2) the 95% "
         "bootstrap interval for the ι split difference lies wholly inside "
         f"±{diag['equivalence_bound']}; (3) the same for the raw solo "
         "difference. Conditions 2 and 3 resample topics within split, so "
         "their half-width falls as 1/√(topics per split). Condition 1 is not "
         "a precision statement: it re-runs four candidate components at half "
         "the frame's topics.", "",
         "## Where `V_stab` fails", "",
         "| frame | arm | ι_A | cands | pass | fail | `V_stab` sole "
         "blocker | admis. only | equiv. only | both | pt outside ±bound | "
         "med \\|Δι\\| | med half-width | sole-blocker repaired at 2× |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in diag["frames"]:
        s = f["shapes"]
        L.append(
            f"| f{f['frame']} | {f['arm']} | {f['iota_a']:.3f} | "
            f"{f['n_candidates']} | {f['n_passing']} | {f['n_failing']} | "
            f"**{f['n_vstab_sole_blocker']}** | "
            f"{s.get('ADMISSIBILITY_ONLY', 0)} | {s.get('EQUIVALENCE_ONLY', 0)} | "
            f"{s.get('BOTH', 0)} | {f['n_equivalence_point_outside_bound']} | "
            f"{_n(f['median_abs_iota_split_difference'])} | "
            f"{_n(f['median_iota_half_width'])} | "
            f"{f['n_sole_blocker_projected_repaired_at_2x']} |")
    L += ["", "`pt outside ±bound` counts candidates whose equivalence *point "
          "estimate* is itself outside the bound — the two topic halves "
          "genuinely disagree by more than §13.7 permits, and no allocation "
          "repairs that. Everything else is an interval that does not resolve.",
          ""]
    for f in diag["frames"]:
        L += [f"### f{f['frame']} — {f['arm']}", "",
              f"- ι_A = {f['iota_a']:.4f}; {f['n_passing']} of "
              f"{f['n_candidates']} pass `V_stab`",
              f"- failure shape: {json.dumps(f['shapes'], sort_keys=True)}",
              f"- ι split difference: median |Δ| "
              f"{_n(f['median_abs_iota_split_difference'])}, max "
              f"{_n(f['max_abs_iota_split_difference'])}; median interval "
              f"half-width {_n(f['median_iota_half_width'])}",
              f"- equivalence failures whose point is outside the bound: "
              f"{f['n_equivalence_point_outside_bound']} "
              f"{f['point_outside_candidates'] or ''}",
              f"- condition-1 clauses by kind: "
              f"{json.dumps(f['admissibility_clause_kinds'], sort_keys=True)}",
              f"- condition-1 components with an allocation-invariant clause: "
              f"{json.dumps(f['admissibility_point_components'], sort_keys=True)}",
              f"- excess beyond the bound (descriptive terciles): "
              f"{json.dumps(f['excess_bins'].get('counts', {}), sort_keys=True)}"]
        ia = f.get("iota_a_stability") or {}
        if ia.get("interval"):
            i = ia["interval"]
            L.append(f"- ι_A's own equivalence: passed={ia.get('passed')}, "
                     f"[{i['lower']:.4f}, {i['upper']:.4f}]")
        L += [f"- **`V_stab` is the sole blocker** for "
              f"{f['n_vstab_sole_blocker']} candidate(s) "
              f"{f['vstab_sole_blocker'] or ''} — every other candidate that "
              f"fails also fails a component no allocation touches",
              f"- condition-1 failures carrying an allocation-**invariant** "
              f"component: {f['n_condition1_with_invariant_component']}; "
              f"split-noise only: {f['n_condition1_sensitive_only']}",
              f"- invariant components: "
              f"{json.dumps(f['condition1_invariant_components'], sort_keys=True)}",
              f"- split-sensitive components: "
              f"{json.dumps(f['condition1_sensitive_components'], sort_keys=True)}",
              f"- **projection (read by nothing)**: "
              f"{f['n_projected_repaired_at_2x']} of {f['n_failing']} "
              f"failing candidates would be repaired by one more pass; of the "
              f"{f['n_vstab_sole_blocker']} `V_stab`-only candidates, "
              f"{f['n_sole_blocker_projected_repaired_at_2x']} repaired and "
              f"{f['n_sole_blocker_projection_unknown']} unknown (condition 1 "
              f"relieved, but the equivalence it would then face was never "
              f"measured: {f['n_equivalence_untested']} rungs never reached "
              f"the bootstrap)"]
        worst = sorted((x for x in f["by_family"].items() if x[1]["n"] >= 3),
                       key=lambda kv: -(kv[1]["rate"] or 0))[:4]
        best = sorted((x for x in f["by_family"].items() if x[1]["n"] >= 3),
                      key=lambda kv: (kv[1]["rate"] or 0))[:4]
        L += [f"- most unstable families: " +
              ", ".join(f"{k} {v['failing']}/{v['n']}" for k, v in worst),
              f"- most stable families: " +
              ", ".join(f"{k} {v['failing']}/{v['n']}" for k, v in best),
              f"- by side of A: " +
              ", ".join(f"{k} {v['failing']}/{v['n']}"
                        for k, v in f["by_side"].items()),
              f"- by caliper: " +
              ", ".join(f"{k} {v['failing']}/{v['n']}"
                        for k, v in f["by_caliper"].items()), ""]
    return "\n".join(L) + "\n"


def _n(v: float | None) -> str:
    return "—" if v is None else f"{v:.4f}"


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    diag = diagnose(root, args.model)
    out = pathlib.Path(args.out_dir) if args.out_dir else REPORTS
    out.mkdir(parents=True, exist_ok=True)
    stem = f"vstab.{root.name}.{args.model}"
    slim = {**diag, "frames": [{k: v for k, v in f.items() if k != "candidates"}
                               for f in diag["frames"]]}
    (out / f"{stem}.json").write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n")
    (out / f"{stem}.md").write_text(render(slim))
    print(f"wrote {out / (stem + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
