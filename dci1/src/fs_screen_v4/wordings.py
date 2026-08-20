"""Four wordings per candidate constraint, under the registered discipline.

The same four rules the registered families obey (§7.3, §13.2 condition 3):

* four wordings per constraint, one verifier deciding all four;
* every wording within 20% of the A wording of the SAME INDEX in
  alphabetic-run word count -- the caliper is against A, not against B;
* severity renders as a numeral, which is not an alphabetic run, so every
  count is severity-invariant;
* whole-answer scope, no positional or per-sentence qualifier;
* vocabulary drawn from the candidate's own rule statement.

A's counts are [6, 7, 7, 7], so index 0 must land in {5, 6, 7} and indices
1-3 in {6, 7, 8}. That is a tight budget and it is what forced the compact
phrasing below; ``assert_caliper_feasible`` proves every candidate severity
clears it at every n rather than trusting the authoring.
"""
from __future__ import annotations

from dci1v4.protocol.wordings import (N_WORDINGS, WORDING_LENGTH_TOLERANCE,
                                      target_wordings, wording_word_count)
from dci1v4.verifiers.constraints import TARGET_GRID
from dci1v4.errors import ProtocolError

from fs_screen_v4.constraints import CANDIDATES, CANDIDATE_IDS


def _rate(kind: str, q: int) -> tuple[str, str, str, str]:
    if kind == "CR7":
        return (f"At most {q}% of words contain letter a.",
                f"Use at most {q}% of words containing letter a.",
                f"No more than {q}% of words contain letter a.",
                f"Limit words containing letter a to {q}%.")
    if kind == "CR4":
        return (f"At most {q}% of words contain doubled letters.",
                f"Use at most {q}% of words with doubled letters.",
                f"No more than {q}% of words contain doubled letters.",
                f"Limit words with doubled letters to {q}%.")
    if kind == "CR6":
        return (f"At most {q}% of words use capitals.",
                f"Use at most {q}% of words with capitals.",
                f"No more than {q}% of words use capitals.",
                f"Limit words that use capitals to {q}%.")
    raise ProtocolError(f"{kind} is not a candidate rate family")


def _lower_bound(kind: str, q: int) -> tuple[str, str, str, str]:
    if kind == "CL1":
        return (f"At least {q} words must begin with b.",
                f"Use at least {q} words beginning with b.",
                f"No fewer than {q} words may begin with b.",
                f"Include at least {q} words starting with b.")
    if kind == "CL7":
        return (f"At least {q} words must contain letter a.",
                f"Use at least {q} words containing letter a.",
                f"No fewer than {q} words contain letter a.",
                f"Include at least {q} words with letter a.")
    if kind == "CL8":
        return (f"At least {q} words must end with y.",
                f"Use at least {q} words ending with y.",
                f"No fewer than {q} words may end with y.",
                f"Include at least {q} words finishing with y.")
    raise ProtocolError(f"{kind} is not a candidate lower-bound family")


def candidate_wordings(kind: str, q: int) -> tuple[str, str, str, str]:
    family = CANDIDATES[kind]
    if q not in family.ladder:
        raise ProtocolError(f"{kind} severity {q} outside its ladder")
    return (_rate(kind, q) if family.form == "rate"
            else _lower_bound(kind, q))


def wording(kind: str, index: int, q: int) -> str:
    if not 0 <= index < N_WORDINGS:
        raise ProtocolError(f"wording index {index} outside 0..3")
    return candidate_wordings(kind, q)[index]


def length_caliper_ok(kind: str, q: int, n: int) -> bool:
    a = [wording_word_count(w) for w in target_wordings(n)]
    c = [wording_word_count(w) for w in candidate_wordings(kind, q)]
    return all(abs(x - y) <= WORDING_LENGTH_TOLERANCE * y
               for x, y in zip(c, a))


def assert_severity_invariance() -> None:
    """Word counts must not move with severity, or the caliper would be a
    function of the rung and admission would depend on the numeral."""
    for kind in CANDIDATE_IDS:
        ladder = CANDIDATES[kind].ladder
        counts = {tuple(wording_word_count(w)
                        for w in candidate_wordings(kind, q)) for q in ladder}
        if len(counts) != 1:
            raise ProtocolError(
                f"{kind} wording word counts vary with severity: {counts}")


def assert_caliper_feasible() -> None:
    """Every candidate severity clears the caliper at every n in the grid."""
    bad = [(k, q, n) for k in CANDIDATE_IDS for q in CANDIDATES[k].ladder
           for n in TARGET_GRID if not length_caliper_ok(k, q, n)]
    if bad:
        raise ProtocolError(
            f"{len(bad)} candidate (family, severity, n) combinations fail the "
            f"20% length caliper against A, e.g. {bad[:5]}")


def assert_rule_vocabulary() -> None:
    """Every content word of a wording appears in its rule statement, so a
    wording cannot smuggle in a concept the rule does not state."""
    allowed_extra = {"use", "no", "more", "than", "limit", "to", "include",
                     "fewer", "may", "must", "at", "least", "most", "of",
                     "the", "in", "with", "that", "answer", "words"}
    for kind in CANDIDATE_IDS:
        rule = set(CANDIDATES[kind].rule_statement.lower()
                   .replace(".", "").split())
        rule |= {"letter", "letters", "doubled", "capitals", "percent",
                 "contain", "containing", "begin", "beginning", "starting",
                 "end", "ending", "finishing", "using"}
        for q in CANDIDATES[kind].ladder:
            for text in candidate_wordings(kind, q):
                words = {w for w in text.lower().replace(".", "")
                         .replace("%", "").split() if w.isalpha()}
                stray = words - rule - allowed_extra
                if stray:
                    raise ProtocolError(
                        f"{kind} wording {text!r} uses {sorted(stray)}, which "
                        f"its rule statement does not state")


def caliper_table(n: int) -> dict[str, dict]:
    a = [wording_word_count(w) for w in target_wordings(n)]
    out = {}
    for kind in CANDIDATE_IDS:
        q = CANDIDATES[kind].ladder[0]
        c = [wording_word_count(w) for w in candidate_wordings(kind, q)]
        out[kind] = {"a_counts": a, "candidate_counts": c,
                     "ok": length_caliper_ok(kind, q, n)}
    return out
