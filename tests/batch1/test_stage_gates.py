"""Stage 1 completeness before Stage 2 (audit F2) and authentication of the
design rows a generator receives (audit F5), on the reduced panel."""
from __future__ import annotations

import json
import shutil

import pytest

from dci.batch1 import cli
from dci.batch1 import design as D
from dci.batch1 import evidence as EV
from dci.batch1 import pipeline as P
from dci.batch1 import runner as RUN
from dci.batch1 import synthetic as SY
from dci.batch1.store import RunError, read_jsonl, write_jsonl
from tests.batch1.helpers import lines, make_root

pytestmark = pytest.mark.cpu

GEN = SY.synthetic_generate()


@pytest.fixture(scope="module")
def stage1(tmp_path_factory):
    """A root whose Stage 1 is completely generated and scored."""
    base = make_root(tmp_path_factory.mktemp("stage1"))
    root, f1 = base["root"], base["freeze1"]
    design = P.write_stage1_plan(root, f1)
    RUN.execute(root, design, freeze1=f1, approvals=base["approvals"],
                generate=GEN)
    P.score_stage(root, D.STAGE1)
    return {**base, "design": design}


@pytest.fixture
def copy(stage1, tmp_path):
    root = tmp_path / "root"
    shutil.copytree(stage1["root"], root)
    return {**stage1, "root": root}


def spy():
    calls = []

    def generate(run_dir, plan, rows):
        calls.append(len(rows))
        return GEN(run_dir, plan, rows)
    return generate, calls


def run_rows(ctx, rows, generate):
    return RUN.execute(ctx["root"], rows, freeze1=ctx["freeze1"],
                       approvals=ctx["approvals"], generate=generate)


# ------------------------------------------------------------- completeness

