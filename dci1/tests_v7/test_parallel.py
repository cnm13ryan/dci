"""The spawned pools change nothing a record carries (engine/parallel, 2026-08-29).

Two loops run in a pool: scoring a backend run's rows and building §13.11's
calibration table. The pool itself is tested from inside a threaded child
process, the shape that deadlocked the fork-based first version. Each is tested against its serial reference --- the same
units in the calling process --- for byte identity, and the calibration
table against a naive scan-everything implementation that never existed in
the tree, so that bucketing the rows is shown to be a change of arithmetic
order only. The chance column is tested for what §13.2 says it is.
"""
from __future__ import annotations

import json

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.engine import parallel
from dci1v7.protocol import constants as C
from dci1v7.run import gates_run
from dci1v7.run.execute import (
    cell_rates,
    fake_backend,
    generate_and_score,
    instance_rates,
    per_topic_compliance,
    prompt_cell,
)
from dci1v7.verifiers.constraints import Constraint
from tests_v7.test_row_indexing import MODEL, SLOT_MAP, TOPIC, _Cell

# ------------------------------------------------------------- pool_map

def _unit(item: int) -> tuple:
    return (item, parallel.shared()["base"] + item * item)


def _failing_unit(item: int) -> int:
    if item == 70:
        raise ProtocolError("unit 70 refuses")
    return item


def test_pool_map_is_the_serial_map_in_order():
    items = list(range(300))
    serial = parallel.pool_map(_unit, items, shared={"base": 7}, workers=1)
    pooled = parallel.pool_map(_unit, items, shared={"base": 7}, workers=3)
    assert pooled == serial == [(i, 7 + i * i) for i in range(300)]
    assert parallel.shared() == {}


def test_pool_map_propagates_a_unit_error_as_itself():
    with pytest.raises(ProtocolError, match="unit 70"):
        parallel.pool_map(_failing_unit, list(range(200)), workers=3)
    with pytest.raises(ProtocolError, match="unit 70"):
        parallel.pool_map(_failing_unit, list(range(200)), workers=1)


def _pool_inside_a_threaded_process(n: int) -> list:
    """What the execution-path audit's scenario workers are: a spawned
    process with another thread alive, calling into a pool."""
    import threading
    import time

    stop = threading.Event()

    def spin():
        while not stop.is_set():
            time.sleep(0.001)

    thread = threading.Thread(target=spin, daemon=True)
    thread.start()
    try:
        return parallel.pool_map(_unit, list(range(n)), shared={"base": 1},
                                 workers=3)
    finally:
        stop.set()


