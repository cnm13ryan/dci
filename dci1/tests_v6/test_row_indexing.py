"""§9.1's verdicts, indexed. The defects here only appear on produced rows.

Every one of these is a regression test for something the synthetic lifecycle
found the first time a stage built an ``ObservationTable`` from rows the
production scorer wrote. Before that, every table in the suite was built from
a fixture whose rows carried exactly the stated constituents --- and the
production rows carry a verdict for **every** registered instance, present or
absent, which is the whole point of §9.1.
"""
from __future__ import annotations

import pytest

from dci1v4.errors import IntegrityError

from dci1v6.analysis.observations import ObservationTable, build_observations
from dci1v6.protocol import constants as C
from dci1v6.run.execute import fake_backend, generate_and_score, prompt_cell
from dci1v6.verifiers.constraints import Constraint

MODEL = "gemma-3n-e2b-it"
SLOT_MAP = {"A": Constraint("A", 4), "B": Constraint("B", 9),
            "R1": Constraint("MK1", 3), "R2": Constraint("MK2", 3)}


class _Cell:
    """The minimum a design cell has to be to be rendered."""

    def __init__(self, cell_id, arm, slots, draws=2, block="block-0000"):
        self.cell_id, self.arm, self.slots = cell_id, arm, tuple(slots)
        self.draws, self.block_id = draws, block
        self.topic_id, self.area = "t-000", "science"
        self.wording_by_slot = {s: 0 for s in slots}


TOPIC = {"topic_id": "t-000", "area": "science",
         "question": "What makes a bridge stable?"}


def _rows(tmp_path, cells):
    prompts = [prompt_cell(c, TOPIC, slot_map=SLOT_MAP,
                           topic_split="prescreen") for c in cells]

    def responder(row):
        return ("However however however however. Short words hold here. "
                "A calm reply that stays inside the stem band and says "
                "little of note at all, plainly and briefly. " * 3)

    return generate_and_score(
        MODEL, prompts, stage=C.STAGE_GATE0, cap=256, device=0,
        run_dir=tmp_path / "run", instances=tuple(SLOT_MAP.values()),
        slot_map=SLOT_MAP, study_id="dci1v6-synthetic",
        generate=fake_backend(responder))


def test_an_absent_verdict_carries_the_slot_it_is_bound_to(tmp_path):
    """§13.6 reads kappa(R|B) by slot, so `slot: null` made it unreadable."""
    rows = _rows(tmp_path, [_Cell("solo:B", "solo", ("B",))])
    scores = rows[0]["scores"]
    assert len(scores) == len(SLOT_MAP)
    absent = [s for s in scores if not s["present"]]
    assert absent, "the B-solo cell scores every instance it did not state"
    assert all(s["slot"] for s in absent), \
        [s for s in absent if not s["slot"]]
    assert {s["slot"] for s in scores} == set(SLOT_MAP)


def test_the_kappa_index_finds_the_b_solo_verdict(tmp_path):
    rows = _rows(tmp_path, [_Cell("solo:B", "solo", ("B",))])
    table = ObservationTable(build_observations(rows, m_draws=2))
    assert table.has_kappa_under_b("R1")
    observation = table.kappa_under_b("block-0000", "R1")
    assert observation.present is False


def test_the_load_zero_cell_is_the_chance_index_not_the_kappa_index(tmp_path):
    """§25 and §9.1 both call it absent; the arm is what separates them.

    Testing `present` before the arm sent every load-0 verdict into the kappa
    index, where they collided on one key --- and `chance()` could then never
    find the rate the difficulty coordinate is built from.
    """
    rows = _rows(tmp_path, [_Cell("unconstrained", "unconstrained", ())])
    table = ObservationTable(build_observations(rows, m_draws=2))
    for slot in SLOT_MAP:
        assert table.has_chance(slot)
        assert table.chance("block-0000", slot).arm == "unconstrained"


def test_a_composed_cells_companion_is_its_other_stated_constituent(tmp_path):
    """Not the next label in the score list, which names every instrument."""
    rows = _rows(tmp_path, [_Cell("pair:A+R1", "composed", ("A", "R1"))])
    observations = build_observations(rows, m_draws=2)
    composed = {o.outcome_slot: o for o in observations if o.present}
    assert composed["A"].companion_slot == "R1"
    assert composed["R1"].companion_slot == "A"
    assert composed["A"].configuration == C.OUTCOME_FIRST
    assert composed["R1"].configuration == C.OUTCOME_SECOND
    # The instruments the cell did not state are absent verdicts, not
    # companions.
    absent = [o for o in observations if not o.present]
    assert {o.outcome_slot for o in absent} == {"B", "R2"}
    assert all(o.companion_slot is None for o in absent)


def test_two_composed_cells_do_not_collide_on_one_index_key(tmp_path):
    table = ObservationTable(build_observations(
        _rows(tmp_path / "a", [_Cell("pair:A+R1", "composed", ("A", "R1"))])
        + _rows(tmp_path / "b", [_Cell("pair:A+R2", "composed", ("A", "R2"))]),
        m_draws=2))
    assert table.companions_of("A") == ("R1", "R2")


def test_the_table_still_refuses_a_genuine_duplicate(tmp_path):
    rows = _rows(tmp_path, [_Cell("pair:A+R1", "composed", ("A", "R1"))])
    observations = build_observations(rows, m_draws=2)
    with pytest.raises(IntegrityError, match="duplicate"):
        ObservationTable(observations + observations)
