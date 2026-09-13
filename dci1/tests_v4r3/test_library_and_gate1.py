"""The candidate library, its coverage criterion, and Gate 1's instrument set.

Mapped to the brief's required failure modes: 2 and 3 (selection reads a
composed outcome), 4 (the vocabulary changes after composed outcomes), 5 (the
stopping rule is not deterministic), 6 (insufficient cross-family support is
accepted), 10 (a new family bypasses Gate 1), 11 (accidental compliance
computed wrongly), 12 (solo compliance substituted for the registered
coordinate), and 24 (plan and implementation disagree).
"""
from __future__ import annotations

import pytest

from dci1v4.errors import InstrumentError, ProtocolError, TerminalStatus

from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import library as lib
from dci1v4r3.stages.gate1 import gate1_payload
from dci1v4r3.verifiers.constraints import (
    FAMILIES, FEATURE_GROUPS, RESERVES, Constraint, declared_range,
)


# --------------------------------------------------------------- the grammar
def test_every_family_is_a_registered_statistic_under_a_registered_form():
    for kind, family in FAMILIES.items():
        assert family.statistic_id in C.STATISTIC_IDS
        assert family.form in C.FORMS
        assert set(family.ladder) <= set(family.reserve), kind


def test_a_rate_budget_never_carries_a_severity_that_means_its_count_sibling():
    """q=0 on a rate budget is the count budget at q=0 wearing another name,
    and §12.6's coverage criterion counts cross-family overlap."""
    for kind, family in FAMILIES.items():
        if family.form == "rate_budget":
            assert 0 not in family.reserve, kind


def test_two_families_of_one_feature_group_never_share_a_cell():
    from dci1v4r3.verifiers.witnesses import assert_pair_realisable
    with pytest.raises(InstrumentError, match="same feature"):
        assert_pair_realisable(Constraint("RF7", 0), Constraint("CR7", 24))
    with pytest.raises(InstrumentError, match="same feature"):
        assert_pair_realisable(Constraint("RF6", 0), Constraint("CR6", 3))
    assert FEATURE_GROUPS["capital_char"] == FEATURE_GROUPS["capital_word"]


def test_the_witness_suite_discharges_every_realisable_pair():
    from dci1v4r3.verifiers.witnesses import run_witness_suite
    report = run_witness_suite()
    assert report["passed"], report
    assert report["pairs"] > 20_000


# -------------------------------------------------- required failures 2 and 3
def _row(kind, q, solo, chance, vacuity=0.0, rnd=0):
    return lib.LibraryRow(kind=kind, severity=q, solo_compliance=solo,
                          chance_compliance=chance, solo_vacuity=vacuity,
                          admitted_in_round=rnd)


def test_the_candidate_table_refuses_a_composed_field_by_schema():
    good = {"kind": "RF1", "severity": 3, "solo_compliance": 0.7,
            "chance_compliance": 0.2, "solo_vacuity": 0.0}
    assert lib.load_prescreen_table([good])
    for field in ("delta_r", "xi", "composed", "delta_difficulty",
                  "d_b_from", "uptake"):
        with pytest.raises(ProtocolError, match="composed"):
            lib.load_prescreen_table([{**good, field: 0.5}])


def test_the_candidate_table_refuses_a_field_the_schema_does_not_model():
    with pytest.raises(ProtocolError, match="does not model"):
        lib.load_prescreen_table([{"kind": "RF1", "severity": 3,
                                   "solo_compliance": 0.7,
                                   "chance_compliance": 0.2,
                                   "solo_vacuity": 0.0,
                                   "b_plus_r_rate": 0.4}])


def test_a_library_row_has_no_field_a_composed_outcome_could_occupy():
    fields = set(lib.LibraryRow.__dataclass_fields__)
    assert not fields & set(f.lower() for f in
                            lib.FORBIDDEN_CALIBRATION_FIELDS)


# ------------------------------------------------------- required failure 4
def test_expansion_may_admit_a_reserve_rung_and_nothing_else():
    with pytest.raises(ProtocolError, match="frozen candidate library"):
        _row("CR1", 99, 0.6, 0.1)
    assert _row("CR1", 13, 0.6, 0.1).severity == 13   # in the reserve, not the ladder


def test_expansion_returns_only_reserve_rungs():
    rows = [_row(k, q, 0.6, 0.1) for k in ("RF1", "CR1")
            for q in FAMILIES[k].ladder]
    plan = lib.expansion_plan(rows, 0.55, round_index=1)
    for kind, q in plan:
        assert q in RESERVES[kind], (kind, q)


