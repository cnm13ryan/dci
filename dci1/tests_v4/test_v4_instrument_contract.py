"""Contract tests for the v4 instrument seam (prereg v4r2 §7.4, §9.3, §10.2, §26).

The dci1v4 package is the pre-freeze implementation of the v4r2 *instrument
layer*: the compliance-vector primitive with graded scores, non-vacuity
predicates and degeneracy flags. These tests define the seam contract:

  1. registered grids — dense ladders, 94 reference severities (§7.2);
  2. byte-identical carry-over of the segmentation and counting sources
     from the closed v3 instruments (§10.2 carry-over rule);
  3. namespace isolation — dci1v4 imports nothing from any earlier DCI
     implementation (§26);
  4. graded scores and non-vacuity against hand-derived expectations
     (§7.4, §9.3);
  5. boolean-pass compatibility with the frozen v3 verifiers on every
     severity the two registrations share;
  6. determinism and the v4 canonical instrument-source hash (§10.6).

The v4r2 preregistration is NOT frozen; nothing here freezes it. dci1v3
sources are never modified — tests import them read-only for cross-checks.
"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from dci1v4.verifiers import verifier_source_hash as instrument_source_hash
from dci1v4.verifiers.carryover import CarryOverMismatch, carry_over_record
from dci1v4.verifiers.compliance import NON_VACUITY_MIN_WORDS, compliance_vector, score_constraint
from dci1v4.verifiers.constraints import (
    FOCAL_GRID,
    REFERENCE_LADDERS,
    TARGET_GRID,
    TARGET_WORD,
    Constraint,
)
from dci1v4.errors import InstrumentError
from dci1v4.verifiers import SEMANTIC_MODULES as INSTRUMENT_MODULES

V4_DIR = (Path(__file__).resolve().parents[1] / "src" / "dci1v4"
          / "verifiers")
V3_VERIFIERS = V4_DIR.parents[1] / "dci1v3" / "verifiers"

A5 = Constraint("A", 5)
B7 = Constraint("B", 7)


# --------------------------------------------------------------- §7 grids
def test_registered_grids_and_ladder_size():
    assert TARGET_WORD == "however"
    assert TARGET_GRID == tuple(range(1, 9))
    assert FOCAL_GRID == (7, 8, 9, 10)
    maxima = {"RF1": 8, "RF2": 8, "RF3": 8, "RF4": 6,
              "RF5": 12, "RF6": 12, "RF7": 24, "RF8": 8}
    assert {f: ladder[-1] for f, ladder in REFERENCE_LADDERS.items()} == maxima
    for family, ladder in REFERENCE_LADDERS.items():
        assert ladder == tuple(range(0, maxima[family] + 1)), family
    assert sum(len(l) for l in REFERENCE_LADDERS.values()) == 94  # §7.2


def test_grids_extend_the_v3_grids():
    """v4 keeps v3's n and m grids and fills the reference interiors."""
    from dci1v3.protocol import constants as v3c
    assert TARGET_GRID == v3c.TARGET_GRID
    assert FOCAL_GRID == v3c.FOCAL_GRID
    assert set(REFERENCE_LADDERS) == set(v3c.REFERENCE_FAMILIES)
    for family, grid in v3c.REFERENCE_FAMILIES.items():
        assert set(grid) <= set(REFERENCE_LADDERS[family]), family


@pytest.mark.parametrize("kind, severity", [
    ("A", 0), ("A", 9), ("B", 6), ("B", 11),
    ("RF1", 9), ("RF4", 7), ("RF7", 25), ("RF9", 1), ("hence", 1),
])
def test_out_of_grid_constraints_are_refused(kind, severity):
    with pytest.raises(InstrumentError):
        Constraint(kind, severity)


def test_interior_ladder_severities_are_registered():
    """The dense-ladder interiors v3 rejected are valid v4 severities."""
    for kind, severity in (("RF1", 3), ("RF4", 5), ("RF5", 1), ("RF7", 13)):
        c = Constraint(kind, severity)
        assert score_constraint(c, "a plain answer", truncated=False) \
            .processing_failure is False


# ------------------------------------------------- §10.2 carry-over seam
def _function_source(path: Path, name: str) -> str:
    source = path.read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"{name} not found in {path}")


@pytest.mark.parametrize("v4_module, v3_module, names", [
    ("words.py", "words.py", ("alpha_runs", "words_lower")),
    ("target.py", "target.py",
     ("s0_count", "s1_count", "s2_count", "s3_preprocess", "s3_count")),
    ("statistics.py", "families.py",
     ("focal_statistic", "_rf1", "_rf2", "_rf3", "_rf4",
      "_rf5", "_rf6", "_rf7", "_rf8")),
])
def test_carried_function_sources_are_byte_identical(
        v4_module, v3_module, names):
    for name in names:
        assert _function_source(V4_DIR / v4_module, name) \
            == _function_source(V3_VERIFIERS / v3_module, name), name


