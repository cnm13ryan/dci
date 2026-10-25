"""Approvals bind the code that implements them, and Freeze 1 binds the
execution environment (audit F7)."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from dci.batch1 import config as CFG
from dci.batch1 import design as D
from dci.batch1 import environment as ENV
from dci.batch1 import freeze as F
from dci.batch1 import store
from tests.batch1.helpers import approved, fake_lock, fake_probe

pytestmark = pytest.mark.cpu


def _payloads():
    return CFG.decision_payloads()


@pytest.fixture
def pkg(tmp_path, monkeypatch):
    """A copy of the package that the decision register reads."""
    copy = tmp_path / "pkg"
    shutil.copytree(Path(CFG.__file__).parent, copy,
                    ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(CFG, "_PKG", copy)
    return copy


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))


def test_every_decision_binds_its_implementation():
    for d in CFG.decisions():
        impl = d.payload["implementation"]
        assert impl and set(impl) == set(CFG.IMPLEMENTATION[d.decision_id])
        assert all(len(h) == 64 for h in impl.values())


def test_changing_selection_code_voids_exactly_its_decisions(pkg):
    before = _payloads()
    _edit(pkg / "calibration.py", "if sep < need:", "if sep <= need:")
    after = _payloads()
    changed = {k for k in before if before[k] != after[k]}
    assert changed == {"D06", "D07", "D08"}


def test_changing_reference_code_voids_eligibility_matching_and_weights(pkg):
    before = _payloads()
    _edit(pkg / "references.py", "return count.n >= cfg.min_cell_fraction",
          "return count.n > cfg.min_cell_fraction")
    changed = {k for k, v in _payloads().items() if v != before[k]}
    assert changed == {"D08", "D09", "D10", "D11", "D13"}


def test_an_approval_of_the_old_code_is_void(pkg):
    approvals = approved()
    _edit(pkg / "calibration.py", "if sep < need:", "if sep <= need:")
    states, blocking = F._decision_state(CFG.DEFAULT_CONFIG, approvals)
    assert {k for k, v in states.items() if v["status"] == "APPROVAL_VOID"} == \
        {"D06", "D07", "D08"}


def test_a_documentation_edit_voids_nothing(pkg):
    before = _payloads()
    _edit(pkg / "calibration.py", '"""Stage 2 refinement, B selection',
          '"""(Reworded.) Stage 2 refinement, B selection')
    _edit(pkg / "references.py", "def usable(count: Count, cfg: CFG.PilotConfig) -> bool:",
          "def usable(count: Count, cfg: CFG.PilotConfig) -> bool:  # note")
    assert _payloads() == before


def test_scoring_and_outcome_code_bind_d04(pkg):
    before = _payloads()
    _edit(pkg / "outcomes.py", 'COMPLETED_FINISH_REASONS = frozenset({"stop", "length"})',
          'COMPLETED_FINISH_REASONS = frozenset({"stop", "length", "abort"})')
    changed = {k for k, v in _payloads().items() if v != before[k]}
    assert changed == {"D04", "D12"}


@pytest.mark.parametrize("change,decision", [
    ({"models": ("qwen3-4b", "qwen3-4b-instruct-2507", "gemma-3n-e2b-it")}, "D12"),
    ({"frames": ("F0",)}, "D02"),
    ({"generation_root_seed": 1}, "D12"),
    ({"seed_domain": "dci.batch1:gen:v2"}, "D12"),
    ({"b_min_median_separation": 0.2}, "D07"),
    ({"a_min_informative_model_frames": 5}, "D08"),
    ({"stability_replicates": 100}, "D14"),
])
def test_configuration_fields_reach_their_decision(change, decision):
    before = _payloads()
    after = CFG.decision_payloads(CFG.PilotConfig(**change))
    assert before[decision] != after[decision]


