"""The frame-blind pre-screen diagnostic (`tools/v8_frame_screen_diagnostic.py`).

Two contracts, on synthetic rows only:

1.  the retrospective ranking is deterministic --- the same rungs in any
    input order give the same order, the same ranks and the same distances,
    with ties broken by label and never by dictionary order;
2.  a rung inside frame f's caliper whose *pooled* coordinate sits outside it
    is flagged as a candidate the pooled forwarded set omitted, and the
    converse case --- forwarded, but outside the frame's caliper --- is
    flagged on the other side.

The diagnostic reads records and changes nothing, so there is nothing else to
protect here: these are the two pieces of arithmetic the report's counts rest
on.
"""
from __future__ import annotations

import itertools

from dci1v7.protocol import constants as C

from tools.v8_frame_screen_diagnostic import (calibration_iota_by_frame,
                                              cross_frame_spread,
                                              frame_aware_vs_pooled,
                                              rank_by_distance)

IOTA_A = 0.60
CALIPER = C.REFERENCE_CALIPER

#: One rung per family. NEAR:1 and TIE:1 are equidistant from iota_A, so the
#: label is the only thing that can order them.
SCREEN_IOTA = {
    "NEAR:1": 0.62,     # inside the frame caliper
    "TIE:1": 0.58,      # the same distance, other side
    "FAR:1": 0.95,      # far above
    "LOW:1": 0.10,      # far below
    "EDGE:1": 0.70,     # exactly on the caliper
}


def _synthetic_calibration_payload() -> dict:
    """A Gate-2-shaped payload: two frames, three rungs, §13.11 row keys."""
    def row(kind, severity, solo, chance, per_topic):
        return {"kind": kind, "severity": severity, "solo_compliance": solo,
                "chance_compliance": chance, "per_topic_solo": list(per_topic),
                "n_topics": len(per_topic), "split": "pooled"}

    return {
        "supported_frames": [0, 1],
        "by_frame": {
            "0": {"iota_a": 0.60, "n_star": 5, "m_star": 9, "n_topics_a": 96,
                  "calibration_rows": {"pooled": [
                      row("NEAR", 1, 0.62, 0.0, [0.5, 0.75, 0.5, 0.75]),
                      row("FAR", 1, 0.95, 0.0, [1.0, 0.9, 1.0, 0.9]),
                      # kappa at the degeneracy bound: no coordinate exists
                      row("DEGEN", 1, 1.0, C.CHANCE_DEGENERACY_MAX, [1.0, 1.0]),
                  ]}},
            "1": {"iota_a": 0.55, "n_star": 5, "m_star": 9, "n_topics_a": 96,
                  "calibration_rows": {"pooled": [
                      row("NEAR", 1, 0.30, 0.0, [0.25, 0.5, 0.25, 0.2]),
                      row("FAR", 1, 0.90, 0.0, [1.0, 0.8, 1.0, 0.8]),
                  ]}},
            # an unsupported frame carries no table and must be ignored
            "2": {"status": "UNSUPPORTED"},
        },
    }


# ------------------------------------------------------------ determinism
def test_ranking_is_deterministic_under_input_order():
    reference = rank_by_distance(SCREEN_IOTA, IOTA_A)
    # NEAR:1 and TIE:1 are an exact tie once the protocol's tie_key rounding
    # is applied, and the label breaks it: binary floats alone would not.
    assert [e["label"] for e in reference] == ["NEAR:1", "TIE:1", "EDGE:1",
                                              "FAR:1", "LOW:1"]
    assert reference[0]["distance"] == reference[1]["distance"]
    assert [e["rank"] for e in reference] == [1, 2, 3, 4, 5]
    for order in itertools.permutations(SCREEN_IOTA):
        shuffled = {label: SCREEN_IOTA[label] for label in order}
        assert rank_by_distance(shuffled, IOTA_A) == reference


def test_ranking_ties_break_on_label_not_insertion_order():
    tied = {"BBB:1": 0.65, "AAA:1": 0.55}
    ranked = rank_by_distance(tied, IOTA_A)
    assert [e["label"] for e in ranked] == ["AAA:1", "BBB:1"]
    assert ranked[0]["distance"] == ranked[1]["distance"]
    assert rank_by_distance({"AAA:1": 0.55, "BBB:1": 0.65}, IOTA_A) == ranked


