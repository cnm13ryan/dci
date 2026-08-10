"""The no-evidence and optional-torch guarantees at the seam level."""
import pytest

from dci.compat import TORCH_AVAILABLE, require_torch, torch

pytestmark = pytest.mark.cpu


def test_stub_matches_headless_harness_surface():
    if TORCH_AVAILABLE:
        pytest.skip("real torch installed")
    assert torch.cuda.is_available() is False
    assert isinstance(torch.Tensor, type)
    assert issubclass(torch.cuda.OutOfMemoryError, RuntimeError)


def test_generation_without_torch_is_an_environment_error():
    if TORCH_AVAILABLE:
        pytest.skip("real torch installed")
    with pytest.raises(EnvironmentError, match="ROCm locally, CUDA"):
        require_torch("scientific generation")
