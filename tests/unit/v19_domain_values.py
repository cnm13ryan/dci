"""Domain-valid stand-in values, for tests that need a slot resolved.

Not a test module - pytest does not collect it. It exists because slots now carry
typed domains, so a test that wants to ask "is the gate still blocked when this one
output is missing?" can no longer freeze the string `"probe"` into everything.

Nothing here is a scientific value. Every entry is either the value the code already
computes (the frozen grammar, the regenerated battery, the installed solver) or an
obviously synthetic record whose only job is to be admissible. Production code has no
access to this module, which is the point: `dci.v19.schemas` must never ship an
"example" value, because an example in the source is indistinguishable from a
legitimately produced output once it reaches an artifact.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from dci.v19 import artifacts, ordering, pairs
from dci.v19.encoding import encoding_map_state
from dci.v19.parsing import CANONICAL_LIST_POLICY
from dci.v19.reliability import AMENDED_INTERVAL, AMENDED_TIER1_DESIGN
from dci.v19.text import CANONICAL_TEXT_POLICY
from dci.v19.witness import CONSTRUCTOR_ID

# What a test freezes into a slot that declares no domain. Any value is admissible
# there, and a recognisable one makes a failure message readable.
UNTYPED_STAND_IN = "probe"


@lru_cache(maxsize=1)
def specification_bundle() -> dict[str, Any]:
    from dci.v19.verifiers import bundle_state
    return bundle_state(CANONICAL_LIST_POLICY)


@lru_cache(maxsize=1)
def bundle_hash_value() -> str:
    from dci.v19.verifiers import bundle_hash
    return bundle_hash(CANONICAL_LIST_POLICY)


def battery_evidence() -> dict[str, Any]:
    """A well-formed battery record, per the stable section 8.7 record schema.

    Deliberately NOT a real battery: the domain checks the record's shape, and
    whether the hashes match one the harness produces is checked by regenerating
    it in `dci.v19.stage2`. A stand-in that satisfied both would have to run the
    harness, which is a two-second cost every gate test would pay.
    """
    from dci.v19.stage2 import MUTATIONS_PER_TEMPLATE
    return {rule.constraint_id: {"records_hash": f"{index:064x}",
                                 "n_mutations": MUTATIONS_PER_TEMPLATE,
                                 "distinct_texts": MUTATIONS_PER_TEMPLATE}
            for index, rule in enumerate(pairs.rules(), start=1)}


@lru_cache(maxsize=1)
def solver_identity_value() -> dict[str, str]:
    from dci.v19.solver import solver_identity
    name, version = solver_identity()
    return {"name": name, "version": version}


@lru_cache(maxsize=1)
def review_trigger_evidence() -> dict[str, Any]:
    from dci.v19.review_trigger import frozen_trigger_evidence
    return frozen_trigger_evidence()


def passing_review_record(witness_hash: str = "0" * 64,
                          clause_ids: tuple[str, ...] = (
                              "v19:p2.focal.all_words_unique",)) -> dict[str, Any]:
    return {"witness_hash": witness_hash, "clause_ids": list(clause_ids),
            "reviews": [{"reviewer_id": "reviewer-a", "satisfied": True,
                         "rationale": "a synthetic rationale for a gate test"},
                        {"reviewer_id": "reviewer-b", "satisfied": True,
                         "rationale": "a second synthetic rationale"}]}


def certified_compositions() -> dict[str, Any]:
    return {"probe/composition": {"semantic_id": "a" * 64,
                                  "implementation_id": "b" * 64,
                                  "evidence_id": "c" * 64,
                                  "certificate_hash": "d" * 64,
                                  "certified": True}}


def tier1_certificates() -> dict[str, Any]:
    return {rule.constraint_id: {"passed": True, "unavailable": []}
            for rule in pairs.rules()}


def for_domain(domain: str) -> Any:
    """An admissible value for one declared domain."""
    if not domain:
        return UNTYPED_STAND_IN
    table = {
        "list_policy": lambda: CANONICAL_LIST_POLICY.state(),
        "text_policy": lambda: CANONICAL_TEXT_POLICY.state(),
        "ordering_depth": lambda: dict(ordering.DECISION),
        "reuse_disposition": lambda: dict(artifacts.REUSE_DISPOSITION),
        "binomial_interval": lambda: AMENDED_INTERVAL,
        "tier1_audit_design": lambda: AMENDED_TIER1_DESIGN.state(),
        "specification_bundle": specification_bundle,
        "bundle_hash": bundle_hash_value,
        "boundary_mutations": battery_evidence,
        # A COMPLETE protocol shape, not a decision: the real one is the
        # investigator's, and this only exists so a gate test can proceed past a
        # slot it is not testing.
        "tier1_audit_protocol": lambda: {
            "independent_reviewers": 2,
            "adjudicator_resolves_disagreement": True,
            "adjudicator_id": "an unassigned adjudicator",
            "unresolved_disagreement": "fails",
            "oversampling_rule": "exact_authoring",
            "citation": "a domain-valid stand-in for a gate test"},
        "tier1_certificates": tier1_certificates,
        "encoding_map": lambda: encoding_map_state(CANONICAL_LIST_POLICY),
        "solver_identity": solver_identity_value,
        "witness_constructor": lambda: CONSTRUCTOR_ID,
        "review_trigger": review_trigger_evidence,
        "semantic_reviews": lambda: {"probe/composition": passing_review_record()},
        "certified_compositions": certified_compositions,
    }
    if domain not in table:
        raise KeyError(f"no stand-in value for domain {domain!r}; add one here "
                       "rather than weakening the domain")
    return table[domain]()


def resolve(table, *names: str):
    """Freeze each named slot with a value its own domain admits."""
    for name in names:
        slot = table[name]
        if slot.resolved:
            continue
        table = table.freeze(name, for_domain(slot.domain),
                             by="a domain-valid stand-in for a gate test")
    return table


def resolve_all_except(table, *held_back: str, names=()):
    """Freeze every named slot but the ones held back."""
    return resolve(table, *[n for n in names if n not in held_back])


def table_without(*withheld: str):
    """The registry with every recorded output applied EXCEPT the named ones.

    Needed because "withhold one requirement and the gate must stay blocked" can no
    longer be tested against the live registry: every Stage 2 prerequisite is now
    resolved there, and a frozen commitment cannot be unfrozen. Rebuilding from the
    declaration with one record left out asks the same question honestly.

    Records whose own prerequisites become unresolved as a consequence are skipped
    too - `frozen.apply` would refuse them - so withholding an early decision
    correctly cascades to everything downstream of it.
    """
    from dci.v19 import frozen
    from dci.v19.registry import declared_table
    table = declared_table()
    held = set(withheld)
    for record in frozen.records():
        name = record["slot"]
        if name in held:
            continue
        if any(not table[d].resolved for d in table[name].depends_on):
            continue
        table = table.freeze(name, record["value"], by=record["frozen_by"])
    return table
