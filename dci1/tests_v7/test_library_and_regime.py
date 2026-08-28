"""The registered library, §12's screen, and the decisions that block them."""
from __future__ import annotations

import dataclasses

import pytest

from dci1v4.errors import InstrumentError, ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions
from dci1v7.stages import regime
from dci1v7.verifiers import constraints as K


def test_the_registered_library_sizes():
    """§7.10's four counts, asserted rather than described."""
    assert K.assert_library_sizes() == {
        "families": 40, "round_0_severities": 350,
        "declared_severities": 656, "instruments": 674, "verifiers": 42,
        # New in v6. Three `probe_only` stand-ins are authored (§34 D24), so
        # the library counts moved --- and the three counts below are why
        # that is safe: the pool §12.2 screens, §12.6 expands and §12.7
        # calibrates is unmoved at v5's 37 families, 326 round-0 severities
        # and 632 declared severities. Authoring a stand-in that reached the
        # selectable pool would move one of them and fail here.
        "probe_only_families": 3, "selectable_families": 37,
        "selectable_round_0_severities": 326,
        "selectable_declared_severities": 632,
        "probe_only_severities": 24}


def test_a_probe_only_family_is_outside_every_selectable_pool():
    """§34 D24's three stand-ins are registered and are not selectable.

    Every route a family can take into a selection is checked, because the
    guarantee is not "the flag exists" but "no pool contains one".
    """
    assert K.PROBE_ONLY_FAMILY_IDS == ("PS1", "PS2", "PS3")
    assert set(K.SELECTABLE_FAMILY_IDS) == (set(K.FAMILY_IDS)
                                            - {"PS1", "PS2", "PS3"})
    assert K.assert_no_probe_only_selection_path()["found"] == []
    pools = (K.TIER1_FAMILY_IDS, K.TIER2_FAMILY_IDS, K.TIER3_FAMILY_IDS,
             K.SELECTABLE_FAMILY_IDS)
    for pool in pools:
        assert set(pool).isdisjoint(K.PROBE_ONLY_FAMILY_IDS)
    for kind in K.PROBE_ONLY_FAMILY_IDS:
        assert K.is_probe_only(kind)
        with pytest.raises(InstrumentError):
            K.assert_selectable(kind, where="a test")
    # And they are in the library proper: same verifier, same hash, same
    # certification path. A stand-in scored by something else would not be
    # measuring what §13.14 measures.
    for kind in K.PROBE_ONLY_FAMILY_IDS:
        assert kind in K.FAMILIES
        assert kind in K.KINDS
        assert K.LADDERS[kind] == K.RESERVES[kind]


def test_no_standin_shares_a_form_with_a_selectable_family_of_its_group():
    """§34 D24 S2, as the property that actually needs to hold.

    A stand-in must never be instrument-identical to something that could be
    selected. It shares a feature group with a selectable family by design ---
    a new group would reorder `FEATURE_GROUP_IDS` and with it
    `selection.group_key`'s tie-break --- so what separates them is the
    (statistic, form) pair, and that is what is asserted.
    """
    taken = {(K.FAMILIES[k].statistic_id, K.FAMILIES[k].form)
             for k in K.SELECTABLE_FAMILY_IDS}
    for kind in K.PROBE_ONLY_FAMILY_IDS:
        family = K.FAMILIES[kind]
        assert (family.statistic_id, family.form) not in taken
        assert family.statistic_id in K.STATISTIC_IDS


def test_authoring_the_standins_did_not_move_the_feature_group_index():
    """The reason S3's group requirement was dropped, as an assertion.

    `selection._group_order` reads a group's **index** in a sorted tuple as a
    reference-selection tie-break, so a stand-in in a new group would reorder
    the tie-break for every selectable family sorting after it.
    """
    from dci1v7.stages import selection

    assert K.FEATURE_GROUP_IDS == tuple(sorted(set(K.FEATURE_GROUPS.values())))
    assert len(K.FEATURE_GROUP_IDS) == 21
    groups = {K.FAMILIES[k].feature_group for k in K.PROBE_ONLY_FAMILY_IDS}
    assert groups <= {K.FAMILIES[k].feature_group
                      for k in K.SELECTABLE_FAMILY_IDS}
    # The index every selectable family sorts at is unchanged, which is the
    # property the requirement was dropped to preserve.
    for kind in K.SELECTABLE_FAMILY_IDS:
        assert selection._group_order(kind) == K.FEATURE_GROUP_IDS.index(
            K.FAMILIES[kind].feature_group)


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
    for _kind, family in K.FAMILIES.items():
        if family.form in (K.FORM_EXACT, K.FORM_RATE):
            assert 0 not in family.reserve


