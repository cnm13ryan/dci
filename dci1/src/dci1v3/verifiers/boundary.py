"""The frozen forty-case boundary suite (§10 content validity, §18.3 Gate 1).

The forty case texts and their S0/S1/S2 expectations are carried byte-for-
byte from the instrument that produced the v2 E2B annotation packet, so the
carry-over's boundary-specification hash can hold (§10). The per-family
statistics are hand-derived v3 expectations for the eight reference families
and the focal rule; Gate 1 requires every verifier to return its specified
verdict on every case at every registered severity.

Coverage (§18.3): empty response, adjacent punctuation, capitalisation,
hyphenation, target text inside a longer word, repeated words, non-Latin
characters, and truncation mid-word.

Statistic keys: ``B`` is the focal statistic (longest word's letter count);
``RF1``–``RF8`` are the family statistics of verifiers/families.py.
"""
from __future__ import annotations

from dci1v3.protocol.constants import FOCAL_GRID, REFERENCE_FAMILIES
from dci1v3.protocol.hashing import canonical_json, sha_text


def _case(case_id, text, s0, s1, s2, covers, stats):
    b, rf1, rf2, rf3, rf4, rf5, rf6, rf7, rf8 = stats
    return {"case_id": case_id, "text": text, "s0": s0, "s1": s1, "s2": s2,
            "covers": covers,
            "stats": {"B": b, "RF1": rf1, "RF2": rf2, "RF3": rf3,
                      "RF4": rf4, "RF5": rf5, "RF6": rf6, "RF7": rf7,
                      "RF8": rf8}}


