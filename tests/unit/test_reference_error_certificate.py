"""The joint certificate must charge mismatch in the unit its slope was fitted in.

`_slope_block` fits the g and r slopes against the MEAN across those families.
Pre-repair the certificate reused that family slope once per family MEMBER, so a
family-level model predicting 0.01 of burden difference was charged 0.06.
"""
import numpy as np
import pandas as pd
import pytest

from dci.analysis.reference_error import (FAMILY_AGGREGATION, aggregate_family,
                                          assert_certificate_complete,
                                          certificate_terms, component_support,
                                          family_slopes,
                                          legacy_componentwise_total,
                                          reference_error_certificate)

pytestmark = pytest.mark.cpu

U = ["ua", "ub", "uc"]
ORDERS = ["target_first", "added_first"]
WORDING = ["s_d", "s_g", "s_r"]
G = [f"g|{u}|{o}" for u in U for o in ORDERS]
R = [f"r|{u}|{o}" for u in U for o in ORDERS]
COMPONENTS = ["d", *G, *R, *WORDING]


def _family(component: str) -> str:
    if component.startswith("g|"):
        return "g"
    if component.startswith("r|"):
        return "r"
    if component in WORDING:
        return "s"
    return component


def _calipers(slopes=None) -> pd.DataFrame:
    slopes = slopes or {"d": 0.5, "g": 0.5, "r": 0.5, "s": 0.5}
    rows = [{"component": c, "family": _family(c),
             "slope_used": slopes[_family(c)],
             "caliper": 0.10} for c in COMPONENTS]
    return pd.DataFrame(rows).set_index("component")


def _gaps(per_component: dict, candidates=("C1",)) -> pd.DataFrame:
    return pd.DataFrame(
        [{c: per_component.get(c, 0.0) for c in COMPONENTS} for _ in candidates],
        index=list(candidates))


def _zero_se(candidates=("C1",)) -> pd.DataFrame:
    return pd.DataFrame([{c: 0.0 for c in COMPONENTS} for _ in candidates],
                        index=list(candidates))


# ------------------------------------------------------------- the unit repair
def test_common_family_movement_is_charged_once():
    """Six g coordinates each off by 0.02, s_g=0.5 -> the family term is 0.01."""
    gaps = _gaps({c: 0.02 for c in G})
    cal = _calipers()
    terms = certificate_terms(gaps, _zero_se(), cal, "C1", uncertainty_q=1.0)
    g_term = terms.set_index("family").loc["g"]
    assert g_term["n_components"] == 6
    assert g_term["aggregation"] == "mean_abs"
    assert g_term["aggregated_gap"] == pytest.approx(0.02)
    assert g_term["contribution"] == pytest.approx(0.01)


def test_legacy_formulation_overcounted_the_same_example_sixfold():
    """The regression-based prediction is 0.01; the pre-repair rule charged 0.06."""
    gaps = _gaps({c: 0.02 for c in G})
    cal = _calipers()
    legacy = legacy_componentwise_total(gaps, _zero_se(), cal, "C1", 1.0)
    terms = certificate_terms(gaps, _zero_se(), cal, "C1", uncertainty_q=1.0)
    repaired_g = float(terms.set_index("family").loc["g", "contribution"])
    assert legacy == pytest.approx(0.06)
    assert repaired_g == pytest.approx(0.01)
    assert legacy / repaired_g == pytest.approx(len(G))