def test_carry_over_record_names_sources_and_matches():
    record = carry_over_record()
    assert record["v3_source"].endswith("dci1v3/verifiers")
    entries = {(e["module"], e["function"]): e for e in record["entries"]}
    assert ("target.py", "s0_count") in entries
    assert ("words.py", "alpha_runs") in entries
    assert ("target.py", "TARGET_WORD") in entries
    for entry in record["entries"]:
        assert entry["identical"] is True
        assert entry["v3_sha256"] == entry["v4_sha256"]
        assert len(entry["v3_sha256"]) == 64
    roles = {e["role"] for e in record["entries"]}
    assert roles == {"carry_over", "compatibility"}


def test_carry_over_refuses_on_any_mismatch(tmp_path):
    altered = tmp_path / "verifiers"
    shutil.copytree(V3_VERIFIERS, altered,
                    ignore=shutil.ignore_patterns("__pycache__"))
    words = altered / "words.py"
    words.write_text(words.read_text().replace(
        "runs.append", "runs.extend"))  # semantic-looking source drift
    with pytest.raises(CarryOverMismatch):
        carry_over_record(altered)


# ----------------------------------------------- §26 namespace isolation
def test_dci1v4_imports_nothing_from_earlier_dci_implementations():
    for module in sorted(V4_DIR.glob("*.py")):
        tree = ast.parse(module.read_text())
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            for name in imported:
                top = name.split(".")[0]
                assert top not in ("dci1", "dci1v3"), \
                    f"{module.name} imports {name}"


# ------------------------------------------------------ §7.4 graded scores
@pytest.mark.parametrize("n, text, expected", [
    (5, "however " * 5, 1.0),          # exact
    (5, "however " * 4, 0.8),          # one short
    (5, "no target word here", 0.0),   # zero count
    (5, "however " * 10, 0.0),         # |10-5|/5 = 1 -> 0
    (5, "however " * 11, 0.0),         # clamped at 0
    (2, "however and However!", 1.0),  # case-folded, punctuation-bounded
])
def test_graded_score_exact_count(n, text, expected):
    assert score_constraint(Constraint("A", n), text,
                            truncated=False).graded \
        == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("m, text, expected", [
    (7, "extraordinary cat", 0.5),     # 1 of 2 words too long
    (7, "cat dog", 1.0),
    (7, "", 0.0),                      # §7.4: empty answer scores 0
    (7, "....", 0.0),                  # wordless answer is empty
    (10, "extraordinary cat cat cat", 0.75),
])
def test_graded_score_word_length(m, text, expected):
    assert score_constraint(Constraint("B", m), text,
                            truncated=False).graded \
        == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("family, q, text, expected", [
    ("RF1", 4, "big bad bear bit bob", 0.8),    # count 5 -> 4/5
    ("RF1", 4, "big bad", 1.0),                 # under budget
    ("RF5", 0, "no commas here", 1.0),          # q=0 indicator
    ("RF5", 0, "one, comma", 0.0),
    ("RF6", 2, "AAAA", 0.5),                    # count 4 -> 2/4
])
def test_graded_score_reference_budget(family, q, text, expected):
    assert score_constraint(Constraint(family, q), text,
                            truncated=False).graded \
        == pytest.approx(expected, abs=1e-12)


# ------------------------------------------------------- §9.3 non-vacuity
WORD = "cat "


def test_non_vacuity_twenty_word_boundary():
    assert NON_VACUITY_MIN_WORDS == 20
    nineteen = score_constraint(B7, WORD * 19, truncated=False)
    twenty = score_constraint(B7, WORD * 20, truncated=False)
    assert nineteen.passed and nineteen.non_vacuous is False
    assert nineteen.vacuous_pass is True
    assert twenty.passed and twenty.non_vacuous is True
    assert twenty.vacuous_pass is False


def test_truncation_forces_vacuity_at_any_length():
    long_pass = score_constraint(B7, WORD * 100, truncated=True)
    assert long_pass.passed and long_pass.non_vacuous is False
    assert long_pass.vacuous_pass is True


def test_exact_count_predicate_has_no_word_floor():
    text = "however " * 5                       # 5 words, passes A@5
    score = score_constraint(A5, text, truncated=False)
    assert score.passed and score.non_vacuous is True
    truncated = score_constraint(A5, text, truncated=True)
    assert truncated.passed and truncated.vacuous_pass is True
    empty = score_constraint(A5, "", truncated=False)
    assert empty.passed is False and empty.non_vacuous is False


def test_vacuous_passes_stay_passes():
    """§9.3: vacuous passes count as passes in the primary estimand."""
    score = score_constraint(Constraint("RF5", 2), "brief.", truncated=False)
    assert score.passed is True
    assert score.vacuous_pass is True


