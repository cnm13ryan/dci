"""The revised A (D08) and B (D07) selection rules (audit F3, F9), on exact
synthetic tables. The two audit counterexamples are reproduced verbatim."""
from __future__ import annotations

import pytest

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1 import synthetic as SY
from tests.batch1.test_selection import flat, with_overrides

pytestmark = pytest.mark.cpu

CFG0 = CFG.DEFAULT_CONFIG
MODELS, FRAMES = CFG0.models, CFG0.frames
BY_ID = L.constraint_by_id()
B_GOOD = {8: 0.2, 9: 0.35, 10: 0.5, 11: 0.6, 12: 0.7, 13: 0.8}


@pytest.fixture(scope="module")
def matrix():
    return COMPAT.compatibility_matrix()


def exact(truth, n=100_000):
    return SY.tables_from_rates(SY.full_rates(truth), n=n)


# --------------------------------------------------------------- A (D08)

def floor_truth(m, f, cid):
    """The audit's D08 counterexample, verbatim (probe section 4)."""
    c = BY_ID[cid]
    if c.role == "B":
        return B_GOOD[c.p["m"]]
    if c.role == "A":
        return {2: .80, 4: .50, 6: .03}[c.p["n"]]
    if c.family_id == "exact_word_count":
        n, w = c.p["n"], c.p["word"]
        if n == 6:
            return 0.25 if (m, f) == ("qwen3-4b-instruct-2507", "F0") else 0.04
        if n == 4:
            return {"indeed": .75, "instead": .70, "perhaps": .32,
                    "although": .28, "moreover": .25, "therefore": .72,
                    "nonetheless": .22, "consequently": .21}[w]
        return 0.98
    return 0.25 if (m, f) == ("qwen3-4b-instruct-2507", "F0") else 0.04


def test_a_floor_level_a_is_never_selected_or_feasible(matrix):
    """Before: A.however.6 (p_A = 0.03 everywhere) selected, FEASIBLE."""
    result = CAL.finalize(exact(floor_truth), CFG0, matrix)
    ranking = {r["a"]: r for r in result["a"]["ranking"]}
    assert not ranking["A.however.6"]["admissible"]
    assert ranking["A.however.6"]["headroom"] == 0
    assert result["a"]["selected"] != "A.however.6"
    assert result["status"] != "FEASIBLE"


def _a_rates(p_a, refs=None):
    rates = flat(p_a=0.5, p_ref=0.5, p_b=B_GOOD)
    for (m, f, cid) in list(rates):
        c = BY_ID[cid]
        if c.role == "A":
            rates[(m, f, cid)] = p_a(m, f, c.p["n"])
    return with_overrides(rates, refs or {})


def test_a_at_three_percent_everywhere_fails_selection(matrix):
    tables = SY.tables_from_rates(_a_rates(lambda m, f, n: 0.03))
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["status"] == "A_SELECTION_FAILED"
    assert result["a"]["selected"] is None and result["configurations"] == []
    assert any("A_HEADROOM_INADEQUATE" in f for f in result["a"]["flags"])


def test_a_at_ninety_seven_percent_everywhere_fails_selection(matrix):
    tables = SY.tables_from_rates(_a_rates(lambda m, f, n: 0.97))
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["status"] == "A_SELECTION_FAILED"


def test_a_moderate_everywhere_is_admissible_and_feasible(matrix):
    result = CAL.finalize(SY.tables_from_rates(SY.full_rates()), CFG0, matrix)
    assert result["status"] == "FEASIBLE"
    chosen = next(r for r in result["a"]["ranking"]
                  if r["a"] == result["a"]["selected"])
    assert chosen["admissible"] and chosen["headroom"] == 8
    assert all(rep["a_informative"] for rep in result["configurations"])


def test_a_informative_for_some_models_only_is_not_admissible(matrix):
    two = {"qwen3-4b", "qwen3-4b-instruct-2507"}
    tables = SY.tables_from_rates(_a_rates(
        lambda m, f, n: {2: 0.5 if m in two else 0.97, 4: 0.5 if m in two
                         else 0.02, 6: 0.02}[n] if n != 2 else
        (0.5 if m != "gemma-3n-e2b-it" else 0.99)))
    a = CAL.select_a(tables, CFG0, matrix, R.eligibility(tables, CFG0), [9, 12])
    rows = {r["a"]: r for r in a["ranking"]}
    assert not rows["A.however.4"]["admissible"]          # 4 of 8, 2 models
    assert "INFORMATIVE_IN_4_MODEL_FRAMES_BELOW_6" in rows["A.however.4"]["reasons"]
    assert rows["A.however.2"]["admissible"]              # 6 of 8, 3 models
    assert a["selected"] == "A.however.2"


def test_better_coverage_with_worse_headroom_loses(matrix):
    """A.6 would give G1 support everywhere, but it is informative in only
    two models; A.4 is informative everywhere and wins."""
    gemma = {"gemma-3n-e2b-it", "gemma-3n-e4b-it"}
    rates = _a_rates(lambda m, f, n: {2: 0.97, 4: 0.5,
                                      6: 0.5 if m in gemma else 0.95}[n])
    for (m, f, cid) in list(rates):
        c = BY_ID[cid]
        if c.role == "reference" and c.family_id == "exact_word_count":
            rates[(m, f, cid)] = (rates[(m, f, "A.however.6")]
                                  if c.p["n"] == 6 else 0.75)
    tables = SY.tables_from_rates(rates)
    a = CAL.select_a(tables, CFG0, matrix, R.eligibility(tables, CFG0), [9, 12])
    rows = {r["a"]: r for r in a["ranking"]}
    assert rows["A.however.6"]["g1_supported_including_uninformative_a"] > \
        rows["A.however.4"]["g1_supported"]
    assert not rows["A.however.6"]["admissible"]
    assert a["selected"] == "A.however.4"


