"""Masking custody (item 62): persistent single-shot mask creation and
unmasking, pilot/confirmatory namespace isolation, permutation coverage,
key-access audit, and the analysis-code-hash rule."""
from __future__ import annotations

import builtins
import json
import multiprocessing

import pytest

from dci1v3.engine import store
from dci1v3.engine.paths import model_tree
from dci1v3.errors import CustodyError
from dci1v3.protocol import constants as C
from dci1v3.stages import masking

MODEL = "gemma-3n-e2b-it"


def _rows(blocks: int = 24) -> list[dict]:
    rows = []
    for i in range(blocks):
        for arm in C.ARMS:
            rows.append({
                "block_id": f"b{i:03d}", "arm": arm,
                "order": C.TARGET_FIRST if i % 2 == 0 else C.ADDED_FIRST,
                "row_id": f"r{i}:{arm}", "cell_id": f"c{i}:{arm}",
                "kind": f"arm:{arm}", "prompt_hash": f"h{i}{arm}",
                "seed": i, "raw_response": "however text",
                "verdicts": {"s0": 1, "s1": 1, "s2": 1, "s3": 1,
                             "added_pass": True,
                             "verifier_source_hash": "v"},
                "non_behavioural": False, "failure_category": "",
                "token_count": 10, "finish_reason": "stop",
                "constraint_id": "B", "severity": 9, "draw_index": 0,
                "n": 1, "target_wording": 0, "added_wording": 0,
                "topic_id": f"t{i}", "prompt_tokens": 5})
    return rows


@pytest.fixture()
def tree(registered_ctx):
    return model_tree(registered_ctx, MODEL)


def test_mask_single_shot_and_view_excludes_identifiers(tree):
    report = masking.create_mask(tree, "confirmatory_mask", _rows())
    assert report["blocks"] == 24
    assert report["blocks_changed"] >= 12
    with pytest.raises(CustodyError, match="second mask attempt"):
        masking.create_mask(tree, "confirmatory_mask", _rows())
    rows = masking.masked_rows(tree, "confirmatory_mask")
    for row in rows:
        for hidden in masking.MASKED_VIEW_EXCLUDED:
            assert hidden not in row
        assert "verifier_source_hash" not in row["verdicts"]


def test_mask_reservation_alone_blocks_second_attempt(tree):
    from dci1v3.engine import fs
    fs.write_json_once(tree.mask_reservation("confirmatory_mask"),
                       {"state": "reserved"})
    with pytest.raises(CustodyError, match="fails before key generation"):
        masking.create_mask(tree, "confirmatory_mask", _rows())


def test_pilot_and_confirmatory_namespaces_isolated(tree):
    masking.create_mask(tree, "confirmatory_mask", _rows())
    before = store.fingerprint_tree(tree.mask_dir("confirmatory_mask"))
    masking.create_mask(tree, "pilot_mask", _rows())
    masking.unmask(tree, "pilot_mask", timestamp="T")
    after = store.fingerprint_tree(tree.mask_dir("confirmatory_mask"))
    masking.assert_namespace_untouched(before, after, "confirmatory_mask")


def test_unmask_single_shot_and_records(tree):
    masking.create_mask(tree, "confirmatory_mask", _rows())
    outcome = masking.unmask(tree, "confirmatory_mask", timestamp="T1")
    record = outcome["record"]
    assert record["mask_key_hash"] and record["analysis_code_hash"]
    with pytest.raises(Exception):
        masking.unmask(tree, "confirmatory_mask", timestamp="T2")


def test_remask_after_unmask_refused(tree):
    masking.create_mask(tree, "confirmatory_mask", _rows())
    masking.unmask(tree, "confirmatory_mask", timestamp="T")
    for path in (tree.mask_reservation("confirmatory_mask"),
                 tree.mask_key_path("confirmatory_mask"),
                 tree.masked_view("confirmatory_mask")):
        path.unlink()
    with pytest.raises(CustodyError, match="fails before mutation"):
        masking.create_mask(tree, "confirmatory_mask", _rows())


def test_key_opened_exactly_once_per_unmask(tree, monkeypatch):
    masking.create_mask(tree, "confirmatory_mask", _rows())
    key_path = str(tree.mask_key_path("confirmatory_mask"))
    opens = []
    real_open = builtins.open

    def audit(file, *args, **kwargs):
        if str(file) == key_path:
            opens.append(file)
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", audit)
    outcome = masking.unmask(tree, "confirmatory_mask", timestamp="T")
    assert len(opens) == 1        # open_mask_key is the single opener
    assert outcome["key"]


def test_apply_key_inverts_permutation(tree):
    rows = _rows()
    masking.create_mask(tree, "confirmatory_mask", rows)
    key = json.loads(
        tree.mask_key_path("confirmatory_mask").read_text())["key"]
    masked = masking.masked_rows(tree, "confirmatory_mask")
    unmasked = masking.apply_key(masked, key)
    truth = {(r["block_id"], r["arm"]): r["verdicts"]["s0"] for r in rows}
    for row in unmasked:
        assert truth[(row["block_id"], row["arm"])] == \
            row["verdicts"]["s0"]


def _concurrent_mask(ctx_args, results, index):
    from dci1v3.engine.context import synthetic_context
    from dci1v3.engine.paths import model_tree as mt
    base, repo = ctx_args
    ctx = synthetic_context(base, repo)
    tree = mt(ctx, MODEL)
    try:
        masking.create_mask(tree, "confirmatory_mask", _rows())
        results[index] = "created"
    except Exception as error:
        results[index] = f"refused:{type(error).__name__}"


def test_concurrent_mask_creation_single_winner(registered_ctx):
    manager = multiprocessing.Manager()
    results = manager.dict()
    args = (registered_ctx.evidence_root.parent,
            registered_ctx.repo_root)
    procs = [multiprocessing.Process(
        target=_concurrent_mask, args=(args, results, i))
        for i in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
    outcomes = sorted(results.values())
    assert outcomes[0] == "created"
    assert outcomes[1].startswith("refused:")
