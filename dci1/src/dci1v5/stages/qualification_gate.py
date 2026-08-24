"""Gate 2.5: candidate qualification (§18 stage 7, §13).

**A new stage, and the reason it exists is a data dependency.** kappa(R|B)
requires m*, so V_inter cannot be evaluated before Gate 2 selects the
operating point; and every later stage needs to know which candidates are
still live before it spends a calibration generation on them. v4r4 had one
Gate 3 doing four jobs at once and no record of why any candidate was gone.

This stage evaluates V_spec, V_sat, V_head, V_chance, V_struct and V_inter on
the **pooled** calibration table and writes the qualified pool with **every
candidate's earliest failing component**. V_stab needs the two split tables
and V_diff needs the comparison against A at the admitted operating point, so
neither is evaluated here and both are recorded as unevaluated rather than as
passes.

**It is not terminal and it may write an empty pool.** An empty qualified pool
is a measurement about the library on that model, and §13.15's
``REFERENCE_SUPPORT_NOT_IDENTIFIED`` is where it becomes a design-time
identification status --- at Gate 3C, on a signed record, not here.

It needs **no generation**. Everything it reads was scored under §9.1's
presence rule on rows Gate 2 already produced, which is what makes §13.6 free.
"""
from __future__ import annotations

from typing import Any, Sequence

from dci1v5.protocol import constants as C
from dci1v5.protocol.taxonomy import SLOT_CORE
from dci1v5.stages.calibration_table import CalibrationRow
from dci1v5.stages.validity import (GATE_2_5_COMPONENTS,
                                    assert_lexicographic_order,
                                    evaluate_validity)
from dci1v5.verifiers.constraints import FAMILIES, family_tier

__all__ = ["qualify_candidates", "QUALIFICATION_COMPONENTS"]

QUALIFICATION_COMPONENTS = GATE_2_5_COMPONENTS


def _slot_for(kind: str) -> str:
    """The slot a candidate is *considered* for at Gate 2.5.

    A Tier-3 family can only ever fill the broad-class slot, so evaluating it
    against the core slot would reject every one of them on V_struct and hide
    whatever else was wrong. Each candidate is therefore evaluated against the
    most permissive slot its own tier admits, and §13.8/§13.9/§13.10 apply the
    slot-specific rule where the slot is actually being filled.
    """
    from dci1v5.protocol.taxonomy import (SLOT_BROAD_CLASS, TIER_1, TIER_2)
    tier = family_tier(kind)
    if tier in (TIER_1, TIER_2):
        return SLOT_CORE
    return SLOT_BROAD_CLASS


def qualify_candidates(rows: Sequence[CalibrationRow], *, model_key: str,
                       m_star: int, producing_commit: str = "",
                       ) -> dict[str, Any]:
    """§18 stage 7's payload: the qualified pool and every rejection reason."""
    verdicts = []
    for row in rows:
        slot = _slot_for(row.kind)
        validity = evaluate_validity(
            row, slot=slot, components=QUALIFICATION_COMPONENTS,
            provenance={"stage": C.STAGE_GATE2_5, "m_star": m_star,
                        "producing_commit": producing_commit})
        # §19 test 3: the recorded reason is the EARLIEST failing component,
        # checked on the object rather than on the algorithm. The check was
        # implemented and called from tests only, so the production path
        # recorded a first-failing component nothing verified.
        assert_lexicographic_order(validity)
        selected = [c for c in validity.components
                    if c.name in QUALIFICATION_COMPONENTS]
        passed = all(c.passed for c in selected)
        first_failing = next((c.name for c in selected if c.passed is False),
                             None)
        verdicts.append({
            "candidate": row.label, "family": row.kind,
            "severity": row.severity, "slot_considered": slot,
            "structural_tier": row.structural_tier,
            "feature_group": row.feature_group,
            "discourse_role": row.discourse_role,
            "constraint_class": row.constraint_class,
            "passed": passed,
            "first_failing_component": first_failing,
            "reason": next((c.reason for c in selected
                            if c.name == first_failing), None),
            "components": [c.as_dict() for c in selected],
            "iota": row.iota, "solo_compliance": row.solo_compliance,
            "chance_compliance": row.chance_compliance,
            "instruction_lift": row.lift,
            "kappa_under_b": row.kappa_under_b,
            "displacement": row.displacement,
            "projected_compliance": row.projected_compliance,
        })
    qualified = [v for v in verdicts if v["passed"]]
    families = sorted({v["family"] for v in qualified})
    tier12 = sorted({f for f in families
                     if FAMILIES[f].structural_tier in (1, 2)})
    by_component: dict[str, int] = {}
    for v in verdicts:
        if v["first_failing_component"]:
            by_component[v["first_failing_component"]] = \
                by_component.get(v["first_failing_component"], 0) + 1
    return {
        "stage": C.STAGE_GATE2_5,
        "model_key": model_key, "m_star": m_star,
        "components_evaluated": list(QUALIFICATION_COMPONENTS),
        "components_not_evaluated":
            [c for c in C.VALIDITY_COMPONENTS
             if c not in QUALIFICATION_COMPONENTS],
        "n_candidates": len(verdicts), "n_qualified": len(qualified),
        "qualified_pool": [v["candidate"] for v in qualified],
        "qualified_families": families,
        "qualified_tier12_families": tier12,
        "rejections_by_first_failing_component": by_component,
        "verdicts": verdicts,
        "terminal": False,
        "note": "Gate 2.5 is not terminal and may write an empty pool. "
                "§13.15's REFERENCE_SUPPORT_NOT_IDENTIFIED is written at "
                "Gate 3C, on a signed record, and not here.",
    }
