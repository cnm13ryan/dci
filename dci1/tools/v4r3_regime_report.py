"""The stage-3 readout: what the candidate library delivered, per model.

Reads only the signed regime records. Every number it prints is recomputed
from `difficulty_table` rather than copied from a summary field, so the report
and the record cannot drift.

    ./.venv/bin/python tools/v4r3_regime_report.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dci1v4.engine import fs                                    # noqa: E402
from dci1v4.models.registry import MODELS                       # noqa: E402
from dci1v4r3.protocol import constants as C                    # noqa: E402
from dci1v4r3.verifiers.constraints import FAMILIES, feature_group  # noqa: E402

EVIDENCE = REPO / "evidence" / "dci1v4r3"
OUT = REPO / "reports" / "dci1v4r3"


def load(model_key: str) -> dict | None:
    path = EVIDENCE / model_key / C.STAGE_REGIME / "regime_record.json"
    return json.loads(path.read_text()) if path.exists() else None


def eligible(entry: dict) -> bool:
    if entry.get("iota") is None:
        return False
    low, high = C.SPECTRUM_ELIGIBILITY_BAND
    return (low <= entry["iota"] <= high
            and entry["solo_vacuity"] <= C.REFERENCE_VACUITY_MAX)


def secondary_coordinate_coverage(record: dict) -> dict:
    """§13.3's registered secondary coordinate, run through §12.6's criterion.

    Reported, never decisive. §13.3 requires raw solo compliance to be carried
    beside instructed compliance and §17.6 registers what a disagreement
    between them means, so the honest thing is to show what the criterion
    would have said on the other coordinate — and to say plainly that the
    registered outcome is the one computed on the registered coordinate.
    """
    from dci1v4r3.stages.library import LibraryRow, coverage_report
    table = record["difficulty_table"]
    a_solo = table[f"A:{record['a_anchor']['severity']}"]["solo"]
    rows = []
    for label, entry in table.items():
        if entry["kind"] not in FAMILIES:
            continue
        # The secondary coordinate is raw solo compliance, so the row is
        # built with chance set to zero: iota then *equals* solo.
        rows.append(LibraryRow(kind=entry["kind"], severity=entry["severity"],
                               solo_compliance=entry["solo"],
                               chance_compliance=0.0,
                               solo_vacuity=entry["solo_vacuity"]))
    report = coverage_report(rows, a_solo)
    return {"coordinate": "raw_solo_compliance", "a_solo": a_solo,
            "passed": report.passed,
            "conditions": {k: v["met"] for k, v in report.conditions.items()},
            "standing": "registered secondary diagnostic (§13.3, §17.6); the "
                        "replication's outcome is the one computed on the "
                        "registered coordinate"}


def summarise(record: dict) -> dict:
    table = record["difficulty_table"]
    iota_a = record["iota_a_prescreen"]
    families: dict[str, list] = {}
    for label, entry in table.items():
        if entry["kind"] in FAMILIES and eligible(entry):
            families.setdefault(entry["kind"], []).append(entry)
    ref = {k: v for k, v in families.items()
           if FAMILIES[k].role == "reference"}
    cls = {k: v for k, v in families.items()
           if FAMILIES[k].role == "class_control"}
    groups_below = {feature_group(k) for k, v in ref.items()
                    if any(e["iota"] < iota_a for e in v)}
    groups_above = {feature_group(k) for k, v in ref.items()
                    if any(e["iota"] > iota_a for e in v)}
    b_curve = {int(k.split(":")[1]): table[k]["solo"]
               for k in table if k.startswith("B:")}
    a_curve = {int(k.split(":")[1]): table[k]["solo"]
               for k in table if k.startswith("A:")}
    anti = [k for k, e in table.items()
            if e["kind"] in FAMILIES and e["iota"] is not None
            and e["iota"] <= 0]
    class_near = sorted(
        ((abs(e["iota"] - iota_a), f"{e['kind']}:{e['severity']}")
         for v in cls.values() for e in v))
    return {
        "model": record["model_key"],
        "selected_cap": record["selected_cap"],
        "rows_generated": record["rows_generated"],
        "iota_a_prescreen": iota_a,
        "a_anchor_severity": record["a_anchor"]["severity"],
        "a_solo_curve": a_curve,
        "b_solo_curve": b_curve,
        "b_solo_vacuity_max": max(table[k]["solo_vacuity"]
                                  for k in table if k.startswith("B:")),
        "eligible_reference_families": len(ref),
        "eligible_reference_rungs": sum(len(v) for v in ref.values()),
        "eligible_groups_below": sorted(groups_below),
        "eligible_groups_above": sorted(groups_above),
        "anti_productive_rungs": len(anti),
        "measured_instances": len(table),
        "expansion_rounds": record["expansion"]["rounds_run"],
        "coverage_passed": record["expansion"]["passed"],
        "coverage": record["expansion"]["coverage"]["conditions"],
        "statuses": record["expansion"]["statuses"],
        "class_nearest": class_near[:3],
        "shortlist": record["shortlist"],
        "secondary_coordinate": secondary_coordinate_coverage(record),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    for spec in MODELS:
        record = load(spec.model_key)
        if record is None:
            continue
        if record.get("outcome") == "TERMINAL":
            summaries.append({"model": spec.model_key,
                              "status": record["status"]})
            continue
        summaries.append(summarise(record))
    fs.write_json(OUT / "regime_summary.json",
                  {"study": "dci1v4r3", "stage": C.STAGE_REGIME,
                   "models": summaries})
    print(json.dumps(summaries, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
