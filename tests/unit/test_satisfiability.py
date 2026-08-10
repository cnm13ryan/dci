"""Logically impossible pairs must never reach a generated design.

Pre-repair the registry's `incompatible_with` was populated on NOTHING and
`entails` on exactly one spec, so the declared-relation machinery was inert. The
rules here are pinned against the LIVE registry, so a renamed rule_family shows up
as a failing test rather than as a silently weakened audit.
"""
import json

import pandas as pd
import pytest

from dci.constraints.satisfiability import (PARAMETRIC_RULES, assert_design_is_satisfiable,
                                            audit_pairs, corpus_witness,
                                            declared_incompatible,
                                            forbidden_pairs, pair_verdict,
                                            parametric_verdict)
from dci.constraints.spec import P, spec

pytestmark = pytest.mark.cpu


def _spec(cid, family, params=(), scope="sentence", role="candidate",
          incompatible=()):
    return spec(cid, "t", cid, "format", "local_check", scope, "span", role,
                family, params, "cse_pool", incompatible_with=incompatible)


NOCOMMA = _spec("U_FMT_NOCOMMA", "no_char", P(char=","), scope="whole_text",
                role="unrelated")
COMMA1 = _spec("S_COMMA", "commas_per_sentence", P(n=1))
COMMA12 = _spec("S_COMMA12", "comma_and_min_words", P(n=12))
SEMI2 = _spec("U_FMT_SEMI2", "exact_char_total", P(char=";", n=2),
              scope="whole_text", role="unrelated")
SEMI_EACH = _spec("S_SEMICOLON", "semicolon_per_sentence", ())
MINW15 = _spec("S_MINWORDS15", "min_words_per_sentence", P(n=15))
CHARS40 = _spec("U_CHARS40", "exact_char_total", P(n=40),
                scope="whole_text", role="unrelated")
BENIGN = _spec("C_L3", "sentence_initial", P(letter="S"))


# ------------------------------------------------------------- the hard case
def test_no_commas_versus_comma_per_sentence_is_impossible():
    kind, why = pair_verdict(NOCOMMA, COMMA1)
    assert kind == "hard"
    assert "forbids commas" in why
    # symmetric
    assert pair_verdict(COMMA1, NOCOMMA)[0] == "hard"


def test_no_commas_versus_comma_and_min_words_is_impossible():
    assert pair_verdict(NOCOMMA, COMMA12)[0] == "hard"


def test_declared_incompatibility_is_read_symmetrically():
    a = _spec("A1", "f1", incompatible=("B1",))
    b = _spec("B1", "f2")
    assert declared_incompatible(a, b) and declared_incompatible(b, a)
    assert pair_verdict(a, b)[0] == "hard"


# ------------------------------------------- the parameter-dependent case
def test_semicolon_total_versus_per_sentence_is_restricted_not_hard():
    """Satisfiable only when the sentence count equals the declared total."""
    kind, why = pair_verdict(SEMI2, SEMI_EACH)
    assert kind == "restricted"
    assert "exactly 2" in why
    assert "impossible" in why


def test_restricted_pairs_are_unusable_for_calibration():
    table = audit_pairs([("U_FMT_SEMI2", "S_SEMICOLON")],
                        {"U_FMT_SEMI2": SEMI2, "S_SEMICOLON": SEMI_EACH})
    assert not bool(table["usable_for_calibration"].iloc[0])


def test_min_words_versus_a_tight_character_budget():
    assert pair_verdict(MINW15, CHARS40)[0] == "hard"


def test_a_character_COUNT_is_not_a_length_budget():
    """exact_char_total is overloaded: with `char` it counts occurrences.

    Reading "exactly two semicolons" as "an answer of two characters" mis-flagged
    96 legitimate Gate 0 calibration rows as contradictions.
    """
    assert pair_verdict(MINW15, SEMI2) == ("ok", "")
    counted = _spec("U_SEMI2", "exact_char_total", P(char=";", n=2),
                    scope="whole_text", role="unrelated")
    assert pair_verdict(_spec("C_W3", "min_words_per_sentence", P(n=8)),
                        counted) == ("ok", "")


def test_a_benign_pair_is_ok():
    assert pair_verdict(BENIGN, SEMI_EACH) == ("ok", "")
    assert parametric_verdict(BENIGN, SEMI_EACH) is None


