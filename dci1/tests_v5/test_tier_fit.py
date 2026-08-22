"""§11.8's secondary fit: not identified as written, and not repaired here."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.analysis.spectrum import SpectrumPoint, fit_with_tier_indicator
from dci1v5.protocol import open_items
from dci1v5.protocol.open_items import OpenItemError

CORE = [
    SpectrumPoint(slot="R1", family="MK1", difficulty=0.30, loss=0.20),
    SpectrumPoint(slot="R1-", family="MK1", difficulty=0.10, loss=0.12),
    SpectrumPoint(slot="R1+", family="MK1", difficulty=0.50, loss=0.28),
    SpectrumPoint(slot="R2", family="MK2", difficulty=0.35, loss=0.26),
    SpectrumPoint(slot="R2-", family="MK2", difficulty=0.15, loss=0.18),
    SpectrumPoint(slot="R2+", family="MK2", difficulty=0.55, loss=0.34),
    SpectrumPoint(slot="R3", family="MK3", difficulty=0.40, loss=0.31),
    SpectrumPoint(slot="R3-", family="MK3", difficulty=0.20, loss=0.23),
    SpectrumPoint(slot="R3+", family="MK3", difficulty=0.60, loss=0.39),
]
NEAR = [
    SpectrumPoint(slot="N1", family="XC1", difficulty=0.32, loss=0.30),
    SpectrumPoint(slot="N2", family="XC2", difficulty=0.38, loss=0.34),
    SpectrumPoint(slot="N3", family="XC3", difficulty=0.44, loss=0.38),
]
TIERS = {p.slot: 1 for p in CORE} | {p.slot: 2 for p in NEAR}


def test_the_secondary_fit_refuses_while_u2_is_unresolved():
    with pytest.raises(OpenItemError):
        fit_with_tier_indicator(CORE + NEAR, TIERS)


def test_it_refuses_an_explicit_formulation_too(restore_open_items):
    """Naming a construction is not resolving the question.

    A caller who passes ``formulation="A2"`` has chosen one of the readings,
    which is exactly the act §33 reserves for the researcher. The block is on
    the fit, not on the arithmetic.
    """
    with pytest.raises(OpenItemError):
        fit_with_tier_indicator(CORE + NEAR, TIERS, formulation="A2")


def test_both_constructed_formulations_run_once_u2_is_resolved(
        restore_open_items):
    restore_open_items.resolve("U2", "A2", resolved_by="test",
                               resolved_on="2026-08-22")
    a2 = fit_with_tier_indicator(CORE + NEAR, TIERS)
    assert a2.formulation == "A2"
    assert a2.n_points == 12
    assert set(a2.intercepts) == {"MK1", "MK2", "MK3"}

    a4 = fit_with_tier_indicator(CORE + NEAR, TIERS, formulation="A4")
    assert a4.formulation == "A4"
    assert set(a4.intercepts) == {"common"}
    # The two estimate different things, which is the whole reason the
    # question is a researcher decision rather than a coding choice.
    assert a2.gamma != pytest.approx(a4.gamma, abs=1e-12) or \
        a2.slope != pytest.approx(a4.slope, abs=1e-12)


def test_a1_is_never_constructed(restore_open_items):
    """The singular reading is refused by name, not by a linear-algebra error.

    Building it and discovering the singularity at run time is what invites a
    pseudoinverse.
    """
    restore_open_items.resolve("U2", "A2", resolved_by="test",
                               resolved_on="2026-08-22")
    with pytest.raises(ProtocolError, match="not a constructed formulation"):
        fit_with_tier_indicator(CORE + NEAR, TIERS, formulation="A1")


def test_without_the_near_form_arm_gamma_is_not_identified():
    with pytest.raises(ProtocolError, match="does not vary"):
        fit_with_tier_indicator(CORE, {p.slot: 1 for p in CORE})


def test_a_excluded_from_the_fit_that_predicts_a():
    with pytest.raises(ProtocolError, match="must not enter"):
        fit_with_tier_indicator(
            CORE + NEAR + [SpectrumPoint(slot="A", family="A",
                                         difficulty=0.4, loss=0.5)],
            TIERS | {"A": 1})


# ------------------------- the evidence behind the U2 recommendation

def _designed(core_spans, near_form, *, beta=0.30, gamma=0.08,
              levels=(("R1", 0.10), ("R2", 0.16), ("R3", 0.22))):
    """Twelve noiseless points from a known model.

    Noiseless on purpose: the question is whether a formulation **recovers**
    the parameters it names, and noise would only blur an answer that is
    exact.
    """
    truth = dict(levels)
    points, tiers = [], {}
    for family, difficulties in core_spans.items():
        for index, difficulty in enumerate(difficulties):
            slot = (f"{family}-" if index == 0 else
                    family if index == 1 else f"{family}+")
            points.append(SpectrumPoint(
                slot=slot, family=family, difficulty=difficulty,
                loss=truth[family] + beta * difficulty))
            tiers[slot] = 1
    mean_alpha = sum(truth.values()) / len(truth)
    for index, difficulty in enumerate(near_form):
        slot = f"N{index + 1}"
        points.append(SpectrumPoint(
            slot=slot, family=f"NF{index + 1}", difficulty=difficulty,
            loss=mean_alpha + gamma + beta * difficulty))
        tiers[slot] = 2
    return points, tiers


#: Family level correlated with family difficulty. §13.8's caliper matches
#: each reference to **A**, not the references to each other, so nothing in
#: the protocol prevents this and it is the configuration to plan for.
_CORRELATED = {"R1": [0.20, 0.30, 0.40], "R2": [0.45, 0.55, 0.65],
               "R3": [0.70, 0.80, 0.90]}


def test_a2_recovers_the_slope_and_a4_absorbs_family_levels(
        restore_open_items):
    """U2's decisive comparison, computed rather than argued.

    A4 pools the intercepts, so between-family level differences have nowhere
    to go but the slope --- and `beta` means something different in the
    secondary than in the primary, which registers three family intercepts
    precisely to remove them.
    """
    open_items.resolve("U2", "A2", resolved_by="test", resolved_on="test")
    points, tiers = _designed(_CORRELATED, [0.40, 0.55, 0.70])
    a2 = fit_with_tier_indicator(points, tiers, formulation="A2")
    a4 = fit_with_tier_indicator(points, tiers, formulation="A4")
    assert a2.slope == pytest.approx(0.30, abs=1e-6)
    assert a2.gamma == pytest.approx(0.08, abs=1e-6)
    assert a4.slope == pytest.approx(0.4875, abs=1e-3)     # 63% inflated
    assert a4.gamma == pytest.approx(0.08, abs=1e-6)       # only here


def test_a4s_gamma_depends_on_where_the_near_form_points_happen_to_sit(
        restore_open_items):
    """The reason A2 is recommended, and it is not a matter of taste.

    Under A4 the Tier-2 offset is read against a pooled line whose slope is
    wrong, so it moves with the near-form controls' position in difficulty ---
    a quantity §13.9 selects on *closeness to A*, not on anything to do with
    the tier. Across three placements of the same three controls, generated
    from the same gamma = 0.08, A4 returns 0.024 to 0.134. A2 returns 0.08
    every time.
    """
    open_items.resolve("U2", "A2", resolved_by="test", resolved_on="test")
    placements = {"low": [0.20, 0.28, 0.36], "centre": [0.40, 0.55, 0.70],
                  "high": [0.75, 0.83, 0.90]}
    a2_gammas, a4_gammas = [], []
    for near_form in placements.values():
        points, tiers = _designed(_CORRELATED, near_form)
        a2_gammas.append(fit_with_tier_indicator(
            points, tiers, formulation="A2").gamma)
        a4_gammas.append(fit_with_tier_indicator(
            points, tiers, formulation="A4").gamma)
    assert all(g == pytest.approx(0.08, abs=1e-6) for g in a2_gammas)
    assert max(a4_gammas) / min(a4_gammas) > 5
    assert min(a4_gammas) < 0.08 < max(a4_gammas)
