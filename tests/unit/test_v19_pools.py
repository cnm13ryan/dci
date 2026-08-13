"""Material splits, background strata, and pool signing.

Three commitments, each with a failure mode that is silent without a check:

  * section 11.1 partitions all material that can affect a frozen scientific
    choice, so an item in two splits breaks the firewall between pre-freeze
    decisions and confirmatory content while producing no visible error;
  * section 8.2 gives each background constraint exactly one stratum, and
    section 8.3 draws one identity from each stratum - so a constraint in two
    strata could enter one superblock twice and the stated proposal law would
    stop describing the sampler;
  * section 11.2 forbids moving items between pools once a pool is signed.

The tests use synthetic content throughout. No real scientific material is
authored here: a pair that cannot populate its pools is a pre-freeze feasibility
failure to be discovered by authoring, not asserted by a registry.
"""
import dataclasses

import pytest

from dci.v19 import pools
from dci.v19.pairs import PAIR_IDS
from dci.v19.pools import (ADAPTER_SPLIT, ALL_SPLITS, MATERIAL_SPLITS,
                           SUFFICIENCY_COUNTS, BackgroundEntry, Pool,
                           PoolViolation, assert_no_declared_incompatibility,
                           assert_one_stratum_per_constraint, assert_pool_excludes,
                           assert_splits_disjoint, declare_pool)
from dci.v19.resolution import UnresolvedDependency
from dci.v19.sampling import STRATA

pytestmark = pytest.mark.cpu


def entry(constraint_id="bg1", stratum="lexical_content", **kw):
    defaults = dict(generative_scope="whole_text", output_schema="plain_text",
                    verifier_hash="sha256:v", canonical_wording_hash="sha256:w",
                    provenance="authored 2026-08-11 under content procedure v1")
    return BackgroundEntry(constraint_id=constraint_id, stratum=stratum,
                           **{**defaults, **kw})


def populated(pool_id="p1.tasks.confirmation", pair="p1", kind="task",
              split="confirmation", items=("t1", "t2"), stratum=""):
    return declare_pool(pool_id, pair, kind, split, rule="synthetic",
                        stratum=stratum).populate(list(items), by="test")


# -------------------------------------------------------------- the vocabulary
def test_the_six_material_splits_are_the_preregistered_ones():
    assert MATERIAL_SPLITS == ("development", "parameter_calibration",
                               "reference_construction", "independent_validation",
                               "confirmation", "terminal_falsification")


def test_the_adapter_bank_is_tracked_outside_the_six():
    """Section 11.1 permits it only if disjoint from every DCI content pool."""
    assert ADAPTER_SPLIT not in MATERIAL_SPLITS
    assert ADAPTER_SPLIT in ALL_SPLITS


def test_there_are_exactly_three_background_strata():
    assert STRATA == ("lexical_content", "structural_format", "relational_order")


def test_the_sufficiency_counts_cover_section_eleven_two():
    for required in ("eligible_tasks", "candidate_reference_identities",
                     "unrelated_targets", "audit_true_pass_examples",
                     "audit_true_fail_examples",
                     "feasible_background_candidates",
                     "terminal_falsification_items"):
        assert required in SUFFICIENCY_COUNTS


# ------------------------------------------------------------ the declaration
def test_every_pair_declares_all_six_splits_of_task_material():
    declared = pools.declared_pools()
    for pair in PAIR_IDS:
        splits = {p.split for p in declared if p.pair == pair and p.kind == "task"}
        assert splits == set(MATERIAL_SPLITS)


def test_every_pair_declares_all_three_confirmation_background_strata():
    declared = pools.declared_pools()
    for pair in PAIR_IDS:
        strata = {p.stratum for p in declared
                  if p.pair == pair and p.kind == "background"}
        assert strata == set(STRATA)


def test_no_declared_pool_arrives_with_content():
    for pool in pools.declared_pools():
        assert not pool.populated and not pool.signed
        assert pool.contents.status == "BLOCKED_BY_CONTENT"


