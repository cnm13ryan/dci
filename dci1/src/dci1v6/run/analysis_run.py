"""§18 stages 15-18: masked analysis, the one-shot unmask, the unmasked
analysis, and the final report.

The path is one line and every arrow is a signed record:

    confirmatory rows -> observation table -> mask -> masked analysis ->
    sealed masked artifact -> one-shot unmask -> registered final analysis ->
    final report.

**The mask is a commitment device (§20).** The masked analysis runs the whole
registered pipeline on a *permuted* view, seals its result and its analysis
code hash, and only then is the key readable. What that buys is that the
analysis code cannot be adjusted after seeing which companion is which --- and
what it costs is that a defect found after the seal cannot be repaired, which
is exactly what happened to v4r4's L4 emitter. That is why §19's pilot runs the
claim-ladder tests *before* qualification.

**Unmask exactly once.** ``analysis/masking.unmask`` binds the event to the
sealed masked artifact's hash and to the analysis code hash, and the
``UNMASKING`` stage record is write-once like every other. A second unmask is
refused by ``assert_transition_legal``: the record already exists, and a
repair is a new protocol revision, not a rewritten record. There is no
"supersede this unmask" path here; §28's supersession machinery is explicit,
historical and separate.

**A quantity is computed only when its identification status licenses it.**
Otherwise the entry is ``NOT_IDENTIFIED`` with the status that explains it ---
never zero, never a bare NaN, never an omission, and never a substitute
estimand that happened to be computable. ``NOT_IDENTIFIED`` and "we measured
it and it was small" are different results and the record distinguishes them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol.hashing import sha_obj

from dci1v6.analysis import claims, estimators, masking, spectrum
from dci1v6.analysis.bootstrap import bootstrap_family
from dci1v6.analysis.observations import ObservationTable, build_observations
from dci1v6.engine import transitions
from dci1v6.engine.paths import ModelTree
from dci1v6.protocol import constants as C
from dci1v6.protocol import identification, seeds
from dci1v6.run.confirmatory_run import collect_rows
from dci1v6.run import final_report_checks
from dci1v6.run.freeze_run import load_freeze
from dci1v6.run.lifecycle import StageOutcome, run_stage
from dci1v6.stages import final_report as final_report_stage
from dci1v6.stages import support as support_stage

__all__ = ["ANALYSIS_MODULES", "NOT_IDENTIFIED", "analysis_code_hash",
           "observation_table", "estimate_all", "masked_payload",
           "run_masked_analysis", "unmask_payload", "run_unmasking",
           "unmasked_payload", "run_unmasked_analysis", "final_report_payload",
           "run_final_report"]

NOT_IDENTIFIED = "NOT_IDENTIFIED"

#: The modules whose bytes decide what the analysis computes. Hashed before
#: the mask is sealed and re-verified before the unmask, so an analysis that
#: moved between the two is refused rather than reported.
ANALYSIS_MODULES = ("analysis/observations.py", "analysis/estimators.py",
                    "analysis/spectrum.py", "analysis/bootstrap.py",
                    "analysis/intervals.py", "analysis/claims.py",
                    "analysis/masking.py", "run/analysis_run.py")


def analysis_code_hash() -> str:
    here = Path(__file__).resolve().parents[1]
    return masking.analysis_code_hash([here / name
                                       for name in ANALYSIS_MODULES])


def observation_table(rows: Sequence[Mapping[str, Any]], *, m_draws: int
                      ) -> ObservationTable:
    return ObservationTable(build_observations(list(rows), m_draws=m_draws))


#: Every member whose value comes from §11.7's difficulty relation or
#: §11.8's secondary fit on it. A status that blocks the relation blocks all
#: of them: naming only ``delta_difficulty`` left F5's two recodings of it and
#: F8's five fit parameters to be attempted, fail for want of a cell, and be
#: recorded ``not_computable`` --- the label §34 D6 exists to distinguish from
#: an unidentified design.
_DIFFICULTY_DEPENDENT: tuple[str, ...] = (
    "delta_difficulty", "delta_difficulty|vacuity_forced",
    "delta_difficulty|graded_0.99", "beta", "alpha_1", "alpha_2", "alpha_3",
    "gamma_tier")


def _licensed(statuses: Sequence[str]) -> dict[str, str | None]:
    """Which estimand each identification status blocks.

    Every entry carries the status that blocked it, so a reader of the record
    can see *why* a quantity was not computed and adding a status without
    deciding what it blocks stays a visible omission.

    **``REFERENCE_SUPPORT_NOT_IDENTIFIED`` blocks the whole reference-dependent
    set**, derived by ``protocol/identification.py``'s one rule rather than
    listed here. An earlier revision named five members; the other forty-three
    were attempted, returned no vector because the design supplies no cell for
    them, and were recorded as ``not_computable`` --- which reads as a design
    that was never asked rather than as §34 D6's irreversible verdict. The
    difference matters because the freeze binds the D6 set and the final
    report is checked against it.
    """
    blocked: dict[str, str] = {}
    statuses = set(statuses)
    if "REFERENCE_SUPPORT_NOT_IDENTIFIED" in statuses or \
            "EXCESS_NOT_IDENTIFIED" in statuses:
        for member in identification.AFFECTED_ESTIMANDS:
            blocked[member] = "REFERENCE_SUPPORT_NOT_IDENTIFIED"
    if "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in statuses:
        for member in _DIFFICULTY_DEPENDENT:
            blocked[member] = "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
    if "NEAR_FORM_ARM_NOT_AVAILABLE" in statuses:
        blocked["Delta_near"] = "NEAR_FORM_ARM_NOT_AVAILABLE"
    if "CLASS_ARM_NOT_AVAILABLE" in statuses:
        blocked["Delta_broad"] = "CLASS_ARM_NOT_AVAILABLE"
    if "DIFFICULTY_COORDINATE_DEGENERATE" in statuses:
        for member in _DIFFICULTY_DEPENDENT:
            blocked[member] = "DIFFICULTY_COORDINATE_DEGENERATE"
    return blocked


def _vector(fn: Callable[..., Any], *args: Any, **kwargs: Any
            ) -> list[float] | None:
    """Compute a per-block vector, or None when the design does not supply it.

    A missing cell is an ``IntegrityError`` from the observation table --- the
    analysis fails closed on a missing cell (§21) --- and that is a different
    fact from an unidentified estimand. It is returned as ``None`` and the
    caller records which of the two it was.
    """
    try:
        return list(fn(*args, **kwargs))
    except Exception:
        return None


#: §15's delivery-loss members, as member name -> (outcome slot, companion
#: slot). Every one of them is `estimators.delivery_loss` with a different
#: pair, and F2's D(B<-R_j), F3's D(A<-R_j), F7's reciprocals, F8's six
#: spectrum losses, F9's D(B<-N_k) and F10's D(B<-CL) were registered members
#: that no production call ever formed.
def _loss_members() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {"D(B<-A)": ("B", "A"),
                                       "D(A<-B)": ("A", "B")}
    for slot in C.CORE_SLOTS:
        out[f"D(B<-{slot})"] = ("B", slot)          # F2
        out[f"D(A<-{slot})"] = ("A", slot)          # F3
        out[f"D({slot}<-B)"] = (slot, "B")          # F7
        out[f"D({slot}<-A)"] = (slot, "A")          # F7
    for slot in C.SPECTRUM_SLOTS:
        out[f"D(B<-{slot})"] = ("B", slot)          # F8
    for slot in C.NEAR_FORM_SLOTS:
        out[f"D(B<-{slot})"] = ("B", slot)          # F9
    out[f"D(B<-{C.CLASS_SLOT})"] = ("B", C.CLASS_SLOT)   # F10
    return out


#: §15 F6: the vacuity-rate difference between each composed cell containing
#: B and the B solo cell, as member name -> companion slot.
def _vacuity_members() -> dict[str, str]:
    out = {"vac(B|A+B)-vac(B solo)": "A"}
    for slot in (C.CORE_SLOTS + C.SPECTRUM_SLOTS + C.NEAR_FORM_SLOTS
                 + (C.CLASS_SLOT,)):
        out[f"vac(B|B+{slot})-vac(B solo)"] = slot
    return out


LOSS_MEMBERS = _loss_members()
VACUITY_MEMBERS = _vacuity_members()

#: §15 F5's two recodings, as member suffix -> the Observation field the
#: estimand is recomputed on. §9.3 forms both at DRAW level --- the
#: vacuity-forced recoding counts a vacuous pass as a failure (§17.4) and the
#: graded recoding thresholds each draw's graded score at 0.99 --- and
#: `observations.build_observations` has always produced them. Nothing read
#: them, so F5 had no member with a producer.
F5_RECODINGS: dict[str, str] = {
    "vacuity_forced": "non_vacuous_compliance",
    "graded_0.99": "graded_threshold",
}
#: Which F1 members F5 recomputes under each recoding, from §15's table: "the
#: six F1 members under the vacuity-forced recoding, and D(B<-A), Delta_R,
#: delta_difficulty under a graded threshold at 0.99".
F5_MEMBERS: dict[str, tuple[str, ...]] = {
    "vacuity_forced": C.FAMILY_MEMBERS["F1"],
    "graded_0.99": ("D(B<-A)", "Delta_R", "delta_difficulty"),
}


#: F5's five vector members, as base member -> the estimator that forms it
#: under a named recoding. Each already took a ``scale`` keyword; nothing
#: ever passed one.
_F5_ESTIMATORS: dict[str, Callable[..., Any]] = {
    "D(B<-A)": lambda table, configuration, *, scale: (
        estimators.delivery_loss(table, "B", "A", configuration, scale=scale)),
    "D(A<-B)": lambda table, configuration, *, scale: (
        estimators.delivery_loss(table, "A", "B", configuration, scale=scale)),
    "Lambda": lambda table, configuration, *, scale: (
        estimators.asymmetry(table, configuration, scale=scale)),
    "Delta_R": lambda table, configuration, *, scale: (
        estimators.delta_r(table, configuration, scale=scale)),
    "Xi": lambda table, configuration, *, scale: (
        estimators.xi(table, configuration, scale=scale)),
}


def tier_inputs(table: ObservationTable,
                slot_families: Mapping[str, str],
                spectrum_by_configuration: Mapping[str, Any]
                ) -> dict[str, spectrum.TierInput]:
    """§11.8's twelve points per configuration, or nothing.

    The three near-form controls are the points that make the tier indicator
    vary; without the arm there is no secondary fit, and §15 records that as
    ``NEAR_FORM_ARM_NOT_AVAILABLE`` rather than as a missing number.
    """
    from dci1v6.verifiers.constraints import FAMILIES

    near = {slot: family for slot, family in slot_families.items()
            if slot in set(C.NEAR_FORM_SLOTS)}
    out: dict[str, spectrum.TierInput] = {}
    if not near:
        return out
    for configuration, base in spectrum_by_configuration.items():
        slots = [s for s in near
                 if table.has_composed("B", s, configuration)]
        if len(slots) != len(near):
            continue
        tiers: dict[str, int] = {}
        for slot, family in list(base.family_of.items()) + [
                (s, near[s]) for s in slots]:
            entry = FAMILIES.get(family)
            tiers[slot] = entry.structural_tier if entry is not None else 0
        out[configuration] = spectrum.TierInput(
            base=base,
            near_family_of={s: near[s] for s in slots},
            near_solo={s: estimators.solo_vector(table, s) for s in slots},
            near_chance={s: estimators.chance_vector(table, s)
                         for s in slots},
            b_with_near={s: estimators.composed_vector(table, "B", s,
                                                       configuration)
                         for s in slots},
            tiers=tiers)
    return out


def spectrum_inputs(table: ObservationTable,
                    slot_families: Mapping[str, str],
                    *, scale: str = estimators.PRIMARY_SCALE
                    ) -> dict[str, spectrum.SpectrumInput]:
    """§11.7's nine points per configuration, from the table and the freeze.

    ``slot_families`` is the freeze's slot map reduced to slot -> family, for
    the core and spectrum slots only: §11.7 fits three families of three
    severities, A is excluded because the relation is what predicts A, and the
    near-form and broad-class slots are not on the ladder.

    Returns one input per configuration, because ``delta_difficulty`` is a
    per-configuration member of F1 exactly as ``Delta_R`` is.
    """
    family_of = {slot: family for slot, family in slot_families.items()
                 if slot in set(C.CORE_SLOTS) | set(C.SPECTRUM_SLOTS)}
    out: dict[str, spectrum.SpectrumInput] = {}
    for configuration in C.CONFIGURATIONS:
        slots = [s for s in family_of if table.has_composed(
            "B", s, configuration)]
        if len(slots) != len(family_of) or not table.has_composed(
                "B", "A", configuration):
            continue
        b_with = {s: estimators.composed_vector(table, "B", s, configuration,
                                                scale=scale)
                  for s in slots}
        b_with["A"] = estimators.composed_vector(table, "B", "A",
                                                 configuration, scale=scale)
        out[configuration] = spectrum.SpectrumInput(
            blocks=tuple(table.blocks),
            family_of={s: family_of[s] for s in slots},
            b_solo=estimators.solo_vector(table, "B", scale=scale),
            b_with=b_with,
            companion_solo={s: estimators.solo_vector(table, s, scale=scale)
                            for s in slots},
            companion_chance={s: estimators.chance_vector(table, s,
                                                          scale=scale)
                              for s in slots},
            a_solo=estimators.solo_vector(table, "A", scale=scale),
            a_chance=estimators.chance_vector(table, "A", scale=scale))
    return out


def estimate_all(table: ObservationTable, *, statuses: Sequence[str],
                 arms: Sequence[str], seed: int,
                 resamples: int = C.BOOTSTRAP_RESAMPLES,
                 slot_families: Mapping[str, str] | None = None
                 ) -> dict[str, Any]:
    """Every registered quantity, or ``NOT_IDENTIFIED`` with its reason.

    The five order contrasts of F11 are computed **across** configurations,
    which is why F11 is declared as the one cross-configuration family: an
    order contrast has no value inside a single configuration and v4r4 had no
    registered direct contrast at all.

    ``slot_families`` supplies §11.7's family grouping and is passed **only
    after unmasking**. A's point sits inside the permuted group, so
    ``delta_difficulty`` and the fit's coefficients have no masked-phase value
    (§20); without it the member is recorded ``NOT_IDENTIFIED`` with that
    reason, which is a different fact from an unidentified design and is
    written as such.
    """
    blocked = _licensed(statuses)
    post_unmask = bool(slot_families)
    spectrum_by_configuration = (spectrum_inputs(table, slot_families)
                                 if post_unmask else {})
    # F5's delta_difficulty recodings need the whole fit refitted on the
    # recoded scale --- §17.4 recomputes the ESTIMAND, not a rescaled point.
    spectrum_by_configuration_recoded = (
        {suffix: spectrum_inputs(table, slot_families, scale=scale)
         for suffix, scale in F5_RECODINGS.items()}
        if post_unmask else {})
    tier_by_configuration = (tier_inputs(table, slot_families,
                                         spectrum_by_configuration)
                             if post_unmask else {})
    # §20 names the members that have no masked-phase value: A's point is
    # inside the permuted group, so a contrast of A against the reference set
    # is a contrast against a set A may have been permuted into. They are
    # withheld here rather than computed and discarded downstream --- a number
    # that exists is a number a masked-phase decision can see.
    # §20 withholds a member by what it IS, not by the exact string: F5's two
    # recodings of Delta_R are still values for Delta_R, computed against the
    # same permuted assignment of companions, and `gamma_tier` is the same fit
    # as `beta`. The stem is what the guard on the sealed record matches, so
    # it is what the withholding matches.
    withheld = () if post_unmask else tuple(
        member
        for members in C.FAMILY_MEMBERS.values() for member in members
        if member.split("|")[0] in masking.MASKED_PHASE_FORBIDDEN_MEMBERS)
    out: dict[str, Any] = {"configurations": {}, "cross_configuration": {},
                           "blocked": blocked,
                           "spectrum_phase": ("post_unmask" if post_unmask
                                              else "masked"),
                           "masked_phase_members_withheld": list(withheld),
                           "not_identified": [], "not_computable": []}

    def record(bucket: dict[str, Any], member: str,
               vector: list[float] | None) -> None:
        if member in withheld:
            bucket[member] = {
                "status": NOT_IDENTIFIED, "reason": "MASKED_PHASE",
                "detail": masking.MASKED_PHASE_DECLARATIONS.get(
                    member, "§20: not computable before the unmask")}
            out["not_computable"].append(member)
            return
        if member in blocked:
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": blocked[member]}
            out["not_identified"].append(member)
            return
        if vector is None:
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": "the admitted design supplies no "
                                        "cell for this contrast"}
            out["not_computable"].append(member)
            return
        bucket[member] = {"status": "IDENTIFIED", "n_blocks": len(vector),
                          "point": sum(vector) / len(vector)}
        bucket[member]["_vector"] = vector

    for configuration in C.CONFIGURATIONS:
        bucket: dict[str, Any] = {}
        # F1's two, and F2's, F3's, F7's, F8's, F9's and F10's delivery
        # losses. Every registered pair, from one registry, so a family
        # cannot lose a member by nobody writing its line.
        for member, (outcome, companion) in sorted(LOSS_MEMBERS.items()):
            record(bucket, member,
                   _vector(estimators.delivery_loss, table, outcome,
                           companion, configuration=configuration))
        record(bucket, "Lambda",
               _vector(estimators.asymmetry, table, configuration))
        record(bucket, "Delta_R",
               _vector(estimators.delta_r, table, configuration))
        # §11.7 and §17.2: a replicate refits the relation, so the member is
        # a *function* of the replicate's index vector, not a per-block
        # vector. ``bootstrap_family`` takes both kinds and gives them one
        # index draw, which is what keeps F1's simultaneous interval coherent
        # --- and an earlier revision computed this member nowhere at all, so
        # F1's critical value was taken over five members instead of six.
        _record_delta_difficulty(bucket, out, spectrum_by_configuration,
                                 configuration, blocked, withheld=withheld)
        record(bucket, "Xi", _vector(estimators.xi, table, configuration))
        for index, slot in enumerate(C.CORE_SLOTS, start=1):
            record(bucket, f"Delta_{index}",
                   _vector(estimators.delta_j, table, slot, configuration))
        record(bucket, "Delta_near",
               _vector(estimators.delta_near, table, configuration))
        record(bucket, "Delta_broad",
               _vector(estimators.delta_broad, table, configuration))
        record(bucket, "Delta^A",
               _vector(estimators.delta_a, table, configuration))
        record(bucket, "D(Rbar<-A)",
               _vector(estimators.d_rbar_from, table, "A", configuration))
        record(bucket, "D(Rbar<-B)",
               _vector(estimators.d_rbar_from, table, "B", configuration))
        record(bucket, "D(Rbar<-Rbar')",
               _vector(estimators.d_rbar_rbar, table, configuration))
        # ------------------------------------------------------------- F6
        # §17.4's gate: the vacuity-rate difference between each composed
        # cell containing B and the B solo cell. `vacuity_difference` existed
        # and was called from nowhere, so the family that GATES the §17.4
        # interpretation had no member with a producer.
        for member, companion in sorted(VACUITY_MEMBERS.items()):
            record(bucket, member,
                   _vector(estimators.vacuity_difference, table, companion,
                           configuration))
        # ------------------------------------------------------------- F5
        # The primary estimands recomputed on §9.3's two draw-level
        # recodings. Not a length restriction and not a re-thresholded cell
        # mean: `observations` forms both at draw level and these read them.
        for suffix, scale in sorted(F5_RECODINGS.items()):
            for base_member in F5_MEMBERS[suffix]:
                member = f"{base_member}|{suffix}"
                if base_member == "delta_difficulty":
                    _record_delta_difficulty(
                        bucket, out,
                        spectrum_by_configuration_recoded.get(suffix, {}),
                        configuration, blocked, member=member,
                        withheld=withheld)
                    continue
                record(bucket, member,
                       _vector(_F5_ESTIMATORS[base_member], table,
                               configuration, scale=scale))
        # ------------------------------------------------------------- F8
        # §11.8's tier-indicator secondary, under U2's adopted A2 reading.
        # `fit_with_tier_indicator` was resolved at A2 and never called by
        # any production path, so the five fit members F8 registers --- the
        # reason U2 was resolved at all --- reached no record.
        _record_tier_fit(bucket, out, tier_by_configuration, configuration,
                         blocked, withheld=withheld)
        out["configurations"][configuration] = bucket

    cross = out["cross_configuration"]
    for member in C.FAMILY_MEMBERS["F11"]:
        record(cross, member,
               _vector(estimators.order_contrast, table, member))

    # §11.3, §11.7 and §11.8 each register an EXECUTABLE check that the
    # quantity's two algebraic forms agree to 1e-9, because the solo baseline
    # has to cancel exactly for the contrast to be a contrast among composed
    # cells. All three were implemented and none had a caller, so §18's steps
    # 8 and 9 asserted nothing. A disagreement refuses; a design that
    # supplies no cell for the contrast is a different fact and is recorded.
    out["algebraic_form_checks"] = _algebraic_form_checks(
        table, spectrum_by_configuration)

    # §18 step 14: repeat steps 9 and 12 on the raw-coordinate secondary
    # fit. Step 9 is executed in full; step 12 is NOT_REGISTERED_FOR_INFERENCE
    # and the reason is in `_raw_coordinate_secondary`.
    out["raw_coordinate_secondary"] = _raw_coordinate_secondary(
        spectrum_by_configuration, seed=seed, resamples=resamples,
        post_unmask=post_unmask)

    out["intervals"] = _intervals(out, seed=seed, resamples=resamples,
                                  n_blocks=len(table.blocks))
    return out


#: §18 step 14 says "repeat steps 9 and 12". Step 12 computes a SIMULTANEOUS
#: interval **within each declared family**, and §15 declares no family
#: containing a raw-coordinate member: it registers the raw-coordinate
#: replication of the fit among the quantities "reported with marginal
#: intervals only and supporting no claim". Declaring one would invent a
#: multiplicity set nobody registered, and computing a simultaneous interval
#: over a family of one is not the same construction. So step 12's half is
#: recorded as not registered for inference, with marginal percentile
#: intervals reported in its place --- which is what §15 asks for.
RAW_COORDINATE_MULTIPLICITY = "NOT_REGISTERED_FOR_INFERENCE"


def _raw_coordinate_secondary(spectrum_by_configuration: Mapping[str, Any], *,
                              seed: int, resamples: int, post_unmask: bool
                              ) -> dict[str, Any]:
    """§18 step 14, §15's raw-coordinate replication, §34 D14's secondary.

    §34 D14 is closed at *"iota remains primary, raw solo secondary,
    `DIFFICULTY_COORDINATE_DEPENDENT` on disagreement"*, and §17.6's
    coordinate-agreement paragraph is the rule that closure serves. Both
    needed a raw-coordinate fit and no production path ever computed one, so
    the status was unreachable and D14's closure bound nothing.

    What is computed here is step 9 in full on the raw coordinate: the fit on
    the nine non-A points, A's exclusion (the fitter refuses an A point on
    either coordinate), §13.13's support conditions, delta_difficulty in both
    algebraic forms with the agreement assertion, and the block bootstrap.
    What is NOT computed is a simultaneous interval, and
    ``RAW_COORDINATE_MULTIPLICITY`` says why.

    Masked phase: A's point is inside the permuted group on either
    coordinate, so the replication has no masked-phase value either and is
    withheld exactly as ``delta_difficulty`` is.
    """
    out: dict[str, Any] = {
        "registered_by": "§18 step 14, §15, §17.6, §34 D14",
        "primary_coordinate": C.DIFFICULTY_COORDINATE,
        "coordinate": C.SECONDARY_DIFFICULTY_COORDINATE,
        "step_9": "executed",
        "step_12": RAW_COORDINATE_MULTIPLICITY,
        "step_12_reason": (
            "§15 registers the raw-coordinate replication of the fit among "
            "the quantities reported with marginal intervals only and "
            "supporting no claim, and §15's F1-F11 declares no family "
            "containing a raw-coordinate member. Declaring one would invent "
            "a multiplicity set; marginal percentile intervals are reported "
            "in its place"),
        "licenses": "no claim at any level; §17.6's coordinate-agreement "
                    "status is its only consequence",
        "configurations": {},
    }
    if not post_unmask:
        out["step_9"] = "MASKED_PHASE"
        out["detail"] = ("§20: A's point is inside the permuted group on "
                         "either coordinate, so the replication has no "
                         "masked-phase value")
        return out
    for configuration, data in sorted(spectrum_by_configuration.items()):
        entry: dict[str, Any] = {}
        try:
            entry["algebraic_forms_worst"] = \
                spectrum.assert_algebraic_forms_agree(
                    data, coordinate=C.SECONDARY_DIFFICULTY_COORDINATE)
        except spectrum.FitNotAvailable as absent:
            entry["algebraic_forms_worst"] = None
            entry["not_available"] = str(absent)
        point = spectrum.estimate(
            data, coordinate=C.SECONDARY_DIFFICULTY_COORDINATE)
        if point["degenerate"]:
            entry["status"] = NOT_IDENTIFIED
            entry["reason"] = "DIFFICULTY_COORDINATE_DEGENERATE"
            entry["detail"] = point.get("reason")
            out["configurations"][configuration] = entry
            continue
        boot = spectrum.bootstrap_spectrum(
            data, resamples=resamples, seed=seed,
            coordinate=C.SECONDARY_DIFFICULTY_COORDINATE)
        entry.update({
            "status": "IDENTIFIED",
            "point": float(point["delta_difficulty"]),
            "slope": float(point["slope"]),
            "intercepts": dict(point["intercepts"]),
            "predicted_at_A": float(point["predicted_at_A"]),
            "difficulty_a": float(point["difficulty_a"]),
            "residuals": dict(point["residuals"]),
            "support": point["support"],
            "dropped_points": list(point["dropped_points"]),
            "marginal_ci95": list(boot["ci95_percentile"]),
            "bootstrap_se": float(boot["bootstrap_se"]),
            "slope_marginal_ci95": list(boot["slope_ci95_percentile"]),
            "support_bootstrap_share": boot["support_bootstrap_share"],
            "identification_statuses": list(boot["identification_statuses"]),
            "simultaneous_ci95": None,
            "simultaneous_ci95_reason": RAW_COORDINATE_MULTIPLICITY,
            "resamples": boot["resamples"],
            "refit_per_replicate": True,
        })
        out["configurations"][configuration] = entry
    return out


def _algebraic_form_checks(table: ObservationTable,
                           spectrum_by_configuration: Mapping[str, Any]
                           ) -> dict[str, Any]:
    """§18 steps 8 and 9's agreement assertions, and what they found.

    Each check raises on a disagreement above the registered tolerance. A
    missing cell is not a disagreement: it is recorded as ``not_available``
    with the reason, exactly as an unidentified member is.
    """
    out: dict[str, Any] = {"tolerance": C.ALGEBRAIC_FORM_TOLERANCE,
                           "checks": {}}
    for configuration in C.CONFIGURATIONS:
        try:
            worst = estimators.assert_delta_r_forms(table, configuration)
        except (IntegrityError, ProtocolError) as absent:
            if isinstance(absent, estimators.AlgebraicFormError):
                raise
            out["checks"][f"Delta_R:{configuration}"] = {
                "not_available": str(absent)}
        else:
            out["checks"][f"Delta_R:{configuration}"] = {"worst": worst}
    try:
        worst_order = estimators.assert_order_forms(table)
    except (IntegrityError, ProtocolError) as absent:
        if isinstance(absent, estimators.AlgebraicFormError):
            raise
        out["checks"]["order_contrasts"] = {"not_available": str(absent)}
    else:
        out["checks"]["order_contrasts"] = {"worst": worst_order}
    for configuration, data in sorted(spectrum_by_configuration.items()):
        try:
            worst = spectrum.assert_algebraic_forms_agree(data)
        except spectrum.FitNotAvailable as absent:
            out["checks"][f"delta_difficulty:{configuration}"] = {
                "not_available": str(absent)}
        else:
            out["checks"][f"delta_difficulty:{configuration}"] = {
                "worst": worst}
    return out


def _record_delta_difficulty(bucket: dict[str, Any], out: dict[str, Any],
                             inputs: Mapping[str, Any], configuration: str,
                             blocked: Mapping[str, str],
                             member: str = "delta_difficulty",
                             withheld: Sequence[str] = ()) -> None:
    """§11.7's residual, or the reason there is no value for it.

    Three different absences, written as three different reasons: the design
    did not identify the spectrum; this is the masked phase and A's point is
    inside the permuted group; or the fit is degenerate on the observed
    sample. None of them is zero and none of them is an omission.
    """
    # §20 first, and D6/§13.13 second. Both can be true of a masked-phase
    # member and they are different facts: the design's verdict is about what
    # the replication can ever identify, and §20's is about what THIS phase
    # may compute. Reading the design's verdict first let it shadow the
    # masking reason on a replication whose spectrum was dropped.
    if member in set(withheld):
        bucket[member] = {
            "status": NOT_IDENTIFIED, "reason": "MASKED_PHASE",
            "detail": masking.MASKED_PHASE_DECLARATIONS.get(
                member.split("|")[0],
                "§20: not computable before the unmask")}
        out["not_computable"].append(member)
        return
    if member in blocked:
        bucket[member] = {"status": NOT_IDENTIFIED, "reason": blocked[member]}
        out["not_identified"].append(member)
        return
    data = inputs.get(configuration)
    if data is None:
        bucket[member] = {
            "status": NOT_IDENTIFIED,
            "reason": "MASKED_PHASE" if not inputs else
                      "the admitted design supplies no spectrum ladder for "
                      "this configuration",
            "detail": "§20: A's point is inside the permuted group, so the "
                      "residual has no masked-phase value" if not inputs
                      else None}
        out["not_computable"].append(member)
        return
    point = spectrum.estimate(data)
    if point["degenerate"]:
        bucket[member] = {"status": NOT_IDENTIFIED,
                          "reason": "DIFFICULTY_COORDINATE_DEGENERATE",
                          "detail": point.get("reason")}
        out["not_identified"].append(member)
        return
    bucket[member] = {
        "status": "IDENTIFIED", "n_blocks": len(data.blocks),
        "point": float(point["delta_difficulty"]),
        "slope": float(point["slope"]),
        "predicted_at_A": float(point["predicted_at_A"]),
        "support": point["support"],
        "refit_per_replicate": True,
        # The callable form §17.2 requires: every replicate resamples blocks,
        # recomputes the difficulties, refits the non-A relation, predicts at
        # A and recomputes the residual.
        "_vector": lambda picks, _d=data: float(
            spectrum.estimate(_d, list(picks))["delta_difficulty"]),
    }


def _record_tier_fit(bucket: dict[str, Any], out: dict[str, Any],
                     inputs: Mapping[str, Any], configuration: str,
                     blocked: Mapping[str, str],
                     withheld: Sequence[str] = ()) -> None:
    """F8's five fit members, or the registered reason there are none.

    §11.8's secondary is the fit U2 was resolved at A2 to make estimable, and
    §15 registers its slope, its three core-family intercepts and its tier
    offset as F8 members. Every one of them refits per replicate, exactly as
    ``delta_difficulty`` does, so each is recorded in the callable form
    §17.2 requires.
    """
    members = ("beta", "alpha_1", "alpha_2", "alpha_3", "gamma_tier")
    data = inputs.get(configuration)

    def unavailable(reason: str, detail: str | None,
                    bucket_key: str) -> None:
        for member in members:
            if member in set(withheld):
                bucket[member] = {"status": NOT_IDENTIFIED,
                                  "reason": "MASKED_PHASE",
                                  "detail": "§20: the fit's coefficients are "
                                            "post-unmasking"}
                out["not_computable"].append(member)
                continue
            if member in blocked:
                bucket[member] = {"status": NOT_IDENTIFIED,
                                  "reason": blocked[member]}
                out["not_identified"].append(member)
                continue
            bucket[member] = {"status": NOT_IDENTIFIED, "reason": reason,
                              "detail": detail}
            out[bucket_key].append(member)

    if data is None:
        unavailable(
            "MASKED_PHASE" if not inputs else "NEAR_FORM_ARM_NOT_AVAILABLE",
            "§20: the tier fit reads A's group and has no masked-phase value"
            if not inputs else
            "§11.8's secondary fit needs the three near-form controls; "
            "without them the tier indicator does not vary and gamma is not "
            "identified",
            "not_computable")
        return
    # One fit per replicate, shared by the five members. `bootstrap_family`
    # gives every member of a family the SAME index draw and calls them in
    # sequence, so a one-entry cache keyed by that draw turns five refits per
    # replicate into one --- without which §17.2's refit-per-replicate rule
    # costs 100,000 least-squares solves per configuration at 10,000
    # resamples. The rule is unchanged; only the arithmetic is not repeated.
    cache: dict[tuple[int, ...], dict[str, object]] = {}

    def fitted(picks: Sequence[int]) -> dict[str, object]:
        key = tuple(picks)
        if key not in cache:
            cache.clear()
            cache[key] = spectrum.tier_estimate(data, list(picks))
        return cache[key]

    point = spectrum.tier_estimate(data)
    if point["degenerate"]:
        unavailable("TIER_FIT_DEGENERATE", str(point.get("reason")),
                    "not_identified")
        return
    # §11.8 and §15: alpha_f ranges over the three CORE families, and F8's
    # three intercepts are those three. The index follows the core slot
    # order, so alpha_j and Delta_j name the same reference.
    core_families = [data.base.family_of[slot] for slot in C.CORE_SLOTS
                     if slot in data.base.family_of]
    intercepts = dict(point["intercepts"])
    values: dict[str, Any] = {"beta": ("beta", None),
                              "gamma_tier": ("gamma", None)}
    for index, family in enumerate(core_families, start=1):
        values[f"alpha_{index}"] = ("intercepts", family)
    for member in members:
        if member in set(withheld):
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": "MASKED_PHASE",
                              "detail": "§20: the fit's coefficients are "
                                        "post-unmasking"}
            out["not_computable"].append(member)
            continue
        if member in blocked:
            bucket[member] = {"status": NOT_IDENTIFIED,
                              "reason": blocked[member]}
            out["not_identified"].append(member)
            continue
        spec = values.get(member)
        if spec is None or (spec[0] == "intercepts"
                            and spec[1] not in intercepts):
            bucket[member] = {
                "status": NOT_IDENTIFIED,
                "reason": "the admitted design supplies no core family for "
                          "this intercept"}
            out["not_computable"].append(member)
            continue
        key, family = spec
        value = (intercepts[family] if key == "intercepts" else point[key])

        def _refit(picks, _key=key, _family=family):
            replicate = fitted(picks)
            if replicate["degenerate"]:
                raise ProtocolError(str(replicate.get("reason")))
            return float(replicate["intercepts"][_family]
                         if _key == "intercepts" else replicate[_key])

        bucket[member] = {
            "status": "IDENTIFIED", "n_blocks": len(data.base.blocks),
            "point": float(value),
            "n_points": point["n_points"],
            "formulation": point["formulation"],
            "adopted_formulation": point["adopted"],
            "core_family": family,
            "refit_per_replicate": True,
            "_vector": _refit,
        }


def _intervals(estimates: Mapping[str, Any], *, seed: int, resamples: int,
               n_blocks: int) -> dict[str, Any]:
    """Simultaneous intervals per §15 family, one index draw per replicate."""
    out: dict[str, Any] = {}
    if n_blocks < 2:
        return {"skipped": "the block bootstrap needs at least two blocks"}
    for family, members in C.FAMILY_MEMBERS.items():
        source = (estimates["cross_configuration"]
                  if family in C.CROSS_CONFIGURATION_FAMILIES else None)
        configurations = ([None] if source is not None
                          else list(C.CONFIGURATIONS))
        for configuration in configurations:
            bucket = (source if source is not None
                      else estimates["configurations"][configuration])
            usable = {m: bucket[m]["_vector"] for m in members
                      if m in bucket and "_vector" in bucket[m]}
            key = f"{family}:{configuration or 'cross'}"
            if not usable:
                # A family with no computable member has no simultaneous
                # interval, and that has to be *said*. Four families were
                # skipped here in silence: they reached neither the interval
                # table nor the not-identified list, so a reader of §31's
                # table could not tell F8 apart from a family that does not
                # exist.
                out[key] = {
                    "family": family,
                    "configuration": configuration or "cross",
                    "interval": None,
                    "status": NOT_IDENTIFIED,
                    "members": list(members),
                    "member_status": {
                        m: (bucket.get(m, {}).get("status") or "NOT_RECORDED")
                        for m in members},
                    "reason": "no member of this family has a computable "
                              "value in this configuration, so §15's "
                              "simultaneous interval is not defined for it"}
                continue
            result = bootstrap_family(usable, seed=seed,
                                      configuration=configuration or "cross",
                                      family=family, n_blocks=n_blocks,
                                      resamples=resamples)
            out[key] = {
                name: {"estimate": member.estimate,
                       "lower": member.simultaneous_lower,
                       "upper": member.simultaneous_upper,
                       "half_width": member.half_width,
                       # §31's table needs the standard error and the
                       # marginal bounds beside the simultaneous ones, and
                       # §17.1 reports the marginal interval alongside. They
                       # were computed and then dropped here, so the final
                       # report had no producer for four of its own fields.
                       "standard_error": member.standard_error,
                       "marginal_lower": member.marginal_lower,
                       "marginal_upper": member.marginal_upper,
                       "refit_per_replicate": member.refit_per_replicate,
                       "degenerate": member.degenerate}
                for name, member in result.members.items()}
    return out


def _strip_vectors(estimates: Mapping[str, Any]) -> dict[str, Any]:
    """The record form: per-block vectors are working state, not evidence."""
    def clean(bucket: Mapping[str, Any]) -> dict[str, Any]:
        return {k: {kk: vv for kk, vv in v.items() if kk != "_vector"}
                for k, v in bucket.items()}
    return {
        "configurations": {k: clean(v)
                           for k, v in estimates["configurations"].items()},
        "cross_configuration": clean(estimates["cross_configuration"]),
        "blocked": estimates["blocked"],
        "spectrum_phase": estimates["spectrum_phase"],
        "masked_phase_members_withheld":
            list(estimates.get("masked_phase_members_withheld", ())),
        "not_identified": sorted(set(estimates["not_identified"])),
        "not_computable": sorted(set(estimates["not_computable"])),
        # §11.3, §11.7 and §11.8's agreement checks and what they found. The
        # record is the only place a reader can see that they ran, and this
        # function's explicit key list dropped them.
        "algebraic_form_checks": estimates.get("algebraic_form_checks", {}),
        "intervals": estimates.get("intervals", {}),
        # §18 step 14's raw-coordinate replication. Same reason as the
        # agreement checks above: this function's explicit key list is the
        # OUTPUT_DROPPED defect class in miniature, and `_statements` reads
        # this key off the STRIPPED result to apply §17.6's coordinate rule.
        "raw_coordinate_secondary":
            estimates.get("raw_coordinate_secondary", {}),
    }


# ------------------------------------------------------------ stage 15

def masked_payload(tree: ModelTree, *, producing_commit: str,
                   entropy: int | None = None) -> dict[str, Any]:
    freeze_record = load_freeze(tree)
    freeze = freeze_record["freeze"]
    confirmatory = transitions.read_stage_record(tree, C.STAGE_CONFIRMATORY)
    rows = collect_rows(tree)
    if not rows:
        raise ProtocolError(
            "§20: the masked analysis has no confirmatory rows to mask")
    observations = build_observations(rows, m_draws=freeze["m_draws"])
    mask = masking.build_mask(observations, namespace="confirmatory_mask",
                              entropy=entropy)
    effectiveness = masking.assert_mask_effective(observations, mask)
    masked_view = masking.apply_mask(observations, mask)

    mask_dir = tree.mask_dir("confirmatory_mask")
    mask_dir.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(tree.mask_key_path("confirmatory_mask"), mask)
    records = [dict(vars(o)) for o in masked_view]
    # §20's cleanliness rule, on the path that writes the artifact. It existed
    # and nothing called it, so the one guarantee about what the masked view
    # may contain was never checked against what was written.
    masking.assert_masked_view_clean(records)
    tree.masked_view("confirmatory_mask").write_text(
        "".join(json.dumps(r, sort_keys=True, default=str) + "\n"
                for r in records))

    table = ObservationTable([_as_observation(o) for o in masked_view])
    statuses = list(freeze_record["identification_statuses"])
    estimates = estimate_all(table, statuses=statuses,
                             arms=freeze["admitted_arms"],
                             seed=seeds.bootstrap_seed(
                                 "masked", tree.model_key),
                             resamples=C.BOOTSTRAP_RESAMPLES)
    result = _strip_vectors(estimates)
    masking.assert_delta_difficulty_not_masked(result)
    payload = {
        "stage": C.STAGE_MASKED_ANALYSIS,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_MASKED_ANALYSIS],
        "outcome": "PASS",
        "inputs": {"confirmatory": {"stage": C.STAGE_CONFIRMATORY,
                                    "n_rows": confirmatory["n_rows"]},
                   "freeze": {"stage": C.STAGE_GATE5,
                              "freeze_hash": freeze_record["freeze_hash"]}},
        "producing_commit": producing_commit,
        "mask_namespace": "confirmatory_mask",
        "mask_effectiveness": effectiveness,
        # §20 requires which order contrasts are masked-phase computable to be
        # derived by one named function and recorded here rather than assumed.
        "masked_phase_order_contrasts":
            masking.masked_phase_order_contrasts(mask),
        "masked_result": result,
        "analysis_code_hash": analysis_code_hash(),
        "n_observations": len(observations),
        "sealed": True,
        "seal_statement":
            "§20: the masked result and the analysis code hash are sealed "
            "here; the key is readable only through the UNMASKING stage, and "
            "a defect found after this point cannot be repaired --- which is "
            "why §19's pilot runs the claim-ladder tests before qualification",
    }
    payload["masked_result_hash"] = sha_obj(result)
    return payload


def _as_observation(masked: Any) -> Any:
    """A masked observation, re-typed for the observation table.

    The two names that differ are the two the mask acts on: the companion is
    the **permuted** label and the cell is its pseudonym. Everything else is
    the observation's own value. Copying only the fields whose names happened
    to match left ``cell_id``, ``arm``, ``companion_slot``, ``draws`` and
    ``processing_failures`` unset and raised on construction, which is why
    the masked stage had never run.
    """
    from dci1v6.analysis.observations import Observation

    return Observation(
        block_id=masked.block_id, cell_id=masked.masked_cell_id,
        arm=masked.arm, outcome_slot=masked.outcome_slot,
        companion_slot=masked.companion_label, position=masked.position,
        configuration=masked.configuration, draws=masked.draws,
        compliance=masked.compliance, graded=masked.graded,
        vacuity=masked.vacuity, truncation=masked.truncation,
        non_vacuous_compliance=masked.non_vacuous_compliance,
        graded_threshold=masked.graded_threshold,
        response_words=masked.response_words,
        processing_failures=masked.processing_failures,
        present=masked.present)


def run_masked_analysis(tree: ModelTree, *, producing_commit: str | None = None,
                        environment_digest: str = "",
                        entropy: int | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_MASKED_ANALYSIS,
        compute=lambda _prev: masked_payload(tree, producing_commit=commit,
                                             entropy=entropy),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 16

def unmask_payload(tree: ModelTree, *, producing_commit: str
                   ) -> dict[str, Any]:
    """§20's irreversible unmask, bound to the sealed masked artifact.

    The stage record is write-once, so a second unmask is refused by the
    stage machine rather than by a flag this function keeps. There is no
    supersession path here on purpose: re-unmasking after seeing a result is
    the failure §20 exists to prevent, and making it require an explicit,
    historical, separately-recorded supersession is the point.
    """
    masked = transitions.read_stage_record(tree, C.STAGE_MASKED_ANALYSIS)
    current = analysis_code_hash()
    if current != masked["analysis_code_hash"]:
        raise ProtocolError(
            "§20: the analysis code moved between the seal and the unmask. "
            f"Sealed {masked['analysis_code_hash']}, now {current}. An "
            "unmasked analysis under a moved analysis hash is refused")
    key = masking.MaskKey(tree.mask_key_path("confirmatory_mask"))
    event = masking.unmask(key, analysis_code_hash=current,
                           masked_outputs_hash=masked["masked_result_hash"])
    return {
        "stage": C.STAGE_UNMASKING,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKING],
        "outcome": "PASS",
        "inputs": {"masked": {"stage": C.STAGE_MASKED_ANALYSIS,
                              "masked_result_hash":
                                  masked["masked_result_hash"]}},
        "producing_commit": producing_commit,
        "unmasked": True,
        "mask_key_hash": sha_obj(fs.read_json(
            tree.mask_key_path("confirmatory_mask"))),
        "unmask_event": event,
        "analysis_code_hash": current,
        "once_only":
            "the stage record is write-once; a second unmask is refused by "
            "assert_transition_legal and a repair is a new protocol "
            "revision, not a rewritten record",
    }


def run_unmasking(tree: ModelTree, *, producing_commit: str | None = None,
                  environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_UNMASKING,
        compute=lambda _prev: unmask_payload(tree, producing_commit=commit),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 17

def unmasked_payload(tree: ModelTree, *, producing_commit: str
                     ) -> dict[str, Any]:
    freeze_record = load_freeze(tree)
    freeze = freeze_record["freeze"]
    unmask_record = transitions.read_stage_record(tree, C.STAGE_UNMASKING)
    if not unmask_record.get("unmasked"):
        raise ProtocolError("§20: the mask has not been lifted")
    rows = collect_rows(tree)
    table = observation_table(rows, m_draws=freeze["m_draws"])
    statuses = list(freeze_record["identification_statuses"])
    # §20: the fit's coefficients and delta_difficulty are post-unmasking, so
    # this is the one call that gets §11.7's family grouping.
    slot_families = {slot: (value[0] if isinstance(value, (list, tuple))
                            else value["kind"])
                     for slot, value in (freeze_record.get("slot_map")
                                         or {}).items()}
    estimates = estimate_all(
        table, statuses=statuses, arms=freeze["admitted_arms"],
        seed=seeds.bootstrap_seed("unmasked", tree.model_key),
        resamples=C.BOOTSTRAP_RESAMPLES, slot_families=slot_families)
    result = _strip_vectors(estimates)
    # §13.8's realised gaps and §13.6's realised interaction drift: two
    # qualifiers emit_l3 registers and that no caller supplied. Both are
    # measured quantities already on signed records --- the freeze's core
    # references carry each reference's iota, and Gate 2.5's interaction
    # report carries the drift statuses --- so the qualifier attaches when
    # the registered magnitude is exceeded rather than never.
    realised_gaps = {
        entry["slot"]: float(entry["iota"]) - float(freeze["iota_a"])
        for entry in (freeze.get("core_references") or ())
        if entry.get("iota") is not None and freeze.get("iota_a") is not None}
    interaction_drift = [status for status in statuses
                         if "INTERACTION" in status or "DRIFT" in status]
    # §3.2's L1 gate, measured rather than asserted: the outcome constraint
    # of D(B<-A) is B and of D(A<-B) is A, and each has headroom when its
    # realised solo compliance at the operating point leaves room to fall.
    headroom = {
        "D(B<-A)": _has_headroom(freeze.get("solo_compliance_b")),
        "D(A<-B)": _has_headroom(freeze.get("solo_compliance_a")),
    }
    statements = _statements(result, statuses=statuses,
                             measurement_basis=freeze["measurement_basis"],
                             near_form_available="NEAR_FORM_ARM_NOT_AVAILABLE"
                             not in statuses,
                             solo_headroom=headroom,
                             realised_gaps=realised_gaps,
                             interaction_drift=interaction_drift)
    success = support_stage.methodological_success(
        freeze["support_realised"], gate4_passed=True)
    # §34 D6: the last place an estimate could appear for a member Gate 3C
    # marked NOT_IDENTIFIED. `_licensed` already blocks them, so this asserts
    # the outcome of that rather than repeating it --- which is the point: a
    # future estimator added beside `estimate_all` is checked too.
    identification.assert_not_rehabilitated(
        {"estimands": result}, gate3c=freeze_record.get("non_identification"),
        where="§34 D6: UNMASKED_ANALYSIS")
    return {
        "stage": C.STAGE_UNMASKED_ANALYSIS,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_UNMASKED_ANALYSIS],
        "outcome": "PASS",
        "inputs": {"unmasking": {"stage": C.STAGE_UNMASKING},
                   "freeze": {"stage": C.STAGE_GATE5,
                              "freeze_hash": freeze_record["freeze_hash"]}},
        "producing_commit": producing_commit,
        "estimands": result,
        "statements": statements,
        "identification_statuses": statuses,
        "success_criterion": success,
        "measurement_basis": freeze["measurement_basis"],
        "scope_sentence": C.SCOPE_SENTENCE,
        "analysis_code_hash": analysis_code_hash(),
        "projection_audit": _projection_audit(table),
        # §18 step 14's raw-coordinate replication, surfaced beside
        # `projection_audit` rather than only inside `estimands`: §23 releases
        # it and the contract's reader is FINAL_REPORT, so the field the
        # reader reads is the field the contract can check is present.
        "raw_coordinate_secondary":
            result.get("raw_coordinate_secondary", {}),
        "spectrum_families": slot_families,
        "not_identified_is_not_zero":
            "a quantity the design does not identify is recorded "
            f"{NOT_IDENTIFIED} with the status that explains it, never as "
            "zero, a bare NaN, an omission or a substitute estimand",
    }


def _has_headroom(solo_compliance: float | None) -> bool:
    """§12: has the outcome constraint room to fall under composition?

    True when the realised solo compliance is above §13.14's
    composed-headroom floor: a constraint already at the floor cannot
    exhibit a loss, and §3.2's L1 gate is a statement about that. A record
    that does not carry the quantity cannot answer, and the gate is not
    asserted in its absence.
    """
    if solo_compliance is None:
        return False
    return float(solo_compliance) > C.COMPOSED_HEADROOM_BAND[0]


def _raw_coordinate_reading(result: Mapping[str, Any], configuration: str
                            ) -> dict[str, Any]:
    """The raw-coordinate replication, in the shape §17.6's rule reads.

    §15 gives it **marginal** intervals only, so the interval handed to the
    comparison is the marginal one --- which is the whole reason this cannot
    license a claim and can only attach a status.
    """
    entry = ((result.get("raw_coordinate_secondary") or {})
             .get("configurations", {}).get(configuration) or {})
    if entry.get("status") != "IDENTIFIED":
        return {"secondary": None, "secondary_support": None}
    lo, hi = entry["marginal_ci95"]
    return {"secondary": claims.Interval("delta_difficulty",
                                         entry["point"], lo, hi),
            "secondary_support": entry.get("support") or {}}


def _interval(result: Mapping[str, Any], family: str, configuration: str,
              member: str) -> claims.Interval | None:
    """One member's simultaneous interval, or None when it has none."""
    bucket = result.get("intervals", {}).get(f"{family}:{configuration}")
    if not isinstance(bucket, Mapping):
        return None
    entry = bucket.get(member)
    if not isinstance(entry, Mapping) or entry.get("estimate") is None:
        return None
    return claims.Interval(member, entry["estimate"], entry["lower"],
                           entry["upper"])


