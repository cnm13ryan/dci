"""The difficulty-response relation and delta_difficulty (§11.7, §13.8, §17.2).

The estimand is

    delta_difficulty = D(B <- A) - [alpha_bar + beta * iota_A]

where ``alpha_f + beta * d`` is fitted by ordinary least squares on the **nine
non-A companions** -- three families, three severities each -- and
``alpha_bar`` is the mean of the three family intercepts, because A belongs to
no family.

Three properties are enforced here rather than described:

**A is excluded from the fit that predicts A.** ``fit_difficulty_relation``
raises if handed a point labelled ``A``. Predicting a point from a fit
containing that point is circular, and the bias is not small when the point
carries leverage: correcting exactly this defect in a design screen moved the
difficulty residuals from +0.055/+0.098 to +0.067/+0.118 and the length
residuals from within +/-0.010 to -0.117/+0.126. The circularity shrinks the
residual toward zero, so registering the exclusion protects against a false
negative.

**The class companion is excluded too.** It is a production-class constraint
and A's excess over its own class is the quantity the class arm exists to
expose; letting the line absorb it would hide it.

**The solo baseline cancels.** The prediction weights sum to one, so
delta_difficulty is a contrast among composed cells alone, exactly as Delta_R
is. ``assert_algebraic_forms_agree`` computes it both ways and refuses a
disagreement above 1e-9, which is the same guard v4r2 put on Delta_R.

Support (§13.8) is evaluated in every bootstrap replicate, not once: a line
fitted on companions that all sit on one side of A does not predict A, it
extrapolates to A, and the residual it produces is an artefact of the slope.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.protocol import open_items
from dci1v5.stages.calibration_table import (
    instructed_compliance, tie_key,
)

__all__ = ["SpectrumPoint", "DifficultyFit", "fit_difficulty_relation",
           "prediction_weights", "support_verdict", "SpectrumInput",
           "estimate", "assert_algebraic_forms_agree", "bootstrap_spectrum",
           "TierInput", "tier_estimate", "FitNotAvailable",
           "TierFit", "fit_with_tier_indicator", "adopted_formulation",
           "assert_adopted_formulation"]


class FitNotAvailable(ProtocolError):
    """There is no fit to compare forms on --- not a disagreement.

    §11.8's both-forms check applies to a fit that exists. A degenerate one is
    a different fact and is recorded as one; conflating them would let a
    caller that tolerates absence tolerate a disagreement too.
    """


@dataclass(frozen=True)
class SpectrumPoint:
    """One companion's contribution to the fit."""

    slot: str          # "R1", "R1-", "R1+", ...  never "A", never "CL"
    family: str
    difficulty: float  # d = iota, the registered coordinate (§13.3)
    loss: float        # Y = D(B <- companion)


