"""Amendment A3: the exact interval, and the fixed design that makes it a rule.

Two things are asserted separately, because they fail separately.

The INTERVAL is exact Clopper-Pearson, and inverting it at the 5% ceiling and 95%
confidence gives 72 rather than the inherited 73, so the Tier-1 planning total moves
from 876 to 864. Those four numbers are computed here, not recalled.

The DESIGN is what turns a bound into a decision. The tests that matter most are the
ones showing an interval alone is insufficient: one error passes at n = 200 and fails
at n = 72, so without a prospectively fixed n the verdict would depend on a sample
size chosen after the errors were seen. A3 forbids that, and forbids the specific
remedy of extending to a larger sample.
"""
from __future__ import annotations

import json

import pytest

from dci.v19 import reliability as R

pytestmark = pytest.mark.cpu

DESIGN = R.AMENDED_TIER1_DESIGN


# ------------------------------------------------------------- the exact interval
def test_the_amended_interval_is_the_exact_one():
    assert R.AMENDED_INTERVAL == "clopper_pearson"
    assert R.INTERVAL_IMPLEMENTATIONS[R.AMENDED_INTERVAL].exact is True


def test_the_exact_interval_reaches_the_ceiling_at_seventy_two():
    assert R.smallest_zero_error_n(R.TIER1_CEILING, R.CONFIDENCE,
                                  R.CLOPPER_PEARSON) == 72
    assert R.AMENDED_TIER1_PER_TRUTH_CLASS == 72


def test_seventy_two_holds_and_seventy_one_does_not():
    assert R.CLOPPER_PEARSON.upper(0, 72, R.CONFIDENCE) <= R.TIER1_CEILING
    assert R.CLOPPER_PEARSON.upper(0, 71, R.CONFIDENCE) > R.TIER1_CEILING


def test_the_inherited_count_came_from_wilson_which_is_not_exact():
    assert R.smallest_zero_error_n(R.TIER1_CEILING, R.CONFIDENCE, R.WILSON) == 73
    assert R.INHERITED_TIER1_PER_TRUTH_CLASS == 73
    assert R.WILSON.exact is False


def test_the_planning_total_moves_from_876_to_864():
    assert R.INHERITED_TIER1_TOTAL_LABELS == 876
    assert R.AMENDED_TIER1_TOTAL_LABELS == 864
    assert R.AMENDED_TIER1_TOTAL_LABELS == 72 * 6 * 2
    assert R.tier1_total_labels(R.CLOPPER_PEARSON) == 864
    assert R.tier1_total_labels(R.WILSON) == 876


def test_the_design_total_agrees_with_the_module_constant():
    assert DESIGN.total_labels == R.AMENDED_TIER1_TOTAL_LABELS == 864


# ------------------------------------------------------------------- the design
def test_the_design_is_the_strict_fixed_one_a3_specifies():
    assert DESIGN.interval == "clopper_pearson"
    assert DESIGN.n_per_truth_class == 72
    assert DESIGN.errors_permitted == 0
    assert DESIGN.extension_permitted is False
    assert DESIGN.ceiling == 0.05
    assert DESIGN.confidence == 0.95


def test_the_design_names_the_remediation_rather_than_leaving_it_open():
    assert "fresh prospectively specified audit" in DESIGN.remediation
    assert "not by extending the original sample" in DESIGN.remediation
    assert "10.6" in DESIGN.remediation


def test_the_design_is_hashed_and_serialisable():
    state = DESIGN.state()
    assert json.loads(json.dumps(state)) == state
    assert len(DESIGN.design_hash) == 64


@pytest.mark.parametrize("field,value", [
    ("n_per_truth_class", 73),
    ("errors_permitted", 1),
    ("extension_permitted", True),
    ("interval", "wilson_score"),
    ("ceiling", 0.10),
])
def test_every_design_decision_moves_the_design_hash(field, value):
    import dataclasses
    other = dataclasses.replace(DESIGN, **{field: value})
    assert other.design_hash != DESIGN.design_hash


def test_a_nonsense_design_is_refused_at_declaration():
    import dataclasses
    with pytest.raises(R.AuditDesignError, match="positive per-class size"):
        dataclasses.replace(DESIGN, n_per_truth_class=0)
    with pytest.raises(R.AuditDesignError, match="not a budget"):
        dataclasses.replace(DESIGN, errors_permitted=-1)


