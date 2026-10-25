"""The shared text semantics: carried word rule, documented edge cases, the
certified sentence segmentation, paragraphs, and oracle agreement."""
from __future__ import annotations

import inspect
import random
import re

import pytest

from dci.batch1 import text as T
from tests.batch1.conftest import function_source, historical_source

pytestmark = pytest.mark.cpu


def test_alpha_runs_is_byte_identical_to_the_historical_rule():
    carried = historical_source("dci1/src/dci1v4/verifiers/words.py")
    assert inspect.getsource(T.alpha_runs) == \
        function_source(carried, "alpha_runs") + "\n"


def test_b_statistic_matches_the_historical_definition():
    source = historical_source("dci1/src/dci1v7/verifiers/statistics.py")
    assert "max((len(run) for run in alpha_runs(text)), default=0)" in \
        function_source(source, "focal_statistic")


@pytest.mark.parametrize("text, words", [
    ("don't stop", ["don", "t", "stop"]),
    ("don’t", ["don", "t"]),
    ("well-known", ["well", "known"]),
    ("café au lait", ["café", "au", "lait"]),
    ("COVID19 cases", ["COVID", "cases"]),
    ("con​sequently", ["con", "sequently"]),
    ("soft­hyphen", ["soft", "hyphen"]),
    ("Привет мир", ["Привет", "мир"]),
    ("**bold** _it_", ["bold", "it"]),
    ("", []),
])
def test_word_rule_edge_cases_are_pinned(text, words):
    assert T.words(text) == words


def test_ligature_counts_as_one_letter_without_normalisation():
    assert T.max_word_letters("ﬁne") == 3       # "ﬁne": ﬁ + n + e


def test_zero_width_space_is_counted_as_a_diagnostic():
    assert T.format_characters("con​sequently­") == 2
    assert T.format_characters("plain text") == 0


def test_fold_after_segmenting_differs_from_fold_first_only_on_dotted_i():
    text = "İstanbul is large"
    assert T.folded_words(text)[0] == "i̇stanbul"
    assert T.alpha_runs(text.lower())[:2] == ["i", "stanbul"]
    for ch in ("A", "É", "ß", "Ω"):
        word = ch + "bc"
        assert T.folded_words(word) == T.alpha_runs(word.lower())


@pytest.mark.parametrize("text, n", [
    ("One. Two. Three.", 3),
    ("Mr. Smith went home. He stayed.", 2),
    ("It ended at 6 a.m. when others slept.", 1),
    ("It ended at 6 p.m. Tomorrow begins early.", 2),
    ("Prices rose 3.5 percent. Then fell.", 2),
    ("Wait... Really? Yes!", 3),
    ("No terminator here", 1),
    ("First line\nSecond line", 2),
    ("- item one\n- item two.", 2),
    ("1. First point.\n2. Second point.", 2),
    ("## Heading\nBody text here.", 2),
    ("...", 0),
    ("", 0),
])
def test_sentence_segmentation(text, n):
    assert len(T.sentences(text)) == n


def test_list_markers_do_not_become_words_or_sentences():
    assert T.first_word("1. Second item here.") == "second"
    assert T.sentences("1. Second item here.") == ["Second item here."]


def test_paragraphs_are_blank_line_blocks_with_words():
    assert len(T.paragraphs("a b\nc\n\n\nd e\n   \nf")) == 3
    assert len(T.paragraphs("one\n\n---\n\ntwo")) == 2
    assert T.paragraphs("") == []


def test_char_count_is_raw():
    assert T.char_count("1,000, and more，", ",") == 2
    with pytest.raises(ValueError):
        T.char_count("x", ",,")


def _oracle_words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", text)


def test_word_rule_agrees_with_an_independent_regex_oracle():
    alphabet = list("abcxyzABCéüßΩж") + list(" ,.;:!?'’-_\n\t0123") + \
        ["​", "­"]
    rng = random.Random(20261018)
    for _ in range(2000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        assert T.words(text) == _oracle_words(text), repr(text)


def test_semantics_hash_is_stable_and_covers_the_rules_module():
    assert T.text_semantics_hash() == T.text_semantics_hash()
    assert "rules_boundary_pattern" in T.TEXT_SEMANTICS
