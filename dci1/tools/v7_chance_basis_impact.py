#!/usr/bin/env python3
"""What the §13.11 chance column's correction does to stored calibration data.

    python3 tools/v7_chance_basis_impact.py \\
        --tree v7=/path/to/dci1/evidence/dci1v7 \\
        --tree v7-development=/path/to/dci1/evidence/dci1v7-development/evidence/dci1v7 \\
        --out reports/dci1v7/chance_basis_impact

Read-only over every tree it is given. For each replication that holds a
signed Gate-2 record it:

1. reads the Gate-2 record and the unconstrained rows of its grid runs;
2. rebuilds §13.11's table with `chance_compliance` measured as §13.2
   registers it --- the same `cell_rates(..., present=False,
   arm="unconstrained")` the corrected producer uses --- every other column
   copied from the record, and applies `_withhold_degenerate`;
3. runs the production kernels on the recorded table and on the corrected
   one: Gate 2.5's qualification, Gate 3A's §13.7 stability and §12.6
   calibrated re-read, Gate 3B's selection, Gate 3C's support and arm set;
4. reproduces the signed Gate 2.5 / 3A / 3B / 3C records from the recorded
   table first (the kernels are the ones the stages call), and reports
   every difference the corrected table makes.

Nothing under any tree is written. The report is
``<out>/impact.json`` and ``<out>/REPORT.md``; every number in the markdown
comes from the JSON. Evidence trees are gitignored, so each Gate-2 record is
cited by path and by the SHA-256 of its bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.errors import ProtocolError
from dci1v7.analysis.intervals import wilson
from dci1v7.protocol import constants as C
from dci1v7.run import gates_run
from dci1v7.run.execute import cell_rates
from dci1v7.stages import feasibility
from dci1v7.stages.calibration_table import (
    instructed_compliance,
    load_calibration_table,
)
from dci1v7.stages.qualification_gate import qualify_candidates

STAGE_FILES = {
    "regime": ("REGIME_SCREEN", "regime_record.json"),
    "gate2": ("GATE_2_FOCAL_CALIBRATION", "gate2_focal_calibration.json"),
    "gate2_5": ("GATE_2_5_CANDIDATE_QUALIFICATION",
                "gate2_5_candidate_qualification.json"),
    "gate3a": ("GATE_3A_REFERENCE_CALIBRATION",
               "gate3a_reference_calibration.json"),
    "gate3b": ("GATE_3B_REFERENCE_SELECTION",
               "gate3b_reference_selection.json"),
    "gate3c": ("GATE_3C_IDENTIFICATION", "gate3c_identification.json"),
    "final": ("FINAL_REPORT", "final_report.json"),
}
SPLITS = (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _record(model_dir: pathlib.Path, key: str) -> dict[str, Any] | None:
    stage, name = STAGE_FILES[key]
    path = model_dir / stage / name
    if not path.exists():
        return None
    return json.load(open(path))


def _unconstrained_rows(gate2_dir: pathlib.Path) -> list[dict[str, Any]]:
    """The grid runs' unconstrained rows, reduced to what `cell_rates` reads."""
    out: list[dict[str, Any]] = []
    runs = sorted(p for p in (gate2_dir / "backend_runs").iterdir()
                  if p.name.startswith("grid"))
    for run in runs:
        with open(run / "scored.jsonl") as f:
            for line in f:
                if '"arm": "unconstrained"' not in line:
                    continue
                r = json.loads(line)
                if r.get("arm") != gates_run.UNCONSTRAINED_ARM:
                    continue
                out.append({
                    "topic_split": r["topic_split"], "arm": r["arm"],
                    "topic_id": r["topic_id"], "block_id": r["block_id"],
                    "word_count": r["word_count"],
                    "truncated": r["truncated"],
                    "scores": [{"kind": s["kind"], "severity": s["severity"],
                                "present": s["present"],
                                "passed": s["passed"],
                                "vacuous_pass": s["vacuous_pass"],
                                "graded": s["graded"]}
                               for s in r["scores"] if not s["present"]]})
    return out


