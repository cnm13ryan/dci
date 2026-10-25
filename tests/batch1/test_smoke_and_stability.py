"""The bounded smoke test (audit F10) and the D14 topic-cluster stability
diagnostics (audit F6)."""
from __future__ import annotations

import random

import pytest

from dci.batch1 import compatibility as COMPAT
from dci.batch1 import calibration as CAL
from dci.batch1 import runner as RUN
from dci.batch1 import smoke as SMOKE
from dci.batch1 import stability as STAB
from dci.batch1 import synthetic as SY
from dci.batch1 import topics as TOP
from dci.batch1.design import TASK_ONLY
from dci.batch1.store import RunError
from tests.batch1.helpers import SMALL, make_root

pytestmark = pytest.mark.cpu


# ---------------------------------------------------------------- smoke

def test_the_smoke_plan_is_bounded_and_single_instruction():
    plan = SMOKE.smoke_plan()
    assert len(plan["rows"]) <= SMOKE.SMOKE_MAX_ROWS
    assert all(r["user_prompt"].count("\n1. ") <= 1 and "\n2. " not in
               r["user_prompt"] for r in plan["rows"])
    assert SMOKE.smoke_plan() == plan


def test_smoke_questions_are_outside_the_topic_bank():
    bank = {t.question for t in TOP.load_bank()}
    assert not set(SMOKE.SMOKE_QUESTIONS) & bank
    report = TOP.overlap_report([TOP.Topic(f"smoke-{i}", "x", q)
                                 for i, q in enumerate(SMOKE.SMOKE_QUESTIONS)])
    assert not report["exact_matches"]


def test_smoke_refuses_without_its_token_or_beyond_its_limit(tmp_path):
    plan = SMOKE.smoke_plan()
    with pytest.raises(RunError, match="smoke plan hash"):
        SMOKE.run_smoke(tmp_path, token=None, max_rows=SMOKE.SMOKE_MAX_ROWS,
                        generate=SY.synthetic_generate())
    with pytest.raises(RunError, match="hard limit"):
        SMOKE.run_smoke(tmp_path, token=plan["plan_hash"],
                        max_rows=SMOKE.SMOKE_MAX_ROWS + 1,
                        generate=SY.synthetic_generate())
    with pytest.raises(RunError, match="hard limit"):
        SMOKE.run_smoke(tmp_path, token=plan["plan_hash"], max_rows=10,
                        generate=SY.synthetic_generate())
    assert not (tmp_path / "RUN.json").exists()


def test_a_smoke_run_reports_health_and_never_compliance(tmp_path):
    plan = SMOKE.smoke_plan(("qwen3-4b",))
    report = SMOKE.run_smoke(tmp_path, token=plan["plan_hash"], max_rows=96,
                             models=("qwen3-4b",),
                             generate=SY.synthetic_generate(empty_rate=0.2))
    entry = report["models"]["qwen3-4b"]
    assert entry["rows"] == len(plan["rows"])
    assert set(entry["outcome_classes"]) <= {"VALID", "EMPTY"}
    assert "compliance" not in str(report).lower().replace(
        "no compliance is computed", "")
    assert (tmp_path / "smoke_report.json").exists()


def test_a_smoke_root_and_a_pilot_root_never_mix(tmp_path):
    plan = SMOKE.smoke_plan(("qwen3-4b",))
    SMOKE.run_smoke(tmp_path, token=plan["plan_hash"], max_rows=96,
                    models=("qwen3-4b",), generate=SY.synthetic_generate())
    ctx = make_root(tmp_path)
    with pytest.raises(RunError, match="another run"):
        RUN.execute(tmp_path, [], freeze1=ctx["freeze1"],
                    approvals=ctx["approvals"],
                    generate=SY.synthetic_generate())


# ------------------------------------------------------------ stability

def _scored(n_topics=6, models=("qwen3-4b",), frames=("F0",)):
    rows = []
    rng = random.Random(1)
    for stage in ("stage1",):
        for t in range(n_topics):
            for m in models:
                for f in frames:
                    for cond in ("A.however.4", "ew.indeed.4"):
                        ok = rng.random() < 0.5
                        rows.append({"row_id": f"{stage}{t}{m}{f}{cond}",
                                     "stage": stage, "topic_id": f"t{t}",
                                     "model": m, "frame": f, "condition": cond,
                                     "scores": {cond: [True, "PASS", ok, True,
                                                       0, ""]}})
    return rows


def test_topic_clusters_keep_responses_of_a_topic_together():
    cells, clusters = STAB.topic_clusters(_scored())
    assert len(clusters["stage1"]) == 6
    a = cells["explicit"]["qwen3-4b|F0|A.however.4"]
    assert set(a) == {("stage1", f"t{t}") for t in range(6)}
    t1 = STAB.resample(cells, clusters, random.Random(5), synthetic=True)
    t2 = STAB.resample(cells, clusters, random.Random(5), synthetic=True)
    assert t1.state() == t2.state()
    for key in ("qwen3-4b|F0|A.however.4", "qwen3-4b|F0|ew.indeed.4"):
        assert t1.explicit[key].n == 6          # same topics, both cells


def test_stability_diagnostics_are_deterministic_and_diagnostic_only():
    matrix = COMPAT.compatibility_matrix()
    tables = SY.tables_from_rates(SY.full_rates(), n=32)
    point = CAL.finalize(tables, SMALL, matrix)
    scored = []
    rng = random.Random(3)
    for key, count in tables.explicit.items():
        m, f, cond = key.split("|")
        for t in range(32):
            scored.append({"row_id": f"{key}{t}", "stage": "stage1",
                           "topic_id": f"t{t}", "model": m, "frame": f,
                           "condition": cond,
                           "scores": {cond: [True, "PASS", t < count.k, True,
                                             0, ""]}})
    for m in SMALL.models:
        for t in range(32):
            scored.append({"row_id": f"to{m}{t}", "stage": "stage1",
                           "topic_id": f"t{t}", "model": m, "frame": None,
                           "condition": TASK_ONLY,
                           "scores": {c: [True, "FAIL", False, True, 0, ""]
                                      for c in ("A.however.4",)}})
    a = STAB.diagnostics(scored, point, SMALL, matrix, synthetic=True,
                         replicates=4)
    b = STAB.diagnostics(scored, point, SMALL, matrix, synthetic=True,
                         replicates=4)
    assert a == b
    assert sum(a["selection"]["status"].values()) == 4
    for groups in a["membership"].values():
        for freqs in groups.values():
            assert all(0 <= f <= 1 for f in freqs.values())
    assert a["interpretation"].startswith("diagnostic only")
    assert point == CAL.finalize(tables, SMALL, matrix)     # untouched