def test_reading_an_unpopulated_pool_refuses():
    with pytest.raises(UnresolvedDependency):
        pools.declared_pools()[0].items


def test_the_coupling_probe_pool_records_the_epsilon_dependency():
    """Expansion past 2,000 probes needs exact epsilon frozen first (7.7)."""
    probe = next(p for p in pools.declared_pools()
                 if p.pool_id == "p1.coupling_probes")
    assert "2,000 base outputs" in probe.contents.rule
    assert "exact epsilon" in probe.contents.note


def test_the_audit_pool_records_that_a_missing_truth_class_is_not_zero_error():
    audit = next(p for p in pools.declared_pools() if p.pool_id == "p2.audit")
    assert "missing evidence, not zero error" in audit.contents.note


def test_the_declared_slot_table_is_all_pending_content():
    table = pools.declared_slots()
    assert len(table) == len(pools.declared_pools())
    assert table.statuses() == {"BLOCKED_BY_CONTENT": len(table)}


def test_the_sufficiency_counts_are_declared_per_pair():
    table = pools.sufficiency_slots()
    assert len(table) == len(PAIR_IDS) * len(SUFFICIENCY_COUNTS)
    assert not table.resolved()


# ----------------------------------------------------------- pool well-formedness
def test_a_background_pool_must_name_a_stratum():
    with pytest.raises(PoolViolation, match="must name one of the three strata"):
        declare_pool("x", "p1", "background", "confirmation", rule="r")


def test_only_a_background_pool_may_name_a_stratum():
    with pytest.raises(PoolViolation, match="only a background pool"):
        declare_pool("x", "p1", "task", "confirmation", rule="r",
                     stratum="lexical_content")


@pytest.mark.parametrize("split", ["confirmatory", "", "pilot", None])
def test_an_unknown_split_is_refused(split):
    with pytest.raises(PoolViolation, match="split"):
        declare_pool("x", "p1", "task", split, rule="r")


@pytest.mark.parametrize("kind", ["prompt", "", None])
def test_an_unknown_pool_kind_is_refused(kind):
    with pytest.raises(PoolViolation, match="kind"):
        declare_pool("x", "p1", kind, "confirmation", rule="r")


def test_a_pool_for_an_unknown_pair_is_refused():
    with pytest.raises(PoolViolation, match="neither a v19 pair"):
        declare_pool("x", "p4", "task", "confirmation", rule="r")


def test_a_shared_pool_is_permitted():
    assert declare_pool("x", "shared", "manipulation_prompt", ADAPTER_SPLIT,
                        rule="r").pair == "shared"


# ------------------------------------------------------- populate, sign, freeze
def test_populating_records_content_and_leaves_the_pool_unsigned():
    got = populated()
    assert got.items == ("t1", "t2") and not got.signed


def test_populating_with_nothing_is_a_feasibility_failure_not_content():
    with pytest.raises(PoolViolation, match="feasibility failure to report"):
        declare_pool("x", "p1", "task", "confirmation", rule="r").populate(
            [], by="test")


def test_signing_requires_content():
    with pytest.raises(PoolViolation, match="prerequisite, not a consequence"):
        declare_pool("x", "p1", "task", "confirmation", rule="r").sign(by="me")


def test_signing_requires_a_signer():
    with pytest.raises(PoolViolation, match="requires a signer"):
        populated().sign(by="")


def test_a_signed_pool_cannot_be_signed_again():
    signed = populated().sign(by="investigator")
    with pytest.raises(PoolViolation, match="items cannot move between pools"):
        signed.sign(by="investigator")


def test_a_signed_pool_cannot_be_repopulated():
    """Section 11.2: once signed and hashed, movement between pools is barred."""
    signed = populated().sign(by="investigator")
    with pytest.raises(PoolViolation, match="contents are frozen"):
        signed.populate(["t3"], by="second thoughts")


def test_a_pool_cannot_be_constructed_as_signed_but_empty():
    empty = declare_pool("x", "p1", "task", "confirmation", rule="r")
    with pytest.raises(PoolViolation, match="freeze the absence of material"):
        Pool(pool_id="x", pair="p1", kind="task", split="confirmation",
             contents=empty.contents, signed_by="investigator")