def _corrected_tables(gate2: dict[str, Any],
                      unconstrained: list[dict[str, Any]]
                      ) -> dict[str, list[dict[str, Any]]]:
    """The recorded table with the chance column measured as §13.2 says."""
    out: dict[str, list[dict[str, Any]]] = {}
    for split in SPLITS:
        restrict = None if split == "pooled" else split
        rows = []
        for row in gate2["calibration_rows"][split]:
            chance = cell_rates(unconstrained, kind=row["kind"],
                                severity=row["severity"], present=False,
                                split=restrict,
                                arm=gates_run.UNCONSTRAINED_ARM)
            if chance["n_topics"] != row["n_topics"]:
                raise ProtocolError(
                    f"{row['kind']}:{row['severity']} on {split}: "
                    f"{chance['n_topics']} unconstrained topics against "
                    f"{row['n_topics']} solo topics")
            new = dict(row)
            new["chance_compliance"] = chance["compliance"]
            rows.append(new)
        out[split] = rows
    return out


def _qualify(table: list[dict[str, Any]], *, model_key: str, m_star: int
             ) -> dict[str, Any]:
    rows = load_calibration_table(table, model_key=model_key, m_star=m_star,
                                  split="pooled")
    return qualify_candidates(rows, model_key=model_key, m_star=m_star)


def _downstream(gate2: dict[str, Any], regime: dict[str, Any] | None, *,
                model_key: str, m_star: int, qualification: dict[str, Any]
                ) -> dict[str, Any]:
    """Gate 3A, 3B and 3C's kernels on one Gate-2 record."""
    shaped = {"qualification_by_severity": {str(m_star): {
        "qualified_pool": qualification["qualified_pool"],
        "qualified_families": qualification["qualified_families"],
        "n_qualified": qualification["n_qualified"]}}}
    calibration = feasibility.calibration_at(
        model_key=model_key, gate2_record=gate2, gate2_5_record=shaped,
        m_star=m_star, seed=0, resamples=C.STABILITY_BOOTSTRAP_RESAMPLES)
    chosen = feasibility.selection_at(calibration, model_key=model_key)
    out: dict[str, Any] = {
        "n_rows": dict(calibration["n_rows"]),
        "n_stable": calibration["n_stable"],
        "stable": sorted(k for k, v in calibration["stability"].items()
                         if v.get("passed")),
        "slot_map": {k: list(v) for k, v in chosen["slot_map"].items()},
        "selection_statuses": list(chosen["identification_statuses"]),
    }
    if regime is not None:
        coverage = feasibility.coverage_at_calibrated_iota_a(
            gate2_record=gate2, regime_record=regime)
        support = feasibility.support_at(
            chosen, model_key=model_key,
            calibration={"qualified_families":
                         list(qualification["qualified_families"])},
            regime_record=regime,
            extra_design_time_failures=list(coverage["failures"]),
            extra_spectrum_failures=list(coverage["spectrum_failures"]))
        report = support["report"]
        out.update({
            "coverage_conditions": dict(coverage["conditions"]),
            "coverage_core_met": coverage["core_met"],
            "coverage_spectrum_met": coverage["spectrum_met"],
            "coverage_n_eligible": coverage["n_eligible"],
            "coverage_coordinate_undefined": [
                r["candidate"] for r in coverage["coordinate_undefined"]],
            "support_met": report["support_met"],
            "support_failures": list(report["failures"]),
            "support_disposition": report["disposition"],
            "spectrum_met": report["spectrum_met"],
            "arms": list(support["arms"]),
            "identification_statuses": list(
                support["identification_statuses"]),
            "not_identified_members": list(report["not_identified_members"]),
        })
    return out


