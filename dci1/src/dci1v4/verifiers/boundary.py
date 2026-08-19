"""Frozen boundary suites, one per registered instrument (v4r2 §10.2, §24).

Under v4 the exact-count rule, the word-length rule and every admitted family
verifier are primary instruments, so each carries its own frozen suite of at
least forty cases covering the §24 enumeration. The suites split exactly as
§10.2 requires:

* **A-side, carried plus extended.** ``CARRIED_CASES`` is the v3 forty case
  texts with their S0/S1/S2 expectations, byte-identical;
  ``dci1v4.verifiers.carryover`` re-derives them from the v3 file read as
  data and refuses on any drift. ``ADDED_TARGET_CASES`` are authored for v4
  and cover what the §24 enumeration requires and the v3 forty do not:
  Unicode punctuation, Unicode lookalikes, zero-width and non-breaking
  characters, combining marks, the soft hyphen, and sentence-boundary
  punctuation. Forty-eight cases in total.
* **B-side and family suites, authored for v4 in full.** ``FOCAL_CASES`` is a
  v4-authored corpus of forty-four texts carrying a hand-derived statistic for
  the word-length rule and for each of the eight families, covering the §24
  word-length enumeration — empty output, single-token output, hyphenated and
  apostrophised forms, non-Latin script, digits and symbols adjacent to words,
  markdown emphasis — together with each family's own boundary features. No
  v3 case text and no v3 expectation enters these suites.

Every expectation here was written by hand from the registered prose and then
audited against ``dci1v4.verifiers.independent``, which reads that prose and
never the primary source. ``evaluate_suites`` executes the primary verifiers
against the frozen numbers; ``tests_v4`` additionally runs the independent
implementation over the whole suite and requires agreement of exactly 1.000.

Statistic keys: ``B`` is the longest word\u0027s letter count; ``RF1``-``RF8`` are
the family statistics of ``verifiers/statistics.py``.
"""
from __future__ import annotations

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text

_STAT_KEYS = ("B", "RF1", "RF2", "RF3", "RF4", "RF5", "RF6", "RF7", "RF8")


def _carried(case_id, text, s0, s1, s2, covers, stats):
    """One of the forty v3 cases. Only the text and S0/S1/S2 are carried
    evidence under §10.2; the trailing statistics vector is the v3 author\u0027s
    and is retained as cross-check evidence, never as the v4 B-side suite."""
    return {"case_id": case_id, "text": text, "s0": s0, "s1": s1, "s2": s2,
            "covers": covers, "origin": "carried_v3",
            "v3_stats": dict(zip(_STAT_KEYS, stats))}


def _added(case_id, text, s0, s1, s2, covers):
    """A v4-authored exact-count case closing a §24 enumeration gap."""
    return {"case_id": case_id, "text": text, "s0": s0, "s1": s1, "s2": s2,
            "covers": covers, "origin": "authored_v4"}


def _focal(case_id, text, covers, stats):
    """A v4-authored case for the word-length rule and the eight families."""
    if len(stats) != len(_STAT_KEYS):
        raise ProtocolError(f"{case_id}: expected {len(_STAT_KEYS)} statistics")
    return {"case_id": case_id, "text": text, "covers": covers,
            "origin": "authored_v4", "stats": dict(zip(_STAT_KEYS, stats))}


