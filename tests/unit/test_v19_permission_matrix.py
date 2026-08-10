"""The complete role x use permission matrix, cell by cell.

A flat role denylist could not express the protocol, and two cases prove it.

`outcome`. Section 11.8's sentence names only post-treatment and diagnostic
fields, so a denylist built from it admitted `target_verdict` as a covariate,
filter, weight, matching coordinate and denominator - conditioning primary
estimation on its own result. The prohibition is real but comes from elsewhere:
section 12.1(2) assigns structural states "without consulting effect direction",
section 10.1 forbids dropping a delivered response for its state, section 15.6
forbids dropping cells whose effects are inconvenient, and section 7.4 bars
construction from inspecting confirmatory outcomes. Yet F_A *is* the response, so
simply adding "outcome" to the denylist would have been wrong in the other
direction.

`matching coordinate`. D7 fixes parameter severity as EXCLUDED from matching while
section 6.5 keeps parameters "archived and reported" - one field legal in general
and illegal for one use. No role-keyed denylist can represent that, and it was a
live violation: `assert_primary_covariate("parameters", use="matching coordinate")`
passed.

Every cell of the matrix is exercised below, in both directions.
"""
import pytest

from dci.v19 import field_roles
from dci.v19.field_roles import (FIELD_ROLES, MATCHING_COORDINATES, PERMISSION,
                                 PRIMARY_USES, REPORTED_BUT_NOT_MATCHED, USES,
                                 FieldRoleViolation, assert_field_use,
                                 assert_matching_coordinate,
                                 assert_primary_covariate, assert_primary_formula,
                                 permission_reason, permits)

pytestmark = pytest.mark.cpu

# The matrix as the preregistration defines it, written out independently of the
# implementation so the test is a specification rather than a mirror.
EXPECTED = {
    "identity":                       {"denominator definition", "diagnostic only"},
    "treatment":                      {"covariate", "filter", "diagnostic only"},
    "pretreatment_design":            {"covariate", "diagnostic only"},
    "apparatus":                      {"diagnostic only"},
    "post_treatment_instrumentation": {"diagnostic only"},
    "outcome":                        {"outcome", "diagnostic only"},
    "diagnostic":                     {"diagnostic only"},
}

A_FIELD = {"identity": "superblock_id", "treatment": "arm",
           "pretreatment_design": "parameters", "apparatus": "dtype",
           "post_treatment_instrumentation": "u_r", "outcome": "target_verdict",
           "diagnostic": "exploit_suspected"}


# ------------------------------------------------------------- the whole matrix
def test_the_matrix_is_well_formed():
    field_roles.assert_roles_well_formed()


def test_every_role_and_use_is_covered():
    assert set(EXPECTED) == set(FIELD_ROLES)
    assert set(USES) == {"outcome", "covariate", "weight", "filter",
                         "matching coordinate", "denominator definition",
                         "diagnostic only"}


@pytest.mark.parametrize("role", sorted(EXPECTED))
@pytest.mark.parametrize("use", USES)
def test_every_matrix_cell_matches_the_preregistration(role, use):
    expected = use in EXPECTED[role]
    assert permits(role, use) is expected, f"({role}, {use})"


@pytest.mark.parametrize("role", sorted(EXPECTED))
@pytest.mark.parametrize("use", USES)
def test_every_cell_is_enforced_on_a_real_field(role, use):
    field = A_FIELD[role]
    if use in EXPECTED[role] and use != "matching coordinate":
        assert assert_field_use(field, use) == field
    else:
        with pytest.raises(FieldRoleViolation):
            assert_field_use(field, use)


def test_every_permitted_cell_carries_a_citation():
    for (role, use), citation in PERMISSION.items():
        assert citation, f"({role}, {use})"
        assert permission_reason(role, use) == citation


def test_asking_the_reason_for_a_forbidden_cell_raises():
    with pytest.raises(FieldRoleViolation, match="may not be used as a"):
        permission_reason("outcome", "covariate")


def test_absent_from_the_matrix_means_forbidden():
    """The default is refusal, so a use added later is barred until cited."""
    assert not permits("apparatus", "weight")
    assert ("apparatus", "weight") not in PERMISSION


def test_no_role_is_permitted_in_every_use():
    for role in FIELD_ROLES:
        assert len(EXPECTED[role]) < len(USES), role


def test_an_unknown_role_or_use_is_refused():
    with pytest.raises(FieldRoleViolation, match="not a declared role"):
        permits("confounder", "covariate")
    with pytest.raises(FieldRoleViolation, match="not a recognised"):
        permits("treatment", "instrument")
    with pytest.raises(FieldRoleViolation, match="not a recognised"):
        assert_field_use("arm", "instrument")


# ---------------------------------------------------- the reported defect: outcome
def test_the_outcome_is_usable_as_the_actual_outcome():
    """Section 12.1 defines D_ipj from the replicate mean of F_A."""
    for field in ("target_verdict", "f_a"):
        assert assert_field_use(field, "outcome") == field


@pytest.mark.parametrize("use", PRIMARY_USES)
@pytest.mark.parametrize("field", ["target_verdict", "f_a"])
def test_the_outcome_is_refused_in_every_conditioning_use(field, use):
    """The exact reproduction: all five of these used to succeed."""
    with pytest.raises(FieldRoleViolation) as caught:
        assert_field_use(field, use)
    if use != "matching coordinate":
        assert "its own result" in str(caught.value)


