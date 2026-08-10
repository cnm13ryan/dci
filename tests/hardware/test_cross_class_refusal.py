"""The migration's central hardware rule: a scientific resume across hardware
execution classes is refused. CPU-runnable: the assertion logic is pure."""
import pytest

pytestmark = pytest.mark.cpu


def test_amd_to_nvidia_resume_is_refused(tmp_path):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    from dci.exceptions import StudyStop

    cfg = loader.load_profile("configs/profiles/dev_fast.toml")
    cfg.data_root = str(tmp_path)
    loader.activate(cfg)
    assert run_pipeline(until="c122") == 0

    frozen_on_workstation = {
        "gpu_name": "AMD Radeon RX 7900 XTX", "compute_capability": "11.0",
        "cuda_runtime": None, "torch_cuda_build": "2.9.1+rocm7.2",
        "attn_implementation": "sdpa", "device_count": 2, "class": "amd7900",
    }
    # simulate the evidence-producing condition the check guards
    object.__setattr__(S.CFG, "dry_run", False)
    try:
        with pytest.raises(StudyStop) as err:
            S.assert_hardware_class(frozen_on_workstation)
        assert err.value.outcome.status == "HARDWARE_CLASS_MISMATCH"
        assert err.value.outcome.new_protocol_version_required
    finally:
        object.__setattr__(S.CFG, "dry_run", True)


def test_no_equivalence_classes_are_declared(tmp_path):
    from dci.config import loader
    from dci.pipeline.runner import run_pipeline
    from dci.pipeline import state as S
    cfg = loader.load_profile("configs/profiles/dev_fast.toml")
    cfg.data_root = str(tmp_path)
    loader.activate(cfg)
    assert run_pipeline(until="c122") == 0
    assert S.CFG.enforce_hardware_class is True
    assert S.CFG.hardware_equivalence_classes == ()