#: The v3 forty, carried byte-identically under the §10.2 carry-over rule.
CARRIED_CASES: tuple[dict, ...] = (
    _carried('bc01', '', 0, 0, 0, 'empty',
              (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc02', '  \n\t  ', 0, 0, 0, 'empty',
              (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc03', 'However, the plan failed.', 1, 0, 1, 'punctuation',
              (7, 0, 0, 0, 0, 1, 1, 2, 0)),
    _carried('bc04', 'however however', 2, 2, 2, 'repeated',
              (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc05', 'Howeverhowever', 0, 0, 2, 'inside-longer-word',
              (14, 0, 0, 0, 0, 0, 1, 0, 0)),
    _carried('bc06', 'how-ever', 0, 0, 0, 'hyphenation',
              (4, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc07', "'however'", 1, 1, 1, 'punctuation',
              (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc08', '**However** we agree.', 1, 0, 1, 'markdown',
              (7, 0, 0, 0, 1, 0, 1, 1, 0)),
    _carried('bc09', 'HOWEVER', 1, 0, 1, 'capitalisation',
              (7, 0, 0, 0, 0, 0, 7, 0, 0)),
    _carried('bc10', 'HoWeVeR appears once.', 1, 0, 1, 'capitalisation',
              (7, 0, 0, 0, 1, 0, 4, 1, 0)),
    _carried('bc11', 'The result was surprising because howev', 0, 0, 0, 'cut-off-mid-word',
              (10, 1, 1, 0, 0, 0, 1, 2, 0)),
    _carried('bc12', '然而 however 然而', 1, 1, 1, 'non-latin',
              (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc13', 'café closed', 0, 0, 0, 'non-latin-accent',
              (6, 0, 0, 0, 0, 0, 0, 1, 0)),
    _carried('bc14', 'coffee shop', 0, 0, 0, 'doubled-letters',
              (6, 0, 0, 0, 1, 0, 0, 0, 0)),
    _carried('bc15', '31 dogs, 42 cats', 0, 0, 0, 'digits',
              (4, 0, 0, 0, 0, 1, 0, 1, 0)),
    _carried('bc16', 'a b c', 0, 0, 0, 'single-letter-words',
              (1, 1, 0, 3, 0, 0, 0, 1, 0)),
    _carried('bc17', 'Truly lovely melody', 0, 0, 0, 'suffix-ly',
              (6, 0, 0, 0, 0, 0, 1, 0, 3)),
    _carried('bc18', 'Singing and dancing bring joy', 0, 0, 0, 'suffix-ing',
              (7, 1, 3, 0, 0, 0, 1, 2, 1)),
    _carried('bc19', 'The however count is one', 1, 1, 1, 'plain',
              (7, 0, 0, 0, 0, 0, 1, 0, 0)),
    _carried('bc20', 'however; however: however!', 3, 3, 3, 'punctuation',
              (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc21', 'Whoever said that was wrong.', 0, 0, 0, 'near-miss-word',
              (7, 0, 0, 0, 0, 0, 1, 3, 0)),
    _carried('bc22', 'This however, that however.', 2, 2, 2, 'repeated',
              (7, 0, 0, 0, 0, 1, 1, 1, 0)),
    _carried('bc23', 'HOWEVERHOWEVERHOWEVER', 0, 0, 3, 'inside-longer-word',
              (21, 0, 0, 0, 0, 0, 21, 0, 0)),
    _carried('bc24', 'Nevertheless, the outcome improved.', 0, 0, 0, 'near-miss-word',
              (12, 0, 0, 0, 1, 1, 1, 0, 0)),
    _carried('bc25', 'He said However loudly.', 1, 0, 1, 'capitalisation',
              (7, 0, 0, 0, 0, 0, 2, 1, 1)),
    _carried('bc26', 'mail email mail', 0, 0, 0, 'initial-letter',
              (5, 0, 0, 0, 0, 0, 0, 3, 0)),
    _carried('bc27', 'The queue formed quickly following heavy interest.', 0, 0, 0, 'suffixes',
              (9, 0, 1, 0, 1, 0, 1, 1, 2)),
    _carried('bc28', 'Ho we ver', 0, 0, 0, 'split-target',
              (3, 0, 0, 0, 0, 0, 1, 0, 0)),
    _carried('bc29', 'however\nhowever\nhowever\nhowever', 4, 4, 4, 'newlines',
              (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _carried('bc30', 'Bright blue banners blew by.', 0, 0, 0, 'initial-letter',
              (7, 5, 0, 0, 1, 0, 1, 1, 1)),
    _carried('bc31', "Stop! Don't shout.", 0, 0, 0, 'apostrophe',
              (5, 0, 0, 1, 0, 0, 2, 0, 0)),
    _carried('bc32', 'People however remained hopeful throughout.', 1, 1, 1, 'word-length',
              (10, 0, 0, 0, 0, 0, 1, 1, 0)),
    _carried('bc33', 'sing sang sung', 0, 0, 0, 'suffix-ing',
              (4, 0, 1, 0, 0, 0, 0, 1, 0)),
    _carried('bc34', 'How ever did you manage?', 0, 0, 0, 'split-target',
              (6, 0, 0, 0, 0, 0, 1, 1, 0)),
    _carried('bc35', 'Every fall, leaves fall.', 0, 0, 0, 'doubled-letters',
              (6, 0, 0, 0, 2, 1, 1, 3, 1)),
    _carried('bc36', 'también mañana', 0, 0, 0, 'non-latin-accent',
              (7, 0, 0, 0, 0, 0, 0, 2, 0)),
    _carried('bc37', 'One two three four five six seven eight nine ten however.', 1, 1, 1, 'many-words',
              (7, 0, 0, 0, 1, 0, 1, 0, 0)),
    _carried('bc38', 'AAA bbb CCC', 0, 0, 0, 'capitalisation',
              (3, 1, 0, 0, 3, 0, 6, 1, 0)),
    _carried('bc39', 'The plan.However succeeded.', 1, 0, 1, 'punctuation-run-boundary',
              (9, 0, 0, 0, 1, 0, 2, 1, 0)),
    _carried('bc40', 'however However HOWEVER hOwEvEr', 4, 1, 4, 'capitalisation',
              (7, 0, 0, 0, 0, 0, 11, 0, 0)),
)

assert len(CARRIED_CASES) == 40

#: Authored for v4: the §24 exact-count cases the v3 forty do not cover.
ADDED_TARGET_CASES: tuple[dict, ...] = (
    _added("ac01", "“however”, he said.", 1, 1, 1,
           "unicode-punctuation"),
    _added("ac02", "hоwever", 0, 0, 0, "unicode-lookalike"),
    _added("ac03", "how​ever", 0, 0, 0, "zero-width"),
    _added("ac04", "however‍ however", 2, 2, 2, "zero-width"),
    _added("ac05", "Yes. However! No? however...", 2, 1, 2,
           "sentence-boundary-punctuation"),
    _added("ac06", "however however", 2, 2, 2, "non-breaking-space"),
    _added("ac07", "how­ever", 0, 0, 0, "soft-hyphen"),
    _added("ac08", "howeveŕ rain", 1, 1, 1, "combining-mark"),
)

#: The A-side suite: forty carried plus eight authored.
TARGET_CASES: tuple[dict, ...] = CARRIED_CASES + ADDED_TARGET_CASES

#                                             B  R1 R2 R3 R4 R5 R6 R7 R8
FOCAL_CASES: tuple[dict, ...] = (
    _focal("fc01", "", "empty-output",
           (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc02", "   \n\t ", "empty-output",
           (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc03", "Yes.", "single-token-output",
           (3, 0, 0, 0, 0, 0, 1, 0, 0)),
    _focal("fc04", "b", "single-token-output",
           (1, 1, 0, 1, 0, 0, 0, 0, 0)),
    _focal("fc05", "state-of-the-art design", "hyphenated-form",
           (6, 0, 0, 0, 0, 0, 0, 2, 0)),
    _focal("fc06", "don't worry", "apostrophised-form",
           (5, 0, 0, 1, 1, 0, 0, 0, 1)),
    _focal("fc07", "然而 事情 改变", "non-latin-script",
           (2, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc08", "Δelta and Ωmega", "non-latin-script",
           (5, 0, 0, 0, 0, 0, 0, 3, 0)),
    _focal("fc09", "The 2026 census, 45% response.", "digits-and-symbols",
           (8, 0, 0, 0, 0, 1, 1, 0, 0)),
    _focal("fc10", "**bold** and _italic_ text", "markdown-emphasis",
           (6, 1, 0, 0, 0, 0, 0, 2, 0)),
    _focal("fc11", "aaa", "doubled-letters",
           (3, 0, 0, 0, 1, 0, 0, 1, 0)),
    _focal("fc12", "abab", "doubled-letters",
           (4, 0, 0, 0, 0, 0, 0, 1, 0)),
    _focal("fc13", "Bobby brings big books, bravely.", "initial-letter",
           (7, 5, 0, 0, 2, 1, 1, 1, 2)),
    _focal("fc14", "Running, jumping and swimming bring lasting joy.",
           "suffix-ing",
           (8, 1, 5, 0, 2, 1, 1, 2, 1)),
    _focal("fc15", "I do a b c d e f g.", "single-letter-words",
           (2, 1, 0, 8, 0, 0, 1, 1, 0)),
    _focal("fc16", "Sorry, sorry, sorry, sorry.", "repeated-words",
           (5, 0, 0, 0, 4, 3, 1, 0, 4)),
    _focal("fc17", "ABCDEFGHIJKL", "capitalisation",
           (12, 0, 0, 0, 0, 0, 12, 1, 0)),
    _focal("fc18", ",,,,,,,,,,,,", "adjacent-punctuation",
           (0, 0, 0, 0, 0, 12, 0, 0, 0)),
    _focal("fc19", "Extraordinarily complicated.", "word-length",
           (15, 0, 0, 0, 0, 0, 1, 2, 1)),
    _focal("fc20", "café naïve résumé", "non-latin-accent",
           (6, 0, 0, 0, 0, 0, 0, 2, 0)),
    _focal("fc21", "however", "target-word-present",
           (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc22", "The plan​ned upgrade", "zero-width",
           (7, 0, 0, 0, 0, 0, 1, 2, 0)),
    _focal("fc23", "“Quoted” text — with dashes",
           "unicode-punctuation",
           (6, 0, 0, 0, 0, 0, 1, 1, 0)),
    _focal("fc24", "Ηοwever", "unicode-lookalike",
           (7, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc25", "Yes, yes; yes: yes.", "adjacent-punctuation",
           (3, 0, 0, 0, 0, 1, 1, 0, 0)),
    _focal("fc26", "A a A a", "letter-a",
           (1, 0, 0, 4, 0, 0, 2, 4, 0)),
    _focal("fc27", "Bee bee BEE", "doubled-letters",
           (3, 3, 0, 0, 3, 0, 4, 0, 0)),
    _focal("fc28", "Sing sings singing", "suffix-ing",
           (7, 0, 2, 0, 0, 0, 1, 0, 0)),
    _focal("fc29", "aaa,bbb,ccc", "digits-and-symbols",
           (3, 1, 0, 0, 3, 2, 0, 1, 0)),
    _focal("fc30", "Happy happy happy day", "suffix-y",
           (5, 0, 0, 0, 3, 0, 1, 4, 4)),
    _focal("fc31", "x", "single-token-output",
           (1, 0, 0, 1, 0, 0, 0, 0, 0)),
    _focal("fc32", "The quick brown fox jumps over the lazy dog.", "plain",
           (5, 1, 0, 0, 0, 0, 1, 1, 1)),
    _focal("fc33", "Twenty words follow here to show a long normal answer "
                   "that a model might produce when it is asked to explain "
                   "something clearly.", "natural-length",
           (9, 0, 1, 2, 1, 0, 1, 8, 2)),
    _focal("fc34", "Ok", "single-token-output",
           (2, 0, 0, 0, 0, 0, 1, 0, 0)),
    _focal("fc35", "Bright books, bold banners; big bells.", "initial-letter",
           (7, 6, 0, 0, 3, 1, 1, 1, 0)),
    _focal("fc36", "one, two, three, four, five, six, seven, eight, nine, "
                   "ten, eleven, twelve, thirteen", "comma-budget",
           (8, 0, 0, 0, 2, 12, 0, 0, 0)),
    _focal("fc37", "ing", "suffix-ing",
           (3, 0, 1, 0, 0, 0, 0, 0, 0)),
    _focal("fc38", "y", "suffix-y",
           (1, 0, 0, 1, 0, 0, 0, 0, 1)),
    _focal("fc39", "Aardvarks and apples are amazing.", "letter-a",
           (9, 0, 1, 0, 2, 0, 1, 5, 0)),
    _focal("fc40", "MiXeD CaSe TeXt", "capitalisation",
           (5, 0, 0, 0, 0, 0, 7, 1, 0)),
    _focal("fc41", "Bunny, buddy, berry.", "doubled-letters",
           (5, 3, 0, 0, 3, 2, 1, 0, 3)),
    _focal("fc42", "The end.The start", "sentence-boundary-punctuation",
           (5, 0, 0, 0, 0, 0, 2, 1, 0)),
    _focal("fc43", "3.14159 42 100", "digits-and-symbols",
           (0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _focal("fc44", "supercalifragilisticexpialidocious", "word-length",
           (34, 0, 0, 0, 0, 0, 0, 1, 0)),
    _focal("fc45", "Type2 errors and 3D models appear in 12pt text.",
           "digits-adjacent-to-words",
           (6, 0, 0, 1, 2, 0, 2, 2, 0)),
)

assert len(ADDED_TARGET_CASES) == 8
assert len(FOCAL_CASES) == 45
assert len({c["case_id"] for c in TARGET_CASES}) == len(TARGET_CASES)
assert len({c["case_id"] for c in FOCAL_CASES}) == len(FOCAL_CASES)

#: §10.2 + §24 exact-count enumeration -> the cases demonstrating each.
TARGET_COVERAGE: dict[str, tuple[str, ...]] = {
    "empty-response": ("bc01", "bc02"),
    "adjacent-punctuation": ("bc03", "bc07", "bc20", "bc39"),
    "capitalisation": ("bc09", "bc10", "bc38", "bc40"),
    "hyphenation": ("bc06",),
    "concatenated-copies": ("bc05", "bc23"),
    "repeated-words": ("bc04", "bc22", "bc29"),
    "non-latin-characters": ("bc12", "bc13", "bc36"),
    "unicode-punctuation": ("ac01",),
    "unicode-lookalikes": ("ac02",),
    "zero-width-characters": ("ac03", "ac04"),
    "non-breaking-and-soft-hyphen": ("ac06", "ac07"),
    "combining-marks": ("ac08",),
    "sentence-boundary-punctuation": ("bc39", "ac05"),
    "truncation-mid-word": ("bc11",),
}

#: §10.2 + §24 word-length and budget enumeration.
FOCAL_COVERAGE: dict[str, tuple[str, ...]] = {
    "empty-output": ("fc01", "fc02"),
    "single-token-output": ("fc03", "fc04", "fc31", "fc34"),
    "hyphenated-forms": ("fc05",),
    "apostrophised-forms": ("fc06",),
    "non-latin-script": ("fc07", "fc08", "fc20"),
    "digits-and-symbols-adjacent": ("fc09", "fc29", "fc43", "fc45"),
    "markdown-emphasis": ("fc10",),
    "adjacent-punctuation": ("fc18", "fc25"),
    "capitalisation": ("fc17", "fc40"),
    "repeated-words": ("fc16", "fc27"),
    "unicode-punctuation": ("fc23",),
    "unicode-lookalikes": ("fc24",),
    "zero-width-characters": ("fc22",),
    "sentence-boundary-punctuation": ("fc42",),
    "doubled-letters": ("fc11", "fc12", "fc27", "fc41"),
    "single-letter-words": ("fc15", "fc26"),
    "suffix-ing": ("fc14", "fc28", "fc37"),
    "suffix-y": ("fc30", "fc38"),
    "initial-letter-b": ("fc13", "fc35"),
    "letter-a": ("fc26", "fc39"),
    "comma-budget": ("fc36",),
    "extreme-word-length": ("fc19", "fc44"),
}


def assert_coverage() -> dict[str, int]:
    """Every enumerated §24 case names at least one suite member that exists."""
    target_ids = {c["case_id"] for c in TARGET_CASES}
    focal_ids = {c["case_id"] for c in FOCAL_CASES}
    for label, ids in TARGET_COVERAGE.items():
        missing = [i for i in ids if i not in target_ids]
        if not ids or missing:
            raise ProtocolError(f"exact-count coverage {label!r} names "
                                f"{missing or 'nothing'}")
    for label, ids in FOCAL_COVERAGE.items():
        missing = [i for i in ids if i not in focal_ids]
        if not ids or missing:
            raise ProtocolError(f"word-length coverage {label!r} names "
                                f"{missing or 'nothing'}")
    return {"target_cases": len(TARGET_CASES),
            "focal_cases": len(FOCAL_CASES),
            "target_coverage_categories": len(TARGET_COVERAGE),
            "focal_coverage_categories": len(FOCAL_COVERAGE)}


def carried_specification() -> str:
    """Canonical serialisation of the carried A-side data, hashed for the
    §10.2 carry-over record. Identical in shape to the v3 serialisation, so
    the two hashes are directly comparable."""
    rows = [{"case_id": c["case_id"], "text": c["text"], "s0": c["s0"],
             "s1": c["s1"], "s2": c["s2"]} for c in CARRIED_CASES]
    return canonical_json(rows)


def carried_specification_hash() -> str:
    return sha_text(carried_specification())


def suite_hash() -> str:
    """One hash over every frozen suite, bound in the Gate 1 record beside the
    canonical verifier hash. Frozen suites are expectations, not scoring
    semantics, so they are deliberately outside the §10.6 verifier hash."""
    payload = {"target": [{k: v for k, v in c.items() if k != "v3_stats"}
                          for c in TARGET_CASES],
               "focal": list(FOCAL_CASES)}
    return sha_text(canonical_json(payload))


def evaluate_suites() -> dict:
    """Execute every primary verifier over its frozen suite (§10.2).

    Returns per-instrument agreement; Gate 1 requires exactly 1.000 for each.
    """
    from dci1v4.verifiers import statistics as stats_mod
    from dci1v4.verifiers import target as target_mod
    from dci1v4.verifiers.compliance import score_constraint
    from dci1v4.verifiers.constraints import (
        FOCAL_GRID,
        REFERENCE_LADDERS,
        Constraint,
        TARGET_GRID,
    )

    failures: list[dict] = []

    for case in TARGET_CASES:
        text = case["text"]
        got = {"s0": target_mod.s0_count(text), "s1": target_mod.s1_count(text),
               "s2": target_mod.s2_count(text)}
        for key in ("s0", "s1", "s2"):
            if got[key] != case[key]:
                failures.append({"instrument": "A", "case": case["case_id"],
                                 "check": key, "expected": case[key],
                                 "observed": got[key]})
        for n in TARGET_GRID:
            expected = case["s0"] == n
            observed = score_constraint(Constraint("A", n), text,
                                        truncated=False).passed
            if observed != expected:
                failures.append({"instrument": "A", "case": case["case_id"],
                                 "check": f"pass@n={n}", "expected": expected,
                                 "observed": observed})

    for case in FOCAL_CASES:
        text, expected_stats = case["text"], case["stats"]
        observed = stats_mod.focal_statistic(text)
        if observed != expected_stats["B"]:
            failures.append({"instrument": "B", "case": case["case_id"],
                             "check": "statistic",
                             "expected": expected_stats["B"],
                             "observed": observed})
        for m in FOCAL_GRID:
            want = expected_stats["B"] <= m
            got_pass = score_constraint(Constraint("B", m), text,
                                        truncated=False).passed
            if got_pass != want:
                failures.append({"instrument": "B", "case": case["case_id"],
                                 "check": f"pass@m={m}", "expected": want,
                                 "observed": got_pass})
        for family, ladder in REFERENCE_LADDERS.items():
            stat = stats_mod.FAMILY_STATISTICS[family](text)
            if stat != expected_stats[family]:
                failures.append({"instrument": family,
                                 "case": case["case_id"], "check": "statistic",
                                 "expected": expected_stats[family],
                                 "observed": stat})
                continue
            for q in ladder:
                want = expected_stats[family] <= q
                got_pass = score_constraint(Constraint(family, q), text,
                                            truncated=False).passed
                if got_pass != want:
                    failures.append({"instrument": family,
                                     "case": case["case_id"],
                                     "check": f"pass@q={q}", "expected": want,
                                     "observed": got_pass})

    instruments = ("A", "B") + tuple(REFERENCE_LADDERS)
    failed_cases = {i: {f["case"] for f in failures if f["instrument"] == i}
                    for i in instruments}
    totals = {"A": len(TARGET_CASES)}
    totals.update({i: len(FOCAL_CASES) for i in instruments if i != "A"})
    agreement = {i: (totals[i] - len(failed_cases[i])) / totals[i]
                 for i in instruments}
    return {"cases": totals, "agreement": agreement, "failures": failures,
            "coverage": assert_coverage(), "suite_hash": suite_hash()}