# ------------------------------------------------------------- the fingerprint
def test_the_fingerprint_is_deterministic_and_order_independent():
    a = populated(items=("t1", "t2", "t3"))
    b = populated(items=("t3", "t1", "t2"))
    assert a.fingerprint == b.fingerprint == a.fingerprint
    assert len(a.fingerprint) == 64


def test_the_fingerprint_changes_with_the_content():
    assert populated(items=("t1",)).fingerprint != populated(
        items=("t1", "t2")).fingerprint


def test_the_fingerprint_changes_with_the_pool_identity():
    assert populated(split="confirmation").fingerprint != populated(
        split="development").fingerprint


def test_an_unpopulated_pool_has_no_fingerprint():
    """A stable identifier for nothing would later appear to prove no change."""
    with pytest.raises(UnresolvedDependency):
        declare_pool("x", "p1", "task", "confirmation", rule="r").fingerprint


def test_a_full_entry_and_a_bare_id_do_not_share_a_fingerprint():
    """This used to be asserted the other way round, which WAS the defect.

    A pool holding the complete section 8.2 entry is not the same signed material
    as a pool holding only its label, so the two must not hash alike.
    """
    a = populated(pool_id="p1.backgrounds.lexical_content", kind="background",
                  stratum="lexical_content", items=(entry("bg1"),))
    b = populated(pool_id="p1.backgrounds.lexical_content", kind="background",
                  stratum="lexical_content", items=("bg1",))
    assert a.fingerprint != b.fingerprint


# -------------------------------------------------------------- disjoint splits
def test_disjoint_splits_pass():
    assert_splits_disjoint([populated(split="confirmation", items=("t1", "t2")),
                            populated(split="development", items=("t3", "t4"))])


def test_an_item_in_two_splits_is_refused():
    """The firewall failure that is otherwise entirely silent."""
    with pytest.raises(PoolViolation, match="more than one material split"):
        assert_splits_disjoint([
            populated(split="confirmation", items=("t1", "shared_task")),
            populated(split="reference_construction", items=("shared_task",))])


def test_the_error_names_the_shared_item_and_its_splits():
    with pytest.raises(PoolViolation, match="leaky in"):
        assert_splits_disjoint([
            populated(split="confirmation", items=("leaky",)),
            populated(split="parameter_calibration", items=("leaky",))])


def test_the_same_item_twice_in_one_split_is_not_a_split_violation():
    """Two pools of one split may legitimately share; the firewall is by split."""
    assert_splits_disjoint([populated(split="confirmation", items=("t1",)),
                            populated(split="confirmation", items=("t1",))])


def test_unpopulated_pools_cannot_be_shown_disjoint_and_are_skipped():
    assert_splits_disjoint(list(pools.declared_pools()))


def test_the_adapter_bank_must_be_disjoint_from_dci_content():
    with pytest.raises(PoolViolation, match="more than one material split"):
        assert_splits_disjoint([
            populated(split="confirmation", items=("prompt_a",)),
            populated(pool_id="shared.manipulation_prompts", pair="shared",
                      kind="manipulation_prompt", split=ADAPTER_SPLIT,
                      items=("prompt_a",))])


# ------------------------------------------------------------------ one stratum
def test_one_stratum_per_constraint_passes():
    assert_one_stratum_per_constraint([
        populated(pool_id="a", kind="background", stratum="lexical_content",
                  items=(entry("bg1", "lexical_content"),)),
        populated(pool_id="b", kind="background", stratum="structural_format",
                  items=(entry("bg2", "structural_format"),))])


def test_a_constraint_in_two_strata_is_refused():
    """Section 8.3 draws one per stratum, so this could double-draw it."""
    with pytest.raises(PoolViolation, match="enter a superblock twice"):
        assert_one_stratum_per_constraint([
            populated(pool_id="a", kind="background", stratum="lexical_content",
                      items=("bg1",)),
            populated(pool_id="b", kind="background",
                      stratum="relational_order", items=("bg1",))])


