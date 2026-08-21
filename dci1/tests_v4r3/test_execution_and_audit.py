"""The execution layer, the topic audit, and the isolation boundary.

Mapped to the brief's required failure modes: 13 (spectrum orders missing or
unbalanced), 14 (registered M draws discarded or selected), 15 (reserved
topics leak into development), 17 (a new scientific field is absent from the
freeze), 18 (post-freeze scientific mutation), 19 (v4r3 evidence enters v4r2
estimators), 20 (historical artifact readers break).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v4r3 import EVIDENCE_DIRNAME, STUDY_ID
from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import audit


# ------------------------------------------------------------ the stem
def test_every_rendered_prompt_carries_the_answer_length_sentence_once():
    from dci1v4r3.design.prompts import assert_stem_present, render
    for lines in ([], ["one"], ["one", "two"]):
        prompt = render("Why is the sky blue?", lines)
        assert_stem_present(prompt)
        assert prompt.count(C.STEM_SENTENCE) == 1
        assert prompt.endswith("Answer:")
    with pytest.raises(ProtocolError):
        render("q", ["a", "b", "c"])


def test_a_prompt_without_the_stem_is_refused_rather_than_generated():
    from dci1v4r3.design.prompts import assert_stem_present
    with pytest.raises(ProtocolError, match="answer-length sentence"):
        assert_stem_present("Why is the sky blue?\n\nAnswer:")


# ------------------------------------------------------ required failure 14
def test_every_registered_draw_gets_a_row_and_none_is_selected():
    from dci1v4r3.run.execute import Cell, design_rows
    from dci1v4r3.design.prompts import prompt_hash, render
    prompt = render("q", ["one"])
    cell = Cell(cell_id="c", arm="a", topic_id="t", area="history",
                prompt=prompt, prompt_hash=prompt_hash(prompt), present=(),
                wording_indices=())
    rows = design_rows([cell], stage="s", model_id="m", draws=C.M_DRAWS)
    assert len(rows) == C.M_DRAWS
    assert sorted(r["draw_index"] for r in rows) == list(range(C.M_DRAWS))
    assert len({r["scientific_seed"] for r in rows}) == C.M_DRAWS


def test_the_seed_stream_separates_v4r3_from_every_earlier_study():
    from dci1v4.protocol import seeds as v4_seeds
    from dci1v4r3.protocol import seeds as v4r3_seeds
    assert not set(v4r3_seeds.V4R3_DOMAINS) & set(v4_seeds.V4_DOMAINS)
    assert v4r3_seeds.GENERATION_ROOT_SEED != v4_seeds.GENERATION_ROOT_SEED
    # ...except the topic-split seed, which is carried DELIBERATELY so that
    # v4r3 and v4r2 name the same development topics.
    assert v4r3_seeds.CARRIED_TOPIC_SPLIT_SEED == v4_seeds.TOPIC_SPLIT_SEED


def test_the_same_prompt_in_two_stages_never_reuses_a_seed():
    from dci1v4r3.protocol.seeds import generation_seed
    a = generation_seed("v4r3-ladder-screen", "m", "hash", 0)
    b = generation_seed("v4r3-solo-calibration", "m", "hash", 0)
    assert a != b


# ------------------------------------------------------ required failure 15
def test_the_audit_refuses_a_stage_that_touched_a_reserved_set():
    rows = [{"topic_id": t["topic_id"], "stage": "v4r3-ladder-screen"}
            for t in __import__("dci1v4r3.topics", fromlist=["x"])
            .split_topics()["composed"][:3]]
    report = audit.audit_rows(rows)
    with pytest.raises(ProtocolError, match="reserved sets are not unspent"):
        audit.assert_reserved_sets_unspent(report)


def test_the_audit_refuses_a_stage_label_it_does_not_recognise():
    rows = [{"topic_id": t["topic_id"], "stage": "some-other-run"}
            for t in __import__("dci1v4r3.topics", fromlist=["x"])
            .split_topics()["prescreen"][:3]]
    report = audit.audit_rows(rows)
    assert report["unresolved_stage_labels"] == ["some-other-run"]
    with pytest.raises(ProtocolError, match="does not recognise"):
        audit.assert_reserved_sets_unspent(report)


def test_a_run_suffix_does_not_hide_a_stage_from_the_audit():
    assert audit.resolve_stage("v4r3-ladder-screen-r2") == C.STAGE_REGIME
    assert audit.resolve_stage("v4r3-confirmatory") == C.STAGE_CONFIRMATORY
    rows = [{"topic_id": t["topic_id"], "stage": "v4r3-confirmatory"}
            for t in __import__("dci1v4r3.topics", fromlist=["x"])
            .split_topics()["prescreen"][:2]]
    with pytest.raises(ProtocolError, match="may not touch"):
        audit.assert_reserved_sets_unspent(audit.audit_rows(rows))


def test_the_generated_v4r3_rows_on_disk_spend_no_reserved_topic():
    root = Path(__file__).resolve().parents[1] / "evidence" / EVIDENCE_DIRNAME
    if not root.exists():                                   # pragma: no cover
        pytest.skip("no v4r3 evidence in this checkout")
    report = audit.assert_reserved_sets_unspent(
        audit.audit_evidence_tree(root))
    assert report["reserved_sets_unspent"]
    for tally in report["by_stage"].values():
        assert set(tally) <= set(C.DEVELOPMENT_TOPIC_SETS)


# ------------------------------------------------------ required failure 17
def test_every_registered_degree_of_freedom_is_a_freeze_field():
    from dci1v4r3.stages.freeze import FREEZE_FIELDS
    for field in ("candidate_family_vocabulary", "candidate_declared_range",
                  "measured_vocabulary", "expansion_rule",
                  "coverage_criterion", "coverage_report", "lexical_rule",
                  "class_match_caliper", "difficulty_coordinate",
                  "spectrum_selection_rule", "bootstrap_refit_algorithm"):
        assert field in FREEZE_FIELDS, field


def test_the_freeze_refuses_a_field_its_list_does_not_carry():
    from dci1v4r3.stages.freeze import build_freeze_record
    with pytest.raises(ProtocolError, match="field list is closed"):
        build_freeze_record(a_new_scientific_knob=1)


# --------------------------------------------- required failures 19 and 20
def test_v4r3_evidence_cannot_enter_a_v4r2_estimator():
    from dci1v4.engine.guards import assert_admissible_manifest
    with pytest.raises(Exception):
        assert_admissible_manifest({"study_id": STUDY_ID})
    assert not STUDY_ID.startswith("dci1-v4")


def test_the_v4r3_context_refuses_a_root_inside_another_study():
    from dci1v4r3.engine.context import StudyContext, foreign_roots
    roots = foreign_roots()
    assert roots, "the isolation check has nothing to check against"
    with pytest.raises(ProtocolError, match="overlaps the historical tree"):
        StudyContext(namespace="registered", study_id=STUDY_ID,
                     repo_root=Path("/"),
                     evidence_root=roots[0].parent / roots[0].name,
                     durable_root=Path("/tmp"))


def test_the_historical_artifact_readers_still_work():
    """v4r3 must not break a reader of an earlier study's evidence."""
    from dci1v4.topics.split import split_topics as v4_split
    from dci1v4.verifiers import verifier_source_hash as v4_hash
    from dci1v4r3.verifiers import verifier_source_hash as v4r3_hash
    assert {k: len(v) for k, v in v4_split().items()} == {
        "prescreen": 24, "solo": 96, "composed": 24, "confirmatory": 384}
    assert v4_hash() != v4r3_hash()


