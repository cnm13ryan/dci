"""The Tier-1 audit apparatus: manifest, blinding, ingestion, and the A3 gate.

Every case below is a TEST FIXTURE. None is audit material, none is a reviewer
judgement, and none reaches the registry. The real cases are `pool.{pair}.audit`,
a declared scientific split whose content is PENDING_CONTENT and is authored by
people under section 11.1's versioned content procedure; the real judgements come
from real reviewers. What is tested here is the apparatus that will carry them.

The fixtures deliberately use obviously synthetic text so that a reader who finds
one of them in an artifact knows immediately that something has gone wrong.
"""
from __future__ import annotations

import json

import pytest

from dci.provenance.hashes import sha
from dci.v19 import pairs
from dci.v19 import tier1_audit as T
from dci.v19.registry import declared_table
from dci.v19.reliability import AMENDED_TIER1_DESIGN as DESIGN

pytestmark = pytest.mark.cpu

UNITS = tuple(rule.constraint_id for rule in pairs.rules())
MATERIAL = T.REQUIRED_MATERIAL


def a_case(unit, index, truth_class, material=("boundary_cases",)):
    return T.AuditCase(
        case_id=f"fixture/{unit}/{truth_class.value}/{index:03d}",
        unit=unit,
        # Neither the unit nor the intended class may appear in the text: it goes
        # into the packet verbatim as `response`, and assert_blinded rightly
        # refuses a response that tells the reviewer what to conclude. An earlier
        # version of this fixture did leak the class, and the blinding check
        # caught it. Hence a digest of the pair rather than the pair itself.
        #
        # `sha`, NOT the builtin `hash`. The builtin is salted per interpreter,
        # so `abs(hash(...)) % 997` gave twelve values from a 997-space that
        # changed every run: about one pytest process in thirty drew a pair of
        # units onto the same discriminator, every one of the 100 indices under
        # them collided, and `assert_no_case_serves_two_units` -- correctly --
        # refused the manifest. A fixture may not be a lottery.
        text=f"SYNTHETIC TEST FIXTURE "
             f"{sha(['v19/tier1-audit-fixture', unit, truth_class.value])[:12]}"
             f" item {index}",
        parameters={"n_items": 3},
        intended_class=truth_class,
        material=tuple(material),
        source_pool="fixture (NOT pool.p1.audit)",
        authored_by="the test suite",
        provenance="a fixture for the audit apparatus; not audit material")


def a_manifest(per_class=None, spanning=True):
    """A structurally complete manifest built entirely from fixtures."""
    per_class = T.CANDIDATES_PER_CLASS if per_class is None else per_class
    cases = []
    for unit in UNITS:
        for truth_class in T.TruthClass:
            for i in range(per_class):
                material = ((MATERIAL[i % len(MATERIAL)],) if spanning
                            else ("boundary_cases",))
                cases.append(a_case(unit, i, truth_class, material))
    return T.AuditManifest(cases=tuple(cases))


PANEL = None   # set below, after T is imported


def a_panel():
    return T.ReviewerPanel(reviewers=("reviewer-a", "reviewer-b"),
                           adjudicator="reviewer-c")


def a_protocol_table():
    """The declared table with the FROZEN protocol applied, for ingestion tests."""
    return declared_table().freeze("verifiers.tier1_audit_protocol",
                                   dict(T.PROTOCOL),
                                   by="the frozen protocol, for an apparatus test")


# ------------------------------------------------------- the fixture itself
def test_the_fixture_gives_every_unit_a_distinct_discriminator():
    """Two units sharing a discriminator make identical case text under both."""
    texts = {}
    for unit in UNITS:
        for truth_class in T.TruthClass:
            texts.setdefault(a_case(unit, 0, truth_class).text, set()).add(unit)
    shared = {text: units for text, units in texts.items() if len(units) > 1}
    assert not shared, f"one fixture text serves several units: {shared}"


