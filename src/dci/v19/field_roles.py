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

But that sentence is not the whole rule, and treating it as one produced two
defects. A denylist of the two roles it names admitted `target_verdict` as a
covariate, filter, weight, matching coordinate and denominator - conditioning the
primary estimator on its own result - and admitted a stored parameter as a matching
coordinate, which D7 fixes as EXCLUDED. Neither could be fixed by editing the
denylist: F_A genuinely IS the response variable, and a parameter is genuinely
admissible as pretreatment design while being inadmissible for that one use.

So legality is keyed on (role, use) rather than on role alone, with refusal as the
default: a cell absent from the matrix is forbidden until someone adds it with a
citation. Matching is handled separately again, because section 7.3 restricts it to
four computed empirical properties rather than to any stored field, which makes it
an allowlist rather than a role rule.
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

# Every way a primary analysis can consume a field. Section 11.8 names five
# prohibited uses; "outcome" and "diagnostic only" are added because legality
# depends on the use as well as the role, and without them the model cannot say
# that F_A is legitimately the response while being illegitimate as a covariate.
USES = ("outcome", "covariate", "weight", "filter", "matching coordinate",
        "denominator definition", "diagnostic only")

# The five uses section 11.8 lists, kept as a named group for error messages.
PRIMARY_USES = ("covariate", "weight", "filter", "matching coordinate",
                "denominator definition")

# Legacy name, retained because the two roles it held are still exactly the ones
# section 11.8 names in that sentence. It is no longer the whole rule.
FORBIDDEN_IN_PRIMARY = ("post_treatment_instrumentation", "diagnostic")

# ------------------------------------------------------- the permission matrix
#
# A flat role denylist could not express the protocol. Two cases prove it:
#
#   * `outcome`. Section 11.8's sentence names only post-treatment and diagnostic
#     fields, so a denylist built from it admitted `target_verdict` as a covariate,
#     filter, weight, matching coordinate and denominator - conditioning primary
#     estimation on its own result. The prohibition is real but comes from
#     elsewhere: section 12.1(2) assigns structural states "without consulting
#     effect direction", section 10.1 forbids dropping a delivered response for
#     its state, section 15.6 forbids dropping cells whose effects are
#     inconvenient, and section 7.4 bars construction from inspecting confirmatory
#     outcomes. Yet F_A *is* the response variable, so a denylist entry would have
#     been wrong too.
#
#   * `matching coordinate`. D7 fixes parameter severity as EXCLUDED from matching
#     while section 6.5 keeps parameters "archived and reported", so one
#     pretreatment field is legal in general and illegal for one specific use. No
#     role-keyed denylist can represent that.
#
# Hence legality is keyed on (role, use). Absent from the matrix means forbidden:
# the default is refusal, so a use added later is prohibited until someone states
# otherwise with a citation.
PERMISSION: Mapping[tuple[str, str], str] = {
    # identity - available for structure, and H_r is a count of superblocks.
    ("identity", "denominator definition"):
        "Appendix I requires H_r = H_p per primitive, a count of superblocks",
    ("identity", "diagnostic only"): "section 11.8 permits description",

    # treatment - the causal conditions themselves. Cell membership is what the
    # primitive family is indexed by, which is selection by design, not filtering
    # on realised data.
    ("treatment", "covariate"):
        "section 12.2 indexes the primitive family by (p, j, b, k, o)",
    ("treatment", "filter"):
        "section 12.2: a cell is defined by its treatment coordinates",
    ("treatment", "diagnostic only"): "section 11.8 permits description",

    # pretreatment design - frozen before treatment, so conditioning on it cannot
    # induce post-treatment bias. NOT admissible as a matching coordinate: D7.
    ("pretreatment_design", "covariate"):
        "section 11.8 lists pretreatment design as a distinct role from the two "
        "it bars from primary conditioning",
    ("pretreatment_design", "diagnostic only"):
        "section 6.5 keeps family-specific parameters archived and reported",

    # apparatus/provenance - invariant within a run by Appendix I, so there is no
    # variation to condition on; retained for description and audit.
    ("apparatus", "diagnostic only"):
        "Appendix I requires invariant apparatus hashes across the run",

    # post-treatment instrumentation - section 11.8's first barred role.
    ("post_treatment_instrumentation", "diagnostic only"):
        "section 11.8: may be described or studied secondarily",

    # outcome - the response variable, and nothing else.
    ("outcome", "outcome"):
        "section 12.1 defines D_ipj from the replicate mean of F_A",
    ("outcome", "diagnostic only"):
        "section 16.2 reports cell-level outcome summaries",

    # diagnostic - section 11.8's second barred role.
    ("diagnostic", "diagnostic only"):
        "section 11.8: prespecified non-primary summaries",
}

