"""§19 test 6, §17.5's fields, and §17.6's two disagreement tables."""
from __future__ import annotations

import pytest

from dci1v5.analysis import claims
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions

BASIS = C.MEASUREMENT_BASIS
SUPPORT = {"holds": True}


def _l3(**kwargs):
    defaults = dict(
        configuration=C.OUTCOME_FIRST, cell="pair:A+B", outcome_position=1,
        measurement_basis=BASIS,
        delta_r=claims.Interval("Delta_R", 0.30, 0.26, 0.34),
        delta_difficulty=claims.Interval("delta_difficulty", 0.20, 0.16,
                                         0.24),
        xi=claims.Interval("Xi", 0.20, 0.16, 0.24), support=SUPPORT,
        references_identified=True)
    defaults.update(kwargs)
    return claims.emit_l3(**defaults)


def test_no_l5_emitter():
    claims.assert_no_l5_emitter(vars(claims))
    with pytest.raises(claims.ClaimError):
        claims.assert_no_l5_emitter({"emit_l5": lambda: None})
    assert C.WITHHELD_CLAIM_LEVELS == ("L5",)


def test_every_statement_names_the_cell():
    """§17.5's field v4r4's reports needed and did not carry."""
    assert "cell" in claims.REQUIRED_FIELDS
    with pytest.raises(claims.ClaimError):
        claims.assert_statement_complete(
            {f: "x" for f in claims.REQUIRED_FIELDS if f != "cell"}
            | {"claim_level": "L1", "cell": ""})


def test_every_l3_statement_carries_reference_pool_same_form():
    statements = _l3()
    emitted = [s for s in statements if s["emitted"]]
    assert emitted
    for statement in emitted:
        assert "REFERENCE_POOL_SAME_FORM" in statement[
            "identification_status"]
        assert statement["reference_pool_sentence"] == \
            C.REFERENCE_POOL_SAME_FORM_SENTENCE


def test_l3b_needs_the_pair_specific_threshold():
    high = _l3(delta_r=claims.Interval("Delta_R", 0.40, 0.36, 0.44))
    assert {s["claim_level"] for s in high if s["emitted"]} >= {"L3a", "L3b"}
    mid = _l3(delta_r=claims.Interval("Delta_R", 0.18, 0.14, 0.22))
    levels = {s["claim_level"] for s in mid if s["emitted"]}
    assert "L3a" in levels and "L3b" not in levels


def test_local_and_spectrum_disagreement_emits_neither():
    out = _l3(delta_difficulty=claims.Interval("delta_difficulty", 0.00,
                                               -0.04, 0.04))
    assert not any(s["emitted"] for s in out)
    assert "LOCAL_AND_SPECTRUM_DISAGREE" in out[0]["identification_status"]


def test_local_tier_disagreement_emits_neither():
    """§17.6 table 2: Delta_R ~ 0 with Delta_near > 0.10 is not L3c."""
    out = _l3(delta_r=claims.Interval("Delta_R", 0.02, -0.01, 0.05),
              delta_difficulty=claims.Interval("delta_difficulty", 0.00,
                                               -0.04, 0.04),
              delta_near=claims.Interval("Delta_near", 0.30, 0.26, 0.34))
    assert not any(s["emitted"] for s in out)
    assert "LOCAL_TIER_DISAGREE" in out[0]["identification_status"]


def _l3c_without_arm():
    return _l3(delta_r=claims.Interval("Delta_R", 0.02, -0.01, 0.05),
               delta_difficulty=claims.Interval("delta_difficulty", 0.00,
                                                -0.04, 0.04),
               delta_near=None, near_form_available=False)


def test_an_l3c_with_no_near_form_arm_refuses_while_d18_is_open():
    """§34 D18 selects the behaviour, so the emitter may not choose one.

    This is the case the two modes differ on. Before this was wired the
    emitter attached §17.6's sentence unconditionally --- the standing
    proposal executing as a default, which is the exact shape §34 exists to
    stop.
    """
    with pytest.raises(decisions.DecisionOpenError):
        _l3c_without_arm()


