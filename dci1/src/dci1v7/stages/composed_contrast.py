"""§18 stage 11, ``GATE_4_COMPOSED_CONTRAST`` (v7): the composed contrast,
projected on §6.2's reserved composed set --- recorded, never terminal.

**What Gate 4 was.** v5 and v6 generated every registered cell type on the 24
composed-validation topics at ``M_CAL`` and asked, of every constraint in
every cell, whether its compliance lay inside [0.05, 0.95]; one outside ended
the replication ``COMPOSED_HEADROOM_FAILURE``. ``gemma-3n-e4b-it`` ended
there twice --- under v5 on a companion slot, and under v6 on ``solo:CL`` =
0.958, the broad-class control's own solo compliance, a quantity that enters
no primary estimand at all.

**What Gate 4 is.** The same rows, read as the estimators read them: the
rows become an ``ObservationTable`` over the 24 topics as blocks, every
registered contrast the admitted arms supply is formed **inside each block**
by the same functions the confirmatory analysis uses, each family is
bootstrapped over topics with §17.1's one-index-draw-per-replicate
construction, every contrast is read through ``analysis/boundary.py``, and
the confirmatory half-width of each is projected. The result is a
projection of what the 384 blocks will estimate --- labelled
``PROJECTION_NOT_REGISTERED_FOR_INFERENCE`` and read by no rule --- beside
the per-cell composed table v5 recorded, with each entry's proximity to the
descriptive band. It has one outcome, ``PASS``, and the freeze binds it.

**Why nothing here decides.** A structural zero on 24 topics is weak evidence
of one on 384; dropping an arm on it would be a design decision taken from
a composed outcome, which §12.5 and §13.11 exist to keep out of the study;
and terminating on it would discard every identified estimand for want of
one. The confirmatory analysis computes the same readings on the blocks
that carry the claim, and those are what a statement carries. This stage's
value is that they were projected, on the same rule, **before** the freeze
--- so a qualification at the end cannot be a reading invented after the
number was seen.

**It selects nothing.** There is no path from anything here to a different
reference, and ``gates_run.assert_no_substitution_path`` is asserted on the
module that runs it. §13.11's schema refusal still rejects any composed
quantity reaching a selection function.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v7.analysis import boundary, estimators
from dci1v7.analysis.bootstrap import bootstrap_family
from dci1v7.analysis.observations import ObservationTable
from dci1v7.protocol import constants as C

__all__ = [
    "GATE4_OUTCOME",
    "PROJECTED_FAMILIES",
    "cell_proximity",
    "composed_table",
    "member_vector",
    "projection",
]

#: The only outcome this stage can record.
GATE4_OUTCOME = "PASS"

#: The families whose members are fixed linear or reciprocal contrasts of
#: cell means and can therefore be projected from one composed table. F5's
#: recodings, F6's vacuity differences and F8's fit parameters are computed
#: on the confirmatory blocks only; ``delta_difficulty`` refits per replicate
#: and is excluded from F1 here, which the record says.
PROJECTED_FAMILIES: tuple[str, ...] = ("F1", "F2", "F3", "F4", "F9", "F10",
                                       "F11")
NOT_PROJECTED_MEMBERS: tuple[str, ...] = ("delta_difficulty",)


def member_vector(table: ObservationTable, member: str,
                  configuration: str | None) -> list[float] | None:
    """One registered member's per-block vector, by the estimator that
    defines it, or ``None`` when the admitted design supplies no cell for it.

    The mapping is explicit rather than derived from ``boundary.composition``
    so that the projection is the **estimator's** value; ``tests_v7`` asserts
    that the composition-derived vector agrees with it to 1e-12, which is
    what makes the boundary reading a reading of the same contrast.
    """
    builders: dict[str, Callable[[], Sequence[float]]] = {}
    cfg = configuration
    if member in NOT_PROJECTED_MEMBERS:
        return None
    if member.startswith("D(") and "<-" in member and member.endswith(")"):
        outcome, companion = member[2:-1].split("<-")
        if outcome == "Rbar":
            builders[member] = lambda: estimators.d_rbar_from(
                table, companion, cfg)
        elif companion == "Rbar'":
            builders[member] = lambda: estimators.d_rbar_rbar(table, cfg)
        else:
            builders[member] = lambda: estimators.delivery_loss(
                table, outcome, companion, cfg)
    elif member == "Lambda":
        builders[member] = lambda: estimators.asymmetry(table, cfg)
    elif member == "Delta_R":
        builders[member] = lambda: estimators.delta_r(table, cfg)
    elif member.startswith("Delta_") and member[6:].isdigit():
        slot = C.CORE_SLOTS[int(member[6:]) - 1]
        builders[member] = lambda: estimators.delta_j(table, slot, cfg)
    elif member == "Delta_near":
        builders[member] = lambda: estimators.delta_near(table, cfg)
    elif member == "Delta_broad":
        builders[member] = lambda: estimators.delta_broad(table, cfg)
    elif member == "Delta^A":
        builders[member] = lambda: estimators.delta_a(table, cfg)
    elif member == "Xi":
        builders[member] = lambda: estimators.xi(table, cfg)
    elif member in C.FAMILY_MEMBERS["F11"]:
        builders[member] = lambda: estimators.order_contrast(table, member)
    else:
        return None
    try:
        return list(builders[member]())
    except (IntegrityError, ProtocolError):
        # A cell the member needs is not on this table, or the estimator
        # refuses its shape: the member is not projectable here. A defect in
        # this module propagates rather than becoming a missing projection.
        return None


def composed_table(rows: Sequence[Mapping[str, Any]],
                   shape: Mapping[str, Sequence[str]],
                   slot_map: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """The per-cell, per-slot compliance table v5 recorded, kept as a
    descriptive record. Row count for the unconstrained cell."""
    table: dict[str, dict[str, float]] = {}
    for cell_id, slots in shape.items():
        cell_rows = [r for r in rows if r["cell_id"] == cell_id]
        if not slots:
            table[cell_id] = {"unconstrained": float(len(cell_rows))}
            continue
        entry: dict[str, float] = {}
        for slot in slots:
            constraint = slot_map[slot]
            passes = [float(s["passed"]) for r in cell_rows
                      for s in r["scores"]
                      if s["present"] and s["kind"] == constraint.kind
                      and s["severity"] == constraint.severity]
            entry[slot] = sum(passes) / len(passes) if passes else 0.0
        table[cell_id] = entry
    return table


def cell_proximity(table: Mapping[str, Mapping[str, float]],
                   shape: Mapping[str, Sequence[str]]
                   ) -> list[dict[str, Any]]:
    """Every cell x slot entry against the DESCRIPTIVE band. Gates nothing."""
    low, high = C.COMPOSED_PROXIMITY_BAND
    out: list[dict[str, Any]] = []
    for cell_id, entry in table.items():
        if not shape.get(cell_id):
            continue
        for slot, value in entry.items():
            out.append({"cell": cell_id, "slot": slot, "compliance": value,
                        "near_boundary": ("floor" if value < low else
                                          "ceiling" if value > high
                                          else None)})
    return out


def _precondition_for(member: str) -> float | None:
    from dci1v7.analysis.claims import precondition_key
    return C.PRECISION_PRECONDITIONS.get(precondition_key(member))


def projection(table: ObservationTable, *, arms: Sequence[str], seed: int,
               resamples: int = C.BOOTSTRAP_RESAMPLES) -> dict[str, Any]:
    """Every projectable registered contrast on the composed table.

    Per family in ``PROJECTED_FAMILIES``, per configuration (or across them
    for F11): the members the admitted arms supply, bootstrapped together so
    the simultaneous interval is the family's; per member, the boundary
    reading, the allowance-widened marginal interval, and the projected
    confirmatory half-width against its registered precision precondition.
    """
    references = estimators.reference_slots(table)
    families: dict[str, Any] = {}
    not_computable: list[str] = []
    statuses: set[str] = set()
    any_structural_zero = False
    for family in PROJECTED_FAMILIES:
        members = [m for m in C.FAMILY_MEMBERS[family]
                   if m not in NOT_PROJECTED_MEMBERS]
        configurations = ([None] if family in C.CROSS_CONFIGURATION_FAMILIES
                          else list(C.CONFIGURATIONS))
        for configuration in configurations:
            key = f"{family}:{configuration or 'cross'}"
            vectors = {m: member_vector(table, m, configuration)
                       for m in members}
            usable = {m: v for m, v in vectors.items() if v is not None}
            missing = sorted(m for m, v in vectors.items() if v is None)
            not_computable += [f"{key}:{m}" for m in missing]
            if not usable:
                families[key] = {"family": family,
                                 "configuration": configuration or "cross",
                                 "members": {}, "not_computable": missing,
                                 "reason": "the admitted arm set supplies no "
                                           "cell for any member"}
                continue
            result = bootstrap_family(
                usable, seed=seed, configuration=configuration or "cross",
                family=family, n_blocks=len(table.blocks),
                resamples=resamples)
            entries: dict[str, Any] = {}
            for member, out in result.members.items():
                reading = boundary.contrast_boundary_from_table(
                    table, member, configuration, references=references)
                lower, upper = boundary.apply_allowance(
                    out.marginal_lower, out.marginal_upper, reading)
                projected = None
                parts = boundary.composition(
                    member, references=references or C.CORE_SLOTS)
                if parts is not None and reading is not None:
                    constituents = []
                    for part, cell in zip(parts, reading["constituents"]):
                        cfg = part.configuration or configuration
                        vec = (estimators.solo_vector(table, part.outcome)
                               if part.role == "solo" else
                               estimators.composed_vector(
                                   table, part.outcome, part.companion, cfg))
                        constituents.append((part, vec))
                    projected = boundary.projected_confirmatory_halfwidth(
                        usable[member], constituents, m_measured=C.M_CAL,
                        family_size=len(members))
                precondition = _precondition_for(member) \
                    if member not in ("Xi",) and not member.startswith(
                        "D(Rbar") and member != "D(Rbar<-Rbar')" else None
                if reading is not None:
                    statuses.update(reading["statuses"])
                    any_structural_zero |= bool(reading["structural_zero"])
                entries[member] = {
                    "estimate": out.estimate,
                    "standard_error": out.standard_error,
                    "marginal_lower": out.marginal_lower,
                    "marginal_upper": out.marginal_upper,
                    "simultaneous_lower": out.simultaneous_lower,
                    "simultaneous_upper": out.simultaneous_upper,
                    "decision_lower_with_allowance": lower,
                    "decision_upper_with_allowance": upper,
                    "degenerate": out.degenerate,
                    "boundary": reading,
                    "statuses": list(reading["statuses"]) if reading else [],
                    "projected_confirmatory": projected,
                    "precision_precondition": precondition,
                    "projected_meets_precondition": (
                        None if projected is None or precondition is None
                        or not projected.get("projected")
                        else projected["half_width"] <= precondition),
                    "label": "PROJECTION_NOT_REGISTERED_FOR_INFERENCE",
                }
            families[key] = {"family": family,
                             "configuration": configuration or "cross",
                             "n_blocks": len(table.blocks),
                             "resamples": resamples,
                             "critical_value": result.critical_value,
                             "members": entries,
                             "not_computable": missing}
    return {
        "outcome": GATE4_OUTCOME,
        "terminates": False,
        "families": families,
        "n_blocks": len(table.blocks),
        "resamples": resamples,
        "statuses": sorted(statuses),
        "any_structural_zero": any_structural_zero,
        "not_computable": not_computable,
        "not_projected_members": list(NOT_PROJECTED_MEMBERS),
        "references": list(references),
        "label": "PROJECTION_NOT_REGISTERED_FOR_INFERENCE",
        "read_by": [],
        "what_this_is":
            "every registered contrast the admitted arms supply, formed "
            "inside each of the 24 composed topics by the confirmatory "
            "estimators, bootstrapped over topics, and read through the v7 "
            "§13.14 boundary rule. A projection of what the 384 confirmatory "
            "blocks will estimate; no rule reads it and nothing here "
            "terminates, drops an arm or moves a threshold",
    }
