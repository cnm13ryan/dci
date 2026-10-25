"""The Lambda helper scripts (scripts/lambda): valid shell, and none of the
actions the run rules forbid on the instance."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu
DIR = Path(__file__).resolve().parents[2] / "scripts" / "lambda"
SCRIPTS = sorted(DIR.glob("*.sh"))
FORBIDDEN = (r"--torch-backend", r"download-kernels", r"\bapt(-get)?\b",
             r"\bshutdown\b", r"\bpoweroff\b", r"\breboot\b", r"--token\b",
             r"\bpip install\b", r"\buv pip\b", r"\buv lock\b")


def test_the_expected_scripts_exist_and_are_executable():
    names = {p.name for p in SCRIPTS}
    assert {"preflight.sh", "bootstrap.sh", "fetch_models.sh",
            "sync_back.sh", "gpu_monitor.sh", "gpu_peaks.sh"} <= names
    assert all(p.stat().st_mode & 0o111 for p in SCRIPTS)


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_scripts_parse_and_avoid_forbidden_actions(path):
    subprocess.run(["bash", "-n", str(path)], check=True)
    code = "\n".join(l for l in path.read_text().splitlines()
                     if not l.lstrip().startswith("#"))
    for pattern in FORBIDDEN:
        assert not re.search(pattern, code), (path.name, pattern)


def test_bootstrap_builds_only_from_the_locks():
    text = (DIR / "bootstrap.sh").read_text()
    code = [l for l in text.splitlines() if not l.lstrip().startswith("#")]
    assert sum("uv sync --frozen" in l for l in code) == 2
    assert not any("uv sync" in l and "--frozen" not in l for l in code)
    assert "UV_PYTHON_PREFERENCE=only-system" in text
    assert "2.9.1+cu129 12.9 True 0.15.1" in text


def test_gpu_peaks_reads_a_monitor_log(tmp_path):
    log = tmp_path / "gpu.csv"
    log.write_text(
        "timestamp, index, uuid, memory.used [MiB], memory.total [MiB], "
        "utilization.gpu [%], power.draw [W]\n"
        "2026/10/25 15:30:00.000, 0, GPU-a, 100, 81559, 0, 70\n"
        "2026/10/25 15:30:01.000, 0, GPU-a, 70000, 81559, 90, 500\n"
        "2026/10/25 15:30:01.000, 1, GPU-b, 65000, 81559, 80, 480\n"
        "2026/10/25 15:30:02.000, 0, GPU-a, 300, 81559, 0, 80\n")
    out = subprocess.run(["bash", str(DIR / "gpu_peaks.sh"), str(log)],
                         capture_output=True, text=True, check=True).stdout
    assert out.splitlines() == ["gpu 0 peak 70000 MiB of 81559 MiB",
                                "gpu 1 peak 65000 MiB of 81559 MiB"]


def test_the_cuda_backend_lock_pins_d12():
    import tomllib
    root = DIR.parents[1] / "environments" / "cuda-vllm"
    project = tomllib.loads((root / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == "==3.12.*"
    assert project["tool"]["uv"]["index"][0]["url"] == \
        "https://download.pytorch.org/whl/cu129"
    lock = {p["name"]: p for p in
            tomllib.loads((root / "uv.lock").read_text())["package"]}
    assert lock["torch"]["version"] == "2.9.1+cu129"
    assert lock["torch"]["source"]["registry"] == \
        "https://download.pytorch.org/whl/cu129"
    assert lock["vllm"]["version"] == "0.15.1"


@pytest.mark.skipif(not all(shutil.which(t) for t in ("sha256sum", "rsync")),
                    reason="needs sha256sum and rsync")
def test_sync_back_copies_and_verifies_and_catches_a_corrupt_copy(tmp_path):
    remote, local, bindir = tmp_path / "fs", tmp_path / "mac", tmp_path / "bin"
    (remote / "runs" / "S").mkdir(parents=True)
    (remote / "runs" / "S" / "rows.jsonl").write_text('{"a": 1}\n')
    (remote / "logs").mkdir()
    (remote / "logs" / "smoke.log").write_text("ok\n")
    bindir.mkdir()
    fake = bindir / "ssh"     # runs the "remote" side here, dropping options
    fake.write_text('#!/usr/bin/env bash\nwhile [[ "$1" == -* ]]; do '
                    '[[ "$1" == -o || "$1" == -i ]] && shift; shift; done\n'
                    'shift\nexec bash -c "$*"\n')
    fake.chmod(0o755)
    env = {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}"}
    cmd = ["bash", str(DIR / "sync_back.sh"), "u@h", str(remote), str(local),
           "runs", "logs"]
    out = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert (local / "runs" / "S" / "rows.jsonl").read_text() == '{"a": 1}\n'
    assert out.stdout.count("verified") == 2
    # a copy corrupted on the Mac after the transfer is caught on re-check
    (local / "runs" / "S" / "rows.jsonl").write_text('{"a": 2}\n')
    check = subprocess.run(["shasum", "-a", "256", "-c", "--quiet",
                            "MANIFEST.sha256"], cwd=local / "runs",
                           capture_output=True, text=True)
    assert check.returncode != 0
