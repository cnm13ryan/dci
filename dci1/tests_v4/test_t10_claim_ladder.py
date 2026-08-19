"""T10. Claim ladder.

Vocabulary closure; one emitter per level; the L1 to L4 licensing rules and
their identification gates; the fifteen-row §28.1 outcome vocabulary;
INDETERMINATE emitted with both bounds; INSUFFICIENT_PRECISION withholding
equivalence and threshold statements while still reporting a resolved
direction; the reference-heterogeneity and companion-difficulty emission
blocks; refusal of an unregistered member name; refusal of a statement missing
a machine field; refusal of a scalar quoted without its configuration; the
equivalence precondition abort; the absence of any L5 code path; the
POSITION_CONFOUNDED wording on every position-shifted L1.
"""
from __future__ import annotations

import pytest

from dci1v4.analysis import claims
from dci1v4.analysis.bootstrap import MemberResult
from dci1v4.errors import ClaimError
from dci1v4.protocol import constants as C


def _member(name, estimate, half_width=0.03):
    return MemberResult(name=name, estimate=estimate, standard_error=0.01,
                        marginal_lower=estimate - half_width,
                        marginal_upper=estimate + half_width,
                        simultaneous_lower=estimate - half_width,
                        simultaneous_upper=estimate + half_width,
                        half_width=half_width)


def _context(**kwargs):
    base = {"configuration": "outcome_first",
            "measurement_basis": "human_validated"}
    base.update(kwargs)
    return claims.ClaimContext(**base)


def test_the_outcome_vocabulary_has_exactly_fifteen_rows():
    assert len(claims.OUTCOME_VOCABULARY) == 15
    for key in ("delivery_loss_resolved", "delivery_gain_resolved",
                "meaningful_magnitude", "equivalence", "asymmetry_resolved",
                "excess_above_generic_load_threshold",
                "pair_specific_threshold_reached",
                "generic_compositional_load",
                "indeterminate_at_a_threshold", "insufficient_precision",
                "reference_heterogeneity", "companion_difficulty_qualifier",
                "vacuity_asymmetry", "replication",
                "configuration_dependence"):
        assert key in claims.OUTCOME_VOCABULARY


def test_one_emitter_per_level_and_no_L5_code_path():
    emitters = [name for name in dir(claims) if name.startswith("emit_")]
    assert set(emitters) == {"emit_l1", "emit_l2", "emit_l3",
                             "emit_equivalence", "emit_l4"}
    claims.assert_no_l5_emitter()
    assert "L5" in C.WITHHELD_CLAIM_LEVELS
    assert "L5" not in claims.LEVEL_MEMBERS


def test_an_emitter_refuses_a_member_not_registered_to_it():
    with pytest.raises(ClaimError, match="may not name"):
        claims.emit_l1("Delta_R", _member("Delta_R", 0.3), _context(),
                       outcome="B", companion="A", outcome_position=1,
                       has_solo_headroom=True)
    with pytest.raises(ClaimError):
        claims._assert_member("L2", "D(B<-A)")
    with pytest.raises(ClaimError):
        claims._assert_member("L3a", "Lambda")


def test_l1_licences_only_when_the_interval_excludes_zero():
    spanning = claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.01, 0.04),
                              _context(), outcome="B", companion="A",
                              outcome_position=1, has_solo_headroom=True)
    assert spanning is None            # never reported as absence
    resolved = claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.20, 0.04),
                              _context(), outcome="B", companion="A",
                              outcome_position=1, has_solo_headroom=True)
    assert resolved.vocabulary_key == "delivery_loss_resolved"
    gain = claims.emit_l1("D(B<-A)", _member("D(B<-A)", -0.20, 0.04),
                          _context(), outcome="B", companion="A",
                          outcome_position=1, has_solo_headroom=True)
    assert gain.vocabulary_key == "delivery_gain_resolved"


def test_l1_requires_solo_headroom():
    assert claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.20, 0.04),
                          _context(), outcome="B", companion="A",
                          outcome_position=1,
                          has_solo_headroom=False) is None