# --------------------------------------------------- zero errors, or it fails
def test_a_clean_audit_at_the_planned_size_passes():
    certificate = R.tier1_certificate_under(
        DESIGN, "v19:p1.target.exact_bullet_count",
        false_passes=0, true_failures=72, false_fails=0, true_passes=72)
    assert certificate.passed is True
    assert certificate.interval == "clopper_pearson"
    assert all(b.design_violation == "" for b in certificate.bounds)


@pytest.mark.parametrize("errors", [1, 2, 5, 72])
def test_any_observed_error_fails_the_audit(errors):
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=errors, true_failures=72,
        false_fails=0, true_passes=72)
    assert certificate.passed is False


def test_a_single_error_fails_on_the_interval_as_well_as_the_design():
    """At the planned n the two rules agree, which is why 72 was chosen."""
    assert R.CLOPPER_PEARSON.upper(1, 72, R.CONFIDENCE) > R.TIER1_CEILING


def test_an_error_in_either_truth_class_fails_the_unit():
    for kwargs in ({"false_passes": 1, "false_fails": 0},
                   {"false_passes": 0, "false_fails": 1}):
        certificate = R.tier1_certificate_under(
            DESIGN, "u", true_failures=72, true_passes=72, **kwargs)
        assert certificate.passed is False


# ----------------------------------------- no conditional extension to a larger n
def test_one_hundred_and_ten_is_exactly_where_one_error_becomes_acceptable():
    """Why A3 names 110 rather than some round number.

    110 is the SMALLEST sample at which a single observed error still clears the
    5% ceiling under the exact interval. So "extend to 110" is not an arbitrary
    enlargement: it is the precise size that converts an audit failure into an
    audit pass, which is what makes it the extension worth forbidding by name.
    """
    assert R.CLOPPER_PEARSON.upper(1, 110, R.CONFIDENCE) <= R.TIER1_CEILING
    assert R.CLOPPER_PEARSON.upper(1, 109, R.CONFIDENCE) > R.TIER1_CEILING
    smallest = next(n for n in range(1, 500)
                    if R.CLOPPER_PEARSON.upper(1, n, R.CONFIDENCE)
                    <= R.TIER1_CEILING)
    assert smallest == 110


def test_one_error_fails_at_the_planned_size_and_would_pass_when_extended():
    """The loophole the fixed design closes, stated as arithmetic."""
    assert R.CLOPPER_PEARSON.upper(1, 72, R.CONFIDENCE) > R.TIER1_CEILING
    for extended in (110, 150, 200, 1000):
        assert R.CLOPPER_PEARSON.upper(1, extended, R.CONFIDENCE) <= R.TIER1_CEILING


@pytest.mark.parametrize("extended", [110, 150, 200, 1000])
def test_extending_the_sample_after_an_error_still_fails(extended):
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=1, true_failures=extended,
        false_fails=0, true_passes=72)
    assert certificate.passed is False
    violation = certificate.bounds[0].design_violation
    assert "forbids conditional extension" in violation
    assert "fresh prospectively specified audit" in violation


def test_extending_to_110_is_refused_even_though_the_interval_would_allow_it():
    """The case A3 names, and the one the interval alone cannot refuse.

    One error in 110 gives an exact upper bound of 0.0496, which clears the
    ceiling. The certificate still fails, and it fails on the DESIGN rather than
    on the bound - which is the whole reason the design had to be frozen.
    """
    assert R.CLOPPER_PEARSON.upper(1, 110, R.CONFIDENCE) <= R.TIER1_CEILING
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=1, true_failures=110,
        false_fails=0, true_passes=72)
    assert certificate.passed is False
    bound = certificate.bounds[0]
    assert bound.upper is not None and bound.upper <= R.TIER1_CEILING
    assert bound.design_violation, "the bound alone was content; the design was not"


def test_a_clean_but_extended_sample_is_also_refused():
    """The design fixed the size, so even a spotless larger audit is not it."""
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=0, true_failures=110,
        false_fails=0, true_passes=72)
    assert certificate.passed is False


def test_a_short_class_is_missing_evidence_not_a_smaller_audit():
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=0, true_failures=40,
        false_fails=0, true_passes=72)
    assert certificate.passed is False
    assert "missing evidence" in certificate.bounds[0].design_violation


