"""A and MK1-MK8 are one marker counter (§9.2; unified 2026-08-29).

The asymmetry this closes: A's counter was ``dci1v4.verifiers.target
.s0_count`` --- lower-case the whole response, then segment --- while the
eight marker counters segmented first and lower-cased each word. The two
orders differ on U+0130 alone. Every test here is a structural statement of
the identity, an edge-case regression the shared implementation must
satisfy, or a measured statement about what the change did to stored
evidence (nothing).
"""
from __future__ import annotations

import tempfile

import inspect
import json
import random
from pathlib import Path

import pytest

from dci1v4.verifiers.target import s0_count as fold_then_segment_s0
from dci1v7.stages import specification
from dci1v7.verifiers import boundary, independent, words
from dci1v7.verifiers import constraints as K
from dci1v7.verifiers import statistics as S

DCI1 = Path(__file__).resolve().parents[1]
MARKERS = {**{word: statistic_id for statistic_id, word
              in K.MARKER_WORDS.items()},
           K.TARGET_WORD: "s0"}


def _primary(word: str, text: str) -> int:
    return S.s0_count(text) if word == K.TARGET_WORD else \
        S.statistic_of(MARKERS[word], text)


def _reimplementation(word: str, text: str) -> int:
    return independent.s0(text) if word == K.TARGET_WORD else \
        independent.statistic(MARKERS[word], text)


# ------------------------------------------------------------ the identity

def test_s0_is_the_marker_counter_with_a_s_word_by_construction():
    assert "marker_count(text, TARGET_WORD)" in inspect.getsource(S.s0_count)
    for text in ("however", "However, however!", "İhowever", "thus however"):
        assert S.s0_count(text) == S.marker_count(text, K.TARGET_WORD)


def test_every_marker_statistic_is_the_same_counter():
    text = "Thus, hence; though whereas INDEED namely instead overall thus."
    for statistic_id, word in K.MARKER_WORDS.items():
        assert S.statistic_of(statistic_id, text) == S.marker_count(text, word)
        assert S.STATISTICS[statistic_id].__name__ == f"count_{word}"