def test_position_confounded_attaches_where_the_outcome_is_stated_second():
    first = claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.2, 0.04),
                           _context(), outcome="B", companion="A",
                           outcome_position=1, has_solo_headroom=True)
    assert "POSITION_CONFOUNDED" not in first.identification_status
    assert first.outcome_position == 1
    assert "position 1" in first.text

    second = claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.2, 0.04),
                            _context(configuration="outcome_second"),
                            outcome="B", companion="A", outcome_position=2,
                            has_solo_headroom=True)
    assert "POSITION_CONFOUNDED" in second.identification_status
    assert C.POSITION_WORDING in second.qualifiers


def test_l2_requires_the_l1_conditions_on_both_sides():
    assert claims.emit_l2(_member("Lambda", 0.3, 0.05), _context(),
                          l1_both_sides=False, outcome_position=1) is None
    resolved = claims.emit_l2(_member("Lambda", 0.3, 0.05), _context(),
                              l1_both_sides=True, outcome_position=1)
    assert resolved.vocabulary_key == "asymmetry_resolved"
    assert claims.emit_l2(_member("Lambda", 0.0, 0.05), _context(),
                          l1_both_sides=True, outcome_position=1) is None


def test_l3_is_withheld_under_excess_not_identified():
    context = _context(identification_status=("EXCESS_NOT_IDENTIFIED",))
    assert claims.emit_l3(_member("Delta_R", 0.4, 0.03), context,
                          outcome_position=1) is None


def test_l3_thresholds_map_to_the_registered_statements():
    context = _context()
    above_specific = claims.emit_l3(_member("Delta_R", 0.40, 0.03), context,
                                    outcome_position=1)
    assert above_specific.claim_level == "L3b"
    assert above_specific.vocabulary_key == "pair_specific_threshold_reached"

    above_generic = claims.emit_l3(_member("Delta_R", 0.18, 0.03), context,
                                   outcome_position=1)
    assert above_generic.claim_level == "L3a"
    assert above_generic.vocabulary_key == "excess_above_generic_load_threshold"

    below = claims.emit_l3(_member("Delta_R", 0.02, 0.03), context,
                           outcome_position=1)
    assert below.claim_level == "L3c"
    assert below.vocabulary_key == "generic_compositional_load"


def test_indeterminate_is_emitted_with_both_bounds():
    statement = claims.emit_l3(_member("Delta_R", 0.10, 0.03), _context(),
                               outcome_position=1)
    assert "INDETERMINATE" in statement.markers
    assert statement.detail["both_bounds"] == [statement.lower,
                                               statement.upper]
    assert 0.10 in statement.detail["thresholds_spanned"]


def test_insufficient_precision_withholds_thresholds_but_keeps_direction():
    wide = _member("Delta_R", 0.30, 0.20)      # half-width above 0.05
    statement = claims.emit_l3(wide, _context(), outcome_position=1)
    assert "INSUFFICIENT_PRECISION" in statement.markers
    assert statement.text == \
        claims.OUTCOME_VOCABULARY["insufficient_precision"]
    assert statement.vocabulary_key == "delivery_loss_resolved"
    unresolved = claims.emit_l3(_member("Delta_R", 0.0, 0.20), _context(),
                                outcome_position=1)
    assert unresolved is None


def test_the_precision_preconditions_are_the_registered_ones():
    assert C.PRECISION_PRECONDITIONS == {"D": 0.05, "Delta_R": 0.05,
                                         "Lambda": 0.08, "Delta_j": 0.06}
    assert claims.precision_ok("D(B<-A)", _member("D(B<-A)", 0.2, 0.05))
    assert not claims.precision_ok("D(B<-A)", _member("D(B<-A)", 0.2, 0.06))
    assert claims.precision_ok("Lambda", _member("Lambda", 0.2, 0.08))
    assert claims.precision_ok("Delta_1", _member("Delta_1", 0.2, 0.06))


