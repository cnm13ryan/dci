import pytest

from dci.config import loader

pytestmark = pytest.mark.cpu


def test_defaults_match_the_notebook_switches():
    cfg = loader.ActiveConfig()
    assert (cfg.model_profile, cfg.run_mode, cfg.dry_run_mode,
            cfg.use_google_drive, cfg.run_id) == ("dev_fast", "smoke", True, True, None)


def test_unknown_profile_key_is_rejected(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text('model_profile = "dev_fast"\nnot_a_key = 1\n')
    with pytest.raises(KeyError):
        loader.load_profile(p)


def test_storage_overrides_route_under_data_root(tmp_path):
    cfg = loader.ActiveConfig(data_root=str(tmp_path))
    ov = cfg.storage_overrides()
    assert ov["drive_root"].endswith("durable") and ov["local_root"].endswith("local")


def test_dry_run_refuses_non_oracle_backend():
    from dci.inference import make_backend
    from dci.pipeline import state as S

    class _CFG:
        dry_run = True
        engine = "hf_transformers"

    S.CFG = _CFG()
    loader.activate(loader.ActiveConfig(backend="hf_transformers"))
    try:
        with pytest.raises(RuntimeError, match="dry run"):
            make_backend()
    finally:
        loader.activate(loader.ActiveConfig())
        S.reset()
