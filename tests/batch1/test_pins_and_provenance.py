"""D12's interpreter pins and the portable code hash (re-audit R2), and the
re-audit's R4 safeguards: per-attempt backend logs, the retry limit, the
seam row schema, non-focal smoke instructions and the near-threshold flag.
Provenance binding in Freeze 2 is tested in ``test_end_to_end``."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from dci.batch1 import cli
from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import environment as ENV
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import library as L
from dci.batch1 import outcomes as OUT
from dci.batch1 import runner as RUN
from dci.batch1 import smoke as SMOKE
from dci.batch1 import store
from dci.batch1 import synthetic as SY
from tests.batch1.helpers import SMALL, fake_probe, lines, make_root
from tests.batch1.test_outcomes_and_runner import (  # noqa: F401 (fixtures)
    execute, protocol, rows_file, run, stub,
)

pytestmark = pytest.mark.cpu
REPO = Path(__file__).resolve().parents[2]


# ------------------------------------------------------- the portable hash

def _hash(text: str, tmp_path: Path) -> str:
    path = tmp_path / "m.py"
    path.write_text(text)
    return store.code_hash(path)


BASE = textwrap.dedent('''\
    """Module docstring."""
    import os


    def f(x, y):
        """Doc."""
        # a comment
        name = f"{x}-{y!r:>4}"
        return os.path.join(name, "z")
    ''')


def test_documentation_and_layout_edits_keep_the_hash(tmp_path):
    h = _hash(BASE, tmp_path)
    edited = (BASE.replace('"""Module docstring."""', '"""Another, longer\n'
                           'module docstring."""')
              .replace('"""Doc."""', '"""Rewritten doc."""')
              .replace("# a comment", "# a different comment\n\n")
              .replace("def f(x, y):", "def f(x,\n      y):  # wrapped"))
    assert _hash(edited, tmp_path) == h


@pytest.mark.parametrize("old,new", [
    ('return os.path.join(name, "z")', 'return os.path.join(name, "y")'),
    ("{y!r:>4}", "{y!r:>5}"),
    ("name = ", "label = "),
    ("import os", "import os.path"),
])
def test_code_and_string_edits_change_the_hash(tmp_path, old, new):
    assert _hash(BASE.replace(old, new), tmp_path) != _hash(BASE, tmp_path)


def _other_interpreters() -> list[str]:
    base = Path.home() / ".local/share/uv/python"
    found = []
    for minor in ("3.12", "3.13"):
        hits = sorted(base.glob(f"cpython-{minor}.*/bin/python{minor}"))
        if hits:
            found.append(str(hits[-1]))
    return found


HASH_SCRIPT = r'''
import importlib.util, json, sys, pathlib
repo = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("s", repo / "src/dci/batch1/store.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
paths = json.loads(sys.argv[2])
print(json.dumps({p: m.code_hash(repo / p) for p in paths}))
'''


@pytest.mark.skipif(not _other_interpreters(),
                    reason="no other CPython minor version installed")
def test_every_frozen_source_hashes_the_same_under_3_12_and_3_13():
    """Re-audit R2: the ast.dump hash differed under 3.11, 3.12 and 3.13."""
    sources = {**{f"src/dci/batch1/{n}": n for n in F.RULE_MODULES},
               **{f"src/{n}": n for n in F.EXTERNAL_RULE_MODULES}}
    seam = sorted(p.relative_to(REPO).as_posix()
                  for p in ENV.BACKEND_DIR.rglob("*.py")
                  if "__pycache__" not in p.parts)
    paths = sorted(sources) + seam
    here = {p: store.code_hash(REPO / p) for p in paths}
    for python in _other_interpreters():
        out = subprocess.run([python, "-I", "-c", HASH_SCRIPT, str(REPO),
                              json.dumps(paths)], capture_output=True,
                             text=True, check=True).stdout
        assert json.loads(out) == here, python


# ----------------------------------------------------- the interpreter pins

def test_the_project_pins_python_3_11():
    assert (REPO / ".python-version").read_text().strip() == \
        CFG.ORCHESTRATOR_PYTHON == "3.11"
    assert ENV.require_orchestrator()["minor"] == "3.11"


def test_every_payload_and_the_approvals_record_the_orchestrator_python():
    for d in CFG.decisions():
        assert d.payload["orchestrator_python"] == "3.11"
    d12 = next(d for d in CFG.decisions() if d.decision_id == "D12")
    assert d12.payload["backend_python"] == CFG.BACKEND_PYTHON == "3.12"
    assert d12.payload["source_hash_scheme"] == store.SOURCE_HASH_SCHEME
    template = F.approvals_template()
    assert template["orchestrator_python"] == "3.11"


@pytest.fixture
def python_312(monkeypatch):
    monkeypatch.setattr(ENV, "_interpreter",
                        lambda: ("3.12.9", "cpython", "/usr/bin/python3.12"))


def test_another_minor_version_is_refused_with_its_reason(python_312, capsys):
    with pytest.raises(ENV.PythonMismatch, match=r"CPython 3\.11.*3\.12\.9"):
        ENV.require_orchestrator()
    with pytest.raises(ENV.PythonMismatch, match="3.12.9"):
        F.freeze1_manifest(SMALL)
    assert cli.main(["validate-library"]) == 3
    assert "refused: Batch 1 protocol commands run under CPython 3.11" in \
        capsys.readouterr().err