@dataclass(frozen=True)
class DifficultyFit:
    """The fitted relation and everything needed to audit it."""

    slope: float
    intercepts: dict[str, float]
    intercept_mean: float
    n_points: int
    n_families: int
    residuals: dict[str, float]
    #: The weight this fit puts on each point when predicting at a given
    #: difficulty. Recorded because it is what makes the estimand a contrast
    #: of composed cells (see ``assert_algebraic_forms_agree``).
    weights_at: dict[str, float]
    predicted_at: float
    difficulty_at: float

    @property
    def sum_weights(self) -> float:
        return sum(self.weights_at.values())

    @property
    def sum_weights_squared(self) -> float:
        return sum(w * w for w in self.weights_at.values())


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def fit_difficulty_relation(points: Sequence[SpectrumPoint], *,
                            predict_at: float) -> DifficultyFit:
    """§11.7's registered form: ``Y = alpha_f + beta*d``, OLS, equal weights.

    Family-aware intercepts are registered rather than a single intercept
    because family is the one companion property the design deliberately
    varies at fixed difficulty, and v4r2 §13.4 recorded D(B<-R_j) varying by
    0.177 and 0.188 at essentially constant companion compliance. A single
    intercept would push that variation into the residual and into
    delta_difficulty.
    """
    if any(p.slot == "A" for p in points):
        raise ProtocolError(
            "§11.7: A must not enter the fit that predicts A. Including it "
            "fits the line through the point it is then used to predict, "
            "which shrinks A's residual toward zero by construction.")
    if any(p.slot == C.CLASS_SLOT for p in points):
        raise ProtocolError(
            "§13.10: the broad-class companion must not enter the difficulty "
            "fit. The line would absorb the class effect the arm exists to "
            "expose.")
    stray = sorted(p.slot for p in points if p.slot in C.NEAR_FORM_SLOTS)
    if stray:
        raise ProtocolError(
            f"§13.9: the near-form controls {stray} contribute NO point to "
            "the primary difficulty fit. They enter the secondary "
            "tier-indicator fit of §11.8 and nothing else.")
    if len(points) < 3:
        raise ProtocolError(f"the fit needs at least three points; got "
                            f"{len(points)}")
    if len({p.slot for p in points}) != len(points):
        raise ProtocolError("a slot appears twice in the fit input")

    by_family: dict[str, list[SpectrumPoint]] = {}
    for p in points:
        by_family.setdefault(p.family, []).append(p)

    d_bar = {f: _mean([p.difficulty for p in ps])
             for f, ps in by_family.items()}
    y_bar = {f: _mean([p.loss for p in ps]) for f, ps in by_family.items()}

    sdd = sum((p.difficulty - d_bar[p.family]) ** 2 for p in points)
    if sdd <= 0:
        raise ProtocolError(
            "the within-family difficulty spread is zero: the slope is not "
            "identified and §17.2 records a degenerate replicate")
    slope = sum((p.difficulty - d_bar[p.family]) * (p.loss - y_bar[p.family])
                for p in points) / sdd
    intercepts = {f: y_bar[f] - slope * d_bar[f] for f in by_family}
    intercept_mean = _mean(list(intercepts.values()))
    predicted = intercept_mean + slope * predict_at

    n_families = len(by_family)
    grand_d_bar = _mean(list(d_bar.values()))
    weights = {}
    for p in points:
        n_f = len(by_family[p.family])
        c = (p.difficulty - d_bar[p.family]) / sdd
        weights[p.slot] = 1.0 / (n_families * n_f) + c * (predict_at
                                                          - grand_d_bar)
    residuals = {p.slot: p.loss - (intercepts[p.family]
                                   + slope * p.difficulty) for p in points}
    return DifficultyFit(
        slope=slope, intercepts=intercepts, intercept_mean=intercept_mean,
        n_points=len(points), n_families=n_families, residuals=residuals,
        weights_at=weights, predicted_at=predicted, difficulty_at=predict_at)


def prediction_weights(fit: DifficultyFit) -> dict[str, float]:
    return dict(fit.weights_at)


def support_verdict(points: Sequence[SpectrumPoint], *, difficulty_a: float,
                    dropped: Sequence[str] = ()) -> dict[str, object]:
    """§13.8. Five conditions, all of them about the realised spread.

    Conditions 2 to 4 are floors below §13.6's construction, which delivers
    three points per side spread over three families; they tolerate one
    family's rung moving across A between calibration and confirmation
    without voiding the estimand.
    """
    xs = [p.difficulty for p in points]
    below = [p for p in points if tie_key(p.difficulty) < tie_key(difficulty_a)]
    above = [p for p in points if tie_key(p.difficulty) > tie_key(difficulty_a)]
    families_below = {p.family for p in below}
    families_above = {p.family for p in above}
    reasons: list[str] = []
    if not (min(xs) <= difficulty_a <= max(xs)):
        reasons.append(
            f"A's difficulty {difficulty_a:.3f} lies outside the fitted range "
            f"[{min(xs):.3f}, {max(xs):.3f}]: the line extrapolates to A")
    if len(below) < C.SUPPORT_MIN_BELOW:
        reasons.append(f"only {len(below)} companions below A; "
                       f"{C.SUPPORT_MIN_BELOW} required")
    if len(above) < C.SUPPORT_MIN_ABOVE:
        reasons.append(f"only {len(above)} companions above A; "
                       f"{C.SUPPORT_MIN_ABOVE} required")
    if len(families_below) < C.SUPPORT_MIN_FAMILIES_PER_SIDE:
        reasons.append(f"only {len(families_below)} families below A; "
                       f"{C.SUPPORT_MIN_FAMILIES_PER_SIDE} required")
    if len(families_above) < C.SUPPORT_MIN_FAMILIES_PER_SIDE:
        reasons.append(f"only {len(families_above)} families above A; "
                       f"{C.SUPPORT_MIN_FAMILIES_PER_SIDE} required")
    if dropped:
        reasons.append(f"points dropped under §11.2's degeneracy rule: "
                       f"{sorted(dropped)}")
    return {
        "holds": not reasons, "reasons": reasons,
        "difficulty_a": difficulty_a,
        "fitted_range": [min(xs), max(xs)],
        "n_below": len(below), "n_above": len(above),
        "families_below": sorted(families_below),
        "families_above": sorted(families_above),
        "reading": ("A's difficulty is inside the fitted support and "
                    "delta_difficulty is identified from these points"
                    if not reasons else
                    "DIFFICULTY_SUPPORT_NOT_IDENTIFIED: the fit does not "
                    "predict A, it extrapolates to A. The point estimate is "
                    "descriptive and is not a measurement, and it is not a "
                    "null."),
    }


