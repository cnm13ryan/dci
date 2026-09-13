"""§10.4's unit of validation: how a written rule became a computed verdict.

**Why the original §10.4 could not run.** It handed the judge a rule and a
response and asked whether the response obeys the rule. For a count budget over
a hundred-word answer that is a long but finite job; for a *rate* it is an
enumeration --- every word classified, counted, divided --- and the judge spent
its whole 2,048-token cap doing it and never reached a verdict. Truncation on
v4r3's pool ran 23/72 and 40/72, and it rose monotonically with how much
counting the rule demanded: 0/12 on `A`, 12/12 on rate lower bounds. The
failure is not the judge's competence. It is that the task was arithmetic.

**What §10.4 is actually for.** §10.2 already establishes, deterministically
and at agreement 1.000, that two independent implementations compute the same
verdict. What agreement between two implementations cannot establish is that
either one implements *the construct the prose describes* --- both could share
a misreading. That gap is exactly what an external validator can close, and it
needs no arithmetic to close it.

So the validated object is not the verdict. It is the **operationalization
card**: the instruction as the model saw it, the response, the segmentation
convention, the numerator and what it counts, the denominator and what it
counts, the derived quantity with its arithmetic shown, the predicate form and
its threshold and direction, and the verdict that follows. The validator judges
whether that chain faithfully implements the written instruction. The
arithmetic is *shown*, not requested.

**Why the card alone would be tautological, and what stops it.** Handing a
validator a correct derivation and asking "is this right?" measures agreeableness.
The procedure is only informative if it also fails when it should, so half the
items carry a planted defect of a registered kind --- a swapped denominator, a
flipped inequality, an off-by-one threshold, a drifted segmentation convention,
a substituted numerator, an ignored vacuity rule. Specificity on faithful cards
and sensitivity on mutated ones are both measured, and both have prospectively
registered floors. A validator that says FAITHFUL to everything fails §10.4
here, where under the old design it would have passed criterion 4 by agreeing
with a verifier that was never really tested.

The deterministic verifier remains the study's scorer throughout. Nothing in
this module scores a generation, and nothing it returns enters a compliance
rate.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol.wordings import wordings
from dci1v4r3.verifiers.compliance import passes
from dci1v4r3.verifiers.constraints import (
    FAMILIES, FORM_COUNT, FORM_LOWER_BOUND, FORM_RATE, FORM_RATE_LOWER_BOUND,
    Constraint,
)
from dci1v4r3.verifiers.statistics import family_statistic, word_count
from dci1v4r3.verifiers.words import words_lower

__all__ = ["SEGMENTATION_PROSE", "NUMERATOR_PROSE", "MUTATIONS", "Card",
           "build_card", "mutate", "card_text", "mutation_kinds"]

#: §7.2/§7.3's segmentation convention, transcribed for the card. This is the
#: sentence the validator is asked to check the counting against.
SEGMENTATION_PROSE = (
    "A word is a maximal run of alphabetic characters. Punctuation, digits "
    "and whitespace separate words and are never part of one. The answer is "
    "segmented first; each word is then lower-cased for the suffix and letter "
    "tests. Comma and upper-case counts read the raw characters of the "
    "answer, not the segmented words.")

#: What each registered numerator counts, in the prose the card shows.
NUMERATOR_PROSE = {
    "b_initial": "words whose first letter is b",
    "ing_final": "words ending in the letters ing",
    "one_letter": "words exactly one letter long",
    "doubled_letter": "words containing the same letter twice in a row",
    "comma": "comma characters in the answer",
    "capital_char": "upper-case characters in the answer",
    "capital_word": "words containing at least one upper-case letter",
    "letter_a": "words containing the letter a",
    "y_final": "words ending in the letter y",
    "however": "occurrences of the word however",
    "longest_word": "words longer than the permitted length",
}

_DIRECTION = {FORM_COUNT: "<=", FORM_LOWER_BOUND: ">=",
              FORM_RATE: "<=", FORM_RATE_LOWER_BOUND: ">="}
_IS_RATE = (FORM_RATE, FORM_RATE_LOWER_BOUND)


@dataclass(frozen=True)
class Card:
    """One operationalization, faithful or mutated.

    ``defect`` is ``None`` for a faithful card and the mutation key otherwise.
    It is never rendered into the text the validator reads.
    """

    item_id: str
    kind: str
    severity: int
    instruction: str
    rule_prose: str
    response: str
    segmentation: str
    numerator_name: str
    numerator: int
    denominator_name: str | None
    denominator: int | None
    derived_name: str
    derived_expression: str
    derived_value: float
    form: str
    direction: str
    threshold: float
    verdict: str
    defect: str | None = None

    @property
    def is_faithful(self) -> bool:
        return self.defect is None


def _numerator_name(kind: str) -> str:
    if kind == "A":
        return NUMERATOR_PROSE["however"]
    if kind == "B":
        return NUMERATOR_PROSE["longest_word"]
    return NUMERATOR_PROSE[FAMILIES[kind].statistic_id]


def _statistic(kind: str, severity: int, text: str) -> int:
    if kind == "A":
        from dci1v4r3.verifiers.statistics import focal_statistic
        return focal_statistic(text)
    if kind == "B":
        return sum(1 for w in words_lower(text) if len(w) > severity)
    return family_statistic(kind, text)


def build_card(constraint: Constraint, text: str, *, item_id: str,
               wording_index: int = 0) -> Card:
    """The faithful card: what the verifier did, laid out for inspection."""
    kind, q = constraint.kind, constraint.severity
    statistic = _statistic(kind, q, text)
    words = word_count(text)

    if kind == "A":
        form, direction = "exact_count", "=="
        derived_name, expression = "count", str(statistic)
        value: float = float(statistic)
        denominator_name, denominator = None, None
    elif kind == "B":
        form, direction = "count_budget", "<="
        derived_name = "count of words over the permitted length"
        expression, value = str(statistic), float(statistic)
        denominator_name, denominator = None, None
    else:
        form = FAMILIES[kind].form
        direction = _DIRECTION[form]
        if form in _IS_RATE:
            denominator_name, denominator = "words in the answer", words
            if words == 0:
                derived_name = "rate per hundred words"
                expression = "undefined: the answer has no words"
                value = float("nan")
            else:
                derived_name = "rate per hundred words"
                expression = f"100 x {statistic} / {words}"
                value = 100.0 * statistic / words
        else:
            denominator_name, denominator = None, None
            derived_name, expression = "count", str(statistic)
            value = float(statistic)

    verdict = "pass" if passes(constraint, statistic, text) else "fail"
    if kind == "B":
        # B's own predicate is over the longest word; the card states the
        # equivalent count form so that the shown arithmetic matches it.
        verdict = "pass" if statistic == 0 else "fail"
        threshold: float = 0.0
    else:
        threshold = float(q)

    return Card(
        item_id=item_id, kind=kind, severity=q,
        instruction=wordings(kind, q)[wording_index],
        rule_prose=(FAMILIES[kind].rule if kind in FAMILIES else
                    ("Use the word however exactly q times." if kind == "A"
                     else "Every word in the answer must have at most q "
                          "letters.")),
        response=text, segmentation=SEGMENTATION_PROSE,
        numerator_name=_numerator_name(kind), numerator=statistic,
        denominator_name=denominator_name, denominator=denominator,
        derived_name=derived_name, derived_expression=expression,
        derived_value=value, form=form, direction=direction,
        threshold=threshold, verdict=verdict)


# --------------------------------------------------------------- mutations

def _m_denominator_swap(card: Card) -> Card | None:
    """Count characters where the rule counts words. A wrong denominator."""
    if card.denominator is None:
        return None
    chars = len(card.response)
    if chars == 0:
        return None
    value = 100.0 * card.numerator / chars
    return replace(
        card, denominator_name="characters in the answer", denominator=chars,
        derived_expression=f"100 x {card.numerator} / {chars}",
        derived_value=value,
        verdict=_apply(card.direction, value, card.threshold),
        defect="denominator_swap")


def _m_inequality_flip(card: Card) -> Card | None:
    """State the opposite inequality from the one the instruction sets."""
    if card.direction not in ("<=", ">="):
        return None
    flipped = ">=" if card.direction == "<=" else "<="
    return replace(card, direction=flipped,
                   verdict=_apply(flipped, card.derived_value, card.threshold),
                   defect="inequality_flip")


def _m_off_by_one(card: Card) -> Card | None:
    """Move the threshold by one, keeping everything else right."""
    if card.kind == "B":
        return None
    moved = card.threshold + 1.0
    return replace(card, threshold=moved,
                   verdict=_apply(card.direction, card.derived_value, moved),
                   defect="off_by_one")


def _m_segmentation_drift(card: Card) -> Card | None:
    """Segment on whitespace, so punctuation joins the word it touches.

    This is the defect the v4r2 independent reimplementation actually had, in
    a different form: a segmentation convention that is not the registered
    one, producing a different numerator on the same text.
    """
    if card.kind in ("A",) or card.denominator is None:
        return None
    tokens = card.response.split()
    if not tokens:
        return None
    return replace(
        card, segmentation=(
            "A word is a maximal run of non-whitespace characters. "
            "Punctuation attached to a word is part of that word."),
        denominator=len(tokens),
        derived_expression=f"100 x {card.numerator} / {len(tokens)}",
        derived_value=100.0 * card.numerator / len(tokens),
        verdict=_apply(card.direction,
                       100.0 * card.numerator / len(tokens), card.threshold),
        defect="segmentation_drift")


def _m_numerator_swap(card: Card) -> Card | None:
    """Keep the instruction, count something else."""
    if card.kind in ("A", "B"):
        return None
    other = {"b_initial": "y_final", "y_final": "b_initial",
             "ing_final": "one_letter", "one_letter": "ing_final",
             "doubled_letter": "letter_a", "letter_a": "doubled_letter",
             "comma": "capital_char", "capital_char": "comma",
             "capital_word": "letter_a"}[FAMILIES[card.kind].statistic_id]
    from dci1v4r3.verifiers.statistics import statistic_of
    value_n = statistic_of(other, card.response)
    if card.denominator:
        value = 100.0 * value_n / card.denominator
        expression = f"100 x {value_n} / {card.denominator}"
    else:
        value, expression = float(value_n), str(value_n)
    return replace(card, numerator_name=NUMERATOR_PROSE[other],
                   numerator=value_n, derived_expression=expression,
                   derived_value=value,
                   verdict=_apply(card.direction, value, card.threshold),
                   defect="numerator_swap")


def _m_vacuity_ignored(card: Card) -> Card | None:
    """Report a rate on a wordless answer as satisfied.

    §7.3: a wordless answer has no rate and fails both rate forms. The empty
    string passes 94 of 94 count severities and none of the rate ones, and
    that asymmetry is the whole reason the rate forms are registered.
    """
    if card.denominator is None:
        return None
    return replace(card, response="", denominator=0, numerator=0,
                   derived_expression="100 x 0 / 0, treated as 0",
                   derived_value=0.0,
                   verdict=_apply(card.direction, 0.0, card.threshold),
                   defect="vacuity_ignored")


def _apply(direction: str, value: float, threshold: float) -> str:
    if value != value:                       # NaN
        return "fail"
    if direction == "<=":
        return "pass" if value <= threshold else "fail"
    if direction == ">=":
        return "pass" if value >= threshold else "fail"
    return "pass" if value == threshold else "fail"


#: The registered defect kinds. Each is one thing the validator must be able
#: to see; §10.4's sensitivity floor applies per kind as well as overall, so a
#: validator blind to one whole class cannot pass by catching the others.
MUTATIONS: Mapping[str, Callable[[Card], "Card | None"]] = {
    "denominator_swap": _m_denominator_swap,
    "inequality_flip": _m_inequality_flip,
    "off_by_one": _m_off_by_one,
    "segmentation_drift": _m_segmentation_drift,
    "numerator_swap": _m_numerator_swap,
    "vacuity_ignored": _m_vacuity_ignored,
}


def mutation_kinds() -> tuple[str, ...]:
    return tuple(MUTATIONS)


def mutate(card: Card, kind: str) -> Card | None:
    """Apply one registered defect, or None when it does not apply here."""
    if kind not in MUTATIONS:
        raise ProtocolError(
            f"{kind!r} is not a registered §10.4 defect kind; "
            f"registered: {tuple(MUTATIONS)}")
    if not card.is_faithful:
        raise ProtocolError("a mutated card cannot be mutated again")
    out = MUTATIONS[kind](card)
    if out is not None and out.defect != kind:
        raise ProtocolError("a mutation must record its own kind")
    return out


def card_text(card: Card) -> str:
    """The card as the validator reads it.

    The defect kind is never rendered, and neither is the word 'faithful'.
    Nothing here tells the validator what answer is wanted.
    """
    lines = [
        "INSTRUCTION GIVEN TO THE SYSTEM:",
        f"  {card.instruction}",
        "",
        "THE SYSTEM'S ANSWER:",
        "<<<", card.response, ">>>",
        "",
        "HOW THE CHECKER SCORED IT:",
        f"  Word convention: {card.segmentation}",
        f"  Counted ({card.numerator_name}): {card.numerator}",
    ]
    if card.denominator_name is not None:
        lines.append(
            f"  Out of ({card.denominator_name}): {card.denominator}")
    lines += [
        f"  {card.derived_name.capitalize()}: "
        f"{card.derived_expression} = {card.derived_value:.4g}",
        f"  Required: {card.derived_name} {card.direction} "
        f"{card.threshold:g}",
        f"  Verdict recorded: {card.verdict.upper()}",
    ]
    return "\n".join(lines)


def card_record(card: Card) -> dict[str, Any]:
    """The card as evidence, defect included. Never shown to the validator."""
    return {
        "item_id": card.item_id, "kind": card.kind, "severity": card.severity,
        "form": card.form, "direction": card.direction,
        "threshold": card.threshold, "numerator": card.numerator,
        "denominator": card.denominator, "derived": card.derived_value,
        "verdict": card.verdict, "defect": card.defect,
        "faithful": card.is_faithful,
    }
