"""Selection logic on synthetic compliance tables: eligibility, matching,
chance correction, G1-G6, weights, coverage, feasibility, A/B selection and
Stage 2 refinement. Every scenario the Batch 1 brief lists is here."""
from __future__ import annotations

import inspect
import random
from fractions import Fraction

import pytest

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1 import synthetic as SY
from dci.batch1.scoring import Count, _key

pytestmark = pytest.mark.cpu

CFG0 = CFG.DEFAULT_CONFIG
MODELS, FRAMES = CFG0.models, CFG0.frames
BY_ID = L.constraint_by_id()
A4 = BY_ID["A.however.4"]
WORD_REFS = [c.cid for c in L.reference_library()
             if c.family_id == "exact_word_count"]


@pytest.fixture(scope="module")
def matrix():
    return COMPAT.compatibility_matrix()


def flat(p_a=0.5, p_ref=0.5, p_b=None, **cells):
    """Every A at p_a, every reference at p_ref, B rising with m; then
    per-(model, frame, cid) or per-cid overrides."""
    p_b = p_b or {8: 0.05, 9: 0.3, 10: 0.45, 11: 0.6, 12: 0.7, 13: 0.95}
    rates = {}
    for m in MODELS:
        for f in FRAMES:
            for c in L.a_candidates():
                rates[(m, f, c.cid)] = p_a
            for c in L.b_candidates():
                rates[(m, f, c.cid)] = p_b[c.p["m"]]
            for c in L.reference_library():
                rates[(m, f, c.cid)] = p_ref
    for key, p in cells.items():
        rates[key] = p
    return rates


def with_overrides(rates, overrides):
    rates = dict(rates)
    for key, p in overrides.items():
        if isinstance(key, str):
            for m in MODELS:
                for f in FRAMES:
                    rates[(m, f, key)] = p
        else:
            rates[key] = p
    return rates


def report(tables, matrix, model="qwen3-4b", frame="F0", m=12, a=A4,
           cfg=CFG0):
    elig = R.eligibility(tables, cfg)
    return R.configuration_report(tables, cfg, matrix, elig, a, model, frame, m)


# ---------------------------------------------------------------- scenarios

def test_successful_coverage_for_all_three_contrasts(matrix):
    tables = SY.tables_from_rates(SY.full_rates())
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["status"] == "FEASIBLE"
    for p in ("P1", "P2", "P3"):
        f = result["feasibility"][p]
        assert f["feasible"] and f["supported_configurations"] >= 12
        assert len(f["models"]) >= 3
        assert f["b_limits"] == result["b"]["selected"]


def test_g1_fails_while_p3_remains_supported(matrix):
    far = {cid: 0.95 for cid in WORD_REFS}
    far.update({"ew.indeed.4": 0.5, "ew.instead.4": 0.5})   # two words only
    tables = SY.tables_from_rates(with_overrides(flat(), far))
    rep = report(tables, matrix)
    cov = rep["coverage"]
    assert not cov["G1"]["supported"]
    assert cov["G1"]["distinct_words"] == ["indeed", "instead"]
    assert not cov["P1"]["supported"] and not cov["P2"]["supported"]
    assert any("G1_TOO_FEW_DISTINCT_WORDS" in r and "matched" in r
               for r in cov["P1"]["reasons"])
    assert cov["P3"]["supported"]
    assert rep["funnel"]["G1"]["limiting_step"] == "matched"


def test_difficulty_matching_differs_by_model(matrix):
    rates = with_overrides(flat(p_ref=0.95), {
        ("qwen3-4b", "F0", "ew.indeed.4"): 0.52,
        ("gemma-3n-e2b-it", "F0", "ew.indeed.4"): 0.80})
    tables = SY.tables_from_rates(rates)
    assert "ew.indeed.4" in report(tables, matrix, "qwen3-4b")["populations"]["G1"]
    assert "ew.indeed.4" not in report(tables, matrix,
                                       "gemma-3n-e2b-it")["populations"]["G1"]
    assert "ew.indeed.4" in report(tables, matrix,
                                   "gemma-3n-e2b-it")["populations"]["G2"]


