"""The registered library, §12's screen, and the decisions that block them."""
from __future__ import annotations

import pytest

from dci1v4.errors import ProtocolError
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.stages import regime
from dci1v5.verifiers import constraints as K


def test_the_registered_library_sizes():
    """§7.10's four counts, asserted rather than described."""
    assert K.assert_library_sizes() == {
        "families": 37, "round_0_severities": 326,
        "declared_severities": 632, "instruments": 650, "verifiers": 39}


def test_the_focal_grid_is_v5s_and_the_extension_is_conditional():
    assert K.FOCAL_GRID == (7, 8, 9, 10, 11, 12, 13, 14)
    assert K.FOCAL_EXTENSION == (15, 16)
    assert K.focal_severities() == K.FOCAL_GRID
    assert len(K.focal_severities(extended=True)) == 10


def test_m_starts_at_seven_because_however_has_seven_letters():
    assert min(K.FOCAL_GRID) == len(K.TARGET_WORD) == 7


def test_the_marker_vocabulary_meets_its_three_rules():
    K.assert_marker_vocabulary()
    for kind in K.TIER1_FAMILY_IDS:
        family = K.FAMILIES[kind]
        assert family.marker != K.TARGET_WORD
        assert len(family.marker) <= K.MARKER_MAX_LETTERS
        assert family.development_frequency_max <= \
            K.MARKER_NATURAL_FREQUENCY_MAX


def test_the_rejected_markers_carry_their_reason():
    for word in ("moreover", "likewise", "therefore", "conversely",
                 "nonetheless"):
        assert "letters" in K.REJECTED_MARKERS[word]
    assert "0.419" in K.REJECTED_MARKERS["also"]
    assert "0.185" in K.REJECTED_MARKERS["finally"]
    assert K.REJECTED_MARKERS["however"].startswith("A's own marker")


def test_the_measured_rule_admits_the_words_an_earlier_draft_rejected():
    """§7.6: `then`, `next`, `yet`, `still` are admissible and unregistered."""
    for word in ("yet", "still", "then", "next", "rather", "further"):
        assert "admissible" in K.REJECTED_MARKERS[word]


def test_the_tier_one_reserve_runs_to_twelve_on_a_measurement():
    for kind in K.TIER1_FAMILY_IDS:
        assert K.FAMILIES[kind].ladder == tuple(range(1, 9))
        assert K.FAMILIES[kind].reserve == tuple(range(1, 13))


def test_no_exact_or_rate_ladder_carries_zero():
    K.assert_no_zero_rung()
    for kind, family in K.FAMILIES.items():
        if family.form in (K.FORM_EXACT, K.FORM_RATE):
            assert 0 not in family.reserve


def test_rate_lower_bound_is_in_the_grammar_and_instantiated_by_nothing():
    assert K.FORM_RATE_LOWER_BOUND in K.FORMS
    assert not any(f.form == K.FORM_RATE_LOWER_BOUND
                   for f in K.FAMILIES.values())


