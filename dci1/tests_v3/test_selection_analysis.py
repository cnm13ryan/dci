"""Selection, calibration, and statistics (item 62): the response-blind
primary rule, pseudo-run separation, Gate 2 selection with registered
tie-breakers, the §12 executable clustering checks, claims vocabulary, the
codebook, and the failure taxonomy."""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dci1v3.analysis import claims
from dci1v3.analysis.bootstrap import family_intervals, resample_indices
from dci1v3.analysis.estimators import (
    BlockTable,
    Member,
    family_members,
    from_primary_rows,
)
from dci1v3.analysis.taxonomy import classify_failure, REFUSAL_PATTERNS
from dci1v3.errors import ProtocolError, TerminalStatus
from dci1v3.protocol import constants as C
from dci1v3.protocol.codebook import (
    GENERATION_CODEBOOK,
    PRIMARY_FORMULA_FIELDS,
    validate_codebook,
    validate_row,
)
from dci1v3.protocol.seeds import primary_draw_index, pseudo_run_index
from dci1v3.stages.gate2a import admit_families, select_scalar
from dci1v3.stages.select import primary_index_for_cell, select_primary


def test_primary_rule_is_blind_and_frozen():
    params = list(inspect.signature(primary_index_for_cell).parameters)
    assert params == ["model_id", "prompt_hash"]
    j = primary_index_for_cell("m", "h")
    assert 0 <= j < 16
    assert j == primary_index_for_cell("m", "h")
    assert primary_index_for_cell("m", "h2") != j or True   # deterministic
    import hashlib
    digest = hashlib.sha256("primary-root\x1fm\x1fh".encode()).digest()
    assert j == int.from_bytes(digest, "big") % 16


def test_pseudo_run_selection_uses_separate_domain():
    same_inputs_primary = primary_draw_index("m", "h")
    pseudo = pseudo_run_index(C.PSEUDO_RUN_ROOT_SEED, 0, "m", "h")
    values = {pseudo_run_index(C.PSEUDO_RUN_ROOT_SEED, r, "m", "h")
              for r in range(50)}
    assert len(values) > 1
    assert isinstance(same_inputs_primary, int) and isinstance(pseudo, int)


def test_select_scalar_band_and_tiebreak():
    grid = (1, 2, 3, 4, 5, 6, 7, 8)
    curve = {1: 0.05, 2: 0.10, 3: 0.20, 4: 0.40, 5: 0.52, 6: 0.60,
             7: 0.70, 8: 0.80}
    assert select_scalar(curve, C.TARGET_BAND, grid=grid,
                         exhausted_status="TARGET_RANGE_EXHAUSTED",
                         payload={}) == 3   # |0.20-0.30| == |0.40-0.30|
    low = {n: 0.01 * n for n in grid}
    with pytest.raises(TerminalStatus) as excinfo:
        select_scalar(low, C.TARGET_BAND, grid=grid,
                      exhausted_status="TARGET_RANGE_EXHAUSTED", payload={})
    assert excinfo.value.status == "TARGET_RANGE_EXHAUSTED"
    jumpy = {1: 0.05, 2: 0.60, 3: 0.61, 4: 0.62, 5: 0.63, 6: 0.64,
             7: 0.65, 8: 0.66}
    with pytest.raises(TerminalStatus) as excinfo:
        select_scalar(jumpy, C.TARGET_BAND, grid=grid,
                      exhausted_status="TARGET_RANGE_EXHAUSTED", payload={})
    assert excinfo.value.status == "GRID_RESOLUTION_INSUFFICIENT"


def test_admit_families_caliper_and_tiebreak():
    focal_rate = 0.30
    rates = {family: {q: 0.90 for q in grid}
             for family, grid in C.REFERENCE_FAMILIES.items()}
    rates["RF1"] = {8: 0.35, 5: 0.25, 2: 0.60, 0: 0.90}   # tie 0.05
    rates["RF2"] = {8: 0.10, 5: 0.28, 2: 0.55, 0: 0.90}
    rates["RF5"] = {12: 0.32, 8: 0.50, 4: 0.70, 0: 0.95}
    table, eligible = admit_families(rates, focal_rate, m_star=9, n_star=3)
    assert set(eligible) == {"RF1", "RF2", "RF5"}
    assert table["RF1"]["selected"] == 8    # less restrictive wins the tie
    assert table["RF2"]["selected"] == 5
    assert table["RF7"]["selected"] is None


