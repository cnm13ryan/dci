#!/usr/bin/env python
"""The wording-policy decision report for one v8 pilot root (read-only).

    .venv/bin/python tools/v8_wording_decision.py --root evidence/dci1v8-pilot \
        [--model qwen3-4b-instruct-2507] [--namespace pilot|synthetic] \
        [--out reports/dci1v8dev] [--exemplars 3] [--outputs-per-frame 2]

Reads the signed Gate-2 and Gate-3 records (hash and signature verified) and
the Gate-2 scored rows of one replication and writes
``<out>/wording_decision[.synthetic].{md,json}`` answering, for the
researcher, the five questions of 2026-08-30:

1. per (family, q): the four frame-specific ι, their SE, the cross-frame
   spread and the descriptive class (``CONSISTENT`` / ``UNRESOLVED`` /
   ``WORDING_SENSITIVE``, ``run/wording.py``), on the pooled calibration
   basis and on each split;
2. whether any frame is a systematic outlier over many families/rungs
   (leave-one-out deviation of each frame from the other three, per rung);
3. whether apparent wording differences replicate across the two disjoint
   calibration splits (Calibration-A vs Calibration-B);
4. whether wording-sensitive rungs touch the reference set (LOCAL-valid,
   SPECTRUM-valid, core references, selected spectrum points, backups ---
   Gate 3's ``wording_sensitive_rungs``);
5. for the strongest cases, the four exact prompts and representative
   outputs with their observed counts.

It ends with the evidence relevant to the three researcher options and
chooses none of them: no frame is selected or discarded here.

**Composed outcomes are never read.** The v8 pilot generates no composed
cell; this tool additionally refuses any scored row with more than one
present constraint, reads no stage beyond ``GATE_3_REFERENCES``, and names
no interference quantity. Base: Gate 2 (48 topics × 4 draws per frame per
split); the pre-screen's 6-topic frames are not used here.

If the root has no Gate-2 record the report says so and lists what must
finish first; the exit status is 2.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dci1v4.errors import IntegrityError, ProtocolError  # noqa: E402
from dci1v7.protocol import constants as C  # noqa: E402
from dci1v7.verifiers.constraints import (FAMILIES, TIER1_FAMILY_IDS,  # noqa: E402
                                          TIER2_FAMILY_IDS, TIER3_FAMILY_IDS)
from dci1v8dev.run import stages as S  # noqa: E402
from dci1v8dev.run import transitions, wording as W  # noqa: E402
from dci1v8dev.run.context import (model_tree, pilot_context,  # noqa: E402
                                   synthetic_context)
from dci1v4.engine import fs  # noqa: E402
from dci1v4.engine.signing import verify_signed  # noqa: E402
from dci1v7.stages.regime import grid_resolution  # noqa: E402
from dci1v8dev.run.execute import UNCONSTRAINED_ARM, row_accounting  # noqa: E402
from dci1v8dev.wordings import v8_wordings  # noqa: E402

STAGES_READ = (S.STAGE_GATE2, S.STAGE_GATE3)
BOUND = S.WORDING_REFERENCE_BOUND
FRAMES = tuple(range(C.N_WORDINGS))
SPLITS = (C.CALIBRATION_A, C.CALIBRATION_B)


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def _context(root: Path, namespace: str):
    if namespace == "pilot":
        return pilot_context(root)
    if namespace == "synthetic":
        return synthetic_context(root)
    raise ProtocolError(f"unknown namespace {namespace!r}")


def _record(tree, stage: str) -> dict[str, Any] | None:
    if not tree.stage_record(stage).exists():
        return None
    return transitions.read_stage_record(tree, stage)


def _scored_rows(tree) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Every scored Gate-2 row and the rendered prompt of every row id.
    Refuses a composed row: the pilot has none and this report reads none."""
    rows: list[dict[str, Any]] = []
    prompts: dict[str, str] = {}
    base = tree.backend_runs(S.STAGE_GATE2)
    if not base.exists():
        return rows, prompts
    for run_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        scored = run_dir / "scored.jsonl"
        design = run_dir / "design.jsonl"
        if design.exists():
            for line in design.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    prompts[d["row_id"]] = d.get("user_prompt", "")
        if not scored.exists():
            continue
        for line in scored.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            present = [s for s in r["scores"] if s.get("present")]
            if len(present) > 1 or len(r.get("slots") or ()) > 1 \
                    or int(r.get("load") or 0) > 1:
                raise ProtocolError(
                    f"{run_dir.name}:{r['row_id']} states more than one "
                    f"constraint; a composed row is never read by this report")
            rows.append(r)
    return rows, prompts


def _terminal(tree) -> dict[str, Any] | None:
    """The signed terminal report's payload, if the replication is terminal."""
    path = tree.terminal_report
    if not path.exists():
        return None
    return verify_signed(fs.read_json(path), tree.context.signing_key_path,
                         where=f"{tree.model_key}:terminal")


