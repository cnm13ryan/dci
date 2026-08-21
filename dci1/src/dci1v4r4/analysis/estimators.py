"""The registered contrasts (§11.1-§11.7), each formed inside a block.

Every function here returns **one value per block**, in `table.blocks` order,
and never a scalar. That is what lets the bootstrap resample block indices and
have every quantity of a drawn block travel together (§14.1, §17.1); a function
that averaged internally would silently break the clustering.

**Reference slots are the three core references, never the spectrum rungs.**
`R1-`, `R1+`, ... are spectrum companions: they enter the difficulty relation
of §11.7 and `analysis.spectrum`, and they are not part of `Delta_R`, `Rbar`,
`Xi` or `Delta^A`. Reading them as references would put nine companions into a
contrast §11.3 defines over three, so `reference_slots` filters on exact
membership in `CORE_SLOTS` rather than on a name prefix --- `"R1-".startswith("R")`
is true, and that is precisely the bug the exact test exists to prevent.
"""
from __future__ import annotations

from itertools import permutations
from typing import Callable, Sequence

from dci1v4.errors import ProtocolError

from dci1v4r4.analysis.observations import Observation, ObservationTable
from dci1v4r4.protocol import constants as C

__all__ = ["PRIMARY_SCALE", "solo_vector", "composed_vector", "delivery_loss",
           "asymmetry", "reference_slots", "spectrum_slots", "delta_r",
           "delta_r_uncancelled", "assert_delta_r_forms", "delta_j",
           "delta_a", "d_rbar_from", "d_rbar_rbar", "xi", "delta_class",
           "vacuity_difference", "graded_threshold_scale", "mean_vectors"]

PRIMARY_SCALE = "compliance"


def _value(obs: Observation, scale: str) -> float:
    return float(getattr(obs, scale))


def solo_vector(table: ObservationTable, slot: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    return [_value(table.solo(b, slot), scale) for b in table.blocks]


def composed_vector(table: ObservationTable, outcome: str, companion: str,
                    configuration: str, *, scale: str = PRIMARY_SCALE
                    ) -> list[float]:
    return [_value(table.composed(b, outcome, companion, configuration), scale)
            for b in table.blocks]


def delivery_loss(table: ObservationTable, outcome: str, companion: str,
                  configuration: str, *, scale: str = PRIMARY_SCALE
                  ) -> list[float]:
    """D(c <- g) per block: solo compliance minus composed compliance."""
    solo = solo_vector(table, outcome, scale=scale)
    composed = composed_vector(table, outcome, companion, configuration,
                               scale=scale)
    return [s - c for s, c in zip(solo, composed)]


def mean_vectors(vectors: Sequence[Sequence[float]]) -> list[float]:
    if not vectors:
        raise ProtocolError("no vectors to average")
    length = len(vectors[0])
    if any(len(v) != length for v in vectors):
        raise ProtocolError("vectors of unequal block length")
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(length)]


def asymmetry(table: ObservationTable, configuration: str, *,
              scale: str = PRIMARY_SCALE) -> list[float]:
    """Lambda = D(B <- A) - D(A <- B), within one configuration."""
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    ab = delivery_loss(table, "A", "B", configuration, scale=scale)
    return [x - y for x, y in zip(ba, ab)]


def reference_slots(table: ObservationTable) -> tuple[str, ...]:
    """The admitted CORE references. Exact membership, never a prefix test."""
    core = {s for s in C.CORE_SLOTS if s not in ("A", "B")}
    return tuple(s for s in table.slots() if s in core)


def spectrum_slots(table: ObservationTable) -> tuple[str, ...]:
    """The spectrum rungs, in registered slot order."""
    present = set(table.slots())
    return tuple(s for s in C.SPECTRUM_SLOTS if s in present)


def delta_r(table: ObservationTable, configuration: str, *,
            scale: str = PRIMARY_SCALE) -> list[float]:
    """Delta_R in §11.3's cancelled form: the solo baseline cancels."""
    references = reference_slots(table)
    if len(references) != C.N_CORE_REFERENCES:
        raise ProtocolError(
            f"Delta_R needs {C.N_CORE_REFERENCES} admitted references; the "
            f"table carries {len(references)}. Under EXCESS_NOT_IDENTIFIED it "
            f"is not computed (§13.5)")
    with_refs = mean_vectors([
        composed_vector(table, "B", r, configuration, scale=scale)
        for r in references])
    with_a = composed_vector(table, "B", "A", configuration, scale=scale)
    return [r - a for r, a in zip(with_refs, with_a)]


def delta_r_uncancelled(table: ObservationTable, configuration: str, *,
                        scale: str = PRIMARY_SCALE) -> list[float]:
    """The definitional form: D(B <- A) - mean_j D(B <- R_j)."""
    references = reference_slots(table)
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    brj = mean_vectors([delivery_loss(table, "B", r, configuration,
                                      scale=scale) for r in references])
    return [x - y for x, y in zip(ba, brj)]


