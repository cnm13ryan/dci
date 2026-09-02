"""Finding 12 of the 2026-09-02 pre-freeze audit, pinned.

1. The operating-point stability bootstrap is reproducible across processes:
   its seed comes from the repository's domain-separated derivation, never
   from Python's per-process-salted builtin ``hash()``.
2. A stage of either v8 lifecycle (pilot or confirm) is addressed to HEAD of
   a clean worktree; a dirty worktree, or an operator-supplied commit that
   is not HEAD, fails closed outside a synthetic namespace.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import pathlib
import subprocess
import sys

import pytest

from dci1v4.errors import IntegrityError
from dci1v8dev.confirm import lifecycle as CL
from dci1v8dev.confirm import membership, stability
from dci1v8dev.run import lifecycle as PL
from dci1v8dev.run import seeds

DCI1 = pathlib.Path(__file__).resolve().parents[1]


# ------------------------------------------------- 1. deterministic bootstrap
_SCRIPT = r"""
import json, sys
from dci1v7.protocol import constants as C
from dci1v8dev.confirm.stability import operating_point_stability
from dci1v8dev.run import seeds
solo = {q: {f"t{i}": ((i * (q + 3)) % 7) / 6.0 for i in range(40)} for q in C.TARGET_GRID}
chance = {q: {f"t{i}": 0.05 for i in range(40)} for q in C.TARGET_GRID}
seed = seeds.bootstrap_seed("operating_point_stability:frame1", "model-x")
out = operating_point_stability(solo, chance, grid=list(C.TARGET_GRID),
                                band=C.TARGET_BAND, aim=C.TARGET_AIM,
                                selected=int(sys.argv[1]), resamples=300, seed=seed)