def test_the_outcome_refusal_points_at_the_legitimate_use():
    with pytest.raises(FieldRoleViolation, match="use='outcome'"):
        assert_field_use("target_verdict", "covariate")


def test_the_legacy_wrapper_also_refuses_the_outcome():
    """assert_primary_covariate is kept for callers, and is now correct."""
    with pytest.raises(FieldRoleViolation):
        assert_primary_covariate("target_verdict")
    with pytest.raises(FieldRoleViolation):
        assert_primary_formula(["target_verdict"], use="filter")


def test_a_formula_mixing_outcome_and_post_treatment_reports_both():
    with pytest.raises(FieldRoleViolation) as caught:
        assert_primary_formula(["arm", "target_verdict", "u_r"], use="filter")
    message = str(caught.value)
    assert "2 field(s)" in message
    assert "target_verdict" in message and "u_r" in message
    assert "arm" not in message          # treatment may define a cell


def test_no_role_whatsoever_may_become_a_primary_weight():
    """Section 12.1: the estimator is the UNWEIGHTED mean across superblocks,
    and "no primary reference weights w_j exist" (section 12.1)."""
    assert not [r for (r, u) in PERMISSION if u == "weight"]
    for role, field in A_FIELD.items():
        with pytest.raises(FieldRoleViolation):
            assert_field_use(field, "weight")


# ------------------------------------- the unreported defect: matching coordinates
@pytest.mark.parametrize("coordinate", MATCHING_COORDINATES)
def test_the_four_preregistered_matching_coordinates_are_permitted(coordinate):
    """Section 7.3's closed set of four empirical properties."""
    assert assert_matching_coordinate(coordinate) == coordinate


def test_there_are_exactly_four_matching_coordinates():
    assert len(MATCHING_COORDINATES) == 4


def test_parameter_severity_is_refused_as_a_matching_coordinate():
    """D7: FIXED, excluded. This passed before the repair."""
    with pytest.raises(FieldRoleViolation, match="EXCLUDED from matching"):
        assert_field_use("parameters", "matching coordinate")
    with pytest.raises(FieldRoleViolation, match="parameter severity"):
        assert_matching_coordinate("parameter_severity")


@pytest.mark.parametrize("field", ["parameters", "canonical_wording", "task",
                                   "target_id", "arm", "superblock_id", "dtype",
                                   "u_r", "f_a", "exploit_suspected"])
def test_no_stored_analysis_field_may_be_a_matching_coordinate(field):
    """Matching ranges over computed statistics, not stored fields at all."""
    with pytest.raises(FieldRoleViolation):
        assert_field_use(field, "matching coordinate")


def test_instruction_length_is_reported_but_not_matched():
    """Section 7.3 says so explicitly, and the error says why."""
    assert REPORTED_BUT_NOT_MATCHED == ("instruction_length",)
    with pytest.raises(FieldRoleViolation, match="does not match it"):
        assert_matching_coordinate("instruction_length")


def test_the_matrix_admits_no_role_to_matching():
    """Enforced by assert_roles_well_formed, so it cannot regress."""
    assert not [r for (r, u) in PERMISSION if u == "matching coordinate"]


def test_adding_a_role_to_matching_is_caught_by_the_well_formed_check():
    import dci.v19.field_roles as module
    original = module.PERMISSION
    try:
        module.PERMISSION = {**original,
                             ("pretreatment_design", "matching coordinate"): "x"}
        with pytest.raises(ValueError, match="section 7.3 restricts matching"):
            module.assert_roles_well_formed()
    finally:
        module.PERMISSION = original
    field_roles.assert_roles_well_formed()


# -------------------------------------------- the roles section 11.8 names barred
@pytest.mark.parametrize("use", PRIMARY_USES)
@pytest.mark.parametrize("field", ["u_r", "cap_hit", "final_answer_length",
                                   "latency", "truncation_state"])
def test_post_treatment_stays_barred_from_every_conditioning_use(field, use):
    with pytest.raises(FieldRoleViolation):
        assert_field_use(field, use)


@pytest.mark.parametrize("use", PRIMARY_USES)
@pytest.mark.parametrize("field", ["focal_compliance", "exploit_suspected",
                                   "partial_compliance_state"])
def test_diagnostic_stays_barred_from_every_conditioning_use(field, use):
    with pytest.raises(FieldRoleViolation):
        assert_field_use(field, use)


def test_both_barred_roles_remain_describable():
    """Section 11.8 permits secondary description; it bars conditioning."""
    for field in ("u_r", "exploit_suspected"):
        assert assert_field_use(field, "diagnostic only") == field


# --------------------------------------------------------------- the audit view
def test_the_matrix_view_is_serialisable_and_complete():
    import json
    matrix = field_roles.permission_matrix()
    json.dumps(matrix)
    assert set(matrix) == set(FIELD_ROLES)
    for role, row in matrix.items():
        assert set(row) == set(USES)
        assert {u for u, ok in row.items() if ok} == EXPECTED[role]


def test_the_audit_lists_permitted_uses_per_field():
    rows = {r["field"]: r for r in field_roles.audit()}
    assert rows["target_verdict"]["permitted_uses"] == ["outcome",
                                                       "diagnostic only"]
    assert rows["arm"]["permitted_uses"] == ["covariate", "filter",
                                             "diagnostic only"]
    assert rows["u_r"]["permitted_uses"] == ["diagnostic only"]


def test_an_undeclared_field_is_still_refused_for_every_use():
    for use in USES:
        with pytest.raises(FieldRoleViolation, match="no declared causal role"):
            assert_field_use("some_new_column", use)
