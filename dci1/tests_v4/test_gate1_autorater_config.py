"""The §10.4 judging condition must be inside the hashed configuration.

Two conditions that demonstrably produce different judgments must produce
different ``config_hash`` values, or ``assert_no_config_drift`` cannot detect a
swap between them.

**A sharp edge in the registered helper, pinned here.**
``dci1v4.stages.autorater.CONFIG_FIELDS`` does not include the rendered
reasoning condition, and ``build_config`` keeps only the declared fields. A
caller that passes ``chat_template_kwargs`` as a sibling of ``decoding`` has it
silently dropped, and medium and high then hash identically. The v4 driver
places it INSIDE ``decoding``, which is a declared field. These tests pin that
the driver does so, and record the failure mode.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "tools"))

from dci1v4.errors import IntegrityError                          # noqa: E402
from dci1v4.stages import autorater                               # noqa: E402

import gate1_autorater_v4 as ar                                   # noqa: E402


def test_every_condition_has_a_distinct_config_hash():
    hashes = {c: ar.judge_config(c)["config_hash"] for c in ar.CONDITIONS}
    assert len(set(hashes.values())) == len(hashes), hashes


def test_the_rendered_reasoning_condition_is_inside_the_hash():
    for condition, spec in ar.CONDITIONS.items():
        config = ar.judge_config(condition)
        assert (config["decoding"]["chat_template_kwargs"]
                == {"reasoning_effort": spec["reasoning_effort"]})


def test_drift_between_two_conditions_is_detected():
    medium = ar.judge_config("v4prompt-medium")
    high = ar.judge_config("v4prompt-high")
    with pytest.raises(IntegrityError):
        autorater.assert_no_config_drift(medium, high)


def test_the_registered_helper_drops_a_sibling_reasoning_field():
    """The failure mode this file exists to prevent, demonstrated.

    Passing the reasoning condition as a sibling of the declared fields is
    silently ignored, and the two conditions become indistinguishable.
    """
    def naive(effort):
        return autorater.build_config(
            "gpt-oss-20b", backend="vllm", prompt_version="p/1",
            prompt_hash="deadbeef", parser_version="q/1",
            label_mapping={"SATISFIES": "pass"},
            decoding={"policy": "greedy"}, output_cap=2048,
            chat_template_kwargs={"reasoning_effort": effort})
    assert naive("medium")["config_hash"] == naive("high")["config_hash"], (
        "if this assertion starts failing, CONFIG_FIELDS has been extended to "
        "cover the rendered reasoning condition and the workaround in "
        "tools/gate1_autorater_v4.py can be removed")
    assert "chat_template_kwargs" not in naive("high")


def test_prompt_version_is_part_of_the_hash():
    carried = ar.judge_config("carried-medium")
    v4 = ar.judge_config("v4prompt-medium")
    assert carried["prompt_version"] != v4["prompt_version"]
    assert carried["prompt_hash"] != v4["prompt_hash"]
    assert carried["config_hash"] != v4["config_hash"]


def test_execution_is_serialised_at_concurrency_one():
    for condition in ar.CONDITIONS:
        config = ar.judge_config(condition)
        assert config["execution_concurrency"] == 1
        assert config["execution_mode"] == "serialised"


def test_the_judge_is_disjoint_from_the_study_replications():
    from dci1v4.models.registry import MODEL_KEYS
    for condition in ar.CONDITIONS:
        assert ar.judge_config(condition)["judge_model_key"] not in MODEL_KEYS


@pytest.mark.skipif(not ar.EVIDENCE.exists(), reason="no stored evidence tree")
def test_the_split_is_disjoint_and_deterministic():
    items = ar.build_items()
    first, second = ar.split_pool(items), ar.split_pool(items)
    assert first["split_hash"] == second["split_hash"]
    dev = {i["item_id"] for i in first["development"]}
    cal = {i["item_id"] for i in first["calibration"]}
    assert not dev & cal
    assert len(dev) + len(cal) == len(items)


@pytest.mark.skipif(not ar.EVIDENCE.exists(), reason="no stored evidence tree")
def test_the_split_preserves_the_verifier_class():
    """Overwriting verifier_class to carry a stratum label would corrupt both
    the strata downstream and the agreement denominator."""
    for item in ar.split_pool(ar.build_items())["development"]:
        assert item["verifier_class"] in ("pass", "fail")


@pytest.mark.skipif(not ar.EVIDENCE.exists(), reason="no stored evidence tree")
def test_the_subsample_is_stratum_balanced():
    split = ar.split_pool(ar.build_items())
    sample = ar.subsample(split["development"], 48)
    counts: dict[str, int] = {}
    for item in sample:
        counts[ar.stratum(item)] = counts.get(ar.stratum(item), 0) + 1
    assert len(sample) == 48
    assert set(counts.values()) == {8}, counts


def test_the_parser_never_recodes_a_non_verdict_into_a_label():
    for text in ("", "   ", "maybe", "<|channel|>analysis<|message|>thinking",
                 "I cannot help with that."):
        status, label, _ = ar.parse(text)
        assert status != ar.VALID
        assert label is None


def test_the_parser_reads_the_harmony_final_channel():
    raw = ("<|channel|>analysis<|message|>reasoning here<|end|><|start|>"
           "assistant<|channel|>final<|message|>VIOLATES\nno however<|return|>")
    status, label, why = ar.parse(raw)
    assert (status, label) == (ar.VALID, "fail")
    assert why == "no however"
