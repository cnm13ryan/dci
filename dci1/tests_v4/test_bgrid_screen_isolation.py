"""The B-grid screen must not be able to touch the registered study.

The extension rungs m = 11 and m = 12 are the risk this file exists for: a
screen that widens a registered grid is one careless import away from widening
it for the study. These pin that the registered grid still refuses them, that
the screen's own renderer and scorer are the registered ones on every
registered rung, and that nothing here writes into a registered tree.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.engine.context import DCI1_ROOT
from dci1v4.engine.guards import assert_registered_v4_input
from dci1v4.errors import ProtocolError, ProvenanceGuardError
from dci1v4.protocol import constants as C
from dci1v4.protocol import seeds as v4seeds
from dci1v4.protocol.wordings import focal_wordings
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          Constraint, TARGET_GRID)
from dci1v4.verifiers.wording_suite import TWENTY_RESPONSES

from bgrid_screen_v4 import focal
from bgrid_screen_v4 import plan as pl
from fs_screen_v4 import plan as fspl


# ------------------------------------------------------------- isolation
def test_screen_evidence_is_refused_as_v4_analysis_input():
    from dci1v4.engine.context import registered_context
    context = registered_context()
    path = DCI1_ROOT / "evidence" / "bgrid-screen-v4" / "any" / "cache.jsonl"
    with pytest.raises(ProvenanceGuardError):
        assert_registered_v4_input(context, path)


def test_screen_writes_only_under_its_own_roots():
    import bgrid_screen_v4.analysis as analysis
    import bgrid_screen_v4.run as run
    forbidden = ("evidence/dci1-v4", "evidence/dci1-v3", "evidence/br-pilot-v4",
                 "evidence/fs-screen-v4", "durable_root/dci1-v4")
    for module in (run, analysis):
        for line in Path(module.__file__).read_text().splitlines():
            if "write" not in line.lower():
                continue
            assert not any(f in line for f in forbidden), (
                f"{module.__name__} writes into another tree: {line.strip()}")


def test_seed_root_is_distinct_from_every_other_stream():
    assert pl.SCREEN_ROOT_SEED != fspl.SCREEN_ROOT_SEED
    assert pl.DOMAIN_SCREEN_GENERATION != fspl.DOMAIN_SCREEN_GENERATION
    assert pl.SCREEN_ROOT_SEED not in {
        v4seeds.GENERATION_ROOT_SEED, v4seeds.BOOTSTRAP_ROOT_SEED,
        v4seeds.TOPIC_SPLIT_SEED, v4seeds.GATE1_SAMPLE_SEED}


def test_the_same_prompt_gets_a_different_seed_in_each_screen():
    a = pl.screen_seed("m", "deadbeef", 0)
    b = fspl.screen_seed("m", "deadbeef", 0)
    assert a != b


# ------------------------------------------ the registered grid still refuses
def test_registered_constraint_still_refuses_the_extension_rungs():
    for m in focal.EXTENSION:
        with pytest.raises(Exception):
            Constraint("B", m)
        with pytest.raises(ProtocolError):
            focal_wordings(m)


def test_registered_focal_grid_is_unchanged():
    assert FOCAL_GRID == (7, 8, 9, 10)
    assert tuple(TARGET_GRID) == tuple(range(1, 9))
    assert C.FOCAL_BAND == (0.60, 0.95) and C.FOCAL_AIM == 0.80
    assert C.NON_VACUITY_MIN_WORDS == 20
    assert C.REFERENCE_CALIPER == 0.10
    assert C.REFERENCE_VACUITY_MAX == 0.10
    assert sum(len(v) for v in REFERENCE_LADDERS.values()) == 94


@pytest.mark.skipif(not (DCI1_ROOT / "evidence" / "dci1-v4" / "registration"
                         / "manifest.json").exists(),
                    reason="no stored evidence tree")
def test_verifier_hash_still_matches_the_signed_manifest():
    manifest = json.loads(
        (DCI1_ROOT / "evidence" / "dci1-v4" / "registration"
         / "manifest.json").read_text())
    assert (verifier_source_hash()
            == manifest["payload"]["instruments"]["canonical_verifier_hash"]), (
        "the canonical verifier hash moved; the screen must not touch verifiers")


# ------------------------------------------- the extension IS the registered B
def test_screen_wordings_equal_the_registered_ones_on_registered_rungs():
    result = focal.assert_wordings_match()
    assert result["wordings_identical"] is True
    for m in FOCAL_GRID:
        assert focal.screen_wordings(m) == focal_wordings(m)


def test_screen_scorer_agrees_with_the_registered_verifier():
    result = focal.assert_scoring_matches(TWENTY_RESPONSES)
    assert result["agreement"] == 1.0
    assert result["verdicts_checked"] == len(FOCAL_GRID) * 20 * 2


def test_b_is_monotone_in_m_across_the_screen_grid():
    focal.assert_monotone_in_m(TWENTY_RESPONSES)
    assert focal.screen_score(12, "considerable", truncated=False)["passed"]
    assert not focal.screen_score(12, "extraordinary", truncated=False)["passed"]


def test_screen_grid_is_not_extended_past_twelve():
    assert focal.GRID_MAX == 12
    with pytest.raises(ProtocolError):
        focal.screen_wordings(13)
    with pytest.raises(ProtocolError):
        focal.screen_score(13, "text", truncated=False)


def test_extension_wordings_are_severity_invariant_in_word_count():
    """Numerals are not alphabetic runs, so every rung's wording has the same
    word count as the registered ones -- the §7.3 property, extended."""
    from dci1v4.protocol.wordings import wording_word_count
    for index in range(4):
        counts = {wording_word_count(focal.screen_wording(m, index))
                  for m in focal.SCREEN_FOCAL_GRID}
        assert len(counts) == 1, (index, counts)


# ------------------------------------------------------------- the cell plan
def test_stem_is_byte_identical_to_the_screened_one():
    assert pl.STEM_SENTENCE == fspl.STEM_SENTENCE
    assert pl.assert_stem_identical()["stem_sentence"] == \
        "Answer in 60 to 120 words."


def test_stem_is_inert_never_scored_and_never_counted_as_load():
    """The stem is background: it appears in the prompt above the numbered
    list, is never a scored constraint, and never enters a compliance vector."""
    from dci1v4.topics.split import split_topics
    topics = split_topics()["prescreen"]
    cells = pl.build_cells(topics)
    for cell in cells:
        load = 1 + (1 if cell.companion else 0)
        assert len(cell.cell_id.split("+")) == load
        if cell.stem == "floored":
            assert pl.STEM_SENTENCE in cell.prompt
            head, _, tail = cell.prompt.partition(pl.STEM_SENTENCE)
            assert "1." not in head and "1." in tail
        else:
            assert pl.STEM_SENTENCE not in cell.prompt
    kinds = {s for c in cells for s in
             ([c.kind] + ([c.companion[0]] if c.companion else []))}
    assert kinds == {"A", "B"}


def test_cell_plan_is_exactly_what_the_protocol_declares():
    from dci1v4.topics.split import split_topics
    topics = split_topics()["prescreen"]
    cells = pl.build_cells(topics)
    summary = pl.plan_summary(cells)
    assert summary["total_generations"] == 24 * (6 + 2 + 8 + 6)
    assert summary["distinct_prompts"] == summary["total_generations"]
    assert summary["by_cell_class"] == {
        "b_solo:floored": 24 * 6, "b_solo:current": 24 * 2,
        "a_solo:floored": 24 * 8, "fixture:floored": 24 * 6}


def test_screen_uses_only_the_prescreen_topics():
    from dci1v4.topics.split import split_topics
    split = split_topics()
    prescreen = {t["topic_id"] for t in split["prescreen"]}
    cells = pl.build_cells(split["prescreen"])
    assert {c.topic_id for c in cells} == prescreen
    for other in ("solo", "composed", "confirmatory"):
        assert not prescreen & {t["topic_id"] for t in split[other]}
