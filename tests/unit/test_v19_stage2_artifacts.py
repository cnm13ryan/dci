"""The recorded Stage 2 outputs, and the review packets they do not include.

Two modules, one purpose: separate what Stage 2 HAS produced from what it is still
waiting on, and make the difference impossible to blur.

`dci.v19.frozen` is where a produced value survives the process that produced it -
without it a freeze that is never written down is a freeze that never happened. Three
properties are asserted here rather than trusted: every value re-runs its own typed
domain at import, a record cannot precede its own prerequisites, and a record cannot
re-freeze something the registry already carries.

`dci.v19.review_packets` prepares the section 8.6 questions. The tests that matter are
the blinding ones: section 10.6 blinds a reviewer to arm, automatic verdict and
constraint role, and a packet that leaked any of them would make the review evidence
about something other than the semantics.
"""
import json
import tempfile
from pathlib import Path

import pytest

from dci.v19 import encoding as E
from dci.v19 import frozen, pairs
from dci.v19 import review_packets as RP
from dci.v19.parsing import CANONICAL_LIST_POLICY as P
from dci.v19.parsing import OrderingRelation
from dci.v19.registry import REGISTRY, build, declared_table

pytestmark = pytest.mark.cpu

RELATION = OrderingRelation(items=("alfa", "bravo", "charlie"),
                            edges=(("alfa", "bravo"), ("bravo", "charlie")))

# Amendments A1-A4 accepted by the investigator, then the artifacts Stage 2
# produces once those decisions exist. Order matters: frozen.apply refuses a
# record whose own prerequisites are still unresolved.
ACCEPTED = ("verifiers.p1.list_policy", "verifiers.p1.ordering_depth",
            "verifiers.inherited_reuse_decision",
            "verifiers.binomial_interval_implementation",
            "verifiers.tier1_audit_design")
PRODUCED = ("satisfiability.solver_identity", "satisfiability.encoding_map",
            "satisfiability.witness_constructor", "satisfiability.review_trigger",
            "verifiers.specification_bundle", "verifiers.boundary_mutations",
            "verifiers.bundle_hash")
RECORDED = ACCEPTED + PRODUCED


def reviewable_compositions():
    return (
        E.encode_composition("p1/review/B", pair_id="p1", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_1.target.constraint_id: {
                                     "n_items": 3, "policy": P},
                                 pairs.PAIR_1.focal.constraint_id: {
                                     "relation": RELATION, "policy": P}}),
        E.encode_composition("p2/review/B", pair_id="p2", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_2.target.constraint_id: {
                                     "mandatory_words": ("alfa", "bravo"),
                                     "policy": P},
                                 pairs.PAIR_2.focal.constraint_id: {"policy": P}}),
        E.encode_composition("p3/review/B", pair_id="p3", arm="B", load=2,
                             realisations={
                                 pairs.PAIR_3.target.constraint_id: {
                                     "n_sentences": 3, "policy": P},
                                 pairs.PAIR_3.focal.constraint_id: {"policy": P}}),
    )


def write_records(directory, records):
    target = Path(directory) / "records.json"
    target.write_text(json.dumps({"records": records}))
    return target


# ------------------------------------------------------- the recorded outputs
def test_exactly_the_three_produced_artifacts_are_recorded():
    assert set(row["slot"] for row in frozen.audit()) == set(RECORDED)
    for name in PRODUCED:
        slot = REGISTRY.slots[name]
        assert slot.resolved and slot.frozen_by and slot.domain


def test_every_record_states_who_produced_it_when_and_on_what_evidence():
    for row in frozen.audit():
        assert row["frozen_by"].strip(), row["slot"]
        assert row["recorded_at"].startswith("20"), row["slot"]
        assert len(row["evidence"]) > 80, row["slot"]


def test_the_audit_never_carries_the_values():
    for row in frozen.audit():
        assert set(row) == {"slot", "frozen_by", "recorded_at", "evidence"}


def test_a_record_missing_any_required_field_is_refused():
    for field in frozen.REQUIRED_FIELDS:
        record = {"slot": "satisfiability.solver_identity", "value": {"a": 1},
                  "frozen_by": "x", "recorded_at": "2026-01-01T00:00:00+00:00",
                  "evidence": "y"}
        del record[field]
        with tempfile.TemporaryDirectory() as directory, \
                pytest.raises(frozen.FrozenRecordError, match="is missing"):
            frozen.records(write_records(directory, [record]))


