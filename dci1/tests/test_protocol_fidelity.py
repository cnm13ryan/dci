"""§8.1 protocol fidelity: splits, arms, orders, wordings, prompt bytes."""
import pytest

pytestmark = pytest.mark.cpu

from dci1.constraints.definitions import assert_parse_independence
from dci1.design.blocks import (
    ADDED_FIRST,
    TARGET_FIRST,
    assert_block_plan,
    build_blocks,
)
from dci1.design.plan import (
    calibration_cells,
    confirmatory_blocks,
    confirmatory_cells,
    greedy_cells,
    pilot_blocks,
    pilot_cells,
)
from dci1.design.prompts import assert_matched_arm_byte_identity, prompt_for_cell
from dci1.protocol.constants import ARMS, N_BLOCKS, PRIMARY_ARMS, SUBJECT_AREAS
from dci1.topics.split import split_bank

REFS = ("C1", "C3", "C10")


def test_split_sizes_stratification_disjointness():
    split = split_bank()
    assert len(split["calibration"]) == 96
    assert len(split["confirmatory"]) == 384
    assert len(split["sequestered"]) == 96
    for area in SUBJECT_AREAS:
        assert sum(1 for t in split["calibration"] if t["area"] == area) == 8
        assert sum(1 for t in split["confirmatory"] if t["area"] == area) == 32
        assert sum(1 for t in split["sequestered"] if t["area"] == area) == 8
    ids = [t["topic_id"] for part in split.values() for t in part]
    assert len(set(ids)) == len(ids) == 576


def test_split_is_deterministic():
    a = [t["topic_id"] for t in split_bank()["confirmatory"]]
    b = [t["topic_id"] for t in split_bank()["confirmatory"]]
    assert a == b


def test_block_plan_structure():
    blocks = confirmatory_blocks()
    report = assert_block_plan(blocks)
    assert report["blocks"] == N_BLOCKS
    assert report["per_order"] == {TARGET_FIRST: 192, ADDED_FIRST: 192}
    for block in blocks:
        assert block.order == (TARGET_FIRST if block.index % 2 == 0
                               else ADDED_FIRST)
        assert block.wording_target == block.index % 4
        assert block.wording_added == (block.index // 4) % 4


def test_six_arm_structure_and_coverage():
    cells = confirmatory_cells(2, 8, REFS)
    assert len(cells) == N_BLOCKS * 6
    seen = {(c.block_id, c.arm) for c in cells}
    assert len(seen) == N_BLOCKS * 6
    for block in confirmatory_blocks():
        for arm in ARMS:
            assert (block.block_id, arm) in seen


def test_prompt_bytes_and_matched_arm_identity():
    blocks = confirmatory_blocks()
    for block in blocks[:8] + blocks[-8:]:
        assert_matched_arm_byte_identity(block, n=2, m=8, references=REFS)
        prompt = prompt_for_cell(block, "topic_alone", n=2, m=8,
                                 references=REFS)
        assert prompt == f"{block.question}\n\nAnswer:"
        target_alone = prompt_for_cell(block, "target_alone", n=2, m=8,
                                       references=REFS)
        assert target_alone.startswith(f"{block.question}\n\n1. ")
        assert target_alone.endswith("\n\nAnswer:")


def test_load_is_two_in_contrast_arms():
    block = confirmatory_blocks()[0]
    for arm in PRIMARY_ARMS:
        text = prompt_for_cell(block, arm, n=2, m=8, references=REFS)
        assert "1. " in text and "2. " in text and "3. " not in text


def test_greedy_plan_is_first_96_blocks_primary_arms():
    cells = greedy_cells(2, 8, REFS)
    assert len(cells) == 96 * 4
    assert {c.arm for c in cells} == set(PRIMARY_ARMS)
    assert len({c.block_id for c in cells}) == 96


def test_pilot_design():
    blocks = pilot_blocks()
    assert len(blocks) == 12
    assert {b.wording_target for b in blocks} == {0, 1, 2, 3}
    assert {b.wording_added for b in blocks} == {0, 1, 2, 3}
    assert sum(1 for b in blocks if b.order == TARGET_FIRST) == 6
    assert len(pilot_cells()) == 72
    areas = {b.topic_id.rsplit("-", 1)[0] for b in blocks}
    assert len(areas) == 12


def test_calibration_cells_and_wording_rotation():
    cells = calibration_cells()
    assert len(cells) == 96 * 19
    arms = {c.arm for c in cells}
    assert len(arms) == 19
    assert "solo:A:n=1" in arms and "solo:B:m=10" in arms and \
        "solo:C12" in arms


def test_parse_independence():
    assert assert_parse_independence()["parse_independent"]


def test_block_construction_rejects_wrong_topic_count():
    from dci1.protocol.constants import ProtocolError

    with pytest.raises(ProtocolError):
        build_blocks([{"topic_id": "x", "question": "Why?"}])
