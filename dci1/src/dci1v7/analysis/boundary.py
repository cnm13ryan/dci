"""v7 §13.14: what a composed rate at 0 or 1 does to a **contrast**.

v5 and v6 asked, of every composed cell, whether its compliance lay inside an
absolute band, and ended the replication when one did not. That is a
statement about a marginal arm rate. The quantity the study estimates is a
paired contrast between composed cells --- ``Delta_R`` is
``mean_j P(B | B+R_j) - P(B | B+A)`` inside each block --- and a rate at a
boundary does not make a difference of rates undefined. Three things it can
do, each a property of the **contrast** and each measured here:

1. **Structural zero.** When every composed cell the contrast differences
   sits at the *same* exact boundary in every block, the contrast is 0 with
   zero *observed* variance. The decision interval is then the allowance of
   reading 2 alone --- symmetric about zero, ``+/- boundary_halfwidth(n)``
   --- so no directional classification is reachable by construction, and
   an equivalence-type classification is licensed exactly when that
   interval satisfies the registered rule: at 384 blocks it lies inside
   the +/-0.10 region and meets the 0.05 precondition, at Gate 4's 24
   topics it does neither. The status and a registered sentence say that
   the bound is the allowance and not observed variation. (Revised
   2026-08-28 by the §13.14 boundary audit: the earlier veto on every
   classification was not a statistical safeguard --- the allowance
   interval is a valid >= 95% interval there and an equivalence false
   positive needs every draw perfect while |Delta_R| >= 0.10 --- and it
   made 3072/3072 perfect draws weaker evidence than 3071/3072.)
2. **An arm at a boundary.** A cell whose every block mean is exactly 0 or 1
   contributes no variance to the block bootstrap, so the interval of any
   contrast it enters is too narrow in the direction that would move that
   cell off its boundary. The only sampling statement the design licenses
   about such a rate is the Wilson interval at the block count: at 384
   blocks a rate observed at 1.0 is at least 0.990. The decision interval is
   therefore widened, in the open direction only, by each boundary
   constituent's weight times that half-width. Conservative, small (under
   0.01 per constituent at 384 blocks) and derived rather than chosen.
3. **A compressed direction.** For a two-arm contrast with observed arm
   levels ``L_P`` (positive weight) and ``L_N`` (negative weight), the
   contrast cannot exceed ``+SESOI`` when ``L_N > 1 - SESOI`` or
   ``L_P < SESOI``, and cannot fall below ``-SESOI`` when ``L_P > 1 - SESOI``
   or ``L_N < SESOI`` --- by arithmetic, not by sampling. A classification
   in the open direction is as informative as ever; a classification that
   *depends on* the compressed direction being closed --- L3c's "upper bound
   below 0.10" when B is delivered under A at 0.92 --- is recorded as
   bounded by the arm level that closes it. The licensing rule reads the
   interval exactly as registered; the status says why the number came out
   as it did.

Nothing here terminates, drops an arm, or moves a threshold. The same
function runs on the 384-block confirmatory table, on Gate 4's 24-topic
composed table and on Gate 2.75's 192-topic probe, so the qualification a
statement carries at the end was projected, on the same rule, before the
freeze.
"""
from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v7.analysis.intervals import wilson
from dci1v7.protocol import constants as C

__all__ = [
    "ARM_AT_BOUNDARY",
    "RANGE_COMPRESSED",
    "STRUCTURAL_ZERO",
    "Constituent",
    "apply_allowance",
    "boundary_halfwidth",
    "classify_cell",
    "composition",
    "contrast_boundary",
    "contrast_boundary_from_table",
    "projected_confirmatory_halfwidth",
    "two_arm_levels",
]

STRUCTURAL_ZERO = "COMPOSED_CONTRAST_STRUCTURAL_ZERO"
ARM_AT_BOUNDARY = "COMPOSED_ARM_AT_BOUNDARY"
RANGE_COMPRESSED = "COMPOSED_CONTRAST_RANGE_COMPRESSED"
assert {STRUCTURAL_ZERO, ARM_AT_BOUNDARY, RANGE_COMPRESSED} == set(
    C.V7_IDENTIFICATION_STATUSES)

