"""§10.3's audit workflow: sampling, blindness, and the rules around a batch.

Six properties are asserted here because six properties are the whole value of
the workflow. If the sample can move after a disagreement, if the annotator can
see a verdict, if a batch's membership can change under it, if an interrupted
session loses a row, if resume shows an item twice, or if a sealed batch can be
edited, then the labels are not evidence about anything.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from dci1v4.analysis.intervals import wilson_upper_bound
from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C
from dci1v4r4.stages.human_audit import (
    BATCH_SIZE, EVAL_STRATA, KEY_ONLY_FIELDS, PACKET_FIELDS,
    agreement_report, allocate, assert_plan_blinded, build_plan,
    effective_labels, eval_stratum, plan_hash, reachability, realised_margin,
)

TOOL = Path(__file__).resolve().parents[1] / "tools" / "v4r3_human_audit.py"


# ------------------------------------------------------------ a fake pool

def _item(index: int, *, kind: str, severity: int, passed: bool,
          margin: int | None) -> dict:
    return {
        "row_id": f"row-{index:04d}", "position": 1,
        "model_key": "model-x", "model_id": "org/model-x", "arm": "solo",
        "stage": "screen", "topic_id": f"topic-{index % 7}",
        "instrument": f"{kind}:{severity}", "kind": kind,
        "severity": severity, "form": "count_budget", "statistic_id": "comma",
        "wording_index": 0,
        "constraint": f"At most {severity} commas may appear.",
        "response": f"response number {index} with some words in it",
        "word_count": 9,
        "verdict": "SATISFIES" if passed else "VIOLATES",
        "verifier_class": "pass" if passed else "fail",
        "margin": margin, "margin_one": margin == 1,
        "stratum": eval_stratum(passed, margin),
    }


def _pool(per_stratum: int = 60, instruments: int = 6) -> list[dict]:
    pool, index = [], 0
    for slot in range(per_stratum):
        for kind, severity in [("RF5", 1 + i) for i in range(instruments)]:
            for passed, margin in ((True, 2), (False, 1), (False, 4)):
                pool.append(_item(index, kind=kind, severity=severity,
                                  passed=passed, margin=margin))
                index += 1
        if len(pool) > per_stratum * instruments * 3:
            break
    return pool


@pytest.fixture
def plan_and_key():
    return build_plan(_pool(), annotator="Tester")


# --------------------------------------------------------------- sampling

def test_the_sample_is_deterministic_given_the_pool():
    first, first_key = build_plan(_pool(), annotator="Tester")
    second, second_key = build_plan(_pool(), annotator="Tester")
    assert first["plan_hash"] == second["plan_hash"]
    assert [r["item_id"] for r in first["packet"]] == \
           [r["item_id"] for r in second["packet"]]
    assert first_key["key"] == second_key["key"]


def test_the_presentation_order_depends_on_the_annotator_and_nothing_else():
    a, _ = build_plan(_pool(), annotator="Tester")
    b, _ = build_plan(_pool(), annotator="Someone-Else")
    assert {r["response_sha256"] for r in a["packet"]} == \
           {r["response_sha256"] for r in b["packet"]}
    assert [r["response_sha256"] for r in a["packet"]] != \
           [r["response_sha256"] for r in b["packet"]]


def test_a_reordered_pool_draws_the_same_sample():
    """Sampling must not depend on the order rows happen to be read in."""
    pool = _pool()
    forward, _ = build_plan(pool, annotator="Tester")
    backward, _ = build_plan(list(reversed(pool)), annotator="Tester")
    assert forward["plan_hash"] == backward["plan_hash"]


def test_the_quota_is_min_150_per_class_split_across_the_margin_strata():
    allocation = allocate(_pool())
    assert allocation["quota"]["pass"] == C.HUMAN_SAMPLE_CAP
    fail = (allocation["quota"]["fail:margin_one"]
            + allocation["quota"]["fail:margin_larger"])
    assert fail == C.HUMAN_SAMPLE_CAP          # the class total, not 2x it
    assert allocation["quota"]["fail:margin_one"] > 0
    assert allocation["quota"]["fail:margin_larger"] > 0


def test_a_small_class_is_taken_whole_rather_than_padded():
    pool = [i for i in _pool() if i["stratum"] != "fail:margin_one"]
    pool += [_item(9000 + n, kind="RF5", severity=1, passed=False, margin=1)
             for n in range(4)]
    allocation = allocate(pool)
    assert allocation["quota"]["fail:margin_one"] == 4
    assert len(allocation["drawn"]["fail:margin_one"]) == 4


def test_the_round_robin_spreads_the_quota_across_instruments():
    """Every instrument contributes before any contributes twice."""
    allocation = allocate(_pool(per_stratum=40, instruments=5))
    drawn = allocation["drawn"]["pass"]
    counts: dict[str, int] = {}
    for item in drawn:
        counts[item["instrument"]] = counts.get(item["instrument"], 0) + 1
    assert len(counts) == 5
    assert max(counts.values()) - min(counts.values()) <= 1


def test_the_margin_generalises_the_exact_count_definition():
    # A count budget: "at most 1 comma", a response with three commas.
    assert realised_margin("RF5", 1, "a, b, c, d") == 2
    # Exactly at the threshold: one change either way flips it for an exact
    # rule and only the upward direction flips a budget.
    assert realised_margin("RF5", 1, "a, b") == 1
    assert realised_margin("CX2", 1, "a; b") == 1
    # A wordless answer fails a rate at every numerator, so no change flips it.
    assert realised_margin("CR5", 1, "   ") is None
    assert eval_stratum(False, None) == "fail:margin_larger"


# -------------------------------------------------------------- blindness

def test_the_packet_carries_only_what_the_annotator_may_see(plan_and_key):
    plan, _ = plan_and_key
    assert_plan_blinded(plan["packet"])
    for row in plan["packet"]:
        assert set(row) == set(PACKET_FIELDS)


def test_a_packet_row_carrying_the_verdict_is_refused(plan_and_key):
    plan, _ = plan_and_key
    leaky = [{**plan["packet"][0], "verdict": "SATISFIES"}]
    with pytest.raises(ProtocolError):
        assert_plan_blinded(leaky)


def test_a_packet_row_carrying_the_model_is_refused(plan_and_key):
    plan, _ = plan_and_key
    leaky = [{**plan["packet"][0], "model_key": "gemma-3n-e2b-it"}]
    with pytest.raises(ProtocolError):
        assert_plan_blinded(leaky)


def test_the_item_id_does_not_name_the_family(plan_and_key):
    plan, _ = plan_and_key
    for row in plan["packet"]:
        assert "rf5" not in row["item_id"].lower()
        assert "cx" not in row["item_id"].lower().split("-")[1]


def test_the_key_holds_what_the_packet_may_not(plan_and_key):
    _, key = plan_and_key
    for row in key["key"]:
        for field in KEY_ONLY_FIELDS:
            assert field in row


def test_the_review_command_never_opens_the_key():
    """A comment saying the reviewer is blind is not evidence; this is.

    Every function reachable from `cmd_review` is walked, and none of them may
    mention the module-level KEY path or the key file by name.
    """
    tree = ast.parse(TOOL.read_text())
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)}
    seen, frontier = set(), ["cmd_review"]
    while frontier:
        name = frontier.pop()
        if name in seen or name not in functions:
            continue
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Name):
                assert node.id != "KEY", f"{name} reaches the answer key"
                if node.id in functions:
                    frontier.append(node.id)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "key.json" not in node.value, \
                    f"{name} names the answer key"
    assert "cmd_review" in seen and "_show" in seen


def test_the_progress_command_reports_no_agreement():
    source = TOOL.read_text()
    body = source.split("def cmd_status")[1].split("\ndef ")[0]
    for forbidden in ("agreement_report", "wilson", "verdict", "agrees"):
        assert forbidden not in body.replace(
            '"agreement": "withheld until every batch is sealed '
            '(§10.3 blinding)",', "")


# --------------------------------------------------- batches and integrity

def test_every_batch_is_created_in_advance_and_hashed(plan_and_key):
    plan, _ = plan_and_key
    assert plan["items"] == 300
    assert plan["batches"] == list(range(1, 13))
    assert set(plan["batch_hashes"]) == {str(b) for b in plan["batches"]}
    for batch in plan["batches"]:
        rows = [r for r in plan["packet"] if r["batch"] == batch]
        assert len(rows) == BATCH_SIZE
        assert [r["position"] for r in rows] == list(range(1, BATCH_SIZE + 1))


def test_moving_one_item_between_batches_breaks_the_plan_hash(plan_and_key):
    plan, _ = plan_and_key
    tampered = json.loads(json.dumps(plan))
    tampered["packet"][0]["batch"] = 12
    assert plan_hash(tampered) != tampered["plan_hash"]


def test_replacing_an_item_breaks_its_batch_hash(plan_and_key):
    from dci1v4.protocol.hashing import canonical_json, sha_text
    plan, _ = plan_and_key
    rows = [r for r in plan["packet"] if r["batch"] == 1]
    assert sha_text(canonical_json(rows)) == plan["batch_hashes"]["1"]
    swapped = [dict(r) for r in rows]
    swapped[0]["response"] = "a different response entirely"
    assert sha_text(canonical_json(swapped)) != plan["batch_hashes"]["1"]


def test_no_item_appears_in_two_batches(plan_and_key):
    plan, _ = plan_and_key
    ids = [r["item_id"] for r in plan["packet"]]
    assert len(ids) == len(set(ids))
    sources = [(r["row_id"], r["position"]) for r in plan_and_key[1]["key"]]
    assert len(sources) == len(set(sources))


# ------------------------------------------------- recording and resuming

def _record(item_id: str, label: str, **extra) -> dict:
    return {"item_id": item_id, "label": label, "annotator": "Tester",
            "recorded_at": "2026-08-21T00:00:00+00:00", **extra}


def test_an_edit_appends_and_the_last_row_wins(plan_and_key):
    plan, _ = plan_and_key
    item = plan["packet"][0]["item_id"]
    rows = [_record(item, "SATISFIES"), _record(item, "VIOLATES")]
    effective = effective_labels(rows)
    assert len(effective) == 1
    assert effective[item]["label"] == "VIOLATES"


def test_resume_shows_only_the_unanswered_items(plan_and_key):
    plan, _ = plan_and_key
    rows = [r for r in plan["packet"] if r["batch"] == 1]
    answered = {r["item_id"] for r in
                [_record(row["item_id"], "SATISFIES") for row in rows[:9]]}
    pending = [r for r in rows if r["item_id"] not in answered]
    assert len(pending) == BATCH_SIZE - 9
    assert not any(r["item_id"] in answered for r in pending)


def test_the_records_are_appended_one_line_at_a_time(tmp_path):
    """An interrupted session keeps every answer already given."""
    path = tmp_path / "batch-01.jsonl"
    for index in range(5):
        with path.open("a") as handle:
            handle.write(json.dumps(_record(f"hs-01-{index:02d}-x",
                                            "SATISFIES")) + "\n")
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(lines) == 5
    # A truncated final line -- the shape a kill mid-write leaves -- costs at
    # most the row being written, never an earlier one.
    path.write_text(path.read_text()[:-12])
    kept = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip() and line.rstrip().endswith("}")]
    assert len(kept) == 4


def test_a_label_for_an_item_outside_the_plan_is_refused(plan_and_key):
    _, key = plan_and_key
    with pytest.raises(ProtocolError):
        agreement_report(key["key"], [_record("hs-99-99-deadbeef", "SATISFIES")])


# ------------------------------------------------------------- the criterion

def _labels(key, *, wrong: int = 0, unsure: int = 0) -> list[dict]:
    rows = []
    for index, entry in enumerate(key):
        if index < wrong:
            label = ("VIOLATES" if entry["verdict"] == "SATISFIES"
                     else "SATISFIES")
        elif index < wrong + unsure:
            label = "UNSURE"
        else:
            label = entry["verdict"]
        rows.append(_record(entry["item_id"], label))
    return rows


def test_a_perfect_audit_meets_every_stratum(plan_and_key):
    _, key = plan_and_key
    report = agreement_report(key["key"], _labels(key["key"]))
    assert report["agreement_overall"] == 1.0
    assert report["all_strata_meet_the_criterion"]
    for stratum in EVAL_STRATA:
        assert report["by_stratum"][stratum]["meets_criterion"]


def test_the_bound_is_the_certified_one_sided_wilson(plan_and_key):
    _, key = plan_and_key
    report = agreement_report(key["key"], _labels(key["key"], wrong=6))
    for stratum in EVAL_STRATA:
        cell = report["by_stratum"][stratum]
        assert cell["wilson_upper_on_disagreement"] == pytest.approx(
            wilson_upper_bound(cell["disagreements"], cell["n"]))


def test_unsure_counts_against_the_criterion(plan_and_key):
    _, key = plan_and_key
    report = agreement_report(key["key"], _labels(key["key"], unsure=40))
    assert report["disagreements_overall"] == 40
    assert not report["all_strata_meet_the_criterion"]
    diagnostic = report["by_stratum"]["pass"]["diagnostic_excluding_unsure"]
    assert diagnostic["standing"] == "reported, never the criterion"


def test_the_report_never_claims_to_satisfy_section_10_3(plan_and_key):
    _, key = plan_and_key
    report = agreement_report(key["key"], _labels(key["key"]))
    assert report["satisfies_section_10_3"] is False
    assert report["standing"] == "author_performed_human_validation"
    assert "independent" in report["why_not"]


def test_reachability_is_known_before_any_label_exists(plan_and_key):
    _, key = plan_and_key
    reach = reachability(key["key"])
    assert set(reach) == set(EVAL_STRATA)
    for stratum, cell in reach.items():
        assert cell["reachable"] is (
            cell["bound_at_zero_disagreements"] <= C.HUMAN_DISAGREEMENT_MAX)
    thin = reachability([{"stratum": "pass"}] * 10)
    assert not thin["pass"]["reachable"]
    assert "MEASUREMENT_EVIDENCE_INSUFFICIENT" in thin["pass"]["note"]


def test_the_draw_is_the_registered_seed_and_not_an_ordering_of_the_pool():
    """Deterministic is not enough: it has to be the registered seed's draw.

    A content-ordered queue would also be reproducible, and would also let the
    sample be steered --- shortest responses first, say. So the test is that
    the drawn set moves when the registered seed moves, and that it is not the
    head of any ordering a chooser could have preferred.
    """
    import dci1v4r4.stages.human_audit as audit

    pool = _pool()
    drawn = {r["response"] for r in allocate(pool)["drawn"]["pass"]}
    available = [i for i in pool if i["stratum"] == "pass"]
    for order in (lambda i: i["row_id"], lambda i: i["response"],
                  lambda i: len(i["response"]), lambda i: -len(i["response"])):
        head = {i["response"] for i in sorted(available, key=order)[:len(drawn)]}
        assert drawn != head

    original = audit.gate1_sample_seed
    try:
        audit.gate1_sample_seed = lambda *parts: original(*parts) + 1
        moved = {r["response"] for r in allocate(pool)["drawn"]["pass"]}
    finally:
        audit.gate1_sample_seed = original
    assert drawn != moved
    assert {r["response"] for r in allocate(pool)["drawn"]["pass"]} == drawn


# ------------------------------------------------------------ the workflow

@pytest.fixture
def cli(tmp_path, monkeypatch):
    """The tool, pointed at a throwaway tree and a small synthetic pool."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("v4r3_human_audit", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PLAN", tmp_path / "plan.json")
    monkeypatch.setattr(module, "KEY", tmp_path / "key.json")
    monkeypatch.setattr(module, "BRIEF", tmp_path / "REVIEWER_BRIEF.md")
    monkeypatch.setattr(module, "natural_pool", lambda *a, **k: _pool())
    return module