def _candidate_rows(recorded: list[dict[str, Any]],
                    corrected: list[dict[str, Any]],
                    q_old: dict[str, Any], q_new: dict[str, Any]
                    ) -> list[dict[str, Any]]:
    """Per pooled candidate: both chance values, both coordinates, and the
    §13.4 / §13.6 verdicts under each."""
    by_old = {v["candidate"]: v for v in q_old["verdicts"]}
    by_new = {v["candidate"]: v for v in q_new["verdicts"]}
    out = []
    for old, new in zip(recorded, corrected):
        label = f"{old['kind']}:{old['severity']}"
        kappa = new["chance_compliance"]
        degenerate = kappa >= C.CHANCE_DEGENERACY_MAX
        entry = {
            "candidate": label, "solo": old["solo_compliance"],
            "chance_recorded": old["chance_compliance"],
            "chance_corrected": kappa,
            "chance_wilson_upper": wilson(kappa, old["n_topics"])[1],
            "iota_recorded": instructed_compliance(
                old["solo_compliance"], old["chance_compliance"]),
            "iota_corrected": (None if degenerate else instructed_compliance(
                old["solo_compliance"], kappa)),
            "lift_corrected": old["solo_compliance"] - kappa,
            "kappa_under_b": old.get("kappa_under_b"),
            "above_ceiling": kappa > C.CHANCE_MAX,
            "wilson_above": wilson(kappa, old["n_topics"])[1]
            > C.CHANCE_WILSON_UPPER_MAX,
            "degenerate_withheld": degenerate,
            "qualified_recorded": by_old[label]["passed"],
            "first_failing_recorded": by_old[label]["first_failing_component"],
        }
        if label in by_new:
            entry["qualified_corrected"] = by_new[label]["passed"]
            entry["first_failing_corrected"] = \
                by_new[label]["first_failing_component"]
            entry["components_changed"] = sorted(
                c_new["component"] for c_old, c_new in zip(
                    by_old[label]["components"], by_new[label]["components"])
                if c_old["passed"] != c_new["passed"])
        else:
            entry["qualified_corrected"] = False
            entry["first_failing_corrected"] = "WITHHELD_DEGENERATE"
            entry["components_changed"] = ["withheld"]
        out.append(entry)
    return out


