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
both and refuses until D6 is closed. **D6 is closed at
``identification_status`` and, since v7 A6, that is what the lifecycle does:
a non-identified replication continues through the pre-freeze audit, the
freeze and confirmatory generation on its surviving arms.** Until A6 the
pre-freeze audit required ``support_met`` and made the closed value terminal
one stage later; seven replications of v5, v6 and v7 ended on it.

**v7 A7: the spectrum has its own support verdict.** §12.6's spectrum
conditions (C2, C4), §13.12's exhaustion and the calibrated re-read's
spectrum verdict cost the spectrum arm alone and record
``DIFFICULTY_SUPPORT_NOT_IDENTIFIED`` at design time, with the
spectrum-dependent estimands on their own irreversible non-identification
block. The core arm stands when §13.8, §13.7 and §13.15 hold.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v7.design.cells import arms_from_identification, n_cells_for
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, identification

__all__ = ["support_disposition", "evaluate_support", "freeze_backups",
           "methodological_success"]


def support_disposition(*, met: bool) -> str:
    """§34 D6: what an unmet support requirement does to the replication.

    **Closed at ``identification_status``**: the replication continues and
    every reference-dependent estimand becomes ``NOT_IDENTIFIED``, irreversibly
    for that replication (``protocol/identification.py``). The ``terminal``
    branch is retained and is **not** a live v5 alternative --- it is the
    behaviour v5 did not adopt, kept so a reader can see what was refused and
    so a historical replication that ran it stays reproducible.
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
                     spectrum_identified: bool,
                     design_time_failures: Sequence[str] = (),
                     spectrum_design_time_failures: Sequence[str] = ()
                     ) -> dict[str, Any]:
    """§13.15's counts, the admitted arm set, and every identification status.

    Returns a Gate-3C payload carrying the D6 disposition and, when §13.15 is
    unmet, the ``non_identification`` block naming the exact estimand set the
    replication may no longer identify. That block is what
    ``identification.assert_not_rehabilitated`` reads at the freeze, at the
    analysis and at the final report, so the status cannot be lifted later.

    v7 A7: ``design_time_failures`` are §12.6 *core* failures and join
    §13.15's own; ``spectrum_design_time_failures`` are §12.6 *spectrum*
    failures (and §13.12's exhaustion) and cost the spectrum arm alone. When
    §13.15 holds and the spectrum is lost, the block names the
    spectrum-dependent set under ``DIFFICULTY_SUPPORT_NOT_IDENTIFIED``.
    """
    core = list(selection.get("core_references", []))
    n_eligible = len(set(structurally_eligible_tier12_families))
    n_qualified = len(set(qualified_families))
    n_tier1 = sum(1 for e in core if e["structural_tier"] == 1)
    groups = {e["feature_group"] for e in core}
    used = [e["family"] for e in core]
    backups = freeze_backups(sorted(set(qualified_families)), used)

    # §12.6: a replication whose identification-coverage criterion is unmet
    # after the registered expansion rounds records
    # REFERENCE_SUPPORT_NOT_IDENTIFIED **at design time** and runs without the
    # core and spectrum arms. That verdict is reached at the regime screen,
    # two stages before any calibration count exists, so it enters here as a
    # failure rather than being re-derived from quantities that cannot see it.
    failures: list[str] = list(design_time_failures)
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
    spectrum_failures: list[str] = list(spectrum_design_time_failures)
    if not spectrum_identified and not spectrum_failures:
        spectrum_failures.append(
            "§13.12: reference selection bound no complete straddling "
            "triple, so the spectrum arm is not generated")
    spectrum_ok = (bool(spectrum_identified) and not spectrum_failures
                   and core_identified and met)
    arms = arms_from_identification(
        core_identified=core_identified and met,
        spectrum_identified=spectrum_ok,
        near_form_identified=bool(near_form_available),
        class_identified=bool(class_available))
    # §8.1: the base arm is unconditional, and the derivation above cannot
    # drop it. Asserted rather than trusted, because the closed §34 D6 rests
    # on the base arm surviving every other loss.
    if C.ARM_BASE not in arms:
        raise ProtocolError("§8.1: the base arm is always admitted")

    statuses = list(selection.get("identification_statuses", []))
    if not met:
        statuses += ["REFERENCE_SUPPORT_NOT_IDENTIFIED",
                     "EXCESS_NOT_IDENTIFIED",
                     "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"]
    elif not spectrum_ok:
        statuses.append("DIFFICULTY_SUPPORT_NOT_IDENTIFIED")
    if not near_form_available:
        statuses.append("NEAR_FORM_ARM_NOT_AVAILABLE")
    if not class_available:
        statuses.append("CLASS_ARM_NOT_AVAILABLE")

    non_identified = identification.non_identification(
        model_key=model_key, support_met=met, failures=failures,
        spectrum_identified=spectrum_ok,
        spectrum_failures=spectrum_failures)
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
        # v7 A7: the spectrum's own verdict, beside the core's.
        "spectrum_met": spectrum_ok,
        "spectrum_failures": spectrum_failures if not spectrum_ok else [],
        "disposition": support_disposition(met=met),
        "disposition_decision": "D6",
        "replication_continues": True,
        "non_identification": non_identified,
        "not_identified_members": (list(non_identified["not_identified_members"])
                                   if non_identified else []),
        "admitted_arms": list(arms),
        "derived_cell_count": n_cells_for(arms),
        "identification_statuses": sorted(set(statuses)),
        "terminal": False,
    }


def methodological_success(support: Mapping[str, Any], *,
                           gate4_contrast: Mapping[str, Any] | None = None
                           ) -> dict[str, Any]:
    """§26's primary methodological success criterion (v7 wording).

    > Before Gate 5, the study identifies a sufficiently redundant set of
    > stable, structurally appropriate, non-degenerate reference controls
    > --- at least five families passing the full V(R) on both calibration
    > splits, three used and two frozen --- and the composed contrast
    > ``Delta_R`` those controls define is **estimable** on Gate 4's composed
    > set: not a structural zero, in either configuration.

    Judged **before any confirmatory composed outcome is seen**, recorded per
    replication on the Gate-3C and Gate-4 records with the realised counts,
    and reported in the final report whether or not any L3 statement is
    emitted. It is **not** the scientific effect claim: it establishes that
    the counterfactual ``Delta_R`` requires is identified and can carry a
    nonzero value. v5's clause --- "survive Gate 4's composed-headroom
    validation without replacement" --- is withdrawn with the criterion it
    named (v7 A1); the without-replacement guarantee stands on its own as
    ``assert_no_substitution_path``.

    ``gate4_contrast`` is Gate 4's ``composed_contrast`` projection, or None
    before Gate 4 runs, in which case the pre-Gate-4 half is reported alone.
    A structural zero for ``Delta_R`` there records ``NOT_MET`` and, like
    every other v7 §13.14 reading, terminates nothing.
    """
    identified = bool(support.get("support_met"))
    if gate4_contrast is None:
        verdict = "MET" if identified else "NOT_MET"
        stage = "pre_gate_4"
        estimable = None
    else:
        estimable = True
        families = gate4_contrast.get("families") or {}
        for configuration in C.CONFIGURATIONS:
            entry = ((families.get(f"F1:{configuration}") or {})
                     .get("members") or {}).get("Delta_R")
            reading = (entry or {}).get("boundary") or {}
            if entry is None or reading.get("structural_zero"):
                estimable = False
        verdict = "MET" if identified and estimable else "NOT_MET"
        stage = "post_gate_4"
    if verdict not in C.SUCCESS_CRITERION_VALUES:
        raise ProtocolError(f"{verdict!r} is not a registered §26 value")
    return {
        "criterion": "§26 methodological success (v7)",
        "stage": stage, "verdict": verdict,
        "reference_support_identified": identified,
        "delta_r_estimable_at_gate_4": estimable,
        "realised": support.get("realised"),
        "note": "This is not the scientific effect claim. A structural zero "
                "for Delta_R on Gate 4's composed set is a finding about the "
                "operating regime --- every composed cell the contrast "
                "differences sat at the same boundary --- and it terminates "
                "nothing; the confirmatory blocks decide.",
    }
