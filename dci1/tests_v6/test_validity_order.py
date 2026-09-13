"""D. V(R): components, lexicographic reason, order-independent verdict.

§19 test 3 registers the second of those by name: *V(R) is evaluated
lexicographically and the recorded rejection reason is the **earliest**
failing component.*
"""
from __future__ import annotations

import itertools

import pytest

from dci1v4.errors import ProtocolError
from dci1v6.protocol import constants as C
from dci1v6.stages import validity as V
from tests_v6.conftest import calibration_row


def _row(**kwargs):
    return calibration_row("MK1", 3, solo=0.70, **kwargs)


def _evaluate(row, **kwargs):
    return V.evaluate_validity(row, slot="core_reference", iota_a=0.69,
                               solo_compliance_a=0.69,
                               stability={"passed": True}, **kwargs)


def test_the_eight_components_are_the_registered_ones_in_order():
    assert V.VALIDITY_COMPONENTS == ("V_spec", "V_sat", "V_head", "V_chance",
                                     "V_struct", "V_inter", "V_stab",
                                     "V_diff")
    assert C.VALIDITY_COMPONENTS == V.VALIDITY_COMPONENTS


def test_iota_is_evaluated_last():
    """§13.3: V_diff is the last component, and that is the central change."""
    assert V.VALIDITY_COMPONENTS[-1] == "V_diff"


def test_a_valid_candidate_passes_every_component():
    verdict = _evaluate(_row())
    assert verdict.passed
    assert verdict.first_failing_component is None
    assert verdict.reason is None


def test_v4r4s_admitted_rung_fails_on_raw_headroom_first():
    """The rung at solo 0.9740 / chance 0.9323 that terminated a replication.

    v4r4 admitted it *because its iota was the closest available*. Under v5 it
    fails V_head --- raw headroom --- before the difficulty caliper is
    reached, which is what demoting iota buys.
    """
    row = calibration_row("RF11", 26, solo=0.9740, chance=0.9323,
                          kappa_b=0.83)
    verdict = V.evaluate_validity(row, slot="core_reference", iota_a=0.62,
                                  solo_compliance_a=0.62,
                                  stability={"passed": True})
    assert not verdict.passed
    assert verdict.first_failing_component == "V_head"
    V.assert_lexicographic_order(verdict)


def test_the_recorded_reason_is_the_earliest_failing_component():
    row = calibration_row("MK1", 3, solo=0.98, chance=0.90, kappa_b=0.95,
                          vacuity=0.5, witnesses_pass=False)
    verdict = _evaluate(row)
    assert verdict.first_failing_component == "V_sat"
    assert len(verdict.failing_components) > 1
    V.assert_lexicographic_order(verdict)


def test_the_conjunction_does_not_depend_on_evaluation_order():
    """§13.1: the order decides the REASON, never the verdict."""
    row = calibration_row("MK1", 3, solo=0.98, chance=0.90, kappa_b=0.95)
    verdict = _evaluate(row)
    for permutation in itertools.islice(
            itertools.permutations(V.VALIDITY_COMPONENTS), 12):
        shuffled = V.evaluate_validity(
            row, slot="core_reference", iota_a=0.69, solo_compliance_a=0.69,
            stability={"passed": True}, components=permutation)
        assert shuffled.passed == verdict.passed
        # ...and the RECORDED order is still the registered one.
        assert [c.name for c in shuffled.components] == \
            list(V.VALIDITY_COMPONENTS)


def test_an_unevaluated_component_is_never_a_pass():
    verdict = V.evaluate_validity(_row(), slot="core_reference",
                                 components=V.GATE_2_5_COMPONENTS)
    assert not verdict.passed
    assert set(verdict.unevaluated_names) == {"V_stab", "V_diff"}
    assert "not established" in verdict.reason


def test_a_missing_kappa_under_b_fails_and_is_not_skipped():
    """§13.6: absence is never read as a pass."""
    row = calibration_row("MK1", 3, solo=0.70, kappa_b=None)
    verdict = _evaluate(row)
    assert not verdict.passed
    assert verdict.first_failing_component == "V_inter"
    assert "never read as a pass" in verdict.reason


def test_headroom_reads_the_interval_not_the_point():
    """§13.4: the band is applied to the Wilson interval, not the estimate."""
    tight = calibration_row("MK1", 3, solo=0.85, n_topics=192)
    loose = calibration_row("MK1", 3, solo=0.85, n_topics=12)
    assert _evaluate(tight).value("V_head", "wilson_upper") < 0.90
    assert _evaluate(loose).value("V_head", "wilson_upper") > 0.90
    assert _evaluate(loose).first_failing_component == "V_head"


def test_the_lift_floor_and_the_chance_ceiling_are_the_registered_values():
    assert C.INSTRUCTION_LIFT_MIN == 0.20
    assert C.CHANCE_MAX == 0.75
    assert C.CHANCE_WILSON_UPPER_MAX == 0.85
    low_lift = calibration_row("MK1", 3, solo=0.30, chance=0.15)
    verdict = V.evaluate_validity(low_lift, slot="core_reference",
                                  iota_a=0.18, solo_compliance_a=0.30,
                                  stability={"passed": True})
    assert verdict.first_failing_component == "V_head"
    assert "instruction lift" in verdict.reason


def test_chance_degeneracy_is_not_the_admission_threshold():
    """v4r4's 0.99 stays, and decides nothing about admission."""
    assert C.CHANCE_DEGENERACY_MAX == 0.99
    assert C.CHANCE_MAX < C.CHANCE_DEGENERACY_MAX


def test_no_weighted_composite_score_exists():
    V.assert_no_composite_score(vars(V))
    with pytest.raises(ProtocolError):
        V.assert_no_composite_score({"validity_score": lambda: None})


def test_unknown_component_names_are_refused():
    with pytest.raises(ProtocolError):
        V.evaluate_validity(_row(), slot="core_reference",
                            components=("V_spec", "V_wibble"))