@dataclass(frozen=True)
class SpectrumInput:
    """Per-block cell means, the only thing the estimator ever sees.

    Every mapping is keyed by slot and every value is one float per block, in
    a fixed block order. The bootstrap resamples block *indices*, so every
    quantity of a drawn block travels together (§14.1).
    """

    blocks: tuple[str, ...]
    family_of: Mapping[str, str]        # slot -> family, spectrum + core
    b_solo: Sequence[float]
    b_with: Mapping[str, Sequence[float]]        # slot -> p(B | B + slot)
    companion_solo: Mapping[str, Sequence[float]]
    companion_chance: Mapping[str, Sequence[float]]
    a_solo: Sequence[float]
    a_chance: Sequence[float]

    def __post_init__(self):
        n = len(self.blocks)
        for name, mapping in (("b_with", self.b_with),
                              ("companion_solo", self.companion_solo),
                              ("companion_chance", self.companion_chance)):
            for slot, values in mapping.items():
                if len(values) != n:
                    raise ProtocolError(
                        f"{name}[{slot}] has {len(values)} blocks, not {n}")
        if "A" not in self.b_with:
            raise ProtocolError("the estimator needs p(B | A+B) to form "
                                "delta_difficulty")
        for slot in self.family_of:
            if slot in ("A", C.CLASS_SLOT):
                raise ProtocolError(
                    f"{slot} must not be given a family: it is excluded from "
                    "the fit by §11.7 and §13.7")


def _resampled(values: Sequence[float], picks: Sequence[int]) -> float:
    return sum(values[i] for i in picks) / len(picks)


def estimate(data: SpectrumInput, picks: Sequence[int] | None = None
             ) -> dict[str, object]:
    """One estimate of the whole spectrum block, on one (re)sample of blocks.

    ``picks`` is a list of block indices with replacement; ``None`` means the
    observed sample. Everything is recomputed from ``picks``: the chance
    rates, the difficulties, the losses, the fit, the prediction and the
    support verdict. §17.2 forbids doing any of it once and reusing it.
    """
    if picks is None:
        picks = list(range(len(data.blocks)))
    if not picks:
        raise ProtocolError("an empty resample")

    b_solo = _resampled(data.b_solo, picks)
    a_solo = _resampled(data.a_solo, picks)
    a_chance = _resampled(data.a_chance, picks)
    d_a = instructed_compliance(a_solo, a_chance)

    points: list[SpectrumPoint] = []
    dropped: list[str] = []
    for slot, family in sorted(data.family_of.items()):
        chance = _resampled(data.companion_chance[slot], picks)
        if chance >= C.CHANCE_DEGENERACY_MAX:
            dropped.append(slot)
            continue
        solo = _resampled(data.companion_solo[slot], picks)
        loss = b_solo - _resampled(data.b_with[slot], picks)
        points.append(SpectrumPoint(slot=slot, family=family,
                                    difficulty=instructed_compliance(solo,
                                                                     chance),
                                    loss=loss))

    d_b_from_a = b_solo - _resampled(data.b_with["A"], picks)
    support = support_verdict(points, difficulty_a=d_a, dropped=dropped)

    try:
        fit = fit_difficulty_relation(points, predict_at=d_a)
    except ProtocolError as exc:
        return {"degenerate": True, "reason": str(exc),
                "D_B_from_A": d_b_from_a, "difficulty_a": d_a,
                "support": support, "delta_difficulty": float("nan")}

    delta = d_b_from_a - fit.predicted_at
    return {
        "degenerate": False,
        "D_B_from_A": d_b_from_a,
        "difficulty_a": d_a,
        "slope": fit.slope,
        "intercepts": fit.intercepts,
        "predicted_at_A": fit.predicted_at,
        "delta_difficulty": delta,
        "residuals": fit.residuals,
        "weights": fit.weights_at,
        "sum_weights": fit.sum_weights,
        "sum_weights_squared": fit.sum_weights_squared,
        "support": support,
        "dropped_points": dropped,
        "fit": fit,
    }


