"""§13.7: two independent calibration splits, and the equivalence rule.

**The problem it names.** v4r4 measured candidates once, at 96 topics, and
selected the nearest inside a caliper of 0.10 --- about 2.1 standard errors
wide on the measured split-half variance. Selection inside a two-SE window is
substantially selection on noise, and the winner's curse it produces is
observable as the pre-screen-to-calibration collapse §12.2 measures: median
|Delta iota| of 0.071, with 35.7% of candidates moving further between the two
stages than the whole width of the caliper they then have to clear.

**The rule.** Calibration-A and Calibration-B are disjoint 96-topic sets, each
measured at M_cal = 4 on the same candidate list. R passes when all three
hold:

1. R is **independently admissible** under V_head, V_chance, V_inter and
   V_diff on Calibration-A **and** on Calibration-B, each evaluated on that
   split alone;
2. the 95% percentile-bootstrap interval for ``iota_A - iota_B``, resampling
   topics within split, lies wholly inside +/- 0.20;
3. the same interval for ``p_solo_A - p_solo_B`` lies wholly inside +/- 0.20.

**Why +/- 0.20.** It is twice the registered matching caliper. A coordinate
that cannot be pinned to twice the caliper across two independent 96-topic
splits cannot support matching at the caliper.

**What it implies, stated so it is not a surprise.** The rule is satisfiable
only when SE(iota_R) at 96 topics is about 0.07 or better. On the v4r4
measurements that holds for chance-free candidates (SE about 0.033) and fails
for candidates near kappa = 0.75 (SE about 0.081). **V_chance and V_stab
therefore overlap**, and the overlap is registered rather than removed: one is
justified on validity and one on precision, and a rule that holds for two
reasons is not a rule to delete.

**iota_A is subject to the same rule**, because §12.2 measured iota_A itself
moving by up to 0.048 between stages and both ends of every distance are
estimated.

**One thing here is not decided, and it is not decided in code either.** §34
D16 asks whether Calibration-B measures the complete carried set or only
Calibration-A's survivors. §12.7's standing proposal restricts it, which
changes no admission verdict --- condition 1 requires admissibility on both
splits, so a candidate failing on A is excluded whatever B would have said ---
at the price that the two splits are not exchangeable and the rule is "A
screens, B confirms" rather than two independent measurements. The red team
(R11) says "independent" overstates it. Both populations are expressible below
and ``calibration_b_population`` refuses until D16 is closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v5.analysis.intervals import bootstrap_difference, interval_inside
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages.calibration_table import CalibrationRow
from dci1v5.stages.validity import evaluate_validity

__all__ = ["SPLIT_ADMISSIBILITY_COMPONENTS", "calibration_b_population",
           "SplitPair", "split_pair", "stability_verdict",
           "assert_not_pooled"]

#: §13.7 condition 1. The components that must hold **on each split alone**.
#: V_spec, V_sat and V_struct are properties of the instrument and the family,
#: not of a topic sample, so re-evaluating them per split would test nothing
#: and they are checked once on the pooled table.
SPLIT_ADMISSIBILITY_COMPONENTS = ("V_head", "V_chance", "V_inter", "V_diff")


def calibration_b_population(carried: Sequence[str],
                             a_survivors: Sequence[str]) -> tuple[str, ...]:
    """§34 D16: which candidates Calibration-B measures.

    Both behaviours exist here and neither is reachable while D16 is open.
    ``a_survivors`` is §12.7's standing proposal --- about 35,000 fewer
    generations per replication, and no admission verdict changes because
    §13.7 condition 1 requires admissibility on both splits. The alternative
    measures everything and buys exchangeability, which is what R11 says the
    word "independent" currently overstates.
    """
    return decisions.choice(
        "D16",
        {"a_survivors": tuple(a_survivors),
         "complete_population": tuple(carried)},
        where="stages.stability.calibration_b_population")


@dataclass(frozen=True)
class SplitPair:
    """One candidate's two split rows, held together so neither is pooled."""

    candidate: str
    a: CalibrationRow
    b: CalibrationRow

    def __post_init__(self):
        if self.a.split != C.CALIBRATION_A or self.b.split != C.CALIBRATION_B:
            raise ProtocolError(
                f"{self.candidate}: §13.7 pairs a Calibration-A row with a "
                f"Calibration-B row; got {self.a.split!r} and {self.b.split!r}")
        if self.a.label != self.b.label:
            raise ProtocolError(
                f"§13.7 pairs the same candidate on both splits; got "
                f"{self.a.label} and {self.b.label}")
        if self.a.model_key != self.b.model_key:
            raise ProtocolError(
                f"{self.candidate}: the two splits describe different models")


def split_pair(rows_a: Sequence[CalibrationRow],
               rows_b: Sequence[CalibrationRow]) -> dict[str, SplitPair]:
    """Index the two split tables by candidate, refusing a mismatch."""
    by_a = {r.label: r for r in rows_a}
    by_b = {r.label: r for r in rows_b}
    return {label: SplitPair(label, by_a[label], by_b[label])
            for label in sorted(set(by_a) & set(by_b))}


def assert_not_pooled(rows: Sequence[CalibrationRow], *, split: str) -> None:
    """Refuse a table that has already been pooled across splits.

    §13.7's whole content is that the two splits are measured separately, so
    a call that hands it one pooled table has already lost the quantity the
    rule tests. Cheap, and it catches the mistake at the boundary.
    """
    wrong = sorted({r.split for r in rows} - {split})
    if wrong:
        raise ProtocolError(
            f"§13.7 evaluates each split on that split alone; this table "
            f"declares {split!r} and carries rows from {wrong}")


