"""§8.1 calibration and gate logic (Gate 1 executable parts, Gate 2 rules)."""
import json

import pytest

pytestmark = pytest.mark.cpu

from dci1.calibration.gate1 import (
    build_annotation_packet,
    determinism_test,
    evaluate_human_agreement,
    item_behaviour,
    wilson_upper,
)
from dci1.calibration.gate2 import evaluate_gate2, parse_solo_arm, solo_failure


def _rates(target=(0.30, 0.32, 0.60), focal=(0.28, 0.31, 0.45, 0.62),
           candidates=None):
    rates = {}
    for n, r in zip((1, 2, 3), target):
        rates[f"solo:A:n={n}"] = r
    for m, r in zip((7, 8, 9, 10), focal):
        rates[f"solo:B:m={m}"] = r
    candidates = candidates or {f"C{i}": 0.30 for i in range(1, 13)}
    for cid, r in candidates.items():
        rates[f"solo:{cid}"] = r
    return rates


def test_gate2_selection_closest_to_030_and_bands():
    record = evaluate_gate2(_rates())
    assert record["selected_n"] == 1          # 0.30 closest
    assert record["selected_m"] == 8          # 0.31 beats 0.28? no: |0.28-0.3|=0.02 < 0.01? 0.31 is 0.01 away
    assert record["passed"], record["failure_reasons"]
    assert len(record["references"]) == 3
    assert record["certificates"]


def test_gate2_band_failure_is_terminal_and_reported():
    rates = _rates(target=(0.70, 0.80, 0.90))
    record = evaluate_gate2(rates)
    assert not record["passed"]
    assert any("outside" in r for r in record["failure_reasons"])


def test_gate2_admission_window_and_ranking():
    candidates = {f"C{i}": 0.90 for i in range(1, 13)}
    candidates["C4"] = 0.33     # distance 0.02 from focal 0.31
    candidates["C7"] = 0.30     # distance 0.01
    candidates["C9"] = 0.36     # distance 0.05
    candidates["C10"] = 0.40    # distance 0.09 — admitted, ranked 4th
    record = evaluate_gate2(_rates(candidates=candidates))
    assert record["admitted_count"] == 4
    assert record["references"] == ["C7", "C4", "C9"]
    assert record["passed"]


def test_gate2_insufficient_candidates_is_scientific_result():
    candidates = {f"C{i}": 0.90 for i in range(1, 13)}
    candidates["C4"] = 0.31
    record = evaluate_gate2(_rates(candidates=candidates))
    assert not record["passed"]
    assert record["admitted_count"] == 1
    assert any("scientific result" in r for r in record["failure_reasons"])


def test_solo_failure_semantics():
    assert solo_failure("However, fine.", "A", n=1) == 0
    assert solo_failure("no target here", "A", n=1) == 1
    assert solo_failure("short words only", "B", m=7) == 0
    assert solo_failure("extraordinary", "B", m=7) == 1
    assert solo_failure("big bad bear", "C3") == 1
    assert parse_solo_arm("solo:A:n=2") == {"constraint_id": "A", "n": 2,
                                            "m": None}


def test_determinism_across_three_processes():
    responses = ["However, one.", "", "no match", "howeverhowever"]
    result = determinism_test(responses)
    assert result["agreement"] == 1.0 and result["passed"]


def test_item_behaviour_tabulation():
    per_topic = {"t1": {1: 1, 2: 1, 3: 1}, "t2": {1: 0, 2: 0, 3: 0},
                 "t3": {1: 0, 2: 1, 3: 0}}
    result = item_behaviour(per_topic)
    assert result["floor_share"] == pytest.approx(1 / 3)
    assert result["ceiling_share"] == pytest.approx(1 / 3)
    assert result["identical_share"] == pytest.approx(2 / 3)


def test_wilson_upper_bound_matches_prereg_example():
    # §18: 2 disagreements out of 75 → 95% Wilson upper bound 0.092.
    assert wilson_upper(2, 75) == pytest.approx(0.092, abs=0.0015)


def test_annotation_packet_blinded_and_evaluator(tmp_path):
    rows = []
    for i in range(200):
        text = "However, fine." if i % 2 == 0 else "missing entirely"
        rows.append({"row_id": f"r{i}", "arm": "solo:A:n=1",
                     "raw_response": text, "block_id": f"t{i}"})
    packet = build_annotation_packet(rows, tmp_path, "modelx")
    assert packet["items"] == 150
    blinded = [json.loads(l) for l in
               (tmp_path / "annotation_packet.jsonl").read_text().splitlines()]
    for item in blinded:
        assert set(item) == {"item_id", "response_text", "constraint_text",
                             "n"}          # no arm, no added constraint
    truth = json.loads((tmp_path / "annotation_truth.json").read_text())
    labels_path = tmp_path / "labels.jsonl"
    with labels_path.open("w") as handle:
        for item_id, verdict in truth.items():
            for annotator in ("a1", "a2", "a3"):
                handle.write(json.dumps({"item_id": item_id,
                                         "annotator": annotator,
                                         "label": verdict}) + "\n")
    result = evaluate_human_agreement(tmp_path / "annotation_truth.json",
                                      labels_path)
    assert result["passed"]
    assert result["disagreements"] == {"pass": 0, "fail": 0}


def test_human_agreement_fails_above_two_disagreements(tmp_path):
    truth = {f"i{k}": ("pass" if k < 75 else "fail") for k in range(150)}
    (tmp_path / "truth.json").write_text(json.dumps(truth))
    labels_path = tmp_path / "labels.jsonl"
    with labels_path.open("w") as handle:
        for k, (item_id, verdict) in enumerate(truth.items()):
            wrong = k < 3                     # 3 majority errors in 'pass'
            label = ("fail" if verdict == "pass" else "pass") if wrong \
                else verdict
            for annotator in ("a1", "a2", "a3"):
                handle.write(json.dumps({"item_id": item_id,
                                         "annotator": annotator,
                                         "label": label}) + "\n")
    result = evaluate_human_agreement(tmp_path / "truth.json", labels_path)
    assert not result["passed"]
    assert result["disagreements"]["pass"] == 3
