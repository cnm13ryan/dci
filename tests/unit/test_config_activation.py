"""Activating a profile must reach consumers that imported ACTIVE earlier.

Stage c112 builds the hashed ProtocolConfig from ACTIVE at module import time.
While activate() rebound the module global, whether `--profile study` took
effect depended on import order: anything that touched a stage module first
kept the dev_fast object and the run silently proceeded under the wrong
profile. This file pins the fixed contract - one stable object identity.
"""
import dataclasses

import pytest

from dci.config import loader
from dci.config.loader import ActiveConfig, activate, active, load_profile
from dci.storage.layout import is_colab_default_root

pytestmark = pytest.mark.cpu


@pytest.fixture(autouse=True)
def restore_active():
    """The profile is process-global state; give every test a clean one back."""
    saved = dataclasses.replace(loader.ACTIVE)
    yield
    activate(saved)


def _study_profile(tmp_path):
    path = tmp_path / "study.toml"
    path.write_text('model_profile = "study"\n'
                    'run_mode = "full"\n'
                    'dry_run_mode = false\n'
                    'use_google_drive = false\n')
    return path


def test_importer_that_bound_active_early_observes_the_activated_profile(tmp_path):
    early = loader.ACTIVE                      # what c112 holds at import time
    assert early.model_profile == "dev_fast"

    activate(load_profile(_study_profile(tmp_path)))

    assert early.model_profile == "study"      # same object, updated in place
    assert early.dry_run_mode is False
    assert early is loader.ACTIVE
    assert active() is early


def test_activate_does_not_alias_the_caller_object(tmp_path):
    cfg = load_profile(_study_profile(tmp_path))
    activate(cfg)
    cfg.protocol_overrides["n_tasks"] = 4      # mutating the caller's copy
    assert "n_tasks" not in loader.ACTIVE.protocol_overrides


def test_activate_copies_every_declared_field():
    """A field added later must not quietly stop propagating."""
    cfg = ActiveConfig(model_profile="pilot", run_mode="full", dry_run_mode=False,
                       use_google_drive=False, run_id="run-x", data_root="/tmp/x",
                       backend="oracle", device_index=3, shard_index=1,
                       shard_total=2, protocol_overrides={"n_tasks": 8},
                       profile_path="p.toml")
    activate(cfg)
    for field in dataclasses.fields(ActiveConfig):
        assert getattr(loader.ACTIVE, field.name) == getattr(cfg, field.name)


@pytest.mark.parametrize("root,expected", [
    ("/content/drive/MyDrive/directional_interference", True),
    ("/content/directional_interference_local", True),
    ("/content", True),
    ("/content-data/dci", False),          # the misclassified case
    ("/contentious/dci", False),
    ("/lambda/nfs/dci-fs/dci", False),
    ("/Users/x/git/dci/artifacts/durable", False),
])
def test_colab_root_detection_uses_path_semantics(root, expected):
    assert is_colab_default_root(root) is expected


def test_planning_only_defaults_off_and_survives_activation(tmp_path):
    assert loader.ACTIVE.planning_only is False
    path = tmp_path / "p.toml"
    path.write_text('model_profile = "study"\nplanning_only = true\n')
    activate(load_profile(path))
    assert loader.ACTIVE.planning_only is True
