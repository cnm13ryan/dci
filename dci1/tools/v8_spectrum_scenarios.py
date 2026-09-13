#!/usr/bin/env python3
"""Constructed-pool scenarios for the spectrum rules (deterministic; no
evidence). Each scenario is a small calibration pool with a known answer:

* local support exists but spectrum support does not;
* spectrum support exists although no single family meets the old C4;
* an extreme but stable reference survives the spectrum rule (and not
  V_head);
* degenerate / vacuous / chance-dominated references are still rejected;
* the reserve extension recovers a missing hard side.

    python3 tools/v8_spectrum_scenarios.py
Writes ``reports/dci1v8dev/prescreen/spectrum_scenarios.json`` and ``.md``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from dci1v7.protocol import constants as C
from dci1v7.stages import regime
from dci1v7.stages.calibration_table import CalibrationRow
from dci1v7.stages.interaction import KappaUnderBSource
from dci1v8dev.prescreen import extension as E
from dci1v8dev.prescreen.legacy import family_c4_states
from dci1v8dev.spectrum.selection import SelectionRule, select_spectrum
from dci1v8dev.spectrum.validity import (
    classify_pool,
)

OUT = Path(__file__).resolve().parents[1] / "reports" / "dci1v8dev" / "prescreen"
MODEL, M_STAR = "fixture-model", 9


def row(kind, q, solo, *, chance=0.0, kappa_b=0.0, vac=0.0, split="pooled",
        n_topics=192, seed=0):
    rng = np.random.default_rng(seed + q * 13 + hash(kind) % 97)
    per = np.clip(np.round(rng.normal(solo, 0.22, size=n_topics) * 4) / 4, 0, 1)
    per = np.clip(per - per.mean() + solo, 0, 1)
    src = KappaUnderBSource(load=1, present=(f"B:{M_STAR}",),
                            candidate=f"{kind}:{q}", model_key=MODEL,
                            m_star=M_STAR, split=split, n_topics=n_topics,
                            n_draws=C.M_CAL)
    return CalibrationRow(kind=kind, severity=q, split=split, model_key=MODEL,
                          solo_compliance=solo, chance_compliance=chance,
                          solo_vacuity=vac, kappa_under_b=kappa_b,
                          kappa_under_b_source=src, n_topics=n_topics,
                          per_topic_solo=tuple(float(v) for v in per))


def pool(spec, iota_a, *, seed=0):
    """spec: {family: {q: solo}}; builds pooled + two split tables whose
    split rates straddle the pooled rate by ±0.01."""
    pooled, a, b = [], [], []
    for kind, ladder in spec.items():
        for q, p in ladder.items():
            extra = ladder.get("extra", {}) if isinstance(ladder.get("extra"), dict) else {}
            if q == "extra":
                continue
            kw = extra.get(q, {})
            pooled.append(row(kind, q, p, seed=seed, **kw))
            a.append(row(kind, q, min(0.999, p + 0.01), split=C.CALIBRATION_A,
                         n_topics=96, seed=seed + 1, **kw))
            b.append(row(kind, q, max(0.001, p - 0.01), split=C.CALIBRATION_B,
                         n_topics=96, seed=seed + 2, **kw))
    folded = {r.label: {"passed": r.chance_compliance < C.CHANCE_DEGENERACY_MAX
                        and abs(r.iota - iota_a) <= 0.10} for r in pooled}
    cp = classify_pool(pooled, a, b, iota_a=iota_a, solo_compliance_a=iota_a,
                       n_topics_a=192, folded_stability=folded, seed=0,
                       resamples=400)
    valid = [r for r in pooled if cp["spectrum"][r.label]["passed"]]
    reaches_below = any(r.iota <= iota_a - 0.15 for r in valid)
    reaches_above = any(r.iota >= iota_a + 0.10 for r in valid)
    sel = select_spectrum(valid, iota_a=iota_a, rule=SelectionRule())
    cov_rows = regime.calibration_coverage_rows(
        [{"kind": r.kind, "severity": r.severity, "solo_compliance": r.solo_compliance,
          "chance_compliance": r.chance_compliance, "solo_vacuity": r.solo_vacuity}
         for r in pooled], formulation="E2")
    old = regime.coverage_criterion(cov_rows, iota_a=iota_a)
    fam_c4 = family_c4_states(cov_rows, iota_a=iota_a)
    return {"n_pooled": len(pooled), "n_local_valid": cp["n_local_valid"],
            "n_spectrum_valid": cp["n_spectrum_valid"],
            "reaches_below": reaches_below, "reaches_above": reaches_above,
            "beyond_v_head": cp["n_spectrum_valid_beyond_v_head"],
            "old_c4": old["conditions"]["C4"],
            "old_c4_groups": old["realised"]["straddling_groups"],
            "families_meeting_old_c4": [f for f, s in fam_c4.items() if s["c4_met"]],
            "new_status": sel["status"], "new_reasons": sel["coverage"]["reasons"],
            "selected": [(p["candidate"], round(p["iota"], 3), p["role"])
                         for p in sel["points"]],
            "se_beta": sel["coverage"]["projection"]["se_beta"],
            "spectrum_rejections": {r.label: cp["spectrum"][r.label]["first_failing_component"]
                                    for r in pooled if not cp["spectrum"][r.label]["passed"]}}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    iota_a = 0.68
    scenarios = {}
    # 1. local support, no spectrum: three families all within ±0.08 of A
    scenarios["local_not_spectrum"] = {
        "expect": "local valid rungs exist; spectrum NOT identified",
        **pool({"MK1": {5: 0.66, 6: 0.70, 7: 0.63},
                "MK2": {4: 0.72, 5: 0.67, 6: 0.62},
                "MK3": {3: 0.74, 4: 0.69, 5: 0.64}}, iota_a)}
    # 2. spectrum without old C4: three families each spanning ~0.28
    scenarios["spectrum_without_old_c4"] = {
        "expect": "no family spans 0.40 (old C4 fails); new rule identified",
        **pool({"MK1": {2: 0.82, 5: 0.68, 8: 0.52},
                "MK2": {2: 0.80, 5: 0.66, 8: 0.50},
                "MK3": {2: 0.84, 5: 0.70, 8: 0.55}}, iota_a)}
    # 3. extreme but stable survives the spectrum rule, not V_head
    scenarios["extreme_stable_survives"] = {
        "expect": "MK1:1 at 0.93 is spectrum-valid (beyond V_head) and selected high",
        **pool({"MK1": {1: 0.93, 4: 0.68, 8: 0.45},
                "MK2": {1: 0.92, 4: 0.66, 8: 0.48}}, iota_a)}
    # 4. degenerate / vacuous / chance-dominated rejected
    scenarios["degenerate_rejected"] = {
        "expect": "RF6:1 (kappa 0.995) no coordinate; RF7:2 vacuous; CR5:3 chance 0.8 fail",
        **pool({"MK1": {2: 0.85, 5: 0.68, 8: 0.45},
                "RF6": {1: 0.995, "extra": {1: {"chance": 0.995}}},
                "RF7": {2: 0.80, "extra": {2: {"vac": 0.30}}},
                "CR5": {3: 0.90, "extra": {3: {"chance": 0.80, "kappa_b": 0.80}}}},
               iota_a)}
    # 5. reserve extension recovers a missing hard side (2507-like)
    ladder = {1: 0.99, 2: 0.98, 3: 0.96, 4: 0.93, 5: 0.90, 6: 0.85, 7: 0.79, 8: 0.72}
    before = pool({"MK8": ladder}, 0.62)
    picks = E.reach_picks("MK8", measured=list(ladder), sides=["below"], n=2)
    picks2 = E.reach_picks("MK8", measured=list(ladder) + picks, sides=["below"], n=2)
    # two bounded batches of two reserve rungs each (the extrapolation puts
    # the crossing near q = 11)
    after = pool({"MK8": {**ladder, 9: 0.64, 10: 0.55, 11: 0.46, 12: 0.38}}, 0.62)
    scenarios["expansion_recovers_hard_side"] = {
        "expect": "no valid rung <= iota_A - 0.15 before; picks 9,10; after: reaches_below "
                  "(one family alone cannot satisfy two-families-per-side, so the "
                  "coverage status is informational here)",
        "before": before, "reach_picks": picks, "reach_picks_batch_2": picks2,
        "after": after,
        "extrapolation": E.expected_severity_to_reach("MK8", ladder, target=0.47)}
    (OUT / "spectrum_scenarios.json").write_text(json.dumps(scenarios, indent=1, default=str))
    L = ["# Spectrum-rule scenarios (constructed pools, deterministic)", ""]
    for name, sc in scenarios.items():
        L.append(f"## {name}")
        L.append(f"Expectation: {sc['expect']}")
        for k, v in sc.items():
            if k == "expect":
                continue
            L.append(f"- {k}: {json.dumps(v, default=str)[:900]}")
        L.append("")
    (OUT / "spectrum_scenarios.md").write_text("\n".join(L) + "\n")
    for name, sc in scenarios.items():
        inner = sc.get("after", sc)
        print(name, "->", inner.get("new_status"), "old_c4", inner.get("old_c4"),
              "families_old_c4", inner.get("families_meeting_old_c4"),
              "beyond_v_head", inner.get("beyond_v_head"),
              "reaches below/above", inner.get("reaches_below"), inner.get("reaches_above"),
              "rejections", inner.get("spectrum_rejections"))
        if "before" in sc:
            print("   before: reaches_below", sc["before"]["reaches_below"],
                  "| picks", sc["reach_picks"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
