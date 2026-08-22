"""§11.8's secondary fit: not identified as written, and not repaired here."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.analysis.spectrum import SpectrumPoint, fit_with_tier_indicator
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