def _plan(cli, **kwargs):
    args = argparse_namespace(annotator="Tester", rule="per_class",
                              batch_size=BATCH_SIZE, replan=False, **kwargs)
    cli.cmd_plan(args)
    return json.loads(cli.PLAN.read_text())


def argparse_namespace(**kwargs):
    import argparse
    return argparse.Namespace(**kwargs)


def _answer_batch(cli, plan, batch, *, correct_key=None, wrong=0):
    rows = [r for r in plan["packet"] if r["batch"] == batch]
    verdicts = {e["item_id"]: e["verdict"] for e in correct_key or []}
    for index, row in enumerate(rows):
        label = verdicts.get(row["item_id"], "SATISFIES")
        if index < wrong:
            label = "VIOLATES" if label == "SATISFIES" else "SATISFIES"
        cli._append("Tester", batch, {"item_id": row["item_id"],
                                      "batch": batch,
                                      "position": row["position"],
                                      "annotator": "Tester", "label": label,
                                      "marks_used": False,
                                      "recorded_at": "2026-08-21T00:00:00Z"})


def test_planning_twice_returns_the_frozen_plan_rather_than_a_new_one(cli):
    first = _plan(cli)
    cli.cmd_plan(argparse_namespace(annotator="Tester", rule="per_class",
                                    batch_size=BATCH_SIZE, replan=False))
    assert json.loads(cli.PLAN.read_text())["plan_hash"] == first["plan_hash"]