def _identified(bucket: Mapping[str, Any], member: str) -> bool:
    entry = bucket.get(member)
    return bool(entry) and entry.get("status") == "IDENTIFIED"


def _vacuity_gate_binds(result: Mapping[str, Any],
                        configuration: str) -> bool:
    """§17.4's F6 gate: does any vacuity-rate difference bind?

    "When every vacuity-rate difference is at or below 0.05 or its interval
    includes zero, the primary estimands are reported without qualification."
    """
    bucket = result.get("intervals", {}).get(f"F6:{configuration}")
    if not isinstance(bucket, Mapping) or bucket.get("interval", "") is None:
        return False
    for member, entry in bucket.items():
        if not isinstance(entry, Mapping) or entry.get("estimate") is None:
            continue
        if abs(entry["estimate"]) <= C.F6_VACUITY_GATE:
            continue
        if entry["lower"] <= 0.0 <= entry["upper"]:
            continue
        return True
    return False


def _heterogeneity_disagrees(result: Mapping[str, Any],
                             configuration: str) -> bool:
    """§15 F2's L3 heterogeneity qualifier.

    The three Delta_j intervals do not agree on one side of the threshold
    used: §11.4's registered smallest effect of interest, which is the
    threshold every L3 sub-level reads.
    """
    sides = set()
    for index in range(1, len(C.CORE_SLOTS) + 1):
        interval = _interval(result, "F2", configuration, f"Delta_{index}")
        if interval is None:
            return False
        if interval.lower > C.DELTA_R_GENERIC_THRESHOLD:
            sides.add("above")
        elif interval.upper < C.DELTA_R_GENERIC_THRESHOLD:
            sides.add("below")
        else:
            sides.add("straddles")
    return len(sides) > 1


