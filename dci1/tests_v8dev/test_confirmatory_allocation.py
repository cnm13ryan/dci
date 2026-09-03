"""The confirmatory allocation and the universal calibration.

Four passes put every registered block (384) under each wording frame: one
allocation, stated once in ``rules`` and read everywhere else. The tests
below pin what that is (derived from the offsets and asserted, never a
literal), that every active source of the number agrees, what it buys (the
registered §16.1 variance form reaches Δ_R's precondition at the joint
constant for a two-frame model), and — the load-bearing one — what it must
**not** touch: no LOCAL support verdict may move with a block count.
"""
from __future__ import annotations

import ast
import math
import pathlib
from statistics import NormalDist

import pytest

from dci1v4.analysis.variance import variances
from dci1v7.analysis.bootstrap import sidak_critical
from dci1v7.protocol import constants as C

from dci1v8dev import rules as R
from dci1v8dev.run import references as REF
from dci1v8dev.run import stages as S
from dci1v8dev.run import manifest as MF
from dci1v8dev.run.context import synthetic_context
from dci1v8dev.run.manifest import rule_table
from dci1v8dev.spectrum import precision
from dci1v8dev.spectrum.coverage import FRAME_COVERAGE_RULE

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PRECONDITION = C.PRECISION_PRECONDITIONS["Delta_R"]
SIMULTANEOUS = sidak_critical(6)          # Delta_R is in F1, six members


def _manifest(name: str = "confirmatory-allocation"):
    return MF.build_manifest(synthetic_context(name),
                             producing_commit="0" * 40, repo_root=REPO_ROOT)


