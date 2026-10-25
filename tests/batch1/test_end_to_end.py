"""The whole pilot on a reduced synthetic panel: plan, execute (with empty
answers and technical failures), resume, score, refine, calibrate, Freeze 2,
its validation against the evidence, and tamper detection (audit F8). The
full-size run is ``python -m dci.batch1 demo``."""
from __future__ import annotations

import json
import shutil

import pytest

from dci.batch1 import cli
from dci.batch1 import design as D
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import outcomes as OUT
from dci.batch1 import pipeline as P
from dci.batch1 import report as REP
from dci.batch1 import runner as RUN
from dci.batch1 import synthetic as SY
from dci.batch1.scoring import PilotTables
from dci.batch1.store import read_jsonl, write_jsonl
from tests.batch1.helpers import SMALL, make_root

pytestmark = pytest.mark.cpu


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    base = make_root(tmp_path_factory.mktemp("batch1"))
    root, f1, approvals = base["root"], base["freeze1"], base["approvals"]
    flaky = {"n": 0}

    def technical(row):                     # the first 9 requests fail once
        flaky["n"] += 1
        return "TECHNICAL_FAILURE" if flaky["n"] <= 9 else None
    gen = SY.synthetic_generate(empty_rate=0.01)
    d1 = P.write_stage1_plan(root, f1)
    first = RUN.execute(root, d1, freeze1=f1, approvals=approvals,
                        generate=SY.synthetic_generate(empty_rate=0.01,
                                                       technical=technical))
    resumed = RUN.execute(root, d1, freeze1=f1, approvals=approvals,
                          generate=gen)
    P.score_stage(root, D.STAGE1)
    d2 = P.write_stage2_plan(root, f1)
    RUN.execute(root, d2, freeze1=f1, approvals=approvals, generate=gen)
    P.score_stage(root, D.STAGE2)
    result = P.finalize(root, f1)
    f2 = P.freeze_membership(root, f1, approvals)
    return {**base, "f1": f1, "f2": f2, "d1": d1, "d2": d2, "first": first,
            "resumed": resumed, "result": result, "gen": gen}


@pytest.fixture
def copy(run, tmp_path):
    root = tmp_path / "root"
    shutil.copytree(run["root"], root)
    return {**run, "root": root}


def test_plan_and_generation_counts(run):
    assert len(run["d1"]) == 4 * 8 * 2 + 4 * 2 * 60 * 8
    assert run["first"]["generated"] == len(run["d1"]) - 9
    assert run["first"]["open"] == 9 and not run["first"]["complete"]
    assert run["resumed"]["generated"] == 9 and run["resumed"]["complete"]
    assert 0 < len(run["d2"]) <= 20 * 16


def test_every_accepted_row_is_scored_once_and_empties_count(run):
    for stage, design in ((D.STAGE1, run["d1"]), (D.STAGE2, run["d2"])):
        scored = read_jsonl(run["root"] / "scored" / f"{stage}.jsonl")
        assert sorted(r["row_id"] for r in scored) == \
            sorted(r["row_id"] for r in design)
        assert all(len(r["scores"]) == 60 for r in scored)
    stage1 = read_jsonl(run["root"] / "scored" / "stage1.jsonl")
    assert any(r["outcome_class"] == OUT.EMPTY for r in stage1)
    tables = PilotTables.from_state(F.read_json(run["root"] / "tables.json"))
    assert sum(c.empty for c in tables.explicit.values()) > 0
    assert all(c.n == c.planned for c in tables.explicit.values())


def test_technical_attempts_are_kept_apart_from_evidence(run):
    ev = run["f2"]["evidence"]["stage1"]
    assert ev["technical_attempts"]["attempts"] == 9
    assert ev["technical_attempts"]["open_rows"] == 0
    assert set(ev["outcome_classes"]) <= {OUT.VALID, OUT.EMPTY}
    assert sum(ev["outcome_classes"].values()) == len(run["d1"])


def test_no_composed_prompt_exists_anywhere_in_the_record(run):
    assert run["f2"]["pilot_record"]["composed_rows"] == 0
    assert run["f2"]["pilot_record"]["max_instruction_lines"] == 1
    for stage in (D.STAGE1, D.STAGE2):
        design = read_jsonl(run["root"] / "plan" / f"{stage}_design.jsonl")
        assert max(D.instruction_lines(r["user_prompt"]) for r in design) <= 1


