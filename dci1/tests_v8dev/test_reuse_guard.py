"""The reuse guard: a stored backend run is reused only if it was generated.

v7's ``_reusable_rows`` matches the design's generation identity and the
row-id set and asks nothing about whether the backend answered. On
2026-09-05 a retry of a Gate-2 candidate run (root ``dci1v8-pilot-r17``)
reused a rows file that a blocked engine had written with all 274,176 rows
unanswered and marked ``TECHNICAL_FAILURE``; the stage scored empty answers
and signed a record on them. ``reusable_rows_checked`` refuses such a run;
these tests pin both halves — it still reuses a generated run unchanged.
"""
from __future__ import annotations

import json

import pytest

from dci1v8dev.run.execute import GENERATED_OUTCOME, reusable_rows_checked

WANTED = [{"row_id": "row-1", "generation_identity": "id-1", "topic_id": "t1"},
          {"row_id": "row-2", "generation_identity": "id-2", "topic_id": "t2"}]


def _run(tmp_path, *, outcome=GENERATED_OUTCOME, blocked=None, answer="an answer"):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "design.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in WANTED))
    (run_dir / "rows.jsonl").write_text("".join(
        json.dumps({"row_id": r["row_id"], "outcome": outcome,
                    "final_answer": answer}, sort_keys=True) + "\n"
        for r in WANTED))
    if blocked is not None:
        (run_dir / "rows_engine.json").write_text(
            json.dumps({"blocked": blocked, "expected_rows": len(WANTED)}))
    return run_dir


def test_a_generated_run_is_reused(tmp_path):
    rows, report = reusable_rows_checked(_run(tmp_path, blocked=False), WANTED)
    assert rows is not None and len(rows) == 2
    assert report["reused"] and report["n_reused"] == 2


def test_a_run_without_a_sidecar_is_still_reused(tmp_path):
    rows, report = reusable_rows_checked(_run(tmp_path), WANTED)
    assert rows is not None and report["reused"]


def test_a_blocked_run_is_refused(tmp_path):
    rows, report = reusable_rows_checked(_run(tmp_path, blocked=True), WANTED)
    assert rows is None
    assert report["reason"] == "PREVIOUS_RUN_BLOCKED"
    assert report["n_reused"] == 0


def test_an_unreadable_sidecar_is_refused(tmp_path):
    run_dir = _run(tmp_path, blocked=False)
    (run_dir / "rows_engine.json").write_text("{not json")
    rows, report = reusable_rows_checked(run_dir, WANTED)
    assert rows is None and report["reason"] == "PREVIOUS_RUN_BLOCKED"


def test_ungenerated_rows_are_refused_even_without_a_sidecar(tmp_path):
    """r17's shape: identities match, rows carry no generation."""
    run_dir = _run(tmp_path, outcome="TECHNICAL_FAILURE", answer="")
    rows, report = reusable_rows_checked(run_dir, WANTED)
    assert rows is None
    assert report["reason"] == "PREVIOUS_RUN_HAS_UNGENERATED_ROWS"
    assert report["ungenerated_outcomes"] == {"TECHNICAL_FAILURE": 2}


def test_one_ungenerated_row_refuses_the_whole_run(tmp_path):
    run_dir = _run(tmp_path, blocked=False)
    rows = [json.loads(l) for l in
            (run_dir / "rows.jsonl").read_text().splitlines() if l.strip()]
    rows[1]["outcome"] = "TECHNICAL_FAILURE"
    (run_dir / "rows.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    reused, report = reusable_rows_checked(run_dir, WANTED)
    assert reused is None
    assert report["ungenerated_outcomes"] == {"TECHNICAL_FAILURE": 1}


def test_the_confirmatory_path_uses_the_guard():
    """The freeze path must not be able to meet r17's defect."""
    import inspect

    from dci1v8dev.confirm import execute as confirm_execute

    src = inspect.getsource(confirm_execute.generate_and_score)
    assert "reusable_rows_checked(" in src
    assert "_reusable_rows(run_dir" not in src
