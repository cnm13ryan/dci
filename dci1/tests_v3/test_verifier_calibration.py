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
    ("SATISFIES", ("valid", "pass", None)),
    ("satisfies\nExactly one occurrence.", ("valid", "pass",
                                            "Exactly one occurrence.")),
    ("VIOLATES.", ("valid", "fail", None)),
    ("  Violates \n too many occurrences ", ("valid", "fail",
                                             "too many occurrences")),
    ("SATISFIED", ("valid", "pass", None)),      # registered prefix rule
    ("Maybe; unclear.", ("invalid_output", None, None)),
    ("YES", ("invalid_output", None, None)),     # superseded vocabulary
    ("", ("invalid_output", None, None)),
    ("I cannot help with that.", ("refusal", None, None)),
])
def test_parse_judgment_statuses(raw, expected):
    assert autorater.parse_judgment(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    # A full harmony transcript: only the final channel is judged.
    ("<|channel|>analysis<|message|>Count is 1, matches n.<|end|>"
     "<|start|>assistant<|channel|>final<|message|>SATISFIES\n"
     "one occurrence<|return|>",
     ("valid", "pass", "one occurrence")),
    ("<|channel|>analysis<|message|>Too many. The word VIOLATES? yes."
     "<|end|><|start|>assistant<|channel|>final<|message|>VIOLATES"
     "<|return|>",
     ("valid", "fail", None)),
    # Truncated at the cap before the final channel: never a label.
    ("<|channel|>analysis<|message|>Counting occurrences of the wo",
     ("invalid_output", None, None)),
    # Final channel present but empty.
    ("<|channel|>analysis<|message|>x<|end|><|start|>assistant"
     "<|channel|>final<|message|><|return|>",
     ("invalid_output", None, None)),
])
def test_parse_judgment_harmony_final_channel(raw, expected):
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
                          "response_text": "x" * 500,
                          "n": 2, "source": "prescreen"}
            for i in range(3)}
    judgments = [
        {"status": "valid", "label": "fail", "verifier_label": "pass",
         "item_id": "item-0", "justification": "missing occurrence",
         "split_class": "pass"},
        {"status": "valid", "label": "pass", "verifier_label": "pass",
         "item_id": "item-1", "justification": None,
         "split_class": "pass"},
        {"status": "invalid_output", "label": None,
         "verifier_label": "fail", "item_id": "item-2",
         "justification": None, "split_class": "fail"},
    ]
    listing = autorater.disagreement_listing(pool, judgments)
    assert [l["item_id"] for l in listing] == ["item-0"]
    assert listing[0]["justification"] == "missing occurrence"
    # every disagreement carries the COMPLETE response, never an excerpt
    assert listing[0]["response_text"] == "x" * 500
    assert listing[0]["split_class"] == "pass"
    assert listing[0]["n"] == 2 and listing[0]["source"] == "prescreen"


def test_disagreement_breakdown_by_n_and_source():
    pool = {"a": {"item_id": "a", "n": 1, "source": "prescreen"},
            "b": {"item_id": "b", "n": 1, "source": "validation"},
            "c": {"item_id": "c", "n": 5, "source": "validation"}}
    judgments = [
        {"status": "valid", "label": "fail", "verifier_label": "pass",
         "item_id": "a"},
        {"status": "valid", "label": "pass", "verifier_label": "fail",
         "item_id": "b"},
        {"status": "valid", "label": "fail", "verifier_label": "pass",
         "item_id": "c"},
        {"status": "invalid_output", "label": None,
         "verifier_label": "fail", "item_id": "c"},
    ]
    breakdown = autorater.disagreement_breakdown(pool, judgments)
    assert breakdown["by_n"] == {"1": 2, "5": 1}
    assert breakdown["by_source"] == {"prescreen": 1, "validation": 2}