def test_the_sample_cannot_be_replaced_once_any_label_exists(cli):
    plan = _plan(cli)
    _answer_batch(cli, plan, 1)
    with pytest.raises(SystemExit) as refusal:
        cli.cmd_plan(argparse_namespace(annotator="Tester", rule="per_class",
                                        batch_size=BATCH_SIZE, replan=True))
    assert "Refusing" in str(refusal.value)
    assert json.loads(cli.PLAN.read_text())["plan_hash"] == plan["plan_hash"]


def test_a_batch_whose_membership_moved_is_refused(cli):
    plan = _plan(cli)
    plan["packet"][0]["response"] = "swapped in after the freeze"
    with pytest.raises(SystemExit) as refusal:
        cli._batch_rows(plan, 1)
    assert "membership hash has moved" in str(refusal.value)


def test_a_plan_whose_hash_no_longer_recomputes_is_refused(cli):
    plan = _plan(cli)
    plan["items"] = 299
    cli.PLAN.write_text(json.dumps(plan))
    with pytest.raises(SystemExit) as refusal:
        cli._load_plan()
    assert "does not recompute" in str(refusal.value)


def test_an_incomplete_batch_cannot_be_sealed(cli):
    plan = _plan(cli)
    rows = [r for r in plan["packet"] if r["batch"] == 1]
    for row in rows[:5]:
        cli._append("Tester", 1, {"item_id": row["item_id"], "batch": 1,
                                  "position": row["position"],
                                  "label": "SATISFIES", "marks_used": False})
    with pytest.raises(SystemExit) as refusal:
        cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    assert "unanswered" in str(refusal.value)