def test_resume_regenerates_only_missing_rows(copy):
    path = copy["root"] / "generation" / D.STAGE1 / "qwen3-4b" / "rows.jsonl"
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:-7]) + "\n")
    summary = RUN.execute(copy["root"], copy["d1"], freeze1=copy["f1"],
                          approvals=copy["approvals"], generate=copy["gen"])
    assert summary["generated"] == 7
    again = RUN.execute(copy["root"], copy["d1"], freeze1=copy["f1"],
                        approvals=copy["approvals"], generate=copy["gen"])
    assert again["generated"] == 0


def test_a_row_from_another_protocol_is_refused(run, tmp_path):
    root = tmp_path / "copy"
    make_root(root, freeze1=run["f1"], approvals=run["approvals"])
    RUN.init_root(root, synthetic=True, freeze1_hash=run["f1"]["manifest_hash"])
    src = run["root"] / "generation" / D.STAGE1 / "qwen3-4b" / "rows.jsonl"
    dst = root / "generation" / D.STAGE1 / "qwen3-4b" / "rows.jsonl"
    dst.parent.mkdir(parents=True)
    rows = read_jsonl(src)
    rows[0]["identity_hash"] = "0" * 64
    write_jsonl(dst, rows)
    with pytest.raises(RUN.RunError, match="different identity"):
        RUN.execute(root, run["d1"], freeze1=run["f1"],
                    approvals=run["approvals"], generate=run["gen"])


def test_calibration_and_freeze2_are_complete_and_synthetic(run):
    result, f2 = run["result"], run["f2"]
    assert result["b"]["status"] in ("SELECTED", "FAILED")
    assert f2["synthetic"] and "SYNTHETIC" in f2["note"]
    assert f2["freeze1_hash"] == run["f1"]["manifest_hash"]
    assert f2["state"] in ("FROZEN", "REVISION_REQUIRED")
    assert f2["confirmatory_interface"]["membership_shared_across_orders"]
    assert f2["stage2_selection_reads"] == \
        f2["evidence"]["stage1"]["evidence_hash"]
    stab = f2["stability"]
    assert stab["replicates"] == SMALL.stability_replicates
    assert sum(stab["selection"]["status"].values()) == stab["replicates"]
    assert "stage1_only" in stab and "sensitivity_stage1_only" in result


def test_freeze2_validates(run):
    assert P.validate_membership(run["root"], run["f1"], run["approvals"]) == []
    assert cli.main(["validate-freeze", "--root", str(run["root"])]) == 0


def _problems(ctx):
    return P.validate_membership(ctx["root"], ctx["f1"], ctx["approvals"])


def test_an_edited_response_invalidates_freeze2(copy):
    path = copy["root"] / "generation" / D.STAGE2 / "qwen3-4b" / "rows.jsonl"
    if not path.exists():
        path = next((copy["root"] / "generation" / D.STAGE2).glob("*/rows.jsonl"))
    rows = read_jsonl(path)
    rows[0]["final_answer"] += " Edited."
    write_jsonl(path, rows)
    problems = _problems(copy)
    assert problems and "cannot be rebuilt" in problems[-1]
    P.score_stage(copy["root"], D.STAGE2)        # re-scoring the edit
    problems = _problems(copy)
    assert any("generation_hash" in p or "evidence_hash" in p for p in problems)


def test_an_altered_verdict_invalidates_freeze2(copy):
    path = copy["root"] / "scored" / "stage1.jsonl"
    rows = read_jsonl(path)
    row = next(r for r in rows if r["condition"] != D.TASK_ONLY)
    row["scores"][row["condition"]][2] = not row["scores"][row["condition"]][2]
    write_jsonl(path, rows)
    problems = _problems(copy)
    assert problems and "differs from the one its response" in problems[-1]


def test_a_duplicated_row_invalidates_freeze2_without_inflating_n(copy):
    """An identical repeat collapses (n is unchanged; the runner tests show
    it), but it changes the Stage 1 evidence record, so the Stage 2 selection
    and Freeze 2 built on the old record no longer validate."""
    path = copy["root"] / "generation" / D.STAGE2
    path = next(path.glob("*/rows.jsonl"))
    path.write_text(path.read_text() + path.read_text().splitlines()[0] + "\n")
    problems = _problems(copy)
    assert any("repeats_collapsed" in p for p in problems)
    tables = P.build_tables(copy["root"], copy["f1"])
    assert all(c.n == c.planned for c in tables.explicit.values())
    stage1 = copy["root"] / "generation" / D.STAGE1 / "qwen3-4b" / "rows.jsonl"
    stage1.write_text(stage1.read_text() + stage1.read_text().splitlines()[0]
                      + "\n")
    assert "since changed" in _problems(copy)[-1]