def test_the_prompt_template_binds_d02_and_the_design(monkeypatch):
    from dci.batch1 import pipeline as P
    before = _payloads()
    cells = [c for c in D.stage1_cells() if c.frame][:3]
    split = P.split_of(CFG.DEFAULT_CONFIG)
    digest = D.design_digest(D.rows_for_cells(cells, split))
    monkeypatch.setattr(CFG, "PROMPT_ONE",
                        "{question}\n\nAnswer briefly.\n\n1. {c1}\n\nAnswer:")
    assert CFG.decision_payloads()["D02"] != before["D02"]
    assert D.design_digest(D.rows_for_cells(cells, split)) != digest


@pytest.fixture
def backend_copy(tmp_path, monkeypatch):
    copy = tmp_path / "vllm_backend"
    shutil.copytree(ENV.BACKEND_DIR, copy,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def test_backend_source_binds_d12_and_freeze1(backend_copy, monkeypatch):
    approvals = approved()
    lock = fake_lock()
    manifest = F.freeze1_manifest(approvals=approvals, environment_lock=lock)
    assert manifest["authorization"]["pilot_authorizable"]
    before = _payloads()["D12"]
    monkeypatch.setattr(ENV, "BACKEND_DIR", backend_copy)
    assert _payloads()["D12"] == before          # an identical copy
    _edit(backend_copy / "records.py", "channel_valid = bool(emitted or answer.strip())",
          "channel_valid = True")
    assert _payloads()["D12"] != before
    problems = F.validate_freeze1(manifest, approvals)
    assert any("backend_source" in p for p in problems)
    assert any("D12" in p for p in problems)
    fresh = F.freeze1_manifest(approvals=approvals, environment_lock=lock)
    assert any("another vLLM seam source" in b
               for b in fresh["authorization"]["blocking"])


def test_the_environment_lock_is_checked_live():
    approvals = approved()
    manifest = F.freeze1_manifest(approvals=approvals,
                                  environment_lock=fake_lock())
    token = manifest["manifest_hash"]
    F.assert_authorized(manifest, approvals, token,
                        live_environment=fake_probe())
    for change in ({"python": "3.12.4"},
                   {"packages": {**fake_probe()["packages"], "vllm": "0.10.0"}},
                   {"distributions_hash": "e" * 64},
                   {"accelerators": ["Other GPU"]}):
        with pytest.raises(F.AuthorizationError, match="differs"):
            F.assert_authorized(manifest, approvals, token,
                                live_environment=fake_probe(**change))
    with pytest.raises(F.AuthorizationError, match="could not be checked"):
        F.assert_authorized(manifest, approvals, token,
                            live_environment={"status": "UNAVAILABLE",
                                              "reason": "no interpreter"})


def test_a_tampered_lock_blocks(monkeypatch):
    lock = fake_lock()
    lock["identity"]["packages"]["vllm"] = "edited"
    manifest = F.freeze1_manifest(approvals=approved(), environment_lock=lock)
    assert any("identity_hash" in b for b in manifest["authorization"]["blocking"])


def test_no_environment_is_fabricated_here(tmp_path):
    found = ENV.probe(str(tmp_path / "no-python"))
    assert found["status"] == "UNAVAILABLE"
    with pytest.raises(ValueError, match="no environment"):
        ENV.lock_from_probe(found)
    with pytest.raises(ValueError, match="no vLLM"):
        ENV.lock_from_probe(fake_probe(packages={"vllm": None}))


def test_freeze1_binds_every_executing_module():
    sources = F.rule_sources()
    pkg = Path(F.__file__).parent
    for path in pkg.glob("*.py"):
        if path.name not in F.NOT_FROZEN:
            assert sources[path.name] == store.code_hash(path)
    for name in ("pipeline.py", "evidence.py", "runner.py", "outcomes.py",
                 "environment.py", "smoke.py", "stability.py", "store.py",
                 "dci/verifiers/rules.py", "dci/provenance/hashes.py"):
        assert name in sources
    assert "report.py" not in sources and "simulate.py" not in sources
