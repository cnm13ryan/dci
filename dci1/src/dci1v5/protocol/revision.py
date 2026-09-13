"""What v5 changes from v4r4, enumerated where the code can read it.

v4r4's own ``protocol/revision.py`` exists because a revision that lists its
changes only in prose has no way to check that the code made them. This one
does the same for v5, and it carries one thing v4r4's did not: the **section
each change is registered under**, so an audit can trace a code difference to
a preregistration paragraph rather than to a commit message.

Every entry here is a scientific change with an entry in
``user-notes/DCI1_v4r4_to_v5_changelog.md``. Ordinary refactors and
re-namespacing are not changes and are not listed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C

__all__ = ["Change", "CHANGES", "UNCHANGED", "assert_changes_realised",
           "revision_record"]


@dataclass(frozen=True)
class Change:
    id: str
    section: str
    what: str
    why: str
    #: A callable returning True when the code actually carries the change.
    check: Any = None


def _tier1_pool_is_production() -> bool:
    from dci1v5.verifiers.constraints import (
        CLASS_PRODUCTION, FAMILIES, TIER1_FAMILY_IDS,
    )
    return bool(TIER1_FAMILY_IDS) and all(
        FAMILIES[k].constraint_class == CLASS_PRODUCTION
        for k in TIER1_FAMILY_IDS)


def _iota_is_last() -> bool:
    return C.VALIDITY_COMPONENTS[-1] == "V_diff"


def _no_prescreen_caliper() -> bool:
    return not hasattr(C, "REFERENCE_PRESCREEN_CALIPER")


def _caliper_unchanged() -> bool:
    return C.REFERENCE_CALIPER == 0.10


def _focal_grid_widened() -> bool:
    return C.FOCAL_GRID == tuple(range(7, 15)) and C.FOCAL_EXTENSION == (15, 16)


def _l4_is_per_member() -> bool:
    import inspect

    from dci1v5.analysis import claims

    if hasattr(claims, "emit_l4"):
        return False
    signature = inspect.signature(claims.emit_l4a)
    parameter = signature.parameters.get("per_member")
    return (parameter is not None
            and parameter.kind is inspect.Parameter.KEYWORD_ONLY)


def _f11_exists() -> bool:
    return C.FAMILY_MEMBERS.get("F11") == ("Ord_A", "Ord_B", "Ord_Lambda",
                                           "Ord_Rbar", "Ord_CL")


def _arms_derive_cells() -> bool:
    from dci1v5.design import cells
    return not hasattr(cells, "VARIANT_EXEMPTIONS") and \
        cells.n_cells_for(C.ARMS) == C.N_CELLS_FULL


def _eighteen_stages() -> bool:
    return (len(C.STAGE_SEQUENCE) == 18
            and C.STAGE_SEQUENCE[0] == C.STAGE_REGISTERED
            and C.STAGE_PREFREEZE_AUDIT in C.STAGE_SEQUENCE
            and C.STAGE_FINAL_REPORT in C.STAGE_SEQUENCE)


def _interaction_gate_exists() -> bool:
    from dci1v5.stages import interaction
    return hasattr(interaction, "interaction_verdict")


def _two_splits() -> bool:
    return (C.N_CALIBRATION_A == 96 and C.N_CALIBRATION_B == 96
            and C.N_CALIBRATION == 192)


CHANGES: tuple[Change, ...] = (
    Change("C1", "§7.5",
           "the core reference pool inverts to production class and same form "
           "with A: eight exact-count marker families",
           "applied to v4r4's own measurements the full v5 stack leaves 3, 0, "
           "0 and 0 qualifying budget-class families and 4, 4, 2 and 3 "
           "production-class ones, and v4r3 §13.1's own rationale says the "
           "reference must resemble A",
           _tier1_pool_is_production),
    Change("C2", "§13.3",
           "iota is demoted from the admission coordinate to the difficulty "
           "coordinate and V_diff is evaluated LAST",
           "a rung at raw solo 0.9740 and chance 0.9323 was admitted because "
           "its iota was closest and terminated its replication on its own "
           "solo cell",
           _iota_is_last),
    Change("C3", "§12.2",
           "the pre-screen distance caliper is REMOVED and the screen becomes "
           "high recall",
           "the two stages' iota estimates disagree by a median of 0.071 and "
           "35.7% of candidates move further than the whole caliper",
           _no_prescreen_caliper),
    Change("C4", "§13.8",
           "the matching caliper does NOT move from 0.10",
           "the sample doubles instead, taking 0.10 from 2.10 to 2.96 "
           "standard errors; tightening it would select harder on noise",
           _caliper_unchanged),
    Change("C5", "§13.6",
           "a pre-composition interaction gate on kappa(R|B), displacement "
           "and the projection",
           "RF11 went 0.635 solo to 0.969 composed because B shifts the "
           "response distribution its verifier integrates over",
           _interaction_gate_exists),
    Change("C6", "§13.7",
           "two disjoint 96-topic calibration splits and an equivalence rule",
           "selection inside a two-SE window is substantially selection on "
           "noise",
           _two_splits),
    Change("C7", "§7.1, §7.2",
           "the focal grid widens to 7..14 with an extension to 15, 16, and "
           "§12.3 adds a bracketing rule",
           "m* was the last measured rung on all four v4r4 replications",
           _focal_grid_widened),
    Change("C8", "§8.1",
           "the design becomes an admitted ARM SET and the cell count is "
           "derived; VARIANT_EXEMPTIONS is deleted",
           "a named variant the code does not enumerate cannot be run, and a "
           "field a variant leaves empty should be explained by the "
           "identification status that caused it",
           _arms_derive_cells),
    Change("C9", "§11.7, §15",
           "five order contrasts in a new family F11, primary tier",
           "v4r4 measured Lambda moving from -0.110 to +0.315 across "
           "configurations and registered no contrast, so the question could "
           "not be answered afterwards either",
           _f11_exists),
    Change("C10", "§17.7",
           "emit_l4 becomes emit_l4a, per NAMED MEMBER, plus emit_l4b",
           "v4r4's emitter compared level SETS and its caller had already "
           "discarded member identity, so the emitted L4 asserted replication "
           "for the replication that least replicates",
           _l4_is_per_member),
    Change("C11", "§18",
           "twelve stages become eighteen; PREFREEZE_AUDIT and FINAL_REPORT "
           "become stages",
           "a check that runs beside the lifecycle can be skipped; a stage "
           "cannot",
           _eighteen_stages),
    Change("C12", "§9.1",
           "the presence rule is mandatory at EVERY generative stage",
           "v4r4's calibration scored load-one rows on the present instance "
           "only, so kappa(R|B) did not exist in its records"),
    Change("C13", "§13.9, §13.10",
           "a near-form arm of three Tier-2 controls, and the broad-class arm "
           "inverts to budget class",
           "one admission rule for every scientific job discovered that the "
           "job changes what valid means"),
    Change("C14", "§13.15",
           "support oversupply: five qualifying families, three used, two "
           "frozen backups that are never substituted",
           "three of four v4r4 replications finished below three core "
           "references and the fourth had no spare"),
    Change("C15", "§7.7",
           "a realistic joint-satisfiability obligation inside §8.5's stem "
           "band",
           "a formal witness certifies that a pair is not contradictory, not "
           "that it is satisfiable by a response of the length asked for"),
    Change("C16", "§34",
           "nineteen open decisions are executable state and block the "
           "stages that depend on them",
           "a draft scientific choice becomes an implementation fact the "
           "moment the code needs a value and nobody records the choice"),
)

#: What v5 deliberately does NOT change, named so a reader does not have to
#: infer it from an absence.
UNCHANGED: tuple[tuple[str, str], ...] = (
    ("§10.7", "the deterministic-measurement architecture and its ten-condition "
              "Gate-1 rule, carried unchanged in substance"),
    ("§10.5", "the measurement basis and its permanent scope sentence"),
    ("§11.9", "the memo's 0.10 and 0.25, which predate every observation in "
              "this constraint vocabulary"),
    ("§16", "384 blocks, M = 8, 10,000 resamples, and the planning constants; "
            "no v4r4 effect estimate enters the sample-size calculation"),
    ("§20", "the stratified mask, the one-shot unmask and the commitment "
            "device, including its known cost"),
    ("§13.8", "the 0.10 caliper and the 0.05 Newcombe region"),
)


def assert_changes_realised() -> dict[str, Any]:
    """Every change with a check has actually been made in the code."""
    findings: list[dict[str, Any]] = []
    unrealised: list[str] = []
    for change in CHANGES:
        realised = None
        if change.check is not None:
            realised = bool(change.check())
            if not realised:
                unrealised.append(change.id)
        findings.append({"id": change.id, "section": change.section,
                         "what": change.what, "why": change.why,
                         "checked": change.check is not None,
                         "realised": realised})
    if unrealised:
        raise ProtocolError(
            f"these registered v4r4 -> v5 changes are not present in the "
            f"code: {unrealised}")
    return {"changes": findings, "n_changes": len(CHANGES),
            "n_checked": sum(1 for c in CHANGES if c.check is not None),
            "unchanged": [{"section": s, "what": w} for s, w in UNCHANGED]}


def revision_record() -> dict[str, Any]:
    from dci1v5 import (
        CLASSIFICATION, PREREGISTRATION, STUDY_ID, SUPERSEDES,
        SUPERSEDES_TERMINAL_STAGE, SUPERSEDES_TERMINAL_STATUS,
    )

    return {"study_id": STUDY_ID, "classification": CLASSIFICATION,
            "preregistration": PREREGISTRATION, "supersedes": SUPERSEDES,
            "supersedes_terminal_stage": SUPERSEDES_TERMINAL_STAGE,
            "supersedes_terminal_status": SUPERSEDES_TERMINAL_STATUS,
            **assert_changes_realised()}
