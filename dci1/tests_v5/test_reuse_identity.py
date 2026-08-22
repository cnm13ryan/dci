"""§26 and §34 D16: what a stored generation may satisfy, and what it may not.

D16 is closed at ``complete_population``: Calibration-B remeasures the whole
carried candidate set rather than only what Calibration-A admitted. The
researcher accepted the generation cost and refused the *accidental* part of
it --- a row whose complete scientific identity already exists is reused, not
regenerated.

That makes the reuse key load-bearing in a way it was not before. These tests
are the seven ways the key has to move, and the one way it must not.

The last of them is the one D16 makes dangerous. Calibration-A and
Calibration-B measure the same quantities with the same functions on
different topics, so a reuse rule that keyed on anything less than the split
could satisfy a Calibration-B row with a Calibration-A generation --- and
§13.7's two estimates are independent only if their rows are.
"""
from __future__ import annotations

from typing import Any

import pytest

from dci1v4.errors import ProtocolError

from dci1v5.protocol import constants as C
from dci1v5.run import execute
from dci1v5.run.execute import (fake_backend, generate_and_score,
                                prompt_cell, reuse_report)
from dci1v5.verifiers.constraints import Constraint

MODEL = "gemma-3n-e2b-it"
SLOT_MAP = {"A": Constraint("A", 4), "B": Constraint("B", 9)}
TOPIC = {"topic_id": "t-000", "area": "science",
         "question": "What makes a bridge stable?"}
OTHER_TOPIC = {"topic_id": "t-001", "area": "science",
               "question": "What makes an arch carry its load?"}
PROTOCOL = {"registration": "reg-hash-1", "freeze": None}


class _Cell:
    def __init__(self, cell_id="solo:B", arm="solo", slots=("B",), draws=2):
        self.cell_id, self.arm, self.slots = cell_id, arm, tuple(slots)
        self.draws, self.block_id = draws, "block-0000"
        self.topic_id, self.area = "t-000", "science"
        self.wording_by_slot = {s: 0 for s in slots}


def _responder(row: Any) -> str:
    return ("Short words hold here. A calm reply that stays inside the stem "
            "band and says little of note at all, plainly and briefly. " * 3)


def _run(tmp_path, *, topic=TOPIC, split="prescreen", cap=256,
         protocol=PROTOCOL, model=MODEL, calls=None) -> list[dict[str, Any]]:
    cells = [prompt_cell(_Cell(), topic, slot_map=SLOT_MAP,
                         topic_split=split)]
    backend = fake_backend(_responder)

    def counting(run_dir, plan, rows):
        if calls is not None:
            calls.append(len(rows))
        return backend(run_dir, plan, rows)

    return generate_and_score(
        model, cells, stage=C.STAGE_GATE0, cap=cap, device=0,
        run_dir=tmp_path / "run", instances=tuple(SLOT_MAP.values()),
        slot_map=SLOT_MAP, study_id="dci1v5-synthetic",
        protocol_identity=protocol, generate=counting)


def _identities(rows):
    return [r["generation_identity"] for r in rows]


# ------------------------------------------------------------ 1. reuse

def test_an_exact_rerun_reuses_and_generates_nothing(tmp_path):
    calls: list[int] = []
    first = _run(tmp_path, calls=calls)
    second = _run(tmp_path, calls=calls)
    assert calls == [2], "the second pass regenerated"
    assert all(r["resumed"] is False for r in first)
    assert all(r["resumed"] is True for r in second)
    assert _identities(first) == _identities(second)
    assert [r["raw_response"] for r in first] == \
        [r["raw_response"] for r in second]
    report = reuse_report(tmp_path / "run",
                          [prompt_cell(_Cell(), TOPIC, slot_map=SLOT_MAP,
                                       topic_split="prescreen")],
                          stage=C.STAGE_GATE0, model_key=MODEL, cap=256,
                          study_id="dci1v5-synthetic",
                          protocol_identity=PROTOCOL)
    assert report["reused"] and report["n_reused"] == 2


# ------------------------------------------- 2-7. the key has to move

@pytest.mark.parametrize("label,kwargs", [
    ("topic", {"topic": OTHER_TOPIC}),
    ("split", {"split": C.CALIBRATION_B}),
    ("decoding", {"cap": 512}),
    ("model_revision", {"model": "gemma-3n-e4b-it"}),
    ("protocol", {"protocol": {"registration": "reg-hash-2", "freeze": None}}),
])
def test_a_changed_degree_of_freedom_forbids_reuse(tmp_path, label, kwargs):
    calls: list[int] = []
    first = _run(tmp_path, calls=calls)
    second = _run(tmp_path, calls=calls, **kwargs)
    assert calls == [2, 2], f"{label} was reused across"
    assert _identities(first) != _identities(second)
    assert all(r["resumed"] is False for r in second)


