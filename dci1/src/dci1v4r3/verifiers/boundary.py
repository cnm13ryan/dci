"""Frozen boundary suites for every v4r3 instrument (§10.2, §24).

The suite is one corpus of case texts, and every verifier in the final
instrument population is evaluated against all of it. That is what makes the
"at least forty cases per verifier" requirement true for 22 verifiers without
22 disjoint corpora: a case text exercises the segmenter, and the segmenter is
what every verifier shares.

Three sources, kept separate because their evidential standing differs:

* **``CARRIED_TARGET_CASES``** — the forty v3 case texts with their S0/S1/S2
  expectations plus the eight v4-authored Unicode cases, read from
  ``dci1v4.verifiers.boundary`` **as data**. $A$'s carry-over survives into
  v4r3 (§7.0: the exact-count rule is untouched), so these are carried
  evidence and ``carryover.py`` refuses on drift.
* **``CARRIED_FOCAL_CASES``** — the forty-five v4-authored texts with their
  hand-derived statistic vectors, likewise read as data. They are v4 evidence
  and are carried into v4r3 only because a check re-derives every one of their
  round-0 statistics under v4r3's corrected lexical rule and finds no change:
  none of the forty-five contains U+0130, which is the whole scope of the
  correction.
* **``V4R3_CASES``** — forty texts authored for this revision, covering what
  the new predicate forms and the corrected rule require and the carried
  corpus does not: the case-folding split itself, rates straddling
  representative severities from both sides, a wordless and a single-word
  answer against the rate forms, counts at $q-1$, $q$ and $q+1$ against the
  lower bounds, the non-vacuity boundary at nineteen and twenty words, and a
  wider Unicode sweep.

**Where the v4r3 expectations come from.** Each was produced by §10.2's
prose-only reimplementation and cross-checked against the primary before being
frozen here; the two agree exactly on all forty. A frozen number that both
implementations produce is evidence about the rule. A frozen number that only
one produces would be a transcription of that one, and this module would then
be measuring itself.
"""
from __future__ import annotations

from typing import Any

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import canonical_json, sha_text
from dci1v4.verifiers import boundary as _v4_boundary

from dci1v4r3.verifiers.compliance import graded, non_vacuous, passes
from dci1v4r3.verifiers.constraints import (
    FAMILIES, Constraint, TARGET_GRID, declared_range, focal_severities,
)
from dci1v4r3.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)
from dci1v4r3.verifiers.constraints import (
    R3_STATISTIC_IDS, STATISTIC_IDS,
)
from dci1v4r3.verifiers.boundary_r3 import R3_CASES, R3_STATS

#: The nine numerators registered at round 0, in their registered order.
_ROUND0_STATISTIC_IDS = tuple(k for k in STATISTIC_IDS
                              if k not in R3_STATISTIC_IDS)

__all__ = ["CARRIED_TARGET_CASES", "CARRIED_FOCAL_CASES", "V4R3_CASES",
           "R3_AUTHORED_CASES",
           "ALL_CASES", "assert_carried_focal_cases_unchanged",
           "assert_coverage", "suite_hash", "evaluate_suites",
           "instrument_population"]


def _case(case_id: str, text: str, covers: str, *, w: int, b: int,
          stats: tuple[int, ...], r3: tuple[int, ...] | None = None,
          origin: str = "authored_v4r3") -> dict[str, Any]:
    """One frozen case.

    ``stats`` is the nine numerators registered at round 0, in their
    registered order, and those numbers are the ones frozen before the R3
    amendment and are unchanged by it. ``r3`` is the six numerators the
    amendment adds; for a case authored before the amendment it comes from
    ``R3_STATS`` and the case's own call site stays byte-identical, so a
    reader can see at a glance which numbers are carried and which are new.
    """
    if len(stats) != len(_ROUND0_STATISTIC_IDS):
        raise ProtocolError(f"{case_id}: expected "
                            f"{len(_ROUND0_STATISTIC_IDS)} statistics, one "
                            "per numerator registered at round 0")
    extra = R3_STATS[case_id] if r3 is None else r3
    if len(extra) != len(R3_STATISTIC_IDS):
        raise ProtocolError(f"{case_id}: expected {len(R3_STATISTIC_IDS)} "
                            "R3 statistics")
    return {"case_id": case_id, "text": text, "covers": covers,
            "origin": origin, "word_count": w, "focal": b,
            "stats": {**dict(zip(_ROUND0_STATISTIC_IDS, stats)),
                      **dict(zip(R3_STATISTIC_IDS, extra))}}


