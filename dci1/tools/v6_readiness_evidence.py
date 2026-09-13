#!/usr/bin/env python3
"""Closed-v5 evidence for the v6 preregistration-readiness memo.

Every number in `reports/dci1v6/READINESS.md` that is not a constant is
computed here, from **signed v5 stage records** whose hash and signature are
verified on read, and from the raw scored rows those records were computed
from. Nothing is transcribed by hand.

**Classification: DEVELOPMENT_EVIDENCE.** Current v5 is read here only for
survival, identification and headroom. No effect quantity is estimated,
compared or interpreted; nothing below is evidence about `Delta_j`, `Delta_R`
or `Xi`; and a `NOT_IDENTIFIED` verdict is never read as a null result. v5 is
closed and none of this re-opens it: no record is written, mutated or
re-verdicted.

Two of the four replications raised `COMPOSED_HEADROOM_FAILURE` at Gate 4, so
no Gate-4 record was written for them. Their headroom tables are recomputed
here from the retained scored rows by the same rule `gates_run.gate4_payload`
applies, and the recomputation is **validated** against the two signed Gate-4
records and against the failing cells named in the two signed terminal
reports; the run aborts if any of those disagree.

    python3 tools/v6_readiness_evidence.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v5.engine import context as ctx                    # noqa: E402
from dci1v5.engine import transitions                       # noqa: E402
from dci1v4.engine.signing import verify_signed             # noqa: E402
from dci1v5.engine.paths import model_tree                  # noqa: E402
from dci1v5.protocol import constants as C                  # noqa: E402
from dci1v5.stages.regime import expansion_round, tie_key   # noqa: E402
from dci1v5.stages.selection import restrictiveness_key     # noqa: E402
from dci1v5.verifiers.constraints import (                  # noqa: E402
    LADDERS, RESERVES, TIER1_FAMILY_IDS)

OUT = DCI1 / "reports" / "dci1v6" / "readiness_evidence.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")
DELTAS = (0.025, 0.05, 0.075)


def _tree(model_key: str):
    return model_tree(ctx.registered_context(), model_key)


def _record(model_key: str, stage: str) -> dict:
    """The signed payload. Hash and signature are verified on read."""
    return transitions.read_stage_record(_tree(model_key), stage)


def _scored(model_key: str, stage: str, run: str) -> list[dict]:
    path = (_tree(model_key).backend_runs(stage) / run / "scored.jsonl")
    with path.open() as handle:
        return [json.loads(line) for line in handle]


# ------------------------------------------------ bottleneck 1: reachability

def expansion_reachability() -> dict:
    """Can §12.6's expansion rule ever reach a Tier-1 reserve rung?

    The Tier-1 reserve was widened from 1..10 to 1..12 for C4's span
    (`verifiers/constraints.py`, §7.10). This replays `expansion_round` on
    each replication's signed pre-screen table, from the registered round-0
    ladders, and records what it admits.
    """
    per_model = {}
    for model_key in MODELS:
        regime = _record(model_key, C.STAGE_REGIME)
        iota_a = regime["iota_a_prescreen"]
        table = [r for r in regime["difficulty_table"]
                 if not r.get("is_outcome")]
        iota = {(r["family"], r["severity"]): r["iota"] for r in table}
        plan = expansion_round(table, iota_a=iota_a,
                               measured={k: list(v)
                                         for k, v in LADDERS.items()})
        families = {}
        for family in TIER1_FAMILY_IDS:
            have = list(LADDERS[family])
            unmeasured = [q for q in RESERVES[family] if q not in have]
            pairs = [(q, iota[(family, q)]) for q in have
                     if (family, q) in iota]
            below = [q for q, v in pairs if tie_key(v) < tie_key(iota_a)]
            above = [q for q, v in pairs if tie_key(v) > tie_key(iota_a)]
            def key(q: int, _family: str = family) -> int:
                return restrictiveness_key(_family, q)

            if below and above:
                edges = sorted([max(below, key=key), min(above, key=key)],
                               key=key)
                lo, hi = key(edges[0]), key(edges[1])
                picks = [q for q in unmeasured if lo < key(q) < hi]
                branch, detail = "bracketing", {"edges": edges}
            elif below:
                edge = min(key(q) for q in have)
                picks = [q for q in unmeasured if key(q) < edge]
                branch, detail = "one_sided_below", {"go": "easier"}
            else:
                edge = max(key(q) for q in have)
                picks = [q for q in unmeasured if key(q) > edge]
                branch, detail = "one_sided_above", {"go": "harder"}
            families[family] = {
                "branch": branch, **detail,
                "n_below": len(below), "n_above": len(above),
                "measured_iota_span": round(max(v for _, v in pairs)
                                            - min(v for _, v in pairs), 4),
                "unmeasured_reserve": unmeasured,
                "picks": sorted(picks)}
        per_model[model_key] = {
            "iota_a_prescreen": iota_a,
            "families_admitted_round_1": sorted(plan["admitted"]),
            "tier1_admitted_round_1": sorted(
                k for k in plan["admitted"] if k in TIER1_FAMILY_IDS),
            "tier1_detail": families,
            "signed_rounds_tier1_admitted": sorted({
                family for rnd in regime["expansion"]["rounds"]
                for family in rnd.get("admitted", {})
                if family in TIER1_FAMILY_IDS}),
            "signed_n_rounds": len(regime["expansion"]["rounds"]),
        }
    reachable = any(m["tier1_admitted_round_1"]
                    or m["signed_rounds_tier1_admitted"]
                    for m in per_model.values())
    return {
        "question": "does §12.6's expansion rule ever admit a Tier-1 "
                    "reserve rung, on any of the four replications?",
        "answer": "yes" if reachable else "no",
        "tier1_reserve_rungs_per_family": [
            q for q in RESERVES["MK1"] if q not in LADDERS["MK1"]],
        "why": "the bracketing branch admits only reserve rungs lying "
               "strictly between the two measured edges that bracket iota_A, "
               "and every Tier-1 rung between those edges is already in the "
               "round-0 ladder; the one-sided-below branch goes easier, and "
               "the unmeasured Tier-1 reserve is harder. Both branches "
               "return an empty pick set for every Tier-1 family, on every "
               "replication.",
        "span_is_not_reachable_by_interpolation":
            "C4's span is max(iota) - min(iota) over a family's ELIGIBLE "
            "rungs. A rung admitted strictly between two measured edges "
            "cannot lie outside their range, so interpolation cannot raise "
            "any family's span by construction.",
        "per_model": per_model,
    }


def span_headroom() -> dict:
    """How much span is REACHABLE, for the families that missed C4 on span.

    C4's span is max(iota) - min(iota) over a family's eligible rungs, and
    §12.6's eligibility (U4 = E2) caps p_solo at 0.10. For a chance-free
    marker iota = p_solo, so the largest span a family could reach is
    max(eligible iota) - 0.10. This says whether 0.40 is reachable in
    principle; it does NOT say the rungs would land there, which is not
    knowable without measuring them.
    """
    diagnosis = json.loads(
        (DCI1 / "reports" / "dci1v5" / "survival_diagnosis.json").read_text())
    low = C.HEADROOM_BAND[0]
    per_model = {}
    for model_key in MODELS:
        regime = _record(model_key, C.STAGE_REGIME)
        eligible: dict[str, list[float]] = {}
        for row in regime["difficulty_table"]:
            if row.get("is_outcome"):
                continue
            if (C.HEADROOM_BAND[0] <= row["solo"] <= C.HEADROOM_BAND[1]
                    and (row.get("vacuity") or 0.0)
                    <= C.REFERENCE_VACUITY_MAX):
                eligible.setdefault(row["family"], []).append(row["iota"])
        entries = []
        for near in (diagnosis["replications"][model_key]
                     ["families_straddling_but_span_short_approx"]):
            values = eligible.get(near["family"], [])
            if not values:
                continue
            ceiling = max(values)
            entries.append({
                "family": near["family"],
                "feature_group": near["feature_group"],
                "measured_span": near["span"],
                "max_eligible_iota": ceiling,
                "largest_reachable_span": ceiling - low,
                "reaches_c4_span_in_principle":
                    ceiling - low >= C.COVERAGE_MIN_WITHIN_FAMILY_SPAN})
        per_model[model_key] = entries
    everything = [e for v in per_model.values() for e in v]
    return {
        "question": "for the families that straddle iota_A with >=3 rungs and "
                    "miss C4 only on the 0.40 span, is 0.40 reachable at all "
                    "inside the eligibility band?",
        "eligibility_floor_on_p_solo": low,
        "c4_span": C.COVERAGE_MIN_WITHIN_FAMILY_SPAN,
        "n_near_miss_families": len(everything),
        "all_reach_c4_span_in_principle":
            all(e["reaches_c4_span_in_principle"] for e in everything),
        "smallest_reachable_span": min(e["largest_reachable_span"]
                                       for e in everything),
        "caveat": "reachable in principle is not the same as reached. "
                  "Whether the added rungs fall far enough is a measurement "
                  "nobody has made; on gemma-3n-e2b-it MK1 had already "
                  "flattened at 0.417/0.416 by q = 7, 8.",
        "per_model": per_model,
    }


# ----------------------------------- bottleneck 2: headroom decomposition

def _headroom_table(model_key: str) -> dict:
    """`gate4_payload`'s rule, recomputed from the retained scored rows."""
    gate3b = _record(model_key, C.STAGE_GATE3B)
    gate2 = _record(model_key, C.STAGE_GATE2)
    slot_map = {k: (v[0], int(v[1]))
                for k, v in (gate3b.get("slot_map") or {}).items()}
    slot_map.setdefault("A", ("A", gate2["n_star"]))
    slot_map.setdefault("B", ("B", gate2["m_star"]))
    passes: dict[str, dict[str, list[float]]] = {}
    for row in _scored(model_key, C.STAGE_GATE4, "composed"):
        if row["cell_id"] == "unconstrained":
            continue
        for slot in row["slots"]:
            kind, severity = slot_map[slot]
            for score in row["scores"]:
                if (score["present"] and score["slot"] == slot
                        and score["kind"] == kind
                        and score["severity"] == severity):
                    passes.setdefault(row["cell_id"], {}) \
                           .setdefault(slot, []).append(float(score["passed"]))
    return {"slot_map": {k: list(v) for k, v in slot_map.items()},
            "table": {cell: {slot: sum(v) / len(v) for slot, v in e.items()}
                      for cell, e in passes.items()}}


