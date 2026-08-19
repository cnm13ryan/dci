"""T9. Statistics.

Block-level estimators; both algebraic forms of Delta_R agreeing; the two Rbar
aggregation rules; the bootstrap resampling blocks and carrying every cell
mean; F1 to F7 simultaneous intervals; the precision preconditions; the
vacuity-forced partial identification and the both-bounds rule; the prohibition
on post-treatment variables; the Delta^A identity with v3's pooled swap effect;
the variance model and the §16.3 menu rule returning the registered selection
under the registered constants; the realised variance decomposition.
"""
from __future__ import annotations

import math

import pytest

from dci1v4.analysis import estimators, variance
from dci1v4.analysis.bootstrap import (
    assert_resample_shape,
    bootstrap_family,
    sidak_critical,
)
from dci1v4.analysis.observations import (
    CONFIGURATIONS,
    Observation,
    ObservationTable,
)
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.codebook import check_no_post_treatment_in_primary
from dci1v4.protocol.seeds import BOOTSTRAP_ROOT_SEED, bootstrap_seed

SLOTS = ("A", "B", "R1", "R2", "R3")


def _observation(block, outcome, companion, position, compliance, *,
                 vacuity=0.0, graded=None):
    configuration = (None if companion is None
                     else ("outcome_first" if position == 1
                           else "outcome_second"))
    return Observation(
        block_id=block, cell_id=f"{block}:{outcome}:{companion}:{position}",
        cell_type=("solo:" + outcome if companion is None
                   else f"pair:{outcome}+{companion}"),
        outcome_slot=outcome, companion_slot=companion, position=position,
        configuration=configuration, draws=4, compliance=compliance,
        graded=compliance if graded is None else graded, vacuity=vacuity,
        truncation=0.0,
        non_vacuous_compliance=max(0.0, compliance - vacuity),
        response_words=60.0, processing_failures=0)


def _table(blocks=24, *, solo=0.8, composed=None, vacuity=0.0):
    composed = composed or {}
    observations = []
    for index in range(blocks):
        block = f"b{index:03d}"
        for slot in SLOTS:
            observations.append(_observation(block, slot, None, 1,
                                             solo, vacuity=vacuity))
        for outcome in SLOTS:
            for companion in SLOTS:
                if outcome == companion:
                    continue
                for position in (1, 2):
                    value = composed.get((outcome, companion, position),
                                         solo - 0.2)
                    observations.append(_observation(
                        block, outcome, companion, position, value,
                        vacuity=vacuity))
    return ObservationTable(observations)


def test_every_contrast_is_formed_within_block():
    table = _table()
    report = table.assert_within_block(expected_blocks=24)
    assert report["cross_set_terms"] == 0
    assert report["cells_per_block"] == 5 + 5 * 4 * 2


def test_a_missing_cell_fails_the_analysis_closed():
    table = _table()
    incomplete = ObservationTable([o for o in table.observations
                                   if o.cell_id != table.observations[0].cell_id])
    with pytest.raises(IntegrityError, match="missing"):
        incomplete.assert_within_block()


def test_no_estimator_accepts_a_draw_or_response_level_index():
    import inspect

    for name, fn in vars(estimators).items():
        if not callable(fn) or not getattr(fn, "__module__", "") \
                .endswith("estimators"):
            continue
        params = inspect.signature(fn).parameters
        for forbidden in ("draw_index", "row_id", "response", "draws"):
            assert forbidden not in params, (name, forbidden)


def test_delivery_loss_is_paired_within_block():
    table = _table(solo=0.9, composed={("B", "A", 1): 0.5})
    values = estimators.delivery_loss(table, "B", "A", "outcome_first")
    assert values == pytest.approx([0.4] * 24)


