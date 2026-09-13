"""Stage 6, ``CONFIRMATORY_ANALYSIS``: the registered estimators, per frame.

For every entering frame the frame's rows become one ``ObservationTable``
(``dci1v7.analysis.observations``: one cell mean per (cell, constituent)
over all M draws, block-indexed and nothing else), and v7's estimators
form every registered contrast **inside a block**; the block bootstrap
(``dci1v7.analysis.bootstrap.bootstrap_family``) resamples that frame's
blocks and gives each family its studentised maximum-modulus critical
value; the boundary allowance (``dci1v7.analysis.boundary``) widens the
decision interval in the open direction where a constituent cell sits at
an exact boundary; ``claims.delta_r_reading`` and friends read the
intervals against the registered thresholds.

What frame conditioning adds --- the **joint family** --- is the one new
statistic: per configuration, every F1 member of every entering frame is
resampled **by topic** with one draw shared across frames (the same topic
underlies each frame's block), and the maximum-modulus over all of them is
the joint critical value. The decision interval of every primary claim is
the joint one; the per-frame F1 interval is beside it. A model-level LOCAL
verdict is the conjunction over entering frames (``precision.
MULTIPLICITY_RULE``). The pre-registered reference-sensitivity family
re-forms Delta_R(f) over every admissible triple of {R1..R5} and is
reported with its own simultaneous interval; it licenses no claim.

**Every v7 gate that survives frame conditioning runs here, per frame.**
This layer has no claim emitters --- there is no analyst decision point for
a mask to protect and nothing is emitted as a statement --- but the
*guards* the emitters carried are what decides what a number means, so
each is a reading on the frame's payload: §3.2's L1 solo-headroom gate and
the L2 precondition that reads it; §3.2's Xi direction gate on the wording
of Delta_R; §15 F2's within-frame heterogeneity qualifier; §17.4's F5
recodings, F6 vacuity-rate family and both-bounds rule; §23's projection
audit of §13.6's admission quantity against the realised composed rate;
§34 D6's identification ledger, which records **every** registered member
as ESTIMATED, NOT_ASKED or NOT_IDENTIFIED so that an absent member cannot
be a silent omission; L4a's per-member cross-configuration consistency;
and §26's methodological success criterion restated for a frame-
conditioned design. F7's reciprocal losses and the runner-up sensitivity
contrast are descriptive families with their own simultaneous intervals
and license nothing.

Nothing here chooses: every threshold is the frozen one, every input is
asserted against the freeze hash, and the stage runs once.
"""
from __future__ import annotations

import math
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci1v4.engine import fs, gitinfo
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import get_model
from dci1v7.analysis import boundary as B
from dci1v7.analysis import claims as CL
from dci1v7.analysis import estimators as E
from dci1v7.analysis import spectrum as SP
from dci1v7.analysis.bootstrap import (FamilyResult, bootstrap_family,
                                       sidak_critical)
from dci1v7.analysis.observations import ObservationTable, build_observations
from dci1v7.protocol import constants as C

from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.design import cell_types, normalise_arms
from dci1v8dev.confirm.freeze import load_freeze
from dci1v8dev.confirm.generation import collect_rows
from dci1v8dev.run.seeds import bootstrap_seed

__all__ = ["frame_table", "assert_frame_table", "frame_members",
           "spectrum_input", "delta_r_over", "delta_r_against",
           "joint_members", "analyse_model", "analysis_payload",
           "run_analysis", "MODEL_VERDICTS", "local_model_verdict",
           "LEDGER_STATUSES", "F5_RECODINGS", "F5_MEMBERS",
           "b_companions", "solo_headroom", "l1_gate", "lambda_gate",
           "reference_heterogeneity", "vacuity_gate_binds",
           "projection_audit", "frame_expectations", "identification_ledger",
           "assert_every_member_ledgered", "l4a_consistency",
           "methodological_success", "L3C_DISPOSITION", "RefitCounter",
           "apply_degenerate_ceiling"]

MODEL_VERDICTS = ("LOCAL_SUPPORTED_L3a", "LOCAL_SUPPORTED_L3b",
                  "LOCAL_EQUIVALENT_SAME_FORM_ONLY", "FRAME_HETEROGENEOUS",
                  "INSUFFICIENT_PRECISION", "INDETERMINATE",
                  "UNIDENTIFIED")
#: §34 D18, closed at ``precondition``, applied to a design with no
#: near-form arm (``freeze.DEVIATIONS``): an L3c-level Delta_R reading is
#: reported and the **strong** refutation verdict is unreachable, so the
#: model verdict never carries ``LOCAL_EQUIVALENT_L3c``.
L3C_DISPOSITION = "NEAR_FORM_UNAVAILABLE"

#: §34 D6's three statuses. A registered member is estimated, or the frame
#: was never asked for it (no such arm), or the arm exists and the member
#: could not be formed --- and the third is not the second.
LEDGER_STATUSES = ("ESTIMATED", "NOT_ASKED", "NOT_IDENTIFIED")

#: §15 F5's two draw-level recodings, as suffix -> the ``Observation`` field
#: the estimand is recomputed on. ``observations.build_observations`` forms
#: both at DRAW level (a vacuous pass counts as a failure; each draw's graded
#: score is thresholded at 0.99), so neither is a re-thresholded cell mean.
F5_RECODINGS: dict[str, str] = {"vacuity_forced": "non_vacuous_compliance",
                                "graded_0.99": "graded_threshold"}
#: Which F1 members each recoding recomputes (§15's table).
F5_MEMBERS: dict[str, tuple[str, ...]] = {
    "vacuity_forced": C.FAMILY_MEMBERS["F1"],
    "graded_0.99": ("D(B<-A)", "Delta_R", "delta_difficulty")}
#: F5's vector members, as base member -> the estimator under a named scale.
_F5_ESTIMATORS: dict[str, Callable[..., Any]] = {
    "D(B<-A)": lambda t, cfg, *, scale: E.delivery_loss(t, "B", "A", cfg,
                                                        scale=scale),
    "D(A<-B)": lambda t, cfg, *, scale: E.delivery_loss(t, "A", "B", cfg,
                                                        scale=scale),
    "Lambda": lambda t, cfg, *, scale: E.asymmetry(t, cfg, scale=scale),
    "Delta_R": lambda t, cfg, *, scale: E.delta_r(t, cfg, scale=scale),
    "Xi": lambda t, cfg, *, scale: E.xi(t, cfg, scale=scale)}


# ------------------------------------------------------------------ tables
def frame_table(rows: Sequence[Mapping[str, Any]], frame: int, *,
                m_draws: int) -> ObservationTable:
    frows = [dict(r) for r in rows if int(r.get("block_frame", -1)) == frame]
    if not frows:
        raise IntegrityError(f"no confirmatory rows for frame {frame}")
    return ObservationTable(build_observations(frows, m_draws=m_draws))


def assert_frame_table(table: ObservationTable, *, arms: Sequence[str],
                       n_spectrum: int, blocks_expected: int,
                       runner_up: Sequence[str] = ()) -> dict[str, Any]:
    """Every block carries exactly the frozen cell set (the within-block
    guarantee, on the confirmatory rows)."""
    expected = cell_types(normalise_arms(arms), n_spectrum=n_spectrum,
                          runner_up=runner_up)
    missing: list[str] = []
    for block in table.blocks:
        for cell in expected:
            if cell.arm == "unconstrained":
                continue
            if cell.arm == "solo":
                try:
                    table.solo(block, cell.slots[0])
                except IntegrityError:
                    missing.append(f"{cell.cell_id}@{block}")
                continue
            first, second = cell.slots
            for outcome, companion in ((first, second), (second, first)):
                cfg = C.OUTCOME_FIRST if outcome == first else C.OUTCOME_SECOND
                if not table.has_composed(outcome, companion, cfg):
                    missing.append(f"{outcome}+{companion}:{cfg}@{block}")
    if missing:
        raise IntegrityError(f"{len(missing)} cell(s) missing from the "
                             f"within-block set, first: {missing[0]}")
    if len(table.blocks) != blocks_expected:
        raise ProtocolError(f"{len(table.blocks)} blocks, expected "
                            f"{blocks_expected}")
    return {"blocks": len(table.blocks), "cells_per_block":
            len(table.observations) // len(table.blocks),
            "cross_block_terms": 0}