# ------------------------------------------------------- required failure 5
def test_the_expansion_rule_is_deterministic_given_the_table():
    rows = [_row(k, q, 0.2 + 0.05 * i, 0.05)
            for k in ("RF1", "CR1", "RF2")
            for i, q in enumerate(FAMILIES[k].ladder)]
    first = lib.expansion_plan(rows, 0.5, round_index=1)
    second = lib.expansion_plan(list(reversed(rows)), 0.5, round_index=1)
    assert first == second


def test_the_expansion_budget_is_registered_and_enforced():
    rows = [_row("RF1", q, 0.5, 0.1) for q in FAMILIES["RF1"].ladder]
    with pytest.raises(ProtocolError, match="expansion rounds"):
        lib.expansion_plan(rows, 0.5,
                           round_index=C.EXPANSION_MAX_ROUNDS + 1)
    plan = lib.expansion_plan(rows, 0.5, round_index=1)
    per_family = {}
    for kind, _ in plan:
        per_family[kind] = per_family.get(kind, 0) + 1
    assert all(n <= C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND
               for n in per_family.values())


# ------------------------------------------------------- required failure 6
def _spread_table(groups, per_side=2):
    """A table with ``groups`` feature groups straddling iota_A = 0.50."""
    rows = []
    families = [k for k in FAMILIES if FAMILIES[k].role == "reference"]
    used = set()
    for kind in families:
        group = FEATURE_GROUPS[FAMILIES[kind].statistic_id]
        if group in used or len(used) >= groups:
            continue
        used.add(group)
        ladder = list(FAMILIES[kind].ladder)
        offsets = [-0.25, -0.10, 0.10, 0.25][:2 * per_side]
        for q, delta in zip(ladder, offsets):
            rows.append(_row(kind, q, 0.50 + delta, 0.0))
    return rows


def test_insufficient_cross_group_support_is_refused_not_accepted():
    report = lib.coverage_report(_spread_table(2), 0.50)
    assert not report.passed
    assert not report.conditions["C2_groups_per_side"]["met"]
    assert not report.conditions["C4_straddling_families"]["met"]


def test_adequate_cross_group_support_passes_every_decisive_condition():
    report = lib.coverage_report(_spread_table(6, per_side=2), 0.50)
    decisive = {k: v["met"] for k, v in report.conditions.items()
                if k != "C7_class_matched"}
    assert all(decisive.values()), decisive
    assert report.passed


def test_the_coverage_criterion_counts_feature_groups_not_families():
    """Eight families over two groups must not read as eight controls."""
    rows = []
    for kind in ("RF1", "CR1", "RF7", "CR7"):
        for i, q in enumerate(FAMILIES[kind].ladder[:4]):
            rows.append(_row(kind, q, 0.50 + [-0.25, -0.10, 0.10, 0.25][i], 0.0))
    report = lib.coverage_report(rows, 0.50)
    assert report.n_eligible_families == 4
    assert not report.conditions["C2_groups_per_side"]["met"]


def test_a_failed_coverage_criterion_names_its_status():
    rows = _spread_table(2)
    result = lib.run_expansion(rows, 0.50, measure=lambda plan, r: [])
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in result["statuses"]
    assert not result["passed"]


# ------------------------------------------------------ required failure 10
def test_every_reserve_rung_is_in_the_gate_1_instrument_population():
    from dci1v4r3.verifiers.boundary import instrument_population
    population = set(instrument_population())
    for kind in FAMILIES:
        for q in declared_range(kind):
            assert (kind, q) in population, f"{kind}:{q}"


def test_gate_1_covers_the_declared_range_and_not_the_round_zero_ladder():
    from dci1v4r3.verifiers.boundary import instrument_population
    n = len(instrument_population())
    round_zero = (len(C.TARGET_GRID) + 6
                  + sum(len(f.ladder) for f in FAMILIES.values()))
    assert n > round_zero
    assert n == (len(C.TARGET_GRID) + 6
                 + sum(len(v) for v in RESERVES.values()))


# ------------------------------------------------ required failures 11 and 12
def test_instructed_compliance_is_the_registered_coordinate_not_solo():
    row = _row("RF1", 3, solo=0.90, chance=0.80)
    assert row.solo_compliance == 0.90
    assert abs(row.iota - 0.5) < 1e-12
    assert C.DIFFICULTY_COORDINATE == "instructed_compliance"