CARRIED_TARGET_CASES: tuple[dict, ...] = tuple(
    {**case, "origin": f"carried_{case['origin']}"}
    for case in _v4_boundary.CARRIED_CASES + _v4_boundary.ADDED_TARGET_CASES)

CARRIED_FOCAL_CASES: tuple[dict, ...] = tuple(
    {"case_id": case["case_id"], "text": case["text"],
     "covers": case["covers"], "origin": "carried_v4",
     "v4_stats": dict(case["stats"])}
    for case in _v4_boundary.FOCAL_CASES)

#: Authored for v4r3; see the module docstring for how the numbers were made.
V4R3_CASES: tuple[dict, ...] = (
    _case('vc01', 'İstanbul is big', 'case-folding-split;combining-mark',
          w=3, b=8,
          stats=(1, 0, 0, 0, 0, 0, 1, 1, 0)),
    _case('vc02', 'İİİ', 'case-folding-split;repeated',
          w=1, b=3,
          stats=(0, 0, 0, 0, 0, 0, 1, 0, 0)),
    _case('vc03', 'a', 'single-word-answer;one-letter',
          w=1, b=1,
          stats=(0, 0, 1, 0, 0, 0, 0, 1, 0)),
    _case('vc04', 'aa', 'single-word-answer;doubled-letter',
          w=1, b=2,
          stats=(0, 0, 0, 1, 0, 0, 0, 1, 0)),
    _case('vc05', 'bay bay bay bay', 'rate-straddle;b-initial-100pc',
          w=4, b=3,
          stats=(4, 0, 0, 0, 0, 0, 0, 4, 4)),
    _case('vc06', 'bay cot cot cot', 'rate-straddle;b-initial-25pc',
          w=4, b=3,
          stats=(1, 0, 0, 0, 0, 0, 0, 1, 1)),
    _case('vc07', 'bay cot cot cot cot cot cot cot', 'rate-straddle;b-initial-12pc',
          w=8, b=3,
          stats=(1, 0, 0, 0, 0, 0, 0, 1, 1)),
    _case('vc08', 'a cot cot cot cot cot cot cot cot cot cot cot', 'rate-straddle;one-letter-8pc',
          w=12, b=3,
          stats=(0, 0, 1, 0, 0, 0, 0, 1, 0)),
    _case('vc09', 'going going going cot', 'rate-straddle;ing-final-75pc',
          w=4, b=5,
          stats=(0, 3, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc10', 'Cot cot cot cot', 'rate-straddle;capital-word-25pc',
          w=4, b=3,
          stats=(0, 0, 0, 0, 0, 1, 1, 0, 0)),
    _case('vc11', 'COT cot cot cot cot cot cot cot', 'rate-straddle;capital-word-12pc',
          w=8, b=3,
          stats=(0, 0, 0, 0, 0, 3, 1, 0, 0)),
    _case('vc12', 'one, two, three', 'comma-rate;two-per-three-words',
          w=3, b=5,
          stats=(0, 0, 0, 1, 2, 0, 0, 0, 0)),
    _case('vc13', 'one,two', 'comma-rate;adjacent-punctuation',
          w=2, b=3,
          stats=(0, 0, 0, 0, 1, 0, 0, 0, 0)),
    _case('vc14', 'happy sunny windy rainy', 'y-final-100pc;lower-bound-4',
          w=4, b=5,
          stats=(0, 0, 0, 2, 0, 0, 0, 2, 4)),
    _case('vc15', 'happy sunny windy cot', 'y-final-75pc;lower-bound-3',
          w=4, b=5,
          stats=(0, 0, 0, 2, 0, 0, 0, 1, 3)),
    _case('vc16', 'happy sunny cot cot', 'y-final-50pc;lower-bound-2',
          w=4, b=5,
          stats=(0, 0, 0, 2, 0, 0, 0, 1, 2)),
    _case('vc17', 'happy cot cot cot', 'y-final-25pc;lower-bound-1',
          w=4, b=5,
          stats=(0, 0, 0, 1, 0, 0, 0, 1, 1)),
    _case('vc18', 'cot cot cot cot', 'y-final-0pc;lower-bound-0',
          w=4, b=3,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc19', 'bell bell bell', 'doubled-letter-100pc',
          w=3, b=4,
          stats=(3, 0, 0, 3, 0, 0, 0, 0, 0)),
    _case('vc20', 'bell bell cot', 'doubled-letter-67pc',
          w=3, b=4,
          stats=(2, 0, 0, 2, 0, 0, 0, 0, 0)),
    _case('vc21', 'soft\xadhyphen inside', 'soft-hyphen',
          w=3, b=6,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc22', 'zero\u200bwidth inside', 'zero-width',
          w=3, b=6,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc23', 'non\xa0breaking space', 'non-breaking-space',
          w=3, b=8,
          stats=(1, 1, 0, 0, 0, 0, 0, 2, 0)),
    _case('vc24', 'café combining', 'combining-mark',
          w=2, b=9,
          stats=(0, 1, 0, 0, 0, 0, 0, 1, 0)),
    _case('vc25', 'Ⅷ roman numeral', 'non-decimal-numeric',
          w=2, b=7,
          stats=(0, 0, 0, 0, 0, 0, 0, 2, 0)),
    _case('vc26', 'H₂O formula', 'subscript-numeric',
          w=3, b=7,
          stats=(0, 0, 2, 0, 0, 2, 2, 1, 0)),
    _case('vc27', 'ＡＢＣ fullwidth', 'fullwidth-lookalike',
          w=2, b=9,
          stats=(0, 0, 0, 1, 0, 0, 1, 0, 0)),
    _case('vc28', 'аpple lookalike', 'cyrillic-lookalike',
          w=2, b=9,
          stats=(0, 0, 0, 2, 0, 0, 0, 1, 0)),
    _case('vc29', '**bold** and _under_', 'markdown-emphasis',
          w=3, b=5,
          stats=(1, 0, 0, 0, 0, 0, 0, 1, 0)),
    _case('vc30', 'however however however however', 'repeated-word;target',
          w=4, b=7,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc31', 'The answer:\nhowever stands alone', 'colon-terminated-preamble',
          w=5, b=7,
          stats=(0, 0, 0, 0, 0, 1, 1, 3, 0)),
    _case('vc32', 'cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot', 'twenty-words;non-vacuity-boundary',
          w=20, b=3,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc33', 'cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot cot', 'nineteen-words;non-vacuity-boundary',
          w=19, b=3,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc34', 'extraordinarilycomplicated', 'long-word;focal-26',
          w=1, b=26,
          stats=(0, 0, 0, 0, 0, 0, 0, 1, 0)),
    _case('vc35', 'abcdefg abcdefgh', 'focal-boundary-7-8',
          w=2, b=8,
          stats=(0, 0, 0, 0, 0, 0, 0, 2, 0)),
    _case('vc36', 'Bay, Bay, Bay', 'capital-and-comma-and-b',
          w=3, b=3,
          stats=(3, 0, 0, 0, 2, 3, 3, 3, 3)),
    _case('vc37', 'aaa aaa aaa', 'letter-a-100pc;doubled-100pc',
          w=3, b=3,
          stats=(0, 0, 0, 3, 0, 0, 0, 3, 0)),
    _case('vc38', 'ǅombie word', 'titlecase-letter',
          w=2, b=6,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc39', 'ﬁnal ligature', 'ligature',
          w=2, b=8,
          stats=(0, 0, 0, 0, 0, 0, 0, 2, 0)),
    _case('vc40', 'one two three four five six seven eight nine ten', 'ten-words;plain',
          w=10, b=5,
          stats=(0, 0, 0, 1, 0, 0, 0, 0, 0)),
    _case('vc41', 'however however', 'concatenated-copies;repeated',
          w=2, b=7,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
    _case('vc42', 'howeverhowever stands', 'concatenated-copies;no-boundary',
          w=2, b=14,
          stats=(0, 0, 0, 0, 0, 0, 0, 1, 0)),
    _case('vc43', 'the sentence stops mid wo', 'truncated-mid-word',
          w=5, b=8,
          stats=(0, 0, 0, 0, 0, 0, 0, 0, 0)),
)


#: §7.0-R3's own cases, rebuilt through ``_case`` so they pass the same
#: shape checks the authored v4r3 cases do.
R3_AUTHORED_CASES: tuple[dict, ...] = tuple(
    _case(c["case_id"], c["text"], c["covers"], w=c["word_count"],
          b=c["focal"], stats=c["round0"], r3=c["r3"], origin=c["origin"])
    for c in R3_CASES)

ALL_CASES: tuple[dict, ...] = (CARRIED_TARGET_CASES + CARRIED_FOCAL_CASES
                               + V4R3_CASES + R3_AUTHORED_CASES)

#: §10.2's carry-over condition for the focal corpus, stated as a mapping from
#: v4's family keys to v4r3's numerators. RF6 counts upper-case characters and
#: v4r3 calls that numerator ``capital_char``; ``capital_word`` is new in v4r3
#: and has no v4 column, which is why it is absent here and why §10.2 requires
#: CR6 to earn its own evidence.
_V4_STAT_KEYS = {"B": None, "RF1": "b_initial", "RF2": "ing_final",
                 "RF3": "one_letter", "RF4": "doubled_letter",
                 "RF5": "comma", "RF6": "capital_char", "RF7": "letter_a",
                 "RF8": "y_final"}


def assert_carried_focal_cases_unchanged() -> dict[str, int]:
    """Every v4 statistic on every carried focal case is unchanged in v4r3.

    This is the §7.0 correction's scope claim applied to the one corpus that
    would notice: if a carried case did contain U+0130 its frozen expectation
    would be a v4 number that v4r3 does not produce, and carrying it would
    import a defect as evidence.
    """
    for case in CARRIED_FOCAL_CASES:
        text = case["text"]
        for v4_key, numerator in _V4_STAT_KEYS.items():
            expected = case["v4_stats"][v4_key]
            got = (focal_statistic(text) if numerator is None
                   else STATISTICS[numerator](text))
            if got != expected:
                raise ProtocolError(
                    f"{case['case_id']}: v4 froze {v4_key} = {expected} and "
                    f"v4r3 computes {got}. The §7.0 correction is scoped to "
                    "U+0130 and this case has escaped that scope, so the "
                    "carry-over is void for it")
    return {"cases": len(CARRIED_FOCAL_CASES),
            "statistics_checked": len(CARRIED_FOCAL_CASES) * len(_V4_STAT_KEYS)}


def instrument_population() -> list[tuple[str, int]]:
    """Every (kind, severity) §10.2 requires evidence for: the declared range."""
    population = [("A", n) for n in TARGET_GRID]
    population += [("B", m) for m in focal_severities(extended=True)]
    for kind in FAMILIES:
        population += [(kind, q) for q in declared_range(kind)]
    return population


#: The §24 phenomena §10.2 enumerates. Every one must be covered by at least
#: one case, and ``assert_coverage`` names the ones that are not.
REQUIRED_COVERAGE = (
    "empty-output", "single-token-output", "single-word-answer",
    "adjacent-punctuation", "capitalisation", "hyphenated-form",
    "concatenated-copies", "repeated", "non-latin-script",
    "unicode-punctuation", "lookalike", "zero-width", "combining-mark",
    "soft-hyphen", "truncated-mid-word", "markdown-emphasis",
    "non-decimal-numeric", "case-folding-split", "rate-straddle",
    "lower-bound", "non-vacuity-boundary",
    # §7.0-R3's phenomena. Sentence segmentation brings three of its own, the
    # exact-count form brings the three-point threshold sweep, and the two
    # over-counts the sentence rule knowingly accepts are enumerated here so
    # that "we knew" is checkable rather than asserted.
    "sentence-boundary", "unterminated-tail", "terminator-run",
    "abbreviation-overcount", "decimal-overcount", "exact-count",
    "threshold-minus-one", "threshold-plus-one", "substring-not-word",
    "vowel-initial", "y-is-not-a-vowel", "s-final", "t-initial",
    "semicolon-run",
)


def assert_coverage() -> dict[str, Any]:
    """Every enumerated phenomenon has a case, and every verifier has forty."""
    labels: set[str] = set()
    for case in ALL_CASES:
        for token in str(case.get("covers", "")).replace(",", ";").split(";"):
            token = token.strip()
            if token:
                labels.add(token)
    missing = [phenomenon for phenomenon in REQUIRED_COVERAGE
               if not any(phenomenon in label for label in labels)]
    if missing:
        raise ProtocolError(f"§24 enumerates phenomena with no boundary case: "
                            f"{missing}")
    if len(ALL_CASES) < 40:
        raise ProtocolError("§10.2 requires at least forty cases per verifier "
                            f"and the corpus holds {len(ALL_CASES)}")
    return {"cases": len(ALL_CASES), "labels": len(labels),
            "carried_target": len(CARRIED_TARGET_CASES),
            "carried_focal": len(CARRIED_FOCAL_CASES),
            "authored_v4r3": len(V4R3_CASES),
            "authored_r3": len(R3_AUTHORED_CASES),
            "instruments": len(instrument_population())}


def _frozen_payload() -> list[dict[str, Any]]:
    return [{"case_id": c["case_id"], "text": c["text"],
             "covers": c.get("covers"), "origin": c["origin"],
             "expectations": {k: v for k, v in c.items()
                              if k in ("s0", "s1", "s2", "word_count",
                                       "focal", "stats", "v4_stats")}}
            for c in ALL_CASES]


def suite_hash() -> str:
    """One hash over every case text and every frozen expectation."""
    return sha_text(canonical_json(_frozen_payload()))


def evaluate_suites() -> dict[str, Any]:
    """Run every registered verifier over the whole corpus at every severity.

    Returns the agreement of the primary against the frozen expectations, and
    the realised distribution of verdicts, which §24 reports.
    """
    from dci1v4.verifiers.target import s0_count, s1_count, s2_count

    failures: list[str] = []
    checked = 0
    for case in ALL_CASES:
        text = case["text"]
        if "s0" in case:
            for rule, fn in (("s0", s0_count), ("s1", s1_count),
                             ("s2", s2_count)):
                checked += 1
                if fn(text) != case[rule]:
                    failures.append(f"{case['case_id']}:{rule}")
        if "stats" in case:
            checked += 1
            if word_count(text) != case["word_count"]:
                failures.append(f"{case['case_id']}:word_count")
            if focal_statistic(text) != case["focal"]:
                failures.append(f"{case['case_id']}:focal")
            for numerator, expected in case["stats"].items():
                checked += 1
                if STATISTICS[numerator](text) != expected:
                    failures.append(f"{case['case_id']}:{numerator}")

    verdicts = {"pass": 0, "fail": 0, "vacuous_pass": 0}
    for kind, severity in instrument_population():
        constraint = Constraint(kind, severity, extended=True, reserve=True) \
            if kind != "A" else Constraint(kind, severity)
        for case in ALL_CASES:
            text = case["text"]
            statistic = (s0_count(text) if kind == "A" else
                         focal_statistic(text) if kind == "B" else
                         STATISTICS[FAMILIES[kind].statistic_id](text))
            ok = passes(constraint, statistic, text)
            nv = non_vacuous(constraint, text, truncated=False)
            score = graded(constraint, statistic, text)
            if not 0.0 <= score <= 1.0:
                failures.append(f"{case['case_id']}:{kind}:{severity}:graded")
            verdicts["pass" if ok else "fail"] += 1
            if ok and not nv:
                verdicts["vacuous_pass"] += 1
    return {"agreement": 1.0 if not failures else 0.0,
            "checked": checked, "failures": failures,
            "verdicts": verdicts, "suite_hash": suite_hash(),
            **assert_coverage()}
