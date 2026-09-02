"""The freeze-readiness audit (confirm/readiness.py), on fabricated inputs:
every item passes on a consistent design, and each of the failure cases the
2026-09-02 audit found refuses the freeze on its own.
"""
from __future__ import annotations

import pytest

from dci1v4.protocol.hashing import sha_obj
from dci1v8dev import rules as R
from dci1v8dev.confirm import PREREGISTRATION_DOCUMENT
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import readiness as RD
from dci1v8dev.confirm.manifest import analysis_code_hashes
from dci1v8dev.run.lifecycle import instrument_hashes


def _prereg(repo, text="Status: FROZEN-READY\nCONFIRMATORY_BLOCKS_PER_FRAME = 384\n"):
    path = repo / PREREGISTRATION_DOCUMENT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return sha_obj({"path": PREREGISTRATION_DOCUMENT, "bytes": path.read_bytes().hex()})


def _inputs(tmp_path, *, synthetic=False):
    repo = tmp_path / "repo"
    h = _prereg(repo)
    ctx = L.confirm_context(tmp_path / "root", synthetic=synthetic, repo_root=repo)
    tree = L.confirm_tree(ctx, "qwen3-4b")
    stab = lambda status, ru=None: {                                  # noqa: E731
        "status": status, "unstable_coordinates": ["n_star"] if ru else [],
        "n_star": {"p_selected_reproduced": 0.5 if ru else 0.9, "runner_up": ru,
                   "status": status},
        "m_star": {"p_selected_reproduced": 0.95, "runner_up": None,
                   "status": R.OPERATING_POINT_STABLE}}
    core = [{"slot": "R1", "family": "MK1"}, {"slot": "R2", "family": "XC1"},
            {"slot": "R3", "family": "MK3"}]
    backups = [{"slot": "R4", "family": "MK2"}, {"slot": "R5", "family": "MK6"}]
    membership = {"by_frame": {
        "0": {"enters": True, "enters_local": True, "enters_spectrum": True,
              "stability": stab(R.OPERATING_POINT_UNSTABLE, ru=5),
              "runner_up_slots": ["A2"], "core": core, "backups": backups,
              "identification_statuses": [],
              "reference_sensitivity": {
                  "families": ["MK1", "XC1", "MK3", "MK2", "MK6"],
                  "admissible_triples": [{"slots": ["R1", "R2", "R3"]}],
                  "distances": {s: {} for s in ("R1", "R2", "R3", "R4", "R5")}}},
        "1": {"enters": True, "enters_local": False, "enters_spectrum": True,
              "stability": stab(R.OPERATING_POINT_UNSTABLE, ru=4),
              "runner_up_slots": [], "core": [], "backups": [],
              "identification_statuses": [], "reference_sensitivity": None},
        "2": {"enters": False, "supported": False}}}
    lock = {"allocation": {"chosen_blocks_per_frame": R.CONFIRMATORY_BLOCKS_PER_FRAME}}
    registration = {"documents": {PREREGISTRATION_DOCUMENT: h},
                    "analysis_code": analysis_code_hashes()}
    gate2 = {"calibration_allocation": {"frame_offsets": list(R.CALIBRATION_FRAME_OFFSETS),
                                        "topics_per_frame": R.CALIBRATION_TOPICS_PER_FRAME},
             **instrument_hashes()}
    return dict(tree=tree, membership=membership, repo_root=repo, lock=lock,
                registration=registration, pilot_gate2=gate2)


def test_a_consistent_design_is_ready(tmp_path):
    out = RD.freeze_readiness(**_inputs(tmp_path))
    assert out["ready"], out["failed"]
    assert set(out["items"]) == {
        "preregistration", "allocation", "calibration_policy",
        "operating_point_stability", "reference_sensitivity",
        "no_protected_artifacts", "instrument", "analysis_code", "worktree",
        "identification_statuses"}
    RD.assert_freeze_ready(out, tree=_inputs(tmp_path)["tree"])


def test_a_draft_preregistration_refuses_outside_synthetic(tmp_path):
    kw = _inputs(tmp_path)
    h = _prereg(kw["repo_root"], "Status: DRAFT\nCONFIRMATORY_BLOCKS_PER_FRAME = 384\n")
    kw["registration"]["documents"][PREREGISTRATION_DOCUMENT] = h
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["preregistration"]
    with pytest.raises(L.TerminalStatus) as exc:
        RD.assert_freeze_ready(out, tree=kw["tree"])
    assert exc.value.status == RD.FREEZE_REFUSED
    # the synthetic namespace records the draft and does not block on it
    kw2 = _inputs(tmp_path / "s", synthetic=True)
    h2 = _prereg(kw2["repo_root"], "Status: DRAFT\n")
    kw2["registration"]["documents"][PREREGISTRATION_DOCUMENT] = h2
    assert RD.freeze_readiness(**kw2)["ready"]


def test_a_preregistration_edited_after_registration_refuses(tmp_path):
    kw = _inputs(tmp_path)
    _prereg(kw["repo_root"], "Status: FROZEN-READY\nedited after the manifest bound it\n")
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["preregistration"]
    assert out["items"]["preregistration"]["bound_hash"] != \
        out["items"]["preregistration"]["current_hash"]


def test_a_second_allocation_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["lock"]["allocation"]["chosen_blocks_per_frame"] = 288
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["allocation"]


def test_a_pilot_calibrated_below_the_universal_allocation_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["pilot_gate2"]["calibration_allocation"] = {"frame_offsets": [0, 2],
                                                   "topics_per_frame": 96}
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["calibration_policy"]
    assert out["items"]["calibration_policy"]["required_frame_offsets"] == [0, 1, 2, 3]


def test_an_unstable_local_frame_without_its_runner_up_arm_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["membership"]["by_frame"]["0"]["runner_up_slots"] = []
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["operating_point_stability"]
    # and a runner-up arm on a stable frame is equally a mismatch
    kw = _inputs(tmp_path / "b")
    kw["membership"]["by_frame"]["0"]["stability"]["status"] = R.OPERATING_POINT_STABLE
    kw["membership"]["by_frame"]["0"]["stability"]["unstable_coordinates"] = []
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["operating_point_stability"]


def test_a_missing_stability_record_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["membership"]["by_frame"]["1"]["stability"] = None
    assert RD.freeze_readiness(**kw)["failed"] == ["operating_point_stability"]


def test_a_local_frame_without_five_frozen_families_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["membership"]["by_frame"]["0"]["reference_sensitivity"]["families"] = ["MK1", "XC1", "MK3"]
    assert RD.freeze_readiness(**kw)["failed"] == ["reference_sensitivity"]


def test_a_protected_artifact_under_the_tree_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["tree"].stage_dir(L.STAGE_GENERATION).mkdir(parents=True)
    out = RD.freeze_readiness(**kw)
    assert out["failed"] == ["no_protected_artifacts"]


def test_a_moved_instrument_or_analysis_module_refuses(tmp_path):
    kw = _inputs(tmp_path)
    kw["pilot_gate2"]["verifier_hash"] = "0" * 64
    assert RD.freeze_readiness(**kw)["failed"] == ["instrument"]
    kw = _inputs(tmp_path / "b")
    kw["registration"]["analysis_code"] = {"dci1v7/analysis/claims.py": "0" * 64}
    assert RD.freeze_readiness(**kw)["failed"] == ["analysis_code"]