def test_uninformative_a_configurations_are_reported_but_never_counted(matrix):
    one_model_extreme = {"gemma-3n-e2b-it"}
    overrides = {(m, f, "A.however.4"): 0.97
                 for m in one_model_extreme for f in FRAMES}
    overrides.update({"A.however.2": 0.99, "A.however.6": 0.01})
    tables = SY.tables_from_rates(with_overrides(SY.full_rates(), overrides))
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["a"]["selected"] == "A.however.4"
    reps = result["configurations"]
    assert len(reps) == 16                              # nothing hidden
    extreme = [r for r in reps if r["model"] in one_model_extreme]
    assert extreme and not any(r["a_informative"] for r in extreme)
    for p in ("P1", "P2", "P3"):
        f = result["feasibility"][p]
        assert f["supported_configurations"] <= 12
        assert f["supported_including_uninformative_a"] >= \
            f["supported_configurations"]
        assert "gemma-3n-e2b-it" not in f["models"]


def test_the_a_band_edges_are_inclusive_in_exact_arithmetic(matrix):
    tables = SY.tables_from_rates(_a_rates(
        lambda m, f, n: 0.10 if n == 4 else 0.90), n=100)
    a = CAL.select_a(tables, CFG0, matrix, R.eligibility(tables, CFG0), [9, 12])
    assert all(r["admissible"] for r in a["ranking"])


# --------------------------------------------------------------- B (D07)

def b_tables(p_b, n=100_000):
    return SY.tables_from_rates(
        {k: v for k, v in flat(p_b=p_b).items()}, n=n)


def test_the_plateau_counterexample_selects_no_pair():
    """The audit's D07 counterexample: 0.16 / 0.165 / 0.17 / 0.88+.
    Before: (8, 10) with medians 0.16 and 0.17."""
    b = CAL.select_b(b_tables({8: .16, 9: .165, 10: .17, 11: .88, 12: .93,
                               13: .96}), CFG0)
    assert b["status"] == "FAILED" and b["selected"] is None
    reasons = {tuple(e["pair"]): e["reasons"] for e in b["evaluated"]}
    assert any("MEDIAN_SEPARATION" in r for r in reasons[(8, 10)])
    assert any("B11_INFORMATIVE_IN_0" in r for r in reasons[(8, 11)])


def test_nearly_identical_limits_are_never_a_pair():
    b = CAL.select_b(b_tables({8: .40, 9: .42, 10: .44, 11: .46, 12: .48,
                               13: .50}), CFG0)
    assert b["status"] == "FAILED"


def test_clear_separation_is_selected():
    b = CAL.select_b(b_tables({8: .2, 9: .3, 10: .45, 11: .6, 12: .7,
                               13: .8}), CFG0)
    assert b["status"] == "SELECTED"
    m1, m2 = b["selected"]
    assert b["per_limit"][m2]["median"] - b["per_limit"][m1]["median"] >= 0.15
    chosen = next(e for e in b["evaluated"] if e["pair"] == [m1, m2])
    assert len(chosen["separated_models"]) >= 3


def test_separation_carried_by_one_or_two_models_is_refused():
    rates = flat()
    two = ("qwen3-4b", "qwen3-4b-instruct-2507")
    for m in MODELS:
        for f in FRAMES:
            for c in L.b_candidates():
                rates[(m, f, c.cid)] = (0.2 + 0.12 * (c.p["m"] - 8)
                                        if m in two else 0.3)
    b = CAL.select_b(SY.tables_from_rates(rates, n=100_000), CFG0)
    assert b["status"] == "FAILED"
    assert all(any("SEPARATED_IN_2_MODELS" in r for r in e["reasons"])
               for e in b["evaluated"]
               if e.get("median_separation", 0) >= 0.15)


def test_a_limit_at_the_floor_or_ceiling_is_never_selected():
    b = CAL.select_b(b_tables({8: .02, 9: .3, 10: .45, 11: .6, 12: .7,
                               13: .98}), CFG0)
    assert b["status"] == "SELECTED"
    assert 8 not in b["selected"] and 13 not in b["selected"]


def test_tied_pairs_break_to_the_smaller_limits():
    b = CAL.select_b(b_tables({8: .05, 9: .3, 10: .3, 11: .99, 12: .6,
                               13: .6}), CFG0)
    assert b["status"] == "SELECTED" and b["selected"] == [9, 12]
    tied = [r for r in b["ranking"] if r["score"] == b["score"]]
    assert {tuple(r["pair"]) for r in tied} == {(9, 12), (9, 13), (10, 12),
                                                (10, 13)}


def test_the_separation_threshold_is_inclusive_and_configurable():
    p_b = {8: .30, 9: .30, 10: .30, 11: .45, 12: .45, 13: .45}
    b = CAL.select_b(b_tables(p_b, n=100), CFG0)
    assert b["status"] == "SELECTED" and b["selected"] == [8, 11]
    assert b["score"][2] == pytest.approx(0.15)        # exactly 15 pp
    strict = CFG.PilotConfig(b_min_median_separation=0.2)
    assert CAL.select_b(b_tables(p_b, n=100), strict)["status"] == "FAILED"


def test_a_failed_b_selection_never_reports_feasible(matrix):
    tables = b_tables({m: 0.5 for m in range(8, 14)})
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["status"] == "B_SELECTION_FAILED"
