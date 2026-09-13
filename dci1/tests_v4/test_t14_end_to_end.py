"""T14. End-to-end readiness, CPU-only and synthetic.

The whole registered pipeline runs on a synthetic generator: qualification's
preconditions, the procedural pilot, cached generation, the compliance vector,
the observation table, every family, the bootstrap, the claim ladder, masking,
the result table, and durable restoration — all in the synthetic namespace,
with no GPU and no real model.

Real-model stages are run separately and only in the registered order.
"""
from __future__ import annotations

import json

import pytest

from dci1v4 import SYNTHETIC_STUDY_ID
from dci1v4.analysis import claims, masking, variance
from dci1v4.analysis.run import (
    build_result_table,
    emit_claims,
    f6_gate,
    run_analysis,
)
from dci1v4.design.cells import design_cells
from dci1v4.engine import store
from dci1v4.engine.context import synthetic_context
from dci1v4.engine.paths import model_tree
from dci1v4.engine.signing import create_signing_key
from dci1v4.generation.backend import build_plan
from dci1v4.generation.cache import cache_rows, fill_cache
from dci1v4.generation.synthetic import synthetic_generate
from dci1v4.models.registry import get_model
from dci1v4.protocol import constants as C
from dci1v4.stages import pilot
from dci1v4.topics.split import confirmatory_blocks, pilot_blocks, split_topics

SLOT_MAP = {"A": ("A", 3), "B": ("B", 8), "R1": ("RF1", 2), "R2": ("RF5", 4),
            "R3": ("RF7", 6)}
SPEC = get_model("gemma-3n-e2b-it")
ENVIRONMENT = {"python_executable": "python", "dependency_digest": "d"}


@pytest.mark.slow
def test_the_whole_pipeline_runs_synthetically(tmp_path):
    context = synthetic_context(tmp_path)
    create_signing_key(context.signing_key_path)
    tree = model_tree(context, SPEC.model_key)
    tree.root.mkdir(parents=True, exist_ok=True)

    # ---- Gate 0: the procedural pilot, all 25 cells on twelve topics -------
    pilot_cells = design_cells("pilot", pilot_blocks(split_topics()),
                               pilot.pilot_slot_map(), draws=C.PILOT_DRAWS)
    pilot_report = fill_cache(
        tree.data_dir("pilot"), pilot_cells, spec=SPEC, stage="pilot",
        slot_map=pilot.pilot_slot_map(), study_id=SYNTHETIC_STUDY_ID,
        plan=build_plan(SPEC, stage="pilot", max_new_tokens=768),
        generate_fn=synthetic_generate, environment=ENVIRONMENT)
    assert pilot_report["draws"] == 1200

    # ---- confirmatory-shaped generation on a small block set ---------------
    blocks = confirmatory_blocks(split_topics())[:16]
    cells = design_cells("confirmatory", blocks, SLOT_MAP, draws=C.M_DRAWS)
    report = fill_cache(
        tree.data_dir("confirmatory"), cells, spec=SPEC,
        stage="confirmatory", slot_map=SLOT_MAP, study_id=SYNTHETIC_STUDY_ID,
        plan=build_plan(SPEC, stage="confirmatory", max_new_tokens=768),
        generate_fn=synthetic_generate, environment=ENVIRONMENT)
    assert report["status"] == "COMPLETE"
    assert report["draws"] == 16 * 25 * 4
    assert report["duplicates"]["overall_rate"] <= \
        C.DUPLICATE_QUALIFICATION_MAX

    rows = cache_rows(tree.data_dir("confirmatory"))

    # ---- the registered analysis, in the §21 order -------------------------
    analysis = run_analysis(
        rows, model_key=SPEC.model_key, model_id=SPEC.model_id,
        m_draws=C.M_DRAWS, measurement_basis="human_validation_unavailable",
        identification_status=["HUMAN_VALIDATION_UNAVAILABLE"],
        expected_blocks=16, resamples=200)
    assert analysis["within_block"]["cross_set_terms"] == 0
    assert analysis["scope_sentence"] == C.SCOPE_SENTENCE
    for configuration, outcome in analysis["per_configuration"].items():
        assert set(outcome["families"]) == {"F1", "F2", "F3", "F4", "F5",
                                            "F6", "F7"}
        assert outcome["inconclusive"] == {}
        assert "clean" in outcome["f6_gate"]

    # ---- the claim ladder through the guarded emitters ---------------------
    context_claims = claims.ClaimContext(
        configuration="outcome_first",
        measurement_basis="human_validation_unavailable",
        identification_status=("HUMAN_VALIDATION_UNAVAILABLE",))
    statements = emit_claims(
        analysis["per_configuration"]["outcome_first"]["families"],
        "outcome_first", context=context_claims,
        solo_headroom={"A": True, "B": True})
    for statement in statements:
        record = statement.as_record()
        claims.assert_statement_complete(record)
        claims.assert_scalar_carries_configuration(record)
        assert record["scope_sentence"] == C.SCOPE_SENTENCE

    # ---- the result table --------------------------------------------------
    table = build_result_table(
        analysis, realised_variance={"sigma2_topic": 0.05,
                                     "sigma2_draw": 0.15, "phi": 0.25},
        blocks=16, m_draws=C.M_DRAWS)
    assert len(table) == sum(len(f.members)
                             for outcome in
                             analysis["per_configuration"].values()
                             for f in outcome["families"].values())
    assert all(row["configuration"] for row in table)

    # ---- masking and one-way unmasking -------------------------------------
    from dci1v4.analysis.observations import build_observations

    observations = build_observations(rows, m_draws=C.M_DRAWS)
    mask = masking.build_mask(observations, namespace="confirmatory_mask")
    masking.assert_mask_effective(observations, mask)
    key = masking.MaskKey(tree.mask_key_path("confirmatory_mask"))
    key.write(mask)
    unmask_record = masking.unmask(key, analysis_code_hash="h",
                                   masked_outputs_hash="o")
    assert unmask_record["declared_limitation"]

    # ---- durable replication and restoration -------------------------------
    store.replicate(tree.root, tree.durable)
    store.assert_replicated(tree.root, tree.durable)
    cache_path = tree.data_dir("confirmatory") / "cache.jsonl"
    original = cache_path.read_bytes()
    cache_path.unlink()
    store.restore(tree.durable, tree.root)
    assert cache_path.read_bytes() == original


def test_the_menu_rule_is_reported_not_decided():
    selection = variance.select_allocation()
    assert "REPORTED, NOT DECIDED" in selection["decision_status"]
    assert selection["selected"]["blocks"] == 384


def test_the_cli_refuses_to_freeze_or_generate():
    from dci1v4 import cli

    with pytest.raises(SystemExit, match="not executed"):
        cli.main(["freeze"])
    with pytest.raises(SystemExit, match="not executed"):
        cli.main(["confirmatory"])
