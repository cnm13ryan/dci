"""§10.4-R2's guards: what the microcase validator may never be told.

§10.4-R failed and its planted-defect arm said why --- the judge recounted the
response and was blind to `vacuity_ignored`. R2 changes the unit, and the
things that make the new unit informative are exactly the things a later edit
could quietly remove: the answer must stay small, the two halves must stay
balanced, the prompt must never carry the verifier's verdict, and the
conventions arm must carry only text that is identical for every case.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v4r4.stages.microcase import (
    ARM_CONVENTIONS, ARM_INSTRUCTION, ARM_OF_DEFECT, CONVENTIONS_TEXT,
    DEFECT_KINDS, MAX_ANSWER_WORDS, NUMERATOR_SWAP, build_cases,
    defect_verdict, split_cases, stratum_counts,
)
from dci1v4r4.verifiers.compliance import passes
from dci1v4r4.verifiers.constraints import Constraint, FAMILIES
from dci1v4r4.verifiers.statistics import STATISTICS, word_count

DCI1 = Path(__file__).resolve().parents[1]


def _tool():
    spec = importlib.util.spec_from_file_location(
        "gate1_microcase_v4r3", DCI1 / "tools" / "gate1_microcase_v4r3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = build_cases()


# --------------------------------------------------------------- the cases

def test_every_answer_is_small_enough_not_to_need_counting():
    for case in CASES:
        assert word_count(case.text) <= MAX_ANSWER_WORDS, case.case_id


def test_the_two_verdict_halves_are_balanced():
    """A validator that answers the same word to everything must fail. With
    the halves equal, always-yes scores one on specificity and zero on
    sensitivity."""
    strata = stratum_counts(CASES)
    assert strata["correct_satisfied"] == strata["correct_not_satisfied"]


def test_every_defect_kind_clears_the_four_item_floor_in_both_halves():
    for half in split_cases(CASES).values():
        counts = stratum_counts(half)["discriminating_by_defect"]
        for defect in DEFECT_KINDS:
            assert counts.get(defect, 0) >= 4, (defect, counts)


def test_the_split_is_disjoint_and_covers_every_case():
    halves = split_cases(CASES)
    ids = [{c.case_id for c in half} for half in halves.values()]
    assert not (ids[0] & ids[1])
    assert ids[0] | ids[1] == {c.case_id for c in CASES}


def test_every_case_carries_the_verdict_the_registered_verifier_records():
    """The `correct` field is computed, never asserted, so a case that misses
    its intended statistic is a case with a different statistic rather than a
    wrong expectation."""
    for case in CASES:
        family = FAMILIES[case.kind]
        constraint = Constraint(case.kind, case.severity, extended=True,
                                reserve=True)
        statistic = STATISTICS[family.statistic_id](case.text)
        assert case.correct == passes(constraint, statistic, case.text)


def test_every_case_separates_at_least_one_defect_kind():
    for case in CASES:
        assert case.discriminates, case.case_id


def test_a_defect_kind_is_judged_only_in_the_arm_that_determines_it():
    """A five-word wording says nothing about segmentation or about what a
    percentage means with no words. Scoring the validator for failing to guess
    a convention would not be an audit."""
    assert ARM_OF_DEFECT["segmentation_drift"] == ARM_CONVENTIONS
    assert ARM_OF_DEFECT["vacuity_ignored"] == ARM_CONVENTIONS
    for defect in ("numerator_swap", "denominator_swap", "inequality_flip",
                   "off_by_one"):
        assert ARM_OF_DEFECT[defect] == ARM_INSTRUCTION


def test_an_unregistered_defect_kind_is_refused():
    with pytest.raises(ProtocolError):
        defect_verdict(Constraint("RF5", 3), "one, two", "make_it_wrong")


def test_the_numerator_swap_map_covers_every_registered_numerator():
    assert set(NUMERATOR_SWAP) == set(STATISTICS)
    for source, target in NUMERATOR_SWAP.items():
        assert target in STATISTICS and target != source


def test_segmentation_drift_is_the_defect_the_repository_actually_found():
    """Not a hypothetical reading: v4r2's own composition, fold-then-segment,
    which §10.2's prose-only reimplementation disagreed with."""
    source = (DCI1 / "src" / "dci1v4r4" / "stages" / "microcase.py").read_text()
    assert "alpha_runs" in source and "text.lower()" in source
    # and it must actually change a verdict somewhere in the frozen set
    assert any("segmentation_drift" in c.discriminates for c in CASES)


