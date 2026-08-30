"""The v8-internal wording diagnostic: the four frames measured separately.

Researcher decision (2026-08-30): the pilot does not judge the repaired
frames against v7's frame statistics, and it does not average the frames
together as its primary instrument diagnostic. For every ``(frame, family,
q)`` it reports the sample, the exact-compliance rate, the chance estimate on
the unconstrained cell, the chance-corrected difficulty ι with its standard
error, and the comparison with the same family/q under the other frames.
Every generated row enters these tables, compliant or not: the exact
compliance verdict is the *outcome* being counted, never a filter.

**What "materially disagree" means here, and what it does not decide.** Two
frames' ι for one rung are compared on the registered §13.7 equivalence
bound (``STABILITY_EQUIVALENCE_BOUND`` = 0.20, the bound two independent
measurements of one instrument must satisfy) --- reused as a *descriptive
reference*, not as a pass/fail threshold. A pair whose difference exceeds
the bound and whose 95 % interval excludes zero is ``WORDING_SENSITIVE``; a
pair beyond the bound whose interval still covers zero is ``UNRESOLVED``;
otherwise ``CONSISTENT``. No frame is discarded on any of this: the wording
policy (retain all frames, a specified subset, or model frame variation) is a
later researcher decision on solo / pre-screen / calibration evidence, and
``stages.WORDING_POLICY_STATUS`` says it is open.

Chance is frame-free: the unconstrained cell states no frame. κ for a frame's
rows is measured on the unconstrained cell of the **same rows' topic set**
(the registered §13.2 basis), and the κ over the frame's own topic subset is
reported beside it.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import FAMILIES

from dci1v8dev.prescreen.ladder import ladder_diagnostics
from dci1v8dev.run.execute import UNCONSTRAINED_ARM, frame_of_row

__all__ = ["CLASSES", "Z_95", "frame_table", "frame_comparison",
           "ladders_by_frame", "wording_dependence",
           "stability_by_frame", "wording_diagnostic", "sensitive_rungs"]

CLASSES = ("CONSISTENT", "UNRESOLVED", "WORDING_SENSITIVE")
Z_95 = 1.959963984540054


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _sd(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def _chance_by_topic(rows: Sequence[Mapping[str, Any]], *, split: str | None
                     ) -> dict[str, dict[str, list[float]]]:
    """label -> topic -> absent verdicts on the unconstrained cell."""
    out: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        if row.get("arm") != UNCONSTRAINED_ARM:
            continue
        if split is not None and row.get("topic_split") != split:
            continue
        for s in row["scores"]:
            if s.get("present"):
                continue
            out.setdefault(f"{s['kind']}:{s['severity']}", {}).setdefault(
                row["topic_id"], []).append(float(bool(s["passed"])))
    return out


def _topic_mean(per_topic: Mapping[str, Sequence[float]],
                topics: Sequence[str] | None = None) -> float | None:
    names = sorted(per_topic) if topics is None else [t for t in topics
                                                     if t in per_topic]
    if not names:
        return None
    return _mean([_mean(per_topic[t]) for t in names])


def frame_table(rows: Sequence[Mapping[str, Any]], *, split: str | None = None
                ) -> list[dict[str, Any]]:
    """Per (frame, family, q): every load-1 row, compliant or not."""
    chance = _chance_by_topic(rows, split=split)
    acc: dict[tuple[int, str, int], dict[str, Any]] = {}
    for row in rows:
        if row.get("load") != 1:
            continue
        if split is not None and row.get("topic_split") != split:
            continue
        frame = frame_of_row(row)
        if frame is None:
            continue
        present = [s for s in row["scores"] if s.get("present")]
        if len(present) != 1:
            continue
        s = present[0]
        key = (frame, s["kind"], int(s["severity"]))
        entry = acc.setdefault(key, {"per_topic": {}, "n_rows": 0, "k": 0,
                                     "vacuous": 0, "statistics": [],
                                     "processing_failures": 0})
        entry["n_rows"] += 1
        passed = bool(s["passed"])
        entry["k"] += int(passed)
        entry["vacuous"] += int(bool(s.get("vacuous_pass")))
        entry["processing_failures"] += int(bool(s.get("processing_failure")))
        if s.get("statistic") is not None:
            entry["statistics"].append(float(s["statistic"]))
        entry["per_topic"].setdefault(row["topic_id"], []).append(float(passed))
    table: list[dict[str, Any]] = []
    for (frame, kind, q), e in sorted(acc.items()):
        label = f"{kind}:{q}"
        topics = sorted(e["per_topic"])
        means = [_mean(e["per_topic"][t]) for t in topics]
        p = _mean(means)
        sd = _sd(means)
        # Topic-level SE, floored by the Agresti-Coull binomial SE over the
        # topic count: a frame whose few topics all pass or all fail has an
        # SD of 0 and would otherwise call any difference "resolved" on no
        # evidence (a boundary artefact, not a finding). A correction of the
        # estimator, not a threshold.
        n_t = len(means)
        se_topic = (sd / math.sqrt(n_t)) if sd is not None else None
        p_ac = (e["k"] / max(e["n_rows"], 1) * n_t + 2.0) / (n_t + 4.0)
        se_floor = math.sqrt(p_ac * (1.0 - p_ac) / (n_t + 4.0)) if n_t else None
        se_p = (max(se_topic, se_floor) if se_topic is not None
                else se_floor)
        kappa_all = _topic_mean(chance.get(label, {}))
        kappa_same = _topic_mean(chance.get(label, {}), topics)
        defined = kappa_all is not None and kappa_all < C.CHANCE_DEGENERACY_MAX
        iota = ((p - kappa_all) / (1.0 - kappa_all)) if defined else None
        se_iota = ((se_p / (1.0 - kappa_all)) if defined and se_p is not None
                   else None)
        table.append({
            "frame": frame, "kind": kind, "severity": q, "candidate": label,
            "family": kind if kind in FAMILIES else None,
            "n_rows": e["n_rows"], "n_topics": len(topics),
            "draws_per_topic": (e["n_rows"] / len(topics)) if topics else None,
            "k_exact_compliant": e["k"],
            "exact_compliance": p,
            "se_exact_compliance": se_p,
            "n_vacuous_pass": e["vacuous"],
            "n_processing_failures": e["processing_failures"],
            "observed_count_mean": _mean(e["statistics"]),
            "observed_count_zero_share": (
                sum(1 for v in e["statistics"] if v == 0) / len(e["statistics"])
                if e["statistics"] else None),
            "chance": kappa_all, "chance_same_topics": kappa_same,
            "chance_basis": "unconstrained cell of the rows' topic set "
                            "(§13.2); frame-free",
            "iota": iota, "se_iota": se_iota,
            "coordinate_defined": defined,
        })
    return table


def _by_rung(table: Sequence[Mapping[str, Any]]
             ) -> dict[str, dict[int, Mapping[str, Any]]]:
    out: dict[str, dict[int, Mapping[str, Any]]] = {}
    for e in table:
        out.setdefault(e["candidate"], {})[int(e["frame"])] = e
    return out


def frame_comparison(table: Sequence[Mapping[str, Any]], *,
                     bound: float = C.STABILITY_EQUIVALENCE_BOUND
                     ) -> dict[str, dict[str, Any]]:
    """Per rung: every frame's ι beside the others, the largest pairwise
    difference, its z, and the descriptive class (see the module note)."""
    out: dict[str, dict[str, Any]] = {}
    for label, frames in sorted(_by_rung(table).items()):
        measured = {w: e for w, e in frames.items()
                    if e["iota"] is not None and e["se_iota"] is not None}
        pairs = []
        for a in sorted(measured):
            for b in sorted(measured):
                if b <= a:
                    continue
                d = measured[b]["iota"] - measured[a]["iota"]
                se = math.sqrt(measured[a]["se_iota"] ** 2
                               + measured[b]["se_iota"] ** 2)
                z = (d / se) if se > 0 else None
                pairs.append({"frames": [a, b], "difference": d, "se": se,
                              "z": z, "beyond_bound": abs(d) > bound,
                              "resolved": z is not None and abs(z) >= Z_95})
        worst = max(pairs, key=lambda p: abs(p["difference"]), default=None)
        iotas = [e["iota"] for e in measured.values()]
        if worst is None:
            klass = None
        elif worst["beyond_bound"] and worst["resolved"]:
            klass = "WORDING_SENSITIVE"
        elif worst["beyond_bound"]:
            klass = "UNRESOLVED"
        else:
            klass = "CONSISTENT"
        out[label] = {
            "kind": label.rpartition(":")[0],
            "severity": int(label.rpartition(":")[2]),
            "frames": {str(w): {"iota": e["iota"], "se_iota": e["se_iota"],
                                "exact_compliance": e["exact_compliance"],
                                "n_topics": e["n_topics"], "n_rows": e["n_rows"]}
                       for w, e in sorted(frames.items())},
            "n_frames_measured": len(measured),
            "spread": (max(iotas) - min(iotas)) if len(iotas) >= 2 else None,
            "pairwise": pairs,
            "max_abs_difference": abs(worst["difference"]) if worst else None,
            "max_abs_z": (max((abs(p["z"]) for p in pairs if p["z"] is not None),
                              default=None)),
            "class": klass,
            "reference_bound": bound,
        }
    return out


def ladders_by_frame(table: Sequence[Mapping[str, Any]]
                     ) -> dict[str, dict[str, Any]]:
    """Per frame, per family: the ladder diagnostic over that frame's rungs."""
    out: dict[str, dict[str, Any]] = {}
    grouped: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
    for e in table:
        if e["family"] is None:
            continue
        grouped.setdefault((int(e["frame"]), e["kind"]), []).append(e)
    for (frame, kind), entries in sorted(grouped.items()):
        entries = sorted(entries, key=lambda e: e["severity"])
        sds = [e["se_iota"] if e["se_iota"] is not None else float("nan")
               for e in entries]
        out.setdefault(str(frame), {})[kind] = ladder_diagnostics(
            kind, [e["severity"] for e in entries],
            [e["iota"] for e in entries], sds,
            [((e["iota"] - s) if e["iota"] is not None else float("nan"),
              (e["iota"] + s) if e["iota"] is not None else float("nan"))
             for e, s in zip(entries, sds)])
    return out


