"""The contract between the two layers that segment sentences.

WHY THIS MODULE EXISTS
----------------------
`v_exact_sentence_count` decides the primary outcome F_A, and two layers compute
its segmentation: `dci.verifiers.rules` (the v15.1 implementation, certified
against 63 adversarial fixtures, a blinded human audit and a mutation bank) and
`dci.v19.text` (the frozen v19 text policy). The v19 layer re-declared the
boundary regex and dropped the abbreviation guard, so it silently reinstated the
sentence-count over-count that the Round 4 repair had already removed once.

The reason that survived is visible in the test suite: 39 tests across
`test_sentence_boundary_abbreviations`, `test_sentence_boundary_properties` and
`test_verifier_opening_punctuation` pin the semantics thoroughly - and every one
of them calls `rules.split_sentences`. The contract was stated once, on one side.

So this module states it at the SEAM instead. It imports the existing case banks
rather than restating them, and runs them through both layers.

THE CONTRACT
------------
1. **Boundary placement is identical.** Both layers decide where a sentence ends
   using `rules.SENTENCE_BOUNDARY` and `rules.ends_sentence`. There is one
   implementation of that decision and both call it.
2. **Segment survival differs, deliberately and only there.** The inherited layer
   keeps a segment only if it contains `[A-Za-z0-9]`; v19 keeps it if it contains
   a Unicode word token. So non-Latin text is zero segments inherited and
   ordinary text in v19. That is amendment A2's `unicode-sentence-survival`
   correction, and it is the ONLY class of divergence permitted here.
3. **The guard is a declared, hashed policy field**, not an implementation
   detail, so dropping it changes the specification hash instead of nothing.
"""
from __future__ import annotations

import dataclasses
import re
import sys
from pathlib import Path

import pytest

from dci.v19 import text as textlib
from dci.v19 import verifiers as V
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import sentences as v19_sentences
from dci.verifiers import rules

# `tests/unit` is not a package; pytest puts it on sys.path, and the banks are
# imported rather than restated so a case added there is checked on both layers.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_sentence_boundary_abbreviations as banks

pytestmark = pytest.mark.cpu

TP = P.text

#: Every case bank the certified boundary semantics are stated in. Imported, not
#: copied: a case added there must hold on both layers without anyone editing
#: this file.
CASE_BANKS = ("ABBREVIATION_CASES", "TITLE_CASES", "INITIAL_CASES",
              "NUMERIC_CASES", "QUOTE_CASES", "ELLIPSIS_CASES",
              "STRUCTURAL_CASES", "UNICODE_CASES", "CLOSER_CASES")


def all_cases() -> list[tuple[str, int, str]]:
    found: list[tuple[str, int, str]] = []
    for name in CASE_BANKS:
        found.extend(getattr(banks, name))
    return found


def _ids(case):
    return f"{case[2]}"


# ============================================================ 1. the seam
@pytest.mark.parametrize("case", all_cases(), ids=_ids)
def test_both_layers_agree_on_the_certified_boundary_bank(case):
    """The property that regressed, asserted on both sides of the seam."""
    text, expected, label = case
    inherited = rules.split_sentences(text)
    v19 = v19_sentences(text, P)
    assert len(inherited) == expected, f"inherited drifted from the bank: {label}"
    assert len(v19) == expected, (
        f"v19 disagrees with the certified segmentation: {label} — "
        f"inherited {len(inherited)}, v19 {len(v19)}")


def test_every_bank_is_reached():
    """A bank renamed or removed upstream must not silently stop being checked."""
    missing = [name for name in CASE_BANKS if not hasattr(banks, name)]
    assert not missing, f"case banks absent from the boundary module: {missing}"
    assert len(all_cases()) >= 45


# ================================================ 2. the permitted divergence
#: The only texts on which the two layers may differ, and why. Both are the
#: enumerated `unicode-sentence-survival` correction in the Stage 2 audit table.
SURVIVAL_ONLY_DIVERGENCES = (
    ("- ЖЖЖ\n- ЩЩЩ", 0, 2),
    ("日本語です。中文です。", 0, 1),
)


@pytest.mark.parametrize("text,inherited_n,v19_n", SURVIVAL_ONLY_DIVERGENCES)
def test_the_permitted_divergence_is_survival_not_boundary_placement(
        text, inherited_n, v19_n):
    """Where the layers differ, they differ about what SURVIVES, not where a
    sentence ends. The inherited filter is `[A-Za-z0-9]`, so a non-Latin segment
    is dropped entirely; v19 keeps it because a Unicode word token is a word."""
    assert len(rules.split_sentences(text)) == inherited_n
    assert len(v19_sentences(text, P)) == v19_n
    # It is a survival difference: v19 drops nothing, so its output is non-empty
    # while the inherited output is empty. No boundary is placed differently.
    assert rules.split_sentences(text) == []


