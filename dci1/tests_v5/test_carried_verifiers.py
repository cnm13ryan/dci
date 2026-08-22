"""B. The carried instrument layer, measured against v4r4 (§10.2, §30)."""
from __future__ import annotations

import pytest

from dci1v4.errors import InstrumentError, ProtocolError
from dci1v5.protocol import wordings as W
from dci1v5.verifiers import (
    boundary, carryover, constraints as K, independent, statistics as S,
    witnesses, words,
)
from dci1v5.verifiers.realistic_witness import run_realistic_suite


def test_the_word_rule_segments_then_folds():
    assert S.words_lower("İstanbul is big") == ["i̇stanbul", "is", "big"]
    assert len(S.alpha_runs("İstanbul is big")) == 3


def test_exactly_one_character_splits_under_fold_then_segment():
    assert words.assert_single_splitter() == "İ"


def test_a_counts_its_own_way_and_the_markers_count_theirs():
    text = "However however HOWEVER thus Thus."
    assert S.s0_count(text) == 3
    assert S.statistic_of("marker_thus", text) == 2


def test_every_carried_numerator_agrees_with_v4r4():
    """§30's first MEASURED invariant, over the whole frozen corpus."""
    finding = carryover.assert_statistics_agree_with_v4r4()
    assert finding["measured"] is True
    assert finding["agreement"] == 1.0
    assert finding["comparisons"] > 2000
    assert set(finding["not_carried"]) == set(K.NEW_STATISTIC_IDS)


def test_the_primary_and_the_reimplementation_agree_on_every_marker():
    text = ("Though whereas thus; indeed, namely instead overall hence. "
            "Thusly hencewise thoughtful.")
    for statistic_id in K.MARKER_STATISTIC_IDS:
        assert S.statistic_of(statistic_id, text) == \
            independent.statistic(statistic_id, text)


def test_the_boundary_suite_reproduces_every_frozen_expectation():
    result = boundary.evaluate_suites()
    assert result["failures"] == []
    assert result["agreement"] == 1.0
    assert result["checked"] > 2000
    assert result["instruments"] == 650


def test_the_corpus_covers_the_four_marker_phenomena():
    coverage = boundary.assert_coverage()
    assert coverage["authored_v5"] >= 4
    assert set(coverage["marker_phenomena"]) == {
        "marker-embedded-in-longer-word", "marker-adjacent-to-punctuation",
        "marker-capitalised-at-sentence-start", "marker-hyphenated"}


def test_the_frozen_marker_expectations_reproduce():
    """tools/v5_freeze_marker_boundary.py --check, as a test."""
    import subprocess
    import sys
    from pathlib import Path

    tool = Path(__file__).resolve().parents[1] / "tools" \
        / "v5_freeze_marker_boundary.py"
    out = subprocess.run([sys.executable, str(tool), "--check"],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_the_witness_suite_discharges_every_realisable_pair():
    result = witnesses.run_witness_suite()
    assert result["pairs"] > 20_000
    assert result["joint_satisfiability_failures"] == []
    assert result["non_entailment_failures"] == []


def test_the_filler_is_feature_free_for_every_registered_numerator():
    counts = witnesses.assert_filler_is_feature_free()
    assert set(counts) == set(K.STATISTIC_IDS)
    assert all(v == 0 for k, v in counts.items() if k != "sentence")


def test_a_marker_words_collateral_features_cannot_share_a_cell():
    """`whereas` contains an `a`; RF7 is Tier 3 and never shares its cell."""
    tolerated = witnesses.assert_feature_words_are_specific()
    assert "letter_a" in tolerated["marker_whereas"]
    with pytest.raises(InstrumentError):
        witnesses.assert_pair_realisable(K.Constraint("MK4", 3),
                                         K.Constraint("RF7", 4))


def test_the_realistic_witness_finds_cl7s_top_reserve_unreachable():
    """§7.7's registered finding, computed rather than asserted."""
    report = run_realistic_suite(["CL7", "MK1", "XC1", "XC3"])
    assert report["unreachable"] == {"CL7": [125, 130, 135, 140]}


def test_cl7_80_is_reachable_and_the_correction_is_recorded():
    """An earlier draft justified §7.7 with CL7:80; the records contradict it."""
    report = run_realistic_suite(["CL7"])
    reachable = {v["candidate"] for v in report["verdicts"]
                 if v["realistic_at"]}
    assert "CL7:80" in reachable


def test_every_wording_is_severity_invariant_and_inside_the_caliper():
    W.assert_severity_invariance()
    W.assert_rule_vocabulary()
    feasible = W.assert_caliper_feasible()
    assert set(feasible) == set(K.FAMILIES)


def test_the_tier_one_wordings_are_as_own_with_the_marker_substituted():
    a = W.wordings("A", 3)
    mk = W.wordings("MK3", 3)
    for one, other in zip(a, mk):
        assert other == one.replace("however", "though")


def test_b_renders_over_the_widened_grid_and_the_extension():
    for m in K.focal_severities(extended=True):
        assert str(m) in W.wordings("B", m)[0]
    with pytest.raises(ProtocolError):
        W.wordings("B", 17)


def test_the_carry_over_record_names_what_is_not_carried():
    record = carryover.carry_over_record()
    assert record["classification"] == "REUSED_IMPLEMENTATION"
    assert record["all_measured_invariants_passed"] is True
    assert set(K.NEW_STATISTIC_IDS) <= set(record["not_carried"])
    # the five asserted invariants are UNVERIFIED without an artifact record
    assert len(record["unverified"]) == 5


def test_a_drifted_stored_wording_is_refused():
    good = [{"kind": "MK1", "severity": 3, "wording_index": 0,
             "constraint_sentence": W.wording("MK1", 0, 3)}]
    assert carryover.assert_wordings_match_stored(good)["rows_checked"] == 1
    bad = [{"kind": "MK1", "severity": 3, "wording_index": 0,
            "constraint_sentence": "Use the word thus exactly 4 times."}]
    with pytest.raises(ProtocolError):
        carryover.assert_wordings_match_stored(bad)
