"""The causal field-role registry: exactly one pre-frozen role per field.

Preregistration section 11.8. "Every analysis field has exactly one pre-frozen
role", and the consequence that matters is the next sentence: "Primary estimators
reject post-treatment and diagnostic fields as covariates, weights, filters,
matching coordinates, or denominator definitions."

That prohibition is easy to state and easy to violate by accident. Realised
reasoning use, cap-hit, final-answer length, latency and truncation state are all
recorded for every generation, all plausible-looking, and all caused by the
treatment - so conditioning on any of them would change the estimand while looking
like a sensible adjustment. Section 11.8 cites the standard post-treatment
argument for exactly this reason.

So the roles are declared once, here, and `assert_primary_covariate` is the check
a primary estimator calls before accepting any field name. Declaring the roles
without a mechanical gate would leave the rule as documentation.
"""
from __future__ import annotations

from typing import Iterable, Mapping

# Section 11.8's seven roles, with the fields the protocol names under each.
FIELD_ROLES: Mapping[str, tuple[str, ...]] = {
    "identity": (
        "protocol", "pair", "accepted_draw_index", "context_fingerprint",
        "superblock_id", "cell_id", "generation_id", "attempt_id"),
    "treatment": (
        "arm", "added_slot_occupant", "hard_budget", "budget_id", "load",
        "presentation_order"),
    "pretreatment_design": (
        "task", "topic", "target_id", "focal_id", "reference_id", "parameters",
        "canonical_wording", "background_set", "s_max", "prompt_template",
        "sampling_distribution", "background_permutation", "construction_field"),
    "apparatus": (
        "checkpoint_revision", "tokenizer", "chat_template", "controller_hash",
        "verifier_hash", "inference_hash", "container_digest",
        "accelerator_backend", "gpu_class", "gpu_identity", "driver_version",
        "runtime_version", "dtype", "attention_backend", "manifest_hash",
        "seed_map_hash", "dependency_lock"),
    "post_treatment_instrumentation": (
        "realised_reasoning_use", "u_r", "cap_hit", "reasoning_ended_naturally",
        "final_answer_length", "latency", "finish_reason", "truncation_state",
        "final_truncated", "cap_forced_transition"),
    "outcome": (
        "target_verdict", "f_a"),
    "diagnostic": (
        "focal_compliance", "reference_compliance", "partial_compliance_state",
        "exploit_suspected", "generation_state", "prescribed_summary"),
}

# The two roles a primary estimator may never consume as a covariate, weight,
# filter, matching coordinate, or denominator definition (section 11.8).
FORBIDDEN_IN_PRIMARY = ("post_treatment_instrumentation", "diagnostic")

# The permitted uses a primary formula has for a field, for error messages.
PRIMARY_USES = ("covariate", "weight", "filter", "matching coordinate",
                "denominator definition")


class FieldRoleViolation(ValueError):
    """A primary estimator reached for a field whose role forbids it."""


def _index() -> dict[str, str]:
    out: dict[str, str] = {}
    for role, fields in FIELD_ROLES.items():
        for field in fields:
            if field in out:
                raise ValueError(
                    f"{field!r} is declared under both {out[field]!r} and "
                    f"{role!r}; section 11.8 gives every field exactly one role")
            out[field] = role
    return out


_ROLE_OF = _index()


def role_of(field: str) -> str:
    """The single declared role of a field, or refuse.

    An undeclared field is an error rather than a default: a field with no role
    has not been through the pre-freeze classification section 11.8 requires, and
    guessing would be exactly the discretion the registry removes.
    """
    try:
        return _ROLE_OF[field]
    except KeyError:
        raise FieldRoleViolation(
            f"{field!r} has no declared causal role. Section 11.8 requires every "
            "analysis field to be classified before freeze, so an unclassified "
            "field cannot enter any analysis. Declare it in FIELD_ROLES."
        ) from None


def fields_with_role(role: str) -> tuple[str, ...]:
    if role not in FIELD_ROLES:
        raise FieldRoleViolation(
            f"{role!r} is not one of the declared roles: {sorted(FIELD_ROLES)}")
    return FIELD_ROLES[role]


def assert_primary_covariate(field: str, use: str = "covariate") -> str:
    """Refuse a field whose role bars it from a primary formula.

    `use` names how the primary analysis wants the field, so the error explains
    which of section 11.8's five prohibited uses was attempted.
    """
    role = role_of(field)
    if role in FORBIDDEN_IN_PRIMARY:
        raise FieldRoleViolation(
            f"{field!r} has role {role!r} and cannot be used as a {use} in a "
            "primary estimator (section 11.8). It is caused by the treatment, so "
            "conditioning on it changes the estimand rather than adjusting for "
            "confounding. It may be described or studied secondarily, but it "
            "cannot redefine the causal replacement contrast")
    return field


def assert_primary_formula(fields: Iterable[str], use: str = "covariate") -> None:
    """Every field a primary formula consumes, checked together.

    Reports all offending fields at once: discovering them one exception at a
    time invites removing them one at a time until the formula happens to pass.
    """
    offending = []
    for field in fields:
        role = role_of(field)
        if role in FORBIDDEN_IN_PRIMARY:
            offending.append(f"{field} ({role})")
    if offending:
        raise FieldRoleViolation(
            f"a primary estimator cannot consume {len(offending)} field(s) as a "
            f"{use}: {', '.join(offending)}. Section 11.8 bars post-treatment "
            "instrumentation and diagnostic fields from primary covariates, "
            "weights, filters, matching coordinates and denominator definitions")


def assert_roles_well_formed() -> None:
    """Every declared field has exactly one role, and every role is populated."""
    _index()                                   # raises on any double declaration
    empty = sorted(role for role, fields in FIELD_ROLES.items() if not fields)
    if empty:
        raise ValueError(f"roles declared with no fields: {empty}")
    for role in FORBIDDEN_IN_PRIMARY:
        if role not in FIELD_ROLES:
            raise ValueError(
                f"{role!r} is barred from primary formulas but is not a declared "
                "role, so the prohibition would never fire")


def audit() -> tuple[dict[str, object], ...]:
    """One row per field, for the completion audit and the freeze bundle."""
    return tuple(
        {"field": field, "role": role,
         "permitted_in_primary": role not in FORBIDDEN_IN_PRIMARY}
        for role, fields in FIELD_ROLES.items() for field in fields)
