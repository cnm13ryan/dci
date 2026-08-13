"""Tests for the Round 5 additions, on the same principle as the Round 1 tests.

Every check here guards a way a generalization run could produce plausible
numbers that mean something other than what the report would claim: an arm that
is logically impossible rather than merely interfering, a target whose count the
analysis reads wrongly, a sensitivity column that silently equals the primary
one, or an exploratory constraint that shadows a registry one.
"""
from __future__ import annotations

import pytest

from dci_exploratory import design, extensions, harvest, mechanism, runner

TASKS = [
    {"task_id": "T1", "split": "pilot", "topic": "Explain how a hinge lets a door swing."},
    {"task_id": "T2", "split": "pilot", "topic": "Explain how a funnel speeds up pouring."},
]


@pytest.fixture(scope="module")
def registered():
    return extensions.register()


# ------------------------------------------------------------- registration
def test_registration_is_idempotent(registered):
    assert extensions.register() is registered


def test_no_exploratory_id_shadows_a_registry_id(registered):
    S = harvest.load()
    for cid in registered["constraints"]:
        assert cid.startswith("X_"), cid
        assert S.CONSTRAINTS[cid].origin == "exploratory"


def test_registering_does_not_change_the_registry_provenance_hash(registered):
    """The harvested definitions must still hash to what earlier runs recorded.

    If this fails, every previous run directory has stopped describing the
    definitions it was made under.
    """
    provenance = harvest.provenance()
    # The value recorded in runs/stageB_20260810T183206Z/config.json, before any
    # exploratory constraint existed.
    assert provenance["instructions_sha256"] == (
        "55bc1e7603298425c512a8e26e662c6f2addb9112a9bf73ca77849473da07ad7")
    assert provenance["n_constraints"] == 45
    S = harvest.load()
    assert provenance["n_constraints"] == sum(
        1 for c in S.CONSTRAINTS.values() if c.origin != "exploratory")


def test_the_mark_family_differs_only_in_the_mark(registered):
    # Ranges over `_FACTORIAL_MARKS`, which names the per-sentence family, rather
    # than over `MARK_CHARS`, which is also a plain character lookup and now
    # carries the two non-boundary controls so that `splice_count` can be
    # evaluated on them. The assertion itself is unchanged.
    wordings = {m: registered["constraints"][f"X_{m.upper()}_EACH"]["wordings"][0]
                for m in extensions._FACTORIAL_MARKS}
    stripped = {w.replace(m, "MARK") for m, w in wordings.items()}
    assert len(stripped) == 1, f"wordings differ by more than the mark: {wordings}"


def test_the_n_variant_targets_use_the_registry_wording(registered):
    for n in (2, 3, 5, 6):
        entry = registered["constraints"][f"X_A{n}"]
        assert entry["wording_origin"].startswith("registry")
        assert entry["wordings"][0] == f"Write exactly {n} sentences."


@pytest.mark.parametrize("cid,good,bad", [
    ("X_SEMICOLON_EACH", "Rain falls; rivers rise. Wind blows; leaves turn.",
     "Rain falls. Rivers rise."),
    ("X_COMMA_EACH", "Rain falls, and rivers rise. Wind blows, and leaves turn.",
     "Rain falls. Rivers rise."),
    ("X_SEMI_TOTAL4", "a; b; c; d; e.", "a; b."),
    ("X_PARA4", "one\n\ntwo\n\nthree\n\nfour", "one\n\ntwo"),
])
def test_each_new_verifier_separates_conforming_from_violating(registered, cid, good, bad):
    S = harvest.load()
    assert S.verify(good, cid).binary_pass == 1
    assert S.verify(bad, cid).binary_pass == 0


def test_the_dash_rule_accepts_every_dash_a_model_might_write(registered):
    S = harvest.load()
    for dash in ("—", "–", "--"):
        text = f"Rain falls {dash} rivers rise. Wind blows {dash} leaves turn."
        assert S.verify(text, "X_DASH_EACH").binary_pass == 1, dash


