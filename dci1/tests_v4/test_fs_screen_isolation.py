"""The FORM x STEM screen must not be able to touch the registered study.

These pin the properties that make the screen safe to run beside a
preregistered protocol: it writes only its own tree, it changes no registered
value, its seeds cannot collide, and its stem is inert.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.engine.context import DCI1_ROOT
from dci1v4.engine.guards import assert_registered_v4_input
from dci1v4.errors import (InstrumentError, ProtocolError,
                           ProvenanceGuardError)
from dci1v4.protocol import constants as C
from dci1v4.protocol import seeds as v4seeds
from dci1v4.verifiers import verifier_source_hash
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          Constraint,
                                          TARGET_GRID)

from fs_screen_v4 import constraints as cc
from fs_screen_v4 import plan as pl
from fs_screen_v4 import suite, witnesses
from fs_screen_v4.wordings import (assert_caliper_feasible,
                                   assert_rule_vocabulary,
                                   assert_severity_invariance)


# ------------------------------------------------------------- isolation
def test_screen_evidence_is_refused_as_v4_analysis_input():
    """The positive-admission guard must refuse the screen tree."""
    from dci1v4.engine.context import registered_context
    context = registered_context()
    path = DCI1_ROOT / "evidence" / "fs-screen-v4" / "any" / "cache.jsonl"
    with pytest.raises(ProvenanceGuardError):
        assert_registered_v4_input(context, path)


def test_screen_writes_only_under_its_own_roots():
    """No screen module may name a registered evidence path as a write target."""
    import fs_screen_v4.analysis as analysis
    import fs_screen_v4.run as run
    forbidden = ("evidence/dci1-v4", "evidence/dci1-v3", "evidence/br-pilot-v4",
                 "durable_root/dci1-v4")
    for module in (run, analysis):
        source = Path(module.__file__).read_text()
        for line in source.splitlines():
            if "write" not in line.lower():
                continue
            assert not any(f in line for f in forbidden), (
                f"{module.__name__} appears to write into a registered tree: "
                f"{line.strip()}")


def test_screen_seeds_cannot_collide_with_registered_streams():
    assert pl.SCREEN_ROOT_SEED not in {
        v4seeds.GENERATION_ROOT_SEED, v4seeds.BOOTSTRAP_ROOT_SEED,
        v4seeds.TOPIC_SPLIT_SEED, v4seeds.GATE1_SAMPLE_SEED,
        v4seeds.AUTORATER_SPLIT_SEED, v4seeds.ADVERSARIAL_SEED}
    assert pl.DOMAIN_SCREEN_GENERATION not in v4seeds.V4_DOMAINS
    # Same model, same prompt, same draw -> different seed by domain alone.
    screen = pl.screen_seed("m", "0" * 64, 0)
    registered = v4seeds.generation_seed(
        v4seeds.GENERATION_ROOT_SEED, pl.STAGE, "m", "0" * 64, 0)
    assert screen != registered


def test_no_registered_value_was_changed():
    """The frozen screen protocol records these; a drift here is a defect."""
    assert C.REFERENCE_CALIPER == 0.10
    assert C.REFERENCE_VACUITY_MAX == 0.10
    assert C.NON_VACUITY_MIN_WORDS == 20
    assert TARGET_GRID == (1, 2, 3, 4, 5, 6, 7, 8)
    assert FOCAL_GRID == (7, 8, 9, 10)
    assert sum(len(v) for v in REFERENCE_LADDERS.values()) == 94
    manifest_path = (DCI1_ROOT / "evidence" / "dci1-v4" / "registration"
                     / "manifest.json")
    if not manifest_path.exists():
        pytest.skip("no stored evidence tree")
    manifest = json.loads(manifest_path.read_text())
    assert (verifier_source_hash()
            == manifest["payload"]["instruments"]["canonical_verifier_hash"]), (
        "the canonical verifier hash moved; the screen must not touch verifiers")


def test_candidate_ids_never_shadow_registered_families():
    assert not set(cc.CANDIDATE_IDS) & set(REFERENCE_LADDERS)


# ---------------------------------------------------------------- the FORM
def test_candidates_break_prefix_closure():
    """The defect the screen exists to test: the empty string is a perfect
    score on the registered pool and must be a zero on every candidate."""
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import Constraint

    registered = [(f, q) for f in REFERENCE_LADDERS for q in REFERENCE_LADDERS[f]]
    assert all(score_constraint(Constraint(f, q), "", truncated=False).passed
               for f, q in registered), "registered pool changed"
    assert not any(cc.passes(k, q, "") for k, q in cc.all_severities())


def test_rf2_is_excluded_and_the_reason_is_measured():
    assert "RF2" in cc.EXCLUDED_FROM_CANDIDATES
    assert not any(k.endswith("2") for k in cc.CANDIDATE_IDS)
    proof = witnesses.assert_rf2_conflict()
    assert proof["all_listed_short_words_are_within_7"]
    assert proof["all_listed_long_words_exceed_7"]


def test_candidate_wording_discipline():
    assert_severity_invariance()
    assert_caliper_feasible()
    assert_rule_vocabulary()
    assert suite.assert_wording_equivalence() == 48 * 20
    suite.assert_parse_independence()


def test_candidate_witnesses_are_certified():
    result = witnesses.verify_all()
    assert result["candidate_severities"] == 48
    assert result["compositions_certified"] == 48 * (len(TARGET_GRID)
                                                     + len(FOCAL_GRID))



def test_the_witness_constructor_refuses_pairings_it_cannot_certify():
    """Out of its envelope this builder reported a construction failure as an
    entailment claim -- ``CR6@7 appears to entail RF3@4`` -- because its
    non-entailment branch fails the companion by appending a long word, which
    moves B's statistic and no reference family's. Found by dci-79 while
    building the matrix screen's witness check. The envelope is now enforced.
    """
    assert witnesses.CERTIFIABLE_OTHERS == ("A", "B")
    for other in (Constraint("RF3", 4), Constraint("RF1", 2)):
        with pytest.raises(ProtocolError) as excinfo:
            witnesses.verify_candidate_pair("CR6", 7, other)
        message = str(excinfo.value)
        assert "outside its envelope" in message
        assert "appears to entail" not in message.replace(
            "'<candidate> appears to entail", "")
    # The A and B pairings the screen actually certified are untouched.
    witnesses.verify_candidate_pair("CR6", 7, Constraint("A", TARGET_GRID[0]))
    witnesses.verify_candidate_pair("CR6", 7, Constraint("B", FOCAL_GRID[0]))


def test_candidate_x_candidate_witnesses_have_no_constructor():
    """Amendment B's cost list omitted this: an enlarged pool owes 7.3
    witnesses for candidate x reference and candidate x candidate pairs, and
    nothing in this screen constructs one.
    """
    other = Constraint("A", TARGET_GRID[0])
    assert "CL1" not in witnesses.CERTIFIABLE_OTHERS
    # joint_witness takes a registered Constraint; a candidate cannot even be
    # expressed as one, which is the shape of the missing work.
    with pytest.raises(InstrumentError):
        Constraint("CL1", 3)
    witnesses.assert_in_envelope(other)  # the registered companion is fine

# ---------------------------------------------------------------- the STEM
def test_stem_appears_in_every_floored_cell_and_no_current_cell():
    from dci1v4.topics.split import split_topics
    topics = split_topics()["prescreen"][:2]
    cells = pl.build_cells(topics, ["RF1:1"])
    floored = [c for c in cells if c.stem == "floored"]
    current = [c for c in cells if c.stem == "current"]
    assert floored and current
    assert all(pl.STEM_SENTENCE in c.prompt for c in floored)
    assert all(pl.STEM_SENTENCE not in c.prompt for c in current)


def test_stem_sits_between_question_and_constraint_list():
    prompt = pl.render("Q?", ["C one.", "C two."], "floored")
    assert prompt.index("Q?") < prompt.index(pl.STEM_SENTENCE)
    assert prompt.index(pl.STEM_SENTENCE) < prompt.index("1. C one.")


def test_stem_is_never_scored_and_never_counts_toward_load():
    """A floored prompt carrying one constraint is a load-1 prompt."""
    from fs_screen_v4.run import score_row
    from dci1v4.topics.split import split_topics
    topics = split_topics()["prescreen"][:1]
    cells = pl.build_cells(topics, ["RF1:1"])
    solo = next(c for c in cells
                if c.stem == "floored" and c.companion is None)
    scored = score_row(solo, "word " * 80, truncated=False)
    assert len(scored["scores"]) == 1, "the stem must not enter the vector"
    assert {s["kind"] for s in scored["scores"]} == {solo.kind}
    pair = next(c for c in cells if c.companion is not None)
    assert len(score_row(pair, "word " * 80,
                         truncated=False)["scores"]) == 2


def test_stem_satisfaction_is_a_diagnostic_band_not_a_predicate_on_passing():
    assert pl.stem_satisfied(60) and pl.stem_satisfied(120)
    assert not pl.stem_satisfied(59) and not pl.stem_satisfied(121)