def test_agreement_identification_interval():
    """[a/N, (a+(N-N_v))/N]: the full-set agreement rate is only
    interval-identified when some judgments are invalid."""
    judgments = (
        [{"status": "valid", "label": "pass", "verifier_label": "pass"}]
        * 6
        + [{"status": "valid", "label": "fail",
            "verifier_label": "pass"}] * 2
        + [{"status": "refusal", "label": None,
            "verifier_label": "fail"}] * 2)
    interval = autorater.judgment_report(judgments)[
        "agreement_identification_interval"]
    assert interval["agree_valid"] == 6
    assert interval["lower"] == pytest.approx(0.6)
    assert interval["upper"] == pytest.approx(0.8)
    # fully valid: the interval collapses to the point estimate
    point = autorater.judgment_report(judgments[:8])[
        "agreement_identification_interval"]
    assert point["lower"] == point["upper"] == pytest.approx(6 / 8)


def test_stability_comparison_reports_flips_never_votes():
    primary = [
        {"item_id": "a", "status": "valid", "label": "pass"},
        {"item_id": "b", "status": "valid", "label": "fail"},
        {"item_id": "c", "status": "refusal", "label": None},
    ]
    stable = autorater.stability_comparison(primary, list(primary))
    assert stable["stable"] and stable["label_flips"] == 0 \
        and stable["status_changes"] == 0
    wobbly = [
        {"item_id": "a", "status": "valid", "label": "fail"},   # flip
        {"item_id": "b", "status": "invalid_output", "label": None},
        {"item_id": "c", "status": "refusal", "label": None},
    ]
    report = autorater.stability_comparison(primary, wobbly)
    assert not report["stable"]
    assert report["label_flips"] == 1 and report["status_changes"] == 1
    assert report["flipped_items"][0]["item_id"] == "a"
    assert report["status_changed_items"][0]["item_id"] == "b"
    assert "vote" not in str(report).lower()


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
    template = AUTORATER_PROMPTS["gate1-judge/2.0.0"]
    rows = [{"row_id": f"judge:{i}", "scientific_seed": i,
             "user_prompt": template.format(
                 constraint="Use the word however exactly 1 time.",
                 response="just once: however.")}
            for i in range(60)]
    ok = synthetic_judge(tmp_path, {}, rows, disagree_rate=0.0)["rows"]
    assert all(r["raw_generation"].startswith("SATISFIES") for r in ok)
    flipped = synthetic_judge(tmp_path, {}, rows, disagree_rate=1.0)
    assert all(r["raw_generation"].startswith("VIOLATES")
               for r in flipped["rows"])
    invalid = synthetic_judge(tmp_path, {}, rows, invalid_rate=1.0)
    statuses = {autorater.parse_judgment(r["raw_generation"])[0]
                for r in invalid["rows"]}
    assert statuses == {"invalid_output"}


# ------------------------------------------------- A3 frozen protocol
def test_judge_is_never_a_registered_replication():
    """The autorater must not be a model the verifier scores."""
    from dci1v3.errors import ProtocolError
    from dci1v3.models.registry import JUDGE_BY_KEY, MODEL_KEYS, get_judge
    assert not set(JUDGE_BY_KEY) & set(MODEL_KEYS)
    for model_key in MODEL_KEYS:
        with pytest.raises(ProtocolError, match="not a registered judge"):
            get_judge(model_key)
    config = autorater.load_config()
    assert config["judge_model_key"] in JUDGE_BY_KEY
    assert config["judge_model_key"] not in MODEL_KEYS


def test_config_binds_the_frozen_protocol():
    """Revision, parser, mapping, cap, and greedy decoding are all
    validated against the registered constants and covered by the
    config hash."""
    config = autorater.load_config()
    judge = __import__("dci1v3.models.registry",
                       fromlist=["get_judge"]).get_judge(
        config["judge_model_key"])
    assert config["judge_revision"] == judge.revision
    assert config["parser_version"] == C.AUTORATER_PARSER_VERSION
    assert config["label_mapping"] == C.AUTORATER_LABEL_MAPPING
    assert config["decoding"]["max_new_tokens"] == C.AUTORATER_CAP
    assert config["decoding"]["policy"] == "greedy"
    # A3.1: the judging condition is part of the hashed config and must
    # equal the judge registry's declaration.
    assert config["chat_template_kwargs"] == judge.chat_template_kwargs
    assert config["chat_template_kwargs"] == {"reasoning_effort":
                                              "high"}
    for key in ("judge_revision", "parser_version", "label_mapping",
                "backend", "chat_template_kwargs"):
        assert key in config     # covered by config_hash (computed over
    #                              every non-hash key at load time)