def test_a_rung_whose_chance_exceeds_its_solo_is_ineligible_everywhere():
    row = _row("RF1", 3, solo=0.30, chance=0.40)
    assert row.iota < 0
    assert not lib.eligible_prescreen(row)


def test_a_degenerate_chance_rate_is_ineligible_rather_than_dividing_by_zero():
    row = _row("RF1", 3, solo=0.999, chance=0.995)
    assert not lib.eligible_prescreen(row)


# ------------------------------------------------------ required failure 23
def test_gate_1_cannot_pass_on_human_validation_unavailable():
    evidence = {
        "determinism": {"agreement": 1.0},
        "suites": {"agreement": 1.0, "cases": 136, "failures": []},
        "reimplementation": {"per_instrument_min": 1.0, "failures": [],
                             "segmenter_differential": {"agreement": 1.0}},
        "witnesses": {"passed": True, "non_entailment_failures": []},
        "wordings": {"passed": True},
        "adversarial": {"passed": True, "uncovered_by_corpus": []},
    }
    with pytest.raises(TerminalStatus) as excinfo:
        gate1_payload(evidence=evidence,
                      measurement_basis="human_validation_unavailable")
    assert excinfo.value.args[0].startswith(
        "MEASUREMENT_EVIDENCE_INSUFFICIENT")

    with pytest.raises(TerminalStatus):
        gate1_payload(evidence=evidence,
                      measurement_basis="autorater_calibration_approved",
                      autorater={"approved": False})

    passed = gate1_payload(
        evidence=evidence, measurement_basis="autorater_calibration_approved",
        autorater={"approved": True, "judge": "gpt-oss-20b"})
    assert passed["outcome"] == "PASS"
    assert passed["scope_sentence"] == C.SCOPE_SENTENCE


def test_gate_1_refuses_a_reimplementation_that_disagrees():
    evidence = {
        "determinism": {"agreement": 1.0},
        "suites": {"agreement": 1.0, "cases": 136, "failures": []},
        "reimplementation": {"per_instrument_min": 0.999,
                             "failures": ["RF3:1"],
                             "segmenter_differential": {"agreement": 1.0}},
        "witnesses": {"passed": True, "non_entailment_failures": []},
        "wordings": {"passed": True},
        "adversarial": {"passed": True, "uncovered_by_corpus": []},
    }
    with pytest.raises(TerminalStatus) as excinfo:
        gate1_payload(evidence=evidence,
                      measurement_basis="autorater_calibration_approved",
                      autorater={"approved": True})
    assert excinfo.value.args[0].startswith(
        "MEASUREMENT_NOT_ESTABLISHED")


# ------------------------------------------------ the segmentation correction
def test_exactly_one_unicode_character_splits_a_word_under_case_folding():
    from dci1v4r3.verifiers.words import assert_single_splitter
    assert assert_single_splitter() == "İ"


def test_the_corrected_word_list_keeps_a_dotted_capital_word_whole():
    from dci1v4.verifiers.words import words_lower as v4r2_words_lower
    from dci1v4r3.verifiers.statistics import STATISTICS, focal_statistic
    from dci1v4r3.verifiers.words import words_lower
    text = "İstanbul is big"
    assert len(words_lower(text)) == 3
    assert len(v4r2_words_lower(text)) == 4      # the carried defect
    assert focal_statistic(text) == 8            # a reader counts eight
    assert STATISTICS["one_letter"](text) == 0


def test_the_correction_moves_no_number_on_text_without_that_character():
    from dci1v4r3.verifiers.statistics import assert_agrees_with_v4r2
    from dci1v4r3.verifiers.boundary import ALL_CASES
    report = assert_agrees_with_v4r2(c["text"] for c in ALL_CASES)
    assert report["checked"] == len(ALL_CASES) - report[
        "skipped_containing_u0130"]
    assert report["skipped_containing_u0130"] >= 1


def test_a_s_carry_over_survives_the_correction():
    from dci1v4r3.verifiers.carryover import NOT_CARRIED, carry_over_record
    record = carry_over_record()
    assert record["a_carry_over_survives"] is True
    assert "words_lower" in NOT_CARRIED
    assert record["carried_target_cases"] == 48


