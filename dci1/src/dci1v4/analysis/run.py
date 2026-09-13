"""The registered analysis, in the fixed order of §21.

The twelve steps run once, in order, and the analysis fails closed: a missing
cell, an incomplete draw set, a duplicate accepted row, a non-finite standard
error or a non-finite bound returns a named inconclusive status for the
affected quantity and computes no claim. No cell, block, constraint or draw is
dropped and no missing value is imputed. The design is fixed size: no interim
analysis, no optional stopping, no adaptive sample size.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from dci1v4.analysis import claims, diagnostics, estimators, results, variance
from dci1v4.analysis.bootstrap import (
    FamilyResult,
    assert_resample_shape,
    bootstrap_family,
)
from dci1v4.analysis.observations import (
    CONFIGURATIONS,
    ObservationTable,
    build_observations,
)
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.codebook import (
    REGISTERED_CONSUMERS,
    check_no_post_treatment_in_primary,
)
from dci1v4.protocol.seeds import BOOTSTRAP_ROOT_SEED, bootstrap_seed

#: The fields the primary formulas read. Checked against the codebook's
#: declared causal roles, so §22 is enforced from the codebook (§27 check 3).
PRIMARY_FORMULA_FIELDS = ("scores", "cell_type", "block_id", "order")


def _finite(family: FamilyResult) -> list[str]:
    bad = []
    for name, member in family.members.items():
        values = (member.estimate, member.standard_error,
                  member.simultaneous_lower, member.simultaneous_upper)
        if any(not math.isfinite(v) for v in values):
            bad.append(name)
    return bad


def analyse_configuration(table: ObservationTable, configuration: str, *,
                          model_id: str, m_draws: int,
                          root: int = BOOTSTRAP_ROOT_SEED,
                          resamples: int = C.BOOTSTRAP_RESAMPLES
                          ) -> dict[str, Any]:
    """Steps 7 to 10 of §21 for one configuration."""
    members = estimators.family_members(table, configuration)
    if "Delta_R" in members.get("F1", {}):
        estimators.assert_delta_r_forms(table, configuration)

    families: dict[str, FamilyResult] = {}
    inconclusive: dict[str, list[str]] = {}
    for family_name, vectors in sorted(members.items()):
        result = bootstrap_family(
            vectors, seed=bootstrap_seed(root, model_id, configuration,
                                         family_name),
            configuration=configuration, family=family_name,
            resamples=resamples)
        bad = _finite(result)
        if bad:
            inconclusive[family_name] = bad
        families[family_name] = result
    return {"families": families, "inconclusive": inconclusive}


def f6_gate(families: Mapping[str, FamilyResult]) -> dict[str, Any]:
    """§17.4: the F6 gate on the interpretation of the primary estimands."""
    family = families.get("F6")
    if family is None:
        return {"clean": True, "reason": "F6 not computed"}
    offending = []
    for name, member in sorted(family.members.items()):
        crosses_zero = (member.simultaneous_lower <= 0
                        <= member.simultaneous_upper)
        if abs(member.estimate) > C.F6_VACUITY_GATE and not crosses_zero:
            offending.append({"member": name, "estimate": member.estimate,
                              "lower": member.simultaneous_lower,
                              "upper": member.simultaneous_upper})
    return {
        "clean": not offending,
        "threshold": C.F6_VACUITY_GATE,
        "offending": offending,
        "block": (None if not offending else
                  "composition changed how often the outcome constraint could "
                  "bind; the primary estimands are reported with the F5 "
                  "vacuity-forced recomputation beside them as partial-"
                  "identification bounds (§17.4)"),
    }


def emit_claims(families: Mapping[str, FamilyResult], configuration: str, *,
                context: claims.ClaimContext,
                solo_headroom: Mapping[str, bool]) -> list[claims.Statement]:
    """Step 11 of §21: the claim ladder through the guarded emitters."""
    primary = families[C.PRIMARY_FAMILY].members
    outcome_position = 1 if configuration == "outcome_first" else 2
    emitted: list[claims.Statement] = []

    l1_ba = claims.emit_l1(
        "D(B<-A)", primary["D(B<-A)"], context, outcome="B", companion="A",
        outcome_position=outcome_position,
        has_solo_headroom=solo_headroom.get("B", False))
    l1_ab = claims.emit_l1(
        "D(A<-B)", primary["D(A<-B)"], context, outcome="A", companion="B",
        outcome_position=outcome_position,
        has_solo_headroom=solo_headroom.get("A", False))
    emitted += [s for s in (l1_ba, l1_ab) if s is not None]

    l2 = claims.emit_l2(primary["Lambda"], context,
                        l1_both_sides=bool(l1_ba and l1_ab),
                        outcome_position=outcome_position)
    if l2 is not None:
        emitted.append(l2)

    if "Delta_R" in primary:
        l3 = claims.emit_l3(primary["Delta_R"], context,
                            outcome_position=outcome_position)
        if l3 is not None:
            emitted.append(l3)
    return emitted


def alternative_rule_recomputation(rows: Sequence[Mapping[str, Any]], *,
                                   model_id: str, m_draws: int,
                                   resamples: int = 1000) -> dict[str, Any]:
    """§23: the primary estimands recomputed under S1, S2 and S3 for the
    A-side outcome.

    The alternatives never redefine X_A (§9.2): the stored verdict stays S0's
    and the recomputation rebuilds cell means from the recorded alternative
    counts. Robustness family only; no claim reads it.
    """
    out: dict[str, Any] = {}
    for rule in ("s1", "s2", "s3"):
        table = ObservationTable(build_observations(rows, m_draws=m_draws,
                                                    exact_count_rule=rule))
        per_configuration = {}
        for configuration in CONFIGURATIONS:
            members = {
                "D(A<-B)": estimators.delivery_loss(table, "A", "B",
                                                    configuration),
            }
            references = estimators.reference_slots(table)
            if len(references) == C.N_FINAL_REFERENCES:
                members["Delta^A"] = estimators.delta_a(table, configuration)
            per_configuration[configuration] = bootstrap_family(
                members, seed=bootstrap_seed(BOOTSTRAP_ROOT_SEED, model_id,
                                             configuration, f"S:{rule}"),
                configuration=configuration, family=f"robustness:{rule}",
                resamples=resamples)
        out[rule] = {cfg: {name: vars(member) for name, member
                           in result.members.items()}
                     for cfg, result in per_configuration.items()}
    return {"rules": out,
            "status": ("robustness family only; S1-S3 never redefine X_A "
                       "and support no claim (§9.2, §23)")}


def run_analysis(rows: Sequence[Mapping[str, Any]], *, model_key: str,
                 model_id: str, m_draws: int, measurement_basis: str,
                 identification_status: Sequence[str] = (),
                 expected_blocks: int | None = None,
                 resamples: int = C.BOOTSTRAP_RESAMPLES,
                 cells_per_block: int = C.N_CELLS_FULL) -> dict[str, Any]:
    """The whole registered analysis, in the §21 order."""
    check_no_post_treatment_in_primary(PRIMARY_FORMULA_FIELDS)

    # Steps 3-5: the complete matrix, cell means over all M draws.
    observations = build_observations(rows, m_draws=m_draws)
    table = ObservationTable(observations)
    within_block = table.assert_within_block(expected_blocks=expected_blocks)
    shape = assert_resample_shape(table, resamples=resamples,
                                  expected_blocks=expected_blocks)

    # Step 6: per-cell summaries.
    per_cell = summarise_cells(observations)

    # Steps 7-10, per configuration.
    per_configuration: dict[str, Any] = {}
    for configuration in CONFIGURATIONS:
        outcome = analyse_configuration(table, configuration,
                                        model_id=model_id, m_draws=m_draws,
                                        resamples=resamples)
        outcome["f6_gate"] = f6_gate(outcome["families"])
        per_configuration[configuration] = outcome

    # §23 secondaries that do not need unmasking. The joint-state quantities
    # and their redistribution are step 12 and belong to the unmasked phase.
    secondary = {
        "accidental_compliance": diagnostics.accidental_compliance(rows),
        "response_length_mediator": diagnostics.length_strata_description(
            observations),
        "alternative_exact_count_rules": alternative_rule_recomputation(
            rows, model_id=model_id, m_draws=m_draws,
            resamples=min(resamples, 1000)),
    }

    # Step 12 belongs to the unmasked phase and is not run here.
    return {
        "secondary": secondary,
        "model_key": model_key, "model_id": model_id,
        "within_block": within_block, "resample_shape": shape,
        "per_cell": per_cell,
        "per_configuration": per_configuration,
        "measurement_basis": measurement_basis,
        "identification_status": list(identification_status),
        "scope_sentence": (None if measurement_basis == "human_validated"
                           else C.SCOPE_SENTENCE),
        "fixed_size": ("no interim analysis, no optional stopping, no "
                       "adaptive sample size (§21)"),
        "cells_per_block": cells_per_block,
    }


def summarise_cells(observations: Sequence[Any]) -> dict[str, Any]:
    """Step 6 of §21: per-cell compliance, vacuity, truncation, length and
    graded summaries, with the truncation-bound rule applied at emission."""
    grouped: dict[tuple[str, str], list[Any]] = {}
    for obs in observations:
        grouped.setdefault((obs.cell_type, obs.outcome_slot), []).append(obs)
    out: dict[str, Any] = {}
    for (cell_type, slot), members in sorted(grouped.items()):
        n = len(members)
        truncation = sum(o.truncation for o in members) / n
        compliance = sum(o.compliance for o in members) / n
        out[f"{cell_type}|{slot}"] = {
            "n_blocks": n,
            "compliance": diagnostics.bounded(
                compliance, truncation, quantity="compliance",
                cell_type=cell_type),
            "graded": sum(o.graded for o in members) / n,
            "vacuity": sum(o.vacuity for o in members) / n,
            "truncation": truncation,
            "mean_response_words": sum(o.response_words for o in members) / n,
            "processing_failures": sum(o.processing_failures
                                       for o in members),
        }
    return out


def build_result_table(analysis: Mapping[str, Any], *,
                       realised_variance: Mapping[str, float],
                       blocks: int, m_draws: int,
                       claim_levels: Mapping[str, str] | None = None
                       ) -> list[dict[str, Any]]:
    """§30: the machine-readable table every reported figure comes from."""
    claim_levels = claim_levels or {}
    preconditions = {}
    for member in C.FAMILY_MEMBERS["F1"]:
        key = ("Lambda" if member == "Lambda"
               else "Delta_R" if member == "Delta_R" else "D")
        preconditions[member] = C.PRECISION_PRECONDITIONS[key]
    for index in (1, 2, 3):
        preconditions[f"Delta_{index}"] = C.PRECISION_PRECONDITIONS["Delta_j"]

    detectable = {}
    phi = realised_variance.get("phi", C.PHI_PRIMARY)
    for member in C.FAMILY_MEMBERS["F1"]:
        key = ("Lambda" if member == "Lambda"
               else "Delta_R" if member == "Delta_R" else "D")
        detectable[member] = variance.detectable_effect(blocks, m_draws, key,
                                                        phi=phi)

    rows: list[dict[str, Any]] = []
    for configuration, outcome in sorted(
            analysis["per_configuration"].items()):
        rows += results.result_rows(
            analysis["model_key"], outcome["families"],
            claim_levels=claim_levels,
            identification_status=analysis["identification_status"],
            measurement_basis=analysis["measurement_basis"],
            precision_preconditions=preconditions,
            variance=realised_variance, detectable=detectable,
            cells_per_block=analysis["cells_per_block"], blocks=blocks,
            draws_per_cell=m_draws,
            scope_sentence=analysis["scope_sentence"])
    results.assert_table_complete(rows)
    return rows