def test_the_fixture_is_identical_under_a_different_interpreter_hash_seed():
    """The suite must not depend on PYTHONHASHSEED.

    Run in a subprocess because the salt is fixed at interpreter start: it
    cannot be varied from inside this one. Two seeds that previously disagreed
    are used, so the regression is reproduced rather than approximated.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    program = (
        f"import sys; sys.path.insert(0, {str(Path(__file__).parent)!r}); "
        "from test_v19_tier1_audit import a_manifest; "
        "print(a_manifest(per_class=2).manifest_hash)")
    digests = set()
    for seed in ("72", "73"):
        done = subprocess.run([sys.executable, "-c", program],
                              env={**os.environ, "PYTHONHASHSEED": seed},
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, done.stderr[-2000:]
        digests.add(done.stdout.strip())
    assert len(digests) == 1, f"the fixture changes with the hash seed: {digests}"


# ------------------------------------------------------------ the audit shape
def test_there_are_exactly_six_tier_one_units():
    assert len(T.units()) == 6
    assert set(T.units()) == set(UNITS)


def test_the_design_the_audit_scores_through_is_the_frozen_a3_one():
    assert DESIGN.n_per_truth_class == 72
    assert DESIGN.total_labels == 864
    assert DESIGN.errors_permitted == 0
    assert DESIGN.extension_permitted is False


def test_the_two_truth_classes_are_the_two_denominators_section_ten_four_names():
    assert {c.value for c in T.TruthClass} == {"truly_fails", "truly_passes"}


def test_the_material_categories_are_the_fourteen_section_ten_six_lists():
    assert len(MATERIAL) == 14
    for name in ("boundary_cases", "chat_preambles", "truncation", "empty_output",
                 "zero_width_characters", "homoglyphs", "smart_quotes",
                 "combining_marks", "code_fences", "line_ending_variants"):
        assert name in MATERIAL


# ---------------------------------------------------------------- audit cases
def test_a_case_records_the_pool_and_the_author_it_came_from():
    case = a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS)
    assert case.source_pool and case.authored_by and case.provenance


@pytest.mark.parametrize("field,value", [
    ("case_id", ""), ("source_pool", ""), ("authored_by", ""), ("provenance", ""),
])
def test_an_untraceable_case_is_refused(field, value):
    import dataclasses
    with pytest.raises(T.Tier1AuditError):
        dataclasses.replace(a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS),
                            **{field: value})


def test_a_case_for_something_that_is_not_a_tier_one_unit_is_refused():
    import dataclasses
    with pytest.raises(T.Tier1AuditError, match="not one of the six"):
        dataclasses.replace(a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS),
                            unit="v19:p9.target.invented")


def test_a_case_claiming_no_material_category_is_refused():
    import dataclasses
    with pytest.raises(T.Tier1AuditError, match="no material category"):
        dataclasses.replace(a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS),
                            material=())


def test_a_case_claiming_an_unlisted_material_category_is_refused():
    import dataclasses
    with pytest.raises(T.Tier1AuditError, match="unknown material category"):
        dataclasses.replace(a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS),
                            material=("vibes",))


def test_a_non_truth_class_is_refused_rather_than_coerced():
    import dataclasses
    with pytest.raises(T.Tier1AuditError, match="not a TruthClass"):
        dataclasses.replace(a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS),
                            intended_class="truly_fails")


def test_the_case_hash_covers_what_is_judged_and_not_the_prose():
    import dataclasses
    case = a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS)
    assert dataclasses.replace(case, provenance="reworded").case_hash == case.case_hash
    assert dataclasses.replace(case, authored_by="someone else").case_hash \
        == case.case_hash
    assert dataclasses.replace(case, text="different").case_hash != case.case_hash
    assert dataclasses.replace(case, parameters={"n_items": 4}).case_hash \
        != case.case_hash


# ------------------------------------------------------------ the manifest
def test_a_complete_manifest_has_1200_candidates_for_864_labels():
    """100 authored per class; 72 per class enter the interval."""
    manifest = a_manifest()
    assert len(manifest.cases) == 1200 == T.CANDIDATES_PER_CLASS * 2 * 6
    for unit in UNITS:
        for truth_class in T.TruthClass:
            assert len(manifest.for_unit(unit, truth_class)) == 100
    assert DESIGN.total_labels == 864


@pytest.mark.parametrize("per_class", [72, 99, 101, 150])
def test_the_authoring_budget_is_exactly_one_hundred_per_class(per_class):
    """Not "at least": under-authoring cannot reach 72 usable, over-authoring means
    the surplus sits outside the hash-bound pool."""
    with pytest.raises(T.Tier1AuditError, match="frozen authoring budget"):
        T.assert_manifest_is_complete(a_manifest(per_class=per_class))


def test_a_case_may_serve_only_one_verifier_unit():
    """Reuse means the SAME response, at the same parameters, under two units."""
    import dataclasses
    manifest = a_manifest(per_class=2)
    first = manifest.ordered[0]
    reused = dataclasses.replace(first, case_id="fixture/reused", unit=UNITS[-1])
    assert reused.text == first.text and reused.parameters == first.parameters
    assert reused.case_hash != first.case_hash        # the unit is in the hash
    with pytest.raises(T.Tier1AuditError, match="more than one verifier unit"):
        T.assert_no_case_serves_two_units(
            T.AuditManifest(cases=manifest.cases + (reused,)))


def test_the_manifest_order_is_deterministic_and_not_insertion_order():
    manifest = a_manifest(per_class=3)
    shuffled = T.AuditManifest(cases=tuple(reversed(manifest.cases)))
    assert [c.case_id for c in manifest.ordered] == \
        [c.case_id for c in shuffled.ordered]
    assert manifest.manifest_hash == shuffled.manifest_hash


def test_the_manifest_hash_moves_with_the_cases_and_the_design():
    import dataclasses
    manifest = a_manifest(per_class=3)
    other = T.AuditManifest(cases=manifest.cases[:-1])
    assert other.manifest_hash != manifest.manifest_hash
    relaxed = dataclasses.replace(DESIGN, errors_permitted=1)
    assert T.AuditManifest(cases=manifest.cases,
                           design=relaxed).manifest_hash != manifest.manifest_hash


def test_duplicate_case_ids_are_refused():
    case = a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS)
    with pytest.raises(T.Tier1AuditError, match="duplicate case id"):
        T.AuditManifest(cases=(case, case))


def test_two_identical_texts_under_different_ids_are_refused():
    import dataclasses
    case = a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS)
    twin = dataclasses.replace(case, case_id="fixture/other")
    with pytest.raises(T.Tier1AuditError, match="the same judgement"):
        T.AuditManifest(cases=(case, twin))


def test_a_stratum_cannot_be_padded_by_copying_one_case_under_many_ids():
    """72 pieces of evidence, not 72 rows."""
    import dataclasses
    case = a_case(UNITS[0], 1, T.TruthClass.TRULY_FAILS)
    copies = tuple(dataclasses.replace(case, case_id=f"fixture/copy/{i}")
                   for i in range(72))
    with pytest.raises(T.Tier1AuditError, match="pads a denominator"):
        T.AuditManifest(cases=copies)


def test_a_manifest_missing_a_material_category_is_refused():
    with pytest.raises(T.Tier1AuditError, match="material category"):
        T.assert_manifest_is_complete(a_manifest(spanning=False))


def test_a_complete_manifest_is_accepted():
    assert T.assert_manifest_is_complete(a_manifest()) is not None


def test_the_manifest_state_is_serialisable_because_it_is_archived():
    state = a_manifest(per_class=2).state()
    assert json.loads(json.dumps(state)) == state
    assert state["coverage"]["by_category"]


# -------------------------------------------------------------- the packets
def test_a_packet_asks_about_the_requirement_not_about_the_machine():
    manifest = a_manifest(per_class=1)
    built = T.packets(manifest)[0]
    assert "as a careful reader would judge it" in built["question"]
    assert "not shown one" in " ".join(built["caveats"])
    assert built["requirement"]


def test_every_packet_is_blinded():
    for built in T.packets(a_manifest(per_class=2)):
        T.assert_blinded(built)


@pytest.mark.parametrize("leak", [
    {"verdict": "PASS"}, {"role": "target"}, {"intended_class": "truly_fails"},
    {"constraint_id": "v19:p1.target.exact_bullet_count"}, {"arm": "B"},
    {"unit": "v19:p1.target.exact_bullet_count"},
])
def test_a_packet_that_leaks_a_blinded_field_is_refused(leak):
    built = dict(T.packets(a_manifest(per_class=1))[0])
    built.update(leak)
    with pytest.raises(T.Tier1AuditError):
        T.assert_blinded(built)


def test_a_leak_nested_inside_the_packet_is_caught_too():
    built = dict(T.packets(a_manifest(per_class=1))[0])
    built["extra"] = {"deeper": [{"verdict": "FAIL"}]}
    with pytest.raises(T.Tier1AuditError):
        T.assert_blinded(built)


def test_packet_ids_are_deterministic_across_builds():
    first = [p["packet_id"] for p in T.packets(a_manifest(per_class=3))]
    second = [p["packet_id"] for p in T.packets(a_manifest(per_class=3))]
    assert first == second
    assert len(set(first)) == len(first)


def test_the_packet_id_is_derived_from_the_case_so_it_is_reproducible():
    manifest = a_manifest(per_class=1)
    from dci.provenance.hashes import sha
    for built, case in zip(T.packets(manifest), manifest.ordered, strict=True):
        expected = sha(["v19/tier1-packet", T.MANIFEST_ID, case.case_hash])[:32]
        assert built["packet_id"] == expected


def test_the_reviewer_bundle_keeps_the_unblinding_index_separate():
    bundle = T.reviewer_bundle(a_manifest(per_class=2))
    assert bundle["n_packets"] == len(bundle["packets"]) == 24
    assert len(bundle["unblinding_index"]) == 24
    assert "investigator" in bundle["note"]
    for built in bundle["packets"]:
        T.assert_blinded(built)
    # The index carries exactly what the packets must not.
    assert all({"unit", "intended_class"} <= set(row)
               for row in bundle["unblinding_index"])


def test_the_reviewer_bundle_is_serialisable():
    bundle = T.reviewer_bundle(a_manifest(per_class=1))
    assert json.loads(json.dumps(bundle)) == bundle


# ------------------------------------------------------------- the protocol
def test_ingestion_refuses_to_run_before_the_audit_protocol_is_decided():
    manifest = a_manifest(per_class=1)
    with pytest.raises(T.Tier1AuditError, match="not decided"):
        T.ingest(manifest, [], declared_table(), a_panel())


def test_the_refusal_explains_why_section_eight_six_does_not_settle_it():
    with pytest.raises(T.Tier1AuditError) as caught:
        T.ingest(a_manifest(per_class=1), [], declared_table(), a_panel())
    message = str(caught.value)
    assert "8.6" in message and "semantic review" in message
    assert "how many reviewers" in message


# ------------------------------------------------------------- ingestion
def judgements_for(manifest, satisfied_by_class=None, reviewers=("a", "b")):
    """Fixture judgements. NOT reviewer output - the apparatus is what is tested."""
    satisfied_by_class = satisfied_by_class or {
        T.TruthClass.TRULY_FAILS: False, T.TruthClass.TRULY_PASSES: True}
    out = []
    for built, case in zip(T.packets(manifest), manifest.ordered, strict=True):
        for reviewer in reviewers:
            out.append({"packet_id": built["packet_id"],
                        "reviewer_id": f"reviewer-{reviewer}",
                        "satisfied": satisfied_by_class[case.intended_class],
                        "rationale": "a fixture rationale"})
    return out


def test_a_complete_unanimous_return_ingests():
    manifest = a_manifest(per_class=2)
    got = T.ingest(manifest, judgements_for(manifest), a_protocol_table(),
                   a_panel())
    assert len(got) == 24
    assert all(a.unanimous and a.matched_intent for a in got)


def test_a_missing_judgement_is_never_read_as_the_intended_class():
    manifest = a_manifest(per_class=2)
    returned = judgements_for(manifest)[:-2]
    with pytest.raises(T.Tier1AuditError, match="no judgement"):
        T.ingest(manifest, returned, a_protocol_table(), a_panel())


def test_a_judgement_about_an_unknown_packet_is_refused():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest) + [
        {"packet_id": "0" * 32, "reviewer_id": "reviewer-a",
         "satisfied": True, "rationale": "about something else"}]
    with pytest.raises(T.Tier1AuditError, match="not a packet in this manifest"):
        T.ingest(manifest, returned, a_protocol_table(), a_panel())


def test_one_reviewer_answering_twice_is_not_two_independent_reviews():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest, reviewers=("a", "a"))
    with pytest.raises(T.Tier1AuditError, match="judged it twice"):
        T.ingest(manifest, returned, a_protocol_table(), a_panel())


def test_too_few_independent_judgements_are_refused():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest, reviewers=("a",))
    with pytest.raises(T.Tier1AuditError, match="independent judgement"):
        T.ingest(manifest, returned, a_protocol_table(), a_panel())


@pytest.mark.parametrize("bad", ["yes", 1, 0, None, "true"])
def test_a_non_boolean_judgement_is_refused(bad):
    with pytest.raises(T.Tier1AuditError, match="real boolean"):
        T.Judgement("p", "reviewer-a", bad, "why")


def test_a_judgement_with_no_rationale_is_refused():
    with pytest.raises(T.Tier1AuditError, match="rationale is required"):
        T.Judgement("p", "reviewer-a", True, "   ")


@pytest.mark.parametrize("drop", ["packet_id", "reviewer_id", "satisfied",
                                  "rationale"])
def test_a_malformed_return_names_what_is_missing(drop):
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest)
    del returned[0][drop]
    with pytest.raises(T.Tier1AuditError, match="missing"):
        T.ingest(manifest, returned, a_protocol_table(), a_panel())


def test_a_return_that_is_not_a_record_at_all_is_refused():
    manifest = a_manifest(per_class=1)
    with pytest.raises(T.Tier1AuditError, match="expected a Judgement"):
        T.ingest(manifest, ["not a judgement"], a_protocol_table(), a_panel())


# ------------------------------------------------------------- adjudication
def split_return(manifest, with_adjudication):
    out = []
    for built in T.packets(manifest):
        out.append({"packet_id": built["packet_id"], "reviewer_id": "reviewer-a",
                    "satisfied": True, "rationale": "reads as satisfied"})
        out.append({"packet_id": built["packet_id"], "reviewer_id": "reviewer-b",
                    "satisfied": False, "rationale": "reads as unsatisfied"})
        if with_adjudication:
            out.append({"packet_id": built["packet_id"],
                        "reviewer_id": "reviewer-c", "satisfied": True,
                        "rationale": "adjudicated as satisfied"})
    return out


def test_an_unresolved_disagreement_is_excluded_as_unusable():
    """The protocol's answer: mark it unusable and exclude it - never resolve it by
    preferring one reviewer, which would invent a ground truth."""
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, False), a_protocol_table(), a_panel())
    assert all(not a.usable for a in got)
    assert all(not a.matched_intent for a in got)
    assert all("no human ground truth was established" in a.unusable_because
               for a in got)


def test_an_adjudicated_disagreement_resolves_to_the_adjudicator():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table(), a_panel())
    assert all(not a.unanimous for a in got)
    assert all(a.adjudicated_class is T.TruthClass.TRULY_PASSES for a in got)
    assert all(a.adjudication.reviewer_id == "reviewer-c" for a in got)


def test_the_adjudicator_is_not_counted_as_an_independent_reviewer():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table(), a_panel())
    for adjudicated in got:
        assert {j.reviewer_id for j in adjudicated.judgements} == {
            "reviewer-a", "reviewer-b"}


def test_adjudication_provenance_survives_into_the_record():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table(), a_panel())
    state = got[0].state()
    assert state["reviewers"] == ["reviewer-a", "reviewer-b"]
    assert state["adjudicator"] == "reviewer-c"
    assert state["unanimous"] is False
    assert json.loads(json.dumps(state)) == state


def test_a_case_adjudicated_against_its_intended_class_is_recorded_as_such():
    """Not a verifier error - a case-authoring miss, and it must be visible."""
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest, satisfied_by_class={
        T.TruthClass.TRULY_FAILS: True, T.TruthClass.TRULY_PASSES: True})
    got = T.ingest(manifest, returned, a_protocol_table(), a_panel())
    missed = [a for a in got if not a.matched_intent]
    assert len(missed) == 6            # one per unit, the truly_fails fixtures
    assert all(a.adjudicated_class is T.TruthClass.TRULY_PASSES for a in missed)


# ------------------------------------------------ deterministic selection
def full_audit(satisfied_by_class=None, unresolved=0, cross_class=0):
    """Adjudicate a complete 1,200-candidate fixture manifest.

    `unresolved` and `cross_class` spoil that many candidates PER STRATUM, so a
    stratum retains 100 - unresolved - cross_class usable cases.
    """
    manifest = a_manifest()
    satisfied_by_class = satisfied_by_class or {
        T.TruthClass.TRULY_FAILS: False, T.TruthClass.TRULY_PASSES: True}
    seen: dict[tuple, int] = {}
    returned = []
    for built, case in zip(T.packets(manifest), manifest.ordered, strict=True):
        key = (case.unit, case.intended_class)
        n = seen.get(key, 0)
        seen[key] = n + 1
        intended = satisfied_by_class[case.intended_class]
        if n < unresolved:                       # A and B disagree, no adjudicator
            answers, adjudicate = (True, False), False
        elif n < unresolved + cross_class:       # unanimous, but the other class
            answers, adjudicate = (not intended, not intended), False
        else:
            answers, adjudicate = (intended, intended), False
        for reviewer, answer in zip(("a", "b"), answers, strict=True):
            returned.append({"packet_id": built["packet_id"],
                             "reviewer_id": f"reviewer-{reviewer}",
                             "satisfied": answer,
                             "rationale": "a fixture rationale"})
        if adjudicate:
            returned.append({"packet_id": built["packet_id"],
                             "reviewer_id": "reviewer-c", "satisfied": intended,
                             "rationale": "a fixture adjudication"})
    return manifest, T.ingest(manifest, returned, a_protocol_table(), a_panel())


def clean_verdicts(adjudicated):
    """A perfect verifier: it agrees with every established human truth."""
    return {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
            for a in adjudicated}


def test_selection_takes_exactly_seventy_two_per_stratum():
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    assert len(selection) == 12
    for chosen in selection.values():
        assert len(chosen.selected) == 72
        assert chosen.reserve_ignored == 28       # 100 authored, 72 taken


def test_selection_is_the_first_seventy_two_in_frozen_manifest_order():
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    for unit in UNITS:
        for truth_class in T.TruthClass:
            expected = [c.case_id
                        for c in manifest.for_unit(unit, truth_class)][:72]
            assert list(selection[(unit, truth_class.value)].selected) == expected


def test_selection_is_deterministic_across_runs():
    manifest, adjudicated = full_audit()
    first = T.select(manifest, adjudicated)
    second = T.select(manifest, adjudicated)
    assert {k: v.selected for k, v in first.items()} == \
        {k: v.selected for k, v in second.items()}


def test_a_cross_class_candidate_is_discarded_not_credited():
    """No cross-crediting: it does not swell the other class."""
    manifest, adjudicated = full_audit(cross_class=5)
    selection = T.select(manifest, adjudicated)
    for chosen in selection.values():
        assert chosen.discarded_cross_class == 5
        assert chosen.usable == 95                # 100 - 5, not 105
        assert len(chosen.selected) == 72


def test_an_unusable_candidate_is_excluded_from_selection():
    manifest, adjudicated = full_audit(unresolved=7)
    selection = T.select(manifest, adjudicated)
    for chosen in selection.values():
        assert chosen.discarded_unusable == 7
        assert chosen.usable == 93
    excluded = {a.case_id for a in adjudicated if not a.usable}
    chosen_ids = {cid for c in selection.values() for cid in c.selected}
    assert not (excluded & chosen_ids)


def test_a_case_never_adjudicated_is_missing_evidence_not_a_discard():
    manifest, adjudicated = full_audit()
    with pytest.raises(T.Tier1AuditError, match="missing evidence"):
        T.select(manifest, [a for a in adjudicated if a.case_id
                            != adjudicated[0].case_id])


# ----------------------------------------------- AUDIT_POOL_INSUFFICIENT
@pytest.mark.parametrize("spoiled", [29, 40, 100])
def test_fewer_than_seventy_two_usable_returns_audit_pool_insufficient(spoiled):
    manifest, adjudicated = full_audit(cross_class=spoiled)
    with pytest.raises(T.AuditPoolInsufficient) as caught:
        T.select(manifest, adjudicated)
    assert "AUDIT_POOL_INSUFFICIENT" in str(caught.value)
    assert len(caught.value.report) == 12
    for row in caught.value.report.values():
        assert row["usable"] == 100 - spoiled
        assert row["required"] == 72


def test_the_insufficiency_report_does_not_say_how_many_more_to_author():
    """Because authoring after seeing the reviews is what the protocol forbids."""
    manifest, adjudicated = full_audit(unresolved=30)
    with pytest.raises(T.AuditPoolInsufficient) as caught:
        T.select(manifest, adjudicated)
    message = str(caught.value)
    assert "no post-review top-up" in message
    assert "fresh prospectively specified audit" in message
    for row in caught.value.report.values():
        assert "author" not in " ".join(map(str, row))


def test_a_stratum_one_case_short_still_fails_closed():
    manifest, adjudicated = full_audit(unresolved=29)
    with pytest.raises(T.AuditPoolInsufficient):
        T.select(manifest, adjudicated)


def test_exactly_seventy_two_usable_is_enough_and_ignores_nothing():
    manifest, adjudicated = full_audit(unresolved=28)
    selection = T.select(manifest, adjudicated)
    for chosen in selection.values():
        assert chosen.usable == 72 and chosen.reserve_ignored == 0


# ---------------------------------------- scoring through the A3 design
def test_a_clean_audit_certifies_every_unit():
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    verdicts = clean_verdicts(adjudicated)
    for unit in UNITS:
        certificate = T.certify_unit(unit, selection, adjudicated, verdicts)
        assert certificate.passed, certificate.describe()


def test_one_verifier_error_inside_the_selection_fails_that_unit():
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    verdicts = clean_verdicts(adjudicated)
    chosen = selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)].selected
    verdicts[chosen[0]] = True                    # a false PASS
    assert not T.certify_unit(UNITS[0], selection, adjudicated, verdicts).passed
    assert T.certify_unit(UNITS[1], selection, adjudicated, verdicts).passed


def test_an_error_on_an_ignored_reserve_case_does_not_enter_the_bound():
    """Only the selected 72 contribute; the reserve is ignored, as frozen."""
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    verdicts = clean_verdicts(adjudicated)
    chosen = set(selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)].selected)
    reserve = [c.case_id for c in manifest.for_unit(UNITS[0],
                                                   T.TruthClass.TRULY_FAILS)
               if c.case_id not in chosen]
    verdicts[reserve[0]] = True
    assert T.certify_unit(UNITS[0], selection, adjudicated, verdicts).passed


def test_a_failed_unit_cannot_be_rescued_by_adding_labels():
    """A3's point, and the protocol's: no top-up, no conditional extension."""
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    verdicts = clean_verdicts(adjudicated)
    chosen = selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)].selected
    verdicts[chosen[0]] = True
    assert not T.certify_unit(UNITS[0], selection, adjudicated, verdicts).passed

    # Widening the stratum to 110 - the size at which one error clears the interval
    # - is refused by the design rather than accepted.
    import dataclasses
    widened = dataclasses.replace(
        selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)],
        selected=tuple(list(chosen) + [
            c.case_id for c in manifest.for_unit(UNITS[0],
                                                 T.TruthClass.TRULY_FAILS)
            if c.case_id not in set(chosen)][:38]))
    spliced = dict(selection)
    spliced[(UNITS[0], T.TruthClass.TRULY_FAILS.value)] = widened
    certificate = T.certify_unit(UNITS[0], spliced, adjudicated, verdicts)
    assert not certificate.passed
    assert any("forbids conditional extension" in b.design_violation
               for b in certificate.bounds)


def test_a_selected_case_with_no_verifier_verdict_cannot_contribute():
    manifest, adjudicated = full_audit()
    selection = T.select(manifest, adjudicated)
    verdicts = clean_verdicts(adjudicated)
    verdicts.pop(selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)].selected[0])
    with pytest.raises(T.Tier1AuditError, match="no verifier verdict"):
        T.certify_unit(UNITS[0], selection, adjudicated, verdicts)


def test_certify_all_returns_a_record_the_registry_domain_accepts():
    from dci.v19.schemas import validate
    manifest, adjudicated = full_audit()
    record = T.certify_all(manifest, adjudicated, clean_verdicts(adjudicated))
    assert set(record) == set(UNITS)
    validate("tier1_certificates", record)
    for row in record.values():
        for bound in row["bounds"]:
            assert bound["denominator"] == 72


def test_a_failing_record_is_refused_by_the_registry_domain():
    from dci.v19.schemas import DomainError, validate
    manifest, adjudicated = full_audit()
    verdicts = clean_verdicts(adjudicated)
    selection = T.select(manifest, adjudicated)
    verdicts[selection[(UNITS[0], T.TruthClass.TRULY_FAILS.value)].selected[0]] = True
    with pytest.raises(DomainError):
        validate("tier1_certificates",
                 T.certify_all(manifest, adjudicated, verdicts))


def test_certify_all_propagates_pool_insufficiency():
    manifest, adjudicated = full_audit(cross_class=40)
    with pytest.raises(T.AuditPoolInsufficient):
        T.certify_all(manifest, adjudicated, clean_verdicts(adjudicated))


# --------------------------------------------- the frozen protocol itself
def test_the_protocol_is_frozen_in_the_registry():
    from dci.v19.registry import REGISTRY
    slot = REGISTRY.slots["verifiers.tier1_audit_protocol"]
    assert slot.resolved and slot.frozen_by
    assert slot.get() == dict(T.PROTOCOL)


def test_the_frozen_protocol_records_every_decision_it_was_asked_to():
    p = T.PROTOCOL
    assert p["candidates_per_class"] == 100
    assert p["candidates_per_unit"] == 200
    assert p["independent_reviewers"] == 2
    assert p["panel_size"] == 3
    assert p["adjudicator_resolves_disagreement"] is True
    assert p["reviewers_communicate_before_submitting"] is False
    assert p["cross_crediting_permitted"] is False
    assert p["unresolved_case"] == "excluded_unusable"
    assert p["top_up_permitted"] is False
    assert p["conditional_extension_permitted"] is False
    assert p["case_reuse_across_units_permitted"] is False
    assert p["selection_rule"] == T.SELECTION_ID
    assert p["selection_size"] == 72
    assert p["insufficient_pool_outcome"] == "AUDIT_POOL_INSUFFICIENT"
    assert p["ground_truth_source"] == "human_adjudication"


def test_every_blinded_field_the_protocol_names_is_enforced():
    for name in ("intended_truth_class", "verifier_verdict", "arm"):
        assert name in T.PROTOCOL["blinded_to"]
    # and the packet checker refuses them
    assert "intended_class" in T.FORBIDDEN_IN_PACKET
    assert "verdict" in T.FORBIDDEN_IN_PACKET
    assert "arm" in T.FORBIDDEN_IN_PACKET
    assert "role" in T.FORBIDDEN_IN_PACKET


@pytest.mark.parametrize("field,value", [
    ("candidates_per_class", 72), ("cross_crediting_permitted", True),
    ("top_up_permitted", True), ("independent_reviewers", 1),
    ("case_reuse_across_units_permitted", True),
    ("conditional_extension_permitted", True),
    ("unresolved_case", "resolved_by_majority"),
])
def test_a_protocol_the_apparatus_does_not_enforce_is_refused(field, value):
    from dci.v19.schemas import DomainError, validate
    offered = dict(T.PROTOCOL)
    offered[field] = value
    with pytest.raises(DomainError, match="differs from the implemented one"):
        validate("tier1_audit_protocol", offered)


# --------------------------------------------------- nothing was fabricated
def test_the_audit_material_pools_are_still_unauthored():
    """The reason this apparatus cannot yet be run for real."""
    from dci.v19.registry import REGISTRY
    for pair in pairs.PAIR_IDS:
        slot = REGISTRY.slots[f"pool.{pair}.audit"]
        assert slot.pending, pair
        assert slot.status == "BLOCKED_BY_CONTENT", pair


def test_the_reliability_slot_is_still_unresolved():
    from dci.v19 import frozen
    from dci.v19.registry import REGISTRY
    assert REGISTRY.slots["verifiers.tier1_reliability"].pending
    assert "verifiers.tier1_reliability" not in {r["slot"] for r in frozen.audit()}


def test_the_reliability_slot_depends_on_the_audit_pools_and_the_protocol():
    from dci.v19.registry import REGISTRY
    depends = set(REGISTRY.slots["verifiers.tier1_reliability"].depends_on)
    for pair in pairs.PAIR_IDS:
        assert f"pool.{pair}.audit" in depends
    assert "verifiers.tier1_audit_protocol" in depends


def test_the_module_ships_no_audit_cases_of_its_own():
    """A fixture that leaked into the source would be indistinguishable evidence."""
    import inspect

    import dci.v19.tier1_audit as module
    source = inspect.getsource(module)
    assert "AuditCase(" not in source.replace("class AuditCase(", "")
    assert "Judgement(" not in source.replace("class Judgement(", "").replace(
        "-> Judgement:", "").replace("return Judgement(", "")
