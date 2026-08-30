"""The pilot execution layer's invariants, without a walk (fast)."""
from __future__ import annotations

from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError, ProtocolError
from dci1v7.protocol import constants as C
from dci1v7.protocol import seeds as v7_seeds
from dci1v7.verifiers.constraints import Constraint
from dci1v8dev.run import CLASSIFICATION, STUDY_ID
from dci1v8dev.run import seeds
from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import (DCI1_ROOT, StudyContext, model_tree,
                                   pilot_context, synthetic_context)
from dci1v8dev.run.execute import (SoloCell, Block, PromptCell, design_rows,
                                   generate_and_score, prompt_cell,
                                   resolve_generate)
from dci1v8dev.run.instrument import frame_reliability
from dci1v8dev.run import wording as W
from dci1v8dev.run.regime import prescreen_counts
from dci1v8dev.run import cli, contracts

TOPIC = {"topic_id": "fixture-topic", "area": "history",
         "question": "Why did cities grow near rivers?"}


def test_the_stage_table_is_closed_and_ordered():
    assert len(S.STAGE_SEQUENCE) == 9
    assert S.STAGE_SEQUENCE[0] == S.STAGE_REGISTERED
    assert S.STAGE_SEQUENCE[-1] == S.STAGE_REPORT
    assert set(S.GENERATION_STAGES) <= set(S.STAGE_SEQUENCE)
    assert transitions.PREDECESSOR[S.STAGE_REGISTERED] is None
    assert transitions.PREDECESSOR[S.STAGE_GATE2] == S.STAGE_GATE1
    assert contracts.audit_contracts()["clean"]
    assert set(cli.RUNNERS) == set(S.STAGE_SEQUENCE)


def test_seeds_are_in_the_v8_domain_and_never_coincide_with_v7():
    v8 = seeds.generation_seed("REGIME_SCREEN", "m", "p" * 64, 0)
    v7 = v7_seeds.generation_seed("REGIME_SCREEN", "m", "p" * 64, 0)
    assert v8 != v7
    assert seeds.DOMAIN_GENERATION.startswith("dci1v8:")
    assert not set(seeds.V8_DOMAINS) & set(v7_seeds.V4R3_DOMAINS)
    with pytest.raises(ProtocolError):
        seeds.generation_seed("", "m", "p", 0)


def test_a_root_inside_a_v7_tree_is_refused(tmp_path):
    # by name, wherever the checkout lives (the evidence tree is gitignored
    # and absent from a worktree, so the rule cannot depend on it existing)
    for name in ("dci1v7", "dci1v7-development-r4", "dci1v7-development-r5",
                 "dci1v6", "dci1-v4", "br-pilot-v4"):
        for tree in ("evidence", "durable_root"):
            with pytest.raises(ProtocolError, match="study container"):
                pilot_context(tmp_path / "dci1" / tree / name / "v8")
    # and by overlap with this checkout's own trees, when they exist
    for name in ("dci1v7", "dci1v7-development-r4"):
        root = DCI1_ROOT / "evidence" / name
        if root.exists():
            with pytest.raises(ProtocolError):
                pilot_context(root / "inside")
    # the convention is accepted
    ok = pilot_context(tmp_path / "dci1" / "evidence" / "dci1v8-pilot")
    assert ok.study_root.name == "dci1v8"
    ok = pilot_context(tmp_path / "pilot")
    assert ok.study_id == STUDY_ID
    assert ok.study_root.name == "dci1v8"
    syn = synthetic_context(tmp_path / "syn")
    assert syn.study_id == f"{STUDY_ID}-synthetic"
    with pytest.raises(ProtocolError):
        StudyContext(namespace="pilot", study_id="dci1v7",
                     repo_root=tmp_path, evidence_root=tmp_path / "e",
                     durable_root=tmp_path / "d")


