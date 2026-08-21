"""What a blinded review packet may never carry, and what its report may never
claim.

The v3 record's 56-item review is the strongest evidence this programme has
that the verifiers measure what the instructions mean --- and every one of its
items was `solo:A:n`. This packet exists to anchor the ten families §7.0-R3
added, which have none. The things that make it worth anything are the things
an edit could quietly remove: the reviewer must not be told the instrument, the
review command must not be able to read the key, the verdicts must stay
balanced, and the report must not describe an author's labels as independent
validation.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v4r4.stages.human_review import (
    KEY_ONLY_FIELDS, LABELS, PACKET_FIELDS, agreement_report,
    assert_packet_blinded, build_packet, candidates, select, wilson_upper,
)
from dci1v4r4.stages.microcase import DEFECT_KINDS, split_cases, build_cases
from dci1v4r4.verifiers.constraints import FAMILIES, R3_FAMILY_IDS

DCI1 = Path(__file__).resolve().parents[1]
BUILT = build_packet(25)


def test_the_packet_carries_only_the_instruction_and_the_answer():
    for item in BUILT["packet"]:
        assert set(item) == set(PACKET_FIELDS)


def test_no_item_id_names_the_family_it_came_from():
    """`mc-rf9-03-...` names the numerator in its second field, and the id is
    the one string the reviewer sees for every item."""
    assert_packet_blinded(BUILT["packet"])
    for item in BUILT["packet"]:
        for family in FAMILIES:
            assert family.lower() not in item["item_id"].lower()


def test_a_packet_carrying_a_key_field_is_refused():
    leaky = [{**BUILT["packet"][0], "verdict": "SATISFIES"}]
    with pytest.raises(ProtocolError):
        assert_packet_blinded(leaky)


def test_every_added_numerator_is_represented():
    statistics = {FAMILIES[k].statistic_id for k in R3_FAMILY_IDS}
    assert set(BUILT["statistics"]) == statistics


def test_only_families_the_amendment_added_are_drawn():
    families = {e["family"] for e in BUILT["key"]}
    assert families <= set(R3_FAMILY_IDS)


def test_the_held_out_half_of_the_autorater_pathway_is_untouched():
    """Drawing a held-out item would spend the autorater's calibration
    material on a different pathway."""
    held_out = {c.case_id for c in split_cases(build_cases())["calibration"]}
    assert not {e["case_id"] for e in BUILT["key"]} & held_out


def test_the_verdicts_are_balanced_to_within_one():
    """A reviewer who answers SATISFIES to everything must score near one
    half, not near one."""
    assert abs(BUILT["satisfies"] - BUILT["violates"]) <= 1


def test_every_defect_kind_is_separated_by_some_item():
    assert set(BUILT["defects_separated"]) == set(DEFECT_KINDS)


def test_the_selection_is_deterministic():
    assert build_packet(25)["packet_hash"] == BUILT["packet_hash"]
    assert build_packet(25)["key_hash"] == BUILT["key_hash"]


def test_the_scarce_verdict_is_not_squeezed_out():
    """`semicolon` has one satisfying case in the whole pool. A rule that
    alternated blindly would drop it."""
    pool = candidates()
    scarce = [c for c in pool
              if FAMILIES[c.kind].statistic_id == "semicolon" and c.correct]
    assert len(scarce) == 1
    chosen = {c.case_id for c in select(pool, items=25)}
    assert scarce[0].case_id in chosen


# ------------------------------------------------------------ the statistic

def test_the_wilson_bound_is_section_10_3s_own_and_25_items_clears_it():
    assert wilson_upper(0, 24) > 0.10
    assert wilson_upper(0, 25) <= 0.10
    assert wilson_upper(1, 25) > wilson_upper(0, 25)


def test_unsure_is_coverage_and_is_neither_agreement_nor_disagreement():
    key = BUILT["key"]
    labels = {e["item_id"]: "UNSURE" for e in key}
    report = agreement_report(key, labels)
    assert report["compared"] == 0 and report["unsure"] == len(key)
    assert report["agreement"] is None


def test_answering_one_label_to_everything_cannot_look_like_agreement():
    key = BUILT["key"]
    for label in ("SATISFIES", "VIOLATES"):
        report = agreement_report(key, {e["item_id"]: label for e in key})
        assert 0.4 <= report["agreement"] <= 0.6
        assert not report["meets_threshold_numerically"]


def test_a_perfect_review_is_reported_as_not_a_section_10_3_pass():
    key = BUILT["key"]
    report = agreement_report(key, {e["item_id"]: e["verdict"] for e in key})
    assert report["agreement"] == 1.0
    assert report["wilson_upper_on_disagreement"] <= 0.10
    assert "never described as independent validation" in report["standing"]
    assert "does not write a measurement basis" in report["standing"]
    assert "not a §10.3 pass" in report["scope"]


def test_the_report_names_the_discordant_items_with_what_they_separate():
    key = BUILT["key"]
    flipped = {e["item_id"]: ("VIOLATES" if e["correct"] else "SATISFIES")
               for e in key[:2]}
    flipped.update({e["item_id"]: e["verdict"] for e in key[2:]})
    report = agreement_report(key, flipped)
    assert report["disagreements"] == 2
    assert all("separates" in row for row in report["discordant"])


# --------------------------------------------------------------- the tool

def _tool_source() -> ast.Module:
    return ast.parse((DCI1 / "tools" / "v4r3_human_review.py").read_text())


def test_the_review_command_cannot_reach_the_key():
    """Structural. The reveal happens in `report` and nowhere else."""
    tree = _tool_source()
    review = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "cmd_review")
    names = {n.id for n in ast.walk(review) if isinstance(n, ast.Name)}
    assert "KEY" not in names


def test_the_review_command_refuses_a_pipe():
    source = (DCI1 / "tools" / "v4r3_human_review.py").read_text()
    assert "sys.stdin.isatty()" in source


def test_the_labels_match_the_v3_review_vocabulary():
    """So the two reviews are comparable item for item."""
    assert LABELS == ("SATISFIES", "VIOLATES", "UNSURE")


def test_key_only_fields_include_everything_that_names_the_instrument():
    for field in ("family", "statistic", "severity", "correct", "verdict",
                  "discriminates", "case_id"):
        assert field in KEY_ONLY_FIELDS