# ------------------------------------------------- §9.1/§9.3 vector record
def test_compliance_vector_scores_every_constraint_present():
    text = ("The chair design holds firm. " * 4).strip()
    record = compliance_vector([B7, Constraint("RF1", 5)], text,
                               truncated=False, finish_reason="stop",
                               token_count=42)
    assert [s.kind for s in record.scores] == ["B", "RF1"]
    assert [s.position for s in record.scores] == [1, 2]
    assert all(s.severity is not None for s in record.scores)
    assert record.word_count == 20
    assert record.empty is False
    assert record.truncated is False
    assert record.finish_reason == "stop"
    assert record.token_count == 42


def test_accidental_target_count_only_when_a_absent():
    text = "However, the design holds. However bold, it stands."
    without_a = compliance_vector([B7], text, truncated=False)
    assert without_a.accidental_s0 == 2
    with_a = compliance_vector([A5, B7], text, truncated=False)
    assert with_a.accidental_s0 is None


def test_vector_refuses_duplicate_and_empty_constraint_lists():
    with pytest.raises(InstrumentError):
        compliance_vector([], "text", truncated=False)
    with pytest.raises(InstrumentError):
        compliance_vector([B7, Constraint("B", 8)], "text", truncated=False)


def test_processing_failure_fails_closed(monkeypatch):
    from dci1v4.verifiers import statistics as stats

    def boom(_text):
        raise RuntimeError("synthetic verifier fault")

    monkeypatch.setitem(stats.FAMILY_STATISTICS, "RF1", boom)
    score = score_constraint(Constraint("RF1", 5), "text", truncated=False)
    assert score.processing_failure is True
    assert score.passed is False
    assert score.graded == 0.0
    assert score.statistic is None
    assert score.non_vacuous is False


# ------------------------------------- v3 boolean-pass compatibility seam
TRICKY_TEXTS = (
    "",
    "   \n\t ",
    "However, however; HOWEVER!",
    "how-ever howevers however2 however",
    "*Bold* markdown **bullets** — and em—dashes",
    "naïve café über ØRE straße",           # non-ASCII alphabetic
    "a b c d e f g one-letter i",
    "running, sing, bring... KING ring wing-ing",
    "comma, comma, comma, comma, comma,",
    "Zero\u200bwidth spa‍ce however",
    "ABCDEFG hijklmnop QRSTUV wxyz",
    "bob bought big bright blue balloons by bay",
    "abba lettuce puddle happen scissors",
    "day by day they say hey may play stay away",
    "a" * 30,
    "word " * 25,
    "The答案 contains 中文 and however tokens.",
    "line one:\nhowever\nline two",
)


def test_boolean_pass_matches_v3_on_every_shared_severity():
    from dci1v3.protocol import constants as v3c
    from dci1v3.verifiers.families import family_passes, focal_passes
    from dci1v3.verifiers.target import s0_count, s1_count, s2_count, s3_count
    from dci1v4.verifiers import target as v4target

    for text in TRICKY_TEXTS:
        for m in v3c.FOCAL_GRID:
            v4 = score_constraint(Constraint("B", m), text, truncated=False)
            assert v4.passed == focal_passes(text, m), (text, m)
        for family, grid in v3c.REFERENCE_FAMILIES.items():
            for q in grid:
                v4 = score_constraint(Constraint(family, q), text,
                                      truncated=False)
                assert v4.passed == family_passes(family, text, q), \
                    (text, family, q)
        assert v4target.s0_count(text) == s0_count(text), text
        assert v4target.s1_count(text) == s1_count(text), text
        assert v4target.s2_count(text) == s2_count(text), text
        wordings = ("Use the word however exactly 5 times.",)
        assert v4target.s3_count(text, wordings) == s3_count(text, wordings)
        for n in v3c.TARGET_GRID:
            v4 = score_constraint(Constraint("A", n), text, truncated=False)
            assert v4.passed == (s0_count(text) == n), (text, n)
            assert v4.statistic == s0_count(text)


# ------------------------------------------- determinism and §10.6 hashing
def test_scoring_is_deterministic():
    text = "However the b-words bring, sing, and stay: a comma, too."
    first = compliance_vector([A5, B7], text, truncated=False)
    second = compliance_vector([A5, B7], text, truncated=False)
    assert first == second


def test_instrument_hash_definition_and_stability():
    assert instrument_source_hash() == instrument_source_hash()
    digests = {}
    for name in INSTRUMENT_MODULES:
        digests[name] = hashlib.sha256(
            (V4_DIR / name).read_bytes()).hexdigest()
    expected = hashlib.sha256(
        json.dumps(digests, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()
    assert instrument_source_hash() == expected
    assert set(INSTRUMENT_MODULES) == {
        "words.py", "target.py", "statistics.py",
        "constraints.py", "compliance.py"}


def test_v3_frozen_instrument_hash_is_untouched():
    """The v4 layer must not move the frozen v3 verifier hash."""
    from dci1v3.verifiers import verifier_source_hash
    assert verifier_source_hash() == \
        "2059509dc0892a3a01928194e2c8a3431b0c07a81f33c235a0d77f1f29ad4f1b"
    assert instrument_source_hash() != verifier_source_hash()