def test_a_record_whose_prerequisites_are_unresolved_is_refused():
    """Section 14 lets a later stage consume a frozen output, not precede it."""
    record = {"slot": "verifiers.bundle_hash", "value": "0" * 64,
              "frozen_by": "probe", "recorded_at": "2026-01-01T00:00:00+00:00",
              "evidence": "probe"}
    with tempfile.TemporaryDirectory() as directory, \
            pytest.raises(frozen.FrozenRecordError, match="out of order"):
        frozen.apply(declared_table(), write_records(directory, [record]))


def test_a_record_cannot_refreeze_what_the_registry_already_carries():
    """Applied to the LIVE registry, where the value is already present."""
    record = {"slot": "verifiers.p1.list_policy", "value": P.state(),
              "frozen_by": "probe", "recorded_at": "2026-01-01T00:00:00+00:00",
              "evidence": "probe"}
    with tempfile.TemporaryDirectory() as directory, \
            pytest.raises(frozen.FrozenRecordError, match="already"):
        frozen.apply(REGISTRY.slots, write_records(directory, [record]))


def a_record(name, value):
    return {"slot": name, "value": value, "frozen_by": "probe",
            "recorded_at": "2026-01-01T00:00:00+00:00", "evidence": "probe"}


@pytest.mark.parametrize("name,bad", [
    ("satisfiability.solver_identity", {"name": "z3", "version": "0.0.0"}),
    ("satisfiability.encoding_map", {"abstract_features": {}}),
])
def test_a_recorded_value_its_domain_rejects_is_refused_at_apply_time(name, bad):
    """A wrong value in the file fails when the registry is built, not later.

    The encoding map waits on the list policy, so that acceptance is supplied
    first: otherwise the ORDERING guard would refuse the record and the domain
    would never run, which would make this test pass for the wrong reason.
    """
    prefix = ([a_record("verifiers.p1.list_policy", P.state())]
              if name == "satisfiability.encoding_map" else [])
    with tempfile.TemporaryDirectory() as directory, \
            pytest.raises(ValueError, match="not admissible for domain"):
        frozen.apply(declared_table(),
                     write_records(directory, prefix + [a_record(name, bad)]))


def test_the_domain_runs_after_the_ordering_guard_lets_a_record_through():
    """The witness constructor waits on the encoding map, so supply it first."""
    from dci.v19.encoding import encoding_map_state
    # The encoding map itself waits on the list policy, so accept that first.
    ordered = [a_record("verifiers.p1.list_policy", P.state()),
               a_record("satisfiability.encoding_map", encoding_map_state(P)),
               a_record("satisfiability.witness_constructor",
                        "v19:witness-constructor.other")]
    with tempfile.TemporaryDirectory() as directory, \
            pytest.raises(ValueError, match="not admissible for domain"):
        frozen.apply(declared_table(), write_records(directory, ordered))
    # And with the right value, both apply.
    from dci.v19.witness import CONSTRUCTOR_ID
    good = [ordered[0], ordered[1],
            a_record("satisfiability.witness_constructor", CONSTRUCTOR_ID)]
    with tempfile.TemporaryDirectory() as directory:
        table = frozen.apply(declared_table(), write_records(directory, good))
        assert table["satisfiability.witness_constructor"].resolved


def test_an_absent_file_records_nothing_rather_than_failing():
    with tempfile.TemporaryDirectory() as directory:
        missing = Path(directory) / "nothing.json"
        assert frozen.records(missing) == ()


def test_a_malformed_file_is_refused():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "records.json"
        target.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(frozen.FrozenRecordError, match="records"):
            frozen.records(target)


def test_the_declared_table_and_the_built_registry_differ_by_exactly_the_records():
    declared = declared_table()
    produced = {slot.name for slot in REGISTRY.slots.resolved()} - {
        slot.name for slot in declared.resolved()}
    assert produced == set(RECORDED)


def test_the_registry_applies_the_records_and_stays_reproducible():
    first, second = build(), build()
    assert first.state_fingerprint == second.state_fingerprint
    assert first.state_fingerprint == REGISTRY.state_fingerprint


def test_the_recorded_values_are_the_ones_the_code_computes():
    from dci.v19.encoding import encoding_map_state
    from dci.v19.solver import solver_identity
    from dci.v19.witness import CONSTRUCTOR_ID
    name, version = solver_identity()
    assert REGISTRY.slots.value("satisfiability.solver_identity") == {
        "name": name, "version": version}
    assert REGISTRY.slots.value("satisfiability.encoding_map") == \
        encoding_map_state(P)
    assert REGISTRY.slots.value("satisfiability.witness_constructor") == \
        CONSTRUCTOR_ID