def test_difficulty_matching_differs_by_frame(matrix):
    rates = with_overrides(flat(p_ref=0.95), {
        ("qwen3-4b", "F0", "ew.indeed.4"): 0.45,
        ("qwen3-4b", "F1", "ew.indeed.4"): 0.70})
    tables = SY.tables_from_rates(rates)
    assert "ew.indeed.4" in report(tables, matrix, frame="F0")["populations"]["G1"]
    assert "ew.indeed.4" not in report(tables, matrix,
                                       frame="F1")["populations"]["G1"]


def test_b9_and_b12_give_different_compatible_populations(matrix):
    tables = SY.tables_from_rates(flat())
    g9 = set(report(tables, matrix, m=9)["populations"]["G1"])
    g12 = set(report(tables, matrix, m=12)["populations"]["G1"])
    assert g12 - g9 == {"ew.nonetheless.2", "ew.nonetheless.4",
                        "ew.consequently.2", "ew.consequently.4"}
    assert "inc.remarkable" in report(tables, matrix, m=12)["populations"]["G6"]
    assert "inc.remarkable" not in report(tables, matrix, m=9)["populations"]["G6"]


def test_a_variant_eligible_on_one_model_enters_every_models_pool(matrix):
    rates = with_overrides(flat(), {"inc.simple": 0.05})
    rates[("gemma-3n-e4b-it", "F1", "inc.simple")] = 0.25
    tables = SY.tables_from_rates(rates)
    elig = R.eligibility(tables, CFG0)
    assert elig["inc.simple"]["status"] == R.ELIGIBLE
    assert elig["inc.simple"]["qualifying_20"] == ["gemma-3n-e4b-it|F1"]
    rep = report(tables, matrix, model="qwen3-4b", frame="F0")
    assert "inc.simple" in rep["populations"]["G6"]
    assert "inc.simple" not in rep["populations"]["G5"]      # unmatched there


def test_raw_and_iota_matching_select_different_references(matrix):
    rates = flat(p_ref=0.95)
    rates[("qwen3-4b", "F0", "ew.indeed.4")] = 0.55
    rates[("qwen3-4b", "F0", "ew.instead.4")] = 0.75
    kappa = {("qwen3-4b", "ew.indeed.4"): 0.5, ("qwen3-4b", "ew.instead.4"): 0.5,
             ("qwen3-4b", "A.however.4"): 0.0}
    tables = SY.tables_from_rates(rates, n=100, kappa=kappa, kappa_n=100)
    rep = report(tables, matrix)
    assert "ew.indeed.4" in rep["populations"]["G1"]
    assert "ew.instead.4" not in rep["populations"]["G1"]
    iota = rep["sensitivity"]["iota_matching"]["G1"]
    assert "ew.instead.4" in iota and "ew.indeed.4" not in iota
    assert rep["raw_vs_iota"]["G1"] == {"raw_only": ["ew.indeed.4"],
                                        "iota_only": ["ew.instead.4"]}


# ------------------------------------------------------ thresholds, exactly

def test_eligibility_threshold_is_inclusive_and_exact(matrix):
    rates = with_overrides(flat(), {"inc.simple": 0.0, "inc.remarkable": 0.0})
    rates[("qwen3-4b", "F0", "inc.simple")] = 0.20
    rates[("qwen3-4b", "F0", "inc.remarkable")] = 0.19
    elig = R.eligibility(SY.tables_from_rates(rates, n=100), CFG0)
    assert elig["inc.simple"]["status"] == R.ELIGIBLE
    assert elig["inc.remarkable"]["status"] == R.EXTENSION_ONLY


