"""Gate 0's procedural pilot, walked on the CPU-only synthetic seam.

§19's point is that the apparatus fails *now* rather than after 144,384
generations, so this test walks the whole chain: 47 cells x 12 topics x M = 4,
prompt rendering, scoring, the block observation table, every registered
contrast, the refit bootstrap, the difficulty relation and its support
diagnostic, the pilot mask cycle, and the redaction that throws every number
away afterwards.

The rows are synthetic and carry `synthetic: true`. No conclusion is drawn
from any value here and none could be: the payload is fully redacted.
"""
from __future__ import annotations

import random

import pytest

from dci1v4.errors import TerminalStatus

from dci1v4r3.engine.context import synthetic_context
from dci1v4r3.engine.paths import model_tree
from dci1v4r3.protocol import constants as C
from dci1v4r3.run import pilot_run
from dci1v4r3.stages import pilot as P

MODEL = "gemma-3n-e2b-it"

FILLER = ("The kettle boils because heat moves quickly through metal and "
          "water. However, the handle stays cool. Steam rises when the "
          "temperature climbs, and a whistle sounds. Cooks watch closely, "
          "since boiling water can spill and scald. ")


def synthetic_generate(run_dir, plan, rows):
    """Deterministic answers with enough variety to move every statistic."""
    rng = random.Random(20260821)
    out = []
    for row in rows:
        words = FILLER.split()
        take = rng.randint(40, 110)
        text = " ".join((words * 4)[:take])
        if rng.random() < 0.35:
            text += " However, however, however."
        if rng.random() < 0.25:
            text += " Bright bells beckon buyers, bringing bustling business."
        out.append({"row_id": row["row_id"], "final_answer": text,
                    "answer_truncated": False, "finish_reason": "stop",
                    "total_generated_tokens": take + 12})
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rows.jsonl").write_text(
        "".join(__import__("json").dumps(r, sort_keys=True) + "\n"
                for r in out))
    return {"rows": out}


@pytest.fixture(scope="module")
def payload(tmp_path_factory):
    from dci1v4.engine.signing import create_signing_key

    root = tmp_path_factory.mktemp("gate0")
    context = synthetic_context(root)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    tree = model_tree(context, MODEL)
    return pilot_run.run_pilot(MODEL, tree, generate=synthetic_generate)


def test_the_pilot_commits_the_registered_number_of_draws(payload):
    # §19: twelve topics x forty-seven cells x M = 4.
    assert payload["cached_draws"] == 2256 == P.expected_draws()
    assert payload["cells"] == C.N_CELLS_FULL == 47
    assert payload["topics"] == C.PILOT_TOPICS == 12


def test_all_eight_acceptance_conditions_are_named_and_checked(payload):
    conditions = payload["acceptance"]["conditions"]
    assert len(conditions) == 8
    assert all(conditions.values()), [k for k, v in conditions.items() if not v]


def test_the_result_table_is_structurally_complete_including_the_spectrum(
        payload):
    # §19's v4r3 addition: a fitted difficulty relation, a support
    # diagnostic and a delta_difficulty row, before any real generation.
    result = payload["redacted_result"]
    assert "delta_difficulty" in result["F1"]["members"]
    assert "beta" in result["F8"]["members"]
    assert "Delta_class" in result["F9"]["members"]
    assert payload["redacted_support"]


def test_the_pilot_exposes_no_number_at_all(payload):
    # Not "exposes no rate by convention": exposes no number, checked.
    P.assert_fully_redacted(payload["redacted_result"])
    P.assert_fully_redacted(payload["redacted_support"])
    assert payload["exposes_no_rate"] is True


def test_the_pilot_mask_cycle_does_not_touch_the_confirmatory_namespace(
        payload):
    assert payload["mask_cycle"]["namespace"] == "pilot_mask"
    assert payload["mask_cycle"]["confirmatory_namespace_untouched"] is True


def test_the_fixtures_cannot_become_calibration_evidence(payload):
    assert set(payload["fixtures"]) == set(C.REGISTERED_SLOT_ORDER)
    assert "cannot become calibration evidence" in payload["fixtures_note"]


def test_a_missing_spectrum_row_fails_gate_0_rather_than_passing_quietly():
    thin = {"F1": {"members": {"D(B<-A)": {}, "D(A<-B)": {}, "Lambda": {},
                               "Delta_R": {}, "Xi": {}}},
            "F8": {"members": {}}, "F9": {"members": {"Delta_class": {}}}}
    with pytest.raises(TerminalStatus) as excinfo:
        P.assert_structural_completeness(thin, {"identified": True})
    record = excinfo.value.record
    assert record["status"] == "APPARATUS_FAILURE"
    assert "F1:delta_difficulty" in record["observed"]["missing"]


def test_a_missing_support_diagnostic_fails_gate_0():
    full = {family: {"members": {m: {} for f, m in
                                 P.REQUIRED_RESULT_STRUCTURE if f == family}}
            for family in ("F1", "F8", "F9")}
    with pytest.raises(TerminalStatus):
        P.assert_structural_completeness(full, None)


def test_the_wrong_draw_count_fails_gate_0():
    with pytest.raises(TerminalStatus):
        P.pilot_payload(draws=99, cells=C.N_CELLS_FULL,
                        structural_result={
                            f: {"members": {m: {} for ff, m in
                                            P.REQUIRED_RESULT_STRUCTURE
                                            if ff == f}}
                            for f in ("F1", "F8", "F9")},
                        support={"identified": True},
                        acceptance_report={}, mask_report={},
                        model_key=MODEL, pilot_dir=".")
