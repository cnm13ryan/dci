"""§17.5 registers one guarded emitter per claim level. Three had none.

`claims.py` held `emit_l3` and nothing else, and `_claims` short-circuited to a
single non-emitted L3 statement as soon as `Delta_R` or `Xi` were unidentified.
So a replication running §8.6's reduced design produced **no claim at all** ---
while §28's status table says in terms that `EXCESS_NOT_IDENTIFIED` means "L1
and L2 proceed under the reduced design; L3a-L3c are withheld", and while the
reduced design's entire identified estimand set is exactly L1's two members and
L2's one.

Both v4r4 replications that survive Gate 4 run that design, so the ladder would
have been silent about precisely the quantities it can speak to.

Every test here reads only the registered licensing rule of §3.2's table and
§17.3's and §17.4's qualifiers. No number from any confirmatory run enters.
"""
from __future__ import annotations

import pytest

from dci1v4r4.analysis import claims as CL
from dci1v4r4.protocol import constants as C

BASIS = "deterministic_measurement_validated"


def I(member, estimate, lower, upper):        # noqa: E743 - reads as maths
    return CL.Interval(member=member, estimate=estimate, lower=lower,
                       upper=upper)


def l1(interval, **over):
    kwargs = dict(configuration=C.OUTCOME_FIRST, outcome_position=1,
                  measurement_basis=BASIS, member=interval.member,
                  interval=interval, solo_headroom=True)
    kwargs.update(over)
    return CL.emit_l1(**kwargs)


def l2(interval, licensed=True, **over):
    kwargs = dict(configuration=C.OUTCOME_FIRST, outcome_position=1,
                  measurement_basis=BASIS, interval=interval,
                  l1_licensed={m: licensed for m in CL.LEVEL_MEMBERS["L1"]})
    kwargs.update(over)
    return CL.emit_l2(**kwargs)


# ---------------------------------------------------------------- existence

def test_one_guarded_emitter_exists_per_registered_level():
    """§17.5, and L5 is permanently withheld and has none by design."""
    for level in ("l1", "l2", "l3", "l4"):
        assert callable(getattr(CL, f"emit_{level}"))
    CL.assert_no_l5_emitter(vars(CL))
    assert "L5" in C.WITHHELD_CLAIM_LEVELS


def test_an_emitter_refuses_a_member_not_registered_to_its_level():
    with pytest.raises(CL.ClaimError):
        l1(I("Lambda", 0.2, 0.1, 0.3), member="Lambda")
    with pytest.raises(CL.ClaimError):
        l2(I("D(B<-A)", 0.2, 0.1, 0.3))


# ------------------------------------------------------------ L1 licensing

def test_l1_is_licensed_by_a_lower_bound_above_zero():
    assert l1(I("D(B<-A)", 0.20, 0.11, 0.29))["emitted"] is True
    assert l1(I("D(B<-A)", 0.20, -0.01, 0.41))["emitted"] is False
    assert l1(I("D(B<-A)", 0.20, 0.0, 0.40))["emitted"] is False


def test_l1_without_solo_headroom_is_gated_and_says_so():
    statement = l1(I("D(A<-B)", 0.3, 0.2, 0.4), solo_headroom=False)
    assert statement["emitted"] is False
    assert "solo headroom" in statement["reason"]


def test_l1_in_the_shifted_configuration_carries_the_position_caveat():
    shifted = l1(I("D(B<-A)", 0.2, 0.1, 0.3),
                 configuration=C.OUTCOME_SECOND, outcome_position=2)
    assert "POSITION_CONFOUNDED" in shifted["identification_status"]
    first = l1(I("D(B<-A)", 0.2, 0.1, 0.3))
    assert "POSITION_CONFOUNDED" not in first["identification_status"]


def test_a_direction_survives_insufficient_precision_and_carries_the_status():
    """§17.3: a half-width above the precondition withholds equivalence and
    threshold statements and still reports a resolved direction."""
    wide = I("D(B<-A)", 0.30, 0.01, 0.59)      # half-width 0.29 > 0.05
    assert wide.half_width > C.PRECISION_PRECONDITIONS["D"]
    statement = l1(wide)
    assert statement["emitted"] is True
    assert "INSUFFICIENT_PRECISION" in statement["identification_status"]

    narrow = l1(I("D(B<-A)", 0.20, 0.16, 0.24))
    assert "INSUFFICIENT_PRECISION" not in narrow["identification_status"]


def test_the_vacuity_forced_recomputation_must_license_the_same_claim():
    """§17.4: otherwise the axis is reported unresolved with both bounds."""
    primary = I("D(B<-A)", 0.20, 0.11, 0.29)
    agrees = I("D(B<-A)|vacuity_forced", 0.18, 0.08, 0.28)
    disagrees = I("D(B<-A)|vacuity_forced", 0.05, -0.05, 0.15)
    assert l1(primary, vacuity_forced=agrees)["emitted"] is True
    blocked = l1(primary, vacuity_forced=disagrees)
    assert blocked["emitted"] is False
    assert "§17.4" in blocked["reason"]
    assert blocked["vacuity_forced_interval"] == [-0.05, 0.15]


