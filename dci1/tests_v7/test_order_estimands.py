"""I. §11.7's order contrasts: paired, both algebraic forms, F11."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.analysis import estimators as E
from dci1v7.protocol import constants as C
from tests_v7.conftest import observation_table

ARMS = ["core", "spectrum", "nearform", "class"]


def _table(**rates):
    return observation_table(ARMS, blocks=16, m_draws=4,
                             rates=rates.pop("rates", None), **rates)


def test_f11_has_the_five_registered_members():
    assert C.FAMILY_MEMBERS["F11"] == ("Ord_A", "Ord_B", "Ord_Lambda",
                                       "Ord_Rbar", "Ord_CL")
    assert E.ORDER_CONTRASTS == C.FAMILY_MEMBERS["F11"]
    assert "F11" in C.PRIMARY_TIER_FAMILIES
    assert "F11" in C.CROSS_CONFIGURATION_FAMILIES


def test_f1s_membership_is_unchanged_from_v4r4():
    """Registering three new arms widens no interval that carries an L1."""
    assert C.FAMILY_MEMBERS["F1"] == ("D(B<-A)", "D(A<-B)", "Lambda",
                                      "Delta_R", "delta_difficulty", "Xi")


def test_both_algebraic_forms_agree_to_one_part_in_a_billion():
    table = observation_table(ARMS, blocks=16)
    worst = E.assert_order_forms(table)
    assert set(worst) >= {"Ord_A", "Ord_B", "Ord_Lambda"}
    assert max(worst.values()) <= C.ALGEBRAIC_FORM_TOLERANCE


def test_ord_lambda_is_exactly_ord_b_minus_ord_a():
    table = observation_table(ARMS, blocks=16)
    a = E.ord_a(table)
    b = E.ord_b(table)
    lam = E.ord_lambda(table)
    for x, y, z in zip(a, b, lam):
        assert z == pytest.approx(y - x, abs=1e-12)


def test_an_installed_order_effect_is_recovered():
    """A known cross-configuration difference reads back out of Ord_A."""
    rates = {("A", "B", C.OUTCOME_FIRST): 0.90,
             ("A", "B", C.OUTCOME_SECOND): 0.30}
    table = observation_table(ARMS, blocks=64, m_draws=4, rates=rates,
                              seed=17)
    ord_a = E.ord_a(table)
    mean = sum(ord_a) / len(ord_a)
    # Ord_A = composed(A second) - composed(A first) = 0.30 - 0.90
    assert mean == pytest.approx(-0.60, abs=0.06)


def test_the_solo_baseline_cancels():
    """Each Ord is a contrast between two composed cells."""
    table = observation_table(ARMS, blocks=16)
    definitional = [
        f - s for f, s in zip(
            E.delivery_loss(table, "A", "B", C.OUTCOME_FIRST),
            E.delivery_loss(table, "A", "B", C.OUTCOME_SECOND))]
    for x, y in zip(E.ord_a(table), definitional):
        assert x == pytest.approx(y, abs=1e-12)


def test_an_unregistered_order_comparison_is_refused():
    table = observation_table(ARMS, blocks=8)
    with pytest.raises(ProtocolError):
        E.order_contrast(table, "Ord_N1")


def test_ord_cl_needs_the_class_arm():
    table = observation_table(["core"], blocks=8)
    with pytest.raises(ProtocolError):
        E.ord_cl(table)


def test_ord_rbar_needs_three_core_references():
    table = observation_table(["class"], blocks=8)
    with pytest.raises(ProtocolError):
        E.ord_rbar(table)


def test_a_linear_arm_companion_never_enters_a_core_estimand():
    table = observation_table(ARMS, blocks=8)
    assert set(E.reference_slots(table)) == set(C.CORE_SLOTS)
    for slot in C.NEAR_FORM_SLOTS + (C.CLASS_SLOT,) + C.SPECTRUM_SLOTS:
        with pytest.raises(ProtocolError):
            E.assert_core_only([slot], where="Delta_R")


def test_delta_r_forms_agree_and_delta_near_needs_its_arm():
    table = observation_table(ARMS, blocks=16)
    E.assert_delta_r_forms(table, C.OUTCOME_FIRST)
    assert len(E.delta_near(table, C.OUTCOME_FIRST)) == 16
    without = observation_table(["core", "class"], blocks=8)
    with pytest.raises(ProtocolError):
        E.delta_near(without, C.OUTCOME_FIRST)
    with pytest.raises(ProtocolError):
        E.delta_broad(observation_table(["core"], blocks=8),
                      C.OUTCOME_FIRST)


def test_kappa_under_b_is_not_defined_for_b_itself():
    table = observation_table(ARMS, blocks=8)
    with pytest.raises(ProtocolError):
        E.counterfactual_chance(table, "B")


def test_every_estimator_returns_one_value_per_block():
    table = observation_table(ARMS, blocks=12)
    for vector in (E.ord_a(table), E.ord_b(table), E.ord_lambda(table),
                   E.ord_rbar(table), E.ord_cl(table),
                   E.delta_r(table, C.OUTCOME_FIRST),
                   E.delta_near(table, C.OUTCOME_FIRST),
                   E.delta_broad(table, C.OUTCOME_FIRST),
                   E.xi(table, C.OUTCOME_FIRST)):
        assert len(vector) == 12