_TOL = 1e-12


@dataclass(frozen=True)
class Constituent:
    """One cell mean a linear contrast reads, with its signed weight.

    ``configuration`` is ``None`` for a within-configuration member --- the
    cell is read in whichever configuration the contrast is evaluated in ---
    and named for F11's order contrasts, which difference the two
    configurations of one cell.
    """

    role: str                    # "solo" | "composed"
    outcome: str
    companion: str | None
    weight: float
    configuration: str | None = None

    def label(self, configuration: str | None) -> str:
        cfg = self.configuration or configuration or "?"
        if self.role == "solo":
            return f"solo:{self.outcome}"
        return f"{self.outcome}|{self.outcome}+{self.companion}@{cfg}"


def _loss(outcome: str, companion: str) -> tuple[Constituent, ...]:
    return (Constituent("solo", outcome, None, +1.0),
            Constituent("composed", outcome, companion, -1.0))


def composition(member: str, *,
                references: Sequence[str] = C.CORE_SLOTS,
                near_form: Sequence[str] = C.NEAR_FORM_SLOTS,
                class_slot: str = C.CLASS_SLOT
                ) -> tuple[Constituent, ...] | None:
    """The linear cell composition of a registered member, or ``None``.

    ``None`` for the members that are not a fixed linear combination of cell
    means --- ``delta_difficulty`` and the fit parameters, which refit per
    replicate --- and for ``Xi``, whose reciprocal bracket is linear but
    whose boundary reading is taken from ``Delta_R``'s constituents plus the
    reciprocal cells separately by the caller. Every other registered member
    of F1-F3 and F9-F11 is here, in the algebraic form the estimator uses:
    the solo baseline is present for ``D`` and ``Lambda`` and cancelled for
    every ``Delta``-type quantity, exactly as §11.3 states.
    """
    refs = tuple(references)
    if member == "D(A<-B)":
        return _loss("A", "B")
    if member == "D(B<-A)":
        return _loss("B", "A")
    if member.startswith("D(") and "<-" in member and member.endswith(")"):
        outcome, companion = member[2:-1].split("<-")
        return _loss(outcome, companion)
    if member == "Lambda":
        return _loss("B", "A") + tuple(
            Constituent(c.role, c.outcome, c.companion, -c.weight)
            for c in _loss("A", "B"))
    if member == "Delta_R":
        return tuple(Constituent("composed", "B", r, 1.0 / len(refs))
                     for r in refs) + (Constituent("composed", "B", "A", -1.0),)
    if member.startswith("Delta_") and member[6:].isdigit():
        r = refs[int(member[6:]) - 1]
        return (Constituent("composed", "B", r, +1.0),
                Constituent("composed", "B", "A", -1.0))
    if member == "Delta_near":
        near = tuple(near_form)
        return tuple(Constituent("composed", "B", n, 1.0 / len(near))
                     for n in near) + (Constituent("composed", "B", "A", -1.0),)
    if member == "Delta_broad":
        return (Constituent("composed", "B", class_slot, +1.0),
                Constituent("composed", "B", "A", -1.0))
    if member == "Delta^A":
        return tuple(Constituent("composed", "A", r, 1.0 / len(refs))
                     for r in refs) + (Constituent("composed", "A", "B", -1.0),)
    first, second = C.OUTCOME_FIRST, C.OUTCOME_SECOND
    if member == "Ord_A":
        return (Constituent("composed", "A", "B", +1.0, second),
                Constituent("composed", "A", "B", -1.0, first))
    if member == "Ord_B":
        return (Constituent("composed", "B", "A", +1.0, second),
                Constituent("composed", "B", "A", -1.0, first))
    if member == "Ord_Lambda":
        return (Constituent("composed", "B", "A", +1.0, second),
                Constituent("composed", "B", "A", -1.0, first),
                Constituent("composed", "A", "B", -1.0, second),
                Constituent("composed", "A", "B", +1.0, first))
    if member == "Ord_Rbar":
        return tuple(Constituent("composed", "B", r, 1.0 / len(refs), second)
                     for r in refs) + tuple(
            Constituent("composed", "B", r, -1.0 / len(refs), first)
            for r in refs)
    if member == "Ord_CL":
        return (Constituent("composed", "B", class_slot, +1.0, second),
                Constituent("composed", "B", class_slot, -1.0, first))
    return None