# -------------------------------------------------------- the general screen
def test_the_registry_screen_still_misses_the_colon_case(registered):
    """The premise of `punctuation_conflicts`, asserted rather than assumed.

    If the registry's own screen is ever generalised, this test fails and the
    exploratory screen becomes redundant — which is the outcome to want, and
    which must be noticed rather than left as dead code.
    """
    S = harvest.load()
    from dci.constraints.satisfiability import pair_verdict
    verdict = pair_verdict(S.CONSTRAINTS["U_FMT_COLON1"], S.CONSTRAINTS["X_COLON_EACH"])
    assert getattr(verdict, "status", verdict)[0] == "ok"


def test_the_general_screen_catches_what_the_registry_screen_misses(registered):
    clashes = extensions.punctuation_conflicts(
        ["A", "U_FMT_COLON1", "X_COLON_EACH"], n_sentences=4)
    assert len(clashes) == 1
    assert clashes[0]["kind"] == "hard"


def test_the_general_screen_catches_a_flat_prohibition(registered):
    clashes = extensions.punctuation_conflicts(
        ["U_FMT_NOCOMMA", "X_COMMA_EACH"], n_sentences=None)
    assert len(clashes) == 1


def test_the_general_screen_allows_a_budget_that_is_large_enough(registered):
    assert extensions.punctuation_conflicts(
        ["X_A2", "U_FMT_SEMI2", "X_SEMICOLON_EACH"], n_sentences=2) == []


def test_custom_selection_refuses_an_impossible_slice(registered):
    with pytest.raises(ValueError, match="punctuation"):
        design.custom_selection(
            target="A", focal="X_COLON_EACH", references=["C_L3"], load=5,
            background=["U_FMT_COLON1", "U_LEX_FORBID3", "U_NUM_MAXINT"])


# ------------------------------------------------------- custom selection
def test_custom_selection_refuses_the_target_as_an_arm(registered):
    with pytest.raises(ValueError, match="cannot also be an arm"):
        design.custom_selection(target="A", focal="B", references=["A"])


def test_custom_selection_says_in_its_rule_that_it_is_not_the_admitted_panel(registered):
    selection = design.custom_selection("A", "X_SEMICOLON_EACH", ["C_L3"], load=5)
    assert "NOT the admitted" in selection.rule


def test_a_custom_design_is_still_matched(registered):
    selection = design.custom_selection(
        "X_A6", "X_SEMICOLON_EACH", ["C_L3", "B"], load=5)
    rows = design.build_design(selection, TASKS, replicates=2, base_seed=7,
                               stage="test")
    design.assert_matched(rows, selection)          # raises if anything is off
    contrast = [r for r in rows if r.condition in ("focal", "reference")]
    assert {r.measured for r in contrast} == {"X_A6"}


# ------------------------------------------------------------- the analysis
def test_the_legacy_segmenter_reproduces_the_defect():
    """It must still get the abbreviation case wrong, or it is not the defect.

    A title abbreviation, not `a.m.`: the legacy rule splits only where a full
    stop is followed by whitespace, and `a.m.` before a capitalised word is a
    boundary under BOTH rules, so it would not separate them.
    """
    text = "Dr. Ellis spoke to Mr. Hall about the survey."
    from dci.verifiers.rules import split_sentences
    assert len(split_sentences(text)) == 1
    assert len(mechanism.legacy_split_sentences(text)) == 3


def test_the_sensitivity_column_is_not_a_copy_of_the_primary():
    corrupted = "Dr. Ellis spoke. The room fell quiet."
    assert (len(mechanism.legacy_split_sentences(corrupted))
            != len(__import__("dci.verifiers.rules", fromlist=["x"])
                   .split_sentences(corrupted)))


def test_paragraphs_split_on_blank_lines_not_single_newlines():
    assert len(extensions.split_paragraphs("one\ntwo\n\nthree")) == 2
    assert len(extensions.split_paragraphs("one\ntwo\nthree")) == 1


