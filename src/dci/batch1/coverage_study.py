"""The D11 coverage-rule study (re-audit R3). Offline, CPU-only, simulated;
never pilot evidence and not part of Freeze 1.

D11 decides when a contrast (P1, P2, P3) counts as *estimable* in a
configuration (model, frame, B limit). It does not decide which references
are admitted: admission is eligibility (D09), compatibility and matching
(D10), and every admitted reference stays in its population
(``references.populations`` has no cap). This module asks which minimum
coverage rule gives reliable verdicts, holding admission fixed.

**Paired design.** Each simulated pilot (``simulate.one_pilot``, the real
Stage 1 -> Stage 2 -> ``calibration.finalize`` path) is drawn once, and every
rule in ``RULES`` is evaluated on the same populations, so rule differences
are never sampling differences.

**Ground truth.** For a surface, the noise-free result is the same pipeline
run on population-mean tables (``simulate.truth_tables``: every cell's
compliance averaged over the topic distribution, as an infinite pilot would
estimate it). For a rule R, *true(R)* is R's verdict on those tables, with
the A and B they select. A pilot verdict under R is a false FEASIBLE when it
is FEASIBLE and true(R) is not, and a false INFEASIBLE in the converse
case. Because a strict rule can be INFEASIBLE in truth where the design rule
is not, every rule is also scored against true(D), the design rule.

**Oracle decomposition.** To attribute errors, each pilot is re-evaluated
with parts of its noise removed: true eligibility (``oracle_E``), true
matching and A cell (``oracle_M``: populations built from true rates with the
pilot's eligibility), both (``oracle_EM``: only the pilot's A/B selection is
noisy), and the true A and B with every estimate noisy (``oracle_S``).

Run: ``python -m dci.batch1.coverage_study --reps 600 --out <json>``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Any, Iterable, Mapping

from dci.batch1 import calibration as CAL
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1 import simulate as S

__all__ = ["Spec", "Rule", "RULES", "CONTRASTS", "VARIANTS", "added",
           "supported", "rule_verdict", "run", "figures", "main"]

CONTRASTS = ("P1", "P2", "P3")
VARIANTS = ("actual", "oracle_E", "oracle_M", "oracle_EM", "oracle_S")
CFG0 = CFG.DEFAULT_CONFIG
BY_ID = L.constraint_by_id()


@dataclass(frozen=True)
class Spec:
    """A minimum for one contrast's newly admitted references.

    ``k``: at least this many variants; ``min_families``: from at least this
    many parameterised families (count variants of one word, or the three
    length orders, are one family); ``min_categories``: spanning at least
    this many operations (P3) or object types (P2). For P1, whose additions
    all share A's operation and object type, the word is both family and
    category. ``margin`` (exploratory; it would be a separate decision): only
    additions whose estimated |p_X - p_A| is at most this count."""
    k: int = 2
    min_families: int = 0
    min_categories: int = 0
    margin: float | None = None

    def describe(self) -> str:
        parts = [f">= {self.k}"]
        if self.min_families:
            parts.append(f">= {self.min_families} families")
        if self.min_categories:
            parts.append(f">= {self.min_categories} categories")
        if self.margin is not None:
            parts.append(f"|diff| <= {self.margin}")
        return ", ".join(parts)


DESIGN = Spec()


@dataclass(frozen=True)
class Rule:
    """Per-contrast minima; a contrast not named keeps the design's (2)."""
    name: str
    p1: Spec = DESIGN
    p2: Spec = DESIGN
    p3: Spec = DESIGN
    design: bool = False
    exploratory: bool = False
    group: str = ""

    def spec(self, contrast: str) -> Spec:
        return {"P1": self.p1, "P2": self.p2, "P3": self.p3}[contrast]

    def describe(self) -> str:
        return "; ".join(f"{p}: {self.spec(p).describe()}" for p in CONTRASTS)


RULES: tuple[Rule, ...] = (
    Rule("D", design=True, group="design"),
    # More variants, P3 only (the auditor's option b and beyond).
    Rule("P3k3", p3=Spec(3), group="count"),
    Rule("P3k4", p3=Spec(4), group="count"),
    Rule("P3k5", p3=Spec(5), group="count"),
    # More variants for both matching-admitted contrasts.
    Rule("P23k3", p2=Spec(3), p3=Spec(3), group="count"),
    # Every contrast, uniformly.
    Rule("Uk3", p1=Spec(3), p2=Spec(3), p3=Spec(3), group="count"),
    Rule("Uk4", p1=Spec(4), p2=Spec(4), p3=Spec(4), group="count"),
    # Diversity instead of, or as well as, more variants.
    Rule("P3c2", p3=Spec(2, min_categories=2), group="diversity"),
    Rule("P3k3c2", p3=Spec(3, min_categories=2), group="diversity"),
    Rule("P3f2", p3=Spec(2, min_families=2), group="diversity"),
    Rule("P3f3", p3=Spec(3, min_families=3), group="diversity"),
    Rule("P23c2", p2=Spec(2, min_categories=2), p3=Spec(2, min_categories=2),
         group="diversity"),
    Rule("P3k4c2", p3=Spec(4, min_categories=2), group="diversity"),
    # Exploratory: count only additions estimated well inside the tolerance.
    Rule("P3m05", p3=Spec(2, margin=0.05), exploratory=True, group="margin"),
    Rule("P3k3m07", p3=Spec(3, margin=0.07), exploratory=True, group="margin"),
)