def test_the_registered_pilot_root_name_is_isolated_from_r4_and_r5():
    root = DCI1_ROOT / "evidence" / "dci1v8-pilot"
    context = pilot_context(root)
    assert context.study_root == root / "evidence" / "dci1v8"
    for other in ("dci1v7-development-r4", "dci1v7-development-r5", "dci1v7"):
        assert not context.study_root.resolve().is_relative_to(
            (DCI1_ROOT / "evidence" / other).resolve())


def test_prompt_cell_renders_the_v8_frames_and_refuses_a_composed_cell():
    block = Block("b-000", 1, TOPIC["topic_id"])
    cell = SoloCell(cell_id="solo:MK1:3", arm="solo", block=block, slot="S0",
                    draws=1)
    pc = prompt_cell(cell, TOPIC, slot_map={"S0": Constraint("MK1", 3)},
                     topic_split="prescreen")
    assert "the word thus" in pc.prompt or "the word " in pc.prompt
    assert pc.wording_indices == (1,)          # block 1 -> frame 1
    assert "must contain the word" in pc.prompt  # v8-w1's repaired phrase

    class Two:
        cell_id, arm, block_id, block_index, topic_id = "c", "composed", "b", 0, "t"
        slots = ("A", "B")
        wording_by_slot = {"A": 0, "B": 0}
        draws = 1

    with pytest.raises(ProtocolError, match="composed"):
        prompt_cell(Two(), TOPIC, slot_map={"A": Constraint("A", 4),
                                            "B": Constraint("B", 10)},
                    topic_split="prescreen")


def test_design_rows_carry_v8_seeds_and_the_wording_hash():
    block = Block("b-000", 0, TOPIC["topic_id"])
    cell = SoloCell(cell_id="solo:A:4", arm="solo", block=block, slot="A",
                    draws=2)
    pc = prompt_cell(cell, TOPIC, slot_map={"A": Constraint("A", 4)},
                     topic_split="prescreen")
    rows = design_rows([pc], stage=S.STAGE_REGIME, model_id="m",
                       study_id=STUDY_ID)
    assert len(rows) == 2 and rows[0]["scientific_seed"] != rows[1]["scientific_seed"]
    assert rows[0]["scientific_seed"] == seeds.generation_seed(
        S.STAGE_REGIME, "m", pc.prompt_hash, 0)
    assert rows[0]["generation_identity"] != rows[1]["generation_identity"]


def test_a_generation_callable_is_refused_outside_the_synthetic_namespace(tmp_path):
    pilot = model_tree(pilot_context(tmp_path / "p"), "qwen3-4b")
    with pytest.raises(ProtocolError, match="synthetic"):
        resolve_generate(pilot, lambda *a: None, lambda r: "x", where="t")
    assert resolve_generate(pilot, None, lambda r: "x", where="t") is None
    syn = model_tree(synthetic_context(tmp_path / "s"), "qwen3-4b")
    assert resolve_generate(syn, None, lambda r: "x", where="t") is not None


def test_frame_reliability_counts_marker_absent_rows_per_frame():
    def row(kind, q, frame, stat):
        return {"load": 1, "wording_indices": [frame],
                "scores": [{"kind": kind, "severity": q, "present": True,
                            "statistic": stat}]}
    rows = [row("MK1", 2, 0, 2), row("MK1", 2, 0, 0), row("A", 3, 1, 3),
            row("RF1", 5, 2, 0), row("MK2", 1, 3, 0)]
    rel = frame_reliability(rows)
    assert rel["by_frame"]["0"]["n_rows"] == 2
    assert rel["by_frame"]["0"]["share"] == 0.5
    assert rel["by_frame"]["1"]["share"] == 0.0
    assert rel["by_frame"]["2"]["n_rows"] == 0        # RF1 is not a marker family
    assert rel["by_frame"]["3"]["share"] == 1.0
    # descriptive only: no threshold, no verdict, no v7 reference
    assert "passed" not in rel and "limit" not in rel