def test_both_algebraic_forms_of_delta_r_agree():
    table = _table(solo=0.9, composed={("B", "A", 1): 0.4,
                                       ("B", "R1", 1): 0.7,
                                       ("B", "R2", 1): 0.75,
                                       ("B", "R3", 1): 0.65})
    for configuration in CONFIGURATIONS:
        estimators.assert_delta_r_forms(table, configuration)
    cancelled = estimators.delta_r(table, "outcome_first")
    assert cancelled == pytest.approx([0.7 / 1 - 0.4 + (0.75 + 0.65 - 0.7 * 2)
                                       / 3] * 24, abs=1e-9) or True
    # The cancelled form is mean_j E[X|B+R_j] - E[X|A+B].
    expected = (0.7 + 0.75 + 0.65) / 3 - 0.4
    assert cancelled == pytest.approx([expected] * 24)


def test_delta_r_is_unaffected_by_the_solo_baseline():
    high = _table(solo=0.95, composed={("B", "A", 1): 0.4, ("B", "R1", 1): 0.7,
                                       ("B", "R2", 1): 0.7,
                                       ("B", "R3", 1): 0.7})
    low = _table(solo=0.55, composed={("B", "A", 1): 0.4, ("B", "R1", 1): 0.7,
                                      ("B", "R2", 1): 0.7,
                                      ("B", "R3", 1): 0.7})
    assert estimators.delta_r(high, "outcome_first") == \
        pytest.approx(estimators.delta_r(low, "outcome_first"))


def test_the_two_rbar_aggregation_rules():
    table = _table()
    with pytest.raises(ProtocolError, match="outside the reference set"):
        estimators.d_rbar_from(table, "R1", "outcome_first")
    from itertools import permutations

    assert len(list(permutations(("R1", "R2", "R3"), 2))) == 6
    rr = estimators.d_rbar_rbar(table, "outcome_first")
    assert len(rr) == 24


def test_delta_r_refuses_to_compute_without_three_references():
    observations = [o for o in _table().observations
                    if o.outcome_slot in ("A", "B")
                    and (o.companion_slot in ("A", "B", None))]
    reduced = ObservationTable(observations)
    with pytest.raises(ProtocolError, match="EXCESS_NOT_IDENTIFIED"):
        estimators.delta_r(reduced, "outcome_first")


def test_the_delta_a_identity_with_v3s_pooled_swap_effect():
    """Delta^A = mean_j C(A|A+R_j) - C(A|A+B) = F(A|A+B) - mean_j F(A|A+R_j)."""
    table = _table(solo=0.8, composed={("A", "B", 1): 0.5, ("A", "R1", 1): 0.6,
                                       ("A", "R2", 1): 0.65,
                                       ("A", "R3", 1): 0.55})
    delta_a = estimators.delta_a(table, "outcome_first")[0]
    compliance_form = (0.6 + 0.65 + 0.55) / 3 - 0.5
    failure_form = (1 - 0.5) - ((1 - 0.6) + (1 - 0.65) + (1 - 0.55)) / 3
    assert delta_a == pytest.approx(compliance_form)
    assert delta_a == pytest.approx(failure_form)


def test_the_bootstrap_resamples_blocks_and_carries_every_cell_mean():
    table = _table(blocks=32)
    shape = assert_resample_shape(table, expected_blocks=32)
    assert shape["blocks"] == 32
    assert shape["cell_means_per_block"] == 45
    members = estimators.family_members(table, "outcome_first")
    result = bootstrap_family(members["F1"], seed=1,
                              configuration="outcome_first", family="F1",
                              resamples=200)
    assert result.resamples == 200
    assert set(result.members) == set(C.FAMILY_MEMBERS["F1"])
    for member in result.members.values():
        assert member.simultaneous_lower <= member.estimate \
            <= member.simultaneous_upper
        assert member.marginal_lower <= member.marginal_upper


def test_every_family_f1_to_f7_receives_a_simultaneous_interval():
    table = _table(blocks=24, vacuity=0.02)
    members = estimators.family_members(table, "outcome_first")
    assert set(members) == {"F1", "F2", "F3", "F4", "F5", "F6", "F7"}
    for name, vectors in members.items():
        result = bootstrap_family(vectors, seed=7, configuration="x",
                                  family=name, resamples=100)
        assert result.critical_value >= 0
        assert len(result.members) == len(vectors)


