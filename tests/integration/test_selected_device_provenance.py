"""Hardware identity, capability and provenance must describe the SELECTED GPU.

`CFG.single_gpu_index` (set by --device) decides model placement, but every
hardware question was asked of device 0. On a heterogeneous host that means two
runs on two different GPUs record the same hardware class, so the resume guard
whose entire purpose is to refuse a dataset generated half on one device and half
on another sees no boundary to refuse - and the bfloat16 capability check
certifies a device that is not the one that will execute.
"""
from pathlib import Path
import types

import pytest

pytestmark = [pytest.mark.cpu, pytest.mark.slow]

STAGE = "dci.pipeline.stages.c122_runtime_provenance_gates"
SOURCE = Path("src/dci/pipeline/stages/c122_runtime_provenance_gates.py")


@pytest.fixture(scope="module")
def stage_module():
    """Run far enough to import c122, then hand back the live module."""
    import sys
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    import tempfile
    cfg = loader.load_profile(Path("configs/profiles/dev_fast.toml"))
    cfg.data_root = tempfile.mkdtemp()
    cfg.use_google_drive = False
    loader.activate(cfg)
    assert run_pipeline(until="c122") == 0
    return sys.modules[STAGE]


def test_no_hardware_question_is_asked_of_device_zero():
    text = SOURCE.read_text()
    assert "get_device_properties(0)" not in text
    # The three hardware questions - diagnostic report, hardware class, dtype
    # capability gate - each resolve the device through the accessor.
    assert text.count("scientific_device_index()") >= 3
    assert "get_device_properties(index)" in text        # class, via the accessor


def test_the_hardware_class_records_which_device_executed(stage_module):
    from dci.pipeline import state as S
    assert "device_index" in S.HARDWARE_CLASS
    # No CUDA on this host, so the recorded index is None and the class is the
    # declared cpu_or_dry_run literal rather than a hash of absent hardware.
    assert S.HARDWARE_CLASS["device_index"] is None
    assert S.HARDWARE_CLASS["class"] == "cpu_or_dry_run"


def test_the_accessor_returns_the_configured_index(stage_module):
    from dci.pipeline import state as S
    assert stage_module.scientific_device_index() == S.CFG.single_gpu_index


def _fake_cuda(monkeypatch, stage_module, visible: int):
    torch = stage_module.torch
    # On a host without torch these live on the compat stub, so the attribute
    # may not exist yet; raising=False lets the fake stand in either way.
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True, raising=False)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: visible, raising=False)


def test_a_nonzero_selected_index_is_used_for_inspection(monkeypatch,
                                                        stage_module):
    """The hardware-independent proof: a fake multi-GPU host, --device 1."""
    from dci.pipeline import state as S
    asked = []
    torch = stage_module.torch
    _fake_cuda(monkeypatch, stage_module, visible=2)
    monkeypatch.setattr(torch.cuda, "get_device_properties",
                        lambda index: asked.append(index) or types.SimpleNamespace(
                            name=f"FakeGPU{index}", major=9, minor=0,
                            total_memory=80 * 2**30), raising=False)
    monkeypatch.setattr(S.CFG, "single_gpu_index", 1, raising=False)

    assert stage_module.scientific_device_index() == 1
    fields = stage_module.hardware_class()
    assert asked == [1], "hardware_class inspected the wrong device"
    assert fields["gpu_name"] == "FakeGPU1"
    assert fields["device_index"] == 1
    assert fields["device_count"] == 2


def test_two_devices_on_one_host_get_different_hardware_classes(monkeypatch,
                                                               stage_module):
    """The boundary the resume guard must be able to see."""
    from dci.pipeline import state as S
    torch = stage_module.torch
    _fake_cuda(monkeypatch, stage_module, visible=2)
    monkeypatch.setattr(torch.cuda, "get_device_properties",
                        lambda index: types.SimpleNamespace(
                            name=f"FakeGPU{index}", major=9, minor=0,
                            total_memory=80 * 2**30), raising=False)
    monkeypatch.setattr(S.CFG, "single_gpu_index", 0, raising=False)
    zero = stage_module.hardware_class()
    monkeypatch.setattr(S.CFG, "single_gpu_index", 1, raising=False)
    one = stage_module.hardware_class()
    assert zero["class"] != one["class"]


def test_selecting_an_absent_device_refuses_rather_than_falling_back(monkeypatch,
                                                                    stage_module):
    from dci.pipeline import state as S
    _fake_cuda(monkeypatch, stage_module, visible=1)
    monkeypatch.setattr(S.CFG, "single_gpu_index", 3, raising=False)
    with pytest.raises(EnvironmentError, match="only 1 CUDA device"):
        stage_module.scientific_device_index()
