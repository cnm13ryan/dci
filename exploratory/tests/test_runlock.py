"""Regression tests for the execution safeguards.

Every test here corresponds to something that actually went wrong in the run
that motivated `crossmodel.runlock`: two runs sharing the GPUs, a rerun
appending to a finished directory, an orphan surviving cleanup, and a corrupt
output file whose row count looked plausible.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import runlock


@pytest.fixture()
def lock_paths(tmp_path):
    return tmp_path / "gpu.lock", tmp_path / "run_a", tmp_path / "run_b"


def make_lock(gpu_lock, out_dir, **kwargs):
    return runlock.RunLock(out_dir, "test/model", "0" * 40,
                           gpu_lock_path=gpu_lock, reap_orphans=False,
                           **kwargs)


# ------------------------------------------------------- mutual exclusion
def test_second_run_is_refused_while_the_first_holds_the_gpu_lock(lock_paths):
    """The failure that produced a 6-row file with 4 distinct row ids."""
    gpu_lock, run_a, run_b = lock_paths
    with make_lock(gpu_lock, run_a):
        with pytest.raises(runlock.RunLockError, match="GPU lock is held"):
            with make_lock(gpu_lock, run_b):
                pytest.fail("a second run must not acquire the GPU lock")


def test_the_gpu_lock_is_released_for_the_next_run(lock_paths):
    gpu_lock, run_a, run_b = lock_paths
    with make_lock(gpu_lock, run_a):
        pass
    with make_lock(gpu_lock, run_b) as second:
        assert second.manifest_path.exists()


def test_the_lock_is_released_when_the_body_raises(lock_paths):
    gpu_lock, run_a, run_b = lock_paths
    with pytest.raises(ValueError):
        with make_lock(gpu_lock, run_a):
            raise ValueError("boom")
    # The next run must be able to start; a crashed run that holds the lock
    # forever is as bad as one that shares it.
    with make_lock(gpu_lock, run_b):
        pass
    manifest = json.loads((run_a / "run_lock_manifest.json").read_text())
    assert manifest["state"] == "failed"


def _child_tries_to_acquire(gpu_lock_path, out_dir, result):
    """Module level, not a closure: `spawn` (the macOS default start method)
    pickles the target, and a locally defined function cannot be pickled. As a
    closure this test failed on every non-fork platform for a reason that had
    nothing to do with the lock it tests."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from crossmodel import runlock as child_runlock

    try:
        with child_runlock.RunLock(out_dir, "test/model", "0" * 40,
                                   gpu_lock_path=Path(gpu_lock_path),
                                   reap_orphans=False):
            result.value = 0                # acquired — wrong
    except child_runlock.RunLockError:
        result.value = 1                    # refused — right


def test_the_lock_excludes_across_processes(lock_paths):
    """flock is held by the OS, so exclusion must survive a real second process."""
    gpu_lock, run_a, run_b = lock_paths

    with make_lock(gpu_lock, run_a):
        result = multiprocessing.Value("i", -1)
        process = multiprocessing.Process(
            target=_child_tries_to_acquire, args=(str(gpu_lock), run_b, result))
        process.start()
        process.join(60)
        assert result.value == 1, "a separate process acquired a held GPU lock"


# --------------------------------------------------------- output protection
def test_existing_output_is_not_overwritten(lock_paths):
    gpu_lock, run_a, _ = lock_paths
    run_a.mkdir(parents=True)
    (run_a / "generations.jsonl").write_text('{"row_id": "x"}\n')
    with pytest.raises(runlock.RunLockError, match="already contains"):
        with make_lock(gpu_lock, run_a):
            pytest.fail("must refuse to write over an existing result")


def test_a_partial_file_also_blocks_a_fresh_run(lock_paths):
    gpu_lock, run_a, _ = lock_paths
    run_a.mkdir(parents=True)
    (run_a / "partial_generations.jsonl").write_text('{"row_id": "x"}\n')
    with pytest.raises(runlock.RunLockError, match="already contains"):
        with make_lock(gpu_lock, run_a):
            pytest.fail("a partial file is still someone's output")


def test_resume_is_possible_but_must_be_explicit(lock_paths):
    gpu_lock, run_a, _ = lock_paths
    run_a.mkdir(parents=True)
    (run_a / "generations.jsonl").write_text('{"row_id": "x"}\n')
    with make_lock(gpu_lock, run_a, allow_resume=True) as lock:
        assert lock.manifest_path.exists()


# ------------------------------------------------------------ the manifest
def test_manifest_records_owner_and_is_written_atomically(lock_paths):
    gpu_lock, run_a, _ = lock_paths
    with make_lock(gpu_lock, run_a) as lock:
        manifest = json.loads(lock.manifest_path.read_text())
        assert manifest["pid"] == os.getpid()
        assert manifest["model_id"] == "test/model"
        assert manifest["model_revision"] == "0" * 40
        assert manifest["state"] == "running"
        assert not lock.manifest_path.with_suffix(".json.tmp").exists()
    assert json.loads((run_a / "run_lock_manifest.json").read_text())[
        "state"] == "finished"


# ----------------------------------------------------- dataset integrity
def test_duplicate_row_ids_are_rejected():
    """The corrupt file had 6 rows and 4 distinct ids, and nothing noticed."""
    rows = [{"row_id": "a"}, {"row_id": "b"}, {"row_id": "a"}]
    with pytest.raises(AssertionError, match="duplicated row_id"):
        runlock.assert_unique_rows(rows)


def test_row_count_mismatch_is_rejected():
    rows = [{"row_id": "a"}, {"row_id": "b"}]
    with pytest.raises(AssertionError, match="expected 160"):
        runlock.assert_unique_rows(rows, expected=160)


def test_missing_row_id_is_rejected():
    with pytest.raises(AssertionError, match="carry no row_id"):
        runlock.assert_unique_rows([{"row_id": "a"}, {}])


def test_a_clean_dataset_passes():
    rows = [{"row_id": f"r{i}"} for i in range(160)]
    assert runlock.assert_unique_rows(rows, expected=160)["duplicates"] == 0


# ------------------------------------------------------------ orphan scan
def test_runner_patterns_cover_the_backend_script_not_only_vllm_children():
    """The orphan that survived fourteen hours was named `python`, not VLLM::."""
    assert "crossmodel/vllm_tp2.py" in runlock.RUNNER_PATTERNS
    assert "VLLM::" in runlock.RUNNER_PATTERNS
    assert "xm_run.py" in runlock.RUNNER_PATTERNS


def test_running_runners_does_not_report_this_process():
    assert all(record["pid"] != os.getpid()
               for record in runlock.running_runners())


def test_audit_machine_reports_the_fields_a_capacity_claim_needs():
    audit = runlock.audit_machine()
    for field in ("free_vram_gib", "runner_processes", "shm_segments"):
        assert field in audit


def test_host_memory_is_absent_rather_than_wrong_off_linux():
    """`host_memory_gib` reads /proc/meminfo and returns {} where there is none.

    Asserted on every platform so the degradation stays deliberate: a capacity
    claim built on a silently invented number is the failure mode this whole
    module exists to prevent.
    """
    memory = runlock.host_memory_gib()
    assert isinstance(memory, dict)
    if sys.platform != "linux":
        assert memory == {}


@pytest.mark.linux
def test_host_memory_is_reported_on_the_workstation():
    """The run hosts are Linux; there the reading must actually be present."""
    memory = runlock.host_memory_gib()
    assert "MemAvailable" in memory and memory["MemAvailable"] > 0
