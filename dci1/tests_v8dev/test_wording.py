"""The wording instrument: audit statistics on synthetic tables, and the
prospective v8 wording set's structural guarantees."""
from __future__ import annotations

import pytest

from dci1v7.protocol.wordings import wordings as v7_wordings
from dci1v8dev import wording as W
from dci1v8dev import wording_v8 as V8
from dci1v8dev.simulate_wording import FLAT, STEEP, simulate_wording_case


def _entry(kind, q, w, hist, n=192):
    return {"kind": kind, "severity": q, "wording": w, "n": n,
            "passed": hist.get(q, 0), "rate": hist.get(q, 0) / n,
            "vacuous_rate": 0.0, "histogram": {str(k): v for k, v in hist.items()},
            "mean_words": 80.0, "per_topic": {}}


def test_wording_table_reports_zero_over_under_and_the_gap_to_siblings():
    scan = {}
    for w in range(4):
        # w1 never uses the marker; the others hit q half the time
        hist = {0: 192} if w == 1 else {3: 96, 4: 48, 2: 48}
        scan[f"MK1:3:{w}"] = _entry("MK1", 3, w, hist)
    table = W.wording_table(scan)
    w1 = next(t for t in table if t["wording"] == 1)
    w0 = next(t for t in table if t["wording"] == 0)
    assert w1["zero"] == 1.0 and w1["exact"] == 0.0
    assert w1["gap_to_others"] == pytest.approx(-0.5)
    assert w0["over"] == pytest.approx(0.25) and w0["under"] == pytest.approx(0.25)


def test_flagging_is_relative_so_a_uniformly_hard_rung_flags_nothing():
    scan = {}
    for q in range(1, 9):
        for w in range(4):
            scan[f"MK1:{q}:{w}"] = _entry("MK1", q, w, {q: 40, q + 1: 152})
    assert not any(v["flagged"] for v in W.flag_wordings(W.wording_table(scan))["MK1"].values())
    for q in range(1, 9):
        scan[f"MK1:{q}:2"] = _entry("MK1", q, 2, {0: 150, q: 42})
    flags = W.flag_wordings(W.wording_table(scan))["MK1"]
    assert flags[2]["flagged"] and not flags[0]["flagged"]


def test_ladders_under_a_wording_subset_recover_the_shape():
    scan = {}
    truth = [0.95, 0.88, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30]
    for i, q in enumerate(range(1, 9)):
        for w in range(4):
            p = 0.30 if w in (1, 2) else truth[i]        # flat bad frames
            k = round(p * 192)
            scan[f"MK1:{q}:{w}"] = _entry("MK1", q, w, {q: k, 0: 192 - k})
    all4 = W.ladders_under(scan, wordings_used=range(4), iota_a=0.68)["MK1"]
    good = W.ladders_under(scan, wordings_used=[0, 3], iota_a=0.68)["MK1"]
    assert good["span_all"] > all4["span_all"]
    assert good["classification"] == "MONOTONE_USABLE"
    assert good["reaches_below"] and good["reaches_above"]


def test_the_simulation_separates_wording_flatness_from_true_flatness():
    conf = simulate_wording_case("x", STEEP, bad=[1, 3], p_confused=0.7, n_sims=20)
    assert conf["detection_rate_bad_frames"] > 0.9
    assert conf["span_after_repair"] > conf["apparent_span_all_frames"] + 0.1
    flat = simulate_wording_case("y", FLAT, bad=[], p_confused=0.0, n_sims=20)
    assert flat["false_flag_rate_good_frames"] < 0.1
    assert abs(flat["span_after_repair"] - flat["apparent_span_all_frames"]) < 0.05


def test_v8_frames_name_the_word_and_keep_a_and_mk_identical():
    info = V8.assert_v8_wordings()
    assert info["repaired_frames"] == [1, 2] and info["unchanged_frames"] == [0, 3]
    a = V8.v8_wordings("A", 3)
    mk = V8.v8_wordings("MK5", 3)
    assert [f.replace("indeed", "however") for f in mk] == list(a)
    assert a[1] == "Your answer must contain the word however exactly 3 times."
    assert a[2] == "Include the word however exactly 3 times in your answer."
    assert V8.v8_wordings("MK1", 1)[3] == "The word thus must appear exactly 1 time."


def test_v8_is_a_minimal_edit_of_v7_and_w0_w3_are_byte_identical():
    for kind in ("A", "MK1", "MK6"):
        for q in (1, 4, 8):
            diffs = V8.diff_from_v7(kind, q)
            assert [d["changed"] for d in diffs] == [False, True, True, False]
            assert all(d["inserted"] == ["the", "word"] for d in diffs if d["changed"])
            assert diffs[0]["v8"] == v7_wordings(kind, q)[0]
            assert diffs[3]["v8"] == v7_wordings(kind, q)[3]


def test_v8_refuses_a_family_that_is_not_an_exact_count_marker():
    with pytest.raises(ValueError):
        V8.v8_wordings("XC1", 3)
