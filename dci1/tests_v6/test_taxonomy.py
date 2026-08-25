"""C. The structural taxonomy, and §19 test 5 (§7.3, §7.4)."""
from __future__ import annotations

import pytest

from dci1v4.errors import InstrumentError
from dci1v6.protocol import constants as C
from dci1v6.protocol import taxonomy as T
from dci1v6.verifiers import constraints as K


def test_every_family_declares_all_thirteen_fields():
    for kind, family in K.FAMILIES.items():
        assert set(family.metadata) == set(T.METADATA_FIELDS), kind


def test_declared_metadata_agrees_with_the_predicate():
    """A family cannot declare a class or a tier its own form contradicts."""
    for kind, family in K.FAMILIES.items():
        T.assert_metadata_consistent(
            kind, family.metadata,
            form_class=family.constraint_class,
            form_operator=K.FORM_OPERATOR[family.form])


def test_inconsistent_metadata_is_rejected():
    meta = dict(K.FAMILIES["MK1"].metadata)
    meta["constraint_class"] = "budget"
    with pytest.raises(InstrumentError):
        T.assert_metadata_consistent("MK1", meta, form_class="production",
                                     form_operator="==")


def test_declared_tier_must_match_the_derived_tier():
    meta = dict(K.FAMILIES["MK1"].metadata)
    meta["structural_tier"] = 3
    with pytest.raises(InstrumentError):
        T.assert_metadata_consistent("MK1", meta, form_class="production",
                                     form_operator="==")


def test_tier_rule_is_relative_to_a_and_to_nothing_else():
    assert T.tier_of_metadata(T.A_STRUCTURAL_RECORD) == T.TIER_1
    near = dict(T.A_STRUCTURAL_RECORD, statistic_type="punctuation_character")
    assert T.tier_of_metadata(near) == T.TIER_2
    broad = dict(T.A_STRUCTURAL_RECORD, operator="<=")
    assert T.tier_of_metadata(broad) == T.TIER_3


def test_the_registered_tiers_are_what_the_protocol_says():
    assert len(K.TIER1_FAMILY_IDS) == 8
    assert len(K.TIER2_FAMILY_IDS) == 3
    assert len(K.TIER3_FAMILY_IDS) == 26
    assert K.N_FAMILIES == 37


def test_every_slot_refuses_a_family_whose_tier_it_does_not_admit():
    with pytest.raises(InstrumentError):
        K.assert_slot_allowed("RF1", T.SLOT_CORE)            # Tier 3 core
    with pytest.raises(InstrumentError):
        K.assert_slot_allowed("MK1", T.SLOT_NEAR_FORM)       # Tier 1 near-form
    with pytest.raises(InstrumentError):
        K.assert_slot_allowed("MK1", T.SLOT_BROAD_CLASS)     # Tier 1 broad
    K.assert_slot_allowed("MK1", T.SLOT_CORE)
    K.assert_slot_allowed("XC1", T.SLOT_CORE)
    K.assert_slot_allowed("XC1", T.SLOT_NEAR_FORM)
    K.assert_slot_allowed("RF1", T.SLOT_BROAD_CLASS)


def test_the_broad_class_slot_admits_budget_class_only():
    """CL7 and CL8 are Tier 3 and production class, so §13.10 refuses them."""
    for kind in ("CL7", "CL8"):
        assert K.family_tier(kind) == T.TIER_3
        assert K.FAMILIES[kind].constraint_class == K.CLASS_PRODUCTION
        with pytest.raises(InstrumentError):
            K.assert_slot_allowed(kind, T.SLOT_BROAD_CLASS)


def test_the_spectrum_slot_needs_its_core_family_tier():
    with pytest.raises(InstrumentError):
        K.assert_slot_allowed("MK1", T.SLOT_SPECTRUM)
    K.assert_slot_allowed("MK1", T.SLOT_SPECTRUM, core_family_tier=1)
    with pytest.raises(InstrumentError):
        K.assert_slot_allowed("MK1", T.SLOT_SPECTRUM, core_family_tier=2)


def test_the_core_set_needs_two_tier_one_members_and_three_groups():
    entries = [
        {"family": "MK1", "structural_tier": 1, "feature_group": "marker_thus",
         "discourse_role": "consecutive"},
        {"family": "MK3", "structural_tier": 1,
         "feature_group": "marker_though", "discourse_role": "contrastive"},
        {"family": "XC1", "structural_tier": 2, "feature_group": "semicolon",
         "discourse_role": "none"},
    ]
    out = T.assert_core_set_structure(entries, min_tier1=2, n_groups=3,
                                      min_roles=2,
                                      a_role=C.A_DISCOURSE_ROLE)
    assert out["n_tier1"] == 2
    assert "REFERENCE_ROLE_NOT_MATCHED" not in out["identification_statuses"]

    one_tier1 = [dict(entries[0], structural_tier=2), entries[1], entries[2]]
    with pytest.raises(InstrumentError):
        T.assert_core_set_structure(one_tier1, min_tier1=2, n_groups=3,
                                    min_roles=2, a_role=C.A_DISCOURSE_ROLE)


def test_none_is_not_a_discourse_role():
    """A Tier-2 member contributes no role, so it cannot supply the spread."""
    entries = [
        {"family": "MK1", "structural_tier": 1, "feature_group": "marker_thus",
         "discourse_role": "consecutive"},
        {"family": "MK2", "structural_tier": 1,
         "feature_group": "marker_hence", "discourse_role": "consecutive"},
        {"family": "XC1", "structural_tier": 2, "feature_group": "semicolon",
         "discourse_role": "none"},
    ]
    assert T.declared_roles(entries) == {"consecutive"}
    with pytest.raises(InstrumentError):
        T.assert_core_set_structure(entries, min_tier1=2, n_groups=3,
                                    min_roles=2, a_role=C.A_DISCOURSE_ROLE)


def test_role_not_matched_is_recorded_and_is_not_terminal():
    entries = [
        {"family": "MK1", "structural_tier": 1, "feature_group": "marker_thus",
         "discourse_role": "consecutive"},
        {"family": "MK5", "structural_tier": 1,
         "feature_group": "marker_indeed", "discourse_role": "emphatic"},
        {"family": "XC1", "structural_tier": 2, "feature_group": "semicolon",
         "discourse_role": "none"},
    ]
    out = T.assert_core_set_structure(entries, min_tier1=2, n_groups=3,
                                      min_roles=2,
                                      a_role=C.A_DISCOURSE_ROLE)
    assert out["identification_statuses"] == ["REFERENCE_ROLE_NOT_MATCHED"]
