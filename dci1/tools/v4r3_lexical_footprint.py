"""What §7.3's word costs: the fragment reading, measured on real responses.

**The observation.** §7.3 registers a word as *a maximal run of alphabetic
characters, where alphabetic is Unicode general category L*. An apostrophe is
not category L and neither is a hyphen, so `don't` is two words --- `don` and
`t` --- and `well-known` is two words, and `It's` is `It` and `s`. The
verifier implements that faithfully; `verifier_audit` showed the consequence on
fourteen of its hundred and twenty-eight cards, as bare `t` and `s` tokens
inside matched lists, and none was marked wrong.

**So this is not a defect and this tool does not treat it as one.** It is a
construct-validity question, which is §10.5's third question and which the
preregistration says in terms is *bounded by §9.3 and §24 and not resolved by
this study*. What was missing was its size. A registered choice whose footprint
is unknown is a choice nobody has actually made.

**What is measured.** A seventh reading --- deliberately **not** one of
§10.4-R2's six registered defects, because it is not a defect --- in which an
internal apostrophe or hyphen does not break a word. That is the reader's word,
and the difference between it and the registered word is the whole footprint.
Both the numerator and the rate denominator are recomputed under it, because a
fragment inflates both.

Read-only, load 0 and load 1 only, no composed cell, no estimand. It changes
no verifier, no preregistration, no candidate and no record.

    python3 tools/v4r3_lexical_footprint.py
"""
from __future__ import annotations

import collections
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.errors import ProtocolError                          # noqa: E402
from dci1v4.protocol.hashing import canonical_json, sha_text     # noqa: E402
from dci1v4r3 import CLASSIFICATION                              # noqa: E402
from dci1v4r3.protocol import constants as C                     # noqa: E402
from dci1v4r3.stages.human_audit import natural_pool             # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash              # noqa: E402
from dci1v4r3.verifiers.compliance import passes                 # noqa: E402
from dci1v4r3.verifiers.constraints import (                     # noqa: E402
    FAMILIES, FORM_COUNT, FORM_EXACT, FORM_LOWER_BOUND, FORM_RATE,
    FORM_RATE_LOWER_BOUND, Constraint,
)
from dci1v4r3.verifiers.statistics import STATISTICS, word_count  # noqa: E402
from dci1v4r3.verifiers.words import alpha_runs                  # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r3" / "lexical_footprint.json"

#: The characters that join two alphabetic runs into one reader's word: the
#: two apostrophes a text actually uses and the two hyphens.
JOINERS = "'’‐-"


def reader_words(text: str) -> list[str]:
    """`alpha_runs`, but a single joiner between two runs does not break them.

    Built on `str.isalpha` --- §7.3's own alphabetic test, Unicode category L
    --- rather than on a regex character class. A first attempt used a
    word-character class minus digits and underscore, which admits Unicode
    category No: `H₂O` came out as one token where §7.3 gives
    `H` and `O`, and the diagnostic then charged that difference to the
    apostrophe rule. The test that caught it is
    `test_the_two_readings_agree_where_no_joiner_occurs`, and this function is
    written against the same predicate the registered rule uses so that the
    only difference between the two readings is the joiner.
    """
    words: list[str] = []
    current: list[str] = []
    pending: str | None = None
    for ch in text:
        if ch.isalpha():
            if pending is not None and current:
                current.append(pending)
            pending = None
            current.append(ch)
        elif ch in JOINERS and current and pending is None:
            pending = ch                       # joins only if a letter follows
        else:
            pending = None
            if current:
                words.append("".join(current))
                current = []
    if current:
        words.append("".join(current))
    return words

#: §11.8's smallest effect of interest and the order of magnitude below it,
#: carried from the defect-sensitivity diagnostic so the two are read on one
#: scale. Diagnostic bands, **not** registered criteria.
CONSEQUENTIAL = C.SMALLEST_EFFECT_OF_INTEREST
DETECTABLE = 0.01