def test_no_unenumerated_divergence_exists_over_the_banks_and_the_audit_texts():
    """The complement of the table, asserted in aggregate.

    Any new disagreement between the layers has to arrive here as a deliberate,
    named correction — which is exactly the discipline section 11.3 requires of
    the differential audit, applied to segmentation rather than to verdicts.
    """
    declared = {text for text, _, _ in SURVIVAL_ONLY_DIVERGENCES}
    unexplained = []
    for text, _expected, label in all_cases():
        if text in declared:
            continue
        if len(rules.split_sentences(text)) != len(v19_sentences(text, P)):
            unexplained.append(label)
    assert not unexplained, f"undeclared layer divergences: {unexplained}"


# ============================================== 3. the shared predicate
@pytest.mark.parametrize("left,right,ends,why", [
    ("Stop!", "Next one.", True, "an exclamation is never ambiguous"),
    ("Really?", "Next one.", True, "nor is a question mark"),
    ("Dr.", "Smith went home.", False, "a title is followed by a name"),
    ("Mr.", "Smith went home.", False, "likewise"),
    ("at 6 a.m.", "when others sleep.", False,
     "a medial abbreviation before a lower-case word continues"),
    ("at 6 a.m.", "Customers arrive.", True,
     "the same abbreviation before a capital is a boundary"),
    ("It ended at 6 p.m.", '"Tomorrow begins early."', True,
     "the capital test looks THROUGH opening punctuation"),
    ("It ended at 6 p.m.", "**Tomorrow begins early.**", True,
     "including Markdown emphasis, which models emit freely"),
    ("J.", "R. Smith went home.", False,
     "a single CAPITAL before a full stop is an initial"),
    ("weekday.", "The next one began.", True, "an ordinary word ends a sentence"),
])
def test_the_shared_boundary_predicate(left, right, ends, why):
    """`rules.ends_sentence` is the one decision both layers call."""
    assert rules.ends_sentence(left, right) is ends, why


def test_v19_calls_the_shared_predicate_rather_than_its_own_copy():
    """Guards against the exact re-drift this repair fixed.

    A source check, because behavioural equality can be reached by two
    implementations that agree today and diverge at the next repair — which is
    what happened. The v19 module must not carry its own boundary regex or its
    own abbreviation tables.
    """
    source = Path(textlib.__file__).read_text()
    # Three things are delegated, not re-typed: the pattern, the split loop, and
    # the ambiguous-terminator decision inside it.
    assert "rules.SENTENCE_BOUNDARY.pattern" in source, (
        "v19 no longer takes the boundary pattern from the certified module")
    assert "rules.split_line(" in source, (
        "v19 no longer delegates the split loop to the certified module")
    for copied in ("TITLE_ABBREVIATIONS", "MEDIAL_ABBREVIATIONS",
                   "TRAILING_ABBREVIATION", "OPENING_PUNCTUATION"):
        assert f"{copied} =" not in source, (
            f"v19 has re-declared {copied}; the tables must have one home")
    # No literal boundary regex: the pattern is taken, never typed.
    assert not re.search(r"""r['"]\(\?<=\[\.!\?\]\)""", source), (
        "v19 carries a literal sentence-boundary regex again")
    # And no second copy of the boundary-acceptance loop.
    assert "def _split_line" not in source, (
        "v19 has grown its own split loop again; `rules.split_line` is the one")


def test_the_certified_module_is_where_the_split_loop_lives():
    """Both layers reach the same loop, and it honours the guard flag."""
    assert callable(rules.split_line)
    line = "Mr. Smith went home. He stayed."
    assert len(rules.split_line(line)) == 2
    assert len(rules.split_line(line, guarded=False)) == 3
    # v19's own pattern object drives the same loop.
    assert rules.split_line(line, re.compile(TP.sentence_boundary)) == \
        rules.split_line(line)


# ================================================ 4. structural invariants
GUARDED_SAMPLE = [
    "Mr. Smith went to Washington. He stayed.",
    "Sales spike at 6 a.m. when others sleep. Then it falls.",
    "A. B. C. D. E.",
    "One. Two. Three. Four.",
    "**Bold.** Next one.",
    "(Aside.) Next one.",
    "No terminator at all",
    "Ends with one.",
    "",
    "   ",
]


@pytest.mark.parametrize("text", GUARDED_SAMPLE)
def test_the_guard_can_only_remove_boundaries_never_add_them(text):
    """The guard is a filter over candidate boundaries, so guarded segmentation
    is never finer than the raw regex split. If this ever fails the guard has
    stopped being a predicate and started being a segmenter of its own."""
    unguarded = dataclasses.replace(
        TP, sentence_abbreviation_guard=textlib.NO_ABBREVIATION_GUARD)
    assert (len(textlib.split_sentences(text, TP))
            <= len(textlib.split_sentences(text, unguarded))), text


@pytest.mark.parametrize("text", GUARDED_SAMPLE)
def test_segmentation_is_idempotent_over_rejoined_segments(text):
    """Re-segmenting a segment yields that segment: no boundary hides inside one."""
    for segment in v19_sentences(text, P):
        assert len(v19_sentences(segment, P)) == 1, segment


@pytest.mark.parametrize("text", ["", "   ", "\n\n", "?!?", "42"])
def test_degenerate_inputs_agree_across_layers(text):
    inherited, v19 = rules.split_sentences(text), v19_sentences(text, P)
    assert (len(inherited) == 0) == (len(v19) == 0), text


