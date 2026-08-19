"""Delivery loss and every registered estimand (§11).

All estimands are block-level and paired within block. Every function here
takes an ``ObservationTable`` and a configuration, reads the same block for
every term of a contrast, and returns a per-block vector; the point estimate is
its mean and the bootstrap resamples the vector. No estimator accepts a draw-
or response-level index (§14.1).

**v4 computes compliance, not failure (T-4).** There is no failure-rate helper
here, and nothing derives an outcome as ``verdicts != n``: delivery loss is on
the compliance scale, and both constituents of a composed cell are scored.

``Delta_R`` is implemented in the cancelled form of §11.3 —
``mean_j E[X_B | B+R_j] - E[X_B | A+B]`` — with ``assert_delta_r_forms``
proving the two algebraic forms agree, because the solo baseline cancels and
the cancelled form is unaffected by solo ceiling or solo noise.

Both §11.5 aggregation rules are asserted in code rather than inferred at the
call site: ``D(Rbar <- g)`` is the mean over the three admitted references of
``D(R_j <- g)``, and ``D(Rbar <- Rbar')`` is the mean over the six *ordered*
pairs of distinct admitted references.
"""
from __future__ import annotations

from itertools import permutations
from typing import Callable, Sequence

from dci1v4.analysis.observations import ObservationTable
from dci1v4.errors import ProtocolError
from dci1v4.protocol import constants as C

#: Which cell-mean field an estimand reads. ``compliance`` is the primary
#: scale; ``non_vacuous_compliance`` is the §17.4 vacuity-forced recoding, in
#: which every vacuous pass becomes a failure.
Scale = str
PRIMARY_SCALE: Scale = "compliance"
VACUITY_FORCED_SCALE: Scale = "non_vacuous_compliance"


def _value(obs, scale: Scale) -> float:
    return float(getattr(obs, scale))


def solo_vector(table: ObservationTable, slot: str, *,
                scale: Scale = PRIMARY_SCALE) -> list[float]:
    return [_value(table.solo(b, slot), scale) for b in table.blocks]


def composed_vector(table: ObservationTable, outcome: str, companion: str,
                    configuration: str, *, scale: Scale = PRIMARY_SCALE
                    ) -> list[float]:
    return [_value(table.composed(b, outcome, companion, configuration), scale)
            for b in table.blocks]


def delivery_loss(table: ObservationTable, outcome: str, companion: str,
                  configuration: str, *, scale: Scale = PRIMARY_SCALE
                  ) -> list[float]:
    """D(c <- g) per block: solo compliance minus composed compliance."""
    solo = solo_vector(table, outcome, scale=scale)
    composed = composed_vector(table, outcome, companion, configuration,
                               scale=scale)
    return [s - c for s, c in zip(solo, composed)]


def _mean_vectors(vectors: Sequence[Sequence[float]]) -> list[float]:
    if not vectors:
        raise ProtocolError("no vectors to average")
    length = len(vectors[0])
    if any(len(v) != length for v in vectors):
        raise ProtocolError("vectors of unequal block length")
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(length)]


def asymmetry(table: ObservationTable, configuration: str, *,
              scale: Scale = PRIMARY_SCALE) -> list[float]:
    """Lambda = D(B <- A) - D(A <- B), within one configuration."""
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    ab = delivery_loss(table, "A", "B", configuration, scale=scale)
    return [x - y for x, y in zip(ba, ab)]


def reference_slots(table: ObservationTable) -> tuple[str, ...]:
    return tuple(s for s in table.slots() if s.startswith("R"))