def test_the_v4r3_topic_split_is_v4r2s_and_says_so():
    from dci1v4.topics.split import split_topics as v4_split
    from dci1v4r3.topics import split_topics
    ours, theirs = split_topics(), v4_split()
    for name in ("prescreen", "solo", "composed", "confirmatory"):
        assert ([t["topic_id"] for t in ours[name]]
                == [t["topic_id"] for t in theirs[name]])


# --------------------------------------------------------- the resume path
def test_a_resume_reuses_generations_only_on_an_exact_design_identity(tmp_path):
    from dci1v4r3.run.execute import _reusable_rows
    wanted = [{"row_id": "r0", "prompt_hash": "h0", "scientific_seed": 1},
              {"row_id": "r1", "prompt_hash": "h1", "scientific_seed": 2}]
    (tmp_path / "design.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in wanted))
    (tmp_path / "rows.jsonl").write_text(
        "".join(json.dumps({"row_id": r["row_id"], "final_answer": "x"}) + "\n"
                for r in wanted))
    assert _reusable_rows(tmp_path, wanted) is not None

    moved = [dict(wanted[0], scientific_seed=99), wanted[1]]
    assert _reusable_rows(tmp_path, moved) is None
    reprompted = [dict(wanted[0], prompt_hash="other"), wanted[1]]
    assert _reusable_rows(tmp_path, reprompted) is None
    assert _reusable_rows(tmp_path, wanted[:1]) is None


# ---------------------------------------------------- the registration guard
def test_the_manifest_refuses_a_model_adaptive_value():
    from dci1v4r3.stages.registration import assert_no_model_adaptive_values
    with pytest.raises(ProtocolError, match="model-adaptive"):
        assert_no_model_adaptive_values({"selection_rules": {"n_star": 3}})
    with pytest.raises(ProtocolError, match="model-adaptive"):
        assert_no_model_adaptive_values(
            {"candidate_library": {"measured_vocabulary": ["RF1:3"]}})


def test_the_manifest_binds_the_whole_declared_library():
    from dci1v4r3.engine.context import registered_context
    from dci1v4r3.stages.registration import build_manifest
    from dci1v4r3.verifiers.constraints import FAMILIES, RESERVES
    manifest = build_manifest(registered_context(), producing_commit="test",
                              adoption={"adopted": True})
    library = manifest["candidate_library"]
    assert set(library["families"]) == set(FAMILIES)
    assert library["declared_severities"] == sum(len(v)
                                                 for v in RESERVES.values())
    for kind, entry in library["families"].items():
        assert entry["reserve"] == list(RESERVES[kind])


# ------------------------------------------------- the supersession mechanism
def test_a_reissued_manifest_retains_the_one_it_replaces(tmp_path):
    """§26: a defective record is marked and retained, never edited away."""
    from dci1v4r3.engine.context import synthetic_context
    from dci1v4r3.stages import registration
    context = synthetic_context(tmp_path)
    first = registration.register(context, producing_commit="c0",
                                  adoption={"adopted": False})
    second = registration.register(context, producing_commit="c1",
                                   adoption={"adopted": True},
                                   supersedes=first["manifest_hash"])
    assert second["supersedes"] == first["manifest_hash"]
    assert second["manifest_hash"] != first["manifest_hash"]
    archived = list(context.registration_root.glob(
        "registration_manifest_superseded_*.json"))
    assert len(archived) == 1
    assert json.loads(archived[0].read_text())["payload"]["manifest_hash"] == \
        first["manifest_hash"]
    assert registration.load_manifest(context)["manifest_hash"] == \
        second["manifest_hash"]


def test_the_registered_manifest_on_disk_says_what_the_code_says():
    from dci1v4r3 import CLASSIFICATION
    from dci1v4r3.engine.context import registered_context
    from dci1v4r3.stages import registration
    from dci1v4r3.verifiers import verifier_source_hash
    context = registered_context()
    if not context.registration_manifest.exists():          # pragma: no cover
        pytest.skip("v4r3 is not registered in this checkout")
    manifest = registration.load_manifest(context)
    assert manifest["classification"] == CLASSIFICATION
    assert manifest["adoption"]["adopted"] is True
    assert (manifest["instruments"]["canonical_verifier_hash"]
            == verifier_source_hash())
    assert manifest["design"]["blocks"] == C.N_BLOCKS
    assert manifest["design"]["M"] == C.M_DRAWS


# ------------------------------------------------------ §18 stage 1
def test_qualification_reads_no_behavioural_rate_and_lists_every_failure():
    from dci1v4.errors import TerminalStatus
    from dci1v4r3.engine.context import registered_context
    from dci1v4r3.stages.qualification import (
        CHECKS, qualification_payload, run_checks)
    context = registered_context()
    results = run_checks(context)
    assert {r["check"] for r in results} == set(CHECKS)
    try:
        record = qualification_payload(context, producing_commit="test")
    except TerminalStatus as terminal:
        record = terminal.record
        # Fails closed with the WHOLE list, not the first entry.
        assert len(record["failed"]) == sum(
            1 for r in record["checks"] if not r["passed"])
        assert record["status"] == "QUALIFICATION_FAILURE"
    assert record["reads_no_behavioural_rate"] is True
    # The literal is here to catch a population that moves without anyone
    # meaning it to, so it moves only with an amendment. §7.0-R3 took it from
    # 348 to 584: six numerators, ten families, one predicate form, and the
    # frozen reserves those families declare. The number is the *declared*
    # range, so it is what §10.2 owes evidence for before qualification --- not
    # what any round of expansion has admitted.
    assert record["instrument_population"] == 584
    from dci1v4r3.verifiers.boundary import instrument_population
    assert record["instrument_population"] == len(instrument_population())


def test_a_dirty_worktree_is_a_qualification_failure_and_says_why():
    """A run whose producing commit does not contain the code that produced
    it has no provenance, and qualification is where that is caught."""
    from dci1v4r3.engine.context import registered_context
    from dci1v4r3.stages.qualification import run_checks
    checks = {r["check"]: r for r in run_checks(registered_context())}
    detail = checks["clean_worktree"]["detail"]
    assert "provenance" in detail["why_it_matters"]


def test_the_audit_resolves_every_label_the_runners_actually_emit():
    """A guard that can be defeated by renaming a stage is a guard about
    spelling. `v4r3-pilot` was restated in the audit table and the runner emits
    `v4r3-gate0-pilot`, so the first Gate 0 pilot the study ever ran produced
    4,512 rows the audit could not place."""
    from dci1v4r3.run.gates_run import STAGE_CALIBRATION
    from dci1v4r3.run.pilot_run import STAGE_PILOT
    from dci1v4r3.run.regime_screen import STAGE_CAP, STAGE_LADDER
    from dci1v4r3.stages.audit import resolve_stage

    for label in (STAGE_PILOT, STAGE_CAP, STAGE_LADDER, STAGE_CALIBRATION):
        assert resolve_stage(label) is not None, label
        assert resolve_stage(f"{label}-r1") == resolve_stage(label)