def test_rate_lower_bound_is_instantiated_by_exactly_one_probe_only_family():
    """The form was registered and exercised by nothing until §34 D24.

    PS3 is the only instrument in the library that certifies it, which is a
    reason to have chosen it and not an accident: a registered predicate form
    with no instance is a form whose verifier no Gate-1 suite ever runs.
    """
    assert K.FORM_RATE_LOWER_BOUND in K.FORMS
    carriers = [k for k, f in K.FAMILIES.items()
                if f.form == K.FORM_RATE_LOWER_BOUND]
    assert carriers == ["PS3"]
    assert not any(K.FAMILIES[k].form == K.FORM_RATE_LOWER_BOUND
                   for k in K.SELECTABLE_FAMILY_IDS)


def test_the_marker_vocabulary_is_approved_and_frozen(restore_decisions):
    """§34 D4 is closed at `approve_eight`, and the eight are bound by hash.

    The guard still refuses if D4 goes away: approving the vocabulary is what
    made the regime screen reachable, and it did not stop being a decision by
    being taken.
    """
    assert len(K.assert_marker_vocabulary_approved()) == 8
    population = K.marker_population()
    assert population["value"] == "approve_eight"
    assert population["population_hash"] == K.marker_population_hash()
    assert len(population["markers"]) == 8
    assert len(population["roles"]) == 6

    restore_decisions.DECISIONS["D4"] = dataclasses.replace(
        restore_decisions.DECISIONS["D4"], value=decisions.UNRESOLVED)
    with pytest.raises(decisions.DecisionOpenError):
        K.assert_marker_vocabulary_approved()


def test_the_frozen_population_names_the_limitations_it_accepted():
    """§34 D4's closure accepted judgements; it did not answer them.

    They are recorded so that a reader of an L3 statement sees them, which is
    where the audit says they belong --- and so that "approved" cannot be read
    as "no concern was found".
    """
    accepted = {x["word"]: x for x in K.D4_ACCEPTED_LIMITATIONS}
    assert {"though", "namely", "overall", "*"} == set(accepted)
    for entry in K.D4_ACCEPTED_LIMITATIONS:
        assert entry["criterion"] and entry["limitation"]
        assert entry["accepted_because"]
    assert "closest single-word" in accepted["though"]["limitation"]
    assert "two productive syntactic frames" in accepted["though"][
        "limitation"]
    assert "appositive" in accepted["namely"]["limitation"]
    assert "0.076-0.112" in accepted["overall"]["limitation"]


def test_the_population_hash_moves_if_a_marker_moves(monkeypatch):
    """A substitution is forbidden; the hash is what makes it detectable."""
    before = K.marker_population_hash()
    monkeypatch.setitem(K.MARKER_WORDS, "marker_though", "albeit")
    assert K.marker_population_hash() != before


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


def test_the_construct_floor_is_registered_and_still_a_decision(
        restore_decisions):
    """§34 D17 closed at `floor`; the rule applies and the guard remains."""
    out = regime.assert_construct_floor(13, chance_compliance_at_m_star=0.3)
    assert out["floor_registered"] is True
    assert out["floor"]["quantity"] == "chance_compliance"
    assert out["floor"]["value"] == 0.50
    assert out["satisfied"] and not out["selection_refused"]

    restore_decisions.DECISIONS["D17"] = dataclasses.replace(
        restore_decisions.DECISIONS["D17"], value=decisions.UNRESOLVED)
    with pytest.raises(decisions.DecisionOpenError):
        regime.assert_construct_floor(13, chance_compliance_at_m_star=0.3)


def test_the_coverage_criterion_separates_decisive_from_arm_dropping():
    assert C.COVERAGE_DECISIVE == ("C1", "C2", "C3", "C4", "C5", "C6")
    table = [{"candidate": "x", "family": "MK1", "structural_tier": 1,
              "feature_group": "marker_thus", "constraint_class": "production",
              "iota": 0.5, "eligible": True}]
    out = regime.coverage_criterion(table, iota_a=0.7)
    assert out["decisive_met"] is False
    assert set(out["identification_statuses"]) == {
        "CLASS_ARM_NOT_AVAILABLE", "NEAR_FORM_ARM_NOT_AVAILABLE"}


