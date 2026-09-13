"""The candidate landscape after §7.0-R3, per model and per rung.

Reads **solo and chance compliance only**, from the §12.2 ladder screen's own
record. It touches no composed cell, no `D(B <- R)`, no `Delta`, no `Xi`: §12.5
and §13.9 forbid a composed outcome reaching candidate construction, and this
is a report about candidate construction.

What it answers is the question amendment R3 was registered to answer. The
round-0 library's numerators are rare in ordinary prose, so their budgets are
impossible at the tight rungs and free at the loose ones; R3 added four common
numerators in both budget forms and A's own predicate in the class arm. Whether
that worked is a per-rung fact about instructed compliance, and this writes it
out per rung rather than summarising it.

    python3 tools/v4r3_candidate_landscape.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4r3 import CLASSIFICATION                                 # noqa: E402
from dci1v4r3.engine.paths import current_files                    # noqa: E402
from dci1v4r3.protocol import constants as C                       # noqa: E402
from dci1v4r3.verifiers.constraints import (                       # noqa: E402
    FAMILIES, R3_FAMILY_IDS,
)

EVIDENCE = DCI1 / "evidence" / "dci1v4r3"
OUT = DCI1 / "reports" / "dci1v4r3" / "candidate_landscape.json"


def _reason(entry: dict[str, Any], iota_a: float) -> str:
    """Why a rung is not eligible, in the registered vocabulary."""
    lo, hi = C.SPECTRUM_ELIGIBILITY_BAND
    if entry.get("iota") is None:
        return (f"chance-degenerate: kappa {entry['chance']:.2f} at or above "
                f"{C.CHANCE_DEGENERACY_MAX}, so iota is undefined (§11.2)")
    iota = entry["iota"]
    if iota < lo:
        return (f"below the eligibility floor {lo}: stating it changes "
                "compliance by less than the smallest effect of interest")
    if iota > hi:
        return f"above the eligibility ceiling {hi}"
    return ""


def _rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    iota_a = record["iota_a_prescreen"]
    lo, hi = C.SPECTRUM_ELIGIBILITY_BAND
    out: list[dict[str, Any]] = []
    for label, entry in sorted(record["difficulty_table"].items()):
        kind = label.split(":")[0]
        family = FAMILIES.get(kind)
        if family is None:
            continue                       # A and B are outcomes, not candidates
        iota = entry.get("iota")
        eligible = iota is not None and lo <= iota <= hi
        out.append({
            "rung": label, "family": kind,
            "statistic": family.statistic_id,
            "feature_group": family.feature_group,
            "form": family.form, "role": family.role,
            "class": family.constraint_class,
            "added_by_r3": kind in R3_FAMILY_IDS,
            "solo_compliance": entry["solo"],
            "accidental_compliance": entry["chance"],
            "iota": iota,
            "eligible": eligible,
            "rejection_reason": "" if eligible else _reason(entry, iota_a),
            "relative_to_A": (None if iota is None else
                              "below" if iota < iota_a else
                              "above" if iota > iota_a else "at"),
            "distance_from_A": None if iota is None else abs(iota - iota_a),
            "solo_vacuity": entry["solo_vacuity"],
            "median_words": entry["median_words"],
        })
    return out


def _per_model(record: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(record)
    coverage = record["expansion"]["coverage"]
    eligible = [r for r in rows if r["eligible"]]
    r3 = [r for r in rows if r["added_by_r3"]]
    r3_eligible = [r for r in r3 if r["eligible"]]
    well_formed = set(coverage["conditions"]["C4_straddling_families"]
                      ["observed"]["well_formed"])
    return {
        "iota_a_prescreen": record["iota_a_prescreen"],
        "selected_cap": record["selected_cap"],
        "coverage_passed": coverage["passed"],
        "expansion_rounds_run": record["expansion"]["rounds_run"],
        "conditions": {k: v["met"] for k, v in coverage["conditions"].items()},
        "straddling_well_formed": sorted(well_formed),
        "well_formed_added_by_r3": sorted(w for w in well_formed
                                          if w in R3_FAMILY_IDS),
        "rungs": {"measured": len(rows), "eligible": len(eligible),
                  "added_by_r3": len(r3),
                  "eligible_added_by_r3": len(r3_eligible)},
        "eligible_share": {
            "round_zero_library": _share(
                [r for r in rows if not r["added_by_r3"]]),
            "added_by_r3": _share(r3)},
        "counterfactual_without_r3": _without_r3(record, rows),
        "leave_one_family_out": _leave_one_out(record, rows),
        "shortlist": record["shortlist"],
        "class_candidates_near_A": coverage["conditions"]["C7_class_matched"]
                                           ["observed"]["rungs"],
        "table": rows,
    }


def _without_r3(record: dict[str, Any], rows: list[dict[str, Any]]
                ) -> dict[str, Any]:
    """How many feature groups C4 would have found in the round-0 library
    alone, at the iota_A this screen measured.

    Necessary, because coverage passing after R3 does not by itself show that
    R3 is why. The screen is a fresh measurement and iota_A moved with it, so
    a family that did not straddle the old value can straddle the new one
    without anything having been added.
    """
    groups = _well_formed_groups(rows, record["iota_a_prescreen"],
                                 only_pre_r3=True)
    return {"well_formed_groups": sorted(groups),
            "n_well_formed_groups": len(groups),
            "c4_would_pass": len(groups) >= C.COVERAGE_MIN_STRADDLING_FAMILIES,
            "rule": "C4 recomputed over the pre-R3 families only, at the "
                    "iota_A this screen measured"}


def _leave_one_out(record: dict[str, Any], rows: list[dict[str, Any]]
                   ) -> dict[str, Any]:
    """Which added families C4 could not do without.

    Coverage passing is not the same as coverage being robust. If one added
    family is load-bearing on three of four replications, the amendment bought
    a margin of exactly one family, and a reader is entitled to know that
    rather than to see four green ticks. C4's own rule is recomputed with each
    admitted family removed in turn.
    """
    iota_a = record["iota_a_prescreen"]
    admitted = sorted({r["family"] for r in rows
                       if r["eligible"] and r["role"] == "reference"})
    out: dict[str, Any] = {}
    for held_out in admitted:
        groups = _well_formed_groups(rows, iota_a, exclude={held_out})
        if len(groups) < C.COVERAGE_MIN_STRADDLING_FAMILIES:
            out[held_out] = {"c4_without_it": False,
                             "groups_left": sorted(groups)}
    return {"load_bearing": sorted(out),
            "detail": out,
            "margin": ("C4 has no spare family on this model"
                       if out else
                       "no single admitted family is load-bearing")}


def _well_formed_groups(rows: list[dict[str, Any]], iota_a: float, *,
                        exclude: set[str] = frozenset(),
                        only_pre_r3: bool = False) -> set[str]:
    """C4's own rule --- straddling, three eligible rungs, span 0.40 ---
    over a chosen subset of the families."""
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if (row["role"] != "reference" or not row["eligible"]
                or row["family"] in exclude
                or (only_pre_r3 and row["added_by_r3"])):
            continue
        by_family.setdefault(row["family"], []).append(row)
    groups = set()
    for family, members in by_family.items():
        values = sorted(r["iota"] for r in members)
        if (any(v < iota_a for v in values) and any(v > iota_a for v in values)
                and len(values) >= C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY
                and max(values) - min(values)
                >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN):
            groups.add(FAMILIES[family].feature_group)
    return groups


def _share(rows: list[dict[str, Any]]) -> float | None:
    return (sum(1 for r in rows if r["eligible"]) / len(rows)) if rows else None


def main() -> int:
    per_model: dict[str, Any] = {}
    for path in sorted(current_files(EVIDENCE, "regime_record.json")):
        if path.parent.name != "records":
            continue
        payload = json.loads(path.read_text())
        payload = payload.get("payload", payload)
        if payload.get("outcome") != "PASS":
            continue
        per_model[payload["model_key"]] = _per_model(payload)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "artifact_type": "v4r3-candidate-landscape",
        "classification": CLASSIFICATION,
        "reads": "solo and chance compliance from the §12.2 ladder screen only",
        "reads_no_composed_outcome": True,
        "eligibility_band": list(C.SPECTRUM_ELIGIBILITY_BAND),
        "r3_families": list(R3_FAMILY_IDS),
        "models": per_model}, indent=1, sort_keys=True) + "\n")

    for model, entry in per_model.items():
        print(f"=== {model}  iota_A={entry['iota_a_prescreen']:.3f}  "
              f"coverage {'PASS' if entry['coverage_passed'] else 'FAIL'}  "
              f"rounds={entry['expansion_rounds_run']}")
        failed = [k for k, met in entry["conditions"].items() if not met]
        print(f"    conditions failing        : {failed or 'none'}")
        print(f"    well-formed straddling    : "
              f"{entry['straddling_well_formed']} "
              f"(R3: {entry['well_formed_added_by_r3']})")
        share = entry["eligible_share"]
        print(f"    eligible share, round-0   : "
              f"{share['round_zero_library']:.3f}" if share["round_zero_library"]
              is not None else "    eligible share, round-0   : n/a")
        print(f"    eligible share, R3        : "
              f"{share['added_by_r3']:.3f}" if share["added_by_r3"]
              is not None else "    eligible share, R3        : n/a")
        counter = entry["counterfactual_without_r3"]
        print(f"    C4 groups without R3      : "
              f"{counter['n_well_formed_groups']} "
              f"{counter['well_formed_groups']} -> C4 "
              f"{'PASSES' if counter['c4_would_pass'] else 'FAILS'}")
        loo = entry["leave_one_family_out"]
        print(f"    load-bearing families     : "
              f"{loo['load_bearing'] or 'none'}")
        print(f"    class candidates near A   : "
              f"{entry['class_candidates_near_A']}")
        print()
    print(f"wrote {OUT.relative_to(DCI1)}  ({len(per_model)} model(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