def test_the_overcount_flipped_the_admission_decision():
    """A candidate the fitted model accepts, the legacy rule rejected."""
    gaps = _gaps({c: 0.02 for c in G})
    cal = _calipers()
    legacy = legacy_componentwise_total(gaps, _zero_se(), cal, "C1", 1.0)
    cert = reference_error_certificate(gaps, _zero_se(), cal, ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert legacy > 0.05                     # legacy: rejected
    assert bool(cert.loc["C1", "budget_ok"])  # repaired: admitted
    assert float(cert.loc["C1", "budget_total"]) == pytest.approx(0.01)


def test_one_family_per_row_not_one_component_per_row():
    terms = certificate_terms(_gaps({}), _zero_se(), _calipers(), "C1", 1.0)
    assert sorted(terms["family"]) == ["d", "g", "r", "s"]
    assert int(terms["n_components"].sum()) == len(COMPONENTS)


# ------------------------------------------------- conservatism is preserved
def test_uncertainty_can_only_make_admission_harder():
    gaps = _gaps({c: 0.02 for c in G})
    ses = _zero_se()
    ses.loc["C1", G] = 0.03
    strict = reference_error_certificate(gaps, ses, _calipers(), ["C1"],
                                        uncertainty_q=1.0, epsilon_ref=0.05)
    lenient = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                         uncertainty_q=1.0, epsilon_ref=0.05)
    assert (float(strict.loc["C1", "budget_total"])
            > float(lenient.loc["C1", "budget_total"]))


def test_mismatches_do_not_cancel_within_a_family():
    """Opposite-signed magnitudes must not offset: `gaps` carries |differences|."""
    balanced = _gaps({G[0]: 0.06, G[1]: 0.06})
    terms = certificate_terms(balanced, _zero_se(), _calipers(), "C1", 1.0)
    g_gap = float(terms.set_index("family").loc["g", "aggregated_gap"])
    assert g_gap == pytest.approx((0.06 + 0.06) / 6)
    assert g_gap > 0


def test_families_are_summed_so_cross_family_accumulation_is_bounded():
    gaps = _gaps({**{c: 0.02 for c in G}, **{c: 0.02 for c in R}, "d": 0.02})
    cert = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    # d + g + r = 0.01 + 0.01 + 0.01, s contributes 0
    assert float(cert.loc["C1", "budget_total"]) == pytest.approx(0.03)


def test_rss_is_a_separate_choice_not_the_unit_fix():
    gaps = _gaps({**{c: 0.02 for c in G}, **{c: 0.02 for c in R}, "d": 0.02})
    summed = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                        uncertainty_q=1.0, epsilon_ref=0.05,
                                        aggregation_mode="sum")
    rss = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                     uncertainty_q=1.0, epsilon_ref=0.05,
                                     aggregation_mode="rss")
    assert (float(rss.loc["C1", "budget_total"])
            < float(summed.loc["C1", "budget_total"]))
    # rss on the LEGACY componentwise terms would still exceed the family total,
    # which is why it was never a substitute for correcting the unit.
    legacy_rss = float(np.sqrt(np.sum(np.square(
        [0.5 * 0.02] * (len(G) + len(R) + 1)))))
    assert legacy_rss > float(summed.loc["C1", "budget_total"])


# --------------------------------------------------------------- definedness
def test_an_undefined_component_makes_the_total_undefined():
    gaps = _gaps({c: 0.02 for c in G})
    gaps.loc["C1", R[0]] = np.nan
    cert = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert not bool(cert.loc["C1", "budget_ok"])
    assert np.isnan(float(cert.loc["C1", "budget_total"]))
    assert int(cert.loc["C1", "n_undefined_components"]) == 1


def test_inconsistent_family_slopes_are_refused():
    cal = _calipers()
    cal.loc[G[0], "slope_used"] = 0.9
    with pytest.raises(ValueError, match="no longer constant within a family"):
        family_slopes(cal)


def test_aggregation_rules_match_the_fitted_predictors():
    assert FAMILY_AGGREGATION["g"] == "mean_abs"   # _slope_block uses nanmean
    assert FAMILY_AGGREGATION["r"] == "mean_abs"   # _slope_block uses nanmean
    assert FAMILY_AGGREGATION["s"] == "max_abs"    # _slope_block uses the max
    assert FAMILY_AGGREGATION["d"] == "single"     # a single coordinate
    assert aggregate_family(np.array([0.1, 0.3]), "mean_abs") == pytest.approx(0.2)
    assert aggregate_family(np.array([0.1, -0.3]), "max_abs") == pytest.approx(0.3)
    assert np.isnan(aggregate_family(np.array([np.nan]), "mean_abs"))


