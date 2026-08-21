"""The stage machine, and the seal on §12.1's composed probe.

Two defects found by the 2026-08-21 audit, both of the same shape: a rule the
protocol states in prose with nothing on the execution path enforcing it.

* **Stage order.** `STAGE_SEQUENCE` existed in `constants.py` and nothing read
  it, which is how the §12.2 regime screen came to run before `QUALIFIED` and
  `GATE_0_APPARATUS`.
* **The cap probe.** §12.1 must generate composed `A + B` prompts to measure
  truncation where the answer is hardest to write, and the shared scorer
  stores per-constituent verdicts on those rows. Nothing read them --- but
  `D(B <- A)` at `A:8 + B:7` was derivable from stored evidence, and §12.5 and
  §13.9 forbid a composed outcome reaching cap selection, candidate
  construction or reference selection.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v4r3.engine.context import synthetic_context
from dci1v4r3.engine.paths import model_tree, required_records
from dci1v4r3.engine.transitions import (
    PREDECESSOR, adopt_out_of_order, assert_transition_legal,
    log_transition, read_stage_record, stage_reached, transition_rows,
    write_stage_record, write_terminal_report,
)
from dci1v4r3.protocol import constants as C
from dci1v4r3.stages import cap_probe

SRC = Path(__file__).resolve().parents[1] / "src"
MODEL = "gemma-3n-e2b-it"


@pytest.fixture()
def tree(tmp_path):
    from dci1v4.engine.signing import create_signing_key

    context = synthetic_context(tmp_path)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    return model_tree(context, MODEL)


def _payload(stage: str, outcome: str = "PASS") -> dict:
    return {"stage": stage, "outcome": outcome,
            "artifact_type": C.STAGE_ARTIFACT_TYPE[stage],
            "model_key": MODEL}


# --------------------------------------------------------- the stage machine

def test_the_registered_sequence_is_a_total_order_with_one_head():
    heads = [s for s, p in PREDECESSOR.items() if p is None]
    assert heads == [C.STAGE_QUALIFIED]
    assert len(PREDECESSOR) == len(C.STAGE_SEQUENCE)


def test_a_stage_cannot_run_before_its_predecessor_passed(tree):
    # This is the exact bypass that let REGIME_SCREEN run before QUALIFIED.
    with pytest.raises(IntegrityError):
        assert_transition_legal(tree, C.STAGE_REGIME)
    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    with pytest.raises(IntegrityError):
        assert_transition_legal(tree, C.STAGE_REGIME)   # GATE_0 still missing
    write_stage_record(tree, C.STAGE_GATE0, _payload(C.STAGE_GATE0))
    assert_transition_legal(tree, C.STAGE_REGIME)       # now legal


def test_a_predecessor_that_did_not_pass_does_not_license_the_next_stage(tree):
    write_stage_record(tree, C.STAGE_QUALIFIED,
                       _payload(C.STAGE_QUALIFIED, outcome="TERMINAL"))
    with pytest.raises(IntegrityError):
        assert_transition_legal(tree, C.STAGE_GATE0)


def test_stage_records_are_write_once(tree):
    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    with pytest.raises(IntegrityError):
        assert_transition_legal(tree, C.STAGE_QUALIFIED)


def test_a_record_whose_artifact_type_disagrees_with_its_stage_is_refused(tree):
    bad = _payload(C.STAGE_QUALIFIED)
    bad["artifact_type"] = "confirmatory_evidence"
    with pytest.raises(IntegrityError):
        write_stage_record(tree, C.STAGE_QUALIFIED, bad)


def test_a_terminal_replication_disables_every_later_stage(tree):
    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    write_terminal_report(tree, {
        "status": C.TERMINAL_STATUSES[0], "model_key": MODEL,
        "gate": C.STAGE_GATE0, "criterion": "a fixture",
        "observed": {}, "producing_commit": "0" * 40,
        "strongest_permissible_statement": "none"})
    with pytest.raises(IntegrityError) as excinfo:
        assert_transition_legal(tree, C.STAGE_GATE0)
    assert C.TERMINAL_SENTENCE in str(excinfo.value)


def test_an_unregistered_terminal_status_cannot_be_written(tree):
    with pytest.raises(ProtocolError):
        write_terminal_report(tree, {
            "status": "NOT_A_REGISTERED_STATUS", "model_key": MODEL,
            "gate": C.STAGE_GATE0, "criterion": "x", "observed": {},
            "producing_commit": "0" * 40,
            "strongest_permissible_statement": "none"})


def test_nothing_at_or_before_the_freeze_may_be_rewritten_after_it(tree):
    for stage in C.STAGE_SEQUENCE[:C.STAGE_SEQUENCE.index(C.STAGE_GATE5) + 1]:
        write_stage_record(tree, stage, _payload(stage))
    assert stage_reached(tree) == C.STAGE_GATE5
    # Removing an earlier record and re-running it is refused *because the
    # freeze exists*, not merely because the record does: the write-once rule
    # alone would be satisfied once the file is gone.
    for stage in (C.STAGE_GATE2, C.STAGE_GATE3):
        tree.stage_record(stage).unlink()
        with pytest.raises(IntegrityError) as excinfo:
            assert_transition_legal(tree, stage)
        assert "frozen" in str(excinfo.value)
    # Deleting the freeze record itself is a different attack surface. The
    # transition guard reads that record, so it cannot be the thing that
    # detects its absence; the evidence manifest and durable mirror are.
    tree.stage_record(C.STAGE_GATE5).unlink()
    assert C.STAGE_GATE5 in required_records(C.STAGE_GATE5)[-1]


def test_the_record_is_signed_and_a_mutated_byte_is_detected(tree):
    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    assert read_stage_record(tree, C.STAGE_QUALIFIED)["outcome"] == "PASS"
    path = tree.stage_record(C.STAGE_QUALIFIED)
    path.write_text(path.read_text().replace('"PASS"', '"FAIL"'))
    with pytest.raises(Exception):
        read_stage_record(tree, C.STAGE_QUALIFIED)


def test_every_attempted_transition_is_logged_including_refusals(tree):
    log_transition(tree, stage=C.STAGE_REGIME, outcome="REFUSED",
                   producing_commit="0" * 40, environment_digest="d")
    rows = transition_rows(tree)
    assert [r["outcome"] for r in rows] == ["REFUSED"]


def test_out_of_order_adoption_does_not_license_the_next_stage(tree):
    # The §12.2 rows are real evidence, generated before the machine existed.
    # Recording that is honest; letting it satisfy GATE_1 would not be.
    adopt_out_of_order(tree, C.STAGE_REGIME, _payload(C.STAGE_REGIME),
                       reason="generated before the stage machine existed",
                       produced_before_commit="6954dd6")
    payload = read_stage_record(tree, C.STAGE_REGIME)
    assert payload["outcome"] == "ADOPTED_OUT_OF_ORDER"
    with pytest.raises(IntegrityError):
        assert_transition_legal(tree, C.STAGE_GATE1)


def test_required_records_grow_with_the_sequence():
    assert len(required_records(C.STAGE_QUALIFIED)) == 1
    assert len(required_records(C.STAGE_GATE5)) == 8
    assert len(required_records(C.STAGE_UNMASKED_ANALYSIS)) == \
        len(C.STAGE_SEQUENCE)


# ------------------------------------------------------------ the cap seal

def _composed_probe_row(truncated=False):
    """A cap row exactly as `generate_and_score` stores it."""
    return {"cell_id": "cap:history-20:A:8+B:7", "load": 2,
            "truncated": truncated, "arm": "cap",
            "scores": [{"kind": "A", "severity": 8, "passed": False,
                        "graded": 0.75, "non_vacuous": True},
                       {"kind": "B", "severity": 7, "passed": True,
                        "graded": 1.0, "non_vacuous": True}],
            "raw_response": "...", "word_count": 108}


def test_restrict_drops_every_outcome_bearing_field():
    restricted = cap_probe.restrict([_composed_probe_row()])
    assert set(restricted[0]) == set(cap_probe.REGISTERED_CAP_FIELDS)
    for field in cap_probe.FORBIDDEN_CAP_FIELDS:
        assert field not in restricted[0]


def test_the_cap_decision_refuses_a_view_that_still_carries_scores():
    with pytest.raises(ProtocolError) as excinfo:
        cap_probe.truncation_by_load([_composed_probe_row()])
    assert "composed compliance outcome is derivable" in str(excinfo.value)


def test_truncation_is_computed_over_loads_one_and_two_together():
    rows = cap_probe.restrict([
        {"cell_id": "cap:t:load0", "load": 0, "truncated": False},
        {"cell_id": "cap:t:A", "load": 1, "truncated": True},
        {"cell_id": "cap:t:B", "load": 1, "truncated": False},
        _composed_probe_row(truncated=False)])
    table = cap_probe.truncation_by_load(rows)
    assert table["unconstrained"] == 0.0
    assert table["constrained"] == pytest.approx(1 / 3)
    assert table["n_by_load"] == {"0": 1, "1": 2, "2": 1}


def test_the_durable_cap_artifact_carries_no_composed_outcome():
    artifact = cap_probe.cap_probe_artifact(
        {512: {"unconstrained": 0.0, "constrained": 0.0, "n": 96}},
        model_key=MODEL, selected_cap=512)
    text = repr(artifact)
    assert "passed" not in text and "graded" not in text
    assert artifact["selected_cap"] == 512


def test_selection_modules_never_read_a_composed_probe_field():
    """The structural half: the selection path cannot name the field at all.

    An assertion on values would only catch a caller that ran. This catches
    one that is written.
    """
    offenders = []
    for name in ("stages/regime.py", "stages/library.py",
                 "stages/selection.py", "stages/gates.py"):
        source = (SRC / "dci1v4r3" / name).read_text()
        tree_ = ast.parse(source)
        for node in ast.walk(tree_):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                continue
            if isinstance(node, ast.Attribute) and node.attr == "scores":
                offenders.append(f"{name}: .scores")
            if isinstance(node, ast.Subscript):
                key = node.slice
                if isinstance(key, ast.Constant) and key.value == "scores":
                    offenders.append(f"{name}: ['scores']")
    assert offenders == [], offenders


def test_the_regime_screen_restricts_the_probe_before_selecting_the_cap():
    source = (SRC / "dci1v4r3" / "run" / "regime_screen.py").read_text()
    assert "cap_probe.restrict(rows)" in source
    # and the old direct read of the raw rows is gone
    assert 'loads[row["load"]].append' not in source


# ------------------------------------------------------------- supersession

def test_superseding_retains_every_row_and_frees_the_stage_to_run_again(tree):
    """A prospective amendment changes the code, and §18 then makes records
    produced under the old code unusable as predecessors. Retiring them must
    keep them readable, not delete them."""
    from dci1v4r3.engine.transitions import supersede_stage_records

    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    rows = tree.backend_runs(C.STAGE_QUALIFIED) / "ladder"
    rows.mkdir(parents=True, exist_ok=True)
    (rows / "scored.jsonl").write_text('{"row": 1}\n')

    note = supersede_stage_records(
        tree, [C.STAGE_QUALIFIED], reason="amendment R3 moved the verifier",
        superseded_by_commit="a" * 40)

    assert not tree.stage_record(C.STAGE_QUALIFIED).exists()
    retained = Path(note["stages"][0]["retained_at"])
    assert (retained / "backend_runs" / "ladder" / "scored.jsonl").read_text() \
        == '{"row": 1}\n'
    assert (retained / "records").exists()
    # and the stage may now run again
    assert_transition_legal(tree, C.STAGE_QUALIFIED)


def test_supersession_is_logged_as_an_attempted_transition(tree):
    from dci1v4r3.engine.transitions import supersede_stage_records

    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    supersede_stage_records(tree, [C.STAGE_QUALIFIED], reason="r",
                            superseded_by_commit="b" * 40)
    outcomes = [row["outcome"] for row in transition_rows(tree)]
    assert "SUPERSEDED" in outcomes


def test_superseding_twice_under_one_commit_refuses_rather_than_overwrites(tree):
    from dci1v4r3.engine.transitions import supersede_stage_records

    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    supersede_stage_records(tree, [C.STAGE_QUALIFIED], reason="r",
                            superseded_by_commit="c" * 40)
    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    with pytest.raises(IntegrityError):
        supersede_stage_records(tree, [C.STAGE_QUALIFIED], reason="r",
                                superseded_by_commit="c" * 40)


def test_supersession_refuses_after_the_freeze(tree):
    """§18.1 forbids exactly this mutation, and superseding is the sharpest
    form of it."""
    from dci1v4r3.engine.transitions import supersede_stage_records

    write_stage_record(tree, C.STAGE_QUALIFIED, _payload(C.STAGE_QUALIFIED))
    write_stage_record(tree, C.STAGE_GATE5, _payload(C.STAGE_GATE5))
    with pytest.raises(IntegrityError):
        supersede_stage_records(tree, [C.STAGE_QUALIFIED], reason="r",
                                superseded_by_commit="d" * 40)


def test_supersession_requires_a_reason_and_a_commit(tree):
    from dci1v4r3.engine.transitions import supersede_stage_records

    with pytest.raises(ProtocolError):
        supersede_stage_records(tree, [C.STAGE_QUALIFIED], reason="",
                                superseded_by_commit="e" * 40)