def test_the_guard_refuses_a_wrong_size_before_any_bound_is_computed():
    R.assert_no_conditional_extension(DESIGN, 72)
    for realised in (71, 73, 110, 200):
        with pytest.raises(R.AuditDesignError, match="fixes 72"):
            R.assert_no_conditional_extension(DESIGN, realised)


def test_a_design_that_permits_extension_says_so_explicitly():
    """Nothing forbids declaring such a design; A3's is simply not one."""
    import dataclasses
    permissive = dataclasses.replace(DESIGN, extension_permitted=True,
                                     errors_permitted=1)
    R.assert_no_conditional_extension(permissive, 200)
    certificate = R.tier1_certificate_under(
        permissive, "u", false_passes=1, true_failures=200,
        false_fails=0, true_passes=200)
    assert certificate.passed is True
    assert DESIGN.extension_permitted is False


# ------------------------------------------ a design violation is not a pass
def test_a_design_violation_overrides_a_passing_bound():
    """A bound over a sample the design does not admit is about another procedure."""
    bound = R._class_bound("true_failures", 1, 200, R.CLOPPER_PEARSON, 0.05, 0.95)
    assert bound.passed is True                     # the interval alone is content
    import dataclasses
    violated = dataclasses.replace(bound, design_violation="extended after the fact")
    assert violated.passed is False
    assert violated.describe()["design_violation"] == "extended after the fact"


def test_a_missing_truth_class_is_still_missing_evidence_under_the_design():
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=0, true_failures=72,
        false_fails=None, true_passes=72)
    assert certificate.passed is False
    assert "true_passes" in certificate.unavailable


def test_an_absent_class_is_not_a_zero_error_class():
    certificate = R.tier1_certificate_under(
        DESIGN, "u", false_passes=0, true_failures=72,
        false_fails=0, true_passes=0)
    assert certificate.passed is False
    assert "true_passes" in certificate.unavailable


def test_an_unimplemented_interval_in_a_design_is_refused():
    import dataclasses
    with pytest.raises(R.ReliabilityBlocked, match="not an implemented interval"):
        R.tier1_certificate_under(
            dataclasses.replace(DESIGN, interval="bootstrap_t"), "u",
            false_passes=0, true_failures=72, false_fails=0, true_passes=72)


def test_the_certificate_is_serialisable_for_the_artifact_trail():
    described = R.tier1_certificate_under(
        DESIGN, "u", false_passes=0, true_failures=72,
        false_fails=0, true_passes=72).describe()
    assert json.loads(json.dumps(described)) == described
    assert all("design_violation" in b for b in described["bounds"])


# --------------------------------------------------------------- register row D45
def test_the_register_row_exists_because_section_ten_four_mis_cited_d9():
    row = R.REGISTER_ROW_D45
    assert row["row"] == "D45"
    assert "construction bootstrap" in row["supersedes_citation"]
    assert "10,000 replicates" in row["supersedes_citation"]


def test_the_register_row_records_both_consequences_of_the_choice():
    row = R.REGISTER_ROW_D45
    assert row["consequences"]["per_truth_class"] == [73, 72]
    assert row["consequences"]["total_tier1_labels"] == [876, 864]


def test_the_register_row_states_the_decision_including_the_design():
    decision = R.REGISTER_ROW_D45["decision"]
    assert "Clopper-Pearson" in decision
    assert "72" in decision
    assert "zero observed errors" in decision
    assert "no conditional sample extension" in decision


def test_the_register_row_is_serialisable():
    assert json.loads(json.dumps(R.REGISTER_ROW_D45)) == R.REGISTER_ROW_D45


# ------------------------------------- the recovery evidence is still available
def test_the_recovery_evidence_survives_the_decision():
    """A frozen decision whose evidence was deleted cannot be re-checked."""
    evidence = R.recover_inherited_interval()
    assert evidence["identified_implementation"] == "wilson_score"
    assert evidence["uniquely_recoverable"] is True
    assert evidence["satisfies_exact_binomial_description"] is False
    assert evidence["conflict"]
    assert evidence["by_implementation"]["clopper_pearson"]["n_at_zero_errors"] == 72
    assert evidence["by_implementation"]["wilson_score"]["n_at_zero_errors"] == 73
