"""The fixed-order analysis (prereg §20), fail-closed.

Order: load and integrity-check rows → assert the complete block × arm matrix
→ score S0 (and declared alternatives) → §16 checks → block contrasts →
stratified 10,000-resample block bootstrap → simultaneous intervals per
family → claim rules with interpretation and bounding rules. A missing cell,
duplicate accepted response, non-finite standard error or non-finite bound
yields a named inconclusive status and computes no claim; no cell is dropped
or averaged around.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from dci1.analysis import checks as check_rules
from dci1.analysis import claims as claim_rules
from dci1.analysis.bootstrap import family_intervals, run_bootstrap
from dci1.analysis.estimators import assert_block_indexed_signatures
from dci1.analysis.families import (
    CHECK_FAMILIES,
    SECONDARY_MARGINAL,
    assemble_stats,
    family_members,
)
from dci1.analysis.precision import (
    discordance,
    marginal_detectable,
    simultaneous_detectable,
    uninformative_share,
)
from dci1.analysis.tables import score_table
from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST, Block
from dci1.protocol.constants import BOOTSTRAP_RESAMPLES, ProtocolError


def analyze(accepted_rows: list[dict[str, Any]], blocks: list[Block], *,
            n: int, m: int, references: tuple[str, str, str],
            bootstrap_seed_value: int,
            n_resamples: int = BOOTSTRAP_RESAMPLES,
            masked: bool = True) -> dict[str, Any]:
    """Run the §20 fixed order on one accepted table; returns the result
    tables. ``masked`` is a label only — the procedure is identical."""
    assert_block_indexed_signatures()

    # Steps 1–2: structural integrity of the matrix, fail closed by name.
    try:
        scored = score_table(accepted_rows, blocks, n=n, m=m,
                             references=references)
        assembled = assemble_stats(scored)
    except ProtocolError as error:
        return {"status": "INCONCLUSIVE_INCOMPLETE_MATRIX",
                "detail": str(error), "claims": None}
    expected = len(blocks) * 6
    if len(scored) != expected:
        return {"status": "INCONCLUSIVE_INCOMPLETE_MATRIX",
                "detail": f"{len(scored)} scored rows, expected {expected}",
                "claims": None}

    # Step 4: checks computed separately from every primary quantity.
    compliance = check_rules.compliance_flags(scored)

    # Steps 5–6: block contrasts and the stratified block bootstrap.
    result = run_bootstrap(assembled["stats"], seed=bootstrap_seed_value,
                           n_resamples=n_resamples)
    from dci1.analysis.bootstrap import add_derived

    add_derived(result, "order_interaction",
                lambda r: r[f"tau_{TARGET_FIRST}"] - r[f"tau_{ADDED_FIRST}"],
                lambda e: e[f"tau_{TARGET_FIRST}"] - e[f"tau_{ADDED_FIRST}"])

    # Step 7: simultaneous intervals within each declared family.
    families = family_members()
    family_results = {name: family_intervals(result, members)
                      for name, members in families.items()}
    check_results = {name: family_intervals(result, members)
                     for name, members in CHECK_FAMILIES.items()}
    secondary = family_intervals(
        result, [s for s in SECONDARY_MARGINAL
                 if s in result.estimates] +
        [f"area_focal_failure_{a}" for a in assembled["areas"]])

    # Precision report (§13).
    ids = assembled["ids_by_stratum"]
    blocks_map = assembled["blocks"]
    def d_column(order):
        return [blocks_map[b]["arms"]["focal"]["f_s0"] -
                (blocks_map[b]["arms"]["ref1"]["f_s0"] +
                 blocks_map[b]["arms"]["ref2"]["f_s0"] +
                 blocks_map[b]["arms"]["ref3"]["f_s0"]) / 3.0
                for b in ids[order]]
    precision = {}
    c1 = family_results["F1"].get("critical_value")
    for order in (TARGET_FIRST, ADDED_FIRST):
        column = d_column(order)
        p_d = discordance(column)
        precision[f"tau_{order}"] = {
            "realised_discordance": p_d,
            "blocks": len(column),
            "marginal_detectable": marginal_detectable(p_d, len(column)),
            "simultaneous_detectable": simultaneous_detectable(
                p_d, len(column), c1),
        }
    precision["uninformative_topic_share"] = uninformative_share(blocks_map)

    # Step 8: claim rules, interpretation blocks, bounding rules.
    exchangeable = claim_rules.exchangeability_holds(family_results["F2"])
    outcomes = {}
    for member in families["F1"]:
        entry = dict(family_results["F1"]["members"][member])
        entry["status"] = (family_results["F1"]["status"]
                           if family_results["F1"]["status"] != "OK"
                           else entry.get("status", "OK"))
        achieved = precision.get(member, {}).get("simultaneous_detectable")
        outcome = claim_rules.primary_outcome(member, entry, achieved)
        outcome["terminal"] = claim_rules.terminal_outcome(
            member, outcome, exchangeable)
        outcomes[member] = outcome

    uptake = check_rules.uptake_check(check_results["uptake_diff"])
    symmetry = check_rules.symmetry_check(family_results["F6"])
    bounds = None
    if symmetry["partial_identification_required"]:
        bounds = check_rules.partial_identification(
            scored, seed=bootstrap_seed_value + 1, n_resamples=n_resamples)

    # §16 target feasibility: solo target failure on confirmatory topics,
    # reported beside the primary estimate when outside the Gate 2 band.
    from dci1.protocol.constants import TARGET_SOLO_BAND

    solo_rate = result.estimates.get("target_alone_failure")
    feasibility = {
        "target_alone_failure": solo_rate,
        "gate2_band": list(TARGET_SOLO_BAND),
        "inside_band": (solo_rate is not None and np.isfinite(solo_rate)
                        and TARGET_SOLO_BAND[0] <= solo_rate
                        <= TARGET_SOLO_BAND[1]),
        "note": (None if solo_rate is None or
                 TARGET_SOLO_BAND[0] <= solo_rate <= TARGET_SOLO_BAND[1]
                 else "confirmatory topics differ in difficulty from the "
                      "calibration topics (§16)")}

    return {
        "status": "OK",
        "masked": masked,
        "n": n, "m": m, "references": list(references),
        "bootstrap": {"seed": bootstrap_seed_value,
                      "resamples": n_resamples},
        "families": family_results,
        "checks": {"uptake": uptake, "symmetry": symmetry,
                   "compliance": compliance, "feasibility": feasibility},
        "secondary": secondary,
        "precision": precision,
        "exchangeability_holds": exchangeable,
        "outcomes": outcomes,
        "partial_identification": bounds,
        "estimates": {k: (None if isinstance(v, float) and not np.isfinite(v)
                          else v)
                      for k, v in result.estimates.items()},
    }
