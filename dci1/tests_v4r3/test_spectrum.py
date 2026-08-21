"""The difficulty relation, delta_difficulty, support and the refitting
bootstrap (§11.7, §13.8, §17.2).

Four failures these pin, each of which has actually occurred somewhere in this
programme's screens:

* a line fitted through the point it then predicts (the residual shrinks
  toward zero by construction, which is toward the null);
* a line fitted over companions all on one side of A, with the extrapolated
  residual reported as a measurement;
* a fitted nuisance object whose uncertainty is never propagated;
* a spectrum arm whose two extra rungs both landed on the same side of A.
"""
from __future__ import annotations

import math
import random

import pytest

from dci1v4.errors import ProtocolError
from dci1v4r3.analysis import spectrum as SP
from dci1v4r3.protocol import constants as C


def points(spec):
    return [SP.SpectrumPoint(slot=s, family=f, difficulty=d, loss=y)
            for s, f, d, y in spec]


NINE = points([
    ("R1-", "RF2", 0.40, 0.02), ("R1", "RF2", 0.60, 0.05),
    ("R1+", "RF2", 0.80, 0.08),
    ("R2-", "RF3", 0.42, 0.00), ("R2", "RF3", 0.61, 0.03),
    ("R2+", "RF3", 0.79, 0.07),
    ("R3-", "RF4", 0.38, 0.04), ("R3", "RF4", 0.59, 0.06),
    ("R3+", "RF4", 0.81, 0.10),
])


# ------------------------------------------------------- required failure 3
def test_A_may_not_enter_the_fit_that_predicts_A():
    with pytest.raises(ProtocolError, match="must not enter the fit"):
        SP.fit_difficulty_relation(
            NINE + points([("A", "A", 0.60, 0.09)]), predict_at=0.60)


def test_the_class_companion_may_not_enter_the_fit_either():
    with pytest.raises(ProtocolError, match="class companion"):
        SP.fit_difficulty_relation(
            NINE + points([(C.CLASS_SLOT, "CL8", 0.62, 0.60)]),
            predict_at=0.60)


def test_including_A_would_shrink_its_residual_toward_zero():
    """Why the exclusion is a rule, demonstrated rather than asserted."""
    fit = SP.fit_difficulty_relation(NINE, predict_at=0.60)
    honest = 0.30 - fit.predicted_at                 # A is far above the line
    contaminated_points = NINE + points([("A", "RF2", 0.60, 0.30)])
    # refit by hand, without the guard, to show the direction of the bias
    by_family = {}
    for p in contaminated_points:
        by_family.setdefault(p.family, []).append(p)
    d_bar = {f: sum(p.difficulty for p in ps) / len(ps)
             for f, ps in by_family.items()}
    y_bar = {f: sum(p.loss for p in ps) / len(ps) for f, ps in by_family.items()}
    sdd = sum((p.difficulty - d_bar[p.family]) ** 2 for p in contaminated_points)
    slope = sum((p.difficulty - d_bar[p.family]) * (p.loss - y_bar[p.family])
                for p in contaminated_points) / sdd
    intercepts = {f: y_bar[f] - slope * d_bar[f] for f in by_family}
    predicted = sum(intercepts.values()) / len(intercepts) + slope * 0.60
    contaminated = 0.30 - predicted
    assert abs(contaminated) < abs(honest)


# ------------------------------------------------------- required failure 6
def test_the_fit_is_family_aware_and_a_single_intercept_would_differ():
    """Three rungs of one family are not three independent observations.

    A single-intercept fit pushes between-family variation into the residual
    and hence into delta_difficulty; v4r2 §13.4 recorded that variation at
    0.177 and 0.188 at essentially constant companion compliance.
    """
    fit = SP.fit_difficulty_relation(NINE, predict_at=0.60)
    assert fit.n_families == 3
    assert len(fit.intercepts) == 3
    xs = [p.difficulty for p in NINE]
    ys = [p.loss for p in NINE]
    mx, my = sum(xs) / 9, sum(ys) / 9
    pooled_slope = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
                    / sum((x - mx) ** 2 for x in xs))
    assert abs(pooled_slope - fit.slope) > 1e-9