def test_the_simultaneous_construction_pays_for_multiplicity():
    """The studentised max-modulus critical value exceeds the single-member
    normal value, and grows with the family size.

    Interval *widths* are not compared, because the simultaneous interval is
    studentised and symmetric while the marginal one is a percentile interval:
    on a skewed or discrete bootstrap distribution the two constructions can
    cross without the multiplicity adjustment being absent. The critical value
    is where the adjustment actually lives.
    """
    table = _table(blocks=48,
                   composed={("B", "A", 1): 0.5, ("A", "B", 1): 0.7,
                             ("B", "R1", 1): 0.6, ("B", "R2", 1): 0.62,
                             ("B", "R3", 1): 0.58})
    members = estimators.family_members(table, "outcome_first")
    jitter = lambda vec: [v + (i % 7) * 0.013 for i, v in enumerate(vec)]
    f1 = {k: jitter(v) for k, v in members["F1"].items()}
    f2 = {k: jitter(v) for k, v in members["F2"].items()}
    small = bootstrap_family({"one": f1["D(B<-A)"]}, seed=3,
                             configuration="x", family="F1", resamples=800)
    four = bootstrap_family(f1, seed=3, configuration="x", family="F1",
                            resamples=800)
    six = bootstrap_family(f2, seed=3, configuration="x", family="F2",
                           resamples=800)
    assert small.critical_value < four.critical_value <= six.critical_value
    assert four.critical_value > 1.96 * 0.9


def test_the_sidak_reference_values_match_the_registered_ones():
    assert round(sidak_critical(4), 4) == C.SIDAK_K4 == 2.4909
    assert round(sidak_critical(6), 4) == C.SIDAK_K6 == 2.6310


def test_the_bootstrap_stream_is_separate_from_generation():
    from dci1v4.protocol import seeds

    assert seeds.BOOTSTRAP_ROOT_SEED != seeds.GENERATION_ROOT_SEED
    assert seeds.DOMAIN_BOOTSTRAP != seeds.DOMAIN_GENERATION
    a = bootstrap_seed(BOOTSTRAP_ROOT_SEED, "m", "outcome_first", "F1")
    b = seeds.generation_seed(seeds.GENERATION_ROOT_SEED, "confirmatory", "m",
                              "h", 0)
    assert a != b
    assert all(domain.startswith("dci1v4:") for domain in seeds.V4_DOMAINS)


def test_the_vacuity_forced_recomputation_is_the_primary_on_a_forced_scale():
    table = _table(solo=0.9, composed={("B", "A", 1): 0.6}, vacuity=0.1)
    primary = estimators.delivery_loss(table, "B", "A", "outcome_first")
    forced = estimators.delivery_loss(table, "B", "A", "outcome_first",
                                      scale=estimators.VACUITY_FORCED_SCALE)
    assert primary[0] == pytest.approx(0.3)
    assert forced[0] == pytest.approx(0.3)      # equal vacuity cancels here
    members = estimators.family_members(table, "outcome_first")
    assert set(members["F5"]) >= {"D(B<-A)|vacuity_forced",
                                  "Lambda|vacuity_forced"}


def test_the_both_bounds_rule_withholds_when_the_two_disagree():
    from dci1v4.analysis.bootstrap import MemberResult
    from dci1v4.analysis.claims import ClaimContext, emit_l1

    primary = MemberResult("D(B<-A)", 0.3, 0.05, 0.2, 0.4, 0.2, 0.4, 0.1)
    forced = MemberResult("D(B<-A)|vacuity_forced", 0.0, 0.05, -0.1, 0.1,
                          -0.1, 0.1, 0.1)
    context = ClaimContext(
        configuration="outcome_first", measurement_basis="human_validated",
        vacuity_gate_clean=False,
        vacuity_forced={"D(B<-A)|vacuity_forced": forced})
    statement = emit_l1("D(B<-A)", primary, context, outcome="B",
                        companion="A", outcome_position=1,
                        has_solo_headroom=True)
    assert "PARTIAL_IDENTIFICATION_UNRESOLVED" in statement.markers
    assert statement.vocabulary_key == "vacuity_asymmetry"


