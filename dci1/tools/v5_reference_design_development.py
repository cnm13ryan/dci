#!/usr/bin/env python3
"""DEVELOPMENT ONLY — the retrospective analyses that choose DCI-1 v5's
reference-validity rule and its thresholds.

Nothing here is confirmatory, nothing here is preregistered, and nothing here
is validation. It is design fitting on the completed v4r4 study, in the sense
v5 §30 states: a rule chosen because it separates v4r4's known failures from
v4r4's known passes has been fitted to those failures, and the prospective
test is v5 itself.

What it reads
-------------
* signed v4r4 ``REGIME_SCREEN``, ``GATE_2_REGIME`` and ``GATE_3_REFERENCES``
  records for all four replications — solo and chance quantities only;
* the stored Gate-2 calibration responses, re-scored with the **registered**
  v4r4 verifiers, to obtain quantities v4r4 did not itself record;
* one composed table: ``gemma-3n-e2b-it``'s Gate-4 headroom rates, used only
  to ask whether a pre-composition projection predicts them. Gate-4 rates are
  viability material on a terminated replication and are never an effect.

Outputs ``dci1/reports/dci1v5/development/*.json``.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "dci1" / "src"))

from dci1v4r4.verifiers.compliance import passes                # noqa: E402
from dci1v4r4.verifiers.constraints import (                    # noqa: E402
    Constraint, FAMILIES, feature_group,
)
from dci1v4r4.verifiers.statistics import family_statistic      # noqa: E402

MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
EV = REPO / "dci1" / "evidence" / "dci1v4r4"
OUT = REPO / "dci1" / "reports" / "dci1v5" / "development"
Z = 1.959963985
N_CAL = 384          # 96 calibration topics x M_cal = 4


# ------------------------------------------------------------------ helpers
def record(model: str, stage: str) -> dict:
    f = sorted((EV / model / stage / "records").glob("*.json"))
    d = json.loads(f[0].read_text())
    return d.get("payload", d)


def wilson(p: float, n: int) -> tuple[float, float]:
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = (Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
            / (1 + Z * Z / n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def iota(solo: float, chance: float) -> float | None:
    return None if chance >= 0.99 else (solo - chance) / (1.0 - chance)


def quantiles(values):
    v = sorted(values)
    if not v:
        return {}
    return {"n": len(v), "min": v[0], "median": st.median(v),
            "p75": v[int(0.75 * len(v))], "p90": v[int(0.90 * len(v))],
            "max": v[-1]}


def split_half(topic_id: str) -> int:
    """Deterministic split by hashed topic identity and nothing else."""
    return int(hashlib.sha256(topic_id.encode()).hexdigest(), 16) % 2


def calibration_rows(model: str):
    for run in ("calibration", "focal_extension"):
        p = EV / model / "GATE_2_REGIME" / "backend_runs" / run / "scored.jsonl"
        if not p.exists():
            continue
        for line in p.open():
            yield json.loads(line)


# --------------------------------------------------- D1  measured landscape
def d1_landscape() -> dict:
    """Solo, chance, iota, vacuity and pre-screen -> calibration drift."""
    out = {}
    for m in MODELS:
        g2, rs = record(m, "GATE_2_REGIME"), record(m, "REGIME_SCREEN")
        rows = []
        for r in g2["calibration_table"]:
            ic = iota(r["solo_compliance"], r["chance_compliance"])
            ip = iota(r["prescreen_solo_compliance"],
                      r["prescreen_chance_compliance"])
            lo, hi = wilson(r["solo_compliance"], N_CAL)
            rows.append({
                "label": f"{r['kind']}:{r['severity']}", "family": r["kind"],
                "severity": r["severity"], "role": FAMILIES[r["kind"]].role,
                "form": FAMILIES[r["kind"]].form,
                "feature_group": feature_group(r["kind"]),
                "solo": r["solo_compliance"], "chance": r["chance_compliance"],
                "solo_ci": [lo, hi], "vacuity": r["solo_vacuity"],
                "lift": r["solo_compliance"] - r["chance_compliance"],
                "iota_calibration": ic, "iota_prescreen": ip,
                "iota_drift": None if None in (ic, ip) else abs(ic - ip),
                "solo_drift": abs(r["solo_compliance"]
                                  - r["prescreen_solo_compliance"]),
                "distance_from_iota_a": None if ic is None
                else abs(ic - g2["iota_a"]),
                "median_words": r.get("median_words"),
            })
        out[m] = {"iota_a": g2["iota_a"], "solo_a": g2["a_solo_compliance"],
                  "prescreen_iota_a": rs["iota_a_prescreen"],
                  "iota_a_drift": abs(g2["iota_a"] - rs["iota_a_prescreen"]),
                  "n_star": g2["n_star"], "m_star": g2["m_star"],
                  "rows": rows}
    drifts = [r["iota_drift"] for m in MODELS for r in out[m]["rows"]
              if r["iota_drift"] is not None]
    out["_pooled_iota_drift"] = quantiles(drifts)
    out["_pooled_iota_drift"]["share_above_0.10_caliper"] = (
        sum(1 for d in drifts if d > 0.10) / len(drifts))
    out["_note"] = ("pre-screen is 24 topics x 1 draw; calibration is 96 x 4 "
                    "on a disjoint split, so the drift confounds sample size "
                    "with the split and is an upper bound on split noise "
                    "alone. D3 measures split noise at fixed n.")
    return out


# -------------------------------------- D2  counterfactual chance under B
def d2_kappa_under_b() -> dict:
    """kappa(R | B alone at m*): R's verifier on responses written under B.

    R is never stated. This is a chance verdict under a different load-one
    treatment, not a composed outcome, and v4r3 §9.1 already records exactly
    this class of verdict wherever a stage scores absent instances.
    """
    out = {}
    for m in MODELS:
        g2 = record(m, "GATE_2_REGIME")
        m_star = g2["m_star"]
        cands = sorted({(r["kind"], r["severity"])
                        for r in g2["calibration_table"]})
        arms = {"unconstrained": [], "b_solo": []}
        for d in calibration_rows(m):
            present = [s for s in d["scores"] if s["present"]]
            if d["load"] == 0:
                arms["unconstrained"].append(d)
            elif (len(present) == 1 and present[0]["kind"] == "B"
                  and present[0]["severity"] == m_star):
                arms["b_solo"].append(d)
        rows = {}
        for kind, sev in cands:
            c = Constraint(kind=kind, severity=sev)
            rate = {}
            for arm, rs in arms.items():
                hits = sum(passes(c, family_statistic(kind, r["raw_response"]),
                                  r["raw_response"]) for r in rs)
                rate[arm] = hits / len(rs)
            rows[f"{kind}:{sev}"] = {
                "kappa": rate["unconstrained"], "kappa_under_b": rate["b_solo"],
                "displacement": rate["b_solo"] - rate["unconstrained"],
                "form": FAMILIES[kind].form, "role": FAMILIES[kind].role}
        out[m] = {
            "m_star": m_star, "n_unconstrained": len(arms["unconstrained"]),
            "n_b_solo": len(arms["b_solo"]),
            "median_words_unconstrained":
                st.median(r["word_count"] for r in arms["unconstrained"]),
            "median_words_b_solo":
                st.median(r["word_count"] for r in arms["b_solo"]),
            "rows": rows}
    return out


# ---------------------------------------- D3  split-half stability at fixed n
def d3_stability() -> dict:
    """|iota(half A) - iota(half B)| at 48 topics x 4 draws, by chance band
    and by predicate form. This is the quantity a v5 Calibration-A/B split
    measures, at half v5's per-split size."""
    by_band, by_form, pooled_i, pooled_s = {}, {}, [], []
    per_model = {}
    for m in MODELS:
        g2 = record(m, "GATE_2_REGIME")
        cands = sorted({(r["kind"], r["severity"])
                        for r in g2["calibration_table"]})
        kappa_full = {f"{r['kind']}:{r['severity']}": r["chance_compliance"]
                      for r in g2["calibration_table"]}
        solo = {0: {}, 1: {}}
        chance = {0: {}, 1: {}}
        for d in calibration_rows(m):
            h = split_half(d["topic_id"])
            present = [s for s in d["scores"] if s["present"]]
            if d["load"] == 0:
                for kind, sev in cands:
                    ok = passes(Constraint(kind=kind, severity=sev),
                                family_statistic(kind, d["raw_response"]),
                                d["raw_response"])
                    cell = chance[h].setdefault((kind, sev), [0, 0])
                    cell[0] += ok
                    cell[1] += 1
            elif (len(present) == 1
                  and (present[0]["kind"], present[0]["severity"]) in cands):
                key = (present[0]["kind"], present[0]["severity"])
                cell = solo[h].setdefault(key, [0, 0])
                cell[0] += present[0]["passed"]
                cell[1] += 1
        di, ds = [], []
        for key in cands:
            if key not in solo[0] or key not in solo[1]:
                continue
            vals = []
            for h in (0, 1):
                ps = solo[h][key][0] / solo[h][key][1]
                kc = chance[h][key][0] / chance[h][key][1]
                i = iota(ps, kc)
                if i is None:
                    vals = None
                    break
                vals.append((ps, i))
            if not vals:
                continue
            d_i = abs(vals[0][1] - vals[1][1])
            di.append(d_i)
            ds.append(abs(vals[0][0] - vals[1][0]))
            k = kappa_full[f"{key[0]}:{key[1]}"]
            band = ("chance_free_below_0.05" if k < 0.05 else
                    "low_0.05_to_0.25" if k < 0.25 else
                    "mid_0.25_to_0.75" if k < 0.75 else "high_0.75_and_above")
            by_band.setdefault(band, []).append(d_i)
            by_form.setdefault(FAMILIES[key[0]].form, []).append(d_i)
        per_model[m] = {"iota": quantiles(di), "solo": quantiles(ds)}
        pooled_i += di
        pooled_s += ds
    sd_diff_48 = st.median(pooled_i) / 0.6745
    return {"per_model": per_model,
            "pooled_iota": quantiles(pooled_i),
            "pooled_solo": quantiles(pooled_s),
            "by_chance_band": {k: quantiles(v) for k, v in by_band.items()},
            "by_predicate_form": {k: quantiles(v) for k, v in by_form.items()},
            "implied_standard_errors": {
                "sd_of_split_difference_at_48_topics": sd_diff_48,
                "se_iota_at_48x4": sd_diff_48 / math.sqrt(2),
                "se_iota_at_96x4": sd_diff_48 / 2.0,
                "se_iota_at_192x4": sd_diff_48 / math.sqrt(8),
                "v4r4_caliper_in_se_at_96x4": 0.10 / (sd_diff_48 / 2.0),
                "v4r4_caliper_in_se_at_192x4":
                    0.10 / (sd_diff_48 / math.sqrt(8))},
            "_note": ("a chance-free candidate's iota equals its raw solo "
                      "compliance, so it carries none of the 1/(1-kappa) "
                      "variance amplification the mid and high bands show")}