def stability_verdict(pair: SplitPair, *, iota_a_by_split: Mapping[str, float],
                      solo_a_by_split: Mapping[str, float],
                      seed: int, slot: str = "core_reference",
                      resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES,
                      ) -> dict[str, Any]:
    """§13.7's three conditions, with every measured value kept.

    ``iota_a_by_split`` and ``solo_a_by_split`` are **A's own** coordinates on
    each split, because condition 1's V_diff is a distance and both ends of
    every distance are estimated. iota_A is subject to the same equivalence
    rule and ``assert_iota_a_stable`` below is where that is checked.
    """
    per_split: dict[str, Any] = {}
    admissible_on_both = True
    reasons: list[str] = []
    for name, row in ((C.CALIBRATION_A, pair.a), (C.CALIBRATION_B, pair.b)):
        verdict = evaluate_validity(
            row, slot=slot, iota_a=iota_a_by_split[name],
            solo_compliance_a=solo_a_by_split[name],
            components=SPLIT_ADMISSIBILITY_COMPONENTS)
        # `passed` is False while any component is unevaluated, so read the
        # selected components directly: this call deliberately evaluates a
        # subset and the subset is what condition 1 names.
        selected = [c for c in verdict.components
                    if c.name in SPLIT_ADMISSIBILITY_COMPONENTS]
        ok = all(c.passed for c in selected)
        per_split[name] = {
            "admissible": ok, "iota": row.iota,
            "solo_compliance": row.solo_compliance,
            "chance_compliance": row.chance_compliance,
            "kappa_under_b": row.kappa_under_b,
            "components": [c.as_dict() for c in selected]}
        if not ok:
            admissible_on_both = False
            first = next(c.name for c in selected if c.passed is False)
            reasons.append(f"not independently admissible on {name}: "
                           f"{first}")

    iota_gap = None
    solo_gap = None
    if pair.a.per_topic_solo and pair.b.per_topic_solo:
        # iota is a monotone transform of the split's own solo mean at a
        # fixed chance value, so the per-topic solo values resample it too.
        ka, kb = pair.a.chance_compliance, pair.b.chance_compliance
        iota_a_topics = [(v - ka) / (1.0 - ka) for v in pair.a.per_topic_solo]
        iota_b_topics = [(v - kb) / (1.0 - kb) for v in pair.b.per_topic_solo]
        iota_gap = bootstrap_difference(iota_a_topics, iota_b_topics,
                                        resamples=resamples, seed=seed)
        solo_gap = bootstrap_difference(list(pair.a.per_topic_solo),
                                        list(pair.b.per_topic_solo),
                                        resamples=resamples, seed=seed + 1)
    bound = (-C.STABILITY_EQUIVALENCE_BOUND, C.STABILITY_EQUIVALENCE_BOUND)
    equivalent = True
    for label, gap in (("iota", iota_gap), ("raw solo compliance", solo_gap)):
        if gap is None:
            equivalent = False
            reasons.append(
                f"§13.7 needs per-topic values on both splits to test the "
                f"{label} difference; none were supplied, and an untested "
                "equivalence is not a satisfied one")
            continue
        if not interval_inside((gap["lower"], gap["upper"]), bound):
            equivalent = False
            reasons.append(
                f"the 95% bootstrap interval for the {label} split difference "
                f"[{gap['lower']:.4f}, {gap['upper']:.4f}] is not inside "
                f"+/-{C.STABILITY_EQUIVALENCE_BOUND}")

    return {"candidate": pair.candidate,
            "passed": bool(admissible_on_both and equivalent),
            "reason": "; ".join(reasons) or None,
            "admissible_on_both_splits": admissible_on_both,
            "equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
            "iota_split_difference": iota_gap,
            "solo_split_difference": solo_gap,
            "per_split": per_split,
            "resamples": resamples, "seed": seed}


def assert_iota_a_stable(*, per_topic_a: Sequence[float],
                         per_topic_b: Sequence[float],
                         chance_a: float, chance_b: float, seed: int,
                         resamples: int = C.STABILITY_BOOTSTRAP_RESAMPLES
                         ) -> dict[str, Any]:
    """§13.7: A's own difficulty coordinate meets the same equivalence rule.

    §12.2 measured iota_A itself moving by up to 0.048 between stages, and
    every §13.8 distance is a distance from it. A design that pinned every
    candidate and left the reference point free would be matching to a moving
    target.
    """
    ia = [(v - chance_a) / (1.0 - chance_a) for v in per_topic_a]
    ib = [(v - chance_b) / (1.0 - chance_b) for v in per_topic_b]
    gap = bootstrap_difference(ia, ib, resamples=resamples, seed=seed)
    bound = (-C.STABILITY_EQUIVALENCE_BOUND, C.STABILITY_EQUIVALENCE_BOUND)
    stable = interval_inside((gap["lower"], gap["upper"]), bound)
    return {"quantity": "iota_A", "passed": stable, "interval": gap,
            "bound": C.STABILITY_EQUIVALENCE_BOUND,
            "reason": None if stable else
            ("A's own difficulty coordinate is not equivalent across the two "
             "calibration splits, so every §13.8 distance is measured from a "
             "reference point the design cannot pin")}