def _projection_audit(table: ObservationTable) -> list[dict[str, Any]]:
    """§23 and §18 step 17: the realised projection against what happened.

    §13.6 admits a candidate on a **projected** composed compliance
    ``p_hat_c = kappa(c|B) + iota_c (1 - kappa(c|B))``, formed before any
    composed cell exists. §31 registers the prospective record of that
    projection: p_hat_c against the realised composed compliance, per
    companion per composed cell, with the absolute error. The field existed
    on both the analysis and the final-report records and was the empty list
    on every path, so the one registered check on §13.6's admission rule
    reported nothing.
    """
    from dci1v6.stages.calibration_table import instructed_compliance

    audit: list[dict[str, Any]] = []
    companions = [slot for slot in table.slots() if slot != "B"]
    for slot in sorted(set(companions)):
        if not table.has_kappa_under_b(slot):
            continue
        try:
            kappa_b = estimators.counterfactual_chance(table, slot)
            solo = estimators.solo_vector(table, slot)
            chance = estimators.chance_vector(table, slot)
        except (IntegrityError, ProtocolError):
            continue
        iota = [instructed_compliance(s, k) for s, k in zip(solo, chance)]
        projected = estimators.projected_compliance_vector(kappa_b, iota)
        displacement = estimators.displacement_vector(chance, kappa_b)
        for configuration in C.CONFIGURATIONS:
            if not table.has_composed(slot, "B", configuration):
                continue
            realised = estimators.composed_vector(table, slot, "B",
                                                  configuration)
            errors = [abs(p - r) for p, r in zip(projected, realised)]
            errors_sorted = sorted(errors)
            audit.append({
                "companion": slot, "configuration": configuration,
                "cell": f"pair:B+{slot}",
                "projected_mean": sum(projected) / len(projected),
                "realised_mean": sum(realised) / len(realised),
                "displacement_mean": (sum(displacement)
                                      / len(displacement)),
                "absolute_error_mean": sum(errors) / len(errors),
                "absolute_error_median":
                    errors_sorted[len(errors_sorted) // 2],
                "absolute_error_max": max(errors),
                "n_blocks": len(errors),
                "allowance": C.PROJECTION_ERROR_ALLOWANCE,
                "within_allowance": (sum(errors) / len(errors)
                                     <= C.PROJECTION_ERROR_ALLOWANCE),
                "reading": "§13.6's projection is an ADMISSION quantity and "
                           "this is its prospective record; it licenses no "
                           "claim and revises no admission",
            })
    return audit


def _statements(result: Mapping[str, Any], *, statuses: Sequence[str],
                measurement_basis: str, near_form_available: bool,
                solo_headroom: Mapping[str, bool] | None = None,
                realised_gaps: Mapping[str, float] | None = None,
                interaction_drift: Sequence[str] = ()
                ) -> list[dict[str, Any]]:
    """§17.5's guarded emitters, applied per configuration, in §18's order.

    Only ``emit_l1`` had a production caller: L2, L3, L4a and L4b were
    implemented, tested and unreachable, so the lifecycle could not emit
    Delta_R's claim --- the study's central registered question --- on any
    data. Each emitter is called here with the inputs §3.2 and §17 register
    for it, and each still enforces its own preconditions: a caller now
    exists, and nothing about what licenses a claim changed.

    An estimand the design did not identify never reaches an emitter: the
    emitter is guarded, but a guard that is only ever reached with a real
    interval is a guard that has never been tested, and the record says which
    members were withheld rather than leaving the reader to notice.
    """
    out: list[dict[str, Any]] = []
    references_identified = (
        "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in set(statuses)
        and "EXCESS_NOT_IDENTIFIED" not in set(statuses))
    classifications: dict[str, dict[str, str | None]] = {
        member: {} for member in claims.LEVEL_MEMBERS["L4a"]}

    for configuration, bucket in result["configurations"].items():
        position = 1 if configuration == C.OUTCOME_FIRST else 2
        gate_binds = _vacuity_gate_binds(result, configuration)
        reached: dict[str, str | None] = {
            member: None for member in claims.LEVEL_MEMBERS["L4a"]}

        # ------------------------------------------------------------- L1
        l1_licensed: dict[str, bool] = {}
        for member in claims.LEVEL_MEMBERS["L1"]:
            interval = _interval(result, "F1", configuration, member)
            if not _identified(bucket, member) or interval is None:
                l1_licensed[member] = False
                continue
            forced = _interval(result, "F5", configuration,
                               f"{member}|vacuity_forced")
            statement = claims.emit_l1(
                configuration=configuration, cell="pair:A+B",
                outcome_position=position,
                measurement_basis=measurement_basis, member=member,
                interval=interval,
                solo_headroom=(solo_headroom or {}).get(member, True),
                identification_statuses=statuses,
                vacuity_forced=forced, vacuity_gate_binds=gate_binds)
            out.append(statement)
            l1_licensed[member] = bool(statement.get("emitted"))
            if statement.get("emitted"):
                reached[member] = "L1"

        # ------------------------------------------------------------- L2
        interval = _interval(result, "F1", configuration, "Lambda")
        if _identified(bucket, "Lambda") and interval is not None:
            statement = claims.emit_l2(
                configuration=configuration, cell="pair:A+B",
                outcome_position=position,
                measurement_basis=measurement_basis, interval=interval,
                l1_licensed=l1_licensed, identification_statuses=statuses,
                vacuity_forced=_interval(result, "F5", configuration,
                                         "Lambda|vacuity_forced"),
                vacuity_gate_binds=gate_binds)
            out.append(statement)
            if statement.get("emitted"):
                reached["Lambda"] = "L2"

        # ------------------------------------------------------------- L3
        delta_r = _interval(result, "F1", configuration, "Delta_R")
        delta_difficulty = _interval(result, "F1", configuration,
                                     "delta_difficulty")
        xi = _interval(result, "F1", configuration, "Xi")
        support = (bucket.get("delta_difficulty") or {}).get("support") or {}
        # §17.6 row 5: when the difficulty support fails, "the local reading
        # stands alone with that status --- L3a/L3b/L3c only". delta_r and Xi
        # are what L3 needs; delta_difficulty may be absent, and the emitter
        # reads its absence as the registered row rather than as a reason to
        # emit nothing. §8.1 registers exactly this: a replication that cannot
        # identify the spectrum still estimates Delta_R, Delta_j and Xi.
        if delta_r is not None and xi is not None:
            forced_r = _interval(result, "F5", configuration,
                                 "Delta_R|vacuity_forced")
            # §17.6's coordinate-agreement rule, closed by §34 D14. The raw
            # replication decides only whether the statement carries
            # DIFFICULTY_COORDINATE_DEPENDENT; the registered coordinate
            # decides which classification is emitted.
            agreement = claims.coordinate_agreement(
                delta_difficulty=delta_difficulty, support=support,
                **_raw_coordinate_reading(result, configuration))
            l3 = claims.emit_l3(
                configuration=configuration, cell="pair:A+B",
                outcome_position=position,
                measurement_basis=measurement_basis, delta_r=delta_r,
                delta_difficulty=delta_difficulty, xi=xi, support=support,
                references_identified=references_identified,
                delta_near=_interval(result, "F9", configuration,
                                     "Delta_near"),
                near_form_available=near_form_available,
                heterogeneity_disagrees=_heterogeneity_disagrees(
                    result, configuration),
                realised_gaps=realised_gaps,
                interaction_drift=interaction_drift,
                vacuity_forced_agrees=claims.l3_vacuity_agrees(
                    delta_r, forced_r),
                coordinate_statuses=agreement["statuses"])
            for statement in l3:
                statement["coordinate_agreement"] = agreement
            out.extend(l3)
            for statement in l3:
                if not statement.get("emitted"):
                    continue
                level = statement["claim_level"]
                member = claims.LEVEL_MEMBERS.get(level, ("",))[0]
                if member in reached:
                    reached[member] = level
        classifications = {
            member: {**classifications[member], configuration: reached[member]}
            for member in classifications}

    # -------------------------------------------------------------- L4a
    out.append(claims.emit_l4a(per_member=classifications,
                               measurement_basis=measurement_basis,
                               identification_statuses=statuses))

    # -------------------------------------------------------------- L4b
    analysed = set(result["configurations"]) == set(C.CONFIGURATIONS)
    cross = result.get("cross_configuration", {})
    for member in claims.LEVEL_MEMBERS["L4b"]:
        interval = _interval(result, "F11", "cross", member)
        if not _identified(cross, member) or interval is None:
            continue
        out.append(claims.emit_l4b(
            member=member, interval=interval,
            measurement_basis=measurement_basis,
            both_configurations_analysed=analysed,
            identification_statuses=statuses))
    return out


def run_unmasked_analysis(tree: ModelTree,
                          *, producing_commit: str | None = None,
                          environment_digest: str = "") -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    return run_stage(
        tree, C.STAGE_UNMASKED_ANALYSIS,
        compute=lambda _prev: unmasked_payload(tree, producing_commit=commit),
        producing_commit=commit, environment_digest=environment_digest)


# ------------------------------------------------------------ stage 18

def final_report_payload(tree: ModelTree, *, producing_commit: str,
                         repo_root: Path | str | None = None
                         ) -> dict[str, Any]:
    """§31's machine-readable table, from signed records only.

    Then stage 18's own checks (``run/final_report_checks.py``): the §33 items
    the pre-freeze audit deferred, plus every traceability claim that only
    becomes checkable once the table exists. A mandatory failure records
    ``outcome`` ``FAIL`` --- ``FINAL_REPORT`` has no successor to refuse, so
    the failure has to be on the record itself.
    """
    freeze_record = load_freeze(tree)
    analysis = transitions.read_stage_record(tree, C.STAGE_UNMASKED_ANALYSIS)
    hashes = {stage: sha_obj(transitions.read_stage_record(tree, stage))
              for stage in C.STAGE_SEQUENCE
              if tree.stage_record(stage).exists()}
    rows = _report_rows(tree, analysis, freeze_record,
                        hashes[C.STAGE_UNMASKED_ANALYSIS])
    report = final_report_stage.build_final_report(
        model_key=tree.model_key, rows=rows,
        statements=analysis["statements"],
        success_criterion=analysis["success_criterion"],
        identification_statuses=analysis["identification_statuses"],
        admitted_arms=freeze_record["admitted_arms"],
        projection_audit=analysis.get("projection_audit", ()),
        raw_coordinate_secondary=analysis.get("raw_coordinate_secondary"),
        stage_record_hashes=hashes)
    root = repo_root if repo_root is not None else tree.context.repo_root
    checks = final_report_checks.final_report_checks(tree, report,
                                                     repo_root=root)
    failed = [c for c in checks if c["mandatory"] and c["verdict"] != "PASS"]
    return {
        **report,
        "stage": C.STAGE_FINAL_REPORT,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_FINAL_REPORT],
        "outcome": "PASS" if not failed else "FAIL",
        "failure_status": None if not failed
        else final_report_checks.FINAL_REPORT_FAILURE,
        "inputs": {"unmasked": {"stage": C.STAGE_UNMASKED_ANALYSIS},
                   "freeze": {"stage": C.STAGE_GATE5}},
        "producing_commit": producing_commit,
        "final_report_checks": checks,
        "n_final_report_checks": len(checks),
        "n_final_report_passed": sum(1 for c in checks
                                     if c["verdict"] == "PASS"),
        "blocked": [c["check"] for c in failed],
        "traceability":
            "every number traces to a v5 stage record and its hash; no v4r4 "
            "outcome is presented as a v5 observation (§30)",
    }


