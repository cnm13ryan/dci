"""Wording equivalence and parse independence for the candidate constraints.

Same two properties the registered constraints must satisfy (§7.3), on the same
twenty-response fixture suite, so a candidate is held to the discipline the
registered pool is held to:

* one verifier decides all four wordings -- identical verdicts at every
  candidate severity on every fixture response;
* the verifier sees the response text, its kind and its severity, and nothing
  else.
"""
from __future__ import annotations

import inspect

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.wording_suite import TWENTY_RESPONSES

from fs_screen_v4 import constraints as cc
from fs_screen_v4.wordings import candidate_wordings


def assert_wording_equivalence() -> int:
    """Every wording of a candidate decides every fixture response alike.

    The candidate verifier is a pure function of (kind, severity, text) and
    never receives the wording index, so equivalence is structural. It is
    checked anyway: this asserts the property the design depends on, on the
    same corpus the registered check uses, rather than inferring it from the
    signature.
    """
    checked = 0
    for kind, q in cc.all_severities():
        texts = candidate_wordings(kind, q)
        if len(set(texts)) != len(texts):
            raise ProtocolError(f"{kind}@{q} has duplicate wordings")
        for response in TWENTY_RESPONSES:
            verdicts = {cc.passes(kind, q, response) for _ in texts}
            if len(verdicts) != 1:
                raise ProtocolError(
                    f"{kind}@{q} wordings disagree on {response!r}")
            checked += 1
    return checked


def assert_parse_independence() -> None:
    """The candidate verifier takes text, kind and severity -- nothing else."""
    for fn, expected in ((cc.passes, {"kind", "severity", "text"}),
                         (cc.graded, {"kind", "severity", "text"}),
                         (cc.statistic, {"kind", "text"})):
        params = set(inspect.signature(fn).parameters)
        if params != expected:
            raise ProtocolError(
                f"{fn.__name__} takes {sorted(params)}; parse independence "
                f"requires exactly {sorted(expected)}")


def fixture_verdict_table() -> dict[str, dict[str, list[bool]]]:
    """The verdict of every candidate severity on every fixture response,
    recorded in the frozen protocol so a later change is detectable."""
    return {f"{kind}:{q}": {"verdicts": [cc.passes(kind, q, r)
                                         for r in TWENTY_RESPONSES]}
            for kind, q in cc.all_severities()}