def test_config_refuses_judging_condition_drift(tmp_path):
    import json as _json
    from dci1v3.errors import ProtocolError
    raw = _json.loads(
        (autorater._CONFIG_PATH).read_text())
    raw["chat_template_kwargs"] = {"reasoning_effort": "low"}
    doctored = tmp_path / "autorater.json"
    doctored.write_text(_json.dumps(raw))
    with pytest.raises(ProtocolError, match="single-valued"):
        autorater.load_config(doctored)


def test_run_autorater_plan_carries_hashed_judging_condition(tmp_path):
    from dci1v3.generation.synthetic import synthetic_judge
    seen = {}

    def capturing(run_dir, plan, rows):
        seen.update(plan)
        return synthetic_judge(run_dir, plan, rows, disagree_rate=0.0)

    items = [_wording_pool_item(0, 1, 1, "pass")]
    config = autorater.load_config()
    autorater.run_autorater(tmp_path / "dev", items, config=config,
                            phase="development", generate_fn=capturing,
                            environment={})
    assert seen["chat_template_kwargs"] == config["chat_template_kwargs"]
    assert seen["generation_ceiling"] == C.AUTORATER_CAP
    assert seen["skip_special_tokens"] is False
    assert seen["tensor_parallel_size"] == 1


def test_stale_judge_rows_detected_and_parked(registered_ctx):
    """A3.1 supersession: judge rows from a prior configuration are
    detected, parked under superseded/<old-prefix>/ with ledger
    entries, and never deleted."""
    import json as _json

    from dci1v3.engine.artifacts import artifact_states
    from dci1v3.engine.paths import model_tree
    from dci1v3.stages.gate1 import park_stale_judgments

    config = autorater.load_config()
    tree = model_tree(registered_ctx, "gemma-3n-e2b-it")
    auto_dir = tree.data_dir("gate1") / "autorater"
    writer = autorater.CacheWriter(auto_dir / "dev" / "judge_rows.jsonl")
    writer.append([{"row_id": "judge:x", "item_id": "x",
                    "prompt_hash": "p" * 64, "config_hash": "0" * 64,
                    "raw_generation": "SATISFIES", "finish_reason":
                    "stop", "outcome": "OK"}])
    (tree.root / "gate1_dev.json").write_text(_json.dumps({"old": True}))

    old = autorater.stale_config_rows(auto_dir / "dev", config)
    assert old == "0" * 64
    assert autorater.stale_config_rows(auto_dir / "dev_repeat",
                                       config) is None

    parked = park_stale_judgments(tree, auto_dir, {"dev": old},
                                  producing_commit="c" * 40)
    assert not (auto_dir / "dev").exists()
    assert (parked / "dev" / "judge_rows.jsonl").exists()
    assert _json.loads((parked / "gate1_dev.json").read_text()) == \
        {"old": True}
    state = artifact_states(tree)[f"autorater-dev:{'0' * 12}"]
    assert state["state"] == "superseded"


def test_stale_cached_judge_rows_fail_closed(tmp_path):
    """Cached judgments are reusable only under valid provenance: a row
    produced under a different configuration refuses the run."""
    import json

    from dci1v3.engine import fs as engine_fs
    from dci1v3.generation.synthetic import synthetic_judge

    items = [_wording_pool_item(0, 1, 1, "pass")]
    config = autorater.load_config()
    phase_dir = tmp_path / "dev"
    autorater.run_autorater(
        phase_dir, items, config=config, phase="development",
        generate_fn=lambda d, p, r: synthetic_judge(d, p, r,
                                                    disagree_rate=0.0),
        environment={})
    rows_path = phase_dir / "judge_rows.jsonl"
    row = json.loads(rows_path.read_text().splitlines()[0])
    row["config_hash"] = "0" * 64
    row = engine_fs.row_with_hash(
        {k: v for k, v in row.items() if k != "row_hash"})
    rows_path.write_text(json.dumps(row, sort_keys=True,
                                    ensure_ascii=False) + "\n")
    with pytest.raises(IntegrityError, match="different autorater"):
        autorater.run_autorater(
            phase_dir, items, config=config, phase="development",
            generate_fn=lambda d, p, r: synthetic_judge(
                d, p, r, disagree_rate=0.0),
            environment={})


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
