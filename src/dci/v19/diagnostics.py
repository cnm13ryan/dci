"""Parse-form and UNPARSEABLE reporting by arm, as diagnostics and nothing more.

Section 4.2's coupling risk is that "a malformed list could change both verdicts
through shared parsing rather than through genuine interference". Amendment A1 makes
the parser arm-blind, which removes the mechanism by construction; this module
supplies the evidence that it stayed removed, by reporting how answers were READ,
separately per arm.

WHY THIS IS NOT AN OUTCOME
--------------------------
Section 10.1 keeps the primary outcome and the generation state orthogonal. `Verdict`
has exactly two members; UNPARSEABLE is a `GenerationState`, and A1 keeps it there.
An UNPARSEABLE answer therefore contributes no PASS and no FAIL - it is not a third
value of the primary outcome, and `assert_outcome_space_is_binary` refuses the change
that would make it one.

What a difference in these rates means is a question for the investigator, not for
this module. A raised UNPARSEABLE rate in one arm is evidence that arm's answers were
harder to read; whether that is genuine interference, a parser artefact, or a
background occupant's formatting influence is a scientific reading. So the report
carries counts and rates and states no interpretation.

WHAT A "PARSE FORM" IS
----------------------
The structural shape the grammar found, independent of the content: which marker
kinds opened items, whether markers were mixed, whether items nested, whether any
item wrapped across lines, and whether prose surrounded the list. Two answers with
the same parse form were read the same way. `dci.v19.parsing.EQUIVALENT_SURFACE_FORMS`
is the complementary fact: distinct surface forms that must parse to the SAME items.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from dci.v19.parsing import ParsedList
from dci.v19.verifiers import GenerationState, Verdict, VerifierOutcome


class DiagnosticError(ValueError):
    """A diagnostic that could not be computed from what was recorded."""


def assert_outcome_space_is_binary() -> None:
    """UNPARSEABLE must remain a generation state, never a primary outcome.

    A1 keeps the existing orthogonal state and creates no third primary outcome.
    Adding one would silently change F_A's definition - the primary outcome is a
    proportion of PASS over scored answers - so the constraint is asserted here and
    tested, rather than left as an intention in a document.
    """
    members = tuple(v.value for v in Verdict)
    if members != ("PASS", "FAIL"):
        raise DiagnosticError(
            f"the primary outcome space is {members}; section 10.1 admits exactly "
            "PASS and FAIL, and amendment A1 creates no third primary outcome. "
            "UNPARSEABLE belongs to GenerationState")
    if "UNPARSEABLE" not in {s.value for s in GenerationState}:
        raise DiagnosticError(
            "UNPARSEABLE is not a GenerationState, so the orthogonal state A1 "
            "preserves no longer exists")


def parse_form(parsed: ParsedList | Mapping[str, Any]) -> str:
    """A short canonical label for how the grammar read one answer.

    Accepts a `ParsedList` or the `describe()` mapping a verifier records in its
    evidence, because the report is normally built from archived outcomes rather than
    from a live parse.
    """
    detail = parse_form_detail(parsed)
    if detail["observed_count"] == 0:
        return "no_items"
    parts = ["+".join(detail["marker_kinds"]) or "none"]
    if detail["mixed_markers"]:
        parts.append("mixed")
    if detail["nested"]:
        parts.append("nested")
    if detail["wrapped"]:
        parts.append("wrapped")
    if detail["excluded_reasons"]:
        parts.append("excl:" + "+".join(detail["excluded_reasons"]))
    if detail["leading_prose"] or detail["trailing_prose"]:
        parts.append("prose")
    return "/".join(parts)


def marker_shape(marker: str, marker_kind: str) -> str:
    """The marker with its ordinal erased, so "1." and "2." are the same marker.

    Without this a correctly enumerated list reads as "mixed markers", because
    every item's marker string differs. Mixed means the answer varied its marker
    STYLE - a hyphen then an asterisk, or a bullet then an enumeration - which is a
    fact about how the answer was written; incrementing a counter is not.
    """
    if marker_kind == "numbered":
        return re.sub(r"\d+", "N", marker)
    return marker


def parse_form_detail(parsed: ParsedList | Mapping[str, Any]) -> dict[str, Any]:
    """The structural facts `parse_form` compresses, kept separate for audit."""
    described = parsed.describe() if isinstance(parsed, ParsedList) else parsed
    if not isinstance(described, Mapping) or "items" not in described:
        raise DiagnosticError(
            f"expected a ParsedList or its describe() mapping, got "
            f"{type(parsed).__name__}")
    items = list(described.get("items", ()))
    excluded = list(described.get("excluded", ()))
    indents = [int(i.get("indent", 0)) for i in items]
    shapes = {marker_shape(str(i.get("marker", "")), str(i.get("marker_kind", "")))
              for i in items}
    return {
        "observed_count": len(items),
        "marker_kinds": sorted({str(i.get("marker_kind", "")) for i in items}),
        "markers": sorted(shapes),
        "mixed_markers": len(shapes) > 1,
        "nested": bool(indents) and max(indents) > min(indents),
        "wrapped": any(int(i.get("continuation_lines", 0)) > 0 for i in items),
        "excluded_reasons": sorted({str(i.get("excluded_because", ""))
                                    for i in excluded if i.get("excluded_because")}),
        "n_excluded": len(excluded),
        "leading_prose": bool(described.get("leading_prose")),
        "trailing_prose": bool(described.get("trailing_prose")),
        "policy_hash": described.get("policy_hash", ""),
    }


def _observation(entry: Any) -> tuple[str, VerifierOutcome]:
    if isinstance(entry, Mapping):
        arm, outcome = entry.get("arm"), entry.get("outcome")
    elif isinstance(entry, Sequence) and not isinstance(entry, str) \
            and len(entry) == 2:
        arm, outcome = entry
    else:
        raise DiagnosticError(
            f"expected (arm, VerifierOutcome) or a mapping with those keys, got "
            f"{type(entry).__name__}")
    if not isinstance(arm, str) or not arm:
        raise DiagnosticError(f"{arm!r} is not an arm label")
    if not isinstance(outcome, VerifierOutcome):
        raise DiagnosticError(
            f"{arm}: expected a VerifierOutcome, got {type(outcome).__name__}. The "
            "rates are computed from what the verifier actually recorded, so they "
            "cannot drift from the measurement they describe")
    return arm, outcome


def rates_by_arm(observations: Sequence[Any]) -> dict[str, Any]:
    """Parse-form and generation-state rates, per arm.

    One row per arm, each carrying the denominator it was computed over: a rate with
    no denominator cannot be compared across arms of different sizes, and the arms
    are not guaranteed equal here because a proposal can be rejected in one arm.
    """
    assert_outcome_space_is_binary()
    per_arm: dict[str, dict[str, Any]] = {}
    for entry in observations:
        arm, outcome = _observation(entry)
        row = per_arm.setdefault(arm, {"arm": arm, "n": 0, "by_generation_state": {},
                                       "by_parse_form": {},
                                       "by_exclusion_reason": {},
                                       "n_with_parse_evidence": 0})
        row["n"] += 1
        state = outcome.generation_state.value
        row["by_generation_state"][state] = row["by_generation_state"].get(state, 0) + 1
        described = outcome.evidence.get("parse")
        if described is None:
            continue
        row["n_with_parse_evidence"] += 1
        form = parse_form(described)
        row["by_parse_form"][form] = row["by_parse_form"].get(form, 0) + 1
        for reason in parse_form_detail(described)["excluded_reasons"]:
            row["by_exclusion_reason"][reason] = \
                row["by_exclusion_reason"].get(reason, 0) + 1

    for row in per_arm.values():
        n = row["n"]
        unparseable = row["by_generation_state"].get(
            GenerationState.UNPARSEABLE.value, 0)
        row["n_unparseable"] = unparseable
        row["unparseable_rate"] = unparseable / n if n else None
        row["generation_state_rates"] = {
            state: count / n for state, count in
            sorted(row["by_generation_state"].items())}
        parsed_n = row["n_with_parse_evidence"]
        row["parse_form_rates"] = {
            form: count / parsed_n for form, count in
            sorted(row["by_parse_form"].items())} if parsed_n else {}
        row["by_generation_state"] = dict(sorted(row["by_generation_state"].items()))
        row["by_parse_form"] = dict(sorted(row["by_parse_form"].items()))
        row["by_exclusion_reason"] = dict(sorted(row["by_exclusion_reason"].items()))

    return {
        "protocol": "v19",
        "citation": "sections 4.2, 10.1, 11.8 + Stage 2 amendment A1",
        "kind": "diagnostic",
        "note": ("Rates describe how answers were READ, not what they were about. "
                 "UNPARSEABLE is the orthogonal generation state of section 10.1 and "
                 "is not a third primary outcome; an UNPARSEABLE answer contributes "
                 "no PASS and no FAIL. Whether a between-arm difference is genuine "
                 "interference, a parser artefact, or a formatting influence of the "
                 "added-slot occupant is a scientific reading, and none is offered "
                 "here"),
        "n_observations": sum(row["n"] for row in per_arm.values()),
        "arms": [per_arm[arm] for arm in sorted(per_arm)],
    }


def parse_form_disagreement(report: Mapping[str, Any]) -> dict[str, Any]:
    """Where the arms were read differently, as a difference table.

    Reports the spread of each rate across arms without testing it. A spread is a
    quantity the investigator interprets; computing a p-value here would create an
    unpreregistered inferential procedure over diagnostic material.
    """
    arms = list(report.get("arms", ()))
    if not arms:
        return {"arms": [], "unparseable_rate_spread": None, "parse_forms": {}}
    rates = [row["unparseable_rate"] for row in arms
             if row["unparseable_rate"] is not None]
    forms = sorted({form for row in arms for form in row["parse_form_rates"]})
    return {
        "arms": [row["arm"] for row in arms],
        "unparseable_rate_by_arm": {row["arm"]: row["unparseable_rate"]
                                    for row in arms},
        "unparseable_rate_spread": (max(rates) - min(rates)) if rates else None,
        "parse_forms": {
            form: {row["arm"]: row["parse_form_rates"].get(form, 0.0)
                   for row in arms}
            for form in forms},
        "forms_seen_in_some_arms_only": [
            form for form in forms
            if any(form not in row["parse_form_rates"] for row in arms)],
        "note": ("A spread is not a test. No inferential procedure over diagnostic "
                 "material is preregistered, so none is applied"),
    }
