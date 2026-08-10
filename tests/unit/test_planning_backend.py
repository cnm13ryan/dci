"""Planning mode refuses generation structurally, whatever the profile says.

The guarantee must not depend on where the stage boundary happens to fall. A
gate that grew a micro-generation self-test, or a hand-passed --until, used to
be enough to make a "no generation" command generate.
"""
import dataclasses
import types

import pytest

from dci.config import loader
from dci.config.loader import activate
from dci.inference import make_backend
from dci.inference.planning import PlanningBackend, PlanningModeViolation

pytestmark = pytest.mark.cpu


@pytest.fixture(autouse=True)
def restore_active():
    saved = dataclasses.replace(loader.ACTIVE)
    yield
    activate(saved)


@pytest.fixture
def fake_state(monkeypatch):
    """A minimal state module: make_backend reads only CFG off it."""
    from dci.pipeline import state

    def _cfg(dry_run, engine="hf_transformers"):
        monkeypatch.setattr(state, "CFG",
                            types.SimpleNamespace(dry_run=dry_run, engine=engine),
                            raising=False)
    return _cfg


@pytest.mark.parametrize("dry_run", [True, False])
def test_planning_mode_wins_over_every_other_branch(fake_state, dry_run):
    fake_state(dry_run=dry_run)
    activate(dataclasses.replace(loader.ACTIVE, planning_only=True,
                                 dry_run_mode=dry_run, backend=None))
    assert isinstance(make_backend(), PlanningBackend)


def test_planning_mode_refuses_even_the_synthetic_oracle(fake_state):
    """Synthetic output written into a run directory is the hazard."""
    fake_state(dry_run=True)
    activate(dataclasses.replace(loader.ACTIVE, planning_only=True,
                                 backend="oracle"))
    assert make_backend().name == "planning_no_generation"


def test_generation_raises_rather_than_returning_empty_text():
    backend = PlanningBackend()
    with pytest.raises(PlanningModeViolation, match="refused to generate 2 row"):
        backend.generate([{"row_id": "a"}, {"row_id": "b"}], 1234)


def test_loading_the_model_is_refused():
    with pytest.raises(PlanningModeViolation, match="refused to load"):
        PlanningBackend().load_model()


def test_the_tokenizer_is_refused():
    with pytest.raises(PlanningModeViolation, match="no tokenizer"):
        PlanningBackend().tokenizer


def test_freeing_a_model_that_was_never_loaded_is_harmless():
    assert PlanningBackend().free_model() is None


def test_it_satisfies_the_backend_contract():
    """Structurally, member by member: the Protocol is not runtime-checkable."""
    from dci.inference.base import InferenceBackend
    required = [name for name in vars(InferenceBackend)
                if not name.startswith("_")]
    assert "generate" in required
    for attribute in required:
        # On the CLASS: `tokenizer` is a property that refuses when read, and
        # hasattr only swallows AttributeError.
        assert hasattr(PlanningBackend, attribute), attribute


def test_a_real_run_is_unaffected(fake_state):
    """planning_only off must leave backend selection exactly as it was."""
    fake_state(dry_run=True)
    activate(dataclasses.replace(loader.ACTIVE, planning_only=False,
                                 backend="oracle"))
    assert make_backend().name != "planning_no_generation"
