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
        # caught it.
        text=f"SYNTHETIC TEST FIXTURE {abs(hash((unit, truth_class.value))) % 997}"
             f" item {index}",
        parameters={"n_items": 3},
        intended_class=truth_class,
        material=tuple(material),
        source_pool="fixture (NOT pool.p1.audit)",
        authored_by="the test suite",
        provenance="a fixture for the audit apparatus; not audit material")


def a_manifest(per_class=None, spanning=True):
    """A structurally complete manifest built entirely from fixtures."""
    per_class = DESIGN.n_per_truth_class if per_class is None else per_class
    cases = []
    for unit in UNITS:
        for truth_class in T.TruthClass:
            for i in range(per_class):
                material = ((MATERIAL[i % len(MATERIAL)],) if spanning
                            else ("boundary_cases",))
                cases.append(a_case(unit, i, truth_class, material))
    return T.AuditManifest(cases=tuple(cases))


def a_protocol_table(**overrides):
    """The declared table with the audit protocol decided, for ingestion tests."""
    value = {"independent_reviewers": 2,
             "adjudicator_resolves_disagreement": True,
             "adjudicator_id": "reviewer-c",
             "unresolved_disagreement": "fails",
             "oversampling_rule": "exact_authoring",
             "citation": "a fixture protocol for an apparatus test"}
    value.update(overrides)
    return declared_table().freeze("verifiers.tier1_audit_protocol", value,
                                   by="a fixture for an apparatus test")


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
def test_a_complete_manifest_has_864_cases():
    manifest = a_manifest()
    assert len(manifest.cases) == 864 == DESIGN.total_labels
    for unit in UNITS:
        for truth_class in T.TruthClass:
            assert len(manifest.for_unit(unit, truth_class)) == 72


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


def test_a_short_stratum_is_refused_before_anything_is_sent_out():
    with pytest.raises(T.Tier1AuditError, match="cannot reach the design size"):
        T.assert_manifest_is_complete(a_manifest(per_class=71))


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
        T.ingest(manifest, [], declared_table())


def test_the_refusal_explains_why_section_eight_six_does_not_settle_it():
    with pytest.raises(T.Tier1AuditError) as caught:
        T.ingest(a_manifest(per_class=1), [], declared_table())
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
    got = T.ingest(manifest, judgements_for(manifest), a_protocol_table())
    assert len(got) == 24
    assert all(a.unanimous and a.matched_intent for a in got)


def test_a_missing_judgement_is_never_read_as_the_intended_class():
    manifest = a_manifest(per_class=2)
    returned = judgements_for(manifest)[:-2]
    with pytest.raises(T.Tier1AuditError, match="no judgement"):
        T.ingest(manifest, returned, a_protocol_table())


def test_a_judgement_about_an_unknown_packet_is_refused():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest) + [
        {"packet_id": "0" * 32, "reviewer_id": "reviewer-a",
         "satisfied": True, "rationale": "about something else"}]
    with pytest.raises(T.Tier1AuditError, match="not a packet in this manifest"):
        T.ingest(manifest, returned, a_protocol_table())


def test_one_reviewer_answering_twice_is_not_two_independent_reviews():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest, reviewers=("a", "a"))
    with pytest.raises(T.Tier1AuditError, match="judged it twice"):
        T.ingest(manifest, returned, a_protocol_table())


def test_too_few_independent_judgements_are_refused():
    manifest = a_manifest(per_class=1)
    returned = judgements_for(manifest, reviewers=("a",))
    with pytest.raises(T.Tier1AuditError, match="independent judgement"):
        T.ingest(manifest, returned, a_protocol_table())


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
        T.ingest(manifest, returned, a_protocol_table())


def test_a_return_that_is_not_a_record_at_all_is_refused():
    manifest = a_manifest(per_class=1)
    with pytest.raises(T.Tier1AuditError, match="expected a Judgement"):
        T.ingest(manifest, ["not a judgement"], a_protocol_table())


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


def test_an_unresolved_disagreement_is_not_evidence():
    manifest = a_manifest(per_class=1)
    with pytest.raises(T.Tier1AuditError, match="no adjudication was returned"):
        T.ingest(manifest, split_return(manifest, False), a_protocol_table())


def test_an_adjudicated_disagreement_resolves_to_the_adjudicator():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table())
    assert all(not a.unanimous for a in got)
    assert all(a.adjudicated_class is T.TruthClass.TRULY_PASSES for a in got)
    assert all(a.adjudication.reviewer_id == "reviewer-c" for a in got)