# ---------------------------------------------------------- design enforcement
def _design(pairs):
    return pd.DataFrame([
        {"row_id": f"r{i}", "stage": "calibration",
         "ordered_constraint_ids": json.dumps(list(p))}
        for i, p in enumerate(pairs)])


REGISTRY = {c.constraint_id: c for c in
            (NOCOMMA, COMMA1, COMMA12, SEMI2, SEMI_EACH, MINW15, CHARS40, BENIGN)}


def test_a_clean_design_passes():
    out = assert_design_is_satisfiable(
        _design([("C_L3", "S_SEMICOLON"), ("C_L3",)]), REGISTRY)
    assert out.empty


def test_an_impossible_calibration_row_is_refused():
    with pytest.raises(ValueError, match="not jointly satisfiable"):
        assert_design_is_satisfiable(
            _design([("U_FMT_NOCOMMA", "S_COMMA")]), REGISTRY, label="calibration")


def test_a_restricted_calibration_row_is_also_refused():
    """g and r are LEARNED here, so a near-impossible pairing distorts them."""
    with pytest.raises(ValueError, match="not jointly satisfiable"):
        assert_design_is_satisfiable(
            _design([("U_FMT_SEMI2", "S_SEMICOLON")]), REGISTRY)


def test_the_error_names_the_row_and_the_reason():
    try:
        assert_design_is_satisfiable(
            _design([("U_FMT_NOCOMMA", "S_COMMA")]), REGISTRY)
    except ValueError as exc:
        assert "U_FMT_NOCOMMA" in str(exc) and "S_COMMA" in str(exc)
        assert "impossibility, not compositional burden" in str(exc)
    else:
        pytest.fail("an impossible pair was accepted")


def test_forbidden_pairs_enumerates_both_kinds():
    out = forbidden_pairs([("U_FMT_NOCOMMA", "S_COMMA"),
                           ("U_FMT_SEMI2", "S_SEMICOLON"),
                           ("C_L3", "S_SEMICOLON")], REGISTRY)
    kinds = {row[2] for row in out}
    assert kinds == {"hard", "restricted"}
    assert len(out) == 2


def test_unknown_ids_are_skipped_not_guessed():
    assert assert_design_is_satisfiable(
        _design([("NOT_IN_REGISTRY", "S_COMMA")]), REGISTRY).empty


# ------------------------------------------------- empirical evidence is a signal
def test_a_witness_proves_satisfiability():
    class R:
        def __init__(self, ok): self.binary_pass = int(ok)

    def verify(text, cid):
        return R(cid in text)

    found = corpus_witness("a", "b", ["a and b", "only a"], verify)
    assert found["witness_found"] and not found["flag_for_review"]


def test_absence_of_a_witness_only_flags_for_review():
    """A finite corpus cannot prove impossibility, so it must not claim to."""
    class R:
        def __init__(self, ok): self.binary_pass = int(ok)

    def verify(text, cid):
        return R(cid in text)

    out = corpus_witness("a", "zzz", ["a only", "a again"], verify)
    assert not out["witness_found"]
    assert out["flag_for_review"] is True
    assert out["n_searched"] == 2
    # It reports a FLAG, never a verdict field.
    assert "verdict" not in out and "impossible" not in out


# ----------------------------------------------- pinned against the live registry
def test_rule_families_still_exist_in_the_real_registry():
    """A renamed rule_family must break this test, not weaken the audit silently."""
    import re
    from pathlib import Path
    src = (Path(__file__).parents[2] / "src/dci/pipeline/stages"
           / "c142_constraints_and_tasks.py").read_text()
    families = set(re.findall(r'"([a-z_0-9]+)",\s*P\(', src))
    families |= set(re.findall(r'"([a-z_0-9]+)",\s*\(\)', src))
    for pair in PARAMETRIC_RULES:
        for family in pair:
            assert family in families, (
                f"rule_family {family!r} is referenced by a satisfiability rule "
                "but no longer appears in the constraint registry")


def test_the_verified_hard_pair_is_declared_in_the_registry():
    from pathlib import Path
    src = (Path(__file__).parents[2] / "src/dci/pipeline/stages"
           / "c142_constraints_and_tasks.py").read_text()
    assert 'incompatible_with=("U_FMT_NOCOMMA",)' in src, (
        "the S_COMMA / U_FMT_NOCOMMA contradiction must be DECLARED, not only "
        "derivable from parameters")
