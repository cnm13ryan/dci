"""Amendment A1's four structural requirements, and the diagnostics it adds.

A1 requires that the grammar be arm-blind and semantically faithful, that the target
bullet-count verifier depend only on generic list segmentation, that ordering-specific
label matching happen only in the focal verifier, that the predeclared equivalent
surface forms all parse alike, and that parse-form and UNPARSEABLE rates be reported
by arm as diagnostics.

The first three are checked structurally as well as behaviourally. A behavioural test
shows the coupling is absent for the cases tried; reading the signature and the source
shows there is no channel for it at all, which is the claim section 4.2 needs.
"""
from __future__ import annotations

import inspect
import json

import pytest

from dci.v19 import diagnostics as D
from dci.v19 import verifiers as V
from dci.v19.parsing import (
    CANONICAL_LIST_POLICY as P,
)
from dci.v19.parsing import (
    EQUIVALENT_SURFACE_FORMS,
    SURFACE_FORM_RATIONALE,
    OrderingRelation,
    assert_surface_forms_cover_the_grammar,
    match_items_to_labels,
    parse_list,
)
from dci.v19.verifiers import GenerationState, Verdict

pytestmark = pytest.mark.cpu

CONTENTS = ("alfa one", "bravo two", "charlie three")


# ------------------------------------------- the predeclared equivalent surfaces
def test_the_surface_form_table_covers_every_marker_the_grammar_admits():
    assert_surface_forms_cover_the_grammar(P)


def test_every_surface_form_has_a_recorded_rationale():
    assert set(EQUIVALENT_SURFACE_FORMS) == set(SURFACE_FORM_RATIONALE)
    for name, reason in SURFACE_FORM_RATIONALE.items():
        assert reason.strip(), name


@pytest.mark.parametrize("name", sorted(EQUIVALENT_SURFACE_FORMS))
def test_every_declared_surface_form_parses_to_the_same_items(name):
    """The metamorphic property: same list, different surface, same reading."""
    reference = parse_list(EQUIVALENT_SURFACE_FORMS["hyphen_bullet"](CONTENTS), P)
    got = parse_list(EQUIVALENT_SURFACE_FORMS[name](CONTENTS), P)
    assert got.contents == reference.contents
    assert got.count == reference.count == len(CONTENTS)


@pytest.mark.parametrize("name", sorted(EQUIVALENT_SURFACE_FORMS))
@pytest.mark.parametrize("n", [1, 2, 5, 9])
def test_the_metamorphic_property_holds_at_several_lengths(name, n):
    contents = tuple(f"item{i:03d} word" for i in range(n))
    reference = parse_list(EQUIVALENT_SURFACE_FORMS["hyphen_bullet"](contents), P)
    got = parse_list(EQUIVALENT_SURFACE_FORMS[name](contents), P)
    assert got.contents == reference.contents
    assert got.count == n


@pytest.mark.parametrize("name", sorted(EQUIVALENT_SURFACE_FORMS))
def test_every_surface_form_gives_the_same_target_verdict(name):
    outcome = V.verify_exact_bullet_count(
        EQUIVALENT_SURFACE_FORMS[name](CONTENTS), n_items=len(CONTENTS), policy=P)
    assert outcome.verdict is Verdict.PASS
    assert outcome.generation_state is GenerationState.SCORABLE


@pytest.mark.parametrize("name", sorted(EQUIVALENT_SURFACE_FORMS))
def test_every_surface_form_gives_the_same_focal_verdict(name):
    labels = tuple(c.split()[0] for c in CONTENTS)
    relation = OrderingRelation(items=labels,
                               edges=tuple((labels[i], labels[i + 1])
                                           for i in range(len(labels) - 1)))
    outcome = V.verify_transitive_order(
        EQUIVALENT_SURFACE_FORMS[name](CONTENTS), relation=relation, policy=P)
    assert outcome.verdict is Verdict.PASS


# ------------------------- the target verifier never reads the ordering relation
def test_the_target_verifier_takes_no_relation_parameter():
    parameters = set(inspect.signature(V.verify_exact_bullet_count).parameters)
    assert "relation" not in parameters
    assert parameters == {"text", "n_items", "policy", "delivered_state"}


def test_the_target_verifier_source_names_no_relation_machinery():
    source = inspect.getsource(V.verify_exact_bullet_count)
    for forbidden in ("relation", "match_items_to_labels", "closure",
                      "ordering_depth"):
        assert forbidden not in source, forbidden


@pytest.mark.parametrize("edges", [
    (),
    (("alfa", "bravo"),),
    (("charlie", "alfa"), ("alfa", "bravo")),
    (("bravo", "charlie"),),
])
def test_the_target_verdict_is_identical_however_the_relation_varies(edges):
    """Whatever the focal parameter is, the count is the same measurement."""
    text = EQUIVALENT_SURFACE_FORMS["hyphen_bullet"](CONTENTS)
    labels = tuple(c.split()[0] for c in CONTENTS)
    OrderingRelation(items=labels, edges=edges)          # a valid realisation
    baseline = V.verify_exact_bullet_count(text, n_items=3, policy=P)
    again = V.verify_exact_bullet_count(text, n_items=3, policy=P)
    assert baseline.verdict is again.verdict
    assert baseline.evidence["parse"] == again.evidence["parse"]
    assert baseline.spec_hash == again.spec_hash


