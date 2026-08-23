"""The pre-data engineering amendment: three defects, and what stops them.

All three were found in the Phase-0 sweep of the registered study, **before**
any model response existed, and all three were invisible to the suite for the
same reason: the integration harness walks one model and always injects its
own generator, so neither the second replication's registration nor the
production generation path had ever been executed.

* **V5-E1** --- ``registration_payload`` signed the study-level manifest on
  every call, so ``write_json_once`` refused the second replication and three
  of the four registered models could never obtain the stage-1 record that
  ``assert_predecessor_passed`` requires.
* **V5-E2** --- four runners wrote ``generate = generate or fake_backend(...)``,
  which is unconditional and admits no override, so ``run_backend`` was
  unreachable from ``GATE_0_APPARATUS``, ``REGIME_SCREEN``,
  ``GATE_2_FOCAL_CALIBRATION`` and ``GATE_4_COMPOSED_HEADROOM``. The CLI passes
  no ``generate``, so the documented entry point would have signed fabricated
  text into the registered evidence tree.
* **V5-E3** --- ``CLASSIFICATION`` still said ``NOT ADOPTED`` after adoption,
  and ``run/execute.py`` stamps it onto every row.

None of these changed a threshold, an estimand, an arm, a prompt, a verifier,
a seed or a selection rule. What they changed is whether the registered study
could be executed at all.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODELS

import dci1v5
from dci1v5.engine.context import registered_context, synthetic_context
from dci1v5.engine.paths import is_superseded, model_tree
from dci1v5.protocol import constants as C
from dci1v5.design import budget
from dci1v5.design.cells import design_cells
from dci1v5.protocol import manifest
from dci1v5.run import registration_run
from dci1v5.run.execute import (fake_backend, generate_and_score,
                                prompt_cell, resolve_generate)
from dci1v5.verifiers.constraints import Constraint

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMIT = "0" * 40
ALL_MODELS = tuple(m.model_key for m in MODELS)


def _ctx(tmp_path):
    return synthetic_context(tmp_path, repo_root=REPO_ROOT)


def _fake_stage(ctx, model_key, stage):
    """A record file where a stage's record goes. Only its existence matters
    to the supersession guard, which is what is under test."""
    path = model_tree(ctx, model_key).stage_record(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}")
    return path


def _register(ctx, model_key, *, commit=COMMIT, **kwargs):
    tree = model_tree(ctx, model_key)
    tree.root.mkdir(parents=True, exist_ok=True)
    return registration_run.run_registration(
        tree, producing_commit=commit, adoption={"status": "SYNTHETIC"},
        repo_root=REPO_ROOT, environment_digest="test", **kwargs)


# --------------------------------------------------------------- V5-E1

def test_every_registered_model_can_obtain_a_stage_one_record(tmp_path):
    """The defect exactly: model 1 passed and models 2-4 raised.

    Four models are registered, not two, because D1 is closed at
    ``four_models_56_cells`` and the failure was *ordinal* --- it appeared on
    whichever replication happened to run second.
    """
    ctx = _ctx(tmp_path)
    assert len(ALL_MODELS) == 4
    for key in ALL_MODELS:
        assert _register(ctx, key).outcome == "PASS"
    for key in ALL_MODELS:
        assert model_tree(ctx, key).stage_record(C.STAGE_REGISTERED).exists()


def test_the_second_replication_verifies_rather_than_signs_again(tmp_path):
    """One study, one manifest, four stage records binding it."""
    ctx = _ctx(tmp_path)
    _register(ctx, ALL_MODELS[0])
    first = manifest.load_manifest(ctx)["manifest_hash"]
    _register(ctx, ALL_MODELS[1])
    assert manifest.load_manifest(ctx)["manifest_hash"] == first
    for key in ALL_MODELS[:2]:
        record = json.loads(
            model_tree(ctx, key).stage_record(C.STAGE_REGISTERED).read_text())
        assert record["payload"]["manifest_hash"] == first


def test_a_replication_registering_at_another_commit_is_refused(tmp_path):
    """Every replication in a study registers under one commit."""
    ctx = _ctx(tmp_path)
    _register(ctx, ALL_MODELS[0])
    with pytest.raises(IntegrityError, match="different registration"):
        _register(ctx, ALL_MODELS[1], commit="1" * 40)


def test_a_manifest_the_code_no_longer_reproduces_is_refused(tmp_path,
                                                             monkeypatch):
    """The verification is a rebuild, not a signature check alone.

    A second replication registering against a manifest its own code no longer
    builds would bind study-wide rules that had moved since they were signed.
    """
    ctx = _ctx(tmp_path)
    _register(ctx, ALL_MODELS[0])
    monkeypatch.setattr(manifest, "PROTOCOL_VERSION", "5.1")
    with pytest.raises(IntegrityError, match="no longer reproduces"):
        _register(ctx, ALL_MODELS[1])


# --------------------------------------------------------------- V5-E2

def test_the_registered_namespace_resolves_to_the_pinned_backend(tmp_path):
    """``None`` is what routes ``generate_and_score`` to ``run_backend``."""
    tree = model_tree(registered_context(), ALL_MODELS[0])
    assert resolve_generate(tree, None, lambda row: "x",
                            where=C.STAGE_GATE2) is None


def test_a_generation_callable_is_refused_in_the_registered_namespace():
    """The seam is not substitutable in the run whose rows become evidence."""
    tree = model_tree(registered_context(), ALL_MODELS[0])
    with pytest.raises(ProtocolError, match="not substitutable"):
        resolve_generate(tree, fake_backend(lambda row: "x"),
                         lambda row: "x", where=C.STAGE_GATE2)


def test_the_synthetic_namespace_still_gets_its_stand_in(tmp_path):
    """The harness has to keep working, or the amendment costs the suite."""
    tree = model_tree(_ctx(tmp_path), ALL_MODELS[0])
    assert resolve_generate(tree, None, lambda row: "x",
                            where=C.STAGE_GATE2) is not None
    injected = fake_backend(lambda row: "x")
    assert resolve_generate(tree, injected, lambda row: "x",
                            where=C.STAGE_GATE2) is injected


def test_no_runner_falls_back_to_a_stand_in():
    """A static check, because the defect was a fallback nobody could see.

    ``x or fake_backend(...)`` reads as a default and behaves as a
    substitution: there is no argument that reaches past it. The check is on
    the parsed source rather than the text, so a runner may *describe* the
    defect in a docstring --- several now do --- and only an actual call is a
    finding. A future runner written the same way would reintroduce it in a
    namespace where the rows are evidence.
    """
    offenders = []
    for path in sorted((REPO_ROOT / "dci1" / "src" / "dci1v5"
                        / "run").glob("*.py")):
        if path.name == "execute.py":
            continue                     # where the stand-in legitimately is
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "fake_backend"):
                offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], offenders


def test_the_synthetic_flag_says_what_produced_the_text(tmp_path):
    """It read ``generate is not None`` --- the call shape, not the source.

    So a real backend injected into one of those runners produced rows stamped
    synthetic, and there was no way to produce a row stamped otherwise.
    """
    slot_map = {"A": Constraint("A", 4), "B": Constraint("B", 9)}
    topic = {"topic_id": "t-000", "area": "science",
             "question": "What makes a bridge stable?"}

    class _Cell:
        cell_id, arm, block_id = "solo:B", "solo", "block-0000"
        topic_id, area, draws = "t-000", "science", 1
        slots = ("B",)
        wording_by_slot = {"B": 0}

    cells = [prompt_cell(_Cell(), topic, slot_map=slot_map,
                         topic_split="prescreen")]
    text = ("A calm reply that stays inside the stem band and says little "
            "of note at all, plainly and briefly. " * 4)

    def kwargs(run_dir, generate):
        return dict(instances=tuple(slot_map.values()), slot_map=slot_map,
                    stage=C.STAGE_GATE0, cap=256, device=0,
                    study_id="dci1v5-synthetic", run_dir=run_dir,
                    generate=generate)

    fabricated = generate_and_score(
        ALL_MODELS[0], cells, **kwargs(tmp_path / "fake",
                                       fake_backend(lambda row: text)))
    assert all(row["synthetic"] for row in fabricated)

    def real_enough(run_dir, plan, rows):
        """A generator that is not the stand-in: no synthetic provenance."""
        out = [{"row_id": r["row_id"], "final_answer": text,
                "answer_truncated": False, "finish_reason": "stop",
                "total_generated_tokens": len(text.split())} for r in rows]
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "design.jsonl").write_text(
            "".join(json.dumps(dict(r), sort_keys=True) + "\n" for r in rows))
        (run_dir / "rows.jsonl").write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in out))
        return {"rows": out, "provenance": {"backend": "not-the-stand-in"}}

    produced = generate_and_score(
        ALL_MODELS[0], cells, **kwargs(tmp_path / "real", real_enough))
    assert not any(row["synthetic"] for row in produced)


def test_the_flag_survives_a_resumed_run(tmp_path):
    """Reuse reads the raw row, so the stand-in stamps the raw row.

    Resumption returns provenance of its own (``resumed``), so a flag derived
    only from the run's provenance would have come back false on the restart
    of a fabricated run.
    """
    slot_map = {"B": Constraint("B", 9)}
    topic = {"topic_id": "t-000", "area": "science",
             "question": "What makes a bridge stable?"}

    class _Cell:
        cell_id, arm, block_id = "solo:B", "solo", "block-0000"
        topic_id, area, draws = "t-000", "science", 1
        slots = ("B",)
        wording_by_slot = {"B": 0}

    cells = [prompt_cell(_Cell(), topic, slot_map=slot_map,
                         topic_split="prescreen")]
    text = ("A calm reply that stays inside the stem band and says little "
            "of note at all, plainly and briefly. " * 4)
    common = dict(instances=tuple(slot_map.values()), slot_map=slot_map,
                  stage=C.STAGE_GATE0, cap=256, device=0,
                  study_id="dci1v5-synthetic", run_dir=tmp_path / "run")

    first = generate_and_score(ALL_MODELS[0], cells,
                              generate=fake_backend(lambda row: text),
                              **common)
    assert all(row["synthetic"] for row in first)
    again = generate_and_score(ALL_MODELS[0], cells,
                               generate=fake_backend(lambda row: text),
                               **common)
    assert all(row["resumed"] for row in again), "the run should have resumed"
    assert all(row["synthetic"] for row in again)


# --------------------------------------------------------------- V5-E3

def test_the_classification_is_no_longer_a_draft_label():
    assert "NOT ADOPTED" not in dci1v5.CLASSIFICATION
    assert "DRAFTED" not in dci1v5.CLASSIFICATION
    assert manifest.PROTOCOL_VERSION == "5.0"


def test_the_superseded_classification_is_retained():
    """A reader meeting a record from the first registration needs the string."""
    assert dci1v5.SUPERSEDED_CLASSIFICATIONS == (
        "DCI-1 PROTOCOL v5 (DRAFTED, NOT ADOPTED, NOT FROZEN)",)
    assert dci1v5.CLASSIFICATION not in dci1v5.SUPERSEDED_CLASSIFICATIONS


# ------------------------------------------------------- the supersession

def test_supersession_retains_the_manifest_and_the_stage_records(tmp_path):
    ctx = _ctx(tmp_path)
    for key in ALL_MODELS[:2]:
        _register(ctx, key)
        _fake_stage(ctx, key, C.STAGE_QUALIFIED)
    old = manifest.load_manifest(ctx)["manifest_hash"]

    record = registration_run.supersede_registration(
        ctx, reason="test", model_keys=ALL_MODELS[:2],
        producing_commit="1" * 40)

    assert record["superseded_manifest_hash"] == old
    assert record["observations_under_it"] == 0
    kept = Path(ctx.registration_root) / "superseded" / old
    assert (kept / "registration_manifest.json").exists()
    assert (kept / "supersession.json").exists()
    assert not Path(ctx.registration_manifest).exists()
    for key in ALL_MODELS[:2]:
        tree = model_tree(ctx, key)
        held = tree.superseded_dir(old) / C.STAGE_REGISTERED
        assert (held / "records" / "registration_record.json").exists()
        assert is_superseded(held)
        assert not tree.stage_record(C.STAGE_REGISTERED).exists()
        # QUALIFIED reads no behavioural rate, so it is retained and re-run
        # rather than blocking the supersession.
        assert (tree.superseded_dir(old) / C.STAGE_QUALIFIED).exists()
        assert not tree.stage_record(C.STAGE_QUALIFIED).exists()
        outcomes = [json.loads(line)["outcome"]
                    for line in tree.transition_log.read_text().splitlines()
                    if line.strip()]
        assert "SUPERSEDED" in outcomes


def test_a_superseded_registration_names_what_it_replaced(tmp_path):
    ctx = _ctx(tmp_path)
    _register(ctx, ALL_MODELS[0])
    old = manifest.load_manifest(ctx)["manifest_hash"]
    registration_run.supersede_registration(
        ctx, reason="test", model_keys=ALL_MODELS[:1],
        producing_commit=COMMIT)
    _register(ctx, ALL_MODELS[0], supersedes=old)

    new = manifest.load_manifest(ctx)
    assert new["supersedes"] == old
    assert new["manifest_hash"] != old
    rebuilt = manifest.build_manifest(
        ctx, producing_commit=new["producing_commit"],
        adoption=new["adoption"], repo_root=REPO_ROOT,
        supersedes=new["supersedes"])
    assert rebuilt["manifest_hash"] == new["manifest_hash"], (
        "a superseded manifest has to be reproducible from its producing "
        "commit like any other, or ensure_registration cannot verify it")


def test_supersession_is_refused_once_an_observation_exists(tmp_path):
    """Retaining a registration that has evidence under it would hide a
    discarded replication behind a file move.

    The boundary is ``GATE_0_APPARATUS``: the first stage that puts a model
    response on disk. Everything at or after it refuses.
    """
    ctx = _ctx(tmp_path)
    _register(ctx, ALL_MODELS[0])
    _fake_stage(ctx, ALL_MODELS[0], C.STAGE_QUALIFIED)
    _fake_stage(ctx, ALL_MODELS[0], C.STAGE_GATE0)
    with pytest.raises(IntegrityError, match="generate or read generated"):
        registration_run.supersede_registration(
            ctx, reason="test", model_keys=ALL_MODELS[:1],
            producing_commit=COMMIT)


def test_the_supersession_boundary_is_the_first_generating_stage():
    """Stated once, so moving GATE_0 in the sequence moves the boundary."""
    first = C.STAGE_SEQUENCE.index(C.STAGE_GATE0)
    assert C.STAGE_SEQUENCE[:first] == (C.STAGE_REGISTERED, C.STAGE_QUALIFIED)
    assert C.STAGE_GATE0 in C.GENERATION_STAGES
    assert C.STAGE_QUALIFIED not in C.GENERATION_STAGES


# --------------------------------------------------------------- V5-E4

def test_the_pilot_budget_is_what_the_pilot_actually_builds():
    """The budget said 240 and §19's pilot builds 2,688.

    `budget.calibration_burden` multiplied the twelve pre-screen topics and
    four draws by a literal ``5`` --- the base arm's cell count --- where §19
    requires "the full 56-cell plan". The registered design was always right;
    the arithmetic over it was not. This asserts the two against each other
    rather than against a number, so neither can drift alone.
    """
    class _Block:
        def __init__(self, index):
            self.block_id, self.index = f"pilot-{index:02d}", index
            self.topic_id = f"t{index}"

    blocks = [_Block(i) for i in range(C.PILOT_TOPICS)]
    built = design_cells(blocks, C.ARMS, draws=C.PILOT_DRAWS)
    rows_the_runner_will_produce = len(built) * C.PILOT_DRAWS

    registered = budget.registered_budget()
    assert registered["calibration"]["pilot"]["rows"] == \
        rows_the_runner_will_produce
    assert rows_the_runner_will_produce == C.PILOT_TOPICS * C.PILOT_DRAWS * 56


def test_the_corrected_totals():
    b = budget.registered_budget()
    assert b["calibration"]["pilot"]["rows"] == 2688
    assert b["per_model"]["calibration"] == 103_440
    assert b["per_model"]["total"] == 286_224
    assert b["total_generations"] == 1_144_896


def test_the_pilot_term_follows_the_arm_set():
    """It was written as if arm-independent, which is how it went wrong.

    The pilot runs the whole cell set, so a design with fewer cells has a
    cheaper pilot --- and a budget that cannot see the arm set cannot say so.
    """
    options = budget.all_options()
    full = options["four_models_56_cells"]
    fewer = options["four_models_47_cells"]
    assert full["cells_per_block"] == 56 and fewer["cells_per_block"] == 47
    assert (full["per_model"]["calibration"]
            - fewer["per_model"]["calibration"]) == (56 - 47) * 12 * 4
