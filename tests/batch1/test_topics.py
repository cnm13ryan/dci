"""The new topic bank: size, split, disjointness, overlap detection."""
from __future__ import annotations

import hashlib
import json

import pytest

from dci.batch1 import text as T
from dci.batch1 import topics as TOP

pytestmark = pytest.mark.cpu


@pytest.fixture(scope="module")
def bank():
    return TOP.load_bank()


@pytest.fixture(scope="module")
def split(bank):
    return TOP.split_bank(bank, pilot_topics=96, stage1_topics=32)


def test_bank_has_48_new_questions_in_each_historical_area(bank):
    assert len(bank) == 576
    areas = {}
    for t in bank:
        areas[t.area] = areas.get(t.area, 0) + 1
    assert len(areas) == 12 and set(areas.values()) == {48}
    assert all(t.topic_id.startswith("b1-") for t in bank)


def test_split_sizes_and_balance(split):
    assert split.manifest()["counts"] == {"stage1": 32, "stage2": 64,
                                          "confirmatory_reserved": 480}
    pilot = split.stage1 + split.stage2
    per_area = {}
    for t in pilot:
        per_area[t.area] = per_area.get(t.area, 0) + 1
    assert set(per_area.values()) == {8}
    stage1_areas = {t.area for t in split.stage1}
    assert len(stage1_areas) == 12


def test_split_is_disjoint_and_deterministic(bank, split):
    ids = [t.topic_id for t in split.stage1 + split.stage2 + split.confirmatory]
    assert len(ids) == len(set(ids)) == 576
    again = TOP.split_bank(list(reversed(bank)), pilot_topics=96,
                           stage1_topics=32)
    assert again.split_hash == split.split_hash
    assert split.split_of(split.confirmatory[0].topic_id) == "confirmatory"


def _skip_without_history(report):
    if report["historical_sources_missing"]:
        pytest.skip("historical bank not in this checkout")


def test_overlap_report_is_clean(bank):
    report = TOP.overlap_report(bank)
    _skip_without_history(report)
    assert report["clean"] and report["unreviewed"] == []
    assert report["exact_matches"] == [] and report["sequestered_matches"] == []
    # every historical bank: v2 576, v3 528 + 48 candidates, v4 528,
    # calibration v5 96 and v6/v7 96, and the src/dci task bank
    assert report["historical_released"] == 2096
    assert report["historical_sequestered_hashes"] == 192
    assert report["max_jaccard_historical"]["value"] < 0.5
    assert {"dci1/v2", "dci1v3", "dci1v3/candidates", "dci1v4",
            "dci/v19/task_bank"} <= set(report["historical_sources"])


def test_every_historical_bank_is_read(bank):
    released, hashes, missing = TOP._historical()
    if missing:
        pytest.skip("historical bank not in this checkout")
    by_source = {}
    for r in released:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    assert by_source["dci1/v2"] == 576 and by_source["dci1v3"] == 528
    assert by_source["dci1v4"] == 528 and by_source["dci1v3/candidates"] == 48
    task_bank = [r["question"] for r in released
                 if r["source"] == "dci/v19/task_bank"]
    assert "Explain how a pendulum clock keeps regular time." in task_bank


# The audit's examples (F4): each was a pilot or reserved question that
# restated a v2/v3 question the old check never read.
AUDIT_EXAMPLES = {
    "b1-art-and-design-00": "dci1/v2",          # perspective drawing, depth
    "b1-geography-40": "dci1/v2",               # volcanoes and earthquakes
    "b1-the-natural-world-18": "dci1/v2",       # lichens on bare rock
    "b1-everyday-science-40": "dci1/v2",        # fingers wrinkle in the bath
}


def _previous(topic_id):
    doc = json.loads(TOP.SOURCE_PATH.read_text())
    return next(r["previous_question"] for r in doc["revisions"]
                if r["topic_id"] == topic_id)


@pytest.mark.parametrize("topic_id,source", sorted(AUDIT_EXAMPLES.items()))
def test_the_audits_historical_overlaps_are_detected(bank, topic_id, source):
    old = TOP.Topic(topic_id, "x", _previous(topic_id))
    report = TOP.overlap_report([old])
    _skip_without_history(report)
    assert not report["clean"]
    assert any(p["neighbour_source"] == source and not p["reviewed"]
               for p in report["flagged_historical"])


