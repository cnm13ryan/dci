"""Membership-stability diagnostics (decision D14, proposed).

Pilot memberships are classifications made from samples of 32 to 96
responses, and every cell of a stage shares the same topics. So the
uncertainty of a membership is estimated by resampling **topics**, not
responses: each replicate draws the Stage 1 topics and the Stage 2 topics
with replacement, separately, and every cell (A, B, references, task-only)
takes the responses of the drawn topics. Responses that share a topic stay
together, which is the dependence the Wilson and Newcombe intervals ignore.

Each replicate is passed through the frozen rules unchanged:

* **fixed selection** --- with the point-estimate A and B: eligibility,
  matching, G1-G6 and P1-P3 coverage per configuration, giving each
  reference's inclusion frequency in G1, G3 and G5;
* **full selection** --- ``calibration.finalize``: how often each A count and
  B pair is selected, and how often the run is FEASIBLE.

``stage1_only`` is the topic-composition sensitivity the audit asked for
(F10): refined cells pool Stage 1 and Stage 2 topics, unrefined cells see
Stage 1 topics only, and the two topic sets differ in characteristics
(``topics.hygiene_report`` profiles). It recomputes eligibility and the
memberships from Stage 1 evidence alone, with the selected A and B held
fixed, and reports every difference from the pooled result.

Also reported: *borderline matches*, the references whose point-estimate
Newcombe interval for p_X - p_A contains an edge of the tolerance.

**Stable-member feasibility.** Coverage is a minimum count of matched
references, and classification noise near the ±0.10 edge adds members more
easily than it removes them when many candidates sit just outside the
window (the precision review, ``CALIBRATION_PRECISION_REVIEW.md``). So the
report also recomputes P1-P3 and the 12-of-16 target with G1, G3 and G5
restricted to members whose inclusion frequency is at least
``stability_stable_threshold`` (majority inclusion). A FEASIBLE point verdict
that is not feasible on stable members is flagged
``FEASIBILITY_RESTS_ON_UNSTABLE_MEMBERS`` for review. The precision review
shows this check is not a reliable gate: no threshold both keeps truly
feasible pilots and removes the anti-conservative false FEASIBLE verdicts,
because the resamples are centred on the observed, already biased, data.

**Interpretation (proposed).** Diagnostic only. Freeze 2 membership is the
point-estimate rule and is never changed by this module. A member whose
inclusion frequency lies inside ``stability_unstable_band`` is listed as
unstable; a FEASIBLE point verdict with a FEASIBLE share below
``stability_min_feasible_share`` is flagged ``FEASIBILITY_UNSTABLE``. Both go
to the researcher for review before Freeze 2 is accepted; the confirmatory
analysis may report the stable-member subset as a sensitivity, never as the
primary population.
"""
from __future__ import annotations

import random
from collections import Counter
from typing import Any, Iterable, Mapping

from dci.batch1 import calibration as CAL
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1.design import TASK_ONLY
from dci.batch1.scoring import Count, PilotTables, _key

__all__ = ["topic_clusters", "resample", "diagnostics", "stage1_only",
           "stable_member_feasibility"]

Cluster = tuple[str, str]          # (stage, topic_id)


def topic_clusters(scored: Iterable[Mapping[str, Any]]
                   ) -> tuple[dict[str, dict[str, dict[Cluster, list[int]]]],
                              dict[str, list[Cluster]]]:
    """Per table and cell: (stage, topic) -> [compliant, behavioural]."""
    cells: dict[str, dict[str, dict[Cluster, list[int]]]] = {
        "explicit": {}, "task_only": {}}
    clusters: dict[str, set[Cluster]] = {}
    for row in scored:
        cluster = (row["stage"], row["topic_id"])
        clusters.setdefault(row["stage"], set()).add(cluster)
        if row["condition"] == TASK_ONLY:
            for cid, entry in row["scores"].items():
                kn = cells["task_only"].setdefault(_key(row["model"], cid), {}) \
                    .setdefault(cluster, [0, 0])
                kn[0] += bool(entry[2])
                kn[1] += 1
            continue
        key = _key(row["model"], row["frame"], row["condition"])
        kn = cells["explicit"].setdefault(key, {}).setdefault(cluster, [0, 0])
        kn[0] += bool(row["scores"][row["condition"]][2])
        kn[1] += 1
    return cells, {s: sorted(c) for s, c in clusters.items()}