def test_an_entry_filed_in_the_wrong_stratum_pool_is_refused():
    with pytest.raises(PoolViolation, match="but declares stratum"):
        assert_one_stratum_per_constraint([
            populated(pool_id="a", kind="background", stratum="lexical_content",
                      items=(entry("bg1", "structural_format"),))])


def test_non_background_pools_are_not_stratum_checked():
    assert_one_stratum_per_constraint([populated(items=("t1",))])


# --------------------------------------------------------------- exclusions
def test_a_pool_containing_the_pairs_own_focal_is_refused():
    """Section 8.2: neither pool may contain the pair's target or focal."""
    with pytest.raises(PoolViolation, match="excluded item"):
        assert_pool_excludes(
            populated(items=("t1", "v19:p1.focal.transitive_order")),
            {"v19:p1.focal.transitive_order": "the pair's own focal constraint"})


def test_the_exclusion_error_says_which_rule_was_broken():
    with pytest.raises(PoolViolation, match="admitted reference"):
        assert_pool_excludes(populated(items=("ref_a",)),
                             {"ref_a": "an admitted reference"})


def test_a_clean_pool_passes_the_exclusion_check():
    assert_pool_excludes(populated(items=("t1", "t2")), {"forbidden": "why"})


def test_an_unpopulated_pool_cannot_be_shown_to_exclude_anything():
    assert_pool_excludes(declare_pool("x", "p1", "task", "confirmation",
                                      rule="r"), {"anything": "why"})


# ---------------------------------------------------- declared incompatibility
def test_declared_incompatible_constraints_cannot_co_occur():
    with pytest.raises(PoolViolation, match="declared incompatible"):
        assert_no_declared_incompatibility([
            entry("bg1", incompatible_with=("bg2",)),
            entry("bg2", "structural_format")])


def test_compatible_constraints_pass():
    assert_no_declared_incompatibility([
        entry("bg1", incompatible_with=("bg9",)),
        entry("bg2", "structural_format")])


def test_the_pairwise_check_says_it_is_not_a_whole_composition_proof():
    """Section 8.7: pairwise compatibility is explicitly insufficient."""
    with pytest.raises(PoolViolation, match="whole-composition certification"):
        assert_no_declared_incompatibility([
            entry("bg1", incompatible_with=("bg2",)),
            entry("bg2", "structural_format")])


def test_a_self_incompatible_entry_is_refused():
    with pytest.raises(PoolViolation, match="incompatible with itself"):
        entry("bg1", incompatible_with=("bg1",))


# ------------------------------------------------------------ background entries
def test_a_background_entry_requires_every_field_section_eight_two_lists():
    for missing in ("output_schema", "verifier_hash", "canonical_wording_hash",
                    "provenance"):
        with pytest.raises(PoolViolation, match=missing):
            entry(**{missing: ""})


def test_a_background_entry_outside_the_three_strata_is_refused():
    with pytest.raises(PoolViolation, match="partitioned into exactly"):
        entry("bg1", "semantic_content")


def test_an_unparameterised_background_entry_is_permitted():
    assert entry("bg1").parameter_distribution == ""


# ---------------------------------------------------------------- the reports
def test_the_sufficiency_report_counts_without_judging():
    report = pools.sufficiency_report(list(pools.declared_pools()))
    assert set(report) == set(PAIR_IDS)
    for pair in PAIR_IDS:
        assert report[pair]["signed_pools"] == []
        assert len(report[pair]["unpopulated_pools"]) > 0
        assert all(v is None for v in
                   report[pair]["task_items_by_split"].values())


def test_the_sufficiency_report_reflects_authored_material():
    declared = list(pools.declared_pools())
    filled = [p.populate(["a", "b", "c"], by="test")
              if p.pool_id == "p1.tasks.confirmation" else p
              for p in declared]
    report = pools.sufficiency_report(filled)
    assert report["p1"]["task_items_by_split"]["confirmation"] == 3
    assert report["p2"]["task_items_by_split"]["confirmation"] is None