def test_ten_percent_extension_is_separate_from_the_primary_pool(matrix):
    rates = with_overrides(flat(), {"inc.simple": 0.15, "pro.letter.b": 0.05})
    tables = SY.tables_from_rates(rates, n=100)
    elig = R.eligibility(tables, CFG0)
    assert elig["inc.simple"]["status"] == R.EXTENSION_ONLY
    assert elig["pro.letter.b"]["status"] == R.INELIGIBLE
    rep = report(tables, matrix)
    assert "inc.simple" not in rep["populations"]["G6"]
    assert "inc.simple" in rep["sensitivity"]["extension_10"]["G6"]
    assert "pro.letter.b" not in rep["sensitivity"]["extension_10"]["G6"]


def test_matching_tolerance_is_inclusive_in_exact_arithmetic():
    rates = flat()
    rates[("qwen3-4b", "F0", "ew.indeed.4")] = 0.60
    rates[("qwen3-4b", "F0", "ew.instead.4")] = 0.61
    rates[("qwen3-4b", "F0", "ew.perhaps.4")] = 0.40
    tables = SY.tables_from_rates(rates, n=100)
    m = {cid: R.match(tables, CFG0, "qwen3-4b", "F0", "A.however.4", cid)
         for cid in ("ew.indeed.4", "ew.instead.4", "ew.perhaps.4")}
    assert m["ew.indeed.4"]["raw"] and m["ew.perhaps.4"]["raw"]
    assert not m["ew.instead.4"]["raw"]
    assert m["ew.indeed.4"]["diff_ci"][0] < 0.10 < m["ew.indeed.4"]["diff_ci"][1]
    assert not m["ew.indeed.4"]["within_tolerance_with_confidence"]


def test_undefined_iota_is_unmatched_and_flagged(matrix):
    tables = SY.tables_from_rates(flat(), kappa={("qwen3-4b", "ew.indeed.4"): 1.0})
    m = R.match(tables, CFG0, "qwen3-4b", "F0", "A.however.4", "ew.indeed.4")
    assert m["raw"] and m["iota"] is None and m["iota_undefined"]
    rep = report(tables, matrix)
    assert "ew.indeed.4" in rep["sensitivity"]["iota_undefined"]
    assert "ew.indeed.4" not in rep["sensitivity"]["iota_matching"]["G1"]


def test_incomplete_pilot_data_is_undetermined_not_ineligible(matrix):
    rates = with_overrides(flat(), {"inc.simple": 0.05})
    tables = SY.tables_from_rates(rates)
    key = _key("qwen3-4b", "F0", "inc.simple")
    tables.explicit[key] = Count(k=30, n=40, planned=96)
    tables.explicit[_key("qwen3-4b", "F0", "ew.indeed.4")] = Count(k=48, n=50,
                                                                  planned=96)
    elig = R.eligibility(tables, CFG0)
    assert elig["inc.simple"]["status"] == R.UNDETERMINED
    assert elig["inc.simple"]["incomplete_cells"] == ["qwen3-4b|F0"]
    m = R.match(tables, CFG0, "qwen3-4b", "F0", "A.however.4", "ew.indeed.4")
    assert m["status"] == R.UNDETERMINED and m["raw"] is None
    rep = report(tables, matrix)
    assert "ew.indeed.4" in rep["excluded"]["matching_undetermined"]
    assert "inc.simple" in rep["excluded"]["eligibility_undetermined"]


def test_an_incomplete_a_cell_is_reported():
    tables = SY.tables_from_rates(flat())
    tables.explicit[_key("qwen3-4b", "F0", "A.however.4")] = Count(1, 2, planned=96)
    rep = report(tables, COMPAT.compatibility_matrix())
    assert "A_CELL_INCOMPLETE" in rep["context"]
    assert rep["populations"]["G1"] == [] and rep["populations"]["G5"] == []


# ------------------------------------------------- populations and weights

