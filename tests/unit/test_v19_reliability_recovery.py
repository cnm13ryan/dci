"""Section 10.4's recovery, and why it ends in a decision rather than a freeze.

The instruction was: "The exact two-sided binomial interval implementation used by
the inherited gate must be recovered from the authoritative code/specification and
frozen at Stage 2; if it is not uniquely recoverable, its choice is a \\PFD within
register item D9 rather than an implementer decision."

Recovery succeeded, and what it recovered contradicts the description. These tests
establish that on arithmetic rather than on recollection:

  * the inherited gate inverts `wilson_interval`, and that inversion returns 73 -
    the count section 10.4 says is preserved;
  * six units times two truth classes times 73 is 876, the other count section
    10.4 states, so both preserved numbers are Wilson's;
  * Wilson is a normal-approximation interval, which is the family section 6.2
    rejects when it requires an exact Clopper-Pearson interval;
  * exact Clopper-Pearson gives 72 and 864 instead.

So the interval is uniquely recoverable AND is not exact, both halves of the
sentence cannot hold, and the choice is an investigator decision. Nothing here
selects one, and `frozen_interval` refuses while the slot is pending.
"""
import pytest

from dci.measurement import audit_sizing
from dci.v19 import reliability as R
from dci.v19.registry import REGISTRY
from dci.v19.reliability import (
    CLOPPER_PEARSON,
    WILSON,
    ReliabilityBlocked,
    tier_certificate,
)

pytestmark = pytest.mark.cpu


# ------------------------------------------------------- the fixed architecture
def test_the_section_ten_four_ceilings_are_the_preregistered_ones():
    assert R.TIER1_CEILING == 0.05
    assert R.TIER2_PER_STRATUM_CEILING == 0.20
    assert R.POOLED_SYSTEM_CEILING == 0.05
    assert R.CONFIDENCE == 0.95
    assert R.INHERITED_TIER1_PER_TRUTH_CLASS == 73
    assert R.TIER1_VERIFIER_UNITS == 6
    assert R.INHERITED_TIER1_TOTAL_LABELS == 876


def test_the_two_truth_classes_are_the_ones_the_protocol_names():
    assert R.TIER1_TRUTH_CLASSES == ("true_failures", "true_passes")


# ------------------------------------------- the v19 Wilson matches the inherited
@pytest.mark.parametrize("k,n", [(0, 1), (0, 73), (1, 73), (5, 100), (50, 100),
                                 (100, 100), (99, 100), (0, 10_000), (3, 7)])
def test_the_v19_wilson_agrees_with_the_inherited_helper_exactly(k, n):
    """Written out rather than imported, so agreement is asserted not assumed."""
    assert WILSON.interval(k, n, 0.95) == pytest.approx(
        audit_sizing.wilson_interval(k, n, 0.95))


def test_the_inherited_gate_inverts_the_wilson_interval():
    assert audit_sizing.wilson_interval in (
        audit_sizing.required_cases_for_ceiling.__defaults__ or ())


# --------------------------------------------------------------- the arithmetic
def test_the_inherited_inversion_returns_the_preserved_count():
    assert audit_sizing.required_cases_for_ceiling(0.05, 0.95) == 73
    assert R.smallest_zero_error_n(0.05, 0.95, WILSON) == 73


def test_seventy_three_is_the_smallest_n_and_seventy_two_is_not_enough():
    assert WILSON.upper(0, 73, 0.95) <= 0.05
    assert WILSON.upper(0, 72, 0.95) > 0.05


def test_the_exact_interval_reaches_the_ceiling_one_sample_earlier():
    assert R.smallest_zero_error_n(0.05, 0.95, CLOPPER_PEARSON) == 72
    assert CLOPPER_PEARSON.upper(0, 72, 0.95) <= 0.05
    assert CLOPPER_PEARSON.upper(0, 71, 0.95) > 0.05


def test_only_wilson_reproduces_the_stated_eight_hundred_and_seventy_six():
    """The second, independent confirmation: 73 x 6 x 2 = 876."""
    assert R.tier1_total_labels(WILSON) == R.INHERITED_TIER1_TOTAL_LABELS == 876
    assert R.tier1_total_labels(CLOPPER_PEARSON) == 864


def test_wilson_is_not_an_exact_interval_and_clopper_pearson_is():
    assert WILSON.exact is False
    assert CLOPPER_PEARSON.exact is True


def test_the_two_intervals_genuinely_differ_at_the_deciding_sample_size():
    assert WILSON.upper(0, 72, 0.95) > 0.05 >= CLOPPER_PEARSON.upper(0, 72, 0.95)


# ------------------------------------------------- Clopper-Pearson correctness
def test_the_exact_interval_matches_its_closed_form_at_zero_errors():
    """With k = 0 the two-sided upper endpoint is 1 - (alpha/2)^(1/n)."""
    for n in (1, 10, 72, 100):
        expected = 1 - (0.025) ** (1 / n)
        assert CLOPPER_PEARSON.upper(0, n, 0.95) == pytest.approx(expected)


