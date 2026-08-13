"""The subprocess seam: how an experiment driver invokes the canonical backend.

Generation runs in a SECOND interpreter — the vLLM/ROCm one — while planning and
analysis run in the scientific one. The only thing crossing that boundary is a
command line and two files, so the command line is the contract, and it is the
narrowest stable seam between the consolidated backend and its consumers.

Before consolidation each driver pointed at `crossmodel/vllm_tp2.py`, which
carried its own engine. That file became a 33-line shim whose whole remaining
job was to put `exploratory/` on `sys.path` and call `vllm_backend.__main__`.
This module pins the seam so the shim can be removed without the drivers
silently losing their entry point.

The path constraint is real and is why the shim existed: `python -m vllm_backend`
resolves the package from `sys.path[0]`, which under `-m` is the working
directory. A driver must therefore run it with `cwd` set to `exploratory/`. That
is asserted here rather than left as folklore.

Nothing here loads weights. The contract being tested is argument handling and
invocability, which is exactly the part a driver depends on and the part that
breaks silently when an entry point moves.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.cpu

#: The canonical invocation. Drivers must produce exactly this prefix.
CANONICAL_COMMAND = ("-m", "vllm_backend")

#: Required by the backend; a driver omitting any of them cannot generate.
REQUIRED_FLAGS = ("--plan", "--design", "--out")

#: Optional, and each one changes execution, so a rename is a silent break.
OPTIONAL_FLAGS = ("--chunk-size", "--deadline-seconds", "--strategy",
                  "--no-verify-switch")

#: Every driver that shells out to the backend.
DRIVERS = ("xm_vllm_smoke.py", "xm_vllm_run.py")


def _run(args, cwd=EXPLORATORY):
    """Invoke the backend module in a subprocess, as a driver does."""
    env = {**os.environ, "PYTHONPATH": str(EXPLORATORY)}
    return subprocess.run([sys.executable, *CANONICAL_COMMAND, *args],
                          cwd=str(cwd), capture_output=True, text=True,
                          timeout=120, env=env)


class TestTheModuleIsInvocable:
    def test_it_runs_as_a_module_from_the_exploratory_directory(self) -> None:
        done = _run(["--help"])
        assert done.returncode == 0, done.stderr[-1500:]
        assert "vllm_backend" in done.stdout

    def test_the_package_resolves_without_a_shim_inserting_the_path(self) -> None:
        """What the deleted shim used to do, done by cwd instead."""
        done = subprocess.run(
            [sys.executable, *CANONICAL_COMMAND, "--help"],
            cwd=str(EXPLORATORY), capture_output=True, text=True, timeout=120,
            env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
        assert done.returncode == 0, (
            "`-m vllm_backend` must work with cwd=exploratory and no "
            f"PYTHONPATH; drivers rely on it.\n{done.stderr[-1500:]}")


class TestTheArgumentContract:
    @pytest.mark.parametrize("flag", REQUIRED_FLAGS + OPTIONAL_FLAGS)
    def test_each_documented_flag_is_accepted(self, flag) -> None:
        assert flag in _run(["--help"]).stdout

    @pytest.mark.parametrize("omitted", REQUIRED_FLAGS)
    def test_omitting_a_required_flag_refuses_rather_than_defaulting(
            self, omitted, tmp_path) -> None:
        """A defaulted --out would write generations somewhere unrecorded."""
        supplied = [a for flag in REQUIRED_FLAGS if flag != omitted
                    for a in (flag, str(tmp_path / flag.strip("-")))]
        done = _run(supplied)
        assert done.returncode != 0
        assert omitted in done.stderr

    def test_an_unknown_flag_is_refused_not_ignored(self, tmp_path) -> None:
        """Silently ignoring it would run a different condition than requested."""
        done = _run(["--plan", str(tmp_path / "p"), "--design",
                     str(tmp_path / "d"), "--out", str(tmp_path / "o"),
                     "--reasoning-budget", "256"])
        assert done.returncode != 0
        assert "unrecognized" in done.stderr or "unrecognised" in done.stderr


class TestEveryDriverUsesTheCanonicalEntryPoint:
    """Parsed from source: a driver pointing at a removed path fails only on a
    GPU box, hours into a run, after the plan has already been written."""

    @staticmethod
    def _backend_target(driver: str) -> list[str]:
        tree = ast.parse((EXPLORATORY / driver).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", "") == "BACKEND_COMMAND"
                            for t in node.targets)):
                continue
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant)]
        raise AssertionError(f"{driver} defines no BACKEND_COMMAND")

    @pytest.mark.parametrize("driver", DRIVERS)
    def test_it_invokes_the_module_not_a_script_path(self, driver) -> None:
        assert tuple(self._backend_target(driver)) == CANONICAL_COMMAND

    @pytest.mark.parametrize("driver", DRIVERS)
    def test_it_names_no_removed_backend_script(self, driver) -> None:
        source = (EXPLORATORY / driver).read_text(encoding="utf-8")
        assert "BACKEND_SCRIPT" not in source
        # The historical name may appear as a run_kind label or in prose; what
        # may not appear is a constructed path to the deleted file.
        assert 'crossmodel" / "vllm_tp2.py"' not in source

    @pytest.mark.parametrize("driver", DRIVERS)
    def test_it_runs_the_backend_with_exploratory_as_the_directory(
            self, driver) -> None:
        """`-m` resolves from the working directory; getting this wrong is a
        ModuleNotFoundError only on the machine that can actually generate."""
        source = (EXPLORATORY / driver).read_text(encoding="utf-8")
        assert "cwd=" in source, (
            f"{driver} must pass cwd to the backend subprocess")


class TestPathsCrossingTheSeamAreAbsolute:
    """Setting `cwd` on the subprocess made relative paths mean two things.

    Both drivers default their output directory to a RELATIVE `runs/...`. The
    backend now runs with cwd=exploratory so `-m vllm_backend` resolves, so an
    unresolved path is written by the driver relative to $PWD and read by the
    backend relative to exploratory/. `xm_vllm_run` then counts rows in the
    driver's $PWD, finds none, prints "GENERATION FAILED (0 rows)" and returns 3
    after a successful multi-hour generation.

    This is the accidental behaviour change the cwd fix introduced, and it is
    invisible whenever the driver happens to be started from `exploratory/`.
    """

    @pytest.mark.parametrize("driver", DRIVERS)
    def test_the_output_directory_is_resolved(self, driver) -> None:
        tree = ast.parse((EXPLORATORY / driver).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", "") == "out_dir"
                            for t in node.targets)):
                continue
            assert (isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "attr", "") == "resolve"), (
                f"{driver} builds out_dir without .resolve(); with cwd set on "
                "the backend subprocess a relative path names two directories")
            return
        raise AssertionError(f"{driver} assigns no out_dir")

    @pytest.mark.parametrize("driver", DRIVERS)
    def test_a_relative_default_is_what_makes_this_necessary(self,
                                                             driver) -> None:
        """If the default ever becomes absolute this test says why it mattered."""
        source = (EXPLORATORY / driver).read_text(encoding="utf-8")
        assert '"runs/xmv' in source


class TestTheOrphanDetectorStillCoversTheOldForm:
    """Deliberately NOT cleaned up with the shim.

    `runlock` matches command lines to find processes still holding VRAM. A
    process launched before this migration carries the old path on its command
    line and can outlive it — the incident that motivated runlock had one
    survive fourteen hours. A detector that forgets a form strands the card, so
    the old pattern is retained on purpose and this test says so.
    """

    def test_both_the_old_path_and_the_module_are_matched(self) -> None:
        sys.path.insert(0, str(EXPLORATORY))
        from crossmodel import runlock
        assert "crossmodel/vllm_tp2.py" in runlock.RUNNER_PATTERNS
        assert "vllm_backend" in runlock.RUNNER_PATTERNS