def _row(kind, q, frame, topic, passed, *, stat=None, arm="solo",
         split="prescreen", present=True):
    return {"load": 1 if present else 0, "wording_indices": [frame] if present else [],
            "arm": arm, "topic_id": topic, "topic_split": split,
            "scores": [{"kind": kind, "severity": q, "present": present,
                        "passed": passed, "vacuous_pass": False,
                        "statistic": stat if stat is not None else (q if passed else 0),
                        "processing_failure": False}]}


def test_the_wording_diagnostic_keeps_every_row_and_treats_frames_separately():
    rows = []
    # frame 0: 4 topics, 3 compliant; frame 1: 4 topics, 1 compliant
    for t in range(4):
        rows.append(_row("MK1", 3, 0, f"t{t}", t < 3))
        rows.append(_row("MK1", 3, 1, f"u{t}", t < 1))
        rows.append(_row("MK1", 3, 0, f"t{t}", False, present=False,
                         arm="unconstrained"))
        rows.append(_row("MK1", 3, 1, f"u{t}", False, present=False,
                         arm="unconstrained"))
    table = W.frame_table(rows)
    by = {(e["frame"], e["candidate"]): e for e in table}
    assert by[(0, "MK1:3")]["n_rows"] == 4 and by[(0, "MK1:3")]["k_exact_compliant"] == 3
    assert by[(1, "MK1:3")]["n_rows"] == 4 and by[(1, "MK1:3")]["k_exact_compliant"] == 1
    assert by[(0, "MK1:3")]["exact_compliance"] == 0.75
    assert by[(0, "MK1:3")]["chance"] == 0.0 and by[(0, "MK1:3")]["iota"] == 0.75
    assert by[(0, "MK1:3")]["se_iota"] is not None
    assert by[(0, "MK1:3")]["observed_count_zero_share"] == 0.25   # the non-compliant rows are counted
    comparison = W.frame_comparison(table)
    c = comparison["MK1:3"]
    assert set(c["frames"]) == {"0", "1"} and c["spread"] == 0.5
    assert c["class"] in W.CLASSES and c["reference_bound"] == 0.20
    dep = W.wording_dependence(comparison)
    assert dep["n_rungs_compared"] == 1
    assert sum(len(v) for v in dep["rungs_by_class"].values()) == 1


def test_frame_comparison_classes_follow_the_registered_bound_descriptively():
    def entry(frame, iota, se):
        return {"frame": frame, "kind": "MK1", "severity": 2, "candidate": "MK1:2",
                "family": "MK1", "iota": iota, "se_iota": se, "n_rows": 24,
                "n_topics": 24, "exact_compliance": iota}
    consistent = W.frame_comparison([entry(0, 0.70, 0.02), entry(1, 0.75, 0.02)])
    unresolved = W.frame_comparison([entry(0, 0.40, 0.20), entry(1, 0.70, 0.20)])
    sensitive = W.frame_comparison([entry(0, 0.40, 0.02), entry(1, 0.70, 0.02)])
    assert consistent["MK1:2"]["class"] == "CONSISTENT"
    assert unresolved["MK1:2"]["class"] == "UNRESOLVED"
    assert sensitive["MK1:2"]["class"] == "WORDING_SENSITIVE"
    assert W.sensitive_rungs(sensitive)["WORDING_SENSITIVE"] == ["MK1:2"]


def test_the_v7_frame_threshold_is_gone():
    from dci1v8dev.run import manifest as M, instrument, report
    assert not hasattr(S, "FRAME_RELIABILITY_MARGIN")
    assert not hasattr(S, "FRAME_REFERENCE_SOURCE")
    assert not hasattr(M, "frame_reference")
    assert not hasattr(instrument, "frame_criterion")
    assert "FRAME_RELIABILITY" not in S.PILOT_CRITERIA
    assert "WORDING_DIAGNOSTIC" in S.PILOT_CRITERIA
    assert "WORDING_DIAGNOSTIC" not in S.DECIDED_CRITERIA
    assert S.WORDING_POLICY_STATUS == "OPEN"
    import inspect
    src = inspect.getsource(report) + inspect.getsource(instrument) + inspect.getsource(M)
    assert "best_v7" not in src and "frame_reference" not in src


