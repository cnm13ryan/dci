"""A basename-only --state-file must not lose a launched instance.

os.makedirs(os.path.dirname("instance.json")) is os.makedirs(""), which raises
FileNotFoundError. That mattered more than an ordinary argument-handling slip: it
fired AFTER the billable launch request succeeded, so an instance was running and
the only record of its id had just been thrown away.
"""
import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.cpu


@pytest.fixture(scope="module")
def cloud():
    spec = importlib.util.spec_from_file_location(
        "lambda_cloud", Path("scripts/lambda_cloud.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PAYLOAD = {"request": {"instance_type_name": "gpu_1x_h100"},
           "response": {"data": {"instance_ids": ["0920..."]}}}


def test_a_basename_only_path_is_written(cloud, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cloud._write_state("instance.json", PAYLOAD)
    assert json.loads((tmp_path / "instance.json").read_text()) == PAYLOAD


def test_a_nested_path_creates_its_directories(cloud, tmp_path):
    target = tmp_path / "runs" / "2026" / "instance.json"
    cloud._write_state(str(target), PAYLOAD)
    assert json.loads(target.read_text()) == PAYLOAD


def test_a_dot_relative_path_is_written(cloud, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cloud._write_state("./instance.json", PAYLOAD)
    assert (tmp_path / "instance.json").exists()


def test_an_existing_directory_is_reused(cloud, tmp_path):
    (tmp_path / "runs").mkdir()
    cloud._write_state(str(tmp_path / "runs" / "a.json"), PAYLOAD)
    cloud._write_state(str(tmp_path / "runs" / "b.json"), PAYLOAD)
    assert {p.name for p in (tmp_path / "runs").iterdir()} == {"a.json", "b.json"}


def test_the_write_leaves_no_partial_file(cloud, tmp_path):
    target = tmp_path / "instance.json"
    cloud._write_state(str(target), PAYLOAD)
    assert [p.name for p in tmp_path.iterdir()] == ["instance.json"]


def test_a_failure_still_prints_the_instance_record(cloud, tmp_path, capsys):
    """A bookkeeping failure must never be the only trace of a live instance."""
    blocked = tmp_path / "file-not-a-dir"
    blocked.write_text("x")
    with pytest.raises(OSError):
        cloud._write_state(str(blocked / "state.json"), PAYLOAD)
    printed = capsys.readouterr().out
    assert "could not write state file" in printed
    assert "instance_ids" in printed


def test_the_standalone_doctor_delegates_to_the_package():
    """No second implementation to drift out of step with `dci doctor`."""
    text = Path("scripts/local_doctor.py").read_text()
    assert "from dci.diagnostics import main" in text
    assert len(text.splitlines()) < 25, "the logic belongs in the package"