# --------------------------------- the secondary coordinate is not decisive
def test_the_class_condition_is_reported_and_never_decisive():
    """C7 is about the class arm, which §7.3 already says is unmatched. A
    replication is never stopped by it."""
    rows = _spread_table(6, per_side=2)
    report = lib.coverage_report(rows, 0.50)
    assert report.conditions["C7_class_matched"]["terminal"] is False
    assert not report.class_matched          # no class rungs in this table
    assert report.passed                     # ...and it still passes


def test_the_recorded_status_comes_from_the_registered_coordinate_alone():
    """Raw solo compliance is a registered *secondary* coordinate (§13.3).

    Netting out chance is what makes a companion's difficulty comparable
    across the production/budget divide, so a table that passes coverage only
    because chance was left in has not identified a difficulty spectrum. This
    pins that `run_expansion` reads `iota` and nothing else: the same rows,
    read on solo compliance, would pass.
    """
    rows, families = [], [k for k in FAMILIES
                          if FAMILIES[k].role == "reference"]
    used = set()
    for kind in families:
        group = FEATURE_GROUPS[FAMILIES[kind].statistic_id]
        if group in used or len(used) >= 6:
            continue
        used.add(group)
        for q, solo in zip(FAMILIES[kind].ladder,
                           (0.25, 0.40, 0.60, 0.75)):
            # High chance: solo straddles 0.50, iota does not come close.
            rows.append(_row(kind, q, solo, chance=min(solo * 0.95, 0.9)))
    on_iota = lib.coverage_report(rows, 0.50)
    on_solo = lib.coverage_report(
        [_row(r.kind, r.severity, r.solo_compliance, 0.0) for r in rows], 0.50)
    assert not on_iota.passed
    assert on_solo.passed
    result = lib.run_expansion(rows, 0.50, measure=lambda plan, r: [])
    assert "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" in result["statuses"]


# ------------------------------------------- §8.6's three design variants
def test_a_failed_coverage_criterion_keeps_the_core_matrix():
    """§12.6 withholds delta_difficulty, not Delta_R, Xi and Lambda too."""
    from dci1v4r3.design.cells import cell_types
    full = cell_types()
    no_spectrum = cell_types(spectrum=False)
    reduced = cell_types(reduced=True)
    assert len(full) == C.N_CELLS_FULL == 47
    assert len(no_spectrum) == C.N_CELLS_NO_SPECTRUM == 29
    assert len(reduced) == C.N_CELLS_REDUCED_WITH_CLASS == 8
    slots = {s for t in no_spectrum for s in t.slots}
    assert {"A", "B", "R1", "R2", "R3", "CL"} == slots
    assert not any(s.startswith("R1-") or s.endswith("+") for s in slots)
    # every unordered core pair survives, in both orders
    pairs = [t for t in no_spectrum if t.arm == "composed"]
    assert len(pairs) == C.N_CORE_COMPOSED_CELLS + C.N_CLASS_COMPOSED_CELLS


def test_the_no_spectrum_variant_still_pairs_the_class_arm_with_b_only():
    from dci1v4r3.design.cells import cell_types
    for cell in cell_types(spectrum=False):
        if cell.arm == "composed" and "CL" in cell.slots:
            assert "B" in cell.slots


# ------------------------------------------------------- §10.4's own criteria
def test_the_autorater_hierarchy_can_return_no_survivor():
    """§10.4's second criterion is a criterion, not a formality.

    On v4r3's pool both registered conditions truncate heavily, so the
    selection has no answer — and an artifact that reported a "selected"
    condition anyway would be reporting a choice the hierarchy did not make.
    """
    import importlib.util
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "autorater_v4r3", root / "tools" / "gate1_autorater_v4r3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    artifact = root / "reports" / "dci1v4r3" / "section_10_4_development.json"
    if not artifact.exists():                               # pragma: no cover
        pytest.skip("the §10.4 development phase has not run in this checkout")
    import json
    payload = json.loads(artifact.read_text())
    selection = payload["selection"]
    assert selection["human_criterion_outstanding"] is True
    # criterion 1 is repeatability and criterion 2 is truncation, in that order
    assert selection["steps"][0]["criterion"] == "valid deterministic execution"
    assert "truncation" in selection["steps"][1]["criterion"]
    # a surviving list and the recorded outcome must agree
    if selection["surviving"]:
        assert selection["outcome"] == selection["surviving"]
    else:
        assert selection["outcome"] == "no condition survives criterion 2"
    assert payload["not_claimed"]["autorater_freeze"].startswith("single-shot")
    assert payload["not_claimed"]["researcher_approval"].startswith("reserved")