def _rows(family, iota_by, *, eligible=True):
    """A coverage-row table in the shape §12.6's criterion actually reads."""
    return [{"candidate": f"{family}:{q}", "family": family, "severity": q,
             "structural_tier": K.FAMILIES[family].structural_tier,
             "feature_group": K.FAMILIES[family].feature_group,
             "constraint_class": K.FAMILIES[family].constraint_class,
             "iota": v, "eligible": eligible}
            for q, v in sorted(iota_by.items())]


def test_expansion_extends_toward_the_deficient_side():
    """Higher q is HARDER for an exact count, so easier means lower q.

    Both one-sided cases, unchanged from v5: the deficiency is
    ``MISSING_SIDE`` and the direction is by restrictiveness, not by raw
    severity.
    """
    # every measured rung is harder than A: the expansion must go EASIER.
    table = _rows("MK1", {q: 0.40 - 0.04 * q for q in range(4, 9)})
    plan = regime.expansion_round(table, iota_a=0.60,
                                  measured={"MK1": list(range(4, 9))})
    assert plan["by_deficiency"]["MISSING_SIDE"] == ["MK1"]
    picks = plan["admitted"]["MK1"]
    assert set(picks) <= set(K.RESERVES["MK1"])
    assert max(picks) < 4
    assert len(picks) <= C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND

    # every measured rung is easier than A: the expansion must go HARDER, and
    # §7.10's reserve to 12 is what it reaches into.
    easier = _rows("MK1", {q: 0.95 - 0.02 * q for q in range(1, 9)})
    harder = regime.expansion_round(easier, iota_a=0.50,
                                    measured={"MK1": list(range(1, 9))})
    assert set(harder["admitted"]["MK1"]) <= {9, 10, 11, 12}


def test_v6_e01_a_short_span_extends_outward_where_v5_interpolated():
    """V6-E01: the branch that can raise a span, and the one that cannot.

    C4's span is ``max(iota) - min(iota)`` over a family's eligible rungs, so
    a rung admitted strictly *between* two measured edges cannot raise it.
    v5 had only the interpolating branch for a straddling family, and on all
    four signed pre-screen tables it admitted no Tier-1 reserve rung in either
    round. Here the family straddles iota_A with three rungs and a span of
    0.15 --- so C4's first unmet condition is the span --- and the plan has to
    reach *outside* the measured range.
    """
    iota_a = 0.60
    table = _rows("MK1", {3: 0.70, 4: 0.66, 5: 0.55})
    state = regime.family_c4_state(table, iota_a=iota_a)
    assert state["has_below"] and state["has_above"] and state["n_rungs"] == 3
    assert state["span"] < C.COVERAGE_MIN_WITHIN_FAMILY_SPAN
    assert regime.family_deficiency(state) == "SPAN_SHORT"

    plan = regime.expansion_plan_for_family(
        "MK1", entries=table, measured=[3, 4, 5], iota_a=iota_a)
    assert plan["deficiency"] == "SPAN_SHORT"
    assert plan["direction"] == "OUTWARD_BOTH"
    assert plan["picks"], "a short span with reserve on both sides must pick"
    assert set(plan["picks"]) <= set(K.RESERVES["MK1"]) - {3, 4, 5}
    # Outward on BOTH sides: something harder than 5 and something easier
    # than 3. Nothing strictly between them, which is all v5 could offer.
    assert any(q > 5 for q in plan["picks"])
    assert any(q < 3 for q in plan["picks"])
    assert not any(3 < q < 5 for q in plan["picks"])
    assert len(plan["picks"]) <= C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND


def test_v6_e01_a_family_meeting_c4_is_skipped():
    """A family that already contributes a straddling group buys nothing."""
    table = _rows("MK1", {2: 0.90, 5: 0.62, 8: 0.20})
    plan = regime.expansion_plan_for_family(
        "MK1", entries=table, measured=[2, 5, 8], iota_a=0.60)
    assert plan["deficiency"] is None
    assert plan["direction"] == "NONE"
    assert plan["picks"] == []


