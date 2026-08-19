"""The fixed forty-case boundary suite (prereg §10 content validity, §18 Gate 1).

Hand-written cases covering every enumerated ambiguity: empty answer,
punctuation adjacent to the target word, capitalisation, hyphenation, the
target word inside a longer word, repeated words, non-Latin characters, and an
answer cut off mid-word. Expectations were derived by hand from the frozen
rule definitions (S0/S1/S2 counts; pool verdicts with the focal bound at
m = 7). Gate 1 requires every case handled exactly as specified.

Pool expectation keys: "B7" is the focal rule at m=7; "C1"–"C12" are the
candidates. True = pass.
"""
from __future__ import annotations


def _case(case_id, text, s0, s1, s2, covers, **pool):
    verdicts = {"B7": True}
    verdicts.update({f"C{i}": True for i in range(1, 13)})
    for key, value in pool.items():
        verdicts[key] = value
    return {"case_id": case_id, "text": text, "s0": s0, "s1": s1, "s2": s2,
            "covers": covers, "pool": verdicts}


BOUNDARY_CASES: tuple[dict, ...] = (
    _case("bc01", "", 0, 0, 0, "empty"),
    _case("bc02", "  \n\t  ", 0, 0, 0, "empty"),
    _case("bc03", "However, the plan failed.", 1, 0, 1, "punctuation",
          C5=False, C7=False, C9=False),
    _case("bc04", "however however", 2, 2, 2, "repeated"),
    _case("bc05", "Howeverhowever", 0, 0, 2, "inside-longer-word", B7=False),
    _case("bc06", "how-ever", 0, 0, 0, "hyphenation"),
    _case("bc07", "'however'", 1, 1, 1, "punctuation"),
    _case("bc08", "**However** we agree.", 1, 0, 1, "markdown",
          C2=False, C12=False),
    _case("bc09", "HOWEVER", 1, 0, 1, "capitalisation"),
    _case("bc10", "HoWeVeR appears once.", 1, 0, 1, "capitalisation",
          C12=False),
    _case("bc11", "The result was surprising because howev", 0, 0, 0,
          "cut-off-mid-word", B7=False, C3=False, C8=False, C9=False,
          C11=False),
    _case("bc12", "然而 however 然而", 1, 1, 1, "non-latin", C2=False),
    _case("bc13", "café closed", 0, 0, 0, "non-latin-accent", C4=False),
    _case("bc14", "coffee shop", 0, 0, 0, "doubled-letters",
          C4=False, C8=False, C12=False),
    _case("bc15", "31 dogs, 42 cats", 0, 0, 0, "digits", C4=False),
    _case("bc16", "a b c", 0, 0, 0, "single-letter-words",
          C1=False, C2=False, C3=False, C4=False),
    _case("bc17", "Truly lovely melody", 0, 0, 0, "suffix-ly",
          C6=False, C9=False, C10=False),
    _case("bc18", "Singing and dancing bring joy", 0, 0, 0, "suffix-ing",
          C3=False, C8=False, C11=False),
    _case("bc19", "The however count is one", 1, 1, 1, "plain",
          C2=False, C4=False, C9=False),
    _case("bc20", "however; however: however!", 3, 3, 3, "punctuation"),
    _case("bc21", "Whoever said that was wrong.", 0, 0, 0,
          "near-miss-word", C8=False, C9=False),
    _case("bc22", "This however, that however.", 2, 2, 2, "repeated",
          C9=False),
    _case("bc23", "HOWEVERHOWEVERHOWEVER", 0, 0, 3, "inside-longer-word",
          B7=False),
    _case("bc24", "Nevertheless, the outcome improved.", 0, 0, 0,
          "near-miss-word", B7=False, C9=False, C12=False),
    _case("bc25", "He said However loudly.", 1, 0, 1, "capitalisation",
          C2=False, C8=False, C10=False),
    _case("bc26", "mail email mail", 0, 0, 0, "initial-letter", C6=False),
    _case("bc27", "The queue formed quickly following heavy interest.",
          0, 0, 0, "suffixes", B7=False, C5=False, C9=False, C10=False,
          C11=False, C12=False),
    _case("bc28", "Ho we ver", 0, 0, 0, "split-target", C2=False),
    _case("bc29", "however\nhowever\nhowever\nhowever", 4, 4, 4,
          "newlines"),
    _case("bc30", "Bright blue banners blew by.", 0, 0, 0, "initial-letter",
          C2=False, C3=False, C12=False),
    _case("bc31", "Stop! Don't shout.", 0, 0, 0, "apostrophe",
          C1=False, C2=False, C8=False, C9=False),
    _case("bc32", "People however remained hopeful throughout.", 1, 1, 1,
          "word-length", B7=False, C7=False, C9=False),
    _case("bc33", "sing sang sung", 0, 0, 0, "suffix-ing",
          C8=False, C11=False),
    _case("bc34", "How ever did you manage?", 0, 0, 0, "split-target",
          C6=False),
    _case("bc35", "Every fall, leaves fall.", 0, 0, 0, "doubled-letters",
          C5=False, C12=False),
    _case("bc36", "también mañana", 0, 0, 0, "non-latin-accent",
          C6=False, C9=False),
    _case("bc37", "One two three four five six seven eight nine ten however.",
          1, 1, 1, "many-words", C5=False, C8=False, C9=False, C12=False),
    _case("bc38", "AAA bbb CCC", 0, 0, 0, "capitalisation",
          C3=False, C4=False, C12=False),
    _case("bc39", "The plan.However succeeded.", 1, 0, 1,
          "punctuation-run-boundary", B7=False, C7=False, C8=False,
          C9=False, C12=False),
    _case("bc40", "however However HOWEVER hOwEvEr", 4, 1, 4,
          "capitalisation"),
)

assert len(BOUNDARY_CASES) == 40


def evaluate_suite() -> dict:
    """Execute every verifier on every case; count cases handled as
    specified (Gate 1 requires 40/40)."""
    from dci1.constraints.definitions import added_verifier
    from dci1.verifiers import target

    failures = []
    for case in BOUNDARY_CASES:
        text = case["text"]
        got = {"s0": target.s0_count(text), "s1": target.s1_count(text),
               "s2": target.s2_count(text)}
        for key in ("s0", "s1", "s2"):
            if got[key] != case[key]:
                failures.append((case["case_id"], key, case[key], got[key]))
        for key, expected in case["pool"].items():
            if key == "B7":
                verdict = added_verifier("B", 7)(text)
            else:
                verdict = added_verifier(key)(text)
            if verdict != expected:
                failures.append((case["case_id"], key, expected, verdict))
    return {"cases": len(BOUNDARY_CASES),
            "handled_as_specified": len(BOUNDARY_CASES) - len(
                {f[0] for f in failures}),
            "failures": failures}