def test_the_split_is_in_the_key_explicitly_and_not_by_luck(tmp_path):
    """§13.7's independence cannot rest on the prompts happening to differ.

    §6.2 makes the two calibration sets disjoint, so in practice a
    Calibration-A prompt and a Calibration-B prompt never match. This asserts
    the stronger thing: hold the topic, the prompt and the seed fixed and
    move only the split, and the identity still moves.
    """
    cell = _Cell()
    a = prompt_cell(cell, TOPIC, slot_map=SLOT_MAP,
                    topic_split=C.CALIBRATION_A)
    b = prompt_cell(cell, TOPIC, slot_map=SLOT_MAP,
                    topic_split=C.CALIBRATION_B)
    assert a.prompt_hash == b.prompt_hash
    common = dict(stage=C.STAGE_GATE0, study_id="dci1v5-synthetic",
                  protocol_identity=PROTOCOL, decoding={"temperature": 0.7})
    rows_a = execute.design_rows([a], model_id="m", **common)
    rows_b = execute.design_rows([b], model_id="m", **common)
    assert rows_a[0]["scientific_seed"] == rows_b[0]["scientific_seed"]
    assert rows_a[0]["generation_identity"] != rows_b[0]["generation_identity"]


def test_a_verifier_change_moves_the_verdict_and_not_the_generation(tmp_path):
    """The one place the two keys deliberately differ.

    A verifier change does not change what the model wrote, and every row is
    rescored from its text on every pass --- so the generation stays
    reusable and the *observation* identity moves. Collapsing the two would
    make a verifier fix cost a full regeneration for no scientific reason,
    and merging them the other way would let a stale verdict survive one.
    """
    rows = _run(tmp_path)
    generation = rows[0]["generation_identity"]
    first = rows[0]["observation_identity"]
    moved = execute.observation_identity(
        generation, verifier_hash="a-different-hash",
        instances=tuple(SLOT_MAP.values()))
    assert moved != first
    same = execute.observation_identity(
        generation, verifier_hash=rows[0]["verifier_hash"],
        instances=tuple(SLOT_MAP.values()))
    assert same == first
    # §9.1's instance set is in it too: the same text scored against a
    # different set of registered instances is a different observation.
    assert execute.observation_identity(
        generation, verifier_hash=rows[0]["verifier_hash"],
        instances=(Constraint("B", 9),)) != first


# ------------------------------------------------------- refusals

def test_a_previous_run_with_no_identity_is_regenerated(tmp_path):
    """A run written before the key existed is not assumed to match."""
    calls: list[int] = []
    _run(tmp_path, calls=calls)
    design = tmp_path / "run" / "design.jsonl"
    import json
    stripped = []
    for line in design.read_text().splitlines():
        row = json.loads(line)
        row.pop("generation_identity")
        stripped.append(json.dumps(row, sort_keys=True))
    design.write_text("\n".join(stripped) + "\n")
    _run(tmp_path, calls=calls)
    assert calls == [2, 2]


def test_an_incomplete_previous_run_is_regenerated(tmp_path):
    calls: list[int] = []
    _run(tmp_path, calls=calls)
    rows_path = tmp_path / "run" / "rows.jsonl"
    rows_path.write_text(rows_path.read_text().splitlines()[0] + "\n")
    _run(tmp_path, calls=calls)
    assert calls == [2, 2]


def test_the_decoding_projection_refuses_a_plan_that_has_drifted():
    with pytest.raises(ProtocolError, match="missing"):
        execute.decoding_identity({"temperature": 0.7})


def test_two_planned_rows_may_not_share_an_identity(monkeypatch):
    """A duplicate key would let one generation satisfy two planned rows.

    Unreachable from a valid plan --- the block, the cell and the draw are
    all in the key, so two distinct rows cannot collide --- which is exactly
    why it is asserted rather than assumed. Forcing a collision is the only
    way to find out whether the backstop is real.
    """
    first = prompt_cell(_Cell(draws=1), TOPIC, slot_map=SLOT_MAP,
                        topic_split="prescreen")
    second = prompt_cell(_Cell(cell_id="solo:A", slots=("A",), draws=1),
                         TOPIC, slot_map=SLOT_MAP, topic_split="prescreen")
    monkeypatch.setattr(execute, "generation_identity",
                        lambda *a, **k: "collided")
    with pytest.raises(ProtocolError, match="generation identity"):
        execute.design_rows([first, second], stage=C.STAGE_GATE0,
                            model_id="m", protocol_identity=PROTOCOL,
                            decoding={"temperature": 0.7})
