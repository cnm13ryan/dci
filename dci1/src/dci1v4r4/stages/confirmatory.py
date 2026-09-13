"""The confirmatory plan, and what licenses it (§8.4, §14.2, §16.2, §21).

Generation is licensed by a **valid freeze and nothing else**. The plan is
derived from the freeze record --- design variant, slot map, block list, M,
cap, decoding, model revision, verifier hash --- so a plan cannot describe a
study the freeze did not bind. `assert_generation_licensed` is the one door.

**Completeness is the acceptance rule, not a target.** §14.2 forms a cell mean
over exactly M accepted draws or not at all, so a plan is complete only when
every (block, cell, draw) identity is present exactly once. `missing_rows`
returns what is absent; nothing in this module can drop, replace, impute or
select a draw, and `assert_no_selective_rerun` refuses a resume whose row set
is not the plan's own.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r4.design.cells import cell_types
from dci1v4r4.protocol import constants as C

__all__ = ["DESIGN_VARIANTS", "confirmatory_plan", "expected_row_ids",
           "missing_rows", "assert_generation_licensed",
           "assert_no_selective_rerun", "assert_plan_matches_freeze",
           "allocation_report"]

#: variant -> (reduced, class_arm, spectrum) for `design.cells`.
DESIGN_VARIANTS = {
    "full": (False, True, True),
    "no_spectrum": (False, True, False),
    "reduced": (True, True, True),
}


def _variant_args(variant: str) -> tuple[bool, bool, bool]:
    try:
        return DESIGN_VARIANTS[variant]
    except KeyError:
        raise ProtocolError(
            f"{variant!r} is not a registered §8.6 design variant; "
            f"registered: {tuple(DESIGN_VARIANTS)}") from None


def assert_generation_licensed(freeze_record: Mapping[str, Any] | None
                               ) -> Mapping[str, Any]:
    """§21: no confirmatory generation without a valid freeze."""
    if not freeze_record:
        raise IntegrityError(
            "confirmatory generation requires a valid Gate 5 freeze; none "
            "exists, and a run without one produces evidence no registered "
            "analysis may read")
    if freeze_record.get("outcome") != "PASS":
        raise IntegrityError(
            f"the freeze record reports {freeze_record.get('outcome')!r}, not "
            f"PASS; generation is not licensed")
    # `canonical_verifier_hash`, which is the name §18.1 registers and the
    # name `freeze_run.assemble` writes. This list asked for
    # `verifier_source_hash` --- the name of the *function* that computes it,
    # and of no freeze field --- so `assert_generation_licensed` refused every
    # valid freeze record and no confirmatory generation was licensable on any
    # replication. The path had never run.
    missing = [field for field in
               ("design_variant", "slot_map", "blocks", "m_draws",
                "completion_cap", "model_revision", "canonical_verifier_hash",
                "producing_commit")
               if field not in freeze_record]
    if missing:
        raise IntegrityError(
            f"the freeze record is missing {missing}; the plan would not be "
            f"derivable from what the freeze bound")
    return freeze_record


def confirmatory_plan(freeze_record: Mapping[str, Any]) -> dict[str, Any]:
    """The plan, derived entirely from the freeze."""
    freeze = assert_generation_licensed(freeze_record)
    variant = freeze["design_variant"]
    reduced, class_arm, spectrum = _variant_args(variant)
    types = cell_types(reduced=reduced, class_arm=class_arm,
                       spectrum=spectrum)
    blocks = list(freeze["blocks"])
    m = int(freeze["m_draws"])
    slot_map = dict(freeze["slot_map"])

    unknown = [t for t in types for s in t.slots if s not in slot_map]
    if unknown:
        raise IntegrityError(
            f"the {variant} design needs slots the freeze's slot map does not "
            f"bind: {sorted({s for t in unknown for s in t.slots})}")

    return {
        "design_variant": variant,
        "cells_per_block": len(types),
        "blocks": len(blocks),
        "m_draws": m,
        "generations": len(blocks) * len(types) * m,
        "orders": C.N_ORDERS,
        "slot_map": slot_map,
        "completion_cap": freeze["completion_cap"],
        "model_revision": freeze["model_revision"],
        "canonical_verifier_hash": freeze["canonical_verifier_hash"],
        "producing_commit": freeze["producing_commit"],
        "cell_ids": [t.cell_id for t in types],
        "row_identities": len(blocks) * len(types) * m,
    }


def expected_row_ids(freeze_record: Mapping[str, Any]) -> list[str]:
    """Every registered (block, cell, draw) identity, exactly once."""
    freeze = assert_generation_licensed(freeze_record)
    reduced, class_arm, spectrum = _variant_args(freeze["design_variant"])
    types = cell_types(reduced=reduced, class_arm=class_arm,
                       spectrum=spectrum)
    m = int(freeze["m_draws"])
    return [f"{block}|{t.cell_id}|{draw}"
            for block in freeze["blocks"] for t in types for draw in range(m)]


def missing_rows(freeze_record: Mapping[str, Any],
                 rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """What the plan still owes. A partial cell is never completed by an
    imputed draw (§14.2), so this is a work list, not a repair."""
    expected = expected_row_ids(freeze_record)
    present: dict[str, int] = {}
    for row in rows:
        key = f"{row['block_id']}|{row['cell_id']}|{row['draw_index']}"
        present[key] = present.get(key, 0) + 1
    absent = [k for k in expected if k not in present]
    duplicated = sorted(k for k, n in present.items() if n > 1)
    unexpected = sorted(set(present) - set(expected))
    return {"expected": len(expected), "present": len(present),
            "missing": len(absent), "first_missing": absent[:8],
            "duplicated": len(duplicated), "first_duplicated": duplicated[:8],
            "unexpected": len(unexpected), "first_unexpected": unexpected[:8],
            "complete": not absent and not duplicated and not unexpected}


def assert_no_selective_rerun(freeze_record: Mapping[str, Any],
                              rows: Sequence[Mapping[str, Any]]) -> None:
    """§21: the row set is the plan's own, whole, and with nothing extra.

    A rerun of chosen cells would show up here as `unexpected` (a row the plan
    does not contain) or as `duplicated` (a row generated twice and one copy
    kept). Both refuse.
    """
    report = missing_rows(freeze_record, rows)
    if report["duplicated"] or report["unexpected"]:
        raise IntegrityError(
            f"the confirmatory row set is not the plan's own: "
            f"{report['duplicated']} duplicated identity(ies) and "
            f"{report['unexpected']} not in the plan. Draws are never "
            f"selected, replaced or re-run cell by cell (§21); first "
            f"duplicated {report['first_duplicated'][:3]}, first unexpected "
            f"{report['first_unexpected'][:3]}")


def assert_plan_matches_freeze(plan: Mapping[str, Any],
                               freeze_record: Mapping[str, Any]) -> None:
    """Nothing the freeze bound may differ in the plan that runs."""
    drift = {field: (plan.get(field), freeze_record.get(field))
             for field in ("design_variant", "m_draws", "completion_cap",
                           "model_revision", "canonical_verifier_hash",
                           "producing_commit")
             if plan.get(field) != freeze_record.get(field)}
    if drift:
        raise IntegrityError(
            f"the confirmatory plan differs from the freeze in {sorted(drift)}"
            f": {drift}. After Gate 5 a scientific change requires a new "
            f"protocol revision, not a different plan")


def allocation_report(per_model: Mapping[str, str], *, blocks: int,
                      m_draws: int) -> dict[str, Any]:
    """§16.2's budget, recomputed from the ACTUAL per-model design variants."""
    rows: dict[str, Any] = {}
    total = 0
    for model_key, variant in sorted(per_model.items()):
        reduced, class_arm, spectrum = _variant_args(variant)
        cells = len(cell_types(reduced=reduced, class_arm=class_arm,
                               spectrum=spectrum))
        generations = blocks * cells * m_draws
        total += generations
        rows[model_key] = {"design_variant": variant, "cells_per_block": cells,
                           "blocks": blocks, "m_draws": m_draws,
                           "generations": generations}
    return {"per_model": rows, "total_generations": total,
            "blocks": blocks, "m_draws": m_draws,
            "note": ("recomputed from the Gate 3 design variants actually in "
                     "force, never from an earlier planning estimate")}