@dataclass(frozen=True)
class TierInput:
    """§11.8's twelve points: the nine the primary fit uses, plus the three
    near-form controls that sit at a different structural tier.

    Held apart from ``SpectrumInput`` because the primary fit must not see
    them --- §11.7 registers it over three families of three severities --- and
    because the secondary is reportable only when the near-form arm exists.
    """

    base: SpectrumInput
    near_family_of: Mapping[str, str]           # near-form slot -> family
    near_solo: Mapping[str, Sequence[float]]
    near_chance: Mapping[str, Sequence[float]]
    b_with_near: Mapping[str, Sequence[float]]
    tiers: Mapping[str, int]                    # slot -> structural tier


def tier_estimate(data: TierInput, picks: Sequence[int] | None = None
                  ) -> dict[str, object]:
    """§11.8's secondary fit on one (re)sample, under U2's adopted reading.

    Returns ``beta``, ``gamma`` and the three core-family intercepts --- the
    five F8 members §15 registers from this fit --- or a named degeneracy.
    Everything is recomputed from ``picks``, exactly as ``estimate`` is:
    §17.2 forbids fitting once and reusing it across replicates.

    ``assert_adopted_formulation`` runs on every returned fit, so a
    non-adopted construction cannot reach an F8 row.
    """
    base = data.base
    if picks is None:
        picks = list(range(len(base.blocks)))
    if not picks:
        raise ProtocolError("an empty resample")
    b_solo = _resampled(base.b_solo, picks)
    points: list[SpectrumPoint] = []
    dropped: list[str] = []
    for slot, family in sorted(base.family_of.items()):
        chance = _resampled(base.companion_chance[slot], picks)
        if chance >= C.CHANCE_DEGENERACY_MAX:
            dropped.append(slot)
            continue
        solo = _resampled(base.companion_solo[slot], picks)
        points.append(SpectrumPoint(
            slot=slot, family=family,
            difficulty=instructed_compliance(solo, chance),
            loss=b_solo - _resampled(base.b_with[slot], picks)))
    for slot, family in sorted(data.near_family_of.items()):
        chance = _resampled(data.near_chance[slot], picks)
        if chance >= C.CHANCE_DEGENERACY_MAX:
            dropped.append(slot)
            continue
        solo = _resampled(data.near_solo[slot], picks)
        points.append(SpectrumPoint(
            slot=slot, family=family,
            difficulty=instructed_compliance(solo, chance),
            loss=b_solo - _resampled(data.b_with_near[slot], picks)))
    try:
        fit = assert_adopted_formulation(
            fit_with_tier_indicator(points, data.tiers),
            where="analysis.spectrum.tier_estimate")
    except ProtocolError as exc:
        return {"degenerate": True, "reason": str(exc),
                "dropped_points": dropped, "n_points": len(points)}
    return {"degenerate": False, "beta": fit.slope, "gamma": fit.gamma,
            "intercepts": dict(fit.intercepts), "n_points": fit.n_points,
            "residuals": dict(fit.residuals), "formulation": fit.formulation,
            "adopted": fit.adopted, "dropped_points": dropped}


