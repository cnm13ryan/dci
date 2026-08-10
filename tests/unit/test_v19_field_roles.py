"""Causal field roles: post-treatment fields cannot enter a primary formula.

Section 11.8 gives every analysis field exactly one pre-frozen role and then
states the consequence: "Primary estimators reject post-treatment and diagnostic
fields as covariates, weights, filters, matching coordinates, or denominator
definitions."

The reason this needs a gate rather than a paragraph is that the tempting fields
are the plausible ones. Realised reasoning use, cap-hit, final-answer length,
latency and truncation state are recorded for every generation, look like sensible
adjustments, and are all *caused by the treatment* - so conditioning on them
changes the estimand instead of removing confounding.
"""
import pytest

from dci.v19 import field_roles
from dci.v19.field_roles import (FIELD_ROLES, FORBIDDEN_IN_PRIMARY, PRIMARY_USES,
                                 FieldRoleViolation, assert_primary_covariate,
                                 assert_primary_formula, role_of)

pytestmark = pytest.mark.cpu


def test_the_declared_roles_are_well_formed():
    field_roles.assert_roles_well_formed()


def test_the_seven_roles_of_section_eleven_eight_are_declared():
    assert set(FIELD_ROLES) == {
        "identity", "treatment", "pretreatment_design", "apparatus",
        "post_treatment_instrumentation", "outcome", "diagnostic"}


def test_every_field_has_exactly_one_role():
    seen = [f for fields in FIELD_ROLES.values() for f in fields]
    assert len(seen) == len(set(seen))


def test_the_forbidden_roles_are_the_two_the_protocol_names():
    assert set(FORBIDDEN_IN_PRIMARY) == {"post_treatment_instrumentation",
                                         "diagnostic"}
    for role in FORBIDDEN_IN_PRIMARY:
        assert role in FIELD_ROLES


@pytest.mark.parametrize("field,role", [
    ("superblock_id", "identity"),
    ("generation_id", "identity"),
    ("arm", "treatment"),
    ("hard_budget", "treatment"),
    ("load", "treatment"),
    ("presentation_order", "treatment"),
    ("task", "pretreatment_design"),
    ("canonical_wording", "pretreatment_design"),
    ("dtype", "apparatus"),
    ("gpu_identity", "apparatus"),
    ("f_a", "outcome"),
    ("target_verdict", "outcome"),
])
def test_the_declared_roles_are_the_preregistered_ones(field, role):
    assert role_of(field) == role


@pytest.mark.parametrize("field", ["arm", "hard_budget", "load",
                                   "presentation_order", "task",
                                   "canonical_wording", "parameters"])
def test_treatment_and_pretreatment_fields_may_be_covariates(field):
    assert assert_primary_covariate(field) == field


@pytest.mark.parametrize("field", [
    "realised_reasoning_use", "u_r", "cap_hit", "reasoning_ended_naturally",
    "final_answer_length", "latency", "finish_reason", "truncation_state",
    "final_truncated", "cap_forced_transition",
])
def test_post_treatment_instrumentation_is_barred_from_primary_formulas(field):
    assert role_of(field) == "post_treatment_instrumentation"
    with pytest.raises(FieldRoleViolation, match="changes the estimand"):
        assert_primary_covariate(field)


@pytest.mark.parametrize("field", [
    "focal_compliance", "reference_compliance", "partial_compliance_state",
    "exploit_suspected", "generation_state",
])
def test_diagnostic_fields_are_barred_from_primary_formulas(field):
    assert role_of(field) == "diagnostic"
    with pytest.raises(FieldRoleViolation):
        assert_primary_covariate(field)


@pytest.mark.parametrize("use", PRIMARY_USES)
def test_every_prohibited_use_is_refused_for_post_treatment(use):
    """Section 11.8 bars five distinct uses, not just 'covariate'."""
    with pytest.raises(FieldRoleViolation):
        assert_primary_covariate("u_r", use=use)


def test_an_undeclared_field_is_refused_rather_than_defaulted():
    """A field with no role has not been through pre-freeze classification."""
    with pytest.raises(FieldRoleViolation, match="no declared causal role"):
        role_of("some_new_column")
    with pytest.raises(FieldRoleViolation, match="Declare it in FIELD_ROLES"):
        assert_primary_covariate("some_new_column")


def test_a_whole_formula_reports_every_offending_field_at_once():
    """One at a time invites removing them until the formula happens to pass."""
    with pytest.raises(FieldRoleViolation) as caught:
        assert_primary_formula(["load", "u_r", "arm", "final_answer_length",
                                "exploit_suspected"], use="filter")
    message = str(caught.value)
    assert "3 field(s)" in message
    for field in ("u_r", "final_answer_length", "exploit_suspected"):
        assert field in message
    assert "load" not in message and "arm" not in message


def test_a_clean_primary_formula_passes():
    assert_primary_formula(["arm", "hard_budget", "load", "presentation_order",
                            "task"])


def test_an_undeclared_field_in_a_formula_is_refused():
    with pytest.raises(FieldRoleViolation, match="no declared causal role"):
        assert_primary_formula(["arm", "mystery_column"])


def test_fields_with_role_rejects_an_unknown_role():
    assert "f_a" in field_roles.fields_with_role("outcome")
    with pytest.raises(FieldRoleViolation, match="not one of the declared roles"):
        field_roles.fields_with_role("confounder")


def test_the_audit_marks_which_fields_primary_analysis_may_consume():
    rows = field_roles.audit()
    assert len(rows) == sum(len(f) for f in FIELD_ROLES.values())
    by_field = {r["field"]: r for r in rows}
    assert by_field["arm"]["permitted_in_primary"] is True
    assert by_field["u_r"]["permitted_in_primary"] is False
    assert by_field["f_a"]["permitted_uses"] == ["outcome", "diagnostic only"]
    assert "covariate" not in by_field["f_a"]["permitted_uses"]
    import json
    json.dumps(rows)


def test_the_outcome_and_the_instrumentation_are_not_confused():
    """F_A is the outcome; how long the answer was is not."""
    assert role_of("f_a") == "outcome"
    assert role_of("final_answer_length") == "post_treatment_instrumentation"


def test_a_duplicated_declaration_would_be_caught():
    """The one-role rule is enforced at import, so simulate the violation."""
    import dci.v19.field_roles as module
    original = module.FIELD_ROLES
    try:
        module.FIELD_ROLES = {**original,
                              "diagnostic": original["diagnostic"] + ("load",)}
        with pytest.raises(ValueError, match="exactly one role"):
            module.assert_roles_well_formed()
    finally:
        module.FIELD_ROLES = original
    field_roles.assert_roles_well_formed()