def test_sealing_is_irreversible_and_a_sealed_batch_takes_no_more_rows(cli):
    plan = _plan(cli)
    _answer_batch(cli, plan, 1)
    cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    assert cli._sealed("Tester", 1)
    with pytest.raises(SystemExit) as again:
        cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    assert "already sealed" in str(again.value)
    with pytest.raises(SystemExit) as review:
        cli.cmd_review(argparse_namespace(batch=1, resume=False, edit=False,
                                          annotator="Tester"))
    assert "sealed" in str(review.value)


def test_the_seal_binds_the_membership_and_the_rows_it_sealed(cli):
    plan = _plan(cli)
    _answer_batch(cli, plan, 1)
    cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    seal = json.loads(cli._seal_file("Tester", 1).read_text())
    assert seal["membership_hash"] == plan["batch_hashes"]["1"]
    assert seal["plan_hash"] == plan["plan_hash"]
    assert seal["items"] == BATCH_SIZE


def test_status_reports_progress_and_withholds_agreement(cli, capsys):
    plan = _plan(cli)
    _answer_batch(cli, plan, 1)
    capsys.readouterr()                     # discard the plan's own output
    cli.cmd_status(argparse_namespace(annotator="Tester"))
    out = json.loads(capsys.readouterr().out)
    assert out["answered"] == BATCH_SIZE
    assert out["sealed_batches"] == 0 and out["all_sealed"] is False
    assert out["agreement"].startswith("withheld")


def test_the_report_refuses_until_every_batch_is_sealed(cli):
    plan = _plan(cli)
    _answer_batch(cli, plan, 1)
    cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    with pytest.raises(SystemExit) as refusal:
        cli.cmd_report(argparse_namespace(annotator="Tester",
                                          reveal_early=False))
    assert "not sealed" in str(refusal.value)


def test_the_report_can_be_revealed_early_only_deliberately(cli, capsys):
    plan = _plan(cli)
    key = json.loads(cli.KEY.read_text())["key"]
    _answer_batch(cli, plan, 1, correct_key=key)
    cli.cmd_seal(argparse_namespace(batch=1, annotator="Tester"))
    capsys.readouterr()                     # discard the plan and seal output
    cli.cmd_report(argparse_namespace(annotator="Tester", reveal_early=True))
    out = json.loads(capsys.readouterr().out)
    assert out["compared"] == BATCH_SIZE
    assert out["complete"] is False
    assert out["satisfies_section_10_3"] is False
    written = json.loads((cli.ROOT / "report_Tester.json").read_text())
    assert written["revealed_early"] is True
    assert written["unsealed_batches"] == list(range(2, 13))
