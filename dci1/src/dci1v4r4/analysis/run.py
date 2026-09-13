"""The registered analysis: families, intervals, and the order they run in.

This module turns confirmatory rows into the §15 family results and nothing
else. It makes no claim; `analysis.claims` does that, from these intervals,
by a lookup that was fixed before any number existed.

**Members are built as vectors where a replicate is an average, and as
functions where it is not.** Everything in F1 except `delta_difficulty` is a
per-block contrast whose bootstrap replicate is the mean of the drawn blocks.
`delta_difficulty` is a refit: §17.2 requires each replicate to resample
blocks, recompute the cell means and the difficulty coordinate, refit the
non-A relation, predict at A, and recompute the residual. It therefore enters
the family as a callable over the replicate's index vector, sharing that
vector with every other member so the family's simultaneous intervals describe
the real joint variation.

**A is never in the fit that predicts A**, and the class companion is never in
it either. Both exclusions live in `analysis.spectrum`, on the path, and this
module simply does not offer a way around them.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r4.analysis import estimators as E
from dci1v4r4.analysis import spectrum as S
from dci1v4r4.analysis.bootstrap import (
    FamilyResult, Member, bootstrap_family, sidak_critical,
)
from dci1v4r4.analysis.observations import ObservationTable
from dci1v4r4.protocol import constants as C

__all__ = ["build_spectrum_input", "build_family_members", "analyse_family",
           "analyse_configuration", "precision_report", "f6_gate"]


def build_spectrum_input(table: ObservationTable, configuration: str, *,
                         family_of: Mapping[str, str]) -> S.SpectrumInput:
    """Assemble §11.7's per-block inputs from the observation table.

    ``family_of`` maps each *spectrum and core reference* slot to the
    registered constraint family it belongs to; Gate 3 writes it. ``A`` and
    the class companion must not appear, and `SpectrumInput` refuses them.
    """
    slots = [s for s in table.slots() if s not in ("A", "B", C.CLASS_SLOT)]
    missing = [s for s in slots + ["A"] if not table.has_chance(s)]
    if missing:
        raise ProtocolError(
            f"§25 chance observations are missing for {missing}; the "
            f"difficulty coordinate is (solo - chance)/(1 - chance) and "
            f"cannot be formed without them")
    return S.SpectrumInput(
        blocks=tuple(table.blocks), family_of=dict(family_of),
        b_solo=E.solo_vector(table, "B"),
        b_with={slot: E.composed_vector(table, "B", slot, configuration)
                for slot in slots + ["A"]},
        companion_solo={slot: E.solo_vector(table, slot) for slot in slots},
        companion_chance={slot: _chance_vector(table, slot) for slot in slots},
        a_solo=E.solo_vector(table, "A"),
        a_chance=_chance_vector(table, "A"))


def _chance_vector(table: ObservationTable, slot: str) -> list[float]:
    """§25's chance compliance: the instrument scored on the load-0 cell.

    A pre-treatment quantity, read from the unconstrained cell and never
    estimated from a composed one.
    """
    return [table.chance(b, slot).compliance for b in table.blocks]


def build_family_members(table: ObservationTable, configuration: str, *,
                         spectrum_input: S.SpectrumInput | None,
                         design: str) -> dict[str, dict[str, Member]]:
    """Every §15 family the design in force identifies, member by member."""
    references = E.reference_slots(table)
    spectrum = E.spectrum_slots(table)
    has_class = C.CLASS_SLOT in table.slots()
    families: dict[str, dict[str, Member]] = {}

    def loss(outcome: str, companion: str) -> list[float]:
        return E.delivery_loss(table, outcome, companion, configuration)

    # ------------------------------------------------------------- F1
    f1: dict[str, Member] = {
        "D(B<-A)": loss("B", "A"),
        "D(A<-B)": loss("A", "B"),
        "Lambda": E.asymmetry(table, configuration),
    }
    if len(references) == C.N_CORE_REFERENCES:
        f1["Delta_R"] = E.delta_r(table, configuration)
        f1["Xi"] = E.xi(table, configuration)
    if spectrum_input is not None:
        def delta_difficulty(picks: Sequence[int]) -> float:
            return float(S.estimate(spectrum_input, list(picks))
                         ["delta_difficulty"])
        f1["delta_difficulty"] = delta_difficulty
    families["F1"] = f1

    # ------------------------------------------------------------- F2
    if references:
        f2: dict[str, Member] = {}
        for index, slot in enumerate(references, start=1):
            f2[f"D(B<-{slot})"] = loss("B", slot)
            f2[f"Delta_{index}"] = E.delta_j(table, slot, configuration)
        families["F2"] = f2

    # ------------------------------------------------------------- F3
    if len(references) == C.N_CORE_REFERENCES:
        f3: dict[str, Member] = {f"D(A<-{s})": loss("A", s)
                                 for s in references}
        f3["Delta^A"] = E.delta_a(table, configuration)
        families["F3"] = f3

        # ---------------------------------------------------------- F4
        families["F4"] = {
            "D(Rbar<-A)": E.d_rbar_from(table, "A", configuration),
            "D(Rbar<-B)": E.d_rbar_from(table, "B", configuration),
            "D(Rbar<-Rbar')": E.d_rbar_rbar(table, configuration)}

        # ---------------------------------------------------------- F7
        families["F7"] = {}
        for slot in references:
            families["F7"][f"D({slot}<-B)"] = loss(slot, "B")
            families["F7"][f"D({slot}<-A)"] = loss(slot, "A")

    # ------------------------------------------------------------- F5
    f5: dict[str, Member] = {
        "D(B<-A)|vacuity_forced": E.delivery_loss(
            table, "B", "A", configuration, scale="non_vacuous_compliance"),
        "D(A<-B)|vacuity_forced": E.delivery_loss(
            table, "A", "B", configuration, scale="non_vacuous_compliance"),
        "Lambda|vacuity_forced": E.asymmetry(
            table, configuration, scale="non_vacuous_compliance"),
        "D(B<-A)|graded_0.99": E.delivery_loss(
            table, "B", "A", configuration, scale="graded_threshold"),
    }
    if len(references) == C.N_CORE_REFERENCES:
        f5["Delta_R|vacuity_forced"] = E.delta_r(
            table, configuration, scale="non_vacuous_compliance")
        f5["Xi|vacuity_forced"] = E.xi(
            table, configuration, scale="non_vacuous_compliance")
        f5["Delta_R|graded_0.99"] = E.delta_r(
            table, configuration, scale="graded_threshold")
    families["F5"] = f5

    # ------------------------------------------------------------- F6
    companions = [s for s in table.companions_of("B")]
    families["F6"] = {
        f"vac(B|B+{c})-vac(B solo)": E.vacuity_difference(table, c,
                                                          configuration)
        for c in companions}

    # ------------------------------------------------------------- F8
    if spectrum:
        f8: dict[str, Member] = {f"D(B<-{s})": loss("B", s) for s in spectrum}
        if spectrum_input is not None:
            def beta(picks: Sequence[int]) -> float:
                result = S.estimate(spectrum_input, list(picks))
                return float("nan") if result["degenerate"] else \
                    float(result["slope"])
            f8["beta"] = beta
            for index, slot in enumerate(references, start=1):
                fam = spectrum_input.family_of.get(slot)

                def alpha(picks: Sequence[int], _f=fam) -> float:
                    result = S.estimate(spectrum_input, list(picks))
                    if result["degenerate"]:
                        return float("nan")
                    return float(result["intercepts"].get(_f, float("nan")))
                f8[f"alpha_{index}"] = alpha
        families["F8"] = f8

    # ------------------------------------------------------------- F9
    if has_class:
        families["F9"] = {
            f"D(B<-{C.CLASS_SLOT})": loss("B", C.CLASS_SLOT),
            "Delta_class": E.delta_class(table, configuration)}

    for name in list(families):
        if not families[name]:
            del families[name]
    if design == "reduced":
        families = {k: v for k, v in families.items() if k in ("F1", "F5",
                                                               "F6", "F9")}
    return families


def analyse_family(members: Mapping[str, Member], *, family: str,
                   configuration: str, seed: int, n_blocks: int,
                   resamples: int = C.BOOTSTRAP_RESAMPLES) -> FamilyResult:
    return bootstrap_family(members, seed=seed, configuration=configuration,
                            family=family, n_blocks=n_blocks,
                            resamples=resamples)


def analyse_configuration(table: ObservationTable, configuration: str, *,
                          spectrum_input: S.SpectrumInput | None,
                          design: str, seed: int,
                          resamples: int = C.BOOTSTRAP_RESAMPLES
                          ) -> dict[str, Any]:
    """Every identified family in one configuration, with its intervals."""
    if configuration not in C.CONFIGURATIONS:
        raise ProtocolError(f"{configuration!r} is not a registered "
                            f"configuration {C.CONFIGURATIONS}")
    E.assert_delta_r_forms(table, configuration) \
        if len(E.reference_slots(table)) == C.N_CORE_REFERENCES else None
    families = build_family_members(table, configuration,
                                    spectrum_input=spectrum_input,
                                    design=design)
    out: dict[str, Any] = {}
    for index, (name, members) in enumerate(sorted(families.items())):
        result = analyse_family(members, family=name,
                                configuration=configuration,
                                seed=seed + index, n_blocks=len(table.blocks),
                                resamples=resamples)
        out[name] = {
            "family": name, "configuration": configuration,
            "resamples": result.resamples,
            "critical_value": result.critical_value,
            "sidak_reference": sidak_critical(len(members)),
            "members": {
                k: {"estimate": m.estimate, "se": m.standard_error,
                    "marginal": [m.marginal_lower, m.marginal_upper],
                    "simultaneous": [m.simultaneous_lower,
                                     m.simultaneous_upper],
                    "half_width": m.half_width,
                    "refit_per_replicate": m.refit_per_replicate,
                    "degenerate": m.degenerate}
                for k, m in result.members.items()}}
    return out


def precision_report(families: Mapping[str, Any]) -> dict[str, Any]:
    """§16.2: realised half-widths against the registered preconditions."""
    out: dict[str, Any] = {}
    for family in families.values():
        for name, member in family["members"].items():
            base = name.split("|")[0]
            key = ("D" if base.startswith("D(") and "<-" in base
                   else "Delta_j" if base.startswith("Delta_")
                   and base not in ("Delta_R",) else base)
            required = C.PRECISION_PRECONDITIONS.get(key)
            if required is None:
                continue
            out[f"{family['family']}:{name}"] = {
                "half_width": member["half_width"], "required": required,
                "met": member["half_width"] <= required}
    return out


def f6_gate(families: Mapping[str, Any]) -> dict[str, Any]:
    """§17.4: the vacuity gate on F6, reported as a bound when it binds."""
    f6 = families.get("F6")
    if not f6:
        return {"applicable": False}
    worst = max((m["simultaneous"][1] for m in f6["members"].values()),
                default=0.0)
    return {"applicable": True, "worst_upper": worst,
            "threshold": C.F6_VACUITY_GATE,
            "binds": worst > C.F6_VACUITY_GATE}