def reader_statistic(statistic_id: str, text: str) -> int | None:
    """The numerator under the reader's word, for the word-shaped numerators.

    The character-shaped numerators --- `comma`, `semicolon`, `capital_char`
    --- read raw characters and cannot move, and `sentence` is not a property
    of the word list at all. They return None and are excluded rather than
    reported as unchanged, because "unchanged" would imply the question
    applied to them.
    """
    words = reader_words(text)
    lowered = [w.lower() for w in words]
    if statistic_id == "b_initial":
        return sum(1 for w in lowered if w.startswith("b"))
    if statistic_id == "t_initial":
        return sum(1 for w in lowered if w.startswith("t"))
    if statistic_id == "ing_final":
        return sum(1 for w in lowered if w.endswith("ing"))
    if statistic_id == "s_final":
        return sum(1 for w in lowered if w.endswith("s"))
    if statistic_id == "y_final":
        return sum(1 for w in lowered if w.endswith("y"))
    if statistic_id == "one_letter":
        return sum(1 for w in words if len(w) == 1)
    if statistic_id == "letter_a":
        return sum(1 for w in lowered if "a" in w)
    if statistic_id == "vowel_initial":
        return sum(1 for w in lowered if w[:1] in "aeiou")
    if statistic_id == "doubled_letter":
        return sum(1 for w in lowered
                   if any(a == b for a, b in zip(w, w[1:])))
    if statistic_id == "capital_word":
        return sum(1 for w in words if any(c.isupper() for c in w))
    return None


def reader_verdict(kind: str, severity: int, text: str) -> bool | None:
    """The verdict under the reader's word, numerator and denominator both."""
    statistic = reader_statistic(FAMILIES[kind].statistic_id, text)
    if statistic is None:
        return None
    form = FAMILIES[kind].form
    if form == FORM_COUNT:
        return statistic <= severity
    if form == FORM_EXACT:
        return statistic == severity
    if form == FORM_LOWER_BOUND:
        return statistic >= severity
    if form not in (FORM_RATE, FORM_RATE_LOWER_BOUND):
        # Fail closed, as `compliance.passes` does. A form added later must
        # be given a reading here deliberately, not inherit a rate one by
        # falling off the end of this function.
        raise ProtocolError(f"no reader's-word reading for form {form!r}")
    words = len(reader_words(text))
    if not words:
        return False
    rate = 100.0 * statistic / words
    return rate <= severity if form == FORM_RATE else rate >= severity


def _band(rate: float) -> str:
    if rate >= CONSEQUENTIAL:
        return "consequential"
    if rate >= DETECTABLE:
        return "detectable"
    return "negligible"