def _validate(model_key: str, table: dict) -> dict:
    """Refuse to report a recomputation that disagrees with a signed record."""
    tree = _tree(model_key)
    checks = []
    if tree.stage_record(C.STAGE_GATE4).exists():
        signed = _record(model_key, C.STAGE_GATE4)["headroom_table"]
        for cell, entry in signed.items():
            for slot, value in entry.items():
                if slot == "unconstrained":
                    continue
                got = table[cell][slot]
                checks.append({"source": "GATE_4 record", "cell": cell,
                               "slot": slot, "signed": value, "recomputed": got,
                               "agrees": abs(got - value) < 1e-9})
    report = tree.terminal_report
    if report.exists():
        payload = verify_signed(json.loads(report.read_text()),
                                tree.context.signing_key_path,
                                where=f"{model_key}:terminal_report")
        for observed in payload.get("observed") or ():
            got = table[observed["cell"]][observed["slot"]]
            checks.append({"source": "terminal_report", **{
                k: observed[k] for k in ("cell", "slot")},
                "signed": observed["compliance"], "recomputed": got,
                "agrees": abs(got - observed["compliance"]) < 1e-9})
    disagree = [c for c in checks if not c["agrees"]]
    if disagree:
        raise SystemExit(
            f"{model_key}: recomputation disagrees with a signed record on "
            f"{len(disagree)} entr(ies); refusing to report. {disagree[:3]}")
    return {"n_checks": len(checks), "all_agree": True}


