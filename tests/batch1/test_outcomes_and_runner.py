"""Outcome classification, scoring denominators, and the runner's handling
of empty, technical, blocked, crashed, duplicated and interrupted runs
(audit F1, F10). The stub backends write the rows the vLLM seam writes."""
from __future__ import annotations

import fcntl
import json
import sys

import pytest

from dci.batch1 import design as D
from dci.batch1 import evidence as EV
from dci.batch1 import outcomes as OUT
from dci.batch1 import runner as RUN
from dci.batch1 import scoring as S
from dci.batch1 import synthetic as SY
from dci.batch1 import verifiers as V
from dci.batch1.store import RunError, canonical, read_jsonl
from tests.batch1.helpers import SMALL, lines, make_root

pytestmark = pytest.mark.cpu


@pytest.fixture(scope="module")
def protocol(tmp_path_factory):
    base = make_root(tmp_path_factory.mktemp("protocol"))
    design = EV.expected_design(base["root"], base["freeze1"], D.STAGE1)
    return {**base, "design": design}


@pytest.fixture
def run(protocol, tmp_path):
    make_root(tmp_path, freeze1=protocol["freeze1"],
              approvals=protocol["approvals"])
    rows = [r for r in protocol["design"] if r["model"] == "qwen3-4b"][:40]
    return {"root": tmp_path, "freeze1": protocol["freeze1"],
            "approvals": protocol["approvals"], "rows": rows,
            "design": protocol["design"]}


def execute(run, generate, rows=None):
    return RUN.execute(run["root"], rows or run["rows"], freeze1=run["freeze1"],
                       approvals=run["approvals"], generate=generate)


def rows_file(run, name="rows.jsonl"):
    return run["root"] / "generation" / "stage1" / "qwen3-4b" / name


def seam_row(design, **fields):
    row = {**design, "seed_reasoning": design["scientific_seed"],
           "reasoning_emitted": False, "channel_valid": True,
           "outcome": "OK", "final_answer": "Text.", "raw_generation": "Text.",
           "finish_reason": "stop", "answer_truncated": False}
    row.update(fields)
    return row


# ------------------------------------------------------------ classification

@pytest.mark.parametrize("fields,kind", [
    ({}, OUT.VALID),
    ({"final_answer": "   ", "raw_generation": "   "}, OUT.EMPTY),
    ({"finish_reason": "length", "answer_truncated": True}, OUT.VALID),
    ({"outcome": "CHANNEL_INVALID", "final_answer": "", "raw_generation": " \n",
      "channel_valid": False}, OUT.EMPTY),
    ({"outcome": "CHANNEL_INVALID", "final_answer": "", "raw_generation": "",
      "finish_reason": "length"}, OUT.EMPTY),
    # CHANNEL_INVALID that the empty-answer rule cannot explain
    ({"outcome": "CHANNEL_INVALID", "final_answer": "",
      "raw_generation": "<think>half"}, OUT.TECHNICAL),
    ({"outcome": "CHANNEL_INVALID", "final_answer": "", "raw_generation": "",
      "reasoning_emitted": True}, OUT.TECHNICAL),
    ({"outcome": "CHANNEL_INVALID", "final_answer": "", "raw_generation": "",
      "finish_reason": ""}, OUT.TECHNICAL),
    ({"outcome": "CHANNEL_INVALID", "final_answer": ""}, OUT.TECHNICAL),
    ({"outcome": "CAPACITY_EXCEEDED", "final_answer": ""}, OUT.TECHNICAL),
    ({"outcome": "BACKEND_UNSUPPORTED"}, OUT.TECHNICAL),
    ({"outcome": "TECHNICAL_FAILURE"}, OUT.TECHNICAL),
    ({"outcome": "NOT_GENERATED"}, OUT.TECHNICAL),
    ({"outcome": "SOMETHING_NEW"}, OUT.TECHNICAL),
    ({"finish_reason": "abort"}, OUT.TECHNICAL),
    ({"final_answer": None}, OUT.TECHNICAL),
])
def test_outcome_classes(protocol, fields, kind):
    raw = seam_row(protocol["design"][0], **fields)
    if fields.get("outcome") == "CHANNEL_INVALID" and "raw_generation" not in fields:
        raw.pop("raw_generation")
    assert OUT.classify(raw).kind == kind