def test_no_v7_module_takes_a_s_counter_from_v4():
    """S1 and S2 may still come from ``dci1v4.verifiers.target``; S0 may not."""
    offenders = []
    for path in sorted((DCI1 / "src" / "dci1v7").rglob("*.py")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith(("from dci1v4.verifiers.target import",
                                    "import dci1v4.verifiers.target")) \
                    and "s0_count" in stripped:
                offenders.append(f"{path.name}: {stripped}")
    assert offenders == []


# ------------------------------------------------------- edge-case table
#: (text, marker word, expected count under the shared counter)
CASES = [
    # case: lower, upper, mixed
    ("however", "however", 1), ("However", "however", 1),
    ("HOWEVER", "however", 1), ("hOwEvEr", "however", 1),
    ("Thus", "thus", 1), ("THUS thus Thus", "thus", 3),
    # punctuation adjacent to the marker
    ("However, however. (however) 'however' \"however\"", "however", 5),
    ("thus; hence: thus!", "thus", 2), ("...hence...", "hence", 1),
    # hyphens split a word
    ("how-ever", "however", 0), ("over-all", "overall", 0),
    ("well-known however", "however", 1),
    # apostrophes split a word
    ("however's", "however", 1), ("thus'", "thus", 1),
    ("'tis however", "however", 1),
    # digits split a word
    ("however1", "however", 1), ("1however", "however", 1),
    ("how3ever", "however", 0), ("thus2thus", "thus", 2),
    # substrings and superstrings do not count
    ("howevers", "however", 0), ("whichever", "however", 0),
    ("nevertheless", "hence", 0), ("thusly", "thus", 0),
    ("although", "though", 0), ("whereas", "where", 0),
    # U+0130: one run, and the folded run is not the marker
    ("İhowever", "however", 0), ("İthus", "thus", 0),
    ("however İ", "however", 1), ("İstanbul thus", "thus", 1),
    ("howeverİ", "however", 0), ("İhowever however", "however", 1),
    # combining marks (category Mn) end a run
    ("howéver", "however", 0), ("howeveŕ", "however", 1),
    ("thuṡ thus", "thus", 2), ("ẗhus", "thus", 0),
    # zero-width separators (category Cf) end a run
    ("how\u200bever", "however", 0), ("however\u200bthus", "however", 1),
    ("however\u200bthus", "thus", 1), ("how‍ever", "however", 0),
    ("﻿however", "however", 1), ("thus⁠", "thus", 1),
    # full-width letters are letters, but not these letters; full-width
    # digits are not letters and split
    ("ｈｏｗｅｖｅｒ", "however", 0), ("ＨＯＷＥＶＥＲ", "however", 0),
    ("however１however", "however", 2), ("ｔｈｕｓ thus", "thus", 1),
    # a character that folds to an ASCII letter (KELVIN SIGN -> k) is
    # folded per run like any other; no marker carries a k
    ("Keep thus", "thus", 1),
    # other scripts adjacent
    ("однако however", "however", 1), ("しかし however", "however", 1),
    # empty and blank
    ("", "however", 0), ("   ", "however", 0), ("\n\t", "thus", 0),
]


@pytest.mark.parametrize("text,word,expected", CASES)
def test_the_shared_counter_on_the_edge_cases(text, word, expected):
    assert S.marker_count(text, word) == expected
    if word in MARKERS:
        assert _primary(word, text) == expected
        assert _reimplementation(word, text) == expected


@pytest.mark.parametrize("text,word,expected", CASES)
def test_the_orders_agree_exactly_when_u0130_is_absent(text, word, expected):
    """The pre-unification A rule, on the same texts: identical unless the
    text carries U+0130, and then only where the character is embedded."""
    if word != K.TARGET_WORD:
        return
    old = fold_then_segment_s0(text)
    if "İ" not in text:
        assert old == expected
    elif text in ("İhowever", "İhowever however"):
        assert old == expected + 1          # the split that the fold makes
    else:
        assert old == expected


def test_the_existing_a_and_marker_behaviour_is_unchanged():
    text = "However however HOWEVER thus Thus."
    assert S.s0_count(text) == 3
    assert S.statistic_of("marker_thus", text) == 2
    for case in boundary.ALL_CASES:
        assert S.s0_count(case["text"]) == fold_then_segment_s0(case["text"])


def test_a_fuzz_over_unicode_finds_no_separation_without_u0130():
    pool = ["however", "However", "HOWEVER", "thus", "Thus", "hence", "though",
            "whereas", "indeed", "namely", "instead", "overall", "a", "the",
            " ", " ", ",", ".", ";", "-", "'", "1", "é", "ß", "ẞ", "Σ", "σ",
            "ς", "ж", "Ж", "日", "😀", "\u200b", "́", "K", "ｈ",
            "Ｈ", "１", "﻿", "\n"]
    rng = random.Random(0)
    for _ in range(3000):
        text = "".join(rng.choice(pool) for _ in range(rng.randint(1, 30)))
        for word in MARKERS:
            assert S.marker_count(text, word) == \
                sum(1 for run in S.alpha_runs(text.lower()) if run == word)


# ---------------------------------------------------- the scope argument

def test_u0130_is_the_only_character_the_two_orders_can_separate():
    assert words.assert_single_splitter() == "İ"
    changes = [cp for cp in range(0x110000)
               if chr(cp).isalpha() != all(c.isalpha()
                                           for c in chr(cp).lower())]
    assert changes == [0x130]
    gained = [cp for cp in range(0x110000)
              if not chr(cp).isalpha()
              and any(c.isalpha() for c in chr(cp).lower())]
    assert gained == []


# ---------------------------------------- the frozen corpus and the readings

def test_the_carried_v3_target_expectations_reproduce_under_the_shared_counter():
    cases = [c for c in boundary.CARRIED_TARGET_CASES if "s0" in c]
    assert len(cases) == 48
    for case in cases:
        assert S.s0_count(case["text"]) == case["s0"], case["case_id"]


def test_the_reimplementation_agrees_with_the_shared_counter_on_the_corpus():
    for case in boundary.ALL_CASES:
        assert independent.s0(case["text"]) == S.s0_count(case["text"])
        for statistic_id in K.MARKER_STATISTIC_IDS:
            assert independent.statistic(statistic_id, case["text"]) == \
                S.statistic_of(statistic_id, case["text"])


def test_a_s_segmentation_drift_reading_is_the_fold_first_order():
    """The defect reading for A is v4r2's composition, the same reading every
    family and B are audited against, and it is separable on U+0130."""
    assert S.s0_count("İhowever") == 0
    assert fold_then_segment_s0("İhowever") == 1
    assert specification.reading_verdict(
        "A", 1, "İhowever", "segmentation_drift") is True
    assert specification.reading_verdict(
        "A", 1, "however", "segmentation_drift") is True
    assert specification.reading_verdict("A", 1, "however", "off_by_one") \
        is False


# ------------------------------------------------------- stored evidence

def test_the_stored_evidence_audit_found_no_row_the_unification_moves():
    """``tools/v7_marker_counter_rescore_audit.py`` over every scored row of
    every evidence root, v4r3 through the v7 development rehearsals."""
    path = DCI1 / "reports/dci1v7/development" \
        / "marker_counter_unification_audit.json"
    report = json.loads(path.read_text())
    assert report["summary"] == {
        "A_statistics_changed": 0, "A_verdicts_changed": 0,
        "MK_statistics_changed": 0, "MK_verdicts_changed": 0}
    assert report["totals"]["rows_with_u0130"] == 0
    assert report["totals"]["reproduction_mismatches"] == 0
    assert report["totals"]["rows"] >= 3_500_000
    assert report["totals"]["entries_checked"] >= 165_000_000
    assert report["changed_rows"] == []
    assert report["read_only"] is True


def test_the_rescore_audit_finds_the_splitter_under_both_json_writers():
    """The audit's detection must not depend on which writer stored the row.

    Two writers in this repository disagree about escaping: `dci1v4.engine.fs`
    and `.store` dump with ``ensure_ascii=False``, so U+0130 is stored as its
    UTF-8 bytes; `dci1v7.run.execute` takes ``json.dumps``' default
    ``ensure_ascii=True`` and stores it as the ASCII escape ``\\u0130``. The
    audit originally searched the raw bytes, which finds the first and can
    never find the second -- so every v7-written file reported zero rows
    containing the splitter whether or not it held any, and the same flag
    gated the recompute skip.
    """
    import subprocess
    import sys
    from pathlib import Path

    tool = Path(__file__).resolve().parents[1] / "tools" / \
        "v7_marker_counter_rescore_audit.py"
    row = {"raw_response": "İhowever", "scores": [
        {"kind": "A", "severity": 1, "statistic": 1, "passed": True,
         "graded": 1.0}]}
    with tempfile.TemporaryDirectory() as tmp:
        evidence = Path(tmp) / "evidence"
        lane = evidence / "dci1v7" / "model" / "STAGE" / "backend_runs" / "lane"
        lane.mkdir(parents=True)
        # the same row under each writer's escaping convention
        (lane / "scored.jsonl").write_text(
            json.dumps(row, sort_keys=True) + "\n"                    # v7
            + json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        out = Path(tmp) / "audit.json"
        subprocess.run(
            [sys.executable, str(tool), "--evidence", str(evidence),
             "--roots", "dci1v7", "--out", str(out), "--workers", "1"],
            check=True, capture_output=True)
        report = json.loads(out.read_text())
    # both rows carry the splitter; a byte search would have found only one
    assert report["totals"]["rows"] == 2
    assert report["totals"]["rows_with_u0130"] == 2, report["totals"]