def test_every_replaced_question_would_be_flagged_and_ids_are_kept(bank):
    doc = json.loads(TOP.SOURCE_PATH.read_text())
    ids = {t.topic_id for t in bank}
    replaced = [r for r in doc["revisions"] if r["reason"].startswith("restated")]
    assert len(replaced) >= 30 and all(r["topic_id"] in ids for r in replaced)
    old = [TOP.Topic(r["topic_id"], "x", r["previous_question"]) for r in replaced]
    report = TOP.overlap_report(old)
    _skip_without_history(report)
    flagged = {p["topic_id"] for p in report["flagged_historical"]}
    assert flagged == {r["topic_id"] for r in replaced}


def test_revisions_do_not_move_the_split(bank):
    doc = json.loads(TOP.SOURCE_PATH.read_text())
    previous = {r["topic_id"]: r["previous_question"] for r in doc["revisions"]}
    restored = [TOP.Topic(t.topic_id, t.area, previous.get(t.topic_id, t.question))
                for t in bank]
    a = TOP.split_bank(bank, pilot_topics=96, stage1_topics=32).manifest()
    b = TOP.split_bank(restored, pilot_topics=96, stage1_topics=32).manifest()
    for group in ("stage1", "stage2", "confirmatory_reserved"):
        assert a[group] == b[group]
    assert a["bank_hash"] != b["bank_hash"]


def test_a_review_decision_is_bound_to_the_question_text(bank):
    review = TOP.load_review()
    (tid, source, nid), decision = next(item for item in sorted(review.items())
                                        if item[0][1] != "batch1")
    topic = next(t for t in bank if t.topic_id == tid)
    edited = TOP.Topic(tid, topic.area, topic.question[:-1] + " ?")
    report = TOP.overlap_report([edited])
    _skip_without_history(report)
    pairs = [p for p in report["flagged_historical"] if p["neighbour_id"] == nid]
    assert pairs and not any(p["reviewed"] for p in pairs)
    assert not report["clean"]


def test_overlap_detection_catches_reuse_of_a_historical_question(bank):
    path, _ = TOP.HISTORICAL_SOURCES["dci1v4"]
    hist = json.loads(path.read_text())[0]
    reused = TOP.Topic("b1-x-99", hist["area"], hist["question"])
    report = TOP.overlap_report(list(bank) + [reused])
    assert not report["clean"] and report["exact_matches"] == ["b1-x-99"]
    with pytest.raises(ValueError, match="overlaps"):
        TOP.assert_clean(report)


def test_overlap_detection_catches_a_sequestered_question(bank, monkeypatch):
    secret = "How do bridges carry heavy loads safely?"
    real = TOP._historical

    def with_secret():
        released, hashes, missing = real()
        return released, hashes | {hashlib.sha256(secret.encode()).hexdigest()}, missing
    monkeypatch.setattr(TOP, "_historical", with_secret)
    report = TOP.overlap_report([TOP.Topic("b1-x-1", "x", secret)])
    assert report["sequestered_matches"] == ["b1-x-1"]


def test_overlap_detection_catches_near_duplicates_within_the_bank(bank):
    a = TOP.Topic("b1-x-1", "x", "Why do rivers bend into wide loops?")
    b = TOP.Topic("b1-x-2", "x", "Why do rivers bend into loops?")
    report = TOP.overlap_report([a, b])
    assert report["flagged_internal"] and not report["clean"]
    assert report["unreviewed"] == ["b1-x-1~batch1:b1-x-2"]


def test_a_missing_historical_source_makes_the_report_unclean(monkeypatch, bank):
    path = TOP.SEQUESTERED_SOURCES["dci1v3/sequestered"]
    monkeypatch.setitem(TOP.SEQUESTERED_SOURCES, "dci1v3/sequestered",
                        path.with_name("missing.json"))
    report = TOP.overlap_report(bank[:3])
    assert not report["clean"]
    assert report["historical_sources_missing"] == ["dci1v3/sequestered"]


def test_hygiene_is_clean_and_profiles_every_set(bank, split):
    report = TOP.hygiene_report(bank, split)
    assert report["clean"]
    assert set(report["profiles"]) == {"stage1", "stage2",
                                       "confirmatory_reserved"}
    assert report["profiles"]["stage1"]["n"] == 32
    assert "however" in report["library_words_checked"]
    assert "the" not in report["library_words_checked"]


