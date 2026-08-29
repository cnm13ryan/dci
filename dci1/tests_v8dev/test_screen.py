"""The family screen: determinism, order invariance, statuses, labels."""
from __future__ import annotations

import random

import pytest

from dci1v4.errors import ProtocolError
from dci1v8dev.prescreen.screen import (
    LOCAL_LABEL,
    SCREEN_ACCEPT,
    SCREEN_REJECT,
    SCREEN_RESAMPLE,
    SPECTRUM_LABEL,
    ScreenConfig,
    screen_families,
)

from .conftest import a_grid, ladder, rung

WIDE = [0.98, 0.92, 0.86, 0.78, 0.66, 0.52, 0.38, 0.25]
FLAT = [0.70, 0.69, 0.68, 0.67, 0.67, 0.66, 0.65, 0.64]
NARROW = [0.80, 0.77, 0.74, 0.72, 0.70, 0.68, 0.66, 0.64]
ONE_SIDED = [0.55, 0.48, 0.42, 0.36, 0.30, 0.25, 0.20, 0.15]
CFG = ScreenConfig(draws=1500)


def _table():
    return (ladder("MK1", WIDE) + ladder("MK2", FLAT) + ladder("MK3", NARROW)
            + ladder("MK4", ONE_SIDED))


def test_results_depend_only_on_each_familys_counts_and_the_config():
    table = _table()
    one = screen_families(table, a_grid(), config=CFG)
    shuffled = list(table)
    random.Random(4).shuffle(shuffled)
    two = screen_families(shuffled, a_grid(), config=CFG)
    for k in one["families"]:
        assert one["families"][k]["p_spectrum"] == two["families"][k]["p_spectrum"]
        assert one["families"][k]["status"] == two["families"][k]["status"]
    assert one["ranking_spectrum"] == two["ranking_spectrum"]
    # screened alone, a family gets the same verdict as screened with others
    alone = screen_families(ladder("MK1", WIDE), a_grid(), config=CFG)
    assert alone["families"]["MK1"]["probabilities"] == \
        one["families"]["MK1"]["probabilities"]


def test_the_same_seed_reproduces_every_number_and_a_new_seed_moves_them():
    a = screen_families(_table(), a_grid(), config=CFG)
    b = screen_families(_table(), a_grid(), config=CFG)
    assert a["families"]["MK1"]["p_spectrum"] == b["families"]["MK1"]["p_spectrum"]
    c = screen_families(_table(), a_grid(), config=ScreenConfig(draws=1500, base_seed=7))
    # the seed moves the Monte Carlo estimate of every family whose
    # probability is not saturated, and only by Monte Carlo error
    interior = [k for k, v in a["families"].items() if 0.0 < v["p_spectrum"] < 1.0]
    assert interior
    assert any(c["families"][k]["p_spectrum"] != a["families"][k]["p_spectrum"]
               for k in interior)
    for k in a["families"]:
        assert abs(c["families"][k]["p_spectrum"] - a["families"][k]["p_spectrum"]) < 0.06


def test_statuses_separate_wide_flat_and_one_sided_ladders():
    out = screen_families(_table(), a_grid(), config=CFG)
    fam = out["families"]
    assert fam["MK1"]["p_spectrum"] > fam["MK3"]["p_spectrum"] >= fam["MK2"]["p_spectrum"]
    assert fam["MK1"]["p_spectrum"] > 0.7 and fam["MK2"]["p_spectrum"] < 0.05
    assert fam["MK2"]["status"] == SCREEN_REJECT           # flat
    assert fam["MK4"]["status"] == SCREEN_REJECT           # one-sided
    assert fam["MK4"]["deficiency"] == "MISSING_ABOVE"
    assert fam["MK1"]["status"] in (SCREEN_ACCEPT, SCREEN_RESAMPLE)
    assert fam["MK1"]["probabilities"]["c4"] > 0.8


def test_labels_are_separate_from_statuses():
    out = screen_families(_table(), a_grid(), config=CFG)
    fam = out["families"]
    # the flat family sits at A: a local candidate, never a spectrum one
    assert LOCAL_LABEL in fam["MK2"]["labels"]
    assert SPECTRUM_LABEL not in fam["MK2"]["labels"]
    # the one-sided family is neither
    assert fam["MK4"]["labels"] == []
    assert set(out["labels"]) == {LOCAL_LABEL, SPECTRUM_LABEL}


def test_a_chance_inflated_rung_does_not_buy_spectrum_support():
    # a Tier-3 family whose easy extreme is mostly chance
    chance_free = [rung("RF6", q, k) for q, k in zip((1, 2, 3), (22, 14, 6))]
    inflated = [rung("RF6", 1, 22, chance=0.85), rung("RF6", 2, 14),
                rung("RF6", 3, 6)]
    free = screen_families(chance_free, a_grid(), config=CFG)["families"]["RF6"]
    chance = screen_families(inflated, a_grid(), config=CFG)["families"]["RF6"]
    assert chance["probabilities"]["support_above"] < free["probabilities"]["support_above"]
    assert chance["rungs"][0]["p_chance_over_ceiling"] > 0.8


def test_the_comparators_are_reported_on_point_eligible_rungs_only():
    out = screen_families(ladder("MK1", WIDE), a_grid(), config=CFG)
    comp = out["families"]["MK1"]["comparators"]
    # 0.98 and 0.92 are outside the point band, so the raw span excludes them
    assert comp["raw_span"] == pytest.approx(0.86 - 0.25, abs=0.05)
    assert comp["conservative_span_90"] <= comp["conservative_span_68"] <= comp["raw_span"]


def test_config_validation():
    with pytest.raises(ProtocolError):
        ScreenConfig(accept=0.2, reject=0.3)
    with pytest.raises(ProtocolError):
        ScreenConfig(spectrum_event="composed")
    with pytest.raises(ProtocolError):
        ScreenConfig(draws=10)


def test_iota_a_posterior_reflects_the_severity_reselection():
    out = screen_families(ladder("MK1", WIDE), a_grid(), config=CFG)
    ia = out["iota_a"]
    assert 0.55 < ia["iota_a_mean"] < 0.78 and ia["iota_a_sd"] > 0.02
    assert sum(ia["n_star_distribution"].values()) == pytest.approx(1.0)
    assert len(ia["n_star_distribution"]) >= 2