def test_the_marker_vocabulary_needs_d4_before_it_is_approved(
        restore_decisions):
    with pytest.raises(decisions.DecisionOpenError):
        K.assert_marker_vocabulary_approved()
    restore_decisions.close("D4", "approve_eight", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    assert len(K.assert_marker_vocabulary_approved()) == 8


def test_rule_two_carries_every_tier12_rung_unconditionally():
    """§12.2: no candidate is discarded on a pre-screen point estimate."""
    verdict = regime.carry_candidate(
        kind="MK1", severity=8, prescreen_solo_compliance=0.0,
        n_prescreen_topics=24, structural=regime.StructuralScreen())
    assert verdict["carried"] and verdict["rule"] == 2


def test_rule_one_reads_an_interval_and_the_structural_screen():
    kept = regime.carry_candidate(
        kind="RF1", severity=4, prescreen_solo_compliance=0.5,
        n_prescreen_topics=24, structural=regime.StructuralScreen())
    assert kept["carried"] and kept["rule"] == 1
    dropped = regime.carry_candidate(
        kind="RF1", severity=4, prescreen_solo_compliance=0.999,
        n_prescreen_topics=4000, structural=regime.StructuralScreen())
    assert not dropped["carried"]
    structural = regime.carry_candidate(
        kind="RF1", severity=4, prescreen_solo_compliance=0.5,
        n_prescreen_topics=24,
        structural=regime.StructuralScreen(realistic_witness=False))
    assert not structural["carried"]
    assert "realistic_witness" in structural["reason"]


def test_no_prescreen_distance_caliper_exists():
    """v4r4 §13.4 condition 2 is deleted (§12.2)."""
    assert not hasattr(C, "REFERENCE_PRESCREEN_CALIPER")


def test_the_prescreen_estimate_decides_only_the_tier3_measurement_budget():
    carried = ([{"candidate": f"MK1:{q}", "family": "MK1",
                 "structural_tier": 1, "prescreen_iota": 0.9} for q in
                range(1, 9)]
               + [{"candidate": f"RF1:{q}", "family": "RF1",
                   "structural_tier": 3, "prescreen_iota": 0.1 * q}
                  for q in range(1, 31)])
    plan = regime.calibration_priority(carried, iota_a_prescreen=0.7)
    assert len(plan["tier12"]) == 8
    assert len(plan["tier3_measured"]) == C.CALIBRATION_TIER3_CAP
    assert plan["tier3_dropped_for_budget"]
    assert "never which candidates are admitted" in plan["note"]


def test_the_bracketing_rule_and_the_grid_boundary_status():
    curve = {m: v for m, v in zip(range(7, 15),
                                  [0.03, 0.11, 0.25, 0.41, 0.66, 0.74, 0.80,
                                   0.85])}
    selected = regime.select_focal(curve)
    assert selected["selected"] == 13 and selected["bracketed"]
    partial = {m: curve[m] for m in range(7, 13)}
    boundary = regime.select_focal(partial)
    assert boundary["identification_statuses"] == [
        "OPERATING_POINT_AT_GRID_BOUNDARY"]


def test_the_extension_is_measured_only_on_escalation():
    top = {m: 0.10 * (m - 6) for m in range(7, 15)}
    top[14] = 0.80
    result = regime.select_focal(top)
    assert result["selected"] == 14
    assert result.get("extension_required") is True
    with_extension = regime.select_focal(top, {15: 0.88, 16: 0.93})
    assert with_extension["extension_measured"] is True


def test_focal_range_exhausted_when_no_severity_is_eligible():
    flat = {m: 0.02 for m in range(7, 15)}
    result = regime.select_focal(flat, {15: 0.03, 16: 0.04})
    assert result["selected"] is None
    assert result["terminal_status"] == "FOCAL_RANGE_EXHAUSTED"


def test_n_star_at_one_is_a_construct_floor_not_a_model_failure():
    curve = {1: 0.72, 2: 0.55, 3: 0.40, 4: 0.30, 5: 0.2, 6: 0.15, 7: 0.1,
             8: 0.05}
    result = regime.select_target(curve)
    assert result["selected"] == 1
    assert "floor of A's construct" in result["reason"]


def test_the_construct_floor_is_a_researcher_decision(restore_decisions):
    with pytest.raises(decisions.DecisionOpenError):
        regime.assert_construct_floor(13, chance_compliance_at_m_star=0.3)
    restore_decisions.close("D17", "no_floor", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    out = regime.assert_construct_floor(13, chance_compliance_at_m_star=0.3)
    assert out["floor_registered"] is False
    restore_decisions.reopen_all_for_testing()
    restore_decisions.close("D17", "floor", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    with pytest.raises(ProtocolError) as excinfo:
        regime.assert_construct_floor(13, chance_compliance_at_m_star=0.3)
    assert "does not invent one" in str(excinfo.value)


def test_the_coverage_criterion_separates_decisive_from_arm_dropping():
    assert C.COVERAGE_DECISIVE == ("C1", "C2", "C3", "C4", "C5", "C6")
    table = [{"candidate": "x", "family": "MK1", "structural_tier": 1,
              "feature_group": "marker_thus", "constraint_class": "production",
              "iota": 0.5, "eligible": True}]
    out = regime.coverage_criterion(table, iota_a=0.7)
    assert out["decisive_met"] is False
    assert set(out["identification_statuses"]) == {
        "CLASS_ARM_NOT_AVAILABLE", "NEAR_FORM_ARM_NOT_AVAILABLE"}


def test_expansion_extends_toward_the_deficient_side():
    """Higher q is HARDER for an exact count, so easier means lower q."""
    # every measured rung is harder than A: the expansion must go EASIER.
    table = [{"family": "MK1", "severity": q, "iota": 0.40 - 0.04 * q,
              "candidate": f"MK1:{q}"} for q in range(4, 9)]
    plan = regime.expansion_round(table, iota_a=0.60,
                                  measured={"MK1": list(range(4, 9))})
    picks = plan["admitted"]["MK1"]
    assert set(picks) <= set(K.RESERVES["MK1"])
    assert max(picks) < 4
    assert len(picks) <= C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND

    # every measured rung is easier than A: the expansion must go HARDER, and
    # §7.10's reserve to 12 is what it reaches into.
    easier = [{"family": "MK1", "severity": q, "iota": 0.95 - 0.02 * q,
               "candidate": f"MK1:{q}"} for q in range(1, 9)]
    harder = regime.expansion_round(easier, iota_a=0.50,
                                    measured={"MK1": list(range(1, 9))})
    assert set(harder["admitted"]["MK1"]) <= {9, 10, 11, 12}


def test_expansion_never_authors_outside_the_frozen_reserve():
    table = [{"family": "RF1", "severity": q, "iota": 0.20 + 0.05 * q,
              "candidate": f"RF1:{q}"} for q in range(0, 9)]
    plan = regime.expansion_round(table, iota_a=0.90,
                                  measured={"RF1": list(range(0, 9))})
    assert set(plan["admitted"].get("RF1", ())) <= set(K.RESERVES["RF1"])


def test_the_calibration_b_bank_does_not_exist(restore_decisions):
    from dci1v5 import topics

    assert topics.CALIBRATION_B_STATUS == "NOT_AUTHORED"
    with pytest.raises(decisions.DecisionOpenError):
        topics.calibration_b_bank()
    restore_decisions.close("D3", "author_before_adoption", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    with pytest.raises(ProtocolError) as excinfo:
        topics.calibration_b_bank()
    assert "96 newly authored questions" in str(excinfo.value)


def test_the_topic_bank_shape_is_720_in_six_sets():
    from dci1v5 import topics

    assert sum(topics.SET_SIZES.values()) == 720
    assert topics.SET_SIZES[C.CALIBRATION_A] == 96
    assert topics.SET_SIZES[C.CALIBRATION_B] == 96
    with pytest.raises(ProtocolError):
        topics.assert_bank_shape({s: [] for s in C.TOPIC_SETS})
