"""§13.10 walked on the CPU-only synthetic seam, before it is walked on a GPU.

Gate 4 is the first stage that composes two constraints in one prompt, and it
is the first stage that spends a **reserved** topic set: the 24
composed-validation topics, which no development work may look at and which
are spent exactly once. Everything below therefore runs against a synthetic
context in a temporary tree, and the rows it makes carry ``synthetic: true``.

Four things had never executed before this file existed, because no v4r4 gate
had ever gone terminal and Gate 4 had never been run at all:

* the terminal branch. `stages/gates.py` declared its own `TerminalStatus`,
  and the stage driver catches `dci1v4.errors.TerminalStatus`. A
  `COMPOSED_HEADROOM_FAILURE` would have escaped `_run_stage` as an unhandled
  exception --- no terminal report, no logged transition, and a replication
  that had failed a gate with nothing on disk saying so;
* the band table's completeness. `gate4_payload` reports the cells it is
  given, so a table missing a cell type reports no failure for it. An empty
  table passed;
* the variant dispatch, which reads Gate 3's `design_variant` --- the field
  that was wrong for every replication until 7eb1947;
* the arithmetic: 47 x 24 x 4 for the full design and 8 x 24 x 4 for the
  reduced one.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import random
from pathlib import Path

import pytest

from dci1v4.errors import TerminalStatus as DriverCatches
from dci1v4.engine.signing import create_signing_key

from dci1v4r4.design.cells import cell_types
from dci1v4r4.engine.context import synthetic_context
from dci1v4r4.engine.paths import model_tree
from dci1v4r4.protocol import constants as C
from dci1v4r4.run import gates_run
from dci1v4r4.stages import gates
from dci1v4r4.stages.confirmatory import DESIGN_VARIANTS
from dci1v4r4.topics import split_topics

DCI1 = Path(__file__).resolve().parents[1]
SRC = DCI1 / "src" / "dci1v4r4"
MODEL = "gemma-3n-e2b-it"

FILLER = ("The kettle boils because heat moves quickly through metal and "
          "water. However, the handle stays cool. Steam rises when the "
          "temperature climbs, and a whistle sounds. Cooks watch closely, "
          "since boiling water can spill and scald. ")


def synthetic_generate(run_dir, plan, rows):
    rng = random.Random(20260822)
    out = []
    for row in rows:
        words = FILLER.split()
        take = rng.randint(40, 110)
        out.append({"row_id": row["row_id"],
                    "final_answer": " ".join((words * 4)[:take]),
                    "answer_truncated": False, "finish_reason": "stop",
                    "total_generated_tokens": take + 12})
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rows.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in out))
    return {"rows": out}


def _records(variant: str) -> tuple[dict, dict, dict]:
    """Gate 2, Gate 3 and regime records with only the fields Gate 4 reads.

    Deliberately minimal: a field Gate 4 reads and no earlier stage writes
    raises `KeyError` here rather than defaulting silently in production.
    """
    gate2 = {"n_star": 2, "m_star": 10}
    gate3 = {"design": "full" if variant == "full" else "reduced",
             "design_variant": variant,
             "class_companion": {"family": "CL7", "severity": 30},
             "slot_map": {"CL": ("CL7", 30)}}
    if variant == "full":
        gate3["slot_map"].update({
            "R1": ("RF9", 10), "R2": ("CR5", 2), "R3": ("RF11", 26),
            "R1-": ("RF9", 8), "R1+": ("RF9", 13),
            "R2-": ("CR5", 3), "R2+": ("CR5", 1),
            "R3-": ("RF11", 21), "R3+": ("RF11", 32)})
    regime = {"selected_cap": 512}
    return gate2, gate3, regime


def _tree(tmp_path):
    context = synthetic_context(tmp_path)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    create_signing_key(context.signing_key_path)
    return model_tree(context, MODEL)


def _expected_table(variant: str) -> dict[str, set[str]]:
    reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
    return {t.cell_id: set(t.slots)
            for t in cell_types(reduced=reduced, class_arm=class_arm,
                                spectrum=spectrum) if t.arm != "unconstrained"}


@pytest.fixture(scope="module")
def reduced_run(tmp_path_factory):
    """The reduced design, all the way through, with the band predicate
    replaced by a recorder so the PASS branch is reachable on filler text."""
    seen: dict = {}

    def recording_payload(table):
        seen["table"] = {k: dict(v) for k, v in table.items()}
        return {"outcome": "PASS", "stage": C.STAGE_GATE4,
                "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_GATE4],
                "band": list(C.COMPOSED_HEADROOM_BAND),
                "table": seen["table"], "computes_no_contrast": True,
                "ranks_nothing": True}

    real = gates.gate4_payload
    gates.gate4_payload = recording_payload
    try:
        tree = _tree(tmp_path_factory.mktemp("gate4-reduced"))
        gate2, gate3, regime = _records("reduced")
        out = gates_run.run_gate4(MODEL, tree, gate2_record=gate2,
                                  gate3_record=gate3, regime_record=regime,
                                  generate=synthetic_generate)
    finally:
        gates.gate4_payload = real
    return out, seen["table"], tree


# ------------------------------------------------------- the registered size

def test_the_registered_headroom_budget_is_cells_times_topics_times_m_cal():
    # §13.10 states the ceiling as 47 x 24 x 4 = 4,512 in so many words.
    assert C.N_CELLS_FULL * C.N_COMPOSED * C.M_CAL == 47 * 24 * 4 == 4512
    assert C.N_CELLS_REDUCED_WITH_CLASS * C.N_COMPOSED * C.M_CAL == 768
    assert C.N_COMPOSED == 24 and C.M_CAL == 4


def test_each_variant_builds_the_cells_its_registered_count_names():
    for variant, expected in (("full", C.N_CELLS_FULL),
                              ("no_spectrum", C.N_CELLS_NO_SPECTRUM),
                              ("reduced", C.N_CELLS_REDUCED_WITH_CLASS)):
        reduced, class_arm, spectrum = DESIGN_VARIANTS[variant]
        assert len(cell_types(reduced=reduced, class_arm=class_arm,
                              spectrum=spectrum)) == expected


def test_the_reduced_run_generates_eight_cells_on_twenty_four_topics(
        reduced_run):
    out, _, _ = reduced_run
    # `cells` counts MATERIALISED cells --- cell types times topics --- not
    # cell types. Pinned because the number is what a reader of the record
    # compares against §13.10's ceiling.
    assert out["cells"] == C.N_CELLS_REDUCED_WITH_CLASS * C.N_COMPOSED == 192
    assert out["rows"] == out["cells"] * C.M_CAL == 768
    assert out["design_variant"] == "reduced"
    assert out["topic_set"] == "composed"
    assert out["draws"] == C.M_CAL


# ------------------------------------------------------ the reserved topics

def test_gate_four_spends_the_composed_set_and_touches_no_other_topic():
    split = split_topics()
    composed = {t["topic_id"] for t in split["composed"]}
    others = {t["topic_id"] for name, rows in split.items()
              if name != "composed" for t in rows}
    gate2, gate3, _ = _records("reduced")
    slot_map = gates_run.full_slot_map(gate2, gate3)
    from dci1v4r4.run.design_run import design_cells_for
    pairs = design_cells_for(split["composed"], slot_map, variant="reduced",
                             prefix="headroom", block_prefix="headroom")
    touched = {c.topic_id for c, _, _ in pairs}
    assert touched == composed
    assert not touched & others


def test_the_topic_set_is_read_from_the_registered_split_and_not_a_slice():
    """Structural: the module names the reserved set, and no other."""
    func = _function("run_gate4")
    subscripts = {n.slice.value for n in ast.walk(func)
                  if isinstance(n, ast.Subscript)
                  and isinstance(n.slice, ast.Constant)}
    assert "composed" in subscripts
    assert not {"confirmatory", "sequestered", "prescreen", "solo"} \
        & subscripts


# -------------------------------------------------------- what Gate 4 reads

def _function(name: str) -> ast.FunctionDef:
    source = ast.parse((SRC / "run" / "gates_run.py").read_text())
    return next(n for n in ast.walk(source)
                if isinstance(n, ast.FunctionDef) and n.name == name)


def test_gate_four_selects_nothing_and_re_reads_no_selection_rule():
    """§13.10: it runs after the spectrum and the companion are fixed."""
    func = _function("run_gate4")
    called = {n.func.id for n in ast.walk(func)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    called |= {n.func.attr for n in ast.walk(func)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for forbidden in ("select_all", "design_variant_for",
                      "admit_core_references", "select_spectrum",
                      "admit_class_companion", "select_severity",
                      "select_focal_severity"):
        assert forbidden not in called


def test_the_variant_comes_from_gate_three_and_not_from_the_design_field():
    """The two agree today. Gate 4 must still read the one §8.6 is stated
    over, because they disagreed in every record written before 7eb1947."""
    gate2, gate3, regime = _records("reduced")
    gate3 = {**gate3, "design": "full"}          # the shape of the defect
    from dci1v4r4.run.design_run import design_cells_for
    slot_map = gates_run.full_slot_map(gate2, gate3)
    pairs = design_cells_for(split_topics()["composed"][:1], slot_map,
                             variant=gate3["design_variant"],
                             prefix="h", block_prefix="h")
    assert len(pairs) == 8
    func = _function("run_gate4")
    read = {n.slice.value for n in ast.walk(func)
            if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)}
    assert "design_variant" in read
    assert "cells_per_block" not in read


# ------------------------------------------------------------- the band table

def test_the_band_table_covers_every_constrained_cell_and_every_slot(
        reduced_run):
    _, table, _ = reduced_run
    expected = _expected_table("reduced")
    assert {cell: set(by_slot) for cell, by_slot in table.items()} == expected


def test_the_unconstrained_cell_contributes_no_band_entry(reduced_run):
    _, table, _ = reduced_run
    assert "unconstrained" not in table
    assert len(table) == C.N_CELLS_REDUCED_WITH_CLASS - 1 == 7


def test_the_chance_vector_is_attached_only_to_the_load_zero_rows(
        reduced_run):
    _, _, tree = reduced_run
    run_dir = tree.backend_runs(C.STAGE_GATE4) / "headroom"
    rows = [json.loads(line) for line in
            (run_dir / "scored.jsonl").open() if line.strip()]
    assert rows, "the stage wrote no scored rows"
    for row in rows:
        absent = [s for s in row["scores"] if not s["present"]]
        if row["load"] == 0:
            assert absent, "§25's chance verdicts are missing from a load-0 row"
        else:
            assert not absent


def test_a_partial_band_table_is_refused_rather_than_reported_as_a_pass():
    """The fail-open this file was written for.

    `gate4_payload` reports the failures among the rates it is handed, so a
    table that lost a cell type reports no failure for it and an empty table
    passes the gate outright. The predicate cannot see the absence. §13.10
    says *every* registered cell type is evaluated, so the runner checks the
    shape against the design the cells were built from, before the predicate
    runs.
    """
    from dci1v4.errors import IntegrityError

    complete = {cell: {slot: 0.5 for slot in slots}
                for cell, slots in _expected_table("reduced").items()}
    gates_run.assert_headroom_table_complete(complete, "reduced")   # no raise

    with pytest.raises(IntegrityError) as empty:
        gates_run.assert_headroom_table_complete({}, "reduced")
    assert "pair:A+B" in str(empty.value)

    missing_cell = {k: v for k, v in complete.items() if k != "pair:B+CL"}
    with pytest.raises(IntegrityError) as one:
        gates_run.assert_headroom_table_complete(missing_cell, "reduced")
    assert "pair:B+CL" in str(one.value)

    missing_slot = {**complete, "pair:A+B": {"A": 0.5}}
    with pytest.raises(IntegrityError) as slot:
        gates_run.assert_headroom_table_complete(missing_slot, "reduced")
    assert "wrong slots" in str(slot.value)

    # A full-design table is not a reduced-design table, and the check is
    # stated over the variant rather than over "at least this many cells".
    with pytest.raises(IntegrityError):
        gates_run.assert_headroom_table_complete(complete, "full")


def test_the_completeness_check_runs_before_the_band_predicate():
    """Structural, because the order is the whole point: a table checked
    afterwards is a table checked after the gate has already passed."""
    func = _function("run_gate4")
    first: dict[str, int] = {}
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            continue
        first.setdefault(name, node.lineno)
        first[name] = min(first[name], node.lineno)
    assert first["assert_headroom_table_complete"] < first["gate4_payload"]


# ---------------------------------------------------------- the terminal path

def test_a_gate_terminal_is_the_exception_the_stage_driver_catches():
    """`_run_stage` catches `dci1v4.errors.TerminalStatus`. `stages/gates.py`
    declared an unrelated class of the same name, so a Gate 2, 3 or 4 terminal
    escaped the handler entirely."""
    assert issubclass(gates.TerminalStatus, DriverCatches)
    raised = gates.TerminalStatus("COMPOSED_HEADROOM_FAILURE", {"band": []})
    assert raised.status == "COMPOSED_HEADROOM_FAILURE"
    assert raised.record["status"] == "COMPOSED_HEADROOM_FAILURE"
    assert raised.detail is raised.record
    assert C.TERMINAL_SENTENCE in raised.record["terminal_sentence"]


def test_the_stage_driver_writes_a_terminal_report_for_a_gate_terminal(
        tmp_path, monkeypatch):
    """End to end through the driver, which is where the class mismatch bit."""
    spec = importlib.util.spec_from_file_location(
        "run_v4r4_under_test", DCI1 / "tools" / "run_v4r4.py")
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)

    tree = _tree(tmp_path)
    monkeypatch.setattr(driver, "registered_context",
                        lambda: tree.context)
    monkeypatch.setattr(driver.registration, "load_manifest", lambda ctx: {})
    monkeypatch.setattr(
        driver, "_commit", lambda: "0" * 40)

    class Args:
        model = MODEL

    def build(_tree, _context):
        raise gates.TerminalStatus("COMPOSED_HEADROOM_FAILURE", {
            "band": list(C.COMPOSED_HEADROOM_BAND),
            "failures": [{"cell": "pair:A+B", "slot": "A", "rate": 1.0}],
            "table": {"pair:A+B": {"A": 1.0}}})

    # The transition machine needs a passed predecessor; the point of the test
    # is the terminal branch, so the predecessor check is stubbed and the
    # branch under test is not.
    monkeypatch.setattr(driver, "_stage_payload", lambda t, s: {})
    from dci1v4r4.engine import transitions
    monkeypatch.setattr(transitions, "assert_transition_legal",
                        lambda t, s: None)

    code = driver._run_stage(Args(), C.STAGE_GATE4, build)
    assert code == 1
    report = json.loads(tree.terminal_report.read_text())
    payload = report.get("payload", report)
    assert payload["status"] == "COMPOSED_HEADROOM_FAILURE"
    assert payload["criterion"] == "COMPOSED_HEADROOM_FAILURE"
    assert payload["gate"] == C.STAGE_GATE4
    assert payload["observed"]["failures"][0]["cell"] == "pair:A+B"
    assert payload["terminal_sentence"] == C.TERMINAL_SENTENCE
    logged = [json.loads(line) for line in
              tree.transition_log.open() if line.strip()]
    assert logged[-1]["outcome"] == "TERMINAL"
    assert logged[-1]["detail"]["status"] == "COMPOSED_HEADROOM_FAILURE"


def test_every_registered_terminal_status_survives_the_round_trip():
    for status in C.TERMINAL_STATUSES:
        raised = gates.TerminalStatus(status, {})
        assert isinstance(raised, DriverCatches)
        assert raised.status == status