def analyse(label: str, model_dir: pathlib.Path) -> dict[str, Any] | None:
    gate2 = _record(model_dir, "gate2")
    if gate2 is None:
        return None
    t0 = time.time()
    model_key = gate2["model_key"]
    m_star = int(gate2["m_star"])
    gate2_dir = model_dir / STAGE_FILES["gate2"][0]
    regime = _record(model_dir, "regime")
    signed = {k: _record(model_dir, k)
              for k in ("gate2_5", "gate3a", "gate3b", "gate3c", "final")}
    unconstrained = _unconstrained_rows(gate2_dir)
    recorded = {s: [dict(r) for r in gate2["calibration_rows"][s]]
                for s in SPLITS}
    corrected_all = _corrected_tables(gate2, unconstrained)
    corrected, withheld = gates_run._withhold_degenerate(corrected_all)

    q_old = _qualify(recorded["pooled"], model_key=model_key, m_star=m_star)
    q_new = _qualify(corrected["pooled"], model_key=model_key, m_star=m_star)
    gate2_old = dict(gate2)
    gate2_new = dict(gate2)
    gate2_new["calibration_rows"] = corrected
    gate2_new["calibration_rows_withheld"] = withheld
    down_old = _downstream(gate2_old, regime, model_key=model_key,
                           m_star=m_star, qualification=q_old)
    down_new = _downstream(gate2_new, regime, model_key=model_key,
                           m_star=m_star, qualification=q_new)

    # Sanity: the kernels on the recorded table reproduce the signed records.
    reproduction: dict[str, Any] = {}
    if signed["gate2_5"] is not None:
        reproduction["gate2_5_pool"] = (
            sorted(q_old["qualified_pool"])
            == sorted(signed["gate2_5"]["qualified_pool"]))
    if signed["gate3a"] is not None:
        reproduction["gate3a_stability"] = (
            sorted(down_old["stable"]) == sorted(
                k for k, v in signed["gate3a"]["stability"].items()
                if v.get("passed")))
    if signed["gate3b"] is not None:
        reproduction["gate3b_slot_map"] = (
            down_old["slot_map"] == {k: list(v) for k, v in
                                     signed["gate3b"]["slot_map"].items()})
    if signed["gate3c"] is not None:
        # A Gate-3C record written before v7 A7 (2026-08-28) read §12.6's
        # coverage failures pre-A7 --- C4 lost cost the core arm --- and the
        # kernel here is A7's, so its arms and support verdict are not the
        # kernel's to reproduce. A7's records carry `spectrum_met`.
        if "spectrum_met" in signed["gate3c"]:
            reproduction["gate3c_arms"] = (
                down_old.get("arms")
                == list(signed["gate3c"]["admitted_arms"]))
            reproduction["gate3c_support_met"] = (
                down_old.get("support_met")
                == signed["gate3c"]["support"]["support_met"])
        else:
            reproduction["gate3c_predates_a7_not_compared"] = True

    rows = _candidate_rows(recorded["pooled"], corrected_all["pooled"],
                           q_old, q_new)
    solo_a = float(gate2["solo_compliance_a"])
    n_star = str(gate2["n_star"])
    kappa_a_blend = float(gate2["chance_curves"]["A"][n_star])
    kappa_a_unc = float(gate2["load_zero_chance_curves"]["A"][n_star])
    # Gate 3B's slot map: R1, R2, R3 are the core references; R1-, R1+, ...
    # the spectrum triples' outer rungs; CL the broad-class control; the
    # near-form controls carry their own slots.
    def _core(slot_map):
        return {slot: f"{k}:{s}" for slot, (k, s) in sorted(slot_map.items())
                if slot in ("R1", "R2", "R3")}

    def _spectrum(slot_map):
        return {slot: f"{k}:{s}" for slot, (k, s) in sorted(slot_map.items())
                if slot[-1] in "+-"}

    core_old = _core(down_old["slot_map"])
    core_new = _core(down_new["slot_map"])
    spectrum_old = _spectrum(down_old["slot_map"])
    spectrum_new = _spectrum(down_new["slot_map"])
    selected_old = sorted(core_old.values())
    selected_new = sorted(core_new.values())
    kappa_by = {r["candidate"]: r["chance_corrected"] for r in rows}
    final = signed["final"]
    delta_r = None
    if final is not None:
        delta_r = {
            "final_report_present": True,
            "admitted_arms": list(final.get("admitted_arms") or ()),
            # The final report's result rows, one per family member and
            # configuration; Delta_R is F1's member of that name.
            "delta_r_rows": [
                {k: s.get(k) for k in (
                    "family", "member", "configuration", "claim_level",
                    "estimate", "simultaneous_lower", "simultaneous_upper",
                    "realised_half_width", "status",
                    "identification_status")}
                for s in final.get("results", [])
                if isinstance(s, dict) and s.get("member") == "Delta_R"],
        }
    return {
        "tree": label, "model_key": model_key,
        "gate2_record": str(gate2_dir / STAGE_FILES["gate2"][1]),
        "gate2_record_sha256": _sha256(gate2_dir / STAGE_FILES["gate2"][1]),
        "study_id": gate2.get("study_id"),
        "producing_commit": gate2.get("producing_commit"),
        "n_star": gate2["n_star"], "m_star": m_star,
        "n_unconstrained_rows": len(unconstrained),
        "chance_basis": gates_run._chance_basis(unconstrained),
        "reproduction_of_signed_records_from_the_recorded_table":
            reproduction,
        "counts": {
            "candidates": len(rows),
            "chance_recorded_zero": sum(
                1 for r in rows if r["chance_recorded"] == 0.0),
            "chance_corrected_nonzero": sum(
                1 for r in rows if r["chance_corrected"] > 0),
            "above_ceiling_0_75": sum(1 for r in rows if r["above_ceiling"]),
            "wilson_upper_above_0_85": sum(
                1 for r in rows if r["wilson_above"]),
            "degenerate_withheld": sum(
                1 for r in rows if r["degenerate_withheld"]),
            "withheld_per_split": {s: len(withheld[s]) for s in SPLITS},
            "qualified_recorded": q_old["n_qualified"],
            "qualified_corrected": q_new["n_qualified"],
            "qualification_flipped": sorted(
                r["candidate"] for r in rows
                if r["qualified_recorded"] != r["qualified_corrected"]),
            "lift_now_below_floor": sorted(
                r["candidate"] for r in rows
                if r["lift_corrected"] < C.INSTRUCTION_LIFT_MIN
                and r["solo"] >= C.INSTRUCTION_LIFT_MIN),
            "max_abs_iota_shift": max(
                (abs(r["iota_corrected"] - r["iota_recorded"])
                 for r in rows if r["iota_corrected"] is not None),
                default=0.0),
        },
        "qualified_families": {"recorded": q_old["qualified_families"],
                               "corrected": q_new["qualified_families"]},
        "gate3": {"recorded": down_old, "corrected": down_new},
        "selected_references": {
            "recorded": selected_old, "corrected": selected_new,
            "changed": selected_old != selected_new,
            "core_slots": {"recorded": core_old, "corrected": core_new},
            "spectrum_slots": {"recorded": spectrum_old,
                               "corrected": spectrum_new,
                               "changed": spectrum_old != spectrum_new},
            "full_slot_map": {"recorded": down_old["slot_map"],
                              "corrected": down_new["slot_map"]},
            "corrected_kappa_of_recorded_selection": {
                c: kappa_by.get(c) for c in selected_old},
            "corrected_kappa_of_recorded_spectrum": {
                c: kappa_by.get(c) for c in sorted(spectrum_old.values())},
        },
        "changed_downstream": sorted(
            k for k in down_old
            if k in down_new and down_old[k] != down_new[k]),
        "iota_a_basis": {
            "note": "iota_A on the Gate-2 record is formed with A's chance "
                    "over every grid-A row where A:n* is absent (the "
                    "unconstrained cell and the other target severities' "
                    "solo cells); §13.2's unconstrained-cell basis gives "
                    "the second value. Reported, not changed by this fix.",
            "solo_a": solo_a,
            "kappa_a_recorded_basis": kappa_a_blend,
            "kappa_a_unconstrained_cell": kappa_a_unc,
            "iota_a_recorded": float(gate2["iota_a"]),
            "iota_a_unconstrained_basis": instructed_compliance(
                solo_a, kappa_a_unc),
        },
        "delta_r_on_final_report": delta_r,
        "candidates": rows,
        "seconds": round(time.time() - t0, 1),
    }