@pytest.mark.parametrize("question,field", [
    ("Why do gardeners water a garden at dusk?", "library_word_leaks"),
    ("Why do people say however so often?", "library_word_leaks"),
    ("Explain why rivers bend.", "instruction_like"),
    ("Why do rivers bend? Answer in 50 words?", "instruction_like"),
    ("Rivers bend for many reasons?", "not_a_single_interrogative_line"),
])
def test_hygiene_flags_leaks_commands_and_form(split, question, field):
    report = TOP.hygiene_report([TOP.Topic("b1-x-1", "x", question)], split)
    assert not report["clean"] and report[field]


def test_split_refuses_a_bank_it_cannot_reserve_from(bank):
    with pytest.raises(ValueError):
        TOP.split_bank(bank[:48], pilot_topics=96, stage1_topics=32)


# --------------------------------------------- re-audit R1: paraphrases

#: The restatements the re-audit named (R1): 5 pilot, 6 reserved.
REAUDIT_R1 = ("b1-everyday-science-03", "b1-everyday-science-04",
              "b1-history-28", "b1-technology-20", "b1-food-42",
              "b1-everyday-science-41", "b1-everyday-science-02",
              "b1-everyday-science-40", "b1-sport-13", "b1-history-19",
              "b1-music-44")


def _r1_revisions():
    doc = json.loads(TOP.SOURCE_PATH.read_text())
    return [r for r in doc["revisions"] if "R1" in r["reason"]
            or "semantic sweep" in r["reason"]]


def test_every_reaudit_restatement_was_rewritten_and_would_be_caught(bank):
    """Each old question is RESTATEMENT in the semantic review, so putting
    it back in the bank makes the report unclean."""
    revised = {r["topic_id"]: r["previous_question"] for r in _r1_revisions()}
    assert set(REAUDIT_R1) <= set(revised)
    current = {t.topic_id: t.question for t in bank}
    for tid in REAUDIT_R1:
        assert current[tid] != revised[tid]
    old = [TOP.Topic(tid, "x", revised[tid]) for tid in REAUDIT_R1]
    report = TOP.overlap_report(old)
    assert sorted(report["semantic_review"]["restatements_still_in_bank"]) \
        == sorted(REAUDIT_R1)
    assert not report["clean"]


def test_the_rare_stem_screen_sees_what_jaccard_missed():
    old = TOP.Topic("b1-everyday-science-02", "x",
                    "Why does a kernel of popcorn burst open when heated?")
    report = TOP.overlap_report([old])
    _skip_without_history(report)
    hits = [p for p in report["flagged_historical"]
            if "popcorn" in p["neighbour"].lower()]
    assert hits and all(p["wordset_jaccard"] < TOP.WORDSET_SCREEN
                        and p["content_jaccard"] < TOP.CONTENT_SCREEN
                        for p in hits)
    assert {"burst", "popcorn"} <= set(hits[0]["rare_shared"])


def test_a_semantic_restatement_left_in_the_bank_is_unclean(bank, tmp_path,
                                                             monkeypatch):
    t = bank[0]
    review = tmp_path / "semantic.json"
    review.write_text(json.dumps({"findings": [{
        "topic_id": t.topic_id, "verdict": "RESTATEMENT",
        "question_sha256": TOP._question_hash(t.question)}]}))
    monkeypatch.setattr(TOP, "SEMANTIC_REVIEW_PATH", review)
    report = TOP.overlap_report([t])
    assert report["semantic_review"]["restatements_still_in_bank"] == \
        [t.topic_id]
    assert not report["clean"]


def test_r1_rewrites_keep_ids_areas_split_and_question_form(bank):
    revisions = _r1_revisions()
    assert len({r["topic_id"] for r in revisions}) == 88
    by_id = {t.topic_id: t for t in bank}
    for r in revisions:
        new = by_id[r["topic_id"]].question
        assert r["previous_sha256"] == TOP._question_hash(r["previous_question"])
        assert new.split()[0] == r["previous_question"].split()[0]
        assert abs(T.word_count(new) - T.word_count(r["previous_question"])) <= 3
    split = TOP.split_bank(bank, pilot_topics=96, stage1_topics=32)
    hygiene = TOP.hygiene_report(bank, split)
    assert hygiene["clean"] and TOP.overlap_report(bank)["clean"]