def test_g1_to_g6_nest_and_exclude_a(matrix):
    rng = random.Random(3)
    rates = {k: rng.random() for k in flat()}
    tables = SY.tables_from_rates(rates)
    for m in (9, 12):
        for a in L.a_candidates():
            rep = report(tables, matrix, m=m, a=a)
            R.assert_nesting(rep["populations"])
            assert all(a.cid not in v for v in rep["populations"].values())


def test_nesting_violation_is_detected():
    with pytest.raises(AssertionError):
        R.assert_nesting({"G1": ["x"], "G2": [], "G3": ["x"], "G4": ["x"],
                          "G5": ["x"], "G6": ["x"]})


def test_hierarchical_weights_are_exact_and_order_invariant():
    members = ["ew.indeed.2", "ew.indeed.4", "ec.comma.3", "inc.simple"]
    w = R.hierarchical_weights(members)
    assert w == {"ec.comma.3": Fraction(1, 4), "ew.indeed.2": Fraction(1, 8),
                 "ew.indeed.4": Fraction(1, 8), "inc.simple": Fraction(1, 2)}
    assert sum(w.values()) == 1
    for seed in range(5):
        shuffled = members[:]
        random.Random(seed).shuffle(shuffled)
        assert R.hierarchical_weights(shuffled) == w
    assert R.hierarchical_weights([]) == {}


def test_word_count_variants_do_not_dominate_the_broad_population():
    g6 = [c.cid for c in L.reference_library()]
    w = R.hierarchical_weights(g6)
    word = sum(v for k, v in w.items() if k.startswith("ew."))
    assert word == Fraction(1, 7) * Fraction(1, 4)      # 1 op of 7, 1 of 4 objects
    assert sum(w.values()) == 1


def test_weights_in_reports_sum_to_one(matrix):
    rep = report(SY.tables_from_rates(SY.full_rates()), matrix)
    for g, weights in rep["weights"].items():
        if weights:
            assert sum(Fraction(v) for v in weights.values()) == 1, g


def test_membership_has_no_prompt_order_input():
    params = inspect.signature(R.configuration_report).parameters
    assert not {"order", "orders", "position"} & set(params)


# ---------------------------------------------------------------- coverage

def test_no_effective_population_expansion_is_reported(matrix):
    tables = SY.tables_from_rates(flat())          # every word ref matched
    cov = report(tables, matrix)["coverage"]
    assert not cov["P1"]["supported"]
    assert "NO_EFFECTIVE_POPULATION_EXPANSION" in cov["P1"]["reasons"]


def test_p3_needs_other_operation_references(matrix):
    others = {c.cid: 0.95 for c in L.reference_library()
              if c.operation != "exact_count"}
    tables = SY.tables_from_rates(with_overrides(flat(), others))
    cov = report(tables, matrix)["coverage"]
    assert not cov["P3"]["supported"]
    assert any(r.startswith("G5_ADDS_0_OTHER_OPERATION") for r in
               cov["P3"]["reasons"])


def test_feasibility_failure_names_its_causes(matrix):
    far = {cid: 0.95 for cid in WORD_REFS}
    tables = SY.tables_from_rates(with_overrides(flat(), far))
    result = CAL.finalize(tables, CFG0, matrix)
    assert result["status"] == "INFEASIBLE_REVISION_REQUIRED"
    f = result["feasibility"]["P1"]
    assert not f["feasible"] and f["supported_configurations"] == 0
    assert "G1_TOO_FEW_DISTINCT_WORDS" in f["reason_counts"]
    assert result["feasibility"]["P3"]["feasible"]
    assert any("A_COVERAGE_INADEQUATE" in x for x in result["a"]["flags"])


# --------------------------------------------------------- A and B selection

def test_b_selection_prefers_informative_and_separated_limits():
    tables = SY.tables_from_rates(flat())
    b = CAL.select_b(tables, CFG0)
    assert b["status"] == "SELECTED" and b["selected"] == [9, 12]
    assert b["per_limit"][8]["informative"] == 0


