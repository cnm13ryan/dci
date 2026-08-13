"""The reaper may only ever signal this checkout's own processes.

`RUNNER_PATTERNS` is fed to `pgrep -af`, which searches every process on the
machine. Two of the patterns are unavoidably broad: `VLLM::` matches any
project's vLLM workers, and `vllm_backend` matches any checkout of this one. So
a pattern match is evidence that a process MIGHT be ours, never that it is —
and the module's most destructive operation, `kill_runners`, takes pids.

This has already had a visible effect: `test_runlock.py` failed on this host
whenever an unrelated repository was generating, because a foreign `VLLM::`
worker was read as a live runner of ours. That was the harmless direction of the
error. The harmful direction is the same mistake reaching `kill_runners`.

The property pinned here: ownership must be ESTABLISHED, and anything that
cannot be established reads as foreign. A run that waits for a card is a cost;
killing a colleague's twelve-hour job is not recoverable.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crossmodel import runlock  # noqa: E402


def _sleeper(cwd: Path, run_id: str | None = None) -> subprocess.Popen:
    """A live process whose command line matches a runner pattern.

    The command line genuinely contains `vllm_backend`, so `pgrep -af` finds it;
    only its working directory and run id say whether it is ours.

    The marker is stripped from the child's environment unless a test asks for
    one. Without that, a `RunLock` entered earlier in the same pytest session
    would have stamped this interpreter, every child would inherit the stamp,
    and a deliberately foreign process would be claimed as ours — which is
    exactly how these tests first failed.
    """
    environment = {k: v for k, v in os.environ.items() if k != runlock.RUN_ID_VAR}
    if run_id is not None:
        environment[runlock.RUN_ID_VAR] = run_id
    process = subprocess.Popen(
        [sys.executable, "-c",
         "import time; vllm_backend = 1; time.sleep(30)"],
        cwd=str(cwd), env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.3)                       # let it appear in the process table
    return process


class TestOwnership:
    def test_this_process_is_ours(self) -> None:
        assert runlock.owned_by_this_checkout(os.getpid()) is True

    def test_a_process_outside_the_checkout_is_not_ours(self, tmp_path) -> None:
        """The load-bearing case: same command line, different repository."""
        process = _sleeper(tmp_path)
        try:
            assert runlock.owned_by_this_checkout(process.pid) is False
        finally:
            process.kill(); process.wait()

    def test_a_process_inside_the_checkout_is_ours(self) -> None:
        process = _sleeper(runlock.REPO_ROOT)
        try:
            assert runlock.owned_by_this_checkout(process.pid) is True
        finally:
            process.kill(); process.wait()

    def test_a_subdirectory_of_the_checkout_counts(self) -> None:
        """vLLM workers inherit cwd, which is usually `exploratory/`."""
        process = _sleeper(Path(__file__).resolve().parents[1])
        try:
            assert runlock.owned_by_this_checkout(process.pid) is True
        finally:
            process.kill(); process.wait()

    def test_a_dead_pid_is_not_ours(self) -> None:
        """Unestablishable ownership reads as foreign, never as ours."""
        process = _sleeper(runlock.REPO_ROOT)
        process.kill(); process.wait()
        assert runlock.owned_by_this_checkout(process.pid) is False

    def test_pid_one_is_not_ours(self) -> None:
        """A process this user cannot inspect must not be claimed."""
        assert runlock.owned_by_this_checkout(1) is False

    def test_the_run_id_marker_claims_a_process_that_moved(self) -> None:
        """cwd is not the only signal: a child that chdirs is still ours."""
        marker = "test-run-id-42"
        process = _sleeper(Path("/tmp"), run_id=marker)
        previous = os.environ.get(runlock.RUN_ID_VAR)
        os.environ[runlock.RUN_ID_VAR] = marker
        try:
            assert runlock.owned_by_this_checkout(process.pid) is True
        finally:
            if previous is None:
                os.environ.pop(runlock.RUN_ID_VAR, None)
            else:
                os.environ[runlock.RUN_ID_VAR] = previous
            process.kill(); process.wait()

    def test_a_different_run_id_does_not_claim_it(self) -> None:
        process = _sleeper(Path("/tmp"), run_id="some-other-checkouts-run")
        previous = os.environ.get(runlock.RUN_ID_VAR)
        os.environ[runlock.RUN_ID_VAR] = "ours-is-different"
        try:
            assert runlock.owned_by_this_checkout(process.pid) is False
        finally:
            if previous is None:
                os.environ.pop(runlock.RUN_ID_VAR, None)
            else:
                os.environ[runlock.RUN_ID_VAR] = previous
            process.kill(); process.wait()


class TestTheScanIsScoped:
    def test_a_foreign_matching_process_is_not_listed_as_a_runner(self, tmp_path) -> None:
        process = _sleeper(tmp_path)
        try:
            pids = {row["pid"] for row in runlock.running_runners()}
            assert process.pid not in pids
        finally:
            process.kill(); process.wait()

    def test_it_can_be_listed_explicitly_as_foreign(self, tmp_path) -> None:
        """Reporting a busy card is legitimate; signalling it is not."""
        process = _sleeper(tmp_path)
        try:
            pids = {row["pid"] for row in runlock.running_runners(foreign=True)}
            assert process.pid in pids
        finally:
            process.kill(); process.wait()


class TestKillRunnersRefusesForeignPids:
    def test_a_foreign_pid_is_never_signalled(self, tmp_path) -> None:
        """The guarantee has to hold at the point of signalling, not upstream."""
        process = _sleeper(tmp_path)
        try:
            signalled = runlock.kill_runners([process.pid], grace=0.1)
            assert signalled == []
            assert process.poll() is None, (
                "an unrelated vLLM-matching process was killed")
        finally:
            process.kill(); process.wait()

    def test_our_own_matching_process_is_signalled(self) -> None:
        """The scoping must not disarm the reaper for real orphans."""
        process = _sleeper(runlock.REPO_ROOT)
        try:
            assert runlock.kill_runners([process.pid], grace=0.1) == [process.pid]
            process.wait(timeout=10)
            assert process.poll() is not None
        finally:
            if process.poll() is None:
                process.kill(); process.wait()

    def test_a_mixed_list_signals_only_ours(self, tmp_path) -> None:
        ours, theirs = _sleeper(runlock.REPO_ROOT), _sleeper(tmp_path)
        try:
            signalled = runlock.kill_runners([ours.pid, theirs.pid], grace=0.1)
            assert signalled == [ours.pid]
            assert theirs.poll() is None
        finally:
            for process in (ours, theirs):
                if process.poll() is None:
                    process.kill()
                process.wait()

    @pytest.mark.parametrize("pid", [1, 0])
    def test_it_never_signals_an_uninspectable_pid(self, pid: int) -> None:
        assert runlock.kill_runners([pid], grace=0.1) == []