def assert_delta_r_forms(table: ObservationTable, configuration: str, *,
                         tolerance: float = 1e-9) -> None:
    """§11.3: the two algebraic forms of Delta_R must agree.

    This is the same guard `analysis.spectrum` puts on delta_difficulty, and
    it is what proves the estimand is a contrast among composed cells alone.
    """
    cancelled = delta_r(table, configuration)
    definitional = delta_r_uncancelled(table, configuration)
    worst = max(abs(a - b) for a, b in zip(cancelled, definitional))
    if worst > tolerance:
        raise ProtocolError(
            f"the cancelled and definitional forms of Delta_R differ by "
            f"{worst:.3e} in {configuration}; the solo baseline must cancel")


def delta_j(table: ObservationTable, reference: str, configuration: str, *,
            scale: str = PRIMARY_SCALE) -> list[float]:
    """Delta_j = D(B <- A) - D(B <- R_j)."""
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    br = delivery_loss(table, "B", reference, configuration, scale=scale)
    return [x - y for x, y in zip(ba, br)]


def delta_a(table: ObservationTable, configuration: str, *,
            scale: str = PRIMARY_SCALE) -> list[float]:
    """Delta^A = D(A <- B) - mean_j D(A <- R_j), a gated diagnostic (§11.5)."""
    references = reference_slots(table)
    ab = delivery_loss(table, "A", "B", configuration, scale=scale)
    arj = mean_vectors([delivery_loss(table, "A", r, configuration,
                                      scale=scale) for r in references])
    return [x - y for x, y in zip(ab, arj)]


def d_rbar_from(table: ObservationTable, companion: str, configuration: str,
                *, scale: str = PRIMARY_SCALE) -> list[float]:
    """§11.5 rule one: D(Rbar <- g) = mean_j D(R_j <- g), g outside the set."""
    references = reference_slots(table)
    if companion in references:
        raise ProtocolError(
            f"D(Rbar <- g) is registered for a companion outside the "
            f"reference set; {companion!r} is a reference (§11.5)")
    return mean_vectors([delivery_loss(table, r, companion, configuration,
                                       scale=scale) for r in references])


def d_rbar_rbar(table: ObservationTable, configuration: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    """§11.5 rule two: the mean over the six ORDERED pairs of references."""
    references = reference_slots(table)
    ordered = list(permutations(references, 2))
    if len(ordered) != 6:
        raise ProtocolError(
            f"expected six ordered reference pairs, got {len(ordered)}")
    return mean_vectors([delivery_loss(table, j, k, configuration, scale=scale)
                         for j, k in ordered])


def xi(table: ObservationTable, configuration: str, *,
       scale: str = PRIMARY_SCALE) -> list[float]:
    """Xi = Delta_R - [D(Rbar <- A) - D(Rbar <- Rbar')]."""
    base = delta_r(table, configuration, scale=scale)
    ra = d_rbar_from(table, "A", configuration, scale=scale)
    rr = d_rbar_rbar(table, configuration, scale=scale)
    return [d - (a - r) for d, a, r in zip(base, ra, rr)]


def delta_class(table: ObservationTable, configuration: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    """§13.7 / F9: Delta_class = D(B <- A) - D(B <- CL).

    The class companion is a production-class control matched to A on the
    difficulty coordinate. It is excluded from the reference set, from Rbar,
    from Xi and from the difficulty fit; this contrast is the only registered
    place it appears.
    """
    if C.CLASS_SLOT not in table.slots():
        raise ProtocolError(
            f"Delta_class needs the {C.CLASS_SLOT} slot; the design in force "
            f"does not carry it")
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    bcl = delivery_loss(table, "B", C.CLASS_SLOT, configuration, scale=scale)
    return [x - y for x, y in zip(ba, bcl)]


def vacuity_difference(table: ObservationTable, companion: str,
                       configuration: str) -> list[float]:
    """F6: the vacuity-rate difference between a composed cell containing B
    and the B solo cell."""
    solo = [table.solo(b, "B").vacuity for b in table.blocks]
    composed = [table.composed(b, "B", companion, configuration).vacuity
                for b in table.blocks]
    return [c - s for c, s in zip(composed, solo)]


def graded_threshold_scale(threshold: float) -> Callable[[Observation], float]:
    """F5's graded recoding at the cell-mean level. Note that the registered
    F5 member reads `graded_threshold`, which is formed at draw level in
    `observations`; this helper exists for §23's sensitivity sweep."""
    def scale(obs: Observation) -> float:
        return 1.0 if obs.graded >= threshold else 0.0
    return scale
