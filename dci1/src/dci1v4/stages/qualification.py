"""Stage 1, QUALIFIED (§18, §19).

Qualification is non-scientific and reads no behavioural rate. It establishes
that the apparatus is the one the protocol registered: a clean tree, a tracked
implementation, resolved model revisions, a non-empty dependency manifest, a
schema-valid prompt plan, the wording and witness suites passing for every
registered pair, reachable cache and durable store, and a hashable environment
and commit.

It also runs the checks that are cheapest to run here and most expensive to
discover later: the §10.2 carry-over comparison, the §7.3 wording-length
caliper against A, the judge-registry disjointness of §10.4, and the topic
bank's authoring record and split hash.
"""
from __future__ import annotations

from typing import Any

from dci1v4.design.cells import design_cells, registered_cell_types
from dci1v4.engine import store
from dci1v4.engine.binding import verifier_provenance
from dci1v4.engine.paths import ModelTree
from dci1v4.errors import TerminalStatus
from dci1v4.models.registry import assert_disjoint_judges, get_model
from dci1v4.protocol import constants as C
from dci1v4.protocol import wordings
from dci1v4.protocol.hashing import sha_obj
from dci1v4.stages.registration import assert_manifest_matches_code
from dci1v4.topics.bank import authoring_record, load_bank
from dci1v4.topics.split import confirmatory_blocks, split_hash, split_topics
from dci1v4.verifiers import boundary, carryover, witnesses, wording_suite


def qualification_payload(tree: ModelTree, ctx: dict[str, Any], *,
                          slot_map_fixture: dict[str, tuple[str, int]]
                          ) -> dict[str, Any]:
    """Everything §18 stage 1 requires, computed and hashed."""
    spec = get_model(tree.model_key)
    assert_disjoint_judges()

    # §6.1: every study-wide rule is fixed in the signed registration manifest
    # BEFORE the first qualification. Qualification fails closed without it,
    # and fails closed if the running code no longer implements what was
    # registered — otherwise the manifest would describe the study rather than
    # constrain it.
    manifest = assert_manifest_matches_code(tree.context)

    bank = load_bank()
    split = split_topics(bank)
    blocks = confirmatory_blocks(split)

    # A schema-valid prompt plan at fixture severities: the plan's structure is
    # checked here, and its severities cannot become calibration evidence.
    cells = design_cells("qualification", blocks, slot_map_fixture,
                         draws=C.M_DRAWS, assert_allocation_over=C.N_BLOCKS)

    suites = boundary.evaluate_suites()
    if any(v != 1.0 for v in suites["agreement"].values()):
        raise TerminalStatus("QUALIFICATION_FAILURE", {
            "status": "QUALIFICATION_FAILURE", "gate": C.STAGE_QUALIFIED,
            "model_key": tree.model_key, "model_revision": spec.revision,
            "criterion": "boundary suite agreement", "threshold": 1.0,
            "observed": suites["agreement"], "artifact_hashes": {},
            "strongest_permissible_statement": "none",
            "estimands_unanswerable": "all"})

    for root in (tree.root, tree.durable):
        root.mkdir(parents=True, exist_ok=True)

    return {
        "outcome": "PASS",
        "registration_manifest_hash": manifest["manifest_hash"],
        "model_id": spec.model_id,
        "model_revision": spec.revision,
        "thinking_policy": spec.thinking_policy,
        "chat_template_kwargs": dict(spec.chat_template_kwargs),
        "topics": {**authoring_record(bank), "split_hash": split_hash(split),
                   "split_counts": {k: len(v) for k, v in split.items()}},
        "design": {"cell_types": len(registered_cell_types(slot_map_fixture)),
                   "blocks": len(blocks), "cells": len(cells),
                   "cached_draws": sum(c.draws for c in cells),
                   "plan_hash": sha_obj(sorted(c.prompt_hash for c in cells))},
        "instruments": {
            **verifier_provenance(),
            "boundary_suites": {"cases": suites["cases"],
                                "agreement": suites["agreement"],
                                "coverage": suites["coverage"],
                                "suite_hash": suites["suite_hash"]},
            "wording_suite": wording_suite.evaluate(),
            "witnesses": witnesses.verify_all_witnesses(),
            "wording_length_caliper":
                wordings.assert_caliper_feasible(),
            "wording_word_counts": wordings.assert_severity_invariance(),
        },
        "carry_over": carryover.carry_over_record(),
        "storage": {"evidence_root": str(tree.root),
                    "durable_root": str(tree.durable),
                    "durable_reachable": tree.durable.exists(),
                    "files_replicated": len(store.replicate(tree.root,
                                                            tree.durable))},
        "environment": ctx["environment"],
        "identification_statuses": [],
    }