def main() -> int:
    pool = natural_pool()
    texts = sorted({item["response"] for item in pool})

    registered = joined = 0
    splits: collections.Counter[str] = collections.Counter()
    for text in texts:
        registered += word_count(text)
        joined += len(reader_words(text))
        for token in text.split():
            stripped = token.strip(".,;:!?\"()[]{}*_")
            if len(reader_words(stripped)) == 1 and \
                    len(alpha_runs(stripped)) > 1:
                splits["".join(c for c in stripped
                               if not c.isalnum())] += 1

    changed: collections.Counter[str] = collections.Counter()
    total: collections.Counter[str] = collections.Counter()
    by_family: collections.Counter[str] = collections.Counter()
    fam_total: collections.Counter[str] = collections.Counter()
    canon_pass = reader_pass = seen = 0
    for item in pool:
        kind, severity = item["kind"], item["severity"]
        if kind in ("A", "B"):
            continue
        statistic_id = FAMILIES[kind].statistic_id
        other = reader_verdict(kind, severity, item["response"])
        if other is None:
            continue
        constraint = Constraint(kind, severity, extended=True, reserve=True)
        here = passes(constraint,
                      STATISTICS[statistic_id](item["response"]),
                      item["response"])
        seen += 1
        canon_pass += here
        reader_pass += other
        total[statistic_id] += 1
        fam_total[kind] += 1
        if other != here:
            changed[statistic_id] += 1
            by_family[kind] += 1

    overall = sum(changed.values()) / seen if seen else 0.0
    payload = {
        "artifact_type": "v4r3-lexical-footprint",
        "classification": CLASSIFICATION,
        "purpose": "size the registered §7.3 word against a reader's word. "
                   "Read-only. Not a defect analysis: the verifier implements "
                   "§7.3 faithfully and this measures what §7.3 costs.",
        "registered_rule": "a word is a maximal run of alphabetic characters, "
                           "Unicode general category L (§7.3), so an "
                           "apostrophe and a hyphen both end a word",
        "the_alternative": "a reader's word, in which one internal apostrophe "
                           "or hyphen does not break a word. NOT one of "
                           "§10.4-R2's six registered defects, because it is "
                           "not a misreading of the registered rule --- it is "
                           "a different rule.",
        "not_resolved_by_this_study": "§10.5 question 3, construct validity, "
                                      "which the preregistration bounds by "
                                      "§9.3 and §24 and does not resolve",
        "canonical_verifier_hash": verifier_source_hash(),
        "responses": len(texts),
        "segmentation": {
            "registered_words": registered,
            "reader_words": joined,
            "words_added_by_the_registered_rule": registered - joined,
            "share_of_the_rate_denominator":
                (registered - joined) / registered if registered else None,
            "what_it_splits_on": dict(splits.most_common(10)),
        },
        "verdicts": {
            "compared": seen,
            "changed": sum(changed.values()),
            "change_rate": overall,
            "band": _band(overall),
            "canonical_pass_rate": canon_pass / seen if seen else None,
            "reader_pass_rate": reader_pass / seen if seen else None,
        },
        # Keyed by identifier, plus an explicit ranking: the artifact is
        # written with sorted keys so it canonicalises, which means dict order
        # carries no information and a reader who wants "worst first" needs it
        # as data.
        "by_numerator": {
            statistic_id: {
                "n": total[statistic_id],
                "changed": changed[statistic_id],
                "change_rate": changed[statistic_id] / total[statistic_id],
                "band": _band(changed[statistic_id] / total[statistic_id]),
            }
            for statistic_id in total
        },
        "numerators_worst_first": [
            statistic_id for statistic_id in
            sorted(total, key=lambda s: (-changed[s] / max(1, total[s]), s))
        ],
        "by_family": {
            kind: {"n": fam_total[kind], "changed": by_family[kind],
                   "change_rate": by_family[kind] / fam_total[kind]}
            for kind in fam_total
        },
        "families_worst_first": [
            kind for kind in
            sorted(fam_total,
                   key=lambda k: (-by_family[k] / max(1, fam_total[k]), k))
        ],
        "excluded": {
            "numerators": ["comma", "semicolon", "capital_char", "sentence"],
            "why": "the first three read raw characters and cannot move; "
                   "`sentence` is not a property of the word list. Reporting "
                   "them as unchanged would imply the question applied.",
            "instruments": ["A", "B"],
            "why_those": "A's §9.2 counter is registered fold-then-segment "
                         "and is carried byte-identically from the closed v3 "
                         "instrument; B is a max over runs, not a count.",
        },
        "bands": {"consequential_at_or_above": CONSEQUENTIAL,
                  "detectable_at_or_above": DETECTABLE,
                  "provenance": "diagnostic bands, NOT registered criteria; "
                                "the upper line is §11.8's smallest effect of "
                                "interest. Carried from the defect-sensitivity "
                                "diagnostic so the two read on one scale."},
        "reads": "load 0 and load 1 rows only; no composed cell enters",
        "computes_no_composed_estimand": True,
        "producing_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=DCI1, capture_output=True,
            text=True, check=False).stdout.strip(),
        "generated_at": _dt.datetime.now(_dt.timezone.utc)
                           .isoformat(timespec="seconds"),
    }
    payload["report_hash"] = sha_text(canonical_json(
        {k: v for k, v in payload.items() if k != "generated_at"}))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "responses": payload["responses"],
        "rate_denominator_inflation":
            payload["segmentation"]["share_of_the_rate_denominator"],
        "verdicts": payload["verdicts"],
        "worst_numerators": {k: payload["by_numerator"][k]["change_rate"]
                             for k in payload["numerators_worst_first"][:4]},
        "report": str(OUT.relative_to(DCI1)),
    }, indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