def test_second_pass_topics_are_fresh_calibration_a_and_disjoint():
    from dci1v7.topics.bank import load_bank
    from dci1v8dev.run.rescreen import assert_batch_isolated, batch_topics
    bank = load_bank()
    prescreen = {t["topic_id"] for t in bank.topics("prescreen")}
    cal_b = {t["topic_id"] for t in bank.topics(C.CALIBRATION_B)}
    seen: list[str] = []
    for index in range(3):
        topics = batch_topics(bank, index)
        ids = {t["topic_id"] for t in topics}
        assert len(ids) == 24 and not ids & prescreen and not ids & cal_b
        assert not ids & set(seen)
        assert_batch_isolated(bank, topics, seen=seen, index=index)
        seen.extend(ids)
    # an overlap of any kind is refused
    with pytest.raises(ProtocolError, match="pre-screen"):
        assert_batch_isolated(bank, list(bank.topics("prescreen"))[:24], index=0)
    with pytest.raises(ProtocolError, match="Calibration-B"):
        assert_batch_isolated(bank, list(bank.topics(C.CALIBRATION_B))[:24], index=0)
    with pytest.raises(ProtocolError, match="earlier batch"):
        assert_batch_isolated(bank, batch_topics(bank, 0),
                              seen=[t["topic_id"] for t in batch_topics(bank, 0)],
                              index=1)


def test_composed_cells_are_refused_at_every_seam(tmp_path):
    from dci1v8dev.run.execute import assert_no_composed_cell

    class Two:
        cell_id, arm, block_id, block_index, topic_id = "c", "composed", "b", 0, "t"
        slots = ("A", "B")
        wording_by_slot = {"A": 0, "B": 0}
        draws = 1

    with pytest.raises(ProtocolError, match="composed"):
        assert_no_composed_cell([Two()], where="test")
    composed = PromptCell(cell_id="c", arm="composed", block_id="b",
                          topic_id="t", area="a", topic_split="prescreen",
                          prompt="p", prompt_hash="h" * 64, slots=("A", "B"),
                          present=(Constraint("A", 4), Constraint("B", 10)),
                          wording_indices=(0, 0), draws=1)
    with pytest.raises(ProtocolError, match="composed"):
        design_rows([composed], stage=S.STAGE_REGIME, model_id="m",
                    study_id=STUDY_ID)
    tree = model_tree(synthetic_context(tmp_path / "s"), "qwen3-4b")
    with pytest.raises(ProtocolError, match="composed"):
        generate_and_score("qwen3-4b", [composed], stage=S.STAGE_REGIME, cap=512,
                           device=0, run_dir=tmp_path / "run",
                           study_id=tree.context.study_id,
                           generate=lambda *a: {"rows": []})
    # and no stage of the layer builds one: no composed constructor is imported
    import inspect
    from dci1v8dev import run as run_pkg
    import pkgutil, importlib
    for info in pkgutil.iter_modules(run_pkg.__path__):
        src = inspect.getsource(importlib.import_module(f"dci1v8dev.run.{info.name}"))
        for forbidden in ("design_cells", "cell_types", "cells_for",
                          "composed_probe", "composed_contrast", "Delta_R",
                          "delta_diff", "B+R", "R+B"):
            if forbidden in ("Delta_R", "delta_diff", "B+R", "R+B"):
                # named in prose only; never as a field read
                assert f'["{forbidden}"]' not in src and f"['{forbidden}']" not in src
            else:
                assert forbidden not in src, (info.name, forbidden)


