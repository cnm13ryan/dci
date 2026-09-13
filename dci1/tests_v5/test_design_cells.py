"""H. §8.1's arm-derived cell plan, for every admissible arm set."""
from __future__ import annotations

import itertools

import pytest

from dci1v4.errors import ProtocolError
from dci1v5.design import cells
from dci1v5.protocol import constants as C

#: §8.1's own table, transcribed so the derivation is checked against the
#: preregistration rather than against itself.
REGISTERED_COUNTS = {
    ("base",): 5,
    ("base", "core"): 26,
    ("base", "core", "spectrum"): 44,
    ("base", "core", "spectrum", "nearform", "class"): 56,
    ("base", "core", "nearform", "class"): 38,
    ("base", "core", "class"): 29,
    ("base", "nearform", "class"): 17,
    ("base", "class"): 8,
}


@pytest.mark.parametrize("arms,expected", sorted(REGISTERED_COUNTS.items()))
def test_the_derived_count_matches_the_registered_table(arms, expected):
    assert cells.n_cells_for(arms) == expected
    assert len(cells.cell_types(arms)) == expected


def test_every_admissible_arm_combination_builds():
    optional = [a for a in C.OPTIONAL_ARMS]
    built = 0
    for size in range(len(optional) + 1):
        for combination in itertools.combinations(optional, size):
            if "spectrum" in combination and "core" not in combination:
                with pytest.raises(ProtocolError):
                    cells.normalise_arms(combination)
                continue
            types = cells.cell_types(combination)
            assert len(types) == cells.n_cells_for(combination)
            built += 1
    assert built == 12       # 16 subsets, four of which need the core arm


def test_the_spectrum_cannot_be_admitted_without_the_core_arm():
    with pytest.raises(ProtocolError):
        cells.normalise_arms(["spectrum"])
    with pytest.raises(ProtocolError):
        cells.arms_from_identification(core_identified=False,
                                       spectrum_identified=True,
                                       near_form_identified=False,
                                       class_identified=False)


def test_the_base_arm_is_never_optional():
    assert cells.normalise_arms([]) == ("base",)
    assert "base" in cells.normalise_arms(["core"])


def test_the_full_design_is_56_cells_and_688128_generations():
    full = cells.n_cells_for(C.ARMS)
    assert full == 56
    assert full * C.N_BLOCKS * C.M_DRAWS == 172_032
    assert full * C.N_BLOCKS * C.M_DRAWS * 4 == 688_128


def test_every_composed_cell_runs_both_orders():
    types = cells.cell_types(C.ARMS)
    composed = [t for t in types if t.arm == "composed"]
    pairs = {frozenset(t.slots) for t in composed}
    for pair in pairs:
        variants = [t for t in composed if frozenset(t.slots) == pair]
        assert len(variants) == 2
        assert {v.slots for v in variants} == {
            tuple(sorted(pair, key=cells.slot_order_key)),
            tuple(reversed(sorted(pair, key=cells.slot_order_key)))}


def test_the_linear_arms_pair_with_b_alone():
    types = cells.cell_types(C.ARMS)
    linear = set(C.SPECTRUM_SLOTS + C.NEAR_FORM_SLOTS + (C.CLASS_SLOT,))
    for cell in types:
        if cell.arm != "composed":
            continue
        touching = set(cell.slots) & linear
        if touching:
            assert set(cell.slots) - touching == {"B"}, cell.cell_id


def test_a_configuration_is_the_position_of_the_outcome():
    types = cells.cell_types(["core"])
    ab = next(t for t in types if t.slots == ("A", "B"))
    ba = next(t for t in types if t.slots == ("B", "A"))
    assert ab.configuration_of("A") == C.OUTCOME_FIRST
    assert ab.configuration_of("B") == C.OUTCOME_SECOND
    assert ba.configuration_of("B") == C.OUTCOME_FIRST
    assert ba.configuration_of("A") == C.OUTCOME_SECOND


def test_no_variant_exemptions_table_exists():
    """§18.1's rule replaced v4r4's per-variant patch."""
    assert not hasattr(cells, "VARIANT_EXEMPTIONS")


def test_the_allocation_assertion_catches_a_wrong_arm_set():
    class _Block:
        def __init__(self, index):
            self.index = index
            self.block_id = f"b{index:03d}"
            self.topic_id = f"t{index:03d}"

    blocks = [_Block(i) for i in range(8)]
    plan = cells.design_cells(blocks, ["core", "class"],
                              assert_allocation_over=8)
    assert len(plan) == 8 * 29
    with pytest.raises(ProtocolError):
        cells.assert_allocation(plan, ["core"], blocks_expected=8)


def test_wording_and_order_are_orthogonal_by_construction():
    assert cells.wording_indices(0, 2) == (0, 0)
    assert cells.wording_indices(5, 2) == (1, 2)
    assert cells.wording_indices(7, 1) == (3,)
    assert cells.wording_indices(3, 0) == ()