def headroom() -> dict:
    """Where the worst B cell's compliance came from, and what delta buys."""
    low, high = C.COMPOSED_HEADROOM_BAND
    per_model = {}
    for model_key in MODELS:
        built = _headroom_table(model_key)
        table = built["table"]
        validation = _validate(model_key, table)
        gate2 = _record(model_key, C.STAGE_GATE2)
        m_star = gate2["m_star"]
        calibration_solo_b = gate2["solo_curves"]["B"][str(m_star)]
        composed_solo_b = table["solo:B"]["B"]
        composed = {cell: entry["B"] for cell, entry in table.items()
                    if "B" in entry and cell != "solo:B"}
        worst_cell = max(composed, key=composed.get)
        entries = [(cell, slot, value) for cell, entry in table.items()
                   for slot, value in entry.items()]
        per_model[model_key] = {
            "m_star": m_star,
            "admitted_arms": _record(model_key,
                                     C.STAGE_GATE3C)["admitted_arms"],
            "n_evaluated_cell_slot_entries": len(entries),
            "recomputation_validated_against_signed_records": validation,
            "decomposition_of_the_worst_B_cell": {
                "calibration_split_solo_B_at_m_star": calibration_solo_b,
                "split_transfer_calibration_to_composed":
                    composed_solo_b - calibration_solo_b,
                "composed_split_solo_B": composed_solo_b,
                "composition_term": composed[worst_cell] - composed_solo_b,
                "worst_B_cell": worst_cell,
                "worst_B_compliance": composed[worst_cell],
                "total_margin_needed_over_calibration_solo_B":
                    composed[worst_cell] - calibration_solo_b},
            "composed_lift_on_B_by_cell": {
                cell: value - composed_solo_b
                for cell, value in sorted(composed.items())},
            "composed_lift_spread_across_companions_and_orders":
                (max(composed.values()) - min(composed.values())),
            "band_verdict": "PASS" if all(low <= v <= high
                                          for _, _, v in entries
                                          if _ != "unconstrained") else "FAIL",
            "delta_sensitivity": {
                str(delta): {
                    "margin_band": [low + delta, high - delta],
                    "flagged": [
                        {"cell": cell, "slot": slot, "compliance": value,
                         "outside_the_registered_band": not (low <= value
                                                             <= high)}
                        for cell, slot, value in sorted(entries,
                                                        key=lambda e: -e[2])
                        if slot != "unconstrained"
                        and not (low + delta <= value <= high - delta)]}
                for delta in DELTAS},
        }
    return {
        "band": list(C.COMPOSED_HEADROOM_BAND),
        "what_the_decomposition_means":
            "worst_B = calibration_solo_B(m*) + split_transfer + composition. "
            "A Gate-2.75 probe on the calibration split MEASURES the "
            "composition term with a stand-in and must BUDGET, in delta, for "
            "(a) the calibration->composed split transfer and (b) the "
            "stand-in -> selected-reference transfer.",
        "per_model": per_model,
    }


