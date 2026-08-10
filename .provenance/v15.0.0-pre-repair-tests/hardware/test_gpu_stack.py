"""Hardware-tier checks. Skipped wherever the corresponding stack is absent,
so CPU CI stays green while the workstation and Lambda runs get real checks."""
import os

import pytest

from dci.compat import TORCH_AVAILABLE

gpu = pytest.mark.skipif(not TORCH_AVAILABLE, reason="no torch installed")


@gpu
@pytest.mark.gpu
def test_accelerator_visible():
    import torch
    assert torch.cuda.is_available(), (
        "torch is installed but no accelerator is visible; on ROCm check "
        "render/video group membership, on Lambda check the driver")


@gpu
@pytest.mark.gpu
def test_expected_device_count():
    import torch
    expected = os.environ.get("DCI_EXPECT_DEVICES")
    if expected is None:
        pytest.skip("set DCI_EXPECT_DEVICES=2 on the workstation")
    assert torch.cuda.device_count() == int(expected)


@gpu
@pytest.mark.rocm
def test_rocm_identifies_as_hip():
    import torch
    if not getattr(torch.version, "hip", None):
        pytest.skip("not a ROCm build")
    assert torch.cuda.is_available()
    name = torch.cuda.get_device_properties(0).name.lower()
    assert "radeon" in name or "amd" in name or "gfx" in name


@gpu
@pytest.mark.cuda
def test_cuda_identifies_as_cuda():
    import torch
    if not getattr(torch.version, "cuda", None):
        pytest.skip("not a CUDA build")
    assert torch.cuda.is_available()


@gpu
@pytest.mark.gpu
def test_hardware_class_is_stable_and_device_specific():
    """The frozen class must be identical across calls on one machine and must
    change with the device inventory it hashes."""
    import torch
    from dci.provenance.hashes import sha
    props = torch.cuda.get_device_properties(0)
    fields = {"gpu_name": props.name,
              "compute_capability": f"{props.major}.{props.minor}",
              "cuda_runtime": getattr(torch.version, "cuda", None),
              "torch_cuda_build": torch.__version__,
              "attn_implementation": "sdpa",
              "device_count": torch.cuda.device_count()}
    assert sha(fields) == sha(dict(fields))
    assert sha({**fields, "gpu_name": "OTHER"}) != sha(fields)
