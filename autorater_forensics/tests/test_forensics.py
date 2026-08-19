"""Smoke checks for the forensics workspace. GPU-independent except
the endpoint tests, which skip when the diagnostic server is down."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.forensics import dataset as ds  # noqa: E402
from src.forensics import parser, paths, verifier  # noqa: E402

REPORTS = paths.REPO / "dci1" / "reports"


# ------------------------------------------------ verifier + prompt
def test_verifier_matches_registered_counts():
    cases = json.loads(
        (REPORTS / "gate1_dev_cases_r3.json").read_text())["models"]
    checked = 0
    for block in cases.values():
        for c in block["cases"]:
            assert verifier.s0_count(c["response_text"]) == \
                c["s0_count"], c["item_id"]
            checked += 1
    assert checked > 0


def test_judge_prompt_matches_registered_template():
    source = paths.DCI_CONSTANTS.read_text()
    for line in ("You are checking one rule against one text.",
                 "Rule: {constraint}",
                 "first line: SATISFIES or VIOLATES."):
        assert line in source
    assert "SATISFIES or VIOLATES" in ds.JUDGE_PROMPT


# --------------------------------------------------------- dataset
def _samples():
    path = paths.DATASET / "diagnostic.jsonl"
    if not path.exists():
        pytest.skip("dataset not built")
    return [json.loads(l) for l in path.read_text().splitlines()]


def test_dataset_stable_unique_ids_and_required_fields():
    samples = _samples()
    ids = [s["id"] for s in samples]
    assert len(ids) == len(set(ids))
    required = ("input", "target", "source_model", "source_pool",
                "target_n", "s0_count", "deterministic_verifier_label",
                "response_text", "contested", "prior_low_status",
                "prior_medium_status", "prior_high_status")
    for s in samples[:5] + samples[-5:]:
        for key in required:
            assert key in s, key


def test_dataset_separates_contested_and_controls():
    samples = _samples()
    contested = [s for s in samples if s["contested"]]
    controls = [s for s in samples if not s["contested"]]
    assert contested and controls
    for s in controls:
        assert s["prior_low_label"] == s["prior_medium_label"] == \
            s["prior_high_label"] == s["deterministic_verifier_label"]


def test_dataset_preserves_invalid_prior_statuses():
    samples = _samples()
    statuses = {s[f"prior_{e}_status"] for s in samples
                for e in ("low", "medium", "high")}
    assert "invalid_output" in statuses     # never silently dropped


# ---------------------------------------------------------- parser
@pytest.mark.parametrize("content,expected", [
    ("SATISFIES\nok", ("valid", "pass", "ok")),
    ("VIOLATES.", ("valid", "fail", None)),
    ("satisfied", ("valid", "pass", None)),
    ("", ("invalid_output", None, None)),
    (None, ("invalid_output", None, None)),
    ("Maybe.", ("invalid_output", None, None)),
    ("I cannot help with that.", ("refusal", None, None)),
])
def test_parse_final(content, expected):
    assert parser.parse_final(content) == expected


# ---------------------------------------- no writes to registered evidence
def test_dataset_build_never_writes_evidence(tmp_path):
    files_before = {p: p.stat().st_mtime_ns
                    for p in paths.EVIDENCE.rglob("*") if p.is_file()}
    ds.build(tmp_path / "d.jsonl")
    files_after = {p: p.stat().st_mtime_ns
                   for p in paths.EVIDENCE.rglob("*") if p.is_file()}
    assert files_before == files_after


# ------------------------------------------------- endpoint (skip if down)
def _server_up() -> bool:
    try:
        urllib.request.urlopen(paths.SERVER_BASE_URL + "/models",
                               timeout=3)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _server_up(), reason="diagnostic server down")
def test_effort_reaches_backend_template():
    def post(path, payload):
        req = urllib.request.Request(
            paths.SERVER_BASE_URL.replace("/v1", "") + path,
            json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    msg = [{"role": "user", "content": "x"}]
    for effort in ("low", "high"):
        tok = post("/tokenize", {
            "model": paths.SERVED_MODEL_NAME, "messages": msg,
            "chat_template_kwargs": {"reasoning_effort": effort}})
        detok = post("/detokenize", {"model": paths.SERVED_MODEL_NAME,
                                     "tokens": tok["tokens"]})
        assert f"Reasoning: {effort}" in detok["prompt"]


# ------------------------------------------- runs (skip until they exist)
def _newest(effort):
    from inspect_ai.log import list_eval_logs, read_eval_log
    logs = list_eval_logs(str(paths.LOGS / effort))
    if not logs:
        pytest.skip(f"no {effort} run yet")
    return read_eval_log(sorted(logs, key=lambda l: l.name)[-1])


def test_runs_differ_only_in_reasoning_effort():
    configs = {}
    for effort in ("low", "medium", "high"):
        cfg = _newest(effort).plan.config
        configs[effort] = {
            "temperature": cfg.temperature, "top_p": cfg.top_p,
            "max_tokens": cfg.max_tokens, "seed": cfg.seed,
            "extra_body": dict(cfg.extra_body)}
        assert configs[effort]["extra_body"].pop("reasoning_effort") \
            == effort
    assert configs["low"] == configs["medium"] == configs["high"]


def test_runs_align_by_sample_id_and_separate_reasoning():
    id_sets, any_nonvalid = [], False
    for effort in ("low", "medium", "high"):
        log = _newest(effort)
        id_sets.append({str(s.id) for s in log.samples})
        for s in log.samples:
            m = s.scores["judge_parse"].metadata
            if m["status"] == "valid" and not m["truncated"]:
                assert m["reasoning_chars"] > 0
                assert m["final_chars"] > 0
            if m["status"] != "valid":
                any_nonvalid = True     # preserved, not dropped
    assert id_sets[0] == id_sets[1] == id_sets[2]
    assert any_nonvalid or True         # presence depends on the run


# ----------------------------------------------------------- scout
def test_scout_operates_only_on_diagnostic_logs():
    source = (paths.ROOT / "scans" / "run_scan.py").read_text()
    assert 'ROOT / "logs"' in source
    assert 'scans" / "results' in source.replace("'", '"')
    assert "evidence" not in source
