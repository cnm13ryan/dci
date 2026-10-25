"""Freeze 1, approvals, the authorisation gate, and the isolation of the
historical study."""
from __future__ import annotations

import ast
import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from dci.batch1 import config as CFG
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import runner as RUN
from dci.batch1 import topics as TOP
from tests.batch1.conftest import REPO
from tests.batch1.helpers import approved, fake_lock, fake_probe

pytestmark = pytest.mark.cpu

FROZEN_V81 = "034fc72"


@pytest.fixture(scope="module")
def proposed():
    return F.freeze1_manifest()


def test_freeze1_is_deterministic_and_hash_bound(proposed):
    again = F.freeze1_manifest()
    assert again == proposed
    assert F.validate_freeze1(proposed, F.approvals_template()) == []
    assert proposed["stage1"]["rows"] == 15_616
    assert proposed["topics"]["overlap_clean"]
    assert proposed["compatibility"]["unresolved"] == []


def test_unapproved_protocol_is_not_authorisable(proposed):
    auth = proposed["authorization"]
    assert not auth["pilot_authorizable"]
    assert len(auth["blocking"]) == len(CFG.decisions()) + 1
    assert any("UNATTESTED" in b for b in auth["blocking"])
    assert proposed["execution_environment"] == {"status": "UNATTESTED"}
    with pytest.raises(F.AuthorizationError, match="not authorisable"):
        F.assert_authorized(proposed, F.approvals_template(),
                            proposed["manifest_hash"])


def test_approved_decisions_without_an_attested_environment_are_not_enough():
    approvals = approved()
    manifest = F.freeze1_manifest(approvals=approvals)
    assert manifest["authorization"]["blocking"] == [
        b for b in manifest["authorization"]["blocking"] if "UNATTESTED" in b]
    assert not manifest["authorization"]["pilot_authorizable"]


def test_fully_approved_protocol_needs_the_token_and_the_locked_environment():
    approvals = approved()
    manifest = F.freeze1_manifest(approvals=approvals,
                                  environment_lock=fake_lock())
    assert manifest["authorization"]["pilot_authorizable"]
    assert F.validate_freeze1(manifest, approvals) == []
    with pytest.raises(F.AuthorizationError, match="token"):
        F.assert_authorized(manifest, approvals, None,
                            live_environment=fake_probe())
    with pytest.raises(F.AuthorizationError, match="token"):
        F.assert_authorized(manifest, approvals, "0" * 64,
                            live_environment=fake_probe())
    with pytest.raises(F.AuthorizationError, match="could not be checked"):
        F.assert_authorized(manifest, approvals, manifest["manifest_hash"])
    F.assert_authorized(manifest, approvals, manifest["manifest_hash"],
                        live_environment=fake_probe)


def test_an_approval_of_a_changed_payload_is_void():
    approvals = approved()
    approvals["decisions"]["D06"]["payload_hash"] = "0" * 64
    manifest = F.freeze1_manifest(approvals=approvals)
    assert manifest["decisions"]["D06"]["status"] == "APPROVAL_VOID"
    assert not manifest["authorization"]["pilot_authorizable"]
    changed = CFG.PilotConfig(stage2_max_cells=241)
    assert CFG.decision_payloads(changed)["D06"] != \
        CFG.decision_payloads()["D06"]


def test_editing_the_manifest_is_detected(proposed):
    edited = copy.deepcopy(proposed)
    edited["config"]["eligibility_threshold"] = 0.15
    problems = F.validate_freeze1(edited, F.approvals_template())
    assert any("manifest_hash" in p for p in problems)
    body = {k: v for k, v in edited.items() if k != "manifest_hash"}
    from dci.provenance.hashes import sha
    edited["manifest_hash"] = sha(["batch1/freeze1", body])
    problems = F.validate_freeze1(edited, F.approvals_template())
    assert problems and not any("manifest_hash" in p for p in problems)


def test_modifying_a_frozen_input_is_detected(proposed, tmp_path, monkeypatch):
    doc = json.loads(TOP.SOURCE_PATH.read_text())
    doc["topics"][0]["question"] = "Why is this question different now?"
    edited = tmp_path / "topics_source.json"
    edited.write_text(json.dumps(doc))
    monkeypatch.setattr(TOP, "SOURCE_PATH", edited)
    problems = F.validate_freeze1(proposed, F.approvals_template())
    assert any("topics" in p for p in problems)


def _package_copy(tmp_path):
    pkg = tmp_path / "pkg"
    shutil.copytree(Path(F.__file__).parent, pkg,
                    ignore=shutil.ignore_patterns("__pycache__", "data"))
    return pkg


def test_modifying_a_rule_module_is_detected(proposed, tmp_path, monkeypatch):
    pkg = _package_copy(tmp_path)
    source = (pkg / "calibration.py").read_text()
    (pkg / "calibration.py").write_text(source.replace(
        '"ELIGIBILITY_10")', '"ELIGIBILITY_10", "EXTRA")', 1))
    monkeypatch.setattr(F, "_PKG", pkg)
    problems = F.validate_freeze1(proposed, F.approvals_template())
    assert any("rule_sources" in p and "calibration.py" in p for p in problems)