def test_v6_e01_too_few_rungs_still_interpolates():
    """The v5 branch survives where it is the right one.

    A straddling family with two rungs and a wide span fails C4 on the rung
    COUNT, and interpolation is exactly what fixes that.
    """
    table = _rows("MK1", {2: 0.90, 7: 0.20})
    plan = regime.expansion_plan_for_family(
        "MK1", entries=table, measured=[2, 7], iota_a=0.60)
    assert plan["deficiency"] == "TOO_FEW_RUNGS"
    assert plan["direction"] == "INTERPOLATE"
    assert all(2 < q < 7 for q in plan["picks"])


def test_v6_e01_the_plan_is_deterministic_and_reads_only_iota_and_severity():
    table = _rows("MK1", {3: 0.70, 4: 0.66, 5: 0.55})
    first = regime.expansion_plan_for_family(
        "MK1", entries=table, measured=[3, 4, 5], iota_a=0.60)
    second = regime.expansion_plan_for_family(
        "MK1", entries=list(reversed(table)), measured=[5, 4, 3],
        iota_a=0.60)
    assert first["picks"] == second["picks"]


def test_v6_e01_non_monotonic_iota_is_a_measurement_not_an_error():
    """MK1 on gemma-3n-e2b-it ran 0.581, 0.792, 0.792, 0.750, 0.541, 0.458,
    0.416, 0.417 --- iota is measurably non-monotonic in severity.

    The rule therefore orders CANDIDATES by restrictiveness, a structural
    property of the predicate known before any data, and evaluates the
    DEFICIENCY on measured iota afterwards.
    """
    realised = {1: 0.581, 2: 0.792, 3: 0.792, 4: 0.750, 5: 0.541,
                6: 0.458, 7: 0.416, 8: 0.417}
    table = _rows("MK1", realised)
    plan = regime.expansion_plan_for_family(
        "MK1", entries=table, measured=sorted(realised), iota_a=0.60)
    assert plan["deficiency"] == "SPAN_SHORT"
    assert set(plan["picks"]) <= {9, 10, 11, 12}
    assert plan["picks"], "the whole reserve lies harder than q = 8"


def test_v6_e02_a_row_the_criterion_would_drop_is_refused():
    """V6-E02: `coverage_criterion` filters on `eligible` before anything.

    v5's ``run_expansion`` extended its table with raw difficulty rows, which
    carry no ``eligible`` field, so every rung the expansion measured was
    counted as ineligible by the criterion it was measured to satisfy. The
    invariant is on the mandatory path now.
    """
    good = _rows("MK1", {3: 0.70})
    regime.assert_coverage_shape(good, where="test")
    raw = [{"candidate": "MK1:9", "family": "MK1", "severity": 9,
            "iota": 0.30}]
    with pytest.raises(ProtocolError) as excinfo:
        regime.assert_coverage_shape(raw, where="test")
    assert "eligible" in str(excinfo.value)


def test_expansion_never_authors_outside_the_frozen_reserve():
    table = [{"family": "RF1", "severity": q, "iota": 0.20 + 0.05 * q,
              "candidate": f"RF1:{q}"} for q in range(0, 9)]
    plan = regime.expansion_round(table, iota_a=0.90,
                                  measured={"RF1": list(range(0, 9))})
    assert set(plan["admitted"].get("RF1", ())) <= set(K.RESERVES["RF1"])


def test_the_calibration_b_bank_exists_and_still_has_to_pass(
        restore_decisions):
    """§34 D3 is closed and the work behind it was done.

    The refusal path is still live: hand the entry point a bank that is not
    96 verified questions and it refuses, which is what stops a closed
    decision from standing in for the questions themselves.
    """
    from dci1v7 import topics

    assert topics.calibration_b_status() == "AUTHORED"
    assert len(topics.calibration_b_bank()) == 96
    with pytest.raises(ProtocolError, match="96 questions"):
        topics.calibration_b_bank([{"topic_id": "x", "area": "food",
                                    "set": "calibration_b",
                                    "question": "Why?"}])
    restore_decisions.override_for_testing("D3", "author_after_adoption")
    with pytest.raises(ProtocolError, match="author after adoption"):
        topics.calibration_b_bank()


def test_the_topic_bank_shape_is_720_in_six_sets():
    from dci1v7 import topics

    assert sum(topics.SET_SIZES.values()) == 720
    assert topics.SET_SIZES[C.CALIBRATION_A] == 96
    assert topics.SET_SIZES[C.CALIBRATION_B] == 96
    with pytest.raises(ProtocolError):
        topics.assert_bank_shape({s: [] for s in C.TOPIC_SETS})