def _b_row(protocol):
    return next(r for r in protocol["design"] if r["condition"] == "B.max8")


def test_a_successful_empty_answer_is_in_the_denominator_and_fails(protocol):
    """Regression 1 (audit probe D): the seam's empty-answer row."""
    d = _b_row(protocol)
    raw = seam_row(d, outcome="CHANNEL_INVALID", final_answer="",
                   raw_generation="", channel_valid=False)
    scored = S.score_row(raw, d)
    assert scored["state"] == V.STATE_EMPTY and scored["outcome_class"] == OUT.EMPTY
    c = S.build_tables([scored], [d]).x(d["model"], d["frame"], "B.max8")
    assert (c.k, c.n, c.empty) == (0, 1, 1)
    assert c.literal_pass == 1 and c.empty_pass == 1 and c.vacuous_pass == 0


def test_a_whitespace_only_answer_is_a_behavioural_failure(protocol):
    """Regression 2."""
    d = _b_row(protocol)
    scored = S.score_row(seam_row(d, final_answer=" \n\t ",
                                  raw_generation=" \n\t "), d)
    c = S.build_tables([scored], [d]).x(d["model"], d["frame"], "B.max8")
    assert scored["state"] == V.STATE_EMPTY and (c.k, c.n) == (0, 1)


def test_a_technical_failure_is_never_scored(protocol):
    """Regression 3: a capacity failure is not evidence."""
    d = _b_row(protocol)
    with pytest.raises(S.ScoringError, match="not behavioural evidence"):
        S.score_row(seam_row(d, outcome="CAPACITY_EXCEEDED", final_answer=""), d)


def test_truncated_passes_are_not_counted_as_vacuous(protocol):
    d = _b_row(protocol)
    text = " ".join(["Calm rivers carry cold water past old mills."] * 5)
    scored = S.score_row(seam_row(d, final_answer=text, raw_generation=text,
                                  finish_reason="length", answer_truncated=True), d)
    c = S.build_tables([scored], [d]).x(d["model"], d["frame"], "B.max8")
    assert (c.k, c.n, c.truncated, c.literal_pass) == (0, 1, 1, 1)
    assert c.truncated_pass == 1 and c.vacuous_pass == 0


# --------------------------------------------------------------------- runner

def test_technical_rows_are_rejected_and_regenerated_on_resume(run):
    """Regression 5."""
    failing = {r["row_id"] for r in run["rows"][:5]}
    first = execute(run, SY.synthetic_generate(
        technical=lambda r: "TECHNICAL_FAILURE" if r["row_id"] in failing
        else None))
    assert (first["generated"], first["rejected"], first["open"]) == (35, 5, 5)
    assert not first["complete"]
    assert {r["row_id"] for r in lines(rows_file(run))} == \
        {r["row_id"] for r in run["rows"]} - failing
    rejected = lines(rows_file(run, "rejected.jsonl"))
    assert {r["row_id"] for r in rejected} == failing
    assert all(r["attempt"] == 1 and r["reason"].startswith("TECHNICAL")
               for r in rejected)
    second = execute(run, SY.synthetic_generate())
    assert (second["generated"], second["reused"], second["open"]) == (5, 35, 0)
    assert second["complete"] and len(lines(rows_file(run))) == 40


def test_a_valid_empty_answer_is_not_regenerated(run):
    """Regression 6."""
    first = execute(run, SY.synthetic_generate(empty_rate=1.0))
    assert first["generated"] == 40 and first["complete"]
    assert all(r["outcome"] == "CHANNEL_INVALID" for r in lines(rows_file(run)))
    again = execute(run, SY.synthetic_generate())
    assert again["generated"] == 0 and again["reused"] == 40


