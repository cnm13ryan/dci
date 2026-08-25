#!/usr/bin/env python3
"""Replay §12.6's expansion, v5's rule beside v6's, on the closed v5 tables.

    python3 tools/v6_expansion_dryrun.py [--check]

**What this is.** ``dci1/reports/dci1v6/READINESS.md` §7 step 2 asks for a
dry-run expansion replay, so that the development measurement in step 3 is a
report over an existing screen table rather than a second run. This is that
replay, and it is also the durable evidence for the two defects the v6
implementation repairs:

* **V6-E01** --- §12.6's expansion could not reach the Tier-1 reserve §7.10
  widened for C4's within-family span. On all four signed v5 pre-screen
  tables, in either round, v5's rule admits **zero** Tier-1 reserve rungs.
* **V6-E02** --- ``run_expansion`` extended its working table with raw
  ``difficulty_table`` rows, which carry no ``eligible`` field.
  ``coverage_criterion`` filters on ``eligible`` first, so **every rung the
  expansion measured was invisible to the criterion it was measured to
  satisfy**. Three v5 replications measured 93 to 99 reserve rungs across two
  rounds and their recorded coverage was computed over the round-0 set every
  time.

**Classification: DEVELOPMENT_EVIDENCE, and nothing here re-opens v5.** No v5
record is written, mutated or re-verdicted; D6 is irreversible and the four
terminal outcomes stand exactly as signed. The recomputations below are
validated against the signed records before anything else is reported: the
*pre-expansion* coverage recomputation must reproduce each signed
``expansion.coverage`` exactly, and the run aborts if it does not.

**What this may not be read as.** v6's rule selects severities whose
compliance nobody has measured. Whether an admitted rung lands inside
``p_solo in [0.10, 0.90]`` and whether it moves a family's span is **not
knowable from closed v5 data** --- that is the measurement READINESS §7 step 3
specifies and the researcher has not authorised. This file therefore reports
*reachability*, never survival, and makes no claim that either repair would
have changed any v5 replication's outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v5.engine import context as v5ctx                   # noqa: E402
from dci1v5.engine import transitions as v5tx                # noqa: E402
from dci1v5.engine.paths import model_tree                   # noqa: E402
from dci1v5.protocol import constants as C5                  # noqa: E402
from dci1v5.stages import regime as v5regime                 # noqa: E402
from dci1v6.stages import regime as v6regime                 # noqa: E402
from dci1v6.verifiers.constraints import (                   # noqa: E402
    LADDERS, RESERVES, TIER1_FAMILY_IDS)

OUT = DCI1 / "reports" / "dci1v6" / "expansion_dryrun.json"
MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")


def _record(model_key: str) -> dict:
    """The signed v5 regime record. Hash and signature verified on read."""
    tree = model_tree(v5ctx.registered_context(), model_key)
    return v5tx.read_stage_record(tree, C5.STAGE_REGIME)


def _prescreen_rows(record: dict) -> tuple[list[dict], list[dict]]:
    """The round-0 table and the full measured table, in criterion shape.

    The round-0 table is the full ``difficulty_table`` minus every rung a
    recorded expansion round admitted, which is exactly what v5's coverage
    criterion saw. Both are joined through ``coverage_rows`` so the criterion
    reads the fields it declares.
    """
    admitted = {(family, q)
                for rnd in record["expansion"]["rounds"]
                for family, severities in rnd.get("admitted", {}).items()
                for q in severities}
    table = record["difficulty_table"]
    round0 = [row for row in table
              if (row.get("family"), row.get("severity")) not in admitted]
    carried = record["carried_set"]
    formulation = record["coverage_eligibility_formulation"]
    return (v5regime.coverage_rows(round0, carried, formulation=formulation),
            v5regime.coverage_rows(table, carried, formulation=formulation))


def replay(model_key: str) -> dict:
    record = _record(model_key)
    iota_a = record["iota_a_prescreen"]
    round0_rows, full_rows = _prescreen_rows(record)
    signed = record["expansion"]["coverage"]

    # ---- validation: the round-0 recomputation must reproduce the signature
    recomputed = v5regime.coverage_criterion(round0_rows, iota_a=iota_a)
    agrees = (recomputed["conditions"] == signed["conditions"]
              and recomputed["realised"]["n_eligible"]
              == signed["realised"]["n_eligible"])
    if not agrees:
        raise SystemExit(
            f"{model_key}: the round-0 coverage recomputation disagrees with "
            f"the signed record ({recomputed['realised']['n_eligible']} vs "
            f"{signed['realised']['n_eligible']} eligible rungs); refusing to "
            "report a replay whose baseline does not reproduce")

    measured = {family: list(rungs) for family, rungs in LADDERS.items()}
    old = v5regime.expansion_round(round0_rows, iota_a=iota_a,
                                   measured=measured)
    new = v6regime.expansion_round(round0_rows, iota_a=iota_a,
                                   measured=measured)

    # ---- V6-E02: what the criterion saw, against what was measured
    full = v5regime.coverage_criterion(full_rows, iota_a=iota_a)
    dropped = (full["realised"]["n_eligible"]
               - signed["realised"]["n_eligible"])

    def tier1(plan: dict) -> dict:
        return {k: v for k, v in plan["admitted"].items()
                if k in TIER1_FAMILY_IDS}

    return {
        "iota_a_prescreen": iota_a,
        "signed": {
            "rounds": len(record["expansion"]["rounds"]),
            "rungs_measured_by_expansion": sum(
                rnd.get("n_rungs", 0)
                for rnd in record["expansion"]["rounds"]),
            "conditions": signed["conditions"],
            "decisive_met": signed["decisive_met"],
            "n_eligible": signed["realised"]["n_eligible"],
            "straddling_groups": len(signed["realised"]
                                     ["straddling_groups"])},
        "baseline_reproduces_signed_record": True,
        "v6_e01_reachability": {
            "v5_rule": {"n_rungs": old["n_rungs"],
                        "tier1_reserve_admitted": tier1(old)},
            "v6_rule": {"n_rungs": new["n_rungs"],
                        "tier1_reserve_admitted": tier1(new),
                        "by_deficiency": new["by_deficiency"]},
            "tier1_reserve_reachable_under_v6_rule":
                bool(tier1(new))},
        "v6_e02_criterion_blindness": {
            "eligible_rungs_the_criterion_used": signed["realised"]
                                                       ["n_eligible"],
            "eligible_rungs_actually_measured": full["realised"]
                                                    ["n_eligible"],
            "measured_rungs_the_criterion_never_saw": dropped,
            "conditions_over_the_full_measured_table": full["conditions"],
            "decisive_met_over_the_full_measured_table":
                full["decisive_met"],
            "straddling_groups_over_the_full_measured_table":
                len(full["realised"]["straddling_groups"])},
    }


def build() -> dict:
    per_model = {model_key: replay(model_key) for model_key in MODELS}
    e01_reached_under_v5 = any(
        m["v6_e01_reachability"]["v5_rule"]["tier1_reserve_admitted"]
        for m in per_model.values())
    e01_reached_under_v6 = all(
        m["v6_e01_reachability"]["tier1_reserve_reachable_under_v6_rule"]
        for m in per_model.values())
    e02_moved = sorted(
        k for k, m in per_model.items()
        if m["v6_e02_criterion_blindness"][
            "decisive_met_over_the_full_measured_table"]
        != m["signed"]["decisive_met"])
    return {
        "_what": "§12.6's expansion replayed under v5's rule and v6's, on "
                 "the four signed v5 pre-screen tables",
        "_classification": "DEVELOPMENT_EVIDENCE",
        "_not_evidence_about": ["Delta_R", "Delta_j", "Xi",
                                "any v5 replication's verdict",
                                "whether an admitted rung is eligible or "
                                "moves a span, which nobody has measured"],
        "_v5_is_unchanged": (
            "no v5 record is written, mutated or re-verdicted here; D6 is "
            "irreversible and the four terminal outcomes stand as signed. "
            "The recomputations are validated against those records before "
            "anything is reported"),
        "_generated_by": "dci1/tools/v6_expansion_dryrun.py",
        "tier1_reserve_rungs_per_family": [
            q for q in RESERVES["MK1"] if q not in LADDERS["MK1"]],
        "v6_e01": {
            "finding": "§12.6's expansion admitted no Tier-1 reserve rung on "
                       "any replication under v5's rule, and admits them on "
                       "every replication under v6's",
            "reachable_under_v5_rule": e01_reached_under_v5,
            "reachable_under_v6_rule_on_every_replication":
                e01_reached_under_v6,
            "why_v5_could_not": (
                "a straddling family took the bracketing branch, whose picks "
                "lie strictly between two adjacent measured edges with every "
                "intervening rung already in the round-0 ladder; a one-sided "
                "family was one-sided BELOW, so the rule went easier while "
                "the unmeasured reserve was harder; and interpolation cannot "
                "raise a span at all, which is the condition three "
                "replications failed"),
            "what_v6_changes": (
                "the deficiency is C4's own first unmet condition, and a "
                "SPAN_SHORT deficiency extends outward from both extremes --- "
                "the only direction that can raise max(iota) - min(iota)")},
        "v6_e02": {
            "finding": "run_expansion extended its working table with raw "
                       "difficulty rows carrying no `eligible` field, so "
                       "every rung the expansion measured was counted as "
                       "ineligible by the criterion it was measured to "
                       "satisfy",
            "replications_whose_decisive_verdict_differs_over_the_full_"
            "measured_table": e02_moved,
            "standing_of_that_difference": (
                "DEVELOPMENT_EVIDENCE about the v5 implementation. It is NOT "
                "a re-verdict: v5's recorded coverage is what v5's "
                "registered code computed, D6 is irreversible, and no v5 "
                "replication is re-run, repaired or re-read as identified. "
                "It is reported because v6 must not repeat the defect and "
                "because it narrows the diagnosis further"),
            "what_v6_changes": (
                "`measure` returns rows in the criterion's shape and "
                "`assert_coverage_shape` refuses any other, on the mandatory "
                "path")},
        "per_model": per_model,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed report is stale")
    args = parser.parse_args()
    payload = build()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; re-run without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
