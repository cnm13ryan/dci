"""§8.7 analysis integrity: masking, fail-closed behaviour, hashes,
regeneration; plus estimator/claims/taxonomy semantics."""
import builtins
import json

import numpy as np
import pytest

pytestmark = pytest.mark.cpu

from helpers import M_PARAM, REFS, SPEC, N, small_config, write_stage

from dci1.analysis.claims import (
    guarded_absence_claim,
    primary_outcome,
    terminal_outcome,
)
from dci1.analysis.estimators import (
    block_contrast,
    build_block_table,
    delta,
    tau_by_order,
)
from dci1.analysis.run import analyze
from dci1.analysis.taxonomy import classify_failure, similarity
from dci1.design.blocks import ADDED_FIRST, TARGET_FIRST
from dci1.masking.mask import analysis_code_hash, construct_mask, unmask
from dci1.protocol.constants import ProtocolError
from dci1.resampling.primary import build_primary, load_accepted


def _stage(tmp_path, config):
    stage_dir, blocks, cells = write_stage(tmp_path, config)
    build_primary(SPEC, cells, stream="confirmatory", stage_dir=stage_dir,
                  config=config)
    return stage_dir, blocks, cells, load_accepted(stage_dir)


def test_estimator_hand_computed():
    rows = []
    f_values = {"T00": {"focal": 1, "ref1": 0, "ref2": 0, "ref3": 1,
                        "target_alone": 0, "topic_alone": 0},
                "T01": {"focal": 0, "ref1": 1, "ref2": 0, "ref3": 0,
                        "target_alone": 1, "topic_alone": 0}}
    for block_id, arms in f_values.items():
        order = TARGET_FIRST if block_id == "T00" else ADDED_FIRST
        for arm, f in arms.items():
            rows.append({"block_id": block_id, "arm": arm, "order": order,
                         "f_s0": f})
    table = build_block_table(rows)
    assert block_contrast(table, "T00") == pytest.approx(1 - 1 / 3)
    assert block_contrast(table, "T01") == pytest.approx(-1 / 3)
    assert tau_by_order(table, TARGET_FIRST) == pytest.approx(2 / 3)
    assert tau_by_order(table, ADDED_FIRST) == pytest.approx(-1 / 3)
    assert delta(table, 1, 2) == pytest.approx(0.5)


def test_guarded_absence_claim_aborts_outside_region():
    assert guarded_absence_claim("x", [-0.05, 0.08], (-0.10, 0.10))
    with pytest.raises(ProtocolError, match="aborts"):
        guarded_absence_claim("x", [-0.05, 0.12], (-0.10, 0.10))


def test_primary_outcome_rules():
    effect = primary_outcome("t", {"status": "OK", "estimate": 0.2,
                                   "simultaneous": [0.12, 0.28]}, 0.09)
    assert effect["outcome"] == "EFFECT"
    assert terminal_outcome("t", effect, exchangeable=True) == \
        "POSITIVE_IDENTITY_SPECIFIC_EFFECT"
    assert terminal_outcome("t", effect, exchangeable=False) == \
        "POSITIVE_SWAP_EFFECT"
    equivalence = primary_outcome("t", {"status": "OK", "estimate": 0.01,
                                        "simultaneous": [-0.06, 0.07]}, 0.09)
    assert equivalence["outcome"] == "EQUIVALENCE"
    unresolved = primary_outcome("t", {"status": "OK", "estimate": 0.06,
                                       "simultaneous": [-0.02, 0.15]}, 0.09)
    assert unresolved["outcome"] == "UNRESOLVED"


def test_taxonomy_priority_order():
    base = dict(finish_reason="stop", s0=0, s2=0, n=2,
                instruction_text="1. Use the word however exactly 2 times.")
    assert classify_failure(response="", **base) == "empty"
    assert classify_failure(response="text",
                            **dict(base, finish_reason="length")) == "cut_off"
    assert classify_failure(response="I'm sorry, I cannot help with that.",
                            **base) == "refusal"
    assert classify_failure(
        response="Use the word however exactly 2 times.",
        **dict(base, s0=1, s2=1)) == "restatement"
    assert classify_failure(response="howeverhowever",
                            **dict(base, s0=0, s2=2)) == \
        "target_inside_longer_word"
    assert classify_failure(response="plain text", **base) == \
        "zero_occurrences"
    assert classify_failure(response="x", **dict(base, s0=1)) == "too_few"
    assert classify_failure(response="x", **dict(base, s0=3)) == "too_many"
    assert similarity("abc", "abc") == 1.0


