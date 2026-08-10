"""estimands — extracted verbatim from the v15 notebook cells by tools/migrate_v15.py.

Behavior-preserving Stage A extraction: bodies are byte-identical to the
notebook source; only the module home changed. See docs/migration_map.csv.
"""
from __future__ import annotations


ESTIMAND_DEFINITIONS: dict[str, dict[str, str]] = {
    "primary_total": {
        "name": "total pair-specific directional constraint interference",
        "reference_definition": (
            "C is admitted when it matches B on isolated difficulty, outgoing "
            "interference, incoming vulnerability and wording stability, and "
            "when its verifier coupling with A is within the declared audit "
            "tolerance of B's. Coupling is an ELIGIBILITY AUDIT, not a matched "
            "coordinate."),
        "interpretation": (
            "tau_{j,o} is the total extra target failure that adding B produces "
            "relative to adding C_j, INCLUDING whatever part of that effect runs "
            "through structural coupling between A and B."),
        "why": (
            "The supplied methodology treats coupling predominantly as verifier "
            "coupling to be excluded, but also lists it once among the principal "
            "potential moderators, which would place it on the causal pathway. "
            "Matching on a pathway variable removes part of the effect under "
            "study, so the primary estimand does not match on it."),
    },
    "kappa_matched": {
        "name": "coupling-matched directional constraint interference",
        "reference_definition": (
            "C is admitted when it matches B on every primary_total coordinate "
            "AND on verifier coupling with A, which is a matched signature "
            "component with its own caliper."),
        "interpretation": (
            "tau^kappa_{j,o} is the extra target failure that adding B produces "
            "relative to adding C_j among constraints whose measurement coupling "
            "with A is held fixed. It is a narrower question and a secondary "
            "result."),
        "why": (
            "If coupling is purely a verifier artefact then this is the cleaner "
            "contrast. Reporting both, separately named, is what the evidence "
            "actually supports."),
    },
}
