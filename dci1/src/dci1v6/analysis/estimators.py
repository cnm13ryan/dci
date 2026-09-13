"""The registered contrasts (§11.1-§11.8), each formed inside a block.

Every function here returns **one value per block**, in ``table.blocks``
order, and never a scalar. That is what lets the bootstrap resample block
identifiers and have every quantity of a drawn block travel together (§14.1,
§17.1); a function that averaged internally would silently break the
clustering.

**Reference slots are the three core references, never anything else.**
``R1-``, ``R1+``, ... are spectrum companions: they enter the difficulty
relation of §11.8 and nothing else. ``N1``, ``N2``, ``N3`` are near-form
controls and ``CL`` is the broad-class control: §13.9 and §13.10 place them
beside B only and keep them out of the core set, the spectrum, the fit,
Delta_R, Rbar and Xi. ``reference_slots`` therefore filters on **exact
membership** in ``CORE_SLOTS`` rather than on a name prefix ---
``"R1-".startswith("R")`` is true, and that is precisely the bug the exact
test exists to prevent --- and ``assert_core_only`` refuses an input that
offers one of the linear arms to a core-set estimand.

**New in v5: the order contrasts.** v4r4 measured a change of Lambda from
-0.110 to +0.315 across configurations on one model, with both
within-configuration intervals excluding zero, and registered **no**
cross-configuration contrast --- so the question could not be answered and
could not be answered afterwards either, because the records store no
bootstrap replicates. Each Ord is a contrast between two composed cells: the
solo baseline cancels, so they are position-clean, baseline-free, and paired
within block because order is a within-block factor. ``assert_order_forms``
computes each in both algebraic forms and refuses a disagreement above 1e-9.
"""
from __future__ import annotations

from itertools import permutations
from typing import Callable, Iterable, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.analysis.observations import Observation, ObservationTable
from dci1v6.protocol import constants as C

__all__ = ["PRIMARY_SCALE", "solo_vector", "composed_vector", "chance_vector",
           "delivery_loss", "asymmetry", "reference_slots", "spectrum_slots",
           "near_form_slots", "assert_core_only", "delta_r",
           "delta_r_uncancelled", "assert_delta_r_forms", "delta_j",
           "delta_a", "d_rbar_from", "d_rbar_rbar", "xi", "delta_near",
           "delta_broad", "vacuity_difference", "graded_threshold_scale",
           "mean_vectors", "counterfactual_chance", "displacement_vector",
           "projected_compliance_vector", "ORDER_CONTRASTS", "ord_a", "ord_b",
           "ord_lambda", "ord_rbar", "ord_cl", "order_contrast",
           "assert_order_forms", "AlgebraicFormError"]

PRIMARY_SCALE = "compliance"


def _value(obs: Observation, scale: str) -> float:
    return float(getattr(obs, scale))