#: §31's per-row claim level: the level a member's estimate **is registered
#: to**, from §3.2's ladder. Every per-configuration row carried "L1" and
#: every cross row carried "L4b", so F4's matrix components and F2's
#: companion losses were released as L1 estimates. A member registered to no
#: level is Secondary in §15's own word, and so is a member registered to a
#: level it did not reach: the row's claim level is what the emitted
#: statements say it reached, and `None` where they say nothing. That is a
#: fact about the estimate, not a missing field. This map records which level
#: each member is REGISTERED to, which is a different statement and is what
#: the emitters enforce.
CLAIM_LEVEL_OF_MEMBER: dict[str, str] = {
    "D(B<-A)": "L1", "D(A<-B)": "L1", "Lambda": "L2",
    "Delta_R": "L3", "delta_difficulty": "L3",
    **{member: "L4b" for member in C.FAMILY_MEMBERS["F11"]},
}


def _levels_reached(statements: Sequence[Mapping[str, Any]]
                    ) -> dict[tuple[str, str], str]:
    """The level each member actually reached, per configuration.

    §31 releases each estimate **with its claim level**, and the level a
    member reached is a result of the run --- L3a and L3c are different
    findings about the same member. It is read off the emitted statements
    rather than mapped from the member name, so the table and the statements
    cannot disagree.
    """
    out: dict[tuple[str, str], str] = {}
    for statement in statements:
        if not statement.get("emitted"):
            continue
        level = statement.get("claim_level")
        if level not in C.CLAIM_LEVELS:
            continue
        members = ([statement["member"]] if statement.get("member")
                   else list(claims.LEVEL_MEMBERS.get(level, ())))
        for configuration in str(statement.get("configuration", "")).split(
                "|") or [""]:
            for member in members:
                out[(member, configuration)] = level
    return out


