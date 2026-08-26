"""§34 D1's generation budget, derived from the constants that produce it.

**Why this is a module and not a spreadsheet.** D1 is a decision about
*compute*, and the registration manifest binds it. A budget quoted into the
manifest from a document is a number nobody can check: it agrees with the
protocol on the day it is written and drifts silently afterwards. Every term
here is computed from ``dci1v6``'s own constants and the arm-derived cell set,
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

from dci1v4.errors import ProtocolError

from dci1v6.design.cells import D1_ARM_SETS, D1_SCALE, n_cells_for
from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions
from dci1v6.verifiers.constraints import (
    FOCAL_GRID, FAMILIES, LADDERS, PROBE_ONLY_FAMILY_IDS,
    RESERVES, SELECTABLE_FAMILY_IDS, TARGET_GRID, focal_severities,
    registered_severities)

__all__ = ["library", "screen_rungs", "expansion_burden",
           "composed_topic_plan", "probe_burden", "calibration_burden",
           "option", "all_options", "registered_budget"]


def library() -> dict[str, Any]:
    """The instrument population by structural tier, round 0 and reserve.

    Over the **selectable** pool. §34 D24's ``probe_only`` stand-ins are
    registered instruments and are hashed, certified and scored like any
    other, but they are never screened, never carried, never qualified and
    never bound, so every term below --- which costs the candidate pipeline
    --- would overstate it by counting them. They are reported separately and
    their cost is ``probe_burden``.
    """
    tiers = {k: FAMILIES[k].structural_tier for k in SELECTABLE_FAMILY_IDS}
    out: dict[str, Any] = {}
    for tier in (1, 2, 3):
        families = [k for k in SELECTABLE_FAMILY_IDS if tiers[k] == tier]
        out[f"tier_{tier}"] = {
            "families": len(families),
            "ladder_rungs": sum(len(LADDERS[k]) for k in families),
            "reserve_rungs": sum(len(RESERVES[k]) for k in families)}
    out["probe_only"] = {
        "families": len(PROBE_ONLY_FAMILY_IDS),
        "ladder_rungs": sum(len(LADDERS[k]) for k in PROBE_ONLY_FAMILY_IDS),
        "reserve_rungs": sum(len(RESERVES[k]) for k in PROBE_ONLY_FAMILY_IDS),
        "counted_in_the_candidate_pipeline": False,
        "costed_by": "design.budget.probe_burden"}
    return out


def screen_rungs() -> int:
    """How many rungs §12.2's screen measures at round 0.

    Computed the same way ``run.regime_run._screen_rungs`` builds them, from
    ``registered_severities``, so the budget and the runner cannot disagree
    about what the screen costs.

    **A's target grid and B's focal grid are part of it.** §12.2's table is
    what fixes iota_A, and §12.6 defines iota_A on the pre-screen; a screen
    that measured only the candidate families left the quantity every §12.6
    distance is taken from unmeasured, and the budget agreed with the runner
    about a screen neither of them should have had.
    """
    return (sum(len(registered_severities(kind))
                for kind in SELECTABLE_FAMILY_IDS)
            + len(C.TARGET_GRID) + len(C.FOCAL_GRID))


def expansion_burden() -> dict[str, Any]:
    """§12.6's expansion, costed --- **conditional**, and new in v6.

    v5's budget did not carry this term at all, and on v5's own records that
    was harmless for the wrong reason: the expansion measured 93 to 99 rungs
    per replication and the coverage criterion never saw one of them
    (V6-E02), so the rows were spent and bought nothing.

    Under v6's rule the expansion can reach the Tier-1 reserve §7.10 widened
    for C4's span (V6-E01), which means it can spend more and can buy
    something. Both halves are costed: the screen rows a round costs, and the
    §12.7 candidate-calibration rows a **carried Tier-1 or Tier-2** reserve
    rung then costs --- because §12.7 measures every carried Tier-1/2 rung and
    the 24-rung Tier-3 cap does not absorb them.

    It is a ceiling, not an expectation. The loop stops the moment C1-C6 pass
    and most families are skipped once they meet C4.
    """
    tier12 = [k for k in SELECTABLE_FAMILY_IDS
              if FAMILIES[k].structural_tier in (1, 2)]
    reserve_beyond_ladder = {
        k: [q for q in RESERVES[k] if q not in LADDERS[k]]
        for k in SELECTABLE_FAMILY_IDS}
    cap = (C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND
           * C.EXPANSION_MAX_ROUNDS)
    per_family_max = {k: min(cap, len(v))
                      for k, v in reserve_beyond_ladder.items()}
    max_rungs = sum(per_family_max.values())
    max_tier12_rungs = sum(per_family_max[k] for k in tier12)
    per_rung_per_split = C.N_CALIBRATION_A * C.M_CAL
    return {
        "max_rounds": C.EXPANSION_MAX_ROUNDS,
        "max_rungs_per_family_per_round":
            C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND,
        "reserve_rungs_beyond_round_0":
            sum(len(v) for v in reserve_beyond_ladder.values()),
        "max_rungs_admissible": max_rungs,
        "screen_rows_per_rung": C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS,
        "max_screen_rows": max_rungs * C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS,
        "max_tier12_rungs_admissible": max_tier12_rungs,
        "calibration_rows_per_tier12_rung": per_rung_per_split * 2,
        "max_candidate_calibration_rows":
            max_tier12_rungs * per_rung_per_split * 2,
        "is_a_ceiling": "the loop stops the moment C1-C6 pass and a family "
                        "meeting C4 is skipped; this is what §12.6 permits, "
                        "not what a replication is expected to spend",
    }


def composed_topic_plan() -> dict[str, Any]:
    """§34 D21 (READINESS R3): how many topics §13.14's verdict is taken on.

    §13.4 admits a companion on 192 calibration topics x M_cal and §13.14
    audits it on 24 reserved composed topics x M_cal --- a hard binary verdict
    against a fixed band, on 12.5% of the topics the admission decision used,
    taken over as many as 95 cell x slot entries. That is a registered design
    property and no threshold change is proposed; what is open is whether v6
    leaves the precision where v5 had it.

    **§34 D21 is an acceptance, not a selection, since 2026-08-26.** Both
    alternatives the register once offered are recorded under
    ``unimplemented_alternatives`` and cannot be closed at:

    * ``enlarge_composed_set`` was never executable. Gate 4 reads
      ``bank.topics("composed")``, which is the v4 split of ``N_COMPOSED``
      topics and is not derived from this plan, so closing there would have
      put 48 in the manifest while Gate 4 measured 24 --- and the topics do
      not exist to enlarge with: §6.2's sequestered eighth was never
      materialised in this repository.
    * ``interval_criterion`` implemented nothing. It returned the registered
      per-area count and appeared nowhere else, so a researcher closing there
      believing they had changed §13.14's criterion would have got §13.14
      exactly as registered.

    What is left is the acceptance: §13.14 stands as registered, a v6 Gate-4
    record is exactly comparable with v5's, and the precision reasoning lives
    in ``GATE_2_75``'s projection where there is no v5 counterpart to break
    comparability with.
    """
    decisions.assert_decisions_closed_for("design.budget.composed_topic_plan")
    per_area = C.COMPOSED_PER_AREA
    n_composed = per_area * C.N_AREAS
    spent = (C.N_PRESCREEN + C.N_CALIBRATION + n_composed + C.N_CONFIRMATORY)
    sequestered = C.N_TOPICS - spent
    if sequestered < 0:
        raise ProtocolError(
            f"§6.2's bank holds {C.N_TOPICS} topics and this plan spends "
            f"{spent}; enlarging the composed set takes from the sequestered "
            "reserve, and the bank is governed")
    return {"composed_per_area": per_area, "n_composed": n_composed,
            "n_sequestered": sequestered,
            "registered_n_composed": C.N_COMPOSED,
            "registered_n_sequestered": C.N_SEQUESTERED,
            "band": list(C.COMPOSED_HEADROOM_BAND),
            "band_is_unchanged": True,
            "criterion_is_unchanged": "every branch applies [0.05, 0.95]; "
                                      "only the precision it is applied at "
                                      "moves, and only under "
                                      "enlarge_composed_set"}


def probe_burden(*, n_standins: int = 3,
                 n_topics: int | None = None,
                 reuse_gate2_cells: bool = True) -> dict[str, Any]:
    """``GATE_2_75_COMPOSED_PROBE``, costed --- new in v6.

    The cell set is **derived** from ``composed_probe.probe_cell_types``
    rather than restated as a formula here, because the probe's shape is
    itself derived from Gate 4's exposure classes and a formula in the budget
    would silently stop tracking it the first time a class is added.

    Three terms:

    * the **ladder**: each stand-in's solo curve on §12.5's 24 pre-screen
      topics at ``LADDER_SCREEN_DRAWS``, measured once per replication. It
      decides only which severity each stand-in is probed at, and that
      severity is pinned to Gate 2's iota_A, so it does not depend on m* and
      is not re-measured when the operating point moves;
    * the **probed cells**, per severity, on the probe split at ``M_CAL``;
    * the cells **not** drawn, because Gate 2 measured them on the same
      topics at the same draws --- the unconstrained cell and the two
      determinate solo cells.

    **The cost is deterministic, not a ceiling.** m* is frozen at Gate 2 and
    this stage measures composed headroom at m* and at no other severity, so
    there is one severity to cost and no worst case to bound. Until
    2026-08-26 the stage could re-select m* over Gate 2's admissible set and
    this function took an ``n_severities`` argument for that; the parameter is
    gone rather than defaulted, so a caller cannot cost a search the protocol
    no longer permits.
    """
    from dci1v6.stages import composed_probe

    slots = composed_probe.probe_slots(n_standins)
    shape = composed_probe.probe_cell_types(slots)
    reused = (len(composed_probe.SHARED_WITH_GATE2) if reuse_gate2_cells
              else 0)
    topics = n_topics if n_topics is not None else C.N_CALIBRATION
    cells = len(shape)
    generated = cells - reused
    per_severity = generated * topics * C.M_CAL
    ladder_rungs = sum(len(registered_severities(kind))
                       for kind in composed_probe.PROBE_ONLY_KINDS()
                       [:n_standins])
    ladder_rows = ladder_rungs * C.N_PRESCREEN * C.LADDER_SCREEN_DRAWS
    coverage = composed_probe.probe_class_coverage(slots)
    return {
        "standins": n_standins,
        "cell_types": cells,
        "cells_read_from_gate2": reused,
        "cells_generated_per_severity": generated,
        "cells_are": "one cell per §13.14 slot-and-order exposure class: the "
                     "unconstrained cell, A and B solo, each stand-in solo, "
                     "both orders of A with B, both orders of B with each "
                     "stand-in, and both orders of the designated stand-in "
                     "with A and with a second stand-in",
        "gate4_classes_covered": sum(1 for e in coverage.values()
                                     if e["covered"] and e["roles"]),
        "gate4_entries_audited_later": sum(e["gate4_entries"]
                                           for e in coverage.values()),
        "topics": topics, "draws": C.M_CAL,
        "rows_at_the_operating_point": per_severity,
        "severities": 1,
        "ladder_rungs": ladder_rungs,
        "ladder_rows": ladder_rows,
        "ladder_topics": C.N_PRESCREEN,
        "ladder_draws": C.LADDER_SCREEN_DRAWS,
        "rows": ladder_rows + per_severity,
        "is_deterministic":
            "m* is frozen at GATE_2_FOCAL_CALIBRATION and this stage measures "
            "it and nothing else, so this is the cost and not a ceiling. A "
            "replication either spends it or terminates "
            "COMPOSED_HEADROOM_UNREACHABLE having spent it",
    }


def calibration_burden(cells: int) -> dict[str, Any]:
    """§12.2's screen, §12.3's grids, §13.7's two splits and §19's pilot.

    Per model. Three of the four terms are **independent of the arm set** ---
    nothing in them runs a composed cell --- and the fourth, §19's pilot, is
    not: it runs the whole cell set, so it takes ``cells``. It was written as
    if it were arm-independent, with a literal ``5`` where the cell count
    belongs, which is how the budget came to disagree with §19.

    §34 D16's standing proposal is ``complete_population`` --- v5's actual
    closure, restated in the register on 2026-08-26 --- so both splits measure
    the
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
        # §12.7: "plus A's grid, B's grid and the unconstrained cell", on the
        # **pooled** calibration topics --- both splits, because §34 D16 makes
        # Calibration-B measure the same set. This read one split's topic
        # count and omitted the unconstrained cell, so it understated the two
        # grids by half. `gates_run.gate2_payload` pools the two banks and
        # appends the unconstrained cell to each grid, which is what §12.7
        # registers; the budget was the side that disagreed.
        "focal_grids": {
            "a_rungs": len(TARGET_GRID),
            "b_rungs": len(FOCAL_GRID),
            "b_rungs_with_extension": len(focal_severities(extended=True)),
            "unconstrained_cell_per_grid": 1,
            "topics": C.N_CALIBRATION_A + C.N_CALIBRATION_B,
            "topics_are": "pooled: Calibration-A and Calibration-B together",
            "draws": C.M_CAL,
            "rows": (len(TARGET_GRID) + 1 + len(FOCAL_GRID) + 1)
            * (C.N_CALIBRATION_A + C.N_CALIBRATION_B) * C.M_CAL,
            # §12.3 measures {15, 16} only when the registered grid finds no
            # eligible severity, or when selection sits at the grid top. It is
            # conditional and model-adaptive, so it is named rather than
            # folded into a budget the study is expected to spend.
            "conditional_extension_rows":
                len(C.FOCAL_EXTENSION)
                * (C.N_CALIBRATION_A + C.N_CALIBRATION_B) * C.M_CAL},
        # §12.7's population: every Tier-1/2 rung plus at most 24 Tier-3. The
        # figures were right; what was missing was anything asserting that the
        # runner measured this set rather than the screen's carried set.
        # `gates_run.assert_calibration_population` is now that assertion.
        "candidate_calibration": {
            "round": 0,
            "carried_rungs_tier12": carried,
            "tier3_cap": C.CALIBRATION_TIER3_CAP,
            "population": carried + C.CALIBRATION_TIER3_CAP,
            "population_is": "§12.7: all Tier-1/2 rungs + at most 24 Tier-3, "
                             "NOT §12.2's carried set, which is high-recall "
                             "and much larger",
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
        # New in v6, and named rather than folded in. §12.6's expansion is a
        # ceiling the loop rarely reaches. The probe is NOT conditional: m*
        # is frozen at Gate 2 and the probe measures it and nothing else, so
        # what it costs is what a replication spends before it either passes
        # or terminates.
        "expansion_conditional": expansion_burden(),
        "composed_probe": probe_burden(),
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
    # validation topics. The topic count is §34 D21's, and while D21 is open
    # this falls back to the registered value **for costing only** --- a
    # budget is an estimate and never a stage.
    try:
        n_composed = composed_topic_plan()["n_composed"]
    except decisions.DecisionOpenError:
        n_composed = C.N_COMPOSED
    gate4 = cells * n_composed * C.M_CAL
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
            "gate_4_composed_topics": n_composed,
            "confirmatory": per_model_confirmatory,
            "confirmatory_derivation":
                f"{cells} cells x {scale['blocks']} blocks x "
                f"{scale['draws']} draws",
            "greedy_sensitivity": greedy,
            "total": per_model},
        # Named, not folded in. §12.6's expansion is conditional --- a
        # ceiling the loop rarely reaches. The probe is exact, because m* is
        # frozen at Gate 2 and it measures m* and nothing else.
        "conditional": {"expansion": calibration["expansion_conditional"]},
        "composed_probe": calibration["composed_probe"],
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
        "derived_from": "dci1v6's own constants and the arm-derived cell set",
        "order": "essential arms -> desired claims -> required models -> "
                 "budget; §34 D1's registered order and not a cost "
                 "minimisation",
        "library": library(),
        "calibration": calibration_burden(payload["cells_per_block"]),
        "cells_by_arm": dict(C.N_CELLS_BY_ARM),
        **payload,
    }
