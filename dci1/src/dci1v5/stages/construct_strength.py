"""§34 D17: is $B$ still the construct it is named after at the selected $m^*$?

**The problem the red team's R14 names.** v4r4's focal grid ended at $m = 12$
and its models repeatedly selected the last available rung; v5 widens the grid
to 16 precisely so that the operating point is not chosen by exhaustion. But
§12.3 selects the rung whose *compliance* is nearest 0.80, and compliance is a
behavioural quantity. 0.80 compliance at $m = 13$ is a real constraint on how
a model writes; *every word at most thirteen letters* is, as a **construct**,
close to a null instruction in ordinary English. The focal band is defined on
compliance and says nothing about construct strength, so the grid extension
buys band membership and can pay for it in what $B$ means.

**What this module is, and what it deliberately is not.** It is the interface:
named quantities, each with a formula and the provenance of where the formula
comes from; a measurement over the whole registered grid; the neighbours of
the candidate $m^*$; and a floor check that binds to §34 D17. It contains **no
threshold**. A construct floor is a registered value with a derivation, and
inventing one here would be exactly the move §34 exists to stop --- the code
needs a number, the number gets chosen by whoever writes the line, and the
choice is never recorded as one.

So ``assert_construct_floor`` has both branches, neither is reachable while
D17 is open, and the ``floor`` branch refuses **even when D17 is closed** if
the closure did not supply a ``FloorSpec``: which quantity, what value, and
the derivation. A floor with no derivation is a threshold nobody chose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions

__all__ = ["ConstructQuantity", "QUANTITIES", "QUANTITY_IDS", "FloorSpec",
           "construct_strength", "measure", "assert_construct_floor",
           "grid_boundary_status"]


@dataclass(frozen=True)
class ConstructQuantity:
    """One named way to say how much work $B$ is doing at a severity.

    ``direction`` is ``"higher_is_stronger"`` or ``"lower_is_stronger"`` and
    is part of the definition, not a convention a caller supplies: a floor on
    a quantity whose direction is ambiguous is a floor that can be read two
    ways.
    """

    id: str
    description: str
    formula: str
    direction: str
    provenance: str

    def value(self, *, chance_compliance: float,
              solo_compliance: float | None = None,
              long_word_share: float | None = None,
              m: int | None = None) -> float | None:
        if self.id == "chance_compliance":
            return chance_compliance
        if self.id == "chance_bite":
            return 1.0 - chance_compliance
        if self.id == "instruction_lift":
            if solo_compliance is None:
                return None
            return solo_compliance - chance_compliance
        if self.id == "long_word_share":
            return long_word_share
        if self.id == "grid_headroom":
            if m is None:
                return None
            top = max(tuple(C.FOCAL_GRID) + tuple(C.FOCAL_EXTENSION))
            return float(top - m)
        raise ProtocolError(f"no value rule for quantity {self.id!r}")


#: The registered candidate quantities. Each is *computable from data v5
#: already collects*, which is why they are the candidates: a floor on a
#: quantity that needs a new measurement would need a new gate.
QUANTITIES: tuple[ConstructQuantity, ...] = (
    ConstructQuantity(
        "chance_compliance",
        "how often an answer written with no instruction already satisfies B "
        "at this severity",
        "kappa_B(m) = P(B passes | unconstrained)",
        "lower_is_stronger",
        "§12.3's standing proposal reports exactly this at m*; §11.2 defines "
        "kappa"),
    ConstructQuantity(
        "chance_bite",
        "the share of unconstrained answers the instruction would have to "
        "change",
        "1 - kappa_B(m)",
        "higher_is_stronger",
        "the complement of the reported quantity, named separately because a "
        "floor reads more naturally as a minimum than as a maximum"),
    ConstructQuantity(
        "instruction_lift",
        "how much stating B moves compliance above chance at this severity",
        "P(B passes | B stated) - kappa_B(m)",
        "higher_is_stronger",
        "§13.4's INSTRUCTION_LIFT_MIN applies this quantity to a *reference*; "
        "it is listed here because the same quantity is defined for B and "
        "§13.4 supplies no value for B"),
    ConstructQuantity(
        "long_word_share",
        "the share of words in unconstrained answers longer than m letters",
        "E[ #{words with > m letters} / #words | unconstrained ]",
        "higher_is_stronger",
        "the graded score of B is 1 - this quantity, so it is already "
        "computed on every row (§7.3's graded definitions)"),
    ConstructQuantity(
        "grid_headroom",
        "how far the selected severity sits from the top of the registered "
        "grid",
        "max(FOCAL_GRID + FOCAL_EXTENSION) - m",
        "higher_is_stronger",
        "§12.3's bracketing status; a headroom of zero is "
        "OPERATING_POINT_AT_GRID_BOUNDARY and is why the grid was widened"),
)
QUANTITY_IDS = tuple(q.id for q in QUANTITIES)
_BY_ID = {q.id: q for q in QUANTITIES}


@dataclass(frozen=True)
class FloorSpec:
    """A registered construct floor: a quantity, a value, and a derivation.

    All three are required. A quantity with no value cannot refuse anything;
    a value with no derivation is a threshold nobody chose; and a derivation
    that does not name the quantity does not say what the value bounds.
    """

    quantity: str
    value: float
    derivation: str
    decided_by: str
    decided_on: str

    def __post_init__(self) -> None:
        if self.quantity not in _BY_ID:
            raise ProtocolError(
                f"{self.quantity!r} is not a registered construct-strength "
                f"quantity; registered: {QUANTITY_IDS}")
        if not isinstance(self.value, (int, float)):
            raise ProtocolError("a construct floor is a number")
        for name in ("derivation", "decided_by", "decided_on"):
            if not str(getattr(self, name)).strip():
                raise ProtocolError(
                    f"a registered construct floor requires {name}; a floor "
                    "without one is a threshold nobody chose")

    def satisfied_by(self, value: float) -> bool:
        quantity = _BY_ID[self.quantity]
        if quantity.direction == "higher_is_stronger":
            return value >= self.value
        return value <= self.value

    def as_dict(self) -> dict[str, Any]:
        return {"quantity": self.quantity, "value": self.value,
                "direction": _BY_ID[self.quantity].direction,
                "derivation": self.derivation,
                "decided_by": self.decided_by, "decided_on": self.decided_on}


def construct_strength(*, m: int, chance_compliance: float,
                       solo_compliance: float | None = None,
                       long_word_share: float | None = None
                       ) -> dict[str, Any]:
    """Every registered quantity at one severity, with its definition."""
    values: dict[str, Any] = {}
    for quantity in QUANTITIES:
        values[quantity.id] = {
            "value": quantity.value(chance_compliance=chance_compliance,
                                    solo_compliance=solo_compliance,
                                    long_word_share=long_word_share, m=m),
            "direction": quantity.direction,
            "formula": quantity.formula,
            "provenance": quantity.provenance,
        }
    return {"m": m, "quantities": values}


def grid_boundary_status(m_star: int) -> list[str]:
    """§12.3: an operating point at either end of the grid is a status."""
    grid = sorted(set(tuple(C.FOCAL_GRID) + tuple(C.FOCAL_EXTENSION)))
    if m_star in (grid[0], grid[-1]):
        return ["OPERATING_POINT_AT_GRID_BOUNDARY"]
    return []


def measure(curve: Mapping[int, float], *, m_star: int,
            solo_curve: Mapping[int, float] | None = None,
            long_word_share: Mapping[int, float] | None = None
            ) -> dict[str, Any]:
    """The report §12.3 requires whether or not a floor is registered.

    ``curve`` maps severity -> B's **chance** compliance. The report carries
    the candidate $m^*$, its immediate neighbours in the measured grid, every
    registered quantity at each, and the whole curve --- which is what the
    standing proposal asks to be reported *instead of* a floor, so it is
    produced on both branches of D17 and not only on one.
    """
    if m_star not in curve:
        raise ProtocolError(
            f"m* = {m_star} is not in the measured curve {sorted(curve)}; the "
            "construct-strength report is computed on measured severities")
    ordered = sorted(curve)
    index = ordered.index(m_star)
    neighbours = [m for m in (ordered[index - 1] if index else None,
                              ordered[index + 1]
                              if index + 1 < len(ordered) else None)
                  if m is not None]

    def _at(m: int) -> dict[str, Any]:
        return construct_strength(
            m=m, chance_compliance=curve[m],
            solo_compliance=(solo_curve or {}).get(m),
            long_word_share=(long_word_share or {}).get(m))

    return {
        "m_star": m_star,
        "at_m_star": _at(m_star),
        "neighbours": {str(m): _at(m) for m in neighbours},
        "curve": {str(m): curve[m] for m in ordered},
        "grid": sorted(set(tuple(C.FOCAL_GRID) + tuple(C.FOCAL_EXTENSION))),
        "statuses": grid_boundary_status(m_star),
        "limitation": "a high m* makes B a weak instrument on this model "
                      "(§29); the whole curve is reported so a reader can "
                      "see how weak",
        "red_team": "R14",
    }


def assert_construct_floor(m_star: int, *, chance_compliance_at_m_star: float,
                           curve: Mapping[int, float] | None = None,
                           solo_curve: Mapping[int, float] | None = None,
                           long_word_share: Mapping[int, float] | None = None,
                           floor: FloorSpec | None = None) -> dict[str, Any]:
    """§34 D17, as the one call that decides whether $m^*$ stands.

    Both branches exist and neither is reachable while D17 is open.

    * ``no_floor`` --- the standing proposal. No selection is refused; the
      realised $m^*$, B's chance compliance at $m^*$ and B's whole curve are
      reported, and §29 states the limitation.
    * ``floor`` --- a registered floor is applied. **The closure must supply
      it**: this call refuses a ``floor`` branch with no ``FloorSpec``, and
      refuses again if the spec's quantity cannot be computed from what was
      measured. No threshold is invented here.
    """
    report = (measure(curve, m_star=m_star, solo_curve=solo_curve,
                      long_word_share=long_word_share)
              if curve is not None
              else measure({m_star: chance_compliance_at_m_star},
                           m_star=m_star, solo_curve=solo_curve,
                           long_word_share=long_word_share))

    def _no_floor() -> dict[str, Any]:
        return {**report, "floor_registered": False,
                "chance_compliance_at_m_star": chance_compliance_at_m_star,
                "reported": "the realised m*, B's chance compliance at m*, "
                            "and B's whole curve",
                "selection_refused": False}

    def _floor() -> dict[str, Any]:
        if floor is None:
            raise ProtocolError(
                "§34 D17 was closed at 'floor' and no FloorSpec accompanies "
                "it. A construct floor is a registered value with a "
                "derivation; this implementation does not invent one, and the "
                "closure must supply the quantity, the value and the "
                f"derivation. Registered quantities: {QUANTITY_IDS}")
        measured = report["at_m_star"]["quantities"][floor.quantity]["value"]
        if measured is None:
            raise ProtocolError(
                f"§34 D17's floor is registered on {floor.quantity!r} and "
                "that quantity was not measured at m*; a floor on an "
                "unmeasured quantity refuses nothing and admits nothing")
        satisfied = floor.satisfied_by(measured)
        return {**report, "floor_registered": True, "floor": floor.as_dict(),
                "measured": measured, "satisfied": satisfied,
                "chance_compliance_at_m_star": chance_compliance_at_m_star,
                "selection_refused": not satisfied,
                "status": None if satisfied else "FOCAL_RANGE_EXHAUSTED",
                "reason": None if satisfied else (
                    f"m* = {m_star} satisfies §12.3's compliance band and "
                    f"fails the registered construct floor: "
                    f"{floor.quantity} = {measured} against {floor.value}")}

    return decisions.choice("D17", {"no_floor": _no_floor, "floor": _floor},
                            where="stages.regime.assert_construct_floor")()


def candidate_report(curve: Mapping[int, float], *,
                     candidates: Sequence[int]) -> list[dict[str, Any]]:
    """Every candidate severity §12.3 considered, with its strength.

    Written so that a reader of the Gate 2 record can see what the compliance
    band admitted *and* what each admitted point would have cost as a
    construct, whichever way D17 closes.
    """
    return [construct_strength(m=m, chance_compliance=curve[m])
            for m in sorted(candidates) if m in curve]