def test_a_malformed_list_moves_both_verdicts_only_through_the_shared_parse():
    """Section 4.2's coupling, made attributable rather than removed by fiat.

    The count and the ordering verdict both change, and the reason is visible in
    one place: the parse both of them read. That is what the amendment buys - not
    the absence of coupling, but its attribution.
    """
    labels = ("alfa", "bravo", "charlie")
    relation = OrderingRelation(items=labels,
                               edges=(("alfa", "bravo"), ("bravo", "charlie")))
    good = "- alfa\n- bravo\n- charlie"
    malformed = "alfa bravo charlie"
    assert V.verify_exact_bullet_count(good, n_items=3, policy=P).verdict is Verdict.PASS
    assert V.verify_transitive_order(good, relation=relation,
                                    policy=P).verdict is Verdict.PASS
    count = V.verify_exact_bullet_count(malformed, n_items=3, policy=P)
    order = V.verify_transitive_order(malformed, relation=relation, policy=P)
    assert count.verdict is Verdict.FAIL and order.verdict is Verdict.FAIL
    assert count.evidence["parse"]["observed_count"] == 0
    assert order.evidence["parse"]["observed_count"] == 0
    # Same parse object underneath, so the coupling is one fact and not two.
    assert count.evidence["parse"] == order.evidence["parse"]


# ---------------------------- label matching lives only in the focal verifier
def test_only_the_focal_verifier_declares_the_label_matcher():
    """Checked against the DECLARED dependency closure, not against prose.

    `Verifier.implementation` is the tuple whose hashes make up the verifier's
    implementation identity, so a verifier that started reading the label matcher
    would either appear here or ship an implementation hash that does not cover
    what it runs. There is no third option, which is what makes this a structural
    claim rather than an observation about today's source.
    """
    matching = [constraint_id
                for constraint_id, entry in V.bundle(P).items()
                if match_items_to_labels in entry.implementation]
    assert matching == ["v19:p1.focal.transitive_order"]


def test_the_target_verifier_declares_only_generic_segmentation():
    entry = V.bundle(P)["v19:p1.target.exact_bullet_count"]
    assert [f.__name__ for f in entry.implementation] == [
        "verify_exact_bullet_count", "parse_list", "normalise"]
    assert match_items_to_labels not in entry.implementation


def test_label_matching_is_reachable_but_not_used_by_the_other_five():
    parsed = parse_list("- alfa\n- bravo", P)
    relation = OrderingRelation(items=("alfa", "bravo"), edges=(("alfa", "bravo"),))
    assert match_items_to_labels(parsed, relation, P)["sequence"] == ["alfa", "bravo"]


# -------------------------------------------------------------- arm-blindness
def test_no_verifier_accepts_an_arm_a_role_or_a_composition():
    for constraint_id, entry in V.bundle(P).items():
        parameters = set(inspect.signature(entry.implementation[0]).parameters)
        leaked = parameters & {"arm", "role", "composition", "composition_id",
                              "pair", "pair_id", "reference", "background"}
        assert not leaked, (constraint_id, leaked)


def test_no_function_a_verifier_declares_mentions_an_arm():
    """Over the whole declared closure, not just the entry point."""
    for constraint_id, entry in V.bundle(P).items():
        for function in entry.implementation:
            source = inspect.getsource(function)
            for forbidden in ("arm", "A+B+S", "A+R_j"):
                assert forbidden not in source, (constraint_id, function.__name__,
                                                 forbidden)


def test_a_verifier_measures_the_same_text_identically_whatever_produced_it():
    """Arm-invariance behaviourally: the verifier has no access to provenance."""
    text = "- alfa one\n- bravo two\n- charlie three"
    outcomes = [V.verify_exact_bullet_count(text, n_items=3, policy=P)
                for _ in range(3)]
    first = outcomes[0]
    for other in outcomes[1:]:
        assert other.verdict is first.verdict
        assert other.spec_hash == first.spec_hash
        assert other.evidence == first.evidence
        assert other.reason == first.reason


# ------------------------------------------------------- UNPARSEABLE stays a state
def test_the_primary_outcome_space_is_still_exactly_pass_and_fail():
    D.assert_outcome_space_is_binary()
    assert [v.value for v in Verdict] == ["PASS", "FAIL"]


def test_unparseable_is_a_generation_state_and_not_a_verdict():
    assert "UNPARSEABLE" in {s.value for s in GenerationState}
    assert "UNPARSEABLE" not in {v.value for v in Verdict}


def test_an_unparseable_answer_carries_no_verdict_of_its_own_kind():
    outcome = V.verify_exact_bullet_count("just prose, no list", n_items=3, policy=P)
    assert outcome.generation_state is GenerationState.UNPARSEABLE
    # Orthogonal: it is still scored, and the score is a genuine FAIL of the count.
    assert outcome.verdict is Verdict.FAIL