def _pair(slots: Sequence[str]) -> str:
    """A composed cell's name, in §8.4's registered slot order, so that
    D(R1<-A) and D(A<-R1) name the one cell they were both read from."""
    order = {slot: index
             for index, slot in enumerate(C.REGISTERED_SLOT_ORDER)}
    return "pair:" + "+".join(sorted(slots,
                                     key=lambda s: (order.get(s, 99), s)))


def _cell_of_member(member: str) -> str:
    """§17.5's cell: the composed cell the member's composed term was read
    from, not the primary pair for every row in the table."""
    # F6's `|` is the conditional bar inside `vac(B|B+R1)` and F5's separates
    # a member from its variant. The vacuity names are matched whole, before
    # anything splits on the bar.
    if member.startswith("vac(B|B+") and member.endswith(")-vac(B solo)"):
        return _pair(["B", member[len("vac(B|B+"):-len(")-vac(B solo)")]])
    if member.startswith("vac(B|A+B)"):
        return _pair(["A", "B"])
    stem = member.split("|", 1)[0]
    if stem.startswith("D(") and "<-" in stem and stem.endswith(")"):
        outcome, _, companion = stem[2:-1].partition("<-")
        if "Rbar" in (outcome, companion):
            other = companion if outcome == "Rbar" else outcome
            return f"mean over the three pair:{other}+R_j cells"
        return _pair([outcome, companion])
    if stem in C.FAMILY_MEMBERS["F11"]:
        return "cross-configuration composed pair"
    if stem in ("beta", "alpha_1", "alpha_2", "alpha_3", "gamma_tier"):
        return "the §11.8 fit over the composed cells of the ladder"
    return "contrast over the composed cells of the admitted arms"


