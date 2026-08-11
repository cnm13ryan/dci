"""Tests for the semicolon-splice intervention.

Covers the pieces the experiment's validity rests on: that the two route
conditions differ in exactly one prompt line, that the semicolon-count and
splice diagnostics measure what they claim, that Omega is the contrast the
directive defines, and that the scientific seed is a function of the
experimental unit rather than of file position.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dci_exploratory import arbprogram as A
from dci_exploratory import extensions, harvest

extensions.register()
STATE = harvest.load()

from dci.verifiers.rules import v_exact_char_total  # noqa: E402
from dci_exploratory.extensions import splice_count  # noqa: E402


# ------------------------------------------------------- design construction
@pytest.fixture(scope="module")
def preflight_design(tmp_path_factory):
    out = tmp_path_factory.mktemp("ssi") / "design.jsonl"
    result = subprocess.run(
        [sys.executable, str(ROOT / "ssi_design.py"), str(out), "--mode",
         "preflight", "--tasks", "6", "--offset", "32", "--replicates", "2"],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]
    return [json.loads(line) for line in out.open()], result.stdout


def test_route_design_has_the_expected_shape(preflight_design):
    rows, _ = preflight_design
    assert len(rows) == 6 * 2 * 1 * 2          # tasks x routes x arms x replicates
    assert {r["route"] for r in rows} == {"off_route", "anti_splice"}
    assert {r["order"] for r in rows} == {"QACD"}
    assert {r["load"] for r in rows} == {4}


def test_the_semicolon_requirement_is_present_in_every_cell(preflight_design):
    rows, _ = preflight_design
    for row in rows:
        assert row["ordered_ids"][2] == "X_SEMICOLON_FREE"
        assert "Use exactly 1 semicolon" in row["user_prompt"]


def test_the_route_instruction_never_moves_slot(preflight_design):
    rows, _ = preflight_design
    for row in rows:
        assert row["ordered_ids"][3] == row["route_id"]
        assert row["user_prompt"].rstrip().split("\n")[-1].startswith("4. ")


def test_matched_prompts_differ_in_exactly_the_D_line(preflight_design):
    rows, stdout = preflight_design
    groups = {}
    for row in rows:
        groups.setdefault((row["task_id"], row["arm"], row["replicate"]), {})[
            row["route"]] = row["user_prompt"]
    for key, texts in groups.items():
        left = texts["off_route"].split("\n")
        right = texts["anti_splice"].split("\n")
        differing = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
        assert differing == [len(left) - 1], (key, differing)
    assert "differ in exactly one line" in stdout


def test_preflight_carries_no_focal_arm(preflight_design):
    """If the preflight had a focal arm, the gate could see the outcome."""
    rows, _ = preflight_design
    assert {r["arm"] for r in rows} == {"C_L3"}


def test_preflight_never_touches_the_evaluation_tasks(preflight_design):
    rows, _ = preflight_design
    evaluation = {t["task_id"] for t in STATE.TASKS.to_dict("records")
                  if t["split"] == "pilot"}
    assert not ({r["task_id"] for r in rows} & evaluation)


# ------------------------------------------------------------- the wordings
def test_route_instructions_are_the_registry_wordings():
    assert harvest.compose_prompt("", ["X_NO_SEMI_SPLICE"], 0).endswith(
        "Do not use a semicolon to join two complete sentences.")
    assert harvest.compose_prompt("", ["X_NO_EXCLAM"], 0).endswith(
        "Do not use any exclamation marks.")


# ------------------------------------------------------------- diagnostics
def test_semicolon_count_verifier():
    assert v_exact_char_total("Rain falls; rivers rise.", ";", 1).binary_pass == 1
    assert v_exact_char_total("Rain falls, rivers rise.", ";", 1).binary_pass == 0
    assert v_exact_char_total("Rain; rivers; wind.", ";", 1).binary_pass == 0


def test_splice_count_flags_a_clause_join():
    assert splice_count("Rain falls steadily; this soaks the ground.", "semicolon") == 1
    assert splice_count("Rain falls steadily; it soaks the ground now.", "semicolon") == 1


def test_splice_count_does_not_flag_a_short_list_item():
    """The Round 7 revision's purpose: a list is not a clause join."""
    assert splice_count("The parts are a lever; a spring; a base.", "semicolon") == 0