# ---------------------------------------------------------------- the rule

def added(report: Mapping[str, Any], a: L.Constraint) -> dict[str, list[str]]:
    """The newly admitted references of each contrast (as
    ``references.coverage`` defines them)."""
    g = {k: set(v) for k, v in report["populations"].items()}
    return {
        "P1": sorted(g["G2"] - g["G1"]),
        "P2": sorted(c for c in g["G3"] - g["G1"]
                     if BY_ID[c].object_type != a.object_type),
        "P3": sorted(c for c in g["G5"] - g["G3"]
                     if BY_ID[c].operation != a.operation),
    }


def _family(contrast: str, cid: str) -> str:
    c = BY_ID[cid]
    return c.p["word"] if contrast == "P1" else c.family_id


def _category(contrast: str, cid: str) -> str:
    c = BY_ID[cid]
    return {"P1": c.p.get("word", c.cid), "P2": c.object_type,
            "P3": c.operation}[contrast]


def counted(report: Mapping[str, Any], a: L.Constraint, rule: Rule,
            contrast: str) -> list[str]:
    members = added(report, a)[contrast]
    margin = rule.spec(contrast).margin
    if margin is not None and contrast != "P1":
        tol = Fraction(str(margin))
        members = [c for c in members
                   if abs(Fraction(str(report["matching"][c]["diff"]))) <= tol]
    return members


def supported(report: Mapping[str, Any], a: L.Constraint, rule: Rule,
              contrast: str, cfg: CFG.PilotConfig = CFG0) -> bool:
    if contrast in ("P1", "P2") and not report["coverage"]["G1"]["supported"]:
        return False
    if contrast == "P3" and len(report["populations"]["G3"]) < cfg.p3_min_g3:
        return False
    spec = rule.spec(contrast)
    members = counted(report, a, rule, contrast)
    return (len(members) >= spec.k
            and len({_family(contrast, c) for c in members}) >= spec.min_families
            and len({_category(contrast, c) for c in members})
            >= spec.min_categories)


def rule_verdict(reports: list[Mapping[str, Any]], a: L.Constraint | None,
                 b_limits: Iterable[int] | None, rule: Rule,
                 cfg: CFG.PilotConfig = CFG0) -> dict[str, Any]:
    """``references.feasibility`` with ``rule`` in place of the minima."""
    if a is None or not b_limits:
        return {"feasible": False, "selection_failed": True,
                **{p: {"supported": 0, "feasible": False} for p in CONTRASTS}}
    b_limits = sorted(b_limits)
    out: dict[str, Any] = {"selection_failed": False}
    for p in CONTRASTS:
        sup = [r for r in reports
               if r["a_informative"] and supported(r, a, rule, p, cfg)]
        ok = (len(sup) >= cfg.feasibility_min_configs
              and len({r["model"] for r in sup}) >= cfg.feasibility_min_models
              and sorted({r["b_limit"] for r in sup}) == b_limits)
        out[p] = {"supported": len(sup), "feasible": ok}
    out["feasible"] = all(out[p]["feasible"] for p in CONTRASTS)
    return out


# ------------------------------------------------------------ per pilot

def _reports(tables, elig, a: L.Constraint, b_limits) -> list[dict[str, Any]]:
    return [R.configuration_report(tables, CFG0, S._matrix(), elig, a, m, f, lim)
            for m, f in R.model_frames(CFG0) for lim in b_limits]


@lru_cache(maxsize=None)
def _truth(surface: str) -> dict[str, Any]:
    tables = S.truth_tables(surface)
    result = CAL.finalize(tables, CFG0, S._matrix())
    a = BY_ID[result["a"]["selected"]] if result.get("a") and \
        result["a"].get("selected") else None
    b = (result.get("b") or {}).get("selected")
    reports = result["configurations"]
    return {"tables": tables, "result": result, "a": a, "b": b,
            "elig": result["eligibility"], "reports": reports,
            "verdicts": {r.name: rule_verdict(reports, a, b, r) for r in RULES}}


_TRUTH_REPORTS: dict[tuple, list] = {}


def _truth_reports(surface: str, elig_key: str, elig, a: L.Constraint,
                   b_limits) -> list[dict[str, Any]]:
    key = (surface, elig_key, a.cid, tuple(b_limits))
    if key not in _TRUTH_REPORTS:
        _TRUTH_REPORTS[key] = _reports(_truth(surface)["tables"], elig, a,
                                       b_limits)
    return _TRUTH_REPORTS[key]


def _true_diff(truth_tables, m, f, a_cid, x_cid) -> Fraction:
    ta, tx = truth_tables.x(m, f, a_cid), truth_tables.x(m, f, x_cid)
    return abs(Fraction(tx.k, tx.n) - Fraction(ta.k, ta.n))


def _weights_equal(members) -> dict[str, float]:
    members = sorted(set(members))
    return {c: 1 / len(members) for c in members} if members else {}


def _tvd(w1: Mapping[str, float], w2: Mapping[str, float]) -> float:
    keys = set(w1) | set(w2)
    return 0.5 * sum(abs(w1.get(k, 0.0) - w2.get(k, 0.0)) for k in keys)


