"""§7.7's realistic joint-satisfiability obligation, new in v5.

v4r4's obligation was **formal**: for every realisable pair at every severity
of the declared range, a machine-verified witness satisfies both at once. A
formal witness certifies only that a pair is not contradictory --- not that it
is satisfiable by a response of the length the task asks for.

v5 adds: for every pair the design can realise **with B at every admissible
severity**, the witness must additionally lie inside §8.5's stem band of 60 to
120 words. `CL7`'s frozen reserve runs to 140, and *at least 130 words must
contain the letter a* cannot be met by any answer of at most 120 words, so
`CL7:130` and `CL7:140` are formally satisfiable and unreachable inside the
response genre this study registers. A family with no realistic witness at a
severity is not admissible to any slot **at that severity**, and the failure
is reported by family and severity rather than waived.

**This check is cheap and narrow, and it is not the main defence.** It catches
a severity whose arithmetic exceeds the stem band. It does **not** catch a
constraint that is reachable in principle and that B pushes into a degenerate
region: `CL7:80` *is* reachable and was reached at 0.609 and 0.662 under
composition on `gemma-3n-e4b-it`. §13.6's interaction gate, and not this one,
is what measures that class of risk --- and an earlier draft of the
preregistration justified this rule with `CL7:80` on an assertion the signed
v4r4 records contradict. The correction is recorded rather than quietly
removed.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.verifiers.compliance import passes
from dci1v6.verifiers.constraints import (
    Constraint, FAMILIES, declared_range, focal_severities,
)
from dci1v6.verifiers.statistics import alpha_runs
from dci1v6.verifiers.witnesses import joint_witness

__all__ = ["STEM_BAND", "witness_word_count", "pad_to_band", "fit_to_band",
           "realistic_witness_verdict", "run_realistic_suite",
           "unreachable_severities"]

#: §8.5's band, used here as a **design constant** and not as a reading of its
#: realised rate. §29 records the consequence: a change to the stem would
#: change which candidates are admissible, so the stem is frozen at the same
#: level as a verifier.
STEM_BAND = C.STEM_BAND


def witness_word_count(text: str) -> int:
    return len(alpha_runs(text))


def _trailing_punctuation(text: str) -> tuple[str, str]:
    """Split a witness into its body and any trailing punctuation run."""
    body = text.rstrip()
    tail = ""
    while body and not body[-1].isalnum():
        tail = body[-1] + tail
        body = body[:-1]
    return body, tail


def fit_to_band(text: str, *, target: int) -> str:
    """Make a witness exactly ``target`` words long, structure preserved.

    Padding **inserts feature-free filler before any trailing punctuation**
    rather than appending after it. Appending after a full stop would add an
    unterminated tail, which §9.2's sentence rule counts as one more sentence
    --- so a witness for *exactly q sentences* padded naively becomes a
    witness for q + 1, and the check would report a construction defect as a
    scientific finding.

    Trimming drops whole words from the end of the body for the same reason.

    The filler is feature-free for every registered numerator and every filler
    word is at most five letters, so neither operation can break B at any
    admissible severity. What either *can* break is the constraint itself, and
    ``realistic_witness_verdict`` re-checks rather than assuming.
    """
    body, tail = _trailing_punctuation(text)
    words = witness_word_count(text)
    if words == target:
        return text
    if words < target:
        return f"{body} {_filler(target - words)}{tail}".strip()
    # trim: drop trailing tokens until the word count reaches the target
    tokens = body.split()
    while tokens and witness_word_count(" ".join(tokens)) > target:
        tokens.pop()
    return f"{' '.join(tokens)}{tail}".strip()


def pad_to_band(text: str, *, target: int | None = None) -> str:
    """Bring a witness into §8.5's band, clamping to the nearer edge."""
    lo, hi = STEM_BAND
    words = witness_word_count(text)
    goal = target if target is not None else min(max(words, lo), hi)
    return fit_to_band(text, target=goal)


def _filler(n_words: int) -> str:
    from dci1v6.verifiers.witnesses import feature_free
    return feature_free(max(n_words, 0))