def test_confirmation_readiness_lists_what_is_not_signed():
    with pytest.raises(UnresolvedDependency) as caught:
        pools.assert_ready_for_confirmation(list(pools.declared_pools()))
    assert "has no authored content" in str(caught.value)


def test_a_populated_but_unsigned_pool_is_not_ready():
    with pytest.raises(UnresolvedDependency, match="populated but unsigned"):
        pools.assert_ready_for_confirmation([populated()])


def test_a_signed_populated_pool_is_ready():
    pools.assert_ready_for_confirmation([populated().sign(by="investigator")])


# ---------------------------------------- content identity versus overlap identity
#
# A pool item has two identities answering different questions, and collapsing
# them breaks whichever one it was not designed for. Content identity answers
# "has this material changed?" and is what section 11.2's signature must cover.
# Overlap identity answers "is this the same scientific item?" and must stay
# id-sensitive, because the same constraint in two splits is leakage even when one
# copy's metadata was edited.

MATERIAL_FIELDS = [
    ("verifier_hash", "sha256:CHANGED"),
    ("canonical_wording_hash", "sha256:CHANGED"),
    ("output_schema", "json_object"),
    ("parameter_distribution", "Uniform{3,4,5}"),
    ("incompatible_with", ("bg9",)),
    ("entails", ("bg7",)),
    ("provenance", "authored later under content procedure v2"),
    ("generative_scope", "sentence"),
]


def bg_pool(*entries, split="confirmation"):
    return populated(pool_id="p1.backgrounds.lexical_content", kind="background",
                     stratum="lexical_content", items=entries, split=split)


@pytest.mark.parametrize("field,value", MATERIAL_FIELDS)
def test_changing_any_scientifically_material_field_changes_the_fingerprint(
        field, value):
    """Section 8.2 lists these as the fields that determine interpretation.

    Before the repair every one of them left the signed fingerprint identical, so
    the signature certified nothing it claimed to.
    """
    base = bg_pool(entry("bg1")).fingerprint
    assert bg_pool(entry("bg1", **{field: value})).fingerprint != base, field


def test_changing_the_stratum_changes_the_fingerprint():
    base = bg_pool(entry("bg1", "lexical_content")).fingerprint
    other = populated(pool_id="p1.backgrounds.structural_format",
                      kind="background", stratum="structural_format",
                      items=(entry("bg1", "structural_format"),)).fingerprint
    assert other != base


def test_changing_the_constraint_id_changes_the_fingerprint():
    assert bg_pool(entry("bg1")).fingerprint != bg_pool(entry("bg2")).fingerprint


def test_an_identical_entry_reproduces_the_same_fingerprint():
    assert bg_pool(entry("bg1")).fingerprint == bg_pool(entry("bg1")).fingerprint


def test_ordering_remains_canonical_for_full_entries():
    a, b = entry("bg1"), entry("bg2", "lexical_content")
    assert bg_pool(a, b).fingerprint == bg_pool(b, a).fingerprint


def test_multiplicity_still_changes_the_fingerprint():
    """A pool is a population: listing an item twice doubles its draw probability."""
    e = entry("bg1")
    assert bg_pool(e, e).fingerprint != bg_pool(e).fingerprint


def test_two_entries_sharing_an_id_but_not_content_are_distinct_material():
    a = bg_pool(entry("bg1", verifier_hash="sha256:V1")).fingerprint
    b = bg_pool(entry("bg1", verifier_hash="sha256:V2")).fingerprint
    assert a != b


# ------------------------------------------------- overlap keeps both notions
def test_the_same_id_with_modified_content_is_still_cross_split_leakage():
    """The regression that a content-only key would have introduced."""
    dev = bg_pool(entry("bg1", verifier_hash="sha256:V1"), split="development")
    conf = bg_pool(entry("bg1", verifier_hash="sha256:V2"), split="confirmation")
    with pytest.raises(PoolViolation, match="more than one material split"):
        assert_splits_disjoint([dev, conf])


