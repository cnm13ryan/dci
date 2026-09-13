"""v7 §13.14: what a composed rate at 0 or 1 does to a contrast, executed.

Three readings, none of them a gate: a structural zero, an arm at an exact
boundary with its Wilson allowance, and a direction compressed below the
SESOI by the other arm's level. Every threshold the rule reads is the
registered SESOI or §14.1's block count; nothing here is a new number.
"""
from __future__ import annotations

import pytest
from dci1v4.errors import ProtocolError
from dci1v7.analysis import boundary as B
from dci1v7.analysis import claims, estimators
from dci1v7.analysis.intervals import wilson
from dci1v7.protocol import constants as C
from dci1v7.stages import composed_contrast as CC

from tests_v7.conftest import observation_table

N = 40


def _vec(level: float, n: int = N) -> list[float]:
    return [level] * n


# ---------------------------------------------------------- compositions

def test_every_projectable_member_has_a_composition_the_estimator_agrees_with():
    """The boundary reading is a reading of the SAME linear combination the
    estimator computes, to 1e-12, on a synthetic table with every arm."""
    arms = ("base", "core", "spectrum", "nearform", "class")
    table = observation_table(arms, blocks=10, m_draws=4, seed=3)
    members = ["D(B<-A)", "D(A<-B)", "Lambda", "Delta_R", "Delta_1",
               "Delta_2", "Delta_3", "Delta_near", "Delta_broad", "Delta^A",
               "D(B<-R1)", "D(R2<-A)", "D(B<-N1)", "D(B<-CL)",
               "Ord_A", "Ord_B", "Ord_Lambda", "Ord_Rbar", "Ord_CL"]
    for member in members:
        cfg = None if member.startswith("Ord") else C.OUTCOME_FIRST
        parts = B.composition(member)
        assert parts is not None, member
        derived = [0.0] * len(table.blocks)
        for part in parts:
            c = part.configuration or cfg
            vector = (estimators.solo_vector(table, part.outcome)
                      if part.role == "solo" else
                      estimators.composed_vector(table, part.outcome,
                                                 part.companion, c))
            derived = [a + part.weight * b for a, b in zip(derived, vector)]
        truth = CC.member_vector(table, member, cfg)
        assert truth is not None, member
        assert max(abs(a - b) for a, b in zip(derived, truth)) < 1e-12, member


def test_members_without_a_linear_composition_say_so():
    assert B.composition("delta_difficulty") is None
    assert B.composition("Xi") is None
    assert B.composition("beta") is None
    assert B.composition("D(Rbar<-A)") is not None   # a loss with a mean slot
    assert B.composition("Delta_R")[0].weight == pytest.approx(1 / 3)
    assert sum(p.weight for p in B.composition("Delta_R")) == pytest.approx(0)


# ------------------------------------------------------------- cells

def test_a_cell_is_at_an_exact_boundary_only_when_every_block_is():
    assert B.classify_cell(_vec(1.0))["exact_boundary"] == "ceiling"
    assert B.classify_cell(_vec(0.0))["exact_boundary"] == "floor"
    nearly = _vec(1.0)
    nearly[0] = 0.75
    cls = B.classify_cell(nearly)
    assert cls["exact_boundary"] is None
    assert cls["near_boundary"] == "ceiling"     # descriptive only
    assert B.classify_cell(_vec(0.5))["near_boundary"] is None
    with pytest.raises(ProtocolError):
        B.classify_cell([])


def test_the_boundary_allowance_is_the_wilson_halfwidth_at_the_block_count():
    for n in (24, 96, 384):
        assert B.boundary_halfwidth(n) == pytest.approx(
            1.0 - wilson(1.0, n)[0])
        assert B.boundary_halfwidth(n) == pytest.approx(wilson(0.0, n)[1])
    assert B.boundary_halfwidth(C.N_BLOCKS) < 0.010
    assert B.boundary_halfwidth(C.N_COMPOSED) > 0.10
    with pytest.raises(ProtocolError):
        B.boundary_halfwidth(384, level=0.90)