def assert_algebraic_forms_agree(data: SpectrumInput,
                                 picks: Sequence[int] | None = None, *,
                                 tolerance: float = 1e-9) -> float:
    """§11.7: the definitional and the cancelled forms must agree.

    Definitional: ``D(B<-A) - [alpha_bar + beta*iota_A]``.
    Cancelled:    ``sum_w p(B | B+R_fs) - p(B | A+B)``.

    They agree exactly because the prediction weights sum to one, so the
    B-solo baseline cancels. Computing both and refusing a disagreement is
    the same guard v4r2 put on Delta_R, and it is what proves the estimand is
    a contrast among composed cells rather than something that inherits the
    solo cell's noise.
    """
    result = estimate(data, picks)
    if result["degenerate"]:
        raise FitNotAvailable(f"cannot compare forms on a degenerate fit: "
                              f"{result['reason']}")
    if picks is None:
        picks = list(range(len(data.blocks)))
    weights = result["weights"]
    if abs(sum(weights.values()) - 1.0) > tolerance:
        raise ProtocolError(
            f"the prediction weights sum to {sum(weights.values())!r}, not 1: "
            "the B-solo baseline does not cancel and the estimand is not the "
            "registered one")
    cancelled = (sum(w * _resampled(data.b_with[slot], picks)
                     for slot, w in weights.items())
                 - _resampled(data.b_with["A"], picks))
    definitional = result["delta_difficulty"]
    if abs(cancelled - definitional) > tolerance:
        raise ProtocolError(
            f"the cancelled and definitional forms of delta_difficulty differ "
            f"by {abs(cancelled - definitional):.3e}")
    return definitional


def bootstrap_spectrum(data: SpectrumInput, *, resamples: int, seed: int,
                       rng_factory=None) -> dict[str, object]:
    """§17.2: every replicate resamples blocks and **refits**.

    Prohibited, and none of it is reachable from here: fitting once and
    bootstrapping the residual (the fit is inside the loop); including A (the
    fitter refuses); selecting the form from bootstrap outcomes (the form is
    a constant); treating spectrum points sharing topic blocks as independent
    (one index vector moves every cell of a block together); resampling
    anything but blocks (``picks`` indexes ``data.blocks``).
    """
    import random

    rng = (rng_factory or random.Random)(seed)
    n = len(data.blocks)
    point = estimate(data)
    draws: list[float] = []
    slopes: list[float] = []
    support_held = 0
    degenerate = 0
    for _ in range(resamples):
        picks = [rng.randrange(n) for _ in range(n)]
        replicate = estimate(data, picks)
        if replicate["degenerate"]:
            degenerate += 1
            continue
        draws.append(float(replicate["delta_difficulty"]))
        slopes.append(float(replicate["slope"]))
        if replicate["support"]["holds"]:
            support_held += 1
    if not draws:
        raise ProtocolError("every bootstrap replicate was degenerate")

    ordered = sorted(draws)
    lo = ordered[max(0, int(math.floor(0.025 * len(ordered))) - 1)]
    hi = ordered[min(len(ordered) - 1,
                     int(math.ceil(0.975 * len(ordered))) - 1)]
    mean = _mean(draws)
    se = math.sqrt(sum((d - mean) ** 2 for d in draws) / (len(draws) - 1))
    share = support_held / resamples
    statuses: list[str] = []
    if not point["degenerate"] and not point["support"]["holds"]:
        statuses.append("DIFFICULTY_SUPPORT_NOT_IDENTIFIED")
    elif share < C.SUPPORT_BOOTSTRAP_SHARE_MIN:
        statuses.append("DIFFICULTY_SUPPORT_MARGINAL")
    if degenerate / resamples > C.DEGENERATE_REPLICATE_MAX:
        statuses.append("INSUFFICIENT_PRECISION")
    return {
        "estimate": point["delta_difficulty"],
        "bootstrap_se": se,
        "ci95_percentile": [lo, hi],
        "slope_estimate": point["slope"],
        "slope_ci95_percentile": [
            sorted(slopes)[max(0, int(math.floor(0.025 * len(slopes))) - 1)],
            sorted(slopes)[min(len(slopes) - 1,
                               int(math.ceil(0.975 * len(slopes))) - 1)]],
        "support": point["support"],
        "support_bootstrap_share": share,
        "degenerate_replicate_share": degenerate / resamples,
        "resamples": resamples,
        "refit_per_replicate": True,
        "identification_statuses": statuses,
    }