def test_validation_names_the_interpreter_not_a_hash(tmp_path, monkeypatch):
    manifest = F.freeze1_manifest(SMALL)
    assert manifest["orchestrator"]["frozen_with"]["minor"] == "3.11"
    assert F.validate_freeze1(manifest, F.approvals_template(SMALL)) == []
    monkeypatch.setattr(ENV, "_interpreter",
                        lambda: ("3.13.7", "cpython", "/opt/py"))
    problems = F.validate_freeze1(manifest, F.approvals_template(SMALL))
    assert len(problems) == 1 and "3.13.7" in problems[0]


def test_a_patch_release_of_3_11_validates(monkeypatch):
    manifest = F.freeze1_manifest(SMALL)
    monkeypatch.setattr(ENV, "_interpreter",
                        lambda: ("3.11.4", "cpython", "/opt/py"))
    assert F.validate_freeze1(manifest, F.approvals_template(SMALL)) == []


def test_approvals_written_for_another_python_block():
    approvals = F.approvals_template(SMALL)
    approvals["orchestrator_python"] = "3.12"
    manifest = F.freeze1_manifest(SMALL, approvals)
    assert any("orchestrator_python '3.12'" in b
               for b in manifest["authorization"]["blocking"])


def test_a_backend_on_another_python_cannot_be_locked_or_frozen():
    with pytest.raises(ValueError, match="D12 records 3.12"):
        ENV.lock_from_probe(fake_probe(python="3.11.9"))
    lock = ENV.lock_from_probe(fake_probe())
    lock["identity"]["python"] = "3.11.9"
    lock["identity_hash"] = store.record_hash(lock["identity"])
    manifest = F.freeze1_manifest(SMALL, environment_lock=lock)
    assert any("backend is Python 3.11.9" in b
               for b in manifest["authorization"]["blocking"])


# ----------------------------------------------------------- R4 safeguards

def test_seam_row_keys_match_the_seam_contract():
    path = ENV.BACKEND_DIR / "contract.py"
    spec = importlib.util.spec_from_file_location("seam_contract", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["seam_contract"] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop("seam_contract", None)
    assert OUT.SEAM_ROW_KEYS == module.ROW_KEYS


def test_each_attempt_keeps_its_own_backend_log(run, stub):
    with pytest.raises(RUN.RunError, match="exited 3"):
        execute(run, stub("crash"))
    execute(run, stub("ok"))
    group = rows_file(run).parent
    logs = sorted(p.relative_to(group).as_posix()
                  for p in group.glob("attempts/*/backend.log"))
    assert logs == ["attempts/001/backend.log", "attempts/002/backend.log"]
    events = [e for e in lines(group / "provenance.jsonl")
              if e["event"] == "backend_run"]
    assert [e["attempt_dir"] for e in events] == ["attempts/001",
                                                  "attempts/002"]
    assert {e["generator"] for e in events} == {RUN.SYNTHETIC_GENERATOR}


def test_a_row_that_always_fails_stops_after_the_limit(run):
    stuck = run["rows"][0]["row_id"]
    gen = SY.synthetic_generate(
        technical=lambda r: "CAPACITY_EXCEEDED" if r["row_id"] == stuck else None)
    sent = []

    def counting(run_dir, plan, rows):
        sent.append(len(rows))
        return gen(run_dir, plan, rows)
    for _ in range(SMALL.max_technical_attempts):
        summary = execute(run, counting)
        assert not summary["complete"]
    assert summary["exhausted"] == [] and sent[-1] == 1
    final = execute(run, counting)
    assert final["exhausted"] == [stuck] and not final["complete"]
    assert len(sent) == SMALL.max_technical_attempts      # not sent again
    assert "not retried" in final["note"]
    summary = EV.rejected_summary(run["root"], D.STAGE1,
                                  max_technical_attempts=3)
    assert summary["exhausted_row_ids"] == [stuck]


def test_a_real_run_refuses_a_row_without_the_seam_schema(run, monkeypatch):
    row = run["rows"][0]
    expected = {row["row_id"]: row}
    gen = SY.synthetic_generate()
    with pytest.raises(RUN.RunError, match="seam schema"):
        RUN._run_group(run["root"], D.STAGE1, row["model"], [row], gen,
                       expected, generator=RUN.SEAM_GENERATOR,
                       environment_identity_hash="e" * 64,
                       max_technical_attempts=3)


def test_the_smoke_test_never_prompts_a_focal_instruction():
    by_id = L.constraint_by_id()
    plan = SMOKE.smoke_plan()
    conditions = {r["condition"] for r in plan["rows"]}
    assert all(c == D.TASK_ONLY or by_id[c].role == "reference"
               for c in conditions)
    assert len(plan["rows"]) <= SMOKE.SMOKE_MAX_ROWS


def test_near_threshold_flag():
    def result(counts):
        return {"status": "FEASIBLE", "feasibility": {
            p: {"supported_configurations": n} for p, n in zip(("P1", "P2", "P3"),
                                                              counts)}}
    assert F.near_threshold(result((16, 16, 14)), CFG.DEFAULT_CONFIG)
    assert not F.near_threshold(result((16, 16, 15)), CFG.DEFAULT_CONFIG)
    assert not F.near_threshold({"status": "INFEASIBLE_REVISION_REQUIRED",
                                 "feasibility": None}, CFG.DEFAULT_CONFIG)