def _report_rows(tree: ModelTree, analysis: Mapping[str, Any],
                 freeze_record: Mapping[str, Any],
                 analysis_hash: str) -> list[dict[str, Any]]:
    """§31's table: one row per (member, configuration), withheld ones too.

    Every one of ``final_report.ROW_FIELDS`` is filled from a signed record.
    An earlier revision emitted six of the twenty-one and the stage refused
    the table, which is the check working: §31 lists what the released table
    carries and a row that omits its standard error, its bounds or its
    provenance is not that table.
    """
    freeze = freeze_record["freeze"]
    confirmatory = transitions.read_stage_record(tree, C.STAGE_CONFIRMATORY)
    rows: list[dict[str, Any]] = []
    statuses = ";".join(analysis["identification_statuses"]) or "none"
    family_of = {member: family
                 for family, members in C.FAMILY_MEMBERS.items()
                 for member in members}
    estimands = analysis["estimands"]
    intervals = estimands.get("intervals") or {}

    # ------------------------------------------------- the row-wide context
    coordinate = {
        "primary": freeze["difficulty_coordinate_definition"],
        "iota_a": freeze.get("iota_a"),
        "solo_compliance_a": freeze.get("solo_compliance_a"),
        "m_star": freeze["m_star"], "n_star": freeze["n_star"]}
    tiers = sorted({int(e["structural_tier"])
                    for e in (freeze.get("core_references") or ())
                    if e.get("structural_tier") is not None})
    # §16.1's decomposition as the freeze bound it. phi splits a cell's
    # variance into a topic and a draw part, and the draw part needs
    # draw-level data that §14.1 keeps out of the analysis on purpose --- so
    # the realised decomposition is the freeze's, with its source named, and
    # the realised *dispersion* is the bootstrap standard error on each row.
    variance = dict(freeze["variance_reestimate"])
    counts = {"blocks": confirmatory["blocks"],
              "cells_per_block": confirmatory["cells_per_block"],
              "draws_per_cell": confirmatory["draws"],
              "rows": confirmatory["n_rows"]}

    def row(member: str, configuration: str, claim_level: str,
            entry: Mapping[str, Any], family: str) -> dict[str, Any]:
        key = f"{family}:{configuration}"
        interval = (intervals.get(key) or {}).get(member) or {}
        half_width = interval.get("half_width")
        precondition = C.PRECISION_PRECONDITIONS.get(
            claims.precondition_key(member))
        return {
            "member": member, "configuration": configuration,
            "cell": _cell_of_member(member), "claim_level": claim_level,
            "family": family,
            "identification_status": (entry.get("reason")
                                      if entry["status"] == NOT_IDENTIFIED
                                      else statuses),
            "status": entry["status"],
            "measurement_basis": freeze["measurement_basis"],
            "difficulty_coordinate": coordinate,
            "structural_tier_of_reference_pool": tiers,
            "point": entry.get("point"),
            "estimate": interval.get("estimate", entry.get("point")),
            "standard_error": interval.get("standard_error"),
            "marginal_lower": interval.get("marginal_lower"),
            "marginal_upper": interval.get("marginal_upper"),
            "simultaneous_lower": interval.get("lower"),
            "simultaneous_upper": interval.get("upper"),
            "realised_half_width": half_width,
            "variance_decomposition": variance,
            # §16.3 reads the realised simultaneous half-width as the
            # magnitude the design resolves --- a half-width of 0.0452
            # resolves an order contrast above about 0.045 --- so the
            # achieved detectable effect *is* that half-width, and the
            # derivation travels with it rather than being asserted.
            "achieved_detectable_effect": {
                "value": half_width,
                "derivation": "§16.3: the realised simultaneous half-width "
                              "is the magnitude at which the interval "
                              "excludes zero",
                "precondition": precondition,
                "met": (None if half_width is None or precondition is None
                        else half_width <= precondition)},
            "cell_counts": counts,
            "source_stage": C.STAGE_UNMASKED_ANALYSIS,
            "stage_record": C.STAGE_UNMASKED_ANALYSIS,
            "stage_record_hash": analysis_hash,
            "freeze_hash": freeze_record["freeze_hash"]}

    reached = _levels_reached(analysis.get("statements") or ())
    for configuration, bucket in estimands["configurations"].items():
        for member, entry in sorted(bucket.items()):
            rows.append(row(
                member, configuration,
                reached.get((member, configuration)),
                entry, family_of.get(member, "unassigned")))
    for member, entry in sorted(estimands["cross_configuration"].items()):
        rows.append(row(
            member, "cross",
            reached.get((member, "cross")),
            entry, family_of.get(member, "F11")))
    return rows


def run_final_report(tree: ModelTree, *, producing_commit: str | None = None,
                     environment_digest: str = "",
                     repo_root: Path | str | None = None) -> StageOutcome:
    """Stage 18. A mandatory check failing raises, **after** the record.

    Every other stage's failure is enforced by its successor refusing to run.
    Stage 18 has no successor, so the record is written first --- it is the
    evidence of what failed and it must survive --- and the failure is then
    raised so no caller mistakes a failed report for a finished study.
    """
    commit = producing_commit or gitinfo.head_commit(
        Path(tree.context.repo_root))
    outcome = run_stage(
        tree, C.STAGE_FINAL_REPORT,
        compute=lambda _prev: final_report_payload(
            tree, producing_commit=commit, repo_root=repo_root),
        producing_commit=commit, environment_digest=environment_digest)
    if outcome.payload.get("outcome") != "PASS":
        raise IntegrityError(
            f"{tree.model_key}: {C.STAGE_FINAL_REPORT} recorded "
            f"{outcome.payload['outcome']!r}; the mandatory checks "
            f"{outcome.payload['blocked']} did not pass and the report does "
            "not establish its own traceability")
    return outcome
