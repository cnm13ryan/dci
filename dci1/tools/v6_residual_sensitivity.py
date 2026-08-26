#!/usr/bin/env python3
"""What §34 D23's reading and §34 D26's magnitude actually cost, swept.

    python3 tools/v6_residual_sensitivity.py [--check]

**Classification: DEVELOPMENT_EVIDENCE. Not a re-verdict of v5.** Every number
is the v6 rule applied to a v5 *measurement*; v5's records, verdicts, terminal
statuses and §34 D6 irreversibility stand exactly as signed.

**Why this exists.** ``precision_design.json``'s
``operating_point_feasibility`` established that every replication retains an
admissible operating point --- at ``residual_used = 0.0``, and at no other
value. The 2026-08-26 red team observed that this is the value the table was
being used to justify, so the feasibility evidence and the proposed magnitude
were the same choice twice. This sweeps the grid instead:

* **§34 D23's two readings.** ``projection_sd`` puts D26's number into the
  projection's quadrature and applies ``RESIDUAL_SD`` nowhere;
  ``beyond_the_measured_sd`` puts the measured ``RESIDUAL_SD = 0.0142`` into
  the quadrature and spends D26's number contracting §13.14's band.
* **Three magnitudes.** ``0.0`` (the withdrawn derivation), ``0.0142`` (the
  measured authored-sub-split residual carried by a pooled probe) and
  ``0.0687`` (``precision_design.json``'s own 95% upper bound on a residual
  sd thirteen observations could have missed).

**And under focal-only reselection**, the rule the researcher adopted on
2026-08-26: admissibility is decided by determinate entries alone. ``solo:B``
is determinate, so applying ``entry_verdict`` to each replication's measured
solo-B curve *is* the production rule and not a model of it. What this cannot
sweep is the rest of the determinate set --- ``solo:A`` and both orders of
``pair:A+B`` --- because v5 measured no composed A+B cell on the calibration
split. That is a real limit and it is reported rather than smoothed over:
these numbers are a *lower* bound on how often the rule bites.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))


def _load_precision_design():
    """Import the sibling tool for its readers, without copying them.

    A second implementation of ``_per_topic`` is a second definition of what
    a Gate-4 entry is, and the two would drift.
    """
    spec = importlib.util.spec_from_file_location(
        "_v6_precision_design", DCI1 / "tools" / "v6_precision_design.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


from dci1v6.protocol import constants as C                      # noqa: E402
from dci1v6.stages import composed_probe                        # noqa: E402

OUT = DCI1 / "reports" / "dci1v6" / "residual_sensitivity.json"

#: The magnitudes §34 D26 is being asked to choose between, and why each is on
#: the grid. Not a menu of admissible values --- D26 admits any number in
#: [0.0, 0.45) --- but the three the evidence actually names.
MAGNITUDES: tuple[tuple[float, str], ...] = (
    (0.0, "the withdrawn 2026-08-25 derivation: the transfer's DISPERSION is "
          "consistent with sampling, so nothing is left for a constant"),
    (composed_probe.RESIDUAL_SD,
     "the measured authored-sub-split residual carried by a pooled probe: "
     "half of 0.0284, paired by instrument on the closed v5 record"),
    (0.0687, "precision_design.json's own 95% upper bound on a residual sd "
             "thirteen observations could have missed --- 4.8x the measured "
             "value"),
)

READINGS: tuple[str, ...] = composed_probe.RESIDUAL_READINGS


def _band_and_sd(reading: str, magnitude: float) -> tuple[tuple[float, float],
                                                          float]:
    """The (band, projection sd) pair a closure at (reading, magnitude) gives.

    This mirrors ``composed_probe.margin_band`` and
    ``composed_probe.projection_residual_sd`` without going through
    ``decisions``, because those refuse while D23 and D26 are open and the
    whole point of this table is to be readable *before* they are closed.
    The mirroring is asserted below rather than trusted.
    """
    low, high = C.COMPOSED_HEADROOM_BAND
    if reading == "projection_sd":
        return (low, high), magnitude
    return (low + magnitude, high - magnitude), composed_probe.RESIDUAL_SD


def _solo_b_curve(pd, model_key: str) -> dict[int, dict[str, float]]:
    """Each measured B severity's compliance and between-topic variance."""
    rows = pd._rows(model_key, C.STAGE_GATE2, "grid-B")
    out: dict[int, dict[str, float]] = {}
    for severity in sorted({s["severity"] for row in rows
                            for s in row["scores"]
                            if s["present"] and s["kind"] == "B"}):
        topics = pd._per_topic(rows, f"solo:B:{severity}", kind="B",
                               severity=severity)
        out[int(severity)] = pd._moments(topics.values())
    return out


