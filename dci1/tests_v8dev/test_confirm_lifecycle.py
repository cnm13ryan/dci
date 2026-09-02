"""The whole confirmatory lifecycle, executed with no model (``slow``):
a synthetic pilot root is walked first (the pilot harness), then the seven
confirmatory stages run on it through the production runners in the
``confirm-synthetic`` namespace."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError
from dci1v7.protocol import constants as C
from dci1v8dev.confirm import MEMBERSHIP_DOCUMENT
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm import (analysis, freeze, generation, membership,
                               registration, report, topup)
from tests_v8dev import confirm_harness as H
from tests_v8dev import pilot_harness as PH

MODEL = "qwen3-4b"      # the four-pass pilot model: every frame on every topic


@pytest.fixture(scope="module")
def pilot(tmp_path_factory):
    root = tmp_path_factory.mktemp("v8-pilot-synthetic")
    return PH.walk(root, topic_limit=96, resamples=120, model_key=MODEL)


@pytest.fixture(scope="module")
def walked(pilot, tmp_path_factory):
    root = tmp_path_factory.mktemp("v8-confirm-synthetic")
    repo_root = pilot["repo_root"]
    commit = pilot["commit"]
    # the confirm design note must exist in the synthetic repo for the
    # manifest to bind it
    doc = Path(repo_root) / "dci1/docs/V8_CONFIRMATORY.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# SYNTHETIC PLACEHOLDER\n")
    ctx = L.confirm_context(root, synthetic=True, repo_root=repo_root)
    tree = L.confirm_tree(ctx, MODEL)
    from dci1v4.engine.signing import create_signing_key
    create_signing_key(ctx.signing_key_path)
    pilot_root = Path(pilot["tree"].context.evidence_root).parent
    payloads = {}
    env = "synthetic"
    payloads[L.STAGE_REGISTERED] = registration.run_registration(
        tree, pilot_roots={MODEL: str(pilot_root)}, producing_commit=commit,
        environment_digest=env, repo_root=repo_root).payload
    # a top-up generator: solo:<label> cells resolved from their label
    payloads[L.STAGE_TOPUP] = topup.run_topup(
        tree, producing_commit=commit, environment_digest=env,
        generate=H.composed_generate({})).payload
    payloads[L.STAGE_MEMBERSHIP] = membership.run_membership(
        tree, producing_commit=commit, environment_digest=env,
        resamples=100).payload
    # the study-level lock, written from the record, into the synthetic repo
    from tools.v8_membership_lock import collect, render
    lock = collect(root, synthetic=True)
    out = Path(repo_root) / MEMBERSHIP_DOCUMENT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n")
    out.with_suffix(".md").write_text(render(lock))
    return {"tree": tree, "payloads": payloads, "root": root,
            "repo_root": repo_root, "commit": commit, "lock": lock,
            "pilot_root": pilot_root}


@pytest.mark.slow
def test_prefreeze_stages_read_the_pilot_and_generate_no_composed_cell(walked):
    p = walked["payloads"]
    reg = p[L.STAGE_REGISTERED]
    assert reg["pilot_source"]["record_hashes"]
    tu = p[L.STAGE_TOPUP]
    assert tu["no_composed_cells"] and set(tu["plan"]["by_frame"]) == {"0", "1", "2", "3"}
    for frame, ok in tu["untouched_frames_reproduce_pilot"].items():
        assert ok, frame
    mem = p[L.STAGE_MEMBERSHIP]
    assert mem["no_composed_cells"]
    for w, e in mem["by_frame"].items():
        if e["supported"]:
            assert e["stability"]["n_star"]["p_selected_reproduced"] is not None
    tree = walked["tree"]
    for stage in (L.STAGE_TOPUP,):
        for path in tree.backend_runs(stage).rglob("scored.jsonl"):
            for line in path.read_text().splitlines():
                assert json.loads(line)["load"] <= 1


@pytest.mark.slow
def test_freeze_generation_analysis_report(walked):
    tree, commit = walked["tree"], walked["commit"]
    repo_root = walked["repo_root"]
    mem = walked["payloads"][L.STAGE_MEMBERSHIP]
    env = "synthetic"
    if not mem["enters_study"]:
        with pytest.raises(L.TerminalStatus):
            freeze.run_freeze(tree, producing_commit=commit,
                              environment_digest=env, repo_root=repo_root,
                              blocks_per_frame=8)
        assert L.terminal_status(tree) == "NOT_ELIGIBLE"
        pytest.skip("the synthetic pilot admitted no frame; the terminal "
                    "path is what was exercised")
    fz = freeze.run_freeze(tree, producing_commit=commit,
                           environment_digest=env, repo_root=repo_root,
                           blocks_per_frame=8).payload
    assert fz["design"]["blocks_per_frame"] == 8
    assert set(fz["design"]["frames"]) == {str(w) for w in mem["frames_entering"]}
    # the freeze is immutable: no earlier stage may write now
    with pytest.raises(IntegrityError, match="after the freeze"):
        L.assert_no_post_freeze_mutation(tree, L.STAGE_MEMBERSHIP)
    with pytest.raises(IntegrityError):
        L.assert_transition_legal(tree, L.STAGE_TOPUP)
    slot_maps = H.slot_maps_of(fz)
    gen = generation.run_generation(
        tree, producing_commit=commit, environment_digest=env,
        generate=H.composed_generate(slot_maps), block_limit=8).payload
    assert gen["completeness"]["complete"] and gen["protected"]
    for w, fr in gen["frames"].items():
        assert fr["blocks"] == 8
        assert gen["allocation_realised"][w]["every_slot_under_block_frame"]
    an = analysis.run_analysis(tree, producing_commit=commit,
                               environment_digest=env, resamples=120).payload
    assert an["freeze_hash"] == fs.read_json(tree.stage_record(L.STAGE_FROZEN))["record_hash"]
    for cfg in C.CONFIGURATIONS:
        assert an["model_verdict"][cfg] in analysis.MODEL_VERDICTS
        joint = an["joint"][cfg]
        assert joint["family_size"] == len(joint["members"])
    rp = report.run_report(tree, producing_commit=commit,
                           environment_digest=env).payload
    assert rp["protected"] and set(rp["frames"]) == set(an["frames"])
    assert rp["deviations"]
    # every record is signed and reads back
    for stage in L.STAGE_SEQUENCE:
        rec = L.read_stage_record(tree, stage)
        assert rec["outcome"] == "PASS" and rec["layer"] == "confirm"
