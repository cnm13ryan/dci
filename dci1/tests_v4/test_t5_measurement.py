"""T5. Verifiers and measurement.

Determinism at 1.000 for every instrument; the split boundary suites with the
carried A-side subset byte-identical and the authored additions present; the
independent reimplementations and an assertion that their source material is
the registered prose only; parse independence; Wilson and Newcombe including
the fail-class margin split; the carry-over hash conditions; the autorater
parser, config-drift refusal, serialised execution and one-shot ledger; the v4
reserved final-check set; the three-value measurement_basis domain; the §10.5
scope sentence; and the annotation interface's blinding and finalisation.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dci1v4.analysis.intervals import (
    intersects,
    newcombe_paired,
    paired_table,
    wilson_upper_bound,
)
from dci1v4.annotation.packets import (
    AnnotationSession,
    build_packet,
    EXCLUDED_FROM_PACKET,
    assert_independent,
    assert_packet_blinded,
)
from dci1v4.engine.context import DCI1_ROOT, synthetic_context
from dci1v4.engine.paths import model_tree
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.stages import autorater, gate1
from dci1v4.verifiers import boundary, independent, wording_suite

PACKAGE = DCI1_ROOT / "src" / "dci1v4"
INSTRUMENTS = [("A", 3), ("B", 8), ("RF1", 2), ("RF5", 4), ("RF7", 6)]


def test_three_process_determinism_is_exactly_one():
    responses = [c["text"] for c in boundary.FOCAL_CASES][:12]
    report = gate1.three_process_determinism(INSTRUMENTS, responses)
    assert report["processes"] == C.DETERMINISM_PROCESSES == 3
    assert report["agreement"] == 1.0


def test_the_boundary_suites_split_carried_from_authored():
    assert len(boundary.CARRIED_CASES) == 40
    assert len(boundary.ADDED_TARGET_CASES) == 8
    assert len(boundary.TARGET_CASES) == 48
    assert len(boundary.FOCAL_CASES) >= C.BOUNDARY_SUITE_MIN_CASES
    assert all(c["origin"] == "carried_v3" for c in boundary.CARRIED_CASES)
    authored = list(boundary.ADDED_TARGET_CASES) + list(boundary.FOCAL_CASES)
    assert all(c["origin"] == "authored_v4" for c in authored)


def test_the_carried_subset_is_byte_identical_to_the_v3_artifact():
    from dci1v4.verifiers.carryover import boundary_carry_over

    report = boundary_carry_over()
    assert report["cases"] == 40
    assert report["v3_sha256"] == report["v4_sha256"]


def test_the_authored_additions_cover_the_wider_enumeration():
    covered = {c["covers"] for c in boundary.ADDED_TARGET_CASES}
    assert {"unicode-punctuation", "unicode-lookalike", "zero-width",
            "sentence-boundary-punctuation"} <= covered
    report = boundary.assert_coverage()
    assert report["target_coverage_categories"] >= 12
    assert report["focal_coverage_categories"] >= 18


def test_every_instrument_agrees_with_its_suite_at_exactly_one():
    report = boundary.evaluate_suites()
    assert report["failures"] == []
    assert set(report["agreement"].values()) == {1.0}
    assert len(report["agreement"]) == 10        # A, B and the eight families


def test_the_independent_reimplementation_reads_only_the_registered_prose():
    path = PACKAGE / "verifiers" / "independent.py"
    imported: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any(name.startswith("dci1") for name in imported), imported
    docstring = ast.get_docstring(ast.parse(path.read_text()))
    assert "§7.1" in docstring and "§9.2" in docstring and "§9.3" in docstring


def test_the_independent_reimplementation_agrees_at_exactly_one():
    responses = [c["text"] for c in boundary.FOCAL_CASES]
    report = gate1.independent_agreement(INSTRUMENTS, responses)
    assert set(report["agreement"].values()) == {1.0}
    assert report["disagreements"] == []


def test_the_two_implementations_use_different_mechanisms():
    """Agreement is evidence about the rule only if the code differs.

    The comparison is on the segmentation, which every instrument depends on:
    the primary walks characters and accumulates runs, the independent one
    matches a compiled Unicode-letter pattern.
    """
    primary = (PACKAGE / "verifiers" / "words.py").read_text()
    other = (PACKAGE / "verifiers" / "independent.py").read_text()
    assert "for ch in text" in primary and "runs.append" in primary
    assert "re.compile" not in primary
    assert "re.compile" in other and "findall" in other
    assert "runs.append" not in other
    assert independent._WORD.pattern == r"[^\W\d_]+"


def test_parse_independence_is_checked_on_signatures():
    signatures = wording_suite.assert_parse_independence()
    assert signatures["focal_statistic"] == ["text"]
    assert signatures["score_constraint"] == ["constraint", "text",
                                              "truncated"]


def test_wording_equivalence_over_twenty_responses():
    report = wording_suite.evaluate()
    assert report["responses"] == 20
    assert report["wordings_per_constraint"] == 4
    assert report["constraint_severities"] == 8 + 4 + 94


def test_the_wilson_bound_and_the_fail_class_margin_split():
    labels = ([{"verifier_class": "pass", "agrees": True}] * 146
              + [{"verifier_class": "pass", "agrees": False}] * 4
              + [{"verifier_class": "fail", "margin_one": True,
                  "agrees": True}] * 40
              + [{"verifier_class": "fail", "margin_one": True,
                  "agrees": False}] * 4
              + [{"verifier_class": "fail", "margin_one": False,
                  "agrees": True}] * 50)
    report = gate1.human_agreement(labels)
    assert set(report["strata"]) == {"pass", "fail:margin_one",
                                     "fail:margin_larger"}
    # v3's realised fail-class disagreements were four of forty-four at margin
    # one and none at larger margins; the split is strictly stricter and the
    # margin-one stratum is what fails.
    assert report["strata"]["fail:margin_one"]["meets_criterion"] is False
    assert report["strata"]["fail:margin_larger"]["meets_criterion"] is True
    assert report["all_met"] is False
    assert wilson_upper_bound(0, 150) < C.HUMAN_DISAGREEMENT_MAX


def test_the_newcombe_interval_and_its_region_test():
    table = paired_table([1] * 80 + [0] * 20, [1] * 78 + [0] * 22)
    interval = newcombe_paired(*table)
    assert interval["lower"] <= interval["difference"] <= interval["upper"]
    assert intersects(interval, C.REFERENCE_NEWCOMBE_REGION)
    far = newcombe_paired(*paired_table([1] * 100, [0] * 100))
    assert not intersects(far, C.REFERENCE_NEWCOMBE_REGION)


def test_the_measurement_basis_domain_has_exactly_three_values():
    assert C.MEASUREMENT_BASES == ("human_validated",
                                   "autorater_calibration_approved",
                                   "human_validation_unavailable")
    assert "HUMAN_VALIDATION_UNAVAILABLE" in C.IDENTIFICATION_STATUSES


def test_the_scope_sentence_attaches_while_the_basis_is_not_human_validated():
    from dci1v4.analysis.claims import ClaimContext

    for basis in ("autorater_calibration_approved",
                  "human_validation_unavailable"):
        assert ClaimContext(configuration="outcome_first",
                            measurement_basis=basis).scope_sentence \
            == C.SCOPE_SENTENCE
    assert ClaimContext(configuration="outcome_first",
                        measurement_basis="human_validated"
                        ).scope_sentence is None


def test_the_autorater_configuration_fails_closed_on_drift():
    config = autorater.build_config(
        "gpt-oss-20b", prompt_version="v1", prompt_hash="a" * 64,
        parser_version="p1", label_mapping={"pass": "PASS"},
        decoding={"temperature": 0.0}, output_cap=256)
    assert config["execution_concurrency"] == 1
    autorater.assert_no_config_drift(config, config)
    drifted = {**config, "output_cap": 512}
    drifted["config_hash"] = "different"
    with pytest.raises(IntegrityError):
        autorater.assert_no_config_drift(config, drifted)


def test_concurrent_autorater_execution_is_refused():
    with pytest.raises(ProtocolError, match="serialised"):
        autorater.build_config(
            "gpt-oss-20b", prompt_version="v1", prompt_hash="a" * 64,
            parser_version="p1", label_mapping={}, decoding={},
            output_cap=256, execution_concurrency=8)


def test_a_study_model_can_never_be_its_own_judge():
    with pytest.raises(ProtocolError, match="disjoint"):
        autorater.build_config("qwen3-4b", prompt_version="v1",
                               prompt_hash="a" * 64, parser_version="p1",
                               label_mapping={}, decoding={}, output_cap=256)


def test_the_autorater_split_is_deterministic_and_disjoint():
    items = [{"item_id": f"i{i}", "verifier_class": "pass" if i % 2 else "fail"}
             for i in range(40)]
    first = autorater.stratified_split(items, model_id="m")
    second = autorater.stratified_split(items, model_id="m")
    assert first["split_hash"] == second["split_hash"]
    dev = {i["item_id"] for i in first["development"]}
    cal = {i["item_id"] for i in first["calibration"]}
    assert not dev & cal
    assert len(dev) + len(cal) == 40


def test_calibration_is_one_shot_and_the_ledger_precedes_the_mutation(tmp_path):
    context = synthetic_context(tmp_path)
    tree = model_tree(context, "gemma-3n-e2b-it")
    tree.root.mkdir(parents=True)
    config = autorater.build_config(
        "gpt-oss-20b", prompt_version="v1", prompt_hash="a" * 64,
        parser_version="p1", label_mapping={}, decoding={}, output_cap=256)
    frozen = {"config": config}
    items = [{"item_id": "i1", "verifier_class": "pass"}]
    autorater.calibrate_once(tree, frozen=frozen, current_config=config,
                             calibration_items=items,
                             judgments={"i1": "pass"}, producing_commit="c")
    # Deleting the record does not re-open the stage: the ledger entry stands.
    (tree.root / "gate1" / "autorater_calibration.json").unlink()
    with pytest.raises(IntegrityError, match="already been claimed|already "
                                             "claimed"):
        autorater.calibrate_once(tree, frozen=frozen, current_config=config,
                                 calibration_items=items,
                                 judgments={"i1": "pass"},
                                 producing_commit="c")


def test_the_sealed_set_is_new_for_v4_and_opens_at_most_once(tmp_path):
    context = synthetic_context(tmp_path)
    tree = model_tree(context, "gemma-3n-e2b-it")
    tree.root.mkdir(parents=True)
    sealed = gate1.seal_final_check_set(tree, [{"item_id": "x"}],
                                        producing_commit="c")
    assert sealed["items"] == 1
    with pytest.raises(ProtocolError, match="before every"):
        gate1.open_final_check_set(tree, autorater_frozen=False,
                                   producing_commit="c")
    with pytest.raises(ProtocolError, match="never used for"):
        gate1.open_final_check_set(tree, autorater_frozen=True,
                                   producing_commit="c", purpose="tuning")
    opened = gate1.open_final_check_set(tree, autorater_frozen=True,
                                        producing_commit="c")
    assert opened["sealed"] is True
    with pytest.raises(IntegrityError, match="already been opened"):
        gate1.open_final_check_set(tree, autorater_frozen=True,
                                   producing_commit="c")


def test_the_v3_sealed_set_is_never_opened_by_v4():
    """Check C4: the v4 instrument population differs, so a new set is sealed
    and nothing in dci1v4 can reach the v3 one."""
    text = "".join((PACKAGE / "stages" / "gate1.py").read_text())
    assert "sequestered_v3" not in text and "dci1v3" not in text


def test_the_annotation_packet_is_structurally_blinded():
    items = [{"item_id": f"i{i}", "response_text": f"a{i}", "kind": "B",
              "instruction_text": "…"} for i in range(4)]
    packet = build_packet(items, annotator_id="ann", packet_id="p")
    assert_packet_blinded(packet)
    for field in EXCLUDED_FROM_PACKET:
        assert all(field not in item for item in packet["items"])
    with pytest.raises(IntegrityError):
        assert_packet_blinded({**packet,
                               "interface_properties":
                                   {**packet["interface_properties"],
                                    "highlighting": True}})


def test_display_order_is_per_annotator_seeded():
    items = [{"item_id": f"i{i}", "response_text": f"a{i}", "kind": "A",
              "instruction_text": "…"} for i in range(12)]
    one = [i["response_text"] for i in
           build_packet(items, annotator_id="x", packet_id="p")["items"]]
    two = [i["response_text"] for i in
           build_packet(items, annotator_id="y", packet_id="p")["items"]]
    again = [i["response_text"] for i in
             build_packet(items, annotator_id="x", packet_id="p")["items"]]
    assert one != two
    assert one == again


def test_finalisation_requires_every_label_and_is_immutable(tmp_path):
    items = [{"item_id": f"i{i}", "response_text": f"a{i}", "kind": "A",
              "instruction_text": "…"} for i in range(3)]
    packet = build_packet(items, annotator_id="ann", packet_id="p")
    session = AnnotationSession(tmp_path / "s.json", packet)
    session.mark(0, ["one"])
    with pytest.raises(ProtocolError, match="label on every item"):
        session.finalise()
    session.mark(1, [])
    session.mark(2, ["a", "b"])
    payload = session.finalise()
    assert payload["labels"][2]["tally"] == 2
    with pytest.raises(IntegrityError):
        session.mark(0, ["late"])
    with pytest.raises(IntegrityError):
        session.finalise()


def test_the_session_file_lives_outside_the_evidence_tree(tmp_path):
    context = synthetic_context(tmp_path / "study")
    items = [{"item_id": "i", "response_text": "a", "kind": "A",
              "instruction_text": "…"}]
    packet = build_packet(items, annotator_id="ann", packet_id="p")
    workspace = tmp_path / "workspace" / "s.json"
    session = AnnotationSession(workspace, packet)
    session.mark(0, [])
    session.finalise()
    assert not workspace.resolve().is_relative_to(
        context.study_root.resolve())
