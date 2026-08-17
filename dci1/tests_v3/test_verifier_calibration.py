"""Amendment A2 unit tests: split determinism and disjointness, autorater
parsing and invalid-output handling, report/contingency math, verifier-
freeze invalidation, and claim boundaries. All mocked; no live inference."""
from __future__ import annotations

import pytest

from dci1v3.errors import IntegrityError
from dci1v3.protocol import constants as C
from dci1v3.stages import autorater
from dci1v3.verifiers.reimplementation import (
    concordance,
    s0_count_independent,
)
from dci1v3.verifiers.boundary import BOUNDARY_CASES
from dci1v3.verifiers.target import s0_count


def _pool(items: int = 40) -> list[dict]:
    pool = []
    for i in range(items):
        cls = "pass" if i % 3 else "fail"
        pool.append({"item_id": f"item-{i:03d}",
                     "response_text": f"text {i} however",
                     "response_hash": f"h{i}",
                     "constraint_text": "Use the word however exactly 1 "
                                        "time.",
                     "n": 1, "verifier_class": cls})
    return pool


# ---------------------------------------------------------------- split
def test_split_deterministic_disjoint_stratified():
    pool = _pool()
    a = autorater.make_split(pool, model_id="m")
    b = autorater.make_split(pool, model_id="m")
    assert a["split_hash"] == b["split_hash"]
    assert a["development"] == b["development"]
    dev, cal = set(a["development"]), set(a["calibration"])
    assert not dev & cal
    assert dev | cal == {i["item_id"] for i in pool}
    by_class = {i["item_id"]: i["verifier_class"] for i in pool}
    for cls in ("pass", "fail"):
        total = sum(1 for v in by_class.values() if v == cls)
        in_dev = sum(1 for item_id in dev if by_class[item_id] == cls)
        assert in_dev == total // 2                 # stratified halves
    other = autorater.make_split(pool, model_id="other-model")
    assert other["development"] != a["development"]


def test_split_refuses_duplicate_ids():
    pool = _pool(4)
    pool.append(dict(pool[0]))
    with pytest.raises(Exception, match="duplicate"):
        autorater.make_split(pool, model_id="m")


# -------------------------------------------------------------- parsing
@pytest.mark.parametrize("raw,expected", [
    ("YES", ("valid", "pass", None)),
    ("yes\nBecause it appears once.", ("valid", "pass",
                                       "Because it appears once.")),
    ("NO.", ("valid", "fail", None)),
    ("  No \n too many occurrences ", ("valid", "fail",
                                       "too many occurrences")),
    ("Maybe; unclear.", ("invalid_output", None, None)),
    ("", ("invalid_output", None, None)),
    ("I cannot help with that.", ("refusal", None, None)),
    ("YESTERDAY it rained", ("valid", "pass", None)),  # YES-prefix rule
])
def test_parse_judgment_statuses(raw, expected):
    assert autorater.parse_judgment(raw) == expected


def test_invalid_outputs_never_recoded():
    judgments = [
        {"status": "valid", "label": "pass", "verifier_label": "pass"},
        {"status": "valid", "label": "fail", "verifier_label": "pass"},
        {"status": "invalid_output", "label": None,
         "verifier_label": "fail"},
        {"status": "refusal", "label": None, "verifier_label": "fail"},
        {"status": "generation_failure", "label": None,
         "verifier_label": "pass"},
    ]
    report = autorater.judgment_report(judgments)
    assert report["items"] == 5 and report["valid"] == 2
    assert report["invalid"] == {"invalid_output": 1, "refusal": 1,
                                 "generation_failure": 1}
    assert report["coverage"] == pytest.approx(0.4)
    # invalid rows appear in verifier marginals but never in the table
    assert sum(report["contingency"].values()) == 2


# ------------------------------------------------------------- reporting
def test_contingency_and_directional_disagreement():
    judgments = []
    for verifier, label, count in (
            ("pass", "pass", 10), ("pass", "fail", 3),
            ("fail", "pass", 2), ("fail", "fail", 15)):
        judgments += [{"status": "valid", "label": label,
                       "verifier_label": verifier}] * count
    report = autorater.judgment_report(judgments)
    assert report["contingency"] == {
        "verifier_pass_autorater_pass": 10,
        "verifier_pass_autorater_fail": 3,
        "verifier_fail_autorater_pass": 2,
        "verifier_fail_autorater_fail": 15}
    assert report["disagreements"] == 5
    assert report["directional_disagreement"] == {
        "verifier_pass_autorater_fail": 3,
        "verifier_fail_autorater_pass": 2}
    assert report["disagreement_rate"] == pytest.approx(5 / 30)
    assert report["verifier_marginal"] == {"pass": 13, "fail": 17}
    assert report["autorater_marginal"] == {"pass": 12, "fail": 18}
    assert report["not_human_validation"] is True
    assert "wilson" not in str(report).lower()      # no threshold machinery


