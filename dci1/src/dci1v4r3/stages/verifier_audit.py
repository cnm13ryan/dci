"""Operationalization cards: what the verifier did, shown so a person can check it.

**Why this exists.** §10.3 asks a human to label a response blind, which means
counting the qualifying words in a hundred-word answer by hand. That is the
same arithmetic task §10.4 handed a judge, and it is why §10.4 failed: the
counting swamps the judgment. A person auditing 300 of them is slower than the
judge was and no more reliable at the part that is mechanical.

But *checking* a verifier is not the same task as *replacing* it. §10.4-R
already registers the right unit for checking, the **operationalization card**:
the instruction as the model received it; the answer; the registered
segmentation convention; the numerator and what it counts; the denominator and
what it counts; the derived quantity with its arithmetic shown; the predicate
form, direction and threshold; and the recorded verdict. *The arithmetic is
shown, not requested.* R1 built that for an LLM. This builds it for a person,
which is the reader it was always better suited to.

So the question this module asks is not "what is the right label?" but "did
this program count the right things?" --- and it makes that answerable in
seconds by showing **which tokens it counted**, not just how many.

**The decomposition cannot drift from the verifier.** A display that
re-derives what the verifier does is a second implementation, and a second
implementation that disagrees silently is worse than no display at all. So the
matched tokens are not recomputed: each unit is put through *the registered
statistic itself*, and a unit is matched when the registered function returns
one for it alone. `decompose` then checks that the per-unit probes sum to the
whole-text statistic and marks itself `faithful: false` when they do not, so a
card either shows a decomposition the verifier agrees with or says it cannot.

**What a card also shows.** For each of §10.4-R2's six registered defective
readings, the verdict that reading would record --- computed by
`microcase.defect_verdict`, the same function the microcase audit uses. An
item where every reading agrees is an item that cannot discriminate between a
correct verifier and a broken one, and it is not worth a person's attention.
Selection prefers the items that can.

**Standing.** This is a verifier audit and it is not §10.3. It shows the
verdict, so it measures nothing about human-verifier agreement and its output
must never be reported as an agreement rate. What it produces is a **defect
worklist**: places a person looked at the derivation and said it counted the
wrong thing. Acting on one is a change to the verifier, with everything §10.2
and `CHANGES_SCIENTIFIC.md` require of one.
"""
from __future__ import annotations

import random
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.target import s0_count

from dci1v4r3.protocol.seeds import gate1_sample_seed
from dci1v4r3.protocol.wordings import wordings
from dci1v4r3.stages.microcase import DEFECT_KINDS, defect_verdict
from dci1v4r3.verifiers.adversarial import PHENOMENA
from dci1v4r3.verifiers.compliance import (
    NON_VACUITY_MIN_WORDS, graded, non_vacuous, passes,
)
from dci1v4r3.verifiers.constraints import (
    FAMILIES, FORM_RATE, FORM_RATE_LOWER_BOUND, Constraint,
)
from dci1v4r3.verifiers.statistics import (
    STATISTICS, focal_statistic, word_count,
)
from dci1v4r3.verifiers.words import alpha_runs

__all__ = ["GRANULARITY", "VERDICTS", "VERDICT_OF_KEY", "RATE_FORMS",
           "decompose", "card", "discriminating", "tags", "select"]

#: How a numerator's count decomposes. `word` and `character` probe the
#: registered function unit by unit; `sentence` and `max` are not counts of
#: independent units and say so rather than pretending.
GRANULARITY = {
    "b_initial": "word", "ing_final": "word", "one_letter": "word",
    "doubled_letter": "word", "capital_word": "word", "letter_a": "word",
    "y_final": "word", "t_initial": "word", "s_final": "word",
    "vowel_initial": "word", "marker_thus": "word",
    "comma": "character", "semicolon": "character", "capital_char": "character",
    "sentence": "sentence",
    "s0": "word", "focal": "max",
}

RATE_FORMS = (FORM_RATE, FORM_RATE_LOWER_BOUND)

#: The auditor's vocabulary. The question is about the derivation, not the
#: response: "did this count the right things?"
VERDICTS = ("correct", "wrong", "unsure")
VERDICT_OF_KEY = {"y": "correct", "n": "wrong", "u": "unsure"}


def _statistic_id(kind: str) -> str:
    if kind == "A":
        return "s0"
    if kind == "B":
        return "focal"
    return FAMILIES[kind].statistic_id


def _count(statistic_id: str, text: str) -> int:
    if statistic_id == "s0":
        return s0_count(text)
    if statistic_id == "focal":
        return focal_statistic(text)
    return STATISTICS[statistic_id](text)


