"""Pairwise satisfiability: declared, parameter-dependent, and empirical.

THREE DIFFERENT IDEAS
---------------------
Individually valid   the constraint is meaningful and its verifier separates
                     satisfying from violating text.
Declared compatible  the registry contains no metadata saying the pair conflicts.
Jointly satisfiable  at least one possible output satisfies BOTH.

The second does NOT imply the third, and pre-repair only the second existed. The
registry provided `incompatible_with` and `entails`, both defaulting to empty
tuples, and the ONLY populated relation in the whole registry was
`B_SOFT.entails=("B",)`. `hard_eligible_universe` consulted those declarations
against A and B, so with nothing declared the machinery was inert.

WHY THIS CONTAMINATES THE SCIENCE
---------------------------------
Reference comparability is LEARNED from how each candidate interacts with
unrelated targets U. If a candidate-U pair is logically impossible, the resulting
g or r measures impossibility rather than generic compositional burden:

    contradiction -> forced failure in calibration -> distorted g/r
                  -> different admission -> a different comparison class for tau

`U_FMT_NOCOMMA` ("no commas anywhere") against `S_COMMA` ("exactly one comma per
sentence") is flatly impossible. `U_FMT_SEMI2` ("exactly two semicolons in the
answer") against `S_SEMICOLON` ("a semicolon in every sentence") is satisfiable
only when the answer has at most two sentences -- and the registry's own comment
noted the relation while declaring no incompatibility.

EMPIRICAL EVIDENCE IS A SIGNAL, NOT A PROOF
-------------------------------------------
`corpus_witness` looks for a response satisfying both. Finding one PROVES
satisfiability. Failing to find one in a finite corpus proves nothing, so it
raises a review flag and never a verdict.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

import pandas as pd

# Declared logical relations between rule families, evaluated on the INSTANTIATED
# parameters rather than the family label alone. Each entry answers: given these
# two parameter dicts, is the pair impossible, or possible only in a restricted
# regime?
#
# `hard` -> no output satisfies both, for any sentence count.
# `restricted` -> satisfiable only under the stated extra condition, which makes
#                 it unsuitable as a generic calibration pairing even though it is
#                 not a contradiction.
PairVerdict = tuple[str, str]        # (kind, explanation); kind in {ok, hard, restricted}


def _p(spec, name: str, default=None):
    return spec.param_dict.get(name, default)


def _no_char_vs_per_sentence(a, b) -> Optional[PairVerdict]:
    """"no <char> anywhere" against "n <char> per sentence"."""
    banned = _p(a, "char")
    if banned == "," and _p(b, "n", 0) and _p(b, "n", 0) > 0:
        return ("hard", f"{a.constraint_id} forbids commas entirely while "
                        f"{b.constraint_id} requires {_p(b, 'n')} per sentence")
    return None


def _exact_char_total_vs_per_sentence(a, b) -> Optional[PairVerdict]:
    """"exactly N <char> in the answer" against "one <char> in EVERY sentence".

    The registry's own note on U_FMT_SEMI2 records that it is "deliberately not
    per-sentence, unlike S_SEMICOLON" -- the relation was documented in prose and
    declared nowhere.
    """
    char, total = _p(a, "char"), _p(a, "n")
    if char != ";" or total is None:
        return None
    return ("restricted",
            f"{a.constraint_id} fixes the whole-answer '{char}' count at "
            f"{total} while {b.constraint_id} requires one per sentence, so the "
            f"pair is satisfiable only when the answer has exactly {total} "
            f"sentences. Under a target that fixes a different sentence count "
            f"the pair is impossible.")


def _min_words_vs_exact_chars(a, b) -> Optional[PairVerdict]:
    """"at least L words per sentence" against a whole-answer LENGTH budget.

    `exact_char_total` is overloaded in the registry: with a `char` parameter it
    counts occurrences of that character ("exactly two semicolons"), and only
    WITHOUT one does `n` mean a total character budget. Reading the count form as
    a budget makes "exactly 2 semicolons" look like "an answer of 2 characters",
    which is how this rule first mis-flagged 96 legitimate calibration rows.
    """
    if _p(b, "char") is not None:
        return None                      # a character COUNT, not a length budget
    lo = _p(a, "n")
    total = _p(b, "n")
    if lo and total and lo * 4 > total:
        return ("hard", f"{b.constraint_id} caps the answer at {total} characters "
                        f"while {a.constraint_id} needs at least {lo} words per "
                        "sentence")
    return None


# (family_a, family_b) -> predicate, evaluated in BOTH orders. Family names are
# the registry's own `rule_family` values, so a renamed family surfaces as a rule
# that stops matching rather than as a silently weakened audit -- which is why
# tests/unit/test_satisfiability.py pins them against the live registry.
PARAMETRIC_RULES: dict[tuple[str, str], Callable] = {
    ("no_char", "commas_per_sentence"): _no_char_vs_per_sentence,
    ("no_char", "comma_and_min_words"): _no_char_vs_per_sentence,
    ("exact_char_total", "semicolon_per_sentence"): _exact_char_total_vs_per_sentence,
    # NB: the registry's family is `min_words_per_sentence`;
    # `min_sentence_words` is the VERIFIER's name and is not a rule_family.
    ("min_words_per_sentence", "exact_char_total"): _min_words_vs_exact_chars,
}


def declared_incompatible(a, b) -> bool:
    """Symmetric reading of the registry's own `incompatible_with`."""
    return (b.constraint_id in getattr(a, "incompatible_with", ())
            or a.constraint_id in getattr(b, "incompatible_with", ()))


