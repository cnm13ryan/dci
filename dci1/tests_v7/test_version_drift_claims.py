"""`docs/VERSION_DRIFT.md`'s carry claims, checked against the code.

The document exists so that no agent mixes v3, v4, v5, v6, v7 and v8
definitions. A carry claim in it that the code contradicts is worse than no
document at all: it invites exactly the pooling it was written to prevent.
Every claim below is one a reader could otherwise only take on trust.
"""
from __future__ import annotations

import re
from pathlib import Path

from dci1v3.protocol.wordings import target_wordings as v3_target
from dci1v4.protocol.wordings import target_wordings as v4_target
from dci1v7.protocol.wordings import target_wordings as v7_target

DRIFT = Path(__file__).resolve().parents[1] / "docs" / "VERSION_DRIFT.md"


def test_only_a_s_canonical_template_carried_from_v3_to_v4():
    """v3 -> v4 changed three of A's four templates, and the document says so.

    v3's alternates name the target as *the word however* and locate the
    count *in your answer*; v4's drop both. This is text the model is shown,
    so a v3 A-rate is not prompt-identical to a v4-or-later one.
    """
    for q in (1, 2, 5):
        v3, v4 = v3_target(q), v4_target(q)
        assert len(v3) == len(v4) == 4
        assert v3[0] == v4[0], "the canonical template did carry"
        assert [a == b for a, b in zip(v3, v4)] == [True, False, False, False]
    # and the differences are exactly the phrases the document names:
    # *the word* leaves alternates 1 and 2, *in your answer* leaves 3.
    v3, v4 = v3_target(1), v4_target(1)
    for i in (1, 2):
        assert "the word however" in v3[i] and "the word however" not in v4[i]
    assert "in your answer" in v3[2] and "in your answer" in v4[2], \
        "alternate 2 keeps its locative; only *the word* leaves it"
    assert "The word however" in v3[3] and "The word however" in v4[3], \
        "alternate 3 keeps its noun phrase; only the locative leaves it"
    assert "in your answer" in v3[3] and "in your answer" not in v4[3]


def test_a_s_templates_carried_byte_identically_from_v4_onward():
    """The document's *other* half: from v4 the four are carried unchanged."""
    for q in (1, 2, 5, 8):
        assert v4_target(q) == v7_target(q)


def test_the_document_does_not_claim_v3_to_v4_was_byte_identical():
    """A regression guard on the prose itself. The claim that all four
    carried byte-identically from v3 was in this document until 2026-08-31.
    """
    text = DRIFT.read_text()
    section = text.split("## The marker families")[0]
    assert "restatement was not byte-identical" in section
    assert not re.search(
        r"authored for v3 \(`85fe950`\), restated in\s+`dci1v4/protocol/"
        r"wordings\.py` \(`09c3896`\) and carried \*\*byte-identically\*\*",
        section), "the corrected claim has regressed"
