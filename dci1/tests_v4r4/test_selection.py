"""Reference, spectrum and class selection read solo and chance, and nothing
else (§13.3-§13.7, §13.9).

The design's route to a false positive is outcome-adaptive selection: keeping
the families and severities whose composed result happens to be convenient.
These tests are the executable form of §13.9, and they check the *shape* of
the input as well as the behaviour of the rules -- a rule that would not use a
composed field is still refused a table that carries one.
"""
from __future__ import annotations

import dataclasses

import pytest

from dci1v4.errors import InstrumentError, ProtocolError
from dci1v4r4.protocol import constants as C
from dci1v4r4.stages import selection as S


def row(kind, severity, solo, chance, **kw):
    base = dict(kind=kind, severity=severity, solo_compliance=solo,
                chance_compliance=chance, solo_vacuity=0.0,
                prescreen_solo_compliance=solo,
                prescreen_chance_compliance=chance,
                wording_within_caliper=True, witnesses_pass=True)
    base.update(kw)
    return S.CalibrationRow(**base)


# --------------------------------------------------- required failure 1 and 2
def test_the_selection_input_has_no_field_a_composed_outcome_could_occupy():
    fields = {f.name for f in dataclasses.fields(S.CalibrationRow)}
    for bad in S.FORBIDDEN_CALIBRATION_FIELDS:
        assert not any(bad in f for f in fields), bad


@pytest.mark.parametrize("field", ["composed_compliance", "delivery_loss",
                                   "d_b_from_companion", "delta_r",
                                   "delta_difficulty", "xi",
                                   "joint_success", "composed_uptake"])
def test_a_calibration_table_carrying_a_composed_field_is_refused(field):
    payload = dict(kind="RF1", severity=3, solo_compliance=0.6,
                   chance_compliance=0.1, solo_vacuity=0.0,
                   prescreen_solo_compliance=0.6,
                   prescreen_chance_compliance=0.1,
                   wording_within_caliper=True, witnesses_pass=True)
    payload[field] = 0.42
    with pytest.raises(ProtocolError, match="§13.9"):
        S.load_calibration_table([payload])


def test_an_unknown_column_is_refused_even_if_it_looks_harmless():
    payload = dict(kind="RF1", severity=3, solo_compliance=0.6,
                   chance_compliance=0.1, solo_vacuity=0.0,
                   prescreen_solo_compliance=0.6,
                   prescreen_chance_compliance=0.1,
                   wording_within_caliper=True, witnesses_pass=True,
                   note="looks fine")
    with pytest.raises(ProtocolError, match="closed"):
        S.load_calibration_table([payload])


# ------------------------------------------------------- required failure 9
def test_instructed_compliance_is_not_raw_solo_compliance():
    """The coordinate nets out chance. A is unaffected; a budget is not."""
    assert S.instructed_compliance(0.61, 0.0) == pytest.approx(0.61)
    assert S.instructed_compliance(0.61, 0.50) == pytest.approx(0.22)
    # the matrix screen's own numbers: a rung matched to A on solo compliance
    # is nowhere near it on the registered coordinate.
    assert abs(S.instructed_compliance(0.6146, 0.0) - 0.6146) < 1e-9
    assert S.instructed_compliance(0.6146, 0.52) < 0.21


def test_an_anti_productive_rung_is_ineligible_everywhere():
    """Chance at or above solo means stating the constraint made it worse."""
    anti = row("CR4", 9, solo=0.335, chance=0.375)
    ok, reasons = S.eligible(anti)
    assert not ok
    assert any("anti-productive" in r for r in reasons)


def test_the_eligibility_floor_is_the_registered_smallest_effect_of_interest():
    assert C.SPECTRUM_ELIGIBILITY_BAND[0] == C.SMALLEST_EFFECT_OF_INTEREST
    assert C.SPECTRUM_ELIGIBILITY_BAND[1] == C.FOCAL_BAND[1]


# ------------------------------------------- §13.4 admission and §7.5 class
def test_a_production_class_family_cannot_be_a_core_reference():
    with pytest.raises(InstrumentError, match="class arm only"):
        S.admit_family("CL8", [row("CL8", 5, 0.62, 0.10)], iota_a=0.60,
                       prescreen_iota_a=0.60, solo_compliance_a=0.60)


def test_admission_reports_every_rejection_reason_rather_than_the_first():
    far = row("RF1", 8, solo=0.95, chance=0.0, solo_vacuity=0.5,
              wording_within_caliper=False)
    verdict = S.admit_family("RF1", [far], iota_a=0.60, prescreen_iota_a=0.60,
                             solo_compliance_a=0.60)
    assert not verdict.admitted
    reasons = verdict.rungs[0]["reasons"]
    assert len(reasons) >= 3
    assert any("caliper" in r for r in reasons)
    assert any("vacuity" in r for r in reasons)


# ------------------------------------------------- §13.6 the straddling rule
def _family(kind, iotas):
    """A family whose rungs sit at the given instructed-compliance values."""
    return [row(kind, i, solo=v, chance=0.0) for i, v in enumerate(iotas)]