def delta_r(table: ObservationTable, configuration: str, *,
            scale: Scale = PRIMARY_SCALE) -> list[float]:
    """Delta_R in the §11.3 cancelled form: the solo baseline cancels."""
    references = reference_slots(table)
    if len(references) != C.N_FINAL_REFERENCES:
        raise ProtocolError(
            f"Delta_R needs {C.N_FINAL_REFERENCES} admitted references; the "
            f"table carries {len(references)}. Under EXCESS_NOT_IDENTIFIED it "
            f"is not computed (§13.5)")
    with_refs = _mean_vectors([
        composed_vector(table, "B", r, configuration, scale=scale)
        for r in references])
    with_a = composed_vector(table, "B", "A", configuration, scale=scale)
    return [r - a for r, a in zip(with_refs, with_a)]


def delta_r_uncancelled(table: ObservationTable, configuration: str, *,
                        scale: Scale = PRIMARY_SCALE) -> list[float]:
    """The definitional form: D(B <- A) - mean_j D(B <- R_j)."""
    references = reference_slots(table)
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    brj = _mean_vectors([delivery_loss(table, "B", r, configuration,
                                       scale=scale) for r in references])
    return [x - y for x, y in zip(ba, brj)]


def assert_delta_r_forms(table: ObservationTable, configuration: str, *,
                         tolerance: float = 1e-9) -> None:
    """§11.3: the two algebraic forms of Delta_R must agree."""
    cancelled = delta_r(table, configuration)
    definitional = delta_r_uncancelled(table, configuration)
    worst = max(abs(a - b) for a, b in zip(cancelled, definitional))
    if worst > tolerance:
        raise ProtocolError(
            f"the cancelled and definitional forms of Delta_R differ by "
            f"{worst:.3e} in {configuration}; the solo baseline must cancel")


def delta_j(table: ObservationTable, reference: str, configuration: str, *,
            scale: Scale = PRIMARY_SCALE) -> list[float]:
    """Delta_j = D(B <- A) - D(B <- R_j)."""
    ba = delivery_loss(table, "B", "A", configuration, scale=scale)
    br = delivery_loss(table, "B", reference, configuration, scale=scale)
    return [x - y for x, y in zip(ba, br)]


def delta_a(table: ObservationTable, configuration: str, *,
            scale: Scale = PRIMARY_SCALE) -> list[float]:
    """Delta^A = D(A <- B) - mean_j D(A <- R_j).

    v3's registered pooled swap effect, re-expressed on the compliance scale
    and demoted to a gated diagnostic (§11.5, §32). Its three gates are
    checked by ``analysis.claims``, not here.
    """
    references = reference_slots(table)
    ab = delivery_loss(table, "A", "B", configuration, scale=scale)
    arj = _mean_vectors([delivery_loss(table, "A", r, configuration,
                                       scale=scale) for r in references])
    return [x - y for x, y in zip(ab, arj)]


def d_rbar_from(table: ObservationTable, companion: str, configuration: str,
                *, scale: Scale = PRIMARY_SCALE) -> list[float]:
    """§11.5 rule one: D(Rbar <- g) = mean_j D(R_j <- g), g outside the set."""
    references = reference_slots(table)
    if companion in references:
        raise ProtocolError(
            f"D(Rbar <- g) is registered for a companion outside the "
            f"reference set; {companion!r} is a reference (§11.5)")
    return _mean_vectors([delivery_loss(table, r, companion, configuration,
                                        scale=scale) for r in references])


def d_rbar_rbar(table: ObservationTable, configuration: str, *,
                scale: Scale = PRIMARY_SCALE) -> list[float]:
    """§11.5 rule two: the mean over the six ORDERED pairs of distinct
    admitted references."""
    references = reference_slots(table)
    ordered = list(permutations(references, 2))
    if len(ordered) != 6:
        raise ProtocolError(f"expected six ordered reference pairs, got "
                            f"{len(ordered)}")
    return _mean_vectors([delivery_loss(table, j, k, configuration,
                                        scale=scale) for j, k in ordered])


def xi(table: ObservationTable, configuration: str, *,
       scale: Scale = PRIMARY_SCALE) -> list[float]:
    """Xi = Delta_R - [D(Rbar <- A) - D(Rbar <- Rbar')]."""
    base = delta_r(table, configuration, scale=scale)
    ra = d_rbar_from(table, "A", configuration, scale=scale)
    rr = d_rbar_rbar(table, configuration, scale=scale)
    return [d - (a - r) for d, a, r in zip(base, ra, rr)]