def test_ranking_drops_unmeasured_rungs_and_keeps_no_partial_rank():
    ranked = rank_by_distance({**SCREEN_IOTA, "MISSING:1": None}, IOTA_A)
    assert "MISSING:1" not in {e["label"] for e in ranked}
    assert [e["rank"] for e in ranked] == list(range(1, len(ranked) + 1))


# ------------------------------------------------- the frame-blindness flag
def test_rung_inside_the_frame_caliper_but_outside_the_pooled_one_is_flagged():
    """The finding, in one cell: NEAR:1 matches on frame f and was never forwarded."""
    ranked = rank_by_distance(SCREEN_IOTA, IOTA_A)
    pooled_distance = {"NEAR:1": 0.30,   # pooled coordinate far from pooled iota_A
                       "TIE:1": 0.02, "EDGE:1": 0.40, "FAR:1": 0.35,
                       "LOW:1": 0.50}
    result = frame_aware_vs_pooled(ranked, forwarded=["TIE:1", "FAR:1"],
                                   pooled_distance=pooled_distance,
                                   caliper=CALIPER)
    flagged = {r["label"]: r for r in result["would_forward_but_pooled_did_not"]}
    assert "NEAR:1" in flagged
    near = flagged["NEAR:1"]
    assert near["distance_frame"] <= CALIPER
    assert near["distance_pooled"] > CALIPER
    assert near["pooled_outside_caliper"] is True
    assert near["forwarded"] is False
    # EDGE:1 sits exactly on the caliper: inclusive, by the same <= the
    # protocol's V_diff uses.
    assert "EDGE:1" in flagged
    # a forwarded rung is never counted as withheld, however near it is
    assert "TIE:1" not in flagged
    assert result["n_would_forward_but_pooled_did_not"] == len(flagged)
    assert result["n_families_would_forward"] == len({"NEAR", "EDGE"})


def test_the_converse_forwarded_but_outside_this_frames_caliper():
    ranked = rank_by_distance(SCREEN_IOTA, IOTA_A)
    result = frame_aware_vs_pooled(ranked, forwarded=["FAR:1", "NEAR:1"],
                                   pooled_distance={}, caliper=CALIPER)
    converse = {r["label"] for r in
                result["forwarded_but_outside_this_frame_caliper"]}
    assert converse == {"FAR:1"}
    assert result["n_forwarded_but_outside"] == 1
    # an unknown pooled coordinate is reported as unknown, never as False
    assert all(r["pooled_outside_caliper"] is None
               for r in result["would_forward_but_pooled_did_not"])


# ---------------------------------------------- iota and spread arithmetic
def test_calibration_iota_is_derived_and_degenerate_rungs_are_dropped():
    cal = calibration_iota_by_frame(_synthetic_calibration_payload())
    assert sorted(cal) == [0, 1]                    # frame 2 was never supported
    assert set(cal[0]["rungs"]) == {"NEAR:1", "FAR:1"}   # DEGEN:1 withheld
    assert cal[0]["rungs"]["NEAR:1"]["iota"] == 0.62     # kappa 0 => iota = solo
    assert cal[0]["rungs"]["NEAR:1"]["se_iota"] > 0.0


def test_cross_frame_spread_is_max_minus_min_over_frames():
    payload = _synthetic_calibration_payload()
    cal = calibration_iota_by_frame(payload)
    screen = {"NEAR:1": {0: {"iota": 0.60, "se_iota": 0.16, "n_topics": 6},
                         1: {"iota": 0.20, "se_iota": 0.16, "n_topics": 6}}}
    spread = cross_frame_spread(screen, cal)
    assert spread["calibration"]["per_rung"]["NEAR:1"] == 0.62 - 0.30
    assert spread["calibration"]["per_rung"]["FAR:1"] == 0.95 - 0.90
    # a family's value is the median over its rungs; one rung each here
    assert spread["calibration"]["per_family_median_over_its_rungs"] == {
        "NEAR": 0.62 - 0.30, "FAR": 0.95 - 0.90}
    assert spread["calibration"]["n_families_above_caliper"] == 1
    assert spread["screen"]["per_rung"]["NEAR:1"] == 0.60 - 0.20
    assert spread["screen"]["noise"]["topics_per_frame"] == [6]
    assert spread["screen"]["noise"]["median_se_iota"] == 0.16