def test_b_selection_reports_extremes_rather_than_dropping_them():
    rates = flat()
    rates[("qwen3-4b", "F0", "B.max12")] = 0.99       # extreme, still chosen
    rates[("qwen3-4b", "F0", "B.max11")] = 0.99
    b = CAL.select_b(SY.tables_from_rates(rates), CFG0)
    assert b["selected"] == [9, 12]
    assert any("B12 qwen3-4b|F0" in x for x in b["measurement_limitations"])


def test_b_selection_fails_without_an_admissible_pair():
    b = CAL.select_b(SY.tables_from_rates(flat(p_b={m: 0.5 for m in range(8, 14)})),
                     CFG0)
    assert b["status"] == "FAILED" and b["selected"] is None


def test_a_selection_prefers_four_on_a_tie(matrix):
    far = {cid: 0.95 for cid in WORD_REFS}
    for w in ("indeed", "instead", "perhaps", "although"):
        far[f"ew.{w}.4"] = 0.5
    tables = SY.tables_from_rates(with_overrides(flat(), far))
    elig = R.eligibility(tables, CFG0)
    a = CAL.select_a(tables, CFG0, matrix, elig, [9, 12])
    assert [r["g1_supported"] for r in a["ranking"]] == [16, 16, 16]
    assert a["selected"] == "A.however.4" and not a["flags"]


def test_a_selection_follows_g1_coverage_before_preference(matrix):
    rates = with_overrides(flat(p_ref=0.6), {
        "A.however.2": 0.9, "A.however.4": 0.9, "A.however.6": 0.3,
        "ew.indeed.2": 0.3, "ew.instead.2": 0.3, "ew.perhaps.2": 0.3})
    tables = SY.tables_from_rates(rates)
    a = CAL.select_a(tables, CFG0, matrix, R.eligibility(tables, CFG0), [9, 12])
    assert a["selected"] == "A.however.6"


def test_no_per_model_fallback_when_a_is_inadequate(matrix):
    tables = SY.tables_from_rates(flat(p_a=0.05, p_ref=0.9))
    a = CAL.select_a(tables, CFG0, matrix, R.eligibility(tables, CFG0), [9, 12])
    # D08 (revised): no admissible global count -> no A at all, never a
    # per-model choice and never a floor-level A.
    assert a["status"] == "FAILED" and a["selected"] is None
    assert any("A_HEADROOM_INADEQUATE" in f for f in a["flags"])
    assert all(not r["admissible"] for r in a["ranking"])


# ----------------------------------------------------------------- Stage 2

def test_stage2_is_deterministic_bounded_and_prioritised():
    tables = SY.tables_from_rates(SY.full_rates(), n=32)
    cfg = CFG.PilotConfig(stage2_max_cells=50)
    one, two = CAL.select_stage2(tables, cfg), CAL.select_stage2(tables, cfg)
    assert one == two and one["n_selected"] == 50 and one["truncated_by_cap"]
    ranks = [CAL.STAGE2_CLASSES.index(c["class"]) for c in one["cells"]]
    assert ranks == sorted(ranks)
    assert all(c["condition"] != "task_only" for c in one["cells"])
    assert len({(c["model"], c["frame"], c["condition"])
                for c in one["cells"]}) == 50


def test_stage2_targets_the_eligibility_boundary():
    rates = with_overrides(flat(p_ref=0.9), {"inc.simple": 0.19})
    tables = SY.tables_from_rates(rates, n=32)
    sel = CAL.select_stage2(tables, CFG0)
    cells = [c for c in sel["cells"] if c["condition"] == "inc.simple"]
    assert len(cells) == 8 and {c["class"] for c in cells} == {"ELIGIBILITY_20"}


def test_stage2_ignores_clear_cells():
    rates = flat(p_a=0.5, p_ref=0.99,
                 p_b={8: 0.5, 9: 0.5, 10: 0.5, 11: 0.5, 12: 0.5, 13: 0.5})
    sel = CAL.select_stage2(SY.tables_from_rates(rates, n=400), CFG0)
    assert sel["n_selected"] == 0