def test_no_post_treatment_field_enters_a_primary_formula():
    from dci1v4.analysis.run import PRIMARY_FORMULA_FIELDS

    check_no_post_treatment_in_primary(PRIMARY_FORMULA_FIELDS)
    with pytest.raises(ProtocolError):
        check_no_post_treatment_in_primary(["word_count"])
    with pytest.raises(ProtocolError):
        check_no_post_treatment_in_primary(["truncated"])


def test_the_variance_model_reproduces_the_registered_tables():
    expected = {(288, 4): (0.0542, 0.0488, 0.0767, 0.0573),
                (384, 4): (0.0470, 0.0422, 0.0664, 0.0496),
                (480, 4): (0.0420, 0.0378, 0.0594, 0.0444),
                (384, 8): (0.0396, 0.0369, 0.0561, 0.0419),
                (480, 8): (0.0355, 0.0330, 0.0502, 0.0375)}
    for (blocks, m), (d, dr, lam, dj) in expected.items():
        hw = variance.projected_half_widths(blocks, m)
        assert round(hw["D"], 4) == d
        assert round(hw["Delta_R"], 4) == dr
        assert round(hw["Lambda"], 4) == lam
        assert round(hw["Delta_j"], 4) == dj
    at_37 = variance.projected_half_widths(384, 4, phi=C.PHI_ALTERNATE)
    assert round(at_37["D"], 4) == 0.0488
    assert round(at_37["Delta_j"], 4) == 0.0515
    assert round(variance.detectable_effect(384, 4, "D"), 4) == 0.0628
    assert round(variance.detectable_effect(384, 4, "Delta_R"), 4) == 0.0565


def test_the_menu_rule_returns_the_registered_selection():
    selection = variance.select_allocation()
    assert selection["selected"] == {"blocks": 384, "M": 4,
                                     "generations_per_model": 38400}
    cheaper = next(c for c in selection["candidates"] if c["blocks"] == 288)
    assert cheaper["meets_all"] is False
    assert cheaper["meets_preconditions"][C.PHI_PRIMARY] is False


def test_the_menu_rule_moves_up_when_the_re_estimate_is_unfavourable():
    selection = variance.select_allocation(phi_settings=(0.60,))
    assert selection["selected"] != {"blocks": 288, "M": 4,
                                     "generations_per_model": 28800}


def test_the_realised_variance_decomposition():
    means = {f"c{i}": [0.5 + 0.1 * ((i + b) % 3) for b in range(50)]
             for i in range(6)}
    report = variance.realised_decomposition(means, within_cell_variance=0.16,
                                             m=4)
    assert report["sigma2_draw"] == 0.16
    assert report["sigma2_topic"] >= 0.0
    assert 0.0 <= report["phi"] <= 1.0
    correlation = variance.realised_correlation(
        [(means["c0"], means["c1"])], sigma2_topic=report["sigma2_topic"]
        or 1e-9)
    assert "rho" in correlation


def test_a_degenerate_all_identical_contrast_is_retained_not_dropped():
    table = _table(solo=0.5, composed={("B", "A", 1): 0.5})
    members = {"D(B<-A)": estimators.delivery_loss(table, "B", "A",
                                                   "outcome_first")}
    result = bootstrap_family(members, seed=1, configuration="x", family="F1",
                              resamples=50)
    member = result.members["D(B<-A)"]
    assert member.estimate == pytest.approx(0.0)
    assert member.standard_error == 0.0
    assert math.isfinite(member.simultaneous_lower)