def _pilot_record(surface: str, alloc: S.Allocation, seed: int
                  ) -> dict[str, Any]:
    truth = _truth(surface)
    sim = S.one_pilot(surface, alloc, seed)
    tables, res = sim["tables"], sim["result"]
    a_sel = (res.get("a") or {}).get("selected")
    a = BY_ID[a_sel] if a_sel and res["status"] != "A_SELECTION_FAILED" else None
    b = (res.get("b") or {}).get("selected")
    elig = res["eligibility"]
    true_elig, ta, tb = truth["elig"], truth["a"], truth["b"]

    reports: dict[str, list] = {}
    if a is not None and b:
        reports["actual"] = res["configurations"]
        reports["oracle_E"] = _reports(tables, true_elig, a, b)
        reports["oracle_M"] = _reports(truth["tables"], elig, a, b)
        reports["oracle_EM"] = _truth_reports(surface, "true", true_elig, a, b)
    if ta is not None and tb:
        reports["oracle_S"] = (res["configurations"]
                               if a is not None and a.cid == ta.cid and b == tb
                               else _reports(tables, elig, ta, tb))
    rec: dict[str, Any] = {
        "seed": seed, "status": res["status"], "a": a_sel if a else None,
        "b": b, "refined": sim["refined"], "verdicts": {}}
    for variant in VARIANTS:
        va, vb = (ta, tb) if variant == "oracle_S" else (a, b)
        reps = reports.get(variant, [])
        rec["verdicts"][variant] = {}
        for rule in RULES:
            v = rule_verdict(reps, va if reps else None, vb if reps else None,
                             rule)
            rec["verdicts"][variant][rule.name] = (
                [int(v["feasible"])] + [v[p]["supported"] for p in CONTRASTS]
                + [int(v[p]["feasible"]) for p in CONTRASTS])

    # With the true A and B: configuration-level accuracy, memberships,
    # contamination and weights.
    if "oracle_S" in reports:
        est, tru = reports["oracle_S"], truth["reports"]
        conf = {r.name: {p: [0, 0, 0, 0] for p in CONTRASTS} for r in RULES}
        # Per rule, over configurations it calls supported (P2, P3): counted
        # additions, of which truly unmatched or ineligible, and configs.
        quality = {r.name: {p: [0, 0, 0] for p in ("P2", "P3")} for r in RULES}
        jac = {g: [] for g in R.GROUPS}
        contam = {"P2": [0, 0], "P3": [0, 0]}
        wfalse = {"hier": [], "equal": []}
        tvd = {(g, w): [] for g in ("G1", "G3", "G5") for w in ("hier", "equal")}
        conc = {"G3_max_w": [], "G5_max_w": [], "G5_neff_share": [],
                "G5_single_member_operation_weight": []}
        diversity = {"P3_ops": [], "P3_families": [], "P3_added": [],
                     "P2_added": []}
        for e, t in zip(est, tru):
            m, f = e["model"], e["frame"]
            def false_member(c):
                return (_true_diff(truth["tables"], m, f, ta.cid, c)
                        > Fraction(1, 10)
                        or true_elig[c]["status"] != R.ELIGIBLE)
            for rule in RULES:
                for p in CONTRASTS:
                    se = e["a_informative"] and supported(e, ta, rule, p)
                    st = t["a_informative"] and supported(t, ta, rule, p)
                    conf[rule.name][p][2 * (not st) + (not se)] += 1
                    if se and p != "P1":
                        members = counted(e, ta, rule, p)
                        q = quality[rule.name][p]
                        q[0] += len(members)
                        q[1] += sum(false_member(c) for c in members)
                        q[2] += 1
            for g in R.GROUPS:
                jac[g].append(S._jaccard(set(e["populations"][g]),
                                         set(t["populations"][g])))
            add = added(e, ta)
            for p in ("P2", "P3"):
                for c in add[p]:
                    contam[p][0] += 1
                    contam[p][1] += false_member(c)
            diversity["P3_added"].append(len(add["P3"]))
            diversity["P2_added"].append(len(add["P2"]))
            diversity["P3_ops"].append(len({BY_ID[c].operation
                                             for c in add["P3"]}))
            diversity["P3_families"].append(len({BY_ID[c].family_id
                                                  for c in add["P3"]}))
            g5 = e["populations"]["G5"]
            truly = set(t["populations"]["G5"])
            hw = {c: float(w) for c, w in R.hierarchical_weights(g5).items()}
            ew = _weights_equal(g5)
            if g5:
                wfalse["hier"].append(sum(w for c, w in hw.items()
                                          if c not in truly))
                wfalse["equal"].append(sum(w for c, w in ew.items()
                                           if c not in truly))
                conc["G5_max_w"].append(max(hw.values()))
                conc["G5_neff_share"].append(
                    1 / sum(w * w for w in hw.values()) / len(g5))
                ops: dict[str, list[str]] = {}
                for c in g5:
                    ops.setdefault(BY_ID[c].operation, []).append(c)
                conc["G5_single_member_operation_weight"].append(sum(
                    hw[cs[0]] for cs in ops.values() if len(cs) == 1))
            g3 = e["populations"]["G3"]
            if g3:
                conc["G3_max_w"].append(max(float(w) for w in
                                            R.hierarchical_weights(g3).values()))
            for g in ("G1", "G3", "G5"):
                pe, pt = e["populations"][g], t["populations"][g]
                tvd[(g, "hier")].append(_tvd(
                    {c: float(w) for c, w in R.hierarchical_weights(pe).items()},
                    {c: float(w) for c, w in R.hierarchical_weights(pt).items()}))
                tvd[(g, "equal")].append(_tvd(_weights_equal(pe),
                                              _weights_equal(pt)))
        rec["fixed_ab"] = {
            "confusion": conf, "quality": quality, "contamination": contam,
            "jaccard": {g: statistics.mean(v) for g, v in jac.items()},
            "false_weight_G5": {k: statistics.mean(v) if v else None
                                for k, v in wfalse.items()},
            "tvd": {f"{g}_{w}": statistics.mean(v) if v else None
                    for (g, w), v in tvd.items()},
            "concentration": {k: statistics.mean(v) if v else None
                              for k, v in conc.items()},
            "diversity": {k: statistics.mean(v) for k, v in diversity.items()},
            "eligibility_errors": sum(
                (elig[c]["status"] == R.ELIGIBLE)
                != (true_elig[c]["status"] == R.ELIGIBLE) for c in elig),
            "matching_errors": _matching_errors(est, truth["tables"], ta),
        }
    return rec


