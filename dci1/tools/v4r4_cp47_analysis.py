"""§7.0-R4's decision input: what the candidate population loses without CP4
and CP7.

**Outcome-safe by construction.** It reads one thing --- the §12.2 pre-screen
difficulty table on each replication's v4r3 `REGIME_SCREEN` record --- and
that table holds solo compliance, chance compliance and solo vacuity per rung
and nothing else. No composed cell, no `D(B <- R)`, no `Delta`, no `Xi`. §12.5
and §13.9 forbid a composed outcome reaching candidate construction, and this
is a report about candidate construction. The refusal is structural: the
loader below rebuilds `LibraryRow`, whose schema has no field a composed
outcome could occupy, and `load_prescreen_table` refuses one by name.

**What it decides.** §10.7 A' classified CP4's and CP7's third and fourth
model-facing wordings as genuinely ambiguous: they state the severity as a
target and name no bound, while the registered predicate is a lower bound.
Two remedies exist and the prospective rule chooses between them on coverage:

    if removing CP4 and CP7 preserves every registered coverage requirement
    with acceptable support -> remove them
    else -> rewrite the ambiguous wordings, invalidate every row generated
            under them, and regenerate before recomputing coverage

The report below evaluates C1 to C7 twice on the same measured table --- once
on v4r3's population, once on the population with the two families removed ---
and adds the support quantities §13.6 and §13.8 will need downstream, plus a
leave-one-family-out sweep, because a criterion that passes only through one
family is a criterion resting on one measurement.

    python3 tools/v4r4_cp47_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.protocol.hashing import sha_file                     # noqa: E402

from dci1v4r3.stages import library as lib_r3                    # noqa: E402
from dci1v4r4.protocol import constants as C                     # noqa: E402
from dci1v4r4.stages import library as lib_r4                    # noqa: E402
from dci1v4r4.verifiers.constraints import (                     # noqa: E402
    FAMILIES, REMOVED_IN_V4R4, feature_group,
)

MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
SOURCE = DCI1 / "evidence" / "dci1v4r3"
OUT = DCI1 / "reports" / "dci1v4r4" / "cp4_cp7_analysis.json"


def _record(model_key: str) -> dict[str, Any]:
    path = (SOURCE / model_key / "REGIME_SCREEN" / "records"
            / "regime_record.json")
    return fs.read_json(path)["payload"], str(path)


def _rows(record: dict[str, Any], module, *, keep: set[str] | None
          ) -> list[Any]:
    """The pre-screen table as library rows, optionally family-restricted."""
    rounds = {label: entry
              for entry in record["expansion"].get("history", [])
              for label in entry.get("admitted", [])}
    out = []
    for label, entry in sorted(record["difficulty_table"].items()):
        kind = entry["kind"]
        if kind in ("A", "B"):
            continue
        if keep is not None and kind not in keep:
            continue
        out.append(module.LibraryRow(
            kind=kind, severity=entry["severity"],
            solo_compliance=entry["solo"],
            chance_compliance=min(entry["chance"], 0.9899),
            solo_vacuity=entry["solo_vacuity"],
            admitted_in_round=rounds.get(label, 0),
            median_words=entry["median_words"],
            graded_mean=entry["graded_mean"]))
    return out


def _support(rows, iota_a: float) -> dict[str, Any]:
    """§13.6's and §13.8's inputs, at pre-screen resolution.

    Not the Gate-3 support verdict, which is defined on the fitted spectrum
    and cannot be computed before Gate 2 exists. These are the quantities that
    decide whether such a fit can be *attempted*: how many eligible reference
    rungs sit on each side of A, from how many distinct feature groups, and
    how dense the neighbourhood of A is.
    """
    eligible = [r for r in rows
                if r.role == "reference" and lib_r4.eligible_prescreen(r)]
    below = [r for r in eligible if r.iota < iota_a]
    above = [r for r in eligible if r.iota > iota_a]
    near = [r for r in eligible
            if abs(r.iota - iota_a) <= C.COVERAGE_NEAR_CALIPER]
    cls = [r for r in rows
           if r.role == "class_control" and lib_r4.eligible_prescreen(r)]
    class_near = [r for r in cls
                  if abs(r.iota - iota_a) <= C.CLASS_MATCH_CALIPER]
    straddling = sorted({
        k for k in {r.kind for r in eligible}
        if any(r.iota < iota_a for r in eligible if r.kind == k)
        and any(r.iota > iota_a for r in eligible if r.kind == k)})
    return {
        "eligible_reference_rungs": len(eligible),
        "easier_support": {
            "rungs": len(below),
            "feature_groups": sorted({feature_group(r.kind) for r in below}),
            "meets_min_below": len(below) >= C.SUPPORT_MIN_BELOW,
            "meets_min_families_per_side":
                len({feature_group(r.kind) for r in below})
                >= C.SUPPORT_MIN_FAMILIES_PER_SIDE},
        "harder_support": {
            "rungs": len(above),
            "feature_groups": sorted({feature_group(r.kind) for r in above}),
            "meets_min_above": len(above) >= C.SUPPORT_MIN_ABOVE,
            "meets_min_families_per_side":
                len({feature_group(r.kind) for r in above})
                >= C.SUPPORT_MIN_FAMILIES_PER_SIDE},
        "local_density": {
            "caliper": C.COVERAGE_NEAR_CALIPER,
            "rungs": len(near),
            "labels": [r.label for r in near],
            "feature_groups": sorted({feature_group(r.kind) for r in near})},
        "distinct_supporting_families": len({r.kind for r in eligible}),
        "distinct_supporting_feature_groups":
            len({feature_group(r.kind) for r in eligible}),
        "spectrum_support": {
            "straddling_families": straddling,
            "straddling_feature_groups":
                sorted({feature_group(k) for k in straddling}),
            "needed": C.N_CORE_REFERENCES,
            "sufficient_for_a_full_spectrum":
                len({feature_group(k) for k in straddling})
                >= C.N_CORE_REFERENCES},
        "core_reference_availability": {
            "eligible_families": sorted({r.kind for r in eligible}),
            "shortlist_needs": C.SHORTLIST_REFERENCE_FAMILIES,
            "available": len({r.kind for r in eligible})},
        "class_arm": {
            "caliper": C.CLASS_MATCH_CALIPER,
            "matched_rungs": [r.label for r in class_near],
            "matched_families": sorted({r.kind for r in class_near}),
            "matched": bool(class_near)},
    }


def _leave_one_out(rows, iota_a: float, module) -> dict[str, Any]:
    """Does the criterion survive dropping any one eligible family?"""
    families = sorted({r.kind for r in rows})
    out: dict[str, Any] = {}
    for dropped in families:
        kept = [r for r in rows if r.kind != dropped]
        report = module.coverage_report(kept, iota_a)
        out[dropped] = {
            "passed": report.passed,
            "failed": sorted(k for k, v in report.conditions.items()
                             if not v["met"] and k != "C7_class_matched"),
            "class_matched": report.class_matched}
    fragile = sorted(k for k, v in out.items() if not v["passed"])
    return {"per_family": out, "families_whose_removal_breaks_coverage":
            fragile, "robust": not fragile}


def main() -> int:
    keep = {k for k in FAMILIES}
    models: dict[str, Any] = {}
    for model_key in MODELS:
        record, path = _record(model_key)
        iota_a = record["iota_a_prescreen"]
        with_cp = _rows(record, lib_r3, keep=None)
        without_cp = _rows(record, lib_r4, keep=keep)
        before = lib_r3.coverage_report(with_cp, iota_a)
        after = lib_r4.coverage_report(without_cp, iota_a)
        moved = sorted(k for k in before.conditions
                       if before.conditions[k]["met"]
                       != after.conditions[k]["met"])
        models[model_key] = {
            "source_record": path,
            "source_record_hash": sha_file(Path(path)),
            "iota_a_prescreen": iota_a,
            "rungs_measured": {"v4r3": len(with_cp), "v4r4": len(without_cp)},
            "coverage_with_cp4_cp7": before.as_dict(),
            "coverage_without_cp4_cp7": after.as_dict(),
            "conditions_that_moved": moved,
            "support_without_cp4_cp7": _support(without_cp, iota_a),
            "leave_one_family_out": _leave_one_out(without_cp, iota_a,
                                                   lib_r4),
            # The same sweep on v4r3's population. It is here to answer the
            # only question the sweep raises that this decision could be
            # responsible for: did removing CP4 and CP7 make coverage more
            # fragile? The two lists agree, because the sweep drops one
            # *reference* family at a time and the removed families are
            # class_control.
            "leave_one_family_out_with_cp4_cp7": _leave_one_out(
                with_cp, iota_a, lib_r3),
        }

    fragility_unchanged = all(
        m["leave_one_family_out"]["families_whose_removal_breaks_coverage"]
        == m["leave_one_family_out_with_cp4_cp7"][
            "families_whose_removal_breaks_coverage"]
        for m in models.values())

    every_condition_holds = all(
        m["coverage_without_cp4_cp7"]["passed"] for m in models.values())
    class_still_matched = all(
        m["coverage_without_cp4_cp7"]["class_matched"]
        for m in models.values())
    nothing_moved = all(not m["conditions_that_moved"]
                        for m in models.values())
    decision = ("REMOVE_CP4_AND_CP7" if every_condition_holds
                and class_still_matched else "REWRITE_AND_REGENERATE")

    report = {
        "artifact_type": "v4r4-cp4-cp7-decision",
        "reads": "the §12.2 pre-screen difficulty table on each v4r3 "
                 "REGIME_SCREEN record: solo compliance, chance compliance "
                 "and solo vacuity per rung",
        "reads_no_composed_outcome": True,
        "finding": {k: dict(v) for k, v in REMOVED_IN_V4R4.items()},
        "decision_rule": (
            "remove CP4 and CP7 if every registered coverage requirement "
            "holds without them with acceptable support; otherwise rewrite "
            "the ambiguous wordings, invalidate every row generated under "
            "them and regenerate before recomputing coverage"),
        "why_c1_to_c6_cannot_move": (
            "§12.6's first six conditions read rows whose role is `reference`. "
            "CP4 and CP7 are `class_control`, so their removal cannot change "
            "those six on any table. This is a property of the criterion, not "
            "an observation about these four models, and the run below "
            "confirms it rather than resting on it"),
        "models": models,
        "every_coverage_condition_holds_without_them": every_condition_holds,
        "class_arm_still_matched_on_every_model": class_still_matched,
        "no_condition_changed_on_any_model": nothing_moved,
        "leave_one_family_out_is_unchanged_by_the_removal": fragility_unchanged,
        "leave_one_family_out_finding": (
            "coverage is NOT robust to dropping an arbitrary eligible "
            "reference family on three of the four replications. C4 requires "
            "four well-formed straddling feature groups and three models have "
            "exactly four, so any one of them is load-bearing. This is a "
            "property of the reference pool that v4r3 already had: the sweep "
            "run on v4r3's population returns the same families. It is "
            "reported, not repaired, because repairing it would mean adding "
            "candidate families after seeing a coverage result, which §12.6 "
            "forbids outside its registered expansion --- and the registered "
            "expansion draws from the frozen reserve, which is available if "
            "the researcher decides the margin is too thin"),
        "decision": decision,
        "what_removal_costs": (
            "CP4 and CP7 were the only families carrying the rate-lower-bound "
            "form. The class arm becomes {count lower bound, exact count}. "
            "§7.4-R3's own argument is why that is tolerable: A is an "
            "exact-count production constraint and CX1 is A's rule over a "
            "different marker word, which is the tightest class companion the "
            "grammar can build. The removed families were the loosest"),
        "what_rewriting_would_have_cost": (
            "the four wordings render at 60 severities across CP4 and CP7's "
            "declared ranges. Changing a live wording invalidates every "
            "measurement taken under it, and the §12.2 screen spreads four "
            "wordings over its 24 pre-screen topics, so the whole of both "
            "families' measured rows --- 16 round-0 rungs x 24 topics on each "
            "of four replications, 1,536 generations --- would have to be "
            "regenerated, not only the 768 rows carrying the two defective "
            "wordings"),
        "not_chosen_for_cost": (
            "the rule above is prospective and reads coverage only. The cost "
            "comparison is recorded because it is a real difference between "
            "the two remedies and a reader is entitled to see it, not because "
            "it entered the decision"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, report)
    print(json.dumps({
        "decision": decision,
        "coverage_holds_without_them": every_condition_holds,
        "class_matched": class_still_matched,
        "no_condition_moved": nothing_moved,
        "leave_one_out_fragility_unchanged": fragility_unchanged,
        "per_model": {k: {
            "iota_A": round(v["iota_a_prescreen"], 4),
            "passed": v["coverage_without_cp4_cp7"]["passed"],
            "class_rungs": v["support_without_cp4_cp7"]["class_arm"][
                "matched_families"],
            "leave_one_out_robust": v["leave_one_family_out"]["robust"],
            "fragile": v["leave_one_family_out"][
                "families_whose_removal_breaks_coverage"],
        } for k, v in models.items()},
        "written": str(OUT),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
