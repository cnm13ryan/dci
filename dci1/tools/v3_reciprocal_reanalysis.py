#!/usr/bin/env python3
"""What the v3 confirmatory rows do and do not identify about companion identity.

A read-only re-analysis of the closed v3 evidence tree. It changes nothing in
v3, recomputes nothing v3 recorded, and licenses no confirmatory claim: v3 is
closed and its registered result stands as `dci1/RESULTS_V3.md` records it.

**The identification statement is the point of this tool.** The v3 confirmatory
design carries six arms on the same 384 blocks -- A solo, A+B, A+R_1, A+R_2,
A+R_3, and the bare topic -- and *no* solo cell for B or for any reference. So:

  identified, same topics, paired within block
    D(A<-B), D(A<-R_j), the companion swap Delta^A and its per-reference
    components, companion uptake in the composed cell, joint success.

  NOT identified from these rows
    D(B<-A), D(R_j<-A), D(R_j<-B), Lambda, Delta_R, Xi. Each needs a solo cell
    for B or for a reference on the confirmatory topics, and none exists. The
    only solo rates for those constraints live in the Gate 2A cache on a
    DIFFERENT topic set (the 96 calibration topics), and pairing across the two
    sets manufactures a contrast the design never ran.

Section 3 reports the cross-set quantity anyway, as an explicitly bounded
diagnostic, because a previous review of this repository quoted it without the
bound. It is reported beside a direct measurement of the topic-set shift --
A's own solo compliance at n* on both sets, same constraint, same estimator --
so the size of the assumption is visible rather than implied.

Usage:  python tools/v3_reciprocal_reanalysis.py [--resamples 10000]
Writes: dci1/reports/v3_reanalysis/result.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Sequence

DCI1 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DCI1 / "src"))

from dci1v3.verifiers.families import (family_passes,   # noqa: E402
                                       focal_passes)
from dci1v3.verifiers.words import alpha_runs           # noqa: E402

EVIDENCE = DCI1 / "evidence" / "dci1-v3"
OUT = DCI1 / "reports" / "v3_reanalysis"
CLASSIFICATION = "DERIVED / POST-HOC re-analysis of closed v3 evidence"
COMPOSED_ARMS = ("AB", "AR1", "AR2", "AR3")


# ------------------------------------------------------------------ loading
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_confirmatory(model: str) -> tuple[dict, dict, dict]:
    """Block-level cell means for every arm, plus the design facts."""
    path = EVIDENCE / model / "confirmatory" / "cache.jsonl"
    passes: dict[tuple[str, str], list[int]] = defaultdict(list)
    uptake: dict[tuple[str, str], list[int]] = defaultdict(list)
    joint: dict[tuple[str, str], list[int]] = defaultdict(list)
    words: dict[tuple[str, str], list[int]] = defaultdict(list)
    order: dict[str, str] = {}
    severity: dict[str, tuple[str, int]] = {}
    n_values: set[int] = set()
    rows = 0
    for line in path.open():
        row = json.loads(line)
        arm, block = row["arm"], row["block_id"]
        rows += 1
        order[block] = row["order"]
        verdicts = row["verdicts"]
        target = 1 if verdicts["target_pass"] else 0
        passes[(arm, block)].append(target)
        words[(arm, block)].append(len(alpha_runs(row.get("raw_response") or "")))
        if "added_pass" in verdicts:
            added = 1 if verdicts["added_pass"] else 0
            uptake[(arm, block)].append(added)
            joint[(arm, block)].append(1 if (target and added) else 0)
            severity[arm] = (row["constraint_id"], row["severity"])
        if arm == "A" and row.get("n") is not None:
            n_values.add(int(row["n"]))
    blocks = sorted({b for _, b in passes})
    design = {"rows": rows, "blocks": len(blocks), "n_star": sorted(n_values),
              "arm_constraints": {k: list(v) for k, v in sorted(severity.items())},
              "source": str(path.relative_to(DCI1)), "sha256": sha256(path)}

    def table(store):
        return {arm: [sum(store[(arm, b)]) / len(store[(arm, b)])
                      if store[(arm, b)] else float("nan") for b in blocks]
                for arm in {a for a, _ in store}}

    cells = {"compliance": table(passes), "uptake": table(uptake),
             "joint": table(joint), "words": table(words)}
    strata = {"blocks": blocks, "order": [order[b] for b in blocks]}
    return cells, strata, design


def load_gate2a_solo(model: str) -> tuple[dict[str, float], dict[str, Any]]:
    """Solo compliance per cell on the 96 CALIBRATION topics. A different
    topic set from the confirmatory rows: never paired with them."""
    path = EVIDENCE / model / "gate2a" / "cache.jsonl"
    totals: dict[str, list[int]] = defaultdict(list)
    for line in path.open():
        row = json.loads(line)
        verdicts = row["verdicts"]
        # A solo records `target_pass`; every non-A solo cell records
        # `added_pass`, because in v3 the non-A constraint always occupied the
        # added slot. Same predicate, different key.
        value = verdicts.get("target_pass", verdicts.get("added_pass"))
        if value is None:
            raise KeyError(f"{row['kind']}: no pass verdict on a solo row")
        totals[row["kind"]].append(1 if value else 0)
    rates = {k: sum(v) / len(v) for k, v in sorted(totals.items())}
    return rates, {"source": str(path.relative_to(DCI1)), "sha256": sha256(path),
                   "topics": 96, "draws_per_cell": 1}


# ------------------------------------------------- estimation and resampling
def summarise(values: Sequence[float]) -> dict[str, float]:
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return {"estimate": mean, "se": float("nan"), "blocks": n}
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return {"estimate": mean, "se": math.sqrt(var / n), "blocks": n}


def stratified_bootstrap(per_block: dict[str, list[float]],
                         strata: Sequence[str], *, resamples: int,
                         seed: int) -> dict[str, Any]:
    """Block bootstrap, resampled WITHIN order stratum.

    Every quantity here is a mean of a per-block contribution, so the point
    estimate, the clustered standard error and every resample are computed from
    the same vector and the studentised statistic needs no inner loop.
    """
    names = list(per_block)
    index_by_stratum: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(strata):
        index_by_stratum[s].append(i)

    point = {k: summarise(v) for k, v in per_block.items()}
    rng = random.Random(seed)
    draws: dict[str, list[float]] = {k: [] for k in names}
    t_max: list[float] = []
    for _ in range(resamples):
        picked: list[int] = []
        for _, idx in sorted(index_by_stratum.items()):
            picked.extend(rng.choices(idx, k=len(idx)))
        worst = 0.0
        for name in names:
            column = per_block[name]
            sample = [column[i] for i in picked]
            stat = summarise(sample)
            draws[name].append(stat["estimate"])
            se = stat["se"]
            if se and not math.isnan(se):
                worst = max(worst, abs(stat["estimate"] - point[name]["estimate"]) / se)
        t_max.append(worst)

    t_max.sort()
    critical = t_max[min(len(t_max) - 1, int(math.ceil(0.95 * len(t_max))) - 1)]
    out: dict[str, Any] = {}
    for name in names:
        column = sorted(draws[name])
        lo = column[max(0, int(math.floor(0.025 * len(column))) - 1)]
        hi = column[min(len(column) - 1, int(math.ceil(0.975 * len(column))) - 1)]
        se = point[name]["se"]
        out[name] = {
            "estimate": point[name]["estimate"],
            "clustered_se": se,
            "ci95_percentile": [lo, hi],
            "ci95_simultaneous": [point[name]["estimate"] - critical * se,
                                  point[name]["estimate"] + critical * se],
            "blocks": point[name]["blocks"]}
    out["_simultaneous_critical_value"] = critical
    out["_resamples"] = resamples
    out["_family_size"] = len(names)
    return out


def contributions(cells: dict[str, dict[str, list[float]]],
                  keep: Callable[[int], bool] | None = None
                  ) -> dict[str, list[float]]:
    """The per-block contribution of every identified quantity."""
    compliance, uptake, joint = cells["compliance"], cells["uptake"], cells["joint"]
    n = len(compliance["A"])
    rows = [i for i in range(n) if (keep is None or keep(i))]
    refs = ("AR1", "AR2", "AR3")

    def col(store, arm):
        return [store[arm][i] for i in rows]

    a_solo, a_ab = col(compliance, "A"), col(compliance, "AB")
    a_ref = {r: col(compliance, r) for r in refs}
    out = {
        "D_A_from_B": [s - c for s, c in zip(a_solo, a_ab)],
        "delta_A": [sum(a_ref[r][i] for r in refs) / 3 - a_ab[i]
                    for i in range(len(rows))],
        "uptake_contrast_B_minus_Rbar": [
            col(uptake, "AB")[i] - sum(col(uptake, r)[i] for r in refs) / 3
            for i in range(len(rows))],
        "p_A_solo": a_solo, "p_A_composed_with_B": a_ab,
        "joint_success_AB": col(joint, "AB"),
        "uptake_B_in_AB": col(uptake, "AB"),
    }
    for r in refs:
        out[f"D_A_from_{r}"] = [s - c for s, c in zip(a_solo, a_ref[r])]
        out[f"delta_A_{r}"] = [a_ref[r][i] - a_ab[i] for i in range(len(rows))]
        out[f"p_A_composed_with_{r}"] = a_ref[r]
        out[f"joint_success_{r}"] = col(joint, r)
        out[f"uptake_{r}"] = col(uptake, r)
    return out


def accidental_compliance(model: str, arm_constraints: dict) -> dict[str, Any]:
    """§25: the rate at which an UNCONSTRAINED answer satisfies each constraint.

    v3's `TOPIC` arm carries the same 384 topics with no constraint at all, and
    its rows record only the target verdict. The other verifiers are applied to
    those responses here, read-only, so a compliance figure elsewhere can be
    read as delivery rather than as accident.

    The figure is length-dependent by construction -- a 23-word answer satisfies
    a max-word-length budget far more often by chance than a 330-word one -- and
    v3's unconstrained answers average 330 words, so these are the base rates at
    v3's own operating length and nowhere else.
    """
    path = EVIDENCE / model / "confirmatory" / "cache.jsonl"
    texts = [json.loads(line).get("raw_response") or "" for line in path.open()
             if '"TOPIC"' in line]
    if not texts:
        return {"unavailable": "no TOPIC arm"}
    words = [len(alpha_runs(t)) for t in texts]
    focal = arm_constraints.get("AB", ["B", None])[1]
    rates: dict[str, float] = {}
    if focal is not None:
        rates[f"B:{focal}"] = sum(1 for t in texts
                                  if focal_passes(t, focal)) / len(texts)
    for arm in ("AR1", "AR2", "AR3"):
        family, severity = arm_constraints[arm]
        rates[f"{family}:{severity}"] = sum(
            1 for t in texts if family_passes(family, t, severity)) / len(texts)
    return {"rows": len(texts), "mean_words": sum(words) / len(words),
            "rates": rates,
            "reading": ("near zero at v3's operating length, so v3 compliance "
                        "is delivery and not accident. It is not a length-free "
                        "statement: the same constraints on a 23-word answer "
                        "would show much higher accidental rates.")}


def vacuity_forced_delta_a(model: str) -> dict[str, Any]:
    """§17.4: Delta^A recomputed with every vacuous pass forced to a failure.

    This is the registered partial-identification bound, and it is the right
    instrument for the question "is this a vacuity artifact" -- unlike a
    restriction to non-vacuous responses, which drops rows selected on a
    consequence of the treatment (§9.3 says so, which is why the protocol
    forces rather than restricts).

    A's non-vacuity predicate is "non-empty and not truncated" (§9.3), with no
    word floor: A is an exact-count production constraint and a short answer
    that contains the target word the right number of times has satisfied it.
    """
    path = EVIDENCE / model / "confirmatory" / "cache.jsonl"
    arms = ("AB", "AR1", "AR2", "AR3")
    raw: dict[str, list[int]] = defaultdict(list)
    forced: dict[str, list[int]] = defaultdict(list)
    degenerate: dict[str, int] = defaultdict(int)
    for line in path.open():
        row = json.loads(line)
        if row["arm"] not in arms:
            continue
        passed = bool(row["verdicts"]["target_pass"])
        words = len(alpha_runs(row.get("raw_response") or ""))
        truncated = row.get("finish_reason") == "length"
        non_vacuous = words > 0 and not truncated
        raw[row["arm"]].append(1 if passed else 0)
        forced[row["arm"]].append(1 if (passed and non_vacuous) else 0)
        if passed and not non_vacuous:
            degenerate[row["arm"]] += 1

    def delta(table):
        return (sum(sum(table[a]) / len(table[a]) for a in arms[1:]) / 3
                - sum(table["AB"]) / len(table["AB"]))

    return {
        "raw_delta_A": delta(raw),
        "vacuity_forced_delta_A": delta(forced),
        "change": delta(forced) - delta(raw),
        "vacuous_passes_by_arm": dict(degenerate),
        "rows_by_arm": {a: len(raw[a]) for a in arms},
        "reading": (
            "the A-side composed cells are 111-167 mean words and essentially "
            "never vacuous, so the registered bound moves Delta^A by less than "
            "0.002. The same bound applied to the B+R pilot's Delta removes "
            "72-82% of it. That asymmetry is not incidental: it is what a "
            "length-monotone budget outcome does that an exact-count production "
            "outcome does not."),
    }


# ------------------------------------------------- the length-matched contrast
LENGTH_BINS = ((0, 60), (60, 90), (90, 120), (120, 160), (160, 220),
               (220, 10 ** 9))
MIN_CELL = 30


def _length_matched(rows: dict[str, list[tuple[int, int]]]) -> dict[str, Any]:
    arms = ("AB", "AR1", "AR2", "AR3")
    table, weight_total, weighted_gap, used = [], 0, 0.0, 0
    for low, high in LENGTH_BINS:
        cells = {a: [p for w, p in rows[a] if low <= w < high] for a in arms}
        entry: dict[str, Any] = {
            "bin": [low, high if high < 10 ** 9 else None],
            "n": {a: len(cells[a]) for a in arms}}
        if min(len(c) for c in cells.values()) < MIN_CELL:
            entry["thin"] = True
            table.append(entry)
            continue
        rates = {a: sum(cells[a]) / len(cells[a]) for a in arms}
        gap = sum(rates[a] for a in arms[1:]) / 3 - rates["AB"]
        entry.update({"rates": rates, "delta_A_in_bin": gap, "thin": False})
        table.append(entry)
        weight_total += len(cells["AB"])
        weighted_gap += len(cells["AB"]) * gap
        used += 1
    raw = (sum(sum(p for _, p in rows[a]) / len(rows[a]) for a in arms[1:]) / 3
           - sum(p for _, p in rows["AB"]) / len(rows["AB"]))
    return {"raw_delta_A": raw,
            "length_matched_delta_A": (weighted_gap / weight_total
                                       if weight_total else None),
            "bins_used": used, "bins_total": len(LENGTH_BINS),
            "mean_words": {a: sum(w for w, _ in rows[a]) / len(rows[a])
                           for a in arms},
            "by_bin": table}


def length_matched_delta_a(model: str) -> dict[str, Any]:
    """Delta^A computed WITHIN word-count bins, and the common support for it.

    Response length is a consequence of the companion (v4r2 §13.3) and §22
    registers it as a mediator the primary estimand is never conditioned on, so
    this is a collider-conditioned description and not a causal decomposition.
    It is here because the same description applied to the B side -- where the
    two cells are five-fold apart in length -- removes the whole of the B+R
    pilot's Delta, and the honest question is whether the A side behaves the
    same way. The common support answers that first: on the A side every arm is
    a composition containing A, so all four cells sit in the same length regime
    and the bins are populated in every arm.
    """
    path = EVIDENCE / model / "confirmatory" / "cache.jsonl"
    arms = ("AB", "AR1", "AR2", "AR3")
    rows: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for line in path.open():
        row = json.loads(line)
        if row["arm"] in arms:
            rows[row["arm"]].append(
                (len(alpha_runs(row.get("raw_response") or "")),
                 1 if row["verdicts"]["target_pass"] else 0))

    by_order: dict[str, dict[str, list[tuple[int, int]]]] = {
        o: defaultdict(list) for o in ("added_first", "target_first")}
    for line in path.open():
        row = json.loads(line)
        if row["arm"] in arms:
            by_order[row["order"]][row["arm"]].append(
                (len(alpha_runs(row.get("raw_response") or "")),
                 1 if row["verdicts"]["target_pass"] else 0))

    pooled = _length_matched(rows)
    return {
        **pooled,
        "weighting": "the AB cell's own length distribution",
        "by_order": {o: _length_matched(v) for o, v in by_order.items()},
        "common_support": (
            f"{pooled['bins_used']} of {len(LENGTH_BINS)} bins carry at least "
            f"{MIN_CELL} responses in all four arms"),
        "order_note": (
            "the two configurations are reported separately because the "
            "length differential between the AB cell and the AR cells is "
            "itself order-dependent, and so is the contrast"),
        "collider_caveat": (
            "length is a consequence of the companion (§13.3) and §22 forbids "
            "conditioning the primary estimand on it. This is a sub-population "
            "description, not a causal decomposition."),
    }


# --------------------------------------------------------------------- main
def analyse_model(model: str, *, resamples: int, seed: int) -> dict[str, Any]:
    cells, strata, design = load_confirmatory(model)
    solo_calibration, solo_provenance = load_gate2a_solo(model)
    orders = strata["order"]

    # --- section 1: identified on the confirmatory topics, block-paired
    primary_family = ["D_A_from_B", "D_A_from_AR1", "D_A_from_AR2",
                      "D_A_from_AR3", "delta_A"]
    per_reference_family = ["delta_A_AR1", "delta_A_AR2", "delta_A_AR3"]
    everything = contributions(cells)
    identified = {
        "pooled": stratified_bootstrap(
            {k: everything[k] for k in primary_family}, orders,
            resamples=resamples, seed=seed),
        "per_reference_simultaneous": stratified_bootstrap(
            {k: everything[k] for k in per_reference_family}, orders,
            resamples=resamples, seed=seed + 1),
        "levels": {k: summarise(v) for k, v in everything.items()
                   if k.startswith(("p_A", "joint_", "uptake_"))},
    }
    by_order: dict[str, Any] = {}
    for level in sorted(set(orders)):
        subset = contributions(cells, keep=lambda i, L=level: orders[i] == L)
        strata_subset = [L for L in orders if L == level]
        by_order[level] = stratified_bootstrap(
            {k: subset[k] for k in primary_family + per_reference_family},
            strata_subset, resamples=resamples, seed=seed + 2)
    identified["by_order"] = by_order

    # --- section 2: length, recorded not conditioned on
    words = {arm: summarise(values) for arm, values in cells["words"].items()}
    length_matched = length_matched_delta_a(model)
    vacuity_forced = vacuity_forced_delta_a(model)
    accidental = accidental_compliance(model, design["arm_constraints"])

    # --- section 3: the cross-set quantity, bounded
    n_star = design["n_star"][0] if len(design["n_star"]) == 1 else None
    arm_constraints = design["arm_constraints"]
    a_solo_calibration = solo_calibration.get(f"solo:A:{n_star}")
    a_solo_confirmatory = sum(cells["compliance"]["A"]) / len(cells["compliance"]["A"])
    shift = (None if a_solo_calibration is None
             else a_solo_confirmatory - a_solo_calibration)

    cross: dict[str, Any] = {
        "what_this_is": (
            "NOT a delivery loss. Each L below subtracts a composed rate "
            "measured on the 384 confirmatory topics from a solo rate measured "
            "on the 96 calibration topics. The two sets are disjoint and the "
            "contrast is unpaired, so L carries the topic-set shift as well as "
            "the companion effect."),
        "topic_set_shift_measured_on_A": {
            "constraint": f"A at n={n_star}, same constraint, same estimator",
            "solo_on_96_calibration_topics": a_solo_calibration,
            "solo_on_384_confirmatory_topics": a_solo_confirmatory,
            "shift": shift,
            "reading": (
                "the size of the assumption the L quantities below require: "
                "that this shift is the same for B and for each reference. It "
                "is measured for A only and is assumed, never shown, for the "
                "others.")},
        "L": {},
    }
    for arm in COMPOSED_ARMS:
        family, sev = arm_constraints[arm]
        key = f"solo:{family}:{sev}"
        solo = solo_calibration.get(key)
        composed = sum(cells["uptake"][arm]) / len(cells["uptake"][arm])
        cross["L"][arm] = {
            "constraint": key, "solo_calibration_topics": solo,
            "composed_with_A_confirmatory_topics": composed,
            "L_unpaired": None if solo is None else solo - composed}
    l_values = [v["L_unpaired"] for k, v in cross["L"].items()
                if k != "AB" and v["L_unpaired"] is not None]
    if l_values and cross["L"]["AB"]["L_unpaired"] is not None:
        cross["L_B_minus_mean_L_R"] = (cross["L"]["AB"]["L_unpaired"]
                                       - sum(l_values) / len(l_values))
        cross["L_B_minus_mean_L_R_reading"] = (
            "the topic-set shift is common to both terms only under the "
            "assumption above; it does not cancel, because the solo terms are "
            "different constraints on the same shifted set. Reported as a "
            "diagnostic and as the correction to any earlier quotation of "
            "these numbers as D(B<-A) and D(Rbar<-A).")

    # Cross-check: check C18 computed Delta^A on all cached draws by an
    # independent path. A disagreement here is a defect in one of the two.
    c18_path = DCI1 / "docs" / "v4_prefreeze" / "C18.json"
    c18 = json.loads(c18_path.read_text())["models"].get(model, {})
    recorded = c18.get("on_all_cached_draws", {}).get("delta_a_compliance_form")
    here = identified["pooled"]["delta_A"]["estimate"]
    cross_check = {
        "quantity": "Delta^A on all cached draws",
        "recorded_by_check_C18": recorded,
        "recomputed_here": here,
        "absolute_difference": (None if recorded is None
                                else abs(recorded - here)),
        "agrees_to_1e_9": (recorded is not None
                           and abs(recorded - here) < 1e-9),
        "source": str(c18_path.relative_to(DCI1))}

    return {
        "model": model,
        "design": design,
        "cross_check_against_prefreeze_C18": cross_check,
        "order_strata": {level: orders.count(level) for level in sorted(set(orders))},
        "references": {a: arm_constraints[a] for a in ("AR1", "AR2", "AR3")},
        "identified_same_topic": identified,
        "response_length_by_arm": words,
        "length_matched_delta_A": length_matched,
        "vacuity_forced_delta_A": vacuity_forced,
        "accidental_compliance": accidental,
        "cross_set_diagnostic": cross,
        "gate2a_provenance": solo_provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resamples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=202608220)
    args = parser.parse_args()

    models = sorted(p.name for p in EVIDENCE.iterdir()
                    if (p / "confirmatory" / "cache.jsonl").exists())
    skipped = sorted(p.name for p in EVIDENCE.iterdir()
                     if p.is_dir() and p.name != "registration"
                     and not (p / "confirmatory" / "cache.jsonl").exists())
    result = {
        "classification": CLASSIFICATION,
        "produced_by": "dci1/tools/v3_reciprocal_reanalysis.py",
        "licenses_no_confirmatory_claim": True,
        "identification": {
            "identified_on_the_confirmatory_topics": [
                "D(A<-B)", "D(A<-R_j)", "Delta^A", "Delta^A_j",
                "companion uptake in the composed cell", "joint success"],
            "not_identified_from_these_rows": {
                "D(B<-A)": "no B solo cell on the confirmatory topics",
                "D(R_j<-A)": "no reference solo cell on the confirmatory topics",
                "D(R_j<-B)": "no B+R_j cell exists in the v3 design at all",
                "Lambda": "needs D(B<-A)",
                "Delta_R": "needs D(B<-R_j), and no B+R_j cell exists",
                "Xi": "needs the reference-on-reference cells, absent by design"},
            "why": (
                "the v3 arms are AB, AR1, AR2, AR3, A and TOPIC. The swapped "
                "slot is the companion and the recorded outcome is A, so every "
                "identified loss is a loss of A. The B-side and "
                "reference-side losses need solo baselines on the same topics "
                "and v3 generated none."),
        },
        "estimation": {
            "unit": "the block; every quantity is a mean of per-block "
                    "contributions over the 384 confirmatory blocks",
            "draws": "all 16 cached draws enter each cell mean; no draw is "
                     "selected, which is where this differs from the v3 "
                     "registered selector",
            "uncertainty": f"block bootstrap, {args.resamples} resamples, "
                           f"resampled within order stratum; percentile and "
                           f"studentised maximum-modulus simultaneous intervals",
            "order": "a block-level factor in v3, so order strata are disjoint "
                     "sets of blocks and the order contrast is unpaired",
        },
        "models_without_confirmatory_data": {
            m: "terminated at Gate 2A with REFERENCE_POOL_MISMATCH; no "
               "confirmatory generation exists, which is non-identification "
               "and not a null" for m in skipped},
        "results": {m: analyse_model(m, resamples=args.resamples,
                                     seed=args.seed) for m in models},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=1,
                                                sort_keys=True) + "\n")
    print(json.dumps({m: {
        "delta_A": r["identified_same_topic"]["pooled"]["delta_A"],
        "D_A_from_B": r["identified_same_topic"]["pooled"]["D_A_from_B"]}
        for m, r in result["results"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
