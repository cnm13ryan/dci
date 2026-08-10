"""Startup failures obey the exit taxonomy like any other failure.

State reset and stage discovery used to run before the try block. stage_order()
imports the stage package, so a syntax error or a missing dependency in any
stage module escaped as an uncaught traceback: the orchestrator saw exit code 1
with no stop record, indistinguishable from the interpreter dying for an
unrelated reason, and with nothing on disk saying which phase failed.
"""
import json

import pytest

from dci.pipeline import runner

pytestmark = pytest.mark.cpu


def _stop_record(tmp_path):
    path = tmp_path / "stop.json"
    return json.loads(path.read_text()) if path.exists() else None


@pytest.fixture
def run_root(tmp_path, monkeypatch):
    """Point the stop record at a temporary run root."""
    from dci.pipeline import state
    monkeypatch.setattr(state, "RUN_ROOT", tmp_path, raising=False)
    return tmp_path


def test_a_stage_package_import_failure_is_a_classified_crash(monkeypatch, run_root):
    def explode():
        raise ImportError("No module named 'torch'")

    monkeypatch.setattr(runner, "stage_order", explode)
    monkeypatch.setattr(runner, "_purge", lambda: None)

    assert runner.run_pipeline() == runner.EXIT_CRASH
    record = _stop_record(run_root)
    assert record is not None, "an import failure must still leave a crash record"
    assert record["kind"] == "crash"
    assert record["stage"] == "startup"
    assert "No module named" in record["error"]


def test_a_state_reset_failure_is_also_inside_the_boundary(monkeypatch, run_root):
    monkeypatch.setattr(runner, "_purge",
                        lambda: (_ for _ in ()).throw(RuntimeError("reset failed")))
    assert runner.run_pipeline() == runner.EXIT_CRASH
    assert _stop_record(run_root)["kind"] == "crash"


def test_an_invariant_failure_during_startup_keeps_its_own_exit_code(monkeypatch,
                                                                    run_root):
    monkeypatch.setattr(runner, "_purge", lambda: None)
    monkeypatch.setattr(runner, "stage_order",
                        lambda: (_ for _ in ()).throw(AssertionError("bad ORDER")))
    assert runner.run_pipeline() == runner.EXIT_INVARIANT
    assert _stop_record(run_root)["kind"] == "invariant_failure"


def test_the_stage_label_is_startup_when_discovery_never_completed(monkeypatch,
                                                                  run_root):
    """_next() indexed an empty order list; the label must not be a stage name."""
    monkeypatch.setattr(runner, "_purge", lambda: None)
    monkeypatch.setattr(runner, "stage_order",
                        lambda: (_ for _ in ()).throw(ImportError("boom")))
    runner.run_pipeline()
    assert _stop_record(run_root)["stage"] == "startup"


def test_exception_classes_are_bound_at_module_import():
    """An except clause naming a locally imported class would raise NameError."""
    import dci.pipeline.runner as mod
    for name in ("StudyStop", "LineageViolation", "FrozenPlanMismatch",
                 "TaskBankInsufficient", "CacheIntegrityError",
                 "ShardConfigError"):
        assert hasattr(mod, name), name


def test_write_stop_tolerates_state_that_never_imported(tmp_path):
    runner._write_stop(None, {"kind": "crash"})          # must not raise