# Section 7.3's closed set of matching coordinates: "four empirical properties,
# measured on unrelated targets and marginalised over the candidate's frozen
# parameter distribution". These are computed comparability statistics, not
# stored analysis fields, so matching is an ALLOWLIST rather than a role rule.
# "Instruction length is reported and is not matched because literal canonical
# wording is part of the instruction-level treatment."
MATCHING_COORDINATES = ("isolated_difficulty", "outgoing_burden",
                        "incoming_vulnerability", "wording_instability")

REPORTED_BUT_NOT_MATCHED = ("instruction_length",)


class FieldRoleViolation(ValueError):
    """A primary estimator reached for a field whose role forbids that use."""


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


def permits(role: str, use: str) -> bool:
    """Whether the matrix allows this role in this use. Absent means forbidden."""
    if role not in FIELD_ROLES:
        raise FieldRoleViolation(f"{role!r} is not a declared role")
    if use not in USES:
        raise FieldRoleViolation(
            f"{use!r} is not a recognised primary-analysis use; known: {USES}")
    return (role, use) in PERMISSION


def permission_reason(role: str, use: str) -> str:
    """The citation permitting this role in this use, or raise if it does not."""
    if not permits(role, use):
        raise FieldRoleViolation(f"{role!r} may not be used as a {use}")
    return PERMISSION[(role, use)]


def _why_forbidden(field: str, role: str, use: str) -> str:
    if role == "outcome":
        return (f"{field!r} is the measured outcome. Using it as a {use} would "
                "condition primary estimation on its own result: section 12.1 "
                "assigns structural states without consulting effect direction, "
                "section 10.1 forbids dropping a delivered response for its "
                "state, and section 15.6 forbids dropping cells whose effects "
                "are inconvenient. Use it as the response variable "
                "(use='outcome') instead")
    if role in ("post_treatment_instrumentation", "diagnostic"):
        return (f"{field!r} has role {role!r} and section 11.8 bars it from "
                f"primary use as a {use}. It is caused by the treatment, so "
                "conditioning on it changes the estimand rather than adjusting "
                "for confounding. It may be described or studied secondarily, "
                "but it cannot redefine the causal replacement contrast")
    if use == "matching coordinate":
        return (f"{field!r} is not one of section 7.3's four matching "
                f"coordinates {MATCHING_COORDINATES}. Matching is an allowlist "
                "of computed comparability statistics, not any pretreatment "
                "field: D7 fixes parameter severity as EXCLUDED from matching "
                "even though parameters remain archived and reported")
    return (f"{field!r} has role {role!r}, which the permission matrix does not "
            f"admit as a {use}. Absent from the matrix means forbidden, so this "
            "requires a preregistration citation rather than an exception")


def assert_field_use(field: str, use: str) -> str:
    """The gate: may a primary analysis consume `field` in this `use`?

    Legality depends on the role AND the use, because the protocol has cells that
    differ within a role - F_A is the response yet forbidden as a covariate, and
    a pretreatment parameter is admissible generally yet excluded from matching.
    """
    if use not in USES:
        raise FieldRoleViolation(
            f"{use!r} is not a recognised primary-analysis use; known: {USES}")
    role = role_of(field)
    if use == "matching coordinate":
        raise FieldRoleViolation(_why_forbidden(field, role, use))
    if not permits(role, use):
        raise FieldRoleViolation(_why_forbidden(field, role, use))
    return field


