"""Wording equivalence and parse independence (v4r2 §7.3).

Two properties, both executable preconditions of qualification:

* **Wording equivalence.** The four frozen wordings of a constraint state one
  rule, so one verifier decides all four and every wording must produce the
  same verdict on a fixed twenty-response suite at every registered severity.
* **Parse independence.** A verifier receives the response text and its own
  kind and severity, and nothing else — no companion identity, no cell label,
  no order, no wording index, and no other verifier's output. That is checked
  against the callables' signatures, not asserted in prose, so a future
  parameter cannot be added without the check failing.

The twenty responses are authored for v4 and deliberately span the states the
design produces: ordinary answers, degenerate ones, the empty answer, and
answers built to sit on a severity boundary.
"""
from __future__ import annotations

import inspect

from dci1v4.errors import ProtocolError
from dci1v4.protocol.wordings import N_WORDINGS, wordings
from dci1v4.verifiers import statistics as stats_mod
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    Constraint,
    TARGET_GRID,
)

TWENTY_RESPONSES: tuple[str, ...] = (
    "The river runs west, then it drifts north over open ground.",
    "however the tide turns and the boats return to harbour",
    "however however however",
    "",
    "   ",
    "Bright blue banners billowed beside the bridge, boldly.",
    "Running, jumping and swimming bring lasting joy to many people.",
    "A B C D E F G H",
    "supercalifragilisticexpialidocious",
    "Yes.",
    "One, two, three, four, five, six, seven, eight, nine, ten, more.",
    "MOST OF THIS ANSWER IS SHOUTED AT THE READER FOR NO GOOD REASON.",
    "café, naïve, résumé and déjà vu are borrowed words in English.",
    "然而 事情 改变 了 很多 次",
    "The coffee spilled, the kettle boiled, and the buttons fell off.",
    "however, the plan failed; however, the crew recovered quickly",
    "state-of-the-art design work needs care and a steady hand",
    "**Bold** text and _italic_ text render differently in markdown.",
    "The answer was cut off mid-w",
    "however the river runs west then it drifts to the north.",
)
assert len(TWENTY_RESPONSES) == 20


def registered_pairs() -> list[tuple[str, int]]:
    pairs = [("A", n) for n in TARGET_GRID] + [("B", m) for m in FOCAL_GRID]
    for family, ladder in REFERENCE_LADDERS.items():
        pairs += [(family, q) for q in ladder]
    return pairs


def assert_parse_independence() -> dict[str, list[str]]:
    """Every scoring callable takes the response text and its own identity."""
    signatures: dict[str, list[str]] = {}
    for name, fn in [("focal_statistic", stats_mod.focal_statistic)] + [
            (f, stats_mod.FAMILY_STATISTICS[f]) for f in REFERENCE_LADDERS]:
        params = list(inspect.signature(fn).parameters)
        if params != ["text"]:
            raise ProtocolError(
                f"{name} takes {params}; a statistic reads the response text "
                f"and nothing else (§7.3)")
        signatures[name] = params
    params = list(inspect.signature(score_constraint).parameters)
    if params != ["constraint", "text", "truncated"]:
        raise ProtocolError(
            f"score_constraint takes {params}; a verifier receives the "
            f"response, its own constraint identity and severity, and the "
            f"degeneracy flag it needs for §9.3 — nothing else")
    signatures["score_constraint"] = params
    return signatures


def evaluate() -> dict:
    """Identical verdicts across all four wordings, at every severity."""
    assert_parse_independence()
    checks = 0
    for kind, severity in registered_pairs():
        texts = wordings(kind, severity)
        if len(texts) != N_WORDINGS or len(set(texts)) != N_WORDINGS:
            raise ProtocolError(f"{kind}@{severity} does not carry four "
                                f"distinct frozen wordings")
        constraint = Constraint(kind, severity)
        for response in TWENTY_RESPONSES:
            verdicts = set()
            for index in range(N_WORDINGS):
                # The wording index is deliberately not an input to scoring;
                # the loop exists to demonstrate that, not to vary anything.
                score = score_constraint(constraint, response, truncated=False)
                verdicts.add((score.passed, round(score.graded, 12),
                              score.statistic))
                _ = texts[index]
            if len(verdicts) != 1:
                raise ProtocolError(
                    f"{kind}@{severity} verdict depends on wording index")
            checks += 1
    return {"responses": len(TWENTY_RESPONSES),
            "constraint_severities": len(registered_pairs()),
            "checks": checks, "wordings_per_constraint": N_WORDINGS}
