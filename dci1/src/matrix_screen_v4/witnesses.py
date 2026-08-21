"""Joint satisfiability and non-entailment for the exact constraint set used,
witnessed by real generations.

§7.3 requires, for every registered pair at every registered severity, a
machine-verified response satisfying both, and one response satisfying the
first while failing the second in each direction. The registered
``verifiers.witnesses.verify_pair`` does that for registered symbols; the FORM
screen's ``verify_candidate_pair`` does it for the candidate families. Neither
covers the two cases this screen creates:

* B at m = 11 or 12, which the registered code refuses by construction;
* a pair of one registered family and one candidate family.

Monotonicity closes half of it and only half. B is monotone in m -- proved on
the fixture suite by ``bgrid_screen_v4.focal.assert_monotone_in_m`` -- so a text
satisfying both R and B at m = 10 also satisfies both at m = 12, and joint
satisfiability carries upward. **Non-entailment does not carry upward**: a
witness that satisfies R and fails B at m = 10 may pass B at m = 12, so the
direction has to be re-witnessed at the severity actually used.

So this module witnesses all three properties directly, and it does it from the
model's own calibration-screen responses rather than from constructed strings. A
real generation is a stronger witness than an authored one: it shows the
property holds in the region of text space the model actually occupies.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.constraints import (FOCAL_GRID, REFERENCE_LADDERS,
                                          TARGET_GRID, Constraint)
from dci1v4.verifiers.witnesses import verify_pair

from cal_screen_v4.run import score_cell
from fs_screen_v4.constraints import CANDIDATES
from fs_screen_v4.witnesses import verify_candidate_pair

#: A witness is an existence proof, so the search is capped. Every pair below
#: is witnessed well inside this many responses; the cap is recorded on the
#: artifact so a failure to witness cannot be confused with a short search.
POOL_LIMIT = 3000

DCI1 = Path(__file__).resolve().parent.parent.parent
CAL_EVIDENCE = DCI1 / "evidence" / "cal-screen-v4"


def response_pool(model: str, *, limit: int | None = None) -> list[str]:
    """Every distinct genuine response the calibration screen produced."""
    texts: list[str] = []
    seen: set[str] = set()
    for path in sorted(CAL_EVIDENCE.glob(f"{model}/screen-cap*/cache*.jsonl")):
        for line in path.open():
            row = json.loads(line)
            text = row.get("raw_response") or ""
            if text and text not in seen:
                seen.add(text)
                texts.append(text)
                if limit and len(texts) >= limit:
                    return texts
    return texts


def _registered(kind: str, severity: int) -> bool:
    """Can the registered witness machinery speak about this symbol at all?"""
    if kind == "A":
        return severity in TARGET_GRID
    if kind == "B":
        return severity in FOCAL_GRID
    return kind in REFERENCE_LADDERS and severity in REFERENCE_LADDERS[kind]


def constructive_proof(a: Mapping[str, Any], b: Mapping[str, Any]
                       ) -> tuple[str, str | None]:
    """Prove the pair with the study's own witness machinery where it reaches.

    ``verify_pair`` and ``verify_candidate_pair`` construct witnesses rather
    than looking for them, so they answer the question §7.3 actually asks --
    *is* this pair jointly satisfiable and non-entailing -- rather than the
    weaker question of whether a particular sample happens to contain a witness.
    They cannot reach two cases this screen creates: B at m = 11 or 12, which
    the registered code refuses by construction, and a candidate paired with a
    candidate. Those fall through to the response-pool search.
    """
    ak, asev = a["kind"], a["severity"]
    bk, bsev = b["kind"], b["severity"]
    try:
        if _registered(ak, asev) and _registered(bk, bsev):
            verify_pair(Constraint(ak, asev), Constraint(bk, bsev))
            return "registered verify_pair", None
        # `verify_candidate_pair` constructs its non-entailment witnesses for
        # A and for B specifically -- `verify_all` iterates exactly those -- and
        # its "candidate satisfied, other failed" branch appends a long word,
        # which fails B and says nothing about an RF family. Using it against a
        # reference family is outside its design envelope and reports a
        # construction failure as an apparent entailment. So it is used only
        # where it was built to be used, and candidate-versus-reference falls
        # through to the response pool.
        if ak in CANDIDATES and bk in ("A", "B") and _registered(bk, bsev):
            verify_candidate_pair(ak, asev, Constraint(bk, bsev))
            return "candidate verify_pair", None
        if bk in CANDIDATES and ak in ("A", "B") and _registered(ak, asev):
            verify_candidate_pair(bk, bsev, Constraint(ak, asev))
            return "candidate verify_pair", None
    except ProtocolError as error:
        return "constructive", str(error)
    return "not reachable constructively", None


def verify_set(model: str, constituents: Sequence[Mapping[str, Any]], *,
               pairs: Sequence[tuple[str, str]] | None = None,
               pool: Iterable[str] | None = None) -> dict[str, Any]:
    """Joint satisfiability and both non-entailment directions for every pair
    that actually **co-occurs in a cell**.

    Not every combination: two severities of one family never share a cell, and
    non-entailment between them is not merely unwitnessed but impossible --
    passing "at most 32% of words" entails passing "at most 44%". §7.3's
    requirement is about registered pairs, which are pairs that compose, so the
    caller passes the pairs the cell plan actually builds.

    An unwitnessed property is REPORTED, not swallowed: a screen that quietly
    proceeds past a missing witness is the failure §7.3 exists to prevent.
    """
    texts = (list(pool) if pool is not None
             else response_pool(model, limit=POOL_LIMIT))

    # Verdicts are memoised per (constraint, text): a witness search over 55
    # pairs would otherwise rescore the same text once per pair.
    cache: dict[tuple[str, int, int], bool] = {}

    def passes(text: str, c: Mapping[str, Any]) -> bool:
        key = (c["kind"], c["severity"], id(text))
        if key not in cache:
            cache[key] = bool(score_cell(c["kind"], c["severity"], text,
                                         truncated=False)["passed"])
        return cache[key]

    by_role = {c["role"]: c for c in constituents}
    wanted = (list(pairs) if pairs is not None
              else [(constituents[i]["role"], constituents[j]["role"])
                    for i, j in combinations(range(len(constituents)), 2)])
    results: dict[str, Any] = {}
    unwitnessed: list[str] = []
    for role_a, role_b in wanted:
        a, b = by_role[role_a], by_role[role_b]
        label = f"{a['role']}({a['kind']}:{a['severity']})|" \
                f"{b['role']}({b['kind']}:{b['severity']})"
        found = {"joint": None, "a_not_b": None, "b_not_a": None}
        for text in texts:
            pa, pb = passes(text, a), passes(text, b)
            if pa and pb and found["joint"] is None:
                found["joint"] = text
            elif pa and not pb and found["a_not_b"] is None:
                found["a_not_b"] = text
            elif pb and not pa and found["b_not_a"] is None:
                found["b_not_a"] = text
            if all(found.values()):
                break
        method, failure = constructive_proof(a, b)
        results[label] = {
            "constructive_method": method,
            "constructive_failure": failure,
            "pool_witnesses": {
                name: (None if text is None else
                       {"words": len(text.split()), "excerpt": text[:80]})
                for name, text in found.items()}}
        missing = [name for name, text in found.items() if text is None]
        if not (not failure and not method.startswith("not reachable")) \
                and missing:
            unwitnessed.append(
                f"{label}: {method}"
                + (f" ({failure})" if failure else "")
                + f", and the response pool supplies no {', '.join(missing)}")
        # A pair is proved if the study's own constructor certifies it, or if
        # real generations supply all three witnesses. A genuine response that
        # satisfies one constraint and fails the other IS a machine-verified
        # non-entailment witness, and a stronger one than a constructed string.
        proved_constructively = not failure and not method.startswith(
            "not reachable")
        proved_by_pool = not missing
        results[label]["proved"] = proved_constructively or proved_by_pool
        results[label]["proved_by"] = (
            "constructor" if proved_constructively else
            "response pool" if proved_by_pool else "neither")
        if missing:
            results[label]["pool_gap"] = missing
    return {"pool_size": len(texts), "pool_limit": POOL_LIMIT,
            "pairs_checked": len(wanted), "pairs": results,
            "all_witnessed": not unwitnessed, "unwitnessed": unwitnessed,
            "source": "the model's own calibration-screen responses",
            "note": ("joint satisfiability carries upward in m by B's proved "
                     "monotonicity; non-entailment does not, and is witnessed "
                     "here at the severity actually used")}


__all__ = ["response_pool", "verify_set"]
