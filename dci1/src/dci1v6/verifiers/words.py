"""Word segmentation for v5 (§9.2), carried unchanged from v4r4.

**Nothing here is scientifically reopened.** §9.2's lexical rule is carried
verbatim, this module is a re-namespaced copy of ``dci1v4r4.verifiers.words``,
and ``verifiers/carryover.py`` *measures* the identity rather than asserting
it: the two revisions' functions are run against each other over the frozen
boundary corpus and over every stored response the caller supplies.

The rule, restated in full because v5 incorporates nothing by reference:

* ``alpha_runs`` is carried byte-identically from ``dci1v4.verifiers.words``,
  which carries it from the closed v3 instrument. It is imported rather than
  restated so the identity is structural.
* ``words_lower`` **segments first and lower-cases each word for the tests**.
  The alternative --- fold the whole response, then segment --- differs on
  exactly one character of Unicode. ``İ`` (U+0130) lower-cases to ``i`` plus
  U+0307, whose general category is ``Mn`` and which is therefore not
  alphabetic, so folding first *splits the word*: ``İstanbul`` becomes ``i``
  and ``stanbul``. §10.2 adjudicates the disagreement against the registered
  prose of §9.2, which defines the word on the response and folds for the
  test.
* **A's own counter is untouched and folds first**, because §9.2 registers
  S0 in its own words --- *take the whole response, lower-case it, find every
  maximal run of alphabetic characters, count the runs equal to `however`* ---
  which is fold-then-segment. A counts occurrences of a string; B and the
  families make claims about words as objects.

**Every Tier-1 marker family uses §9.2's convention, not S0's**, and that is
registered rather than incidental: a marker family is A's *predicate form*
over a different marker word, and its numerator is a word-list test like every
other family's. The two conventions differ on U+0130 alone, which occurs zero
times in the 285,936 rows this programme has generated.
"""
from __future__ import annotations

from dci1v4.verifiers.words import alpha_runs

__all__ = ["alpha_runs", "words_lower", "case_folding_splitters",
           "assert_single_splitter", "SENTENCE_TERMINATORS", "sentence_units"]

#: §9.2. The three characters that end a sentence, a literal set rather than a
#: Unicode category, because the construct is the ordinary written one.
SENTENCE_TERMINATORS = ".!?"


def words_lower(text: str) -> list[str]:
    """§9.2: segment the answer, then lower-case each word for the tests."""
    return [run.lower() for run in alpha_runs(text)]


def case_folding_splitters() -> tuple[str, ...]:
    """Every alphabetic character whose lower-case form is not alphabetic
    throughout, and which therefore splits a word under fold-then-segment.

    Executable because "exactly one character behaves this way" is
    load-bearing for the scope of the correction above, and a claim of that
    shape should be recomputed rather than believed.
    """
    out = []
    for codepoint in range(0x110000):
        ch = chr(codepoint)
        if ch.isalpha() and not all(c.isalpha() for c in ch.lower()):
            out.append(ch)
    return tuple(out)


def assert_single_splitter() -> str:
    """§24: the enumeration finds U+0130 and nothing else."""
    found = case_folding_splitters()
    if found != ("İ",):
        raise AssertionError(
            "the case-folding split enumeration no longer names exactly "
            f"U+0130; it names {[hex(ord(c)) for c in found]}. §9.2's scope "
            "argument is stated over that enumeration and must be re-derived")
    return "İ"


def sentence_units(text: str) -> int:
    """§9.2: the number of sentences in the answer.

    *Count the maximal runs of the characters* ``.``, ``!`` *and* ``?`` *in
    the answer; if any character that is not whitespace follows the last such
    run --- or if there is no such run and the answer is not blank --- add one
    for the unterminated final sentence.* A blank answer has no sentences.

    The trailing clause is why this is not a terminator count. A response that
    ends mid-clause contains a sentence a reader would count and a bare tally
    would not, and a budget verifier scoring such an answer as zero sentences
    would pass it at every severity for having written nothing it could count.
    Runs are maximal, so ``...`` ends one sentence rather than three. A
    decimal point and an abbreviation's full stop both terminate a sentence
    under this rule: a registered over-count, stated rather than discovered.
    """
    count, in_run, seen_since = 0, False, False
    for ch in text:
        if ch in SENTENCE_TERMINATORS:
            if not in_run:
                count += 1
                in_run = True
            seen_since = False
        else:
            in_run = False
            if not ch.isspace():
                seen_since = True
    return count + (1 if seen_since else 0)