def _gate2_from_rows(tree, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The Gate-2 wording blocks recomputed from the stage's scored rows, for
    a replication that ended terminal *inside* Gate 2 (after the A and B
    grids, before the candidates). Unsigned: the stage wrote no record; the
    rows carry their own provenance and the terminal report is signed."""
    by_frame = {C.CALIBRATION_A: W.frame_table(rows, split=C.CALIBRATION_A),
                C.CALIBRATION_B: W.frame_table(rows, split=C.CALIBRATION_B),
                "pooled": W.frame_table(rows)}
    comparison = W.frame_comparison(by_frame["pooled"], bound=BOUND)
    base = tree.backend_runs(S.STAGE_GATE2)
    accounting = {p.name: row_accounting(p) for p in sorted(base.iterdir())
                  if p.is_dir() and (p / "design.jsonl").exists()}
    return {
        "wording_by_frame": by_frame,
        "frame_comparison_pooled": comparison,
        "ladders_by_frame_pooled": W.ladders_by_frame(by_frame["pooled"]),
        "wording_dependence_pooled": W.wording_dependence(comparison),
        "split_stability_by_frame": W.stability_by_frame(
            by_frame[C.CALIBRATION_A], by_frame[C.CALIBRATION_B], bound=BOUND,
            names=(C.CALIBRATION_A, C.CALIBRATION_B)),
        "rungs_by_wording_class": W.sensitive_rungs(comparison),
        "iota_a": None, "iota_a_by_split": None,
        "chance_basis": {"basis": "unconstrained cell of the grid rows' topic "
                                  "set (§13.2); computed by this report from "
                                  "the rows, not by the stage"},
        "row_accounting": accounting,
        "recomputed_from_rows": True,
    }


def regime_by_frame(gate2: Mapping[str, Any], *, pooled_curve: Mapping[str, float] | None
                    ) -> dict[str, Any]:
    """§12.3 on each frame's own A curve: would the target grid resolve the
    band under that frame alone? The stage applies the rule to the curve
    pooled over the four frames (v7's reading of §7.8); the per-frame
    curves are what the wording policy turns on."""
    tab = gate2["wording_by_frame"]["pooled"]
    low, high = C.TARGET_BAND
    out: dict[str, Any] = {"band": [low, high], "grid": list(C.TARGET_GRID),
                           "by_frame": {}, "pooled": None}
    for w in FRAMES:
        curve = {e["severity"]: e["exact_compliance"] for e in tab
                 if e["kind"] == "A" and int(e["frame"]) == w
                 and e["exact_compliance"] is not None}
        if not curve:
            continue
        res = grid_resolution(curve, band=(low, high), grid=C.TARGET_GRID)
        inside = sorted(q for q, p in curve.items() if low <= p <= high)
        out["by_frame"][str(w)] = {
            "curve": {str(q): curve[q] for q in sorted(curve)},
            "severities_inside_band": inside,
            "grid_resolution_insufficient": bool(res["insufficient"]),
            "straddling_pairs": res["straddling_pairs"],
        }
    if pooled_curve:
        pc = {int(q): float(p) for q, p in pooled_curve.items()}
        res = grid_resolution(pc, band=(low, high), grid=C.TARGET_GRID)
        out["pooled"] = {"curve": {str(q): pc[q] for q in sorted(pc)},
                         "severities_inside_band": sorted(q for q, p in pc.items()
                                                          if low <= p <= high),
                         "grid_resolution_insufficient": bool(res["insufficient"]),
                         "straddling_pairs": res["straddling_pairs"]}
    return out


# --------------------------------------------------------------------------
# arithmetic
# --------------------------------------------------------------------------

def _mean(v: Sequence[float]) -> float | None:
    return sum(v) / len(v) if v else None


def _median(v: Sequence[float]) -> float | None:
    if not v:
        return None
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _rank(v: Sequence[float]) -> list[float]:
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def _spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3:
        return None
    rx, ry = _rank(x), _rank(y)
    mx, my = _mean(rx), _mean(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def _fmt(v: Any, nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _tier(kind: str) -> int | None:
    for n, ids in ((1, TIER1_FAMILY_IDS), (2, TIER2_FAMILY_IDS),
                   (3, TIER3_FAMILY_IDS)):
        if kind in ids:
            return n
    return None


def _rung_key(label: str) -> tuple[str, int]:
    kind, _, q = label.rpartition(":")
    return kind, int(q)


# --------------------------------------------------------------------------
# 1. per (family, q): four frames, SE, spread, class --- pooled and per split
# --------------------------------------------------------------------------

def _chance_of(table: Sequence[Mapping[str, Any]], label: str) -> float | None:
    for e in table:
        if e["candidate"] == label and e.get("chance") is not None:
            return e["chance"]
    return None


def _max_abs_p_difference(c: Mapping[str, Any]) -> float | None:
    """The largest pairwise difference in exact compliance (not ι): on a
    rung whose chance κ is high, ι = (p − κ)/(1 − κ) amplifies a one-answer
    difference by 1/(1 − κ); the reader needs both."""
    ps = [f["exact_compliance"] for f in c["frames"].values()
          if f and f.get("exact_compliance") is not None]
    return (max(ps) - min(ps)) if len(ps) >= 2 else None


def rung_table(gate2: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_frame = gate2["wording_by_frame"]
    pooled = gate2["frame_comparison_pooled"]
    per_split = {split: W.frame_comparison(by_frame[split], bound=BOUND)
                 for split in SPLITS}
    out = []
    for label in sorted(pooled, key=_rung_key):
        c = pooled[label]
        kind, q = _rung_key(label)
        entry = {
            "candidate": label, "family": kind, "severity": q,
            "tier": _tier(kind),
            "frames": {str(w): c["frames"].get(str(w)) for w in FRAMES},
            "chance": _chance_of(by_frame["pooled"], label),
            "max_abs_difference_compliance": _max_abs_p_difference(c),
            "n_frames_measured": c["n_frames_measured"],
            "spread": c["spread"],
            "max_abs_difference": c["max_abs_difference"],
            "max_abs_z": c["max_abs_z"],
            "class": c["class"],
            "class_by_split": {split: (per_split[split].get(label) or {}).get("class")
                               for split in SPLITS},
            "spread_by_split": {split: (per_split[split].get(label) or {}).get("spread")
                                for split in SPLITS},
        }
        out.append(entry)
    return out


# --------------------------------------------------------------------------
# 2. is any frame a systematic outlier?
# --------------------------------------------------------------------------

def frame_outliers(gate2: Mapping[str, Any]) -> dict[str, Any]:
    """Per frame, over every rung with all four frames measured: the frame's
    ι minus the mean of the other three, its z, whether it is the extreme
    frame of the rung, and the rate at which its deviation is resolved and
    beyond the bound. A frame that is an outlier on many rungs shows a
    consistent sign, a high share of extremes and a mean |z| well above the
    others; the expected share of extremes under exchangeability is 1/2
    (either extreme) and 1/4 (the hardest)."""
    pooled = gate2["frame_comparison_pooled"]
    stats = {str(w): {"n_rungs": 0, "deviations": [], "z": [],
                      "n_hardest": 0, "n_easiest": 0, "n_extreme": 0,
                      "n_beyond_bound_resolved": 0,
                      "beyond_bound_resolved_rungs": []} for w in FRAMES}
    n_complete = 0
    for label, c in pooled.items():
        fr = {w: c["frames"].get(str(w)) for w in FRAMES}
        if any(f is None or f["iota"] is None or f["se_iota"] is None
               for f in fr.values()):
            continue
        n_complete += 1
        iotas = {w: fr[w]["iota"] for w in FRAMES}
        lo, hi = min(iotas.values()), max(iotas.values())
        # ties share the credit: a rung where two frames tie at the minimum
        # counts 1/2 for each (a fixture with many exact ties would otherwise
        # credit frame 0 through dict order)
        tied_lo = [w for w in FRAMES if iotas[w] == lo]
        tied_hi = [w for w in FRAMES if iotas[w] == hi]
        for w in FRAMES:
            others = [iotas[o] for o in FRAMES if o != w]
            dev = iotas[w] - _mean(others)
            se = math.sqrt(fr[w]["se_iota"] ** 2
                           + sum(fr[o]["se_iota"] ** 2 for o in FRAMES
                                 if o != w) / 9.0)
            z = dev / se if se > 0 else None
            st = stats[str(w)]
            st["n_rungs"] += 1
            st["deviations"].append(dev)
            if z is not None:
                st["z"].append(z)
            h = (1.0 / len(tied_lo)) if w in tied_lo else 0.0
            e = (1.0 / len(tied_hi)) if w in tied_hi else 0.0
            st["n_hardest"] += h
            st["n_easiest"] += e
            st["n_extreme"] += (h + e) if lo != hi else (1.0 / len(FRAMES)) * 2
            if abs(dev) > BOUND and z is not None and abs(z) >= W.Z_95:
                st["n_beyond_bound_resolved"] += 1
                st["beyond_bound_resolved_rungs"].append(label)
    summary = {}
    for w, st in stats.items():
        n = st["n_rungs"]
        devs, zs = st["deviations"], st["z"]
        summary[w] = {
            "n_rungs": n,
            "mean_deviation": _mean(devs),
            "median_deviation": _median(devs),
            "mean_abs_deviation": _mean([abs(d) for d in devs]),
            "mean_abs_z": _mean([abs(z) for z in zs]),
            "share_negative_deviation": (
                sum(1 for d in devs if d < 0) / n if n else None),
            "share_hardest": st["n_hardest"] / n if n else None,
            "share_easiest": st["n_easiest"] / n if n else None,
            "share_extreme": st["n_extreme"] / n if n else None,
            "n_beyond_bound_resolved": st["n_beyond_bound_resolved"],
            "beyond_bound_resolved_rungs": sorted(
                st["beyond_bound_resolved_rungs"], key=_rung_key),
        }
    return {"n_rungs_with_all_frames": n_complete,
            "expected_share_hardest_if_exchangeable": 1.0 / len(FRAMES),
            "expected_share_extreme_if_exchangeable": 2.0 / len(FRAMES),
            "by_frame": summary,
            "reading": "leave-one-out: each frame's ι minus the mean of the "
                       "other three, per rung; a systematic outlier keeps "
                       "one sign and is the extreme far more often than "
                       "chance; ties share the credit; descriptive only"}


# --------------------------------------------------------------------------
# 3. do apparent wording differences replicate across the splits?
# --------------------------------------------------------------------------

def split_replication(gate2: Mapping[str, Any],
                      rungs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_frame = gate2["wording_by_frame"]
    cmp = {split: W.frame_comparison(by_frame[split], bound=BOUND)
           for split in SPLITS}
    stab = gate2["split_stability_by_frame"]
    # (a) the per-frame stability of ι between A and B (Gate 2's block)
    per_frame: dict[str, dict[str, Any]] = {}
    for key, e in stab["entries"].items():
        w = str(e["frame"])
        d = per_frame.setdefault(w, {"n": 0, "inside": 0, "abs_diff": []})
        d["n"] += 1
        d["inside"] += int(e["inside_bound"])
        d["abs_diff"].append(abs(e["difference"]))
    for w, d in per_frame.items():
        d["share_inside_bound"] = d["inside"] / d["n"] if d["n"] else None
        d["mean_abs_difference"] = _mean(d["abs_diff"])
        del d["abs_diff"]
    # (b) does the pooled ordering/difference replicate on both halves?
    flagged = []
    spreads_a, spreads_b = [], []
    for r in rungs:
        label = r["candidate"]
        ca, cb = cmp[C.CALIBRATION_A].get(label), cmp[C.CALIBRATION_B].get(label)
        if ca and cb and ca["spread"] is not None and cb["spread"] is not None:
            spreads_a.append(ca["spread"])
            spreads_b.append(cb["spread"])
        if r["class"] not in ("WORDING_SENSITIVE", "UNRESOLVED"):
            continue
        pooled_worst = max(gate2["frame_comparison_pooled"][label]["pairwise"],
                           key=lambda p: abs(p["difference"]), default=None)
        if pooled_worst is None:
            continue
        a, b = pooled_worst["frames"]

        def _pair(c):
            if not c:
                return None
            for p in c["pairwise"]:
                if p["frames"] == [a, b]:
                    return p
            return None
        pa, pb = _pair(ca), _pair(cb)
        same_sign = (pa is not None and pb is not None
                     and pa["difference"] * pb["difference"] > 0)
        both_beyond = bool(pa and pb and pa["beyond_bound"] and pb["beyond_bound"])
        both_resolved = bool(pa and pb and pa["resolved"] and pb["resolved"])
        order_a = ([w for w, _ in sorted(((w, f["iota"]) for w, f in ca["frames"].items()
                                          if f["iota"] is not None),
                                         key=lambda t: t[1])] if ca else None)
        order_b = ([w for w, _ in sorted(((w, f["iota"]) for w, f in cb["frames"].items()
                                          if f["iota"] is not None),
                                         key=lambda t: t[1])] if cb else None)
        flagged.append({
            "candidate": label, "class_pooled": r["class"],
            "worst_pair": [a, b],
            "difference_pooled": pooled_worst["difference"],
            "difference_a": pa["difference"] if pa else None,
            "difference_b": pb["difference"] if pb else None,
            "z_a": pa["z"] if pa else None, "z_b": pb["z"] if pb else None,
            "same_sign_on_both_splits": same_sign,
            "beyond_bound_on_both_splits": both_beyond,
            "resolved_on_both_splits": both_resolved,
            "class_a": ca["class"] if ca else None,
            "class_b": cb["class"] if cb else None,
            "frame_order_hardest_first_a": order_a,
            "frame_order_hardest_first_b": order_b,
            "replicates": same_sign and both_beyond,
        })
    n_flag = len(flagged)
    return {
        "per_frame_stability_a_vs_b": per_frame,
        "gate2_split_stability": {k: stab[k] for k in
                                  ("n_compared", "n_inside_bound",
                                   "share_inside_bound", "reference_bound")},
        "spread_correlation_a_vs_b": {
            "n_rungs": len(spreads_a),
            "spearman": _spearman(spreads_a, spreads_b),
            "reading": "rank correlation of the cross-frame spread on A with "
                       "the spread on B over rungs: a real frame effect "
                       "reproduces the same large spreads on fresh topics; "
                       "sampling noise does not"},
        "flagged_rungs": flagged,
        "n_flagged": n_flag,
        "n_replicating": sum(1 for f in flagged if f["replicates"]),
        "n_same_sign": sum(1 for f in flagged if f["same_sign_on_both_splits"]),
        "n_resolved_on_both": sum(1 for f in flagged if f["resolved_on_both_splits"]),
    }


# --------------------------------------------------------------------------
# 4. do the sensitive rungs touch the reference set?
# --------------------------------------------------------------------------

def reference_exposure(gate3: Mapping[str, Any] | None,
                       rungs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if gate3 is None:
        return {"available": False,
                "reason": f"{S.STAGE_GATE3} has not been reached; the "
                          f"reference set does not exist yet"}
    klass = {r["candidate"]: r["class"] for r in rungs}
    local = gate3["local"]
    spectrum = gate3["spectrum"]
    core = {f"{f}:{q}" for f, q in (gate3.get("core_references") or {}).items()}
    selected = {p["candidate"] for p in
                (gate3.get("spectrum_selection") or {}).get("points", ())}
    backup_families = set((gate3.get("backups") or {}).get("backups") or ())

    def _tally(labels: Sequence[str]) -> dict[str, Any]:
        counts = Counter(klass.get(l) for l in labels)
        return {"n": len(labels),
                "by_class": {k: counts.get(k, 0) for k in W.CLASSES},
                "unclassified": counts.get(None, 0),
                "sensitive": sorted((l for l in labels
                                     if klass.get(l) == "WORDING_SENSITIVE"),
                                    key=_rung_key),
                "unresolved": sorted((l for l in labels
                                      if klass.get(l) == "UNRESOLVED"),
                                     key=_rung_key)}
    local_valid = sorted((l for l, v in local.items() if v.get("passed")),
                         key=_rung_key)
    spectrum_valid = sorted((l for l, v in spectrum.items() if v.get("passed")),
                            key=_rung_key)
    backup_rungs = sorted((l for l in local_valid
                           if _rung_key(l)[0] in backup_families), key=_rung_key)
    return {
        "available": True,
        "gate3_block": gate3["wording_sensitive_rungs"],
        "survival": gate3["survival"],
        "sets": {
            "local_valid_candidates": _tally(local_valid),
            "spectrum_valid_candidates": _tally(spectrum_valid),
            "selected_local_references_core": _tally(sorted(core, key=_rung_key)),
            "selected_spectrum_points": _tally(sorted(selected, key=_rung_key)),
            "backup_family_rungs_local_valid": _tally(backup_rungs),
        },
        "backup_families": sorted(backup_families),
        "core_references": sorted(core, key=_rung_key),
        "selected_spectrum_points": sorted(selected, key=_rung_key),
    }


# --------------------------------------------------------------------------
# 5. the strongest cases: four prompts, outputs, counts
# --------------------------------------------------------------------------

def exemplars(rungs: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]],
              prompts: Mapping[str, str], *, n_cases: int, per_frame: int,
              snippet: int = 280) -> dict[str, Any]:
    sensitive = [r for r in rungs if r["class"] == "WORDING_SENSITIVE"]
    basis = "WORDING_SENSITIVE rungs ordered by |z| then spread"
    pool = sorted(sensitive, key=lambda r: (-(r["max_abs_z"] or 0),
                                            -(r["spread"] or 0)))
    if not pool:
        basis = ("no WORDING_SENSITIVE rung: the largest-spread rungs are "
                 "shown instead (all CONSISTENT or UNRESOLVED)")
        pool = sorted((r for r in rungs if r["spread"] is not None),
                      key=lambda r: -(r["spread"] or 0))
    cases = []
    by_rung_frame: dict[tuple[str, int], list[Mapping[str, Any]]] = {}
    for r in rows:
        if r.get("load") != 1 or r.get("frame") is None:
            continue
        present = [s for s in r["scores"] if s.get("present")]
        if len(present) != 1:
            continue
        s = present[0]
        by_rung_frame.setdefault((f"{s['kind']}:{s['severity']}", int(r["frame"])),
                                 []).append(r)
    for r in pool[:n_cases]:
        kind, q = r["family"], r["severity"]
        try:
            wordings = list(v8_wordings(kind, q))
        except ProtocolError as exc:
            wordings = [f"<not renderable: {exc}>"] * len(FRAMES)
        frames_out = {}
        # one topic shown under every frame, when one topic saw all four
        topics_by_frame = {w: {x["topic_id"] for x in by_rung_frame.get((r["candidate"], w), [])}
                           for w in FRAMES}
        for w in FRAMES:
            frows = sorted(by_rung_frame.get((r["candidate"], w), []),
                           key=lambda x: (x["topic_id"], x["draw_index"]))
            present = [next(s for s in x["scores"] if s.get("present")) for x in frows]
            counts = Counter(int(s["statistic"]) if s.get("statistic") is not None
                             else None for s in present)
            k = sum(1 for s in present if s["passed"])
            compliant = [x for x in frows if next(s for s in x["scores"]
                                                  if s.get("present"))["passed"]]
            non = [x for x in frows if not next(s for s in x["scores"]
                                                if s.get("present"))["passed"]]
            picks = compliant[:max(1, per_frame // 2)] + non[:max(1, per_frame - per_frame // 2)]
            frames_out[str(w)] = {
                "constraint_sentence": wordings[w],
                "n_rows": len(frows), "n_topics": len(topics_by_frame[w]),
                "k_exact_compliant": k,
                "exact_compliance": (k / len(frows)) if frows else None,
                "iota": (r["frames"].get(str(w)) or {}).get("iota"),
                "se_iota": (r["frames"].get(str(w)) or {}).get("se_iota"),
                "observed_count_distribution": {
                    str(c): n for c, n in sorted(counts.items(),
                                                 key=lambda t: (t[0] is None, t[0]))},
                "full_prompt_example": prompts.get(frows[0]["row_id"]) if frows else None,
                "outputs": [{
                    "row_id": x["row_id"], "topic_id": x["topic_id"],
                    "topic_split": x["topic_split"], "draw_index": x["draw_index"],
                    "observed_count": next(s for s in x["scores"]
                                           if s.get("present"))["statistic"],
                    "exact_compliant": bool(next(s for s in x["scores"]
                                                 if s.get("present"))["passed"]),
                    "word_count": x.get("word_count"),
                    "truncated": x.get("truncated"),
                    "response_head": (x.get("raw_response") or "")[:snippet],
                } for x in picks],
            }
        cases.append({
            "candidate": r["candidate"], "class": r["class"],
            "chance": r.get("chance"),
            "max_abs_difference_compliance": r.get("max_abs_difference_compliance"),
            "spread": r["spread"], "max_abs_z": r["max_abs_z"],
            "class_by_split": r["class_by_split"],
            "frames": frames_out,
        })
    return {"basis": basis, "n_cases": len(cases), "cases": cases}


# --------------------------------------------------------------------------
# the three options: what the evidence says about each (no choice made)
# --------------------------------------------------------------------------

def option_evidence(gate2: Mapping[str, Any], rungs: Sequence[Mapping[str, Any]],
                    outliers: Mapping[str, Any], replication: Mapping[str, Any],
                    exposure: Mapping[str, Any]) -> dict[str, Any]:
    dep = gate2["wording_dependence_pooled"]
    n = len(rungs)
    shares = Counter(r["class"] for r in rungs)
    tau2 = dep.get("tau2_median")
    within = _median([_mean([f["se_iota"] ** 2 for f in r["frames"].values()
                             if f and f.get("se_iota") is not None]) or 0.0
                      for r in rungs if r["n_frames_measured"] >= 2])
    icc = (tau2 / (tau2 + within)) if (tau2 is not None and within
                                        and tau2 + within > 0) else None
    by_frame = outliers["by_frame"]
    most_extreme = max(by_frame, key=lambda w: by_frame[w]["share_extreme"] or 0) \
        if by_frame else None
    sets = exposure.get("sets") or {}
    touched = {name: t["by_class"]["WORDING_SENSITIVE"] for name, t in sets.items()}
    return {
        "retain_all_frames": {
            "share_consistent": shares.get("CONSISTENT", 0) / n if n else None,
            "share_unresolved": shares.get("UNRESOLVED", 0) / n if n else None,
            "share_wording_sensitive": shares.get("WORDING_SENSITIVE", 0) / n if n else None,
            "tau_median": dep.get("tau_median"),
            "spread_median": dep.get("spread_median"),
            "spread_q90": dep.get("spread_q90"),
            "sensitive_rungs_replicating_on_both_splits": replication["n_replicating"],
            "reference_set_rungs_that_are_sensitive": touched,
            "reading": "if nearly every rung is CONSISTENT, τ is small next to "
                       "the SE, and no sensitive rung replicates on both splits "
                       "or touches the reference set, pooling the four frames "
                       "as one instrument (v7's reading of §7.8) is supported "
                       "by this pilot",
        },
        "retain_specified_subset": {
            "frame_outlier_summary": {w: {k: by_frame[w][k] for k in
                                          ("n_rungs", "mean_deviation",
                                           "share_hardest", "share_easiest",
                                           "share_extreme", "mean_abs_z",
                                           "n_beyond_bound_resolved")}
                                      for w in by_frame},
            "most_often_extreme_frame": most_extreme,
            "expected_share_extreme_if_exchangeable":
                outliers["expected_share_extreme_if_exchangeable"],
            "reading": "a subset is supported only if one (or two) frames are "
                       "the resolved outlier on many rungs with one sign, and "
                       "that outlier status replicates on both splits; the "
                       "per-frame ladders (Gate 2 ladders_by_frame_pooled) say "
                       "whether the remaining frames still carry the ladder",
        },
        "model_frame_variation": {
            "tau2_median": tau2,
            "within_frame_sampling_variance_median": within,
            "icc_like_ratio": icc,
            "n_rungs_with_resolved_frame_effect": shares.get("WORDING_SENSITIVE", 0),
            "n_rungs_with_all_frames": outliers["n_rungs_with_all_frames"],
            "split_spread_spearman": replication["spread_correlation_a_vs_b"]["spearman"],
            "reading": "modelling the frame (a random or fixed frame term in "
                       "ι) is supported when τ² is a non-trivial share of the "
                       "total variance and the spreads reproduce across the "
                       "splits, but no single frame is the culprit",
        },
        "decision_made_here": None,
        "no_frame_discarded": True,
    }


# --------------------------------------------------------------------------
# assembly + rendering
# --------------------------------------------------------------------------

def build(root: Path, *, model_key: str, namespace: str, n_cases: int,
          per_frame: int) -> dict[str, Any]:
    ctx = _context(root, namespace)
    tree = model_tree(ctx, model_key)
    reached = transitions.stage_reached(tree)
    head = {
        "root": str(root), "namespace": namespace, "study_id": ctx.study_id,
        "model_key": model_key, "stage_reached": reached,
        "stages_read": list(STAGES_READ),
        "basis": "GATE_2_CALIBRATION (pooled = Calibration-A ∪ Calibration-B; "
                 "each split reported separately); the pre-screen is not used",
        "reference_bound": BOUND,
        "composed_outcomes_read": False,
        "synthetic": namespace == "synthetic",
    }
    terminal = _terminal(tree)
    head["terminal"] = ({"gate": terminal.get("gate"), "status": terminal.get("status"),
                         "criterion": terminal.get("criterion")} if terminal else None)
    gate2 = _record(tree, S.STAGE_GATE2)
    rows, prompts = _scored_rows(tree)
    head["signed_gate2_record"] = gate2 is not None
    if gate2 is None and rows and terminal and terminal.get("gate") == S.STAGE_GATE2:
        gate2 = _gate2_from_rows(tree, rows)
        head["basis"] = (f"UNSIGNED: {S.STAGE_GATE2} ended terminal "
                         f"({terminal.get('status')}) after the A and B grids and "
                         f"before any candidate; the per-frame tables below are "
                         f"recomputed by this report from the stage's {len(rows)} "
                         f"scored grid rows (A and B only). The pre-screen is not used")
    if gate2 is None:
        needed = list(S.STAGE_SEQUENCE[:S.STAGE_SEQUENCE.index(S.STAGE_GATE2) + 1])
        return {**head, "available": False,
                "reason": f"no {S.STAGE_GATE2} record under {tree.root}"
                          + (f"; terminal {terminal.get('status')} at {terminal.get('gate')}"
                             if terminal else ""),
                "must_finish": needed,
                "then_for_item_4": S.STAGE_GATE3}
    gate3 = _record(tree, S.STAGE_GATE3)
    rungs = rung_table(gate2)
    outliers = frame_outliers(gate2)
    replication = split_replication(gate2, rungs)
    exposure = reference_exposure(gate3, rungs)
    cases = exemplars(rungs, rows, prompts, n_cases=n_cases, per_frame=per_frame)
    return {
        **head, "available": True,
        "gate2": {"iota_a": gate2.get("iota_a"),
                  "iota_a_by_split": gate2.get("iota_a_by_split"),
                  "chance_basis": gate2.get("chance_basis"),
                  "row_accounting": gate2.get("row_accounting"),
                  "n_scored_rows_read": len(rows),
                  "wording_dependence_pooled": gate2["wording_dependence_pooled"],
                  "ladders_by_frame_pooled": {
                      w: {fam: d.get("ladder_class") for fam, d in fams.items()}
                      for w, fams in gate2["ladders_by_frame_pooled"].items()}},
        "regime_by_frame": regime_by_frame(
            gate2, pooled_curve=((terminal or {}).get("observed") or {}).get("curve")
            if terminal and terminal.get("gate") == S.STAGE_GATE2 else None),
        "item1_rungs": rungs,
        "item2_frame_outliers": outliers,
        "item3_split_replication": replication,
        "item4_reference_exposure": exposure,
        "item5_exemplars": cases,
        "options": option_evidence(gate2, rungs, outliers, replication, exposure),
    }


def render(rep: Mapping[str, Any]) -> str:
    L: list[str] = []
    p = L.append
    banner = ("> **SYNTHETIC WALK — NOT EVIDENCE.** The rows below come from the "
              "`dci1v8-synthetic` namespace's scripted generator, which has no "
              "wording effect by construction. The tables show the *shape* of "
              "the report; every number is a fixture.\n"
              if rep["synthetic"] else "")
    p("# DCI-1 v8 pilot — wording-policy decision report\n")
    p("> Generated by `dci1/tools/v8_wording_decision.py`. Do not edit by hand. "
      "Read-only; no composed outcome is read; no frame is chosen or discarded.\n")
    if banner:
        p(banner)
    p(f"Root `{rep['root']}` (namespace `{rep['namespace']}`, study "
      f"`{rep['study_id']}`), model `{rep['model_key']}`, stage reached "
      f"`{rep['stage_reached']}`. Basis: {rep['basis']}. Reference bound "
      f"{rep['reference_bound']} (§13.7).\n")
    if not rep["available"]:
        p(f"## Gate-2 data: NOT AVAILABLE\n\n{rep['reason']}.\n")
        p("Must finish first, in order: " + ", ".join(f"`{s}`" for s in rep["must_finish"])
          + f"; item 4 additionally needs `{rep['then_for_item_4']}`.\n")
        return "\n".join(L)
    g2 = rep["gate2"]
    if rep.get("terminal"):
        t = rep["terminal"]
        p(f"> **Replication terminal at `{t['gate']}`: `{t['status']}`** — {t['criterion']}. "
          f"A terminal status is a statement about the operating regime; it carries "
          f"no evidence about the effect. Signed Gate-2 record: "
          f"{'yes' if rep.get('signed_gate2_record') else 'no (tables recomputed from the grid rows)'}.\n")
    p(f"ι_A = {_fmt(g2['iota_a'])} (by split {g2['iota_a_by_split']}); "
      f"{g2['n_scored_rows_read']} scored Gate-2 rows read; chance basis: "
      f"{(g2['chance_basis'] or {}).get('basis', g2['chance_basis'])}.\n")
    rg = rep.get("regime_by_frame") or {}
    if rg.get("by_frame"):
        p("## 0. §12.3 on each frame's own A curve\n")
        p(f"Target band {rg['band']} on raw solo compliance; the stage applies the rule "
          f"to the curve pooled over the four frames. Per frame (48 topics × 4 draws per split):\n")
        qs = [str(q) for q in rg["grid"]]
        p("| curve | " + " | ".join(f"q={q}" for q in qs) + " | inside band | resolves alone? |")
        p("|---|" + "---:|" * len(qs) + "---|---|")
        for w, d in sorted(rg["by_frame"].items()):
            p(f"| f{w} | " + " | ".join(_fmt(d["curve"].get(q)) for q in qs)
              + f" | {d['severities_inside_band'] or '—'} | "
              + ("**no** (" + "; ".join(f"q{s['severities'][0]}→q{s['severities'][1]}" for s in d["straddling_pairs"]) + ")"
                 if d["grid_resolution_insufficient"] else "yes") + " |")
        if rg.get("pooled"):
            d = rg["pooled"]
            p(f"| pooled (stage) | " + " | ".join(_fmt(d["curve"].get(q)) for q in qs)
              + f" | {d['severities_inside_band'] or '—'} | "
              + ("**no** (" + "; ".join(f"q{s['severities'][0]}→q{s['severities'][1]}" for s in d["straddling_pairs"]) + ")"
                 if d["grid_resolution_insufficient"] else "yes") + " |")
        p("")

    # 1
    p("## 1. Per (family, q): the four frames\n")
    p("ι ± SE per frame (pooled calibration basis); spread = max ι − min ι; "
      "class per the descriptive rule; A/B = class on each split alone.\n")
    p("| rung | tier | κ | f0 | f1 | f2 | f3 | spread ι | max Δp | max\\|z\\| | class | A | B |")
    p("|---|---|---:|---|---|---|---|---:|---:|---:|---|---|---|")
    for r in rep["item1_rungs"]:
        cells = []
        for w in FRAMES:
            f = r["frames"].get(str(w))
            cells.append(f"{_fmt(f['iota'])} ± {_fmt(f['se_iota'])}"
                         if f and f.get("iota") is not None else "—")
        cb = r["class_by_split"]
        p(f"| {r['candidate']} | {r['tier'] or '—'} | {_fmt(r['chance'])} | " + " | ".join(cells)
          + f" | {_fmt(r['spread'])} | {_fmt(r['max_abs_difference_compliance'])} | {_fmt(r['max_abs_z'], 2)} | {r['class'] or '—'}"
          + f" | {(cb.get(C.CALIBRATION_A) or '—')} | {(cb.get(C.CALIBRATION_B) or '—')} |")
    dep = g2["wording_dependence_pooled"]
    p(f"\nRungs compared: {dep['n_rungs_compared']} ({dep['n_rungs_with_all_frames']} "
      f"with all four frames); τ median {_fmt(dep['tau_median'])}; spread median "
      f"{_fmt(dep['spread_median'])}, q90 {_fmt(dep['spread_q90'])}; class shares "
      + ", ".join(f"{k} {_fmt(v)}" for k, v in dep["share_by_class"].items()) + ".\n")
    ladders = g2["ladders_by_frame_pooled"]
    p("Ladder class per frame (pooled): " + ("; ".join(
        f"f{w}: " + ", ".join(f"{fam}={cls}" for fam, cls in sorted(fams.items()))
        for w, fams in sorted(ladders.items())) if any(ladders.values())
        else "— (no registered family measured on this basis; A and B carry no ladder class)") + "\n")

    # 2
    o = rep["item2_frame_outliers"]
    p("## 2. Is any frame a systematic outlier?\n")
    p(f"Leave-one-out over the {o['n_rungs_with_all_frames']} rungs with all four "
      f"frames; under exchangeability a frame is the extreme on "
      f"{_fmt(o['expected_share_extreme_if_exchangeable'], 2)} of rungs and the "
      f"hardest on {_fmt(o['expected_share_hardest_if_exchangeable'], 2)}.\n")
    p("| frame | rungs | mean dev | median dev | mean \\|dev\\| | mean \\|z\\| | "
      "share dev<0 | share hardest | share easiest | share extreme | resolved beyond bound |")
    p("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for w, s in sorted(o["by_frame"].items()):
        p(f"| f{w} | {s['n_rungs']} | {_fmt(s['mean_deviation'])} | "
          f"{_fmt(s['median_deviation'])} | {_fmt(s['mean_abs_deviation'])} | "
          f"{_fmt(s['mean_abs_z'], 2)} | {_fmt(s['share_negative_deviation'], 2)} | "
          f"{_fmt(s['share_hardest'], 2)} | {_fmt(s['share_easiest'], 2)} | "
          f"{_fmt(s['share_extreme'], 2)} | {s['n_beyond_bound_resolved']}"
          + (" (" + ", ".join(s['beyond_bound_resolved_rungs']) + ")"
             if s['beyond_bound_resolved_rungs'] else "") + " |")
    p("")

    # 3
    rp = rep["item3_split_replication"]
    p("## 3. Do wording differences replicate across fresh topic splits (A vs B)?\n")
    st = rp["gate2_split_stability"]
    p(f"Per-(frame, rung) stability of ι between Calibration-A and Calibration-B: "
      f"{st['n_inside_bound']}/{st['n_compared']} inside the bound "
      f"({_fmt(st['share_inside_bound'])}). Per frame: " + "; ".join(
          f"f{w}: {d['inside']}/{d['n']} inside, mean |Δι| {_fmt(d['mean_abs_difference'])}"
          for w, d in sorted(rp["per_frame_stability_a_vs_b"].items())) + ".\n")
    sc = rp["spread_correlation_a_vs_b"]
    p(f"Cross-frame spread on A vs on B over {sc['n_rungs']} rungs: Spearman "
      f"{_fmt(sc['spearman'])} ({sc['reading']}).\n")
    p(f"Flagged rungs (pooled WORDING_SENSITIVE or UNRESOLVED): {rp['n_flagged']}; "
      f"same sign on both splits {rp['n_same_sign']}; beyond the bound on both and "
      f"same sign {rp['n_replicating']}; resolved on both {rp['n_resolved_on_both']}.\n")
    if rp["flagged_rungs"]:
        p("| rung | pooled class | worst pair | Δ pooled | Δ A | Δ B | z A | z B | "
          "class A | class B | order A (hardest first) | order B | replicates |")
        p("|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|")
        for f in rp["flagged_rungs"]:
            p(f"| {f['candidate']} | {f['class_pooled']} | f{f['worst_pair'][0]}–f{f['worst_pair'][1]} | "
              f"{_fmt(f['difference_pooled'])} | {_fmt(f['difference_a'])} | {_fmt(f['difference_b'])} | "
              f"{_fmt(f['z_a'], 2)} | {_fmt(f['z_b'], 2)} | {f['class_a'] or '—'} | {f['class_b'] or '—'} | "
              f"{','.join('f' + w for w in (f['frame_order_hardest_first_a'] or []))} | "
              f"{','.join('f' + w for w in (f['frame_order_hardest_first_b'] or []))} | "
              f"{_fmt(f['replicates'])} |")
        p("")

    # 4
    ex = rep["item4_reference_exposure"]
    p("## 4. Do wording-sensitive rungs touch the reference set?\n")
    if not ex["available"]:
        p(ex["reason"] + ".\n")
    else:
        sv = ex["survival"]
        p(f"Gate 3: LOCAL-valid families {sv.get('n_local_valid_families')}, spectrum "
          f"pool ok {_fmt(sv.get('spectrum_pool_ok'))}, core identified "
          f"{_fmt(sv.get('core_identified'))}, coverage identified "
          f"{_fmt(sv.get('coverage_identified'))}. Core references: "
          f"{', '.join(ex['core_references']) or '—'}; selected spectrum points: "
          f"{', '.join(ex['selected_spectrum_points']) or '—'}; backup families: "
          f"{', '.join(ex['backup_families']) or '—'}.\n")
        p("| set | n | CONSISTENT | UNRESOLVED | WORDING_SENSITIVE | sensitive rungs | unresolved rungs |")
        p("|---|---:|---:|---:|---:|---|---|")
        for name, t in ex["sets"].items():
            bc = t["by_class"]
            p(f"| {name} | {t['n']} | {bc['CONSISTENT']} | {bc['UNRESOLVED']} | "
              f"{bc['WORDING_SENSITIVE']} | {', '.join(t['sensitive']) or '—'} | "
              f"{', '.join(t['unresolved']) or '—'} |")
        blk = ex["gate3_block"]
        p(f"\nGate 3's own block: {blk['n_wording_sensitive']} sensitive, "
          f"{blk['n_unresolved']} unresolved; touching the reference set: "
          f"{blk['touching_reference_set']}.\n")

    # 5
    e5 = rep["item5_exemplars"]
    p("## 5. The strongest cases: prompts, outputs, counts\n")
    p(f"Basis: {e5['basis']}. {e5['n_cases']} case(s).\n")
    for c in e5["cases"]:
        p(f"### {c['candidate']} — {c['class']} (κ {_fmt(c.get('chance'))}, max Δp {_fmt(c.get('max_abs_difference_compliance'))}, spread ι {_fmt(c['spread'])}, "
          f"max |z| {_fmt(c['max_abs_z'], 2)}; A {c['class_by_split'].get(C.CALIBRATION_A)}, "
          f"B {c['class_by_split'].get(C.CALIBRATION_B)})\n")
        for w, f in sorted(c["frames"].items()):
            p(f"**Frame f{w}** — ι {_fmt(f['iota'])} ± {_fmt(f['se_iota'])}; exact "
              f"compliance {f['k_exact_compliant']}/{f['n_rows']} "
              f"({_fmt(f['exact_compliance'])}) over {f['n_topics']} topics; observed-count "
              f"distribution {f['observed_count_distribution']}.\n")
            p(f"Constraint sentence: `{f['constraint_sentence']}`\n")
            if f.get("full_prompt_example"):
                p("Full prompt (one row):\n")
                p("```")
                p(f["full_prompt_example"])
                p("```\n")
            for o in f["outputs"]:
                p(f"- `{o['row_id']}` topic {o['topic_id']} ({o['topic_split']}), draw "
                  f"{o['draw_index']}: observed {o['observed_count']}, exact-compliant "
                  f"{_fmt(o['exact_compliant'])}, {o['word_count']} words"
                  f"{', truncated' if o['truncated'] else ''}:")
                p("  > " + (o["response_head"].replace("\n", " ") or "<empty>"))
            p("")

    # options
    op = rep["options"]
    p("## Evidence for the three researcher options (no choice made here)\n")
    a = op["retain_all_frames"]
    p("### Retain all frames\n")
    p(f"- class shares: CONSISTENT {_fmt(a['share_consistent'])}, UNRESOLVED "
      f"{_fmt(a['share_unresolved'])}, WORDING_SENSITIVE {_fmt(a['share_wording_sensitive'])}")
    p(f"- τ median {_fmt(a['tau_median'])}; spread median {_fmt(a['spread_median'])}, "
      f"q90 {_fmt(a['spread_q90'])}")
    p(f"- sensitive rungs replicating on both splits: {a['sensitive_rungs_replicating_on_both_splits']}")
    p(f"- sensitive rungs in the reference set: {a['reference_set_rungs_that_are_sensitive'] or 'Gate 3 not reached'}")
    p(f"- reading: {a['reading']}\n")
    b = op["retain_specified_subset"]
    p("### Retain a specified subset\n")
    p(f"- most often the extreme frame: f{b['most_often_extreme_frame']} (expected share "
      f"{_fmt(b['expected_share_extreme_if_exchangeable'], 2)} if exchangeable)")
    for w, s in sorted(b["frame_outlier_summary"].items()):
        p(f"- f{w}: mean dev {_fmt(s['mean_deviation'])}, hardest {_fmt(s['share_hardest'], 2)}, "
          f"easiest {_fmt(s['share_easiest'], 2)}, extreme {_fmt(s['share_extreme'], 2)}, "
          f"mean |z| {_fmt(s['mean_abs_z'], 2)}, resolved beyond bound {s['n_beyond_bound_resolved']}")
    p(f"- reading: {b['reading']}\n")
    m = op["model_frame_variation"]
    p("### Explicitly model wording/frame variation\n")
    p(f"- τ² median {_fmt(m['tau2_median'], 4)} vs within-frame sampling variance median "
      f"{_fmt(m['within_frame_sampling_variance_median'], 4)}; ICC-like ratio {_fmt(m['icc_like_ratio'])}")
    p(f"- rungs with a resolved frame effect: {m['n_rungs_with_resolved_frame_effect']} of "
      f"{m['n_rungs_with_all_frames']} with all frames; spread Spearman A vs B "
      f"{_fmt(m['split_spread_spearman'])}")
    p(f"- reading: {m['reading']}\n")
    p("Decision made here: none. No frame discarded.\n")
    return "\n".join(L)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", default="qwen3-4b-instruct-2507")
    ap.add_argument("--namespace", choices=("pilot", "synthetic"), default="pilot")
    ap.add_argument("--out", default=str(REPO / "reports" / "dci1v8dev"))
    ap.add_argument("--exemplars", type=int, default=3)
    ap.add_argument("--outputs-per-frame", type=int, default=2)
    args = ap.parse_args(argv)
    try:
        rep = build(Path(args.root), model_key=args.model, namespace=args.namespace,
                    n_cases=args.exemplars, per_frame=args.outputs_per_frame)
    except (ProtocolError, IntegrityError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = "wording_decision" + (".synthetic" if rep["synthetic"] else "")
    (out / f"{stem}.json").write_text(json.dumps(rep, indent=1, sort_keys=True,
                                                  default=str) + "\n")
    (out / f"{stem}.md").write_text(render(rep))
    print(f"wrote {out / (stem + '.md')} and .json; available={rep['available']}; "
          f"stage_reached={rep['stage_reached']}")
    return 0 if rep["available"] else 2


if __name__ == "__main__":
    sys.exit(main())