# -------------------------------------------------------------- estimators
def delta_r_against(table: ObservationTable, slots: Sequence[str],
                    alternative: str, configuration: str) -> list[float]:
    """``mean_j p(O | O+R_j) - p(O | O+alternative)`` in the cancelled form,
    where ``O`` is ``B`` for the frozen and the A2 contrasts and ``B2`` for
    the runner-up-m contrast (the outcome is whatever the alternative
    replaces). The solo baseline cancels exactly as it does in Delta_R."""
    outcome = "B2" if alternative == "A" else "B"
    with_refs = E.mean_vectors([E.composed_vector(table, outcome, r,
                                                  configuration)
                                for r in slots])
    with_alt = E.composed_vector(table, outcome, alternative, configuration)
    return [r - a for r, a in zip(with_refs, with_alt)]


def delta_r_over(table: ObservationTable, slots: Sequence[str],
                 configuration: str) -> list[float]:
    """Delta_R re-formed over an arbitrary reference triple (the
    reference-sensitivity family); the cancelled form."""
    with_refs = E.mean_vectors([E.composed_vector(table, "B", r, configuration)
                                for r in slots])
    with_a = E.composed_vector(table, "B", "A", configuration)
    return [r - a for r, a in zip(with_refs, with_a)]


def b_companions(frozen: Mapping[str, Any]) -> tuple[str, ...]:
    """Every slot the FROZEN design puts beside B in a composed cell.

    Derived from the frozen arms rather than from the realised table, so a
    companion whose cells are missing is a NOT_IDENTIFIED member and not an
    absence nobody notices.
    """
    types = cell_types(normalise_arms(frozen["arms"]),
                       n_spectrum=int(frozen["n_spectrum_slots"]),
                       runner_up=tuple(frozen.get("runner_up_slots") or ()))
    out: list[str] = []
    for t in types:
        if t.arm != "composed" or "B" not in t.slots:
            continue
        other = t.slots[0] if t.slots[1] == "B" else t.slots[1]
        if other not in out:
            out.append(other)
    return tuple(out)


def spectrum_input(table: ObservationTable, frozen: Mapping[str, Any],
                   configuration: str, *, scale: str = E.PRIMARY_SCALE
                   ) -> SP.SpectrumInput | None:
    """§11.7's points for this frame, on ``scale``.

    ``scale`` is F5's recoding: §17.4 recomputes the *estimand*, so the
    whole relation is refitted on the recoded cell means rather than the
    primary residual being rescaled.
    """
    points = frozen.get("spectrum_points") or []
    if not points:
        return None
    family_of = {p["slot"]: p["family"] for p in points}
    for s in family_of:
        if not table.has_composed("B", s, configuration):
            return None
    if not table.has_composed("B", "A", configuration):
        return None
    b_with = {s: E.composed_vector(table, "B", s, configuration, scale=scale)
              for s in family_of}
    b_with["A"] = E.composed_vector(table, "B", "A", configuration, scale=scale)
    return SP.SpectrumInput(
        blocks=tuple(table.blocks), family_of=family_of,
        b_solo=E.solo_vector(table, "B", scale=scale), b_with=b_with,
        companion_solo={s: E.solo_vector(table, s, scale=scale)
                        for s in family_of},
        companion_chance={s: E.chance_vector(table, s, scale=scale)
                          for s in family_of},
        a_solo=E.solo_vector(table, "A", scale=scale),
        a_chance=E.chance_vector(table, "A", scale=scale))


class RefitCounter:
    """What each refit of a bootstrapped spectrum member did.

    §13.13's ``DEGENERATE_REPLICATE_MAX`` is a ceiling on the share of
    replicates whose refit was not the registered one --- the fit was not
    available, or a point was dropped because its chance rate reached
    ``CHANCE_DEGENERACY_MAX`` and iota is undefined there. The closure form
    the block bootstrap needs hides that, so the closure reports it here and
    the caller enforces the ceiling on the realised bootstrap.
    """

    __slots__ = ("calls", "unavailable", "dropped")

    def __init__(self) -> None:
        self.calls = self.unavailable = self.dropped = 0

    def observe(self, estimate: Mapping[str, Any]) -> None:
        self.calls += 1
        if self.calls == 1:
            return          # the point estimate, which is not a replicate
        if estimate.get("degenerate"):
            self.unavailable += 1
        elif estimate.get("dropped_points"):
            self.dropped += 1

    def record(self, resamples: int) -> dict[str, Any]:
        n = max(1, int(resamples))
        share = (self.unavailable + self.dropped) / n
        return {"replicates": self.calls - 1, "resamples": resamples,
                "fit_unavailable": self.unavailable,
                "dropped_a_point": self.dropped,
                "degenerate_replicate_share": share,
                "ceiling": C.DEGENERATE_REPLICATE_MAX,
                "status": ("DEGENERATE_REPLICATES"
                           if share > C.DEGENERATE_REPLICATE_MAX else "OK")}