def classify_cell(values: Sequence[float], *,
                  band: tuple[float, float] = C.COMPOSED_PROXIMITY_BAND
                  ) -> dict[str, Any]:
    """One cell's block means: its level, and whether it is AT or NEAR an edge.

    ``exact_boundary`` is the fact that matters to inference --- every block
    mean is exactly 0 or exactly 1, so the bootstrap sees no variance.
    ``near_boundary`` is descriptive only: the level lies outside the
    proximity band. Neither terminates anything.
    """
    vector = [float(v) for v in values]
    if not vector:
        raise ProtocolError("a cell classification needs at least one block")
    level = sum(vector) / len(vector)
    exact = None
    if all(abs(v) < _TOL for v in vector):
        exact = "floor"
    elif all(abs(v - 1.0) < _TOL for v in vector):
        exact = "ceiling"
    near = None
    if level < band[0]:
        near = "floor"
    elif level > band[1]:
        near = "ceiling"
    return {"level": level, "n_blocks": len(vector),
            "exact_boundary": exact, "near_boundary": near,
            "proximity_band": list(band)}


def boundary_halfwidth(n_blocks: int, *,
                       level: float = C.BOUNDARY_ALLOWANCE_LEVEL) -> float:
    """How far a rate observed at 0 or 1 over ``n_blocks`` may truly sit
    from that boundary: the Wilson half-width at the block count.

    Symmetric --- ``1 - wilson(1, n).lower == wilson(0, n).upper`` --- and
    taken at the block level because the block is the unit (§14.1) and draws
    inside one are correlated.
    """
    if n_blocks <= 0:
        raise ProtocolError("the boundary allowance needs a block count")
    if abs(level - 0.95) > 1e-12:
        raise ProtocolError(
            "the boundary allowance is registered at §13.4's 95% level")
    return 1.0 - wilson(1.0, n_blocks)[0]


def two_arm_levels(constituents: Sequence[tuple[Constituent, float]]
                   ) -> dict[str, Any] | None:
    """The positive-arm and negative-arm levels of a two-arm contrast.

    A contrast is two-arm when its positive weights sum to one and its
    negative weights sum to minus one: every ``D``, every ``Delta``-type
    quantity and every order contrast except ``Ord_Lambda``. ``Lambda`` and
    ``Ord_Lambda`` are differences of two such and have no single arm level
    to compress; they return ``None`` and carry no compression reading.
    """
    pos = [(c, lvl) for c, lvl in constituents if c.weight > 0]
    neg = [(c, lvl) for c, lvl in constituents if c.weight < 0]
    if not pos or not neg:
        return None
    wp = sum(c.weight for c, _ in pos)
    wn = -sum(c.weight for c, _ in neg)
    if abs(wp - 1.0) > 1e-9 or abs(wn - 1.0) > 1e-9:
        return None
    return {"positive_arm": sum(c.weight * lvl for c, lvl in pos),
            "negative_arm": sum(-c.weight * lvl for c, lvl in neg),
            "positive_arm_cells": [c.label(c.configuration) for c, _ in pos],
            "negative_arm_cells": [c.label(c.configuration) for c, _ in neg]}