def _constraint(kind: str, severity: int) -> Constraint:
    return (Constraint(kind, severity) if kind == "A"
            else Constraint(kind, severity, extended=True, reserve=True))


def decompose(statistic_id: str, text: str) -> dict[str, Any]:
    """Which units the registered statistic counted, decided by itself.

    A unit is matched when the registered counting function, given that unit
    and nothing else, returns one. Nothing here re-implements a predicate, so
    the list cannot say the verifier counted something it did not --- and when
    the per-unit probes fail to sum to the whole-text count, the
    decomposition declares itself unfaithful rather than guessing.
    """
    if statistic_id not in GRANULARITY:
        raise ProtocolError(f"no registered decomposition for {statistic_id!r}")
    total = _count(statistic_id, text)
    grain = GRANULARITY[statistic_id]

    if grain == "max":
        runs = alpha_runs(text)
        longest = max(runs, key=len) if runs else None
        return {"granularity": grain, "units": len(runs), "count": total,
                "matched": [longest] if longest else [],
                "faithful": total == (len(longest) if longest else 0),
                "reads": "the longest word's letter count"}
    if grain == "sentence":
        return {"granularity": grain, "units": None, "count": total,
                "matched": [], "faithful": True,
                "reads": "maximal runs of . ! ? plus one for an unterminated "
                         "tail; not a count of independent units, so no "
                         "per-unit decomposition is shown"}

    units = alpha_runs(text) if grain == "word" else list(text)
    matched = [unit for unit in units if _count(statistic_id, unit) == 1]
    probed = sum(_count(statistic_id, unit) for unit in units)
    return {"granularity": grain, "units": len(units), "count": total,
            "matched": matched, "probed_total": probed,
            "faithful": probed == total,
            "reads": ("§7.3's word list, segmented then folded"
                      if grain == "word" else "raw characters of the answer")}


def card(kind: str, severity: int, text: str, *,
         wording_index: int = 0) -> dict[str, Any]:
    """§10.4-R's unit, for a person: the whole derivation, arithmetic shown."""
    constraint = _constraint(kind, severity)
    statistic_id = _statistic_id(kind)
    form = ("exact_count" if kind == "A" else
            "focal_budget" if kind == "B" else FAMILIES[kind].form)
    statistic = _count(statistic_id, text)
    words = word_count(text)
    is_rate = kind not in ("A", "B") and FAMILIES[kind].form in RATE_FORMS

    if is_rate:
        rate = 100.0 * statistic / words if words else None
        derived = {"quantity": "rate", "value": rate,
                   "arithmetic": (f"100 x {statistic} / {words} = "
                                  f"{rate:.4f}%" if words else
                                  "the answer has no words, so it has no "
                                  "rate and the predicate fails")}
    else:
        derived = {"quantity": "count", "value": statistic,
                   "arithmetic": f"{statistic}"}

    verdict = passes(constraint, statistic, text)
    readings = {defect: ("SATISFIES" if defect_verdict(constraint, text,
                                                       defect)
                         else "VIOLATES")
                for defect in DEFECT_KINDS} if kind not in ("A", "B") else {}
    return {
        "instrument": f"{kind}:{severity}",
        "instruction": wordings(kind, severity)[wording_index],
        "response": text,
        "segmentation": {
            "convention": "§7.3: segment into alphabetic runs, then fold each "
                          "word. A's own counter (§9.2) folds first and "
                          "segments after; the two differ on one character of "
                          "Unicode.",
            "words": words,
        },
        "numerator": {
            "statistic": statistic_id,
            "counts": _COUNTS[statistic_id],
            **decompose(statistic_id, text),
        },
        "denominator": ({"is": "the word count", "value": words}
                        if is_rate else
                        {"is": "none; this is a count predicate",
                         "value": None}),
        "derived": derived,
        "predicate": {
            "form": form,
            "direction": _DIRECTION[form],
            "threshold": severity,
            "statement": _STATEMENT[form].format(q=severity),
        },
        "verdict": "SATISFIES" if verdict else "VIOLATES",
        "graded": round(graded(constraint, statistic, text), 6),
        "non_vacuous": non_vacuous(constraint, text, truncated=False),
        "vacuity_rule": (f"a budget pass under {NON_VACUITY_MIN_WORDS} words "
                         f"is a vacuous pass (§9.3); lower bounds and exact "
                         f"counts carry no word-count clause"),
        "alternative_readings": readings,
        "discriminates": sorted(k for k, v in readings.items()
                                if (v == "SATISFIES") != verdict),
    }