def test_splice_count_is_zero_without_the_mark():
    assert splice_count("Rain falls steadily. It soaks the ground.", "semicolon") == 0


def test_the_anti_splice_verifier_is_the_splice_proxy():
    """Route compliance and the manipulation check are the SAME measurement.

    Pinned because it changes how the preflight may be read: they are not two
    independent signals agreeing.
    """
    joined = "Rain falls steadily; this soaks the ground."
    clean = "Rain falls steadily. It soaks the ground; heavily."
    assert int(STATE.verify(joined, "X_NO_SEMI_SPLICE").binary_pass) == 0
    assert splice_count(joined, "semicolon") > 0
    assert int(STATE.verify(clean, "X_NO_SEMI_SPLICE").binary_pass) == \
        int(splice_count(clean, "semicolon") == 0)


def test_off_route_instruction_is_independently_verifiable():
    assert int(STATE.verify("Rain falls.", "X_NO_EXCLAM").binary_pass) == 1
    assert int(STATE.verify("Rain falls!", "X_NO_EXCLAM").binary_pass) == 0


# ---------------------------------------------------------------- estimands
def route_frame() -> pd.DataFrame:
    """Two tasks, hand-chosen A-failures, one background, two routes."""
    plan = {
        ("T1", "off_route", "B"): 1.0, ("T1", "off_route", "C_L3"): 0.0,
        ("T1", "anti_splice", "B"): 0.0, ("T1", "anti_splice", "C_L3"): 0.0,
        ("T2", "off_route", "B"): 1.0, ("T2", "off_route", "C_L3"): 0.0,
        ("T2", "anti_splice", "B"): 1.0, ("T2", "anti_splice", "C_L3"): 0.0,
    }
    return pd.DataFrame([
        {"task_id": task, "route": route, "arm": arm, "A_failure": failure,
         "background": A.AMPLIFIER, "order": "QACD", "reasoning_budget": 4096}
        for (task, route, arm), failure in plan.items()])


def test_tau_accepts_an_extra_selector():
    frame = route_frame()
    tau = A.tau(frame, background=A.AMPLIFIER, order="QACD",
                reasoning_budget=4096, route="off_route")
    assert tau["T1"] == pytest.approx(1.0)
    assert tau["T2"] == pytest.approx(1.0)


def test_omega_is_closed_minus_control_within_task():
    frame = route_frame()
    om = A.omega(frame, order="QACD", reasoning_budget=4096)
    assert om["T1"] == pytest.approx(-1.0)   # closing the route removed it
    assert om["T2"] == pytest.approx(0.0)    # closing it changed nothing
    assert om.mean() == pytest.approx(-0.5)


def test_omega_is_negative_when_closing_the_route_helps():
    """The sign convention the directive fixes: Omega < 0 means less interference."""
    frame = route_frame()
    assert A.omega(frame, order="QACD", reasoning_budget=4096).mean() < 0


def test_omega_does_not_silently_reuse_the_background_contrast():
    frame = route_frame()
    # `delta` compares two BACKGROUNDS; this frame has only one, so it is empty.
    assert A.delta(frame, order="QACD", reasoning_budget=4096).empty
    assert not A.omega(frame, order="QACD", reasoning_budget=4096).empty


# --------------------------------------------------------------- seeds
def scientific_seed(task_id: str, replicate: int, phase: str,
                    master: int = 20260812) -> int:
    import hashlib
    key = f"{master}|{task_id}|{replicate}|{phase}".encode()
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(),
                          "big") % (2 ** 31 - 1)


def test_seed_depends_on_the_unit_not_on_file_position():
    assert scientific_seed("PLT01", 0, "answer") == scientific_seed("PLT01", 0, "answer")
    assert scientific_seed("PLT01", 0, "answer") != scientific_seed("PLT01", 1, "answer")
    assert scientific_seed("PLT01", 0, "answer") != scientific_seed("PLT02", 0, "answer")
    assert scientific_seed("PLT01", 0, "think") != scientific_seed("PLT01", 0, "answer")


def test_matched_route_conditions_share_a_seed():
    """Route is not a seed input, so the two arms are common-random-number paired."""
    assert scientific_seed("PLT01", 2, "answer") == scientific_seed("PLT01", 2, "answer")