def test_a_one_third_stage1_cannot_produce_a_stage2_plan(tmp_path, stage1):
    """Audit probe F: 5,205 of 15,616 rows used to give a 150-cell plan."""
    ctx = {**stage1, **make_root(tmp_path, freeze1=stage1["freeze1"],
                                 approvals=stage1["approvals"])}
    design = P.write_stage1_plan(tmp_path, ctx["freeze1"])
    run_rows(ctx, design[: len(design) // 3], GEN)
    P.score_stage(tmp_path, D.STAGE1)
    with pytest.raises(EV.IncompleteEvidence, match="incomplete"):
        P.write_stage2_plan(tmp_path, ctx["freeze1"])
    assert not (tmp_path / "plan" / "stage2_selection.json").exists()
    assert cli.main(["select-refinement", "--root", str(tmp_path)]) == 3
    status = P.status(tmp_path, ctx["freeze1"])
    assert status["stage1"]["state"] == "INCOMPLETE"
    assert status["stage1"]["missing"] == len(design) - len(design) // 3


def test_generated_but_unscored_stage1_is_incomplete(copy):
    (copy["root"] / "scored" / "stage1.jsonl").unlink()
    with pytest.raises(EV.IncompleteEvidence, match="scoring"):
        P.write_stage2_plan(copy["root"], copy["freeze1"])


def test_a_complete_stage1_gives_a_bound_stage2_plan(copy):
    rows = P.write_stage2_plan(copy["root"], copy["freeze1"])
    sel = json.loads((copy["root"] / "plan" / "stage2_selection.json").read_text())
    ev1 = EV.stage_evidence(copy["root"], copy["freeze1"], D.STAGE1)
    assert sel["stage1_evidence_hash"] == ev1.evidence_hash
    assert sel["stage1_rows"] == len(copy["design"]) == 3904
    assert len(rows) == sel["n_selected"] * 16 and rows
    assert P.write_stage2_plan(copy["root"], copy["freeze1"]) == rows


def test_an_edited_stage1_response_invalidates_the_stage2_selection(copy):
    P.write_stage2_plan(copy["root"], copy["freeze1"])
    path = copy["root"] / "generation" / "stage1" / "qwen3-4b" / "rows.jsonl"
    stored = read_jsonl(path)
    stored[3]["final_answer"] = stored[3]["final_answer"] + " Edited."
    write_jsonl(path, stored)
    stage2 = read_jsonl(copy["root"] / "plan" / "stage2_design.jsonl")
    generate, calls = spy()
    with pytest.raises(RunError, match="edited or stale"):
        run_rows(copy, stage2, generate)
    P.score_stage(copy["root"], D.STAGE1)      # re-scoring does not launder it
    with pytest.raises(RunError, match="has since changed"):
        run_rows(copy, stage2, generate)
    assert calls == []


def test_an_edited_stage1_score_is_caught(copy):
    path = copy["root"] / "scored" / "stage1.jsonl"
    scored = read_jsonl(path)
    row = next(r for r in scored if r["condition"] != D.TASK_ONLY)
    entry = row["scores"][row["condition"]]
    entry[2] = not entry[2]
    write_jsonl(path, scored)
    with pytest.raises(RunError, match="differs from the one its response"):
        P.write_stage2_plan(copy["root"], copy["freeze1"])


def test_stage2_resumes_without_moving_the_selection(copy):
    rows = P.write_stage2_plan(copy["root"], copy["freeze1"])
    selection = (copy["root"] / "plan" / "stage2_selection.json").read_bytes()
    first = run_rows(copy, rows[: len(rows) // 2], GEN)
    again = run_rows(copy, rows, GEN)
    assert first["generated"] == len(rows) // 2
    assert again["generated"] == len(rows) - len(rows) // 2
    assert (copy["root"] / "plan" / "stage2_selection.json").read_bytes() == \
        selection
    assert P.write_stage2_plan(copy["root"], copy["freeze1"]) == rows


def test_an_interrupted_stage2_cannot_be_finalised(copy):
    rows = P.write_stage2_plan(copy["root"], copy["freeze1"])
    run_rows(copy, rows[: len(rows) // 4], GEN)
    P.score_stage(copy["root"], D.STAGE2)
    with pytest.raises(EV.IncompleteEvidence, match="stage2 is incomplete"):
        P.finalize(copy["root"], copy["freeze1"])
    with pytest.raises(EV.IncompleteEvidence):
        P.freeze_membership(copy["root"], copy["freeze1"], copy["approvals"])
    assert cli.main(["finalize-calibration", "--root", str(copy["root"])]) == 3


def test_an_edited_stage2_selection_is_refused(copy):
    rows = P.write_stage2_plan(copy["root"], copy["freeze1"])
    path = copy["root"] / "plan" / "stage2_selection.json"
    sel = json.loads(path.read_text())
    sel["cells"] = sel["cells"][:-1]
    path.write_text(json.dumps(sel))
    with pytest.raises(RunError, match="edited"):
        P.write_stage2_plan(copy["root"], copy["freeze1"])
    generate, calls = spy()
    with pytest.raises(RunError, match="edited"):
        run_rows(copy, rows, generate)
    assert calls == []


# ----------------------------------------------------- design authentication

def _tampered(ctx, change):
    mine = [dict(r) for r in ctx["design"] if r["model"] == "qwen3-4b"]
    rows = [r for r in mine if r["condition"] == D.TASK_ONLY][:2] + \
        [r for r in mine if r["frame"] == "F0"][:2] + \
        [r for r in mine if r["frame"] == "F1"][:2]
    change(rows)
    return rows


def _composed(rows):
    """Audit probe C: a second instruction, with ``load`` still 0."""
    r = next(r for r in rows if r["condition"] != D.TASK_ONLY)
    r["user_prompt"] = r["user_prompt"].replace(
        "\n\nAnswer:", "\n2. Use only words of 8 letters or fewer.\n\nAnswer:")
    r["load"] = 0


def _seed(rows):
    rows[1]["scientific_seed"] += 1


def _topic(rows):
    rows[2]["user_prompt"] = rows[2]["user_prompt"].replace("?", " today?", 1)


def _topic_id(rows):
    rows[2]["topic_id"] = "b1-food-00"


def _duplicate(rows):
    rows.append(dict(rows[0]))


def _frame(rows):
    r = next(r for r in rows if r["frame"] == "F0")
    r["frame"] = "F1"


def _prompt_and_hash(rows):
    from dci.provenance.hashes import sha_text
    r = next(r for r in rows if r["condition"] != D.TASK_ONLY)
    r["user_prompt"] = r["user_prompt"].replace("\n1. ", "\n1. Ignore this. ")
    r["prompt_hash"] = sha_text(r["user_prompt"])


@pytest.mark.parametrize("change,match", [
    (_composed, "differs from the frozen design"),
    (_seed, "differs from the frozen design"),
    (_topic, "differs from the frozen design"),
    (_topic_id, "differs from the frozen design"),
    (_duplicate, "requested twice"),
    (_frame, "differs from the frozen design"),
    (_prompt_and_hash, "differs from the frozen design"),
])
def test_execution_refuses_a_row_that_is_not_the_frozen_design(stage1, tmp_path,
                                                                change, match):
    ctx = {**stage1, **make_root(tmp_path, freeze1=stage1["freeze1"],
                                 approvals=stage1["approvals"])}
    generate, calls = spy()
    with pytest.raises(EV.DesignAuthenticationError, match=match):
        run_rows(ctx, _tampered(ctx, change), generate)
    assert calls == []
    assert not (tmp_path / "generation").exists()


def test_the_prompt_bytes_are_checked_even_if_every_field_agrees(stage1, tmp_path,
                                                                 monkeypatch):
    """Defence in depth: the instruction count is read from the prompt."""
    ctx = {**stage1, **make_root(tmp_path, freeze1=stage1["freeze1"],
                                 approvals=stage1["approvals"])}
    def composed_with_hash(rows):
        from dci.provenance.hashes import sha_text
        _composed(rows)
        for r in rows:
            r["prompt_hash"] = sha_text(r["user_prompt"])
    rows = _tampered(ctx, composed_with_hash)
    real = EV.expected_design

    def forged(root, f1, stage):        # an attacker who also forged the plan
        by_id = {r["row_id"]: r for r in rows}
        return [by_id.get(r["row_id"], r) for r in real(root, f1, stage)]
    monkeypatch.setattr(EV, "expected_design", forged)
    generate, calls = spy()
    with pytest.raises(EV.DesignAuthenticationError, match="instruction lines"):
        run_rows(ctx, rows, generate)
    assert calls == []


def test_a_stale_stage2_plan_file_is_refused(copy):
    rows = P.write_stage2_plan(copy["root"], copy["freeze1"])
    path = copy["root"] / "plan" / "stage2_design.jsonl"
    stored = read_jsonl(path)
    stored[0]["scientific_seed"] += 1
    write_jsonl(path, stored)
    with pytest.raises(EV.DesignAuthenticationError, match="differs"):
        P.score_stage(copy["root"], D.STAGE2)
    generate, calls = spy()
    with pytest.raises(EV.DesignAuthenticationError):
        run_rows(copy, stored, generate)
    assert calls == []
    assert rows[0]["scientific_seed"] != stored[0]["scientific_seed"]


def test_the_cli_refuses_a_tampered_plan_file(copy):
    path = copy["root"] / "plan" / "stage1_design.jsonl"
    stored = read_jsonl(path)
    _composed(stored)
    write_jsonl(path, stored)
    assert cli.main(["execute", "--root", str(copy["root"]), "--stage",
                     "stage1", "--synthetic"]) == 3
