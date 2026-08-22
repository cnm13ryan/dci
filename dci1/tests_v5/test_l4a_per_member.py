"""J. §19 test 1: the three registered L4a regression tests (§17.7).

The first reconstructs v4r4's `gemma-3n-e4b-it` pattern from its signed
records --- ``D(A<-B)`` reaching L1 in ``outcome_first`` only and ``D(B<-A)``
in ``outcome_second`` only --- and asserts that L4a is **not** emitted for it.
v4r4's emitter compared the SETS of levels reached, the sets matched, and the
emitted L4 asserted replication for the replication that least replicates.
"""
from __future__ import annotations

import inspect

import pytest

from dci1v5.analysis import claims
from dci1v5.protocol import constants as C

BASIS = C.MEASUREMENT_BASIS

#: v4r4's `gemma-3n-e4b-it`, reconstructed from its claim table.
E4B_PATTERN = {
    "D(A<-B)": {C.OUTCOME_FIRST: "L1", C.OUTCOME_SECOND: None},
    "D(B<-A)": {C.OUTCOME_FIRST: None, C.OUTCOME_SECOND: "L1"},
}
#: v4r4's `qwen3-4b`: the same named member at L1 in both.
QWEN_PATTERN = {
    "D(A<-B)": {C.OUTCOME_FIRST: "L1", C.OUTCOME_SECOND: "L1"},
    "D(B<-A)": {C.OUTCOME_FIRST: None, C.OUTCOME_SECOND: None},
}


def test_v4r4s_e4b_swap_pattern_does_not_emit_replication():
    result = claims.emit_l4a(per_member=E4B_PATTERN, measurement_basis=BASIS)
    assert result["emitted"] is False
    assert result["differing_members"] == ["D(A<-B)", "D(B<-A)"]
    assert result["registered_reading"] == "Configuration dependence (§28.1)"
    assert "per member" in result["reason"]


def test_v4r4s_qwen_pattern_emits():
    result = claims.emit_l4a(per_member=QWEN_PATTERN, measurement_basis=BASIS)
    assert result["emitted"] is True
    assert result["stable_classifications"]["D(A<-B)"] == "L1"


def test_an_l4_emitter_cannot_be_called_with_a_bare_level_sequence():
    """The shape that produced v4r4's defect is not callable."""
    signature = inspect.signature(claims.emit_l4a)
    parameter = signature.parameters["per_member"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(claims.ClaimError):
        claims.emit_l4a(per_member={"D(A<-B)": ["L1"]},
                        measurement_basis=BASIS)
    with pytest.raises(TypeError):
        claims.emit_l4a({"D(A<-B)": {C.OUTCOME_FIRST: "L1"}}, BASIS)


def test_the_old_level_set_emitter_does_not_exist():
    assert not hasattr(claims, "emit_l4")


def test_a_member_not_registered_to_l4a_is_refused():
    with pytest.raises(claims.ClaimError):
        claims.emit_l4a(per_member={"Ord_A": {C.OUTCOME_FIRST: "L4b"}},
                        measurement_basis=BASIS)


def test_an_incomplete_configuration_set_does_not_emit():
    result = claims.emit_l4a(
        per_member={"Lambda": {C.OUTCOME_FIRST: "L2"}},
        measurement_basis=BASIS)
    assert result["emitted"] is False
    assert "not every registered configuration" in result["reason"]


def test_no_member_reaching_a_level_does_not_emit():
    result = claims.emit_l4a(
        per_member={"Xi": {C.OUTCOME_FIRST: None, C.OUTCOME_SECOND: None}},
        measurement_basis=BASIS)
    assert result["emitted"] is False


def test_l4b_reads_f11_and_never_says_order_invariance():
    tight = claims.Interval("Ord_A", 0.15, 0.11, 0.19)
    emitted = claims.emit_l4b(member="Ord_A", interval=tight,
                              measurement_basis=BASIS,
                              both_configurations_analysed=True)
    assert emitted["emitted"] is True
    assert emitted["family"] == "F11"

    spanning = claims.Interval("Ord_A", 0.01, -0.03, 0.05)
    quiet = claims.emit_l4b(member="Ord_A", interval=spanning,
                            measurement_basis=BASIS,
                            both_configurations_analysed=True)
    assert quiet["emitted"] is False
    assert "NOT order-invariance" in quiet["reason"]


def test_l4b_refuses_an_unregistered_member():
    with pytest.raises(claims.ClaimError):
        claims.emit_l4b(member="Ord_N1",
                        interval=claims.Interval("Ord_N1", 0.1, 0.05, 0.15),
                        measurement_basis=BASIS,
                        both_configurations_analysed=True)


def test_l4a_and_l4b_are_complementary():
    """Neither implies the other; both are reported."""
    assert set(claims.LEVEL_MEMBERS["L4a"]) & \
        set(claims.LEVEL_MEMBERS["L4b"]) == set()