# ------------------------------------------- §11.8's secondary tier fit (v5)
@dataclass(frozen=True)
class TierFit:
    """The tier-indicator secondary fit, reported in F8 and licensing nothing.

    ``Y = alpha_f + beta*d + gamma * 1[Tier 2]`` over **twelve** points: the
    nine the primary fit uses plus the three near-form controls, which sit at
    a different structural tier. It is registered so that the tier's
    contribution is *reported* rather than absorbed silently into a residual,
    and ``gamma`` is an F8 secondary: it licenses no claim.
    """

    slope: float
    gamma: float
    intercepts: dict[str, float]
    n_points: int
    residuals: dict[str, float]
    #: The named formulation of open_items.U2 this fit was computed under.
    #: Recorded on the object because two of them estimate different things.
    formulation: str = ""
    #: Whether this is the formulation U2 was **resolved** at. A fit computed
    #: under a non-adopted construction is a characterisation of what the
    #: study did not register, and it says so on its own face rather than
    #: relying on a reader to check the formulation string against the record.
    adopted: bool = False


def _tier_design_rows(points: Sequence[SpectrumPoint],
                      indicator: Mapping[str, float],
                      formulation: str) -> tuple[list[list[float]],
                                                 list[str]]:
    """The design matrix for one **named** formulation of §11.8's secondary.

    Both constructions are written here so that a reader can see what the
    choice cost. U2 resolved at A2, so A2 is what a caller who names nothing
    gets --- but it is reached through the open-item registry, not by being
    written into a signature, so the refusal is still there if the resolution
    goes away. ``A1`` --- a family intercept for each of the six families ---
    is not constructed at all: it is exactly singular, and building it to
    discover that at runtime would invite a caller to reach for a
    pseudoinverse. ``A3`` is not constructed either: it deletes F8's
    registered ``gamma_tier``.
    """
    if formulation == "A2":
        # alpha_f over the three CORE families; a Tier-2 point sits at the
        # unweighted mean core intercept plus gamma.
        families = sorted({p.family for p in points if not indicator[p.slot]})
        if len(families) < 2:
            raise ProtocolError(
                "the secondary fit needs at least two core families to "
                "define the intercepts gamma is measured against")
        rows = []
        for p in points:
            if indicator[p.slot]:
                row = [1.0 / len(families)] * len(families)
            else:
                row = [1.0 if p.family == f else 0.0 for f in families]
            rows.append(row + [p.difficulty, indicator[p.slot]])
        return rows, families
    if formulation == "A4":
        # one common intercept; beta then absorbs between-family level
        # differences that the PRIMARY form removes deliberately.
        return ([[1.0, p.difficulty, indicator[p.slot]] for p in points],
                ["common"])
    raise ProtocolError(
        f"{formulation!r} is not a constructed formulation of §11.8's "
        "secondary fit; open_items.U2 registers A1 (singular, never "
        "constructed), A2, A3 (drops F8's gamma_tier and is not constructed) "
        "and A4")


def adopted_formulation() -> str:
    """§11.8's registered secondary formulation, from U2's resolution.

    Not a module literal: U2 is resolved in ``researcher_decisions.json`` and
    read from there, so the construction the study registers and the
    construction the code runs are the same fact rather than two facts that
    have to be kept equal.
    """
    return open_items.assert_item_resolved(
        "U2", where="analysis.spectrum.adopted_formulation")


def assert_adopted_formulation(fit: TierFit, *, where: str) -> TierFit:
    """Refuse a non-adopted construction on any reporting path.

    U2 is resolved at A2. A1, A3 and A4 remain in the source --- A4
    constructed, A1 refused by name, A3 never built --- because a study has to
    be able to show what it did not register and because the U2 packet's
    decisive comparison is computed from A4 on every test run. None of them
    may reach a v5 result table, and this is the call that says so.
    """
    if not fit.adopted:
        raise ProtocolError(
            f"{where}: this fit was computed under formulation "
            f"{fit.formulation!r} and §11.8's registered secondary is "
            f"{adopted_formulation()!r} (open_items U2). A non-adopted "
            "construction is a historical characterisation and estimates a "
            "different quantity; it may not be reported as the study's "
            "gamma_tier")
    return fit