def parametric_verdict(a, b) -> Optional[PairVerdict]:
    """Instantiated-parameter verdict, or None when no rule applies."""
    for (fam_a, fam_b), rule in PARAMETRIC_RULES.items():
        if a.rule_family == fam_a and b.rule_family == fam_b:
            got = rule(a, b)
            if got:
                return got
        if a.rule_family == fam_b and b.rule_family == fam_a:
            got = rule(b, a)
            if got:
                return got
    return None


def pair_verdict(a, b) -> PairVerdict:
    """The combined verdict for one instantiated pair."""
    if declared_incompatible(a, b):
        return ("hard", f"{a.constraint_id} and {b.constraint_id} are declared "
                        "incompatible in the registry")
    got = parametric_verdict(a, b)
    return got or ("ok", "")


def corpus_witness(a_id: str, b_id: str, corpus: Iterable[str],
                   verify: Callable[[str, str], Any]) -> dict:
    """Search a finite corpus for a response satisfying both constraints.

    A witness PROVES satisfiability. Its absence proves nothing about a finite
    corpus, so `flag_for_review` is a prompt to look, never a verdict.
    """
    texts = list(corpus)
    for text in texts:
        if (verify(text, a_id).binary_pass and verify(text, b_id).binary_pass):
            return {"pair": f"{a_id}+{b_id}", "witness_found": True,
                    "n_searched": len(texts), "flag_for_review": False}
    return {"pair": f"{a_id}+{b_id}", "witness_found": False,
            "n_searched": len(texts), "flag_for_review": True}


def audit_pairs(pairs: Iterable[tuple[str, str]], constraints: dict) -> pd.DataFrame:
    """Verdict for every pair, for the artifact trail."""
    rows = []
    for a_id, b_id in pairs:
        if a_id not in constraints or b_id not in constraints:
            continue
        kind, why = pair_verdict(constraints[a_id], constraints[b_id])
        rows.append({"constraint_a": a_id, "constraint_b": b_id,
                     "verdict": kind, "explanation": why,
                     "usable_for_calibration": kind == "ok"})
    return pd.DataFrame(rows, columns=["constraint_a", "constraint_b", "verdict",
                                       "explanation", "usable_for_calibration"])


def forbidden_pairs(pairs: Iterable[tuple[str, str]], constraints: dict
                    ) -> list[tuple[str, str, str, str]]:
    """Pairs no generated design row may contain."""
    out = []
    for a_id, b_id in pairs:
        if a_id not in constraints or b_id not in constraints:
            continue
        kind, why = pair_verdict(constraints[a_id], constraints[b_id])
        if kind != "ok":
            out.append((a_id, b_id, kind, why))
    return out


def assert_design_is_satisfiable(design: pd.DataFrame, constraints: dict,
                                 label: str = "design") -> pd.DataFrame:
    """No generated row may pair two constraints known to be unsatisfiable.

    Applies to EVERY design -- calibration, validation and confirmatory alike --
    because a contradiction in calibration distorts the signature that defines the
    reference class, which reaches tau just as surely as a contradiction in the
    confirmatory prompt would.
    """
    import json
    problems = []
    for row in design.to_dict("records"):
        ids = row.get("ordered_constraint_ids", [])
        if isinstance(ids, str):
            ids = json.loads(ids)
        for i, a_id in enumerate(ids):
            for b_id in ids[i + 1:]:
                if a_id not in constraints or b_id not in constraints:
                    continue
                kind, why = pair_verdict(constraints[a_id], constraints[b_id])
                if kind != "ok":
                    problems.append({"row_id": row.get("row_id"),
                                     "constraint_a": a_id, "constraint_b": b_id,
                                     "verdict": kind, "explanation": why})
    frame = pd.DataFrame(problems, columns=["row_id", "constraint_a",
                                            "constraint_b", "verdict",
                                            "explanation"])
    if len(frame):
        worst = frame.head(6).to_string(index=False)
        raise ValueError(
            f"{label} contains {len(frame)} row(s) pairing constraints that are "
            f"not jointly satisfiable. Measured failure on such a row records "
            f"impossibility, not compositional burden:\n{worst}")
    return frame
