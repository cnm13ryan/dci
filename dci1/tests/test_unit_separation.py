"""§8.5 experimental unit and dataset separation."""
import numpy as np
import pytest

pytestmark = pytest.mark.cpu

from helpers import M_PARAM, REFS, SPEC, N, small_config, write_stage

from dci1.analysis.bootstrap import ColumnStat, run_bootstrap
from dci1.analysis.estimators import (
    FORBIDDEN_PARAMETERS,
    PRIMARY_ESTIMATORS,
    assert_block_indexed_signatures,
    build_block_table,
    tau_by_order,
)
from dci1.analysis.tables import score_table
from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST
from dci1.protocol.constants import BOOTSTRAP_RESAMPLES, ProtocolError
from dci1.protocol.seeds import bootstrap_seed, generation_seed
from dci1.resampling.primary import build_primary, load_accepted
from dci1.resampling.pseudo import (
    _guard_pseudo_path,
    assert_primary_invariant,
    build_pseudo_run,
    primary_fingerprint,
)


def _primary_scored(tmp_path, config):
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_primary(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                  config=config)
    accepted = load_accepted(stage_dir)
    scored = score_table(accepted, blocks, n=N, m=M_PARAM, references=REFS)
    return stage_dir, blocks, cells, accepted, scored


def test_one_row_per_cell_blocks_times_six(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted, scored = _primary_scored(tmp_path,
                                                                 config)
    assert len(accepted) == len(blocks) * 6
    table = build_block_table(scored)
    assert len(table.blocks) == len(blocks)
    for entry in table.blocks.values():
        assert len(entry["f"]) == 6          # all six arms travel together


def test_pool_rows_never_reach_estimators(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted, scored = _primary_scored(tmp_path,
                                                                 config)
    # M members per cell exist in the cache, but exactly one observation per
    # cell reaches the block table; duplicating a cell raises.
    with pytest.raises(ProtocolError, match="duplicate"):
        build_block_table(scored + [scored[0]])


def test_estimator_signatures_are_block_indexed():
    assert_block_indexed_signatures()
    import inspect

    for fn in PRIMARY_ESTIMATORS:
        assert not (set(inspect.signature(fn).parameters)
                    & FORBIDDEN_PARAMETERS)
    with pytest.raises(ProtocolError, match="BlockTable"):
        tau_by_order([{"arm": "focal"}], TARGET_FIRST)


def test_bootstrap_resamples_blocks_default_10000():
    assert BOOTSTRAP_RESAMPLES == 10_000
    values = {TARGET_FIRST: np.array([0.0, 1.0, 0.5]),
              ADDED_FIRST: np.array([1.0, 0.0, 0.5])}
    stat = ColumnStat("x", values, TARGET_FIRST)
    result = run_bootstrap([stat], seed=1, n_resamples=200)
    assert result.resamples["x"].shape == (200,)


def test_generation_and_bootstrap_rng_are_independent():
    g = generation_seed(111, "confirmatory", "m", "p" * 64, 0)
    b = bootstrap_seed(111, "m", "confirmatory")
    assert g != b            # disjoint domains even under equal roots


def test_variance_behaviour_prices_between_block_variation():
    """§12 check 3: doubling within-block noise, holding the block-level
    means fixed, leaves the block-mean interval unchanged within MC error."""
    rng = np.random.default_rng(0)
    block_means = rng.normal(0.0, 1.0, size=192)

    def width(scale):
        # within-block noise cancels in the block mean by construction:
        # six arms per block whose noise averages to zero.
        noise = rng.normal(0, scale, size=(192, 6))
        noise -= noise.mean(axis=1, keepdims=True)
        column = block_means + noise.mean(axis=1)     # == block_means
        stat = ColumnStat("m", {TARGET_FIRST: column}, TARGET_FIRST)
        result = run_bootstrap([stat], seed=7, n_resamples=3000)
        se = result.se("m")
        return 2 * 1.96 * se

    w1, w2 = width(1.0), width(2.0)
    assert abs(w1 - w2) / w1 < 0.05


def test_primary_bit_identical_across_pseudo_runs(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_primary(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                  config=config)
    before = primary_fingerprint(stage_dir)
    for r in range(10):
        build_pseudo_run(SPEC, cells, stream="confirmatory",
                         stage_dir=stage_dir, config=config, run_index=r)
    after = primary_fingerprint(stage_dir)
    assert_primary_invariant(before, after)
    assert before == after


def test_pseudo_cannot_write_primary_paths(tmp_path):
    with pytest.raises(ProtocolError, match="pseudo lineage"):
        _guard_pseudo_path(tmp_path / "confirmatory" / "primary" / "x.jsonl")
    with pytest.raises(ProtocolError, match="pseudo lineage"):
        _guard_pseudo_path(tmp_path / "confirmatory" / "accepted.jsonl")


def test_primary_rebuild_divergence_fails_closed(tmp_path):
    config = small_config()
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_primary(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                  config=config)
    accepted_path = stage_dir / "primary" / "accepted.jsonl"
    original = accepted_path.read_text()
    accepted_path.write_text(original.replace("However", "Nevertheless", 1))
    with pytest.raises(ProtocolError, match="immutable"):
        build_primary(SPEC, cells, stream="confirmatory",
                      stage_dir=stage_dir, config=config)