def assert_matching_coordinate(coordinate: str) -> str:
    """Section 7.3's closed allowlist of four empirical matching properties.

    Separate from assert_field_use because matching does not range over stored
    analysis fields at all: the coordinates are statistics measured on unrelated
    targets and marginalised over the candidate's frozen parameter distribution.
    """
    if coordinate in MATCHING_COORDINATES:
        return coordinate
    extra = ""
    if coordinate in REPORTED_BUT_NOT_MATCHED:
        extra = (" Section 7.3 reports instruction length and does not match it, "
                 "because literal canonical wording is part of the "
                 "instruction-level treatment.")
    raise FieldRoleViolation(
        f"{coordinate!r} is not one of section 7.3's four matching coordinates "
        f"{MATCHING_COORDINATES}.{extra} D7 additionally fixes parameter "
        "severity as EXCLUDED, so no stored parameter or descriptor may become a "
        "matching coordinate")


def assert_primary_covariate(field: str, use: str = "covariate") -> str:
    """Thin wrapper over the matrix, kept so callers need not change.

    Retained because `use` already meant "which prohibited operation"; the
    difference is that legality is now decided by the (role, use) matrix rather
    than by a role denylist that could not express D7 or the outcome rule.
    """
    return assert_field_use(field, use)


def assert_primary_formula(fields: Iterable[str], use: str = "covariate") -> None:
    """Every field a primary formula consumes, checked together.

    Reports all offending fields at once: discovering them one exception at a
    time invites removing them one at a time until the formula happens to pass.
    """
    offending = []
    for field in fields:
        try:
            assert_field_use(field, use)
        except FieldRoleViolation:
            offending.append(f"{field} ({role_of(field)})")
    if offending:
        raise FieldRoleViolation(
            f"a primary estimator cannot consume {len(offending)} field(s) as a "
            f"{use}: {', '.join(offending)}. The permission matrix admits a field "
            "only when both its causal role and the intended use are permitted "
            "by the preregistration")


def assert_roles_well_formed() -> None:
    """Every field has one role, every role is populated, the matrix is closed."""
    _index()                                   # raises on any double declaration
    empty = sorted(role for role, fields in FIELD_ROLES.items() if not fields)
    if empty:
        raise ValueError(f"roles declared with no fields: {empty}")
    for role in FORBIDDEN_IN_PRIMARY:
        if role not in FIELD_ROLES:
            raise ValueError(
                f"{role!r} is barred from primary formulas but is not a declared "
                "role, so the prohibition would never fire")
    for role, use in PERMISSION:
        if role not in FIELD_ROLES:
            raise ValueError(f"the matrix permits unknown role {role!r}")
        if use not in USES:
            raise ValueError(f"the matrix permits unknown use {use!r}")
    # Every role must be describable, or a field could not be reported at all.
    for role in FIELD_ROLES:
        if (role, "diagnostic only") not in PERMISSION:
            raise ValueError(
                f"{role!r} has no permitted diagnostic use, so a field with that "
                "role could never be reported even descriptively")
    # Matching is an allowlist, so no role may be admitted to it by the matrix.
    matched = [r for (r, u) in PERMISSION if u == "matching coordinate"]
    if matched:
        raise ValueError(
            f"the matrix admits {matched} as matching coordinates, but section "
            "7.3 restricts matching to four computed empirical properties and D7 "
            "excludes parameter severity; use assert_matching_coordinate")


def audit() -> tuple[dict[str, object], ...]:
    """One row per field, with its permitted uses, for the completion audit."""
    return tuple(
        {"field": field, "role": role,
         "permitted_uses": [u for u in USES if (role, u) in PERMISSION],
         "permitted_in_primary": any((role, u) in PERMISSION
                                     for u in PRIMARY_USES)}
        for role, fields in FIELD_ROLES.items() for field in fields)


def permission_matrix() -> dict[str, dict[str, bool]]:
    """The complete role x use matrix, for the audit table and the freeze bundle."""
    return {role: {use: (role, use) in PERMISSION for use in USES}
            for role in FIELD_ROLES}
