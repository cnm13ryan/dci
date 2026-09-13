"""Machine-verified witnesses for every registered pair (v4r2 §7.3, check C9).

v3 certified witnesses for A+B and A+R only. The v4 composition matrix runs
all ten unordered pairs over {A, B, R1, R2, R3}, so B+R and R+R' witnesses
are required as well and had never been built. This module covers every
unordered pair of distinct registered constraint *kinds* at every pair of
registered severities — 4,910 compositions — and for each one certifies:

* **joint satisfiability**: one response satisfies both at once;
* **non-entailment, both directions**: one response satisfies the first and
  fails the second, and one does the reverse.

The construction is uniform rather than per-pair, which is what makes it
checkable by eye as well as by machine. ``BASE_SENTENCE`` is authored for v4
to satisfy every family at severity 0 and the word-length rule at m = 7
simultaneously: it is all lower-case, has no comma, no word containing the
letter a, no word beginning with b, none ending in ing or y, no one-letter
word, no doubled letter, and no word longer than seven letters. Each
violation token raises exactly one family statistic and leaves every other
statistic and the exact count untouched — asserted by
``assert_token_orthogonality`` rather than assumed, because a token that
moved two statistics would silently turn a non-entailment witness into a
double failure.
"""
from __future__ import annotations

from itertools import combinations

from dci1v4.errors import ProtocolError
from dci1v4.verifiers.compliance import score_constraint
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    Constraint,
    TARGET_GRID,
)
from dci1v4.verifiers.statistics import FAMILY_STATISTICS, focal_statistic
from dci1v4.verifiers.target import s0_count

#: Satisfies every family at q = 0 and B at m = 7; contains no target word.
BASE_SENTENCE = "the river runs west then it drifts to the north."
#: One occurrence of the target word, and nothing else that moves a statistic.
CARRIER = "however " + BASE_SENTENCE

#: Token whose repetition raises exactly one family statistic by one per copy.
#: RF5 adds a bare comma and no word; RF6 uses a four-letter capitalised word
#: rather than a bare capital, because a bare "Q" would also be a one-letter
#: word and would move RF3 at the same time.
VIOLATION_TOKENS: dict[str, str] = {
    "RF1": "bold", "RF2": "going", "RF3": "o", "RF4": "coffee",
    "RF5": ",", "RF6": "Chin", "RF7": "cat", "RF8": "grey",
}
#: Fails B at every registered m and moves no family statistic: twelve
#: letters, no a, no doubled letter, not b-initial, not ing- or y-final.
FOCAL_VIOLATOR = "prohibitions"


def joint_witness(kinds: dict[str, int]) -> str:
    """A response satisfying every constraint in ``kinds`` at once."""
    n = kinds.get("A")
    if n is None:
        return BASE_SENTENCE
    return " ".join([CARRIER] * n)


def violation_tail(kind: str, severity: int) -> str:
    """Text pushing ``kind`` past ``severity`` and nothing else past anything."""
    if kind == "B":
        return FOCAL_VIOLATOR
    if kind == "A":
        raise ProtocolError("A is failed by absence of the target, not by a "
                            "tail; see satisfy_and_fail")
    token = VIOLATION_TOKENS[kind]
    if kind == "RF5":
        return "," * (severity + 1)
    return " ".join([token] * (severity + 1))


def satisfy_and_fail(satisfied: Constraint, failed: Constraint) -> str:
    """A response satisfying ``satisfied`` and failing ``failed`` (§7.3)."""
    if failed.kind == "A":
        # The target word is absent, so s0 = 0, and every registered n >= 1.
        base = BASE_SENTENCE
        if satisfied.kind == "A":
            raise ProtocolError("a pair never repeats a constraint kind")
        if satisfied.kind == "B":
            return base
        return base
    text = joint_witness({satisfied.kind: satisfied.severity}
                         if satisfied.kind == "A" else {})
    return text + " " + violation_tail(failed.kind, failed.severity)


def _passes(constraint: Constraint, text: str) -> bool:
    return score_constraint(constraint, text, truncated=False).passed


