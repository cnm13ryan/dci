"""Core, spectrum, near-form and broad-class selection, end to end (§13)."""
from __future__ import annotations

import random


from dci1v5.protocol import constants as C
from dci1v5.stages import selection as S
from dci1v5.stages.calibration_table import CalibrationRow
from tests_v5.conftest import calibration_row

IOTA_A = 0.68


def _library(seed: int = 3, *, tier3: bool = True,
             marker_offsets: dict[str, float] | None = None
             ) -> list[CalibrationRow]:
    rng = random.Random(seed)
    offsets = dict(marker_offsets or {})
    rows: list[CalibrationRow] = []
    for kind in C.TIER1_FAMILY_IDS:
        base = 0.95 + offsets.get(kind, 0.0)
        for q in range(1, 9):
            solo = max(0.06, min(0.94, base - 0.09 * (q - 1)
                                 + rng.uniform(-0.01, 0.01)))
            rows.append(calibration_row(kind, q, solo=solo, chance=0.01))
    for kind, ladder in (("XC1", range(1, 9)),
                         ("XC2", (2, 4, 6, 8, 10, 12, 14, 16)),
                         ("XC3", range(3, 11))):
        base = 0.93
        for index, q in enumerate(ladder):
            solo = max(0.06, min(0.94, base - 0.08 * index
                                 + rng.uniform(-0.01, 0.01)))
            rows.append(calibration_row(kind, q, solo=solo, chance=0.06,
                                        kappa_b=0.06))
    if tier3:
        for kind, ladder in (("RF1", range(0, 9)), ("RF9", (0, 2, 4, 6, 8,
                                                            10, 13, 16))):
            for index, q in enumerate(ladder):
                solo = min(0.93, 0.34 + 0.075 * index)
                rows.append(calibration_row(kind, q, solo=solo, chance=0.20,
                                            kappa_b=0.24))
    return rows


def _stability(rows):
    return {r.label: {"passed": True} for r in rows}


def _select(rows):
    return S.select_all(rows, iota_a=IOTA_A, solo_compliance_a=IOTA_A,
                        stability_by_candidate=_stability(rows))


def test_the_core_set_is_three_families_from_three_groups():
    rows = _library()
    result = _select(rows)
    core = result.core["core_references"]
    assert result.core["references_identified"]
    assert len(core) == C.N_CORE_REFERENCES
    assert len({e["feature_group"] for e in core}) == 3
    assert sum(1 for e in core if e["structural_tier"] == 1) >= \
        C.MIN_TIER1_CORE


def test_the_core_set_spans_two_discourse_roles_by_substitution():
    rows = _library()
    result = _select(rows)
    roles = {e["discourse_role"] for e in result.core["core_references"]
             if e["discourse_role"] != "none"}
    assert len(roles) >= C.MIN_CORE_DISCOURSE_ROLES


def test_reference_pool_same_form_attaches_always():
    result = _select(_library())
    assert "REFERENCE_POOL_SAME_FORM" in result.identification_statuses


def test_the_spectrum_straddles_strictly_and_comes_from_the_core_family():
    result = _select(_library())
    core_families = {e["family"] for e in result.core["core_references"]}
    assert {e["family"] for e in result.spectrum} == core_families
    for triple in result.core["spectrum_triples"]:
        assert triple["lower"]["iota"] < IOTA_A < triple["upper"]["iota"]


def test_a_spectrum_rung_is_exempt_from_v_diff():
    assert "V_diff" not in S.SPECTRUM_COMPONENTS
    assert set(S.SPECTRUM_COMPONENTS) == set(C.VALIDITY_COMPONENTS) - \
        {"V_diff"}


def test_the_near_form_arm_is_three_tier_two_controls():
    rows = _library()
    result = _select(rows)
    if result.near_form["available"]:
        controls = result.near_form["controls"]
        assert len(controls) == C.N_NEAR_FORM_CONTROLS
        assert all(c["structural_tier"] == 2 for c in controls)
        assert len({c["feature_group"] for c in controls}) == 3


def test_the_broad_class_control_is_tier_three_budget_class():
    result = _select(_library())
    companion = result.broad_class.get("companion")
    if companion:
        assert companion["structural_tier"] == 3
        assert companion["constraint_class"] == "budget"
        assert "COMPANION_CLASS_NOT_MATCHED" in \
            result.broad_class["identification_statuses"]


def test_the_class_arm_drops_when_no_tier3_budget_severity_qualifies():
    result = _select(_library(tier3=False))
    assert result.broad_class["available"] is False
    assert "CLASS_ARM_NOT_AVAILABLE" in result.identification_statuses


def test_restrictiveness_runs_the_right_way_for_each_form():
    """§7.10: higher q is harder for an exact count and looser for a budget."""
    assert S.restrictiveness_key("MK1", 3) < S.restrictiveness_key("MK1", 5)
    assert S.restrictiveness_key("XC1", 3) < S.restrictiveness_key("XC1", 5)
    assert S.restrictiveness_key("RF1", 5) < S.restrictiveness_key("RF1", 3)
    assert S.restrictiveness_key("CL7", 10) < S.restrictiveness_key("CL7", 20)


def test_the_family_verdicts_record_every_rungs_earliest_failure():
    rows = _library()
    result = _select(rows)
    verdicts = result.core["family_verdicts"]
    assert verdicts
    for verdict in verdicts:
        for rung in verdict["rungs"]:
            if not rung["passed"]:
                assert rung["first_failing_component"] in \
                    C.VALIDITY_COMPONENTS


def test_a_tier_three_family_never_reaches_the_core_pool():
    rows = _library()
    result = _select(rows)
    for entry in result.core["core_references"]:
        assert entry["structural_tier"] in (1, 2)


def test_an_unstable_candidate_is_not_admitted():
    rows = _library()
    unstable = {r.label: {"passed": False, "reason": "split difference"}
                for r in rows}
    result = S.select_all(rows, iota_a=IOTA_A, solo_compliance_a=IOTA_A,
                          stability_by_candidate=unstable)
    assert not result.core["references_identified"]
    assert "EXCESS_NOT_IDENTIFIED" in result.identification_statuses


def test_selection_reads_no_pre_screen_quantity():
    """§12.2: no pre-screen quantity enters any admission decision in §13."""
    rows = _library()
    with_prescreen = [
        CalibrationRow(**{**{f: getattr(r, f) for f in
                             ("kind", "severity", "split", "model_key",
                              "solo_compliance", "chance_compliance",
                              "solo_vacuity", "kappa_under_b",
                              "kappa_under_b_source", "n_topics")},
                          "prescreen_solo_compliance": 0.99,
                          "prescreen_chance_compliance": 0.0})
        for r in rows]
    a = _select(rows)
    b = _select(with_prescreen)
    assert [e["family"] for e in a.core["core_references"]] == \
        [e["family"] for e in b.core["core_references"]]
