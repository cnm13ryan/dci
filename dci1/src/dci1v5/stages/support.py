"""Gate 3C: support, the admitted arm set, and §26's success criterion.

**v4r4 calibrated to the minimum and it cost the study its primary question.**
Three of four replications finished below three core references and the fourth
had no spare. §13.15 therefore asks for more support than estimation needs:

| requirement | value |
|---|---:|
| structurally eligible Tier-1/Tier-2 families entering calibration | >= 8 |
| families passing the full V(R) on the pooled table and both splits | >= 5 |
| core references used | 3 |
| of which Tier 1 | >= 2 |
| distinct feature groups among them | 3 |
| qualifying families frozen as **unused backups** | 2 |

**The backups are not a substitution mechanism.** They exist so the support
requirement is a real requirement rather than a formality --- a replication
that qualifies exactly three families has no evidence its pool was anything
but lucky --- and so a future protocol version has a documented, pre-committed
pool. They are generated on no confirmatory block and carry no estimand, and
``selection.assert_no_backup_substitution`` is the guarantee that the path to
promote one does not exist.

**One thing here is a researcher decision and is not taken in code.** §34 D6
asks whether ``REFERENCE_SUPPORT_NOT_IDENTIFIED`` is terminal or an
identification status. §13.15's standing proposal makes it an identification
status, so a replication does not discard identified estimands --- D, Lambda,
the order contrasts, Delta_near, Delta_broad --- for want of an unidentified
one. The red team (R16) reads it the other way: three of four v4r4
replications ran a design that could not answer the primary question and each
consumed a full confirmatory budget doing so. ``support_disposition`` expresses
both and refuses until D6 is closed.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.design.cells import arms_from_identification, n_cells_for
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions

__all__ = ["support_disposition", "evaluate_support", "freeze_backups",
           "methodological_success"]


def support_disposition(*, met: bool) -> str:
    """§34 D6: what an unmet support requirement does to the replication.

    Both outcomes are expressible and neither is reachable while D6 is open.
    ``identification_status`` keeps the replication running without the core
    and spectrum arms; ``terminal`` stops it. Nothing else in this module
    reads a standing proposal.
    """
    if met:
        return "SUPPORTED"
    return decisions.choice(
        "D6",
        {"identification_status": "REFERENCE_SUPPORT_NOT_IDENTIFIED",
         "terminal": "REFERENCE_SUPPORT_NOT_IDENTIFIED_TERMINAL"},
        where="stages.support.support_disposition")


def freeze_backups(qualified_families: Sequence[str],
                   used_families: Sequence[str]) -> list[str]:
    """§13.15: the two qualifying families frozen as unused backups.

    Chosen in the registered qualification order so the choice is a function
    of the frozen rule and the frozen table, and recorded in the freeze with
    the statement that they are never substituted.
    """
    used = set(used_families)
    spare = [f for f in qualified_families if f not in used]
    return spare[:C.N_BACKUP_FAMILIES]


def evaluate_support(*, model_key: str,
                     structurally_eligible_tier12_families: Sequence[str],
                     qualified_families: Sequence[str],
                     selection: Mapping[str, Any],
                     near_form_available: bool,
                     class_available: bool,
                     spectrum_identified: bool) -> dict[str, Any]:
    """§13.15's counts, the admitted arm set, and every identification status.

    Returns a Gate-3C payload. It does **not** decide what an unmet
    requirement does: ``disposition`` is left ``UNRESOLVED`` and the caller
    reaches ``support_disposition``, which refuses while D6 is open.
    """
    core = list(selection.get("core_references", []))
    n_eligible = len(set(structurally_eligible_tier12_families))
    n_qualified = len(set(qualified_families))
    n_tier1 = sum(1 for e in core if e["structural_tier"] == 1)
    groups = {e["feature_group"] for e in core}
    used = [e["family"] for e in core]
    backups = freeze_backups(sorted(set(qualified_families)), used)

    failures: list[str] = []
    if n_eligible < C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES:
        failures.append(
            f"{n_eligible} structurally eligible Tier-1/Tier-2 families "
            f"entered calibration, against §13.15's minimum of "
            f"{C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES}")
    if n_qualified < C.MIN_QUALIFIED_FAMILIES:
        failures.append(
            f"{n_qualified} families passed the full V(R), against "
            f"§13.15's minimum of {C.MIN_QUALIFIED_FAMILIES} --- three core "
            "references plus two frozen backups")
    if len(core) != C.N_CORE_REFERENCES:
        failures.append(f"{len(core)} core references admitted, against "
                        f"{C.N_CORE_REFERENCES}")
    if n_tier1 < C.MIN_TIER1_CORE:
        failures.append(f"{n_tier1} Tier-1 core references, against "
                        f"§13.15's minimum of {C.MIN_TIER1_CORE}")
    if len(groups) != C.N_CORE_FEATURE_GROUPS and core:
        failures.append(f"{len(groups)} distinct feature groups among the "
                        f"core references, against {C.N_CORE_FEATURE_GROUPS}")
    if len(backups) < C.N_BACKUP_FAMILIES:
        failures.append(
            f"{len(backups)} qualifying families available as frozen backups, "
            f"against §13.15's {C.N_BACKUP_FAMILIES}")

    met = not failures
    core_identified = bool(core) and len(core) == C.N_CORE_REFERENCES
    arms = arms_from_identification(
        core_identified=core_identified and met,
        spectrum_identified=bool(spectrum_identified) and core_identified
        and met,
        near_form_identified=bool(near_form_available),
        class_identified=bool(class_available))

    statuses = list(selection.get("identification_statuses", []))
    if not met:
        statuses += ["REFERENCE_SUPPORT_NOT_IDENTIFIED",
                     "EXCESS_NOT_IDENTIFIED",
                     "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]
    elif not spectrum_identified:
        statuses.append("DIFFICULTY_SUPPORT_NOT_IDENTIFIED")
    if not near_form_available:
        statuses.append("NEAR_FORM_ARM_NOT_AVAILABLE")
    if not class_available:
        statuses.append("CLASS_ARM_NOT_AVAILABLE")

    return {
        "stage": C.STAGE_GATE3C, "model_key": model_key,
        "requirements": {
            "min_structurally_eligible_tier12_families":
                C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES,
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "n_core_feature_groups": C.N_CORE_FEATURE_GROUPS,
            "n_backup_families": C.N_BACKUP_FAMILIES,
            "backups_may_substitute_after_gate_4":
                C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4,
        },
        "realised": {
            "structurally_eligible_tier12_families": n_eligible,
            "qualified_families": n_qualified,
            "core_references": len(core), "tier1_core": n_tier1,
            "feature_groups": sorted(groups),
            "frozen_backups": backups,
        },
        "support_met": met, "failures": failures,
        "disposition": decisions.UNRESOLVED if not met else "SUPPORTED",
        "disposition_decision": "D6",
        "admitted_arms": list(arms),
        "derived_cell_count": n_cells_for(arms),
        "identification_statuses": sorted(set(statuses)),
        "terminal": False,
    }


def methodological_success(support: Mapping[str, Any], *,
                           gate4_passed: bool | None = None) -> dict[str, Any]:
    """§26's primary methodological success criterion.

    > Before Gate 5, v5 identifies a sufficiently redundant set of stable,
    > structurally appropriate, non-degenerate reference controls --- at least
    > five families passing the full V(R) on both calibration splits, three
    > used and two frozen --- and those controls survive Gate 4's
    > composed-headroom validation **without replacement**.

    Judged **before any confirmatory composed outcome is seen**, recorded per
    replication on the Gate-3C and Gate-4 records with the realised counts,
    and reported in the final report whether or not any L3 statement is
    emitted. It is **not** the scientific effect claim: it establishes that
    the counterfactual Delta_R requires is identified.

    ``gate4_passed`` is None before Gate 4 runs, and the criterion is then
    reported as the pre-Gate-4 half alone.
    """
    identified = bool(support.get("support_met"))
    if gate4_passed is None:
        verdict = "MET" if identified else "NOT_MET"
        stage = "pre_gate_4"
    else:
        verdict = "MET" if identified and gate4_passed else "NOT_MET"
        stage = "post_gate_4"
    if verdict not in C.SUCCESS_CRITERION_VALUES:
        raise ProtocolError(f"{verdict!r} is not a registered §26 value")
    return {
        "criterion": "§26 methodological success",
        "stage": stage, "verdict": verdict,
        "reference_support_identified": identified,
        "gate4_passed": gate4_passed,
        "realised": support.get("realised"),
        "note": "This is not the scientific effect claim. A Gate-4 failure in "
                "v5 is a finding about §13.6's interaction rule, because "
                "§13.4 and §13.6 exist to move the predictable failures "
                "earlier, and it is reported as one.",
    }