# --------------------------------------------------------------- the rule
def test_the_allocation_is_derived_from_the_passes_and_not_a_literal():
    assert R.CONFIRMATORY_FRAME_PASSES == len(R.CONFIRMATORY_FRAME_OFFSETS) == 4
    assert R.CONFIRMATORY_BLOCKS_PER_FRAME == (
        C.N_BLOCKS * R.CONFIRMATORY_FRAME_PASSES // C.N_WORDINGS) == 384
    assert R.CONFIRMATORY_BLOCKS_TOTAL == C.N_BLOCKS * 4 == 1536
    assert S.CONFIRMATORY_BLOCKS_PER_FRAME == R.CONFIRMATORY_BLOCKS_PER_FRAME


def test_the_passes_never_put_one_block_under_one_frame_twice():
    """The count is a count of *independent units*: §17.1's bootstrap
    resamples blocks, so a block met twice inside a frame would inflate the
    denominator every standard error is formed at."""
    seen = [(i + off) % C.N_WORDINGS
            for off in R.CONFIRMATORY_FRAME_OFFSETS for i in range(C.N_BLOCKS)]
    for frame in S.FRAMES:
        assert seen.count(frame) == R.CONFIRMATORY_BLOCKS_PER_FRAME
    assert len({o % C.N_WORDINGS for o in R.CONFIRMATORY_FRAME_OFFSETS}) == \
        R.CONFIRMATORY_FRAME_PASSES
    with pytest.raises(AssertionError):
        R._assert_offsets((0, 1, 1), "duplicate")
    with pytest.raises(AssertionError):
        R._assert_offsets((0, 4), "same modulo N_WORDINGS")


def test_the_ceiling_is_stated_and_not_exceeded():
    assert R.CONFIRMATORY_MAX_PASSES == C.N_WORDINGS == 4
    assert R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME == C.N_BLOCKS
    assert R.CONFIRMATORY_FRAME_PASSES <= R.CONFIRMATORY_MAX_PASSES
    assert R.CONFIRMATORY_BLOCKS_PER_FRAME <= R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME
    assert R.confirmatory_allocation()["at_block_ceiling"] is True


def test_the_allocation_record_states_what_the_constants_say():
    rec = R.confirmatory_allocation()
    assert rec["passes"] == R.CONFIRMATORY_FRAME_PASSES
    assert rec["frame_offsets"] == list(R.CONFIRMATORY_FRAME_OFFSETS)
    assert rec["blocks_per_frame"] == R.CONFIRMATORY_BLOCKS_PER_FRAME
    assert rec["blocks_total"] == R.CONFIRMATORY_BLOCKS_TOTAL
    assert rec["single_pass_blocks_per_frame"] == C.N_BLOCKS // C.N_WORDINGS == 96
    assert rec["draws"] == C.M_DRAWS
    assert "CHANGES_SCIENTIFIC.md" in rec["amendment"]


def test_the_signed_manifest_carries_the_confirmatory_allocation():
    """It is a property of the design, so it is bound before any stage runs
    and there is no per-model override to look up."""
    table = rule_table()
    for name in ("CONFIRMATORY_FRAME_OFFSETS", "CONFIRMATORY_FRAME_PASSES",
                 "CONFIRMATORY_BLOCKS_PER_FRAME", "CONFIRMATORY_BLOCKS_TOTAL",
                 "CONFIRMATORY_MAX_PASSES"):
        assert name in table, name
    assert table["CONFIRMATORY_BLOCKS_PER_FRAME"] == 384
    manifest = _manifest()
    alloc = manifest["design"]["confirmatory_allocation"]
    assert alloc == R.confirmatory_allocation()
    fc = manifest["frame_conditioning"]
    assert fc["confirmatory_blocks_per_frame"] == 384
    assert fc["confirmatory_passes"] == 4


def test_every_active_source_of_the_allocation_agrees():
    """One allocation. rules states it; the confirm precision module, the
    coverage gate's projection, the pilot stage constants, the confirm
    manifest and the v8 preregistration all read the same number. A
    disagreement anywhere fails here."""
    from dci1v8dev.confirm import precision as CP
    from dci1v8dev.confirm import manifest as CM
    n = R.CONFIRMATORY_BLOCKS_PER_FRAME
    assert n == 384 == C.N_BLOCKS == R.CONFIRMATORY_MAX_BLOCKS_PER_FRAME
    assert CP.ALLOCATION == n
    assert CP.precision_at(2)["blocks_per_frame"] == n
    assert CP.allocation_record({"m": 2})["chosen_blocks_per_frame"] == n
    assert FRAME_COVERAGE_RULE.n_blocks == n
    assert S.CONFIRMATORY_BLOCKS_PER_FRAME == n
    assert not hasattr(CP, "ALLOCATION_MENU")
    assert not hasattr(CP, "choose_allocation")
    from dci1v8dev.confirm import PREREGISTRATION_DOCUMENT
    prereg = REPO_ROOT / PREREGISTRATION_DOCUMENT
    assert prereg.exists(), "the preregistration is missing"
    text = prereg.read_text()
    assert f"CONFIRMATORY_BLOCKS_PER_FRAME = {n}" in text
    m = CM.build_manifest(synthetic_context("allocation-agreement"),
                          producing_commit="0" * 40, repo_root=REPO_ROOT,
                          pilot_roots={})
    assert m["allocation"]["blocks_per_frame"] == n
    assert m["rules"]["CONFIRMATORY_BLOCKS_PER_FRAME"] == n


# ------------------------------------------------------- what it buys
def _half_width(blocks: int, **kw) -> float:
    return SIMULTANEOUS * math.sqrt(variances(blocks, C.M_DRAWS, **kw)["Delta_R"])


def test_the_allocation_reaches_the_registered_precision_precondition():
    """§16.1's registered variance form at §16.2's own planning constants,
    on the simultaneous half-width `Interval.meets_precondition` reads."""
    assert _half_width(R.CONFIRMATORY_BLOCKS_PER_FRAME) <= PRECONDITION
    assert _half_width(R.CONFIRMATORY_BLOCKS_PER_FRAME,
                       phi=C.PHI_ALTERNATE) <= PRECONDITION


def test_fewer_passes_would_not_have_met_the_per_frame_precondition():
    one, two = C.N_BLOCKS // C.N_WORDINGS, 2 * C.N_BLOCKS // C.N_WORDINGS
    assert _half_width(one) > PRECONDITION
    assert _half_width(two) > PRECONDITION
    # three passes met it per frame but not at the joint constant of a
    # two-frame model under the adverse scenarios (confirm.precision), which
    # is why 2026-09-02 bound 384; the ceiling is now the one allocation
    from dci1v8dev.confirm import precision as CP
    assert not CP.precision_at(2, blocks=288)["precondition_met_adverse"]
    assert CP.precision_at(2)["precondition_met_adverse"]
    # and the MDE at one pass sat on §11.9's smallest effect of interest
    z = NormalDist().inv_cdf(0.80)
    mde = (SIMULTANEOUS + z) * math.sqrt(variances(one, C.M_DRAWS)["Delta_R"])
    assert mde >= C.SMALLEST_EFFECT_OF_INTEREST
    mde_now = (SIMULTANEOUS + z) * math.sqrt(
        variances(R.CONFIRMATORY_BLOCKS_PER_FRAME, C.M_DRAWS)["Delta_R"])
    assert mde_now < C.SMALLEST_EFFECT_OF_INTEREST


def test_the_spectrum_projection_follows_the_allocation():
    """`spectrum.coverage`'s condition 4 is defined at the blocks a frame
    will hold; the threshold it is compared against does not move."""
    assert FRAME_COVERAGE_RULE.n_blocks == R.CONFIRMATORY_BLOCKS_PER_FRAME
    assert FRAME_COVERAGE_RULE.max_se_beta == R.SPECTRUM_MAX_SE_BETA == 0.05
    points = [("MK1", 0.5), ("MK1", 0.7), ("MK2", 0.55), ("MK2", 0.75)]
    at_one = precision.projected_se_beta(points, n_blocks=96)
    at_four = precision.projected_se_beta(
        points, n_blocks=R.CONFIRMATORY_BLOCKS_PER_FRAME)
    assert at_four["leverage"] == at_one["leverage"]     # a property of the design
    assert at_four["se_beta"] == pytest.approx(at_one["se_beta"] / math.sqrt(4))


# ------------------------------------ what it must not touch: the LOCAL arm
def _survival_inputs(*, families: int, backups: int, core: bool):
    pool = {"local": {f"MK{i}:{i}": {"passed": True} for i in range(1, families + 1)},
            "spectrum": {}}
    core_block = {"references_identified": core,
                  "core_references": [{"family": f"MK{i}", "severity": i,
                                       "iota": 0.6} for i in range(1, 4)]}
    selection = {"coverage": {"identified": True, "status": "OK", "reasons": [],
                             "projection": {"n_blocks": R.CONFIRMATORY_BLOCKS_PER_FRAME}},
                 "families": [], "n_spectrum_references": 0}
    return pool, core_block, selection, {"backups": [f"B{i}" for i in range(backups)]}


@pytest.mark.parametrize("blocks", [24, 96, 192, 288, 384])
def test_local_support_does_not_move_with_the_block_count(monkeypatch, blocks):
    """The allocation amendment must not silently re-verdict the LOCAL arm.
    If this ever fails, r8's and r9's recorded LOCAL support stops meaning
    what it meant."""
    pool, core, selection, backups = _survival_inputs(families=5, backups=2,
                                                      core=True)
    baseline = REF.survival_summary(pool, core, selection, backups,
                                    iota_a=0.6, frame=1)
    monkeypatch.setattr(R, "CONFIRMATORY_BLOCKS_PER_FRAME", blocks)
    moved = REF.survival_summary(pool, core, selection, backups,
                                 iota_a=0.6, frame=1)
    for field in ("local_supported", "local_support_state",
                  "local_unsupported_reason", "local_unsupported_reasons",
                  "n_local_valid_families", "meets_min_local_families",
                  "core_identified", "n_backups", "meets_min_backups"):
        assert moved[field] == baseline[field], field
    # the one field that is *supposed* to move with it
    assert moved["projected_delta_r_precision"]["n_blocks"] == blocks


def test_no_local_rule_module_reads_a_block_count():
    """Structural, not behavioural: LOCAL validity, §13.15's family count and
    the backup rule are functions of a frame's own table, and nothing in them
    may take an allocation as input."""
    import dci1v8dev.spectrum.backups as backups_mod
    import dci1v8dev.spectrum.validity as validity_mod
    import inspect
    for module in (validity_mod, backups_mod):
        tree = ast.parse(inspect.getsource(module))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {kw.arg for n in ast.walk(tree) if isinstance(n, ast.Call)
                  for kw in n.keywords if kw.arg}
        offenders = {n for n in names
                     if n in {"n_blocks", "N_BLOCKS", "CONFIRMATORY_BLOCKS_PER_FRAME",
                              "CONFIRMATORY_FRAME_PASSES", "se_point", "block_corr"}}
        assert not offenders, f"{module.__name__} reads an allocation: {offenders}"


# --------------------------------------------- the raised calibration (§4b)
def test_every_model_runs_the_calibration_at_the_topic_ceiling():
    """Universal: no per-model table exists and every model key --- known,
    unknown or None --- resolves to the same four passes."""
    for model in ("qwen3-4b", "qwen3-4b-instruct-2507", "gemma-3n-e2b-it",
                  "gemma-3n-e4b-it", "unknown-model", None):
        assert R.calibration_frame_offsets(model) == (0, 1, 2, 3)
        assert R.calibration_passes(model) == R.CALIBRATION_MAX_PASSES
        assert R.calibration_topics_per_frame(model) == C.N_CALIBRATION == 192
        assert R.calibration_topics_per_frame_per_split(model) == 96
    assert not hasattr(R, "CALIBRATION_FRAME_OFFSETS_BY_MODEL")
    assert "universal" in R.CALIBRATION_POLICY


def test_the_manifest_states_the_universal_allocation_for_every_model():
    by_model = _manifest()["design"]["calibration_allocation"]["by_model"]
    assert by_model, "no model in the manifest"
    for m, e in by_model.items():
        assert e["is_default"], m
        assert e["passes"] == 4
        assert e["topics_per_frame"] == 192
        assert by_model[m]["generations_per_rung"] == 192 * C.M_CAL * 4