# ---------------------------------------------------- the weights and algebra
def test_the_prediction_weights_sum_to_one_so_the_solo_baseline_cancels():
    fit = SP.fit_difficulty_relation(NINE, predict_at=0.60)
    assert fit.sum_weights == pytest.approx(1.0, abs=1e-12)


def test_a_fit_centred_on_A_puts_equal_weight_on_every_point():
    """§16.1's leverage argument, which is why §13.6's offset is symmetric."""
    fit = SP.fit_difficulty_relation(NINE, predict_at=0.60)
    grand = sum(p.difficulty for p in NINE) / 9
    assert abs(grand - 0.60) < 0.01
    assert fit.sum_weights_squared < 0.13
    assert fit.sum_weights_squared >= 1.0 / 9.0 - 1e-12


# ------------------------------------------------------- required failure 4
def test_a_one_sided_companion_set_reports_non_identification():
    one_sided = points([
        ("R1-", "RF2", 0.20, 0.02), ("R1", "RF2", 0.30, 0.05),
        ("R1+", "RF2", 0.40, 0.08),
        ("R2-", "RF3", 0.22, 0.00), ("R2", "RF3", 0.31, 0.03),
        ("R2+", "RF3", 0.39, 0.07),
    ])
    verdict = SP.support_verdict(one_sided, difficulty_a=0.70)
    assert not verdict["holds"]
    assert "extrapolates to A" in verdict["reasons"][0]
    assert "not a null" in verdict["reading"]


def test_support_needs_two_companions_and_two_families_on_each_side():
    thin = points([
        ("R1-", "RF2", 0.55, 0.02), ("R1", "RF2", 0.62, 0.05),
        ("R1+", "RF2", 0.80, 0.08),
        ("R2", "RF3", 0.61, 0.03), ("R2+", "RF3", 0.79, 0.07),
        ("R3", "RF4", 0.59, 0.06), ("R3+", "RF4", 0.81, 0.10),
    ])
    verdict = SP.support_verdict(thin, difficulty_a=0.58)
    assert not verdict["holds"]
    assert any("families below" in r for r in verdict["reasons"])


def test_a_straddling_set_built_by_the_registered_rule_has_support():
    verdict = SP.support_verdict(NINE, difficulty_a=0.60)
    assert verdict["holds"]
    # §13.6 guarantees at least one point per side per family; a core rung
    # landing marginally off A adds to whichever side it falls on.
    assert verdict["n_below"] >= 3 and verdict["n_above"] >= 3
    assert len(verdict["families_below"]) == 3
    assert len(verdict["families_above"]) == 3


# ---------------------------------------------------- the end-to-end estimand
def _input(n_blocks=64, seed=11):
    rng = random.Random(seed)
    slots = {"R1-": "RF2", "R1": "RF2", "R1+": "RF2",
             "R2-": "RF3", "R2": "RF3", "R2+": "RF3",
             "R3-": "RF4", "R3": "RF4", "R3+": "RF4"}
    truth = {p.slot: (p.difficulty, p.loss) for p in NINE}
    blocks = tuple(f"b{i:03d}" for i in range(n_blocks))
    b_solo = [0.80 + rng.gauss(0, 0.02) for _ in blocks]
    companion_solo, companion_chance, b_with = {}, {}, {}
    for slot, family in slots.items():
        d, y = truth[slot]
        companion_chance[slot] = [0.20 + rng.gauss(0, 0.01) for _ in blocks]
        companion_solo[slot] = [0.20 + 0.80 * d + rng.gauss(0, 0.01)
                                for _ in blocks]
        b_with[slot] = [s - y + rng.gauss(0, 0.02)
                        for s in b_solo]
    b_with["A"] = [s - 0.14 + rng.gauss(0, 0.02) for s in b_solo]
    return SP.SpectrumInput(
        blocks=blocks, family_of=slots, b_solo=b_solo, b_with=b_with,
        companion_solo=companion_solo, companion_chance=companion_chance,
        a_solo=[0.60 + rng.gauss(0, 0.02) for _ in blocks],
        a_chance=[0.0 for _ in blocks])