def test_d18_mode_2_emits_l3c_with_the_narrower_interpretation(
        restore_decisions):
    restore_decisions.close("D18", "not_a_precondition", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    out = _l3c_without_arm()
    l3c = [s for s in out if s.get("claim_level") == "L3c" and s["emitted"]]
    assert l3c
    assert l3c[0]["d18_mode"] == "not_a_precondition"
    assert l3c[0]["near_form_absent_sentence"] == \
        C.L3C_WITHOUT_NEAR_FORM_SENTENCE
    assert "NEAR_FORM_ARM_NOT_AVAILABLE" in l3c[0]["identification_status"]


def test_d18_mode_1_withholds_l3c_and_says_why(restore_decisions):
    restore_decisions.close("D18", "precondition", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    out = _l3c_without_arm()
    assert not [s for s in out
                if s.get("claim_level") == "L3c" and s["emitted"]]
    withheld = [s for s in out if s.get("claim_level") == "L3c"]
    assert withheld and withheld[0]["emitted"] is False
    assert withheld[0]["d18_mode"] == "precondition"
    assert "NEAR_FORM_ARM_NOT_AVAILABLE" in withheld[0][
        "identification_status"]


def test_l3c_with_the_arm_present_does_not_consult_d18():
    """The decision is consulted only where the two modes differ."""
    disposition = claims.l3c_disposition(
        near_form_available=True,
        delta_near=claims.Interval("Delta_near", 0.20, 0.14, 0.26))
    assert disposition["emit"] is True
    assert disposition["consulted_d18"] is False


def test_whether_l3c_needs_the_near_form_arm_is_unresolved(restore_decisions):
    """§34 D18. The standing proposal is not a decision."""
    with pytest.raises(decisions.DecisionOpenError):
        claims.l3c_requires_near_form()
    restore_decisions.close("D18", "precondition", evidence="test",
                            decided_by="test", decided_on="2026-08-22")
    assert claims.l3c_requires_near_form() is True


def test_xi_gates_the_wording_and_not_the_emission():
    out = _l3(xi=claims.Interval("Xi", 0.00, -0.04, 0.04))
    emitted = [s for s in out if s["emitted"]]
    assert emitted
    assert "A_GENERAL_NOT_EXCLUDED" in emitted[0]["identification_status"]
    assert "not distinguishable" in emitted[0][
        "outcome_specificity_wording"]


def test_an_unidentified_reference_set_withholds_the_local_sublevels():
    """§13.15: Delta_R is not computed, and L3d still is --- it reads the fit.

    Dropping an identified estimand because an unidentified one is
    unavailable is not a rule this protocol contains (§8.1).
    """
    out = _l3(references_identified=False)
    levels = {s["claim_level"] for s in out if s["emitted"]}
    assert levels.isdisjoint({"L3a", "L3b", "L3c"})
    assert "L3d" in levels
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" in out[0][
        "identification_status"]


def test_l1_needs_solo_headroom_and_names_its_cell():
    interval = claims.Interval("D(B<-A)", 0.3, 0.2, 0.4)
    ok = claims.emit_l1(configuration=C.OUTCOME_FIRST, cell="pair:A+B",
                        outcome_position=1, measurement_basis=BASIS,
                        member="D(B<-A)", interval=interval,
                        solo_headroom=True)
    assert ok["emitted"] and ok["cell"] == "pair:A+B"
    no_headroom = claims.emit_l1(configuration=C.OUTCOME_FIRST,
                                 cell="pair:A+B", outcome_position=1,
                                 measurement_basis=BASIS, member="D(B<-A)",
                                 interval=interval, solo_headroom=False)
    assert not no_headroom["emitted"]


def test_position_confounded_attaches_in_the_shifted_configuration():
    interval = claims.Interval("D(B<-A)", 0.3, 0.2, 0.4)
    shifted = claims.emit_l1(configuration=C.OUTCOME_SECOND,
                             cell="pair:B+A", outcome_position=2,
                             measurement_basis=BASIS, member="D(B<-A)",
                             interval=interval, solo_headroom=True)
    assert "POSITION_CONFOUNDED" in shifted["identification_status"]


def test_the_scope_sentence_travels_with_every_statement():
    for statement in _l3():
        assert statement["scope_sentence"] == C.SCOPE_SENTENCE