# ------------------------------------------------------------- the parse form
@pytest.mark.parametrize("text,expected", [
    ("- alfa\n- bravo", "bullet"),
    ("1. alfa\n2. bravo", "numbered"),
    ("- alfa\n* bravo", "bullet/mixed"),
    ("- alfa\n  - bravo", "bullet/nested"),
    ("- alfa\n  continued", "bullet/wrapped"),
    ("prose first\n- alfa", "bullet/prose"),
    ("no list at all", "no_items"),
])
def test_the_parse_form_labels_the_structural_shape(text, expected):
    assert D.parse_form(parse_list(text, P)) == expected


def test_the_parse_form_reads_a_described_parse_as_well_as_a_live_one():
    parsed = parse_list("- alfa\n- bravo", P)
    assert D.parse_form(parsed) == D.parse_form(parsed.describe())


def test_the_parse_form_detail_keeps_the_facts_separate():
    detail = D.parse_form_detail(parse_list("- alfa\n  - bravo\n1. charlie", P))
    assert detail["mixed_markers"] is True
    assert detail["nested"] is True
    assert sorted(detail["marker_kinds"]) == ["bullet", "numbered"]
    assert detail["observed_count"] == 3


def test_an_excluded_item_is_named_in_the_form():
    form = D.parse_form(parse_list("- alfa\n- \n- bravo", P))
    assert "excl:empty_item" in form


def test_a_non_parse_is_refused_rather_than_guessed():
    with pytest.raises(D.DiagnosticError, match="ParsedList"):
        D.parse_form_detail("- alfa")


# -------------------------------------------------------------- rates by arm
def _outcome(text, n_items=3):
    return V.verify_exact_bullet_count(text, n_items=n_items, policy=P)


def test_rates_are_reported_per_arm_with_their_denominators():
    observations = [
        ("B", _outcome("- a x\n- b y\n- c z")),
        ("B", _outcome("1. a x\n2. b y\n3. c z")),
        ("R1", _outcome("- a x\n- b y\n- c z")),
        ("R1", _outcome("no list here")),
    ]
    report = D.rates_by_arm(observations)
    rows = {row["arm"]: row for row in report["arms"]}
    assert set(rows) == {"B", "R1"}
    assert rows["B"]["n"] == rows["R1"]["n"] == 2
    assert rows["B"]["unparseable_rate"] == 0.0
    assert rows["R1"]["unparseable_rate"] == 0.5
    assert report["n_observations"] == 4


def test_the_report_states_that_it_is_a_diagnostic():
    report = D.rates_by_arm([("B", _outcome("- a x\n- b y\n- c z"))])
    assert report["kind"] == "diagnostic"
    assert "not a third primary outcome" in report["note"]
    assert "11.8" in report["citation"]


def test_parse_form_rates_are_reported_by_arm():
    observations = [("B", _outcome("- a x\n- b y\n- c z")),
                    ("R1", _outcome("1. a x\n2. b y\n3. c z"))]
    rows = {row["arm"]: row for row in D.rates_by_arm(observations)["arms"]}
    assert rows["B"]["parse_form_rates"] == {"bullet": 1.0}
    assert rows["R1"]["parse_form_rates"] == {"numbered": 1.0}


def test_an_arm_with_a_different_reading_shows_up_as_a_spread():
    observations = [("B", _outcome("- a x\n- b y\n- c z")),
                    ("B", _outcome("- a x\n- b y\n- c z")),
                    ("R1", _outcome("no list here")),
                    ("R1", _outcome("- a x\n- b y\n- c z"))]
    table = D.parse_form_disagreement(D.rates_by_arm(observations))
    assert table["unparseable_rate_by_arm"] == {"B": 0.0, "R1": 0.5}
    assert table["unparseable_rate_spread"] == 0.5
    assert "not a test" in table["note"]


def test_the_disagreement_table_names_forms_seen_in_some_arms_only():
    observations = [("B", _outcome("- a x\n- b y\n- c z")),
                    ("R1", _outcome("1. a x\n2. b y\n3. c z"))]
    table = D.parse_form_disagreement(D.rates_by_arm(observations))
    assert sorted(table["forms_seen_in_some_arms_only"]) == ["bullet", "numbered"]


def test_an_empty_report_is_reported_rather_than_divided_by_zero():
    report = D.rates_by_arm([])
    assert report["arms"] == [] and report["n_observations"] == 0
    assert D.parse_form_disagreement(report)["unparseable_rate_spread"] is None


@pytest.mark.parametrize("bad", [
    "not an observation", 42, ("B",), ("B", "not an outcome"), (None, None)])
def test_a_malformed_observation_is_refused(bad):
    with pytest.raises(D.DiagnosticError):
        D.rates_by_arm([bad])


def test_a_mapping_observation_is_accepted_too():
    report = D.rates_by_arm(
        [{"arm": "B", "outcome": _outcome("- a x\n- b y\n- c z")}])
    assert report["arms"][0]["arm"] == "B"


def test_the_report_is_serialisable_because_it_is_archived():
    report = D.rates_by_arm([("B", _outcome("- a x\n- b y\n- c z")),
                             ("R1", _outcome("prose"))])
    assert json.loads(json.dumps(report)) == report