def split_transfer() -> dict:
    """Every solo slot measured twice: calibration split, then composed split.

    §13.4 admits a candidate on its **calibration** solo compliance and
    §13.14 audits the **composed** split. Both are the same quantity on the
    same instrument, so their difference is the transfer error the audit
    inherits, and it is measurable on the closed run without any new data.
    """
    observations = []
    for model_key in MODELS:
        gate2 = _record(model_key, C.STAGE_GATE2)
        gate3a = _record(model_key, C.STAGE_GATE3A)
        gate3b = _record(model_key, C.STAGE_GATE3B)
        pooled = gate3a["pooled_table"]
        rows = pooled if isinstance(pooled, list) else pooled.get("rows", [])
        calibration = {(r["kind"], r["severity"]): r["solo_compliance"]
                       for r in rows}
        slot_map = {k: (v[0], int(v[1]))
                    for k, v in (gate3b.get("slot_map") or {}).items()}
        slot_map.setdefault("A", ("A", gate2["n_star"]))
        slot_map.setdefault("B", ("B", gate2["m_star"]))
        table = _headroom_table(model_key)["table"]
        for slot, (kind, severity) in sorted(slot_map.items()):
            cell = f"solo:{slot}"
            if cell not in table:
                continue
            before = (gate2["solo_curves"][kind][str(severity)]
                      if kind in ("A", "B")
                      else calibration.get((kind, severity)))
            if before is None:
                continue
            after = table[cell][slot]
            observations.append({
                "model_key": model_key, "slot": slot,
                "instrument": f"{kind}:{severity}",
                "calibration_split_solo": before,
                "composed_split_solo": after,
                "transfer": after - before,
                "topics_calibration": C.N_CALIBRATION,
                "topics_composed": C.N_COMPOSED})
    transfers = [abs(o["transfer"]) for o in observations]
    return {
        "question": "how far does one instrument's solo compliance move "
                    "between the split it is ADMITTED on (§13.4, 192 "
                    "calibration topics) and the split it is AUDITED on "
                    "(§13.14, 24 reserved composed topics)?",
        "n_observations": len(observations),
        "max_absolute_transfer": max(transfers),
        "mean_absolute_transfer": sum(transfers) / len(transfers),
        "largest": max(observations, key=lambda o: abs(o["transfer"])),
        "caveat": "the composed split is 24 topics at M_cal draws, so part "
                  "of each transfer is sampling error at that size and part "
                  "is a real topic-set difference; this separates neither, "
                  "and reports the realised movement only.",
        "observations": observations,
    }


# ------------------------------------------------------------ what it costs