def vacuity_difference(table: ObservationTable, companion: str,
                       configuration: str) -> list[float]:
    """F6: the vacuity-rate difference between a composed cell containing B
    and the B solo cell."""
    solo = [table.solo(b, "B").vacuity for b in table.blocks]
    composed = [table.composed(b, "B", companion, configuration).vacuity
                for b in table.blocks]
    return [c - s for c, s in zip(composed, solo)]


def graded_threshold_scale(threshold: float) -> Callable[[object], float]:
    """F5's graded recoding: a pass requires the graded score at or above the
    registered threshold (0.99)."""
    def scale(obs) -> float:
        return 1.0 if obs.graded >= threshold else 0.0
    return scale


def family_members(table: ObservationTable, configuration: str
                   ) -> dict[str, dict[str, list[float]]]:
    """Every registered family member as a per-block vector (§15).

    F5's graded members are computed from the graded cell mean rather than from
    a recoded indicator, because a cell mean of a thresholded indicator needs
    the draw-level graded score; ``analysis.run`` supplies that variant from the
    rows and passes it in. Here F5 carries the vacuity-forced members, which
    are exactly the primary estimands on the ``non_vacuous_compliance`` scale.
    """
    references = reference_slots(table)
    full = len(references) == C.N_FINAL_REFERENCES
    out: dict[str, dict[str, list[float]]] = {}

    out["F1"] = {
        "D(B<-A)": delivery_loss(table, "B", "A", configuration),
        "D(A<-B)": delivery_loss(table, "A", "B", configuration),
        "Lambda": asymmetry(table, configuration),
    }
    if full:
        out["F1"]["Delta_R"] = delta_r(table, configuration)

    if full:
        out["F2"] = {}
        for index, ref in enumerate(references, start=1):
            out["F2"][f"D(B<-R{index})"] = delivery_loss(
                table, "B", ref, configuration)
            out["F2"][f"Delta_{index}"] = delta_j(table, ref, configuration)
        out["F3"] = {f"D(A<-R{i})": delivery_loss(table, "A", r,
                                                  configuration)
                     for i, r in enumerate(references, start=1)}
        out["F3"]["Delta^A"] = delta_a(table, configuration)
        out["F4"] = {
            "D(Rbar<-A)": d_rbar_from(table, "A", configuration),
            "D(Rbar<-B)": d_rbar_from(table, "B", configuration),
            "D(Rbar<-Rbar')": d_rbar_rbar(table, configuration),
            "Xi": xi(table, configuration),
        }
        out["F7"] = {}
        for index, ref in enumerate(references, start=1):
            out["F7"][f"D(R{index}<-B)"] = delivery_loss(
                table, ref, "B", configuration)
            out["F7"][f"D(R{index}<-A)"] = delivery_loss(
                table, ref, "A", configuration)

    forced = VACUITY_FORCED_SCALE
    out["F5"] = {
        "D(B<-A)|vacuity_forced": delivery_loss(table, "B", "A",
                                                configuration, scale=forced),
        "D(A<-B)|vacuity_forced": delivery_loss(table, "A", "B",
                                                configuration, scale=forced),
        "Lambda|vacuity_forced": asymmetry(table, configuration, scale=forced),
    }
    if full:
        out["F5"]["Delta_R|vacuity_forced"] = delta_r(table, configuration,
                                                      scale=forced)

    out["F6"] = {"vac(B|A+B)-vac(B solo)":
                 vacuity_difference(table, "A", configuration)}
    if full:
        for index, ref in enumerate(references, start=1):
            out["F6"][f"vac(B|B+R{index})-vac(B solo)"] = vacuity_difference(
                table, ref, configuration)
    return out
