"""T4. Topics, prompts, cells, allocation, row schema.

624 topics, the five-way split, disjointness, no v3 or pilot topic present,
sequestered inaccessibility; the 25-cell enumeration; both order variants in
every block; the explicit 96-of-384 wording count per order per cell type,
refusal of a structural zero, and qualification failure where a formula and an
assertion disagree; byte-level prompt equality between two composed cells
differing in one constituent; the row schema.
"""
from __future__ import annotations

from collections import Counter

import pytest

from dci1v4 import SYNTHETIC_STUDY_ID
from dci1v4.design.cells import (
    assert_allocation,
    block_cells,
    design_cells,
    registered_cell_types,
)
from dci1v4.design.prompts import assert_shared_constituent_identity, render
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.topics.bank import authoring_record, load_bank, validate_question
from dci1v4.topics.sequestered import (
    assert_no_materialisation,
    load_manifest,
    sequestered_ids,
)
from dci1v4.topics.split import (
    Block,
    confirmatory_blocks,
    pilot_blocks,
    split_hash,
    split_topics,
)

SLOT_MAP = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 2), "R2": ("RF5", 4),
            "R3": ("RF7", 6)}


@pytest.fixture(scope="module")
def split():
    return split_topics()


def test_the_bank_holds_528_released_of_624_authored():
    bank = load_bank()
    assert len(bank) == 528
    record = authoring_record(bank)
    assert record["authored_total"] == C.N_TOPICS == 624
    assert set(record["released_per_area"]) == set(C.SUBJECT_AREAS)
    assert all(v == 44 for v in record["released_per_area"].values())


def test_the_five_way_split_is_complete_and_disjoint(split):
    assert {k: len(v) for k, v in split.items()} == {
        "prescreen": 24, "solo": 96, "composed": 24, "confirmatory": 384}
    assert len(sequestered_ids()) == 96
    ids = [t["topic_id"] for part in split.values() for t in part]
    assert len(set(ids)) == len(ids) == 528
    assert not set(ids) & sequestered_ids()
    for area in C.SUBJECT_AREAS:
        counts = {name: sum(1 for t in members if t["area"] == area)
                  for name, members in split.items()}
        assert counts == {"prescreen": 2, "solo": 8, "composed": 2,
                          "confirmatory": 32}, area


def test_sequestered_text_is_inaccessible():
    manifest = load_manifest()
    assert len(manifest) == 96
    for entry in manifest:
        assert set(entry) == {"topic_id", "area", "sha256"}
        assert "question" not in entry
    assert_no_materialisation(load_bank())


def test_a_released_topic_colliding_with_a_sequestered_hash_fails_closed():
    manifest = load_manifest()
    with pytest.raises(ProtocolError):
        assert_no_materialisation([{"topic_id": manifest[0]["topic_id"],
                                    "question": "x"}])


def test_every_question_passes_the_four_authoring_rules():
    for topic in load_bank():
        validate_question(topic["topic_id"], topic["question"])


def test_the_split_hash_is_stable(split):
    assert split_hash(split) == split_hash(split_topics())


def test_the_registered_cell_set_is_five_solo_and_twenty_composed():
    types = registered_cell_types(SLOT_MAP)
    assert len(types) == C.N_CELLS_FULL == 25
    assert sum(1 for t in types if t.startswith("solo:")) == 5
    assert sum(1 for t in types if t.startswith("pair:")) == 20
    reduced = registered_cell_types({"A": ("A", 3), "B": ("B", 8)})
    assert len(reduced) == C.N_CELLS_REDUCED == 4


def test_every_block_carries_both_order_variants_of_every_pair(split):
    block = confirmatory_blocks(split)[0]
    cells = block_cells("confirmatory", block, SLOT_MAP, draws=4)
    composed = [c for c in cells if c.load == 2]
    assert len(composed) == 20
    per_pair = Counter(c.cell_type.rsplit(":", 1)[0] for c in composed)
    assert set(per_pair.values()) == {2}
    assert {c.order for c in composed} == set(C.ORDERS)


def test_one_composed_generation_yields_two_observations(split):
    block = confirmatory_blocks(split)[0]
    cells = block_cells("confirmatory", block, SLOT_MAP, draws=4)
    solo = [c for c in cells if c.load == 1]
    composed = [c for c in cells if c.load == 2]
    assert len(solo) == 5 and len(composed) == 20
    assert sum(len(c.constituents) for c in composed) == 40


def test_the_wording_allocation_is_96_of_384_per_slot_per_cell_type(split):
    blocks = confirmatory_blocks(split)
    cells = design_cells("confirmatory", blocks, SLOT_MAP, draws=4)
    report = assert_allocation(cells, blocks_expected=384, slot_map=SLOT_MAP)
    assert report["wording_count_per_cell_type"] == 96
    counts = report["wording_counts"]
    assert set(counts.values()) == {96}
    assert len(counts) == (5 * 4) + (20 * 2 * 4)


def test_the_allocation_assertion_refuses_a_structural_zero(split):
    blocks = confirmatory_blocks(split)
    cells = design_cells("confirmatory", blocks, SLOT_MAP, draws=4)
    kept = [c for c in cells
            if not (c.cell_type == "solo:A"
                    and c.constituents[0].wording_index == 3)]
    with pytest.raises(ProtocolError, match="structural zero"):
        assert_allocation(kept, blocks_expected=384, slot_map=SLOT_MAP)


