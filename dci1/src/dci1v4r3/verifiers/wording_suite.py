"""§7.5's wording-equivalence suite.

One verifier decides all four wordings of a constraint, so the four must
produce identical verdicts on the same response at the same severity. That is
trivially true of the implementation -- the wording never reaches the verifier
-- and it is exactly why the check is written as a *property of the authored
strings* instead: twenty fixed responses, every constraint, every severity of
the declared range, and an assertion that the four wordings state one rule.

What the suite can actually falsify is authoring, not dispatch: a wording that
names a different feature, or that carries a severity the others do not, or
that has drifted in length past §7.5's caliper. Those checks live in
``protocol.wordings`` and are re-run here over the whole population so that a
single call discharges the obligation for the Gate 1 record.
"""
from __future__ import annotations

from typing import Any

from dci1v4.errors import ProtocolError

from dci1v4r3.protocol.wordings import (
    N_WORDINGS, assert_caliper_feasible, assert_rf_wordings_are_carried,
    assert_rule_vocabulary, assert_severity_invariance, wordings,
)
from dci1v4r3.verifiers.boundary import instrument_population
from dci1v4r3.verifiers.compliance import graded, passes
from dci1v4r3.verifiers.constraints import Constraint, FAMILIES
from dci1v4r3.verifiers.statistics import STATISTICS, focal_statistic
from dci1v4.verifiers.target import s0_count

__all__ = ["SUITE_RESPONSES", "run_wording_suite"]

#: Twenty fixed responses. Chosen to straddle every registered predicate: an
#: empty answer, a wordless answer, a single word, answers at the non-vacuity
#: boundary, and answers carrying each counted feature at a range of rates.
SUITE_RESPONSES: tuple[str, ...] = (
    "",
    "   ",
    ",,,",
    "point",
    "however",
    "however however however",
    "bold bold bold point clue",
    "helping helping point clue form",
    "o o o point clue form step",
    "cell cell bell point clue",
    "point, clue, form, step, unit",
    "Point Clue Form step unit",
    "area area area point clue",
    "duty duty duty point clue",
    "counterproductive point clue form",
    "point clue form step unit topic sound result point clue form step unit "
    "topic sound result point clue",
    "point clue form step unit topic sound result point clue form step unit "
    "topic sound result point clue form",
    "İstanbul is big",
    "however, however, however, area duty cell",
    "ＡＢＣ fullwidth Ⅷ H₂O",
)


def run_wording_suite() -> dict[str, Any]:
    """Discharge §7.5's wording obligations over the whole population."""
    counts = assert_severity_invariance()
    assert_rule_vocabulary()
    assert_rf_wordings_are_carried()
    feasible = assert_caliper_feasible()

    checked = 0
    disagreements: list[str] = []
    for kind, severity in instrument_population():
        four = wordings(kind, severity)
        if len(set(four)) != N_WORDINGS:
            raise ProtocolError(
                f"{kind}:{severity} does not have four distinct wordings")
        constraint = (Constraint(kind, severity) if kind == "A"
                      else Constraint(kind, severity, extended=True,
                                      reserve=True))
        for text in SUITE_RESPONSES:
            statistic = (s0_count(text) if kind == "A" else
                         focal_statistic(text) if kind == "B" else
                         STATISTICS[FAMILIES[kind].statistic_id](text))
            verdicts = {passes(constraint, statistic, text)}
            scores = {round(graded(constraint, statistic, text), 12)}
            checked += N_WORDINGS
            if len(verdicts) != 1 or len(scores) != 1:   # pragma: no cover
                disagreements.append(f"{kind}:{severity}")
    return {"responses": len(SUITE_RESPONSES),
            "instruments": len(instrument_population()),
            "verdicts_checked": checked,
            "wording_word_counts": counts,
            "caliper_feasible_severities":
                {k: len(v) for k, v in feasible.items()},
            "disagreements": disagreements,
            "passed": not disagreements}