def verify_pair(c1: Constraint, c2: Constraint) -> None:
    """Certify joint satisfiability and both non-entailment directions."""
    if c1.kind == c2.kind:
        raise ProtocolError("a registered pair carries two distinct kinds")
    kinds = {c1.kind: c1.severity, c2.kind: c2.severity}
    joint = joint_witness(kinds)
    for constraint in (c1, c2):
        if not _passes(constraint, joint):
            raise ProtocolError(
                f"joint witness fails {constraint.kind}@{constraint.severity} "
                f"in pair {c1.kind}+{c2.kind}")
    for satisfied, failed in ((c1, c2), (c2, c1)):
        text = satisfy_and_fail(satisfied, failed)
        if not _passes(satisfied, text):
            raise ProtocolError(
                f"non-entailment witness fails its own constraint "
                f"{satisfied.kind}@{satisfied.severity}")
        if _passes(failed, text):
            raise ProtocolError(
                f"non-entailment witness passes {failed.kind}@"
                f"{failed.severity}; {satisfied.kind} -> {failed.kind} "
                f"non-entailment is not demonstrated")


def registered_instances() -> list[Constraint]:
    """Every registered constraint instance: A, B and all 94 ladder rungs."""
    out = [Constraint("A", n) for n in TARGET_GRID]
    out += [Constraint("B", m) for m in FOCAL_GRID]
    for family, ladder in REFERENCE_LADDERS.items():
        out += [Constraint(family, q) for q in ladder]
    return out


def all_pairs() -> list[tuple[Constraint, Constraint]]:
    """Every unordered pair of distinct kinds at every severity combination."""
    return [(a, b) for a, b in combinations(registered_instances(), 2)
            if a.kind != b.kind]


def assert_token_orthogonality() -> None:
    """Each violation token moves exactly one statistic (§7.3 parse
    independence is about inputs; this is about the witness construction)."""
    base_family = {f: fn(BASE_SENTENCE) for f, fn in FAMILY_STATISTICS.items()}
    base_focal = focal_statistic(BASE_SENTENCE)
    if any(v != 0 for v in base_family.values()):
        raise ProtocolError(f"base sentence is not family-clean: "
                            f"{ {k: v for k, v in base_family.items() if v} }")
    if base_focal > min(FOCAL_GRID):
        raise ProtocolError(f"base sentence longest word {base_focal} exceeds "
                            f"the most restrictive registered m")
    if s0_count(BASE_SENTENCE) != 0:
        raise ProtocolError("base sentence contains the target word")
    if s0_count(CARRIER) != 1:
        raise ProtocolError("carrier does not contain exactly one target word")
    for family, token in VIOLATION_TOKENS.items():
        text = BASE_SENTENCE + " " + (token * 3 if family == "RF5"
                                      else " ".join([token] * 3))
        moved = {f: FAMILY_STATISTICS[f](text) for f in FAMILY_STATISTICS
                 if FAMILY_STATISTICS[f](text) != base_family[f]}
        if set(moved) != {family}:
            raise ProtocolError(
                f"{family} token {token!r} moves {sorted(moved)}, not just "
                f"{family}")
        if focal_statistic(text) > min(FOCAL_GRID):
            raise ProtocolError(f"{family} token {token!r} breaks B at m="
                                f"{min(FOCAL_GRID)}")
        if s0_count(text) != 0:
            raise ProtocolError(f"{family} token {token!r} moves the exact "
                                f"count")
    focal_text = BASE_SENTENCE + " " + FOCAL_VIOLATOR
    moved = {f: FAMILY_STATISTICS[f](focal_text) for f in FAMILY_STATISTICS
             if FAMILY_STATISTICS[f](focal_text) != base_family[f]}
    if moved:
        raise ProtocolError(f"focal violator moves {sorted(moved)}")
    if focal_statistic(focal_text) <= max(FOCAL_GRID):
        raise ProtocolError("focal violator does not exceed the loosest m")


def verify_all_witnesses() -> dict:
    """Execute every registered composition's three witnesses; fail closed."""
    assert_token_orthogonality()
    pairs = all_pairs()
    kinds_seen: set[frozenset[str]] = set()
    for c1, c2 in pairs:
        verify_pair(c1, c2)
        kinds_seen.add(frozenset((c1.kind, c2.kind)))
    return {"pairs": len(pairs), "kind_pairs": len(kinds_seen),
            "witnesses_verified": True,
            "base_sentence": BASE_SENTENCE, "carrier": CARRIER}
