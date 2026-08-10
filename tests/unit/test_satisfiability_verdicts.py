"""A `hard` verdict is a proof; a heuristic is a flag.

These tests are deliberately registry-independent: they exercise the deduction
rules on synthetic specs so that the LOGIC is pinned separately from the live
constraint identifiers (which tests/unit/test_satisfiability.py pins once the
registry exists). Every case here answers one question - does the rule state
something that is true of the whole admissible text space, or only of ordinary
English prose?
"""
import pytest

from dci.constraints.satisfiability import (BLOCKING_VERDICTS, VERDICT_KINDS,
                                            audit_pairs, corpus_witness,
                                            pair_verdict)
from dci.constraints.spec import P, spec

pytestmark = pytest.mark.cpu


def _spec(cid, family, role="unrelated", scope="whole_text", **params):
    return spec(cid, cid, cid, "format", "mechanism", scope, "answer", role,
                family, P(**params) if params else ())


def _min_words(cid="U_MINW", n=5):
    return _spec(cid, "min_words_per_sentence", scope="sentence", n=n)


def _char_budget(cid="U_LEN", n=40):
    return _spec(cid, "exact_char_total", n=n)


def _semicolon_total(cid="U_FMT_SEMI2", n=2):
    return _spec(cid, "exact_char_total", char=";", n=n)


def _semicolon_per_sentence(cid="S_SEMICOLON", n=1):
    return _spec(cid, "semicolon_per_sentence", role="candidate",
                 scope="sentence", n=n)


# ----------------------------------------------------------------- heuristics

def test_four_characters_per_word_is_a_review_flag_not_a_contradiction():
    """"a b c d e" is five words in nine characters, so the pair is possible."""
    kind, why = pair_verdict(_min_words(n=5), _char_budget(n=12))
    assert kind == "review"
    assert kind not in BLOCKING_VERDICTS
    assert "review rather than exclude" in why


def test_a_review_flag_does_not_exclude_the_pair_from_calibration():
    frame = audit_pairs([("U_MINW", "U_LEN")],
                        {"U_MINW": _min_words(n=5), "U_LEN": _char_budget(n=12)})
    assert frame.loc[0, "verdict"] == "review"
    assert bool(frame.loc[0, "usable_for_calibration"]) is True


def test_the_valid_character_floor_still_proves_impossibility():
    """Five words need at least 9 characters: 5 letters plus 4 separators."""
    kind, why = pair_verdict(_min_words(n=5), _char_budget(n=8))
    assert kind == "hard"
    assert "cannot occupy fewer than 9 characters" in why
    assert pair_verdict(_min_words(n=5), _char_budget(n=9))[0] != "hard"


def test_a_generous_budget_produces_no_verdict_at_all():
    assert pair_verdict(_min_words(n=5), _char_budget(n=400)) == ("ok", "")


# ------------------------------------------------------- the semicolon bound

def test_semicolon_total_bounds_the_sentence_count_from_above():
    kind, why = pair_verdict(_semicolon_total(n=2), _semicolon_per_sentence(n=1))
    assert kind == "restricted"
    assert "AT MOST 2 sentence(s)" in why
    # The old rule claimed the count had to EQUAL the total.
    assert "exactly 2 sentences" not in why


def test_one_semicolon_per_sentence_with_four_total_allows_four_sentences():
    _, why = pair_verdict(_semicolon_total(n=4), _semicolon_per_sentence(n=1))
    assert "AT MOST 4 sentence(s)" in why


def test_two_per_sentence_halves_the_admissible_sentence_count():
    _, why = pair_verdict(_semicolon_total(n=4), _semicolon_per_sentence(n=2))
    assert "AT MOST 2 sentence(s)" in why


def test_fewer_semicolons_than_one_sentence_needs_is_a_real_contradiction():
    kind, why = pair_verdict(_semicolon_total(n=1), _semicolon_per_sentence(n=2))
    assert kind == "hard"
    assert "at least one sentence" in why


def test_a_character_count_is_not_read_as_a_length_budget():
    """The overloaded family once made "exactly 2 semicolons" mean "2 chars"."""
    kind, _ = pair_verdict(_min_words(n=5), _semicolon_total(n=2))
    assert kind == "ok"


# ------------------------------------------------------------ proven clashes

def test_forbidding_a_character_required_per_sentence_stays_hard():
    banned = _spec("U_FMT_NOCOMMA", "no_char", char=",")
    required = _spec("S_COMMA", "commas_per_sentence", role="candidate",
                     scope="sentence", n=1)
    assert pair_verdict(banned, required)[0] == "hard"
    assert pair_verdict(required, banned)[0] == "hard"      # symmetric


def test_declared_incompatibility_is_honoured_in_both_directions():
    a = spec("A1", "A1", "A1", "format", "m", "whole_text", "answer", "target",
             "fam_a", (), incompatible_with=("B1",))
    b = _spec("B1", "fam_b")
    assert pair_verdict(a, b)[0] == "hard"
    assert pair_verdict(b, a)[0] == "hard"


def test_every_verdict_kind_is_declared():
    for pair in [(_min_words(n=5), _char_budget(n=8)),
                 (_min_words(n=5), _char_budget(n=12)),
                 (_min_words(n=5), _char_budget(n=400)),
                 (_semicolon_total(n=2), _semicolon_per_sentence(n=1))]:
        assert pair_verdict(*pair)[0] in VERDICT_KINDS


# ------------------------------------------------------------------ witnesses

class _Result:
    def __init__(self, ok):
        self.binary_pass = int(ok)


def test_n_searched_counts_only_entries_actually_inspected():
    corpus = ["no", "no", "yes", "no", "no", "no"]
    seen = []

    def verify(text, _cid):
        seen.append(text)
        return _Result(text == "yes")

    out = corpus_witness("A", "B", corpus, verify)
    assert out["witness_found"] is True
    assert out["n_searched"] == 3           # not len(corpus) == 6
    assert out["witness"] == "yes"


def test_absent_witness_reports_the_whole_sweep_and_flags_review():
    out = corpus_witness("A", "B", ["a", "b"], lambda t, c: _Result(False))
    assert out == {"pair": "A+B", "witness_found": False, "n_searched": 2,
                   "witness": None, "flag_for_review": True}


def test_a_consumed_generator_reports_what_it_consumed():
    """The corpus may be lazy; the count must describe the actual search."""
    out = corpus_witness("A", "B", (str(i) for i in range(100)),
                         lambda t, c: _Result(t == "4"))
    assert out["n_searched"] == 5
