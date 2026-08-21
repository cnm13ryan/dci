"""Word segmentation for v4r3 (§7.3, §9.2), and one corrected composition.

``alpha_runs`` is **carried byte-identically** from ``dci1v4.verifiers.words``,
which carries it byte-identically from the closed v3 instrument. It is
imported here rather than restated, so the identity is structural and
``carryover.py`` checks it anyway.

``words_lower`` is **not** carried, and this module exists to say why.

# The finding

§10.2's independent reimplementation, written from the registered prose of
§7.3 by a process that read no primary source, disagreed with the primary on
the ``one_letter`` statistic. The cause is a composition order:

* v4r2's helper is ``alpha_runs(text.lower())`` -- lower-case the whole
  response, **then** segment;
* §7.3's prose says a word is a maximal run of alphabetic characters in the
  answer, and that "suffix and letter tests use the lower-cased word" --
  segment, **then** lower-case each word.

The two coincide on every character of Unicode except exactly one. ``İ``
(U+0130, LATIN CAPITAL LETTER I WITH DOT ABOVE) lower-cases to ``i`` followed
by U+0307 COMBINING DOT ABOVE, whose general category is ``Mn`` and which is
therefore not alphabetic -- so folding first **splits the word**.
``İstanbul`` is one eight-letter word to a reader and to §7.3; to
``alpha_runs(text.lower())`` it is ``i`` and ``stanbul``, two words of one and
seven letters. Under that reading B at m = 7 passes a response containing an
eight-letter word, ``one_letter`` gains a word that is not there, and every
suffix and letter test reads the fragments rather than the word.

An exhaustive sweep of the Unicode range finds **one** such character and no
other; the enumeration is executable below.

# The adjudication, and its scope

§10.2 adjudicates a disagreement against the registered prose. The prose of
§7.3 defines the word on the response and folds for the *test*, so the
reimplementation is right and the carried composition is wrong. v4r3
therefore composes in the registered order.

**A is untouched, and deliberately.** §9.2 registers S0 in its own words --
"take the whole response, lower-case it, find every maximal run of alphabetic
characters, count the runs equal to *however*" -- which *is* fold-then-segment,
and ``s0_count`` implements exactly that. A's construct string, segmentation
function and counting function stay byte-identical to v3 and A's §10.2
carry-over survives. The two rules differ because the two prose passages
differ, and §7.3 records that rather than smoothing it over: A counts
occurrences of a string, and a fold-then-match is the natural reading of that;
B and the families make claims about words as objects, and a word's identity
must not depend on its case.

# What changes in the numbers

Nothing measured. ``İ`` occurs **zero** times in the 285,936 rows every v4-era
process has generated, so no historical rate moves and no comparison is
broken. The correction is prospective, the boundary suites carry a frozen case
for it, and §24 reports its realised frequency so a future firing is visible
rather than silent.
"""
from __future__ import annotations

from dci1v4.verifiers.words import alpha_runs

__all__ = ["alpha_runs", "words_lower", "case_folding_splitters",
           "assert_single_splitter"]


def words_lower(text: str) -> list[str]:
    """§7.3: segment the answer, then lower-case each word for the tests."""
    return [run.lower() for run in alpha_runs(text)]


def case_folding_splitters() -> tuple[str, ...]:
    """Every alphabetic character whose lower-case form is not alphabetic
    throughout, and which therefore splits a word under fold-then-segment.

    Executable because the claim "exactly one character behaves this way" is
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
            f"U+0130; it names {[hex(ord(c)) for c in found]}. §7.3's scope "
            "argument is stated over that enumeration and must be re-derived")
    return "İ"
