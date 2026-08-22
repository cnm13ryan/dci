#!/usr/bin/env python3
"""§34 D1: the generation budget of each registered compute option.

Every number is derived from `dci1v5`'s own constants and the arm-derived cell
set --- not from a spreadsheet and not from a hand estimate. A budget quoted
from a document that has drifted from the code is a budget for a study nobody
is running.

**The order matters and it is the researcher's.** Arms come first, because
they decide which estimands exist; claims second, because they decide which
arms are essential; models third; and the budget is what falls out. This tool
computes the last step only.

    python3 tools/v5_compute_budget.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dci1v5.design.cells import (                     # noqa: E402
    D1_ARM_SETS, D1_SCALE, n_cells_for)
from dci1v5.protocol import constants as C            # noqa: E402
from dci1v5.run.regime_run import _screen_rungs                # noqa: E402
from dci1v5.verifiers.constraints import (            # noqa: E402
    FAMILIES, FAMILY_IDS, LADDERS, RESERVES, TARGET_GRID, focal_severities)

DCI1 = Path(__file__).resolve().parents[1]
OUT = DCI1 / "reports" / "dci1v5" / "development" / "d1_compute_budget.json"


def library() -> dict[str, object]:
    tiers = {k: FAMILIES[k].structural_tier for k in FAMILY_IDS}
    out = {}
    for tier in (1, 2, 3):
        families = [k for k in FAMILY_IDS if tiers[k] == tier]
        out[f"tier_{tier}"] = {
            "families": len(families),
            "ladder_rungs": sum(len(LADDERS[k]) for k in families),
            "reserve_rungs": sum(len(RESERVES[k]) for k in families)}
    return out


def calibration_burden() -> dict[str, object]:
    """§12.2's screen, §12.3's grids and §13.7's two splits, per model.

    §34 D16 is closed at ``complete_population``: **both** splits measure the
    whole carried set, so the calibration term is doubled relative to the
    standing proposal it replaced. That is the cost the researcher accepted,
    and it is the largest single term in the pre-freeze budget.
    """
    lib = library()
    # **Round 0, not the declared range.** §12.2's screen runs
    # `registered_severities` --- the round-0 ladders --- and §12.6's
    # expansion is what may later admit a reserve rung. Costing the screen or
    # the carried set over the reserve would inflate this by roughly a factor
    # of two and would be a budget for a study nobody is running.
    carried = lib["tier_1"]["ladder_rungs"] + lib["tier_2"]["ladder_rungs"]
    screen = len(_screen_rungs())
    per_rung_per_split = C.N_CALIBRATION_A * C.M_CAL
    return {
        "ladder_screen": {
            "rungs": screen,
            "round": 0,
            "topics": C.N_PRESCREEN,
            "draws": C.LADDER_SCREEN_DRAWS,
            "rows": screen * C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS},
        "focal_grids": {
            "a_rungs": len(TARGET_GRID),
            "b_rungs": len(focal_severities(extended=True)),
            "topics": C.N_CALIBRATION_A,
            "draws": C.M_CAL,
            "rows": (len(TARGET_GRID) + len(focal_severities(extended=True)))
            * C.N_CALIBRATION_A * C.M_CAL},
        "candidate_calibration": {
            "round": 0,
            "carried_rungs_tier12": carried,
            "tier3_cap": C.CALIBRATION_TIER3_CAP,
            "rows_per_rung_per_split": per_rung_per_split,
            "splits": 2,
            "d16": "complete_population",
            "rows_tier12_both_splits": carried * per_rung_per_split * 2,
            "rows_tier3_both_splits":
                C.CALIBRATION_TIER3_CAP * per_rung_per_split * 2},
        "pilot": {"rows": C.PILOT_TOPICS * C.PILOT_DRAWS * 5},
    }


def option(name: str) -> dict[str, object]:
    arms = D1_ARM_SETS[name]
    scale = D1_SCALE[name]
    cells = n_cells_for(arms)
    per_model_confirmatory = cells * scale["blocks"] * scale["draws"]
    calibration = calibration_burden()
    per_model_calibration = (
        calibration["ladder_screen"]["rows"]
        + calibration["focal_grids"]["rows"]
        + calibration["candidate_calibration"]["rows_tier12_both_splits"]
        + calibration["candidate_calibration"]["rows_tier3_both_splits"]
        + calibration["pilot"]["rows"])
    # §13.14's composed-headroom check runs the same cell set on the composed
    # validation topics.
    gate4 = cells * C.N_COMPOSED * C.M_CAL
    # §8.3's greedy sensitivity run, one draw per cell per greedy block.
    greedy = cells * C.GREEDY_BLOCKS * C.GREEDY_DRAWS
    per_model = per_model_confirmatory + per_model_calibration + gate4 + greedy
    return {
        "arms": list(arms),
        "cells_per_block": cells,
        "models": scale["models"],
        "blocks": scale["blocks"],
        "draws_per_cell": scale["draws"],
        "per_model": {
            "calibration": per_model_calibration,
            "gate_4_composed_headroom": gate4,
            "confirmatory": per_model_confirmatory,
            "greedy_sensitivity": greedy,
            "total": per_model},
        "total_generations": per_model * scale["models"],
    }


def build() -> dict[str, object]:
    options = {name: option(name) for name in D1_ARM_SETS}
    marginal = {}
    full = tuple(C.ARMS)
    for arm in C.OPTIONAL_ARMS:
        rest = tuple(a for a in full if a != arm)
        try:
            cells = n_cells_for(rest)
            marginal[arm] = {"cells_without": cells,
                             "cells_saved": n_cells_for(full) - cells}
        except Exception as exc:                     # noqa: BLE001
            marginal[arm] = {"cells_without": None, "refused": str(exc)}
    return {
        "_what": "§34 D1's registered options, costed from the code's own "
                 "constants and the arm-derived cell set",
        "_decision": "§34 D1",
        "_units": "generations = prompt x draw; one generation is one "
                  "model response",
        "library": library(),
        "calibration": calibration_burden(),
        "cells_by_arm": dict(C.N_CELLS_BY_ARM),
        "cells_full": C.N_CELLS_FULL,
        "removing_one_arm": marginal,
        "options": options,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT} is stale; rerun without --check")
            return 1
        print(f"{OUT} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    built = json.loads(text)
    print(f"wrote {OUT}")
    for name, opt in built["options"].items():
        print(f"  {name:24s} {opt['cells_per_block']:3d} cells x "
              f"{opt['models']} models -> {opt['total_generations']:,} "
              f"generations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