def test_a_pool_started_from_a_threaded_child_process_completes():
    """The 2026-08-29 deadlock: a fork-based pool inside a spawned process
    that had a helper thread hung for eight hours in the audit. Workers now
    come from a forkserver, so the caller's threads cannot reach them."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(1, mp_context=mp.get_context("spawn")) as pool:
        future = pool.submit(_pool_inside_a_threaded_process, 200)
        assert future.result(timeout=120) == [(i, 1 + i * i)
                                              for i in range(200)]


def test_the_pool_size_reads_the_environment(monkeypatch):
    monkeypatch.setenv("DCI1_V7_CPU_WORKERS", "1")
    assert parallel.cpu_workers() == 1
    monkeypatch.setenv("DCI1_V7_CPU_WORKERS", "5")
    assert parallel.cpu_workers() == 5
    monkeypatch.delenv("DCI1_V7_CPU_WORKERS")
    assert 1 <= parallel.cpu_workers() <= parallel.MAX_DEFAULT_WORKERS


# ------------------------------------------------- scoring in the pool

def _scored(tmp_path, workers: int, monkeypatch):
    """Enough rows for a pool (above MIN_ITEMS_FOR_A_POOL), through the
    documented seam, with the pool size the environment names."""
    monkeypatch.setenv("DCI1_V7_CPU_WORKERS", str(workers))
    cells = [_Cell("solo:B", "solo", ("B",), draws=40),
             _Cell("unconstrained", "unconstrained", (), draws=40)]
    prompts = [prompt_cell(c, TOPIC, slot_map=SLOT_MAP,
                           topic_split="prescreen") for c in cells]

    def responder(row):
        # Varies by row so that identical rows cannot mask a mis-ordering.
        return ("However however however. Short words hold here. " +
                "Plainly and briefly. " * (1 + int(row["row_id"][-1]) % 3))

    rows = generate_and_score(
        MODEL, prompts, stage=C.STAGE_GATE0, cap=256, device=0,
        run_dir=tmp_path / f"w{workers}", instances=tuple(SLOT_MAP.values()),
        slot_map=SLOT_MAP, study_id="dci1v7-synthetic",
        generate=fake_backend(responder))
    return rows, (tmp_path / f"w{workers}" / "scored.jsonl").read_bytes()


def test_scoring_in_the_pool_is_byte_identical_to_the_serial_loop(
        tmp_path, monkeypatch):
    serial_rows, serial_bytes = _scored(tmp_path, 1, monkeypatch)
    pooled_rows, pooled_bytes = _scored(tmp_path, 4, monkeypatch)
    assert len(serial_rows) >= parallel.MIN_ITEMS_FOR_A_POOL
    assert pooled_rows == serial_rows
    assert pooled_bytes == serial_bytes
    assert [r["row_id"] for r in pooled_rows] == \
        [r["row_id"] for r in serial_rows]


# ------------------------------------------ the calibration table

CANDIDATES = (Constraint("MK1", 1), Constraint("MK2", 2),
              Constraint("MK6", 3))
B_STAR = 9


def _score(kind, severity, passed, *, present, graded=None):
    return {"slot": "S0", "kind": kind, "severity": severity,
            "passed": passed,
            "graded": (1.0 if passed else 0.0) if graded is None else graded,
            "non_vacuous": True, "vacuous_pass": False, "position": 1,
            "present": present, "processing_failure": False}


def _row(cell_id, arm, topic, draw, split, scores, words=80):
    return {"cell_id": cell_id, "arm": arm, "topic_id": topic,
            "draw_index": draw, "topic_split": split, "scores": scores,
            "truncated": False, "word_count": words}


def _split(index):
    return C.CALIBRATION_A if index % 2 == 0 else C.CALIBRATION_B


def _candidate_rows(n_topics=12, draws=4):
    """Pass-1 candidate solo cells: each states one candidate and scores
    the others (and B at m*) absent."""
    rows = []
    for index in range(n_topics):
        topic = f"fixture-topic-{index:03d}"
        for candidate in CANDIDATES:
            for draw in range(draws):
                hit = ((index + draw) % 5) < (2 + candidate.severity)
                scores = [_score(candidate.kind, candidate.severity, hit,
                                 present=True, graded=0.25 * ((index + draw)
                                                              % 4))]
                for other in CANDIDATES:
                    if other is not candidate:
                        scores.append(_score(other.kind, other.severity,
                                             (index * draw) % 3 == 0,
                                             present=False))
                scores.append(_score("B", B_STAR, False, present=False))
                rows.append(_row(f"solo:{candidate.label}", "solo", topic,
                                 draw, _split(index), scores,
                                 words=60 + index + draw))
    return rows


def _grid_rows(n_topics=12, draws=4, *, chance_by_kind):
    """Grid runs: an unconstrained cell and B-solo cells per topic, every
    candidate scored absent with a known chance rate in the unconstrained
    cell and a different rate under B.

    The unconstrained verdict cycles through the four draws of every topic
    --- pass on the first ``4 * rate`` residues of ``(index + draw) % 4`` ---
    so each topic's mean is exactly ``rate`` and so is every split's; a rate
    in {0, 0.25, 0.5, 0.75, 1.0} is therefore reproduced to the bit. The
    B-solo cells pass every candidate on half the rows, a value a wrong
    denominator would pick up.
    """
    rows = []
    for index in range(n_topics):
        topic = f"fixture-topic-{index:03d}"
        for draw in range(draws):
            unc = [_score(c.kind, c.severity,
                          ((index + draw) % draws)
                          < round(draws * chance_by_kind[c.kind]),
                          present=False)
                   for c in CANDIDATES]
            rows.append(_row("unconstrained", "unconstrained", topic, draw,
                             _split(index), unc))
            b = [_score("B", B_STAR, True, present=True)]
            b += [_score(c.kind, c.severity, (index + draw) % 2 == 0,
                         present=False) for c in CANDIDATES]
            rows.append(_row(f"solo:B:{B_STAR}", "solo", topic, draw,
                             _split(index), b))
    return rows


def _naive_reference(candidates, *, solo_rows, chance_rows, b_solo_rows,
                     m_star, prescreen):
    """Scan every row for every candidate; chance from the unconstrained
    cells alone (§11.2, §13.2); kappa(R|B) from the per-candidate reference
    `_kappa_under_b`."""
    unconstrained = [r for r in chance_rows if r.get("arm") == "unconstrained"]
    out = {}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B, "pooled"):
        restrict = None if split == "pooled" else split
        entries = []
        for candidate in candidates:
            try:
                solo = cell_rates(solo_rows, kind=candidate.kind,
                                  severity=candidate.severity, present=True,
                                  split=restrict)
                cell_rates(solo_rows, kind=candidate.kind,
                           severity=candidate.severity, present=False,
                           split=restrict)
            except ProtocolError:
                continue
            chance = cell_rates(unconstrained, kind=candidate.kind,
                                severity=candidate.severity, present=False,
                                split=restrict, arm="unconstrained")
            kappa_b, n_t, n_d = gates_run._kappa_under_b(
                b_solo_rows, candidate, split=restrict)
            entry = {
                "kind": candidate.kind, "severity": candidate.severity,
                "split": split, "model_key": MODEL,
                "solo_compliance": solo["compliance"],
                "chance_compliance": chance["compliance"],
                "solo_vacuity": solo["vacuity"],
                "n_topics": solo["n_topics"], "n_draws": C.M_CAL,
                "median_words": solo["median_words"],
                "graded_mean": solo["graded_mean"],
                "per_topic_solo": list(per_topic_compliance(
                    solo_rows, kind=candidate.kind,
                    severity=candidate.severity, split=restrict))}
            screened = prescreen.get(candidate.label) or {}
            if screened.get("solo") is not None:
                entry["prescreen_solo_compliance"] = screened["solo"]
            if screened.get("chance") is not None:
                entry["prescreen_chance_compliance"] = screened["chance"]
            if kappa_b is not None:
                entry["kappa_under_b"] = kappa_b
                entry["kappa_under_b_source"] = {
                    "load": 1, "present": [f"B:{m_star}"],
                    "candidate": candidate.label, "model_key": MODEL,
                    "m_star": m_star, "split": split,
                    "n_topics": n_t, "n_draws": n_d}
            entries.append(entry)
        out[split] = entries
    return out


def test_the_calibration_table_matches_a_naive_scan(
        monkeypatch):
    chance_by_kind = {"MK1": 0.0, "MK2": 0.5, "MK6": 0.75}
    solo_rows = _candidate_rows()
    grid_rows = _grid_rows(chance_by_kind=chance_by_kind)
    b_solo = [r for r in grid_rows if r["cell_id"] == f"solo:B:{B_STAR}"]
    prescreen = {"MK1:1": {"solo": 0.5, "chance": 0.0},
                 "MK2:2": {"solo": 0.4, "chance": 0.1}}
    kwargs = {"m_star": B_STAR, "solo_rows": solo_rows,
              "chance_rows": grid_rows, "b_solo_rows": b_solo,
              "prescreen": prescreen}
    reference = _naive_reference(CANDIDATES, **kwargs)
    for workers in (1, 3):
        monkeypatch.setenv("DCI1_V7_CPU_WORKERS", str(workers))
        monkeypatch.setattr(parallel, "MIN_ITEMS_FOR_A_POOL", 2)
        table = gates_run._calibration_rows(MODEL, CANDIDATES, **kwargs)
        assert json.dumps(table, sort_keys=True) == \
            json.dumps(reference, sort_keys=True), workers
    # The chance column is §13.2's kappa_c: the unconstrained cells' rate,
    # exactly, on every split --- and not the B-solo cells' 0.5, which a
    # denominator over every absent verdict would have averaged in.
    for split, rows in table.items():
        assert {r["kind"]: r["chance_compliance"] for r in rows} == \
            chance_by_kind, split
    assert instance_rates is not None       # the old path is still imported


# ------------------------------------------- a stalled pool falls back

def _stalling_unit(item: int) -> int:
    """Blocks forever in a *worker* for one item (and ignores SIGTERM there,
    as the stuck workers of 2026-08-29 did); returns at once in the calling
    process, so the serial fallback can finish the same units."""
    import multiprocessing as mp
    import signal
    import time

    if item == 3 and mp.parent_process() is not None:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(600)
    return item * 2


def test_a_stalled_pool_is_torn_down_within_the_bound_and_the_units_rerun(
        monkeypatch):
    """2026-08-29: a stage's pool finished every unit and then hung for 75
    minutes in Pool.__exit__ on two workers that never exited. Now a pool
    that stops delivering results within the bound is terminated, workers
    still alive after the teardown bound are killed, and the units are
    rerun serially --- the same results, later, rather than never."""
    import time

    monkeypatch.setattr(parallel, "RESULT_TIMEOUT_SECONDS", 3.0)
    monkeypatch.setattr(parallel, "TEARDOWN_TIMEOUT_SECONDS", 2.0)
    started = time.monotonic()
    out = parallel.pool_map(_stalling_unit, list(range(80)), workers=2,
                            chunksize=1)
    assert out == [i * 2 for i in range(80)]
    assert time.monotonic() - started < 60
    with pytest.raises(parallel.PoolStalled):
        parallel._pooled(_stalling_unit, list(range(80)), {}, 2, 1)


# ---------------------------------- payloads larger than a pipe buffer

def _bulky_unit(item: int) -> bytes:
    return bytes([item % 251]) * 200_000            # 200 kB per result


def test_results_larger_than_a_pipe_buffer_do_not_deadlock():
    """A first dispatcher sent every chunk before reading any result; with
    chunks and results bigger than a pipe's buffer the parent and a worker
    blocked on each other's full pipe forever (rehearsal r5, Gate 2). One
    chunk in flight per worker, collected as it completes, cannot."""
    import time

    started = time.monotonic()
    out = parallel.pool_map(_bulky_unit, list(range(96)), workers=2,
                            chunksize=3)              # 600 kB per result message
    assert out == [_bulky_unit(i) for i in range(96)]
    assert time.monotonic() - started < 120