# --------------------------- D4  does a pre-composition projection predict?
def d4_projection() -> dict:
    """p_hat(R | B+R) = kappa(R|B) + iota_R * (1 - kappa(R|B)) against
    gemma-3n-e2b-it's observed Gate-4 composed rates."""
    m = "gemma-3n-e2b-it"
    anat = json.loads((REPO / "dci1" / "reports" / "dci1v4r4"
                       / "followup_diagnostics" / "03_gate4_anatomy.json"
                       ).read_text())["models"][m]
    kb = d2_cache[m]["rows"]
    iot = {r["label"]: r["iota_calibration"] for r in d1_cache[m]["rows"]}
    b_label = next(c["constraint"] for c in anat["cells"] if c["slot"] == "B")
    rows = []
    for c in anat["cells"]:
        cell = c["cell"]
        if c["arm"] != "composed" or c["constraint"] == b_label:
            continue
        if not (cell.startswith("pair:B+") or cell.endswith("+B")):
            continue
        lab = c["constraint"]
        if lab not in kb or iot.get(lab) is None:
            continue
        k = kb[lab]["kappa_under_b"]
        i = iot[lab]
        p_hat = k + i * (1 - k)
        rows.append({"cell": cell, "companion": lab, "kappa_under_b": k,
                     "iota": i, "projected": p_hat,
                     "observed_gate4": c["composed_or_solo_rate"],
                     "error": p_hat - c["composed_or_solo_rate"],
                     "gate4_failed": c["fails_band"]})
    rows.sort(key=lambda r: -r["projected"])
    errs = [abs(r["error"]) for r in rows]
    sweep = {}
    for thr in (0.85, 0.875, 0.90, 0.92, 0.95):
        caught = sum(1 for r in rows if r["projected"] > thr and r["gate4_failed"])
        missed = sum(1 for r in rows if r["projected"] <= thr and r["gate4_failed"])
        false = sum(1 for r in rows if r["projected"] > thr and not r["gate4_failed"])
        sweep[f"{thr}"] = {"caught": caught, "missed": missed,
                           "false_alarms": false}
    return {"model": m, "n_rate_checks": len(rows), "rows": rows,
            "absolute_error": quantiles(errs),
            "ceiling_sweep": sweep,
            "_note": ("one replication, 20 rate checks. A threshold chosen to "
                      "sit inside an observed gap on 20 points is fitted to "
                      "those 20 points; v5 §9.3 chooses it from the band and a "
                      "registered error allowance instead, and records that "
                      "the two happen to coincide.")}