def solo_vector(table: ObservationTable, slot: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    return [_value(table.solo(b, slot), scale) for b in table.blocks]


def chance_vector(table: ObservationTable, slot: str, *,
                  scale: str = PRIMARY_SCALE) -> list[float]:
    """§25: the slot's compliance on the load-zero cell, per block."""
    return [_value(table.chance(b, slot), scale) for b in table.blocks]


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
    core = set(C.CORE_SLOTS)
    return tuple(s for s in table.slots() if s in core)


def spectrum_slots(table: ObservationTable) -> tuple[str, ...]:
    present = set(table.slots())
    return tuple(s for s in C.SPECTRUM_SLOTS if s in present)


def near_form_slots(table: ObservationTable) -> tuple[str, ...]:
    present = set(table.slots())
    return tuple(s for s in C.NEAR_FORM_SLOTS if s in present)


def assert_core_only(slots: Iterable[str], *, where: str) -> None:
    """§13.9 and §13.10: a linear-arm companion never enters a core estimand.

    Delta_R, Rbar, Xi and the §11.8 fit are defined over the three core
    references. Admitting a near-form control or the broad-class companion
    would let the quantity the arm exists to expose be absorbed by the
    quantity it is meant to be compared against.
    """
    stray = sorted(s for s in slots
                   if s in C.NEAR_FORM_SLOTS + (C.CLASS_SLOT,)
                   + C.SPECTRUM_SLOTS)
    if stray:
        raise ProtocolError(
            f"{where}: {stray} belong to the spectrum, near-form or "
            "broad-class arm. §13.9 and §13.10 place them beside B only and "
            "keep them out of the core set, the spectrum fit, Delta_R, Rbar "
            "and Xi")


def delta_r(table: ObservationTable, configuration: str, *,
            scale: str = PRIMARY_SCALE) -> list[float]:
    """Delta_R in §11.3's cancelled form: the solo baseline cancels."""
    references = reference_slots(table)
    assert_core_only(references, where="Delta_R")
    if len(references) != C.N_CORE_REFERENCES:
        raise ProtocolError(
            f"Delta_R needs {C.N_CORE_REFERENCES} admitted references; the "
            f"table carries {len(references)}. Under "
            "REFERENCE_SUPPORT_NOT_IDENTIFIED it is not computed (§13.15)")
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


class AlgebraicFormError(ProtocolError):
    """The two algebraic forms of a registered estimand disagree.

    Its own type because §11.3, §11.7 and §11.8's checks can also be *not
    applicable* --- a missing cell, a degenerate fit --- and a caller that
    records "not available" must not be able to record a disagreement as one.
    """


def _assert_forms(a: Sequence[float], b: Sequence[float], *, name: str,
                  configuration: str,
                  tolerance: float = C.ALGEBRAIC_FORM_TOLERANCE) -> float:
    worst = max(abs(x - y) for x, y in zip(a, b))
    if worst > tolerance:
        raise AlgebraicFormError(
            f"the two algebraic forms of {name} differ by {worst:.3e} in "
            f"{configuration}; the solo baseline must cancel exactly")
    return worst


def assert_delta_r_forms(table: ObservationTable, configuration: str, *,
                         tolerance: float = C.ALGEBRAIC_FORM_TOLERANCE
                         ) -> float:
    """§11.3: the two algebraic forms of Delta_R must agree."""
    return _assert_forms(delta_r(table, configuration),
                         delta_r_uncancelled(table, configuration),
                         name="Delta_R", configuration=configuration,
                         tolerance=tolerance)


def delta_j(table: ObservationTable, reference: str, configuration: str, *,
            scale: str = PRIMARY_SCALE) -> list[float]:
    """Delta_j = D(B <- A) - D(B <- R_j)."""
    assert_core_only([reference], where="Delta_j")
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
    """§11.6: D(Rbar <- g) = mean_j D(R_j <- g), g outside the set."""
    references = reference_slots(table)
    if companion in references:
        raise ProtocolError(
            "D(Rbar <- g) is registered for a companion outside the "
            f"reference set; {companion!r} is a reference (§11.6)")
    return mean_vectors([delivery_loss(table, r, companion, configuration,
                                       scale=scale) for r in references])


def d_rbar_rbar(table: ObservationTable, configuration: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    """§11.6: the mean over the six ORDERED pairs of distinct references."""
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


def delta_near(table: ObservationTable, configuration: str, *,
               scale: str = PRIMARY_SCALE) -> list[float]:
    """§11.5 / F9: Delta_near = D(B <- A) - mean_k D(B <- N_k).

    The three near-form controls are Tier-2 companions sharing A's operator
    but not its statistic. Delta_near is the second half of the answer to
    H_form and it is what §17.6's ``LOCAL_TIER_DISAGREE`` reads: a
    Delta_R ~ 0 with Delta_near > 0.10 is **not** emitted as L3c but as a
    registered disagreement, which is the mitigation the red team's R1 asks
    for and the reason §34 D1's option of dropping this arm is not free.
    """
    controls = near_form_slots(table)
    if len(controls) != C.N_NEAR_FORM_CONTROLS:
        raise ProtocolError(
            f"Delta_near needs {C.N_NEAR_FORM_CONTROLS} near-form controls; "
            f"the table carries {len(controls)}. Under "
            "NEAR_FORM_ARM_NOT_AVAILABLE it is not computed (§13.9)")
    with_n = mean_vectors([
        composed_vector(table, "B", n, configuration, scale=scale)
        for n in controls])
    with_a = composed_vector(table, "B", "A", configuration, scale=scale)
    return [n - a for n, a in zip(with_n, with_a)]


def delta_broad(table: ObservationTable, configuration: str, *,
                scale: str = PRIMARY_SCALE) -> list[float]:
    """§11.5 / F10: Delta_broad = D(B <- A) - D(B <- CL).

    One Tier-3 budget-class companion. **One companion cannot separate
    "budget constraints interfere differently" from "this particular budget
    constraint interferes differently"**, so §5 registers this as a bound on
    how much class could matter and never as an estimate of a class effect.
    """
    if C.CLASS_SLOT not in table.slots():
        raise ProtocolError(
            f"Delta_broad needs the {C.CLASS_SLOT} slot; the admitted arm set "
            "does not carry it (CLASS_ARM_NOT_AVAILABLE)")
    with_cl = composed_vector(table, "B", C.CLASS_SLOT, configuration,
                              scale=scale)
    with_a = composed_vector(table, "B", "A", configuration, scale=scale)
    return [c - a for c, a in zip(with_cl, with_a)]


# --------------------------------------------------------- §11.2 chance terms
def counterfactual_chance(table: ObservationTable, slot: str, *,
                          scale: str = PRIMARY_SCALE) -> list[float]:
    """kappa(c|B) per block: c's verdict on the **B-solo** cell, c absent.

    §9.1's presence rule makes this readable from rows the design already
    generates, which is what makes §13.6 cost zero extra generations. It reads
    no composed cell and observes B's compliance nowhere; §13.6 registers its
    only use as an admission quantity, and §23's projection audit is where the
    confirmatory value is reported against the realised composed rate.

    ``slot`` must be a companion, never ``B`` itself: B is *present* on its
    own solo cell, so ``kappa(B|B)`` is not a chance quantity and asking for
    it is a category error rather than a missing value.
    """
    if slot == "B":
        raise ProtocolError(
            "kappa(c|B) is a chance verdict on a constraint the B-solo cell "
            "did not state; B is present there, so kappa(B|B) is not defined")
    return [_value(table.kappa_under_b(b, slot), scale)
            for b in table.blocks]


def displacement_vector(chance: Sequence[float],
                        chance_under_b: Sequence[float]) -> list[float]:
    """Sigma_c = kappa(c|B) - kappa(c), per block."""
    return [b - k for k, b in zip(chance, chance_under_b)]


def projected_compliance_vector(chance_under_b: Sequence[float],
                                iota: Sequence[float]) -> list[float]:
    """p_hat_c = kappa(c|B) + iota_c (1 - kappa(c|B)), per block."""
    return [kb + i * (1.0 - kb) for kb, i in zip(chance_under_b, iota)]


# ------------------------------------------------- §11.7 the order contrasts
#: F11's five members, in registered order.
ORDER_CONTRASTS = C.FAMILY_MEMBERS["F11"]


def _ord_from_composed(table: ObservationTable, outcome: str, companion: str,
                       *, scale: str) -> list[float]:
    """The cancelled form: composed(outcome second) - composed(outcome first).

    ``D(c <- g)|first - D(c <- g)|second`` has the solo term in both
    positions, so it cancels and what remains is the difference of the two
    composed cells with the outcome in the two positions.
    """
    first = composed_vector(table, outcome, companion, C.OUTCOME_FIRST,
                            scale=scale)
    second = composed_vector(table, outcome, companion, C.OUTCOME_SECOND,
                             scale=scale)
    return [s - f for f, s in zip(first, second)]


def _ord_definitional(table: ObservationTable, outcome: str, companion: str,
                      *, scale: str) -> list[float]:
    """The definitional form: D|first - D|second."""
    first = delivery_loss(table, outcome, companion, C.OUTCOME_FIRST,
                          scale=scale)
    second = delivery_loss(table, outcome, companion, C.OUTCOME_SECOND,
                           scale=scale)
    return [f - s for f, s in zip(first, second)]


def ord_a(table: ObservationTable, *, scale: str = PRIMARY_SCALE
          ) -> list[float]:
    """Ord_A = D(A <- B)|first - D(A <- B)|second."""
    return _ord_from_composed(table, "A", "B", scale=scale)


def ord_b(table: ObservationTable, *, scale: str = PRIMARY_SCALE
          ) -> list[float]:
    """Ord_B = D(B <- A)|first - D(B <- A)|second."""
    return _ord_from_composed(table, "B", "A", scale=scale)


def ord_lambda(table: ObservationTable, *, scale: str = PRIMARY_SCALE
               ) -> list[float]:
    """Ord_Lambda = Lambda|first - Lambda|second = Ord_B - Ord_A.

    **Linearly dependent on Ord_A and Ord_B, and registered anyway.** It is
    the asymmetry's own order dependence and is the quantity a reader of
    v4r4's sign reversal wants; §11.7 declares the dependence rather than
    hiding it, and F11's simultaneous interval accounts for its members as
    declared without pretending they are independent.
    """
    a = ord_a(table, scale=scale)
    b = ord_b(table, scale=scale)
    return [x - y for x, y in zip(b, a)]


def ord_rbar(table: ObservationTable, *, scale: str = PRIMARY_SCALE
             ) -> list[float]:
    """Ord_Rbar = mean_j [ D(B <- R_j)|first - D(B <- R_j)|second ]."""
    references = reference_slots(table)
    assert_core_only(references, where="Ord_Rbar")
    if len(references) != C.N_CORE_REFERENCES:
        raise ProtocolError(
            f"Ord_Rbar needs {C.N_CORE_REFERENCES} admitted references; the "
            f"table carries {len(references)}")
    return mean_vectors([_ord_from_composed(table, "B", r, scale=scale)
                         for r in references])


def ord_cl(table: ObservationTable, *, scale: str = PRIMARY_SCALE
           ) -> list[float]:
    """Ord_CL = D(B <- CL)|first - D(B <- CL)|second."""
    if C.CLASS_SLOT not in table.slots():
        raise ProtocolError(
            f"Ord_CL needs the {C.CLASS_SLOT} slot; the admitted arm set does "
            "not carry it (CLASS_ARM_NOT_AVAILABLE)")
    return _ord_from_composed(table, "B", C.CLASS_SLOT, scale=scale)


def order_contrast(table: ObservationTable, member: str, *,
                   scale: str = PRIMARY_SCALE) -> list[float]:
    """One F11 member by name. Refuses a name F11 does not register."""
    builders = {"Ord_A": ord_a, "Ord_B": ord_b, "Ord_Lambda": ord_lambda,
                "Ord_Rbar": ord_rbar, "Ord_CL": ord_cl}
    if member not in ORDER_CONTRASTS:
        raise ProtocolError(
            f"{member!r} is not a registered F11 member; F11 is "
            f"{list(ORDER_CONTRASTS)}. §17.5's emitter refuses an "
            "unregistered order comparison and so does this")
    return builders[member](table, scale=scale)


def assert_order_forms(table: ObservationTable, *,
                       tolerance: float = C.ALGEBRAIC_FORM_TOLERANCE
                       ) -> dict[str, float]:
    """§11.7: every order contrast agrees in both algebraic forms.

    ``Ord_Lambda`` is checked against ``Ord_B - Ord_A`` as well as against the
    difference of the two within-configuration Lambdas, because its linear
    dependence is registered and an implementation that broke it would be
    computing a different quantity under a registered name.
    """
    worst: dict[str, float] = {}
    for outcome, companion, name in (("A", "B", "Ord_A"),
                                     ("B", "A", "Ord_B")):
        worst[name] = _assert_forms(
            _ord_from_composed(table, outcome, companion, scale=PRIMARY_SCALE),
            _ord_definitional(table, outcome, companion, scale=PRIMARY_SCALE),
            name=name, configuration="cross-configuration",
            tolerance=tolerance)
    lam = [x - y for x, y in zip(asymmetry(table, C.OUTCOME_FIRST),
                                 asymmetry(table, C.OUTCOME_SECOND))]
    worst["Ord_Lambda"] = _assert_forms(
        ord_lambda(table), lam, name="Ord_Lambda",
        configuration="cross-configuration", tolerance=tolerance)
    if C.CORE_SLOTS[0] in table.slots():
        references = reference_slots(table)
        if len(references) == C.N_CORE_REFERENCES:
            worst["Ord_Rbar"] = _assert_forms(
                ord_rbar(table),
                mean_vectors([_ord_definitional(table, "B", r,
                                                scale=PRIMARY_SCALE)
                              for r in references]),
                name="Ord_Rbar", configuration="cross-configuration",
                tolerance=tolerance)
    if C.CLASS_SLOT in table.slots():
        worst["Ord_CL"] = _assert_forms(
            ord_cl(table),
            _ord_definitional(table, "B", C.CLASS_SLOT, scale=PRIMARY_SCALE),
            name="Ord_CL", configuration="cross-configuration",
            tolerance=tolerance)
    return worst


def vacuity_difference(table: ObservationTable, companion: str,
                       configuration: str) -> list[float]:
    """F6: the vacuity-rate difference between a composed cell containing B
    and the B solo cell."""
    solo = [table.solo(b, "B").vacuity for b in table.blocks]
    composed = [table.composed(b, "B", companion, configuration).vacuity
                for b in table.blocks]
    return [c - s for c, s in zip(composed, solo)]


def graded_threshold_scale(threshold: float) -> Callable[[Observation], float]:
    """§23's sensitivity sweep at the cell-mean level. The registered F5
    member reads ``graded_threshold``, formed at draw level in
    ``observations``."""
    def scale(obs: Observation) -> float:
        return 1.0 if obs.graded >= threshold else 0.0
    return scale
