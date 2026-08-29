"""Local-reference validity and spectrum-reference validity, stated apart.

**Where the local closeness rule leaks into the spectrum in v5-v7.**

1. ``dci1v7.stages.stability.SPLIT_ADMISSIBILITY_COMPONENTS`` is
   ``("V_head", "V_chance", "V_inter", "V_diff")``: §13.7 condition 1 asks
   for independent admissibility on each split **including V_diff**, §13.8's
   proximity caliper (|iota_R - iota_A| <= 0.10, the Newcombe region, the
   secondary caliper).
2. ``dci1v7.stages.feasibility.calibration_at`` computes **one**
   ``stability_verdict`` per candidate, in the default slot
   ``core_reference``, and passes the same dictionary to core admission and
   to spectrum selection.
3. ``dci1v7.stages.selection.select_spectrum_triple`` evaluates
   ``SPECTRUM_COMPONENTS`` = every component except V_diff --- but ``V_stab``
   is one of them, and ``_v_stab`` only *reads* the pre-computed verdict, so
   the spectrum rung is required to be within the caliper on both splits
   after all. The registered ±0.20 targets are then unreachable by
   construction (the registered spectrum pool spans <= 0.16 on every stored
   replication), and v6 qwen3-4b met C4 6/6 yet bound zero triples.

**The separation.** Two validities over the same registered components:

* ``LOCAL`` --- the v7 full V(R) **unchanged**, folded stability included:
  a local reference must be matched to A on the pooled table *and*
  independently admissible-and-matched on each split. Nothing here is
  weakened; Delta_R keeps every guarantee it has.
* ``SPECTRUM`` --- V_spec, V_sat, V_head, V_chance, V_struct, V_inter, an
  **unfolded** V_stab (§13.7 with condition 1 read on V_head, V_chance,
  V_inter --- the components that are properties of the rung, not of its
  distance from A --- and conditions 2 and 3 unchanged: the bootstrap split
  differences of iota and of raw solo inside ±0.20), and a position rule
  ``V_pos``: the rung sits at least ``d_min`` from iota_A on the pooled
  table. A spectrum rung is deliberately *not* close to A and is never asked
  to be.

``unfolded_stability`` reuses the registered helpers (``evaluate_validity``
and ``bootstrap_difference``) so the equivalence conditions are computed by
the same code and the same seed as §13.7's.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from dci1v7.analysis.intervals import bootstrap_difference, interval_inside, wilson
from dci1v7.protocol import constants as C
from dci1v7.protocol.taxonomy import SLOT_CORE, SLOT_SPECTRUM
from dci1v7.stages.calibration_table import CalibrationRow, tie_key
from dci1v7.stages.interaction import displacement, projected_compliance
from dci1v7.stages.stability import SplitPair, split_pair
from dci1v7.stages.validity import VALIDITY_COMPONENTS, evaluate_validity

__all__ = [
    "FOLDED_SPLIT_COMPONENTS",
    "LOCAL_COMPONENTS",
    "SPECTRUM_COMPONENTS",
    "UNFOLDED_SPLIT_COMPONENTS",
    "SpectrumRule",
    "classify_pool",
    "coordinate_verdict",
    "interaction_guard_verdict",
    "local_validity",
    "spectrum_validity",
    "unfolded_stability",
]

#: The registered v7 full V(R): the LOCAL rule, unchanged.
LOCAL_COMPONENTS = tuple(VALIDITY_COMPONENTS)
#: The SPECTRUM rule, in evaluation order. V_spec, V_sat, V_struct and
#: V_chance are the registered components unchanged; V_coord replaces
#: V_head, V_inter_s replaces V_inter, V_stab is the unfolded §13.7, V_pos
#: is new. See ``SpectrumRule`` for why each of the two replacements exists.
SPECTRUM_COMPONENTS = ("V_spec", "V_sat", "V_coord", "V_chance", "V_struct",
                       "V_inter_s", "V_stab", "V_pos")
#: The registered components the spectrum reads through ``evaluate_validity``.
_REGISTERED_SHARED = ("V_spec", "V_sat", "V_chance", "V_struct")
#: §13.7 condition 1 as v7 runs it (folded) and as the spectrum reads it.
FOLDED_SPLIT_COMPONENTS = ("V_head", "V_chance", "V_inter", "V_diff")
UNFOLDED_SPLIT_COMPONENTS = ("V_coord", "V_chance", "V_inter_s")


@dataclass(frozen=True)
class SpectrumRule:
    """Spectrum-specific admissibility: what a difficulty coordinate needs.

    **Which registered rules are headroom rules, and why they do not apply
    to a spectrum slot.** §13.4's V_head band [0.10, 0.90] on the Wilson
    interval is §13.14's composed-headroom band (0.05, 0.95) contracted by
    0.05: it guarantees the *reference's own* composed compliance has room to
    move, which the reciprocal estimands D(R <- B) of the core arm need.
    §13.6's V_inter projected band [0.10, 0.90] is the same band again, on
    the projection of R's compliance under B. A spectrum slot carries
    D(B <- X) and d_X only (``protocol/identification.SPECTRUM_ESTIMANDS``
    has no reciprocal member), so neither headroom band protects anything
    the spectrum reads; what they do is remove exactly the easy references
    (p_solo above ~0.855 at n = 192) the difficulty-response fit needs above
    a 0.70-aimed A.

    **Which rules protect the coordinate and stay.** Vacuity (a vacuous pass
    is not a difficulty); the chance ceiling and its Wilson bound (V_chance:
    a chance-dominated rate has an amplified, unstable iota); the lift floor
    (a reference that buys < 0.20 over chance is not an instruction the
    model follows); degeneracy (kappa >= 0.99: no coordinate); the
    displacement bound (B must not move the regime the coordinate was
    measured in); the two-split equivalence (V_stab); joint satisfiability
    and structure (V_sat, V_spec, V_struct).

    **What replaces the headroom bands.** ``V_coord``: the point solo rate
    inside ``band`` --- v5 registered ``SPECTRUM_ELIGIBILITY_BAND = (0.10,
    0.95)`` for the spectrum and no code ever applied it; it is a degeneracy
    guard on the *point*, not a headroom band on an interval --- plus a
    precision floor on the coordinate itself, SE(iota) <= ``max_se_iota``
    from the per-topic values (a coordinate the design cannot pin is not a
    design point). ``V_inter_s``: the displacement bound unchanged, and the
    projection inside the same guard band rather than the headroom band.
    """

    band: tuple[float, float] = C.SPECTRUM_ELIGIBILITY_BAND
    vacuity_max: float = C.REFERENCE_VACUITY_MAX
    lift_min: float = C.INSTRUCTION_LIFT_MIN
    degeneracy: float = C.CHANCE_DEGENERACY_MAX
    max_se_iota: float = 0.05
    displacement_max: float = C.DISPLACEMENT_MAX
    projection_guard: tuple[float, float] = C.SPECTRUM_ELIGIBILITY_BAND
    d_min: float = 0.05


DEFAULT_SPECTRUM_RULE = SpectrumRule()


def _se_iota(row: CalibrationRow) -> float | None:
    if not row.per_topic_solo:
        return None
    n = len(row.per_topic_solo)
    if n < 2:
        return None
    m = sum(row.per_topic_solo) / n
    var = sum((v - m) ** 2 for v in row.per_topic_solo) / (n - 1)
    se_p = math.sqrt(var / n)
    return se_p / (1.0 - row.chance_compliance)


def coordinate_verdict(row: CalibrationRow, *, rule: SpectrumRule = DEFAULT_SPECTRUM_RULE
                       ) -> dict:
    """V_coord: the difficulty coordinate is defined, real, and precise."""
    problems = []
    p, k = row.solo_compliance, row.chance_compliance
    if k >= rule.degeneracy:
        problems.append(f"chance compliance {k:.4f} at or above "
                        f"{rule.degeneracy}: iota is undefined (§11.2)")
    if not rule.band[0] <= p <= rule.band[1]:
        problems.append(f"raw solo compliance {p:.4f} outside the spectrum "
                        f"guard band {list(rule.band)}")
    if row.solo_vacuity > rule.vacuity_max:
        problems.append(f"solo vacuity {row.solo_vacuity:.4f} above "
                        f"{rule.vacuity_max}")
    if p - k < rule.lift_min:
        problems.append(f"instruction lift {p - k:.4f} below {rule.lift_min}")
    se = _se_iota(row) if k < rule.degeneracy else None
    if se is not None and se > rule.max_se_iota:
        problems.append(f"SE(iota) {se:.4f} above {rule.max_se_iota}")
    return {"component": "V_coord", "evaluated": True, "passed": not problems,
            "reason": "; ".join(problems) or None,
            "values": {"solo": p, "chance": k, "lift": p - k,
                       "vacuity": row.solo_vacuity, "se_iota": se,
                       "band": list(rule.band),
                       "wilson": list(wilson(p, row.n_topics))}}


def interaction_guard_verdict(row: CalibrationRow, *,
                              rule: SpectrumRule = DEFAULT_SPECTRUM_RULE) -> dict:
    """V_inter_s: §13.6's displacement bound, and the projection inside the
    guard band (not the headroom band)."""
    if row.kappa_under_b is None:
        return {"component": "V_inter_s", "evaluated": True, "passed": False,
                "reason": "kappa(R|B) not measured; absence is never a pass",
                "values": {}}
    if row.chance_compliance >= rule.degeneracy:
        return {"component": "V_inter_s", "evaluated": True, "passed": False,
                "reason": "no coordinate to project", "values": {}}
    sigma = displacement(row.chance_compliance, row.kappa_under_b)
    p_hat = projected_compliance(row.kappa_under_b, row.iota)
    problems = []
    if abs(sigma) > rule.displacement_max:
        problems.append(f"displacement {sigma:+.4f} beyond "
                        f"+/-{rule.displacement_max}")
    if not rule.projection_guard[0] <= p_hat <= rule.projection_guard[1]:
        problems.append(f"projected compliance under B {p_hat:.4f} outside "
                        f"the guard band {list(rule.projection_guard)}")
    return {"component": "V_inter_s", "evaluated": True, "passed": not problems,
            "reason": "; ".join(problems) or None,
            "values": {"kappa": row.chance_compliance,
                       "kappa_under_b": row.kappa_under_b,
                       "displacement": sigma, "projected": p_hat}}


def _spectrum_components(row: CalibrationRow, *, rule: SpectrumRule,
                         stability=None, with_stab: bool = True) -> list[dict]:
    reg = evaluate_validity(row, slot=SLOT_SPECTRUM,
                            components=_REGISTERED_SHARED,
                            core_family_tier=row.structural_tier)
    by = {c.name: c.as_dict() for c in reg.components
          if c.name in _REGISTERED_SHARED}
    out = [by["V_spec"], by["V_sat"], coordinate_verdict(row, rule=rule),
           by["V_chance"], by["V_struct"],
           interaction_guard_verdict(row, rule=rule)]
    if with_stab:
        if stability is None:
            out.append({"component": "V_stab", "evaluated": False,
                        "passed": None, "reason": "no two-split table",
                        "values": {}})
        else:
            out.append({"component": "V_stab", "evaluated": True,
                        "passed": bool(stability["passed"]),
                        "reason": stability.get("reason"),
                        "values": {k: v for k, v in stability.items()
                                   if k in ("iota_split_difference",
                                            "solo_split_difference",
                                            "admissible_on_both_splits")}})
    return out


def unfolded_stability(pair: SplitPair, *, seed: int,
                       resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES,
                       rule: SpectrumRule = DEFAULT_SPECTRUM_RULE) -> dict[str, Any]:
    """§13.7 for a spectrum rung: conditions 2 and 3 verbatim, condition 1
    on the spectrum's own per-rung components (V_coord, V_chance, V_inter_s)
    --- no V_diff, no headroom band. Same helpers and seed convention as
    ``stability.stability_verdict``."""
    per_split: dict[str, Any] = {}
    admissible = True
    reasons: list[str] = []
    for name, row in ((C.CALIBRATION_A, pair.a), (C.CALIBRATION_B, pair.b)):
        comps = _spectrum_components(row, rule=rule, with_stab=False)
        selected = [c for c in comps if c["component"] in UNFOLDED_SPLIT_COMPONENTS]
        ok = all(c["passed"] for c in selected)
        per_split[name] = {"admissible": ok, "iota": row.iota
                           if row.chance_compliance < rule.degeneracy else None,
                           "solo_compliance": row.solo_compliance,
                           "components": selected}
        if not ok:
            admissible = False
            first = next(c["component"] for c in selected if c["passed"] is False)
            reasons.append(f"not independently admissible on {name}: {first}")
    iota_gap = solo_gap = None
    if pair.a.per_topic_solo and pair.b.per_topic_solo and admissible:
        ka, kb = pair.a.chance_compliance, pair.b.chance_compliance
        ia = [(v - ka) / (1.0 - ka) for v in pair.a.per_topic_solo]
        ib = [(v - kb) / (1.0 - kb) for v in pair.b.per_topic_solo]
        iota_gap = bootstrap_difference(ia, ib, resamples=resamples, seed=seed)
        solo_gap = bootstrap_difference(list(pair.a.per_topic_solo),
                                        list(pair.b.per_topic_solo),
                                        resamples=resamples, seed=seed + 1)
    bound = (-C.STABILITY_EQUIVALENCE_BOUND, C.STABILITY_EQUIVALENCE_BOUND)
    equivalent = True
    for label, gap in (("iota", iota_gap), ("raw solo compliance", solo_gap)):
        if gap is None:
            equivalent = False
            if admissible:
                reasons.append(f"no per-topic values to test the {label} "
                               "split difference")
            continue
        if not interval_inside((gap["lower"], gap["upper"]), bound):
            equivalent = False
            reasons.append(f"the {label} split difference interval "
                           f"[{gap['lower']:.4f}, {gap['upper']:.4f}] is not "
                           f"inside +/-{C.STABILITY_EQUIVALENCE_BOUND}")
    return {"candidate": pair.candidate, "passed": bool(admissible and equivalent),
            "reason": "; ".join(reasons) or None,
            "admissible_on_both_splits": admissible,
            "split_components": list(UNFOLDED_SPLIT_COMPONENTS),
            "iota_split_difference": iota_gap,
            "solo_split_difference": solo_gap,
            "per_split": per_split, "resamples": resamples, "seed": seed,
            "folded": False}


def local_validity(row: CalibrationRow, *, iota_a: float,
                   solo_compliance_a: float, n_topics_a: int | None,
                   folded_stability: Mapping[str, Any] | None,
                   slot: str = SLOT_CORE) -> dict[str, Any]:
    """The v7 full V(R) for a local (core) reference. Unchanged.

    A rung whose chance compliance is at or above the degeneracy point has no
    coordinate (§11.2); v7 withholds such a row before selection sees it, and
    here it is recorded as failing at V_chance rather than evaluated."""
    if row.chance_compliance >= C.CHANCE_DEGENERACY_MAX:
        return {"candidate": row.label, "rule": "LOCAL", "passed": False,
                "first_failing_component": "V_chance",
                "components": [{"component": "V_chance", "evaluated": True,
                                "passed": False,
                                "reason": f"chance compliance "
                                          f"{row.chance_compliance:.4f} at or "
                                          f"above {C.CHANCE_DEGENERACY_MAX}: "
                                          "no difficulty coordinate (§11.2)",
                                "values": {}}],
                "iota": None, "distance": None}
    verdict = evaluate_validity(
        row, slot=slot, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
        n_topics_a=n_topics_a, stability=folded_stability,
        components=LOCAL_COMPONENTS)
    return {"candidate": row.label, "rule": "LOCAL",
            "passed": bool(verdict.passed),
            "first_failing_component": verdict.first_failing_component,
            "components": [c.as_dict() for c in verdict.components],
            "iota": row.iota, "distance": abs(row.iota - iota_a)}


def spectrum_validity(row: CalibrationRow, *, iota_a: float,
                      unfolded: Mapping[str, Any] | None,
                      rule: SpectrumRule = DEFAULT_SPECTRUM_RULE) -> dict[str, Any]:
    """The SPECTRUM rule (``SpectrumRule``), evaluated lexicographically."""
    components = _spectrum_components(row, rule=rule, stability=unfolded)
    defined = row.chance_compliance < rule.degeneracy
    distance = (row.iota - iota_a) if defined else float("nan")
    side = ("undefined" if not defined else
            "below" if tie_key(distance) < 0 else
            "above" if tie_key(distance) > 0 else "at")
    pos_ok = defined and abs(distance) >= rule.d_min and side != "at"
    components.append({"component": "V_pos", "evaluated": True,
                       "passed": pos_ok,
                       "reason": None if pos_ok else
                       (f"|iota - iota_A| = {abs(distance):.4f} is inside the "
                        f"spectrum minimum distance {rule.d_min}" if defined
                        else "no coordinate"),
                       "values": {"iota": row.iota if defined else None,
                                  "iota_a": iota_a, "distance": distance,
                                  "side": side, "d_min": rule.d_min}})
    failing = next((c["component"] for c in components
                    if c["passed"] is False), None)
    return {"candidate": row.label, "rule": "SPECTRUM",
            "passed": failing is None, "first_failing_component": failing,
            "components": components, "iota": row.iota if defined else None,
            "side": side, "distance": distance,
            "se_iota": _se_iota(row) if defined else None,
            "passes_v7_v_head": bool(evaluate_validity(
                row, slot=SLOT_SPECTRUM, components=("V_head",),
                core_family_tier=row.structural_tier).components[2].passed)}


def classify_pool(pooled: Sequence[CalibrationRow],
                  rows_a: Sequence[CalibrationRow],
                  rows_b: Sequence[CalibrationRow], *, iota_a: float,
                  solo_compliance_a: float, n_topics_a: int | None,
                  folded_stability: Mapping[str, Mapping[str, Any]],
                  seed: int = 0,
                  resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES,
                  rule: SpectrumRule = DEFAULT_SPECTRUM_RULE) -> dict[str, Any]:
    """Every pooled rung under both rules. ``folded_stability`` is v7's
    Gate-3A stability map (read, not recomputed); the unfolded one is
    computed here from the split rows."""
    pairs = split_pair(rows_a, rows_b)
    unfolded = {label: unfolded_stability(pair, seed=seed, resamples=resamples,
                                          rule=rule)
                for label, pair in pairs.items()}
    local, spectrum = {}, {}
    for row in pooled:
        local[row.label] = local_validity(
            row, iota_a=iota_a, solo_compliance_a=solo_compliance_a,
            n_topics_a=n_topics_a,
            folded_stability=folded_stability.get(row.label))
        spectrum[row.label] = spectrum_validity(
            row, iota_a=iota_a, unfolded=unfolded.get(row.label), rule=rule)
    n_head = sum(1 for v in spectrum.values()
                 if v["passed"] and v["passes_v7_v_head"])
    return {"local": local, "spectrum": spectrum, "unfolded_stability": unfolded,
            "n_local_valid": sum(1 for v in local.values() if v["passed"]),
            "n_spectrum_valid": sum(1 for v in spectrum.values()
                                    if v["passed"]),
            "n_spectrum_valid_inside_v_head": n_head,
            "n_spectrum_valid_beyond_v_head": sum(
                1 for v in spectrum.values() if v["passed"]) - n_head,
            "n_folded_stable": sum(1 for v in folded_stability.values()
                                   if v.get("passed")),
            "n_unfolded_stable": sum(1 for v in unfolded.values()
                                     if v["passed"])}
