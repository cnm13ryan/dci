"""§34 D1's generation budget, derived from the constants that produce it.

**Why this is a module and not a spreadsheet.** D1 is a decision about
*compute*, and the registration manifest binds it. A budget quoted into the
manifest from a document is a number nobody can check: it agrees with the
protocol on the day it is written and drifts silently afterwards. Every term
here is computed from ``dci1v5``'s own constants and the arm-derived cell set,
so the manifest carries a figure the code reproduces on demand and a test can
fail when a constant moves under it.

**Round 0, not the declared range.** §12.2's screen measures the round-0
ladders; §12.6's expansion is what may later admit a reserve rung. Costing the
screen --- or the carried candidate set --- over the reserve would roughly
double both terms and would be a budget for a study nobody is running.

The units are **generations**: one prompt, one draw, one model response.
"""
from __future__ import annotations

from typing import Any

from dci1v5.design.cells import D1_ARM_SETS, D1_SCALE, n_cells_for
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.verifiers.constraints import (
    FAMILIES, FAMILY_IDS, LADDERS, RESERVES, TARGET_GRID, focal_severities,
    registered_severities)

__all__ = ["library", "screen_rungs", "calibration_burden", "option",
           "all_options", "registered_budget"]


def library() -> dict[str, Any]:
    """The instrument population by structural tier, round 0 and reserve."""
    tiers = {k: FAMILIES[k].structural_tier for k in FAMILY_IDS}
    out: dict[str, Any] = {}
    for tier in (1, 2, 3):
        families = [k for k in FAMILY_IDS if tiers[k] == tier]
        out[f"tier_{tier}"] = {
            "families": len(families),
            "ladder_rungs": sum(len(LADDERS[k]) for k in families),
            "reserve_rungs": sum(len(RESERVES[k]) for k in families)}
    return out


def screen_rungs() -> int:
    """How many rungs §12.2's screen measures at round 0.

    Computed the same way ``run.regime_run._screen_rungs`` builds them, from
    ``registered_severities``, so the budget and the runner cannot disagree
    about what the screen costs.
    """
    return sum(len(registered_severities(kind)) for kind in FAMILIES)


def calibration_burden(cells: int) -> dict[str, Any]:
    """§12.2's screen, §12.3's grids, §13.7's two splits and §19's pilot.

    Per model. Three of the four terms are **independent of the arm set** ---
    nothing in them runs a composed cell --- and the fourth, §19's pilot, is
    not: it runs the whole cell set, so it takes ``cells``. It was written as
    if it were arm-independent, with a literal ``5`` where the cell count
    belongs, which is how the budget came to disagree with §19.

    §34 D16 is closed at ``complete_population``, so both splits measure the
    whole carried set and the candidate term is doubled relative to the
    ``a_survivors`` proposal it replaced. That is the largest single term in
    the pre-freeze budget and it is the cost the researcher accepted to make
    §13.7 a test of the candidate landscape rather than a re-confirmation of
    it.
    """
    lib = library()
    carried = lib["tier_1"]["ladder_rungs"] + lib["tier_2"]["ladder_rungs"]
    screen = screen_rungs()
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
        # §19's pilot runs **the full cell set**, not one arm's worth: "the
        # full 56-cell plan, both orders, and the registered wording
        # allocation, at fixture values that cannot become calibration
        # evidence, with M = 4". The multiplier was 5 --- the base arm's cell
        # count --- which understated the term by 2,448 per model and the
        # study by 9,792. `run/qualification_run.pilot_payload` always built
        # the full plan, so this was the budget disagreeing with the design,
        # never the design being wrong.
        "pilot": {"rows": C.PILOT_TOPICS * C.PILOT_DRAWS * cells,
                  "topics": C.PILOT_TOPICS, "draws": C.PILOT_DRAWS,
                  "cells": cells},
    }


def option(name: str) -> dict[str, Any]:
    """One registered D1 option, costed end to end."""
    arms = D1_ARM_SETS[name]
    scale = D1_SCALE[name]
    cells = n_cells_for(arms)
    per_model_confirmatory = cells * scale["blocks"] * scale["draws"]
    calibration = calibration_burden(cells)
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


def all_options() -> dict[str, Any]:
    return {name: option(name) for name in D1_ARM_SETS}


def registered_budget() -> dict[str, Any]:
    """The adopted option, for the registration manifest. Refuses while open.

    ``decisions.choice`` carries every branch, so this cannot return a
    default: a runner that asked for the registered budget before D1 was
    closed got a refusal, not the recommendation.
    """
    costed = decisions.choice(
        "D1", {name: name for name in D1_ARM_SETS},
        where="design.budget.registered_budget")
    payload = option(costed)
    return {
        "d1_value": costed,
        "units": "generations = one prompt, one draw, one model response",
        "derived_from": "dci1v5's own constants and the arm-derived cell set",
        "order": "essential arms -> desired claims -> required models -> "
                 "budget; §34 D1's registered order and not a cost "
                 "minimisation",
        "library": library(),
        "calibration": calibration_burden(payload["cells_per_block"]),
        "cells_by_arm": dict(C.N_CELLS_BY_ARM),
        **payload,
    }