def _matching_errors(est, truth_tables, a) -> dict[str, list[int]]:
    """[errors, total] for references whose true distance from A is within
    0.02, 0.02-0.05 and beyond 0.05 of the tolerance edge."""
    out = {"within_0.02": [0, 0], "0.02_to_0.05": [0, 0], "beyond_0.05": [0, 0]}
    tol = Fraction(1, 10)
    for e in est:
        m, f = e["model"], e["frame"]
        if e["b_limit"] != max(x["b_limit"] for x in est):
            continue                      # matching does not depend on B
        for cid, row in e["matching"].items():
            if row.get("status") != "OK":
                continue
            d = _true_diff(truth_tables, m, f, a.cid, cid)
            gap = abs(d - tol)
            band = ("within_0.02" if gap <= Fraction(1, 50) else
                    "0.02_to_0.05" if gap <= Fraction(1, 20) else "beyond_0.05")
            out[band][0] += (d <= tol) != bool(row["raw"])
            out[band][1] += 1
    return out


def _task(args) -> list[dict[str, Any]]:
    surface, alloc, seeds = args
    return [_pilot_record(surface, alloc, s) for s in seeds]


# ------------------------------------------------------------- summarising

def _wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def _rate(k: int, n: int) -> dict[str, Any]:
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None,
            "ci95": _wilson(k, n)}


