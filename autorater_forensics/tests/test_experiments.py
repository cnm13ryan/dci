"""Smoke checks for the pre-registered experiment machinery
(PREREGISTERED.md): sample-set construction, blindness of the human
review app, refusal rules, and parsing helpers."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def dataset_rows():
    return [json.loads(l) for l in
            (ROOT / "dataset" / "diagnostic.jsonl").read_text()
            .splitlines()]


def test_exp1_dataset_covers_all_truncated_plus_matched_controls():
    merged = {r["id"]: r for r in map(json.loads,
              (ROOT / "analysis" / "out" / "merged.jsonl").read_text()
              .splitlines())}
    exp1 = [json.loads(l) for l in
            (ROOT / "dataset" / "exp1_cap.jsonl").read_text()
            .splitlines()]
    ids = [r["id"] for r in exp1]
    assert len(ids) == len(set(ids))
    truncated_anywhere = {i for i, m in merged.items() if any(
        m[f"{e}_truncated"] for e in ("low", "medium", "high"))}
    assert truncated_anywhere <= set(ids)
    for r in exp1:
        if r["id"] not in truncated_anywhere:
            assert not merged[r["id"]]["high_truncated"]


def test_exp2_subset_composition():
    exp2 = [json.loads(l) for l in
            (ROOT / "dataset" / "exp2_repeat.jsonl").read_text()
            .splitlines()]
    assert len(exp2) == 120
    controls = [r for r in exp2 if not r["contested"]]
    assert len(controls) == 61          # every control included
    all_ids = {r["id"] for r in dataset_rows()}
    assert {r["id"] for r in exp2} <= all_ids


def test_calibration_sample_probabilities_recorded_and_consistent():
    cal = json.loads((ROOT / "experiments" / "human_review"
                      / "calibration_sample.json").read_text())
    samples = cal["samples"]
    assert len(samples) == 56
    assert len({s["id"] for s in samples}) == 56
    by_stratum = {}
    for s in samples:
        assert 0 < s["inclusion_probability"] <= 1
        by_stratum.setdefault(tuple(s["stratum"]), set()).add(
            s["inclusion_probability"])
    # within a stratum every item has the same known probability
    assert all(len(ps) == 1 for ps in by_stratum.values())
    alloc = cal["allocation"]
    assert sum(alloc.values()) == 56


def test_reserved_set_sealed_and_disjoint():
    reserved = json.loads((ROOT / "experiments"
                           / "reserved_final_check_ids.json")
                          .read_text())
    ids = set(reserved["ids"])
    assert len(ids) == 40
    diag_ids = {r["id"] for r in dataset_rows()}
    assert not ids & diag_ids           # never exposed to diagnosis
    cal = json.loads((ROOT / "experiments" / "human_review"
                      / "calibration_sample.json").read_text())
    assert not ids & {s["id"] for s in cal["samples"]}
    assert "SEALED" in reserved["note"]


def test_review_app_display_is_blind():
    app = load("review_app_t", "experiments/human_review/review_app.py")
    items = app.load_items("calibration")
    assert len(items) == 56
    forbidden = ("label", "verifier", "effort", "judge", "scout",
                 "s0", "reasoning")
    for it in items:
        for key in it:
            assert not any(f in key.lower() for f in forbidden), key
        # display fields only
        assert set(it) == {"id", "n", "constraint", "response"}


def test_review_app_refuses_scripted_input(tmp_path, monkeypatch):
    app = load("review_app_t2",
               "experiments/human_review/review_app.py")
    monkeypatch.setattr(app, "record_path",
                        lambda s, a: tmp_path / f"{s}_{a}.jsonl")
    # stdin is not a tty under pytest -> must refuse without selftest
    with pytest.raises(SystemExit, match="human"):
        app.review("calibration", "nobody", None)


def test_review_app_selftest_records_marked_synthetic(tmp_path,
                                                      monkeypatch):
    app = load("review_app_t3",
               "experiments/human_review/review_app.py")
    rec = tmp_path / "calibration_selftest.jsonl"
    monkeypatch.setattr(app, "record_path", lambda s, a: rec)
    n = len(app.load_items("calibration"))
    app.review("calibration", "selftest",
               (["S", "V", "U"] * (n // 3 + 1))[:n])
    rows = [json.loads(l) for l in rec.read_text().splitlines()]
    assert len(rows) == n
    assert all(r["synthetic"] for r in rows)
    assert {r["label"] for r in rows} <= {"SATISFIES", "VIOLATES",
                                          "UNSURE"}
    # append-only resume: nothing left afterwards
    app.review("calibration", "selftest", [])


def test_reveal_refused_before_judgment(tmp_path, monkeypatch):
    app = load("review_app_t4",
               "experiments/human_review/review_app.py")
    monkeypatch.setattr(app, "record_path",
                        lambda s, a: tmp_path / "empty.jsonl")
    with pytest.raises(SystemExit, match="hidden"):
        app.reveal("calibration", "nobody", "gemma-3n-e2b-it::x")


def test_agreement_report_refuses_synthetic_records(tmp_path):
    rec = tmp_path / "records.jsonl"
    rec.write_text(json.dumps({"id": "a", "label": "SATISFIES",
                               "synthetic": True}) + "\n")
    cfg = tmp_path / "cfg.jsonl"
    cfg.write_text(json.dumps({"sample_id": "a", "label": "pass",
                               "status": "valid"}) + "\n")
    import subprocess
    proc = subprocess.run(
        [sys.executable,
         str(ROOT / "experiments" / "human_review"
             / "agreement_report.py"),
         "--records", str(rec), "--config", f"c={cfg}"],
        capture_output=True, text=True)
    assert proc.returncode != 0
    assert "synthetic" in proc.stderr


def test_harmony_final_extraction():
    an = load("exp3_analyze_t", "experiments/exp3_path/analyze.py")
    raw = ("<|channel|>analysis<|message|>count... 3 times."
           "<|end|><|start|>assistant<|channel|>final<|message|>"
           "VIOLATES\nAppears 3 times, not 4.<|return|>")
    assert an.harmony_final(raw) == \
        "VIOLATES\nAppears 3 times, not 4."
    assert an.harmony_final("truncated analysis only") is None


def test_no_writes_to_registered_evidence_by_set_builder():
    evidence = ROOT.parent / "dci1" / "evidence" / "dci1-v3"
    before = {p: p.stat().st_mtime_ns
              for p in evidence.rglob("*") if p.is_file()}
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(ROOT / "experiments" / "build_sets.py")],
        capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr
    after = {p: p.stat().st_mtime_ns
             for p in evidence.rglob("*") if p.is_file()}
    assert before == after


def test_set_builder_deterministic():
    cal_path = (ROOT / "experiments" / "human_review"
                / "calibration_sample.json")
    res_path = ROOT / "experiments" / "reserved_final_check_ids.json"
    before = (cal_path.read_bytes(), res_path.read_bytes())
    import subprocess
    subprocess.run([sys.executable,
                    str(ROOT / "experiments" / "build_sets.py")],
                   capture_output=True, cwd=str(ROOT), check=True)
    assert (cal_path.read_bytes(), res_path.read_bytes()) == before
