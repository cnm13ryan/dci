"""T6. Stage machine and gates.

Every legal and illegal transition; cap selection including zero-constraint
prompts and the truncation-bound rule firing above 0.10; the ladder screen and
the shortlist written before Gate 2; n* and m* selection with tie-breakers;
reference admission including the Newcombe condition and the disjoint
pre-screen confirmation; the composed-headroom predicate computing no contrast;
EXCESS_NOT_IDENTIFIED selecting the reduced design and not stopping; every
terminal payload.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dci1v4.analysis.diagnostics import bounded
from dci1v4.engine import transitions
from dci1v4.engine.context import synthetic_context
from dci1v4.engine.paths import model_tree
from dci1v4.engine.signing import create_signing_key
from dci1v4.errors import IntegrityError, ProtocolError, TerminalStatus
from dci1v4.protocol import constants as C
from dci1v4.stages import gates, regime
from dci1v4.topics.split import split_topics
from dci1v4.verifiers.constraints import (FOCAL_GRID,
                                          REFERENCE_LADDERS,
                                          TARGET_GRID)


@pytest.fixture()
def tree(tmp_path):
    context = synthetic_context(tmp_path)
    create_signing_key(context.signing_key_path)
    tree = model_tree(context, "gemma-3n-e2b-it")
    tree.root.mkdir(parents=True, exist_ok=True)
    return tree


def _pass(stage: str, **extra):
    return {"stage": stage, "outcome": "PASS",
            "artifact_type": C.STAGE_ARTIFACT_TYPE[stage],
            "namespace": "synthetic", **extra}


def test_the_registered_sequence_is_the_only_legal_one():
    assert C.STAGE_SEQUENCE[:8] == (
        C.STAGE_QUALIFIED, C.STAGE_GATE0, C.STAGE_REGIME, C.STAGE_GATE1,
        C.STAGE_GATE2, C.STAGE_GATE3, C.STAGE_GATE4, C.STAGE_GATE5)
    assert transitions.PREDECESSOR[C.STAGE_QUALIFIED] is None
    assert transitions.PREDECESSOR[C.STAGE_GATE3] == C.STAGE_GATE2


def test_a_stage_cannot_run_before_its_predecessor_passed(tree):
    with pytest.raises(IntegrityError, match="record missing"):
        transitions.assert_transition_legal(tree, C.STAGE_GATE2)
    transitions.write_stage_record(tree, C.STAGE_QUALIFIED,
                                   _pass(C.STAGE_QUALIFIED))
    transitions.assert_transition_legal(tree, C.STAGE_GATE0)
    with pytest.raises(IntegrityError, match="record missing"):
        transitions.assert_transition_legal(tree, C.STAGE_GATE2)


def test_a_stage_record_is_write_once(tree):
    transitions.write_stage_record(tree, C.STAGE_QUALIFIED,
                                   _pass(C.STAGE_QUALIFIED))
    with pytest.raises(IntegrityError, match="write-once"):
        transitions.assert_transition_legal(tree, C.STAGE_QUALIFIED)


def test_a_declared_artifact_type_must_match_its_stage(tree):
    with pytest.raises(IntegrityError, match="disagrees with stage"):
        transitions.write_stage_record(
            tree, C.STAGE_QUALIFIED,
            {"stage": C.STAGE_QUALIFIED, "outcome": "PASS",
             "artifact_type": "masked_result"})


def test_a_terminal_state_disables_every_later_stage(tree):
    transitions.write_stage_record(tree, C.STAGE_QUALIFIED,
                                   _pass(C.STAGE_QUALIFIED))
    transitions.write_terminal_report(tree, {
        "status": "REGIME_NOT_FOUND", "model_key": tree.model_key,
        "model_revision": "r", "gate": C.STAGE_GATE2, "criterion": "c",
        "threshold": 1, "observed": {}, "artifact_hashes": {},
        "producing_commit": "c", "environment_digest": "d",
        "strongest_permissible_statement": "s",
        "estimands_unanswerable": "all"})
    assert transitions.terminal_status(tree) == "REGIME_NOT_FOUND"
    with pytest.raises(IntegrityError, match="terminal"):
        transitions.assert_transition_legal(tree, C.STAGE_GATE0)


def test_every_terminal_record_carries_the_registered_sentence(tree):
    transitions.write_terminal_report(tree, {
        "status": "APPARATUS_FAILURE", "model_key": tree.model_key,
        "model_revision": "r", "gate": C.STAGE_GATE0, "criterion": "c",
        "threshold": 1, "observed": {}, "artifact_hashes": {},
        "producing_commit": "c", "environment_digest": "d",
        "strongest_permissible_statement": "s",
        "estimands_unanswerable": "all"})
    payload = transitions.read_stage_record.__wrapped__ \
        if hasattr(transitions.read_stage_record, "__wrapped__") else None
    from dci1v4.engine import fs
    record = fs.read_json(tree.terminal_report)["payload"]
    assert record["terminal_sentence"] == C.TERMINAL_SENTENCE
    assert "carries no evidence about the effect" in record["terminal_sentence"]


def test_a_terminal_record_missing_a_required_field_is_refused(tree):
    with pytest.raises(ProtocolError, match="missing"):
        transitions.write_terminal_report(tree, {"status": "REGIME_NOT_FOUND"})


def test_every_attempted_transition_is_logged_including_refusals(tree):
    transitions.log_transition(tree, stage=C.STAGE_GATE2, outcome="REFUSED",
                               producing_commit="c", environment_digest="d")
    rows = transitions.transition_rows(tree)
    assert rows[0]["outcome"] == "REFUSED"
    assert rows[0]["stage"] == C.STAGE_GATE2


# ------------------------------------------------------------- cap selection
def test_the_cap_set_carries_all_three_loads_and_is_subject_balanced():
    split = split_topics()
    cells = regime.cap_selection_cells(split["prescreen"])
    assert len(cells) == C.CAP_SELECTION_PROMPTS == 96
    assert {c.load for c in cells} == {0, 1, 2}
    assert sum(1 for c in cells if c.load == 0) == 24


def test_cap_selection_reads_only_the_constrained_prompts():
    result = regime.select_cap({
        512: {"constrained": 0.30, "zero_constraint": 0.95},
        768: {"constrained": 0.09, "zero_constraint": 0.90},
        1024: {"constrained": 0.02, "zero_constraint": 0.80}})
    assert result["selected_cap"] == 768
    assert result["zero_constraint_truncation"] == 0.90


def test_no_qualifying_cap_is_terminal():
    with pytest.raises(TerminalStatus) as excinfo:
        regime.select_cap({cap: {"constrained": 0.4, "zero_constraint": 0.9}
                           for cap in C.COMPLETION_CAPS})
    assert excinfo.value.status == "RESPONSE_LENGTH_INCOMPATIBLE"


def test_the_truncation_bound_rule_is_a_property_of_the_emitter():
    clean = bounded(0.42, 0.05, quantity="compliance", cell_type="solo:A")
    assert clean["is_bound"] is False and "label" not in clean
    marked = bounded(0.42, 0.11, quantity="compliance", cell_type="solo:A")
    assert marked["is_bound"] is True
    assert "reported as a bound" in marked["label"]


def test_the_ladder_screen_is_2544_cells_and_the_shortlist_precedes_gate2():
    split = split_topics()
    cells = regime.ladder_screen_cells(split["prescreen"])
    assert len(cells) == (8 + 4 + 94) * 24 == 2544
    assert {c.draws for c in cells} == {C.LADDER_SCREEN_DRAWS}
    curve = {("RF1", q): 0.5 + 0.04 * q for q in range(9)}
    table = regime.shortlist(curve, a_compliance=0.70)
    assert len(table["RF1"]) == C.LADDER_SHORTLIST_MAX
    # The curves go into the record with the shortlist, not beside it: §13.2
    # condition 2 reads them, so a record carrying one without the other is a
    # record the registered pipeline cannot produce.
    payload = regime.regime_screen_payload(
        cap={"selected_cap": 768},
        ladder_curves={"A": {}, "B": {},
                       "families": {f"{f}:{q}": v for (f, q), v in curve.items()}},
        a_prescreen_compliance=0.70, shortlist_table=table,
        truncation_by_cell={}, screen_dir=".")
    assert payload["shortlist_written_before_gate2"] is True


# ------------------------------------------------------------------- Gate 2
def test_n_star_and_m_star_selection_with_tie_breakers():
    curve = {1: 0.95, 2: 0.88, 3: 0.75, 4: 0.65, 5: 0.55, 6: 0.4, 7: 0.3,
             8: 0.2}
    chosen = gates.select_severity(curve, TARGET_GRID, C.TARGET_BAND,
                                   C.TARGET_AIM,
                                   exhausted_status="TARGET_RANGE_EXHAUSTED",
                                   quantity="A")
    assert chosen["selected"] == 3          # exact tie -> the smaller n
    focal = {7: 0.90, 8: 0.85, 9: 0.75, 10: 0.70}
    chosen_m = gates.select_severity(focal, FOCAL_GRID, C.FOCAL_BAND,
                                     C.FOCAL_AIM,
                                     exhausted_status="FOCAL_RANGE_EXHAUSTED",
                                     quantity="B")
    assert chosen_m["selected"] == 8


def test_the_three_band_diagnoses_are_distinguished():
    with pytest.raises(TerminalStatus) as jump:
        gates.select_severity({7: 0.99, 8: 0.5, 9: 0.4, 10: 0.3}, FOCAL_GRID,
                              C.FOCAL_BAND, C.FOCAL_AIM,
                              exhausted_status="FOCAL_RANGE_EXHAUSTED",
                              quantity="B")
    assert jump.value.status == "GRID_RESOLUTION_INSUFFICIENT"

    with pytest.raises(TerminalStatus) as above:
        gates.select_severity({m: 0.99 for m in FOCAL_GRID}, FOCAL_GRID,
                              C.FOCAL_BAND, C.FOCAL_AIM,
                              exhausted_status="FOCAL_RANGE_EXHAUSTED",
                              quantity="B")
    assert above.value.status == "FOCAL_RANGE_EXHAUSTED"
    assert above.value.record["observed"]["side"] == "above"

    with pytest.raises(TerminalStatus) as below:
        gates.select_severity({n: 0.05 for n in TARGET_GRID}, TARGET_GRID,
                              C.TARGET_BAND, C.TARGET_AIM,
                              exhausted_status="TARGET_RANGE_EXHAUSTED",
                              quantity="A")
    assert below.value.status == "TARGET_RANGE_EXHAUSTED"


def test_every_band_diagnosis_records_the_complete_curve():
    with pytest.raises(TerminalStatus) as excinfo:
        gates.select_severity({m: 0.99 for m in FOCAL_GRID}, FOCAL_GRID,
                              C.FOCAL_BAND, C.FOCAL_AIM,
                              exhausted_status="FOCAL_RANGE_EXHAUSTED",
                              quantity="B")
    assert excinfo.value.record["curves"]["B"] == {m: 0.99 for m in FOCAL_GRID}
    assert "registered grid" in \
        excinfo.value.record["strongest_permissible_statement"]


def test_regime_adequacy_fails_on_vacuity_or_a_degenerate_graded():
    good = {"a_curve": {n: 0.7 for n in TARGET_GRID},
            "b_curve": {m: 0.8 for m in FOCAL_GRID}}
    with pytest.raises(TerminalStatus) as vac:
        gates.gate2_payload(**good, b_solo_vacuity=0.2,
                            graded_distribution={"A": 0.6, "B": 0.7})
    assert vac.value.status == "REGIME_NOT_FOUND"
    with pytest.raises(TerminalStatus):
        gates.gate2_payload(**good, b_solo_vacuity=0.05,
                            graded_distribution={"A": 0.995, "B": 0.7})
    passed = gates.gate2_payload(**good, b_solo_vacuity=0.05,
                                 graded_distribution={"A": 0.6, "B": 0.7})
    assert passed["outcome"] == "PASS"


# ------------------------------------------------------------------- Gate 3
def _family_inputs(mean: float, *, prescreen_gap: float = 0.0,
                   vacuity: float = 0.02):
    a_cal = [0.70] * 96
    cal = {2: [mean] * 96}
    draws = {2: ([1] * int(mean * 384) + [0] * (384 - int(mean * 384)),
                 [1] * int(0.70 * 384) + [0] * (384 - int(0.70 * 384)))}
    return {"calibration": cal, "a_calibration": a_cal,
            "prescreen": {2: 0.70 + prescreen_gap}, "a_prescreen": 0.70,
            "vacuity": {2: vacuity}, "draw_level": draws}


def test_reference_admission_applies_every_registered_condition():
    close = gates.admit_family("RF1", n_star=3, **_family_inputs(0.70))
    assert close["selected"] is not None

    far = gates.admit_family("RF1", n_star=3, **_family_inputs(0.40))
    assert far["selected"] is None
    assert any("caliper" in r for r in far["candidates"][0]["reasons"])

    prescreen = gates.admit_family("RF1", n_star=3,
                                   **_family_inputs(0.70, prescreen_gap=0.30))
    assert prescreen["selected"] is None
    assert any("pre-screen" in r
               for r in prescreen["candidates"][0]["reasons"])

    vacuous = gates.admit_family("RF1", n_star=3,
                                 **_family_inputs(0.70, vacuity=0.5))
    assert vacuous["selected"] is None
    assert any("vacuity" in r for r in vacuous["candidates"][0]["reasons"])


def test_the_newcombe_condition_can_refuse_an_otherwise_close_reference():
    inputs = _family_inputs(0.70)
    inputs["draw_level"] = {2: ([1] * 384, [0] * 384)}
    inputs["calibration"] = {2: [0.70] * 96}
    result = gates.admit_family("RF1", n_star=3, **inputs)
    reasons = result["candidates"][0]["reasons"]
    assert any("Newcombe" in r for r in reasons)


def test_fewer_than_three_references_selects_the_reduced_design():
    result = gates.gate3_payload([
        {"family": "RF1", "selected": {"severity": 2, "abs_difference": 0.01},
         "candidates": []}], n_star=3)
    assert result["outcome"] == "PASS"
    assert result["design"] == "reduced"
    assert result["cells_per_block"] == C.N_CELLS_REDUCED
    assert result["identification_statuses"] == ["EXCESS_NOT_IDENTIFIED"]


def test_three_references_select_the_full_design_by_smallest_distance():
    families = [
        {"family": "RF8", "selected": {"severity": 1, "abs_difference": 0.05},
         "candidates": []},
        {"family": "RF1", "selected": {"severity": 2, "abs_difference": 0.01},
         "candidates": []},
        {"family": "RF5", "selected": {"severity": 4, "abs_difference": 0.03},
         "candidates": []},
        {"family": "RF7", "selected": {"severity": 6, "abs_difference": 0.09},
         "candidates": []}]
    result = gates.gate3_payload(families, n_star=3)
    assert result["design"] == "full"
    assert [a["family"] for a in result["admitted"]] == ["RF1", "RF5", "RF8"]
    assert result["reference_slots"]["R1"] == ["RF1", 2]
    assert result["identification_statuses"] == []


# ------------------------------------------------------------------- Gate 4
def test_gate4_evaluates_each_cell_independently_and_ranks_nothing():
    report = gates.gate4_payload({
        "pair:A+B:c1_first": {"A": 0.42, "B": 0.61},
        "pair:A+B:c2_first": {"A": 0.10, "B": 0.90}})
    assert report["computes_no_contrast"] is True
    assert all(row["inside_band"] for row in report["composed_table"])
    with pytest.raises(TerminalStatus) as excinfo:
        gates.gate4_payload({"pair:A+B:c1_first": {"A": 0.42, "B": 0.99}})
    assert excinfo.value.status == "COMPOSED_HEADROOM_FAILURE"
    assert excinfo.value.record["composed_table"]


# ------------------------------------------------- §13.2 condition 2's input
#
# §13.2 condition 2 checks the reference-minus-A distance on the disjoint 24
# pre-screen topics, and its only input is the REGIME_SCREEN record. The
# registered pipeline supplies it for free -- §12.2 measures all 94 rungs
# there and §12.3 measures only the shortlist §12.2 wrote -- so an
# unevaluable condition 2 is a symptom of the stages having been run out of
# order, never a gap in the rule. These tests keep it that way.
def test_a_shortlist_naming_an_unmeasured_rung_is_refused():
    curves = {"families": {"RF1:0": 0.1, "RF1:1": 0.2}}
    regime.assert_shortlist_is_measured(
        curves, {"RF1": [{"severity": 0}, {"severity": 1}]})
    with pytest.raises(ProtocolError) as error:
        regime.assert_shortlist_is_measured(curves, {"RF1": [{"severity": 7}]})
    assert "13.2 condition 2" in str(error.value)


def test_a_shortlist_longer_than_three_is_refused():
    curves = {"families": {f"RF1:{q}": 0.1 for q in range(4)}}
    with pytest.raises(ProtocolError):
        regime.assert_shortlist_is_measured(
            curves, {"RF1": [{"severity": q} for q in range(4)]})


def test_the_regime_record_cannot_be_written_without_that_guarantee(tmp_path):
    kwargs = dict(cap={"selected_cap": 512},
                  ladder_curves={"A": {}, "B": {}, "families": {"RF1:0": 0.5}},
                  a_prescreen_compliance=0.5,
                  truncation_by_cell={}, screen_dir=tmp_path)
    payload = regime.regime_screen_payload(
        shortlist_table={"RF1": [{"severity": 0}]}, **kwargs)
    assert payload["shortlist_written_before_gate2"] is True
    with pytest.raises(ProtocolError):
        regime.regime_screen_payload(
            shortlist_table={"RF1": [{"severity": 4}]}, **kwargs)


def test_admit_family_rejects_a_rung_with_no_prescreen_value():
    """The registered disposition is reject, not abstain.

    Both runs are identical apart from the pre-screen value, so the reason
    list isolates condition 2. A future change to abstain would be a change
    to §13.2 and has to be visible as one.
    """
    ladder = REFERENCE_LADDERS["RF1"]
    per_topic = [1.0] * 70 + [0.0] * 26
    draws = ([1] * 280 + [0] * 104, [1] * 280 + [0] * 104)

    def run(prescreen):
        return gates.admit_family(
            "RF1", n_star=4, calibration={q: per_topic for q in ladder},
            a_calibration=list(per_topic), prescreen=prescreen,
            a_prescreen=0.70, vacuity={q: 0.0 for q in ladder},
            draw_level={q: draws for q in ladder})

    present = run({q: 0.70 for q in ladder})
    absent = run({q: 0.70 for q in ladder if q != 1})
    assert next(c["admissible"] for c in present["candidates"]
                if c["severity"] == 1) is True
    rung = next(c for c in absent["candidates"] if c["severity"] == 1)
    assert rung["admissible"] is False
    assert rung["reasons"] == ["no pre-screen measurement"]


@pytest.mark.parametrize("model", ["gemma-3n-e2b-it", "gemma-3n-e4b-it",
                                   "qwen3-4b", "qwen3-4b-instruct-2507"])
def test_every_registered_regime_record_satisfies_the_invariant(model):
    path = (Path(__file__).resolve().parents[1] / "evidence" / "dci1-v4"
            / model / "regime_screen.json")
    if not path.exists():                      # evidence is machine-local
        pytest.skip(f"{model}: no registered regime record on this machine")
    record = json.loads(path.read_text())["payload"]
    curves = record["ladder_screen"]["curves"]
    assert len(curves["families"]) == sum(len(v)
                                          for v in REFERENCE_LADDERS.values())
    regime.assert_shortlist_is_measured(curves, record["shortlist"])