def resample(cells: Mapping[str, Mapping[str, Mapping[Cluster, list[int]]]],
             clusters: Mapping[str, list[Cluster]], rng: random.Random,
             *, synthetic: bool) -> PilotTables:
    weight: Counter = Counter()
    for stage, members in sorted(clusters.items()):
        weight.update(rng.choice(members) for _ in members)
    tables = PilotTables(synthetic=synthetic)
    for name, target in (("explicit", tables.explicit),
                         ("task_only", tables.task_only)):
        for key, by_cluster in cells[name].items():
            k = n = 0
            for cluster, (ck, cn) in by_cluster.items():
                w = weight.get(cluster, 0)
                k += w * ck
                n += w * cn
            target[key] = Count(k=k, n=n, planned=n)
    return tables


def _config_key(model: str, frame: str, m: int) -> str:
    return f"{model}|{frame}|B{m}"


def diagnostics(scored: list[Mapping[str, Any]], point: Mapping[str, Any],
                cfg: CFG.PilotConfig, compat: Mapping[str, Any], *,
                synthetic: bool, replicates: int | None = None,
                full_selection: bool = True) -> dict[str, Any]:
    """The D14 report for a pilot whose point-estimate result is ``point``."""
    replicates = cfg.stability_replicates if replicates is None else replicates
    cells, clusters = topic_clusters(scored)
    rng = random.Random(cfg.stability_seed)
    a_cid = (point.get("a") or {}).get("selected")
    b_sel = (point.get("b") or {}).get("selected")
    fixed = a_cid is not None and b_sel is not None
    focal = L.constraint_by_id()[a_cid] if fixed else None
    inclusion: dict[str, dict[str, Counter]] = {}
    supported: dict[str, Counter] = {p: Counter() for p in ("P1", "P2", "P3")}
    supported_counts: dict[str, Counter] = {p: Counter()
                                            for p in ("P1", "P2", "P3")}
    a_sel, b_pairs, status = Counter(), Counter(), Counter()
    for _ in range(replicates):
        tables = resample(cells, clusters, rng, synthetic=synthetic)
        if fixed:
            elig = R.eligibility(tables, cfg)
            per_p = Counter()
            for model, frame in R.model_frames(cfg):
                for m in b_sel:
                    rep = R.configuration_report(tables, cfg, compat, elig,
                                                 focal, model, frame, m)
                    key = _config_key(model, frame, m)
                    groups = inclusion.setdefault(key, {})
                    for g in ("G1", "G3", "G5"):
                        groups.setdefault(g, Counter()).update(
                            rep["populations"][g])
                    for p in ("P1", "P2", "P3"):
                        if rep["coverage"][p]["supported"] and \
                                rep["a_informative"]:
                            supported[p][key] += 1
                            per_p[p] += 1
            for p in ("P1", "P2", "P3"):
                supported_counts[p][per_p[p]] += 1
        if not full_selection:
            continue
        result = CAL.finalize(tables, cfg, compat)
        status[result["status"]] += 1
        a_sel[(result.get("a") or {}).get("selected") or "none"] += 1
        pair = (result.get("b") or {}).get("selected")
        b_pairs["-".join(map(str, pair)) if pair else "none"] += 1
    lo, hi = cfg.stability_unstable_band
    membership, unstable = {}, {}
    for rep in point.get("configurations", []):
        key = _config_key(rep["model"], rep["frame"], rep["b_limit"])
        freq = {g: {cid: c / replicates for cid, c in
                    sorted(inclusion.get(key, {}).get(g, Counter()).items())}
                for g in ("G1", "G3", "G5")}
        membership[key] = freq
        unstable[key] = {g: sorted(cid for cid, f in freq[g].items()
                                   if lo <= f <= hi) for g in freq}
    borderline = {}
    tol = cfg.matching_tolerance
    for rep in point.get("configurations", []):
        key = _config_key(rep["model"], rep["frame"], rep["b_limit"])
        borderline[key] = sorted(
            cid for cid, mt in rep["matching"].items()
            if mt.get("status") == "OK" and any(
                mt["diff_ci"][0] <= edge <= mt["diff_ci"][1]
                for edge in (-tol, tol)))
    stable = (stable_member_feasibility(point, membership, cfg,
                                        cfg.stability_stable_threshold)
              if fixed else None)
    feasible_share = (status.get("FEASIBLE", 0) / replicates
                      if replicates and full_selection else None)
    flags = []
    if point.get("status") == "FEASIBLE" and stable and \
            not stable["all_feasible"]:
        flags.append("FEASIBILITY_RESTS_ON_UNSTABLE_MEMBERS: not feasible "
                     "when G1/G3/G5 keep only members included in >= "
                     f"{cfg.stability_stable_threshold} of topic resamples "
                     "(for review; not a gate)")
    if point.get("status") == "FEASIBLE" and feasible_share is not None and \
            feasible_share < cfg.stability_min_feasible_share:
        flags.append(f"FEASIBILITY_UNSTABLE: FEASIBLE in {feasible_share:.2f} "
                     f"of topic resamples (< "
                     f"{cfg.stability_min_feasible_share})")
    n_unstable = sum(len(v) for g in unstable.values() for v in g.values())
    if n_unstable:
        flags.append(f"MEMBERSHIP_UNSTABLE: {n_unstable} configuration "
                     "memberships with inclusion frequency in "
                     f"[{lo}, {hi}]")
    return {
        "schema": "dci.batch1/stability/v1", "rule": "D14 (proposed)",
        "replicates": replicates, "seed": cfg.stability_seed,
        "clusters": {s: len(c) for s, c in sorted(clusters.items())},
        "selection": {"a": dict(sorted(a_sel.items())),
                      "b": dict(sorted(b_pairs.items())),
                      "status": dict(sorted(status.items())),
                      "feasible_share": feasible_share},
        "membership": membership, "unstable": unstable,
        "coverage_share": {p: {k: v / replicates
                               for k, v in sorted(supported[p].items())}
                           for p in supported},
        "supported_configurations": {
            p: {str(k): v for k, v in sorted(supported_counts[p].items())}
            for p in supported_counts},
        "borderline_matches": borderline,
        "stable_member_feasibility": None if stable is None else {
            "all_feasible": stable["all_feasible"],
            **{p: {"feasible": stable[p]["feasible"],
                   "supported_configurations":
                       stable[p]["supported_configurations"]}
               for p in ("P1", "P2", "P3")}},
        "flags": flags,
        "interpretation": "diagnostic only; membership is the point-estimate "
                          "rule (D14, proposed)",
    }


