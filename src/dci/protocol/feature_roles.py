"""Executable enforcement of the frozen causal-role declaration.

WHY A HASH IS NOT ENOUGH
------------------------
`FEATURE_ROLES` assigns every feature a causal role -- eligibility, caliper,
diagnostic, ranking-only, mechanism-never-matched -- and the table is hashed into
the protocol record. A hash certifies WHAT THE PROTOCOL SAYS. It says nothing
about what the code does, so pre-repair the declaration and the machinery could
disagree indefinitely and both the freeze and the export would look correct.

The distinctions matter causally, not stylistically:
  * a `caliper` feature is a MATCHING variable and defines the reference class;
  * a `diagnostic` feature is reported and must never narrow that class;
  * a `mechanism_never_matched` feature lies on the causal pathway under study,
    so matching on it would remove part of the effect being measured;
  * a `post_treatment_reported_never_matched` feature is an outcome of the
    treatment, so matching on it conditions on a consequence.

`verify_feature_roles` compares the declaration against the actual caliper index
and fails the run when they disagree.
"""
from __future__ import annotations

from typing import Iterable

# Roles whose features MUST appear in the caliper/matching machinery.
MATCHING_ROLES = frozenset({"caliper"})
# Roles whose features must NEVER appear there.
NON_MATCHING_ROLES = frozenset({
    "diagnostic",
    "ranking_after_eligibility",
    "weighting_after_admissibility",
    "post_treatment_reported_never_matched",
    "mechanism_never_matched",
    "eligibility",
    "exact_eligibility",
})
KNOWN_ROLES = MATCHING_ROLES | NON_MATCHING_ROLES


def role_of_component(component: str, family_of, roles: dict[str, str]) -> str:
    """The declared role of a signature component, via its family."""
    if component in roles:
        return roles[component]
    return roles.get(family_of(component), "undeclared")


def verify_feature_roles(roles: dict[str, str], caliper_components: Iterable[str],
                         family_of, coupling_component: str,
                         coupling_role: str) -> list[str]:
    """Problems, as strings. Empty means the declaration matches the code.

    `caliper_components` is the ACTUAL caliper index the admission rule iterates,
    so this compares the declaration to behaviour rather than to another list.
    """
    problems: list[str] = []

    unknown = {k: v for k, v in roles.items() if v not in KNOWN_ROLES}
    if unknown:
        problems.append(f"features declared with unknown roles: {unknown}")

    components = list(caliper_components)
    families_in_use = {family_of(c) for c in components} | set(components)

    # 1. Every feature the code matches on must be DECLARED as a matching feature.
    for comp in components:
        role = role_of_component(comp, family_of, roles)
        if role == "undeclared":
            problems.append(
                f"caliper component {comp!r} (family {family_of(comp)!r}) has no "
                "declared causal role, yet it constrains reference admission")
        elif role in NON_MATCHING_ROLES:
            problems.append(
                f"caliper component {comp!r} is declared {role!r}, which must "
                "never be a matching variable, yet it constrains admission")

    # 2. Every feature DECLARED as a caliper must actually be matched on -- with
    #    one legitimate exception: kappa is declared a caliper because it IS one
    #    under kappa_matched, and is audited rather than matched under
    #    primary_total. That switch is itself declared, so it is checked rather
    #    than excused.
    for feature, role in roles.items():
        if role not in MATCHING_ROLES:
            continue
        if feature == coupling_component:
            if coupling_role == "matched" and feature not in families_in_use:
                problems.append(
                    f"{feature!r} has coupling_role='matched' but is absent from "
                    "the caliper set")
            if coupling_role == "audit" and feature in families_in_use:
                problems.append(
                    f"{feature!r} has coupling_role='audit' but appears in the "
                    "caliper set, which would silently switch the estimand to "
                    "kappa_matched")
            continue
        if feature not in families_in_use:
            problems.append(
                f"{feature!r} is declared {role!r} but no caliper component "
                "belongs to it, so the declaration is not enforced anywhere")

    return problems


def audited_but_not_matched(roles: dict[str, str], coupling_component: str,
                            coupling_role: str) -> bool:
    """True when kappa is in its declared `primary_total` configuration."""
    return (coupling_role == "audit"
            and roles.get(coupling_component) in MATCHING_ROLES)