def test_row_features_are_computable_without_any_verdict():
    features = mechanism.row_features("Rain falls; rivers rise — slowly.\nNext line.")
    assert features["n_semicolons"] == 1
    assert features["n_dashes"] == 1
    assert features["n_newlines"] == 1
    assert features["n_sentences"] >= 1


def test_severe_collapse_is_one_unit_at_every_target_count():
    """The threshold must not move with N, or it is not one variable."""
    import inspect
    source = inspect.getsource(mechanism.load)
    assert 'frame["severe_collapse"] = (observed == 1)' in source


# ---------------------------------------------------------------- scaffolds
def test_the_sham_is_length_matched_to_the_scaffold_it_controls():
    strong = runner.SCAFFOLDS["one_sentence_per_line"]
    sham = runner.SCAFFOLDS["sham_plain_style"]
    assert abs(len(strong) - len(sham)) <= 2
    assert strong.split()[:3] == sham.split()[:3] == ["Write", "each", "sentence"]


def test_the_sham_says_nothing_about_boundaries():
    sham = runner.SCAFFOLDS["sham_plain_style"].lower()
    for word in ("line", "full stop", "period", "sentence on", "separate", "break"):
        assert word not in sham


def test_every_scaffold_declares_what_obeying_it_would_mean():
    assert set(runner.SCAFFOLDS) == set(runner.SCAFFOLD_COMPLIANCE)


def test_the_scaffold_never_enters_the_numbered_instruction_list():
    selection = design.custom_selection("A", "S_SEMICOLON", ["C_L3"], load=5)
    rows = design.build_design(selection, TASKS, replicates=1, base_seed=7,
                               stage="test",
                               scaffolds=("", "one_sentence_per_line"))
    by_scaffold = {}
    for row in rows:
        by_scaffold.setdefault(row.scaffold, set()).add(row.user_prompt)
    assert by_scaffold[""] == by_scaffold["one_sentence_per_line"], (
        "the scaffold changed the user prompt; it must live in the system "
        "message only, or the load is no longer matched")


def test_collapse_signature_separates_substitution_from_a_run_on():
    """The two routes must be distinguishable by the columns, not by eye.

    Built from synthetic rows so the test asserts the STATISTIC's behaviour
    rather than re-asserting a result.
    """
    import pandas as pd
    rows = []
    for i in range(4):
        rows.append({"condition": "reference", "arm": "SUBSTITUTE", "order": "o_Q",
                     "severe_collapse": True, "n_semicolons": 3, "n_colons": 0,
                     "n_dashes": 0, "n_commas": 1, "n_words": 45, "n_periods": 1,
                     "arm_scorable": True, "arm_binary_pass": 1})
        rows.append({"condition": "reference", "arm": "RUNON", "order": "o_Q",
                     "severe_collapse": True, "n_semicolons": 0, "n_colons": 0,
                     "n_dashes": 0, "n_commas": 9, "n_words": 150, "n_periods": 1,
                     "arm_scorable": False, "arm_binary_pass": None})
    frame = pd.DataFrame(rows)
    frame.attrs["n_target"] = 4
    table = mechanism.collapse_signature(frame).set_index("arm")
    assert table.loc["SUBSTITUTE", "marks_per_lost_boundary"] == pytest.approx(1.0)
    assert table.loc["RUNON", "marks_per_lost_boundary"] == pytest.approx(0.0)
    assert table.loc["RUNON", "commas_per_lost_boundary"] > \
        table.loc["SUBSTITUTE", "commas_per_lost_boundary"]
    assert table.loc["SUBSTITUTE", "arm_compliance_when_collapsed"] == 1.0
    # An arm whose own rule cannot be scored at one sentence must report that,
    # not a compliance number invented from an empty set.
    assert pd.isna(table.loc["RUNON", "arm_compliance_when_collapsed"])
    assert table.loc["RUNON", "n_arm_unscorable"] == 4