def summarise(surface: str, records: list[dict[str, Any]],
              alloc: S.Allocation) -> dict[str, Any]:
    truth = _truth(surface)
    n = len(records)
    true_v = {r.name: truth["verdicts"][r.name] for r in RULES}
    design_true = true_v["D"]["feasible"]
    out: dict[str, Any] = {
        "pilots": n, "allocation": alloc.name, "max_rows": alloc.max_rows(),
        "truth": {"status": truth["result"]["status"],
                  "a": truth["a"].cid if truth["a"] else None,
                  "b": truth["b"],
                  "rules": {k: {"feasible": v["feasible"],
                                **{p: v[p]["supported"] for p in CONTRASTS}}
                            for k, v in true_v.items()}},
        "a_matches_truth": _rate(sum(r["a"] == (truth["a"].cid if truth["a"]
                                                 else None) for r in records), n),
        "b_matches_truth": _rate(sum(r["b"] == truth["b"] for r in records), n),
        "a_counts": _counter(r["a"] or "FAILED" for r in records),
        "b_counts": _counter("-".join(map(str, r["b"])) if r["b"] else "FAILED"
                             for r in records),
        "status_counts": _counter(r["status"] for r in records),
        "rules": {}}
    for rule in RULES:
        tv = true_v[rule.name]["feasible"]
        rs: dict[str, Any] = {"true_feasible": tv}
        for variant in VARIANTS:
            feas = [r["verdicts"][variant][rule.name][0] for r in records]
            k = sum(feas)
            v = {"feasible": _rate(k, n),
                 "false_feasible": _rate(k, n) if not tv else None,
                 "false_infeasible": _rate(n - k, n) if tv else None,
                 "vs_design_truth": (_rate(n - k, n) if design_true
                                     else _rate(k, n)),
                 "supported_mean": {p: round(statistics.mean(
                     r["verdicts"][variant][rule.name][1 + i] for r in records), 3)
                     for i, p in enumerate(CONTRASTS)},
                 "supported_sd": {p: round(statistics.pstdev(
                     r["verdicts"][variant][rule.name][1 + i] for r in records), 3)
                     for i, p in enumerate(CONTRASTS)}}
            if variant == "actual":
                v["contrast_feasible"] = {
                    p: _rate(sum(r["verdicts"][variant][rule.name][4 + i]
                                 for r in records), n)
                    for i, p in enumerate(CONTRASTS)}
                v["contrast_true"] = {p: true_v[rule.name][p]["feasible"]
                                      for p in CONTRASTS}
                v["verdict_agreement_between_two_pilots"] = round(
                    (k / n) ** 2 + (1 - k / n) ** 2, 4)
                v["near_threshold_feasible"] = _rate(sum(
                    r["verdicts"][variant][rule.name][0] and min(
                        r["verdicts"][variant][rule.name][1:4]) <= 14
                    for r in records), n)
                if not tv:
                    v["false_feasible_when_flag_absent"] = _rate(sum(
                        r["verdicts"][variant][rule.name][0] and min(
                            r["verdicts"][variant][rule.name][1:4]) > 14
                        for r in records), n)
            rs[variant] = v
        design = [r["verdicts"]["actual"]["D"][0] for r in records]
        mine = [r["verdicts"]["actual"][rule.name][0] for r in records]
        rs["paired_vs_design"] = {
            "design_feasible_rule_not": sum(d and not m
                                            for d, m in zip(design, mine)),
            "rule_feasible_design_not": sum(m and not d
                                            for d, m in zip(design, mine)),
            "pilots": n}
        fixed = [r["fixed_ab"] for r in records if "fixed_ab" in r]
        if fixed:
            rs["configuration_accuracy_fixed_ab"] = {}
            for p in CONTRASTS:
                tp = sum(x["confusion"][rule.name][p][0] for x in fixed)
                fn = sum(x["confusion"][rule.name][p][1] for x in fixed)
                fp = sum(x["confusion"][rule.name][p][2] for x in fixed)
                tn = sum(x["confusion"][rule.name][p][3] for x in fixed)
                rs["configuration_accuracy_fixed_ab"][p] = {
                    "true_supported": tp + fn, "true_unsupported": fp + tn,
                    "sensitivity": round(tp / (tp + fn), 4) if tp + fn else None,
                    "false_support_rate": round(fp / (fp + tn), 4)
                    if fp + tn else None}
            rs["counted_member_quality_fixed_ab"] = {}
            for p in ("P2", "P3"):
                n_mem = sum(x["quality"][rule.name][p][0] for x in fixed)
                n_false = sum(x["quality"][rule.name][p][1] for x in fixed)
                n_conf = sum(x["quality"][rule.name][p][2] for x in fixed)
                rs["counted_member_quality_fixed_ab"][p] = {
                    "supported_configs": n_conf,
                    "false_member_share": round(n_false / n_mem, 4)
                    if n_mem else None,
                    "true_members_per_supported_config":
                        round((n_mem - n_false) / n_conf, 3) if n_conf else None,
                    "false_members_per_supported_config":
                        round(n_false / n_conf, 3) if n_conf else None}
        out["rules"][rule.name] = rs
    fixed = [r["fixed_ab"] for r in records if "fixed_ab" in r]
    if fixed:
        def mean(path):
            vals = [x for x in (_get(f, path) for f in fixed) if x is not None]
            return round(statistics.mean(vals), 4) if vals else None
        out["fixed_ab"] = {
            "pilots": len(fixed),
            "membership_jaccard": {g: mean(("jaccard", g)) for g in R.GROUPS},
            "contamination": {p: _rate(sum(f["contamination"][p][1] for f in fixed),
                                       sum(f["contamination"][p][0] for f in fixed))
                              for p in ("P2", "P3")},
            "false_member_weight_G5": {w: mean(("false_weight_G5", w))
                                       for w in ("hier", "equal")},
            "weight_tvd": {k: mean(("tvd", k)) for k in fixed[0]["tvd"]},
            "concentration": {k: mean(("concentration", k))
                              for k in fixed[0]["concentration"]},
            "diversity": {k: mean(("diversity", k)) for k in fixed[0]["diversity"]},
            "eligibility_errors_per_pilot": mean(("eligibility_errors",)),
            "matching_error_rate": {
                band: _rate(sum(f["matching_errors"][band][0] for f in fixed),
                            sum(f["matching_errors"][band][1] for f in fixed))
                for band in fixed[0]["matching_errors"]}}
    return out


def _get(d, path):
    for k in path:
        if d is None:
            return None
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _counter(items) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return dict(sorted(out.items()))


def _seeds(seed: int, surface: str, alloc: str, reps: int) -> list[int]:
    return [int.from_bytes(hashlib.sha256(
        f"{seed}|coverage|{surface}|{alloc}|{i}".encode()).digest()[:4], "big")
        for i in range(reps)]


def run(reps: int, *, surfaces=None, alloc: S.Allocation = S.ALLOCATIONS[0],
        workers: int = 9, seed: int = 20261019) -> dict[str, Any]:
    surfaces = list(surfaces or S.ALL_SURFACES)
    tasks = []
    for s in surfaces:
        seeds = _seeds(seed, s, alloc.name, reps)
        size = max(1, math.ceil(len(seeds) / (workers * 4)))
        tasks += [(s, alloc, seeds[i:i + size])
                  for i in range(0, len(seeds), size)]
    started = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_task, tasks))
    grouped: dict[str, list] = {}
    for (s, _, _), recs in zip(tasks, results):
        grouped.setdefault(s, []).extend(recs)
    return {
        "schema": "dci.batch1/coverage-study/v1",
        "note": "SIMULATED: invented compliance surfaces passed through the "
                "real Batch 1 selection code; not an empirical finding",
        "reps": reps, "seed": seed, "allocation": alloc.name,
        "topic_sd": S.TOPIC_SD, "cell_topic_sd": S.CELL_TOPIC_SD,
        "rules": {r.name: {"description": r.describe(), "design": r.design,
                           "exploratory": r.exploratory, "group": r.group,
                           **{p: asdict(r.spec(p)) for p in CONTRASTS}}
                  for r in RULES},
        "surfaces": {s: summarise(s, grouped[s], alloc) for s in surfaces},
        "seconds": round(time.time() - started, 1)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m dci.batch1.coverage_study")
    p.add_argument("--reps", type=int, default=600)
    p.add_argument("--workers", type=int, default=9)
    p.add_argument("--surfaces", nargs="*")
    p.add_argument("--allocation", default=S.ALLOCATIONS[0].name,
                   choices=[a.name for a in S.ALLOCATIONS])
    p.add_argument("--out", required=True)
    p.add_argument("--figures", metavar="DIR",
                   help="write the review figures from --out (and --cost) "
                        "instead of simulating")
    p.add_argument("--cost", help="a second result, at a larger allocation")
    p.add_argument("--tables", action="store_true",
                   help="print the review tables from --out (and --cost)")
    args = p.parse_args(argv)
    if args.tables:
        with open(args.out) as fh:
            result = json.load(fh)
        cost = None
        if args.cost:
            with open(args.cost) as fh:
                cost = json.load(fh)
        for name, table in review_tables(result, cost).items():
            print(f"<!-- {name} -->\n{table}\n")
        return 0
    if args.figures:
        with open(args.out) as fh:
            result = json.load(fh)
        cost = None
        if args.cost:
            with open(args.cost) as fh:
                cost = json.load(fh)
        print(json.dumps({"written": figures(result, args.figures, cost)}))
        return 0
    alloc = next(a for a in S.ALLOCATIONS if a.name == args.allocation)
    result = run(args.reps, surfaces=args.surfaces, alloc=alloc,
                 workers=args.workers)
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps({"written": args.out, "seconds": result["seconds"]}))
    return 0