def test_full_analysis_and_regeneration_byte_identical(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted = _stage(tmp_path, config)
    result_a = analyze(accepted, blocks, n=N, m=M_PARAM, references=REFS,
                       bootstrap_seed_value=99, n_resamples=300)
    result_b = analyze(accepted, blocks, n=N, m=M_PARAM, references=REFS,
                       bootstrap_seed_value=99, n_resamples=300)
    assert result_a["status"] == "OK"
    assert json.dumps(result_a, sort_keys=True, default=str) == \
        json.dumps(result_b, sort_keys=True, default=str)


def test_duplicate_cell_fails_closed(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted = _stage(tmp_path, config)
    result = analyze(accepted + [accepted[0]], blocks, n=N, m=M_PARAM,
                     references=REFS, bootstrap_seed_value=1,
                     n_resamples=50)
    assert result["status"] == "INCONCLUSIVE_INCOMPLETE_MATRIX"
    assert result["claims"] is None


def test_masking_invariants_and_key_opened_once(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted = _stage(tmp_path, config)
    info = construct_mask(accepted, tmp_path / "analysis", tmp_path)
    masked = [json.loads(line) for line in
              (tmp_path / "analysis" / "masked_accepted.jsonl")
              .read_text().splitlines()]
    assert len(masked) == len(accepted)
    # §19 check 1 recorded at construction; here: masked really differs
    assert any(a["arm"] != b["arm"]
               for a, b in zip(sorted(accepted, key=lambda r: r["row_id"]),
                               sorted(masked, key=lambda r: r["row_id"])))

    key_path = tmp_path / "analysis" / "mask_key.json"
    opens = {"count": 0}
    real_open = builtins.open

    def counting_open(file, *args, **kwargs):
        try:
            if str(file) == str(key_path):
                opens["count"] += 1
        except Exception:
            pass
        return real_open(file, *args, **kwargs)

    builtins.open = counting_open
    try:
        masked_result = analyze(masked, blocks, n=N, m=M_PARAM,
                                references=REFS, bootstrap_seed_value=5,
                                n_resamples=100, masked=True)
        restored = unmask(masked, key_path, tmp_path)
        unmasked_result = analyze(restored, blocks, n=N, m=M_PARAM,
                                  references=REFS, bootstrap_seed_value=5,
                                  n_resamples=100, masked=False)
    finally:
        builtins.open = real_open
    assert opens["count"] == 1              # §19 check 2
    assert masked_result["status"] == unmasked_result["status"] == "OK"
    # unmasking restores the true labels exactly
    truth = {r["row_id"]: r["arm"] for r in accepted}
    for row in restored:
        assert row["arm"] == truth[row["row_id"]]
    # §19 check 3: run record carries the analysis code hash at unmasking
    events = [json.loads(line) for line in
              (tmp_path / "runrecord.jsonl").read_text().splitlines()]
    unmask_events = [e for e in events if e["event"] == "unmasked"]
    assert len(unmask_events) == 1
    assert unmask_events[0]["analysis_code_hash"] == analysis_code_hash()


def test_masked_phase_rerun_byte_identical(tmp_path):
    config = small_config()
    stage_dir, blocks, cells, accepted = _stage(tmp_path, config)
    construct_mask(accepted, tmp_path / "analysis", tmp_path)
    masked = [json.loads(line) for line in
              (tmp_path / "analysis" / "masked_accepted.jsonl")
              .read_text().splitlines()]
    a = analyze(masked, blocks, n=N, m=M_PARAM, references=REFS,
                bootstrap_seed_value=5, n_resamples=100, masked=True)
    b = analyze(masked, blocks, n=N, m=M_PARAM, references=REFS,
                bootstrap_seed_value=5, n_resamples=100, masked=True)
    assert json.dumps(a, sort_keys=True, default=str) == \
        json.dumps(b, sort_keys=True, default=str)


def test_nonfinite_se_yields_named_status():
    from dci1.analysis.bootstrap import ColumnStat, family_intervals, run_bootstrap

    stat = ColumnStat("bad", {TARGET_FIRST: np.array([1.0, 1.0])},
                      TARGET_FIRST,
                      mask_by_stratum={TARGET_FIRST: np.array([0.0, 0.0])})
    result = run_bootstrap([stat], seed=1, n_resamples=50)
    out = family_intervals(result, ["bad"])
    assert out["status"] == "INCONCLUSIVE_NONFINITE_SE"
    assert out["members"]["bad"]["status"] == "INCONCLUSIVE_NONFINITE_SE"