def realistic_witness_verdict(candidate: Constraint, focal: Constraint
                              ) -> dict[str, Any]:
    """One (candidate, B) pair: does a joint witness fit the stem band?

    The obligation §7.7 states is that a witness inside the band **exists**,
    not that the constructor's shortest one does. So the shortest witness is
    brought into the band --- padded up to 60 words or trimmed down to 120 ---
    and both constraints are re-checked on the result. A pair that survives
    has a realistic witness; a pair that does not is reported with which of
    the two obligations failed and why.

    A witness that fails *formal* satisfiability is a different failure and is
    reported as one: §13.5 evaluates ``V_sat`` over both obligations and the
    reason must say which was not met.
    """
    if focal.kind != "B":
        raise ProtocolError(
            "§7.7's realistic obligation is stated against B at every "
            f"admissible severity; got {focal.kind!r}")
    try:
        minimal = joint_witness(candidate, focal)
    except Exception as exc:
        return {"candidate": candidate.label, "focal": focal.label,
                "formal": False, "realistic": False, "words": None,
                "adjusted": None,
                "reason": f"no formal joint witness: {exc}"}
    formal = (passes(candidate, _statistic(candidate, minimal), minimal)
              and passes(focal, _statistic(focal, minimal), minimal))
    lo, hi = STEM_BAND
    minimal_words = witness_word_count(minimal)
    text = pad_to_band(minimal)
    words = witness_word_count(text)
    inside = lo <= words <= hi
    still_passes = (passes(candidate, _statistic(candidate, text), text)
                    and passes(focal, _statistic(focal, text), text))
    adjusted = ("padded" if words > minimal_words else
                "trimmed" if words < minimal_words else "unchanged")
    reason = None
    if not formal:
        reason = ("the constructed witness does not satisfy both "
                  "constraints, so the pair fails FORMAL joint "
                  "satisfiability")
    elif not inside:
        reason = (f"no witness of {lo}-{hi} words could be constructed; the "
                  f"shortest is {minimal_words} words")
    elif not still_passes:
        reason = (f"the shortest joint witness is {minimal_words} words and "
                  f"{adjusting_verb(adjusted)} it to {words} words --- "
                  f"§8.5's stem band --- breaks one of the two constraints, "
                  "so this severity is formally satisfiable and unreachable "
                  "inside the response genre this study registers")
    return {"candidate": candidate.label, "focal": focal.label,
            "formal": bool(formal),
            "realistic": bool(formal and inside and still_passes),
            "words": words, "minimal_words": minimal_words,
            "adjusted": adjusted, "band": list(STEM_BAND), "reason": reason}


def adjusting_verb(adjusted: str) -> str:
    return {"padded": "padding", "trimmed": "trimming",
            "unchanged": "leaving"}[adjusted]


def _statistic(constraint: Constraint, text: str) -> int:
    from dci1v6.verifiers.statistics import (
        family_statistic, focal_statistic, s0_count,
    )
    if constraint.kind == "A":
        return s0_count(text)
    if constraint.kind == "B":
        return focal_statistic(text)
    return family_statistic(constraint.kind, text)


def run_realistic_suite(families: Sequence[str] | None = None, *,
                        focal_severities_to_test: Iterable[int] | None = None
                        ) -> dict[str, Any]:
    """§7.7 over the declared range of every family, against B at every m.

    Returns the per-(family, severity) verdict and the set of severities with
    **no** realistic witness at any admissible m --- which §13.5's ``V_sat``
    reads and which is reported by family and severity rather than waived.
    """
    families = list(families if families is not None else FAMILIES)
    focal = list(focal_severities_to_test if focal_severities_to_test
                 is not None else focal_severities(extended=True))
    verdicts: list[dict[str, Any]] = []
    unreachable: dict[str, list[int]] = {}
    for family in families:
        for severity in declared_range(family):
            candidate = Constraint(family, severity, reserve=True)
            results = [realistic_witness_verdict(candidate,
                                                 Constraint("B", m,
                                                            extended=True))
                       for m in focal]
            realistic = [r for r in results if r["realistic"]]
            verdicts.append({
                "candidate": candidate.label,
                "realistic_at": [r["focal"] for r in realistic],
                "n_focal_tested": len(results),
                "worst_words": max((r["words"] or 0) for r in results),
                "minimal_words": min((r.get("minimal_words") or 0)
                                     for r in results),
                "reason": (None if realistic else
                           next((r["reason"] for r in results if r["reason"]),
                                None)),
            })
            if not realistic:
                unreachable.setdefault(family, []).append(severity)
    return {"section": "§7.7", "families": families,
            "focal_severities": focal, "verdicts": verdicts,
            "unreachable": {k: sorted(v) for k, v in unreachable.items()},
            "n_unreachable": sum(len(v) for v in unreachable.values()),
            "note": "a family with no realistic witness at a severity is not "
                    "admissible to any slot AT THAT SEVERITY; the failure is "
                    "reported by family and severity rather than waived"}


def unreachable_severities(report: dict[str, Any]) -> dict[str, list[int]]:
    return dict(report["unreachable"])