def fit_with_tier_indicator(points: Sequence[SpectrumPoint],
                            tiers: Mapping[str, int],
                            *, formulation: str | None = None) -> TierFit:
    """§11.8's secondary fit over twelve points, under U2's adopted reading.

    ``tiers`` maps slot -> structural tier. The indicator is 1 for Tier 2 and
    0 otherwise.

    **§11.8 did not identify this fit and this function never chose one for
    it.** The section writes ``Y = alpha_f + beta*d + gamma*1[Tier 2]`` over
    twelve points and never said what ``alpha_f`` is for the three near-form
    controls. Give each of them a family intercept and ``gamma`` becomes
    exactly collinear with the sum of those three dummies: the normal
    equations are singular and ``gamma`` has no unique least-squares value.
    More than one repair is mathematically admissible and they estimate
    different things --- ``protocol/open_items.py`` U2 carries all four with
    what each changes --- so this refused until a researcher resolved U2.

    **U2 is now resolved at A2**: ``alpha_f`` ranges over the three CORE
    families and a Tier-2 point sits at the unweighted mean core intercept
    plus ``gamma``. It was never repaired by a pseudoinverse, a dropped column
    chosen from the observed data, a ridge term or a silent reference coding,
    because each of those would have picked one of the alternatives without
    saying so. Passing ``formulation`` explicitly still runs a named
    construction, and the returned fit carries ``adopted=False`` when that
    construction is not the registered one.

    ``gamma`` is an F8 **secondary** and licenses no claim, so the amendment
    §11.8 needed costs no claim level either way.
    """
    if any(p.slot == "A" for p in points):
        raise ProtocolError("§11.8: A must not enter the fit that predicts A")
    if any(p.slot == C.CLASS_SLOT for p in points):
        raise ProtocolError(
            "§13.10: the broad-class companion enters no fit")
    indicator = {p.slot: 1.0 if tiers.get(p.slot) == 2 else 0.0
                 for p in points}
    if len(set(indicator.values())) < 2:
        raise ProtocolError(
            "the tier indicator does not vary over these points, so gamma is "
            "not identified. §11.8's secondary fit needs the near-form arm; "
            "without it the status is NEAR_FORM_ARM_NOT_AVAILABLE and the "
            "secondary is not reported")
    chosen = formulation or open_items.assert_item_resolved(
        "U2", where="analysis.spectrum.fit_with_tier_indicator")
    if formulation is not None:
        # An explicit formulation is a caller saying which construction it
        # wants exercised. It still may not produce a v5 number while U2 is
        # unresolved: the block is on the fit, not on the arithmetic.
        open_items.assert_item_resolved(
            "U2", where="analysis.spectrum.fit_with_tier_indicator"
                        f" (formulation={formulation})")
    design, columns = _tier_design_rows(points, indicator, chosen)
    k = len(design[0])
    xtx = [[sum(r[i] * r[j] for r in design) for j in range(k)]
           for i in range(k)]
    xty = [sum(r[i] * p.loss for r, p in zip(design, points))
           for i in range(k)]
    for col in range(k):
        pivot = max(range(col, k), key=lambda r: abs(xtx[r][col]))
        if abs(xtx[pivot][col]) < 1e-12:
            raise ProtocolError(
                "the tier-indicator design matrix is singular; the secondary "
                "fit is not identified on these points")
        xtx[col], xtx[pivot] = xtx[pivot], xtx[col]
        xty[col], xty[pivot] = xty[pivot], xty[col]
        for row in range(k):
            if row == col:
                continue
            factor = xtx[row][col] / xtx[col][col]
            for j in range(col, k):
                xtx[row][j] -= factor * xtx[col][j]
            xty[row] -= factor * xty[col]
    beta = [xty[i] / xtx[i][i] for i in range(k)]
    intercepts = {f: beta[i] for i, f in enumerate(columns)}
    slope, gamma = beta[-2], beta[-1]
    mean_intercept = sum(intercepts.values()) / len(intercepts)
    residuals = {}
    for p in points:
        base = (mean_intercept + gamma if indicator[p.slot]
                else intercepts.get(p.family, mean_intercept))
        residuals[p.slot] = p.loss - (base + slope * p.difficulty)
    return TierFit(slope=slope, gamma=gamma, intercepts=intercepts,
                   n_points=len(points), residuals=residuals,
                   formulation=chosen,
                   adopted=chosen == adopted_formulation())