# ------------------------------------- D5  attrition of the proposed gates
def d5_attrition() -> dict:
    """What each proposed gate would have cost in support, on v4r4's own
    candidate library and measurements."""
    def survive(model, *, headroom, chance_max, lift_min, projected_band,
                displacement_max, caliper, role):
        kept = []
        for r in d1_cache[model]["rows"]:
            if r["role"] != role or r["iota_calibration"] is None:
                continue
            reasons = []
            lo, hi = r["solo_ci"]
            if not (headroom[0] <= lo and hi <= headroom[1]):
                reasons.append("raw solo headroom")
            if r["chance"] > chance_max:
                reasons.append("chance ceiling")
            if r["lift"] < lift_min:
                reasons.append("instruction lift")
            if r["vacuity"] > 0.10:
                reasons.append("vacuity")
            k = d2_cache[model]["rows"].get(r["label"])
            if k is None:
                reasons.append("no kappa|B measurement")
            else:
                p_hat = (k["kappa_under_b"]
                         + r["iota_calibration"] * (1 - k["kappa_under_b"]))
                if not projected_band[0] <= p_hat <= projected_band[1]:
                    reasons.append("projected composed compliance")
                if abs(k["displacement"]) > displacement_max:
                    reasons.append("displacement under B")
            if r["distance_from_iota_a"] > caliper:
                reasons.append("iota caliper")
            if not reasons:
                kept.append(r["label"])
        fams = sorted({lab.split(":")[0] for lab in kept})
        return {"rungs": kept, "families": fams,
                "feature_groups": sorted({feature_group(f) for f in fams})}

    OFF = dict(headroom=(0.0, 1.0), chance_max=0.99, lift_min=0.0,
               projected_band=(0.0, 1.0), displacement_max=1.0, caliper=0.10)
    V5 = dict(headroom=(0.10, 0.90), chance_max=0.75, lift_min=0.20,
              projected_band=(0.10, 0.90), displacement_max=0.25, caliper=0.10)
    stack = [
        ("v4r4 rule (iota caliper and vacuity only)", OFF),
        ("+ raw solo headroom CI in [0.10, 0.90]",
         {**OFF, "headroom": (0.10, 0.90)}),
        ("+ chance <= 0.75 and lift >= 0.20",
         {**OFF, "headroom": (0.10, 0.90), "chance_max": 0.75,
          "lift_min": 0.20}),
        ("+ interaction gates (the full v5 stack)", V5),
    ]
    out = {}
    for role in ("reference", "class_control"):
        out[role] = {}
        for name, cfg in stack:
            cal = 0.15 if role == "class_control" else cfg["caliper"]
            out[role][name] = {m: survive(m, role=role, **{**cfg,
                                                           "caliper": cal})
                               for m in MODELS}
    return out