def contrast_boundary(member: str,
                      constituents: Sequence[tuple[Constituent,
                                                   Sequence[float]]],
                      *, configuration: str | None,
                      band: tuple[float, float] = C.COMPOSED_PROXIMITY_BAND
                      ) -> dict[str, Any]:
    """The three readings above, for one contrast from its cell vectors.

    ``constituents`` pairs each constituent with its per-block vector. All
    vectors must have the same length --- they are the same blocks, which is
    what makes the contrast paired.
    """
    if not constituents:
        raise ProtocolError(f"{member}: a contrast has at least one cell")
    lengths = {len(v) for _, v in constituents}
    if len(lengths) != 1:
        raise ProtocolError(
            f"{member}: constituent vectors of unequal block length "
            f"{sorted(lengths)}; a paired contrast reads one block set")
    n_blocks = lengths.pop()
    cells: list[dict[str, Any]] = []
    allowance_lower = 0.0
    allowance_upper = 0.0
    half = boundary_halfwidth(n_blocks)
    exact_boundaries: list[str | None] = []
    for constituent, vector in constituents:
        cls = classify_cell(vector, band=band)
        entry = {"cell": constituent.label(configuration),
                 "role": constituent.role, "outcome": constituent.outcome,
                 "companion": constituent.companion,
                 "weight": constituent.weight, **cls}
        exact_boundaries.append(cls["exact_boundary"])
        w = constituent.weight
        if cls["exact_boundary"] == "ceiling":
            # true level in [1 - half, 1]: w*(p - 1) in [-w*half, 0]
            if w > 0:
                allowance_lower += w * half
            else:
                allowance_upper += -w * half
        elif cls["exact_boundary"] == "floor":
            # true level in [0, half]: w*p in [0, w*half]
            if w > 0:
                allowance_upper += w * half
            else:
                allowance_lower += -w * half
        cells.append(entry)
    weighted = [c for c in cells if abs(c["weight"]) > _TOL]
    structural_zero = (bool(weighted)
                       and all(c["exact_boundary"] is not None
                               for c in weighted)
                       and len({c["exact_boundary"] for c in weighted}) == 1)
    any_boundary = any(c["exact_boundary"] is not None for c in weighted)
    levels = [(cst, c["level"]) for cst, c in zip(
        [k for k, _ in constituents], cells)]
    arms = two_arm_levels(levels)
    compression: dict[str, Any] = {"two_arm": arms is not None,
                                   "positive_direction_compressed": False,
                                   "negative_direction_compressed": False,
                                   "compressed_by": []}
    if arms is not None:
        sesoi = C.SMALLEST_EFFECT_OF_INTEREST
        top = C.CONTRAST_COMPRESSION_LEVEL
        lp, ln = arms["positive_arm"], arms["negative_arm"]
        by: list[dict[str, Any]] = []
        if ln > top:
            by.append({"direction": "positive", "arm": "negative_arm",
                       "level": ln,
                       "bound": f"contrast <= 1 - {ln:.4f} = {1 - ln:.4f}"})
        if lp < sesoi:
            by.append({"direction": "positive", "arm": "positive_arm",
                       "level": lp, "bound": f"contrast <= {lp:.4f}"})
        if lp > top:
            by.append({"direction": "negative", "arm": "positive_arm",
                       "level": lp,
                       "bound": f"contrast >= {lp:.4f} - 1 = {lp - 1:.4f}"})
        if ln < sesoi:
            by.append({"direction": "negative", "arm": "negative_arm",
                       "level": ln, "bound": f"contrast >= -{ln:.4f}"})
        compression.update({
            **arms,
            "attainable_given_positive_arm": [lp - 1.0, lp],
            "attainable_given_negative_arm": [-ln, 1.0 - ln],
            "positive_direction_compressed": any(
                e["direction"] == "positive" for e in by),
            "negative_direction_compressed": any(
                e["direction"] == "negative" for e in by),
            "compressed_by": by,
            "sesoi": sesoi, "compression_level": top})
    statuses: list[str] = []
    if structural_zero:
        statuses.append(STRUCTURAL_ZERO)
    if any_boundary:
        statuses.append(ARM_AT_BOUNDARY)
    if compression["positive_direction_compressed"] or \
            compression["negative_direction_compressed"]:
        statuses.append(RANGE_COMPRESSED)
    return {
        "member": member, "configuration": configuration,
        "n_blocks": n_blocks, "constituents": cells,
        "structural_zero": structural_zero,
        "structural_zero_boundary": (weighted[0]["exact_boundary"]
                                     if structural_zero else None),
        "any_arm_at_boundary": any_boundary,
        "boundary_halfwidth": half,
        "allowance_lower": allowance_lower,
        "allowance_upper": allowance_upper,
        "compression": compression,
        "statuses": statuses,
        "terminates": False,
        "rule": "v7 §13.14: recorded, never terminal; the decision interval "
                "is widened by the allowance in the open direction, a "
                "structural zero has no direction and is read on its "
                "allowance interval, and a compressed direction is named "
                "on the statement",
    }


