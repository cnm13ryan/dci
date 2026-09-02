"""The confirmatory design, the allocation rule and the joint family."""
from __future__ import annotations

import math
import random

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.analysis.bootstrap import bootstrap_family, sidak_critical
from dci1v7.protocol import constants as C
from dci1v8dev.confirm import design as D
from dci1v8dev.confirm import precision as P
from dci1v8dev.confirm.analysis import joint_members, local_model_verdict


def test_cell_counts_by_arm():
    assert D.n_cells_for(["base"], n_spectrum=0) == 5
    assert D.n_cells_for(["base", "core"], n_spectrum=0) == 26
    assert D.n_cells_for(["base", "core", "backup"], n_spectrum=0) == 32
    assert D.n_cells_for(["base", "spectrum"], n_spectrum=8) == 29
    full = [a for a in D.ARMS if a != D.ARM_RUNNER_UP]
    assert D.n_cells_for(full, n_spectrum=8) == 56
    assert len(D.cell_types(full, n_spectrum=8)) == 56
    assert D.n_cells_for(D.ARMS, n_spectrum=8, runner_up=("A2",)) == 59
    assert len(D.cell_types(D.ARMS, n_spectrum=8, runner_up=("A2", "B2"))) == 68


def test_backup_arm_needs_core():
    with pytest.raises(ProtocolError):
        D.normalise_arms(["base", "backup"])


def test_every_slot_of_a_block_is_under_the_blocks_frame():
    topics = [{"topic_id": f"t{i}", "area": "a"} for i in range(8)]
    for frame in range(C.N_WORDINGS):
        blocks = D.frame_blocks(topics, frame)
        cells = D.design_cells(blocks, D.ARMS, n_spectrum=3, runner_up=("A2",))
        for cell in cells:
            assert cell.block_index % C.N_WORDINGS == frame
            assert all(w == frame for w in cell.wording_by_slot.values())
        D.assert_frame_allocation(cells, D.ARMS, n_spectrum=3, frame=frame, runner_up=("A2",),
                                  blocks_expected=8)


def test_both_orders_of_every_pair_in_every_block():
    types = D.cell_types(["base", "core", "backup"], n_spectrum=0)
    composed = {t.slots for t in types if t.arm == "composed"}
    for first, second in list(composed):
        assert (second, first) in composed
    assert ("B", "R4") in composed and ("R4", "B") in composed
    assert ("R1", "R4") not in composed          # backups are linear with B


def test_precision_is_projected_at_the_one_allocation_and_never_chosen():
    two = P.precision_at(2)
    assert two["blocks_per_frame"] == 384 == P.ALLOCATION
    assert two["precondition_met_adverse"] and two["precondition_met_planning"]
    four = P.precision_at(4)
    assert four["blocks_per_frame"] == 384 and not four["precondition_met_adverse"]
    rec = P.allocation_record({"a": 2, "b": 4, "c": 0})
    assert rec["chosen_blocks_per_frame"] == 384
    assert rec["decided_at_n_frames"] == 4
    assert not rec["precondition_met_adverse_at_max"]
    assert rec["per_model"]["a"]["precondition_met_adverse"]
    # the projection arithmetic is §16.1's, at the registered constants
    row = two["table"]["REGISTERED_PLANNING"]
    assert abs(row["half_width_frame"] - 0.0390) < 5e-4
    assert row["critical_joint"] == pytest.approx(sidak_critical(12))


def test_runner_up_arm_adds_the_sensitivity_cells_and_needs_the_core():
    arms = ["base", "core", "backup", "runner_up"]
    assert D.n_cells_for(arms, n_spectrum=0, runner_up=("A2",)) == 35
    assert D.n_cells_for(arms, n_spectrum=0, runner_up=("B2",)) == 41
    assert D.n_cells_for(arms, n_spectrum=0, runner_up=("A2", "B2")) == 44
    types = D.cell_types(arms, n_spectrum=0, runner_up=("A2", "B2"))
    composed = {t.slots for t in types if t.arm == "composed"}
    assert ("B", "A2") in composed and ("A2", "B") in composed
    assert ("A", "B2") in composed and ("B2", "A") in composed
    for r in C.CORE_SLOTS:
        assert (r, "B2") in composed and ("B2", r) in composed
    assert not any("A2" in s and "B2" in s for s in composed)
    with pytest.raises(ProtocolError):
        D.cell_types(["base", "runner_up"], n_spectrum=0, runner_up=("A2",))
    with pytest.raises(ProtocolError):
        D.cell_types(arms, n_spectrum=0)          # the arm names no slot
    with pytest.raises(ProtocolError):
        D.cell_types(["base", "core"], n_spectrum=0, runner_up=("A2",))


def test_joint_family_shares_one_topic_draw_across_frames():
    rng = random.Random(3)
    n = 40
    # two frames over the same topics; frame 1 holds only 30 of them
    v0 = [rng.gauss(0.1, 0.2) for _ in range(n)]
    v1 = [rng.gauss(0.1, 0.2) for _ in range(30)]
    per_frame = {0: {"Delta_R": v0}, 1: {"Delta_R": v1}}
    positions = {0: list(range(n)), 1: list(range(30))}
    jm = joint_members(per_frame, positions, n)
    res = bootstrap_family(jm, seed=1, configuration="c", family="JOINT_F1",
                           n_blocks=n, resamples=300)
    assert set(res.members) == {"f0:Delta_R", "f1:Delta_R"}
    assert res.members["f0:Delta_R"].estimate == pytest.approx(sum(v0) / n)
    assert res.members["f1:Delta_R"].estimate == pytest.approx(sum(v1) / 30)
    assert res.critical_value >= 1.0


def test_local_model_verdict_is_a_conjunction():
    a = {"levels": ["L3a"], "markers": []}
    b = {"levels": ["L3a", "L3b"], "markers": []}
    c = {"levels": ["L3c"], "markers": []}
    ip = {"levels": [], "markers": ["INSUFFICIENT_PRECISION"]}
    assert local_model_verdict({0: a, 3: a})["verdict"] == "LOCAL_SUPPORTED_L3a"
    assert local_model_verdict({0: b, 3: b})["verdict"] == "LOCAL_SUPPORTED_L3b"
    assert local_model_verdict({0: a, 3: b})["verdict"] == "LOCAL_SUPPORTED_L3a"
    assert local_model_verdict({0: a, 3: c})["verdict"] == "FRAME_HETEROGENEOUS"
    assert local_model_verdict({0: c, 3: c})["verdict"] == "LOCAL_EQUIVALENT_L3c"
    assert local_model_verdict({0: a, 3: ip})["verdict"] == "INSUFFICIENT_PRECISION"
    assert local_model_verdict({})["verdict"] == "UNIDENTIFIED"


def test_frame_blocks_index_encodes_the_frame():
    topics = [{"topic_id": f"t{i}", "area": "a"} for i in range(5)]
    for f in range(4):
        for b in D.frame_blocks(topics, f):
            assert b.index % C.N_WORDINGS == f
            assert int(b.block_id.rpartition("-")[2]) == b.index