def library_and_budget() -> dict:
    """What a Tier-1 ladder extension costs, in rows, per replication."""
    from dci1v5.design.budget import calibration_burden
    from dci1v5.design.cells import n_cells_for

    burden = calibration_burden(C.N_CELLS_FULL)
    screen = burden["ladder_screen"]
    candidates = burden["candidate_calibration"]
    rows_per_rung = candidates["rows_per_rung_per_split"] * candidates["splits"]
    tier1_ladder = sum(len(LADDERS[k]) for k in TIER1_FAMILY_IDS)
    tier1_reserve = sum(len(RESERVES[k]) for k in TIER1_FAMILY_IDS)
    added = tier1_reserve - tier1_ladder
    realised = {}
    for model_key in MODELS:
        regime = _record(model_key, C.STAGE_REGIME)
        gate2 = _record(model_key, C.STAGE_GATE2)
        realised[model_key] = {
            "screened_rungs": sum(len(v) for v in
                                  regime["expansion"]["measured"].values()),
            "gate2_candidates_measured": gate2["n_candidates_measured"],
            "behavioural_rows": sum(
                sum(1 for _ in path.open())
                for stage in C.STAGE_SEQUENCE
                for path in sorted(
                    _tree(model_key).backend_runs(stage).glob("*/scored.jsonl"))
                if _tree(model_key).backend_runs(stage).exists()),
        }
    return {
        "registered_v5": {
            "tier1_round_0_ladder_rungs": tier1_ladder,
            "tier1_frozen_reserve_rungs": tier1_reserve,
            "tier1_reserve_rungs_never_measured_on_any_replication": added,
            "ladder_screen_rows": screen["rows"],
            "screen_rows_per_rung": screen["topics"] * screen["draws"],
            "candidate_calibration_population": candidates["population"],
            "candidate_calibration_rows_per_rung": rows_per_rung,
            "candidate_calibration_rows":
                candidates["rows_tier12_both_splits"]
                + candidates["rows_tier3_both_splits"],
        },
        "cost_of_measuring_the_whole_tier1_reserve_per_replication": {
            "added_rungs": added,
            "added_screen_rows": added * screen["topics"] * screen["draws"],
            "added_candidate_calibration_rows": added * rows_per_rung,
            "note": "§12.7 measures EVERY carried Tier-1/Tier-2 rung, so a "
                    "Tier-1 rung admitted at the screen is a mandatory "
                    "Gate-2 candidate; the 24-rung Tier-3 cap does not "
                    "absorb it.",
        },
        "realised_v5": realised,
        "confirmatory_by_admitted_arms": {
            "_derivation": "n_cells(arms) x N_BLOCKS x M_DRAWS, plus the §8.3 "
                           "greedy sensitivity run at GREEDY_BLOCKS x "
                           "GREEDY_DRAWS",
            "blocks": C.N_BLOCKS, "draws": C.M_DRAWS,
            "greedy_blocks": C.GREEDY_BLOCKS, "greedy_draws": C.GREEDY_DRAWS,
            "per_arm_set": {
                "+".join(arms): {
                    "cells": n_cells_for(arms),
                    "confirmatory_rows":
                        n_cells_for(arms) * C.N_BLOCKS * C.M_DRAWS,
                    "greedy_rows": n_cells_for(arms) * C.GREEDY_BLOCKS
                                   * C.GREEDY_DRAWS}
                for arms in (("base",), ("base", "class"), ("base", "core"),
                             ("base", "core", "class"), C.ARMS)},
        },
    }


def build() -> dict:
    return {
        "_what": "closed-v5 evidence for the DCI-1 v6 preregistration-"
                 "readiness memo",
        "_classification": "DEVELOPMENT_EVIDENCE",
        "_not_evidence_about": ["Delta_R", "Delta_j", "Xi",
                                "any order estimand"],
        "_reads": "signed v5 stage records (hash and signature verified on "
                  "read) and the scored rows they were computed from",
        "_v5_closure": "reports/dci1v5/CLOSURE.md",
        "expansion_reachability": expansion_reachability(),
        "span_headroom": span_headroom(),
        "composed_headroom": headroom(),
        "split_transfer": split_transfer(),
        "library_and_budget": library_and_budget(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed JSON is stale")
    args = parser.parse_args()
    built = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != built:
            print(f"{OUT} is stale; re-run without --check", file=sys.stderr)
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(built)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