def frame_members(table: ObservationTable, frozen: Mapping[str, Any],
                  configuration: str) -> dict[str, dict[str, Any]]:
    """Every registered member this frame supports, by family, as per-block
    vectors or refit callables."""
    local = bool(frozen["enters_local"])
    spectrum = bool(frozen["enters_spectrum"])
    fam: dict[str, dict[str, Any]] = {}
    f1: dict[str, Any] = {
        "D(B<-A)": E.delivery_loss(table, "B", "A", configuration),
        "D(A<-B)": E.delivery_loss(table, "A", "B", configuration),
        "Lambda": E.asymmetry(table, configuration)}
    if local:
        f1["Delta_R"] = E.delta_r(table, configuration)
        f1["Xi"] = E.xi(table, configuration)
        refs = E.reference_slots(table)
        fam["F2"] = {**{f"D(B<-{r})": E.delivery_loss(table, "B", r, configuration)
                        for r in refs},
                     **{f"Delta_{i + 1}": E.delta_j(table, r, configuration)
                        for i, r in enumerate(refs)}}
        fam["F3"] = {**{f"D(A<-{r})": E.delivery_loss(table, "A", r, configuration)
                        for r in refs},
                     "Delta^A": E.delta_a(table, configuration)}
        fam["F4"] = {"D(Rbar<-A)": E.d_rbar_from(table, "A", configuration),
                     "D(Rbar<-B)": E.d_rbar_from(table, "B", configuration),
                     "D(Rbar<-Rbar')": E.d_rbar_rbar(table, configuration)}
        sens = frozen.get("reference_sensitivity") or {}
        fam["F_REFSENS"] = {
            "Delta_R[" + "+".join(t["slots"]) + "]":
                delta_r_over(table, t["slots"], configuration)
            for t in sens.get("admissible_triples", ())}
        # §15 F7: the reciprocal losses, from the core cells the frame
        # already carries. Descriptive: they say what B and A cost the
        # references, which is the other half of every F2/F3 pair, and they
        # license no claim level.
        fam["F7"] = {}
        for r in refs:
            for g in ("B", "A"):
                fam["F7"][f"D({r}<-{g})"] = E.delivery_loss(table, r, g,
                                                            configuration)
        # The runner-up sensitivity contrast, when the frozen operating
        # point was OPERATING_POINT_UNSTABLE on a coordinate. Descriptive:
        # the frozen n*(f), m*(f) stand and this licenses nothing.
        runner_up: dict[str, Any] = {}
        for slot in tuple(frozen.get("runner_up_slots") or ()):
            if slot == "A2":
                runner_up["Delta_R[A2]"] = delta_r_against(table, refs, "A2",
                                                           configuration)
            elif slot == "B2":
                runner_up["Delta_R[B2]"] = delta_r_against(table, refs, "A",
                                                           configuration)
        if runner_up:
            fam["F_RUNNER_UP"] = runner_up
    if spectrum:
        data = spectrum_input(table, frozen, configuration)
        if data is not None:
            f1["delta_difficulty"] = (lambda picks, d=data:
                                      float(SP.estimate(d, picks)["delta_difficulty"]))
            counter = RefitCounter()

            def _slope(picks, d=data, c=counter):
                est = SP.estimate(d, picks)
                c.observe(est)
                return float(est.get("slope", float("nan")))

            fam["F_SPECTRUM"] = {"slope": _slope}
            fam["_spectrum_point"] = {"data": data, "refits": counter}
    fam["F1"] = f1
    # ------------------------------------------------------------- F5, F6
    # §17.4's two halves. F5 recomputes the primary estimands on the two
    # draw-level recodings; F6 is the vacuity-rate difference between each
    # composed cell containing B and the B solo cell, and it is F6 that
    # GATES §17.4's reporting rule.
    f5: dict[str, Any] = {}
    for suffix, scale in sorted(F5_RECODINGS.items()):
        for base in F5_MEMBERS[suffix]:
            if base not in f1:
                continue                # the frame was not asked for it
            member = f"{base}|{suffix}"
            if base == "delta_difficulty":
                recoded = spectrum_input(table, frozen, configuration,
                                         scale=scale)
                if recoded is None:
                    continue
                f5[member] = (lambda picks, d=recoded:
                              float(SP.estimate(d, picks)["delta_difficulty"]))
                continue
            f5[member] = _F5_ESTIMATORS[base](table, configuration, scale=scale)
    if f5:
        fam["F5"] = f5
    f6: dict[str, Any] = {}
    for companion in b_companions(frozen):
        name = ("vac(B|A+B)-vac(B solo)" if companion == "A"
                else f"vac(B|B+{companion})-vac(B solo)")
        try:
            f6[name] = E.vacuity_difference(table, companion, configuration)
        except (IntegrityError, ProtocolError):
            continue
    if f6:
        fam["F6"] = f6
    return fam


def order_members(table: ObservationTable, local: bool) -> dict[str, Any]:
    out = {"Ord_A": E.ord_a(table), "Ord_B": E.ord_b(table),
           "Ord_Lambda": E.ord_lambda(table)}
    if local:
        out["Ord_Rbar"] = E.ord_rbar(table)
    return out


# --------------------------------------------------------------- intervals
def _member_dict(m: Any) -> dict[str, Any]:
    d = asdict(m)
    return {k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in d.items()}


def _interval(table: ObservationTable, member: str, configuration: str | None,
              estimate: float, se: float, critical: float,
              references: Sequence[str]) -> tuple[CL.Interval, dict[str, Any] | None]:
    try:
        bound = B.contrast_boundary_from_table(table, member, configuration,
                                               references=references)
    except (ProtocolError, IntegrityError, KeyError, ValueError):
        bound = None
    lo, hi = estimate - critical * se, estimate + critical * se
    lo, hi = B.apply_allowance(lo, hi, bound)
    return CL.Interval(member=member, estimate=estimate, lower=lo, upper=hi,
                       boundary=bound), bound


def _precondition(iv: CL.Interval) -> bool | None:
    try:
        return bool(iv.meets_precondition())
    except ProtocolError:
        return None


def _reading(member: str, iv: CL.Interval, *, support: Mapping[str, Any] | None
             ) -> dict[str, Any]:
    if member == "Delta_R":
        return CL.delta_r_reading(iv)
    if member == "delta_difficulty":
        return CL.delta_difficulty_reading(iv, support or {"holds": False})
    direction = CL.contrast_direction(iv)
    return {"levels": [], "markers": ([] if _precondition(iv) in (True, None)
                                      else ["INSUFFICIENT_PRECISION"]),
            "direction": direction, "statuses": CL.boundary_statuses(iv)}


# --------------------------------------------------------------- the gates
def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def solo_headroom(table: ObservationTable, frozen: Mapping[str, Any]
                  ) -> dict[str, Any]:
    """§3.2's L1 identification gate, measured on this frame's blocks.

    "c has solo headroom": the outcome constraint's realised solo compliance
    must exceed §3.2's floor for a loss to be exhibitable at all --- a
    constraint already at the floor cannot fall. v7 read the quantity off
    the freeze, which carries only B's calibration value; here it is the
    realised confirmatory rate for both outcome slots, with the frozen
    calibration value beside B's so a reader can see them disagree.
    """
    out: dict[str, Any] = {"floor": C.L1_SOLO_HEADROOM_FLOOR}
    for slot in ("B", "A"):
        try:
            realised: float | None = _mean(E.solo_vector(table, slot))
        except (IntegrityError, ProtocolError):
            realised = None
        out[slot] = {"realised_solo_compliance": realised,
                     "has_headroom": (realised is not None
                                      and realised > C.L1_SOLO_HEADROOM_FLOOR)}
    out["B"]["frozen_solo_compliance"] = frozen.get("solo_compliance_b")
    return out


#: The outcome slot of each L1 member: the constraint whose loss is read.
_L1_OUTCOME = {"D(B<-A)": "B", "D(A<-B)": "A"}


def l1_gate(headroom: Mapping[str, Any],
            intervals: Mapping[str, CL.Interval],
            forced: Mapping[str, CL.Interval]) -> dict[str, Any]:
    """``emit_l1``'s precondition chain as a reading, per L1 member.

    The order is v7's: no headroom, then a structural zero, then §17.4's
    both-bounds agreement, then the lower bound. ``licensed`` is what v7's
    caller took from ``statement["emitted"]`` and what L2 reads.
    """
    out: dict[str, Any] = {}
    for member, slot in _L1_OUTCOME.items():
        entry = dict(headroom.get(slot) or {})
        iv = intervals.get(member)
        room = bool(entry.get("has_headroom"))
        licensed, reason = False, None
        if iv is None:
            reason = "the design supplies no cell for this loss on this frame"
        elif not room:
            reason = ("§12: the outcome constraint has no solo headroom, so "
                      "the L1 identification gate does not hold")
        elif CL.is_structural_zero(iv):
            reason = ("v7 §13.14: the solo and composed cells sit at the same "
                      "exact boundary in every block; a lower bound above "
                      "zero is unreachable by construction")
        elif not _vacuity_agrees(iv, forced.get(f"{member}|vacuity_forced")):
            reason = ("§17.4: the primary and the vacuity-forced "
                      "recomputation do not license the same claim")
        elif not iv.excludes_zero_from_below():
            reason = ("the simultaneous interval does not have a lower bound "
                      "above 0")
        else:
            licensed = True
        out[member] = {"member": member, "outcome_slot": slot,
                       "solo_headroom": room,
                       "realised_solo_compliance":
                           entry.get("realised_solo_compliance"),
                       "floor": C.L1_SOLO_HEADROOM_FLOOR,
                       "licensed": licensed, "reason": reason}
    return out


def _vacuity_agrees(primary: CL.Interval, forced: CL.Interval | None) -> bool:
    """§17.4 for a direction claim: the primary and the recomputation must
    license the same predicate (``claims._vacuity_agrees``, which is private
    there and is the rule, not a number)."""
    if forced is None:
        return True
    return (primary.excludes_zero_from_below()
            == forced.excludes_zero_from_below())