# ------------------------------------------------------------ the review packets
def test_one_packet_per_incompletely_covered_clause():
    bundle = RP.bundle(reviewable_compositions(), P)
    assert bundle["n_packets"] == 3
    assert len(bundle["unblinding_index"]) == 3


@pytest.mark.parametrize("index", range(3))
def test_every_packet_is_blinded(index):
    packet = RP.bundle(reviewable_compositions(), P)["packets"][index]
    RP.assert_blinded(packet)


def test_a_packet_leaking_the_arm_or_a_verdict_is_refused():
    for leak in ({"arm": "B"}, {"role": "focal"}, {"verdict": "PASS"},
                 {"composition_id": "p2/1/B"}, {"nested": {"v_all": 1}}):
        with pytest.raises(RP.PacketError):
            RP.assert_blinded({"packet_id": "x", **leak})


def test_a_packet_naming_a_pair_constraint_identifier_is_refused():
    with pytest.raises(RP.PacketError, match="pair and the role"):
        RP.assert_blinded({"note": pairs.PAIR_2.focal.constraint_id})


def test_a_packet_asks_only_about_an_incompletely_covered_clause():
    """Asking about a COMPLETE clause would invite a reviewer to override the code."""
    composition = reviewable_compositions()[0]
    complete = next(c for c in composition.clauses
                    if c.constraint_id == pairs.PAIR_1.target.constraint_id)
    with pytest.raises(RP.PacketError, match="requires no human review"):
        RP.packet(composition, complete, P)


def test_a_packet_carries_what_the_question_cannot_be_answered_without():
    packet = RP.bundle(reviewable_compositions(), P)["packets"][0]
    assert packet["requirement"] and packet["not_covered_deterministically"]
    assert packet["response"] and packet["response_hash"]
    assert packet["answer_schema"]["satisfied"].startswith("true or false")
    assert "third reviewer adjudicates" in packet["procedure"] or \
        "third reviewer" in packet["procedure"]
    assert any("NOT calibrated" in caveat for caveat in packet["caveats"])


def test_the_packet_response_is_the_witness_the_verifiers_accepted():
    from dci.v19 import certification as C
    from dci.v19.witness import construct_witness
    for composition in reviewable_compositions():
        built = construct_witness(composition, P)
        conjunction = C.run_conjunction(composition, built.text or "", P)
        assert conjunction.v_all == 1
        packet = RP.packets_for(composition, P)[0]
        assert packet["response"] == built.text
        assert packet["response_hash"] == built.witness_hash


def test_the_packet_identifier_is_opaque_and_stable():
    first = RP.bundle(reviewable_compositions(), P)["packets"]
    second = RP.bundle(reviewable_compositions(), P)["packets"]
    assert [p["packet_id"] for p in first] == [p["packet_id"] for p in second]
    for packet in first:
        assert len(packet["packet_id"]) == 32
        for pair_id in pairs.PAIR_IDS:
            assert pair_id not in packet["packet_id"]


def test_the_unblinding_index_is_kept_out_of_the_packets():
    bundle = RP.bundle(reviewable_compositions(), P)
    assert all("composition_id" in row for row in bundle["unblinding_index"])
    for packet in bundle["packets"]:
        assert "composition_id" not in packet


def test_no_review_is_recorded_by_this_module():
    """It prepares questions; a verdict needs a named human and a rationale."""
    assert RP.outstanding(reviewable_compositions()) == (
        "p1/review/B", "p2/review/B", "p3/review/B")
    assert REGISTRY.slots["satisfiability.semantic_reviews"].pending


def test_a_recorded_review_that_did_not_resolve_still_counts_as_outstanding():
    recorded = {"p1/review/B": {
        "witness_hash": "0" * 64,
        "clause_ids": [pairs.PAIR_1.focal.constraint_id],
        "reviews": [{"reviewer_id": "a", "satisfied": True, "rationale": "yes"},
                    {"reviewer_id": "b", "satisfied": False, "rationale": "no"}]}}
    assert "p1/review/B" in RP.outstanding(reviewable_compositions(), recorded)


def test_the_generated_bundle_on_disk_matches_the_generator():
    published = Path("docs/v19_stage2_semantic_review_packets.json")
    if not published.exists():                     # pragma: no cover - source tree
        pytest.skip("the published packet bundle is not in this checkout")
    on_disk = json.loads(published.read_text())
    regenerated = RP.bundle(reviewable_compositions(), P)
    assert on_disk["n_packets"] == regenerated["n_packets"]
    assert [p["packet_id"] for p in on_disk["packets"]] == \
        [p["packet_id"] for p in regenerated["packets"]]
    assert on_disk["list_policy_hash"] == P.policy_hash