def test_the_exact_interval_is_degenerate_at_the_endpoints():
    assert CLOPPER_PEARSON.interval(0, 10, 0.95)[0] == 0.0
    assert CLOPPER_PEARSON.interval(10, 10, 0.95)[1] == 1.0


def test_the_exact_interval_covers_the_point_estimate():
    for k, n in [(1, 10), (5, 20), (17, 50)]:
        low, high = CLOPPER_PEARSON.interval(k, n, 0.95)
        assert low <= k / n <= high


def test_the_exact_interval_is_wider_than_wilson_where_it_matters():
    """That is the point of an exact interval near a boundary."""
    for n in (10, 30, 72):
        assert CLOPPER_PEARSON.upper(1, n, 0.95) >= WILSON.upper(1, n, 0.95)


@pytest.mark.parametrize("implementation", [WILSON, CLOPPER_PEARSON])
def test_the_upper_bound_decreases_as_the_denominator_grows(implementation):
    bounds = [implementation.upper(0, n, 0.95) for n in (10, 20, 50, 100, 200)]
    assert bounds == sorted(bounds, reverse=True)


# --------------------------------------------------------- argument validation
@pytest.mark.parametrize("implementation", [WILSON, CLOPPER_PEARSON])
def test_a_missing_denominator_is_missing_evidence_not_zero_error(implementation):
    for n in (0, -1):
        with pytest.raises(ValueError, match="missing evidence, not zero error"):
            implementation.interval(0, n, 0.95)


@pytest.mark.parametrize("implementation", [WILSON, CLOPPER_PEARSON])
def test_impossible_or_ill_typed_counts_are_refused(implementation):
    with pytest.raises(ValueError, match="not a possible count"):
        implementation.interval(11, 10, 0.95)
    with pytest.raises(ValueError, match="not a possible count"):
        implementation.interval(-1, 10, 0.95)
    with pytest.raises(ValueError, match="must be integers, not booleans"):
        implementation.interval(True, 10, 0.95)
    with pytest.raises(ValueError, match="must be integers"):
        implementation.interval(1.0, 10, 0.95)
    with pytest.raises(ValueError, match="confidence"):
        implementation.interval(0, 10, 1.5)


def test_an_unattainable_ceiling_is_reported_rather_than_returned():
    with pytest.raises(ValueError, match="no attainable sample size"):
        R.smallest_zero_error_n(1e-9, 0.95, WILSON, cap=100)
    with pytest.raises(ValueError, match="outside"):
        R.smallest_zero_error_n(0.0, 0.95, WILSON)


# ------------------------------------------------------------- the recovery row
def test_the_recovery_identifies_wilson_and_flags_the_contradiction():
    got = R.recover_inherited_interval()
    assert got["uniquely_recoverable"] is True
    assert got["identified_implementation"] == "wilson_score"
    assert got["satisfies_exact_binomial_description"] is False
    assert got["reproduces_inherited_count"] == ["wilson_score"]
    assert got["conflict"]
    assert "investigator decision" in got["conflict"]


def test_the_recovery_records_both_candidate_sample_sizes():
    rows = R.recover_inherited_interval()["by_implementation"]
    assert rows["wilson_score"]["n_at_zero_errors"] == 73
    assert rows["clopper_pearson"]["n_at_zero_errors"] == 72


def test_the_recovery_records_the_mis_cited_register_row():
    """Section 10.4 says D9; D9 is the construction bootstrap."""
    got = R.recover_inherited_interval()
    assert got["register_row_cited"] == "D9"
    assert got["register_row_matches"] is False
    assert "construction bootstrap" in got["register_row_actual_subject"]


def test_the_recovery_is_serialisable_for_the_artifact_trail():
    import json
    json.dumps(R.recover_inherited_interval())


# ------------------------------------------------------- the slot stays pending
def test_the_interval_slot_is_accepted_by_record_rather_than_declared():
    """A3 is accepted, so the slot is FROZEN by a record naming who accepted it."""
    from dci.v19 import registry
    from dci.v19.resolution import Resolution
    slot = REGISTRY.slots["verifiers.binomial_interval_implementation"]
    assert slot.resolution is Resolution.FROZEN
    assert slot.get() == R.AMENDED_INTERVAL == "clopper_pearson"
    assert slot.frozen_by
    # The DECLARATION still leaves it open: implemented is not accepted.
    declared = registry.declared_table()["verifiers.binomial_interval_implementation"]
    assert declared.resolution is Resolution.PENDING_DECISION
    assert declared.status == "BLOCKED_BY_PROSPECTIVE_DECISION"

def test_the_frozen_interval_is_the_exact_one():
    """A3 accepted, so frozen_interval returns Clopper-Pearson rather than raising."""
    assert R.frozen_interval(REGISTRY.slots) is R.CLOPPER_PEARSON
    assert R.frozen_interval(REGISTRY.slots).exact is True