# --------------------------------------------------------------- contrasts

def _delta_r(a_level, r_levels):
    parts = B.composition("Delta_R")
    vectors = []
    for part in parts:
        if part.companion == "A":
            vectors.append((part, a_level))
        else:
            vectors.append((part, r_levels[part.companion]))
    return B.contrast_boundary("Delta_R", vectors,
                               configuration=C.OUTCOME_FIRST)


def test_an_interior_contrast_carries_no_status():
    out = _delta_r(_vec(0.6), {"R1": _vec(0.7), "R2": _vec(0.65),
                               "R3": _vec(0.72)})
    assert out["statuses"] == []
    assert out["allowance_lower"] == out["allowance_upper"] == 0.0
    assert not out["structural_zero"]
    assert out["compression"]["two_arm"] is True
    assert not out["compression"]["positive_direction_compressed"]


def test_a_ceiling_on_the_a_arm_widens_upward_and_compresses_the_excess():
    """The v6 Qwen case taken to the limit: B delivered under A everywhere.
    Delta_R = r - 1 is real, negative and estimable; what a ceiling costs is
    the bootstrap's view of the A arm's uncertainty (widened upward by the
    allowance) and the possibility of an excess (compressed)."""
    out = _delta_r(_vec(1.0), {"R1": _vec(0.7), "R2": _vec(0.6),
                               "R3": _vec(0.65)})
    assert not out["structural_zero"]
    assert out["any_arm_at_boundary"]
    assert out["allowance_upper"] == pytest.approx(B.boundary_halfwidth(N))
    assert out["allowance_lower"] == 0.0
    assert out["compression"]["positive_direction_compressed"]
    assert not out["compression"]["negative_direction_compressed"]
    assert [e["arm"] for e in out["compression"]["compressed_by"]] == [
        "negative_arm"]
    assert set(out["statuses"]) == {B.ARM_AT_BOUNDARY, B.RANGE_COMPRESSED}
    assert out["terminates"] is False


def test_a_ceiling_on_one_reference_widens_by_its_weight_only():
    out = _delta_r(_vec(0.6), {"R1": _vec(1.0), "R2": _vec(0.65),
                               "R3": _vec(0.7)})
    assert out["allowance_lower"] == pytest.approx(B.boundary_halfwidth(N) / 3)
    assert out["allowance_upper"] == 0.0
    assert not out["structural_zero"]
    assert out["statuses"] == [B.ARM_AT_BOUNDARY]


def test_a_common_boundary_is_a_structural_zero_read_on_its_allowance():
    """v7 §13.14 as revised 2026-08-28 (V10): the decision interval at a
    shared exact boundary is +/- the Wilson half-width at the block count,
    no direction is reachable, and the equivalence reading follows the
    registered rule on that interval --- L3c at 384 blocks, nothing at 24."""
    for n, expected in ((C.N_BLOCKS, ["L3c"]), (24, [])):
        out = _delta_r(_vec(1.0, n), {"R1": _vec(1.0, n), "R2": _vec(1.0, n),
                                      "R3": _vec(1.0, n)})
        assert out["structural_zero"] and out["structural_zero_boundary"] == \
            "ceiling"
        assert B.STRUCTURAL_ZERO in out["statuses"]
        lower, upper = B.apply_allowance(0.0, 0.0, out)
        half = B.boundary_halfwidth(n)
        assert lower == pytest.approx(-half) and upper == pytest.approx(half)
        interval = claims.Interval("Delta_R", 0.0, lower, upper, boundary=out)
        reading = claims.delta_r_reading(interval)
        assert reading["levels"] == expected, n
        assert "STRUCTURAL_ZERO" in reading["markers"]
        assert reading["direction"]["direction"] == "DIRECTION_UNRESOLVED"
        assert not reading["direction_resolved"]
        if n == 24:
            assert "INSUFFICIENT_PRECISION" in reading["markers"]
    # The same floor: a shared floor is read exactly like a shared ceiling.
    n = C.N_BLOCKS
    out = _delta_r(_vec(0.0, n), {"R1": _vec(0.0, n), "R2": _vec(0.0, n),
                                  "R3": _vec(0.0, n)})
    assert out["structural_zero_boundary"] == "floor"
    lower, upper = B.apply_allowance(0.0, 0.0, out)
    assert lower == pytest.approx(-B.boundary_halfwidth(n))
    assert claims.delta_r_reading(claims.Interval(
        "Delta_R", 0.0, lower, upper, boundary=out))["levels"] == ["L3c"]
    # Mixed boundaries are not a structural zero: floor on one arm and
    # ceiling on the other is the largest contrast there is.
    mixed = _delta_r(_vec(0.0), {"R1": _vec(1.0), "R2": _vec(1.0),
                                 "R3": _vec(1.0)})
    assert not mixed["structural_zero"]
    assert mixed["compression"]["positive_arm"] == 1.0
    assert mixed["compression"]["negative_arm"] == 0.0


