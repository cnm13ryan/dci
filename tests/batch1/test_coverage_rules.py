"""D11: reference admission keeps every qualifying reference (no cap), the
coverage-rule study evaluates its rules on the same pilot (paired), and the
design rule in the study is the pipeline's own rule."""
from __future__ import annotations

from fractions import Fraction

import pytest

from dci.batch1 import calibration as CAL
from dci.batch1 import compatibility as COMPAT
from dci.batch1 import config as CFG
from dci.batch1 import coverage_study as C
from dci.batch1 import library as L
from dci.batch1 import references as R
from dci.batch1 import simulate as S

pytestmark = pytest.mark.cpu
BY_ID = L.constraint_by_id()


@pytest.fixture(scope="module")
def moderate():
    tables = S.truth_tables("moderate")
    return tables, CAL.finalize(tables, S.CFG0, S._matrix())


def test_admission_keeps_every_qualifying_reference(moderate):
    """G5 is exactly {eligible, B-compatible, matched, not A}: recomputed here
    from the tables without the population code, so no cap or sample."""
    tables, result = moderate
    a = BY_ID[result["a"]["selected"]]
    eligible = R.eligible_ids(result["eligibility"])
    for rep in result["configurations"]:
        m, f, lim = rep["model"], rep["frame"], rep["b_limit"]
        pa = tables.x(m, f, a.cid)
        want = set()
        for c in L.reference_library():
            px = tables.x(m, f, c.cid)
            if c.cid in eligible and \
                    c.cid in COMPAT.compatible_ids(S._matrix(), lim) and \
                    abs(Fraction(px.k, px.n) - Fraction(pa.k, pa.n)) \
                    <= Fraction(1, 10):
                want.add(c.cid)
        assert set(rep["populations"]["G5"]) == want


def test_a_large_matched_pool_is_admitted_whole():
    """Every reference matched: G5 is the whole compatible eligible pool."""
    tables = S.truth_tables("moderate")
    a = BY_ID["A.however.4"]
    for key, count in list(tables.explicit.items()):
        m, f, cid = key.split("|")
        if BY_ID.get(cid) and BY_ID[cid].role == "reference":
            tables.explicit[key] = tables.x(m, f, a.cid)
    elig = R.eligibility(tables, S.CFG0)
    rep = R.configuration_report(tables, S.CFG0, S._matrix(), elig, a,
                                 "qwen3-4b", "F0", 12)
    assert set(rep["populations"]["G5"]) == set(rep["populations"]["G6"])
    assert len(rep["populations"]["G5"]) == len(
        [c for c in COMPAT.compatible_ids(S._matrix(), 12)
         if BY_ID[c].role == "reference"])


def test_the_design_rule_is_the_pipelines_rule(moderate):
    _, result = moderate
    a = BY_ID[result["a"]["selected"]]
    design = next(r for r in C.RULES if r.design)
    v = C.rule_verdict(result["configurations"], a, result["b"]["selected"],
                       design)
    assert v["feasible"] == (result["status"] == "FEASIBLE")
    for p in C.CONTRASTS:
        assert v[p]["supported"] == \
            result["feasibility"][p]["supported_configurations"]


def test_rules_are_paired_and_a_stricter_count_never_adds_support(moderate):
    _, result = moderate
    a = BY_ID[result["a"]["selected"]]
    rules = {r.name: r for r in C.RULES}
    for rep in result["configurations"]:
        for strict in ("P3k3", "P3k4", "P3k5", "P3k3c2"):
            if C.supported(rep, a, rules[strict], "P3"):
                assert C.supported(rep, a, rules["D"], "P3")


def test_one_pilot_record_scores_every_rule_on_the_same_draw():
    rec = C._pilot_record("other_operation_harder", S.ALLOCATIONS[0], 7)
    assert set(rec["verdicts"]["actual"]) == {r.name for r in C.RULES}
    # The pipeline's own verdict is the study's rule for the configured
    # minimum: P3k3 since the researcher's D11 decision of 2026-10-25 (the
    # design rule "D" keeps the design value 2, for comparison).
    k = CFG.DEFAULT_CONFIG.p3_min_additional_other_operation
    configured = "D" if k == 2 else f"P3k{k}"
    assert bool(rec["verdicts"]["actual"][configured][0]) == \
        (rec["status"] == "FEASIBLE")


@pytest.mark.parametrize("rule,expected", [("D", 14), ("P3k3", 10),
                                            ("P3k4", 6), ("P3k5", 2)])
def test_graded_coverage_truth_is_as_designed(rule, expected):
    truth = C._truth("graded_coverage")
    assert truth["verdicts"][rule]["P3"]["supported"] == expected