def test_neither_A_nor_the_class_slot_may_be_given_a_family():
    data = _input()
    with pytest.raises(ProtocolError, match="excluded from"):
        SP.SpectrumInput(blocks=data.blocks,
                         family_of={**data.family_of, "A": "RF2"},
                         b_solo=data.b_solo, b_with=data.b_with,
                         companion_solo=data.companion_solo,
                         companion_chance=data.companion_chance,
                         a_solo=data.a_solo, a_chance=data.a_chance)


def test_the_two_algebraic_forms_of_delta_difficulty_agree():
    data = _input()
    value = SP.assert_algebraic_forms_agree(data)
    assert math.isfinite(value)


def test_delta_difficulty_recovers_the_excess_it_was_built_from():
    data = _input(n_blocks=400, seed=7)
    result = SP.estimate(data)
    assert result["support"]["holds"]
    # A costs B 0.14; the nine companions cost 0.00 to 0.10 with A's
    # difficulty in the middle, so the excess is positive and of that order.
    assert 0.05 < result["delta_difficulty"] < 0.15


# ------------------------------------------------------- required failure 5
def test_every_bootstrap_replicate_refits_rather_than_reusing_the_fit():
    data = _input(n_blocks=48, seed=3)
    full = list(range(len(data.blocks)))
    half = full[: len(full) // 2] * 2
    a = SP.estimate(data, full)
    b = SP.estimate(data, half)
    assert a["slope"] != b["slope"], (
        "a different resample must produce a different fitted slope; if it "
        "does not, the fit is being reused across replicates")
    assert a["difficulty_a"] != b["difficulty_a"], (
        "the difficulty coordinate must be recomputed per replicate too")


def test_the_bootstrap_resamples_blocks_and_nothing_else():
    data = _input(n_blocks=40, seed=5)
    out = SP.bootstrap_spectrum(data, resamples=200, seed=99)
    assert out["refit_per_replicate"] is True
    assert out["resamples"] == 200
    assert out["bootstrap_se"] > 0
    lo, hi = out["ci95_percentile"]
    assert lo < out["estimate"] < hi
    assert out["support"]["holds"]
    assert out["support_bootstrap_share"] > 0.5


def test_the_bootstrap_reports_the_support_share_not_only_the_point_verdict():
    data = _input(n_blocks=40, seed=5)
    out = SP.bootstrap_spectrum(data, resamples=200, seed=99)
    assert 0.0 <= out["support_bootstrap_share"] <= 1.0
    if out["support_bootstrap_share"] < C.SUPPORT_BOOTSTRAP_SHARE_MIN:
        assert "DIFFICULTY_SUPPORT_MARGINAL" in out["identification_statuses"]


def test_a_degenerate_spread_is_reported_rather_than_divided_by():
    flat = points([("R1", "RF2", 0.60, 0.05), ("R2", "RF3", 0.60, 0.03),
                   ("R3", "RF4", 0.60, 0.06)])
    with pytest.raises(ProtocolError, match="not identified"):
        SP.fit_difficulty_relation(flat, predict_at=0.60)


def test_a_companion_at_the_chance_ceiling_is_dropped_and_recorded():
    data = _input(n_blocks=40, seed=5)
    chance = dict(data.companion_chance)
    chance["R1+"] = [0.995 for _ in data.blocks]
    degenerate = SP.SpectrumInput(
        blocks=data.blocks, family_of=data.family_of, b_solo=data.b_solo,
        b_with=data.b_with, companion_solo=data.companion_solo,
        companion_chance=chance, a_solo=data.a_solo, a_chance=data.a_chance)
    result = SP.estimate(degenerate)
    assert result["dropped_points"] == ["R1+"]
    assert not result["support"]["holds"]
    assert any("degeneracy" in r for r in result["support"]["reasons"])