# ------------------------------------------------- fail-closed on the inputs
def test_a_missing_coordinate_is_not_a_matched_coordinate():
    """Dropping the column used to shrink the sum to fewer families."""
    gaps = _gaps({c: 0.02 for c in G}).drop(columns=["d"])
    cert = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert bool(cert.loc["C1", "certificate_complete"]) is False
    assert bool(cert.loc["C1", "budget_ok"]) is False
    assert not np.isfinite(float(cert.loc["C1", "budget_total"]))
    assert int(cert.loc["C1", "n_missing_components"]) == 1
    assert "missing coordinates" in str(cert.loc["C1", "incomplete_reason"])


def test_a_whole_family_absent_from_the_gap_table_is_reported():
    gaps = _gaps({}).drop(columns=G)
    cert = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert bool(cert.loc["C1", "budget_ok"]) is False
    assert int(cert.loc["C1", "n_missing_components"]) == len(G)
    assert int(cert.loc["C1", "n_components_declared"]) == len(COMPONENTS)


def test_a_missing_se_is_not_zero_uncertainty():
    ses = _zero_se().drop(columns=[G[0]])
    cert = reference_error_certificate(_gaps({c: 0.02 for c in G}), ses,
                                      _calipers(), ["C1"], uncertainty_q=1.0,
                                      epsilon_ref=0.05)
    assert bool(cert.loc["C1", "budget_ok"]) is False
    assert int(cert.loc["C1", "n_missing_se"]) == 1
    assert "missing SEs" in str(cert.loc["C1", "incomplete_reason"])


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_a_nonfinite_se_cannot_certify(bad):
    ses = _zero_se()
    ses.loc["C1", G[0]] = bad
    cert = reference_error_certificate(_gaps({c: 0.02 for c in G}), ses,
                                      _calipers(), ["C1"], uncertainty_q=1.0,
                                      epsilon_ref=0.05)
    assert bool(cert.loc["C1", "budget_ok"]) is False
    assert int(cert.loc["C1", "n_nonfinite_se"]) == 1


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_a_nonfinite_gap_cannot_certify(bad):
    gaps = _gaps({c: 0.02 for c in G})
    gaps.loc["C1", "d"] = bad
    cert = reference_error_certificate(gaps, _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert bool(cert.loc["C1", "budget_ok"]) is False
    assert bool(cert.loc["C1", "certificate_complete"]) is False


def test_a_complete_signature_still_certifies_exactly_as_before():
    """The fail-closed guard must not disturb the admissible case."""
    cert = reference_error_certificate(_gaps({c: 0.02 for c in G}), _zero_se(),
                                      _calipers(), ["C1"], uncertainty_q=1.0,
                                      epsilon_ref=0.05)
    assert bool(cert.loc["C1", "certificate_complete"]) is True
    assert bool(cert.loc["C1", "budget_ok"]) is True
    assert float(cert.loc["C1", "budget_total"]) == pytest.approx(0.01)
    assert str(cert.loc["C1", "incomplete_reason"]) == ""


def test_component_support_answers_from_the_declared_set():
    support = component_support(_gaps({}).drop(columns=["d"]), _zero_se(),
                               _calipers(), "C1")
    assert len(support) == len(COMPONENTS)
    assert bool(support.loc["d", "gap_present"]) is False
    assert bool(support.loc[G[0], "gap_present"]) is True


def test_assert_certificate_complete_raises_on_missing_evidence():
    cert = reference_error_certificate(_gaps({}).drop(columns=["d"]), _zero_se(),
                                      _calipers(), ["C1"], uncertainty_q=1.0,
                                      epsilon_ref=0.05)
    with pytest.raises(ValueError, match="incomplete reference signature"):
        assert_certificate_complete(cert)
    good = reference_error_certificate(_gaps({}), _zero_se(), _calipers(), ["C1"],
                                      uncertainty_q=1.0, epsilon_ref=0.05)
    assert_certificate_complete(good)          # does not raise
