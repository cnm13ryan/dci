"""Global eligibility, difficulty matching, reference populations G1-G6,
hierarchical weights, and P1-P3 coverage.

All of it reads stand-alone pilot tables (``scoring.PilotTables``), the
compatibility matrix and the configuration. Nothing here reads, or could
read, a composed outcome.

**Eligibility (D09).** A candidate is eligible when its raw stand-alone
compliance point estimate is at least ``eligibility_threshold`` in at least
one model-frame cell (an OR across the panel); once eligible it is eligible
for every model. ``EXTENSION_ONLY`` marks candidates admitted at the 10%
threshold but not at 20% --- a separate sensitivity population, never merged
into the primary one. A candidate with no qualifying cell and at least one
incomplete cell is ``UNDETERMINED``, not ineligible.

**Matching (D10).** In each model-frame, X is matched to A when
``|p_X - p_A| <= matching_tolerance``, compared in exact rational arithmetic
so 0.10 is not lost to floating point. Matching is never pooled across
models or frames. The chance-corrected sensitivity uses
``iota = (p - kappa) / (1 - kappa)`` with kappa the task-only spontaneous
rate for that model; iota is undefined when kappa = 1 or kappa is missing,
and an undefined iota is unmatched and flagged.

**Populations.** For a configuration (model, frame, B limit) and the
selected A, with ``pool`` = eligible, B-compatible, not A:

    G6 = pool                     G5 = matched(pool)
    G4 = same operation as A      G3 = matched(G4)
    G2 = same operation & object  G1 = matched(G2)

so the nesting G1 <= G2 <= G4 <= G6, G1 <= G3 <= G4, G3 <= G5 <= G6 holds by
construction and is asserted anyway. Prompt order is not an input, so both
orders share membership.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Iterable, Mapping

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1.intervals import newcombe, wilson
from dci.batch1.scoring import Count, PilotTables

__all__ = ["ELIGIBLE", "EXTENSION_ONLY", "INELIGIBLE", "UNDETERMINED",
           "GROUPS", "usable", "eligibility", "match", "populations",
           "hierarchical_weights", "coverage", "configuration_report",
           "feasibility", "assert_nesting"]

ELIGIBLE, EXTENSION_ONLY = "ELIGIBLE", "EXTENSION_ONLY"
INELIGIBLE, UNDETERMINED = "INELIGIBLE", "UNDETERMINED"
GROUPS = ("G1", "G2", "G3", "G4", "G5", "G6")


def usable(count: Count, cfg: CFG.PilotConfig) -> bool:
    """A cell decides something only with enough behavioural rows."""
    if count.n == 0:
        return False
    if count.planned:
        return count.n >= cfg.min_cell_fraction * count.planned
    return True


def _frac(x: float) -> Fraction:
    return Fraction(str(x))


def _ge(count: Count, threshold: float) -> bool:
    return Fraction(count.k, count.n) >= _frac(threshold)


def model_frames(cfg: CFG.PilotConfig) -> list[tuple[str, str]]:
    return [(m, f) for m in cfg.models for f in cfg.frames]


# -------------------------------------------------------------- eligibility

def eligibility(tables: PilotTables, cfg: CFG.PilotConfig,
                refs: Iterable[L.Constraint] | None = None
                ) -> dict[str, dict[str, Any]]:
    refs = tuple(L.reference_library() if refs is None else refs)
    out: dict[str, dict[str, Any]] = {}
    for c in refs:
        cells, q20, q10, missing = {}, [], [], []
        for model, frame in model_frames(cfg):
            count = tables.x(model, frame, c.cid)
            key = f"{model}|{frame}"
            if not usable(count, cfg):
                missing.append(key)
                cells[key] = {"k": count.k, "n": count.n, "usable": False}
                continue
            lo, hi = wilson(count.k, count.n, cfg.z)
            cells[key] = {"k": count.k, "n": count.n, "p": count.p,
                          "ci": [lo, hi], "usable": True}
            if _ge(count, cfg.eligibility_threshold):
                q20.append(key)
            if _ge(count, cfg.extension_threshold):
                q10.append(key)
        if q20:
            status = ELIGIBLE
        elif missing:
            status = UNDETERMINED
        elif q10:
            status = EXTENSION_ONLY
        else:
            status = INELIGIBLE
        usable_cells = [v for v in cells.values() if v["usable"]]
        certain = (any(v["ci"][0] >= cfg.eligibility_threshold
                       for v in usable_cells) if status == ELIGIBLE else
                   bool(usable_cells) and not missing and all(
                       v["ci"][1] < cfg.eligibility_threshold
                       for v in usable_cells))
        out[c.cid] = {"status": status, "qualifying_20": q20,
                      "qualifying_10": q10, "incomplete_cells": missing,
                      "decision": "clear" if certain else "borderline",
                      "cells": cells}
    return out


def eligible_ids(elig: Mapping[str, Mapping[str, Any]], *,
                 extension: bool = False) -> set[str]:
    admit = {ELIGIBLE, EXTENSION_ONLY} if extension else {ELIGIBLE}
    return {cid for cid, e in elig.items() if e["status"] in admit}


# ----------------------------------------------------------------- matching

def _iota(count: Count, kappa: Count, cfg: CFG.PilotConfig) -> Fraction | None:
    if not usable(kappa, cfg) or kappa.k == kappa.n:
        return None
    p = Fraction(count.k, count.n)
    k = Fraction(kappa.k, kappa.n)
    return (p - k) / (1 - k)


def match(tables: PilotTables, cfg: CFG.PilotConfig, model: str, frame: str,
          a_cid: str, x_cid: str) -> dict[str, Any]:
    a, x = tables.x(model, frame, a_cid), tables.x(model, frame, x_cid)
    if not (usable(a, cfg) and usable(x, cfg)):
        return {"raw": None, "iota": None, "status": UNDETERMINED,
                "reason": "incomplete stand-alone cell"}
    tol = _frac(cfg.matching_tolerance)
    diff = Fraction(x.k, x.n) - Fraction(a.k, a.n)
    lo, hi = newcombe(x.k, x.n, a.k, a.n, cfg.z)
    ia = _iota(a, tables.kappa(model, a_cid), cfg)
    ix = _iota(x, tables.kappa(model, x_cid), cfg)
    iota_diff = None if ia is None or ix is None else ix - ia
    return {
        "status": "OK", "p_x": float(Fraction(x.k, x.n)),
        "p_a": float(Fraction(a.k, a.n)), "diff": float(diff),
        "diff_ci": [lo, hi], "raw": abs(diff) <= tol,
        "within_tolerance_with_confidence": -float(tol) <= lo and hi <= float(tol),
        "iota_x": None if ix is None else float(ix),
        "iota_a": None if ia is None else float(ia),
        "iota": None if iota_diff is None else abs(iota_diff) <= tol,
        "iota_undefined": iota_diff is None,
    }


# -------------------------------------------------------------- populations

def populations(a: L.Constraint, pool: Iterable[L.Constraint],
                matched: set[str]) -> dict[str, list[str]]:
    pool = [c for c in pool if c.cid != a.cid]
    same_op = [c for c in pool if c.operation == a.operation]
    same_obj = [c for c in same_op if c.object_type == a.object_type]
    pops = {
        "G6": pool, "G5": [c for c in pool if c.cid in matched],
        "G4": same_op, "G3": [c for c in same_op if c.cid in matched],
        "G2": same_obj, "G1": [c for c in same_obj if c.cid in matched],
    }
    out = {g: sorted(c.cid for c in members) for g, members in pops.items()}
    assert_nesting(out)
    return out


def assert_nesting(pops: Mapping[str, Iterable[str]]) -> None:
    s = {g: set(pops[g]) for g in GROUPS}
    for small, big in (("G1", "G2"), ("G1", "G3"), ("G3", "G4"), ("G3", "G5"),
                       ("G2", "G6"), ("G4", "G6"), ("G5", "G6"), ("G2", "G4")):
        if not s[small] <= s[big]:
            raise AssertionError(f"{small} is not a subset of {big}")


def hierarchical_weights(members: Iterable[str], mode: str = "variant"
                         ) -> dict[str, Fraction]:
    """Equal over operations, then object types within an operation, then
    variants within an operation-object group. Exact; sums to one.

    ``mode="word_then_count"`` (revision 2026-10, R10): inside a group of
    exact-word-count variants, each target word gets an equal share, split
    equally over that word's count variants, so a word with several matched
    counts does not outweigh one with a single matched count."""
    by_id = L.constraint_by_id()
    members = sorted(set(members))
    if not members:
        return {}
    tree: dict[str, dict[str, list[str]]] = {}
    for cid in members:
        c = by_id[cid]
        tree.setdefault(c.operation, {}).setdefault(c.object_type, []).append(cid)
    weights: dict[str, Fraction] = {}
    for op, objects in tree.items():
        for obj, cids in objects.items():
            group = Fraction(1, len(tree)) * Fraction(1, len(objects))
            words = {}
            if mode == "word_then_count":
                for cid in cids:
                    c = by_id[cid]
                    if c.family_id == "exact_word_count":
                        words.setdefault(c.p["word"], []).append(cid)
            if words and sum(map(len, words.values())) == len(cids):
                for variants in words.values():
                    for cid in variants:
                        weights[cid] = group * Fraction(1, len(words)) * \
                            Fraction(1, len(variants))
                continue
            for cid in cids:
                weights[cid] = group * Fraction(1, len(cids))
    if sum(weights.values()) != 1:
        raise AssertionError("hierarchical weights do not sum to one")
    return dict(sorted(weights.items()))


# ----------------------------------------------------------------- coverage

def _distinct_words(cids: Iterable[str]) -> set[str]:
    by_id = L.constraint_by_id()
    return {by_id[c].p["word"] for c in cids
            if by_id[c].family_id == "exact_word_count"}


def coverage(a: L.Constraint, pops: Mapping[str, list[str]],
             funnel: Mapping[str, Any], cfg: CFG.PilotConfig
             ) -> dict[str, dict[str, Any]]:
    by_id = L.constraint_by_id()
    g = {k: set(v) for k, v in pops.items()}
    g1_words = _distinct_words(g["G1"])
    g1_ok = len(g1_words) >= cfg.g1_min_distinct_words
    out: dict[str, dict[str, Any]] = {}

    def result(name, supported, reasons, added, restricted, relaxed):
        expansion = g[relaxed] - g[restricted]
        if not expansion:
            reasons = reasons + ["NO_EFFECTIVE_POPULATION_EXPANSION"]
        out[name] = {"supported": supported, "reasons": [] if supported
                     else reasons, "added": sorted(added),
                     "restricted": restricted, "relaxed": relaxed}

    g1_reason = [] if g1_ok else [
        f"G1_TOO_FEW_DISTINCT_WORDS ({len(g1_words)} < "
        f"{cfg.g1_min_distinct_words}; limiting step: "
        f"{funnel['G1']['limiting_step']})"]
    added1 = g["G2"] - g["G1"]
    ok1 = g1_ok and len(added1) >= cfg.p1_min_additional
    result("P1", ok1, g1_reason + ([] if len(added1) >= cfg.p1_min_additional
                                   else [f"G2_ADDS_{len(added1)}_OF_"
                                         f"{cfg.p1_min_additional}"]),
           added1, "G1", "G2")
    added2 = {c for c in g["G3"] - g["G1"]
              if by_id[c].object_type != a.object_type}
    ok2 = g1_ok and len(added2) >= cfg.p2_min_additional_other_object
    result("P2", ok2, g1_reason + (
        [] if len(added2) >= cfg.p2_min_additional_other_object else
        [f"G3_ADDS_{len(added2)}_OTHER_OBJECT_OF_"
         f"{cfg.p2_min_additional_other_object} (limiting step: "
         f"{funnel['P2']['limiting_step']})"]), added2, "G1", "G3")
    added3 = {c for c in g["G5"] - g["G3"]
              if by_id[c].operation != a.operation}
    ok3_g3 = len(g["G3"]) >= cfg.p3_min_g3
    ok3 = ok3_g3 and len(added3) >= cfg.p3_min_additional_other_operation
    result("P3", ok3, ([] if ok3_g3 else
                       [f"G3_HAS_{len(g['G3'])}_OF_{cfg.p3_min_g3}"]) + (
        [] if len(added3) >= cfg.p3_min_additional_other_operation else
        [f"G5_ADDS_{len(added3)}_OTHER_OPERATION_OF_"
         f"{cfg.p3_min_additional_other_operation} (limiting step: "
         f"{funnel['P3']['limiting_step']})"]), added3, "G3", "G5")
    out["G1"] = {"supported": g1_ok, "distinct_words": sorted(g1_words)}
    return out


def _funnel(candidates: list[L.Constraint], elig: set[str], compatible: set[str],
            matched: set[str], undetermined: set[str], need: int,
            measure) -> dict[str, Any]:
    """How many candidates survive each filter, and which filter bites."""
    steps = [("library", candidates)]
    steps.append(("eligible", [c for c in steps[-1][1] if c.cid in elig]))
    steps.append(("compatible", [c for c in steps[-1][1] if c.cid in compatible]))
    steps.append(("matched", [c for c in steps[-1][1] if c.cid in matched]))
    sizes = {name: measure(members) for name, members in steps}
    limiting = "none"
    for name, _ in steps:
        if sizes[name] < need:
            limiting = name
            break
    if limiting != "none" and undetermined & {c.cid for c in candidates}:
        limiting += " (incomplete pilot cells involved)"
    return {"sizes": sizes, "limiting_step": limiting}


def configuration_report(tables: PilotTables, cfg: CFG.PilotConfig,
                         compat: Mapping[str, Any], elig: Mapping[str, Any],
                         a: L.Constraint, model: str, frame: str, m: int
                         ) -> dict[str, Any]:
    """G1-G6 (primary and sensitivities), weights and coverage for one
    configuration."""
    refs = L.reference_library()
    compatible = COMPAT.compatible_ids(compat, m)
    unresolved = sorted(cid for cid, row in compat["cells"].items()
                        if row[str(m)]["status"] == COMPAT.UNRESOLVED)
    matches = {c.cid: match(tables, cfg, model, frame, a.cid, c.cid)
               for c in refs}
    raw = {cid for cid, r in matches.items() if r["raw"]}
    iota = {cid for cid, r in matches.items() if r["iota"]}
    undetermined = {cid for cid, r in matches.items()
                    if r["status"] == UNDETERMINED}
    elig20 = eligible_ids(elig)
    elig10 = eligible_ids(elig, extension=True)

    def pool(admitted):
        return [c for c in refs if c.cid in admitted and c.cid in compatible]

    primary = populations(a, pool(elig20), raw)
    same = [c for c in refs if c.operation == a.operation
            and c.object_type == a.object_type]
    other_obj = [c for c in refs if c.operation == a.operation
                 and c.object_type != a.object_type]
    other_op = [c for c in refs if c.operation != a.operation]
    funnel = {
        "G1": _funnel(same, elig20, compatible, raw, undetermined,
                      cfg.g1_min_distinct_words,
                      lambda cs: len(_distinct_words(c.cid for c in cs))),
        "P2": _funnel(other_obj, elig20, compatible, raw, undetermined,
                      cfg.p2_min_additional_other_object, len),
        "P3": _funnel(other_op, elig20, compatible, raw, undetermined,
                      cfg.p3_min_additional_other_operation, len),
    }
    pa = tables.x(model, frame, a.cid)
    context = []
    a_informative = False
    if usable(pa, cfg):
        lo, hi = cfg.a_headroom_band
        a_informative = _frac(lo) <= Fraction(pa.k, pa.n) <= _frac(hi)
        if not a_informative:
            context.append(f"A_EXTREME_FOLLOWABILITY (p_A={pa.p:.3f})")
    else:
        context.append("A_CELL_INCOMPLETE")
    return {
        "model": model, "frame": frame, "b_limit": m, "a": a.cid,
        "p_a": pa.p, "n_a": pa.n, "a_informative": a_informative,
        "populations": primary,
        "weights": {gname: {cid: str(w) for cid, w in
                            hierarchical_weights(members,
                                                 cfg.weights_mode).items()}
                    for gname, members in primary.items()},
        "counts_by_operation_object": {
            gname: _taxonomy_counts(members)
            for gname, members in primary.items()},
        "coverage": coverage(a, primary, funnel, cfg),
        "funnel": funnel, "context": context,
        "sensitivity": {
            "iota_matching": populations(a, pool(elig20), iota),
            "extension_10": populations(a, pool(elig10), raw),
            "iota_undefined": sorted(cid for cid, r in matches.items()
                                     if r.get("iota_undefined")),
        },
        "raw_vs_iota": {g: {
            "raw_only": sorted(set(primary[g]) - set(
                populations(a, pool(elig20), iota)[g])),
            "iota_only": sorted(set(populations(a, pool(elig20), iota)[g])
                                - set(primary[g]))} for g in ("G1", "G3", "G5")},
        "excluded": {"unresolved_compatibility": unresolved,
                     "matching_undetermined": sorted(undetermined),
                     "eligibility_undetermined": sorted(
                         cid for cid, e in elig.items()
                         if e["status"] == UNDETERMINED)},
        "matching": {cid: r for cid, r in sorted(matches.items())},
    }


def _taxonomy_counts(members: Iterable[str]) -> dict[str, int]:
    by_id = L.constraint_by_id()
    counts: dict[str, int] = {}
    for cid in members:
        c = by_id[cid]
        key = f"{c.operation}/{c.object_type}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def feasibility(reports: list[dict[str, Any]], cfg: CFG.PilotConfig,
                b_limits: Iterable[int]) -> dict[str, Any]:
    """§23's diagnostic: each contrast supported in at least
    ``feasibility_min_configs`` configurations, spanning at least
    ``feasibility_min_models`` models and every selected B limit. Only
    configurations whose A is informative (D08) count."""
    b_limits = sorted(b_limits)
    planned = len(cfg.models) * len(cfg.frames) * len(b_limits)
    out: dict[str, Any] = {"planned_configurations": planned}
    for name in ("P1", "P2", "P3"):
        # D08 (revised): a configuration whose A is outside the headroom band
        # is reported but never counts toward the target.
        nominal = [r for r in reports if r["coverage"][name]["supported"]]
        supported = [r for r in nominal if r.get("a_informative", True)]
        models = sorted({r["model"] for r in supported})
        limits = sorted({r["b_limit"] for r in supported})
        reasons: dict[str, int] = {}
        for r in reports:
            for reason in r["coverage"][name]["reasons"]:
                code = reason.split(" (")[0]
                reasons[code] = reasons.get(code, 0) + 1
        ok = (len(supported) >= cfg.feasibility_min_configs
              and len(models) >= cfg.feasibility_min_models
              and limits == b_limits)
        failures = []
        if len(supported) < cfg.feasibility_min_configs:
            failures.append(f"supported in {len(supported)} of {planned} "
                            f"configurations (< {cfg.feasibility_min_configs})")
        if len(models) < cfg.feasibility_min_models:
            failures.append(f"spans {len(models)} models "
                            f"(< {cfg.feasibility_min_models})")
        if limits != b_limits:
            failures.append(f"spans B limits {limits}, not {b_limits}")
        out[name] = {"feasible": ok, "supported_configurations": len(supported),
                     "supported_including_uninformative_a": len(nominal),
                     "coverage_share": len(supported) / planned if planned else 0,
                     "models": models, "b_limits": limits,
                     "failures": failures, "reason_counts": reasons}
    out["all_feasible"] = all(out[n]["feasible"] for n in ("P1", "P2", "P3"))
    return out