def test_a_family_that_cannot_straddle_A_supplies_no_triple():
    rows = _family("RF1", [0.62, 0.66, 0.70])          # all above iota_a
    assert S.select_spectrum_triple("RF1", rows, core_severity=0,
                                    iota_a=0.60) is None


def test_the_triple_takes_one_rung_strictly_below_and_one_strictly_above():
    rows = _family("RF1", [0.30, 0.45, 0.60, 0.75, 0.90])
    triple = S.select_spectrum_triple("RF1", rows, core_severity=2,
                                      iota_a=0.60)
    assert triple["lower"]["iota"] < 0.60 < triple["upper"]["iota"]
    # nearest to iota_a -/+ 0.20, i.e. 0.40 and 0.80
    assert triple["lower"]["iota"] == pytest.approx(0.45)
    assert triple["upper"]["iota"] == pytest.approx(0.75)


def test_two_rungs_on_the_same_side_are_never_selected():
    """The failure a screen-scale spanning arm actually produced.

    Without strictness, 'the two rungs nearest iota_a -/+ 0.20' can both land
    below A when the ladder is one-sided. The rule refuses instead.
    """
    rows = _family("RF1", [0.20, 0.35, 0.50, 0.58])     # nothing above 0.60
    assert S.select_spectrum_triple("RF1", rows, core_severity=3,
                                    iota_a=0.60) is None


def test_a_family_admitted_but_unable_to_straddle_loses_its_slot():
    # RF1's near rung matches A best of all, but every eligible rung sits
    # above A, so it cannot supply a lower point and cannot be a reference.
    rows = (_family("RF1", [0.61, 0.63]) +
            _family("RF2", [0.35, 0.60, 0.85]) +
            _family("RF3", [0.38, 0.61, 0.82]) +
            _family("RF4", [0.40, 0.59, 0.80]))
    result = S.admit_core_references(rows, iota_a=0.60, prescreen_iota_a=0.60,
                                     solo_compliance_a=0.60)
    assert result["references_identified"]
    chosen = {r["family"] for r in result["core_references"]}
    assert "RF1" not in chosen
    assert [d["family"] for d in result["dropped_for_no_triple"]] == ["RF1"]


def test_fewer_than_three_straddling_families_is_the_reduced_design():
    rows = _family("RF2", [0.35, 0.60, 0.85]) + _family("RF3", [0.38, 0.61,
                                                                0.82])
    result = S.admit_core_references(rows, iota_a=0.60, prescreen_iota_a=0.60,
                                     solo_compliance_a=0.60)
    assert not result["references_identified"]
    assert result["design"] == "reduced"
    assert set(result["identification_statuses"]) == {
        "EXCESS_NOT_IDENTIFIED", "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"}


def test_selection_is_deterministic_under_reordering_of_the_input():
    rows = (_family("RF2", [0.35, 0.60, 0.85]) +
            _family("RF3", [0.38, 0.61, 0.82]) +
            _family("RF4", [0.40, 0.59, 0.80]))
    first = S.select_all(rows, iota_a=0.60, prescreen_iota_a=0.60,
                         solo_compliance_a=0.60).slot_map()
    second = S.select_all(list(reversed(rows)), iota_a=0.60,
                          prescreen_iota_a=0.60,
                          solo_compliance_a=0.60).slot_map()
    assert first == second


# ------------------------------------------------------------ §13.7 the class arm
def test_the_class_companion_comes_only_from_the_lower_bound_families():
    rows = (_family("RF2", [0.35, 0.60, 0.85]) +
            [row("CL8", 5, solo=0.63, chance=0.05)])
    verdict = S.admit_class_companion(rows, iota_a=0.60)
    assert verdict["available"]
    assert verdict["companion"]["family"] == "CL8"
    assert verdict["companion"]["constraint_class"] == "production"


def test_no_eligible_class_severity_drops_the_arm_rather_than_widening():
    rows = _family("RF2", [0.35, 0.60, 0.85])
    verdict = S.admit_class_companion(rows, iota_a=0.60)
    assert not verdict["available"]
    assert verdict["identification_statuses"] == ["CLASS_ARM_NOT_AVAILABLE"]


def test_every_selection_result_carries_the_permanent_class_status():
    rows = (_family("RF2", [0.35, 0.60, 0.85]) +
            _family("RF3", [0.38, 0.61, 0.82]) +
            _family("RF4", [0.40, 0.59, 0.80]) +
            [row("CL8", 5, solo=0.63, chance=0.05)])
    result = S.select_all(rows, iota_a=0.60, prescreen_iota_a=0.60,
                          solo_compliance_a=0.60)
    assert "COMPANION_CLASS_NOT_MATCHED" in result.identification_statuses
    assert len(result.spectrum) == C.N_SPECTRUM_COMPANIONS
    assert C.CLASS_SLOT in result.slot_map()