def test_renamed_identical_content_is_caught_as_leakage():
    """A copy under a new id is the same scientific material (section 8.2)."""
    dev = bg_pool(entry("bg1"), split="development")
    renamed = dataclasses.replace(entry("bg1"), constraint_id="bg1_copy")
    conf = bg_pool(renamed, split="confirmation")
    with pytest.raises(PoolViolation, match="more than one material split"):
        assert_splits_disjoint([dev, conf])


def test_distinct_id_and_distinct_content_are_not_treated_as_overlap():
    dev = bg_pool(entry("bg1"), split="development")
    conf = bg_pool(entry("bg2", verifier_hash="sha256:other"),
                   split="confirmation")
    assert_splits_disjoint([dev, conf])


def test_a_renamed_forbidden_item_is_still_excluded():
    from dci.v19.pools import _material_key
    original = entry("bg1")
    renamed = dataclasses.replace(original, constraint_id="innocuous")
    with pytest.raises(PoolViolation, match="excluded item"):
        assert_pool_excludes(bg_pool(renamed),
                             {f"material:{_material_key(original)}":
                              "the pair's own focal constraint, renamed"})


def test_the_signing_key_includes_the_id_but_the_overlap_key_does_not():
    """The two identities are deliberately different, and both are needed."""
    from dci.v19.pools import _content_key, _material_key
    original = entry("bg1")
    renamed = dataclasses.replace(original, constraint_id="bg1_copy")
    assert _content_key(original) != _content_key(renamed)     # signing sees it
    assert _material_key(original) == _material_key(renamed)   # overlap sees through


def test_one_stratum_uses_the_declared_id_not_the_content_hash():
    """Two edited copies under one id are still one constraint in two strata."""
    a = populated(pool_id="a", kind="background", stratum="lexical_content",
                  items=(entry("bg1", "lexical_content"),))
    b = populated(pool_id="b", kind="background", stratum="relational_order",
                  items=(entry("bg1", "relational_order",
                               verifier_hash="sha256:edited"),))
    with pytest.raises(PoolViolation, match="enter a superblock twice"):
        assert_one_stratum_per_constraint([a, b])


# ------------------------- the readiness gate ENFORCES, it does not merely check
#
# Before this, four correct helper assertions existed with unit tests and no
# production caller at all. Signing each pool individually proves nothing about
# the partition: section 11.1's firewall is a property of the SET, so two
# separately valid signed pools can share an item and both signatures stay valid.

def signed(pool_id, split, items, **kw):
    return populated(pool_id=pool_id, split=split, items=items, **kw).sign(
        by="investigator")


def test_the_gate_rejects_individually_signed_but_overlapping_splits():
    """The reported defect: this used to pass."""
    dev = signed("p1.tasks.development", "development", ("shared_task", "d2"))
    conf = signed("p1.tasks.confirmation", "confirmation", ("shared_task", "c2"))
    with pytest.raises(PoolViolation, match="more than one material split"):
        pools.assert_ready_for_confirmation([dev, conf])


def test_the_gate_accepts_disjoint_signed_splits():
    dev = signed("p1.tasks.development", "development", ("d1", "d2"))
    conf = signed("p1.tasks.confirmation", "confirmation", ("c1", "c2"))
    pools.assert_ready_for_confirmation([dev, conf])


def test_the_gate_rejects_a_renamed_duplicate_across_splits():
    original = entry("bg1")
    renamed = dataclasses.replace(original, constraint_id="bg1_copy")
    dev = signed("a", "development", (original,), kind="background",
                 stratum="lexical_content")
    conf = signed("b", "confirmation", (renamed,), kind="background",
                  stratum="lexical_content")
    with pytest.raises(PoolViolation, match="more than one material split"):
        pools.assert_ready_for_confirmation([dev, conf])