# -------------------------------------------------------------- the prompt

def test_the_prompt_never_carries_a_verdict_a_statistic_or_a_derivation():
    tool = _tool()
    forbidden = ("correct", "passed", "verdict", "statistic", "the checker",
                 "compliant", "faithful", "defect")
    for name, body in tool.MICROCASE_PROMPTS.items():
        lowered = body.lower()
        for token in forbidden:
            assert token not in lowered, (name, token)


def test_the_rendered_prompt_carries_only_the_instruction_and_the_answer():
    tool = _tool()
    case = next(c for c in CASES if c.text.strip()).as_dict()
    rendered = tool.render(case, ARM_INSTRUCTION)
    assert case["instruction"] in rendered and case["text"] in rendered
    assert str(case["correct"]) not in rendered.split("ANSWER")[0]
    assert case["kind"] not in rendered           # not even the family id


def test_an_empty_answer_is_rendered_empty_and_not_described():
    """A sentence saying the answer is empty would put words into the one case
    whose whole point is that there are none."""
    tool = _tool()
    case = next(c for c in CASES if not c.text.strip()).as_dict()
    rendered = tool.render(case, ARM_INSTRUCTION)
    assert "empty" not in rendered.lower().split("instruction:")[0]
    assert "[begin answer]\n\n[end answer]" in rendered


def test_the_conventions_text_is_identical_for_every_case():
    """It carries the protocol's own definitions and therefore no information
    about any one case's verdict."""
    tool = _tool()
    body = tool.MICROCASE_PROMPTS["microcase-conventions/1.0.0"]
    assert body.startswith(CONVENTIONS_TEXT)
    assert "{" not in CONVENTIONS_TEXT     # nothing per-case can be formatted in


def test_the_thresholds_are_literals_and_carry_R1s_values():
    tool = _tool()
    source = (DCI1 / "tools" / "gate1_microcase_v4r3.py").read_text()
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "THRESHOLDS")
    for value in node.value.values:
        assert isinstance(value, ast.Constant)
    for key, value in {"truncation_pooled_max": 0.10,
                       "parse_validity_min": 0.95, "specificity_min": 0.90,
                       "sensitivity_min": 0.80,
                       "sensitivity_per_kind_min": 0.50}.items():
        assert tool.THRESHOLDS[key] == value


def test_the_output_cap_fits_the_registered_judge_context():
    """R1 registered 8,192 as its contingency and the judge's context is
    4,096, so that contingency was never runnable."""
    tool = _tool()
    from dci1v4.models.registry import get_judge
    assert tool.MICROCASE_CAP < get_judge("gpt-oss-20b").max_model_len
    assert tool.assert_prompts_fit(
        [c.as_dict() for c in CASES])["estimated_tokens"] \
        < tool.PROMPT_HEADROOM_TOKENS


def test_always_answering_yes_fails_and_so_does_always_answering_no():
    tool = _tool()
    rows_yes, rows_no = [], []
    for case in CASES:
        for arm in (ARM_INSTRUCTION, ARM_CONVENTIONS):
            base = {"case_id": case.case_id, "arm": arm, "kind": case.kind,
                    "form": FAMILIES[case.kind].form,
                    "severity": case.severity, "covers": case.covers,
                    "discriminates": list(case.discriminates),
                    "correct": case.correct, "status": tool.VALID,
                    "justification": None, "truncated": False, "tokens": 1,
                    "config_hash": "x", "prompt_hash": "y"}
            rows_yes.append({**base, "label": True,
                             "agrees": case.correct is True})
            rows_no.append({**base, "label": False,
                            "agrees": case.correct is False})
    for rows in (rows_yes, rows_no):
        assert tool.verdict(tool.evaluate(rows))["outcome"] == "FAIL"
