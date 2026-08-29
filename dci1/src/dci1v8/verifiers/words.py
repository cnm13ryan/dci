"""Word segmentation and the one marker counter (v8, §9.2 unified).

**The change.** v7 scored A with ``dci1v4.verifiers.target.s0_count`` ---
*lower-case the whole response, then find the alphabetic runs* --- and every
marker family with the lexical rule of §9.2 --- *find the alphabetic runs of
the response as written, then lower-case each run for the test*. The two
orders agree on every code point but one: ``İ`` (U+0130) lower-cases to ``i``
followed by U+0307 COMBINING DOT ABOVE, which is not alphabetic, so folding
first splits the run. ``İhowever`` was one occurrence of *however* to A's
counter and ``İthus`` zero occurrences of *thus* to MK1's.

v8 counts A and MK1--MK8 with **one function**, ``count_marker``, under the
lexical rule. The lexical rule is chosen over S0's because it is the rule the
other fourteen numerators already use, it is the one §9.2 states for *word*,
and it reads the word as the model wrote it: ``İhowever`` is one word, and it
is not *however*.

Everything else is carried: ``alpha_runs`` is the closed v3 segmenter through
``dci1v4``, and the sentence rule is v7's.
"""
from __future__ import annotations

from dci1v4.errors import InstrumentError
from dci1v4.verifiers.words import alpha_runs
from dci1v7.verifiers.words import (
    SENTENCE_TERMINATORS, assert_single_splitter, case_folding_splitters,
    sentence_units,
)

__all__ = ["alpha_runs", "words_lower", "count_marker", "assert_marker_word",
           "case_folding_splitters", "assert_single_splitter",
           "SENTENCE_TERMINATORS", "sentence_units"]


def words_lower(text: str) -> list[str]:
    """§9.2: segment the answer as written, then lower-case each word."""
    return [run.lower() for run in alpha_runs(text)]


def assert_marker_word(marker: str) -> str:
    """A marker is one lower-case alphabetic run, or no run could equal it.

    On the mandatory path because the alternative is a counter that returns
    zero for every response and never says why: ``count_marker(text,
    "However")`` and ``count_marker(text, "over-all")`` cannot match anything
    ``words_lower`` produces.
    """
    if not isinstance(marker, str) or not marker:
        raise InstrumentError("a marker is a non-empty string")
    if alpha_runs(marker) != [marker]:
        raise InstrumentError(
            f"marker {marker!r} is not a single alphabetic run; nothing "
            "words_lower produces could ever equal it")
    if marker != marker.lower():
        raise InstrumentError(
            f"marker {marker!r} is not lower-case; the words it is compared "
            "with are")
    return marker


def count_marker(text: str, marker: str) -> int:
    """Occurrences of the whole word ``marker`` in ``text`` (§9.2, unified).

    Segment ``text`` into maximal runs of Unicode-alphabetic characters,
    lower-case each run, count the runs equal to ``marker``. Punctuation,
    digits, whitespace, hyphens, apostrophes, soft hyphens, zero-width
    characters and combining marks all end a run; a run that merely contains
    the marker does not count; fullwidth or otherwise non-identical letters
    never equal an ASCII marker.

    This is A's numerator with ``marker="however"`` and every Tier-1 family's
    with its own word. One function, nine target strings.
    """
    assert_marker_word(marker)
    return sum(1 for word in words_lower(text) if word == marker)