def contrast_boundary_from_table(table: Any, member: str,
                                 configuration: str | None, *,
                                 references: Sequence[str] | None = None,
                                 band: tuple[float, float]
                                 = C.COMPOSED_PROXIMITY_BAND
                                 ) -> dict[str, Any] | None:
    """``contrast_boundary`` read off an ``ObservationTable``.

    ``None`` when the member has no linear composition or when the table
    does not carry a cell the composition needs --- the caller records that
    fact the way it records a member the design did not supply.
    """
    from dci1v7.analysis import estimators

    refs = tuple(references) if references is not None else \
        estimators.reference_slots(table)
    parts = composition(member, references=refs or C.CORE_SLOTS)
    if parts is None:
        return None
    vectors: list[tuple[Constituent, Sequence[float]]] = []
    for part in parts:
        cfg = part.configuration or configuration
        try:
            if part.role == "solo":
                vector = estimators.solo_vector(table, part.outcome)
            else:
                vector = estimators.composed_vector(
                    table, part.outcome, part.companion, cfg)
        except (IntegrityError, ProtocolError):
            # The table lacks a cell the composition needs, or the estimator
            # refuses the table's shape: no reading. Anything else is a defect
            # in this module and propagates rather than becoming "no ceiling".
            return None
        vectors.append((part, vector))
    return contrast_boundary(member, vectors, configuration=configuration,
                             band=band)


def apply_allowance(lower: float, upper: float,
                    boundary: Mapping[str, Any] | None
                    ) -> tuple[float, float]:
    """Widen a decision interval by the boundary allowance, open side only."""
    if not boundary:
        return lower, upper
    return (lower - float(boundary.get("allowance_lower", 0.0)),
            upper + float(boundary.get("allowance_upper", 0.0)))


def projected_confirmatory_halfwidth(
        contrast_by_block: Sequence[float],
        constituents: Sequence[tuple[Constituent, Sequence[float]]], *,
        m_measured: int, m_target: int = C.M_DRAWS,
        t_target: int = C.N_BLOCKS, family_size: int) -> dict[str, Any]:
    """What the confirmatory half-width of this contrast is projected to be.

    Two variance components, separated from what one block set at
    ``m_measured`` draws can say: the between-block variance of the paired
    contrast as measured, and the draw component estimated from each
    constituent's own binomial variance inside a block (bias-corrected by
    ``m/(m-1)``). The topic component is what is left, floored at zero, and
    §16.1's form re-combines them at the registered ``M`` and block count.
    The level is the family's Šidák planning constant, which is what §16.2's
    table is quoted at; the realised verdict reads the bootstrap.

    A projection, labelled as one. It gates nothing: §17.3's precision
    precondition is evaluated on the realised confirmatory interval and
    ``INSUFFICIENT_PRECISION`` is its registered consequence.
    """
    from dci1v7.analysis.bootstrap import sidak_critical

    values = [float(v) for v in contrast_by_block]
    n = len(values)
    if n < 2 or m_measured < 2:
        return {"projected": False,
                "reason": "needs at least two blocks and two draws"}
    s2 = statistics.variance(values)
    correction = m_measured / (m_measured - 1)
    draw_terms = []
    for index in range(n):
        term = 0.0
        for constituent, vector in constituents:
            p = float(vector[index])
            term += constituent.weight ** 2 * p * (1.0 - p) * correction
        draw_terms.append(term)
    s2_draw = sum(draw_terms) / n
    s2_topic = max(0.0, s2 - s2_draw / m_measured)
    variance = (s2_topic + s2_draw / m_target) / t_target
    z = sidak_critical(family_size)
    return {"projected": True, "n_blocks_measured": n,
            "m_measured": m_measured, "m_target": m_target,
            "t_target": t_target, "s2_contrast_measured": s2,
            "s2_draw": s2_draw, "s2_topic": s2_topic,
            "planning_constant": z, "family_size": family_size,
            "half_width": z * math.sqrt(variance),
            "label": "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"}
