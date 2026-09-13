"""Read the screen cache and answer Q1, Q2 and Q3 with the registered rules.

Nothing is decided here that the registered code can decide. §12.3 selection
runs through ``dci1v4.stages.gates.select_severity``; §13.2 admission runs
through ``cal_screen_v4.admission.admit``, which the frozen protocol proves is
``dci1v4.stages.gates.admit_family``; §12.4 adequacy applies the registered
constants. What this module adds is the plumbing: block means, topic-clustered
bootstrap intervals, and the pre-screen values §13.2 condition 2 reads.
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.protocol import constants as C
from dci1v4.verifiers.constraints import FOCAL_GRID, TARGET_GRID

from bgrid_screen_v4 import focal
from cal_screen_v4 import admission as ad
from cal_screen_v4 import plan as pl
from cal_screen_v4.lowerbound_run import LOWER_BOUND_FAMILIES
from fs_screen_v4.constraints import CANDIDATES

#: The three rate families (budgets, like B) and the three lower-bound families
#: (production, like A) are reported separately throughout: they answer
#: different questions and lumping them would hide the class contrast.
RATE_FAMILIES = tuple(pl.CANDIDATE_FAMILIES)

DCI1 = Path(__file__).resolve().parent.parent.parent
EVIDENCE = DCI1 / "evidence" / "cal-screen-v4"
FS_RESULTS = DCI1 / "reports" / "fs_screen_v4" / "results.json"


# ------------------------------------------------------------------ loading
def load_rows(model: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The main arm, plus the registered-pool arm when it has been run.

    The four-rung ``registered_control`` arm of the main pass and the 24-rung
    ``registered_pool`` arm are two measurements of the same families. When the
    pool arm exists it supersedes the control arm -- its shortlist is the §12.2
    rule rather than one rung per family -- and the control rows are dropped so
    that no cell mean silently averages two seed streams at eight draws instead
    of the registered four.
    """
    hits = sorted(EVIDENCE.glob(f"{model}/screen-cap*/cache.jsonl"))
    if not hits:
        raise FileNotFoundError(f"no calibration-screen cache for {model}")
    main = [json.loads(line) for line in hits[-1].open()]
    pool_path = hits[-1].parent / "cache_registered_pool.jsonl"
    lower_path = hits[-1].parent / "cache_lower_bound.jsonl"
    provenance = {"main_cache": str(hits[-1].relative_to(EVIDENCE.parent.parent)),
                  "main_rows": len(main), "registered_pool_arm": False,
                  "lower_bound_arm": False}
    if pool_path.exists():
        pool = [json.loads(line) for line in pool_path.open()]
        # The four-rung control arm and the 24-rung pool arm measure the same
        # families at DIFFERENT rungs, chosen by different rules: the control
        # arm takes the rung nearest A on the floored pre-screen curve, the pool
        # arm brackets the anchor by the §12.2 shortlist rule. Neither dominates
        # -- on gemma-3n-E4B the control arm's RF3:4 sits inside the caliper and
        # the pool arm's RF3:{6,7,8} do not. So the two are UNIONED rather than
        # one superseding the other, and where a rung appears in both the pool
        # arm's rows win, so no cell mean ever averages two seed streams at
        # eight draws instead of the registered four.
        covered = {(r["stem"], r["kind"], r["severity"]) for r in pool}
        kept = [r for r in main
                if r["arm"] != "registered_control"
                or (r["stem"], r["kind"], r["severity"]) not in covered]
        dropped = len(main) - len(kept)
        main = kept + pool
        provenance.update({
            "registered_pool_arm": True,
            "pool_cache": str(pool_path.relative_to(EVIDENCE.parent.parent)),
            "pool_rows": len(pool),
            "control_arm_rows_dropped_as_duplicates": dropped,
            "control_arm_disposition": ("unioned with the pool arm; control "
                                        "rows are dropped only for rungs the "
                                        "pool arm also measures")})
    if lower_path.exists():
        lower = [json.loads(line) for line in lower_path.open()]
        main = main + lower
        provenance.update({
            "lower_bound_arm": True,
            "lower_bound_cache": str(lower_path.relative_to(
                EVIDENCE.parent.parent)),
            "lower_bound_rows": len(lower)})
    return main, provenance