def test_an_edited_freeze2_is_detected(copy):
    path = copy["root"] / "freeze2.json"
    f2 = json.loads(path.read_text())
    f2["selected"] = {"a": "A.however.2", "b_limits": [8, 13]}
    path.write_text(json.dumps(f2))
    assert any("manifest_hash" in p for p in _problems(copy))


def test_synthetic_evidence_cannot_be_frozen_as_pilot_evidence(run):
    bundle = P.evidence_bundle(run["root"], run["f1"], verify_scores=False)
    with pytest.raises(F.FreezeError, match="synthetic"):
        F.freeze2_manifest(run["f1"], bundle)


def test_freeze2_binds_backend_provenance(run):
    """Re-audit R4.1: every backend run is recorded by the runner and bound."""
    f2 = run["f2"]
    assert f2["namespace"] == "synthetic"
    for stage in (D.STAGE1, D.STAGE2):
        prov = f2["evidence"][stage]["provenance"]
        assert prov["namespace"] == "synthetic"
        assert prov["generator"] == RUN.SYNTHETIC_GENERATOR
        assert prov["backend_runs"] >= 1 and len(prov["hash"]) == 64


def _relabel_real(root):
    marker = root / "RUN.json"
    state = json.loads(marker.read_text())
    state["namespace"] = "real"
    marker.write_text(json.dumps(state))


def test_relabelling_a_synthetic_root_as_real_is_refused(copy):
    _relabel_real(copy["root"])
    with pytest.raises(RUN.RunError, match="seam schema"):
        EV.stage_evidence(copy["root"], copy["f1"], D.STAGE1)
    problems = _problems(copy)
    assert problems and "cannot be rebuilt" in problems[-1]


def test_forged_provenance_cannot_make_synthetic_rows_real(copy):
    """Relabel the root and rewrite every provenance event as a seam run:
    the rows still lack the seam's schema, and no environment was attested."""
    _relabel_real(copy["root"])
    for path in copy["root"].glob("generation/*/*/provenance.jsonl"):
        events = read_jsonl(path)
        for e in events:
            if e.get("event") == "backend_run":
                e["generator"] = RUN.SEAM_GENERATOR
        write_jsonl(path, events)
    with pytest.raises(RUN.RunError, match="seam schema|attested"):
        EV.stage_evidence(copy["root"], copy["f1"], D.STAGE1)


def test_an_edited_provenance_event_invalidates_freeze2(copy):
    path = next(copy["root"].glob("generation/stage2/*/provenance.jsonl"))
    events = read_jsonl(path)
    run_event = next(e for e in events if e.get("event") == "backend_run")
    run_event["provenance"]["wall_seconds"] = 12345.0
    write_jsonl(path, events)
    assert any("provenance" in p for p in _problems(copy))


def test_selection_report_has_every_required_section(run):
    tables = PilotTables.from_state(F.read_json(run["root"] / "tables.json"))
    text = REP.selection_report(run["result"], tables, SMALL)
    for heading in ("B selection", "A selection", "SYNTHETIC"):
        assert heading in text
    assert "interference" not in text.split("Coverage here")[0].lower()


def test_storage_constants_bound_the_measured_rows(run):
    root = run["root"]
    n = len(run["d1"])
    scored = (root / "scored" / "stage1.jsonl").stat().st_size / n
    design = (root / "plan" / "stage1_design.jsonl").stat().st_size / n
    assert scored <= D.BYTES_PER_SCORED_ROW
    assert design <= D.BYTES_PER_DESIGN_ROW


def test_cli_refuses_real_execution_without_authorisation(run, capsys):
    rc = cli.main(["execute", "--root", str(run["root"]), "--stage", "stage1"])
    assert rc == 3
    assert "refused" in capsys.readouterr().err


def test_cli_validation_commands(run, capsys):
    assert cli.main(["validate-library"]) == 0
    assert cli.main(["validate-verifiers"]) == 0
    assert cli.main(["check-compatibility"]) == 0
    capsys.readouterr()
    assert cli.main(["status", "--root", str(run["root"])]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["stage1"]["state"] == status["stage2"]["state"] == "COMPLETE"
    assert status["stage1"]["technical"]["attempts"] == 9


@pytest.mark.slow
def test_full_size_demo(tmp_path, capsys):
    assert cli.main(["demo", "--root", str(tmp_path / "demo"),
                     "--replicates", "20"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["synthetic"] and out["status"] == "FEASIBLE"