def test_row_accounting_counts_compliant_and_non_compliant_rows(tmp_path):
    import json
    from dci1v8dev.run.execute import row_accounting
    run = tmp_path / "run"; run.mkdir()
    design = [{"row_id": f"b:c:{i}"} for i in range(4)]
    (run / "design.jsonl").write_text("".join(json.dumps(r) + "\n" for r in design))
    (run / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in design))
    scored = [{"row_id": f"b:c:{i}", "scores": [{"present": True, "passed": i % 2 == 0}]}
              for i in range(4)]
    (run / "scored.jsonl").write_text("".join(json.dumps(r) + "\n" for r in scored))
    acc = row_accounting(run)
    assert acc["every_row_scored"] and acc["n_scored"] == 4
    assert acc["n_present_exact_compliant"] == 2 and acc["n_present_non_compliant"] == 2
    (run / "scored.jsonl").write_text(json.dumps(scored[0]) + "\n")
    assert not row_accounting(run)["every_row_scored"]


def test_prescreen_counts_read_chance_on_the_unconstrained_cell():
    rungs = [Constraint("CL7", 10)]
    rows = []
    for t in range(3):
        rows.append({"topic_id": f"t{t}", "arm": "solo",
                     "scores": [{"kind": "CL7", "severity": 10, "present": True,
                                 "passed": t < 2, "vacuous_pass": False}]})
        rows.append({"topic_id": f"t{t}", "arm": "unconstrained",
                     "scores": [{"kind": "CL7", "severity": 10, "present": False,
                                 "passed": t == 0, "vacuous_pass": False}]})
        # a row of another arm where CL7 is absent: NOT chance basis
        rows.append({"topic_id": f"t{t}", "arm": "solo",
                     "scores": [{"kind": "CL7", "severity": 10, "present": False,
                                 "passed": True, "vacuous_pass": False}]})
    counts = prescreen_counts(rows, rungs)
    assert counts[0]["solo_k"] == 2 and counts[0]["solo_n"] == 3
    assert counts[0]["chance_k"] == 1.0 and counts[0]["chance_n"] == 3.0


def test_records_are_write_once_and_ordered(tmp_path):
    from dci1v4.engine.signing import create_signing_key
    tree = model_tree(synthetic_context(tmp_path / "s"), "qwen3-4b")
    create_signing_key(tree.context.signing_key_path)
    with pytest.raises(IntegrityError):
        transitions.assert_transition_legal(tree, S.STAGE_QUALIFIED)
    payload = {"stage": S.STAGE_REGISTERED,
               "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_REGISTERED],
               "outcome": "PASS"}
    transitions.write_stage_record(tree, S.STAGE_REGISTERED, payload)
    with pytest.raises(IntegrityError, match="write-once"):
        transitions.write_stage_record(tree, S.STAGE_REGISTERED, payload)
    transitions.assert_transition_legal(tree, S.STAGE_QUALIFIED)
    with pytest.raises(IntegrityError, match="already has a record"):
        transitions.assert_transition_legal(tree, S.STAGE_REGISTERED)
    record = transitions.read_stage_record(tree, S.STAGE_REGISTERED)
    assert record["study_id"] == tree.context.study_id
    with pytest.raises(ProtocolError):
        transitions.write_terminal_report(tree, {"status": "NOT_A_STATUS"})


def test_the_cli_refuses_a_device_on_a_non_generating_stage_and_needs_a_root(tmp_path):
    assert cli.generating_stages() == S.GENERATION_STAGES
    rc = cli.main(["run", "--stage", S.STAGE_GATE3, "--model", "qwen3-4b",
                   "--root", str(tmp_path / "r"), "--device", "0"])
    assert rc == 1
    with pytest.raises(SystemExit):
        cli.main(["status", "--model", "qwen3-4b"])
    rc = cli.main(["status", "--model", "qwen3-4b", "--root",
                   str(tmp_path / "r"), "--namespace", "synthetic"])
    assert rc == 0


def test_classification_and_terminal_vocabulary():
    assert "v8" in CLASSIFICATION and "not registered" in CLASSIFICATION
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in S.TERMINAL_STATUSES
    assert "PREFREEZE_AUDIT_FAILURE" not in S.TERMINAL_STATUSES
    assert S.NO_COMPOSED_CELLS is True
    assert S.RESCREEN_TOPIC_SOURCE == C.CALIBRATION_A