def block_means(rows: Sequence[Mapping[str, Any]], field: str
                ) -> dict[tuple[str, str, int], dict[str, float]]:
    """Per (stem, kind, severity) the per-topic mean of ``field`` over draws."""
    buckets: dict[tuple[str, str, int], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    for row in rows:
        key = (row["stem"], row["kind"], row["severity"])
        buckets[key][row["topic_id"]].append(float(row[field]))
    return {key: {t: sum(v) / len(v) for t, v in topics.items()}
            for key, topics in buckets.items()}


def draw_level(rows: Sequence[Mapping[str, Any]], key: tuple[str, str, int]
               ) -> dict[tuple[str, int], int]:
    """Draw-level 0/1 verdicts keyed by (topic, draw index).

    §13.2 condition 1's Newcombe interval is a PAIRED interval, and the pairing
    that matters is the topic: the same question is put to the model under the
    reference and under A. Draws within a topic are exchangeable, so pairing
    draw k with draw k is arbitrary. It is also conservative: an arbitrary
    within-topic pairing can only inflate the discordant counts the Newcombe
    interval reads, which widens the interval and makes admission harder, never
    easier. That is the right direction for a caliper.
    """
    out: dict[tuple[str, int], int] = {}
    for row in rows:
        if (row["stem"], row["kind"], row["severity"]) == key:
            out[(row["topic_id"], row["draw_index"])] = 1 if row["passed"] else 0
    return out


def rate(values: Mapping[str, float]) -> float:
    return sum(values.values()) / len(values)


def clustered_se(values: Mapping[str, float]) -> float:
    xs = list(values.values())
    n = len(xs)
    if n < 2:
        return float("nan")
    mean = sum(xs) / n
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1) / n)


def bootstrap_ci(values: Mapping[str, float], *, resamples: int, seed: int
                 ) -> list[float]:
    xs = list(values.values())
    rng = random.Random(seed)
    draws = sorted(sum(rng.choices(xs, k=len(xs))) / len(xs)
                   for _ in range(resamples))
    lo = draws[max(0, int(math.floor(0.025 * resamples)) - 1)]
    hi = draws[min(resamples - 1, int(math.ceil(0.975 * resamples)) - 1)]
    return [lo, hi]


# ---------------------------------------------------------- the three answers
FS_EVIDENCE = DCI1 / "evidence" / "fs-screen-v4"


