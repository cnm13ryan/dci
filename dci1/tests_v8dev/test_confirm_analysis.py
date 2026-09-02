"""The frame-aware analysis on fabricated confirmatory rows: every
registered estimator per frame, the joint family, the readings."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.models.registry import get_model
from dci1v7.protocol import constants as C
from dci1v7.topics.bank import load_bank
from dci1v8dev.confirm import analysis as A
from dci1v8dev.confirm import lifecycle as L
from dci1v8dev.confirm.design import FrameBlock, design_cells
from dci1v8dev.confirm.execute import generate_and_score, prompt_cell
from tests_v8dev import confirm_harness as H

MODEL = "qwen3-4b"
BLOCKS = 12


@pytest.fixture(scope="module")
def rows_and_freeze(tmp_path_factory):
    frames = {0: H.fabricated_frame(0, local=True, spectrum=True),
              3: H.fabricated_frame(3, local=True, spectrum=False),
              1: H.fabricated_frame(1, local=False, spectrum=True)}
    freeze = H.fabricated_freeze(frames, blocks_per_frame=BLOCKS)
    slot_maps = H.slot_maps_of(freeze)
    gen = H.composed_generate(slot_maps)
    bank = load_bank()
    topics = list(bank.topics("confirmatory"))[:BLOCKS]
    by_id = {t["topic_id"]: t for t in topics}
    root = tmp_path_factory.mktemp("confirm-rows")
    rows = []
    for w, e in frames.items():
        blocks = [FrameBlock(position=i, frame=w, topic_id=t["topic_id"],
                             area=t["area"]) for i, t in enumerate(topics)]
        cells = design_cells(blocks, e["arms"], n_spectrum=e["n_spectrum_slots"])
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_maps[w])
                   for c in cells]
        rows += generate_and_score(
            MODEL, prompts, stage=L.STAGE_GENERATION, cap=512, device=0,
            run_dir=Path(root) / f"frame-{w}",
            instances=tuple(dict.fromkeys(slot_maps[w].values())),
            slot_map=slot_maps[w], study_id="dci1v8-synthetic",
            protocol_identity={"test": True}, generate=gen,
            composed_licensed=True)
    return rows, freeze


def test_rows_carry_composed_cells_under_the_blocks_frame(rows_and_freeze):
    rows, _ = rows_and_freeze
    loads = {r["load"] for r in rows}
    assert loads == {0, 1, 2}
    for r in rows:
        assert r["block_frame"] == r["block_index"] % C.N_WORDINGS
        assert all(w == r["block_frame"] for w in r["wording_indices"])
        assert r["layer"] == "confirm" and "CONFIRMATORY" in r["classification"]


def test_analysis_forms_every_registered_member_per_frame(rows_and_freeze):
    rows, freeze = rows_and_freeze
    out = A.analyse_model(rows, freeze, model_id=get_model(MODEL).model_id,
                          resamples=150)
    assert set(out["frames"]) == {"0", "3", "1"}
    f0 = out["frames"]["0"]["configurations"][C.OUTCOME_FIRST]
    assert set(f0["F1"]["members"]) == {"D(B<-A)", "D(A<-B)", "Lambda",
                                        "Delta_R", "Xi", "delta_difficulty"}
    assert set(f0) >= {"F1", "F2", "F3", "F4", "F_REFSENS", "F_SPECTRUM"}
    f1 = out["frames"]["1"]["configurations"][C.OUTCOME_FIRST]
    assert "Delta_R" not in f1["F1"]["members"] and "F_REFSENS" not in f1
    assert "delta_difficulty" in f1["F1"]["members"]
    f3 = out["frames"]["3"]["configurations"][C.OUTCOME_FIRST]
    assert "delta_difficulty" not in f3["F1"]["members"]
    # per-block vectors have one entry per block; Delta_R's two forms agree
    dr = f0["F1"]["members"]["Delta_R"]
    assert len(dr["per_block"]) == BLOCKS
    assert out["frames"]["0"]["algebraic_forms"][C.OUTCOME_FIRST]["Delta_R"] < 1e-9
    assert dr["decision_lower"] <= dr["estimate"] <= dr["decision_upper"]
    # the reference-sensitivity family is every admissible triple, the
    # frozen core among them
    sens = f0["F_REFSENS"]["members"]
    triples = freeze["design"]["frames"]["0"]["reference_sensitivity"]["admissible_triples"]
    assert len(sens) == len(triples) and "Delta_R[R1+R2+R3]" in sens
    assert sens["Delta_R[R1+R2+R3]"]["estimate"] == pytest.approx(dr["estimate"])


def test_joint_family_covers_every_entering_frames_f1(rows_and_freeze):
    rows, freeze = rows_and_freeze
    out = A.analyse_model(rows, freeze, model_id=get_model(MODEL).model_id,
                          resamples=150)
    joint = out["joint"][C.OUTCOME_FIRST]
    names = set(joint["members"])
    assert {"f0:Delta_R", "f3:Delta_R", "f0:delta_difficulty",
            "f1:delta_difficulty", "f1:D(B<-A)"} <= names
    assert "f1:Delta_R" not in names
    assert joint["family_size"] == len(names) and joint["topics"] == BLOCKS
    # the joint decision interval is never narrower than the per-frame one
    for name, m in joint["members"].items():
        w, member = name.partition(":")[0][1:], name.partition(":")[2]
        per = out["frames"][w]["configurations"][C.OUTCOME_FIRST]["F1"]["members"][member]
        assert m["decision_half_width"] >= per["decision_half_width"] - 1e-9
    assert out["model_verdict"][C.OUTCOME_FIRST] in A.MODEL_VERDICTS
    assert set(joint["local_model_verdict"]["frames"]) == {"0", "3"}


def test_analysis_refuses_a_block_missing_a_cell(rows_and_freeze):
    rows, freeze = rows_and_freeze
    broken = [r for r in rows if not (r["block_frame"] == 0 and
                                      r["cell_id"] == "pair:B+R1")]
    with pytest.raises(Exception, match="missing"):
        A.analyse_model(broken, freeze, model_id=get_model(MODEL).model_id,
                        resamples=20)


def test_delta_r_sign_and_direction_on_a_companion_dependent_effect(tmp_path):
    """B is spoiled under A with probability 0.5 and under the references
    with 0.1: Delta_R must come out positive, read A_HARMS_MORE, and the
    joint interval must exclude zero; the reference-sensitivity triples
    that swap in the backups (spoiled at 0.1 too) agree in sign."""
    frames = {0: H.fabricated_frame(0, local=True, spectrum=False),
              2: H.fabricated_frame(2, local=True, spectrum=False)}
    freeze = H.fabricated_freeze(frames, blocks_per_frame=48)
    slot_maps = H.slot_maps_of(freeze)
    gen = H.effect_generate(slot_maps, spoil_b_under={
        "A": 0.5, "R1": 0.1, "R2": 0.1, "R3": 0.1, "R4": 0.1, "R5": 0.1})
    bank = load_bank()
    topics = list(bank.topics("confirmatory"))[:48]
    by_id = {t["topic_id"]: t for t in topics}
    rows = []
    for w, e in frames.items():
        blocks = [FrameBlock(position=i, frame=w, topic_id=t["topic_id"],
                             area=t["area"]) for i, t in enumerate(topics)]
        cells = design_cells(blocks, e["arms"], n_spectrum=0)
        prompts = [prompt_cell(c, by_id[c.topic_id], slot_map=slot_maps[w])
                   for c in cells]
        rows += generate_and_score(
            MODEL, prompts, stage=L.STAGE_GENERATION, cap=512, device=0,
            run_dir=Path(tmp_path) / f"frame-{w}",
            instances=tuple(dict.fromkeys(slot_maps[w].values())),
            slot_map=slot_maps[w], study_id="dci1v8-synthetic",
            protocol_identity={"test": True}, generate=gen,
            composed_licensed=True)
    out = A.analyse_model(rows, freeze, model_id=get_model(MODEL).model_id,
                          resamples=300)
    for cfg in C.CONFIGURATIONS:
        for w in ("0", "2"):
            dr = out["frames"][w]["configurations"][cfg]["F1"]["members"]["Delta_R"]
            assert dr["estimate"] > 0.2, (w, cfg, dr["estimate"])
            assert dr["reading"]["direction"]["direction"] == "A_HARMS_MORE"
            j = out["joint"][cfg]["members"][f"f{w}:Delta_R"]
            assert j["decision_lower"] > 0.0
            # D(B<-A) is the loss under A: positive and larger than under R1
            f1 = out["frames"][w]["configurations"][cfg]["F1"]["members"]
            f2 = out["frames"][w]["configurations"][cfg]["F2"]["members"]
            assert f1["D(B<-A)"]["estimate"] > f2["D(B<-R1)"]["estimate"] > -0.05
            sens = out["frames"][w]["configurations"][cfg]["F_REFSENS"]["members"]
            assert all(m["estimate"] > 0.15 for m in sens.values())
        # 48 blocks cannot meet the 0.05 precondition; the verdict says so
        # rather than claiming, and the direction is nonetheless resolved
        assert out["model_verdict"][cfg] in ("LOCAL_SUPPORTED_L3a",
                                              "LOCAL_SUPPORTED_L3b",
                                              "INSUFFICIENT_PRECISION")
        for w in ("0", "2"):
            j = out["joint"][cfg]["members"][f"f{w}:Delta_R"]
            assert j["reading"]["direction_resolved"] is True
