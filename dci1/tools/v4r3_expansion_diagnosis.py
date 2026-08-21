"""Why §12.6's coverage fails, in enough detail to design the expansion.

Reads **solo and chance compliance only**, from the §12.2 ladder screen. It
touches no composed cell, no `D(B <- R)`, no `Delta`, no `Xi` --- §12.5 and
§13.9 forbid a composed outcome reaching candidate construction, and this is
candidate construction.

The question it answers is narrow and it matters: C4 asks for at least four
feature groups each containing **one family** that straddles `iota_A` with at
least three eligible rungs spanning 0.40. Three models fail it. There are two
very different reasons that could be true, and they call for opposite repairs:

* the **vocabulary** lacks rungs on one side of `iota_A` --- then the repair is
  new constraint families reaching that region;
* the vocabulary **has** rungs on both sides but they are split across two
  families of the same feature group, because a count budget and a rate budget
  over the same statistic land in different places --- then the repair is a
  family whose own ladder spans both sides.

The report separates them per model and per group. It proposes nothing and
changes nothing; C1-C7 and their values are untouched.
"""
from __future__ import annotations

import collections
import glob
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r3.protocol import constants as C                     # noqa: E402
from dci1v4r3.verifiers.constraints import (                     # noqa: E402
    FAMILIES, FEATURE_GROUPS, RESERVES,
)

EVIDENCE = DCI1 / "evidence" / "dci1v4r3"
OUT = DCI1 / "reports" / "dci1v4r3" / "expansion_diagnosis.json"

MIN_RUNGS = 3
MIN_SPAN = 0.40


def group_of(kind: str) -> str:
    return FEATURE_GROUPS[FAMILIES[kind].statistic_id]


def diagnose(record: dict) -> dict:
    iota_a = record["iota_a_prescreen"]
    lo, hi = C.SPECTRUM_ELIGIBILITY_BAND
    table = record["difficulty_table"]

    per_family: dict[str, list[float]] = collections.defaultdict(list)
    ineligible = collections.Counter()
    for label, entry in table.items():
        kind = label.split(":")[0]
        if kind in ("A", "B") or FAMILIES.get(kind) is None:
            continue
        if FAMILIES[kind].role != "reference":
            continue
        iota = entry.get("iota")
        if iota is None:
            ineligible["chance_degenerate"] += 1
            continue
        if iota < lo:
            ineligible["below_band"] += 1
            continue
        if iota > hi:
            ineligible["above_band"] += 1
            continue
        per_family[kind].append(float(iota))

    families = {}
    for kind, values in per_family.items():
        values = sorted(values)
        below = [v for v in values if v < iota_a]
        above = [v for v in values if v > iota_a]
        span = max(values) - min(values)
        families[kind] = {
            "group": group_of(kind), "form": FAMILIES[kind].form,
            "n_eligible": len(values), "n_below": len(below),
            "n_above": len(above), "iota_min": min(values),
            "iota_max": max(values), "span": span,
            "measured_of_reserve": f"{len(values)}/{len(RESERVES[kind])}",
            "straddles": bool(below and above),
            "well_formed": bool(below and above) and len(values) >= MIN_RUNGS
            and span >= MIN_SPAN,
        }

    groups: dict[str, dict] = {}
    for group in sorted({f["group"] for f in families.values()}):
        members = {k: v for k, v in families.items() if v["group"] == group}
        joint = sorted(v for k in members for v in per_family[k])
        below = [v for v in joint if v < iota_a]
        above = [v for v in joint if v > iota_a]
        groups[group] = {
            "families": sorted(members),
            "any_family_well_formed": any(m["well_formed"]
                                          for m in members.values()),
            "group_straddles_jointly": bool(below and above),
            "group_n_below": len(below), "group_n_above": len(above),
            "group_span": (max(joint) - min(joint)) if joint else 0.0,
            # the case that distinguishes the two repairs
            "split_across_families": (
                bool(below and above)
                and not any(m["straddles"] for m in members.values())),
        }

    well_formed_groups = [g for g, v in groups.items()
                          if v["any_family_well_formed"]]
    joint_groups = [g for g, v in groups.items()
                    if v["group_straddles_jointly"]]
    split = [g for g, v in groups.items() if v["split_across_families"]]
    return {
        "iota_a": iota_a,
        "eligibility_band": list(C.SPECTRUM_ELIGIBILITY_BAND),
        "c4_requirement": {"groups": 4, "min_rungs": MIN_RUNGS,
                           "min_span": MIN_SPAN},
        "well_formed_groups": well_formed_groups,
        "n_well_formed_groups": len(well_formed_groups),
        "c4_met": len(well_formed_groups) >= 4,
        "groups_straddling_jointly": joint_groups,
        "n_groups_straddling_jointly": len(joint_groups),
        "groups_split_across_families": split,
        "ineligible_rungs": dict(ineligible),
        "families": families, "groups": groups,
    }


def main() -> int:
    out = {}
    for path in sorted(glob.glob(str(EVIDENCE / "*/REGIME_SCREEN"
                                     "/regime_record.json"))):
        model = Path(path).parts[-3]
        out[model] = diagnose(json.loads(Path(path).read_text()))

    shortfall = {}
    for model, d in out.items():
        if d["c4_met"]:
            shortfall[model] = "C4 met"
            continue
        need = 4 - d["n_well_formed_groups"]
        gained = len(set(d["groups_straddling_jointly"])
                     - set(d["well_formed_groups"]))
        shortfall[model] = {
            "groups_short": need,
            "groups_that_straddle_jointly_but_have_no_single_straddling_family":
                gained,
            "reading": (
                "the vocabulary reaches both sides of iota_A in these groups; "
                "what it lacks is a FAMILY whose own ladder does"
                if gained >= need else
                "even jointly the vocabulary does not reach both sides in "
                "enough groups; new families reaching the missing region are "
                "needed, not only a re-shaped ladder")}

    payload = {
        "artifact": "§12.6 expansion diagnosis",
        "reads": "solo and chance compliance from the §12.2 ladder screen only",
        "reads_no_composed_outcome": True,
        "proposes": "nothing; C1-C7 and their values are untouched",
        "per_model": out, "shortfall": shortfall,
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")

    for model, d in out.items():
        print(f"=== {model}  iota_A={d['iota_a']:.3f}  "
              f"C4 {'MET' if d['c4_met'] else 'FAILS'}")
        print(f"    groups with a well-formed family : "
              f"{d['n_well_formed_groups']} {d['well_formed_groups']}")
        print(f"    groups straddling jointly        : "
              f"{d['n_groups_straddling_jointly']} "
              f"{d['groups_straddling_jointly']}")
        print(f"    groups split across families     : "
              f"{d['groups_split_across_families']}")
        print(f"    ineligible rungs                 : {d['ineligible_rungs']}")
        print(f"    -> {shortfall[model]}")
        print()
    print(f"wrote {OUT.relative_to(DCI1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