def lambda_gate(interval: CL.Interval | None,
                l1: Mapping[str, Mapping[str, Any]],
                forced: CL.Interval | None) -> dict[str, Any]:
    """§3.2 L2's precondition: **both** L1 directions licensed.

    Without it there is no loss for an asymmetry to be an asymmetry of, so
    the Lambda reading is ``NOT_LICENSED`` with the members that did not
    reach L1 --- not an unresolved direction and not an absence.
    """
    missing = sorted(m for m in _L1_OUTCOME
                     if not (l1.get(m) or {}).get("licensed"))
    base = {"l1_licensed": {m: bool((l1.get(m) or {}).get("licensed"))
                            for m in sorted(_L1_OUTCOME)}}
    if interval is None:
        return {**base, "status": "NOT_LICENSED",
                "reason": "the design supplies no Lambda on this frame"}
    if missing:
        return {**base, "status": "NOT_LICENSED",
                "reason": f"L2's gate is L1 for both directions and {missing} "
                          "did not reach L1"}
    if not _vacuity_agrees(interval, forced):
        return {**base, "status": "NOT_LICENSED",
                "reason": "§17.4: the primary and the vacuity-forced "
                          "recomputation do not license the same claim"}
    return {**base, "status": "READ",
            "excludes_zero": interval.excludes_zero(),
            "direction": ("B <- A" if interval.estimate > 0 else "A <- B")}


def reference_heterogeneity(intervals: Mapping[str, CL.Interval]
                            ) -> dict[str, Any]:
    """§15 F2's L3 qualifier, **within** one frame.

    The three Delta_j intervals must agree on one side of §11.4's registered
    smallest effect of interest --- the threshold every L3 sub-level reads.
    When they do not, the frame's Delta_R is an average over references that
    disagree, and the reading says so. Distinct from the cross-frame
    ``FRAME_HETEROGENEOUS`` verdict, which compares whole frames.
    """
    names = [f"Delta_{i}" for i in range(1, len(C.CORE_SLOTS) + 1)]
    sides: dict[str, str] = {}
    for name in names:
        iv = intervals.get(name)
        if iv is None:
            return {"asked": False, "disagrees": False, "sides": {},
                    "threshold": C.DELTA_R_GENERIC_THRESHOLD,
                    "reason": f"{name} is not estimated on this frame"}
        if iv.lower > C.DELTA_R_GENERIC_THRESHOLD:
            sides[name] = "above"
        elif iv.upper < C.DELTA_R_GENERIC_THRESHOLD:
            sides[name] = "below"
        else:
            sides[name] = "straddles"
    return {"asked": True, "disagrees": len(set(sides.values())) > 1,
            "sides": sides, "threshold": C.DELTA_R_GENERIC_THRESHOLD}


def vacuity_gate_binds(members: Mapping[str, Mapping[str, Any]]
                       ) -> dict[str, Any]:
    """§17.4's F6 gate, on this frame's vacuity-rate differences.

    "When every vacuity-rate difference is at or below 0.05 or its interval
    includes zero, the primary estimands are reported without
    qualification." So the gate binds when some difference is both larger
    than the registered gate and resolved away from zero.
    """
    binding: list[str] = []
    for name, entry in sorted(members.items()):
        estimate = entry.get("estimate")
        lo, hi = entry.get("simultaneous_lower"), entry.get("simultaneous_upper")
        if estimate is None or lo is None or hi is None:
            continue
        if abs(estimate) <= C.F6_VACUITY_GATE:
            continue
        if lo <= 0.0 <= hi:
            continue
        binding.append(name)
    return {"binds": bool(binding), "binding_members": binding,
            "gate": C.F6_VACUITY_GATE, "n_members": len(members)}