def test_an_unfrozen_interval_still_fails_closed_with_the_decision():
    """The fail-closed path is still live for a registry without the record."""
    from dci.v19 import registry
    with pytest.raises(R.ReliabilityBlocked) as caught:
        R.frozen_interval(registry.declared_table())
    message = str(caught.value)
    assert "not frozen" in message
    assert "wilson_score" in message and "clopper_pearson" in message


@pytest.mark.parametrize("choice", ["wilson_score", "clopper_pearson"])
def test_either_choice_would_have_resolved_the_interval(choice):
    """Applied to the DECLARED table: the accepted slot refuses to be re-frozen."""
    from dci.v19 import registry
    table = registry.declared_table().freeze(
        "verifiers.binomial_interval_implementation", choice, by="a probe")
    assert R.frozen_interval(table) is R.INTERVAL_IMPLEMENTATIONS[choice]


def test_an_unimplemented_interval_name_is_refused_by_the_slot_domain():
    from dci.v19 import registry
    with pytest.raises(ValueError, match="not admissible for domain"):
        registry.declared_table().freeze(
            "verifiers.binomial_interval_implementation", "bootstrap_t",
            by="a probe")

def test_a_certificate_needs_an_explicit_interval():
    with pytest.raises(ReliabilityBlocked, match="no default"):
        tier_certificate("p1.target", false_passes=0, true_failures=73,
                         false_fails=0, true_passes=73,
                         implementation="wilson_score")


def test_both_truth_classes_at_zero_errors_and_the_planning_count_pass():
    got = tier_certificate("p3.target", false_passes=0, true_failures=73,
                           false_fails=0, true_passes=73, implementation=WILSON)
    assert got.passed and not got.unavailable
    assert [b.truth_class for b in got.bounds] == list(R.TIER1_TRUTH_CLASSES)


@pytest.mark.parametrize("missing", ["true_failures", "true_passes"])
def test_an_absent_truth_class_is_missing_evidence_not_zero_error(missing):
    """Section 10.4: the bound is unavailable and the unit cannot pass."""
    counts: dict[str, object] = {"false_passes": 0, "true_failures": 73,
                                 "false_fails": 0, "true_passes": 73}
    if missing == "true_failures":
        counts.update(true_failures=0, false_passes=None)
    else:
        counts.update(true_passes=0, false_fails=None)
    got = tier_certificate("p2.focal", implementation=WILSON, **counts)
    assert not got.passed
    assert got.unavailable == (missing,)
    unavailable = next(b for b in got.bounds if b.truth_class == missing)
    assert unavailable.upper is None
    assert "missing evidence, not zero error" in unavailable.reason


def test_a_denominator_without_an_error_count_is_also_unavailable():
    got = tier_certificate("p2.focal", false_passes=None, true_failures=73,
                           false_fails=0, true_passes=73, implementation=WILSON)
    assert not got.passed and got.unavailable == ("true_failures",)
    assert "no error count" in got.bounds[0].reason


def test_one_error_in_the_planning_count_exceeds_the_ceiling():
    got = tier_certificate("p1.focal", false_passes=1, true_failures=73,
                           false_fails=0, true_passes=73, implementation=WILSON)
    assert not got.passed
    assert got.bounds[0].available and got.bounds[0].upper > R.TIER1_CEILING


def test_the_tier_two_ceiling_is_looser_and_says_so():
    """Section 10.4's Tier 2 is a coarser 20% per-stratum ceiling."""
    evidence = {"false_passes": 0, "true_failures": 30,
                "false_fails": 0, "true_passes": 30}
    at_tier1 = tier_certificate("reference.stratum", implementation=WILSON,
                                ceiling=R.TIER1_CEILING, **evidence)
    at_tier2 = tier_certificate("reference.stratum", implementation=WILSON,
                                ceiling=R.TIER2_PER_STRATUM_CEILING, **evidence)
    # 30 adjudicated labels per class is not enough for a 5% ceiling and is
    # comfortably enough for 20%, which is the coarser system-level claim.
    assert not at_tier1.passed and at_tier2.passed
    assert at_tier1.bounds[0].upper == at_tier2.bounds[0].upper


def test_the_certificate_records_which_interval_produced_it():
    for implementation in (WILSON, CLOPPER_PEARSON):
        got = tier_certificate("p1.target", false_passes=0, true_failures=73,
                               false_fails=0, true_passes=73,
                               implementation=implementation)
        assert got.interval == implementation.name


def test_the_two_intervals_can_disagree_on_the_same_evidence():
    """Which is exactly why the choice cannot be left to the implementation."""
    at_72 = {"false_passes": 0, "true_failures": 72, "false_fails": 0,
             "true_passes": 72}
    assert not tier_certificate("p1.target", implementation=WILSON,
                                **at_72).passed
    assert tier_certificate("p1.target", implementation=CLOPPER_PEARSON,
                            **at_72).passed


def test_the_certificate_is_serialisable():
    import json
    got = tier_certificate("p1.target", false_passes=0, true_failures=73,
                           false_fails=None, true_passes=0,
                           implementation=WILSON)
    described = got.describe()
    json.dumps(described)
    assert described["passed"] is False
    assert described["unavailable"] == ["true_passes"]
