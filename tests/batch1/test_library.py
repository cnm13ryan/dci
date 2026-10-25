"""The 51-candidate library: completeness, schema, rejection of bad
specifications, wording frames and determinism."""
from __future__ import annotations

import json

import pytest

from dci.batch1 import library as L
from dci.batch1 import verifiers as V
from tests.batch1.conftest import historical_source, string_constants

pytestmark = pytest.mark.cpu


def test_the_library_has_51_variants_in_seven_operation_classes():
    refs = L.reference_library()
    summary = L.validate_library()
    assert len(refs) == 51 == summary["n_variants"]
    assert summary["n_operations"] == 7
    assert {c.operation for c in refs} == set(L.OPERATIONS)


def test_family_rows_match_the_design_table():
    rows: dict = {}
    for c in L.reference_library():
        key = (c.operation, c.family.design_row)
        rows[key] = rows.get(key, 0) + 1
    assert rows == L.PLANNED_FAMILY_COUNTS


def test_exact_word_count_grid_is_the_design_grid_and_excludes_however():
    grid = sorted((c.p["word"], c.p["n"]) for c in L.reference_library()
                  if c.family_id == "exact_word_count")
    assert len(grid) == 22
    assert ("however", 2) not in grid
    assert {w for w, _ in grid} == {"indeed", "instead", "perhaps", "although",
                                    "moreover", "therefore", "nonetheless",
                                    "consequently"}
    assert [n for w, n in grid if w == "nonetheless"] == [2, 4]


def test_every_variant_has_a_verifier_both_frames_and_a_complete_spec():
    required = {"cid", "operation", "object_type", "family_id", "params",
                "semantic_spec", "wording", "verifier_id",
                "verifier_implementation_hash", "applicability",
                "non_vacuity", "empty_response", "truncated_response",
                "provenance", "status"}
    for c in L.all_constraints():
        spec = c.spec()
        assert required <= set(spec), c.cid
        assert spec["verifier_id"] in V.VERIFIERS
        assert set(spec["wording"]) == set(L.FRAMES)
        assert spec["wording"]["F0"] != spec["wording"]["F1"]
        assert len(c.spec_hash) == 64


def test_proposed_and_prescribed_status_is_explicit():
    status = {c.cid: c.status for c in L.reference_library()}
    assert sum(s == L.STATUS_PRESCRIBED for s in status.values()) == 22
    assert sum(s == L.STATUS_PROPOSED for s in status.values()) == 29
    assert all(c.status == L.STATUS_PRESCRIBED
               for c in L.a_candidates() + L.b_candidates())


def test_a_and_b_wordings_are_the_historical_strings():
    v8 = historical_source("dci1/src/dci1v8dev/wording_v8.py")
    v4 = historical_source("dci1/src/dci1v4/protocol/wordings.py")
    a4 = {c.p["n"]: c for c in L.a_candidates()}[4]
    assert a4.render("F0") == "Use the word however exactly 4 times."
    assert a4.render("F1") == \
        "Your answer must contain the word however exactly 4 times."
    assert '"Use the word {X} exactly {q} time{s}."' in v8
    assert '"Your answer must contain the word {X} exactly {q} time{s}."' in v8
    b9 = {c.p["m"]: c for c in L.b_candidates()}[9]
    assert b9.render("F0") == "Use only words of 9 letters or fewer."
    assert b9.render("F1") == "Every word in the answer must have at most 9 letters."
    assert 'f"Use only words of {m} letters or fewer."' in v4
    assert 'f"Every word in the answer must have at most {m} letters."' in v4


def test_grammatical_number_follows_the_count():
    by_id = L.constraint_by_id()
    assert by_id["ec.semicolon.1"].render("F0") == "Use exactly 1 semicolon."
    assert by_id["ec.semicolon.2"].render("F0") == "Use exactly 2 semicolons."


def _c(**overrides):
    base = dict(cid="x", role=L.ROLE_REFERENCE, family_id="exact_word_count",
                params=(("n", 2), ("word", "indeed")),
                status=L.STATUS_PROPOSED, provenance="test")
    base.update(overrides)
    return L.Constraint(**base)


@pytest.mark.parametrize("overrides", [
    {"family_id": "no_such_family"},
    {"role": "focal"},
    {"status": "approved"},
    {"provenance": ""},
    {"params": (("word", "indeed"), ("n", 2))},          # unsorted
    {"params": (("n", 2),)},                             # missing word
    {"params": (("n", 0), ("word", "indeed"))},          # non-positive
    {"params": (("n", 2), ("word", "Indeed"))},          # not lower case
    {"params": (("n", True), ("word", "indeed"))},       # bool is not int
    {"family_id": "include_words", "params": (("words", ("a", "a")),)},
    {"family_id": "forbid_letter", "params": (("letter", "ab"),)},
    {"family_id": "length_order",
     "params": (("direction", "sideways"), ("min_sentences", 4))},
    {"family_id": "chain_word", "params": (("min_sentences", 1),)},
    {"family_id": "exact_char_count", "params": (("char", "!"), ("n", 1))},
])
def test_invalid_specifications_are_rejected(overrides):
    with pytest.raises(L.LibraryError):
        _c(**overrides)


def test_the_focal_word_cannot_be_a_reference_target():
    bad = _c(params=(("n", 2), ("word", "however")))
    with pytest.raises(L.LibraryError, match="focal word"):
        L.validate_library([bad], expect_design_counts=False)


def test_an_incomplete_library_is_rejected():
    with pytest.raises(L.LibraryError, match="family counts"):
        L.validate_library(L.reference_library()[:-1])


def test_a_family_without_both_frames_is_rejected():
    with pytest.raises(L.LibraryError, match="frames"):
        L.Family("f", "exact_count", "word", "row", "b1.exact_word_count",
                 "forced_production", {"one": {"F0": "x"}}, "s", "any")


def test_wordings_name_every_parameter_in_both_frames():
    for c in L.reference_library():
        for frame in L.FRAMES:
            text = c.render(frame)
            for token in L._parameter_tokens(c):
                assert token in text, (c.cid, frame, token)


def test_frames_only_change_rendering_never_scoring():
    for c in L.all_constraints():
        spec = c.spec()
        assert "frame" not in json.dumps(spec["params"])
        assert spec["verifier_id"] == c.family.verifier_id


def test_manifest_and_hash_are_deterministic_and_parameter_sensitive():
    assert L.library_hash() == L.library_hash()
    a = _c()
    b = _c(params=(("n", 4), ("word", "indeed")))
    assert a.spec_hash != b.spec_hash
    assert a.spec_hash == _c().spec_hash


def test_prompt_template_is_carried_from_dci1v7():
    from dci.batch1 import config as CFG
    src = historical_source("dci1/src/dci1v7/protocol/constants.py")
    carried = string_constants(src, ("STEM_SENTENCE", "PROMPT_ZERO",
                                     "PROMPT_ONE"))
    assert carried == {"STEM_SENTENCE": CFG.STEM_SENTENCE,
                       "PROMPT_ZERO": CFG.PROMPT_ZERO,
                       "PROMPT_ONE": CFG.PROMPT_ONE}