#: What each numerator counts, in the words §7.3 uses. Displayed on the card
#: so the auditor is checking the program against the *rule*, not against
#: their own memory of what the identifier probably means.
_COUNTS = {
    "b_initial": "words beginning with b",
    "ing_final": "words ending with ing",
    "one_letter": "words of exactly one letter",
    "doubled_letter": "words containing a doubled letter",
    "comma": "comma characters in the raw answer",
    "capital_char": "upper-case characters A-Z in the raw answer",
    "capital_word": "words containing an upper-case character (new in v4r3, "
                    "no carry-over evidence)",
    "letter_a": "words containing the letter a",
    "y_final": "words ending with y",
    "t_initial": "words beginning with t",
    "s_final": "words ending with s",
    "vowel_initial": "words beginning with a, e, i, o or u (y is not a vowel "
                     "here, §7.3-R3)",
    "sentence": "sentence units: maximal runs of . ! ? plus one for an "
                "unterminated tail",
    "marker_thus": "occurrences of the word thus, segmented then folded",
    "semicolon": "semicolon characters in the raw answer",
    "s0": "occurrences of the target word however, folded then segmented",
    "focal": "the longest word's letter count",
}

_DIRECTION = {
    "count_budget": "at most", "rate_budget": "at most",
    "count_lower_bound": "at least", "rate_lower_bound": "at least",
    "exact_count": "exactly", "focal_budget": "at most",
}
_STATEMENT = {
    "count_budget": "passes when the count is <= {q}",
    "rate_budget": "passes when the rate is <= {q} percent, and a wordless "
                   "answer has no rate and fails",
    "count_lower_bound": "passes when the count is >= {q}",
    "rate_lower_bound": "passes when the rate is >= {q} percent, and a "
                        "wordless answer fails",
    "exact_count": "passes when the count is exactly {q}",
    "focal_budget": "passes when the longest word is <= {q} letters",
}


def discriminating(kind: str, severity: int, text: str) -> list[str]:
    """Which registered misreadings would record a different verdict here."""
    if kind in ("A", "B"):
        return []
    constraint = _constraint(kind, severity)
    here = passes(constraint, _count(_statistic_id(kind), text), text)
    return sorted(d for d in DEFECT_KINDS
                  if defect_verdict(constraint, text, d) != here)


def tags(item: Mapping[str, Any]) -> set[str]:
    """What an item exercises, for coverage-greedy selection."""
    text = item["response"]
    found = {f"phenomenon:{name}" for name, detector in PHENOMENA.items()
             if detector(text)}
    found.add(f"numerator:{item['statistic_id']}")
    found.add(f"form:{item['form']}")
    found.add(f"numerator-form:{item['statistic_id']}:{item['form']}")
    found.add("margin:one" if item.get("margin") == 1 else
              "margin:none" if item.get("margin") is None else "margin:larger")
    found.add(f"verdict:{item['verdict']}")
    for defect in discriminating(item["kind"], item["severity"], text):
        found.add(f"discriminates:{defect}")
    if not alpha_runs(text):
        found.add("wordless")
    return found


def select(pool: Sequence[Mapping[str, Any]], *, per_family: int = 4,
           candidates_per_family: int = 240,
           seed_label: str = "verifier-audit") -> list[dict[str, Any]]:
    """Coverage-greedy, per family, seeded.

    Within a family the next card is the one exercising most that no chosen
    card exercises yet --- a new phenomenon, a new misreading it would catch,
    a boundary margin. Ties break on the seeded order, so the choice is
    reproducible and is not a function of the verdict.

    The candidate list is capped first, under the same seed, because a family
    can carry a thousand responses and the greedy pass is quadratic in them.
    The cap is a cost bound and it is recorded; it is not a filter, because it
    is applied before any tag is looked at.
    """
    by_family: dict[str, list[Mapping[str, Any]]] = {}
    for item in pool:
        by_family.setdefault(item["kind"], []).append(item)

    chosen: list[dict[str, Any]] = []
    for kind in sorted(by_family):
        members = sorted(by_family[kind],
                         key=lambda i: (i["row_id"], i.get("position") or 0))
        random.Random(gate1_sample_seed(kind, seed_label)).shuffle(members)
        members = members[:candidates_per_family]
        tagged = [(item, tags(item)) for item in members]
        covered: set[str] = set()
        taken: list[int] = []
        while len(taken) < min(per_family, len(tagged)):
            best, best_gain = None, -1
            for index, (_, item_tags) in enumerate(tagged):
                if index in taken:
                    continue
                gain = len(item_tags - covered)
                if gain > best_gain:
                    best, best_gain = index, gain
            if best is None:
                break
            taken.append(best)
            covered |= tagged[best][1]
        for index in taken:
            item, item_tags = tagged[index]
            chosen.append({**item, "tags": sorted(item_tags)})
    return chosen