def projection_audit(table: ObservationTable, frozen: Mapping[str, Any]
                     ) -> list[dict[str, Any]]:
    """§23: §13.6's admission projection against what the composed cells did.

    §13.6 admits a candidate on a **projected** composed compliance
    ``p_hat_c = kappa_c + iota_c (1 - kappa_c)``, formed before any composed
    cell exists: ``kappa_c`` is the companion's unconstrained rate and
    ``iota_c`` the frozen difficulty coordinate. This is the prospective
    record of that projection --- per companion, per order, the projected
    rate against the realised one and the absolute error against
    ``PROJECTION_ERROR_ALLOWANCE``. It licenses no claim and revises no
    admission; A2 has no frozen coordinate and is ``NOT_PROJECTABLE``.
    """
    iota = _frozen_iota(frozen)
    audit: list[dict[str, Any]] = []
    for slot in b_companions(frozen):
        entry_iota = iota.get(slot)
        try:
            chance = E.chance_vector(table, slot)
        except (IntegrityError, ProtocolError):
            chance = None
        for configuration in C.CONFIGURATIONS:
            entry: dict[str, Any] = {
                "companion": slot, "configuration": configuration,
                "cell": f"pair:B+{slot}",
                "iota": entry_iota,
                "allowance": C.PROJECTION_ERROR_ALLOWANCE,
                "reading": "§13.6's projection is an ADMISSION quantity and "
                           "this is its prospective record; it licenses no "
                           "claim and revises no admission"}
            if entry_iota is None:
                audit.append({**entry, "status": "NOT_PROJECTABLE",
                              "reason": "the freeze carries no difficulty "
                                        "coordinate for this slot"})
                continue
            if chance is None or not table.has_composed(slot, "B",
                                                        configuration):
                audit.append({**entry, "status": "NOT_PROJECTABLE",
                              "reason": "the table carries no unconstrained "
                                        "or composed cell for this companion"})
                continue
            realised_all = E.composed_vector(table, slot, "B", configuration)
            defined = [i for i, k in enumerate(chance)
                       if k < C.CHANCE_DEGENERACY_MAX]
            n_degenerate = len(chance) - len(defined)
            projected = [chance[i] + entry_iota * (1.0 - chance[i])
                         for i in defined]
            realised = [realised_all[i] for i in defined]
            errors = [abs(p - r) for p, r in zip(projected, realised)]
            entry.update({"n_blocks": len(errors),
                          "n_blocks_degenerate": n_degenerate})
            if n_degenerate:
                entry["status"] = "DIFFICULTY_COORDINATE_DEGENERATE"
                entry["degenerate_reading"] = (
                    f"§11.2: on {n_degenerate} block(s) the unconstrained "
                    f"cell satisfied {slot} on (almost) every draw, iota is "
                    "not defined there, and the projection is formed on the "
                    f"{len(errors)} block(s) where it is")
            if not errors:
                audit.append({**entry, "projected_mean": None,
                              "realised_mean": None,
                              "absolute_error_mean": None,
                              "absolute_error_max": None,
                              "within_allowance": None})
                continue
            audit.append({**entry,
                          "projected_mean": _mean(projected),
                          "realised_mean": _mean(realised),
                          "chance_mean": _mean([chance[i] for i in defined]),
                          "absolute_error_mean": _mean(errors),
                          "absolute_error_median": sorted(errors)[len(errors) // 2],
                          "absolute_error_max": max(errors),
                          "within_allowance":
                              _mean(errors) <= C.PROJECTION_ERROR_ALLOWANCE})
    return audit


def _frozen_iota(frozen: Mapping[str, Any]) -> dict[str, float | None]:
    """slot -> the frozen difficulty coordinate, or None where there is none.

    A is the frame's ``iota_a``; the core and backup references and the
    spectrum points carry their own. The runner-up slots do not: they were
    never calibrated as companions, and §23's projection is not formed for
    them rather than being formed on a substitute.
    """
    out: dict[str, float | None] = {"A": (None if frozen.get("iota_a") is None
                                          else float(frozen["iota_a"]))}
    for entry in list(frozen.get("core") or ()) + list(frozen.get("backups") or ()):
        value = entry.get("iota")
        out[entry["slot"]] = None if value is None else float(value)
    for point in frozen.get("spectrum_points") or ():
        value = point.get("iota")
        out[point["slot"]] = None if value is None else float(value)
    return out


# ------------------------------------------------ §34 D6: the ledger
_NOT_LOCAL = ("the frame does not enter the LOCAL arm, so it carries no "
              "reference set and this member has no cells")
_NOT_SPECTRUM = ("the frame does not enter the SPECTRUM arm, so there is no "
                 "difficulty relation on it")
_NO_CLASS_ARM = ("the broad-class arm is not run in v8 "
                 "(CLASS_ARM_NOT_AVAILABLE); the member is not asked")


def frame_expectations(frozen: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Every registered member this frame *could* carry, and whether the
    frozen design asks for it.

    family -> member -> (asked, reason-when-not). Built from the freeze, so
    a member the analysis never formed is either NOT_ASKED here or shows up
    as NOT_IDENTIFIED in the ledger; it cannot be absent.
    """
    local = bool(frozen["enters_local"])
    spectrum = bool(frozen["enters_spectrum"])
    exp: dict[str, dict[str, Any]] = {}
    f1: dict[str, Any] = {}
    for member in C.FAMILY_MEMBERS["F1"]:
        if member in ("Delta_R", "Xi"):
            f1[member] = (local, None if local else _NOT_LOCAL)
        elif member == "delta_difficulty":
            f1[member] = (spectrum, None if spectrum else _NOT_SPECTRUM)
        else:
            f1[member] = (True, None)
    exp["F1"] = f1
    for family in ("F2", "F3", "F4", "F7"):
        exp[family] = {m: (local, None if local else _NOT_LOCAL)
                       for m in C.FAMILY_MEMBERS[family]}
    exp["F5"] = {f"{base}|{suffix}": f1.get(base, (False, _NOT_LOCAL))
                 for suffix in sorted(F5_RECODINGS)
                 for base in F5_MEMBERS[suffix]}
    exp["F6"] = {("vac(B|A+B)-vac(B solo)" if c == "A"
                  else f"vac(B|B+{c})-vac(B solo)"): (True, None)
                 for c in b_companions(frozen)}
    sens = frozen.get("reference_sensitivity") or {}
    exp["F_REFSENS"] = {
        "Delta_R[" + "+".join(t["slots"]) + "]": (local,
                                                  None if local else _NOT_LOCAL)
        for t in sens.get("admissible_triples", ())}
    exp["F_SPECTRUM"] = {"slope": (spectrum,
                                   None if spectrum else _NOT_SPECTRUM)}
    runner_up = tuple(frozen.get("runner_up_slots") or ())
    exp["F_RUNNER_UP"] = {
        f"Delta_R[{s}]": (s in runner_up, None if s in runner_up else
                          "the frozen operating point is stable on this "
                          "coordinate, so no runner-up arm was generated")
        for s in ("A2", "B2")}
    exp["F11"] = {"Ord_A": (True, None), "Ord_B": (True, None),
                  "Ord_Lambda": (True, None),
                  "Ord_Rbar": (local, None if local else _NOT_LOCAL),
                  "Ord_CL": (False, _NO_CLASS_ARM)}
    return exp


def identification_ledger(expectations: Mapping[str, Mapping[str, Any]],
                          formed: Mapping[str, Mapping[str, Any]]
                          ) -> dict[str, dict[str, Any]]:
    """§34 D6: one status for every registered member, never an omission.

    ``ESTIMATED`` when the analysis formed it; ``NOT_ASKED`` when the frozen
    design has no arm for it; ``NOT_IDENTIFIED`` when the arm exists and the
    member could not be formed --- and the last is a result, not a missing
    number, which is the whole point of recording all three apart.
    """
    ledger: dict[str, dict[str, Any]] = {}
    for family, members in expectations.items():
        block = formed.get(family)
        # A family block is the bootstrap's output (a "members" mapping) or,
        # in a unit test, the mapping itself. An EMPTY members mapping means
        # nothing was formed, which is exactly what the ledger has to be able
        # to say --- so it must not fall through to the block's own keys.
        got = set(block.get("members") or ()) if isinstance(block, Mapping) \
            and "members" in block else set(block or ())
        entries: dict[str, Any] = {}
        for member, (asked, reason) in members.items():
            if member in got:
                entries[member] = {"status": "ESTIMATED"}
            elif not asked:
                entries[member] = {"status": "NOT_ASKED", "reason": reason}
            else:
                entries[member] = {
                    "status": "NOT_IDENTIFIED",
                    "reason": "the arm exists on this frame and the member "
                              "could not be formed from its cells"}
        ledger[family] = entries
    return ledger


def assert_every_member_ledgered(ledger: Mapping[str, Mapping[str, Any]],
                                 formed: Mapping[str, Mapping[str, Any]], *,
                                 where: str) -> dict[str, Any]:
    """Nothing is silently absent, and nothing is silently present.

    Both directions, because §34 D6's failure mode is an *omission*: a
    member with no status would read as a design that was never asked, and
    an estimated member with no ledger entry would leave the registered set
    quietly larger than the recorded one.
    """
    bad_status = [f"{fam}:{m}" for fam, ms in ledger.items()
                  for m, e in ms.items()
                  if e.get("status") not in LEDGER_STATUSES]
    if bad_status:
        raise ProtocolError(f"{where}: {bad_status} carry a status outside "
                            f"{list(LEDGER_STATUSES)}")
    unledgered: list[str] = []
    for family, entry in formed.items():
        if family.startswith("_"):
            continue
        members = (entry or {}).get("members") or {}
        for member in members:
            recorded = (ledger.get(family) or {}).get(member)
            if recorded is None or recorded.get("status") != "ESTIMATED":
                unledgered.append(f"{family}:{member}")
    if unledgered:
        raise ProtocolError(
            f"{where}: {sorted(unledgered)} were estimated and are not "
            "recorded ESTIMATED in the identification ledger; §34 D6 "
            "requires every registered member to carry a status")
    counts: dict[str, int] = {s: 0 for s in LEDGER_STATUSES}
    for members in ledger.values():
        for e in members.values():
            counts[e["status"]] += 1
    return {"members": sum(counts.values()), "by_status": counts,
            "rule": "every registered member is ESTIMATED, NOT_ASKED or "
                    "NOT_IDENTIFIED; an absent member is a refusal"}


def l4a_consistency(readings: Mapping[str, Mapping[str, Any]]
                    ) -> dict[str, Any]:
    """§3.2 L4a, within one frame: the same classification for the same
    NAMED member in both configurations.

    ``readings`` is configuration -> member -> reading. v4r4's defect was
    comparing the *sets* of levels reached and so declaring replication for
    the pattern that least replicates; this is per member, and a member that
    reached a level in one configuration and not the other is recorded as
    differing rather than as agreeing.
    """
    per_member: dict[str, dict[str, Any]] = {}
    for member in C.FAMILY_MEMBERS["F1"]:
        levels = {}
        for configuration in C.CONFIGURATIONS:
            reading = (readings.get(configuration) or {}).get(member)
            if reading is None:
                levels[configuration] = None
                continue
            got = list(reading.get("levels") or ())
            levels[configuration] = got[0] if got else None
        if all(v is None for v in levels.values()):
            continue
        per_member[member] = {
            "levels": levels,
            "agree": len({levels[c] for c in C.CONFIGURATIONS}) == 1}
    differing = sorted(m for m, e in per_member.items() if not e["agree"])
    return {"per_member": per_member, "differing_members": differing,
            "configurations": list(C.CONFIGURATIONS),
            "consistent": bool(per_member) and not differing,
            "registered_reading": ("Configuration dependence (§28.1)"
                                   if differing else None),
            "rule": "per NAMED member across the two registered outcome "
                    "positions; comparing the sets of levels reached is "
                    "v4r4's defect"}


def joint_members(per_frame: Mapping[int, Mapping[str, Any]],
                  block_positions: Mapping[int, Sequence[int]],
                  n_positions: int) -> dict[str, Callable[[Sequence[int]], float]]:
    """Every (frame, F1 member) as a function of a TOPIC resample."""
    out: dict[str, Callable[[Sequence[int]], float]] = {}
    for frame, members in sorted(per_frame.items()):
        pos_to_idx = {p: i for i, p in enumerate(block_positions[frame])}
        for name, member in members.items():
            def f(picks, member=member, pos_to_idx=pos_to_idx):
                idx = [pos_to_idx[p] for p in picks if p in pos_to_idx]
                if not idx:
                    return float("nan")
                if callable(member):
                    return float(member(idx))
                return sum(member[i] for i in idx) / len(idx)
            out[f"f{frame}:{name}"] = f
    return out


def local_model_verdict(readings: Mapping[int, Mapping[str, Any]]
                        ) -> dict[str, Any]:
    """The conjunction over entering LOCAL frames of the Delta_R readings on
    the joint interval (one configuration).

    **No verdict is ever ``LOCAL_EQUIVALENT_L3c``.** §34 D18 is closed at
    ``precondition`` and v8 runs no near-form arm (``freeze.DEVIATIONS``),
    so L3c's *strong* refutation verdict --- "no pair-specific excess" --- is
    unreachable by construction. An L3c-level reading is reported with the
    disposition ``NEAR_FORM_UNAVAILABLE`` and the model verdict is the
    narrower ``LOCAL_EQUIVALENT_SAME_FORM_ONLY``: no excess relative to
    same-form exact-count companions, which is what a same-form pool
    licenses. ``claims.l3c_disposition`` supplies the registered scope and
    its sentence.

    §17.4's both-bounds rule also applies here: a frame whose Delta_R and
    whose vacuity-forced recomputation do not license the same claim reached
    no level in v7 either, and it enters the conjunction as INDETERMINATE.
    """
    if not readings:
        return {"verdict": "UNIDENTIFIED", "frames": {},
                "rule": P.MULTIPLICITY_RULE}
    per, l3c_frames = {}, []
    for w, r in readings.items():
        levels = set(r.get("levels", ()))
        markers = set(r.get("markers", ()))
        if r.get("vacuity_withholds_levels"):
            per[w] = "INDETERMINATE"
        elif "INSUFFICIENT_PRECISION" in markers:
            per[w] = "INSUFFICIENT_PRECISION"
        elif "L3b" in levels:
            per[w] = "L3b"
        elif "L3a" in levels:
            per[w] = "L3a"
        elif "L3c" in levels:
            per[w] = "L3c"
            l3c_frames.append(str(w))
        else:
            per[w] = "INDETERMINATE"
    values = set(per.values())
    if "INSUFFICIENT_PRECISION" in values:
        verdict = "INSUFFICIENT_PRECISION"
    elif len(values) == 1:
        v = next(iter(values))
        verdict = {"L3a": "LOCAL_SUPPORTED_L3a", "L3b": "LOCAL_SUPPORTED_L3b",
                   "L3c": "LOCAL_EQUIVALENT_SAME_FORM_ONLY",
                   "INDETERMINATE": "INDETERMINATE"}[v]
    elif values <= {"L3a", "L3b"}:
        verdict = "LOCAL_SUPPORTED_L3a"      # every frame beyond the generic threshold
    else:
        verdict = "FRAME_HETEROGENEOUS"
    if verdict == "LOCAL_EQUIVALENT_L3c":    # unreachable, and asserted so
        raise ProtocolError(
            "§34 D18: the strong L3c verdict requires the near-form arm and "
            "v8 runs none; the narrow reading is the only one licensed")
    out = {"verdict": verdict, "frames": {str(w): v for w, v in per.items()},
           "rule": "conjunction over entering LOCAL frames on the joint "
                   "decision interval; heterogeneity is a verdict, not a "
                   "support claim"}
    if l3c_frames:
        disposition = CL.l3c_disposition(near_form_available=False,
                                         delta_near=None)
        out["l3c"] = {"frames": sorted(l3c_frames),
                      "disposition": L3C_DISPOSITION,
                      "scope": disposition["scope"],
                      "scope_sentence": disposition["scope_sentence"],
                      "statuses": list(disposition["statuses"]),
                      "reason": disposition.get("reason")}
    return out


def methodological_success(result: Mapping[str, Any],
                           frames: Mapping[int, Mapping[str, Any]]
                           ) -> dict[str, Any]:
    """§26's methodological success criterion, restated per model for a
    frame-conditioned design.

    MET when, for every entering frame: every registered F1 member the frame
    was **asked** for is ESTIMATED; the registered precision precondition is
    met on every primary interval (the joint F1 decision intervals and the
    per-frame F1 ones); and no frame's table failed its cell-set assertion.
    It is not the scientific effect claim: it says the design identified and
    could measure what it registered, whatever the numbers came out to be.
    """
    reasons: list[str] = []
    for w in sorted(frames):
        fr = result["frames"].get(str(w))
        if fr is None:
            reasons.append(f"frame {w} has no analysis entry")
            continue
        for configuration in C.CONFIGURATIONS:
            ledger = ((fr.get("identification_ledger") or {})
                      .get("configurations", {}).get(configuration, {})
                      .get("F1") or {})
            for member, entry in sorted(ledger.items()):
                if entry.get("status") == "NOT_IDENTIFIED":
                    reasons.append(f"f{w}:{configuration}:{member} is "
                                   "NOT_IDENTIFIED")
            f1 = ((fr.get("configurations") or {}).get(configuration, {})
                  .get("F1") or {}).get("members") or {}
            for member, entry in sorted(f1.items()):
                if entry.get("meets_precondition") is False:
                    reasons.append(f"f{w}:{configuration}:{member} does not "
                                   "meet its precision precondition "
                                   "(per-frame interval)")
    for configuration in C.CONFIGURATIONS:
        for name, entry in sorted((result["joint"].get(configuration) or {})
                                  .get("members", {}).items()):
            if entry.get("meets_precondition") is False:
                reasons.append(f"{name}:{configuration} does not meet its "
                               "precision precondition (joint interval)")
    within_block = result.get("within_block") or {}
    missing = sorted(str(w) for w in frames if str(w) not in within_block)
    if missing:
        reasons.append(f"no within-block assertion recorded for frames "
                       f"{missing}")
    verdict = "MET" if not reasons else "NOT_MET"
    if verdict not in C.SUCCESS_CRITERION_VALUES:
        raise ProtocolError(f"{verdict!r} is not a registered §26 value")
    return {
        "criterion": "§26 methodological success, restated per model for the "
                     "frame-conditioned design",
        "verdict": verdict, "reasons": reasons,
        "rule": "every entering frame's asked F1 members ESTIMATED; the "
                "registered precision precondition met on every primary "
                "interval; every frame table passed its cell-set assertion",
        "note": "not the scientific effect claim: it says the design "
                "identified and could measure what it registered"}


def _frame_gates(families: Mapping[str, Any], ivs: Mapping[str, CL.Interval],
                 headroom: Mapping[str, Any]) -> dict[str, Any]:
    """Every gate of one (frame, configuration), from that block's own
    intervals: L1's headroom chain, L2's precondition, Xi's direction gate,
    F2's within-frame heterogeneity and §17.4's two vacuity halves."""
    l1 = l1_gate(headroom, ivs, ivs)
    l2 = lambda_gate(ivs.get("Lambda"), l1, ivs.get("Lambda|vacuity_forced"))
    xi = CL.xi_gate(ivs["Xi"]) if "Xi" in ivs else None
    f6 = (families.get("F6") or {}).get("members") or {}
    gate = vacuity_gate_binds(f6)
    forced = ivs.get("Delta_R|vacuity_forced")
    agrees = (CL.l3_vacuity_agrees(ivs["Delta_R"], forced)
              if "Delta_R" in ivs else None)
    vacuity = {
        **gate, "gate_binds": gate["binds"], "forced_agrees": agrees,
        "qualification_sentence": (C.VACUITY_QUALIFICATION_SENTENCE
                                   if gate["binds"] else None),
        "partial_identification_bounds": ([forced.lower, forced.upper]
                                          if gate["binds"] and forced else None),
        "rule": "§17.4: F6 gates the REPORTING half (the qualification "
                "sentence and the partial-identification bounds); the F5 "
                "recomputation gates the LICENSING half (both bounds must "
                "license the same claim)"}
    return {"headroom": dict(headroom), "l1": l1, "l2": l2, "xi": xi,
            "reference_heterogeneity": reference_heterogeneity(ivs),
            "vacuity": vacuity}


def apply_degenerate_ceiling(fam_out: dict[str, Any], counter: RefitCounter,
                              resamples: int) -> dict[str, Any]:
    """§13.13's ``DEGENERATE_REPLICATE_MAX`` on the realised F_SPECTRUM
    bootstrap.

    Above the ceiling the interval is **refused**, not reported wide: more
    than one replicate in a hundred refitted something other than the
    registered relation, so the percentile of that distribution is not the
    quantity's sampling interval. The point estimate stays --- it is
    descriptive --- and the status says why there is no interval.
    """
    record = counter.record(resamples)
    fam_out["degenerate_replicates"] = record
    if record["status"] != "DEGENERATE_REPLICATES":
        return fam_out
    for entry in fam_out["members"].values():
        entry["status"] = "DEGENERATE_REPLICATES"
        entry["decision_lower"] = entry["decision_upper"] = None
        entry["decision_half_width"] = None
        entry["meets_precondition"] = None
        entry["reading"] = {
            "levels": [], "markers": ["DEGENERATE_REPLICATES"],
            "statuses": [],
            "reason": (f"{record['degenerate_replicate_share']:.3f} of the "
                       f"replicates did not refit the registered relation, "
                       f"above the registered ceiling "
                       f"{C.DEGENERATE_REPLICATE_MAX}; the interval is "
                       "refused rather than reported")}
    return fam_out


def _qualify_delta_r(reading: dict[str, Any], gates: Mapping[str, Any]
                     ) -> dict[str, Any]:
    """v7's ``emit_l3`` inputs, attached to a Delta_R reading.

    Xi decides the *wording* and never whether the reading exists (§3.2);
    F2's heterogeneity and §17.4's vacuity rule attach qualifiers. A
    disagreement with the vacuity-forced recomputation withholds the level
    exactly as ``emit_l3`` did, and ``vacuity_withholds_levels`` is what the
    model verdict reads.
    """
    qualifiers = list(reading.get("qualifiers") or ())
    gate = gates.get("xi")
    if gate is not None:
        reading["xi_gate"] = gate
        reading["outcome_specificity_wording"] = gate["wording"]
        reading["statuses"] = sorted(set(reading.get("statuses") or ())
                                     | set(gate["statuses"]))
    heterogeneity = gates.get("reference_heterogeneity") or {}
    reading["reference_heterogeneity"] = heterogeneity
    if heterogeneity.get("disagrees"):
        qualifiers.append("REFERENCE_HETEROGENEOUS")
    vacuity = gates.get("vacuity") or {}
    reading["vacuity"] = vacuity
    reading["vacuity_withholds_levels"] = vacuity.get("forced_agrees") is False
    if vacuity.get("gate_binds") or vacuity.get("forced_agrees") is False:
        qualifiers.append("VACUITY_DEPENDENT")
    reading["qualifiers"] = qualifiers
    return reading


# ----------------------------------------------------------------- driver
def analyse_model(rows: Sequence[Mapping[str, Any]], freeze: Mapping[str, Any],
                  *, model_id: str, resamples: int) -> dict[str, Any]:
    design = freeze["design"]
    m_draws = int(design["draws"])
    frames = {int(w): e for w, e in design["frames"].items()}
    tables: dict[int, ObservationTable] = {}
    checks: dict[str, Any] = {}
    for w, e in frames.items():
        t = frame_table(rows, w, m_draws=m_draws)
        checks[str(w)] = assert_frame_table(
            t, arms=e["arms"], n_spectrum=int(e["n_spectrum_slots"]),
            runner_up=tuple(e.get("runner_up_slots") or ()),
            blocks_expected=len({r["block_id"] for r in rows
                                 if int(r.get("block_frame", -1)) == w}))
        tables[w] = t
    references = list(C.CORE_SLOTS)
    result: dict[str, Any] = {"frames": {}, "joint": {}, "model_verdict": {},
                              "within_block": checks}
    joint_f1: dict[str, dict[int, dict[str, Any]]] = {c: {} for c in C.CONFIGURATIONS}
    positions: dict[int, list[int]] = {}
    expectations: dict[int, dict[str, dict[str, Any]]] = {}
    for w, t in tables.items():
        positions[w] = [int(b.rpartition("-")[2]) // C.N_WORDINGS for b in t.blocks]
        expectations[w] = frame_expectations(frames[w])
        headroom = solo_headroom(t, frames[w])
        fr: dict[str, Any] = {"frame": w, "blocks": len(t.blocks),
                              "enters_local": frames[w]["enters_local"],
                              "enters_spectrum": frames[w]["enters_spectrum"],
                              "configurations": {}, "algebraic_forms": {},
                              "solo_headroom": headroom, "gates": {},
                              # §23: the admission projection against what
                              # the composed cells actually did.
                              "projection_audit": projection_audit(
                                  t, frames[w]),
                              "identification_ledger": {"configurations": {}}}
        for cfg in C.CONFIGURATIONS:
            members = frame_members(t, frames[w], cfg)
            point = members.pop("_spectrum_point", None)
            forms: dict[str, Any] = {}
            if frames[w]["enters_local"]:
                forms["Delta_R"] = E.assert_delta_r_forms(t, cfg)
            families: dict[str, Any] = {}
            ivs: dict[str, CL.Interval] = {}
            support = None
            if point is not None:
                est = SP.estimate(point["data"])
                support = est["support"]
                fr.setdefault("spectrum_fit", {})[cfg] = {
                    k: est[k] for k in ("degenerate", "difficulty_a",
                                        "D_B_from_A", "delta_difficulty",
                                        "support", "dropped_points")
                    if k in est}
                if not est.get("degenerate"):
                    fr["spectrum_fit"][cfg].update({
                        "slope": est["slope"], "intercepts": est["intercepts"],
                        "predicted_at_A": est["predicted_at_A"],
                        "residuals": est["residuals"]})
                # §11.7's own agreement check: the cancelled and the
                # definitional forms of delta_difficulty must agree, because
                # the prediction weights sum to one and the B-solo baseline
                # cancels. A disagreement refuses; a fit that is not
                # available is a different fact and is recorded.
                try:
                    forms["delta_difficulty"] = SP.assert_algebraic_forms_agree(
                        point["data"])
                    forms["delta_difficulty_status"] = "AGREE"
                except SP.FitNotAvailable as exc:
                    forms["delta_difficulty"] = None
                    forms["delta_difficulty_status"] = "FIT_NOT_AVAILABLE"
                    forms["delta_difficulty_reason"] = str(exc)
            if forms:
                fr["algebraic_forms"][cfg] = forms
            for fname, fmembers in members.items():
                if not fmembers:
                    continue
                res: FamilyResult = bootstrap_family(
                    fmembers, seed=bootstrap_seed(f"{fname}:{cfg}:f{w}", model_id),
                    configuration=cfg, family=fname, n_blocks=len(t.blocks),
                    resamples=resamples)
                fam_out: dict[str, Any] = {
                    "critical_value": res.critical_value,
                    "sidak_reference": sidak_critical(len(fmembers)),
                    "resamples": res.resamples, "blocks": res.blocks,
                    "members": {}}
                for name, m in res.members.items():
                    iv, bound = _interval(t, name, cfg, m.estimate,
                                          m.standard_error, res.critical_value,
                                          references)
                    ivs[name] = iv
                    fam_out["members"][name] = {
                        **_member_dict(m),
                        "decision_lower": iv.lower, "decision_upper": iv.upper,
                        "decision_half_width": iv.half_width,
                        "boundary": bound,
                        "meets_precondition": _precondition(iv),
                        "reading": _reading(name, iv, support=support),
                        "per_block": (None if callable(fmembers[name])
                                      else list(fmembers[name]))}
                if fname == "F_SPECTRUM" and point is not None:
                    apply_degenerate_ceiling(fam_out, point["refits"],
                                            resamples)
                families[fname] = fam_out
            gates = _frame_gates(families, ivs, headroom)
            f1_out = (families.get("F1") or {}).get("members") or {}
            for member, entry in gates["l1"].items():
                if member in f1_out:
                    f1_out[member]["reading"]["l1"] = entry
            if "Lambda" in f1_out:
                f1_out["Lambda"]["reading"]["l2"] = gates["l2"]
            if "Delta_R" in f1_out:
                _qualify_delta_r(f1_out["Delta_R"]["reading"], gates)
            fr["gates"][cfg] = gates
            ledger = identification_ledger(
                {k: v for k, v in expectations[w].items() if k != "F11"},
                families)
            assert_every_member_ledgered(
                ledger, families,
                where=f"CONFIRMATORY_ANALYSIS f{w}:{cfg}")
            fr["identification_ledger"]["configurations"][cfg] = ledger
            fr["configurations"][cfg] = families
            joint_f1[cfg][w] = dict(members["F1"])
        ords = order_members(t, frames[w]["enters_local"])
        fr["algebraic_forms"]["order"] = E.assert_order_forms(t)
        res = bootstrap_family(ords, seed=bootstrap_seed(f"F11:f{w}", model_id),
                               configuration="cross-configuration",
                               family="F11", n_blocks=len(t.blocks),
                               resamples=resamples)
        fr["F11"] = {"critical_value": res.critical_value,
                     "members": {name: {**_member_dict(m),
                                        "meets_precondition": _precondition(
                                            CL.Interval(name, m.estimate,
                                                        m.simultaneous_lower,
                                                        m.simultaneous_upper))}
                                 for name, m in res.members.items()}}
        f11_ledger = identification_ledger({"F11": expectations[w]["F11"]},
                                           {"F11": fr["F11"]})
        assert_every_member_ledgered(f11_ledger, {"F11": fr["F11"]},
                                     where=f"CONFIRMATORY_ANALYSIS f{w}:F11")
        fr["identification_ledger"]["cross_configuration"] = f11_ledger
        result["frames"][str(w)] = fr
    # -------------------------------------------------------- joint family
    n_positions = 1 + max(p for ps in positions.values() for p in ps)
    for cfg in C.CONFIGURATIONS:
        jm = joint_members(joint_f1[cfg], positions, n_positions)
        res = bootstrap_family(jm, seed=bootstrap_seed(f"JOINT_F1:{cfg}", model_id),
                               configuration=cfg, family="JOINT_F1",
                               n_blocks=n_positions, resamples=resamples)
        joint: dict[str, Any] = {
            "critical_value": res.critical_value,
            "sidak_reference": sidak_critical(len(jm)),
            "family_size": len(jm), "topics": n_positions,
            "members": {}}
        delta_readings: dict[int, dict[str, Any]] = {}
        joint_readings: dict[int, dict[str, Any]] = {w: {} for w in tables}
        for name, m in res.members.items():
            w = int(name.partition(":")[0][1:])
            member = name.partition(":")[2]
            t = tables[w]
            iv, bound = _interval(t, member, cfg, m.estimate, m.standard_error,
                                  res.critical_value, references)
            support = (result["frames"][str(w)].get("spectrum_fit", {})
                       .get(cfg, {}).get("support"))
            reading = _reading(member, iv, support=support)
            gates = result["frames"][str(w)]["gates"][cfg]
            if member == "Delta_R":
                _qualify_delta_r(reading, gates)
            joint["members"][name] = {
                **_member_dict(m), "frame": w, "member": member,
                "decision_lower": iv.lower, "decision_upper": iv.upper,
                "decision_half_width": iv.half_width,
                "meets_precondition": _precondition(iv), "reading": reading}
            joint_readings[w][member] = reading
            if member == "Delta_R":
                delta_readings[w] = reading
        joint["local_model_verdict"] = local_model_verdict(delta_readings)
        joint_expectations = {
            "JOINT_F1": {f"f{w}:{member}": expectations[w]["F1"][member]
                         for w in sorted(tables)
                         for member in C.FAMILY_MEMBERS["F1"]}}
        joint_ledger = identification_ledger(joint_expectations,
                                             {"JOINT_F1": joint})
        assert_every_member_ledgered(joint_ledger, {"JOINT_F1": joint},
                                     where=f"CONFIRMATORY_ANALYSIS JOINT:{cfg}")
        joint["identification_ledger"] = joint_ledger
        for w in tables:
            # L4a is per frame and per NAMED member, read on the decision
            # interval --- which is the joint one (precision.MULTIPLICITY_RULE).
            entry = result["frames"][str(w)].setdefault(
                "l4a", {"configurations": {}})
            entry["configurations"][cfg] = joint_readings[w]
        result["joint"][cfg] = joint
        result["model_verdict"][cfg] = joint["local_model_verdict"]["verdict"]
    for w in tables:
        fr = result["frames"][str(w)]
        fr["l4a"] = l4a_consistency(fr["l4a"]["configurations"])
    result["methodological_success"] = methodological_success(result, frames)
    return result


def analysis_payload(tree: L.ConfirmTree, *, producing_commit: str,
                     resamples: int | None = None) -> dict[str, Any]:
    freeze, freeze_hash = load_freeze(tree)
    gen = L.read_stage_record(tree, L.STAGE_GENERATION)
    if gen.get("freeze_hash") != freeze_hash:
        raise IntegrityError("the generation record was signed under a "
                             "different freeze")
    if resamples is not None and not tree.synthetic:
        raise ProtocolError("resamples is a synthetic-namespace knob")
    resamples = resamples or C.BOOTSTRAP_RESAMPLES
    rows = collect_rows(tree)
    if len(rows) != int(gen["n_rows"]):
        raise IntegrityError(f"{len(rows)} rows on disk; the generation "
                             f"record counted {gen['n_rows']}")
    spec = get_model(tree.model_key)
    result = analyse_model(rows, freeze, model_id=spec.model_id,
                           resamples=resamples)
    return {
        "stage": L.STAGE_ANALYSIS,
        "artifact_type": L.STAGE_ARTIFACT_TYPE[L.STAGE_ANALYSIS],
        "outcome": "PASS", "producing_commit": producing_commit,
        "inputs": {"freeze_hash": freeze_hash,
                   "generation_record_hash":
                       fs.read_json(tree.stage_record(L.STAGE_GENERATION))["record_hash"]},
        "freeze_hash": freeze_hash, "resamples": resamples,
        "n_rows": len(rows), "protected": True,
        "multiplicity_rule": P.MULTIPLICITY_RULE,
        **result,
    }


def run_analysis(tree: L.ConfirmTree, *, producing_commit: str | None = None,
                 environment_digest: str = "", resamples: int | None = None
                 ) -> L.StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    return L.run_stage(
        tree, L.STAGE_ANALYSIS,
        compute=lambda _prev: analysis_payload(tree, producing_commit=commit,
                                               resamples=resamples),
        producing_commit=commit, environment_digest=environment_digest)