def test_a_blocked_engine_fails_safely_and_accepts_nothing(run):
    """Regression 4: exit code 2, as the seam's blocked engine exits."""
    with pytest.raises(RunError, match="blocked"):
        execute(run, SY.synthetic_generate(blocked=True, returncode=2))
    assert not rows_file(run).exists() or lines(rows_file(run)) == []
    assert len(lines(rows_file(run, "rejected.jsonl"))) == 40
    resumed = execute(run, SY.synthetic_generate())
    assert resumed["generated"] == 40 and resumed["complete"]


def test_a_blocked_sidecar_with_exit_zero_is_still_blocked(run):
    with pytest.raises(RunError, match="blocked"):
        execute(run, SY.synthetic_generate(blocked=True, returncode=0))


def test_a_crash_keeps_completed_rows_and_resume_finishes(run):
    good = SY.synthetic_generate()

    def crash(run_dir, plan, rows):
        out = good(run_dir, plan, rows[:17])
        return {**out, "returncode": RUN.CRASH_EXIT}
    with pytest.raises(RunError, match="exited 3"):
        execute(run, crash)
    assert len(lines(rows_file(run))) == 17
    assert {r["reason"] for r in lines(rows_file(run, "rejected.jsonl"))} == \
        {"NOT_RETURNED"}
    assert execute(run, good)["generated"] == 23


def test_interrupted_and_resumed_equals_uninterrupted(run, protocol, tmp_path_factory):
    """Regression 8."""
    good = SY.synthetic_generate(empty_rate=0.1, truncation_rate=0.1)
    other = tmp_path_factory.mktemp("uninterrupted")
    make_root(other, freeze1=run["freeze1"], approvals=run["approvals"])
    RUN.execute(other, run["rows"], freeze1=run["freeze1"],
                approvals=run["approvals"], generate=good)

    def interrupted(run_dir, plan, rows):
        return {**good(run_dir, plan, rows[:11]), "returncode": RUN.CRASH_EXIT}
    with pytest.raises(RunError):
        execute(run, interrupted)
    with rows_file(run).open("a") as fh:          # a write cut mid-record
        fh.write('{"row_id": "b1-trunc')
    execute(run, good)
    a = sorted(canonical(r) for r in lines(rows_file(run)))
    b = sorted(canonical(r) for r in
               lines(other / "generation" / "stage1" / "qwen3-4b" / "rows.jsonl"))
    assert a == b
    events = lines(rows_file(run, "provenance.jsonl"))
    assert any(e["event"] == "repaired_partial_line" for e in events)


def test_duplicates_collapse_and_conflicts_refuse(run):
    """Regression 7."""
    execute(run, SY.synthetic_generate())
    path = rows_file(run)
    stored = lines(path)
    path.write_text(path.read_text() + json.dumps(stored[0], sort_keys=True) + "\n")
    again = execute(run, SY.synthetic_generate())
    assert again["generated"] == 0 and again["repeats_collapsed"] == 1
    design = {r["row_id"]: r for r in run["design"]}
    scored = S.score_rows(read_jsonl(path), design.values())
    assert len(scored) == 40
    tables = S.build_tables(scored, design.values())
    assert sum(c.n for c in tables.explicit.values()) + \
        sum(c.n for k, c in tables.task_only.items() if k.endswith("|A.however.2")) \
        == 40
    with pytest.raises(S.ScoringError, match="scored twice"):
        S.build_tables(scored + scored[:1], design.values())
    conflict = dict(stored[1], final_answer="Something else.")
    path.write_text(path.read_text() + json.dumps(conflict) + "\n")
    with pytest.raises(RunError, match="two different records"):
        execute(run, SY.synthetic_generate())