def test_compression_reads_the_sesoi_and_nothing_else():
    top = C.CONTRAST_COMPRESSION_LEVEL
    assert top == pytest.approx(1.0 - C.SMALLEST_EFFECT_OF_INTEREST)
    just_under = _delta_r(_vec(top - 0.01), {"R1": _vec(0.5), "R2": _vec(0.5),
                                             "R3": _vec(0.5)})
    just_over = _delta_r(_vec(top + 0.01), {"R1": _vec(0.5), "R2": _vec(0.5),
                                            "R3": _vec(0.5)})
    assert not just_under["compression"]["positive_direction_compressed"]
    assert just_over["compression"]["positive_direction_compressed"]
    # A reference arm near the ceiling compresses the OTHER direction.
    refs_high = _delta_r(_vec(0.5), {"R1": _vec(0.95), "R2": _vec(0.95),
                                     "R3": _vec(0.95)})
    assert refs_high["compression"]["negative_direction_compressed"]
    assert not refs_high["compression"]["positive_direction_compressed"]


def test_lambda_is_not_a_two_arm_contrast_and_carries_no_compression():
    parts = B.composition("Lambda")
    out = B.contrast_boundary("Lambda", [(p, _vec(0.6)) for p in parts],
                              configuration=C.OUTCOME_FIRST)
    assert out["compression"]["two_arm"] is False
    assert B.RANGE_COMPRESSED not in out["statuses"]


def test_unequal_block_lengths_are_refused():
    parts = B.composition("D(B<-A)")
    with pytest.raises(ProtocolError, match="unequal"):
        B.contrast_boundary("D(B<-A)", [(parts[0], _vec(0.5, 10)),
                                        (parts[1], _vec(0.5, 11))],
                            configuration=C.OUTCOME_FIRST)


def test_apply_allowance_widens_only_the_open_side():
    reading = {"allowance_lower": 0.0, "allowance_upper": 0.02}
    assert B.apply_allowance(-0.3, -0.1, reading) == (-0.3, -0.08)
    assert B.apply_allowance(-0.3, -0.1, None) == (-0.3, -0.1)


def test_the_projected_precision_recombines_section_16_1s_components():
    parts = B.composition("D(B<-A)")
    solo = [0.6 + 0.02 * (i % 5) for i in range(N)]
    composed = [0.4 + 0.02 * (i % 3) for i in range(N)]
    contrast = [s - c for s, c in zip(solo, composed)]
    out = B.projected_confirmatory_halfwidth(
        contrast, [(parts[0], solo), (parts[1], composed)],
        m_measured=4, family_size=6)
    assert out["projected"] and out["t_target"] == C.N_BLOCKS
    assert out["m_target"] == C.M_DRAWS
    assert out["s2_draw"] > 0 and out["s2_topic"] >= 0
    assert out["half_width"] > 0
    assert out["label"] == "PROJECTION_NOT_REGISTERED_FOR_INFERENCE"
    assert B.projected_confirmatory_halfwidth(
        [0.1], [(parts[0], [0.5])], m_measured=4, family_size=6)[
        "projected"] is False