def test_disagreement_listing_for_inspection():
    pool = {f"item-{i}": {"item_id": f"item-{i}",
                          "constraint_text": "rule",
                          "response_text": "x" * 500}
            for i in range(3)}
    judgments = [
        {"status": "valid", "label": "fail", "verifier_label": "pass",
         "item_id": "item-0", "justification": "missing occurrence"},
        {"status": "valid", "label": "pass", "verifier_label": "pass",
         "item_id": "item-1", "justification": None},
        {"status": "invalid_output", "label": None,
         "verifier_label": "fail", "item_id": "item-2",
         "justification": None},
    ]
    listing = autorater.disagreement_listing(pool, judgments)
    assert [l["item_id"] for l in listing] == ["item-0"]
    assert listing[0]["justification"] == "missing occurrence"
    assert len(listing[0]["response_excerpt"]) == 400


# ------------------------------------------------------- verifier freeze
def test_verifier_freeze_invalidation():
    manifest = {"verifier_sources": autorater.verifier_source_state()}
    autorater.assert_verifier_unchanged(manifest)     # identical: fine
    doctored = {"verifier_sources": {
        **manifest["verifier_sources"], "target.py": "0" * 64}}
    with pytest.raises(IntegrityError, match="contaminated"):
        autorater.assert_verifier_unchanged(doctored)
    missing = {"verifier_sources": {
        k: v for k, v in manifest["verifier_sources"].items()
        if k != "words.py"}}
    with pytest.raises(IntegrityError, match="contaminated"):
        autorater.assert_verifier_unchanged(missing)


# ------------------------------------------------- verifier regression
def test_reimplementation_concordance_on_boundary_and_packets():
    """The independent reimplementation agrees with S0 everywhere we can
    check offline — the regression guard behind verifier refinement."""
    items = [{"item_id": case["case_id"], "response_text": case["text"]}
             for case in BOUNDARY_CASES]
    assert concordance(items)["mismatches"] == []
    assert s0_count_independent("However, however; HOWEVER!") == 3
    assert s0_count_independent("Howeverhowever") == 0
    from pathlib import Path
    packet = Path("/home/cnm13ryan/git/dci/dci1/evidence/dci1-v3/"
                  "gemma-3n-e2b-it/gate1/annotation_packet.jsonl")
    if packet.exists():
        import json
        rows = [json.loads(l) for l in packet.read_text().splitlines()]
        for row in rows:
            assert s0_count(row["response_text"]) == \
                s0_count_independent(row["response_text"])


# -------------------------------------------------------- claim scope
def test_claim_boundaries_registered():
    assert C.MEASUREMENT_SCOPE["human_validation"] == \
        "HUMAN_VALIDATION_UNAVAILABLE"
    assert C.MEASUREMENT_SCOPE["strongest_claim"] == C.STRONGEST_CLAIM
    assert "Independent human validation is unavailable" in \
        C.STRONGEST_CLAIM
    lowered = C.STRONGEST_CLAIM.lower()
    assert "human validation" not in lowered.replace(
        "human validation is unavailable", "")
    config = autorater.load_config()
    assert "never human validation" in config["notes"].lower()


def test_synthetic_judge_statuses(tmp_path):
    from dci1v3.generation.synthetic import synthetic_judge
    from dci1v3.protocol.constants import AUTORATER_PROMPTS
    template = AUTORATER_PROMPTS["gate1-judge/1.0.0"]
    rows = [{"row_id": f"judge:{i}", "scientific_seed": i,
             "user_prompt": template.format(
                 constraint="Use the word however exactly 1 time.",
                 response="just once: however.")}
            for i in range(60)]
    ok = synthetic_judge(tmp_path, {}, rows, disagree_rate=0.0)["rows"]
    assert all(r["raw_generation"].startswith("YES") for r in ok)
    flipped = synthetic_judge(tmp_path, {}, rows, disagree_rate=1.0)
    assert all(r["raw_generation"].startswith("NO")
               for r in flipped["rows"])
    invalid = synthetic_judge(tmp_path, {}, rows, invalid_rate=1.0)
    statuses = {autorater.parse_judgment(r["raw_generation"])[0]
                for r in invalid["rows"]}
    assert statuses == {"invalid_output"}


# ----------------------------------------------------- A2.1 invariants
def test_freeze_refused_before_designated_dev_runs(registered_ctx):
    """The study-level freeze cannot occur before every designated
    (non-terminal) replication completed gate1-dev."""
    from dci1v3.errors import ProtocolError
    from dci1v3.stages.gate1 import verifier_freeze
    with pytest.raises(ProtocolError, match="missing gate1-dev"):
        verifier_freeze(registered_ctx)
    assert not (registered_ctx.study_root
                / "verifier_freeze.json").exists()