#                                                      B  1  2  3  4  5  6  7  8
BOUNDARY_CASES: tuple[dict, ...] = (
    _case("bc01", "", 0, 0, 0, "empty",
          (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc02", "  \n\t  ", 0, 0, 0, "empty",
          (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc03", "However, the plan failed.", 1, 0, 1, "punctuation",
          (7, 0, 0, 0, 0, 1, 1, 2, 0)),
    _case("bc04", "however however", 2, 2, 2, "repeated",
          (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc05", "Howeverhowever", 0, 0, 2, "inside-longer-word",
          (14, 0, 0, 0, 0, 0, 1, 0, 0)),
    _case("bc06", "how-ever", 0, 0, 0, "hyphenation",
          (4, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc07", "'however'", 1, 1, 1, "punctuation",
          (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc08", "**However** we agree.", 1, 0, 1, "markdown",
          (7, 0, 0, 0, 1, 0, 1, 1, 0)),
    _case("bc09", "HOWEVER", 1, 0, 1, "capitalisation",
          (7, 0, 0, 0, 0, 0, 7, 0, 0)),
    _case("bc10", "HoWeVeR appears once.", 1, 0, 1, "capitalisation",
          (7, 0, 0, 0, 1, 0, 4, 1, 0)),
    _case("bc11", "The result was surprising because howev", 0, 0, 0,
          "cut-off-mid-word",
          (10, 1, 1, 0, 0, 0, 1, 2, 0)),
    _case("bc12", "然而 however 然而", 1, 1, 1, "non-latin",
          (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc13", "café closed", 0, 0, 0, "non-latin-accent",
          (6, 0, 0, 0, 0, 0, 0, 1, 0)),
    _case("bc14", "coffee shop", 0, 0, 0, "doubled-letters",
          (6, 0, 0, 0, 1, 0, 0, 0, 0)),
    _case("bc15", "31 dogs, 42 cats", 0, 0, 0, "digits",
          (4, 0, 0, 0, 0, 1, 0, 1, 0)),
    _case("bc16", "a b c", 0, 0, 0, "single-letter-words",
          (1, 1, 0, 3, 0, 0, 0, 1, 0)),
    _case("bc17", "Truly lovely melody", 0, 0, 0, "suffix-ly",
          (6, 0, 0, 0, 0, 0, 1, 0, 3)),
    _case("bc18", "Singing and dancing bring joy", 0, 0, 0, "suffix-ing",
          (7, 1, 3, 0, 0, 0, 1, 2, 1)),
    _case("bc19", "The however count is one", 1, 1, 1, "plain",
          (7, 0, 0, 0, 0, 0, 1, 0, 0)),
    _case("bc20", "however; however: however!", 3, 3, 3, "punctuation",
          (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc21", "Whoever said that was wrong.", 0, 0, 0, "near-miss-word",
          (7, 0, 0, 0, 0, 0, 1, 3, 0)),
    _case("bc22", "This however, that however.", 2, 2, 2, "repeated",
          (7, 0, 0, 0, 0, 1, 1, 1, 0)),
    _case("bc23", "HOWEVERHOWEVERHOWEVER", 0, 0, 3, "inside-longer-word",
          (21, 0, 0, 0, 0, 0, 21, 0, 0)),
    _case("bc24", "Nevertheless, the outcome improved.", 0, 0, 0,
          "near-miss-word",
          (12, 0, 0, 0, 1, 1, 1, 0, 0)),
    _case("bc25", "He said However loudly.", 1, 0, 1, "capitalisation",
          (7, 0, 0, 0, 0, 0, 2, 1, 1)),
    _case("bc26", "mail email mail", 0, 0, 0, "initial-letter",
          (5, 0, 0, 0, 0, 0, 0, 3, 0)),
    _case("bc27", "The queue formed quickly following heavy interest.",
          0, 0, 0, "suffixes",
          (9, 0, 1, 0, 1, 0, 1, 1, 2)),
    _case("bc28", "Ho we ver", 0, 0, 0, "split-target",
          (3, 0, 0, 0, 0, 0, 1, 0, 0)),
    _case("bc29", "however\nhowever\nhowever\nhowever", 4, 4, 4, "newlines",
          (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case("bc30", "Bright blue banners blew by.", 0, 0, 0, "initial-letter",
          (7, 5, 0, 0, 1, 0, 1, 1, 1)),
    _case("bc31", "Stop! Don't shout.", 0, 0, 0, "apostrophe",
          (5, 0, 0, 1, 0, 0, 2, 0, 0)),
    _case("bc32", "People however remained hopeful throughout.", 1, 1, 1,
          "word-length",
          (10, 0, 0, 0, 0, 0, 1, 1, 0)),
    _case("bc33", "sing sang sung", 0, 0, 0, "suffix-ing",
          (4, 0, 1, 0, 0, 0, 0, 1, 0)),
    _case("bc34", "How ever did you manage?", 0, 0, 0, "split-target",
          (6, 0, 0, 0, 0, 0, 1, 1, 0)),
    _case("bc35", "Every fall, leaves fall.", 0, 0, 0, "doubled-letters",
          (6, 0, 0, 0, 2, 1, 1, 3, 1)),
    _case("bc36", "también mañana", 0, 0, 0, "non-latin-accent",
          (7, 0, 0, 0, 0, 0, 0, 2, 0)),
    _case("bc37", "One two three four five six seven eight nine ten however.",
          1, 1, 1, "many-words",
          (7, 0, 0, 0, 1, 0, 1, 0, 0)),
    _case("bc38", "AAA bbb CCC", 0, 0, 0, "capitalisation",
          (3, 1, 0, 0, 3, 0, 6, 1, 0)),
    _case("bc39", "The plan.However succeeded.", 1, 0, 1,
          "punctuation-run-boundary",
          (9, 0, 0, 0, 1, 0, 2, 1, 0)),
    _case("bc40", "however However HOWEVER hOwEvEr", 4, 1, 4,
          "capitalisation",
          (7, 0, 0, 0, 0, 0, 11, 0, 0)),
)

assert len(BOUNDARY_CASES) == 40

#: §18.3 required coverage categories -> case ids demonstrating each.
COVERAGE = {
    "empty": ("bc01", "bc02"),
    "adjacent-punctuation": ("bc03", "bc07", "bc20", "bc39"),
    "capitalisation": ("bc09", "bc10", "bc38", "bc40"),
    "hyphenation": ("bc06",),
    "target-inside-longer-word": ("bc05", "bc23"),
    "repeated-words": ("bc04", "bc22", "bc29"),
    "non-latin": ("bc12", "bc13", "bc36"),
    "truncation-mid-word": ("bc11",),
}


def target_boundary_specification() -> str:
    """Canonical serialization of the target-relevant boundary data, hashed
    for the E2B carry-over record (§10)."""
    rows = [{"case_id": c["case_id"], "text": c["text"], "s0": c["s0"],
             "s1": c["s1"], "s2": c["s2"]} for c in BOUNDARY_CASES]
    return canonical_json(rows)


def boundary_specification_hash() -> str:
    return sha_text(target_boundary_specification())


def evaluate_suite() -> dict:
    """Execute every verifier on every case at every registered severity;
    Gate 1 requires 40/40 cases handled exactly as specified."""
    from dci1v3.verifiers import families, target

    failures: list[tuple] = []
    for case in BOUNDARY_CASES:
        text = case["text"]
        got = {"s0": target.s0_count(text), "s1": target.s1_count(text),
               "s2": target.s2_count(text)}
        for key in ("s0", "s1", "s2"):
            if got[key] != case[key]:
                failures.append((case["case_id"], key, case[key], got[key]))
        for m in FOCAL_GRID:
            expected = case["stats"]["B"] <= m
            if families.focal_passes(text, m) != expected:
                failures.append((case["case_id"], f"B@{m}", expected,
                                 not expected))
        for family, grid in REFERENCE_FAMILIES.items():
            stat = families.family_statistic(family, text)
            if stat != case["stats"][family]:
                failures.append((case["case_id"], family,
                                 case["stats"][family], stat))
                continue
            for q in grid:
                expected = case["stats"][family] <= q
                if families.family_passes(family, text, q) != expected:
                    failures.append((case["case_id"], f"{family}@{q}",
                                     expected, not expected))
    return {"cases": len(BOUNDARY_CASES),
            "handled_as_specified": len(BOUNDARY_CASES) - len(
                {f[0] for f in failures}),
            "failures": failures}