def test_the_adjudicator_is_not_counted_as_an_independent_reviewer():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table())
    for adjudicated in got:
        assert {j.reviewer_id for j in adjudicated.judgements} == {
            "reviewer-a", "reviewer-b"}


def test_adjudication_provenance_survives_into_the_record():
    manifest = a_manifest(per_class=1)
    got = T.ingest(manifest, split_return(manifest, True), a_protocol_table())
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
    got = T.ingest(manifest, returned, a_protocol_table())
    missed = [a for a in got if not a.matched_intent]
    assert len(missed) == 6            # one per unit, the truly_fails fixtures
    assert all(a.adjudicated_class is T.TruthClass.TRULY_PASSES for a in missed)


# --------------------------------------------- scoring through the A3 design
def adjudicate_full(satisfied_by_class=None):
    manifest = a_manifest()
    returned = judgements_for(manifest, satisfied_by_class)
    return manifest, T.ingest(manifest, returned, a_protocol_table())


def test_a_clean_audit_certifies_every_unit():
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
                for a in adjudicated}
    for unit in UNITS:
        certificate = T.certify_unit(unit, adjudicated, verdicts)
        assert certificate.passed, certificate.describe()


def test_one_verifier_error_fails_that_unit():
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
                for a in adjudicated}
    wrong = next(a for a in adjudicated
                 if a.unit == UNITS[0]
                 and a.adjudicated_class is T.TruthClass.TRULY_FAILS)
    verdicts[wrong.case_id] = True                    # a false PASS
    assert not T.certify_unit(UNITS[0], adjudicated, verdicts).passed
    assert T.certify_unit(UNITS[1], adjudicated, verdicts).passed


def test_a_failed_unit_cannot_be_rescued_by_adding_labels():
    """A3's whole point, exercised end to end through the audit apparatus."""
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
                for a in adjudicated}
    wrong = next(a for a in adjudicated
                 if a.unit == UNITS[0]
                 and a.adjudicated_class is T.TruthClass.TRULY_FAILS)
    verdicts[wrong.case_id] = True
    assert not T.certify_unit(UNITS[0], adjudicated, verdicts).passed

    # Now add 38 more truly-failing cases, taking the stratum to 110 - the size at
    # which one error clears the interval. It must still fail, on the design.
    extra = [T.AdjudicatedCase(
        case_id=f"fixture/extra/{i}", unit=UNITS[0],
        adjudicated_class=T.TruthClass.TRULY_FAILS,
        intended_class=T.TruthClass.TRULY_FAILS,
        judgements=(), adjudication=None, unanimous=True) for i in range(38)]
    for case in extra:
        verdicts[case.case_id] = False
    certificate = T.certify_unit(UNITS[0], list(adjudicated) + extra, verdicts)
    assert not certificate.passed
    assert any("forbids conditional extension" in b.design_violation
               for b in certificate.bounds)


def test_a_case_with_no_verifier_verdict_cannot_contribute():
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: True for a in adjudicated}
    verdicts.pop(adjudicated[0].case_id)
    with pytest.raises(T.Tier1AuditError, match="no verifier verdict"):
        T.certify_unit(adjudicated[0].unit, adjudicated, verdicts)


def test_certify_all_returns_a_record_the_registry_domain_accepts():
    from dci.v19.schemas import validate
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
                for a in adjudicated}
    record = T.certify_all(adjudicated, verdicts)
    assert set(record) == set(UNITS)
    validate("tier1_certificates", record)


def test_a_failing_record_is_refused_by_the_registry_domain():
    from dci.v19.schemas import DomainError, validate
    _manifest, adjudicated = adjudicate_full()
    verdicts = {a.case_id: a.adjudicated_class is T.TruthClass.TRULY_PASSES
                for a in adjudicated}
    wrong = next(a for a in adjudicated
                 if a.unit == UNITS[0]
                 and a.adjudicated_class is T.TruthClass.TRULY_FAILS)
    verdicts[wrong.case_id] = True
    with pytest.raises(DomainError):
        validate("tier1_certificates", T.certify_all(adjudicated, verdicts))


# --------------------------------------------------- nothing was fabricated
def test_the_audit_material_pools_are_still_unauthored():
    """The reason this apparatus cannot yet be run for real."""
    from dci.v19.registry import REGISTRY
    for pair in pairs.PAIR_IDS:
        slot = REGISTRY.slots[f"pool.{pair}.audit"]
        assert slot.pending, pair
        assert slot.status == "BLOCKED_BY_CONTENT", pair


def test_the_reliability_slot_depends_on_the_audit_pools():
    """The edge that was missing: a certificate with no material is not evidence."""
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