# ------------------------------------------------------------ L2 licensing

def test_l2_needs_lambda_to_exclude_zero_from_either_side():
    assert l2(I("Lambda", 0.15, 0.05, 0.25))["emitted"] is True
    assert l2(I("Lambda", -0.15, -0.25, -0.05))["emitted"] is True
    assert l2(I("Lambda", 0.02, -0.08, 0.12))["emitted"] is False


def test_l2_is_gated_on_l1_for_both_directions():
    both = l2(I("Lambda", 0.15, 0.05, 0.25))
    assert both["emitted"] is True
    one = CL.emit_l2(configuration=C.OUTCOME_FIRST, outcome_position=1,
                     measurement_basis=BASIS,
                     interval=I("Lambda", 0.15, 0.05, 0.25),
                     l1_licensed={"D(B<-A)": True, "D(A<-B)": False})
    assert one["emitted"] is False
    assert "D(A<-B)" in one["reason"]


def test_l2_names_the_direction_of_the_larger_loss():
    assert "B <- A" in l2(I("Lambda", 0.15, 0.05, 0.25))["statement"]
    assert "A <- B" in l2(I("Lambda", -0.15, -0.25, -0.05))["statement"]


# ------------------------------------------------------------ L4 licensing

def test_l4_needs_the_same_classification_in_every_configuration():
    same = CL.emit_l4(per_configuration={C.OUTCOME_FIRST: ["L1", "L2"],
                                         C.OUTCOME_SECOND: ["L1", "L2"]},
                      measurement_basis=BASIS)
    assert same["emitted"] is True

    differing = CL.emit_l4(
        per_configuration={C.OUTCOME_FIRST: ["L1", "L2"],
                           C.OUTCOME_SECOND: ["L1"]},
        measurement_basis=BASIS)
    assert differing["emitted"] is False
    assert "same classification" in differing["reason"]


def test_l4_is_not_licensed_when_no_configuration_reached_a_level():
    empty = CL.emit_l4(per_configuration={C.OUTCOME_FIRST: [],
                                          C.OUTCOME_SECOND: []},
                       measurement_basis=BASIS)
    assert empty["emitted"] is False
    assert "no configuration reached a level" in empty["reason"]


def test_l4_is_not_licensed_from_one_configuration_alone():
    partial = CL.emit_l4(per_configuration={C.OUTCOME_FIRST: ["L1"]},
                         measurement_basis=BASIS)
    assert partial["emitted"] is False


# --------------------------------------------------------- machine fields

@pytest.mark.parametrize("statement", [
    l1(I("D(B<-A)", 0.2, 0.1, 0.3)),
    l2(I("Lambda", 0.15, 0.05, 0.25)),
    CL.emit_l4(per_configuration={C.OUTCOME_FIRST: ["L1"],
                                  C.OUTCOME_SECOND: ["L1"]},
               measurement_basis=BASIS),
])
def test_every_emitted_statement_carries_every_machine_field(statement):
    assert statement["emitted"] is True
    CL.assert_statement_complete(statement)
    for field in CL.REQUIRED_FIELDS:
        assert field in statement
    assert statement["class_sentence"] == C.CLASS_SENTENCE


def test_the_reduced_design_reaches_l1_and_l2_and_no_l3_sub_level():
    """§28: `EXCESS_NOT_IDENTIFIED` means L1 and L2 proceed and L3a-L3c are
    withheld. That is the whole reason these emitters have to exist."""
    from dci1v4r4.run.analysis_run import _claims

    entry = {"families": {C.PRIMARY_FAMILY: {"members": {
        "D(B<-A)": {"estimate": 0.2, "simultaneous": [0.15, 0.25]},
        "D(A<-B)": {"estimate": 0.1, "simultaneous": [0.06, 0.14]},
        "Lambda": {"estimate": 0.1, "simultaneous": [0.05, 0.15]}}}}}
    ladder = _claims(entry, configuration=C.OUTCOME_FIRST,
                     measurement_basis=BASIS,
                     identification_statuses=["EXCESS_NOT_IDENTIFIED"],
                     solo_headroom=True)
    levels = [s["claim_level"] for s in ladder["statements"] if s["emitted"]]
    assert levels == ["L1", "L1", "L2"]
    withheld = [s for s in ladder["statements"] if not s["emitted"]]
    assert [s["claim_level"] for s in withheld] == ["L3"]
    assert ladder["identified"] == {"Delta_R": False, "Xi": False,
                                    "delta_difficulty": False}