def test_the_equivalence_emitter_aborts_when_its_precondition_is_false():
    inside_but_imprecise = _member("D(B<-A)", 0.0, 0.09)
    with pytest.raises(ClaimError, match="analysis aborts"):
        claims.emit_equivalence("D(B<-A)", inside_but_imprecise, _context(),
                                outcome_position=1)
    outside_but_precise = _member("D(B<-A)", 0.30, 0.04)
    with pytest.raises(ClaimError):
        claims.emit_equivalence("D(B<-A)", outside_but_precise, _context(),
                                outcome_position=1)
    licensed = claims.emit_equivalence("D(B<-A)", _member("D(B<-A)", 0.0,
                                                          0.04),
                                       _context(), outcome_position=1)
    assert licensed.vocabulary_key == "equivalence"


def test_the_reference_heterogeneity_block_names_the_disagreeing_reference():
    context = _context(delta_j_intervals={
        "Delta_1": _member("Delta_1", 0.30, 0.03),
        "Delta_2": _member("Delta_2", 0.30, 0.03),
        "Delta_3": _member("Delta_3", 0.02, 0.03)})
    statement = claims.emit_l3(_member("Delta_R", 0.20, 0.03), context,
                               outcome_position=1)
    joined = " ".join(statement.qualifiers)
    assert "disagreeing reference named" in joined
    assert "Delta_3" in joined


def test_the_companion_difficulty_block_fires_above_the_realised_gap():
    context = _context(realised_gaps={"R1": 0.02, "R2": 0.21})
    statement = claims.emit_l3(_member("Delta_R", 0.20, 0.03), context,
                               outcome_position=1)
    joined = " ".join(statement.qualifiers)
    assert "realised gap" in joined and "R2" in joined
    assert "R1" not in joined


def test_every_statement_carries_the_seven_machine_fields():
    statement = claims.emit_l1("D(B<-A)", _member("D(B<-A)", 0.2, 0.04),
                               _context(), outcome="B", companion="A",
                               outcome_position=1, has_solo_headroom=True)
    record = statement.as_record()
    for field in claims.REQUIRED_FIELDS:
        assert field in record
    claims.assert_statement_complete(record)
    claims.assert_scalar_carries_configuration(record)


def test_a_statement_missing_a_field_or_a_configuration_is_refused():
    with pytest.raises(ClaimError):
        claims.assert_statement_complete({"claim_level": "L1"})
    with pytest.raises(ClaimError):
        claims.assert_scalar_carries_configuration(
            {"estimate": 0.2, "configuration": None})


def test_the_scope_sentence_attaches_below_human_validation():
    statement = claims.emit_l1(
        "D(B<-A)", _member("D(B<-A)", 0.2, 0.04),
        _context(measurement_basis="autorater_calibration_approved"),
        outcome="B", companion="A", outcome_position=1,
        has_solo_headroom=True)
    assert statement.scope_sentence == C.SCOPE_SENTENCE
    assert statement.as_record()["scope_sentence"] == C.SCOPE_SENTENCE


def test_an_unregistered_measurement_basis_or_status_is_refused():
    with pytest.raises(ClaimError):
        claims.ClaimContext(configuration="c", measurement_basis="invented")
    with pytest.raises(ClaimError):
        claims.ClaimContext(configuration="c",
                            measurement_basis="human_validated",
                            identification_status=("MADE_UP",))


def test_l4_reports_replication_or_configuration_dependence():
    stable = claims.emit_l4({"outcome_first": {"D(B<-A)": "loss"},
                             "outcome_second": {"D(B<-A)": "loss"}},
                            _context())
    assert stable.vocabulary_key == "replication"
    differing = claims.emit_l4({"outcome_first": {"D(B<-A)": "loss"},
                                "outcome_second": {"D(B<-A)": "gain"}},
                               _context())
    assert differing.vocabulary_key == "configuration_dependence"
    assert claims.emit_l4({"only": {}}, _context()) is None