def _analyse_job(job: tuple[str, pathlib.Path]) -> dict[str, Any] | None:
    return analyse(*job)


def _md(results: list[dict[str, Any]]) -> str:
    lines = ["# §13.11 chance column: impact on stored calibration data",
             "",
             ("> Generated by `dci1/tools/v7_chance_basis_impact.py`. "
             "Do not edit by hand; every number is in `impact.json`."),
             "",
             ("Read-only over the trees named below. The recorded table's "
             "chance column is 0.0 on every replication (the defect); the "
             "corrected column is §13.2's kappa_c on the grid runs' "
             "unconstrained cells. The production kernels (Gate 2.5 "
             "qualification, Gate 3A stability and calibrated §12.6, Gate 3B "
             "selection, Gate 3C support) are run on both tables; on the "
             "recorded table they reproduce the signed records (the "
             "`reproduces` column), which is what makes the corrected "
             "column's consequences a statement about the study and not "
             "about this tool."),
             "",
             ("| tree | model | m* | cand. | κ>0 | >0.75 | Wilson>0.85 | "
             "withheld (≥0.99) | qualified rec→cor | flipped | selected "
             "refs changed | arms rec→cor | Δ_R-relevant κ of recorded "
             "refs | reproduces |"),
             "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|---|---|"]
    for r in results:
        c = r["counts"]
        g = r["gate3"]
        arms = f"{g['recorded'].get('arms')} → {g['corrected'].get('arms')}"
        sel = r["selected_references"]
        kap = ", ".join(f"{k}={v:.3f}" for k, v in
                        sel["corrected_kappa_of_recorded_selection"].items())
        rep = ", ".join(
            (f"{k}" if k.endswith("not_compared")
             else f"{k}={'yes' if v else 'NO'}")
            for k, v in r["reproduction_of_signed_records_from_the_"
                          "recorded_table"].items()) or "n/a"
        lines.append(
            f"| {r['tree']} | {r['model_key']} | {r['m_star']} | "
            f"{c['candidates']} | {c['chance_corrected_nonzero']} | "
            f"{c['above_ceiling_0_75']} | {c['wilson_upper_above_0_85']} | "
            f"{c['degenerate_withheld']} | {c['qualified_recorded']}→"
            f"{c['qualified_corrected']} | "
            f"{len(c['qualification_flipped'])} | "
            f"{'YES' if sel['changed'] else 'no'} | {arms} | {kap or '—'} | "
            f"{rep} |")
    lines += ["", "## Per replication", ""]
    for r in results:
        c = r["counts"]
        sel = r["selected_references"]
        g = r["gate3"]
        lines += [f"### {r['tree']} / {r['model_key']}", "",
                  (f"- Gate-2 record: `{r['gate2_record']}` "
                  f"(sha256 `{r['gate2_record_sha256'][:16]}…`), producing "
                  f"commit `{r['producing_commit']}`, study id "
                  f"`{r['study_id']}`."),
                  (f"- Chance basis: {r['n_unconstrained_rows']} unconstrained "
                  f"rows from runs {r['chance_basis']['runs']}; pooled "
                  f"{r['chance_basis']['per_split']['pooled']['n_topics']} "
                  f"topics × "
                  f"{r['chance_basis']['per_split']['pooled']['draws_per_topic']:.0f} "
                  "draws."),
                  (f"- Candidates whose qualification flips: "
                  f"{c['qualification_flipped'] or 'none'}."),
                  (f"- Candidates whose lift falls below 0.20 on the corrected "
                  f"column: {c['lift_now_below_floor'] or 'none'}."),
                  (f"- Largest |Δι| across candidates: "
                  f"{c['max_abs_iota_shift']:.4f}."),
                  (f"- Core references (Gate 3B slots R1–R3): recorded "
                  f"{sel['core_slots']['recorded']} → corrected "
                  f"{sel['core_slots']['corrected']}."),
                  (f"- Spectrum rungs (slots R·−/R·+): recorded "
                  f"{sel['spectrum_slots']['recorded']} → corrected "
                  f"{sel['spectrum_slots']['corrected']}."),
                  (f"- Full slot map: recorded "
                  f"{sel['full_slot_map']['recorded']} → corrected "
                  f"{sel['full_slot_map']['corrected']}."),
                  (f"- Downstream fields that differ between the two tables: "
                  f"{r['changed_downstream'] or 'none'}."),
                  (f"- §12.6 on the calibrated basis: conditions recorded "
                  f"{g['recorded'].get('coverage_conditions')} → corrected "
                  f"{g['corrected'].get('coverage_conditions')}; core met "
                  f"{g['recorded'].get('coverage_core_met')} → "
                  f"{g['corrected'].get('coverage_core_met')}; spectrum met "
                  f"{g['recorded'].get('coverage_spectrum_met')} → "
                  f"{g['corrected'].get('coverage_spectrum_met')}."),
                  (f"- Gate 3C: support met "
                  f"{g['recorded'].get('support_met')} → "
                  f"{g['corrected'].get('support_met')}; arms "
                  f"{g['recorded'].get('arms')} → {g['corrected'].get('arms')}; "
                  f"statuses {g['recorded'].get('identification_statuses')} "
                  f"→ {g['corrected'].get('identification_statuses')}."),
                  (f"- ι_A basis (reported, not changed): recorded "
                  f"{r['iota_a_basis']['iota_a_recorded']:.4f} "
                  f"(κ_A = {r['iota_a_basis']['kappa_a_recorded_basis']:.4f} "
                  "over every A-absent grid row) against "
                  f"{r['iota_a_basis']['iota_a_unconstrained_basis']:.4f} "
                  f"(κ_A = {r['iota_a_basis']['kappa_a_unconstrained_cell']:.4f} "
                  "on the unconstrained cell alone)."),
                  ""]
        in_maps = {f"{k}:{s}" for m in sel["full_slot_map"].values()
                   for k, s in m.values()}
        above = [x for x in r["candidates"]
                 if x["above_ceiling"] or x["degenerate_withheld"]
                 or x["qualified_recorded"] != x["qualified_corrected"]
                 or x["candidate"] in in_maps]
        if above:
            lines += [("| candidate | solo | κ corrected | ι rec | ι cor | "
                      "lift | κ(R|B) | qualified rec→cor | first failing "
                      "rec→cor | components changed |"),
                      "|---|---:|---:|---:|---:|---:|---:|---|---|---|"]
            for x in above:
                iota_c = ("—" if x["iota_corrected"] is None
                          else f"{x['iota_corrected']:.3f}")
                kb = ("—" if x["kappa_under_b"] is None
                      else f"{x['kappa_under_b']:.3f}")
                lines.append(
                    f"| {x['candidate']} | {x['solo']:.3f} | "
                    f"{x['chance_corrected']:.3f} | "
                    f"{x['iota_recorded']:.3f} | {iota_c} | "
                    f"{x['lift_corrected']:.3f} | {kb} | "
                    f"{x['qualified_recorded']}→{x['qualified_corrected']} | "
                    f"{x['first_failing_recorded']}→"
                    f"{x['first_failing_corrected']} | "
                    f"{x['components_changed']} |")
            lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", action="append", required=True,
                    help="label=path to a directory holding <model>/<STAGE>/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--workers", type=int, default=1,
                    help="replications analysed at once (spawned processes)")
    args = ap.parse_args()
    jobs: list[tuple[str, pathlib.Path]] = []
    for spec in args.tree:
        label, _, path = spec.partition("=")
        root = pathlib.Path(path)
        for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if args.models and model_dir.name not in args.models:
                continue
            if (model_dir / STAGE_FILES["gate2"][0]
                    / STAGE_FILES["gate2"][1]).exists():
                jobs.append((label, model_dir))
    if args.workers <= 1:
        outcomes = [analyse(label, model_dir) for label, model_dir in jobs]
    else:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(
                args.workers, mp_context=mp.get_context("spawn")) as pool:
            outcomes = list(pool.map(_analyse_job, jobs))
    results = []
    for (label, model_dir), result in zip(jobs, outcomes):
        if result is None:
            continue
        print(f"{label}/{model_dir.name}: {result['counts']} "
              f"selected changed={result['selected_references']['changed']} "
              f"({result['seconds']} s)", flush=True)
        results.append(result)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"generated_by": "dci1/tools/v7_chance_basis_impact.py",
               "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime()),
               "read_only": True, "results": results}
    (out / "impact.json").write_text(json.dumps(payload, indent=1,
                                                sort_keys=True))
    (out / "REPORT.md").write_text(_md(results))
    print(f"wrote {out / 'impact.json'} and {out / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