def test_binding_mismatch_detection():
    from dci1v3.stages.gate1 import binding_mismatches
    entry = {"pool_hash": "a", "split_hash": "b", "dev_record_hash": "c"}
    assert binding_mismatches(entry, dict(entry)) == []
    assert binding_mismatches(entry, {**entry, "pool_hash": "X"}) == \
        ["pool_hash"]
    assert binding_mismatches({}, entry) == \
        ["dev_record_hash", "pool_hash", "split_hash"]


def test_calibration_one_shot_via_ledger(registered_ctx):
    """Exposed calibration data can never be re-presented as fresh: the
    append-only ledger refuses before mutation, in every prior state."""
    from dci1v3.engine.artifacts import record_state
    from dci1v3.engine.paths import model_tree
    from dci1v3.errors import ProtocolError
    from dci1v3.stages.gate1 import assert_calibration_unexposed

    tree = model_tree(registered_ctx, "gemma-3n-e2b-it")
    assert_calibration_unexposed(tree)            # no prior state: fine
    path = tree.root / "gate1_calibration.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}")
    kwargs = dict(artifact_id="op:gate1-calibrate", path=path,
                  artifact_type="gate_record", stage="gate1-calibrate",
                  producing_commit="c" * 40)
    record_state(tree, state="generated", **kwargs)
    record_state(tree, state="committed", **kwargs)
    with pytest.raises(ProtocolError, match="one-shot"):
        assert_calibration_unexposed(tree)
    record_state(tree, state="superseded", **{
        **kwargs, "artifact_type": "superseded_non_evidence"})
    with pytest.raises(ProtocolError, match="genuinely new untouched"):
        assert_calibration_unexposed(tree)


# ------------------------------------------------ dev-loop label fidelity
def _wording_pool_item(i: int, n: int, count: int, stored_class: str):
    return {"item_id": f"live-{i:02d}",
            "response_text": " ".join(["however"] * count) or "no word",
            "response_hash": f"lh{i}",
            "constraint_text": f"Use the word however exactly {n} "
                               f"{'time' if n == 1 else 'times'}.",
            "n": n, "verifier_class": stored_class}


def test_judgments_use_live_verifier_not_frozen_stratum(tmp_path):
    """The comparison label tracks the CURRENT verifier (the dev loop
    exists to refine it); the split stratum stays frozen."""
    from dci1v3.generation.synthetic import synthetic_judge
    # Live verdict is pass (count == n) but the stored stratum says fail —
    # as it would after a verifier refinement changed the verdict.
    items = [_wording_pool_item(0, 2, 2, stored_class="fail"),
             _wording_pool_item(1, 1, 3, stored_class="pass")]
    judgments = autorater.run_autorater(
        tmp_path / "dev", items, config=autorater.load_config(),
        phase="development",
        generate_fn=lambda d, p, r: synthetic_judge(d, p, r,
                                                    disagree_rate=0.0),
        environment={})
    by_id = {j["item_id"]: j for j in judgments}
    assert by_id["live-00"]["verifier_label"] == "pass"   # live, not stored
    assert by_id["live-00"]["split_class"] == "fail"      # frozen stratum
    assert by_id["live-01"]["verifier_label"] == "fail"
    assert by_id["live-01"]["split_class"] == "pass"


def test_generation_failures_retry_and_attempts_preserved(tmp_path):
    """Transient judge failures are retried on the next run (still
    reported as generation_failure until repaired) and every generation
    attempt keeps its own raw run directory."""
    from dci1v3.generation.synthetic import synthetic_judge
    items = [_wording_pool_item(i, 1, 1, "pass") for i in range(4)]
    fail_ids = {"judge:live-00", "judge:live-01"}

    def flaky(run_dir, plan, rows):
        outcome = synthetic_judge(run_dir, plan, rows, disagree_rate=0.0)
        for row in outcome["rows"]:
            if row["row_id"] in fail_ids:
                row["outcome"] = "ENGINE_ERROR"
        return outcome

    phase_dir = tmp_path / "dev"
    config = autorater.load_config()
    first = autorater.run_autorater(phase_dir, items, config=config,
                                    phase="development",
                                    generate_fn=flaky, environment={})
    statuses = {j["item_id"]: j["status"] for j in first}
    assert statuses["live-00"] == "generation_failure"
    assert statuses["live-02"] == "valid"
    assert (phase_dir / "backend_runs" / "attempt0").exists()

    second = autorater.run_autorater(
        phase_dir, items, config=config, phase="development",
        generate_fn=lambda d, p, r: synthetic_judge(d, p, r,
                                                    disagree_rate=0.0),
        environment={})
    assert all(j["status"] == "valid" for j in second)
    assert (phase_dir / "backend_runs" / "attempt1").exists()
    ids = [r["row_id"] for r in
           autorater.CacheWriter(phase_dir / "judge_rows.jsonl").rows()]
    assert len(ids) == len(set(ids)) == 4        # append-once, repaired