def prescreen_precision(model: str, n_star: int) -> dict[str, Any]:
    """How much of §13.2 condition 2 is noise.

    Condition 2 requires the reference-minus-A solo distance to be at most 0.15
    on the disjoint 24 pre-screen topics. Both terms are §12.2 measurements:
    24 topics at ONE draw. This computes the paired standard error of that
    difference from the FORM x STEM screen's own rows, so the comparison
    between the caliper and its own precision is measured rather than assumed.
    """
    hits = sorted(FS_EVIDENCE.glob(f"{model}/screen-cap*/cache.jsonl"))
    if not hits:
        return {"unavailable": "no FORM x STEM cache"}
    by_cell: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for line in hits[-1].open():
        row = json.loads(line)
        if row.get("stem") != "floored" or row.get("companion"):
            continue
        for score in row["scores"]:
            if score["kind"] != row["kind"]:
                continue
            by_cell[(row["kind"], row["severity"])][row["topic_id"]] = (
                1.0 if score["passed"] else 0.0)
    anchor = by_cell.get(("A", n_star))
    if not anchor:
        return {"unavailable": f"no floored pre-screen A cell at n={n_star}"}
    out: dict[str, Any] = {
        "topics": len(anchor), "draws_per_cell": 1,
        "caliper": C.REFERENCE_PRESCREEN_CALIPER, "pairs": {}}
    ses = []
    for (kind, severity), cells in sorted(by_cell.items()):
        if kind in ("A", "B"):
            continue
        shared = sorted(set(cells) & set(anchor))
        if len(shared) < 2:
            continue
        differences = [cells[t] - anchor[t] for t in shared]
        se = clustered_se({t: d for t, d in zip(shared, differences)})
        ses.append(se)
        out["pairs"][f"{kind}:{severity}"] = {
            "difference": sum(differences) / len(differences),
            "paired_se": se, "topics": len(shared)}
    if ses:
        out["median_paired_se"] = sorted(ses)[len(ses) // 2]
        out["reading"] = (
            f"the caliper is {C.REFERENCE_PRESCREEN_CALIPER} and the median "
            f"paired standard error of the quantity it bounds is "
            f"{sorted(ses)[len(ses) // 2]:.4f} on these rows. A reference whose "
            f"true pre-screen distance is zero is rejected by condition 2 with "
            f"probability 2*Phi(-{C.REFERENCE_PRESCREEN_CALIPER}/se).")
    return out


def prescreen_tables_m4(model: str) -> dict[str, Any] | None:
    """Pre-screen solo rates from the M_cal-draw arm, when it has been run.

    Same 24 topics, same stem, same wordings, same verifier as the one-draw
    §12.2 measurement; four times the draws. Never merged with the calibration
    tables -- these are pre-screen topics and they feed §13.2 condition 2 only.
    """
    hits = sorted(EVIDENCE.glob(f"{model}/screen-cap*/cache_prescreen_m4.jsonl"))
    if not hits:
        return None
    rows = [json.loads(line) for line in hits[-1].open()]
    buckets: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    for row in rows:
        buckets[(row["kind"], row["severity"])][row["topic_id"]].append(
            1.0 if row["passed"] else 0.0)
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for (kind, severity), topics in buckets.items():
        means = {t: sum(v) / len(v) for t, v in topics.items()}
        out[kind][severity] = sum(means.values()) / len(means)
    return {"rates": {k: dict(sorted(v.items())) for k, v in out.items()},
            "rows": len(rows),
            "source": str(hits[-1].relative_to(EVIDENCE.parent.parent))}


def prescreen_tables(model: str) -> dict[str, Any]:
    """§13.2 condition 2 reads the disjoint 24 pre-screen topics. The FORM x
    STEM screen measured every quantity this screen needs, under both stems, so
    the values are read rather than regenerated."""
    data = json.loads(FS_RESULTS.read_text())["severity_tables"][model]
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for key, entry in data.items():
        form, stem, kind, severity = key.split("|")
        if stem != "floored":
            continue
        out[kind][int(severity)] = entry["raw"]
    return {k: dict(sorted(v.items())) for k, v in out.items()}


def condition_2_at_m4(model: str, *, n_star: int, families: Sequence[str],
                      passed, vacuous, topics, a_calibration, rows,
                      a_draws_map) -> dict[str, Any]:
    """The registered rule, with condition 2's pre-screen term measured at
    M_cal draws instead of one.

    Nothing else moves: the same 0.15 caliper, the same 24 topics, the same
    stem, the same wordings, the same verifier, and every other condition
    unchanged and read from the calibration set exactly as before.
    """
    table = prescreen_tables_m4(model)
    if table is None:
        return {"unavailable": "the M_cal pre-screen arm has not been run"}
    rates = table["rates"]
    a_prescreen = rates.get("A", {}).get(n_star)
    if a_prescreen is None:
        return {"unavailable": f"no M_cal pre-screen A cell at n={n_star}"}
    results = []
    for family in families:
        severities = sorted(sev for (s, k, sev) in passed
                            if s == "floored" and k == family)
        calibration = {sev: [passed[("floored", family, sev)][t]
                             for t in topics] for sev in severities}
        vac = {sev: rate(vacuous[("floored", family, sev)])
               for sev in severities}
        draws = {}
        for sev in severities:
            ref_map = draw_level(rows, ("floored", family, sev))
            shared = sorted(set(ref_map) & set(a_draws_map))
            draws[sev] = ([ref_map[k] for k in shared],
                          [a_draws_map[k] for k in shared])
        results.append(ad.admit(
            family, n_star=n_star, calibration=calibration,
            a_calibration=a_calibration, prescreen=rates.get(family, {}),
            a_prescreen=a_prescreen, vacuity=vac, draw_level=draws,
            focal_grid=focal.SCREEN_FOCAL_GRID,
            missing_prescreen="abstain"))
    return {
        "what": ("the registered §13.2 rule with condition 2's pre-screen term "
                 "measured at M_cal = 4 draws on the same 24 topics. The "
                 "criterion is unchanged; only the precision of the quantity it "
                 "reads changes. Reported beside the registered-precision "
                 "result, never in place of it."),
        "a_prescreen_at_M_cal": a_prescreen,
        "a_prescreen_at_one_draw": prescreen_tables(model).get("A", {}).get(n_star),
        "source": table["source"], "rows": table["rows"],
        "candidates": ad.choose_final([r for r in results
                                       if r["family"] in RATE_FAMILIES]),
        "lower_bound": ad.choose_final([r for r in results
                                        if r["family"] in LOWER_BOUND_FAMILIES]),
        "registered_control": ad.choose_final(
            [r for r in results if r["family"] not in CANDIDATES]),
        "enlarged_pool": ad.choose_final(results),
        "table": results,
    }


def analyse(model: str, *, resamples: int = 10000, seed: int = 202608220
            ) -> dict[str, Any]:
    rows, provenance = load_rows(model)
    passed = block_means(rows, "passed")
    vacuous = block_means(rows, "vacuous_pass")
    graded = block_means(rows, "graded")
    words = block_means(rows, "word_count")
    truncated = block_means(rows, "truncated")
    prescreen = prescreen_tables(model)

    def curve(stem: str, kind: str) -> dict[int, float]:
        return {sev: rate(v) for (s, k, sev), v in passed.items()
                if s == stem and k == kind}

    # ---- Q2/Q3: the outcome constraints
    outcomes: dict[str, Any] = {}
    for stem in ("floored", "current"):
        a_curve = curve(stem, "A")
        b_curve = curve(stem, "B")
        entry: dict[str, Any] = {"A_curve": a_curve, "B_curve": b_curve}
        entry["registered_grid"] = ad.select_outcomes(
            a_curve, b_curve, target_grid=TARGET_GRID, focal_grid=FOCAL_GRID)
        entry["extended_grid"] = ad.select_outcomes(
            a_curve, b_curve, target_grid=TARGET_GRID,
            focal_grid=focal.SCREEN_FOCAL_GRID)
        entry["B_vacuity_by_m"] = {
            sev: rate(v) for (s, k, sev), v in vacuous.items()
            if s == stem and k == "B"}
        entry["B_words_median_by_m"] = {
            sev: sorted(v.values())[len(v) // 2]
            for (s, k, sev), v in words.items() if s == stem and k == "B"}
        entry["B_truncation_by_m"] = {
            sev: rate(v) for (s, k, sev), v in truncated.items()
            if s == stem and k == "B"}
        entry["any_rung_meets_12_4"] = [
            sev for sev, value in sorted(entry["B_vacuity_by_m"].items())
            if value <= C.REGIME_VACUITY_MAX]
        outcomes[stem] = entry

    floored = outcomes["floored"]
    selection = floored.get("extended_grid", {})
    n_star = (selection.get("A", {}) or {}).get("selected")
    m_star_registered = ((floored.get("registered_grid", {}).get("B", {}) or {})
                         .get("selected"))
    m_star_extended = (selection.get("B", {}) or {}).get("selected")
    # The extended grid contains the registered one, so a model whose only
    # in-band rung is m = 11 or 12 is identified ONLY under Amendment C. That
    # distinction is the whole point of carrying both selections.
    only_under_amendment_c = (m_star_registered is None
                              and m_star_extended is not None)

    def share_above(key: tuple[str, str, int], bound: float) -> float:
        """The share of DRAWS whose graded score exceeds ``bound``."""
        hits = [1.0 if float(r["graded"]) > bound else 0.0 for r in rows
                if (r["stem"], r["kind"], r["severity"]) == key]
        return sum(hits) / len(hits) if hits else float("nan")

    # §12.4 clause by clause at EVERY rung, not only at m*. The two clauses
    # pull against each other for a word-length budget: a permissive m raises
    # compliance into the band and simultaneously pushes the graded mean toward
    # 1, because a failing answer usually has only two or three words over the
    # limit out of sixty. Reporting the whole grid shows whether a feasible
    # rung exists at all, which reporting m* alone cannot.
    by_rung: dict[str, Any] = {}
    for stem in ("floored", "current"):
        entry = outcomes[stem]
        rows_out = []
        for m in focal.SCREEN_FOCAL_GRID:
            key = (stem, "B", m)
            if key not in passed:
                continue
            compliance = rate(passed[key])
            vac = rate(vacuous[key])
            g_mean = rate(graded[key])
            g_share = share_above(key, C.GRADED_DEGENERACY_HIGH)
            low, high = C.FOCAL_BAND
            rows_out.append({
                "m": m, "in_registered_grid": m in FOCAL_GRID,
                "solo_compliance": compliance,
                "inside_band": low <= compliance <= high,
                "vacuity": vac, "vacuity_ok": vac <= C.REGIME_VACUITY_MAX,
                "graded_mean": g_mean,
                "graded_mean_ok": g_mean <= C.GRADED_DEGENERACY_HIGH,
                "graded_share_above_0_99": g_share,
                "graded_share_ok": g_share <= C.GRADED_DEGENERACY_HIGH,
                "feasible_mean_reading": (low <= compliance <= high
                                          and vac <= C.REGIME_VACUITY_MAX
                                          and g_mean <= C.GRADED_DEGENERACY_HIGH),
                "feasible_share_reading": (low <= compliance <= high
                                           and vac <= C.REGIME_VACUITY_MAX
                                           and g_share <= C.GRADED_DEGENERACY_HIGH),
            })
        by_rung[stem] = rows_out

    adequacy: dict[str, Any] = {}
    for stem in ("floored", "current"):
        entry = outcomes[stem]
        for label, m in (("registered_grid", m_star_registered),
                         ("extended_grid", m_star_extended)):
            if m is None or n_star is None:
                continue
            keys = {"A": (stem, "A", n_star), "B": (stem, "B", m)}
            means = {name: rate(graded[key]) if key in graded else float("nan")
                     for name, key in keys.items()}
            shares = {name: share_above(key, C.GRADED_DEGENERACY_HIGH)
                      for name, key in keys.items()}
            record = {
                "reading_mean_graded": ad.regime_adequacy(
                    b_solo_vacuity=entry["B_vacuity_by_m"].get(m, float("nan")),
                    graded_distribution=means),
                "reading_share_above_0_99": ad.regime_adequacy(
                    b_solo_vacuity=entry["B_vacuity_by_m"].get(m, float("nan")),
                    graded_distribution=shares),
                "graded_mean": means, "graded_share_above_0_99": shares,
                "m": m, "n_star": n_star,
                "note": ("§12.4's graded clause has two readings and the "
                         "registered code fixes neither; both are reported"),
            }
            record["passed_under_both_readings"] = (
                record["reading_mean_graded"]["passed"]
                and record["reading_share_above_0_99"]["passed"])
            record["readings_disagree"] = (
                record["reading_mean_graded"]["passed"]
                != record["reading_share_above_0_99"]["passed"])
            adequacy[f"{stem}:{label}"] = record

    # ---- Q1: §13.2 admission, on the floored stem, against A at n*
    admission: dict[str, Any] = {"skipped": "no n* under the floored stem"}
    if n_star is not None:
        a_cells = passed[("floored", "A", n_star)]
        topics = sorted(a_cells)
        a_calibration = [a_cells[t] for t in topics]
        a_draws_map = draw_level(rows, ("floored", "A", n_star))
        a_prescreen = prescreen.get("A", {}).get(n_star)

        family_results = []
        # Every family the screen actually measured: the rate candidates, the
        # lower-bound candidates when that arm has run, and every registered
        # family the pool or control arm carried.
        measured = {k for (s, k, _) in passed if s == "floored"
                    and k not in ("A", "B")}
        families = ([f for f in pl.CANDIDATE_FAMILIES if f in measured]
                    + [f for f in LOWER_BOUND_FAMILIES if f in measured]
                    + sorted(k for k in measured if k not in CANDIDATES))
        for family in families:
            severities = sorted(sev for (s, k, sev) in passed
                                if s == "floored" and k == family)
            calibration = {sev: [passed[("floored", family, sev)][t]
                                 for t in topics] for sev in severities}
            vac = {sev: rate(vacuous[("floored", family, sev)])
                   for sev in severities}
            draws = {}
            for sev in severities:
                ref_map = draw_level(rows, ("floored", family, sev))
                shared = sorted(set(ref_map) & set(a_draws_map))
                draws[sev] = ([ref_map[k] for k in shared],
                              [a_draws_map[k] for k in shared])
            family_results.append(ad.admit(
                family, n_star=n_star, calibration=calibration,
                a_calibration=a_calibration,
                prescreen=prescreen.get(family, {}),
                a_prescreen=(a_prescreen if a_prescreen is not None else 0.0),
                vacuity=vac, draw_level=draws,
                focal_grid=focal.SCREEN_FOCAL_GRID))
        # Condition 2 applied only where its input exists. §12.2 measures all
        # 94 rungs on the pre-screen topics, so in the real study every rung
        # has a value; the floored-stem pre-screen available to this screen
        # covers only the current-stem caliper rungs, and rejecting a rung for
        # that is a data-availability artifact rather than a criterion. This is
        # the disposition the matrix screen's reference set is taken from, and
        # the strict one is reported beside it.
        abstain = []
        for family in families:
            severities = sorted(sev for (s, k, sev) in passed
                                if s == "floored" and k == family)
            calibration = {sev: [passed[("floored", family, sev)][t]
                                 for t in topics] for sev in severities}
            vac = {sev: rate(vacuous[("floored", family, sev)])
                   for sev in severities}
            draws = {}
            for sev in severities:
                ref_map = draw_level(rows, ("floored", family, sev))
                shared = sorted(set(ref_map) & set(a_draws_map))
                draws[sev] = ([ref_map[k] for k in shared],
                              [a_draws_map[k] for k in shared])
            abstain.append(ad.admit(
                family, n_star=n_star, calibration=calibration,
                a_calibration=a_calibration,
                prescreen=prescreen.get(family, {}),
                a_prescreen=(a_prescreen if a_prescreen is not None else 0.0),
                vacuity=vac, draw_level=draws,
                focal_grid=focal.SCREEN_FOCAL_GRID,
                missing_prescreen="abstain"))

        # The condition-2 sensitivity: identical inputs, disjoint-sample
        # confirmation switched off. Diagnostic only; it admits nothing.
        no_c2 = []
        for family in families:
            severities = sorted(sev for (s, k, sev) in passed
                                if s == "floored" and k == family)
            calibration = {sev: [passed[("floored", family, sev)][t]
                                 for t in topics] for sev in severities}
            vac = {sev: rate(vacuous[("floored", family, sev)])
                   for sev in severities}
            draws = {}
            for sev in severities:
                ref_map = draw_level(rows, ("floored", family, sev))
                shared = sorted(set(ref_map) & set(a_draws_map))
                draws[sev] = ([ref_map[k] for k in shared],
                              [a_draws_map[k] for k in shared])
            no_c2.append(ad.admit(
                family, n_star=n_star, calibration=calibration,
                a_calibration=a_calibration,
                prescreen=prescreen.get(family, {}),
                a_prescreen=(a_prescreen if a_prescreen is not None else 0.0),
                vacuity=vac, draw_level=draws,
                focal_grid=focal.SCREEN_FOCAL_GRID,
                prescreen_caliper=float("inf")))

        candidate_results = [r for r in family_results
                             if r["family"] in RATE_FAMILIES]
        lower_results = [r for r in family_results
                         if r["family"] in LOWER_BOUND_FAMILIES]
        control_results = [r for r in family_results
                           if r["family"] not in CANDIDATES]
        admission = {
            "anchor": {"n_star": n_star, "A_solo_compliance": rate(a_cells),
                       "clustered_se": clustered_se(a_cells),
                       "ci95": bootstrap_ci(a_cells, resamples=resamples,
                                            seed=seed),
                       "A_prescreen_compliance": a_prescreen},
            "candidates": ad.choose_final(candidate_results),
            "candidate_table": candidate_results,
            "lower_bound": ad.choose_final(lower_results),
            "lower_bound_table": lower_results,
            "class_matched_companion": {
                "what": ("the best-admitted lower-bound family. A is the only "
                         "PRODUCTION constraint in the registered pool and "
                         "every other constraint is a budget, so a positive "
                         "Delta_R against budgets alone cannot separate 'A is "
                         "damaging to B' from 'a production companion is "
                         "damaging to a budget outcome'. This is the companion "
                         "that separates them."),
                "selected": (ad.choose_final(lower_results)["chosen"][:1]
                             or None)},
            "registered_control": ad.choose_final(control_results),
            "registered_control_table": control_results,
            "enlarged_pool": ad.choose_final(family_results),
            "enlarged_pool_condition_2_where_measured": {
                "what": ("conditions 1 and 3-6 as registered, with condition 2 "
                         "applied only to rungs that have a floored-stem "
                         "pre-screen measurement. This is the disposition the "
                         "matrix screen takes its reference set from, and it "
                         "is declared in the matrix screen's frozen protocol."),
                "result": ad.choose_final(abstain),
                "table": abstain,
                "rungs_without_a_prescreen_measurement": sorted(
                    f"{r['family']}:{c['severity']}" for r in abstain
                    for c in r["candidates"] if c.get("prescreen_missing")),
            },
            "condition_2_precision": prescreen_precision(model, n_star),
            # Which disposition the matrix screen takes its reference set from,
            # named on the artifact so it is auditable rather than implied.
            "matrix_reference_set": None,     # filled below

            "condition_2_at_M_cal": condition_2_at_m4(
                model, n_star=n_star, families=families, passed=passed,
                vacuous=vacuous, topics=topics, a_calibration=a_calibration,
                rows=rows, a_draws_map=a_draws_map),
            "condition_2_sensitivity": {
                "what": ("the registered rule with §13.2 condition 2 -- the "
                         "disjoint 24-topic pre-screen confirmation -- switched "
                         "off. DIAGNOSTIC ONLY. It admits nothing and no "
                         "reference decision may rest on it."),
                "candidates": ad.choose_final(
                    [r for r in no_c2 if r["family"] in RATE_FAMILIES]),
                "lower_bound": ad.choose_final(
                    [r for r in no_c2 if r["family"] in LOWER_BOUND_FAMILIES]),
                "registered_control": ad.choose_final(
                    [r for r in no_c2 if r["family"] not in CANDIDATES]),
                "enlarged_pool": ad.choose_final(no_c2),
            },
        }

    # ---- the disposition the matrix screen reads
    #
    # Preference order, most to least faithful to the registered rule *given
    # the data available to this screen*:
    #   1. condition 2 with its pre-screen input measured at M_cal on the same
    #      24 topics -- the registered criterion, the registered threshold, the
    #      registered sample, four draws instead of one;
    #   2. condition 2 applied only where a one-draw input exists;
    # and in both cases every other condition exactly as registered on the
    # calibration set. The strict registered-precision count is reported beside
    # it and neither is a claim.
    if "anchor" in admission:
        # The matrix takes the disposition CLOSEST TO THE REGISTERED RULE that
        # is not contaminated by this screen's own data gap: conditions 1 and
        # 3-6 exactly as registered on the 96 calibration topics, and condition
        # 2 with its registered §12.2 input -- 24 topics at one draw -- applied
        # wherever that input exists.
        #
        # NOT the M_cal variant, even though it is the better measurement.
        # §12.2 registers one draw, and letting a screen-invented precision
        # upgrade choose the design would be the screen deciding a protocol
        # question. It is reported as a sensitivity instead, and on E2B it is
        # a large one: A's pre-screen compliance at n* reads 0.583 at one draw
        # and 0.469 at four, a 0.115 shift in the anchor every reference is
        # measured against, which reverses which families condition 2 admits.
        where = admission["enlarged_pool_condition_2_where_measured"]["result"]
        at_m4 = admission.get("condition_2_at_M_cal", {})
        admission["matrix_reference_set"] = {
            "disposition": ("conditions 1 and 3-6 as registered on the 96 "
                            "calibration topics; condition 2 with its "
                            "registered one-draw §12.2 input, applied where "
                            "that input exists"),
            "chosen": where["chosen"],
            "admitted": where["admitted"],
            "admitted_families": where["admitted_families"],
            "n_admitted": where["n_admitted"],
            "identification_status": where["identification_status"],
            "class_matched": (admission.get("class_matched_companion", {})
                              or {}).get("selected") or [],
            "strict_registered_precision": {
                "n_admitted": admission["enlarged_pool"]["n_admitted"],
                "admitted_families":
                    admission["enlarged_pool"]["admitted_families"]},
            "sensitivity_condition_2_at_M_cal": {
                "n_admitted": at_m4.get("enlarged_pool", {}).get("n_admitted"),
                "admitted_families": at_m4.get("enlarged_pool", {}).get(
                    "admitted_families"),
                "a_prescreen_one_draw": at_m4.get("a_prescreen_at_one_draw"),
                "a_prescreen_at_M_cal": at_m4.get("a_prescreen_at_M_cal"),
            },
            "sensitivity_condition_2_off": {
                "n_admitted": admission["condition_2_sensitivity"][
                    "enlarged_pool"]["n_admitted"],
                "admitted_families": admission["condition_2_sensitivity"][
                    "enlarged_pool"]["admitted_families"]},
        }

    # ---- the criteria, as frozen
    q1 = admission.get("candidates", {}).get("n_admitted")
    verdicts = {
        "Q1_three_candidate_families": {
            "required": C.N_FINAL_REFERENCES, "observed": q1,
            "met": (q1 is not None and q1 >= C.N_FINAL_REFERENCES)},
        "Q2_honest_focal_severity": {
            "registered_grid_m_star": m_star_registered,
            "extended_grid_m_star": m_star_extended,
            "met_on_registered_grid": m_star_registered is not None,
            "met_on_extended_grid": m_star_extended is not None,
            "identified_only_under_amendment_C": only_under_amendment_c,
            "registered_grid_diagnosis":
                (floored.get("registered_grid", {}).get("B", {}) or {})
                .get("status")},
        "Q3_regime_adequacy": {
            k: {"mean_reading": v["reading_mean_graded"]["passed"],
                "share_reading": v["reading_share_above_0_99"]["passed"],
                "readings_disagree": v["readings_disagree"],
                "vacuity_clause_passed":
                    v["reading_mean_graded"]["b_solo_vacuity"]
                    <= C.REGIME_VACUITY_MAX}
            for k, v in adequacy.items()},
    }
    if m_star_extended is not None:
        cells = passed[("floored", "B", m_star_extended)]
        se = clustered_se(cells)
        value = rate(cells)
        low, high = C.FOCAL_BAND
        verdicts["Q2_honest_focal_severity"]["margin_in_standard_errors"] = (
            min(value - low, high - value) / se if se else float("nan"))
        verdicts["Q2_honest_focal_severity"]["selected_rung"] = {
            "m": m_star_extended, "solo_compliance": value, "clustered_se": se,
            "ci95": bootstrap_ci(cells, resamples=resamples, seed=seed + 3)}

    return {"model": model, "rows": len(rows), "provenance": provenance,
            "screen_protocol_hash": rows[0]["screen_protocol_hash"],
            "outcomes": outcomes, "regime_adequacy": adequacy,
            "regime_adequacy_by_rung": by_rung,
            "admission": admission, "verdicts": verdicts,
            "prescreen_source": str(FS_RESULTS.relative_to(DCI1))}


__all__ = ["load_rows", "block_means", "prescreen_tables", "analyse"]