def test_a_non_evidence_row_in_the_rows_file_is_refused(run):
    """What the old runner wrote: a blocked row stored as if generated."""
    d = run["rows"][0]
    rows_file(run).parent.mkdir(parents=True)
    rows_file(run).write_text(json.dumps(seam_row(
        d, outcome="CAPACITY_EXCEEDED", final_answer="")) + "\n")
    with pytest.raises(RunError, match="non-evidence row"):
        execute(run, SY.synthetic_generate())


def test_a_second_process_on_the_root_is_refused(run):
    run["root"].mkdir(exist_ok=True)
    with (run["root"] / "RUN.lock").open("a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RunError, match="in use by another process"):
            execute(run, SY.synthetic_generate())


# ------------------------------------------- the seam itself, as a subprocess

STUB = r'''
import argparse, json, sys
p = argparse.ArgumentParser()
for a in ("--plan", "--design", "--out", "--chunk-size"):
    p.add_argument(a)
a = p.parse_args()
mode = open(__file__.replace("__main__.py", "MODE")).read().strip()
rows = [json.loads(l) for l in open(a.design)]
with open(a.out, "w") as out:
    for i, r in enumerate(rows):
        ident = {k: v for k, v in r.items()
                 if k not in ("user_prompt", "system_message", "scientific_seed",
                              "answer_seed")}
        if mode == "blocked":
            rec = {**ident, "outcome": "CAPACITY_EXCEEDED", "final_answer": "",
                   "raw_generation": "", "finish_reason": "",
                   "seed_reasoning": r["scientific_seed"]}
        else:
            text = "" if i == 0 else "Calm rivers carry cold water past old mills."
            rec = {**ident, "outcome": "CHANNEL_INVALID" if i == 0 else "OK",
                   "final_answer": text, "raw_generation": text,
                   "reasoning_emitted": False, "finish_reason": "stop",
                   "answer_truncated": False,
                   "seed_reasoning": r["scientific_seed"]}
        out.write(json.dumps(rec) + "\n")
        if mode == "crash" and i == 2:
            out.write('{"row_id": "cut')
            out.flush()
            sys.exit(3)
blocked = mode == "blocked"
json.dump({"blocked": blocked, "outcome": "CAPACITY_EXCEEDED" if blocked else "",
           "load_seconds": 1.0, "generation_seconds": 2.0},
          open(a.out[:-6] + "_engine.json", "w"))
raise SystemExit(2 if blocked else 0)
'''


@pytest.fixture
def stub(tmp_path_factory):
    root = tmp_path_factory.mktemp("stub")
    (root / "vllm_backend").mkdir()
    (root / "vllm_backend" / "__init__.py").write_text("")
    (root / "vllm_backend" / "__main__.py").write_text(STUB)

    def backend(mode):
        (root / "vllm_backend" / "MODE").write_text(mode)
        return RUN.subprocess_backend(RUN.BackendSpec(python=sys.executable,
                                                      cwd=str(root)))
    return backend


def test_the_audits_blocked_engine_probe_through_the_real_adapter(run, stub):
    """Audit probe E: 40 blocked rows, exit 2. Before: '40 generated', then
    '0 generated, 40 reused'. Now: refused, nothing accepted, resumable."""
    with pytest.raises(RunError, match="blocked"):
        execute(run, stub("blocked"))
    assert not rows_file(run).exists() or lines(rows_file(run)) == []
    assert len(lines(rows_file(run, "rejected.jsonl"))) == 40
    done = execute(run, stub("ok"))
    assert done["generated"] == 40 and done["complete"]
    stored = lines(rows_file(run))
    assert sum(OUT.classify(r).kind == OUT.EMPTY for r in stored) == 1


def test_a_crashed_subprocess_keeps_its_complete_rows(run, stub):
    with pytest.raises(RunError, match="exited 3"):
        execute(run, stub("crash"))
    assert len(lines(rows_file(run))) == 3
    assert execute(run, stub("ok"))["generated"] == 37


# ------------------------------------- one worker per GPU (D12, 2026-10-25)

def _per_model(protocol, n=12):
    out = []
    for model in sorted({r["model"] for r in protocol["design"]}):
        out += [r for r in protocol["design"] if r["model"] == model][:n]
    return out


def test_two_workers_use_both_devices_and_match_one_worker(protocol,
                                                           tmp_path_factory):
    import threading
    import time as _time
    rows = _per_model(protocol)
    good = SY.synthetic_generate(empty_rate=0.1, truncation_rate=0.1)
    active, peak, lock = [0], [0], threading.Lock()

    def slow(run_dir, plan, design_rows):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        _time.sleep(0.3)
        try:
            return good(run_dir, plan, design_rows)
        finally:
            with lock:
                active[0] -= 1
    roots = {}
    for name, devices in (("two", (0, 1)), ("one", None)):
        root = tmp_path_factory.mktemp(name)
        make_root(root, freeze1=protocol["freeze1"],
                  approvals=protocol["approvals"])
        summary = RUN.execute(root, rows, freeze1=protocol["freeze1"],
                              approvals=protocol["approvals"],
                              generate=slow, devices=devices)
        assert summary["complete"] and summary["generated"] == len(rows)
        roots[name] = root
    assert peak[0] == 2
    models = sorted({r["model"] for r in rows})
    used = set()
    for model in models:
        group = roots["two"] / "generation" / "stage1" / model
        used |= {e["device"] for e in lines(group / "provenance.jsonl")
                 if e["event"] == "backend_run"}
        a = sorted(canonical(r) for r in lines(group / "rows.jsonl"))
        b = sorted(canonical(r) for r in lines(
            roots["one"] / "generation" / "stage1" / model / "rows.jsonl"))
        assert a == b
    assert used == {0, 1}


def test_a_device_listed_twice_is_refused(run):
    with pytest.raises(RunError, match="listed twice"):
        RUN.execute(run["root"], run["rows"], freeze1=run["freeze1"],
                    approvals=run["approvals"],
                    generate=SY.synthetic_generate(), devices=(0, 0))


def test_each_worker_sees_only_its_own_gpu():
    spec = RUN.BackendSpec(visibility_var="CUDA_VISIBLE_DEVICES", device=0)
    from dataclasses import replace
    envs = [replace(spec, device=d).env() for d in (0, 1)]
    assert [e["CUDA_VISIBLE_DEVICES"] for e in envs] == ["0", "1"]
    assert all("HIP_VISIBLE_DEVICES" not in e for e in envs)


# ------------------------------------------- third audit, C5 and C6 hardening

def test_inherited_vllm_settings_never_reach_the_seam(monkeypatch):
    monkeypatch.setenv("VLLM_BATCH_INVARIANT", "1")
    monkeypatch.setenv("VLLM_ATTENTION_BACKEND", "XFORMERS")
    env = RUN.BackendSpec(visibility_var="CUDA_VISIBLE_DEVICES").env()
    assert not {"VLLM_BATCH_INVARIANT", "VLLM_ATTENTION_BACKEND"} & set(env)
    assert env["VLLM_WORKER_MULTIPROC_METHOD"] == "spawn"


def test_a_cuda_backend_with_rocm_visibility_is_refused():
    from tests.batch1.helpers import fake_probe
    with pytest.raises(RunError, match="--accelerator cuda"):
        RUN.check_visibility(fake_probe(), RUN.BackendSpec())
    RUN.check_visibility(fake_probe(), RUN.BackendSpec(
        visibility_var="CUDA_VISIBLE_DEVICES"))


def test_an_attempt_directory_without_its_event_is_not_reused(run):
    group = rows_file(run).parent
    (group / "attempts" / "001").mkdir(parents=True)
    (group / "attempts" / "001" / "backend.log").write_text("killed\n")
    execute(run, SY.synthetic_generate())
    assert (group / "attempts" / "001" / "backend.log").read_text() == "killed\n"
    events = [e for e in lines(rows_file(run, "provenance.jsonl"))
              if e["event"] == "backend_run"]
    assert [e["attempt"] for e in events] == [2]