def build() -> dict[str, Any]:
    pd = _load_precision_design()
    curves = {m: _solo_b_curve(pd, m) for m in pd.MODELS}
    m_stars = {}
    for model_key in pd.MODELS:
        record = pd.transitions.read_stage_record(
            pd._tree(model_key), C.STAGE_GATE2)
        m_stars[model_key] = int(record["m_star"])

    # The half-width a typical determinate entry gets, so a reader can see
    # what a magnitude buys before reading any per-model verdict.
    s2_ref = pd.st.median(
        [v["s2_topic"] for c in curves.values() for v in c.values()])

    policies: list[dict[str, Any]] = []
    for reading in READINGS:
        for magnitude, why in MAGNITUDES:
            band, sd = _band_and_sd(reading, magnitude)
            half_ref = composed_probe.projected_halfwidth(
                s2_ref, n_probe=C.N_CALIBRATION, residual_sd=sd)
            per_model: dict[str, Any] = {}
            for model_key, curve in curves.items():
                per_severity = {}
                for severity, moments in curve.items():
                    verdict = composed_probe.entry_verdict(
                        {"compliance": moments["p"],
                         "s2_topic": moments["s2_topic"],
                         "n_topics": moments["n_topics"]},
                        cell_id="solo:B", slot="B", cell_slots=("B",),
                        residual_sd=sd, band=band)
                    per_severity[str(severity)] = {
                        "compliance": moments["p"],
                        "half_width": verdict["half_width"],
                        "passes": verdict["passes"]}
                passing = sorted(int(q) for q, v in per_severity.items()
                                 if v["passes"])
                per_model[model_key] = {
                    "m_star": m_stars[model_key],
                    "m_star_passes":
                        per_severity[str(m_stars[model_key])]["passes"],
                    "n_admissible_severities": len(passing),
                    "passing_severities": passing,
                    "per_severity": per_severity}
            policies.append({
                "reading": reading,
                "magnitude": magnitude,
                "magnitude_is": why,
                "evaluated_band": list(band),
                "projection_residual_sd": sd,
                "half_width_at_median_s2": half_ref,
                "band_width_consumed_by_one_entry":
                    2 * half_ref + (C.COMPOSED_HEADROOM_BAND[1]
                                    - C.COMPOSED_HEADROOM_BAND[0]
                                    - (band[1] - band[0])),
                "every_replication_retains_an_operating_point":
                    all(v["passing_severities"] for v in per_model.values()),
                "replications_with_no_operating_point": sorted(
                    k for k, v in per_model.items()
                    if not v["passing_severities"]),
                "per_model": per_model})

    return {
        "_what": "§34 D23's reading x §34 D26's magnitude, costed on the "
                 "closed v5 solo-B curves under focal-only reselection",
        "_classification": "DEVELOPMENT_EVIDENCE",
        "_not_a_re_verdict":
            "v5's records, verdicts and terminal statuses stand exactly as "
            "signed. This applies a v6 rule to a v5 measurement and says "
            "nothing about what v5 should have done",
        "_scope_limit":
            "solo:B is one of the six determinate entries and is the only one "
            "v5 measured on the calibration split: there is no composed A+B "
            "cell there. These verdicts are therefore a LOWER bound on how "
            "often the determinate rule bites, and the other five entries are "
            "measured for the first time when GATE_2_75 runs",
        "reselection_rule": "focal_only",
        "reselection_rule_is":
            "the researcher's 2026-08-26 decision: only determinate entries "
            "decide admissibility, so a stand-in cannot move m* or terminate "
            "a replication",
        "registered_band": list(C.COMPOSED_HEADROOM_BAND),
        "measured_residual_sd": composed_probe.RESIDUAL_SD,
        "median_s2_topic": s2_ref,
        "n_probe_topics": C.N_CALIBRATION,
        "n_composed_topics": C.N_COMPOSED,
        "policies": policies,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    payload = build()
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if args.check:
        current = OUT.exists() and OUT.read_text() == text
        print(f"{OUT} is {'current' if current else 'STALE'}")
        return 0 if current else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    for policy in payload["policies"]:
        print(f"  {policy['reading']:<22} {policy['magnitude']:<7} "
              f"half-width {policy['half_width_at_median_s2']:.4f}  "
              f"all retain an operating point: "
              f"{policy['every_replication_retains_an_operating_point']}"
              + (f"  (lost: {policy['replications_with_no_operating_point']})"
                 if policy["replications_with_no_operating_point"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