# ----------------------------------------------------------------- figures

FIGURE_RULES = ("D", "P3k3", "P3k4", "P3c2", "P3k3c2")
SURFACE_LABELS = {
    "moderate": "moderate", "model_differences": "model diffs",
    "frame_differences": "frame diffs", "boundary_cluster": "G1 at edge",
    "low_followability": "low followability",
    "other_operation_harder": "other ops harder",
    "strong_model_sensitivity": "strong model", "strong_paraphrase_sensitivity":
    "strong paraphrase", "edge_crowded": "edge crowded",
    "graded_coverage": "graded", "graded_coverage_sparse": "graded sparse",
    "single_operation_coverage": "one operation"}


def figures(result: Mapping[str, Any], outdir: str,
            cost: Mapping[str, Any] | None = None) -> list[str]:
    """PNG figures for COVERAGE_SIMULATION_REVIEW.md (matplotlib, Agg)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    S = result["surfaces"]
    names = list(S)
    labels = [SURFACE_LABELS.get(s, s) for s in names]
    written = []

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(out / name, dpi=130)
        plt.close(fig)
        written.append(str(out / name))

    # 1. P(FEASIBLE) by rule, truth marked.
    fig, ax = plt.subplots(figsize=(11, 4.8))
    width = 0.8 / len(FIGURE_RULES)
    for i, r in enumerate(FIGURE_RULES):
        xs = [j + (i - len(FIGURE_RULES) / 2 + 0.5) * width
              for j in range(len(names))]
        ys = [S[s]["rules"][r]["actual"]["feasible"]["rate"] for s in names]
        bars = ax.bar(xs, ys, width, label=r)
        for x, s in zip(xs, names):
            if S[s]["rules"][r]["true_feasible"]:
                ax.plot(x, 1.03, marker="v", ms=4,
                        color=bars.patches[0].get_facecolor())
    ax.set_xticks(range(len(names)), labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("share of simulated pilots FEASIBLE")
    ax.set_title("Pilot verdicts by coverage rule (▼ = FEASIBLE in truth "
                 "under that rule)")
    ax.legend(ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.38))
    save(fig, "coverage_fig1_feasible_by_rule.png")

    # 2. Where the error comes from (design rule D).
    fig, ax = plt.subplots(figsize=(11, 4.8))
    variants = (("actual", "pilot as run"), ("oracle_E", "true eligibility"),
                ("oracle_M", "true matching"), ("oracle_S", "true A and B"))
    width = 0.8 / len(variants)
    for i, (v, lab) in enumerate(variants):
        xs = [j + (i - len(variants) / 2 + 0.5) * width for j in range(len(names))]
        ax.bar(xs, [S[s]["rules"]["D"][v]["feasible"]["rate"] for s in names],
               width, label=lab)
    for j, s in enumerate(names):
        ax.text(j, 1.02, "T" if S[s]["rules"]["D"]["true_feasible"] else "F",
                ha="center", fontsize=8)
    ax.set_xticks(range(len(names)), labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("share FEASIBLE (design rule)")
    ax.set_title("Removing one source of noise at a time (T/F = true verdict)")
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.38))
    save(fig, "coverage_fig2_noise_sources.png")

    # 3. Counted P3 members that are not truly matched.
    fig, ax = plt.subplots(figsize=(11, 4.8))
    width = 0.8 / len(FIGURE_RULES)
    for i, r in enumerate(FIGURE_RULES):
        xs = [j + (i - len(FIGURE_RULES) / 2 + 0.5) * width
              for j in range(len(names))]
        ys = [S[s]["rules"][r]["counted_member_quality_fixed_ab"]["P3"]
              ["false_member_share"] or 0 for s in names]
        ax.bar(xs, ys, width, label=r)
    ax.set_xticks(range(len(names)), labels, rotation=35, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("share of counted P3 references\nthat are not truly matched")
    ax.set_title("Admission errors inside configurations each rule calls "
                 "supported (true A and B)")
    ax.legend(ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.38))
    save(fig, "coverage_fig3_member_quality.png")

    # 4. Hierarchical versus equal weights.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fx = [S[s]["fixed_ab"] for s in names]
    for ax, key, title in (
            (axes[0], ("weight_tvd", "G5_hier", "G5_equal"),
             "Weight that moves because of sampling noise (G5)"),
            (axes[1], ("false_member_weight_G5", "hier", "equal"),
             "Weight on references that are not truly in G5")):
        h = [f[key[0]][key[1]] for f in fx]
        e = [f[key[0]][key[2]] for f in fx]
        ax.scatter(e, h)
        for x, y, lab in zip(e, h, labels):
            ax.annotate(lab, (x, y), fontsize=7, xytext=(3, 2),
                        textcoords="offset points")
        lo, hi = min(e + h) - 0.03, max(e + h) + 0.03
        ax.plot([lo, hi], [lo, hi], color="grey", lw=0.8)
        ax.set_xlabel("equal weights")
        ax.set_ylabel("hierarchical weights (D13)")
        ax.set_title(title, fontsize=10)
    save(fig, "coverage_fig4_weights.png")

    if cost:
        fig, ax = plt.subplots(figsize=(11, 4.8))
        CS = cost["surfaces"]
        common = [s for s in names if s in CS]
        for i, (r, src, lab) in enumerate(
                (("D", S, "D, 30,976 rows"), ("D", CS, "D, ~46,000 rows"),
                 ("P3k3", S, "P3k3, 30,976"), ("P3k3", CS, "P3k3, ~46,000"))):
            xs = [j + (i - 1.5) * 0.2 for j in range(len(common))]
            ax.bar(xs, [src[s]["rules"][r]["actual"]["feasible"]["rate"]
                        for s in common], 0.2, label=lab)
        ax.set_xticks(range(len(common)),
                      [SURFACE_LABELS.get(s, s) for s in common], rotation=35,
                      ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("share FEASIBLE")
        ax.set_title("Does a larger Stage 2 (480 instead of 240 cells) help?")
        ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.38))
        save(fig, "coverage_fig5_budget.png")
    return written


# ------------------------------------------------------------------ tables

TABLE_RULES = ("D", "P3k3", "P3k4", "P3k5", "P23k3", "Uk3", "P3c2", "P3k3c2",
               "P3f2", "P3f3", "P3m05")
TYPICAL = ("moderate", "model_differences", "frame_differences",
           "boundary_cluster")
THIN = ("other_operation_harder", "graded_coverage_sparse")


def _pct(x) -> str:
    return "—" if x is None else f"{100 * x:.0f}%"


def review_tables(result: Mapping[str, Any],
                  cost: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Markdown tables for COVERAGE_SIMULATION_REVIEW.md, from the stored
    results (``python -m dci.batch1.coverage_study --out R --tables``)."""
    S = result["surfaces"]
    names = list(S)
    lab = {s: SURFACE_LABELS.get(s, s) for s in names}
    out: dict[str, str] = {}

    rows = ["| scenario | true A, B | true P3 support (of 16): design / P3k3 "
            "| true verdict: design / P3k3 |", "|---|---|---|---|"]
    for s in names:
        t = S[s]["truth"]
        rows.append(f"| {lab[s]} | {t['a']}, {t['b']} | {t['rules']['D']['P3']}"
                    f" / {t['rules']['P3k3']['P3']} | "
                    f"{'FEASIBLE' if t['rules']['D']['feasible'] else 'INFEASIBLE'}"
                    f" / {'FEASIBLE' if t['rules']['P3k3']['feasible'] else 'INFEASIBLE'} |")
    out["truth"] = "\n".join(rows)

    rows = ["| scenario | " + " | ".join(TABLE_RULES) + " |",
            "|---|" + "---|" * len(TABLE_RULES)]
    for s in names:
        cells = []
        for r in TABLE_RULES:
            x = S[s]["rules"][r]
            v = _pct(x["actual"]["feasible"]["rate"])
            cells.append(f"**{v}**" if x["true_feasible"] else v)
        rows.append(f"| {lab[s]} | " + " | ".join(cells) + " |")
    out["feasible"] = "\n".join(rows)

    rows = ["| rule | what it requires (P3 unless stated) | scenarios FEASIBLE "
            "in truth | mean error | worst error | false FEASIBLE, thin "
            "coverage | false INFEASIBLE, typical |",
            "|---|---|---|---|---|---|---|"]
    for r in TABLE_RULES:
        errs, n_true = [], 0
        for s in names:
            x = S[s]["rules"][r]
            if x["true_feasible"]:
                n_true += 1
                errs.append(x["actual"]["false_infeasible"]["rate"])
            else:
                errs.append(x["actual"]["false_feasible"]["rate"])
        thin = statistics.mean(S[s]["rules"][r]["actual"]["vs_design_truth"]
                               ["rate"] for s in THIN)
        typ = statistics.mean(S[s]["rules"][r]["actual"]["vs_design_truth"]
                              ["rate"] for s in TYPICAL)
        rows.append(f"| {r} | {result['rules'][r]['description']} | "
                    f"{n_true} of {len(names)} | {_pct(statistics.mean(errs))} | "
                    f"{_pct(max(errs))} | {_pct(thin)} | {_pct(typ)} |")
    out["summary"] = "\n".join(rows)

    rows = ["| scenario | true verdict | as run | true eligibility | true "
            "matching | true A and B |", "|---|---|---|---|---|---|"]
    for s in names:
        x = S[s]["rules"]["D"]
        rows.append(f"| {lab[s]} | {'FEASIBLE' if x['true_feasible'] else 'INFEASIBLE'}"
                    " | " + " | ".join(_pct(x[v]["feasible"]["rate"]) for v in
                                       ("actual", "oracle_E", "oracle_M",
                                        "oracle_S")) + " |")
    out["noise"] = "\n".join(rows)

    rows = ["| scenario | A as in truth | B as in truth | G1 | G3 | G5 | two "
            "pilots agree (design) | two pilots agree (P3k3) |",
            "|---|---|---|---|---|---|---|---|"]
    for s in names:
        f = S[s]["fixed_ab"]["membership_jaccard"]
        rows.append(f"| {lab[s]} | {_pct(S[s]['a_matches_truth']['rate'])} | "
                    f"{_pct(S[s]['b_matches_truth']['rate'])} | {f['G1']:.2f} | "
                    f"{f['G3']:.2f} | {f['G5']:.2f} | "
                    f"{_pct(S[s]['rules']['D']['actual']['verdict_agreement_between_two_pilots'])}"
                    f" | {_pct(S[s]['rules']['P3k3']['actual']['verdict_agreement_between_two_pilots'])} |")
    out["stability"] = "\n".join(rows)

    rows = ["| scenario | wrong when within 0.02 of the edge | 0.02–0.05 | "
            "beyond 0.05 | P2 additions not truly matched | P3 additions "
            "not truly matched | eligibility errors per pilot |",
            "|---|---|---|---|---|---|---|"]
    for s in names:
        f = S[s]["fixed_ab"]
        m = f["matching_error_rate"]
        rows.append(f"| {lab[s]} | {_pct(m['within_0.02']['rate'])} | "
                    f"{_pct(m['0.02_to_0.05']['rate'])} | "
                    f"{_pct(m['beyond_0.05']['rate'])} | "
                    f"{_pct(f['contamination']['P2']['rate'])} | "
                    f"{_pct(f['contamination']['P3']['rate'])} | "
                    f"{f['eligibility_errors_per_pilot']:.1f} |")
    out["matching"] = "\n".join(rows)

    rows = ["| scenario | G5 weight on wrong members: hierarchical / equal | "
            "G5 weight that moves with noise: hierarchical / equal | largest "
            "single weight in G5 | weight on one-member operations |",
            "|---|---|---|---|---|"]
    for s in names:
        f = S[s]["fixed_ab"]
        rows.append(f"| {lab[s]} | {_pct(f['false_member_weight_G5']['hier'])} / "
                    f"{_pct(f['false_member_weight_G5']['equal'])} | "
                    f"{_pct(f['weight_tvd']['G5_hier'])} / "
                    f"{_pct(f['weight_tvd']['G5_equal'])} | "
                    f"{_pct(f['concentration']['G5_max_w'])} | "
                    f"{_pct(f['concentration']['G5_single_member_operation_weight'])} |")
    out["weights"] = "\n".join(rows)

    rows = ["| scenario | P3 configurations wrongly called supported: design / "
            "P3k3 / P3k4 | truly supported configurations found: design / "
            "P3k3 / P3k4 | counted P3 references not truly matched: design / "
            "P3k3 |", "|---|---|---|---|"]
    for s in names:
        acc = [S[s]["rules"][r]["configuration_accuracy_fixed_ab"]["P3"]
               for r in ("D", "P3k3", "P3k4")]
        q = [S[s]["rules"][r]["counted_member_quality_fixed_ab"]["P3"]
             ["false_member_share"] for r in ("D", "P3k3")]
        rows.append(f"| {lab[s]} | " + " / ".join(_pct(a["false_support_rate"])
                                                   for a in acc) + " | "
                    + " / ".join(_pct(a["sensitivity"]) for a in acc) + " | "
                    + " / ".join(_pct(x) for x in q) + " |")
    out["configurations"] = "\n".join(rows)

    rows = ["| scenario | near-threshold flag raised on a FEASIBLE pilot | "
            "false FEASIBLE without the flag |", "|---|---|---|"]
    for s in names:
        a = S[s]["rules"]["D"]["actual"]
        rows.append(f"| {lab[s]} | {_pct(a['near_threshold_feasible']['rate'])} | "
                    f"{_pct((a.get('false_feasible_when_flag_absent') or {}).get('rate'))} |")
    out["flag"] = "\n".join(rows)

    if cost:
        C2 = cost["surfaces"]
        rows = ["| scenario | design: 30,976 rows → 46,336 | P3k3 | P3k4 | "
                "P3 additions not truly matched (design) |",
                "|---|---|---|---|---|"]
        for s in names:
            if s not in C2:
                continue
            cells = [f"{_pct(S[s]['rules'][r]['actual']['feasible']['rate'])} → "
                     f"{_pct(C2[s]['rules'][r]['actual']['feasible']['rate'])}"
                     for r in ("D", "P3k3", "P3k4")]
            rows.append(f"| {lab[s]}{' (true: FEASIBLE)' if S[s]['rules']['D']['true_feasible'] else ''} | "
                        + " | ".join(cells) + " | "
                        f"{_pct(S[s]['fixed_ab']['contamination']['P3']['rate'])} → "
                        f"{_pct(C2[s]['fixed_ab']['contamination']['P3']['rate'])} |")
        out["budget"] = "\n".join(rows)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