# ----------------------------- D6  natural frequency of candidate markers
def d6_marker_frequency() -> dict:
    """P(the word appears at least once) on unconstrained and B-solo responses.

    A Tier-1 family is worth having only when its marker is rare in ordinary
    prose, and the benchmark is not zero but A's own marker: `however` appears
    in 1.3% to 10.4% of unconstrained development responses. This measures
    every candidate against that benchmark instead of asserting it.
    """
    import re
    from collections import Counter
    word = re.compile(r"[^\W\d_]+", re.UNICODE)
    candidates = [
        # marker, letters, declared discourse role
        ("however", "contrastive"), ("thus", "consecutive"),
        ("hence", "consecutive"), ("though", "contrastive"),
        ("whereas", "contrastive"), ("indeed", "emphatic"),
        ("namely", "exemplifying"), ("instead", "substitutive"),
        ("overall", "summative"), ("notably", "emphatic"),
        ("finally", "summative"), ("also", "additive"),
        ("then", "consecutive"), ("next", "consecutive"),
        ("yet", "contrastive"), ("still", "contrastive"),
        ("rather", "substitutive"), ("further", "additive"),
        ("albeit", "contrastive"), ("besides", "additive"),
        ("granted", "concessive"), ("equally", "additive"),
        ("moreover", "additive"), ("therefore", "consecutive"),
        ("meanwhile", "temporal"), ("otherwise", "conditional"),
        ("conversely", "contrastive"), ("likewise", "additive"),
        ("nonetheless", "contrastive"),
    ]
    out = {}
    for m in MODELS:
        m_star = record(m, "GATE_2_REGIME")["m_star"]
        arms = {"unconstrained": [], "b_solo": []}
        for d in calibration_rows(m):
            present = [s for s in d["scores"] if s["present"]]
            if d["load"] == 0:
                arms["unconstrained"].append(d["raw_response"])
            elif (len(present) == 1 and present[0]["kind"] == "B"
                  and present[0]["severity"] == m_star):
                arms["b_solo"].append(d["raw_response"])
        counts = {a: [Counter(w.lower() for w in word.findall(t)) for t in ts]
                  for a, ts in arms.items()}
        out[m] = {}
        for marker, _role in candidates:
            u = [c[marker] for c in counts["unconstrained"]]
            b = [c[marker] for c in counts["b_solo"]]
            out[m][marker] = {
                "p_at_least_one_unconstrained": sum(1 for x in u if x) / len(u),
                "p_at_least_one_b_solo": sum(1 for x in b if x) / len(b),
                "mean_count_unconstrained": st.mean(u),
                "mean_count_b_solo": st.mean(b)}
    summary = {}
    for marker, role in candidates:
        worst = max(out[m][marker]["p_at_least_one_unconstrained"]
                    for m in MODELS)
        summary[marker] = {
            "letters": len(marker), "discourse_role": role,
            "max_p_at_least_one": worst,
            "passes_length_rule": len(marker) <= 7,
            "passes_frequency_rule": worst <= 0.15}
    return {"per_model": out, "summary": summary,
            "a_marker_benchmark": {
                m: out[m]["however"]["p_at_least_one_unconstrained"]
                for m in MODELS},
            "_rules": {
                "length": "at most 7 letters, so the family is jointly "
                          "satisfiable with B at every admissible m >= 7",
                "frequency": "P(at least one occurrence | unconstrained) <= "
                             "0.15 on every registered model, against A's own "
                             "maximum of 0.104",
                "reserved": "however is A's marker and is excluded"},
            "_note": ("B suppresses markers: `however` falls from 0.102 to "
                      "0.008 under B alone on gemma-3n-e2b-it, because B "
                      "shortens answers and shifts the register. The "
                      "displacement is negative and small in absolute terms "
                      "for every admitted marker.")}


# ------------------------------------------------------------------- main
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    d1_cache = d1_landscape()
    d2_cache = d2_kappa_under_b()
    artifacts = {
        "d1_candidate_landscape.json": d1_cache,
        "d2_kappa_under_b.json": d2_cache,
        "d3_split_half_stability.json": d3_stability(),
        "d4_interaction_projection.json": d4_projection(),
        "d5_gate_attrition.json": d5_attrition(),
        "d6_marker_frequency.json": d6_marker_frequency(),
    }
    for name, payload in artifacts.items():
        payload = {"_status": "DEVELOPMENT ONLY — design fitting on completed "
                              "v4r4 evidence; not preregistered, not "
                              "confirmatory, not validation",
                   **payload}
        (OUT / name).write_text(json.dumps(payload, indent=1, sort_keys=True)
                                + "\n")
        print(f"wrote {OUT / name}")