def stable_member_feasibility(point: Mapping[str, Any],
                              membership: Mapping[str, Any],
                              cfg: CFG.PilotConfig, threshold: float
                              ) -> dict[str, Any] | None:
    """P1-P3 and the target with G1/G3/G5 cut to members whose inclusion
    frequency is at least ``threshold``."""
    a_cid = (point.get("a") or {}).get("selected")
    b_sel = (point.get("b") or {}).get("selected")
    if a_cid is None or b_sel is None:
        return None
    focal = L.constraint_by_id()[a_cid]
    reports = []
    for rep in point.get("configurations", []):
        key = _config_key(rep["model"], rep["frame"], rep["b_limit"])
        pops = {g: list(rep["populations"][g]) for g in R.GROUPS}
        for g in ("G1", "G3", "G5"):
            pops[g] = [c for c in pops[g]
                       if membership[key][g].get(c, 0) >= threshold]
        R.assert_nesting(pops)
        reports.append({"model": rep["model"], "b_limit": rep["b_limit"],
                        "a_informative": rep["a_informative"],
                        "coverage": R.coverage(focal, pops, rep["funnel"],
                                               cfg)})
    return R.feasibility(reports, cfg, b_sel)


def stage1_only(ev1: Any, point: Mapping[str, Any], cfg: CFG.PilotConfig,
                compat: Mapping[str, Any], *, synthetic: bool
                ) -> dict[str, Any]:
    """Eligibility and G1/G3/G5 from Stage 1 alone, against the pooled
    result, with the pooled selection of A and B held fixed."""
    from dci.batch1 import evidence as EV
    tables = EV.tables_for([ev1], synthetic=synthetic)
    elig1 = R.eligibility(tables, cfg)
    pooled = point.get("eligibility", {})
    e1, ep = R.eligible_ids(elig1), R.eligible_ids(pooled)
    out: dict[str, Any] = {
        "eligible_stage1_only": sorted(e1 - ep),
        "eligible_pooled_only": sorted(ep - e1),
        "configurations": {}}
    a_cid = (point.get("a") or {}).get("selected")
    b_sel = (point.get("b") or {}).get("selected")
    if a_cid is None or b_sel is None:
        out["note"] = "no pooled selection; memberships not compared"
        return out
    focal = L.constraint_by_id()[a_cid]
    for rep in point.get("configurations", []):
        r1 = R.configuration_report(tables, cfg, compat, elig1, focal,
                                    rep["model"], rep["frame"],
                                    rep["b_limit"])
        key = _config_key(rep["model"], rep["frame"], rep["b_limit"])
        out["configurations"][key] = {
            g: {"stage1_only": sorted(set(r1["populations"][g])
                                      - set(rep["populations"][g])),
                "pooled_only": sorted(set(rep["populations"][g])
                                      - set(r1["populations"][g]))}
            for g in ("G1", "G3", "G5")}
        out["configurations"][key]["supported_stage1_only"] = {
            p: r1["coverage"][p]["supported"] and r1["a_informative"]
            for p in ("P1", "P2", "P3")}
    changed = sum(1 for c in out["configurations"].values()
                  for g in ("G1", "G3", "G5")
                  if c[g]["stage1_only"] or c[g]["pooled_only"])
    out["memberships_that_differ"] = changed
    return out