def test_qualification_fails_where_a_formula_and_the_assertion_disagree(split):
    """A block plan whose wording formula skews the allocation is refused."""
    topics = split["confirmatory"][:8]
    skewed = [Block(block_id=f"b{i}", index=i, topic_id=t["topic_id"],
                    area=t["area"], question=t["question"], w1=0, w2=0)
              for i, t in enumerate(topics)]
    cells = design_cells("confirmatory", skewed, SLOT_MAP, draws=4)
    with pytest.raises(ProtocolError):
        assert_allocation(cells, blocks_expected=8, slot_map=SLOT_MAP)


def test_two_composed_prompts_sharing_a_constituent_differ_in_one_line(split):
    block = confirmatory_blocks(split)[0]
    cells = block_cells("confirmatory", block, SLOT_MAP, draws=4)
    ab = next(c for c in cells if c.cell_type == "pair:A+B:c1_first")
    ar1 = next(c for c in cells if c.cell_type == "pair:A+R1:c1_first")
    b_line = ab.constituent("B").text
    r1_line = ar1.constituent("R1").text
    assert ab.prompt.replace(b_line, "{OTHER}") == \
        ar1.prompt.replace(r1_line, "{OTHER}")
    lines_ab = ab.prompt.splitlines()
    lines_ar = ar1.prompt.splitlines()
    differing = [i for i, (x, y) in enumerate(zip(lines_ab, lines_ar))
                 if x != y]
    assert len(differing) == 1


def test_the_byte_identity_assertion_refuses_a_divergent_template():
    prompts = {"one": "Q\n\n1. A\n2. B\n\nAnswer:",
               "two": "Q!\n\n1. A\n2. C\n\nAnswer:"}
    lines = {"one": ("A", "B"), "two": ("A", "C")}
    with pytest.raises(ProtocolError):
        assert_shared_constituent_identity(prompts, lines)


def test_prompt_structure_is_question_numbered_list_answer():
    assert render("Q?", []) == "Q?\n\nAnswer:"
    assert render("Q?", ["one"]) == "Q?\n\n1. one\n\nAnswer:"
    assert render("Q?", ["one", "two"]) == "Q?\n\n1. one\n2. two\n\nAnswer:"
    with pytest.raises(ProtocolError):
        render("Q?", ["a", "b", "c"])


def test_the_row_schema_carries_the_whole_compliance_vector(split):
    from dci1v4.generation.cache import compliance_row

    block = confirmatory_blocks(split)[0]
    cells = block_cells("confirmatory", block, SLOT_MAP, draws=4)
    composed = next(c for c in cells if c.cell_type == "pair:A+B:c1_first")
    row = compliance_row(composed, "however " * 3, slot_map=SLOT_MAP,
                         finish_reason="stop")
    assert {s["slot"] for s in row["scores"]} == {"A", "B"}
    for score in row["scores"]:
        for field in ("kind", "severity", "position", "wording_index",
                      "passed", "graded", "non_vacuous", "vacuous_pass",
                      "processing_failure"):
            assert field in score
        assert score["role"] == "outcome"
    assert {s["slot"] for s in row["accidental"]} == {"R1", "R2", "R3"}
    for entry in row["accidental"]:
        assert entry["role"] == "accidental_compliance_diagnostic"
    for field in ("empty", "word_count", "truncated", "finish_reason",
                  "verifier_processing_failure", "accidental_s0",
                  "exact_count_alternatives", "verifier_source_hash"):
        assert field in row


def test_the_accidental_occurrence_count_is_recorded_where_A_is_absent(split):
    from dci1v4.generation.cache import compliance_row

    block = confirmatory_blocks(split)[0]
    cells = block_cells("confirmatory", block, SLOT_MAP, draws=4)
    solo_b = next(c for c in cells if c.cell_type == "solo:B")
    row = compliance_row(solo_b, "however however", slot_map=SLOT_MAP,
                         finish_reason="stop")
    assert row["accidental_s0"] == 2
    solo_a = next(c for c in cells if c.cell_type == "solo:A")
    assert compliance_row(solo_a, "however", slot_map=SLOT_MAP,
                          finish_reason="stop")["accidental_s0"] is None


def test_a_verifier_processing_failure_is_flagged_and_fails_closed(monkeypatch):
    from dci1v4.verifiers import statistics as stats
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import Constraint

    monkeypatch.setitem(stats.FAMILY_STATISTICS, "RF1",
                        lambda _t: (_ for _ in ()).throw(RuntimeError("x")))
    score = score_constraint(Constraint("RF1", 3), "text", truncated=False)
    assert score.processing_failure is True
    assert score.passed is False and score.graded == 0.0


def test_the_pilot_uses_twelve_topics_and_the_same_allocation(split):
    blocks = pilot_blocks(split)
    assert len(blocks) == C.PILOT_TOPICS == 12
    assert len({b.area for b in blocks}) == 12
    cells = design_cells("pilot", blocks, SLOT_MAP, draws=C.PILOT_DRAWS)
    assert len(cells) == 12 * 25
    assert sum(c.draws for c in cells) == 1200
