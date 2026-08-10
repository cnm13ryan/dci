"""Confirmatory family cardinalities and the deterministic max-min headline.

Preregistration sections 12.2, 12.11-12.13 and Appendix I. Two things live here
because both are mechanically checkable and both were places where a plausible
shortcut would silently change the guarantee:

  * the cardinalities. The primary one-sided primitive family has
    3 pairs x 4 references x 2 loads x 2 orders x |B_ret| budgets = 48|B_ret|
    members. The compute family has 48, the load and order families 24|B_ret|
    each. Appendix I requires these to be verified against the frozen retained
    budget count rather than counted from whatever rows the analysis happens to
    hold - a family that lost a member would otherwise be protected at a level
    it never earned.
  * the transformation. L_s = min_j L_r over a cell's four references and
    L_Theta = max_s L_s over the frozen search set. This needs NO further
    multiplicity correction, because simultaneous coverage of every primitive
    already protects the whole searched family; applying one anyway would be
    double-counting. The plug-in maximum is computed too, and is labelled
    descriptive: its cell is selected from noisy estimates and can overstate the
    effect, so section 15.5 requires it to travel next to L_Theta and the
    warning, never alone.

v19 makes SEPARATE per-family guarantees. There is deliberately no joint 5% level
across all families, and `describe_guarantees` exists so a report cannot quietly
imply one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

from dci.v19 import ALPHA

N_PAIRS = 3
N_REFERENCES = 4              # exactly four independently admitted references
N_LOADS = 2                   # k in {2, 5}
N_ORDERS = 2                  # o_A and o_Q
MIN_RETAINED_BUDGETS = 3      # fewer fails the compute-treatment gate

# The selected-maximum warning. Required adjacent to every appearance of the
# plug-in headline (section 15.5).
SELECTION_WARNING = (
    "The maximised plug-in estimate is selected from a noisy surface and can "
    "overstate the underlying maximised effect. The claim-bearing statement is "
    "the simultaneous lower bound L_Theta, not this magnitude.")


def primary_family_size(n_retained_budgets: int) -> int:
    """48 |B_ret| (section 12.2)."""
    if n_retained_budgets < MIN_RETAINED_BUDGETS:
        raise ValueError(
            f"{n_retained_budgets} retained budgets is below the frozen minimum "
            f"of {MIN_RETAINED_BUDGETS}; that fails the compute-treatment gate "
            "rather than shrinking the family")
    return N_PAIRS * N_REFERENCES * N_LOADS * N_ORDERS * n_retained_budgets


def compute_family_size() -> int:
    """48: one highest-minus-lowest contrast per pair, reference, load, order."""
    return N_PAIRS * N_REFERENCES * N_LOADS * N_ORDERS


def load_family_size(n_retained_budgets: int) -> int:
    """24 |B_ret|."""
    return N_PAIRS * N_REFERENCES * n_retained_budgets * N_ORDERS


def order_family_size(n_retained_budgets: int) -> int:
    """24 |B_ret|."""
    return N_PAIRS * N_REFERENCES * n_retained_budgets * N_ORDERS


def declared_families(n_retained_budgets: int) -> dict[str, int]:
    """Every confirmatory family and its cardinality."""
    return {
        "primary_primitive_one_sided": primary_family_size(n_retained_budgets),
        "primary_primitive_two_sided": primary_family_size(n_retained_budgets),
        "compute_highest_minus_lowest": compute_family_size(),
        "paired_load": load_family_size(n_retained_budgets),
        "paired_order": order_family_size(n_retained_budgets),
    }


def assert_family_cardinality(name: str, observed: int,
                              n_retained_budgets: int) -> None:
    """Appendix I: the realised family must be the declared family, exactly."""
    declared = declared_families(n_retained_budgets)
    if name not in declared:
        raise ValueError(f"{name!r} is not a declared confirmatory family; "
                         f"known: {sorted(declared)}")
    expected = declared[name]
    if observed != expected:
        raise ValueError(
            f"family {name!r} holds {observed} members but the frozen design "
            f"declares {expected} for {n_retained_budgets} retained budgets. A "
            "family that lost or gained a member is not protected at the level "
            "it reports; this is a fail-closed condition, not a rescaling.")


def describe_guarantees(n_retained_budgets: int,
                        alpha: float = ALPHA) -> dict[str, object]:
    """What may and may not be claimed about multiplicity (section 12.11)."""
    return {
        "per_family_alpha": alpha,
        "families": declared_families(n_retained_budgets),
        "joint_alpha_across_families": None,
        "permitted_statement":
            f"each confirmatory family separately controls its familywise error "
            f"rate at {alpha:.0%}",
        "forbidden_statement":
            f"a single {alpha:.0%} familywise error rate jointly across every "
            "primary and secondary claim",
    }


# --------------------------------------------------------------- the headline

@dataclass(frozen=True)
class Cell:
    """One retained cell s = (pair, budget, load, order) and its references."""
    pair: str
    budget: str
    load: int
    order: str

    @property
    def key(self) -> tuple:
        """The frozen lexicographic tie order: pair, budget, load, order."""
        return (self.pair, self.budget, self.load, self.order)


@dataclass(frozen=True)
class Headline:
    l_theta: float
    plug_in: float
    selected_cell: Optional[tuple]
    per_cell_lower: dict[tuple, float]
    per_cell_plug_in: dict[tuple, float]
    warning: str = SELECTION_WARNING


def cell_lower_bound(reference_bounds: Mapping[str, float]) -> float:
    """L_s = min_j L_r: robustness to the least favourable admitted reference."""
    if len(reference_bounds) != N_REFERENCES:
        raise ValueError(
            f"a cell has exactly {N_REFERENCES} reference-specific primitives, "
            f"got {len(reference_bounds)}. A cell missing a reference cannot be "
            "reduced to a least-favourable bound.")
    return min(reference_bounds.values())


def global_headline(cells: Mapping[Cell, Mapping[str, float]],
                    estimates: Optional[Mapping[Cell, Mapping[str, float]]] = None
                    ) -> Headline:
    """L_Theta = max_s min_j L_r over the frozen search set.

    Deterministic: no additional multiplicity correction, because simultaneous
    primitive coverage already protects every member of the searched family.
    """
    if not cells:
        raise ValueError("the frozen search set is empty")
    lower = {c.key: cell_lower_bound(b) for c, b in cells.items()}
    plug_in = {c.key: min(estimates[c].values()) for c in cells} if estimates else {}

    best = max(lower.values())
    selected = None
    if plug_in:
        top = max(plug_in.values())
        # Exact ties resolve by the frozen lexicographic order, never by which
        # dictionary key happened to come first.
        selected = min(k for k, v in plug_in.items() if v == top)
    return Headline(l_theta=best,
                    plug_in=max(plug_in.values()) if plug_in else float("nan"),
                    selected_cell=selected, per_cell_lower=lower,
                    per_cell_plug_in=plug_in)


ROBUST_POSITIVE_SESOI = "ROBUST_POSITIVE_SESOI"
ROBUST_POSITIVE = "ROBUST_POSITIVE"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
FEASIBILITY_MEASUREMENT_PILOT = "FEASIBILITY_MEASUREMENT_PILOT"


def headline_label(l_theta: float, sesoi: float,
                   feasibility_pilot: bool = False) -> str:
    """The mutually exclusive primary result states (section 15.1)."""
    if feasibility_pilot:
        # Frozen prospectively: a descriptive magnitude cannot promote it.
        return FEASIBILITY_MEASUREMENT_PILOT
    if l_theta > sesoi:
        return ROBUST_POSITIVE_SESOI
    if l_theta > 0:
        return ROBUST_POSITIVE
    return NOT_ESTABLISHED