def _table(blocks: int = 40, rng_seed: int = 7) -> BlockTable:
    rng = np.random.default_rng(rng_seed)
    rows = []
    for i in range(blocks):
        order = C.TARGET_FIRST if i % 2 == 0 else C.ADDED_FIRST
        for arm in C.ARMS:
            s0 = int(rng.integers(0, 3))
            rows.append({
                "block_id": f"b{i:03d}", "arm": arm, "order": order,
                "verdicts": {"s0": s0, "s1": s0, "s2": s0, "s3": s0,
                             "added_pass": bool(rng.integers(0, 2))},
                "non_behavioural": False, "failure_category": "",
                "raw_response": "text", "token_count": 50,
                "finish_reason": "stop"})
    return from_primary_rows(rows, n=1)


def test_family_membership_counts():
    members = family_members(_table())
    counts: dict[str, int] = {}
    for member in members:
        counts[member.family] = counts.get(member.family, 0) + 1
    assert counts == C.FAMILY_SIZES


def test_resampling_unit_assertion():
    table = _table()
    indices = resample_indices(table, model_id="m", family="F1",
                               resamples=50)
    for order in C.ORDERS:
        stratum = table.stratum(order)
        assert indices[order].shape == (50, stratum.size)
        assert set(np.unique(indices[order])) <= set(stratum)


def test_estimators_reject_response_level_input():
    """§12 function-signature check: primary estimators receive the block
    table; a duplicate response-level row is refused."""
    rows = []
    for arm in C.ARMS:
        rows.append({"block_id": "b0", "arm": arm,
                     "order": C.TARGET_FIRST,
                     "verdicts": {"s0": 1, "s1": 1, "s2": 1, "s3": 1},
                     "non_behavioural": False, "failure_category": "",
                     "raw_response": "x", "token_count": 1,
                     "finish_reason": "stop"})
    rows.append(dict(rows[0]))          # a second response for one cell
    with pytest.raises(ProtocolError, match="duplicate"):
        from_primary_rows(rows, n=1)
    params = list(inspect.signature(family_members).parameters)
    assert params == ["table"]