# ============================================ 5. the guard is declared, not hidden
def test_the_canonical_policy_declares_the_guard():
    assert TP.sentence_abbreviation_guard == textlib.ABBREVIATION_GUARD
    assert TP.state()["sentence_abbreviation_guard"] == textlib.ABBREVIATION_GUARD


def test_dropping_the_guard_moves_the_specification_hash():
    """A future policy may legitimately want the raw split. It cannot get one
    silently: the choice is in `state()`, so it is in the Pair 3 spec hash."""
    unguarded = dataclasses.replace(
        TP, sentence_abbreviation_guard=textlib.NO_ABBREVIATION_GUARD)
    assert unguarded.policy_hash != TP.policy_hash
    assert len(textlib.split_sentences("Mr. Smith went home. He stayed.",
                                       unguarded)) == 3


def test_an_undeclared_guard_is_refused():
    with pytest.raises(textlib.TextPolicyError, match="sentence_abbreviation_guard|not one of"):
        dataclasses.replace(TP, sentence_abbreviation_guard="hand-rolled")


def test_the_delegated_guard_is_inside_the_frozen_closure():
    """Delegation must not move executed behaviour outside the hash.

    Found in review of the repair: once Pair 3 delegates boundary decisions to
    `rules`, a change to the abbreviation TABLES moves sentence counts — and so
    F_A — while the guard's name, every v19 helper's source, and every hash
    derived from them stay identical. The freeze would then certify an identity
    the measurement no longer has.

    Both halves are covered: the tables travel in the spec hash via
    `abbreviation_guard_state`, and the delegated functions' source travels in
    the implementation hash via the Pair 3 implementation tuples.
    """
    built = V.bundle(P)
    for constraint_id in ("v19:p3.target.exact_sentence_count",
                          "v19:p3.focal.increasing_lengths"):
        closure = {fn.__name__ for fn in built[constraint_id].implementation}
        assert {"split_line", "ends_sentence", "_opens_with_capital"} <= closure, (
            f"{constraint_id} executes the delegated guard but does not hash it")

    guard = built["v19:p3.target.exact_sentence_count"].spec.segmentation[
        "abbreviation_guard"]
    assert guard["guard"] == textlib.ABBREVIATION_GUARD
    assert sorted(rules.TITLE_ABBREVIATIONS) == guard["title_abbreviations"]
    assert sorted(rules.MEDIAL_ABBREVIATIONS) == guard["medial_abbreviations"]
    assert guard["boundary_pattern"] == rules.SENTENCE_BOUNDARY.pattern
    assert guard["trailing_abbreviation_pattern"] == rules.TRAILING_ABBREVIATION.pattern
    assert guard["trailing_abbreviation_flags"] == rules.TRAILING_ABBREVIATION.flags


def test_changing_an_abbreviation_table_moves_the_frozen_identity(monkeypatch):
    """The property above, exercised rather than described.

    `Gov.` is not a title abbreviation today, so adding it changes where a
    sentence ends. If that can happen without the bundle hash moving, the freeze
    is not freezing the measurement.
    """
    text = "I met Gov. Adams yesterday. He agreed."
    before_count = len(v19_sentences(text, P))
    before_hash = V.bundle_hash(P)

    monkeypatch.setattr(rules, "TITLE_ABBREVIATIONS",
                        frozenset(rules.TITLE_ABBREVIATIONS | {"gov"}))

    assert len(v19_sentences(text, P)) != before_count, "fixture stopped biting"
    assert V.bundle_hash(P) != before_hash, (
        "an abbreviation-table change moved F_A without moving the frozen "
        "bundle identity")


def test_changing_the_abbreviation_regex_flags_moves_the_frozen_identity(monkeypatch):
    """A flags-only change to the delegated regex is a measurement change too.

    Found in review: the guard state recorded `TRAILING_ABBREVIATION.pattern`
    but not its flags. Recompiled with `re.ASCII`, `[^\\W\\d_]` no longer
    matches `É`, so the trailing token of "ÉA." shrinks to the capital "A", is
    read as an initial, and the boundary after it disappears, with the pattern
    string, and so every hash, unchanged.
    """
    text = "The label reads ÉA. Next stop is Paris."
    before_count = len(v19_sentences(text, P))
    before_hash = V.bundle_hash(P)

    monkeypatch.setattr(rules, "TRAILING_ABBREVIATION",
                        re.compile(rules.TRAILING_ABBREVIATION.pattern, re.ASCII))

    assert len(v19_sentences(text, P)) != before_count, "fixture stopped biting"
    assert V.bundle_hash(P) != before_hash, (
        "a regex-flags change moved F_A without moving the frozen bundle identity")


def test_the_guard_name_resolves_to_the_function_it_names():
    """The field is a provenance string; it has to point at something real."""
    module, _, attribute = textlib.ABBREVIATION_GUARD.rpartition(".")
    assert module == "dci.verifiers.rules"
    assert getattr(rules, attribute) is rules.ends_sentence
