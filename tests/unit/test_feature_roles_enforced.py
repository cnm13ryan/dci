"""A hashed causal-role declaration must have executable consequences.

Pre-repair `FEATURE_ROLES` was hashed into the protocol and consumed by nothing,
so the declaration and the matching machinery could disagree while the freeze and
the export both looked correct.
"""
import pytest

from dci.protocol.feature_roles import (KNOWN_ROLES, MATCHING_ROLES,
                                        NON_MATCHING_ROLES,
                                        audited_but_not_matched,
                                        role_of_component,
                                        verify_feature_roles)

pytestmark = pytest.mark.cpu

ROLES = {
    "generative_scope": "exact_eligibility",
    "logical_compatibility": "eligibility",
    "verifier_validity": "eligibility",
    "d": "caliper",
    "g": "caliper",
    "r": "caliper",
    "kappa": "caliper",
    "s_d": "caliper", "s_g": "caliper", "s_r": "caliper",
    "s_max": "diagnostic",
    "mahalanobis_distance": "ranking_after_eligibility",
    "response_words": "post_treatment_reported_never_matched",
    "cross_sentence_planning_demand": "mechanism_never_matched",
}
WORDING = ("s_d", "s_g", "s_r")


def family_of(component: str) -> str:
    if component.startswith("g|"):
        return "g"
    if component.startswith("r|"):
        return "r"
    if component in WORDING or component == "s_max":
        return "s"
    return component


def _components(u=("ua", "ub"), orders=("target_first", "added_first"),
                with_kappa=False):
    comps = ["d"]
    comps += [f"g|{t}|{o}" for t in u for o in orders]
    comps += [f"r|{t}|{o}" for t in u for o in orders]
    if with_kappa:
        comps.append("kappa")
    comps += list(WORDING)
    return comps


def test_roles_are_partitioned_and_known():
    assert MATCHING_ROLES.isdisjoint(NON_MATCHING_ROLES)
    assert set(ROLES.values()) <= KNOWN_ROLES


def test_primary_total_configuration_is_clean():
    """kappa declared a caliper, role 'audit', absent from the caliper set."""
    problems = verify_feature_roles(ROLES, _components(with_kappa=False),
                                    family_of, "kappa", "audit")
    assert problems == [], problems
    assert audited_but_not_matched(ROLES, "kappa", "audit")


def test_kappa_matched_configuration_is_clean():
    problems = verify_feature_roles(ROLES, _components(with_kappa=True),
                                    family_of, "kappa", "matched")
    assert problems == [], problems
    assert not audited_but_not_matched(ROLES, "kappa", "matched")


def test_kappa_in_calipers_while_audited_is_caught():
    """This is the silent estimand switch from primary_total to kappa_matched."""
    problems = verify_feature_roles(ROLES, _components(with_kappa=True),
                                    family_of, "kappa", "audit")
    assert any("kappa_matched" in p for p in problems), problems


def test_kappa_matched_without_the_caliper_is_caught():
    problems = verify_feature_roles(ROLES, _components(with_kappa=False),
                                    family_of, "kappa", "matched")
    assert any("absent from the caliper set" in p for p in problems), problems


def test_a_diagnostic_feature_used_as_a_caliper_is_caught():
    """s_max is a summary of the three family instabilities: matching on it
    would double count, so it is declared diagnostic."""
    problems = verify_feature_roles(ROLES, [*_components(), "s_max"],
                                    family_of, "kappa", "audit")
    # s_max resolves to family 's', which IS a caliper family, so the check must
    # look at the component's own declaration before falling back to the family.
    assert any("s_max" in p for p in problems), problems


def test_post_treatment_feature_used_as_a_caliper_is_caught():
    problems = verify_feature_roles(ROLES, [*_components(), "response_words"],
                                    family_of, "kappa", "audit")
    assert any("response_words" in p and "never be a matching variable" in p
               for p in problems), problems


def test_mechanism_feature_used_as_a_caliper_is_caught():
    problems = verify_feature_roles(
        ROLES, [*_components(), "cross_sentence_planning_demand"],
        family_of, "kappa", "audit")
    assert any("cross_sentence_planning_demand" in p for p in problems), problems


def test_undeclared_caliper_component_is_caught():
    problems = verify_feature_roles(ROLES, [*_components(), "instruction_tokens"],
                                    family_of, "kappa", "audit")
    assert any("no declared causal role" in p for p in problems), problems


def test_declared_caliper_family_that_is_never_matched_is_caught():
    """A role can be declared and then not enforced anywhere. That is the defect."""
    problems = verify_feature_roles(
        ROLES, [c for c in _components() if not c.startswith("r|")],
        family_of, "kappa", "audit")
    assert any(p.startswith("'r' is declared") for p in problems), problems


def test_unknown_role_string_is_caught():
    roles = {**ROLES, "d": "sort_of_matched"}
    problems = verify_feature_roles(roles, _components(), family_of, "kappa",
                                    "audit")
    assert any("unknown roles" in p for p in problems), problems


def test_role_of_component_prefers_the_component_over_its_family():
    assert role_of_component("s_max", family_of, ROLES) == "diagnostic"
    assert role_of_component("g|ua|target_first", family_of, ROLES) == "caliper"
    assert role_of_component("nope", family_of, ROLES) == "undeclared"