print(json.dumps(out, sort_keys=True))
"""


def _run_isolated(hash_seed: str, selected: int) -> str:
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    proc = subprocess.run([sys.executable, "-c", _SCRIPT, str(selected)],
                          capture_output=True, text=True, env=env, check=True,
                          cwd=str(DCI1))
    return proc.stdout.strip()


def test_stability_bootstrap_is_byte_identical_across_processes():
    a = _run_isolated("1", 5)
    b = _run_isolated("424242", 5)
    assert a == b
    out = json.loads(a)
    assert out["resamples"] == 300 and out["distribution"]
    assert out["status"] in ("OPERATING_POINT_STABLE", "OPERATING_POINT_UNSTABLE")
    assert 0.0 <= out["p_selected_reproduced"] <= 1.0
    # a different frozen point is a different record, same distribution
    c = json.loads(_run_isolated("7", 6))
    assert c["distribution"] == out["distribution"]
    assert c["selected"] == 6 and out["selected"] == 5


def test_no_builtin_hash_seeds_any_confirm_or_stability_path():
    """The builtin is salted per process (PYTHONHASHSEED); nothing in the
    confirm package may seed a resample with it."""
    root = DCI1 / "src" / "dci1v8dev"
    offenders = []
    for path in sorted((root / "confirm").glob("*.py")) + [root / "run" / "seeds.py"]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "hash"):
                offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, offenders
    src = inspect.getsource(membership.membership_payload)
    assert "seeds.bootstrap_seed(" in src
    assert seeds.bootstrap_seed("operating_point_stability:frame0", "m") == \
        seeds.bootstrap_seed("operating_point_stability:frame0", "m")
    assert seeds.bootstrap_seed("operating_point_stability:frame0", "m") != \
        seeds.bootstrap_seed("operating_point_stability:frame1", "m")


def test_status_threshold_is_two_thirds_and_the_frozen_point_is_kept():
    from dci1v7.protocol import constants as C
    from dci1v8dev import rules as R
    assert R.OPERATING_POINT_MIN_RECOVERY == pytest.approx(2.0 / 3.0)
    # a curve whose selected rung sits exactly on the band edge is unstable
    solo = {q: {f"t{i}": (0.0 if (i % 2) else 1.0) for i in range(30)}
            for q in C.TARGET_GRID}
    out = stability.operating_point_stability(
        solo, None, grid=list(C.TARGET_GRID), band=C.TARGET_BAND,
        aim=C.TARGET_AIM, selected=int(C.TARGET_GRID[0]), resamples=200, seed=3)
    assert out["selected"] == int(C.TARGET_GRID[0])       # never replaced
    assert out["status"] in ("OPERATING_POINT_STABLE", "OPERATING_POINT_UNSTABLE")
    assert (out["status"] == "OPERATING_POINT_UNSTABLE") == \
        (out["p_selected_reproduced"] < R.OPERATING_POINT_MIN_RECOVERY)
    if out["runner_up"] is not None:
        assert out["runner_up"] != out["selected"]


# ------------------------------------------------------ 2. clean worktree
def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "a.txt").write_text("a\n")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "one"], check=True)
    return repo


def _head(repo: pathlib.Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_a_clean_worktree_is_addressed_to_head(tmp_path):
    repo = _repo(tmp_path)
    out = PL.stage_provenance(repo, namespace="confirm", producing_commit=None)
    assert out == {"producing_commit": _head(repo), "worktree_clean": True,
                   "enforced": True, "repo_root": str(repo),
                   "operator_commit": None}
    # the operator may name HEAD, and nothing else
    assert PL.stage_provenance(repo, namespace="pilot",
                               producing_commit=_head(repo))["worktree_clean"]
    with pytest.raises(IntegrityError, match="not HEAD"):
        PL.stage_provenance(repo, namespace="pilot", producing_commit="0" * 40)


def test_a_dirty_worktree_cannot_produce_a_real_record(tmp_path):
    repo = _repo(tmp_path)
    (repo / "untracked.txt").write_text("x\n")
    with pytest.raises(IntegrityError, match="dirty"):
        PL.stage_provenance(repo, namespace="confirm", producing_commit=None)
    with pytest.raises(IntegrityError, match="dirty"):
        PL.stage_provenance(repo, namespace="pilot", producing_commit=None)
    (repo / "untracked.txt").unlink()
    (repo / "a.txt").write_text("changed\n")              # modified, tracked
    with pytest.raises(IntegrityError, match="dirty"):
        PL.stage_provenance(repo, namespace="confirm", producing_commit=None)
    # a synthetic namespace records the state and enforces nothing
    out = PL.stage_provenance(repo, namespace="confirm-synthetic",
                              producing_commit="0" * 40)
    assert out["worktree_clean"] is False and out["enforced"] is False
    assert out["producing_commit"] == _head(repo)          # still HEAD, not the operator's


def test_a_directory_that_is_not_a_repository_fails_closed(tmp_path):
    with pytest.raises(IntegrityError):
        PL.stage_provenance(tmp_path, namespace="confirm", producing_commit=None)


def test_both_lifecycles_call_the_gate_before_computing():
    for fn in (PL.run_stage, CL.run_stage):
        src = inspect.getsource(fn)
        assert "stage_provenance(" in src
        assert src.index("stage_provenance(") < src.index("compute(previous)")
        assert 'payload["provenance"] = provenance' in src
        assert 'payload["producing_commit"] = producing_commit' in src


def test_no_bypass_flag_exists():
    for module in (PL, CL):
        src = inspect.getsource(module)
        for token in ("allow_dirty", "ALLOW_DIRTY", "SKIP_CLEAN", "skip_clean",
                      "DCI1_ALLOW_DIRTY"):
            assert token not in src, (module.__name__, token)


def test_environment_record_names_the_backend_packages():
    env = PL.environment_record("op")
    assert env["operator_digest"] == "op"
    assert env["python"] and env["platform"]
    assert isinstance(env["backend_packages"], dict)
    if env["backend_venv"] is not None:
        assert any(k.lower().startswith("vllm") for k in env["backend_packages"]), \
            env["backend_packages"]
