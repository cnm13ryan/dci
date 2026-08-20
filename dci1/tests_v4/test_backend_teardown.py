"""The backend must leave no process behind, on every exit path.

Three orphaned ``vllm_backend`` parents were observed alive for twelve hours
after their driver shell died, reparented to systemd and still holding KFD
registrations. The device check for the next run then sees a card that looks
occupied. These tests pin the three exit paths that produced it.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest

from dci1v4.generation.backend import (_LIVE_BACKEND_PGIDS, _child_setup,
                                       _terminate_group)

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"),
                                reason="PDEATHSIG and killpg are Linux-only")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_gone(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.05)
    return False


def test_child_gets_its_own_process_group():
    """Without this, killpg would signal the driver's own group."""
    process = subprocess.Popen(["sleep", "30"], preexec_fn=_child_setup)
    try:
        assert os.getpgid(process.pid) == process.pid
        assert os.getpgid(process.pid) != os.getpgid(os.getpid())
    finally:
        _terminate_group(process.pid)
        process.wait(timeout=5)


def test_terminate_group_reaps_the_whole_tree():
    """The backend spawns engine workers; killing the parent is not enough."""
    process = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess, time; subprocess.Popen(['sleep', '30']); "
         "time.sleep(30)"],
        preexec_fn=_child_setup)
    time.sleep(1.0)
    group = subprocess.run(["pgrep", "-g", str(process.pid)],
                           capture_output=True, text=True)
    members = [int(p) for p in group.stdout.split()]
    assert len(members) >= 2, f"expected a parent and a worker, got {members}"

    _terminate_group(process.pid)
    process.wait(timeout=5)
    for pid in members:
        assert _wait_gone(pid), f"{pid} survived the group teardown"
    assert process.pid not in _LIVE_BACKEND_PGIDS


def test_child_dies_when_the_driver_is_hard_killed():
    """The orphaning case: SIGKILL runs no handler, so only PDEATHSIG saves us."""
    driver = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess, sys, time\n"
         f"sys.path.insert(0, {os.path.dirname(os.path.dirname(__file__)) + '/src'!r})\n"
         "from dci1v4.generation.backend import _child_setup\n"
         "p = subprocess.Popen(['sleep', '60'], preexec_fn=_child_setup)\n"
         "print(p.pid, flush=True)\n"
         "time.sleep(60)\n"],
        stdout=subprocess.PIPE, text=True)
    child = int(driver.stdout.readline().strip())
    time.sleep(0.5)
    assert _alive(child)

    os.kill(driver.pid, signal.SIGKILL)
    driver.wait(timeout=5)
    assert _wait_gone(child), (
        f"backend {child} survived a hard-killed driver — this is the defect "
        f"that orphaned three vllm_backend parents for twelve hours")