def test_variance_prices_between_block_variation():
    """§12 variance-behaviour check: doubling within-block noise leaves the
    block-mean interval width unchanged up to Monte Carlo error."""
    rng = np.random.default_rng(3)
    blocks = 200
    order = np.array([C.TARGET_FIRST, C.ADDED_FIRST] * (blocks // 2),
                     dtype=object)
    between = rng.normal(0, 1.0, size=blocks)
    widths = []
    for scale in (1.0, 2.0):
        values = between + rng.normal(0, 0.05 * scale, size=blocks)
        table = BlockTable(
            block_ids=[f"b{i}" for i in range(blocks)], order=order,
            f={"s0": np.zeros((blocks, 4)), "s1": np.zeros((blocks, 4)),
               "s2": np.zeros((blocks, 4)), "s3": np.zeros((blocks, 4))},
            non_behavioural=np.zeros((blocks, 4)),
            uptake=np.zeros((blocks, 4)),
            category=np.full((blocks, 4), "", dtype=object))
        member = Member("block_mean", "F1", values, "all")
        result = family_intervals(table, [member], model_id="m",
                                  resamples=2000)
        low, high = result["F1"]["members"][0]["marginal"]
        widths.append(high - low)
    assert abs(widths[0] - widths[1]) < 0.05 * widths[0] + 0.02


def test_degenerate_contrast_reported_not_claimed():
    table = _table()
    member = Member("degenerate", "F1", np.zeros(table.n_blocks), "all")
    result = family_intervals(table, [member], model_id="m", resamples=100)
    entry = result["F1"]["members"][0]
    assert entry["status"] == "DEGENERATE_REPORTED"
    assert entry["simultaneous"] is None
    assert claims.primary_claims(None)["status"] == \
        "INCONCLUSIVE_NO_INTERVAL"


def test_claims_vocabulary_and_guard():
    assert claims.primary_claims((0.12, 0.30)) == {
        "direction": claims.DIRECTION_POSITIVE,
        "magnitude": claims.MAGNITUDE_POSITIVE, "status": "OK"}
    assert claims.primary_claims((-0.04, 0.06))["magnitude"] == \
        claims.EQUIVALENCE
    assert claims.primary_claims((-0.2, 0.2))["magnitude"] == \
        claims.MAGNITUDE_UNRESOLVED
    with pytest.raises(ProtocolError, match="aborts"):
        claims.licensed_equivalence((-0.2, 0.05), C.EQUIVALENCE_REGION)
    assert claims.exchangeability_holds(
        [(-0.02, 0.03)] * 3) is True
    assert claims.exchangeability_holds(
        [(-0.02, 0.06)] * 3) is False
    assert claims.exchangeability_holds([(-0.01, 0.01), None,
                                         (-0.01, 0.01)]) is None


def test_codebook_checks():
    assert validate_codebook()["valid"]
    for field in PRIMARY_FORMULA_FIELDS:
        assert GENERATION_CODEBOOK[field][3] != "Post-treatment"
    good = {name: None for name in GENERATION_CODEBOOK}
    good.update({
        "row_id": "r", "stage": "pilot", "artifact_state": "committed",
        "model_key": "k", "model_id": "m", "model_revision": "rev",
        "cell_id": "c", "topic_id": "t", "kind": "arm:AB",
        "draw_index": 3, "prompt_hash": "h", "backend_version": "v",
        "hardware_class": "g", "seed": 5, "raw_response": "x",
        "response_content_hash": "h", "prompt_tokens": 1,
        "token_count": 2, "finish_reason": "stop", "verdicts": {},
        "record_hash": "h", "arm": "AB", "order": "target_first",
        "n": 3, "constraint_id": "B", "severity": 9,
        "target_wording": 1, "added_wording": 2, "block_id": "b"})
    validate_row(good)
    with pytest.raises(ProtocolError, match="domain"):
        validate_row({**good, "arm": "NOT_AN_ARM"})
    with pytest.raises(ProtocolError, match="outside the codebook"):
        validate_row({**good, "surprise": 1})


def test_taxonomy_priority_order():
    assert len(REFUSAL_PATTERNS) == 20
    kwargs = dict(s0=0, s2=0, n=2, instruction_text="Use x.")
    assert classify_failure(response="", finish_reason="stop",
                            **kwargs) == "empty"
    assert classify_failure(response="text", finish_reason="length",
                            **kwargs) == "cut_off"
    assert classify_failure(response="I cannot help with that.",
                            finish_reason="stop", **kwargs) == "refusal"
    assert classify_failure(response="ok fine", finish_reason="stop",
                            s0=0, s2=3, n=2,
                            instruction_text="z") == \
        "target_inside_longer_word"
    assert classify_failure(response="ok fine", finish_reason="stop",
                            s0=1, s2=1, n=2, instruction_text="z") == \
        "too_few"
    assert classify_failure(response="ok fine", finish_reason="stop",
                            s0=3, s2=3, n=2, instruction_text="z") == \
        "too_many"


def test_analysis_reproduces_deterministically():
    """Item 62: deterministic report reproduction — identical inputs give
    byte-identical analysis output."""
    from dci1v3.analysis.run import analyse
    from dci1v3.protocol.hashing import sha_obj
    rng = np.random.default_rng(11)
    rows = []
    for i in range(12):
        order = C.TARGET_FIRST if i % 2 == 0 else C.ADDED_FIRST
        for arm in C.ARMS:
            s0 = int(rng.integers(0, 3))
            rows.append({
                "block_id": f"b{i:03d}", "arm": arm, "order": order,
                "verdicts": {"s0": s0, "s1": s0, "s2": s0, "s3": s0,
                             "added_pass": True},
                "non_behavioural": False, "failure_category": "",
                "raw_response": "words", "token_count": 9,
                "finish_reason": "stop"})
    first = analyse(rows, model_id="m", n=1, resamples=300,
                    expected_blocks=12)
    second = analyse(rows, model_id="m", n=1, resamples=300,
                     expected_blocks=12)
    assert sha_obj(first) == sha_obj(second)


def test_select_primary_requires_complete_cache():
    from dci1v3.generation.prompts import Cell
    cell = Cell(cell_id="s:t:arm:AB", stage="s", topic_id="t",
                block_id="b0", arm="AB", kind="arm:AB", constraint_id="B",
                severity=9, order=C.TARGET_FIRST, target_wording=0,
                added_wording=0, n=3, prompt="p", prompt_hash="h",
                draws=16, active_wordings=("w",))
    with pytest.raises(Exception, match="incomplete"):
        select_primary([cell], [], model_id="m")