def wording_dependence(comparison: Mapping[str, Mapping[str, Any]]
                       ) -> dict[str, Any]:
    """How strongly ι depends on the frame, over every rung with at least
    two frames: the between-frame variance net of sampling variance (a
    method-of-moments τ²), the distribution of spreads, the share of rungs
    in each class, and the flagged rungs by name."""
    tau2s, spreads = [], []
    by_class: dict[str, list[str]] = {k: [] for k in CLASSES}
    n_all_frames = 0
    for label, c in comparison.items():
        measured = [f for f in c["frames"].values() if f["iota"] is not None
                    and f["se_iota"] is not None]
        if len(measured) < 2:
            continue
        if len(measured) == C.N_WORDINGS:
            n_all_frames += 1
        iotas = [f["iota"] for f in measured]
        within = _mean([f["se_iota"] ** 2 for f in measured])
        between = _sd(iotas) ** 2
        tau2s.append(max(0.0, between - within))
        spreads.append(c["spread"])
        if c["class"]:
            by_class[c["class"]].append(label)
    n = len(tau2s)
    tau2s_sorted = sorted(tau2s)
    spreads_sorted = sorted(spreads)
    return {
        "n_rungs_compared": n,
        "n_rungs_with_all_frames": n_all_frames,
        "tau2_median": tau2s_sorted[n // 2] if n else None,
        "tau2_mean": _mean(tau2s),
        "tau_median": math.sqrt(tau2s_sorted[n // 2]) if n else None,
        "spread_median": spreads_sorted[n // 2] if n else None,
        "spread_q90": spreads_sorted[int(0.9 * (n - 1))] if n else None,
        "share_by_class": {k: (len(v) / n if n else None)
                           for k, v in by_class.items()},
        "rungs_by_class": {k: sorted(v) for k, v in by_class.items()},
        "reading": "τ² is the between-frame variance of ι net of sampling "
                   "variance, per rung, summarised over rungs; the classes "
                   "are descriptive (module note) and select nothing",
    }


def stability_by_frame(table_a: Sequence[Mapping[str, Any]],
                       table_b: Sequence[Mapping[str, Any]], *,
                       bound: float = C.STABILITY_EQUIVALENCE_BOUND,
                       names: tuple[str, str] = ("a", "b")
                       ) -> dict[str, Any]:
    """Per (frame, rung) measured on two disjoint topic sets: the difference
    in ι, its z, and whether it lies inside the §13.7 bound --- the
    stability of a frame's difficulty estimate across fresh topics."""
    a, b = _by_rung(table_a), _by_rung(table_b)
    entries: dict[str, Any] = {}
    inside = total = 0
    for label in sorted(set(a) & set(b)):
        for w in sorted(set(a[label]) & set(b[label])):
            ea, eb = a[label][w], b[label][w]
            if ea["iota"] is None or eb["iota"] is None:
                continue
            d = eb["iota"] - ea["iota"]
            se = math.sqrt((ea["se_iota"] or 0.0) ** 2
                           + (eb["se_iota"] or 0.0) ** 2)
            z = (d / se) if se > 0 else None
            ok = abs(d) <= bound
            total += 1
            inside += int(ok)
            entries[f"{label}@{w}"] = {
                "candidate": label, "frame": w,
                f"iota_{names[0]}": ea["iota"], f"iota_{names[1]}": eb["iota"],
                "difference": d, "se": se, "z": z, "inside_bound": ok}
    return {"basis": list(names), "reference_bound": bound,
            "n_compared": total, "n_inside_bound": inside,
            "share_inside_bound": (inside / total) if total else None,
            "entries": entries}


def sensitive_rungs(comparison: Mapping[str, Mapping[str, Any]]
                    ) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in CLASSES}
    for label, c in comparison.items():
        if c.get("class"):
            out[c["class"]].append(label)
    return {k: sorted(v) for k, v in out.items()}


def wording_diagnostic(rows: Sequence[Mapping[str, Any]], *,
                       split: str | None = None,
                       bound: float = C.STABILITY_EQUIVALENCE_BOUND
                       ) -> dict[str, Any]:
    """The whole diagnostic on one row set: table, comparison, ladders per
    frame, dependence summary."""
    table = frame_table(rows, split=split)
    comparison = frame_comparison(table, bound=bound)
    return {"frame_table": table, "frame_comparison": comparison,
            "ladders_by_frame": ladders_by_frame(table),
            "wording_dependence": wording_dependence(comparison),
            "rungs_by_class": sensitive_rungs(comparison),
            "primary_diagnostic": "per (frame, family, q); frames are never "
                                  "averaged here",
            "selection_rule": None,
            "no_frame_discarded": True}