def test_the_gate_rejects_one_constraint_in_two_strata():
    a = signed("a", "confirmation", (entry("bg1", "lexical_content"),),
               kind="background", stratum="lexical_content")
    b = signed("b", "confirmation", (entry("bg1", "relational_order"),),
               kind="background", stratum="relational_order")
    with pytest.raises(PoolViolation, match="enter a superblock twice"):
        pools.assert_ready_for_confirmation([a, b])


def test_the_gate_rejects_a_pairs_own_focal_constraint():
    """Section 8.2: neither pool may contain the pair's target or focal."""
    conf = signed("p1.tasks.confirmation", "confirmation",
                  ("c1", "v19:p1.focal.transitive_order"))
    with pytest.raises(PoolViolation, match="own focal constraint"):
        pools.assert_ready_for_confirmation([conf])


def test_the_gate_rejects_a_pairs_own_target_constraint():
    conf = signed("p3.tasks.confirmation", "confirmation",
                  ("c1", "v19:p3.target.exact_sentence_count"), pair="p3")
    with pytest.raises(PoolViolation, match="own target constraint"):
        pools.assert_ready_for_confirmation([conf])


def test_the_gate_rejects_declared_incompatible_background_entries():
    a = signed("a", "confirmation", (entry("bg1", incompatible_with=("bg2",)),),
               kind="background", stratum="lexical_content")
    b = signed("b", "confirmation", (entry("bg2", "structural_format"),),
               kind="background", stratum="structural_format")
    with pytest.raises(PoolViolation, match="declared incompatible"):
        pools.assert_ready_for_confirmation([a, b])


def test_the_gate_still_rejects_unsigned_and_unpopulated_pools_first():
    with pytest.raises(UnresolvedDependency, match="has no authored content"):
        pools.assert_ready_for_confirmation(list(pools.declared_pools()))
    with pytest.raises(UnresolvedDependency, match="populated but unsigned"):
        pools.assert_ready_for_confirmation([populated()])


def test_the_exclusion_map_comes_from_the_pair_registry():
    """Not a hand-maintained list: it is derived, so it cannot drift."""
    got = pools.forbidden_items("p2")
    assert got["id:v19:p2.target.mandatory_words"] == \
        "the pair's own target constraint"
    assert got["id:v19:p2.focal.all_words_unique"] == \
        "the pair's own focal constraint"


def test_the_exclusion_map_omits_references_until_stage_eight_admits_them():
    """It cannot exclude identities that do not exist yet."""
    got = pools.forbidden_items("p1")
    assert not any("admitted reference" in why for why in got.values())
    assert len(got) == 2


def test_an_explicit_exclusion_map_overrides_the_derived_one():
    conf = signed("p1.tasks.confirmation", "confirmation", ("banned_item",))
    pools.assert_ready_for_confirmation([conf], exclusions={})
    with pytest.raises(PoolViolation, match="excluded item"):
        pools.assert_ready_for_confirmation(
            [conf], exclusions={"id:banned_item": "a Stage 8 reference"})


def test_semantic_duplicate_review_is_a_pending_human_decision():
    """Section 8.7 assigns semantic equivalence to review, not to code."""
    slot = pools.semantic_duplicate_review("p1")
    assert slot.status == "BLOCKED_BY_PROSPECTIVE_DECISION"
    assert "two independent human reviews" in slot.rule
    assert "third reviewer" in slot.rule
    assert "not semantic equivalence" in slot.note
    with pytest.raises(UnresolvedDependency):
        slot.get()


def test_the_gate_does_not_claim_to_settle_semantic_equivalence():
    """A near-duplicate with different wording passes the deterministic gate.

    That is correct behaviour, not a hole: the protocol assigns this judgement to
    human review, and asserting it automatically would fabricate a certification.
    """
    dev = signed("a", "development", (entry("bg1"),), kind="background",
                 stratum="lexical_content")
    near = dataclasses.replace(entry("bg2", "lexical_content"),
                               canonical_wording_hash="sha256:paraphrase")
    conf = signed("b", "confirmation", (near,), kind="background",
                  stratum="lexical_content")
    pools.assert_ready_for_confirmation([dev, conf])
    assert pools.semantic_duplicate_review("p1").pending