def test_a_comment_or_docstring_edit_does_not_move_freeze1(proposed, tmp_path,
                                                           monkeypatch):
    pkg = _package_copy(tmp_path)
    source = (pkg / "calibration.py").read_text()
    (pkg / "calibration.py").write_text(
        source.replace('"""Stage 2 refinement', '"""(Edited docs.) Stage 2 '
                       'refinement', 1) + "\n# a comment\n")
    monkeypatch.setattr(F, "_PKG", pkg)
    assert not [p for p in F.validate_freeze1(proposed, F.approvals_template())
                if "rule_sources" in p]


def test_real_execution_refuses_without_authorisation(proposed, tmp_path,
                                                      monkeypatch):
    launched = []
    monkeypatch.setattr(RUN, "subprocess_backend",
                        lambda spec: launched.append(spec))
    with pytest.raises(F.AuthorizationError):
        RUN.execute(tmp_path / "run", [], freeze1=proposed,
                    approvals=F.approvals_template(), token=None)
    assert launched == [] and not (tmp_path / "run").exists()


def test_authorised_execution_reaches_the_backend_only_through_the_gate(
        tmp_path, monkeypatch):
    approvals = approved()
    manifest = F.freeze1_manifest(approvals=approvals,
                                  environment_lock=fake_lock())
    calls = []

    def fake_backend(spec):
        def generate(run_dir, plan, rows):
            calls.append((plan["model_id"], len(rows)))
            return {"rows": [], "provenance": {}, "returncode": 0}
        return generate
    monkeypatch.setattr(RUN, "subprocess_backend", fake_backend)
    monkeypatch.setattr(RUN.ENV, "probe", lambda python: fake_probe())
    cuda = RUN.BackendSpec(visibility_var="CUDA_VISIBLE_DEVICES")
    row = next(r for r in EV.expected_design(tmp_path, manifest, "stage1")
               if r["model"] == "qwen3-4b")
    summary = RUN.execute(tmp_path / "run", [row], freeze1=manifest,
                          approvals=approvals, token=manifest["manifest_hash"],
                    backend=cuda)
    assert calls == [("Qwen/Qwen3-4B", 1)]
    assert summary["open"] == 1 and not summary["complete"]   # not returned
    with pytest.raises(RUN.RunError, match="composed"):
        RUN.execute(tmp_path / "run", [dict(row, load=2)], freeze1=manifest,
                    approvals=approvals, token=manifest["manifest_hash"],
                    backend=cuda)
    monkeypatch.setattr(RUN.ENV, "probe",
                        lambda python: fake_probe(python="3.13.0"))
    with pytest.raises(F.AuthorizationError, match="differs from the attested"):
        RUN.execute(tmp_path / "run", [row], freeze1=manifest,
                    approvals=approvals, token=manifest["manifest_hash"],
                    backend=cuda)
    assert len(calls) == 1


def test_synthetic_and_real_namespaces_never_share_a_root(tmp_path):
    RUN.init_root(tmp_path, synthetic=True, freeze1_hash="a")
    with pytest.raises(RUN.RunError, match="another run"):
        RUN.init_root(tmp_path, synthetic=False, freeze1_hash="a")
    with pytest.raises(RUN.RunError, match="another run"):
        RUN.init_root(tmp_path, synthetic=True, freeze1_hash="b")


def test_backend_plan_carries_the_registered_decoding_and_gpu_selection():
    plan = RUN.seam_plan(CFG.MODEL_BY_KEY["qwen3-4b"], "stage1")
    assert (plan["temperature"], plan["top_p"], plan["top_k"]) == (0.7, 0.9, 50)
    assert plan["chat_template_kwargs"] == {"enable_thinking": False}
    assert plan["generation_ceiling"] == CFG.DECODING["max_new_tokens"]
    env = RUN.BackendSpec(visibility_var="CUDA_VISIBLE_DEVICES", device=1).env()
    assert env["CUDA_VISIBLE_DEVICES"] == "1" and "HIP_VISIBLE_DEVICES" not in env
    with pytest.raises(RUN.RunError):
        RUN.BackendSpec(visibility_var="GPU").env()


def test_batch1_imports_no_dci1_package_and_no_composed_template():
    pkg = Path(F.__file__).parent
    for path in pkg.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                assert not name.startswith(("dci1", "bgrid", "cal_screen",
                                            "fs_screen", "matrix_screen")), \
                    (path.name, name)
    assert "PROMPT_TWO" not in (pkg / "config.py").read_text()


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True,
                          text=True)


def test_historical_v81_sources_are_unchanged_since_the_freeze():
    if _git("cat-file", "-e", f"{FROZEN_V81}^{{commit}}").returncode != 0:
        pytest.skip("the v8.1 freeze commit is not in this clone")
    paths = ["dci1/src/dci1v4", "dci1/src/dci1v7", "dci1/src/dci1v8dev",
             "dci1/docs/DCI1_preregistration_v8.1.md"]
    diff = _git("diff", "--stat", FROZEN_V81, "--", *paths)
    assert diff.returncode == 0 and diff.stdout.strip() == "", diff.stdout
    untracked = _git("ls-files", "--others", "--exclude-standard", "--", *paths)
    assert untracked.stdout.strip() == ""
